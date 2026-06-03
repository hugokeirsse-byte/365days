"""
BrightOwl Learning — Fun Math shared design core.
Vibrant, playful design system used by all 'fun' product generators.

Provides: palette, fonts, headers, shapes (star, speech bubble, dice),
OpenMoji loading/rendering, name line, footer.
"""
from __future__ import annotations

import io
import math
import random
from pathlib import Path

import cairosvg
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

TPT      = Path(__file__).resolve().parent.parent       # scripts/tpt
FONT_DIR = TPT / "fonts"
OMOJI    = TPT / "assets" / "openmoji"
OUT_ROOT = TPT.parent.parent / "products" / "tpt"

PAGE_W, PAGE_H = letter
M = 0.55 * inch
AUTHOR = "BrightOwl Learning"
YEAR   = 2026

# ── Palette ──────────────────────────────────────────────────────────────────
# A friendly, vibrant-but-not-garish set. Used across all fun products.
PINK   = "#FF6B9D"
YELLOW = "#FFC93C"
MINT   = "#3FC9B0"
INK    = "#3D3B6E"
SKY    = "#5AA9F0"
CORAL  = "#FF8C61"
GRAPE  = "#9B6DD6"
TINT   = "#FFF6FA"

# Theme accents (header color, secondary, soft background)
THEMES = {
    "candy":     {"a": PINK,   "b": YELLOW, "bg": "#FFF6FA"},
    "ocean":     {"a": SKY,    "b": MINT,   "bg": "#F1FAFF"},
    "halloween": {"a": "#F07818", "b": "#7B4FB5", "bg": "#FFF3E6"},
    "christmas": {"a": "#E0483B", "b": "#37A05A", "bg": "#FBEFED"},
    "spring":    {"a": MINT,   "b": YELLOW, "bg": "#EFFBF6"},
}

def _col(c):
    """Accept a hex string or an existing Color/HexColor and return a Color."""
    if isinstance(c, str):
        return HexColor(c)
    return c

_REG = False
def _reg():
    global _REG
    if _REG:
        return
    try:
        pdfmetrics.registerFont(TTFont("Nunito",    str(FONT_DIR / "Nunito-Regular.ttf")))
        pdfmetrics.registerFont(TTFont("Nunito-B",  str(FONT_DIR / "Nunito-Bold.ttf")))
        pdfmetrics.registerFont(TTFont("Nunito-XB", str(FONT_DIR / "Nunito-ExtraBold.ttf")))
        _REG = True
    except Exception:
        pass

def F(w="r"):
    _reg()
    if not _REG:
        return {"r": "Helvetica", "b": "Helvetica-Bold", "xb": "Helvetica-Bold"}[w]
    return {"r": "Nunito", "b": "Nunito-B", "xb": "Nunito-XB"}[w]


# ── Shapes ─────────────────────────────────────────────────────────────────────
def star(c, cx, cy, r, fill, stroke=None):
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    p = c.beginPath(); p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    c.saveState()
    if fill:
        c.setFillColor(_col(fill))
    c.setStrokeColor(_col(stroke or fill or "#000000"))
    c.setLineWidth(1)
    c.drawPath(p, fill=1 if fill else 0, stroke=1)
    c.restoreState()

def check(c, x, y, color, size=10):
    c.saveState()
    c.setStrokeColor(_col(color)); c.setLineWidth(2.2); c.setLineCap(1)
    c.line(x, y + size * 0.35, x + size * 0.35, y)
    c.line(x + size * 0.35, y, x + size, y + size)
    c.restoreState()

def dice(c, x, y, size, n, color):
    """Draw a dice face with n pips (1-6)."""
    c.saveState()
    c.setFillColor(white); c.setStrokeColor(_col(color)); c.setLineWidth(2)
    c.roundRect(x, y, size, size, size * 0.18, fill=1, stroke=1)
    pr = size * 0.09
    c.setFillColor(_col(color))
    g = size / 4
    spots = {
        1: [(2, 2)],
        2: [(1, 3), (3, 1)],
        3: [(1, 3), (2, 2), (3, 1)],
        4: [(1, 1), (1, 3), (3, 1), (3, 3)],
        5: [(1, 1), (1, 3), (2, 2), (3, 1), (3, 3)],
        6: [(1, 1), (1, 2), (1, 3), (3, 1), (3, 2), (3, 3)],
    }[n]
    for gx, gy in spots:
        c.circle(x + gx * g, y + gy * g, pr, fill=1, stroke=0)
    c.restoreState()

def speech_bubble(c, x, y, w, h, fill, stroke, tail_x=None):
    c.saveState()
    c.setFillColor(_col(fill)); c.setStrokeColor(_col(stroke)); c.setLineWidth(2.5)
    c.roundRect(x, y, w, h, 14, fill=1, stroke=1)
    if tail_x is not None:
        p = c.beginPath()
        p.moveTo(tail_x, y); p.lineTo(tail_x + 0.28 * inch, y - 0.22 * inch); p.lineTo(tail_x + 0.45 * inch, y)
        c.setFillColor(_col(fill)); c.setStrokeColor(_col(fill))
        c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


# ── OpenMoji loading ───────────────────────────────────────────────────────────
_PNG_CACHE = {}
def moji(name, variant="color", px=120):
    """Return an ImageReader for an OpenMoji icon, or None."""
    key = (name, variant, px)
    if key in _PNG_CACHE:
        return _PNG_CACHE[key]
    f = OMOJI / f"{name}_{variant}.svg"
    if not f.exists():
        return None
    try:
        data = cairosvg.svg2png(url=str(f), output_width=px, output_height=px)
        ir = ImageReader(io.BytesIO(data))
        _PNG_CACHE[key] = ir
        return ir
    except Exception:
        return None

def available_moji(variant="color"):
    return sorted(f.stem.rsplit("_", 1)[0] for f in OMOJI.glob(f"*_{variant}.svg"))

def draw_moji(c, name, x, y, size, variant="color"):
    ir = moji(name, variant, px=int(size / inch * 150))
    if ir:
        c.drawImage(ir, x, y, size, size, mask="auto")
        return True
    return False


# ── Common page furniture ───────────────────────────────────────────────────
def fun_header(c, theme, title, subtitle=None):
    th = THEMES[theme]
    hh = 0.95 * inch
    hy = PAGE_H - 0.5 * inch - hh
    c.setFillColor(HexColor(th["a"]))
    c.roundRect(M - 6, hy, PAGE_W - 2 * M + 12, hh, 16, fill=1, stroke=0)
    star(c, M + 0.2 * inch, hy + hh * 0.55, 11, th["b"])
    star(c, PAGE_W - M - 0.2 * inch, hy + hh * 0.55, 11, th["b"])
    c.setFillColor(white)
    c.setFont(F("xb"), 26)
    c.drawCentredString(PAGE_W / 2, hy + (hh * 0.5 if not subtitle else hh * 0.55), title)
    if subtitle:
        c.setFont(F("b"), 11)
        c.drawCentredString(PAGE_W / 2, hy + 0.18 * inch, subtitle)
    return hy

def name_line(c, theme, y=None):
    if y is None:
        y = PAGE_H - 0.5 * inch - 0.95 * inch - 0.28 * inch
    c.setFillColor(HexColor(THEMES[theme]["a"]))
    c.setFont(F("b"), 10)
    c.drawString(M, y, "Name: ___________________________")
    c.drawRightString(PAGE_W - M, y, "Date: ____________")
    return y - 0.3 * inch

def fun_footer(c, tag="Fun Math"):
    c.setFont(F("r"), 8)
    c.setFillColor(HexColor("#BBBBBB"))
    c.drawString(M, 0.35 * inch, f"© {YEAR} {AUTHOR} — single classroom use only.")
    c.drawRightString(PAGE_W - M, 0.35 * inch, f"{AUTHOR} · {tag}")

def page_bg(c, theme):
    c.setFillColor(HexColor(THEMES[theme]["bg"]))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)


# ── Math fact helpers ───────────────────────────────────────────────────────
def make_fact(op, a, b):
    if op == "mult": return f"{a} × {b}", a * b
    if op == "add":  return f"{a} + {b}", a + b
    if op == "sub":
        hi, lo = max(a, b), min(a, b); return f"{hi} − {lo}", hi - lo
    if op == "div":  return f"{a*b} ÷ {b}", a
    raise ValueError(op)

OP_WORD = {"mult": "Multiplication", "add": "Addition", "sub": "Subtraction", "div": "Division"}
