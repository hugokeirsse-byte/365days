#!/usr/bin/env python3
"""
Production Vintage PD depuis CdC validé — gate_cdc=approved requis.

ZÉRO génération d'image payante : la source EXISTE déjà (domaine public).
Pipeline = acquisition (banque locale ou Wikimedia) + traitement Pillow.

Types supportés :
  coloring_page             → lineart 8.5×11" + PDF KDP
  educational_coloring_book → lineart + fiche éducative (2 pages template) + PDF
  merch_tshirt              → PNG 4500×5400 fond transparent
  merch_tote                → PNG 4096×4096 fond blanc, composition centrée + texte
  merch_mug                 → PNG 3300×2550 bande + texte
  kdp_journal_cover         → couverture 6×9" + titre, PDF

Env vars :
  VPD_DIR   — chemin du produit (products/vintage_pd/{slug}). Vide = auto-détecte approuvé.

Sorties (dans le dossier produit) :
  source.jpg                — illustration source téléchargée
  output_<type>.png         — livrable image principal
  output.pdf                — pour les types KDP (coloring, educational, journal_cover)
  source_meta.json          — provenance/licence de la source
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

try:
    from PIL import Image, ImageOps, ImageFilter, ImageEnhance, ImageDraw, ImageFont
except ImportError:
    print("ERREUR : Pillow non installé. pip install Pillow")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

VPD_DIR = ROOT / "products" / "vintage_pd"
IMAGES_BANK = ROOT / "images"
MANIFEST = IMAGES_BANK / "manifest.json"
USER_AGENT = "365days-vpd/1.0 (hugo.keirsse@gmail.com)"
DPI = 300

# Dimensions cibles par type (largeur, hauteur) en pixels
DIMENSIONS = {
    "coloring_page":             (2550, 3300),   # 8.5×11"
    "educational_coloring_book": (2550, 3300),   # A4-ish portrait
    "merch_tshirt":              (4500, 5400),
    "merch_tote":                (4096, 4096),
    "merch_mug":                 (3300, 2550),
    "kdp_journal_cover":         (1800, 2700),   # 6×9"
}


# --------------------------------------------------------------------------- #
# Sélection du CdC approuvé
# --------------------------------------------------------------------------- #
def find_approved() -> Path | None:
    if not VPD_DIR.exists():
        return None
    for d in sorted(VPD_DIR.iterdir()):
        cdc_path = d / "cdc.json"
        if not cdc_path.exists():
            continue
        try:
            cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if cdc.get("gate_cdc") == "approved" and not cdc.get("production_status"):
            return d
    return None


# --------------------------------------------------------------------------- #
# Acquisition de la source (banque locale → Wikimedia)
# --------------------------------------------------------------------------- #
def _norm(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum() or c == " ").strip()


def acquire_source(cdc: dict, out_dir: Path) -> dict | None:
    """Récupère l'image source. Renvoie un dict {path, source_url, title, licence}."""
    source = cdc.get("source", {})
    sujet = source.get("sujet", "")
    sujet_affiche = source.get("sujet_affiche", sujet)
    dest = out_dir / "source.jpg"

    # 1) Banque locale (images/manifest.json) — match par latin/nom/sujet
    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}
        targets = [_norm(sujet.replace("_", " ")), _norm(sujet_affiche)]
        for slug, meta in manifest.items():
            hay = " ".join([_norm(str(meta.get("latin", ""))),
                            _norm(str(meta.get("name", ""))),
                            _norm(slug.replace("_", " "))])
            if any(t and t in hay for t in targets):
                local = IMAGES_BANK / meta.get("file", "")
                if local.exists():
                    dest.write_bytes(local.read_bytes())
                    print(f"[VPD] Source depuis banque locale : {local.name}")
                    return {
                        "path": dest,
                        "source_url": meta.get("source_url", ""),
                        "title": meta.get("name", sujet_affiche),
                        "licence": meta.get("licence", "public_domain"),
                    }

    # 2) Wikimedia Commons via le finder existant
    try:
        from scripts.agent_domain_image_finder import find_and_download
    except Exception as e:
        print(f"[VPD] Import finder impossible : {e}")
        find_and_download = None

    if find_and_download:
        search = sujet_affiche or sujet.replace("_", " ")
        print(f"[VPD] Recherche Wikimedia : '{search}'")
        tmp = out_dir / "_wiki"
        results = find_and_download(search, tmp, max_images=1, min_width_px=600)
        if results:
            r = results[0]
            local = Path(r["local_path"])
            if local.exists():
                dest.write_bytes(local.read_bytes())
                print(f"[VPD] Source Wikimedia : {r.get('title','')}")
                return {
                    "path": dest,
                    "source_url": r.get("source_url", ""),
                    "title": r.get("title", search),
                    "licence": r.get("license", "public_domain"),
                }

    print("[VPD] ✗ Aucune source trouvée (banque locale + Wikimedia).")
    return None


# --------------------------------------------------------------------------- #
# Helpers traitement image
# --------------------------------------------------------------------------- #
def load_font(size: int) -> "ImageFont.FreeTypeFont":
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()


def hex_to_rgb(h: str, default=(45, 74, 45)) -> tuple:
    h = (h or "").lstrip("#")
    if len(h) == 6:
        try:
            return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        except Exception:
            pass
    return default


def make_white_transparent(img: "Image.Image", threshold: int = 235) -> "Image.Image":
    """Rend les pixels quasi-blancs transparents (pour merch fond transparent)."""
    img = img.convert("RGBA")
    try:
        import numpy as np
        arr = np.array(img)
        white = (arr[:, :, 0] > threshold) & (arr[:, :, 1] > threshold) & (arr[:, :, 2] > threshold)
        arr[white, 3] = 0
        return Image.fromarray(arr, "RGBA")
    except Exception:
        datas = img.getdata()
        new = [(r, g, b, 0) if (r > threshold and g > threshold and b > threshold) else (r, g, b, a)
               for (r, g, b, a) in datas]
        img.putdata(new)
        return img


def extract_line_art(img: "Image.Image") -> "Image.Image":
    """Convertit une illustration couleur en lineart noir sur blanc."""
    img = img.convert("RGB").filter(ImageFilter.GaussianBlur(radius=0.8))
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Contrast(edges).enhance(8.0)
    edges = edges.filter(ImageFilter.SHARPEN).filter(ImageFilter.SHARPEN)
    inverted = ImageOps.invert(edges)
    bw = inverted.point(lambda x: 0 if x < 210 else 255)
    result = Image.new("RGB", bw.size, (255, 255, 255))
    result.paste(bw)
    return result


def fit_within(img: "Image.Image", max_w: int, max_h: int) -> "Image.Image":
    img = img.copy()
    img.thumbnail((max_w, max_h), Image.LANCZOS)
    return img


def draw_centered_text(canvas: "Image.Image", text: str, font, fill, y: int) -> None:
    if not text:
        return
    draw = ImageDraw.Draw(canvas)
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
    except Exception:
        tw = len(text) * font.size // 2
    x = (canvas.width - tw) // 2
    draw.text((x, y), text, font=font, fill=fill)


def compose_on_canvas(art: "Image.Image", size: tuple, texte: dict,
                      bg=(255, 255, 255)) -> "Image.Image":
    """Place l'illustration centrée + texte décoratif sur un canevas."""
    canvas = Image.new("RGB", size, bg)
    W, H = size
    # zone image = 70% hauteur, texte en dessous
    art_fitted = fit_within(art, int(W * 0.82), int(H * 0.62))
    ax = (W - art_fitted.width) // 2
    ay = int(H * 0.08)
    if art_fitted.mode == "RGBA":
        canvas.paste(art_fitted, (ax, ay), art_fitted)
    else:
        canvas.paste(art_fitted, (ax, ay))

    if texte.get("actif"):
        color = hex_to_rgb(texte.get("couleur_texte_hex", ""))
        principal = texte.get("texte_principal", "")
        secondaire = texte.get("texte_secondaire", "")
        f_main = load_font(int(H * 0.052))
        f_sub = load_font(int(H * 0.030))
        ty = ay + art_fitted.height + int(H * 0.04)
        draw_centered_text(canvas, principal, f_main, color, ty)
        if secondaire:
            draw_centered_text(canvas, secondaire, f_sub, color, ty + int(H * 0.07))
    return canvas


# --------------------------------------------------------------------------- #
# Handlers par type de produit
# --------------------------------------------------------------------------- #
def build_pdf(images: list, out_pdf: Path, title: str, size: tuple) -> None:
    try:
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.utils import ImageReader
    except ImportError:
        print("[VPD] reportlab absent — PDF ignoré (PNG livré).")
        return
    W, H = size
    c = pdf_canvas.Canvas(str(out_pdf), pagesize=(W, H))
    c.setTitle(title)
    c.setAuthor("365days")
    margin = int(min(W, H) * 0.04)
    for img_path in images:
        if not Path(img_path).exists():
            continue
        c.drawImage(ImageReader(str(img_path)), margin, margin,
                    width=W - 2 * margin, height=H - 2 * margin,
                    preserveAspectRatio=True, anchor="c")
        c.showPage()
    c.save()
    print(f"[VPD] PDF → {out_pdf.name} ({len(images)} page(s))")


def make_educational_sheet(cdc: dict, size: tuple) -> "Image.Image":
    """Page fiche éducative (texte) pour educational_coloring_book."""
    W, H = size
    canvas = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    edu = cdc.get("contenu_educatif") or {}
    fiche = edu.get("exemple_fiche", {})
    color = (40, 40, 40)
    f_title = load_font(int(H * 0.045))
    f_body = load_font(int(H * 0.028))
    margin = int(W * 0.10)
    y = int(H * 0.10)

    titre = fiche.get("titre_planche", cdc.get("produit", {}).get("titre_commercial", ""))
    draw.text((margin, y), titre, font=f_title, fill=color)
    y += int(H * 0.08)

    rows = [
        ("Nom scientifique", fiche.get("nom_scientifique", "")),
        ("Famille", fiche.get("famille_botanique", "")),
        ("Origine", fiche.get("zone_origine", "")),
        ("Description", fiche.get("description_courte", "")),
        ("Usage historique", fiche.get("usage_historique_medicinal", "")),
        ("Anecdote", fiche.get("anecdote", "")),
    ]
    for label, val in rows:
        if not val:
            continue
        draw.text((margin, y), f"{label} :", font=f_body, fill=(90, 90, 90))
        y += int(H * 0.038)
        # wrap simple
        words = str(val).split()
        line = ""
        max_chars = 52
        for w in words:
            if len(line) + len(w) + 1 > max_chars:
                draw.text((margin + 30, y), line, font=f_body, fill=color)
                y += int(H * 0.036)
                line = w
            else:
                line = (line + " " + w).strip()
        if line:
            draw.text((margin + 30, y), line, font=f_body, fill=color)
            y += int(H * 0.05)
    return canvas


def produce(cdc: dict, out_dir: Path, source_path: Path) -> list:
    """Génère le ou les livrables selon le type. Renvoie la liste des fichiers créés."""
    ptype = cdc.get("produit", {}).get("type", "coloring_page")
    size = DIMENSIONS.get(ptype, DIMENSIONS["coloring_page"])
    texte = cdc.get("texte_decoratif", {}) or {}
    title = cdc.get("produit", {}).get("titre_commercial", "Vintage PD")
    src = Image.open(source_path)
    created = []

    if ptype in ("coloring_page", "educational_coloring_book"):
        art = extract_line_art(src)
        page = compose_on_canvas(art, size, texte)
        png = out_dir / f"output_{ptype}.png"
        page.save(png, "PNG", dpi=(DPI, DPI))
        created.append(png)
        pages = [png]
        if ptype == "educational_coloring_book":
            sheet = make_educational_sheet(cdc, size)
            sheet_png = out_dir / "output_fiche_educative.png"
            sheet.save(sheet_png, "PNG", dpi=(DPI, DPI))
            created.append(sheet_png)
            pages = [png, sheet_png]
        build_pdf(pages, out_dir / "output.pdf", title, size)
        created.append(out_dir / "output.pdf")

    elif ptype == "merch_tshirt":
        transparent = make_white_transparent(src.convert("RGB"))
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        art = fit_within(transparent, int(size[0] * 0.9), int(size[1] * 0.78))
        ax = (size[0] - art.width) // 2
        ay = int(size[1] * 0.06)
        canvas.paste(art, (ax, ay), art)
        if texte.get("actif"):
            color = hex_to_rgb(texte.get("couleur_texte_hex", ""))
            f_main = load_font(int(size[1] * 0.05))
            draw_centered_text(canvas, texte.get("texte_principal", ""),
                               f_main, color + (255,), ay + art.height + int(size[1] * 0.04))
        png = out_dir / "output_merch_tshirt.png"
        canvas.save(png, "PNG", dpi=(DPI, DPI))
        created.append(png)

    elif ptype == "merch_tote":
        page = compose_on_canvas(src.convert("RGB"), size, texte, bg=(250, 248, 242))
        png = out_dir / "output_merch_tote.png"
        page.save(png, "PNG", dpi=(DPI, DPI))
        created.append(png)

    elif ptype == "merch_mug":
        canvas = Image.new("RGB", size, (255, 255, 255))
        art = fit_within(src.convert("RGB"), int(size[0] * 0.4), int(size[1] * 0.8))
        canvas.paste(art, ((size[0] - art.width) // 2, (size[1] - art.height) // 2))
        if texte.get("actif"):
            color = hex_to_rgb(texte.get("couleur_texte_hex", ""))
            f_main = load_font(int(size[1] * 0.09))
            draw_centered_text(canvas, texte.get("texte_principal", ""),
                               f_main, color, int(size[1] * 0.08))
        png = out_dir / "output_merch_mug.png"
        canvas.save(png, "PNG", dpi=(DPI, DPI))
        created.append(png)

    elif ptype == "kdp_journal_cover":
        canvas = Image.new("RGB", size, (250, 246, 238))
        art = fit_within(src.convert("RGB"), int(size[0] * 0.78), int(size[1] * 0.55))
        ax = (size[0] - art.width) // 2
        ay = int(size[1] * 0.20)
        canvas.paste(art, (ax, ay))
        color = hex_to_rgb(texte.get("couleur_texte_hex", "") if texte else "")
        f_title = load_font(int(size[1] * 0.055))
        draw_centered_text(canvas, (texte.get("texte_principal", "") if texte else title) or title,
                           f_title, color, int(size[1] * 0.08))
        png = out_dir / "output_kdp_journal_cover.png"
        canvas.save(png, "PNG", dpi=(DPI, DPI))
        created.append(png)
        build_pdf([png], out_dir / "output.pdf", title, size)
        created.append(out_dir / "output.pdf")

    else:
        # fallback : composition simple
        page = compose_on_canvas(src.convert("RGB"), size, texte)
        png = out_dir / f"output_{ptype}.png"
        page.save(png, "PNG", dpi=(DPI, DPI))
        created.append(png)

    return created


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def run():
    vpd_env = os.environ.get("VPD_DIR", "").strip()
    out_dir = (ROOT / vpd_env) if vpd_env else find_approved()

    if not out_dir:
        print("[VPD] Aucun CdC approuvé dans products/vintage_pd/")
        print("[VPD] → Approuver : gate_cdc = 'approved' dans cdc.json")
        sys.exit(0)

    cdc_path = out_dir / "cdc.json"
    if not cdc_path.exists():
        print(f"[VPD] cdc.json manquant : {cdc_path}")
        sys.exit(1)

    cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
    if cdc.get("gate_cdc") != "approved":
        print(f"[VPD] gate_cdc = '{cdc.get('gate_cdc')}' (≠ approved). Abandon.")
        sys.exit(0)

    ptype = cdc.get("produit", {}).get("type", "coloring_page")
    print(f"[VPD] Production : {out_dir.name} | Type : {ptype}")

    # 1. Acquisition
    src_meta = acquire_source(cdc, out_dir)
    if not src_meta:
        print("[VPD] ✗ Production impossible sans source.")
        sys.exit(1)
    (out_dir / "source_meta.json").write_text(
        json.dumps({k: (str(v) if isinstance(v, Path) else v) for k, v in src_meta.items()},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    # 2. Traitement
    try:
        created = produce(cdc, out_dir, src_meta["path"])
    except Exception as e:
        print(f"[VPD] ✗ Erreur de traitement : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 3. Marquage production_status
    cdc["production_status"] = {
        "produced_at": date.today().isoformat(),
        "type": ptype,
        "files": [f.name for f in created if Path(f).exists()],
        "source_url": src_meta.get("source_url", ""),
    }
    cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[VPD] === PRODUCTION TERMINÉE ===")
    for f in created:
        if Path(f).exists():
            kb = Path(f).stat().st_size // 1024
            print(f"  ✓ {f.name} ({kb} KB)")
    print(f"  Source : {src_meta.get('title','')} — {src_meta.get('licence','')}")
    print(f"  Dossier : products/vintage_pd/{out_dir.name}/")


if __name__ == "__main__":
    run()
