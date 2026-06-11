#!/usr/bin/env python3
"""
Agent Art Director POD — De la tendance au cahier des charges artistique.

Lit data/pod/trend.json, sélectionne les 3 meilleures niches du moment,
et génère pour chacune un brief complet :
  - Prompt FLUX/SDXL pour génération seamless pattern
  - Palette couleurs (5 hex)
  - Style et mood
  - Tags SEO Spoonflower / Society6 / Redbubble (max 20 tags)
  - Specs techniques (résolution, repeat type, format)
  - 3 variantes de prompt (base / dark / light)

Output : data/pod/cahier_des_charges.json

Usage : python scripts/pod/agent_art_director.py
Dépend de : data/pod/trend.json (généré par agent_radar.py)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data" / "pod"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ─── Palettes par catégorie de niche ───────────────────────────────────────────

PALETTES: dict[str, dict] = {
    "botanical": {
        "name":    "Garden Fresh",
        "colors":  ["#2D5016", "#5A7A2E", "#A8C86B", "#F2EDD3", "#8B4513"],
        "mood":    "fresh, natural, lush, organic",
    },
    "geometric": {
        "name":    "Modern Bold",
        "colors":  ["#1A1A2E", "#16213E", "#0F3460", "#E94560", "#F5F5F5"],
        "mood":    "bold, graphic, modern, clean",
    },
    "celestial": {
        "name":    "Midnight Sky",
        "colors":  ["#0D0221", "#261447", "#5C4B9E", "#B8A9E4", "#F4D03F"],
        "mood":    "mystical, dreamy, cosmic, ethereal",
    },
    "woodland": {
        "name":    "Forest Floor",
        "colors":  ["#3E2723", "#5D4037", "#8D6E63", "#A5D6A7", "#FFF9C4"],
        "mood":    "cozy, whimsical, earthy, storybook",
    },
    "coastal": {
        "name":    "Sea Glass",
        "colors":  ["#006994", "#00A8B4", "#7FCDCD", "#E8F4F8", "#F5CBA7"],
        "mood":    "fresh, airy, relaxed, nautical",
    },
    "holiday": {
        "name":    "Festive Classic",
        "colors":  ["#CC0000", "#006600", "#FFFFFF", "#FFD700", "#8B4513"],
        "mood":    "festive, warm, traditional, joyful",
    },
    "boho": {
        "name":    "Desert Sunset",
        "colors":  ["#C4622D", "#E8956D", "#F2C571", "#89A79A", "#4A3728"],
        "mood":    "warm, eclectic, free-spirited, earthy",
    },
    "vintage": {
        "name":    "Faded Elegance",
        "colors":  ["#8B7355", "#C4A882", "#E8DCC8", "#6B8E5E", "#4A3728"],
        "mood":    "nostalgic, elegant, antique, refined",
    },
    "cottagecore": {
        "name":    "Wildflower Meadow",
        "colors":  ["#F8BBD9", "#C8E6C9", "#FFF9C4", "#E1BEE7", "#D7CCC8"],
        "mood":    "soft, romantic, pastoral, gentle",
    },
    "maximalist": {
        "name":    "Jewel Tones",
        "colors":  ["#880E4F", "#1A237E", "#1B5E20", "#F57F17", "#37474F"],
        "mood":    "opulent, rich, bold, layered",
    },
    "default": {
        "name":    "Neutral Base",
        "colors":  ["#2C2C2C", "#7A7A7A", "#BDBDBD", "#F5F5F5", "#FF7043"],
        "mood":    "balanced, versatile, commercial",
    },
}

# ─── Specs techniques par plateforme ───────────────────────────────────────────

PLATFORM_SPECS = {
    "spoonflower": {
        "fabric_min_px":    5400,  # 150dpi × 36 inches (yard width)
        "wallpaper_min_px": 7200,  # 200dpi × 36 inches
        "preferred_repeat": "basic_tile",  # tile, half_drop, half_brick, mirror
        "file_format":      "PNG or JPG",
        "color_mode":       "sRGB",
        "max_file_mb":      40,
        "notes":            "Repeat type dans les métadonnées upload. Eviter les bords visibles.",
    },
    "society6": {
        "art_print_px":     4500,  # 300dpi × 15in minimum
        "phone_case_px":    1200,  # 300dpi small
        "preferred_repeat": "seamless_tile",
        "file_format":      "PNG (transparent ou fond blanc)",
        "color_mode":       "sRGB",
        "max_file_mb":      25,
        "notes":            "Art prints: 300dpi minimum. Designs full-bleed pour phone cases.",
    },
    "redbubble": {
        "sticker_px":       2160,
        "poster_px":        7632,  # 300dpi × 25.4in
        "preferred_repeat": "seamless_tile",
        "file_format":      "PNG avec transparence pour stickers",
        "color_mode":       "sRGB",
        "max_file_mb":      30,
        "notes":            "Designs avec marges blanches risquent le recadrage. Plein écran recommandé.",
    },
}

# ─── Style directions par catégorie ────────────────────────────────────────────

STYLE_DIRECTIONS: dict[str, dict] = {
    "botanical": {
        "composition": "dense botanical repeat, overlapping leaves and flowers, no visible gaps",
        "technique":   "watercolor illustration style, loose brushstrokes, organic edges",
        "avoid":       "digital gradient, hard shadows, white background visible in repeat",
    },
    "geometric": {
        "composition": "precise geometric tessellation, clean lines, mathematical repeat",
        "technique":   "vector-flat, no texture, high contrast",
        "avoid":       "organic shapes, gradients, random placement",
    },
    "celestial": {
        "composition": "scattered celestial elements (moon phases, stars, planets) on dark bg",
        "technique":   "detailed fine-line illustration, gold/silver accents, mystical",
        "avoid":       "cartoonish style, bright daytime colors, bold primary colors",
    },
    "woodland": {
        "composition": "scattered forest creatures and elements, playful arrangement",
        "technique":   "charming folk art illustration, flat color with detail",
        "avoid":       "realistic rendering, dark gothic mood",
    },
    "coastal": {
        "composition": "flowing waves, shells, and nautical elements in loose arrangement",
        "technique":   "watercolor washes, soft edges, breezy feel",
        "avoid":       "harsh lines, dark colors, winter tones",
    },
    "holiday": {
        "composition": "classic holiday motifs in structured or scattered repeat",
        "technique":   "bold, graphic illustration, traditional color palette",
        "avoid":       "modern minimal, muted tones",
    },
    "boho": {
        "composition": "layered decorative elements, mandalas, feathers, geometric borders",
        "technique":   "intricate linework, warm earth tones, eclectic mix",
        "avoid":       "stark minimalism, cold blues",
    },
    "vintage": {
        "composition": "aged botanical prints, toile-style vignettes, antique map details",
        "technique":   "engraving-inspired, sepia tones, aged paper texture",
        "avoid":       "modern typography, bright neon",
    },
    "cottagecore": {
        "composition": "soft wildflower scatter, gingham checks, cottage elements",
        "technique":   "delicate watercolor, soft focus, dreamy pastels",
        "avoid":       "bold graphics, dark background, industrial elements",
    },
    "maximalist": {
        "composition": "rich all-over print, dense layering, no empty space",
        "technique":   "jewel-toned gouache illustration, high detail, baroque influence",
        "avoid":       "minimalism, white space, simple patterns",
    },
    "default": {
        "composition": "balanced all-over repeat with clear tile point",
        "technique":   "mixed media illustration, versatile style",
        "avoid":       "obvious seams in the repeat",
    },
}

# ─── Générateur de prompts FLUX/SDXL ───────────────────────────────────────────

def build_prompt(keyword: str, category: str, palette: dict, style: dict) -> dict:
    """Génère 3 variantes de prompt pour la génération IA."""
    palette_desc = ", ".join(palette["colors"][:3])
    mood   = palette["mood"]
    comp   = style["composition"]
    tech   = style["technique"]
    avoid  = style["avoid"]

    base = (
        f"Seamless repeating pattern, {keyword} theme, {tech}, "
        f"{comp}, color palette: {palette_desc} ({mood}), "
        f"surface pattern design, textile print, tiling pattern, "
        f"no text, no watermark, professional quality, 8K"
    )
    dark = (
        f"Seamless repeating pattern, {keyword} theme, dark background, "
        f"deep {category} aesthetic, {tech}, {comp}, "
        f"rich jewel tones, sophisticated, textile quality, "
        f"no text, no watermark, 8K"
    )
    light = (
        f"Seamless repeating pattern, {keyword} theme, light airy background, "
        f"soft {category} style, {tech}, {comp}, "
        f"pastel tones, delicate, Scandinavian influence, "
        f"no text, no watermark, 8K"
    )
    negative = (
        f"seam visible, tile edge, repetition artifact, "
        f"blurry, low quality, watermark, text, signature, "
        f"{avoid}"
    )
    return {
        "base":     base,
        "dark":     dark,
        "light":    light,
        "negative": negative,
    }


def build_seo_tags(keyword: str, category: str, event: str | None) -> list[str]:
    """Génère jusqu'à 20 tags SEO optimisés."""
    base_tags = [
        keyword,
        f"{keyword} pattern",
        f"{keyword} fabric",
        f"{keyword} wallpaper",
        f"seamless {keyword}",
        category,
        f"{category} design",
        f"{category} pattern",
        "surface design",
        "repeat pattern",
        "fabric by the yard",
        "spoonflower fabric",
        "hand drawn",
        "artisan fabric",
        "interior decor",
    ]
    if event:
        base_tags.extend([f"{event.lower()} fabric", f"{event.lower()} pattern"])
    return list(dict.fromkeys(base_tags))[:20]  # déduplique, max 20


# ─── Appel LLM (optionnel — si GEMINI_API_KEY dispo) ──────────────────────────

def llm_enrich(brief: dict) -> dict:
    """Tente d'enrichir le brief via Gemini API. Retourne le brief inchangé si échec."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY")
    if not api_key:
        return brief

    prompt = (
        f"You are a surface pattern design expert and Spoonflower seller.\n"
        f"Given this niche: '{brief['keyword']}' in category '{brief['category']}',\n"
        f"suggest 3 specific design concepts (NOT generic — be very specific).\n"
        f"Also suggest 5 Etsy-style listing titles for this pattern.\n"
        f"Output JSON: {{concepts: [...], listing_titles: [...]}}"
    )

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 600}
    }).encode()

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash-latest:generateContent?key={api_key}"
    )
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
        text = resp["candidates"][0]["content"]["parts"][0]["text"]
        # Extrait le JSON du texte
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            enriched = json.loads(m.group())
            brief["concepts"]       = enriched.get("concepts", [])
            brief["listing_titles"] = enriched.get("listing_titles", [])
    except Exception as exc:
        print(f"  ⚠ Gemini enrichissement échoué : {exc}")
    return brief


import re  # already used above — just making sure it's imported

# ─── Main ───────────────────────────────────────────────────────────────────────

def run():
    trend_file = DATA_DIR / "trend.json"
    if not trend_file.exists():
        print("✗ data/pod/trend.json introuvable — lance d'abord agent_radar.py")
        sys.exit(1)

    report = json.loads(trend_file.read_text())
    today  = date.today().isoformat()

    top_kws = report.get("top_keywords", [])[:15]
    upcoming = report.get("upcoming_events", [])
    next_event = upcoming[0]["event"] if upcoming else None

    print(f"Art Director — {len(top_kws)} niches candidates")
    print(f"Événement prioritaire : {next_event or 'aucun'}")

    briefs = []
    # On prend les 5 meilleures niches avec catégorie connue, sinon top 3
    candidates = [k for k in top_kws if k.get("category")][:5]
    if len(candidates) < 3:
        candidates = top_kws[:3]

    for item in candidates:
        kw       = item["keyword"]
        cat      = item.get("category") or "default"
        palette  = PALETTES.get(cat, PALETTES["default"])
        style    = STYLE_DIRECTIONS.get(cat, STYLE_DIRECTIONS["default"])
        prompts  = build_prompt(kw, cat, palette, style)
        seo_tags = build_seo_tags(kw, cat, next_event)

        # Choisir le repeat type selon catégorie
        repeat_types = {
            "geometric": "half_drop",
            "botanical":  "half_brick",
            "celestial":  "basic_tile",
            "cottagecore": "mirror",
        }
        repeat = repeat_types.get(cat, "basic_tile")

        brief = {
            "keyword":        kw,
            "category":       cat,
            "rank":           item["rank"],
            "score":          item["score"],
            "event_hook":     next_event,
            "palette":        palette,
            "style_direction": style,
            "prompts":        prompts,
            "repeat_type":    repeat,
            "seo_tags":       seo_tags,
            "platforms":      {
                "spoonflower": {
                    "product_types": ["fabric", "wallpaper", "giftwrap"],
                    "min_resolution": f"{PLATFORM_SPECS['spoonflower']['fabric_min_px']}px",
                    "notes": PLATFORM_SPECS["spoonflower"]["notes"],
                },
                "society6": {
                    "product_types": ["art_print", "phone_case", "tapestry", "throw_pillow"],
                    "min_resolution": f"{PLATFORM_SPECS['society6']['art_print_px']}px",
                    "notes": PLATFORM_SPECS["society6"]["notes"],
                },
                "redbubble": {
                    "product_types": ["sticker", "poster", "tshirt", "tote_bag", "shower_curtain"],
                    "min_resolution": f"{PLATFORM_SPECS['redbubble']['poster_px']}px",
                    "notes": PLATFORM_SPECS["redbubble"]["notes"],
                },
            },
            "listing_titles": [],
            "concepts":       [],
        }

        brief = llm_enrich(brief)
        briefs.append(brief)
        print(f"  ✓ Brief : [{cat}] {kw}")

    output = {
        "generated_at": today,
        "briefs": briefs,
        "next_event": next_event,
        "production_priority": [b["keyword"] for b in briefs],
    }

    out_file = DATA_DIR / "cahier_des_charges.json"
    out_file.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n✓ {len(briefs)} briefs → {out_file}")
    return output


if __name__ == "__main__":
    run()
