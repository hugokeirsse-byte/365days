# Cahier des charges — Pipeline Redbubble POD
*À destination de Claude Code pour implémentation*

## Contexte

L'infrastructure existante génère des images via Pollinations.ai (Flux) et les note via Gemini Vision. L'objectif ici est d'ajouter un pipeline secondaire dédié à la création de designs print-on-demand pour Redbubble.

**Contraintes dures :**
- Zéro budget. APIs gratuites uniquement.
- Pilotage Android via GitHub mobile (bouton "Run workflow").
- Quota à préserver : Hugging Face Inference API (Real-ESRGAN) est gratuit mais limité. **On n'upscale que les images sélectionnées**, jamais le batch complet.
- Tout tourne dans GitHub Actions. Aucun serveur, aucun VPS.

---

## Ce que le pipeline doit faire (vue d'ensemble)

```
[1] prompts_redbubble.py        ← fichier de config : niche + prompts
        ↓
[2] generate_images.py          ← génère N images via Pollinations.ai
        ↓
[3] score_images.py             ← note toutes les images via Gemini Vision
        ↓
[4] select_top.py               ← copie les TOP K images dans /selected/
        ↓
[5] upscale_images.py           ← upscale UNIQUEMENT /selected/ via Real-ESRGAN
        ↓
[6] /output_redbubble/          ← dossier final, images prêtes pour upload
```

Chaque étape est un script Python indépendant, déclenchable séparément ou en chaîne via un workflow GitHub Actions.

---

## Détail de chaque brique

### [1] `prompts_redbubble.py` — Config de la niche

Fichier de configuration unique à modifier pour changer de niche. Exemple :

```python
NICHE = "botanical_watercolor"

STYLE_SUFFIX = (
    "botanical watercolor illustration, soft color washes, "
    "white background, high detail, professional quality, isolated plant"
)

SUBJECTS = [
    "chamomile flower",
    "lavender sprig",
    "rosemary branch",
    "mint leaves",
    # ... autant de sujets que voulu
]

N_IMAGES_PER_SUBJECT = 3   # nombre d'images générées par sujet
TOP_K = 30                  # nombre d'images à sélectionner pour l'upscale
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024
```

**Le prompt final envoyé à Pollinations = `SUBJECTS[i]` + `, ` + `STYLE_SUFFIX`**

Changer de niche = modifier uniquement ce fichier (changer NICHE, STYLE_SUFFIX, SUBJECTS).

---

### [2] `generate_images_redbubble.py` — Génération

- Lit `prompts_redbubble.py`
- Pour chaque sujet × N_IMAGES_PER_SUBJECT : appelle `https://image.pollinations.ai/prompt/{prompt}?width={W}&height={H}&nologo=true`
- Sauvegarde dans `/images_raw/{niche}/{subject}_{index}.jpg`
- **Idempotent** : si le fichier existe déjà, skip (ne re-génère pas)
- Retry automatique (3 tentatives, délai exponentiel) si Pollinations timeout
- Log de progression dans la console GitHub Actions

---

### [3] `score_images_redbubble.py` — Notation via Gemini Vision

- Lit tous les fichiers de `/images_raw/{niche}/`
- Pour chaque image, appelle Gemini Vision (API gratuite, 1500 req/jour) avec ce prompt de scoring :

```
Rate this image for print-on-demand product design on a scale of 1-10.
Criteria:
- Clean white or very light background (mandatory for POD): /3
- Visual clarity and impact at small size: /3  
- Professional illustration quality: /2
- Originality / not generic: /2

Return JSON: {"score": X, "background_clean": true/false, "notes": "..."}
```

- Sauvegarde les scores dans `/scores/{niche}_scores.json`
- **Si le quota Gemini est atteint** : pause et reprend au prochain run (checkpoint dans le JSON)

---

### [4] `select_top.py` — Sélection

- Lit `/scores/{niche}_scores.json`
- Filtre : **exclure toutes les images où `background_clean == false`** (fond non blanc = inutilisable sur Redbubble sans post-traitement)
- Trie par score décroissant
- Copie les `TOP_K` meilleures images dans `/selected/{niche}/`
- Génère `/selected/{niche}/manifest.json` avec la liste des fichiers sélectionnés et leurs scores

---

### [5] `upscale_images.py` — Upscale (Real-ESRGAN via Hugging Face)

**C'est l'étape la plus critique côté quota — on n'upscale QUE ce qui est dans `/selected/`.**

- Lit `/selected/{niche}/manifest.json`
- Pour chaque image listée : appelle l'API Hugging Face Inference avec le modèle `Seyys/Real-ESRGAN` (ou `ai-forever/Real-ESRGAN` selon disponibilité)
- Sauvegarde le résultat dans `/output_redbubble/{niche}/{filename}_4x.png`
- **Checkpoint** : si une image est déjà dans `/output_redbubble/`, skip
- Si le quota HF est atteint dans la session, s'arrête proprement et log combien il reste à upscaler

Format de sortie : PNG, résolution ×4 (donc 1024px → 4096px).

**Secret GitHub requis** : `HF_TOKEN` (token Hugging Face gratuit)

---

### [6] Workflow GitHub Actions — `redbubble_pipeline.yml`

Déclenchement : **manuel uniquement** (`workflow_dispatch`) avec un paramètre `niche` pour choisir quel fichier de config charger.

```yaml
name: Redbubble Pipeline

on:
  workflow_dispatch:
    inputs:
      step:
        description: 'Étape à lancer'
        required: true
        default: 'all'
        type: choice
        options:
          - all          # Lance tout en séquence
          - generate     # Étape 2 seulement
          - score        # Étape 3 seulement
          - select       # Étape 4 seulement
          - upscale      # Étape 5 seulement (upscale uniquement les selected)
      niche:
        description: 'Nom de la niche (doit correspondre à NICHE dans prompts_redbubble.py)'
        required: true
        default: 'botanical_watercolor'
```

**Pourquoi les étapes séparées ?** Gemini Vision a 1500 req/jour. Si on génère 200 images, le scoring prend 2 runs. Le découpage permet de reprendre sans tout relancer.

**Secrets GitHub Actions nécessaires :**
- `GEMINI_API_KEY` (déjà présent si score_images.py existe)
- `HF_TOKEN` (Hugging Face, gratuit, à créer sur huggingface.co)

---

## Structure de dossiers finale

```
/
├── prompts_redbubble.py          ← config niche (à modifier)
├── generate_images_redbubble.py
├── score_images_redbubble.py
├── select_top.py
├── upscale_images.py
├── images_raw/
│   └── botanical_watercolor/     ← images brutes générées
├── scores/
│   └── botanical_watercolor_scores.json
├── selected/
│   └── botanical_watercolor/     ← top K images pré-upscale
│       └── manifest.json
├── output_redbubble/
│   └── botanical_watercolor/     ← images finales 4096px, prêtes upload
└── .github/workflows/
    └── redbubble_pipeline.yml
```

---

## Ce que ce pipeline ne fait PAS

- Il ne gère pas l'upload sur Redbubble (pas d'API publique). L'upload reste manuel depuis le navigateur mobile.
- Il ne génère pas les titres/tags pour les listings Redbubble (ça peut être un script Gemini séparé si besoin).
- Il ne resize pas au format exact de chaque produit Redbubble (poster vs t-shirt vs mug) — le recadrage se fait lors de l'upload sur Redbubble directement.

---

## Changer de niche

Pour passer de "botanical watercolor" à n'importe quelle autre niche (cottagecore, space art, anime chibi, typographie, etc.) :

1. Modifier `prompts_redbubble.py` — changer `NICHE`, `STYLE_SUFFIX`, `SUBJECTS`
2. Lancer le workflow avec le nouveau nom de niche
3. Tout le reste est automatique

**C'est le seul fichier à toucher pour changer complètement de produit.**
