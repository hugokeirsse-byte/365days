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
from scripts.lib.brain_utils import llm_call, extract_json, get_previous_propositions

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
  }},
  "strategie_produit": {{
    "pilier": "creation_originale|domaine_public|imitation_amelioree",
    "justification": "Pourquoi CE pilier pour CETTE app spécifique, avec preuves concrètes",
    "creation_originale": {{
      "signaux_trend": ["signal Google Trends / TikTok / Reddit / App Store observé", "..."],
      "timing_optimal": "Pourquoi MAINTENANT et pas dans 6 mois",
      "risque_saturation": "faible|moyen|fort — dans combien de mois"
    }},
    "domaine_public": {{
      "oeuvre_source": "Titre + auteur + année de publication",
      "source_telechargement": "archive.org / Project Gutenberg / Wikimedia Commons / etc.",
      "licence_confirmee": "CC0 / domaine public US + pays cibles confirmé",
      "qualite_disponible": "300 DPI / vectorisable / restauration nécessaire",
      "angle_commercial": "Comment on monétise cette oeuvre PD concrètement"
    }},
    "imitation_amelioree": {{
      "produit_cible": "Titre exact de l'app qui explose sur App Store/Google Play",
      "pourquoi_ca_marche": "Analyse précise de son succès (téléchargements, avis, revenus estimés)",
      "ce_qui_est_mal_fait": "Ce que les utilisateurs reprochent (avis 1-3 étoiles précis)",
      "notre_amelioration_concrete": "Comment on fait strictement mieux, point par point",
      "differentiation_legale": "En quoi on ne copie pas (UX inspirée ≠ clone)"
    }}
  }},
  "potentiel_revenu": {{
    "scenario_conservateur": {{"ventes_mois_1": 10, "ventes_mois_6": 50, "revenu_annuel_estime": "$500"}},
    "scenario_optimiste": {{"ventes_mois_1": 50, "ventes_mois_6": 300, "revenu_annuel_estime": "$3000"}},
    "levier_croissance": "ce qui peut multiplier les revenus (abonnement, IAP, version Pro, B2B...)"
  }}
}}
JSON only."""

    user_prompt = f"""Create the App Design Document for this mobile application:
- Category: {app_category}
- Niche: {app_niche}
- Target: solo developer, publishable in 21-30 days

The app must be viable on App Store and Google Play.
The monetization model must match category conventions (subscription for lifestyle/health, one_time for tools).
Focus on a tight MVP scope — solve one problem exceptionally well.

PRODUCT STRATEGY — determine which of the 3 pillars applies and justify with evidence:
1. creation_originale — if a clear signal from Google Trends / TikTok / Reddit / App Store charts indicates an emerging need not yet addressed
2. domaine_public — if a public domain methodology, book, or system (pre-1928) can be digitized and monetized as an app feature
3. imitation_amelioree — if a competitor app is already exploding but with exploitable flaws (bad UX, no offline, intrusive ads, missing features)"""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.82, max_tokens=8000)
    if not response:
        print("[CdC Mobile Apps] LLM call failed.", file=sys.stderr)
        sys.exit(1)

    clean = extract_json(response)

    try:
        cdc = json.loads(clean)
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
    strategie = cdc.get("strategie_produit", {})
    potentiel = cdc.get("potentiel_revenu", {})

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
        "## Stratégie Produit",
        f"**Pilier** : `{strategie.get('pilier', '?')}`",
        f"**Justification** : {strategie.get('justification', '?')}",
        "",
    ]

    pilier = strategie.get("pilier", "")
    if pilier == "creation_originale":
        co = strategie.get("creation_originale", {})
        md += [
            "**Signaux trend** : " + " | ".join(co.get("signaux_trend", [])),
            f"**Timing** : {co.get('timing_optimal', '?')}",
            f"**Risque saturation** : {co.get('risque_saturation', '?')}",
        ]
    elif pilier == "domaine_public":
        dp = strategie.get("domaine_public", {})
        md += [
            f"**Oeuvre source** : {dp.get('oeuvre_source', '?')}",
            f"**Source** : {dp.get('source_telechargement', '?')}",
            f"**Licence** : {dp.get('licence_confirmee', '?')}",
            f"**Angle commercial** : {dp.get('angle_commercial', '?')}",
        ]
    elif pilier == "imitation_amelioree":
        ia = strategie.get("imitation_amelioree", {})
        md += [
            f"**Produit cible** : {ia.get('produit_cible', '?')}",
            f"**Pourquoi ça marche** : {ia.get('pourquoi_ca_marche', '?')}",
            f"**Ce qui est mal fait** : {ia.get('ce_qui_est_mal_fait', '?')}",
            f"**Notre amélioration** : {ia.get('notre_amelioration_concrete', '?')}",
            f"**Différenciation légale** : {ia.get('differentiation_legale', '?')}",
        ]

    sc = potentiel.get("scenario_conservateur", {})
    so = potentiel.get("scenario_optimiste", {})
    md += [
        "",
        "### Potentiel Revenu",
        f"**Conservateur** : M1={sc.get('ventes_mois_1','?')} ventes, M6={sc.get('ventes_mois_6','?')} ventes, annuel {sc.get('revenu_annuel_estime','?')}",
        f"**Optimiste** : M1={so.get('ventes_mois_1','?')} ventes, M6={so.get('ventes_mois_6','?')} ventes, annuel {so.get('revenu_annuel_estime','?')}",
        f"**Levier croissance** : {potentiel.get('levier_croissance', '?')}",
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
