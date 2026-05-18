"""
Pipeline CHATEAU LOCAL — produits B2B POD pour partenariats monuments.

Consomme data/chateau_local/<chateau>.json (config Hugo) et génère
5 produits POD prêts à proposer au gérant de la boutique :

1. codex_carnet         — couverture carnet A5 simili-cuir
2. plans_anciens        — poster cartographique vintage 3 tailles
3. mug_medieval         — wrap mug 11oz style céramique ancienne
4. mini_livre_legendes  — PDF livret 10×15cm KDP-ready
5. empreinte_plaque     — design plaque déco 15×15cm laser-ready

Identité visuelle : palette dérivée des armoiries + atmosphère du château.
Texte 100% overlay Pillow (zéro gibberish). Illustrations via Pollinations.

Variables d'env :
  CHATEAU=example_chateau    nom du fichier JSON dans data/chateau_local/
  PRODUITS=all               liste produits ou 'all'
"""

from __future__ import annotations

import csv
import json
import math
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    print("ERREUR : Pillow non installé")
    sys.exit(2)

try:
    from reportlab.lib.units import inch as INCH
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "chateau_local"
OUTPUT_DIR = ROOT / "products" / "chateau_local"
USER_AGENT = "ChateauLocalProducer/1.0"
TIMEOUT = 180


sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from lib.specs_visual_identity import (  # noqa: E402
        get_font, draw_text_centered, wrap_text, find_optimal_size,
        FONTS_DIR,
    )
except ImportError:
    print("ERREUR : impossible d'importer specs_visual_identity")
    sys.exit(2)


# ============================================================
# POLLINATIONS (illustrations atmosphériques sans texte)
# ============================================================

def pollinations_url(prompt: str, seed: int, w: int, h: int) -> str:
    encoded = urllib.parse.quote(prompt, safe="")
    return (f"https://image.pollinations.ai/prompt/{encoded}"
            f"?model=flux&width={w}&height={h}"
            f"&seed={seed}&nologo=true&private=true&enhance=true")


def http_get(url: str, dest: Path, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
            if len(data) < 5000:
                raise ValueError(f"too short {len(data)}")
            dest.write_bytes(data)
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"    retry {attempt+1}/{retries} : {exc}")
            time.sleep(6 + attempt * 6)
    return False


# ============================================================
# PALETTE HÉRALDIQUE → RGB
# ============================================================

HERALDIC_RGB = {
    "azur": (40, 70, 150),
    "or": (200, 165, 70),
    "argent": (240, 240, 235),
    "gueules": (170, 35, 40),  # rouge
    "sable": (30, 30, 35),
    "sinople": (60, 110, 60),  # vert
    "pourpre": (110, 50, 110),
}


def palette_from_armoiries(palette_names: list[str]) -> dict:
    """Convertit ['azur', 'or'] en couleurs utilisables."""
    main = HERALDIC_RGB.get(palette_names[0].lower() if palette_names else "azur",
                              HERALDIC_RGB["azur"])
    accent = HERALDIC_RGB.get(palette_names[1].lower() if len(palette_names) > 1 else "or",
                                HERALDIC_RGB["or"])
    third = HERALDIC_RGB.get(palette_names[2].lower() if len(palette_names) > 2 else "argent",
                               HERALDIC_RGB["argent"])
    return {"main": main, "accent": accent, "third": third}


# ============================================================
# PRODUIT 1 : CODEX CARNET (couverture A5 simili-cuir)
# ============================================================

def produce_codex_carnet(config: dict, out_dir: Path) -> dict:
    print("  → 1. Codex Carnet (couverture A5)")
    # A5 KDP = 5.83×8.27" = 1749×2481 px @ 300 DPI bleed
    w, h = 1800, 2550
    palette = palette_from_armoiries(config.get("armoiries_palette", ["azur", "or"]))

    # Fond simili-cuir : texture sombre dérivée de la palette main
    bg_path = out_dir / "raw_leather.png"
    leather_prompt = (
        f"seamless aged leather book cover texture, "
        f"deep {config['armoiries_palette'][0] if config.get('armoiries_palette') else 'dark blue'} "
        f"tones with worn patina, embossed edges, vintage medieval grimoire feel, "
        f"no text no letters no symbols"
    )
    seed = hash(config["chateau_id"] + "_codex") % 99999
    if not http_get(pollinations_url(leather_prompt, seed, 1024, 1536), bg_path):
        print("     ✗ leather generation failed")
        return {"ok": False}

    bg = Image.open(bg_path).convert("RGB")
    # Resize to cover area
    bg_ratio = bg.width / bg.height
    target_ratio = w / h
    if bg_ratio > target_ratio:
        new_w = int(bg.height * target_ratio)
        off = (bg.width - new_w) // 2
        bg = bg.crop((off, 0, off + new_w, bg.height))
    else:
        new_h = int(bg.width / target_ratio)
        off = (bg.height - new_h) // 2
        bg = bg.crop((0, off, bg.width, off + new_h))
    bg = bg.resize((w, h), Image.LANCZOS)

    # Désature un peu pour effet cuir uniforme
    bg = bg.filter(ImageFilter.GaussianBlur(radius=4))

    canvas = bg.convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # Cadre doré ornemental
    margin = 100
    for offset in (0, 8, 16):
        draw.rectangle(
            [margin - offset, margin - offset, w - margin + offset, h - margin + offset],
            outline=palette["accent"], width=3 if offset == 0 else 1,
        )

    # Nom du château en haut
    name = config["chateau_name"].upper()
    f_title = get_font("title", 130)
    draw_text_centered(draw, name, (w // 2, 380), f_title,
                        palette["accent"], letter_spacing=4)

    # Année
    annee = config.get("annee_fondation", "")
    if annee:
        f_year = get_font("title", 60)
        draw_text_centered(draw, f"FONDÉ EN {annee}", (w // 2, 500),
                            f_year, palette["third"], letter_spacing=8)

    # Ligne ornementale
    draw.line([(w // 2 - 200, 580), (w // 2 + 200, 580)],
               fill=palette["accent"], width=3)

    # Devise latine
    devise = config.get("devise_latine", "")
    if devise:
        f_devise = get_font("body", 50)
        draw_text_centered(draw, f"« {devise} »", (w // 2, h - 600),
                            f_devise, palette["third"], letter_spacing=2)

    # Subtitle
    f_sub = get_font("body", 42)
    draw_text_centered(draw, "CODEX & CARNET DE NOTES", (w // 2, h - 480),
                        f_sub, palette["accent"], letter_spacing=6)

    # Village + pays
    village = config.get("village", "")
    country = config.get("country", "")
    if village:
        f_loc = get_font("body", 36)
        draw_text_centered(draw, f"{village} · {country}", (w // 2, h - 350),
                            f_loc, palette["third"], letter_spacing=4)

    out_path = out_dir / "codex_carnet_cover.png"
    canvas.save(out_path, "PNG", optimize=True)
    if bg_path.exists():
        bg_path.unlink()

    return {
        "ok": True,
        "product_id": "codex_carnet",
        "title": f"Codex {config['chateau_name']} — Carnet de Notes Premium",
        "format": "A5 paperback KDP",
        "price_eur": 14.99,
        "files": [str(out_path.name)],
    }


# ============================================================
# PRODUIT 2 : PLANS ANCIENS (poster cartographique)
# ============================================================

def produce_plans_anciens(config: dict, out_dir: Path) -> dict:
    print("  → 2. Plans Anciens (poster vintage)")
    # A3 portrait @ 300 DPI = 3508×4961
    w, h = 3000, 4200  # version optimisée
    palette = palette_from_armoiries(config.get("armoiries_palette", ["azur", "or"]))

    map_prompt = (
        f"vintage 18th century cartographic map style illustration, "
        f"plan of medieval castle and surrounding village, {config['atmosphere_visuelle']}, "
        f"aged parchment paper texture, sepia tones with ink details, "
        f"decorative compass rose corner, ornamental border, "
        f"no text no letters no numbers anywhere"
    )
    bg_path = out_dir / "raw_map.png"
    seed = hash(config["chateau_id"] + "_map") % 99999
    if not http_get(pollinations_url(map_prompt, seed, 1024, 1456), bg_path):
        print("     ✗ map generation failed")
        return {"ok": False}

    bg = Image.open(bg_path).convert("RGB")
    bg_ratio = bg.width / bg.height
    target_ratio = w / h
    if bg_ratio > target_ratio:
        new_w = int(bg.height * target_ratio)
        off = (bg.width - new_w) // 2
        bg = bg.crop((off, 0, off + new_w, bg.height))
    else:
        new_h = int(bg.width / target_ratio)
        off = (bg.height - new_h) // 2
        bg = bg.crop((0, off, bg.width, off + new_h))
    canvas = bg.resize((w, h), Image.LANCZOS).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # Cartouche titre en haut
    f_title = get_font("title", 110)
    title_text = config["chateau_name"].upper()
    draw_text_centered(draw, title_text, (w // 2, 200),
                        f_title, (50, 30, 15), letter_spacing=6)

    # Sous-titre
    f_sub = get_font("body", 55)
    draw_text_centered(draw, f"PLAN ANCIEN · {config.get('village', '')}",
                        (w // 2, 320), f_sub, (80, 50, 30), letter_spacing=8)

    # Cartouche bas : coords + altitude
    coords = config.get("gps_coords", "")
    alt = config.get("altitude_m", "")
    f_coord = get_font("body", 38)
    if coords:
        draw_text_centered(draw, coords, (w // 2, h - 240),
                            f_coord, (80, 50, 30), letter_spacing=3)
    if alt:
        draw_text_centered(draw, f"ALTITUDE {alt} M", (w // 2, h - 180),
                            f_coord, (100, 70, 40), letter_spacing=4)

    out_path = out_dir / "plans_anciens_A3.png"
    canvas.save(out_path, "PNG", optimize=True)
    if bg_path.exists():
        bg_path.unlink()

    # Variantes A4 + A2 (resize)
    for size_name, ratio_w in [("A4", 0.7), ("A2", 1.4)]:
        new_w = int(w * ratio_w)
        new_h = int(h * ratio_w)
        Image.open(out_path).convert("RGB").resize(
            (new_w, new_h), Image.LANCZOS,
        ).save(out_dir / f"plans_anciens_{size_name}.png",
                "PNG", optimize=True)

    return {
        "ok": True,
        "product_id": "plans_anciens",
        "title": f"Plan Ancien {config['chateau_name']} — Poster Cartographique Vintage",
        "format": "A4/A3/A2 print",
        "price_eur": 24.99,
        "files": ["plans_anciens_A4.png", "plans_anciens_A3.png", "plans_anciens_A2.png"],
    }


# ============================================================
# PRODUIT 3 : MUG MÉDIÉVAL (wrap 11oz)
# ============================================================

def produce_mug_medieval(config: dict, out_dir: Path) -> dict:
    print("  → 3. Mug Médiéval (wrap 11oz)")
    # Mug 11oz wrap = 8.5×3.5" @ 300 DPI = 2550×1050 (paysage)
    w, h = 2550, 1050
    palette = palette_from_armoiries(config.get("armoiries_palette", ["azur", "or"]))

    # Fond pierre/céramique
    stone_prompt = (
        f"seamless ancient stone ceramic texture, medieval mug surface look, "
        f"{config.get('couleur_dominante_pierre', 'aged sandstone')} tones, "
        f"slightly worn patina, no text no letters no symbols, "
        f"horizontal panoramic format"
    )
    bg_path = out_dir / "raw_stone.png"
    seed = hash(config["chateau_id"] + "_mug") % 99999
    if not http_get(pollinations_url(stone_prompt, seed, 1536, 768), bg_path):
        print("     ✗ stone texture generation failed")
        return {"ok": False}

    bg = Image.open(bg_path).convert("RGB").resize((w, h), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=2))
    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    # Voile sombre pour lisibilité
    overlay = Image.new("RGBA", (w, h), (15, 15, 20, 90))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # Texte central : nom du château
    name = config["chateau_name"].upper()
    f_main = get_font("display", 220)
    draw_text_centered(draw, name, (w // 2, h // 2 - 60),
                        f_main, palette["accent"], letter_spacing=14)

    # Année
    annee = config.get("annee_fondation", "")
    f_year = get_font("title", 80)
    if annee:
        draw_text_centered(draw, f"EST. {annee}", (w // 2, h // 2 + 130),
                            f_year, palette["third"], letter_spacing=12)

    # Ornements aux deux extrémités
    for x_anchor in (200, w - 200):
        draw.line([(x_anchor - 40, h // 2 - 10),
                    (x_anchor + 40, h // 2 - 10)],
                   fill=palette["accent"], width=4)
        draw.line([(x_anchor - 40, h // 2 + 10),
                    (x_anchor + 40, h // 2 + 10)],
                   fill=palette["accent"], width=4)

    out_path = out_dir / "mug_medieval_wrap.png"
    canvas.save(out_path, "PNG", optimize=True)
    if bg_path.exists():
        bg_path.unlink()

    return {
        "ok": True,
        "product_id": "mug_medieval",
        "title": f"Mug {config['chateau_name']} — Tasse Médiévale Vintage",
        "format": "Mug 11oz wrap PNG",
        "price_eur": 17.99,
        "files": [out_path.name],
        "manufacturing": "Printify ceramic mug 11oz / Prodigi enamel mug",
    }


# ============================================================
# PRODUIT 4 : MINI LIVRE LÉGENDES (PDF KDP)
# ============================================================

def produce_mini_livre_legendes(config: dict, out_dir: Path) -> dict:
    print("  → 4. Mini Livre Légendes (PDF KDP)")
    if not REPORTLAB_OK:
        print("     ⊝ reportlab non dispo")
        return {"ok": False}

    # Format livret 10×15cm = 4×6" @ 300 DPI portrait
    TRIM_W = 4 * INCH   # 288 pt
    TRIM_H = 6 * INCH   # 432 pt
    MARGIN_INNER = 0.5 * INCH
    MARGIN_OUTER = 0.4 * INCH
    MARGIN_TOP = 0.5 * INCH
    MARGIN_BOTTOM = 0.5 * INCH

    palette = palette_from_armoiries(config.get("armoiries_palette", ["azur", "or"]))

    # Charge fonts
    try:
        pdfmetrics.registerFont(TTFont("ChateauTitle", str(FONTS_DIR / "Anton-Regular.ttf")))
        pdfmetrics.registerFont(TTFont("ChateauBody",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"))
        pdfmetrics.registerFont(TTFont("ChateauBodyIt",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"))
        F_TITLE = "ChateauTitle"
        F_BODY = "ChateauBody"
        F_IT = "ChateauBodyIt"
    except Exception:
        F_TITLE = "Helvetica-Bold"
        F_BODY = "Helvetica"
        F_IT = "Helvetica-Oblique"

    pdf_path = out_dir / "mini_livre_legendes.pdf"
    c = pdf_canvas.Canvas(str(pdf_path), pagesize=(TRIM_W, TRIM_H))
    c.setTitle(f"Légendes du {config['chateau_name']}")
    c.setAuthor(config.get("village", "Daystone Press"))
    c.setSubject(f"Mini-livret des légendes locales du {config['chateau_name']}")

    # Page de titre
    c.setFillColorRGB(palette["main"][0] / 255,
                        palette["main"][1] / 255,
                        palette["main"][2] / 255)
    c.setFont(F_TITLE, 24)
    c.drawCentredString(TRIM_W / 2, TRIM_H - 100, "LÉGENDES")
    c.setFont(F_TITLE, 18)
    c.drawCentredString(TRIM_W / 2, TRIM_H - 130, "DU")
    c.setFont(F_TITLE, 22)
    chateau_name = config["chateau_name"].upper()
    c.drawCentredString(TRIM_W / 2, TRIM_H - 165, chateau_name)
    # Ornement
    c.setStrokeColorRGB(palette["accent"][0] / 255,
                          palette["accent"][1] / 255,
                          palette["accent"][2] / 255)
    c.setLineWidth(1.2)
    c.line(TRIM_W / 2 - 50, TRIM_H - 200, TRIM_W / 2 + 50, TRIM_H - 200)
    # Sous-titre
    c.setFillColorRGB(0.3, 0.25, 0.2)
    c.setFont(F_IT, 11)
    c.drawCentredString(TRIM_W / 2, TRIM_H - 230, f"{config.get('village', '')}")
    annee = config.get("annee_fondation", "")
    if annee:
        c.drawCentredString(TRIM_W / 2, TRIM_H - 250, f"Fondé en {annee}")
    # Imprint bas
    c.setFont(F_BODY, 8)
    c.drawCentredString(TRIM_W / 2, 50, "DAYSTONE PRESS")
    c.showPage()

    # Une page par légende
    legendes = config.get("legendes_locales", [])
    for i, leg in enumerate(legendes, 1):
        # Numéro de chapitre
        c.setFillColorRGB(palette["accent"][0] / 255,
                            palette["accent"][1] / 255,
                            palette["accent"][2] / 255)
        c.setFont(F_TITLE, 14)
        c.drawString(MARGIN_INNER, TRIM_H - MARGIN_TOP,
                      f"LÉGENDE {i:02d}")
        # Titre légende
        c.setFillColorRGB(palette["main"][0] / 255,
                            palette["main"][1] / 255,
                            palette["main"][2] / 255)
        c.setFont(F_TITLE, 16)
        title = leg.get("titre", "")
        c.drawString(MARGIN_INNER, TRIM_H - MARGIN_TOP - 25, title[:30])
        # Ornement
        c.setStrokeColorRGB(palette["accent"][0] / 255,
                              palette["accent"][1] / 255,
                              palette["accent"][2] / 255)
        c.setLineWidth(0.8)
        c.line(MARGIN_INNER, TRIM_H - MARGIN_TOP - 40,
                MARGIN_INNER + 60, TRIM_H - MARGIN_TOP - 40)

        # Année si dispo
        annee = leg.get("annee_premiere_apparition") or leg.get("annee")
        if annee:
            c.setFillColorRGB(0.5, 0.4, 0.3)
            c.setFont(F_IT, 9)
            c.drawString(MARGIN_INNER, TRIM_H - MARGIN_TOP - 60,
                          f"Première mention : {annee}")

        # Synopsis (wrap)
        c.setFillColorRGB(0.15, 0.12, 0.1)
        c.setFont(F_BODY, 10)
        synopsis = leg.get("synopsis_court", "")
        y = TRIM_H - MARGIN_TOP - 100
        max_w = TRIM_W - MARGIN_INNER - MARGIN_OUTER
        words = synopsis.split()
        line = ""
        for w_ in words:
            test = (line + " " + w_).strip()
            if c.stringWidth(test, F_BODY, 10) <= max_w:
                line = test
            else:
                c.drawString(MARGIN_INNER, y, line)
                y -= 13
                line = w_
        if line:
            c.drawString(MARGIN_INNER, y, line)
            y -= 13

        # Pied de page
        c.setFillColorRGB(0.4, 0.3, 0.2)
        c.setFont(F_IT, 8)
        c.drawCentredString(TRIM_W / 2, 30, f"— {i} —")
        c.showPage()

    # Page finale credits
    c.setFillColorRGB(palette["main"][0] / 255,
                        palette["main"][1] / 255,
                        palette["main"][2] / 255)
    c.setFont(F_TITLE, 14)
    c.drawCentredString(TRIM_W / 2, TRIM_H - 100, "TABLE DES LÉGENDES")
    c.setFillColorRGB(0.15, 0.1, 0.05)
    c.setFont(F_BODY, 10)
    y = TRIM_H - 140
    for i, leg in enumerate(legendes, 1):
        c.drawString(MARGIN_INNER, y, f"{i:02d}. {leg.get('titre', '')[:32]}")
        y -= 16
    c.showPage()

    c.save()

    return {
        "ok": True,
        "product_id": "mini_livre_legendes",
        "title": f"Légendes du {config['chateau_name']} — Mini Livret",
        "format": "10×15cm paperback KDP",
        "price_eur": 9.99,
        "files": ["mini_livre_legendes.pdf"],
    }


# ============================================================
# PRODUIT 5 : EMPREINTE PLAQUE (15×15 cm design)
# ============================================================

def produce_empreinte_plaque(config: dict, out_dir: Path) -> dict:
    print("  → 5. Empreinte Plaque (15×15cm design)")
    # 15×15cm = 5.9×5.9" @ 300 DPI = 1770×1770
    size = 1800
    palette = palette_from_armoiries(config.get("armoiries_palette", ["azur", "or"]))

    # Fond bois ou résine
    bg_prompt = (
        f"seamless aged wood texture, natural oak grain with warm honey tones, "
        f"decorative plaque background, no text no letters no symbols, "
        f"square format"
    )
    bg_path = out_dir / "raw_wood.png"
    seed = hash(config["chateau_id"] + "_plaque") % 99999
    if not http_get(pollinations_url(bg_prompt, seed, 1024, 1024), bg_path):
        print("     ✗ wood texture generation failed")
        return {"ok": False}

    bg = Image.open(bg_path).convert("RGB").resize((size, size), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=1.5))
    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    # Double cadre brûlé/gravé
    for margin, w_line in [(80, 8), (110, 3)]:
        draw.rectangle([margin, margin, size - margin, size - margin],
                        outline=(60, 40, 25), width=w_line)

    # Nom du château au centre haut
    f_main = get_font("display", 150)
    name = config["chateau_name"].upper()
    draw_text_centered(draw, name, (size // 2, size // 2 - 200),
                        f_main, (40, 25, 15), letter_spacing=6)

    # Petit ornement
    draw.line([(size // 2 - 150, size // 2 - 90),
                (size // 2 + 150, size // 2 - 90)],
               fill=(40, 25, 15), width=4)

    # Coords GPS
    coords = config.get("gps_coords", "")
    f_coord = get_font("title", 70)
    if coords:
        draw_text_centered(draw, coords, (size // 2, size // 2 + 60),
                            f_coord, (60, 40, 20), letter_spacing=8)

    # Altitude
    alt = config.get("altitude_m", "")
    f_alt = get_font("body", 55)
    if alt:
        draw_text_centered(draw, f"ALTITUDE {alt} m",
                            (size // 2, size // 2 + 160),
                            f_alt, (80, 55, 30), letter_spacing=10)

    # Année fondation en bas
    annee = config.get("annee_fondation", "")
    if annee:
        f_year = get_font("body", 50)
        draw_text_centered(draw, f"EST. {annee}", (size // 2, size - 200),
                            f_year, (80, 55, 30), letter_spacing=12)

    out_path = out_dir / "empreinte_plaque_15x15.png"
    canvas.save(out_path, "PNG", optimize=True)
    if bg_path.exists():
        bg_path.unlink()

    return {
        "ok": True,
        "product_id": "empreinte_plaque",
        "title": f"Plaque {config['chateau_name']} — Design Gravure Laser",
        "format": "15×15cm laser engraving ready",
        "price_eur": 29.99,
        "files": [out_path.name],
        "manufacturing": "Prodigi laser engraving on wood/acrylic/aluminum",
    }


# ============================================================
# MAIN
# ============================================================

PRODUCERS = {
    "codex_carnet": produce_codex_carnet,
    "plans_anciens": produce_plans_anciens,
    "mug_medieval": produce_mug_medieval,
    "mini_livre_legendes": produce_mini_livre_legendes,
    "empreinte_plaque": produce_empreinte_plaque,
}


def produce_chateau(chateau_key: str, produits: list[str]) -> int:
    config_path = DATA_DIR / f"{chateau_key}.json"
    if not config_path.exists():
        print(f"✗ Config absente : {config_path}")
        return 1
    config = json.loads(config_path.read_text())

    out_dir = OUTPUT_DIR / chateau_key
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== CHÂTEAU LOCAL — {config['chateau_name']} ===")

    results = []
    for prod_key in produits:
        if prod_key not in PRODUCERS:
            print(f"  ⊝ {prod_key} : inconnu")
            continue
        try:
            result = PRODUCERS[prod_key](config, out_dir)
            results.append(result)
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ {prod_key} : {exc}")
            results.append({"ok": False, "product_id": prod_key, "error": str(exc)})
        time.sleep(2)

    # Manifest pour gérant
    manifest = {
        "chateau_id": chateau_key,
        "chateau_name": config["chateau_name"],
        "produced_at": datetime.utcnow().isoformat() + "Z",
        "products": results,
        "boutique_partenaire": config.get("boutique_partenaire", {}),
        "next_steps_hugo": [
            "1. Vérifier visuellement chaque produit dans products/chateau_local/" + chateau_key,
            "2. Préparer un dossier PDF de présentation pour M. le gérant",
            "3. Proposer rendez-vous avec mockups imprimés (1 carnet, 1 poster A4)",
            "4. Si accord : configurer Printify/Prodigi avec ces fichiers",
            "5. Pitch : 0€ stock pour le château, marge sur chaque vente",
        ],
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False))

    # Pitch deck text
    pitch = (
        f"=== PITCH POUR M. {config.get('boutique_partenaire', {}).get('nom_gerant', '[Gérant]')} ===\n\n"
        f"Bonjour,\n\n"
        f"Je m'appelle Hugo et je vis à {config.get('village', '[Village]')}. "
        f"Je vous propose un partenariat 100% sans risque pour la boutique du "
        f"{config['chateau_name']}.\n\n"
        f"LE PRINCIPE :\n"
        f"Je crée à mes frais une gamme de produits exclusifs au château "
        f"(carnet, poster, mug, livret, plaque). Chaque vente déclenche "
        f"une fabrication unitaire à la demande chez un imprimeur professionnel "
        f"(Printify/Prodigi). Vous payez seulement quand un client achète.\n\n"
        f"VOTRE BÉNÉFICE :\n"
        f"- Zéro stock, zéro avance de trésorerie\n"
        f"- 30 % de marge sur chaque vente\n"
        f"- Gamme exclusive (les autres châteaux ne l'auront pas)\n"
        f"- Délai d'expédition 5-7 jours pour le client final\n\n"
        f"MA PROPOSITION :\n"
        f"5 produits prêts à présenter dans votre boutique (mockups joints).\n"
        f"Si rien ne se vend en 3 mois, on arrête sans frais.\n\n"
        f"PRODUITS PROPOSÉS :\n"
    )
    for r in results:
        if r.get("ok"):
            pitch += f"- {r.get('title', '')} ({r.get('format', '')}) — {r.get('price_eur', 0):.2f}€\n"
    pitch += (
        f"\nQuand pouvons-nous nous rencontrer pour vous montrer les mockups ?\n\n"
        f"Cordialement,\nHugo\n"
    )
    (out_dir / "PITCH_GERANT.txt").write_text(pitch, encoding="utf-8")

    print(f"\n  Dossier : {out_dir}")
    success = sum(1 for r in results if r.get("ok"))
    print(f"  {success}/{len(results)} produits générés OK")
    return 0


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    chateau_key = os.environ.get("CHATEAU", "example_chateau").strip()
    produits_env = os.environ.get("PRODUITS", "all").strip().lower()
    if produits_env == "all":
        produits = list(PRODUCERS.keys())
    else:
        produits = [p.strip() for p in produits_env.split(",") if p.strip()]
    return produce_chateau(chateau_key, produits)


if __name__ == "__main__":
    sys.exit(main())
