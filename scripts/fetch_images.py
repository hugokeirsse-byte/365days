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
import json
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


def canonical_wikimedia_url(filename_underscored: str) -> str:
    """Construit l'URL Wikimedia canonique pour un nom de fichier donné.

    Sur Commons, le chemin /X/XX/ est le MD5 du nom de fichier underscored.
    """
    md5 = hashlib.md5(filename_underscored.encode("utf-8")).hexdigest()
    quoted = urllib.parse.quote(filename_underscored, safe="")
    return (
        f"https://upload.wikimedia.org/wikipedia/commons/"
        f"{md5[0]}/{md5[:2]}/{quoted}"
    )


def url_variants(original_url: str):
    """Yield les URLs Wikimedia à essayer pour cette entrée Data.py.

    Data.py contient des URLs avec des hashes /X/XX/ presque tous erronés
    et un nom de fichier qui utilise l'en-dash (Köhler–s). En réalité, la
    plupart des fichiers Wikimedia Köhler portent l'apostrophe (Köhler's).
    On essaie les deux orthographes, recalculées via MD5.
    """
    encoded_filename = original_url.rsplit("/", 1)[-1]
    base = urllib.parse.unquote(encoded_filename).replace(" ", "_")

    seen = set()
    # 1. Apostrophe ASCII (la plus courante sur Commons)
    apos = base.replace("Köhler–s", "Köhler's").replace("Köhler–s", "Köhler's")
    if apos not in seen:
        seen.add(apos)
        yield canonical_wikimedia_url(apos)
    # 2. En-dash (cas Taraxacum, fichiers historiques)
    if base not in seen:
        seen.add(base)
        yield canonical_wikimedia_url(base)
    # 3. Sans apostrophe ni dash (cas marginal)
    plain = base.replace("Köhler–s", "Köhlers").replace("Köhler–s", "Köhlers")
    if plain not in seen:
        seen.add(plain)
        yield canonical_wikimedia_url(plain)


def unique_by_url(plants):
    seen = {}
    for p in plants:
        url = p["image_url"]
        if url not in seen:
            seen[url] = p
    return list(seen.values())


def url_exists(url: str) -> bool:
    """HEAD request rapide pour vérifier qu'une URL Wikimedia répond 200."""
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except Exception:  # noqa: BLE001
        return False


# ─────────────────────────────────────────────────────────────────────
# API Commons : index global des fichiers Köhler
# ─────────────────────────────────────────────────────────────────────
KOHLER_CATEGORIES = [
    "Category:Köhler's_Medizinal-Pflanzen",
    "Category:Köhler's_Medizinal-Pflanzen_(Atlas)",
]
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
_KOHLER_INDEX = None  # cache global


def fetch_kohler_index() -> dict:
    """Récupère via l'API Commons l'index des fichiers Köhler.

    Une requête de catégorie suffit (≤500 fichiers). On retourne un
    dict {nom_latin_normalisé: [liste de filenames]}.
    """
    global _KOHLER_INDEX
    if _KOHLER_INDEX is not None:
        return _KOHLER_INDEX

    all_files: list[str] = []
    for category in KOHLER_CATEGORIES:
        cmcontinue = None
        while True:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": category,
                "cmtype": "file",
                "cmlimit": "500",
                "format": "json",
            }
            if cmcontinue:
                params["cmcontinue"] = cmcontinue
            url = COMMONS_API + "?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except Exception as exc:  # noqa: BLE001
                print(f"  ! API Commons {category}: {type(exc).__name__}: {exc}")
                break
            for m in data.get("query", {}).get("categorymembers", []):
                all_files.append(m["title"])
            cmcontinue = data.get("continue", {}).get("cmcontinue")
            if not cmcontinue:
                break

    index: dict[str, list[str]] = {}
    for fn in all_files:
        title = fn.replace("File:", "")
        base = title.rsplit(".", 1)[0]
        parts = base.split(" - ", 1)
        if len(parts) < 2:
            continue
        latin = parts[0].strip().lower()
        index.setdefault(latin, []).append(title)

    print(f"Index Köhler API Commons : {len(index)} plantes, {len(all_files)} fichiers")
    _KOHLER_INDEX = index
    return index


def find_kohler_url(latin_name: str) -> str | None:
    """Cherche dans l'index Köhler une URL pour cette plante."""
    index = fetch_kohler_index()
    norm = latin_name.strip().lower()
    # match exact
    if norm in index:
        return canonical_wikimedia_url(index[norm][0].replace(" ", "_"))
    # match préfixe (cas synonymes : "Cinnamomum verum" → "Cinnamomum zeylanicum")
    genus = norm.split()[0] if norm else ""
    for latin_key, files in index.items():
        if latin_key.startswith(genus + " ") and len(files) > 0:
            return canonical_wikimedia_url(files[0].replace(" ", "_"))
    return None


def search_commons(latin_name: str) -> str | None:
    """Recherche par plante via l'API search de Commons (fallback robuste).

    Plus lent (1 requête HTTP par plante manquante) mais ne dépend pas
    du nom exact de catégorie. Trouve les fichiers Köhler quelle que soit
    la typographie réelle sur Commons.
    """
    params = {
        "action": "query",
        "list": "search",
        "srnamespace": "6",  # File:
        "srsearch": f'"{latin_name}" Köhler Medizinal',
        "srlimit": "3",
        "format": "json",
    }
    url = COMMONS_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None
    for item in data.get("query", {}).get("search", []):
        title = item.get("title", "")
        if not title.startswith("File:"):
            continue
        lower = title.lower()
        if not (".jpg" in lower or ".jpeg" in lower or ".png" in lower):
            continue
        filename = title.replace("File:", "")
        return canonical_wikimedia_url(filename.replace(" ", "_"))
    return None


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
        filename = f"{normalize_latin(latin)}.jpg"
        dest = os.path.join(IMAGES_DIR, filename)

        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            skipped += 1
            print(f"[{i:>3}/{len(unique)}] SKIP  {filename}")
            continue

        print(f"[{i:>3}/{len(unique)}] GET   {filename}")
        ok = False
        info = "aucune source n'a répondu"
        # 1) variantes URL locales (apostrophe / en-dash / sans)
        urls_to_try: list[tuple[str, str]] = [
            (u, "variante") for u in url_variants(plant["image_url"])
        ]
        # 2) index Köhler via API Commons categorymembers
        api_url = find_kohler_url(latin)
        if api_url and api_url not in [u for u, _ in urls_to_try]:
            urls_to_try.append((api_url, "API-cat"))
        # 3) recherche par plante via API Commons search
        search_url = search_commons(latin)
        if search_url and search_url not in [u for u, _ in urls_to_try]:
            urls_to_try.append((search_url, "API-search"))

        for url, source in urls_to_try:
            if not url_exists(url):
                continue
            ok, info = download(url, dest)
            if ok:
                variant_tail = urllib.parse.unquote(url).rsplit("/", 1)[-1]
                print(f"                  ✓ {info}  ({source}: {variant_tail})")
                break
        if ok:
            downloaded += 1
            since_last_commit += 1
            if since_last_commit >= COMMIT_EVERY:
                git_checkpoint(downloaded // COMMIT_EVERY, len(unique) // COMMIT_EVERY)
                since_last_commit = 0
        else:
            failed += 1
            failures.append((latin, plant["image_url"], info))
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
