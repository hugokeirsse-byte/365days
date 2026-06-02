"""
KDP — Coloring Activity Book generator
Réutilise les mêmes SVGs / images Gemini que le pipeline TPT.
Produit : interior.pdf (24 pages min.) + cover_front.pdf + bundle.zip

Usage :
  python scripts/kdp/pipeline_kdp.py
  THEMES=halloween,christmas python scripts/kdp/pipeline_kdp.py
  OUT_DIR=products/kdp/books python scripts/kdp/pipeline_kdp.py
"""
from __future__ import annotations

import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brand import BRAND, C_PRIMARY, C_SECONDARY, C_ACCENT, C_LIGHT, footer, header_band, lighten, text_color_on
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

ROOT  = Path(__file__).resolve().parent.parent.parent
THEMES_DIR = ROOT / "scripts" / "tpt" / "themes"

PAGE_W, PAGE_H = letter
M = 0.5 * inch

# Import theme configs from TPT pipeline
sys.path.insert(0, str(ROOT / "scripts" / "tpt"))
from pipeline_cbc import THEMES, get_image


# ── Helpers ───────────────────────────────────────────────────────────────────

def _embed(c, img_path: Path, x, y, max_w, max_h):
    suffix = img_path.suffix.lower()
    if suffix == ".svg":
        drawing = svg2rlg(str(img_path))
        if not drawing:
            return x, y, 0, 0
        scale = min(max_w / drawing.width, max_h / drawing.height)
        dw, dh = drawing.width * scale, drawing.height * scale
        ox = x + (max_w - dw) / 2
        oy = y + (max_h - dh) / 2
        drawing.width, drawing.height = dw, dh
        drawing.transform = (scale, 0, 0, scale, 0, 0)
        renderPDF.draw(drawing, c, ox, oy)
        return ox, oy, dw, dh
    else:
        from reportlab.lib.utils import ImageReader
        img = ImageReader(str(img_path))
        iw, ih = img.getSize()
        scale = min(max_w / iw, max_h / ih)
        dw, dh = iw * scale, ih * scale
        ox = x + (max_w - dw) / 2
        oy = y + (max_h - dh) / 2
        c.drawImage(str(img_path), ox, oy, dw, dh, mask="auto")
        return ox, oy, dw, dh


def _overlay_labels(c, cfg, ix, iy, iw, ih):
    ans_map = {ans: HexColor(hx) for ans, _, hx in cfg["colors"]}
    for ans, rx, ry in cfg["regions"]:
        lx = ix + rx * iw
        ly = iy + ih * (1 - ry)
        col = ans_map.get(ans, C_PRIMARY)
        c.saveState()
        c.setFillColor(white)
        c.setStrokeColor(col)
        c.setLineWidth(2)
        c.circle(lx, ly, 11, fill=1, stroke=1)
        c.setFillColor(col)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(lx, ly - 4, str(ans))
        c.restoreState()


# ── KDP pages ─────────────────────────────────────────────────────────────────

def page_title(c, book_title: str, subtitle: str):
    """Page 1 — Titre."""
    light = HexColor(lighten(BRAND["primary"]))
    c.setFillColor(light)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setStrokeColor(C_PRIMARY)
    c.setLineWidth(5)
    c.roundRect(M, M, PAGE_W - 2*M, PAGE_H - 2*M, 14, fill=0, stroke=1)

    # Owl emoji (Unicode, simple)
    c.setFillColor(C_PRIMARY)
    c.setFont("Helvetica-Bold", 56)
    c.drawCentredString(PAGE_W/2, PAGE_H*0.62, "🦉")

    c.setFillColor(C_SECONDARY)
    c.setFont("Helvetica-Bold", 28)
    words = book_title.split()
    mid = len(words) // 2 or 1
    c.drawCentredString(PAGE_W/2, PAGE_H*0.50, " ".join(words[:mid]))
    c.drawCentredString(PAGE_W/2, PAGE_H*0.43, " ".join(words[mid:]))

    c.setFont("Helvetica", 15)
    c.setFillColor(HexColor("#555"))
    c.drawCentredString(PAGE_W/2, PAGE_H*0.36, subtitle)

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(C_PRIMARY)
    c.drawCentredString(PAGE_W/2, PAGE_H*0.22, BRAND["name"])
    c.setFont("Helvetica", 11)
    c.setFillColor(HexColor("#777"))
    c.drawCentredString(PAGE_W/2, PAGE_H*0.17, BRAND["tagline"])

    c.showPage()


def page_instructions(c):
    """Page 2 — Comment utiliser ce livre."""
    header_band(c, PAGE_W, PAGE_H, M, "How to Use This Book")
    y = PAGE_H - M - 0.65*inch - 0.5*inch

    steps = [
        ("1", "Solve each math problem on the page."),
        ("2", "Find the answer in the Color Key."),
        ("3", "Color each region with the matching color."),
        ("4", "When done, your picture will come to life!"),
    ]
    for num, text in steps:
        # Cercle numéroté
        cx = M + 0.35*inch
        c.setFillColor(C_PRIMARY)
        c.circle(cx, y, 0.28*inch, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(cx, y - 7, num)
        # Texte
        c.setFillColor(black)
        c.setFont("Helvetica", 14)
        c.drawString(M + 0.80*inch, y - 5, text)
        y -= 0.80*inch

    # Astuce bonus
    y -= 0.3*inch
    c.setFillColor(HexColor(lighten(BRAND["primary"])))
    c.roundRect(M, y - 0.6*inch, PAGE_W - 2*M, 0.9*inch, 8, fill=1, stroke=0)
    c.setFillColor(C_SECONDARY)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(PAGE_W/2, y + 0.14*inch, "⭐  Tip: Check your answer key on the last pages!")

    footer(c, PAGE_W, M)
    c.showPage()


def page_activity(c, cfg: dict, img_path: Path, show_answers: bool, page_num: int):
    """Page d'activité : image + color key + 5 problèmes (format livre)."""
    hx = cfg["header_hex"]
    title = cfg["title"] + (" — Answer Key" if show_answers else "")
    y = header_band(c, PAGE_W, PAGE_H, M, title, cfg["subtitle"], color_hex=hx)

    # Color key strip
    ky = y - 0.28*inch
    kh = 0.28*inch
    c.saveState()
    c.setFillColor(HexColor("#FFF8E7"))
    c.setStrokeColor(HexColor(hx))
    c.setLineWidth(1)
    c.roundRect(M, ky, PAGE_W - 2*M, kh, 4, fill=1, stroke=1)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(black)
    c.drawString(M + 5, ky + kh/2 - 4, "COLOR KEY:")
    sw = 11
    reserve = 74
    iw_ = (PAGE_W - 2*M - reserve) / len(cfg["colors"])
    for i, (ans, name, chex) in enumerate(cfg["colors"]):
        ix_ = M + reserve + i * iw_
        iy_ = ky + kh/2 - sw/2
        c.setFillColor(HexColor(chex))
        c.setStrokeColor(HexColor("#555"))
        c.setLineWidth(0.5)
        c.rect(ix_, iy_, sw, sw, fill=1, stroke=1)
        c.setFillColor(black)
        c.setFont("Helvetica", 7.5)
        c.drawString(ix_ + sw + 2, iy_ + 1, f"{ans}={name}")
    c.restoreState()

    # Layout : image (left 60%) + problèmes (right 40%)
    ct_top = ky - 0.08*inch
    ct_bot = 0.48*inch
    ct_h = ct_top - ct_bot
    total_w = PAGE_W - 2*M
    scene_w = total_w * 0.56
    prob_w = total_w - scene_w - 0.10*inch

    result = _embed(c, img_path, M, ct_bot, scene_w, ct_h)
    if len(result) == 4:
        ox, oy, dw, dh = result
        _overlay_labels(c, cfg, ox, oy, dw, dh)

    # Problèmes (5 premiers pour format livre, plus grand)
    probs = cfg["problems"][:5] if not show_answers else cfg["problems"][:5]
    ans_map = {ans: HexColor(chex) for ans, _, chex in cfg["colors"]}
    px = M + scene_w + 0.10*inch
    py = ct_top
    c.setFillColor(C_PRIMARY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(px, py, "Solve & Color:")
    py -= 0.30*inch

    bh = (ct_h - 0.30*inch) / 5 - 4
    for i, (a, op, b, ans) in enumerate(probs):
        by_ = py - i * (bh + 4)
        c.saveState()
        c.setFillColor(HexColor("#F7F3FF") if i % 2 == 0 else white)
        c.rect(px, by_ - bh, prob_w, bh, fill=1, stroke=0)
        # Badge
        c.setFillColor(C_PRIMARY)
        c.circle(px + 10, by_ - bh/2, 8, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(px + 10, by_ - bh/2 - 3, str(i+1))
        # Equation
        c.setFillColor(black)
        c.setFont("Helvetica", 15)
        c.drawString(px + 24, by_ - bh/2 - 6, f"{a}  {op}  {b}  =")
        # Answer box
        bax = px + prob_w - 28
        bay = by_ - bh + 6
        c.setStrokeColor(HexColor("#AAAAAA"))
        c.setLineWidth(0.8)
        c.rect(bax, bay, 22, 22, fill=0, stroke=1)
        if show_answers:
            acol = ans_map.get(ans, white)
            c.setFillColor(acol)
            c.rect(bax, bay, 22, 22, fill=1, stroke=1)
            tc = text_color_on(cfg["colors"][[x[0] for x in cfg["colors"]].index(ans)][2]
                               if ans in [x[0] for x in cfg["colors"]] else "#FFFFFF")
            c.setFillColor(tc)
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(bax + 11, bay + 5, str(ans))
        c.restoreState()

    # Numéro de page
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#AAAAAA"))
    c.drawCentredString(PAGE_W/2, 0.22*inch, str(page_num))

    footer(c, PAGE_W, M)
    c.showPage()


def page_coloring_only(c, cfg: dict, img_path: Path, page_num: int):
    """Page coloriage libre (sans problèmes) — bonus pour les plus jeunes."""
    hx = cfg["header_hex"]
    title = f"{cfg['title'].split()[0]} Coloring Page"
    y = header_band(c, PAGE_W, PAGE_H, M, title, "Color for fun!", color_hex=hx)

    ct_top = y - 0.10*inch
    ct_bot = 0.48*inch
    ct_h = ct_top - ct_bot
    iw_ = PAGE_W - 2*M

    _embed(c, img_path, M, ct_bot, iw_, ct_h)

    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#AAAAAA"))
    c.drawCentredString(PAGE_W/2, 0.22*inch, str(page_num))
    footer(c, PAGE_W, M)
    c.showPage()


def page_answer_section_header(c, page_num: int):
    header_band(c, PAGE_W, PAGE_H, M, "Answer Keys", "Check your work!")
    c.setFont("Helvetica", 13)
    c.setFillColor(black)
    c.drawCentredString(PAGE_W/2, PAGE_H/2,
                        "Answer keys follow on the next pages.")
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#AAAAAA"))
    c.drawCentredString(PAGE_W/2, 0.22*inch, str(page_num))
    footer(c, PAGE_W, M)
    c.showPage()


def page_notes(c, page_num: int):
    header_band(c, PAGE_W, PAGE_H, M, "Notes")
    # Lignes
    y = PAGE_H - M - 0.65*inch - 0.5*inch
    while y > M + 0.5*inch:
        c.setStrokeColor(HexColor("#DDDDDD"))
        c.setLineWidth(0.5)
        c.line(M, y, PAGE_W - M, y)
        y -= 0.32*inch
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#AAAAAA"))
    c.drawCentredString(PAGE_W/2, 0.22*inch, str(page_num))
    footer(c, PAGE_W, M)
    c.showPage()


# ── KDP Cover ─────────────────────────────────────────────────────────────────

def build_cover(path: Path, book_title: str, subtitle: str, color_hex: str):
    c = rl_canvas.Canvas(str(path), pagesize=letter)
    light = HexColor(lighten(color_hex, 0.78))
    hx = HexColor(color_hex)

    c.setFillColor(light)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setStrokeColor(hx)
    c.setLineWidth(8)
    c.roundRect(M*0.5, M*0.5, PAGE_W - M, PAGE_H - M, 18, fill=0, stroke=1)

    # Bandeau central
    bh = 3.0*inch
    by = PAGE_H*0.38
    c.setFillColor(hx)
    c.roundRect(M + 0.3*inch, by, PAGE_W - 2*M - 0.6*inch, bh, 14, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 30)
    words = book_title.split()
    mid = len(words)//2 or 1
    c.drawCentredString(PAGE_W/2, by + bh - 0.75*inch, " ".join(words[:mid]))
    c.drawCentredString(PAGE_W/2, by + bh - 1.35*inch, " ".join(words[mid:]))
    c.setFont("Helvetica", 16)
    c.drawCentredString(PAGE_W/2, by + 0.45*inch, subtitle)

    # Bullets
    bullets = ["No Prep · Just Print", "Answer Keys Included", "Ages 5–9"]
    yb = by - 0.9*inch
    for blt in bullets:
        c.setFillColor(hx)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(M + 0.9*inch, yb, "✓")
        c.setFillColor(black)
        c.setFont("Helvetica", 14)
        c.drawString(M + 1.25*inch, yb, blt)
        yb -= 0.45*inch

    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(HexColor("#555"))
    c.drawCentredString(PAGE_W/2, M + 0.5*inch, f"by {BRAND['name']}")
    c.showPage()
    c.save()


# ── Master builder ─────────────────────────────────────────────────────────────

def build_book(theme_ids: list[str], out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    # Résoudre les images
    images: dict[str, Path] = {}
    cfgs: dict[str, dict] = {}
    for tid in theme_ids:
        cfg = THEMES[tid]
        cfgs[tid] = cfg
        try:
            img = get_image(tid, cfg, out_dir / tid)
            images[tid] = img
        except FileNotFoundError:
            print(f"  [KDP] image manquante pour {tid}, thème ignoré")

    available = [t for t in theme_ids if t in images]
    if not available:
        print("  [KDP] aucun thème disponible, abandon")
        return

    # Titre du livre
    if len(available) == 1:
        book_title = cfgs[available[0]]["title"] + " Activity Book"
        book_subtitle = cfgs[available[0]]["subtitle"]
        main_color = cfgs[available[0]]["header_hex"]
    else:
        book_title = "Math Color by Code Activity Book"
        book_subtitle = f"Grades K–3  ·  {len(available)} Themes  ·  Answer Keys Included"
        main_color = BRAND["primary"]

    # Interior PDF
    interior_path = out_dir / "interior.pdf"
    c = rl_canvas.Canvas(str(interior_path), pagesize=letter)
    pg = 1

    page_title(c, book_title, book_subtitle);          pg += 1
    page_instructions(c);                              pg += 1

    # Activités
    for tid in available:
        page_activity(c, cfgs[tid], images[tid], False, pg); pg += 1

    # Coloriages libres bonus
    for tid in available:
        page_coloring_only(c, cfgs[tid], images[tid], pg); pg += 1

    # Section answer keys
    page_answer_section_header(c, pg); pg += 1
    for tid in available:
        page_activity(c, cfgs[tid], images[tid], True, pg); pg += 1

    # Notes (pour atteindre 24 pages minimum)
    while pg < 24:
        page_notes(c, pg); pg += 1

    c.save()
    print(f"  ✓ Interior : {pg - 1} pages → {interior_path.name}")

    # Cover
    cover_path = out_dir / "cover_front.pdf"
    build_cover(cover_path, book_title, book_subtitle, main_color)
    print(f"  ✓ Cover front → {cover_path.name}")

    # ZIP
    bundle = out_dir / "kdp_bundle.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(interior_path, "interior.pdf")
        z.write(cover_path, "cover_front.pdf")
    print(f"  ✓ Bundle : {bundle.name} ({bundle.stat().st_size // 1024}ko)")


def main():
    theme_filter = os.environ.get("THEMES", "").strip()
    out_base = Path(os.environ.get("OUT_DIR", str(ROOT / "products" / "kdp" / "books")))

    if theme_filter:
        ids = [t.strip() for t in theme_filter.split(",")]
        book_dir = out_base / "_".join(ids)
        build_book(ids, book_dir)
    else:
        # Un livre multi-thèmes
        all_ids = list(THEMES.keys())
        build_book(all_ids, out_base / "math_color_by_code_bundle")
        # Et un livre par saison
        seasons = {
            "halloween": ["halloween"],
            "christmas": ["christmas", "snowman"],
            "spring":    ["valentine", "back_to_school"],
        }
        for season_name, ids in seasons.items():
            build_book(ids, out_base / season_name)

    print(f"\n[DONE] Livres KDP dans {out_base}/")


if __name__ == "__main__":
    main()
