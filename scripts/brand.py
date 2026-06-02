"""
BrightOwl Learning — Brand constants partagés par tous les pipelines.
Modifier ici = appliqué partout (TPT + KDP).
"""
from reportlab.lib.colors import HexColor, white, black

BRAND = {
    "name":         "BrightOwl Learning",
    "tagline":      "Engaging resources for curious learners.",
    "website":      "brightowllearning.com",
    "tpt_store":    "BrightOwlLearning",
    "primary":      "#E8771A",   # orange chaud
    "secondary":    "#2C3E50",   # navy
    "accent":       "#F1C40F",   # jaune
    "light":        "#FFF8F0",   # blanc chaud
    "footer":       "BrightOwl Learning · No Prep · Just Print",
    "copyright":    "For single classroom use only. Not for redistribution.",
}

# Raccourcis couleurs ReportLab
C_PRIMARY   = HexColor(BRAND["primary"])
C_SECONDARY = HexColor(BRAND["secondary"])
C_ACCENT    = HexColor(BRAND["accent"])
C_LIGHT     = HexColor(BRAND["light"])


def footer(c, page_w, margin, year=2026):
    from reportlab.lib.units import inch
    c.saveState()
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(HexColor("#999999"))
    c.drawString(margin, 0.28 * inch,
                 f"© {year} {BRAND['name']}  —  {BRAND['copyright']}")
    c.drawRightString(page_w - margin, 0.28 * inch, BRAND["footer"])
    c.restoreState()


def header_band(c, page_w, page_h, margin, title, subtitle="", color_hex=None):
    """Bandeau de titre standardisé, retourne la coordonnée y juste en dessous."""
    from reportlab.lib.units import inch
    hx = HexColor(color_hex or BRAND["primary"])
    hh = 0.65 * inch
    hy = page_h - margin - hh
    c.setFillColor(hx)
    c.roundRect(margin, hy, page_w - 2 * margin, hh, 8, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(page_w / 2, hy + hh / 2 - 5, title)
    if subtitle:
        c.setFont("Helvetica", 10)
        c.drawCentredString(page_w / 2, hy + 7, subtitle)
    return hy - 0.25 * inch


def lighten(hex_: str, factor: float = 0.82) -> str:
    r, g, b = int(hex_[1:3], 16), int(hex_[3:5], 16), int(hex_[5:7], 16)
    return "#{:02X}{:02X}{:02X}".format(
        int(r + (255 - r) * factor),
        int(g + (255 - g) * factor),
        int(b + (255 - b) * factor),
    )


def text_color_on(hex_: str) -> object:
    """Retourne white ou black selon la luminosité du fond."""
    r, g, b = int(hex_[1:3], 16), int(hex_[3:5], 16), int(hex_[5:7], 16)
    return white if (r * 299 + g * 587 + b * 114) / 1000 < 140 else black
