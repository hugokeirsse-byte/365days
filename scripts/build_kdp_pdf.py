import os
import sys
import json
from datetime import datetime
from pathlib import Path

from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# --- Constants ---
POINTS_PER_INCH = 72
DEFAULT_DPI = 300

# --- Helper Functions ---
def get_brief_id():
    """
    Retrieves BRIEF_ID from CLI arguments or environment variables.
    CLI argument takes precedence.
    """
    if len(sys.argv) > 1:
        return sys.argv[1]
    brief_id = os.environ.get("BRIEF_ID")
    if not brief_id:
        raise ValueError(
            "BRIEF_ID not provided. "
            "Use: python scripts/build_kdp_pdf.py [BRIEF_ID] "
            "or set BRIEF_ID environment variable."
        )
    return brief_id

def get_dpi():
    """
    Retrieves DPI from environment variables or uses default.
    """
    try:
        return int(os.environ.get("DPI", DEFAULT_DPI))
    except ValueError:
        print(f"Warning: Invalid DPI environment variable. Using default {DEFAULT_DPI}.", file=sys.stderr)
        return DEFAULT_DPI

def load_json_file(filepath):
    """
    Loads a JSON file from the given path.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Required file not found: {filepath}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in file: {filepath}")

def save_json_file(filepath, data):
    """
    Saves data to a JSON file, creating parent directories if necessary.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def main():
    brief_id = get_brief_id()
    dpi = get_dpi()

    print(f"Starting KDP PDF build for brief ID: {brief_id} with DPI: {dpi}")

    # --- 1. Load brief for format metadata ---
    brief_path = Path(f"data/briefs/{brief_id}.json")
    brief_data = load_json_file(brief_path)

    try:
        trim_width_in = brief_data['format']['trim']['width']
        trim_height_in = brief_data['format']['trim']['height']
        bleed_in = brief_data['format']['bleed']
        pages_interior_expected = brief_data['format']['pages_interior']
    except KeyError as e:
        raise ValueError(f"Missing expected key in brief data from {brief_path}: {e}")

    # --- 2. Calculate PDF page dimensions (trim + 2*bleed) ---
    page_w_in = trim_width_in + 2 * bleed_in
    page_h_in = trim_height_in + 2 * bleed_in

    page_w_pt = page_w_in * POINTS_PER_INCH
    page_h_pt = page_h_in * POINTS_PER_INCH

    print(f"Calculated PDF page size: {page_w_in:.3f}x{page_h_in:.3f} inches ({page_w_pt:.2f}x{page_h_pt:.2f} points)")

    # --- 3. Load generation_report.json ---
    generation_report_path = Path(f"products/coloring_books/_gate1/{brief_id}/generation_report.json")
    generation_report_data = load_json_file(generation_report_path)

    # Filter for 'ok' pages and sort by index to ensure correct order
    ok_pages = sorted(
        [p for p in generation_report_data.get('pages', []) if p.get('status') == 'ok'],
        key=lambda x: x['index']
    )
    actual_page_count = len(ok_pages)
    print(f"Found {actual_page_count} 'ok' pages from generation report. Expected: {pages_interior_expected}")

    # --- 4. Initialize PDF Canvas ---
    output_base_dir = Path(f"products/coloring_books/_gate1/{brief_id}")
    output_base_dir.mkdir(parents=True, exist_ok=True) # Ensure output directory exists
    output_pdf_path = output_base_dir / "interior.pdf"

    c = canvas.Canvas(str(output_pdf_path), pagesize=(page_w_pt, page_h_pt))
    c.setCreator("KDP PDF Builder Script")
    c.setTitle(f"Interior for {brief_id}")

    # --- 5. Process each page ---
    for page_info in ok_pages:
        page_index = page_info['index']
        png_path = output_base_dir / "pages" / f"page_{page_index:03d}.png"

        if not png_path.exists():
            print(f"Warning: PNG file not found for page {page_index:03d} at {png_path}. Skipping this page.", file=sys.stderr)
            continue

        try:
            # Open PNG image
            img = Image.open(png_path)
            # Convert to grayscale (L) then to RGB. ReportLab's ImageReader
            # works best with RGB/RGBA images, even for B&W content.
            img = img.convert('L').convert('RGB')

            img_w_px, img_h_px = img.size

            # Calculate image dimensions in points based on its pixel size and DPI
            # This assumes the PNG's pixel dimensions correspond to its intended
            # physical size at the given DPI (e.g., 8.5in * 300dpi = 2550px)
            draw_w_pt = (img_w_px / dpi) * POINTS_PER_INCH
            draw_h_pt = (img_h_px / dpi) * POINTS_PER_INCH

            # Calculate offsets to center the image on the PDF page
            # The image content will be centered within the total page size (trim + bleed)
            x_offset = (page_w_pt - draw_w_pt) / 2
            y_offset = (page_h_pt - draw_h_pt) / 2

            # Draw the image onto the canvas
            c.drawImage(ImageReader(img), x_offset, y_offset, width=draw_w_pt, height=draw_h_pt)
            c.showPage() # Marks the end of the current page and starts a new one
            print(f"Added page {page_index:03d} from {png_path} to PDF.")

        except Exception as e:
            print(f"Error processing page {page_index:03d} from {png_path}: {e}", file=sys.stderr)
            # Continue processing other pages even if one fails

    # --- 6. Save PDF and write kdp_package.json ---
    c.save()
    print(f"PDF interior saved to: {output_pdf_path}")

    # Determine if the package is ready for gate2 based on page count
    ready_for_gate2 = (actual_page_count == pages_interior_expected)
    if not ready_for_gate2:
        print(f"Warning: Page count mismatch. Expected {pages_interior_expected}, got {actual_page_count}. Setting ready_for_gate2 to false.", file=sys.stderr)

    kdp_package_data = {
        "built_at": datetime.now().isoformat(),
        "page_count": actual_page_count,
        "format": f"{trim_width_in}x{trim_height_in}in",
        "bleed": f"{bleed_in}in",
        "ready_for_gate2": ready_for_gate2
    }
    kdp_package_path = output_base_dir / "kdp_package.json"
    save_json_file(kdp_package_path, kdp_package_data)
    print(f"KDP package metadata saved to: {kdp_package_path}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An unhandled error occurred: {e}", file=sys.stderr)
        sys.exit(1)