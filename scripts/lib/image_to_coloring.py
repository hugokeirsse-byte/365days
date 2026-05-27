import sys
from PIL import Image, ImageFilter
from pathlib import Path
import os
import argparse

def convert(
    src: str | Path,
    dst: str | Path | None = None,
    *,
    line_thickness: int = 2,
    threshold: int = 128,
    invert_input: bool = False,
) -> Path:
    """
    Converts a color or grayscale image into a line-art coloring page.

    The process involves converting to grayscale, smoothing, edge detection,
    thickening lines, and binarizing to pure black lines on a pure white background.

    Args:
        src: Path to the source image file (PNG or JPEG).
        dst: Optional path for the output coloring page file (PNG).
             If None, defaults to <src_stem>_coloring.png in the same directory.
        line_thickness: The desired thickness of the lines. Higher values result
                        in thicker lines. Must be a positive integer.
        threshold: Binarization threshold (0-255). Pixels darker than this value
                   (after processing) will become black (0), others white (255).
        invert_input: If True, the input image's colors are inverted before processing.
                      Useful for "negative" style inputs or dark-on-light images.

    Returns:
        The Path object of the generated coloring page.

    Raises:
        FileNotFoundError: If the source image does not exist.
        IOError: If there's an issue opening or saving the image.
        ValueError: If line_thickness is not a positive integer.
    """
    src_path = Path(src)
    if not src_path.is_file():
        raise FileNotFoundError(f"Source image not found: {src_path}")

    if dst is None:
        dst_path = src_path.parent / f"{src_path.stem}_coloring.png"
    else:
        dst_path = Path(dst)

    if not isinstance(line_thickness, int) or line_thickness <= 0:
        raise ValueError("line_thickness must be a positive integer.")
    if not 0 <= threshold <= 255:
        raise ValueError("threshold must be between 0 and 255.")

    # 1. Ouvrir l'image, convertir en L (niveaux de gris)
    img = Image.open(src_path).convert("L")

    # Appliquer invert_input si demandé
    if invert_input:
        img = img.point(lambda p: 255 - p)

    # 2. Appliquer ImageFilter.SMOOTH (réduire le bruit FLUX)
    img = img.filter(ImageFilter.SMOOTH)

    # 3. Appliquer ImageFilter.FIND_EDGES (détection de contours)
    # Pillow's FIND_EDGES typically produces dark edges on a light background.
    img = img.filter(ImageFilter.FIND_EDGES)

    # 4. MinFilter(size) épaissit les contours, puis inverser → trait noir épais sur blanc
    # Calculate MinFilter size: 1 for no expansion, 3 for 1-pixel expansion, etc.
    # A size of 2*N-1 expands by N-1 pixels.
    min_filter_size = max(1, 2 * line_thickness - 1)
    img = img.filter(ImageFilter.MinFilter(size=min_filter_size))

    # "puis inverser" as per specification.
    # At this point, we have thick dark lines on a light background.
    # Inverting makes them thick light lines on a dark background.
    img = img.point(lambda p: 255 - p)

    # 5. Binariser : point(lambda p: 0 if p < threshold else 255)
    # With light lines on a dark background, this step will make the dark background
    # black (0) and the light lines white (255). Result: white lines on black background.
    img = img.point(lambda p: 0 if p < threshold else 255)

    # 6. Forcer fond=255 (blanc), traits=0 (noir)
    # To achieve "fond blanc pur, traits noir pur" from the previous step's
    # "white lines on black background", we need a final inversion.
    img = img.point(lambda p: 255 - p)

    # 7. Convertir en RGB, sauvegarder en PNG
    # The image is already pure black and white (0 or 255). Converting to RGB
    # will make (0,0,0) for black and (255,255,255) for white.
    img = img.convert("RGB")
    img.save(dst_path, "PNG")

    return dst_path

def run_integrated_test():
    """
    Runs an integrated test: creates a synthetic image, converts it,
    and verifies the output.
    """
    print("Running integrated test...")
    test_src_path = Path("test_input_coloring.png")
    test_dst_path = Path("test_output_coloring.png")

    try:
        # Create a synthetic test image: red rectangle on green background
        img_test = Image.new("RGB", (200, 150), color="green")
        # Draw a red rectangle in the center
        for x in range(55, 145):
            for y in range(45, 105):
                img_test.putpixel((x, y), (255, 0, 0))
        img_test.save(test_src_path)
        print(f"Created synthetic test image: {test_src_path}")

        # Convert it to a coloring page
        output_path = convert(
            test_src_path,
            test_dst_path,
            line_thickness=2,
            threshold=128,
            invert_input=False,
        )
        print(f"Converted test image to: {output_path}")

        # Verify output
        output_img = Image.open(output_path)
        if output_img.mode != "RGB":
            raise AssertionError(f"Output image mode is {output_img.mode}, expected RGB.")

        # Check a few pixels to ensure pure black/white and correct line detection
        # Background pixel (outside rectangle, should be white)
        bg_pixel = output_img.getpixel((10, 10))
        if bg_pixel != (255, 255, 255):
            raise AssertionError(f"Background pixel (10,10) is {bg_pixel}, expected (255,255,255).")

        # Inner pixel (inside rectangle, should be white)
        inner_pixel = output_img.getpixel((100, 75))
        if inner_pixel != (255, 255, 255):
            raise AssertionError(f"Inner pixel (100,75) is {inner_pixel}, expected (255,255,255).")

        # Line pixel (on the edge of the rectangle, should be black)
        # The rectangle is from x=55 to x=144, y=45 to y=104.
        # With line_thickness=2, the line should be around x=55 and x=144.
        # Let's check a pixel that should be part of the left vertical line.
        line_pixel_left = output_img.getpixel((55, 75))
        if line_pixel_left != (0, 0, 0):
            raise AssertionError(f"Line pixel (55,75) is {line_pixel_left}, expected (0,0,0).")
        
        # Check a pixel on the right vertical line
        line_pixel_right = output_img.getpixel((144, 75))
        if line_pixel_right != (0, 0, 0):
            raise AssertionError(f"Line pixel (144,75) is {line_pixel_right}, expected (0,0,0).")

        print("OK: Integrated test passed successfully.")

    except Exception as e:
        print(f"Test FAILED: {e}")
        sys.exit(1)
    finally:
        # Clean up test files
        if test_src_path.exists():
            os.remove(test_src_path)
        if test_dst_path.exists():
            os.remove(test_dst_path)
        print("Test files cleaned up.")

def main():
    """
    Main function to handle command-line arguments and execute the conversion.
    """
    parser = argparse.ArgumentParser(
        description="Convert an image to a coloring page (black lines on white background)."
    )
    parser.add_argument(
        "src",
        type=str,
        nargs="?", # Make src optional for the test case
        help="Source image file (PNG or JPEG). Required unless running test mode.",
    )
    parser.add_argument(
        "dst",
        type=str,
        nargs="?",
        default=None,
        help="Destination coloring page file (PNG). Defaults to <src_stem>_coloring.png.",
    )
    parser.add_argument(
        "--thickness",
        type=int,
        default=2,
        help="Thickness of the lines. Higher value means thicker lines. (Default: 2)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=128,
        help="Binarization threshold (0-255). Pixels darker than this become black. (Default: 128)",
    )
    parser.add_argument(
        "--invert-input",
        action="store_true",
        help="Invert the input image before processing (useful for negative-like inputs).",
    )

    args = parser.parse_args()

    if args.src is None:
        # If no arguments are provided, run the integrated test
        run_integrated_test()
    else:
        try:
            output_path = convert(
                args.src,
                args.dst,
                line_thickness=args.thickness,
                threshold=args.threshold,
                invert_input=args.invert_input,
            )
            print(f"Successfully converted '{args.src}' to '{output_path}'")
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print(f"Error: Invalid parameter value: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()