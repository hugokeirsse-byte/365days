"""
Upscale ×4 des images via Real-ESRGAN (binaire local sur GitHub Actions).

- Lit toutes les images dans SOURCE_DIR (par défaut generated_images/).
- Passe chaque image au binaire realesrgan-ncnn-vulkan (mode CPU sur Actions).
- Écrit le résultat dans TARGET_DIR (par défaut generated_images_hd/).
- Idempotent : skip les images déjà upscalées.
- Commit intermédiaire toutes les 5 images réussies pour ne rien perdre
  en cas de timeout du workflow.

Le binaire et les modèles sont téléchargés par le workflow GitHub Actions
depuis les releases officielles de Real-ESRGAN, donc aucune dépendance
Python, aucune API tierce, aucun compte, aucune clé.
"""

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE_DIR_NAME = os.environ.get("SOURCE_DIR", "generated_images")
TARGET_DIR_NAME = os.environ.get("TARGET_DIR", "generated_images_hd")
MODEL = os.environ.get("UPSCALE_MODEL", "realesrgan-x4plus")
SCALE = os.environ.get("UPSCALE_SCALE", "4")
BIN = os.environ.get("REALESRGAN_BIN", "./realesrgan-ncnn-vulkan")
GPU_ID = os.environ.get("REALESRGAN_GPU", "-1")  # -1 = CPU forcé

SOURCE_DIR = os.path.join(ROOT, SOURCE_DIR_NAME)
TARGET_DIR = os.path.join(ROOT, TARGET_DIR_NAME)
COMMIT_EVERY = 5
MIN_IMAGE_BYTES = 2000


def git_checkpoint(label: str) -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    branch = os.environ.get("GITHUB_REF_NAME", "")
    try:
        subprocess.run(["git", "add", TARGET_DIR_NAME], check=True, cwd=ROOT)
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], cwd=ROOT
        ).returncode
        if diff == 0:
            return
        subprocess.run(
            ["git", "commit", "-m", f"Checkpoint upscale : {label}"],
            check=True,
            cwd=ROOT,
        )
        if branch:
            subprocess.run(
                ["git", "push", "origin", f"HEAD:{branch}"], check=True, cwd=ROOT
            )
        print(f"  → checkpoint pushé : {label}")
    except subprocess.CalledProcessError as exc:
        print(f"  ! checkpoint en échec : {exc}")


def main() -> int:
    if not os.path.isdir(SOURCE_DIR):
        print(f"ERREUR : dossier source {SOURCE_DIR} introuvable.")
        return 2
    if not os.path.exists(BIN):
        print(f"ERREUR : binaire {BIN} introuvable. Le workflow doit le télécharger.")
        return 2

    os.makedirs(TARGET_DIR, exist_ok=True)
    images = sorted(
        f
        for f in os.listdir(SOURCE_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
        and not f.startswith(".")
    )
    if not images:
        print(f"Aucune image dans {SOURCE_DIR}.")
        return 1

    print(f"Source : {SOURCE_DIR}")
    print(f"Cible  : {TARGET_DIR}")
    print(f"Modèle : {MODEL} (×{SCALE})  ·  GPU : {GPU_ID} (-1 = CPU)")
    print(f"À traiter : {len(images)}")
    print()

    done = skipped = failed = 0
    since_last_commit = 0
    start = time.time()

    for i, name in enumerate(images, 1):
        inp = os.path.join(SOURCE_DIR, name)
        out = os.path.join(TARGET_DIR, name)

        if os.path.exists(out) and os.path.getsize(out) > MIN_IMAGE_BYTES:
            skipped += 1
            print(f"[{i:>3}/{len(images)}] SKIP  {name}")
            continue

        print(f"[{i:>3}/{len(images)}] UP    {name}")
        t0 = time.time()
        cmd = [
            BIN,
            "-i", inp,
            "-o", out,
            "-n", MODEL,
            "-s", SCALE,
            "-g", GPU_ID,
            "-f", "jpg",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        dt = time.time() - t0

        if result.returncode != 0:
            failed += 1
            tail = (result.stderr or result.stdout or "")[-200:].replace("\n", " ")
            print(f"                  ✗ exit {result.returncode} en {dt:.1f}s · {tail}")
            continue

        if not os.path.exists(out) or os.path.getsize(out) < MIN_IMAGE_BYTES:
            failed += 1
            print(f"                  ✗ fichier de sortie vide ou trop petit")
            continue

        size_kb = os.path.getsize(out) // 1024
        done += 1
        since_last_commit += 1
        print(f"                  ✓ {size_kb} KB en {dt:.1f}s")

        if since_last_commit >= COMMIT_EVERY:
            git_checkpoint(f"{done} images upscalées")
            since_last_commit = 0

    total_time = time.time() - start
    print()
    print("=" * 60)
    print(f"Upscalées : {done}")
    print(f"Ignorées  : {skipped}")
    print(f"Échecs    : {failed}")
    print(f"Durée     : {total_time / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
