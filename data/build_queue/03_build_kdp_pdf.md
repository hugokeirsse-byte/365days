TARGET: scripts/build_kdp_pdf.py

## Rôle
Assemble le PDF intérieur KDP-ready à partir des pages line-art générées.
Lit le brief pour les métadonnées de format. Produit un PDF
B&W 300 DPI au format 8.5×11 pouces avec bleed.

## Variables d'environnement
- `BRIEF_ID` : identifiant du brief
- `DPI` : résolution cible (défaut `300`)

## Fichiers lus
- `data/briefs/<BRIEF_ID>.json` (pour format.trim, format.bleed, format.pages_interior)
- `products/coloring_books/_gate1/<BRIEF_ID>/pages/page_001.png` … `page_NNN.png`
- `products/coloring_books/_gate1/<BRIEF_ID>/generation_report.json` (pour savoir quelles pages sont ok)

## Fichiers écrits
- `products/coloring_books/_gate1/<BRIEF_ID>/interior.pdf`
  - PDF standard (pas nécessairement PDF/X-1a, mais A&B compatible KDP)
  - Taille page : (8.5 + 2×0.125) × (11 + 2×0.125) pouces = 8.75 × 11.25 pouces
  - Chaque page = une image PNG centrée, fond blanc, 300 DPI
  - B&W : convertir chaque image en L (grayscale) avant insertion
- `products/coloring_books/_gate1/<BRIEF_ID>/kdp_package.json`
  ```json
  {
    "brief_id": "...",
    "built_at": "ISO8601",
    "interior_pdf": "...",
    "page_count": 30,
    "format": "8.5x11in",
    "bleed": "0.125in",
    "dpi": 300,
    "ready_for_gate2": true
  }
  ```

## Algorithme
1. Charger brief → lire trim size, bleed, pages_interior
2. Calculer taille canvas avec bleed (en points ReportLab = 1/72 inch)
   - page_w = (8.5 + 2*0.125) * 72  ≈  630 pt
   - page_h = (11 + 2*0.125) * 72   ≈  810 pt
3. Charger generation_report.json → liste des pages "ok" ou "skipped" (avec chemin)
4. Trier les pages par page_number
5. Créer le PDF avec reportlab :
   - `canvas.Canvas(output_path, pagesize=(page_w, page_h))`
   - Pour chaque page :
     a. Ouvrir l'image avec Pillow
     b. Convertir en L (grayscale) → convertir en RGB pour ReportLab (ImageReader attend RGB ou L)
     c. Redimensionner pour tenir dans le canvas (garder ratio, centrer)
     d. Fond blanc, dessiner l'image centrée
     e. `c.showPage()`
6. `c.save()`
7. Écrire kdp_package.json
8. Afficher : "PDF intérieur : interior.pdf (30 pages, 8.75×11.25in, B&W)"

## Comportement si pages manquantes
- Si moins de `pages_interior` pages sont disponibles : inclure ce qui est disponible,
  logguer un warning, mettre `ready_for_gate2: false` dans kdp_package.json.
- Ne jamais planter sur une image manquante : l'ignorer et continuer.

## Dépendances
- Pillow
- reportlab (`pip install reportlab`)
- stdlib

## CLI
```
python scripts/build_kdp_pdf.py [BRIEF_ID]
```
Si BRIEF_ID passé en argv[1], l'utiliser (sinon lire env var BRIEF_ID).
