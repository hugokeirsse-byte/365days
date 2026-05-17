"""
Agent TREND & DESIGN MATCHER — scrape Etsy bestsellers + extrait
structures de phrases récurrentes à fort potentiel.

Pour une liste de niches cibles (ex: "cat lover gift t-shirt",
"dnd shirt funny"…), va sur la page de recherche publique Etsy
(HTML, légal car données publiques affichées sans login), récupère
les titres des bestsellers, et analyse :

1. Structures de phrases récurrentes (regex patterns sur les titres)
   - Ex: "[ADJECTIF] [NICHE] Mom", "[NICHE] Lover Gift", "I'm a [NICHE]"
2. Mots-clés émotionnels saturés (love, gift, funny, vintage…)
3. Détermine le "mood" visuel associé (cynique → vintage label,
   geek → terminal interface, mignon → kawaii pastel)
4. Génère un JSON config avec : nouveau format candidat + niche cible
   + prompt visuel suggéré, prêt à être injecté dans produce_viral_formats

Mode dégradé sans Etsy : utilise les corpus déjà collectés dans
data/trends.json et data/trend_explosion.json comme fallback.

Sortie : data/trend_design_matches.json

Variables d'env :
  TARGET_NICHES="cat shirt funny,dnd t-shirt,gardener gift"
  USE_LIVE_ETSY=1   tente le scraping Etsy live (sinon mode dégradé)
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
)
TIMEOUT = 30

# Niches par défaut pour le scan
DEFAULT_NICHES = [
    "cat lover gift shirt",
    "dog mom gift",
    "dnd dungeon master gift",
    "book lover funny shirt",
    "coffee addict shirt",
    "introvert humor shirt",
    "knitting gift funny",
    "crochet humor shirt",
    "teacher gift funny",
    "nurse gift humor",
    "fishing gift dad",
    "gardener gift mom",
    "hiking gift outdoor",
    "yoga gift namaste",
    "vintage music lover",
]

# Patterns regex pour détecter les STRUCTURES récurrentes
STRUCTURE_PATTERNS = [
    (r"\b([Cc]ertified|[Pp]rofessional|[Oo]fficial)\s+(\w+\s+\w+)\b",
     "certification_format"),
    (r"\b(I'm a|I am a|I'm an)\s+(\w+)\b",
     "identity_statement"),
    (r"\b(\w+)\s+[Mm]om(?:\s+[Ll]ife)?\b",
     "x_mom_format"),
    (r"\b(\w+)\s+[Dd]ad(?:\s+[Ll]ife)?\b",
     "x_dad_format"),
    (r"\b[Ll]ife\s+is\s+(better|good|great)\s+with\s+(\w+)\b",
     "life_is_better_with"),
    (r"\b(Funny|Hilarious|Sarcastic)\s+(\w+)\s+(Shirt|Gift|Mug)\b",
     "adjective_niche_product"),
    (r"\b(?:Just\s+a)\s+(?:[Gg]irl|[Bb]oy|[Mm]om)\s+who\s+loves\s+(\w+)\b",
     "just_a_girl_who_loves"),
    (r"\b[Bb]orn\s+to\s+(\w+)\b",
     "born_to_x"),
    (r"\b[Ee]at\s+[Ss]leep\s+(\w+)\s+[Rr]epeat\b",
     "eat_sleep_repeat"),
    (r"\b[Pp]owered\s+by\s+(\w+)\b",
     "powered_by"),
    (r"\b(?:My|The)\s+(\w+)\s+[Ee]ra\b",
     "my_era"),
    (r"\b[Bb]ut\s+[Ff]irst\s+(\w+)\b",
     "but_first_x"),
    (r"\bIt's\s+a\s+(\w+)\s+[Tt]hing\b",
     "its_a_thing"),
    (r"\b[Aa]ddicted\s+to\s+(\w+)\b",
     "addicted_to"),
    (r"\b(Mama|Papa|Grandma)\s+[Bb]ear\b",
     "mama_bear"),
]

# Mood detection : mots-clés qui signalent un mood visuel
MOOD_SIGNALS = {
    "vintage_americana": ["vintage", "retro", "classic", "americana", "70s", "old school"],
    "cottagecore_watercolor": ["cottage", "garden", "flower", "soft", "cozy", "cute"],
    "dark_academia": ["dark", "academia", "library", "gothic", "moody", "vintage book"],
    "kawaii_cute": ["kawaii", "cute", "chibi", "kitten", "puppy", "sweet"],
    "minimalist_typography": ["minimalist", "simple", "clean", "modern", "typography"],
    "geek_terminal": ["error", "404", "system", "ctrl", "geek", "nerd", "matrix"],
    "medical_label": ["diagnosed", "prescription", "warning", "medical", "side effects"],
    "esoteric_witchy": ["witch", "spell", "tarot", "moon", "occult", "magic"],
    "y2k_pop": ["y2k", "pink", "chrome", "butterfly", "2000s", "rhinestone"],
    "wood_burned": ["rustic", "wood", "farmhouse", "country", "barn", "cabin"],
}

# Family → suggested visual style
FORMAT_FAMILY_TO_STYLE = {
    "certification_format":       "medical_label",
    "identity_statement":          "minimalist_typography",
    "x_mom_format":                "cottagecore_watercolor",
    "x_dad_format":                "vintage_americana",
    "life_is_better_with":         "minimalist_typography",
    "adjective_niche_product":     "vintage_americana",
    "just_a_girl_who_loves":       "kawaii_cute",
    "born_to_x":                   "vintage_americana",
    "eat_sleep_repeat":            "geek_terminal",
    "powered_by":                  "geek_terminal",
    "my_era":                      "y2k_pop",
    "but_first_x":                 "minimalist_typography",
    "its_a_thing":                 "minimalist_typography",
    "addicted_to":                 "medical_label",
    "mama_bear":                   "wood_burned",
}


def fetch_etsy_search(niche_query: str) -> list[str]:
    """Tente de récupérer les titres bestsellers Etsy pour une query.

    Etsy expose les résultats publiquement sans login.
    Si Etsy bloque (403, captcha), retourne liste vide.
    """
    query = urllib.parse.quote(niche_query)
    url = (
        f"https://www.etsy.com/search?q={query}"
        f"&order=most_relevant&ref=auto-1"
    )
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:  # noqa: BLE001
        print(f"  ✗ Etsy r/{niche_query[:30]} : {type(exc).__name__}")
        return []

    # Pattern : Etsy met les titres dans des balises <a> avec data-listing-id
    # ou dans des <h3 class="v2-listing-card__title">
    titles = []
    # Pattern 1 : h3 listing card
    titles += re.findall(
        r'<h3[^>]*class="[^"]*listing-card__title[^"]*"[^>]*>\s*([^<]+?)\s*</h3>',
        html, re.IGNORECASE)
    # Pattern 2 : title attribute sur <a>
    titles += re.findall(
        r'<a[^>]*data-listing-id="[^"]+"[^>]*title="([^"]+)"', html)
    # Dédup + nettoyage
    cleaned = []
    seen = set()
    for t in titles:
        t = re.sub(r"\s+", " ", t).strip()
        if t and t not in seen and len(t) > 10:
            seen.add(t)
            cleaned.append(t)
    return cleaned[:40]


def extract_structures(titles: list[str]) -> dict:
    """Pour chaque titre, identifie les patterns matchés."""
    structures = defaultdict(list)
    for title in titles:
        for pattern, label in STRUCTURE_PATTERNS:
            for match in re.finditer(pattern, title):
                groups = [g for g in match.groups() if g]
                structures[label].append({
                    "title": title,
                    "matched": match.group(0),
                    "captured": groups,
                })
    return dict(structures)


def detect_mood(titles: list[str]) -> str:
    """Détecte le mood visuel dominant dans la liste de titres."""
    blob = " ".join(titles).lower()
    scores = {}
    for mood, signals in MOOD_SIGNALS.items():
        scores[mood] = sum(blob.count(s) for s in signals)
    best = max(scores.items(), key=lambda x: x[1])
    return best[0] if best[1] > 0 else "minimalist_typography"


def extract_top_keywords(titles: list[str], top_n: int = 15) -> list[str]:
    """Mots-clés thématiques les plus fréquents (hors stopwords)."""
    stop = {
        "the", "and", "for", "with", "this", "that", "from", "your", "you",
        "are", "was", "but", "not", "all", "can", "her", "his", "she", "him",
        "shirt", "tshirt", "gift", "mug", "design", "etsy", "digital",
        "download", "print", "art", "wall", "decor", "sticker", "poster",
        "funny", "cute", "love", "best", "new", "cool", "great", "good",
    }
    words = re.findall(r"\b[a-z]{4,}\b", " ".join(titles).lower())
    filtered = [w for w in words if w not in stop]
    return [w for w, _ in Counter(filtered).most_common(top_n)]


def build_config_for_pipeline(niche_query: str, titles: list[str],
                                structures: dict, mood: str) -> dict:
    """Construit un fichier de config injectable dans produce_viral_formats."""
    keywords = extract_top_keywords(titles)
    # On garde les top 5 structures les plus fréquentes
    top_structures = sorted(
        structures.items(), key=lambda x: -len(x[1]))[:5]

    suggested_formats = []
    for label, occurrences in top_structures:
        captures = [c for occ in occurrences for c in occ["captured"]]
        most_common_capture = Counter(captures).most_common(1)
        if most_common_capture:
            sample = most_common_capture[0][0]
            suggested_visual = FORMAT_FAMILY_TO_STYLE.get(label, mood)
            suggested_formats.append({
                "format_label": label,
                "occurrences": len(occurrences),
                "sample_captured": sample,
                "sample_titles": [occ["title"][:120] for occ in occurrences[:3]],
                "suggested_visual_style": suggested_visual,
                "suggested_template_en": _build_template(label, "{niche}"),
            })
    return {
        "niche_query": niche_query,
        "titles_analyzed": len(titles),
        "top_keywords": keywords,
        "dominant_mood": mood,
        "suggested_formats": suggested_formats,
        "raw_sample_titles": titles[:10],
    }


def _build_template(label: str, slot: str) -> str:
    templates = {
        "certification_format": f"Certified Professional {slot}",
        "identity_statement": f"I'm a {slot}",
        "x_mom_format": f"{slot} Mom Life",
        "x_dad_format": f"{slot} Dad Life",
        "life_is_better_with": f"Life is better with {slot}",
        "adjective_niche_product": f"Funny {slot} Gift",
        "just_a_girl_who_loves": f"Just a girl who loves {slot}",
        "born_to_x": f"Born to {slot}",
        "eat_sleep_repeat": f"Eat Sleep {slot} Repeat",
        "powered_by": f"Powered by {slot}",
        "my_era": f"My {slot} Era",
        "but_first_x": f"But first, {slot}",
        "its_a_thing": f"It's a {slot} thing",
        "addicted_to": f"Addicted to {slot}",
        "mama_bear": f"{slot} Mama Bear",
    }
    return templates.get(label, f"{slot}")


def fallback_from_local_data() -> list[str]:
    """Si Etsy bloque, fallback sur trends.json + trend_explosion.json."""
    titles = []
    for fname in ["trends.json", "trend_explosion.json", "niche_gap.json"]:
        path = DATA_DIR / fname
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        if "top_exploding_niches" in data:
            for n in data["top_exploding_niches"]:
                titles += n.get("sample_titles", [])
        if "top_underserved_niches" in data:
            for n in data["top_underserved_niches"]:
                for s in n.get("sample_requests", []):
                    titles.append(s.get("title", ""))
        if "top_trending_keywords" in data:
            for n in data["top_trending_keywords"]:
                titles += n.get("sample_titles", [])
    return [t for t in titles if t]


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    niches_env = os.environ.get("TARGET_NICHES", "").strip()
    use_live = os.environ.get("USE_LIVE_ETSY", "1") != "0"
    niches = [n.strip() for n in niches_env.split(",") if n.strip()] \
        if niches_env else DEFAULT_NICHES

    print("=" * 70)
    print("TREND & DESIGN MATCHER — analyse structures de phrases bestsellers")
    print("=" * 70)
    print(f"Niches cibles : {len(niches)} | Live Etsy : {use_live}\n")

    all_results = []
    for niche in niches:
        print(f"→ r/{niche}")
        titles = fetch_etsy_search(niche) if use_live else []
        if not titles:
            print(f"   (Etsy KO, fallback local data)")
            titles = fallback_from_local_data()[:50]
        if not titles:
            print(f"   ✗ aucune donnée")
            continue
        structures = extract_structures(titles)
        mood = detect_mood(titles)
        config = build_config_for_pipeline(niche, titles, structures, mood)
        all_results.append(config)
        print(f"   {len(titles)} titres analysés, mood {mood}, "
              f"{len(structures)} structures détectées")
        time.sleep(2)

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "niches_analyzed": len(all_results),
        "matches": all_results,
    }
    output_path = DATA_DIR / "trend_design_matches.json"
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    print(f"\n{'=' * 70}")
    print(f"  → {output_path}")
    print(f"  → {len(all_results)} niches × structures détectées")

    # Top recommandations
    print("\n🎯 TOP STRUCTURES DÉTECTÉES (à injecter dans viral_formats)")
    format_counts = Counter()
    for r in all_results:
        for f in r["suggested_formats"]:
            format_counts[f["format_label"]] += f["occurrences"]
    for label, count in format_counts.most_common(10):
        print(f"  {count:>4}× {label:<30} (style: "
              f"{FORMAT_FAMILY_TO_STYLE.get(label, 'minimalist')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
