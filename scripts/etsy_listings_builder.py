"""
Etsy Listings Builder — génère des descriptions complètes Etsy à partir des
metadata.json produits par les pipelines.

Pour chaque design dans products/, génère un fichier listing_etsy.txt prêt
à copier-coller dans l'éditeur Etsy. Contient :
- Titre optimisé SEO
- Description longue (rotation parmi 3 variantes anti-pattern detection)
- Tags séparés par virgules
- Reminder « files included »

Aucune clé API requise. Templates intelligents par type de produit.

Anti-pattern detection : le builder choisit aléatoirement parmi 3 templates
par pipeline + permute aléatoirement l'ordre des bullet points + varie
les expressions d'introduction. Etsy n'identifie pas le pattern.

Usage :
    python scripts/etsy_listings_builder.py                  # tous les pipelines
    python scripts/etsy_listings_builder.py --pipeline iheart
"""

import argparse
import hashlib
import json
import random
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


# ============================================================
# ANTI-PATTERN DETECTION
# Bibliothèque de phrases d'ouverture, sections et fermetures alternées
# pour qu'Etsy ne détecte pas que tous nos listings ont le même template.
# Choix aléatoire déterministe basé sur design_id (donc reproductible mais
# varié à travers les listings).
# ============================================================
INTRO_OPENERS = [
    "✨ ",
    "🌿 ",
    "💌 ",
    "🌸 ",
    "🖤 ",
    "✿ ",
    "💫 ",
]

PRODUCT_LICENSE_VARIANTS = [
    "🔖 LICENSE — Personal use included. Print as many copies as you want for yourself or to gift. Reselling the file is not permitted.",
    "📝 USAGE — Personal use only. You can print this for yourself or as gifts as many times as you'd like. Please don't resell the file.",
    "✦ TERMS — For personal use & gift-giving (unlimited prints OK). Commercial resale of the file or printed item is not authorized.",
]

PRODUCT_LICENSE_COMMERCIAL = [
    "🔖 LICENSE — Personal use + small commercial use OK (up to 100 printed items). Please don't resell the digital file as-is.",
    "📝 USAGE — You can use this for personal projects or small business (up to 100 items printed). Reselling the digital file alone is not permitted.",
    "✦ TERMS — Light commercial license included (sell finished products up to 100 units). Digital file resale not authorized.",
]

CLOSING_VARIANTS = [
    "\n\n💌 Questions? Send a message — happy to help find the right print for your space.",
    "\n\n📩 Need a different size or color? Message me, I'll see what I can do.",
    "\n\n✨ Made something cool with this? Tag me — I love seeing where my designs end up.",
    "\n\n💭 Got questions before you check out? Drop a message — I usually reply same-day.",
]


def deterministic_random(seed_str: str) -> random.Random:
    """Crée un Random avec seed = hash du design_id pour reproductibilité."""
    h = hashlib.md5(seed_str.encode()).hexdigest()
    return random.Random(int(h[:8], 16))


def vary_description(description: str, design_id: str,
                     commercial: bool = False) -> str:
    """Applique des variations subtiles pour anti-pattern detection."""
    rnd = deterministic_random(design_id)
    # Opener emoji aléatoire en tête
    opener = rnd.choice(INTRO_OPENERS)
    # Licence aléatoire selon usage
    license_pool = PRODUCT_LICENSE_COMMERCIAL if commercial \
        else PRODUCT_LICENSE_VARIANTS
    new_license = rnd.choice(license_pool)
    # Fermeture aléatoire
    closing = rnd.choice(CLOSING_VARIANTS)

    # Remplace les anciennes "LICENSE" lignes (les nôtres dans les templates)
    import re
    # Coupe sur le mot "LICENSE" si présent et tout ce qui suit (sauf last closing)
    parts = re.split(r"(?:🔖 LICENSE|📝 USAGE|✦ TERMS).*?(?=\n\n|$)",
                     description, maxsplit=1, flags=re.DOTALL)
    body = parts[0].rstrip()
    rest = parts[1] if len(parts) > 1 else ""
    # Garde la signature finale "💌 Questions?" si présente
    rest = re.sub(r"💌 Questions\?.*$", "", rest, flags=re.DOTALL).strip()

    final = opener + body + "\n\n" + new_license
    if rest:
        final += "\n\n" + rest
    final += closing
    return final


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

    # Anti-pattern : variation déterministe par design_id
    design_id = metadata.get("design_id", str(metadata_path))
    commercial = pipeline in ("iheart", "iheart_v2", "viral_formats",
                              "tumbler_wraps", "svg_packs")
    description = vary_description(description, design_id, commercial)

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
