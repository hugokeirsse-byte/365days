"""
Pipeline WEDDING STATIONERY — wildflower / garden romance / boho.

Trend Q2 2026 identifié par recherche web :
- Bridesmaid baskets boho garden : +4200% YoY (loveeattravelrepeat.com)
- Garden romance + wildflower wedding : explosion
- Soft Stitch Era embroidery aesthetic : +20000%

Suite de papeterie mariage prête à imprimer, par thème :
1. Save the date
2. Wedding invitation
3. RSVP card
4. Menu card
5. Place card / Table number
6. Thank you card

Sortie : suite PDF + PNG individuels haute résolution.
Texte personnalisable via Pillow overlay (date/lieux par template).

Niches saisonnières (mariage = mai-octobre = sweet spot 2026).
Marché : couples 25-40 ans, public américain principalement.

Variables d'env :
  THEME=wildflower_meadow   (wildflower_meadow, boho_desert, garden_romance,
                              vintage_botanical, soft_stitch_embroidery)
  MAX_ITEMS=6               nombre d'items dans la suite
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

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "wedding_stationery"
USER_AGENT = "WeddingStationeryProducer/1.0"
TIMEOUT = 180

# 5 thèmes wedding 2026 — trend-validated
THEMES = {
    "wildflower_meadow": {
        "name": "Wildflower Meadow",
        "bg_prompt": "soft watercolor wildflower meadow border illustration, daisies poppies cosmos coreopsis lavender, scattered loose botanical pattern, romantic garden aesthetic, soft pastel palette of dusty pink sage green and cream, ABSOLUTELY NO TEXT NO LETTERS NO WORDS in the entire image, decorative wedding invitation background",
        "palette_text": (90, 80, 70),
        "palette_accent": (180, 130, 140),
        "vibe": "wildflower wedding romantic garden",
    },
    "boho_desert": {
        "name": "Boho Desert",
        "bg_prompt": "boho desert wedding watercolor illustration, pampas grass eucalyptus dried flowers terracotta tones, soft sandy beige and warm rust palette, ABSOLUTELY NO TEXT NO LETTERS NO WORDS, decorative wedding invitation background",
        "palette_text": (80, 50, 35),
        "palette_accent": (190, 110, 70),
        "vibe": "boho bohemian desert wedding",
    },
    "garden_romance": {
        "name": "Garden Romance",
        "bg_prompt": "romantic garden wedding watercolor illustration, English garden roses peonies sweet peas, lush green foliage, dusty rose and emerald green palette, ABSOLUTELY NO TEXT NO LETTERS NO WORDS, decorative wedding invitation background",
        "palette_text": (60, 50, 60),
        "palette_accent": (170, 90, 100),
        "vibe": "garden romance vintage wedding",
    },
    "vintage_botanical": {
        "name": "Vintage Botanical",
        "bg_prompt": "vintage botanical wedding illustration, Victorian era pressed flowers herbs ferns, sepia and forest green palette, scientific book aesthetic, ABSOLUTELY NO TEXT NO LETTERS NO WORDS, decorative wedding invitation background",
        "palette_text": (45, 35, 25),
        "palette_accent": (90, 110, 70),
        "vibe": "vintage botanical wedding apothecary",
    },
    "soft_stitch_embroidery": {
        "name": "Soft Stitch Embroidery",
        "bg_prompt": "soft embroidery aesthetic illustration, delicate flowers cross-stitched look, warm cream linen background with thread accents, sage green dusty pink and gold palette, ABSOLUTELY NO TEXT NO LETTERS NO WORDS, decorative wedding invitation background",
        "palette_text": (75, 65, 55),
        "palette_accent": (155, 120, 100),
        "vibe": "embroidery aesthetic stitched wedding",
    },
}

# 6 items dans la suite (template texte)
SUITE_ITEMS = [
    {
        "key": "save_the_date",
        "name": "Save the Date",
        "size": (1500, 2100),  # ratio 5x7
        "text_layout": [
            {"text": "save the date", "size_ratio": 0.07, "y_ratio": 0.20, "weight": "light"},
            {"text": "[Couple Names]", "size_ratio": 0.12, "y_ratio": 0.35, "weight": "bold"},
            {"text": "are getting married", "size_ratio": 0.045, "y_ratio": 0.55, "weight": "light"},
            {"text": "[MM.DD.YYYY]", "size_ratio": 0.08, "y_ratio": 0.65, "weight": "bold"},
            {"text": "[City, State]", "size_ratio": 0.045, "y_ratio": 0.78, "weight": "light"},
            {"text": "Invitation to follow", "size_ratio": 0.035, "y_ratio": 0.88, "weight": "light"},
        ],
    },
    {
        "key": "wedding_invitation",
        "name": "Wedding Invitation",
        "size": (1500, 2100),
        "text_layout": [
            {"text": "together with their families", "size_ratio": 0.035, "y_ratio": 0.15, "weight": "light"},
            {"text": "[Couple Names]", "size_ratio": 0.10, "y_ratio": 0.27, "weight": "bold"},
            {"text": "invite you to celebrate", "size_ratio": 0.04, "y_ratio": 0.45, "weight": "light"},
            {"text": "their wedding", "size_ratio": 0.055, "y_ratio": 0.52, "weight": "bold"},
            {"text": "[Day, Month DD, YYYY]", "size_ratio": 0.045, "y_ratio": 0.65, "weight": "light"},
            {"text": "[Time]", "size_ratio": 0.04, "y_ratio": 0.72, "weight": "light"},
            {"text": "[Venue]", "size_ratio": 0.045, "y_ratio": 0.79, "weight": "bold"},
            {"text": "[Address]", "size_ratio": 0.035, "y_ratio": 0.85, "weight": "light"},
            {"text": "Reception to follow", "size_ratio": 0.03, "y_ratio": 0.92, "weight": "light"},
        ],
    },
    {
        "key": "rsvp_card",
        "name": "RSVP Card",
        "size": (2100, 1500),  # paysage
        "text_layout": [
            {"text": "Please reply by [MM.DD]", "size_ratio": 0.04, "y_ratio": 0.20, "weight": "light"},
            {"text": "[Guest Name]", "size_ratio": 0.05, "y_ratio": 0.32, "weight": "bold"},
            {"text": "□ Joyfully accepts", "size_ratio": 0.04, "y_ratio": 0.50, "weight": "light"},
            {"text": "□ Regretfully declines", "size_ratio": 0.04, "y_ratio": 0.60, "weight": "light"},
            {"text": "Number of guests: ___", "size_ratio": 0.035, "y_ratio": 0.75, "weight": "light"},
        ],
    },
    {
        "key": "menu_card",
        "name": "Menu Card",
        "size": (1500, 2100),
        "text_layout": [
            {"text": "menu", "size_ratio": 0.10, "y_ratio": 0.13, "weight": "bold"},
            {"text": "first course", "size_ratio": 0.04, "y_ratio": 0.27, "weight": "light"},
            {"text": "[Dish description]", "size_ratio": 0.035, "y_ratio": 0.32, "weight": "light"},
            {"text": "main course", "size_ratio": 0.04, "y_ratio": 0.46, "weight": "light"},
            {"text": "[Dish description]", "size_ratio": 0.035, "y_ratio": 0.51, "weight": "light"},
            {"text": "dessert", "size_ratio": 0.04, "y_ratio": 0.65, "weight": "light"},
            {"text": "[Dish description]", "size_ratio": 0.035, "y_ratio": 0.70, "weight": "light"},
            {"text": "[Couple Initials]", "size_ratio": 0.045, "y_ratio": 0.88, "weight": "bold"},
        ],
    },
    {
        "key": "place_card",
        "name": "Place Card",
        "size": (2100, 1050),  # paysage très fin (folded card)
        "text_layout": [
            {"text": "[Guest Name]", "size_ratio": 0.10, "y_ratio": 0.45, "weight": "bold"},
            {"text": "Table [N]", "size_ratio": 0.05, "y_ratio": 0.70, "weight": "light"},
        ],
    },
    {
        "key": "thank_you_card",
        "name": "Thank You Card",
        "size": (1500, 2100),
        "text_layout": [
            {"text": "thank you", "size_ratio": 0.12, "y_ratio": 0.30, "weight": "bold"},
            {"text": "for celebrating with us", "size_ratio": 0.04, "y_ratio": 0.48, "weight": "light"},
            {"text": "[Couple Names]", "size_ratio": 0.05, "y_ratio": 0.78, "weight": "bold"},
        ],
    },
]


def pollinations_url(prompt: str, seed: int, w: int = 1024, h: int = 1440) -> str:
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


def find_font(weight: str, size: int):
    """Choix de typo : 'bold' = serif bold pour les noms/titres,
    'light' = serif normal pour le corps."""
    if weight == "bold":
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf",
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def compose_item(bg_path: Path, item: dict, theme: dict, dest: Path) -> None:
    """Compose un item de papeterie : fond + texte overlay centré."""
    w, h = item["size"]
    bg = Image.open(bg_path).convert("RGB")
    # Crop/resize au format demandé
    bg_ratio = bg.width / bg.height
    target_ratio = w / h
    if bg_ratio > target_ratio:
        new_w = int(bg.height * target_ratio)
        off = (bg.width - new_w) // 2
        bg = bg.crop((off, 0, off + new_w, bg.height))
    else:
        new_h = int(bg.width / target_ratio)
        off = (bg.height - new_h) // 2
        bg = bg.crop((0, off, bg.width, off + new_h))
    bg = bg.resize((w, h), Image.LANCZOS)

    # Overlay légère blanchâtre pour rehausser le texte
    overlay = Image.new("RGBA", (w, h), (255, 250, 245, 60))
    canvas = bg.convert("RGBA")
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    text_color = theme["palette_text"] + (255,)
    accent_color = theme["palette_accent"] + (255,)

    for layout in item["text_layout"]:
        text = layout["text"]
        size = int(min(w, h) * layout["size_ratio"])
        y = int(h * layout["y_ratio"])
        font = find_font(layout["weight"], size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        x = (w - text_w) // 2
        # Couleur accent pour les "bold" qui contiennent [...] placeholders
        color = accent_color if "[" in text else text_color
        draw.text((x, y), text, fill=color, font=font)

    canvas.convert("RGB").save(dest, "PNG", optimize=True)


def produce_item(theme_key: str, theme: dict, item: dict, idx: int) -> dict | None:
    item_dir = OUTPUT_DIR / theme_key / item["key"]
    item_dir.mkdir(parents=True, exist_ok=True)
    bg_path = item_dir / "raw_bg.png"
    final = item_dir / f"{item['key']}.png"
    seed = idx * 10091 + random.randint(0, 9999)
    url = pollinations_url(theme["bg_prompt"], seed,
                            w=1024, h=1440 if item["size"][1] > item["size"][0] else 720)

    print(f"  [{idx:>2}] {theme['name']} / {item['name']}")
    if not http_get(url, bg_path):
        print(f"         echec Pollinations bg")
        return None

    try:
        compose_item(bg_path, item, theme, final)
        # Preview Etsy carré 1080
        img = Image.open(final).convert("RGB")
        side = min(img.width, img.height)
        ox = (img.width - side) // 2
        oy = (img.height - side) // 2
        sq = img.crop((ox, oy, ox + side, oy + side))
        sq.resize((1080, 1080), Image.LANCZOS).save(
            item_dir / "etsy_preview.jpg", "JPEG", quality=92)
    except Exception as exc:  # noqa: BLE001
        print(f"         compose echoue : {exc}")
        return None
    finally:
        if bg_path.exists():
            bg_path.unlink()

    title = (f"{item['name']} Template — {theme['name']} Wedding "
             f"Stationery Printable Editable")
    tags = [
        f"{item['key'].replace('_', ' ')} template",
        f"{theme['vibe'].split()[0]} wedding",
        "wedding printable",
        "wedding invitation suite",
        "editable wedding",
        "wedding stationery",
        f"{theme['key'].split('_')[0]} wedding",
        "bridal shower",
        "wedding decor",
        "instant download wedding",
        "diy wedding",
        "wedding template",
        "modern wedding invite",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"wedding_{theme_key}_{item['key']}",
        "text_overlay_method": "pillow",
        "theme": theme_key,
        "theme_name": theme["name"],
        "item_key": item["key"],
        "item_name": item["name"],
        "size_px": f"{item['size'][0]}x{item['size'][1]}",
        "title": title[:140],
        "tags_etsy": ", ".join(tags),
        "price_etsy": 8.99,  # papeterie wedding = prix premium
        "files_included": (
            f"{item['key']}.png ({item['size'][0]}x{item['size'][1]}), "
            f"etsy_preview.jpg (1080x1080). "
            f"Customizable via Pillow/Canva — placeholders [Couple Names], [Date], etc."
        ),
        "personalization_required": True,
        "personalization_instructions": (
            "Replace placeholders [Couple Names], [Date], [Venue] etc. "
            "with your own details. Compatible with Canva/Photoshop."
        ),
        "seed": seed,
    }
    (item_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    theme_key = os.environ.get("THEME", "wildflower_meadow").strip()
    max_items = int(os.environ.get("MAX_ITEMS") or "0") or len(SUITE_ITEMS)

    if theme_key not in THEMES:
        print(f"Theme inconnu. Choix : {list(THEMES)}")
        return 2
    theme = THEMES[theme_key]
    items = SUITE_ITEMS[:max_items]

    print(f"=== WEDDING STATIONERY : {theme['name']} ({len(items)} items) ===\n")

    metas = []
    for idx, item in enumerate(items, 1):
        m = produce_item(theme_key, theme, item, idx)
        if m:
            metas.append(m)
        time.sleep(2)

    if metas:
        csv_path = OUTPUT_DIR / theme_key / "etsy_bulk_upload.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["design_id", "theme", "item_key", "item_name",
                            "title", "tags_etsy", "price_etsy", "size_px"],
                extrasaction="ignore",
            )
            w.writeheader()
            w.writerows(metas)

    print(f"\n{'=' * 60}")
    print(f"  Items produits : {len(metas)}/{len(items)}")
    print(f"  Dossier : {OUTPUT_DIR}/{theme_key}/")
    print(f"\n  💡 Trend Q2 2026 : +4200% YoY sur bridesmaid baskets")
    print(f"     Wedding stationery = niche premium (prix 8-25€/item)")
    return 0 if metas else 1


if __name__ == "__main__":
    sys.exit(main())
