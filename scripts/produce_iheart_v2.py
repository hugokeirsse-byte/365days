"""
Pipeline I ❤️ X V2 — illustration EN FORME de cœur (pas en fond).

Évolution du I ❤️ X v1 : au lieu d'un cœur rouge plein + illustration
en fond, le cœur LUI-MÊME contient une scène thématique de la niche.

Exemple : I ❤️ Fishing → cœur contenant un pêcheur silhouette
au coucher de soleil ; I ❤️ Reading → cœur contenant une fille
qui lit dans un fauteuil cosy ; I ❤️ My Cat → cœur contenant
un chat dormant.

Concept beaucoup plus original et collectionable. Plus dur à copier
qu'un cœur plein générique.

Variables d'env :
  MAX_NICHES=8       limite à N niches
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
OUTPUT_DIR = ROOT / "products" / "iheart_v2"
USER_AGENT = "IHeartV2Producer/1.0"
TIMEOUT = 180

# Niches avec leur scène intra-cœur évocatrice
NICHES = [
    {"slug": "fishing", "label": "Fishing",
     "heart_scene": "silhouette of a fisherman casting his line at golden hour sunset, calm lake water reflection, mountains in background",
     "audience": "anglers fishermen"},
    {"slug": "reading", "label": "Reading",
     "heart_scene": "cozy scene of a person curled up in armchair reading book by warm lamp, stacks of books around, tea cup on side",
     "audience": "booktok readers"},
    {"slug": "my_cat", "label": "My Cat",
     "heart_scene": "cute sleepy cat curled up on a cozy windowsill with sunlight streaming, plant in background",
     "audience": "cat parents"},
    {"slug": "my_dog", "label": "My Dog",
     "heart_scene": "golden retriever sitting happily in a meadow with sunlight, tail wagging illustration",
     "audience": "dog parents"},
    {"slug": "hiking", "label": "Hiking",
     "heart_scene": "silhouette of hiker standing on mountain peak watching sunrise, valley below, dramatic landscape",
     "audience": "hikers backpackers"},
    {"slug": "camping", "label": "Camping",
     "heart_scene": "small tent next to glowing campfire at night under starry sky, pine forest silhouettes",
     "audience": "campers outdoor lovers"},
    {"slug": "coffee", "label": "Coffee",
     "heart_scene": "steaming coffee cup with latte art surrounded by morning light, croissant and book beside",
     "audience": "coffee lovers baristas"},
    {"slug": "gardening", "label": "Gardening",
     "heart_scene": "person tending to flowers in cottage garden, watering can and butterflies, soft morning light",
     "audience": "gardeners plant lovers"},
    {"slug": "crochet", "label": "Crochet",
     "heart_scene": "hands crocheting with colorful yarn balls scattered, finished doily emerging, cozy lamp light",
     "audience": "crocheters yarn lovers"},
    {"slug": "knitting", "label": "Knitting",
     "heart_scene": "hands knitting cozy scarf with multiple yarn balls, fireplace warmth in background",
     "audience": "knitters yarn lovers"},
    {"slug": "yoga", "label": "Yoga",
     "heart_scene": "silhouette of woman in tree pose at sunrise on mountaintop, lotus flower below",
     "audience": "yoga practitioners"},
    {"slug": "running", "label": "Running",
     "heart_scene": "silhouette of runner on coastal path at sunrise, ocean waves visible, dynamic motion",
     "audience": "runners marathoners"},
    {"slug": "horses", "label": "Horses",
     "heart_scene": "horse galloping freely through meadow with mane flowing, golden hour warmth",
     "audience": "horse riders equestrians"},
    {"slug": "baking", "label": "Baking",
     "heart_scene": "hands kneading dough on flour-dusted countertop, fresh bread and rolling pin nearby",
     "audience": "home bakers pastry lovers"},
    {"slug": "music", "label": "Music",
     "heart_scene": "vintage acoustic guitar leaning against amp with sheet music floating notes around",
     "audience": "musicians music lovers"},
    {"slug": "wine", "label": "Wine",
     "heart_scene": "wine glass on rustic table beside grape vine, vineyard at sunset in background",
     "audience": "wine lovers sommeliers"},
    {"slug": "dnd", "label": "D&D",
     "heart_scene": "dice rolling on ancient parchment map with magical dragon silhouette and candle",
     "audience": "tabletop roleplayers"},
    {"slug": "chess", "label": "Chess",
     "heart_scene": "vintage chess board with king piece prominent, soft window light, scholarly atmosphere",
     "audience": "chess players"},
    {"slug": "fall", "label": "Fall",
     "heart_scene": "cozy autumn scene with pumpkins maple leaves cinnamon stick mug of cider falling leaves",
     "audience": "autumn enthusiasts"},
    {"slug": "beach", "label": "Beach",
     "heart_scene": "tropical beach scene with palm trees crystal water and small sailboat on horizon",
     "audience": "beach lovers vacationers"},
]

# 3 styles visuels pour le cœur
HEART_STYLES = [
    {"key": "vintage_engraving",
     "name": "Vintage Engraving",
     "describe": "vintage engraved illustration style, fine line work, warm sepia tones with hint of red on heart outline, classic detailed etching aesthetic"},
    {"key": "watercolor_modern",
     "name": "Watercolor Modern",
     "describe": "soft watercolor illustration inside heart shape, gentle washes of color, modern editorial style, white background"},
    {"key": "minimalist_silhouette",
     "name": "Minimalist Silhouette",
     "describe": "minimalist silhouette illustration inside heart, single accent color, clean modern flat design, white background"},
]


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


def make_outputs(raw: Path, design_dir: Path) -> None:
    img = Image.open(raw).convert("RGB")
    side = min(img.width, img.height)
    off_x = (img.width - side) // 2
    off_y = (img.height - side) // 2
    sq = img.crop((off_x, off_y, off_x + side, off_y + side))
    sq.resize((1080, 1080), Image.LANCZOS).save(
        design_dir / "etsy_preview.jpg", "JPEG", quality=92)
    sq.resize((3000, 3000), Image.LANCZOS).save(
        design_dir / "print_3000.png", "PNG", optimize=True)
    ratio = 2400 / 3000
    h = img.height
    w = int(h * ratio)
    if w > img.width:
        w = img.width
        h = int(w / ratio)
    off_x = (img.width - w) // 2
    off_y = (img.height - h) // 2
    tee = img.crop((off_x, off_y, off_x + w, off_y + h))
    tee.resize((2400, 3000), Image.LANCZOS).save(
        design_dir / "tshirt_2400x3000.png", "PNG", optimize=True)


def produce_design(niche: dict, style: dict, idx: int) -> dict | None:
    prompt = (
        f"poster design centered on a large bold heart-shaped frame, "
        f"inside the heart shape there is an illustration of {niche['heart_scene']}, "
        f"above the heart big bold text 'I' and below the heart big bold text "
        f"'{niche['label']}', so the design reads 'I [heart] {niche['label']}', "
        f"the heart is the visual centerpiece containing the scene, "
        f"style: {style['describe']}, "
        f"clean composition for t-shirt and poster, no watermark no signature"
    )
    design_dir = OUTPUT_DIR / niche["slug"] / style["key"]
    design_dir.mkdir(parents=True, exist_ok=True)
    raw = design_dir / "raw.png"
    seed = idx * 10041 + random.randint(0, 9999)
    url = pollinations_url(prompt, seed)

    print(f"  [{idx:>3}] I ❤️ {niche['label']} → {style['name']}")
    if not http_get(url, raw):
        print(f"        echec Pollinations")
        return None

    try:
        make_outputs(raw, design_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"        traitement echoue : {exc}")
        return None
    finally:
        if raw.exists():
            raw.unlink()

    title = (f"I Love {niche['label']} Print — Scene Inside Heart "
             f"{style['name']} Gift for {niche['audience'].title()}")
    tags = [
        f"i love {niche['label'].lower()}",
        f"{niche['slug'].replace('_', ' ')} gift",
        f"{niche['audience']}",
        "heart illustration",
        "wall art print",
        "tshirt design",
        style["name"].lower(),
        "digital download",
        f"{niche['label'].lower()} lover",
        "unique gift idea",
        "scene in heart",
        "personalized art",
        "redbubble pod",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"iheart_v2_{niche['slug']}_{style['key']}",
        "niche": niche["slug"],
        "niche_label": niche["label"],
        "audience": niche["audience"],
        "style": style["key"],
        "concept": "heart-shaped frame containing thematic scene",
        "title": title[:140],
        "tags_etsy": ", ".join(tags),
        "price_etsy": 4.50,
        "files_included": (
            "etsy_preview.jpg (1080x1080), print_3000.png (3000x3000), "
            "tshirt_2400x3000.png (Printful)"
        ),
        "prompt_used": prompt,
        "seed": seed,
    }
    (design_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    max_n = int(os.environ.get("MAX_NICHES") or "0") or len(NICHES)
    max_s = int(os.environ.get("MAX_STYLES") or "0") or len(HEART_STYLES)
    niches = NICHES[:max_n]
    styles = HEART_STYLES[:max_s]
    total = len(niches) * len(styles)
    print(f"=== I ❤️ X V2 (scene dans le cœur) — {len(niches)} niches × "
          f"{len(styles)} styles = {total} designs ===\n")

    metas = []
    idx = 0
    for niche in niches:
        for style in styles:
            idx += 1
            m = produce_design(niche, style, idx)
            if m:
                metas.append(m)
            time.sleep(2)

    if metas:
        csv_path = OUTPUT_DIR / "etsy_bulk_upload.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["design_id", "niche", "style", "title",
                            "tags_etsy", "price_etsy"],
                extrasaction="ignore",
            )
            w.writeheader()
            w.writerows(metas)

    print(f"\n{'=' * 60}")
    print(f"  Produits : {len(metas)}/{total}")
    print(f"  Dossier  : {OUTPUT_DIR}")
    return 0 if metas else 1


if __name__ == "__main__":
    sys.exit(main())
