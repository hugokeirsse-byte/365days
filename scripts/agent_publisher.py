#!/usr/bin/env python3
"""
Agent Publisher
Prépare le paquet de publication KDP + Etsy après validation du GATE 2.
Génère metadata KDP, fiche Etsy, et PUBLICATION_READY.md lisible par Hugo.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

def main():
    # 1. Résolution du BRIEF_ID (CLI ou Variable d'environnement)
    brief_id = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BRIEF_ID")
    if not brief_id:
        print("Erreur : BRIEF_ID doit être fourni en argument CLI ou via la variable d'environnement BRIEF_ID.")
        sys.exit(1)

    # Définition des chemins
    base_dir = Path("products/coloring_books/_gate1") / brief_id
    pub_dir = base_dir / "publication"
    
    # Recherche de kdp_package.json
    kdp_package_path = pub_dir / "kdp_package.json"
    if not kdp_package_path.exists():
        kdp_package_path = base_dir / "kdp_package.json"

    if not kdp_package_path.exists():
        print(f"Erreur : kdp_package.json introuvable pour le brief {brief_id}.")
        sys.exit(1)

    # Lecture et validation de kdp_package.json
    try:
        with open(kdp_package_path, "r", encoding="utf-8") as f:
            package_data = json.load(f)
    except Exception as e:
        print(f"Erreur lors de la lecture de kdp_package.json : {e}")
        sys.exit(1)

    # Vérification de la validation du Gate 2
    ready_for_gate2 = package_data.get("ready_for_gate2")
    if not ready_for_gate2 or str(ready_for_gate2).lower() != "true":
        print("Erreur : ready_for_gate2 n'est pas à 'true' dans kdp_package.json. Le Gate 2 doit être approuvé.")
        sys.exit(1)

    # Extraction des métadonnées de base
    title = package_data.get("title", "Coloring Book")
    subtitle = package_data.get("subtitle", "")
    author = package_data.get("author", "Creative Press")
    theme = package_data.get("theme", "Coloring")
    target_audience = package_data.get("target_audience", "Adults")
    categories = package_data.get("categories", ["Activity Books", "Crafts & Hobbies"])

    # 2. Appel à l'API Gemini ou Fallback
    api_key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    
    gemini_success = False
    generated_content = {}

    if api_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        
        prompt = f"""You are an expert copywriter for Amazon KDP and Etsy. Based on the following coloring book metadata, generate optimized marketing copy.
        
        Metadata:
        - Title: {title}
        - Subtitle: {subtitle}
        - Author: {author}
        - Theme: {theme}
        - Target Audience: {target_audience}
        
        You must return a JSON object with exactly the following keys:
        - "kdp_description": A compelling blurb for Amazon KDP (150-200 words).
        - "kdp_keywords": Exactly 7 highly relevant search keywords/phrases for KDP.
        - "etsy_title": A keyword-stuffed Etsy title (max 140 characters, keywords-first).
        - "etsy_description": A detailed, SEO-optimized Etsy product description (500-800 words) highlighting benefits, features, and digital/physical nature.
        - "etsy_tags": Exactly 13 relevant tags for Etsy.
        
        Return ONLY the raw JSON object. Do not wrap it in markdown code blocks or any other text."""

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
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
                generated_content = json.loads(text_response.strip())
                gemini_success = True
        except Exception as e:
            print(f"Warning: Échec de l'appel Gemini ({e}). Utilisation du mode fallback statique.")

    # 3. Mode Fallback (Templates statiques)
    if not gemini_success:
        kdp_desc = (
            f"Unleash your creativity with '{title}: {subtitle}'. This beautifully crafted coloring book "
            f"is specifically designed for {target_audience} who love {theme}. Inside, you will find "
            f"a stunning collection of high-quality, unique illustrations designed to provide hours of "
            f"relaxation, stress relief, and artistic expression. Each page is single-sided to prevent "
            f"bleed-through, making it perfect for markers, gel pens, or colored pencils. Whether you are "
            f"an experienced artist or just starting your coloring journey, this book offers a perfect "
            f"escape into a world of color and imagination. It also makes a wonderful gift for friends "
            f"and family who appreciate the therapeutic benefits of coloring. Grab your copy today and "
            f"start coloring your way to peace and tranquility!"
        )
        
        kdp_keywords = [
            f"{theme} coloring book",
            f"coloring book for {target_audience}",
            f"creative coloring pages",
            f"relaxation coloring",
            f"stress relief coloring",
            f"artistic coloring book",
            f"beautiful {theme} designs"
        ][:7]
        
        etsy_title = f"{title} Coloring Book PDF - Printable {theme} Pages for {target_audience}"[:140]
        
        etsy_desc = (
            f"Welcome to our creative studio! Bring your imagination to life with the '{title}' printable coloring book.\n\n"
            f"This digital download features a gorgeous collection of {theme}-themed coloring pages, perfect for {target_audience} "
            f"seeking a relaxing and mindful artistic escape. Designed with love and attention to detail, these pages offer "
            f"the perfect balance of complexity and simplicity to suit all skill levels.\n\n"
            f"--- WHAT YOU WILL RECEIVE ---\n"
            f"- 1 High-Resolution PDF file containing all coloring pages.\n"
            f"- Standard Letter Size (8.5 x 11 inches) for easy printing.\n"
            f"- Clean, crisp, high-quality black and white vector-style illustrations.\n\n"
            f"--- WHY YOU WILL LOVE THIS BOOK ---\n"
            f"- Stress Relief & Mindfulness: Coloring is a proven way to reduce anxiety and find your inner calm.\n"
            f"- Print Unlimited Times: Print your favorite designs as many times as you like on your preferred paper.\n"
            f"- Perfect for All Mediums: Great for colored pencils, markers, crayons, or watercolors (we recommend printing on heavy cardstock for wet mediums).\n\n"
            f"--- PLEASE NOTE ---\n"
            f"This is a DIGITAL DOWNLOAD product. No physical item will be shipped to you. "
            f"Due to the digital nature of this product, all sales are final. For personal use only. "
            f"Commercial reproduction or resale is strictly prohibited.\n\n"
            f"Thank you for supporting our shop! Happy coloring!"
        )
        
        etsy_tags = [
            "coloring book", "printable coloring", f"{theme} coloring", "digital download",
            "pdf coloring book", "adult coloring", "kids coloring", "stress relief",
            "mindful coloring", "printable pdf", "creative hobby", "coloring pages", "diy craft"
        ][:13]
        
        generated_content = {
            "kdp_description": kdp_desc,
            "kdp_keywords": kdp_keywords,
            "etsy_title": etsy_title,
            "etsy_description": etsy_desc,
            "etsy_tags": etsy_tags
        }

    # Assurer la création du dossier de publication
    pub_dir.mkdir(parents=True, exist_ok=True)

    # 4. Écriture des 3 fichiers requis

    # Fichier 1 : kdp_metadata.json
    kdp_metadata = {
        "title": title,
        "subtitle": subtitle,
        "author": author,
        "description": generated_content.get("kdp_description"),
        "keywords": generated_content.get("kdp_keywords")[:7],
        "categories": categories,
        "price": 8.99
    }
    with open(pub_dir / "kdp_metadata.json", "w", encoding="utf-8") as f:
        json.dump(kdp_metadata, f, indent=2, ensure_ascii=False)

    # Fichier 2 : etsy_listing.json
    etsy_listing = {
        "title": generated_content.get("etsy_title")[:140],
        "description": generated_content.get("etsy_description"),
        "tags": generated_content.get("etsy_tags")[:13]
    }
    with open(pub_dir / "etsy_listing.json", "w", encoding="utf-8") as f:
        json.dump(etsy_listing, f, indent=2, ensure_ascii=False)

    # Fichier 3 : PUBLICATION_READY.md (Formaté pour Hugo)
    hugo_ready_content = f"""---
title: "Publication Ready: {title}"
date: "{datetime.now().isoformat()}"
brief_id: "{brief_id}"
draft: false
---

# Publication Package Ready for {title}

This package has been fully prepared and validated. Below is the summary of the generated assets.

## KDP Checklist
- [ ] **Title**: {title}
- [ ] **Subtitle**: {subtitle}
- [ ] **Author**: {author}
- [ ] **Price**: $8.99
- [ ] **Categories**: {", ".join(categories)}
- [ ] **Keywords**: {", ".join(kdp_metadata["keywords"])}

### KDP Description