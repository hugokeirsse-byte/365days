#!/usr/bin/env python3
"""
CdC Mobile Games — génère un Cahier des Charges pour un jeu mobile.

Genres supportés :
  hyper_casual   — jeu à mécanique simple, session ultra-courte
  puzzle         — jeu de réflexion, logique, mots
  platformer     — plateforme 2D, saut, précision
  rpg            — jeu de rôle, progression, inventaire
  simulation     — gestion, construction, ferme
  arcade         — action rapide, score, endless
  idle           — incrémental, clicker, offline progress
  strategy       — stratégie temps réel ou tour par tour

Plateformes cibles : Android (Google Play) + iOS (App Store) + optionnel Itch.io

Variables d'env :
  GAME_GENRE    — genre du jeu (ex: puzzle, idle, platformer)
  GAME_NICHE    — sous-niche (ex: "cute animals idle clicker")
  GAME_ID       — identifiant (défaut: game_YYYY-MM-DD)
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions

ROOT = Path(__file__).resolve().parent.parent
GAMES_DIR = ROOT / "products" / "mobile_games"
REPORTS_DIR = ROOT / "data" / "reports"


def get_brain_signals() -> str:
    """Lit les derniers fichiers mobile_games_trends_*.json pour injecter le contexte marché."""
    if not REPORTS_DIR.exists():
        return ""
    files = sorted(
        [f for f in REPORTS_DIR.glob("mobile_games_trends_*.json")],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:3]
    signals = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            genres = data.get("genres_tendance", [])
            reco = data.get("recommandation_principale", "")
            for g in genres[:3]:
                signals.append(
                    f"- {g.get('genre')}/{g.get('sous_niche')}: {g.get('croissance')} growth, "
                    f"{g.get('saturation')} saturation, {g.get('framework_recommande')}"
                )
            if reco:
                signals.append(f"- RECO: {reco[:100]}")
        except Exception:
            pass
    if not signals:
        return ""
    return "MARKET SIGNALS FROM BRAIN ANALYSIS:\n" + "\n".join(signals) + "\n"


def run():
    today = date.today().isoformat()
    game_genre = os.environ.get("GAME_GENRE", "puzzle")
    game_niche = os.environ.get("GAME_NICHE", "minimalist logic grid")
    game_id = os.environ.get("GAME_ID", f"game_{today}")

    brain_signals = get_brain_signals()
    previous = get_previous_propositions("products/mobile_games", "mobile_games_cdc")

    print(f"[CdC Mobile Games] Genre: {game_genre} | Niche: {game_niche}")

    system_prompt = f"""You are an expert in mobile game design and App Store/Google Play publishing strategy.
You create complete Game Design Documents (Cahiers des Charges) for monetizable mobile games.

{brain_signals}
{previous}

GAME GENRE: {game_genre}
NICHE: {game_niche}

STRATEGIC RULES:
- LANGUAGE: English by default for all store listings and content. Exception only if a specific proven market opportunity exists.
- REHABILITATION: Consider if this niche has poorly-rated competitors that can be beaten with quality execution.

RESPONSE FORMAT — STRICT JSON:
{{
  "game_id": "{game_id}",
  "date_cdc": "{today}",
  "gate_cdc": "pending",
  "concept": {{
    "titre": "...",
    "genre": "{game_genre}",
    "pitch": "...",
    "gameplay_core": "core mechanic in 1 sentence",
    "session_length_min": 3
  }},
  "framework": {{
    "choix": "Godot 4|Unity|Phaser",
    "justification": "...",
    "export_targets": ["android", "ios", "web"]
  }},
  "monetisation": {{
    "modele": "free_ads|freemium_iap|paid|demo_plus_paid",
    "prix_achat_usd": 0,
    "iap_description": "...",
    "justification": "..."
  }},
  "visuel": {{
    "style": "pixel art 16x16|cartoon vector|minimalist|low poly 3d",
    "palette": "...",
    "ambiance": "..."
  }},
  "store_listing": {{
    "titre_store": "...",
    "description_courte_en": "80 words max",
    "keywords": ["..."],
    "age_rating": "4+|9+|12+|17+"
  }},
  "mvp_scope": {{
    "nb_niveaux": 10,
    "features_v1": ["..."],
    "features_v2": ["..."],
    "effort_estimé_jours": 14
  }},
  "mots_cles_aso": ["..."]
}}
JSON only."""

    user_prompt = f"""Create the Game Design Document for this mobile game:
- Genre: {game_genre}
- Niche: {game_niche}
- Target: solo developer, publishable in 14-21 days

The game must be viable on App Store and Google Play.
The monetization model must be justified by genre conventions.
Focus on a tight MVP scope that can be shipped fast."""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.82, max_tokens=16000)
    if not response:
        print("[CdC Mobile Games] LLM call failed.", file=sys.stderr)
        sys.exit(1)

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]

    try:
        cdc = json.loads(clean.strip())
    except Exception as e:
        print(f"[CdC Mobile Games] Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    concept = cdc.get("concept", {})
    titre = concept.get("titre", game_id)
    slug = f"{game_id}_{titre[:30].lower().replace(' ', '_')}"
    out_dir = GAMES_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "cdc.json").write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")

    store = cdc.get("store_listing", {})
    framework = cdc.get("framework", {})
    monetisation = cdc.get("monetisation", {})
    mvp = cdc.get("mvp_scope", {})
    visuel = cdc.get("visuel", {})

    md = [
        f"# CAHIER DES CHARGES — {titre}",
        f"**Genre** : {game_genre} | **Niche** : {game_niche}",
        f"**Statut** : EN ATTENTE VALIDATION HUGO",
        f"**Date** : {today}",
        "",
        "## GATE = PENDING",
        "Valider : `gate_cdc = \"approved\"` dans cdc.json → push",
        "",
        "## Concept",
        f"**Titre** : {titre}",
        f"**Pitch** : {concept.get('pitch', '?')}",
        f"**Gameplay core** : {concept.get('gameplay_core', '?')}",
        f"**Session** : {concept.get('session_length_min', '?')} min",
        "",
        "## Framework",
        f"**Choix** : {framework.get('choix', '?')}",
        f"**Justification** : {framework.get('justification', '?')}",
        f"**Export** : {', '.join(framework.get('export_targets', []))}",
        "",
        "## Monetisation",
        f"**Modèle** : {monetisation.get('modele', '?')}",
        f"**Prix** : {monetisation.get('prix_achat_usd', 0)} USD",
        f"**IAP** : {monetisation.get('iap_description', '?')}",
        "",
        "## Visuel",
        f"**Style** : {visuel.get('style', '?')}",
        f"**Palette** : {visuel.get('palette', '?')}",
        f"**Ambiance** : {visuel.get('ambiance', '?')}",
        "",
        "## Store Listing",
        f"**Titre store** : {store.get('titre_store', '?')}",
        f"**Description** : {store.get('description_courte_en', '?')}",
        f"**Keywords** : {', '.join(store.get('keywords', [])[:8])}",
        f"**Age rating** : {store.get('age_rating', '4+')}",
        "",
        "## MVP Scope",
        f"**Niveaux** : {mvp.get('nb_niveaux', '?')}",
        f"**Effort estimé** : {mvp.get('effort_estimé_jours', '?')} jours",
        "",
        "### Features V1",
    ]
    for f in mvp.get("features_v1", []):
        md.append(f"- {f}")
    md += [
        "",
        "### Features V2",
    ]
    for f in mvp.get("features_v2", []):
        md.append(f"- {f}")
    md += [
        "",
        "## ASO Keywords",
        ", ".join(cdc.get("mots_cles_aso", [])[:10]),
    ]

    (out_dir / "CAHIER_DES_CHARGES.md").write_text("\n".join(md), encoding="utf-8")

    print(f"[CdC Mobile Games] ✓ '{titre}' → {out_dir}")
    print(f"[CdC Mobile Games] GATE: pending — Hugo validates before production.")


if __name__ == "__main__":
    run()
