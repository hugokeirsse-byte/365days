TARGET: scripts/agent_domain_image_finder.py

## Role
Telecharge des images libre de droits (domaine public / CC0) depuis Wikimedia Commons
pour alimenter le pipeline de livres de coloriage sans IA generative.

## Fonction principale
```python
def find_and_download(
    theme: str,             # ex : "botanical flowers vintage", "Art Nouveau animals"
    out_dir: str | Path,    # dossier de sortie
    max_images: int = 20,   # max a telecharger
    min_width_px: int = 800, # filtre qualite
) -> list[dict]:            # liste {path, title, author, license, url}
```

## Source : Wikimedia Commons API
URL : https://commons.wikimedia.org/w/api.php

### Etape 1 : Recherche
POST/GET avec params :
```
action=query&list=search&srsearch=<theme>&srnamespace=6&srlimit=50&format=json
```
Renvoie liste de pageids.

### Etape 2 : Info image (pour chaque pageid)
```
action=query&pageids=<id>&prop=imageinfo&iiprop=url|size|extmetadata&format=json
```
Filtres :
- iiprop size : largeur >= min_width_px
- extmetadata LicenseShortName contient "CC0", "Public Domain", "CC-BY" ou "CC-BY-SA"
- format : jpg ou png uniquement

### Etape 3 : Telecharger
`urllib.request.urlopen(image_url)` -> sauvegarder en PNG/JPG dans out_dir.
Nommer : `<theme_slug>_<index:03d>.jpg`

## Metadonnees
Pour chaque image, ecrire `<nom>.json` avec :
```json
{"title": "...", "author": "...", "license": "...", "source_url": "...",
 "width": ..., "height": ..., "local_path": "..."}
```

## Contraintes
- Dependances : stdlib uniquement (urllib, json, pathlib)
- Robuste : si une image echoue, continuer avec la suivante
- Idempotent : si l'image existe deja (meme nom), sauter
- User-Agent : "365days-ImageFinder/1.0 (hugo.keirsse@gmail.com)"
- Timeout : 30s par image
- Pas de numpy, pas de Pillow (ce module telecharge seulement)

## CLI
```
python scripts/agent_domain_image_finder.py "botanical vintage" --out data/public_domain/botanical --max 20
```
Argparse avec --out, --max, --min-width.

## Affichage
Ecrire une ligne par image : OK/SKIP/FAIL + titre + licence.
Afficher en fin : "X images telecharge, Y sautees, Z echecs"
