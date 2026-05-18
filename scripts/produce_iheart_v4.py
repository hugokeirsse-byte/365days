"""
Pipeline I ❤️ X V4 — illustration EN FORME DE CŒUR (Pillow mask).

Évolution V4 (différent de V3) : l'illustration thématique est croppée
en forme de cœur via masque Pillow, sans cadre visible. Le texte I + NICHE
est placé autour. Style plus moderne et plus original.

Concept : « I [Cœur en forme d'image] FISHING » où le cœur EST
littéralement l'image du pêcheur au coucher de soleil.

V3 garde l'illustration dans un CADRE cœur visible. V4 transforme
l'illustration EN cœur. Les deux coexistent pour A/B test.
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
from lib.design_composer import compose_design, get_layout, \
    DesignLayout, IllustrationPlacement, TextZone, DecorativeElement  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "iheart_v4"
USER_AGENT = "IHeartV4/1.0"
TIMEOUT = 180

NICHES = [
    {"slug": "fishing", "label": "Fishing",
     "scene": "wide horizontal landscape silhouette of fisherman casting line at golden hour sunset on calm lake, mountains background",
     "audience": "anglers"},
    {"slug": "reading", "label": "Reading",
     "scene": "cozy scene of person reading in warm armchair by lamp, book stacks, tea cup, warm tones",
     "audience": "booktok readers"},
    {"slug": "my_cat", "label": "My Cat",
     "scene": "cute sleeping orange tabby cat curled on cozy blanket with sunlight, soft warm pastel palette",
     "audience": "cat parents"},
    {"slug": "my_dog", "label": "My Dog",
     "scene": "happy golden retriever in meadow with sunlight and flowers warm cheerful palette",
     "audience": "dog parents"},
    {"slug": "hiking", "label": "Hiking",
     "scene": "silhouette of hiker on mountain peak watching sunrise, dramatic landscape, warm golden palette",
     "audience": "hikers"},
    {"slug": "camping", "label": "Camping",
     "scene": "small tent next to glowing campfire under starry night sky, pine forest silhouettes, warm orange glow",
     "audience": "campers"},
    {"slug": "coffee", "label": "Coffee",
     "scene": "steaming coffee cup on rustic wood table with morning light, croissant, warm brown palette",
     "audience": "coffee lovers"},
    {"slug": "gardening", "label": "Gardening",
     "scene": "person tending colorful flowers in cottage garden with watering can, butterflies, soft pastel light",
     "audience": "gardeners"},
    {"slug": "yoga", "label": "Yoga",
     "scene": "silhouette of woman in tree pose at sunrise on mountaintop, peaceful warm palette",
     "audience": "yoga practitioners"},
    {"slug": "wine", "label": "Wine",
     "scene": "wine glass on rustic table beside grape vine, vineyard at golden hour sunset, warm tones",
     "audience": "wine lovers"},
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


def make_outputs(composed: Path, design_dir: Path) -> None:
    from PIL import Image
    img = Image.open(composed).convert("RGB")
    img.resize((1080, 1080), Image.LANCZOS).save(
        design_dir / "etsy_preview.jpg", "JPEG", quality=92)
    # T-shirt format
    ratio = 2400 / 3000
    h = img.height
    w_t = int(h * ratio)
    if w_t > img.width:
        w_t = img.width
        h = int(w_t / ratio)
    off_x = (img.width - w_t) // 2
    off_y = (img.height - h) // 2
    tee = img.crop((off_x, off_y, off_x + w_t, off_y + h))
    tee.resize((2400, 3000), Image.LANCZOS).save(
        design_dir / "tshirt_2400x3000.png", "PNG", optimize=True)


def produce_design(niche: dict, idx: int) -> dict | None:
    # Prompt : scène thématique CARRÉE pour le masque cœur
    illust_prompt = (
        f"{niche['scene']}, square composition centered, "
        f"high quality detailed illustration, ABSOLUTELY NO TEXT NO LETTERS NO HEART SYMBOLS in the image, "
        f"vibrant colors, no border no frame"
    )
    design_dir = OUTPUT_DIR / niche["slug"]
    design_dir.mkdir(parents=True, exist_ok=True)
    illust_path = design_dir / "raw_illust.png"
    final = design_dir / "print_3000.png"
    seed = idx * 10133 + random.randint(0, 9999)

    print(f"  [{idx:>3}] I ❤️ {niche['label']}")
    if not http_get(pollinations_url(illust_prompt, seed), illust_path):
        print(f"        echec Pollinations")
        return None

    try:
        layout = get_layout("iheart_masked")
        compose_design(
            layout=layout,
            illustration_path=illust_path,
            text_values={
                "I": "I",
                "niche": niche["label"],
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

    title = (f"I Love {niche['label']} Print — Heart-Shaped Scene "
             f"Modern Gift for {niche['audience'].title()}")[:140]
    tags = [
        f"i love {niche['label'].lower()}",
        f"{niche['slug'].replace('_', ' ')} gift",
        niche["audience"],
        "heart shaped art",
        "wall art print",
        "tshirt design",
        "modern minimalist",
        "digital download",
        f"{niche['label'].lower()} lover",
        "unique gift idea",
        "scene in heart",
        "redbubble pod",
        "instant download",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"iheart_v4_{niche['slug']}",
        "version": "v4",
        "text_overlay_method": "pillow",
        "concept": "illustration cropped INTO heart shape via Pillow mask",
        "niche": niche["slug"],
        "niche_label": niche["label"],
        "audience": niche["audience"],
        "title": title,
        "tags_etsy": ", ".join(tags),
        "price_etsy": 4.50,
        "files_included": "etsy_preview.jpg, print_3000.png, tshirt_2400x3000.png",
        "illust_prompt_used": illust_prompt,
        "seed": seed,
    }
    (design_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    max_n = int(os.environ.get("MAX_NICHES") or "0") or len(NICHES)
    niches = NICHES[:max_n]
    print(f"=== I ❤️ X V4 (heart mask) — {len(niches)} niches ===\n")

    metas = []
    for idx, niche in enumerate(niches, 1):
        m = produce_design(niche, idx)
        if m:
            metas.append(m)
        time.sleep(2)

    if metas:
        csv_path = OUTPUT_DIR / "etsy_bulk_upload.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["design_id", "niche", "title",
                            "tags_etsy", "price_etsy"],
                extrasaction="ignore",
            )
            w.writeheader()
            w.writerows(metas)

    print(f"\n  Produits : {len(metas)}/{len(niches)} → {OUTPUT_DIR}")
    return 0 if metas else 1


if __name__ == "__main__":
    sys.exit(main())
