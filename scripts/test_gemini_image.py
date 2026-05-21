#!/usr/bin/env python3
"""Test Gemini 2.5 Flash Image (Nano Banana) — text2img ET img2img.

But : valider que la cle GEMINI_API_KEY permet de generer/editer des images
(500/jour gratuit), AVEC image de reference. Compare :
  1. text2img : prompt seul -> coloriage line-art
  2. img2img  : image de base (page deja generee) + prompt "nettoie en line-art propre"
Resultats dans products/_generator_test/ pour comparaison visuelle.

Env : GEMINI_API_KEY (deja pose). Modele override : GEMINI_IMAGE_MODEL.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "products" / "_generator_test"
BASE_IMAGE = ROOT / "products" / "coloring_books" / "mystical_creatures" / "pages" / "page_01.png"

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

PROMPT_T2I = (
    "Generate an adult coloring book page: clean BOLD black outline line art ONLY, "
    "uniform thick vector-style outlines on pure white background, flat clean cartoon style, "
    "NO shading, NO grey, NO hatching, NO sketch, NO color. "
    "Subject: a cute kawaii baby dragon sitting in a cozy cottage room with a fireplace, "
    "books and potted plants, full scene with simple background. Pure white background."
)
PROMPT_I2I = (
    "Redraw this image as a clean professional adult coloring book page: "
    "convert everything to BOLD uniform black outlines only on pure white background, "
    "remove ALL shading, grey, hatching, crosshatching and sketch texture, "
    "keep closed simple shapes ready to color, flat clean cartoon line art."
)


def call_gemini(prompt: str, ref_bytes: bytes | None = None) -> tuple[bytes | None, str]:
    if not API_KEY:
        return None, "GEMINI_API_KEY absent"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
    parts: list[dict] = [{"text": prompt}]
    if ref_bytes:
        parts.append({"inline_data": {"mime_type": "image/png",
                                      "data": base64.b64encode(ref_bytes).decode()}})
    body = {"contents": [{"parts": parts}]}
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            resp = json.loads(r.read())
    except urllib.error.HTTPError as exc:  # type: ignore[attr-defined]
        return None, f"HTTP {exc.code}: {exc.read()[:300].decode(errors='ignore')}"
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"
    for cand in resp.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            inline = part.get("inline_data") or part.get("inlineData")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"]), "OK"
    return None, f"pas d'image dans la reponse: {json.dumps(resp)[:300]}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = [f"Gemini image test — modele: {MODEL}", f"cle presente: {bool(API_KEY)}", "=" * 60]

    img, status = call_gemini(PROMPT_T2I)
    if img:
        (OUT / "gemini_text2img.png").write_bytes(img)
        report.append(f"✅ text2img : OK {len(img)}o -> gemini_text2img.png")
    else:
        report.append(f"❌ text2img : {status}")

    if BASE_IMAGE.exists():
        ref = BASE_IMAGE.read_bytes()
        img2, status2 = call_gemini(PROMPT_I2I, ref_bytes=ref)
        if img2:
            (OUT / "gemini_img2img.png").write_bytes(img2)
            report.append(f"✅ img2img (base=page_01) : OK {len(img2)}o -> gemini_img2img.png")
        else:
            report.append(f"❌ img2img : {status2}")
    else:
        report.append(f"⊘ img2img : image de base absente ({BASE_IMAGE})")

    (OUT / "_gemini_report.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
