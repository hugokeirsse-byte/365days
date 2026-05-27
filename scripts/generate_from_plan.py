import os
import sys
import json
import logging
from pathlib import Path

# Configuration des chemins et imports requis par le cahier des charges
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

from lib.image_router import generate as ir_generate
from lib.image_to_coloring import convert as coloring_convert

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("generate_from_plan")

def main():
    # 1. Chargement et validation des variables d'environnement
    brief_id = os.environ.get("BRIEF_ID")
    if not brief_id:
        logger.error("La variable d'environnement BRIEF_ID est requise.")
        sys.exit(1)

    line_thickness = int(os.environ.get("LINE_THICKNESS", 2))
    
    max_pages_env = os.environ.get("MAX_PAGES")
    max_pages = int(max_pages_env) if max_pages_env else None

    # Définition des chemins d'accès
    brief_path = ROOT / "data" / "briefs" / f"{brief_id}.json"
    gate1_dir = ROOT / "products" / "coloring_books" / "_gate1" / brief_id
    plan_path = gate1_dir / "production_plan.json"
    pages_dir = gate1_dir / "pages"
    report_path = gate1_dir / "generation_report.json"

    # 2. Vérification de la validation du brief (gate_start == approved)
    if not brief_path.exists():
        logger.error(f"Fichier brief introuvable : {brief_path}")
        sys.exit(1)

    try:
        with open(brief_path, "r", encoding="utf-8") as f:
            brief_data = json.load(f)
    except Exception as e:
        logger.error(f"Impossible de lire le brief {brief_path} : {e}")
        sys.exit(1)

    if brief_data.get("gate_start") != "approved":
        logger.error(f"Le brief {brief_id} n'est pas approuvé (gate_start = {brief_data.get('gate_start')}).")
        sys.exit(1)

    # 3. Chargement du plan de production
    if not plan_path.exists():
        logger.error(f"Fichier production_plan.json introuvable : {plan_path}")
        sys.exit(1)

    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            production_plan = json.load(f)
    except Exception as e:
        logger.error(f"Impossible de lire le plan de production {plan_path} : {e}")
        sys.exit(1)

    # Création du dossier de destination pour les pages
    pages_dir.mkdir(parents=True, exist_ok=True)

    # Initialisation du rapport de génération
    report = {
        "pages": [],
        "summary": {
            "ok": 0,
            "failed": 0,
            "skipped": 0
        }
    }

    # Prompt négatif par défaut pour optimiser le rendu "line-art"
    default_negative_prompt = (
        "color, colored, shading, shadows, gradients, grayscale, photo, realistic, "
        "background noise, dark background, blurry, textured paper"
    )

    # 4. Traitement des pages de coloriage
    pages_to_process = production_plan.get("pages", [])
    if max_pages is not None:
        logger.info(f"Limite MAX_PAGES active : traitement de {max_pages} pages max.")
        pages_to_process = pages_to_process[:max_pages]

    for page in pages_to_process:
        index = page.get("index")
        prompt = page.get("prompt")
        
        if index is None or not prompt:
            logger.warning(f"Page invalide ignorée (index ou prompt manquant) : {page}")
            continue

        page_filename = f"page_{index:03d}.png"
        dest_path = pages_dir / page_filename
        tmp_path = pages_dir / f"tmp_{page_filename}"

        # Idempotence : si le fichier final existe déjà, on passe
        if dest_path.exists():
            logger.info(f"La page {page_filename} existe déjà. Passage (idempotent).")
            report["pages"].append({
                "page_number": index,
                "status": "skipped",
                "provider_used": "existing"
            })
            report["summary"]["skipped"] += 1
            continue

        logger.info(f"Génération de la page {index:03d}...")
        try:
            # Génération de l'image brute via le routeur
            # Le routeur gère l'ordre des providers via l'env var IMAGE_PROVIDERS
            success = ir_generate(
                prompt=prompt,
                negative_prompt=default_negative_prompt,
                width=832,
                height=1152,
                dest=str(tmp_path)
            )

            if success and tmp_path.exists():
                # Conversion en line-art (coloriage)
                coloring_convert(
                    input_path=tmp_path,
                    output_path=dest_path,
                    line_thickness=line_thickness
                )
                
                # Nettoyage du fichier temporaire
                if tmp_path.exists():
                    tmp_path.unlink()

                if dest_path.exists():
                    logger.info(f"Page {page_filename} générée et convertie avec succès.")
                    report["pages"].append({
                        "page_number": index,
                        "status": "ok",
                        "provider_used": os.environ.get("IMAGE_PROVIDERS", "default")
                    })
                    report["summary"]["ok"] += 1
                else:
                    raise RuntimeError("Le fichier converti n'a pas pu être créé.")
            else:
                raise RuntimeError("La génération de l'image brute a échoué ou le fichier temporaire est manquant.")

        except Exception as e:
            logger.error(f"Échec de la génération pour la page {index:03d} : {e}")
            if tmp_path.exists():
                tmp_path.unlink()
            report["pages"].append({
                "page_number": index,
                "status": "failed",
                "provider_used": "none"
            })
            report["summary"]["failed"] += 1

    # 5. Traitement des couvertures (Covers)
    covers_plan = production_plan.get("covers", {})
    for cover_type in ["front", "back"]:
        cover_data = covers_plan.get(cover_type)
        if not cover_data:
            continue

        cover_filename = f"cover_{cover_type}.png"
        dest_path = pages_dir / cover_filename
        prompt = cover_data.get("prompt")

        if not prompt:
            logger.warning(f"Prompt manquant pour la couverture {cover_type}.")
            continue

        if dest_path.exists():
            logger.info(f"La couverture {cover_filename} existe déjà. Passage.")
            report["pages"].append({
                "page_number": f"cover_{cover_type}",
                "status": "skipped",
                "provider_used": "existing"
            })
            report["summary"]["skipped"] += 1
            continue

        logger.info(f"Génération de la couverture {cover_type} (KDP 300DPI)...")
        try:
            # Les couvertures restent en couleur, pas de conversion line-art requise
            success = ir_generate(
                prompt=prompt,
                negative_prompt="blurry, low quality, distorted",
                width=2625,
                height=3375,
                dest=str(dest_path)
            )

            if success and dest_path.exists():
                logger.info(f"Couverture {cover_filename} générée avec succès.")
                report["pages"].append({
                    "page_number": f"cover_{cover_type}",
                    "status": "ok",
                    "provider_used": os.environ.get("IMAGE_PROVIDERS", "default")
                })
                report["summary"]["ok"] += 1
            else:
                raise RuntimeError("La génération de la couverture a échoué.")

        except Exception as e:
            logger.error(f"Échec de la génération pour la couverture {cover_type} : {e}")
            report["pages"].append({
                "page_number": f"cover_{cover_type}",
                "status": "failed",
                "provider_used": "none"
            })
            report["summary"]["failed"] += 1

    # 6. Écriture du rapport de génération
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Rapport de génération écrit avec succès dans {report_path}")
    except Exception as e:
        logger.error(f"Impossible d'écrire le rapport de génération : {e}")

    # Sortie propre (Exit 0 même si échecs partiels, conformément au cahier des charges)
    logger.info(f"Processus terminé. Succès: {report['summary']['ok']}, Échecs: {report['summary']['failed']}, Ignorés: {report['summary']['skipped']}")
    sys.exit(0)

if __name__ == "__main__":
    main()