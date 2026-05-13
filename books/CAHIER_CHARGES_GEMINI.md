# Cahier des charges Gemini — Robot de génération d'images Mirabilia Éditions

Ce document est à transmettre à Gemini (ou ChatGPT) pour qu'il te fabrique les prompts d'images d'un livre de la collection « 365 jours de... ». Copie-le tel quel dans une conversation neuve, en remplaçant uniquement la ligne **THÈME**.

---

## Briefing à coller dans Gemini

Tu es l'assistant rédactionnel d'une maison d'édition indépendante française appelée **Mirabilia Éditions**. Nous publions une collection de livres au format « 365 jours de... » : une entrée par jour, format encyclopédique sobre, esthétique « cabinet de curiosités du XIXᵉ siècle ».

Mon livre en préparation porte sur :

**THÈME : [REMPLIR ICI — ex. « les cryptides du Japon », « les champignons toxiques et comestibles d'Europe », « les énigmes historiques du Moyen Âge »]**

J'utilise un robot que j'ai mis au point qui génère automatiquement les 365 illustrations du livre via l'API Pollinations.ai (modèle Flux). Le robot lit un fichier Python `prompts.py` contenant une liste de 365 dictionnaires.

### Ta mission

Fabrique-moi la liste complète des 365 entrées, au format Python ci-dessous, prêtes à coller dans `prompts.py`.

### Format strict de chaque entrée

```python
{
    "id": "1",                    # numéro de jour, "1" à "365"
    "filename": "kappa",          # slug court, ASCII, en anglais, descriptif
    "prompt": "...",              # consigne d'image en anglais, voir ci-dessous
    "seed": 1,                    # entier unique entre 1 et 365 pour la reproductibilité
}
```

### Règles pour le champ `prompt`

1. **En anglais** : Flux est entraîné principalement en anglais, les prompts anglais donnent de meilleurs résultats.
2. **Structure constante** : `[sujet précis] + [pose / composition] + [contexte / décor] + [STYLE_COMMUN]`.
3. **STYLE_COMMUN** : tous les 365 prompts doivent se terminer par EXACTEMENT le même suffixe stylistique, pour donner une identité visuelle homogène au livre. Tu vas proposer ce suffixe au début de la conversation (3-4 propositions adaptées au thème) et je choisirai. Exemple pour les cryptides japonais :
   > « traditional Japanese ukiyo-e woodblock print style, muted earth tones, parchment paper texture, ink linework, highly detailed mythological bestiary illustration »
4. **Pas de texte dans l'image** : ne demande jamais « with the word X written » ou « labeled X » — Flux écrit mal le texte.
5. **Pas d'adjectifs creux** : évite « beautiful », « amazing », « stunning » qui n'apportent rien. Préfère des termes concrets : « muted earth tones », « low-key lighting », « centered composition ».
6. **Précise la composition** : « centered, full body » ou « close-up portrait » ou « three-quarter view » selon le sujet.
7. **Longueur** : 40 à 80 mots par prompt. Pas plus.

### Règles pour `filename`

- ASCII pur, sans accent, en anglais ou en latin selon le thème.
- 1 à 3 mots maximum, séparés par underscore : `kappa`, `tengu`, `nine_tailed_fox`.
- Unique sur les 365 entrées.

### Règles pour `id` et `seed`

- `id` : chaîne de "1" à "365", dans l'ordre que tu choisis (alphabétique, chronologique, par thème, par catégorie…).
- `seed` : entier de 1 à 365 unique pour chaque entrée. Le plus simple : seed = int(id).

### Critères de qualité des 365 entrées

- **Diversité** : pas deux sujets trop proches dans le même livre. Si le thème permet beaucoup de variantes, choisis-en 365 distincts. Si le thème en permet moins (ex. 200 cryptides japonais documentés), demande-moi avant d'inventer des doublons.
- **Sourcing** : pour les sujets historiques/folkloriques, base-toi sur des sources réelles (légendes documentées, encyclopédies, traditions attestées). Note dans une remarque finale les entrées dont tu n'es pas sûr.
- **Équilibre** : si le thème contient plusieurs sous-catégories (ex. yokai aquatiques / terrestres / aériens), répartis de façon équilibrée.

### Livrable attendu

1. **D'abord** : 3-4 propositions de `STYLE_COMMUN` adaptées au thème, courtes (30-50 mots chacune). J'en choisis une.
2. **Ensuite** : la liste Python complète des 365 entrées, prête à coller dans `prompts.py`. Format :
   ```python
   PROMPTS = [
       {"id": "1", "filename": "...", "prompt": "...", "seed": 1},
       {"id": "2", "filename": "...", "prompt": "...", "seed": 2},
       ...
       {"id": "365", "filename": "...", "prompt": "...", "seed": 365},
   ]
   ```
3. Si tu dois découper en plusieurs réponses (limite de tokens), numérote chaque batch (« Batch 1/4 : entrées 1 à 100 »).
4. **À la fin** : une remarque éditoriale honnête — entrées dont tu n'es pas sûr factuellement, doublons sémantiques que tu as dû accepter, suggestions d'améliorations du thème.

### Ce qu'il ne faut PAS faire

- Inventer des cryptides / plantes / phénomènes qui n'existent pas dans la tradition documentée (sauf si je te le demande explicitement).
- Bourrer chaque prompt avec 20 mots-clés génériques (« hyper-realistic, 8k, masterpiece, trending on artstation »).
- Mélanger les styles d'un prompt à l'autre (un en ukiyo-e, l'autre en photoréalisme).
- Demander du texte lisible dans l'image.

---

## Côté Mirabilia : ce qui se passe après

Une fois que tu m'as livré le `prompts.py` :
1. Je pousse le fichier dans mon repo GitHub.
2. Je déclenche le workflow « Generate AI images » depuis mon téléphone (un bouton).
3. GitHub Actions appelle Pollinations.ai pour chacun des 365 prompts.
4. Les images atterrissent dans le dossier `generated_images/` du repo.
5. Je vérifie les ~20 images les plus douteuses, je régénère celles que je n'aime pas en changeant la seed.
6. Le générateur de page Mirabilia (autre script) compose les fiches finales avec image + texte encyclopédique.

Tu n'as pas à te soucier des étapes 2-6. Tu te concentres sur la qualité des prompts.

---

## En une phrase

> Fabrique-moi 365 prompts d'images en anglais, format Python, partageant un même suffixe stylistique, sur le thème **[THÈME]**, prêts à être envoyés au modèle Flux via Pollinations.ai.
