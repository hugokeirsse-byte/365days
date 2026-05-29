"""
Pipeline COLORING BOOK triple-trend — KDP-ready.

Génère un livre de coloriage 30 pages prêt pour KDP, basé sur la
formule TRIPLE TREND :
  style générique (cute kawaii line art)
  × niche choisie (mushrooms, mystical animals, dragons, plants…)
  × event upcoming (Halloween, Christmas, Mother's Day…) — optionnel

Pollinations Flux génère le line art (fond blanc, traits noirs épais).
PIL nettoie l'image (force le contraste pour des traits propres).
ReportLab assemble en PDF KDP-ready (8.5×11", marges KDP 0.75").

Format KDP standard :
- Trim size : 8.5 × 11 inch (US Letter)
- Bleed : 0.125" (on génère 8.625 × 11.125)
- Marge intérieure : 0.75" (gutter), extérieure 0.5"
- Format final : PDF/X-1a compatible

Variables d'env :
  NICHE=mystical_mushrooms     niche du livre (clé de NICHES)
  PAGES=30                     nombre de pages (par défaut 30)
  EVENT_KEY=halloween          optionnel, ajoute un event au croisement
"""

import json
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("ERREUR : Pillow non installé")
    sys.exit(2)

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
except ImportError:
    print("ERREUR : reportlab non installé. pip install reportlab")
    sys.exit(2)


# === PIPELINE EN PAUSE ===
# Pollinations rend des résultats trop variables pour ce pipeline.
# Réactiver dès que HF_API_KEY est dispo (script produce_iheart_hf.py).
# Cf. STRATEGY.md section "Pipelines EN PAUSE".
import os as _os
if not (_os.environ.get('HF_API_KEY') or _os.environ.get('FORCE_RUN') == '1'):
    print('⏸ PAUSED : ni HF_API_KEY ni FORCE_RUN=1. Configure HF_API_KEY pour produire en qualité HF.')
    raise SystemExit(0)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "coloring_books"
USER_AGENT = "ColoringBookProducer/1.0"
TIMEOUT = 240

# Style de base = cute kawaii line art (sans copier coco wyo : adultes,
# pas pour enfants, traits épais propres, fond pur blanc)
STYLE_BASE = (
    "adult coloring book page, clean BOLD black outline line art ONLY, "
    "uniform thick vector-style outlines on pure white background, "
    "closed simple shapes ready to color, flat clean cartoon style, "
    "absolutely NO shading, NO grey, NO hatching, NO crosshatching, "
    "NO sketch lines, NO pencil texture, NO fill, NO color, "
    "cute kawaii style with rounded shapes and large expressive eyes, "
    "with simple whimsical decorative background scenery around the subject, "
    "professional coloring book quality, no text no watermark"
)

# Niches à fort potentiel KDP, classées par marché identifié
NICHES = {
    "mystical_mushrooms": {
        "title": "Mystical Mushrooms",
        "subtitle": "30 Magical Mushroom Coloring Pages for Adults",
        "description": "Step into an enchanted forest of fly agarics, fairy rings, and whimsical fungi cottages. 30 detailed coloring pages perfect for stress relief and mindful creativity.",
        "kdp_keywords": [
            "mushroom coloring book adults",
            "mystical mushroom art therapy",
            "cottagecore coloring book",
            "fungi illustration coloring",
            "whimsical forest coloring book",
            "fairy mushroom coloring",
            "kawaii mushroom adult coloring",
        ],
        "categories": ["Adult Coloring Books", "Cottagecore", "Botanical Coloring"],
        "subjects": [
            "fly agaric mushroom with stars and moons floating around",
            "fairy ring of mushrooms with small fairy door",
            "tiny mushroom cottage with smoking chimney",
            "stacked mushrooms forming a tower",
            "mushroom holding an umbrella in the rain",
            "mushroom couple having tea together",
            "owl perched on giant mushroom",
            "snail with mushroom hat on its shell",
            "mushroom wearing witch hat",
            "mushroom garden with bees and butterflies",
            "mushroom carrying lantern at night",
            "mushroom reading book by candlelight",
            "giant mushroom with tiny door and windows like a fairy house",
            "mushroom dancing with leaves",
            "mushroom riding tiny snail",
            "mushroom with ladybug friend",
            "field of mushrooms with crescent moon above",
            "mushroom inside crystal ball",
            "mushroom with butterfly wings",
            "mushroom sleeping under leaf blanket",
            "mushroom with constellation pattern on cap",
            "old wise mushroom with beard and walking stick",
            "mushroom baker with apron and bread",
            "mushroom holding ornate magic key",
            "mushroom with sunflower companion",
            "kitten curled up between mushrooms",
            "frog sitting on mushroom playing tiny flute",
            "mushroom with vines and grapes climbing on it",
            "winter mushroom in snow with pine cones",
            "mushroom emerging from book pages",
        ],
    },
    "mystical_creatures": {
        "title": "Mystical Creatures",
        "subtitle": "30 Whimsical Magical Animal Coloring Pages",
        "description": "Dragons, unicorns, phoenixes and tiny mystical creatures from forgotten folklore. 30 enchanting line art pages for adult coloring meditation.",
        "kdp_keywords": [
            "mystical creatures coloring book",
            "dragon coloring book adults",
            "unicorn fantasy coloring",
            "magical creatures coloring",
            "folklore creatures coloring book",
            "fantasy adult coloring book",
            "mythical animals coloring",
        ],
        "categories": ["Adult Coloring Books", "Fantasy Coloring", "Mythology"],
        "subjects": [
            "cute baby dragon curled up with crystal",
            "tiny unicorn in flower meadow",
            "phoenix rising from flames in elegant pose",
            "kitsune fox with multiple tails sitting peacefully",
            "small griffin with feathers and paws",
            "cute mermaid with seashell jewelry",
            "fairy with ornate wings holding lantern",
            "tiny gnome with pointed hat reading book",
            "celtic hare with knotwork patterns",
            "wood nymph emerging from tree",
            "cute kelpie horse in lake",
            "small selkie seal pup",
            "miniature pegasus among clouds",
            "tiny basilisk peeking from herbs",
            "moon rabbit on crescent moon",
            "lucky cat with bell and ribbon",
            "tiny dragon hatching from ornate egg",
            "garden gnome tending mushroom",
            "fairy door in tree trunk",
            "tiny phoenix in nest",
            "small wyvern with delicate wings",
            "cute kraken with friendly tentacles",
            "snow leopard with magical aurora",
            "celestial dragon among stars",
            "spirit deer with antlers full of flowers",
            "cute centaur young foal",
            "tiny familiar cat with witch hat",
            "small water spirit with ripples",
            "cherub holding heart",
            "wise tortoise with moss and herbs on shell",
        ],
    },
    "fairy_cottages": {
        "title": "Fairy Cottages",
        "subtitle": "30 Whimsical Cottagecore Houses Coloring Pages",
        "description": "Tiny enchanted cottages hidden in mushroom groves, treetop houses, and cozy garden retreats. Cottagecore coloring book for stress relief.",
        "kdp_keywords": [
            "cottagecore coloring book",
            "fairy houses coloring book",
            "whimsical cottage coloring",
            "tiny house coloring book adults",
            "fairy tale coloring book",
            "magical cottages coloring",
            "garden cottage coloring book",
        ],
        "categories": ["Adult Coloring Books", "Cottagecore", "Architecture"],
        "subjects": [
            "tiny mushroom cottage with chimney and round door",
            "treetop fairy house with rope ladder",
            "pumpkin cottage with windows and curtains",
            "teacup turned into miniature house",
            "cottage built inside hollow tree stump",
            "snail shell as cozy home with windows",
            "tiny cottage on giant flower",
            "cottage built inside open book",
            "garden gnome cottage with vegetable garden",
            "fairy lantern as glowing tiny home",
            "boot turned into cozy cottage",
            "underground burrow cottage with skylight window",
            "floating cloud cottage",
            "shell cottage on beach",
            "cottage built into giant pumpkin patch",
            "cottage inside hollowed acorn",
            "watering can converted to fairy cottage",
            "treasure chest fairy cottage opened",
            "music box cottage with tiny door",
            "kettle cottage with steam chimney",
            "birdhouse luxurious fairy cottage",
            "tiny cottage built on lily pad",
            "rooftop garden cottage with flowers everywhere",
            "winter cottage with snow and icicles",
            "spring cottage covered in cherry blossoms",
            "lighthouse cottage on tiny island",
            "windmill miniature with cozy interior",
            "moon-shaped cottage among stars",
            "rainbow cottage at end of arch",
            "library cottage filled with books",
        ],
    },
}

# Events permettant de teinter le livre (optionnel)
EVENTS_OVERLAY = {
    "halloween": "with halloween touches like pumpkins black cats witches hats and crescent moons",
    "christmas": "with christmas touches like pine cones snow ornaments and ribbons",
    "mothers_day": "with romantic floral touches roses ribbons and hearts",
    "valentines": "with valentine touches like hearts roses and ribbons",
    "spring": "with spring touches like cherry blossoms birds and butterflies",
    "autumn": "with autumn touches like maple leaves acorns and pumpkins",
}


def pollinations_url(prompt: str, seed: int, width: int = 1280, height: int = 1664) -> str:
    """Format portrait 5:6.5 pour respecter le ratio US Letter."""
    encoded = urllib.parse.quote(prompt, safe="")
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?model=flux&width={width}&height={height}"
        f"&seed={seed}&nologo=true&private=true&enhance=true"
    )


def http_get(url: str, dest: Path, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
            if len(data) < 5000:
                raise ValueError(f"too short {len(data)}")
            dest.write_bytes(data)
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"    retry {attempt + 1}/{retries} : {exc}")
            time.sleep(8 + attempt * 6)
    return False


def clean_line_art(src: Path, dest: Path) -> None:
    """Force contraste maximal pour traits noirs purs sur fond blanc.

    Convertit en niveaux de gris, applique seuil pour éliminer le gris
    parasite, repasse en RGB pour PDF.
    """
    img = Image.open(src).convert("L")
    # Auto-contrast pour étirer la dynamique
    img = ImageOps.autocontrast(img, cutoff=2)
    # Seuil binaire : tout ce qui est <140 devient noir, le reste blanc
    img = img.point(lambda px: 0 if px < 140 else 255, mode="L")
    img.convert("RGB").save(dest, "PNG", optimize=True)


def produce_page(niche_key: str, niche: dict, subject: str, page_num: int,
                  event_overlay: str, book_dir: Path) -> Path | None:
    page_dir = book_dir / "pages"
    page_dir.mkdir(parents=True, exist_ok=True)
    raw = page_dir / f"page_{page_num:02d}_raw.png"
    clean = page_dir / f"page_{page_num:02d}.png"

    if clean.exists():
        print(f"  [{page_num:>2}] (déjà existe) {subject[:50]}")
        return clean

    prompt = f"{STYLE_BASE}, subject is {subject}"
    if event_overlay:
        prompt += f", {event_overlay}"
    seed = page_num * 10037 + random.randint(0, 9999)

    print(f"  [{page_num:>2}] {subject[:55]}")
    # Qualité d'abord : HF Inference (SDXL, + style ref si dispo).
    # Fallback Pollinations automatique si HF_API_KEY absent ou échec.
    neg = "color, shading, grayscale, gray tones, text, watermark, signature, blurry, deformed"
    img_bytes = None
    try:
        from lib.hf_image_generator import get_image_for_pipeline
        img_bytes = get_image_for_pipeline(
            prompt, "coloring_books", niche_key,
            width=1280, height=1664, negative_prompt=neg)
    except Exception as exc:  # noqa: BLE001
        print(f"        HF indisponible ({exc}) -> fallback Pollinations")
    if img_bytes:
        raw.write_bytes(img_bytes)
        print("        ✓ HF")
    else:
        url = pollinations_url(prompt, seed)
        if not http_get(url, raw):
            print("        echec Pollinations")
            return None
    try:
        clean_line_art(raw, clean)
    except Exception as exc:  # noqa: BLE001
        print(f"        nettoyage echoue : {exc}")
        return None
    finally:
        if raw.exists():
            raw.unlink()
    return clean


def assemble_pdf(book_dir: Path, niche: dict, pages: list[Path], event_key: str) -> Path:
    """Assemble les pages en PDF KDP-ready (8.5×11", marges 0.75")."""
    pdf_path = book_dir / f"{book_dir.name}.pdf"
    page_w, page_h = letter  # 612 × 792 pt
    margin_top = 0.5 * inch
    margin_bottom = 0.5 * inch
    margin_inner = 0.75 * inch  # KDP gutter
    margin_outer = 0.5 * inch

    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.setTitle(niche["title"])
    c.setAuthor("Daystone Press")
    c.setSubject(niche["subtitle"])

    # Page de titre
    c.setFont("Helvetica-Bold", 28)
    title_y = page_h / 2 + 40
    c.drawCentredString(page_w / 2, title_y, niche["title"])
    c.setFont("Helvetica", 14)
    c.drawCentredString(page_w / 2, title_y - 30, niche["subtitle"])
    if event_key:
        c.setFont("Helvetica-Oblique", 11)
        c.drawCentredString(page_w / 2, title_y - 55,
                            f"Special {event_key.title()} edition")
    c.setFont("Helvetica", 10)
    c.drawCentredString(page_w / 2, 60, "Daystone Press")
    c.showPage()

    # Pages d'illustrations : alternance recto/verso → gutter alterne
    for i, page_path in enumerate(pages, 1):
        # Page impaire = recto = gutter à gauche
        if i % 2 == 1:
            left = margin_inner
            right = margin_outer
        else:
            left = margin_outer
            right = margin_inner
        avail_w = page_w - left - right
        avail_h = page_h - margin_top - margin_bottom

        try:
            img = ImageReader(str(page_path))
            iw, ih = img.getSize()
            scale = min(avail_w / iw, avail_h / ih)
            draw_w = iw * scale
            draw_h = ih * scale
            x = left + (avail_w - draw_w) / 2
            y = margin_bottom + (avail_h - draw_h) / 2
            c.drawImage(img, x, y, width=draw_w, height=draw_h,
                        preserveAspectRatio=True, mask="auto")
            # Numéro de page discret
            c.setFont("Helvetica", 8)
            c.setFillGray(0.6)
            c.drawCentredString(page_w / 2, 25, str(i))
            c.setFillGray(0)
        except Exception as exc:  # noqa: BLE001
            print(f"    PDF page {i} skip : {exc}")
        c.showPage()

    c.save()
    return pdf_path


def slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def main() -> int:
    niche_key = os.environ.get("NICHE", "mystical_mushrooms").strip()
    if niche_key not in NICHES:
        print(f"Niche inconnue. Choix : {list(NICHES)}")
        return 2
    niche = NICHES[niche_key]
    pages_count = int(os.environ.get("PAGES") or "30")
    pages_count = min(pages_count, len(niche["subjects"]))
    event_key = os.environ.get("EVENT_KEY", "").strip().lower()
    event_overlay = EVENTS_OVERLAY.get(event_key, "") if event_key else ""

    book_id = niche_key + (f"_{event_key}" if event_key else "")
    book_dir = OUTPUT_DIR / book_id
    book_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== COLORING BOOK : {niche['title']} ({pages_count} pages) ===")
    if event_overlay:
        print(f"    overlay event : {event_key}")
    print()

    generated = []
    for i, subject in enumerate(niche["subjects"][:pages_count], 1):
        page = produce_page(niche_key, niche, subject, i, event_overlay, book_dir)
        if page:
            generated.append(page)
        time.sleep(2)

    if len(generated) < 5:
        print(f"\n✗ Trop peu de pages générées ({len(generated)}). Abort PDF.")
        return 1

    print(f"\n  → {len(generated)}/{pages_count} pages OK, assembly PDF…")
    pdf_path = assemble_pdf(book_dir, niche, generated, event_key)
    print(f"  → PDF : {pdf_path}")

    metadata = {
        "book_id": book_id,
        "niche_key": niche_key,
        "title": niche["title"],
        "subtitle": niche["subtitle"],
        "description": niche["description"],
        "event_overlay": event_key or None,
        "pages_count": len(generated),
        "kdp_keywords": niche["kdp_keywords"],
        "categories": niche["categories"],
        "price_kdp": 7.99,
        "price_etsy_digital": 9.99,
        "trim_size": "8.5 x 11 in",
        "interior_type": "black and white",
        "paper_type": "white paper",
        "binding": "paperback",
        "imprint": "Daystone Press",
    }
    (book_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    print(f"  → metadata : {book_dir / 'metadata.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
