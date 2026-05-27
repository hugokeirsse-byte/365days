import os
import sys
import json
from pathlib import Path

# Setup paths and imports as specified
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

try:
    from lib.image_router import generate as ir_generate
    from lib.image_to_coloring import convert as coloring_convert
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def main():
    # 1. Retrieve and validate environment variables
    brief_id = os.getenv("BRIEF_ID")
    if not brief_id:
        print("Error: BRIEF_ID environment variable is required.")
        sys.exit(1)

    line_thickness = int(os.getenv("LINE_THICKNESS", "2"))
    max_pages_env = os.getenv("MAX_PAGES")
    max_pages = int(max_pages_env) if max_pages_env else None

    # Define paths
    brief_path = ROOT / "data" / "briefs" / f"{brief_id}.json"
    gate1_dir = ROOT / "products" / "coloring_books" / "_gate1" / brief_id
    plan_path = gate1_dir / "production_plan.json"
    pages_dir = gate1_dir / "pages"
    report_path = gate1_dir / "generation_report.json"

    # 2. Verify brief approval status
    if not brief_path.exists():
        print(f"Error: Brief file not found at {brief_path}")
        sys.exit(1)

    with open(brief_path, "r", encoding="utf-8") as f:
        brief_data = json.load(f)

    gate_start = brief_data.get("gate_start")
    status = brief_data.get("status")
    if gate_start != "approved" and status != "approved":
        print(f"Error: Brief {brief_id} is not approved (gate_start={gate_start}, status={status}).")
        sys.exit(1)

    # 3. Read production plan
    if not plan_path.exists():
        print(f"Error: Production plan not found at {plan_path}")
        sys.exit(1)

    with open(plan_path, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    pages_dir.mkdir(parents=True, exist_ok=True)

    # Initialize report tracking
    report_pages = []
    summary = {"ok": 0, "failed": 0, "skipped": 0}

    # 4. Process standard coloring pages
    pages = plan_data.get("pages", [])
    if max_pages is not None:
        pages = pages[:max_pages]

    for page in pages:
        idx = page.get("index")
        prompt = page.get("prompt")
        subject = page.get("subject", f"Page {idx}")
        neg_prompt = page.get("negative_prompt", "color, shading, gradients, grayscale, photo, realistic, ugly, deformed, noisy")

        if not idx or not prompt:
            print(f"Skipping invalid page entry: {page}")
            continue

        filename = f"page_{idx:03d}.png"
        dest_path = pages_dir / filename
        tmp_path = pages_dir / f"tmp_{filename}"

        # Idempotency check
        if dest_path.exists():
            print(f"Page {idx:03d} already exists. Skipping.")
            report_pages.append({
                "page_number": idx,
                "status": "skipped",
                "provider_used": "n/a"
            })
            summary["skipped"] += 1
            continue

        print(f"Generating page {idx:03d} ({subject})...")
        try:
            # Generate base image via router
            provider_used = ir_generate(
                prompt=prompt,
                negative_prompt=neg_prompt,
                width=832,
                height=1152,
                dest=str(tmp_path)
            )
            
            if tmp_path.exists():
                # Convert base image to line-art
                coloring_convert(str(tmp_path), str(dest_path), line_thickness=line_thickness)
                
                # Clean up temporary file
                if tmp_path.exists():
                    tmp_path.unlink()

                report_pages.append({
                    "page_number": idx,
                    "status": "ok",
                    "provider_used": provider_used or "unknown"
                })
                summary["ok"] += 1
                print(f"Successfully created {filename}")
            else:
                raise RuntimeError("Router did not produce the expected output file.")

        except Exception as e:
            print(f"Failed to generate page {idx:03d}: {e}")
            if tmp_path.exists():
                tmp_path.unlink()
            report_pages.append({
                "page_number": idx,
                "status": "failed",
                "provider_used": "none"
            })
            summary["failed"] += 1

    # 5. Process covers (Front and Back)
    covers = plan_data.get("covers", {})
    for cover_type in ["front", "back"]:
        if cover_type in covers:
            cover_info = covers[cover_type]
            prompt = cover_info.get("prompt")
            if not prompt:
                continue

            filename = f"cover_{cover_type}.png"
            dest_path = pages_dir / filename
            neg_prompt = cover_info.get("negative_prompt", "low quality, blurry, bad anatomy")

            # Idempotency check
            if dest_path.exists():
                print(f"Cover {cover_type} already exists. Skipping.")
                report_pages.append({
                    "page_number": f"cover_{cover_type}",
                    "status": "skipped",
                    "provider_used": "n/a"
                })
                summary["skipped"] += 1
                continue

            print(f"Generating cover {cover_type}...")
            try:
                # Covers are generated directly in high resolution (KDP 300DPI)
                provider_used = ir_generate(
                    prompt=prompt,
                    negative_prompt=neg_prompt,
                    width=2625,
                    height=3375,
                    dest=str(dest_path)
                )

                if dest_path.exists():
                    report_pages.append({
                        "page_number": f"cover_{cover_type}",
                        "status": "ok",
                        "provider_used": provider_used or "unknown"
                    })
                    summary["ok"] += 1
                    print(f"Successfully created {filename}")
                else:
                    raise RuntimeError("Router did not produce the expected cover file.")

            except Exception as e:
                print(f"Failed to generate cover {cover_type}: {e}")
                report_pages.append({
                    "page_number": f"cover_{cover_type}",
                    "status": "failed",
                    "provider_used": "none"
                })
                summary["failed"] += 1

    # 6. Write generation report
    generation_report = {
        "pages": report_pages,
        "summary": summary
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(generation_report, f, indent=2, ensure_ascii=False)

    print(f"\nGeneration process completed. Report saved to {report_path}")
    print(f"Summary: {summary['ok']} succeeded, {summary['failed']} failed, {summary['skipped']} skipped.")

    # Exit 0 even if there are partial failures as per requirements
    sys.exit(0)

if __name__ == "__main__":
    main()