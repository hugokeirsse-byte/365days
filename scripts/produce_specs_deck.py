"""
Pipeline SPECS — production d'un deck complet pour The Game Crafter.

Consomme un fichier data/specs_decks/<edition>.json (Hugo's brief) et
génère :
- 1 PNG par carte Trait (description)
- 1 PNG par carte Target (avec multiplier badge)
- 1 PNG par carte Blank (Trait et Target)
- 1 verso de carte commun (motif empreinte SPECS)
- 1 box cover (tuck box TGC)
- 1 manifest CSV pour upload TGC bulk
- 1 PDF règlement A4 imprimable

Identité visuelle ORIGINALE 365days/SPECS :
- Noir mat (#0A0A0F)
- Cyan néon (#00E5FF)
- Empreinte digitale procédurale
- Typo Bebas Neue / Anton / Inter

Variables d'env :
  EDITION=roast_and_boast_us_base    nom du fichier JSON sans .json
  MAX_CARDS=0                         0 = toutes, sinon limite test
  RENDER_FULL_BOX=1                   1 = inclut box cover + règles PDF
"""

from __future__ import annotations

import csv
import json
import math
import os
import random
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.specs_visual_identity import (  # noqa: E402
    SpecsPalette,
    CardDimensions,
    get_font,
    generate_fingerprint,
    apply_glitch_effect,
    add_scan_lines,
    add_vignette,
    draw_text_centered,
    wrap_text,
    find_optimal_size,
    draw_corner_brackets,
    draw_specs_logo,
    draw_difficulty_badge,
)


ROOT = Path(__file__).resolve().parent.parent
DECKS_DIR = ROOT / "data" / "specs_decks"
OUTPUT_BASE = ROOT / "products" / "specs"


# ============================================================
# RENDERING HELPERS
# ============================================================

def make_base_canvas(width: int, height: int,
                      bg_color: tuple = SpecsPalette.BLACK_MAT) -> Image.Image:
    """Crée un canvas avec gradient subtil noir vers noir-bleu."""
    canvas = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(canvas)
    # Léger gradient radial du centre (un poil plus clair) vers les bords
    cx, cy = width / 2, height / 2
    max_dist = math.sqrt(cx ** 2 + cy ** 2)
    for r_ratio in [0.95, 0.75, 0.50, 0.30, 0.15]:
        r = int(max_dist * r_ratio)
        alpha = int(8 * (1 - r_ratio))
        # On dessine en mode RGBA pour pouvoir composer
        color = (15 + alpha, 18 + alpha, 24 + alpha)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    return canvas


def add_background_fingerprint(canvas: Image.Image,
                                 color: tuple = SpecsPalette.CYAN_NEON,
                                 alpha: int = 35,
                                 seed: int = 42) -> Image.Image:
    """Ajoute une empreinte digitale subtile en fond."""
    w, h = canvas.size
    size = max(w, h)
    fp = generate_fingerprint(size, color=color, background=None,
                               rings=22, density=0.75, seed=seed)
    # Réduit l'opacité globale
    if fp.mode != "RGBA":
        fp = fp.convert("RGBA")
    r, g, b, a = fp.split()
    a = a.point(lambda px: int(px * alpha / 255))
    fp = Image.merge("RGBA", (r, g, b, a))
    # Centre l'empreinte
    offset = ((w - size) // 2, (h - size) // 2)
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(fp, offset, fp)
    return canvas_rgba.convert("RGB")


# ============================================================
# CARD LAYOUTS — TRAIT, TARGET, BLANK, BACK
# ============================================================

def render_trait_card(trait: dict, edition: dict) -> Image.Image:
    """Render une carte Description/Trait — fond cream chaud, texte noir."""
    w, h = CardDimensions.WIDTH, CardDimensions.HEIGHT
    # Fond cream chaud direct (pas de gradient)
    canvas = Image.new("RGB", (w, h), SpecsPalette.OFFWHITE)

    # Empreinte cyan deep subtile en fond
    canvas = add_background_fingerprint(
        canvas, color=SpecsPalette.CYAN_DEEP, alpha=45,
        seed=hash(trait["id"]) % 99999,
    )

    draw = ImageDraw.Draw(canvas)

    # Header : barre cyan en haut sur toute la largeur
    draw.rectangle([0, 0, w, 14], fill=SpecsPalette.CYAN_NEON)

    # Logo SPECS petit en haut
    draw_specs_logo(draw, center=(w // 2, 80), size=56,
                     color=SpecsPalette.BLACK_MAT)

    # Catégorie cyan deep avec mini séparateurs
    category = trait.get("category", "TRAIT").upper()
    cat_font = get_font("body_bold", 28)
    cat_bbox = draw.textbbox((0, 0), category, font=cat_font)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.text(((w - cat_w) // 2, 130), category,
               fill=SpecsPalette.CYAN_DEEP, font=cat_font)
    # Mini-traits horizontaux de chaque côté de la catégorie
    sep_y = 145
    draw.line([(60, sep_y), ((w - cat_w) // 2 - 20, sep_y)],
               fill=SpecsPalette.CYAN_NEON, width=2)
    draw.line([((w + cat_w) // 2 + 20, sep_y), (w - 60, sep_y)],
               fill=SpecsPalette.CYAN_NEON, width=2)

    # Corner brackets cyan
    margin = 55
    draw_corner_brackets(
        draw, (margin, 200, w - margin, h - 200),
        SpecsPalette.CYAN_NEON, length=42, thickness=4,
    )

    # TEXTE PRINCIPAL — large, lisible, parfaitement centré
    text = trait["text"]
    text_box_w = w - 2 * 95
    text_box_h = h - 480

    size, lines = find_optimal_size(
        draw, text, "body_bold", text_box_w, text_box_h,
        max_lines=9, start_size=88, min_size=46,
        line_height_ratio=1.20,
    )
    font = get_font("body_bold", size)
    line_h = int(size * 1.20)
    total_h = line_h * len(lines)
    y = (h - total_h) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        draw.text(((w - line_w) // 2, y), line,
                  fill=SpecsPalette.BLACK_DEEP, font=font)
        y += line_h

    # Footer : edition + ID + barre basse cyan
    foot_font = get_font("body", 20)
    edition_label = "SPECS · ROAST & BOAST"
    draw_text_centered(draw, edition_label, (w // 2, h - 110),
                        foot_font, SpecsPalette.CYAN_DEEP,
                        letter_spacing=3)
    id_font = get_font("body", 16)
    draw_text_centered(draw, trait["id"], (w // 2, h - 75),
                        id_font, SpecsPalette.BLACK_MAT,
                        letter_spacing=2)
    # Barre cyan en bas
    draw.rectangle([0, h - 14, w, h], fill=SpecsPalette.CYAN_NEON)

    return canvas


def render_target_card(target: dict, edition: dict) -> Image.Image:
    """Render une carte Target — fond noir mat, empreinte cyan néon, multiplier badge."""
    w, h = CardDimensions.WIDTH, CardDimensions.HEIGHT
    canvas = Image.new("RGB", (w, h), SpecsPalette.BLACK_MAT)
    canvas = add_background_fingerprint(
        canvas, color=SpecsPalette.CYAN_NEON, alpha=85,
        seed=hash(target["id"]) % 99999,
    )

    draw = ImageDraw.Draw(canvas)

    # Barre cyan en haut sur toute la largeur
    draw.rectangle([0, 0, w, 14], fill=SpecsPalette.CYAN_NEON)

    # Header : label TARGET en cyan néon (énorme)
    label_font = get_font("display", 92)
    draw_text_centered(draw, "TARGET", (w // 2, 105),
                        label_font, SpecsPalette.CYAN_NEON,
                        letter_spacing=10)

    # Sous-séparateur
    draw.rectangle([w // 2 - 80, 172, w // 2 + 80, 176],
                    fill=SpecsPalette.CYAN_BRIGHT)

    # Type indicator (Table_Combat, Judge, Relatives, Absent)
    type_label = target.get("type", "").replace("_", " ").upper()
    type_font = get_font("body_bold", 26)
    draw_text_centered(draw, type_label, (w // 2, 215),
                        type_font, SpecsPalette.CYAN_GLOW,
                        letter_spacing=4)

    # Corner brackets cyan
    margin = 50
    draw_corner_brackets(
        draw, (margin, 260, w - margin, h - 290),
        SpecsPalette.CYAN_NEON, length=48, thickness=4,
    )

    # TEXTE PRINCIPAL — gros, blanc cassé, parfaitement centré
    text = target["text"]
    text_box_w = w - 2 * 85
    text_box_h = h - 620

    size, lines = find_optimal_size(
        draw, text, "body_bold", text_box_w, text_box_h,
        max_lines=6, start_size=84, min_size=42,
        line_height_ratio=1.22,
    )
    font = get_font("body_bold", size)
    line_h = int(size * 1.22)
    total_h = line_h * len(lines)
    y = (h - 200) // 2 - total_h // 2 + 60
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        draw.text(((w - line_w) // 2, y), line,
                  fill=SpecsPalette.OFFWHITE, font=font)
        y += line_h

    # MULTIPLIER BADGE en bas-centre
    mult = target.get("multiplier", 1)
    badge_cy = h - 180
    draw_difficulty_badge(draw, (w // 2, badge_cy), float(mult),
                           SpecsPalette)

    # Footer : id discret + barre cyan
    id_font = get_font("body", 16)
    draw_text_centered(draw, target["id"], (w // 2, h - 65),
                        id_font, SpecsPalette.CYAN_DEEP,
                        letter_spacing=2)
    draw.rectangle([0, h - 14, w, h], fill=SpecsPalette.CYAN_NEON)

    return canvas


def render_blank_card(blank_type: str, idx: int, edition: dict) -> Image.Image:
    """Render une carte Blank (dry erase placeholder)."""
    w, h = CardDimensions.WIDTH, CardDimensions.HEIGHT
    if blank_type == "trait":
        canvas = make_base_canvas(w, h, SpecsPalette.OFFWHITE)
        canvas = add_background_fingerprint(
            canvas, color=SpecsPalette.CYAN_NEON, alpha=14,
            seed=idx * 9001,
        )
        overlay = Image.new("RGBA", (w, h),
                             SpecsPalette.OFFWHITE + (200,))
        canvas = Image.alpha_composite(
            canvas.convert("RGBA"), overlay).convert("RGB")
        text_color = SpecsPalette.BLACK_MAT
        accent_color = SpecsPalette.CYAN_DEEP
        label = "CUSTOM TRAIT"
    else:  # target
        canvas = make_base_canvas(w, h, SpecsPalette.BLACK_MAT)
        canvas = add_background_fingerprint(
            canvas, color=SpecsPalette.CYAN_NEON, alpha=50,
            seed=idx * 9002,
        )
        text_color = SpecsPalette.OFFWHITE
        accent_color = SpecsPalette.CYAN_NEON
        label = "CUSTOM TARGET"

    draw = ImageDraw.Draw(canvas)

    # Logo SPECS
    draw_specs_logo(draw, center=(w // 2, 100), size=64, color=text_color)

    # Label TYPE
    cat_font = get_font("body_bold", 28)
    draw_text_centered(draw, label, (w // 2, 180),
                        cat_font, accent_color, letter_spacing=4)

    # Cadre de zone d'écriture (lignes pointillées style "write here")
    margin = 90
    box = (margin, 280, w - margin, h - 250)
    # Cadre simple
    for offset in (0, 4, 8):
        draw.rectangle(
            (box[0] - offset, box[1] - offset,
             box[2] + offset, box[3] + offset),
            outline=accent_color, width=1,
        )
    # Lignes horizontales pour guider l'écriture
    n_lines = 6
    line_y_start = box[1] + 40
    line_y_end = box[3] - 40
    line_spacing = (line_y_end - line_y_start) / max(n_lines - 1, 1)
    for i in range(n_lines):
        ly = int(line_y_start + i * line_spacing)
        # Trait pointillé
        x = box[0] + 30
        while x < box[2] - 30:
            draw.line([(x, ly), (x + 12, ly)],
                       fill=accent_color, width=2)
            x += 22

    # Instruction
    instr_font = get_font("body", 20)
    draw_text_centered(
        draw, "WRITE WITH DRY-ERASE MARKER",
        (w // 2, box[1] - 30),
        instr_font, accent_color, letter_spacing=3,
    )

    # Footer
    foot_font = get_font("body", 18)
    edition_label = edition.get("edition", "SPECS").upper()[:32]
    draw_text_centered(draw, edition_label, (w // 2, h - 110),
                        foot_font, text_color, letter_spacing=2)
    id_font = get_font("body", 16)
    draw_text_centered(draw,
                        f"BLANK_{blank_type.upper()}_{idx:03d}",
                        (w // 2, h - 80),
                        id_font, accent_color)
    return canvas


def render_card_back() -> Image.Image:
    """Render le verso commun de toutes les cartes SPECS."""
    w, h = CardDimensions.WIDTH, CardDimensions.HEIGHT
    canvas = make_base_canvas(w, h, SpecsPalette.BLACK_DEEP)

    # Empreinte centrale grande, cyan néon, plus intense
    size = int(min(w, h) * 0.78)
    fp = generate_fingerprint(
        size, color=SpecsPalette.CYAN_NEON,
        background=None, rings=24, density=0.9, seed=4242,
    )
    if fp.mode != "RGBA":
        fp = fp.convert("RGBA")
    offset = ((w - size) // 2, (h - size) // 2 - 30)
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(fp, offset, fp)
    canvas = canvas_rgba.convert("RGB")

    # Logo SPECS en bas
    draw = ImageDraw.Draw(canvas)
    draw_specs_logo(draw, center=(w // 2, h - 130),
                     size=110, color=SpecsPalette.OFFWHITE)

    # Glitch léger pour donner du style
    canvas = apply_glitch_effect(canvas, intensity=0.25, seed=99)
    canvas = add_vignette(canvas, strength=0.5)
    return canvas


# ============================================================
# BOX COVER
# ============================================================

def render_box_cover(edition: dict) -> Image.Image:
    """Render la cover de la tuck box TGC."""
    w, h = CardDimensions.BOX_COVER_W, CardDimensions.BOX_COVER_H
    canvas = make_base_canvas(w, h, SpecsPalette.BLACK_DEEP)

    # Empreinte ENORME centrale
    size = int(min(w, h) * 0.82)
    fp = generate_fingerprint(
        size, color=SpecsPalette.CYAN_NEON,
        background=None, rings=26, density=0.92, seed=7777,
    )
    if fp.mode != "RGBA":
        fp = fp.convert("RGBA")
    offset = ((w - size) // 2, (h - size) // 2 - 60)
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(fp, offset, fp)
    canvas = canvas_rgba.convert("RGB")

    draw = ImageDraw.Draw(canvas)

    # Titre SPECS énorme par-dessus
    title_font = get_font("display", 220)
    draw_text_centered(draw, "SPECS", (w // 2, h // 2 - 60),
                        title_font, SpecsPalette.OFFWHITE,
                        letter_spacing=14)

    # Sous-titre
    subtitle_text = edition.get("edition", "ROAST & BOAST").upper()
    # Garde seulement le sous-titre principal (sans (US Base Deck))
    if "(" in subtitle_text:
        subtitle_text = subtitle_text.split("(")[0].strip()
    subtitle_font = get_font("title", 64)
    draw_text_centered(draw, subtitle_text, (w // 2, h - 220),
                        subtitle_font, SpecsPalette.CYAN_NEON,
                        letter_spacing=6)

    # Age rating
    rating = edition.get("age_rating", "18+")
    rating_font = get_font("body_bold", 32)
    draw_text_centered(draw, f"ADULT {rating}", (w // 2, h - 130),
                        rating_font, SpecsPalette.OFFWHITE_DIM,
                        letter_spacing=4)

    # Glitch + vignette
    canvas = apply_glitch_effect(canvas, intensity=0.4, seed=1234)
    canvas = add_scan_lines(canvas, opacity=25, spacing=3)
    canvas = add_vignette(canvas, strength=0.65)
    return canvas


# ============================================================
# OUTPUT
# ============================================================

def save_card(card: Image.Image, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    card.save(dest, "PNG", optimize=True)


def produce_deck(edition_key: str, max_cards: int = 0,
                  render_full_box: bool = True) -> dict:
    json_path = DECKS_DIR / f"{edition_key}.json"
    if not json_path.exists():
        print(f"✗ Deck inconnu : {json_path}")
        return {"ok": False}
    data = json.loads(json_path.read_text())

    out_dir = OUTPUT_BASE / edition_key
    cards_dir = out_dir / "cards"
    targets_dir = cards_dir / "targets"
    traits_dir = cards_dir / "traits"
    blanks_dir = cards_dir / "blanks"
    box_dir = out_dir / "box"
    for d in (targets_dir, traits_dir, blanks_dir, box_dir):
        d.mkdir(parents=True, exist_ok=True)

    print(f"=== SPECS — {data.get('edition', '?')} ===")

    manifest = []

    # Traits
    traits = data["cards"]["descriptions"]
    if max_cards > 0:
        traits = traits[:max_cards]
    print(f"\n  → {len(traits)} TRAITS")
    for trait in traits:
        try:
            card = render_trait_card(trait, data)
            dest = traits_dir / f"{trait['id']}.png"
            save_card(card, dest)
            manifest.append({
                "card_id": trait["id"],
                "card_type": "trait",
                "category": trait.get("category", ""),
                "text": trait["text"],
                "multiplier": "",
                "image_file": str(dest.relative_to(OUTPUT_BASE.parent)),
            })
            print(f"    ✓ {trait['id']}")
        except Exception as exc:  # noqa: BLE001
            print(f"    ✗ {trait['id']} : {exc}")

    # Targets
    targets = data["cards"]["targets"]
    if max_cards > 0:
        targets = targets[:max_cards]
    print(f"\n  → {len(targets)} TARGETS")
    for target in targets:
        try:
            card = render_target_card(target, data)
            dest = targets_dir / f"{target['id']}.png"
            save_card(card, dest)
            manifest.append({
                "card_id": target["id"],
                "card_type": "target",
                "category": target.get("type", ""),
                "text": target["text"],
                "multiplier": str(target.get("multiplier", 1)),
                "image_file": str(dest.relative_to(OUTPUT_BASE.parent)),
            })
            print(f"    ✓ {target['id']}")
        except Exception as exc:  # noqa: BLE001
            print(f"    ✗ {target['id']} : {exc}")

    # Blanks
    blanks_trait_count = data["cards"].get("blanks_traits_count", 10)
    blanks_target_count = data["cards"].get("blanks_targets_count", 10)
    if max_cards > 0:
        blanks_trait_count = min(blanks_trait_count, max_cards)
        blanks_target_count = min(blanks_target_count, max_cards)
    print(f"\n  → {blanks_trait_count} BLANK TRAITS + {blanks_target_count} BLANK TARGETS")
    for i in range(1, blanks_trait_count + 1):
        card = render_blank_card("trait", i, data)
        dest = blanks_dir / f"BLANK_TRAIT_{i:03d}.png"
        save_card(card, dest)
        manifest.append({
            "card_id": f"BLANK_TRAIT_{i:03d}",
            "card_type": "blank_trait",
            "category": "",
            "text": "",
            "multiplier": "",
            "image_file": str(dest.relative_to(OUTPUT_BASE.parent)),
        })
    for i in range(1, blanks_target_count + 1):
        card = render_blank_card("target", i, data)
        dest = blanks_dir / f"BLANK_TARGET_{i:03d}.png"
        save_card(card, dest)
        manifest.append({
            "card_id": f"BLANK_TARGET_{i:03d}",
            "card_type": "blank_target",
            "category": "",
            "text": "",
            "multiplier": "",
            "image_file": str(dest.relative_to(OUTPUT_BASE.parent)),
        })

    # Card back commun
    print(f"\n  → CARD BACK")
    back = render_card_back()
    save_card(back, cards_dir / "card_back.png")

    # Box cover
    if render_full_box:
        print(f"  → BOX COVER")
        box = render_box_cover(data)
        save_card(box, box_dir / "box_cover.png")

    # Manifest CSV
    csv_path = out_dir / "tgc_upload.csv"
    if manifest:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=["card_id", "card_type", "category",
                            "text", "multiplier", "image_file"],
            )
            w.writeheader()
            w.writerows(manifest)
        print(f"\n  CSV : {csv_path}")

    # Metadata
    metadata = {
        "deck_id": edition_key,
        "game": data.get("game", "SPECS"),
        "edition": data.get("edition", ""),
        "version": data.get("version", ""),
        "language": data.get("language", "en"),
        "mature": data.get("mature", True),
        "age_rating": data.get("age_rating", "18+"),
        "total_cards": len(manifest),
        "traits": len(traits),
        "targets": len(targets),
        "blanks": blanks_trait_count + blanks_target_count,
        "card_format": f"Poker TGC bleed {CardDimensions.WIDTH}x{CardDimensions.HEIGHT}",
        "platform_target": "The Game Crafter + BoardGamesMaker",
        "production_method": "Pillow pure (Pollinations-free, gibberish-proof, deterministic identity)",
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    (out_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False))

    print(f"\n  → Total cards : {len(manifest)}")
    print(f"  → Output : {out_dir}")
    return {"ok": True, "count": len(manifest)}


def main() -> int:
    edition = os.environ.get("EDITION", "roast_and_boast_us_base").strip()
    max_cards = int(os.environ.get("MAX_CARDS") or "0")
    render_full_box = os.environ.get("RENDER_FULL_BOX", "1") != "0"

    result = produce_deck(edition, max_cards=max_cards,
                           render_full_box=render_full_box)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
