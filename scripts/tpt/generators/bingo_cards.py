"""
Halloween Math Bingo — Multiplication Facts Grade 3
BrightOwl Learning  |  30 unique bingo cards + caller cards
Sample: 3 bingo cards + 1 page of caller problems
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
def FB():
    try: pdfmetrics.getFont("Nunito-Bold"); return "Nunito-Bold"
    except: return "Helvetica-Bold"
def FN():
    try: pdfmetrics.getFont("Nunito"); return "Nunito"
    except: return "Helvetica"

# 24 possible answers (products)
ANSWERS_POOL = [6,8,9,10,12,14,15,16,18,20,21,24,25,27,28,30,32,35,36,40,42,45,48,49]

# Caller problems: (a, b) pairs whose product is in ANSWERS_POOL
CALLERS = []
for a in range(2, 8):
    for b in range(a, 8):
        if a*b in ANSWERS_POOL:
            CALLERS.append((a, b))
# supplement with more
extra_pairs = [(2,3),(2,4),(2,5),(2,6),(2,7),(3,3),(3,4),(3,5),(3,6),(3,7),
               (4,4),(4,5),(4,6),(4,7),(5,5),(5,6),(5,7),(6,6),(6,7),(7,7),
               (2,8),(3,8),(4,8),(6,8),(7,8),(3,9),(5,9),(7,9),(6,8),(7,6)]
for p in extra_pairs:
    if p[0]*p[1] in ANSWERS_POOL and p not in CALLERS:
        CALLERS.append(p)
random.shuffle(CALLERS)

def make_bingo_card(card_num):
    """Return a 5x5 grid with FREE center."""
    nums = random.sample(ANSWERS_POOL, 24)
    grid = []
    idx = 0
    for r in range(5):
        row = []
        for c in range(5):
            if r == 2 and c == 2:
                row.append("FREE")
            else:
                row.append(nums[idx])
                idx += 1
        grid.append(row)
    return grid

def draw_pumpkin_small(c, cx, cy, r=10):
    c.setFillColor(BRAND_COLOR)
    c.circle(cx, cy, r, fill=1, stroke=0)
    c.ellipse(cx-r*0.6, cy-r*0.45, cx-r*0.05, cy+r*0.45, fill=1, stroke=0)
    c.ellipse(cx+r*0.05, cy-r*0.45, cx+r*0.6, cy+r*0.45, fill=1, stroke=0)
    c.setFillColor(HexColor("#2D9A2D"))
    c.setLineWidth(1.5); c.setStrokeColor(HexColor("#2D9A2D"))
    c.line(cx, cy+r, cx+r*0.35, cy+r*1.45)
    c.setFillColor(black)
    c.circle(cx-r*0.3, cy+r*0.1, r*0.11, fill=1, stroke=0)
    c.circle(cx+r*0.3, cy+r*0.1, r*0.11, fill=1, stroke=0)
    p = c.beginPath()
    p.moveTo(cx-r*0.32, cy-r*0.12)
    p.lineTo(cx-r*0.12, cy-r*0.32)
    p.lineTo(cx+r*0.12, cy-r*0.32)
    p.lineTo(cx+r*0.32, cy-r*0.12)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

def draw_bingo_card(c, card_num, grid):
    """Draw a full-page bingo card."""
    # Background
    c.setFillColor(BRAND_LIGHT)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Header
    c.setFillColor(SECONDARY)
    c.rect(0, PAGE_H - 1.2*inch, PAGE_W, 1.2*inch, fill=1, stroke=0)

    # BINGO letters
    bingo_letters = "BINGO"
    letter_colors = [BRAND_COLOR, ACCENT, HexColor("#FF6B6B"), BRAND_COLOR, ACCENT]
    lx = PAGE_W/2 - 2.2*inch
    for i, (lt, lc) in enumerate(zip(bingo_letters, letter_colors)):
        c.setFillColor(lc)
        c.setFont(FB(), 52)
        c.drawCentredString(lx + i * 1.1*inch, PAGE_H - 0.85*inch, lt)

    # Subtitle
    c.setFillColor(white)
    c.setFont(FN(), 11)
    c.drawCentredString(PAGE_W/2, PAGE_H - 1.08*inch, "Halloween Multiplication Math  |  Grade 3")

    # Pumpkins in header corners
    draw_pumpkin_small(c, 0.5*inch, PAGE_H - 0.6*inch, r=14)
    draw_pumpkin_small(c, PAGE_W - 0.5*inch, PAGE_H - 0.6*inch, r=14)

    # Card number
    c.setFillColor(HexColor("#999999"))
    c.setFont(FN(), 9)
    c.drawRightString(PAGE_W - 0.3*inch, PAGE_H - 1.35*inch, f"Card #{card_num}")

    # Grid
    grid_left   = 0.85*inch
    grid_top    = PAGE_H - 1.5*inch
    cell_size   = (PAGE_W - 1.7*inch) / 5
    letter_row_h = 0.45*inch

    # Column headers (B I N G O)
    col_hdrs = "BINGO"
    hdr_colors = [HexColor("#E8771A"), HexColor("#2C3E50"), HexColor("#E8771A"),
                  HexColor("#2C3E50"), HexColor("#E8771A")]
    for ci, (lt, hc) in enumerate(zip(col_hdrs, hdr_colors)):
        hx = grid_left + ci * cell_size
        c.setFillColor(hc)
        c.rect(hx, grid_top - letter_row_h, cell_size, letter_row_h, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(FB(), 22)
        c.drawCentredString(hx + cell_size/2, grid_top - letter_row_h*0.65, lt)

    # Cells
    for row in range(5):
        for col in range(5):
            cx = grid_left + col * cell_size
            cy = grid_top - letter_row_h - (row+1) * cell_size
            val = grid[row][col]

            if val == "FREE":
                c.setFillColor(BRAND_COLOR)
            elif (row + col) % 2 == 0:
                c.setFillColor(white)
            else:
                c.setFillColor(HexColor("#FFF0DC"))

            c.setStrokeColor(SECONDARY)
            c.setLineWidth(1.5)
            c.rect(cx, cy, cell_size, cell_size, fill=1, stroke=1)

            if val == "FREE":
                c.setFillColor(white)
                c.setFont(FB(), 16)
                c.drawCentredString(cx + cell_size/2, cy + cell_size/2 - 6, "FREE")
                draw_pumpkin_small(c, cx + cell_size/2, cy + cell_size*0.72, r=12)
            else:
                c.setFillColor(SECONDARY)
                c.setFont(FB(), 24)
                c.drawCentredString(cx + cell_size/2, cy + cell_size/2 - 9, str(val))

    # Footer
    c.setFillColor(SECONDARY)
    c.rect(0, 0, PAGE_W, 0.4*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FN(), 9)
    c.drawCentredString(PAGE_W/2, 0.12*inch, AUTHOR + "  •  Halloween Math Bingo")

def draw_caller_page(c, callers_list):
    """Draw a page of caller problem cards."""
    c.setFillColor(BRAND_LIGHT)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    c.setFillColor(BRAND_COLOR)
    c.rect(0, PAGE_H - 0.7*inch, PAGE_W, 0.7*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FB(), 16)
    c.drawCentredString(PAGE_W/2, PAGE_H - 0.45*inch, "Caller Cards — Read the problem, players find the answer!")

    # Grid of caller cards: 6 columns × 8 rows = 48 per page
    cols = 6
    rows = 8
    pad = 0.45*inch
    cw = (PAGE_W - 2*pad) / cols
    ch = (PAGE_H - 1.2*inch) / rows

    row_colors = [BRAND_COLOR, SECONDARY, HexColor("#5B2D8E"), BRAND_COLOR,
                  SECONDARY, HexColor("#5B2D8E"), BRAND_COLOR, SECONDARY]

    for idx, (a, b) in enumerate(callers_list[:48]):
        ci = idx % cols
        ri = idx // cols
        if ri >= rows:
            break
        cx = pad + ci * cw
        cy = PAGE_H - 1.0*inch - (ri+1)*ch + 4

        c.setFillColor(row_colors[ri])
        c.roundRect(cx+3, cy+3, cw-6, ch-6, 5, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(FB(), 14)
        c.drawCentredString(cx+cw/2, cy+ch/2+1, f"{a} × {b}")
        c.setFont(FN(), 8)
        c.drawCentredString(cx+cw/2, cy+ch/2-12, "= ?")

    c.setFillColor(SECONDARY)
    c.rect(0, 0, PAGE_W, 0.35*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FN(), 8)
    c.drawCentredString(PAGE_W/2, 0.1*inch, AUTHOR + "  •  Bingo Caller Cards — Cut apart and use to call the game")

def build():
    out = ROOT / "products/tpt/samples/bingo_cards/sample.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out), pagesize=letter)

    random.seed(42)
    # 3 sample bingo cards
    for card_num in range(1, 4):
        grid = make_bingo_card(card_num)
        draw_bingo_card(c, card_num, grid)
        c.showPage()

    # 1 page of caller cards
    random.shuffle(CALLERS)
    draw_caller_page(c, CALLERS)
    c.showPage()

    c.save()
    print(f"✓ bingo_cards  → {out}  ({out.stat().st_size:,} bytes)")

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
