#!/usr/bin/env python3
"""
Agent STL Trends — Perpetual brain agent for the 3D print vertical.
Tracks trending niches on Cults3D, Printables, MyMiniFactory, r/3Dprinting.

Output:
  data/brain/stl/stl_trends_YYYY-MM-DD.json
  data/brain/stl/stl_trends_latest.json
  data/reports/rapport_stl_YYYY-MM-DD.md

Env:
  STL_ANGLE    optional override for the angle
  GEMINI_API_KEY
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions, get_angle, get_temperature

# ------------------------------------------------------------------ #
# Angle registry for STL vertical (rotates by week)
# ------------------------------------------------------------------ #
STL_ANGLES = [
    "gift_personalization",
    "cottagecore_homedecor",
    "gaming_tabletop",
    "functional_organizers",
    "seasonal_holiday",
    "plant_lovers",
    "booklovers",
    "cosplay_props",
    "pet_accessories",
    "minimalist_modern",
]

BRAIN_DIR = Path("data/brain/stl")
REPORTS_DIR = Path("data/reports")


def _get_stl_angle() -> str:
    """Returns this week's STL angle, or env override."""
    override = os.environ.get("STL_ANGLE", "").strip()
    if override:
        return override
    week = date.today().isocalendar()[1]
    return STL_ANGLES[week % len(STL_ANGLES)]


def run_stl_trends():
    today = date.today().isoformat()
    angle = _get_stl_angle()

    BRAIN_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    previous = get_previous_propositions("data/brain/stl", "stl_trends")

    print(f"[STL Trends] Date: {today} | Angle: {angle}")
    if previous:
        print(f"[STL Trends] Mémoire précédente chargée — INTERDIT de répéter.")

    system_prompt = f"""Tu es un expert du marché 3D print / STL files (Cults3D, Printables, MyMiniFactory, Etsy Digital).
Tu analyses les tendances du marché maker/3D print avec l'oeil d'un vendeur qui optimise ses revenus sur Cults3D et Printables.

ANGLE D'ANALYSE DU JOUR : {angle}
Toute l'analyse doit être colorée par cet angle. Cherche des niches en lien avec "{angle}".

CONTEXTE MARCHÉ :
- Cults3D : plateforme française leader, 80% royalties créateur, communauté internationale
- Printables (Prusa) : trafic massif, visibilité organique forte, badge "printed" social proof
- MyMiniFactory : forte communauté UK/US, gaming/miniatures très forts
- r/3Dprinting (Reddit) : 2,5M membres, détecteur précoce de tendances
- Marché en croissance explosive : imprimantes FDM grand public sous 200€ (Bambu A1 mini, etc.)
- Buyer personas : makers à domicile, parents qui veulent des cadeaux uniques, gamers, jardiniers, lecteurs, animaux

FORMATS QUI MARCHENT :
- Marque-pages avec texte engravé (booklovers, cottagecore, witchy)
- Organisateurs fonctionnels (bureau, cuisine, salle de bain)
- Porte-clés avec texte/animal (gift, personnalisation)
- Plaques de porte (chambre enfants, home decor)
- Marqueurs de plantes (jardinage, plant mom)
- Sous-verres gravés (home decor, cadeau)
- Figurines miniatures (gaming, D&D, Warhammer)
- Props cosplay (conventions, Halloween)
- Accessoires animaux (chats, chiens)

AVANTAGES CONCURRENTIELS À EXPLORER :
- Variantes multiples (15 textes pour un même modèle)
- Niche croisée (cottagecore + booklovers = marque-pages "cozy reader")
- Saisonnalité (Halloween, Noël, Saint-Valentin, rentrée)
- Personnalisation facile (OpenSCAD paramétrique)

RÈGLES STRATÉGIQUES :
- LANGUE : Titres et descriptions en anglais pour tous les produits (marché international).
- RÉHABILITATION : Repère les STL avec nombreux téléchargements/achats sur Cults3D mais
  mauvaises notes. Raison habituelle : texte non gravé (juste en relief), supports difficiles,
  dimensions hors marges imprimantes standard. Propose une version corrigeant ces défauts.

{previous}

FORMAT RÉPONSE — JSON STRICTEMENT (pas de markdown, pas de texte avant ou après) :
{{
  "date_analyse": "{today}",
  "angle": "{angle}",
  "agent": "stl_trends",
  "niches_trending": [
    {{
      "niche_name": "...",
      "plateformes_presence": {{
        "cults3d": 4,
        "printables": 3
      }},
      "volume_recherche_estime": "...",
      "croissance": "hausse|stable|baisse",
      "cible_acheteur": "...",
      "prix_moyen_usd": 2.50,
      "exemple_bestseller": "...",
      "notre_avantage_potentiel": "..."
    }}
  ],
  "produits_gagnants": [
    {{
      "type_objet": "bookmark|keychain|coaster|door_plate|plant_marker",
      "texte_ou_theme": "...",
      "raison_succes": "...",
      "difficulte_production": "facile|moyen|complexe",
      "priorite_score": 8
    }}
  ],
  "niches_a_eviter": [
    {{
      "niche": "...",
      "raison": "..."
    }}
  ],
  "opportunite_saisonniere": {{
    "evenement": "...",
    "date_approx": "...",
    "produit_suggere": "...",
    "urgence": "urgent|normal|anticiper"
  }},
  "recommandation_cdc": {{
    "type_produit": "bookmark|keychain|coaster|door_plate|plant_marker",
    "niche": "...",
    "theme": "...",
    "nb_variantes_suggere": 15,
    "priorite": "haute|moyenne|basse"
  }}
}}

RÈGLES :
- niches_trending : exactement 10 items
- produits_gagnants : exactement 5 items
- niches_a_eviter : exactement 5 items
- plateformes_presence : notes de 1 à 5 (1=rare, 5=saturé-mais-demandé)
- prix_moyen_usd : réaliste pour du STL (entre 1.50 et 6.00 USD)
- JSON uniquement, sans markdown ni texte autour"""

    user_prompt = f"""Analyse le marché 3D print STL de cette semaine.

Angle de la semaine : {angle}
Date : {today}

Identifie les 10 niches les plus prometteuses pour vendre des STL sur Cults3D et Printables.
Pense aux makers qui impriment à la maison pour offrir des cadeaux ou décorer.
Propose des produits concrets qu'on peut faire en OpenSCAD paramétrique (texte + géométrie simple).

Réponds avec le JSON complet. Aucun texte en dehors du JSON."""

    temperature = get_temperature("prospecteur")  # 0.85-1.0 pour la créativité
    print(f"[STL Trends] Appel LLM Gemini (temperature={temperature:.2f})...")
    response = llm_call("stl_trends", system_prompt, user_prompt, temperature=temperature, max_tokens=4000)

    if not response:
        print("[STL Trends] Échec LLM — aucune réponse.")
        sys.exit(1)

    # Clean markdown fences if present
    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:].strip() if parts[1].startswith("json") else parts[1].strip()

    try:
        data = json.loads(clean)
    except Exception as e:
        print(f"[STL Trends] JSON invalide : {e}")
        debug_path = BRAIN_DIR / f"stl_trends_debug_{today}.txt"
        debug_path.write_text(response, encoding="utf-8")
        print(f"[STL Trends] Raw sauvegardé → {debug_path}")
        sys.exit(1)

    # Write dated JSON
    dated_path = BRAIN_DIR / f"stl_trends_{today}.json"
    dated_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[STL Trends] JSON → {dated_path}")

    # Write latest (copy)
    latest_path = BRAIN_DIR / "stl_trends_latest.json"
    latest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[STL Trends] Latest → {latest_path}")

    # Write human-readable MD report
    md_lines = _build_md_report(data, today, angle)
    md_path = REPORTS_DIR / f"rapport_stl_{today}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[STL Trends] Rapport MD → {md_path}")

    # Summary print
    niches = data.get("niches_trending", [])
    produits = data.get("produits_gagnants", [])
    reco = data.get("recommandation_cdc", {})
    saisonnier = data.get("opportunite_saisonniere", {})

    print(f"\n[STL Trends] === RÉSUMÉ ===")
    print(f"Angle    : {angle}")
    print(f"Top niche: {niches[0].get('niche_name', '?') if niches else '?'}")
    print(f"Top produit: {produits[0].get('type_objet', '?')} — {produits[0].get('texte_ou_theme', '?') if produits else '?'}")
    print(f"Reco CdC : {reco.get('type_produit', '?')} / {reco.get('niche', '?')} (priorité: {reco.get('priorite', '?')})")
    print(f"Saison   : {saisonnier.get('evenement', '?')} — {saisonnier.get('urgence', '?')}")
    print(f"\n[STL Trends] Terminé. Outputs dans data/brain/stl/ et data/reports/")


def _build_md_report(data: dict, today: str, angle: str) -> list[str]:
    niches = data.get("niches_trending", [])
    produits = data.get("produits_gagnants", [])
    eviter = data.get("niches_a_eviter", [])
    saisonnier = data.get("opportunite_saisonniere", {})
    reco = data.get("recommandation_cdc", {})

    lines = [
        f"# Rapport STL Trends — {today}",
        f"**Angle** : {angle}",
        f"**Agent** : stl_trends | **Plateforme** : Cults3D, Printables, MyMiniFactory, r/3Dprinting",
        "",
        "---",
        "",
        "## 1. Niches Trending (10)",
        "",
        "| Niche | Cults3D | Printables | Croissance | Prix moy. | Cible |",
        "|-------|---------|------------|------------|-----------|-------|",
    ]

    for n in niches:
        pp = n.get("plateformes_presence", {})
        lines.append(
            f"| {n.get('niche_name', '?')} "
            f"| {'★' * pp.get('cults3d', 0)} ({pp.get('cults3d', 0)}/5) "
            f"| {'★' * pp.get('printables', 0)} ({pp.get('printables', 0)}/5) "
            f"| {n.get('croissance', '?')} "
            f"| ${n.get('prix_moyen_usd', '?'):.2f} "
            f"| {n.get('cible_acheteur', '?')} |"
        )

    lines += ["", "### Détail par niche", ""]
    for n in niches:
        lines.append(f"#### {n.get('niche_name', '?')}")
        lines.append(f"- **Volume recherche** : {n.get('volume_recherche_estime', '?')}")
        lines.append(f"- **Exemple bestseller** : {n.get('exemple_bestseller', '?')}")
        lines.append(f"- **Notre avantage** : {n.get('notre_avantage_potentiel', '?')}")
        lines.append("")

    lines += [
        "---",
        "",
        "## 2. Produits Gagnants (5)",
        "",
    ]
    for i, p in enumerate(produits, 1):
        score = p.get("priorite_score", "?")
        lines.append(f"### #{i} — {p.get('type_objet', '?')} : {p.get('texte_ou_theme', '?')}")
        lines.append(f"- **Raison succès** : {p.get('raison_succes', '?')}")
        lines.append(f"- **Difficulté** : {p.get('difficulte_production', '?')}")
        lines.append(f"- **Priorité score** : {score}/10")
        lines.append("")

    lines += [
        "---",
        "",
        "## 3. Opportunité Saisonnière",
        "",
        f"**Événement** : {saisonnier.get('evenement', '?')}",
        f"**Date approx.** : {saisonnier.get('date_approx', '?')}",
        f"**Produit suggéré** : {saisonnier.get('produit_suggere', '?')}",
        f"**Urgence** : {saisonnier.get('urgence', '?')}",
        "",
        "---",
        "",
        "## 4. Niches à Éviter",
        "",
    ]
    for e in eviter:
        lines.append(f"- **{e.get('niche', '?')}** : {e.get('raison', '?')}")

    lines += [
        "",
        "---",
        "",
        "## 5. Recommandation CdC",
        "",
        f"**Type produit** : `{reco.get('type_produit', '?')}`",
        f"**Niche** : {reco.get('niche', '?')}",
        f"**Thème** : {reco.get('theme', '?')}",
        f"**Nb variantes suggérées** : {reco.get('nb_variantes_suggere', '?')}",
        f"**Priorité** : {reco.get('priorite', '?')}",
        "",
        "> Pour lancer la production : `STL_TYPE={reco.get('type_produit', 'bookmark')} STL_NICHE={reco.get('niche', 'cottagecore')} python scripts/agent_stl_cdc.py`",
        "",
        "---",
        f"*Généré automatiquement le {today} par agent_stl_trends.py*",
    ]

    return lines


# Register angle in brain_utils format (monkey-patch ANGLES dict)
def _register_angle():
    """Register 'stl_trends' angle list in brain_utils so get_angle() works."""
    try:
        import scripts.lib.brain_utils as bu
        if "stl_trends" not in bu.ANGLES:
            bu.ANGLES["stl_trends"] = STL_ANGLES
    except Exception:
        pass


if __name__ == "__main__":
    _register_angle()
    run_stl_trends()
