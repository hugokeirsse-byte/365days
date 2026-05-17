"""
Dashboard d'inventaire — scanne products/ et affiche ce qui est prêt à uploader.

Usage :
    python scripts/inventory_dashboard.py            # vue d'ensemble
    python scripts/inventory_dashboard.py --details  # détail par pipeline

Affiche pour chaque pipeline :
- Nombre de designs/livres produits
- Plateformes cibles
- CSV bulk upload disponibles
- Estimation revenus mensuels si uploadés
"""

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"

PIPELINE_INFO = {
    "svg_packs": {
        "label": "SVG Packs Cricut",
        "platform": "Etsy",
        "unit": "ZIP",
        "avg_price_eur": 4.99,
        "estimated_sales_per_month_per_design": 0.6,
    },
    "tumbler_wraps": {
        "label": "Tumbler Wraps Sublimation",
        "platform": "Etsy",
        "unit": "wrap",
        "avg_price_eur": 3.99,
        "estimated_sales_per_month_per_design": 1.0,
    },
    "cultural_arbitrage": {
        "label": "Cultural Arbitrage (mots intraduisibles)",
        "platform": "Etsy + Redbubble",
        "unit": "design",
        "avg_price_eur": 4.50,
        "estimated_sales_per_month_per_design": 0.4,
    },
    "iheart": {
        "label": "I Heart X (avec illustration de fond)",
        "platform": "Etsy + Printful",
        "unit": "design",
        "avg_price_eur": 3.50,
        "estimated_sales_per_month_per_design": 0.7,
    },
    "literal_idioms": {
        "label": "Literal Idioms (humour polyglotte)",
        "platform": "Etsy + Redbubble",
        "unit": "design",
        "avg_price_eur": 4.99,
        "estimated_sales_per_month_per_design": 0.3,
    },
    "coloring_books": {
        "label": "Coloring Books KDP",
        "platform": "KDP + Etsy",
        "unit": "livre",
        "avg_price_eur": 7.99,
        "estimated_sales_per_month_per_design": 4.0,
    },
    "viral_formats": {
        "label": "Viral Formats (50 concepts moteurs)",
        "platform": "Etsy + Printful + Redbubble",
        "unit": "design",
        "avg_price_eur": 3.99,
        "estimated_sales_per_month_per_design": 0.5,
    },
    "iheart_v2": {
        "label": "I Heart V2 (scène DANS le cœur)",
        "platform": "Etsy + Printful + Redbubble",
        "unit": "design",
        "avg_price_eur": 4.50,
        "estimated_sales_per_month_per_design": 0.6,
    },
    "stl_parametric": {
        "label": "STL Parametric (Cults3D + Printables)",
        "platform": "Cults3D + Printables",
        "unit": "STL",
        "avg_price_eur": 1.80,
        "estimated_sales_per_month_per_design": 1.5,
    },
    "bible_verses": {
        "label": "Bible Verses (christian wall art)",
        "platform": "Etsy + Redbubble",
        "unit": "design",
        "avg_price_eur": 4.99,
        "estimated_sales_per_month_per_design": 0.7,
    },
    "cope_pack": {
        "label": "COPE Multi-Format (witchy etc.)",
        "platform": "Etsy + Pinterest + Society6",
        "unit": "design",
        "avg_price_eur": 4.99,
        "estimated_sales_per_month_per_design": 0.4,
    },
}


def count_designs(pipeline_dir: Path) -> tuple[int, list[str]]:
    """Retourne (nombre de designs avec metadata.json, liste des dossiers)."""
    if not pipeline_dir.exists():
        # Fallback : pour cope_pack et autres, regarde sous-dossiers racine de products/
        return 0, []
    designs = list(pipeline_dir.rglob("metadata.json"))
    return len(designs), [str(d.parent.relative_to(pipeline_dir)) for d in designs]


def count_stl_files(pipeline_dir: Path) -> int:
    if not pipeline_dir.exists():
        return 0
    return len(list(pipeline_dir.rglob("*.stl")))


def count_cope_pack_designs() -> int:
    """COPE pack n'a pas de sous-dossier dédié — produits directement sous products/<niche>/."""
    count = 0
    for d in PRODUCTS_DIR.iterdir():
        if not d.is_dir():
            continue
        # Skip les pipelines connus
        if d.name in PIPELINE_INFO:
            continue
        # Compte les metadata.json
        count += len(list(d.rglob("metadata.json")))
    return count


def count_csv_files(pipeline_dir: Path) -> int:
    if not pipeline_dir.exists():
        return 0
    return len(list(pipeline_dir.rglob("*.csv")))


def count_pdfs(pipeline_dir: Path) -> int:
    if not pipeline_dir.exists():
        return 0
    return len(list(pipeline_dir.rglob("*.pdf")))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--details", action="store_true")
    args = parser.parse_args()

    print("=" * 70)
    print("📦 INVENTAIRE PRODUITS — prêt à uploader")
    print("=" * 70)

    if not PRODUCTS_DIR.exists():
        print(f"\n  ✗ Dossier {PRODUCTS_DIR} inexistant.")
        print(f"  Lance d'abord un pipeline depuis Actions UI.")
        return 1

    total_designs = 0
    total_revenue_low = 0
    total_revenue_high = 0

    for key, info in PIPELINE_INFO.items():
        pipeline_dir = PRODUCTS_DIR / key
        count, designs = count_designs(pipeline_dir)
        pdfs = count_pdfs(pipeline_dir)
        stls = count_stl_files(pipeline_dir)
        if key == "coloring_books":
            unit_count = pdfs
        elif key == "stl_parametric":
            unit_count = stls
        elif key == "cope_pack":
            unit_count = count_cope_pack_designs()
        else:
            unit_count = count
        csvs = count_csv_files(pipeline_dir)

        if unit_count == 0:
            status_icon = "○"
        else:
            status_icon = "●"

        print(f"\n  {status_icon} {info['label']}")
        print(f"     Plateforme  : {info['platform']}")
        print(f"     Inventaire  : {unit_count} {info['unit']}(s) produits")
        if csvs:
            print(f"     CSV upload  : {csvs} fichier(s)")
        if unit_count:
            sales_low = unit_count * info["estimated_sales_per_month_per_design"] * 0.5
            sales_high = unit_count * info["estimated_sales_per_month_per_design"] * 1.5
            rev_low = sales_low * info["avg_price_eur"] * 0.7  # 70% net après fees
            rev_high = sales_high * info["avg_price_eur"] * 0.85
            print(f"     Revenu est. : {rev_low:.0f}–{rev_high:.0f} €/mois "
                  f"(si uploadé sur {info['platform']})")
            total_designs += unit_count
            total_revenue_low += rev_low
            total_revenue_high += rev_high

        if args.details and designs:
            for d in designs[:5]:
                print(f"        - {d}")
            if len(designs) > 5:
                print(f"        … et {len(designs) - 5} autres")

    print(f"\n{'=' * 70}")
    print(f"  📊 TOTAL : {total_designs} produits prêts à uploader")
    if total_revenue_low:
        print(f"  💰 Potentiel : {total_revenue_low:.0f}–{total_revenue_high:.0f} €/mois "
              f"(estimation honnête, 6 mois après upload)")
    print(f"{'=' * 70}")

    # Suggestions next actions
    print("\n🎯 PROCHAINES ACTIONS")
    empty_pipelines = []
    for key, info in PIPELINE_INFO.items():
        count, _ = count_designs(PRODUCTS_DIR / key)
        if count == 0:
            empty_pipelines.append((key, info))

    if empty_pipelines:
        print("\n  Pipelines vides à lancer (UI Actions ou .triggers/) :")
        for key, info in empty_pipelines:
            print(f"    → produce_{key} ({info['label']})")
    else:
        print("  Tous les pipelines ont du stock. Focus : upload sur les plateformes.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
