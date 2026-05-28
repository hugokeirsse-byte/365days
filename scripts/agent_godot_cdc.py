#!/usr/bin/env python3
"""
CdC Godot Assets — génère un Cahier des Charges pour assets/templates Godot.

Types :
  sprite_pack    — pack de sprites thématiques (personnages, ennemis, décors)
  ui_kit         — interface utilisateur complète (boutons, panneaux, icônes)
  tileset        — tilesets pour platformer/RPG/top-down
  sound_pack     — sons et musiques (si génération audio disponible)
  game_template  — template de jeu complet (platformer, RPG, puzzle, runner)
  shader_pack    — shaders Godot 4 (effets visuels, post-process)
  addon          — plugin/addon Godot (outil éditeur, système de dialogue...)

Plateforme principale : Itch.io (60-80% revenus, ~10% commission)
Secondaire : Godot Asset Library (gratuit/donationware → visibilité)

Variables d'env :
  GODOT_TYPE     — sprite_pack|ui_kit|tileset|game_template|shader_pack|addon
  GODOT_THEME    — thème (ex: "fantasy medieval", "cyberpunk neon", "cozy farm")
  GODOT_NB_ASSETS — nombre d'assets dans le pack (défaut: 30)
  GODOT_ID       — identifiant (défaut: godot_YYYY-MM-DD)
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions

ROOT = Path(__file__).resolve().parent.parent
GODOT_DIR = ROOT / "products" / "godot_assets"

TYPE_SPECS = {
    "sprite_pack": {
        "livrable": "PNG sprites + JSON atlas, 16x16/32x32/64x64px, fond transparent",
        "outil": "Pillow (génération procédurale ou Pollinations pour l'art)",
        "prix_typique": "4.99-14.99 USD",
        "nb_assets_typique": "30-100 sprites",
    },
    "ui_kit": {
        "livrable": "PNG/SVG composants UI, scales multiples, thème cohérent",
        "outil": "ReportLab/SVG + Pillow",
        "prix_typique": "6.99-19.99 USD",
        "nb_assets_typique": "50-150 éléments",
    },
    "tileset": {
        "livrable": "PNG tileset 16x16 ou 32x32, compatibilité Godot TileMap",
        "outil": "Pillow (génération procédurale)",
        "prix_typique": "4.99-12.99 USD",
        "nb_assets_typique": "1 tileset de 64-256 tuiles",
    },
    "game_template": {
        "livrable": "Projet Godot 4 (.godot + scenes + scripts GDScript)",
        "outil": "Génération de code GDScript + assets",
        "prix_typique": "9.99-29.99 USD",
        "nb_assets_typique": "1 template complet",
    },
    "shader_pack": {
        "livrable": "Fichiers .gdshader + démo scène Godot",
        "outil": "Génération code GLSL/GDScript",
        "prix_typique": "4.99-14.99 USD",
        "nb_assets_typique": "10-30 shaders",
    },
    "addon": {
        "livrable": "Plugin Godot 4 (addons/ folder) + documentation",
        "outil": "Génération code GDScript",
        "prix_typique": "free/donationware ou 4.99-24.99 USD",
        "nb_assets_typique": "1 addon complet",
    },
}


def run():
    today = date.today().isoformat()
    godot_type = os.environ.get("GODOT_TYPE", "sprite_pack")
    godot_theme = os.environ.get("GODOT_THEME", "fantasy medieval")
    nb_assets = int(os.environ.get("GODOT_NB_ASSETS", "30"))
    godot_id = os.environ.get("GODOT_ID", f"godot_{today}")

    spec = TYPE_SPECS.get(godot_type, TYPE_SPECS["sprite_pack"])
    previous = get_previous_propositions("products/godot_assets", "godot_cdc")

    print(f"[CdC Godot] Type: {godot_type} | Thème: {godot_theme} | {nb_assets} assets")

    system_prompt = f"""Tu es un expert en game development assets pour Godot 4 et en vente sur Itch.io.
Tu crées des Cahiers des Charges complets pour des packs d'assets vendables.

{previous}

TYPE D'ASSET : {godot_type}
Livrable attendu : {spec['livrable']}
Outil de production : {spec['outil']}
Prix typique : {spec['prix_typique']}
Volume typique : {spec['nb_assets_typique']}

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "godot_id": "{godot_id}",
  "date_cdc": "{today}",
  "gate_cdc": "pending",
  "type_asset": "{godot_type}",
  "concept": {{
    "titre": "...",
    "sous_titre": "...",
    "theme": "{godot_theme}",
    "description": "...",
    "element_unique": "Ce qui le différencie des 1000 packs gratuits sur Itch.io",
    "nb_assets": {nb_assets},
    "compatibilite": "Godot 4.x (4.2+)"
  }},
  "public_cible": {{
    "profil": "indie dev solo / étudiant gamedev / game jam participant",
    "niveau": "débutant|intermédiaire|avancé",
    "projet_type": "platformer|RPG|top-down|puzzle|runner|horror"
  }},
  "contenu_pack": [
    {{
      "categorie": "...",
      "nb": 10,
      "description": "...",
      "format": "PNG 32x32px transparent",
      "exemples": ["...", "...", "..."]
    }}
  ],
  "spec_production": {{
    "outil": "{spec['outil']}",
    "resolution": "32x32 ou 64x64px",
    "format_fichiers": ["PNG", "JSON atlas optionnel"],
    "structure_dossiers": {{
      "characters/": "sprites personnages",
      "environment/": "décors et obstacles",
      "ui/": "interface si applicable",
      "demo/": "scène Godot de démonstration"
    }},
    "godot_demo": true,
    "licence": "CC0 (domaine public) ou Custom License (usage commercial OK)"
  }},
  "listing_itchio": {{
    "titre": "...",
    "description_courte": "...",
    "description_longue": "...",
    "tags": ["godot", "assets", "...", "...", "..."],
    "prix_usd": 6.99,
    "modele": "payant|pwyw|gratuit+premium",
    "screenshots_necessaires": 4
  }},
  "cinq_concurrents_itchio": [
    {{"titre": "...", "prix": 0, "downloads": 5000, "notre_avantage": "..."}}
  ],
  "calendrier": {{
    "jours_production": 2,
    "mise_a_jour_prevue": "v2 dans 30 jours (20 assets supplémentaires)",
    "serie_possible": true
  }},
  "criteres_validation": {{
    "assets_coherents": "Style visuel homogène sur tous les assets ?",
    "demo_fonctionnelle": "La scène démo se charge dans Godot 4 sans erreur ?",
    "documentation": "README avec instructions d'import inclus ?",
    "differenciateur": "Ce pack apporte-t-il quelque chose qu'on ne trouve pas gratuit ?"
  }}
}}
JSON uniquement."""

    user_prompt = f"""Crée le CdC pour ce pack d'assets Godot :
- Type : {godot_type}
- Thème : {godot_theme}
- Nombre d'assets : {nb_assets}

Le pack doit être VENDABLE sur Itch.io face à la concurrence gratuite.
L'élément unique doit justifier le prix."""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.82, max_tokens=16000)
    if not response:
        print("[CdC Godot] Échec LLM.", file=sys.stderr)
        sys.exit(1)

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]

    try:
        cdc = json.loads(clean.strip())
    except Exception as e:
        print(f"[CdC Godot] JSON invalide: {e}", file=sys.stderr)
        sys.exit(1)

    concept = cdc.get("concept", {})
    titre = concept.get("titre", godot_id)
    slug = f"{godot_id}_{titre[:30].lower().replace(' ', '_')}"
    out_dir = GODOT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "cdc.json").write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")

    listing = cdc.get("listing_itchio", {})
    contenu = cdc.get("contenu_pack", [])
    md = [
        f"# CAHIER DES CHARGES — {titre}",
        f"**Type** : {godot_type} | **Thème** : {godot_theme}",
        f"**Statut** : EN ATTENTE VALIDATION HUGO",
        f"**Date** : {today}",
        "",
        "## 🔴 GATE = PENDING",
        "Valider : `gate_cdc = \"approved\"` dans cdc.json → push",
        "",
        f"## Concept",
        f"**Titre** : {titre}",
        f"**Élément unique** : {concept.get('element_unique', '?')}",
        f"**Assets** : {concept.get('nb_assets', '?')} | **Compatibilité** : {concept.get('compatibilite', '?')}",
        "",
        "## Contenu du pack",
    ]
    for cat in contenu:
        md.append(f"- **{cat.get('categorie')}** × {cat.get('nb')} — {cat.get('description')} ({cat.get('format')})")
        for ex in cat.get("exemples", [])[:3]:
            md.append(f"  - {ex}")
    md += [
        "",
        f"## Listing Itch.io",
        f"**Prix** : {listing.get('prix_usd')} USD ({listing.get('modele')})",
        f"**Tags** : {', '.join(listing.get('tags', []))}",
        "",
        "## Checklist validation",
        f"- [ ] {cdc.get('criteres_validation', {}).get('assets_coherents', '?')}",
        f"- [ ] {cdc.get('criteres_validation', {}).get('demo_fonctionnelle', '?')}",
        f"- [ ] {cdc.get('criteres_validation', {}).get('differenciateur', '?')}",
    ]
    (out_dir / "CAHIER_DES_CHARGES.md").write_text("\n".join(md), encoding="utf-8")

    print(f"[CdC Godot] ✓ '{titre}' → {out_dir}")
    print(f"[CdC Godot] GATE: pending — Hugo valide avant production.")


if __name__ == "__main__":
    run()
