"""
Pipeline CULTURAL ARBITRAGE V2 — utilise design_composer.

V1 : Flux gibberish sur définitions longues.
V2 : Pollinations génère un fond ambiant SANS texte selon mood,
design_composer overlay mot + langue/classe + définition.

Format : "word" grand + "Portuguese, n." petit + "longing for what is absent" plus petit
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.design_composer import compose_design, get_layout  # noqa: E402

from produce_cultural_arbitrage import EXPRESSIONS, MOOD_PALETTES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "cultural_arbitrage_v2"
USER_AGENT = "CulturalArbitrageV2/1.0"
TIMEOUT = 180

# Backgrounds par mood (sans texte)
MOOD_BG_PROMPTS = {
    "cozy": "soft warm cream textured paper background with subtle hygge elements candles tea cups very faded delicate ABSOLUTELY NO TEXT NO LETTERS",
    "zen": "soft sage green minimalist zen background subtle bamboo leaves japanese aesthetic faded delicate ABSOLUTELY NO TEXT NO LETTERS",
    "melancholic": "dusty blue-grey faded watercolor sky background poetic atmospheric melancholic ABSOLUTELY NO TEXT NO LETTERS",
    "adventure": "vintage map texture deep teal and mustard yellow worn traveler aesthetic ABSOLUTELY NO TEXT NO LETTERS",
    "joyful": "warm sunshine yellow cream background with subtle italian rural elements faded delicate ABSOLUTELY NO TEXT NO LETTERS",
    "romantic": "soft blush pink dusty rose romantic background with subtle floral hints faded delicate ABSOLUTELY NO TEXT NO LETTERS",
    "spiritual": "lotus pink and gold on ivory subtle mandala patterns spiritual aesthetic faded delicate ABSOLUTELY NO TEXT NO LETTERS",
    "philosophical": "deep navy and antique gold marble texture intellectual classical aesthetic faded ABSOLUTELY NO TEXT NO LETTERS",
    "wit": "muted olive and burnt orange aged paper texture witty humorous aesthetic faded ABSOLUTELY NO TEXT NO LETTERS",
    "bookish": "warm leather brown aged paper cream texture book-loving aesthetic faded delicate ABSOLUTELY NO TEXT NO LETTERS",
    "elegant": "soft ivory matte black elegant minimalist background french chic faded ABSOLUTELY NO TEXT NO LETTERS",
    "strength": "iron grey warm copper metal texture stoic aesthetic faded delicate ABSOLUTELY NO TEXT NO LETTERS",
    "passionate": "deep crimson burnt sienna textured background spanish flamenco aesthetic faded ABSOLUTELY NO TEXT NO LETTERS",
    "tender": "pale lavender warm white tender soft background faded delicate ABSOLUTELY NO TEXT NO LETTERS",
}


def pollinations_url(prompt: str, seed: int, w: int = 1280, h: int = 1280) -> str:
    encoded = urllib.parse.quote(prompt, safe="")
    return (f"https://image.pollinations.ai/prompt/{encoded}"
            f"?model=flux&width={w}&height={h}"
            f"&seed={seed}&nologo=true&private=true&enhance=true")


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
            print(f"    retry {attempt+1}/{retries} : {exc}")
            time.sleep(6 + attempt * 6)
    return False


def slugify(text: str) -> str:
    import re
    s = text.lower().replace("'", "").replace("-", "_")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def make_outputs(composed_path: Path, design_dir: Path) -> None:
    from PIL import Image
    img = Image.open(composed_path).convert("RGB")
    img.resize((1080, 1080), Image.LANCZOS).save(
        design_dir / "etsy_preview.jpg", "JPEG", quality=92)


def produce_design(expr: dict, idx: int) -> dict | None:
    mood = expr["mood"]
    word_slug = slugify(expr["word"])
    design_dir = OUTPUT_DIR / word_slug
    design_dir.mkdir(parents=True, exist_ok=True)
    bg_path = design_dir / "raw_bg.png"
    final = design_dir / "print_3000.png"
    seed = idx * 10111 + random.randint(0, 9999)

    bg_prompt = MOOD_BG_PROMPTS.get(mood, MOOD_BG_PROMPTS["cozy"])
    url = pollinations_url(bg_prompt, seed)

    print(f"  [{idx:>3}] {expr['word']:<20} ({mood})")
    if not http_get(url, bg_path):
        print(f"        echec Pollinations bg")
        return None

    try:
        layout = get_layout("cultural_word")
        compose_design(
            layout=layout,
            illustration_path=None,
            text_values={
                "word": expr["word"],
                "language_class": f"{expr['lang']}, {expr['class']}",
                "meaning": expr["meaning"],
            },
            output_path=final,
            background_override=bg_path,
        )
        make_outputs(final, design_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"        compose echoue : {exc}")
        return None
    finally:
        if bg_path.exists():
            bg_path.unlink()

    title = (f"{expr['word']} — {expr['lang'].title()} Word Print "
             f"Untranslatable Definition Art")[:140]
    tags = [
        expr["word"].lower(),
        f"{expr['lang']} word",
        f"{expr['lang']} art",
        "untranslatable word",
        "language gift",
        "definition print",
        "minimalist art",
        "wall art",
        "literary gift",
        "polyglot gift",
        "etymology print",
        f"{expr['mood']} aesthetic",
        "typography poster",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"cultural_v2_{word_slug}",
        "version": "v2",
        "text_overlay_method": "pillow",
        "expression": expr["word"],
        "language": expr["lang"],
        "meaning": expr["meaning"],
        "mood": expr["mood"],
        "title": title,
        "tags_etsy": ", ".join(tags),
        "price_etsy": 4.50,
        "files_included": "etsy_preview.jpg, print_3000.png (3000x3000)",
        "bg_prompt_used": bg_prompt,
        "seed": seed,
    }
    (design_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    max_e = int(os.environ.get("MAX_EXPRESSIONS") or "0") or len(EXPRESSIONS)
    source_lang = os.environ.get("SOURCE_LANG", "").strip().lower()

    expressions = EXPRESSIONS[:max_e]
    if source_lang:
        expressions = [e for e in expressions if e["lang"] == source_lang]

    print(f"=== CULTURAL ARBITRAGE V2 (overlay) — {len(expressions)} mots ===\n")

    metas = []
    for idx, expr in enumerate(expressions, 1):
        m = produce_design(expr, idx)
        if m:
            metas.append(m)
        time.sleep(2)

    if metas:
        csv_path = OUTPUT_DIR / "etsy_bulk_upload.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["design_id", "expression", "language", "mood",
                            "title", "tags_etsy", "price_etsy"],
                extrasaction="ignore",
            )
            w.writeheader()
            w.writerows(metas)

    print(f"\n  Produits : {len(metas)}/{len(expressions)} → {OUTPUT_DIR}")
    return 0 if metas else 1


if __name__ == "__main__":
    sys.exit(main())
