"""
Pipeline Tumbler Wraps — production de designs sublimation pour Etsy.

Tumbler wraps = LE bestseller digital sublimation 2026 (Etsy).
Prix de vente : 3-6 € par design. Marge 100 % (digital download).

FORMAT TUMBLER 20oz STRAIGHT :
- Dimensions wrap : 9.3" × 8.3" → 2790 × 2490 px @ 300 DPI

Pipeline :
1. Pollinations Flux génère un design en ratio wrap
2. Pillow recadre aux dimensions Etsy exactes
3. Génère preview Etsy carré
4. Métadonnées Etsy + CSV bulk upload
"""

import csv
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
    from PIL import Image
except ImportError:
    print("ERREUR : Pillow non installé")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "tumbler_wraps"
USER_AGENT = "TumblerWrapsProducer/1.0"
TIMEOUT = 180

TUMBLER_FORMATS = {
    "tumbler_20oz_straight": {
        "name": "20oz Straight Tumbler Wrap",
        "width_in": 9.3, "height_in": 8.3, "dpi": 300,
    },
    "tumbler_30oz": {
        "name": "30oz Tumbler Wrap",
        "width_in": 9.4, "height_in": 9.5, "dpi": 300,
    },
    "mug_11oz": {
        "name": "11oz Mug Wrap",
        "width_in": 8.5, "height_in": 3.5, "dpi": 300,
    },
}

NICHES = {
    "witchy_cottagecore": {
        "title_template": "Witchy Cottagecore {subject} Tumbler Wrap PNG — 20oz Sublimation",
        "tags": ["witchy tumbler", "cottagecore wrap", "witch sublimation",
                 "halloween tumbler", "magical wrap", "dark academia",
                 "moon tumbler", "occult design", "gothic wrap",
                 "tarot tumbler", "spell book", "autumn aesthetic",
                 "fall tumbler"],
        "price_etsy": 3.99,
        "prompts": [
            "all-over pattern of witchy cottagecore elements mushrooms moons stars crystals candles, repeating seamless tile, deep eggplant purple and gold palette, watercolor illustration style",
            "all-over pattern of vintage tarot cards moons and pentacles, repeating seamless design, deep midnight blue with gold accents, art nouveau decorative style",
            "all-over pattern of mystical herbs and apothecary bottles, repeating seamless tile, sage green and burgundy palette, vintage botanical illustration",
            "all-over pattern of ravens crystals and skulls, repeating seamless design, dark academia palette of deep teal and gold, gothic ornamental style",
            "all-over pattern of celestial moons stars and constellations, repeating seamless tile, deep navy with gold and silver accents, mystical astrology aesthetic",
        ],
    },
    "pride_celebration": {
        "title_template": "Pride {subject} Tumbler Wrap — Rainbow Sublimation 2026",
        "tags": ["pride tumbler", "lgbtq wrap", "rainbow design",
                 "love is love", "pride month", "queer aesthetic",
                 "celebrate pride", "pride gift", "ally tumbler",
                 "inclusive design", "rainbow flag", "pride parade",
                 "pride 2026"],
        "price_etsy": 3.99,
        "prompts": [
            "all-over watercolor rainbow pride pattern with flowers and hearts, repeating seamless tile, vibrant rainbow palette, celebratory feminine style",
            "all-over pattern of pride flags hearts and rainbow elements, repeating seamless design, bold vibrant colors, modern pride celebration aesthetic",
            "all-over pattern with text Love is Love and rainbow stripes flowers, repeating seamless tile, romantic rainbow watercolor style",
            "all-over pattern of butterflies in rainbow colors with floral accents, repeating seamless design, vibrant pride palette, joyful illustration",
            "all-over pattern of pride affirmations with rainbow watercolor splashes, repeating seamless tile, inspirational pride aesthetic",
        ],
    },
    "fathers_day": {
        "title_template": "Father's Day {subject} Tumbler Wrap — Dad Gift Sublimation",
        "tags": ["fathers day tumbler", "dad gift", "papa wrap",
                 "best dad ever", "dad humor", "grilling dad",
                 "fishing dad", "dad mug design", "fathers day 2026",
                 "papa coffee", "dad tumbler gift", "dad birthday",
                 "step dad gift"],
        "price_etsy": 3.99,
        "prompts": [
            "all-over pattern of dad humor quotes with rustic icons, repeating seamless tile, vintage masculine palette of navy brown and cream",
            "all-over pattern of fishing gear lures and fish illustrations, repeating seamless design, vintage outdoor palette, rustic dad aesthetic",
            "all-over pattern of grilling tools BBQ icons and food, repeating seamless tile, warm BBQ-inspired palette",
            "all-over pattern of beard mustache and typography ornaments, repeating seamless design, classic barbershop palette of navy white and red",
            "all-over pattern of tools wrenches and industrial elements, repeating seamless tile, vintage industrial palette of grey and ochre",
        ],
    },
    "summer_beach": {
        "title_template": "Summer Vibes {subject} Tumbler Wrap — Beach Sublimation",
        "tags": ["summer tumbler", "beach wrap", "vacation vibes",
                 "tropical design", "summer 2026", "pool party",
                 "beach mama", "salty hair", "vacation mode",
                 "summer gift", "ocean wrap", "palm trees",
                 "sunshine aesthetic"],
        "price_etsy": 3.99,
        "prompts": [
            "all-over watercolor pattern of palm trees flamingos and tropical flowers, repeating seamless tile, bright summer palette of coral pink turquoise and yellow, tropical vacation",
            "all-over pattern of seashells starfish and ocean waves, repeating seamless design, beach palette of turquoise cream and gold, coastal illustration",
            "all-over pattern of cocktails fruit slices and beach umbrellas, repeating seamless tile, vibrant summer palette, retro vacation aesthetic",
            "all-over watercolor pattern of sunglasses sunscreen and beach essentials, repeating seamless design, bright cheerful palette, summer fun aesthetic",
            "all-over pattern of pineapples coconuts and tropical leaves, repeating seamless tile, vivid tropical palette, vacation paradise illustration",
        ],
    },
    "coffee_humor": {
        "title_template": "Funny Coffee {subject} Tumbler Wrap — Sublimation PNG",
        "tags": ["coffee tumbler", "funny coffee", "caffeine addict",
                 "coffee mom", "but first coffee", "barista gift",
                 "office humor tumbler", "morning person", "espresso",
                 "coffee lover gift", "tumbler quote", "coffee wrap",
                 "monday motivation"],
        "price_etsy": 3.99,
        "prompts": [
            "vintage typography all-over pattern with coffee quotes and bean illustrations, repeating seamless tile, warm sepia tones, hand-lettered style",
            "all-over pattern of coffee cups beans and steam swirls, repeating seamless design, warm brown palette and cream, vintage Americana style",
            "watercolor all-over pattern of coffee cups in different styles, repeating seamless tile, warm earth tones",
            "all-over typographic pattern with coffee bean ornaments, vintage diner palette of red and cream, retro Americana",
            "all-over pattern of cute coffee cup characters with faces and steam, repeating seamless design, warm pastel palette, kawaii illustration",
        ],
    },
}


def pollinations_url(prompt: str, seed: int, width: int, height: int) -> str:
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


def fit_image(src: Image.Image, target_w: int, target_h: int) -> Image.Image:
    sr = src.width / src.height
    tr = target_w / target_h
    if sr > tr:
        new_w = int(src.height * tr)
        off = (src.width - new_w) // 2
        src = src.crop((off, 0, off + new_w, src.height))
    elif sr < tr:
        new_h = int(src.width / tr)
        off = (src.height - new_h) // 2
        src = src.crop((0, off, src.width, off + new_h))
    return src.resize((target_w, target_h), Image.LANCZOS)


def short_subject(prompt: str) -> str:
    words = re.findall(r"\b[a-z]{4,}\b", prompt.lower())
    stop = {"with", "from", "into", "this", "their", "these", "those",
            "style", "color", "palette", "background", "illustration",
            "vintage", "watercolor", "minimalist", "modern", "design",
            "warm", "deep", "pattern", "seamless", "repeating", "tile",
            "elements", "various", "different", "overall", "around"}
    keepers = [w.capitalize() for w in words if w not in stop][:3]
    return " ".join(keepers) or "Design"


def produce_design(niche_key: str, niche: dict, idx: int, prompt: str) -> dict | None:
    fmt = TUMBLER_FORMATS["tumbler_20oz_straight"]
    target_w = int(fmt["width_in"] * fmt["dpi"])
    target_h = int(fmt["height_in"] * fmt["dpi"])
    gen_w, gen_h = min(target_w, 2048), min(target_h, 2048)

    design_dir = OUTPUT_DIR / niche_key / f"design_{idx:02d}"
    design_dir.mkdir(parents=True, exist_ok=True)
    raw_path = design_dir / "raw.png"
    seed = idx * 10000 + random.randint(0, 9999)
    url = pollinations_url(prompt, seed, gen_w, gen_h)

    print(f"  [{idx:>2}] {prompt[:60]}...")
    if not http_get(url, raw_path):
        print(f"        echec generation Pollinations")
        return None

    try:
        src = Image.open(raw_path).convert("RGB")
    except Exception as exc:  # noqa: BLE001
        print(f"        image illisible : {exc}")
        return None

    wrap = fit_image(src, target_w, target_h)
    wrap.save(design_dir / "wrap.png", "PNG", optimize=True)
    preview = fit_image(src, 1080, 1080)
    preview.save(design_dir / "etsy_preview.jpg", "JPEG", quality=90)
    raw_path.unlink()

    subject = short_subject(prompt)
    title = niche["title_template"].format(subject=subject)
    metadata = {
        "design_id": f"{niche_key}_{idx:02d}",
        "title": title[:140],
        "tags_etsy": ", ".join(niche["tags"][:13]),
        "price_etsy": niche["price_etsy"],
        "format": fmt["name"],
        "dimensions_in": f"{fmt['width_in']}x{fmt['height_in']}",
        "dimensions_px": f"{target_w}x{target_h}",
        "prompt_used": prompt,
        "seed": seed,
    }
    (design_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    print(f"        OK wrap {target_w}x{target_h}")
    return metadata


def produce_niche(niche_key: str, niche: dict, max_designs: int | None = None) -> int:
    prompts = niche["prompts"][:max_designs] if max_designs else niche["prompts"]
    print(f"\n=== NICHE : {niche_key} ({len(prompts)} designs) ===")
    metas = []
    for i, prompt in enumerate(prompts, 1):
        meta = produce_design(niche_key, niche, i, prompt)
        if meta:
            metas.append(meta)
        time.sleep(2)

    csv_path = OUTPUT_DIR / niche_key / "etsy_bulk_upload.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["design_id", "title", "tags_etsy", "price_etsy",
                        "format", "dimensions_in", "dimensions_px"],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(metas)
    print(f"  -> {len(metas)}/{len(prompts)} produits, CSV : {csv_path}")
    return len(metas)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    target = os.environ.get("SOURCE_NICHE", "").strip()
    max_designs = int(os.environ.get("MAX_DESIGNS") or "0") or None
    if target:
        if target not in NICHES:
            print(f"Niche inconnue. Choix : {list(NICHES)}")
            return 2
        produce_niche(target, NICHES[target], max_designs)
    else:
        for k, n in NICHES.items():
            produce_niche(k, n, max_designs)
    print(f"\n{'=' * 60}\nTumbler wraps : {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
