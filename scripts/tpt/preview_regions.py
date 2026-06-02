"""
Preview — Affiche où seront placés les labels de régions sur un SVG téléchargé.
Génère un PDF de vérification avec les points numérotés sur l'image.

Usage :
  python scripts/tpt/preview_regions.py halloween
  python scripts/tpt/preview_regions.py back_to_school
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
from tpt.pipeline_cbc import THEMES, SVG_DIR, ROOT, get_image
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, black, white, red
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

PAGE_W, PAGE_H = letter


def preview(theme_id: str):
    cfg = THEMES[theme_id]
    out_dir = ROOT / "products" / "tpt" / "preview"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        img_path = get_image(theme_id, cfg, out_dir)
    except FileNotFoundError as e:
        print(e)
        return

    out = out_dir / f"preview_{theme_id}.pdf"
    c = rl_canvas.Canvas(str(out), pagesize=letter)
    M = 0.5 * inch

    # Titre
    c.setFillColor(HexColor(cfg["header_hex"]))
    c.roundRect(M, PAGE_H - M - 0.5*inch, PAGE_W - 2*M, 0.5*inch, 6, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(PAGE_W/2, PAGE_H - M - 0.32*inch,
                        f"PREVIEW régions — {theme_id}")

    # Image pleine page (gauche)
    scene_w = PAGE_W - 2*M
    scene_h = PAGE_H - 2*M - 0.6*inch
    ix, iy = M, M

    if img_path.suffix.lower() == ".svg":
        drawing = svg2rlg(str(img_path))
        if drawing:
            scale = min(scene_w / drawing.width, scene_h / drawing.height)
            dw, dh = drawing.width * scale, drawing.height * scale
            ox = ix + (scene_w - dw) / 2
            oy = iy + (scene_h - dh) / 2
            drawing.width, drawing.height = dw, dh
            drawing.transform = (scale, 0, 0, scale, 0, 0)
            renderPDF.draw(drawing, c, ox, oy)
    else:
        from reportlab.lib.utils import ImageReader
        img = ImageReader(str(img_path))
        iw, ih = img.getSize()
        scale = min(scene_w / iw, scene_h / ih)
        dw, dh = iw * scale, ih * scale
        ox = ix + (scene_w - dw) / 2
        oy = iy + (scene_h - dh) / 2
        c.drawImage(str(img_path), ox, oy, dw, dh, mask="auto")

    # Overlay des points avec coordonnées
    ans_map = {ans: HexColor(hx) for ans, _, hx in cfg["colors"]}
    for ans, rx, ry in cfg["regions"]:
        lx = ox + rx * dw
        ly = oy + dh * (1 - ry)
        col = ans_map.get(ans, red)
        # Cercle rouge visible
        c.setFillColor(col)
        c.setStrokeColor(black)
        c.setLineWidth(1.5)
        c.circle(lx, ly, 14, fill=1, stroke=1)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(lx, ly - 4, str(ans))
        # Coordonnées en petit
        c.setFillColor(black)
        c.setFont("Helvetica", 7)
        c.drawCentredString(lx, ly - 18, f"({rx:.2f},{ry:.2f})")

    c.showPage()
    c.save()
    print(f"✓ Preview : {out}")
    print(f"  Si les labels ne sont pas au bon endroit, modifie 'regions' dans THEMES['{theme_id}']")


if __name__ == "__main__":
    tid = sys.argv[1] if len(sys.argv) > 1 else "halloween"
    if tid == "all":
        from tpt.pipeline_cbc import THEMES
        for t in THEMES:
            preview(t)
    else:
        preview(tid)
