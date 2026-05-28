import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

def log(message: str, level: str = "INFO"):
    print(f"[{level}] {message}")

def main():
    # 1. Resolve BRIEF_ID
    brief_id = None
    if len(sys.argv) > 1:
        brief_id = sys.argv[1]
    else:
        brief_id = os.environ.get("BRIEF_ID")

    if not brief_id:
        log("Error: BRIEF_ID must be provided as a CLI argument or environment variable.", "ERROR")
        sys.exit(1)

    # Define paths
    base_dir = Path("products/coloring_books/_gate1") / brief_id
    publication_dir = base_dir / "publication"
    
    # Locate kdp_package.json
    kdp_package_paths = [
        publication_dir / "kdp_package.json",
        base_dir / "kdp_package.json"
    ]
    
    kdp_package_path = None
    for path in kdp_package_paths:
        if path.exists():
            kdp_package_path = path
            break

    if not kdp_package_path:
        log(f"Error: kdp_package.json not found for brief '{brief_id}'. Checked paths: {[str(p) for p in kdp_package_paths]}", "ERROR")
        sys.exit(1)

    # Read and verify kdp_package.json
    try:
        with open(kdp_package_path, "r", encoding="utf-8") as f:
            kdp_package = json.load(f)
    except Exception as e:
        log(f"Error reading {kdp_package_path}: {e}", "ERROR")
        sys.exit(1)

    if not kdp_package.get("ready_for_gate2"):
        log("Error: kdp_package.json does not have 'ready_for_gate2' set to true. Gate 2 approval is required.", "ERROR")
        sys.exit(1)

    # Extract metadata from package or brief
    title = kdp_package.get("title") or kdp_package.get("metadata", {}).get("title") or f"Coloring Book {brief_id}"
    author = kdp_package.get("author") or kdp_package.get("metadata", {}).get("author") or "Creative Press"
    theme = kdp_package.get("theme") or kdp_package.get("metadata", {}).get("theme") or "Coloring"
    audience = kdp_package.get("target_audience") or kdp_package.get("metadata", {}).get("target_audience") or "Adults"

    # Ensure publication directory exists
    publication_dir.mkdir(parents=True, exist_ok=True)

    # 2. Call Gemini API or Fallback
    api_key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    
    generated_data = None

    if api_key:
        log(f"Using Gemini API ({model}) to generate marketing copy...")
        prompt = f"""
        You are an expert copywriter for Amazon KDP and Etsy coloring books.
        Based on the following book details:
        Title: {title}
        Theme: {theme}
        Audience: {audience}
        Author: {author}

        Generate a JSON object with the following keys:
        - kdp_description: A compelling book description for Amazon KDP (150-200 words).
        - kdp_keywords: An array of exactly 7 highly relevant search keywords/phrases for KDP.
        - etsy_title: A keyword-stuffed Etsy title (max 140 characters, keywords-first).
        - etsy_description: A highly optimized SEO description for Etsy (500-800 words), highlighting benefits, features, and digital download aspect.
        - etsy_tags: An array of exactly 13 search tags for Etsy.

        Return ONLY the raw JSON object. Do not wrap it in markdown formatting or code blocks.
        """
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                text_response = res_data["candidates"][0]["content"]["parts"][0]["text"]
                generated_data = json.loads(text_response.strip())
                log("Successfully generated copy via Gemini API.")
        except Exception as e:
            log(f"Gemini API call failed or returned invalid JSON: {e}. Falling back to static templates.", "WARNING")

    if not generated_data:
        log("Using static fallback templates for marketing copy.")
        # Fallback generation
        kdp_desc = (
            f"Discover the ultimate {theme} coloring book designed specifically for {audience}! "
            f"Created by {author}, this book offers a unique collection of beautifully crafted illustrations "
            f"that will help you unwind, relax, and express your creativity. Whether you are a beginner or an "
            f"experienced colorist, you will find hours of enjoyment and stress relief within these pages. "
            f"Perfect as a gift for yourself or a loved one who loves {theme}!"
        )
        etsy_title = f"{theme} Coloring Book for {audience} | Printable PDF Pages | {title} by {author}"[:140]
        etsy_desc = (
            f"Welcome to our shop! Enjoy instant relaxation with our '{title}' coloring book, "
            f"perfectly tailored for {audience}.\n\n"
            f"This is a DIGITAL DOWNLOAD. No physical product will be shipped. You will receive high-quality "
            f"printable PDF files that you can print at home as many times as you like!\n\n"
            f"--- WHY YOU WILL LOVE THIS COLORING BOOK ---\n"
            f"- Beautiful {theme} themed illustrations designed to inspire creativity.\n"
            f"- High-resolution pages for clean, crisp prints.\n"
            f"- Perfect for stress relief, mindfulness, and artistic expression.\n"
            f"- Great for all skill levels.\n\n"
            f"--- WHAT IS INCLUDED ---\n"
            f"- 1 High-Quality PDF file containing the complete coloring book.\n"
            f"- Standard letter size (8.5 x 11 inches).\n\n"
            f"Thank you for supporting our creative journey! Happy coloring!"
        )
        kdp_keywords = [
            f"{theme} coloring book",
            f"coloring book for {audience}",
            f"{theme} designs",
            "stress relief coloring",
            "creative coloring pages",
            f"{author} books",
            "mindful coloring"
        ]
        etsy_tags = [
            "coloring book",
            "printable coloring",
            "digital download",
            f"{theme} coloring",
            f"gift for {audience}",
            "pdf coloring pages",
            "adult coloring",
            "kids coloring",
            "diy craft",
            "stress relief",
            "mindfulness art",
            "printable pdf",
            "coloring pages"
        ]
        generated_data = {
            "kdp_description": kdp_desc,
            "kdp_keywords": kdp_keywords,
            "etsy_title": etsy_title,
            "etsy_description": etsy_desc,
            "etsy_tags": etsy_tags
        }

    # 3. Write output files
    
    # kdp_metadata.json
    kdp_metadata = {
        "title": title,
        "author": author,
        "description": generated_data.get("kdp_description"),
        "keywords": generated_data.get("kdp_keywords")[:7],
        "categories": ["Coloring Books", "Activity Books"],
        "price": 8.99
    }
    kdp_metadata_path = publication_dir / "kdp_metadata.json"
    with open(kdp_metadata_path, "w", encoding="utf-8") as f:
        json.dump(kdp_metadata, f, indent=2, ensure_ascii=False)
    log(f"Wrote {kdp_metadata_path}")

    # etsy_listing.json
    etsy_listing = {
        "title": generated_data.get("etsy_title")[:140],
        "description": generated_data.get("etsy_description"),
        "tags": generated_data.get("etsy_tags")[:13]
    }
    etsy_listing_path = publication_dir / "etsy_listing.json"
    with open(etsy_listing_path, "w", encoding="utf-8") as f:
        json.dump(etsy_listing, f, indent=2, ensure_ascii=False)
    log(f"Wrote {etsy_listing_path}")

    # PUBLICATION_READY.md (Hugo-compatible frontmatter)
    pub_ready_path = publication_dir / "PUBLICATION_READY.md"
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    markdown_content = f"""---
title: "Publication Ready: {title}"
date: {current_date}
brief_id: "{brief_id}"
draft: false
---

# Ready for Publication: {title}

This package has been successfully prepared and validated for publication on Amazon KDP and Etsy.

## KDP Publication Checklist

- [ ] **Title**: `{kdp_metadata['title']}`
- [ ] **Author**: `{kdp_metadata['author']}`
- [ ] **Price**: `${kdp_metadata['price']}`
- [ ] **Categories**: {", ".join(kdp_metadata['categories'])}
- [ ] **Keywords**:
{chr(10).join([f"  - {kw}" for kw in kdp_metadata['keywords']])}

### KDP Description
> {kdp_metadata['description']}

---

## Etsy Listing Details

- **Title**: `{etsy_listing['title']}`
- **Tags**:
{chr(10).join([f"  - {tag}" for tag in etsy_listing['tags']])}

### Etsy Description
{etsy_listing['description']}

---

*Generated on {current_date} — ready for upload*
"""
    with open(pub_ready_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    log(f"Wrote {pub_ready_path}")

    log("Publication package complete.")
    log(f"Files written to: {publication_dir}")
    log("Next steps:")
    log("  1. Upload PDF to Amazon KDP")
    log("  2. Use kdp_metadata.json for title/description/keywords")
    log("  3. Review PUBLICATION_READY.md for full checklist")


if __name__ == "__main__":
    main()