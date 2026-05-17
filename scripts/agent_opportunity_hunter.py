"""
Agent OPPORTUNITY HUNTER — le cerveau du système.

Croise les dimensions pour identifier les meilleures opportunités de
production de la semaine :
  STYLE  × SIGNAL  × ÉVÉNEMENT  × CATÉGORIE PRODUIT

Sort DEUX listes séparées :
  1. URGENT EXPLOSION (Voie A) — produire maintenant pour surfer la vague
  2. STABLE NICHE GAP (Voie B) — investir durablement sur un besoin non comblé

Lit :
- data/trend_explosion.json  (Voie A — explosions Reddit subs commerciaux)
- data/niche_gap.json        (Voie B — demandes non comblées subs passionnés)
- data/upcoming_events.json  (Seasonal Calendar — 12 semaines)
- data/styles_du_moment.json (Styles graphiques porteurs 2026)

Sortie : data/opportunities.json
- 15 opportunités URGENTES (à shipper sous 2-7 jours)
- 15 opportunités STABLES (à construire sur 3-8 semaines, marché à long terme)

Cron suggéré : lundi matin, juste après les 2 scans Reddit + Seasonal.
"""

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

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


def load_json(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text())


def estimate_roi(product_cat: str, intensity: int, multiplier: float = 1.0) -> str:
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
    boost = (1 + intensity / 10) * multiplier
    return f"{int(base[0] * boost)}-{int(base[1] * boost)} €/mois"


# ============================================================
# VOIE A — URGENT EXPLOSION
# ============================================================

def score_explosion_opportunity(style: dict, signal: dict, event: dict, product_cat: str) -> float:
    """Score Voie A : on PRIVILÉGIE la rapidité de production
    + alignement avec un signal d'explosion FORT et RÉCENT.
    """
    score = 0.0
    score += style.get("popularity_2026", 3) * 8
    score -= style.get("saturation", 3) * 3

    # Le signal d'explosion : 0-10 selon score + cross-sub
    explosion_strength = min(signal.get("score", 0) / 200, 10)
    cross = signal.get("cross_subreddit_count", 1)
    score += explosion_strength * 5
    score += cross * 6  # cross-subreddit = preuve forte

    # Event : compte mais moins (l'explosion est plus urgente que l'event)
    intensity = event.get("intensity", 3)
    days = event.get("days_to_event", 60)
    score += intensity * 3
    if 7 <= days <= 35:
        score += 8  # event PROCHE pour amplifier la vague
    elif days > 70:
        score -= 6  # event trop loin, on perd la vague d'ici-là

    # Pour Voie A on PRIVILÉGIE l'effort low — on doit pouvoir shipper en 2-7j
    effort_map = {"very_low": 12, "low": 8, "medium": -2, "high": -10}
    score += effort_map.get(PRODUCT_CATEGORIES[product_cat]["effort"], 0)

    marge_map = {"very_high": 6, "high": 4, "medium": 2, "long_tail": 0}
    score += marge_map.get(PRODUCT_CATEGORIES[product_cat]["marge"], 0)

    return round(score, 2)


def hunt_explosion_opportunities(styles_data: dict, events_data: list,
                                  explosion_data: dict) -> list[dict]:
    """Voie A : croise les niches en explosion avec styles/events."""
    signals = explosion_data.get("top_exploding_niches", [])
    if not signals:
        return []

    opportunities = []
    for style_key, style in styles_data.items():
        for signal in signals[:20]:
            for event in events_data[:6]:
                fits = STYLE_PRODUCT_FIT.get(style_key, [])
                # Pour Voie A, on filtre les produits à effort faible UNIQUEMENT
                fast_products = [
                    p for p in fits
                    if PRODUCT_CATEGORIES[p]["effort"] in ("very_low", "low")
                ]
                for product_cat in fast_products[:2]:
                    score = score_explosion_opportunity(style, signal, event, product_cat)
                    if score < 35:
                        continue
                    sample_title = (signal.get("sample_titles") or [""])[0]
                    days = event.get("days_to_event", 60)
                    urgency = "SHIPPER SOUS 48H" if days < 14 else "SHIPPER CETTE SEMAINE"
                    brief = (
                        f"[{urgency}] {product_cat.replace('_', ' ').title()} "
                        f"style « {style['display_name']} » sur niche « {signal['niche']} » "
                        f"(en explosion : « {sample_title[:80]} »). "
                        f"Synchro avec {event['event']} (J-{days})."
                    )
                    opportunities.append({
                        "voie": "A_explosion",
                        "style_key": style_key,
                        "style_name": style["display_name"],
                        "signal_niche": signal["niche"],
                        "signal_score": signal.get("score", 0),
                        "signal_cross_subs": signal.get("cross_subreddit_count", 0),
                        "signal_sample": sample_title[:120],
                        "signal_sources": signal.get("sources", []),
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
                        "estimated_roi_eur_monthly": estimate_roi(
                            product_cat, event["intensity"], multiplier=1.3
                        ),
                    })

    seen = set()
    unique = []
    for o in sorted(opportunities, key=lambda x: -x["composite_score"]):
        key = (o["style_key"], o["signal_niche"], o["product_category"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(o)
    return unique[:15]


# ============================================================
# VOIE B — STABLE NICHE GAP
# ============================================================

def score_niche_gap_opportunity(style: dict, gap: dict, event: dict, product_cat: str) -> float:
    """Score Voie B : on PRIVILÉGIE la profondeur du marché
    + l'absence de concurrence + l'alignement style/niche.
    """
    score = 0.0
    score += style.get("popularity_2026", 3) * 6
    # Pour Voie B la saturation pèse MOINS (le gap signifie déjà sous-exploitation)
    score -= style.get("saturation", 3) * 2

    # Force du gap : nombre de gens qui demandent × cross-subreddit
    gap_strength = min(gap.get("score", 0) / 100, 10)
    cross = gap.get("cross_subreddit_count", 1)
    score += gap_strength * 5
    score += cross * 8  # cross-sub fort = demande TRANSVERSE

    # Event : on tolère bien plus loin (construction long terme)
    intensity = event.get("intensity", 3)
    days = event.get("days_to_event", 60)
    score += intensity * 4
    if 30 <= days <= 120:
        score += 8  # sweet spot construction long terme
    elif days < 14:
        score -= 5  # trop pressé pour construire un catalogue de qualité

    # Effort : on accepte effort medium voire high (catalogue durable)
    effort_map = {"very_low": 4, "low": 6, "medium": 6, "high": 4}
    score += effort_map.get(PRODUCT_CATEGORIES[product_cat]["effort"], 0)

    marge_map = {"very_high": 8, "high": 6, "medium": 3, "long_tail": 4}
    score += marge_map.get(PRODUCT_CATEGORIES[product_cat]["marge"], 0)

    return round(score, 2)


def hunt_niche_gap_opportunities(styles_data: dict, events_data: list,
                                   gap_data: dict) -> list[dict]:
    """Voie B : croise les niches sous-exploitées avec styles/events."""
    gaps = gap_data.get("top_underserved_niches", [])
    if not gaps:
        return []

    opportunities = []
    for style_key, style in styles_data.items():
        for gap in gaps[:20]:
            for event in events_data[:8]:
                fits = STYLE_PRODUCT_FIT.get(style_key, [])
                for product_cat in fits[:3]:
                    score = score_niche_gap_opportunity(style, gap, event, product_cat)
                    if score < 30:
                        continue
                    sample = (gap.get("sample_requests") or [{}])[0]
                    sample_title = sample.get("title", "")
                    sample_sub = sample.get("subreddit", "")
                    days = event.get("days_to_event", 60)
                    brief = (
                        f"[CONSTRUCTION LONG TERME] Catalogue "
                        f"{product_cat.replace('_', ' ')} style « {style['display_name']} » "
                        f"sur niche sous-exploitée « {gap['niche']} » "
                        f"(demande r/{sample_sub} : « {sample_title[:80]} »). "
                        f"Cible event {event['event']} (J-{days})."
                    )
                    opportunities.append({
                        "voie": "B_niche_gap",
                        "style_key": style_key,
                        "style_name": style["display_name"],
                        "gap_niche": gap["niche"],
                        "gap_score": gap.get("score", 0),
                        "gap_cross_subs": gap.get("cross_subreddit_count", 0),
                        "gap_sample_title": sample_title[:120],
                        "gap_sample_subreddit": sample_sub,
                        "gap_sample_pattern": sample.get("pattern", ""),
                        "gap_sources": gap.get("sources", []),
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
                        "estimated_roi_eur_monthly": estimate_roi(
                            product_cat, event["intensity"], multiplier=1.0
                        ),
                    })

    seen = set()
    unique = []
    for o in sorted(opportunities, key=lambda x: -x["composite_score"]):
        key = (o["style_key"], o["gap_niche"], o["product_category"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(o)
    return unique[:15]


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    print("=" * 70)
    print("OPPORTUNITY HUNTER — Voie A (explosion) × Voie B (niche gap)")
    print("=" * 70)

    styles_data = load_json(DATA_DIR / "styles_du_moment.json", {}).get("styles", {})
    events_data = load_json(DATA_DIR / "upcoming_events.json", [])
    explosion_data = load_json(DATA_DIR / "trend_explosion.json", {})
    gap_data = load_json(DATA_DIR / "niche_gap.json", {})

    if not styles_data:
        print("✗ data/styles_du_moment.json absent.")
        return 1
    if not events_data:
        print("✗ data/upcoming_events.json absent — lance d'abord seasonal_calendar.py")
        return 1

    has_explosion = bool(explosion_data.get("top_exploding_niches"))
    has_gap = bool(gap_data.get("top_underserved_niches"))

    if not has_explosion:
        print("⚠ data/trend_explosion.json vide — lance d'abord agent_trend_explosion.py")
    if not has_gap:
        print("⚠ data/niche_gap.json vide — lance d'abord agent_niche_gap.py")
    if not has_explosion and not has_gap:
        print("✗ Aucune des 2 sources de signal disponible. Abort.")
        return 1

    explosion_opps = hunt_explosion_opportunities(
        styles_data, events_data, explosion_data) if has_explosion else []
    gap_opps = hunt_niche_gap_opportunities(
        styles_data, events_data, gap_data) if has_gap else []

    # Affichage console
    print(f"\n{'=' * 70}")
    print(f"🔴 VOIE A — URGENT EXPLOSION  ({len(explosion_opps)} opportunités)")
    print(f"   Action : SHIPPER VITE pour surfer la vague qui monte MAINTENANT")
    print(f"{'=' * 70}")
    if explosion_opps:
        for i, o in enumerate(explosion_opps[:10], 1):
            print(f"\n  #{i:>2}  score {o['composite_score']:.1f}  "
                  f"({o['estimated_roi_eur_monthly']})")
            print(f"      Style    : {o['style_name']}")
            print(f"      Niche    : « {o['signal_niche']} » "
                  f"(cross {o['signal_cross_subs']} subs)")
            print(f"      Event    : {o['event_name']} (J-{o['event_days_away']})")
            print(f"      Produit  : {o['product_category']} → {o['product_marche']}")
            if o['signal_sample']:
                print(f"      Preuve   : « {o['signal_sample'][:90]} »")
    else:
        print("  (aucune opportunité d'explosion détectée)")

    print(f"\n{'=' * 70}")
    print(f"🟦 VOIE B — STABLE NICHE GAP  ({len(gap_opps)} opportunités)")
    print(f"   Action : CONSTRUIRE catalogue durable sur demande non comblée")
    print(f"{'=' * 70}")
    if gap_opps:
        for i, o in enumerate(gap_opps[:10], 1):
            print(f"\n  #{i:>2}  score {o['composite_score']:.1f}  "
                  f"({o['estimated_roi_eur_monthly']})")
            print(f"      Style    : {o['style_name']}")
            print(f"      Gap      : « {o['gap_niche']} » "
                  f"(cross {o['gap_cross_subs']} subs, "
                  f"r/{o['gap_sample_subreddit']})")
            print(f"      Event    : {o['event_name']} (J-{o['event_days_away']})")
            print(f"      Produit  : {o['product_category']} → {o['product_marche']}")
            if o['gap_sample_title']:
                print(f"      Preuve   : « {o['gap_sample_title'][:90]} »")
    else:
        print("  (aucune opportunité de niche gap détectée)")

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "voie_a_explosion": {
            "count": len(explosion_opps),
            "description": "Opportunités URGENTES : niche en explosion + style + event proche. À shipper sous 2-7 jours.",
            "opportunities": explosion_opps,
        },
        "voie_b_niche_gap": {
            "count": len(gap_opps),
            "description": "Opportunités STABLES : demande non comblée + catalogue à construire. ROI long terme.",
            "opportunities": gap_opps,
        },
    }
    output_path = DATA_DIR / "opportunities.json"
    output_path.write_text(json.dumps(output, indent=2, default=str, ensure_ascii=False))

    print(f"\n{'=' * 70}")
    print(f"→ Sauvegardé : {output_path}")
    print(f"   {len(explosion_opps)} opportunités explosion + {len(gap_opps)} niche gap")
    print(f"{'=' * 70}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
