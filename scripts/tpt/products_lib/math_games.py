"""
Math Games — printable math centers / partner games (FUN format).
A multi-page book of low-prep games: BUMP, Math Maze, and Spin & Solve.

Product = cover + how-to-play + 2 BUMP boards + 2 Mazes + 2 Spin & Solve
          + maze answer key / teacher notes.
"""
from __future__ import annotations
import math, random, sys
from pathlib import Path

from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fun_core import (PAGE_W, PAGE_H, M, AUTHOR, THEMES, F, star, check, dice,
                      fun_header, name_line, fun_footer, page_bg,
                      make_fact, OP_WORD, OUT_ROOT, _col)


# ── BUMP ─────────────────────────────────────────────────────────────────────
def _bump_numbers(op, variant):
    """Return a list of 24 numbers reachable with 2 dice for the given op."""
    if op == "mult":
        # products of two dice (1..6): range 1..36
        if variant == 0:
            nums = sorted({a * b for a in range(1, 7) for b in range(1, 7)})
        else:
            # higher products only
            nums = sorted({a * b for a in range(1, 7) for b in range(1, 7)})[-24:]
    else:  # add: sums of two dice 2..12
        if variant == 0:
            nums = list(range(2, 13))
        else:
            nums = list(range(2, 13))
    # pad / trim to 24 by repeating common values (sums repeat naturally)
    base = list(nums)
    while len(base) < 24:
        base += list(nums)
    return base[:24]


def page_bump(c, theme, op, variant, board_no):
    th = THEMES[theme]
    page_bg(c, theme)
    op_word = "multiply" if op == "mult" else "add"
    fun_header(c, theme, f"BUMP!  Board {board_no}",
               f"A 2-player dice game — roll, {op_word}, and cover!")

    # ── Rules card with two dice drawn ──
    ry = PAGE_H - 1.45 * inch
    rh = 1.65 * inch
    c.setFillColor(white); c.setStrokeColor(HexColor(th["b"])); c.setLineWidth(2)
    c.roundRect(M, ry - rh, PAGE_W - 2 * M, rh, 12, fill=1, stroke=1)
    c.setFillColor(HexColor(th["a"]))
    c.roundRect(M, ry - 0.34 * inch, PAGE_W - 2 * M, 0.34 * inch, 12, fill=1, stroke=0)
    c.rect(M, ry - 0.34 * inch, PAGE_W - 2 * M, 0.17 * inch, fill=1, stroke=0)
    c.setFillColor(white); c.setFont(F("xb"), 13)
    c.drawString(M + 0.18 * inch, ry - 0.25 * inch, "How to Play")

    sym = "×" if op == "mult" else "+"
    rules = [
        "1. Players take turns. On your turn, roll the two dice.",
        f"2. {('Multiply' if op=='mult' else 'Add')} the two numbers ({sym}) and find the answer on the board.",
        "3. Cover that number with one of YOUR colored chips.",
        "4. If your opponent has a single chip there, BUMP it off!",
        "5. Two of your own chips on a number = locked (it's safe).",
        "6. First player to place all their chips wins!",
    ]
    ty = ry - 0.55 * inch
    c.setFillColor(black); c.setFont(F("r"), 9.6)
    for r in rules:
        c.drawString(M + 0.2 * inch, ty, r)
        ty -= 0.18 * inch

    # two dice in the corner of the rules card
    dsz = 0.42 * inch
    dx = PAGE_W - M - 0.2 * inch - 2 * dsz - 0.14 * inch
    dy = ry - rh + 0.22 * inch
    dice(c, dx, dy, dsz, 3, HexColor(th["a"]))
    dice(c, dx + dsz + 0.14 * inch, dy, dsz, 5, HexColor(th["b"]))
    c.setFillColor(HexColor(th["a"])); c.setFont(F("xb"), 16)
    c.drawCentredString(dx + dsz + 0.07 * inch, dy + dsz + 0.06 * inch, sym)

    # ── Board grid of numbered circles ──
    nums = _bump_numbers(op, variant)
    cols, rows = 6, 4
    top = ry - rh - 0.35 * inch
    avail_h = top - 1.0 * inch
    avail_w = PAGE_W - 2 * M
    cw = avail_w / cols
    chx = avail_h / rows
    rad = min(cw, chx) * 0.40
    rng = random.Random(1000 * board_no + variant)
    rng.shuffle(nums)
    palette = [th["a"], th["b"], "#FF8C61", "#9B6DD6", "#5AA9F0", "#3FC9B0"]
    for i, n in enumerate(nums):
        col = i % cols; row = i // cols
        cx = M + cw * (col + 0.5)
        cy = top - chx * (row + 0.5)
        ring = _col(palette[(row * cols + col) % len(palette)])
        c.setFillColor(white); c.setStrokeColor(ring); c.setLineWidth(2.4)
        c.circle(cx, cy, rad, fill=1, stroke=1)
        c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 17)
        c.drawCentredString(cx, cy - 0.085 * inch, str(n))

    fun_footer(c, "Math Games")
    c.showPage()


# ── MAZE ─────────────────────────────────────────────────────────────────────
def _build_maze(op, rule, seed, cols=6, rows=8):
    """
    Build a grid of facts. Returns (grid, path_set).
    grid[r][c] = (expr, ans). path_set = set of (r,c) on the solution path.
    'rule' selects which answers are "on path": 'even' or 'mult5'.
    Path is a connected route from START (top-left) to FINISH (bottom-right),
    using only down/right steps, guaranteed solvable.
    """
    rng = random.Random(seed)

    # 1. Build a monotone (down/right) path from (0,0) to (rows-1, cols-1).
    path = [(0, 0)]
    r, cc = 0, 0
    while (r, cc) != (rows - 1, cols - 1):
        can_down = r < rows - 1
        can_right = cc < cols - 1
        if can_down and can_right:
            if rng.random() < 0.5:
                r += 1
            else:
                cc += 1
        elif can_down:
            r += 1
        else:
            cc += 1
        path.append((r, cc))
    path_set = set(path)

    def on_rule(ans):
        if rule == "even":
            return ans % 2 == 0
        if rule == "mult5":
            return ans % 5 == 0
        return False

    if op == "mult":
        pairs = [(a, b) for a in range(1, 10) for b in range(1, 10)]
    else:
        pairs = [(a, b) for a in range(1, 13) for b in range(1, 13)]

    on_facts = [(make_fact(op, a, b)) for (a, b) in pairs if on_rule(make_fact(op, a, b)[1])]
    off_facts = [(make_fact(op, a, b)) for (a, b) in pairs if not on_rule(make_fact(op, a, b)[1])]
    rng.shuffle(on_facts); rng.shuffle(off_facts)

    def take(lst):
        f = lst.pop()
        lst.insert(0, f)  # cycle so we never run out
        return f

    grid = [[None] * cols for _ in range(rows)]
    for r in range(rows):
        for cc in range(cols):
            if (r, cc) in path_set:
                grid[r][cc] = take(on_facts)
            else:
                # ensure off-path cells do NOT satisfy the rule (so path is unique-ish)
                grid[r][cc] = take(off_facts)
    return grid, path_set


def page_maze(c, theme, op, rule, maze_no, seed):
    th = THEMES[theme]
    page_bg(c, theme)
    rule_word = "EVEN answers" if rule == "even" else "answers that are MULTIPLES of 5"
    fun_header(c, theme, f"Math Maze  {maze_no}",
               "Solve each fact — follow the path to escape!")
    y = name_line(c, theme)

    # Instruction banner
    iy = y - 0.5 * inch
    c.setFillColor(white); c.setStrokeColor(HexColor(th["b"])); c.setLineWidth(2)
    c.roundRect(M, iy, PAGE_W - 2 * M, 0.5 * inch, 10, fill=1, stroke=1)
    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("b"), 11)
    c.drawCentredString(PAGE_W / 2, iy + 0.28 * inch,
                        f"Solve every box. Color the path of {rule_word}")
    c.setFont(F("r"), 9.5); c.setFillColor(black)
    c.drawCentredString(PAGE_W / 2, iy + 0.09 * inch,
                        "from START to FINISH. You may only move down or right.")

    grid, path_set = _build_maze(op, rule, seed)
    rows = len(grid); cols = len(grid[0])

    top = iy - 0.3 * inch
    avail_h = top - 0.9 * inch
    avail_w = PAGE_W - 2 * M
    cw = avail_w / cols
    chh = avail_h / rows
    for r in range(rows):
        for cc in range(cols):
            x = M + cc * cw
            yy = top - (r + 1) * chh
            c.setFillColor(white); c.setStrokeColor(HexColor("#C9C9D8")); c.setLineWidth(1.2)
            c.rect(x, yy, cw, chh, fill=1, stroke=1)
            expr, ans = grid[r][cc]
            c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("b"), 12)
            c.drawCentredString(x + cw / 2, yy + chh / 2 - 0.04 * inch, expr)
    # START / FINISH labels
    def cell_xy(rc):
        r, cc = rc
        return M + cc * cw, top - (r + 1) * chh
    sx, sy = cell_xy((0, 0))
    c.setFillColor(HexColor(th["a"])); c.setFont(F("xb"), 8)
    c.drawCentredString(sx + cw / 2, sy + chh - 0.13 * inch, "START")
    fx, fy = cell_xy((rows - 1, cols - 1))
    c.setFillColor(HexColor(th["b"]))
    c.drawCentredString(fx + cw / 2, fy + 0.05 * inch, "FINISH")

    fun_footer(c, "Math Games")
    c.showPage()
    return (maze_no, rule, grid, path_set, cols, rows)


# ── SPIN & SOLVE ───────────────────────────────────────────────────────────────
def page_spin(c, theme, op, spin_no, seed, n_wedges=8):
    th = THEMES[theme]
    page_bg(c, theme)
    op_word = "add" if op == "add" else "multiply"
    sym = "+" if op == "add" else "×"
    fun_header(c, theme, f"Spin & Solve  {spin_no}",
               "Spin the spinner twice, then write the equation!")
    y = name_line(c, theme)

    # Instructions
    iy = y - 0.45 * inch
    c.setFillColor(white); c.setStrokeColor(HexColor(th["b"])); c.setLineWidth(2)
    c.roundRect(M, iy, PAGE_W - 2 * M, 0.45 * inch, 10, fill=1, stroke=1)
    c.setFillColor(black); c.setFont(F("r"), 10)
    c.drawCentredString(PAGE_W / 2, iy + 0.16 * inch,
        f"Use a paperclip and pencil as a spinner. Spin twice, then {op_word} the two numbers and write the equation.")

    # Spinner circle divided into wedges
    rng = random.Random(seed)
    if op == "mult":
        vals = rng.sample(range(2, 10), n_wedges) if n_wedges <= 8 else [rng.randint(2, 9) for _ in range(n_wedges)]
    else:
        vals = rng.sample(range(1, 13), n_wedges) if n_wedges <= 12 else [rng.randint(1, 12) for _ in range(n_wedges)]
    cx = PAGE_W / 2
    rad = 1.55 * inch
    cy = iy - 0.35 * inch - rad
    palette = [th["a"], th["b"], "#FF8C61", "#9B6DD6", "#5AA9F0", "#3FC9B0", "#FFC93C", "#FF6B9D"]
    for i in range(n_wedges):
        a0 = 360.0 / n_wedges * i
        a1 = 360.0 / n_wedges * (i + 1)
        c.setFillColor(_col(palette[i % len(palette)]))
        c.setStrokeColor(white); c.setLineWidth(2)
        p = c.beginPath()
        p.moveTo(cx, cy)
        steps = 12
        for s in range(steps + 1):
            ang = math.radians(a0 + (a1 - a0) * s / steps)
            p.lineTo(cx + rad * math.cos(ang), cy + rad * math.sin(ang))
        p.close()
        c.drawPath(p, fill=1, stroke=1)
        # number label at wedge mid
        mid = math.radians((a0 + a1) / 2)
        lx = cx + rad * 0.62 * math.cos(mid)
        ly = cy + rad * 0.62 * math.sin(mid)
        c.setFillColor(white); c.setFont(F("xb"), 18)
        c.drawCentredString(lx, ly - 0.09 * inch, str(vals[i]))
    # center hub
    c.setFillColor(white); c.setStrokeColor(HexColor("#3D3B6E")); c.setLineWidth(2)
    c.circle(cx, cy, 0.16 * inch, fill=1, stroke=1)
    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 9)
    c.drawCentredString(cx, cy - 0.05 * inch, "•")
    # spinner hint
    c.setFillColor(HexColor(th["a"])); c.setFont(F("b"), 9)
    c.drawCentredString(cx, cy - rad - 0.22 * inch, "Put a paperclip in the center and spin it with your pencil!")

    # Recording table
    ty = cy - rad - 0.5 * inch
    cols = ["Spin 1", "Spin 2", "My Equation", "Answer"]
    nrows = 6
    tw = PAGE_W - 2 * M
    col_w = [tw * 0.14, tw * 0.14, tw * 0.50, tw * 0.22]
    rh = (ty - 0.85 * inch) / (nrows + 1)
    rh = min(rh, 0.4 * inch)
    # header row
    x = M
    c.setFillColor(HexColor(th["a"]))
    c.rect(M, ty - rh, tw, rh, fill=1, stroke=0)
    for j, h in enumerate(cols):
        c.setFillColor(white); c.setFont(F("xb"), 10.5)
        c.drawCentredString(x + col_w[j] / 2, ty - rh + rh / 2 - 0.05 * inch, h)
        x += col_w[j]
    # body rows
    for ri in range(nrows):
        ry = ty - rh * (ri + 2)
        x = M
        for j in range(len(cols)):
            c.setFillColor(white if ri % 2 == 0 else HexColor(th["bg"]))
            c.setStrokeColor(HexColor("#C9C9D8")); c.setLineWidth(1)
            c.rect(x, ry, col_w[j], rh, fill=1, stroke=1)
            if j == 2:
                c.setFillColor(HexColor("#BBBBBB")); c.setFont(F("r"), 11)
                c.drawString(x + 0.12 * inch, ry + rh / 2 - 0.05 * inch,
                             f"____  {sym}  ____  =  ____")
            x += col_w[j]
    fun_footer(c, "Math Games")
    c.showPage()


# ── COVER ───────────────────────────────────────────────────────────────────
def page_cover(c, theme, op, grade):
    th = THEMES[theme]
    page_bg(c, theme)
    c.setFillColor(HexColor(th["a"]))
    c.rect(0, PAGE_H - 3.0 * inch, PAGE_W, 3.0 * inch, fill=1, stroke=0)
    for i in range(6):
        star(c, 1.2 * inch + i * 1.2 * inch, PAGE_H - 0.5 * inch, 9, th["b"])
    c.setFillColor(white); c.setFont(F("xb"), 44)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 1.7 * inch, "Math Games")
    c.setFont(F("xb"), 22)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 2.25 * inch, f"{OP_WORD[op]} Centers & Partner Games")
    c.setFont(F("b"), 14)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 2.65 * inch, f"Grade {grade}  ·  Low-Prep · Print & Play")

    # three game badges (dice / maze / spinner)
    by = PAGE_H - 4.55 * inch
    bx = [PAGE_W / 2 - 1.9 * inch, PAGE_W / 2, PAGE_W / 2 + 1.9 * inch]
    labels = ["BUMP", "MAZE", "SPIN"]
    for i, (x, lab) in enumerate(zip(bx, labels)):
        c.setFillColor(white); c.setStrokeColor(HexColor(th["a"])); c.setLineWidth(3)
        c.circle(x, by, 0.78 * inch, fill=1, stroke=1)
        if lab == "BUMP":
            dice(c, x - 0.32 * inch, by - 0.05 * inch, 0.32 * inch, 4, HexColor(th["a"]))
            dice(c, x + 0.02 * inch, by - 0.05 * inch, 0.32 * inch, 2, HexColor(th["b"]))
        elif lab == "MAZE":
            c.setStrokeColor(HexColor(th["a"])); c.setLineWidth(2.5)
            mx, my = x - 0.35 * inch, by - 0.3 * inch
            c.line(mx, my, mx, my + 0.6 * inch)
            c.line(mx, my + 0.6 * inch, mx + 0.35 * inch, my + 0.6 * inch)
            c.line(mx + 0.35 * inch, my + 0.6 * inch, mx + 0.35 * inch, my + 0.25 * inch)
            c.line(mx + 0.35 * inch, my + 0.25 * inch, mx + 0.7 * inch, my + 0.25 * inch)
        else:
            for k in range(6):
                a0 = math.radians(60 * k); a1 = math.radians(60 * (k + 1))
                c.setFillColor(_col([th["a"], th["b"], "#FFC93C"][k % 3]))
                p = c.beginPath(); p.moveTo(x, by)
                p.lineTo(x + 0.45 * inch * math.cos(a0), by + 0.45 * inch * math.sin(a0))
                p.lineTo(x + 0.45 * inch * math.cos(a1), by + 0.45 * inch * math.sin(a1))
                p.close(); c.drawPath(p, fill=1, stroke=0)
        c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 12)
        c.drawCentredString(x, by - 1.02 * inch, lab)

    cy = 1.55 * inch; card_h = 1.55 * inch
    c.setFillColor(white); c.setStrokeColor(HexColor(th["a"])); c.setLineWidth(1.5)
    c.roundRect(M + 0.4 * inch, cy, PAGE_W - 2 * M - 0.8 * inch, card_h, 10, fill=1, stroke=1)
    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 14)
    c.drawCentredString(PAGE_W / 2, cy + card_h - 0.32 * inch, "What's Inside")
    for i, b in enumerate([
        "3 partner & center games — BUMP, Math Maze, Spin & Solve",
        "Just add dice, chips, a paperclip & pencil",
        "Builds fact fluency through play",
        "Answer key & teacher notes included",
    ]):
        yb = cy + card_h - 0.62 * inch - i * 0.24 * inch
        check(c, M + 0.85 * inch, yb, th["a"], 10)
        c.setFillColor(black); c.setFont(F("r"), 11)
        c.drawString(M + 1.12 * inch, yb, b)
    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 15)
    c.drawCentredString(PAGE_W / 2, 0.95 * inch, AUTHOR)
    fun_footer(c, "Math Games")
    c.showPage()


# ── HOW TO PLAY (overview) ─────────────────────────────────────────────────────
def page_how_to_play(c, theme, op):
    th = THEMES[theme]
    page_bg(c, theme)
    fun_header(c, theme, "How to Play", "Three fun ways to practice math facts")
    op_word = "multiply" if op == "mult" else "add"
    sym = "×" if op == "mult" else "+"

    games = [
        ("BUMP  (2 players)", "#FF8C61",
         ["You need: 2 dice + colored chips (one color each).",
          f"Roll both dice and {op_word} the numbers ({sym}).",
          "Cover that answer on the board with your chip.",
          "Land on an opponent's single chip? BUMP it off!",
          "Stack two of your own chips to lock a number.",
          "Win by placing all your chips first."]),
        ("Math Maze  (solo or partners)", "#9B6DD6",
         ["You need: a pencil or crayon.",
          "Solve the math fact written in every box.",
          "Start at START. Move only DOWN or RIGHT.",
          "Follow the boxes whose answers match the rule",
          "(even answers, or multiples of 5).",
          "Color the path all the way to FINISH."]),
        ("Spin & Solve  (solo or partners)", "#3FC9B0",
         ["You need: a paperclip + a pencil.",
          "Hold the paperclip in the spinner center with your pencil.",
          "Flick the paperclip to spin — record the number.",
          "Spin a second time for the second number.",
          f"{op_word.capitalize()} the two numbers and write the equation.",
          "Fill in a full row of the recording table each turn."]),
    ]
    y = PAGE_H - 1.65 * inch
    box_h = 1.75 * inch
    for title, accent, lines in games:
        c.setFillColor(white); c.setStrokeColor(HexColor(accent)); c.setLineWidth(2)
        c.roundRect(M, y - box_h, PAGE_W - 2 * M, box_h, 12, fill=1, stroke=1)
        c.setFillColor(HexColor(accent))
        c.roundRect(M, y - 0.36 * inch, PAGE_W - 2 * M, 0.36 * inch, 12, fill=1, stroke=0)
        c.rect(M, y - 0.36 * inch, PAGE_W - 2 * M, 0.18 * inch, fill=1, stroke=0)
        c.setFillColor(white); c.setFont(F("xb"), 14)
        c.drawString(M + 0.2 * inch, y - 0.26 * inch, title)
        ly = y - 0.58 * inch
        c.setFillColor(black); c.setFont(F("r"), 10.5)
        for line in lines:
            check(c, M + 0.22 * inch, ly - 0.02 * inch, accent, 9)
            c.drawString(M + 0.45 * inch, ly, line)
            ly -= 0.205 * inch
        y -= box_h + 0.22 * inch
    fun_footer(c, "Math Games")
    c.showPage()


# ── ANSWER KEY / TEACHER NOTES ──────────────────────────────────────────────────
def page_answer_key(c, theme, op, mazes):
    th = THEMES[theme]
    page_bg(c, theme)
    fun_header(c, theme, "Answer Key & Teacher Notes", None)
    y = PAGE_H - 1.75 * inch

    c.setFillColor(HexColor("#3D3B6E")); c.setFont(F("xb"), 12)
    c.drawString(M, y, "Teacher Notes")
    y -= 0.24 * inch
    c.setFillColor(black); c.setFont(F("r"), 10)
    for note in [
        "BUMP: laminate boards for repeated use. Each player needs ~10 chips in one color.",
        f"Spin & Solve: any spin combo is correct — check that equations use {('×' if op=='mult' else '+')} and the right answer.",
        "Math Maze solutions are shaded below. There is exactly one down/right path to FINISH.",
    ]:
        c.drawString(M + 0.12 * inch, y, note)
        y -= 0.2 * inch
    y -= 0.1 * inch

    # Maze solutions — draw mini grids with the solution path shaded
    for (maze_no, rule, grid, path_set, cols, rows) in mazes:
        rule_word = "even answers" if rule == "even" else "multiples of 5"
        c.setFillColor(HexColor(th["a"])); c.setFont(F("xb"), 11)
        c.drawString(M, y, f"Math Maze {maze_no} — color the path of {rule_word}:")
        y -= 0.18 * inch
        mini_w = (PAGE_W - 2 * M) * 0.62
        cw = mini_w / cols
        chh = 0.2 * inch
        gtop = y
        for r in range(rows):
            for cc in range(cols):
                x = M + cc * cw
                yy = gtop - (r + 1) * chh
                on = (r, cc) in path_set
                c.setFillColor(HexColor(th["b"]) if on else white)
                c.setStrokeColor(HexColor("#C9C9D8")); c.setLineWidth(0.8)
                c.rect(x, yy, cw, chh, fill=1, stroke=1)
                expr, ans = grid[r][cc]
                c.setFillColor(white if on else HexColor("#3D3B6E"))
                c.setFont(F("b"), 6.5)
                c.drawCentredString(x + cw / 2, yy + chh / 2 - 0.025 * inch, f"{expr}={ans}")
        y = gtop - rows * chh - 0.3 * inch
    fun_footer(c, "Math Games")
    c.showPage()


# ── BUILD ─────────────────────────────────────────────────────────────────────
def build_product(op="mult", grade=3, theme="ocean", out_dir=None):
    if op not in ("mult", "add"):
        raise ValueError("op must be 'mult' or 'add'")
    if theme not in THEMES:
        theme = "ocean"
    if out_dir is None:
        slug = f"{op}_g{grade}_{theme}"
        out_dir = OUT_ROOT / "math_games" / slug
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "product.pdf"
    c = rl_canvas.Canvas(str(out), pagesize=letter)

    page_cover(c, theme, op, grade)
    page_how_to_play(c, theme, op)

    page_bump(c, theme, op, variant=0, board_no=1)
    page_bump(c, theme, op, variant=1, board_no=2)

    mazes = []
    mazes.append(page_maze(c, theme, op, rule="even",  maze_no=1, seed=11))
    mazes.append(page_maze(c, theme, op, rule="mult5", maze_no=2, seed=22))

    page_spin(c, theme, op, spin_no=1, seed=31, n_wedges=6)
    page_spin(c, theme, op, spin_no=2, seed=42, n_wedges=8)

    page_answer_key(c, theme, op, mazes)

    c.save()
    print(f"✓ Math Games {OP_WORD[op]} G{grade} [{theme}] → {out} ({out.stat().st_size:,} B)")
    return out


if __name__ == "__main__":
    op = sys.argv[1] if len(sys.argv) > 1 else "mult"
    grade = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    theme = sys.argv[3] if len(sys.argv) > 3 else "ocean"
    build_product(op=op, grade=grade, theme=theme)
