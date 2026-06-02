"""
Mystery Picture Halloween — Multiplication Grade 3
BrightOwl Learning
"""
from __future__ import annotations
import random
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

def F(name, fallback="Helvetica"):
    try: pdfmetrics.getFont(name); return name
    except: return fallback

def FB(): return F("Nunito-Bold","Helvetica-Bold")
def FN(): return F("Nunito","Helvetica")

# ── Pumpkin pixel map ─────────────────────────────────────────────────────────
PUMPKIN = [
    list("WWWWWGGWWWWWWWW"),
    list("WWWWWWGWWWWWWWW"),
    list("WWOOOOOOOOOOWWW"),
    list("WOOOOOOOOOOOOWW"),
    list("WOOBOOOOOBOOOWW"),
    list("WOOBOOOOOBOOOWW"),
    list("WOOOOBBBOOOOWWW"),
    list("WOOOBOOOBOOOWWW"),
    list("WOOOOBBBOOOOWWW"),
    list("WOOOOOOOOOOOOWW"),
    list("WWOOOOOOOOOOWWW"),
    list("WWWOOOOOOOOWWWW"),
    list("WWWWWWWWWWWWWWW"),
    list("WWWWWWWWWWWWWWW"),
    list("WWWWWWWWWWWWWWW"),
]

# Answer map
ANSWERS = {'O': 12, 'B': 24, 'G': 6, 'W': 0}
COLORS  = {
    'O': HexColor("#E8771A"),
    'B': HexColor("#111111"),
    'G': HexColor("#2D9A2D"),
    'W': HexColor("#FFFFFF"),
}
PROBLEMS = {
    'O': [(3,4),(4,3),(2,6),(6,2)],
    'B': [(4,6),(6,4),(3,8),(8,3)],
    'G': [(2,3),(3,2),(1,6),(6,1)],
    'W': [],
}

def make_problem(cell):
    if cell == 'W':
        return "0 × 1"
    a, b = random.choice(PROBLEMS[cell])
    return f"{a} × {b}"

def draw_header(c, title, subtitle=""):
    c.setFillColor(BRAND_COLOR)
    c.rect(0, PAGE_H - 0.75*inch, PAGE_W, 0.75*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FB(), 16)
    c.drawCentredString(PAGE_W/2, PAGE_H - 0.48*inch, title)
    if subtitle:
        c.setFont(FN(), 10)
        c.drawCentredString(PAGE_W/2, PAGE_H - 0.65*inch, subtitle)

def draw_footer(c):
    c.setFillColor(SECONDARY)
    c.rect(0, 0, PAGE_W, 0.35*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FN(), 9)
    c.drawCentredString(PAGE_W/2, 0.1*inch, AUTHOR + "  •  Halloween Mystery Picture")

def draw_grid_page(c, show_answers=False):
    draw_header(c,
        "Halloween Mystery Picture — Multiplication",
        "Grade 3  |  Color by answer to reveal the hidden picture!")
    draw_footer(c)

    # Color key bar
    ky = PAGE_H - 1.1*inch
    c.setFillColor(BRAND_LIGHT)
    c.rect(0.4*inch, ky - 0.3*inch, PAGE_W - 0.8*inch, 0.35*inch, fill=1, stroke=0)
    c.setFont(FB(), 10)
    key_items = [
        (HexColor("#E8771A"), "12 = Orange"),
        (HexColor("#111111"), "24 = Black"),
        (HexColor("#2D9A2D"), "6 = Green"),
        (HexColor("#DDDDDD"), "0 = White (leave blank)"),
    ]
    kx = 0.6*inch
    for col, label in key_items:
        c.setFillColor(col)
        c.rect(kx, ky - 0.22*inch, 0.18*inch, 0.18*inch, fill=1, stroke=1)
        c.setFillColor(black)
        c.setFont(FN(), 9)
        c.drawString(kx + 0.22*inch, ky - 0.12*inch, label)
        kx += 1.6*inch

    # Grid dimensions
    grid_left = 0.45*inch
    grid_top  = ky - 0.45*inch
    cell_w    = (PAGE_W - 0.9*inch) / 15
    cell_h    = (grid_top - 0.5*inch) / 15

    for row in range(15):
        for col in range(15):
            cell = PUMPKIN[row][col]
            x = grid_left + col * cell_w
            y = grid_top  - (row+1) * cell_h

            if show_answers:
                fill_col = COLORS[cell]
            else:
                fill_col = white

            c.setFillColor(fill_col)
            c.setStrokeColor(HexColor("#CCCCCC"))
            c.setLineWidth(0.5)
            c.rect(x, y, cell_w, cell_h, fill=1, stroke=1)

            if not show_answers:
                prob = make_problem(cell)
                c.setFillColor(HexColor("#333333"))
                c.setFont(FN(), 6.5)
                c.drawCentredString(x + cell_w/2, y + cell_h*0.55, prob)
                c.setFont(FB(), 5.5)
                ans = ANSWERS[cell]
                c.setFillColor(HexColor("#888888"))
                c.drawCentredString(x + cell_w/2, y + cell_h*0.2, f"={ans}")
            else:
                if cell != 'W':
                    c.setFillColor(white if cell=='B' else black)
                    c.setFont(FB(), 6)
                    c.drawCentredString(x + cell_w/2, y + cell_h*0.35,
                                        str(ANSWERS[cell]))

    # Row & column numbers
    c.setFont(FN(), 6)
    c.setFillColor(HexColor("#999999"))
    for i in range(15):
        # col header
        cx = grid_left + i*cell_w + cell_w/2
        c.drawCentredString(cx, grid_top + 0.04*inch, str(i+1))
        # row header
        ry = grid_top - (i+0.5)*cell_h
        c.drawRightString(grid_left - 0.05*inch, ry - 3, str(i+1))

def build():
    out = ROOT / "products/tpt/samples/mystery_picture/sample.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out), pagesize=letter)

    # Page 1: student worksheet
    draw_grid_page(c, show_answers=False)
    c.showPage()

    # Page 2: answer key
    draw_header(c,
        "ANSWER KEY — Halloween Mystery Picture",
        "Cells filled with correct colors reveal the pumpkin!")
    draw_footer(c)

    # Reuse grid drawing with answers
    ky = PAGE_H - 1.1*inch
    grid_left = 0.45*inch
    grid_top  = ky - 0.1*inch
    cell_w    = (PAGE_W - 0.9*inch) / 15
    cell_h    = (grid_top - 0.5*inch) / 15

    for row in range(15):
        for col in range(15):
            cell = PUMPKIN[row][col]
            x = grid_left + col * cell_w
            y = grid_top  - (row+1) * cell_h
            c.setFillColor(COLORS[cell])
            c.setStrokeColor(HexColor("#AAAAAA"))
            c.setLineWidth(0.5)
            c.rect(x, y, cell_w, cell_h, fill=1, stroke=1)

    # Legend on answer key
    c.setFont(FB(), 12)
    c.setFillColor(SECONDARY)
    c.drawCentredString(PAGE_W/2, 0.55*inch, "Answer Key — Color the squares to reveal the Halloween Pumpkin!")
    c.showPage()
    c.save()
    print(f"✓ mystery_picture  → {out}  ({out.stat().st_size:,} bytes)")

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
