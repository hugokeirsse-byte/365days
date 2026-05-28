#!/usr/bin/env python3
"""
Cerveau perpétuel Merch / Print-on-Demand — tendances designs POD.

Couvre : tumbler wraps, SVG packs, iHeart designs, COPE packs,
cultural arbitrage, literal idioms, quotes, bible verses.
Plateformes : Redbubble, Merch by Amazon, Etsy (digital), Society6.

Cron : vendredi 04h UTC

Variables d'env : MERCH_ANGLE (override)
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions

ROOT = Path(__file__).resolve().parent.parent
BRAIN_DIR = ROOT / "data" / "brain" / "merch"

ANGLES_MERCH = [
    "tumbler_wraps_niches",          # 20oz/30oz sublimation Etsy bestsellers
    "svg_cricut_tendances",          # SVG cutting files Cricut/Silhouette
    "redbubble_niches_montantes",    # tags sous-exploités Redbubble
    "iheart_niches_locales",         # "I ❤️ X" géo-niches ou hobbies
    "quotes_viral_tiktok",           # citations virales courtes
    "cultural_words_untranslatable", # mots étrangers sans traduction
    "bible_verse_designs",           # marché chrétien KDP/Redbubble
]


def run():
    today = date.today().isoformat()
    week = date.today().isocalendar()[1]
    angle = os.environ.get("MERCH_ANGLE") or ANGLES_MERCH[week % len(ANGLES_MERCH)]

    previous = get_previous_propositions("products/tumbler_wraps", "merch_trends")
    print(f"[Merch Brain] Angle: {angle} | Semaine: {week}")

    system_prompt = f"""Tu es un expert en print-on-demand et digital downloads sur Redbubble, Etsy, Merch by Amazon.
Tu analyses les tendances de designs pour identifier les niches rentables.

{previous}

ANGLE D'ANALYSE : {angle}

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "date": "{today}",
  "angle": "{angle}",
  "niches_designs": [
    {{
      "niche": "...",
      "type_produit": "tumbler_wrap|svg_pack|quote_design|iheart|cultural|bible_verse",
      "plateforme": "etsy|redbubble|merch_amazon|society6",
      "trending_keywords": ["...", "..."],
      "volume_recherche": "faible|moyen|fort",
      "concurrence": "faible|moyenne|forte",
      "prix_optimal_usd": 3.99,
      "style_visuel": "minimaliste|coloré|vintage|boho|dark|cute",
      "pourquoi_ca_vend": "..."
    }}
  ],
  "sujets_viraux_actuels": [
    {{
      "sujet": "...",
      "plateforme_source": "TikTok|Pinterest|Instagram|Reddit",
      "duree_vie_estimee": "court_terme|moyen_terme|evergreen",
      "type_design_ideal": "..."
    }}
  ],
  "niches_eviter": ["...", "..."],
  "recommandation_production": {{
    "type_produit": "...",
    "niche": "...",
    "keywords_cles": ["...", "..."],
    "plateforme": "...",
    "priorite": "haute|normale"
  }}
}}
JSON uniquement."""

    user_prompt = f"""Analyse le marché POD/digital downloads aujourd'hui.
Focus : {angle}

Qu'est-ce qui performe sur Etsy et Redbubble en ce moment ?
Quels designs génèrent des ventes récurrentes (evergreen) vs viral court terme ?"""

    response = llm_call("stratege", system_prompt, user_prompt, temperature=0.75, max_tokens=3000)
    if not response:
        print("[Merch Brain] Échec LLM.")
        return

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]

    try:
        data = json.loads(clean.strip())
    except Exception as e:
        print(f"[Merch Brain] JSON invalide: {e}")
        return

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    out = BRAIN_DIR / f"merch_trends_{today}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (BRAIN_DIR / "merch_trends_latest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report_dir = ROOT / "data" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    rec = data.get("recommandation_production", {})
    niches = data.get("niches_designs", [])
    md = [
        f"# Rapport Merch Brain — {today}",
        f"**Angle** : {angle}",
        "",
        "## Niches designs",
    ]
    for n in niches[:5]:
        md.append(f"- **{n.get('niche')}** ({n.get('type_produit')}) — {n.get('plateforme')} | {n.get('concurrence')} concurrence | {n.get('prix_optimal_usd')} USD")
        md.append(f"  → {n.get('pourquoi_ca_vend')}")
    md += [
        "",
        "## Recommandation production",
        f"**Type** : {rec.get('type_produit')} | **Niche** : {rec.get('niche')}",
        f"**Keywords** : {', '.join(rec.get('keywords_cles', []))}",
        f"**Plateforme** : {rec.get('plateforme')} | **Priorité** : {rec.get('priorite')}",
    ]
    (report_dir / f"rapport_merch_{today}.md").write_text("\n".join(md), encoding="utf-8")

    print(f"[Merch Brain] ✓ → {out}")


if __name__ == "__main__":
    run()
