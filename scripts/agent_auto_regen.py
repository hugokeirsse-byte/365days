"""
Agent AUTO REGEN — supprime les designs rejetés et marque pour re-trigger.

Pipeline :
1. Lit data/visual_audit.json (et data/gemini_quality_report.json si dispo)
2. Pour chaque design avec status=reject :
   - Supprime le dossier (libère le repo)
   - Note le pipeline et la niche dans regen_queue.json
3. Pour chaque pipeline avec >5 rejected, crée .triggers/<pipeline> pour re-générer
4. Mode dry-run par défaut

Variables d'env :
  DRY_RUN=1     simule sans supprimer (défaut)
  THRESHOLD=5   nb min de rejected dans un pipeline pour déclencher regen
  MAX_DELETE=50 limite la suppression par run
"""

import json
import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PRODUCTS_DIR = ROOT / "products"
TRIGGERS_DIR = ROOT / ".triggers"


def load_audits() -> list[dict]:
    """Charge les audits depuis visual_audit et gemini si dispo."""
    audits = []
    visual = DATA_DIR / "visual_audit.json"
    if visual.exists():
        data = json.loads(visual.read_text())
        audits.extend(data.get("audits", []))
    gemini = DATA_DIR / "gemini_quality_report.json"
    if gemini.exists():
        data = json.loads(gemini.read_text())
        audits.extend(data.get("audits", []))
    return audits


def is_design_path(p: Path) -> bool:
    """Vérifie qu'on supprime bien un dossier de design (pas un parent)."""
    return (p / "metadata.json").exists() and p.is_dir() \
        and PRODUCTS_DIR in p.parents


def main() -> int:
    dry_run = os.environ.get("DRY_RUN", "1") != "0"
    threshold = int(os.environ.get("THRESHOLD") or "5")
    max_delete = int(os.environ.get("MAX_DELETE") or "50")

    print("=" * 70)
    print(f"AUTO REGEN — {'DRY RUN' if dry_run else 'EXECUTING'}")
    print("=" * 70)

    audits = load_audits()
    if not audits:
        print("⊝ Aucun audit disponible. Lance visual_audit ou gemini_quality_check d'abord.")
        return 0

    # Filtre les rejected récents
    rejected = [a for a in audits if a.get("status") == "reject"
                                    or a.get("verdict") == "reject"]
    if not rejected:
        print("✓ Aucun design rejected. Rien à faire.")
        return 0

    print(f"\n{len(rejected)} designs rejected détectés.\n")

    # Group by pipeline
    by_pipeline = defaultdict(list)
    for r in rejected:
        pipeline = r.get("pipeline", "")
        if not pipeline:
            # Tente de l'extraire depuis design_path
            path = r.get("design_path", "")
            pipeline = path.split("/")[0] if path else "?"
        by_pipeline[pipeline].append(r)

    # Stats par pipeline
    print("Rejected par pipeline :")
    for p, items in sorted(by_pipeline.items(), key=lambda x: -len(x[1])):
        print(f"  {p:<30} {len(items)} rejected")

    # Suppression
    deleted = 0
    queue = defaultdict(list)
    for r in rejected[:max_delete]:
        path = r.get("design_path", "")
        if not path:
            continue
        full = PRODUCTS_DIR / path
        if not full.exists():
            continue
        if not is_design_path(full):
            print(f"  ⊝ skip {path} (pas un design folder)")
            continue
        pipeline = r.get("pipeline", path.split("/")[0])
        queue[pipeline].append({
            "path": path,
            "score": r.get("composite_score", r.get("rating_0_100", 0)),
        })
        if dry_run:
            print(f"  [DRY] delete {path}")
        else:
            try:
                shutil.rmtree(full)
                print(f"  ⛔ delete {path}")
                deleted += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  ✗ erreur sur {path} : {exc}")

    # Déclenche regen pour les pipelines qui dépassent le threshold
    triggered = []
    TRIGGERS_DIR.mkdir(parents=True, exist_ok=True)
    for pipeline, items in queue.items():
        if len(items) < threshold:
            continue
        # Map pipeline → trigger file name (heuristique)
        trigger_name_map = {
            "viral_formats": "viral_formats_v2",  # on recommande V2
            "iheart": "iheart_v3",
            "iheart_v2": "iheart_v3",
            "cultural_arbitrage": "cultural_arbitrage_v2",
            "literal_idioms": "literal_idioms_v2",
            "bible_verses": "bible_verses_v2",
        }
        trigger = trigger_name_map.get(pipeline, pipeline)
        trigger_path = TRIGGERS_DIR / trigger
        if dry_run:
            print(f"\n  [DRY] would trigger {trigger} ({len(items)} regens needed)")
        else:
            trigger_path.write_text(
                f"{datetime.utcnow().isoformat()}Z\n"
                f"auto_regen : {len(items)} rejected dans {pipeline}\n")
            print(f"\n  ▶ trigger {trigger} ({len(items)} regens needed)")
            triggered.append(trigger)

    # Log
    log = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dry_run": dry_run,
        "rejected_count": len(rejected),
        "deleted_count": deleted,
        "triggered_pipelines": triggered,
        "queue_by_pipeline": {p: len(items) for p, items in queue.items()},
    }
    (DATA_DIR / "auto_regen_log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False))

    print(f"\n→ {deleted} dossiers supprimés, {len(triggered)} regens déclenchés")
    if dry_run:
        print(f"  (DRY RUN — relance avec DRY_RUN=0 pour exécuter)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
