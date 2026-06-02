"""
BrightOwl Learning — Number Sense Pack
Halloween theme · Grade 2 · 6 activity pages

Pages:
  1. Hundreds Chart (1-100)
  2. Ten Frames (pumpkin counts)
  3. Number Bonds
  4. Skip Counting
  5. Greater / Less / Equal
  6. Expanded Form
"""
from __future__ import annotations
import math
from pathlib import Path
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

PAGE_W, PAGE_H = letter
M       = 0.45 * inch
BRAND   = "#E8771A"
DARK    = "#2C3E50"
LIGHT   = "#FFF5E6"
AUTHOR  = "BrightOwl Learning"
FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"
_REG = False

def _reg():
    global _REG
    if _REG: return
    f = FONT_DIR / "Nunito-Regular.ttf"
    if f.exists():
        try:
            pdfmetrics.registerFont(TTFont("Nunito",      str(f)))
            pdfmetrics.registerFont(TTFont("Nunito-Bold", str(FONT_DIR/"Nunito-Bold.ttf")))
            _REG = True
        except Exception: pass

def F(b=False):
    _reg()
    if b: return "Nunito-Bold" if _REG else "Helvetica-Bold"
    return "Nunito" if _REG else "Helvetica"

def header(c, title, subtitle=""):
    hh = 0.50 * inch
    hy = PAGE_H - M - hh
    c.setFillColor(HexColor(BRAND))
    c.roundRect(M, hy, PAGE_W-2*M, hh, 8, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(F(True), 17); c.drawCentredString(PAGE_W/2, hy+hh/2+1, title)
    c.setFont(F(), 9);       c.drawCentredString(PAGE_W/2, hy+7, subtitle or AUTHOR)
    return hy - 10

def footer(c):
    c.setFont(F(), 7.5); c.setFillColor(HexColor("#AAAAAA"))
    c.drawString(M, 0.22*inch, f"© 2026 {AUTHOR}  —  For single classroom use only.")
    c.drawRightString(PAGE_W-M, 0.22*inch, "BrightOwl Learning  ·  No Prep")

def pumpkin(c, x, y, r=8):
    c.saveState()
    c.setFillColor(HexColor(BRAND)); c.setStrokeColor(HexColor(DARK)); c.setLineWidth(0.6)
    c.ellipse(x-r*.9, y-r*.6, x+r*.9, y+r*.6, fill=1, stroke=1)
    c.setFillColor(HexColor("#4CAF50"))
    c.roundRect(x-r*.08, y+r*.55, r*.18, r*.5, 1, fill=1, stroke=0)
    c.setFillColor(HexColor(DARK))
    p = c.beginPath(); p.moveTo(x-r*.4,y+r*.1); p.lineTo(x-r*.1,y+r*.1); p.lineTo(x-r*.25,y+r*.35); p.close(); c.drawPath(p, fill=1, stroke=0)
    p = c.beginPath(); p.moveTo(x+r*.1,y+r*.1); p.lineTo(x+r*.4,y+r*.1); p.lineTo(x+r*.25,y+r*.35); p.close(); c.drawPath(p, fill=1, stroke=0)
    for dx in (-r*.28, 0, r*.28):
        c.rect(x+dx-r*.09, y-r*.35, r*.16, r*.15, fill=1, stroke=0)
    c.restoreState()

# ── PAGE 1 — Hundreds Chart ───────────────────────────────────────────────────
def page_hundreds(c):
    top = header(c, "Hundreds Chart", "Color EVEN numbers orange  ·  Color ODD numbers black")
    top -= 6
    cols, rows = 10, 10
    cell = min((PAGE_W-2*M)/cols, (top-M-6)/rows)
    gw, gh = cell*cols, cell*rows
    ox = (PAGE_W-gw)/2
    oy = top - gh
    for n in range(1, 101):
        col = (n-1) % 10
        row = (n-1) // 10
        x = ox + col*cell; y = oy + (rows-1-row)*cell
        # Header row/col shading
        c.setFillColor(HexColor("#F0E6D3")); c.setStrokeColor(HexColor("#CCCCCC")); c.setLineWidth(0.4)
        c.rect(x, y, cell, cell, fill=1, stroke=1)
        c.setFillColor(black); c.setFont(F(), cell*.38)
        c.drawCentredString(x+cell/2, y+cell*.28, str(n))
    # Pumpkin corners
    for px, py in ((ox-18, oy+gh+6), (ox+gw+6, oy+gh+6)):
        pumpkin(c, px+10, py-6, 10)
    footer(c); c.showPage()

# ── PAGE 2 — Ten Frames ───────────────────────────────────────────────────────
COUNTS = [3, 7, 5, 10, 2, 8, 4, 6]

def ten_frame(c, ox, oy, fw, fh, count):
    cw, ch = fw/5, fh/2
    for cell_i in range(10):
        col = cell_i % 5; row = cell_i // 5
        x = ox + col*cw; y = oy + (1-row)*ch
        c.setFillColor(white); c.setStrokeColor(HexColor(DARK)); c.setLineWidth(1)
        c.rect(x, y, cw, ch, fill=1, stroke=1)
        if cell_i < count:
            pumpkin(c, x+cw/2, y+ch/2, min(cw,ch)*.32)

def page_ten_frames(c):
    top = header(c, "Ten Frames", "Count the pumpkins. Write the number.")
    top -= 12
    cols, rows = 2, 4
    pad = 8
    fw = (PAGE_W-2*M - pad*(cols+1)) / cols
    fh = (top - M - 30 - pad*(rows+1)) / rows
    for i, count in enumerate(COUNTS):
        col = i % cols; row = i // cols
        ox = M + pad + col*(fw+pad)
        oy = top - 30 - (row+1)*(fh+pad) + pad
        c.setFillColor(HexColor(LIGHT)); c.setStrokeColor(HexColor(BRAND)); c.setLineWidth(1)
        c.roundRect(ox-4, oy-22, fw+8, fh+30, 4, fill=1, stroke=1)
        ten_frame(c, ox, oy, fw, fh, count)
        c.setFont(F(), 9); c.setFillColor(black)
        c.drawString(ox, oy-16, "How many pumpkins? ____")
    footer(c); c.showPage()

# ── PAGE 3 — Number Bonds ─────────────────────────────────────────────────────
BONDS = [
    (10, 4, None),(8, None, 5),(15, 7, None),(12, None, 9),
    (11, 6, None),(14, None, 8),(9, 3, None),(16, None, 7),
    (13, 5, None),(7, None, 4),(18, 9, None),(20, None, 11),
]

def bond(c, cx, cy, r, whole, a, b):
    # Top circle (whole)
    c.setFillColor(HexColor(BRAND) if whole is not None else white)
    c.setStrokeColor(HexColor(DARK)); c.setLineWidth(1.2)
    c.circle(cx, cy+r*1.6, r*.9, fill=1, stroke=1)
    c.setFillColor(white if whole else black); c.setFont(F(True), r*.9)
    if whole is not None: c.drawCentredString(cx, cy+r*1.3, str(whole))
    # Lines
    c.setStrokeColor(HexColor(DARK))
    c.line(cx, cy+r*.7, cx-r*1.1, cy-r*.3)
    c.line(cx, cy+r*.7, cx+r*1.1, cy-r*.3)
    # Bottom circles
    for part, dx in ((a, -1.2), (b, 1.2)):
        c.setFillColor(HexColor(LIGHT) if part is not None else HexColor("#FFFFEE"))
        c.circle(cx+dx*r, cy-r*.5, r*.9, fill=1, stroke=1)
        c.setFillColor(black); c.setFont(F(True if part else False), r*.9)
        if part is not None: c.drawCentredString(cx+dx*r, cy-r*.8, str(part))
        else:
            c.setStrokeColor(HexColor("#999")); c.setLineWidth(0.5)
            c.line(cx+dx*r-r*.4, cy-r*.6, cx+dx*r+r*.4, cy-r*.6)

def page_bonds(c):
    top = header(c, "Number Bonds", "Fill in the missing number in each bond.")
    top -= 10
    cols, rows = 4, 3
    cw = (PAGE_W-2*M) / cols
    ch = (top - M - 8) / rows
    for i, (whole, a, b_) in enumerate(BONDS):
        col = i % cols; row = i // cols
        cx = M + col*cw + cw/2
        cy = top - (row+.5)*ch - 4
        bond(c, cx, cy, min(cw,ch)*.12, whole, a, b_)
    footer(c); c.showPage()

# ── PAGE 4 — Skip Counting ────────────────────────────────────────────────────
SKIP_SEQS = [
    ("Skip count by 2s",  [2,4,None,8,None,12,None,16,None,20]),
    ("Skip count by 5s",  [5,10,None,20,None,30,None,40,None,50]),
    ("Skip count by 10s", [10,None,30,None,50,None,70,None,90,None]),
    ("Skip count by 3s",  [3,None,9,None,15,None,21,None,27,None]),
]

def page_skip(c):
    top = header(c, "Skip Counting", "Fill in the missing numbers.")
    top -= 14
    row_h = (top - M - 8) / len(SKIP_SEQS)
    for si, (label, seq) in enumerate(SKIP_SEQS):
        ry = top - (si+1)*row_h + 4
        # Label
        c.setFont(F(True), 10); c.setFillColor(HexColor(DARK))
        c.drawString(M, ry+row_h/2, label)
        # Boxes
        n = len(seq); bw = (PAGE_W-2*M-1.5*inch)/n; bh = min(row_h*.55, 30)
        bx0 = M + 1.5*inch
        for j, val in enumerate(seq):
            bx = bx0 + j*bw
            by = ry + row_h/2 - bh/2
            filled = val is not None
            c.setFillColor(HexColor("#FFE0B2") if filled else white)
            c.setStrokeColor(HexColor(BRAND)); c.setLineWidth(1)
            c.roundRect(bx+1, by, bw-2, bh, 3, fill=1, stroke=1)
            if filled:
                c.setFillColor(HexColor(DARK)); c.setFont(F(True), bh*.5)
                c.drawCentredString(bx+bw/2, by+bh*.22, str(val))
        # Arrow between boxes
        c.setStrokeColor(HexColor("#CCCCCC")); c.setLineWidth(0.5)
    footer(c); c.showPage()

# ── PAGE 5 — Greater / Less / Equal ──────────────────────────────────────────
COMPARE = [
    (35,53),(47,74),(28,28),(91,19),(62,62),(50,48),
    (73,37),(16,61),(84,84),(29,92),(55,45),(38,83),
    (66,56),(44,44),(71,17),(87,78),
]

def page_compare(c):
    top = header(c, "Greater, Less, or Equal?", "Write  >  <  or  =  in the box.")
    top -= 12
    cols, rows = 4, 4
    cw = (PAGE_W-2*M-8) / cols
    ch = (top - M - 8) / rows
    for i, (a, b) in enumerate(COMPARE):
        col = i % cols; row = i // cols
        cx = M + col*(cw+2)
        cy = top - (row+1)*ch + 4
        correct = ">" if a>b else ("<" if a<b else "=")
        c.setFillColor(HexColor(LIGHT)); c.setStrokeColor(HexColor(BRAND)); c.setLineWidth(0.8)
        c.roundRect(cx+2, cy+2, cw-4, ch-4, 4, fill=1, stroke=1)
        mid = cx+cw/2; my = cy+ch/2
        c.setFont(F(True), 14); c.setFillColor(HexColor(DARK))
        c.drawRightString(mid-16, my-5, str(a))
        c.drawString(mid+16, my-5, str(b))
        # Symbol box
        c.setFillColor(white); c.setStrokeColor(HexColor("#888")); c.setLineWidth(0.8)
        c.rect(mid-10, my-9, 20, 18, fill=1, stroke=1)
        c.setFont(F(), 6.5); c.setFillColor(HexColor("#AAAAAA"))
        c.drawCentredString(mid, my-5, ">  <  =")
    footer(c); c.showPage()

# ── PAGE 6 — Expanded Form ───────────────────────────────────────────────────
EXP_A = [(200,40,3),(500,70,8),(300,20,5),(400,60,9)]
EXP_B = [574, 263, 815, 492]
EXP_C = [(3,"three hundred forty-two",342),(1,"one hundred fifty-six",156)]

def page_expanded(c):
    top = header(c, "Expanded Form", "Write numbers in expanded form.")
    y = top - 14

    def section(title, items, draw_fn):
        nonlocal y
        c.setFont(F(True), 11); c.setFillColor(HexColor(BRAND))
        c.drawString(M, y, title)
        y -= 4
        c.setStrokeColor(HexColor(BRAND)); c.setLineWidth(0.5)
        c.line(M, y, PAGE_W-M, y); y -= 14
        draw_fn(items)
        y -= 8

    def draw_A(items):
        nonlocal y
        cw2 = (PAGE_W-2*M-10)/2
        for i, (h,t,o) in enumerate(items):
            col = i%2
            if col==0 and i>0: y -= 26
            cx = M + col*(cw2+10)
            c.setFont(F(), 10); c.setFillColor(black)
            expr = f"{h} + {t} + {o} = "
            c.drawString(cx, y, expr)
            tw = c.stringWidth(expr, F(), 10)
            c.setStrokeColor(HexColor("#888")); c.setLineWidth(0.7)
            c.line(cx+tw+2, y, cx+cw2-4, y)
        y -= 26

    def draw_B(items):
        nonlocal y
        cw2 = (PAGE_W-2*M-10)/2
        for i, n in enumerate(items):
            col = i%2
            if col==0 and i>0: y -= 26
            cx = M + col*(cw2+10)
            c.setFont(F(True), 11); c.setFillColor(HexColor(DARK))
            c.drawString(cx, y, f"{n}  =  ")
            tw = c.stringWidth(f"{n}  =  ", F(True), 11)
            # Three blanks with + between
            bw = 40
            for bi in range(3):
                bx = cx+tw+bi*(bw+14)
                c.setStrokeColor(HexColor("#888")); c.setLineWidth(0.7)
                c.line(bx, y, bx+bw, y)
                if bi < 2:
                    c.setFont(F(True), 11); c.setFillColor(black)
                    c.drawString(bx+bw+2, y, "+")
        y -= 26

    def draw_C(items):
        nonlocal y
        for _, label, num in items:
            c.setFont(F(), 10); c.setFillColor(black)
            c.drawString(M, y, f"{num}  →  Write in words:")
            c.setStrokeColor(HexColor("#888")); c.setLineWidth(0.7)
            lx = M + c.stringWidth(f"{num}  →  Write in words:", F(), 10) + 8
            c.line(lx, y, PAGE_W-M, y)
            y -= 18

    section("A.  Add to find the number:", EXP_A, draw_A)
    section("B.  Break the number apart:", EXP_B, draw_B)
    section("C.  Write the number in words:", EXP_C, draw_C)

    footer(c); c.showPage()


# ── Main ─────────────────────────────────────────────────────────────────────

def build(out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out_path), pagesize=letter)
    page_hundreds(c)
    page_ten_frames(c)
    page_bonds(c)
    page_skip(c)
    page_compare(c)
    page_expanded(c)
    c.save()
    print(f"✓ number_sense  → {out_path}  ({out_path.stat().st_size:,} bytes)")


def build_all(out_dir=None, themes=None, gemini_key=None):
    base = Path(out_dir) if out_dir else Path(__file__).resolve().parents[3] / "products" / "tpt"
    build(base / "samples" / "number_sense" / "sample.pdf")


if __name__ == "__main__":
    build_all()
