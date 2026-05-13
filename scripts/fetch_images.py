"""
Télécharge les illustrations botaniques Wikimedia listées dans Data.py.

- Déduplique par URL (302 images uniques sur 365 entrées).
- Idempotent : ignore les fichiers déjà présents.
- Respecte la User-Agent policy Wikimedia + délai 1 s entre requêtes.
- Nomme les fichiers d'après le nom latin normalisé.
"""

import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from Data import PLANTS  # noqa: E402

IMAGES_DIR = os.path.join(ROOT, "images")
USER_AGENT = (
    "MirabiliaEditions-365MedicinalPlants/1.0 "
    "(https://github.com/hugokeirsse-byte/365days; contact via GitHub)"
)
DELAY_SECONDS = 1.0
TIMEOUT_SECONDS = 60
MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 15]  # secondes


def normalize_latin(latin: str) -> str:
    slug = latin.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def unique_by_url(plants):
    seen = {}
    for p in plants:
        url = p["image_url"]
        if url not in seen:
            seen[url] = p
    return list(seen.values())


def download(url: str, dest: str) -> tuple[bool, str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "image/jpeg,image/*"},
    )
    last_err = ""
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                data = resp.read()
            with open(dest, "wb") as f:
                f.write(data)
            return True, f"{len(data) // 1024} KB"
        except Exception as exc:  # noqa: BLE001
            last_err = f"{type(exc).__name__}: {exc}"
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF[attempt])
    return False, last_err


def main() -> int:
    os.makedirs(IMAGES_DIR, exist_ok=True)
    unique = unique_by_url(PLANTS)
    print(f"Entrées totales : {len(PLANTS)}")
    print(f"URLs uniques    : {len(unique)}")

    downloaded = skipped = failed = 0
    failures = []

    for i, plant in enumerate(unique, 1):
        latin = plant["latin"]
        url = plant["image_url"]
        filename = f"{normalize_latin(latin)}.jpg"
        dest = os.path.join(IMAGES_DIR, filename)

        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            skipped += 1
            print(f"[{i:>3}/{len(unique)}] SKIP  {filename}")
            continue

        decoded = urllib.parse.unquote(url)
        print(f"[{i:>3}/{len(unique)}] GET   {filename}  ← {decoded[-70:]}")
        ok, info = download(url, dest)
        if ok:
            downloaded += 1
            print(f"                  ✓ {info}")
        else:
            failed += 1
            failures.append((latin, url, info))
            print(f"                  ✗ {info}")

        time.sleep(DELAY_SECONDS)

    print()
    print("=" * 60)
    print(f"Téléchargées : {downloaded}")
    print(f"Ignorées     : {skipped}")
    print(f"Échecs       : {failed}")

    if failures:
        log_path = os.path.join(ROOT, "fetch_failures.log")
        with open(log_path, "w") as f:
            for latin, url, info in failures:
                f.write(f"{latin}\t{url}\t{info}\n")
        print(f"Log des échecs : {log_path}")

    # Succès partiel acceptable : on commit ce qui est téléchargé.
    # On n'échoue que si rien du tout n'a pu être récupéré.
    if downloaded == 0 and skipped == 0:
        print("Aucune image téléchargée et aucune existante : échec total.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
