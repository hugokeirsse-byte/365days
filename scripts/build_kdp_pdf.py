#!/usr/bin/env python3
"""
Script de génération du PDF intérieur KDP-ready à partir des pages line-art.
Calcule les dimensions avec bleed, centre les images converties en niveaux de gris (L),
et génère le rapport de package KDP.
"""

import os
import sys
import json
import logging
from datetime import datetime
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def parse_trim(trim_str):
    """Parse une chaîne de format type '8.5x11' ou '8.5x11in' en (largeur, hauteur) floats."""
    try:
        clean_str = str(trim_str).lower().replace("in", "").strip()
        parts = clean_str.split("x")
        return float(parts[0]), float(parts[1])
    except Exception as e:
        logger.error(f"Erreur lors du parsing du trim '{trim_str}': {e}")
        raise


def parse_bleed(bleed_val):
    """Parse la valeur de bleed (string ou float) en float."""
    try:
        if isinstance(bleed_val, (int, float)):
            return float(bleed_val)
        clean_str = str(bleed_val).lower().replace("in", "").strip()
        return float(clean_str)
    except Exception as e:
        logger.error(f"Erreur lors du parsing du bleed '{bleed_val}': {e}")
        raise


def main():
    # 1. Récupération des paramètres (CLI ou Variables d'environnement)
    brief_id = None
    if len(sys.argv) > 1:
        brief_id = sys.argv[1]
    else:
        brief_id = os.environ.get("BRIEF_ID")

    if not brief_id:
        logger.error("BRIEF_ID manquant. Spécifiez-le en argument ou via la variable d'environnement BRIEF_ID.")
        sys.exit(1)

    dpi = int(os.environ.get("DPI", "300"))
    logger.info(f"Début de la génération KDP pour le brief: {brief_id} (DPI cible: {dpi})")

    # Définition des chemins
    brief_path = f"data/briefs/{brief_id}.json"
    gate1_dir = f"products/coloring_books/_gate1/{brief_id}"
    pages_dir = f"{gate1_dir}/pages"
    report_path = f"{gate1_dir}/generation_report.json"
    pdf_path = f"{gate1_dir}/interior.pdf"
    package_path = f"{gate1_dir}/kdp_package.json"

    # 2. Chargement du brief
    if not os.path.exists(brief_path):
        logger.error(f"Fichier brief introuvable: {brief_path}")
        sys.exit(1)

    with open(brief_path, "r", encoding="utf-8") as f:
        brief_data = json.load(f)

    format_cfg = brief_data.get("format", {})
    trim_raw = format_cfg.get("trim", "8.5x11")
    bleed_raw = format_cfg.get("bleed", 0.125)
    expected_pages = format_cfg.get("pages_interior", 30)

    trim_w, trim_h = parse_trim(trim_raw)
    bleed = parse_bleed(bleed_raw)

    # Calcul des dimensions finales de la page PDF en points (1 inch = 72 points)
    page_w_pt = (trim_w + 2 * bleed) * 72
    page_h_pt = (trim_h + 2 * bleed) * 72

    logger.info(f"Format cible: {trim_w}x{trim_h} in | Bleed: {bleed} in")
    logger.info(f"Dimensions PDF calculées: {page_w_pt:.2f}x{page_h_pt:.2f} pt ({page_w_pt/72:.3f}x{page_h_pt/72:.3f} in)")

    # 3. Vérification du rapport de génération si existant
    generation_ok = True
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                report_data = json.load(f)
            # On peut analyser le rapport ici si nécessaire
            logger.info("Rapport de génération trouvé et chargé.")
        except Exception as e:
            logger.warning(f"Impossible de lire le rapport de génération: {e}")

    # 4. Assemblage du PDF
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    c = canvas.Canvas(pdf_path, pagesize=(page_w_pt, page_h_pt))

    successful_pages = 0
    ready_for_gate2 = True

    for i in range(1, expected_pages + 1):
        img_name = f"page_{i:03d}.png"
        img_path = os.path.join(pages_dir, img_name)

        if os.path.exists(img_path):
            try:
                # Ouvrir l'image, convertir en niveaux de gris (L) puis RGB pour ReportLab
                with Image.open(img_path) as img:
                    img_gray = img.convert("L").convert("RGB")
                    img_w, img_h = img_gray.size

                    # Calcul du ratio pour centrer l'image sans déformation
                    scale = min(page_w_pt / img_w, page_h_pt / img_h)
                    draw_w = img_w * scale
                    draw_h = img_h * scale
                    x = (page_w_pt - draw_w) / 2
                    y = (page_h_pt - draw_h) / 2

                    # Dessiner un fond blanc opaque
                    c.setFillColorRGB(1, 1, 1)
                    c.rect(0, 0, page_w_pt, page_h_pt, fill=1, stroke=0)

                    # Dessiner l'image centrée
                    img_reader = ImageReader(img_gray)
                    c.drawImage(img_reader, x, y, width=draw_w, height=draw_h)
                    c.showPage()
                    successful_pages += 1

            except Exception as e:
                logger.error(f"Erreur lors du traitement de l'image {img_name}: {e}")
                ready_for_gate2 = False
        else:
            logger.warning(f"Page manquante: {img_name}")
            ready_for_gate2 = False

    # Sauvegarde du PDF
    try:
        c.save()
        logger.info(f"PDF enregistré avec succès: {pdf_path}")
    except Exception as e:
        logger.error(f"Échec de la sauvegarde du PDF: {e}")
        sys.exit(1)

    # Validation finale du nombre de pages
    if successful_pages != expected_pages:
        logger.warning(f"Nombre de pages générées ({successful_pages}) différent de l'attendu ({expected_pages})")
        ready_for_gate2 = False

    # 5. Écriture du rapport de package KDP
    package_data = {
        "built_at": datetime.utcnow().isoformat() + "Z",
        "page_count": successful_pages,
        "format": f"{trim_w}x{trim_h}in",
        "bleed": f"{bleed}in",
        "ready_for_gate2": ready_for_gate2
    }

    with open(package_path, "w", encoding="utf-8") as f:
        json.dump(package_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Package KDP écrit: {package_path}")
    logger.info(f"Statut final ready_for_gate2: {ready_for_gate2}")


if __name__ == "__main__":
    main()