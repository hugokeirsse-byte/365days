#!/usr/bin/env python3
"""
Agent Merch Design CdC — Generates a Cahier des Charges for a print-on-demand merch collection.

One CdC = one theme → 20-50 designs, all sharing the theme but each unique.
Hugo reviews via gate_cdc field; production is triggered only after approval.

Env vars:
  MERCH_CONCEPT     — theme/concept  (ex: "world proverbs translated to english funny illustration")
  MERCH_NB_DESIGNS  — number of designs in the collection  (default: 30)
  MERCH_STYLE       — visual style  (ex: "flat colorful illustration", "minimalist line art", "watercolor")
  MERCH_LANGUE      — en|fr  (default: en)
  MERCH_ID          — default: merch_YYYY-MM-DD
  GEMINI_API_KEY

Output:
  products/merch/{merch_id}_{titre_slug}/cdc.json
  products/merch/{merch_id}_{titre_slug}/CAHIER_DES_CHARGES.md
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, extract_json, get_previous_propositions

MERCH_DIR = Path("products/merch")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _slugify(text: str) -> str:
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


def _strip_json_fences(text: str) -> str:
    """Remove ```json ... ``` fences if present."""
    clean = text.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        block = parts[1] if len(parts) > 1 else ""
        if block.startswith("json"):
            block = block[4:]
        clean = block.strip()
    return clean


def _write_markdown(out_dir: Path, cdc: dict) -> None:
    """Write human-readable CAHIER_DES_CHARGES.md."""
    ct = cdc.get("concept_theme", {})
    sv = cdc.get("style_visuel", {})
    sp = cdc.get("spec_production", {})
    lp = cdc.get("listing_plateforme", {})
    am = cdc.get("analyse_marche", {})
    cv = cdc.get("criteres_validation", {})
    plateformes = cdc.get("plateformes", [])
    produits = cdc.get("produits_cibles", [])
    designs = cdc.get("designs", [])

    lines = [
        f"# {ct.get('titre', 'Merch Collection')}",
        "",
        f"> **Merch ID:** `{cdc.get('merch_id', '')}` | **Date:** {cdc.get('date_cdc', '')} | **Gate:** `{cdc.get('gate_cdc', 'pending')}`",
        "",
        "## Concept",
        "",
        f"**Description:** {ct.get('description', '')}",
        "",
        f"**Émotion cible:** {ct.get('emotion_cible', '')}",
        f"**Élément unique:** {ct.get('element_unique', '')}",
        f"**Nombre de designs:** {ct.get('nb_designs', len(designs))}",
        f"**Evergreen:** {'Oui' if ct.get('evergreen') else 'Non'}",
        "",
        "## Produits cibles",
        "",
        ", ".join(produits),
        "",
        "## Plateformes",
        "",
        "| Plateforme | Format principal | Royalty |",
        "|---|---|---|",
    ]
    for p in plateformes:
        lines.append(f"| {p.get('nom')} | {p.get('format_principal')} | {p.get('royalty_pct')}% |")

    palette = sv.get("palette_principale", {})
    lines += [
        "",
        "## Style visuel",
        "",
        f"**Style illustration:** {sv.get('style_illustration', '')}",
        f"**Palette — Primaire:** {palette.get('primaire', '')} | **Secondaire:** {palette.get('secondaire', '')} | **Fond:** {palette.get('fond', '')}",
        f"**Font titre:** {sv.get('font_titre', '')}",
        f"**Font corps:** {sv.get('font_corps', '')}",
        f"**Ton graphique:** {sv.get('ton_graphique', '')}",
        "",
        "## Spec de production",
        "",
        f"**Format base:** {sp.get('format_base_px', '')}px",
        f"**Fond:** {sp.get('fond', '')}",
        f"**Zone illustration:** {sp.get('zone_illustration_pct', '')}%  |  **Zone texte:** {sp.get('zone_texte_pct', '')}%  |  **Marge:** {sp.get('marge_pct', '')}%",
        f"**Prompt modifiers communs:** `{sp.get('prompt_base_modifiers', '')}`",
        "",
        "## Listing & Prix",
        "",
        f"**Titre collection:** {lp.get('titre_collection', '')}",
        f"**Tags communs:** {', '.join(lp.get('tags_communs', []))}",
        f"**Prix T-shirt:** ${lp.get('prix_tshirt_usd', '')}  |  **Prix Mug:** ${lp.get('prix_mug_usd', '')}",
        "",
        "## Analyse marché",
        "",
        f"**Potentiel:** {am.get('potentiel', '')}",
        f"**Concurrence:** {am.get('concurrence', '')}",
        f"**Avantage:** {am.get('avantage', '')}",
        "",
        "## Critères de validation",
        "",
        f"- **Concept unique:** {cv.get('concept_unique', '')}",
        f"- **Scalable:** {cv.get('scalable', '')}",
        f"- **Achetable:** {cv.get('achetable', '')}",
        f"- **Illustrations faisables:** {cv.get('illustrations_faisables', '')}",
        "",
        "---",
        "",
        f"## Designs ({len(designs)} total)",
        "",
        "| # | Sous-thème | Texte principal | Description illustration | Prompt Pollinations |",
        "|---|---|---|---|---|",
    ]
    for d in designs:
        n = d.get("n", "?")
        sous = d.get("sous_theme", "")
        texte = d.get("texte_principal", "").replace("|", "\\|")
        desc = d.get("description_illustration", "").replace("|", "\\|")
        prompt = d.get("prompt_pollinations", "").replace("|", "\\|")
        lines.append(f"| {n} | {sous} | {texte} | {desc} | {prompt} |")

    lines += [
        "",
        "---",
        "",
        "> **GATE: pending** — Hugo valide, puis `produce_merch_designs.py` génère les images.",
    ]

    (out_dir / "CAHIER_DES_CHARGES.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[Merch CdC] CAHIER_DES_CHARGES.md écrit ({len(designs)} designs)")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def run_merch_cdc():
    today = date.today().isoformat()

    concept = os.environ.get("MERCH_CONCEPT", "").strip()
    if not concept:
        print("[Merch CdC] ERREUR: MERCH_CONCEPT non défini. Ex: MERCH_CONCEPT='world proverbs funny illustration'")
        sys.exit(1)

    nb_designs = int(os.environ.get("MERCH_NB_DESIGNS", "30"))
    style = os.environ.get("MERCH_STYLE", "flat colorful illustration").strip()
    langue = os.environ.get("MERCH_LANGUE", "en").strip().lower()
    merch_id = os.environ.get("MERCH_ID", f"merch_{today}").strip()

    MERCH_DIR.mkdir(parents=True, exist_ok=True)

    previous = get_previous_propositions("products/merch", "merch_cdc")
    print(f"[Merch CdC] Concept: {concept!r} | Designs: {nb_designs} | Style: {style} | Langue: {langue} | ID: {merch_id}")
    if previous:
        print("[Merch CdC] Mémoire précédente chargée — INTERDIT de répéter les thèmes existants.")

    system_prompt = f"""You are an expert print-on-demand designer and market strategist for Redbubble, Merch by Amazon, Society6, and Etsy+Printful.
You create complete, actionable Cahiers des Charges (design briefs) for merch collections.

One CdC = one theme → {nb_designs} designs, all sharing the theme but each completely unique.
Each design must have a distinct prompt_pollinations, a unique sous_theme, and standalone visual appeal.

{previous}

LANGUAGE: {"English" if langue == "en" else "French (but product names and tags in English for global market)"}
STYLE REQUESTED: {style}
TARGET CONCEPT: {concept}

PLATFORMS: Redbubble, Merch by Amazon, Society6, Etsy+Printful
PRODUCTS: t-shirts, mugs, keychains, stickers, posters, tote bags, phone cases, hoodies

RULES:
- Every design in the "designs" array must be fully specified (no placeholders, no "...")
- Each prompt_pollinations must be unique, detailed, and optimized for image generation (no text in image)
- The collection must feel cohesive yet each design must work standalone
- All designs must be print-on-demand safe (no copyrighted characters, no real logos)
- Pollinations prompts: always end with "flat design, white background, no text, colorful, simple illustration, clean lines"
- The designs array must contain EXACTLY {nb_designs} entries

RESPONSE FORMAT: strict JSON only (no markdown, no text before or after the JSON block)"""

    user_prompt = f"""Create the complete Cahier des Charges for this merch collection.

Concept: {concept}
Number of designs: {nb_designs}
Visual style: {style}
Target language: {langue}
Merch ID: {merch_id}

Return this exact JSON structure with ALL {nb_designs} designs fully specified:

{{
  "merch_id": "{merch_id}",
  "date_cdc": "{today}",
  "gate_cdc": "pending",
  "concept_theme": {{
    "titre": "Collection title (catchy, marketable)",
    "description": "1-2 sentence description of the concept",
    "emotion_cible": "e.g. humor + cultural discovery + shareable",
    "element_unique": "What makes this collection stand out on Redbubble",
    "nb_designs": {nb_designs},
    "evergreen": true
  }},
  "produits_cibles": ["t-shirt", "mug", "sticker", "poster", "tote_bag", "phone_case", "hoodie"],
  "plateformes": [
    {{"nom": "redbubble", "format_principal": "2400x3200px PNG", "royalty_pct": 20}},
    {{"nom": "merch_amazon", "format_principal": "4500x5400px PNG transparent", "royalty_pct": 37}},
    {{"nom": "society6", "format_principal": "2400x3200px PNG", "royalty_pct": 10}},
    {{"nom": "etsy_printful", "format_principal": "4000x4000px PNG transparent", "royalty_pct": 30}}
  ],
  "style_visuel": {{
    "style_illustration": "{style}",
    "palette_principale": {{"primaire": "#XXXXXX", "secondaire": "#XXXXXX", "fond": "#FFFFFF"}},
    "font_titre": "bold rounded sans-serif",
    "font_corps": "clean readable sans-serif",
    "ton_graphique": "fun and colorful / minimal and elegant / vintage"
  }},
  "designs": [
    {{
      "n": 1,
      "sous_theme": "specific sub-topic (e.g. country, animal, situation)",
      "texte_principal": "The main text on the design (catchy, quote, or label)",
      "sous_texte": "Secondary line (emoji + label, e.g. '🇵🇹 Portuguese Proverb')",
      "texte_secondaire": "(Optional explanation or tagline in parentheses)",
      "description_illustration": "Detailed description of the illustration (2-3 sentences)",
      "prompt_pollinations": "Full image generation prompt ending with: flat design, white background, no text, colorful, simple illustration, clean lines",
      "emoji": "1-2 relevant emojis",
      "couleur_accent": "#XXXXXX"
    }}
  ],
  "spec_production": {{
    "format_base_px": "2400x2400",
    "fond": "white",
    "zone_illustration_pct": 60,
    "zone_texte_pct": 35,
    "marge_pct": 5,
    "prompt_base_modifiers": "flat design, white background, no text, colorful, simple illustration, clean lines"
  }},
  "listing_plateforme": {{
    "titre_collection": "SEO-optimized collection title for platforms",
    "tags_communs": ["funny", "gift", "humor", "unique", "illustration"],
    "prix_tshirt_usd": 24.99,
    "prix_mug_usd": 17.99
  }},
  "analyse_marche": {{
    "potentiel": "Market potential analysis (2-3 sentences)",
    "concurrence": "faible|moyenne|forte",
    "avantage": "Our competitive advantage for this collection"
  }},
  "criteres_validation": {{
    "concept_unique": "Does the theme stand out from what exists on Redbubble?",
    "scalable": "Can we generate 100+ designs in this theme?",
    "achetable": "Would someone buy this as a gift?",
    "illustrations_faisables": "Are the illustration descriptions achievable by Pollinations?"
  }}
}}

Generate ALL {nb_designs} entries in the designs array. Each must be unique, creative, and fully specified."""

    print(f"[Merch CdC] Appel LLM Gemini (génération CdC complet, {nb_designs} designs)...")
    response = llm_call("stl_cdc", system_prompt, user_prompt, temperature=0.85, max_tokens=12000)

    if not response:
        print("[Merch CdC] Échec LLM — aucune réponse reçue.")
        sys.exit(1)

    clean = extract_json(response)
    try:
        cdc = json.loads(clean)
    except Exception as e:
        print(f"[Merch CdC] JSON invalide : {e}")
        # Save raw response for debugging
        debug_path = MERCH_DIR / f"_debug_{merch_id}_raw.txt"
        debug_path.write_text(response, encoding="utf-8")
        print(f"[Merch CdC] Réponse brute sauvegardée : {debug_path}")
        sys.exit(1)

    # Verify design count
    designs = cdc.get("designs", [])
    actual_nb = len(designs)
    if actual_nb < nb_designs:
        print(f"[Merch CdC] WARNING: LLM a généré {actual_nb}/{nb_designs} designs.")
    else:
        print(f"[Merch CdC] {actual_nb} designs générés.")

    # Ensure merch_id is correct
    cdc["merch_id"] = merch_id
    cdc["date_cdc"] = today
    cdc.setdefault("gate_cdc", "pending")

    # Build output directory
    titre = cdc.get("concept_theme", {}).get("titre", concept)
    titre_slug = _slugify(titre)
    out_dir = MERCH_DIR / f"{merch_id}_{titre_slug}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write cdc.json
    cdc_path = out_dir / "cdc.json"
    cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Merch CdC] cdc.json écrit : {cdc_path}")

    # Write markdown
    _write_markdown(out_dir, cdc)

    print()
    print(f"  Collection : {titre}")
    print(f"  Dossier    : {out_dir}")
    print(f"  Designs    : {actual_nb}")
    print()
    print(f"GATE: pending — Hugo valide puis production génère les {actual_nb} designs.")
    print(f"Pour approuver : éditer gate_cdc → 'approved' dans {cdc_path}")
    print(f"Pour produire  : MERCH_DIR={out_dir} python scripts/produce_merch_designs.py")


if __name__ == "__main__":
    run_merch_cdc()
