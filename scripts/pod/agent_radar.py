#!/usr/bin/env python3
"""
Agent Radar POD — Moteur de découverte de niches pour Print-on-Demand.

Détecte les tendances en temps réel sur 5 sources complémentaires :
  1. Reddit (r/Spoonflower, r/sewing, r/quilting, r/fabricpatterns + POD)
  2. Google Trends RSS (keywords fabric/pattern/wallpaper/textile)
  3. Etsy public search (fabric patterns, digital downloads)
  4. Spoonflower public pages (contests en cours, bestsellers)
  5. Seasonal calendar (événements 6-12 semaines = fenêtre de production)

Score chaque niche par fréquence × engagement × saisonnalité.
Output : data/pod/trend.json

Cron : lundi + jeudi 5h UTC
Usage : python scripts/pod/agent_radar.py
"""
from __future__ import annotations

import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data" / "pod"
DATA_DIR.mkdir(parents=True, exist_ok=True)

UA = (
    "Mozilla/5.0 (compatible; PODRadar/1.0; "
    "+https://github.com/hugokeirsse-byte/365days)"
)
TIMEOUT = 25

# ─── Sources Reddit ────────────────────────────────────────────────────────────

SUBREDDITS = [
    # Spoonflower & fabric POD
    ("Spoonflower",      "top",  "month"),
    ("sewing",           "top",  "week"),
    ("quilting",         "top",  "week"),
    ("fabricpatterns",   "top",  "month"),
    ("SewingForBeginners", "top", "month"),
    ("CrossStitch",      "top",  "week"),
    # Intérieur / wallpaper
    ("InteriorDesign",   "top",  "week"),
    ("wallpaper",        "top",  "week"),
    ("malelivingspace",  "top",  "week"),
    ("femalelivingspace","top",  "week"),
    ("RoomPorn",         "top",  "month"),
    # POD général
    ("PrintOnDemand",    "hot",  "day"),
    ("PrintOnDemand",    "top",  "week"),
    ("RedBubble",        "top",  "week"),
    ("Etsy",             "hot",  "day"),
    ("EtsySellers",      "top",  "week"),
    # Aesthetics porteurs pour patterns
    ("cottagecore",      "top",  "week"),
    ("witchcraft",       "top",  "week"),
    ("BohoDecor",        "top",  "month"),
    ("maximalism",       "top",  "month"),
    ("darkacademia",     "top",  "week"),
    ("plantsnoblooms",   "top",  "month"),
]

# Mots vides — on les exclut du scoring
STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "your", "you", "are",
    "have", "from", "they", "their", "would", "should", "could", "about",
    "what", "when", "where", "which", "while", "made", "best", "good",
    "great", "love", "want", "need", "make", "making", "just", "really",
    "very", "more", "much", "many", "some", "any", "all", "etsy", "shop",
    "store", "selling", "sale", "sell", "seller", "buy", "got", "get",
    "post", "comment", "thread", "reddit", "help", "please", "thanks",
    "design", "designs", "pattern", "fabric", "print", "printed", "prints",
    "start", "started", "starting", "feedback", "review", "question",
    "share", "show", "looking", "found", "took", "take", "look",
    "thought", "think", "know", "feel", "going", "want", "using", "used",
    "also", "just", "can", "has", "was", "not", "its", "but", "are",
    "how", "new", "one", "two", "like", "see", "been", "even", "had",
    "his", "her", "our", "who", "did", "now", "way", "only", "time",
    "use", "each", "she", "him", "may", "use", "into", "over", "such",
    "after", "think", "here", "well", "work", "long", "place", "year",
    "back", "come", "give", "most", "know", "game", "give", "live",
    "mean", "move", "give", "hand", "high", "keep", "last", "left",
    "line", "list", "next", "play", "read", "side", "stay", "stop",
}

# Keywords pertinents pour notre marché (boost ×2 si présent)
BOOST_KEYWORDS = {
    # Styles de patterns
    "botanical", "floral", "geometric", "abstract", "vintage", "retro",
    "watercolor", "boho", "cottagecore", "maximalist", "minimal",
    "art deco", "art nouveau", "liberty", "chinoiserie", "toile",
    "damask", "ikat", "paisley", "plaid", "checkered", "stripe",
    "polka dot", "houndstooth", "chevron", "herringbone", "lattice",
    # Thèmes porteurs
    "mushroom", "moon", "celestial", "butterfly", "moth", "bee",
    "fern", "leaf", "forest", "woodland", "ocean", "wave", "coral",
    "tropical", "jungle", "bird", "fox", "cat", "dog", "rabbit",
    "skull", "halloween", "christmas", "holiday", "floral",
    "witch", "mystical", "tarot", "crystals", "astrology",
    "japanese", "korean", "scandinavian", "mediterranean",
    # Formats Spoonflower
    "seamless", "repeat", "tile", "surface design", "fabric design",
    "wallpaper", "giftwrap", "spoonflower", "society6",
    # Moments / saisons
    "summer", "autumn", "fall", "winter", "spring", "christmas",
    "halloween", "easter", "valentines", "mothers day", "wedding",
}


def _fetch(url: str, extra_headers: dict | None = None) -> str | None:
    headers = {"User-Agent": UA, "Accept": "application/json, text/html"}
    if extra_headers:
        headers.update(extra_headers)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        print(f"  ✗ {url[:60]}… → {type(exc).__name__}: {exc}")
        return None


def _extract_keywords(text: str) -> list[str]:
    """Extrait les mots et bi-grammes significatifs d'un texte."""
    text = text.lower()
    words = re.findall(r"\b[a-z]{3,}\b", text)
    words = [w for w in words if w not in STOPWORDS]
    # Bi-grammes
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)
               if words[i] not in STOPWORDS and words[i+1] not in STOPWORDS]
    return words + bigrams


# ─── Source 1 : Reddit ─────────────────────────────────────────────────────────

def scrape_reddit(scores: defaultdict) -> int:
    total = 0
    for sub, sort, t in SUBREDDITS:
        url = f"https://www.reddit.com/r/{sub}/{sort}.json?t={t}&limit=25"
        raw = _fetch(url, {"Accept": "application/json"})
        if not raw:
            time.sleep(1)
            continue
        try:
            data = json.loads(raw)
            posts = data.get("data", {}).get("children", [])
        except json.JSONDecodeError:
            continue
        for post in posts:
            p = post.get("data", {})
            title = p.get("title", "")
            body  = p.get("selftext", "")
            score = p.get("score", 1) + p.get("num_comments", 0) * 2
            score = max(score, 1)
            weight = math.log(score + 1)
            text = f"{title} {body}"
            for kw in _extract_keywords(text):
                boost = 2.0 if kw in BOOST_KEYWORDS else 1.0
                scores[kw] += weight * boost
        total += len(posts)
        time.sleep(0.6)
    print(f"  Reddit : {total} posts analysés sur {len(SUBREDDITS)} subreddits")
    return total


# ─── Source 2 : Google Trends RSS ──────────────────────────────────────────────

GOOGLE_GEO = ["US", "GB", "AU", "CA"]

def scrape_google_trends(scores: defaultdict) -> int:
    found = 0
    for geo in GOOGLE_GEO:
        url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={geo}"
        raw = _fetch(url)
        if not raw:
            continue
        items = re.findall(r"<item>(.*?)</item>", raw, re.DOTALL)
        for item in items:
            m_title   = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", item)
            m_traffic = re.search(
                r"<ht:approx_traffic>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</ht:approx_traffic>", item)
            if not m_title:
                continue
            title = m_title.group(1).strip()
            traffic_str = m_traffic.group(1).strip() if m_traffic else ""
            score = 0
            if traffic_str:
                tm = re.match(r"(\d+(?:\.\d+)?)\s*([KM]?)", traffic_str)
                if tm:
                    val  = float(tm.group(1))
                    mult = {"K": 1_000, "M": 1_000_000, "": 1}[tm.group(2)]
                    score = int(val * mult)
            weight = math.log(max(score, 1) + 1) * 0.5
            for kw in _extract_keywords(title):
                boost = 2.5 if kw in BOOST_KEYWORDS else 0.8
                scores[kw] += weight * boost
                found += 1
        time.sleep(0.5)
    print(f"  Google Trends : {found} signaux collectés ({len(GOOGLE_GEO)} pays)")
    return found


# ─── Source 3 : Etsy public search ─────────────────────────────────────────────

ETSY_QUERIES = [
    "spoonflower fabric",
    "seamless pattern fabric",
    "fabric by the yard floral",
    "wallpaper removable pattern",
    "surface pattern design",
    "cottagecore fabric",
    "boho fabric pattern",
    "botanical fabric",
]

def scrape_etsy(scores: defaultdict) -> int:
    found = 0
    for q in ETSY_QUERIES:
        encoded = urllib.parse.quote_plus(q)
        url = f"https://www.etsy.com/search?q={encoded}&ref=search_bar"
        raw = _fetch(url, {
            "Accept": "text/html",
            "Accept-Language": "en-US,en;q=0.9",
        })
        if not raw:
            time.sleep(1.5)
            continue
        # Etsy embed product data dans des balises JSON-LD et data attributes
        titles = re.findall(r'"title":\s*"([^"]{10,80})"', raw)
        listing_titles = re.findall(r'data-listing-title="([^"]{5,100})"', raw)
        all_titles = titles[:30] + listing_titles[:30]
        for title in all_titles:
            for kw in _extract_keywords(title):
                boost = 2.0 if kw in BOOST_KEYWORDS else 1.0
                scores[kw] += 3.0 * boost  # Etsy = signal commercial fort
                found += 1
        time.sleep(1.5)
    print(f"  Etsy : {found} signaux depuis {len(ETSY_QUERIES)} requêtes")
    return found


# ─── Source 4 : Spoonflower public pages ───────────────────────────────────────

SPOONFLOWER_URLS = [
    ("contests",  "https://www.spoonflower.com/contests"),
    ("trending",  "https://www.spoonflower.com/en/shop?on=fabric&q=trending&sort=bestSelling"),
    ("new",       "https://www.spoonflower.com/en/shop?on=fabric&q=&sort=newestPublicDesigns"),
]

def scrape_spoonflower(scores: defaultdict) -> dict:
    contests: list[str] = []
    found = 0
    for label, url in SPOONFLOWER_URLS:
        raw = _fetch(url, {"Accept": "text/html", "Accept-Language": "en-US,en;q=0.9"})
        if not raw:
            time.sleep(1)
            continue
        # Titres de designs (JSON-LD ou data attrs)
        design_titles = re.findall(r'"name":\s*"([^"]{5,100})"', raw)
        design_titles += re.findall(r'alt="([^"]{5,80})"', raw)
        design_titles += re.findall(r'title="([^"]{5,80})"', raw)
        # Themes de contests
        if label == "contests":
            contest_themes = re.findall(
                r'(?:theme|contest|challenge)[^>]{0,20}>\s*([A-Za-z][^<]{5,60})<',
                raw, re.IGNORECASE)
            contests.extend(contest_themes[:10])
        for title in design_titles[:50]:
            for kw in _extract_keywords(title):
                boost = 3.0 if kw in BOOST_KEYWORDS else 1.5
                scores[kw] += 5.0 * boost  # Spoonflower = signal très ciblé
                found += 1
        time.sleep(1)
    print(f"  Spoonflower : {found} signaux + {len(contests)} thèmes de contest")
    return {"contest_themes": contests[:10]}


# ─── Source 5 : Calendrier saisonnier ──────────────────────────────────────────

# Événements codés en dur (12 mois, US + global)
EVENTS: list[tuple[int, int, str, list[str], int]] = [
    # (mois, jour, nom, niches, intensité 1-5)
    (1,  1,  "New Year",          ["celebration", "confetti", "stars", "minimal"], 3),
    (1, 20,  "Martin Luther King","civil rights", 2) if False else
    (2, 14,  "Valentines Day",    ["heart", "rose", "love", "romantic", "floral"], 5),
    (3, 17,  "St Patricks Day",   ["shamrock", "celtic", "green", "clover"], 3),
    (3, 20,  "Spring Equinox",    ["botanical", "flower", "pastel", "garden"], 4),
    (4,  1,  "Easter",            ["egg", "bunny", "spring floral", "pastel"], 4),
    (5,  5,  "Cinco de Mayo",     ["mexican", "fiesta", "folk", "geometric"], 2),
    (5, 12,  "Mothers Day",       ["floral", "botanical", "feminine", "soft"], 4),
    (6, 21,  "Summer Solstice",   ["tropical", "beach", "nautical", "sunshine"], 4),
    (7,  4,  "4th of July",       ["americana", "patriotic", "stars stripes"], 4),
    (9,  1,  "Back to School",    ["geometric", "school", "classic", "bold"], 3),
    (9, 22,  "Autumn Equinox",    ["leaf", "pumpkin", "mushroom", "harvest"], 4),
    (10, 31, "Halloween",         ["skull", "witch", "gothic", "spider", "moon"], 5),
    (11, 27, "Thanksgiving",      ["plaid", "harvest", "autumn", "warm"], 4),
    (12, 25, "Christmas",         ["holiday", "pine", "nordic", "plaid", "candy cane"], 5),
    (12, 31, "New Year Eve",      ["celebration", "gold", "sparkle", "midnight"], 3),
]

def score_seasonal(scores: defaultdict) -> list[dict]:
    today = date.today()
    upcoming = []
    for row in EVENTS:
        if len(row) != 5:
            continue
        month, day, name, niches, intensity = row
        event_date = date(today.year, month, day)
        if event_date < today:
            event_date = date(today.year + 1, month, day)
        delta = (event_date - today).days
        if delta < 0 or delta > 120:
            continue
        # Zone de production optimale : 6-14 semaines avant
        weeks = delta / 7
        if 6 <= weeks <= 14:
            urgency = 5
        elif 4 <= weeks < 6:
            urgency = 4
        elif 2 <= weeks < 4:
            urgency = 3
        else:
            urgency = 2
        niche_list = niches if isinstance(niches, list) else [niches]
        for niche in niche_list:
            weight = urgency * intensity * 2.0
            for kw in _extract_keywords(niche):
                scores[kw] += weight
        upcoming.append({
            "event": name,
            "date": str(event_date),
            "days_away": delta,
            "urgency": urgency,
            "niches": niche_list,
        })
    upcoming.sort(key=lambda x: x["days_away"])
    print(f"  Calendrier : {len(upcoming)} événements dans les 120 prochains jours")
    return upcoming


# ─── Agrégation et scoring final ───────────────────────────────────────────────

# Catégories de niches pour taggage automatique
NICHE_CATEGORIES = {
    "botanical":    ["flower", "floral", "leaf", "botanical", "garden", "fern", "herb"],
    "geometric":    ["geometric", "abstract", "pattern", "stripe", "chevron", "hexagon"],
    "celestial":    ["moon", "star", "celestial", "galaxy", "cosmic", "astrology"],
    "woodland":     ["mushroom", "fox", "rabbit", "forest", "woodland", "deer", "bird"],
    "coastal":      ["wave", "ocean", "nautical", "coral", "beach", "shell", "sea"],
    "holiday":      ["christmas", "halloween", "easter", "holiday", "festive"],
    "boho":         ["boho", "bohemian", "mandala", "ikat", "paisley", "tribal"],
    "vintage":      ["vintage", "retro", "antique", "art deco", "art nouveau", "liberty"],
    "cottagecore":  ["cottagecore", "cottage", "wildflower", "linen", "gingham"],
    "maximalist":   ["maximalist", "baroque", "ornate", "bold", "colorful", "eclectic"],
}

def categorize(keyword: str) -> str | None:
    kl = keyword.lower()
    for cat, terms in NICHE_CATEGORIES.items():
        if any(t in kl for t in terms):
            return cat
    return None


def build_report(scores: defaultdict, meta: dict) -> dict:
    # Filtre : mots de 3 chars min, score > 0.5
    scored = [(kw, sc) for kw, sc in scores.items()
              if len(kw) >= 3 and sc > 0.5]
    scored.sort(key=lambda x: x[1], reverse=True)

    top50 = []
    for rank, (kw, sc) in enumerate(scored[:50], 1):
        top50.append({
            "rank": rank,
            "keyword": kw,
            "score": round(sc, 2),
            "category": categorize(kw),
        })

    # Top 10 par catégorie
    by_cat: defaultdict[str, list] = defaultdict(list)
    for item in top50:
        if item["category"]:
            by_cat[item["category"]].append(item["keyword"])

    return {
        "generated_at": date.today().isoformat(),
        "total_signals": sum(scores.values()),
        "keywords_analyzed": len(scores),
        "top_keywords": top50,
        "by_category": dict(by_cat),
        "upcoming_events": meta.get("upcoming_events", []),
        "spoonflower_contests": meta.get("contest_themes", []),
        "recommended_niches": [item["keyword"] for item in top50[:10]],
    }


# ─── Main ───────────────────────────────────────────────────────────────────────

def run():
    print("=" * 60)
    print("Agent Radar POD — démarrage")
    print(f"Date : {date.today()}")
    print("=" * 60)

    scores: defaultdict[str, float] = defaultdict(float)
    meta: dict = {}

    print("\n[1/5] Reddit…")
    scrape_reddit(scores)

    print("\n[2/5] Google Trends…")
    scrape_google_trends(scores)

    print("\n[3/5] Etsy…")
    scrape_etsy(scores)

    print("\n[4/5] Spoonflower…")
    sf_meta = scrape_spoonflower(scores)
    meta.update(sf_meta)

    print("\n[5/5] Calendrier saisonnier…")
    upcoming = score_seasonal(scores)
    meta["upcoming_events"] = upcoming

    print("\n[✓] Agrégation et scoring…")
    report = build_report(scores, meta)

    out = DATA_DIR / "trend.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(f"\n{'=' * 60}")
    print(f"✓ Rapport écrit : {out}")
    print(f"  {len(report['top_keywords'])} niches détectées")
    print(f"  Top 5 : {', '.join(report['recommended_niches'][:5])}")
    if report["upcoming_events"]:
        next_ev = report["upcoming_events"][0]
        print(f"  Prochain événement : {next_ev['event']} dans {next_ev['days_away']} jours")
    print("=" * 60)
    return report


if __name__ == "__main__":
    run()
