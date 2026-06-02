"""
TPT Math Drills Generator — Fiches d'exercices pro (sans image requise)
Design : Nunito, cells arrondies, badges numérotés, thèmes saisonniers.
Produit : worksheet.pdf (3 niveaux) + answer_key.pdf + cover.pdf + listing.md + ZIP

Types produits :
  drill_25   — 25 problèmes, grille 5×5
  drill_40   — 40 problèmes, grille 5×8 (format "sprint")
  mixed_ops  — 4 opérations mélangées

Usage :
  python scripts/tpt/generators/math_drills.py
  THEME=christmas OP=add GRADE=2 python scripts/tpt/generators/math_drills.py
"""
from __future__ import annotations

import json
import os
import random
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONTS_DIR = Path(__file__).parent.parent / "fonts"

def _register_fonts():
    for name, fname in [
        ("Nunito",          "Nunito-Regular.ttf"),
        ("Nunito-Bold",     "Nunito-Bold.ttf"),
        ("Nunito-SemiBold", "Nunito-SemiBold.ttf"),
    ]:
        path = FONTS_DIR / fname
        if path.exists():
            pdfmetrics.registerFont(TTFont(name, str(path)))
        else:
            # Fallback Helvetica
            from reportlab.lib.fonts import addMapping
            _FALLBACK = {"Nunito": "Helvetica", "Nunito-Bold": "Helvetica-Bold",
                         "Nunito-SemiBold": "Helvetica"}
            pdfmetrics.registerFont(pdfmetrics.getFont(_FALLBACK.get(name, "Helvetica")))

_register_fonts()

PAGE_W, PAGE_H = letter
M = 0.55 * inch

GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# ── Theme configs ──────────────────────────────────────────────────────────────
THEMES = {
    "halloween": {
        "label":    "Halloween",
        "primary":  "#E8771A",
        "dark":     "#A04500",
        "light":    "#FFF3E8",
        "accent":   "#7B2FBE",
        "deco":     "pumpkin",   # forme décorative
        "months":   "September–October",
    },
    "christmas": {
        "label":    "Christmas",
        "primary":  "#C0392B",
        "dark":     "#922B21",
        "light":    "#FFEEEE",
        "accent":   "#1E8449",
        "deco":     "star",
        "months":   "November–December",
    },
    "back_to_school": {
        "label":    "Back to School",
        "primary":  "#2980B9",
        "dark":     "#1A6B9A",
        "light":    "#EBF5FB",
        "accent":   "#F39C12",
        "deco":     "pencil",
        "months":   "August–September",
    },
    "valentine": {
        "label":    "Valentine's Day",
        "primary":  "#D6336C",
        "dark":     "#A0255A",
        "light":    "#FDE8F0",
        "accent":   "#E91E8C",
        "deco":     "heart",
        "months":   "January–February",
    },
    "spring": {
        "label":    "Spring",
        "primary":  "#2E9E5B",
        "dark":     "#1A7040",
        "light":    "#E8F8EF",
        "accent":   "#F1C40F",
        "deco":     "flower",
        "months":   "March–May",
    },
    "winter": {
        "label":    "Winter",
        "primary":  "#1A6B9A",
        "dark":     "#0D4E75",
        "light":    "#EBF5FB",
        "accent":   "#AED6F1",
        "deco":     "snowflake",
        "months":   "December–January",
    },
    "thanksgiving": {
        "label":    "Thanksgiving",
        "primary":  "#C0652B",
        "dark":     "#8E4A20",
        "light":    "#FDF0E8",
        "accent":   "#F4A236",
        "deco":     "leaf",
        "months":   "October–November",
    },
    "plain": {
        "label":    "Math Practice",
        "primary":  "#2C3E50",
        "dark":     "#1A252F",
        "light":    "#F4F6F7",
        "accent":   "#2980B9",
        "deco":     "star",
        "months":   "Year-round",
    },
}

# ── Operations ────────────────────────────────────────────────────────────────
OPS = {
    "add": {"sym": "+",  "name": "Addition",       "verb": "adding"},
    "sub": {"sym": "−",  "name": "Subtraction",    "verb": "subtracting"},
    "mul": {"sym": "×",  "name": "Multiplication", "verb": "multiplying"},
    "div": {"sym": "÷",  "name": "Division",       "verb": "dividing"},
}

LEVELS = {
    "support":   {"label": "Level 1 · Support",   "emoji": "⭐"},
    "on_level":  {"label": "Level 2 · On Level",  "emoji": "⭐⭐"},
    "challenge": {"label": "Level 3 · Challenge", "emoji": "⭐⭐⭐"},
}

RANGES = {
    "support":   {"add": (1,10),   "sub": (1,10),   "mul": (2,5),   "div": (1,5)},
    "on_level":  {"add": (10,50),  "sub": (10,50),  "mul": (2,10),  "div": (2,10)},
    "challenge": {"add": (50,199), "sub": (50,199), "mul": (3,12),  "div": (3,12)},
}

# ── Problem generation ─────────────────────────────────────────────────────────

def gen_problems(op: str, level: str, seed: int, count: int = 25) -> list[tuple]:
    rng = random.Random(seed)
    lo, hi = RANGES[level][op]
    problems = []
    seen = set()
    attempts = 0
    while len(problems) < count and attempts < count * 10:
        attempts += 1
        if op == "add":
            a, b = rng.randint(lo, hi), rng.randint(lo, hi)
            ans = a + b
        elif op == "sub":
            a, b = rng.randint(lo, hi), rng.randint(lo, hi)
            if b > a: a, b = b, a
            if a == b and lo > 0: continue
            ans = a - b
        elif op == "mul":
            a, b = rng.randint(lo, hi), rng.randint(lo, hi)
            ans = a * b
        elif op == "div":
            b = rng.randint(max(1, lo), hi)
            q = rng.randint(max(1, lo), hi)
            a = b * q
            ans = q
        else:
            raise ValueError(f"op inconnue: {op}")
        key = (a, b)
        if key in seen:
            continue
        seen.add(key)
        problems.append((a, OPS[op]["sym"], b, ans))
    return problems


# ── Decorative shapes ──────────────────────────────────────────────────────────

def _draw_deco(c, deco: str, x: float, y: float, size: float, color: HexColor, alpha: float = 0.25):
    """Dessine une forme décorative (sans image) à la position x,y."""
    import math
    c.saveState()
    c.setFillColor(color)
    c.setStrokeColor(color)
    c.setFillAlpha(alpha)
    c.setStrokeAlpha(alpha)

    if deco == "pumpkin":
        # Cercle principal
        c.circle(x, y, size * 0.45, fill=1, stroke=0)
        # Tige
        c.setLineWidth(size * 0.08)
        c.line(x, y + size * 0.45, x, y + size * 0.65)
    elif deco == "star":
        pts = []
        for i in range(10):
            angle = math.radians(90 - i * 36)
            r = size * 0.5 if i % 2 == 0 else size * 0.2
            pts.append((x + r * math.cos(angle), y + r * math.sin(angle)))
        p = c.beginPath()
        p.moveTo(*pts[0])
        for pt in pts[1:]: p.lineTo(*pt)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    elif deco == "heart":
        # Deux cercles + triangle
        r = size * 0.22
        c.circle(x - r * 0.9, y + size * 0.05, r, fill=1, stroke=0)
        c.circle(x + r * 0.9, y + size * 0.05, r, fill=1, stroke=0)
        p = c.beginPath()
        p.moveTo(x, y - size * 0.38)
        p.lineTo(x - size * 0.42, y + size * 0.08)
        p.lineTo(x + size * 0.42, y + size * 0.08)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    elif deco == "snowflake":
        c.setLineWidth(size * 0.07)
        for angle_deg in range(0, 180, 30):
            angle = math.radians(angle_deg)
            dx, dy = math.cos(angle) * size * 0.45, math.sin(angle) * size * 0.45
            c.line(x - dx, y - dy, x + dx, y + dy)
    elif deco == "pencil":
        # Rectangle corps + triangle pointe
        c.rect(x - size*0.12, y - size*0.4, size*0.24, size*0.65, fill=1, stroke=0)
        p = c.beginPath()
        p.moveTo(x - size*0.12, y - size*0.4)
        p.lineTo(x + size*0.12, y - size*0.4)
        p.lineTo(x, y - size*0.65)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    elif deco == "flower":
        # Pétales
        for angle_deg in range(0, 360, 45):
            angle = math.radians(angle_deg)
            px_ = x + math.cos(angle) * size * 0.28
            py_ = y + math.sin(angle) * size * 0.28
            c.circle(px_, py_, size * 0.2, fill=1, stroke=0)
        c.setFillAlpha(min(1.0, alpha * 1.5))
        c.circle(x, y, size * 0.15, fill=1, stroke=0)
    elif deco == "leaf":
        p = c.beginPath()
        p.moveTo(x, y - size*0.5)
        p.curveTo(x + size*0.4, y - size*0.2, x + size*0.4, y + size*0.2, x, y + size*0.5)
        p.curveTo(x - size*0.4, y + size*0.2, x - size*0.4, y - size*0.2, x, y - size*0.5)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def _deco_corners(c, deco: str, color: HexColor, size: float = 28, alpha: float = 0.18):
    """4 décorations dans les coins de la page."""
    margin = M + size * 0.6
    for cx, cy in [
        (margin, margin),
        (PAGE_W - margin, margin),
        (margin, PAGE_H - margin),
        (PAGE_W - margin, PAGE_H - margin),
    ]:
        _draw_deco(c, deco, cx, cy, size, color, alpha)


def _deco_row(c, deco: str, color: HexColor, y: float, count: int = 7, alpha: float = 0.12):
    """Rangée de décorations espacées horizontalement."""
    step = (PAGE_W - 2 * M) / (count - 1)
    for i in range(count):
        _draw_deco(c, deco, M + i * step, y, 14, color, alpha)


# ── Canvas helpers ─────────────────────────────────────────────────────────────

def _header(c, title: str, subtitle: str, theme: dict) -> float:
    """Bandeau titre. Retourne y juste en dessous."""
    hx = HexColor(theme["primary"])
    hh = 0.72 * inch
    hy = PAGE_H - M - hh
    # Fond
    c.setFillColor(hx)
    c.roundRect(M, hy, PAGE_W - 2*M, hh, 10, fill=1, stroke=0)
    # Déco dans le bandeau (gauche + droite)
    _draw_deco(c, theme["deco"], M + 0.45*inch, hy + hh/2, 22,
               HexColor(theme["light"]), alpha=0.5)
    _draw_deco(c, theme["deco"], PAGE_W - M - 0.45*inch, hy + hh/2, 22,
               HexColor(theme["light"]), alpha=0.5)
    # Titre
    c.setFillColor(white)
    c.setFont("Nunito-Bold", 19)
    c.drawCentredString(PAGE_W/2, hy + hh/2 + 4, title)
    c.setFont("Nunito", 10)
    c.drawCentredString(PAGE_W/2, hy + 8, subtitle)
    return hy - 0.20 * inch


def _nameline(c, y: float, theme: dict):
    """Ligne Name / Date / Score."""
    hx = HexColor(theme["primary"])
    lh = 0.32 * inch
    c.setFillColor(HexColor(theme["light"]))
    c.roundRect(M, y - lh, PAGE_W - 2*M, lh, 6, fill=1, stroke=0)
    c.setStrokeColor(hx)
    c.setLineWidth(0.8)
    c.roundRect(M, y - lh, PAGE_W - 2*M, lh, 6, fill=0, stroke=1)
    c.setFont("Nunito", 10)
    c.setFillColor(HexColor(theme["dark"]))
    parts = [
        (M + 0.12*inch, "Name:"),
        (PAGE_W*0.55, "Date:"),
        (PAGE_W*0.78, "Score:"),
    ]
    for px, label in parts:
        c.drawString(px, y - lh + 0.09*inch, label)
        # Ligne de réponse
        lx = px + c.stringWidth(label, "Nunito", 10) + 5
        ex = px + (0.24 * PAGE_W if label == "Name:" else 0.16 * PAGE_W)
        c.setStrokeColor(HexColor(theme["primary"]))
        c.setLineWidth(0.6)
        c.line(lx, y - lh + 0.09*inch, min(ex, PAGE_W - M - 5), y - lh + 0.09*inch)
    return y - lh - 0.14 * inch


def _footer(c, theme: dict, page_num: int = 0):
    c.saveState()
    c.setFont("Nunito", 7.5)
    c.setFillColor(HexColor("#AAAAAA"))
    c.drawString(M, 0.25*inch, f"© {datetime.now().year} BrightOwl Learning  —  For single classroom use only.")
    c.drawRightString(PAGE_W - M, 0.25*inch, "brightowllearning.com · No Prep · Just Print")
    if page_num:
        c.drawCentredString(PAGE_W/2, 0.25*inch, str(page_num))
    c.restoreState()


# ── Problem grid ───────────────────────────────────────────────────────────────

def _problem_grid(c, problems: list, start_y: float, is_key: bool, theme: dict,
                  cols: int = 5):
    """Grille de problèmes stylisée. Retourne la hauteur utilisée."""
    hx    = HexColor(theme["primary"])
    dk    = HexColor(theme["dark"])
    lt    = HexColor(theme["light"])
    acc   = HexColor(theme["accent"])

    rows = (len(problems) + cols - 1) // cols
    usable_w = PAGE_W - 2 * M
    usable_h = start_y - 0.42 * inch   # espace jusqu'au footer
    cell_w = usable_w / cols
    cell_h = min(usable_h / rows, 1.30 * inch)
    cell_h = max(cell_h, 0.90 * inch)

    pad = 6  # pt padding interne

    for idx, (a, op, b, ans) in enumerate(problems):
        row, col = divmod(idx, cols)
        cx = M + col * cell_w
        cy = start_y - row * cell_h

        # Fond de la cellule
        c.saveState()
        c.setFillColor(lt)
        c.roundRect(cx + pad, cy - cell_h + pad, cell_w - 2*pad, cell_h - 2*pad,
                    6, fill=1, stroke=0)
        c.restoreState()

        # Badge numéro (cercle coloré)
        badge_r = 9
        badge_x = cx + pad + badge_r + 3
        badge_y = cy - pad - badge_r
        c.setFillColor(hx)
        c.circle(badge_x, badge_y, badge_r, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Nunito-Bold", 8)
        c.drawCentredString(badge_x, badge_y - 3, str(idx + 1))

        # Equation (centrée dans la cellule)
        c.setFillColor(dk)
        eq_y = cy - cell_h * 0.40
        c.setFont("Nunito-Bold", 17)
        eq = f"{a}  {op}  {b}  ="
        c.drawCentredString(cx + cell_w/2, eq_y, eq)

        # Ligne réponse ou réponse colorée
        ans_y = cy - cell_h * 0.72
        ans_x1 = cx + cell_w * 0.30
        ans_x2 = cx + cell_w * 0.85
        if is_key:
            c.setFillColor(HexColor("#C0392B"))
            c.setFont("Nunito-Bold", 17)
            c.drawCentredString((ans_x1 + ans_x2)/2, ans_y - 2, str(ans))
        else:
            c.setStrokeColor(hx)
            c.setLineWidth(1.2)
            c.line(ans_x1, ans_y, ans_x2, ans_y)

    return rows * cell_h


# ── Page builders ──────────────────────────────────────────────────────────────

def _build_worksheet_page(c, problems: list, title: str, subtitle: str,
                           level_label: str, theme: dict, is_key: bool,
                           page_num: int, cols: int = 5):
    hx = HexColor(theme["primary"])

    # Décorations de fond
    _deco_corners(c, theme["deco"], hx, size=26, alpha=0.15)
    _deco_row(c, theme["deco"], hx, y=M * 0.6, count=8, alpha=0.10)

    # Filet de bord
    c.saveState()
    c.setStrokeColor(hx)
    c.setLineWidth(2.5)
    c.roundRect(M * 0.45, M * 0.45, PAGE_W - M * 0.9, PAGE_H - M * 0.9,
                10, fill=0, stroke=1)
    c.restoreState()

    # Header
    y = _header(c, title, f"{level_label}  ·  {subtitle}", theme)

    # Name line
    y = _nameline(c, y, theme)

    # Grille
    _problem_grid(c, problems, y, is_key, theme, cols)

    # Footer
    _footer(c, theme, page_num)
    c.showPage()


def _build_cover(path: Path, title: str, theme: dict, op_name: str, grade: str):
    c = rl_canvas.Canvas(str(path), pagesize=letter)
    hx  = HexColor(theme["primary"])
    dk  = HexColor(theme["dark"])
    lt  = HexColor(theme["light"])
    acc = HexColor(theme["accent"])

    # Fond coloré
    c.setFillColor(lt)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Décoration pleine page
    for i in range(12):
        _draw_deco(c, theme["deco"],
                   M + (i % 4) * 1.5*inch + 0.5*inch,
                   M + (i // 4) * 1.8*inch + 0.8*inch,
                   22, hx, alpha=0.10)

    # Bordure
    c.setStrokeColor(hx)
    c.setLineWidth(6)
    c.roundRect(M*0.6, M*0.6, PAGE_W - M*1.2, PAGE_H - M*1.2, 14, fill=0, stroke=1)

    # Bandeau principal
    bh = 3.0 * inch
    by = (PAGE_H - bh) / 2
    c.setFillColor(hx)
    c.roundRect(M + 0.25*inch, by, PAGE_W - 2*M - 0.5*inch, bh, 14, fill=1, stroke=0)

    # Déco dans bandeau
    _draw_deco(c, theme["deco"], M + 0.75*inch, by + bh/2, 38, lt, alpha=0.6)
    _draw_deco(c, theme["deco"], PAGE_W - M - 0.75*inch, by + bh/2, 38, lt, alpha=0.6)

    # Titre
    c.setFillColor(white)
    c.setFont("Nunito-Bold", 28)
    words = title.split()
    mid = len(words) // 2 or 1
    c.drawCentredString(PAGE_W/2, by + bh - 0.72*inch, " ".join(words[:mid]))
    c.drawCentredString(PAGE_W/2, by + bh - 1.28*inch, " ".join(words[mid:]))
    c.setFont("Nunito", 15)
    c.drawCentredString(PAGE_W/2, by + 0.44*inch,
                        f"{op_name}  ·  Grade {grade}  ·  3 Differentiated Levels")

    # Bullets
    bullets = [
        "75 Problems  ·  3 Differentiated Levels",
        "Answer Keys for Every Page",
        "No Prep  —  Just Print & Go",
        "Common Core Aligned  ·  US Letter",
    ]
    c.setFillColor(dk)
    yb = by - 0.95 * inch
    for blt in bullets:
        c.setFillColor(hx)
        c.setFont("Nunito-Bold", 15)
        c.circle(M + 0.95*inch, yb + 4, 7, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Nunito-Bold", 9)
        c.drawCentredString(M + 0.95*inch, yb + 1, "✓")
        c.setFillColor(HexColor("#2C3E50"))
        c.setFont("Nunito", 13)
        c.drawString(M + 1.15*inch, yb, blt)
        yb -= 0.45 * inch

    # Author
    c.setFont("Nunito", 12)
    c.setFillColor(HexColor("#777"))
    c.drawCentredString(PAGE_W/2, M + 0.55*inch, "by BrightOwl Learning")

    c.showPage()
    c.save()


def _build_terms(path: Path, theme: dict):
    c = rl_canvas.Canvas(str(path), pagesize=letter)
    _deco_corners(c, theme["deco"], HexColor(theme["primary"]), size=22, alpha=0.12)
    hx = HexColor(theme["primary"])
    hh = 0.65*inch
    hy = PAGE_H - M - hh
    c.setFillColor(hx)
    c.roundRect(M, hy, PAGE_W - 2*M, hh, 10, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Nunito-Bold", 20)
    c.drawCentredString(PAGE_W/2, hy + hh/2 - 6, "Terms of Use")

    lines = [
        "✓  Use with your own students in your classroom.",
        "✓  Print as many copies as needed for your class.",
        "✓  Store on a personal password-protected device.",
        "",
        "✗  Do not share, sell, or redistribute this resource.",
        "✗  Do not post to shared drives or social media.",
        "✗  Do not claim this work as your own.",
        "",
        "Additional licenses are available at a discount for teams.",
        f"© {datetime.now().year} BrightOwl Learning. All rights reserved.",
    ]
    ty = hy - 0.55*inch
    for ln in lines:
        col = HexColor("#1E8449") if ln.startswith("✓") else \
              HexColor("#C0392B") if ln.startswith("✗") else HexColor("#2C3E50")
        c.setFillColor(col)
        c.setFont("Nunito-Bold" if ln and ln[0] in "✓✗" else "Nunito", 12)
        c.drawString(M + 0.3*inch, ty, ln)
        ty -= 0.34*inch
    _footer(c, theme)
    c.showPage()
    c.save()


# ── Listing generation ────────────────────────────────────────────────────────

def _gemini_text(prompt: str) -> str | None:
    if not GEMINI_KEY:
        return None
    import urllib.request, json as _json
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"gemini-2.5-flash:generateContent?key={GEMINI_KEY}")
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    req = urllib.request.Request(url, data=_json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = _json.loads(r.read())
        for cand in resp.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                if "text" in part:
                    return part["text"]
    except Exception as exc:
        print(f"  [Gemini] {exc}")
    return None


def _generate_listing(cfg: dict, out_dir: Path):
    op   = OPS[cfg["op"]]
    theme = THEMES[cfg["theme"]]
    grade = cfg["grade"]

    if GEMINI_KEY:
        prompt = (
            f"Write a Teachers Pay Teachers product listing for:\n"
            f"Title: {cfg['title']}\n"
            f"Subject: {op['name']}\nGrade: {grade}\nTheme: {theme['label']}\n"
            f"Format: 3 differentiated worksheets (75 problems total), answer keys, no prep\n\n"
            f"Output exactly:\n"
            f"TITLE: [SEO title, max 80 chars, include grade + subject + theme + 'worksheets']\n"
            f"DESCRIPTION: [100-150 words, teacher-focused, bullet points for what's included]\n"
            f"TAGS: [12 comma-separated TPT search tags]"
        )
        text = _gemini_text(prompt)
        if text:
            (out_dir / "listing.md").write_text(
                f"# TPT LISTING\n\n{text}\n\n## Prix conseillé: ${cfg['price']:.2f}\n",
                encoding="utf-8")
            return

    # Template fallback
    listing = f"""# TPT LISTING

## Titre SEO
{theme['label']} {op['name']} Worksheets Grade {grade} — Differentiated No Prep Math Practice

## Prix
${cfg['price']:.2f}

## Description
Make {op['verb']} practice engaging with these **{theme['label'].lower()} themed** math worksheets!
Perfect for Grade {grade}, this no-prep pack includes 3 differentiated levels so every
student is challenged at the right pace.

**What's included:**
- 3 worksheets × 25 problems = **75 problems total**
- Support, On-Level, and Challenge levels
- Answer keys for every page
- Terms of use
- Print-ready US Letter (8.5 × 11")

**Perfect for:** morning work, homework, math centers, early finishers, sub plans.

## Tags
{theme['label'].lower()}, {op['name'].lower()}, grade {grade}, math worksheets, no prep,
differentiated, answer key, print and go, math facts, {theme['months'].split('–')[0].lower()},
common core, just print

## Standards
- Common Core {op['name']} standards Grade {grade}
"""
    (out_dir / "listing.md").write_text(listing, encoding="utf-8")


# ── Master pack builder ────────────────────────────────────────────────────────

def build_pack(cfg: dict, base_out: Path) -> Path:
    """Génère un pack complet. Retourne le chemin du dossier."""
    op    = OPS[cfg["op"]]
    theme = THEMES[cfg["theme"]]
    grade = cfg["grade"]
    seed  = cfg.get("seed", 42)
    cols  = cfg.get("cols", 5)
    count = cols * 5  # 25 par défaut

    out = base_out / cfg["id"]
    out.mkdir(parents=True, exist_ok=True)

    title = f"{theme['label']} {op['name']} Worksheets — Grade {grade}"
    cfg["title"] = title

    # Générer les problèmes (mêmes seeds pour worksheet et answer key)
    level_problems = {}
    for i, lvl in enumerate(["support", "on_level", "challenge"]):
        level_problems[lvl] = gen_problems(cfg["op"], lvl, seed + i * 1000, count)

    # worksheet.pdf
    ws_path = out / "worksheet.pdf"
    c = rl_canvas.Canvas(str(ws_path), pagesize=letter)
    for pg, lvl in enumerate(["support", "on_level", "challenge"], 1):
        _build_worksheet_page(c, level_problems[lvl],
                              title, f"Grade {grade}  ·  {op['name']}",
                              LEVELS[lvl]["label"], theme,
                              is_key=False, page_num=pg, cols=cols)
    c.save()

    # answer_key.pdf
    ak_path = out / "answer_key.pdf"
    c = rl_canvas.Canvas(str(ak_path), pagesize=letter)
    for pg, lvl in enumerate(["support", "on_level", "challenge"], 1):
        _build_worksheet_page(c, level_problems[lvl],
                              title + " — ANSWER KEY",
                              f"Grade {grade}  ·  {op['name']}",
                              LEVELS[lvl]["label"], theme,
                              is_key=True, page_num=pg, cols=cols)
    c.save()

    # cover.pdf
    _build_cover(out / "cover.pdf", title, theme, op["name"], grade)

    # terms.pdf
    _build_terms(out / "terms.pdf", theme)

    # listing.md
    _generate_listing(cfg, out)

    # bundle.zip
    bundle = out / "bundle.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in ("cover.pdf", "worksheet.pdf", "answer_key.pdf", "terms.pdf", "listing.md"):
            fp = out / fn
            if fp.exists():
                z.write(fp, fn)

    size = bundle.stat().st_size // 1024
    print(f"  ✓ {cfg['id']}  ({size}ko)  → {out.name}/")
    return out


# ── Batch configs ─────────────────────────────────────────────────────────────

# Tous les produits à générer (thème × opération × grade)
BATCH = [
    # Back to School (plus grande fenêtre TPT - juillet/août)
    dict(id="bts_add_g1",  theme="back_to_school", op="add", grade="1", price=3.50),
    dict(id="bts_add_g2",  theme="back_to_school", op="add", grade="2", price=3.50),
    dict(id="bts_sub_g2",  theme="back_to_school", op="sub", grade="2", price=3.50),
    dict(id="bts_mul_g3",  theme="back_to_school", op="mul", grade="3", price=3.50),

    # Halloween
    dict(id="hw_add_g1",   theme="halloween",      op="add", grade="1", price=3.50),
    dict(id="hw_sub_g2",   theme="halloween",      op="sub", grade="2", price=3.50),
    dict(id="hw_mul_g3",   theme="halloween",      op="mul", grade="3", price=3.50),
    dict(id="hw_div_g4",   theme="halloween",      op="div", grade="4", price=3.50),

    # Christmas
    dict(id="xmas_add_g1", theme="christmas",      op="add", grade="1", price=3.50),
    dict(id="xmas_sub_g2", theme="christmas",      op="sub", grade="2", price=3.50),
    dict(id="xmas_mul_g3", theme="christmas",      op="mul", grade="3", price=3.50),
    dict(id="xmas_div_g4", theme="christmas",      op="div", grade="4", price=3.50),

    # Valentine
    dict(id="val_add_k",   theme="valentine",      op="add", grade="K", price=3.00),
    dict(id="val_add_g1",  theme="valentine",      op="add", grade="1", price=3.50),
    dict(id="val_sub_g2",  theme="valentine",      op="sub", grade="2", price=3.50),

    # Spring
    dict(id="spr_add_g1",  theme="spring",         op="add", grade="1", price=3.50),
    dict(id="spr_mul_g3",  theme="spring",         op="mul", grade="3", price=3.50),

    # Thanksgiving
    dict(id="tg_add_g1",   theme="thanksgiving",   op="add", grade="1", price=3.50),
    dict(id="tg_mul_g3",   theme="thanksgiving",   op="mul", grade="3", price=3.50),

    # Winter
    dict(id="win_add_g1",  theme="winter",         op="add", grade="1", price=3.50),
    dict(id="win_sub_g2",  theme="winter",         op="sub", grade="2", price=3.50),

    # Plain year-round
    dict(id="plain_mul_g3",theme="plain",          op="mul", grade="3", price=3.00),
    dict(id="plain_div_g4",theme="plain",          op="div", grade="4", price=3.00),
]


def main():
    only = os.environ.get("THEME", "").strip()
    out_base = Path(os.environ.get("OUT_DIR",
                    str(ROOT / "products" / "tpt" / "math_drills")))

    batch = [b for b in BATCH if not only or b["theme"] == only]
    print(f"Génération de {len(batch)} packs math drills...\n")

    for cfg in batch:
        try:
            build_pack(cfg, out_base)
        except Exception as exc:
            print(f"  ✗ {cfg['id']}: {exc}")

    print(f"\n[DONE] {len(batch)} packs → {out_base}/")


if __name__ == "__main__":
    main()
