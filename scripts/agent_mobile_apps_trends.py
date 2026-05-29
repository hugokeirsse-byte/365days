#!/usr/bin/env python3
"""
Brain agent hebdomadaire — tendances applications mobiles.

Analyse les tendances sur App Store, Google Play, ProductHunt pour identifier
les catégories et niches d'applications mobiles les plus porteuses.

Plateformes : App Store (iOS), Google Play (Android), ProductHunt (launches)

Cron : vendredi 05h UTC
Variables d'env : MOBILE_APPS_ANGLE (override)
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "data" / "reports"

ANGLES_MOBILE_APPS = [
    "appstore_top_charts_productivity",     # apps productivité en tête des charts
    "google_play_health_wellness_rising",   # santé/bien-être en montée
    "producthunt_launches_week",            # lancements ProductHunt de la semaine
    "subscription_apps_analysis",          # apps à abonnement qui fonctionnent
    "no_ads_privacy_opportunity",          # apps sans pub ni cloud = niche croissante
    "finance_tools_underserved",           # outils finance sous-exploités
    "low_rating_high_download_targets",    # cibles de réhabilitation
]


def run():
    today = date.today().isoformat()
    week = date.today().isocalendar()[1]
    angle = os.environ.get("MOBILE_APPS_ANGLE") or ANGLES_MOBILE_APPS[week % len(ANGLES_MOBILE_APPS)]

    previous = get_previous_propositions("products/mobile_apps", "mobile_apps_trends")
    print(f"[Mobile Apps Brain] Angle: {angle} | Week: {week}")

    system_prompt = f"""You are an expert in mobile app development and market analysis on App Store, Google Play, and ProductHunt.
You analyze mobile app market trends to identify opportunities for solo indie developers.

{previous}

ANALYSIS ANGLE: {angle}

STRATEGIC RULES:
- LANGUAGE: English by default. Exception only if a specific market opportunity is proven (e.g., a non-English market with no local competition and proven demand).
- REHABILITATION: Identify apps with high download volume but poor ratings (<3.5 stars). Typical causes: poor onboarding, too many ads, privacy concerns, missing offline mode, bad UX. A fixed version can outrank weak competition.

RESPONSE FORMAT — STRICT JSON:
{{
  "date": "{today}",
  "angle": "{angle}",
  "categories_tendance": [
    {{
      "categorie": "productivity|health|finance|lifestyle|education|tools|creativity",
      "sous_niche": "...",
      "croissance": "explosif|fort|stable|déclinant",
      "saturation": "faible|moyenne|forte",
      "framework_recommande": "Flutter|React Native|PWA|Swift/Kotlin",
      "monetisation_optimale": "freemium|subscription|one_time|free_ads",
      "arpu_estime_usd": 2.50,
      "effort_mvp_jours": 21,
      "pourquoi_ca_marche": "...",
      "app_faible_notes_exemple": "..."
    }}
  ],
  "apps_a_rehabiliter": [{{"nom": "...", "probleme": "...", "opportunite": "..."}}],
  "recommandation_principale": "..."
}}
JSON only."""

    user_prompt = f"""Analyze mobile app market trends for week {week} of {today[:4]}.
Angle: {angle}

Focus on:
- App Store and Google Play top charts (free + paid + grossing)
- ProductHunt recent app launches (trending products)
- Apps with high installs but poor reviews (rehabilitation targets)
- Underserved niches in productivity, health, finance, lifestyle, tools

Identify what a solo developer can build in 14-30 days and monetize immediately."""

    response = llm_call("stratege", system_prompt, user_prompt, temperature=0.75, max_tokens=3000)
    if not response:
        print("[Mobile Apps Brain] LLM call failed.", file=sys.stderr)
        sys.exit(1)

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]

    try:
        data = json.loads(clean.strip())
    except Exception as e:
        print(f"[Mobile Apps Brain] Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"mobile_apps_trends_{today}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    categories = data.get("categories_tendance", [])
    rehabilitations = data.get("apps_a_rehabiliter", [])
    reco = data.get("recommandation_principale", "")

    md = [
        f"# Mobile Apps Brain — {today} (angle: {angle})",
        "",
        "## Trending Categories",
    ]
    for c in categories[:5]:
        md.append(
            f"- **{c.get('categorie')} / {c.get('sous_niche')}** — {c.get('croissance')} | "
            f"saturation: {c.get('saturation')} | {c.get('framework_recommande')} | "
            f"{c.get('monetisation_optimale')} | ARPU ~${c.get('arpu_estime_usd', '?')}"
        )
    md += [
        "",
        "## Rehabilitation Targets",
    ]
    for r in rehabilitations[:3]:
        md.append(f"- **{r.get('nom')}** — {r.get('probleme')} → {r.get('opportunite')}")
    md += [
        "",
        "## Main Recommendation",
        reco,
    ]
    (REPORTS_DIR / f"mobile_apps_trends_{today}.md").write_text("\n".join(md), encoding="utf-8")

    print(f"[Mobile Apps Brain] ✓ → {out_path}")
    print(f"[Mobile Apps Brain] Reco: {reco[:120]}")


if __name__ == "__main__":
    run()
