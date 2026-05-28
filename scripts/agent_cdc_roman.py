#!/usr/bin/env python3
"""
CdC Roman — Generates a complete spec (Cahier des Charges) for a novel.
Gate system: gate_cdc=pending until Hugo approves → then production starts.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions

REPORTS_DIR = Path("data/reports")
NOVELS_DIR = Path("products/novels")


def read_brain_signals() -> str:
    signals = []
    for folder in ["data/brain", "data/reports"]:
        p = Path(folder)
        if not p.exists():
            continue
        for f in sorted(p.rglob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
            try:
                signals.append(f.read_text(encoding="utf-8")[:1000])
            except Exception:
                pass
    return "\n---\n".join(signals) if signals else "Aucun signal brain."


def run_cdc_roman():
    today = date.today().isoformat()

    # Read parameters from environment (set by CI from trigger file)
    genre = os.environ.get("ROMAN_GENRE", "romance")
    sous_genre = os.environ.get("ROMAN_SOUS_GENRE", "contemporary")
    langue = os.environ.get("ROMAN_LANGUE", "en")
    roman_id = os.environ.get("ROMAN_ID", f"roman_{today}")

    previous = get_previous_propositions("products/novels", "cdc_roman")
    brain_signals = read_brain_signals()

    print(f"[CdC Roman] Genre: {genre} | Sous-genre: {sous_genre} | Langue: {langue}")

    system_prompt = f"""Tu es un expert en publication KDP qui crée des Cahiers des Charges ultra-complets pour des romans.

{previous}

CONTRAINTES :
- Langue du roman : {langue}
- Genre : {genre}
- Sous-genre / angle : {sous_genre}
- Plateforme cible : Amazon KDP (eBook + paperback)
- Chaque roman doit avoir un NOM DE PLUME UNIQUE (pas le vrai nom de l'auteur)
- Le nom de plume doit être mémorisable et adapté au genre

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "roman_id": "{roman_id}",
  "date_cdc": "{today}",
  "gate_cdc": "pending",
  "identite_commerciale": {{
    "nom_de_plume": "Prénom Nom inventé, adapté au genre",
    "bio_auteur": "Biographie de 100 mots à la 3e personne pour la page Amazon",
    "style_signature": "Description du style d'écriture de cet auteur fictif"
  }},
  "concept": {{
    "titre_principal": "...",
    "sous_titre": "...",
    "logline": "En 2 phrases, l'essence du roman",
    "genre_exact": "{genre}",
    "sous_genre": "{sous_genre}",
    "langue": "{langue}",
    "longueur_cible_mots": 65000,
    "nombre_chapitres": 38
  }},
  "public_cible": {{
    "persona_principal": "...",
    "tranche_age": "...",
    "interets": ["...", "..."],
    "pourquoi_ce_livre": "..."
  }},
  "analyse_marche": {{
    "taille_marche_estimee": "...",
    "tendance": "croissante|stable|déclinante",
    "timing": "Pourquoi maintenant ?"
  }},
  "cinq_concurrents": [
    {{
      "titre": "...",
      "auteur": "...",
      "asin": "...",
      "note_moyenne": 4.2,
      "nb_avis": 1500,
      "ce_qui_marche": "...",
      "notre_angle_differentiant": "..."
    }}
  ],
  "description_amazon": {{
    "accroche": "...",
    "corps": "...",
    "appel_action": "...",
    "longueur_totale_chars": 0
  }},
  "mots_cles_kdp": ["...", "...", "...", "...", "...", "...", "..."],
  "categories_kdp": ["...", "..."],
  "personnages": [
    {{
      "nom": "...",
      "role": "protagoniste|antagoniste|secondaire",
      "description_physique": "...",
      "personnalite": "...",
      "arc_narratif": "...",
      "voice": "Comment il/elle parle ?"
    }}
  ],
  "structure_narrative": {{
    "acte_1": {{"chapitres": "1-10", "objectif": "...", "turning_point": "..."}},
    "acte_2a": {{"chapitres": "11-20", "objectif": "...", "turning_point": "..."}},
    "acte_2b": {{"chapitres": "21-30", "objectif": "...", "turning_point": "..."}},
    "acte_3": {{"chapitres": "31-38", "objectif": "...", "turning_point": "..."}}
  }},
  "plan_38_chapitres": [
    {{"numero": 1, "titre": "...", "pov": "...", "synopsis": "...", "hook_fin": "...", "mots_cibles": 1700}}
  ],
  "guide_style": {{
    "ton_general": "...",
    "niveau_sensualite": "sweet|warm|spicy|steamy",
    "longueur_scene_type": "...",
    "pacing": "...",
    "tropes_utilises": ["...", "..."],
    "tropes_a_eviter": ["..."],
    "voix_narrative": "1ere personne|3e personne limitée|omnisciente"
  }},
  "exigences_kdp": {{
    "isbn_requis": false,
    "drm": true,
    "prix_ebook_usd": 3.99,
    "prix_paperback_usd": 12.99,
    "cover_dimensions": "1600x2560px",
    "interior_font": "Garamond 12pt",
    "margins_cm": {{"top": 2.5, "bottom": 2.5, "inner": 2.0, "outer": 1.5}}
  }},
  "calendrier_production": {{
    "semaines_redaction": 4,
    "semaines_relecture": 1,
    "semaines_mise_en_page": 0.5,
    "date_publication_cible": "...",
    "budget_cover_design_eur": 30
  }},
  "criteres_validation": {{
    "longueur_min_mots": 60000,
    "score_lisibilite_min": 70,
    "test_trope": "Tous les tropes listés présents ?",
    "test_arc": "L'arc de chaque personnage principal est complet ?"
  }}
}}
JSON uniquement, sans markdown. Le plan des 38 chapitres doit être COMPLET."""

    user_prompt = f"""Crée le Cahier des Charges complet pour ce roman.

Signaux marché actuels :
{brain_signals[:2000]}

Genre cible : {genre} / {sous_genre} en {langue}.
Génère un roman qui se vendra bien sur Amazon KDP dès aujourd'hui."""

    print("[CdC Roman] Appel LLM (génération CdC complet)...")
    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.85, max_tokens=8000)

    if not response:
        print("[CdC Roman] Échec LLM.", file=sys.stderr)
        sys.exit(1)

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]
    clean = clean.strip()

    try:
        cdc = json.loads(clean)
    except Exception as e:
        print(f"[CdC Roman] JSON invalide : {e}", file=sys.stderr)
        debug_path = NOVELS_DIR / roman_id / "cdc_raw_debug.txt"
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        debug_path.write_text(response, encoding="utf-8")
        print(f"[CdC Roman] Raw sauvegardé → {debug_path}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    nom_plume = cdc.get("identite_commerciale", {}).get("nom_de_plume", "auteur")
    titre = cdc.get("concept", {}).get("titre_principal", roman_id)
    slug = f"{roman_id}_{titre[:30].lower().replace(' ', '_')}"
    out_dir = NOVELS_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    cdc_json = out_dir / "cdc.json"
    cdc_json.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[CdC Roman] cdc.json → {cdc_json}")

    # Generate readable CdC markdown
    concept = cdc.get("concept", {})
    identite = cdc.get("identite_commerciale", {})
    public = cdc.get("public_cible", {})
    style = cdc.get("guide_style", {})

    md_lines = [
        f"# CAHIER DES CHARGES — {titre}",
        f"**Statut** : EN ATTENTE VALIDATION HUGO",
        f"**Date** : {today}",
        "",
        "## 🔴 GATE CdC = PENDING",
        "Pour valider : ouvrir `cdc.json` et changer `gate_cdc` de `pending` à `approved`",
        "Puis pousser le fichier — la production démarre automatiquement.",
        "",
        "---",
        "",
        "## 1. Identité Commerciale",
        f"**Nom de plume** : {identite.get('nom_de_plume', '?')}",
        f"**Style signature** : {identite.get('style_signature', '?')}",
        "",
        f"**Bio Amazon** :",
        identite.get("bio_auteur", "?"),
        "",
        "## 2. Concept",
        f"**Titre** : {concept.get('titre_principal', '?')}",
        f"**Sous-titre** : {concept.get('sous_titre', '?')}",
        f"**Logline** : {concept.get('logline', '?')}",
        f"**Genre** : {concept.get('genre_exact', '?')} / {concept.get('sous_genre', '?')}",
        f"**Langue** : {concept.get('langue', '?')}",
        f"**Longueur** : {concept.get('longueur_cible_mots', '?')} mots / {concept.get('nombre_chapitres', '?')} chapitres",
        "",
        "## 3. Public Cible",
        f"**Persona** : {public.get('persona_principal', '?')}",
        f"**Âge** : {public.get('tranche_age', '?')}",
        "",
        "## 4. Guide de Style",
        f"**Ton** : {style.get('ton_general', '?')}",
        f"**Voix** : {style.get('voix_narrative', '?')}",
        f"**Niveau sensualité** : {style.get('niveau_sensualite', '?')}",
        f"**Tropes** : {', '.join(style.get('tropes_utilises', []))}",
        "",
        "## 5. Personnages",
    ]

    for perso in cdc.get("personnages", []):
        md_lines.append(f"### {perso.get('nom', '?')} ({perso.get('role', '?')})")
        md_lines.append(f"- Physique : {perso.get('description_physique', '?')}")
        md_lines.append(f"- Personnalité : {perso.get('personnalite', '?')}")
        md_lines.append(f"- Arc : {perso.get('arc_narratif', '?')}")
        md_lines.append("")

    md_lines.append("## 6. Plan des 38 Chapitres")
    for ch in cdc.get("plan_38_chapitres", []):
        md_lines.append(f"**Ch.{ch.get('numero', '?')}** : {ch.get('titre', '?')}")
        md_lines.append(f"  > {ch.get('synopsis', '?')}")

    md_path = out_dir / "CAHIER_DES_CHARGES.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[CdC Roman] CAHIER_DES_CHARGES.md → {md_path}")

    print(f"\n[CdC Roman] ✓ CdC généré pour '{titre}' par {identite.get('nom_de_plume', '?')}")
    print(f"[CdC Roman] → products/novels/{slug}/")
    print(f"[CdC Roman] GATE: pending — Hugo doit valider avant production.")


if __name__ == "__main__":
    run_cdc_roman()
