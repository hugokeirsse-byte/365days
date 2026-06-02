"""
TPT — Color by Code : Halloween Multiplication (Grade 3)
100% procédural, zéro IA, zéro asset externe.

Usage:
  python scripts/tpt/color_by_code.py
  OUT_DIR=products/tpt/cbc_halloween python scripts/tpt/color_by_code.py
"""
import math
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas as rl_canvas

PAGE_W, PAGE_H = letter   # 612 × 792 pt
M = 0.5 * inch

COLOR_CODE = [
    (15, "Purple",  HexColor("#7B2FBE")),
    (18, "Yellow",  HexColor("#FFD700")),
    (12, "Orange",  HexColor("#E8771A")),
    ( 6, "Green",   HexColor("#2D7A2D")),
    (24, "Black",   HexColor("#111111")),
]
ANS_MAP = {ans: (name, col) for ans, name, col in COLOR_CODE}

PROBLEMS = [
    (3, "×", 5, 15), (5, "×", 3, 15),
    (6, "×", 3, 18), (9, "×", 2, 18),
    (3, "×", 4, 12), (4, "×", 3, 12),
    (2, "×", 3,  6), (3, "×", 2,  6),
    (8, "×", 3, 24), (6, "×", 4, 24),
]


# ── Draw primitives ────────────────────────────────────────────────────────────

def poly(c, pts, fill_col, stroke_col=None, lw=1.5):
    c.saveState()
    c.setFillColor(fill_col)
    p = c.beginPath()
    p.moveTo(*pts[0])
    for x, y in pts[1:]:
        p.lineTo(x, y)
    p.close()
    if stroke_col:
        c.setStrokeColor(stroke_col)
        c.setLineWidth(lw)
        c.drawPath(p, fill=1, stroke=1)
    else:
        c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def star_pts(cx, cy, r_out, r_in):
    pts = []
    for i in range(10):
        a = math.radians(90 - i * 36)
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def lbl(c, x, y, text, size=11, col=black, bold=False):
    c.saveState()
    c.setFillColor(col)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawCentredString(x, y, text)
    c.restoreState()


# ── Scene ─────────────────────────────────────────────────────────────────────

def draw_scene(c, x0, y0, w, h):
    cx = x0 + w / 2
    purple = HexColor("#7B2FBE")
    yellow = HexColor("#FFD700")
    orange = HexColor("#E8771A")
    green  = HexColor("#2D7A2D")
    blk    = HexColor("#111111")
    dark_o = HexColor("#A04500")

    # Sky (purple, answer 15)
    c.saveState()
    c.setFillColor(purple)
    c.rect(x0, y0, w, h, fill=1, stroke=0)
    c.restoreState()
    lbl(c, x0 + 18, y0 + h - 18, "15", 11, white, bold=True)

    # Ground strip (green, answer 6)
    gh = h * 0.13
    c.saveState()
    c.setFillColor(green)
    c.rect(x0, y0, w, gh, fill=1, stroke=0)
    c.restoreState()
    lbl(c, cx, y0 + gh * 0.45, "6", 11, white, bold=True)

    # Moon (yellow, answer 18)
    mr = min(w, h) * 0.085
    mcx, mcy = x0 + w * 0.79, y0 + h * 0.84
    c.saveState()
    c.setFillColor(yellow)
    c.setStrokeColor(HexColor("#C8A800"))
    c.setLineWidth(1)
    c.circle(mcx, mcy, mr, fill=1, stroke=1)
    c.restoreState()
    lbl(c, mcx, mcy - 5, "18", 9, purple, bold=True)

    # Stars (yellow, answer 18)
    for sx, sy, ro in [
        (x0 + w*0.13, y0 + h*0.88, h*0.025),
        (x0 + w*0.30, y0 + h*0.92, h*0.018),
        (x0 + w*0.50, y0 + h*0.86, h*0.020),
        (x0 + w*0.63, y0 + h*0.77, h*0.016),
    ]:
        poly(c, star_pts(sx, sy, ro, ro*0.42), yellow)
        lbl(c, sx, sy - ro * 0.7, "18", 6, purple)

    # Pumpkin body (orange, answer 12)
    pcx, pcy = cx, y0 + gh + h * 0.30
    prx, pry = w * 0.40, h * 0.24
    c.saveState()
    c.setFillColor(orange)
    c.setStrokeColor(dark_o)
    c.setLineWidth(2)
    c.ellipse(pcx - prx, pcy - pry, pcx + prx, pcy + pry, fill=1, stroke=1)
    c.setStrokeColor(dark_o)
    c.setLineWidth(1.5)
    for dx in (-prx*0.37, prx*0.37):
        c.bezier(pcx+dx, pcy+pry*0.88,
                 pcx+dx*0.45, pcy+pry*0.28,
                 pcx+dx*0.45, pcy-pry*0.28,
                 pcx+dx, pcy-pry*0.88)
    c.restoreState()
    lbl(c, pcx, pcy - 6, "12", 14, white, bold=True)

    # Stem (green, answer 6)
    sw_, sh_ = prx * 0.18, h * 0.10
    c.saveState()
    c.setFillColor(green)
    c.setStrokeColor(HexColor("#1A5E1A"))
    c.setLineWidth(1)
    c.rect(pcx - sw_/2, pcy + pry - 4, sw_, sh_, fill=1, stroke=1)
    c.restoreState()
    lbl(c, pcx, pcy + pry + sh_ * 0.32, "6", 8, white, bold=True)

    # Eyes — two triangles (black, answer 24)
    ey_top = pcy + pry * 0.10
    ew_, eh_ = prx * 0.20, pry * 0.28
    for ex in (pcx - prx*0.38, pcx + prx*0.38):
        poly(c, [(ex, ey_top), (ex-ew_, ey_top-eh_), (ex+ew_, ey_top-eh_)], blk, blk, 1)
        lbl(c, ex, ey_top - eh_*0.72, "24", 7, white, bold=True)

    # Mouth with teeth (black, answer 24; teeth orange like pumpkin body)
    mty = pcy - pry * 0.22
    mw_ = prx * 0.72
    mh_ = pry * 0.24
    mx_ = pcx - mw_
    poly(c, [(mx_, mty), (mx_+mw_*2, mty),
             (mx_+mw_*2, mty-mh_*0.6), (mx_, mty-mh_*0.6)], blk)
    tw_ = mw_ * 2 / 5
    for i in range(4):
        tx = mx_ + tw_*(i+1)
        poly(c, [(tx-tw_*0.38, mty), (tx+tw_*0.38, mty), (tx, mty-mh_*0.52)], orange)
    lbl(c, pcx, mty - mh_*0.30, "24", 7, white, bold=True)

    # Scene border
    c.saveState()
    c.setStrokeColor(HexColor("#333333"))
    c.setLineWidth(2)
    c.rect(x0, y0, w, h, fill=0, stroke=1)
    c.restoreState()


# ── Color key strip (horizontal, full width) ───────────────────────────────────

def draw_key_strip(c, x0, y0, w, h):
    c.saveState()
    c.setFillColor(HexColor("#FFF3E0"))
    c.setStrokeColor(HexColor("#E8771A"))
    c.setLineWidth(1)
    c.roundRect(x0, y0, w, h, 4, fill=1, stroke=1)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(black)
    c.drawString(x0 + 6, y0 + h/2 - 4, "COLOR KEY:")
    sw_ = 12
    reserve = 76
    item_w = (w - reserve) / len(COLOR_CODE)
    for i, (ans, name, col) in enumerate(COLOR_CODE):
        ix = x0 + reserve + i * item_w
        iy = y0 + h/2 - sw_/2
        c.setFillColor(col)
        c.setStrokeColor(HexColor("#555555"))
        c.setLineWidth(0.5)
        c.rect(ix, iy, sw_, sw_, fill=1, stroke=1)
        c.setFillColor(black)
        c.setFont("Helvetica", 8)
        c.drawString(ix + sw_ + 3, iy + 1, f"{ans} = {name}")
    c.restoreState()


# ── Problems panel ─────────────────────────────────────────────────────────────

def draw_problems(c, x0, y0, w, h, show_answers):
    bh = 33
    gap = 5
    col_w = w / 2 - 5

    lbl(c, x0 + w/2, y0 + h - 14, "Solve. Find the color. Color the picture!", 9, black, bold=True)

    for i, (a, op, b, ans) in enumerate(PROBLEMS):
        ci = i // 5
        ri = i % 5
        bx = x0 + ci * (col_w + 10)
        by = y0 + h - 30 - ri * (bh + gap)

        # alternating row bg
        c.saveState()
        c.setFillColor(HexColor("#F7F3FF") if ri % 2 == 0 else white)
        c.rect(bx, by - bh, col_w, bh, fill=1, stroke=0)
        c.restoreState()

        # number badge
        c.saveState()
        c.setFillColor(HexColor("#E8771A"))
        c.circle(bx + 10, by - bh/2, 8, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(bx + 10, by - bh/2 - 3, str(i+1))
        c.restoreState()

        # equation
        c.setFillColor(black)
        c.setFont("Helvetica", 13)
        c.drawString(bx + 23, by - bh/2 - 5, f"{a} {op} {b} =")

        # answer box
        bax = bx + col_w - 28
        bay = by - bh + 6
        c.saveState()
        c.setStrokeColor(HexColor("#AAAAAA"))
        c.setLineWidth(0.8)
        c.rect(bax, bay, 22, 20, fill=0, stroke=1)
        if show_answers:
            _, acol = ANS_MAP[ans]
            c.setFillColor(acol)
            c.rect(bax, bay, 22, 20, fill=1, stroke=1)
            c.setFillColor(white if ans == 24 else black)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(bax + 11, bay + 5, str(ans))
        c.restoreState()


# ── Full page ──────────────────────────────────────────────────────────────────

def build_page(path, show_answers):
    c = rl_canvas.Canvas(path, pagesize=letter)

    # Header
    hh = 0.65 * inch
    hy = PAGE_H - M - hh
    c.setFillColor(HexColor("#E8771A"))
    c.roundRect(M, hy, PAGE_W - 2*M, hh, 8, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 19)
    title = "Halloween Multiplication  —  Color by Code"
    if show_answers:
        title += "  (ANSWER KEY)"
    c.drawCentredString(PAGE_W/2, hy + hh/2 - 5, title)
    c.setFont("Helvetica", 10)
    c.drawCentredString(PAGE_W/2, hy + 7, "Grade 3  •  Multiplication  •  Times Tables")

    # Name / Date
    ny = hy - 0.28*inch
    c.setFillColor(black)
    c.setFont("Helvetica", 10)
    c.drawString(M, ny, "Name: ___________________________________")
    c.drawRightString(PAGE_W - M, ny, "Date: _______________")

    # Color key strip
    ky = ny - 0.22*inch - 0.30*inch
    draw_key_strip(c, M, ky, PAGE_W - 2*M, 0.30*inch)

    # Content
    ct_top = ky - 0.12*inch
    ct_bot = 0.50*inch
    ct_h = ct_top - ct_bot

    total_w = PAGE_W - 2*M
    scene_w = total_w * 0.56
    prob_w = total_w - scene_w - 0.12*inch

    draw_scene(c, M, ct_bot, scene_w, ct_h)
    draw_problems(c, M + scene_w + 0.12*inch, ct_bot, prob_w, ct_h, show_answers)

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(HexColor("#999999"))
    c.drawString(M, 0.28*inch, "© 2026 BrightOwl Learning  —  For single classroom use only.")
    c.drawRightString(PAGE_W - M, 0.28*inch, "365days · No Prep · Just Print")

    c.showPage()
    c.save()


def main():
    out_dir = os.environ.get("OUT_DIR", "products/tpt/cbc_halloween")
    os.makedirs(out_dir, exist_ok=True)
    ws = os.path.join(out_dir, "worksheet.pdf")
    ak = os.path.join(out_dir, "answer_key.pdf")
    build_page(ws, show_answers=False)
    build_page(ak, show_answers=True)
    print(f"[OK] worksheet  → {ws}")
    print(f"[OK] answer key → {ak}")


if __name__ == "__main__":
    main()
