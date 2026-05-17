"""
Etsy Listings Builder — génère des descriptions complètes Etsy à partir des
metadata.json produits par les pipelines.

Pour chaque design dans products/, génère un fichier listing_etsy.txt prêt
à copier-coller dans l'éditeur Etsy. Contient :
- Titre optimisé SEO
- Description longue (intro + 3-5 bullet points + use cases + closing)
- Tags séparés par virgules
- Reminder « files included »

Aucune clé API requise. Templates intelligents par type de produit.

Usage :
    python scripts/etsy_listings_builder.py                  # tous les pipelines
    python scripts/etsy_listings_builder.py --pipeline iheart
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"

# Patterns de description par catégorie de pipeline
DESCRIPTION_TEMPLATES = {
    "cultural_arbitrage": (
        "✨ {word} — a {lang_title} word that captures {short_meaning}\n\n"
        "There are some words that no language can translate perfectly — and "
        "{word} is one of them. This {format_name} celebrates that gentle "
        "untranslatable beauty with elegant typography you'll love to live with.\n\n"
        "✦ INSTANT DIGITAL DOWNLOAD ✦\n"
        "Print at home or at your local print shop — your file is ready as soon as you check out.\n\n"
        "🎨 WHAT YOU GET\n"
        "• High-resolution PNG (3000×3000 px @ 300 DPI)\n"
        "• Sharp on prints from 8×8 inches all the way to 24×24 inches\n"
        "• Squared format perfect for gallery walls and minimalist decor\n\n"
        "💡 PERFECT FOR\n"
        "• Cozy reading corners and bookshelves\n"
        "• Language learners, polyglots, language teachers\n"
        "• Gift for a friend who loves words and {lang_title} culture\n"
        "• Minimalist apartments and Scandinavian-inspired interiors\n\n"
        "📝 ABOUT THE WORD\n"
        "{word} ({lang_title}, {class_short}) — {meaning_long}\n\n"
        "🔖 LICENSE\n"
        "Personal use only. Print as many copies as you'd like for yourself "
        "and as gifts. Please do not resell the file or printed copies.\n\n"
        "💌 QUESTIONS?\n"
        "Send a message — I love helping you find the right print for your space."
    ),
    "iheart": (
        "❤️ I Love {niche_label} — {variant_name} edition\n\n"
        "Wear your passion for {niche_label_lower} with a design that feels "
        "both modern and timeless. This {variant_name_lower} print pairs a "
        "soft illustrated background with bold typography for a piece that "
        "stops eyes (in a good way).\n\n"
        "✦ INSTANT DIGITAL DOWNLOAD ✦\n\n"
        "🎨 FILES INCLUDED\n"
        "• Square print 3000×3000 px @ 300 DPI (wall art ready)\n"
        "• T-shirt-ready 2400×3000 px portrait (Printful safe area)\n"
        "• Etsy preview 1080×1080 px for social sharing\n\n"
        "💡 PERFECT FOR\n"
        "• {audience_title}\n"
        "• Custom t-shirt or hoodie printing (Printful, Printify, Gelato)\n"
        "• Mugs, tote bags, stickers, phone cases\n"
        "• Birthday and holiday gifts for someone who loves {niche_label_lower}\n\n"
        "🔖 LICENSE\n"
        "Personal use plus small commercial use (up to 100 printed items). "
        "Please do not resell the digital file as-is.\n\n"
        "💌 If you make something cool with this, tag me — I love seeing it!"
    ),
    "literal_idioms": (
        "🌍 \"{literal_translation}\" — a beautifully weird idiom from {lang_title}\n\n"
        "In {lang_title}, people actually say \"{original}\" — which LITERALLY "
        "translates to \"{literal_translation}\". What it really means? \"{meaning}\". "
        "Languages are wonderfully strange.\n\n"
        "This editorial print celebrates that strangeness with a literal "
        "illustration of the phrase — the kind of art that makes language nerds "
        "smile every time they walk past it.\n\n"
        "✦ INSTANT DIGITAL DOWNLOAD ✦\n\n"
        "🎨 FILES\n"
        "• High-resolution PNG 3000×3000 px @ 300 DPI\n"
        "• Square format perfect for framing\n\n"
        "💡 PERFECT FOR\n"
        "• {lang_title} language students and teachers\n"
        "• Polyglots and linguistics nerds\n"
        "• Translators, interpreters, language podcasters\n"
        "• Anyone who's ever laughed at a literal translation\n\n"
        "📚 ABOUT THE IDIOM\n"
        "Original: {original}\n"
        "Literal: {literal_translation}\n"
        "Meaning: {meaning}\n\n"
        "🔖 LICENSE\n"
        "Personal use only. Print as many copies as you'd like for yourself "
        "or as gifts. Please do not resell."
    ),
    "tumbler_wraps": (
        "🥤 {title_subject} — 20oz Sublimation Tumbler Wrap\n\n"
        "Ready-to-press sublimation design for your 20oz straight tumbler. "
        "High-resolution PNG, sharp every time, vibrant colors on white "
        "polyester-coated blanks.\n\n"
        "✦ INSTANT DIGITAL DOWNLOAD ✦\n\n"
        "🎨 FILE SPECS\n"
        "• 9.3 × 8.3 inches @ 300 DPI\n"
        "• PNG format, ready to print\n"
        "• Compatible with all 20oz straight skinny tumblers\n\n"
        "💡 PERFECT FOR\n"
        "• Small business owners doing sublimation\n"
        "• Personalized gift makers\n"
        "• Craft fair sellers\n\n"
        "🔖 LICENSE\n"
        "Small commercial use OK (sell finished tumblers, up to 200 units). "
        "Do not resell the digital design itself."
    ),
}

# Champs requis par pipeline pour formatter le template
PIPELINE_FIELD_MAP = {
    "cultural_arbitrage": {
        "word": "expression",
        "lang_title": ("language", str.title),
        "format_name": "format",
        "meaning_long": "meaning",
        "short_meaning": ("meaning", lambda s: s.split(",")[0]),
        "class_short": ("title", lambda s: ""),  # fallback
    },
    "iheart": {
        "niche_label": "niche_label",
        "niche_label_lower": ("niche_label", str.lower),
        "variant_name": ("variant", lambda s: s.replace("_", " ").title()),
        "variant_name_lower": ("variant", lambda s: s.replace("_", " ").lower()),
        "audience_title": ("audience", str.title),
    },
    "literal_idioms": {
        "original": "original",
        "literal_translation": "literal_translation",
        "meaning": "actual_meaning",
        "lang_title": ("language", str.title),
    },
    "tumbler_wraps": {
        "title_subject": ("title", lambda s: s.split(" Tumbler ")[0]),
    },
}


def detect_pipeline(metadata_path: Path) -> str:
    """Détecte la pipeline depuis le chemin (products/PIPELINE/...)."""
    parts = metadata_path.relative_to(PRODUCTS_DIR).parts
    if not parts:
        return ""
    return parts[0]


def extract_field(metadata: dict, spec) -> str:
    if isinstance(spec, str):
        return str(metadata.get(spec, ""))
    if isinstance(spec, tuple):
        key, transform = spec
        return transform(metadata.get(key, ""))
    return ""


def build_description(metadata: dict, pipeline: str) -> str | None:
    template = DESCRIPTION_TEMPLATES.get(pipeline)
    if not template:
        return None
    field_map = PIPELINE_FIELD_MAP.get(pipeline, {})
    values = {}
    for placeholder, spec in field_map.items():
        try:
            values[placeholder] = extract_field(metadata, spec)
        except Exception:  # noqa: BLE001
            values[placeholder] = ""
    try:
        return template.format(**values)
    except KeyError as e:
        return f"[Template incomplete : {e}]"


def build_listing(metadata_path: Path) -> bool:
    metadata = json.loads(metadata_path.read_text())
    pipeline = detect_pipeline(metadata_path)
    description = build_description(metadata, pipeline)
    if not description:
        # Fallback : si le metadata contient déjà une description (cope_pack, etc.)
        existing = metadata.get("description", "")
        if existing:
            description = existing
        else:
            return False

    title = metadata.get("title", "Untitled")
    tags = metadata.get("tags_etsy", "")
    price = metadata.get("price_etsy", "")
    files = metadata.get("files_included", "high resolution digital files")

    listing = (
        "=" * 70 + "\n"
        "ETSY LISTING — copie-colle dans Add a Listing\n"
        + "=" * 70 + "\n\n"
        "TITRE (max 140 caractères Etsy) :\n"
        f"{title}\n\n"
        + "-" * 70 + "\n"
        "DESCRIPTION :\n"
        + "-" * 70 + "\n\n"
        f"{description}\n\n"
        + "-" * 70 + "\n"
        "TAGS (13 max, séparés par virgules) :\n"
        + "-" * 70 + "\n\n"
        f"{tags}\n\n"
        + "-" * 70 + "\n"
        "PRIX :\n"
        + "-" * 70 + "\n\n"
        f"{price} €\n\n"
        + "-" * 70 + "\n"
        "FICHIERS À UPLOAD (Add files) :\n"
        + "-" * 70 + "\n\n"
        f"{files}\n\n"
        + "-" * 70 + "\n"
        "TYPE DE LISTING : Digital download (instant)\n"
        "CATEGORIE : Art & Collectibles → Prints (ou catégorie pertinente)\n"
    )

    dest = metadata_path.parent / "listing_etsy.txt"
    dest.write_text(listing, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline", default="",
                        help="Pipeline (ex: cultural_arbitrage). Vide = tous.")
    args = parser.parse_args()

    if not PRODUCTS_DIR.exists():
        print(f"✗ {PRODUCTS_DIR} inexistant — lance d'abord un pipeline.")
        return 1

    scan_dirs = (
        [PRODUCTS_DIR / args.pipeline] if args.pipeline
        else list(PRODUCTS_DIR.iterdir())
    )

    built = 0
    skipped = 0
    for sd in scan_dirs:
        if not sd.is_dir():
            continue
        for meta in sd.rglob("metadata.json"):
            if build_listing(meta):
                built += 1
            else:
                skipped += 1

    print(f"✓ {built} listings Etsy générés (listing_etsy.txt)")
    if skipped:
        print(f"  ({skipped} skipped — pipeline non templaté)")
    print(f"\nProchaine étape : pour chaque dossier, ouvre listing_etsy.txt et")
    print(f"copie-colle son contenu dans le formulaire Etsy 'Add a Listing'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
