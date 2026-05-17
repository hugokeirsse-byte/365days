"""
Agent EXTERNAL TRENDS — sources de tendances additionnelles gratuites.

Élargit notre détection au-delà de Reddit avec :
1. Google Trends (via lib pytrends, gratuit, API publique Google)
2. TikTok Creative Center (HTML public, scrapeable légalement)
3. Pinterest Trends (HTML public)

Sortie : data/external_trends.json
- Top 30 keywords trending Google + TikTok + Pinterest
- Score normalisé inter-sources
- Mood/style implicite si détectable

Sans clé API. Gratuit. Légal (data publique affichée sans login).

Cron suggéré : mardi 6h UTC (avant Trend Design Matcher 5h... ah non,
on met 4h UTC pour qu'il tourne avant).

Variables d'env :
  GOOGLE_TRENDS_COUNTRY=FR    (FR, US, GB, DE, IT, ES)
  SKIP_GOOGLE=0               1 pour skip Google Trends
  SKIP_TIKTOK=0               1 pour skip TikTok
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)
TIMEOUT = 30

# Catégories à scanner sur chaque source (ce qui nous intéresse pour Etsy/POD)
GOOGLE_CATEGORIES = [
    "gift", "shirt", "decor", "home", "art",
]


def fetch_google_trends_daily(country: str = "US") -> list[dict]:
    """Récupère les daily trending searches de Google Trends via le
    feed RSS public (pas besoin de pytrends ni de clé).
    """
    url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={country}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            xml_text = resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:  # noqa: BLE001
        print(f"  ✗ Google Trends ({country}) : {type(exc).__name__}")
        return []

    # Parse XML simple — on cherche <title> dans <item>
    items = re.findall(r"<item>(.*?)</item>", xml_text, re.DOTALL)
    results = []
    for item in items:
        title_match = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", item)
        traffic_match = re.search(
            r"<ht:approx_traffic>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</ht:approx_traffic>",
            item)
        if not title_match:
            continue
        title = title_match.group(1).strip()
        traffic = (traffic_match.group(1).strip()
                    if traffic_match else "")
        # Parse traffic ex "500K+" → 500000
        score = 0
        if traffic:
            m = re.match(r"(\d+(?:\.\d+)?)\s*([KM]?)", traffic)
            if m:
                val = float(m.group(1))
                mult = {"K": 1000, "M": 1000000, "": 1}[m.group(2)]
                score = int(val * mult)
        results.append({"keyword": title, "score": score,
                        "source": f"google_trends_{country}"})
    return results


def fetch_pinterest_trends() -> list[dict]:
    """Récupère les trends Pinterest depuis trends.pinterest.com (HTML public).
    Pas d'API officielle gratuite — on parse le HTML rendu côté serveur.
    """
    url = "https://trends.pinterest.com/?country=US&period=week"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        })
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:  # noqa: BLE001
        print(f"  ✗ Pinterest Trends : {type(exc).__name__}")
        return []

    # Pinterest charge ses trends via JS souvent — fallback : on cherche
    # des data attributes ou JSON inline
    keywords = []
    # Pattern : json inline qui contient des "term": "X"
    matches = re.findall(r'"term":\s*"([^"]+)"', html)
    seen = set()
    for term in matches:
        term = term.strip()
        if term and term.lower() not in seen and len(term) > 2:
            seen.add(term.lower())
            keywords.append({"keyword": term, "score": 100,
                              "source": "pinterest_trends"})
    return keywords[:30]


def fetch_tiktok_creative_center() -> list[dict]:
    """Récupère les hashtags trending depuis TikTok Creative Center
    (page publique sans login).

    Note : TikTok change souvent son HTML. Si KO, mode dégradé.
    """
    url = ("https://www.tiktok.com/business/creativecenter/inspiration/"
           "popular/hashtag/pc/en")
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        })
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:  # noqa: BLE001
        print(f"  ✗ TikTok Creative Center : {type(exc).__name__}")
        return []

    # On cherche tous les hashtags affichés
    hashtags = re.findall(r'#([a-zA-Z0-9_]{3,30})', html)
    seen = set()
    keywords = []
    for h in hashtags:
        if h.lower() not in seen:
            seen.add(h.lower())
            keywords.append({"keyword": h, "score": 50,
                              "source": "tiktok_creative_center"})
    return keywords[:30]


def normalize_keyword(kw: str) -> str:
    return re.sub(r"\s+", " ", kw.lower().strip())


def merge_sources(sources: list[list[dict]]) -> list[dict]:
    """Fusionne en gardant les keywords vus dans plusieurs sources."""
    by_kw = defaultdict(lambda: {"sources": set(), "score_total": 0})
    for source in sources:
        for item in source:
            kw_norm = normalize_keyword(item["keyword"])
            by_kw[kw_norm]["sources"].add(item["source"])
            by_kw[kw_norm]["score_total"] += item["score"]
            by_kw[kw_norm]["display"] = item["keyword"]

    merged = []
    for kw_norm, data in by_kw.items():
        merged.append({
            "keyword": data["display"],
            "keyword_normalized": kw_norm,
            "score_total": data["score_total"],
            "sources": sorted(data["sources"]),
            "cross_source_count": len(data["sources"]),
        })
    # Priorité au cross-source puis au score
    merged.sort(key=lambda x: (-x["cross_source_count"], -x["score_total"]))
    return merged


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    country = os.environ.get("GOOGLE_TRENDS_COUNTRY", "US").strip().upper()
    skip_google = os.environ.get("SKIP_GOOGLE") == "1"
    skip_tiktok = os.environ.get("SKIP_TIKTOK") == "1"

    print("=" * 70)
    print("EXTERNAL TRENDS — Google + TikTok + Pinterest")
    print("=" * 70)

    sources = []
    if not skip_google:
        print(f"\n→ Google Trends {country}")
        gt = fetch_google_trends_daily(country)
        print(f"   {len(gt)} keywords")
        sources.append(gt)
        time.sleep(2)

        # Aussi US si pas déjà
        if country != "US":
            print(f"→ Google Trends US (en bonus)")
            gt_us = fetch_google_trends_daily("US")
            print(f"   {len(gt_us)} keywords")
            sources.append(gt_us)
            time.sleep(2)

    if not skip_tiktok:
        print(f"\n→ TikTok Creative Center")
        tt = fetch_tiktok_creative_center()
        print(f"   {len(tt)} hashtags")
        sources.append(tt)
        time.sleep(2)

    print(f"\n→ Pinterest Trends")
    pt = fetch_pinterest_trends()
    print(f"   {len(pt)} keywords")
    sources.append(pt)

    merged = merge_sources(sources)
    print(f"\n{len(merged)} keywords totaux (fusionnés)")

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sources_scanned": [s for src in sources for s in (
            [src[0]["source"]] if src else [])],
        "total_keywords": len(merged),
        "top_cross_source": [m for m in merged if m["cross_source_count"] >= 2][:30],
        "top_overall": merged[:50],
    }
    out = DATA_DIR / "external_trends.json"
    out.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n→ Sauvegardé : {out}")

    print(f"\n🔥 TOP 10 CROSS-SOURCE (vus dans ≥2 sources) :")
    for i, m in enumerate(output["top_cross_source"][:10], 1):
        print(f"  {i:>2}. {m['keyword']:<40} "
              f"[{m['cross_source_count']} sources, score {m['score_total']}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
