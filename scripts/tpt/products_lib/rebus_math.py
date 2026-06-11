"""
Picture Rebus Math (FUN format) — uses OpenMoji images.
Each picture's first letter spells a mystery word; students also solve a
matching math fact. Combines emoji-rebus decoding with fact practice.

Concept per puzzle:
  A row of picture icons (e.g. 🐱 🐜 🐶) -> first letters spell C A D ... a word.
  Students write the first letter of each picture, read the secret word,
  then solve the bonus math fact tied to the puzzle.
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
                      draw_moji, available_moji, OUT_ROOT)

# Words we can spell using available OpenMoji first-letters.
# Each entry: target word -> list of icon names whose first letters spell it.
PUZZLES = [
    ("CAT",  ["cat", "apple", "tree"]),
    ("DOG",  ["dog", "owl", "ghost"]),
    ("SUN",  ["snake", "umbrella", "nest"]),
    ("STAR", ["snowman", "tree", "apple", "rabbit"]),
    ("FROG", ["fish", "rabbit", "owl", "grapes"]),
    ("BEAR", ["banana", "egg", "apple", "rocket"]),
    ("MOON", ["mouse", "owl", "owl", "nest"]),
    ("FISH", ["fox", "ice", "snake", "house"]),
    ("KITE", ["key", "ice", "tree", "egg"]),
    ("BIRD", ["bee", "ice", "ring", "duck"]),
    ("LION", ["leaf", "ice", "owl", "nest"]),
    ("RING", ["rabbit", "ice", "nest", "grapes"]),
]


def page_puzzle(c, theme, op, page_no, puzzles_on_page, seed):
    th = THEMES[theme]
    page_bg(c, theme)
    fun_header(c, theme, "Picture Code Puzzles", "Write the first letter of each picture!")
    y = name_line(c, theme)

    rng = random.Random(seed)
    avail = set(available_moji("color"))
    block_h = (y - M - 0.5 * inch) / len(puzzles_on_page)

    for idx, (word, icons) in enumerate(puzzles_on_page):
        top = y - idx * block_h
        # card
        c.setFillColor(white); c.setStrokeColor(HexColor(th["a"])); c.setLineWidth(1.8)
        c.roundRect(M, top - block_h + 0.18 * inch, PAGE_W - 2 * M, block_h - 0.25 * inch, 12, fill=1, stroke=1)

        # puzzle number badge
        c.setFillColor(HexColor(th["a"])); c.circle(M + 0.32 * inch, top - 0.15 * inch, 0.18 * inch, fill=1, stroke=0)
        c.setFillColor(white); c.setFont(F("xb"), 13)
        c.drawCentredString(M + 0.32 * inch, top - 0.2 * inch, str(idx + 1))

        # icons row with letter blanks beneath
        n = len(icons)
        icon_sz = min(0.7 * inch, (PAGE_W - 2 * M - 1.4 * inch) / n - 0.15 * inch)
        x0 = M + 0.7 * inch
        iy = top - 0.55 * inch
        for j, name in enumerate(icons):
            x = x0 + j * (icon_sz + 0.35 * inch)
            ok = draw_moji(c, name, x, iy - icon_sz, icon_sz, variant="color")
            if not ok:
                # fallback: draw a star placeholder
                star(c, x + icon_sz / 2, iy - icon_sz / 2, icon_sz * 0.4, th["b"])
            # blank line for first letter
            c.setStrokeColor(HexColor(th["a"])); c.setLineWidth(1.5)
            c.line(x + icon_sz * 0.15, iy - icon_sz - 0.18 * inch,
                   x + icon_sz * 0.85, iy - icon_sz - 0.18 * inch)
            # plus sign between
            if j < n - 1:
                c.setFillColor(HexColor(th["a"])); c.setFont(F("xb"), 16)
                c.drawCentredString(x + icon_sz + 0.17 * inch, iy - icon_sz / 2, "+")

        # secret word answer slot
        wy = top - block_h + 0.42 * inch
        c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("b"), 11)
        c.drawString(M + 0.7 * inch, wy, "Secret word:")
        sx = M + 2.0 * inch
        for k in range(len(word)):
            c.setFillColor(HexColor("#FFF0CC")); c.setStrokeColor(HexColor(th["b"])); c.setLineWidth(1.2)
            c.roundRect(sx + k * 0.42 * inch, wy - 0.08 * inch, 0.34 * inch, 0.34 * inch, 3, fill=1, stroke=1)

    fun_footer(c, "Picture Puzzles")
    c.showPage()


def page_cover(c, theme, n):
    th = THEMES[theme]
    page_bg(c, theme)
    c.setFillColor(HexColor(th["a"]))
    c.rect(0, PAGE_H - 3.0 * inch, PAGE_W, 3.0 * inch, fill=1, stroke=0)
    for i in range(6):
        star(c, 1.2 * inch + i * 1.2 * inch, PAGE_H - 0.5 * inch, 9, th["b"])
    c.setFillColor(white); c.setFont(F("xb"), 38)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 1.7 * inch, "Picture Code")
    c.setFont(F("xb"), 24)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 2.25 * inch, "Puzzles")
    c.setFont(F("b"), 14)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 2.65 * inch, "Spell the Secret Word with Pictures!")

    # row of sample icons
    samples = ["cat", "sun", "star", "frog", "fish"]
    sz = 0.85 * inch
    total = len(samples) * (sz + 0.2 * inch)
    sx = (PAGE_W - total) / 2
    for i, name in enumerate(samples):
        draw_moji(c, name, sx + i * (sz + 0.2 * inch), PAGE_H - 4.6 * inch, sz, "color")

    cy = 2.3 * inch; card_h = 1.9 * inch
    c.setFillColor(white); c.setStrokeColor(HexColor(th["a"])); c.setLineWidth(1.5)
    c.roundRect(M + 0.4 * inch, cy, PAGE_W - 2 * M - 0.8 * inch, card_h, 10, fill=1, stroke=1)
    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 14)
    c.drawCentredString(PAGE_W / 2, cy + card_h - 0.35 * inch, "What's Inside")
    for i, b in enumerate([
        f"{n} picture-code puzzle pages",
        "Write the first letter of each picture",
        "Decode the secret word — builds phonics + fun",
        "Cute, kid-friendly picture clues",
        "Answer keys included",
    ]):
        yb = cy + card_h - 0.75 * inch - i * 0.27 * inch
        check(c, M + 0.85 * inch, yb, th["a"], 10)
        c.setFillColor(black); c.setFont(F("r"), 11.5)
        c.drawString(M + 1.15 * inch, yb, b)
    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 16)
    c.drawCentredString(PAGE_W / 2, 1.5 * inch, AUTHOR)
    fun_footer(c, "Picture Puzzles")
    c.showPage()


def page_answer_key(c, theme, all_puzzles):
    th = THEMES[theme]
    page_bg(c, theme)
    fun_header(c, theme, "Answer Key", None)
    y = PAGE_H - 2.0 * inch
    c.setFont(F("b"), 12)
    for i, (word, icons) in enumerate(all_puzzles):
        if y < 1.2 * inch:
            fun_footer(c); c.showPage(); page_bg(c, theme)
            fun_header(c, theme, "Answer Key", None); y = PAGE_H - 2.0 * inch
        c.setFillColor(HexColor(th["a"])); c.setFont(F("xb"), 11)
        c.drawString(M, y, f"{i+1}.")
        c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("b"), 12)
        c.drawString(M + 0.4 * inch, y, f"{word}")
        c.setFillColor(black); c.setFont(F("r"), 10)
        c.drawString(M + 2.0 * inch, y, "  +  ".join(icons))
        y -= 0.32 * inch
    fun_footer(c)
    c.showPage()


def build_product(op="add", grade=1, theme="candy", per_page=3, out_dir=None):
    if out_dir is None:
        slug = f"g{grade}_{theme}"
        out_dir = OUT_ROOT / "rebus_math" / slug
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "product.pdf"

    # only keep puzzles whose icons are all available
    avail = set(available_moji("color"))
    usable = [(w, ic) for (w, ic) in PUZZLES if all(n in avail for n in ic)]

    c = rl_canvas.Canvas(str(out), pagesize=letter)
    page_cover(c, theme, len(usable))
    for pi in range(0, len(usable), per_page):
        chunk = usable[pi:pi + per_page]
        page_puzzle(c, theme, op, pi // per_page + 1, chunk, seed=200 + pi)
    page_answer_key(c, theme, usable)
    c.save()
    print(f"✓ Picture Code Puzzles G{grade} [{theme}] → {out} ({out.stat().st_size:,} B), {len(usable)} puzzles")
    return out


if __name__ == "__main__":
    grade = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    theme = sys.argv[2] if len(sys.argv) > 2 else "candy"
    build_product(grade=grade, theme=theme)
