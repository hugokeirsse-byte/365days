import os
import sys
import json
from pathlib import Path

# Setup ROOT and import paths
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

try:
    from lib.image_router import generate as ir_generate
    from lib.image_to_coloring import convert as coloring_convert
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    print("Please ensure scripts/lib/image_router.py and scripts/lib/image_to_coloring.py exist.", file=sys.stderr)
    sys.exit(1)


def main():
    # 1. Retrieve and validate environment variables
    brief_id = os.environ.get("BRIEF_ID")
    if not brief_id:
        print("Error: BRIEF_ID environment variable is required.", file=sys.stderr)
        sys.exit(1)

    try:
        line_thickness = int(os.environ.get("LINE_THICKNESS", "2"))
    except ValueError:
        line_thickness = 2

    max_pages = None
    max_pages_env = os.environ.get("MAX_PAGES")
    if max_pages_env:
        try:
            max_pages = int(max_pages_env)
        except ValueError:
            print(f"Warning: Invalid MAX_PAGES value '{max_pages_env}', ignoring limit.", file=sys.stderr)

    # Define paths
    brief_path = ROOT / "data" / "briefs" / f"{brief_id}.json"
    gate1_dir = ROOT / "products" / "coloring_books" / "_gate1" / brief_id
    plan_path = gate1_dir / "production_plan.json"
    pages_dir = gate1_dir / "pages"
    report_path = gate1_dir / "generation_report.json"

    # 2. Verify brief approval status
    if not brief_path.exists():
        print(f"Error: Brief file not found at {brief_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(brief_path, "r", encoding="utf-8") as f:
            brief_data = json.load(f)
    except Exception as e:
        print(f"Error reading brief file: {e}", file=sys.stderr)
        sys.exit(1)

    gate_start = brief_data.get("gate_start") or brief_data.get("status")
    if gate_start != "approved":
        print(f"Error: Brief {brief_id} is not approved (gate_start={gate_start}). Aborting.", file=sys.stderr)
        sys.exit(1)

    # 3. Read production plan
    if not plan_path.exists():
        print(f"Error: Production plan not found at {plan_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
    except Exception as e:
        print(f"Error reading production plan: {e}", file=sys.stderr)
        sys.exit(1)

    pages_dir.mkdir(parents=True, exist_ok=True)

    pages_to_process = plan_data.get("pages", [])
    if max_pages is not None:
        pages_to_process = pages_to_process[:max_pages]

    report_pages = []
    summary = {"ok": 0, "failed": 0}

    # 4. Process standard coloring pages
    for page in pages_to_process:
        index = page.get("index")
        prompt = page.get("prompt")
        neg_prompt = page.get("negative_prompt")

        if index is None or not prompt:
            print(f"Warning: Skipping invalid page entry: {page}", file=sys.stderr)
            continue

        dest_file = pages_dir / f"page_{index:03d}.png"
        tmp_file = pages_dir / f"tmp_page_{index:03d}.png"

        # Idempotency check
        if dest_file.exists() and dest_file.stat().st_size > 0:
            print(f"Page {index:03d} already exists. Skipping.")
            report_pages.append({
                "page_number": index,
                "status": "skipped",
                "provider_used": "cache"
            })
            summary["ok"] += 1
            continue

        print(f"Generating page {index:03d}...")
        provider_used = "unknown"
        status = "failed"

        try:
            # Generate raw image
            res = ir_generate(
                prompt=prompt,
                negative_prompt=neg_prompt,
                width=832,
                height=1152,
                dest=str(tmp_file)
            )

            # Extract provider if returned by router
            if isinstance(res, dict):
                provider_used = res.get("provider", "unknown")
            elif isinstance(res, str) and res:
                provider_used = res

            if tmp_file.exists() and tmp_file.stat().st_size > 0:
                # Convert raw image to line-art
                coloring_convert(str(tmp_file), str(dest_file), line_thickness=line_thickness)

                if dest_file.exists() and dest_file.stat().st_size > 0:
                    status = "ok"
                    print(f"Successfully generated and converted page {index:03d}")
                else:
                    print(f"Failed to convert page {index:03d} to line-art.", file=sys.stderr)
            else:
                print(f"Failed to generate raw image for page {index:03d}.", file=sys.stderr)

        except Exception as e:
            print(f"Exception occurred while processing page {index:03d}: {e}", file=sys.stderr)
        finally:
            # Clean up intermediate raw file
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass

        report_pages.append({
            "page_number": index,
            "status": status,
            "provider_used": provider_used
        })
        if status == "ok":
            summary["ok"] += 1
        else:
            summary["failed"] += 1

    # 5. Process covers (Front & Back)
    covers = plan_data.get("covers", {})
    for cover_type in ["front", "back"]:
        cover_info = covers.get(cover_type)
        if not cover_info:
            continue

        prompt = cover_info.get("prompt")
        neg_prompt = cover_info.get("negative_prompt")
        if not prompt:
            continue

        dest_file = pages_dir / f"cover_{cover_type}.png"

        # Idempotency check
        if dest_file.exists() and dest_file.stat().st_size > 0:
            print(f"Cover {cover_type} already exists. Skipping.")
            report_pages.append({
                "page_number": f"cover_{cover_type}",
                "status": "skipped",
                "provider_used": "cache"
            })
            summary["ok"] += 1
            continue

        print(f"Generating cover {cover_type}...")
        provider_used = "unknown"
        status = "failed"

        try:
            # Covers are generated directly in color (no line-art conversion)
            res = ir_generate(
                prompt=prompt,
                negative_prompt=neg_prompt,
                width=2625,
                height=3375,
                dest=str(dest_file)
            )

            if isinstance(res, dict):
                provider_used = res.get("provider", "unknown")
            elif isinstance(res, str) and res:
                provider_used = res

            if dest_file.exists() and dest_file.stat().st_size > 0:
                status = "ok"
                print(f"Successfully generated cover {cover_type}")
            else:
                print(f"Failed to generate cover {cover_type}.", file=sys.stderr)

        except Exception as e:
            print(f"Exception occurred while processing cover {cover_type}: {e}", file=sys.stderr)

        report_pages.append({
            "page_number": f"cover_{cover_type}",
            "status": status,
            "provider_used": provider_used
        })
        if status == "ok":
            summary["ok"] += 1
        else:
            summary["failed"] += 1

    # 6. Write generation report
    report = {
        "pages": report_pages,
        "summary": {
            "ok": summary["ok"],
            "failed": summary["failed"]
        }
    }

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"Generation report successfully written to {report_path}")
    except Exception as e:
        print(f"Error writing generation report: {e}", file=sys.stderr)

    # Exit 0 even if there are partial generation failures
    sys.exit(0)


if __name__ == "__main__":
    main()