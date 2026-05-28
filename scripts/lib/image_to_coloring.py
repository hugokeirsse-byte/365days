from __future__ import annotations

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps, ImageDraw

def convert(
    src: str | Path,
    dst: str | Path | None = None,
    *,
    line_thickness: int = 2,
    threshold: int = 128,
    invert_input: bool = False,
) -> Path:
    """
    Converts a color or grayscale image into a clean black and white line-art coloring page.
    
    Args:
        src: Path to the source image.
        dst: Path to the destination image. If None, auto-generated.
        line_thickness: Thickness of the lines (1-5). Maps to Pillow's MinFilter.
        threshold: Binarization threshold (0-255). Lower values mean fewer lines.
        invert_input: Whether to invert the input image colors before processing.
        
    Returns:
        Path to the saved PNG image.
    """
    src_path = Path(src)
    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src_path}")
        
    if dst is None:
        dst_path = src_path.parent / f"{src_path.stem}_coloring.png"
    else:
        dst_path = Path(dst)

    # 1. Open image and convert to L (grayscale)
    img = Image.open(src_path)
    if img.mode != 'L':
        img = img.convert('L')
        
    if invert_input:
        img = ImageOps.invert(img)

    # 2. Apply SMOOTH to reduce noise
    img = img.filter(ImageFilter.SMOOTH)

    # 3. Apply FIND_EDGES (detects white edges on black background)
    img = img.filter(ImageFilter.FIND_EDGES)

    # 4. Invert to get black edges on white background
    img = ImageOps.invert(img)

    # Apply MinFilter to thicken the black lines (Pillow MinFilter supports size 3 or 5)
    if line_thickness > 0:
        filter_size = 3 if line_thickness <= 2 else 5
        img = img.filter(ImageFilter.MinFilter(size=filter_size))

    # 5. Binarize: force pure black (0) and pure white (255)
    img = img.point(lambda p: 0 if p < threshold else 255)

    # 6. Convert to RGB and save as PNG
    img = img.convert('RGB')
    
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst_path, format="PNG")

    return dst_path


def run_test() -> None:
    """Runs an integrated test using a synthetic image and verifies the output."""
    test_src = Path("test_input_synthetic.png")
    test_dst = Path("test_output_coloring.png")
    
    try:
        # Create a synthetic image: red rectangle on green background
        img = Image.new("RGB", (200, 200), color=(0, 255, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 150, 150], fill=(255, 0, 0))
        img.save(test_src)
        
        # Convert synthetic image
        output_path = convert(test_src, test_dst, line_thickness=2, threshold=128)
        
        # Verify output properties
        out_img = Image.open(output_path)
        assert out_img.mode == "RGB", "Output mode must be RGB"
        
        pixels = list(out_img.getdata())
        unique_colors = set(pixels)
        
        # Ensure only pure black and pure white exist
        for color in unique_colors:
            assert color in [(0, 0, 0), (255, 255, 255)], f"Non B&W pixel found: {color}"
            
        assert (0, 0, 0) in unique_colors, "No black contours detected"
        assert (255, 255, 255) in unique_colors, "No white background detected"
        
        print("OK")
        
    finally:
        # Cleanup test files
        if test_src.exists():
            test_src.unlink()
        if test_dst.exists():
            test_dst.unlink()


def main() -> None:
    if len(sys.argv) == 1:
        run_test()
        sys.exit(0)
        
    parser = argparse.ArgumentParser(description="Convert an image to a line-art coloring page.")
    parser.add_argument("src", help="Path to the source image")
    parser.add_argument("dst", nargs="?", default=None, help="Path to the destination image (optional)")
    parser.add_argument("--thickness", type=int, default=2, help="Line thickness (1-5, default: 2)")
    parser.add_argument("--threshold", type=int, default=128, help="Binarization threshold (0-255, default: 128)")
    parser.add_argument("--invert", action="store_true", help="Invert input image before processing")
    
    args = parser.parse_args()
    
    try:
        out_path = convert(
            src=args.src,
            dst=args.dst,
            line_thickness=args.thickness,
            threshold=args.threshold,
            invert_input=args.invert
        )
        print(f"Success: {out_path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()