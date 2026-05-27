import os
import sys
import json
import tempfile
from pathlib import Path

# Setup root path and import custom modules
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

from lib.image_router import generate as ir_generate
from lib.image_to_coloring import convert as coloring_convert

def main():
    # 1. Retrieve and validate environment variables
    brief_id = os.environ.get("BRIEF_ID")
    if not brief_id:
        print("Error: BRIEF_ID environment variable is required.", file=sys.stderr)
        sys.exit(1)

    line_thickness = int(os.environ.get("LINE_THICKNESS", 2))
    max_pages_env = os.environ.get("MAX_PAGES")
    max_pages = int(max_pages_env) if max_pages_env else None

    # 2. Verify brief status (gate_start == approved)
    brief_path = ROOT / "data" / "briefs" / f"{brief_id}.json"
    if not brief_path.exists():
        print(f"Error: Brief file not found at {brief_path}", file=sys.stderr)
        sys.exit(1)

    with open(brief_path, "r", encoding="utf-8") as f:
        brief_data = json.load(f)

    gate_start = brief_data.get("gate_start")
    status = brief_data.get("status")
    if gate_start != "approved" and status != "approved":
        print(f"Error: Brief {brief_id} is not approved (gate_start={gate_start}, status={status}).", file=sys.stderr)
        sys.exit(1)

    # 3. Load production plan
    plan_path = ROOT / "products" / "coloring_books" / "_gate1" / brief_id / "production_plan.json"
    if not plan_path.exists():
        print(f"Error: Production plan not found at {plan_path}", file=sys.stderr)
        sys.exit(1)

    with open(plan_path, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    pages_dir = ROOT / "products" / "coloring_books" / "_gate1" / brief_id / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    pages_to_process = plan_data.get("pages", [])
    if max_pages is not None:
        pages_to_process = pages_to_process[:max_pages]

    report_pages = []
    summary = {"ok": 0, "failed": 0, "skipped": 0}

    # Standard negative prompt for coloring pages to ensure clean line art
    default_neg_prompt = "color, shading, grayscale, shadows, gradients, realistic, photo, dark background, blurry, textured"

    # 4. Process each page
    for page in pages_to_process:
        idx = page.get("index")
        prompt = page.get("prompt")
        if not prompt:
            print(f"Warning: Page {idx} has no prompt. Skipping.")
            continue

        out_filename = f"page_{idx:03d}.png"
        out_path = pages_dir / out_filename

        # Idempotency check
        if out_path.exists():
            print(f"Page {idx} already exists at {out_path}. Skipping.")
            report_pages.append({
                "page_number": idx,
                "status": "skipped",
                "provider_used": "none"
            })
            summary["skipped"] += 1
            continue

        print(f"Generating page {idx}...")
        
        # Create a temporary file for the raw generated image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Generate raw image using the image router
            provider = ir_generate(
                prompt=prompt,
                negative_prompt=default_neg_prompt,
                width=832,
                height=1152,
                dest=str(tmp_path)
            )

            if provider and tmp_path.exists() and tmp_path.stat().st_size > 0:
                # Convert raw image to clean line-art
                coloring_convert(str(tmp_path), str(out_path), line_thickness=line_thickness)
                print(f"Successfully generated and converted page {idx} using {provider}")
                report_pages.append({
                    "page_number": idx,
                    "status": "ok",
                    "provider_used": provider
                })
                summary["ok"] += 1
            else: 
                raise Exception("Image router returned empty file or failed.")

        except Exception as e:
            print(f"Error generating page {idx}: {e}", file=sys.stderr)
            report_pages.append({
                "page_number": idx,
                "status": "failed",
                "provider_used": "none"
            })
            summary["failed"] += 1
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass

    # 5. Process covers (Front and Back)
    covers = plan_data.get("covers", {})
    for cover_type in ["front", "back"]:
        cover_info = covers.get(cover_type)
        if not cover_info:
            continue

        prompt = cover_info.get("prompt")
        if not prompt:
            continue

        out_filename = f"cover_{cover_type}.png"
        out_path = pages_dir / out_filename

        # Idempotency check for covers
        if out_path.exists():
            print(f"Cover {cover_type} already exists. Skipping.")
            report_pages.append({
                "page_number": f"cover_{cover_type}",
                "status": "skipped",
                "provider_used": "none"
            })
            summary["skipped"] += 1
            continue

        print(f"Generating cover {cover_type}...")
        try:
            # Covers are generated in color directly to the destination (no line-art conversion)
            provider = ir_generate(
                prompt=prompt,
                negative_prompt="blurry, low quality, low resolution, distorted",
                width=2625,
                height=3375,
                dest=str(out_path)
            )
            if provider and out_path.exists() and out_path.stat().st_size > 0:
                print(f"Successfully generated cover {cover_type} using {provider}")
                report_pages.append({
                    "page_number": f"cover_{cover_type}",
                    "status": "ok",
                    "provider_used": provider
                })
                summary["ok"] += 1
            else:
                raise Exception("Cover generation failed or returned empty file.")
        except Exception as e:
            print(f"Error generating cover {cover_type}: {e}", file=sys.stderr)
            report_pages.append({
                "page_number": f"cover_{cover_type}",
                "status": "failed",
                "provider_used": "none"
            })
            summary["failed"] += 1

    # 6. Write generation report
    report_path = ROOT / "products" / "coloring_books" / "_gate1" / brief_id / "generation_report.json"
    report_data = {
        "pages": report_pages,
        "summary": {
            "ok": summary["ok"],
            "failed": summary["failed"],
            "skipped": summary["skipped"]
        }
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"Generation report written to {report_path}")
    print(f"Summary: {summary}")

if __name__ == "__main__":
    main()
