"""
Post-processing automatique des mandalas générés par Pollinations.

Pipeline :
1. Threshold N&B pur (élimine les gris résiduels de Flux)
2. Symétrisation forcée (4-fold ou 8-fold) — force la symétrie radiale
   parfaite même si Flux a produit un mandala légèrement asymétrique.
3. Sauvegarde en JPEG haute qualité.

Le résultat est un mandala parfaitement symétrique en line art noir/blanc
pur, prêt pour le coloriage adulte sans aucun artefact IA.

Utilisation :
    SOURCE_DIR=generated_images TARGET_DIR=generated_images_final \\
    SYMMETRY=8 THRESHOLD=180 python scripts/mandala_finalize.py
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError:
    print("ERREUR : Pillow non installé. pip install Pillow")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent

SOURCE_DIR = ROOT / os.environ.get("SOURCE_DIR", "generated_images")
TARGET_DIR = ROOT / os.environ.get("TARGET_DIR", "generated_images_final")
THRESHOLD = int(os.environ.get("THRESHOLD") or "180")  # 0=tout noir, 255=tout blanc
SYMMETRY = int(os.environ.get("SYMMETRY") or "8")      # 0 (no), 2, 4, 8
MIN_SIZE = int(os.environ.get("MIN_SIZE") or "1500")    # px


def threshold_pure_bw(img: Image.Image, threshold: int = 180) -> Image.Image:
    """Convertit en noir/blanc pur : tout pixel > threshold → blanc, sinon noir."""
    gray = img.convert("L")
    return gray.point(lambda p: 255 if p > threshold else 0, mode="L")


def symmetrize_8fold(img: Image.Image) -> Image.Image:
    """Force la symétrie 8-fold : prend le secteur supérieur-gauche, le miroir
    pour les 3 autres quadrants, puis miroir diagonal pour les 4 octants.

    Résultat : symétrie radiale parfaite à partir du quadrant le plus
    représentatif (top-left par défaut).
    """
    w, h = img.size
    size = min(w, h)
    img = img.crop(((w - size) // 2, (h - size) // 2,
                    (w - size) // 2 + size, (h - size) // 2 + size))

    # Quadrant top-left → reconstitue le carré par miroir H + V (4-fold)
    half = size // 2
    tl = img.crop((0, 0, half, half))
    tr = tl.transpose(Image.FLIP_LEFT_RIGHT)
    bl = tl.transpose(Image.FLIP_TOP_BOTTOM)
    br = bl.transpose(Image.FLIP_LEFT_RIGHT)
    canvas = Image.new("L", (size, size), 255)
    canvas.paste(tl, (0, 0))
    canvas.paste(tr, (half, 0))
    canvas.paste(bl, (0, half))
    canvas.paste(br, (half, half))

    # 8-fold : on miroir aussi sur la diagonale pour les 8 octants
    diag = canvas.transpose(Image.TRANSPOSE)
    # Combine avec le mode minimum (= prend le pixel le plus sombre)
    out = ImageChops.darker(canvas, diag)
    return out


def symmetrize_4fold(img: Image.Image) -> Image.Image:
    """Version 4-fold (miroir H + V seulement, pas de diagonale)."""
    w, h = img.size
    size = min(w, h)
    img = img.crop(((w - size) // 2, (h - size) // 2,
                    (w - size) // 2 + size, (h - size) // 2 + size))
    half = size // 2
    tl = img.crop((0, 0, half, half))
    tr = tl.transpose(Image.FLIP_LEFT_RIGHT)
    bl = tl.transpose(Image.FLIP_TOP_BOTTOM)
    br = bl.transpose(Image.FLIP_LEFT_RIGHT)
    canvas = Image.new("L", (size, size), 255)
    canvas.paste(tl, (0, 0))
    canvas.paste(tr, (half, 0))
    canvas.paste(bl, (0, half))
    canvas.paste(br, (half, half))
    return canvas


def finalize_one(src: Path, dst: Path) -> tuple[bool, str]:
    try:
        img = Image.open(src)
        if max(img.size) < MIN_SIZE:
            return False, f"trop petit ({img.size})"
        img = threshold_pure_bw(img, THRESHOLD)
        if SYMMETRY == 8:
            img = symmetrize_8fold(img)
        elif SYMMETRY == 4:
            img = symmetrize_4fold(img)
        # Mode "L" → JPEG noir et blanc
        img.save(dst, "JPEG", quality=92, optimize=True)
        return True, f"{dst.stat().st_size // 1024} KB"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    if not SOURCE_DIR.is_dir():
        print(f"ERREUR : dossier source {SOURCE_DIR} introuvable.")
        return 2

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    images = sorted(
        f for f in os.listdir(SOURCE_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
        and not f.startswith(".")
    )
    if not images:
        print(f"Aucune image dans {SOURCE_DIR}.")
        return 1

    print(f"Source     : {SOURCE_DIR}")
    print(f"Cible      : {TARGET_DIR}")
    print(f"Threshold  : {THRESHOLD}")
    print(f"Symétrie   : {SYMMETRY}-fold" if SYMMETRY else "Symétrie   : aucune")
    print(f"À traiter  : {len(images)}")
    print()

    done = failed = 0
    for i, name in enumerate(images, 1):
        src = SOURCE_DIR / name
        dst = TARGET_DIR / name
        ok, info = finalize_one(src, dst)
        if ok:
            done += 1
            print(f"[{i:>3}/{len(images)}] ✓ {name}  ({info})")
        else:
            failed += 1
            print(f"[{i:>3}/{len(images)}] ✗ {name}  ({info})")

    print()
    print("=" * 60)
    print(f"Finalisées : {done}")
    print(f"Échecs     : {failed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
