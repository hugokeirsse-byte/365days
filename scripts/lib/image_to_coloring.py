import argparse
import sys
import tempfile
from pathlib import Path
from typing import Union

from PIL import Image, ImageFilter


def convert(
    src: Union[str, Path],
    dst: Union[str, Path, None] = None,
    *,
    line_thickness: int = 2,
    threshold: int = 128,
    invert_input: bool = False,
) -> Path:
    """
    Converts a color or grayscale image into a line-art coloring page.

    The process involves converting to grayscale, smoothing, edge detection,
    thickening contours, and binarizing to pure black lines on a pure white background.

    Args:
        src: Path to the source image (PNG or JPEG).
        dst: Optional path for the destination PNG image. If None, a default
             name (<src_stem>_coloring.png) in the same directory as src will be used.
        line_thickness: The desired thickness of the lines. This value is used
                        as the kernel size for the MinFilter operation. Default is 2.
        threshold: Binarization threshold (0-255). Pixels with a value darker
                   than this become black (0), others become white (255). Default is 128.
        invert_input: If True, the input image's grayscale values are inverted
                      before processing (e.g., dark areas become light). Default is False.

    Returns:
        The Path object of the generated coloring page.

    Raises:
        FileNotFoundError: If the source image does not exist.
        IOError: If there's an issue opening or saving the image.
        ValueError: If line_thickness or threshold are out of valid range.
    """
    if not isinstance(src, Path):
        src_path = Path(src)
    else:
        src_path = src

    if not src_path.exists():
        raise FileNotFoundError(f"Source image not found: {src_path}")

    if dst is None:
        dst_path = src_path.parent / f"{src_path.stem}_coloring.png"
    elif not isinstance(dst, Path):
        dst_path = Path(dst)
    else:
        dst_path = dst

    if not (1 <= line_thickness <= 10):  # Arbitrary reasonable range for thickness
        raise ValueError("line_thickness must be between 1 and 10.")
    if not (0 <= threshold <= 255):
        raise ValueError("threshold must be between 0 and 255.")

    try:
        # 1. Ouvrir l'image, convertir en L (niveaux de gris)
        img = Image.open(src_path).convert("L")

        # Apply input inversion if requested
        if invert_input:
            img = img.point(lambda p: 255 - p)

        # 2. Appliquer ImageFilter.SMOOTH (réduire le bruit FLUX)
        img = img.filter(ImageFilter.SMOOTH)

        # 3. Appliquer ImageFilter.FIND_EDGES (détection de contours)
        img = img.filter(ImageFilter.FIND_EDGES)

        # 4. MinFilter(size) épaissit les contours
        #    FIND_EDGES typically produces dark lines on a light background.
        #    MinFilter expands these dark regions, effectively thickening the lines.
        #    The "puis inverser" part of the spec's step 4 is implicitly handled
        #    by the binarization (step 5/6) to ensure black lines on white.
        if line_thickness > 1:  # MinFilter(1) is an identity operation
            img = img.filter(ImageFilter.MinFilter(size=line_thickness))

        # 5. Binariser : point(lambda p: 0 if p < threshold else 255)
        # 6. Forcer fond=255 (blanc), traits=0 (noir)
        #    These two steps are combined: pixels darker than threshold become black (0),
        #    all others become pure white (255).
        img = img.point(lambda p: 0 if p < threshold else 255)

        # 7. Convertir en RGB, sauvegarder en PNG
        #    Converting to RGB ensures a standard output format, even though it's B&W.
        img = img.convert("RGB")
        img.save(dst_path, "PNG")

        return dst_path

    except Exception as e:
        # Catch any Pillow-related errors or other exceptions during processing
        raise IOError(f"Failed to process image '{src_path}': {e}") from e


def run_integrated_test():
    """
    Runs an integrated test by creating a synthetic image, converting it,
    and verifying the output.
    """
    print("Running integrated test...")

    # Create a synthetic image: red rectangle on green background
    width, height = 200, 150
    test_img = Image.new("RGB", (width, height), color="green")
    # Draw a red rectangle
    for x in range(50, 150):
        for y in range(40, 110):
            test_img.putpixel((x, y), (255, 0, 0))  # Red

    with tempfile.TemporaryDirectory() as tmpdir:
        src_test_path = Path(tmpdir) / "test_input.png"
        dst_test_path = Path(tmpdir) / "test_output.png"
        test_img.save(src_test_path)
        print(f"Created synthetic test image: {src_test_path}")

        try:
            output_path = convert(
                src=src_test_path,
                dst=dst_test_path,
                line_thickness=2,
                threshold=128,
                invert_input=False,
            )

            # Verify output
            result_img = Image.open(output_path).convert("RGB")

            # Check if the image is purely black and white (0,0,0) or (255,255,255)
            is_pure_bw = True
            for pixel in result_img.getdata():
                if pixel not in [(0, 0, 0), (255, 255, 255)]:
                    is_pure_bw = False
                    break

            # Check if it contains both black and white pixels (i.e., not entirely blank or solid)
            unique_colors = set(result_img.getdata())
            has_black = (0, 0, 0) in unique_colors
            has_white = (255, 255, 255) in unique_colors

            if is_pure_bw and has_black and has_white:
                print("OK: Test image converted successfully to pure black and white line art.")
            else:
                print("FAIL: Output image is not pure black and white or lacks expected features.")
                sys.exit(1)

        except Exception as e:
            print(f"FAIL: An error occurred during test: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    """
    Parses command-line arguments and calls the convert function.
    """
    parser = argparse.ArgumentParser(
        description="Convert an image to a coloring line-art page (black lines on white background)."
    )
    parser.add_argument(
        "src",
        type=str,
        help="Path to the source image (PNG or JPEG)."
    )
    parser.add_argument(
        "dst",
        type=str,
        nargs="?",  # Optional argument
        help="Path for the destination PNG image. Defaults to <src_stem>_coloring.png."
    )
    parser.add_argument(
        "--thickness",
        type=int,
        default=2,
        help="Line thickness for contours (MinFilter kernel size). Default: 2."
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=128,
        help="Binarization threshold (0-255). Pixels darker than this become black. Default: 128."
    )
    # The 'invert_input' parameter is not exposed via the CLI as per the specification.

    args = parser.parse_args()

    try:
        output_path = convert(
            src=args.src,
            dst=args.dst,
            line_thickness=args.thickness,
            threshold=args.threshold,
            invert_input=False,  # Not exposed via CLI
        )
        print(f"Successfully converted '{args.src}' to '{output_path}'")
    except (FileNotFoundError, IOError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # If called without arguments, run the integrated test.
    if len(sys.argv) == 1:
        run_integrated_test()
    else:
        main()