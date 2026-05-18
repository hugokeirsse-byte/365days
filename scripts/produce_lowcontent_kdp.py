"""
Pipeline LOW-CONTENT KDP — journals, planners, trackers nichés.

100% offline. Aucune IA image. Layout pur PIL + ReportLab.
Qualité PARFAITE garantie (texte vectoriel via police TTF).

Concept : livres de 100 pages avec :
- Page de garde stylisée
- Pages intérieures structurées (lignes, grilles, prompts)
- Couverture optionnelle (peut utiliser produce_kdp_cover en complément)

Format KDP standard :
- Trim : 6×9 inches (152.4×228.6 mm) — format paperback le plus vendu
- Marges : 0.75" intérieure (gutter), 0.5" extérieure, 0.5" haut/bas
- DPI : 300

Niches codées (10 livres prêts) :
- fishing_log : journal pêche (100 prises notées)
- bird_watching : journal ornithologue
- crochet_tracker : projets crochet
- pet_health : suivi vétérinaire chat/chien
- sourdough_log : journal levain
- dnd_campaign : campagne D&D
- garden_planner : planning jardinage saisonnier
- climbing_log : voies escaladées
- vinyl_collection : collection vinyles
- brewing_log : journal brassage bière

Variables d'env :
  BOOK=fishing_log    (clé dans LOW_CONTENT_BOOKS)
  PAGES=100           nombre de pages intérieures
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from reportlab.lib.pagesizes import inch
    from reportlab.lib.units import inch as INCH
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("ERREUR : reportlab non installé. pip install reportlab")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "lowcontent_kdp"

# Format KDP 6x9 paperback (le plus vendu)
TRIM_W = 6 * INCH   # 432 pt
TRIM_H = 9 * INCH   # 648 pt
MARGIN_INNER = 0.75 * INCH  # gutter KDP
MARGIN_OUTER = 0.5 * INCH
MARGIN_TOP = 0.5 * INCH
MARGIN_BOTTOM = 0.5 * INCH

# Polices : on essaie de charger DejaVu, fallback Helvetica
try:
    pdfmetrics.registerFont(TTFont("DejaVuSerif",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSerifBold",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSerifItalic",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"))
    SERIF = "DejaVuSerif"
    SERIF_BOLD = "DejaVuSerifBold"
    SERIF_ITALIC = "DejaVuSerifItalic"
except Exception:
    SERIF = "Helvetica"
    SERIF_BOLD = "Helvetica-Bold"
    SERIF_ITALIC = "Helvetica-Oblique"


# ============================================================
# LIBRARY DES LIVRES LOW-CONTENT
# Chaque entrée définit la structure des pages intérieures
# ============================================================

def gutter_offset(page_num: int) -> tuple[float, float]:
    """Retourne (left_margin, right_margin) selon recto/verso."""
    if page_num % 2 == 1:  # impair = recto, gutter à gauche
        return MARGIN_INNER, MARGIN_OUTER
    return MARGIN_OUTER, MARGIN_INNER


def draw_decorative_border(c, page_num: int) -> None:
    """Bordure décorative discrète en haut et bas."""
    left, right = gutter_offset(page_num)
    c.setStrokeColorRGB(0.5, 0.4, 0.3)
    c.setLineWidth(0.4)
    # Ligne horizontale en haut
    c.line(left, TRIM_H - MARGIN_TOP / 2,
           TRIM_W - right, TRIM_H - MARGIN_TOP / 2)
    # Ligne horizontale en bas
    c.line(left, MARGIN_BOTTOM / 2,
           TRIM_W - right, MARGIN_BOTTOM / 2)
    # Numéro de page
    c.setFont(SERIF_ITALIC, 9)
    c.setFillColorRGB(0.4, 0.3, 0.2)
    c.drawCentredString(TRIM_W / 2, MARGIN_BOTTOM / 4, f"— {page_num} —")


# ============================================================
# Templates de pages réutilisables
# ============================================================

def draw_lined_page(c, page_num: int, title: str, fields: list[tuple],
                     lines_below: int = 15) -> None:
    """Page avec en-tête, champs (label : ____), puis lignes pour notes."""
    left, right = gutter_offset(page_num)
    content_w = TRIM_W - left - right
    y = TRIM_H - MARGIN_TOP - 12

    # Titre
    c.setFont(SERIF_BOLD, 14)
    c.setFillColorRGB(0.2, 0.15, 0.1)
    c.drawString(left, y, title)
    y -= 14
    # Sous-ligne décorative
    c.setStrokeColorRGB(0.5, 0.4, 0.3)
    c.setLineWidth(0.6)
    c.line(left, y, left + 40, y)
    y -= 18

    # Champs structurés
    c.setFont(SERIF, 10)
    c.setFillColorRGB(0.15, 0.1, 0.05)
    for label, _ in fields:
        c.drawString(left, y, f"{label}:")
        # Ligne pointillée pour saisie
        label_width = c.stringWidth(f"{label}:", SERIF, 10)
        c.setDash(2, 2)
        c.setStrokeColorRGB(0.5, 0.45, 0.4)
        c.line(left + label_width + 8, y - 1,
               TRIM_W - right, y - 1)
        c.setDash()
        y -= 22

    # Lignes pour notes
    if lines_below > 0:
        y -= 10
        c.setFont(SERIF_ITALIC, 9)
        c.setFillColorRGB(0.4, 0.3, 0.2)
        c.drawString(left, y, "Notes")
        y -= 14
        c.setStrokeColorRGB(0.6, 0.55, 0.5)
        c.setLineWidth(0.3)
        for _ in range(lines_below):
            c.line(left, y, TRIM_W - right, y)
            y -= 16
            if y < MARGIN_BOTTOM + 30:
                break


def draw_title_page(c, title: str, subtitle: str, author: str) -> None:
    c.setFont(SERIF_BOLD, 28)
    c.setFillColorRGB(0.15, 0.1, 0.05)
    c.drawCentredString(TRIM_W / 2, TRIM_H / 2 + 50, title)

    c.setFont(SERIF_ITALIC, 14)
    c.setFillColorRGB(0.35, 0.25, 0.15)
    # Wrap subtitle if needed
    max_w = TRIM_W - 100
    words = subtitle.split()
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if c.stringWidth(test, SERIF_ITALIC, 14) <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    yy = TRIM_H / 2 + 10
    for line in lines:
        c.drawCentredString(TRIM_W / 2, yy, line)
        yy -= 18

    # Ornement central
    c.setStrokeColorRGB(0.4, 0.3, 0.2)
    c.setLineWidth(1.2)
    c.line(TRIM_W / 2 - 30, yy - 20, TRIM_W / 2 + 30, yy - 20)

    c.setFont(SERIF, 10)
    c.setFillColorRGB(0.3, 0.25, 0.2)
    c.drawCentredString(TRIM_W / 2, 60, author)


def draw_intro_page(c, content_paragraphs: list[str]) -> None:
    c.setFont(SERIF_BOLD, 16)
    c.setFillColorRGB(0.2, 0.15, 0.1)
    c.drawString(MARGIN_INNER, TRIM_H - MARGIN_TOP - 14, "How to use this journal")

    c.setFont(SERIF, 10.5)
    c.setFillColorRGB(0.15, 0.1, 0.05)
    y = TRIM_H - MARGIN_TOP - 50
    for para in content_paragraphs:
        # Wrap
        words = para.split()
        line = ""
        for w in words:
            test = (line + " " + w).strip()
            if c.stringWidth(test, SERIF, 10.5) <= TRIM_W - MARGIN_INNER - MARGIN_OUTER:
                line = test
            else:
                c.drawString(MARGIN_INNER, y, line)
                y -= 14
                line = w
        if line:
            c.drawString(MARGIN_INNER, y, line)
            y -= 14
        y -= 8  # paragraph break


# ============================================================
# LIVRES PRÉ-CONFIGURÉS
# ============================================================

LOW_CONTENT_BOOKS = {
    "fishing_log": {
        "title": "The Angler's Log",
        "subtitle": "100 pages to record every catch, lure, and unforgettable spot",
        "author": "Daystone Press",
        "kdp_keywords": [
            "fishing log book", "angler journal", "fishing diary",
            "fisherman gift", "fishing record book",
            "outdoor adventure journal", "bass fishing log",
        ],
        "categories": ["Sports & Outdoors", "Fishing", "Hobbies"],
        "intro": [
            "Welcome to your personal fishing log. Every angler has stories. This journal helps you keep them organized — date, location, weather, lure, and the one that didn't get away.",
            "Use the structured fields on each page to capture the essentials. Leave notes for what worked, what didn't, and the conditions that made a memorable catch.",
            "Over time, patterns will emerge — your favorite spots in spring, the lures that consistently outperform, the moon phases that yield the biggest fish.",
        ],
        "page_fields": [
            ("Date", ""), ("Location", ""), ("Water type", ""),
            ("Weather", ""), ("Water temp", ""), ("Time of day", ""),
            ("Lure / Bait", ""), ("Technique", ""),
            ("Fish caught", ""), ("Weight / Length", ""),
            ("Released? / Kept?", ""),
        ],
        "lines_below": 8,
        "page_title": "Catch entry",
    },
    "bird_watching": {
        "title": "The Bird Watcher's Field Journal",
        "subtitle": "100 entries to record sightings, habits, and seasons",
        "author": "Daystone Press",
        "kdp_keywords": [
            "bird watching journal", "birding log", "ornithology notebook",
            "nature observation journal", "bird identification book",
            "wildlife journal", "birder gift",
        ],
        "categories": ["Nature & Outdoors", "Birds", "Hobbies"],
        "intro": [
            "Birding is patience rewarded. This journal turns each sighting into something more — a record you can return to, build upon, and share.",
            "Note the species, the time of day, the weather. Sketch a quick silhouette. Over the seasons, you'll build a personal field guide unique to your patch.",
            "Some of the best discoveries come from re-reading old entries and noticing a pattern you missed in the moment.",
        ],
        "page_fields": [
            ("Date", ""), ("Time of day", ""), ("Location", ""),
            ("Habitat", ""), ("Weather", ""),
            ("Species observed", ""), ("Number seen", ""),
            ("Plumage / Coloring", ""),
            ("Behavior", ""), ("Song / Call", ""),
            ("Camera / Sketch?", ""),
        ],
        "lines_below": 7,
        "page_title": "Sighting entry",
    },
    "crochet_tracker": {
        "title": "The Crochet Project Tracker",
        "subtitle": "100 projects organized — yarn, hooks, hours, and finishing touches",
        "author": "Daystone Press",
        "kdp_keywords": [
            "crochet project journal", "crochet notebook",
            "crocheter gift", "yarn craft journal",
            "knitting project log", "fiber arts notebook",
        ],
        "categories": ["Crafts & Hobbies", "Knitting & Crochet"],
        "intro": [
            "Every crochet project deserves a record. Yarn brand and dye lot, hook size, pattern source, and the hours actually spent.",
            "This journal helps you remember what worked — and avoid repeating the substitutions that didn't. Use the pages to track gifts, items for sale, and your own wardrobe.",
            "Filled-in pages become a portfolio of your fiber journey.",
        ],
        "page_fields": [
            ("Project name", ""), ("Started date", ""), ("Finished date", ""),
            ("Pattern / Designer", ""), ("Yarn brand & weight", ""),
            ("Color / Dye lot", ""), ("Hook size", ""),
            ("Gauge swatch?", ""), ("Total hours", ""),
            ("Recipient / For", ""), ("Difficulty 1-5", ""),
        ],
        "lines_below": 8,
        "page_title": "Project log",
    },
    "pet_health": {
        "title": "My Pet's Health Journal",
        "subtitle": "Track vet visits, vaccinations, food, and milestones for one beloved companion",
        "author": "Daystone Press",
        "kdp_keywords": [
            "pet health journal", "dog vaccination record",
            "cat medical book", "veterinary log",
            "pet care notebook", "puppy first year",
        ],
        "categories": ["Pets", "Pet Care", "Health"],
        "intro": [
            "This journal is your pet's medical companion. Every vet visit, every vaccination, every change in food or behavior — all captured here for you and any vet you may see in the future.",
            "Bring this journal to appointments. The structured fields help your veterinarian see your pet's full history at a glance.",
            "Beyond medical records, leave room for milestones: first walks, favorite toys, the moments that made you smile.",
        ],
        "page_fields": [
            ("Date", ""), ("Reason for visit", ""),
            ("Veterinarian", ""), ("Clinic", ""),
            ("Weight", ""), ("Temperature", ""),
            ("Vaccination given", ""), ("Medication prescribed", ""),
            ("Dosage / Schedule", ""), ("Next visit", ""),
        ],
        "lines_below": 8,
        "page_title": "Visit entry",
    },
    "sourdough_log": {
        "title": "The Sourdough Baker's Log",
        "subtitle": "100 bakes — flour, hydration, fold timing, crumb shots",
        "author": "Daystone Press",
        "kdp_keywords": [
            "sourdough journal", "bread baking log",
            "fermentation tracker", "artisan bread journal",
            "home baker gift", "sourdough starter book",
        ],
        "categories": ["Cooking", "Baking", "Hobbies"],
        "intro": [
            "Sourdough is science you can taste. This journal lets you record what worked, what flopped, and the variables that made the difference.",
            "Track flour brands, hydration percentages, fold timing, and proof temperatures. Note the weather — sourdough cares.",
            "Re-read old entries when a bake disappoints. Patterns reveal themselves over time.",
        ],
        "page_fields": [
            ("Date", ""), ("Flour brand & blend", ""),
            ("Hydration %", ""), ("Starter ratio / Levain", ""),
            ("Autolyse time", ""), ("Bulk ferment time / Temp", ""),
            ("Folds (count & timing)", ""), ("Shaping notes", ""),
            ("Cold retard time", ""), ("Oven temp / Time", ""),
            ("Crumb rating 1-10", ""),
        ],
        "lines_below": 6,
        "page_title": "Bake entry",
    },
    "dnd_campaign": {
        "title": "The Adventurer's Campaign Journal",
        "subtitle": "100 sessions for quests, loot, NPCs, and party shenanigans",
        "author": "Daystone Press",
        "kdp_keywords": [
            "dnd journal", "tabletop rpg notebook",
            "dungeon master log", "dnd campaign book",
            "rpg session notes", "ttrpg player journal",
        ],
        "categories": ["Games", "Tabletop Games", "Role-Playing Games"],
        "intro": [
            "Every campaign deserves a chronicler. Whether you're the DM, the rogue who pockets everything, or the bard who narrates every fight, this journal is your scroll.",
            "Sessions blur. Quests get tangled. NPCs return when you least expect. This book helps you remember who Glimnar the Tinkerer was and why your party owes him gold.",
            "Sketch maps. Doodle initials. The best campaign journals are part record, part artifact.",
        ],
        "page_fields": [
            ("Session #", ""), ("Date", ""), ("Location IRL", ""),
            ("In-game day / Date", ""), ("Campaign", ""),
            ("Party members present", ""),
            ("Key NPCs encountered", ""),
            ("Quest progress", ""), ("Loot acquired", ""),
            ("XP earned / Level up?", ""),
        ],
        "lines_below": 8,
        "page_title": "Session log",
    },
    "garden_planner": {
        "title": "The Gardener's Seasonal Planner",
        "subtitle": "100 entries to track sowings, harvests, and seasons of growth",
        "author": "Daystone Press",
        "kdp_keywords": [
            "gardening journal", "vegetable garden planner",
            "seed sowing book", "permaculture log",
            "harvest record book", "gardener gift journal",
        ],
        "categories": ["Gardening", "Home & Garden", "Hobbies"],
        "intro": [
            "Gardening rewards memory. What variety bolted in July? Which row got too much shade in August? This journal turns each season into reference for the next.",
            "Track sowings, transplant dates, harvest weights, and the unexpected pests you faced. Add weather observations and soil amendments.",
            "Year after year, your garden teaches you. This book helps you listen.",
        ],
        "page_fields": [
            ("Date", ""), ("Bed / Area", ""),
            ("Crop / Variety", ""), ("Source (seed company)", ""),
            ("Quantity sown / Spacing", ""),
            ("Germination date", ""), ("Transplant date", ""),
            ("Soil amendments", ""), ("Pest / Disease notes", ""),
            ("Harvest date / Weight", ""), ("Notes for next year", ""),
        ],
        "lines_below": 5,
        "page_title": "Crop entry",
    },
    "climbing_log": {
        "title": "The Climber's Ascent Log",
        "subtitle": "100 routes — grade, conditions, partners, and the send",
        "author": "Daystone Press",
        "kdp_keywords": [
            "climbing journal", "rock climbing log",
            "bouldering tracker", "mountaineering notebook",
            "climber gift", "alpine route log",
        ],
        "categories": ["Sports & Outdoors", "Climbing"],
        "intro": [
            "Climbing is a sport of marginal gains. Each attempt, each beta change, each rest — all of it accumulates.",
            "This journal records every route you touch. Grade, send/project, beta refinements, the partner who held your rope.",
            "Years from now you'll flip back and remember the day the rain came in halfway up the wall.",
        ],
        "page_fields": [
            ("Date", ""), ("Crag / Gym", ""),
            ("Route name", ""), ("Grade", ""),
            ("Style (lead/TR/boulder)", ""),
            ("Attempts", ""), ("Send / Project?", ""),
            ("Conditions", ""), ("Partner / Belayer", ""),
            ("Beta notes", ""),
        ],
        "lines_below": 7,
        "page_title": "Route entry",
    },
    "vinyl_collection": {
        "title": "The Vinyl Collector's Index",
        "subtitle": "100 records cataloged — pressing, condition, story",
        "author": "Daystone Press",
        "kdp_keywords": [
            "vinyl collection book", "record collector journal",
            "lp catalog notebook", "vinyl tracker",
            "music lover gift", "audiophile journal",
        ],
        "categories": ["Music", "Collecting"],
        "intro": [
            "Records are objects with histories. The pressing, the catalog number, the day you found it at the back of a dusty crate.",
            "This index turns your collection into a reference — useful when selling, lending, or showing off.",
            "Note condition, sleeve quirks, and the story of how each one came to you.",
        ],
        "page_fields": [
            ("Date added", ""), ("Artist", ""),
            ("Album title", ""), ("Year (original press)", ""),
            ("Pressing details", ""), ("Catalog #", ""),
            ("Genre", ""), ("Condition (sleeve)", ""),
            ("Condition (vinyl)", ""),
            ("Purchase price / Source", ""),
        ],
        "lines_below": 7,
        "page_title": "Record entry",
    },
    "brewing_log": {
        "title": "The Home Brewer's Log",
        "subtitle": "100 batches — recipes, fermentation, tasting notes",
        "author": "Daystone Press",
        "kdp_keywords": [
            "beer brewing journal", "homebrew log",
            "fermentation tracker", "brewing notebook",
            "craft beer journal", "homebrewer gift",
        ],
        "categories": ["Cooking", "Beer", "Hobbies"],
        "intro": [
            "Brewing is repeatable chemistry — when you keep notes. This journal lets you record OG, FG, mash temps, hop schedules, and tasting impressions.",
            "Track what works. Tweak one variable at a time. Over batches, your recipes refine themselves.",
            "Re-read past entries. The pattern you're looking for is in there.",
        ],
        "page_fields": [
            ("Brew date", ""), ("Recipe name / Style", ""),
            ("Batch size (L)", ""), ("OG / FG", ""),
            ("Grain bill", ""), ("Hops & additions", ""),
            ("Yeast & ferm. temp", ""), ("Fermentation time", ""),
            ("Bottling date", ""), ("Tasting notes (week 1/2/4)", ""),
        ],
        "lines_below": 6,
        "page_title": "Batch entry",
    },
}


def build_book(book_key: str, book: dict, pages_count: int) -> Path:
    book_dir = OUTPUT_DIR / book_key
    book_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = book_dir / f"{book_key}.pdf"

    c = pdf_canvas.Canvas(str(pdf_path), pagesize=(TRIM_W, TRIM_H))
    c.setTitle(book["title"])
    c.setAuthor(book["author"])
    c.setSubject(book["subtitle"])

    # Page 1 : titre
    draw_title_page(c, book["title"], book["subtitle"], book["author"])
    c.showPage()

    # Page 2 : intro / how to use
    draw_intro_page(c, book["intro"])
    c.showPage()

    # Pages 3 à N : entrées structurées
    for page_num in range(1, pages_count + 1):
        draw_lined_page(
            c, page_num,
            f"{book['page_title']} #{page_num:03d}",
            book["page_fields"],
            book["lines_below"],
        )
        draw_decorative_border(c, page_num)
        c.showPage()

    c.save()

    metadata = {
        "book_id": book_key,
        "title": book["title"],
        "subtitle": book["subtitle"],
        "author": book["author"],
        "pages_count": pages_count + 2,  # +title +intro
        "kdp_keywords": book["kdp_keywords"],
        "categories": book["categories"],
        "trim_size": "6 x 9 in",
        "interior_type": "black and white",
        "paper_type": "white paper",
        "binding": "paperback",
        "imprint": book["author"],
        "price_kdp_suggested": 7.99,
        "price_etsy_digital": 5.99,
        "production_method": "100% Python ReportLab + DejaVu fonts (no AI image)",
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    (book_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return pdf_path


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    book_key = os.environ.get("BOOK", "").strip().lower()
    pages = int(os.environ.get("PAGES") or "0") or 100

    if book_key and book_key not in LOW_CONTENT_BOOKS:
        print(f"Book inconnu. Choix : {list(LOW_CONTENT_BOOKS)}")
        return 2

    books = {book_key: LOW_CONTENT_BOOKS[book_key]} if book_key \
        else LOW_CONTENT_BOOKS

    print(f"=== LOW-CONTENT KDP — {len(books)} livre(s) × {pages} pages ===\n")

    for k, b in books.items():
        print(f"  → {b['title']}")
        pdf = build_book(k, b, pages)
        print(f"     PDF : {pdf}")

    print(f"\n  → {OUTPUT_DIR}")
    print(f"  Format : 6x9 inches paperback KDP-ready")
    print(f"  Upload : amazon.com/kdp → Create Paperback")
    return 0


if __name__ == "__main__":
    sys.exit(main())
