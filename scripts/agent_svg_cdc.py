#!/usr/bin/env python3
"""
CdC SVG Packs — génère un Cahier des Charges pour un pack SVG Etsy/Cricut.

Types :
  mandala         — mandalas vectoriels paramétriques (adultes)
  floral          — motifs floraux / botaniques cuttable
  monogram        — cadres monogrammes et alphabets décoratifs
  seasonal        — thèmes saisonniers (Noël, Halloween, Pâques...)
  animal          — silhouettes animaux lifestyle/cottage/farm
  quote_frame     — cadres et banderoles pour citations
  geometric       — formes géométriques modernes / boho
  bundle_mix      — bundle multi-thèmes (best-seller Etsy)

Plateforme principale : Etsy Digital Downloads (prix 1.50-8 USD)
Machines cibles : Cricut Maker/Joy, Silhouette Cameo 4

Variables d'env :
  SVG_TYPE       — type de pack (défaut: mandala)
  SVG_NICHE      — niche/thème (ex: "boho wildflowers", "gothic halloween")
  SVG_NB_ELEMENTS — nombre de SVG dans le pack (défaut: 20)
  SVG_ID         — identifiant (défaut: svg_YYYY-MM-DD)
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, extract_json, get_previous_propositions, generate_preview_images, preview_markdown_section

ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = ROOT / "products" / "svg_packs"

TYPE_SPECS = {
    "mandala": {
        "livrable": "SVG mandala vectoriel paramétrique, symétrie parfaite, 20-40 éléments",
        "outil": "Python svgwrite (génération procédurale — 0 API image)",
        "prix_typique": "2.50-6.00 USD",
        "nb_elements_typique": "15-25 SVG",
        "machine": "Cricut & Silhouette",
    },
    "floral": {
        "livrable": "Silhouettes florales/botaniques bold, cuttable, formes nettes",
        "outil": "Pollinations Flux → Potrace (vectorisation) ou svgwrite procédural",
        "prix_typique": "2.00-5.00 USD",
        "nb_elements_typique": "15-30 SVG",
        "machine": "Cricut & Silhouette",
    },
    "monogram": {
        "livrable": "Cadres décoratifs + 26 lettres alphabet SVG, style cohérent",
        "outil": "Python svgwrite (formes géométriques + texte vectoriel)",
        "prix_typique": "3.00-7.00 USD",
        "nb_elements_typique": "26 lettres + 5-10 cadres",
        "machine": "Cricut (Design Space natif)",
    },
    "seasonal": {
        "livrable": "Pack thématique saison/fête, éléments variés + scène complète",
        "outil": "Pollinations → Potrace ou svgwrite",
        "prix_typique": "2.00-5.00 USD",
        "nb_elements_typique": "20-30 SVG",
        "machine": "Cricut & Silhouette",
    },
    "animal": {
        "livrable": "Silhouettes animaux style cottage/farm, bold, cuttable",
        "outil": "Pollinations → Potrace (silhouettes nettes)",
        "prix_typique": "2.00-4.50 USD",
        "nb_elements_typique": "15-25 SVG",
        "machine": "Cricut & Silhouette",
    },
    "quote_frame": {
        "livrable": "Cadres décoratifs + banderoles + bordures pour citations",
        "outil": "Python svgwrite (formes géométriques et courbes de Bézier)",
        "prix_typique": "2.00-5.00 USD",
        "nb_elements_typique": "15-20 cadres/frames",
        "machine": "Cricut & Silhouette",
    },
    "geometric": {
        "livrable": "Formes géométriques modernes, boho, Sacred Geometry, laser-ready",
        "outil": "Python svgwrite (formes mathématiques précises)",
        "prix_typique": "2.00-4.00 USD",
        "nb_elements_typique": "20-35 SVG",
        "machine": "Cricut & Silhouette & laser cutter",
    },
    "bundle_mix": {
        "livrable": "Bundle multi-thèmes avec README catégorisé, valeur perçue élevée",
        "outil": "Combinaison des outils ci-dessus",
        "prix_typique": "4.00-8.00 USD",
        "nb_elements_typique": "40-80 SVG",
        "machine": "Cricut & Silhouette",
    },
}


def run():
    today = date.today().isoformat()
    svg_type = os.environ.get("SVG_TYPE", "mandala")
    svg_niche = os.environ.get("SVG_NICHE", "boho wildflowers")
    nb_elements = int(os.environ.get("SVG_NB_ELEMENTS", "20"))
    svg_id = os.environ.get("SVG_ID", f"svg_{today}")

    spec = TYPE_SPECS.get(svg_type, TYPE_SPECS["mandala"])
    previous = get_previous_propositions("products/svg_packs", "svg_cdc")

    print(f"[CdC SVG] Type: {svg_type} | Niche: {svg_niche} | {nb_elements} éléments")

    system_prompt = f"""Tu es un expert en SVG packs pour Cricut/Silhouette et en vente Etsy Digital Downloads.
Tu crées des Cahiers des Charges complets pour des packs SVG vendables sur Etsy.

{previous}

TYPE DE PACK : {svg_type}
Livrable : {spec['livrable']}
Outil de production : {spec['outil']}
Prix typique Etsy : {spec['prix_typique']}
Volume typique : {spec['nb_elements_typique']}
Machine cible : {spec['machine']}

RÈGLES OBLIGATOIRES :
- Tous les SVG doivent être CUTTABLE : formes bold, pas de détails internes fins, contours connectés
- Compatibilité Cricut Design Space : pas plus de 10 000 nœuds par SVG, viewBox propre
- Compatibilité Silhouette Studio : inclure DXF si possible (même géométrie)
- Fond BLANC PUR — aucun gris, aucune ombre, aucun gradient
- Style cohérent sur tout le pack (même épaisseur de trait, même densité)
- Prix optimal Etsy : 2.50-5.00 USD (sweet spot conversion/valeur perçue)

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "id": "{svg_id}",
  "gate_cdc": "pending",
  "date": "{today}",
  "type_pack": "{svg_type}",
  "niche": "{svg_niche}",
  "concept": {{
    "type_pack": "{svg_type}",
    "niche": "{svg_niche}",
    "titre_etsy": "...",
    "sous_titre": "...",
    "style_visuel": "...",
    "machine_cible": "{spec['machine']}"
  }},
  "listing_etsy": {{
    "titre": "...",
    "prix_usd": 3.50,
    "tags": ["...", "...", "...", "...", "...", "...", "...", "...", "...", "..."],
    "description": "...",
    "categorie": "Craft Supplies & Tools > Patterns & How To > Patterns",
    "section_boutique": "SVG Cut Files"
  }},
  "elements": [
    {{
      "nom": "...",
      "description": "...",
      "style": "...",
      "outil_production": "svgwrite|pollinations_potrace",
      "complexite": "simple|moyen|complexe"
    }}
  ],
  "specs_techniques": {{
    "nb_elements": {nb_elements},
    "format_livraison": ["SVG", "PNG preview"],
    "taille_recommandee": "1000x1000 viewBox",
    "stroke_width": "...",
    "style_courbes": "...",
    "compatibilite_dxf": true
  }},
  "prompts_pollinations": [
    {{
      "element": "...",
      "prompt": "bold thick black silhouette on pure white background, NO COLOR, NO SHADING, NO GRADIENT, simple clean shapes, thick connected outlines, vector-style minimalist, perfectly cuttable for Cricut, no fine internal details, no text, high contrast pure black and white, [specific description]",
      "style_suffix": "cuttable craft SVG design"
    }}
  ],
  "checklist_upload": [
    "Vérifier que chaque SVG s'ouvre dans Cricut Design Space sans erreur",
    "Tester le cut sur papier (simulated cut) avant upload",
    "Préparer ZIP avec SVG + DXF + PNG preview 2000x2000",
    "Créer mosaïque preview 4:5 pour Etsy (premier visuel = plus important)",
    "Uploader ZIP sur Etsy → Digital Download → prix {spec['prix_typique'].split('-')[0]} USD"
  ],
  "strategie": "..."
}}
JSON uniquement."""

    user_prompt = f"""Crée un Cahier des Charges complet pour un pack SVG {svg_type} sur la niche "{svg_niche}".

Le pack doit contenir {nb_elements} éléments SVG distincts, tous cuttable machine.

Contraintes :
- Type : {svg_type} ({spec['livrable']})
- Niche : {svg_niche} (recherche les sous-thèmes qui se vendent le mieux)
- Outil disponible : {spec['outil']}
- Prix cible : {spec['prix_typique']}

Fournis :
1. Listing Etsy complet (titre optimisé + 13 tags + description markdown)
2. Liste des {nb_elements} éléments SVG avec description détaillée pour la production
3. Prompts Pollinations (si type nécessite images) ou specs svgwrite (si procédural)
4. Specs techniques (stroke width, style courbes, viewBox, DXF)
5. Stratégie différenciation vs concurrents Etsy"""

    response = llm_call("stratege", system_prompt, user_prompt, temperature=0.7, max_tokens=12000)
    if not response:
        print("[CdC SVG] Échec LLM.", file=sys.stderr)
        sys.exit(1)

    clean = extract_json(response)

    try:
        data = json.loads(clean)
    except Exception as e:
        print(f"[CdC SVG] JSON invalide: {e}", file=sys.stderr)
        sys.exit(1)

    data.setdefault("gate_cdc", "pending")
    data.setdefault("id", svg_id)

    out_dir = SVG_DIR / svg_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "cdc.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    svg_preview_prompt = (data.get("prompts_pollinations") or [{}])[0].get("prompt", "")
    previews = generate_preview_images(svg_preview_prompt, out_dir / "previews", width=512, height=512)

    elements = data.get("elements", [])
    listing = data.get("listing_etsy", {})
    concept = data.get("concept", {})
    specs = data.get("specs_techniques", {})
    checklist = data.get("checklist_upload", [])

    md_lines = [
        f"# {listing.get('titre', concept.get('titre_etsy', 'SVG Pack'))}",
        "",
        f"> **ID:** `{data.get('id', svg_id)}` | **Date:** {data.get('date', '')} | **Gate:** `{data.get('gate_cdc', 'pending')}`",
        "",
        "## Concept",
        "",
        f"**Type:** {data.get('type_pack', svg_type)}  |  **Niche:** {data.get('niche', svg_niche)}",
        f"**Style visuel:** {concept.get('style_visuel', '')}",
        f"**Machine cible:** {concept.get('machine_cible', spec.get('machine', ''))}",
        "",
        "## Listing Etsy",
        "",
        f"**Titre:** {listing.get('titre', '')}",
        f"**Prix:** ${listing.get('prix_usd', '?')} USD",
        f"**Tags:** {', '.join(listing.get('tags', []))}",
        "",
        f"> {listing.get('description', '')}",
        "",
        "## Specs techniques",
        "",
        f"**Nb éléments:** {specs.get('nb_elements', nb_elements)}",
        f"**Formats:** {', '.join(specs.get('format_livraison', ['SVG']))}",
        f"**ViewBox:** {specs.get('taille_recommandee', '')}",
        f"**Stroke width:** {specs.get('stroke_width', '')}",
        f"**Compatibilité DXF:** {'Oui' if specs.get('compatibilite_dxf') else 'Non'}",
        "",
        "## Éléments du pack",
        "",
        "| # | Nom | Description | Outil | Complexité |",
        "|---|---|---|---|---|",
    ]
    for i, el in enumerate(elements, 1):
        nom = el.get("nom", "").replace("|", "\\|")
        desc = el.get("description", "").replace("|", "\\|")
        outil = el.get("outil_production", "").replace("|", "\\|")
        complexite = el.get("complexite", "")
        md_lines.append(f"| {i} | {nom} | {desc} | {outil} | {complexite} |")

    md_lines += [
        "",
        "## Checklist upload",
        "",
    ]
    for item in checklist:
        md_lines.append(f"- {item}")

    md_lines += [
        "",
        "---",
        "",
        f"**Stratégie:** {data.get('strategie', '')}",
        "",
        "> **GATE: pending** — Hugo valide, puis production SVG.",
    ]

    md_lines += preview_markdown_section(previews)

    (out_dir / "CAHIER_DES_CHARGES.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(f"[CdC SVG] ✓ → {out_dir}/cdc.json")
    print(f"  Titre Etsy : {listing.get('titre', '')[:70]}")
    print(f"  Prix : ${listing.get('prix_usd', '?')} | {len(elements)} éléments")
    print(f"  → Valider : gate_cdc = approved pour lancer la production")


if __name__ == "__main__":
    run()
