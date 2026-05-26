TARGET: scripts/agent_publisher.py

## Rôle
Étape post-GATE 2 : prépare le paquet de publication pour KDP et Etsy.
Lit le brief approuvé + kdp_package.json + interior.pdf et génère
tous les fichiers nécessaires pour la soumission KDP + une fiche Etsy.

## Variables d'environnement
- `BRIEF_ID` : identifiant du brief
- `GEMINI_API_KEY` : pour rédiger la description Etsy et le blurb KDP
- `GEMINI_MODEL` : modèle Gemini (défaut gemini-2.5-flash)

## Fichiers lus
- `data/briefs/<BRIEF_ID>.json`
- `products/coloring_books/_gate1/<BRIEF_ID>/kdp_package.json`
- `products/coloring_books/_gate1/<BRIEF_ID>/interior.pdf`
- `products/coloring_books/_gate1/<BRIEF_ID>/pages/cover_front.png`

## Fichiers écrits
`products/coloring_books/_gate1/<BRIEF_ID>/publication/`
- `kdp_metadata.json`
  ```json
  {
    "title": "...",
    "subtitle": "...",
    "author": "...",
    "description": "...(blurb 150-200 mots, généré par Gemini)...",
    "keywords": ["...", "...", "...", "...", "...", "...", "..."],
    "categories": ["...", "..."],
    "price_usd": 8.99,
    "price_eur": 8.99,
    "language": "en",
    "pages": 30,
    "trim_size": "8.5x11",
    "paper": "black_and_white",
    "interior_pdf": "products/coloring_books/_gate1/<id>/interior.pdf",
    "cover_image": "products/coloring_books/_gate1/<id>/pages/cover_front.png"
  }
  ```
- `etsy_listing.json`
  ```json
  {
    "title": "...(max 140 chars, keywords-first)...",
    "description": "...(500-800 mots Etsy-optimisé, généré par Gemini)...",
    "tags": ["...", "...", "...", "...", "...", "...", "...", "...", "...", "...", "...", "...", "..."],
    "price": 4.99,
    "digital_download": true,
    "files_to_attach": ["interior.pdf"]
  }
  ```
- `PUBLICATION_READY.md` : résumé lisible par Hugo avec toutes les infos + checklist KDP

## Algorithme
1. Vérifier que `gate_end == "approved"` dans le brief (ou que kdp_package.json existe avec `ready_for_gate2: true`)
2. Appeler Gemini pour générer :
   a. Blurb KDP (150-200 mots, en anglais, axé bénéfices client)
   b. Description Etsy (500-800 mots, SEO-optimisée, en anglais)
   c. 13 tags Etsy (max 20 chars chacun, séparés par virgule)
   d. 7 mots-clés KDP (max 50 chars chacun)
3. Remplir les JSON avec les métadonnées du brief (titre, auteur, format, etc.)
4. Écrire PUBLICATION_READY.md avec :
   - Titre, auteur, format
   - Lien vers interior.pdf
   - Lien vers cover_front.png
   - Blurb KDP
   - Checklist KDP : [ ] Upload interior.pdf [ ] Upload cover [ ] Set price [ ] Set keywords [ ] Publish
   - Listing Etsy : titre + description + prix
5. Afficher "PRÊT POUR PUBLICATION : voir PUBLICATION_READY.md"

## Mode fallback (sans Gemini)
Utiliser des templates statiques avec les variables du brief (titre, auteur, etc.)
Ne jamais planter — sortir un fichier même incomplet.

## Dépendances
- stdlib + urllib (appel Gemini)
- Aucune dépendance externe requise

## CLI
```
python scripts/agent_publisher.py [BRIEF_ID]
```
