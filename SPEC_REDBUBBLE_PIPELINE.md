# Cahier des charges — Pipeline images (Redbubble POD + Livres KDP)
*À destination de Claude Code pour implémentation*

## Contexte

Pipeline de génération et traitement d'images utilisé pour deux usages :
1. **Livres KDP** — illustrations intérieures haute résolution
2. **Designs Redbubble POD** — prints, posters, t-shirts, etc.

L'upscaler est un outil partagé. Il tourne uniquement sur les images
**manuellement sélectionnées** par l'utilisateur — jamais en automatique,
jamais sur le batch complet.

**Contraintes dures :**
- Zéro budget. APIs gratuites uniquement.
- Pilotage Android via GitHub mobile (bouton "Run workflow" + édition de fichier texte).
- Quota Hugging Face à préserver : on n'upscale que ce que l'utilisateur a validé.

---

## Vue d'ensemble du pipeline

```
[1] prompts_images.py           ← config : niche + prompts + style
        ↓
[2] generate_images.py          ← génère N images via Pollinations.ai
        ↓
[3] score_images.py             ← note toutes les images via Gemini Vision
                                   (aide au tri, pas de sélection auto)
        ↓
[4] >>> L'UTILISATEUR CHOISIT <<<
        Il édite to_upscale.txt depuis GitHub mobile
        et y écrit les noms des fichiers qu'il veut upscaler
        ↓
[5] upscale_selected.py         ← upscale UNIQUEMENT les fichiers listés
                                   dans to_upscale.txt via Real-ESRGAN (HF)
        ↓
[6] /output/                    ← images finales 4096px, prêtes à l'emploi
                                   (livres KDP ou upload Redbubble)
```

---

## Détail de chaque brique

### [1] `prompts_images.py` — Config

Un seul fichier à modifier pour changer de niche ou de projet.

```python
PROJECT = "botanical_watercolor"   # nom du dossier de sortie

STYLE_SUFFIX = (
    "botanical watercolor illustration, soft color washes, "
    "white background, high detail, professional quality, isolated plant"
)

SUBJECTS = [
    "chamomile flower",
    "lavender sprig",
    "rosemary branch",
    # ...
]

N_IMAGES_PER_SUBJECT = 3   # images générées par sujet
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024
```

Changer de projet = modifier uniquement ce fichier.

---

### [2] `generate_images.py` — Génération via Pollinations.ai

- Construit le prompt : `SUBJECTS[i]` + `, ` + `STYLE_SUFFIX`
- Appelle `https://image.pollinations.ai/prompt/{prompt}?width={W}&height={H}&nologo=true`
- Sauvegarde dans `/images_raw/{PROJECT}/{subject}_{index}.jpg`
- Idempotent : si le fichier existe déjà, skip
- Retry automatique (3 tentatives, délai exponentiel) sur timeout
- Log clair dans GitHub Actions

---

### [3] `score_images.py` — Notation via Gemini Vision

**Rôle : aider l'utilisateur à trier, pas décider à sa place.**

- Lit tous les fichiers de `/images_raw/{PROJECT}/`
- Pour chaque image, appelle Gemini Vision avec le prompt :

```
Rate this image for print quality on a scale of 1-10.
Criteria:
- Clean light background (important for print): /3
- Visual clarity and sharpness: /3
- Overall quality and appeal: /4

Return JSON only: {"score": X, "background_clean": true/false}
```

- Génère `/scores/{PROJECT}_scores.json`
- **Génère aussi `/scores/{PROJECT}_review.md`** : un fichier Markdown
  lisible depuis GitHub mobile, avec pour chaque image son score,
  son statut fond propre, et l'URL de l'image pour la voir directement.
  Exemple de ligne :
  ```
  | chamomile_1.jpg | 8/10 | ✅ fond propre | ![](../images_raw/botanical_watercolor/chamomile_1.jpg) |
  ```
- Checkpoint : si le quota Gemini est atteint, sauvegarde la progression
  et reprend au prochain run

---

### [4] `to_upscale.txt` — Sélection manuelle

**C'est l'unique étape manuelle. L'utilisateur édite ce fichier depuis GitHub mobile.**

Format : un nom de fichier par ligne.

```
chamomile_1.jpg
lavender_3.jpg
rosemary_2.jpg
mint_1.jpg
```

Il ouvre `/scores/{PROJECT}_review.md` pour voir les images notées,
choisit celles qu'il veut, et écrit leurs noms dans `to_upscale.txt`.

Quand il est prêt, il lance le workflow `upscale` depuis GitHub mobile.

---

### [5] `upscale_selected.py` — Upscale Real-ESRGAN

**Upscale UNIQUEMENT les fichiers listés dans `to_upscale.txt`.**

- Lit `to_upscale.txt`
- Pour chaque fichier listé :
  - Cherche l'image dans `/images_raw/{PROJECT}/`
  - Appelle l'API Hugging Face Inference avec Real-ESRGAN
  - Sauvegarde dans `/output/{PROJECT}/{filename}_4x.png`
- Checkpoint : si une image est déjà dans `/output/`, skip
- Si quota HF atteint en cours de run, s'arrête proprement
  et log combien il reste à traiter
- À la fin : log du nombre d'images traitées + taille finale

**Secret GitHub requis** : `HF_TOKEN` (token Hugging Face gratuit)

Format de sortie : PNG, ×4 résolution (1024px → 4096px).
4096px = suffisant pour poster A2 à 300 DPI et pour les intérieurs KDP.

---

### [6] Workflow GitHub Actions — `images_pipeline.yml`

Déclenchement : **manuel uniquement** (`workflow_dispatch`).

```yaml
name: Images Pipeline

on:
  workflow_dispatch:
    inputs:
      step:
        description: 'Étape à lancer'
        required: true
        default: 'generate'
        type: choice
        options:
          - generate      # Génère les images (étape 2)
          - score         # Note toutes les images (étape 3)
          - upscale       # Upscale les fichiers dans to_upscale.txt (étape 5)
      project:
        description: 'Nom du projet (doit correspondre à PROJECT dans prompts_images.py)'
        required: true
        default: 'botanical_watercolor'
```

**Pourquoi les étapes sont séparées :**
- `generate` peut tourner des heures sur 200 images
- `score` consomme du quota Gemini (1500 req/jour)
- `upscale` consomme du quota HF et doit attendre la sélection manuelle

L'utilisateur lance chaque étape quand il est prêt, depuis GitHub mobile.

**Secrets GitHub Actions requis :**
- `GEMINI_API_KEY`
- `HF_TOKEN`

---

## Structure de dossiers

```
/
├── prompts_images.py             ← config projet (seul fichier à modifier)
├── generate_images.py
├── score_images.py
├── upscale_selected.py
├── to_upscale.txt                ← liste manuelle des images à upscaler
├── images_raw/
│   └── botanical_watercolor/    ← images brutes 1024px
├── scores/
│   ├── botanical_watercolor_scores.json
│   └── botanical_watercolor_review.md   ← lisible depuis GitHub mobile
├── output/
│   └── botanical_watercolor/    ← images finales 4096px (livres + Redbubble)
└── .github/workflows/
    └── images_pipeline.yml
```

---

## Usage selon la destination

**Pour un livre KDP :**
1. Générer les illustrations du livre
2. Scorer pour identifier les meilleures
3. Sélectionner manuellement celles qui vont dans le livre → `to_upscale.txt`
4. Upscaler → `/output/` → intégrer dans le PDF du livre

**Pour Redbubble POD :**
1. Générer des designs (niche au choix — pas uniquement botanique)
2. Scorer pour trier
3. Sélectionner les designs vendables → `to_upscale.txt`
4. Upscaler → `/output/` → upload manuel sur Redbubble/Displate/Society6

**Le pipeline est identique. Seul `prompts_images.py` change selon le projet.**
