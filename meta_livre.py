"""
Métadonnées centrales d'un livre Mirabilia Éditions.

Ce fichier pilote TOUS les scripts du pipeline industriel :
- générateur de page (mise en page intérieure)
- fabricant de couverture
- générateur de visuels marketing
- exporteur Amazon KDP / Print-on-Demand
- juge IA des images générées

Pour chaque nouveau livre :
    1. Copie ce fichier sous le nom meta_livre.py (1 par repo).
    2. Renseigne tous les champs.
    3. Tous les scripts liront automatiquement cette config.

Format Python (pas de YAML/JSON) pour rester cohérent avec Info.py et
prompts.py, et pour permettre commentaires + calculs si besoin.
"""

META = {
    # ─────────────────────────────────────────────────────────────────
    # IDENTITÉ DU LIVRE
    # ─────────────────────────────────────────────────────────────────
    "livre": {
        "slug":        "plantes_medicinales",
        "titre":       "365 jours des plantes médicinales",
        "sous_titre":  "Une encyclopédie botanique du quotidien",
        "thème":       "Plantes médicinales et leurs usages traditionnels",
        "résumé_4e":   "",  # 4e de couverture, à remplir une fois rédigée
        "langue":      "fr",
        "nb_entrées":  365,
    },

    # ─────────────────────────────────────────────────────────────────
    # PUBLICATION
    # ─────────────────────────────────────────────────────────────────
    "publication": {
        "éditeur":      "Mirabilia Éditions",
        "auteur":       "",  # nom à afficher en couverture
        "année":        2026,
        "isbn":         "",
        "dépôt_légal":  "",
        "édition":      "Première édition",
    },

    # ─────────────────────────────────────────────────────────────────
    # FORMAT PHYSIQUE (impression)
    # ─────────────────────────────────────────────────────────────────
    "format": {
        "page_largeur_mm":  148,   # A5 par défaut
        "page_hauteur_mm":  210,
        "marges_mm": {
            "haut":     18,
            "bas":      18,
            "intérieur": 20,  # côté reliure
            "extérieur": 15,
        },
        "fond_perdu_mm":    3,
        "dpi":              300,
    },

    # ─────────────────────────────────────────────────────────────────
    # IDENTITÉ VISUELLE
    # ─────────────────────────────────────────────────────────────────
    "typographie": {
        "titre":     "Cormorant Garamond",
        "corps":     "Crimson Pro",
        "accent":    "EB Garamond Italic",
        "tailles_pt": {
            "titre_fiche":  22,
            "sous_titre":   13,
            "corps":        11,
            "légende":      9,
        },
    },
    "palette": {
        "fond":       "#f4ede0",  # parchemin clair
        "encre":      "#2a2418",  # encre brune profonde
        "accent":     "#8b6f47",  # sépia
        "ornement":   "#a89270",  # filets décoratifs
    },

    # ─────────────────────────────────────────────────────────────────
    # SOURCES DE DONNÉES (chemins relatifs à la racine du repo)
    # ─────────────────────────────────────────────────────────────────
    "sources": {
        "fiches":             "Info.py",          # contenu rédactionnel
        "images_dir":         "images",           # illustrations validées
        "generated_dir":      "generated_images", # images IA brutes
        "scores":             "image_scores.json",
        "cover":              "cover.jpg",        # cover plate (face)
        "back_cover":         "back_cover.jpg",
    },

    # ─────────────────────────────────────────────────────────────────
    # CHAÎNE IA
    # ─────────────────────────────────────────────────────────────────
    "ia": {
        "rédaction":          "Gemini 2.0 Pro",
        "images":             "Pollinations.ai (Flux)",
        "juge_images":        "Gemini 2.0 Flash (vision)",
        "déclaration_amazon": False,  # passe à True si images IA-générées
    },

    # ─────────────────────────────────────────────────────────────────
    # CRITÈRES POUR LE JUGE IA (score_images.py)
    # ─────────────────────────────────────────────────────────────────
    "jugement_images": {
        "critères": [
            "fidélité au sujet (l'image illustre-t-elle bien la plante ?)",
            "qualité botanique (les feuilles, fleurs, fruits sont-ils plausibles ?)",
            "composition (cadrage, équilibre, lisibilité du sujet principal)",
            "qualité technique (netteté, absence d'artefacts IA, pas de doigts/feuilles déformés)",
        ],
        "seuil_acceptation":  3.5,  # score moyen min sur 5
    },

    # ─────────────────────────────────────────────────────────────────
    # MARKETING
    # ─────────────────────────────────────────────────────────────────
    "marketing": {
        "accroche_courte":    "365 plantes médicinales, une par jour, à découvrir comme un cabinet de curiosités.",
        "site":               "https://mirabilia-editions.fr",
        "instagram":          "@mirabilia.editions",
        "prix_ttc":           24.90,
        "catégorie_amazon":   "Botanique > Plantes médicinales",
        "mots_clés_amazon":   [
            "plantes médicinales",
            "phytothérapie",
            "herboristerie",
            "encyclopédie botanique",
            "365 jours",
            "Köhler",
        ],
    },
}


def load():
    """Helper pour les autres scripts."""
    return META
