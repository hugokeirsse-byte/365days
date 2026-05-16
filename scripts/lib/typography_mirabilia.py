"""
Système typographique Mirabilia — règles communes à tous les livres
de la marque Mirabilia Éditions.

Palette, polices, marges, ornements, dimensions KDP par format.
Importé par tous les scripts produce_*.py qui mettent en page un
livre Mirabilia.
"""

from dataclasses import dataclass, field

# ─────────────────────────────────────────────────────────────────────
# PALETTE COULEURS (par collection)
# ─────────────────────────────────────────────────────────────────────

PALETTE = {
    "ivoire_fond":      (244, 237, 224),   # #F4EDE0 — fond intérieur + couverture
    "or_chaud":         (201, 169, 97),    # #C9A961 — logo, titres, ornements
    "or_pale":          (212, 194, 138),   # #D4C28A — sur fond sombre
    "encre_brune":      (42, 36, 24),      # #2A2418 — corps de texte
    "sepia":            (139, 111, 71),    # #8B6F47 — sous-titres, italiques
    "ornement_pale":    (168, 146, 112),   # #A89270 — filets décoratifs
    # Bandes titre par collection
    "strategy_bleu_nuit":   (30, 42, 74),  # #1E2A4A — Chess, jeux, stratégie
    "botanica_vert_foret":  (31, 61, 42),  # #1F3D2A — Plantes, herbes, nature
    "curiosities_bordeaux": (90, 31, 46),  # #5A1F2E — Cocktails, étranges
    "mythology_noir":       (26, 26, 46),  # #1A1A2E — Cryptides, dieux
    "atlas_marine":         (31, 45, 74),  # #1F2D4A — Voyages, lieux
    "esoterica_violet":     (46, 26, 61),  # #2E1A3D — Tarot, alchimie
}


# ─────────────────────────────────────────────────────────────────────
# POLICES (Google Fonts gratuits, à télécharger dans le workflow)
# ─────────────────────────────────────────────────────────────────────

FONTS = {
    "titre_serie":      "Cormorant Garamond",     # 365 Days of Wonder
    "titre_tome":       "Cormorant Garamond Bold",
    "sous_titre":       "EB Garamond Italic",
    "corps":            "Crimson Pro",
    "drop_cap":         "Cormorant Garamond Bold",
    "footer":           "EB Garamond",
    "nom_latin":        "EB Garamond Italic",
    "url_titre_serie":  "https://fonts.google.com/specimen/Cormorant+Garamond",
    "url_corps":        "https://fonts.google.com/specimen/Crimson+Pro",
    "url_eb":           "https://fonts.google.com/specimen/EB+Garamond",
}

FONT_FILES = {
    # Quand téléchargés via fonts-cormorant-garamond / fonts-crimson-pro / fonts-ebgaramond
    "cormorant_regular": "CormorantGaramond-Regular.ttf",
    "cormorant_bold":    "CormorantGaramond-Bold.ttf",
    "cormorant_italic":  "CormorantGaramond-Italic.ttf",
    "crimson_regular":   "CrimsonPro-Regular.ttf",
    "crimson_italic":    "CrimsonPro-Italic.ttf",
    "ebgaramond_regular": "EBGaramond-Regular.ttf",
    "ebgaramond_italic": "EBGaramond-Italic.ttf",
}


# ─────────────────────────────────────────────────────────────────────
# DIMENSIONS PHYSIQUES (KDP)
# ─────────────────────────────────────────────────────────────────────

@dataclass
class BookFormat:
    """Spécifications physiques d'un livre KDP."""
    name: str
    trim_width_in: float       # largeur trim
    trim_height_in: float      # hauteur trim
    bleed_in: float = 0.125    # bleed standard KDP
    dpi: int = 300

    @property
    def trim_width_pt(self) -> float:
        return self.trim_width_in * 72

    @property
    def trim_height_pt(self) -> float:
        return self.trim_height_in * 72

    @property
    def page_with_bleed_pt(self) -> tuple[float, float]:
        return (
            (self.trim_width_in + 2 * self.bleed_in) * 72,
            (self.trim_height_in + 2 * self.bleed_in) * 72,
        )


FORMATS = {
    # Format carré 8.5×8.5" = signature Mirabilia (tous les livres)
    "mirabilia_square": BookFormat(
        name="Mirabilia Square",
        trim_width_in=8.5,
        trim_height_in=8.5,
    ),
    # Formats KDP alternatifs si besoin
    "kdp_5x8": BookFormat(name="KDP 5x8", trim_width_in=5.0, trim_height_in=8.0),
    "kdp_6x9": BookFormat(name="KDP 6x9", trim_width_in=6.0, trim_height_in=9.0),
}


# ─────────────────────────────────────────────────────────────────────
# MARGES (en pouces, mesurées du trim)
# ─────────────────────────────────────────────────────────────────────

@dataclass
class Margins:
    top_in: float = 0.75
    bottom_in: float = 0.75
    inner_in: float = 0.875       # côté reliure
    outer_in: float = 0.625       # côté extérieur


MIRABILIA_MARGINS = Margins(
    top_in=0.75,
    bottom_in=0.75,
    inner_in=0.875,
    outer_in=0.625,
)


# ─────────────────────────────────────────────────────────────────────
# TAILLES TYPOGRAPHIQUES (en points)
# ─────────────────────────────────────────────────────────────────────

TYPE_SIZES = {
    "titre_serie":      9,      # MIRABILIA ÉDITIONS petit en haut de couverture
    "titre_principal":  42,     # 365 DAYS OF WONDER sur couverture
    "titre_collection": 14,     # THE STRATEGY COLLECTION
    "titre_tome":       28,     # Chess Puzzles · Volume I
    "chapter_title":    24,     # MOIS 1 — FORKS
    "section_title":    14,     # Puzzle #1
    "corps":            11,
    "footer":           9,
    "drop_cap":         48,
    "nom_latin":        10,
    "page_number":      9,
}


# ─────────────────────────────────────────────────────────────────────
# INTERLIGNE et ESPACEMENT
# ─────────────────────────────────────────────────────────────────────

LINE_SPACING = {
    "corps":            14,     # interligne 11/14
    "chapter_title":    30,
    "section_title":    18,
}

PARAGRAPH_SPACING = {
    "after_paragraph":  6,
    "after_section":    18,
    "before_chapter":   72,     # saut de page logique
}


# ─────────────────────────────────────────────────────────────────────
# ORNEMENTS Mirabilia (caractères Unicode décoratifs)
# ─────────────────────────────────────────────────────────────────────

ORNAMENTS = {
    "fleuron":          "❦",     # fleuron classique
    "asterism":         "⁂",     # trois étoiles
    "section_break":    "•   •   •",
    "double_diamond":   "❖ ❖",
    "scroll_left":      "⊰",
    "scroll_right":     "⊱",
    "ornament_filet":   "————",
}


# ─────────────────────────────────────────────────────────────────────
# COLLECTION CONFIG (pour la couverture et les bandes)
# ─────────────────────────────────────────────────────────────────────

COLLECTIONS = {
    "strategy": {
        "display_name": "The Strategy Collection",
        "band_color_key": "strategy_bleu_nuit",
        "themes": ["chess", "go", "puzzles", "strategy_games"],
    },
    "botanica": {
        "display_name": "The Botanica Collection",
        "band_color_key": "botanica_vert_foret",
        "themes": ["plants", "herbs", "flowers", "trees"],
    },
    "curiosities": {
        "display_name": "The Curiosities Collection",
        "band_color_key": "curiosities_bordeaux",
        "themes": ["cocktails", "recipes", "oddities", "strange_facts"],
    },
    "mythology": {
        "display_name": "The Mythology Collection",
        "band_color_key": "mythology_noir",
        "themes": ["cryptids", "gods", "legends", "folklore"],
    },
    "atlas": {
        "display_name": "The Atlas Collection",
        "band_color_key": "atlas_marine",
        "themes": ["places", "travel", "geography", "world"],
    },
    "esoterica": {
        "display_name": "The Esoterica Collection",
        "band_color_key": "esoterica_violet",
        "themes": ["tarot", "alchemy", "occult", "esoteric"],
    },
}


def get_collection_band_color(collection_key: str) -> tuple[int, int, int]:
    """Retourne la couleur de bande RGB pour cette collection."""
    if collection_key not in COLLECTIONS:
        raise ValueError(f"Collection inconnue : {collection_key}")
    return PALETTE[COLLECTIONS[collection_key]["band_color_key"]]


if __name__ == "__main__":
    print(f"Palette : {len(PALETTE)} couleurs")
    print(f"Formats : {len(FORMATS)}")
    print(f"Collections : {len(COLLECTIONS)}")
    for key, c in COLLECTIONS.items():
        rgb = get_collection_band_color(key)
        print(f"  {key:<14} → {c['display_name']:<30} RGB{rgb}")
