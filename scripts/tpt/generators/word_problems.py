"""
Halloween Word Problems — Math Grade 3
BrightOwl Learning  |  5 problem pages (20 total) + 1 answer-key page
"""
from __future__ import annotations
import sys
import math
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


# ── 20 word problems ───────────────────────────────────────────────────────────

# Each entry: (text_lines, answer, operation)
PROBLEMS = [
    (
        "Emma collected 8 bags of candy on Halloween night.",
        "Each bag holds 7 pieces of candy.",
        "How many pieces of candy does she have in all?",
        "56", "Multiplication"
    ),
    (
        "The haunted house had 48 visitors on Friday",
        "and 35 visitors on Saturday.",
        "How many more visitors came on Friday?",
        "13", "Subtraction"
    ),
    (
        "6 witches flew over the neighborhood.",
        "Each witch cast 9 spells along the way.",
        "How many spells were cast in all?",
        "54", "Multiplication"
    ),
    (
        "A pumpkin patch started with 120 pumpkins.",
        "The farmers sold 48 pumpkins by noon.",
        "How many pumpkins are left in the patch?",
        "72", "Subtraction"
    ),
    (
        "4 friendly ghosts each carry 6 spooky chains.",
        "They rattle them all night long!",
        "How many chains are there altogether?",
        "24", "Multiplication"
    ),
    (
        "A spider spun 3 webs in the morning",
        "and 5 more webs in the evening.",
        "How many webs did the spider spin in all?",
        "8", "Addition"
    ),
    (
        "There are 7 cauldrons in the witch's kitchen.",
        "Each cauldron holds 8 bubbling potions.",
        "How many potions are there altogether?",
        "56", "Multiplication"
    ),
    (
        "A bag of Halloween candy has 94 pieces.",
        "Liam ate 27 pieces in one night.",
        "How many pieces are left in the bag?",
        "67", "Subtraction"
    ),
    (
        "5 skeletons each found 4 golden coins",
        "buried in the haunted graveyard.",
        "How many golden coins did they find in all?",
        "20", "Multiplication"
    ),
    (
        "At the school parade there were 36 witches",
        "and 29 vampires in costumes.",
        "How many students wore costumes altogether?",
        "65", "Addition"
    ),
    (
        "A jar of candy corn has 9 rows.",
        "Each row has exactly 8 pieces of candy corn.",
        "How many pieces are in the jar in all?",
        "72", "Multiplication"
    ),
    (
        "A haunted castle has 3 towers.",
        "Each tower has 7 bats living inside it.",
        "How many bats live in the castle altogether?",
        "21", "Multiplication"
    ),
    (
        "On Halloween night 145 trick-or-treaters",
        "visited the neighborhood. 68 wore scary masks.",
        "How many did NOT wear a scary mask?",
        "77", "Subtraction"
    ),
    (
        "A witch made 6 batches of magic potion.",
        "Each batch fills 9 little bottles with potion.",
        "How many bottles of potion did she make?",
        "54", "Multiplication"
    ),
    (
        "There were 43 orange pumpkins and 28 white",
        "pumpkins displayed on a porch for Halloween.",
        "How many pumpkins were there in all?",
        "71", "Addition"
    ),
    (
        "8 friendly monsters each ate 5 chocolate bars",
        "at the Halloween party last night.",
        "How many chocolate bars did they eat in all?",
        "40", "Multiplication"
    ),
    (
        "The class collected 112 cans of food",
        "during the Halloween food drive this year.",
        "They gave away 75 cans. How many cans remain?",
        "37", "Subtraction"
    ),
    (
        "4 jack-o'-lanterns sat on each step of the stairs.",
        "There are 9 steps leading up to the house.",
        "How many jack-o'-lanterns are there in all?",
        "36", "Multiplication"
    ),
    (
        "There were 58 children at the Halloween dance.",
        "Then 27 more children arrived at the party.",
        "How many children are at the dance now?",
        "85", "Addition"
    ),
    (
        "A ghost visits 7 houses each hour on Halloween.",
        "The ghost goes trick-or-treating for 6 hours.",
        "How many houses does the ghost visit in all?",
        "42", "Multiplication"
    ),
]


# ── icon drawers ──────────────────────────────────────────────────────────────

def draw_icon_pumpkin(c, cx, cy, r=13):
    c.setFillColor(BRAND)
    c.setStrokeColor(HexColor("#8B4513"))
    c.setLineWidth(0.8)
    c.circle(cx, cy, r, fill=1, stroke=1)
    c.setFillColor(BRAND)
    for ox in (-r * 0.55, r * 0.55):
        c.ellipse(cx + ox - r * 0.28, cy - r * 0.55, cx + ox + r * 0.28, cy + r * 0.55, fill=1, stroke=0)
    c.setFillColor(HexColor("#3A7D44"))
    c.setLineWidth(1.5)
    c.setStrokeColor(HexColor("#3A7D44"))
    c.line(cx, cy + r, cx + r * 0.35, cy + r * 1.45)
    c.setFillColor(black)
    for ex in (cx - r * 0.26, cx + r * 0.26):
        p = c.beginPath()
        p.moveTo(ex, cy + r * 0.24)
        p.lineTo(ex - r * 0.12, cy + r * 0.03)
        p.lineTo(ex + r * 0.12, cy + r * 0.03)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
    c.setStrokeColor(black)
    c.setLineWidth(1)
    p = c.beginPath()
    p.moveTo(cx - r * 0.28, cy - r * 0.15)
    p.curveTo(cx - r * 0.1, cy - r * 0.35, cx + r * 0.1, cy - r * 0.35, cx + r * 0.28, cy - r * 0.15)
    c.drawPath(p, fill=0, stroke=1)


def draw_icon_bat(c, cx, cy, r=13):
    c.setFillColor(HexColor("#1A1A2E"))
    p = c.beginPath()
    p.moveTo(cx, cy)
    p.curveTo(cx - r * 0.4, cy + r * 0.7, cx - r * 1.5, cy + r * 0.4, cx - r * 1.8, cy - r * 0.2)
    p.curveTo(cx - r * 1.2, cy - r * 0.05, cx - r * 0.7, cy - r * 0.35, cx, cy)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    p = c.beginPath()
    p.moveTo(cx, cy)
    p.curveTo(cx + r * 0.4, cy + r * 0.7, cx + r * 1.5, cy + r * 0.4, cx + r * 1.8, cy - r * 0.2)
    p.curveTo(cx + r * 1.2, cy - r * 0.05, cx + r * 0.7, cy - r * 0.35, cx, cy)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.circle(cx, cy, r * 0.35, fill=1, stroke=0)
    c.setFillColor(HexColor("#FF6B35"))
    c.circle(cx - r * 0.12, cy + r * 0.05, r * 0.07, fill=1, stroke=0)
    c.circle(cx + r * 0.12, cy + r * 0.05, r * 0.07, fill=1, stroke=0)


def draw_icon_web(c, cx, cy, r=13):
    c.setStrokeColor(HexColor("#888888"))
    c.setLineWidth(0.6)
    for i in range(8):
        angle = math.radians(i * 45)
        c.line(cx, cy, cx + r * math.cos(angle), cy + r * math.sin(angle))
    for ring in range(1, 4):
        rr = r * ring / 3
        for i in range(8):
            a1 = math.radians(i * 45)
            a2 = math.radians((i + 1) * 45)
            p = c.beginPath()
            p.moveTo(cx + rr * math.cos(a1), cy + rr * math.sin(a1))
            p.curveTo(
                cx + rr * 1.04 * math.cos(a1), cy + rr * 1.04 * math.sin(a1),
                cx + rr * 1.04 * math.cos(a2), cy + rr * 1.04 * math.sin(a2),
                cx + rr * math.cos(a2), cy + rr * math.sin(a2)
            )
            c.drawPath(p, fill=0, stroke=1)
    c.setFillColor(black)
    c.circle(cx, cy, r * 0.1, fill=1, stroke=0)


def draw_icon_ghost(c, cx, cy, r=13):
    c.setFillColor(white)
    c.setStrokeColor(HexColor("#CCCCCC"))
    c.setLineWidth(0.7)
    p = c.beginPath()
    p.moveTo(cx - r, cy - r * 0.4)
    p.lineTo(cx - r, cy + r * 0.25)
    p.curveTo(cx - r, cy + r * 0.95, cx + r, cy + r * 0.95, cx + r, cy + r * 0.25)
    p.lineTo(cx + r, cy - r * 0.4)
    p.curveTo(cx + r * 0.65, cy - r * 0.15, cx + r * 0.3, cy - r * 0.85, cx, cy - r * 0.55)
    p.curveTo(cx - r * 0.3, cy - r * 0.85, cx - r * 0.65, cy - r * 0.15, cx - r, cy - r * 0.4)
    p.close()
    c.drawPath(p, fill=1, stroke=1)
    c.setFillColor(DARK)
    c.circle(cx - r * 0.3, cy + r * 0.3, r * 0.13, fill=1, stroke=0)
    c.circle(cx + r * 0.3, cy + r * 0.3, r * 0.13, fill=1, stroke=0)


ICON_DRAWERS = [draw_icon_pumpkin, draw_icon_bat, draw_icon_web, draw_icon_ghost]


# ── layout helpers ─────────────────────────────────────────────────────────────

HEADER_H = 0.55 * inch
FOOTER_H = 0.28 * inch

def draw_header(c, page_num):
    c.setFillColor(BRAND)
    c.rect(0, PAGE_H - HEADER_H, PAGE_W, HEADER_H, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FB(), 18)
    c.drawCentredString(PAGE_W / 2, PAGE_H - HEADER_H + 0.18 * inch,
                        "Halloween Word Problems")
    c.setFont(FN(), 9)
    c.drawCentredString(PAGE_W / 2, PAGE_H - HEADER_H + 0.05 * inch,
                        f"Grade 3 • Mixed Operations  |  Page {page_num}")


def draw_footer(c):
    c.setFillColor(DARK)
    c.rect(0, 0, PAGE_W, FOOTER_H, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FN(), 8)
    c.drawCentredString(PAGE_W / 2, 0.08 * inch,
                        AUTHOR + "  •  BrightOwlLearning.com  •  © 2024")


def wrap_text(text, max_chars=48):
    """Simple word-wrap returning list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if len(test) <= max_chars:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_problem_card(c, x, y, w, h, prob_num, prob_data):
    l1, l2, l3, answer, op = prob_data
    full_text = l1 + " " + l2 + " " + l3

    # Card background
    c.setFillColor(LIGHT)
    c.setStrokeColor(BRAND)
    c.setLineWidth(1.5)
    c.roundRect(x + 3, y + 3, w - 6, h - 6, 8, fill=1, stroke=1)

    # Problem number badge (circle)
    badge_r = 12
    badge_cx = x + 10 + badge_r
    badge_cy = y + h - 10 - badge_r
    c.setFillColor(BRAND)
    c.circle(badge_cx, badge_cy, badge_r, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FB(), 10)
    c.drawCentredString(badge_cx, badge_cy - 4, str(prob_num))

    # Icon (top-right area)
    icon_fn = ICON_DRAWERS[(prob_num - 1) % len(ICON_DRAWERS)]
    icon_cx = x + w - 22
    icon_cy = y + h - 22
    icon_fn(c, icon_cx, icon_cy, r=13)

    # Problem text
    lines = wrap_text(full_text, max_chars=50)
    txt_x = x + 8
    txt_y = y + h - 35
    c.setFillColor(DARK)
    c.setFont(FN(), 10)
    for line in lines[:3]:
        c.drawString(txt_x, txt_y, line)
        txt_y -= 14

    # "Show your work:" + blank box
    work_label_y = y + 44
    c.setFillColor(BRAND)
    c.setFont(FB(), 8)
    c.drawString(txt_x, work_label_y, "Show your work:")
    c.setFillColor(white)
    c.setStrokeColor(HexColor("#CCCCCC"))
    c.setLineWidth(0.8)
    box_w = (w - 16) * 0.55
    box_h = 22
    c.roundRect(txt_x, work_label_y - box_h - 2, box_w, box_h, 3, fill=1, stroke=1)

    # Answer line
    ans_x = txt_x + box_w + 8
    ans_w = w - 16 - box_w - 8
    c.setFillColor(DARK)
    c.setFont(FB(), 8)
    c.drawString(ans_x, work_label_y, "Answer:")
    c.setStrokeColor(DARK)
    c.setLineWidth(0.8)
    c.line(ans_x, work_label_y - 12, ans_x + ans_w - 5, work_label_y - 12)
    c.setFont(FN(), 7)
    c.setFillColor(HexColor("#999999"))
    c.drawString(ans_x, work_label_y - 26, "Operation: " + op[0:3] + ".")


# ── answer key ─────────────────────────────────────────────────────────────────

def draw_answer_key(c):
    c.setFillColor(BRAND)
    c.rect(0, PAGE_H - 0.55 * inch, PAGE_W, 0.55 * inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FB(), 20)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 0.38 * inch, "Answer Key")

    draw_footer(c)

    cols = 2
    rows_per_col = 10
    col_w = (PAGE_W - 2 * M) / cols
    start_y = PAGE_H - 0.65 * inch
    row_h = (start_y - FOOTER_H - 0.18 * inch) / rows_per_col

    # column headers
    for col in range(cols):
        hx = M + col * col_w
        c.setFillColor(DARK)
        c.setFont(FB(), 9.5)
        c.drawString(hx + 6, start_y - row_h * 0.3, "#")
        c.drawString(hx + 30, start_y - row_h * 0.3, "Answer")
        c.drawString(hx + 100, start_y - row_h * 0.3, "Operation")
        c.setStrokeColor(BRAND)
        c.setLineWidth(1)
        c.line(hx, start_y - row_h * 0.5, hx + col_w - 10, start_y - row_h * 0.5)

    for i, (l1, l2, l3, answer, op) in enumerate(PROBLEMS):
        col = i // rows_per_col
        row = i % rows_per_col
        rx = M + col * col_w
        ry = start_y - (row + 1) * row_h - row_h * 0.2

        bg = LIGHT if row % 2 == 0 else white
        c.setFillColor(bg)
        c.setStrokeColor(HexColor("#E0E0E0"))
        c.setLineWidth(0.4)
        c.rect(rx + 2, ry - 2, col_w - 14, row_h - 2, fill=1, stroke=1)

        c.setFillColor(BRAND)
        c.setFont(FB(), 9)
        c.drawString(rx + 6, ry + row_h * 0.18, str(i + 1))

        c.setFillColor(DARK)
        c.setFont(FB(), 9)
        c.drawString(rx + 30, ry + row_h * 0.18, answer)

        c.setFont(FN(), 8.5)
        c.drawString(rx + 100, ry + row_h * 0.18, op)

    c.showPage()


# ── main ───────────────────────────────────────────────────────────────────────

def generate(out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out_path), pagesize=letter)

    # 5 problem pages, 4 problems per page
    per_page = 4
    cols_per_page = 2
    rows_per_page = 2

    card_w = (PAGE_W - 2 * M - 0.12 * inch) / cols_per_page
    card_h = (PAGE_H - HEADER_H - FOOTER_H - 0.18 * inch) / rows_per_page

    for page in range(5):
        draw_header(c, page + 1)
        draw_footer(c)

        for slot in range(per_page):
            prob_idx = page * per_page + slot
            col = slot % cols_per_page
            row = slot // cols_per_page

            px = M + col * (card_w + 0.12 * inch)
            py = PAGE_H - HEADER_H - (row + 1) * card_h - 0.08 * inch

            draw_problem_card(c, px, py, card_w, card_h,
                              prob_idx + 1, PROBLEMS[prob_idx])

        c.showPage()

    draw_answer_key(c)
    c.save()
    size = out_path.stat().st_size
    print(f"✓ word_problems → {out_path}  ({size:,} bytes)")


if __name__ == "__main__":
    OUT = Path(__file__).resolve().parent.parent.parent.parent / \
          "products" / "tpt" / "samples" / "word_problems" / "sample.pdf"
    generate(OUT)


def build_all(out_dir=None, themes=None, gemini_key=None):
    from pathlib import Path as _P
    base = _P(out_dir) if out_dir else _P(__file__).resolve().parents[3] / "products" / "tpt"
    name = _P(__file__).stem
    out = base / "samples" / name / "sample.pdf"
    generate(out)
