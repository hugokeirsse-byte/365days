"""Assemble le PDF interieur KDP depuis les pages line-art generees.

Lis la liste de pages depuis production_plan.json (pas generation_report.json
qui n'existe qu'apres generation images). Insere les pages presentes dans
pages/, saute les manquantes avec un blanc. Ecrit interior.pdf + kdp_package.json.

Retourne toujours exit 0 (CI non-bloquant) ; ready_for_gate2 reflete la completude.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def main():
    brief_id = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("BRIEF_ID", "")
    if not brief_id:
        print("build_kdp_pdf: BRIEF_ID manquant.", file=sys.stderr)
        return 0

    brief_path = ROOT / "data" / "briefs" / f"{brief_id}.json"
    if not brief_path.exists():
        print(f"build_kdp_pdf: brief introuvable {brief_path}", file=sys.stderr)
        return 0

    brief = json.loads(brief_path.read_text(encoding="utf-8"))
    fmt = brief.get("target", {}).get("format", {})

    # Dimensions avec bleed
    trim_str = fmt.get("trim", "8.5x11in")
    bleed_str = fmt.get("bleed", "0.125in")
    pages_interior = fmt.get("pages_interior", 30)

    try:
        tw, th = [float(x) for x in trim_str.lower().replace("in", "").split("x")]
        bl = float(bleed_str.lower().replace("in", ""))
    except Exception as e:
        print(f"build_kdp_pdf: erreur parsing dimensions: {e}", file=sys.stderr)
        tw, th, bl = 8.5, 11.0, 0.125

    pw = (tw + 2 * bl) * inch
    ph = (th + 2 * bl) * inch
    bleed_pt = bl * inch
    trim_w_pt = tw * inch
    trim_h_pt = th * inch

    gate1_dir = ROOT / "products" / "coloring_books" / "_gate1" / brief_id
    pages_dir = gate1_dir / "pages"
    out_pdf = gate1_dir / "interior.pdf"
    out_pkg = gate1_dir / "kdp_package.json"
    gate1_dir.mkdir(parents=True, exist_ok=True)

    plan_path = gate1_dir / "production_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.exists() else {}
    page_entries = plan.get("pages", [{"index": i} for i in range(1, pages_interior + 1)])

    if not HAS_REPORTLAB:
        print("build_kdp_pdf: reportlab absent — PDF non genere.", file=sys.stderr)
        out_pkg.write_text(
            json.dumps({"built_at": datetime.utcnow().isoformat() + "Z",
                        "brief_id": brief_id, "ready_for_gate2": False,
                        "error": "reportlab manquant"}, indent=2),
            encoding="utf-8"
        )
        return 0

    print(f"Assemblage PDF : {brief_id} | format {tw}x{th}in + bleed {bl}in")
    c = canvas.Canvas(str(out_pdf), pagesize=(pw, ph))

    pages_included = 0
    pages_missing = 0

    for entry in page_entries[:pages_interior]:
        idx = entry.get("index", 0)
        img_path = pages_dir / f"page_{idx:03d}.png"

        if img_path.exists():
            try:
                # Centrer l'image dans la zone trim
                c.drawImage(
                    str(img_path),
                    bleed_pt, bleed_pt,
                    width=trim_w_pt, height=trim_h_pt,
                    preserveAspectRatio=True, anchor="c"
                )
                pages_included += 1
            except Exception as e:
                print(f"  page {idx}: erreur drawImage: {e}", file=sys.stderr)
                pages_missing += 1
        else:
            # Page manquante : blanc (KDP accepte les pages blanches)
            pages_missing += 1

        c.showPage()

    c.save()
    ready = pages_missing == 0
    print(f"PDF ecrit : {out_pdf} ({pages_included}/{len(page_entries[:pages_interior])} pages)")
    if pages_missing:
        print(f"  {pages_missing} pages manquantes (blancs) — ready_for_gate2=False")

    out_pkg.write_text(
        json.dumps({
            "built_at": datetime.utcnow().isoformat() + "Z",
            "brief_id": brief_id,
            "title": brief.get("target", {}).get("collection", {}).get("title", ""),
            "author": brief.get("target", {}).get("collection", {}).get("author", ""),
            "pages_included": pages_included,
            "pages_missing": pages_missing,
            "format": f"{tw}x{th}in",
            "bleed": f"{bl}in",
            "ready_for_gate2": ready,
        }, indent=2),
        encoding="utf-8"
    )
    print(f"kdp_package.json ecrit (ready_for_gate2={ready})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
