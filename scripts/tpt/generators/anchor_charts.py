"""
Halloween Anchor Charts — Multiplication Grade 3
BrightOwl Learning  |  3 poster-style pages
"""
from __future__ import annotations
import sys
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PAGE_W, PAGE_H = letter
M = 0.45 * inch
BRAND = HexColor("#E8771A")
DARK  = HexColor("#2C3E50")
LIGHT = HexColor("#FFF5E6")
AUTHOR = "BrightOwl Learning"
FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"

def register_fonts():
    for name, fname in [("Nunito", "Nunito-Regular.ttf"), ("Nunito-Bold", "Nunito-Bold.ttf")]:
        p = FONT_DIR / fname
        if p.exists() and name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(p)))

register_fonts()

def FB():
    try: pdfmetrics.getFont("Nunito-Bold"); return "Nunito-Bold"
    except: return "Helvetica-Bold"

def FN():
    try: pdfmetrics.getFont("Nunito"); return "Nunito"
    except: return "Helvetica"


# ── decorative primitives ──────────────────────────────────────────────────────

def draw_pumpkin(c, cx, cy, r=18):
    """Draw a cartoon pumpkin at (cx, cy) with radius r."""
    # stem
    c.setFillColor(HexColor("#3A7D44"))
    c.setStrokeColor(HexColor("#3A7D44"))
    c.setLineWidth(2)
    c.line(cx, cy + r, cx + r * 0.4, cy + r * 1.5)
    # body
    c.setFillColor(BRAND)
    c.setStrokeColor(HexColor("#8B4513"))
    c.setLineWidth(1.2)
    c.circle(cx, cy, r, fill=1, stroke=1)
    # lobes
    c.setStrokeColor(HexColor("#8B4513"))
    c.setLineWidth(0.8)
    for ox in (-r * 0.55, r * 0.55):
        c.ellipse(cx + ox - r * 0.3, cy - r * 0.6, cx + ox + r * 0.3, cy + r * 0.6, fill=1, stroke=1)
    # eyes (triangles)
    c.setFillColor(black)
    for ex in (cx - r * 0.28, cx + r * 0.28):
        p = c.beginPath()
        p.moveTo(ex, cy + r * 0.28)
        p.lineTo(ex - r * 0.14, cy + r * 0.0)
        p.lineTo(ex + r * 0.14, cy + r * 0.0)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    # mouth
    c.setStrokeColor(black)
    c.setLineWidth(1.2)
    p = c.beginPath()
    p.moveTo(cx - r * 0.3, cy - r * 0.18)
    p.curveTo(cx - r * 0.15, cy - r * 0.38, cx + r * 0.15, cy - r * 0.38, cx + r * 0.3, cy - r * 0.18)
    c.drawPath(p, fill=0, stroke=1)


def draw_bat(c, cx, cy, r=14):
    """Draw a simple bat using bezier wings."""
    c.setFillColor(HexColor("#1A1A2E"))
    c.setStrokeColor(HexColor("#1A1A2E"))
    c.setLineWidth(0.5)
    # left wing
    p = c.beginPath()
    p.moveTo(cx, cy)
    p.curveTo(cx - r * 0.5, cy + r * 0.8, cx - r * 1.6, cy + r * 0.5, cx - r * 2.0, cy - r * 0.3)
    p.curveTo(cx - r * 1.4, cy - r * 0.1, cx - r * 0.9, cy - r * 0.4, cx, cy)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    # right wing (mirror)
    p = c.beginPath()
    p.moveTo(cx, cy)
    p.curveTo(cx + r * 0.5, cy + r * 0.8, cx + r * 1.6, cy + r * 0.5, cx + r * 2.0, cy - r * 0.3)
    p.curveTo(cx + r * 1.4, cy - r * 0.1, cx + r * 0.9, cy - r * 0.4, cx, cy)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    # body
    c.setFillColor(HexColor("#1A1A2E"))
    c.circle(cx, cy, r * 0.38, fill=1, stroke=0)
    # ears
    for ex in (-r * 0.18, r * 0.18):
        p = c.beginPath()
        p.moveTo(cx + ex - r * 0.12, cy + r * 0.32)
        p.lineTo(cx + ex, cy + r * 0.65)
        p.lineTo(cx + ex + r * 0.12, cy + r * 0.32)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    # eyes
    c.setFillColor(HexColor("#FF6B35"))
    for ex in (-r * 0.12, r * 0.12):
        c.circle(cx + ex, cy + r * 0.05, r * 0.08, fill=1, stroke=0)


def draw_spider_web(c, cx, cy, r=16):
    """Draw a spider web with radial lines and concentric arcs."""
    c.setStrokeColor(HexColor("#9E9E9E"))
    c.setLineWidth(0.7)
    num_spokes = 8
    num_rings = 4
    for i in range(num_spokes):
        angle = math.radians(i * 360 / num_spokes)
        c.line(cx, cy, cx + r * math.cos(angle), cy + r * math.sin(angle))
    for ring in range(1, num_rings + 1):
        rr = r * ring / num_rings
        # draw arc segments between spokes
        for i in range(num_spokes):
            a1 = math.radians(i * 360 / num_spokes)
            a2 = math.radians((i + 1) * 360 / num_spokes)
            p = c.beginPath()
            p.moveTo(cx + rr * math.cos(a1), cy + rr * math.sin(a1))
            p.curveTo(
                cx + rr * math.cos(a1) * 1.05, cy + rr * math.sin(a1) * 1.05,
                cx + rr * math.cos(a2) * 1.05, cy + rr * math.sin(a2) * 1.05,
                cx + rr * math.cos(a2), cy + rr * math.sin(a2)
            )
            c.drawPath(p, fill=0, stroke=1)
    # spider body
    c.setFillColor(black)
    c.circle(cx, cy, r * 0.1, fill=1, stroke=0)


def draw_ghost(c, cx, cy, r=16):
    """Draw a friendly ghost shape."""
    c.setFillColor(white)
    c.setStrokeColor(HexColor("#CCCCCC"))
    c.setLineWidth(0.8)
    # main body – rounded top
    p = c.beginPath()
    p.moveTo(cx - r, cy - r * 0.5)
    # left side up
    p.lineTo(cx - r, cy + r * 0.3)
    # arc over top
    p.curveTo(cx - r, cy + r * 1.0, cx + r, cy + r * 1.0, cx + r, cy + r * 0.3)
    # right side down
    p.lineTo(cx + r, cy - r * 0.5)
    # wavy bottom  (3 bumps)
    p.curveTo(cx + r * 0.67, cy - r * 0.2, cx + r * 0.33, cy - r * 0.9, cx, cy - r * 0.6)
    p.curveTo(cx - r * 0.33, cy - r * 0.9, cx - r * 0.67, cy - r * 0.2, cx - r, cy - r * 0.5)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    # eyes
    c.setFillColor(HexColor("#2C3E50"))
    c.circle(cx - r * 0.3, cy + r * 0.35, r * 0.14, fill=1, stroke=0)
    c.circle(cx + r * 0.3, cy + r * 0.35, r * 0.14, fill=1, stroke=0)
    # smile
    c.setStrokeColor(HexColor("#2C3E50"))
    c.setLineWidth(1)
    p = c.beginPath()
    p.moveTo(cx - r * 0.25, cy + r * 0.08)
    p.curveTo(cx - r * 0.1, cy - r * 0.08, cx + r * 0.1, cy - r * 0.08, cx + r * 0.25, cy + r * 0.08)
    c.drawPath(p, fill=0, stroke=1)


# ── page helpers ───────────────────────────────────────────────────────────────

HEADER_H = 0.65 * inch
FOOTER_H = 0.3 * inch

def draw_header(c, title, subtitle=""):
    c.setFillColor(BRAND)
    c.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FB(), 22)
    c.drawCentredString(PAGE_W / 2, PAGE_H - HEADER_H + 0.22 * inch, title)
    if subtitle:
        c.setFont(FN(), 11)
        c.drawCentredString(PAGE_W / 2, PAGE_H - HEADER_H + 0.05 * inch, subtitle)

def draw_footer(c):
    c.setFillColor(DARK)
    c.rect(0, 0, PAGE_W, FOOTER_H, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FN(), 8)
    c.drawCentredString(PAGE_W / 2, 0.09 * inch, AUTHOR + "  •  BrightOwlLearning.com")

def draw_page_border(c):
    c.setStrokeColor(BRAND)
    c.setLineWidth(2.5)
    c.rect(M * 0.5, M * 0.5, PAGE_W - M, PAGE_H - M, fill=0, stroke=1)


# ── Page 1 — Multiplication Table ─────────────────────────────────────────────

ROW_COLORS = [
    HexColor("#FFE5CC"), HexColor("#FFF0CC"), HexColor("#E5FFE5"),
    HexColor("#CCF0FF"), HexColor("#F0E5FF"), HexColor("#FFE5E5"),
    HexColor("#E5FFEE"), HexColor("#FFEEF0"), HexColor("#E5F5FF"),
    HexColor("#FFFFF0"),
]

def page1_mult_table(c):
    draw_page_border(c)
    draw_header(c, "Multiplication Table 1–10", "Halloween Math Reference")
    draw_footer(c)

    # pumpkin top-right
    draw_pumpkin(c, PAGE_W - M - 0.35 * inch, PAGE_H - HEADER_H - 0.5 * inch, r=20)

    # grid dimensions
    cols = 11  # label col + 10 data cols
    rows = 11
    grid_left  = M
    grid_right = PAGE_W - M
    grid_top   = PAGE_H - HEADER_H - 0.18 * inch
    grid_bot   = FOOTER_H + 0.25 * inch
    cell_w = (grid_right - grid_left) / cols
    cell_h = (grid_top - grid_bot) / rows

    for r in range(rows):
        for col in range(cols):
            cx = grid_left + col * cell_w
            cy = grid_top - (r + 1) * cell_h

            # backgrounds
            if r == 0 and col == 0:
                bg = BRAND
            elif r == 0 or col == 0:
                bg = DARK
            else:
                bg = ROW_COLORS[(r - 1) % len(ROW_COLORS)]

            c.setFillColor(bg)
            c.setStrokeColor(white)
            c.setLineWidth(0.5)
            c.rect(cx, cy, cell_w, cell_h, fill=1, stroke=1)

            # text
            if r == 0 and col == 0:
                label = "×"
                c.setFillColor(white)
                c.setFont(FB(), 11)
            elif r == 0:
                label = str(col)
                c.setFillColor(white)
                c.setFont(FB(), 11)
            elif col == 0:
                label = str(r)
                c.setFillColor(white)
                c.setFont(FB(), 11)
            else:
                label = str(r * col)
                c.setFillColor(DARK)
                c.setFont(FN(), 10)

            c.drawCentredString(cx + cell_w / 2, cy + cell_h * 0.3, label)

    c.showPage()


# ── Page 2 — Vocab Poster ──────────────────────────────────────────────────────

VOCAB = [
    ("Factor",      "A number that is multiplied\nby another number.",    "3 × 4: 3 and 4 are factors"),
    ("Product",     "The answer you get when\nyou multiply two numbers.", "3 × 4 = 12 → 12 is the product"),
    ("Multiply",    "To add equal groups\ntogether quickly.",             "5 × 3 means 5 groups of 3"),
    ("Array",       "Objects arranged in equal\nrows and columns.",        "●●●\n●●●  = 2 rows × 3 cols"),
    ("Equation",    "A math sentence showing\ntwo equal values.",          "4 × 6 = 24"),
    ("Skip Count",  "Counting by equal jumps\non a number line.",         "2, 4, 6, 8, 10…"),
]

CARD_COLORS = [HexColor("#FFE8CC"), HexColor("#FFF5CC")]

def page2_vocab(c):
    draw_page_border(c)
    draw_header(c, "Multiplication Vocabulary", "Key Terms to Know")
    draw_footer(c)

    # bat decoration
    draw_bat(c, PAGE_W - M - 0.45 * inch, PAGE_H - HEADER_H - 0.5 * inch, r=16)

    cols_n = 2
    rows_n = 3
    pad = 0.18 * inch
    card_w = (PAGE_W - 2 * M - pad) / cols_n
    avail_h = PAGE_H - HEADER_H - FOOTER_H - 0.5 * inch
    card_h = (avail_h - pad * (rows_n - 1)) / rows_n

    top_y = PAGE_H - HEADER_H - 0.22 * inch

    for idx, (term, defn, example) in enumerate(VOCAB):
        col = idx % cols_n
        row = idx // cols_n

        cx = M + col * (card_w + pad)
        cy = top_y - (row + 1) * card_h - row * pad * 0.3

        bg = CARD_COLORS[idx % 2]
        c.setFillColor(bg)
        c.setStrokeColor(BRAND)
        c.setLineWidth(1.5)
        c.roundRect(cx, cy, card_w, card_h, 8, fill=1, stroke=1)

        # colored top accent strip
        c.setFillColor(BRAND)
        c.roundRect(cx, cy + card_h - 28, card_w, 28, 8, fill=1, stroke=0)
        # fix bottom of strip
        c.setFillColor(BRAND)
        c.rect(cx, cy + card_h - 28, card_w, 14, fill=1, stroke=0)

        # term
        c.setFillColor(white)
        c.setFont(FB(), 13)
        c.drawCentredString(cx + card_w / 2, cy + card_h - 20, term)

        # definition
        c.setFillColor(DARK)
        c.setFont(FN(), 9.5)
        ty = cy + card_h - 42
        for line in defn.split("\n"):
            c.drawCentredString(cx + card_w / 2, ty, line)
            ty -= 13

        # example box
        c.setFillColor(white)
        c.setStrokeColor(BRAND)
        c.setLineWidth(0.8)
        ex_x = cx + 8
        ex_y = cy + 6
        ex_w = card_w - 16
        ex_h = 32
        c.roundRect(ex_x, ex_y, ex_w, ex_h, 4, fill=1, stroke=1)
        c.setFillColor(BRAND)
        c.setFont(FB(), 7.5)
        c.drawString(ex_x + 4, ex_y + 21, "Example:")
        c.setFillColor(DARK)
        c.setFont(FN(), 8.5)
        for i, line in enumerate(example.split("\n")):
            c.drawCentredString(cx + card_w / 2, ex_y + 10 - i * 11, line)

    c.showPage()


# ── Page 3 — Strategies Poster ─────────────────────────────────────────────────

def page3_strategies(c):
    draw_page_border(c)
    draw_header(c, "Ways to Multiply", "Multiplication Strategies")
    draw_footer(c)

    # ghost decoration
    draw_ghost(c, PAGE_W - M - 0.4 * inch, PAGE_H - HEADER_H - 0.55 * inch, r=18)

    top_y = PAGE_H - HEADER_H - 0.22 * inch
    avail_h = top_y - FOOTER_H - 0.18 * inch
    n = 5
    section_h = avail_h / n

    strategies = [
        "Skip Counting",
        "Equal Groups",
        "Array",
        "Repeated Addition",
        "Number Line",
    ]

    for i, strat in enumerate(strategies):
        sy = top_y - (i + 1) * section_h
        sx = M

        # row bg alternating
        bg = HexColor("#FFF5E6") if i % 2 == 0 else HexColor("#FFF0FF")
        c.setFillColor(bg)
        c.setStrokeColor(BRAND)
        c.setLineWidth(0.8)
        c.roundRect(sx, sy + 4, PAGE_W - 2 * M, section_h - 8, 6, fill=1, stroke=1)

        # strategy label badge
        badge_w = 1.65 * inch
        badge_h = section_h - 18
        c.setFillColor(BRAND)
        c.roundRect(sx + 6, sy + 10, badge_w, badge_h, 5, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(FB(), 10)
        c.drawCentredString(sx + 6 + badge_w / 2, sy + 10 + badge_h * 0.3, strat)

        # visual area
        vx = sx + badge_w + 20
        vy = sy + 8
        vw = PAGE_W - 2 * M - badge_w - 28
        vh = section_h - 16

        _draw_strategy_visual(c, i, vx, vy, vw, vh)

    c.showPage()


def _draw_strategy_visual(c, idx, vx, vy, vw, vh):
    """Draw the visual for each strategy inside the bounding box."""
    cx = vx + vw / 2
    cy = vy + vh / 2

    if idx == 0:  # Skip Counting: number line with jumps
        _draw_skip_counting(c, vx, cy, vw, vh)

    elif idx == 1:  # Equal Groups: 3 circles with 4 dots
        _draw_equal_groups(c, vx, cy, vw, vh)

    elif idx == 2:  # Array: 3×4 dot grid
        _draw_array(c, vx, cy, vw, vh)

    elif idx == 3:  # Repeated Addition
        _draw_repeated_addition(c, vx, cy, vw, vh)

    elif idx == 4:  # Number Line arcs
        _draw_number_line_arcs(c, vx, cy, vw, vh)


def _draw_skip_counting(c, vx, cy, vw, vh):
    # number line
    lx1 = vx + 5
    lx2 = vx + vw - 5
    c.setStrokeColor(DARK)
    c.setLineWidth(1.5)
    c.line(lx1, cy, lx2, cy)
    # tick marks + labels
    nums = [0, 3, 6, 9, 12]
    step_px = (lx2 - lx1) / (len(nums) - 1 + 0.5)
    for j, val in enumerate(nums):
        tx = lx1 + j * step_px + step_px * 0.25
        c.setStrokeColor(DARK)
        c.setLineWidth(1)
        c.line(tx, cy - 4, tx, cy + 4)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(tx, cy - 14, str(val))
        # jump arc between consecutive numbers
        if j < len(nums) - 1:
            nx = lx1 + (j + 1) * step_px + step_px * 0.25
            arc_h = 10
            p = c.beginPath()
            p.moveTo(tx, cy)
            p.curveTo(tx + (nx - tx) * 0.25, cy + arc_h,
                      tx + (nx - tx) * 0.75, cy + arc_h, nx, cy)
            c.setStrokeColor(BRAND)
            c.setLineWidth(1.5)
            c.drawPath(p, fill=0, stroke=1)
    # label
    c.setFillColor(DARK)
    c.setFont("Helvetica", 8)
    c.drawString(vx + 5, cy + 16, "Count by 3s: 0, 3, 6, 9, 12")


def _draw_equal_groups(c, vx, cy, vw, vh):
    group_r = min(vw / 10, vh / 3)
    dot_r = group_r * 0.18
    n_groups = 3
    n_dots = 4
    spacing = vw / (n_groups + 0.5)
    for g in range(n_groups):
        gcx = vx + spacing * (g + 0.75)
        # group circle
        c.setFillColor(HexColor("#FFF0CC"))
        c.setStrokeColor(BRAND)
        c.setLineWidth(1.2)
        c.circle(gcx, cy, group_r, fill=1, stroke=1)
        # 4 dots in 2x2 inside
        dot_positions = [
            (-dot_r * 1.8, dot_r * 1.4), (dot_r * 1.8, dot_r * 1.4),
            (-dot_r * 1.8, -dot_r * 1.4), (dot_r * 1.8, -dot_r * 1.4),
        ]
        c.setFillColor(BRAND)
        for dx, dy in dot_positions:
            c.circle(gcx + dx, cy + dy, dot_r, fill=1, stroke=0)
    # equation label
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(vx + vw / 2, cy - group_r - 10, "3 groups of 4 = 12")


def _draw_array(c, vx, cy, vw, vh):
    rows_a, cols_a = 3, 4
    dot_r = min(vw / (cols_a * 3.5), vh / (rows_a * 3.5))
    grid_w = cols_a * dot_r * 3
    grid_h = rows_a * dot_r * 3
    ox = vx + (vw - grid_w) / 2
    oy = cy - grid_h / 2
    for r in range(rows_a):
        for col in range(cols_a):
            dx = ox + col * dot_r * 3 + dot_r * 1.5
            dy = oy + r * dot_r * 3 + dot_r * 1.5
            c.setFillColor(BRAND)
            c.circle(dx, dy, dot_r, fill=1, stroke=0)
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(vx + vw / 2, oy - 10, "3 rows × 4 cols = 12")


def _draw_repeated_addition(c, vx, cy, vw, vh):
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 13)
    eq = "3 + 3 + 3 + 3 = 12"
    c.drawCentredString(vx + vw / 2, cy - 5, eq)
    c.setFont("Helvetica", 8.5)
    c.setFillColor(BRAND)
    c.drawCentredString(vx + vw / 2, cy - 18, "Four groups of 3  →  4 × 3 = 12")


def _draw_number_line_arcs(c, vx, cy, vw, vh):
    lx1 = vx + 5
    lx2 = vx + vw - 5
    c.setStrokeColor(DARK)
    c.setLineWidth(1.5)
    c.line(lx1, cy, lx2, cy)
    # 5 tick marks: 0, 3, 6, 9, 12
    n_ticks = 5
    step = (lx2 - lx1) / (n_ticks - 1)
    labels = [0, 3, 6, 9, 12]
    for j in range(n_ticks):
        tx = lx1 + j * step
        c.setStrokeColor(DARK)
        c.setLineWidth(1)
        c.line(tx, cy - 4, tx, cy + 4)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(tx, cy - 14, str(labels[j]))
    # 4 arcs
    arc_h = 14
    for j in range(n_ticks - 1):
        x1 = lx1 + j * step
        x2 = lx1 + (j + 1) * step
        p = c.beginPath()
        p.moveTo(x1, cy)
        p.curveTo(x1 + step * 0.25, cy + arc_h, x2 - step * 0.25, cy + arc_h, x2, cy)
        c.setStrokeColor(BRAND)
        c.setLineWidth(1.8)
        c.drawPath(p, fill=0, stroke=1)
        mid = (x1 + x2) / 2
        c.setFillColor(BRAND)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(mid, cy + arc_h + 2, "+3")
    c.setFillColor(DARK)
    c.setFont("Helvetica", 8)
    c.drawString(vx + 5, cy + arc_h + 14, "4 jumps of 3 = 12")


# ── main ───────────────────────────────────────────────────────────────────────

def generate(out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out_path), pagesize=letter)
    page1_mult_table(c)
    page2_vocab(c)
    page3_strategies(c)
    c.save()
    size = out_path.stat().st_size
    print(f"✓ anchor_charts → {out_path}  ({size:,} bytes)")


if __name__ == "__main__":
    OUT = Path(__file__).resolve().parent.parent.parent.parent / \
          "products" / "tpt" / "samples" / "anchor_charts" / "sample.pdf"
    generate(OUT)


def build_all(out_dir=None, themes=None, gemini_key=None):
    from pathlib import Path as _P
    base = _P(out_dir) if out_dir else _P(__file__).resolve().parents[3] / "products" / "tpt"
    name = _P(__file__).stem
    out = base / "samples" / name / "sample.pdf"
    generate(out)
