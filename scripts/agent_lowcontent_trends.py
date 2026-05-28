#!/usr/bin/env python3
"""
Cerveau perpétuel Low-Content KDP — tendances journals/planners/trackers.

Analyse ce qui se vend sur Amazon KDP dans le segment low-content :
journals, planners, habit trackers, gratitude journals, reading logs, etc.

Cron : mardi 05h UTC (après le rapporteur du dimanche)

Variables d'env : LC_ANGLE (override de l'angle hebdomadaire)
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions

ROOT = Path(__file__).resolve().parent.parent
BRAIN_DIR = ROOT / "data" / "brain" / "lowcontent"

ANGLES_LC = [
    "niches_ultra_specifiques",       # fisher log vs generic journal
    "tendances_saisonnières",          # planners back-to-school, new year
    "audiences_ignorées",              # hommes, ados, seniors, soignants
    "formats_innovants",               # half-year, weekly+daily combo
    "prix_premium_vs_budget",          # positionnement prix
    "mots_cles_inexploités",           # long-tail KDP keywords
    "séries_et_volumes",               # vol.1 vol.2 approach
]


def run():
    today = date.today().isoformat()
    week = date.today().isocalendar()[1]
    angle = os.environ.get("LC_ANGLE") or ANGLES_LC[week % len(ANGLES_LC)]

    previous = get_previous_propositions("products/lowcontent_kdp", "lowcontent_trends")
    print(f"[LC Brain] Angle: {angle} | Semaine: {week}")

    system_prompt = f"""Tu es un expert en low-content KDP (journals, planners, trackers, activity books).
Tu analyses le marché Amazon KDP pour identifier les niches rentables et sous-exploitées.

{previous}

ANGLE D'ANALYSE CETTE SEMAINE : {angle}

RÈGLES STRATÉGIQUES :
- LANGUE : Tous les produits en anglais par défaut. Ne recommande une autre langue que si tu
  identifies une opportunité spécifique prouvée dans ce marché (ex: forte demande locale non
  couverte, gap de concurrence dans cette langue).
- RÉHABILITATION : Cherche des produits KDP avec fort volume (BSR < 50 000) mais mauvaises
  notes (< 3.5 étoiles). Indique pourquoi ils échouent (qualité, format, contenu) et comment
  une meilleure version surpasserait la concurrence.

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "date": "{today}",
  "angle": "{angle}",
  "niches_tendance": [
    {{
      "niche": "...",
      "type_livre": "journal|planner|tracker|habit_tracker|activity_book",
      "bsp_estime": 50000,
      "prix_moyen_usd": 8.99,
      "concurrence": "faible|moyenne|forte",
      "saisonnalite": "annuel|saisonnier|event_driven",
      "notre_angle": "Comment se différencier"
    }}
  ],
  "mots_cles_opportunites": [
    {{
      "keyword": "...",
      "volume_recherche": "faible|moyen|élevé",
      "competition": "faible|moyenne|forte",
      "exemple_titre_optimise": "..."
    }}
  ],
  "formats_gagnants": [
    {{
      "format": "...",
      "pages_optimales": 120,
      "prix_optimal_usd": 8.99,
      "pourquoi": "..."
    }}
  ],
  "niches_a_eviter": ["...", "..."],
  "recommandation_cdc": {{
    "type": "journal|planner|tracker",
    "theme": "...",
    "audience": "...",
    "element_differentiant": "...",
    "priorite": "haute|normale"
  }}
}}
JSON uniquement."""

    user_prompt = f"""Analyse le marché low-content KDP aujourd'hui.
Focus : {angle}

Identifie les niches avec :
- Demande prouvée (BSP < 100 000)
- Concurrence encore faisable (pas 10 000 résultats identiques)
- Angle différenciant possible pour nous"""

    response = llm_call("stratege", system_prompt, user_prompt, temperature=0.75, max_tokens=3000)
    if not response:
        print("[LC Brain] Échec LLM.")
        return

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]

    try:
        data = json.loads(clean.strip())
    except Exception as e:
        print(f"[LC Brain] JSON invalide: {e}")
        return

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    out = BRAIN_DIR / f"lc_trends_{today}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (BRAIN_DIR / "lc_trends_latest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report_dir = ROOT / "data" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    rec = data.get("recommandation_cdc", {})
    niches = data.get("niches_tendance", [])
    md = [
        f"# Rapport Low-Content Brain — {today}",
        f"**Angle** : {angle}",
        "",
        "## Niches tendance",
    ]
    for n in niches[:5]:
        md.append(f"- **{n.get('niche')}** ({n.get('type_livre')}) — BSP ~{n.get('bsp_estime'):,} | {n.get('concurrence')} concurrence | {n.get('prix_moyen_usd')} USD")
        md.append(f"  → {n.get('notre_angle')}")
    md += [
        "",
        "## Recommandation CdC",
        f"**Type** : {rec.get('type')} | **Thème** : {rec.get('theme')}",
        f"**Audience** : {rec.get('audience')} | **Différenciant** : {rec.get('element_differentiant')}",
        f"**Priorité** : {rec.get('priorite')}",
    ]
    (report_dir / f"rapport_lc_{today}.md").write_text("\n".join(md), encoding="utf-8")

    print(f"[LC Brain] ✓ → {out}")
    print(f"[LC Brain] Recommandation : {rec.get('type')} / {rec.get('theme')}")


if __name__ == "__main__":
    run()
