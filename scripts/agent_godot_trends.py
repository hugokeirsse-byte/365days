#!/usr/bin/env python3
"""
Cerveau perpétuel Godot Assets / Itch.io — tendances assets game dev.

Analyse ce qui se vend sur Itch.io et Godot Asset Library pour identifier
les types d'assets et thèmes les plus recherchés par les game developers.

Plateformes : Itch.io (primary), Godot Asset Library (secondary, gratuit/visibilité)

Cron : samedi 05h UTC
Variables d'env : GODOT_ANGLE (override)
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions

ROOT = Path(__file__).resolve().parent.parent
BRAIN_DIR = ROOT / "data" / "brain" / "godot"

ANGLES_GODOT = [
    "itchio_bestsellers_assets",      # top assets payants Itch.io
    "game_jam_needs",                 # assets demandés pendant game jams
    "godot4_migration_gaps",          # ce qui manque spécifiquement Godot 4
    "solo_dev_productivity_tools",    # addons qui font gagner du temps
    "pixel_art_trends",               # styles pixel art en vogue
    "mobile_game_assets",             # assets optimisés mobile
    "horror_indie_rising",            # niche horror indie en croissance
]


def run():
    today = date.today().isoformat()
    week = date.today().isocalendar()[1]
    angle = os.environ.get("GODOT_ANGLE") or ANGLES_GODOT[week % len(ANGLES_GODOT)]

    previous = get_previous_propositions("products/godot_assets", "godot_trends")
    print(f"[Godot Brain] Angle: {angle} | Semaine: {week}")

    system_prompt = f"""Tu es un expert en assets game dev et en vente sur Itch.io.
Tu analyses les tendances du marché des assets Godot pour identifier les opportunités.

{previous}

ANGLE D'ANALYSE : {angle}

RÈGLES STRATÉGIQUES :
- LANGUE : Anglais uniquement pour les assets et documentations (marché Itch.io international).
- RÉHABILITATION : Cherche des assets très téléchargés/achetés sur Itch.io avec mauvaises
  reviews. Raison habituelle : pas de README, assets incomplets, résolution trop basse,
  incompatibilité Godot 4. Une version qui corrige ça face à la concurrence gratuite = vente.

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "date": "{today}",
  "angle": "{angle}",
  "types_assets_tendance": [
    {{
      "type": "sprite_pack|ui_kit|tileset|shader_pack|addon|game_template",
      "theme": "...",
      "croissance": "explosif|fort|stable|déclinant",
      "concurrence_gratuite": "faible|moyenne|forte",
      "prix_optimal_usd": 6.99,
      "acheteurs_cibles": "indie solo|game jam|étudiant|pro",
      "differenciateur_cle": "Ce qui manque dans les assets gratuits existants",
      "nb_assets_minimum": 30,
      "pourquoi_ca_vend": "..."
    }}
  ],
  "game_jams_prochains": [
    {{
      "jam": "...",
      "date_approximative": "...",
      "theme_probable": "...",
      "assets_a_preparer": "..."
    }}
  ],
  "niches_sous_exploitees": [
    {{
      "niche": "...",
      "raison": "...",
      "type_asset_ideal": "..."
    }}
  ],
  "erreurs_a_eviter": ["...", "..."],
  "recommandation_prochain_pack": {{
    "type": "...",
    "theme": "...",
    "nb_assets": 30,
    "prix_suggere_usd": 6.99,
    "justification": "...",
    "urgence": "haute|normale|basse"
  }}
}}
JSON uniquement."""

    user_prompt = f"""Analyse les tendances du marché assets Godot/Itch.io pour la semaine {week} de {today[:4]}.
Angle : {angle}

Focus sur :
- Itch.io (principale plateforme de vente, prix 4-20$)
- Godot Asset Library (gratuit → visibilité → upsell Itch.io)
- Besoins des game jams (Ludum Dare, GMTK, etc.)
- Godot 4 spécifiquement (migration depuis Unity post-controversy toujours active)

Identifie ce qu'un créateur solo peut produire en 2-3 jours et vendre immédiatement."""

    response = llm_call("stratege", system_prompt, user_prompt, temperature=0.75, max_tokens=3000)
    if not response:
        print("[Godot Brain] Échec LLM.")
        return

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]

    try:
        data = json.loads(clean.strip())
    except Exception as e:
        print(f"[Godot Brain] JSON invalide: {e}")
        return

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    out_path = BRAIN_DIR / f"godot_trends_{today}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    latest = BRAIN_DIR / "godot_trends_latest.json"
    latest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    reco = data.get("recommandation_prochain_pack", {})
    types_tendance = data.get("types_assets_tendance", [])
    md = [
        f"# Godot Brain — {today} (angle: {angle})",
        "",
        "## Types d'assets en tendance",
    ]
    for t in types_tendance[:5]:
        md.append(f"- **{t.get('type')} / {t.get('theme')}** — {t.get('croissance')} | {t.get('differenciateur_cle', '')[:80]}")
    md += [
        "",
        "## Recommandation prochain pack",
        f"**Type** : {reco.get('type')} / {reco.get('theme')}",
        f"**Prix suggéré** : {reco.get('prix_suggere_usd')} USD",
        f"**Urgence** : {reco.get('urgence')}",
        f"**Justification** : {reco.get('justification', '')}",
    ]
    (BRAIN_DIR / f"godot_trends_{today}.md").write_text("\n".join(md), encoding="utf-8")

    print(f"[Godot Brain] ✓ → {out_path}")
    print(f"[Godot Brain] Reco: {reco.get('type')} / {reco.get('theme')} ({reco.get('prix_suggere_usd')} USD)")


if __name__ == "__main__":
    run()
