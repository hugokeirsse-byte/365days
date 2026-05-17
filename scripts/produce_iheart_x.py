"""
Pipeline I ❤️ X — designs "I LOVE [niche]" avec illustration de fond.

Bestseller éternel sur Etsy/Redbubble/Printful : merch "I ❤️ Reading",
"I ❤️ My Cat", "I ❤️ Crochet"… La force de cette niche : public ultra
captif, achat-cadeau récurrent, design ultra simple à décliner.

Notre angle différencié : pas juste "I ❤️ X" en typo plate, mais avec
illustration thématique en fond léger + cadrage moderne. Ça rend chaque
design plus premium et plus visuellement riche.

Pour chaque niche : 4 variants visuels (style fond + couleur du cœur +
ambiance). Soit ~80 designs sur 20 niches.

Variables d'env :
  MAX_NICHES=5      limite à N niches
  MAX_VARIANTS=2    limite à N variants par niche
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
OUTPUT_DIR = ROOT / "products" / "iheart"
USER_AGENT = "IHeartProducer/1.0"
TIMEOUT = 180

# 24 niches I ❤️ X à fort potentiel
NICHES = [
    # Hobbies créatifs
    {"slug": "reading", "label": "Reading", "bg": "open vintage books with bookmarks and reading glasses watercolor illustration",
     "audience": "booktok readers"},
    {"slug": "crochet", "label": "Crochet", "bg": "vintage crochet hooks yarn balls and finished doilies hand-painted illustration",
     "audience": "crocheters"},
    {"slug": "knitting", "label": "Knitting", "bg": "knitting needles yarn balls and cozy scarves watercolor illustration",
     "audience": "knitters"},
    {"slug": "embroidery", "label": "Embroidery", "bg": "embroidery hoops floss skeins and floral stitches illustration",
     "audience": "embroiderers"},
    {"slug": "gardening", "label": "Gardening", "bg": "watercolor garden tools terracotta pots and seedlings",
     "audience": "gardeners"},
    {"slug": "baking", "label": "Baking", "bg": "watercolor whisks rolling pins flour clouds and cupcakes",
     "audience": "home bakers"},
    {"slug": "painting", "label": "Painting", "bg": "watercolor palette brushes and paint splashes",
     "audience": "amateur painters"},
    # Animaux
    {"slug": "my_cat", "label": "My Cat", "bg": "cute watercolor cat faces in different breeds soft pastel palette",
     "audience": "cat parents"},
    {"slug": "my_dog", "label": "My Dog", "bg": "cute watercolor dog faces different breeds soft pastel palette",
     "audience": "dog parents"},
    {"slug": "horses", "label": "Horses", "bg": "watercolor horse heads and horseshoes warm earth palette",
     "audience": "horse lovers"},
    {"slug": "chickens", "label": "Chickens", "bg": "cute watercolor chickens eggs and farm elements soft palette",
     "audience": "backyard chicken keepers"},
    # Lifestyle / wellness
    {"slug": "yoga", "label": "Yoga", "bg": "watercolor lotus poses mandala and zen elements pastel",
     "audience": "yoga practitioners"},
    {"slug": "coffee", "label": "Coffee", "bg": "watercolor coffee cups beans and steam swirls warm sepia",
     "audience": "coffee lovers"},
    {"slug": "tea", "label": "Tea", "bg": "watercolor teapots cups and herbal leaves soft palette",
     "audience": "tea drinkers"},
    {"slug": "wine", "label": "Wine", "bg": "watercolor wine bottles grapes glasses burgundy palette",
     "audience": "wine lovers"},
    # Hobbies geeks
    {"slug": "dnd", "label": "D&D", "bg": "watercolor dice scrolls dragons swords fantasy palette",
     "audience": "tabletop gamers"},
    {"slug": "chess", "label": "Chess", "bg": "watercolor chess pieces on board sepia and ivory",
     "audience": "chess players"},
    {"slug": "puzzles", "label": "Puzzles", "bg": "watercolor jigsaw pieces and crossword grids pastel",
     "audience": "puzzle solvers"},
    # Identité
    {"slug": "being_a_mom", "label": "Being a Mom", "bg": "watercolor family icons hearts and stars soft pastel",
     "audience": "moms"},
    {"slug": "being_a_dad", "label": "Being a Dad", "bg": "watercolor tools fishing rods and BBQ icons warm tones",
     "audience": "dads"},
    {"slug": "being_a_grandma", "label": "Being a Grandma", "bg": "watercolor knitting tea cups and flowers soft palette",
     "audience": "grandmothers"},
    {"slug": "being_a_teacher", "label": "Being a Teacher", "bg": "watercolor apples chalkboard pencils and books",
     "audience": "teachers"},
    {"slug": "being_a_nurse", "label": "Being a Nurse", "bg": "watercolor stethoscope hearts caduceus and bandages soft palette",
     "audience": "nurses"},
    {"slug": "fall", "label": "Fall", "bg": "watercolor pumpkins maple leaves acorns warm autumn palette",
     "audience": "autumn enthusiasts"},
]

# 4 variants de style visuel
VARIANTS = [
    {
        "key": "watercolor_pastel",
        "name": "Watercolor Pastel",
        "heart_color": "soft watercolor pink and coral red",
        "typography": "elegant rounded serif",
        "bg_intensity": "very soft faded background, generous white space, watercolor wash light",
        "palette": "soft pastel watercolor palette",
    },
    {
        "key": "vintage_bold",
        "name": "Vintage Bold",
        "heart_color": "deep vintage red with subtle paper texture",
        "typography": "bold vintage sans-serif",
        "bg_intensity": "faded sepia background, slightly grungy texture",
        "palette": "vintage sepia and brick red palette",
    },
    {
        "key": "modern_minimalist",
        "name": "Modern Minimalist",
        "heart_color": "clean flat red minimalist heart",
        "typography": "ultra-modern geometric sans-serif",
        "bg_intensity": "very minimal background, single icon barely visible, ultra clean",
        "palette": "monochrome black and red on pure white",
    },
    {
        "key": "boho_floral",
        "name": "Boho Floral",
        "heart_color": "heart made of small flowers and leaves",
        "typography": "hand-lettered boho serif",
        "bg_intensity": "delicate floral wreath frame around composition",
        "palette": "boho earth tones with mustard and terracotta",
    },
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
    # T-shirt safe area : portrait 2400x3000
    img_p = img.copy()
    ratio = 2400 / 3000
    h = img_p.height
    w = int(h * ratio)
    if w > img_p.width:
        w = img_p.width
        h = int(w / ratio)
    off_x = (img_p.width - w) // 2
    off_y = (img_p.height - h) // 2
    tee = img_p.crop((off_x, off_y, off_x + w, off_y + h))
    tee.resize((2400, 3000), Image.LANCZOS).save(
        design_dir / "tshirt_2400x3000.png", "PNG", optimize=True)


def produce_design(niche: dict, variant: dict, idx: int) -> dict | None:
    prompt = (
        f"poster design with bold large text 'I' then a stylized heart symbol "
        f"then text '{niche['label']}', three elements stacked vertically, "
        f"the heart is {variant['heart_color']}, typography style {variant['typography']}, "
        f"background features {niche['bg']}, "
        f"{variant['bg_intensity']}, {variant['palette']}, "
        f"professional commercial illustration, no watermark no signature, "
        f"clean composition for t-shirt and poster"
    )
    design_dir = OUTPUT_DIR / niche["slug"] / variant["key"]
    design_dir.mkdir(parents=True, exist_ok=True)
    raw = design_dir / "raw.png"
    seed = idx * 10009 + random.randint(0, 9999)
    url = pollinations_url(prompt, seed)

    print(f"  [{idx:>3}] I ❤️ {niche['label']} → {variant['name']}")
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

    title = (f"I Love {niche['label']} Print — {variant['name']} "
             f"Gift for {niche['audience'].title()}")
    tags = [
        f"i love {niche['label'].lower()}",
        f"{niche['slug'].replace('_', ' ')} gift",
        f"{niche['audience']}",
        "wall art print",
        "tshirt design",
        "gift idea",
        variant["name"].lower(),
        "digital download",
        f"{niche['label'].lower()} lover",
        "mug design",
        "tote bag print",
        "sticker design",
        "redbubble pod",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"iheart_{niche['slug']}_{variant['key']}",
        "niche": niche["slug"],
        "niche_label": niche["label"],
        "audience": niche["audience"],
        "variant": variant["key"],
        "title": title[:140],
        "tags_etsy": ", ".join(tags),
        "price_etsy": 3.50,
        "files_included": (
            "etsy_preview.jpg (1080x1080), print_3000.png (3000x3000 @ 300dpi), "
            "tshirt_2400x3000.png (Printful t-shirt format)"
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
    max_v = int(os.environ.get("MAX_VARIANTS") or "0") or len(VARIANTS)
    niches = NICHES[:max_n]
    variants = VARIANTS[:max_v]
    total = len(niches) * len(variants)
    print(f"=== I ❤️ X — {len(niches)} niches × {len(variants)} variants "
          f"= {total} designs ===\n")

    metas = []
    idx = 0
    for niche in niches:
        for variant in variants:
            idx += 1
            m = produce_design(niche, variant, idx)
            if m:
                metas.append(m)
            time.sleep(2)

    if metas:
        csv_path = OUTPUT_DIR / "etsy_bulk_upload.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["design_id", "niche", "variant", "title",
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
