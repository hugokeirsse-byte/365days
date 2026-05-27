#!/usr/bin/env python3
"""
Agent Publisher
Prepares KDP and Etsy publication packages after GATE 2 approval.
Generates KDP metadata, Etsy listing details, and a PUBLICATION_READY.md report.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Default configuration
DEFAULT_MODEL = "gemini-2.5-flash"
KDP_PRICE = 8.99
ETSY_PRICE = 4.99


def log(message: str, level: str = "INFO"):
    print(f"[{level}] {message}")


def load_kdp_package(package_path: Path) -> dict:
    """Loads and validates the kdp_package.json file."""
    if not package_path.exists():
        raise FileNotFoundError(f"kdp_package.json not found at {package_path}")
    
    with open(package_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Verify GATE 2 approval status
    if not data.get("ready_for_gate2", False) and not data.get("ready_for_publication", False):
        log("Warning: ready_for_gate2 is not set to true in kdp_package.json. Proceeding anyway.", "WARN")
        
    return data


def call_gemini_api(api_key: str, model: str, prompt: str) -> dict:
    """Calls the Gemini API using standard urllib to generate structured JSON."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        log(f"Contacting Gemini API ({model})...")
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            
            # Extract text from Gemini response structure
            text_response = result["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text_response)
    except Exception as e:
        log(f"Gemini API call failed: {e}. Using fallback generator.", "ERROR")
        return {}


def generate_fallback_metadata(metadata: dict) -> dict:
    """Generates static fallback assets if Gemini is unavailable."""
    log("Generating fallback assets from local templates...", "INFO")
    title = metadata.get("title", "Premium Coloring Book")
    theme = metadata.get("theme", "Beautiful Designs")
    audience = metadata.get("target_audience", "Adults and Teens")
    
    kdp_blurb = (
        f"Discover the wonderful world of {theme}! This premium coloring book is specifically designed "
        f"for {audience} seeking relaxation, mindfulness, and creative expression. Inside, you will find "
        f"high-quality, beautifully detailed illustrations crafted to provide hours of stress relief and artistic fun. "
        f"Perfect for colored pencils, markers, or gel pens. Grab your copy today and start your coloring journey!"
    )
    
    etsy_title = f"{theme} Coloring Book PDF | Printable Coloring Pages for {audience} | Digital Download"
    if len(etsy_title) > 140:
        etsy_title = etsy_title[:137] + "..."
        
    etsy_description = (
        f"Welcome to our creative studio!\n\n"
        f"Bring your imagination to life with this gorgeous printable {theme} coloring book, "
        f"perfectly tailored for {audience}.\n\n"
        f"--- WHAT YOU GET ---\n"
        f"- High-resolution PDF file ready for instant printing.\n"
        f"- Beautifully curated coloring pages featuring unique {theme} designs.\n"
        f"- Standard letter size format (8.5 x 11 inches).\n\n"
        f"--- HOW TO DOWNLOAD ---\n"
        f"1. Purchase the listing.\n"
        f"2. Once payment is confirmed, download your files directly from Etsy.\n"
        f"3. Print at home or at your local print shop as many times as you like!\n\n"
        f"Please note: This is a DIGITAL DOWNLOAD product. No physical item will be shipped."
    )
    
    # Basic keyword extraction
    keywords = [t.strip().lower() for t in theme.split() if len(t) > 3][:4]
    keywords += [a.strip().lower() for a in audience.split() if len(a) > 3][:3]
    while len(keywords) < 7:
        keywords.append("coloring book")
    
    tags = [f"{theme[:15]} art", "printable pdf", "coloring pages", "digital download", "instant print"]
    while len(tags) < 13:
        tags.append(f"coloring {len(tags)}")
        
    return {
        "kdp_blurb": kdp_blurb,
        "etsy_title": etsy_title,
        "etsy_description": etsy_description,
        "etsy_tags": tags[:13],
        "kdp_keywords": keywords[:7]
    }


def build_prompt(metadata: dict) -> str:
    """Constructs the prompt for Gemini to generate optimized marketing copy."""
    return f"""
You are an expert KDP and Etsy publisher. Based on the following book metadata, generate optimized publication assets.

Book Metadata:
{json.dumps(metadata, indent=2)}

Requirements:
1. KDP Blurb: 150-200 words, engaging, highlighting benefits, formatting with clean spacing.
2. Etsy Title: Max 140 characters, keywords-first, separated by pipes or commas (e.g., "Printable Coloring Book PDF | Theme Pages for Kids | ...").
3. Etsy Description: 500-800 words, highly SEO-optimized, includes sections like "What's Included", "How to Download", "Terms of Use".
4. Etsy Tags: Exactly 13 highly relevant search tags (max 20 chars per tag).
5. KDP Keywords: Exactly 7 highly relevant search keywords/phrases.

Respond ONLY with a JSON object matching this schema:
{{
  "kdp_blurb": "string (150-200 words)",
  "etsy_title": "string (max 140 chars)",
  "etsy_description": "string (500-800 words)",
  "etsy_tags": ["string", "string", ... 13 total],
  "kdp_keywords": ["string", "string", ... 7 total]
}}
"""


def write_publication_ready_md(output_dir: Path, brief_id: str, kdp_meta: dict, etsy_meta: dict) -> None:
    """Generates the PUBLICATION_READY.md file with Hugo front matter and checklists."""
    md_content = f"""---
title: "Publication Package - {brief_id}"
date: {import_date()}
draft: false
brief_id: "{brief_id}"
type: "publication"
---

# Publication Ready Package: {brief_id}

This package contains all the metadata and assets required to publish your coloring book on Amazon KDP and Etsy.

---

## 📋 KDP PUBLISHING CHECKLIST

- [ ] **Title**: `{kdp_meta.get('title')}`
- [ ] **Subtitle**: `{kdp_meta.get('subtitle', '')}`
- [ ] **Author**: `{kdp_meta.get('author')}`
- [ ] **Description (Blurb)**: Copy from `kdp_metadata.json` (or see below)
- [ ] **Primary Category**: `{kdp_meta.get('categories', [''])[0]}`
- [ ] **Keywords**: Enter the 7 keywords listed in `kdp_metadata.json`
- [ ] **Upload Interior**: Select your generated PDF interior
- [ ] **Upload Cover**: Select your generated PDF cover
- [ ] **Pricing**: Set price to **${kdp_meta.get('price', 8.99)}**

### KDP Blurb Preview