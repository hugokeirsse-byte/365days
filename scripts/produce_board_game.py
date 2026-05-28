#!/usr/bin/env python3
"""
produce_board_game.py — Génère les composants print-and-play d'un jeu de société
depuis un CdC JSON validé (gate_cdc = "approved").

Composants supportés :
  cards       — feuilles A4 recto/verso (9 cartes par page, format poker 2.5×3.5")
  rulebook    — livret A5 (couverture + règles complètes)
  tokens      — planche A4 de 40 pions ronds
  score_sheet — feuille de score avec tableau joueurs
  board       — plateau A3 (grille 6×6 + piste 30 cases pour board_game)

Variables d'env :
  JEU_DIR — chemin vers le répertoire produit (products/jeux_societe/{slug})
             Si absent, cherche le dernier CdC approuvé dans products/jeux_societe/

Sortie : products/jeux_societe/{slug}/print/*.pdf + PRINT_GUIDE.md
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4, A3, landscape
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
except ImportError:
    print("ERREUR : reportlab non installé. pip install reportlab")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
GAMES_DIR = ROOT / "products" / "jeux_societe"

VALID_TYPES = {"board_game", "card_game", "dice_game", "party_game", "educational", "rpg_accessory"}

# ── Dimensions poker card (2.5 × 3.5 inches @ 300 DPI) ──────────────────────
CARD_W_MM = 63.5   # 2.5 inches
CARD_H_MM = 88.9   # 3.5 inches
BLEED_MM = 3.0
CUT_GUIDE_MM = 2.0  # longueur des tirets de coupe

# A5 dimensions (mm)
A5_W_MM = 148.0
A5_H_MM = 210.0

# A3 dimensions (mm)
A3_W_MM = 297.0
A3_H_MM = 420.0


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def hex_to_rgb(hex_color: str) -> tuple:
    """Convertit #RRGGBB en (r, g, b) flottants 0-1."""
    h = str(hex_color).lstrip("#")
    if len(h) != 6:
        return (0.15, 0.15, 0.15)
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return (r / 255.0, g / 255.0, b / 255.0)
    except ValueError:
        return (0.15, 0.15, 0.15)


def wrap_text(text: str, max_chars: int) -> list:
    """Découpe le texte en lignes de max_chars caractères (sur les espaces)."""
    words = str(text).split()
    lines = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [""]


def draw_wrapped_text(c, x: float, y: float, text: str,
                       font: str, font_size: float,
                       max_width: float, line_height: float,
                       align: str = "left") -> float:
    """
    Dessine du texte avec retour à la ligne automatique.
    Retourne la position y après le dernier texte.
    """
    c.setFont(font, font_size)
    # Estimation caractères par ligne
    avg_char_w = font_size * 0.55
    max_chars = max(10, int(max_width / avg_char_w))
    lines = wrap_text(text, max_chars)
    for line in lines:
        if align == "center":
            c.drawCentredString(x, y, line)
        elif align == "right":
            c.drawRightString(x, y, line)
        else:
            c.drawString(x, y, line)
        y -= line_height
    return y


def _font_bold() -> str:
    return "Helvetica-Bold"


def _font_regular() -> str:
    return "Helvetica"


def _font_italic() -> str:
    return "Helvetica-Oblique"


# ─────────────────────────────────────────────────────────────────────────────
# Cards component
# ─────────────────────────────────────────────────────────────────────────────

def _draw_single_card_face(c, ox: float, oy: float,
                            cw: float, ch: float,
                            title: str, category: str, content: str,
                            palette: dict, card_n: int, total: int) -> None:
    """
    Dessine une carte (recto) dans le rectangle (ox, oy, ox+cw, oy+ch).
    oy est le coin BAS-GAUCHE (convention ReportLab).
    """
    pri = hex_to_rgb(palette.get("primaire", "#2C3E7A"))
    fond = hex_to_rgb(palette.get("fond", "#F8F4E8"))
    texte = hex_to_rgb(palette.get("texte", "#1A1A2E"))

    # Fond de carte
    c.setFillColorRGB(*fond)
    c.rect(ox, oy, cw, ch, fill=1, stroke=0)

    # Bordure colorée
    c.setStrokeColorRGB(*pri)
    c.setLineWidth(1.2)
    c.rect(ox, oy, cw, ch, fill=0, stroke=1)

    # Bande de titre (haut)
    band_h = ch * 0.18
    c.setFillColorRGB(*pri)
    c.rect(ox, oy + ch - band_h, cw, band_h, fill=1, stroke=0)

    # Titre de la carte
    c.setFillColorRGB(1, 1, 1)
    c.setFont(_font_bold(), min(9, cw / 8))
    title_str = title[:28] if len(title) > 28 else title
    c.drawCentredString(ox + cw / 2, oy + ch - band_h + band_h * 0.35, title_str)

    # Badge catégorie
    badge_y = oy + ch - band_h - 8 * mm
    badge_h = 4 * mm
    c.setFillColorRGB(*pri)
    c.setFillAlpha(0.15)
    c.rect(ox + 2 * mm, badge_y, cw - 4 * mm, badge_h, fill=1, stroke=0)
    c.setFillAlpha(1.0)
    c.setFillColorRGB(*pri)
    c.setFont(_font_italic(), min(7, cw / 9))
    cat_str = category[:30] if len(category) > 30 else category
    c.drawCentredString(ox + cw / 2, badge_y + 1 * mm, cat_str)

    # Contenu principal
    c.setFillColorRGB(*texte)
    body_top = badge_y - 3 * mm
    body_bot = oy + 6 * mm
    body_h = body_top - body_bot
    font_size = min(8.5, cw / 8.5)
    line_h = font_size * 1.4
    lines = wrap_text(content, max(10, int((cw - 4 * mm) / (font_size * 0.52))))
    max_lines = int(body_h / line_h)
    y_text = body_top - line_h
    for line in lines[:max_lines]:
        c.setFont(_font_regular(), font_size)
        c.drawCentredString(ox + cw / 2, y_text, line)
        y_text -= line_h

    # Numéro de carte
    c.setFillColorRGB(*texte)
    c.setFont(_font_regular(), 5.5)
    c.drawCentredString(ox + cw / 2, oy + 1.5 * mm, f"{card_n}/{total}")


def _draw_single_card_back(c, ox: float, oy: float,
                            cw: float, ch: float,
                            game_title: str, palette: dict) -> None:
    """Dessine le verso d'une carte."""
    pri = hex_to_rgb(palette.get("primaire", "#2C3E7A"))
    fond = hex_to_rgb(palette.get("fond", "#F8F4E8"))

    # Fond
    c.setFillColorRGB(*fond)
    c.rect(ox, oy, cw, ch, fill=1, stroke=0)

    # Bordure épaisse
    c.setStrokeColorRGB(*pri)
    c.setLineWidth(2.0)
    c.rect(ox + 1 * mm, oy + 1 * mm, cw - 2 * mm, ch - 2 * mm, fill=0, stroke=1)
    c.setLineWidth(0.5)
    c.rect(ox + 3 * mm, oy + 3 * mm, cw - 6 * mm, ch - 6 * mm, fill=0, stroke=1)

    # Titre centré
    c.setFillColorRGB(*pri)
    c.setFont(_font_bold(), min(9, cw / 7))
    title_lines = wrap_text(game_title, max(8, int(cw / (min(9, cw / 7) * 0.58))))
    ty = oy + ch / 2 + len(title_lines) * min(9, cw / 7) * 0.6
    for line in title_lines:
        c.drawCentredString(ox + cw / 2, ty, line)
        ty -= min(9, cw / 7) * 1.3

    # Petit ornement
    c.setStrokeColorRGB(*pri)
    c.setLineWidth(0.7)
    cx2 = ox + cw / 2
    deco_y = oy + ch * 0.25
    c.line(cx2 - 8 * mm, deco_y, cx2 + 8 * mm, deco_y)
    c.setFont(_font_italic(), 7)
    c.setFillColorRGB(*pri)
    c.drawCentredString(cx2, deco_y - 4 * mm, "print & play")


def _draw_cut_guides(c, ox: float, oy: float, cw: float, ch: float) -> None:
    """Dessine les petits tirets de repères de coupe aux 4 coins."""
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.setLineWidth(0.3)
    guide = CUT_GUIDE_MM * mm
    offset = 0.5 * mm

    corners = [(ox, oy), (ox + cw, oy), (ox, oy + ch), (ox + cw, oy + ch)]
    for cx2, cy2 in corners:
        # Horizontal
        if cx2 == ox:
            c.line(cx2 - guide, cy2, cx2 - offset, cy2)
        else:
            c.line(cx2 + offset, cy2, cx2 + guide, cy2)
        # Vertical
        if cy2 == oy:
            c.line(cx2, cy2 - guide, cx2, cy2 - offset)
        else:
            c.line(cx2, cy2 + offset, cx2, cy2 + guide)


def generate_cards_pdf(out_path: Path, cdc: dict) -> int:
    """
    Génère le PDF des cartes (recto + verso) — 9 cartes/page en grille 3×3.
    Retourne le nombre de cartes générées.
    """
    concept = cdc.get("concept", {})
    contenu = cdc.get("contenu_cartes", {})
    spec = cdc.get("spec_production", {})
    palette = spec.get("palette_couleurs", {})
    game_title = concept.get("titre", "Jeu de Cartes")

    # Calculer le nombre total de cartes attendu depuis composants
    composants = cdc.get("composants", [])
    total_cards = 0
    for comp in composants:
        if comp.get("type") == "cards":
            total_cards = int(comp.get("nombre", 54))
            break
    if total_cards == 0:
        total_cards = 54

    # Construire la liste de cartes depuis contenu_cartes
    cards_data = []
    categories = contenu.get("categories", [])
    for cat in categories:
        cat_name = cat.get("nom", "Carte")
        exemples = cat.get("exemples", [])
        cat_total = int(cat.get("nombre", len(exemples)))
        for ex in exemples:
            cards_data.append({
                "title": game_title[:20],
                "category": cat_name,
                "content": str(ex),
            })
        # Compléter avec des placeholders si pas assez d'exemples
        for i in range(len(exemples), cat_total):
            cards_data.append({
                "title": game_title[:20],
                "category": cat_name,
                "content": f"CARTE {len(cards_data) + 1}",
            })

    # Remplir jusqu'au total avec placeholders si nécessaire
    while len(cards_data) < total_cards:
        cards_data.append({
            "title": game_title[:20],
            "category": "Carte",
            "content": f"CARTE {len(cards_data) + 1}",
        })
    cards_data = cards_data[:total_cards]

    # Dimensions carte en points ReportLab
    cw = CARD_W_MM * mm
    ch = CARD_H_MM * mm

    # Marges et espacement sur A4
    page_w, page_h = A4  # portrait
    margin_x = (page_w - 3 * cw) / 2
    margin_y = (page_h - 3 * ch) / 2
    gap_x = 0.0
    gap_y = 0.0

    # Si les 3 cartes + marges dépassent A4, réduire les marges
    if margin_x < 5 * mm:
        margin_x = 5 * mm
    if margin_y < 5 * mm:
        margin_y = 5 * mm

    step_x = cw + gap_x
    step_y = ch + gap_y

    c = canvas.Canvas(str(out_path), pagesize=A4)
    c.setTitle(f"{game_title} — Cartes")

    pages_recto = []  # tuples (page_index_in_batch, cards_on_page)

    def flush_recto_page(batch: list) -> None:
        """Dessine une page recto de 9 cartes (ou moins)."""
        for i, card in enumerate(batch):
            col = i % 3
            row = i // 3
            ox = margin_x + col * step_x
            oy = margin_y + (2 - row) * step_y  # ligne 0 en haut = oy le plus grand
            _draw_single_card_face(
                c, ox, oy, cw, ch,
                card["title"], card["category"], card["content"],
                palette, cards_data.index(card) + 1, total_cards
            )
            _draw_cut_guides(c, ox, oy, cw, ch)
        c.showPage()

    def flush_verso_page(batch: list) -> None:
        """Dessine une page verso — ordre miroir horizontal pour impression recto-verso."""
        for i in range(len(batch)):
            col_mirror = 2 - (i % 3)  # miroir
            row = i // 3
            ox = margin_x + col_mirror * step_x
            oy = margin_y + (2 - row) * step_y
            _draw_single_card_back(c, ox, oy, cw, ch, game_title, palette)
            _draw_cut_guides(c, ox, oy, cw, ch)
        c.showPage()

    # Regrouper en pages de 9
    for page_start in range(0, len(cards_data), 9):
        batch = cards_data[page_start:page_start + 9]
        flush_recto_page(batch)
        flush_verso_page(batch)

    c.save()
    return len(cards_data)


# ─────────────────────────────────────────────────────────────────────────────
# Rulebook component
# ─────────────────────────────────────────────────────────────────────────────

def _rulebook_header(c, page_num: int, title: str, pri: tuple, page_w: float, page_h: float,
                     margin: float) -> None:
    """En-tête discret sur chaque page."""
    c.setStrokeColorRGB(*pri)
    c.setLineWidth(0.4)
    c.line(margin, page_h - margin * 0.7, page_w - margin, page_h - margin * 0.7)
    c.setFont(_font_regular(), 7)
    c.setFillColorRGB(*pri)
    c.drawRightString(page_w - margin, page_h - margin * 0.5, title[:40])
    c.setFont(_font_regular(), 7)
    c.drawString(margin, margin * 0.4, f"{page_num}")


def _rulebook_section_title(c, x: float, y: float, text: str,
                             pri: tuple, font_size: float = 13) -> float:
    """Titre de section avec ligne décorative. Retourne y après le titre."""
    c.setFont(_font_bold(), font_size)
    c.setFillColorRGB(*pri)
    c.drawString(x, y, text)
    y -= 3 * mm
    c.setStrokeColorRGB(*pri)
    c.setLineWidth(0.8)
    c.line(x, y, x + 40 * mm, y)
    return y - 5 * mm


def _rulebook_body_text(c, x: float, y: float, text: str,
                         text_rgb: tuple, page_w: float, margin: float,
                         font_size: float = 10.5) -> float:
    """Dessine un bloc de texte corps avec retour à la ligne. Retourne y final."""
    max_w = page_w - 2 * margin
    line_h = font_size * 1.45
    c.setFont(_font_regular(), font_size)
    c.setFillColorRGB(*text_rgb)
    avg_char = font_size * 0.52
    max_chars = max(20, int(max_w / avg_char))
    lines = wrap_text(text, max_chars)
    for line in lines:
        if y < margin + 10 * mm:
            break
        c.drawString(x, y, line)
        y -= line_h
    return y - 2 * mm


def _rulebook_bullet_list(c, x: float, y: float, items: list,
                            text_rgb: tuple, page_w: float, margin: float,
                            font_size: float = 10.0) -> float:
    """Liste à puces. Retourne y final."""
    max_w = page_w - 2 * margin - 5 * mm
    line_h = font_size * 1.4
    c.setFont(_font_regular(), font_size)
    c.setFillColorRGB(*text_rgb)
    avg_char = font_size * 0.52
    max_chars = max(20, int(max_w / avg_char))
    for item in items:
        if y < margin + 10 * mm:
            break
        lines = wrap_text(f"• {item}", max_chars)
        for j, line in enumerate(lines):
            if y < margin + 10 * mm:
                break
            indent = 0 if j == 0 else 3 * mm
            c.drawString(x + indent, y, line)
            y -= line_h
        y -= 1 * mm
    return y


def generate_rulebook_pdf(out_path: Path, cdc: dict) -> int:
    """
    Génère le livret de règles au format A5.
    Retourne le nombre de pages générées.
    """
    concept = cdc.get("concept", {})
    regles = cdc.get("regles_jeu", {})
    spec = cdc.get("spec_production", {})
    palette = spec.get("palette_couleurs", {})

    game_title = concept.get("titre", "Mon Jeu")
    sous_titre = concept.get("sous_titre", concept.get("tagline", ""))
    nb_min = concept.get("nb_joueurs", {}).get("min", 2)
    nb_max = concept.get("nb_joueurs", {}).get("max", 6)
    duree = concept.get("duree_partie_min", 30)
    age = concept.get("age_minimum", 12)

    pri = hex_to_rgb(palette.get("primaire", "#2C3E7A"))
    fond_rgb = hex_to_rgb(palette.get("fond", "#F8F4E8"))
    texte_rgb = hex_to_rgb(palette.get("texte", "#1A1A2E"))

    page_w = A5_W_MM * mm
    page_h = A5_H_MM * mm
    margin = 12 * mm

    c = canvas.Canvas(str(out_path), pagesize=(page_w, page_h))
    c.setTitle(f"{game_title} — Règles du jeu")
    page_count = 0

    # ── PAGE 1 : Couverture ──────────────────────────────────────────────────
    # Fond coloré
    c.setFillColorRGB(*pri)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # Cadre blanc intérieur
    inset = 6 * mm
    c.setStrokeColorRGB(1, 1, 1)
    c.setFillColorRGB(1, 1, 1)
    c.setLineWidth(0.6)
    c.rect(inset, inset, page_w - 2 * inset, page_h - 2 * inset, fill=0, stroke=1)

    # Titre
    c.setFont(_font_bold(), 22)
    c.setFillColorRGB(1, 1, 1)
    title_words = game_title.split()
    mid = max(1, len(title_words) // 2)
    t1 = " ".join(title_words[:mid])
    t2 = " ".join(title_words[mid:])
    cy_title = page_h * 0.58
    c.drawCentredString(page_w / 2, cy_title, t1)
    if t2:
        c.drawCentredString(page_w / 2, cy_title - 26, t2)
        cy_title -= 13

    # Ligne séparatrice
    c.setStrokeColorRGB(1, 1, 1)
    c.setLineWidth(1.0)
    c.line(page_w / 2 - 25 * mm, cy_title - 18, page_w / 2 + 25 * mm, cy_title - 18)

    # Sous-titre
    if sous_titre:
        c.setFont(_font_italic(), 10)
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.drawCentredString(page_w / 2, cy_title - 30, sous_titre[:55])

    # Infos joueurs / durée / âge
    info_str = f"{nb_min}–{nb_max} joueurs  |  {duree} min  |  {age}+"
    c.setFont(_font_regular(), 9)
    c.setFillColorRGB(0.85, 0.85, 0.85)
    c.drawCentredString(page_w / 2, page_h * 0.22, info_str)

    # Mention print & play
    c.setFont(_font_italic(), 7.5)
    c.setFillColorRGB(0.7, 0.7, 0.7)
    c.drawCentredString(page_w / 2, inset + 4 * mm, "Jeu print & play — à imprimer et jouer")

    c.showPage()
    page_count += 1

    # ── PAGE 2 : OBJECTIF ────────────────────────────────────────────────────
    c.setFillColorRGB(*fond_rgb)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    _rulebook_header(c, page_count + 1, game_title, pri, page_w, page_h, margin)

    y = page_h - margin - 8 * mm
    y = _rulebook_section_title(c, margin, y, "OBJECTIF DU JEU", pri, 13)
    objectif = regles.get("objectif_victoire", "Soyez le premier à atteindre l'objectif.")
    y = _rulebook_body_text(c, margin, y, objectif, texte_rgb, page_w, margin)

    y -= 6 * mm
    y = _rulebook_section_title(c, margin, y, "MISE EN PLACE", pri, 13)
    setup = regles.get("mise_en_place", "Distribuez les composants selon le guide.")
    y = _rulebook_body_text(c, margin, y, setup, texte_rgb, page_w, margin)

    c.showPage()
    page_count += 1

    # ── PAGE 3 : DÉROULEMENT ────────────────────────────────────────────────
    c.setFillColorRGB(*fond_rgb)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    _rulebook_header(c, page_count + 1, game_title, pri, page_w, page_h, margin)

    y = page_h - margin - 8 * mm
    y = _rulebook_section_title(c, margin, y, "DÉROULEMENT D'UN TOUR", pri, 13)
    deroulement = regles.get("deroulement_tour", "Le joueur actif effectue ses actions.")
    y = _rulebook_body_text(c, margin, y, deroulement, texte_rgb, page_w, margin)

    actions = regles.get("actions_possibles", [])
    if actions:
        y -= 4 * mm
        c.setFont(_font_bold(), 10)
        c.setFillColorRGB(*pri)
        c.drawString(margin, y, "Actions possibles :")
        y -= 5 * mm
        y = _rulebook_bullet_list(c, margin, y, [str(a) for a in actions[:8]],
                                   texte_rgb, page_w, margin)

    c.showPage()
    page_count += 1

    # ── PAGE 4 : FIN DE PARTIE + VARIANTES ──────────────────────────────────
    c.setFillColorRGB(*fond_rgb)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    _rulebook_header(c, page_count + 1, game_title, pri, page_w, page_h, margin)

    y = page_h - margin - 8 * mm
    y = _rulebook_section_title(c, margin, y, "FIN DE PARTIE", pri, 13)
    fin = regles.get("fin_de_partie", "La partie se termine lorsqu'un joueur remplit la condition de victoire.")
    y = _rulebook_body_text(c, margin, y, fin, texte_rgb, page_w, margin)

    variante_rapide = regles.get("variante_rapide", "")
    variante_avancee = regles.get("variante_avancee", "")

    if variante_rapide or variante_avancee:
        y -= 6 * mm
        y = _rulebook_section_title(c, margin, y, "VARIANTES", pri, 12)

        if variante_rapide:
            c.setFont(_font_bold(), 10)
            c.setFillColorRGB(*texte_rgb)
            c.drawString(margin, y, "Version rapide :")
            y -= 5 * mm
            y = _rulebook_body_text(c, margin, y, variante_rapide, texte_rgb, page_w, margin, 10)

        if variante_avancee and y > margin + 20 * mm:
            y -= 3 * mm
            c.setFont(_font_bold(), 10)
            c.setFillColorRGB(*texte_rgb)
            c.drawString(margin, y, "Version avancée :")
            y -= 5 * mm
            y = _rulebook_body_text(c, margin, y, variante_avancee, texte_rgb, page_w, margin, 10)

    # Pied de page page 4
    c.setFont(_font_italic(), 7)
    c.setFillColorRGB(*pri)
    c.drawCentredString(page_w / 2, margin * 0.45, "Bon jeu !")

    c.showPage()
    page_count += 1

    c.save()
    return page_count


# ─────────────────────────────────────────────────────────────────────────────
# Tokens component
# ─────────────────────────────────────────────────────────────────────────────

def generate_tokens_pdf(out_path: Path, cdc: dict) -> int:
    """
    Génère une planche A4 de 40 pions ronds (grille 5×8).
    Retourne le nombre de pions générés.
    """
    concept = cdc.get("concept", {})
    spec = cdc.get("spec_production", {})
    palette = spec.get("palette_couleurs", {})
    game_title = concept.get("titre", "Jeu")

    # Compter le nombre de tokens demandé
    composants = cdc.get("composants", [])
    nb_tokens = 40
    tokens_labels = []
    for comp in composants:
        if comp.get("type") == "tokens":
            nb_tokens = int(comp.get("nombre", 40))
            desc = comp.get("description", "")
            if desc:
                tokens_labels.append(desc[:20])
            break

    pri = hex_to_rgb(palette.get("primaire", "#2C3E7A"))
    fond_rgb = hex_to_rgb(palette.get("fond", "#F8F4E8"))
    texte_rgb = hex_to_rgb(palette.get("texte", "#1A1A2E"))

    page_w, page_h = A4
    margin = 10 * mm

    cols = 5
    rows = 8
    per_page = cols * rows

    # Rayon des pions
    usable_w = page_w - 2 * margin
    usable_h = page_h - 2 * margin - 15 * mm  # espace pour titre
    cell_w = usable_w / cols
    cell_h = usable_h / rows
    radius = min(cell_w, cell_h) * 0.38

    c = canvas.Canvas(str(out_path), pagesize=A4)
    c.setTitle(f"{game_title} — Pions")

    count = 0
    page_num = 0

    while count < nb_tokens:
        c.setFillColorRGB(*fond_rgb)
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

        # Titre page
        c.setFont(_font_bold(), 11)
        c.setFillColorRGB(*pri)
        page_num += 1
        c.drawCentredString(page_w / 2, page_h - margin * 0.7,
                             f"{game_title} — Pions à découper (p. {page_num})")

        batch_start = count
        batch_end = min(count + per_page, nb_tokens)

        for i in range(batch_start, batch_end):
            local_i = i - batch_start
            col = local_i % cols
            row = local_i // cols

            cx2 = margin + cell_w * col + cell_w / 2
            # y en haut de la page moins l'en-tête
            cy2 = page_h - margin - 12 * mm - cell_h * row - cell_h / 2

            # Cercle coloré
            c.setFillColorRGB(*pri)
            c.circle(cx2, cy2, radius, fill=1, stroke=0)

            # Cercle intérieur (fond)
            inner_r = radius * 0.78
            c.setFillColorRGB(*fond_rgb)
            c.circle(cx2, cy2, inner_r, fill=1, stroke=0)

            # Label
            label = tokens_labels[0] if tokens_labels else ""
            if not label:
                label = f"P{i + 1}"
            c.setFont(_font_bold(), min(8, radius * 0.7))
            c.setFillColorRGB(*texte_rgb)
            c.drawCentredString(cx2, cy2 - radius * 0.13, label[:8])

            # Repère de coupe (cercle pointillé autour)
            c.setStrokeColorRGB(0.6, 0.6, 0.6)
            c.setLineWidth(0.3)
            c.setDash(2, 3)
            c.circle(cx2, cy2, radius + 1.5 * mm, fill=0, stroke=1)
            c.setDash()

        count = batch_end
        c.showPage()

    c.save()
    return nb_tokens


# ─────────────────────────────────────────────────────────────────────────────
# Score sheet component
# ─────────────────────────────────────────────────────────────────────────────

def generate_score_sheet_pdf(out_path: Path, cdc: dict) -> int:
    """
    Génère une feuille de score A4 avec tableau joueurs × rondes.
    Retourne le nombre de pages.
    """
    concept = cdc.get("concept", {})
    spec = cdc.get("spec_production", {})
    palette = spec.get("palette_couleurs", {})
    game_title = concept.get("titre", "Jeu")
    nb_max = concept.get("nb_joueurs", {}).get("max", 6)
    duree = concept.get("duree_partie_min", 30)

    pri = hex_to_rgb(palette.get("primaire", "#2C3E7A"))
    fond_rgb = hex_to_rgb(palette.get("fond", "#F8F4E8"))
    texte_rgb = hex_to_rgb(palette.get("texte", "#1A1A2E"))

    page_w, page_h = A4
    margin = 12 * mm

    c = canvas.Canvas(str(out_path), pagesize=A4)
    c.setTitle(f"{game_title} — Feuille de score")

    c.setFillColorRGB(*fond_rgb)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # Titre
    c.setFont(_font_bold(), 16)
    c.setFillColorRGB(*pri)
    c.drawCentredString(page_w / 2, page_h - margin, game_title)

    c.setFont(_font_italic(), 9)
    c.setFillColorRGB(*texte_rgb)
    c.drawCentredString(page_w / 2, page_h - margin - 8 * mm,
                         f"Feuille de score  |  {nb_max} joueurs max  |  ~{duree} min")

    # Ligne décorative
    c.setStrokeColorRGB(*pri)
    c.setLineWidth(0.8)
    c.line(margin, page_h - margin - 13 * mm, page_w - margin, page_h - margin - 13 * mm)

    # Tableau
    table_top = page_h - margin - 20 * mm
    table_bot = margin + 20 * mm
    table_h = table_top - table_bot

    nb_players = min(int(nb_max), 8)
    nb_rounds = 12

    col_label_w = 30 * mm
    col_w = (page_w - 2 * margin - col_label_w) / nb_players

    row_label_h = 10 * mm
    row_h = (table_h - row_label_h) / nb_rounds

    # En-tête colonnes joueurs
    c.setFillColorRGB(*pri)
    c.rect(margin, table_top - row_label_h, page_w - 2 * margin, row_label_h, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(_font_bold(), 8.5)
    # Label "Tour" en haut à gauche
    c.drawCentredString(margin + col_label_w / 2,
                         table_top - row_label_h + 3 * mm, "Tour")
    for p in range(nb_players):
        cx2 = margin + col_label_w + col_w * p + col_w / 2
        c.drawCentredString(cx2, table_top - row_label_h + 3 * mm, f"Joueur {p + 1}")

    # Lignes des tours
    for r in range(nb_rounds):
        row_y = table_top - row_label_h - row_h * (r + 1)
        # Alternance de fond
        if r % 2 == 0:
            c.setFillColorRGB(pri[0], pri[1], pri[2])
            c.setFillAlpha(0.06)
            c.rect(margin, row_y, page_w - 2 * margin, row_h, fill=1, stroke=0)
            c.setFillAlpha(1.0)

        # Étiquette tour
        c.setFont(_font_bold(), 8)
        c.setFillColorRGB(*pri)
        c.drawCentredString(margin + col_label_w / 2, row_y + 3 * mm, f"Tour {r + 1}")

        # Lignes de score par joueur
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(0.25)
        for p in range(nb_players):
            lx = margin + col_label_w + col_w * p + 3 * mm
            rx = margin + col_label_w + col_w * (p + 1) - 3 * mm
            ly = row_y + row_h * 0.35
            c.line(lx, ly, rx, ly)

    # Quadrillage du tableau
    c.setStrokeColorRGB(*texte_rgb)
    c.setLineWidth(0.4)
    # Bordure externe
    c.rect(margin, table_bot, page_w - 2 * margin, table_top - table_bot + row_label_h,
           fill=0, stroke=1)
    # Ligne verticale après colonne label
    c.line(margin + col_label_w, table_bot, margin + col_label_w, table_top)
    # Lignes verticales joueurs
    for p in range(1, nb_players):
        lx = margin + col_label_w + col_w * p
        c.setLineWidth(0.25)
        c.setStrokeColorRGB(0.6, 0.6, 0.6)
        c.line(lx, table_bot, lx, table_top)
    # Lignes horizontales tours
    for r in range(nb_rounds + 1):
        ly = table_top - row_label_h - row_h * r
        c.setLineWidth(0.25)
        c.setStrokeColorRGB(0.6, 0.6, 0.6)
        c.line(margin, ly, page_w - margin, ly)

    # Ligne TOTAL
    total_y = table_bot
    c.setFillColorRGB(*pri)
    c.setFillAlpha(0.12)
    c.rect(margin, total_y - 8 * mm, page_w - 2 * margin, 8 * mm, fill=1, stroke=0)
    c.setFillAlpha(1.0)
    c.setFont(_font_bold(), 9)
    c.setFillColorRGB(*pri)
    c.drawCentredString(margin + col_label_w / 2, total_y - 5 * mm, "TOTAL")
    c.setStrokeColorRGB(*pri)
    c.setLineWidth(0.6)
    c.rect(margin, total_y - 8 * mm, page_w - 2 * margin, 8 * mm, fill=0, stroke=1)

    c.showPage()
    c.save()
    return 1


# ─────────────────────────────────────────────────────────────────────────────
# Board component
# ─────────────────────────────────────────────────────────────────────────────

def generate_board_pdf(out_path: Path, cdc: dict) -> int:
    """
    Génère le plateau au format A3.
    Pour board_game : ajoute une piste de 30 cases sur le périmètre.
    Retourne le nombre de pages.
    """
    concept = cdc.get("concept", {})
    spec = cdc.get("spec_production", {})
    palette = spec.get("palette_couleurs", {})
    type_jeu = cdc.get("type_jeu", "board_game")

    game_title = concept.get("titre", "Jeu de Plateau")
    sous_titre = concept.get("sous_titre", concept.get("tagline", ""))
    nb_min = concept.get("nb_joueurs", {}).get("min", 2)
    nb_max = concept.get("nb_joueurs", {}).get("max", 6)

    pri = hex_to_rgb(palette.get("primaire", "#2C3E7A"))
    sec_raw = palette.get("secondaire", "#E8A020")
    sec = hex_to_rgb(sec_raw)
    fond_rgb = hex_to_rgb(palette.get("fond", "#F8F4E8"))
    texte_rgb = hex_to_rgb(palette.get("texte", "#1A1A2E"))

    # A3 paysage
    page_w = A3_H_MM * mm   # 420 mm (largeur en paysage)
    page_h = A3_W_MM * mm   # 297 mm (hauteur en paysage)

    c = canvas.Canvas(str(out_path), pagesize=(page_w, page_h))
    c.setTitle(f"{game_title} — Plateau")

    margin = 10 * mm

    # Fond
    c.setFillColorRGB(*fond_rgb)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # Bordure décorative du plateau
    c.setStrokeColorRGB(*pri)
    c.setLineWidth(2.5)
    c.rect(margin, margin, page_w - 2 * margin, page_h - 2 * margin, fill=0, stroke=1)
    c.setLineWidth(0.8)
    c.setStrokeColorRGB(*sec)
    inset = margin + 2.5 * mm
    c.rect(inset, inset, page_w - 2 * inset, page_h - 2 * inset, fill=0, stroke=1)

    # Zone titre (haut)
    title_zone_h = 20 * mm
    title_y = page_h - margin - title_zone_h
    c.setFillColorRGB(*pri)
    c.rect(margin, title_y, page_w - 2 * margin, title_zone_h, fill=1, stroke=0)

    c.setFillColorRGB(1, 1, 1)
    c.setFont(_font_bold(), 20)
    c.drawCentredString(page_w / 2, title_y + title_zone_h * 0.55, game_title)
    if sous_titre:
        c.setFont(_font_italic(), 9)
        c.setFillColorRGB(0.85, 0.85, 0.85)
        c.drawCentredString(page_w / 2, title_y + 4 * mm, sous_titre[:70])

    # Infos joueurs (coin haut gauche)
    c.setFont(_font_regular(), 8)
    c.setFillColorRGB(0.85, 0.85, 0.85)
    c.drawString(margin + 3 * mm, title_y + title_zone_h * 0.55,
                 f"{nb_min}–{nb_max} joueurs")

    # Zone principale du plateau
    board_top = title_y - 2 * mm
    board_bot = margin + 18 * mm  # espace pour la légende en bas
    board_left = margin + 2 * mm
    board_right = page_w - margin - 2 * mm
    board_w = board_right - board_left
    board_h = board_top - board_bot

    if type_jeu == "board_game":
        # Piste de 30 cases sur le périmètre
        _draw_perimeter_track(c, board_left, board_bot, board_w, board_h,
                               pri, sec, fond_rgb, texte_rgb)
    else:
        # Grille 6×6 au centre
        _draw_central_grid(c, board_left, board_bot, board_w, board_h,
                            pri, sec, fond_rgb, texte_rgb)

    # Zone de légende (bas)
    legend_y = margin
    legend_h = 16 * mm
    c.setFillColorRGB(*pri)
    c.setFillAlpha(0.08)
    c.rect(margin, legend_y, page_w - 2 * margin, legend_h, fill=1, stroke=0)
    c.setFillAlpha(1.0)
    c.setFont(_font_bold(), 8)
    c.setFillColorRGB(*pri)
    c.drawString(margin + 3 * mm, legend_y + legend_h * 0.65, "LÉGENDE :")
    c.setFont(_font_regular(), 7.5)
    c.setFillColorRGB(*texte_rgb)
    c.drawString(margin + 28 * mm, legend_y + legend_h * 0.65,
                 "Départ / Arrivée    Cases spéciales    Zone centrale")

    # Mention format
    c.setFont(_font_italic(), 7)
    c.setFillColorRGB(0.6, 0.6, 0.6)
    c.drawRightString(page_w - margin - 3 * mm, legend_y + 3 * mm,
                       "Format A3 — Imprimer en paysage")

    c.showPage()
    c.save()
    return 1


def _draw_perimeter_track(c, bx: float, by: float, bw: float, bh: float,
                            pri: tuple, sec: tuple, fond_rgb: tuple, texte_rgb: tuple) -> None:
    """Dessine une piste de 30 cases autour du périmètre + zone centrale."""
    # Déterminer la taille d'une case de piste
    track_cell = min(bw, bh) * 0.12
    track_cell = max(track_cell, 12 * mm)

    # Centre du plateau pour la zone intérieure
    center_x = bx + bw / 2
    center_y = by + bh / 2
    center_w = bw - 2 * track_cell - 6 * mm
    center_h = bh - 2 * track_cell - 6 * mm

    # Zone centrale
    c.setFillColorRGB(*fond_rgb)
    c.setStrokeColorRGB(*pri)
    c.setLineWidth(1.2)
    cx0 = center_x - center_w / 2
    cy0 = center_y - center_h / 2
    c.rect(cx0, cy0, center_w, center_h, fill=1, stroke=1)

    # Grille 4×4 dans la zone centrale
    grid_cols = 4
    grid_rows = 4
    gw = center_w / grid_cols
    gh = center_h / grid_rows
    c.setStrokeColorRGB(*pri)
    c.setLineWidth(0.4)
    c.setStrokeAlpha(0.3)
    for i in range(1, grid_cols):
        c.line(cx0 + gw * i, cy0, cx0 + gw * i, cy0 + center_h)
    for j in range(1, grid_rows):
        c.line(cx0, cy0 + gh * j, cx0 + center_w, cy0 + gh * j)
    c.setStrokeAlpha(1.0)

    c.setFont(_font_bold(), 10)
    c.setFillColorRGB(*pri)
    c.drawCentredString(center_x, center_y + 3 * mm, "ZONE CENTRALE")
    c.setFont(_font_italic(), 8)
    c.setFillColorRGB(*texte_rgb)
    c.drawCentredString(center_x, center_y - 7 * mm, "Placez vos ressources ici")

    # Piste périmétrique — 30 cases réparties sur les 4 côtés
    # Calculer le nombre de cases par côté approximativement
    perimeter = 2 * (bw + bh)
    cell_size = perimeter / 30

    # Cases du bas (gauche → droite)
    n_bottom = max(1, int(bw / cell_size))
    n_right = max(1, int(bh / cell_size))
    n_top = max(1, int(bw / cell_size))
    n_left = max(1, int(bh / cell_size))

    # Ajuster pour avoir exactement 30
    total = n_bottom + n_right + n_top + n_left
    diff = 30 - total
    n_bottom += max(0, diff)

    track_cells_list = []
    # Bas : gauche → droite
    for i in range(n_bottom):
        fx = bx + bw * i / n_bottom
        fw = bw / n_bottom
        track_cells_list.append((fx, by, fw, track_cell, "h"))
    # Droite : bas → haut
    for i in range(n_right):
        fy = by + track_cell + (bh - 2 * track_cell) * i / n_right
        fh = (bh - 2 * track_cell) / n_right
        track_cells_list.append((bx + bw - track_cell, fy, track_cell, fh, "v"))
    # Haut : droite → gauche
    for i in range(n_top):
        fx = bx + bw - bw * i / n_top
        fw = bw / n_top
        track_cells_list.append((fx - fw, by + bh - track_cell, fw, track_cell, "h"))
    # Gauche : haut → bas
    for i in range(n_left):
        fy = by + bh - track_cell - (bh - 2 * track_cell) * i / n_left
        fh = (bh - 2 * track_cell) / n_left
        track_cells_list.append((bx, fy - fh, track_cell, fh, "v"))

    for idx, (fx, fy, fw, fh, orient) in enumerate(track_cells_list[:30]):
        # Case numérotée
        is_start = idx == 0
        is_special = idx % 5 == 0 and idx > 0

        if is_start:
            c.setFillColorRGB(*sec)
        elif is_special:
            c.setFillColorRGB(*pri)
            c.setFillAlpha(0.25)
        else:
            c.setFillColorRGB(*fond_rgb)
        c.rect(fx, fy, fw, fh, fill=1, stroke=0)
        c.setFillAlpha(1.0)

        c.setStrokeColorRGB(*pri)
        c.setLineWidth(0.5)
        c.rect(fx, fy, fw, fh, fill=0, stroke=1)

        # Numéro de case
        font_sz = min(fw, fh) * 0.28
        font_sz = max(5, min(font_sz, 9))
        c.setFont(_font_bold() if is_start else _font_regular(), font_sz)
        c.setFillColorRGB(1, 1, 1) if is_start else c.setFillColorRGB(*texte_rgb)
        label = "START" if is_start else str(idx + 1)
        c.drawCentredString(fx + fw / 2, fy + fh / 2 - font_sz * 0.4, label)


def _draw_central_grid(c, bx: float, by: float, bw: float, bh: float,
                        pri: tuple, sec: tuple, fond_rgb: tuple, texte_rgb: tuple) -> None:
    """Dessine une grille 6×6 centrée sur le plateau."""
    cols = 6
    rows = 6
    # Taille maximale de la grille
    cell_size = min(bw * 0.85 / cols, bh * 0.85 / rows)
    grid_w = cell_size * cols
    grid_h = cell_size * rows
    gx = bx + (bw - grid_w) / 2
    gy = by + (bh - grid_h) / 2

    for row in range(rows):
        for col in range(cols):
            cx2 = gx + col * cell_size
            cy2 = gy + row * cell_size

            # Alternance de couleurs style échiquier léger
            if (row + col) % 2 == 0:
                c.setFillColorRGB(*fond_rgb)
            else:
                c.setFillColorRGB(*pri)
                c.setFillAlpha(0.08)
            c.rect(cx2, cy2, cell_size, cell_size, fill=1, stroke=0)
            c.setFillAlpha(1.0)

            c.setStrokeColorRGB(*pri)
            c.setLineWidth(0.6)
            c.rect(cx2, cy2, cell_size, cell_size, fill=0, stroke=1)

    # Bordure épaisse de la grille
    c.setStrokeColorRGB(*pri)
    c.setLineWidth(2.0)
    c.rect(gx, gy, grid_w, grid_h, fill=0, stroke=1)

    # Étiquettes colonnes (A-F) et lignes (1-6)
    c.setFont(_font_bold(), cell_size * 0.22)
    c.setFillColorRGB(*texte_rgb)
    for col in range(cols):
        label = chr(ord("A") + col)
        c.drawCentredString(gx + col * cell_size + cell_size / 2,
                             gy + grid_h + 2 * mm, label)
    for row in range(rows):
        label = str(rows - row)
        c.drawCentredString(gx - 4 * mm, gy + row * cell_size + cell_size / 2, label)


# ─────────────────────────────────────────────────────────────────────────────
# Print guide
# ─────────────────────────────────────────────────────────────────────────────

def generate_print_guide(out_path: Path, cdc: dict, generated: dict) -> None:
    """Génère le PRINT_GUIDE.md expliquant comment imprimer chaque composant."""
    concept = cdc.get("concept", {})
    game_title = concept.get("titre", "Mon Jeu")
    nb_min = concept.get("nb_joueurs", {}).get("min", 2)
    nb_max = concept.get("nb_joueurs", {}).get("max", 6)

    lines = [
        f"# GUIDE D'IMPRESSION — {game_title}",
        "",
        f"Jeu pour {nb_min}–{nb_max} joueurs | Print & Play",
        "",
        "---",
        "",
        "## Fichiers à imprimer",
        "",
    ]

    file_infos = {
        "cards.pdf": {
            "format": "A4",
            "copies": str(nb_max),
            "note": "Recto-verso activé. Couper le long des repères (tirets gris).",
            "instructions": [
                "Imprimer en **recto-verso** (retournement sur le bord long).",
                f"Imprimer **{nb_max} exemplaire(s)** pour {nb_max} joueurs.",
                "Couper le long des tirets de repère (traits gris aux coins).",
                "Format de carte obtenu : 2.5 × 3.5 pouces (poker standard).",
            ],
        },
        "rulebook.pdf": {
            "format": "A5 (ou A4 plié en deux)",
            "copies": "1 par joueur ou 1 par table",
            "note": "Imprimer en A5 direct ou en A4 recto-verso puis plier.",
            "instructions": [
                "Imprimer en **A5** si votre imprimante le supporte.",
                "Sinon, imprimer en A4 **recto-verso** et plier en deux.",
                "Agrafer au centre si nécessaire.",
                "1 exemplaire par table est suffisant.",
            ],
        },
        "tokens.pdf": {
            "format": "A4",
            "copies": "1",
            "note": "Découper les cercles le long des tirets pointillés.",
            "instructions": [
                "Imprimer sur papier épais (200g/m² recommandé) ou coller sur carton.",
                "Découper les pions le long des cercles pointillés.",
                "Option : plastifier avant découpe pour plus de durabilité.",
            ],
        },
        "score_sheet.pdf": {
            "format": "A4",
            "copies": "plusieurs (1 par partie)",
            "note": "Imprimer autant d'exemplaires que de parties prévues.",
            "instructions": [
                "Imprimer en **A4** standard.",
                "Prévoir **1 feuille par partie** (peut être réutilisée au crayon).",
                "Conserver dans la boîte du jeu.",
            ],
        },
        "board.pdf": {
            "format": "A3 paysage",
            "copies": "1",
            "note": "Imprimer en A3 paysage. Plastifier recommandé.",
            "instructions": [
                "Imprimer en **A3 paysage** (orientation : paysage).",
                "Si imprimante A4 seulement : imprimer en 2 moitiés et coller (option dans Acrobat : « Affiche »).",
                "Plastifier pour plus de durabilité.",
                "Option : coller sur carton plume (5mm).",
            ],
        },
    }

    for fname, info in file_infos.items():
        if fname not in generated:
            continue
        lines.append(f"### `{fname}`")
        lines.append("")
        lines.append(f"- **Format papier** : {info['format']}")
        lines.append(f"- **Copies** : {info['copies']}")
        lines.append(f"- **Note** : {info['note']}")
        lines.append("")
        lines.append("**Instructions :**")
        for instr in info["instructions"]:
            lines.append(f"- {instr}")
        lines.append("")

    lines += [
        "---",
        "",
        "## Matériel supplémentaire recommandé",
        "",
        "- Ciseaux ou massicot pour la découpe",
        "- Plastifieuse (optionnelle mais conseillée pour les cartes)",
        "- Dés standards (non inclus)",
        "- Pions de couleur (épingles, bouchons ou pièces de monnaie si pions non inclus)",
        "",
        "## Instructions de découpe des cartes",
        "",
        "1. Imprimer `cards.pdf` en recto-verso.",
        "2. Vérifier l'alignement : le verso doit être **miroir** du recto.",
        "3. Couper d'abord les rangées horizontales, puis les colonnes.",
        "4. Les tirets gris indiquent exactement où couper.",
        "5. Optionnel : arrondir les coins avec un perforatrice coin arrondi.",
        "",
        "---",
        "",
        f"*Guide généré automatiquement le {datetime.now().strftime('%Y-%m-%d')}*",
    ]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [guide] {out_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrateur principal
# ─────────────────────────────────────────────────────────────────────────────

def find_latest_approved_game() -> Path | None:
    """Cherche le dernier CdC approuvé dans products/jeux_societe/."""
    if not GAMES_DIR.exists():
        return None
    candidates = []
    for d in GAMES_DIR.iterdir():
        if not d.is_dir():
            continue
        cdc_path = d / "cdc.json"
        if not cdc_path.exists():
            continue
        try:
            cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
            if (cdc.get("gate_cdc") == "approved"
                    and cdc.get("type_jeu") in VALID_TYPES
                    and not cdc.get("production_status")):
                candidates.append((d.stat().st_mtime, d))
        except Exception:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[-1][1]


def produce_game(product_dir: Path) -> None:
    """Orchestre la production complète depuis le cdc.json d'un jeu."""
    cdc_path = product_dir / "cdc.json"
    if not cdc_path.exists():
        print(f"[BoardGame] ERREUR : cdc.json introuvable dans {product_dir}")
        sys.exit(1)

    cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
    gate = cdc.get("gate_cdc", "pending")

    if gate == "pending":
        print(f"[BoardGame] GATE = pending — Hugo doit valider {product_dir.name} avant production.")
        print(f"[BoardGame] Éditer cdc.json → gate_cdc: 'approved' puis push.")
        sys.exit(0)
    if gate == "rejected":
        print(f"[BoardGame] GATE = rejected — Production annulée pour {product_dir.name}.")
        sys.exit(0)

    type_jeu = cdc.get("type_jeu", "")
    if type_jeu not in VALID_TYPES:
        print(f"[BoardGame] type_jeu='{type_jeu}' non reconnu. Acceptés : {VALID_TYPES}")
        sys.exit(1)

    concept = cdc.get("concept", {})
    game_title = concept.get("titre", product_dir.name)
    print(f"\n[BoardGame] Production : '{game_title}' ({type_jeu})")
    print(f"[BoardGame] Répertoire : {product_dir}")

    # Créer le répertoire de sortie
    print_dir = product_dir / "print"
    print_dir.mkdir(parents=True, exist_ok=True)

    composants = cdc.get("composants", [])
    comp_types = {c.get("type", "") for c in composants}

    generated_files = {}
    stats = {}

    # ── Cartes ───────────────────────────────────────────────────────────────
    if "cards" in comp_types or type_jeu in {"card_game", "party_game", "educational"}:
        out = print_dir / "cards.pdf"
        print(f"  [cards] Génération des cartes...")
        n = generate_cards_pdf(out, cdc)
        generated_files["cards.pdf"] = out
        stats["cards"] = n
        print(f"  [cards] {n} cartes → {out.name}")

    # ── Rulebook ─────────────────────────────────────────────────────────────
    needs_rulebook = any(c.get("type") == "rulebook" for c in composants)
    if needs_rulebook or True:  # le rulebook est toujours généré
        out = print_dir / "rulebook.pdf"
        print(f"  [rulebook] Génération du livret de règles...")
        n = generate_rulebook_pdf(out, cdc)
        generated_files["rulebook.pdf"] = out
        stats["rulebook"] = n
        print(f"  [rulebook] {n} pages → {out.name}")

    # ── Tokens ───────────────────────────────────────────────────────────────
    if "tokens" in comp_types:
        out = print_dir / "tokens.pdf"
        print(f"  [tokens] Génération des pions...")
        n = generate_tokens_pdf(out, cdc)
        generated_files["tokens.pdf"] = out
        stats["tokens"] = n
        print(f"  [tokens] {n} pions → {out.name}")

    # ── Score sheet ──────────────────────────────────────────────────────────
    if "score_sheet" in comp_types or type_jeu in {"dice_game"}:
        out = print_dir / "score_sheet.pdf"
        print(f"  [score_sheet] Génération de la feuille de score...")
        n = generate_score_sheet_pdf(out, cdc)
        generated_files["score_sheet.pdf"] = out
        stats["score_sheet"] = n
        print(f"  [score_sheet] {n} page(s) → {out.name}")

    # ── Board ────────────────────────────────────────────────────────────────
    if "board" in comp_types or type_jeu == "board_game":
        out = print_dir / "board.pdf"
        print(f"  [board] Génération du plateau...")
        n = generate_board_pdf(out, cdc)
        generated_files["board.pdf"] = out
        stats["board"] = n
        print(f"  [board] {n} page(s) A3 → {out.name}")

    # ── Print Guide ──────────────────────────────────────────────────────────
    guide_path = print_dir / "PRINT_GUIDE.md"
    generate_print_guide(guide_path, cdc, generated_files)

    # ── Mise à jour cdc.json ─────────────────────────────────────────────────
    cdc["production_status"] = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "print_dir": str(print_dir.relative_to(ROOT)) if print_dir.is_relative_to(ROOT) else str(print_dir),
        "fichiers_generes": list(generated_files.keys()),
        "stats": stats,
    }
    cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[BoardGame] cdc.json mis à jour (production_status)")

    # ── Résumé ───────────────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"  PRODUCTION TERMINÉE : {game_title}")
    print(f"{'=' * 60}")
    for fname, fpath in generated_files.items():
        size = fpath.stat().st_size / 1024
        print(f"  {fname:25s}  {size:6.1f} KB  → {fpath}")
    print(f"  {'PRINT_GUIDE.md':25s}             → {guide_path}")
    print(f"{'=' * 60}")
    print(f"\n  Répertoire de sortie : {print_dir}")
    print(f"  Prêt à imprimer — voir PRINT_GUIDE.md pour les instructions.")


def run() -> None:
    jeu_dir = os.environ.get("JEU_DIR", "").strip()

    if jeu_dir:
        product_dir = ROOT / jeu_dir if not Path(jeu_dir).is_absolute() else Path(jeu_dir)
        if not product_dir.exists():
            print(f"[BoardGame] ERREUR : répertoire introuvable : {product_dir}")
            sys.exit(1)
    else:
        print("[BoardGame] JEU_DIR non défini — recherche du dernier CdC approuvé...")
        product_dir = find_latest_approved_game()
        if product_dir is None:
            print("[BoardGame] Aucun jeu avec gate_cdc=approved trouvé dans products/jeux_societe/")
            print("[BoardGame] 1. Générer un CdC : python scripts/agent_jeux_societe_cdc.py")
            print("[BoardGame] 2. Valider : éditer cdc.json → gate_cdc: 'approved'")
            sys.exit(0)

    print(f"[BoardGame] Répertoire produit : {product_dir}")
    produce_game(product_dir)


if __name__ == "__main__":
    run()
