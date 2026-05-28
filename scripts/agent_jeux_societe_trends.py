#!/usr/bin/env python3
"""
Cerveau perpétuel Jeux de Société — tendances tabletop print-and-play.

Analyse Etsy, DriveThruRPG, Itch.io, BoardGameGeek, Reddit r/tabletopgaming.
Identifie les niches rentables pour jeux imprimables.

Cron : jeudi 04h UTC

Variables d'env : JEU_ANGLE (override)
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions

ROOT = Path(__file__).resolve().parent.parent
BRAIN_DIR = ROOT / "data" / "brain" / "jeux_societe"

ANGLES_JEU = [
    "niches_metier_dark_humor",     # infirmières, profs, devs, pompiers
    "party_games_soirees",          # adultes, EVJF, team building
    "jeux_famille_intergenerationnel",
    "jeux_educatifs_ecole",
    "rpg_accessories_dnd",          # D&D 5e, Pathfinder, OSR
    "print_and_play_solo",          # solo games trending
    "jeux_voyage_compact",          # quick games, travel
]


def run():
    today = date.today().isoformat()
    week = date.today().isocalendar()[1]
    angle = os.environ.get("JEU_ANGLE") or ANGLES_JEU[week % len(ANGLES_JEU)]

    previous = get_previous_propositions("products/jeux_societe", "jeux_trends")
    print(f"[Jeux Brain] Angle: {angle} | Semaine: {week}")

    system_prompt = f"""Tu es un expert en jeux de société print-and-play vendus sur Etsy, DriveThruRPG et Itch.io.
Tu analyses le marché pour identifier les niches rentables et sous-exploitées.

{previous}

ANGLE D'ANALYSE : {angle}

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "date": "{today}",
  "angle": "{angle}",
  "niches_gagnantes": [
    {{
      "niche": "...",
      "type_jeu": "card_game|board_game|party_game|educational|rpg_accessory|dice_game",
      "plateforme_principale": "etsy|drivethrurpg|itch_io",
      "prix_moyen_usd": 7.99,
      "volume_ventes_estime": "faible|moyen|fort",
      "concurrence": "faible|moyenne|forte",
      "public_cible": "...",
      "angle_gagnant": "Ce qui fait vendre dans cette niche"
    }}
  ],
  "tendances_mecaniques": [
    {{
      "mecanique": "...",
      "pourquoi_ca_marche": "...",
      "type_jeu_ideal": "..."
    }}
  ],
  "niches_eviter": ["...", "..."],
  "opportunite_saisonniere": {{
    "event": "...",
    "date_approx": "...",
    "type_jeu_suggere": "...",
    "urgence": "urgent|normal|anticiper"
  }},
  "recommandation_cdc": {{
    "type_jeu": "...",
    "theme": "...",
    "mecanique": "...",
    "langue": "fr",
    "plateforme": "...",
    "priorite": "haute|normale"
  }}
}}
JSON uniquement."""

    user_prompt = f"""Analyse le marché jeux de société print-and-play aujourd'hui.
Focus : {angle}

Plateforme principale à analyser : Etsy (digital downloads) + DriveThruRPG (RPG) + Itch.io (indie)
Qu'est-ce qui se vend VRAIMENT en ce moment dans ces niches ?"""

    response = llm_call("stratege", system_prompt, user_prompt, temperature=0.75, max_tokens=3000)
    if not response:
        print("[Jeux Brain] Échec LLM.")
        return

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]

    try:
        data = json.loads(clean.strip())
    except Exception as e:
        print(f"[Jeux Brain] JSON invalide: {e}")
        return

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    out = BRAIN_DIR / f"jeux_trends_{today}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (BRAIN_DIR / "jeux_trends_latest.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report_dir = ROOT / "data" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    rec = data.get("recommandation_cdc", {})
    niches = data.get("niches_gagnantes", [])
    md = [
        f"# Rapport Jeux de Société Brain — {today}",
        f"**Angle** : {angle}",
        "",
        "## Niches gagnantes",
    ]
    for n in niches[:5]:
        md.append(f"- **{n.get('niche')}** ({n.get('type_jeu')}) — {n.get('plateforme_principale')} | {n.get('concurrence')} concurrence | {n.get('prix_moyen_usd')} USD")
        md.append(f"  → {n.get('angle_gagnant')}")
    md += [
        "",
        "## Recommandation CdC",
        f"**Type** : {rec.get('type_jeu')} | **Thème** : {rec.get('theme')}",
        f"**Mécanique** : {rec.get('mecanique')} | **Plateforme** : {rec.get('plateforme')}",
        f"**Priorité** : {rec.get('priorite')}",
    ]
    (report_dir / f"rapport_jeux_{today}.md").write_text("\n".join(md), encoding="utf-8")

    print(f"[Jeux Brain] ✓ → {out}")
    print(f"[Jeux Brain] Recommandation : {rec.get('type_jeu')} / {rec.get('theme')}")


if __name__ == "__main__":
    run()
