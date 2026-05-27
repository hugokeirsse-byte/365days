import os
import sys
import json
from pathlib import Path

# Configuration des chemins et imports requis
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

try:
    from lib.image_router import generate as ir_generate
    from lib.image_to_coloring import convert as coloring_convert
except ImportError as e:
    print(f"Erreur d'importation des librairies internes : {e}", file=sys.stderr)
    sys.exit(1)


def main():
    # Récupération et validation des variables d'environnement
    brief_id = os.getenv("BRIEF_ID")
    if not brief_id:
        print("Erreur : La variable d'environnement BRIEF_ID est requise.", file=sys.stderr)
        sys.exit(1)

    line_thickness = int(os.getenv("LINE_THICKNESS", "2"))
    max_pages_env = os.getenv("MAX_PAGES")
    max_pages = int(max_pages_env) if max_pages_env else None

    # Définition des chemins d'accès
    brief_path = ROOT / "data" / "briefs" / f"{brief_id}.json"
    gate1_dir = ROOT / "products" / "coloring_books" / "_gate1" / brief_id
    plan_path = gate1_dir / "production_plan.json"
    pages_dir = gate1_dir / "pages"
    report_path = gate1_dir / "generation_report.json"

    # 1. Vérification de l'approbation du brief (gate_start == approved)
    if not brief_path.exists():
        print(f"Erreur : Le brief {brief_path} n'existe pas.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(brief_path, "r", encoding="utf-8") as f:
            brief_data = json.load(f)
    except Exception as e:
        print(f"Erreur lors de la lecture du brief : {e}", file=sys.stderr)
        sys.exit(1)

    gate_start = brief_data.get("gate_start") or brief_data.get("status")
    if gate_start != "approved":
        print(f"Erreur : Le brief {brief_id} n'est pas approuvé (gate_start={gate_start}).", file=sys.stderr)
        sys.exit(1)

    # Lecture du plan de production
    if not plan_path.exists():
        print(f"Erreur : Le plan de production {plan_path} n'existe pas.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
    except Exception as e:
        print(f"Erreur lors de la lecture du plan de production : {e}", file=sys.stderr)
        sys.exit(1)

    pages = plan_data.get("pages", [])
    covers = plan_data.get("covers", {})

    if max_pages is not None:
        pages = pages[:max_pages]

    pages_dir.mkdir(parents=True, exist_ok=True)
    report_pages = []

    # Paramètres par défaut pour la génération de coloriages
    default_neg_prompt = "color, colored, shading, shadows, textured, realistic, photo, blurry, low quality"

    # 2. Génération des pages de coloriage
    for page in pages:
        index = page.get("index")
        prompt = page.get("prompt")
        page_filename = f"page_{index:03d}.png"
        dest_path = pages_dir / page_filename

        if dest_path.exists():
            print(f"Page {index:03d} déjà existante. Passage.")
            report_pages.append({
                "page_number": index,
                "status": "skipped",
                "provider_used": "unknown"
            })
            continue

        tmp_path = pages_dir / f"tmp_page_{index:03d}.png"
        status = "failed"
        provider_used = "unknown"

        try:
            print(f"Génération de la page {index:03d}...")
            res = ir_generate(
                prompt=prompt,
                negative_prompt=default_neg_prompt,
                width=832,
                height=1152,
                dest=str(tmp_path)
            )

            # Extraction optionnelle du provider utilisé si retourné par le routeur
            if isinstance(res, dict):
                provider_used = res.get("provider", "unknown")
            elif isinstance(res, str) and res:
                provider_used = res

            if tmp_path.exists():
                print(f"Conversion en line-art pour la page {index:03d}...")
                coloring_convert(str(tmp_path), str(dest_path), line_thickness=line_thickness)
                if dest_path.exists():
                    status = "ok"
            else:
                print(f"Erreur : Le fichier temporaire {tmp_path} n'a pas été généré.")

        except Exception as e:
            print(f"Exception lors du traitement de la page {index:03d} : {e}", file=sys.stderr)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception as e:
                    print(f"Impossible de supprimer le fichier temporaire {tmp_path} : {e}", file=sys.stderr)

        report_pages.append({
            "page_number": index,
            "status": status,
            "provider_used": provider_used
        })

    # 3. Génération des couvertures (en couleur, pas de conversion line-art)
    cover_neg_prompt = "text, watermark, low quality, blurry, deformed, bad anatomy"
    for cover_type in ["front", "back"]:
        if cover_type in covers:
            cover_data = covers[cover_type]
            prompt = cover_data.get("prompt")
            dest_path = pages_dir / f"cover_{cover_type}.png"

            if dest_path.exists():
                print(f"Couverture {cover_type} déjà existante. Passage.")
                report_pages.append({
                    "page_number": f"cover_{cover_type}",
                    "status": "skipped",
                    "provider_used": "unknown"
                })
                continue

            status = "failed"
            provider_used = "unknown"

            try:
                print(f"Génération de la couverture {cover_type}...")
                res = ir_generate(
                    prompt=prompt,
                    negative_prompt=cover_neg_prompt,
                    width=2625,
                    height=3375,
                    dest=str(dest_path)
                )

                if isinstance(res, dict):
                    provider_used = res.get("provider", "unknown")
                elif isinstance(res, str) and res:
                    provider_used = res

                if dest_path.exists():
                    status = "ok"
            except Exception as e:
                print(f"Exception lors du traitement de la couverture {cover_type} : {e}", file=sys.stderr)

            report_pages.append({
                "page_number": f"cover_{cover_type}",
                "status": status,
                "provider_used": provider_used
            })

    # 4. Écriture du rapport de génération
    ok_count = sum(1 for p in report_pages if p["status"] in ("ok", "skipped"))
    failed_count = sum(1 for p in report_pages if p["status"] == "failed")

    report = {
        "pages": report_pages,
        "summary": {
            "ok": ok_count,
            "failed": failed_count
        }
    }

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Rapport de génération écrit avec succès dans {report_path}")
    except Exception as e:
        print(f"Erreur lors de l'écriture du rapport de génération : {e}", file=sys.stderr)

    print(f"Processus terminé. Succès/Skipped : {ok_count}, Échecs : {failed_count}")
    sys.exit(0)


if __name__ == "__main__":
    main()