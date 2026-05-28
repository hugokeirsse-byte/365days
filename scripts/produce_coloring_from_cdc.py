#!/usr/bin/env python3
"""
Production Coloring Book depuis CdC validé — gate_cdc=approved requis.

Pipeline :
  1. Génère une illustration COULEUR normale (meilleure qualité source)
  2. Extraction de contours propres (GaussianBlur → FIND_EDGES → enhance → invert)
  3. Upscale LANCZOS × 2 (Runware quand disponible)
  4. Assemble PDF 8.5×11 inches KDP-ready

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
    from PIL import Image, ImageOps, ImageFilter, ImageEnhance
except ImportError:
    print("ERREUR : Pillow non installé. pip install Pillow")
    sys.exit(2)

try:
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.utils import ImageReader
except ImportError:
    print("ERREUR : reportlab non installé. pip install reportlab")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent

# KDP 8.5×11 interior
PAGE_W = 8.5 * inch
PAGE_H = 11.0 * inch
MARGIN = 0.75 * inch

# Pollinations : image couleur haute résolution
# On génère en couleur d'abord → meilleure source pour extraction de contours
IMG_W = 1664
IMG_H = 2160
# Upscale final × 2 → 3328×4320px (300 DPI KDP 11×14")
UPSCALE = 2


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


def build_color_prompt(modifiers: list, theme_keywords: list, page_n: int) -> str:
    """
    Génère un prompt pour une illustration COULEUR normale.
    L'extraction de contours est faite en post-traitement — pas dans le prompt.
    Résultat bien meilleur qu'une demande directe de 'coloring page'.
    """
    modifier = modifiers[(page_n - 1) % len(modifiers)] if modifiers else ""
    theme_hint = ", ".join(theme_keywords[:5]) if theme_keywords else ""
    # Illustration couleur riche — les contours seront extraits par Pillow
    return (
        f"beautiful detailed illustration, {modifier}, {theme_hint}, "
        f"rich colors, clean composition, professional digital art, "
        f"intricate details, vibrant, no text, centered composition"
    ).strip(", ")


def download_pollinations(prompt: str, out_path: Path) -> bool:
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


def extract_line_art(raw_path: Path, out_path: Path):
    """
    Convertit une illustration couleur en page de coloriage ligne propre.

    Pipeline :
    1. Légère réduction du bruit (GaussianBlur)
    2. Conversion en niveaux de gris
    3. Extraction des contours (FIND_EDGES = différence de pixels voisins)
    4. Amplification du contraste pour lignes nettes
    5. Inversion (lignes noires sur fond blanc)
    6. Seuil pour éliminer le gris résiduel
    7. Upscale × 2 LANCZOS (qualité impression)
    """
    img = Image.open(raw_path).convert("RGB")

    # 1. Lissage léger pour réduire le bruit (pixels isolés)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))

    # 2. Niveaux de gris
    gray = img.convert("L")

    # 3. Extraction des contours (détection de bords)
    edges = gray.filter(ImageFilter.FIND_EDGES)

    # 4. Amplifier le contraste pour avoir des lignes marquées
    enhancer = ImageEnhance.Contrast(edges)
    edges = enhancer.enhance(8.0)

    # 4b. Légère augmentation de la netteté
    edges = edges.filter(ImageFilter.SHARPEN)
    edges = edges.filter(ImageFilter.SHARPEN)

    # 5. Inversion : lignes noires sur fond blanc
    inverted = ImageOps.invert(edges)

    # 6. Seuil : élimine le gris résiduel → noir pur ou blanc pur
    bw = inverted.point(lambda x: 0 if x < 210 else 255)

    # 7. Upscale × 2 pour qualité impression (LANCZOS = meilleure qualité PIL)
    w, h = bw.size
    upscaled = bw.resize((w * UPSCALE, h * UPSCALE), Image.LANCZOS)

    # Sauvegarder en RGB blanc + canal L B&W
    result = Image.new("RGB", upscaled.size, (255, 255, 255))
    result.paste(upscaled)
    result.save(out_path, "PNG", dpi=(300, 300))


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

    # Lire les infos thème depuis le CdC (le style_base du CdC peut être "coloring page"
    # mais on l'ignore — on génère en couleur et on extrait les contours après)
    modifiers = prompts_cfg.get("style_modificateurs", [])
    theme_keywords = prompts_cfg.get("theme_keywords", [concept.get("theme_principal", titre)])

    images_dir = coloring_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = images_dir / "_raw"
    raw_dir.mkdir(exist_ok=True)

    print(f"\n[Coloring] Production: '{titre}' — {nb_pages} pages")
    print(f"[Coloring] Pipeline: illustration couleur → extraction contours → upscale ×{UPSCALE}")
    print(f"[Coloring] Source: {coloring_dir.name}")

    generated = 0
    failed = []

    for n in range(1, nb_pages + 1):
        clean_path = images_dir / f"page_{n:02d}.png"
        if clean_path.exists():
            print(f"  [{n}/{nb_pages}] Skip (déjà généré)")
            generated += 1
            continue

        # Générer une illustration COULEUR normale (pas "coloring page")
        prompt = build_color_prompt(modifiers, theme_keywords, n)
        print(f"  [{n}/{nb_pages}] Génération couleur + extraction contours...")

        raw_path = raw_dir / f"raw_{n:02d}.png"
        ok = download_pollinations(prompt, raw_path)
        if not ok:
            failed.append(n)
            time.sleep(2)
            continue

        try:
            extract_line_art(raw_path, clean_path)
            generated += 1
            print(f"  [{n}/{nb_pages}] ✓")
        except Exception as e:
            print(f"  [{n}/{nb_pages}] ✗ Extraction contours: {e}")
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
