"""
Cover Generator KDP — génère automatiquement la couverture des livres
KDP à partir du metadata.json du livre.

Format KDP paperback 8.5×11 :
- Trim 8.5 × 11 inch (612×792 pt)
- Bleed 0.125" sur 4 côtés → 8.75 × 11.25" finale
- DPI 300 → 2625 × 3375 px pour le front cover
- Spine dépend du nombre de pages (1 page = 0.0025" pour b&w)
- Wrap complet = back + spine + front (KDP impose un PDF unique)

Pour v1 : on génère uniquement le front cover. Le back cover et la
tranche, Hugo les fera via KDP Cover Creator (qui prend le front PNG
en input et complète automatiquement).

Pipeline :
1. Pollinations génère une illustration de fond thématique (sans texte)
2. Pillow overlay : titre + sous-titre + nom auteur en typo claire,
   bandeau semi-transparent pour la lisibilité
3. Sortie : products/coloring_books/{book_id}/cover_front.png

Variables d'env :
  BOOK_ID=mystical_mushrooms        livre cible (un dossier de coloring_books)
"""

import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    print("ERREUR : Pillow non installé")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
COLORING_DIR = ROOT / "products" / "coloring_books"
USER_AGENT = "CoverGenerator/1.0"
TIMEOUT = 240

# KDP 8.5×11 paperback : front cover @ 300 DPI = 2625×3375 (avec bleed)
COVER_W = 2625
COVER_H = 3375

# Prompts d'illustration de couverture par niche
COVER_PROMPTS = {
    "mystical_mushrooms": (
        "magical mushroom forest illustration, whimsical scene with various "
        "colorful mushrooms in pastel palette, fairy lights and gentle "
        "atmosphere, soft watercolor style, book cover quality illustration, "
        "centered composition with negative space at top for title text, "
        "vertical portrait format"
    ),
    "mystical_creatures": (
        "whimsical mystical creatures scene illustration, baby dragon unicorn "
        "and small fantasy animals in enchanted meadow, dreamy pastel palette, "
        "book cover quality watercolor and ink, magical atmosphere, centered "
        "composition with space at top for title, vertical portrait format"
    ),
    "fairy_cottages": (
        "enchanted fairy cottage village illustration, tiny whimsical houses "
        "in mushroom and treetop, magical garden with flowers, soft pastel "
        "watercolor palette, dreamy storybook quality, book cover composition "
        "with space at top for title, vertical portrait format"
    ),
}

# Couleurs de bandeau par mood
TITLE_BAND_COLORS = {
    "mystical_mushrooms": (245, 235, 220, 220),  # crème opaque
    "mystical_creatures": (240, 235, 245, 220),  # lavande pâle
    "fairy_cottages":     (245, 240, 230, 220),  # ivoire chaud
}


def pollinations_url(prompt: str, seed: int) -> str:
    encoded = urllib.parse.quote(prompt, safe="")
    # On génère en 1024×1536 puis on upscale + crop
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?model=flux&width=1024&height=1536"
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
            time.sleep(8 + attempt * 6)
    return False


def find_font(preferred: list[str], size: int) -> ImageFont.ImageFont:
    """Cherche une police TTF sur le système, fallback default."""
    candidates = preferred + [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/Library/Fonts/Georgia.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont,
              max_width: int) -> list[str]:
    """Découpe le texte en lignes qui rentrent dans max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_background(src: Path, w: int, h: int) -> Image.Image:
    img = Image.open(src).convert("RGB")
    sr = img.width / img.height
    tr = w / h
    if sr > tr:
        new_w = int(img.height * tr)
        off = (img.width - new_w) // 2
        img = img.crop((off, 0, off + new_w, img.height))
    elif sr < tr:
        new_h = int(img.width / tr)
        off = (img.height - new_h) // 2
        img = img.crop((0, off, img.width, off + new_h))
    return img.resize((w, h), Image.LANCZOS)


def add_title_overlay(bg: Image.Image, title: str, subtitle: str,
                      author: str, band_color: tuple) -> Image.Image:
    """Ajoute un bandeau translucide en haut + textes."""
    cover = bg.copy().convert("RGBA")
    overlay = Image.new("RGBA", cover.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Bandeau supérieur prenant ~32% de la hauteur
    band_h = int(cover.height * 0.32)
    draw.rectangle([(0, 0), (cover.width, band_h)], fill=band_color)

    # Petite ombre sous le bandeau pour profondeur
    shadow_h = 40
    for i in range(shadow_h):
        alpha = int(80 * (1 - i / shadow_h))
        draw.rectangle(
            [(0, band_h + i), (cover.width, band_h + i + 1)],
            fill=(0, 0, 0, alpha),
        )

    # Polices : on essaie une serif élégante pour le titre, sans-serif pour author
    title_font = find_font(
        ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"], 180)
    subtitle_font = find_font(
        ["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"], 72)
    author_font = find_font(
        ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"], 64)

    text_color = (40, 30, 30, 255)

    # Titre — word wrap
    title_lines = wrap_text(draw, title.upper(), title_font,
                             cover.width - 200)
    title_total_h = sum(
        draw.textbbox((0, 0), line, font=title_font)[3] -
        draw.textbbox((0, 0), line, font=title_font)[1]
        for line in title_lines
    ) + (len(title_lines) - 1) * 30

    # Position : centré dans le bandeau supérieur
    y = (band_h - title_total_h - 200) // 2
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        x = (cover.width - line_w) // 2
        draw.text((x, y), line, fill=text_color, font=title_font)
        y += line_h + 30

    # Sous-titre
    y += 30
    sub_lines = wrap_text(draw, subtitle, subtitle_font, cover.width - 300)
    for line in sub_lines[:2]:
        bbox = draw.textbbox((0, 0), line, font=subtitle_font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        x = (cover.width - line_w) // 2
        draw.text((x, y), line, fill=(60, 50, 50, 255), font=subtitle_font)
        y += line_h + 15

    # Auteur en bas de cover
    bbox = draw.textbbox((0, 0), author, font=author_font)
    line_w = bbox[2] - bbox[0]
    line_h = bbox[3] - bbox[1]
    x = (cover.width - line_w) // 2
    y_author = cover.height - 200
    # Bandeau opaque autour de l'auteur pour lisibilité
    pad = 30
    draw.rectangle(
        [(x - pad * 2, y_author - pad),
         (x + line_w + pad * 2, y_author + line_h + pad)],
        fill=band_color,
    )
    draw.text((x, y_author), author, fill=text_color, font=author_font)

    return Image.alpha_composite(cover, overlay).convert("RGB")


def generate_cover(book_dir: Path) -> Path | None:
    meta_path = book_dir / "metadata.json"
    if not meta_path.exists():
        print(f"  ✗ Pas de metadata.json dans {book_dir.name}")
        return None
    metadata = json.loads(meta_path.read_text())
    niche_key = metadata.get("niche_key", "")
    title = metadata.get("title", "Untitled")
    subtitle = metadata.get("subtitle", "")
    author = metadata.get("imprint", "Daystone Press")

    cover_prompt = COVER_PROMPTS.get(niche_key)
    if not cover_prompt:
        print(f"  ✗ Pas de prompt cover pour niche {niche_key}")
        return None

    band_color = TITLE_BAND_COLORS.get(niche_key, (245, 235, 220, 220))

    raw = book_dir / "cover_raw.png"
    final = book_dir / "cover_front.png"
    seed = random.randint(1000, 999999)
    url = pollinations_url(cover_prompt, seed)

    print(f"  → Génération illustration cover : {title}")
    if not http_get(url, raw):
        print(f"     ✗ Echec Pollinations")
        return None

    try:
        bg = fit_background(raw, COVER_W, COVER_H)
        cover = add_title_overlay(bg, title, subtitle, author, band_color)
        cover.save(final, "PNG", optimize=True)
    except Exception as exc:  # noqa: BLE001
        print(f"     ✗ Composition cover : {exc}")
        return None
    finally:
        if raw.exists():
            raw.unlink()

    print(f"     ✓ Cover : {final}")
    return final


def main() -> int:
    book_id = os.environ.get("BOOK_ID", "").strip()
    if book_id:
        book_dir = COLORING_DIR / book_id
        if not book_dir.exists():
            print(f"✗ {book_dir} inexistant")
            return 1
        cover = generate_cover(book_dir)
        return 0 if cover else 1

    # Sinon, traite tous les livres sans cover
    if not COLORING_DIR.exists():
        print(f"✗ {COLORING_DIR} inexistant")
        return 1
    treated = 0
    for book_dir in COLORING_DIR.iterdir():
        if not book_dir.is_dir():
            continue
        if (book_dir / "cover_front.png").exists():
            print(f"  ⊝ {book_dir.name} : cover déjà existe")
            continue
        if generate_cover(book_dir):
            treated += 1
        time.sleep(2)
    print(f"\n{treated} cover(s) générée(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
