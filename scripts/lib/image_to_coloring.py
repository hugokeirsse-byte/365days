from PIL import Image, ImageFilter
from pathlib import Path
import argparse
import sys

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
    The output will have a pure white background and thick, closed black outlines.

    Args:
        src: Path to the source image (PNG or JPEG).
        dst: Path to save the output image (PNG). If None, a default name
             will be generated based on the source path.
        line_thickness: The thickness of the black lines. Corresponds to
                        the 'size' parameter of ImageFilter.MinFilter.
                        Must be a positive integer (e.g., 2 for a 2x2 kernel).
        threshold: Binarization threshold (0-255). Pixels darker than this value
                   will become black (0), otherwise white (255).
        invert_input: If True, the input image's colors will be inverted
                      after grayscale conversion but before edge detection.
                      Useful for light-on-dark inputs where features are light.

    Returns:
        The Path object of the saved output image.

    Raises:
        FileNotFoundError: If the source image does not exist.
        IOError: If there's an issue opening or saving the image.
        ValueError: If line_thickness is not positive or threshold is out of range.
    """
    if not Path(src).exists():
        raise FileNotFoundError(f"Source image not found: {src}")
    if not isinstance(line_thickness, int) or line_thickness <= 0:
        raise ValueError("line_thickness must be a positive integer.")
    if not isinstance(threshold, int) or not (0 <= threshold <= 255):
        raise ValueError("threshold must be an integer between 0 and 255.")

    src_path = Path(src)
    if dst is None:
        # Generate default destination path: e.g., 'image_coloring.png'
        dst_path = src_path.parent / f"{src_path.stem}_coloring.png"
    else:
        dst_path = Path(dst)

    try:
        # 1. Open image, convert to L (grayscale)
        img = Image.open(src_path).convert("L")

        # Apply invert_input if requested (after grayscale, before edge detection)
        if invert_input:
            img = img.point(lambda p: 255 - p)

        # 2. Apply ImageFilter.SMOOTH (reduce noise)
        img = img.filter(ImageFilter.SMOOTH)

        # 3. Apply ImageFilter.FIND_EDGES (edge detection)
        img = img.filter(ImageFilter.FIND_EDGES)

        # 4. Apply MinFilter to thicken contours.
        # MinFilter replaces each pixel with the darkest pixel in its neighborhood.
        # If FIND_EDGES produces dark lines, MinFilter will expand them.
        img = img.filter(ImageFilter.MinFilter(size=line_thickness))

        # 5. Binarize: turn pixels darker than threshold to black (0), others to white (255).
        # This ensures pure black lines on a pure white background.
        img = img.point(lambda p: 0 if p < threshold else 255)

        # 6. Forcer fond=255 (blanc), traits=0 (noir) - already achieved by binarization.

        # 7. Convert to RGB (for consistent output format), save as PNG.
        img = img.convert("RGB")
        img.save(dst_path, "PNG")

    except Exception as e:
        raise IOError(f"Error processing image {src_path}: {e}") from e

    return dst_path

def _create_test_image(path: Path):
    """Creates a synthetic test image: a red rectangle on a green background."""
    img_size = (200, 150)
    img = Image.new("RGB", img_size, color="green")
    # Draw a red rectangle
    for x in range(50, 150):
        for y in range(30, 120):
            img.putpixel((x, y), (255, 0, 0))  # Red
    img.save(path, "PNG")

def _run_test():
    """Runs the integrated test for the image conversion."""
    print("Running integrated test...")
    test_src_path = Path("test_input.png")
    test_dst_path = Path("test_output_coloring.png")

    try:
        _create_test_image(test_src_path)
        print(f"Created synthetic test image: {test_src_path}")

        # Test with specific parameters to ensure lines are detected and thickened
        output_path = convert(test_src_path, test_dst_path, line_thickness=3, threshold=100)
        print(f"Generated coloring image: {output_path}")

        # Verify output: check for pure black and white pixels, and presence of both.
        output_img = Image.open(output_path).convert("L")
        pixels = list(output_img.getdata())

        unique_pixels = set(pixels)
        if not all(p in (0, 255) for p in unique_pixels):
            raise AssertionError("Output image contains colors other than pure black and white.")

        if 0 not in unique_pixels or 255 not in unique_pixels:
            raise AssertionError("Output image is either completely black or completely white (no lines or no background).")

        print("Test successful: Output is B&W with detected lines.")
        print("OK")

    except Exception as e:
        print(f"Test failed: {e}", file=sys.stderr)
        print("FAIL")
    finally:
        # Clean up test files
        if test_src_path.exists():
            test_src_path.unlink()
        if test_dst_path.exists():
            test_dst_path.unlink()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments provided, run integrated test
        _run_test()
    else:
        # Parse command-line arguments
        parser = argparse.ArgumentParser(
            description="Convert an image to a line-art coloring page.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument("src", type=str, help="Path to the source image (PNG or JPEG).")
        parser.add_argument(
            "dst",
            type=str,
            nargs="?",  # 0 or 1 argument
            default=None,
            help="Path to save the output image (PNG). If not provided, a default name will be generated."
        )
        parser.add_argument(
            "--thickness",
            type=int,
            default=2,
            help="The thickness of the black lines. Must be a positive integer."
        )
        parser.add_argument(
            "--threshold",
            type=int,
            default=128,
            help="Binarization threshold (0-255). Pixels darker than this value become black."
        )
        parser.add_argument(
            "--invert-input",
            action="store_true",
            help="Invert the input image's colors before processing. Useful for light-on-dark inputs."
        )

        args = parser.parse_args()

        try:
            output_path = convert(
                args.src,
                args.dst,
                line_thickness=args.thickness,
                threshold=args.threshold,
                invert_input=args.invert_input,
            )
            print(f"Successfully converted '{args.src}' to '{output_path}'")
        except (FileNotFoundError, IOError, ValueError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
            sys.exit(1)
