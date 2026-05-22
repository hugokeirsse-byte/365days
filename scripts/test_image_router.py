#!/usr/bin/env python3
"""Test de l'ImageRouter : genere un coloriage via le routeur multi-fournisseurs.

Verifie que le fallback fonctionne (au minimum Pollinations sans cle, et
Together/Cloudflare/Segmind si leurs cles sont posees). Resultat dans
products/_generator_test/router_result.png + rapport.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.image_router import DEFAULT_ORDER, generate  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "products" / "_generator_test"
PROMPT = (
    "adult coloring book page, clean bold black outline line art only, "
    "no shading no grey no hatching, flat clean cartoon style, "
    "cute kawaii baby dragon in a cozy cottage with fireplace, books and "
    "potted plants, full scene with background, pure white background"
)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Ordre des fournisseurs : {DEFAULT_ORDER}")
    dest = OUT / "router_result.png"
    res = generate(PROMPT, seed=42, dest=dest)
    report = OUT / "_image_router_report.txt"
    if res:
        size = Path(res).stat().st_size
        report.write_text(f"OK -> {Path(res).name} ({size} o)\n", encoding="utf-8")
        print(f"OK : {res} ({size} o)")
        return 0
    report.write_text("ECHEC : aucun fournisseur n'a produit d'image\n", encoding="utf-8")
    print("ECHEC")
    return 1


if __name__ == "__main__":
    sys.exit(main())
