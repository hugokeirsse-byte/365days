"""
Agent NICHE GAP (Voie B) — détecte les niches sous-exploitées.

Scanne Reddit pour identifier les niches où il y a une **forte demande**
(gens qui cherchent activement quelque chose) mais une **faible offre**
(personne ne leur propose, ou personne ne le fait bien).

Indicateurs de gap :
- "I wish I could find X"
- "Where can I buy Y?"
- "Anyone make Z for me?"
- "Why isn't there anything for [niche]?"
- "Can't find a good X anywhere"
- "Why does no one sell..."
- "Need recommendations for..."

Sortie : data/niche_gap.json
- Top 20 niches sous-exploitées avec exemples concrets de posts
- Score basé sur récurrence des demandes
- Public cible identifié (subreddit d'origine)

Mode 100 % gratuit (Reddit JSON public sans clé).
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
USER_AGENT = "Mozilla/5.0 (compatible; NicheGapHunter/1.0)"
TIMEOUT = 30

# Subreddits avec public passionné qui exprime des besoins non comblés
PASSIONATE_SUBS = [
    # Crafts & DIY
    ("Crafts", "hot", "week"),
    ("ArtsAndCrafts", "hot", "week"),
    # Niches lifestyle hyper-passionnées
    ("cottagecore", "hot", "week"),
    ("witchcore", "hot", "week"),
    ("DarkAcademia", "hot", "week"),
    ("BookTok", "hot", "week"),
    ("Romantasy", "hot", "week"),
    ("LitRPG", "hot", "week"),
    # Hobbies très précis
    ("Knitting", "hot", "week"),
    ("Embroidery", "hot", "week"),
    ("crochet", "hot", "week"),
    ("Mycology", "hot", "week"),
    ("Foraging", "hot", "week"),
    ("permaculture", "hot", "week"),
    ("HouseplantsClub", "hot", "week"),
    ("DnD", "hot", "week"),
    ("rpg", "hot", "week"),
    # Identité / minorités sous-servies
    ("WitchesVsPatriarchy", "hot", "week"),
    ("AskWomenOver30", "hot", "week"),
    ("childfree", "hot", "week"),
    # Lifestyle
    ("simpleliving", "hot", "week"),
    ("minimalism", "hot", "week"),
    ("zerowaste", "hot", "week"),
    ("introvert", "hot", "week"),
    ("hsp", "hot", "week"),  # Highly Sensitive Persons
]

# Patterns regex pour détecter une demande non comblée
GAP_PATTERNS = [
    (r"\bi (wish|wished) i could find\b", "wish_to_find"),
    (r"\bwhere (can|could) i (buy|find|get)\b", "where_to_buy"),
    (r"\b(any|anyone)\s+(have|know|recommend|make)\b.*\bfor\b", "recommendation_request"),
    (r"\bwhy (isn'?t|is no one) (there|selling|making)\b", "why_no_one"),
    (r"\bcan'?t find (a |any |good )", "cant_find"),
    (r"\bneed (recommendations?|suggestions?) for\b", "need_recommendations"),
    (r"\bdoes (anyone|anybody) (sell|make|have)\b", "does_anyone_make"),
    (r"\blook(ing)? for (something|someone|a place) (that|who|where)\b", "looking_for_something"),
    (r"\bwhy don'?t they make\b", "why_dont_they_make"),
    (r"\bsomeone should (make|sell|create)\b", "someone_should_make"),
    (r"\bwhere are all the\b", "where_are_all_the"),
    (r"\bis there a (place|shop|store|site)\b", "is_there_a_place"),
]

STOPWORDS = {
    "this", "that", "with", "from", "they", "their", "what", "have",
    "would", "could", "should", "about", "there", "where", "when",
    "your", "more", "than", "very", "much", "such", "even",
    "today", "yesterday", "week", "month", "year", "day",
    "best", "good", "great", "love", "want", "need", "make",
    "just", "really", "very", "looks", "looking", "look", "made",
    "anyone", "someone", "people", "thing", "things", "stuff",
    "products", "product", "design", "etsy", "amazon", "redbubble",
    "buy", "sell", "find", "wish", "place", "store", "shop", "site",
    "recommendations", "suggestions", "doing", "trying", "tried",
    "going", "after", "before", "since", "again", "still", "even",
    "really", "actually", "currently",
}


def fetch_subreddit(sub: str, sort: str, timespan: str) -> list[dict]:
    url = f"https://www.reddit.com/r/{sub}/{sort}.json?t={timespan}&limit=100"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())
        return [c["data"] for c in data.get("data", {}).get("children", [])]
    except Exception as exc:  # noqa: BLE001
        print(f"  ✗ r/{sub} : {type(exc).__name__}: {exc}")
        return []


def detect_gap_pattern(text: str) -> str | None:
    """Retourne le type de pattern détecté, ou None."""
    text_low = text.lower()
    for pattern, label in GAP_PATTERNS:
        if re.search(pattern, text_low):
            return label
    return None


def extract_what_after_pattern(text: str, pattern: str) -> str:
    """Extrait la phrase qui suit le pattern (ce que la personne cherche)."""
    text_low = text.lower()
    match = re.search(pattern, text_low)
    if not match:
        return ""
    start = match.end()
    # Garder les 80 prochains caractères qui suivent
    snippet = text_low[start:start + 100]
    # Garder jusqu'à la première ponctuation forte
    end = re.search(r"[.!?\n]", snippet)
    if end:
        snippet = snippet[:end.start()]
    return snippet.strip()


def extract_niche_keywords(text: str) -> list[str]:
    """Extrait les mots-clés thématiques (en ignorant les stopwords)."""
    text = text.lower()
    keywords = []
    # Mots significatifs 5+ caractères
    for word in re.findall(r"\b[a-z]{5,}\b", text):
        if word not in STOPWORDS:
            keywords.append(word)
    # Phrases courtes 2-3 mots
    phrases = re.findall(r"\b[a-z]{4,}\s+[a-z]{4,}(?:\s+[a-z]{4,})?\b", text)
    for phrase in phrases:
        words = phrase.split()
        if all(w not in STOPWORDS for w in words):
            keywords.append(phrase)
    return keywords


def hunt_gaps() -> dict:
    print("=" * 60)
    print("NICHE GAP HUNTER — scan demandes non comblées Reddit")
    print("=" * 60)

    gap_keywords: dict[str, float] = defaultdict(float)
    gap_sources: dict[str, set[str]] = defaultdict(set)
    gap_samples: dict[str, list[dict]] = defaultdict(list)
    total_gap_posts = 0

    for sub, sort, timespan in PASSIONATE_SUBS:
        print(f"r/{sub} ", end="", flush=True)
        posts = fetch_subreddit(sub, sort, timespan)
        sub_gap_count = 0
        for post in posts:
            title = post.get("title", "")
            body = post.get("selftext", "")
            text = (title + " " + body).strip()
            if not text:
                continue
            pattern_label = detect_gap_pattern(text)
            if not pattern_label:
                continue
            sub_gap_count += 1
            total_gap_posts += 1
            # Score = upvotes × récence
            import math
            ups = max(post.get("ups", 0), 1)
            comments = post.get("num_comments", 0)
            score = ups * math.log(comments + 2)
            # Extraction des mots-clés du titre + extrait après pattern
            keywords = extract_niche_keywords(title)
            for kw in keywords:
                gap_keywords[kw] += score
                gap_sources[kw].add(f"r/{sub}")
                if len(gap_samples[kw]) < 3:
                    snippet = extract_what_after_pattern(
                        text, [p for p, l in GAP_PATTERNS if l == pattern_label][0]
                    )
                    gap_samples[kw].append({
                        "pattern": pattern_label,
                        "title": title[:120],
                        "subreddit": sub,
                        "snippet": snippet[:100],
                        "ups": post.get("ups", 0),
                    })
        print(f"→ {sub_gap_count} gap posts")
        time.sleep(1.5)

    print(f"\n  → {total_gap_posts} demandes non comblées détectées au total")

    candidates = [
        (kw, sc, len(gap_sources[kw]))
        for kw, sc in gap_keywords.items()
        if len(gap_sources[kw]) >= 2 and len(kw) > 5
    ]
    candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)
    top = candidates[:30]

    result = {
        "voie": "B — Niche Gap (long terme, stable, sous-exploité)",
        "scanned_at": datetime.utcnow().isoformat() + "Z",
        "total_gap_posts": total_gap_posts,
        "subreddits_scanned": [s[0] for s in PASSIONATE_SUBS],
        "patterns_detected": [label for _, label in GAP_PATTERNS],
        "top_underserved_niches": [
            {
                "niche": kw,
                "score": round(score, 1),
                "cross_subreddit_count": cross,
                "sample_requests": gap_samples[kw],
                "sources": sorted(gap_sources[kw]),
            }
            for kw, score, cross in top
        ],
    }
    return result


def main() -> int:
    out_dir = ROOT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    result = hunt_gaps()
    output_path = out_dir / "niche_gap.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"\n=== TOP 15 niches sous-exploitées ===")
    for i, t in enumerate(result["top_underserved_niches"][:15], 1):
        print(f"{i:>2}. {t['niche']:<40} score {t['score']:>6.0f}  "
              f"[{t['cross_subreddit_count']} subs]")
        if t["sample_requests"]:
            sr = t["sample_requests"][0]
            print(f"    [{sr['pattern']}] r/{sr['subreddit']} ↑{sr['ups']}")
            print(f"    « {sr['title']} »")

    if not result["top_underserved_niches"]:
        print("⚠ Aucune niche sous-exploitée détectée cette fois.")
        print("  Les posts récents ne contiennent pas les signaux")
        print("  'I wish I could find X'. Réessaye demain ou ajoute")
        print("  d'autres subreddits dans PASSIONATE_SUBS.")

    print(f"\n→ Sauvegardé : {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
