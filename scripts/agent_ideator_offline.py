"""
Agent IDEATOR offline — brainstorm combinatoire sans LLM.

Croise toutes les dimensions disponibles pour générer 200-500 idées
de produits scorées :
  STYLE × NICHE × FORMAT_VIRAL × EVENT × PRODUCT_TYPE × AUDIENCE

Sortie : data/ideas_brainstorm.json — liste d'idées avec :
- Idée formulée en 1 ligne
- Score combinatoire (popularité × saturation inverse × event proximity)
- Lien direct vers le pipeline qui peut la produire
- Estimation revenus mensuels

Permet à Hugo de voir d'un coup d'œil 100 idées de la plus prometteuse
à la moins prometteuse, sans nécessiter de clé LLM.

Cron suggéré : mercredi 6h UTC (après les autres agents).
"""

import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# Composantes croisables
PRODUCT_TYPES = [
    {"key": "tshirt_pod", "label": "T-shirt POD", "effort": "low",
     "platforms": "Etsy+Printful+Redbubble", "marge": "medium",
     "pipeline": "produce_viral_formats / produce_iheart_v2"},
    {"key": "mug_pod", "label": "Mug POD", "effort": "low",
     "platforms": "Etsy+Printful", "marge": "medium",
     "pipeline": "produce_cope_pack / produce_viral_formats"},
    {"key": "wall_art", "label": "Wall art print", "effort": "very_low",
     "platforms": "Etsy + Society6", "marge": "very_high",
     "pipeline": "produce_cope_pack / produce_cultural_arbitrage"},
    {"key": "sticker", "label": "Sticker", "effort": "very_low",
     "platforms": "Etsy + Redbubble", "marge": "high",
     "pipeline": "produce_viral_formats / produce_iheart_v2"},
    {"key": "tumbler_wrap", "label": "Tumbler wrap", "effort": "low",
     "platforms": "Etsy sublimation", "marge": "very_high",
     "pipeline": "produce_tumbler_wraps"},
    {"key": "coloring_book", "label": "Coloring book", "effort": "medium",
     "platforms": "KDP + Etsy", "marge": "high",
     "pipeline": "produce_coloring_book + produce_kdp_cover"},
    {"key": "stl_bookmark", "label": "STL bookmark", "effort": "low",
     "platforms": "Cults3D + Printables", "marge": "very_high",
     "pipeline": "produce_stl_parametric"},
    {"key": "stl_keychain", "label": "STL keychain", "effort": "low",
     "platforms": "Cults3D + Printables", "marge": "very_high",
     "pipeline": "produce_stl_parametric"},
    {"key": "stl_coaster", "label": "STL coaster", "effort": "low",
     "platforms": "Cults3D + Printables", "marge": "very_high",
     "pipeline": "produce_stl_parametric"},
    {"key": "totebag_pod", "label": "Tote bag POD", "effort": "low",
     "platforms": "Etsy+Printful+Redbubble", "marge": "medium",
     "pipeline": "produce_viral_formats"},
    {"key": "phonecase", "label": "Phone case POD", "effort": "low",
     "platforms": "Redbubble + Society6", "marge": "low",
     "pipeline": "produce_viral_formats / produce_iheart_v2"},
    {"key": "notebook_cover", "label": "Notebook cover", "effort": "low",
     "platforms": "Redbubble + Society6", "marge": "medium",
     "pipeline": "produce_cope_pack"},
]

AUDIENCES = [
    {"key": "booktok_readers", "label": "BookTok readers",
     "buying_power": "high", "engagement": "very_high"},
    {"key": "introverts", "label": "Introverts",
     "buying_power": "medium", "engagement": "high"},
    {"key": "cat_parents", "label": "Cat parents",
     "buying_power": "very_high", "engagement": "very_high"},
    {"key": "dog_parents", "label": "Dog parents",
     "buying_power": "very_high", "engagement": "very_high"},
    {"key": "language_learners", "label": "Language learners",
     "buying_power": "medium", "engagement": "high"},
    {"key": "dnd_players", "label": "D&D players",
     "buying_power": "high", "engagement": "very_high"},
    {"key": "crocheters", "label": "Crocheters / knitters",
     "buying_power": "high", "engagement": "high"},
    {"key": "tea_coffee_lovers", "label": "Tea / coffee enthusiasts",
     "buying_power": "high", "engagement": "high"},
    {"key": "yoga_practitioners", "label": "Yoga practitioners",
     "buying_power": "medium", "engagement": "high"},
    {"key": "teachers_nurses", "label": "Teachers / nurses",
     "buying_power": "high", "engagement": "very_high"},
    {"key": "moms_grandmas", "label": "Moms / grandmas",
     "buying_power": "very_high", "engagement": "high"},
    {"key": "dads_grandpas", "label": "Dads / grandpas",
     "buying_power": "high", "engagement": "medium"},
    {"key": "outdoor_lovers", "label": "Outdoor / hikers / campers",
     "buying_power": "high", "engagement": "medium"},
    {"key": "witchy_spiritual", "label": "Witchy / spiritual",
     "buying_power": "medium", "engagement": "very_high"},
    {"key": "minimalists", "label": "Minimalist lifestyle",
     "buying_power": "high", "engagement": "medium"},
]

# Angles concept (façon de présenter le produit)
ANGLES = [
    {"key": "humor_self_deprecation", "label": "Humour autodérision",
     "examples": ["Diagnosed with…", "Allergic to humans…", "Cant, I have…"]},
    {"key": "pride_identity", "label": "Fierté identité",
     "examples": ["Certified expert", "Officially obsessed", "Born to…"]},
    {"key": "minimalist_quote", "label": "Citation minimaliste",
     "examples": ["Less drama more X", "Just X", "Be like X"]},
    {"key": "definition_humor", "label": "Définition humoristique",
     "examples": ["X (noun): art of…", "Side effects of X include…"]},
    {"key": "personalized_name", "label": "Personnalisation prénom/nom",
     "examples": ["Sarah's coffee", "The Smith family", "Best Mom of…"]},
    {"key": "milestone_celebration", "label": "Milestone / célébration",
     "examples": ["I survived X", "10 years of X", "X graduate"]},
    {"key": "warning_disclaimer", "label": "Warning / disclaimer",
     "examples": ["Caution: X in progress", "Hazardous: X levels high"]},
    {"key": "rebrand_classic", "label": "Twist sur un classique",
     "examples": ["Keep calm and X", "I ❤️ X", "Coca-Cola-style X"]},
]

BUYING_POWER_SCORE = {"low": 1, "medium": 2, "high": 3, "very_high": 4}
ENGAGEMENT_SCORE = {"low": 1, "medium": 2, "high": 3, "very_high": 4}
EFFORT_SCORE = {"very_low": 5, "low": 4, "medium": 3, "high": 1}
MARGE_SCORE = {"low": 1, "medium": 2, "high": 3, "very_high": 4}


def load_json(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text())


def score_idea(product: dict, audience: dict, angle: dict,
                trend_score: float, event_intensity: int) -> float:
    score = 0.0
    score += BUYING_POWER_SCORE[audience["buying_power"]] * 8
    score += ENGAGEMENT_SCORE[audience["engagement"]] * 5
    score += EFFORT_SCORE[product["effort"]] * 4
    score += MARGE_SCORE[product["marge"]] * 5
    score += min(trend_score / 100, 8)
    score += event_intensity * 3
    return round(score, 1)


def estimate_revenue(product: dict, audience: dict) -> str:
    base = {
        "tshirt_pod": (40, 150),
        "mug_pod": (25, 100),
        "wall_art": (50, 200),
        "sticker": (15, 60),
        "tumbler_wrap": (50, 200),
        "coloring_book": (80, 400),
        "stl_bookmark": (30, 120),
        "stl_keychain": (25, 100),
        "stl_coaster": (40, 150),
        "totebag_pod": (30, 100),
        "phonecase": (15, 50),
        "notebook_cover": (20, 80),
    }.get(product["key"], (20, 80))
    bp = BUYING_POWER_SCORE[audience["buying_power"]]
    return f"{int(base[0] * bp / 2)}–{int(base[1] * bp / 2)} €/mois"


def formulate_idea(product: dict, audience: dict, angle: dict,
                    trend_keyword: str, event: dict) -> str:
    event_part = f" pour {event['event']} (J-{event['days_to_event']})" if event else ""
    angle_ex = random.choice(angle["examples"])
    return (
        f"{product['label']} sur le thème « {trend_keyword} » "
        f"ciblé {audience['label']}, angle « {angle['label']} » "
        f"(ex: \"{angle_ex.replace('X', trend_keyword)}\"){event_part}"
    )


def brainstorm() -> list[dict]:
    trends_explosion = load_json(DATA_DIR / "trend_explosion.json", {})
    trends_gap = load_json(DATA_DIR / "niche_gap.json", {})
    events = load_json(DATA_DIR / "upcoming_events.json", [])

    # Sources de trend keywords
    keywords = []
    for t in trends_explosion.get("top_exploding_niches", [])[:15]:
        keywords.append({"kw": t["niche"], "score": t.get("score", 0),
                         "source": "voie_a_explosion"})
    for t in trends_gap.get("top_underserved_niches", [])[:15]:
        keywords.append({"kw": t["niche"], "score": t.get("score", 0),
                         "source": "voie_b_niche_gap"})

    # Fallback evergreen si rien
    if not keywords:
        keywords = [
            {"kw": "cottagecore", "score": 500, "source": "evergreen"},
            {"kw": "dark academia", "score": 450, "source": "evergreen"},
            {"kw": "witchy", "score": 400, "source": "evergreen"},
            {"kw": "mushroom", "score": 380, "source": "evergreen"},
            {"kw": "dnd", "score": 350, "source": "evergreen"},
            {"kw": "booktok", "score": 320, "source": "evergreen"},
        ]

    if not events:
        events = [{"event": "Evergreen (no event)", "date": "",
                   "days_to_event": 60, "intensity": 2}]

    ideas = []
    random.seed(42)
    for product in PRODUCT_TYPES:
        for audience in AUDIENCES:
            for angle in ANGLES:
                # On échantillonne 1 trend keyword + 1 event par tuple
                # pour éviter une explosion combinatoire excessive
                kw_pick = random.choice(keywords)
                event_pick = random.choice(events[:6])
                score = score_idea(
                    product, audience, angle,
                    kw_pick["score"], event_pick.get("intensity", 2),
                )
                if score < 40:
                    continue
                idea = formulate_idea(
                    product, audience, angle, kw_pick["kw"], event_pick)
                ideas.append({
                    "idea": idea,
                    "score": score,
                    "product_type": product["label"],
                    "product_pipeline": product["pipeline"],
                    "audience": audience["label"],
                    "angle": angle["label"],
                    "trend_keyword": kw_pick["kw"],
                    "trend_source": kw_pick["source"],
                    "event": event_pick.get("event", ""),
                    "event_days_away": event_pick.get("days_to_event", 0),
                    "platforms": product["platforms"],
                    "estimated_revenue": estimate_revenue(product, audience),
                })

    ideas.sort(key=lambda x: -x["score"])
    return ideas[:200]


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("IDEATOR OFFLINE — brainstorm combinatoire")
    print("=" * 70)

    ideas = brainstorm()
    if not ideas:
        print("✗ Aucune idée générée — données insuffisantes")
        return 1

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_ideas": len(ideas),
        "top_50_ideas": ideas[:50],
        "all_ideas": ideas,
    }
    out_path = DATA_DIR / "ideas_brainstorm.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    print(f"\n{len(ideas)} idées générées. Top 15 :\n")
    for i, idea in enumerate(ideas[:15], 1):
        print(f"  #{i:>2} (score {idea['score']:>5.1f}, "
              f"~{idea['estimated_revenue']:>15})")
        print(f"      → {idea['idea']}")
        print(f"      Pipeline : {idea['product_pipeline']}")
        print()

    print(f"→ Sauvegardé : {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
