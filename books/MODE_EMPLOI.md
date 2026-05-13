# Mode d'emploi — Production industrielle Mirabilia Éditions

> Ce dossier permet de produire un livre « 365 » en sollicitant Claude (moi) **uniquement pour la mise en page**.
> La rédaction est déléguée à Gemini / ChatGPT via les prompts fournis.

---

## Arborescence

```
books/
├── schema.json              ← Schéma JSON officiel d'une fiche (référence)
├── prompts/
│   ├── 00_index_alphabetique.md   ← Re-numérotation finale par ordre alphabétique
│   ├── 01_fiche_plante.md         ← Rédaction des 13 rubriques d'une plante
│   └── 02_legende_kohler.md       ← Traduction de la légende botanique
└── 365_medicinal_plants/
    └── plants.json          ← Le livre, pré-rempli (302 entrées id+nom+URL),
                               rubriques à compléter par les IA externes
```

---

## Flux de production (par plante)

1. **Tu copies le prompt** `prompts/01_fiche_plante.md` dans Gemini ou ChatGPT.
2. **Tu remplaces** le bloc `ENTRÉE À RÉDIGER` par les valeurs de la plante (tu les trouves dans `plants.json`).
3. **L'IA renvoie un JSON** complet. Tu colles ce JSON dans `plants.json` à la place de l'entrée vide correspondante (même `id`).
4. Pour la légende : prompt `02_legende_kohler.md`, idem. Tu colles le tableau dans le champ `legend`.
5. **Push sur la branche.** Le workflow GitHub déclenche automatiquement la mise en page (côté Claude).

## Flux de production (en lot)

Pour aller plus vite, demande aux IA externes 10 fiches à la fois (passe-leur 10 entrées en une fois). Elles renvoient un tableau JSON, tu fusionnes dans `plants.json`.

---

## Ce que je (Claude) prends en charge

- Téléchargement automatique des illustrations Wikimedia (workflow `fetch_images.yml`).
- Génération des pages PNG (2400×2400 px, 300 DPI) dès qu'une entrée est complète.
- Assemblage du PDF final aux normes KDP.
- Création de la couverture finale aux dimensions KDP exactes.
- Génération de l'index alphabétique et de la matrice systèmes corporels × régions.

## Ce que tu fournis une seule fois par livre

- **Maquette de page type** (image ou PSD/PDF) → définit la mise en page.
- **Logo Mirabilia Éditions** (PNG transparent haute résolution).
- **Modèle de couverture** (recto + verso ou full wrap).
- **Décision finale** sur les ~63 entrées doublons : à compléter par d'autres plantes ou à supprimer.

---

## Réutilisation pour les livres suivants de la collection « 365 »

La structure est volontairement générique. Pour un nouveau livre :
1. Duplique le dossier `365_medicinal_plants/` → `365_<nouveau_theme>/`.
2. Adapte le prompt `01_fiche_plante.md` au thème (champs spécifiques).
3. Le schéma reste identique → les outils de mise en page sont réutilisés tels quels.
