"""
Pipeline LITERAL IDIOMS V2 — utilise design_composer.

V1 : Flux gibberish sur les phrases longues.
V2 : Pollinations génère l'illustration littérale (la scène absurde),
design_composer overlay les 3 textes : original + traduction littérale + sens.

Pour cette V2, on garde l'illustration au CENTRE (vraie valeur de la
blague visuelle), mais les textes sont overlay propres.
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
from lib.design_composer import compose_design, DesignLayout, \
    IllustrationPlacement, TextZone, DecorativeElement  # noqa: E402

from produce_literal_idioms import IDIOMS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "literal_idioms_v2"
USER_AGENT = "LiteralIdiomsV2/1.0"
TIMEOUT = 180


# Layout spécial : illustration en HAUT (40%) + textes en bas
LAYOUT_LITERAL_WITH_SCENE = DesignLayout(
    name="literal_with_scene",
    canvas_size=(3000, 3000),
    background_color=(250, 245, 235),
    illustration=IllustrationPlacement(
        center_xy_pct=(0.5, 0.28),
        size_pct=(0.85, 0.50),
        fit_mode="cover",
    ),
    text_zones=[
        TextZone(text_key="original", center_xy_pct=(0.5, 0.62),
                 max_box_pct=(0.85, 0.07), font_role="title_italic",
                 color=(80, 60, 40), max_lines=2, auto_size=True,
                 min_size=50),
        TextZone(text_key="literal", center_xy_pct=(0.5, 0.76),
                 max_box_pct=(0.85, 0.15), font_role="title_bold",
                 color=(40, 30, 25), max_lines=3, auto_size=True,
                 min_size=60),
        TextZone(text_key="meaning", center_xy_pct=(0.5, 0.92),
                 max_box_pct=(0.78, 0.07), font_role="body_serif_italic",
                 color=(100, 80, 70), max_lines=2, auto_size=True,
                 min_size=40),
    ],
    decorative_elements=[
        DecorativeElement(type="horizontal_line",
                          center_xy_pct=(0.5, 0.68),
                          size_pct=0.10, color=(160, 110, 70),
                          extra={"thickness": 2}),
        DecorativeElement(type="horizontal_line",
                          center_xy_pct=(0.5, 0.87),
                          size_pct=0.10, color=(160, 110, 70),
                          extra={"thickness": 2}),
    ],
)


def pollinations_url(prompt: str, seed: int, w: int = 1536, h: int = 1024) -> str:
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
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:50]


def make_outputs(composed: Path, design_dir: Path) -> None:
    from PIL import Image
    img = Image.open(composed).convert("RGB")
    img.resize((1080, 1080), Image.LANCZOS).save(
        design_dir / "etsy_preview.jpg", "JPEG", quality=92)


def produce_design(idiom: dict, idx: int) -> dict | None:
    # Illustration prompt explicite — pas de texte
    illust_prompt = (
        f"{idiom['scene']}, centered illustration, editorial poster quality, "
        f"ABSOLUTELY NO TEXT NO LETTERS NO WORDS in the image, "
        f"clean composition with white margins"
    )
    slug = slugify(idiom["literal"])
    design_dir = OUTPUT_DIR / idiom["lang"] / slug
    design_dir.mkdir(parents=True, exist_ok=True)
    illust_path = design_dir / "raw_illust.png"
    final = design_dir / "print_3000.png"
    seed = idx * 10121 + random.randint(0, 9999)

    print(f"  [{idx:>3}] {idiom['flag']} « {idiom['literal']} »")
    if not http_get(pollinations_url(illust_prompt, seed), illust_path):
        print(f"        echec Pollinations illust")
        return None

    try:
        compose_design(
            layout=LAYOUT_LITERAL_WITH_SCENE,
            illustration_path=illust_path,
            text_values={
                "original": idiom["original"],
                "literal": idiom["literal"],
                "meaning": idiom["meaning"],
            },
            output_path=final,
        )
        make_outputs(final, design_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"        compose echoue : {exc}")
        return None
    finally:
        if illust_path.exists():
            illust_path.unlink()

    title = (f"{idiom['literal']} — Funny {idiom['lang'].title()} Idiom "
             f"Translation Print")[:140]
    tags = [
        f"funny {idiom['lang']} idiom",
        f"{idiom['lang']} learning",
        "language learner gift",
        "polyglot art",
        "linguistics print",
        "translation humor",
        f"{idiom['lang']} expression",
        "language teacher gift",
        "etymology art",
        "literal translation",
        "language nerd",
        "idiom wall art",
        "humor poster",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"idiom_v2_{idiom['lang']}_{slug}",
        "version": "v2",
        "text_overlay_method": "pillow",
        "language": idiom["lang"],
        "original": idiom["original"],
        "literal_translation": idiom["literal"],
        "actual_meaning": idiom["meaning"],
        "title": title,
        "tags_etsy": ", ".join(tags),
        "price_etsy": 4.99,
        "files_included": "etsy_preview.jpg, print_3000.png",
        "illust_prompt_used": illust_prompt,
        "seed": seed,
    }
    (design_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    max_i = int(os.environ.get("MAX_IDIOMS") or "0") or len(IDIOMS)
    idioms = IDIOMS[:max_i]
    print(f"=== LITERAL IDIOMS V2 (overlay) — {len(idioms)} idiomes ===\n")

    metas = []
    for idx, idiom in enumerate(idioms, 1):
        m = produce_design(idiom, idx)
        if m:
            metas.append(m)
        time.sleep(2)

    if metas:
        csv_path = OUTPUT_DIR / "etsy_bulk_upload.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["design_id", "language", "original",
                            "literal_translation", "actual_meaning",
                            "title", "tags_etsy", "price_etsy"],
                extrasaction="ignore",
            )
            w.writeheader()
            w.writerows(metas)

    print(f"\n  Produits : {len(metas)}/{len(idioms)} → {OUTPUT_DIR}")
    return 0 if metas else 1


if __name__ == "__main__":
    sys.exit(main())
