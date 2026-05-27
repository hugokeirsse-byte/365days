TARGET: scripts/build_kdp_pdf.py

## Rôle
Assemble le PDF intérieur KDP-ready à partir des pages line-art.
Lit le brief pour les métadonnées de format.

## Variables d'environnement
- BRIEF_ID : identifiant du brief
- DPI : résolution cible (défaut 300)

## Fichiers lus
- data/briefs/<BRIEF_ID>.json (format.trim, format.bleed, format.pages_interior)
- products/coloring_books/_gate1/<BRIEF_ID>/pages/page_001.png ... page_NNN.png
- products/coloring_books/_gate1/<BRIEF_ID>/generation_report.json

## Fichiers écrits
- products/coloring_books/_gate1/<BRIEF_ID>/interior.pdf
  - Taille page : (8.5 + 2*0.125) * 72 × (11 + 2*0.125) * 72 points = 630×810 pt
  - Chaque page = image PNG centrée, fond blanc, B&W (convertir en L)
- products/coloring_books/_gate1/<BRIEF_ID>/kdp_package.json
  {"built_at": "ISO8601", "page_count": 30, "format": "8.5x11in", "bleed": "0.125in", "ready_for_gate2": true}

## Algorithme
1. Charger brief → trim, bleed, pages_interior
2. page_w = (8.5 + 2*0.125) * 72, page_h = (11 + 2*0.125) * 72
3. Charger generation_report.json → pages ok/skipped triées par index
4. canvas.Canvas(output, pagesize=(page_w, page_h))
5. Pour chaque page : ouvrir PNG, convertir L→RGB, redimensionner centré, showPage()
6. c.save() → écrire kdp_package.json
7. Si pages manquantes : ready_for_gate2=false, warning

## Dépendances
- Pillow, reportlab
- stdlib

## CLI
```
python scripts/build_kdp_pdf.py [BRIEF_ID]
```
