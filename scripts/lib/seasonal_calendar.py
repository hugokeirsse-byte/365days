"""
Calendrier mondial — anticipation des trends saisonniers et événementiels.

Identifie les événements à venir dans les 8-12 prochaines semaines pour
qu'on puisse produire du merch/livre/contenu EN AVANCE et catcher le pic
de demande quand l'événement arrive.

Sans aucune dépendance externe (pure Python). Tourne en cron via le
Trendhunter pour enrichir data/trends.json avec un volet "upcoming events".

Usage :
    python scripts/lib/seasonal_calendar.py
    → affiche les événements dans les 12 prochaines semaines
    → écrit data/upcoming_events.json
"""

import json
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# ─────────────────────────────────────────────────────────────────────
# ÉVÉNEMENTS RÉCURRENTS À DATE FIXE OU FORMULE
# ─────────────────────────────────────────────────────────────────────

@dataclass
class Event:
    name: str
    date: date  # date pour l'année en cours/prochaine
    countries: list[str]  # marchés concernés
    niches: list[str]  # niches produits qui marchent
    anticipation_weeks: int  # nb semaines à anticiper pour catcher le pic
    intensity: int  # 1-5, force de la demande


def fixed_date_events(year: int) -> list[Event]:
    """Événements à date fixe."""
    return [
        # Janvier
        Event(name="New Year's Day", date=date(year, 1, 1),
              countries=["WORLD"],
              niches=["resolutions", "fresh start", "planners", "new year"],
              anticipation_weeks=4, intensity=4),
        Event(name="Veganuary", date=date(year, 1, 1),
              countries=["WORLD"],
              niches=["vegan recipes", "plant-based", "wellness"],
              anticipation_weeks=4, intensity=3),

        # Février
        Event(name="Valentine's Day", date=date(year, 2, 14),
              countries=["WORLD", "US", "FR"],
              niches=["romance", "couple gifts", "anti-valentine",
                      "self-love", "heart designs", "love quotes"],
              anticipation_weeks=8, intensity=5),
        Event(name="Lunar New Year", date=date(year, 2, 10),  # approx
              countries=["WORLD", "ASIA"],
              niches=["zodiac", "asian culture", "red gold designs"],
              anticipation_weeks=6, intensity=3),

        # Mars
        Event(name="International Women's Day", date=date(year, 3, 8),
              countries=["WORLD"],
              niches=["feminism", "women empowerment", "girl power",
                      "women quotes", "boss lady"],
              anticipation_weeks=4, intensity=4),
        Event(name="St. Patrick's Day", date=date(year, 3, 17),
              countries=["US", "IE", "UK"],
              niches=["irish", "shamrock", "green party", "lucky"],
              anticipation_weeks=4, intensity=3),
        Event(name="Spring Equinox", date=date(year, 3, 20),
              countries=["WORLD"],
              niches=["spring", "rebirth", "flowers", "garden",
                      "cottagecore", "pastel"],
              anticipation_weeks=6, intensity=4),

        # Avril
        Event(name="April Fool's Day", date=date(year, 4, 1),
              countries=["WORLD"],
              niches=["pranks", "humor", "funny"],
              anticipation_weeks=2, intensity=2),
        Event(name="Earth Day", date=date(year, 4, 22),
              countries=["WORLD"],
              niches=["eco", "sustainable", "nature", "planet",
                      "save earth"],
              anticipation_weeks=4, intensity=3),

        # Mai
        Event(name="Mother's Day (US)", date=mothers_day_us(year),
              countries=["US"],
              niches=["mom gifts", "mom mug", "mother quotes",
                      "appreciation"],
              anticipation_weeks=6, intensity=5),
        Event(name="Cinco de Mayo", date=date(year, 5, 5),
              countries=["US", "MX"],
              niches=["mexican", "fiesta", "margaritas", "tacos"],
              anticipation_weeks=4, intensity=3),
        Event(name="Star Wars Day", date=date(year, 5, 4),
              countries=["WORLD"],
              niches=["sci-fi", "may the 4th", "geek"],
              anticipation_weeks=4, intensity=3),

        # Juin
        Event(name="Pride Month", date=date(year, 6, 1),
              countries=["WORLD", "US", "WESTERN"],
              niches=["lgbtq", "rainbow", "pride", "queer",
                      "inclusion", "love is love"],
              anticipation_weeks=6, intensity=4),
        Event(name="Father's Day (US)", date=fathers_day_us(year),
              countries=["US"],
              niches=["dad gifts", "father quotes", "best dad",
                      "grilling humor"],
              anticipation_weeks=6, intensity=4),
        Event(name="Summer Solstice", date=date(year, 6, 21),
              countries=["WORLD"],
              niches=["summer", "beach", "sun", "vacation"],
              anticipation_weeks=6, intensity=4),

        # Juillet
        Event(name="Independence Day (US)", date=date(year, 7, 4),
              countries=["US"],
              niches=["patriotic", "american flag", "july 4th",
                      "freedom", "bbq"],
              anticipation_weeks=4, intensity=4),
        Event(name="Bastille Day (FR)", date=date(year, 7, 14),
              countries=["FR"],
              niches=["french", "patriotic fr", "paris"],
              anticipation_weeks=4, intensity=2),

        # Août
        Event(name="Back to School", date=date(year, 8, 15),
              countries=["WORLD", "US"],
              niches=["school", "teacher gifts", "student",
                      "study", "organization", "supplies"],
              anticipation_weeks=6, intensity=5),
        Event(name="Friendship Day", date=date(year, 8, 4),
              countries=["WORLD"],
              niches=["friends", "best friend gifts",
                      "friendship quotes"],
              anticipation_weeks=4, intensity=3),

        # Septembre
        Event(name="Autumn Equinox", date=date(year, 9, 22),
              countries=["WORLD"],
              niches=["autumn", "fall", "pumpkin", "cozy",
                      "leaves", "sweater weather", "harvest"],
              anticipation_weeks=8, intensity=5),
        Event(name="World Animal Day", date=date(year, 10, 4),
              countries=["WORLD"],
              niches=["pets", "animal rescue", "cat mom",
                      "dog dad"],
              anticipation_weeks=4, intensity=3),

        # Octobre
        Event(name="Halloween", date=date(year, 10, 31),
              countries=["WORLD", "US"],
              niches=["spooky", "witchy", "halloween", "pumpkin",
                      "ghosts", "horror cute", "vampires",
                      "trick or treat", "fall decor"],
              anticipation_weeks=10, intensity=5),
        Event(name="Día de los Muertos", date=date(year, 11, 2),
              countries=["MX", "US-hispanic"],
              niches=["sugar skulls", "mexican folk art",
                      "day of the dead"],
              anticipation_weeks=6, intensity=3),

        # Novembre
        Event(name="Thanksgiving (US)", date=thanksgiving_us(year),
              countries=["US"],
              niches=["gratitude", "thankful", "family",
                      "fall recipes"],
              anticipation_weeks=6, intensity=4),
        Event(name="Black Friday", date=black_friday(year),
              countries=["WORLD", "US"],
              niches=["sale", "deals", "shopping", "gift guides"],
              anticipation_weeks=4, intensity=5),
        Event(name="Singles Day (China)", date=date(year, 11, 11),
              countries=["CN", "WORLD"],
              niches=["shopping", "self-love"],
              anticipation_weeks=3, intensity=2),

        # Décembre
        Event(name="Hanukkah", date=hanukkah_start(year),
              countries=["WORLD", "US-jewish"],
              niches=["menorah", "jewish", "festival of lights"],
              anticipation_weeks=4, intensity=3),
        Event(name="Christmas", date=date(year, 12, 25),
              countries=["WORLD"],
              niches=["christmas", "santa", "winter", "tree",
                      "gifts", "cozy", "ugly sweater", "snowy",
                      "elf", "reindeer", "advent"],
              anticipation_weeks=12, intensity=5),
        Event(name="Winter Solstice", date=date(year, 12, 21),
              countries=["WORLD"],
              niches=["winter", "yule", "snow", "cozy"],
              anticipation_weeks=6, intensity=4),
        Event(name="Kwanzaa", date=date(year, 12, 26),
              countries=["US-african"],
              niches=["african heritage", "unity", "kwanzaa"],
              anticipation_weeks=4, intensity=2),
        Event(name="New Year's Eve", date=date(year, 12, 31),
              countries=["WORLD"],
              niches=["nye party", "champagne", "fireworks",
                      "celebration"],
              anticipation_weeks=4, intensity=4),
    ]


def mothers_day_us(year: int) -> date:
    """Deuxième dimanche de mai."""
    d = date(year, 5, 1)
    while d.weekday() != 6:  # 6 = Sunday
        d += timedelta(days=1)
    return d + timedelta(days=7)


def fathers_day_us(year: int) -> date:
    """Troisième dimanche de juin."""
    d = date(year, 6, 1)
    while d.weekday() != 6:
        d += timedelta(days=1)
    return d + timedelta(days=14)


def thanksgiving_us(year: int) -> date:
    """Quatrième jeudi de novembre."""
    d = date(year, 11, 1)
    while d.weekday() != 3:  # 3 = Thursday
        d += timedelta(days=1)
    return d + timedelta(days=21)


def black_friday(year: int) -> date:
    """Vendredi après Thanksgiving US."""
    return thanksgiving_us(year) + timedelta(days=1)


def hanukkah_start(year: int) -> date:
    """Date approximative (varie selon calendrier hébreu)."""
    # Pour 2026 : ~14 décembre. Approximation.
    return date(year, 12, 14)


# ─────────────────────────────────────────────────────────────────────
# COMBINAISONS DOUBLE-TREND (calendrier × thèmes émergents)
# ─────────────────────────────────────────────────────────────────────

def combine_with_evergreen_trends(event: Event) -> list[str]:
    """Suggère des combinaisons double-trend pour un événement.

    Croise l'événement avec les niches durablement porteuses 2026 :
    cottagecore, dark academia, witchy, romantasy, etc.
    """
    evergreen_trends = [
        "cottagecore aesthetic",
        "dark academia",
        "witchy mystical",
        "romantasy fantasy romance",
        "cute kawaii (Coco Wyo style)",
        "boho minimalist",
        "vintage aesthetic 90s",
        "anime manga style",
        "litRPG fantasy",
    ]
    return [f"{event.name} × {trend}" for trend in evergreen_trends]


# ─────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────


def upcoming_events(weeks_ahead: int = 12, today: date | None = None) -> list[Event]:
    """Liste les événements dans les N prochaines semaines."""
    today = today or date.today()
    horizon = today + timedelta(weeks=weeks_ahead)
    all_events = fixed_date_events(today.year) + fixed_date_events(today.year + 1)
    upcoming = [e for e in all_events if today <= e.date <= horizon]
    upcoming.sort(key=lambda e: e.date)
    return upcoming


def production_brief(event: Event, today: date | None = None) -> dict:
    """Brief actionnable pour un événement à venir."""
    today = today or date.today()
    days_to_event = (event.date - today).days
    weeks_to_event = days_to_event / 7
    optimal_production_start = event.date - timedelta(weeks=event.anticipation_weeks)
    days_to_optimal_start = (optimal_production_start - today).days
    status = (
        "OVERDUE — start NOW" if days_to_optimal_start < 0
        else "URGENT — start this week" if days_to_optimal_start <= 7
        else "PLAN — start in 2-3 weeks" if days_to_optimal_start <= 21
        else "FUTURE — keep on radar"
    )
    return {
        "event": event.name,
        "date": event.date.isoformat(),
        "days_to_event": days_to_event,
        "weeks_to_event": round(weeks_to_event, 1),
        "anticipation_weeks": event.anticipation_weeks,
        "optimal_production_start": optimal_production_start.isoformat(),
        "days_to_optimal_start": days_to_optimal_start,
        "status": status,
        "intensity": event.intensity,
        "countries": event.countries,
        "niches_primary": event.niches,
        "double_trend_combos": combine_with_evergreen_trends(event),
    }


def main() -> int:
    out_dir = ROOT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    upcoming = upcoming_events(weeks_ahead=12)
    briefs = [production_brief(e) for e in upcoming]

    print(f"\n{len(briefs)} événements à anticiper dans les 12 prochaines semaines :\n")
    for b in briefs:
        marker = {
            "OVERDUE — start NOW": "🔴",
            "URGENT — start this week": "🟧",
            "PLAN — start in 2-3 weeks": "🟨",
            "FUTURE — keep on radar": "🟩",
        }.get(b["status"], "⬜")
        print(f"{marker} {b['event']:<32} | {b['date']} | "
              f"J-{b['days_to_event']:>3} | intensity {b['intensity']}")
        print(f"   ↳ {b['status']}")
        print(f"   ↳ Niches : {', '.join(b['niches_primary'][:5])}")

    out_path = out_dir / "upcoming_events.json"
    out_path.write_text(json.dumps(briefs, indent=2, default=str))
    print(f"\n→ Brief sauvegardé : {out_path}")
    return 0


if __name__ == "__main__":
    main()
