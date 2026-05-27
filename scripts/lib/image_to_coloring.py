import argparse
import sys
from pathlib import Path
import tempfile
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
    Converts a color or grayscale image into a clean, black-and-white line-art coloring page.
    
    Args:
        src: Path to the source image.
        dst: Path to the destination image. If None, saves as <src_stem>_coloring.png.
        line_thickness: Thickness of the lines (maps to MinFilter size).
        threshold: Binarization threshold (0-255).
        invert_input: Whether to invert the input image before processing.
        
    Returns:
        Path to the saved destination image.
    """
    src_path = Path(src)
    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src_path}")
    
    if dst is None:
        dst_path = src_path.parent / f"{src_path.stem}_coloring.png"
    else:
        dst_path = Path(dst)
        
    # Ensure destination directory exists
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Open image and convert to grayscale (L)
    with Image.open(src_path) as img:
        img_l = img.convert("L")
        
    if invert_input:
        img_l = ImageOps.invert(img_l)
        
    # 2. Apply SMOOTH to reduce noise
    img_smooth = img_l.filter(ImageFilter.SMOOTH)
    
    # 3. Apply FIND_EDGES (detects boundaries as white lines on black background)
    edges = img_smooth.filter(ImageFilter.FIND_EDGES)
    
    # 4. Invert to get black lines on white background
    edges_inv = ImageOps.invert(edges)
    
    # Apply MinFilter to thicken the black lines (minimum filter expands dark regions)
    if line_thickness > 1:
        # MinFilter size must be an odd integer >= 3
        size = line_thickness if line_thickness % 2 != 0 else line_thickness + 1
        if size < 3:
            size = 3
        edges_inv = edges_inv.filter(ImageFilter.MinFilter(size=size))
        
    # 5 & 6. Binarize: force pure white (255) and pure black (0)
    binarized = edges_inv.point(lambda p: 0 if p < threshold else 255)
    
    # 7. Convert to RGB and save as PNG
    output_rgb = binarized.convert("RGB")
    output_rgb.save(dst_path, "PNG")
    
    return dst_path

def run_self_test() -> None:
    """
    Runs an integrated self-test using a synthetic image.
    Prints 'OK' if successful, otherwise raises an exception.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        src_test = tmp_path / "test_input.png"
        dst_test = tmp_path / "test_output.png"
        
        # Create a synthetic image: green background with a red rectangle
        img = Image.new("RGB", (200, 200), color=(0, 255, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 150, 150], fill=(255, 0, 0))
        img.save(src_test)
        
        # Convert synthetic image
        convert(src_test, dst_test, line_thickness=2, threshold=128)
        
        # Verify output exists and is strictly black and white
        if not dst_test.exists():
            raise AssertionError("Output file was not created.")
            
        with Image.open(dst_test) as out_img:
            if out_img.mode != "RGB":
                raise AssertionError(f"Expected RGB mode, got {out_img.mode}")
            
            colors = out_img.getcolors()
            if not colors:
                raise AssertionError("Could not retrieve image colors.")
                
            for _, color in colors:
                if color not in [(0, 0, 0), (255, 255, 255)]:
                    raise AssertionError(f"Non-B&W color detected in output: {color}")
                    
        print("OK")

if __name__ == "__main__":
    # If run without arguments, execute the self-test
    if len(sys.argv) == 1:
        run_self_test()
        sys.exit(0)
        
    parser = argparse.ArgumentParser(description="Convert an image to a clean line-art coloring page.")
    parser.add_argument("src", help="Path to the source image")
    parser.add_argument("dst", nargs="?", default=None, help="Path to the destination image (optional)")
    parser.add_argument("--thickness", type=int, default=2, help="Line thickness (default: 2)")
    parser.add_argument("--threshold", type=int, default=128, help="Binarization threshold 0-255 (default: 128)")
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