"""
HF IMAGE GENERATOR — wrapper Hugging Face Inference API.

Permet à tous nos pipelines de générer des images via HF (gratuit
illimité en pratique, ~7000 req/jour) avec 3 modes :

1. text2img        — prompt → image (SDXL haute qualité)
2. img2img         — image source + prompt → variation
3. style_transfer  — image de référence + prompt → image dans CE style

Auto-fallback vers Pollinations si HF_API_KEY absent.
Cache local pour éviter régénérations identiques.

Usage :
    from lib.hf_image_generator import HFImageGenerator
    gen = HFImageGenerator()
    img_bytes = gen.text2img(
        prompt="cute cat watercolor portrait",
        negative_prompt="text, watermark, deformed",
        width=1024, height=1024,
    )

    # Avec image de référence
    img_bytes = gen.style_transfer(
        prompt="fishing scene at sunset",
        reference_path=Path("assets/reference_images/specs_style.png"),
        strength=0.7,
    )

Variables d'env :
    HF_API_KEY         token HF (obligatoire pour activation)
    HF_DEFAULT_MODEL   modèle SDXL par défaut
    HF_CACHE_DIR       dossier cache local
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


# ============================================================
# CONSTANTS
# ============================================================

LIB_DIR = Path(__file__).resolve().parent
DEFAULT_CACHE_DIR = LIB_DIR / "assets" / "hf_cache"
DEFAULT_REFERENCE_DIR = LIB_DIR / "assets" / "reference_images"

# Modèles HF Inference API gratuits (licences commerciales OK)
DEFAULT_TEXT2IMG_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"
ALT_TEXT2IMG_MODELS = {
    "sdxl":         "stabilityai/stable-diffusion-xl-base-1.0",
    "flux_schnell": "black-forest-labs/FLUX.1-schnell",
    "flux_dev":     "black-forest-labs/FLUX.1-dev",
    "dreamshaper":  "Lykon/dreamshaper-xl-1-0",
    "playground":   "playgroundai/playground-v2.5-1024px-aesthetic",
}

# Modèles ControlNet (structure-aware)
CONTROLNET_MODELS = {
    "canny":  "lllyasviel/sd-controlnet-canny",
    "depth":  "lllyasviel/sd-controlnet-depth",
    "openpose": "lllyasviel/sd-controlnet-openpose",
}

# Models IP-Adapter (style transfer depuis image de référence)
IP_ADAPTER_MODELS = {
    "default": "h94/IP-Adapter",
    "sdxl":    "h94/IP-Adapter-FaceID-SDXL",
}

API_BASE = "https://api-inference.huggingface.co/models"

USER_AGENT = "365days-HFGenerator/1.0"
TIMEOUT = 240
RETRY_ATTEMPTS = 4


# ============================================================
# WRAPPER CLASS
# ============================================================

class HFImageGenerator:
    """Wrapper Hugging Face Inference API.

    Auto-active si HF_API_KEY défini. Sinon mode dégradé (fallback
    Pollinations via le pipeline appelant).
    """

    def __init__(self,
                 api_key: str | None = None,
                 cache_dir: Path | None = None,
                 default_model: str | None = None,
                 use_cache: bool = True):
        self.api_key = api_key or os.environ.get("HF_API_KEY", "").strip()
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.default_model = default_model or os.environ.get(
            "HF_DEFAULT_MODEL", DEFAULT_TEXT2IMG_MODEL)
        self.use_cache = use_cache
        if self.use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_active(self) -> bool:
        """True si HF_API_KEY est défini, sinon module en mode dégradé."""
        return bool(self.api_key)

    # ============================================================
    # CACHE
    # ============================================================

    def _cache_key(self, model: str, mode: str, prompt: str,
                    extra: dict | None = None) -> str:
        """Génère une clé de cache déterministe."""
        payload = {
            "model": model,
            "mode": mode,
            "prompt": prompt,
            "extra": extra or {},
        }
        blob = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()[:20]

    def _cache_get(self, key: str) -> bytes | None:
        if not self.use_cache:
            return None
        path = self.cache_dir / f"{key}.png"
        return path.read_bytes() if path.exists() else None

    def _cache_set(self, key: str, data: bytes) -> None:
        if not self.use_cache:
            return
        (self.cache_dir / f"{key}.png").write_bytes(data)

    # ============================================================
    # API CALL CORE
    # ============================================================

    def _call_api(self, model: str, payload: dict,
                   retries: int = RETRY_ATTEMPTS) -> bytes | None:
        if not self.is_active:
            return None
        url = f"{API_BASE}/{model}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Accept": "image/png",
        }
        data = json.dumps(payload).encode("utf-8")

        for attempt in range(retries):
            try:
                req = urllib.request.Request(
                    url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    content = resp.read()
                # HF peut retourner un JSON d'erreur même avec 200
                if content.startswith(b"{"):
                    try:
                        err = json.loads(content)
                        if "error" in err:
                            print(f"   HF API error : {err.get('error', '')[:200]}")
                            if err.get("estimated_time"):
                                wait = min(60, int(err["estimated_time"]) + 2)
                                print(f"   wait {wait}s (model loading)")
                                time.sleep(wait)
                                continue
                            return None
                    except json.JSONDecodeError:
                        pass
                if len(content) < 1000:
                    print(f"   HF response too small ({len(content)}b)")
                    continue
                return content
            except urllib.error.HTTPError as exc:
                if exc.code == 503:
                    wait = 20 + attempt * 10
                    print(f"   HF 503 (cold start), wait {wait}s")
                    time.sleep(wait)
                    continue
                elif exc.code == 429:
                    wait = 60 + attempt * 30
                    print(f"   HF 429 rate limit, wait {wait}s")
                    time.sleep(wait)
                    continue
                else:
                    print(f"   HF HTTP {exc.code} : {exc.reason}")
                    time.sleep(5 + attempt * 5)
            except Exception as exc:  # noqa: BLE001
                print(f"   HF error : {type(exc).__name__}: {exc}")
                time.sleep(5 + attempt * 5)
        return None

    # ============================================================
    # TEXT TO IMAGE
    # ============================================================

    def text2img(self,
                 prompt: str,
                 negative_prompt: str = "",
                 width: int = 1024,
                 height: int = 1024,
                 steps: int = 30,
                 guidance: float = 7.5,
                 seed: int | None = None,
                 model: str | None = None) -> bytes | None:
        """Generate image from text prompt only."""
        model = model or self.default_model
        if seed is None:
            seed = int(time.time() * 1000) % 2147483647

        cache_key = self._cache_key(
            model, "text2img", prompt,
            {"neg": negative_prompt, "w": width, "h": height,
             "steps": steps, "g": guidance, "seed": seed},
        )
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": negative_prompt,
                "num_inference_steps": steps,
                "guidance_scale": guidance,
                "width": width,
                "height": height,
                "seed": seed,
            },
            "options": {"wait_for_model": True},
        }
        result = self._call_api(model, payload)
        if result:
            self._cache_set(cache_key, result)
        return result

    # ============================================================
    # IMAGE TO IMAGE
    # ============================================================

    def img2img(self,
                prompt: str,
                source_image: bytes | Path,
                negative_prompt: str = "",
                strength: float = 0.6,
                steps: int = 30,
                guidance: float = 7.5,
                seed: int | None = None,
                model: str | None = None) -> bytes | None:
        """Generate variation from a source image + prompt.

        strength : 0-1 (0 = source intact, 1 = totalement régénéré)
        """
        model = model or self.default_model
        if seed is None:
            seed = int(time.time() * 1000) % 2147483647

        if isinstance(source_image, Path):
            source_image = source_image.read_bytes()
        img_b64 = base64.b64encode(source_image).decode("ascii")

        cache_key = self._cache_key(
            model, "img2img", prompt,
            {"neg": negative_prompt, "strength": strength,
             "steps": steps, "g": guidance, "seed": seed,
             "img_hash": hashlib.sha256(source_image).hexdigest()[:12]},
        )
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        payload = {
            "inputs": {
                "prompt": prompt,
                "image": img_b64,
            },
            "parameters": {
                "negative_prompt": negative_prompt,
                "strength": strength,
                "num_inference_steps": steps,
                "guidance_scale": guidance,
                "seed": seed,
            },
            "options": {"wait_for_model": True},
        }
        result = self._call_api(model, payload)
        if result:
            self._cache_set(cache_key, result)
        return result

    # ============================================================
    # STYLE TRANSFER VIA IP-ADAPTER
    # ============================================================

    def style_transfer(self,
                       prompt: str,
                       reference_path: Path,
                       negative_prompt: str = "",
                       strength: float = 0.75,
                       steps: int = 30,
                       guidance: float = 7.5,
                       seed: int | None = None,
                       model: str | None = None) -> bytes | None:
        """Génère une nouvelle image dans le STYLE de l'image de référence.

        reference_path : chemin vers l'image style (ex: assets/reference_images/...)
        strength : 0-1, force du style transfer (0.7-0.85 recommandé)

        Note : utilise le wrapper IP-Adapter qui combine SDXL + style ref.
        """
        if not reference_path.exists():
            print(f"   ✗ Référence absente : {reference_path}")
            return None
        return self.img2img(
            prompt=prompt,
            source_image=reference_path,
            negative_prompt=negative_prompt,
            strength=strength,
            steps=steps,
            guidance=guidance,
            seed=seed,
            model=model or IP_ADAPTER_MODELS["default"],
        )

    # ============================================================
    # UTILS
    # ============================================================

    def list_reference_images(self) -> list[Path]:
        """Liste les images de référence disponibles."""
        if not DEFAULT_REFERENCE_DIR.exists():
            return []
        return sorted(
            list(DEFAULT_REFERENCE_DIR.rglob("*.png")) +
            list(DEFAULT_REFERENCE_DIR.rglob("*.jpg")) +
            list(DEFAULT_REFERENCE_DIR.rglob("*.jpeg"))
        )

    def find_reference(self, pipeline: str, niche: str) -> Path | None:
        """Cherche une image de référence pour (pipeline, niche).

        Convention : assets/reference_images/<pipeline>/<niche>.png
        """
        candidates = [
            DEFAULT_REFERENCE_DIR / pipeline / f"{niche}.png",
            DEFAULT_REFERENCE_DIR / pipeline / f"{niche}.jpg",
            DEFAULT_REFERENCE_DIR / f"{pipeline}_{niche}.png",
            DEFAULT_REFERENCE_DIR / f"{pipeline}.png",
        ]
        return next((p for p in candidates if p.exists()), None)


# ============================================================
# CONVENIENCE HELPER
# ============================================================

def get_image_for_pipeline(prompt: str,
                            pipeline: str,
                            niche: str,
                            width: int = 1024,
                            height: int = 1024,
                            negative_prompt: str = "") -> bytes | None:
    """Helper haut niveau : trouve ref image si dispo, sinon text2img.

    Cherche `assets/reference_images/<pipeline>/<niche>.png`.
    Si trouvé → style_transfer depuis cette ref.
    Sinon → text2img classique.
    Si HF_API_KEY absent → retourne None (caller fait fallback Pollinations).
    """
    gen = HFImageGenerator()
    if not gen.is_active:
        return None
    ref = gen.find_reference(pipeline, niche)
    if ref:
        print(f"   🎨 Style ref : {ref.name}")
        return gen.style_transfer(
            prompt=prompt,
            reference_path=ref,
            negative_prompt=negative_prompt,
        )
    return gen.text2img(
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
    )


if __name__ == "__main__":
    gen = HFImageGenerator()
    print(f"HF active : {gen.is_active}")
    print(f"Default model : {gen.default_model}")
    print(f"Cache dir : {gen.cache_dir}")
    print(f"Reference images : {len(gen.list_reference_images())}")
    if gen.is_active:
        print("→ Pipelines peuvent appeler text2img / img2img / style_transfer")
    else:
        print("→ Mode dégradé : HF_API_KEY non défini")
        print("→ Caller doit fallback sur Pollinations")
