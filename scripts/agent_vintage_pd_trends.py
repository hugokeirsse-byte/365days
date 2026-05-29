#!/usr/bin/env python3
"""
Agent Vintage Public Domain Trends — Cerveau perpétuel pour le vertical vintage_pd.

Recherche en continu :
- Collections du domaine public sous-exploitées à fort potentiel commercial
- Tendances esthétiques vintage sur Etsy, Pinterest, Redbubble
- Nouvelles combinaisons (collection × type produit) rentables
- Opportunités d'exploitation multi-produit d'une même source

Output :
  data/brain/vintage_pd/vpd_trends_YYYY-MM-DD.json
  data/brain/vintage_pd/vpd_trends_latest.json
  data/reports/rapport_vpd_YYYY-MM-DD.md

Env :
  VPD_ANGLE        override de l'angle d'analyse (optionnel)
  GEMINI_API_KEY
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, extract_json, get_previous_propositions, get_angle, get_temperature

BRAIN_DIR   = Path("data/brain/vintage_pd")
REPORTS_DIR = Path("data/reports")

VPD_ANGLES = [
    "botanical_medicinal_plants",
    "ornithological_birds",
    "entomological_insects_butterflies",
    "marine_life_ocean",
    "anatomical_scientific",
    "cartographic_antique_maps",
    "mycological_mushrooms_fungi",
    "newly_digitized_archives",
    "cross_product_bundle_strategy",
    "trending_vintage_aesthetics_2026",
]


def _get_vpd_angle() -> str:
    override = os.environ.get("VPD_ANGLE", "").strip()
    if override:
        return override
    week = date.today().isocalendar()[1]
    return VPD_ANGLES[week % len(VPD_ANGLES)]


def run_vpd_trends():
    today = date.today().isoformat()
    angle = _get_vpd_angle()

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    previous = get_previous_propositions("data/brain/vintage_pd", "vpd_trends")

    print(f"[VPD Trends] Date: {today} | Angle: {angle}")
    if previous:
        print(f"[VPD Trends] Mémoire précédente chargée — interdit de répéter.")

    system_prompt = f"""Tu es un expert en exploitation commerciale des images du domaine public.
Tu analyses le potentiel de vente des illustrations historiques libres de droits sur Etsy, Amazon KDP,
Redbubble, Printify et Merch by Amazon.

ANGLE D'ANALYSE DU JOUR : {angle}
Toute l'analyse doit explorer les opportunités liées à cet angle spécifique.

CONTEXTE MARCHÉ :
- Etsy : forte demande pour prints vintage botaniques, animaux, anatomie, cartes
  Recherches tendances : "vintage botanical print", "antique bird illustration", "Haeckel poster"
- Amazon KDP : coloring books adultes avec thématique scientifique/vintage très porteurs
  Niche sous-exploitée : livres de coloriage ÉDUCATIFS (coloriage + fiches explicatives)
- Redbubble / TeePublic : t-shirts vintage botanical à €18-25, marges 20-30%
- Printify (Etsy) : mugs, tote bags, hoodies avec illustrations vintage

COLLECTIONS DOMAINE PUBLIC CONFIRMÉES (pré-1928 ou CC0) :
- Köhler's Medizinal-Pflanzen (1887) — plantes médicinales, qualité exceptionnelle
- Redouté Les Roses (1817) + Les Liliacées — fleurs romantiques
- Audubon Birds of America (1827-1838) — oiseaux américains iconiques
- Haeckel Kunstformen der Natur (1904) — radiolaires, méduses, coraux, orchidées
- Maria Sibylla Merian Metamorphosis Insectorum (1705) — insectes + plantes tropicaux
- Gould Birds of Europe (1837) — oiseaux européens haute qualité
- Wilson American Ornithology (1808) — oiseaux nord-américains
- Donovan Natural History of British Insects (1792-1813) — entomologie britannique
- Brehm's Tierleben (1883) — mammifères et oiseaux européens
- Atlas van de Botanik — plantes ornementales haute résolution
- Gray's Anatomy (1858) — anatomie humaine iconique (très populaire en merch)
- Blaeu/Jansson Atlas Major (1660s) — cartes ornementées européennes

TYPES DE PRODUITS :
- coloring_page : page unique KDP, facile à produire, forte demande
- educational_coloring_book : livre complet KDP avec fiches (NICHE BLUE OCEAN)
- merch_tshirt : bestseller Redbubble/Merch by Amazon pour botanical/birds
- merch_mug : fort volume Etsy/Printify, marge correcte
- merch_tote : fort sur Redbubble et Etsy, audience écolo/nature
- kdp_journal_cover : notebooks/journaux KDP thématiques

STRATÉGIE MULTI-PRODUIT :
Une même illustration peut générer 4-6 produits différents.
Ex: Planche Köhler Lavande → coloring page + t-shirt + mug + tote + journal cover + educational book

{previous}

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "date_analyse": "{today}",
  "angle": "{angle}",
  "agent": "vintage_pd_trends",

  "collections_opportunites": [
    {{
      "collection": "Nom de la collection",
      "auteur_annee": "Auteur, année",
      "type_illustration": "botanical|ornithological|anatomical|...",
      "potentiel_commercial": "haute|moyenne|basse",
      "produits_recommandes": ["coloring_page", "merch_tshirt"],
      "specimens_prioritaires": ["Specimen 1", "Specimen 2", "Specimen 3"],
      "wikimedia_dispo": true,
      "raison_sous_exploitee": "Pourquoi cette collection est sous-utilisée aujourd'hui",
      "score_priorite": 8
    }}
  ],

  "combinaisons_gagnantes": [
    {{
      "collection": "...",
      "sujet": "...",
      "type_produit": "coloring_page|merch_tshirt|...",
      "titre_commercial_suggere": "...",
      "audience": "...",
      "avantage_vs_concurrence": "...",
      "difficulte_production": "facile|moyen|avance",
      "score_roi": 8
    }}
  ],

  "tendances_esthetiques": [
    {{
      "tendance": "...",
      "plateformes": ["Etsy", "Redbubble"],
      "collections_compatibles": ["Köhler", "Haeckel"],
      "croissance": "hausse|stable|baisse"
    }}
  ],

  "opportunite_educational_coloring": {{
    "concept_livre": "...",
    "collection_source": "...",
    "nombre_planches": 25,
    "audience": "...",
    "avantage_concurrentiel": "...",
    "prix_suggere": 16.99,
    "urgence": "haute|normale|basse"
  }},

  "alerte_saisonniere": {{
    "evenement": "...",
    "date_approx": "...",
    "collection_recommandee": "...",
    "produits_urgents": ["..."],
    "action_requise": "..."
  }},

  "recommandation_cdc_prioritaire": {{
    "collection": "...",
    "sujet": "...",
    "type_produit": "...",
    "justification": "...",
    "priorite": "haute|moyenne|basse"
  }}
}}
JSON uniquement, sans markdown ni texte autour."""

    user_prompt = f"""Analyse les opportunités du domaine public pour la semaine du {today}.

Angle : {angle}

Identifie :
1. Les 5 collections les plus prometteuses à exploiter MAINTENANT pour cet angle
2. Les 5 meilleures combinaisons (collection × produit) avec le meilleur ROI
3. L'opportunité educational coloring book la plus forte
4. Une alerte saisonnière si pertinente

Priorité aux collections disponibles sur Wikimedia Commons avec images haute résolution.
Réponds avec le JSON complet. Aucun texte en dehors du JSON."""

    temperature = get_temperature("prospecteur")
    print(f"[VPD Trends] Appel LLM (temperature={temperature:.2f})...")
    response = llm_call("stratege", system_prompt, user_prompt,
                        temperature=temperature, max_tokens=6000)

    if not response:
        print("[VPD Trends] Échec LLM.")
        sys.exit(1)

    clean = extract_json(response)

    try:
        data = json.loads(clean)
    except Exception as e:
        print(f"[VPD Trends] JSON invalide : {e}")
        debug_path = BRAIN_DIR / f"vpd_trends_debug_{today}.txt"
        debug_path.write_text(response, encoding="utf-8")
        sys.exit(1)

    dated_path = BRAIN_DIR / f"vpd_trends_{today}.json"
    dated_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[VPD Trends] JSON → {dated_path}")

    latest_path = BRAIN_DIR / "vpd_trends_latest.json"
    latest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[VPD Trends] Latest → {latest_path}")

    md_lines = _build_md_report(data, today, angle)
    md_path = REPORTS_DIR / f"rapport_vpd_{today}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[VPD Trends] Rapport → {md_path}")

    collections = data.get("collections_opportunites", [])
    combinaisons = data.get("combinaisons_gagnantes", [])
    reco = data.get("recommandation_cdc_prioritaire", {})
    educ = data.get("opportunite_educational_coloring", {})

    print(f"\n[VPD Trends] === RÉSUMÉ ===")
    print(f"Angle    : {angle}")
    top_col = collections[0] if collections else {}
    print(f"Top coll : {top_col.get('collection','?')} (score {top_col.get('score_priorite','?')}/10)")
    top_combo = combinaisons[0] if combinaisons else {}
    print(f"Top combo: {top_combo.get('collection','?')} × {top_combo.get('type_produit','?')} — {top_combo.get('titre_commercial_suggere','?')[:50]}")
    print(f"Reco CdC : {reco.get('collection','?')} / {reco.get('sujet','?')} → {reco.get('type_produit','?')}")
    print(f"Éducatif : {educ.get('concept_livre','?')[:60]} (urgence: {educ.get('urgence','?')})")


def _build_md_report(data: dict, today: str, angle: str) -> list[str]:
    collections  = data.get("collections_opportunites", [])
    combinaisons = data.get("combinaisons_gagnantes", [])
    tendances    = data.get("tendances_esthetiques", [])
    educ         = data.get("opportunite_educational_coloring", {})
    alerte       = data.get("alerte_saisonniere", {})
    reco         = data.get("recommandation_cdc_prioritaire", {})

    lines = [
        f"# Rapport Vintage Public Domain Trends — {today}",
        f"**Angle** : {angle}",
        f"**Agent** : vintage_pd_trends | **Sources** : Wikimedia Commons, Etsy, Amazon KDP, Redbubble",
        "",
        "---",
        "",
        "## 1. Collections Opportunités",
        "",
        "| Collection | Type | Potentiel | Produits | Score |",
        "|---|---|---|---|---|",
    ]
    for c in collections:
        lines.append(
            f"| {c.get('collection','')} ({c.get('auteur_annee','')}) "
            f"| {c.get('type_illustration','')} "
            f"| {c.get('potentiel_commercial','')} "
            f"| {', '.join(c.get('produits_recommandes',[]))} "
            f"| {c.get('score_priorite','')}/10 |"
        )
    lines.append("")
    for c in collections:
        lines += [
            f"### {c.get('collection','')}",
            f"- **Spécimens prioritaires** : {', '.join(c.get('specimens_prioritaires',[]))}",
            f"- **Wikimedia dispo** : {'✓' if c.get('wikimedia_dispo') else '✗'}",
            f"- **Pourquoi sous-exploitée** : {c.get('raison_sous_exploitee','')}",
            "",
        ]

    lines += [
        "---",
        "",
        "## 2. Combinaisons Gagnantes",
        "",
    ]
    for i, combo in enumerate(combinaisons, 1):
        lines += [
            f"### #{i} — {combo.get('collection','')} × {combo.get('type_produit','')}",
            f"**Titre suggéré** : {combo.get('titre_commercial_suggere','')}",
            f"**Sujet** : {combo.get('sujet','')} | **Audience** : {combo.get('audience','')}",
            f"**Avantage** : {combo.get('avantage_vs_concurrence','')}",
            f"**Difficulté** : {combo.get('difficulte_production','')} | **ROI score** : {combo.get('score_roi','')}/10",
            "",
        ]

    lines += [
        "---",
        "",
        "## 3. Opportunité Educational Coloring Book",
        "",
        f"**Concept** : {educ.get('concept_livre','')}",
        f"**Source** : {educ.get('collection_source','')} | **Planches** : {educ.get('nombre_planches','')}",
        f"**Audience** : {educ.get('audience','')}",
        f"**Avantage** : {educ.get('avantage_concurrentiel','')}",
        f"**Prix suggéré** : ${educ.get('prix_suggere','')} | **Urgence** : {educ.get('urgence','')}",
        "",
        "---",
        "",
        "## 4. Tendances Esthétiques",
        "",
    ]
    for t in tendances:
        lines += [
            f"- **{t.get('tendance','')}** ({t.get('croissance','')}) — "
            f"plateformes: {', '.join(t.get('plateformes',[]))} — "
            f"compatible: {', '.join(t.get('collections_compatibles',[]))}",
        ]

    lines += [
        "",
        "---",
        "",
        "## 5. Alerte Saisonnière",
        "",
        f"**Événement** : {alerte.get('evenement','')}",
        f"**Date** : {alerte.get('date_approx','')}",
        f"**Collection recommandée** : {alerte.get('collection_recommandee','')}",
        f"**Produits urgents** : {', '.join(alerte.get('produits_urgents',[]))}",
        f"**Action** : {alerte.get('action_requise','')}",
        "",
        "---",
        "",
        "## 6. Recommandation CdC Prioritaire",
        "",
        f"**Collection** : {reco.get('collection','')} | **Sujet** : {reco.get('sujet','')}",
        f"**Type produit** : {reco.get('type_produit','')} | **Priorité** : {reco.get('priorite','')}",
        f"**Justification** : {reco.get('justification','')}",
        "",
        "---",
        "",
        f"*Rapport généré le {today} — Agent: vintage_pd_trends*",
    ]
    return lines


if __name__ == "__main__":
    run_vpd_trends()
