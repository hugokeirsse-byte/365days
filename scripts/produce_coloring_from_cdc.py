#!/usr/bin/env python3
"""
Production Coloring Book depuis CdC validé — gate_cdc=approved requis.

Lit les prompts Pollinations du CdC et génère N images KDP-ready.
Assemble un PDF 8.5×11 inches prêt pour impression KDP.

Variables d'env :
  COLORING_DIR — chemin du produit (products/coloring_books/{slug})
                 si absent, cherche le dernier approuvé automatiquement
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from PIL import Image, ImageOps, ImageFilter
except ImportError:
    print("ERREUR : Pillow non installé. pip install Pillow")
    sys.exit(2)

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.utils import ImageReader
except ImportError:
    print("ERREUR : reportlab non installé. pip install reportlab")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent

# KDP 8.5×11 interior (with bleed)
PAGE_W = 8.5 * inch
PAGE_H = 11.0 * inch
MARGIN = 0.75 * inch

# Pollinations target size (portrait, high-res for 300 DPI at 8.5×11)
IMG_W = 2550
IMG_H = 3300


def find_approved_coloring() -> Path | None:
    base = ROOT / "products" / "coloring_books"
    if not base.exists():
        return None
    for d in sorted(base.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        cdc_path = d / "cdc.json"
        if not cdc_path.exists():
            continue
        try:
            cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
            if cdc.get("gate_cdc") == "approved" and not cdc.get("production_status"):
                return d
        except Exception:
            continue
    return None


def build_prompt(style_base: str, modifiers: list, theme_keywords: list,
                 negative_keywords: list, page_n: int) -> tuple[str, str]:
    modifier = modifiers[(page_n - 1) % len(modifiers)] if modifiers else ""
    theme_hint = ", ".join(theme_keywords[:4]) if theme_keywords else ""
    negative = ", ".join(negative_keywords[:6]) if negative_keywords else ""
    positive = f"{style_base}, {modifier}, {theme_hint}".strip(", ")
    return positive, negative


def download_pollinations(prompt: str, negative: str, out_path: Path) -> bool:
    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={IMG_W}&height={IMG_H}&nologo=true&model=flux"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = resp.read()
        out_path.write_bytes(data)
        return True
    except Exception as e:
        print(f"    ✗ Download error: {e}")
        return False


def clean_coloring_image(img_path: Path, out_path: Path):
    img = Image.open(img_path).convert("L")
    # High-contrast threshold to ensure pure black/white
    img = img.point(lambda x: 0 if x < 180 else 255)
    # Slight sharpening for cleaner lines
    img = img.filter(ImageFilter.SHARPEN)
    rgb = Image.new("RGB", img.size, (255, 255, 255))
    rgb.paste(img)
    rgb.save(out_path, "PNG", dpi=(300, 300))


def assemble_pdf(images: list[Path], out_pdf: Path, title: str):
    c = pdf_canvas.Canvas(str(out_pdf), pagesize=(PAGE_W, PAGE_H))
    c.setTitle(title)
    c.setAuthor("365days")

    for img_path in images:
        if not img_path.exists():
            c.showPage()
            continue
        try:
            c.drawImage(
                ImageReader(str(img_path)),
                MARGIN, MARGIN,
                width=PAGE_W - 2 * MARGIN,
                height=PAGE_H - 2 * MARGIN,
                preserveAspectRatio=True,
                anchor="c",
            )
        except Exception as e:
            print(f"  [PDF] Erreur image {img_path.name}: {e}")
        c.showPage()

    c.save()
    size_mb = out_pdf.stat().st_size / 1_000_000
    print(f"  [PDF] {out_pdf.name} — {len(images)} pages — {size_mb:.1f} MB")


def run():
    coloring_dir_env = os.environ.get("COLORING_DIR", "").strip()

    if coloring_dir_env:
        coloring_dir = ROOT / coloring_dir_env
    else:
        coloring_dir = find_approved_coloring()

    if not coloring_dir:
        print("[Coloring] Aucun CdC approuvé trouvé dans products/coloring_books/")
        print("[Coloring] → Approuver un CdC: gate_cdc = 'approved' dans cdc.json")
        sys.exit(0)

    cdc_path = coloring_dir / "cdc.json"
    if not cdc_path.exists():
        print(f"[Coloring] cdc.json manquant: {cdc_path}")
        sys.exit(1)

    cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
    gate = cdc.get("gate_cdc", "pending")

    if gate == "pending":
        titre = cdc.get("concept", {}).get("titre_livre", cdc.get("concept", {}).get("theme_principal", "?"))
        print(f"[Coloring] GATE=PENDING — '{titre}' en attente de validation Hugo.")
        sys.exit(0)
    if gate == "rejected":
        print("[Coloring] GATE=REJECTED — CdC rejeté, production annulée.")
        sys.exit(0)

    concept = cdc.get("concept", {})
    prompts_cfg = cdc.get("prompts_pollinations", {})
    titre = concept.get("titre_livre", concept.get("theme_principal", coloring_dir.name))
    nb_pages = int(concept.get("nombre_pages", 30))

    style_base = prompts_cfg.get("style_base", "black and white coloring page, clean lines, white background, no gray, no shading")
    modifiers = prompts_cfg.get("style_modificateurs", [])
    theme_keywords = prompts_cfg.get("theme_keywords", [])
    negative_keywords = prompts_cfg.get("negative_keywords", [])

    images_dir = coloring_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = images_dir / "_raw"
    raw_dir.mkdir(exist_ok=True)

    print(f"\n[Coloring] Production: '{titre}' — {nb_pages} pages")
    print(f"[Coloring] Source: {coloring_dir.name}")

    generated = 0
    failed = []

    for n in range(1, nb_pages + 1):
        clean_path = images_dir / f"page_{n:02d}.png"
        if clean_path.exists():
            print(f"  [{n}/{nb_pages}] Skip (déjà généré)")
            generated += 1
            continue

        positive, negative = build_prompt(style_base, modifiers, theme_keywords, negative_keywords, n)
        print(f"  [{n}/{nb_pages}] Génération...")

        raw_path = raw_dir / f"raw_{n:02d}.png"
        ok = download_pollinations(positive, negative, raw_path)
        if not ok:
            failed.append(n)
            time.sleep(2)
            continue

        try:
            clean_coloring_image(raw_path, clean_path)
            generated += 1
            print(f"  [{n}/{nb_pages}] ✓")
        except Exception as e:
            print(f"  [{n}/{nb_pages}] ✗ Traitement image: {e}")
            failed.append(n)

        time.sleep(0.5)

    # Assemble PDF
    ordered = [images_dir / f"page_{n:02d}.png" for n in range(1, nb_pages + 1)]
    pdf_path = coloring_dir / f"{coloring_dir.name}.pdf"
    print(f"\n[Coloring] Assemblage PDF ({generated} pages)...")
    assemble_pdf([p for p in ordered if p.exists()], pdf_path, titre)

    # Update cdc.json
    cdc["production_status"] = {
        "date": str(__import__("datetime").date.today()),
        "pages_generees": generated,
        "pages_echouees": failed,
        "pdf": str(pdf_path.relative_to(ROOT)),
    }
    cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[Coloring] ✓ '{titre}' — {generated}/{nb_pages} pages — {pdf_path.name}")
    if failed:
        print(f"[Coloring] Pages échouées: {failed} (re-générer manuellement)")
    print(f"[Coloring] PDF KDP → {pdf_path}")
    print(f"[Coloring] → Uploader sur KDP: 8.5×11 inches, PDF intérieur")


if __name__ == "__main__":
    run()
