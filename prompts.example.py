"""
Fichier modèle pour le robot de génération d'images Pollinations.ai.

Pour l'utiliser :
1. Copie ce fichier sous le nom `prompts.py` à la racine du repo.
2. Remplace la liste PROMPTS ci-dessous par tes 365 entrées.
3. Push sur GitHub, puis déclenche le workflow "Generate AI images"
   depuis l'onglet Actions du repo.

Format d'une entrée :
- id        : numéro (string ou int), utilisé pour préfixer le nom de fichier
              (ex. id="1" → 001_xxx.jpg). Garde le tri chronologique.
- filename  : slug court qui décrit l'image (ex. "kappa", "tengu").
              Sera nettoyé automatiquement (accents, espaces, etc.).
- prompt    : la consigne envoyée au modèle. EN ANGLAIS pour de meilleurs
              résultats. Décris : sujet + style + composition + ambiance.
- seed      : (optionnel) entier pour reproductibilité. Même seed + même
              prompt = même image. Pratique pour régénérer plus tard.

Conseils pour les prompts :
- Style cohérent : ajoute le même suffixe à TOUS les prompts pour que la
  collection ait une identité visuelle homogène. Ex. ", traditional
  Japanese ukiyo-e woodblock print, muted earth tones, parchment texture".
- Précise toujours : sujet (au début), style artistique, palette,
  lumière, format. Évite "beautiful", "amazing" — sans effet.
- Pour les sujets fantastiques, ajoute "highly detailed, mythological
  bestiary illustration".
- Pour les portraits/personnages, indique pose et expression.
- Évite tout texte dans l'image (Flux écrit mal) : ne mets pas de mots
  censés apparaître dans la composition.
"""

PROMPTS = [
    {
        "id": "1",
        "filename": "kappa",
        "prompt": (
            "A traditional Japanese kappa yokai, aquatic green humanoid "
            "creature with a turtle shell on its back and a water-filled "
            "depression on top of its head, standing in shallow river water, "
            "traditional Japanese ukiyo-e woodblock print style, muted "
            "earth tones, parchment paper texture, ink linework, full body, "
            "centered composition, highly detailed mythological bestiary "
            "illustration"
        ),
        "seed": 1,
    },
    {
        "id": "2",
        "filename": "tengu",
        "prompt": (
            "A traditional Japanese tengu yokai, mountain spirit with long "
            "red nose and crow features, wearing ascetic monk robes, "
            "holding a feather fan, perched on a pine branch at dawn, "
            "traditional Japanese ukiyo-e woodblock print style, muted "
            "earth tones, parchment paper texture, ink linework, "
            "highly detailed mythological bestiary illustration"
        ),
        "seed": 2,
    },
    {
        "id": "3",
        "filename": "kitsune",
        "prompt": (
            "A traditional Japanese nine-tailed kitsune fox spirit, white "
            "fur with red markings, standing on a moss-covered shrine "
            "stone, multiple tails curling in the air, glowing eyes, "
            "moonlit night, traditional Japanese ukiyo-e woodblock print "
            "style, muted earth tones, parchment paper texture, ink "
            "linework, highly detailed mythological bestiary illustration"
        ),
        "seed": 3,
    },
    # … remplis jusqu'à 365 entrées en gardant ce schéma.
]
