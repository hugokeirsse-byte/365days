#!/usr/bin/env python3
"""
CdC Coloring Book — Generates a complete spec for a KDP coloring book.
Gate system: gate_cdc=pending until Hugo validates the prompt strategy
and manually tests one image before any production run starts.

Problem solved: previously 30 images at 1664x2160 were generated blind,
often with gray contamination, wrong style, and at 75 DPI (too low).
This script forces a validation gate BEFORE any image is generated.
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions

COLORING_DIR = Path("products/coloring_books")


def slugify(text: str, max_len: int = 40) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:max_len].strip("_")


def run_cdc_coloring():
    today = date.today().isoformat()

    # Read parameters from environment (set by CI from workflow inputs)
    theme = os.environ.get("COLORING_THEME", "botanical_garden")
    audience = os.environ.get("COLORING_AUDIENCE", "adult")
    pages = os.environ.get("COLORING_PAGES", "30")
    coloring_id = os.environ.get("COLORING_ID", f"coloring_{today}")

    previous = get_previous_propositions("products/coloring_books", "coloring_cdc")

    print(f"[CdC Coloring] Thème: {theme} | Audience: {audience} | Pages: {pages}")

    system_prompt = f"""Tu es un expert en publication KDP spécialisé dans les livres de coloriage.
Tu génères des Cahiers des Charges ultra-complets pour des livres produits avec Pollinations AI.

CONTEXTE CRITIQUE :
- La production génère {pages} images à 1664×2160px avec Pollinations AI (Flux)
- Problèmes passés : gris contaminants, mauvais style, DPI trop bas (75 DPI)
- Hugo DOIT valider la stratégie de prompts AVANT toute génération
- Les prompts doivent garantir : pur noir/blanc, pas de gris, lignes nettes, fond blanc

{previous}

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "coloring_id": "{coloring_id}",
  "date_cdc": "{today}",
  "gate_cdc": "pending",
  "concept": {{
    "titre": "Titre commercial accrocheur en anglais",
    "sous_titre": "Sous-titre descriptif pour Amazon",
    "theme_principal": "{theme}",
    "style_artistique": "botanical_precision|whimsical|zentangle|kawaii|realistic|mandala",
    "audience": "{audience}",
    "niveau_complexite": "simple|medium|intricate",
    "nombre_pages": {pages},
    "element_unique": "Ce qui le différencie des 200+ autres sur Amazon — sois précis et concret"
  }},
  "prompts_pollinations": {{
    "style_base": "black and white coloring page, clean outlines, no fill, white background, no gray, no shading",
    "style_modificateurs": ["modificateur 1 adapté au thème", "modificateur 2", "modificateur 3"],
    "theme_keywords": ["mot-clé thème 1", "mot-clé thème 2", "mot-clé thème 3", "mot-clé thème 4"],
    "negative_keywords": ["gray", "shading", "photo", "realistic texture", "color", "gradient", "shadow"],
    "exemple_prompt_complet": "black and white coloring page, [description scène précise], intricate details, clean lines, no fill, white background, no gray, no shading",
    "variantes_exemples": [
      "Prompt page simple (débutant) : ...",
      "Prompt page medium (intermédiaire) : ...",
      "Prompt page complexe (expert) : ..."
    ],
    "note_importante": "Toujours exclure les mots qui génèrent du gris ou du shading. Tester 1 page avant production."
  }},
  "pages_distribution": {{
    "pages_simples": 8,
    "pages_medium": 14,
    "pages_complexes": 8,
    "description_progression": "Description de la progression du début (simple) à la fin (complexe)"
  }},
  "public_cible": {{
    "persona": "Description précise de la personne qui achète ce livre",
    "tranche_age": "ex: 25-55 ans",
    "pourquoi_ce_theme": "Pourquoi ce thème résonne avec cette audience ?"
  }},
  "cinq_concurrents_amazon": [
    {{
      "titre": "Titre concurrent réaliste",
      "note": 4.5,
      "nb_avis": 500,
      "ce_qui_manque": "Ce que les acheteurs reprochent dans les avis 1-3 étoiles",
      "notre_avantage": "Comment notre livre résout ce problème"
    }}
  ],
  "kdp_listing": {{
    "titre_amazon": "Titre optimisé SEO Amazon (max 200 chars)",
    "sous_titre_amazon": "Sous-titre avec mots-clés",
    "description": "Description Amazon complète avec HTML basique (<b>, <br>), 600-900 caractères",
    "mots_cles": ["kw1", "kw2", "kw3", "kw4", "kw5", "kw6", "kw7"],
    "categories": ["Catégorie KDP 1", "Catégorie KDP 2"],
    "prix_usd": 9.99
  }},
  "criteres_validation": {{
    "test_style": "Générer 1 page test avec exemple_prompt_complet — vérifier : pur noir/blanc, ZERO gris, lignes nettes, fond blanc",
    "test_complexite": "Niveau de difficulté approprié à l'audience cible ? (adult=intricate ok, child=simple obligatoire)",
    "test_impression": "Lignes assez épaisses pour impression laser 300 DPI ? (min 2-3px à 1664px de large)",
    "test_marche": "Le thème est-il frais ou saturé sur Amazon aujourd'hui ? Chercher '{theme} coloring book' sur Amazon"
  }}
}}
JSON uniquement, sans markdown ni balises. Tous les champs doivent être remplis avec du contenu concret, pas des placeholders."""

    user_prompt = f"""Crée le Cahier des Charges complet pour ce livre de coloriage KDP :

- Thème principal : {theme}
- Audience : {audience}
- Nombre de pages : {pages}

PRIORITÉ ABSOLUE : les prompts Pollinations doivent garantir des images
pur noir/blanc sans aucun gris. C'est le problème critique qui a rendu
les productions précédentes inutilisables.

Génère un concept différenciant qui se vendra bien sur Amazon KDP dès aujourd'hui.
Les 5 concurrents doivent être réalistes (titres qui existent vraiment dans cette niche)."""

    print("[CdC Coloring] Appel LLM (génération CdC complet)...")
    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.80, max_tokens=6000)

    if not response:
        print("[CdC Coloring] Echec LLM.")
        sys.exit(1)

    # Strip markdown fences if present
    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]
    clean = clean.strip()

    try:
        cdc = json.loads(clean)
    except Exception as e:
        print(f"[CdC Coloring] JSON invalide : {e}")
        debug_path = COLORING_DIR / coloring_id / "cdc_raw_debug.txt"
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        debug_path.write_text(response, encoding="utf-8")
        print(f"[CdC Coloring] Raw sauvegarde -> {debug_path}")
        sys.exit(1)

    # Build output directory
    concept = cdc.get("concept", {})
    titre = concept.get("titre", coloring_id)
    titre_slug = slugify(titre)
    out_dir = COLORING_DIR / f"{coloring_id}_{titre_slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    cdc_json = out_dir / "cdc.json"
    cdc_json.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[CdC Coloring] cdc.json -> {cdc_json}")

    # Build human-readable CdC markdown
    prompts = cdc.get("prompts_pollinations", {})
    pages_dist = cdc.get("pages_distribution", {})
    public = cdc.get("public_cible", {})
    kdp = cdc.get("kdp_listing", {})
    criteres = cdc.get("criteres_validation", {})

    md_lines = [
        f"# CAHIER DES CHARGES — {titre}",
        f"**Statut** : EN ATTENTE VALIDATION HUGO",
        f"**Date** : {today}",
        f"**ID** : {cdc.get('coloring_id', coloring_id)}",
        "",
        "## GATE CdC = PENDING",
        "",
        "**Avant toute production :**",
        "1. Lire ce document et valider le concept + prompts",
        "2. Copier `exemple_prompt_complet` ci-dessous et tester manuellement sur https://pollinations.ai",
        "3. Verifier : pur noir/blanc, zero gris, lignes nettes, fond blanc",
        "4. Si OK : ouvrir `cdc.json` et changer `gate_cdc` de `pending` a `approved`",
        "5. Pousser le fichier — la production demarre automatiquement.",
        "",
        "---",
        "",
        "## 1. Concept",
        f"**Titre** : {concept.get('titre', '?')}",
        f"**Sous-titre** : {concept.get('sous_titre', '?')}",
        f"**Theme** : {concept.get('theme_principal', '?')}",
        f"**Style artistique** : {concept.get('style_artistique', '?')}",
        f"**Audience** : {concept.get('audience', '?')}",
        f"**Complexite** : {concept.get('niveau_complexite', '?')}",
        f"**Pages** : {concept.get('nombre_pages', '?')}",
        "",
        f"**Element unique** : {concept.get('element_unique', '?')}",
        "",
        "## 2. STRATEGIE PROMPTS POLLINATIONS",
        "",
        "> Ces prompts sont la CLE du projet. Tester avant de valider.",
        "",
        "### Style de base (a inclure dans TOUS les prompts)",
        f"```",
        prompts.get("style_base", "?"),
        f"```",
        "",
        "### Modificateurs de style",
    ]

    for mod in prompts.get("style_modificateurs", []):
        md_lines.append(f"- {mod}")

    md_lines += [
        "",
        "### Mots-cles du theme",
        ", ".join(prompts.get("theme_keywords", [])),
        "",
        "### Mots-cles NEGATIFS (a exclure pour eviter le gris)",
        ", ".join(prompts.get("negative_keywords", [])),
        "",
        "### EXEMPLE DE PROMPT COMPLET A TESTER",
        "",
        "> Copier ce prompt sur https://pollinations.ai et verifier le resultat",
        "",
        "```",
        prompts.get("exemple_prompt_complet", "?"),
        "```",
        "",
        "### Variantes par niveau de complexite",
    ]

    for variante in prompts.get("variantes_exemples", []):
        md_lines.append(f"- {variante}")

    md_lines += [
        "",
        f"**Note importante** : {prompts.get('note_importante', '?')}",
        "",
        "## 3. Distribution des Pages",
        f"- Pages simples : {pages_dist.get('pages_simples', '?')}",
        f"- Pages medium : {pages_dist.get('pages_medium', '?')}",
        f"- Pages complexes : {pages_dist.get('pages_complexes', '?')}",
        f"- Progression : {pages_dist.get('description_progression', '?')}",
        "",
        "## 4. Public Cible",
        f"**Persona** : {public.get('persona', '?')}",
        f"**Age** : {public.get('tranche_age', '?')}",
        f"**Pourquoi ce theme** : {public.get('pourquoi_ce_theme', '?')}",
        "",
        "## 5. Analyse Concurrence Amazon",
    ]

    for i, concur in enumerate(cdc.get("cinq_concurrents_amazon", []), 1):
        md_lines += [
            f"",
            f"### Concurrent {i} : {concur.get('titre', '?')}",
            f"- Note : {concur.get('note', '?')} | Avis : {concur.get('nb_avis', '?')}",
            f"- Ce qui manque : {concur.get('ce_qui_manque', '?')}",
            f"- Notre avantage : {concur.get('notre_avantage', '?')}",
        ]

    md_lines += [
        "",
        "## 6. Listing KDP",
        f"**Titre Amazon** : {kdp.get('titre_amazon', '?')}",
        f"**Sous-titre** : {kdp.get('sous_titre_amazon', '?')}",
        f"**Prix** : ${kdp.get('prix_usd', 9.99)}",
        "",
        "**Description** :",
        kdp.get("description", "?"),
        "",
        "**Mots-cles** : " + ", ".join(kdp.get("mots_cles", [])),
        "**Categories** : " + ", ".join(kdp.get("categories", [])),
        "",
        "## 7. Checklist de Validation",
        "",
        "Avant de changer gate_cdc a `approved` :",
        "",
        f"- [ ] **Test style** : {criteres.get('test_style', '?')}",
        f"- [ ] **Test complexite** : {criteres.get('test_complexite', '?')}",
        f"- [ ] **Test impression** : {criteres.get('test_impression', '?')}",
        f"- [ ] **Test marche** : {criteres.get('test_marche', '?')}",
        "",
        "---",
        "",
        f"*CdC genere le {today} — GATE: pending*",
    ]

    md_path = out_dir / "CAHIER_DES_CHARGES.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[CdC Coloring] CAHIER_DES_CHARGES.md -> {md_path}")

    print(f"\n[CdC Coloring] CdC genere pour '{titre}'")
    print(f"[CdC Coloring] -> {out_dir}/")
    print(f"[CdC Coloring] GATE: pending — Hugo doit tester un prompt et valider avant production.")
    print(f"\n[CdC Coloring] ETAPES SUIVANTES :")
    print(f"  1. Lire {md_path}")
    print(f"  2. Tester le prompt sur https://pollinations.ai")
    print(f"  3. Verifier : zero gris, lignes nettes, fond blanc pur")
    print(f"  4. Si OK : editer {cdc_json} -> gate_cdc = 'approved'")
    print(f"  5. Push -> la production demarre automatiquement")


if __name__ == "__main__":
    run_cdc_coloring()
