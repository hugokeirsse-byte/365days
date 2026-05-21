#!/usr/bin/env python3
"""Test comparatif de générateurs d'images — line-art coloriage.

But : identifier (a) quels modèles HF Inference répondent VRAIMENT (gratuit) en
2026, et (b) lequel donne le meilleur line-art coloriage. Génère le MÊME prompt
via plusieurs modèles HF + Pollinations (témoin), commit les résultats dans
products/_generator_test/ pour comparaison visuelle.

Env : HF_API_KEY (sinon HF inactif → seul Pollinations marche).
"""
from __future__ import annotations

import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # import lib/
from lib.hf_image_generator import HFImageGenerator  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "products" / "_generator_test"

PROMPT = (
    "adult coloring book page, clean BOLD black outline line art ONLY, "
    "no shading no grey no hatching no sketch, flat clean cartoon style, "
    "cute kawaii baby dragon sitting in a cozy cottage room with fireplace, "
    "books and potted plants, full scene with background, pure white background"
)
NEG = "color, grey, shading, hatching, crosshatching, sketch, pencil, blurry, photo, realistic, text, watermark"

# Candidats HF Inference (commercial-safe en priorité ; dev = test seulement).
HF_MODELS = [
    "black-forest-labs/FLUX.1-schnell",            # Apache-2.0, rapide
    "stabilityai/stable-diffusion-xl-base-1.0",    # défaut actuel (à confirmer)
    "stabilityai/sdxl-turbo",
    "black-forest-labs/FLUX.1-dev",                # non-commercial : test uniquement
]


def pollinations(prompt: str, dest: Path) -> int:
    url = (
        "https://image.pollinations.ai/prompt/"
        + urllib.parse.quote(prompt, safe="")
        + "?model=flux&width=1024&height=1024&nologo=true&enhance=true"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "gen-test/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    dest.write_bytes(data)
    return len(data)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    gen = HFImageGenerator()
    report = [f"HF active : {gen.is_active}", f"prompt : {PROMPT}", "=" * 60]

    for model in HF_MODELS:
        name = model.replace("/", "__")
        dest = OUT / f"{name}.png"
        t0 = time.time()
        try:
            img = gen.text2img(PROMPT, negative_prompt=NEG, width=1024, height=1024, model=model)
        except Exception as exc:  # noqa: BLE001
            report.append(f"❌ {model} : EXC {type(exc).__name__}: {exc}")
            continue
        dt = time.time() - t0
        if img:
            dest.write_bytes(img)
            report.append(f"✅ {model} : OK {len(img)}o {dt:.0f}s -> {dest.name}")
        else:
            report.append(f"❌ {model} : ECHEC (None apres retries) {dt:.0f}s")

    try:
        n = pollinations(PROMPT, OUT / "_pollinations_flux.png")
        report.append(f"🟡 pollinations/flux (temoin) : OK {n}o -> _pollinations_flux.png")
    except Exception as exc:  # noqa: BLE001
        report.append(f"❌ pollinations : EXC {exc}")

    (OUT / "_report.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
