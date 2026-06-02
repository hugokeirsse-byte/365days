"""
TPT — Moteur de production de fiches d'exercices (vertical Teachers Pay Teachers).

Génère un PACK complet prêt à vendre :
  worksheet.pdf  — les fiches élève (3 niveaux : support / on-level / challenge)
  answer_key.pdf — les corrigés (correct PAR CONSTRUCTION : même code génère problème + réponse)
  cover.pdf      — la vignette/cover TPT (procédurale, zéro IA)
  terms.pdf      — terms of use (template légal)
  listing.md     — titre SEO + description + tags + prix pour l'upload
  bundle.zip     — tout regroupé

PRINCIPE NON-NÉGOCIABLE (cf. data/verticals/tpt/CAHIER_DES_CHARGES.md) :
  le contenu mathématique est généré par du code pur. Le corrigé est dérivé du MÊME
  appel (mêmes seed + params) → il est impossible d'avoir une réponse fausse.

Usage (env vars, tout optionnel — defaults = pack démo) :
  SKILL=arithmetic OPERATION=mul GRADE=3 THEME=halloween SEED=42 \
  TITLE="Halloween Multiplication Worksheets 3rd Grade" \
  OUT_DIR=products/tpt/demo \
  python scripts/tpt/generate_worksheet.py

Stdlib + reportlab uniquement. Exit 0 toujours (sauf erreur de config dure).
"""

import json
import os
import random
import zipfile
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas

try:
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF
    _SVGLIB = True
except ImportError:
    _SVGLIB = False

_CLIPART_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "_shared", "clipart")

# theme → list of SVG filenames in _CLIPART_DIR (used as corner decorations)
_THEME_CLIPART = {
    "halloween": ["halloween_pumpkin.svg"],
    "christmas": ["christmas_snowflake.svg"],
}

# ----------------------------------------------------------------------------- #
# CONFIG
# ----------------------------------------------------------------------------- #

PAGE_W, PAGE_H = letter  # 8.5 x 11 in
MARGIN = 0.6 * inch      # > 0.5in print-safe (cf. CdC §11)

LEVELS = ["support", "on_level", "challenge"]
LEVEL_LABELS = {
    "support": "Level 1 — Support",
    "on_level": "Level 2 — On Level",
    "challenge": "Level 3 — Challenge",
}

# Palettes thématiques (cover + accents). Chaque thème = (primaire, clair, emoji-ish label)
THEMES = {
    "plain":     {"primary": "#2E5E8C", "light": "#E8F0F8", "label": "Math Practice"},
    "halloween": {"primary": "#E8771A", "light": "#FBEBDC", "label": "Halloween Math"},
    "christmas": {"primary": "#C0392B", "light": "#FBEAE8", "label": "Christmas Math"},
    "valentine": {"primary": "#D6336C", "light": "#FCE6EE", "label": "Valentine Math"},
    "spring":    {"primary": "#2E9E5B", "light": "#E6F6EC", "label": "Spring Math"},
}

OP_SYMBOL = {"add": "+", "sub": "−", "mul": "×", "div": "÷"}
OP_NAME = {"add": "Addition", "sub": "Subtraction", "mul": "Multiplication", "div": "Division"}


# ----------------------------------------------------------------------------- #
# GÉNÉRATEURS DE CONTENU — procéduraux, corrects par construction
# ----------------------------------------------------------------------------- #

def gen_arithmetic(operation, level, rng, count):
    """Retourne une liste de (a, op, b, answer). Réponse calculée → toujours correcte."""
    problems = []
    # plages par niveau et par opération
    ranges = {
        "support":   {"add": (1, 20), "sub": (1, 20), "mul": (2, 6), "div": (2, 6)},
        "on_level":  {"add": (10, 99), "sub": (10, 99), "mul": (2, 10), "div": (2, 10)},
        "challenge": {"add": (100, 999), "sub": (100, 999), "mul": (3, 12), "div": (3, 12)},
    }
    lo, hi = ranges[level][operation]
    for _ in range(count):
        if operation == "add":
            a, b = rng.randint(lo, hi), rng.randint(lo, hi)
            ans = a + b
        elif operation == "sub":
            a, b = rng.randint(lo, hi), rng.randint(lo, hi)
            if b > a:
                a, b = b, a  # pas de négatif (niveau primaire)
            ans = a - b
        elif operation == "mul":
            a, b = rng.randint(lo, hi), rng.randint(lo, hi)
            ans = a * b
        elif operation == "div":
            # division exacte : on construit b * quotient pour garantir un reste nul
            b = rng.randint(lo, hi)
            q = rng.randint(lo, hi)
            a = b * q
            ans = q
        else:
            raise ValueError(f"opération inconnue: {operation}")
        problems.append((a, OP_SYMBOL[operation], b, ans))
    return problems


# ----------------------------------------------------------------------------- #
# DESSIN — helpers ReportLab
# ----------------------------------------------------------------------------- #

def _name_line(c, y):
    """Ligne Name / Date en haut de chaque fiche (standard TPT)."""
    c.setFont("Helvetica", 11)
    c.setFillColor(black)
    c.drawString(MARGIN, y, "Name: ______________________________")
    c.drawRightString(PAGE_W - MARGIN, y, "Date: ________________")


def _header(c, title, subtitle, theme):
    """Bandeau de titre coloré en haut de page."""
    pal = THEMES[theme]
    band_h = 0.7 * inch
    top = PAGE_H - MARGIN
    c.setFillColor(HexColor(pal["primary"]))
    c.roundRect(MARGIN, top - band_h, PAGE_W - 2 * MARGIN, band_h, 8, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(PAGE_W / 2, top - band_h / 2 + 4, title)
    if subtitle:
        c.setFont("Helvetica", 11)
        c.drawCentredString(PAGE_W / 2, top - band_h / 2 - 13, subtitle)
    return top - band_h - 0.25 * inch


def _footer(c, author):
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(HexColor("#999999"))
    c.drawString(MARGIN, 0.35 * inch, f"© {datetime.now().year} {author}  —  For single classroom use. Do not redistribute.")
    c.drawRightString(PAGE_W - MARGIN, 0.35 * inch, "365days · No Prep · Just Print")


def _problem_grid(c, problems, start_y, is_answer_key, theme):
    """Dessine une grille de problèmes verticaux (style colonne). 5 colonnes.

    Hauteur de rangée calculée dynamiquement pour que la réponse (corrigé) ne
    déborde jamais sur la rangée suivante (cf. audit : densité + lisibilité).
    """
    pal = THEMES[theme]
    cols = 5
    usable_w = PAGE_W - 2 * MARGIN
    col_w = usable_w / cols
    bottom = 0.75 * inch  # marge basse avant le footer
    n = len(problems)
    rows = (n + cols - 1) // cols
    # hauteur de rangée : remplit l'espace dispo, bornée pour rester lisible
    avail = start_y - bottom
    row_h = max(1.0 * inch, min(1.35 * inch, avail / max(rows, 1)))

    # offsets internes à la cellule (toujours < row_h pour éviter tout chevauchement)
    OFF_A = 18      # premier opérande
    OFF_OPB = 40    # opérateur + second opérande
    OFF_LINE = 48   # barre de calcul
    OFF_ANS = 70    # réponse (corrigé)

    for idx, (a, op, b, ans) in enumerate(problems):
        r, col = divmod(idx, cols)
        x = MARGIN + col * col_w
        y = start_y - r * row_h
        # numéro
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(HexColor(pal["primary"]))
        c.drawString(x, y, f"{idx + 1}.")
        # opération alignée à droite dans la cellule
        c.setFillColor(black)
        c.setFont("Helvetica", 18)
        box_r = x + col_w - 0.35 * inch
        c.drawRightString(box_r, y - OFF_A, str(a))
        c.drawRightString(box_r, y - OFF_OPB, f"{op} {b}")
        # barre
        c.setLineWidth(1.2)
        c.line(x + 0.15 * inch, y - OFF_LINE, box_r, y - OFF_LINE)
        # réponse (corrigé)
        if is_answer_key:
            c.setFillColor(HexColor("#C0392B"))
            c.setFont("Helvetica-Bold", 18)
            c.drawRightString(box_r, y - OFF_ANS, str(ans))
            c.setFillColor(black)
    return n


# ----------------------------------------------------------------------------- #
# PAGES
# ----------------------------------------------------------------------------- #

def _draw_corner_decorations(c, theme, count=4):
    """Draw small SVG clip art in the four corners of the content area."""
    if not _SVGLIB:
        return
    names = _THEME_CLIPART.get(theme, [])
    if not names:
        return
    svg_path = os.path.join(_CLIPART_DIR, names[0])
    if not os.path.exists(svg_path):
        return
    try:
        drawing = svg2rlg(svg_path)
    except Exception:
        return
    if not drawing:
        return
    size = 0.75 * inch
    scale = size / max(drawing.width, drawing.height)
    positions = [
        (MARGIN, PAGE_H - MARGIN - size),
        (PAGE_W - MARGIN - size, PAGE_H - MARGIN - size),
        (MARGIN, MARGIN + 0.2 * inch),
        (PAGE_W - MARGIN - size, MARGIN + 0.2 * inch),
    ]
    for x, y in positions[:count]:
        c.saveState()
        c.translate(x, y)
        c.scale(scale, scale)
        renderPDF.draw(drawing, c, 0, 0)
        c.restoreState()


def build_worksheet_pdf(path, cfg, content_by_level, is_answer_key):
    c = canvas.Canvas(path, pagesize=letter)
    title = cfg["title_short"]
    if is_answer_key:
        title += " — ANSWER KEY"
    for level in LEVELS:
        problems = content_by_level[level]
        sub = f"{LEVEL_LABELS[level]}  •  Grade {cfg['grade']}  •  {OP_NAME[cfg['operation']]}"
        y = _header(c, title, sub, cfg["theme"])
        _name_line(c, y)
        y -= 0.4 * inch
        _problem_grid(c, problems, y, is_answer_key, cfg["theme"])
        _draw_corner_decorations(c, cfg["theme"])
        _footer(c, cfg["author"])
        c.showPage()
    c.save()


def build_cover_pdf(path, cfg):
    pal = THEMES[cfg["theme"]]
    c = canvas.Canvas(path, pagesize=letter)
    # fond clair
    c.setFillColor(HexColor(pal["light"]))
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # cadre
    c.setStrokeColor(HexColor(pal["primary"]))
    c.setLineWidth(6)
    c.roundRect(MARGIN, MARGIN, PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN, 16, fill=0, stroke=1)
    # bandeau titre
    band_h = 2.2 * inch
    by = PAGE_H - MARGIN - 1.2 * inch - band_h
    c.setFillColor(HexColor(pal["primary"]))
    c.roundRect(MARGIN + 0.4 * inch, by, PAGE_W - 2 * MARGIN - 0.8 * inch, band_h, 12, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 30)
    # titre sur 2 lignes
    words = cfg["title_short"].split()
    mid = len(words) // 2
    line1 = " ".join(words[:mid]) or cfg["title_short"]
    line2 = " ".join(words[mid:])
    c.drawCentredString(PAGE_W / 2, by + band_h - 0.75 * inch, line1)
    if line2:
        c.drawCentredString(PAGE_W / 2, by + band_h - 1.35 * inch, line2)
    c.setFont("Helvetica", 16)
    c.drawCentredString(PAGE_W / 2, by + 0.45 * inch, f"Grade {cfg['grade']}  •  {OP_NAME[cfg['operation']]}")
    # bullets de vente
    bullets = [
        "3 Differentiated Levels Included",
        "Answer Keys for Every Page",
        "No Prep — Just Print & Go",
        "Print-Ready 8.5 x 11 (US Letter)",
    ]
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 16)
    yb = by - 0.9 * inch
    for b in bullets:
        c.setFillColor(HexColor(pal["primary"]))
        c.drawString(MARGIN + 1.0 * inch, yb, "✓")
        c.setFillColor(black)
        c.drawString(MARGIN + 1.35 * inch, yb, b)
        yb -= 0.5 * inch
    # pied
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(HexColor("#666666"))
    c.drawCentredString(PAGE_W / 2, MARGIN + 0.4 * inch, f"by {cfg['author']}")
    c.showPage()
    c.save()


def build_terms_pdf(path, cfg):
    c = canvas.Canvas(path, pagesize=letter)
    y = _header(c, "Terms of Use", "Thank you for your purchase!", cfg["theme"])
    c.setFillColor(black)
    c.setFont("Helvetica", 11)
    lines = [
        "",
        "PERMITTED:",
        "  • Use with your own students, in your own classroom.",
        "  • Print as many copies as you need for your students.",
        "  • Save on a password-protected device for personal use.",
        "",
        "NOT PERMITTED:",
        "  • Sharing, selling, or redistributing this resource.",
        "  • Posting on shared drives, websites, or social media.",
        "  • Claiming this resource as your own.",
        "",
        "Each license is for a single classroom. Additional licenses are",
        "available at a discount for your grade-level team or school.",
        "",
        "Fonts & layout: generated procedurally; standard typefaces (Helvetica).",
        "Math content is computer-generated and verified for accuracy.",
        "",
        f"© {datetime.now().year} {cfg['author']}. All rights reserved.",
    ]
    ty = y - 0.2 * inch
    for ln in lines:
        c.drawString(MARGIN, ty, ln)
        ty -= 0.28 * inch
    _footer(c, cfg["author"])
    c.showPage()
    c.save()


def build_listing_md(path, cfg, total_problems):
    pal = THEMES[cfg["theme"]]
    tags = cfg["tags"]
    md = f"""# TPT LISTING — {cfg['id']}

## Titre (SEO — copier tel quel)
{cfg['title_seo']}

## Prix conseillé
${cfg['price_usd']:.2f}

## Description (copier-coller dans TPT)
{pal['label']} made easy! This **no-prep** resource gives you {OP_NAME[cfg['operation']].lower()} practice for **Grade {cfg['grade']}** at **3 differentiated levels** so every student is challenged at the right level.

**What's included:**
- 3 worksheets (Support / On-Level / Challenge) — {total_problems} problems total
- Full answer keys for every page
- Print-ready 8.5 x 11 (US Letter)
- Terms of use

**Perfect for:** morning work, homework, math centers, early finishers, sub plans, and review.

Just print and go — no prep required!

## Tags ({len(tags)})
{', '.join(tags)}

## Standards (Common Core — à ajuster selon le grade)
- 3.OA.C.7 — Multiply and divide within 100
- 3.OA.A.1 — Interpret products of whole numbers

## Fichiers du pack
- worksheet.pdf — fiches élève (3 niveaux)
- answer_key.pdf — corrigés
- cover.pdf — vignette TPT
- terms.pdf — terms of use
- bundle.zip — tout regroupé
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)


# ----------------------------------------------------------------------------- #
# MAIN
# ----------------------------------------------------------------------------- #

def main():
    skill = os.environ.get("SKILL", "arithmetic")
    operation = os.environ.get("OPERATION", "mul")
    grade = os.environ.get("GRADE", "3")
    theme = os.environ.get("THEME", "halloween")
    seed = int(os.environ.get("SEED", "42"))
    author = os.environ.get("AUTHOR", "BrightOwl Learning")
    count = int(os.environ.get("PROBLEMS_PER_PAGE", "25"))
    out_dir = os.environ.get("OUT_DIR", "products/tpt/demo")

    if theme not in THEMES:
        theme = "plain"
    if operation not in OP_SYMBOL:
        operation = "mul"

    pal = THEMES[theme]
    title_short = f"{pal['label']}"
    default_seo = f"{pal['label']} Worksheets {grade}{_ordinal(grade)} Grade — Differentiated 3 Levels, Answer Keys, No Prep"
    title_seo = os.environ.get("TITLE", default_seo)

    cfg = {
        "id": os.environ.get("PRODUCT_ID",
                             f"tpt_{datetime.now():%Y-%m-%d}_{skill}_{operation}_{theme}_g{grade}"),
        "skill": skill,
        "operation": operation,
        "grade": grade,
        "theme": theme,
        "author": author,
        "title_short": title_short,
        "title_seo": title_seo,
        "price_usd": float(os.environ.get("PRICE_USD", "3.50")),
        "tags": [theme, OP_NAME[operation].lower(), f"{grade}{_ordinal(grade)} grade",
                 "differentiated", "no prep", "answer key", "math facts", "printable"],
    }

    # contenu : même rng par niveau → reproductible. Worksheet et answer key partagent EXACTEMENT le contenu.
    content = {}
    for i, level in enumerate(LEVELS):
        rng = random.Random(seed + i * 1000)
        content[level] = gen_arithmetic(operation, level, rng, count)

    total_problems = sum(len(v) for v in content.values())

    os.makedirs(out_dir, exist_ok=True)
    ws = os.path.join(out_dir, "worksheet.pdf")
    ak = os.path.join(out_dir, "answer_key.pdf")
    cov = os.path.join(out_dir, "cover.pdf")
    terms = os.path.join(out_dir, "terms.pdf")
    listing = os.path.join(out_dir, "listing.md")

    build_worksheet_pdf(ws, cfg, content, is_answer_key=False)
    build_worksheet_pdf(ak, cfg, content, is_answer_key=True)
    build_cover_pdf(cov, cfg)
    build_terms_pdf(terms, cfg)
    build_listing_md(listing, cfg, total_problems)

    # content.json : source de vérité pour l'audit (vérifie la correction du corrigé)
    content_dump = {
        "id": cfg["id"], "skill": skill, "operation": operation, "grade": grade,
        "theme": theme, "seed": seed, "pages_expected": {"worksheet": len(LEVELS), "answer_key": len(LEVELS)},
        "config": {"margin_in": MARGIN / inch, "body_font_pt": 18},
        "levels": {lvl: [{"a": a, "op": op, "b": b, "answer": ans}
                         for (a, op, b, ans) in content[lvl]] for lvl in LEVELS},
    }
    with open(os.path.join(out_dir, "content.json"), "w", encoding="utf-8") as f:
        json.dump(content_dump, f, indent=2)

    # bundle zip
    bundle = os.path.join(out_dir, "bundle.zip")
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        for fn in ("cover.pdf", "worksheet.pdf", "answer_key.pdf", "terms.pdf", "listing.md"):
            z.write(os.path.join(out_dir, fn), fn)

    print(f"[OK] Pack TPT généré dans {out_dir}/")
    print(f"     skill={skill} op={operation} grade={grade} theme={theme} seed={seed}")
    print(f"     {total_problems} problèmes sur 3 niveaux — corrigés inclus")
    print(f"     fichiers : worksheet.pdf, answer_key.pdf, cover.pdf, terms.pdf, listing.md, bundle.zip")


def _ordinal(grade):
    try:
        n = int(grade)
    except ValueError:
        return ""
    return {1: "st", 2: "nd", 3: "rd"}.get(n if n < 20 else n % 10, "th")


if __name__ == "__main__":
    main()
