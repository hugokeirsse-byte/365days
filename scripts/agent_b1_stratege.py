#!/usr/bin/env python3
"""
B1 Stratège — Reads all brain reports, scores opportunities, outputs weekly ranked proposals.
Runs every Monday 06h UTC. Each proposal gets a full mini-CdC.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_angle, get_previous_propositions, get_temperature, log_api_call

REPORTS_DIR = Path("data/reports")
OUTPUT_DIR = Path("data/strategie")


def collect_brain_signals() -> str:
    """Reads all recent brain reports and returns a condensed summary."""
    signals = []

    for folder in ["brain", "reports"]:
        p = Path("data") / folder
        if not p.exists():
            continue
        for f in sorted(p.rglob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
            try:
                content = f.read_text(encoding="utf-8")[:2000]
                signals.append(f"[{f.name}]\n{content}\n")
            except Exception:
                pass
        for f in sorted(p.rglob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
            try:
                content = f.read_text(encoding="utf-8")[:1500]
                signals.append(f"[{f.name}]\n{content}\n")
            except Exception:
                pass

    if not signals:
        return "Aucun rapport brain disponible pour le moment."

    return "\n---\n".join(signals[:15])


def collect_existing_products() -> str:
    """Lists existing products to avoid proposing duplicates."""
    products = []
    products_dir = Path("products")
    if products_dir.exists():
        for d in products_dir.iterdir():
            if d.is_dir():
                products.append(d.name)
    return ", ".join(products) if products else "aucun"


def run_stratege():
    today = date.today().isoformat()
    week = date.today().isocalendar()[1]
    angle = get_angle("stratege")
    temperature = get_temperature("stratege")
    previous = get_previous_propositions("data/strategie", "stratege")
    brain_signals = collect_brain_signals()
    existing_products = collect_existing_products()

    print(f"[B1 Stratège] Semaine {week} | Angle : {angle}")
    print(f"[B1 Stratège] Température : {temperature}")

    system_prompt = f"""Tu es le B1 Stratège de l'Usine 365days — une fabrique autonome de produits numériques.
Tu lis les rapports des agents Brain (tendances, niches, opportunités) et tu décides quoi produire cette semaine.

ANGLE DE CETTE SEMAINE :
{angle}

{previous}

PRODUITS DÉJÀ EN PRODUCTION / EXISTANTS :
{existing_products}

TON RÔLE :
1. Analyser les signaux brain
2. Scorer les opportunités sur 100 pts (potentiel revenu 35pts, fraîcheur/timing 25pts, faisabilité technique 20pts, différenciation 20pts)
3. Proposer 3 à 5 produits CONCRETS à lancer, classés par score décroissant
4. Pour chaque produit : mini-CdC complet (type, thème, plateforme, estimation revenu mensuel, effort, pourquoi maintenant)

STRATÉGIES DISPONIBLES :
- MONO-TREND : un produit qui surfe sur UNE tendance forte
- CROSS-TREND : croise deux tendances pour quelque chose d'unique
- ORIGINAL : création pure basée sur un insight non encore exploité
- REFONTE : amélioration d'un de nos produits existants sous-performants

TYPES DE PRODUITS POSSIBLES :
- Livre de coloriage KDP (Pollinations = gratuit, pas besoin de clé image)
- Roman KDP (Groq Llama 70B pour l'écriture)
- Low-content KDP (journal, planner, tracker — ReportLab, zéro image)
- STL 3D paramétrique (numpy-stl, Cults3D)
- Pack d'assets pour gamedev (sprites, textures, UI kits — itch.io, GameDevMarket)
- Jeu de cartes (PDF imprimable, Etsy)
- Affiche / art print (Redbubble, Society6)

FORMAT DE RÉPONSE — JSON STRICTEMENT :
{{
  "semaine": {week},
  "date": "{today}",
  "angle_applique": "...",
  "propositions": [
    {{
      "rang": 1,
      "strategie": "MONO-TREND|CROSS-TREND|ORIGINAL|REFONTE",
      "type_produit": "...",
      "titre_provisoire": "...",
      "theme": "...",
      "plateforme_cible": "...",
      "score_total": 87,
      "scores_detail": {{"potentiel": 32, "fraicheur": 22, "faisabilite": 18, "differenciation": 15}},
      "revenu_mensuel_estime": "150-300€",
      "effort_jours": 3,
      "pourquoi_maintenant": "...",
      "signal_source": "rapport brain qui justifie ce choix",
      "mini_cdc": {{
        "concept": "...",
        "public_cible": "...",
        "angle_unique": "...",
        "workflow_production": "...",
        "risques": "..."
      }}
    }}
  ],
  "propositions_reportees": []
}}
"""

    user_prompt = f"""Voici les signaux brain de cette semaine :

{brain_signals}

Génère ton rapport stratégique hebdomadaire. Réponds en JSON uniquement, sans markdown autour."""

    print("[B1 Stratège] Appel LLM...")
    response = llm_call("stratege", system_prompt, user_prompt, temperature=temperature, max_tokens=5000)

    if not response:
        print("[B1 Stratège] Échec LLM, rapport vide.")
        return

    # Parse and validate
    clean = response.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()

    try:
        data = json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"[B1 Stratège] JSON invalide : {e}")
        data = {"raw": clean, "date": today, "semaine": week, "parse_error": str(e)}

    # Write outputs
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    json_path = OUTPUT_DIR / f"rapport_stratege_{today}.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[B1 Stratège] Rapport JSON → {json_path}")

    # Generate Markdown summary
    md_lines = [f"# Rapport B1 Stratège — {today}", f"**Semaine {week}** | Angle : {angle}", ""]
    if "propositions" in data:
        for p in data["propositions"]:
            score = p.get("score_total", "?")
            md_lines.append(f"## #{p.get('rang', '?')} — {p.get('titre_provisoire', 'Sans titre')} [{score}/100]")
            md_lines.append(f"- **Type** : {p.get('type_produit', '?')}")
            md_lines.append(f"- **Stratégie** : {p.get('strategie', '?')}")
            md_lines.append(f"- **Plateforme** : {p.get('plateforme_cible', '?')}")
            md_lines.append(f"- **Revenu estimé** : {p.get('revenu_mensuel_estime', '?')}")
            md_lines.append(f"- **Effort** : {p.get('effort_jours', '?')} jours")
            md_lines.append(f"- **Pourquoi maintenant** : {p.get('pourquoi_maintenant', '?')}")
            cdc = p.get("mini_cdc", {})
            if cdc:
                md_lines.append(f"- **Concept** : {cdc.get('concept', '?')}")
                md_lines.append(f"- **Public** : {cdc.get('public_cible', '?')}")
            md_lines.append("")

    md_path = REPORTS_DIR / f"rapport_stratege_{today}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[B1 Stratège] Rapport MD → {md_path}")

    n = len(data.get("propositions", []))
    print(f"[B1 Stratège] {n} propositions générées. À valider par Hugo.")


if __name__ == "__main__":
    run_stratege()
