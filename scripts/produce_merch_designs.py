#!/usr/bin/env python3
"""
Merch Design Producer — generates all design PNGs from an approved merch CdC.

Uses Pollinations AI for illustrations + Pillow for text overlay and compositing.
Skips designs that already exist. Generates a preview mosaic + upload checklist.

Env vars:
  MERCH_DIR   — path to the merch product folder  (default: latest approved in products/merch/)
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("[Merch Produce] ERREUR: Pillow non installé. Exécuter: pip install Pillow")
    sys.exit(1)

MERCH_ROOT = Path("products/merch")
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/{prompt}&width=1200&height=1200&nologo=true"
DOWNLOAD_DELAY = 0.5  # seconds between Pollinations calls


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _find_latest_approved() -> Path | None:
    """Find the most recently modified merch folder with gate_cdc == 'approved'."""
    if not MERCH_ROOT.exists():
        return None
    candidates = []
    for d in MERCH_ROOT.iterdir():
        if not d.is_dir():
            continue
        cdc_file = d / "cdc.json"
        if not cdc_file.exists():
            continue
        try:
            cdc = json.loads(cdc_file.read_text(encoding="utf-8"))
            if cdc.get("gate_cdc") == "approved" and not cdc.get("production_status"):
                candidates.append((cdc_file.stat().st_mtime, d))
        except Exception:
            pass
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def _load_font(size: int, bold: bool = False):
    """Try to load a system TrueType font; fall back to Pillow default."""
    candidates = []
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap_text(text: str, font, draw: ImageDraw.ImageDraw, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [text]


def _draw_text_centered(draw: ImageDraw.ImageDraw, text: str, font, y: int,
                         canvas_w: int, fill: tuple, max_width: int) -> int:
    """Draw centered text (with wrapping). Returns y position after the text block."""
    lines = _wrap_text(text, font, draw, max_width)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (canvas_w - line_w) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += (bbox[3] - bbox[1]) + 8
    return y


def _download_image(prompt: str, out_path: Path) -> bool:
    """Download image from Pollinations. Returns True on success."""
    encoded = urllib.parse.quote(prompt)
    url = POLLINATIONS_BASE.format(prompt=encoded)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "365days-merch/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
        out_path.write_bytes(data)
        return True
    except urllib.error.HTTPError as e:
        print(f"  [download] HTTP {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"  [download] Network error: {e.reason}")
        return False
    except Exception as e:
        print(f"  [download] Erreur inattendue: {e}")
        return False


def _compose_design(raw_img_path: Path, design: dict, spec: dict, out_path: Path) -> bool:
    """
    Compose final 2400×2400 design:
      - top 60%: illustration (white-padded)
      - bottom 35%: text zone (texte_principal, sous_texte, texte_secondaire)
      - 5% margins
    """
    canvas_size = 2400
    margin_pct = spec.get("marge_pct", 5) / 100
    illus_pct = spec.get("zone_illustration_pct", 60) / 100
    text_pct = spec.get("zone_texte_pct", 35) / 100

    margin_px = int(canvas_size * margin_pct)
    inner_w = canvas_size - 2 * margin_px
    illus_h = int(canvas_size * illus_pct)
    text_zone_y = illus_h
    text_zone_h = int(canvas_size * text_pct)

    # Create white canvas
    canvas = Image.new("RGB", (canvas_size, canvas_size), color=(255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # Open and paste illustration
    try:
        raw_img = Image.open(raw_img_path).convert("RGBA")
        bg = Image.new("RGBA", raw_img.size, (255, 255, 255, 255))
        bg.paste(raw_img, mask=raw_img.split()[3])
        raw_img_rgb = bg.convert("RGB")

        illus_inner_h = illus_h - margin_px
        raw_img_rgb.thumbnail((inner_w, illus_inner_h), Image.LANCZOS)
        paste_x = (canvas_size - raw_img_rgb.width) // 2
        paste_y = margin_px + (illus_inner_h - raw_img_rgb.height) // 2
        canvas.paste(raw_img_rgb, (paste_x, paste_y))
    except Exception as e:
        print(f"  [compose] Erreur ouverture illustration: {e}")
        return False

    # ---- Text zone ----
    text_max_w = inner_w - 40  # small inner padding
    text_dark = (30, 30, 30)
    text_mid = (80, 80, 80)
    text_light = (120, 120, 120)

    # Parse accent color
    accent_hex = design.get("couleur_accent", "#444444").lstrip("#")
    try:
        accent = tuple(int(accent_hex[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        accent = (68, 68, 68)

    texte_principal = design.get("texte_principal", "")
    sous_texte = design.get("sous_texte", "")
    texte_secondaire = design.get("texte_secondaire", "")

    # Font sizes scaled to canvas
    font_large = _load_font(96, bold=True)
    font_medium = _load_font(60, bold=False)
    font_small = _load_font(48, bold=False)

    # Separator line above text zone
    sep_y = text_zone_y + 20
    draw.line([(margin_px + 80, sep_y), (canvas_size - margin_px - 80, sep_y)], fill=(220, 220, 220), width=3)

    # Draw texts top-to-bottom in text zone
    y = text_zone_y + 60

    if texte_principal:
        y = _draw_text_centered(draw, texte_principal, font_large, y, canvas_size, accent, text_max_w)
        y += 12

    if sous_texte:
        y = _draw_text_centered(draw, sous_texte, font_medium, y, canvas_size, text_mid, text_max_w)
        y += 8

    if texte_secondaire:
        y = _draw_text_centered(draw, texte_secondaire, font_small, y, canvas_size, text_light, text_max_w)

    canvas.save(str(out_path), "PNG", optimize=True)
    return True


def _generate_mosaic(designs_dir: Path, design_list: list, out_path: Path) -> None:
    """Generate a 4-per-row mosaic of all design thumbnails."""
    thumb_size = 400
    cols = 4
    n = len(design_list)
    rows = (n + cols - 1) // cols

    mosaic_w = cols * thumb_size
    mosaic_h = rows * thumb_size
    mosaic = Image.new("RGB", (mosaic_w, mosaic_h), color=(245, 245, 245))
    draw = ImageDraw.Draw(mosaic)
    font_label = _load_font(28, bold=False)

    for idx, d in enumerate(design_list):
        n_design = d.get("n", idx + 1)
        img_path = designs_dir / f"design_{n_design:02d}.png"
        row = idx // cols
        col = idx % cols
        ox = col * thumb_size
        oy = row * thumb_size

        if img_path.exists():
            try:
                thumb = Image.open(img_path).convert("RGB")
                thumb.thumbnail((thumb_size, thumb_size), Image.LANCZOS)
                paste_x = ox + (thumb_size - thumb.width) // 2
                paste_y = oy + (thumb_size - thumb.height) // 2
                mosaic.paste(thumb, (paste_x, paste_y))
            except Exception:
                pass
        else:
            # Gray placeholder
            draw.rectangle([ox, oy, ox + thumb_size - 1, oy + thumb_size - 1], fill=(200, 200, 200))
            draw.text((ox + 10, oy + thumb_size // 2), f"#{n_design} missing", font=font_label, fill=(100, 100, 100))

        # Draw label
        label = f"#{n_design} {d.get('sous_theme', '')}"[:28]
        draw.text((ox + 4, oy + thumb_size - 36), label, font=font_label, fill=(50, 50, 50))

    mosaic.save(str(out_path), "PNG")
    print(f"[Merch Produce] Mosaïque aperçu : {out_path}")


def _write_tags(listing_dir: Path, cdc: dict) -> None:
    lp = cdc.get("listing_plateforme", {})
    tags = lp.get("tags_communs", [])
    concept = cdc.get("concept_theme", {})
    all_tags = list(tags)

    # Add per-design sous_theme tags (unique)
    for d in cdc.get("designs", []):
        st = d.get("sous_theme", "").lower().replace(" ", "-")
        if st and st not in all_tags:
            all_tags.append(st)

    (listing_dir / "tags.txt").write_text("\n".join(all_tags), encoding="utf-8")
    print(f"[Merch Produce] tags.txt écrit ({len(all_tags)} tags)")


def _write_upload_checklist(listing_dir: Path, cdc: dict) -> None:
    plateformes = cdc.get("plateformes", [])
    lp = cdc.get("listing_plateforme", {})
    ct = cdc.get("concept_theme", {})
    produits = cdc.get("produits_cibles", [])
    n_designs = len(cdc.get("designs", []))

    lines = [
        "# Upload Checklist — Merch Collection",
        "",
        f"**Collection:** {ct.get('titre', '')}",
        f"**Designs à uploader:** {n_designs}",
        f"**Date:** {date.today().isoformat()}",
        "",
        "---",
        "",
    ]

    platform_guides = {
        "redbubble": {
            "url": "https://www.redbubble.com/portfolio/images/new",
            "format": "2400x3200px PNG (transparent or white bg)",
            "notes": [
                "Upload each design individually",
                f"Enable all products: {', '.join(produits)}",
                f"Collection title: {lp.get('titre_collection', '')}",
                f"Tags (max 15): add from tags.txt",
                f"T-shirt price: ${lp.get('prix_tshirt_usd', 24.99)}  |  Mug: ${lp.get('prix_mug_usd', 17.99)}",
            ],
        },
        "merch_amazon": {
            "url": "https://merch.amazon.com/dashboard",
            "format": "4500x5400px PNG with transparent background",
            "notes": [
                "Resize each design to 4500x5400 before upload",
                "Select Standard fit + Relaxed fit",
                "Title: include primary keyword in first 60 chars",
                f"Bullet points: use description from listing_plateforme",
                "Royalty tier: 37% (ensure pricing reflects this)",
            ],
        },
        "society6": {
            "url": "https://society6.com/studio",
            "format": "2400x3200px PNG",
            "notes": [
                "Upload as Art Print first, then enable other products",
                f"Enable: {', '.join(produits)}",
                "Set tags from tags.txt (comma separated)",
                "Royalty: 10% (price accordingly)",
            ],
        },
        "etsy_printful": {
            "url": "https://www.etsy.com/your/shops/me/tools/listings",
            "format": "4000x4000px PNG with transparent background",
            "notes": [
                "Create listing in Etsy → connect to Printful",
                "Upload print file (4000x4000 transparent)",
                f"Mockup: generate from Printful mockup generator",
                f"Tags: add 13 tags from tags.txt",
                "Shipping: Printful handles fulfillment",
            ],
        },
    }

    platform_map = {p.get("nom"): p for p in plateformes}

    for pname, guide in platform_guides.items():
        p_info = platform_map.get(pname, {})
        royalty = p_info.get("royalty_pct", "?")
        lines += [
            f"## {pname.replace('_', ' ').title()}",
            "",
            f"**URL:** {guide['url']}",
            f"**Format requis:** {guide['format']}",
            f"**Royalty:** {royalty}%",
            "",
            "**Checklist:**",
        ]
        for note in guide["notes"]:
            lines.append(f"- [ ] {note}")
        lines += [
            f"- [ ] Upload {n_designs} designs",
            "- [ ] Verify preview on platform",
            "- [ ] Set collection/tag grouping",
            "",
        ]

    lines += [
        "---",
        "",
        "## General Checklist",
        "",
        "- [ ] Preview mosaic reviewed (`designs/preview_mosaic.png`)",
        "- [ ] All designs at correct resolution",
        "- [ ] No copyrighted elements",
        "- [ ] Tags diversity (not all same root keyword)",
        "- [ ] Pricing set per platform royalty",
        "- [ ] First design up and approved before bulk upload",
        "",
        f"> Generated: {datetime.utcnow().isoformat()}Z",
    ]

    (listing_dir / "upload_checklist.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[Merch Produce] upload_checklist.md écrit")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def run_produce():
    # Locate merch directory
    merch_dir_env = os.environ.get("MERCH_DIR", "").strip()
    if merch_dir_env:
        merch_dir = Path(merch_dir_env)
    else:
        print("[Merch Produce] MERCH_DIR non défini, recherche du dernier CdC approuvé...")
        merch_dir = _find_latest_approved()
        if not merch_dir:
            print("[Merch Produce] Aucun CdC approuvé trouvé dans products/merch/")
            print("  Approuver via: éditer gate_cdc → 'approved' dans cdc.json, puis relancer.")
            sys.exit(0)

    cdc_path = merch_dir / "cdc.json"
    if not cdc_path.exists():
        print(f"[Merch Produce] ERREUR: {cdc_path} introuvable.")
        sys.exit(1)

    try:
        cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[Merch Produce] ERREUR lecture cdc.json: {e}")
        sys.exit(1)

    gate = cdc.get("gate_cdc", "pending")
    if gate == "pending":
        print(f"[Merch Produce] GATE: pending — éditer gate_cdc → 'approved' dans {cdc_path}")
        sys.exit(0)
    if gate == "rejected":
        print(f"[Merch Produce] GATE: rejected — ce CdC a été rejeté. Relancer agent_merch_design_cdc.py.")
        sys.exit(0)
    if gate != "approved":
        print(f"[Merch Produce] GATE inconnu: '{gate}' — valeurs attendues: pending|approved|rejected")
        sys.exit(1)

    designs = cdc.get("designs", [])
    spec = cdc.get("spec_production", {})
    ct = cdc.get("concept_theme", {})
    total = len(designs)

    if total == 0:
        print("[Merch Produce] Aucun design dans le CdC.")
        sys.exit(1)

    print(f"[Merch Produce] Collection: {ct.get('titre', merch_dir.name)}")
    print(f"[Merch Produce] Dossier   : {merch_dir}")
    print(f"[Merch Produce] Designs   : {total}")
    print()

    # Create subdirectories
    designs_dir = merch_dir / "designs"
    raw_dir = merch_dir / "designs" / "_raw"
    listing_dir = merch_dir / "listing"
    designs_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    listing_dir.mkdir(parents=True, exist_ok=True)

    failed = []
    skipped = 0
    produced = 0

    for design in designs:
        n = design.get("n", 0)
        sous_theme = design.get("sous_theme", f"design_{n}")
        prompt = design.get("prompt_pollinations", "")
        # Forcer l'exclusion de tout texte généré par l'IA — le texte est ajouté
        # proprement par Pillow après. L'IA génère souvent du texte illisible/déformé.
        NO_TEXT_SUFFIX = ", no text, no words, no letters, no typography, illustration only"
        if NO_TEXT_SUFFIX.strip(", ") not in prompt:
            prompt = prompt.rstrip(", ") + NO_TEXT_SUFFIX
        final_path = designs_dir / f"design_{n:02d}.png"
        raw_path = raw_dir / f"design_{n:02d}_raw.png"

        # Skip if already produced
        if final_path.exists():
            print(f"[{n}/{total}] {sous_theme} — déjà existant, skip")
            skipped += 1
            continue

        print(f"[{n}/{total}] {sous_theme} — téléchargement Pollinations...")

        if not prompt:
            print(f"  WARNING: prompt vide pour design #{n}, skip")
            failed.append(n)
            continue

        # Download raw image
        ok = _download_image(prompt, raw_path)
        if not ok:
            print(f"  ECHEC téléchargement design #{n} ({sous_theme})")
            failed.append(n)
            time.sleep(DOWNLOAD_DELAY)
            continue

        # Compose final design with text overlay
        print(f"  Composition du design #{n}...")
        compose_ok = _compose_design(raw_path, design, spec, final_path)
        if compose_ok:
            print(f"[{n}/{total}] {sous_theme} ✓")
            produced += 1
        else:
            print(f"  ECHEC composition design #{n}")
            failed.append(n)

        time.sleep(DOWNLOAD_DELAY)

    print()
    print(f"[Merch Produce] Production terminée: {produced} produits, {skipped} skippés, {len(failed)} échecs")
    if failed:
        print(f"  Designs en échec: {failed}")

    # Generate mosaic
    print("[Merch Produce] Génération de la mosaïque aperçu...")
    mosaic_path = designs_dir / "preview_mosaic.png"
    _generate_mosaic(designs_dir, designs, mosaic_path)

    # Generate listing files
    _write_tags(listing_dir, cdc)
    _write_upload_checklist(listing_dir, cdc)

    # Update cdc.json with production status
    cdc["production_status"] = {
        "date_production": date.today().isoformat(),
        "total_designs": total,
        "produced": produced,
        "skipped": skipped,
        "failed": failed,
        "mosaic_path": str(mosaic_path.relative_to(merch_dir)),
    }
    cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Merch Produce] cdc.json mis à jour (production_status)")
    print()
    print(f"Aperçu mosaïque : {mosaic_path}")
    print(f"Checklist upload: {listing_dir / 'upload_checklist.md'}")


if __name__ == "__main__":
    run_produce()
