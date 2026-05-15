# 365days — Édition multi-marques

Repo unique qui héberge **3 marques d'auto-édition Amazon KDP** opérées par Hugo Keirsse, chacune avec ses livres, sa charte visuelle et son public.

## Les 3 marques

| Marque | Pilier | Format | Marché cible |
|---|---|---|---|
| **Mirabilia Éditions** | Premium / savant | 365 par an, beau livre relié | Beau cadeau, lecteur curieux |
| **Inkwell & Hush** | Coloriage IA volumique | 100 illustrations par thème | Coloriage adulte, méditation, cadeau |
| **Daystone Press** | Low-content intelligent | Journaux, planners, trackers thématiques | Productivité, lifestyle, journaling |

## Structure du repo

```
365days/
├── .github/workflows/   # robots GitHub Actions (génériques, multi-marques)
├── scripts/             # robots Python (généricisés)
├── .triggers/           # fichiers sentinelles pour déclenchements automatiques
├── _shared/             # ressources transverses par marque
│   ├── mirabilia/       (logo, charte, template couverture)
│   ├── inkwell_hush/
│   └── daystone_press/
├── books/               # production des livres
│   ├── mirabilia/
│   │   └── 01_chess_puzzles/
│   ├── inkwell_hush/
│   │   └── 01_floral_mandalas/
│   └── daystone_press/
│       └── (premier livre TBD)
└── README.md            # ce fichier
```

## En production actuelle

- **Mirabilia · Vol I — 365 Days of Chess Puzzles** *(en démarrage)*
- **Inkwell & Hush · Vol I — Floral Mandalas, 100 pages** *(en démarrage)*
- **Daystone Press · Vol I — TBD** *(à définir)*

## Pipeline technique

Tous les livres bénéficient des mêmes robots GitHub Actions :
1. **Generate AI images** → Pollinations.ai (Flux) pour illustrations
2. **Score images** → Gemini Vision pour pré-notation qualité
3. **Upscale images** → Real-ESRGAN ×4 pour qualité impression
4. **Cover generator** → Pillow pour couvertures KDP (à venir)
5. **Layout generator** → mise en page automatique (à venir)

Les workflows sont déclenchables manuellement depuis l'app GitHub mobile, ou via push d'un fichier sentinelle dans `.triggers/`.
