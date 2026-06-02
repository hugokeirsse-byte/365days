"""
TPT Color-by-Code — Pipeline complet
Génère N packs finis (worksheet + answer key + cover + listing.md + ZIP)

Workflow :
  1. Télécharge un SVG CC0 depuis ASSETS_CC0.md
  2. Dépose-le dans scripts/tpt/themes/<nom>.svg
  3. Lance ce script → pack prêt en 10 secondes

Prérequis :
  pip install reportlab svglib pillow

Clé optionnelle :
  GEMINI_API_KEY — génère les descriptions SEO (gemini-2.5-flash)
                   Sans la clé : listing template utilisé

Usage :
  python scripts/tpt/pipeline_cbc.py              # tous les thèmes
  THEME=halloween python scripts/tpt/pipeline_cbc.py  # un seul
  OUT_DIR=products/tpt/packs python scripts/tpt/pipeline_cbc.py
"""
from __future__ import annotations

import json
import math
import os
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas
from svglib.svglib import svg2rlg

ROOT = Path(__file__).resolve().parent.parent.parent
SVG_DIR = Path(__file__).parent / "themes"
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

PAGE_W, PAGE_H = letter   # 612 × 792 pt
M = 0.5 * inch

AUTHOR = "BrightOwl Learning"

# ──────────────────────────────────────────────────────────────────────────────
# THEMES CONFIG
# ──────────────────────────────────────────────────────────────────────────────

THEMES: dict[str, dict] = {

    "halloween": {
        "title":         "Halloween Multiplication",
        "subtitle":      "Color by Code · Grade 3",
        "grade":         "3",
        "subject":       "Multiplication",
        "price":         3.50,
        "header_hex":    "#E8771A",
        "svg":           "halloween_pumpkin.svg",
        "image_prompt":  (
            "A cute Halloween jack-o-lantern pumpkin coloring page for kids. "
            "Clean BOLD black outlines only on pure white background. No shading, no gray, no color. "
            "Large pumpkin with triangle eyes and jagged smile, green stem on top, "
            "background with a simple moon and stars. Flat cartoon coloring-book style. "
            "Thick distinct outlines separating each region. Pure white background."
        ),
        "colors": [
            (12, "Orange",  "#E8771A"),
            ( 6, "Green",   "#2D7A2D"),
            (24, "Black",   "#111111"),
            (18, "Yellow",  "#FFD700"),
            (15, "Purple",  "#7B2FBE"),
        ],
        "problems": [
            (3,"×",4,12),(4,"×",3,12),
            (2,"×",3, 6),(3,"×",2, 6),
            (8,"×",3,24),(6,"×",4,24),
            (6,"×",3,18),(9,"×",2,18),
            (3,"×",5,15),(5,"×",3,15),
        ],
        # (answer, rx, ry) — rx/ry ratios, ry=0 = TOP of image
        "regions": [
            (12, 0.50, 0.52),  # pumpkin body center
            ( 6, 0.50, 0.12),  # stem top
            (24, 0.34, 0.45),  # left eye
            (24, 0.66, 0.45),  # right eye
            (18, 0.82, 0.14),  # moon
            (15, 0.12, 0.10),  # sky
        ],
        "download_url": "https://freesvg.org/carved-pumpkin-coloring-vector-drawing",
        "tags": ["halloween", "multiplication", "3rd grade", "color by code",
                 "no prep", "October", "math facts", "differentiated"],
    },

    "back_to_school": {
        "title":         "Back to School Addition",
        "subtitle":      "Color by Code · Grade 1",
        "grade":         "1",
        "subject":       "Addition",
        "price":         3.50,
        "header_hex":    "#C0392B",
        "svg":           "apple.svg",
        "image_prompt":  (
            "A cute back-to-school apple coloring page for kids. "
            "Clean BOLD black outlines on pure white background. No shading, no gray, no color. "
            "Big round apple with a leaf on top, a stem, a shine spot on the upper left, "
            "and a cute worm peeking out. Flat cartoon coloring-book style. "
            "Thick distinct outlines separating each region."
        ),
        "colors": [
            ( 9, "Red",    "#C0392B"),
            ( 6, "Green",  "#27AE60"),
            ( 4, "Brown",  "#795548"),
            (12, "Yellow", "#F1C40F"),
            (15, "Blue",   "#2980B9"),
        ],
        "problems": [
            (4,"+",5, 9),(3,"+",6, 9),
            (3,"+",3, 6),(4,"+",2, 6),
            (2,"+",2, 4),(3,"+",1, 4),
            (6,"+",6,12),(5,"+",7,12),
            (8,"+",7,15),(9,"+",6,15),
        ],
        "regions": [
            ( 9, 0.50, 0.55),  # apple body center
            ( 6, 0.65, 0.18),  # leaf
            ( 4, 0.50, 0.10),  # stem
            (12, 0.35, 0.38),  # shine spot
            (15, 0.10, 0.10),  # sky background
        ],
        "download_url": "https://freesvg.org/apple-outline",
        "tags": ["back to school", "addition", "1st grade", "color by code",
                 "no prep", "August", "September", "apple", "math"],
    },

    "christmas": {
        "title":         "Christmas Subtraction",
        "subtitle":      "Color by Code · Grade 2",
        "grade":         "2",
        "subject":       "Subtraction",
        "price":         3.50,
        "header_hex":    "#C0392B",
        "svg":           "christmas_tree.svg",
        "image_prompt":  (
            "A cute Christmas tree coloring page for kids. "
            "Clean BOLD black outlines on pure white background. No shading, no gray, no color. "
            "Decorated Christmas tree with 3 tiers, round ornaments, a star on top, "
            "a trunk, and snow on the ground. Flat cartoon coloring-book style. "
            "Thick distinct outlines separating each region."
        ),
        "colors": [
            ( 8, "Green",  "#27AE60"),
            ( 4, "Brown",  "#795548"),
            (12, "Red",    "#C0392B"),
            ( 6, "Yellow", "#F1C40F"),
            (15, "Blue",   "#2980B9"),
        ],
        "problems": [
            (15,"-", 7, 8),(16,"-", 8, 8),
            ( 9,"-", 5, 4),(10,"-", 6, 4),
            (18,"-", 6,12),(20,"-", 8,12),
            (10,"-", 4, 6),( 8,"-", 2, 6),
            (20,"-", 5,15),(19,"-", 4,15),
        ],
        "regions": [
            ( 8, 0.50, 0.52),  # tree body center
            ( 4, 0.50, 0.88),  # trunk
            (12, 0.38, 0.62),  # ornament left
            ( 6, 0.50, 0.06),  # star top
            (15, 0.10, 0.10),  # background sky
        ],
        "download_url": "https://freesvg.org/christmas-tree-drawing",
        "tags": ["christmas", "subtraction", "2nd grade", "color by code",
                 "no prep", "December", "winter", "math facts"],
    },

    "valentine": {
        "title":         "Valentine's Day Addition",
        "subtitle":      "Color by Code · Kindergarten",
        "grade":         "K",
        "subject":       "Addition",
        "price":         3.00,
        "header_hex":    "#D6336C",
        "svg":           "valentine_heart.svg",
        "image_prompt":  (
            "A cute Valentine's Day heart coloring page for kindergarten kids. "
            "Clean BOLD black outlines on pure white background. No shading, no gray. "
            "Large heart with a smaller heart inside, cute kawaii face, "
            "bow on top, small stars and dots around. Flat cartoon coloring-book style."
        ),
        "colors": [
            (8, "Red",    "#C0392B"),
            (4, "Pink",   "#F48FB1"),
            (6, "Purple", "#7B2FBE"),
            (3, "Yellow", "#F1C40F"),
            (5, "Blue",   "#2980B9"),
        ],
        "problems": [
            (4,"+",4,8),(5,"+",3,8),
            (2,"+",2,4),(3,"+",1,4),
            (3,"+",3,6),(4,"+",2,6),
            (1,"+",2,3),(2,"+",1,3),
            (2,"+",3,5),(4,"+",1,5),
        ],
        "regions": [
            (8, 0.50, 0.58),  # main heart body
            (4, 0.50, 0.72),  # inner heart
            (6, 0.12, 0.12),  # background star
            (3, 0.85, 0.12),  # background star right
            (5, 0.50, 0.22),  # bow center
        ],
        "download_url": "https://freesvg.org/heart-outline",
        "tags": ["valentine's day", "addition", "kindergarten", "color by code",
                 "no prep", "February", "heart", "math"],
    },

    "snowman": {
        "title":         "Winter Snowman Addition",
        "subtitle":      "Color by Code · Grade 2",
        "grade":         "2",
        "subject":       "Addition",
        "price":         3.50,
        "header_hex":    "#2980B9",
        "svg":           "snowman.svg",
        "image_prompt":  (
            "A cute winter snowman coloring page for kids. "
            "Clean BOLD black outlines on pure white background. No shading, no gray. "
            "Three-ball snowman with top hat, scarf, carrot nose, button eyes, twig arms, "
            "snowflakes in background, snow on ground. Flat cartoon coloring-book style."
        ),
        "colors": [
            (10, "Light Blue", "#AED6F1"),
            ( 4, "Black",      "#2C3E50"),
            ( 6, "Orange",     "#E67E22"),
            ( 8, "Red",        "#C0392B"),
            (12, "Dark Blue",  "#1A5276"),
        ],
        "problems": [
            (5,"+",5,10),(6,"+",4,10),
            (2,"+",2, 4),(3,"+",1, 4),
            (3,"+",3, 6),(5,"+",1, 6),
            (4,"+",4, 8),(6,"+",2, 8),
            (7,"+",5,12),(8,"+",4,12),
        ],
        "regions": [
            (10, 0.50, 0.72),  # bottom snowball
            (10, 0.50, 0.50),  # middle snowball
            (10, 0.50, 0.33),  # head
            ( 4, 0.50, 0.15),  # hat
            ( 6, 0.50, 0.45),  # carrot nose
            ( 8, 0.50, 0.42),  # scarf
            (12, 0.10, 0.10),  # sky background
        ],
        "download_url": "https://freesvg.org/snowman-vector-clip-art-graphics",
        "tags": ["winter", "snowman", "addition", "2nd grade", "color by code",
                 "no prep", "December", "January", "math"],
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# GEMINI — texte uniquement (SEO listings)
# ──────────────────────────────────────────────────────────────────────────────

def _gemini_text(prompt: str, model: str = "gemini-2.5-flash") -> str | None:
    if not GEMINI_KEY:
        return None
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={GEMINI_KEY}")
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read())
    except Exception as exc:
        print(f"  [Gemini text] erreur: {exc}")
        return None
    for cand in resp.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            if "text" in part:
                return part["text"]
    return None


# ──────────────────────────────────────────────────────────────────────────────
# IMAGE — get or generate
# ──────────────────────────────────────────────────────────────────────────────

def get_image(theme_id: str, cfg: dict, out_dir: Path) -> Path:
    """
    Cherche l'image CC0 dans scripts/tpt/themes/.
    Formats acceptés : .svg (priorité), .png, .jpg
    Si PNG/JPG → upscale automatique à 300 DPI équivalent.
    Si absent → erreur claire avec lien de téléchargement.
    """
    svg_name = cfg["svg"]
    base = svg_name.rsplit(".", 1)[0]

    # Cherche SVG en priorité (vectoriel = qualité parfaite)
    for ext in (".svg", ".png", ".jpg", ".jpeg"):
        candidate = SVG_DIR / (base + ext)
        if candidate.exists():
            if ext in (".png", ".jpg", ".jpeg"):
                return _upscale_png(candidate, out_dir)
            return candidate

    # Introuvable → message clair
    dl_url = cfg.get("download_url", "voir ASSETS_CC0.md")
    raise FileNotFoundError(
        f"\n  ✗ Image manquante pour '{theme_id}'\n"
        f"  → Télécharge le SVG CC0 : {dl_url}\n"
        f"  → Dépose-le ici          : scripts/tpt/themes/{svg_name}\n"
        f"  → Puis relance           : python scripts/tpt/pipeline_cbc.py\n"
    )


def _upscale_png(src: Path, out_dir: Path) -> Path:
    """
    Upscale un PNG à 3× via Lanczos (300 DPI pour impression).
    Résultat mis en cache dans out_dir/coloring_upscaled.png.
    """
    from PIL import Image
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / "coloring_upscaled.png"
    if dst.exists():
        return dst
    img = Image.open(src).convert("RGBA")
    w, h = img.size
    scale = max(1, min(4, 1800 // min(w, h)))   # cible ~1800px côté court
    if scale > 1:
        img = img.resize((w * scale, h * scale), Image.LANCZOS)
        print(f"  → Upscale ×{scale} ({w}×{h} → {w*scale}×{h*scale})")
    img.save(dst, dpi=(300, 300))
    return dst


# ──────────────────────────────────────────────────────────────────────────────
# DRAW PRIMITIVES
# ──────────────────────────────────────────────────────────────────────────────

def _lbl(c, x, y, text, size=11, col=black, bold=False):
    c.saveState()
    c.setFillColor(col)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawCentredString(x, y, text)
    c.restoreState()


def _embed_image(c, img_path: Path, x, y, max_w, max_h):
    """Intègre une image (SVG ou PNG) dans le canvas, centrée dans la zone."""
    suffix = img_path.suffix.lower()

    if suffix == ".svg":
        drawing = svg2rlg(str(img_path))
        if drawing is None:
            return 0, 0
        scale = min(max_w / drawing.width, max_h / drawing.height)
        dw = drawing.width * scale
        dh = drawing.height * scale
        ox = x + (max_w - dw) / 2
        oy = y + (max_h - dh) / 2
        drawing.width = dw
        drawing.height = dh
        drawing.transform = (scale, 0, 0, scale, 0, 0)
        renderPDF.draw(drawing, c, ox, oy)
        return ox, oy, dw, dh

    else:  # PNG / JPEG
        from reportlab.lib.utils import ImageReader
        img = ImageReader(str(img_path))
        iw, ih = img.getSize()
        scale = min(max_w / iw, max_h / ih)
        dw, dh = iw * scale, ih * scale
        ox = x + (max_w - dw) / 2
        oy = y + (max_h - dh) / 2
        c.drawImage(str(img_path), ox, oy, dw, dh, mask="auto")
        return ox, oy, dw, dh


def _overlay_region_labels(c, cfg, img_x, img_y, img_w, img_h):
    """Overlaye les chiffres-réponses sur l'image de coloriage."""
    ans_map = {ans: (name, HexColor(hex_)) for ans, name, hex_ in cfg["colors"]}

    # Badge style: petit cercle blanc avec bordure colorée + chiffre en gras
    for ans, rx, ry in cfg["regions"]:
        label_x = img_x + rx * img_w
        # ry=0 est le haut de l'image → en PDF: img_y + img_h * (1 - ry)
        label_y = img_y + img_h * (1 - ry)

        _, col = ans_map[ans]

        # Fond blanc + contour coloré
        c.saveState()
        c.setFillColor(white)
        c.setStrokeColor(col)
        c.setLineWidth(2)
        c.circle(label_x, label_y, 12, fill=1, stroke=1)
        # Chiffre
        c.setFillColor(col)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(label_x, label_y - 4, str(ans))
        c.restoreState()


def _key_strip(c, x, y, w, h, cfg):
    """Bandeau horizontal de la color key."""
    c.saveState()
    c.setFillColor(HexColor("#FFF8E7"))
    c.setStrokeColor(HexColor(cfg["header_hex"]))
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 4, fill=1, stroke=1)

    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(black)
    c.drawString(x + 6, y + h/2 - 4, "COLOR KEY:")
    sw = 12
    reserve = 78
    item_w = (w - reserve) / len(cfg["colors"])
    for i, (ans, name, hex_) in enumerate(cfg["colors"]):
        ix = x + reserve + i * item_w
        iy = y + h/2 - sw/2
        c.setFillColor(HexColor(hex_))
        c.setStrokeColor(HexColor("#555"))
        c.setLineWidth(0.5)
        c.rect(ix, iy, sw, sw, fill=1, stroke=1)
        c.setFillColor(black)
        c.setFont("Helvetica", 7.5)
        c.drawString(ix + sw + 3, iy + 1, f"{ans}={name}")
    c.restoreState()


def _problems_panel(c, x, y, w, h, cfg, show_answers):
    """Panneau droit : instructions + 10 problèmes en 2 colonnes."""
    ans_map = {ans: (name, HexColor(hex_)) for ans, name, hex_ in cfg["colors"]}
    col_hdr = HexColor(cfg["header_hex"])

    _lbl(c, x + w/2, y + h - 14, "Solve. Find the color.", 9, black, bold=True)
    _lbl(c, x + w/2, y + h - 26, "Color the picture!", 9, black, bold=True)

    bh, gap = 32, 4
    col_w = w / 2 - 5

    for i, (a, op, b, ans) in enumerate(cfg["problems"]):
        ci = i // 5
        ri = i % 5
        bx = x + ci * (col_w + 10)
        by = y + h - 38 - ri * (bh + gap)

        # Fond alternant
        c.saveState()
        c.setFillColor(HexColor("#F7F3FF") if ri % 2 == 0 else white)
        c.rect(bx, by - bh, col_w, bh, fill=1, stroke=0)
        c.restoreState()

        # Badge numéro
        c.saveState()
        c.setFillColor(col_hdr)
        c.circle(bx + 10, by - bh/2, 8, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(bx + 10, by - bh/2 - 3, str(i+1))
        c.restoreState()

        # Equation
        c.setFillColor(black)
        c.setFont("Helvetica", 13)
        c.drawString(bx + 23, by - bh/2 - 5, f"{a} {op} {b} =")

        # Case réponse
        bax = bx + col_w - 26
        bay = by - bh + 6
        c.saveState()
        c.setStrokeColor(HexColor("#AAAAAA"))
        c.setLineWidth(0.8)
        c.rect(bax, bay, 21, 19, fill=0, stroke=1)
        if show_answers:
            _, acol = ans_map[ans]
            c.setFillColor(acol)
            c.rect(bax, bay, 21, 19, fill=1, stroke=1)
            txt_col = white if ans in (4, 24) and cfg.get("dark_answers") else black
            # Use white text on dark colors
            _, aname, ahex = next(
                (x for x in cfg["colors"] if x[0] == ans), (ans, "", "#000"))
            r = int(ahex[1:3], 16)
            g = int(ahex[3:5], 16)
            b_ = int(ahex[5:7], 16)
            brightness = (r*299 + g*587 + b_*114) / 1000
            txt_col = white if brightness < 128 else black
            c.setFillColor(txt_col)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(bax + 10, bay + 4, str(ans))
        c.restoreState()


def _cover_page(c, cfg, out_dir):
    """Page cover simple, style TPT."""
    hx = HexColor(cfg["header_hex"])
    light = HexColor(_lighten(cfg["header_hex"]))

    c.setFillColor(light)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setStrokeColor(hx)
    c.setLineWidth(6)
    c.roundRect(M, M, PAGE_W-2*M, PAGE_H-2*M, 16, fill=0, stroke=1)

    # Bandeau titre
    bh = 2.2 * inch
    by = PAGE_H - M - 1.0*inch - bh
    c.setFillColor(hx)
    c.roundRect(M+0.4*inch, by, PAGE_W-2*M-0.8*inch, bh, 12, fill=1, stroke=0)
    c.setFillColor(white)
    words = (cfg["title"] + " Color by Code").split()
    mid = len(words) // 2
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(PAGE_W/2, by + bh - 0.72*inch, " ".join(words[:mid]))
    c.drawCentredString(PAGE_W/2, by + bh - 1.28*inch, " ".join(words[mid:]))
    c.setFont("Helvetica", 15)
    c.drawCentredString(PAGE_W/2, by + 0.42*inch, cfg["subtitle"])

    bullets = [
        "10 Problems — 5 Color Regions",
        "Answer Key Included",
        "No Prep — Just Print & Go",
        "Print-Ready 8.5 x 11 (US Letter)",
    ]
    c.setFillColor(black)
    yb = by - 0.88*inch
    for blt in bullets:
        c.setFillColor(hx)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(M + 1.0*inch, yb, "✓")
        c.setFillColor(black)
        c.setFont("Helvetica", 14)
        c.drawString(M + 1.35*inch, yb, blt)
        yb -= 0.50*inch

    c.setFont("Helvetica-Oblique", 12)
    c.setFillColor(HexColor("#666"))
    c.drawCentredString(PAGE_W/2, M + 0.4*inch, f"by {AUTHOR}")


def _lighten(hex_: str) -> str:
    """Eclaircit une couleur hex (mélange 85% blanc)."""
    r = int(hex_[1:3], 16)
    g = int(hex_[3:5], 16)
    b = int(hex_[5:7], 16)
    r2 = int(r + (255-r) * 0.82)
    g2 = int(g + (255-g) * 0.82)
    b2 = int(b + (255-b) * 0.82)
    return f"#{r2:02X}{g2:02X}{b2:02X}"


# ──────────────────────────────────────────────────────────────────────────────
# PAGE BUILDER
# ──────────────────────────────────────────────────────────────────────────────

def build_worksheet(path: Path, cfg: dict, img_path: Path, show_answers: bool):
    c = rl_canvas.Canvas(str(path), pagesize=letter)
    hx = HexColor(cfg["header_hex"])

    # Header
    hh = 0.65 * inch
    hy = PAGE_H - M - hh
    c.setFillColor(hx)
    c.roundRect(M, hy, PAGE_W-2*M, hh, 8, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    title = f"{cfg['title']} — Color by Code"
    if show_answers:
        title += "  (ANSWER KEY)"
    c.drawCentredString(PAGE_W/2, hy + hh/2 - 5, title)
    c.setFont("Helvetica", 10)
    c.drawCentredString(PAGE_W/2, hy + 7, cfg["subtitle"])

    # Name / Date
    ny = hy - 0.28*inch
    c.setFillColor(black)
    c.setFont("Helvetica", 10)
    c.drawString(M, ny, "Name: _______________________________")
    c.drawRightString(PAGE_W-M, ny, "Date: _________________")

    # Color key strip
    ky = ny - 0.22*inch - 0.28*inch
    _key_strip(c, M, ky, PAGE_W-2*M, 0.28*inch, cfg)

    # Content area
    ct_top = ky - 0.10*inch
    ct_bot = 0.48*inch
    ct_h = ct_top - ct_bot

    total_w = PAGE_W - 2*M
    scene_w = total_w * 0.56
    prob_w  = total_w - scene_w - 0.10*inch

    # Draw coloring image + overlay
    result = _embed_image(c, img_path, M, ct_bot, scene_w, ct_h)
    if len(result) == 4:
        ox, oy, dw, dh = result
        _overlay_region_labels(c, cfg, ox, oy, dw, dh)

    # Problems
    _problems_panel(c, M + scene_w + 0.10*inch, ct_bot, prob_w, ct_h, cfg, show_answers)

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(HexColor("#999"))
    c.drawString(M, 0.26*inch, f"© {datetime.now().year} {AUTHOR}  —  For single classroom use only.")
    c.drawRightString(PAGE_W-M, 0.26*inch, "365days · No Prep · Just Print")

    c.showPage()
    c.save()


def build_cover(path: Path, cfg: dict):
    c = rl_canvas.Canvas(str(path), pagesize=letter)
    _cover_page(c, cfg, path.parent)
    c.showPage()
    c.save()


# ──────────────────────────────────────────────────────────────────────────────
# SEO LISTING
# ──────────────────────────────────────────────────────────────────────────────

LISTING_TEMPLATE = """\
# TPT LISTING — {id}

## Titre SEO
{title} Color by Code Worksheets {grade}{ord} Grade — {subject} Practice No Prep

## Prix
${price:.2f}

## Description
Make {subject_lower} practice FUN and engaging with this **color by code** worksheet!
Students solve each problem, find the answer in the color key, and color the picture.
Perfect for {season_hint} — no prep required, just print and go!

**What's included:**
- 1 color-by-code worksheet (10 problems, 5 color regions)
- Answer key
- Cover page
- Terms of use

**Perfect for:** morning work, early finishers, math centers, homework, sub plans.

## Tags
{tags}

## Standards (Common Core)
{cc_standards}
"""

CC_STANDARDS = {
    "Multiplication": "3.OA.C.7 — Fluently multiply within 100",
    "Addition":       "1.OA.C.6 — Add within 20; K.OA.A.5 — Fluently add within 5",
    "Subtraction":    "2.OA.B.2 — Fluently subtract within 20",
}


def _ordinal(grade: str) -> str:
    try:
        n = int(grade)
        return {1:"st",2:"nd",3:"rd"}.get(n, "th")
    except ValueError:
        return ""


def generate_listing(cfg: dict, theme_id: str, out_dir: Path):
    # Try Gemini for richer SEO
    if GEMINI_KEY:
        prompt = (
            f"Write a Teachers Pay Teachers product listing for this resource:\n"
            f"Title: {cfg['title']} Color by Code\n"
            f"Grade: {cfg['grade']}\nSubject: {cfg['subject']}\n"
            f"Format: color-by-code worksheet (student solves math, colors picture based on answer)\n"
            f"Content: 10 problems, 5 color regions, answer key included, no prep\n\n"
            f"Write:\n1. An SEO-optimized title (under 80 chars, include grade + subject + 'color by code' + 'no prep')\n"
            f"2. A 100-word description (engaging, teacher-focused, bullet points for what's included)\n"
            f"3. 12 TPT search tags (comma-separated)\n"
            f"Format your response as:\nTITLE: ...\nDESCRIPTION: ...\nTAGS: ..."
        )
        text = _gemini_text(prompt)
        if text:
            listing_path = out_dir / "listing.md"
            listing_path.write_text(f"# TPT LISTING — {theme_id}\n\n{text}\n", encoding="utf-8")
            print(f"  → Listing Gemini généré")
            return

    # Fallback template
    grade = cfg["grade"]
    listing = LISTING_TEMPLATE.format(
        id=theme_id,
        title=cfg["title"],
        grade=grade,
        ord=_ordinal(grade),
        subject=cfg["subject"],
        subject_lower=cfg["subject"].lower(),
        price=cfg["price"],
        season_hint=cfg["tags"][0] if cfg["tags"] else "any season",
        tags=", ".join(cfg["tags"]),
        cc_standards=CC_STANDARDS.get(cfg["subject"], ""),
    )
    (out_dir / "listing.md").write_text(listing, encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────────────
# TERMS
# ──────────────────────────────────────────────────────────────────────────────

def build_terms(path: Path, cfg: dict):
    c = rl_canvas.Canvas(str(path), pagesize=letter)
    hx = HexColor(cfg["header_hex"])

    hh = 0.65*inch
    hy = PAGE_H - M - hh
    c.setFillColor(hx)
    c.roundRect(M, hy, PAGE_W-2*M, hh, 8, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(PAGE_W/2, hy + hh/2 - 5, "Terms of Use")

    lines = [
        "", "PERMITTED:",
        "  • Use with your own students in your own classroom.",
        "  • Print as many copies as needed for your students.",
        "  • Save on a password-protected personal device.",
        "", "NOT PERMITTED:",
        "  • Sharing, selling, or redistributing this resource.",
        "  • Posting to shared drives, websites, or social media.",
        "  • Claiming this resource as your own.",
        "",
        "Each license is for one classroom. Purchase additional licenses",
        "for your grade-level team (available at a discount).",
        "",
        f"© {datetime.now().year} {AUTHOR}. All rights reserved.",
    ]
    ty = hy - 0.5*inch
    c.setFillColor(black)
    c.setFont("Helvetica", 11)
    for ln in lines:
        c.drawString(M, ty, ln)
        ty -= 0.28*inch

    c.showPage()
    c.save()


# ──────────────────────────────────────────────────────────────────────────────
# PIPELINE
# ──────────────────────────────────────────────────────────────────────────────

def run_theme(theme_id: str, cfg: dict, base_out: Path):
    out = base_out / theme_id
    out.mkdir(parents=True, exist_ok=True)
    print(f"\n{'='*60}")
    print(f"  Thème : {theme_id}  ({cfg['title']})")
    print(f"{'='*60}")

    # 1. Image
    try:
        img_path = get_image(theme_id, cfg, out)
        print(f"  ✓ Image : {img_path.name}")
    except FileNotFoundError as e:
        print(f"  ✗ Image introuvable : {e}")
        return

    # 2. PDFs
    ws  = out / "worksheet.pdf"
    ak  = out / "answer_key.pdf"
    cov = out / "cover.pdf"
    trm = out / "terms.pdf"

    build_worksheet(ws,  cfg, img_path, show_answers=False)
    build_worksheet(ak,  cfg, img_path, show_answers=True)
    build_cover(cov, cfg)
    build_terms(trm, cfg)
    print(f"  ✓ PDFs : worksheet, answer_key, cover, terms")

    # 3. Listing
    generate_listing(cfg, theme_id, out)
    print(f"  ✓ Listing : listing.md")

    # 4. ZIP
    bundle = out / "bundle.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in ("cover.pdf", "worksheet.pdf", "answer_key.pdf", "terms.pdf", "listing.md"):
            fp = out / fn
            if fp.exists():
                z.write(fp, fn)
    print(f"  ✓ Bundle : bundle.zip ({bundle.stat().st_size//1024}ko)")


def main():
    only_theme = os.environ.get("THEME", "").strip()
    out_dir = Path(os.environ.get("OUT_DIR", str(ROOT / "products" / "tpt" / "packs")))
    out_dir.mkdir(parents=True, exist_ok=True)

    themes_to_run = {k: v for k, v in THEMES.items()
                     if not only_theme or k == only_theme}

    print(f"Gemini API : {'✓ disponible' if GEMINI_KEY else '✗ absent (fallback SVG + template listing)'}")
    print(f"Thèmes à produire : {list(themes_to_run.keys())}")

    for tid, cfg in themes_to_run.items():
        run_theme(tid, cfg, out_dir)

    print(f"\n[DONE] Packs dans {out_dir}/")


if __name__ == "__main__":
    main()
