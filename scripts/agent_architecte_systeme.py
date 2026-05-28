#!/usr/bin/env python3
"""
Architecte Système — Weekly audit of CdC vs reality. Auto-generates Builder briefings.
Runs every Sunday 04h UTC. Identifies gaps, vulnerabilities, quick wins.
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_angle, get_previous_propositions, get_temperature

REPORTS_DIR = Path("data/reports")
BUILD_QUEUE = Path("data/build_queue")


def inventory_system() -> dict:
    """Takes a snapshot of the actual system state."""
    state = {
        "workflows": [],
        "scripts": [],
        "products": [],
        "briefings_pending": [],
        "briefings_done": [],
        "trigger_files": [],
        "reports": [],
    }

    # Workflows
    wf_dir = Path(".github/workflows")
    if wf_dir.exists():
        state["workflows"] = [f.name for f in wf_dir.glob("*.yml")]

    # Scripts
    scripts_dir = Path("scripts")
    if scripts_dir.exists():
        state["scripts"] = [f.name for f in scripts_dir.glob("*.py")]

    # Products
    products_dir = Path("products")
    if products_dir.exists():
        for d in products_dir.iterdir():
            if d.is_dir():
                state["products"].append(d.name)

    # Build queue
    if BUILD_QUEUE.exists():
        state["briefings_pending"] = [f.name for f in BUILD_QUEUE.glob("*.md")]
        done = BUILD_QUEUE / "done"
        if done.exists():
            state["briefings_done"] = [f.name for f in done.glob("*.md")]

    # Triggers
    triggers_dir = Path(".triggers")
    if triggers_dir.exists():
        state["trigger_files"] = [f.name for f in triggers_dir.iterdir() if f.is_file()]

    # Reports
    if REPORTS_DIR.exists():
        state["reports"] = [f.name for f in REPORTS_DIR.rglob("*.json")][:20]

    return state


def read_cdc_doc() -> str:
    p = Path("CAHIER_DES_CHARGES.md")
    return p.read_text(encoding="utf-8")[:5000] if p.exists() else "Non trouvé."


def run_architecte():
    today = date.today().isoformat()
    week = date.today().isocalendar()[1]
    angle = get_angle("architecte")
    temperature = get_temperature("architecte")
    previous = get_previous_propositions("data/reports", "architecte")

    print(f"[Architecte] Semaine {week} | Angle : {angle[:60]}...")

    system_state = inventory_system()
    cdc_doc = read_cdc_doc()

    system_prompt = f"""Tu es l'Architecte Système de l'Usine 365days — tu audites l'infrastructure chaque semaine.
Tu compares le Cahier des Charges (vision) avec la réalité du système (ce qui existe vraiment).

ANGLE DE CETTE SEMAINE :
{angle}

{previous}

FORMAT DE RÉPONSE — JSON STRICTEMENT :
{{
  "date": "{today}",
  "semaine": {week},
  "angle_applique": "...",
  "score_sante_systeme": 72,
  "gaps_critiques": [
    {{
      "titre": "...",
      "description": "...",
      "priorite": "critique|haute|moyenne",
      "impact_si_non_corrige": "...",
      "solution_proposee": "...",
      "generer_briefing": true
    }}
  ],
  "vulnerabilites": [
    {{
      "titre": "...",
      "description": "...",
      "risque": "...",
      "mitigation": "..."
    }}
  ],
  "ameliorations_durables": [
    {{
      "titre": "...",
      "description": "...",
      "benefice": "...",
      "effort": "faible|moyen|élevé"
    }}
  ],
  "quick_wins": [
    {{
      "titre": "...",
      "action": "...",
      "temps_estime": "..."
    }}
  ],
  "couverture_cdc": {{
    "Coloriages KDP": "OK|PARTIEL|MANQUANT",
    "Merch POD": "OK|PARTIEL|MANQUANT",
    "Restauration vintage": "OK|PARTIEL|MANQUANT",
    "Jeux de cartes": "OK|PARTIEL|MANQUANT",
    "Bébés crossover": "OK|PARTIEL|MANQUANT",
    "Mashups culturels": "OK|PARTIEL|MANQUANT",
    "Low-content KDP": "OK|PARTIEL|MANQUANT",
    "Fictions/Romans": "OK|PARTIEL|MANQUANT",
    "Jeux mobiles": "OK|PARTIEL|MANQUANT",
    "STL 3D": "OK|PARTIEL|MANQUANT",
    "Vidéo faceless": "OK|PARTIEL|MANQUANT",
    "Affiliation": "OK|PARTIEL|MANQUANT",
    "Assets gamedev": "OK|PARTIEL|MANQUANT"
  }},
  "resume_executif": "..."
}}
JSON uniquement."""

    user_prompt = f"""ÉTAT RÉEL DU SYSTÈME :

Workflows CI ({len(system_state['workflows'])}) : {', '.join(system_state['workflows'][:30])}

Scripts ({len(system_state['scripts'])}) : {', '.join(system_state['scripts'][:30])}

Produits ({len(system_state['products'])}) : {', '.join(system_state['products'][:20])}

Briefings en attente ({len(system_state['briefings_pending'])}) : {', '.join(system_state['briefings_pending'])}

Briefings traités ({len(system_state['briefings_done'])}) : {', '.join(system_state['briefings_done'])}

Rapports brain ({len(system_state['reports'])}) : {', '.join(system_state['reports'][:15])}

VISION CdC (extrait) :
{cdc_doc}

Génère ton audit système complet."""

    print("[Architecte] Appel LLM...")
    response = llm_call("architecte", system_prompt, user_prompt, temperature=temperature, max_tokens=5000)

    if not response:
        print("[Architecte] Échec LLM.")
        return

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]
    clean = clean.strip()

    try:
        data = json.loads(clean)
    except Exception as e:
        print(f"[Architecte] JSON invalide : {e}")
        data = {"raw": clean, "date": today, "parse_error": str(e)}

    # Write report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / f"rapport_architecte_{today}.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Architecte] Rapport → {json_path}")

    # Auto-generate briefings for critical gaps
    briefings_generated = 0
    if "gaps_critiques" in data:
        for gap in data["gaps_critiques"]:
            if gap.get("generer_briefing") and gap.get("priorite") in ("critique", "haute"):
                briefing_content = f"""# AUTO_{today}_{gap.get('titre', 'gap').replace(' ', '_')[:40]}

## GÉNÉRÉ AUTOMATIQUEMENT par Architecte Système — {today}

## PROBLÈME IDENTIFIÉ
{gap.get('description', '')}

## PRIORITÉ
{gap.get('priorite', '')}

## IMPACT SI NON CORRIGÉ
{gap.get('impact_si_non_corrige', '')}

## SOLUTION PROPOSÉE
{gap.get('solution_proposee', '')}

## FICHIER À PRODUIRE
Un script Python dans `scripts/` ou un workflow dans `.github/workflows/`
qui résout le problème décrit ci-dessus.
"""
                briefing_name = f"AUTO_architecte_{today}_{briefings_generated+1:02d}.md"
                BUILD_QUEUE.mkdir(parents=True, exist_ok=True)
                (BUILD_QUEUE / briefing_name).write_text(briefing_content, encoding="utf-8")
                print(f"[Architecte] Briefing auto-généré : {briefing_name}")
                briefings_generated += 1

    # Markdown summary
    md_lines = [
        f"# Rapport Architecte Système — {today}",
        f"**Santé** : {data.get('score_sante_systeme', '?')}/100 | **Angle** : {angle[:60]}",
        "",
        f"## Résumé",
        data.get("resume_executif", "N/A"),
        "",
    ]

    gaps = data.get("gaps_critiques", [])
    if gaps:
        md_lines.append(f"## Gaps Critiques ({len(gaps)})")
        for g in gaps:
            prio = g.get("priorite", "?")
            md_lines.append(f"- [{prio.upper()}] **{g.get('titre', '?')}** : {g.get('description', '')[:120]}")
        md_lines.append("")

    quick_wins = data.get("quick_wins", [])
    if quick_wins:
        md_lines.append(f"## Quick Wins")
        for qw in quick_wins:
            md_lines.append(f"- **{qw.get('titre', '?')}** ({qw.get('temps_estime', '?')}) : {qw.get('action', '')[:100]}")
        md_lines.append("")

    coverage = data.get("couverture_cdc", {})
    if coverage:
        md_lines.append("## Couverture CdC")
        for domain, status in coverage.items():
            icon = "✓" if status == "OK" else ("~" if status == "PARTIEL" else "✗")
            md_lines.append(f"- {icon} {domain} : {status}")

    md_path = REPORTS_DIR / f"rapport_architecte_{today}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[Architecte] MD → {md_path}")
    print(f"[Architecte] {briefings_generated} briefings auto-générés.")


if __name__ == "__main__":
    run_architecte()
