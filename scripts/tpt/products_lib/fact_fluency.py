"""
BrightOwl Learning — Math Fact Fluency Product Generator
Follows CDC 3. Produces a complete multi-page PDF "book" product:

  Page 1        : Cover
  Page 2        : How to Use / Teacher note
  Pages 3..N    : Progressive timed drill sheets (×0..×12, then mixed, then challenge)
  Page N+1      : Progress Tracker
  Pages ...     : Answer Keys (compact grids)

Key best-seller rules baked in:
  - RANDOM order of facts on every sheet (never sequential)
  - Multiple versions can be generated via different seeds
  - Score box + timer + "Beat my record" on every drill
  - Progress tracker included
  - Answer key for every sheet

Usage:
  python scripts/tpt/products_lib/fact_fluency.py            # default: multiplication G3
  python scripts/tpt/products_lib/fact_fluency.py add 2      # addition grade 2
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

ROOT     = Path(__file__).resolve().parent.parent          # scripts/tpt
FONT_DIR = ROOT / "fonts"
OUT_ROOT = ROOT.parent.parent / "products" / "tpt"          # products/tpt

PAGE_W, PAGE_H = letter
M = 0.5 * inch

AUTHOR = "BrightOwl Learning"
YEAR   = 2026

# ── Theme palettes ───────────────────────────────────────────────────────────
THEMES = {
    "plain":     {"accent": "#5B4FCF", "dark": "#37308C", "tint": "#F3F1FF", "name": ""},
    "halloween": {"accent": "#E8771A", "dark": "#B85A0E", "tint": "#FFF3E6", "name": "Halloween"},
    "christmas": {"accent": "#C0392B", "dark": "#922A1F", "tint": "#FBEBE9", "name": "Christmas"},
    "spring":    {"accent": "#27AE60", "dark": "#1B8049", "tint": "#E9F8EF", "name": "Spring"},
}

# ── Fonts ─────────────────────────────────────────────────────────────────────
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

def F(weight="r"):
    _reg()
    if not _REG:
        return {"r": "Helvetica", "b": "Helvetica-Bold", "xb": "Helvetica-Bold"}[weight]
    return {"r": "Nunito", "b": "Nunito-B", "xb": "Nunito-XB"}[weight]

# ── Operation config ────────────────────────────────────────────────────────
OPS = {
    "mult": {"sym": "×", "word": "Multiplication", "verb": "multiply"},
    "add":  {"sym": "+", "word": "Addition",       "verb": "add"},
    "sub":  {"sym": "−", "word": "Subtraction",    "verb": "subtract"},
    "div":  {"sym": "÷", "word": "Division",        "verb": "divide"},
}


def make_fact(op, a, b):
    """Return (problem_string, answer_int) for one fact."""
    if op == "mult":
        return f"{a} × {b} =", a * b
    if op == "add":
        return f"{a} + {b} =", a + b
    if op == "sub":
        hi, lo = max(a, b), min(a, b)
        return f"{hi} − {lo} =", hi - lo
    if op == "div":
        # a is the quotient seed, b is divisor -> dividend = a*b
        dividend = a * b
        return f"{dividend} ÷ {b} =", a
    raise ValueError(op)


def facts_for_table(op, table, count, seed):
    """Generate `count` facts focused on a single table (0..12 partner), random order."""
    rng = random.Random(seed)
    partners = list(range(0, 13))
    pool = []
    while len(pool) < count:
        rng.shuffle(partners)
        pool.extend(partners)
    pool = pool[:count]
    return [make_fact(op, table, p) for p in pool]


def facts_mixed(op, lo, hi, count, seed):
    """Mixed facts with both operands in [lo, hi]."""
    rng = random.Random(seed)
    out = []
    for _ in range(count):
        a = rng.randint(lo, hi)
        b = rng.randint(lo, hi)
        out.append(make_fact(op, a, b))
    return out


# ── Drawing helpers ───────────────────────────────────────────────────────────
def header_band(c, theme, title, subtitle=None, height=0.5):
    hh = height * inch
    hy = PAGE_H - M - hh
    c.setFillColor(HexColor(theme["accent"]))
    c.roundRect(M, hy, PAGE_W - 2 * M, hh, 8, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(F("xb"), 16)
    c.drawCentredString(PAGE_W / 2, hy + hh / 2 + (4 if subtitle else -2), title)
    if subtitle:
        c.setFont(F("r"), 9)
        c.drawCentredString(PAGE_W / 2, hy + 7, subtitle)
    return hy


def footer(c):
    c.setFont(F("r"), 7.5)
    c.setFillColor(HexColor("#AAAAAA"))
    c.drawString(M, 0.28 * inch, f"© {YEAR} {AUTHOR} — For single classroom use only.")
    c.drawRightString(PAGE_W - M, 0.28 * inch, f"{AUTHOR} · No Prep · Just Print")


def name_date_score(c, y, score_total):
    c.setFillColor(black)
    c.setFont(F("b"), 10)
    c.drawString(M, y, "Name: ______________________________")
    c.drawString(PAGE_W / 2 + 0.2 * inch, y, "Date: ________________")
    # Score + timer row
    y2 = y - 0.32 * inch
    box_w = 1.7 * inch
    c.setFont(F("b"), 10)
    c.drawString(M, y2 + 2, "Time:  ______ min  ______ sec")
    # score box
    bx = PAGE_W - M - box_w
    c.setFillColor(HexColor("#FFF9E6"))
    c.setStrokeColor(HexColor("#E8B600"))
    c.setLineWidth(1.2)
    c.roundRect(bx, y2 - 0.05 * inch, box_w, 0.34 * inch, 4, fill=1, stroke=1)
    c.setFillColor(black)
    c.setFont(F("xb"), 13)
    c.drawCentredString(bx + box_w / 2, y2 + 0.07 * inch, f"Score: ____ / {score_total}")
    return y2 - 0.3 * inch


# ── Page builders ─────────────────────────────────────────────────────────────
def _check(c, x, y, color, size=9):
    """Draw a checkmark with vector lines (font-independent)."""
    c.saveState()
    c.setStrokeColor(HexColor(color))
    c.setLineWidth(2)
    c.setLineCap(1)
    c.line(x, y + size * 0.35, x + size * 0.35, y)
    c.line(x + size * 0.35, y, x + size, y + size)
    c.restoreState()


def _star(c, cx, cy, r, fill_color, stroke_color):
    """Draw a 5-point star (font-independent)."""
    import math
    pts = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    p.close()
    c.saveState()
    if fill_color:
        c.setFillColor(HexColor(fill_color))
    c.setStrokeColor(HexColor(stroke_color))
    c.setLineWidth(0.8)
    c.drawPath(p, fill=1 if fill_color else 0, stroke=1)
    c.restoreState()


def page_cover(c, theme, op, grade, n_sheets):
    info = OPS[op]
    # full color background panel
    c.setFillColor(HexColor(theme["tint"]))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # top band
    c.setFillColor(HexColor(theme["accent"]))
    c.rect(0, PAGE_H - 2.6 * inch, PAGE_W, 2.6 * inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(F("xb"), 34)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 1.4 * inch, f"{info['word']}")
    c.setFont(F("xb"), 26)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 2.0 * inch, "Fact Fluency")
    theme_label = f"  {theme['name']}" if theme["name"] else ""
    c.setFont(F("b"), 14)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 2.35 * inch, f"Timed Tests  ·  Grade {grade}{theme_label}")

    # central symbol in a circle badge
    badge_cy = PAGE_H - 4.0 * inch
    c.setFillColor(white)
    c.setStrokeColor(HexColor(theme["accent"]))
    c.setLineWidth(3)
    c.circle(PAGE_W / 2, badge_cy, 0.95 * inch, fill=1, stroke=1)
    c.setFillColor(HexColor(theme["accent"]))
    c.setFont(F("xb"), 70)
    c.drawCentredString(PAGE_W / 2, badge_cy - 0.5 * inch, info["sym"])

    # feature bullets card
    cy = 2.5 * inch
    card_h = 2.1 * inch
    c.setFillColor(white)
    c.setStrokeColor(HexColor(theme["accent"]))
    c.setLineWidth(1.5)
    c.roundRect(M + 0.4 * inch, cy, PAGE_W - 2 * M - 0.8 * inch, card_h, 10, fill=1, stroke=1)
    c.setFillColor(HexColor(theme["dark"]))
    c.setFont(F("xb"), 14)
    c.drawCentredString(PAGE_W / 2, cy + card_h - 0.35 * inch, "What's Inside")
    bullets = [
        f"{n_sheets} no-prep timed practice sheets",
        "Facts in random order on every page",
        "Score box & timer to track speed",
        "Student progress tracker included",
        "Complete answer keys",
    ]
    by = cy + card_h - 0.75 * inch
    for b in bullets:
        _check(c, M + 0.85 * inch, by, theme["accent"], size=10)
        c.setFillColor(black)
        c.setFont(F("r"), 11.5)
        c.drawString(M + 1.15 * inch, by, b)
        by -= 0.28 * inch

    c.setFillColor(HexColor(theme["dark"]))
    c.setFont(F("xb"), 16)
    c.drawCentredString(PAGE_W / 2, 1.55 * inch, AUTHOR)
    footer(c)
    c.showPage()


def page_how_to_use(c, theme, op):
    info = OPS[op]
    header_band(c, theme, "How to Use These Pages", AUTHOR, height=0.5)
    y = PAGE_H - M - 0.9 * inch
    c.setFillColor(black)
    blocks = [
        ("For the teacher",
         [
            "Each sheet focuses on one set of facts and arranges them in random order, so",
            "students practice recall — not the order of the page.",
            "Use as a daily warm-up, Friday timed test, homework, or center activity.",
            "Set a timer (1–5 minutes). Students write the time and their score at the top.",
         ]),
        ("Building fluency",
         [
            "Start with the single-table sheets, then move to the mixed-fact sheets.",
            "Encourage students to beat their previous score using the progress tracker.",
            "Re-print any sheet — facts can be regenerated in a fresh order for retesting.",
         ]),
        ("What's included",
         [
            "Single-table drills, mixed-fact drills, and challenge sheets.",
            "A progress tracker for the whole set, plus complete answer keys at the back.",
         ]),
    ]
    for title, lines in blocks:
        c.setFillColor(HexColor(theme["dark"]))
        c.setFont(F("xb"), 13)
        c.drawString(M, y, title)
        y -= 0.05 * inch
        c.setStrokeColor(HexColor(theme["accent"]))
        c.setLineWidth(1)
        c.line(M, y, PAGE_W - M, y)
        y -= 0.26 * inch
        c.setFillColor(black)
        c.setFont(F("r"), 11)
        for ln in lines:
            c.drawString(M + 0.1 * inch, y, ln)
            y -= 0.24 * inch
        y -= 0.2 * inch
    footer(c)
    c.showPage()


def page_drill(c, theme, op, sheet_label, sheet_no, facts, n_cols=5):
    """Render one drill sheet. facts = list of (problem, answer)."""
    total = len(facts)
    header_band(c, theme, f"{OPS[op]['word']} Facts", sheet_label, height=0.5)
    y = name_date_score(c, PAGE_H - M - 0.85 * inch, total)

    # "beat my record" tickbox line
    c.setFont(F("r"), 9)
    c.setFillColor(HexColor("#666666"))
    c.drawString(M, y + 0.04 * inch, "☐  I beat my record!")
    c.drawRightString(PAGE_W - M, y + 0.04 * inch, f"Sheet {sheet_no}")

    grid_top = y - 0.18 * inch
    grid_bottom = M + 0.45 * inch
    grid_h = grid_top - grid_bottom
    n_rows = -(-total // n_cols)  # ceil
    col_w = (PAGE_W - 2 * M) / n_cols
    row_h = grid_h / n_rows

    fs = 15 if total <= 50 else 11
    pad = 8 if total <= 50 else 5
    for i, (problem, _ans) in enumerate(facts):
        col = i % n_cols
        row = i // n_cols
        x = M + col * col_w
        yy = grid_top - (row + 1) * row_h
        if row % 2 == 0:
            c.setFillColor(HexColor(theme["tint"]))
            c.rect(x, yy, col_w, row_h, fill=1, stroke=0)
        c.setFillColor(black)
        c.setFont(F("b"), fs)
        c.drawString(x + pad, yy + row_h * 0.32, problem)

    # vertical separators
    c.setStrokeColor(HexColor("#E0E0E0"))
    c.setLineWidth(0.5)
    for col in range(1, n_cols):
        x = M + col * col_w
        c.line(x, grid_top, x, grid_top - n_rows * row_h)

    footer(c)
    c.showPage()


def page_progress_tracker(c, theme, sheet_titles):
    header_band(c, theme, "My Progress Tracker", "Color a star each time you beat your score!", height=0.5)
    y = PAGE_H - M - 1.0 * inch

    col_sheet = M + 0.1 * inch
    col_date  = PAGE_W - M - 3.6 * inch
    col_score = PAGE_W - M - 2.2 * inch
    col_stars = PAGE_W - M - 1.25 * inch
    c.setFillColor(HexColor(theme["dark"]))
    c.setFont(F("xb"), 11)
    c.drawString(col_sheet, y, "Practice Sheet")
    c.drawString(col_date,  y, "Date")
    c.drawString(col_score, y, "Score")
    c.drawString(col_stars, y, "I beat it!")
    y -= 0.12 * inch
    c.setStrokeColor(HexColor(theme["accent"]))
    c.setLineWidth(1.2)
    c.line(M, y, PAGE_W - M, y)
    y -= 0.1 * inch

    # Use generous fixed rows so the table fills the page nicely
    row_h = 0.46 * inch
    for i, title in enumerate(sheet_titles):
        ry = y - (i + 1) * row_h
        if i % 2 == 0:
            c.setFillColor(HexColor(theme["tint"]))
            c.rect(M, ry, PAGE_W - 2 * M, row_h, fill=1, stroke=0)
        tcy = ry + row_h / 2 - 4
        c.setFillColor(black)
        c.setFont(F("b"), 11)
        c.drawString(col_sheet, tcy, title)
        c.setStrokeColor(HexColor("#BBBBBB"))
        c.setLineWidth(0.7)
        c.line(col_date, ry + 0.12 * inch, col_date + 1.2 * inch, ry + 0.12 * inch)
        c.line(col_score, ry + 0.12 * inch, col_score + 0.85 * inch, ry + 0.12 * inch)
        # three empty stars to color
        for s in range(3):
            _star(c, col_stars + 0.12 * inch + s * 0.3 * inch, tcy + 4, 8, None, "#C9A100")
    footer(c)
    c.showPage()


def page_answer_keys(c, theme, key_blocks):
    """key_blocks: list of (sheet_label, facts). Pack several per page."""
    per_page = 2
    idx = 0
    while idx < len(key_blocks):
        header_band(c, theme, "Answer Key", None, height=0.45)
        block_top = PAGE_H - M - 0.7 * inch
        block_h = (block_top - M - 0.4 * inch) / per_page
        for slot in range(per_page):
            if idx >= len(key_blocks):
                break
            label, facts = key_blocks[idx]
            idx += 1
            by = block_top - slot * block_h
            c.setFillColor(HexColor(theme["dark"]))
            c.setFont(F("xb"), 11)
            c.drawString(M, by, label)
            # grid of answers
            n_cols = 10
            total = len(facts)
            n_rows = -(-total // n_cols)
            cw = (PAGE_W - 2 * M) / n_cols
            rh = min(0.26 * inch, (block_h - 0.4 * inch) / max(n_rows, 1))
            gy = by - 0.28 * inch
            c.setFont(F("r"), 8)
            for i, (problem, ans) in enumerate(facts):
                col = i % n_cols
                row = i // n_cols
                x = M + col * cw
                yy = gy - row * rh
                c.setFillColor(black)
                # show "n) ans"
                c.drawString(x, yy, f"{i+1}.{ans}")
        footer(c)
        c.showPage()


# ── Product assembly ────────────────────────────────────────────────────────
def build_product(op="mult", grade=3, theme="plain", seed_base=1000, out_dir=None):
    info = OPS[op]
    th = THEMES[theme]
    _reg()

    # Decide sheet plan based on operation
    sheets = []        # (label, sheet_no, facts, n_cols)
    key_blocks = []
    tracker_titles = []

    sheet_no = 0

    if op in ("mult", "div"):
        tables = list(range(2, 13))   # ×2..×12
        per_sheet = 50
        for t in tables:
            sheet_no += 1
            label = f"{info['word']} by {t}   ({info['sym']}{t})"
            facts = facts_for_table(op, t, per_sheet, seed=seed_base + sheet_no)
            sheets.append((label, sheet_no, facts, 5))
            key_blocks.append((label, facts))
            tracker_titles.append(f"{info['sym']}{t} facts")
        # mixed sheets
        for lo, hi, tag in [(0, 5, "0–5"), (6, 9, "6–9"), (2, 12, "2–12")]:
            sheet_no += 1
            label = f"Mixed {info['word']} Facts {tag}"
            facts = facts_mixed(op, lo, hi, 100, seed=seed_base + sheet_no)
            sheets.append((label, sheet_no, facts, 10))
            key_blocks.append((label, facts))
            tracker_titles.append(f"Mixed {tag}")
    else:  # add / sub
        # by single addend/minuend buckets
        buckets = [(0, 5, "Sums to 5" if op == "add" else "Within 5"),
                   (0, 10, "Sums to 10" if op == "add" else "Within 10"),
                   (0, 18, "Sums to 18" if op == "add" else "Within 18"),
                   (0, 20, "Sums to 20" if op == "add" else "Within 20")]
        for lo, hi, tag in buckets:
            for v in range(3):
                sheet_no += 1
                label = f"{tag}  (Set {v+1})"
                facts = facts_mixed(op, lo, hi, 50, seed=seed_base + sheet_no)
                sheets.append((label, sheet_no, facts, 5))
                key_blocks.append((label, facts))
                tracker_titles.append(f"{tag} #{v+1}")

    n_sheets = len(sheets)

    # output path
    if out_dir is None:
        slug = f"{op}_g{grade}" + (f"_{theme}" if theme != "plain" else "")
        out_dir = OUT_ROOT / "fact_fluency" / slug
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "product.pdf"

    c = rl_canvas.Canvas(str(out_path), pagesize=letter)
    page_cover(c, th, op, grade, n_sheets)
    page_how_to_use(c, th, op)
    for label, sno, facts, ncols in sheets:
        page_drill(c, th, op, label, sno, facts, n_cols=ncols)
    page_progress_tracker(c, th, tracker_titles)
    page_answer_keys(c, th, key_blocks)
    c.save()

    total_pages = 2 + n_sheets + 1 + (-(-len(key_blocks) // 2))
    print(f"✓ {info['word']} G{grade} [{theme}] → {out_path}")
    print(f"  {n_sheets} drill sheets · ~{total_pages} pages · {out_path.stat().st_size:,} bytes")
    return out_path


if __name__ == "__main__":
    op    = sys.argv[1] if len(sys.argv) > 1 else "mult"
    grade = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    theme = sys.argv[3] if len(sys.argv) > 3 else "plain"
    build_product(op=op, grade=grade, theme=theme)
