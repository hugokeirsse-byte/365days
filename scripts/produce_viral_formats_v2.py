"""
Pipeline VIRAL FORMATS V2 — gibberish-proof avec overlay Pillow.

V1 demandait à Flux d'écrire le texte directement dans l'image →
gibberish illisible. V2 utilise la stratégie validée par produce_kdp_cover :

1. Pollinations génère UNIQUEMENT un fond/illustration ambiant (style
   visual_hint du format) SANS aucun texte.
2. Pillow overlay le texte du format en grand au centre avec police
   TTF appropriée au style.

Texte garanti correct. Reproductibilité parfaite.

Variables d'env :
  MAX_FORMATS=5      limite à N formats
  MAX_NICHES=5       limite à N niches
  FORMAT_FAMILY=medical   filtre par famille
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
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
except ImportError:
    print("ERREUR : Pillow non installé")
    sys.exit(2)

# Import des FORMATS depuis produce_viral_formats (v1) pour pas dupliquer
sys.path.insert(0, str(Path(__file__).resolve().parent))
from produce_viral_formats import FORMATS, NICHES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "viral_formats_v2"
USER_AGENT = "ViralFormatsV2Producer/1.0"
TIMEOUT = 180

# Style → palette + typo + bg description (pour Pollinations sans texte)
STYLE_RECIPES = {
    # MEDICAL
    "medical": {
        "bg_prompt": "vintage medical prescription pad parchment background texture, faded sepia and cream, no text no letters, abstract aesthetic",
        "font_paths": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
        "text_color": (140, 30, 30),
        "bg_overlay_color": (250, 240, 220, 200),
        "italic": False,
    },
    "certification": {
        "bg_prompt": "official seal red wax stamp on aged paper, vintage certificate background, no text no letters, decorative ornamental",
        "font_paths": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
        "text_color": (60, 30, 30),
        "bg_overlay_color": (250, 245, 230, 200),
        "italic": False,
    },
    "warning": {
        "bg_prompt": "yellow caution warning sign background with bold geometric shapes, no text no letters, industrial graphic",
        "font_paths": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "text_color": (30, 30, 30),
        "bg_overlay_color": (240, 200, 50, 200),
        "italic": False,
    },
    "office": {
        "bg_prompt": "minimalist office paper texture cream background, subtle geometric pattern, no text, no letters, clean professional",
        "font_paths": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "text_color": (40, 40, 40),
        "bg_overlay_color": (252, 248, 240, 200),
        "italic": False,
    },
    "quote": {
        "bg_prompt": "elegant cream paper texture with subtle ornamental flourishes corners, no text no letters, minimal classical",
        "font_paths": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
        "text_color": (30, 30, 30),
        "bg_overlay_color": (252, 248, 240, 220),
        "italic": True,
    },
    "geek": {
        "bg_prompt": "retro computer terminal screen background dark blue with subtle scan lines, no text no letters, cyberpunk",
        "font_paths": ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "text_color": (100, 240, 100),
        "bg_overlay_color": (15, 25, 35, 220),
        "italic": False,
    },
    "vintage": {
        "bg_prompt": "vintage cassette tape paper texture sepia background, 80s retro decorative pattern, no text no letters",
        "font_paths": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
        "text_color": (60, 40, 25),
        "bg_overlay_color": (240, 220, 190, 200),
        "italic": False,
    },
    "introvert": {
        "bg_prompt": "cozy soft pastel illustration with subtle introvert imagery cup tea book plant, no text no letters, minimalist",
        "font_paths": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
        "text_color": (60, 50, 70),
        "bg_overlay_color": (250, 240, 245, 220),
        "italic": True,
    },
    "dictionary": {
        "bg_prompt": "vintage dictionary page parchment background slightly yellowed, subtle book texture, no text no letters",
        "font_paths": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
        "text_color": (40, 30, 20),
        "bg_overlay_color": (245, 235, 215, 220),
        "italic": False,
    },
    "esoteric": {
        "bg_prompt": "mystical tarot card border ornamental gold detail on deep midnight blue, no text no letters, occult decorative",
        "font_paths": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
        "text_color": (220, 180, 80),
        "bg_overlay_color": (20, 20, 50, 200),
        "italic": False,
    },
    "house": {
        "bg_prompt": "minimalist textured cream paper with abstract geometric accent corners, no text no letters, modern editorial",
        "font_paths": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "text_color": (30, 30, 30),
        "bg_overlay_color": (250, 245, 235, 215),
        "italic": False,
    },
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


def find_font(paths: list[str], size: int):
    for p in paths + ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def compose_design(bg_path: Path, text: str, family: str,
                    dest: Path, canvas_size: int = 3000) -> None:
    """Compose le design final : background + overlay translucide + texte."""
    recipe = STYLE_RECIPES.get(family, STYLE_RECIPES["house"])
    bg = Image.open(bg_path).convert("RGB")
    # Crop carré centré
    side = min(bg.width, bg.height)
    off_x = (bg.width - side) // 2
    off_y = (bg.height - side) // 2
    bg = bg.crop((off_x, off_y, off_x + side, off_y + side))
    bg = bg.resize((canvas_size, canvas_size), Image.LANCZOS)

    # Désature un peu le bg pour pas concurrencer le texte
    bg = ImageEnhance.Color(bg).enhance(0.7)
    bg = ImageEnhance.Brightness(bg).enhance(0.95)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=3))

    canvas = bg.convert("RGBA")

    # Overlay couleur translucide pour assurer la lisibilité du texte
    overlay = Image.new("RGBA", canvas.size, recipe["bg_overlay_color"])
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    # Texte : on cherche la plus grande taille de police qui rentre
    # dans 80% de la largeur sur 3-4 lignes max
    target_w = int(canvas_size * 0.82)
    text_color = recipe["text_color"] + (255,)

    # Recherche binaire de la bonne taille
    best_size = 80
    best_lines = []
    for size in range(280, 80, -20):
        font = find_font(recipe["font_paths"], size)
        lines = wrap_text(draw, text, font, target_w)
        total_h = 0
        max_w = 0
        line_heights = []
        for ln in lines:
            bbox = draw.textbbox((0, 0), ln, font=font)
            h = bbox[3] - bbox[1]
            w = bbox[2] - bbox[0]
            total_h += h
            line_heights.append(h)
            max_w = max(max_w, w)
        total_h += (len(lines) - 1) * int(size * 0.15)
        if total_h < canvas_size * 0.7 and len(lines) <= 5:
            best_size = size
            best_lines = lines
            break

    if not best_lines:
        font = find_font(recipe["font_paths"], 80)
        best_lines = wrap_text(draw, text, font, target_w)

    font = find_font(recipe["font_paths"], best_size)

    # Calcule la position de départ pour centrage vertical
    line_h = best_size + int(best_size * 0.15)
    total_h = line_h * len(best_lines)
    y = (canvas_size - total_h) // 2

    for line in best_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (canvas_size - line_w) // 2
        draw.text((x, y), line, fill=text_color, font=font)
        y += line_h

    canvas.convert("RGB").save(dest, "PNG", optimize=True)


def make_outputs(composed: Path, design_dir: Path) -> None:
    img = Image.open(composed).convert("RGB")
    img.resize((1080, 1080), Image.LANCZOS).save(
        design_dir / "etsy_preview.jpg", "JPEG", quality=92)
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


def produce_design(fmt: dict, niche: dict, idx: int) -> dict | None:
    text = fmt["text_en"].format(niche=niche["label"])
    family = fmt["family"]
    recipe = STYLE_RECIPES.get(family, STYLE_RECIPES["house"])

    design_dir = OUTPUT_DIR / family / fmt["key"] / niche["slug"]
    design_dir.mkdir(parents=True, exist_ok=True)
    raw = design_dir / "raw_bg.png"
    final_print = design_dir / "print_3000.png"
    seed = idx * 10079 + random.randint(0, 9999)
    url = pollinations_url(recipe["bg_prompt"], seed)

    print(f"  [{idx:>4}] [{family}] {fmt['key']} × {niche['slug']}")
    if not http_get(url, raw):
        print(f"         echec Pollinations background")
        return None

    try:
        compose_design(raw, text, family, final_print)
        make_outputs(final_print, design_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"         compose echoue : {exc}")
        return None
    finally:
        if raw.exists():
            raw.unlink()

    title = f"{text} — Funny {niche['label']} Gift Print"
    tags = [
        f"{niche['label'].lower()} gift",
        f"{niche['audience']}",
        "funny tshirt design",
        "hobby gift",
        "humor print",
        family,
        "personality gift",
        f"{niche['slug'].replace('_', ' ')} lover",
        "digital download",
        "etsy bestseller",
        "redbubble pod",
        "tshirt mug poster",
        "instant download",
    ]
    tags = list(dict.fromkeys(tags))[:13]

    metadata = {
        "design_id": f"viral_v2_{fmt['key']}_{niche['slug']}",
        "version": "v2",
        "text_overlay_method": "pillow",  # important pour audit visuel
        "format_key": fmt["key"],
        "format_family": family,
        "format_text": text,
        "niche": niche["slug"],
        "niche_label": niche["label"],
        "audience": niche["audience"],
        "title": title[:140],
        "tags_etsy": ", ".join(tags),
        "price_etsy": 3.99,
        "files_included": "etsy_preview.jpg, print_3000.png, tshirt_2400x3000.png",
        "bg_prompt_used": recipe["bg_prompt"],
        "seed": seed,
    }
    (design_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))
    return metadata


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    max_f = int(os.environ.get("MAX_FORMATS") or "0") or len(FORMATS)
    max_n = int(os.environ.get("MAX_NICHES") or "0") or len(NICHES)
    family_filter = os.environ.get("FORMAT_FAMILY", "").strip().lower()

    formats = FORMATS[:max_f]
    if family_filter:
        formats = [f for f in formats if f["family"] == family_filter]
        print(f"Filtré family={family_filter} : {len(formats)} formats")
    niches = NICHES[:max_n]
    total = len(formats) * len(niches)
    print(f"=== VIRAL FORMATS V2 (overlay Pillow) — {len(formats)} formats × "
          f"{len(niches)} niches = {total} designs ===\n")

    metas = []
    idx = 0
    for fmt in formats:
        for niche in niches:
            idx += 1
            m = produce_design(fmt, niche, idx)
            if m:
                metas.append(m)
            time.sleep(2)

    if metas:
        csv_path = OUTPUT_DIR / "etsy_bulk_upload.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["design_id", "format_family", "format_key",
                            "format_text", "niche", "title",
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
