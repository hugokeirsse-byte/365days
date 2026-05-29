#!/usr/bin/env python3
"""
Brain agent hebdomadaire — tendances jeux mobiles.

Analyse les tendances sur App Store, Google Play, Itch.io pour identifier
les genres et niches de jeux mobiles les plus porteurs.

Plateformes : App Store (iOS), Google Play (Android), Itch.io (indie)

Cron : lundi 05h UTC
Variables d'env : MOBILE_GAMES_ANGLE (override)
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

ANGLES_MOBILE_GAMES = [
    "appstore_top_grossing_genres",        # genres qui génèrent le plus de revenus
    "google_play_rising_indie",            # jeux indie en montée sur Google Play
    "hypercasual_saturation_analysis",     # où le hypercasual est encore viable
    "mid_core_mobile_opportunity",         # jeux mid-core sous-exploités
    "itch_mobile_niche_gems",              # gems mobiles nichés sur Itch.io
    "seasonal_trending_mechanics",         # mécaniques saisonnières en vogue
    "low_rating_high_download_targets",    # cibles de réhabilitation
]


def run():
    today = date.today().isoformat()
    week = date.today().isocalendar()[1]
    angle = os.environ.get("MOBILE_GAMES_ANGLE") or ANGLES_MOBILE_GAMES[week % len(ANGLES_MOBILE_GAMES)]

    previous = get_previous_propositions("products/mobile_games", "mobile_games_trends")
    print(f"[Mobile Games Brain] Angle: {angle} | Semaine: {week}")

    system_prompt = f"""You are an expert in mobile game development and market analysis on App Store, Google Play, and Itch.io.
You analyze mobile game market trends to identify opportunities for solo indie developers.

{previous}

ANALYSIS ANGLE: {angle}

STRATEGIC RULES:
- LANGUAGE: English by default. Exception only if a specific market opportunity is proven (e.g., a Portuguese-speaking market with no competition).
- REHABILITATION: Identify games with high download volume but poor ratings (<3.5 stars). Typical causes: poor onboarding, intrusive ads, bugs at launch, missing content. A fixed version against weak competition = revenue opportunity.

RESPONSE FORMAT — STRICT JSON:
{{
  "date": "{today}",
  "angle": "{angle}",
  "genres_tendance": [
    {{
      "genre": "hyper_casual|puzzle|platformer|rpg|simulation|arcade|idle|strategy",
      "sous_niche": "...",
      "croissance": "explosif|fort|stable|déclinant",
      "saturation": "faible|moyenne|forte",
      "framework_recommande": "Godot 4|Unity|Phaser",
      "monetisation_optimale": "free_ads|freemium_iap|paid",
      "effort_mvp_jours": 14,
      "pourquoi_ca_marche": "...",
      "concurrent_faible_notes": "..."
    }}
  ],
  "jeux_a_rehabiliter": [{{"titre": "...", "probleme": "...", "opportunite": "..."}}],
  "recommandation_principale": "..."
}}
JSON only."""

    user_prompt = f"""Analyze mobile game market trends for week {week} of {today[:4]}.
Angle: {angle}

Focus on:
- App Store and Google Play top charts (free + paid + grossing)
- Itch.io mobile games section (indie opportunities)
- Emerging mechanics and genres
- Games with high installs but poor reviews (rehabilitation targets)

Identify what a solo developer can build in 14-21 days and monetize immediately."""

    response = llm_call("stratege", system_prompt, user_prompt, temperature=0.75, max_tokens=3000)
    if not response:
        print("[Mobile Games Brain] LLM call failed.", file=sys.stderr)
        sys.exit(1)

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]

    try:
        data = json.loads(clean.strip())
    except Exception as e:
        print(f"[Mobile Games Brain] Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"mobile_games_trends_{today}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    genres = data.get("genres_tendance", [])
    rehabilitations = data.get("jeux_a_rehabiliter", [])
    reco = data.get("recommandation_principale", "")

    md = [
        f"# Mobile Games Brain — {today} (angle: {angle})",
        "",
        "## Trending Genres",
    ]
    for g in genres[:5]:
        md.append(
            f"- **{g.get('genre')} / {g.get('sous_niche')}** — {g.get('croissance')} | "
            f"saturation: {g.get('saturation')} | {g.get('framework_recommande')} | "
            f"{g.get('monetisation_optimale')}"
        )
    md += [
        "",
        "## Rehabilitation Targets",
    ]
    for r in rehabilitations[:3]:
        md.append(f"- **{r.get('titre')}** — {r.get('probleme')} → {r.get('opportunite')}")
    md += [
        "",
        "## Main Recommendation",
        reco,
    ]
    (REPORTS_DIR / f"mobile_games_trends_{today}.md").write_text("\n".join(md), encoding="utf-8")

    print(f"[Mobile Games Brain] ✓ → {out_path}")
    print(f"[Mobile Games Brain] Reco: {reco[:120]}")


if __name__ == "__main__":
    run()
