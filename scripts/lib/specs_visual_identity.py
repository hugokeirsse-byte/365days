"""
SPECS — module d'identité visuelle.

Palette, fonts, et helpers Pillow pour produire toutes les déclinaisons
SPECS (Roast & Boast et futures éditions).

Identité visuelle ORIGINALE 365days/SPECS — palette noir mat + cyan
néon + blanc cassé, motif empreinte digitale procédural avec glitch
RGB, typo condensed bold.

Reproductible 100% en Pillow pur sans IA générative. Qualité garantie.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


# ============================================================
# PATHS
# ============================================================

LIB_DIR = Path(__file__).resolve().parent
FONTS_DIR = LIB_DIR / "assets" / "fonts"

# Display/Title fonts depuis Google Fonts (téléchargées en local)
FONT_DISPLAY = FONTS_DIR / "BebasNeue-Regular.ttf"
FONT_TITLE = FONTS_DIR / "Anton-Regular.ttf"

# Body fonts depuis système (DejaVu installé partout via fonts-dejavu)
_SYSTEM_FONTS = [
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
]
_SYSTEM_FONTS_BOLD = [
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
]
FONT_BODY = next((f for f in _SYSTEM_FONTS if f.exists()), FONT_TITLE)
FONT_BODY_BOLD = next((f for f in _SYSTEM_FONTS_BOLD if f.exists()), FONT_TITLE)


# ============================================================
# PALETTE SPECS
# ============================================================

class SpecsPalette:
    """Palette officielle de l'identité SPECS."""
    # Fonds
    BLACK_MAT = (10, 10, 15)
    BLACK_DEEP = (4, 4, 8)
    OFFWHITE = (240, 244, 248)
    OFFWHITE_DIM = (210, 216, 222)

    # Accent principal cyan néon
    CYAN_NEON = (0, 229, 255)
    CYAN_BRIGHT = (40, 240, 255)
    CYAN_GLOW = (100, 220, 255)
    CYAN_DEEP = (0, 120, 180)
    CYAN_SHADOW = (0, 60, 100)

    # Accent secondaire glitch (décalages RGB)
    GLITCH_RED = (255, 40, 80)
    GLITCH_BLUE = (40, 80, 255)

    # Multiplicateurs (par difficulté Target)
    MULT_EASY = (140, 200, 220)        # cyan dilué
    MULT_MEDIUM = (0, 229, 255)         # cyan principal
    MULT_HARD = (255, 180, 40)          # orange ambre
    MULT_LEGENDARY = (255, 80, 120)     # rose magenta

    # Categorisation des cartes
    TRAIT_ACCENT = (0, 229, 255)
    TARGET_ACCENT = (255, 100, 60)
    BLANK_ACCENT = (240, 244, 248)


# ============================================================
# DIMENSIONS CARTES
# ============================================================

class CardDimensions:
    """Format poker card The Game Crafter avec bleed."""
    # 2.75 × 3.75 inches @ 300 DPI (avec bleed 0.125")
    WIDTH = 825
    HEIGHT = 1125
    # Zone safe (sans coupe) : 0.125" en moins de chaque côté
    SAFE_MARGIN = 75
    # Zone print actuelle : 2.5 × 3.5 inch
    SAFE_WIDTH = WIDTH - 2 * SAFE_MARGIN
    SAFE_HEIGHT = HEIGHT - 2 * SAFE_MARGIN

    # Box cover tuck box TGC = 3 × 4 × 0.85 inch
    BOX_COVER_W = 900   # 3" + bleed
    BOX_COVER_H = 1200  # 4" + bleed


# ============================================================
# FONT LOADERS
# ============================================================

_font_cache: dict = {}


def get_font(role: str, size: int) -> ImageFont.FreeTypeFont:
    """Charge une font avec cache. Roles : display, title, body, body_bold."""
    paths = {
        "display": FONT_DISPLAY,    # Bebas Neue - titres énormes
        "title": FONT_TITLE,         # Anton - sous-titres
        "body": FONT_BODY,           # Inter Regular - texte courant
        "body_bold": FONT_BODY_BOLD, # Inter Bold - emphase
    }
    path = paths.get(role, FONT_BODY)
    key = (str(path), size)
    if key not in _font_cache:
        try:
            _font_cache[key] = ImageFont.truetype(str(path), size)
        except (OSError, IOError):
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


# ============================================================
# FINGERPRINT PATTERN PROCÉDURAL
# ============================================================

def generate_fingerprint(size: int, color: tuple = SpecsPalette.CYAN_NEON,
                          background: tuple | None = None,
                          rings: int = 18,
                          density: float = 0.85,
                          fragmentation: float = 0.35,
                          seed: int = 42) -> Image.Image:
    """Génère un motif empreinte digitale procédural.

    Approche : N ellipses concentriques légèrement déformées, segmentées
    en arcs irréguliers pour donner l'aspect organique d'une empreinte.

    Args:
        size : taille carrée du canvas (px)
        color : couleur RGB des lignes
        background : couleur fond RGB ou None pour transparent
        rings : nombre d'anneaux concentriques
        density : 0-1, fraction de chaque anneau effectivement dessiné
        fragmentation : 0-1, hardness des coupures dans les lignes
        seed : reproductibilité
    """
    rng = random.Random(seed)
    if background:
        img = Image.new("RGB", (size, size), background)
    else:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")

    cx, cy = size / 2, size / 2 + size * 0.05  # centre légèrement bas (style empreinte)
    base_radius_x = size * 0.40
    base_radius_y = size * 0.45

    for r_idx in range(rings):
        ratio = (r_idx + 1) / rings
        rx = base_radius_x * ratio
        ry = base_radius_y * ratio

        # Décalage aléatoire du centre par anneau (style organique)
        offset_x = rng.uniform(-size * 0.015, size * 0.015) * ratio
        offset_y = rng.uniform(-size * 0.025, size * 0.020) * ratio

        # Épaisseur progressive (lignes intérieures plus fines)
        thickness = max(2, int(size * 0.005 * (0.6 + ratio * 0.8)))

        # Segmentation de l'anneau en arcs (ne pas tracer l'anneau complet)
        num_segments = rng.randint(3, 8)
        # Points d'angle des breaks
        angles = sorted([rng.uniform(0, 360) for _ in range(num_segments * 2)])

        for i in range(0, len(angles) - 1, 2):
            start = angles[i]
            end = angles[i + 1]
            # Décide si on dessine ce segment selon density
            if rng.random() > density:
                continue
            # Trace l'arc d'ellipse
            bbox = [
                cx + offset_x - rx,
                cy + offset_y - ry,
                cx + offset_x + rx,
                cy + offset_y + ry,
            ]
            # Couleur avec alpha décroissant vers le centre
            alpha = int(255 * (0.4 + 0.6 * ratio))
            line_color = color + (alpha,)
            draw.arc(bbox, start=start, end=end,
                     fill=line_color, width=thickness)

    # Ajoute quelques deltas/whorls (lignes courtes traversantes)
    for _ in range(rng.randint(4, 8)):
        x1 = cx + rng.uniform(-size * 0.25, size * 0.25)
        y1 = cy + rng.uniform(-size * 0.30, size * 0.30)
        angle = rng.uniform(0, 2 * math.pi)
        length = rng.uniform(size * 0.04, size * 0.10)
        x2 = x1 + length * math.cos(angle)
        y2 = y1 + length * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=color + (220,),
                  width=max(2, int(size * 0.004)))

    return img


def apply_glitch_effect(img: Image.Image, intensity: float = 0.5,
                         seed: int = 7) -> Image.Image:
    """Applique un effet glitch RGB (décalage de canaux par bandes).

    intensity : 0-1, force de l'effet
    """
    rng = random.Random(seed)
    img = img.convert("RGB")
    w, h = img.size
    r, g, b = img.split()

    # Décalage du canal rouge globalement
    r_offset = int(w * 0.008 * intensity)
    r_shifted = Image.new("L", (w, h), 0)
    r_shifted.paste(r, (r_offset, 0))

    # Décalage du canal bleu
    b_offset = -int(w * 0.006 * intensity)
    b_shifted = Image.new("L", (w, h), 0)
    b_shifted.paste(b, (b_offset, 0))

    img = Image.merge("RGB", (r_shifted, g, b_shifted))
    draw = ImageDraw.Draw(img, "RGBA")

    # Bandes horizontales glitch (slices décalées)
    num_bands = int(8 * intensity)
    for _ in range(num_bands):
        band_y = rng.randint(0, h - 1)
        band_h = rng.randint(2, max(3, int(h * 0.015)))
        band_offset = rng.randint(-int(w * 0.03), int(w * 0.03))
        if band_offset == 0:
            continue
        # Extract band
        band = img.crop((0, band_y, w, min(h, band_y + band_h)))
        # Re-paste shifted
        img.paste(band, (band_offset, band_y))

    return img


def add_scan_lines(img: Image.Image, opacity: int = 30,
                    spacing: int = 4) -> Image.Image:
    """Ajoute des scan lines horizontales subtiles (effet écran CRT)."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(0, img.size[1], spacing):
        draw.line([(0, y), (img.size[0], y)],
                  fill=(0, 0, 0, opacity), width=1)
    img_rgba = img.convert("RGBA")
    out = Image.alpha_composite(img_rgba, overlay)
    return out.convert("RGB")


def add_vignette(img: Image.Image, strength: float = 0.6) -> Image.Image:
    """Ajoute un vignettage sombre aux bords."""
    w, h = img.size
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)
    max_dist = math.sqrt((w / 2) ** 2 + (h / 2) ** 2)
    # Trace des cercles dégradés du noir transparent vers noir opaque
    for radius_ratio in [0.95, 0.85, 0.72, 0.58, 0.42]:
        r = int(max_dist * radius_ratio)
        alpha = int(255 * strength * (1 - radius_ratio))
        draw.ellipse(
            [w / 2 - r, h / 2 - r, w / 2 + r, h / 2 + r],
            outline=(0, 0, 0, alpha), width=max(1, int(max_dist * 0.04)),
        )
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=20))
    img_rgba = img.convert("RGBA")
    out = Image.alpha_composite(img_rgba, vignette)
    return out.convert("RGB")


def add_outer_glow(img: Image.Image, color: tuple, radius: int = 20,
                    strength: float = 0.4) -> Image.Image:
    """Ajoute un halo lumineux autour des éléments brillants."""
    glow = img.copy().filter(ImageFilter.GaussianBlur(radius=radius))
    # Blend additif léger
    glow_rgba = glow.convert("RGBA")
    glow_alpha = Image.new("L", img.size,
                            int(255 * strength))
    glow_rgba.putalpha(glow_alpha)
    base = img.convert("RGBA")
    out = Image.alpha_composite(base, glow_rgba)
    return out.convert("RGB")


# ============================================================
# TEXT HELPERS
# ============================================================

def draw_text_centered(draw: ImageDraw.ImageDraw, text: str,
                        center: tuple, font: ImageFont.FreeTypeFont,
                        color: tuple, letter_spacing: int = 0) -> None:
    """Dessine du texte centré sur le point center=(x,y)."""
    if letter_spacing == 0:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text((center[0] - w / 2, center[1] - h / 2),
                  text, fill=color, font=font)
    else:
        # Letter spacing manuel : on dessine caractère par caractère
        total_w = 0
        char_widths = []
        for ch in text:
            bbox = draw.textbbox((0, 0), ch, font=font)
            cw = bbox[2] - bbox[0]
            char_widths.append(cw)
            total_w += cw + letter_spacing
        total_w -= letter_spacing
        bbox = draw.textbbox((0, 0), text, font=font)
        h = bbox[3] - bbox[1]
        x = center[0] - total_w / 2
        y = center[1] - h / 2
        for ch, cw in zip(text, char_widths):
            draw.text((x, y), ch, fill=color, font=font)
            x += cw + letter_spacing


def wrap_text(draw: ImageDraw.ImageDraw, text: str,
               font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def find_optimal_size(draw: ImageDraw.ImageDraw, text: str,
                       font_role: str, max_w: int, max_h: int,
                       max_lines: int, start_size: int = 200,
                       min_size: int = 30,
                       line_height_ratio: float = 1.15) -> tuple[int, list[str]]:
    """Recherche la plus grande taille de police qui rentre dans (max_w, max_h)
    et ne dépasse pas max_lines lignes après wrap.

    Itère du plus grand au plus petit par pas de 4px.
    """
    for size in range(start_size, min_size - 1, -4):
        font = get_font(font_role, size)
        lines = wrap_text(draw, text, font, max_w)
        if len(lines) > max_lines:
            continue
        # Hauteur estimée = nb lignes × line_h
        line_h = int(size * line_height_ratio)
        total_h = line_h * len(lines)
        if total_h <= max_h:
            return size, lines
    # Fallback : on retourne min_size même si ça déborde un peu
    font = get_font(font_role, min_size)
    lines = wrap_text(draw, text, font, max_w)
    return min_size, lines


# ============================================================
# CORNER DECORATIONS / FRAMES
# ============================================================

def draw_corner_brackets(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int],
                          color: tuple, length: int = 30, thickness: int = 3) -> None:
    """Dessine 4 brackets aux coins d'une zone (style tech HUD)."""
    x1, y1, x2, y2 = box
    # Top-left
    draw.line([(x1, y1), (x1 + length, y1)], fill=color, width=thickness)
    draw.line([(x1, y1), (x1, y1 + length)], fill=color, width=thickness)
    # Top-right
    draw.line([(x2, y1), (x2 - length, y1)], fill=color, width=thickness)
    draw.line([(x2, y1), (x2, y1 + length)], fill=color, width=thickness)
    # Bottom-left
    draw.line([(x1, y2), (x1 + length, y2)], fill=color, width=thickness)
    draw.line([(x1, y2), (x1, y2 - length)], fill=color, width=thickness)
    # Bottom-right
    draw.line([(x2, y2), (x2 - length, y2)], fill=color, width=thickness)
    draw.line([(x2, y2), (x2, y2 - length)], fill=color, width=thickness)


def draw_specs_logo(draw: ImageDraw.ImageDraw, center: tuple,
                     size: int, color: tuple = SpecsPalette.OFFWHITE) -> None:
    """Dessine le logo SPECS (typo display)."""
    font = get_font("display", size)
    draw_text_centered(draw, "SPECS", center, font, color,
                        letter_spacing=int(size * 0.06))


def draw_difficulty_badge(draw: ImageDraw.ImageDraw, center: tuple,
                            multiplier: float, palette: SpecsPalette) -> None:
    """Dessine un badge multiplier (x1 / x1.5 / x2 / x3)."""
    color_map = {
        1.0: palette.MULT_EASY,
        1.5: palette.MULT_MEDIUM,
        2.0: palette.MULT_HARD,
        3.0: palette.MULT_LEGENDARY,
    }
    color = color_map.get(multiplier, palette.MULT_MEDIUM)
    radius = 60
    cx, cy = center
    # Cercle de fond avec contour
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                  fill=palette.BLACK_DEEP, outline=color, width=4)
    # Texte multiplicateur
    label = f"×{multiplier:g}"
    font = get_font("title", 56)
    draw_text_centered(draw, label, center, font, color)
