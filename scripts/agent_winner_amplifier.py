"""
Agent WINNER AMPLIFIER — boucle 3 du système (apprentissage).

Lit data/sales_feedback.csv (rempli par Hugo chaque dimanche) et :

1. Identifie les designs qui ONT vendu (winners)
2. Identifie les niches/formats/audiences qui sortent du lot
3. Génère un fichier data/winner_strategy.json avec :
   - Top 10 winners (designs)
   - Top 5 winning niches
   - Top 5 winning format families
   - Recommandations de production : "génère 10 variantes de [design winner]"
   - Anti-recommendations : "ne plus produire dans [niche] qui flop depuis 60j"

4. Optionnel : écrit des .triggers/ pour relancer automatiquement la
   production des winners (selon STRATEGY=auto).

Format `data/sales_feedback.csv` attendu :
  date,platform,design_id,niche,format_family,units_sold,revenue_eur,notes
  2026-05-25,etsy,iheart_v2_fishing_vintage,fishing,iheart_v2,3,13.50,décollage rapide
  2026-05-25,etsy,viral_diagnosed_terminal_cats_v0,cats,medical,5,19.95,
  ...

Cron : dimanche 22h UTC (juste après que Hugo ait fait son point hebdo)
"""

import csv
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SALES_CSV = DATA_DIR / "sales_feedback.csv"

# Seuils
WINNER_MIN_UNITS = 2   # design qui vend ≥2x = winner
WINNER_MIN_REVENUE_EUR = 8.0
LOSER_DAYS_THRESHOLD = 60  # niche sans vente depuis 60j = à descorer


def load_sales() -> list[dict]:
    """Charge sales_feedback.csv. Retourne liste vide si absent."""
    if not SALES_CSV.exists():
        return []
    rows = []
    with SALES_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row["units_sold"] = int(row.get("units_sold", 0) or 0)
                row["revenue_eur"] = float(row.get("revenue_eur", 0) or 0)
                rows.append(row)
            except (ValueError, KeyError):
                continue
    return rows


def identify_winners(sales: list[dict]) -> list[dict]:
    """Agrège par design_id, retourne ceux qui ont vendu assez."""
    by_design = defaultdict(lambda: {"units": 0, "revenue": 0.0,
                                       "platforms": set(), "first_sale": None,
                                       "last_sale": None, "niche": "",
                                       "format_family": ""})
    for row in sales:
        d = by_design[row["design_id"]]
        d["units"] += row["units_sold"]
        d["revenue"] += row["revenue_eur"]
        d["platforms"].add(row.get("platform", ""))
        d["niche"] = row.get("niche", "")
        d["format_family"] = row.get("format_family", "")
        date = row.get("date", "")
        if date:
            if not d["first_sale"] or date < d["first_sale"]:
                d["first_sale"] = date
            if not d["last_sale"] or date > d["last_sale"]:
                d["last_sale"] = date

    winners = []
    for design_id, d in by_design.items():
        if d["units"] >= WINNER_MIN_UNITS or d["revenue"] >= WINNER_MIN_REVENUE_EUR:
            winners.append({
                "design_id": design_id,
                "total_units": d["units"],
                "total_revenue_eur": round(d["revenue"], 2),
                "platforms": sorted(d["platforms"]),
                "niche": d["niche"],
                "format_family": d["format_family"],
                "first_sale": d["first_sale"],
                "last_sale": d["last_sale"],
            })
    winners.sort(key=lambda x: -x["total_revenue_eur"])
    return winners


def top_winning_niches(sales: list[dict], top_n: int = 5) -> list[dict]:
    by_niche = defaultdict(lambda: {"units": 0, "revenue": 0.0, "designs": set()})
    for row in sales:
        n = row.get("niche", "")
        if not n:
            continue
        by_niche[n]["units"] += row["units_sold"]
        by_niche[n]["revenue"] += row["revenue_eur"]
        by_niche[n]["designs"].add(row.get("design_id", ""))
    ranked = sorted(by_niche.items(), key=lambda x: -x[1]["revenue"])
    return [
        {
            "niche": n,
            "total_units": v["units"],
            "total_revenue_eur": round(v["revenue"], 2),
            "unique_designs": len(v["designs"]),
            "avg_revenue_per_design": round(
                v["revenue"] / max(len(v["designs"]), 1), 2),
        }
        for n, v in ranked[:top_n]
    ]


def top_winning_families(sales: list[dict], top_n: int = 5) -> list[dict]:
    by_fam = defaultdict(lambda: {"units": 0, "revenue": 0.0, "designs": set()})
    for row in sales:
        f = row.get("format_family", "")
        if not f:
            continue
        by_fam[f]["units"] += row["units_sold"]
        by_fam[f]["revenue"] += row["revenue_eur"]
        by_fam[f]["designs"].add(row.get("design_id", ""))
    ranked = sorted(by_fam.items(), key=lambda x: -x[1]["revenue"])
    return [
        {
            "format_family": f,
            "total_units": v["units"],
            "total_revenue_eur": round(v["revenue"], 2),
            "unique_designs": len(v["designs"]),
        }
        for f, v in ranked[:top_n]
    ]


def identify_losers(sales: list[dict]) -> list[str]:
    """Niches qui n'ont pas vendu depuis LOSER_DAYS_THRESHOLD jours."""
    cutoff = (datetime.utcnow() - timedelta(days=LOSER_DAYS_THRESHOLD)).strftime("%Y-%m-%d")
    by_niche_last_sale = defaultdict(str)
    for row in sales:
        n = row.get("niche", "")
        date = row.get("date", "")
        if n and date and date > by_niche_last_sale[n]:
            by_niche_last_sale[n] = date
    return [
        n for n, last in by_niche_last_sale.items()
        if last < cutoff
    ]


def generate_recommendations(winners: list[dict]) -> list[dict]:
    """Pour chaque winner, propose 10 variantes à produire."""
    recos = []
    for w in winners[:10]:  # top 10 winners
        # Recommandation : produire 10 variantes du même format × niches voisines
        recos.append({
            "winner_design_id": w["design_id"],
            "winning_niche": w["niche"],
            "winning_format_family": w["format_family"],
            "action": "produce_10_variants",
            "rationale": (
                f"Design vend bien ({w['total_units']} units, "
                f"{w['total_revenue_eur']:.2f} €). Produire 10 variantes "
                f"de la même family avec niches voisines."
            ),
            "suggested_pipeline_command": _suggest_pipeline_for(w),
        })
    return recos


def _suggest_pipeline_for(winner: dict) -> str:
    """Heuristique : depuis le design_id, devine quel pipeline et quels params."""
    design_id = winner["design_id"]
    if design_id.startswith("viral_"):
        return (f"produce_viral_formats avec FORMAT_FAMILY="
                f"{winner['format_family']} et MAX_NICHES=10")
    if design_id.startswith("iheart_v2_"):
        return "produce_iheart_v2 avec MAX_NICHES=10 MAX_STYLES=3"
    if design_id.startswith("iheart_"):
        return "produce_iheart_x avec MAX_NICHES=10"
    if "cultural" in design_id or design_id.startswith("hygge") or \
       design_id.startswith("ikigai"):
        return "produce_cultural_arbitrage avec MAX_EXPRESSIONS=10"
    if design_id.startswith("idiom_"):
        return "produce_literal_idioms avec MAX_IDIOMS=10"
    if "tumbler" in design_id:
        return "produce_tumbler_wraps avec MAX_DESIGNS=10"
    if design_id.startswith("stl_"):
        return "produce_stl_parametric avec MAX_VARIANTS=15"
    return "pipeline indéterminé — vérifier design_id"


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("WINNER AMPLIFIER — boucle apprentissage ventes")
    print("=" * 70)

    sales = load_sales()
    if not sales:
        print(f"\n⊝ {SALES_CSV} vide ou inexistant.")
        print("   Hugo doit remplir le CSV avec ses ventes hebdomadaires.")
        print("   Format : date,platform,design_id,niche,format_family,units_sold,revenue_eur,notes")
        # Crée un template si absent
        if not SALES_CSV.exists():
            SALES_CSV.write_text(
                "date,platform,design_id,niche,format_family,units_sold,revenue_eur,notes\n"
            )
            print(f"   → Template créé : {SALES_CSV}")
        return 0

    print(f"\n{len(sales)} ventes chargées depuis {SALES_CSV}")

    winners = identify_winners(sales)
    top_niches = top_winning_niches(sales)
    top_families = top_winning_families(sales)
    losers = identify_losers(sales)
    recommendations = generate_recommendations(winners)

    print(f"\n🏆 {len(winners)} winners identifiés")
    print(f"📈 {len(top_niches)} top niches")
    print(f"🎨 {len(top_families)} top families")
    if losers:
        print(f"⚠ {len(losers)} losers à descorer : {', '.join(losers[:5])}")

    if winners:
        print(f"\nTOP 5 WINNERS :")
        for w in winners[:5]:
            print(f"  → {w['design_id']:<45} {w['total_units']:>3}u  "
                  f"{w['total_revenue_eur']:>7.2f}€")

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_sales_rows": len(sales),
        "winners": winners,
        "top_winning_niches": top_niches,
        "top_winning_format_families": top_families,
        "losers_niches": losers,
        "recommendations": recommendations,
    }
    out_path = DATA_DIR / "winner_strategy.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n→ Sauvegardé : {out_path}")

    if recommendations:
        print(f"\n🎯 PROCHAINES PRODUCTIONS RECOMMANDÉES :")
        for r in recommendations[:5]:
            print(f"  {r['suggested_pipeline_command']}")
            print(f"  ({r['rationale'][:100]})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
