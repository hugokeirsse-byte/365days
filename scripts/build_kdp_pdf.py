import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4, letter

# --- Configuration & Constants ---
# Resolve the base directory of the project (assuming script is in scripts/)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PRODUCTS_DIR = BASE_DIR / "products"

BRIEFS_DIR = DATA_DIR / "briefs"
COLORING_BOOKS_GATE1_DIR = PRODUCTS_DIR / "coloring_books" / "_gate1"

DEFAULT_DPI = 300

# --- Helper Functions ---

def parse_inch_value(dim_str: str) -> float:
    """
    Parses a string like '0.125in' or '8.5' into a float representing inches.
    Raises ValueError if the format is invalid.
    """
    dim_str = dim_str.strip().lower()
    if dim_str.endswith('in'):
        try:
            return float(dim_str[:-2])
        except ValueError:
            raise ValueError(f"Invalid numeric value in dimension string: '{dim_str}'")
    try:
        return float(dim_str)
    except ValueError:
        raise ValueError(f"Invalid inch dimension string: '{dim_str}'. Expected 'X.Xin' or 'X.X'")

def parse_trim_format(trim_str: str) -> tuple[float, float]:
    """
    Parses a string like '8.5x11in' into (width_inches, height_inches).
    Raises ValueError if the format is invalid.
    """
    trim_str = trim_str.strip().lower()
    parts = trim_str.replace('in', '').split('x')
    if len(parts) != 2:
        raise ValueError(f"Invalid trim format string: '{trim_str}'. Expected 'WxHin'")
    try:
        width = float(parts[0])
        height = float(parts[1])
        return width, height
    except ValueError:
        raise ValueError(f"Invalid numeric values in trim format: '{trim_str}'")

def load_json_file(filepath: Path) -> dict:
    """Loads a JSON file and returns its content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while loading {filepath}: {e}", file=sys.stderr)
        sys.exit(1)

def get_nested_value(data: dict, keys: str, default=None):
    """Safely retrieves a nested value from a dictionary using a dot-separated key string."""
    keys_list = keys.split('.')
    current_value = data
    for key in keys_list:
        if isinstance(current_value, dict) and key in current_value:
            current_value = current_value[key]
        else:
            return default
    return current_value

# --- Main Script Logic ---

def main():
    parser = argparse.ArgumentParser(
        description="Assembles a KDP-ready interior PDF from line-art pages."
    )
    parser.add_argument(
        "brief_id_arg",
        nargs="?",
        help="Identifier of the brief (e.g., 'my_coloring_book_v1'). Overrides BRIEF_ID env var."
    )
    args = parser.parse_args()

    # Determine BRIEF_ID
    brief_id = args.brief_id_arg or os.getenv("BRIEF_ID")
    if not brief_id:
        print("Error: BRIEF_ID not provided. Use CLI argument or set BRIEF_ID environment variable.", file=sys.stderr)
        sys.exit(1)

    # Determine DPI
    dpi_str = os.getenv("DPI", str(DEFAULT_DPI))
    try:
        dpi = int(dpi_str)
        if dpi <= 0:
            raise ValueError
    except ValueError:
        print(f"Warning: Invalid DPI value '{dpi_str}'. Using default DPI={DEFAULT_DPI}.", file=sys.stderr)
        dpi = DEFAULT_DPI

    print(f"Building KDP PDF for brief: {brief_id} with DPI: {dpi}")

    # --- 1. Load brief for format metadata ---
    brief_path = BRIEFS_DIR / f"{brief_id}.json"
    brief_data = load_json_file(brief_path)

    try:
        trim_format_str = get_nested_value(brief_data, "format.trim")
        bleed_str = get_nested_value(brief_data, "format.bleed")
        pages_interior = get_nested_value(brief_data, "format.pages_interior")

        if not all([trim_format_str, bleed_str, pages_interior is not None]):
            raise ValueError("Missing 'format.trim', 'format.bleed', or 'format.pages_interior' in brief.")

        trim_width_in, trim_height_in = parse_trim_format(trim_format_str)
        bleed_in = parse_inch_value(bleed_str)

    except ValueError as e:
        print(f"Error parsing brief data from {brief_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error accessing brief data from {brief_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # --- 2. Calculate page dimensions in points ---
    # KDP page size includes bleed on all sides
    page_width_pts = (trim_width_in + 2 * bleed_in) * inch
    page_height_pts = (trim_height_in + 2 * bleed_in) * inch

    trim_width_pts = trim_width_in * inch
    trim_height_pts = trim_height_in * inch
    bleed_pts = bleed_in * inch

    print(f"Calculated PDF page size: {page_width_pts:.2f}pt x {page_height_pts:.2f}pt "
          f"({trim_width_in + 2*bleed_in:.2f}in x {trim_height_in + 2*bleed_in:.2f}in)")
    print(f"Trim area: {trim_width_pts:.2f}pt x {trim_height_pts:.2f}pt "
          f"({trim_width_in:.2f}in x {trim_height_in:.2f}in)")
    print(f"Bleed: {bleed_pts:.2f}pt ({bleed_in:.3f}in)")

    # --- Setup paths for input/output ---
    gate1_brief_dir = COLORING_BOOKS_GATE1_DIR / brief_id
    pages_dir = gate1_brief_dir / "pages"
    generation_report_path = gate1_brief_dir / "generation_report.json"
    output_pdf_path = gate1_brief_dir / "interior.pdf"
    kdp_package_path = gate1_brief_dir / "kdp_package.json"

    # Ensure output directory exists
    gate1_brief_dir.mkdir(parents=True, exist_ok=True)

    # --- 3. Load generation_report.json ---
    generation_report_data = load_json_file(generation_report_path)
    pages_ok_indices = sorted(get_nested_value(generation_report_data, "pages_ok", []))
    pages_skipped_indices = get_nested_value(generation_report_data, "pages_skipped", [])

    print(f"Expected interior pages: {pages_interior}")
    print(f"Generated pages (OK): {len(pages_ok_indices)}")
    if pages_skipped_indices:
        print(f"Skipped pages: {len(pages_skipped_indices)}")

    # --- 4. Initialize PDF canvas ---
    c = canvas.Canvas(str(output_pdf_path), pagesize=(page_width_pts, page_height_pts))
    ready_for_gate2 = True
    processed_page_count = 0

    # --- 5. Process each page ---
    for i in range(1, pages_interior + 1):
        page_filename = f"page_{i:03d}.png"
        page_filepath = pages_dir / page_filename

        if i in pages_ok_indices and page_filepath.exists():
            try:
                img = Image.open(page_filepath)
                # KDP requires B&W images to be grayscale (L) or RGB.
                # ReportLab handles RGB better, so convert L to RGB if it's L.
                if img.mode == 'L':
                    img = img.convert('RGB')
                elif img.mode != 'RGB':
                    img = img.convert('RGB') # Ensure it's RGB for consistency

                img_w_px, img_h_px = img.size

                # Calculate scaling to fit image within the trim area while maintaining aspect ratio
                aspect_ratio_img = img_w_px / img_h_px
                aspect_ratio_trim = trim_width_pts / trim_height_pts

                if aspect_ratio_img > aspect_ratio_trim:
                    # Image is wider relative to trim area, fit to trim width
                    scaled_w_pts = trim_width_pts
                    scaled_h_pts = trim_width_pts / aspect_ratio_img
                else:
                    # Image is taller relative to trim area, fit to trim height
                    scaled_h_pts = trim_height_pts
                    scaled_w_pts = trim_height_pts * aspect_ratio_img

                # Calculate position to center the image within the trim area
                x_offset = bleed_pts + (trim_width_pts - scaled_w_pts) / 2
                y_offset = bleed_pts + (trim_height_pts - scaled_h_pts) / 2

                c.drawImage(
                    Image.open(page_filepath), # ReportLab can take a PIL Image object directly
                    x_offset,
                    y_offset,
                    width=scaled_w_pts,
                    height=scaled_h_pts,
                    mask='auto' # Let ReportLab handle transparency if any
                )
                print(f"Added page {i:03d} from {page_filename}")
                processed_page_count += 1

            except Exception as e:
                print(f"Warning: Could not process page {i:03d} ({page_filename}): {e}. Adding blank page.", file=sys.stderr)
                ready_for_gate2 = False
                # Add a blank page to maintain page count
                c.showPage()
                continue # Skip to next page

        else:
            print(f"Warning: Page {i:03d} ({page_filename}) is missing or was skipped. Adding blank page.", file=sys.stderr)
            ready_for_gate2 = False

        c.showPage() # Finalize the current page and move to the next

    # --- 6. Save PDF and write kdp_package.json ---
    c.save()
    print(f"PDF interior saved to {output_pdf_path}")

    # Create kdp_package.json
    kdp_package_data = {
        "built_at": datetime.now().isoformat(),
        "page_count": pages_interior,
        "format": trim_format_str,
        "bleed": bleed_str,
        "ready_for_gate2": ready_for_gate2
    }

    try:
        with open(kdp_package_path, 'w', encoding='utf-8') as f:
            json.dump(kdp_package_data, f, indent=2)
        print(f"KDP package metadata saved to {kdp_package_path}")
    except Exception as e:
        print(f"Error writing KDP package metadata to {kdp_package_path}: {e}", file=sys.stderr)
        sys.exit(1)

    if not ready_for_gate2:
        print("\n--- WARNING ---", file=sys.stderr)
        print("Some pages were missing or could not be processed. 'ready_for_gate2' is set to false.", file=sys.stderr)
        print("Please review the warnings above.", file=sys.stderr)
        sys.exit(1) # Indicate a non-zero exit for CI/CD if not ready

    print("\nKDP PDF build completed successfully.")


if __name__ == "__main__":
    main()