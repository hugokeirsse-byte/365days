"""ImageRouter — génération d'image résiliente multi-fournisseurs.

Essaie plusieurs fournisseurs dans l'ordre et bascule automatiquement au suivant
en cas d'échec (clé absente, erreur HTTP, timeout, réponse vide). Conçu pour
tourner sur GitHub Actions et ne JAMAIS bloquer un pipeline : Pollinations
(sans clé) est le filet de sécurité final.

Ordre par défaut : together -> cloudflare -> segmind -> pollinations.
Surchargeable via la variable d'env IMAGE_PROVIDERS="cloudflare,pollinations"
ou l'argument providers=[...].

Retourne des bytes (PNG/JPEG) ou, si dest est fourni, écrit le fichier et
retourne son Path. Retourne None si TOUS les fournisseurs échouent.

Clés (toutes optionnelles — un fournisseur sans clé est simplement sauté) :
  TOGETHER_API_KEY
  CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID
  SEGMIND_API_KEY
  POLLINATIONS_TOKEN (optionnel, Pollinations marche sans)
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_ORDER = ["together", "cloudflare", "segmind", "pollinations"]
UA = "365days-ImageRouter/1.0"


def _log(msg: str) -> None:
    print(f"[ImageRouter] {msg}")


def _post_json(url: str, payload: dict, headers: dict, timeout: int) -> tuple[str, bytes]:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json", "User-Agent": UA},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.headers.get("Content-Type", ""), r.read()


def _http_err(exc: urllib.error.HTTPError) -> str:
    return f"HTTP {exc.code} {exc.read()[:140].decode(errors='ignore')}"


def _try_together(prompt, w, h, seed, timeout):
    key = os.environ.get("TOGETHER_API_KEY", "").strip()
    if not key:
        return None, "skip (pas de TOGETHER_API_KEY)"
    model = os.environ.get("TOGETHER_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell-Free")
    payload = {"model": model, "prompt": prompt, "width": w, "height": h, "n": 1, "steps": 4}
    if seed is not None:
        payload["seed"] = seed
    try:
        _, body = _post_json("https://api.together.xyz/v1/images/generations",
                             payload, {"Authorization": f"Bearer {key}"}, timeout)
        data = json.loads(body)
        item = (data.get("data") or [{}])[0]
        if item.get("b64_json"):
            return base64.b64decode(item["b64_json"]), "ok"
        if item.get("url"):
            with urllib.request.urlopen(item["url"], timeout=timeout) as r:
                return r.read(), "ok"
        return None, f"reponse inattendue: {json.dumps(data)[:140]}"
    except urllib.error.HTTPError as exc:
        return None, _http_err(exc)
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__} {exc}"


def _try_cloudflare(prompt, w, h, seed, timeout):
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    acct = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    if not (token and acct):
        return None, "skip (pas de clés Cloudflare)"
    model = os.environ.get("CLOUDFLARE_IMAGE_MODEL", "@cf/black-forest-labs/flux-1-schnell")
    try:
        ctype, body = _post_json(
            f"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/run/{model}",
            {"prompt": prompt, "steps": 6}, {"Authorization": f"Bearer {token}"}, timeout)
        if "json" in ctype:
            j = json.loads(body)
            b64 = (j.get("result") or {}).get("image")
            if b64:
                return base64.b64decode(b64), "ok"
            return None, f"json sans image: {json.dumps(j)[:140]}"
        return body, "ok"  # binaire
    except urllib.error.HTTPError as exc:
        return None, _http_err(exc)
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__} {exc}"


def _try_segmind(prompt, w, h, seed, timeout):
    key = os.environ.get("SEGMIND_API_KEY", "").strip()
    if not key:
        return None, "skip (pas de SEGMIND_API_KEY)"
    url = os.environ.get("SEGMIND_IMAGE_URL", "https://api.segmind.com/v1/flux-schnell")
    payload = {"prompt": prompt, "img_width": w, "img_height": h, "num_inference_steps": 4}
    if seed is not None:
        payload["seed"] = seed
    try:
        ctype, body = _post_json(url, payload, {"x-api-key": key}, timeout)
        if "json" in ctype:
            j = json.loads(body)
            b64 = j.get("image") or j.get("b64_json")
            if b64:
                return base64.b64decode(b64), "ok"
            return None, f"json sans image: {json.dumps(j)[:140]}"
        return body, "ok"  # binaire image direct
    except urllib.error.HTTPError as exc:
        return None, _http_err(exc)
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__} {exc}"


def _try_pollinations(prompt, w, h, seed, timeout):
    token = os.environ.get("POLLINATIONS_TOKEN", "").strip()
    model = os.environ.get("POLLINATIONS_MODEL", "flux")
    q = {"width": w, "height": h, "model": model, "nologo": "true"}
    if seed is not None:
        q["seed"] = seed
    if token:
        q["token"] = token
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?{urllib.parse.urlencode(q)}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            if data and len(data) > 1000:
                return data, "ok"
            return None, "reponse vide"
        except Exception as exc:  # noqa: BLE001
            if attempt == 2:
                return None, f"{type(exc).__name__} {exc}"
            time.sleep(5 * (attempt + 1))
    return None, "echec"


_PROVIDERS = {
    "together": _try_together,
    "cloudflare": _try_cloudflare,
    "segmind": _try_segmind,
    "pollinations": _try_pollinations,
}


def generate(prompt: str, seed: int | None = None, width: int = 1024, height: int = 1024,
             providers: list[str] | None = None, dest=None, timeout: int = 180):
    """Génère une image via le 1er fournisseur disponible. Retourne bytes, Path ou None."""
    env_order = [p.strip() for p in os.environ.get("IMAGE_PROVIDERS", "").split(",") if p.strip()]
    order = providers or env_order or DEFAULT_ORDER
    for name in order:
        fn = _PROVIDERS.get(name)
        if not fn:
            _log(f"{name}: fournisseur inconnu, ignoré")
            continue
        img, info = fn(prompt, width, height, seed, timeout)
        if img and len(img) > 1000:
            _log(f"{name}: OK ({len(img)} o)")
            if dest is not None:
                dest = Path(dest)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(img)
                return dest
            return img
        _log(f"{name}: {info}")
    _log("ÉCHEC — aucun fournisseur n'a produit d'image")
    return None
