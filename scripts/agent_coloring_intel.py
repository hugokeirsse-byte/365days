"""
Agent COLORING INTEL — analyse compétitive des coloring books bestsellers.

Pipeline :
1. Scrape Amazon search results publics (HTML, légal) pour "adult coloring book"
   et 10 sous-niches (mandala, mushroom, fantasy, etc.)
2. Extrait titres + URL covers (PAS les images, juste métadonnées)
3. Si GEMINI_API_KEY dispo : Gemini Vision analyse les covers pour décrire
   le style dominant (line weight, palette, sujets récurrents, mood)
4. Clustering manuel des styles dominants → JSON config
5. Output : data/coloring_styles_meta.json

Le pipeline produce_coloring_book ou produce_coloring_book_hf peut
ensuite consommer ce JSON pour générer dans les styles validés par le
marché (pas re-créer 1:1, mais s'inspirer des codes visuels efficaces).

Variables d'env :
  GEMINI_API_KEY      pour analyse Vision (sinon mode dégradé)
  NICHES_LIMIT=10     nb sous-niches à analyser
  RESULTS_PER_NICHE=8 nb covers analysées par niche
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
TIMEOUT = 30


# 12 sous-niches coloring books à analyser
COLORING_NICHES = [
    "mandala coloring book adults",
    "mushroom coloring book adults",
    "fantasy coloring book adults",
    "fairy coloring book adults",
    "animal coloring book adults",
    "flower coloring book adults",
    "cottagecore coloring book adults",
    "witchy coloring book adults",
    "dragon coloring book adults",
    "geometric coloring book adults",
    "anime coloring book adults",
    "horror coloring book adults",
]


# ============================================================
# AMAZON SEARCH SCRAPER
# ============================================================

def amazon_search_html(query: str) -> str | None:
    """Récupère la page de résultats de recherche Amazon."""
    url = (f"https://www.amazon.com/s?"
           f"k={urllib.parse.quote(query)}&i=stripbooks")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:  # noqa: BLE001
        print(f"  ✗ Amazon {query[:30]} : {type(exc).__name__}")
        return None


def extract_products(html: str, max_items: int = 8) -> list[dict]:
    """Extrait titres + URL cover des résultats Amazon."""
    if not html:
        return []
    # Pattern : div data-component-type="s-search-result"
    items = []
    # Titres dans h2 > a > span
    title_matches = re.findall(
        r'<h2[^>]*>.*?<span[^>]*>(.*?)</span>',
        html, re.DOTALL,
    )
    # Image URLs (covers)
    img_matches = re.findall(
        r'<img[^>]*class="[^"]*s-image[^"]*"[^>]*src="([^"]+)"',
        html,
    )
    # Ratings (étoiles)
    rating_matches = re.findall(
        r'(\d\.\d)\s*out of 5 stars',
        html,
    )

    for i in range(min(max_items, len(title_matches))):
        title = re.sub(r"\s+", " ", title_matches[i]).strip()[:160]
        if not title:
            continue
        img = img_matches[i] if i < len(img_matches) else ""
        rating = rating_matches[i] if i < len(rating_matches) else ""
        items.append({
            "title": title,
            "cover_url": img,
            "rating": rating,
        })
    return items


# ============================================================
# GEMINI VISION STYLE ANALYSIS
# ============================================================

def fetch_cover_bytes(url: str) -> bytes | None:
    """Download cover thumbnail (pour analyse, pas re-hébergement)."""
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read()
        if len(data) < 1000 or len(data) > 5_000_000:
            return None
        return data
    except Exception:  # noqa: BLE001
        return None


def gemini_analyze_cover(cover_bytes: bytes, niche: str) -> dict | None:
    """Demande à Gemini Vision de décrire le style visuel."""
    if not GEMINI_API_KEY or not cover_bytes:
        return None
    img_b64 = base64.b64encode(cover_bytes).decode("ascii")
    prompt = (
        f"You are a visual design analyst. This is a cover of an adult "
        f"coloring book in the '{niche}' niche. Describe its visual style "
        f"in a concise structured way. Reply ONLY with valid JSON:\n"
        '{"line_weight": "thin/medium/thick", '
        '"line_style": "clean/sketchy/decorative", '
        '"composition": "centered/scattered/border/grid", '
        '"detail_level": "minimal/medium/intricate", '
        '"cover_color_palette": ["color1", "color2"], '
        '"mood": "soft/dark/whimsical/elegant/etc", '
        '"signature_elements": ["element1", "element2", "element3"], '
        '"target_buyer_persona": "Who would buy this"}'
    )
    url = f"{API_BASE}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    body = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
            ],
        }],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json",
            "maxOutputTokens": 800,
        },
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            resp_data = json.loads(resp.read())
        text = resp_data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except Exception as exc:  # noqa: BLE001
        print(f"     gemini vision fail : {type(exc).__name__}")
        return None


# ============================================================
# STYLE AGGREGATION
# ============================================================

def aggregate_niche_styles(analyses: list[dict]) -> dict:
    """Agrège les styles dominants pour une niche."""
    if not analyses:
        return {}
    line_weights = Counter(a.get("line_weight", "") for a in analyses if a)
    moods = Counter(a.get("mood", "") for a in analyses if a)
    details = Counter(a.get("detail_level", "") for a in analyses if a)
    compositions = Counter(a.get("composition", "") for a in analyses if a)
    all_elements = []
    for a in analyses:
        if a:
            all_elements.extend(a.get("signature_elements", []))
    common_elements = [e for e, _ in Counter(all_elements).most_common(8)]

    return {
        "samples_analyzed": len(analyses),
        "dominant_line_weight": line_weights.most_common(1)[0][0] if line_weights else "",
        "dominant_mood": moods.most_common(1)[0][0] if moods else "",
        "dominant_detail_level": details.most_common(1)[0][0] if details else "",
        "dominant_composition": compositions.most_common(1)[0][0] if compositions else "",
        "recurring_elements": common_elements,
        "suggested_prompt_template": (
            f"adult coloring book page line art illustration, "
            f"{details.most_common(1)[0][0] if details else 'medium'} detail, "
            f"{line_weights.most_common(1)[0][0] if line_weights else 'medium'} clean black lines on pure white background, "
            f"{compositions.most_common(1)[0][0] if compositions else 'centered'} composition, "
            f"{moods.most_common(1)[0][0] if moods else 'whimsical'} mood, "
            f"featuring {', '.join(common_elements[:5])}, "
            f"no shading no color no text"
        ),
    }


# ============================================================
# MAIN
# ============================================================

def analyze_niche(niche: str, results_per_niche: int) -> dict:
    print(f"\n→ {niche}")
    html = amazon_search_html(niche)
    if not html:
        return {"niche": niche, "error": "amazon fetch failed"}
    products = extract_products(html, max_items=results_per_niche)
    print(f"   {len(products)} bestsellers extracted")
    if not products:
        return {"niche": niche, "products": []}

    # Si Gemini dispo, analyse les covers
    analyses = []
    if GEMINI_API_KEY:
        for i, p in enumerate(products[:results_per_niche], 1):
            print(f"   [{i}/{len(products)}] analyzing cover...")
            cover = fetch_cover_bytes(p["cover_url"])
            if not cover:
                continue
            analysis = gemini_analyze_cover(cover, niche)
            if analysis:
                analyses.append(analysis)
                p["style_analysis"] = analysis
            time.sleep(2.5)  # rate limit politesse
    else:
        print("   ⊝ GEMINI_API_KEY absent → skip vision analysis")

    aggregated = aggregate_niche_styles(analyses)

    return {
        "niche": niche,
        "scanned_at": datetime.utcnow().isoformat() + "Z",
        "products_found": len(products),
        "products": products,
        "style_aggregate": aggregated,
    }


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    niches_limit = int(os.environ.get("NICHES_LIMIT") or "0") or len(COLORING_NICHES)
    results_per_niche = int(os.environ.get("RESULTS_PER_NICHE") or "0") or 8
    niches = COLORING_NICHES[:niches_limit]

    print("=" * 70)
    print(f"COLORING INTEL — analyse {len(niches)} niches × {results_per_niche} covers")
    print(f"Gemini Vision : {'OK' if GEMINI_API_KEY else 'PAUSED (no key)'}")
    print("=" * 70)

    all_results = []
    for niche in niches:
        all_results.append(analyze_niche(niche, results_per_niche))
        time.sleep(3)  # politesse Amazon

    output = {
        "agent": "coloring_intel",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "gemini_vision_active": bool(GEMINI_API_KEY),
        "niches_analyzed": len(niches),
        "results": all_results,
    }
    out_path = DATA_DIR / "coloring_styles_meta.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n→ {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
