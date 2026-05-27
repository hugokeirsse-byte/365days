"""
Agent ORCHESTRATOR — ferme la boucle automatique production.

Lit data/opportunities.json + data/ideas_brainstorm.json + état actuel
products/, identifie les pipelines à lancer cette semaine, et écrit
les .triggers/ correspondants pour les déclencher automatiquement.

Cron suggéré : jeudi 7h UTC.

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

OPPORTUNITY_TO_PIPELINE = [
    ("stl_3d", "stl_parametric"),
    ("coloring_books", "coloring_book"),
    ("ebook_fiction", None),
    ("ebook_non_fiction", None),
    ("tumbler_wraps", "tumbler"),
    ("t_shirt_pod", "iheart_v2"),
    ("mug_pod", "viral_formats"),
    ("wall_art_prints", "cultural_arbitrage"),
    ("stickers", "viral_formats"),
    ("tarot_oracle", None),
    ("notion_templates", None),
    ("audio_lofi", None),
    ("sleep_stories", None),
]

COOLDOWN_DAYS = 7
SCORE_THRESHOLD = 40


def load_json(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return default if default is not None else {}


def get_last_run_age_days(pipeline: str) -> float:
    pipeline_dirs = {
        "viral_formats": "viral_formats", "iheart_v2": "iheart_v2",
        "iheart": "iheart", "cultural_arbitrage": "cultural_arbitrage",
        "literal_idioms": "literal_idioms", "tumbler": "tumbler_wraps",
        "stl_parametric": "stl_parametric", "coloring_book": "coloring_books",
        "kdp_cover": "coloring_books",
    }
    pdir = PRODUCTS_DIR / pipeline_dirs.get(pipeline, pipeline)
    if not pdir.exists():
        return 999
    candidates = [f.stat().st_mtime for f in pdir.rglob("metadata.json")]
    if not candidates:
        return 999
    return (datetime.now().timestamp() - max(candidates)) / 86400


def get_orchestrator_log() -> dict:
    return load_json(DATA_DIR / "orchestrator_log.json", {"runs": [], "last_triggered": {}})


def save_orchestrator_log(log: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "orchestrator_log.json").write_text(json.dumps(log, indent=2, default=str))


def collect_candidates() -> list:
    opportunities = load_json(DATA_DIR / "opportunities.json", {})
    candidates = []
    for opp in opportunities.get("voie_a_explosion", {}).get("opportunities", [])[:5]:
        candidates.append({"type": "explosion", "score": opp.get("composite_score", 0),
                           "product_category": opp.get("product_category"),
                           "niche": opp.get("signal_niche", ""), "brief": opp.get("brief", ""), "urgency": "high"})
    for opp in opportunities.get("voie_b_niche_gap", {}).get("opportunities", [])[:5]:
        candidates.append({"type": "niche_gap", "score": opp.get("composite_score", 0),
                           "product_category": opp.get("product_category"),
                           "niche": opp.get("gap_niche", ""), "brief": opp.get("brief", ""), "urgency": "low"})
    if not candidates:
        ideas = load_json(DATA_DIR / "ideas_brainstorm.json", {})
        for idea in ideas.get("top_50_ideas", [])[:10]:
            candidates.append({"type": "brainstorm", "score": idea.get("score", 0),
                               "product_category": _idea_product_to_category(idea.get("product_type", "")),
                               "niche": idea.get("trend_keyword", ""), "brief": idea.get("idea", ""), "urgency": "medium"})
    return candidates


def _idea_product_to_category(product_label: str) -> str:
    mapping = {"T-shirt POD": "t_shirt_pod", "Mug POD": "mug_pod", "Wall art print": "wall_art_prints",
               "Sticker": "stickers", "Tumbler wrap": "tumbler_wraps", "Coloring book": "coloring_books",
               "STL bookmark": "stl_3d", "STL keychain": "stl_3d", "STL coaster": "stl_3d",
               "Tote bag POD": "t_shirt_pod", "Phone case POD": "t_shirt_pod"}
    return mapping.get(product_label, "")


def select_pipelines_to_trigger(candidates: list, dry_run: bool = False) -> list:
    pipeline_for_category = {cat: pipe for cat, pipe in OPPORTUNITY_TO_PIPELINE if pipe is not None}
    decisions = []
    pipelines_planned = set()
    for cand in sorted(candidates, key=lambda x: -x["score"]):
        if cand["score"] < SCORE_THRESHOLD:
            continue
        category = cand.get("product_category", "")
        pipeline = pipeline_for_category.get(category)
        if not pipeline:
            decisions.append({**cand, "decision": "skip", "reason": f"no pipeline for {category}"})
            continue
        if pipeline in pipelines_planned:
            decisions.append({**cand, "decision": "skip", "reason": "pipeline already planned"})
            continue
        age = get_last_run_age_days(pipeline)
        if age < COOLDOWN_DAYS:
            decisions.append({**cand, "decision": "skip", "reason": f"cooldown {age:.1f}d < {COOLDOWN_DAYS}d"})
            continue
        decisions.append({**cand, "decision": "trigger", "pipeline": pipeline, "last_run_age_days": round(age, 1)})
        pipelines_planned.add(pipeline)
        if len(pipelines_planned) >= 1:
            break
    return decisions


def dispatch_brief_pipeline(dry_run: bool) -> list:
    """Déclenche production_loop pour chaque brief approuvé non encore produit."""
    triggered = []
    briefs_dir = ROOT / "data" / "briefs"
    gate1_dir = ROOT / "products" / "coloring_books" / "_gate1"
    for brief_path in sorted(briefs_dir.glob("brief_*.json")):
        try:
            brief = json.loads(brief_path.read_text())
        except Exception:
            continue
        if brief.get("human_gates", {}).get("gate_start") != "approved":
            continue
        bid = brief.get("id", brief_path.stem)
        prod_dir = gate1_dir / bid
        if (prod_dir / "kdp_package.json").exists() or (prod_dir / "interior.pdf").exists():
            print(f"  ○ brief {bid} déjà produit — skip")
            continue
        content = f"brief_id={bid}\n"
        if dry_run:
            print(f"  [DRY] production_loop <- {bid}")
        else:
            TRIGGERS_DIR.mkdir(parents=True, exist_ok=True)
            (TRIGGERS_DIR / "production_loop").write_text(content)
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
    if dry_run:
        print(f"  [DRY] builder trigger")
    else:
        TRIGGERS_DIR.mkdir(parents=True, exist_ok=True)
        (TRIGGERS_DIR / "builder").write_text(f"run_all=true\n{datetime.utcnow().isoformat()}Z\n")
        print(f"  ✓ Builder déclenché ({len(pending)} briefings)")
    return True


def write_triggers(decisions: list, dry_run: bool) -> int:
    TRIGGERS_DIR.mkdir(parents=True, exist_ok=True)
    triggered = 0
    for d in decisions:
        if d["decision"] != "trigger":
            continue
        trigger_path = TRIGGERS_DIR / d["pipeline"]
        if dry_run:
            print(f"  [DRY] trigger {trigger_path}")
        else:
            trigger_path.write_text(f"{datetime.utcnow().isoformat()}Z\norchestrator: {d['niche']}\n")
            print(f"  ✓ trigger {trigger_path.name}")
        triggered += 1
    return triggered


def main() -> int:
    dry_run = os.environ.get("DRY_RUN") == "1"
    print("=" * 70)
    print("ORCHESTRATOR — décide quoi produire cette semaine")
    print("=" * 70)
    if dry_run:
        print("  (DRY RUN)")

    candidates = collect_candidates()
    if not candidates:
        print("\n✗ Aucune opportunité — lance agent_trend_explosion + opportunity_hunter d'abord.")
        # Continue quand même pour les briefs et le Builder
    else:
        print(f"\n{len(candidates)} candidates :")
        decisions = select_pipelines_to_trigger(candidates, dry_run)
        triggered_count, skipped_count = 0, 0
        for d in decisions:
            icon = "▶" if d["decision"] == "trigger" else "○"
            print(f"  {icon} [{d['type']:>10}] score {d['score']:>5.1f}  {d.get('niche', '?'):<25} → {d['decision']}")
            if d["decision"] == "trigger":
                triggered_count += 1
            else:
                skipped_count += 1
        write_triggers(decisions, dry_run)
        print(f"\n→ {triggered_count} pipeline(s) déclenché(s), {skipped_count} skipped")

    print("\n--- Briefs approuvés ---")
    dispatch_brief_pipeline(dry_run)
    print("\n--- Builder queue ---")
    dispatch_builder_queue(dry_run)

    log = get_orchestrator_log()
    log["runs"].append({"timestamp": datetime.utcnow().isoformat() + "Z",
                        "candidates": len(candidates) if candidates else 0, "dry_run": dry_run})
    log["runs"] = log["runs"][-50:]
    if not dry_run:
        save_orchestrator_log(log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
