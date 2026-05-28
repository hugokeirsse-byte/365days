#!/usr/bin/env python3
"""
Production Mobile Game Scaffold — génère la structure du projet depuis un CdC validé.

NE GÉNÈRE PAS de code de jeu complet — génère la structure et les fichiers clés
pour que Hugo puisse démarrer le développement immédiatement.

Produit dans products/mobile_games/{slug}/ :
  README.md             — spec complète + instructions setup
  STORE_LISTING.md      — texte App Store / Google Play / Itch.io
  project_structure.md  — arborescence recommandée du projet
  main_scene.gd         — fichier entry point commenté (si Godot 4)
  main.js               — fichier entry point commenté (si Phaser)
  main.py               — fichier entry point commenté (autre)

Variables d'env :
  GAME_DIR — chemin du produit (products/mobile_games/{slug})
             si absent, auto-détecte le dernier approuvé non produit
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.lib.brain_utils import llm_call


def find_approved_game() -> Path | None:
    """Trouve le dernier CdC approuvé non produit dans products/mobile_games/."""
    base = ROOT / "products" / "mobile_games"
    if not base.exists():
        return None
    for d in sorted(base.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        cdc_path = d / "cdc.json"
        if not cdc_path.exists():
            continue
        try:
            cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
            if cdc.get("gate_cdc") == "approved" and not cdc.get("production_status"):
                return d
        except Exception:
            continue
    return None


def generate_readme(cdc: dict) -> str:
    """Génère le README.md complet via LLM."""
    concept = cdc.get("concept", {})
    framework = cdc.get("framework", {})
    monetisation = cdc.get("monetisation", {})
    mvp = cdc.get("mvp_scope", {})
    store = cdc.get("store_listing", {})
    visuel = cdc.get("visuel", {})

    system_prompt = """You are a game developer documentation expert.
Generate a complete, developer-ready README.md for a mobile game project.
The README must include: project overview, setup instructions, architecture overview, MVP scope, monetization notes, and store submission checklist.
Write in English. Be concise but complete. Use Markdown formatting.
Output only the Markdown content, no JSON wrapper."""

    user_prompt = f"""Generate the README.md for this mobile game project:

Title: {concept.get('titre', 'Mobile Game')}
Genre: {concept.get('genre', '?')}
Pitch: {concept.get('pitch', '?')}
Core mechanic: {concept.get('gameplay_core', '?')}
Session length: {concept.get('session_length_min', 3)} minutes

Framework: {framework.get('choix', 'Godot 4')}
Export targets: {', '.join(framework.get('export_targets', ['android', 'ios']))}
Visual style: {visuel.get('style', '?')} | Palette: {visuel.get('palette', '?')}

Monetization: {monetisation.get('modele', '?')} | Price: ${monetisation.get('prix_achat_usd', 0)}
IAP: {monetisation.get('iap_description', 'N/A')}

MVP scope: {mvp.get('nb_niveaux', 10)} levels, ~{mvp.get('effort_estimé_jours', 14)} days effort
V1 features: {', '.join(mvp.get('features_v1', [])[:5])}

Store title: {store.get('titre_store', '?')}
Age rating: {store.get('age_rating', '4+')}
ASO keywords: {', '.join(cdc.get('mots_cles_aso', [])[:8])}

Include: setup steps for the chosen framework, folder structure overview, build commands for Android/iOS, monetization integration notes."""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.65, max_tokens=3000)
    if not response:
        print("[Scaffold] LLM failed to generate README.", file=sys.stderr)
        sys.exit(1)
    return response.strip()


def generate_store_listing(cdc: dict) -> str:
    """Génère le STORE_LISTING.md via LLM."""
    concept = cdc.get("concept", {})
    store = cdc.get("store_listing", {})
    monetisation = cdc.get("monetisation", {})

    system_prompt = """You are an App Store Optimization (ASO) expert.
Generate a complete STORE_LISTING.md with all text needed to submit the app to App Store, Google Play, and Itch.io.
Include: title variations, short description, long description, keywords, what's new (placeholder), and screenshots plan.
Write in English. Output only the Markdown content."""

    user_prompt = f"""Generate the complete store listing for:

Game title: {concept.get('titre', '?')}
Genre: {concept.get('genre', '?')}
Pitch: {concept.get('pitch', '?')}
Core mechanic: {concept.get('gameplay_core', '?')}

Store title: {store.get('titre_store', concept.get('titre', '?'))}
Short description provided: {store.get('description_courte_en', '?')}
Keywords: {', '.join(store.get('keywords', []))}
Age rating: {store.get('age_rating', '4+')}

Monetization: {monetisation.get('modele', '?')}
Price: ${monetisation.get('prix_achat_usd', 0)}

ASO keywords: {', '.join(cdc.get('mots_cles_aso', []))}

Generate sections for:
1. App Store (iOS) — title (30 chars), subtitle (30 chars), description (4000 chars), keywords (100 chars)
2. Google Play — title (50 chars), short description (80 chars), full description (4000 chars)
3. Itch.io — title, tagline, description
4. Screenshots plan (what each of the 5-8 screenshots should show)"""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.65, max_tokens=3000)
    if not response:
        print("[Scaffold] LLM failed to generate STORE_LISTING.", file=sys.stderr)
        sys.exit(1)
    return response.strip()


def generate_project_structure(cdc: dict) -> str:
    """Génère project_structure.md via LLM."""
    concept = cdc.get("concept", {})
    framework = cdc.get("framework", {})
    mvp = cdc.get("mvp_scope", {})

    system_prompt = """You are a game architecture expert.
Generate a project_structure.md showing the recommended folder/file tree for the mobile game project.
Include: folder tree with comments, key files description, naming conventions, asset organization.
Write in English. Output only the Markdown content."""

    user_prompt = f"""Generate the recommended project structure for:

Game: {concept.get('titre', '?')} ({concept.get('genre', '?')})
Framework: {framework.get('choix', 'Godot 4')}
Export targets: {', '.join(framework.get('export_targets', ['android', 'ios']))}

V1 features: {', '.join(mvp.get('features_v1', []))}
Visual style: {cdc.get('visuel', {}).get('style', '?')}

Include:
- Complete folder tree with inline comments
- Key scene/file descriptions
- Asset naming conventions
- Export/build folder structure
- Where to put monetization (ads/IAP) integration files"""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.6, max_tokens=2000)
    if not response:
        print("[Scaffold] LLM failed to generate project_structure.", file=sys.stderr)
        sys.exit(1)
    return response.strip()


def generate_entry_point(cdc: dict, framework: str) -> tuple[str, str]:
    """Génère le fichier entry point commenté. Retourne (nom_fichier, contenu)."""
    concept = cdc.get("concept", {})
    mvp = cdc.get("mvp_scope", {})

    system_prompt = """You are an expert game developer.
Generate a well-commented entry point / main scene file for the specified framework.
The file should be a practical starting template — NOT a complete game, but a solid foundation.
Include: scene setup, state machine skeleton, core loop placeholder, TODO comments for each V1 feature.
Write code comments in English. Output only the code, no JSON wrapper, no markdown fences."""

    if framework == "Godot 4":
        filename = "main_scene.gd"
        lang = "GDScript (Godot 4)"
    elif framework == "Phaser":
        filename = "main.js"
        lang = "JavaScript (Phaser 3)"
    else:
        filename = "main.py"
        lang = "Python (Pygame / generic)"

    user_prompt = f"""Generate the entry point file for:

Game: {concept.get('titre', '?')} ({concept.get('genre', '?')})
Framework: {lang}
Core mechanic: {concept.get('gameplay_core', '?')}
Session length: {concept.get('session_length_min', 3)} minutes

V1 features to scaffold:
{chr(10).join(f'- {f}' for f in mvp.get('features_v1', [])[:6])}

Requirements:
- Proper class/scene structure for {lang}
- State machine with at least: MENU, PLAYING, GAME_OVER states
- Core game loop skeleton
- TODO comments for each V1 feature
- Mobile-specific considerations (touch input, screen size, battery)
- Monetization hooks (banner/interstitial placeholder)"""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.65, max_tokens=3000)
    if not response:
        print("[Scaffold] LLM failed to generate entry point.", file=sys.stderr)
        sys.exit(1)
    return filename, response.strip()


def run():
    game_dir_env = os.environ.get("GAME_DIR", "").strip()

    if game_dir_env:
        game_dir = ROOT / game_dir_env
    else:
        game_dir = find_approved_game()

    if not game_dir:
        print("[Scaffold] No approved CdC found in products/mobile_games/")
        sys.exit(0)

    cdc_path = game_dir / "cdc.json"
    if not cdc_path.exists():
        print(f"[Scaffold] cdc.json missing: {cdc_path}", file=sys.stderr)
        sys.exit(1)

    cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
    gate = cdc.get("gate_cdc", "pending")

    if gate == "pending":
        print("[Scaffold] GATE=PENDING — waiting for Hugo validation.")
        sys.exit(0)
    if gate == "rejected":
        print("[Scaffold] GATE=REJECTED — production cancelled.")
        sys.exit(0)

    concept = cdc.get("concept", {})
    titre = concept.get("titre", game_dir.name)
    framework_choice = cdc.get("framework", {}).get("choix", "Godot 4")

    print(f"\n[Scaffold] Production: '{titre}' ({concept.get('genre', '?')})")
    print(f"[Scaffold] Framework: {framework_choice}")
    print(f"[Scaffold] Source: {game_dir.name}")

    # Generate README
    print("\n[Scaffold] Generating README.md...")
    readme = generate_readme(cdc)
    (game_dir / "README.md").write_text(readme, encoding="utf-8")
    print("[Scaffold] ✓ README.md")

    # Generate STORE_LISTING
    print("[Scaffold] Generating STORE_LISTING.md...")
    store_listing = generate_store_listing(cdc)
    (game_dir / "STORE_LISTING.md").write_text(store_listing, encoding="utf-8")
    print("[Scaffold] ✓ STORE_LISTING.md")

    # Generate project structure
    print("[Scaffold] Generating project_structure.md...")
    proj_structure = generate_project_structure(cdc)
    (game_dir / "project_structure.md").write_text(proj_structure, encoding="utf-8")
    print("[Scaffold] ✓ project_structure.md")

    # Generate entry point
    print(f"[Scaffold] Generating entry point for {framework_choice}...")
    entry_filename, entry_code = generate_entry_point(cdc, framework_choice)
    (game_dir / entry_filename).write_text(entry_code, encoding="utf-8")
    print(f"[Scaffold] ✓ {entry_filename}")

    # Update cdc.json
    cdc["production_status"] = "scaffold_generated"
    cdc["production_date"] = date.today().isoformat()
    cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[Scaffold] ✓ '{titre}' scaffold generated")
    print(f"[Scaffold] → {game_dir}")
    print(f"[Scaffold] Files: README.md, STORE_LISTING.md, project_structure.md, {entry_filename}")
    print(f"[Scaffold] Next: Open {entry_filename} in {framework_choice} and start coding!")


if __name__ == "__main__":
    run()
