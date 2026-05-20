#!/usr/bin/env python3
"""Compositeur de page de coloriage par ASSEMBLAGE D'ÉLÉMENTS — multi-layouts.

Idée Hugo (20/05) : générer des ÉLÉMENTS line-art unitaires (créatures, objets…)
puis les ASSEMBLER sur une page via un patron d'emplacements (comme placer des
sprites, mais statique). Un élément raté = on régénère juste l'élément, pas la page.

Layouts (= « systèmes de valeur ») :
  grid         grille régulière (variation organique optionnelle)
  tessellation pavage dense (saturation visuelle) — répétition d'éléments
  scene        1 grand sujet central + satellites autour (composition narrative)
  border       cadre décoratif d'éléments répétés + grand sujet au centre

Sortie : page PNG + PDF prêt KDP (8.5x11", 300 DPI), line-art noir pur.
Mode --demo : dessine des éléments placeholder (sans clé/réseau).

Usage :
  python scripts/lib/page_composer.py --demo --layout tessellation --out OUT
  python scripts/lib/page_composer.py --elements DIR --layout scene --out OUT
"""
from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

DPI = 300
PAGE_W, PAGE_H = int(8.5 * DPI), int(11 * DPI)  # 2550 x 3300
MARGIN = int(0.6 * DPI)
LINE = 9
LAYOUTS = ("grid", "tessellation", "scene", "border")


# ---------- helpers image ----------

def _binarize(img: Image.Image, threshold: int = 200) -> Image.Image:
    return img.convert("L").point(lambda p: 0 if p < threshold else 255, mode="L")


def _trim(img: Image.Image) -> Image.Image:
    inv = img.convert("L").point(lambda p: 255 if p < 200 else 0)
    bbox = inv.getbbox()
    return img.crop(bbox) if bbox else img


def _fit(img: Image.Image, box_w: int, box_h: int) -> Image.Image:
    img = _trim(img)
    ratio = min(box_w / img.width, box_h / img.height)
    return img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))), Image.LANCZOS)


def _paste_centered(page: Image.Image, el: Image.Image, cx: int, cy: int, rot: float = 0.0) -> None:
    if rot:
        el = el.rotate(rot, expand=True, fillcolor=255)
    mask = el.convert("L").point(lambda p: 255 if p < 128 else 0)
    page.paste(0, (cx - el.width // 2, cy - el.height // 2), mask=mask)


# ---------- layouts ----------

def _grid(page, els, rng, cols=2, rows=3, scatter=True):
    cw = (PAGE_W - 2 * MARGIN) // cols
    ch = (PAGE_H - 2 * MARGIN) // rows
    pad = int(min(cw, ch) * 0.10)
    slots = [(c, r) for r in range(rows) for c in range(cols)]
    for i, (c, r) in enumerate(slots):
        scale = rng.uniform(0.82, 1.0) if scatter else 1.0
        el = _fit(els[i % len(els)], int((cw - 2 * pad) * scale), int((ch - 2 * pad) * scale))
        cx = MARGIN + c * cw + cw // 2 + (rng.randint(-pad // 2, pad // 2) if scatter else 0)
        cy = MARGIN + r * ch + ch // 2 + (rng.randint(-pad // 2, pad // 2) if scatter else 0)
        _paste_centered(page, el, cx, cy, rng.uniform(-7, 7) if scatter else 0)


def _tessellation(page, els, rng, cols=4, rows=5):
    cw = (PAGE_W - 2 * MARGIN) // cols
    ch = (PAGE_H - 2 * MARGIN) // rows
    for i in range(cols * rows):
        c, r = i % cols, i // cols
        el = _fit(els[i % len(els)], int(cw * 0.92), int(ch * 0.92))
        cx = MARGIN + c * cw + cw // 2
        cy = MARGIN + r * ch + ch // 2
        _paste_centered(page, el, cx, cy, rng.uniform(-12, 12))


def _scene(page, els, rng):
    # sujet focal central
    focal = _fit(els[0], int(PAGE_W * 0.52), int(PAGE_H * 0.40))
    _paste_centered(page, focal, PAGE_W // 2, PAGE_H // 2)
    # satellites en anneau
    sats = els[1:] or els
    k = max(4, len(sats))
    rad_x, rad_y = int(PAGE_W * 0.33), int(PAGE_H * 0.34)
    for i in range(k):
        ang = 2 * math.pi * i / k - math.pi / 2
        el = _fit(sats[i % len(sats)], int(PAGE_W * 0.18), int(PAGE_H * 0.13))
        cx = int(PAGE_W // 2 + rad_x * math.cos(ang))
        cy = int(PAGE_H // 2 + rad_y * math.sin(ang))
        _paste_centered(page, el, cx, cy, rng.uniform(-10, 10))


def _border(page, els, rng):
    big = _fit(els[0], int(PAGE_W * 0.5), int(PAGE_H * 0.42))
    _paste_centered(page, big, PAGE_W // 2, PAGE_H // 2)
    per = els[1:] or els
    n_x, n_y = 4, 5
    sz = int(0.13 * DPI * 6)
    xs = [MARGIN + int((PAGE_W - 2 * MARGIN) * j / (n_x - 1)) for j in range(n_x)]
    ys = [MARGIN + int((PAGE_H - 2 * MARGIN) * j / (n_y - 1)) for j in range(n_y)]
    spots = [(x, ys[0]) for x in xs] + [(x, ys[-1]) for x in xs] \
        + [(xs[0], y) for y in ys[1:-1]] + [(xs[-1], y) for y in ys[1:-1]]
    for i, (cx, cy) in enumerate(spots):
        el = _fit(per[i % len(per)], sz, sz)
        _paste_centered(page, el, cx, cy, rng.uniform(-8, 8))


_DISPATCH = {"grid": _grid, "tessellation": _tessellation, "scene": _scene, "border": _border}


def compose_page(elements, layout="grid", seed=0, **opts) -> Image.Image:
    if layout not in _DISPATCH:
        raise ValueError(f"layout inconnu: {layout} (choix: {', '.join(LAYOUTS)})")
    rng = random.Random(seed)
    page = Image.new("L", (PAGE_W, PAGE_H), 255)
    kwargs = {k: v for k, v in opts.items() if v is not None}
    _DISPATCH[layout](page, elements, rng, **kwargs)
    return _binarize(page)


def save_outputs(page: Image.Image, out_stem: Path):
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    png, pdf = out_stem.with_suffix(".png"), out_stem.with_suffix(".pdf")
    page.save(png, dpi=(DPI, DPI))
    page.convert("RGB").save(pdf, "PDF", resolution=DPI)
    return png, pdf


# ---------- démo (éléments placeholder line-art) ----------

def _demo_element(kind: int, size: int = 700) -> Image.Image:
    img = Image.new("L", (size, size), 255)
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    body = int(size * 0.34)
    d.ellipse([cx - body, cy - body, cx + body, cy + body], outline=0, width=LINE)
    eye = int(size * 0.05)
    for sx in (-1, 1):
        ex, ey = cx + sx * int(body * 0.4), cy - int(body * 0.15)
        d.ellipse([ex - eye, ey - eye, ex + eye, ey + eye], outline=0, width=LINE)
        d.ellipse([ex - eye // 3, ey - eye // 3, ex + eye // 3, ey + eye // 3], fill=0)
    sm = int(body * 0.45)
    d.arc([cx - sm, cy, cx + sm, cy + int(body * 0.6)], 20, 160, fill=0, width=LINE)
    if kind % 3 == 0:
        for sx in (-1, 1):
            x = cx + sx * int(body * 0.5)
            d.line([x, cy - body, x + sx * 40, cy - body - 90], fill=0, width=LINE)
            d.ellipse([x + sx * 40 - 22, cy - body - 130, x + sx * 40 + 22, cy - body - 86], outline=0, width=LINE)
    elif kind % 3 == 1:
        for sx in (-1, 1):
            x = cx + sx * int(body * 0.55)
            d.polygon([(x, cy - body), (x + sx * 70, cy - body - 120), (x + sx * 120, cy - body + 10)], outline=0)
    else:
        d.arc([cx - 60, cy - body - 120, cx + 60, cy - body + 20], 200, 340, fill=0, width=LINE)
    for _ in range(3 + kind % 3):
        rx, ry = cx + random.randint(-body // 2, body // 2), cy + random.randint(0, body // 2)
        rr = random.randint(15, 35)
        d.ellipse([rx - rr, ry - rr, rx + rr, ry + rr], outline=0, width=max(4, LINE - 3))
    return img


def make_demo_elements(n: int = 8):
    random.seed(42)
    return [_demo_element(k) for k in range(n)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--elements", help="dossier d'images d'éléments line-art")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--layout", choices=LAYOUTS, default="grid")
    ap.add_argument("--cols", type=int)
    ap.add_argument("--rows", type=int)
    ap.add_argument("--out", default="stage_local/coloring_page")
    a = ap.parse_args()

    if a.demo:
        elements = make_demo_elements(8)
    elif a.elements:
        paths = sorted(p for p in Path(a.elements).iterdir()
                       if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
        if not paths:
            raise SystemExit(f"Aucune image dans {a.elements}")
        elements = [Image.open(p) for p in paths]
    else:
        raise SystemExit("précise --demo ou --elements DIR")

    page = compose_page(elements, layout=a.layout, cols=a.cols, rows=a.rows)
    png, pdf = save_outputs(page, Path(a.out))
    print(f"✅ Layout '{a.layout}' : {len(elements)} éléments dispo")
    print(f"   PNG : {png}  ({page.width}x{page.height} @ {DPI}dpi)")
    print(f"   PDF : {pdf}  (prêt KDP 8.5x11)")


if __name__ == "__main__":
    main()
