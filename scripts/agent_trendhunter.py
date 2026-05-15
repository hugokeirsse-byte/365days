"""
Agent Trendhunter — scanner gratuit de tendances et sous-niches.

Scrape les subreddits clés (JSON endpoint public, sans compte ni API key)
et identifie les mots-clés et thèmes émergents. Score chaque mot-clé par
fréquence pondérée × engagement (upvotes + comments).

Sources scannées :
- r/Etsy, r/EtsySellers
- r/PrintOnDemand, r/RedBubble
- r/aestheticshop, r/cottagecore, r/witchcore, r/cozycore
- r/ArtsAndCrafts, r/SmallBusinessClub

Output : data/trends.json avec top 50 niches détectées + métadonnées.

Aucun compte, aucune clé API requise. 100 % légal (endpoint Reddit JSON
public, respect du rate-limit avec délais).

Usage :
    python scripts/agent_trendhunter.py

Trigger via .triggers/trendhunt ou workflow_dispatch.
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
OUTPUT_DIR = ROOT / "data"
USER_AGENT = (
    "Mozilla/5.0 (compatible; TrendHunter/1.0; "
    "+https://github.com/hugokeirsse-byte/365days)"
)
TIMEOUT = 30

SUBREDDITS = [
    ("Etsy", "top", "week"),
    ("EtsySellers", "top", "week"),
    ("EtsySellersClub", "top", "month"),
    ("PrintOnDemand", "top", "week"),
    ("printondemand", "top", "month"),
    ("RedBubble", "top", "week"),
    ("aestheticshop", "top", "week"),
    ("cottagecore", "top", "week"),
    ("witchcore", "top", "month"),
    ("cozycore", "top", "month"),
    ("ArtsAndCrafts", "top", "week"),
    ("SmallBusinessClub", "top", "week"),
    ("InteriorDesign", "top", "week"),
    ("designporn", "top", "week"),
]

# Mots vides à ignorer dans l'extraction
STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "your", "you", "are",
    "have", "from", "they", "their", "would", "should", "could", "about",
    "what", "when", "where", "which", "while", "made", "made", "best",
    "good", "great", "love", "want", "need", "make", "making", "just",
    "really", "very", "more", "much", "many", "some", "any", "all",
    "etsy", "shop", "store", "selling", "sale", "sell", "seller", "buy",
    "got", "get", "got", "thought", "first", "second", "third", "year",
    "month", "week", "day", "today", "yesterday", "tomorrow", "post",
    "comment", "thread", "reddit", "questions", "asking", "advice",
    "help", "please", "thanks", "thank", "hello", "anyone", "everyone",
    "someone", "nobody", "people", "person", "things", "thing", "stuff",
    "items", "item", "products", "product", "design", "designs",
    "printable", "printables", "printed", "print", "prints",
    "starting", "started", "start", "feedback", "review", "opinion",
    "thoughts", "ideas", "idea", "tips", "tip", "guide", "tutorial",
    "question", "questions", "answer", "answers", "share", "showing",
    "show", "showcase", "promote", "marketing", "free", "paid",
    "business", "businesses", "money", "income", "revenue", "profit",
    "side", "hustle", "passive", "trying", "tried", "looking", "find",
    "found", "took", "take", "look", "looks", "looking", "wanted",
    "buying", "bought", "selling", "sold", "after", "before", "since",
    "amazon", "facebook", "instagram", "tiktok", "twitter", "youtube",
    "platform", "platforms", "site", "sites", "website", "websites",
    "online", "digital", "physical", "thank", "thanks", "okay",
    "yeah", "yes", "yes", "yep", "nope", "wow", "haha", "lol",
    "well", "still", "actually", "basically", "definitely", "probably",
    "maybe", "perhaps", "might", "may", "must", "will", "wont", "don",
    "dont", "doesnt", "didnt", "havent", "hasnt", "isnt", "wasnt",
    "weren", "werent", "aren", "arent", "cant", "cannot", "couldn",
    "wouldn", "shouldn", "wasnt", "would", "could", "should", "did",
    "does", "doing", "done", "been", "being", "becoming", "become",
    "going", "went", "gone", "came", "come", "came", "say", "said",
    "tell", "told", "thinking", "think", "thought", "know", "knew",
    "seen", "saw", "see", "watching", "watch", "listening", "listen",
    "hearing", "heard", "hear", "feeling", "felt", "feel", "asking",
    "asked", "ask", "wondering", "wondered", "wonder", "talking",
    "talked", "talk", "going", "went", "gone", "trying", "tried",
    "try", "around", "below", "above", "into", "onto", "without",
    "within", "without", "through", "between", "among", "during",
    "regarding", "concerning", "despite", "although", "even", "until",
    "unless", "however", "moreover", "furthermore", "therefore",
    "nonetheless", "though", "but", "and", "nor", "yet", "so",
    "either", "neither", "both", "each", "every", "another", "other",
    "others", "such", "same", "different", "various", "several",
    "few", "less", "least", "more", "most", "now", "then", "later",
    "earlier", "soon", "right", "left", "next", "previous", "last",
    "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
    "eighth", "ninth", "tenth", "old", "new", "newer", "newest",
    "oldest", "young", "youngest", "small", "big", "large", "tiny",
    "huge", "minimum", "maximum", "min", "max",
}


def fetch_subreddit(sub: str, sort: str = "top", timespan: str = "week") -> list[dict]:
    url = f"https://www.reddit.com/r/{sub}/{sort}.json?t={timespan}&limit=50"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())
        return [c["data"] for c in data.get("data", {}).get("children", [])]
    except Exception as exc:  # noqa: BLE001
        print(f"  ✗ r/{sub} : {type(exc).__name__}: {exc}")
        return []


def extract_keywords(text: str) -> list[str]:
    """Extrait les mots-clés pertinents (2-3 mots, sans stopwords)."""
    if not text:
        return []
    text = text.lower()
    # Phrases courtes (2-3 mots significatifs)
    phrases = re.findall(r"\b[a-z][a-z]+(?:\s+[a-z][a-z]+){0,2}\b", text)
    keywords = []
    for phrase in phrases:
        words = phrase.split()
        if len(words) < 2:
            continue
        clean = [w for w in words if w not in STOPWORDS and len(w) > 3]
        if len(clean) >= 2:
            keywords.append(" ".join(clean))
    # Mots simples significatifs aussi
    for word in re.findall(r"\b[a-z]{5,}\b", text):
        if word not in STOPWORDS:
            keywords.append(word)
    return keywords


def score_post(post: dict) -> float:
    """Engagement score = upvotes * log(comments + 1) avec pondération."""
    import math
    upvotes = max(post.get("ups", 0), 1)
    comments = post.get("num_comments", 0)
    return upvotes * math.log(comments + 2)


def run() -> dict:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== Trend hunting sur {len(SUBREDDITS)} subreddits ===\n")

    keyword_scores: dict[str, float] = defaultdict(float)
    keyword_sources: dict[str, set[str]] = defaultdict(set)
    all_posts = 0

    for sub, sort, timespan in SUBREDDITS:
        print(f"r/{sub} ({sort}/{timespan}) ", end="", flush=True)
        posts = fetch_subreddit(sub, sort, timespan)
        print(f"→ {len(posts)} posts")
        all_posts += len(posts)
        for post in posts:
            text = (post.get("title", "") + " " + post.get("selftext", "")).strip()
            score = score_post(post)
            for kw in extract_keywords(text):
                keyword_scores[kw] += score
                keyword_sources[kw].add(sub)
        time.sleep(1.5)  # respect rate-limit Reddit

    # Top niches : keyword qui apparaît dans au moins 2 subreddits différents
    # ET avec score cumulé élevé
    candidates = [
        (kw, sc, len(keyword_sources[kw]))
        for kw, sc in keyword_scores.items()
        if len(keyword_sources[kw]) >= 2 and len(kw) > 5
    ]
    candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)
    top = candidates[:50]

    result = {
        "scanned_at": datetime.utcnow().isoformat() + "Z",
        "posts_scanned": all_posts,
        "subreddits_scanned": [s[0] for s in SUBREDDITS],
        "top_trending_keywords": [
            {
                "keyword": kw,
                "score": round(score, 1),
                "cross_subreddit_count": cross,
                "sources": sorted(keyword_sources[kw]),
            }
            for kw, score, cross in top
        ],
    }

    output_path = OUTPUT_DIR / "trends.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"\n=== Top 20 niches détectées ===")
    for i, t in enumerate(result["top_trending_keywords"][:20], 1):
        print(f"{i:>2}. {t['keyword']:<40} score={t['score']:.0f}  "
              f"[{t['cross_subreddit_count']} subs]")
    print(f"\n→ Sauvegardé dans {output_path}")
    return result


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
