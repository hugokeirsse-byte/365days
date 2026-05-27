#!/usr/bin/env python3
"""
Injecteur d'idées Hugo — convertit une idée libre en CdC structuré.

Hugo tape une idée dans le workflow dispatch → ce script détecte le bon
vertical, génère les paramètres CdC, puis lance le bon générateur.

Variables d'env :
  HUGO_IDEE       — l'idée libre de Hugo
  HUGO_VERTICAL   — vertical cible (ou "auto_detect")
  HUGO_NB_VARIATIONS — nb de designs/variantes
"""

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call

ROOT = Path(__file__).resolve().parent.parent

VERTICAL_SCRIPTS = {
    "merch_design":  "scripts/agent_merch_design_cdc.py",
    "jeux_societe":  "scripts/agent_jeux_societe_cdc.py",
    "coloring":      "scripts/agent_coloring_cdc.py",
    "lowcontent":    "scripts/agent_cdc_lowcontent.py",
    "stl":           "scripts/agent_stl_cdc.py",
    "roman":         "scripts/agent_cdc_roman.py",
    "godot_assets":  "scripts/agent_godot_cdc.py",
}

VERTICAL_ENV_BUILDERS = {
    "merch_design": lambda p, n: {
        "MERCH_CONCEPT": p.get("concept", ""),
        "MERCH_NB_DESIGNS": str(n),
        "MERCH_STYLE": p.get("style", "flat colorful illustration"),
        "MERCH_LANGUE": p.get("langue", "en"),
    },
    "jeux_societe": lambda p, n: {
        "JEU_TYPE": p.get("type_jeu", "card_game"),
        "JEU_THEME": p.get("theme", ""),
        "JEU_MECANIQUE": p.get("mecanique", "questions réponses"),
        "JEU_LANGUE": p.get("langue", "fr"),
    },
    "coloring": lambda p, n: {
        "COLORING_THEME": p.get("theme", ""),
        "COLORING_AUDIENCE": p.get("audience", "adult"),
        "COLORING_PAGES": str(n) if int(n) <= 40 else "30",
    },
    "lowcontent": lambda p, n: {
        "LC_TYPE": p.get("type", "journal"),
        "LC_THEME": p.get("theme", ""),
        "LC_AUDIENCE": p.get("audience", "adults"),
    },
    "stl": lambda p, n: {
        "STL_TYPE": p.get("type_produit", "bookmark"),
        "STL_NICHE": p.get("niche", ""),
        "STL_NB_VARIANTES": str(min(int(n), 20)),
    },
    "roman": lambda p, n: {
        "ROMAN_GENRE": p.get("genre", "romance"),
        "ROMAN_SOUS_GENRE": p.get("sous_genre", "contemporary"),
        "ROMAN_LANGUE": p.get("langue", "en"),
    },
    "godot_assets": lambda p, n: {
        "GODOT_TYPE": p.get("type_asset", "sprite_pack"),
        "GODOT_THEME": p.get("theme", ""),
        "GODOT_NB_ASSETS": str(n),
    },
}


def detect_and_parse(idee: str, vertical_hint: str, nb: int) -> tuple[str, dict]:
    """Détecte le vertical et extrait les paramètres CdC depuis l'idée libre."""
    system_prompt = f"""Tu es un assistant qui analyse des idées de produits numériques.
Tu dois :
1. Détecter le vertical le plus approprié
2. Extraire les paramètres structurés pour générer un CdC

VERTICAUX DISPONIBLES :
- merch_design : designs POD (t-shirts, mugs, stickers, totes) — thème avec N variations graphiques
- jeux_societe : jeux imprimables (cartes, plateau, party, éducatif, RPG)
- coloring : livres de coloriage KDP (adulte/enfant)
- lowcontent : journaux/planners/trackers KDP
- stl : objets 3D imprimables (Cults3D)
- roman : romans KDP (romance, mystery, cozy...)
- godot_assets : assets/templates pour Godot (Itch.io)

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "vertical_detecte": "merch_design",
  "confiance": "haute|moyenne",
  "raison": "L'idée est clairement un concept de design avec plusieurs variations",
  "parametres": {{
    "concept": "proverbes du monde entier traduits en anglais avec illustration humoristique",
    "style": "flat colorful illustration",
    "langue": "en",
    "theme": "...",
    "type_jeu": "...",
    "mecanique": "...",
    "type": "...",
    "audience": "...",
    "genre": "...",
    "sous_genre": "...",
    "type_produit": "...",
    "niche": "...",
    "type_asset": "...",
    "titre_suggere": "..."
  }},
  "potentiel_commercial": "...",
  "commentaire": "Ce qui est bien dans cette idée"
}}
JSON uniquement. Inclure TOUS les champs parametres même si vides."""

    user_prompt = f"""Idée de Hugo : "{idee}"
Vertical suggéré par Hugo : {vertical_hint}
Nombre de variations voulues : {nb}

Analyse et structure cette idée."""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.5, max_tokens=1500)
    if not response:
        return vertical_hint if vertical_hint != "auto_detect" else "merch_design", {}

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]

    try:
        parsed = json.loads(clean.strip())
    except Exception:
        return vertical_hint if vertical_hint != "auto_detect" else "merch_design", {}

    vertical = parsed.get("vertical_detecte", vertical_hint)
    if vertical_hint != "auto_detect" and vertical_hint in VERTICAL_SCRIPTS:
        vertical = vertical_hint  # Hugo override

    params = parsed.get("parametres", {})
    print(f"[Idea Injector] Vertical détecté: {vertical} (confiance: {parsed.get('confiance', '?')})")
    print(f"[Idea Injector] Potentiel: {parsed.get('potentiel_commercial', '?')}")
    print(f"[Idea Injector] 💬 {parsed.get('commentaire', '')}")

    return vertical, params


def run():
    idee = os.environ.get("HUGO_IDEE", "")
    vertical_hint = os.environ.get("HUGO_VERTICAL", "auto_detect")
    nb = int(os.environ.get("HUGO_NB_VARIATIONS", "30"))

    if not idee:
        print("[Idea Injector] ERREUR: HUGO_IDEE est vide")
        sys.exit(1)

    print(f"[Idea Injector] Idée Hugo: '{idee}'")
    print(f"[Idea Injector] Vertical hint: {vertical_hint} | Nb variations: {nb}")

    vertical, params = detect_and_parse(idee, vertical_hint, nb)

    script_path = ROOT / VERTICAL_SCRIPTS.get(vertical, "scripts/agent_merch_design_cdc.py")
    if not script_path.exists():
        print(f"[Idea Injector] Script manquant: {script_path}")
        print(f"[Idea Injector] Vertical '{vertical}' pas encore implémenté.")
        sys.exit(1)

    env_builder = VERTICAL_ENV_BUILDERS.get(vertical)
    if not env_builder:
        print(f"[Idea Injector] Pas de builder d'env pour {vertical}")
        sys.exit(1)

    env_vars = env_builder(params, nb)
    env_vars["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")

    print(f"\n[Idea Injector] → Lancement {script_path.name} avec:")
    for k, v in env_vars.items():
        if k != "GEMINI_API_KEY":
            print(f"  {k}={v}")

    env = os.environ.copy()
    env.update(env_vars)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        env=env, cwd=str(ROOT),
        capture_output=False,
        timeout=300,
    )

    if result.returncode != 0:
        print(f"[Idea Injector] ✗ Échec (code {result.returncode})")
        sys.exit(result.returncode)

    print(f"\n[Idea Injector] ✓ CdC généré (gate=pending)")
    print(f"[Idea Injector] Idée '{idee}' → CdC en attente de validation Hugo")


if __name__ == "__main__":
    run()
