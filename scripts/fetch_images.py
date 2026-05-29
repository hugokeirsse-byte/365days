#!/usr/bin/env python3
"""
fetch_images.py — Télécharge la banque d'illustrations domaine public (Köhler's
Medizinal-Pflanzen) définie dans Data.py vers images/.

Cette banque locale alimente le vertical `vintage_pd` (collection kohler_medizinal) :
la production n'a plus à dépendre d'un fetch Wikimedia live à chaque CdC.

Comportement :
  - Idempotent : une image déjà présente (taille > 0) est ignorée.
  - Commits intermédiaires tous les COMMIT_EVERY téléchargements (défaut 30),
    pour ne pas perdre le travail si le run est interrompu.
  - Les échecs sont consignés dans fetch_failures.log (n'interrompt pas le run).

Env vars :
  COMMIT_EVERY   — nombre de DL entre deux commits (défaut: 30)
  MAX_IMAGES     — limite optionnelle (défaut: 0 = toutes)
  MIN_BYTES      — taille minimale pour considérer un fichier valide (défaut: 1024)

Sortie :
  images/<slug>.jpg       — illustrations
  images/manifest.json    — index {slug: metadata}
  fetch_failures.log      — lignes "slug<TAB>url<TAB>raison"
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = ROOT / "images"
MANIFEST = IMAGES_DIR / "manifest.json"
FAILURES_LOG = ROOT / "fetch_failures.log"

USER_AGENT = "365days-fetch/1.0 (hugo.keirsse@gmail.com)"
TIMEOUT = 45

COMMIT_EVERY = int(os.environ.get("COMMIT_EVERY", "30"))
MAX_IMAGES = int(os.environ.get("MAX_IMAGES", "0"))
MIN_BYTES = int(os.environ.get("MIN_BYTES", "1024"))


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def load_plants() -> list:
    """Charge la liste PLANTS depuis Data.py sans exécuter de code arbitraire."""
    import ast
    data_py = ROOT / "Data.py"
    if not data_py.exists():
        print(f"[fetch] ERREUR: {data_py} introuvable.", file=sys.stderr)
        sys.exit(1)
    src = data_py.read_text(encoding="utf-8")
    # Récupère la partie après "PLANTS ="
    if "=" not in src:
        print("[fetch] ERREUR: Data.py mal formé (pas de '=').", file=sys.stderr)
        sys.exit(1)
    literal = src.split("=", 1)[1].strip()
    return ast.literal_eval(literal)


def load_manifest() -> dict:
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def git_commit_push(count: int) -> None:
    """Commit + push intermédiaire. Best-effort, ne lève pas si rien à committer."""
    branch = os.environ.get("GITHUB_REF_NAME", "")
    try:
        subprocess.run(["git", "add", "images/", "fetch_failures.log"],
                       cwd=ROOT, check=False)
        staged = subprocess.run(["git", "diff", "--cached", "--quiet"],
                                cwd=ROOT).returncode
        if staged == 0:
            return  # rien à committer
        subprocess.run(["git", "commit", "-m",
                        f"Ajoute {count} illustrations Wikimedia (Köhler)"],
                       cwd=ROOT, check=False)
        push_cmd = ["git", "push"]
        if branch:
            push_cmd = ["git", "push", "origin", f"HEAD:{branch}"]
        for attempt in range(4):
            if subprocess.run(push_cmd, cwd=ROOT).returncode == 0:
                return
            time.sleep(2 ** (attempt + 1))
    except Exception as e:
        print(f"[fetch] commit/push intermédiaire échoué (non bloquant): {e}")


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        dest.write_bytes(resp.read())


def main() -> None:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    plants = load_plants()
    manifest = load_manifest()
    failures = []

    if MAX_IMAGES > 0:
        plants = plants[:MAX_IMAGES]

    print(f"[fetch] {len(plants)} illustrations à traiter (commit tous les {COMMIT_EVERY}).")

    downloaded_since_commit = 0
    total_downloaded = 0
    total_skipped = 0

    for plant in plants:
        url = plant.get("image_url", "")
        latin = plant.get("latin", "") or plant.get("name", "") or plant.get("id", "")
        slug = slugify(f"{latin}_{plant.get('id','')}")
        dest = IMAGES_DIR / f"{slug}.jpg"

        if dest.exists() and dest.stat().st_size >= MIN_BYTES:
            total_skipped += 1
            manifest.setdefault(slug, {
                "id": plant.get("id"), "name": plant.get("name"),
                "latin": latin, "source_url": url,
                "description": plant.get("description", ""),
                "file": dest.name,
                "collection": "kohler_medizinal",
                "licence": "public_domain_pre_1928",
            })
            continue

        if not url:
            failures.append(f"{slug}\t(no_url)\tmissing image_url")
            continue

        try:
            download(url, dest)
            if dest.stat().st_size < MIN_BYTES:
                dest.unlink(missing_ok=True)
                failures.append(f"{slug}\t{url}\ttoo_small")
                continue
            manifest[slug] = {
                "id": plant.get("id"), "name": plant.get("name"),
                "latin": latin, "source_url": url,
                "description": plant.get("description", ""),
                "file": dest.name,
                "collection": "kohler_medizinal",
                "licence": "public_domain_pre_1928",
            }
            total_downloaded += 1
            downloaded_since_commit += 1
            print(f"[fetch] ✓ {slug} ({dest.stat().st_size // 1024} KB)")
            time.sleep(0.5)  # courtoisie envers Wikimedia
        except Exception as e:
            failures.append(f"{slug}\t{url}\t{e}")
            print(f"[fetch] ✗ {slug}: {e}")

        if downloaded_since_commit >= COMMIT_EVERY:
            MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                encoding="utf-8")
            if failures:
                FAILURES_LOG.write_text("\n".join(failures) + "\n", encoding="utf-8")
            git_commit_push(downloaded_since_commit)
            downloaded_since_commit = 0

    # Écriture finale du manifest + log
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    if failures:
        FAILURES_LOG.write_text("\n".join(failures) + "\n", encoding="utf-8")

    print(f"\n[fetch] === RÉSUMÉ ===")
    print(f"  Téléchargées : {total_downloaded}")
    print(f"  Déjà présentes : {total_skipped}")
    print(f"  Échecs : {len(failures)}")
    print(f"  Banque totale : {len(manifest)} entrées dans images/")


if __name__ == "__main__":
    main()
