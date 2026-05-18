"""
Module DESIGN COMPOSER — composition propre de designs imprimables.

Sépare strictement génération d'illustration (Pollinations) et
composition typographique (Pillow). Tous les pipelines de production
utilisent cette lib partagée.

Concepts :
- DesignLayout : description du layout final (canvas, illustration box,
  zones de texte, éléments décoratifs)
- TextZone : zone de texte avec auto-sizing pour rentrer dans la box
- DecorativeElement : cœur dessiné, anneau, ornement, etc.

Layouts pré-faits :
- LAYOUT_IHEART_HEART_FRAME : I + cœur + illustration cœur-scène + niche bas
- LAYOUT_VIRAL_TEXT_CENTERED : texte central énorme sur fond ambiant
- LAYOUT_BIBLE_VERSE : référence haut + verset central + ornement bas
- LAYOUT_CULTURAL_WORD : mot grand + traduction petite
- LAYOUT_DICTIONARY_ENTRY : entrée de dictionnaire stylisée
- LAYOUT_QUOTE_MINIMAL : citation minimaliste centrée
- LAYOUT_KDP_COVER : bandeau titre + illustration + auteur

Usage :
    from lib.design_composer import compose_design, LAYOUT_IHEART_HEART_FRAME
    compose_design(
        layout=LAYOUT_IHEART_HEART_FRAME,
        illustration_path=Path("raw.png"),
        text_values={"I": "I", "niche": "Fishing"},
        output_path=Path("final.png"),
        style_overrides={"text_color": (60, 30, 20)},
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

try:
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
except ImportError as exc:
    raise ImportError("Pillow requis : pip install Pillow") from exc


# ============================================================
# TYPES
# ============================================================

@dataclass
class TextZone:
    """Zone de texte avec auto-sizing.

    Attributs :
    - text_key : clé dans le dict text_values (ex: "title", "niche")
    - center_xy_pct : position du centre en % du canvas (0-1, 0-1)
    - max_box_pct : taille max de la zone en % du canvas (w_pct, h_pct)
    - font_role : "title_bold", "title_serif", "body_serif", "body_sans", "mono"
    - color : RGB tuple (sera traduit en RGBA)
    - align : "center", "left", "right"
    - max_lines : nombre max de lignes (auto-wrap)
    - upper : forcer en MAJUSCULES
    - auto_size : True = trouver la plus grosse taille qui rentre
    - fallback_size : taille si auto_size impossible
    """
    text_key: str
    center_xy_pct: tuple[float, float] = (0.5, 0.5)
    max_box_pct: tuple[float, float] = (0.8, 0.15)
    font_role: str = "title_bold"
    color: tuple[int, int, int] = (40, 30, 30)
    align: str = "center"
    max_lines: int = 2
    upper: bool = False
    auto_size: bool = True
    fallback_size: int = 100
    min_size: int = 40
    line_height_ratio: float = 1.15


@dataclass
class DecorativeElement:
    """Élément décoratif Pillow dessiné."""
    type: str  # "heart", "circle", "horizontal_line", "ornament_corner"
    center_xy_pct: tuple[float, float] = (0.5, 0.1)
    size_pct: float = 0.1  # % du canvas (largeur)
    color: tuple[int, int, int] = (200, 30, 50)
    extra: dict = field(default_factory=dict)


@dataclass
class IllustrationPlacement:
    """Où et comment placer l'illustration générée."""
    center_xy_pct: tuple[float, float] = (0.5, 0.5)
    size_pct: tuple[float, float] = (0.7, 0.7)  # w_pct, h_pct max
    fit_mode: str = "cover"  # "cover", "contain", "fill"
    mask_shape: Optional[str] = None  # "heart", "circle" pour clipping


@dataclass
class DesignLayout:
    """Description complète d'un design."""
    name: str
    canvas_size: tuple[int, int] = (3000, 3000)
    background_color: tuple[int, int, int] = (252, 248, 240)
    background_overlay: Optional[tuple[int, int, int, int]] = None  # RGBA semi-transparent
    illustration: Optional[IllustrationPlacement] = None
    text_zones: list[TextZone] = field(default_factory=list)
    decorative_elements: list[DecorativeElement] = field(default_factory=list)
    blur_bg: float = 0.0  # blur radius si > 0 pour fond moins distractif


# ============================================================
# FONT REGISTRY
# ============================================================

FONT_PATHS = {
    "title_bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    ],
    "title_serif": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    ],
    "title_italic": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
    ],
    "body_serif": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ],
    "body_serif_italic": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
    ],
    "body_sans": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "body_sans_bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "mono": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ],
}


def find_font(role: str, size: int) -> ImageFont.ImageFont:
    paths = FONT_PATHS.get(role, FONT_PATHS["title_bold"])
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


# ============================================================
# CORE FUNCTIONS
# ============================================================

def fit_illustration(src: Image.Image, target_w: int, target_h: int,
                     fit_mode: str = "cover") -> Image.Image:
    """Crop/resize illustration au format demandé."""
    if fit_mode == "cover":
        sr = src.width / src.height
        tr = target_w / target_h
        if sr > tr:
            new_w = int(src.height * tr)
            off = (src.width - new_w) // 2
            src = src.crop((off, 0, off + new_w, src.height))
        elif sr < tr:
            new_h = int(src.width / tr)
            off = (src.height - new_h) // 2
            src = src.crop((0, off, src.width, off + new_h))
        return src.resize((target_w, target_h), Image.LANCZOS)
    elif fit_mode == "contain":
        # Fit inside, garde ratio
        ratio = min(target_w / src.width, target_h / src.height)
        new_w = int(src.width * ratio)
        new_h = int(src.height * ratio)
        return src.resize((new_w, new_h), Image.LANCZOS)
    else:  # fill = stretch
        return src.resize((target_w, target_h), Image.LANCZOS)


def apply_mask(img: Image.Image, mask_shape: str) -> Image.Image:
    """Applique un masque cœur ou cercle pour clipping."""
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    mdraw = ImageDraw.Draw(mask)
    if mask_shape == "circle":
        mdraw.ellipse([0, 0, w, h], fill=255)
    elif mask_shape == "heart":
        # Cœur paramétrique mathématique propre (équation classique)
        # x(t) = 16 * sin(t)^3
        # y(t) = 13*cos(t) - 5*cos(2t) - 2*cos(3t) - cos(4t)
        # Normalisé et scalé pour remplir le canvas (w, h)
        import math
        points = []
        steps = 200
        for i in range(steps + 1):
            t = (i / steps) * 2 * math.pi
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t)
                  - 2 * math.cos(3 * t) - math.cos(4 * t))
            points.append((x, y))
        # Bornes de la courbe
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        cw = x_max - x_min
        ch = y_max - y_min
        # Scale pour remplir le canvas avec 2% padding
        scale = min(w / cw, h / ch) * 0.96
        cx, cy = w / 2, h / 2
        # Translate & scale les points
        scaled = []
        for x, y in points:
            sx = cx + (x - (x_min + x_max) / 2) * scale
            sy = cy + (y - (y_min + y_max) / 2) * scale
            scaled.append((sx, sy))
        mdraw.polygon(scaled, fill=255)
    result = Image.new("RGBA", img.size, (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)
    return result


def wrap_text(draw: ImageDraw.ImageDraw, text: str,
              font: ImageFont.ImageFont, max_width: int) -> list[str]:
    """Découpe en lignes qui rentrent dans max_width."""
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


def find_optimal_font_size(draw: ImageDraw.ImageDraw, text: str,
                            role: str, max_w: int, max_h: int,
                            max_lines: int, line_height_ratio: float,
                            start_size: int = 400, min_size: int = 40) -> tuple[int, list[str]]:
    """Recherche binaire descendante de la plus grosse taille qui rentre."""
    for size in range(start_size, min_size - 1, -10):
        font = find_font(role, size)
        lines = wrap_text(draw, text, font, max_w)
        if len(lines) > max_lines:
            continue
        # Hauteur totale
        line_heights = []
        for ln in lines:
            bbox = draw.textbbox((0, 0), ln, font=font)
            line_heights.append(bbox[3] - bbox[1])
        total_h = sum(line_heights) + (len(lines) - 1) * int(size * (line_height_ratio - 1))
        if total_h <= max_h:
            return size, lines
    return min_size, wrap_text(draw, text, find_font(role, min_size), max_w)


def draw_heart_shape(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                      w: int, color: tuple) -> None:
    """Dessine un cœur plein centré sur (cx, cy) de largeur w.

    Utilise l'équation paramétrique classique :
    x(t) = 16 * sin(t)^3
    y(t) = 13*cos(t) - 5*cos(2t) - 2*cos(3t) - cos(4t)
    """
    import math
    points = []
    steps = 120
    for i in range(steps + 1):
        t = (i / steps) * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t)
              - 2 * math.cos(3 * t) - math.cos(4 * t))
        points.append((x, y))
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    cw = x_max - x_min
    ch = y_max - y_min
    h = int(w * ch / cw)  # garde le ratio naturel
    scale = w / cw
    # Translate les points : centrés sur (cx, cy)
    scaled = []
    for x, y in points:
        sx = cx + (x - (x_min + x_max) / 2) * scale
        sy = cy + (y - (y_min + y_max) / 2) * scale
        scaled.append((sx, sy))
    draw.polygon(scaled, fill=color)


def draw_decorative_element(canvas: Image.Image, elem: DecorativeElement) -> None:
    """Dessine un élément décoratif sur le canvas."""
    w, h = canvas.size
    cx = int(w * elem.center_xy_pct[0])
    cy = int(h * elem.center_xy_pct[1])
    size = int(w * elem.size_pct)
    draw = ImageDraw.Draw(canvas)

    if elem.type == "heart":
        draw_heart_shape(draw, cx, cy, size, elem.color)
    elif elem.type == "circle":
        draw.ellipse([cx - size // 2, cy - size // 2,
                      cx + size // 2, cy + size // 2], fill=elem.color)
    elif elem.type == "horizontal_line":
        thickness = elem.extra.get("thickness", 4)
        draw.rectangle([cx - size // 2, cy - thickness // 2,
                        cx + size // 2, cy + thickness // 2],
                       fill=elem.color)
    elif elem.type == "ornament_corner":
        # Petits motifs aux 4 coins
        margin = elem.extra.get("margin", 0.05)
        s = int(w * elem.size_pct)
        positions = [
            (int(w * margin), int(h * margin)),
            (w - int(w * margin), int(h * margin)),
            (int(w * margin), h - int(h * margin)),
            (w - int(w * margin), h - int(h * margin)),
        ]
        for px, py in positions:
            draw.line([(px - s, py), (px + s, py)], fill=elem.color, width=3)
            draw.line([(px, py - s), (px, py + s)], fill=elem.color, width=3)


# ============================================================
# MAIN COMPOSER
# ============================================================

def compose_design(
    layout: DesignLayout,
    illustration_path: Optional[Path],
    text_values: dict[str, str],
    output_path: Path,
    background_override: Optional[Path] = None,
    style_overrides: Optional[dict] = None,
) -> None:
    """Compose un design final selon le layout.

    layout : DesignLayout définissant la structure
    illustration_path : Path vers l'illustration générée (ou None)
    text_values : dict {clé: valeur} pour remplir les zones de texte
    output_path : chemin de sortie PNG
    background_override : si fourni, utilise cette image comme fond entier
    style_overrides : override les couleurs des zones de texte
    """
    style_overrides = style_overrides or {}
    canvas_w, canvas_h = layout.canvas_size

    # 1. Fond
    if background_override and background_override.exists():
        bg = Image.open(background_override).convert("RGB")
        bg = fit_illustration(bg, canvas_w, canvas_h, "cover")
        if layout.blur_bg > 0:
            bg = bg.filter(ImageFilter.GaussianBlur(radius=layout.blur_bg))
        # Désature légèrement pour pas concurrencer le texte
        bg = ImageEnhance.Color(bg).enhance(0.85)
        canvas = bg.convert("RGBA")
    else:
        canvas = Image.new("RGBA", layout.canvas_size,
                            layout.background_color + (255,))

    # 2. Overlay couleur translucide si défini (lisibilité texte)
    if layout.background_overlay:
        overlay = Image.new("RGBA", layout.canvas_size, layout.background_overlay)
        canvas = Image.alpha_composite(canvas, overlay)

    # 3. Illustration (s'il y en a une, et pas en background_override)
    if layout.illustration and illustration_path and illustration_path.exists():
        ill_w = int(canvas_w * layout.illustration.size_pct[0])
        ill_h = int(canvas_h * layout.illustration.size_pct[1])
        cx = int(canvas_w * layout.illustration.center_xy_pct[0])
        cy = int(canvas_h * layout.illustration.center_xy_pct[1])

        ill = Image.open(illustration_path).convert("RGB")
        ill = fit_illustration(ill, ill_w, ill_h, layout.illustration.fit_mode)
        if layout.illustration.mask_shape:
            ill = apply_mask(ill, layout.illustration.mask_shape)
        else:
            ill = ill.convert("RGBA")
        paste_x = cx - ill.width // 2
        paste_y = cy - ill.height // 2
        canvas.paste(ill, (paste_x, paste_y),
                     ill if ill.mode == "RGBA" else None)

    # 4. Éléments décoratifs (avant texte pour ne pas masquer le texte)
    for elem in layout.decorative_elements:
        draw_decorative_element(canvas, elem)

    # 5. Zones de texte
    draw = ImageDraw.Draw(canvas)
    for zone in layout.text_zones:
        raw_text = text_values.get(zone.text_key, "")
        if not raw_text:
            continue
        text = raw_text.upper() if zone.upper else raw_text
        color = style_overrides.get(
            f"{zone.text_key}_color", zone.color) + (255,)

        max_w = int(canvas_w * zone.max_box_pct[0])
        max_h = int(canvas_h * zone.max_box_pct[1])

        if zone.auto_size:
            size, lines = find_optimal_font_size(
                draw, text, zone.font_role, max_w, max_h,
                zone.max_lines, zone.line_height_ratio,
                start_size=int(canvas_h * zone.max_box_pct[1] * 1.2),
                min_size=zone.min_size,
            )
        else:
            size = zone.fallback_size
            font = find_font(zone.font_role, size)
            lines = wrap_text(draw, text, font, max_w)

        font = find_font(zone.font_role, size)

        # Position centrée verticalement dans la zone autour de center_xy
        cx = int(canvas_w * zone.center_xy_pct[0])
        cy = int(canvas_h * zone.center_xy_pct[1])

        # Hauteur totale du bloc
        line_h_px = int(size * zone.line_height_ratio)
        total_h = line_h_px * len(lines)
        y = cy - total_h // 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            if zone.align == "center":
                x = cx - line_w // 2
            elif zone.align == "left":
                x = cx
            else:  # right
                x = cx - line_w
            draw.text((x, y), line, fill=color, font=font)
            y += line_h_px

    # 6. Sauvegarde
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, "PNG", optimize=True)


# ============================================================
# LAYOUTS PRÊTS À L'EMPLOI
# ============================================================

# I ❤️ X : illustration cœur scène + I à gauche + cœur centre haut + NICHE bas
LAYOUT_IHEART_HEART_FRAME = DesignLayout(
    name="iheart_heart_frame",
    canvas_size=(3000, 3000),
    background_color=(255, 252, 248),
    illustration=IllustrationPlacement(
        center_xy_pct=(0.5, 0.52),
        size_pct=(0.72, 0.65),
        fit_mode="cover",
    ),
    decorative_elements=[
        DecorativeElement(type="heart", center_xy_pct=(0.5, 0.08),
                          size_pct=0.13, color=(200, 30, 50)),
    ],
    text_zones=[
        TextZone(text_key="I", center_xy_pct=(0.12, 0.09),
                 max_box_pct=(0.15, 0.12), font_role="title_bold",
                 color=(40, 30, 30), upper=False, auto_size=False,
                 fallback_size=320),
        TextZone(text_key="niche", center_xy_pct=(0.5, 0.93),
                 max_box_pct=(0.85, 0.10), font_role="title_bold",
                 color=(40, 30, 30), upper=True, max_lines=1),
    ],
)


# Bible verse : référence en haut + verset central grand + ornement bas
LAYOUT_BIBLE_VERSE = DesignLayout(
    name="bible_verse",
    canvas_size=(3000, 3000),
    background_color=(252, 248, 235),
    background_overlay=(252, 248, 235, 180),
    blur_bg=4.0,
    text_zones=[
        TextZone(text_key="reference", center_xy_pct=(0.5, 0.13),
                 max_box_pct=(0.7, 0.08), font_role="title_italic",
                 color=(120, 80, 30), max_lines=1, auto_size=False,
                 fallback_size=90),
        TextZone(text_key="verse", center_xy_pct=(0.5, 0.50),
                 max_box_pct=(0.82, 0.55), font_role="title_serif",
                 color=(40, 30, 25), max_lines=6, auto_size=True),
    ],
    decorative_elements=[
        DecorativeElement(type="horizontal_line",
                          center_xy_pct=(0.5, 0.18),
                          size_pct=0.18, color=(180, 140, 60),
                          extra={"thickness": 3}),
        DecorativeElement(type="horizontal_line",
                          center_xy_pct=(0.5, 0.85),
                          size_pct=0.18, color=(180, 140, 60),
                          extra={"thickness": 3}),
    ],
)


# Cultural word : mot grand + (optionnel) translation petit
LAYOUT_CULTURAL_WORD = DesignLayout(
    name="cultural_word",
    canvas_size=(3000, 3000),
    background_color=(248, 244, 235),
    text_zones=[
        TextZone(text_key="word", center_xy_pct=(0.5, 0.42),
                 max_box_pct=(0.85, 0.30), font_role="title_bold",
                 color=(40, 30, 25), max_lines=1, auto_size=True),
        TextZone(text_key="language_class", center_xy_pct=(0.5, 0.56),
                 max_box_pct=(0.7, 0.05), font_role="body_serif_italic",
                 color=(120, 90, 70), max_lines=1, auto_size=True),
        TextZone(text_key="meaning", center_xy_pct=(0.5, 0.70),
                 max_box_pct=(0.75, 0.20), font_role="body_serif",
                 color=(80, 70, 60), max_lines=4, auto_size=True),
    ],
    decorative_elements=[
        DecorativeElement(type="horizontal_line",
                          center_xy_pct=(0.5, 0.61),
                          size_pct=0.06, color=(150, 110, 80),
                          extra={"thickness": 2}),
    ],
)


# Literal idiom : phrase originale + traduction littérale + sens
LAYOUT_LITERAL_IDIOM = DesignLayout(
    name="literal_idiom",
    canvas_size=(3000, 3000),
    background_color=(250, 245, 235),
    background_overlay=(250, 245, 235, 160),
    blur_bg=5.0,
    text_zones=[
        TextZone(text_key="original", center_xy_pct=(0.5, 0.18),
                 max_box_pct=(0.85, 0.10), font_role="title_italic",
                 color=(80, 60, 40), max_lines=2, auto_size=True),
        TextZone(text_key="literal", center_xy_pct=(0.5, 0.40),
                 max_box_pct=(0.88, 0.25), font_role="title_bold",
                 color=(40, 30, 25), max_lines=3, auto_size=True),
        TextZone(text_key="meaning", center_xy_pct=(0.5, 0.75),
                 max_box_pct=(0.78, 0.15), font_role="body_serif_italic",
                 color=(100, 80, 70), max_lines=3, auto_size=True),
    ],
    decorative_elements=[
        DecorativeElement(type="horizontal_line",
                          center_xy_pct=(0.5, 0.26),
                          size_pct=0.10, color=(160, 110, 70),
                          extra={"thickness": 2}),
        DecorativeElement(type="horizontal_line",
                          center_xy_pct=(0.5, 0.64),
                          size_pct=0.10, color=(160, 110, 70),
                          extra={"thickness": 2}),
    ],
)


# Viral format : texte central énorme sur fond ambiant
LAYOUT_VIRAL_TEXT_CENTERED = DesignLayout(
    name="viral_text_centered",
    canvas_size=(3000, 3000),
    background_color=(250, 245, 235),
    background_overlay=(250, 245, 235, 200),
    blur_bg=6.0,
    text_zones=[
        TextZone(text_key="text", center_xy_pct=(0.5, 0.5),
                 max_box_pct=(0.85, 0.7), font_role="title_bold",
                 color=(40, 30, 30), max_lines=5, auto_size=True),
    ],
)


# Quote minimaliste centrée
LAYOUT_QUOTE_MINIMAL = DesignLayout(
    name="quote_minimal",
    canvas_size=(3000, 3000),
    background_color=(252, 248, 240),
    text_zones=[
        TextZone(text_key="quote", center_xy_pct=(0.5, 0.5),
                 max_box_pct=(0.82, 0.5), font_role="title_serif",
                 color=(40, 35, 30), max_lines=4, auto_size=True),
    ],
)


# I ❤️ X avec illustration en MASK cœur (l'illustration prend la forme d'un cœur)
LAYOUT_IHEART_MASKED = DesignLayout(
    name="iheart_masked",
    canvas_size=(3000, 3000),
    background_color=(255, 252, 248),
    illustration=IllustrationPlacement(
        center_xy_pct=(0.5, 0.5),
        size_pct=(0.70, 0.70),
        fit_mode="cover",
        mask_shape="heart",  # ← l'illustration devient un cœur
    ),
    text_zones=[
        TextZone(text_key="I", center_xy_pct=(0.18, 0.50),
                 max_box_pct=(0.18, 0.16), font_role="title_bold",
                 color=(40, 30, 30), auto_size=False, fallback_size=400),
        TextZone(text_key="niche", center_xy_pct=(0.5, 0.92),
                 max_box_pct=(0.85, 0.10), font_role="title_bold",
                 color=(40, 30, 30), upper=True, max_lines=1),
    ],
)


# KDP cover : bandeau titre haut + illustration milieu + auteur bas
LAYOUT_KDP_COVER = DesignLayout(
    name="kdp_cover",
    canvas_size=(2625, 3375),  # 8.75 × 11.25 inch bleed @ 300 DPI
    background_color=(252, 248, 240),
    background_overlay=(252, 248, 240, 80),  # léger voile pour cohérence
    illustration=IllustrationPlacement(
        center_xy_pct=(0.5, 0.55),
        size_pct=(1.0, 0.65),
        fit_mode="cover",
    ),
    text_zones=[
        TextZone(text_key="title", center_xy_pct=(0.5, 0.13),
                 max_box_pct=(0.85, 0.16), font_role="title_bold",
                 color=(40, 30, 25), max_lines=2, upper=True),
        TextZone(text_key="subtitle", center_xy_pct=(0.5, 0.25),
                 max_box_pct=(0.85, 0.05), font_role="title_italic",
                 color=(80, 60, 50), max_lines=2),
        TextZone(text_key="author", center_xy_pct=(0.5, 0.94),
                 max_box_pct=(0.7, 0.05), font_role="body_sans",
                 color=(60, 50, 40), max_lines=1, auto_size=True),
    ],
)


# Registry pour accès par nom
LAYOUTS = {
    "iheart_heart_frame": LAYOUT_IHEART_HEART_FRAME,
    "iheart_masked": LAYOUT_IHEART_MASKED,
    "bible_verse": LAYOUT_BIBLE_VERSE,
    "cultural_word": LAYOUT_CULTURAL_WORD,
    "literal_idiom": LAYOUT_LITERAL_IDIOM,
    "viral_text_centered": LAYOUT_VIRAL_TEXT_CENTERED,
    "quote_minimal": LAYOUT_QUOTE_MINIMAL,
    "kdp_cover": LAYOUT_KDP_COVER,
}


def get_layout(name: str) -> DesignLayout:
    if name not in LAYOUTS:
        raise KeyError(f"Layout '{name}' inconnu. Choix : {list(LAYOUTS)}")
    return LAYOUTS[name]
