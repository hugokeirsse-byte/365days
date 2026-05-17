"""
Pinterest Descriptions Builder — pour chaque design dans products/,
génère un fichier pinterest_pin.txt avec description SEO + hashtags
prêt à copier-coller dans Pinterest.

Pinterest = principal canal de trafic GRATUIT vers Etsy. Une bonne
description = 3-10× plus de vues.

Aucune API requise. Templates intelligents + détection mood.

Pour chaque metadata.json, génère :
- Titre Pin (40-100 caractères, attention-grabbing)
- Description (250-500 caractères, SEO-rich)
- 8-12 hashtags ciblés
- Board suggéré (selon mood/niche)

Usage :
    python scripts/pinterest_descriptions_builder.py
    python scripts/pinterest_descriptions_builder.py --pipeline viral_formats
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"

# Templates par pipeline
PIN_TEMPLATES = {
    "cultural_arbitrage": {
        "title_template": "{word} — That untranslatable {lang} word you needed",
        "description_template": (
            "{word} is a beautiful {lang} word meaning {meaning}. "
            "This minimalist art print celebrates the gentle untranslatable "
            "beauty of language with elegant typography on neutral background. "
            "Perfect for booklovers, language learners, polyglots, and anyone "
            "who appreciates the words other languages have that English doesn't.\n\n"
            "💌 Instant digital download. Print at home or local shop.\n"
            "✨ Available in multiple sizes for gallery walls."
        ),
        "hashtags": [
            "#untranslatablewords", "#wordart", "#languagelover",
            "#linguisticgift", "#booktok", "#typographyposter",
            "#minimalistprint", "#wallart", "#bookishgift",
            "#polyglotlife", "#etsyfinds",
        ],
        "board": "Words & Wall Art",
    },
    "iheart": {
        "title_template": "I ❤️ {niche_label} — perfect {audience} gift",
        "description_template": (
            "Show your love for {niche_label_lower} with this gorgeous "
            "{variant_lower} print. Whether you're a passionate "
            "{audience} or shopping for someone who is, this is the "
            "kind of design that makes a small space feel like home. "
            "Print, frame, gift, or transfer to a tote bag, mug, or t-shirt.\n\n"
            "💌 Instant digital download. Multiple formats included."
        ),
        "hashtags": [
            "#ilove{slug_no_underscore}", "#{slug_no_underscore}gift",
            "#{slug_no_underscore}lover", "#wallartdecor", "#giftideas",
            "#tshirtdesign", "#redbubble", "#mugdesign",
            "#etsyfinds", "#instantdownload", "#homeart",
        ],
        "board": "Gift Prints",
    },
    "iheart_v2": {
        "title_template": "I ❤️ {niche_label} — scene inside heart art print",
        "description_template": (
            "A unique twist on the classic I ❤️ design — the scene "
            "of {niche_label_lower} lives INSIDE the heart itself. "
            "Beautifully illustrated with {style} style, this print is "
            "perfect for showing your love in a way that's actually original. "
            "Frame it, gift it, or transfer to any product.\n\n"
            "💌 Instant download."
        ),
        "hashtags": [
            "#ilove{slug_no_underscore}", "#sceneinheart",
            "#{slug_no_underscore}art", "#uniquegift", "#wallartdesign",
            "#illustration", "#giftforher", "#giftforhim",
            "#redbubble", "#etsy",
        ],
        "board": "Unique Gift Art",
    },
    "literal_idioms": {
        "title_template": "\"{literal}\" — funny {lang} idiom literal translation",
        "description_template": (
            "In {lang}, people actually say \"{original}\" — which "
            "literally translates to \"{literal}\". What it really means? "
            "{meaning}. Languages are wonderfully strange. This editorial "
            "print celebrates that strangeness with a literal illustration "
            "of the idiom. Perfect for language learners, polyglots, and "
            "anyone who's ever laughed at a translation.\n\n"
            "💌 Instant download."
        ),
        "hashtags": [
            "#funny{lang_no_space}idiom", "#languagelearning",
            "#polyglot", "#linguistics", "#languagegift",
            "#funnyprint", "#editorialart", "#languageteacher",
            "#translatorgift", "#etsy",
        ],
        "board": "Language & Idioms",
    },
    "viral_formats": {
        "title_template": "{format_text} — Funny {niche_label} Gift",
        "description_template": (
            "The kind of design that gets noticed. \"{format_text}\" — "
            "perfect for any {audience} who knows the struggle is real. "
            "Print, frame, gift, or transfer to tshirts, mugs, totes, "
            "stickers. Endless possibilities.\n\n"
            "💌 Instant digital download. Personal + small commercial "
            "use included."
        ),
        "hashtags": [
            "#{niche_no_underscore}humor", "#funnygift",
            "#{niche_no_underscore}gift", "#sarcastictshirt",
            "#wittyart", "#redbubble", "#etsy",
            "#tshirtdesign", "#mugdesign", "#stickerart",
        ],
        "board": "Funny Hobby Gifts",
    },
    "tumbler_wraps": {
        "title_template": "{title_subject} Tumbler Wrap PNG — Sublimation Design",
        "description_template": (
            "Ready-to-press 20oz straight tumbler wrap design — high "
            "resolution PNG at 300 DPI, prints sharp and vibrant on "
            "white polyester-coated tumblers. Sublimation creators, "
            "this is for you.\n\n"
            "💌 Instant download. Small commercial license included "
            "(up to 200 units)."
        ),
        "hashtags": [
            "#tumblerwrap", "#sublimationdesign", "#20oztumbler",
            "#sublimationpng", "#craftsupplies", "#sublimationblanks",
            "#tumblerdesign", "#sublimationart", "#etsysubliminater",
            "#instantdownload",
        ],
        "board": "Sublimation Designs",
    },
}


def slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def detect_pipeline(meta_path: Path) -> str:
    parts = meta_path.relative_to(PRODUCTS_DIR).parts
    return parts[0] if parts else ""


def build_values(metadata: dict, pipeline: str) -> dict:
    """Extrait/normalise les valeurs nécessaires aux templates."""
    v = {}
    if pipeline == "cultural_arbitrage":
        v["word"] = metadata.get("expression", "")
        v["lang"] = metadata.get("language", "").title()
        v["meaning"] = metadata.get("meaning", "")
    elif pipeline == "iheart":
        v["niche_label"] = metadata.get("niche_label", "")
        v["niche_label_lower"] = v["niche_label"].lower()
        v["audience"] = metadata.get("audience", "")
        v["variant"] = metadata.get("variant", "").replace("_", " ")
        v["variant_lower"] = v["variant"].lower()
        v["slug_no_underscore"] = slugify(metadata.get("niche", ""))
    elif pipeline == "iheart_v2":
        v["niche_label"] = metadata.get("niche_label", "")
        v["niche_label_lower"] = v["niche_label"].lower()
        v["audience"] = metadata.get("audience", "")
        v["style"] = metadata.get("style", "").replace("_", " ")
        v["slug_no_underscore"] = slugify(metadata.get("niche", ""))
    elif pipeline == "literal_idioms":
        v["original"] = metadata.get("original", "")
        v["literal"] = metadata.get("literal_translation", "")
        v["meaning"] = metadata.get("actual_meaning", "")
        v["lang"] = metadata.get("language", "").title()
        v["lang_no_space"] = slugify(metadata.get("language", ""))
    elif pipeline == "viral_formats":
        v["format_text"] = metadata.get("format_text", "")
        v["niche_label"] = metadata.get("niche_label", "")
        v["audience"] = metadata.get("audience", "")
        v["niche_no_underscore"] = slugify(metadata.get("niche", ""))
    elif pipeline == "tumbler_wraps":
        title = metadata.get("title", "")
        v["title_subject"] = title.split(" Tumbler ")[0]
    return v


def safe_format(template: str, values: dict) -> str:
    """Format en ignorant les placeholders manquants."""
    class SafeDict(dict):
        def __missing__(self, key):
            return f"{{{key}}}"
    return template.format_map(SafeDict(**values))


def build_pin(meta_path: Path) -> bool:
    metadata = json.loads(meta_path.read_text())
    pipeline = detect_pipeline(meta_path)
    template = PIN_TEMPLATES.get(pipeline)
    if not template:
        return False
    values = build_values(metadata, pipeline)
    title = safe_format(template["title_template"], values)
    description = safe_format(template["description_template"], values)
    hashtags = [safe_format(h, values) for h in template["hashtags"]]
    hashtags_str = " ".join(hashtags)

    content = (
        "=" * 70 + "\n"
        "PINTEREST PIN — copie-colle dans Pinterest\n"
        + "=" * 70 + "\n\n"
        "TITLE (max 100 caractères) :\n"
        f"{title[:100]}\n\n"
        + "-" * 70 + "\n"
        "DESCRIPTION (250-500 caractères) :\n"
        + "-" * 70 + "\n\n"
        f"{description}\n\n"
        + "-" * 70 + "\n"
        "HASHTAGS (à mettre EN PLUS dans la description ou dans les commentaires) :\n"
        + "-" * 70 + "\n\n"
        f"{hashtags_str}\n\n"
        + "-" * 70 + "\n"
        "BOARD SUGGÉRÉ :\n"
        + "-" * 70 + "\n\n"
        f"{template['board']}\n\n"
        + "-" * 70 + "\n"
        "PIN IMAGE :\n"
        + "-" * 70 + "\n\n"
        f"Utilise etsy_preview.jpg (1080×1080) ou print_3000.png (3000×3000)\n"
        f"Pour Pinterest, format VERTICAL 2:3 idéal (1000×1500).\n"
        f"Si pas dispo, le 1080×1080 marche très bien aussi.\n\n"
        "LIEN OUTBOUND :\n"
        f"→ Ton listing Etsy correspondant\n"
    )

    dest = meta_path.parent / "pinterest_pin.txt"
    dest.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline", default="")
    args = parser.parse_args()

    if not PRODUCTS_DIR.exists():
        print(f"✗ {PRODUCTS_DIR} inexistant")
        return 1

    scan = [PRODUCTS_DIR / args.pipeline] if args.pipeline \
        else list(PRODUCTS_DIR.iterdir())

    built = skipped = 0
    for sd in scan:
        if not sd.is_dir():
            continue
        for meta in sd.rglob("metadata.json"):
            if build_pin(meta):
                built += 1
            else:
                skipped += 1

    print(f"✓ {built} pinterest_pin.txt générés")
    if skipped:
        print(f"  ({skipped} skipped — pipeline non templaté)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
