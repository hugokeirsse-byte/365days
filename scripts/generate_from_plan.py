import os
import sys
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lib.image_router import generate as ir_generate
from lib.image_to_coloring import convert as coloring_convert


def main():
    brief_id = os.environ.get("BRIEF_ID", "").strip()
    if not brief_id:
        print("Error: BRIEF_ID environment variable is required.", file=sys.stderr)
        sys.exit(1)

    line_thickness = int(os.environ.get("LINE_THICKNESS", 2))
    max_pages_env = os.environ.get("MAX_PAGES", "").strip()
    max_pages = int(max_pages_env) if max_pages_env else None

    # Charger le brief
    brief_path = ROOT / "data" / "briefs" / f"{brief_id}.json"
    if not brief_path.exists():
        print(f"Error: Brief not found at {brief_path}", file=sys.stderr)
        sys.exit(1)

    brief_data = json.loads(brief_path.read_text(encoding="utf-8"))

    # Verifier gate_start (structure : brief.human_gates.gate_start)
    gate_start = brief_data.get("human_gates", {}).get("gate_start", "")
    if gate_start != "approved":
        print(f"Error: Brief {brief_id} non approuve (human_gates.gate_start={gate_start!r}).",
              file=sys.stderr)
        sys.exit(1)

    # Charger le plan de production
    plan_path = (ROOT / "products" / "coloring_books" / "_gate1"
                 / brief_id / "production_plan.json")
    if not plan_path.exists():
        print(f"Error: production_plan.json absent a {plan_path}", file=sys.stderr)
        sys.exit(1)

    plan_data = json.loads(plan_path.read_text(encoding="utf-8"))

    pages_dir = ROOT / "products" / "coloring_books" / "_gate1" / brief_id / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    pages_to_process = plan_data.get("pages", [])
    if max_pages is not None:
        pages_to_process = pages_to_process[:max_pages]

    report_pages = []
    summary = {"ok": 0, "failed": 0, "skipped": 0}

    # Pages interieures
    for page in pages_to_process:
        idx = page.get("index")
        prompt = page.get("prompt", "").strip()
        if not prompt:
            print(f"Warning: page {idx} sans prompt — skip.")
            continue

        out_path = pages_dir / f"page_{idx:03d}.png"

        if out_path.exists():
            print(f"Page {idx} deja presente — skip.")
            report_pages.append({"page_number": idx, "status": "skipped", "provider_used": "none"})
            summary["skipped"] += 1
            continue

        print(f"Generation page {idx}...")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            tmp_path = Path(tf.name)

        try:
            provider = ir_generate(prompt=prompt, width=832, height=1152, dest=str(tmp_path))
            if provider and tmp_path.exists() and tmp_path.stat().st_size > 0:
                coloring_convert(str(tmp_path), str(out_path), line_thickness=line_thickness)
                print(f"OK page {idx} via {provider}")
                report_pages.append({"page_number": idx, "status": "ok",
                                      "provider_used": str(provider)})
                summary["ok"] += 1
            else:
                raise RuntimeError("image_router n'a retourne aucune image.")
        except Exception as e:
            print(f"Echec page {idx}: {e}", file=sys.stderr)
            report_pages.append({"page_number": idx, "status": "failed", "provider_used": "none"})
            summary["failed"] += 1
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass

    # Couvertures
    covers = plan_data.get("covers", {})
    for cover_type in ["front", "back"]:
        cover_info = covers.get(cover_type, {})
        prompt = cover_info.get("prompt", "").strip()
        if not prompt:
            continue

        out_path = pages_dir / f"cover_{cover_type}.png"
        if out_path.exists():
            print(f"Cover {cover_type} deja presente — skip.")
            report_pages.append({"page_number": f"cover_{cover_type}", "status": "skipped",
                                  "provider_used": "none"})
            summary["skipped"] += 1
            continue

        print(f"Generation cover {cover_type}...")
        try:
            provider = ir_generate(prompt=prompt, width=2625, height=3375, dest=str(out_path))
            if provider and out_path.exists() and out_path.stat().st_size > 0:
                print(f"OK cover {cover_type} via {provider}")
                report_pages.append({"page_number": f"cover_{cover_type}", "status": "ok",
                                      "provider_used": str(provider)})
                summary["ok"] += 1
            else:
                raise RuntimeError("image_router n'a retourne aucune image pour la cover.")
        except Exception as e:
            print(f"Echec cover {cover_type}: {e}", file=sys.stderr)
            report_pages.append({"page_number": f"cover_{cover_type}", "status": "failed",
                                  "provider_used": "none"})
            summary["failed"] += 1

    # Rapport
    report_path = (ROOT / "products" / "coloring_books" / "_gate1"
                   / brief_id / "generation_report.json")
    report_path.write_text(
        json.dumps({"pages": report_pages, "summary": summary}, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Rapport ecrit -> {report_path}")
    print(f"Resume : {summary}")


if __name__ == "__main__":
    main()
