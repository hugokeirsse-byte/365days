"""
Halloween Math Sort — Even/Odd, Comparing Numbers, Multiplication
BrightOwl Learning  |  3 sorting activity pages
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PAGE_W, PAGE_H = letter
BRAND_COLOR = HexColor("#E8771A")
SECONDARY   = HexColor("#2C3E50")
ACCENT      = HexColor("#FFD700")
BRAND_LIGHT = HexColor("#FFF5E6")
AUTHOR      = "BrightOwl Learning"
FONT_DIR    = Path(__file__).parent.parent / "fonts"

def register_fonts():
    for name, fname in [("Nunito","Nunito-Regular.ttf"),("Nunito-Bold","Nunito-Bold.ttf")]:
        p = FONT_DIR / fname
        if p.exists():
            pdfmetrics.registerFont(TTFont(name, str(p)))

register_fonts()
def FB():
    try: pdfmetrics.getFont("Nunito-Bold"); return "Nunito-Bold"
    except: return "Helvetica-Bold"
def FN():
    try: pdfmetrics.getFont("Nunito"); return "Nunito"
    except: return "Helvetica"

def draw_header(c, title, subtitle=""):
    c.setFillColor(BRAND_COLOR)
    c.rect(0, PAGE_H - 0.75*inch, PAGE_W, 0.75*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FB(), 16)
    c.drawCentredString(PAGE_W/2, PAGE_H - 0.48*inch, title)
    if subtitle:
        c.setFont(FN(), 10)
        c.drawCentredString(PAGE_W/2, PAGE_H - 0.65*inch, subtitle)

def draw_footer(c, note=""):
    c.setFillColor(SECONDARY)
    c.rect(0, 0, PAGE_W, 0.35*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FN(), 8)
    c.drawCentredString(PAGE_W/2, 0.1*inch, f"{AUTHOR}  •  Halloween Math Sort  •  Grade 2-3" + (f"  |  {note}" if note else ""))

def draw_pumpkin(c, cx, cy, r=9):
    c.setFillColor(BRAND_COLOR)
    c.circle(cx, cy, r, fill=1, stroke=0)
    c.ellipse(cx-r*0.62, cy-r*0.45, cx-r*0.05, cy+r*0.45, fill=1, stroke=0)
    c.ellipse(cx+r*0.05, cy-r*0.45, cx+r*0.62, cy+r*0.45, fill=1, stroke=0)
    c.setFillColor(HexColor("#2D9A2D"))
    c.setLineWidth(1.5); c.setStrokeColor(HexColor("#2D9A2D"))
    c.line(cx, cy+r, cx+r*0.4, cy+r*1.45)
    c.setFillColor(black)
    c.circle(cx-r*0.28, cy+r*0.1, r*0.11, fill=1, stroke=0)
    c.circle(cx+r*0.28, cy+r*0.1, r*0.11, fill=1, stroke=0)
    p = c.beginPath()
    p.moveTo(cx-r*0.28, cy-r*0.12)
    p.lineTo(cx-r*0.12, cy-r*0.3)
    p.lineTo(cx+r*0.12, cy-r*0.3)
    p.lineTo(cx+r*0.28, cy-r*0.12)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

def dashed_h(c, x1, y, x2):
    c.setStrokeColor(HexColor("#BBBBBB"))
    c.setLineWidth(0.5)
    c.setDash([4,3])
    c.line(x1, y, x2, y)
    c.setDash([])

def draw_sort_mat(c, left_label, right_label, left_color, right_color,
                  left_x, right_x, top_y, mat_w, mat_h):
    """Draw a 2-column sorting mat."""
    half = mat_w / 2 - 0.1*inch
    # Left column
    c.setFillColor(left_color)
    c.setStrokeColor(SECONDARY); c.setLineWidth(1.5)
    c.roundRect(left_x, top_y - mat_h, half, mat_h, 8, fill=1, stroke=1)
    c.setFillColor(white)
    c.setFont(FB(), 14)
    c.drawCentredString(left_x + half/2, top_y - 30, left_label)
    # Right column
    c.setFillColor(right_color)
    c.roundRect(right_x, top_y - mat_h, half, mat_h, 8, fill=1, stroke=1)
    c.setFillColor(white)
    c.setFont(FB(), 14)
    c.drawCentredString(right_x + half/2, top_y - 30, right_label)

def draw_cut_card(c, x, y, w, h, text, color=None):
    bg = color or BRAND_LIGHT
    c.setFillColor(bg)
    c.setStrokeColor(HexColor("#AAAAAA"))
    c.setLineWidth(0.5)
    c.roundRect(x+1, y+1, w-2, h-2, 4, fill=1, stroke=1)
    c.setFillColor(SECONDARY)
    c.setFont(FB(), 11)
    c.drawCentredString(x+w/2, y+h/2-5, text)

# ── Page 1: Even vs Odd ────────────────────────────────────────────────────────
def page_even_odd(c):
    draw_header(c, "Even vs. Odd Number Sort", "Cut out the number cards and sort them into the correct column!")
    draw_footer(c, "Activity 1 of 3")

    mat_left  = 0.4*inch
    mat_top   = PAGE_H - 0.9*inch
    mat_w     = PAGE_W - 0.8*inch
    mat_h     = 3.5*inch
    half_w    = mat_w/2 - 0.1*inch
    right_x   = mat_left + mat_w/2 + 0.1*inch

    draw_sort_mat(c, "EVEN", "ODD",
                  HexColor("#E8771A"), HexColor("#2C3E50"),
                  mat_left, right_x, mat_top, mat_w, mat_h)

    # Decorative pumpkins on mat columns
    draw_pumpkin(c, mat_left + half_w/2, mat_top - mat_h/2, r=12)
    draw_pumpkin(c, right_x + half_w/2, mat_top - mat_h/2, r=12)

    # Instructions
    c.setFont(FN(), 9)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(PAGE_W/2, mat_top - mat_h - 0.2*inch,
        "✂  Cut out the number cards below and glue them into the correct column.")

    # Cut-out cards: 20 numbers
    numbers = [2,7,14,9,22,15,38,11,46,5,30,13,72,19,84,3,60,17,96,21]
    card_w = (PAGE_W - 0.8*inch) / 10
    card_h = 0.45*inch
    start_x = 0.4*inch
    start_y = mat_top - mat_h - 0.55*inch

    dashed_h(c, 0.3*inch, start_y + card_h + 0.1*inch, PAGE_W - 0.3*inch)
    c.setFont(FN(), 7)
    c.setFillColor(HexColor("#999999"))
    c.drawString(0.3*inch, start_y + card_h + 0.13*inch, "✂ cut")

    for i, n in enumerate(numbers):
        row = i // 10
        col = i % 10
        cx = start_x + col * card_w
        cy = start_y - row * (card_h + 0.08*inch)
        color = HexColor("#FFF0DC") if n % 2 == 0 else HexColor("#E8E8F0")
        draw_cut_card(c, cx, cy, card_w - 4, card_h, str(n), color)
        if i == 9:
            dashed_h(c, 0.3*inch, cy - 0.06*inch, PAGE_W - 0.3*inch)

# ── Page 2: Greater / Less than ───────────────────────────────────────────────
def page_greater_less(c):
    draw_header(c, "Greater Than / Less Than Sort", "Write >, < or = then cut and sort the cards!")
    draw_footer(c, "Activity 2 of 3")

    mat_left  = 0.4*inch
    mat_top   = PAGE_H - 0.9*inch
    mat_w     = PAGE_W - 0.8*inch
    mat_h     = 3.2*inch
    half_w    = mat_w/2 - 0.1*inch
    right_x   = mat_left + mat_w/2 + 0.1*inch

    draw_sort_mat(c, "Greater Than  >", "Less Than  <",
                  HexColor("#E8771A"), HexColor("#2C3E50"),
                  mat_left, right_x, mat_top, mat_w, mat_h)

    c.setFont(FN(), 9)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(PAGE_W/2, mat_top - mat_h - 0.2*inch,
        "✂  Cut out the comparison cards. Write >, < or = in the blank, then sort!")

    expressions = [
        ("34", "43"), ("87","78"), ("56","65"), ("12","21"),
        ("99","90"), ("45","54"), ("33","33"), ("71","17"),
        ("68","86"), ("24","42"), ("55","55"), ("19","91"),
        ("82","28"), ("63","36"), ("47","74"), ("15","51"),
    ]

    card_w = (PAGE_W - 0.8*inch) / 8
    card_h = 0.5*inch
    start_x = 0.4*inch
    start_y = mat_top - mat_h - 0.55*inch

    dashed_h(c, 0.3*inch, start_y + card_h + 0.08*inch, PAGE_W - 0.3*inch)
    c.setFont(FN(), 7)
    c.setFillColor(HexColor("#999999"))
    c.drawString(0.3*inch, start_y + card_h + 0.1*inch, "✂ cut")

    for i, (a, b) in enumerate(expressions):
        row = i // 8
        col = i % 8
        cx = start_x + col * card_w
        cy = start_y - row * (card_h + 0.08*inch)

        actual = int(a) > int(b)
        bg = HexColor("#FFF0DC") if int(a) > int(b) else (
             HexColor("#E8E8F0") if int(a) < int(b) else HexColor("#FFFFF0"))
        c.setFillColor(bg)
        c.setStrokeColor(HexColor("#AAAAAA")); c.setLineWidth(0.5)
        c.roundRect(cx+1, cy+1, card_w-2, card_h-2, 3, fill=1, stroke=1)
        c.setFillColor(SECONDARY)
        c.setFont(FN(), 9)
        c.drawString(cx+4, cy+card_h/2-4, f"{a}  ___  {b}")

        if i == 7:
            dashed_h(c, 0.3*inch, cy - 0.06*inch, PAGE_W - 0.3*inch)

# ── Page 3: Multiplication < 20 vs ≥ 20 ──────────────────────────────────────
def page_mult_sort(c):
    draw_header(c, "Multiplication Products Sort", 'Solve and sort: "Less than 20" or "20 or More"')
    draw_footer(c, "Activity 3 of 3")

    mat_left  = 0.4*inch
    mat_top   = PAGE_H - 0.9*inch
    mat_w     = PAGE_W - 0.8*inch
    mat_h     = 3.0*inch
    half_w    = mat_w/2 - 0.1*inch
    right_x   = mat_left + mat_w/2 + 0.1*inch

    draw_sort_mat(c, "Less Than 20", "20 or More",
                  HexColor("#2D9A2D"), HexColor("#8B2FC9"),
                  mat_left, right_x, mat_top, mat_w, mat_h)

    c.setFont(FN(), 9)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(PAGE_W/2, mat_top - mat_h - 0.2*inch,
        "✂  Solve each problem, then cut and sort into the correct column.")

    problems = [
        (2,4),(3,5),(4,6),(2,7),(3,3),(5,5),(2,9),(4,4),
        (2,6),(3,6),(5,6),(2,8),(4,5),(3,7),(6,6),(4,7),
        (2,5),(3,4),(5,4),(6,7),
    ]

    card_w = (PAGE_W - 0.8*inch) / 10
    card_h = 0.48*inch
    start_x = 0.4*inch
    start_y = mat_top - mat_h - 0.52*inch

    dashed_h(c, 0.3*inch, start_y + card_h + 0.08*inch, PAGE_W - 0.3*inch)
    c.setFont(FN(), 7)
    c.setFillColor(HexColor("#999999"))
    c.drawString(0.3*inch, start_y + card_h + 0.1*inch, "✂ cut")

    for i, (a, b) in enumerate(problems):
        row = i // 10
        col = i % 10
        cx = start_x + col * card_w
        cy = start_y - row * (card_h + 0.08*inch)

        product = a * b
        bg = HexColor("#E8F5E9") if product < 20 else HexColor("#F3E5F5")
        c.setFillColor(bg)
        c.setStrokeColor(HexColor("#AAAAAA")); c.setLineWidth(0.5)
        c.roundRect(cx+1, cy+1, card_w-2, card_h-2, 3, fill=1, stroke=1)
        c.setFillColor(SECONDARY)
        c.setFont(FB(), 10)
        c.drawCentredString(cx+card_w/2, cy+card_h/2+1, f"{a}×{b}")
        c.setFont(FN(), 7)
        c.setFillColor(HexColor("#888888"))
        c.drawCentredString(cx+card_w/2, cy+5, f"={product}")

        if i == 9:
            dashed_h(c, 0.3*inch, cy - 0.05*inch, PAGE_W - 0.3*inch)

def build():
    out = ROOT / "products/tpt/samples/math_sort/sample.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out), pagesize=letter)

    page_even_odd(c)
    c.showPage()
    page_greater_less(c)
    c.showPage()
    page_mult_sort(c)
    c.showPage()

    c.save()
    print(f"✓ math_sort  → {out}  ({out.stat().st_size:,} bytes)")

if __name__ == "__main__":
    build()


def build_all(out_dir=None, themes=None, gemini_key=None):
    """Interface standard pour run_all.py"""
    import os
    from pathlib import Path as _P
    if out_dir:
        name = _P(__file__).stem
        os.environ.setdefault("OUT_DIR", str(_P(out_dir) / name))
    build()
