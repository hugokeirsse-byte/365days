#!/usr/bin/env python3
"""Compositeur de page de coloriage par ASSEMBLAGE D'ÉLÉMENTS.

Idée Hugo (20/05) : plutôt que générer une page de coloriage complète d'un coup
(peu fiable), on génère des ÉLÉMENTS line-art unitaires (créatures, objets…) puis
on les ASSEMBLE sur une page via un patron d'emplacements (comme placer des sprites,
mais statique). Un élément raté = on régénère juste l'élément, pas la page.

- Entrée : un dossier d'images d'éléments (line-art, noir sur blanc/transparent).
- Sortie : une page PNG + un PDF prêt KDP (8.5x11", 300 DPI), line-art noir pur.
- Mode --demo : dessine des éléments placeholder (sans clé/réseau) pour valider.

Usage :
  python scripts/lib/page_composer.py --demo --out stage_local/demo_coloring_page
  python scripts/lib/page_composer.py --elements DIR --cols 2 --rows 3 --out OUT
"""
from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

# Format KDP : 8.5 x 11 pouces @ 300 DPI
DPI = 300
PAGE_W, PAGE_H = int(8.5 * DPI), int(11 * DPI)  # 2550 x 3300
MARGIN = int(0.6 * DPI)  # marge de sécurité
LINE = 9  # épaisseur de trait (line-art épais, colorable)


def _binarize(img: Image.Image, threshold: int = 200) -> Image.Image:
    """Force noir pur / blanc pur (pas de zone grise — cf. quality_rules)."""
    g = img.convert("L")
    return g.point(lambda p: 0 if p < threshold else 255, mode="L")


def _trim_to_content(img: Image.Image) -> Image.Image:
    """Recadre sur le contenu noir (retire le blanc autour)."""
    gray = img.convert("L")
    inverted = gray.point(lambda p: 255 if p < 200 else 0)
    bbox = inverted.getbbox()
    return img.crop(bbox) if bbox else img


def _fit(img: Image.Image, box_w: int, box_h: int) -> Image.Image:
    """Redimensionne en gardant le ratio pour tenir dans la cellule."""
    img = _trim_to_content(img)
    ratio = min(box_w / img.width, box_h / img.height)
    new = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
    return img.resize(new, Image.LANCZOS)


def compose_page(elements: list[Image.Image], cols: int, rows: int,
                 scatter: bool = True, seed: int = 0) -> Image.Image:
    """Assemble les éléments sur une page line-art au format KDP."""
    rng = random.Random(seed)
    page = Image.new("L", (PAGE_W, PAGE_H), 255)
    cell_w = (PAGE_W - 2 * MARGIN) // cols
    cell_h = (PAGE_H - 2 * MARGIN) // rows
    pad = int(min(cell_w, cell_h) * 0.10)

    slots = [(c, r) for r in range(rows) for c in range(cols)]
    for i, (c, r) in enumerate(slots):
        if not elements:
            break
        el = elements[i % len(elements)]
        # variation de taille douce pour un rendu organique (non-clone)
        scale = rng.uniform(0.82, 1.0) if scatter else 1.0
        fitted = _fit(el, int((cell_w - 2 * pad) * scale), int((cell_h - 2 * pad) * scale))
        if scatter:
            fitted = fitted.rotate(rng.uniform(-7, 7), expand=True, fillcolor=255)
        cx = MARGIN + c * cell_w + (cell_w - fitted.width) // 2
        cy = MARGIN + r * cell_h + (cell_h - fitted.height) // 2
        if scatter:
            cx += rng.randint(-pad // 2, pad // 2)
            cy += rng.randint(-pad // 2, pad // 2)
        # coller en gardant le noir (masque = pixels sombres)
        mask = fitted.point(lambda p: 255 if p < 128 else 0).convert("L")
        page.paste(0, (cx, cy), mask=mask.resize(fitted.size))
    return _binarize(page)


def save_outputs(page: Image.Image, out_stem: Path) -> tuple[Path, Path]:
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    png = out_stem.with_suffix(".png")
    pdf = out_stem.with_suffix(".pdf")
    page.save(png, dpi=(DPI, DPI))
    page.convert("RGB").save(pdf, "PDF", resolution=DPI)
    return png, pdf


# ---------- Mode démo : éléments placeholder line-art (sans clé/réseau) ----------

def _demo_element(kind: int, size: int = 700) -> Image.Image:
    """Dessine une 'créature' mignonne en line-art épais (démo de la chaîne)."""
    img = Image.new("L", (size, size), 255)
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    body = int(size * 0.34)
    # corps
    d.ellipse([cx - body, cy - body, cx + body, cy + body], outline=0, width=LINE)
    # yeux
    eye = int(size * 0.05)
    for sx in (-1, 1):
        ex = cx + sx * int(body * 0.4)
        ey = cy - int(body * 0.15)
        d.ellipse([ex - eye, ey - eye, ex + eye, ey + eye], outline=0, width=LINE)
        d.ellipse([ex - eye // 3, ey - eye // 3, ex + eye // 3, ey + eye // 3], fill=0)
    # sourire (arc)
    sm = int(body * 0.45)
    d.arc([cx - sm, cy, cx + sm, cy + int(body * 0.6)], 20, 160, fill=0, width=LINE)
    # variations décoratives selon kind
    if kind % 3 == 0:  # antennes
        for sx in (-1, 1):
            x = cx + sx * int(body * 0.5)
            d.line([x, cy - body, x + sx * 40, cy - body - 90], fill=0, width=LINE)
            d.ellipse([x + sx * 40 - 22, cy - body - 130, x + sx * 40 + 22, cy - body - 86], outline=0, width=LINE)
    elif kind % 3 == 1:  # oreilles
        for sx in (-1, 1):
            x = cx + sx * int(body * 0.55)
            d.polygon([(x, cy - body), (x + sx * 70, cy - body - 120), (x + sx * 120, cy - body + 10)], outline=0)
    else:  # petite feuille/chapeau
        d.arc([cx - 60, cy - body - 120, cx + 60, cy - body + 20], 200, 340, fill=0, width=LINE)
    # quelques motifs internes (à colorier)
    for _ in range(3 + kind % 3):
        rx, ry = cx + random.randint(-body // 2, body // 2), cy + random.randint(0, body // 2)
        rr = random.randint(15, 35)
        d.ellipse([rx - rr, ry - rr, rx + rr, ry + rr], outline=0, width=max(4, LINE - 3))
    return img


def make_demo_elements(n: int = 6) -> list[Image.Image]:
    random.seed(42)
    return [_demo_element(k) for k in range(n)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--elements", help="dossier d'images d'éléments line-art")
    ap.add_argument("--demo", action="store_true", help="génère des éléments placeholder")
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--rows", type=int, default=3)
    ap.add_argument("--no-scatter", action="store_true", help="grille stricte (sans variation)")
    ap.add_argument("--out", default="stage_local/coloring_page", help="chemin de sortie (sans extension)")
    a = ap.parse_args()

    if a.demo:
        elements = make_demo_elements(a.cols * a.rows)
    elif a.elements:
        paths = sorted(p for p in Path(a.elements).iterdir()
                       if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
        if not paths:
            raise SystemExit(f"Aucune image dans {a.elements}")
        elements = [Image.open(p) for p in paths]
    else:
        raise SystemExit("précise --demo ou --elements DIR")

    page = compose_page(elements, a.cols, a.rows, scatter=not a.no_scatter)
    png, pdf = save_outputs(page, Path(a.out))
    print(f"✅ Page composée : {len(elements)} éléments → {a.cols}x{a.rows}")
    print(f"   PNG : {png}  ({page.width}x{page.height} @ {DPI}dpi)")
    print(f"   PDF : {pdf}  (prêt KDP 8.5x11)")


if __name__ == "__main__":
    main()
