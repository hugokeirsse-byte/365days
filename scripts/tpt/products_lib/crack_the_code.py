"""
Crack the Code — Math Joke decoding worksheets (FUN format).
Solve facts -> each answer maps to a letter -> decode a kid joke punchline.

Product = multi-page book: cover + N joke pages + answer keys.
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
                      speech_bubble, fun_header, name_line, fun_footer, page_bg,
                      make_fact, OP_WORD, OUT_ROOT)

# Kid-friendly jokes: (setup, punchline). Punchline letters get decoded.
JOKES = [
    ("Why was the math book so sad?", "TOO MANY PROBLEMS"),
    ("What do you call a number that can't sit still?", "A ROAMIN NUMERAL"),
    ("Why did the student eat his homework?", "IT WAS A PIECE OF CAKE"),
    ("What is a butterfly's favorite subject?", "MATHEMATICS"),
    ("Why was six afraid of seven?", "SEVEN ATE NINE"),
    ("What do you call a sleeping dinosaur?", "A DINOSNORE"),
    ("Why did the cookie go to the doctor?", "IT FELT CRUMMY"),
    ("What do you get when you cross a snowman and a dog?", "FROSTBITE"),
    ("Why can't your nose be twelve inches long?", "IT WOULD BE A FOOT"),
    ("What did one wall say to the other wall?", "MEET AT THE CORNER"),
]


def assign_code(letters, op, lo, hi, seed):
    """Map each distinct letter to a fact with a unique product."""
    rng = random.Random(seed)
    facts, used = {}, set()
    pairs = [(a, b) for a in range(lo, hi + 1) for b in range(lo, hi + 1)]
    rng.shuffle(pairs)
    for L in letters:
        for a, b in pairs:
            expr, ans = make_fact(op, a, b)
            if ans not in used and ans > 0:
                used.add(ans); facts[L] = (expr, ans); pairs.remove((a, b)); break
    return facts


def page_joke(c, theme, op, joke_no, setup, punch, lo, hi, seed):
    th = THEMES[theme]
    page_bg(c, theme)
    fun_header(c, theme, "Crack the Code!", "Solve each fact, then decode the joke")
    y = name_line(c, theme)

    letters = sorted(set(punch.replace(" ", "")))
    facts = assign_code(letters, op, lo, hi, seed)

    # Joke setup bubble
    by = y - 0.55 * inch
    speech_bubble(c, M, by, PAGE_W - 2 * M, 0.72 * inch, white, th["b"], tail_x=M + 1.0 * inch)
    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 15)
    c.drawCentredString(PAGE_W / 2, by + 0.42 * inch, setup)
    c.setFillColor(HexColor(th["a"])); c.setFont(F("b"), 10)
    c.drawCentredString(PAGE_W / 2, by + 0.16 * inch, "Solve the problems to find the answer!")

    # Problems card
    py = by - 0.3 * inch
    items = list(facts.items()); random.Random(seed + 1).shuffle(items)
    ncols = 3
    rows = -(-len(items) // ncols)
    card_h = 0.45 * inch + rows * 0.42 * inch
    c.setFillColor(white); c.setStrokeColor(HexColor(th["b"])); c.setLineWidth(2)
    c.roundRect(M, py - card_h, PAGE_W - 2 * M, card_h, 14, fill=1, stroke=1)
    c.setFillColor(HexColor(th["b"]))
    c.roundRect(M, py - 0.36 * inch, PAGE_W - 2 * M, 0.36 * inch, 14, fill=1, stroke=0)
    c.rect(M, py - 0.36 * inch, PAGE_W - 2 * M, 0.18 * inch, fill=1, stroke=0)
    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 12)
    c.drawCentredString(PAGE_W / 2, py - 0.26 * inch, "Solve & Find the Letter")

    cw = (PAGE_W - 2 * M - 0.3 * inch) / ncols
    gy = py - 0.62 * inch
    for i, (L, (expr, ans)) in enumerate(items):
        col = i % ncols; row = i // ncols
        x = M + 0.2 * inch + col * cw; yy = gy - row * 0.42 * inch
        c.setFillColor(HexColor(th["a"])); c.circle(x + 0.13 * inch, yy, 0.14 * inch, fill=1, stroke=0)
        c.setFillColor(white); c.setFont(F("xb"), 12)
        c.drawCentredString(x + 0.13 * inch, yy - 0.05 * inch, L)
        c.setFillColor(black); c.setFont(F("b"), 13)
        c.drawString(x + 0.38 * inch, yy - 0.05 * inch, f"{expr} = ____")

    # Decode strip
    dy = py - card_h - 0.4 * inch
    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 12)
    c.drawString(M, dy, "Write the matching letter under each answer:")
    dy -= 0.5 * inch
    x = M; box = 0.34 * inch; gap = 0.07 * inch
    for ch in punch:
        if ch == " ":
            x += box * 0.55
            if x > PAGE_W - M - box:
                x = M; dy -= 0.85 * inch
            continue
        _, ans = facts[ch]
        c.setFillColor(HexColor("#FFF0CC")); c.setStrokeColor(HexColor(th["b"])); c.setLineWidth(1.2)
        c.roundRect(x, dy, box, box, 4, fill=1, stroke=1)
        c.setFillColor(black); c.setFont(F("b"), 12)
        c.drawCentredString(x + box / 2, dy + box / 2 - 4, str(ans))
        c.setStrokeColor(HexColor("#3D3B6E")); c.setLineWidth(1.2)
        c.line(x, dy - 0.16 * inch, x + box, dy - 0.16 * inch)
        x += box + gap
        if x > PAGE_W - M - box:
            x = M; dy -= 0.85 * inch
    fun_footer(c)
    c.showPage()
    return (joke_no, setup, punch, facts)


def page_cover(c, theme, op, grade, n):
    th = THEMES[theme]
    page_bg(c, theme)
    c.setFillColor(HexColor(th["a"]))
    c.rect(0, PAGE_H - 3.0 * inch, PAGE_W, 3.0 * inch, fill=1, stroke=0)
    for i in range(6):
        star(c, 1.2 * inch + i * 1.2 * inch, PAGE_H - 0.5 * inch, 9, th["b"])
    c.setFillColor(white); c.setFont(F("xb"), 40)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 1.7 * inch, "Crack the Code")
    c.setFont(F("xb"), 22)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 2.25 * inch, f"{OP_WORD[op]} Math Jokes")
    c.setFont(F("b"), 14)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 2.65 * inch, f"Grade {grade}  ·  Self-Checking Fun")

    # giant ? badge
    c.setFillColor(white); c.setStrokeColor(HexColor(th["a"])); c.setLineWidth(3)
    c.circle(PAGE_W / 2, PAGE_H - 4.3 * inch, 0.9 * inch, fill=1, stroke=1)
    c.setFillColor(HexColor(th["a"])); c.setFont(F("xb"), 80)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 4.75 * inch, "?")

    cy = 2.3 * inch; card_h = 2.0 * inch
    c.setFillColor(white); c.setStrokeColor(HexColor(th["a"])); c.setLineWidth(1.5)
    c.roundRect(M + 0.4 * inch, cy, PAGE_W - 2 * M - 0.8 * inch, card_h, 10, fill=1, stroke=1)
    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 14)
    c.drawCentredString(PAGE_W / 2, cy + card_h - 0.35 * inch, "What's Inside")
    for i, b in enumerate([
        f"{n} self-checking math joke pages",
        "Kids solve facts to decode a funny punchline",
        "Built-in error checking (wrong = silly words!)",
        "Complete answer keys included",
        "No prep — just print & laugh",
    ]):
        yb = cy + card_h - 0.75 * inch - i * 0.28 * inch
        check(c, M + 0.85 * inch, yb, th["a"], 10)
        c.setFillColor(black); c.setFont(F("r"), 11.5)
        c.drawString(M + 1.15 * inch, yb, b)
    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 16)
    c.drawCentredString(PAGE_W / 2, 1.5 * inch, AUTHOR)
    fun_footer(c)
    c.showPage()


def page_answer_keys(c, theme, solved):
    th = THEMES[theme]
    page_bg(c, theme)
    fun_header(c, theme, "Answer Key", None)
    y = PAGE_H - 2.0 * inch
    for joke_no, setup, punch, facts in solved:
        if y < 1.5 * inch:
            fun_footer(c); c.showPage(); page_bg(c, theme)
            fun_header(c, theme, "Answer Key", None); y = PAGE_H - 2.0 * inch
        c.setFillColor(HexColor(th["a"])); c.setFont(F("xb"), 11)
        c.drawString(M, y, f"#{joke_no}  {setup}")
        y -= 0.22 * inch
        c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("b"), 12)
        c.drawString(M + 0.2 * inch, y, f"Answer: {punch}")
        y -= 0.2 * inch
        c.setFillColor(black); c.setFont(F("r"), 9)
        code = "   ".join(f"{L}={ans}" for L, (e, ans) in sorted(facts.items()))
        c.drawString(M + 0.2 * inch, y, code[:110])
        y -= 0.4 * inch
    fun_footer(c)
    c.showPage()


def build_product(op="mult", grade=3, theme="candy", n_jokes=8, out_dir=None):
    lo, hi = (2, 9) if op in ("mult", "div") else (1, 12)
    if out_dir is None:
        slug = f"{op}_g{grade}_{theme}"
        out_dir = OUT_ROOT / "crack_the_code" / slug
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "product.pdf"
    c = rl_canvas.Canvas(str(out), pagesize=letter)
    page_cover(c, theme, op, grade, n_jokes)
    solved = []
    for i in range(n_jokes):
        setup, punch = JOKES[i % len(JOKES)]
        solved.append(page_joke(c, theme, op, i + 1, setup, punch, lo, hi, seed=100 * (i + 1)))
    page_answer_keys(c, theme, solved)
    c.save()
    print(f"✓ Crack the Code {OP_WORD[op]} G{grade} [{theme}] → {out} ({out.stat().st_size:,} B)")
    return out


if __name__ == "__main__":
    op = sys.argv[1] if len(sys.argv) > 1 else "mult"
    grade = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    theme = sys.argv[3] if len(sys.argv) > 3 else "candy"
    build_product(op=op, grade=grade, theme=theme)
