"""
Agent OPPORTUNITY HUNTER — le cerveau du système.

Croise 4 dimensions pour identifier les meilleures opportunités de
production de la semaine :
  STYLE  × TREND  × ÉVÉNEMENT  × CATÉGORIE PRODUIT

Lit :
- data/trends.json           (Trendhunter v2 — niches émergentes Reddit)
- data/upcoming_events.json  (Seasonal Calendar — événements 12 semaines)
- data/styles_du_moment.json (Styles graphiques porteurs 2026)

Sortie : data/opportunities.json — top 10-20 opportunités scorées,
chacune avec : style + trend + event + catégorie produit + brief
de production prêt à lancer.

Modes :
- Mode dégradé (sans Gemini) : scoring heuristique pur (combinatoire +
  facteurs : intensité event, score trend, popularité style, croisement
  saturation). Tourne en quelques secondes.
- Mode optimal (avec GEMINI_API_KEY) : passe le top 50 à Gemini Pro
  pour synthèse intelligente + brief créatif détaillé.

Cron suggéré : tous les lundis matin (juste après Trendhunter et
Seasonal Planner), pour orienter la production de la semaine.
"""

import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# Catégories de produits dans lesquels on opère
PRODUCT_CATEGORIES = {
    "coloring_books":      {"effort": "medium",   "marge": "high", "marche": "Etsy + KDP"},
    "tumbler_wraps":       {"effort": "low",      "marge": "very_high", "marche": "Etsy"},
    "mug_pod":             {"effort": "low",      "marge": "medium", "marche": "Etsy+Printful"},
    "t_shirt_pod":         {"effort": "low",      "marge": "medium", "marche": "Etsy+Printful+Redbubble"},
    "wall_art_prints":     {"effort": "low",      "marge": "very_high", "marche": "Etsy + Society6"},
    "stickers":            {"effort": "very_low", "marge": "high", "marche": "Etsy + Redbubble"},
    "ebook_fiction":       {"effort": "high",     "marge": "high", "marche": "KDP + Audible"},
    "ebook_non_fiction":   {"effort": "high",     "marge": "high", "marche": "KDP"},
    "stl_3d":              {"effort": "medium",   "marge": "very_high", "marche": "Cults3D + Printables"},
    "tarot_oracle":        {"effort": "medium",   "marge": "high", "marche": "MakePlayingCards + Etsy"},
    "notion_templates":    {"effort": "low",      "marge": "very_high", "marche": "Gumroad + Etsy"},
    "audio_lofi":          {"effort": "low",      "marge": "long_tail", "marche": "Spotify"},
    "sleep_stories":       {"effort": "medium",   "marge": "long_tail", "marche": "Spotify"},
}

# Mapping : pour chaque style, quels types de produits sont idéaux
STYLE_PRODUCT_FIT = {
    "cute_kawaii_line_art": ["coloring_books", "stickers", "mug_pod", "tumbler_wraps"],
    "vintage_botanical":    ["wall_art_prints", "tumbler_wraps", "ebook_non_fiction"],
    "dark_academia":        ["ebook_fiction", "tumbler_wraps", "t_shirt_pod", "wall_art_prints", "stickers"],
    "cottagecore_watercolor": ["coloring_books", "tumbler_wraps", "wall_art_prints"],
    "y2k_aesthetic":        ["t_shirt_pod", "stickers", "wall_art_prints"],
    "pastel_goth":          ["t_shirt_pod", "stickers", "coloring_books", "tumbler_wraps"],
    "minimalist_line_tattoo": ["stickers", "wall_art_prints", "t_shirt_pod"],
    "folk_art":             ["wall_art_prints", "tumbler_wraps"],
    "anime_manga_line":     ["coloring_books", "t_shirt_pod", "stickers"],
    "art_nouveau":          ["wall_art_prints", "tarot_oracle", "ebook_non_fiction"],
    "lo_fi_chill":          ["wall_art_prints", "audio_lofi", "stickers"],
    "retro_70s":            ["t_shirt_pod", "tumbler_wraps", "wall_art_prints", "stickers"],
    "minimalist_scandinavian": ["wall_art_prints", "notion_templates", "mug_pod"],
    "vintage_americana":    ["wall_art_prints", "t_shirt_pod", "mug_pod"],
    "art_deco_gold":        ["wall_art_prints"],
    "watercolor_loose":     ["wall_art_prints"],
    "tribal_geometric":     ["wall_art_prints", "t_shirt_pod"],
}


@dataclass
class Opportunity:
    style_key: str
    style_name: str
    trend_keyword: str
    trend_score: float
    event_name: str
    event_date: str
    event_days_away: int
    event_intensity: int
    product_category: str
    product_effort: str
    product_marge: str
    composite_score: float
    brief: str
    estimated_roi_eur_monthly: str


def load_json(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text())


def score_opportunity(style: dict, trend: dict, event: dict, product_cat: str) -> float:
    """Score composite — plus haut = meilleure opportunité.

    Facteurs :
    + popularité du style 2026 (1-5)
    + score du trend (Reddit)
    + intensité de l'événement (1-5)
    + proximité de l'événement (boost si proche, mais malus si trop urgent <14j)
    + alignement style/produit (déjà filtré en amont)
    - saturation du style (malus si trop saturé)
    + effort produit (boost effort low)
    """
    score = 0.0

    pop = style.get("popularity_2026", 3)
    sat = style.get("saturation", 3)
    score += pop * 10
    score -= sat * 5  # malus saturation

    score += min(trend.get("score", 0) / 100, 10)  # trend Reddit score normalisé

    intensity = event.get("intensity", 3)
    days = event.get("days_to_event", 60)
    score += intensity * 8
    # Sweet spot : 30-60 jours d'anticipation
    if 20 <= days <= 70:
        score += 10
    elif days < 14:
        score -= 8  # trop urgent
    elif days > 90:
        score -= 5  # trop loin

    # Effort : faible = boost
    effort_map = {"very_low": 8, "low": 5, "medium": 2, "high": -3}
    score += effort_map.get(PRODUCT_CATEGORIES[product_cat]["effort"], 0)

    # Marge : haute = boost
    marge_map = {"very_high": 6, "high": 4, "medium": 2, "long_tail": 1}
    score += marge_map.get(PRODUCT_CATEGORIES[product_cat]["marge"], 0)

    return round(score, 2)


def estimate_roi(product_cat: str, intensity: int) -> str:
    """ROI mensuel estimé en euros pour un design top de la catégorie."""
    base = {
        "tumbler_wraps":   (50, 200),
        "stickers":        (20, 80),
        "mug_pod":         (30, 120),
        "t_shirt_pod":     (40, 150),
        "wall_art_prints": (40, 180),
        "coloring_books":  (50, 250),
        "ebook_fiction":   (100, 500),
        "ebook_non_fiction": (80, 350),
        "stl_3d":          (30, 150),
        "tarot_oracle":    (60, 250),
        "notion_templates": (40, 180),
        "audio_lofi":      (20, 150),
        "sleep_stories":   (30, 200),
    }.get(product_cat, (20, 100))
    boost = 1 + (intensity / 10)
    return f"{int(base[0] * boost)}-{int(base[1] * boost)} €/mois"


def generate_brief(style_name: str, trend_keyword: str, event: dict,
                   product_cat: str, score: float) -> str:
    intensity = event.get("intensity", 3)
    days = event.get("days_to_event", 60)
    urgency = ("DÉMARRER MAINTENANT" if days < 30
               else "Démarrer cette semaine" if days < 50
               else "Planifier dans 2-3 semaines")
    return (
        f"[{urgency}] Produire un/des {product_cat.replace('_', ' ')} sur le "
        f"thème '{trend_keyword}' dans le style {style_name}, ciblé pour "
        f"l'événement '{event['event']}' ({event['date']}, J-{days}). "
        f"Intensité événement {intensity}/5. Score composite {score:.1f}."
    )


def hunt_opportunities() -> list[dict]:
    trends_data = load_json(DATA_DIR / "trends.json", {})
    events_data = load_json(DATA_DIR / "upcoming_events.json", [])
    styles_data = load_json(DATA_DIR / "styles_du_moment.json", {}).get("styles", {})

    if not events_data:
        print("⚠ data/upcoming_events.json absent — lance d'abord seasonal_calendar.py")
        return []
    if not styles_data:
        print("⚠ data/styles_du_moment.json absent")
        return []

    # Si pas de trends.json, on utilise trends "evergreen" prédéfinis
    evergreen_trends = [
        {"keyword": "cottagecore", "score": 500},
        {"keyword": "witchy", "score": 450},
        {"keyword": "dark academia", "score": 400},
        {"keyword": "kawaii cute", "score": 550},
        {"keyword": "minimalist line art", "score": 350},
        {"keyword": "Y2K aesthetic", "score": 400},
        {"keyword": "self-care wellness", "score": 380},
        {"keyword": "boho wildflowers", "score": 320},
        {"keyword": "vintage americana", "score": 290},
        {"keyword": "pastel goth", "score": 280},
    ]
    if isinstance(trends_data, dict) and trends_data.get("top_trending_keywords"):
        trends_list = [
            {"keyword": t["keyword"], "score": t["score"]}
            for t in trends_data["top_trending_keywords"][:30]
        ]
    else:
        trends_list = evergreen_trends

    opportunities = []
    for style_key, style in styles_data.items():
        for trend in trends_list[:15]:
            for event in events_data[:8]:  # 8 events les plus proches
                fits = STYLE_PRODUCT_FIT.get(style_key, [])
                for product_cat in fits[:3]:  # top 3 produits par style
                    score = score_opportunity(style, trend, event, product_cat)
                    if score < 25:  # filtre les scores faibles
                        continue
                    brief = generate_brief(
                        style["display_name"],
                        trend["keyword"],
                        event,
                        product_cat,
                        score,
                    )
                    roi = estimate_roi(product_cat, event.get("intensity", 3))
                    opportunities.append({
                        "style_key": style_key,
                        "style_name": style["display_name"],
                        "trend_keyword": trend["keyword"],
                        "trend_score": trend["score"],
                        "event_name": event["event"],
                        "event_date": event["date"],
                        "event_days_away": event["days_to_event"],
                        "event_intensity": event["intensity"],
                        "product_category": product_cat,
                        "product_effort": PRODUCT_CATEGORIES[product_cat]["effort"],
                        "product_marge": PRODUCT_CATEGORIES[product_cat]["marge"],
                        "product_marche": PRODUCT_CATEGORIES[product_cat]["marche"],
                        "composite_score": score,
                        "brief": brief,
                        "estimated_roi_eur_monthly": roi,
                    })

    # Dédup : 1 opportunité par triplet (style × event × product_cat)
    seen = set()
    unique = []
    for o in sorted(opportunities, key=lambda x: -x["composite_score"]):
        key = (o["style_key"], o["event_name"], o["product_category"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(o)

    return unique[:30]  # top 30


def main() -> int:
    print("=" * 70)
    print("OPPORTUNITY HUNTER — croise styles × trends × events × produits")
    print("=" * 70)

    opportunities = hunt_opportunities()
    if not opportunities:
        print("\n✗ Aucune opportunité — données manquantes.")
        print("   Lance d'abord :")
        print("   1. python scripts/lib/seasonal_calendar.py")
        print("   2. python scripts/agent_trendhunter.py (optionnel)")
        return 1

    print(f"\n{len(opportunities)} opportunités identifiées. Top 15 :\n")
    for i, o in enumerate(opportunities[:15], 1):
        marker = "🔴" if o["event_days_away"] < 30 else "🟧" if o["event_days_away"] < 50 else "🟨"
        print(f"{marker} #{i:>2}  score {o['composite_score']:.1f}  "
              f"({o['estimated_roi_eur_monthly']})")
        print(f"    {o['style_name']}")
        print(f"    × {o['trend_keyword']}")
        print(f"    × {o['event_name']} (J-{o['event_days_away']})")
        print(f"    → {o['product_category']} sur {o['product_marche']}")
        print(f"    {o['brief'][:100]}...")
        print()

    output_path = DATA_DIR / "opportunities.json"
    output_path.write_text(json.dumps({
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "opportunities_count": len(opportunities),
        "opportunities": opportunities,
    }, indent=2, default=str))
    print(f"→ Sauvegardé : {output_path}")
    print("\nProchaine étape : tu choisis une opportunité, je lance le pipeline correspondant.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
