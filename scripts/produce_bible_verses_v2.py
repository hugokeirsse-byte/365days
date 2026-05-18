"""
Pipeline BIBLE VERSES V2 — utilise design_composer (overlay Pillow).

Résout le problème V1 : Flux générait du gibberish pour les versets.
V2 : Pollinations génère une illustration de fond (paysage, fleurs,
mountains selon style) SANS texte, puis design_composer overlay le
verset avec une typo lisible et le bandeau référence.

50 versets × 4 styles = 200 designs.

Variables d'env :
  MAX_VERSES=10
  MAX_STYLES=2
  TESTAMENT=both    (old, new, both)
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

# Réutilise la liste VERSES de la V1
from produce_bible_verses import VERSES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "bible_verses_v2"
USER_AGENT = "BibleVersesV2/1.0"
TIMEOUT = 180

# 4 styles avec backgrounds Pollinations SANS texte
STYLES = [
    {"key": "soft_watercolor",
     "name": "Soft Watercolor",
     "bg_prompt": "soft watercolor floral border illustration delicate roses peonies pastel pink and cream palette peaceful christian aesthetic ABSOLUTELY NO TEXT NO LETTERS NO WORDS decorative background only",
     "text_color": (60, 40, 50),
     "ref_color": (160, 90, 80)},
    {"key": "vintage_botanical",
     "name": "Vintage Botanical",
     "bg_prompt": "vintage botanical illustration ferns olive branches scientific style sepia and forest green palette scholarly christian aesthetic ABSOLUTELY NO TEXT NO LETTERS NO WORDS decorative background only",
     "text_color": (35, 30, 20),
     "ref_color": (110, 85, 40)},
    {"key": "modern_mountains",
     "name": "Modern Mountains",
     "bg_prompt": "modern minimalist mountain landscape silhouette soft sunrise palette peach lavender contemporary christian poster style ABSOLUTELY NO TEXT NO LETTERS NO WORDS decorative background only",
     "text_color": (40, 45, 70),
     "ref_color": (140, 100, 130)},
    {"key": "minimalist_gold",
     "name": "Minimalist Gold",
     "bg_prompt": "minimalist abstract gold leaf accents on cream paper texture elegant christian wall art generous white space ABSOLUTELY NO TEXT NO LETTERS NO WORDS decorative background only",
     "text_color": (45, 35, 30),
     "ref_color": (170, 130, 60)},
]


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
    s = text.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:40]


def make_outputs(composed_path: Path, design_dir: Path) -> None:
    from PIL import Image
    img = Image.open(composed_path).convert("RGB")
    img.resize((1080, 1080), Image.LANCZOS).save(
        design_dir / "etsy_preview.jpg", "JPEG", quality=92)


def produce_design(verse: dict, style: dict, idx: int) -> dict | None:
    ref_slug = slugify(verse["ref"])
    design_dir = OUTPUT_DIR / verse["testament"] / verse["topic"] / \
                  f"{ref_slug}_{style['key']}"
    design_dir.mkdir(parents=True, exist_ok=True)
    bg_path = design_dir / "raw_bg.png"
    final = design_dir / "print_3000.png"
    seed = idx * 10103 + random.randint(0, 9999)
    url = pollinations_url(style["bg_prompt"], seed)

    print(f"  [{idx:>3}] {verse['ref']:<20} → {style['name']}")
    if not http_get(url, bg_path):
        print(f"        echec Pollinations bg")
        return None

    try:
        layout = get_layout("bible_verse")
        compose_design(
            layout=layout,
            illustration_path=None,
            text_values={
                "reference": verse["ref"],
                "verse": verse["text"],
            },
            output_path=final,
            background_override=bg_path,
            style_overrides={
                "verse_color": style["text_color"],
                "reference_color": style["ref_color"],
            },
        )
        make_outputs(final, design_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"        compose echoue : {exc}")
        return None
    finally:
        if bg_path.exists():
            bg_path.unlink()

    title = (f"{verse['ref']} Bible Verse Print — {style['name']} "
             f"Christian Wall Art")[:140]
    tags = [
        verse["ref"].lower(),
        "bible verse art",
        "christian wall art",
        f"{verse['topic']} verse",
        "scripture print",
        "religious decor",
        "faith print",
        "christian gift",
        "church decor",
        style["name"].lower(),
        "inspirational quote",
        "prayer room art",
        "baptism gift",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"bible_v2_{ref_slug}_{style['key']}",
        "version": "v2",
        "text_overlay_method": "pillow",
        "reference": verse["ref"],
        "verse_text": verse["text"],
        "topic": verse["topic"],
        "testament": verse["testament"],
        "style": style["key"],
        "title": title,
        "tags_etsy": ", ".join(tags),
        "price_etsy": 4.99,
        "files_included": "etsy_preview.jpg, print_3000.png",
        "bg_prompt_used": style["bg_prompt"],
        "seed": seed,
    }
    (design_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    max_v = int(os.environ.get("MAX_VERSES") or "0") or len(VERSES)
    max_s = int(os.environ.get("MAX_STYLES") or "0") or len(STYLES)
    testament = os.environ.get("TESTAMENT", "both").strip().lower()

    verses = VERSES[:max_v]
    if testament in ("old", "new"):
        verses = [v for v in verses if v["testament"] == testament]

    styles = STYLES[:max_s]
    total = len(verses) * len(styles)
    print(f"=== BIBLE VERSES V2 (overlay) — {len(verses)} × {len(styles)} = {total} ===\n")

    metas = []
    idx = 0
    for verse in verses:
        for style in styles:
            idx += 1
            m = produce_design(verse, style, idx)
            if m:
                metas.append(m)
            time.sleep(2)

    if metas:
        csv_path = OUTPUT_DIR / "etsy_bulk_upload.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["design_id", "reference", "topic", "style",
                            "title", "tags_etsy", "price_etsy"],
                extrasaction="ignore",
            )
            w.writeheader()
            w.writerows(metas)

    print(f"\n  Produits : {len(metas)}/{total} → {OUTPUT_DIR}")
    return 0 if metas else 1


if __name__ == "__main__":
    sys.exit(main())
