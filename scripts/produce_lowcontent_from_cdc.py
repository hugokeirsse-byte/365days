#!/usr/bin/env python3
"""
Production Low-Content KDP depuis CdC validé.

Lit le cdc.json (gate_cdc=approved) et génère un PDF ReportLab complet.
100% offline, texte vectoriel → qualité impression parfaite à 300 DPI.

Variables d'env :
  LC_DIR  — chemin du produit (products/lowcontent_kdp/{slug})
            si absent, cherche le dernier produit avec gate=approved

Format : 6×9 inches (152.4×228.6 mm), marges KDP standard.
"""

import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

try:
    from reportlab.lib.pagesizes import inch
    from reportlab.lib.units import inch as INCH
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("ERREUR : reportlab non installé. pip install reportlab")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent

# ── KDP 6×9 inches paperback ─────────────────────────────────────────────────
TRIM_W = 6 * INCH
TRIM_H = 9 * INCH
MARGIN_INNER = 0.75 * INCH
MARGIN_OUTER = 0.5 * INCH
MARGIN_TOP = 0.5 * INCH
MARGIN_BOTTOM = 0.5 * INCH

# Polices (system fonts avec fallback Helvetica)
_FONT_LOADED = False

def _load_fonts():
    global _FONT_LOADED, SERIF, SERIF_BOLD, SERIF_ITALIC
    if _FONT_LOADED:
        return
    font_candidates = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "DejaVuSerif"),
        ("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf", "LiberationSerif"),
    ]
    SERIF = SERIF_BOLD = SERIF_ITALIC = None
    for path, name in font_candidates:
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                bold_path = path.replace("-Regular", "-Bold").replace(".ttf", "-Bold.ttf")
                italic_path = path.replace("-Regular", "-Italic").replace(".ttf", "-Italic.ttf")
                SERIF = name
                if Path(bold_path).exists():
                    pdfmetrics.registerFont(TTFont(name + "Bold", bold_path))
                    SERIF_BOLD = name + "Bold"
                else:
                    SERIF_BOLD = "Helvetica-Bold"
                if Path(italic_path).exists():
                    pdfmetrics.registerFont(TTFont(name + "Italic", italic_path))
                    SERIF_ITALIC = name + "Italic"
                else:
                    SERIF_ITALIC = "Helvetica-Oblique"
                break
            except Exception:
                continue

    if not SERIF:
        SERIF = "Helvetica"
        SERIF_BOLD = "Helvetica-Bold"
        SERIF_ITALIC = "Helvetica-Oblique"
    _FONT_LOADED = True


def hex_to_rgb(hex_color: str) -> tuple:
    """Convertit #RRGGBB en (r, g, b) flottants 0-1."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (0.2, 0.15, 0.1)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r / 255, g / 255, b / 255)


def gutter(page_num: int) -> tuple:
    """Marges gauche/droite selon recto/verso."""
    if page_num % 2 == 1:
        return MARGIN_INNER, MARGIN_OUTER
    return MARGIN_OUTER, MARGIN_INNER


# ── Primitives de dessin ──────────────────────────────────────────────────────

def draw_header_footer(c, page_num: int, title: str,
                        primary_rgb: tuple, accent_rgb: tuple) -> None:
    """En-tête et pied de page discrets."""
    _load_fonts()
    left, right = gutter(page_num)
    w = TRIM_W - left - right

    # Ligne décorative en haut
    c.setStrokeColorRGB(*accent_rgb)
    c.setLineWidth(0.5)
    c.line(left, TRIM_H - MARGIN_TOP + 4, left + w, TRIM_H - MARGIN_TOP + 4)

    # Numéro de page en bas
    c.setFont(SERIF_ITALIC, 8)
    c.setFillColorRGB(*primary_rgb)
    c.drawCentredString(TRIM_W / 2, MARGIN_BOTTOM / 2, f"— {page_num} —")


def y_label_dotted_line(c, x_left: float, x_right: float, y: float,
                          label: str, font_size: int = 10,
                          label_rgb: tuple = (0.2, 0.15, 0.1),
                          line_rgb: tuple = (0.6, 0.55, 0.5)) -> float:
    """Dessine 'Label: ........................' et retourne la nouvelle position y."""
    _load_fonts()
    c.setFont(SERIF, font_size)
    c.setFillColorRGB(*label_rgb)
    c.drawString(x_left, y, f"{label}:")
    lw = c.stringWidth(f"{label}: ", SERIF, font_size)
    c.setDash(1.5, 2)
    c.setStrokeColorRGB(*line_rgb)
    c.setLineWidth(0.3)
    c.line(x_left + lw, y - 1, x_right, y - 1)
    c.setDash()
    return y - (font_size + 8)


def y_ruled_lines(c, x_left: float, x_right: float, y: float,
                   n_lines: int, spacing: float = 16,
                   line_rgb: tuple = (0.7, 0.65, 0.6)) -> float:
    """Dessine n lignes réglées et retourne la position y finale."""
    c.setStrokeColorRGB(*line_rgb)
    c.setLineWidth(0.3)
    for _ in range(n_lines):
        if y < MARGIN_BOTTOM + 20:
            break
        c.line(x_left, y, x_right, y)
        y -= spacing
    return y


def y_checkboxes(c, x_left: float, x_right: float, y: float,
                  n_items: int, label: str = "",
                  box_size: float = 7, spacing: float = 18,
                  label_rgb: tuple = (0.2, 0.15, 0.1)) -> float:
    """Dessine n cases à cocher et retourne la nouvelle position y."""
    _load_fonts()
    if label:
        c.setFont(SERIF_BOLD, 9)
        c.setFillColorRGB(*label_rgb)
        c.drawString(x_left, y, label)
        y -= 14

    c.setStrokeColorRGB(0.4, 0.35, 0.3)
    c.setLineWidth(0.5)
    for _ in range(n_items):
        if y < MARGIN_BOTTOM + 20:
            break
        c.rect(x_left, y - box_size + 1, box_size, box_size)
        # Ligne à droite de la case
        c.setDash(1, 2)
        c.line(x_left + box_size + 5, y - 1, x_right, y - 1)
        c.setDash()
        y -= spacing
    return y


def y_star_rating(c, x_left: float, y: float,
                   label: str = "Mood",
                   n_stars: int = 5,
                   primary_rgb: tuple = (0.3, 0.2, 0.1)) -> float:
    """Ligne de rating avec étoiles vides."""
    _load_fonts()
    c.setFont(SERIF, 10)
    c.setFillColorRGB(*primary_rgb)
    c.drawString(x_left, y, f"{label}:")
    # Étoiles (caractères unicode basiques)
    star_x = x_left + 60
    c.setFont(SERIF, 14)
    c.drawString(star_x, y - 1, "☆ " * n_stars)
    return y - 22


def y_section_title(c, x_left: float, y: float, title: str,
                     accent_rgb: tuple, font_size: int = 10) -> float:
    """Titre de section avec mini-décoration."""
    _load_fonts()
    c.setFont(SERIF_BOLD, font_size)
    c.setFillColorRGB(*accent_rgb)
    c.drawString(x_left, y, title)
    y -= 4
    c.setStrokeColorRGB(*accent_rgb)
    c.setLineWidth(0.4)
    c.line(x_left, y, x_left + 30, y)
    return y - 10


def y_quote_box(c, x_left: float, x_right: float, y: float,
                 primary_rgb: tuple, height: float = 40) -> float:
    """Zone réservée pour une citation (cadre pointillé)."""
    c.setStrokeColorRGB(*primary_rgb)
    c.setDash(2, 3)
    c.setLineWidth(0.4)
    c.rect(x_left, y - height, x_right - x_left, height)
    c.setDash()
    c.setFont(SERIF_ITALIC, 8)
    c.setFillColorRGB(*primary_rgb)
    c.drawCentredString((x_left + x_right) / 2, y - height / 2 - 4,
                          "✦  my quote / intention  ✦")
    return y - height - 10


# ── Constructeur de pages depuis éléments CdC ────────────────────────────────

ELEMENT_ALIASES = {
    "date": ["date"],
    "mood": ["humeur", "mood", "émotion", "emotion", "feeling"],
    "gratitude": ["gratitude", "gratitudes", "gratuit", "thankful", "grateful"],
    "intention": ["intention", "intention du jour", "daily intention", "objectif"],
    "notes": ["notes", "lines", "lignes", "notes libres", "espace notes", "reflections"],
    "checkboxes": ["tasks", "tâches", "habits", "habitudes", "to-do", "todo", "checklist"],
    "rating": ["rating", "note", "score", "energy", "énergie", "note journée"],
    "quote": ["quote", "citation", "affirmation"],
    "separator": ["separator", "séparateur", "---"],
    "title": ["titre page", "page title", "title"],
}


def detect_element(raw: str) -> str:
    """Détecte le type d'élément à partir d'une description en texte libre."""
    raw_lower = raw.lower().strip()
    for etype, aliases in ELEMENT_ALIASES.items():
        if any(alias in raw_lower for alias in aliases):
            return etype
    # Détection par motifs numériques (ex: "3 gratitudes", "5 tasks")
    if re.search(r'\d+\s*(ligne|line|gratitud|task|habit|habitud)', raw_lower):
        match = re.search(r'(\d+)', raw_lower)
        n = int(match.group(1)) if match else 3
        if "line" in raw_lower or "ligne" in raw_lower:
            return f"notes:{n}"
        if "gratitud" in raw_lower:
            return f"gratitude:{n}"
        if "task" in raw_lower or "habit" in raw_lower:
            return f"checkboxes:{n}"
    return "notes"


def draw_dynamic_page(c, page_num: int, elements_raw: list,
                       primary_rgb: tuple, accent_rgb: tuple,
                       header_title: str, spacing_mm: float = 8) -> None:
    """Génère une page selon la liste d'éléments du CdC."""
    _load_fonts()
    left, right = gutter(page_num)
    x_right = TRIM_W - right
    x_left = left
    y = TRIM_H - MARGIN_TOP - 14
    spacing = spacing_mm * (INCH / 25.4)

    draw_header_footer(c, page_num, header_title, primary_rgb, accent_rgb)

    for raw_element in elements_raw:
        if y < MARGIN_BOTTOM + 30:
            break

        y -= 4  # petit espace entre éléments

        etype = detect_element(raw_element)

        # Extraire nombre si format "notes:15"
        n_count = 3
        if ":" in etype:
            parts = etype.split(":")
            etype = parts[0]
            try:
                n_count = int(parts[1])
            except (IndexError, ValueError):
                n_count = 3

        if etype == "date":
            y = y_label_dotted_line(c, x_left, x_right, y, "Date",
                                     label_rgb=primary_rgb)

        elif etype == "mood":
            y = y_star_rating(c, x_left, y, "Mood", primary_rgb=primary_rgb)

        elif etype == "gratitude":
            y = y_section_title(c, x_left, y, "Gratitude", accent_rgb)
            for i in range(max(1, n_count)):
                if y < MARGIN_BOTTOM + 20:
                    break
                y = y_label_dotted_line(c, x_left, x_right, y,
                                         f"  {i+1}.", label_rgb=primary_rgb)

        elif etype == "intention":
            y = y_section_title(c, x_left, y, "Intention", accent_rgb)
            y = y_label_dotted_line(c, x_left, x_right, y, " ", label_rgb=primary_rgb)
            y = y_label_dotted_line(c, x_left, x_right, y, " ", label_rgb=primary_rgb)

        elif etype == "notes":
            y = y_section_title(c, x_left, y, "Notes", accent_rgb)
            n = max(3, n_count)
            y = y_ruled_lines(c, x_left, x_right, y, n_lines=n)

        elif etype == "checkboxes":
            y = y_checkboxes(c, x_left, x_right, y, n_items=max(3, n_count),
                               label_rgb=primary_rgb)

        elif etype == "rating":
            label = raw_element.strip().split("(")[0].strip()
            y = y_label_dotted_line(c, x_left, x_right, y, label[:20],
                                     label_rgb=primary_rgb)

        elif etype == "quote":
            y = y_quote_box(c, x_left, x_right, y, primary_rgb, height=38)

        elif etype == "separator":
            c.setStrokeColorRGB(*accent_rgb)
            c.setLineWidth(0.3)
            c.setDash(1, 4)
            c.line(x_left + 20, y, x_right - 20, y)
            c.setDash()
            y -= 12

        else:
            # Fallback : traiter comme une ligne labellisée
            y = y_label_dotted_line(c, x_left, x_right, y,
                                     raw_element[:25], label_rgb=primary_rgb)


def draw_title_page(c, titre: str, sous_titre: str, nom_de_plume: str,
                     primary_rgb: tuple, accent_rgb: tuple) -> None:
    """Page de titre élégante."""
    _load_fonts()
    cy = TRIM_H / 2

    # Cadre décoratif
    c.setStrokeColorRGB(*accent_rgb)
    c.setLineWidth(0.6)
    margin = 0.65 * INCH
    c.rect(margin, margin, TRIM_W - 2 * margin, TRIM_H - 2 * margin)
    inner = margin + 6
    c.setLineWidth(0.2)
    c.rect(inner, inner, TRIM_W - 2 * inner, TRIM_H - 2 * inner)

    # Titre
    c.setFont(SERIF_BOLD, 22)
    c.setFillColorRGB(*primary_rgb)
    # Word wrap rudimentaire
    words = titre.split()
    line1 = " ".join(words[:len(words)//2]) if len(words) > 3 else titre
    line2 = " ".join(words[len(words)//2:]) if len(words) > 3 else ""
    c.drawCentredString(TRIM_W / 2, cy + 30, line1)
    if line2:
        c.drawCentredString(TRIM_W / 2, cy + 6, line2)
        cy -= 24

    # Séparateur
    c.setStrokeColorRGB(*accent_rgb)
    c.setLineWidth(0.8)
    c.line(TRIM_W / 2 - 35, cy - 8, TRIM_W / 2 + 35, cy - 8)

    # Sous-titre
    c.setFont(SERIF_ITALIC, 12)
    c.setFillColorRGB(*accent_rgb)
    c.drawCentredString(TRIM_W / 2, cy - 28, sous_titre[:60])

    # Auteur
    c.setFont(SERIF, 10)
    c.setFillColorRGB(*primary_rgb)
    c.drawCentredString(TRIM_W / 2, MARGIN_BOTTOM + 40, nom_de_plume)


def draw_intro_page(c, page_num: int, content: str,
                     primary_rgb: tuple, accent_rgb: tuple) -> None:
    """Page d'introduction avec texte libre."""
    _load_fonts()
    left, right = gutter(page_num)
    x_right = TRIM_W - right
    y = TRIM_H - MARGIN_TOP - 14

    draw_header_footer(c, page_num, "", primary_rgb, accent_rgb)

    c.setFont(SERIF, 10)
    c.setFillColorRGB(*primary_rgb)
    # Texte simple découpé par lignes
    lines = content.replace("\n", " ").split(". ")
    for sentence in lines[:20]:
        if y < MARGIN_BOTTOM + 20:
            break
        # Découpe si trop long
        max_chars = int((x_right - left) / (INCH * 0.1) * 1.8)
        if len(sentence) > max_chars:
            sentence = sentence[:max_chars] + "..."
        c.drawString(left, y, sentence.strip())
        y -= 16


# ── Production principale ─────────────────────────────────────────────────────

def produce_from_cdc(product_dir: Path) -> Path:
    """Génère le PDF complet depuis le cdc.json d'un produit low-content."""
    cdc_path = product_dir / "cdc.json"
    if not cdc_path.exists():
        raise FileNotFoundError(f"cdc.json introuvable dans {product_dir}")

    cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
    gate = cdc.get("gate_cdc", "pending")

    if gate == "pending":
        print(f"[Low-Content] GATE = pending. Hugo doit valider {product_dir.name} avant production.")
        sys.exit(0)
    elif gate == "rejected":
        print("[Low-Content] GATE = rejected. Production annulée.")
        sys.exit(0)

    concept = cdc.get("concept", {})
    identite = cdc.get("identite_commerciale", {})
    structure = cdc.get("structure_pages", {})
    spec_rl = cdc.get("spec_reportlab", {})

    titre = concept.get("titre", "My Journal")
    sous_titre = concept.get("sous_titre", "")
    nom_de_plume = identite.get("nom_de_plume", "")
    nb_pages = int(concept.get("nombre_pages", 120))

    primary_rgb = hex_to_rgb(spec_rl.get("couleur_primaire_hex", "#3D2B1A"))
    accent_rgb = hex_to_rgb(spec_rl.get("couleur_accent_hex", "#8B6914"))

    pages_princ = structure.get("pages_principales", {})
    elements_raw = pages_princ.get("elements_par_page", ["date", "mood", "gratitude", "notes"])
    espacement_mm = float(pages_princ.get("espacement_mm", 8))
    nb_intro = int(structure.get("pages_intro", {}).get("nb_pages", 4))
    nb_bonus = int(structure.get("pages_bonus", {}).get("nb_pages", 8))
    intro_content = structure.get("pages_intro", {}).get("contenu", "Welcome to your journal...")
    bonus_content = structure.get("pages_bonus", {}).get("contenu", "")

    # Calculer nb de pages principales
    nb_main = nb_pages - 1 - nb_intro - nb_bonus - 1  # titre + fin
    nb_main = max(20, nb_main)

    print(f"[Low-Content] Titre: {titre}")
    print(f"[Low-Content] Pages: 1 titre + {nb_intro} intro + {nb_main} principales + {nb_bonus} bonus + 1 fin")
    print(f"[Low-Content] Éléments/page: {elements_raw}")

    product_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = product_dir / f"{product_dir.name}.pdf"

    c = pdf_canvas.Canvas(str(pdf_path), pagesize=(TRIM_W, TRIM_H))
    c.setTitle(titre)
    c.setAuthor(nom_de_plume)
    c.setSubject(sous_titre)

    page_num = 0

    # Page de titre
    page_num += 1
    draw_title_page(c, titre, sous_titre, nom_de_plume, primary_rgb, accent_rgb)
    c.showPage()

    # Pages d'introduction
    for i in range(nb_intro):
        page_num += 1
        draw_intro_page(c, page_num, intro_content, primary_rgb, accent_rgb)
        c.showPage()

    # Pages principales
    for i in range(nb_main):
        page_num += 1
        draw_dynamic_page(c, page_num, elements_raw, primary_rgb, accent_rgb,
                           titre, spacing_mm=espacement_mm)
        c.showPage()

    # Pages bonus
    for i in range(nb_bonus):
        page_num += 1
        draw_dynamic_page(c, page_num, ["notes", "notes", "notes"],
                           primary_rgb, accent_rgb, "Notes")
        c.showPage()

    # Page de fin
    page_num += 1
    c.setFont(SERIF_ITALIC, 12)
    c.setFillColorRGB(*accent_rgb)
    c.drawCentredString(TRIM_W / 2, TRIM_H / 2, "Thank you for using this journal.")
    c.setFont(SERIF, 9)
    c.setFillColorRGB(*primary_rgb)
    c.drawCentredString(TRIM_W / 2, TRIM_H / 2 - 20, nom_de_plume)
    c.showPage()

    c.save()

    size_mb = pdf_path.stat().st_size / 1_048_576
    print(f"\n[Low-Content] ✓ PDF généré: {pdf_path}")
    print(f"[Low-Content] Pages: {page_num} | Taille: {size_mb:.1f} MB")

    # Update cdc.json
    cdc["production_status"] = {
        "date": date.today().isoformat(),
        "pdf_path": str(pdf_path.relative_to(ROOT)),
        "pages_generees": page_num,
        "taille_mb": round(size_mb, 2),
    }
    cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")

    return pdf_path


def run():
    lc_dir = os.environ.get("LC_DIR", "")

    if lc_dir:
        product_dir = ROOT / lc_dir if not Path(lc_dir).is_absolute() else Path(lc_dir)
    else:
        # Cherche le dernier produit approved sans production
        lc_base = ROOT / "products" / "lowcontent_kdp"
        if not lc_base.exists():
            print("[Low-Content] products/lowcontent_kdp/ introuvable")
            sys.exit(1)

        approved = []
        for d in sorted(lc_base.iterdir()):
            if not d.is_dir():
                continue
            cdc_path = d / "cdc.json"
            if not cdc_path.exists():
                continue
            try:
                cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
                if cdc.get("gate_cdc") == "approved" and not cdc.get("production_status"):
                    approved.append(d)
            except Exception:
                continue

        if not approved:
            print("[Low-Content] Aucun produit avec gate_cdc=approved en attente de production.")
            print("[Low-Content] Générer un CdC: python scripts/agent_cdc_lowcontent.py")
            sys.exit(0)

        product_dir = approved[-1]

    print(f"[Low-Content] Production depuis: {product_dir}")
    pdf_path = produce_from_cdc(product_dir)
    print(f"[Low-Content] → {pdf_path}")
    print("[Low-Content] Prochaine étape: audit → agent_visual_audit.py")


if __name__ == "__main__":
    run()
