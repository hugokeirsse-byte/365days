"""
Pipeline de production massive de SVG cuttable pour Etsy/Cricut/Silhouette.

Pour chaque thème listé dans THEMES :
1. Pollinations Flux génère 10 silhouettes line art noir/blanc
2. Pillow threshold pur N&B
3. Potrace vectorise en SVG propre cuttable
4. Pillow génère une mosaïque preview commerciale 4:5 Etsy
5. Le pack (10 SVGs + README + preview) est zippé prêt à uploader
6. CSV Etsy bulk-upload pré-rempli (titre, description, tags, prix)

Tout en local sur GitHub Actions runner Ubuntu :
- pip install Pillow requests
- apt install potrace

Zéro API payante, zéro compte tiers, zéro stockage cloud.
Tu obtiens N packs ZIP prêts à vendre, à uploader manuellement sur
Etsy (30s par pack via CSV bulk import — pas d'automation Playwright
qui se fait ban).
"""

import csv
import os
import random
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERREUR : Pillow non installé. pip install Pillow")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "svg_packs"
USER_AGENT = "SvgPackProducer/1.0 (+github actions)"
TIMEOUT = 120

# ─────────────────────────────────────────────────────────────────────
# CATALOGUE DE THÈMES — chaque thème = 1 pack vendable sur Etsy
# Bestseller Etsy SVG : floral, boho, halloween, cottage, mountains,
# witchy, christmas, butterflies. Niche mais demande croissante.
# ─────────────────────────────────────────────────────────────────────

THEME_SUFFIX = (
    "bold thick black silhouette on pure white background, "
    "NO COLOR, NO SHADING, NO GRADIENT, simple clean shapes, "
    "thick connected outlines, vector-style minimalist, "
    "perfectly cuttable for Cricut and Silhouette machines, "
    "no fine internal details, no text, no signature, "
    "high contrast pure black and white, professional craft design"
)

THEMES = {
    "boho_mandala_pack": {
        "title": "Boho Mandala SVG Pack — 10 Designs for Cricut & Silhouette",
        "description": (
            "Beautiful set of 10 hand-crafted boho mandala SVG designs perfect "
            "for your Cricut, Silhouette, or any cutting machine. "
            "Each design is clean, layered-ready, and commercial-use friendly. "
            "Use them for wall decor, t-shirts, tote bags, mugs, stickers, "
            "scrapbooking, and more.\n\n"
            "✦ 10 unique high-quality SVG files\n"
            "✦ Pure black silhouette designs\n"
            "✦ Compatible Cricut Design Space, Silhouette Studio, Adobe Illustrator\n"
            "✦ Commercial use allowed (small business)\n"
            "✦ Instant digital download"
        ),
        "tags": ["boho mandala svg", "mandala cricut", "spiritual svg", "yoga decor svg",
                 "boho cricut bundle", "witchy svg pack", "moon mandala", "sacred geometry"],
        "price_usd": 4.99,
        "prompts": [
            f"intricate symmetric flower mandala silhouette, lotus center with 8-fold petals, {THEME_SUFFIX}",
            f"sun and moon mandala silhouette, celestial bohemian design, {THEME_SUFFIX}",
            f"dreamcatcher mandala silhouette with feathers and beads, {THEME_SUFFIX}",
            f"hamsa hand with mandala inside, evil eye protection symbol, {THEME_SUFFIX}",
            f"crescent moon mandala silhouette with stars and planets, {THEME_SUFFIX}",
            f"lotus flower mandala silhouette, eight petals symmetric, {THEME_SUFFIX}",
            f"tree of life mandala silhouette with circular branches, {THEME_SUFFIX}",
            f"butterfly mandala silhouette, symmetric wings with patterns, {THEME_SUFFIX}",
            f"sunflower mandala silhouette, symmetric radial petals, {THEME_SUFFIX}",
            f"mandala compass silhouette, cardinal directions ornate, {THEME_SUFFIX}",
        ],
    },
    "mountain_adventure_pack": {
        "title": "Mountain Adventure SVG Pack — 10 Hiking & Outdoor Designs",
        "description": (
            "Stunning collection of 10 mountain landscape silhouettes for "
            "outdoor lovers, hikers, and adventurers. Perfect for t-shirts, "
            "water bottles, camping mugs, posters, and travel journals.\n\n"
            "✦ 10 unique SVG mountain designs\n"
            "✦ Pure silhouette, ready to cut\n"
            "✦ Cricut, Silhouette, Glowforge compatible\n"
            "✦ Commercial use allowed\n"
            "✦ Instant digital download"
        ),
        "tags": ["mountain svg", "adventure svg", "hiking cricut", "outdoor decor",
                 "national park svg", "camping svg", "explore svg", "wanderlust"],
        "price_usd": 4.99,
        "prompts": [
            f"three mountain peaks silhouette with pine trees foreground, {THEME_SUFFIX}",
            f"camping tent silhouette under starry mountain sky, {THEME_SUFFIX}",
            f"hiker silhouette on mountain ridge at sunset, {THEME_SUFFIX}",
            f"forest with deer and mountain background silhouette, {THEME_SUFFIX}",
            f"campfire silhouette with mountains and stars, {THEME_SUFFIX}",
            f"compass with mountain peaks silhouette inside, {THEME_SUFFIX}",
            f"canoe on lake silhouette with mountains, {THEME_SUFFIX}",
            f"wolf howling at moon silhouette with mountains, {THEME_SUFFIX}",
            f"cabin in mountains silhouette with pine trees, {THEME_SUFFIX}",
            f"bear silhouette in mountain pine forest, {THEME_SUFFIX}",
        ],
    },
    "halloween_witch_pack": {
        "title": "Halloween Witch SVG Pack — 10 Spooky Cute Designs",
        "description": (
            "Adorable and spooky Halloween SVG designs for crafters who love "
            "the witchy aesthetic. Perfect for Halloween shirts, tote bags, "
            "decorations, and gift tags.\n\n"
            "✦ 10 unique Halloween SVG files\n"
            "✦ Cricut, Silhouette ready\n"
            "✦ Commercial use\n"
            "✦ Instant download"
        ),
        "tags": ["halloween svg", "witch svg", "spooky cute", "witchy cricut",
                 "halloween shirt svg", "fall svg", "pumpkin svg", "spooky season"],
        "price_usd": 4.99,
        "prompts": [
            f"witch hat silhouette with stars and moon, {THEME_SUFFIX}",
            f"cute pumpkin silhouette with stem and leaves, {THEME_SUFFIX}",
            f"black cat silhouette with arched back, {THEME_SUFFIX}",
            f"ghost silhouette holding a heart, {THEME_SUFFIX}",
            f"crescent moon with bats silhouette, {THEME_SUFFIX}",
            f"haunted house silhouette with full moon, {THEME_SUFFIX}",
            f"crystal ball silhouette on stand with stars, {THEME_SUFFIX}",
            f"potion bottle silhouette with bubbles, {THEME_SUFFIX}",
            f"spider on web silhouette decorative, {THEME_SUFFIX}",
            f"broomstick crossed with wand silhouette, {THEME_SUFFIX}",
        ],
    },
    "floral_botanical_pack": {
        "title": "Floral Botanical SVG Pack — 10 Wildflower Designs",
        "description": (
            "Elegant botanical silhouettes featuring wildflowers, branches, "
            "and herbs. Perfect for wedding stationery, wall art, kitchen "
            "decor, and feminine apparel.\n\n"
            "✦ 10 unique floral SVG designs\n"
            "✦ Vector silhouettes, scalable\n"
            "✦ Cricut/Silhouette compatible\n"
            "✦ Commercial use allowed\n"
            "✦ Instant download"
        ),
        "tags": ["floral svg", "botanical svg", "wildflower cricut", "flower bundle",
                 "wedding svg", "boho floral", "minimalist flowers", "herbs svg"],
        "price_usd": 4.99,
        "prompts": [
            f"wildflower bouquet silhouette with daisies and grass, {THEME_SUFFIX}",
            f"single rose with stem and leaves silhouette, {THEME_SUFFIX}",
            f"lavender sprig silhouette minimalist, {THEME_SUFFIX}",
            f"eucalyptus branch silhouette decorative, {THEME_SUFFIX}",
            f"sunflower with stem and leaves silhouette, {THEME_SUFFIX}",
            f"floral wreath silhouette circular, {THEME_SUFFIX}",
            f"peony flower silhouette with leaves, {THEME_SUFFIX}",
            f"fern leaf silhouette delicate, {THEME_SUFFIX}",
            f"poppy flower silhouette with bud, {THEME_SUFFIX}",
            f"tulip bouquet silhouette tied with ribbon, {THEME_SUFFIX}",
        ],
    },
}


def pollinations_url(prompt: str, seed: int, size: int = 1536) -> str:
    encoded = urllib.parse.quote(prompt, safe="")
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?model=flux&width={size}&height={size}"
        f"&seed={seed}&nologo=true&private=true&enhance=true"
    )


def http_get(url: str, dest: Path, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
            if len(data) < 5000:
                raise ValueError(f"réponse trop courte ({len(data)} bytes)")
            dest.write_bytes(data)
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"    ↻ retry {attempt + 1}/{retries} : {exc}")
            time.sleep(5 + attempt * 5)
    return False


def png_to_pbm(png_path: Path, pbm_path: Path, threshold: int = 180) -> None:
    """Convertit en bitmap noir/blanc pur, prêt pour Potrace."""
    img = Image.open(png_path).convert("L")
    bw = img.point(lambda p: 0 if p < threshold else 255, mode="1")
    bw.save(pbm_path)


def trace_to_svg(pbm_path: Path, svg_path: Path) -> bool:
    try:
        subprocess.run(
            [
                "potrace",
                str(pbm_path),
                "-s",                       # output SVG
                "-o", str(svg_path),
                "--turdsize", "20",         # ignore noise < 20 px
                "--alphamax", "1",          # smooth corners
                "--opttolerance", "0.2",    # bezier optimization
            ],
            check=True,
            capture_output=True,
        )
        return svg_path.exists() and svg_path.stat().st_size > 200
    except subprocess.CalledProcessError as exc:
        print(f"    ✗ potrace error: {exc.stderr.decode()[:200]}")
        return False


def make_preview_mosaic(svg_files: list[Path], output: Path, title: str) -> None:
    """Génère une mosaïque 4:5 Etsy à partir des PNGs intermédiaires.
    On utilise des PNGs car convertir SVG→PNG en pur Python est lourd ;
    on a gardé les png raw pour cette étape juste avant cleanup.
    """
    pngs = sorted(svg_files[0].parent.glob("raw_*.png"))
    if not pngs:
        return
    cell = 400
    cols, rows = 2, 5
    canvas = Image.new("RGB", (cols * cell, rows * cell + 120), "white")
    draw = ImageDraw.Draw(canvas)
    for idx, p in enumerate(pngs[: cols * rows]):
        thumb = Image.open(p).convert("RGB").resize((cell, cell), Image.LANCZOS)
        canvas.paste(thumb, ((idx % cols) * cell, (idx // cols) * cell))
    # Bandeau titre
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    except OSError:
        font = ImageFont.load_default()
    draw.rectangle([0, rows * cell, cols * cell, rows * cell + 120], fill="black")
    draw.text((20, rows * cell + 40), title[:50], fill="white", font=font)
    canvas.save(output, "JPEG", quality=85)


def produce_pack(theme_key: str, theme_def: dict) -> tuple[Path, dict]:
    pack_dir = OUTPUT_DIR / theme_key
    pack_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {theme_def['title']} ===")
    svg_files: list[Path] = []

    for i, prompt in enumerate(theme_def["prompts"], 1):
        seed = i * 1000 + random.randint(0, 999)
        png = pack_dir / f"raw_{i:02d}.png"
        pbm = pack_dir / f"raw_{i:02d}.pbm"
        svg = pack_dir / f"design_{i:02d}.svg"

        print(f"  [{i:>2}/10] {prompt[:60]}...")

        if not http_get(pollinations_url(prompt, seed), png):
            print(f"    ✗ génération échouée")
            continue
        png_to_pbm(png, pbm)
        if trace_to_svg(pbm, svg):
            svg_files.append(svg)
            print(f"    ✓ {svg.stat().st_size // 1024} KB SVG")
        pbm.unlink(missing_ok=True)
        time.sleep(2)

    if len(svg_files) < 5:
        print(f"  ! Pack avorté : seulement {len(svg_files)} SVG valides")
        return None, None

    # Preview commerciale
    preview = pack_dir / "preview.jpg"
    make_preview_mosaic(svg_files, preview, theme_def["title"])

    # README intégré au ZIP
    readme = (
        f"{theme_def['title']}\n"
        f"{'=' * len(theme_def['title'])}\n\n"
        f"{theme_def['description']}\n\n"
        f"FILES INCLUDED :\n"
        + "\n".join(f"- {f.name}" for f in svg_files)
        + "\n\nINSTRUCTIONS :\n"
        "1. Unzip this file\n"
        "2. Import the SVG files into Cricut Design Space, Silhouette Studio,\n"
        "   Adobe Illustrator, or any vector software\n"
        "3. Resize freely (vector format = no quality loss)\n"
        "4. Cut, print, or use as you wish\n\n"
        "LICENSE :\n"
        "Small commercial use allowed (up to 500 physical items per design).\n"
        "Reselling the digital files as-is is not allowed.\n\n"
        "Thank you for your purchase!\n"
    )

    # Cleanup raw PNGs avant zip
    for png in pack_dir.glob("raw_*.png"):
        png.unlink()

    zip_path = OUTPUT_DIR / f"{theme_key}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for svg in svg_files:
            z.write(svg, arcname=svg.name)
        z.writestr("README.txt", readme)

    metadata = {
        "title": theme_def["title"],
        "description": theme_def["description"],
        "tags": ", ".join(theme_def["tags"][:13]),  # Etsy max 13 tags
        "price_usd": theme_def["price_usd"],
        "zip_file": zip_path.name,
        "preview_file": preview.name,
        "svg_count": len(svg_files),
    }

    print(f"  ✓ Pack prêt : {zip_path.name} ({len(svg_files)} SVGs)")
    return zip_path, metadata


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Production de {len(THEMES)} packs SVG…")

    metas = []
    for key, theme in THEMES.items():
        zip_path, meta = produce_pack(key, theme)
        if meta:
            metas.append(meta)

    # CSV Etsy bulk-upload metadata
    csv_path = OUTPUT_DIR / "etsy_listings.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["title", "description", "tags", "price_usd",
                        "svg_count", "zip_file", "preview_file"],
        )
        writer.writeheader()
        writer.writerows(metas)

    print(f"\n{'=' * 60}")
    print(f"Packs produits : {len(metas)}")
    print(f"CSV Etsy       : {csv_path}")
    print(f"Output dir     : {OUTPUT_DIR}")
    return 0 if metas else 1


if __name__ == "__main__":
    sys.exit(main())
