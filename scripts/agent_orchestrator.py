"""
Agent ORCHESTRATOR — ferme la boucle automatique production.

Lit data/opportunities.json + data/ideas_brainstorm.json + état actuel
products/, identifie les pipelines à lancer cette semaine, et écrit
les .triggers/ correspondants pour les déclencher automatiquement.

Logique de décision :
1. Lit les TOP opportunités (voie A urgent + voie B stable)
2. Mappe chaque opportunité au pipeline qui peut la produire
3. Vérifie ce qui est DÉJÀ en stock (via inventory_dashboard logic)
4. Lance UNIQUEMENT les pipelines qui :
   - couvrent une opportunité non encore traitée
   - n'ont pas tourné depuis 7 jours
   - ont une opportunité avec score > seuil
5. Écrit data/orchestrator_log.json pour traçabilité

Cron suggéré : jeudi 7h UTC (juste après opportunity_hunter lundi
et ideator mercredi).

Variables d'env :
  DRY_RUN=1     simule sans toucher aux triggers (debug)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TRIGGERS_DIR = ROOT / ".triggers"
PRODUCTS_DIR = ROOT / "products"

# Mapping opportunité → pipeline trigger
# Priorité : si plusieurs pipelines matchent, on prend le 1er
OPPORTUNITY_TO_PIPELINE = [
    ("stl_3d", "stl_parametric"),
    ("coloring_books", "coloring_book"),
    ("ebook_fiction", None),  # nécessite Gemini, on skip
    ("ebook_non_fiction", None),  # nécessite Gemini
    ("tumbler_wraps", "tumbler"),
    ("t_shirt_pod", "iheart_v2"),  # iheart_v2 est plus original que iheart
    ("mug_pod", "viral_formats"),
    ("wall_art_prints", "cultural_arbitrage"),
    ("stickers", "viral_formats"),
    ("tarot_oracle", None),
    ("notion_templates", None),
    ("audio_lofi", None),
    ("sleep_stories", None),
]

# Cooldown : combien de jours minimum entre 2 runs d'un même pipeline
COOLDOWN_DAYS = 7

# Seuil de score d'opportunité pour déclencher
SCORE_THRESHOLD = 40


def load_json(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return default if default is not None else {}


def get_last_run_age_days(pipeline: str) -> float:
    """Retourne l'âge du dernier run en jours, ou 999 si jamais lancé."""
    # Heuristique : dossier produit le plus récent dans products/<pipeline>/
    candidates = []
    pipeline_dirs = {
        "viral_formats": "viral_formats",
        "iheart_v2": "iheart_v2",
        "iheart": "iheart",
        "cultural_arbitrage": "cultural_arbitrage",
        "literal_idioms": "literal_idioms",
        "tumbler": "tumbler_wraps",
        "stl_parametric": "stl_parametric",
        "coloring_book": "coloring_books",
        "kdp_cover": "coloring_books",
    }
    pdir = PRODUCTS_DIR / pipeline_dirs.get(pipeline, pipeline)
    if not pdir.exists():
        return 999
    for f in pdir.rglob("metadata.json"):
        candidates.append(f.stat().st_mtime)
    if not candidates:
        return 999
    most_recent = max(candidates)
    age_sec = datetime.now().timestamp() - most_recent
    return age_sec / 86400


def get_orchestrator_log() -> dict:
    return load_json(DATA_DIR / "orchestrator_log.json", {
        "runs": [],
        "last_triggered": {},
    })


def save_orchestrator_log(log: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "orchestrator_log.json").write_text(
        json.dumps(log, indent=2, default=str))


def collect_candidates() -> list[dict]:
    """Collecte les opportunités candidates depuis opportunity_hunter."""
    opportunities = load_json(DATA_DIR / "opportunities.json", {})
    candidates = []

    # Voie A (urgent explosion) — priorité haute
    voie_a = opportunities.get("voie_a_explosion", {}).get("opportunities", [])
    for opp in voie_a[:5]:  # top 5 urgentes
        candidates.append({
            "type": "explosion",
            "score": opp.get("composite_score", 0),
            "product_category": opp.get("product_category"),
            "niche": opp.get("signal_niche", ""),
            "brief": opp.get("brief", ""),
            "urgency": "high",
        })

    # Voie B (stable niche gap) — top 5
    voie_b = opportunities.get("voie_b_niche_gap", {}).get("opportunities", [])
    for opp in voie_b[:5]:
        candidates.append({
            "type": "niche_gap",
            "score": opp.get("composite_score", 0),
            "product_category": opp.get("product_category"),
            "niche": opp.get("gap_niche", ""),
            "brief": opp.get("brief", ""),
            "urgency": "low",
        })

    # Si pas d'opportunities, fallback sur ideas_brainstorm top 10
    if not candidates:
        ideas = load_json(DATA_DIR / "ideas_brainstorm.json", {})
        for idea in ideas.get("top_50_ideas", [])[:10]:
            candidates.append({
                "type": "brainstorm",
                "score": idea.get("score", 0),
                "product_category": _idea_product_to_category(
                    idea.get("product_type", "")),
                "niche": idea.get("trend_keyword", ""),
                "brief": idea.get("idea", ""),
                "urgency": "medium",
            })

    return candidates


def _idea_product_to_category(product_label: str) -> str:
    mapping = {
        "T-shirt POD": "t_shirt_pod",
        "Mug POD": "mug_pod",
        "Wall art print": "wall_art_prints",
        "Sticker": "stickers",
        "Tumbler wrap": "tumbler_wraps",
        "Coloring book": "coloring_books",
        "STL bookmark": "stl_3d",
        "STL keychain": "stl_3d",
        "STL coaster": "stl_3d",
        "Tote bag POD": "t_shirt_pod",
        "Phone case POD": "t_shirt_pod",
    }
    return mapping.get(product_label, "")


def select_pipelines_to_trigger(candidates: list[dict],
                                  dry_run: bool = False) -> list[dict]:
    """Sélectionne les pipelines à déclencher."""
    pipeline_for_category = {cat: pipe for cat, pipe in OPPORTUNITY_TO_PIPELINE
                              if pipe is not None}

    decisions = []
    pipelines_planned = set()

    for cand in sorted(candidates, key=lambda x: -x["score"]):
        if cand["score"] < SCORE_THRESHOLD:
            continue
        category = cand.get("product_category", "")
        pipeline = pipeline_for_category.get(category)
        if not pipeline:
            decisions.append({
                **cand,
                "decision": "skip",
                "reason": f"no pipeline for category {category}",
            })
            continue
        if pipeline in pipelines_planned:
            decisions.append({
                **cand,
                "decision": "skip",
                "reason": "pipeline already planned this run",
            })
            continue
        age = get_last_run_age_days(pipeline)
        if age < COOLDOWN_DAYS:
            decisions.append({
                **cand,
                "decision": "skip",
                "reason": f"cooldown : last run {age:.1f}d ago < {COOLDOWN_DAYS}d",
            })
            continue
        decisions.append({
            **cand,
            "decision": "trigger",
            "pipeline": pipeline,
            "last_run_age_days": round(age, 1),
        })
        pipelines_planned.add(pipeline)
        # IMPORTANT : limite à 1 nouveau pipeline triggered par run.
        # Source LECONS_DU_WEB.md : éviter le "content farm flag" d'Etsy.
        # Uploader plus de 5 listings/jour avec structure similaire = ban auto.
        # Le cadencement lent est crucial pour rester sous le radar.
        if len(pipelines_planned) >= 1:
            break

    return decisions


def dispatch_brief_pipeline(dry_run: bool) -> list[str]:
    """Déclenche production_loop pour chaque brief approuvé non encore produit."""
    triggered = []
    briefs_dir = ROOT / "data" / "briefs"
    gate1_dir = ROOT / "products" / "coloring_books" / "_gate1"
    for brief_path in sorted(briefs_dir.glob("brief_*.json")):
        try:
            brief = json.loads(brief_path.read_text())
        except Exception:
            continue
        gates = brief.get("human_gates", {})
        if gates.get("gate_start") != "approved":
            continue
        bid = brief.get("id", brief_path.stem)
        # Déjà produit si kdp_package.json ou interior.pdf présents
        prod_dir = gate1_dir / bid
        if (prod_dir / "kdp_package.json").exists() or (prod_dir / "interior.pdf").exists():
            print(f"  ○ brief {bid} déjà produit — skip")
            continue
        trigger_path = TRIGGERS_DIR / "production_loop"
        content = f"brief_id={bid}\n"
        if dry_run:
            print(f"  [DRY] production_loop <- {bid}")
        else:
            TRIGGERS_DIR.mkdir(parents=True, exist_ok=True)
            trigger_path.write_text(content)
            print(f"  ✓ production_loop déclenché pour {bid}")
        triggered.append(bid)
    return triggered


def dispatch_builder_queue(dry_run: bool) -> bool:
    """Déclenche le Builder si des briefings sont en attente."""
    queue = ROOT / "data" / "build_queue"
    pending = list(queue.glob("*.md")) if queue.exists() else []
    if not pending:
        return False
    print(f"  Builder : {len(pending)} briefing(s) en attente")
    trigger_path = TRIGGERS_DIR / "builder"
    if dry_run:
        print(f"  [DRY] builder trigger")
    else:
        TRIGGERS_DIR.mkdir(parents=True, exist_ok=True)
        trigger_path.write_text(f"run_all=true\n{datetime.utcnow().isoformat()}Z\n")
        print(f"  ✓ Builder déclenché ({len(pending)} briefings)")
    return True


def write_triggers(decisions: list[dict], dry_run: bool) -> int:
    TRIGGERS_DIR.mkdir(parents=True, exist_ok=True)
    triggered = 0
    for d in decisions:
        if d["decision"] != "trigger":
            continue
        trigger_path = TRIGGERS_DIR / d["pipeline"]
        if dry_run:
            print(f"  [DRY] trigger {trigger_path}")
        else:
            trigger_path.write_text(
                f"{datetime.utcnow().isoformat()}Z\n"
                f"orchestrator decision: {d['niche']} ({d['type']})\n"
            )
            print(f"  ✓ trigger {trigger_path.name}")
        triggered += 1
    return triggered


def main() -> int:
    dry_run = os.environ.get("DRY_RUN") == "1"
    print("=" * 70)
    print("ORCHESTRATOR — décide quoi produire cette semaine")
    print("=" * 70)
    if dry_run:
        print("  (DRY RUN — pas de trigger réel)")

    candidates = collect_candidates()
    if not candidates:
        print("\n✗ Aucune opportunité disponible. Lance d'abord les agents :")
        print("   - agent_trend_explosion")
        print("   - agent_niche_gap")
        print("   - agent_opportunity_hunter")
        print("   ou attends que les crons aient tourné")
        return 1

    print(f"\n{len(candidates)} candidates analysés :")
    decisions = select_pipelines_to_trigger(candidates, dry_run)

    triggered_count = 0
    skipped_count = 0
    for d in decisions:
        icon = "▶" if d["decision"] == "trigger" else "○"
        print(f"  {icon} [{d['type']:>10}] score {d['score']:>5.1f}  "
              f"{d.get('niche', '?'):<25} → {d['decision']}")
        if d["decision"] == "trigger":
            triggered_count += 1
            print(f"      pipeline : {d['pipeline']} "
                  f"(last run {d.get('last_run_age_days', '?')}d ago)")
        else:
            skipped_count += 1
            print(f"      reason : {d.get('reason', '')}")

    written = write_triggers(decisions, dry_run)
    print(f"\n→ {written} pipeline(s) déclenché(s), {skipped_count} skipped")

    # Dispatching brief-based production (nouvelle boucle autonome)
    print("\n--- Briefs approuvés ---")
    brief_triggered = dispatch_brief_pipeline(dry_run)
    print("\n--- Builder queue ---")
    dispatch_builder_queue(dry_run)

    # Log
    log = get_orchestrator_log()
    log["runs"].append({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "candidates_analyzed": len(candidates),
        "triggered_pipelines": [d["pipeline"] for d in decisions
                                if d["decision"] == "trigger"],
        "skipped_count": skipped_count,
        "dry_run": dry_run,
    })
    # Garder uniquement les 50 derniers runs
    log["runs"] = log["runs"][-50:]
    for d in decisions:
        if d["decision"] == "trigger":
            log["last_triggered"][d["pipeline"]] = \
                datetime.utcnow().isoformat() + "Z"
    if not dry_run:
        save_orchestrator_log(log)

    return 0


if __name__ == "__main__":
    sys.exit(main())
