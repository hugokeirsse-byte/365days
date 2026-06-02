"""
Halloween Math Task Cards — Multiplication Grade 3
BrightOwl Learning  |  36 cards, 4 per page
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

# 36 multiplication problems 2×2 through 9×9 unique
PROBLEMS = []
for a in range(2, 10):
    for b in range(a, 10):
        PROBLEMS.append((a, b))
# exactly 36 pairs from (2,2) to (9,9) = 8+7+6+5+4+3+2+1 = 36
assert len(PROBLEMS) == 36

def draw_pumpkin(c, cx, cy, r=12):
    """Draw a tiny pumpkin at (cx,cy) with radius r."""
    # Body
    c.setFillColor(BRAND_COLOR)
    c.setStrokeColor(HexColor("#8B4513"))
    c.setLineWidth(1)
    c.circle(cx, cy, r, fill=1, stroke=1)
    # Left lobe
    c.setFillColor(BRAND_COLOR)
    c.ellipse(cx-r*0.6, cy-r*0.5, cx-r*0.05, cy+r*0.5, fill=1, stroke=0)
    # Right lobe
    c.ellipse(cx+r*0.05, cy-r*0.5, cx+r*0.6, cy+r*0.5, fill=1, stroke=0)
    # Stem
    c.setFillColor(HexColor("#2D9A2D"))
    c.setStrokeColor(HexColor("#2D9A2D"))
    c.setLineWidth(2)
    c.line(cx, cy+r, cx+r*0.3, cy+r*1.5)
    # Face
    c.setFillColor(black)
    eye_r = r * 0.12
    c.circle(cx - r*0.3, cy + r*0.1, eye_r, fill=1, stroke=0)
    c.circle(cx + r*0.3, cy + r*0.1, eye_r, fill=1, stroke=0)
    # Mouth (3 teeth triangles)
    p = c.beginPath()
    p.moveTo(cx - r*0.35, cy - r*0.15)
    p.lineTo(cx - r*0.15, cy - r*0.35)
    p.lineTo(cx + r*0.15, cy - r*0.35)
    p.lineTo(cx + r*0.35, cy - r*0.15)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

def draw_card(c, x, y, w, h, num, a, b):
    """Draw a single task card at (x,y) width w height h."""
    # Background
    c.setFillColor(BRAND_LIGHT)
    c.setStrokeColor(BRAND_COLOR)
    c.setLineWidth(2)
    c.roundRect(x+4, y+4, w-8, h-8, 8, fill=1, stroke=1)

    # Orange top band
    c.setFillColor(BRAND_COLOR)
    c.roundRect(x+4, y+h-36, w-8, 32, 6, fill=1, stroke=0)

    # Card number
    c.setFillColor(white)
    c.setFont(FB(), 11)
    c.drawString(x+12, y+h-24, f"#{num}")

    # "Halloween Multiplication" label
    c.setFont(FN(), 8)
    c.drawCentredString(x+w/2, y+h-24, "Halloween Multiplication")

    # Pumpkin decoration top-right
    draw_pumpkin(c, x+w-24, y+h-22, r=10)

    # Problem
    c.setFillColor(SECONDARY)
    c.setFont(FB(), 28)
    c.drawCentredString(x+w/2, y+h*0.45, f"{a}  ×  {b}  =  ?")

    # Underline for answer
    c.setStrokeColor(SECONDARY)
    c.setLineWidth(1)
    uw = w * 0.3
    c.line(x+w/2-uw/2, y+h*0.28, x+w/2+uw/2, y+h*0.28)
    c.setFont(FN(), 9)
    c.setFillColor(HexColor("#888888"))
    c.drawCentredString(x+w/2, y+h*0.17, "Write your answer above")

    # Footer
    c.setFillColor(SECONDARY)
    c.setFont(FN(), 7)
    c.drawCentredString(x+w/2, y+12, AUTHOR)

def draw_trim_marks(c, x, y, w, h, margin=6):
    c.setStrokeColor(HexColor("#AAAAAA"))
    c.setLineWidth(0.4)
    c.setDash([3,3])
    # vertical center
    c.line(x+w/2, y-margin, x+w/2, y+h+margin)
    # horizontal center
    c.line(x-margin, y+h/2, x+w+margin, y+h/2)
    c.setDash([])

def draw_header(c, title):
    c.setFillColor(BRAND_COLOR)
    c.rect(0, PAGE_H - 0.55*inch, PAGE_W, 0.55*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FB(), 14)
    c.drawCentredString(PAGE_W/2, PAGE_H - 0.38*inch, title)

def draw_footer(c, msg):
    c.setFillColor(SECONDARY)
    c.rect(0, 0, PAGE_W, 0.35*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FN(), 8)
    c.drawCentredString(PAGE_W/2, 0.1*inch, msg)

def build():
    out = ROOT / "products/tpt/samples/task_cards/sample.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out), pagesize=letter)

    CARD_W = (PAGE_W - 1.2*inch) / 2
    CARD_H = (PAGE_H - 1.6*inch) / 2
    LEFT   = 0.6*inch
    BOTTOM = 0.55*inch

    # Pages 1-2: first 2 pages of cards (8 cards, pages 1-2)
    for page_idx in range(2):
        draw_header(c, "Halloween Task Cards — Multiplication  |  Grade 3")
        draw_footer(c, f"CUT CARDS APART — Store in a bag or envelope  •  {AUTHOR}")

        for slot in range(4):
            card_num = page_idx * 4 + slot + 1
            a, b = PROBLEMS[card_num - 1]
            col = slot % 2
            row = slot // 2
            cx = LEFT + col * CARD_W
            cy = BOTTOM + (1 - row) * CARD_H
            draw_card(c, cx, cy, CARD_W, CARD_H, card_num, a, b)

        draw_trim_marks(c, LEFT, BOTTOM, PAGE_W-1.2*inch, PAGE_H-1.6*inch)
        c.showPage()

    # Answer key page
    draw_header(c, "ANSWER KEY — Halloween Task Cards")
    c.setFont(FN(), 9)
    c.setFillColor(HexColor("#999999"))
    c.drawCentredString(PAGE_W/2, PAGE_H - 0.68*inch, "All 36 problems and answers")

    # Table of answers
    cols_per_row = 4
    col_w = (PAGE_W - 1.2*inch) / cols_per_row
    start_y = PAGE_H - 0.95*inch
    row_h = 0.32*inch

    # Header row
    headers = ["Card", "Problem", "Answer", "  "] * (cols_per_row // 4)
    c.setFillColor(BRAND_COLOR)
    c.rect(0.6*inch, start_y, PAGE_W-1.2*inch, row_h, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FB(), 10)
    for ci in range(cols_per_row):
        lbl = ["Card #", "Problem", "=", ""][ci % 4] if cols_per_row == 4 else ""
    # Draw headers for 2 groups of 3 cols (card, problem, answer)
    groups = 3  # 3 columns per table: card#, problem, answer
    group_cols = 3
    num_groups = 3  # 3 side-by-side tables
    group_w = (PAGE_W - 1.2*inch) / num_groups
    c.setFillColor(BRAND_COLOR)
    c.rect(0.6*inch, start_y, PAGE_W-1.2*inch, row_h, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FB(), 9)
    for g in range(num_groups):
        gx = 0.6*inch + g * group_w
        c.drawString(gx+4, start_y+8, "Card")
        c.drawString(gx+group_w*0.35, start_y+8, "Problem")
        c.drawString(gx+group_w*0.72, start_y+8, "Answer")

    # rows per group
    per_group = 12  # 36 / 3 = 12 rows each
    for i, (a, b) in enumerate(PROBLEMS):
        g = i // per_group
        ri = i % per_group
        gx = 0.6*inch + g * group_w
        ry = start_y - (ri+1)*row_h

        bg = BRAND_LIGHT if ri % 2 == 0 else white
        c.setFillColor(HexColor("#FFF5E6") if ri % 2 == 0 else white)
        c.rect(gx, ry, group_w, row_h, fill=1, stroke=0)

        c.setFillColor(SECONDARY)
        c.setFont(FB(), 9)
        c.drawString(gx+8, ry+8, f"#{i+1}")
        c.setFont(FN(), 9)
        c.drawString(gx+group_w*0.35, ry+8, f"{a} × {b} =")
        c.setFont(FB(), 9)
        c.setFillColor(BRAND_COLOR)
        c.drawString(gx+group_w*0.72, ry+8, str(a*b))

    # Grid lines
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(0.3)
    for i in range(per_group+1):
        line_y = start_y - i*row_h
        c.line(0.6*inch, line_y, PAGE_W-0.6*inch, line_y)

    draw_footer(c, AUTHOR + "  •  Halloween Task Cards Answer Key")
    c.showPage()
    c.save()
    print(f"✓ task_cards  → {out}  ({out.stat().st_size:,} bytes)")

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
