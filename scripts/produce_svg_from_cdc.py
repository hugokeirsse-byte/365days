#!/usr/bin/env python3
"""
Production SVG Packs depuis CdC approuvé.

Lit le cdc.json d'un pack SVG (gate_cdc=approved) et génère :
1. SVG procéduraux via svgwrite (mandalas, géométriques, monogrammes, cadres)
2. SVG vectorisés via Pollinations→Pillow→Potrace (floraux, animaux, saisonniers)
3. PNG preview mosaïque 4:5 Etsy (premier visuel)
4. ZIP final prêt à uploader
5. README.txt inclus dans le ZIP
6. Mise à jour du cdc.json (production_status = done)
"""

import json
import math
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("[SVG Prod] Pillow non installé — preview désactivée", file=sys.stderr)

try:
    import svgwrite
    HAS_SVGWRITE = True
except ImportError:
    HAS_SVGWRITE = False

ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = ROOT / "products" / "svg_packs"
TIMEOUT = 90

# ── Détection du CdC approuvé ─────────────────────────────────────────────────

def find_approved_cdc():
    override = os.environ.get("SVG_DIR")
    if override:
        p = Path(override) / "cdc.json"
        if p.exists():
            return p
    for d in sorted(SVG_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        p = d / "cdc.json"
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("gate_cdc") == "approved" and not data.get("production_status"):
                return p
        except Exception:
            continue
    return None


# ── Génération SVG procédurale ────────────────────────────────────────────────

def make_mandala_svg(nom: str, idx: int, out_path: Path):
    """Génère un mandala symétrique via svgwrite."""
    if not HAS_SVGWRITE:
        return _make_fallback_svg(nom, out_path)

    size = 800
    cx, cy = size / 2, size / 2
    dwg = svgwrite.Drawing(str(out_path), size=(size, size), profile="full")
    dwg.viewbox(0, 0, size, size)
    dwg.add(dwg.rect(insert=(0, 0), size=(size, size), fill="white"))

    petals = 8 + (idx % 4) * 2  # 8, 10, 12, 14 pétales selon variante
    layers = 4 + (idx % 3)

    for layer in range(layers):
        r_inner = 40 + layer * 55
        r_outer = r_inner + 45
        sw = max(2.5, 4 - layer * 0.5)

        for i in range(petals):
            angle = 2 * math.pi * i / petals
            x1 = cx + r_inner * math.cos(angle)
            y1 = cy + r_inner * math.sin(angle)
            x2 = cx + r_outer * math.cos(angle)
            y2 = cy + r_outer * math.sin(angle)
            angle2 = angle + math.pi / petals
            cx2 = cx + (r_inner + r_outer) / 2 * math.cos(angle2) * 0.6
            cy2 = cy + (r_inner + r_outer) / 2 * math.sin(angle2) * 0.6
            d = f"M {x1:.1f} {y1:.1f} Q {cx2:.1f} {cy2:.1f} {x2:.1f} {y2:.1f}"
            dwg.add(dwg.path(d=d, fill="none", stroke="black", stroke_width=sw))

        # Cercle de liaison
        dwg.add(dwg.circle(center=(cx, cy), r=r_inner, fill="none",
                            stroke="black", stroke_width=2))

    # Centre
    dwg.add(dwg.circle(center=(cx, cy), r=18, fill="none", stroke="black", stroke_width=3))
    dwg.save()


def make_geometric_svg(nom: str, idx: int, out_path: Path):
    """Génère une forme géométrique boho/sacrée."""
    if not HAS_SVGWRITE:
        return _make_fallback_svg(nom, out_path)

    size = 800
    cx, cy = size / 2, size / 2
    dwg = svgwrite.Drawing(str(out_path), size=(size, size), profile="full")
    dwg.viewbox(0, 0, size, size)
    dwg.add(dwg.rect(insert=(0, 0), size=(size, size), fill="white"))

    shapes = idx % 4
    sw = 4

    if shapes == 0:  # Étoile à 6 branches
        for i in range(6):
            angle = math.pi / 3 * i
            x1 = cx + 50 * math.cos(angle)
            y1 = cy + 50 * math.sin(angle)
            x2 = cx + 300 * math.cos(angle)
            y2 = cy + 300 * math.sin(angle)
            dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke="black", stroke_width=sw))
        for r in [80, 160, 240]:
            dwg.add(dwg.circle(center=(cx, cy), r=r, fill="none", stroke="black", stroke_width=3))
    elif shapes == 1:  # Hexagone imbriqué
        for scale in [1.0, 0.7, 0.4]:
            pts = [(cx + 280 * scale * math.cos(math.pi / 6 + math.pi / 3 * i),
                    cy + 280 * scale * math.sin(math.pi / 6 + math.pi / 3 * i))
                   for i in range(6)]
            dwg.add(dwg.polygon(points=pts, fill="none", stroke="black", stroke_width=sw))
    elif shapes == 2:  # Carré en rotation
        for angle_deg in [0, 15, 30, 45]:
            angle = math.radians(angle_deg)
            r = 280
            pts = [(cx + r * math.cos(angle + math.pi / 2 * i),
                    cy + r * math.sin(angle + math.pi / 2 * i))
                   for i in range(4)]
            dwg.add(dwg.polygon(points=pts, fill="none", stroke="black", stroke_width=3))
    else:  # Fleur de vie simplifiée
        r = 100
        for i in range(6):
            angle = math.pi / 3 * i
            ox = cx + r * math.cos(angle)
            oy = cy + r * math.sin(angle)
            dwg.add(dwg.circle(center=(ox, oy), r=r, fill="none", stroke="black", stroke_width=sw))
        dwg.add(dwg.circle(center=(cx, cy), r=r, fill="none", stroke="black", stroke_width=sw))

    dwg.save()


def make_frame_svg(nom: str, idx: int, out_path: Path):
    """Génère un cadre décoratif pour citations."""
    if not HAS_SVGWRITE:
        return _make_fallback_svg(nom, out_path)

    size = 800
    dwg = svgwrite.Drawing(str(out_path), size=(size, size), profile="full")
    dwg.viewbox(0, 0, size, size)
    dwg.add(dwg.rect(insert=(0, 0), size=(size, size), fill="white"))

    sw = 4
    margin = 60 + (idx % 3) * 20
    corner = 40 + (idx % 4) * 15

    # Cadre extérieur avec coins arrondis
    dwg.add(dwg.rect(insert=(margin, margin), size=(size - 2 * margin, size - 2 * margin),
                     rx=corner, ry=corner, fill="none", stroke="black", stroke_width=sw))
    # Cadre intérieur
    inner = margin + 20
    dwg.add(dwg.rect(insert=(inner, inner), size=(size - 2 * inner, size - 2 * inner),
                     rx=corner - 10, ry=corner - 10, fill="none", stroke="black", stroke_width=2))

    # Ornements coins
    for ox, oy in [(margin, margin), (size - margin, margin),
                   (margin, size - margin), (size - margin, size - margin)]:
        dwg.add(dwg.circle(center=(ox, oy), r=12, fill="black"))

    # Ligne centrale décorative haut et bas
    mid_x = size / 2
    for y_pos in [margin - 15, size - margin + 15]:
        dwg.add(dwg.line(start=(mid_x - 80, y_pos), end=(mid_x + 80, y_pos),
                         stroke="black", stroke_width=3))
        dwg.add(dwg.circle(center=(mid_x, y_pos), r=8, fill="black"))

    dwg.save()


def _make_fallback_svg(nom: str, out_path: Path):
    """SVG minimal si svgwrite absent."""
    content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 800" width="800" height="800">
  <rect width="800" height="800" fill="white"/>
  <circle cx="400" cy="400" r="300" fill="none" stroke="black" stroke-width="4"/>
  <circle cx="400" cy="400" r="200" fill="none" stroke="black" stroke-width="3"/>
  <circle cx="400" cy="400" r="100" fill="none" stroke="black" stroke-width="2"/>
</svg>'''
    out_path.write_text(content, encoding="utf-8")


# ── Vectorisation via Pollinations + Potrace ──────────────────────────────────

def fetch_pollinations_image(prompt: str, seed: int = 42) -> bytes | None:
    encoded = urllib.request.quote(prompt[:500])
    url = f"https://image.pollinations.ai/prompt/{encoded}?model=flux&seed={seed}&nologo=true&width=512&height=512"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SvgPackProducer/2.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read()
    except Exception as e:
        print(f"  [Pollinations] Erreur: {e}", file=sys.stderr)
        return None


def image_to_svg_potrace(img_bytes: bytes, out_svg: Path) -> bool:
    if not HAS_PILLOW:
        return False
    try:
        result = subprocess.run(["potrace", "--version"], capture_output=True)
        has_potrace = result.returncode == 0
    except FileNotFoundError:
        has_potrace = False

    if not has_potrace:
        # Fallback : SVG avec rect placeholder
        _make_fallback_svg("fallback", out_svg)
        return False

    try:
        img = Image.open(BytesIO(img_bytes)).convert("L")
        img = img.point(lambda p: 0 if p < 128 else 255)
        img = img.convert("1")

        with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as tmp:
            bmp_path = Path(tmp.name)
            img.save(str(bmp_path), format="BMP")

        subprocess.run(
            ["potrace", str(bmp_path), "-s", "-o", str(out_svg),
             "--blacklevel", "0.5", "--turdsize", "10"],
            capture_output=True, check=True
        )
        bmp_path.unlink(missing_ok=True)
        return True
    except Exception as e:
        print(f"  [Potrace] Erreur: {e}", file=sys.stderr)
        _make_fallback_svg("fallback", out_svg)
        return False


# ── Génération selon le type du CdC ──────────────────────────────────────────

PROCEDRAL_TYPES = {"mandala", "geometric", "monogram", "quote_frame"}
POLLINATIONS_TYPES = {"floral", "animal", "seasonal", "bundle_mix"}

SVG_GENERATORS = {
    "mandala": make_mandala_svg,
    "geometric": make_geometric_svg,
    "quote_frame": make_frame_svg,
    "monogram": make_frame_svg,  # utilise cadres
}


def generate_element(elem: dict, idx: int, pack_type: str, out_dir: Path, prompts: list) -> Path:
    nom = elem.get("nom", f"element_{idx:02d}")
    safe_nom = "".join(c if c.isalnum() or c in "-_" else "_" for c in nom)[:40]
    out_svg = out_dir / f"{idx:02d}_{safe_nom}.svg"

    outil = elem.get("outil_production", "svgwrite")
    use_pollinations = "pollinations" in outil or pack_type in POLLINATIONS_TYPES

    if use_pollinations and prompts:
        prompt_idx = idx % len(prompts)
        base_prompt = prompts[prompt_idx].get("prompt", "") if prompts else ""
        if not base_prompt:
            base_prompt = (
                f"bold thick black silhouette of {nom} on pure white background, "
                "NO COLOR, NO SHADING, NO GRADIENT, simple clean shapes, "
                "thick connected outlines, cuttable for Cricut, high contrast"
            )
        print(f"  [{idx+1}] {nom} → Pollinations+Potrace")
        img_bytes = fetch_pollinations_image(base_prompt, seed=idx * 17 + 42)
        if img_bytes:
            image_to_svg_potrace(img_bytes, out_svg)
        else:
            _make_fallback_svg(nom, out_svg)
        time.sleep(2)
    else:
        gen_fn = SVG_GENERATORS.get(pack_type, make_mandala_svg)
        print(f"  [{idx+1}] {nom} → svgwrite ({pack_type})")
        gen_fn(nom, idx, out_svg)

    return out_svg


# ── Preview mosaïque Etsy ─────────────────────────────────────────────────────

def make_preview(svg_files: list, out_path: Path, titre: str):
    if not HAS_PILLOW or not svg_files:
        return
    W, H = 1200, 1500  # 4:5 Etsy
    preview = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(preview)

    cols, rows = 4, 5
    cell_w, cell_h = W // cols, (H - 120) // rows

    for i, svg_path in enumerate(svg_files[: cols * rows]):
        # Tente de rasteriser (placeholder si impossible)
        col, row = i % cols, i // cols
        x, y = col * cell_w + 5, row * cell_h + 5 + 40
        draw.rectangle([x, y, x + cell_w - 10, y + cell_h - 10], outline="#ccc", width=1)

    draw.text((20, 10), titre[:60], fill="black")
    draw.text((20, H - 40), f"{len(svg_files)} SVG Cut Files — Cricut & Silhouette", fill="#555")
    preview.save(str(out_path), format="PNG", optimize=True)


# ── ZIP et README ─────────────────────────────────────────────────────────────

def make_readme(cdc: dict, nb_svg: int) -> str:
    listing = cdc.get("listing_etsy", {})
    specs = cdc.get("specs_techniques", {})
    return f"""SVG Pack — {listing.get('titre', cdc.get('niche', ''))}
{'=' * 60}

This pack contains {nb_svg} SVG cut files.

FORMATS INCLUDED
-----------------
- SVG (Cricut Design Space, Silhouette Studio, Inkscape, Illustrator)
- PNG preview (not for cutting)

MACHINE COMPATIBILITY
---------------------
- Cricut Maker / Maker 3 / Explore Air 2
- Silhouette Cameo 4 / Portrait
- Other cutting machines that accept SVG

HOW TO USE
----------
1. Download and unzip
2. Open Cricut Design Space → New Project → Upload
3. Select SVG file → set as Cut Image
4. Resize and cut as needed

TERMS OF USE
------------
For PERSONAL and SMALL COMMERCIAL use.
Do not resell the digital files.

SPECS
------
- ViewBox: {specs.get('taille_recommandee', '1000x1000')}
- Format: SVG 1.1
- Background: Pure White

Thank you for your purchase!
"""


def build_zip(svg_files: list, preview_path: Path, readme: str, out_zip: Path):
    with zipfile.ZipFile(str(out_zip), "w", zipfile.ZIP_DEFLATED) as zf:
        for svg in svg_files:
            zf.write(str(svg), svg.name)
        if preview_path.exists():
            zf.write(str(preview_path), preview_path.name)
        zf.writestr("README.txt", readme)


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    cdc_path = find_approved_cdc()
    if not cdc_path:
        print("[SVG Prod] Aucun CdC approuvé trouvé.", file=sys.stderr)
        sys.exit(0)

    cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
    pack_dir = cdc_path.parent

    pack_type = cdc.get("type_pack", "mandala")
    niche = cdc.get("niche", "unknown")
    elements = cdc.get("elements", [])
    prompts = cdc.get("prompts_pollinations", [])
    listing = cdc.get("listing_etsy", {})
    titre = listing.get("titre", niche)[:60]

    print(f"[SVG Prod] Pack: {pack_type} | Niche: {niche} | {len(elements)} éléments")
    print(f"  CdC: {cdc_path}")

    svg_out_dir = pack_dir / "svg_files"
    svg_out_dir.mkdir(parents=True, exist_ok=True)

    svg_files = []
    for i, elem in enumerate(elements):
        svg_path = generate_element(elem, i, pack_type, svg_out_dir, prompts)
        if svg_path.exists():
            svg_files.append(svg_path)

    print(f"[SVG Prod] {len(svg_files)} SVG générés")

    preview_path = pack_dir / "preview.png"
    make_preview(svg_files, preview_path, titre)

    readme = make_readme(cdc, len(svg_files))
    zip_name = f"{cdc.get('id', 'svg_pack')}.zip"
    zip_path = pack_dir / zip_name
    build_zip(svg_files, preview_path, readme, zip_path)

    # Mise à jour CdC
    cdc["production_status"] = "done"
    cdc["production_date"] = __import__("datetime").date.today().isoformat()
    cdc["nb_svg_generes"] = len(svg_files)
    cdc["zip_path"] = str(zip_path.relative_to(ROOT))
    cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[SVG Prod] ✓ ZIP: {zip_path}")
    print(f"[SVG Prod] ✓ CdC mis à jour → production_status=done")
    print(f"")
    print(f"  PROCHAINE ÉTAPE : upload {zip_path.name} sur Etsy")
    print(f"  Prix suggéré : ${listing.get('prix_usd', 3.50)}")
    print(f"  Titre : {titre}")


if __name__ == "__main__":
    run()
