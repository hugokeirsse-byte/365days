#!/usr/bin/env python3
"""Test Cloudflare Workers AI — FLUX-schnell (text2img) + SD1.5 (img2img).

Gratuit 10 000 neurons/jour. Cloudflare sert sa propre API => repond depuis
GitHub Actions (contrairement a HF/AI Horde). Supporte l'image de reference (img2img).
Resultats dans products/_generator_test/.

Env : CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "products" / "_generator_test"
BASE_IMAGE = ROOT / "products" / "coloring_books" / "mystical_creatures" / "pages" / "page_01.png"

TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
ACCOUNT = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()

PROMPT = (
    "adult coloring book page, clean bold black outline line art only, "
    "no shading no grey no hatching no sketch, flat clean cartoon style, "
    "cute kawaii baby dragon in a cozy cottage with fireplace, books and "
    "potted plants, full scene with background, pure white background"
)


def run_model(model: str, payload: dict) -> bytes | None:
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run/{model}"
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        ctype = r.headers.get("Content-Type", "")
        data = r.read()
    if "json" in ctype:
        j = json.loads(data)
        b64 = (j.get("result") or {}).get("image")
        if b64:
            return base64.b64decode(b64)
        raise RuntimeError(f"json sans image: {json.dumps(j)[:200]}")
    return data  # binaire (PNG/JPEG)


def attempt(name: str, model: str, payload: dict, report: list[str]) -> None:
    try:
        img = run_model(model, payload)
    except urllib.error.HTTPError as exc:
        report.append(f"❌ {name} : HTTP {exc.code} {exc.read()[:200].decode(errors='ignore')}")
        return
    except Exception as exc:  # noqa: BLE001
        report.append(f"❌ {name} : {type(exc).__name__} {exc}")
        return
    if img and len(img) > 1000:
        (OUT / f"cloudflare_{name}.png").write_bytes(img)
        report.append(f"✅ {name} : OK {len(img)}o -> cloudflare_{name}.png")
    else:
        report.append(f"❌ {name} : reponse vide/trop petite")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = [f"Cloudflare test — token:{bool(TOKEN)} account:{bool(ACCOUNT)}", "=" * 50]
    if not (TOKEN and ACCOUNT):
        report.append("❌ CLOUDFLARE_API_TOKEN ou CLOUDFLARE_ACCOUNT_ID absent (secrets a poser)")
        (OUT / "_cloudflare_report.txt").write_text("\n".join(report), encoding="utf-8")
        print("\n".join(report))
        return

    attempt("flux_text2img", "@cf/black-forest-labs/flux-1-schnell",
            {"prompt": PROMPT, "steps": 6}, report)

    if BASE_IMAGE.exists():
        b64 = base64.b64encode(BASE_IMAGE.read_bytes()).decode()
        attempt("sd_img2img", "@cf/runwayml/stable-diffusion-v1-5-img2img",
                {"prompt": "clean bold black outline coloring page line art, no shading no grey, flat cartoon",
                 "image_b64": b64, "strength": 0.6, "num_steps": 20}, report)
    else:
        report.append(f"⊘ img2img : image de base absente ({BASE_IMAGE})")

    (OUT / "_cloudflare_report.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
