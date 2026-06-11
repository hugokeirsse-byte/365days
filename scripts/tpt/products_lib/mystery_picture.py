"""
Mystery Picture — color-by-number math reveal worksheets (FUN format).
Solve each cell's fact -> answer falls in a color band -> color it that color
-> a pixel-art picture emerges.

Product = multi-page book: cover + how-it-works + N mystery pages + answer keys.
"""
from __future__ import annotations
import random, sys
from pathlib import Path

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fun_core import (PAGE_W, PAGE_H, M, AUTHOR, THEMES, F, star, check,
                      fun_header, name_line, fun_footer, page_bg,
                      make_fact, OP_WORD, OUT_ROOT, _col)

# ── Color bands ──────────────────────────────────────────────────────────────
# 6 kid-friendly colors. Each maps to a contiguous answer range.
# Band index 0 is reserved as the "background" / lightest color.
# (label, swatch hex, lo, hi)  — ranges are inclusive and disjoint.
BANDS = [
    ("Blue",   "#5AA9F0",  0, 10),
    ("Green",  "#46C36B", 11, 20),
    ("Yellow", "#FFC93C", 21, 30),
    ("Orange", "#FF8C42", 31, 45),
    ("Red",    "#FF5C6C", 46, 60),
    ("Purple", "#9B6DD6", 61, 99),
]
NBANDS = len(BANDS)

# ── Pixel pictures ───────────────────────────────────────────────────────────
# Each picture is a 15-row x 12-col grid of band indices (0..5).
# Designed so the shape reads clearly with a flat background band.
# 0=Blue(bg-ish), 1=Green, 2=Yellow, 3=Orange, 4=Red, 5=Purple

# Background fill used by most pictures (sky blue band 0).
def _grid(rows):
    g = [list(r) for r in rows]
    assert len(g) == 15 and all(len(r) == 12 for r in g), "picture must be 15x12"
    return g

# Heart (red on blue background)
HEART = _grid([
    "000000000000",
    "000000000000",
    "004400044000",
    "044440444400",
    "044444444440",
    "044444444440",
    "044444444440",
    "044444444440",
    "004444444400",
    "000444444000",
    "000044440000",
    "000004400000",
    "000000000000",
    "000000000000",
    "000000000000",
])

# Star (yellow on blue background)
STAR = _grid([
    "000000000000",
    "000000000000",
    "000002200000",
    "000002200000",
    "000022220000",
    "022222222220",
    "002222222200",
    "000222222000",
    "000222222000",
    "000222222000",
    "002220022200",
    "002200002200",
    "022000000220",
    "000000000000",
    "000000000000",
])

# Apple (red body, green leaf, purple stem)
APPLE = _grid([
    "000000000000",
    "000000050000",
    "000001150000",
    "000000050000",
    "000044044000",
    "000444444400",
    "004444444440",
    "004444444440",
    "004444444440",
    "004444444440",
    "004444444440",
    "000444444400",
    "000044444000",
    "000004400000",
    "000000000000",
])

# Fish (orange body on blue water, yellow tail)
FISH = _grid([
    "000000000000",
    "000000000000",
    "000000000022",
    "000333300202",
    "003333330022",
    "033333333302",
    "333333333322",
    "333303333302",
    "333333333322",
    "033333333302",
    "003333330022",
    "000333300202",
    "000000000022",
    "000000000000",
    "000000000000",
])

# Tree (green foliage, purple/brown trunk)
TREE = _grid([
    "000000000000",
    "000001100000",
    "000011110000",
    "000111111000",
    "001111111100",
    "011111111110",
    "001111111100",
    "011111111110",
    "000111111000",
    "001111111100",
    "000011110000",
    "000005500000",
    "000005500000",
    "000005500000",
    "000000000000",
])

# Flower (red petals, yellow center, green stem/leaf)
FLOWER = _grid([
    "000000000000",
    "000044440000",
    "000444444000",
    "004442244400",
    "004422224400",
    "004442244400",
    "000444444000",
    "000044440000",
    "000001100000",
    "000001100000",
    "000011100000",
    "000001110000",
    "000001100000",
    "000001100000",
    "000000000000",
])

PICTURES = [
    ("Heart",  HEART),
    ("Star",   STAR),
    ("Apple",  APPLE),
    ("Fish",   FISH),
    ("Tree",   TREE),
    ("Flower", FLOWER),
]

# ── Fact generation per band ──────────────────────────────────────────────────
def _facts_for_op(op, grade):
    """Build a pool of (expr, ans) facts for the op, then bucket by band."""
    if op in ("mult", "div"):
        lo, hi = (2, 9) if grade <= 3 else (2, 12)
        pairs = [(a, b) for a in range(lo, hi + 1) for b in range(lo, hi + 1)]
    else:
        lo, hi = (1, 20) if grade <= 2 else (5, 50)
        pairs = [(a, b) for a in range(lo, hi + 1) for b in range(lo, hi + 1)]
    buckets = [[] for _ in BANDS]
    for a, b in pairs:
        expr, ans = make_fact(op, a, b)
        for bi, (_, _, blo, bhi) in enumerate(BANDS):
            if blo <= ans <= bhi:
                buckets[bi].append((expr, ans))
                break
    return buckets


def pick_fact(buckets, band_idx, rng):
    """Pick a fact whose answer lands in the given band. Falls back gracefully."""
    pool = buckets[band_idx]
    if pool:
        return rng.choice(pool)
    # Fallback: synthesize a trivial fact landing mid-band.
    lo, hi = BANDS[band_idx][2], BANDS[band_idx][3]
    target = (lo + hi) // 2
    return (f"{target} + 0", target)


# ── Grid geometry ──────────────────────────────────────────────────────────────
GRID_ROWS, GRID_COLS = 15, 12


def _grid_rect(top_y):
    """Return (gx, gy_bottom, cw, ch) for the grid given a top y."""
    avail_w = PAGE_W - 2 * M
    cw = avail_w / GRID_COLS
    ch = cw  # square cells
    gx = M
    gy_bottom = top_y - GRID_ROWS * ch
    return gx, gy_bottom, cw, ch


# ── Color key box ────────────────────────────────────────────────────────────
def draw_color_key(c, theme, y):
    th = THEMES[theme]
    box_h = 0.62 * inch
    c.setFillColor(white); c.setStrokeColor(HexColor(th["a"])); c.setLineWidth(1.6)
    c.roundRect(M, y - box_h, PAGE_W - 2 * M, box_h, 10, fill=1, stroke=1)
    c.setFillColor(HexColor(th["a"])); c.setFont(F("xb"), 10)
    c.drawString(M + 0.14 * inch, y - 0.2 * inch, "COLOR KEY")
    # swatches in two columns x three rows
    sw = 0.16 * inch
    col_w = (PAGE_W - 2 * M - 0.3 * inch) / 3
    for i, (label, hexc, lo, hi) in enumerate(BANDS):
        col = i % 3
        rowi = i // 3
        x = M + 0.18 * inch + col * col_w
        yy = y - 0.34 * inch - rowi * 0.22 * inch
        c.setFillColor(_col(hexc)); c.setStrokeColor(HexColor("#777777")); c.setLineWidth(0.7)
        c.roundRect(x, yy - sw + 0.02 * inch, sw, sw, 2, fill=1, stroke=1)
        c.setFillColor(black); c.setFont(F("b"), 8.5)
        c.drawString(x + sw + 0.05 * inch, yy - 0.085 * inch, f"{lo}-{hi} = {label}")
    return y - box_h


# ── Mystery page ───────────────────────────────────────────────────────────────
def page_mystery(c, theme, op, pic_no, name, picture, buckets, seed):
    th = THEMES[theme]
    rng = random.Random(seed)
    page_bg(c, theme)
    fun_header(c, theme, "Mystery Picture", f"Solve, then color by the key — a picture appears!")
    y = name_line(c, theme)

    y = draw_color_key(c, theme, y - 0.12 * inch)

    gx, gy_bottom, cw, ch = _grid_rect(y - 0.18 * inch)

    # Generate facts for every cell and remember them for the answer key.
    cell_facts = [[None] * GRID_COLS for _ in range(GRID_ROWS)]
    for r in range(GRID_ROWS):
        for col in range(GRID_COLS):
            band = picture[r][col]
            expr, ans = pick_fact(buckets, band, rng)
            cell_facts[r][col] = (expr, ans, band)

    # Draw grid cells (white, NOT colored).
    c.setLineWidth(0.6)
    for r in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = gx + col * cw
            yy = gy_bottom + (GRID_ROWS - 1 - r) * ch
            c.setFillColor(white); c.setStrokeColor(HexColor("#9AA0B5"))
            c.rect(x, yy, cw, ch, fill=1, stroke=1)
            expr, ans, band = cell_facts[r][col]
            c.setFillColor(black); c.setFont(F("r"), 6.4)
            c.drawCentredString(x + cw / 2, yy + ch / 2 - 2.3, expr)

    fun_footer(c, tag="Mystery Picture")
    c.showPage()
    return (pic_no, name, picture, cell_facts)


def page_mystery_answer(c, theme, pic_no, name, picture, cell_facts):
    th = THEMES[theme]
    page_bg(c, theme)
    fun_header(c, theme, "Answer Key", f"Mystery Picture #{pic_no}: {name}")
    y = PAGE_H - 0.5 * inch - 0.95 * inch - 0.3 * inch

    gx, gy_bottom, cw, ch = _grid_rect(y - 0.1 * inch)

    c.setLineWidth(0.5)
    for r in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = gx + col * cw
            yy = gy_bottom + (GRID_ROWS - 1 - r) * ch
            band = picture[r][col]
            c.setFillColor(_col(BANDS[band][1]))
            c.setStrokeColor(HexColor("#FFFFFF"))
            c.rect(x, yy, cw, ch, fill=1, stroke=1)
            expr, ans, _ = cell_facts[r][col]
            # answer number, dark on light bands / white on dark bands
            light = band in (1, 2, 3)  # green/yellow/orange are lighter
            c.setFillColor(black if light else white)
            c.setFont(F("b"), 6.2)
            c.drawCentredString(x + cw / 2, yy + ch / 2 - 2.2, str(ans))

    # mini legend reminder
    ly = gy_bottom - 0.28 * inch
    c.setFillColor(HexColor(th["a"])); c.setFont(F("b"), 9)
    c.drawCentredString(PAGE_W / 2, ly, f"Finished picture: {name}")
    fun_footer(c, tag="Mystery Picture")
    c.showPage()


# ── How it works ───────────────────────────────────────────────────────────────
def page_how(c, theme, op, grade):
    th = THEMES[theme]
    page_bg(c, theme)
    fun_header(c, theme, "How It Works", "Solve · Match · Color · Reveal!")
    y = PAGE_H - 2.1 * inch

    steps = [
        ("1. Solve", "Work out the math fact inside every square."),
        ("2. Match", "Find which color band the answer falls into using the COLOR KEY."),
        ("3. Color", "Color the square that color. Do every square."),
        ("4. Reveal", "A mystery pixel picture appears — like magic!"),
    ]
    for title, body in steps:
        c.setFillColor(white); c.setStrokeColor(HexColor(th["a"])); c.setLineWidth(1.5)
        c.roundRect(M, y - 0.78 * inch, PAGE_W - 2 * M, 0.78 * inch, 10, fill=1, stroke=1)
        c.setFillColor(HexColor(th["a"])); c.setFont(F("xb"), 14)
        c.drawString(M + 0.25 * inch, y - 0.32 * inch, title)
        c.setFillColor(black); c.setFont(F("r"), 11.5)
        c.drawString(M + 0.25 * inch, y - 0.58 * inch, body)
        y -= 0.95 * inch

    # show the key here too
    c.setFillColor(HexColor(th["a"])); c.setFont(F("xb"), 13)
    c.drawString(M, y - 0.05 * inch, "Example Color Key")
    draw_color_key(c, theme, y - 0.22 * inch)

    fun_footer(c, tag="Mystery Picture")
    c.showPage()


# ── Cover ──────────────────────────────────────────────────────────────────────
def page_cover(c, theme, op, grade, n):
    th = THEMES[theme]
    page_bg(c, theme)
    c.setFillColor(HexColor(th["a"]))
    c.rect(0, PAGE_H - 3.0 * inch, PAGE_W, 3.0 * inch, fill=1, stroke=0)
    for i in range(6):
        star(c, 1.2 * inch + i * 1.2 * inch, PAGE_H - 0.5 * inch, 9, th["b"])
    c.setFillColor(white); c.setFont(F("xb"), 40)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 1.7 * inch, "Mystery Pictures")
    c.setFont(F("xb"), 22)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 2.25 * inch, f"{OP_WORD[op]} Color-by-Number")
    c.setFont(F("b"), 14)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 2.65 * inch, f"Grade {grade}  ·  Solve · Color · Reveal")

    # mini pixel-art preview badge (a small heart)
    badge_cx, badge_cy = PAGE_W / 2, PAGE_H - 4.4 * inch
    preview = [
        "01100",
        "11110",
        "11110",
        "01100",
        "00100",
    ]
    ps = 0.26 * inch
    px0 = badge_cx - len(preview[0]) * ps / 2
    py0 = badge_cy + len(preview) * ps / 2
    for ri, row in enumerate(preview):
        for ci, ch in enumerate(row):
            if ch == "1":
                c.setFillColor(HexColor("#FF5C6C"))
            else:
                c.setFillColor(HexColor("#CFE7FF"))
            c.rect(px0 + ci * ps, py0 - (ri + 1) * ps, ps, ps, fill=1, stroke=0)

    cy = 2.3 * inch; card_h = 2.0 * inch
    c.setFillColor(white); c.setStrokeColor(HexColor(th["a"])); c.setLineWidth(1.5)
    c.roundRect(M + 0.4 * inch, cy, PAGE_W - 2 * M - 0.8 * inch, card_h, 10, fill=1, stroke=1)
    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 14)
    c.drawCentredString(PAGE_W / 2, cy + card_h - 0.35 * inch, "What's Inside")
    for i, b in enumerate([
        f"{n} mystery picture color-by-number pages",
        "Kids solve facts, then color by the key",
        "Hidden pixel pictures reveal as they color",
        "Full colored answer keys for teachers",
        "No prep — just print & reveal",
    ]):
        yb = cy + card_h - 0.75 * inch - i * 0.28 * inch
        check(c, M + 0.85 * inch, yb, th["a"], 10)
        c.setFillColor(black); c.setFont(F("r"), 11.5)
        c.drawString(M + 1.15 * inch, yb, b)
    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 16)
    c.drawCentredString(PAGE_W / 2, 1.5 * inch, AUTHOR)
    fun_footer(c, tag="Mystery Picture")
    c.showPage()


# ── Build ──────────────────────────────────────────────────────────────────────
def build_product(op="mult", grade=3, theme="candy", n_pictures=5, out_dir=None):
    n_pictures = max(4, min(n_pictures, len(PICTURES)))
    buckets = _facts_for_op(op, grade)
    if out_dir is None:
        slug = f"{op}_g{grade}_{theme}"
        out_dir = OUT_ROOT / "mystery_picture" / slug
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "product.pdf"
    c = rl_canvas.Canvas(str(out), pagesize=letter)

    page_cover(c, theme, op, grade, n_pictures)
    page_how(c, theme, op, grade)

    solved = []
    for i in range(n_pictures):
        name, picture = PICTURES[i % len(PICTURES)]
        solved.append(page_mystery(c, theme, op, i + 1, name, picture, buckets,
                                   seed=1000 * (i + 1) + grade))
    for pic_no, name, picture, cell_facts in solved:
        page_mystery_answer(c, theme, pic_no, name, picture, cell_facts)

    c.save()
    print(f"✓ Mystery Picture {OP_WORD[op]} G{grade} [{theme}] → {out} ({out.stat().st_size:,} B)")
    return out


if __name__ == "__main__":
    op = sys.argv[1] if len(sys.argv) > 1 else "mult"
    grade = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    theme = sys.argv[3] if len(sys.argv) > 3 else "candy"
    build_product(op=op, grade=grade, theme=theme)
