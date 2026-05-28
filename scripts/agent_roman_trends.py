#!/usr/bin/env python3
"""
Cerveau perpétuel Romans KDP — tendances genres et sous-genres.

Analyse les bestsellers KDP pour identifier les genres en croissance,
les tropes populaires, et les niches sous-exploitées en fiction.

Plateformes : Amazon KDP (eBook + paperback)

Cron : mercredi 05h UTC
Variables d'env : ROMAN_ANGLE (override)
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions

ROOT = Path(__file__).resolve().parent.parent
BRAIN_DIR = ROOT / "data" / "brain" / "roman"

ANGLES_ROMAN = [
    "romance_tropes_viral",        # tropes viraux TikTok/BookTok
    "cozy_mystery_sous_niches",    # bakery/bookshop/cat sleuth cozy
    "kindle_unlimited_strategies", # genres qui fonctionnent en KU
    "series_formulas",             # séries à fort LTV lecteur
    "covers_titres_tendances",     # analyse couvertures bestsellers
    "emerging_subgenres",          # sous-genres en émergence 2026
    "non_anglophone_gap",          # marchés FR/ES/DE sous-exploités
]


def run():
    today = date.today().isoformat()
    week = date.today().isocalendar()[1]
    angle = os.environ.get("ROMAN_ANGLE") or ANGLES_ROMAN[week % len(ANGLES_ROMAN)]

    previous = get_previous_propositions("products/novels", "roman_trends")
    print(f"[Roman Brain] Angle: {angle} | Semaine: {week}")

    system_prompt = f"""Tu es un expert en publication KDP, analyste des bestsellers Amazon Fiction.
Tu identifies les tendances de genres, tropes, et niches qui vendent sur Kindle.

{previous}

ANGLE D'ANALYSE : {angle}

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "date": "{today}",
  "angle": "{angle}",
  "genres_tendance": [
    {{
      "genre": "romance|cozy_mystery|paranormal|thriller|women_fiction",
      "sous_genre": "...",
      "trope_principal": "enemies_to_lovers|small_town|second_chance|...",
      "croissance": "explosif|fort|stable|déclinant",
      "concurrence": "faible|moyenne|forte|saturé",
      "prix_optimal_ebook_usd": 4.99,
      "longueur_ideale_mots": 65000,
      "public": "femmes 25-45|adultes 30-50|jeunes adultes",
      "pourquoi_ca_vend": "...",
      "exemple_titre_tendance": "..."
    }}
  ],
  "tropes_viraux_booktok": [
    {{
      "trope": "...",
      "plateforme_source": "TikTok|Instagram|Goodreads",
      "momentum": "montant|pic|redescend",
      "genre_associe": "..."
    }}
  ],
  "niches_sous_exploitees": [
    {{
      "niche": "...",
      "raison": "Peu de titres, forte demande",
      "premier_tome_suffit": true,
      "serie_recommandee": "3|5|standalone"
    }}
  ],
  "erreurs_a_eviter": ["...", "..."],
  "recommandation_prochain_roman": {{
    "genre": "...",
    "sous_genre": "...",
    "trope": "...",
    "langue": "en",
    "longueur_cible": 65000,
    "justification": "..."
  }}
}}
JSON uniquement."""

    user_prompt = f"""Analyse les tendances KDP Fiction pour la semaine {week} de {today[:4]}.
Angle : {angle}

Focus sur ce qui se vend MAINTENANT sur Amazon US KDP, particulièrement :
- Romance (le genre #1 KDP, 40%+ des ventes eBook)
- Cozy Mystery (croissance forte post-2023)
- Women's Fiction (stable, forte LTV)
- Paranormal Romance (retour en force)

Identifie les opportunités concrètes pour un auteur solo publiant via KDP."""

    response = llm_call("stratege", system_prompt, user_prompt, temperature=0.75, max_tokens=3000)
    if not response:
        print("[Roman Brain] Échec LLM.")
        return

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]

    try:
        data = json.loads(clean.strip())
    except Exception as e:
        print(f"[Roman Brain] JSON invalide: {e}")
        return

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BRAIN_DIR / f"roman_trends_{today}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    latest = BRAIN_DIR / "roman_trends_latest.json"
    latest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Report MD
    reco = data.get("recommandation_prochain_roman", {})
    genres = data.get("genres_tendance", [])
    md = [
        f"# Roman Brain — {today} (angle: {angle})",
        "",
        "## Genres en tendance",
    ]
    for g in genres[:5]:
        md.append(f"- **{g.get('genre')} / {g.get('sous_genre')}** — {g.get('trope_principal')} | {g.get('croissance')} | {g.get('pourquoi_ca_vend', '')[:80]}")
    md += [
        "",
        "## Recommandation prochain roman",
        f"**Genre** : {reco.get('genre')} / {reco.get('sous_genre')}",
        f"**Trope** : {reco.get('trope')}",
        f"**Justification** : {reco.get('justification', '')}",
    ]
    (BRAIN_DIR / f"roman_trends_{today}.md").write_text("\n".join(md), encoding="utf-8")

    print(f"[Roman Brain] ✓ → {out_path}")
    print(f"[Roman Brain] Reco: {reco.get('genre')} / {reco.get('sous_genre')} / {reco.get('trope')}")


if __name__ == "__main__":
    run()
