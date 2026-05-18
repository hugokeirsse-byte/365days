"""
Pipeline I ❤️ X V3 — illustration cœur-scène SANS texte généré.

Évolution V3 (problème V2 résolu) : Flux ne sait pas faire de texte
fiable, donc on génère UNIQUEMENT l'illustration (cœur + scène
thématique) sans aucun texte, puis on overlay « I ❤️ {niche} »
avec Pillow et une vraie police TTF. Texte garanti correct.

Layout :
- Haut (5-10% hauteur) : « I »
- Milieu (60-70%) : illustration cœur-scène générée par Pollinations
- Bas (10-15%) : « {Niche label} »
- Symbole ❤️ : dans le cœur naturel de l'illustration

Variables d'env :
  MAX_NICHES=8       limite à N niches
  MAX_STYLES=2       limite à N styles
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
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERREUR : Pillow non installé")
    sys.exit(2)


# === PIPELINE EN PAUSE ===
# Pollinations rend des résultats trop variables pour ce pipeline.
# Réactiver dès que HF_API_KEY est dispo (script produce_iheart_hf.py).
# Cf. STRATEGY.md section "Pipelines EN PAUSE".
import os as _os
if _os.environ.get('FORCE_RUN') != '1':
    print('⏸ PAUSED until HF_API_KEY available. Set FORCE_RUN=1 to bypass.')
    raise SystemExit(0)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "iheart_v3"
USER_AGENT = "IHeartV3Producer/1.0"
TIMEOUT = 180

# Mêmes niches que V2
NICHES = [
    {"slug": "fishing", "label": "Fishing",
     "heart_scene": "silhouette of a fisherman casting his line at golden hour sunset, calm lake reflection, mountains in background",
     "audience": "anglers fishermen"},
    {"slug": "reading", "label": "Reading",
     "heart_scene": "cozy scene of a person reading in armchair by warm lamp, stacks of books, tea cup",
     "audience": "booktok readers"},
    {"slug": "my_cat", "label": "My Cat",
     "heart_scene": "cute sleepy cat curled on cozy windowsill with sunlight, plant in background",
     "audience": "cat parents"},
    {"slug": "my_dog", "label": "My Dog",
     "heart_scene": "golden retriever sitting happily in meadow with sunlight, tail wagging",
     "audience": "dog parents"},
    {"slug": "hiking", "label": "Hiking",
     "heart_scene": "silhouette of hiker on mountain peak watching sunrise, valley below",
     "audience": "hikers backpackers"},
    {"slug": "camping", "label": "Camping",
     "heart_scene": "small tent next to glowing campfire at night, starry sky, pine silhouettes",
     "audience": "campers outdoor lovers"},
    {"slug": "coffee", "label": "Coffee",
     "heart_scene": "steaming coffee cup with latte art in morning light, croissant beside",
     "audience": "coffee lovers"},
    {"slug": "gardening", "label": "Gardening",
     "heart_scene": "person tending flowers in cottage garden, watering can, butterflies",
     "audience": "gardeners plant lovers"},
    {"slug": "crochet", "label": "Crochet",
     "heart_scene": "hands crocheting with colorful yarn balls scattered, finished doily, cozy lamp light",
     "audience": "crocheters"},
    {"slug": "knitting", "label": "Knitting",
     "heart_scene": "hands knitting cozy scarf with yarn balls, fireplace warmth in background",
     "audience": "knitters"},
    {"slug": "yoga", "label": "Yoga",
     "heart_scene": "silhouette of woman in tree pose at sunrise on mountaintop",
     "audience": "yoga practitioners"},
    {"slug": "running", "label": "Running",
     "heart_scene": "silhouette of runner on coastal path at sunrise, ocean waves",
     "audience": "runners"},
    {"slug": "horses", "label": "Horses",
     "heart_scene": "horse galloping in meadow with mane flowing, golden hour",
     "audience": "horse riders"},
    {"slug": "baking", "label": "Baking",
     "heart_scene": "hands kneading dough on flour-dusted counter, fresh bread, rolling pin",
     "audience": "home bakers"},
    {"slug": "wine", "label": "Wine",
     "heart_scene": "wine glass on rustic table beside grape vine, vineyard at sunset",
     "audience": "wine lovers"},
    {"slug": "dnd", "label": "D&D",
     "heart_scene": "dice rolling on parchment map with magical dragon silhouette and candle",
     "audience": "tabletop roleplayers"},
    {"slug": "chess", "label": "Chess",
     "heart_scene": "vintage chess board with king prominent, soft window light",
     "audience": "chess players"},
    {"slug": "fall", "label": "Fall",
     "heart_scene": "cozy autumn scene with pumpkins maple leaves cinnamon mug falling leaves",
     "audience": "autumn lovers"},
    {"slug": "beach", "label": "Beach",
     "heart_scene": "tropical beach with palm trees crystal water small sailboat",
     "audience": "beach lovers"},
    {"slug": "music", "label": "Music",
     "heart_scene": "vintage acoustic guitar leaning against amp with floating music notes",
     "audience": "musicians"},
]

# Styles visuels — adapt to "no text in image"
HEART_STYLES = [
    {"key": "vintage_engraving",
     "name": "Vintage Engraving",
     "describe": "vintage engraved illustration centered on heart-shaped frame, fine line work, warm sepia tones with red on heart outline, classic detailed etching aesthetic, ABSOLUTELY NO TEXT NO LETTERS NO WORDS in the entire image",
     "text_color": (60, 30, 20),  # dark sepia
     "bg_color": None,  # use illustration bg
     "heart_color": "vintage red"},
    {"key": "watercolor_modern",
     "name": "Watercolor Modern",
     "describe": "soft watercolor illustration inside heart-shaped frame, gentle color washes, modern editorial style, white background, ABSOLUTELY NO TEXT NO LETTERS NO WORDS in the entire image",
     "text_color": (40, 40, 40),
     "bg_color": (255, 252, 248),
     "heart_color": "soft coral pink"},
    {"key": "minimalist_silhouette",
     "name": "Minimalist Silhouette",
     "describe": "minimalist silhouette inside heart-shaped frame, single accent color, clean modern flat design, white background, ABSOLUTELY NO TEXT NO LETTERS NO WORDS in the entire image",
     "text_color": (20, 20, 20),
     "bg_color": (255, 255, 255),
     "heart_color": "minimalist red"},
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


def find_font(preferred_paths: list[str], size: int):
    paths = preferred_paths + [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Georgia.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def compose_iheart_design(illustration_path: Path, dest_path: Path,
                           niche: dict, style: dict, canvas_size: int = 3000) -> None:
    """Compose le design final avec overlay Pillow.

    Layout : « I » en haut, ❤️ centré gros, illustration au milieu,
    « {Niche label} » en bas.
    """
    # Charger l'illustration
    illust = Image.open(illustration_path).convert("RGB")
    # Crop carré centré
    side = min(illust.width, illust.height)
    off_x = (illust.width - side) // 2
    off_y = (illust.height - side) // 2
    illust = illust.crop((off_x, off_y, off_x + side, off_y + side))

    # Resize illustration au cœur du canvas (70% taille)
    illust_size = int(canvas_size * 0.72)
    illust = illust.resize((illust_size, illust_size), Image.LANCZOS)

    # Canvas final
    if style["bg_color"]:
        canvas = Image.new("RGB", (canvas_size, canvas_size), style["bg_color"])
    else:
        # Si bg None : on prend la couleur dominante de l'illustration
        canvas = Image.new("RGB", (canvas_size, canvas_size), (250, 245, 235))

    # Paste illustration centrée
    paste_x = (canvas_size - illust_size) // 2
    paste_y = (canvas_size - illust_size) // 2 + int(canvas_size * 0.02)
    canvas.paste(illust, (paste_x, paste_y))

    draw = ImageDraw.Draw(canvas)

    # Choix de typo selon style
    if style["key"] == "vintage_engraving":
        font_main = find_font(
            ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"], 280)
        font_niche = find_font(
            ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"], 260)
    elif style["key"] == "minimalist_silhouette":
        font_main = find_font(
            ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"], 280)
        font_niche = find_font(
            ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"], 260)
    else:  # watercolor_modern
        font_main = find_font(
            ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"], 280)
        font_niche = find_font(
            ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"], 250)

    text_color = style["text_color"]

    # « I » en haut à gauche
    i_text = "I"
    bbox = draw.textbbox((0, 0), i_text, font=font_main)
    i_w = bbox[2] - bbox[0]
    draw.text(
        (paste_x - int(canvas_size * 0.08), paste_y - int(canvas_size * 0.06)),
        i_text, fill=text_color, font=font_main,
    )

    # ❤️ symbole : on dessine un cœur Pillow (pas d'emoji car les fonts
    # système ne le rendent pas toujours). On le met en haut centre.
    heart_w = int(canvas_size * 0.16)
    heart_color = (200, 30, 50) if style["key"] != "vintage_engraving" \
        else (130, 30, 30)
    draw_heart(draw,
               x=canvas_size // 2 - heart_w // 2,
               y=paste_y - int(canvas_size * 0.04) - heart_w // 4,
               w=heart_w, h=heart_w, color=heart_color)

    # Label de la niche en bas
    niche_text = niche["label"].upper()
    bbox = draw.textbbox((0, 0), niche_text, font=font_niche)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((canvas_size - text_w) // 2,
         paste_y + illust_size + int(canvas_size * 0.02)),
        niche_text, fill=text_color, font=font_niche,
    )

    canvas.save(dest_path, "PNG", optimize=True)


def draw_heart(draw, x, y, w, h, color):
    """Dessine un cœur plein via 2 cercles + 1 triangle."""
    # 2 cercles côte à côte
    r = w // 4
    draw.ellipse([x, y, x + 2*r, y + 2*r], fill=color)
    draw.ellipse([x + w - 2*r, y, x + w, y + 2*r], fill=color)
    # Triangle pour la pointe du bas
    draw.polygon([
        (x, y + r),
        (x + w, y + r),
        (x + w // 2, y + h),
    ], fill=color)


def make_outputs(composed: Path, design_dir: Path) -> None:
    img = Image.open(composed).convert("RGB")
    img.resize((1080, 1080), Image.LANCZOS).save(
        design_dir / "etsy_preview.jpg", "JPEG", quality=92)
    # Le composed est déjà en 3000x3000, on le garde tel quel
    if composed.name != "print_3000.png":
        shutil_copy(composed, design_dir / "print_3000.png")
    # T-shirt portrait
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


def shutil_copy(src: Path, dest: Path) -> None:
    import shutil
    shutil.copy2(str(src), str(dest))


def produce_design(niche: dict, style: dict, idx: int) -> dict | None:
    # Prompt INSISTE sur "no text" pour éviter les artefacts texte de Flux
    prompt = (
        f"{style['describe']}, "
        f"scene inside heart shape: {niche['heart_scene']}, "
        f"centered composition, professional commercial illustration"
    )
    design_dir = OUTPUT_DIR / niche["slug"] / style["key"]
    design_dir.mkdir(parents=True, exist_ok=True)
    raw = design_dir / "raw_illust.png"
    final_print = design_dir / "print_3000.png"
    seed = idx * 10059 + random.randint(0, 9999)
    url = pollinations_url(prompt, seed)

    print(f"  [{idx:>3}] I ❤️ {niche['label']} → {style['name']}")
    if not http_get(url, raw):
        print(f"        echec Pollinations illustration")
        return None

    try:
        compose_iheart_design(raw, final_print, niche, style, canvas_size=3000)
        make_outputs(final_print, design_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"        compose echoue : {exc}")
        return None
    finally:
        if raw.exists():
            raw.unlink()

    title = (f"I Love {niche['label']} Print — {style['name']} "
             f"Gift for {niche['audience'].title()}")
    tags = [
        f"i love {niche['label'].lower()}",
        f"{niche['slug'].replace('_', ' ')} gift",
        f"{niche['audience']}",
        "scene in heart",
        "wall art print",
        "tshirt design",
        style["name"].lower(),
        "digital download",
        f"{niche['label'].lower()} lover",
        "unique gift",
        "modern art",
        "redbubble pod",
        "instant download",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"iheart_v3_{niche['slug']}_{style['key']}",
        "version": "v3",
        "text_overlay_method": "pillow",  # ← important pour audit visuel
        "niche": niche["slug"],
        "niche_label": niche["label"],
        "audience": niche["audience"],
        "style": style["key"],
        "concept": "heart-shaped scene + Pillow text overlay (gibberish-proof)",
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
    print(f"=== I ❤️ X V3 (text overlay Pillow, gibberish-proof) — "
          f"{len(niches)} niches × {len(styles)} styles = {total} designs ===\n")

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
