TARGET: scripts/lib/image_to_coloring.py

## Rôle
Convertit une image couleur ou niveaux de gris (sortie FLUX schnell)
en line-art coloriage : fond blanc pur, contours noirs épais, fermés,
prêts à colorier. Aucune couleur, aucun gris résiduel.

## Fonction publique principale
```python
def convert(
    src: str | Path,
    dst: str | Path | None = None,
    *,
    line_thickness: int = 2,
    threshold: int = 128,
    invert_input: bool = False,
) -> Path:
```

## Algorithme (Pillow uniquement — PAS de cv2, PAS de scipy)
1. Ouvrir l'image, convertir en L (niveaux de gris)
2. Appliquer `ImageFilter.SMOOTH` (réduire le bruit FLUX)
3. Appliquer `ImageFilter.FIND_EDGES` (détection de contours)
4. MinFilter(size) épaissit les contours, puis inverser → trait noir épais sur blanc
5. Binariser : `point(lambda p: 0 if p < threshold else 255)`
6. Forcer fond=255 (blanc), traits=0 (noir)
7. Convertir en RGB, sauvegarder en PNG

## Contraintes
- Dépendances : **Pillow uniquement** (pas de numpy, pas de cv2)
- Entrée : PNG ou JPEG, toute taille
- Sortie : PNG RGB 8-bit, blanc pur, noir pur
- Idempotent, robuste

## CLI
```
python scripts/lib/image_to_coloring.py src.png [dst.png] [--thickness 2] [--threshold 128]
```

## Test intégré
Si appelé sans argument : créer image test synthétique (rectangle rouge sur fond vert),
vérifier sortie B&W. Afficher "OK" si réussi.
