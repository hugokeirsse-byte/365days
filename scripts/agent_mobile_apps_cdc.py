#!/usr/bin/env python3
"""
CdC Mobile Apps — génère un Cahier des Charges pour une application mobile.

Catégories supportées :
  productivity   — tâches, to-do, focus, organisation
  health         — sommeil, eau, respiration, fitness
  finance        — budget, dépenses, split bills
  lifestyle      — habitudes, humeur, journaling
  education      — flashcards, lecture rapide, langues
  tools          — convertisseur, utilitaires offline
  creativity     — sketch, journal créatif, écriture

Plateformes cibles : iOS (App Store) + Android (Google Play)

Variables d'env :
  APP_CATEGORY  — catégorie de l'app (ex: productivity, health, finance)
  APP_NICHE     — sous-niche (ex: "task manager anxiety-friendly")
  APP_ID        — identifiant (défaut: app_YYYY-MM-DD)
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions

ROOT = Path(__file__).resolve().parent.parent
APPS_DIR = ROOT / "products" / "mobile_apps"
REPORTS_DIR = ROOT / "data" / "reports"


def get_brain_signals() -> str:
    """Lit les derniers fichiers mobile_apps_trends_*.json pour injecter le contexte marché."""
    if not REPORTS_DIR.exists():
        return ""
    files = sorted(
        [f for f in REPORTS_DIR.glob("mobile_apps_trends_*.json")],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:3]
    signals = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            categories = data.get("categories_tendance", [])
            reco = data.get("recommandation_principale", "")
            for c in categories[:3]:
                signals.append(
                    f"- {c.get('categorie')}/{c.get('sous_niche')}: {c.get('croissance')} growth, "
                    f"{c.get('saturation')} saturation, {c.get('framework_recommande')}, "
                    f"ARPU ~${c.get('arpu_estime_usd', '?')}"
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
    app_category = os.environ.get("APP_CATEGORY", "productivity")
    app_niche = os.environ.get("APP_NICHE", "task manager minimal")
    app_id = os.environ.get("APP_ID", f"app_{today}")

    brain_signals = get_brain_signals()
    previous = get_previous_propositions("products/mobile_apps", "mobile_apps_cdc")

    print(f"[CdC Mobile Apps] Category: {app_category} | Niche: {app_niche}")

    system_prompt = f"""You are an expert in mobile app design, UX, and App Store/Google Play publishing strategy.
You create complete App Design Documents (Cahiers des Charges) for monetizable mobile applications.

{brain_signals}
{previous}

APP CATEGORY: {app_category}
NICHE: {app_niche}

STRATEGIC RULES:
- LANGUAGE: English by default for all store listings and content. Exception only if a specific proven market opportunity exists.
- REHABILITATION: Consider if this niche has poorly-rated competitors that can be beaten with better UX, offline support, or no-ads positioning.

RESPONSE FORMAT — STRICT JSON:
{{
  "app_id": "{app_id}",
  "date_cdc": "{today}",
  "gate_cdc": "pending",
  "concept": {{
    "titre": "...",
    "categorie": "{app_category}",
    "probleme_resolu": "...",
    "valeur_unique": "...",
    "public_cible": "..."
  }},
  "framework": {{
    "choix": "Flutter|React Native|PWA|Swift+Kotlin",
    "justification": "...",
    "plateformes": ["ios", "android"]
  }},
  "monetisation": {{
    "modele": "freemium|subscription|one_time|free_ads",
    "prix_mensuel_usd": 0,
    "prix_achat_usd": 0,
    "features_free": ["..."],
    "features_premium": ["..."],
    "justification": "..."
  }},
  "ux_key_screens": ["onboarding", "home", "..."],
  "store_listing": {{
    "titre_store": "...",
    "tagline_en": "...",
    "description_en": "150 words",
    "keywords_aso": ["..."],
    "screenshots_count": 5
  }},
  "mvp_scope": {{
    "features_v1": ["..."],
    "features_v2_plus": ["..."],
    "effort_estimé_jours": 21
  }}
}}
JSON only."""

    user_prompt = f"""Create the App Design Document for this mobile application:
- Category: {app_category}
- Niche: {app_niche}
- Target: solo developer, publishable in 21-30 days

The app must be viable on App Store and Google Play.
The monetization model must match category conventions (subscription for lifestyle/health, one_time for tools).
Focus on a tight MVP scope — solve one problem exceptionally well."""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.82, max_tokens=16000)
    if not response:
        print("[CdC Mobile Apps] LLM call failed.", file=sys.stderr)
        sys.exit(1)

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]

    try:
        cdc = json.loads(clean.strip())
    except Exception as e:
        print(f"[CdC Mobile Apps] Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    concept = cdc.get("concept", {})
    titre = concept.get("titre", app_id)
    slug = f"{app_id}_{titre[:30].lower().replace(' ', '_')}"
    out_dir = APPS_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "cdc.json").write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")

    store = cdc.get("store_listing", {})
    framework = cdc.get("framework", {})
    monetisation = cdc.get("monetisation", {})
    mvp = cdc.get("mvp_scope", {})
    ux_screens = cdc.get("ux_key_screens", [])

    md = [
        f"# CAHIER DES CHARGES — {titre}",
        f"**Category** : {app_category} | **Niche** : {app_niche}",
        f"**Status** : PENDING HUGO VALIDATION",
        f"**Date** : {today}",
        "",
        "## GATE = PENDING",
        "Validate: `gate_cdc = \"approved\"` in cdc.json → push",
        "",
        "## Concept",
        f"**Title** : {titre}",
        f"**Problem solved** : {concept.get('probleme_resolu', '?')}",
        f"**Unique value** : {concept.get('valeur_unique', '?')}",
        f"**Target audience** : {concept.get('public_cible', '?')}",
        "",
        "## Framework",
        f"**Choice** : {framework.get('choix', '?')}",
        f"**Justification** : {framework.get('justification', '?')}",
        f"**Platforms** : {', '.join(framework.get('plateformes', []))}",
        "",
        "## Monetisation",
        f"**Model** : {monetisation.get('modele', '?')}",
        f"**Monthly price** : ${monetisation.get('prix_mensuel_usd', 0)} | **One-time** : ${monetisation.get('prix_achat_usd', 0)}",
        "",
        "### Free Features",
    ]
    for f in monetisation.get("features_free", []):
        md.append(f"- {f}")
    md += [
        "",
        "### Premium Features",
    ]
    for f in monetisation.get("features_premium", []):
        md.append(f"- {f}")
    md += [
        "",
        "## UX Key Screens",
        ", ".join(ux_screens),
        "",
        "## Store Listing",
        f"**Title** : {store.get('titre_store', '?')}",
        f"**Tagline** : {store.get('tagline_en', '?')}",
        f"**Description** : {store.get('description_en', '?')}",
        f"**ASO Keywords** : {', '.join(store.get('keywords_aso', [])[:10])}",
        f"**Screenshots** : {store.get('screenshots_count', 5)}",
        "",
        "## MVP Scope",
        f"**Estimated effort** : {mvp.get('effort_estimé_jours', '?')} days",
        "",
        "### Features V1",
    ]
    for f in mvp.get("features_v1", []):
        md.append(f"- {f}")
    md += [
        "",
        "### Features V2+",
    ]
    for f in mvp.get("features_v2_plus", []):
        md.append(f"- {f}")

    (out_dir / "CAHIER_DES_CHARGES.md").write_text("\n".join(md), encoding="utf-8")

    print(f"[CdC Mobile Apps] ✓ '{titre}' → {out_dir}")
    print(f"[CdC Mobile Apps] GATE: pending — Hugo validates before production.")


if __name__ == "__main__":
    run()
