import os
import sys
import json
import logging
from pathlib import Path

# Setup paths and imports
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

from lib.image_router import generate as ir_generate
from lib.image_to_coloring import convert as coloring_convert

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("generate_from_plan")

def main():
    # 1. Retrieve and validate environment variables
    brief_id = os.environ.get("BRIEF_ID")
    if not brief_id:
        logger.error("BRIEF_ID environment variable is required.")
        sys.exit(1)

    line_thickness = int(os.environ.get("LINE_THICKNESS", "2"))
    max_pages_env = os.environ.get("MAX_PAGES")
    max_pages = int(max_pages_env) if max_pages_env else None

    # Define paths
    brief_path = ROOT / "data" / "briefs" / f"{brief_id}.json"
    gate1_dir = ROOT / "products" / "coloring_books" / "_gate1" / brief_id
    plan_path = gate1_dir / "production_plan.json"
    pages_dir = gate1_dir / "pages"
    report_path = gate1_dir / "generation_report.json"

    # 2. Verify gate_start == approved
    if not brief_path.exists():
        logger.error(f"Brief file not found: {brief_path}")
        sys.exit(1)

    try:
        with open(brief_path, "r", encoding="utf-8") as f:
            brief_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read brief file: {e}")
        sys.exit(1)

    gate_start = brief_data.get("gate_start") or brief_data.get("status")
    if gate_start != "approved":
        logger.error(f"Brief status is '{gate_start}', must be 'approved' to generate.")
        sys.exit(1)

    # 3. Read production plan
    if not plan_path.exists():
        logger.error(f"Production plan not found: {plan_path}")
        sys.exit(1)

    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read production plan: {e}")
        sys.exit(1)

    pages_dir.mkdir(parents=True, exist_ok=True)

    # Initialize report structure
    report = {
        "pages": [],
        "summary": {
            "ok": 0,
            "failed": 0,
            "skipped": 0
        }
    }

    # Standard negative prompt for coloring book pages
    default_negative_prompt = (
        "shading, gradients, shadows, realistic, photo, color, grayscale, "
        "blurry, textured, background noise, dark fills"
    )

    # 4. Process Pages
    pages_list = plan_data.get("pages", [])
    if max_pages is not None:
        logger.info(f"Limiting generation to {max_pages} pages (MAX_PAGES set).")
        pages_list = pages_list[:max_pages]

    for page in pages_list:
        index = page.get("index")
        prompt = page.get("prompt")
        
        if index is None or not prompt:
            logger.warning(f"Skipping invalid page entry: {page}")
            continue

        page_filename = f"page_{index:03d}.png"
        dest_path = pages_dir / page_filename
        tmp_path = pages_dir / f"tmp_page_{index:03d}.png"

        # Idempotency check
        if dest_path.exists():
            logger.info(f"Page {index:03d} already exists. Skipping.")
            report["pages"].append({
                "page_number": index,
                "status": "skipped",
                "provider_used": "existing"
            })
            report["summary"]["skipped"] += 1
            continue

        logger.info(f"Generating page {index:03d}...")
        try:
            # Generate raw image
            ir_generate(
                prompt=prompt,
                negative_prompt=default_negative_prompt,
                width=832,
                height=1152,
                dest=str(tmp_path)
            )

            if tmp_path.exists():
                # Convert to line-art
                coloring_convert(
                    input_path=str(tmp_path),
                    output_path=str(dest_path),
                    line_thickness=line_thickness
                )
                
                report["pages"].append({
                    "page_number": index,
                    "status": "ok",
                    "provider_used": "router_default"
                })
                report["summary"]["ok"] += 1
                logger.info(f"Successfully generated and converted page {index:03d}.")
            else:
                raise FileNotFoundError("Temporary generated image not found.")

        except Exception as e:
            logger.error(f"Failed to generate page {index:03d}: {e}")
            report["pages"].append({
                "page_number": index,
                "status": "failed",
                "provider_used": "none"
            })
            report["summary"]["failed"] += 1
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete temporary file {tmp_path}: {e}")

    # 5. Process Covers (Front & Back)
    covers = plan_data.get("covers", {})
    for cover_key in ["front", "back"]:
        cover_data = covers.get(cover_key)
        if not cover_data:
            continue

        prompt = cover_data.get("prompt")
        if not prompt:
            logger.warning(f"No prompt found for cover_{cover_key}.")
            continue

        dest_path = pages_dir / f"cover_{cover_key}.png"
        tmp_path = pages_dir / f"tmp_cover_{cover_key}.png"

        # Idempotency check
        if dest_path.exists():
            logger.info(f"Cover {cover_key} already exists. Skipping.")
            report["pages"].append({
                "page_number": f"cover_{cover_key}",
                "status": "skipped",
                "provider_used": "existing"
            })
            report["summary"]["skipped"] += 1
            continue

        logger.info(f"Generating cover {cover_key} (KDP 300DPI)...")
        try:
            # Covers are generated in color, no line-art conversion needed
            ir_generate(
                prompt=prompt,
                width=2625,
                height=3375,
                dest=str(tmp_path)
            )

            if tmp_path.exists():
                tmp_path.rename(dest_path)
                report["pages"].append({
                    "page_number": f"cover_{cover_key}",
                    "status": "ok",
                    "provider_used": "router_default"
                })
                report["summary"]["ok"] += 1
                logger.info(f"Successfully generated cover {cover_key}.")
            else:
                raise FileNotFoundError("Temporary cover image not found.")

        except Exception as e:
            logger.error(f"Failed to generate cover {cover_key}: {e}")
            report["pages"].append({
                "page_number": f"cover_{cover_key}",
                "status": "failed",
                "provider_used": "none"
            })
            report["summary"]["failed"] += 1
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete temporary file {tmp_path}: {e}")

    # 6. Write Generation Report
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Generation report written to {report_path}")
    except Exception as e:
        logger.error(f"Failed to write generation report: {e}")

    # Exit 0 even if partial failures occurred, as requested
    logger.info("Generation process completed.")
    sys.exit(0)

if __name__ == "__main__":
    main()