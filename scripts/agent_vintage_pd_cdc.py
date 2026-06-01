#!/usr/bin/env python3
"""
Agent Vintage Public Domain CdC — Génère un Cahier des Charges pour un produit
dérivé d'une illustration du domaine public (Köhler, Audubon, Haeckel, etc.).

Un CdC = une source × un type de produit.
Types supportés : coloring_page, merch_tshirt, merch_mug, merch_tote,
                  kdp_journal_cover, educational_coloring_book.

L'avantage clé : l'image SOURCE existe déjà, aucune génération IA requise.
Le pipeline de production = acquisition Wikimedia + traitement Pillow/OpenCV.

Env vars :
  VPD_COLLECTION   — collection source (ex: kohler_medizinal)
  VPD_SUJET        — sujet/spécimen  (ex: lavandula_officinalis)
  VPD_PRODUCT_TYPE — type de produit cible (ex: coloring_page)
  VPD_ID           — défaut: vpd_YYYY-MM-DD
  GEMINI_API_KEY

Output :
  products/vintage_pd/{vpd_id}_{slug}/cdc.json
  products/vintage_pd/{vpd_id}_{slug}/CAHIER_DES_CHARGES.md
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, extract_json, get_previous_propositions

VPD_DIR = Path("products/vintage_pd")


def _slugify(text: str, max_len: int = 45) -> str:
    text = text.lower().strip()
    for src, dst in [("é","e"),("è","e"),("ê","e"),("ë","e"),("à","a"),("â","a"),
                     ("ü","u"),("ù","u"),("û","u"),("î","i"),("ï","i"),("ô","o"),("ç","c")]:
        text = text.replace(src, dst)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")[:max_len]


def run_cdc_vintage_pd():
    today = date.today().isoformat()

    collection   = os.environ.get("VPD_COLLECTION",   "kohler_medizinal")
    sujet        = os.environ.get("VPD_SUJET",        "lavandula_officinalis")
    product_type = os.environ.get("VPD_PRODUCT_TYPE", "coloring_page")
    vpd_id       = os.environ.get("VPD_ID",           f"vpd_{today}")

    previous = get_previous_propositions("products/vintage_pd", "vpd_cdc")

    print(f"[CdC VPD] Collection: {collection} | Sujet: {sujet} | Produit: {product_type}")

    # ------------------------------------------------------------------ #
    # Description de chaque type de produit pour guider le LLM
    # ------------------------------------------------------------------ #
    product_type_hints = {
        "coloring_page": (
            "Page de coloriage KDP — l'image source est convertie en lineart pur (Canny + seuillage). "
            "Format 8.5×11 pouces, 300 DPI, niveaux de gris. Texte décoratif optionnel en bas (nom latin, date)."
        ),
        "merch_tshirt": (
            "Design t-shirt (Printify / Merch by Amazon) — l'image source est nettoyée, fond transparent, "
            "éventuellement colorisée ou traitée effet risographie. Texte stylisé requis (nom, devise, date). "
            "Format PNG 4500×5400px fond transparent."
        ),
        "merch_mug": (
            "Design mug (Printify) — bande horizontale 3300×2550px ou design full-wrap. "
            "Image centrale + texte élégant autour. Fond uni ou texture légère acceptable."
        ),
        "merch_tote": (
            "Design tote bag (Printify / Redbubble) — format carré PNG 4096×4096px fond blanc ou transparent. "
            "Composition centrée, texte décoratif en bas, style poster vintage."
        ),
        "kdp_journal_cover": (
            "Couverture journal/carnet KDP — image ornementée en couverture, titre du journal "
            "(ex: 'My Botanical Journal'), format 6×9 pouces, 300 DPI. "
            "Typographie vintage soignée, palette harmonieuse avec l'illustration."
        ),
        "educational_coloring_book": (
            "Livre de coloriage ÉDUCATIF — double page spread : gauche = lineart à colorier, "
            "droite = fiche éducative (nom scientifique, famille, usages, anecdote historique). "
            "Format A4, 25 planches, KDP. Idéal pour adultes passionnés de botanique/nature."
        ),
    }
    product_hint = product_type_hints.get(product_type, product_type)

    # ------------------------------------------------------------------ #
    # Champs supplémentaires selon le type
    # ------------------------------------------------------------------ #
    extra_fields = ""
    if product_type == "educational_coloring_book":
        extra_fields = """
  "contenu_educatif": {
    "titre_livre": "Titre commercial du livre éducatif",
    "sous_titre": "Sous-titre descriptif",
    "nb_planches": 25,
    "format_pdf": "A4 portrait 300DPI",
    "structure_page": "Page gauche lineart + Page droite fiche éducative",
    "exemple_fiche": {
      "titre_planche": "Nom commun de l'illustration",
      "nom_scientifique": "Genre espèce auteur",
      "famille_botanique": "Famille",
      "description_courte": "2-3 phrases accessibles grand public",
      "usage_historique_medicinal": "Usage traditionnel ou historique précis",
      "anecdote": "Fait surprenant ou historique mémorable",
      "zone_origine": "Région géographique d'origine"
    }
  },"""
    else:
        extra_fields = '\n  "contenu_educatif": null,'

    system_prompt = f"""Tu es un expert en produits dérivés d'illustrations du domaine public.
Tu génères des Cahiers des Charges complets pour des produits commerciaux basés sur des images historiques libres de droits.

CONTEXTE DU PROJET :
- Source : collection "{collection}", sujet "{sujet}"
- Produit cible : {product_type}
- Description du type : {product_hint}
- AVANTAGE CLÉ : l'image existe déjà sur Wikimedia Commons — pas de génération IA.
  Le pipeline = téléchargement Wikimedia + traitement Python (Pillow, OpenCV).
- Légalité : seules les œuvres du domaine public CONFIRMÉES (pré-1928 USA ou CC0).

{previous}

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "vpd_id": "{vpd_id}",
  "date_cdc": "{today}",
  "gate_cdc": "pending",

  "source": {{
    "collection": "{collection}",
    "auteur_original": "Nom de l'auteur/artiste original",
    "annee_publication": 1887,
    "sujet": "{sujet}",
    "sujet_affiche": "Nom commun + nom scientifique lisibles",
    "type_illustration": "botanical|ornithological|anatomical|entomological|cartographic|marine|other",
    "statut_domaine_public": "pre_1928_us_confirmed|cc0|public_domain_all_countries",
    "wikimedia_commons_path": "Chemin relatif sur commons.wikimedia.org (ex: wiki/File:Köhler_Lavandula.jpg)",
    "qualite_estimee": "haute_resolution|moyenne|basse",
    "note_legale": "Explication précise du statut juridique (date publication, pays, etc.)"
  }},

  "produit": {{
    "type": "{product_type}",
    "titre_commercial": "Titre accrocheur en anglais",
    "plateforme_cible": "KDP|Printify|Etsy|Redbubble|Merch by Amazon",
    "format_fichier_final": "Description précise du fichier de sortie attendu",
    "prix_estime_usd": 9.99
  }},

  "traitement_pipeline": {{
    "etape_1_acquisition": "Télécharger image HD depuis Wikimedia Commons — URL ou chemin précis",
    "etape_2_preparation": "Recadrage, redressement, suppression d'artefacts de scan",
    "etape_3_traitement": "Traitement spécifique au type de produit (lineart/colorisation/fond transparent/etc.)",
    "etape_4_finition": "Mise en page, marges, DPI, format final",
    "outils_python": ["Pillow (PIL)", "OpenCV cv2", "fpdf2 si PDF"],
    "difficulte": "facile|moyen|avance",
    "script_hint": "Description du script Python de production en 2-3 lignes"
  }},

  "texte_decoratif": {{
    "actif": true,
    "texte_principal": "Texte principal (nom latin ou titre)",
    "texte_secondaire": "Texte secondaire (date, collection, devise)",
    "style_typographie": "serif_victorien|script_elegant|sans_moderne|gravure_vintage",
    "font_google": "Nom de la Google Font recommandée (gratuite)",
    "placement": "bas_centre|haut_centre|bas_droite|superpose_transparent",
    "couleur_texte_hex": "#2D4A2D",
    "note_composition": "Instructions précises pour le script de composition"
  }},{extra_fields}

  "marche": {{
    "audience_cible": "Description précise du persona acheteur",
    "communautes_cibles": ["r/botany", "r/herbalism", "autres communautés pertinentes"],
    "mots_cles_etsy": ["kw1", "kw2", "kw3", "kw4", "kw5"],
    "mots_cles_amazon_kdp": ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6", "kw7"],
    "avantage_concurrentiel": "Ce qui nous différencie des produits similaires sur le marché",
    "saturation_estimee": "faible|moderee|elevee",
    "volume_marche_estime": "Estimation volume de recherche mensuel"
  }},

  "listing": {{
    "titre_principal": "Titre optimisé SEO pour la plateforme cible (max 200 chars)",
    "sous_titre": "Sous-titre avec mots-clés secondaires",
    "description_commerciale": "Description complète 400-600 mots, ton adapté à l'audience",
    "mots_cles": ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6", "kw7"],
    "categories": ["Catégorie 1", "Catégorie 2"],
    "prix_usd": 9.99
  }},

  "strategie_produit": {{
    "pilier": "domaine_public",
    "justification": "Ce produit est TOUJOURS domaine_public — l'illustration source est une oeuvre historique pré-1928 confirmée",
    "domaine_public": {{
      "oeuvre_source": "Titre + auteur + année de publication exacte",
      "source_telechargement": "URL Wikimedia Commons ou archive.org précise et vérifiable",
      "licence_confirmee": "CC0 / domaine public US + pays cibles confirmé (préciser la date de publication)",
      "qualite_disponible": "300 DPI / vectorisable / restauration nécessaire — état précis de l'image",
      "angle_commercial": "Comment on monétise cette oeuvre PD concrètement pour ce type de produit"
    }}
  }},
  "potentiel_revenu": {{
    "scenario_conservateur": {{"ventes_mois_1": 10, "ventes_mois_6": 50, "revenu_annuel_estime": "$500"}},
    "scenario_optimiste": {{"ventes_mois_1": 50, "ventes_mois_6": 300, "revenu_annuel_estime": "$3000"}},
    "levier_croissance": "ce qui peut multiplier les ventes (collection complète, multi-produits même illustration, bundle saisonnier...)"
  }},
  "checklist_validation": {{
    "verifier_source": "Confirmer l'URL Wikimedia Commons et télécharger un aperçu",
    "verifier_legal": "Vérifier la date de publication — doit être < 1928 pour domaine public USA",
    "verifier_qualite_image": "Résolution suffisante ? (min 300 DPI natif ou upscalable sans artefacts)",
    "verifier_traitement": "Tester le pipeline sur l'image : lineart/fond transparent correct ?",
    "verifier_marche": "Chercher '{sujet}' + '{product_type}' sur Etsy/Amazon — niveau de concurrence ?"
  }}
}}
JSON uniquement, sans markdown ni balises. Tous les champs avec du contenu concret, aucun placeholder vide."""

    user_prompt = f"""Génère le Cahier des Charges pour ce projet domaine public :

Collection : {collection}
Sujet/spécimen : {sujet}
Type de produit : {product_type}
Description produit : {product_hint}

PRIORITÉS :
1. La source Wikimedia Commons doit être RÉELLE et vérifiable (pas inventée).
2. Le statut domaine public doit être CONFIRMÉ avec justification légale précise.
3. Le pipeline de traitement doit être ACTIONNABLE avec Pillow + OpenCV en Python.
4. Le listing commercial doit être VENDEUR pour l'audience cible.

STRATÉGIE PRODUIT : Ce projet est TOUJOURS domaine_public.
- Confirme l'oeuvre source avec titre + auteur + année de publication exacte
- Donne l'URL Wikimedia Commons précise et vérifiable
- Explique comment on monétise concrètement cette illustration pour le type "{product_type}"
- Estime le potentiel de revenus en scénario conservateur et optimiste

Pour le texte décoratif : propose une composition typographique précise
(font, placement, couleur) qui valorise l'illustration sans la surcharger."""

    print("[CdC VPD] Appel LLM (génération CdC complet)...")
    response = llm_call("cdc_generator", system_prompt, user_prompt,
                        temperature=0.80, max_tokens=10000)

    if not response:
        print("[CdC VPD] Échec LLM.")
        sys.exit(1)

    clean = extract_json(response)

    try:
        cdc = json.loads(clean)
    except Exception as e:
        print(f"[CdC VPD] JSON invalide : {e}")
        debug_dir = VPD_DIR / vpd_id
        debug_dir.mkdir(parents=True, exist_ok=True)
        (debug_dir / "cdc_raw_debug.txt").write_text(response, encoding="utf-8")
        print(f"[CdC VPD] Raw sauvegardé → {debug_dir}/cdc_raw_debug.txt")
        sys.exit(1)

    cdc.setdefault("gate_cdc", "pending")

    # Build output directory
    source = cdc.get("source", {})
    produit = cdc.get("produit", {})
    titre = produit.get("titre_commercial", sujet)
    titre_slug = _slugify(titre)
    out_dir = VPD_DIR / f"{vpd_id}_{titre_slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    cdc_json_path = out_dir / "cdc.json"
    cdc_json_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[CdC VPD] cdc.json → {cdc_json_path}")

    # Build markdown CdC
    _write_markdown(cdc, out_dir, today)

    # Summary
    marche = cdc.get("marche", {})
    texte = cdc.get("texte_decoratif", {}) or {}
    traitement = cdc.get("traitement_pipeline", {})
    print(f"\n[CdC VPD] === RÉSUMÉ ===")
    print(f"Titre    : {titre}")
    print(f"Source   : {source.get('auteur_original','?')} {source.get('annee_publication','?')} — {source.get('type_illustration','?')}")
    print(f"Légal    : {source.get('statut_domaine_public','?')}")
    print(f"Pipeline : {traitement.get('difficulte','?')} — {traitement.get('script_hint','?')[:80]}")
    print(f"Marché   : saturation {marche.get('saturation_estimee','?')} | {marche.get('volume_marche_estime','?')}")
    print(f"Texte    : {texte.get('texte_principal','—')} / {texte.get('font_google','—')}")
    print(f"Dossier  : products/vintage_pd/{out_dir.name}/")
    print(f"\n[CdC VPD] GATE: pending — Hugo valide avant production.")
    print(f"  Ouvrir cdc.json → gate_cdc = 'approved' → push → production démarre.")


def _write_markdown(cdc: dict, out_dir: Path, today: str) -> None:
    source  = cdc.get("source", {})
    produit = cdc.get("produit", {})
    traitement = cdc.get("traitement_pipeline", {})
    texte   = cdc.get("texte_decoratif", {}) or {}
    educatif = cdc.get("contenu_educatif") or {}
    marche  = cdc.get("marche", {})
    listing = cdc.get("listing", {})
    checklist = cdc.get("checklist_validation", {})
    strategie = cdc.get("strategie_produit", {})
    potentiel = cdc.get("potentiel_revenu", {})

    titre = produit.get("titre_commercial", "Vintage PD Project")
    prod_type = produit.get("type", "?")

    lines = [
        f"# CAHIER DES CHARGES — {titre}",
        "",
        f"> **ID:** `{cdc.get('vpd_id','')}` | **Date:** {today} | **Gate:** `{cdc.get('gate_cdc','pending')}`",
        f"> **Collection:** {source.get('collection','')} | **Sujet:** {source.get('sujet_affiche', source.get('sujet',''))}",
        f"> **Produit:** {prod_type} → **Plateforme:** {produit.get('plateforme_cible','')}",
        "",
        "## ✅ GATE CdC = PENDING",
        "",
        "Avant toute production :",
        "1. Vérifier le lien Wikimedia Commons ci-dessous (télécharger un aperçu)",
        "2. Confirmer le statut domaine public (note légale)",
        "3. Tester le pipeline de traitement sur 1 image",
        "4. Si OK : ouvrir `cdc.json`, changer `gate_cdc` → `approved`, pousser",
        "",
        "---",
        "",
        "## 1. Source Domaine Public",
        "",
        f"| Champ | Valeur |",
        f"|---|---|",
        f"| Collection | {source.get('collection','')} |",
        f"| Auteur original | {source.get('auteur_original','')} |",
        f"| Année publication | {source.get('annee_publication','')} |",
        f"| Sujet | {source.get('sujet_affiche', source.get('sujet',''))} |",
        f"| Type illustration | {source.get('type_illustration','')} |",
        f"| Statut légal | **{source.get('statut_domaine_public','')}** |",
        f"| Qualité estimée | {source.get('qualite_estimee','')} |",
        "",
        f"**Note légale** : {source.get('note_legale','')}",
        "",
        f"**Wikimedia Commons** : `{source.get('wikimedia_commons_path','À vérifier')}`",
        "",
        "---",
        "",
        "## 2. Produit Cible",
        "",
        f"**Type** : {prod_type}",
        f"**Titre commercial** : {titre}",
        f"**Plateforme** : {produit.get('plateforme_cible','')}",
        f"**Format fichier final** : {produit.get('format_fichier_final','')}",
        f"**Prix estimé** : ${produit.get('prix_estime_usd',9.99)}",
        "",
        "---",
        "",
        "## 3. Pipeline de Traitement",
        "",
        f"**Difficulté** : {traitement.get('difficulte','')}",
        f"**Outils Python** : {', '.join(traitement.get('outils_python',[]))}",
        "",
        f"1. **Acquisition** : {traitement.get('etape_1_acquisition','')}",
        f"2. **Préparation** : {traitement.get('etape_2_preparation','')}",
        f"3. **Traitement** : {traitement.get('etape_3_traitement','')}",
        f"4. **Finition** : {traitement.get('etape_4_finition','')}",
        "",
        f"**Script hint** : {traitement.get('script_hint','')}",
        "",
        "---",
        "",
        "## 4. Texte Décoratif",
        "",
    ]

    if texte.get("actif"):
        lines += [
            f"**Principal** : `{texte.get('texte_principal','')}` — *{texte.get('style_typographie','')}*",
            f"**Secondaire** : `{texte.get('texte_secondaire','')}`",
            f"**Font Google** : {texte.get('font_google','')}",
            f"**Placement** : {texte.get('placement','')}",
            f"**Couleur** : `{texte.get('couleur_texte_hex','')}` — {texte.get('note_composition','')}",
        ]
    else:
        lines.append("*(Pas de texte décoratif pour ce type de produit)*")

    if educatif:
        lines += [
            "",
            "---",
            "",
            "## 4b. Contenu Éducatif",
            "",
            f"**Titre livre** : {educatif.get('titre_livre','')}",
            f"**Sous-titre** : {educatif.get('sous_titre','')}",
            f"**Planches** : {educatif.get('nb_planches',25)} | **Format** : {educatif.get('format_pdf','')}",
            f"**Structure** : {educatif.get('structure_page','')}",
            "",
            "### Exemple de fiche éducative",
        ]
        ef = educatif.get("exemple_fiche", {})
        for k, v in ef.items():
            lines.append(f"- **{k}** : {v}")

    lines += [
        "",
        "---",
        "",
        "## 4b. Stratégie Produit",
        "",
        f"**Pilier** : `domaine_public` (toujours pour les produits Vintage PD)",
        f"**Justification** : {strategie.get('justification', '?')}",
        "",
    ]

    dp = strategie.get("domaine_public", {})
    sc = potentiel.get("scenario_conservateur", {})
    so = potentiel.get("scenario_optimiste", {})
    lines += [
        f"**Oeuvre source** : {dp.get('oeuvre_source', source.get('auteur_original', '?'))}",
        f"**Source téléchargement** : {dp.get('source_telechargement', source.get('wikimedia_commons_path', '?'))}",
        f"**Licence confirmée** : {dp.get('licence_confirmee', source.get('statut_domaine_public', '?'))}",
        f"**Qualité disponible** : {dp.get('qualite_disponible', source.get('qualite_estimee', '?'))}",
        f"**Angle commercial** : {dp.get('angle_commercial', '?')}",
        "",
        "### Potentiel Revenu",
        f"**Conservateur** : M1={sc.get('ventes_mois_1','?')} ventes, M6={sc.get('ventes_mois_6','?')} ventes, annuel {sc.get('revenu_annuel_estime','?')}",
        f"**Optimiste** : M1={so.get('ventes_mois_1','?')} ventes, M6={so.get('ventes_mois_6','?')} ventes, annuel {so.get('revenu_annuel_estime','?')}",
        f"**Levier croissance** : {potentiel.get('levier_croissance', '?')}",
        "",
        "---",
        "",
        "## 5. Marché",
        "",
        f"**Audience** : {marche.get('audience_cible','')}",
        f"**Communautés** : {', '.join(marche.get('communautes_cibles',[]))}",
        f"**Saturation** : {marche.get('saturation_estimee','')} | **Volume** : {marche.get('volume_marche_estime','')}",
        "",
        f"**Avantage concurrentiel** : {marche.get('avantage_concurrentiel','')}",
        "",
        f"**Mots-clés Etsy** : {', '.join(marche.get('mots_cles_etsy',[]))}",
        f"**Mots-clés Amazon/KDP** : {', '.join(marche.get('mots_cles_amazon_kdp',[]))}",
        "",
        "---",
        "",
        "## 6. Listing Commercial",
        "",
        f"**Titre** : {listing.get('titre_principal','')}",
        f"**Sous-titre** : {listing.get('sous_titre','')}",
        f"**Prix** : ${listing.get('prix_usd',9.99)}",
        "",
        "**Description** :",
        "",
        listing.get("description_commerciale",""),
        "",
        f"**Mots-clés** : {', '.join(listing.get('mots_cles',[]))}",
        f"**Catégories** : {', '.join(listing.get('categories',[]))}",
        "",
        "---",
        "",
        "## 7. Checklist Validation",
        "",
        f"- [ ] {checklist.get('verifier_source','')}",
        f"- [ ] {checklist.get('verifier_legal','')}",
        f"- [ ] {checklist.get('verifier_qualite_image','')}",
        f"- [ ] {checklist.get('verifier_traitement','')}",
        f"- [ ] {checklist.get('verifier_marche','')}",
        "",
        "---",
        "",
        f"*CdC généré le {today} — GATE: pending*",
    ]

    md_path = out_dir / "CAHIER_DES_CHARGES.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[CdC VPD] CAHIER_DES_CHARGES.md → {md_path}")


if __name__ == "__main__":
    run_cdc_vintage_pd()
