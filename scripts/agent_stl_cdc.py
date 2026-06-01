#!/usr/bin/env python3
"""
Agent STL CdC — Generates a Cahier des Charges for a new STL product.
Hugo reviews and approves/rejects via gate_cdc field.

Env vars:
  STL_TYPE        bookmark|keychain|coaster|door_plate|plant_marker  (default: bookmark)
  STL_NICHE       cottagecore|dnd|witchy|minimalist|booklover|botanical|gaming|pet  (default: cottagecore)
  STL_NB_VARIANTES  int  (default: 15)
  STL_ID          e.g. stl_2026-05-27  (default: stl_YYYY-MM-DD)
  GEMINI_API_KEY

Output:
  products/stl_3d/{stl_id}_{titre_slug}/cdc.json
  products/stl_3d/{stl_id}_{titre_slug}/CAHIER_DES_CHARGES.md
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, extract_json, get_previous_propositions

STL_3D_DIR = Path("products/stl_3d")
BRAIN_STL_DIR = Path("data/brain/stl")

# Decoration options per product type
DECORATION_MAP = {
    "bookmark": "border_groove|botanical_corner|minimal|celtic_knot",
    "keychain": "minimal|heart_outline|star_border|paw_print",
    "coaster": "border_groove|botanical_corner|minimal|celtic_knot",
    "door_plate": "border_groove|minimal|floral_corner|geometric",
    "plant_marker": "minimal|botanical_corner|leaf_outline|arrow_tip",
}

# Default dimensions per product type (mm)
DIMENSIONS_MAP = {
    "bookmark":    {"width": 55,  "height": 115, "thickness": 3},
    "keychain":    {"width": 45,  "height": 45,  "thickness": 4},
    "coaster":     {"width": 90,  "height": 90,  "thickness": 5},
    "door_plate":  {"width": 100, "height": 60,  "thickness": 4},
    "plant_marker":{"width": 40,  "height": 120, "thickness": 3},
}

# Rough print time estimates (minutes)
PRINT_TIME_MAP = {
    "bookmark":    35,
    "keychain":    20,
    "coaster":     60,
    "door_plate":  45,
    "plant_marker":25,
}


def _read_stl_trends() -> str:
    """Reads latest stl_trends brain data to inform the CdC."""
    latest = BRAIN_STL_DIR / "stl_trends_latest.json"
    if not latest.exists():
        return "Aucun signal STL trends disponible."
    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
        niches = data.get("niches_trending", [])[:5]
        reco = data.get("recommandation_cdc", {})
        saisonnier = data.get("opportunite_saisonniere", {})
        lines = [
            f"=== STL Trends (angle: {data.get('angle', '?')}, date: {data.get('date_analyse', '?')}) ===",
            "",
            "Top niches trending :",
        ]
        for n in niches:
            lines.append(
                f"  - {n.get('niche_name', '?')} | croissance: {n.get('croissance', '?')} "
                f"| prix moy: ${n.get('prix_moyen_usd', '?')} | {n.get('notre_avantage_potentiel', '?')}"
            )
        lines += [
            "",
            f"Recommandation CdC brain: {reco.get('type_produit', '?')} / {reco.get('niche', '?')} "
            f"— {reco.get('theme', '?')} ({reco.get('nb_variantes_suggere', '?')} variantes)",
            f"Opportunité saisonnière: {saisonnier.get('evenement', '?')} "
            f"({saisonnier.get('urgence', '?')}) → {saisonnier.get('produit_suggere', '?')}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Erreur lecture stl_trends_latest.json : {e}"


def _slugify(text: str) -> str:
    """Convert text to a safe filesystem slug."""
    text = text.lower().strip()
    text = re.sub(r"[àáâãäå]", "a", text)
    text = re.sub(r"[èéêë]", "e", text)
    text = re.sub(r"[ìíîï]", "i", text)
    text = re.sub(r"[òóôõö]", "o", text)
    text = re.sub(r"[ùúûü]", "u", text)
    text = re.sub(r"[ç]", "c", text)
    text = re.sub(r"[ñ]", "n", text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:50]


def run_stl_cdc():
    today = date.today().isoformat()

    # Read env parameters
    stl_type = os.environ.get("STL_TYPE", "bookmark").strip().lower()
    stl_niche = os.environ.get("STL_NICHE", "cottagecore").strip().lower()
    nb_variantes = int(os.environ.get("STL_NB_VARIANTES", "15"))
    stl_id = os.environ.get("STL_ID", f"stl_{today}").strip()

    # Validate type
    valid_types = {"bookmark", "keychain", "coaster", "door_plate", "plant_marker"}
    if stl_type not in valid_types:
        print(f"[STL CdC] WARNING: STL_TYPE '{stl_type}' non reconnu. Fallback: bookmark")
        stl_type = "bookmark"

    STL_3D_DIR.mkdir(parents=True, exist_ok=True)

    # Load context
    trends_context = _read_stl_trends()
    previous = get_previous_propositions("products/stl_3d", "stl_cdc")

    print(f"[STL CdC] Type: {stl_type} | Niche: {stl_niche} | Variantes: {nb_variantes} | ID: {stl_id}")
    if previous:
        print("[STL CdC] Mémoire précédente chargée — INTERDIT de répéter.")

    dims = DIMENSIONS_MAP.get(stl_type, DIMENSIONS_MAP["bookmark"])
    decoration = DECORATION_MAP.get(stl_type, "border_groove|botanical_corner|minimal|celtic_knot")
    print_time = PRINT_TIME_MAP.get(stl_type, 35)

    # Text area is inner bounding box (7mm margins each side)
    text_area = {
        "width": max(20, dims["width"] - 10),
        "height": max(15, dims["height"] - 20) if stl_type in ("bookmark", "plant_marker", "door_plate") else max(20, dims["height"] - 20),
    }

    system_prompt = f"""Tu es un expert en design produit STL 3D print et en vente sur Cults3D, Printables, Etsy Digital.
Tu génères des Cahiers des Charges ultra-complets et directement actionnables pour des fichiers STL paramétriques.

{previous}

CONTEXTE MARCHÉ :
{trends_context}

PRODUCT TYPE : {stl_type}
NICHE CIBLE : {stl_niche}
NB VARIANTES : {nb_variantes}

RÈGLES DE GÉNÉRATION :
- Chaque variante doit avoir un texte UNIQUE, accrocheur, mémorisable (pas juste "variant 1")
- Les textes doivent parler directement à la cible ({stl_niche} lovers)
- Les prix Cults3D : entre $1.50 et $4.00 selon la valeur perçue
- Les slugs de variante : snake_case, max 30 chars (ex: bloom_where_planted)
- L'élément unique du produit doit être RÉELLEMENT différenciant vs la concurrence
- La spec OpenSCAD doit être précise au mm pour pouvoir être codée directement

FORMAT RÉPONSE — JSON STRICTEMENT (aucun texte avant ou après, aucun markdown) :
{{
  "stl_id": "{stl_id}",
  "date_cdc": "{today}",
  "gate_cdc": "pending",
  "identite_commerciale": {{
    "nom_boutique": "Nom de la boutique Cults3D (mémorisable, anglais)",
    "slogan": "Tagline courte en anglais (max 8 mots)",
    "niche_principale": "{stl_niche}"
  }},
  "concept": {{
    "titre": "Nom commercial du produit en anglais",
    "type_produit": "{stl_type}",
    "niche": "{stl_niche}",
    "theme": "Thème précis (ex: cottagecore botanical, dark academia, etc.)",
    "element_unique": "Ce qui différencie ce produit de tous les STL existants",
    "pourquoi_ca_va_vendre": "Analyse en 2-3 phrases du potentiel commercial"
  }},
  "variantes": [
    {{
      "slug": "bloom_where_planted",
      "texte": "Bloom Where Planted",
      "description_courte": "For cottagecore lovers who embrace growth",
      "emoji_thumbnail": "🌸",
      "prix_cults3d_usd": 2.50
    }}
  ],
  "spec_openscad": {{
    "product_type": "{stl_type}",
    "dimensions_mm": {json.dumps(dims)},
    "text_area_mm": {json.dumps(text_area)},
    "font": "Liberation Sans:style=Bold",
    "text_size_mm": 9,
    "engrave_depth_mm": 0.8,
    "corner_radius_mm": 5,
    "decoration": "{decoration.split('|')[0]}",
    "decoration_options": "{decoration}",
    "print_settings": {{
      "layer_height_mm": 0.2,
      "infill_pct": 20,
      "supports_needed": false,
      "material": "PLA",
      "print_time_min_estimate": {print_time}
    }}
  }},
  "listing_cults3d": {{
    "titre_listing": "Titre SEO pour Cults3D (max 70 chars, inclure mots-clés)",
    "description_longue": "Description complète pour Cults3D (300-400 mots, anglais, inclure use cases, matériaux recommandés, pourquoi les gens adorent)",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10"],
    "categorie": "Catégorie Cults3D appropriée",
    "licence": "Creative Commons - Attribution - Non-Commercial - No Derivatives"
  }},
  "strategie_produit": {{
    "pilier": "creation_originale|domaine_public|imitation_amelioree",
    "justification": "Pourquoi CE pilier pour CE produit spécifique, avec preuves concrètes",
    "creation_originale": {{
      "signaux_trend": ["signal Google Trends / TikTok / Reddit observé", "..."],
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
      "produit_cible": "Titre exact du produit qui explose sur Cults3D/Etsy/Amazon",
      "pourquoi_ca_marche": "Analyse précise de son succès (volume, téléchargements, prix)",
      "ce_qui_est_mal_fait": "Ce que les acheteurs reprochent (avis 1-3 étoiles précis)",
      "notre_amelioration_concrete": "Comment on fait strictement mieux, point par point",
      "differentiation_legale": "En quoi on ne copie pas (style inspiré ≠ plagiat)"
    }}
  }},
  "potentiel_revenu": {{
    "scenario_conservateur": {{"ventes_mois_1": 10, "ventes_mois_6": 50, "revenu_annuel_estime": "$500"}},
    "scenario_optimiste": {{"ventes_mois_1": 50, "ventes_mois_6": 300, "revenu_annuel_estime": "$3000"}},
    "levier_croissance": "ce qui peut multiplier les ventes (série, bundles, niches connexes...)"
  }},
  "analyse_marche": {{
    "concurrents_cults3d": [
      {{
        "titre": "Titre d'un concurrent réel ou plausible",
        "prix": 2.00,
        "downloads": 500,
        "note": "Ce qui manque / notre angle différenciant"
      }},
      {{
        "titre": "Deuxième concurrent",
        "prix": 1.50,
        "downloads": 300,
        "note": "Point faible exploitable"
      }},
      {{
        "titre": "Troisième concurrent",
        "prix": 3.00,
        "downloads": 800,
        "note": "Leçon à retenir"
      }}
    ],
    "notre_positionnement": "En quoi notre version est supérieure (texte, niche, variantes, qualité)",
    "revenue_estime_mensuel_usd": 0
  }},
  "criteres_validation": {{
    "texte_lisible_imprime": "Tester sur imprimante avec texte le plus long",
    "dimensions_ok_slicer": "Vérifier dans Bambu Studio ou PrusaSlicer",
    "fichier_sans_erreur": "Passer STL dans Meshmixer/Manifold check",
    "photos_pro": "3 angles: face, oblique 45°, gros plan texte"
  }}
}}

ATTENTION :
- Le tableau "variantes" doit contenir EXACTEMENT {nb_variantes} entrées
- Chaque variante doit avoir un slug unique et un texte différent
- Tous les textes doivent être en rapport avec la niche "{stl_niche}"
- JSON uniquement, sans markdown ni texte autour"""

    user_prompt = f"""Crée le Cahier des Charges complet pour ce produit STL 3D print.

Type : {stl_type}
Niche : {stl_niche}
Nombre de variantes : {nb_variantes}
ID produit : {stl_id}

Ce produit sera vendu sur Cults3D comme fichier STL paramétrique (OpenSCAD).
Chaque variante = un texte différent engravé sur le même modèle.
Le prix par variante est entre $1.50 et $4.00.

STRATÉGIE PRODUIT — détermine lequel des 3 piliers s'applique et justifie avec des preuves :
1. creation_originale — si un signal Google Trends / TikTok / Reddit clair indique une tendance émergente
2. domaine_public — si une illustration ou design historique (pré-1928) peut être réutilisé concrètement
3. imitation_amelioree — si un produit concurrent explose déjà mais avec des failles exploitables (avis négatifs, qualité médiocre)

Génère {nb_variantes} variantes créatives et vendables pour la niche "{stl_niche}".
Le JSON doit être complet et directement utilisable par le script de production OpenSCAD."""

    print(f"[STL CdC] Appel LLM Gemini (génération CdC complet, {nb_variantes} variantes)...")
    response = llm_call("stl_cdc", system_prompt, user_prompt, temperature=0.85, max_tokens=12000)

    if not response:
        print("[STL CdC] Échec LLM — aucune réponse.")
        sys.exit(1)

    clean = extract_json(response)

    try:
        cdc = json.loads(clean)
    except Exception as e:
        print(f"[STL CdC] JSON invalide : {e}")
        debug_dir = STL_3D_DIR / stl_id
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_path = debug_dir / "cdc_raw_debug.txt"
        debug_path.write_text(response, encoding="utf-8")
        print(f"[STL CdC] Raw sauvegardé → {debug_path}")
        sys.exit(1)

    # Build output directory from stl_id + titre slug
    titre = cdc.get("concept", {}).get("titre", stl_id)
    titre_slug = _slugify(titre)
    dir_slug = f"{stl_id}_{titre_slug}"
    out_dir = STL_3D_DIR / dir_slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write cdc.json
    cdc_json_path = out_dir / "cdc.json"
    cdc_json_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[STL CdC] cdc.json → {cdc_json_path}")

    # Write human-readable CAHIER_DES_CHARGES.md
    md_lines = _build_md_cdc(cdc, today)
    md_path = out_dir / "CAHIER_DES_CHARGES.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[STL CdC] CAHIER_DES_CHARGES.md → {md_path}")

    # Final gate status
    concept = cdc.get("concept", {})
    identite = cdc.get("identite_commerciale", {})
    variantes = cdc.get("variantes", [])
    reco_reco = cdc.get("spec_openscad", {})

    print(f"\n[STL CdC] === RÉSUMÉ ===")
    print(f"Produit  : {titre}")
    print(f"Boutique : {identite.get('nom_boutique', '?')} — \"{identite.get('slogan', '?')}\"")
    print(f"Niche    : {concept.get('niche', '?')} | Thème: {concept.get('theme', '?')}")
    print(f"Variantes: {len(variantes)} générées")
    print(f"Spec     : {reco_reco.get('dimensions_mm', '?')}")
    print(f"Dossier  : products/stl_3d/{dir_slug}/")
    print(f"\n[STL CdC] GATE: pending — Hugo doit valider avant production.")
    print(f"[STL CdC] Pour valider : ouvrir cdc.json, changer gate_cdc='approved', puis pousser.")


def _build_md_cdc(cdc: dict, today: str) -> list[str]:
    concept = cdc.get("concept", {})
    identite = cdc.get("identite_commerciale", {})
    variantes = cdc.get("variantes", [])
    spec = cdc.get("spec_openscad", {})
    listing = cdc.get("listing_cults3d", {})
    marche = cdc.get("analyse_marche", {})
    criteres = cdc.get("criteres_validation", {})
    print_settings = spec.get("print_settings", {})
    strategie = cdc.get("strategie_produit", {})
    potentiel = cdc.get("potentiel_revenu", {})

    titre = concept.get("titre", "?")

    lines = [
        f"# CAHIER DES CHARGES STL — {titre}",
        f"**Statut** : EN ATTENTE VALIDATION HUGO",
        f"**Date** : {today}",
        f"**ID** : {cdc.get('stl_id', '?')}",
        "",
        "## GATE CdC = PENDING",
        "Pour valider : ouvrir `cdc.json` et changer `gate_cdc` de `pending` a `approved`",
        "Puis pousser le fichier — la production STL démarre automatiquement.",
        "",
        "---",
        "",
        "## 1. Identité Commerciale",
        f"**Boutique** : {identite.get('nom_boutique', '?')}",
        f"**Slogan** : _{identite.get('slogan', '?')}_",
        f"**Niche principale** : {identite.get('niche_principale', '?')}",
        "",
        "---",
        "",
        "## 2. Concept Produit",
        f"**Titre** : {titre}",
        f"**Type** : `{concept.get('type_produit', '?')}`",
        f"**Niche** : {concept.get('niche', '?')}",
        f"**Thème** : {concept.get('theme', '?')}",
        f"**Élément unique** : {concept.get('element_unique', '?')}",
        "",
        f"**Pourquoi ça va vendre** :",
        concept.get("pourquoi_ca_va_vendre", "?"),
        "",
        "---",
        "",
        "## 2b. Stratégie Produit",
        f"**Pilier** : `{strategie.get('pilier', '?')}`",
        f"**Justification** : {strategie.get('justification', '?')}",
        "",
    ]

    pilier = strategie.get("pilier", "")
    if pilier == "creation_originale":
        co = strategie.get("creation_originale", {})
        lines += [
            "**Signaux trend** : " + " | ".join(co.get("signaux_trend", [])),
            f"**Timing** : {co.get('timing_optimal', '?')}",
            f"**Risque saturation** : {co.get('risque_saturation', '?')}",
        ]
    elif pilier == "domaine_public":
        dp = strategie.get("domaine_public", {})
        lines += [
            f"**Oeuvre source** : {dp.get('oeuvre_source', '?')}",
            f"**Source** : {dp.get('source_telechargement', '?')}",
            f"**Licence** : {dp.get('licence_confirmee', '?')}",
            f"**Qualité** : {dp.get('qualite_disponible', '?')}",
            f"**Angle commercial** : {dp.get('angle_commercial', '?')}",
        ]
    elif pilier == "imitation_amelioree":
        ia = strategie.get("imitation_amelioree", {})
        lines += [
            f"**Produit cible** : {ia.get('produit_cible', '?')}",
            f"**Pourquoi ça marche** : {ia.get('pourquoi_ca_marche', '?')}",
            f"**Ce qui est mal fait** : {ia.get('ce_qui_est_mal_fait', '?')}",
            f"**Notre amélioration** : {ia.get('notre_amelioration_concrete', '?')}",
            f"**Différenciation légale** : {ia.get('differentiation_legale', '?')}",
        ]

    sc = potentiel.get("scenario_conservateur", {})
    so = potentiel.get("scenario_optimiste", {})
    lines += [
        "",
        "### Potentiel Revenu",
        f"**Conservateur** : M1={sc.get('ventes_mois_1','?')} ventes, M6={sc.get('ventes_mois_6','?')} ventes, annuel {sc.get('revenu_annuel_estime','?')}",
        f"**Optimiste** : M1={so.get('ventes_mois_1','?')} ventes, M6={so.get('ventes_mois_6','?')} ventes, annuel {so.get('revenu_annuel_estime','?')}",
        f"**Levier croissance** : {potentiel.get('levier_croissance', '?')}",
        "",
        "---",
        "",
        f"## 3. Variantes ({len(variantes)} items)",
        "",
        "| # | Slug | Texte | Description | Prix |",
        "|---|------|-------|-------------|------|",
    ]

    for i, v in enumerate(variantes, 1):
        lines.append(
            f"| {i} | `{v.get('slug', '?')}` "
            f"| {v.get('emoji_thumbnail', '')} **{v.get('texte', '?')}** "
            f"| {v.get('description_courte', '?')} "
            f"| ${v.get('prix_cults3d_usd', '?'):.2f} |"
        )

    dims = spec.get("dimensions_mm", {})
    text_area = spec.get("text_area_mm", {})

    lines += [
        "",
        "---",
        "",
        "## 4. Spec OpenSCAD",
        "",
        f"**Type produit** : `{spec.get('product_type', '?')}`",
        f"**Dimensions** : {dims.get('width', '?')} × {dims.get('height', '?')} × {dims.get('thickness', '?')} mm",
        f"**Zone texte** : {text_area.get('width', '?')} × {text_area.get('height', '?')} mm",
        f"**Police** : `{spec.get('font', '?')}`",
        f"**Taille texte** : {spec.get('text_size_mm', '?')} mm",
        f"**Profondeur gravure** : {spec.get('engrave_depth_mm', '?')} mm",
        f"**Rayon coins** : {spec.get('corner_radius_mm', '?')} mm",
        f"**Décoration** : `{spec.get('decoration', '?')}`",
        f"**Options décoration** : {spec.get('decoration_options', '?')}",
        "",
        "### Print Settings",
        f"- Layer height : {print_settings.get('layer_height_mm', '?')} mm",
        f"- Infill : {print_settings.get('infill_pct', '?')}%",
        f"- Supports : {'Oui' if print_settings.get('supports_needed') else 'Non'}",
        f"- Matériau : {print_settings.get('material', '?')}",
        f"- Temps estimé : ~{print_settings.get('print_time_min_estimate', '?')} min",
        "",
        "---",
        "",
        "## 5. Listing Cults3D",
        "",
        f"**Titre listing** : {listing.get('titre_listing', '?')}",
        f"**Catégorie** : {listing.get('categorie', '?')}",
        f"**Licence** : {listing.get('licence', '?')}",
        "",
        "**Tags** :",
        ", ".join(f"`{t}`" for t in listing.get("tags", [])),
        "",
        "**Description** :",
        listing.get("description_longue", "?"),
        "",
        "---",
        "",
        "## 6. Analyse Marché",
        "",
        f"**Positionnement** : {marche.get('notre_positionnement', '?')}",
        "",
        "**Concurrents Cults3D** :",
    ]

    for c in marche.get("concurrents_cults3d", []):
        lines.append(
            f"- **{c.get('titre', '?')}** — ${c.get('prix', '?')} "
            f"| {c.get('downloads', '?')} downloads | Note: {c.get('note', '?')}"
        )

    lines += [
        "",
        "---",
        "",
        "## 7. Critères de Validation",
        "",
        f"- [ ] {criteres.get('texte_lisible_imprime', '?')}",
        f"- [ ] {criteres.get('dimensions_ok_slicer', '?')}",
        f"- [ ] {criteres.get('fichier_sans_erreur', '?')}",
        f"- [ ] {criteres.get('photos_pro', '?')}",
        "",
        "---",
        "",
        "## Commandes de Production",
        "",
        f"```bash",
        f"# Générer les STL (après validation gate)",
        f"STL_TYPE={concept.get('type_produit', 'bookmark')} \\",
        f"STL_NICHE={concept.get('niche', 'cottagecore')} \\",
        f"STL_ID={cdc.get('stl_id', 'stl_today')} \\",
        f"python scripts/produce_stl_parametric.py",
        f"```",
        "",
        "---",
        f"*Généré automatiquement le {today} par agent_stl_cdc.py*",
    ]

    return lines


if __name__ == "__main__":
    run_stl_cdc()
