#!/usr/bin/env python3
"""
CdC Low-Content — Generates complete spec for KDP low-content books.
(Journals, planners, trackers, activity books — built with ReportLab, no image API needed)
gate_cdc=pending until Hugo approves.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions

LOWCONTENT_DIR = Path("products/lowcontent_kdp")


def run_cdc_lowcontent():
    today = date.today().isoformat()

    lc_type = os.environ.get("LC_TYPE", "journal")
    lc_theme = os.environ.get("LC_THEME", "mindfulness")
    lc_audience = os.environ.get("LC_AUDIENCE", "adults")
    lc_id = os.environ.get("LC_ID", f"lc_{today}")

    previous = get_previous_propositions("products/lowcontent_kdp", "cdc_lowcontent")

    print(f"[CdC Low-Content] Type: {lc_type} | Thème: {lc_theme} | Audience: {lc_audience}")

    system_prompt = f"""Tu es un expert KDP spécialisé dans les low-content books (journaux, planners, trackers).
Tu génères des Cahiers des Charges ultra-complets pour des livres construits avec ReportLab (Python).

{previous}

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "lc_id": "{lc_id}",
  "date_cdc": "{today}",
  "gate_cdc": "pending",
  "identite_commerciale": {{
    "nom_de_plume": "Prénom Nom inventé",
    "bio_auteur": "100 mots à la 3e personne",
    "marque_serie": "Nom de la collection (ex: 'Moonlight Press')"
  }},
  "concept": {{
    "titre": "...",
    "sous_titre": "...",
    "type": "{lc_type}",
    "theme": "{lc_theme}",
    "langue": "en",
    "nombre_pages": 120,
    "format": "6x9 pouces",
    "element_unique": "Ce qui rend CE journal différent de tous les autres"
  }},
  "public_cible": {{
    "persona": "...",
    "tranche_age": "{lc_audience}",
    "douleur_resolue": "...",
    "ou_ils_cherchent": "Amazon, Pinterest, Instagram"
  }},
  "cinq_concurrents": [
    {{
      "titre": "...",
      "auteur": "...",
      "prix_usd": 8.99,
      "note": 4.3,
      "nb_avis": 500,
      "ce_qui_manque": "...",
      "notre_avantage": "..."
    }}
  ],
  "structure_pages": {{
    "page_titre": {{"description": "..."}},
    "pages_intro": {{"nb_pages": 4, "contenu": "..."}},
    "pages_principales": {{
      "nb_pages": 104,
      "layout_description": "Description précise du layout ReportLab",
      "elements_par_page": ["...", "..."],
      "colonnes": 1,
      "lignes_par_page": 0,
      "espacement_mm": 8
    }},
    "pages_bonus": {{"nb_pages": 8, "contenu": "..."}},
    "page_fin": {{"description": "..."}}
  }},
  "spec_reportlab": {{
    "police_titre": "...",
    "police_corps": "...",
    "couleur_primaire_hex": "#...",
    "couleur_accent_hex": "#...",
    "style_bordure": "...",
    "elements_decoratifs": ["..."],
    "header_footer": "..."
  }},
  "description_amazon": {{
    "accroche": "...",
    "corps": "...",
    "bullets": ["...", "...", "..."],
    "appel_action": "..."
  }},
  "mots_cles_kdp": ["...", "...", "...", "...", "...", "...", "..."],
  "categories_kdp": ["...", "..."],
  "pricing": {{
    "prix_paperback_usd": 8.99,
    "royaltie_estimee_usd": 3.45,
    "bsps_cible": 50000
  }},
  "calendrier": {{
    "jours_production": 2,
    "date_publication_cible": "...",
    "serie_possible": true,
    "nb_volumes_serie": 12
  }},
  "criteres_validation": {{
    "pages_min": 100,
    "test_impression": "Pages lisibles en impression noir et blanc ?",
    "test_kdp_cover": "Dimensions cover exactes vérifiées ?",
    "test_bleed": "Bleed 0.125 inch de chaque côté ?"
  }}
}}
JSON uniquement."""

    user_prompt = f"""Crée le CdC complet pour :
- Type : {lc_type}
- Thème : {lc_theme}
- Audience : {lc_audience}

Ce livre doit être entièrement généré par ReportLab (Python), sans image externe.
Le layout doit être précis au millimètre pour que le script de production puisse l'implémenter directement."""

    print("[CdC Low-Content] Appel LLM...")
    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.80, max_tokens=5000)

    if not response:
        print("[CdC Low-Content] Échec LLM.", file=sys.stderr)
        sys.exit(1)

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]
    clean = clean.strip()

    try:
        cdc = json.loads(clean)
    except Exception as e:
        print(f"[CdC Low-Content] JSON invalide : {e}", file=sys.stderr)
        debug_path = LOWCONTENT_DIR / lc_id / "cdc_raw_debug.txt"
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        debug_path.write_text(response, encoding="utf-8")
        sys.exit(1)

    concept = cdc.get("concept", {})
    titre = concept.get("titre", lc_id)
    slug = f"{lc_id}_{titre[:30].lower().replace(' ', '_')}"
    out_dir = LOWCONTENT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    cdc_json = out_dir / "cdc.json"
    cdc_json.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[CdC Low-Content] cdc.json → {cdc_json}")

    identite = cdc.get("identite_commerciale", {})
    structure = cdc.get("structure_pages", {})
    spec_rl = cdc.get("spec_reportlab", {})

    md_lines = [
        f"# CAHIER DES CHARGES — {titre}",
        f"**Statut** : EN ATTENTE VALIDATION HUGO",
        f"**Date** : {today}",
        "",
        "## 🔴 GATE CdC = PENDING",
        "Pour valider : ouvrir `cdc.json` et changer `gate_cdc` de `pending` à `approved`",
        "",
        "---",
        "",
        "## 1. Identité Commerciale",
        f"**Nom de plume** : {identite.get('nom_de_plume', '?')}",
        f"**Marque/Série** : {identite.get('marque_serie', '?')}",
        "",
        "## 2. Concept",
        f"**Titre** : {concept.get('titre', '?')}",
        f"**Type** : {concept.get('type', '?')} | **Thème** : {concept.get('theme', '?')}",
        f"**Pages** : {concept.get('nombre_pages', '?')} | **Format** : {concept.get('format', '?')}",
        f"**Élément unique** : {concept.get('element_unique', '?')}",
        "",
        "## 3. Structure des Pages",
    ]

    pages_princ = structure.get("pages_principales", {})
    md_lines.append(f"**Pages principales** : {pages_princ.get('nb_pages', '?')} pages")
    md_lines.append(f"**Layout** : {pages_princ.get('layout_description', '?')}")
    md_lines.append(f"**Éléments/page** : {', '.join(pages_princ.get('elements_par_page', []))}")
    md_lines.append("")

    md_lines.append("## 4. Spec ReportLab")
    md_lines.append(f"- Police titre : {spec_rl.get('police_titre', '?')}")
    md_lines.append(f"- Police corps : {spec_rl.get('police_corps', '?')}")
    md_lines.append(f"- Couleur primaire : {spec_rl.get('couleur_primaire_hex', '?')}")
    md_lines.append(f"- Accent : {spec_rl.get('couleur_accent_hex', '?')}")
    md_lines.append(f"- Éléments décoratifs : {', '.join(spec_rl.get('elements_decoratifs', []))}")
    md_lines.append("")

    md_lines.append("## 5. Mots-clés KDP")
    md_lines.append(", ".join(cdc.get("mots_cles_kdp", [])))

    md_path = out_dir / "CAHIER_DES_CHARGES.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[CdC Low-Content] CAHIER_DES_CHARGES.md → {md_path}")
    print(f"\n[CdC Low-Content] ✓ CdC généré pour '{titre}'")
    print(f"[CdC Low-Content] GATE: pending — Hugo doit valider avant production.")


if __name__ == "__main__":
    run_cdc_lowcontent()
