import argparse
import sys
import tempfile
from pathlib import Path
from typing import Union

from PIL import Image, ImageFilter, ImageOps


def convert(
    src: Union[str, Path],
    dst: Union[str, Path, None] = None,
    *,
    line_thickness: int = 2,
    threshold: int = 128,
    invert_input: bool = False,
) -> Path:
    """
    src            : chemin image source (PNG ou JPEG)
    dst            : chemin de sortie PNG (si None, src stem + '_coloring.png' a cote)
    line_thickness : epaisseur de trait (1-6), utilise comme base pour MinFilter
    threshold      : seuil binarisation 0-255 (128 par defaut)
    invert_input   : inverser avant traitement (si image deja dark-on-light)
    Retourne le Path du fichier ecrit.
    """
    src_path = Path(src)
    if not src_path.exists():
        raise FileNotFoundError(f"Source image not found: {src_path}")

    if dst is None:
        dst_path = src_path.parent / f"{src_path.stem}_coloring.png"
    else:
        dst_path = Path(dst)

    if not (1 <= line_thickness <= 10):
        raise ValueError("line_thickness must be between 1 and 10.")
    if not (0 <= threshold <= 255):
        raise ValueError("threshold must be between 0 and 255.")

    # 1. Ouvrir en niveaux de gris
    img = Image.open(src_path).convert("L")

    if invert_input:
        img = ImageOps.invert(img)

    # 2. Reduire le bruit FLUX
    img = img.filter(ImageFilter.SMOOTH)

    # 3. Detecter les contours (edges claires sur fond sombre apres FIND_EDGES)
    img = img.filter(ImageFilter.FIND_EDGES)

    # 4. Inverser : edges claires -> edges sombres sur fond blanc
    #    Necessaire pour que MinFilter epaississe correctement les traits noirs
    img = ImageOps.invert(img)

    # 5. MinFilter epaissit les zones sombres (traits) — kernel toujours impair
    kernel_size = line_thickness * 2 + 1
    if kernel_size >= 3:
        img = img.filter(ImageFilter.MinFilter(size=kernel_size))

    # 6. Binariser : sombre -> 0 (noir), clair -> 255 (blanc)
    img = img.point(lambda p: 0 if p < threshold else 255)

    # 7. Verifier orientation : fond doit etre blanc (255)
    hist = img.histogram()
    black_px = hist[0]
    white_px = hist[255]
    if black_px > white_px:
        # image inversee (fond noir), on re-inverse
        img = img.point(lambda p: 255 - p)

    # 8. Convertir en RGB et sauvegarder
    img = img.convert("RGB")
    img.save(dst_path, "PNG")
    return dst_path


def run_integrated_test():
    """Test avec image synthetique (rectangle rouge sur fond vert)."""
    print("Running integrated test...")
    width, height = 200, 150
    test_img = Image.new("RGB", (width, height), color="green")
    for x in range(50, 150):
        for y in range(40, 110):
            test_img.putpixel((x, y), (255, 0, 0))

    with tempfile.TemporaryDirectory() as tmpdir:
        src_test_path = Path(tmpdir) / "test_input.png"
        dst_test_path = Path(tmpdir) / "test_output.png"
        test_img.save(src_test_path)

        output_path = convert(
            src=src_test_path,
            dst=dst_test_path,
            line_thickness=2,
            threshold=128,
        )

        result_img = Image.open(output_path).convert("RGB")
        pixels = list(result_img.getdata())

        # Verifier : purement N&B
        is_pure_bw = all(p in [(0, 0, 0), (255, 255, 255)] for p in pixels)

        # Verifier : fond majoritairement blanc (coloring page = fond blanc)
        white_count = sum(1 for p in pixels if p == (255, 255, 255))
        black_count = sum(1 for p in pixels if p == (0, 0, 0))
        white_dominant = white_count > black_count

        if is_pure_bw and white_dominant:
            print(f"OK — {white_count} px blancs, {black_count} px noirs (traits sur fond blanc)")
        else:
            print(f"FAIL — pure_bw={is_pure_bw}, white_dominant={white_dominant} "
                  f"({white_count} blanc, {black_count} noir)")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Convertit une image en line-art coloriage (traits noirs sur fond blanc)."
    )
    parser.add_argument("src", type=str, help="Image source (PNG ou JPEG).")
    parser.add_argument("dst", type=str, nargs="?",
                        help="Destination PNG (defaut: <src>_coloring.png).")
    parser.add_argument("--thickness", type=int, default=2,
                        help="Epaisseur des traits (1-6). Defaut: 2.")
    parser.add_argument("--threshold", type=int, default=128,
                        help="Seuil binarisation 0-255. Defaut: 128.")
    args = parser.parse_args()

    try:
        out = convert(src=args.src, dst=args.dst,
                      line_thickness=args.thickness, threshold=args.threshold)
        print(f"OK -> {out}")
    except Exception as e:
        print(f"Erreur: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        run_integrated_test()
    else:
        main()
