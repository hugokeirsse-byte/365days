#!/usr/bin/env python3
"""
Cerveau perpétuel SVG Packs / Etsy Digital Downloads — tendances Cricut/Silhouette.

Analyse ce qui se vend sur Etsy pour les SVG packs destinés aux machines de découpe
(Cricut, Silhouette Cameo) afin d'identifier les niches et thèmes les plus porteurs.

Plateformes : Etsy (primary, digital downloads)
Machines cibles : Cricut Maker/Joy, Silhouette Cameo

Cron : dimanche 04h UTC
Variables d'env : SVG_ANGLE (override)
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call, get_previous_propositions

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "data" / "reports"

ANGLES_SVG = [
    "etsy_bestsellers_svg",          # top ventes SVG Etsy toutes catégories
    "seasonal_trending_svg",          # SVG saisonniers et tendances du moment
    "cricut_niche_underserved",       # niches sous-servies sur Cricut/Design Space
    "silhouette_specific_demand",     # besoins spécifiques Silhouette Cameo
    "monogram_personalization_surge", # boom personnalisation et monogrammes
    "svg_bundle_strategy",            # stratégie bundles et packs multi-éléments
    "holiday_evergreen_svg",          # SVG evergreen vs saisonniers — équilibre idéal
]


def run():
    today = date.today().isoformat()
    week = date.today().isocalendar()[1]
    angle = os.environ.get("SVG_ANGLE") or ANGLES_SVG[week % len(ANGLES_SVG)]

    previous = get_previous_propositions("products/svg_packs", "svg_trends")
    print(f"[SVG Brain] Angle: {angle} | Semaine: {week}")

    system_prompt = f"""Tu es un expert en SVG packs pour Cricut et Silhouette et en vente Etsy Digital Downloads.
Tu analyses les tendances du marché SVG pour identifier les opportunités pour un créateur solo.

{previous}

ANGLE D'ANALYSE : {angle}

RÈGLES STRATÉGIQUES :
- LANGUE : Anglais uniquement pour les titres Etsy et descriptions (marché international).
  Exception prouvée : si une niche locale spécifique génère clairement plus de revenus en langue locale.
- RÉHABILITATION : Cherche des packs SVG très vendus mais mal notés sur Etsy.
  Raison habituelle : SVG trop complexes pour Cricut Design Space, pas de fichier DXF, taille
  incorrecte, pas de support. Une version qui corrige ça face à la concurrence = vente garantie.
- Concentre-toi sur ce qu'un créateur solo peut produire avec Python svgwrite en 1-2 jours.

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "date": "{today}",
  "angle": "{angle}",
  "niches_tendance": [
    {{
      "niche": "...",
      "type_svg": "mandala|floral|animal|quote|monogram|seasonal|geometric|character",
      "machine_cible": "Cricut|Silhouette|both",
      "croissance": "explosif|fort|stable",
      "saturation": "faible|moyenne|forte",
      "prix_moyen_usd": 3.50,
      "nb_elements_optimal": 20,
      "pourquoi_ca_marche": "...",
      "concurrent_faible_notes": "..."
    }}
  ],
  "packs_a_rehabiliter": [
    {{
      "niche": "...",
      "probleme": "...",
      "opportunite": "..."
    }}
  ],
  "recommandation_principale": "..."
}}
JSON uniquement."""

    user_prompt = f"""Analyse les tendances du marché SVG packs pour Etsy Digital Downloads, semaine {week} de {today[:4]}.
Angle : {angle}

Focus sur :
- Etsy (plateforme principale, prix 1-8 USD par pack SVG)
- Cricut Design Space (compatibilité requise : SVG propres, pas trop de nœuds)
- Silhouette Studio (DXF souvent requis en plus du SVG)
- Saisonnalité : quels thèmes booker maintenant pour dans 4-6 semaines
- Ce qu'un créateur solo peut produire avec Python svgwrite (formes vectorielles nettes)

Identifie les 5-7 meilleures niches avec données marché précises.
Propose 2-3 packs à réhabiliter (vendus mais mal notés, problème technique corrigeable)."""

    response = llm_call("stratege", system_prompt, user_prompt, temperature=0.75, max_tokens=3000)
    if not response:
        print("[SVG Brain] Échec LLM.", file=sys.stderr)
        sys.exit(1)

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]

    try:
        data = json.loads(clean.strip())
    except Exception as e:
        print(f"[SVG Brain] JSON invalide: {e}", file=sys.stderr)
        sys.exit(1)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"svg_trends_{today}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    niches = data.get("niches_tendance", [])
    recos = data.get("packs_a_rehabiliter", [])
    recommandation = data.get("recommandation_principale", "")

    md = [
        f"# SVG Brain — {today} (angle: {angle})",
        "",
        "## Niches en tendance",
    ]
    for n in niches[:5]:
        md.append(
            f"- **{n.get('niche')}** ({n.get('type_svg')}) — "
            f"{n.get('croissance')} | saturation: {n.get('saturation')} | "
            f"~${n.get('prix_moyen_usd')} | {n.get('pourquoi_ca_marche', '')[:80]}"
        )
    if recos:
        md += ["", "## Packs à réhabiliter"]
        for r in recos:
            md.append(f"- **{r.get('niche')}** — problème: {r.get('probleme')} → {r.get('opportunite')}")
    md += [
        "",
        "## Recommandation principale",
        recommandation,
    ]
    (REPORTS_DIR / f"svg_trends_{today}.md").write_text("\n".join(md), encoding="utf-8")

    print(f"[SVG Brain] ✓ → {out_path}")
    print(f"[SVG Brain] Recommandation: {recommandation[:120]}")


if __name__ == "__main__":
    run()
