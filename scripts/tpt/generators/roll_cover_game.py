"""
Halloween Roll & Cover Math Game — Multiplication Grade 3
BrightOwl Learning  |  Game board + token sheet + instruction card
"""
from __future__ import annotations
import random
import math
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

# Products from 2×2 through 12×12 that fit the game
PRODUCTS = sorted(set(a*b for a in range(2,13) for b in range(2,13)))
# Take 36 products for a 6×6 grid
BOARD_NUMS = PRODUCTS[:36]

def draw_pumpkin_token(c, cx, cy, r=14, color=BRAND_COLOR):
    c.setFillColor(color)
    c.circle(cx, cy, r, fill=1, stroke=0)
    c.ellipse(cx-r*0.62, cy-r*0.45, cx-r*0.05, cy+r*0.45, fill=1, stroke=0)
    c.ellipse(cx+r*0.05, cy-r*0.45, cx+r*0.62, cy+r*0.45, fill=1, stroke=0)
    c.setFillColor(HexColor("#2D9A2D"))
    c.setLineWidth(1.8); c.setStrokeColor(HexColor("#2D9A2D"))
    c.line(cx, cy+r, cx+r*0.38, cy+r*1.45)
    c.setFillColor(black)
    c.circle(cx-r*0.28, cy+r*0.1, r*0.12, fill=1, stroke=0)
    c.circle(cx+r*0.28, cy+r*0.1, r*0.12, fill=1, stroke=0)
    p = c.beginPath()
    p.moveTo(cx-r*0.3, cy-r*0.12)
    p.lineTo(cx-r*0.12, cy-r*0.32)
    p.lineTo(cx+r*0.12, cy-r*0.32)
    p.lineTo(cx+r*0.3, cy-r*0.12)
    p.close()
    c.drawPath(p, fill=1, stroke=0)

def draw_game_board(c):
    # Full page background
    c.setFillColor(HexColor("#1A0A2E"))  # Deep purple/dark background
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Stars
    random.seed(7)
    for _ in range(40):
        sx = random.uniform(0.2*inch, PAGE_W - 0.2*inch)
        sy = random.uniform(0.5*inch, PAGE_H - 1.2*inch)
        sr = random.uniform(1, 3)
        c.setFillColor(HexColor("#FFFACD"))
        c.circle(sx, sy, sr, fill=1, stroke=0)

    # Header
    c.setFillColor(BRAND_COLOR)
    c.rect(0, PAGE_H - 1.1*inch, PAGE_W, 1.1*inch, fill=1, stroke=0)

    # Pumpkin decorations in header
    draw_pumpkin_token(c, 0.6*inch, PAGE_H - 0.55*inch, r=18)
    draw_pumpkin_token(c, PAGE_W - 0.6*inch, PAGE_H - 0.55*inch, r=18)

    c.setFillColor(HexColor("#1A0A2E"))
    c.setFont(FB(), 22)
    c.drawCentredString(PAGE_W/2, PAGE_H - 0.5*inch, "Halloween Roll & Cover")
    c.setFont(FN(), 12)
    c.drawCentredString(PAGE_W/2, PAGE_H - 0.78*inch, "Multiplication Math Game  |  Grade 3")

    # Roll instructions banner
    c.setFillColor(ACCENT)
    c.roundRect(1.2*inch, PAGE_H - 1.38*inch, PAGE_W - 2.4*inch, 0.28*inch, 5, fill=1, stroke=0)
    c.setFillColor(SECONDARY)
    c.setFont(FN(), 9)
    c.drawCentredString(PAGE_W/2, PAGE_H - 1.25*inch,
        "Roll 2 dice  •  Multiply the numbers  •  Cover that product with your pumpkin token!")

    # 6×6 grid of circles with numbers
    grid_cols = 6
    grid_rows = 6
    grid_left = 0.55*inch
    grid_top  = PAGE_H - 1.6*inch
    grid_w    = PAGE_W - 1.1*inch
    grid_h    = PAGE_H - 2.1*inch

    cell_w = grid_w / grid_cols
    cell_h = grid_h / grid_rows
    circle_r = min(cell_w, cell_h) * 0.4

    row_colors = [
        HexColor("#E8771A"), HexColor("#9B59B6"), HexColor("#E74C3C"),
        HexColor("#2ECC71"), HexColor("#3498DB"), HexColor("#F39C12"),
    ]

    random.seed(42)
    board = BOARD_NUMS[:]
    random.shuffle(board)

    for row in range(grid_rows):
        for col in range(grid_cols):
            idx = row * grid_cols + col
            cx = grid_left + col * cell_w + cell_w/2
            cy = grid_top - row * cell_h - cell_h/2

            # Glow circle
            c.setFillColor(HexColor("#2A1545"))
            c.circle(cx, cy, circle_r + 4, fill=1, stroke=0)

            # Main circle
            c.setFillColor(row_colors[row])
            c.setStrokeColor(ACCENT)
            c.setLineWidth(2)
            c.circle(cx, cy, circle_r, fill=1, stroke=1)

            # Number
            c.setFillColor(white)
            c.setFont(FB(), 18 if board[idx] < 100 else 14)
            c.drawCentredString(cx, cy - 6, str(board[idx]))

    # Footer
    c.setFillColor(BRAND_COLOR)
    c.rect(0, 0, PAGE_W, 0.45*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FN(), 9)
    c.drawCentredString(PAGE_W/2, 0.15*inch, AUTHOR + "  •  Halloween Roll & Cover Game")

def draw_token_sheet(c):
    c.setFillColor(BRAND_LIGHT)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    c.setFillColor(BRAND_COLOR)
    c.rect(0, PAGE_H - 0.7*inch, PAGE_W, 0.7*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FB(), 16)
    c.drawCentredString(PAGE_W/2, PAGE_H - 0.45*inch, "Token Sheet — Cut Out Your Pumpkin Tokens!")

    # Instructions
    c.setFont(FN(), 10)
    c.setFillColor(SECONDARY)
    c.drawCentredString(PAGE_W/2, PAGE_H - 0.9*inch,
        "Player 1: Orange tokens   |   Player 2: Purple tokens   |   Each player needs 20 tokens")

    # Player labels
    half_w = PAGE_W / 2
    c.setFont(FB(), 14)
    c.setFillColor(BRAND_COLOR)
    c.drawCentredString(half_w/2, PAGE_H - 1.2*inch, "PLAYER 1")
    c.setFillColor(HexColor("#9B59B6"))
    c.drawCentredString(half_w + half_w/2, PAGE_H - 1.2*inch, "PLAYER 2")

    # Divider
    c.setStrokeColor(HexColor("#DDDDDD"))
    c.setLineWidth(1)
    c.setDash([5,3])
    c.line(PAGE_W/2, 0.4*inch, PAGE_W/2, PAGE_H - 1.35*inch)
    c.setDash([])

    # Player 1 orange tokens (4 rows × 5 cols = 20)
    token_r = 22
    cols = 5
    rows = 4
    p1_start_x = 0.55*inch
    p1_start_y = PAGE_H - 1.6*inch
    spacing_x  = (half_w - 1.0*inch) / cols
    spacing_y  = (PAGE_H - 2.1*inch) / rows

    for row in range(rows):
        for col in range(cols):
            tx = p1_start_x + col * spacing_x + spacing_x/2
            ty = p1_start_y - row * spacing_y - spacing_y/2
            draw_pumpkin_token(c, tx, ty, r=token_r, color=BRAND_COLOR)
            # dashed cut circle
            c.setStrokeColor(HexColor("#BBBBBB"))
            c.setLineWidth(0.4)
            c.setDash([3,2])
            c.circle(tx, ty, token_r + 5, fill=0, stroke=1)
            c.setDash([])

    # Player 2 purple tokens
    p2_start_x = half_w + 0.55*inch
    for row in range(rows):
        for col in range(cols):
            tx = p2_start_x + col * spacing_x + spacing_x/2
            ty = p1_start_y - row * spacing_y - spacing_y/2
            draw_pumpkin_token(c, tx, ty, r=token_r, color=HexColor("#9B59B6"))
            c.setStrokeColor(HexColor("#BBBBBB"))
            c.setLineWidth(0.4)
            c.setDash([3,2])
            c.circle(tx, ty, token_r + 5, fill=0, stroke=1)
            c.setDash([])

    c.setFillColor(SECONDARY)
    c.rect(0, 0, PAGE_W, 0.35*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FN(), 8)
    c.drawCentredString(PAGE_W/2, 0.1*inch, AUTHOR + "  •  Cut out tokens along dashed lines. Color in or laminate for durability.")

def draw_instructions(c):
    c.setFillColor(HexColor("#FFF8F0"))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Header
    c.setFillColor(BRAND_COLOR)
    c.rect(0, PAGE_H - 0.9*inch, PAGE_W, 0.9*inch, fill=1, stroke=0)
    draw_pumpkin_token(c, 0.7*inch, PAGE_H-0.45*inch, r=18)
    draw_pumpkin_token(c, PAGE_W-0.7*inch, PAGE_H-0.45*inch, r=18)
    c.setFillColor(white)
    c.setFont(FB(), 20)
    c.drawCentredString(PAGE_W/2, PAGE_H-0.52*inch, "Halloween Roll & Cover")
    c.setFont(FN(), 11)
    c.drawCentredString(PAGE_W/2, PAGE_H-0.75*inch, "How to Play")

    # Materials needed
    box_x, box_y = 0.6*inch, PAGE_H - 1.5*inch
    box_w, box_h = PAGE_W - 1.2*inch, 0.9*inch
    c.setFillColor(BRAND_LIGHT)
    c.setStrokeColor(BRAND_COLOR); c.setLineWidth(2)
    c.roundRect(box_x, box_y, box_w, box_h, 8, fill=1, stroke=1)
    c.setFillColor(SECONDARY)
    c.setFont(FB(), 12)
    c.drawString(box_x + 0.2*inch, box_y + 0.6*inch, "You need:")
    c.setFont(FN(), 11)
    c.drawString(box_x + 0.2*inch, box_y + 0.32*inch,
        "2 players  •  2 dice  •  20 pumpkin tokens per player  •  Game board")

    # Steps
    steps = [
        ("1.", "Place the game board between two players."),
        ("2.", "Player 1 takes orange tokens. Player 2 takes purple tokens."),
        ("3.", "On your turn, roll both dice and MULTIPLY the two numbers."),
        ("4.", "Find that product on the game board and cover it with your token."),
        ("5.", "If the number is already covered, your turn is over — no move!"),
        ("6.", "The first player to get 4 tokens in a row (across, down, or diagonal) WINS!"),
        ("7.", "Variation: Play until the board is full. The player with the most tokens wins!"),
    ]

    sy = PAGE_H - 2.65*inch
    for num, text in steps:
        c.setFillColor(BRAND_COLOR)
        c.circle(box_x + 0.18*inch, sy + 0.08*inch, 0.14*inch, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont(FB(), 11)
        c.drawCentredString(box_x + 0.18*inch, sy + 0.04*inch, num[0])
        c.setFillColor(SECONDARY)
        c.setFont(FN(), 11)
        c.drawString(box_x + 0.45*inch, sy, text)
        sy -= 0.45*inch

    # Tip box
    ty = sy - 0.1*inch
    c.setFillColor(ACCENT)
    c.roundRect(box_x, ty, box_w, 0.8*inch, 8, fill=1, stroke=0)
    c.setFillColor(SECONDARY)
    c.setFont(FB(), 11)
    c.drawString(box_x + 0.2*inch, ty + 0.52*inch, "Math Tips:")
    c.setFont(FN(), 10)
    c.drawString(box_x + 0.2*inch, ty + 0.25*inch,
        "Remember: multiplication is repeated addition! 4 × 3 = 4 + 4 + 4 = 12")

    # Dice reference
    dy = ty - 0.5*inch
    c.setFillColor(SECONDARY)
    c.setFont(FB(), 11)
    c.drawString(box_x, dy, "Quick Multiplication Reference:")
    c.setFont(FN(), 9)
    ref = "2×2=4  3×3=9  4×4=16  5×5=25  6×6=36  2×6=12  3×4=12  4×6=24"
    c.drawString(box_x, dy - 0.25*inch, ref)

    c.setFillColor(SECONDARY)
    c.rect(0, 0, PAGE_W, 0.4*inch, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont(FN(), 8)
    c.drawCentredString(PAGE_W/2, 0.12*inch,
        AUTHOR + "  •  Halloween Roll & Cover  •  Grade 3  •  Supports multiplication fluency")

def build():
    out = ROOT / "products/tpt/samples/roll_cover_game/sample.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(out), pagesize=letter)

    draw_game_board(c)
    c.showPage()
    draw_token_sheet(c)
    c.showPage()
    draw_instructions(c)
    c.showPage()

    c.save()
    print(f"✓ roll_cover_game  → {out}  ({out.stat().st_size:,} bytes)")

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
