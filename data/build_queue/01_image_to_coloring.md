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
    """
    src            : chemin image source (PNG ou JPEG)
    dst            : chemin de sortie PNG (si None, src stem + '_coloring.png' à côté)
    line_thickness : épaisseur de trait en pixels après binarisation (1-6)
    threshold      : seuil binarisation 0-255 (128 par défaut)
    invert_input   : inverser avant traitement (si image déjà dark-on-light)
    Retourne le Path du fichier écrit.
    """
```

## Algorithme (Pillow uniquement — PAS de cv2, PAS de scipy)
1. Ouvrir l'image, convertir en L (niveaux de gris)
2. Appliquer `ImageFilter.SMOOTH` (réduire le bruit FLUX)
3. Appliquer `ImageFilter.FIND_EDGES` (détection de contours)
4. Inverser (`ImageOps.invert`) → contours noirs sur blanc
5. Appliquer `ImageFilter.MaxFilter(line_thickness * 2 + 1)` pour épaissir les traits
   (note : MaxFilter sur image inversée épaissit les zones noires)
   → utiliser MinFilter sur l'image NON-inversée puis ré-inverser est plus propre :
   - avant inversion : FIND_EDGES donne trait clair sur fond sombre
   - MinFilter(size) épaissit les contours (réduit les zones claires)
   - puis inverser → trait noir épais sur blanc
6. Binariser : `point(lambda p: 0 if p < threshold else 255)` → mode '1' puis 'L'
7. Forcer fond=255 (blanc), traits=0 (noir) — vérifier histogram et inverser si besoin
8. Convertir en RGB, sauvegarder en PNG (qualité max)

## Contraintes importantes
- Dépendances : **Pillow uniquement** (pas de numpy, pas de cv2)
- Entrée : PNG ou JPEG, toute taille
- Sortie : PNG RGB 8-bit, blanc pur (255,255,255), noir pur (0,0,0)
- Idempotent : si dst existe déjà, écraser (ne pas lever d'exception)
- Robuste : si l'image d'entrée est déjà noir/blanc, ne pas planter

## CLI (usage direct)
```
python scripts/lib/image_to_coloring.py src.png [dst.png] [--thickness 2] [--threshold 128]
```
Bloc `if __name__ == "__main__":` avec argparse.

## Tests intégrés (dans le bloc __main__)
Si appelé sans argument : créer une image de test synthétique (rectangle rouge
sur fond vert) et vérifier que la sortie est bien B&W. Afficher "OK" si réussi.
