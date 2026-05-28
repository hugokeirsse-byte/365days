#!/usr/bin/env python3
"""
Rapporteur Hebdomadaire — Weekly digest agent.

Reads all reports, audits, build queues and triggers from the past 7 days,
then calls Gemini to produce a structured French weekly digest for Hugo.

Outputs:
  data/reports/rapport_hebdo_YYYY-MM-DD.md   (dated copy)
  data/reports/rapport_hebdo_latest.md       (always overwritten)

Runs every Sunday at 20h UTC via .github/workflows/rapporteur_hebdo.yml
"""
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Allow both direct execution and import from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.lib.brain_utils import llm_call

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "data" / "reports"
STRATEGIE_DIR = ROOT / "data" / "strategie"
BRAIN_DIR = ROOT / "data" / "brain"
BUILD_QUEUE_DIR = ROOT / "data" / "build_queue"
PRODUCTS_DIR = ROOT / "products"
TRIGGERS_DIR = ROOT / ".triggers"

VERTICAL_DIRS = {
    "coloring":     ROOT / "products" / "coloring_books",
    "lowcontent":   ROOT / "products" / "lowcontent_kdp",
    "roman":        ROOT / "products" / "novels",
    "stl":          ROOT / "products" / "stl_3d",
    "jeux_societe": ROOT / "products" / "jeux_societe",
    "merch_design": ROOT / "products" / "merch",
    "godot_assets": ROOT / "products" / "godot_assets",
}

# --------------------------------------------------------------------------- #
# Collectors
# --------------------------------------------------------------------------- #

def _read_recent_files(directory: Path, days: int = 7, exts=(".json", ".md"),
                        max_chars: int = 2000, max_files: int = 20) -> str:
    """Returns a concatenated string of recent files from directory."""
    if not directory.exists():
        return ""
    cutoff = datetime.utcnow() - timedelta(days=days)
    files = sorted(
        [
            f for f in directory.rglob("*")
            if f.suffix in exts and f.stat().st_mtime >= cutoff.timestamp()
        ],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:max_files]
    parts = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8")[:max_chars]
            parts.append(f"### [{f.name}]\n{content}\n")
        except Exception:
            pass
    return "\n".join(parts)


def collect_recent_reports() -> str:
    """Reads all report files from data/reports/, data/strategie/, data/brain/ (last 7 days)."""
    sections = []
    for label, path in [
        ("REPORTS", REPORTS_DIR),
        ("STRATÉGIE", STRATEGIE_DIR),
        ("BRAIN", BRAIN_DIR),
    ]:
        content = _read_recent_files(path, days=7)
        if content:
            sections.append(f"## Fichiers {label} (7 derniers jours)\n{content}")
    return "\n\n".join(sections) if sections else "Aucun rapport récent trouvé."


def collect_cdc_queue_status() -> str:
    """Reads all cdc.json files and summarizes the CdC pipeline state per vertical."""
    lines = ["## État de la file CdC par vertical"]
    totals = {"pending": 0, "approved_unprod": 0, "produced": 0, "rejected": 0}

    for vertical, vdir in VERTICAL_DIRS.items():
        if not vdir.exists():
            lines.append(f"  - {vertical}: aucun dossier products/")
            continue
        counts = {"pending": 0, "approved_unprod": 0, "produced": 0, "rejected": 0}
        for cdc_path in vdir.rglob("cdc.json"):
            try:
                cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
                gate = cdc.get("gate_cdc", "pending")
                has_prod = bool(cdc.get("production_status"))
                if gate == "pending":
                    counts["pending"] += 1
                elif gate == "approved" and not has_prod:
                    counts["approved_unprod"] += 1
                elif gate == "approved" and has_prod:
                    counts["produced"] += 1
                elif gate == "rejected":
                    counts["rejected"] += 1
            except Exception:
                pass
        for k in totals:
            totals[k] += counts[k]
        lines.append(
            f"  - {vertical}: {counts['pending']} pending | "
            f"{counts['approved_unprod']} approuvés (à produire) | "
            f"{counts['produced']} produits | "
            f"{counts['rejected']} rejetés"
        )

    lines.append(
        f"\nTOTAL : {totals['pending']} pending | {totals['approved_unprod']} à produire | "
        f"{totals['produced']} produits | {totals['rejected']} rejetés"
    )
    return "\n".join(lines)


def collect_audit_summary() -> str:
    """Reads AUDIT.txt files in products/ and counts APPROVE/REVIEW/REJECT by type."""
    totals = {"APPROVE": 0, "REVIEW": 0, "REJECT": 0}
    by_type: dict[str, dict] = {}

    if not PRODUCTS_DIR.exists():
        return "Aucun produit trouvé."

    for audit_file in PRODUCTS_DIR.rglob("AUDIT.txt"):
        product_type = audit_file.parent.parent.name  # products/<type>/<item>/AUDIT.txt
        if product_type not in by_type:
            by_type[product_type] = {"APPROVE": 0, "REVIEW": 0, "REJECT": 0}
        try:
            content = audit_file.read_text(encoding="utf-8").upper()
            for verdict in ("APPROVE", "REVIEW", "REJECT"):
                if verdict in content:
                    by_type[product_type][verdict] += 1
                    totals[verdict] += 1
        except Exception:
            pass

    lines = ["## Résultats d'audit produits (tous temps)"]
    lines.append(f"TOTAL : APPROVE={totals['APPROVE']}  REVIEW={totals['REVIEW']}  REJECT={totals['REJECT']}")
    lines.append("")
    for ptype, counts in sorted(by_type.items()):
        lines.append(
            f"  - {ptype}: APPROVE={counts['APPROVE']} | REVIEW={counts['REVIEW']} | REJECT={counts['REJECT']}"
        )
    return "\n".join(lines)


def collect_build_queue() -> str:
    """Lists pending briefings in data/build_queue/."""
    if not BUILD_QUEUE_DIR.exists():
        return "Aucune file de production trouvée."
    items = []
    for f in sorted(BUILD_QUEUE_DIR.iterdir()):
        if f.is_file():
            try:
                preview = f.read_text(encoding="utf-8")[:300].replace("\n", " ")
                items.append(f"  - {f.name}: {preview[:200]}…")
            except Exception:
                items.append(f"  - {f.name}")
    if not items:
        return "File de production vide (aucun briefing en attente)."
    return "## Build queue (briefings en attente)\n" + "\n".join(items)


def collect_triggers_this_week() -> str:
    """Checks .triggers/ to see what was triggered recently."""
    if not TRIGGERS_DIR.exists():
        return "Aucun dossier .triggers/ trouvé."
    cutoff = datetime.utcnow() - timedelta(days=7)
    triggered = []
    for f in TRIGGERS_DIR.iterdir():
        if f.is_file() and f.stat().st_mtime >= cutoff.timestamp():
            triggered.append(f"  - {f.name} (modifié {datetime.utcfromtimestamp(f.stat().st_mtime).date()})")
    if not triggered:
        return "## Triggers déclenchés cette semaine\nAucun trigger actif cette semaine."
    return "## Triggers déclenchés cette semaine\n" + "\n".join(triggered)


# --------------------------------------------------------------------------- #
# LLM call
# --------------------------------------------------------------------------- #

def generate_digest(context: str, today: str, week_number: int) -> str:
    system = """Tu es le Rapporteur Hebdomadaire de l'Usine 365days — une fabrique de produits numériques automatisée.
Tu génères un digest hebdomadaire structuré en Français pour Hugo, le fondateur, qui lit ce rapport le dimanche soir.
Le rapport doit être clair, dense en information utile, sans fluff, et immédiatement actionnable.
Format de sortie OBLIGATOIRE en Markdown :

# 📊 Rapport Hebdomadaire — Semaine [N] ([DATE])

## Résumé Exécutif
[3-4 phrases. Ce qui s'est passé cette semaine : productions lancées, résultats d'audit, signaux importants.]

## Pipeline Produits
[Tableau ou liste avec statuts APPROVE / REVIEW / REJECT par type de produit. Ce qui est prêt à publier, ce qui attend validation.]

## Highlights Agents Brain
[Ce que le Prospecteur d'Émergence a trouvé de meilleur. Ce que le B1 Stratège a proposé. 3-5 bullet points maximum.]

## Actions pour Hugo
[Liste numérotée, claire et actionnable. Max 7 items. Chaque item doit avoir une action concrète, pas un vague conseil.]

## La semaine prochaine
[Quels agents vont tourner automatiquement. Quels événements saisonniers approchent. Ce à quoi s'attendre.]

Sois direct, honnête sur ce qui manque ou dysfonctionne, et précis sur les opportunités."""

    user = f"""Date du rapport : {today} (semaine {week_number})

=== CONTEXTE COMPLET DE L'USINE CETTE SEMAINE ===

{context}

Génère le rapport hebdomadaire complet selon le format spécifié."""

    return llm_call("conseil", system, user, temperature=0.6, max_tokens=4000)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> int:
    today = date.today().isoformat()
    week_number = date.today().isocalendar()[1]

    print(f"[Rapporteur Hebdo] Semaine {week_number} — {today}")

    # 1. Collect all context
    print("[Rapporteur] Collecte des rapports récents...")
    recent_reports = collect_recent_reports()

    print("[Rapporteur] Collecte des audits produits...")
    audit_summary = collect_audit_summary()

    print("[Rapporteur] Collecte de l'état des files CdC...")
    cdc_status = collect_cdc_queue_status()

    print("[Rapporteur] Collecte de la file de production...")
    build_queue = collect_build_queue()

    print("[Rapporteur] Collecte des triggers...")
    triggers = collect_triggers_this_week()

    full_context = "\n\n".join([
        recent_reports,
        audit_summary,
        cdc_status,
        build_queue,
        triggers,
    ])

    # 2. Generate digest via Gemini
    print("[Rapporteur] Appel LLM pour générer le digest...")
    digest = generate_digest(full_context, today, week_number)

    if not digest:
        print("[Rapporteur] ERREUR : LLM n'a retourné aucun contenu.")
        return 1

    # 3. Write outputs
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    dated_path = REPORTS_DIR / f"rapport_hebdo_{today}.md"
    latest_path = REPORTS_DIR / "rapport_hebdo_latest.md"

    dated_path.write_text(digest, encoding="utf-8")
    latest_path.write_text(digest, encoding="utf-8")

    print(f"[Rapporteur] Rapport écrit : {dated_path}")
    print(f"[Rapporteur] Rapport latest mis à jour : {latest_path}")
    print(f"[Rapporteur] {len(digest)} caractères générés.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
