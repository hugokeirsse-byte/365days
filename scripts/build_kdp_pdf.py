import os
import json
import argparse
import logging
import sys
from datetime import datetime

# External dependencies
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch # 1 inch = 72 points

# --- Configuration ---
# Determine the project root based on the script's location
# Assuming scripts/build_kdp_pdf.py is in PROJECT_ROOT/scripts/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(BASE_DIR, '..', '..') 

DATA_BRIEFS_PATH = os.path.join(PROJECT_ROOT, 'data', 'briefs')
PRODUCTS_GATE1_PATH = os.path.join(PROJECT_ROOT, 'products', 'coloring_books', '_gate1')

DEFAULT_DPI = 300

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def build_kdp_pdf(brief_id: str, dpi: int):
    """
    Assembles a KDP-ready interior PDF from line-art pages.
    Reads brief for format metadata and generation report for page status.
    Generates a PDF with bleed and a KDP package metadata file.
    """
    logger.info(f"Starting KDP PDF build for BRIEF_ID: {brief_id} with target DPI: {dpi}")

    # --- 1. Load brief for format metadata ---
    brief_file_path = os.path.join(DATA_BRIEFS_PATH, f"{brief_id}.json")
    try:
        with open(brief_file_path, 'r', encoding='utf-8') as f:
            brief_data = json.load(f)
        
        trim_format = brief_data.get('format', {}).get('trim')
        bleed_inches = brief_data.get('format', {}).get('bleed')
        pages_interior_expected = brief_data.get('format', {}).get('pages_interior')

        if not all([trim_format, bleed_inches is not None, pages_interior_expected is not None]):
            raise ValueError("Missing 'format.trim', 'format.bleed', or 'format.pages_interior' in brief.")
        
        trim_width_inches = trim_format.get('width')
        trim_height_inches = trim_format.get('height')

        if not all([trim_width_inches, trim_height_inches]):
            raise ValueError("Missing 'format.trim.width' or 'format.trim.height' in brief.")

        logger.info(f"Brief loaded: Trim {trim_width_inches}x{trim_height_inches} inches, Bleed {bleed_inches} inches, Expected pages {pages_interior_expected}")

    except FileNotFoundError:
        logger.error(f"Brief file not found: {brief_file_path}. Please ensure the brief ID is correct.")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from brief file: {brief_file_path}. Check file integrity.")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid brief data in {brief_file_path}: {e}")
        sys.exit(1)

    # --- 2. Calculate PDF page dimensions (including bleed) ---
    pdf_page_width_inches = trim_width_inches + (2 * bleed_inches)
    pdf_page_height_inches = trim_height_inches + (2 * bleed_inches)

    pdf_page_width_pts = pdf_page_width_inches * inch
    pdf_page_height_pts = pdf_page_height_inches * inch

    logger.info(f"Calculated PDF page size: {pdf_page_width_inches:.3f}x{pdf_page_height_inches:.3f} inches ({pdf_page_width_pts:.2f}x{pdf_page_height_pts:.2f} points)")

    # --- Define paths for current brief_id ---
    brief_output_dir = os.path.join(PRODUCTS_GATE1_PATH, brief_id)
    pages_input_dir = os.path.join(brief_output_dir, 'pages')
    generation_report_path = os.path.join(brief_output_dir, 'generation_report.json')
    output_pdf_path = os.path.join(brief_output_dir, 'interior.pdf')
    kdp_package_path = os.path.join(brief_output_dir, 'kdp_package.json')

    # Ensure the output directory for the brief exists
    os.makedirs(brief_output_dir, exist_ok=True)

    # --- 3. Load generation_report.json to get available pages ---
    generated_pages_info = []
    try:
        with open(generation_report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        # Filter for pages with 'ok' status and sort them by index
        generated_pages_info = sorted(
            [p for p in report_data.get('pages', []) if p.get('status') == 'ok'],
            key=lambda x: x['index']
        )
        logger.info(f"Generation report loaded. Found {len(generated_pages_info)} 'ok' pages.")

    except FileNotFoundError:
        logger.error(f"Generation report not found: {generation_report_path}. Cannot build PDF without page information.")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from generation report: {generation_report_path}. Check file integrity.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading generation report: {e}")
        sys.exit(1)

    # Create a set of available page indices for efficient lookup
    available_page_indices = {p['index'] for p in generated_pages_info}
    
    # --- 4. Initialize PDF Canvas ---
    c = canvas.Canvas(output_pdf_path, pagesize=(pdf_page_width_pts, pdf_page_height_pts))
    logger.info(f"PDF canvas initialized for output: {output_pdf_path}")

    successful_png_pages_count = 0
    missing_pages_detected = False

    # --- 5. Process each expected page ---
    # Iterate through the expected number of pages from the brief
    for i in range(pages_interior_expected):
        page_index = i + 1 # Page filenames are 1-indexed (e.g., page_001.png)
        png_filename = f"page_{page_index:03d}.png"
        png_path = os.path.join(pages_input_dir, png_filename)

        if page_index in available_page_indices:
            try:
                img = Image.open(png_path)
                # Convert image to grayscale ('L') then to RGB.
                # ReportLab's drawImage works best with RGB/RGBA images,
                # and 'L' ensures the content is truly B&W before conversion to 3-channel RGB.
                img_rgb = img.convert('L').convert('RGB') 

                # The PNG image is assumed to represent the content for the TRIM area.
                # Calculate its drawing dimensions in points.
                img_draw_width_pts = trim_width_inches * inch
                img_draw_height_pts = trim_height_inches * inch

                # Calculate the position to center the image within the PDF page.
                # The image should start at (bleed_inches * inch, bleed_inches * inch)
                # from the bottom-left of the PDF page, effectively placing the trim content.
                x_offset_pts = bleed_inches * inch
                y_offset_pts = bleed_inches * inch

                c.drawImage(
                    img_rgb, 
                    x_offset_pts, 
                    y_offset_pts, 
                    width=img_draw_width_pts, 
                    height=img_draw_height_pts, 
                    mask='auto' # Let ReportLab handle transparency if present
                )
                c.showPage() # Finalize the current page and move to the next
                successful_png_pages_count += 1
                logger.debug(f"Added page {page_index} from {png_filename}")

            except FileNotFoundError:
                logger.warning(f"PNG file not found for page {page_index}: {png_path}. Adding a blank page to maintain count.")
                c.showPage() # Add a blank page if PNG is missing
                missing_pages_detected = True
            except Exception as e:
                logger.error(f"Error processing page {page_index} from {png_path}: {e}. Adding a blank page.")
                c.showPage() # Add a blank page on other errors
                missing_pages_detected = True
        else:
            logger.warning(f"Page {page_index} (expected {png_filename}) not found in generation report as 'ok'. Adding a blank page.")
            c.showPage() # Add a blank page if not marked 'ok' in report
            missing_pages_detected = True
    
    # --- 6. Save PDF ---
    try:
        c.save()
        logger.info(f"PDF successfully saved to {output_pdf_path}")
    except Exception as e:
        logger.error(f"Error saving PDF to {output_pdf_path}: {e}")
        sys.exit(1)

    # --- Write kdp_package.json ---
    # The page_count in kdp_package.json should reflect the total pages in the PDF,
    # which is pages_interior_expected, even if some are blank.
    kdp_package_data = {
        "built_at": datetime.now().isoformat(),
        "page_count": pages_interior_expected, 
        "format": f"{trim_width_inches}x{trim_height_inches}in",
        "bleed": f"{bleed_inches}in",
        "ready_for_gate2": not missing_pages_detected
    }

    # If the number of successfully processed PNGs is less than expected,
    # it means some pages were skipped or errored, so it's not ready for Gate 2.
    if successful_png_pages_count < pages_interior_expected:
        kdp_package_data["ready_for_gate2"] = False
        logger.warning(f"Only {successful_png_pages_count} out of {pages_interior_expected} pages were successfully built from PNGs. "
                       f"{pages_interior_expected - successful_png_pages_count} pages are blank in the PDF.")
    
    try:
        with open(kdp_package_path, 'w', encoding='utf-8') as f:
            json.dump(kdp_package_data, f, indent=4)
        logger.info(f"KDP package metadata saved to {kdp_package_path}")
        if not kdp_package_data["ready_for_gate2"]:
            logger.warning("KDP package is NOT ready for Gate 2 due to missing or errored pages. Review logs for details.")
    except Exception as e:
        logger.error(f"Error saving KDP package metadata to {kdp_package_path}: {e}")
        sys.exit(1)

    logger.info(f"KDP PDF build finished for BRIEF_ID: {brief_id}. Ready for Gate 2: {kdp_package_data['ready_for_gate2']}")


def main():
    parser = argparse.ArgumentParser(
        description="Assemble a KDP-ready interior PDF from line-art pages.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "brief_id",
        nargs='?', # Make it optional, so it can be read from env var
        help="Identifier of the brief (e.g., 'my_coloring_book_v1').\n"
             "If not provided, will try to read from BRIEF_ID environment variable."
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=None, # Use None to distinguish from DEFAULT_DPI
        help=f"Target resolution in DPI (default: {DEFAULT_DPI}).\n"
             "If not provided, will try to read from DPI environment variable."
    )

    args = parser.parse_args()

    # Determine BRIEF_ID: CLI argument takes precedence, then environment variable
    brief_id = args.brief_id or os.environ.get('BRIEF_ID')
    if not brief_id:
        logger.error("BRIEF_ID is required. Please provide it as a CLI argument or set the BRIEF_ID environment variable.")
        sys.exit(1)

    # Determine DPI: CLI argument takes precedence, then environment variable, then default
    dpi = args.dpi or int(os.environ.get('DPI', DEFAULT_DPI))

    build_kdp_pdf(brief_id, dpi)

if __name__ == "__main__":
    main()