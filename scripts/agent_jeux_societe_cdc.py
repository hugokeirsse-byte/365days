#!/usr/bin/env python3
"""
CdC Jeux de Société — génère un Cahier des Charges complet pour tout type
de jeu de société imprimable (print-and-play).

Types supportés :
  card_game     — jeu de cartes (Blanc Manger Coco style, deck builder, etc.)
  board_game    — jeu de plateau (plateau + cartes + pions + règles)
  dice_game     — jeu de dés (feuilles de score, étiquettes dés custom)
  party_game    — party game (questions, défis, gages — style Jungle Speed, etc.)
  educational   — jeu éducatif (mémory, flashcards, quiz, apprentissage)
  rpg_accessory — accessoire JDR (feuilles de perso, cartes rencontres, tuiles)

Plateformes : Etsy (PDF), DriveThruRPG (RPG), Itch.io (indie), The Game Crafter (physique)

Variables d'env :
  JEU_TYPE      — card_game|board_game|dice_game|party_game|educational|rpg_accessory
  JEU_THEME     — thème libre (ex: "nurse dark humor", "medieval fantasy", "cyberpunk")
  JEU_MECANIQUE — mécanique libre (ex: "bluffing", "cooperative", "deck building")
  JEU_LANGUE    — fr|en (défaut: fr)
  JEU_ID        — identifiant unique (défaut: jeu_YYYY-MM-DD)
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, extract_json, get_previous_propositions

ROOT = Path(__file__).resolve().parent.parent
GAMES_DIR = ROOT / "products" / "jeux_societe"


# ── Spécifications par type de jeu ───────────────────────────────────────────

TYPE_SPECS = {
    "card_game": {
        "composants_typiques": "52-200 cartes (poker 2.5×3.5\"), 1 rulebook 4-8 pages",
        "plateformes": "Etsy (PDF print-and-play), The Game Crafter (impression physique)",
        "mecaniques_courantes": "questions/réponses, matching, bluffing, deck building, set collection",
        "duree_typique": "15-45 minutes",
        "complexite": "simple à medium",
        "prix_typique": "4.99-12.99 USD",
    },
    "board_game": {
        "composants_typiques": "1 plateau A3/A2, 40-150 cartes, 20-60 tokens, 2-6 pions, 1-2 dés, rulebook",
        "plateformes": "Etsy (PDF), Itch.io, The Game Crafter",
        "mecaniques_courantes": "movement, resource management, tile placement, worker placement, area control",
        "duree_typique": "30-120 minutes",
        "complexite": "medium à complex",
        "prix_typique": "8.99-24.99 USD",
    },
    "dice_game": {
        "composants_typiques": "6-12 dés custom (étiquettes imprimables), feuilles de score, règles 2 pages",
        "plateformes": "Etsy (PDF), Itch.io",
        "mecaniques_courantes": "push your luck, yahtzee-like, combinaisons, rapidité",
        "duree_typique": "10-30 minutes",
        "complexite": "simple",
        "prix_typique": "3.99-7.99 USD",
    },
    "party_game": {
        "composants_typiques": "100-300 cartes, timer optionnel, scorecards, règles simples 1 page",
        "plateformes": "Etsy (PDF), Amazon (physique via KDP ou POD)",
        "mecaniques_courantes": "acting, drawing, word association, voting, speed, humor",
        "duree_typique": "20-60 minutes",
        "complexite": "simple (accessible à tous)",
        "prix_typique": "5.99-14.99 USD",
    },
    "educational": {
        "composants_typiques": "40-120 flashcards, plateau optionnel, rulebook pédagogique",
        "plateformes": "Etsy (PDF), Teachers Pay Teachers, Amazon KDP",
        "mecaniques_courantes": "memory, quiz, matching, progression par niveaux",
        "duree_typique": "10-30 minutes",
        "complexite": "adapté à l'âge cible",
        "prix_typique": "3.99-9.99 USD",
    },
    "rpg_accessory": {
        "composants_typiques": "feuilles de personnage, cartes d'objets/sorts/rencontres, tuiles de donjon",
        "plateformes": "DriveThruRPG, Itch.io, Etsy",
        "mecaniques_courantes": "compatible D&D 5e/Pathfinder/OSR, narration collaborative",
        "duree_typique": "variable (sessions JDR)",
        "complexite": "selon le système JDR cible",
        "prix_typique": "2.99-9.99 USD (accessoire), 9.99-24.99 USD (supplément complet)",
    },
}


def run_cdc_jeux_societe():
    today = date.today().isoformat()

    jeu_type = os.environ.get("JEU_TYPE", "card_game")
    jeu_theme = os.environ.get("JEU_THEME", "dark humor office")
    jeu_mecanique = os.environ.get("JEU_MECANIQUE", "questions reponses")
    jeu_langue = os.environ.get("JEU_LANGUE", "fr")
    jeu_id = os.environ.get("JEU_ID", f"jeu_{today}")

    spec = TYPE_SPECS.get(jeu_type, TYPE_SPECS["card_game"])
    previous = get_previous_propositions("products/jeux_societe", "jeu_cdc")

    print(f"[CdC Jeu] Type: {jeu_type} | Thème: {jeu_theme} | Mécanique: {jeu_mecanique} | Langue: {jeu_langue}")

    system_prompt = f"""Tu es un expert en game design et publication de jeux de société print-and-play.
Tu crées des Cahiers des Charges ultra-complets pour des jeux vendus en PDF sur Etsy, DriveThruRPG et Itch.io.

{previous}

TYPE DE JEU : {jeu_type}
Composants typiques : {spec['composants_typiques']}
Plateformes visées : {spec['plateformes']}
Mécaniques courantes : {spec['mecaniques_courantes']}
Durée typique : {spec['duree_typique']}
Prix typique : {spec['prix_typique']}

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "jeu_id": "{jeu_id}",
  "date_cdc": "{today}",
  "gate_cdc": "pending",
  "type_jeu": "{jeu_type}",
  "langue": "{jeu_langue}",
  "concept": {{
    "titre": "...",
    "sous_titre": "...",
    "tagline": "En une phrase percutante",
    "mecanique_principale": "{jeu_mecanique}",
    "nb_joueurs": {{"min": 2, "max": 6, "optimal": 4}},
    "duree_partie_min": 30,
    "age_minimum": 12,
    "niveau_complexite": "simple|medium|complex",
    "theme": "{jeu_theme}",
    "element_unique": "Ce qui le rend INOUBLIABLE vs les 1000 autres jeux"
  }},
  "public_cible": {{
    "persona": "...",
    "tranche_age": "...",
    "contexte_jeu": "soirée famille|entre amis|team building|convention|salle de classe",
    "douleur_resolue": "...",
    "ou_ils_cherchent": "Etsy, Reddit r/boardgames, TikTok, Amazon"
  }},
  "composants": [
    {{
      "type": "cards|board|tokens|dice_labels|rulebook|score_sheet|tiles",
      "nombre": 100,
      "format": "poker_card_2.5x3.5in|A4|A3|round_25mm|d6_label|A5",
      "recto": "...",
      "verso": "...",
      "description": "..."
    }}
  ],
  "regles_jeu": {{
    "objectif_victoire": "...",
    "mise_en_place": "...",
    "deroulement_tour": "...",
    "actions_possibles": ["...", "..."],
    "fin_de_partie": "...",
    "variante_rapide": "...",
    "variante_avancee": "..."
  }},
  "contenu_cartes": {{
    "categories": [
      {{
        "nom": "...",
        "nombre": 50,
        "exemples": ["...", "...", "..."],
        "ton": "humoristique|sérieux|éducatif|provocateur"
      }}
    ],
    "style_ecriture": "...",
    "niveau_humour": "familial|adulte|dark|absurde"
  }},
  "spec_production": {{
    "outil_principal": "reportlab|pillow|reportlab+pillow",
    "fichiers_a_produire": [
      {{"nom": "cards_sheet.pdf", "description": "9 cartes par page A4 avec traits de coupe"}},
      {{"nom": "rulebook.pdf", "description": "Règles illustrées 4-8 pages"}},
      {{"nom": "box_cover.pdf", "description": "Couverture imprimable optionnelle"}}
    ],
    "resolution_dpi": 300,
    "palette_couleurs": {{"primaire": "#...", "secondaire": "#...", "fond": "#...", "texte": "#..."}},
    "style_graphique": "...",
    "bleed_mm": 3
  }},
  "listing_plateforme": {{
    "plateforme_principale": "etsy|drivethrurpg|itch_io|the_game_crafter",
    "plateforme_secondaire": "...",
    "titre_listing": "...",
    "description_courte": "...",
    "description_longue": "...",
    "tags": ["...", "...", "...", "...", "..."],
    "prix_usd": 7.99,
    "type_fichier": "PDF print-and-play",
    "licence": "Personal use only / Commercial use allowed"
  }},
  "strategie_produit": {{
    "pilier": "creation_originale|domaine_public|imitation_amelioree",
    "justification": "Pourquoi CE pilier pour CE jeu spécifique, avec preuves concrètes",
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
      "produit_cible": "Titre exact du jeu qui explose sur Etsy/Itch.io/Amazon",
      "pourquoi_ca_marche": "Analyse précise de son succès (volume, avis, prix)",
      "ce_qui_est_mal_fait": "Ce que les acheteurs reprochent (avis 1-3 étoiles précis)",
      "notre_amelioration_concrete": "Comment on fait strictement mieux, point par point",
      "differentiation_legale": "En quoi on ne copie pas (style inspiré ≠ plagiat)"
    }}
  }},
  "potentiel_revenu": {{
    "scenario_conservateur": {{"ventes_mois_1": 10, "ventes_mois_6": 50, "revenu_annuel_estime": "$500"}},
    "scenario_optimiste": {{"ventes_mois_1": 50, "ventes_mois_6": 300, "revenu_annuel_estime": "$3000"}},
    "levier_croissance": "ce qui peut multiplier les ventes (série, extensions, traductions, bundles...)"
  }},
  "cinq_concurrents": [
    {{
      "titre": "...",
      "plateforme": "...",
      "prix": 6.99,
      "downloads_approx": 500,
      "ce_qui_manque": "...",
      "notre_avantage": "..."
    }}
  ],
  "calendrier": {{
    "jours_production": 3,
    "priorite": "haute|normale|basse",
    "serie_possible": true,
    "extensions_prevues": ["Extension 1: ...", "Extension 2: ..."]
  }},
  "criteres_validation": {{
    "regles_claires": "Peut-on jouer sans vidéo explicative ?",
    "composants_imprimables": "Tous les composants tiennent sur papier A4/A3 standard ?",
    "theme_original": "La niche est-elle assez spécifique pour un public captif ?",
    "jeu_testable": "Peut-on jouer une partie test avec papier + stylo ?",
    "prix_justifie": "Le prix correspond à la valeur perçue vs concurrents ?",
    "regles_incluses": "OBLIGATOIRE — le jeu doit livrer un rulebook complet"
  }}
}}
JSON uniquement."""

    user_prompt = f"""Crée le CdC complet pour ce jeu de société print-and-play :
- Type : {jeu_type}
- Thème : {jeu_theme}
- Mécanique principale : {jeu_mecanique}
- Langue : {jeu_langue}

Le jeu doit être :
1. Entièrement produisible par script Python (ReportLab + Pillow)
2. Vendable en PDF sur {spec['plateformes']}
3. Suffisamment niche pour avoir un public captif (pas un jeu générique)
4. Livré avec des RÈGLES COMPLÈTES (cause #1 de mauvaises reviews)
5. Jouable dès l'impression, sans matériel supplémentaire coûteux

STRATÉGIE PRODUIT — détermine lequel des 3 piliers s'applique et justifie avec des preuves :
1. creation_originale — si un signal Google Trends / TikTok / Reddit / BoardGameGeek clair indique une tendance émergente non saturée
2. domaine_public — si un jeu classique, un texte ou une illustration historique (pré-1928) peut être réutilisé concrètement
3. imitation_amelioree — si un jeu concurrent explose déjà sur Etsy/Itch.io mais avec des failles exploitables (règles confuses, manque de contenu, avis négatifs précis)"""

    print("[CdC Jeu] Appel LLM...")
    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.85, max_tokens=12000)

    if not response:
        print("[CdC Jeu] Échec LLM.", file=sys.stderr)
        sys.exit(1)

    clean = extract_json(response)

    try:
        cdc = json.loads(clean)
    except Exception as e:
        print(f"[CdC Jeu] JSON invalide : {e}", file=sys.stderr)
        debug_dir = GAMES_DIR / jeu_id
        debug_dir.mkdir(parents=True, exist_ok=True)
        (debug_dir / "cdc_raw_debug.txt").write_text(response, encoding="utf-8")
        sys.exit(1)

    concept = cdc.get("concept", {})
    titre = concept.get("titre", jeu_id)
    slug = f"{jeu_id}_{titre[:30].lower().replace(' ', '_').replace('/', '_')}"
    out_dir = GAMES_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    cdc_path = out_dir / "cdc.json"
    cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[CdC Jeu] cdc.json → {cdc_path}")

    listing = cdc.get("listing_plateforme", {})
    composants = cdc.get("composants", [])
    regles = cdc.get("regles_jeu", {})
    spec_prod = cdc.get("spec_production", {})
    contenu = cdc.get("contenu_cartes", {})
    cal = cdc.get("calendrier", {})
    strategie = cdc.get("strategie_produit", {})
    potentiel = cdc.get("potentiel_revenu", {})

    md = [
        f"# CAHIER DES CHARGES — {titre}",
        f"**Type** : {jeu_type} | **Langue** : {jeu_langue}",
        f"**Statut** : EN ATTENTE VALIDATION HUGO",
        f"**Date** : {today}",
        "",
        "## 🔴 GATE CdC = PENDING",
        "Pour valider : éditer `cdc.json` → `gate_cdc: \"approved\"` → push",
        "Pour rejeter : éditer `cdc.json` → `gate_cdc: \"rejected\"` → push",
        "",
        "---",
        "",
        "## 1. Concept",
        f"**Titre** : {titre}",
        f"**Tagline** : {concept.get('tagline', '?')}",
        f"**Mécanique** : {concept.get('mecanique_principale', '?')}",
        f"**Joueurs** : {concept.get('nb_joueurs', {}).get('min', '?')}-{concept.get('nb_joueurs', {}).get('max', '?')} (optimal: {concept.get('nb_joueurs', {}).get('optimal', '?')})",
        f"**Durée** : {concept.get('duree_partie_min', '?')} min | **Âge** : {concept.get('age_minimum', '?')}+",
        f"**Complexité** : {concept.get('niveau_complexite', '?')}",
        f"**Élément unique** : {concept.get('element_unique', '?')}",
        "",
        "## 2. Stratégie Produit",
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
        "## 3. Composants",
    ]

    for comp in composants:
        md.append(f"- **{comp.get('type', '?')}** × {comp.get('nombre', '?')} | Format: {comp.get('format', '?')}")
        md.append(f"  {comp.get('description', '')}")

    md += [
        "",
        "## 4. Règles (résumé)",
        f"**Objectif** : {regles.get('objectif_victoire', '?')}",
        f"**Setup** : {regles.get('mise_en_place', '?')}",
        f"**Tour de jeu** : {regles.get('deroulement_tour', '?')}",
        f"**Fin** : {regles.get('fin_de_partie', '?')}",
        "",
        "## 5. Contenu des cartes",
    ]

    for cat in contenu.get("categories", []):
        md.append(f"### {cat.get('nom', '?')} ({cat.get('nombre', '?')} cartes) — ton: {cat.get('ton', '?')}")
        for ex in cat.get("exemples", [])[:3]:
            md.append(f"  - \"{ex}\"")

    md += [
        "",
        "## 6. Production",
        f"**Outil** : {spec_prod.get('outil_principal', '?')}",
        "**Fichiers à produire** :",
    ]

    for f in spec_prod.get("fichiers_a_produire", []):
        md.append(f"  - `{f.get('nom', '?')}` : {f.get('description', '?')}")

    couleurs = spec_prod.get("palette_couleurs", {})
    md.append(f"**Palette** : primaire {couleurs.get('primaire', '?')} | fond {couleurs.get('fond', '?')}")

    md += [
        "",
        "## 7. Listing",
        f"**Plateforme** : {listing.get('plateforme_principale', '?')} + {listing.get('plateforme_secondaire', '?')}",
        f"**Prix** : {listing.get('prix_usd', '?')} USD",
        f"**Tags** : {', '.join(listing.get('tags', []))}",
        "",
        "## 8. Checklist Validation Hugo",
        f"- [ ] {cdc.get('criteres_validation', {}).get('regles_claires', '?')}",
        f"- [ ] {cdc.get('criteres_validation', {}).get('composants_imprimables', '?')}",
        f"- [ ] {cdc.get('criteres_validation', {}).get('theme_original', '?')}",
        f"- [ ] {cdc.get('criteres_validation', {}).get('jeu_testable', '?')}",
        f"- [ ] {cdc.get('criteres_validation', {}).get('regles_incluses', '?')}",
        "",
        f"**Priorité** : {cal.get('priorite', '?')} | **Série possible** : {cal.get('serie_possible', '?')}",
    ]

    if cal.get("extensions_prevues"):
        md.append(f"**Extensions** : {' / '.join(cal['extensions_prevues'][:3])}")

    md_path = out_dir / "CAHIER_DES_CHARGES.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"[CdC Jeu] CAHIER_DES_CHARGES.md → {md_path}")

    print(f"\n[CdC Jeu] ✓ CdC généré pour '{titre}' ({jeu_type})")
    print(f"[CdC Jeu] → {out_dir}")
    print(f"[CdC Jeu] GATE: pending — Hugo doit valider avant production.")


if __name__ == "__main__":
    run_cdc_jeux_societe()
