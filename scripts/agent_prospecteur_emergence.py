#!/usr/bin/env python3
"""
Prospecteur d'Émergence — Scans unexplored business domains every Thursday.
12 rotating angles. Reads past reports to force variety.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_angle, get_previous_propositions, get_temperature

REPORTS_DIR = Path("data/reports")


def read_existing_domains() -> str:
    """Reads CdC and MAP to know what's already covered."""
    context_parts = []
    for fname in ["CAHIER_DES_CHARGES.md", "MAP_BUSINESS_ET_AGENTS.md", "NOUVELLES_IDEES.md"]:
        p = Path(fname)
        if p.exists():
            context_parts.append(f"=== {fname} ===\n{p.read_text(encoding='utf-8')[:3000]}")
    return "\n\n".join(context_parts) if context_parts else "Pas de CdC disponible."


def run_prospecteur():
    today = date.today().isoformat()
    week = date.today().isocalendar()[1]
    angle = get_angle("prospecteur")
    temperature = get_temperature("prospecteur")
    previous = get_previous_propositions("data/reports", "prospecteur")
    existing_domains = read_existing_domains()

    print(f"[Prospecteur] Semaine {week} | Angle : {angle[:60]}...")
    print(f"[Prospecteur] Température : {temperature}")

    # --- APPEL 1 : Large scan ---
    system1 = f"""Tu es le Prospecteur d'Émergence de l'Usine 365days — une fabrique de produits numériques autonome.
Ta mission : trouver des domaines business que l'usine N'EXPLOITE PAS ENCORE mais devrait explorer.

CONTRAINTE MAJEURE — ANGLE DE CETTE SEMAINE :
{angle}

{previous}

DOMAINES DÉJÀ COUVERTS (ne pas re-proposer) :
Coloriages KDP, Merch POD, Restauration vintage, Jeux de cartes, Bébés crossover,
Mashups culturels, Low-content KDP (journaux/planners), Fictions/romans, Jeux mobiles,
STL 3D paramétrique, Vidéo faceless, Affiliation, Packs d'assets gamedev.

CONTEXTE USINE (extrait) :
{existing_domains[:2000]}

Génère 10 à 15 idées de nouveaux business domains, en JSON :
{{
  "idees": [
    {{
      "domaine": "Nom court du domaine",
      "description": "...",
      "signal_emergence": "Pourquoi c'est en train d'émerger maintenant ?",
      "compatibilite_usine": 8,
      "urgence": "haute|moyenne|basse",
      "plateforme_principale": "...",
      "revenu_potentiel_mensuel": "50-200€",
      "effort_mise_en_place": "...",
      "pourquoi_pas_encore_exploite": "..."
    }}
  ]
}}
Réponds JSON uniquement, sans markdown."""

    user1 = f"Scan de l'émergence — semaine {week}, angle : {angle}"

    print("[Prospecteur] Appel 1 : scan large...")
    response1 = llm_call("prospecteur", system1, user1, temperature=temperature, max_tokens=4000)

    if not response1:
        print("[Prospecteur] Échec appel 1.")
        return

    clean1 = response1.strip()
    if clean1.startswith("```"):
        parts = clean1.split("```")
        clean1 = parts[1][4:] if parts[1].startswith("json") else parts[1]
    clean1 = clean1.strip()

    try:
        data1 = json.loads(clean1)
        ideas = data1.get("idees", [])
    except Exception as e:
        print(f"[Prospecteur] JSON invalide appel 1 : {e}")
        ideas = []

    # Filter and sort
    ideas.sort(key=lambda x: (x.get("urgence", "basse") == "haute", x.get("compatibilite_usine", 0)), reverse=True)
    top3 = ideas[:3]

    # --- APPEL 2 : Deep dive sur top 3 ---
    top3_text = json.dumps(top3, ensure_ascii=False, indent=2)
    system2 = f"""Tu es le Prospecteur d'Émergence. Voici les 3 opportunités prioritaires identifiées.
Fais un deep dive sur chacune. Réponds en JSON :
{{
  "deep_dives": [
    {{
      "domaine": "...",
      "analyse_marche": "...",
      "stack_technique": "outils/scripts/APIs nécessaires",
      "trois_premiers_produits": ["...", "...", "..."],
      "fenetre_opportunite": "Ce marché sera saturé dans X mois si on n'agit pas.",
      "plan_action_30j": "...",
      "risques": "..."
    }}
  ]
}}
JSON uniquement, sans markdown."""

    user2 = f"Deep dive sur ces 3 opportunités :\n{top3_text}"

    print("[Prospecteur] Appel 2 : deep dive top 3...")
    response2 = llm_call("prospecteur", system2, user2, temperature=max(0.7, temperature - 0.1), max_tokens=4000)

    deep_dives = []
    if response2:
        clean2 = response2.strip()
        if clean2.startswith("```"):
            parts = clean2.split("```")
            clean2 = parts[1][4:] if parts[1].startswith("json") else parts[1]
        try:
            data2 = json.loads(clean2.strip())
            deep_dives = data2.get("deep_dives", [])
        except Exception as e:
            print(f"[Prospecteur] JSON invalide appel 2 : {e}")

    # Write report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    rapport = {
        "date": today,
        "semaine": week,
        "angle": angle,
        "temperature": temperature,
        "scan_complet": ideas,
        "top3": top3,
        "deep_dives": deep_dives,
    }

    json_path = REPORTS_DIR / f"rapport_prospecteur_{today}.json"
    json_path.write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Prospecteur] Rapport JSON → {json_path}")

    # Markdown
    md_lines = [f"# Rapport Prospecteur d'Émergence — {today}", f"**Angle** : {angle}", ""]
    md_lines.append(f"## {len(ideas)} Domaines identifiés\n")
    for i, idea in enumerate(ideas, 1):
        urgence = idea.get("urgence", "?")
        compat = idea.get("compatibilite_usine", "?")
        md_lines.append(f"### {i}. {idea.get('domaine', '?')} [{urgence}] [{compat}/10]")
        md_lines.append(f"{idea.get('description', '')}")
        md_lines.append(f"- **Signal** : {idea.get('signal_emergence', '?')}")
        md_lines.append(f"- **Plateforme** : {idea.get('plateforme_principale', '?')}")
        md_lines.append(f"- **Revenu** : {idea.get('revenu_potentiel_mensuel', '?')}")
        md_lines.append("")

    md_lines.append("## Deep Dives — Top 3\n")
    for dd in deep_dives:
        md_lines.append(f"### {dd.get('domaine', '?')}")
        md_lines.append(f"**Marché** : {dd.get('analyse_marche', '?')}")
        md_lines.append(f"**Stack** : {dd.get('stack_technique', '?')}")
        produits = dd.get("trois_premiers_produits", [])
        if produits:
            md_lines.append(f"**3 premiers produits** : {', '.join(produits)}")
        md_lines.append(f"**Fenêtre** : {dd.get('fenetre_opportunite', '?')}")
        md_lines.append(f"**Plan 30j** : {dd.get('plan_action_30j', '?')}")
        md_lines.append("")

    md_path = REPORTS_DIR / f"rapport_prospecteur_{today}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[Prospecteur] Rapport MD → {md_path}")
    print(f"[Prospecteur] {len(ideas)} idées, {len(deep_dives)} deep dives. Rapport prêt.")


if __name__ == "__main__":
    run_prospecteur()
