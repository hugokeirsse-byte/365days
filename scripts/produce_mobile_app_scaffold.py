#!/usr/bin/env python3
"""
Production Mobile App Scaffold — génère la structure du projet depuis un CdC validé.

NE GÉNÈRE PAS une application complète — génère la structure et les fichiers clés
pour que Hugo puisse démarrer le développement immédiatement.

Produit dans products/mobile_apps/{slug}/ :
  README.md             — spec complète + instructions setup
  STORE_LISTING.md      — texte App Store / Google Play
  UX_FLOW.md            — écrans clés et flux de navigation
  main_screen.dart      — fichier entry point commenté (si Flutter)
  App.tsx               — fichier entry point commenté (si React Native)
  index.html            — fichier entry point commenté (si PWA)

Variables d'env :
  APP_DIR — chemin du produit (products/mobile_apps/{slug})
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


def find_approved_app() -> Path | None:
    """Trouve le dernier CdC approuvé non produit dans products/mobile_apps/."""
    base = ROOT / "products" / "mobile_apps"
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

    system_prompt = """You are a mobile app developer documentation expert.
Generate a complete, developer-ready README.md for a mobile application project.
The README must include: project overview, problem solved, setup instructions, architecture overview,
MVP scope, monetization notes, and store submission checklist.
Write in English. Be concise but complete. Use Markdown formatting.
Output only the Markdown content, no JSON wrapper."""

    user_prompt = f"""Generate the README.md for this mobile app project:

Title: {concept.get('titre', 'Mobile App')}
Category: {concept.get('categorie', '?')}
Problem solved: {concept.get('probleme_resolu', '?')}
Unique value: {concept.get('valeur_unique', '?')}
Target audience: {concept.get('public_cible', '?')}

Framework: {framework.get('choix', 'Flutter')}
Platforms: {', '.join(framework.get('plateformes', ['ios', 'android']))}

Monetization model: {monetisation.get('modele', '?')}
Monthly price: ${monetisation.get('prix_mensuel_usd', 0)}
One-time price: ${monetisation.get('prix_achat_usd', 0)}
Free features: {', '.join(monetisation.get('features_free', [])[:4])}
Premium features: {', '.join(monetisation.get('features_premium', [])[:4])}

MVP scope: ~{mvp.get('effort_estimé_jours', 21)} days effort
V1 features: {', '.join(mvp.get('features_v1', [])[:5])}

Store title: {store.get('titre_store', '?')}
Tagline: {store.get('tagline_en', '?')}
ASO keywords: {', '.join(store.get('keywords_aso', [])[:8])}

Include: setup steps for the chosen framework, folder structure overview,
build/run commands for iOS and Android, monetization integration notes,
privacy/offline data handling notes."""

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
Generate a complete STORE_LISTING.md with all text needed to submit the app to App Store and Google Play.
Include: title variations, short description, long description, keywords, what's new (placeholder),
privacy policy placeholder, and screenshots plan.
Write in English. Output only the Markdown content."""

    user_prompt = f"""Generate the complete store listing for:

App title: {concept.get('titre', '?')}
Category: {concept.get('categorie', '?')}
Problem solved: {concept.get('probleme_resolu', '?')}
Unique value: {concept.get('valeur_unique', '?')}
Target audience: {concept.get('public_cible', '?')}

Store title: {store.get('titre_store', concept.get('titre', '?'))}
Tagline: {store.get('tagline_en', '?')}
Description provided: {store.get('description_en', '?')}
ASO keywords: {', '.join(store.get('keywords_aso', []))}

Monetization: {monetisation.get('modele', '?')}
Free features: {', '.join(monetisation.get('features_free', [])[:4])}

Generate sections for:
1. App Store (iOS) — title (30 chars), subtitle (30 chars), description (4000 chars), keywords (100 chars)
2. Google Play — title (50 chars), short description (80 chars), full description (4000 chars)
3. Screenshots plan (what each of the {store.get('screenshots_count', 5)} screenshots should show)
4. Privacy policy template (offline-first, no data collection assumed)"""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.65, max_tokens=3000)
    if not response:
        print("[Scaffold] LLM failed to generate STORE_LISTING.", file=sys.stderr)
        sys.exit(1)
    return response.strip()


def generate_ux_flow(cdc: dict) -> str:
    """Génère UX_FLOW.md décrivant les écrans clés et le flux de navigation."""
    concept = cdc.get("concept", {})
    ux_screens = cdc.get("ux_key_screens", [])
    mvp = cdc.get("mvp_scope", {})
    monetisation = cdc.get("monetisation", {})

    system_prompt = """You are a mobile UX designer expert.
Generate a UX_FLOW.md describing the key screens, navigation flow, and UX decisions for a mobile app.
Include: screen inventory, navigation diagram (text-based), UX notes for each screen, onboarding flow,
monetization touchpoints, and accessibility considerations.
Write in English. Output only the Markdown content."""

    user_prompt = f"""Generate the UX flow document for:

App: {concept.get('titre', '?')} ({concept.get('categorie', '?')})
Problem solved: {concept.get('probleme_resolu', '?')}
Unique value: {concept.get('valeur_unique', '?')}
Target audience: {concept.get('public_cible', '?')}

Key screens identified: {', '.join(ux_screens)}
Monetization: {monetisation.get('modele', '?')}
Free features: {', '.join(monetisation.get('features_free', [])[:4])}
Premium features: {', '.join(monetisation.get('features_premium', [])[:3])}

V1 features: {', '.join(mvp.get('features_v1', []))}

For each screen, describe:
- Screen name and purpose
- Key UI elements
- User actions available
- Navigation destinations
- Data displayed/captured

Also include:
- Onboarding flow (first-launch experience)
- Paywall/upgrade prompt placement
- Empty states (first use)
- Error states"""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.65, max_tokens=2500)
    if not response:
        print("[Scaffold] LLM failed to generate UX_FLOW.", file=sys.stderr)
        sys.exit(1)
    return response.strip()


def generate_entry_point(cdc: dict, framework: str) -> tuple[str, str]:
    """Génère le fichier entry point commenté. Retourne (nom_fichier, contenu)."""
    concept = cdc.get("concept", {})
    mvp = cdc.get("mvp_scope", {})
    monetisation = cdc.get("monetisation", {})
    ux_screens = cdc.get("ux_key_screens", [])

    system_prompt = """You are an expert mobile app developer.
Generate a well-commented entry point / main screen file for the specified framework.
The file should be a practical starting template — NOT a complete app, but a solid foundation.
Include: navigation setup skeleton, key screen stubs, TODO comments for each V1 feature.
Write code comments in English. Output only the code, no JSON wrapper, no markdown fences."""

    if framework == "Flutter":
        filename = "main_screen.dart"
        lang = "Dart (Flutter)"
    elif framework == "React Native":
        filename = "App.tsx"
        lang = "TypeScript (React Native)"
    elif framework == "PWA":
        filename = "index.html"
        lang = "HTML/JS (Progressive Web App)"
    else:
        filename = "main.dart"
        lang = "Dart (Flutter)"

    user_prompt = f"""Generate the entry point file for:

App: {concept.get('titre', '?')} ({concept.get('categorie', '?')})
Framework: {lang}
Problem solved: {concept.get('probleme_resolu', '?')}

Key screens: {', '.join(ux_screens[:6])}

V1 features to scaffold:
{chr(10).join(f'- {f}' for f in mvp.get('features_v1', [])[:6])}

Monetization model: {monetisation.get('modele', '?')}

Requirements:
- Proper navigation/routing setup for {lang}
- Screen stubs for each key screen (empty but named correctly)
- TODO comments for each V1 feature
- Monetization hook placeholder ({monetisation.get('modele', 'freemium')} model)
- Local storage / offline-first architecture notes
- Accessibility basics (semantic labels)"""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.65, max_tokens=3000)
    if not response:
        print("[Scaffold] LLM failed to generate entry point.", file=sys.stderr)
        sys.exit(1)
    return filename, response.strip()


def run():
    app_dir_env = os.environ.get("APP_DIR", "").strip()

    if app_dir_env:
        app_dir = ROOT / app_dir_env
    else:
        app_dir = find_approved_app()

    if not app_dir:
        print("[Scaffold] No approved CdC found in products/mobile_apps/")
        sys.exit(0)

    cdc_path = app_dir / "cdc.json"
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
    titre = concept.get("titre", app_dir.name)
    framework_choice = cdc.get("framework", {}).get("choix", "Flutter")

    print(f"\n[Scaffold] Production: '{titre}' ({concept.get('categorie', '?')})")
    print(f"[Scaffold] Framework: {framework_choice}")
    print(f"[Scaffold] Source: {app_dir.name}")

    # Generate README
    print("\n[Scaffold] Generating README.md...")
    readme = generate_readme(cdc)
    (app_dir / "README.md").write_text(readme, encoding="utf-8")
    print("[Scaffold] ✓ README.md")

    # Generate STORE_LISTING
    print("[Scaffold] Generating STORE_LISTING.md...")
    store_listing = generate_store_listing(cdc)
    (app_dir / "STORE_LISTING.md").write_text(store_listing, encoding="utf-8")
    print("[Scaffold] ✓ STORE_LISTING.md")

    # Generate UX flow
    print("[Scaffold] Generating UX_FLOW.md...")
    ux_flow = generate_ux_flow(cdc)
    (app_dir / "UX_FLOW.md").write_text(ux_flow, encoding="utf-8")
    print("[Scaffold] ✓ UX_FLOW.md")

    # Generate entry point
    print(f"[Scaffold] Generating entry point for {framework_choice}...")
    entry_filename, entry_code = generate_entry_point(cdc, framework_choice)
    (app_dir / entry_filename).write_text(entry_code, encoding="utf-8")
    print(f"[Scaffold] ✓ {entry_filename}")

    # Update cdc.json
    cdc["production_status"] = "scaffold_generated"
    cdc["production_date"] = date.today().isoformat()
    cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[Scaffold] ✓ '{titre}' scaffold generated")
    print(f"[Scaffold] → {app_dir}")
    print(f"[Scaffold] Files: README.md, STORE_LISTING.md, UX_FLOW.md, {entry_filename}")
    print(f"[Scaffold] Next: Open {entry_filename} in {framework_choice} and start building!")


if __name__ == "__main__":
    run()
