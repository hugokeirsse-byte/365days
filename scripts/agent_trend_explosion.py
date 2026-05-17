"""
Agent TREND EXPLOSION (Voie A) — détecte ce qui explose à l'instant T.

Scanne les subreddits commerciaux (Etsy, PrintOnDemand, RedBubble,
EtsySellers, etc.) pour détecter les posts récents qui mentionnent
des produits/niches actuellement en explosion de ventes.

Mots-clés signaux : "selling like crazy", "viral", "best seller",
"sold out", "trending now", "won't stop selling", "obsessed",
"exploding sales", "going crazy", etc.

Sortie : data/trend_explosion.json
- Top 20 niches/produits actuellement en explosion
- Score = mentions × upvotes × récence
- Confidence basée sur cross-subreddit

Mode dégradé sans clé (Reddit JSON public).
"""

import json
import re
import sys
import time
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "Mozilla/5.0 (compatible; TrendExplosion/1.0)"
TIMEOUT = 30

# Subreddits ciblés vendeurs (focalisés sur "what sells now")
COMMERCIAL_SUBS = [
    ("Etsy", "hot", "week"),
    ("Etsy", "new", "day"),
    ("EtsySellers", "hot", "week"),
    ("EtsySellersClub", "hot", "week"),
    ("PrintOnDemand", "hot", "week"),
    ("PrintOnDemand", "top", "week"),
    ("RedBubble", "hot", "week"),
    ("printondemand", "hot", "week"),
    ("SmallBusinessClub", "hot", "week"),
    ("CricutCraft", "hot", "week"),
    ("Sublimation", "hot", "week"),
]

# Signaux d'explosion = phrases qui indiquent un best-seller du moment
EXPLOSION_SIGNALS = [
    r"\bselling like (crazy|hotcakes)\b",
    r"\bcan'?t keep (it|them) in stock\b",
    r"\bsold out (in|so)\b",
    r"\bbest ?sell(er|ing)\b",
    r"\bgoing viral\b",
    r"\btrending now\b",
    r"\bobsessed with\b",
    r"\bexplod(ed|ing) in sales\b",
    r"\bbiggest seller\b",
    r"\bnumber one (seller|product)\b",
    r"\bwon'?t stop selling\b",
    r"\bcrazy demand\b",
    r"\bcouldn'?t keep up\b",
    r"\b(hottest|fastest) (seller|moving)\b",
    r"\b\d+\+? sales (this|last) (week|month)\b",
    r"\bskyrocket(ing|ed)\b",
    r"\bgoing crazy\b",
    r"\bhuge spike\b",
    r"\btake[sn] off\b",
]

# Filtre des mots-clés à extraire (on cherche des NICHES, pas des mots vides)
NICHE_STOPWORDS = {
    "etsy", "shop", "store", "selling", "sale", "sell", "seller", "buy",
    "post", "comment", "thread", "reddit", "questions", "asking", "advice",
    "help", "please", "thanks", "thank", "hello", "anyone", "everyone",
    "this", "that", "with", "from", "they", "their", "what", "have",
    "would", "could", "should", "about", "there", "where", "when",
    "your", "more", "than", "very", "much", "such", "even", "much",
    "today", "yesterday", "tomorrow", "week", "month", "year", "day",
    "best", "good", "great", "love", "want", "need", "make", "making",
    "just", "really", "very", "looks", "looking", "look", "made",
    "first", "second", "anyone", "someone", "nobody", "people", "person",
    "thing", "things", "stuff", "items", "item", "products", "product",
    "design", "designs", "got", "get", "really", "actually", "currently",
    "started", "starting", "trying", "tried", "going", "month",
    "after", "before", "since", "again", "still", "yet", "also",
    "though", "although", "however", "moreover", "furthermore",
    "amazon", "facebook", "instagram", "tiktok", "twitter", "youtube",
    "platform", "site", "website", "online", "digital", "physical",
}


def fetch_subreddit(sub: str, sort: str, timespan: str) -> list[dict]:
    url = f"https://www.reddit.com/r/{sub}/{sort}.json?t={timespan}&limit=80"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())
        return [c["data"] for c in data.get("data", {}).get("children", [])]
    except Exception as exc:  # noqa: BLE001
        print(f"  ✗ r/{sub} : {type(exc).__name__}: {exc}")
        return []


def has_explosion_signal(text: str) -> bool:
    text_low = text.lower()
    return any(re.search(pattern, text_low) for pattern in EXPLOSION_SIGNALS)


def extract_niche_keywords(text: str) -> list[str]:
    """Extrait les mots-clés de niche du texte (1-3 mots, sans stopwords)."""
    text = text.lower()
    # Phrases 2-3 mots
    phrases = re.findall(r"\b[a-z][a-z]+(?:\s+[a-z][a-z]+){1,2}\b", text)
    keywords = []
    for phrase in phrases:
        words = phrase.split()
        clean = [w for w in words if w not in NICHE_STOPWORDS and len(w) > 3]
        if len(clean) >= 2:
            keywords.append(" ".join(clean))
    # Mots simples significatifs
    for word in re.findall(r"\b[a-z]{5,}\b", text):
        if word not in NICHE_STOPWORDS:
            keywords.append(word)
    return keywords


def score_explosion(post: dict, days_old: float) -> float:
    """Score d'explosion = upvotes × engagement × récence."""
    import math
    upvotes = max(post.get("ups", 0), 1)
    comments = post.get("num_comments", 0)
    base = upvotes * math.log(comments + 2)
    # Décroissance temporelle : récent = boost
    recency = max(1, 14 / max(days_old, 0.5))
    return base * recency


def hunt_explosions() -> dict:
    print("=" * 60)
    print("TREND EXPLOSION HUNTER — scan vendeurs Reddit")
    print("=" * 60)

    keyword_scores: dict[str, float] = defaultdict(float)
    keyword_sources: dict[str, set[str]] = defaultdict(set)
    keyword_samples: dict[str, list[str]] = defaultdict(list)
    explosion_posts_count = 0

    for sub, sort, timespan in COMMERCIAL_SUBS:
        print(f"r/{sub} ({sort}/{timespan}) ", end="", flush=True)
        posts = fetch_subreddit(sub, sort, timespan)
        print(f"→ {len(posts)} posts")
        for post in posts:
            text = (post.get("title", "") + " "
                    + post.get("selftext", "")).strip()
            if not text:
                continue
            # On filtre uniquement les posts qui mentionnent l'explosion
            if not has_explosion_signal(text):
                continue
            explosion_posts_count += 1
            created = post.get("created_utc", time.time())
            days_old = (time.time() - created) / 86400
            score = score_explosion(post, days_old)
            for kw in extract_niche_keywords(text):
                keyword_scores[kw] += score
                keyword_sources[kw].add(f"r/{sub}")
                if len(keyword_samples[kw]) < 3:
                    keyword_samples[kw].append(post.get("title", "")[:120])
        time.sleep(1.5)

    print(f"\n  → {explosion_posts_count} posts d'explosion détectés")

    # Top : keyword apparu dans au moins 2 sources DIFFÉRENTES
    candidates = [
        (kw, sc, len(keyword_sources[kw]))
        for kw, sc in keyword_scores.items()
        if len(keyword_sources[kw]) >= 2 and len(kw) > 5
    ]
    candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)
    top = candidates[:30]

    result = {
        "voie": "A — Trend Explosion (court terme, réactif)",
        "scanned_at": datetime.utcnow().isoformat() + "Z",
        "explosion_posts_count": explosion_posts_count,
        "subreddits_scanned": [s[0] for s in COMMERCIAL_SUBS],
        "top_exploding_niches": [
            {
                "niche": kw,
                "score": round(score, 1),
                "cross_subreddit_count": cross,
                "sample_titles": keyword_samples[kw],
                "sources": sorted(keyword_sources[kw]),
            }
            for kw, score, cross in top
        ],
    }
    return result


def main() -> int:
    out_dir = ROOT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    result = hunt_explosions()
    output_path = out_dir / "trend_explosion.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"\n=== TOP 15 niches en explosion ===")
    for i, t in enumerate(result["top_exploding_niches"][:15], 1):
        print(f"{i:>2}. {t['niche']:<40} score {t['score']:>6.0f}  "
              f"[{t['cross_subreddit_count']} subs]")
        if t["sample_titles"]:
            print(f"    « {t['sample_titles'][0][:100]} »")

    if not result["top_exploding_niches"]:
        print("⚠ Aucune niche en explosion détectée.")
        print("  Les posts récents r/Etsy etc. ne contiennent pas les")
        print("  signaux 'selling like crazy'. Réessaye demain ou attends")
        print("  un cycle de scan plus large.")

    print(f"\n→ Sauvegardé : {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
