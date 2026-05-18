# 🎨 REFERENCE IMAGES — guide de dépôt

Dépose ici les images que tu as générées manuellement via :
- **Bing Image Creator** (bing.com/create — DALL-E 3 gratuit illimité avec compte Microsoft)
- **ChatGPT 4o** (interface web ChatGPT)
- **Microsoft Designer**
- N'importe quel générateur de qualité

Mes pipelines les utiliseront automatiquement comme **référence stylistique**
via Hugging Face IP-Adapter (dès que tu auras configuré `HF_API_KEY` en
secret GitHub).

## Structure attendue

```
reference_images/
├── specs/
│   ├── box_cover.png
│   ├── trait_style.png
│   └── target_style.png
├── iheart/
│   ├── fishing.png       # référence parfaite pour ce style
│   ├── my_cat.png
│   └── default.png       # fallback générique
├── coloring/
│   ├── mushroom_page_sample.png
│   └── creature_page_sample.png
└── viral_formats/
    └── medical_card_style.png
```

## Convention de nommage

`<pipeline_name>/<niche>.png` → utilisé automatiquement pour les designs
de cette niche dans ce pipeline.

`<pipeline_name>/default.png` → fallback si pas de référence dédiée.

## Workflow recommandé

1. Tu génères 3-5 versions parfaites d'un design via Bing Image Creator
2. Tu choisis la meilleure
3. Tu la nommes selon la convention ci-dessus
4. Tu la commit dans `assets/reference_images/<pipeline>/<niche>.png`
5. Le pipeline correspondant l'utilisera comme référence pour produire 50+
   variations dans CE style (via HF IP-Adapter)

## Format

- PNG ou JPG
- 1024×1024 ou plus (sera redimensionné si nécessaire)
- Pas de watermark (Bing en met parfois — crop avant de commit)
- Style cohérent avec ce que tu veux pour le pipeline

## Note

Tant que `HF_API_KEY` n'est pas configuré, ce dossier n'est pas utilisé.
Les pipelines tournent en mode Pollinations standard.
