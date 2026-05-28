#!/usr/bin/env python3
"""
Éclaireur Bestsellers — Market intelligence agent.

Simulates Amazon KDP / Etsy bestseller research for our niches via Gemini.
Uses rotating angle (get_angle) to vary focus each week.

Outputs:
  data/reports/rapport_eclaireur_YYYY-MM-DD.json   (structured data)
  data/reports/rapport_eclaireur_YYYY-MM-DD.md     (human-readable report)

Runs every Tuesday at 03h UTC via .github/workflows/agent_eclaireur.yml
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.lib.brain_utils import llm_call, get_angle, get_temperature

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "data" / "reports"

# Our current product types — context for the LLM
OUR_NICHES = [
    "coloring books (adult, kawaii, cottagecore, mystical)",
    "low-content KDP books (journals, planners, notebooks)",
    "card games (educational, party, niche interest)",
    "STL files for 3D printing (decorative, functional, collectible)",
    "printable digital products (stationery, worksheets, templates)",
    "POD merch (t-shirts, tote bags, mugs with niche designs)",
]

# --------------------------------------------------------------------------- #
# LLM calls
# --------------------------------------------------------------------------- #

def generate_market_intelligence(today: str, week_number: int) -> str:
    angle = get_angle("prospecteur")
    temperature = get_temperature("prospecteur")

    print(f"[Éclaireur] Semaine {week_number} | Angle : {angle[:60]}...")

    system = """Tu es l'Éclaireur Bestsellers de l'Usine 365days — un agent de market intelligence spécialisé sur Amazon KDP et Etsy.
Tu simules une analyse approfondie des meilleures ventes actuelles sur ces plateformes pour des produits numériques et physiques de niche.

Ton analyse doit être :
- Basée sur des patterns réels de marchés (tu connais le marché KDP/Etsy en détail)
- Actionnable immédiatement pour une équipe de production de 1 personne
- Focalisée sur les niches à faible concurrence mais forte demande
- Orientée sur ce qui SE VEND MAINTENANT, pas des théories

Réponds UNIQUEMENT en JSON valide, sans markdown, sans explication. Format exact :
{
  "analyse_date": "YYYY-MM-DD",
  "semaine": N,
  "angle_semaine": "...",
  "top_niches": [
    {
      "keyword": "mot-clé principal",
      "bsr_estimate": "1000-5000",
      "competition_level": "faible|modérée|forte",
      "monthly_searches": "5000-15000",
      "avg_price": "8.99",
      "platform": "KDP|Etsy|both",
      "why_now": "Raison précise pourquoi cette niche performe maintenant",
      "product_angle": "Notre angle spécifique pour se démarquer"
    }
  ],
  "trending_titles": [
    {
      "title": "Titre exact ou style",
      "platform": "KDP|Etsy",
      "why_performing": "Explication courte",
      "our_equivalent": "Ce qu'on pourrait faire"
    }
  ],
  "gaps": [
    {
      "gap_description": "Description du gap",
      "search_volume": "estimation",
      "why_underserved": "Pourquoi peu de bons résultats",
      "opportunity_score": 8
    }
  ],
  "recommendations": [
    {
      "product_type": "coloring|lowcontent|card_game|stl|merch",
      "title": "Titre suggéré",
      "niche": "niche ciblée",
      "why_now": "Justification urgente",
      "production_effort": "1-3 jours",
      "revenue_potential": "50-200€/mois",
      "platform": "KDP|Etsy|both"
    }
  ]
}"""

    user = f"""Date d'analyse : {today} (semaine {week_number})

ANGLE DE CETTE SEMAINE : {angle}

PRODUITS QUE NOUS PRODUISONS DÉJÀ :
{chr(10).join(f"- {n}" for n in OUR_NICHES)}

Effectue une analyse bestsellers complète sur Amazon KDP et Etsy pour ces types de produits.
Identifie :
1. Les 10 niches les plus prometteuses RIGHT NOW avec keyword, BSR estimé, niveau de concurrence, pourquoi maintenant
2. Les 5 titres/styles qui performent bien et pourquoi
3. Les 5 gaps du marché (recherches avec peu de bons résultats)
4. Les 3 produits concrets à créer en priorité cette semaine

Focus sur des niches inexploitées ou sous-exploitées, pas les géants saturés."""

    return llm_call("prospecteur", system, user, temperature=temperature, max_tokens=4000)


def generate_md_report(data: dict, today: str) -> str:
    """Converts JSON data to a readable Markdown report."""
    week = data.get("semaine", "?")
    angle = data.get("angle_semaine", "")

    lines = [
        f"# Rapport Éclaireur Bestsellers — {today} (semaine {week})",
        "",
        f"**Angle de la semaine :** {angle}",
        "",
        "---",
        "",
        "## Top 10 Niches Opportunistes",
        "",
    ]

    for i, niche in enumerate(data.get("top_niches", []), 1):
        lines += [
            f"### {i}. `{niche.get('keyword', '?')}` — {niche.get('platform', '?')}",
            f"- **BSR estimé :** {niche.get('bsr_estimate', '?')}",
            f"- **Concurrence :** {niche.get('competition_level', '?')}",
            f"- **Recherches/mois :** {niche.get('monthly_searches', '?')}",
            f"- **Prix moyen :** {niche.get('avg_price', '?')} €",
            f"- **Pourquoi maintenant :** {niche.get('why_now', '?')}",
            f"- **Notre angle :** {niche.get('product_angle', '?')}",
            "",
        ]

    lines += ["---", "", "## Titres/Styles en Tête", ""]
    for item in data.get("trending_titles", []):
        lines += [
            f"- **{item.get('title', '?')}** ({item.get('platform', '?')})",
            f"  {item.get('why_performing', '')}",
            f"  → Notre version : {item.get('our_equivalent', '')}",
            "",
        ]

    lines += ["---", "", "## Gaps du Marché (opportunités)", ""]
    for i, gap in enumerate(data.get("gaps", []), 1):
        score = gap.get("opportunity_score", "?")
        lines += [
            f"### Gap {i} — Score {score}/10",
            f"**{gap.get('gap_description', '?')}**",
            f"- Volume : {gap.get('search_volume', '?')}",
            f"- Pourquoi sous-servi : {gap.get('why_underserved', '?')}",
            "",
        ]

    lines += ["---", "", "## Recommandations Produits (cette semaine)", ""]
    for i, rec in enumerate(data.get("recommendations", []), 1):
        lines += [
            f"### {i}. {rec.get('title', '?')} [{rec.get('product_type', '?').upper()}]",
            f"- **Niche :** {rec.get('niche', '?')}",
            f"- **Plateforme :** {rec.get('platform', '?')}",
            f"- **Pourquoi maintenant :** {rec.get('why_now', '?')}",
            f"- **Effort production :** {rec.get('production_effort', '?')}",
            f"- **Potentiel :** {rec.get('revenue_potential', '?')}",
            "",
        ]

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# JSON extraction helper
# --------------------------------------------------------------------------- #

def extract_json(text: str) -> dict:
    """Extracts first JSON object from LLM response."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # Try extracting JSON block
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main() -> int:
    today = date.today().isoformat()
    week_number = date.today().isocalendar()[1]

    print(f"[Éclaireur Bestsellers] {today} — semaine {week_number}")

    # 1. Call LLM
    print("[Éclaireur] Appel LLM pour analyse marché...")
    raw_response = generate_market_intelligence(today, week_number)

    if not raw_response:
        print("[Éclaireur] ERREUR : LLM n'a retourné aucun contenu.")
        return 1

    # 2. Parse JSON
    data = extract_json(raw_response)
    if not data:
        print("[Éclaireur] AVERTISSEMENT : impossible de parser le JSON — sauvegarde raw.")
        data = {
            "analyse_date": today,
            "semaine": week_number,
            "raw_response": raw_response,
            "top_niches": [],
            "trending_titles": [],
            "gaps": [],
            "recommendations": [],
        }
    else:
        data["analyse_date"] = today
        data["semaine"] = week_number

    # 3. Write outputs
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS_DIR / f"rapport_eclaireur_{today}.json"
    md_path = REPORTS_DIR / f"rapport_eclaireur_{today}.md"

    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[Éclaireur] JSON : {json_path}")

    md_content = generate_md_report(data, today)
    md_path.write_text(md_content, encoding="utf-8")
    print(f"[Éclaireur] Rapport MD : {md_path}")

    print(f"[Éclaireur] {len(data.get('top_niches', []))} niches, "
          f"{len(data.get('recommendations', []))} recommandations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
