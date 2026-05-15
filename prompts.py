"""
Test rapide de 5 mandalas via Pollinations Flux.

Objectif : valider la qualité du line art Pollinations pour les mandalas
avant de lancer la production complète des 100 mandalas Floral Mandalas.

STYLE_COMMUN ultra-strict (no color, no shading, lignes nettes,
8-fold radial symmetry) pour maximiser les chances de sortir du
coloring-book-quality directement.

Si la qualité est bonne après post-processing Pillow (threshold +
symétrie forcée), on garde Pollinations pour Inkwell & Hush.
Sinon on bascule sur Ideogram avec compte.
"""

# Suffixe stylistique identique sur tous les prompts pour cohérence.
STYLE = (
    "perfectly symmetric mandala viewed from above, black ink line art on "
    "pure white background, NO COLOR, NO SHADING, NO GRADIENT, thick clean "
    "outlines, intricate ornate filigree details, high contrast coloring "
    "book page design, vector-style precision, 8-fold radial symmetry, "
    "centered composition, fine ornamental patterns, sharp crisp lines, "
    "professional adult coloring book quality, no text, no signature"
)

PROMPTS = [
    {
        "id": "1",
        "filename": "test_mandala_rose_floral",
        "prompt": f"A floral mandala centered on a blooming rose with detailed petals and leaves radiating outward, vintage botanical illustration style, {STYLE}",
        "seed": 1001,
    },
    {
        "id": "2",
        "filename": "test_mandala_sacred_geometry",
        "prompt": f"A sacred geometry mandala with concentric circles, hexagons and triangles forming a flower of life pattern, mathematical precision, {STYLE}",
        "seed": 1002,
    },
    {
        "id": "3",
        "filename": "test_mandala_art_nouveau_lotus",
        "prompt": f"An art nouveau mandala centered on a lotus flower with flowing organic lines and ornamental swirls, Alphonse Mucha inspired patterns, {STYLE}",
        "seed": 1003,
    },
    {
        "id": "4",
        "filename": "test_mandala_cosmic_sun_moon",
        "prompt": f"A cosmic mandala with a central sun surrounded by moons stars and celestial patterns, mystical ornamental design, {STYLE}",
        "seed": 1004,
    },
    {
        "id": "5",
        "filename": "test_mandala_tibetan_inspired",
        "prompt": f"A Tibetan thangka inspired mandala with lotus petals, dorje symbols and traditional Buddhist ornamental patterns, sacred art style, {STYLE}",
        "seed": 1005,
    },
]
