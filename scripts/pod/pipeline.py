#!/usr/bin/env python3
"""
POD Pipeline — Orchestrateur du cycle complet Spoonflower/Society6/Redbubble.

Enchaîne les 4 agents dans l'ordre logique :
  1. agent_radar        → data/pod/trend.json
  2. agent_art_director → data/pod/cahier_des_charges.json
  3. (manuel/IA)        → génération des images (Runware ou HF)
  4. agent_public_domain → data/pod/public_domain_candidates.json
  5. agent_quality_inspector → validation + upscale

Usage :
    python scripts/pod/pipeline.py               # cycle complet
    python scripts/pod/pipeline.py radar         # étape 1 seulement
    python scripts/pod/pipeline.py art           # étape 2 seulement
    python scripts/pod/pipeline.py pd            # étape public domain
    python scripts/pod/pipeline.py qa [path]     # étape QA

Variables d'env utilisées :
    HF_API_KEY        — HuggingFace (upscale Real-ESRGAN)
    GEMINI_API_KEY    — enrichissement LLM des briefs
    DPLA_API_KEY      — DPLA (optionnel, une clé démo est incluse)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


def step_radar():
    print("\n" + "=" * 60)
    print("ÉTAPE 1 — Radar de tendances")
    print("=" * 60)
    from scripts.pod.agent_radar import run
    return run()


def step_art_director():
    print("\n" + "=" * 60)
    print("ÉTAPE 2 — Direction artistique")
    print("=" * 60)
    from scripts.pod.agent_art_director import run
    return run()


def step_public_domain():
    print("\n" + "=" * 60)
    print("ÉTAPE 3B — Archives domaine public")
    print("=" * 60)
    from scripts.pod.agent_public_domain import run
    return run()


def step_quality(target: str | None = None):
    print("\n" + "=" * 60)
    print("ÉTAPE 4 — Contrôle qualité + upscale")
    print("=" * 60)
    from scripts.pod.agent_quality_inspector import run
    return run(target)


def print_summary(results: dict):
    print("\n" + "=" * 60)
    print("RÉSUMÉ DU CYCLE POD")
    print("=" * 60)

    trend_file = ROOT / "data" / "pod" / "trend.json"
    cdc_file   = ROOT / "data" / "pod" / "cahier_des_charges.json"
    pd_file    = ROOT / "data" / "pod" / "public_domain_candidates.json"
    qa_file    = ROOT / "data" / "pod" / "quality_report.json"

    import json
    if trend_file.exists():
        t = json.loads(trend_file.read_text())
        print(f"  ✓ Top niches : {', '.join(t.get('recommended_niches', [])[:5])}")
        if t.get("upcoming_events"):
            ev = t["upcoming_events"][0]
            print(f"  ✓ Prochain événement : {ev['event']} dans {ev['days_away']}j")

    if cdc_file.exists():
        c = json.loads(cdc_file.read_text())
        print(f"  ✓ {len(c.get('briefs', []))} briefs générés")
        for b in c.get("briefs", []):
            print(f"     — [{b['category']}] {b['keyword']} | tags: {', '.join(b['seo_tags'][:4])}")

    if pd_file.exists():
        p = json.loads(pd_file.read_text())
        print(f"  ✓ {p.get('total_found', 0)} images domaine public trouvées")
        print(f"     {len(p.get('downloaded', []))} téléchargées pour traitement")

    if qa_file.exists():
        q = json.loads(qa_file.read_text())
        print(f"  ✓ QA : {q.get('pass_count', 0)} OK / {q.get('fail_count', 0)} corrigés")

    print("\n  PROCHAINES ÉTAPES (manuelles) :")
    print("  1. Générer les images avec Runware/ComfyUI selon les prompts dans cahier_des_charges.json")
    print("  2. Lancer : python scripts/pod/pipeline.py qa products/pod/generated/")
    print("  3. Uploader manuellement sur Spoonflower / Society6 / Redbubble")
    print("     (les SEO tags et titres sont dans cahier_des_charges.json)")
    print("=" * 60)


def run_full():
    results = {}
    results["radar"] = step_radar()
    time.sleep(1)
    results["art"]   = step_art_director()
    time.sleep(1)
    results["pd"]    = step_public_domain()
    print_summary(results)
    return results


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "full"

    if cmd == "radar":
        step_radar()
    elif cmd == "art":
        step_art_director()
    elif cmd == "pd":
        step_public_domain()
    elif cmd == "qa":
        target = sys.argv[2] if len(sys.argv) > 2 else None
        step_quality(target)
    else:
        run_full()
