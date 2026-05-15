"""
Upscale ×4 des images via Real-ESRGAN — PyTorch CPU sur GitHub Actions.

Approche 100% gratuite et sans clé : utilise le package Python officiel
realesrgan (basé sur PyTorch CPU), pas le binaire ncnn-vulkan qui plante
sur les runners sans GPU.

- Lit toutes les images dans SOURCE_DIR (par défaut generated_images/).
- Charge le modèle Real-ESRGAN x4plus depuis l'URL officielle.
- Upscale chaque image (~30-60s/image en CPU).
- Écrit dans TARGET_DIR (par défaut generated_images_hd/).
- Idempotent : skip ce qui existe déjà.
- Commit checkpoint toutes les 3 images réussies (CPU = lent, on
  protège l'avancée).
"""

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SOURCE_DIR_NAME = os.environ.get("SOURCE_DIR", "generated_images")
TARGET_DIR_NAME = os.environ.get("TARGET_DIR", "generated_images_hd")
MODEL_NAME = os.environ.get("UPSCALE_MODEL", "RealESRGAN_x4plus")
SCALE = int(os.environ.get("UPSCALE_SCALE", "4"))

SOURCE_DIR = ROOT / SOURCE_DIR_NAME
TARGET_DIR = ROOT / TARGET_DIR_NAME
COMMIT_EVERY = 3
MIN_IMAGE_BYTES = 2000

MODEL_URLS = {
    "RealESRGAN_x4plus": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
    "RealESRGAN_x4plus_anime_6B": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth",
    "RealESRGAN_x2plus": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth",
}


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
            # Push avec retry + rebase pour gérer les runs parallèles
            # (ex. fetch_images qui pousse sur la même branche).
            for attempt in range(5):
                push = subprocess.run(
                    ["git", "push", "origin", f"HEAD:{branch}"], cwd=ROOT
                )
                if push.returncode == 0:
                    break
                print(f"  ⟲ push rejeté, rebase + retry {attempt + 1}/5")
                subprocess.run(
                    ["git", "pull", "--rebase", "origin", branch],
                    cwd=ROOT, check=False,
                )
        print(f"  → checkpoint pushé : {label}")
    except subprocess.CalledProcessError as exc:
        print(f"  ! checkpoint en échec : {exc}")


def build_upsampler():
    """Charge Real-ESRGAN sur CPU, télécharge le modèle si besoin."""
    import cv2  # noqa: F401 (vérifie l'install)
    import torch
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer

    print(f"PyTorch : {torch.__version__}  ·  device : cpu")

    if MODEL_NAME not in MODEL_URLS:
        raise SystemExit(f"Modèle inconnu : {MODEL_NAME}. Choix : {list(MODEL_URLS)}")

    if "anime" in MODEL_NAME:
        net = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=6, num_grow_ch=32, scale=4)
        scale = 4
    elif "x2" in MODEL_NAME:
        net = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
        scale = 2
    else:
        net = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        scale = 4

    upsampler = RealESRGANer(
        scale=scale,
        model_path=MODEL_URLS[MODEL_NAME],
        model=net,
        tile=400,       # tiles pour limiter la RAM
        tile_pad=10,
        pre_pad=0,
        half=False,     # FP32 sur CPU
        device=torch.device("cpu"),
    )
    return upsampler, scale


def main() -> int:
    if not SOURCE_DIR.is_dir():
        print(f"ERREUR : dossier source {SOURCE_DIR} introuvable.")
        return 2

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
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
    print(f"Modèle : {MODEL_NAME}")
    print(f"À traiter : {len(images)}")
    print()

    print("Initialisation Real-ESRGAN…")
    upsampler, real_scale = build_upsampler()
    print(f"  → upscale ×{real_scale} prêt")
    print()

    import cv2
    done = skipped = failed = 0
    since_last_commit = 0
    start = time.time()

    for i, name in enumerate(images, 1):
        inp = SOURCE_DIR / name
        out = TARGET_DIR / name

        if out.exists() and out.stat().st_size > MIN_IMAGE_BYTES:
            skipped += 1
            print(f"[{i:>3}/{len(images)}] SKIP  {name}")
            continue

        print(f"[{i:>3}/{len(images)}] UP    {name}")
        t0 = time.time()
        try:
            img = cv2.imread(str(inp), cv2.IMREAD_UNCHANGED)
            if img is None:
                raise RuntimeError("cv2.imread retour None (image corrompue ?)")
            output, _ = upsampler.enhance(img, outscale=SCALE)
            cv2.imwrite(str(out), output, [cv2.IMWRITE_JPEG_QUALITY, 92])
            dt = time.time() - t0
            size_kb = out.stat().st_size // 1024
            done += 1
            since_last_commit += 1
            print(f"                  ✓ {size_kb} KB en {dt:.1f}s")
        except Exception as exc:  # noqa: BLE001
            dt = time.time() - t0
            failed += 1
            print(f"                  ✗ {type(exc).__name__}: {exc} (après {dt:.1f}s)")
            continue

        if since_last_commit >= COMMIT_EVERY:
            git_checkpoint(f"{done} images upscalées")
            since_last_commit = 0

    total = time.time() - start
    print()
    print("=" * 60)
    print(f"Upscalées : {done}")
    print(f"Ignorées  : {skipped}")
    print(f"Échecs    : {failed}")
    print(f"Durée     : {total / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
