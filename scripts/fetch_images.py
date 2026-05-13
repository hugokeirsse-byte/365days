"""
Télécharge les illustrations botaniques Wikimedia listées dans Data.py.

- Déduplique par URL (302 images uniques sur 365 entrées).
- Reconstruit l'URL Wikimedia depuis le nom de fichier : sur Commons, le
  chemin /X/XX/ est le MD5 du nom de fichier. Les URLs hardcodées dans
  Data.py utilisent des hashes erronés (404 sauf coup de chance) — on
  les ignore et on recalcule.
- Idempotent : ignore les fichiers déjà présents (relance possible).
- Respecte la User-Agent policy Wikimedia + délai entre requêtes.
- Nomme les fichiers d'après le nom latin normalisé.
- Commit intermédiaire toutes les COMMIT_EVERY images réussies : si le runner
  GitHub Actions atteint son timeout, l'avancée est préservée et la relance
  reprend où on s'est arrêté.
"""

import hashlib
import os
import re
import subprocess
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
DELAY_SECONDS = 0.5
TIMEOUT_SECONDS = 60
MAX_RETRIES = 2
RETRY_BACKOFF = [2, 5]  # secondes
COMMIT_EVERY = 30


def normalize_latin(latin: str) -> str:
    slug = latin.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def canonical_wikimedia_url(original_url: str) -> str:
    """Reconstruit l'URL Wikimedia avec le bon hash MD5.

    Les URLs Data.py ont la forme
        https://upload.wikimedia.org/wikipedia/commons/X/XX/<filename>
    où <filename> est le nom de fichier réel sur Commons (ex. avec en-dash
    'Köhler–s'). Le hash /X/XX/ est calculé sur le filename underscored.
    """
    encoded_filename = original_url.rsplit("/", 1)[-1]
    filename_underscored = urllib.parse.unquote(encoded_filename).replace(" ", "_")
    md5 = hashlib.md5(filename_underscored.encode("utf-8")).hexdigest()
    quoted = urllib.parse.quote(filename_underscored, safe="")
    return (
        f"https://upload.wikimedia.org/wikipedia/commons/"
        f"{md5[0]}/{md5[:2]}/{quoted}"
    )


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


def git_checkpoint(batch_index: int, batch_total: int) -> None:
    """Commit et push l'avancée actuelle. Silencieux hors CI."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    branch = os.environ.get("GITHUB_REF_NAME", "")
    try:
        subprocess.run(["git", "add", "images/"], check=True, cwd=ROOT)
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], cwd=ROOT
        ).returncode
        if diff == 0:
            return  # rien à commiter
        msg = f"Checkpoint {batch_index}/{batch_total} ({COMMIT_EVERY} images)"
        subprocess.run(["git", "commit", "-m", msg], check=True, cwd=ROOT)
        if branch:
            subprocess.run(
                ["git", "push", "origin", f"HEAD:{branch}"], check=True, cwd=ROOT
            )
        print(f"  → checkpoint committed: {msg}")
    except subprocess.CalledProcessError as exc:
        print(f"  ! checkpoint failed: {exc}")


def main() -> int:
    os.makedirs(IMAGES_DIR, exist_ok=True)
    unique = unique_by_url(PLANTS)
    print(f"Entrées totales : {len(PLANTS)}")
    print(f"URLs uniques    : {len(unique)}")

    downloaded = skipped = failed = 0
    failures = []
    since_last_commit = 0

    for i, plant in enumerate(unique, 1):
        latin = plant["latin"]
        url = canonical_wikimedia_url(plant["image_url"])
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
            since_last_commit += 1
            print(f"                  ✓ {info}")
            if since_last_commit >= COMMIT_EVERY:
                git_checkpoint(downloaded // COMMIT_EVERY, len(unique) // COMMIT_EVERY)
                since_last_commit = 0
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

    if downloaded == 0 and skipped == 0:
        print("Aucune image téléchargée et aucune existante : échec total.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
