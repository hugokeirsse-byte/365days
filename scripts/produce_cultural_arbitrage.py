"""
Pipeline CULTURAL ARBITRAGE — merch des expressions intraduisibles.

Génère des designs typographiques pour 30+ expressions étrangères
(Hygge, Ikigai, Saudade, Wabi-sabi, La Dolce Vita…) déclinées en
plusieurs formats :
  1. Typo pure (minimaliste serif)
  2. Definition art (style entrée de dictionnaire)
  3. Watercolor lettering
  4. Definition bilingue (mot + traduction anglaise)

Pour chaque design : version Etsy (1080×1080), version impression
(3000×3000 @ 300 DPI), métadonnées Etsy/Redbubble.

Marché : public BookTok / lifestyle / language learners. Concurrence
faible car peu de vendeurs font les versions traduites pour autres marchés.

Variables d'env :
  MAX_EXPRESSIONS=10   limite à N expressions
  MAX_FORMATS=2        limite à N formats par expression
  SOURCE_LANG=japanese filtre par origine linguistique
"""

import csv
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("ERREUR : Pillow non installé")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "cultural_arbitrage"
USER_AGENT = "CulturalArbitrageProducer/1.0"
TIMEOUT = 180

# Top 30 expressions ROI-confirmées (cf. CULTURAL_ARBITRAGE_MERCH.md)
EXPRESSIONS = [
    # ⭐⭐⭐⭐⭐ ROI maximum
    {"word": "Hygge", "lang": "danish", "flag": "🇩🇰", "meaning": "cozy contentment, the art of comfort",
     "mood": "cozy", "phonetic": "/ˈhuːɡə/", "class": "n."},
    {"word": "Ikigai", "lang": "japanese", "flag": "🇯🇵", "meaning": "a reason for being, life's purpose",
     "mood": "zen", "phonetic": "/ˌiː.kiˈɡaɪ/", "class": "n."},
    {"word": "Wabi-sabi", "lang": "japanese", "flag": "🇯🇵", "meaning": "beauty in imperfection and impermanence",
     "mood": "zen", "phonetic": "/ˌwɑː.biˈsɑː.bi/", "class": "n."},
    {"word": "Saudade", "lang": "portuguese", "flag": "🇵🇹", "meaning": "a tender longing for what is absent",
     "mood": "melancholic", "phonetic": "/sɐwˈdadɨ/", "class": "n."},
    {"word": "Wanderlust", "lang": "german", "flag": "🇩🇪", "meaning": "a strong desire to travel and explore",
     "mood": "adventure", "phonetic": "/ˈwɒn.də.lʌst/", "class": "n."},
    {"word": "La Dolce Vita", "lang": "italian", "flag": "🇮🇹", "meaning": "the sweet life, the good life",
     "mood": "joyful", "phonetic": "/la ˈdoltʃe ˈvita/", "class": "n. phrase"},
    {"word": "Mi Amor", "lang": "spanish", "flag": "🇪🇸", "meaning": "my love",
     "mood": "romantic", "phonetic": "/mi aˈmoɾ/", "class": "n. phrase"},
    {"word": "Namaste", "lang": "sanskrit", "flag": "🇮🇳", "meaning": "the divine in me honors the divine in you",
     "mood": "spiritual", "phonetic": "/ˈnʌməsteɪ/", "class": "greeting"},
    {"word": "Karma", "lang": "sanskrit", "flag": "🇮🇳", "meaning": "the cosmic law of cause and effect",
     "mood": "spiritual", "phonetic": "/ˈkɑːr.mə/", "class": "n."},
    {"word": "C'est la vie", "lang": "french", "flag": "🇫🇷", "meaning": "such is life, that's life",
     "mood": "philosophical", "phonetic": "/sɛ la vi/", "class": "phrase"},

    # ⭐⭐⭐⭐ ROI très haut
    {"word": "Lagom", "lang": "swedish", "flag": "🇸🇪", "meaning": "just the right amount, balance",
     "mood": "cozy", "phonetic": "/ˈlɑːɡɔm/", "class": "adj."},
    {"word": "Fika", "lang": "swedish", "flag": "🇸🇪", "meaning": "a coffee break that means more than coffee",
     "mood": "cozy", "phonetic": "/ˈfiːkä/", "class": "n."},
    {"word": "Kintsugi", "lang": "japanese", "flag": "🇯🇵", "meaning": "mending broken things with gold",
     "mood": "zen", "phonetic": "/kɪnˈtsuːɡi/", "class": "n."},
    {"word": "Komorebi", "lang": "japanese", "flag": "🇯🇵", "meaning": "sunlight filtering through leaves",
     "mood": "zen", "phonetic": "/koˈmoɾebi/", "class": "n."},
    {"word": "Tsundoku", "lang": "japanese", "flag": "🇯🇵", "meaning": "buying books, letting them pile up",
     "mood": "bookish", "phonetic": "/tsɯndokɯ/", "class": "n."},
    {"word": "Schadenfreude", "lang": "german", "flag": "🇩🇪", "meaning": "pleasure derived from others' misfortune",
     "mood": "wit", "phonetic": "/ˈʃɑː.dənˌfrɔɪ.də/", "class": "n."},
    {"word": "Fernweh", "lang": "german", "flag": "🇩🇪", "meaning": "longing for far-away places",
     "mood": "adventure", "phonetic": "/ˈfɛʁnveː/", "class": "n."},
    {"word": "Zeitgeist", "lang": "german", "flag": "🇩🇪", "meaning": "the spirit of the times",
     "mood": "philosophical", "phonetic": "/ˈtsaɪtˌɡaɪst/", "class": "n."},
    {"word": "Mamma Mia", "lang": "italian", "flag": "🇮🇹", "meaning": "an exclamation of surprise or joy",
     "mood": "joyful", "phonetic": "/ˈmamma ˈmia/", "class": "interj."},
    {"word": "Ciao Bella", "lang": "italian", "flag": "🇮🇹", "meaning": "hello beautiful",
     "mood": "joyful", "phonetic": "/ˈtʃao ˈbɛlla/", "class": "greeting"},
    {"word": "Voilà", "lang": "french", "flag": "🇫🇷", "meaning": "there it is, behold",
     "mood": "elegant", "phonetic": "/vwa.la/", "class": "interj."},
    {"word": "Déjà vu", "lang": "french", "flag": "🇫🇷", "meaning": "the feeling of having lived this before",
     "mood": "philosophical", "phonetic": "/de.ʒa vy/", "class": "n."},
    {"word": "Joie de Vivre", "lang": "french", "flag": "🇫🇷", "meaning": "exuberant joy of being alive",
     "mood": "joyful", "phonetic": "/ʒwa də vivʁ/", "class": "n."},
    {"word": "Sobremesa", "lang": "spanish", "flag": "🇪🇸", "meaning": "the conversation lingering after a meal",
     "mood": "cozy", "phonetic": "/soβɾeˈmesa/", "class": "n."},

    # ⭐⭐⭐ ROI solide / niche profonde
    {"word": "Mono no aware", "lang": "japanese", "flag": "🇯🇵", "meaning": "the pathos of fleeting beauty",
     "mood": "melancholic", "phonetic": "/mono no aware/", "class": "n."},
    {"word": "Shinrin-yoku", "lang": "japanese", "flag": "🇯🇵", "meaning": "forest bathing, healing in the woods",
     "mood": "zen", "phonetic": "/ʃinɾiɲjokɯ/", "class": "n."},
    {"word": "Friluftsliv", "lang": "norwegian", "flag": "🇳🇴", "meaning": "the philosophy of open-air living",
     "mood": "adventure", "phonetic": "/ˈfriːˌlʉftsˌliːv/", "class": "n."},
    {"word": "Sisu", "lang": "finnish", "flag": "🇫🇮", "meaning": "stoic courage in the face of adversity",
     "mood": "strength", "phonetic": "/ˈsisu/", "class": "n."},
    {"word": "Waldeinsamkeit", "lang": "german", "flag": "🇩🇪", "meaning": "the peaceful solitude of being alone in the forest",
     "mood": "zen", "phonetic": "/ˈvaltʔaɪnzaːmkaɪt/", "class": "n."},
    {"word": "Flâner", "lang": "french", "flag": "🇫🇷", "meaning": "to wander without aim, savoring the city",
     "mood": "elegant", "phonetic": "/fla.ne/", "class": "v."},
    {"word": "Duende", "lang": "spanish", "flag": "🇪🇸", "meaning": "the soulful charm of art that moves you",
     "mood": "passionate", "phonetic": "/ˈdwende/", "class": "n."},
    {"word": "Iktsuarpok", "lang": "inuit", "flag": "🇨🇦", "meaning": "anticipation of someone's arrival",
     "mood": "tender", "phonetic": "/ɪktsuarpok/", "class": "n."},
]

# Palettes par mood
MOOD_PALETTES = {
    "cozy":         "warm cream and soft terracotta",
    "zen":          "soft sage green and warm cream",
    "melancholic":  "dusty blue-grey and faded rose",
    "adventure":    "deep teal and mustard yellow",
    "joyful":       "sunshine yellow and tomato red on cream",
    "romantic":     "soft blush pink and dusty rose",
    "spiritual":    "lotus pink and gold on ivory",
    "philosophical": "deep navy and antique gold",
    "wit":          "muted olive and burnt orange",
    "bookish":      "warm leather brown and aged paper cream",
    "elegant":      "soft ivory and matte black",
    "strength":     "iron grey and warm copper",
    "passionate":   "deep crimson and burnt sienna",
    "tender":       "pale lavender and warm white",
}

# Formats de design
FORMATS = {
    "minimalist_typo": {
        "name": "Minimalist Typography",
        "prompt": (
            "elegant minimalist typography poster, the single word '{word}' "
            "in large serif font, centered on solid {palette} background, "
            "generous white space, professional graphic design, museum poster "
            "style, no watermark no signature"
        ),
        "etsy_title_template": "{word} Print — Minimalist Typography {lang_title} Art",
    },
    "definition_dict": {
        "name": "Dictionary Definition",
        "prompt": (
            "dictionary entry style typography poster, header word '{word}' "
            "in large serif, below in small italic '{class_short}' and "
            "phonetic '{phonetic}', then in smaller serif the definition: "
            "'{meaning}', warm aged paper texture, vintage typography, "
            "{palette} palette, scholarly aesthetic"
        ),
        "etsy_title_template": "{word} Definition Print — {lang_title} Dictionary Art Poster",
    },
    "watercolor_lettering": {
        "name": "Watercolor Lettering",
        "prompt": (
            "hand-painted watercolor lettering of the word '{word}', "
            "soft brush strokes calligraphy, {palette} palette with gentle "
            "color bleeds, delicate floral accents around the word, "
            "romantic artistic poster, white background, no text outside word"
        ),
        "etsy_title_template": "{word} Watercolor Print — Hand Lettered {lang_title} Word Art",
    },
    "bilingual_swap": {
        "name": "Bilingual Translation",
        "prompt": (
            "elegant bilingual typography poster, top half features the word "
            "'{word}' in bold serif large, bottom half features the translation "
            "'{meaning}' in smaller italic, {palette} palette, modern editorial "
            "design, generous spacing, museum poster style"
        ),
        "etsy_title_template": "{word} Translation Print — {lang_title} Word with English Meaning",
    },
}

# Tags de base par mood (à compléter avec lang/word)
MOOD_TAGS = {
    "cozy":         ["hygge", "cozy decor", "scandinavian", "minimalist", "cottage"],
    "zen":          ["zen decor", "japanese aesthetic", "mindfulness", "wabi sabi", "meditation"],
    "melancholic":  ["poetic art", "literary print", "bookish gift", "soft aesthetic"],
    "adventure":    ["travel poster", "wanderlust print", "explore", "vintage map"],
    "joyful":       ["italian decor", "kitchen art", "joyful print", "happy decor"],
    "romantic":     ["romance gift", "valentines art", "love quote", "anniversary"],
    "spiritual":    ["yoga decor", "spiritual gift", "meditation art", "namaste"],
    "philosophical": ["philosophy quote", "stoic art", "intellectual decor"],
    "wit":          ["funny german", "smart humor", "witty print", "philosophy joke"],
    "bookish":      ["booktok gift", "reader gift", "library decor", "book lover"],
    "elegant":      ["french chic", "parisian decor", "elegant art", "minimalist quote"],
    "strength":     ["motivational print", "strong woman", "perseverance"],
    "passionate":   ["flamenco art", "passionate quote", "spanish decor"],
    "tender":       ["tender quote", "loving gift", "gentle decor"],
}


def pollinations_url(prompt: str, seed: int, width: int = 1536, height: int = 1536) -> str:
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
            time.sleep(6 + attempt * 6)
    return False


def slugify(text: str) -> str:
    import re
    s = text.lower().replace("'", "").replace("'", "").replace("-", "_")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def make_etsy_preview(src: Path, dest: Path) -> None:
    img = Image.open(src).convert("RGB")
    side = min(img.width, img.height)
    off_x = (img.width - side) // 2
    off_y = (img.height - side) // 2
    img = img.crop((off_x, off_y, off_x + side, off_y + side))
    img = img.resize((1080, 1080), Image.LANCZOS)
    img.save(dest, "JPEG", quality=92)


def make_print_size(src: Path, dest: Path) -> None:
    img = Image.open(src).convert("RGB")
    side = min(img.width, img.height)
    off_x = (img.width - side) // 2
    off_y = (img.height - side) // 2
    img = img.crop((off_x, off_y, off_x + side, off_y + side))
    img = img.resize((3000, 3000), Image.LANCZOS)
    img.save(dest, "PNG", optimize=True)


def produce_design(expr: dict, fmt_key: str, fmt: dict, idx: int) -> dict | None:
    palette = MOOD_PALETTES.get(expr["mood"], "warm cream and dusty rose")
    prompt = fmt["prompt"].format(
        word=expr["word"],
        palette=palette,
        meaning=expr["meaning"],
        phonetic=expr["phonetic"],
        class_short=expr["class"],
    )
    word_slug = slugify(expr["word"])
    design_dir = OUTPUT_DIR / word_slug / fmt_key
    design_dir.mkdir(parents=True, exist_ok=True)
    raw = design_dir / "raw.png"
    seed = idx * 10007 + random.randint(0, 9999)
    url = pollinations_url(prompt, seed)

    print(f"  [{idx:>3}] {expr['word']} → {fmt_key}")
    if not http_get(url, raw):
        print(f"        echec Pollinations")
        return None

    try:
        make_etsy_preview(raw, design_dir / "etsy_preview.jpg")
        make_print_size(raw, design_dir / "print_3000.png")
    except Exception as exc:  # noqa: BLE001
        print(f"        traitement image echoue : {exc}")
        return None
    finally:
        if raw.exists():
            raw.unlink()

    lang_title = expr["lang"].capitalize()
    title = fmt["etsy_title_template"].format(
        word=expr["word"], lang_title=lang_title)
    base_tags = MOOD_TAGS.get(expr["mood"], [])
    tags = [
        expr["word"].lower(),
        f"{expr['lang']} word",
        f"{expr['lang']} art",
        "untranslatable word",
        "language gift",
        "linguistic art",
        "word definition",
        "typography poster",
        "minimalist print",
        "wall art",
        "literary gift",
        "etymology",
        "polyglot gift",
    ] + base_tags
    tags = list(dict.fromkeys(tags))[:13]  # dedup + max 13 Etsy

    metadata = {
        "design_id": f"{word_slug}_{fmt_key}",
        "expression": expr["word"],
        "language": expr["lang"],
        "meaning": expr["meaning"],
        "format": fmt["name"],
        "title": title[:140],
        "tags_etsy": ", ".join(tags),
        "price_etsy": 4.50,
        "license": "personal use only",
        "files_included": "print_3000.png (3000x3000 @ 300dpi)",
        "prompt_used": prompt,
        "seed": seed,
    }
    (design_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    max_expr = int(os.environ.get("MAX_EXPRESSIONS") or "0") or len(EXPRESSIONS)
    max_fmt = int(os.environ.get("MAX_FORMATS") or "0") or len(FORMATS)
    source_lang = os.environ.get("SOURCE_LANG", "").strip().lower()

    expressions = EXPRESSIONS[:max_expr]
    if source_lang:
        expressions = [e for e in expressions if e["lang"] == source_lang]
        print(f"Filtré sur lang={source_lang} : {len(expressions)} expressions")

    formats = dict(list(FORMATS.items())[:max_fmt])
    total = len(expressions) * len(formats)
    print(f"=== CULTURAL ARBITRAGE — {len(expressions)} mots × "
          f"{len(formats)} formats = {total} designs ===\n")

    all_metas = []
    idx = 0
    for expr in expressions:
        for fmt_key, fmt in formats.items():
            idx += 1
            meta = produce_design(expr, fmt_key, fmt, idx)
            if meta:
                all_metas.append(meta)
            time.sleep(2)

    csv_path = OUTPUT_DIR / "etsy_bulk_upload.csv"
    if all_metas:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["design_id", "expression", "language", "format",
                            "title", "tags_etsy", "price_etsy"],
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(all_metas)

    print(f"\n{'=' * 60}")
    print(f"  Produits : {len(all_metas)}/{total}")
    print(f"  CSV bulk : {csv_path}")
    print(f"  Dossier  : {OUTPUT_DIR}")
    return 0 if all_metas else 1


if __name__ == "__main__":
    sys.exit(main())
