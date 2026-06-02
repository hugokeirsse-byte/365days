"""
Halloween Exit Tickets — Multiplication Grade 3
BrightOwl Learning  |  5 pages, 4 tickets per page = 20 total
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

# 20 problems
PROBLEMS = [
    (2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,9),(2,7),(3,6),(4,8),
    (5,9),(6,8),(2,9),(3,7),(4,9),(5,7),(6,9),(3,9),(4,7),(7,9),
]

def draw_mini_pumpkin(c, cx, cy, r=8):
    c.setFillColor(BRAND_COLOR)
    c.circle(cx, cy, r, fill=1, stroke=0)
    c.ellipse(cx-r*0.65, cy-r*0.45, cx-r*0.05, cy+r*0.45, fill=1, stroke=0)
    c.ellipse(cx+r*0.05, cy-r*0.45, cx+r*0.65, cy+r*0.45, fill=1, stroke=0)
    c.setFillColor(HexColor("#2D9A2D"))
    c.setLineWidth(1.5)
    c.setStrokeColor(HexColor("#2D9A2D"))
    c.line(cx, cy+r, cx+r*0.4, cy+r*1.4)
    c.setFillColor(black)
    c.circle(cx-r*0.28, cy+r*0.05, r*0.12, fill=1, stroke=0)
    c.circle(cx+r*0.28, cy+r*0.05, r*0.12, fill=1, stroke=0)
    p = c.beginPath()
    p.moveTo(cx-r*0.3, cy-r*0.12)
    p.lineTo(cx-r*0.12, cy-r*0.3)
    p.lineTo(cx+r*0.12, cy-r*0.3)
    p.lineTo(cx+r*0.3, cy-r*0.12)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

def draw_ticket(c, x, y, w, h, ticket_num, problems_triple):
    # Border + background
    c.setFillColor(BRAND_LIGHT)
    c.setStrokeColor(BRAND_COLOR)
    c.setLineWidth(1.5)
    c.roundRect(x+3, y+3, w-6, h-6, 6, fill=1, stroke=1)

    # Orange header strip
    c.setFillColor(BRAND_COLOR)
    c.roundRect(x+3, y+h-28, w-6, 25, 4, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FB(), 10)
    c.drawString(x+10, y+h-18, f"Exit Ticket #{ticket_num}")
    c.setFont(FN(), 8)
    c.drawRightString(x+w-8, y+h-18, "Halloween Math")

    # Pumpkin
    draw_mini_pumpkin(c, x+w-18, y+h-14, r=7)

    # Name / Date line
    c.setStrokeColor(HexColor("#AAAAAA"))
    c.setLineWidth(0.5)
    c.line(x+8, y+h-38, x+w/2-5, y+h-38)
    c.line(x+w/2+5, y+h-38, x+w-8, y+h-38)
    c.setFillColor(HexColor("#888888"))
    c.setFont(FN(), 7)
    c.drawString(x+8, y+h-47, "Name:")
    c.drawString(x+w/2+5, y+h-47, "Date:")

    # Problems
    prob_start = y + h - 56
    for i, (a, b) in enumerate(problems_triple):
        py = prob_start - i * 22
        c.setFillColor(SECONDARY)
        c.setFont(FB(), 12)
        c.drawString(x+10, py, f"{i+1}.  {a} × {b} = ____")

    # Self-assessment
    sa_y = y + 16
    c.setFont(FB(), 8)
    c.setFillColor(SECONDARY)
    c.drawString(x+8, sa_y+4, "I can multiply:  ")
    # Checkboxes
    box_x = x + 90
    for label in ["I got it! ✓", "I need help"]:
        c.setStrokeColor(BRAND_COLOR)
        c.setFillColor(white)
        c.setLineWidth(1)
        c.rect(box_x, sa_y, 10, 10, fill=1, stroke=1)
        c.setFillColor(SECONDARY)
        c.setFont(FN(), 8)
        c.drawString(box_x+13, sa_y+1, label)
        box_x += 80

def draw_dashed_line_h(c, x, y, length):
    c.setStrokeColor(HexColor("#AAAAAA"))
    c.setLineWidth(0.5)
    c.setDash([4, 3])
    c.line(x, y, x+length, y)
    c.setDash([])

def draw_dashed_line_v(c, x, y, length):
    c.setStrokeColor(HexColor("#AAAAAA"))
    c.setLineWidth(0.5)
    c.setDash([4, 3])
    c.line(x, y, x, y+length)
    c.setDash([])

def draw_header(c, title):
    c.setFillColor(BRAND_COLOR)
    c.rect(0, PAGE_H - 0.5*inch, PAGE_W, 0.5*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FB(), 13)
    c.drawCentredString(PAGE_W/2, PAGE_H - 0.34*inch, title)

def draw_footer(c):
    c.setFillColor(SECONDARY)
    c.rect(0, 0, PAGE_W, 0.3*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FN(), 8)
    c.drawCentredString(PAGE_W/2, 0.08*inch, AUTHOR + "  •  Halloween Exit Tickets  •  Grade 3")

def build():
    out = ROOT / "products/tpt/samples/exit_tickets/sample.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out), pagesize=letter)

    TICKET_W = (PAGE_W - 0.8*inch) / 2
    TICKET_H = (PAGE_H - 1.2*inch) / 2

    for page in range(5):
        draw_header(c, "Halloween Exit Tickets — Multiplication  |  Grade 3")
        draw_footer(c)

        for slot in range(4):
            ticket_num = page * 4 + slot + 1
            probs = [PROBLEMS[(ticket_num-1+j) % len(PROBLEMS)] for j in range(3)]

            col = slot % 2
            row = slot // 2
            tx = 0.4*inch + col * TICKET_W
            ty = 0.35*inch + (1 - row) * TICKET_H

            draw_ticket(c, tx, ty, TICKET_W, TICKET_H, ticket_num, probs)

        # Cut lines
        draw_dashed_line_h(c, 0.3*inch, 0.35*inch + TICKET_H, PAGE_W - 0.6*inch)
        draw_dashed_line_v(c, 0.4*inch + TICKET_W, 0.3*inch, PAGE_H - 0.6*inch)

        # Scissors icon hint
        c.setFont(FN(), 8)
        c.setFillColor(HexColor("#999999"))
        c.drawString(0.3*inch, 0.35*inch + TICKET_H + 2, "✂  Cut along dashed lines")

        c.showPage()

    c.save()
    print(f"✓ exit_tickets  → {out}  ({out.stat().st_size:,} bytes)")

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
