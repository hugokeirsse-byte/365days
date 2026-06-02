"""
Télécharge les SVGs CC0 directement dans scripts/tpt/themes/.
Lancé automatiquement par la GitHub Action "Download CC0 Assets".

Usage local :
  python scripts/tpt/download_assets.py
  python scripts/tpt/download_assets.py halloween    # un seul thème
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

THEMES_DIR = Path(__file__).parent / "themes"

# Sources CC0 confirmées avec URLs alternatives pour chaque asset
ASSETS = [
    {
        "filename": "halloween_pumpkin.svg",
        "name":     "Halloween Pumpkin",
        "urls": [
            "https://freesvg.org/img/carved-pumpkin-coloring-vector-drawing.svg",
            "https://openclipart.org/download/301089/carved-pumpkin.svg",
            "https://upload.wikimedia.org/wikipedia/commons/e/e3/Jack-o'-lantern.svg",
        ],
    },
    {
        "filename": "apple.svg",
        "name":     "Apple (Back to School)",
        "urls": [
            "https://freesvg.org/img/apple-outline.svg",
            "https://openclipart.org/download/181651/apple.svg",
            "https://upload.wikimedia.org/wikipedia/commons/1/15/Red_Apple.svg",
        ],
    },
    {
        "filename": "christmas_tree.svg",
        "name":     "Christmas Tree",
        "urls": [
            "https://freesvg.org/img/christmas-tree-drawing.svg",
            "https://openclipart.org/download/233730/drawing-christmas-tree.svg",
            "https://upload.wikimedia.org/wikipedia/commons/3/37/Christmas_tree.svg",
        ],
    },
    {
        "filename": "valentine_heart.svg",
        "name":     "Valentine Heart",
        "urls": [
            "https://freesvg.org/img/heart-outline.svg",
            "https://openclipart.org/download/219791/heart-outline.svg",
            "https://upload.wikimedia.org/wikipedia/commons/f/f1/Heart_coraz%C3%B3n.svg",
        ],
    },
    {
        "filename": "snowman.svg",
        "name":     "Snowman",
        "urls": [
            "https://freesvg.org/img/snowman-vector-clip-art-graphics.svg",
            "https://openclipart.org/download/233966/drawing-snowman.svg",
        ],
    },
    {
        "filename": "turkey.svg",
        "name":     "Thanksgiving Turkey",
        "urls": [
            "https://freesvg.org/img/1543187054.svg",
            "https://openclipart.org/download/173661/turkey.svg",
        ],
    },
    {
        "filename": "bunny.svg",
        "name":     "Easter Bunny",
        "urls": [
            "https://openclipart.org/download/213759/bunny-outline.svg",
            "https://freesvg.org/img/cute-bunny-outline.svg",
        ],
    },
    {
        "filename": "butterfly.svg",
        "name":     "Spring Butterfly",
        "urls": [
            "https://openclipart.org/download/195905/coloring-book-butterfly.svg",
            "https://freesvg.org/img/1195905.svg",
        ],
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "image/svg+xml,*/*",
}


def download_one(asset: dict) -> bool:
    dst = THEMES_DIR / asset["filename"]
    if dst.exists():
        print(f"  ✓ déjà présent : {asset['filename']}")
        return True

    for url in asset["urls"]:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            # Vérification minimale : doit ressembler à du SVG
            if b"<svg" not in data[:500] and b"<?xml" not in data[:100]:
                print(f"  ✗ pas un SVG valide depuis {url}")
                continue
            dst.write_bytes(data)
            print(f"  ✓ {asset['filename']} ({len(data)//1024}ko) ← {url}")
            return True
        except Exception as exc:
            print(f"  ✗ {url} → {exc}")

    print(f"  ✗ ÉCHEC : {asset['name']} — toutes les sources ont échoué")
    print(f"    Télécharge manuellement depuis ASSETS_CC0.md → {asset['filename']}")
    return False


def main():
    THEMES_DIR.mkdir(parents=True, exist_ok=True)
    filter_name = sys.argv[1].lower() if len(sys.argv) > 1 else None

    assets = [a for a in ASSETS
              if not filter_name or filter_name in a["filename"]]

    print(f"Téléchargement de {len(assets)} asset(s) CC0 → {THEMES_DIR}\n")
    ok, fail = 0, 0
    for asset in assets:
        if download_one(asset):
            ok += 1
        else:
            fail += 1

    print(f"\n{'='*40}")
    print(f"✓ {ok} téléchargés  |  ✗ {fail} échoués")
    if fail:
        print("Pour les échoués : ouvre ASSETS_CC0.md pour les liens manuels.")
    return fail


if __name__ == "__main__":
    sys.exit(main())
