"""
Pipeline QUOTES MINIMAL — citations universelles en typo serif minimaliste.

Marché énorme Etsy : « inspirational quotes wall art » est dans les
top 10 catégories. Format simple à exécuter parfaitement avec overlay.

50 citations universelles éprouvées × 3 styles = 150 designs.

Aucune génération de texte par IA → 100% fiable.
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

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "quotes_minimal"
USER_AGENT = "QuotesMinimal/1.0"
TIMEOUT = 180

QUOTES = [
    # Self-care / lifestyle
    {"quote": "Be kind to yourself", "category": "self_care", "mood": "soft"},
    {"quote": "You are enough", "category": "self_care", "mood": "soft"},
    {"quote": "Slow down", "category": "self_care", "mood": "soft"},
    {"quote": "Breathe in. Breathe out.", "category": "self_care", "mood": "soft"},
    {"quote": "Rest is productive", "category": "self_care", "mood": "soft"},
    {"quote": "Trust the timing", "category": "self_care", "mood": "soft"},
    {"quote": "One day at a time", "category": "self_care", "mood": "soft"},
    {"quote": "Stay soft in a hard world", "category": "self_care", "mood": "soft"},
    # Motivation
    {"quote": "Do it scared", "category": "motivation", "mood": "bold"},
    {"quote": "Less doubt, more action", "category": "motivation", "mood": "bold"},
    {"quote": "Begin again", "category": "motivation", "mood": "bold"},
    {"quote": "Take the leap", "category": "motivation", "mood": "bold"},
    {"quote": "Done is better than perfect", "category": "motivation", "mood": "bold"},
    {"quote": "Show up anyway", "category": "motivation", "mood": "bold"},
    {"quote": "Start where you are", "category": "motivation", "mood": "bold"},
    # Bookish
    {"quote": "Just one more chapter", "category": "bookish", "mood": "classic"},
    {"quote": "Reading is my therapy", "category": "bookish", "mood": "classic"},
    {"quote": "Born to read, forced to adult", "category": "bookish", "mood": "classic"},
    {"quote": "So many books, so little time", "category": "bookish", "mood": "classic"},
    {"quote": "A book a day", "category": "bookish", "mood": "classic"},
    # Romance / love
    {"quote": "You & me", "category": "love", "mood": "soft"},
    {"quote": "Always", "category": "love", "mood": "soft"},
    {"quote": "Home is where you are", "category": "love", "mood": "soft"},
    {"quote": "Love grows here", "category": "love", "mood": "soft"},
    # Minimalist lifestyle
    {"quote": "Less but better", "category": "minimalist", "mood": "modern"},
    {"quote": "Simple is enough", "category": "minimalist", "mood": "modern"},
    {"quote": "Own less, live more", "category": "minimalist", "mood": "modern"},
    {"quote": "Slow living", "category": "minimalist", "mood": "modern"},
    # Coffee / morning
    {"quote": "But first, coffee", "category": "coffee", "mood": "classic"},
    {"quote": "Espresso yourself", "category": "coffee", "mood": "classic"},
    {"quote": "Caffeinated soul", "category": "coffee", "mood": "classic"},
    # Witty / sarcastic
    {"quote": "I am tired", "category": "witty", "mood": "bold"},
    {"quote": "Pretty sure I'm done", "category": "witty", "mood": "bold"},
    {"quote": "I can't, I have plans", "category": "witty", "mood": "bold"},
    {"quote": "Currently buffering", "category": "witty", "mood": "bold"},
    {"quote": "Introvert. Don't disturb.", "category": "witty", "mood": "bold"},
    # Wisdom
    {"quote": "This too shall pass", "category": "wisdom", "mood": "classic"},
    {"quote": "Be here now", "category": "wisdom", "mood": "classic"},
    {"quote": "Tomorrow is another day", "category": "wisdom", "mood": "classic"},
    {"quote": "All is well", "category": "wisdom", "mood": "classic"},
    {"quote": "Trust the journey", "category": "wisdom", "mood": "classic"},
    # Home decor friendly
    {"quote": "Gather here", "category": "home", "mood": "classic"},
    {"quote": "Home sweet home", "category": "home", "mood": "classic"},
    {"quote": "Stay awhile", "category": "home", "mood": "classic"},
    {"quote": "Welcome home", "category": "home", "mood": "classic"},
    # Travel
    {"quote": "Adventure awaits", "category": "travel", "mood": "bold"},
    {"quote": "Wander often", "category": "travel", "mood": "bold"},
    {"quote": "Let's get lost", "category": "travel", "mood": "bold"},
    # Mom / family
    {"quote": "Best Mom Ever", "category": "family", "mood": "soft"},
    {"quote": "Mama's tribe", "category": "family", "mood": "soft"},
    {"quote": "Family first", "category": "family", "mood": "soft"},
]

STYLES = [
    {"key": "cream_serif",
     "name": "Cream Serif",
     "bg_color": (252, 248, 240),
     "text_color": (40, 35, 30),
     "uses_pollinations": False},
    {"key": "warm_ambient",
     "name": "Warm Ambient",
     "bg_color": None,
     "uses_pollinations": True,
     "bg_prompt": "soft warm beige cream abstract minimalist background subtle texture ABSOLUTELY NO TEXT NO LETTERS",
     "text_color": (50, 40, 30)},
    {"key": "moody_navy",
     "name": "Moody Navy",
     "bg_color": (30, 35, 50),
     "text_color": (235, 225, 200),
     "uses_pollinations": False},
]


def pollinations_url(prompt: str, seed: int) -> str:
    encoded = urllib.parse.quote(prompt, safe="")
    return (f"https://image.pollinations.ai/prompt/{encoded}"
            f"?model=flux&width=1280&height=1280"
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
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:50]


def make_outputs(composed: Path, design_dir: Path) -> None:
    from PIL import Image
    img = Image.open(composed).convert("RGB")
    img.resize((1080, 1080), Image.LANCZOS).save(
        design_dir / "etsy_preview.jpg", "JPEG", quality=92)


def produce_design(quote: dict, style: dict, idx: int) -> dict | None:
    q_slug = slugify(quote["quote"])
    design_dir = OUTPUT_DIR / quote["category"] / f"{q_slug}_{style['key']}"
    design_dir.mkdir(parents=True, exist_ok=True)
    bg_path = design_dir / "raw_bg.png"
    final = design_dir / "print_3000.png"
    seed = idx * 10139 + random.randint(0, 9999)

    print(f"  [{idx:>3}] « {quote['quote']:<30} » → {style['name']}")

    bg_override = None
    if style["uses_pollinations"]:
        if not http_get(pollinations_url(style["bg_prompt"], seed), bg_path):
            print(f"        echec Pollinations bg")
            return None
        bg_override = bg_path

    try:
        layout = get_layout("quote_minimal")
        # Override background color si style l'impose
        if style["bg_color"] and not style["uses_pollinations"]:
            # Hack : on duplique le layout pour pas modifier le shared
            from copy import deepcopy
            layout = deepcopy(layout)
            layout.background_color = style["bg_color"]
        compose_design(
            layout=layout,
            illustration_path=None,
            text_values={"quote": quote["quote"]},
            output_path=final,
            background_override=bg_override,
            style_overrides={"quote_color": style["text_color"]},
        )
        make_outputs(final, design_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"        compose echoue : {exc}")
        return None
    finally:
        if bg_path.exists():
            bg_path.unlink()

    title = (f"\"{quote['quote']}\" Print — {style['name']} "
             f"Minimalist Quote Wall Art")[:140]
    tags = [
        f"{quote['category']} quote",
        "inspirational quote",
        "minimalist quote print",
        "wall art quote",
        style["key"].replace("_", " "),
        "typography poster",
        "modern home decor",
        "motivational print",
        "quote of the day",
        "etsy bestseller",
        "digital download quote",
        "instant download",
        "small business gift",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"quote_{q_slug}_{style['key']}",
        "text_overlay_method": "pillow",
        "quote": quote["quote"],
        "category": quote["category"],
        "style": style["key"],
        "title": title,
        "tags_etsy": ", ".join(tags),
        "price_etsy": 3.99,
        "files_included": "etsy_preview.jpg, print_3000.png (3000x3000)",
        "seed": seed,
    }
    (design_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    max_q = int(os.environ.get("MAX_QUOTES") or "0") or len(QUOTES)
    max_s = int(os.environ.get("MAX_STYLES") or "0") or len(STYLES)
    category_filter = os.environ.get("CATEGORY", "").strip().lower()

    quotes = QUOTES[:max_q]
    if category_filter:
        quotes = [q for q in quotes if q["category"] == category_filter]

    styles = STYLES[:max_s]
    total = len(quotes) * len(styles)
    print(f"=== QUOTES MINIMAL — {len(quotes)} × {len(styles)} = {total} ===\n")

    metas = []
    idx = 0
    for quote in quotes:
        for style in styles:
            idx += 1
            m = produce_design(quote, style, idx)
            if m:
                metas.append(m)
            time.sleep(1)

    if metas:
        csv_path = OUTPUT_DIR / "etsy_bulk_upload.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["design_id", "quote", "category", "style",
                            "title", "tags_etsy", "price_etsy"],
                extrasaction="ignore",
            )
            w.writeheader()
            w.writerows(metas)

    print(f"\n  Produits : {len(metas)}/{total} → {OUTPUT_DIR}")
    return 0 if metas else 1


if __name__ == "__main__":
    sys.exit(main())
