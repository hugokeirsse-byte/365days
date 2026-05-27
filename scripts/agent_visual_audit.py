"""
VISUAL AUDIT v3 — Auditeur multi-produits aligné sur les exigences consommateurs.

Chaque type de produit a ses propres critères, calqués sur ce que les acheteurs
vérifient et ce qui génère des 1 étoile ou des retours. L'audit reflète la réalité
commerciale, pas des métriques techniques arbitraires.

PRODUITS COUVERTS :
  coloring_books   → KDP paperback coloriage
  lowcontent_kdp   → KDP journaux/planners/trackers (ReportLab)
  stl_parametric   → Fichiers STL pour Cults3D / Printables
  card_game        → Jeux de cartes imprimables (Etsy / TGC)
  novels           → Romans KDP (Groq / Gemini)
  bible_verses     → Versets bibliques print-on-demand
  *                → Générique (iHeart, viral, cultural_arbitrage, etc.)

PHILOSOPHIE :
  - REJECT = ne pas uploader, le produit ferait mauvaise réputation
  - REVIEW = borderline, Hugo doit regarder avant de décider
  - APPROVE = viable commercialement, peut être uploadé

Variables d'env :
  AUTO_REJECT=1     déplace les rejected vers products/_rejected/
  PIPELINE=xxx      audite seulement ce pipeline
  MIN_APPROVE=65    seuil d'approbation (défaut 65)
"""

import json
import os
import shutil
import struct
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev

try:
    from PIL import Image, ImageStat
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

HAS_TESSERACT = False
try:
    import subprocess
    r = subprocess.run(["tesseract", "--version"], capture_output=True, timeout=5)
    HAS_TESSERACT = r.returncode == 0
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"
DATA_DIR = ROOT / "data"
REJECTED_DIR = PRODUCTS_DIR / "_rejected"

MIN_APPROVE = float(os.environ.get("MIN_APPROVE", "65"))


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES COMMUNS
# ═══════════════════════════════════════════════════════════════════════════════

def ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


def load_meta(directory: Path) -> dict:
    meta = directory / "metadata.json"
    if meta.exists():
        try:
            return json.loads(meta.read_text())
        except Exception:
            pass
    return {}


def find_images(directory: Path, extensions=(".png", ".jpg", ".jpeg")) -> list[Path]:
    imgs = []
    for ext in extensions:
        imgs += list(directory.rglob(f"*{ext}"))
    return sorted(imgs)


def find_images_pages(directory: Path) -> list[Path]:
    """Trouve les pages d'un livre (pages/ ou page_*.png à la racine)."""
    pages_dir = directory / "pages"
    if pages_dir.exists():
        imgs = find_images(pages_dir)
        if imgs:
            return imgs
    imgs = sorted(list(directory.glob("page_*.png")) + list(directory.glob("page_*.jpg")))
    return imgs


def pixel_analysis(img_gray) -> dict:
    """Analyse rapide de la distribution de pixels en niveaux de gris."""
    w, h = img_gray.size
    total = w * h
    pixels = list(img_gray.getdata())
    dark   = sum(1 for p in pixels if p <= 40)
    mid    = sum(1 for p in pixels if 41 <= p <= 214)
    light  = sum(1 for p in pixels if p >= 215)
    return {
        "fill_pct":   round(dark  / total * 100, 2),
        "gray_pct":   round(mid   / total * 100, 2),
        "white_pct":  round(light / total * 100, 2),
        "purity_pct": round((dark + light) / total * 100, 2),
        "w": w, "h": h,
    }


def band_composition(img_gray, n=5) -> list[dict]:
    """Découpe l'image en n bandes horizontales et analyse chaque bande."""
    w, h = img_gray.size
    band_h = max(1, h // n)
    result = []
    for i in range(n):
        y0, y1 = i * band_h, min((i + 1) * band_h, h)
        band = img_gray.crop((0, y0, w, y1))
        px = list(band.getdata())
        dark = sum(1 for p in px if p <= 40)
        result.append({"band": i, "fill_pct": round(dark / max(len(px), 1) * 100, 1)})
    return result


def ocr_text(image_path: Path) -> str:
    if not HAS_TESSERACT:
        return ""
    try:
        r = subprocess.run(
            ["tesseract", str(image_path), "-", "--psm", "6"],
            capture_output=True, timeout=30,
        )
        return r.stdout.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


COMMON_ENGLISH = {
    "a", "the", "is", "of", "and", "to", "in", "i", "it", "you", "that", "he",
    "was", "for", "on", "are", "with", "as", "his", "they", "at", "be", "this",
    "have", "from", "or", "one", "had", "by", "but", "not", "what", "all", "were",
    "we", "when", "your", "can", "said", "love", "my", "me", "her", "him", "she",
    "an", "if", "do", "will", "no", "so", "out", "go", "up", "got", "now", "good",
    "best", "more", "less", "new", "old", "any", "way", "cat", "dog", "coffee",
    "tea", "yoga", "mom", "dad", "girl", "boy", "life", "joy", "hope", "faith",
    "peace", "strength", "grace", "lord", "god", "blessed", "heart", "soul",
    "fishing", "hiking", "camping", "knitting", "gardening", "chess", "baking",
}


def text_score(text: str) -> float:
    if not text or len(text.strip()) < 3:
        return 50
    words = [w.lower().strip(".,!?;:\"'") for w in text.split() if w.strip()]
    if not words:
        return 50
    matches = sum(1 for w in words if w in COMMON_ENGLISH or len(w) <= 2)
    ratio = matches / len(words)
    if len(words) >= 5 and ratio < 0.25:
        return 5   # gibberish probable → très grave
    if ratio < 0.4:
        return 30
    if ratio < 0.6:
        return 65
    return 90


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT COLORIAGE KDP
# Critères consommateurs Amazon :
#   - "Flou à l'impression" → résolution
#   - "Lignes disparues" → pureté des lignes
#   - "Styles complètement différents selon les pages" → cohérence
#   - "Pas assez de pages pour le prix" → quantité
#   - "Champignons mais aussi des chats ?" → cohérence du thème
#   - "Plein d'espace vide" → composition
# ═══════════════════════════════════════════════════════════════════════════════

def audit_coloring(product_dir: Path) -> dict:
    issues = []
    warnings = []
    score = 100

    pages = find_images_pages(product_dir)
    if not pages:
        return {"score": 0, "issues": ["Aucune page trouvée — produit vide"], "warnings": []}

    # 1. QUANTITÉ — KDP impose 24 pages min, 30+ pour justifier le prix
    if len(pages) < 20:
        issues.append(f"Seulement {len(pages)} pages. Un livre de coloriage KDP viable nécessite ≥30 pages. Les acheteurs laissent 1★ pour 'pas assez de contenu'.")
        score -= 40
    elif len(pages) < 30:
        warnings.append(f"{len(pages)} pages — acceptable mais borderline pour le prix (30+ recommandé).")
        score -= 10

    if not HAS_PIL:
        return {"score": max(0, score), "issues": issues + ["[Pillow manquant — analyse pixel impossible]"], "warnings": warnings}

    fills, grays, purities, resolutions = [], [], [], []
    low_res_pages, gray_pages, empty_pages, overfull_pages, composition_bad = [], [], [], [], []

    for img_path in pages:
        try:
            img = Image.open(img_path).convert("L")
        except Exception as e:
            issues.append(f"{img_path.name} illisible: {e}")
            score -= 5
            continue

        w, h = img.size
        resolutions.append(min(w, h))

        # KDP 6×9" à 300 DPI = 1800×2700px. Seuil minimum absolu : 1400px (côté court)
        if min(w, h) < 1400:
            dpi_est = round(min(w, h) / 9 * 10) / 10  # estimation DPI pour 6×9"
            low_res_pages.append(f"{img_path.name} ({w}×{h}px ≈ {dpi_est:.0f} DPI)")

        pa = pixel_analysis(img)
        fills.append(pa["fill_pct"])
        grays.append(pa["gray_pct"])
        purities.append(pa["purity_pct"])

        # Contamination grise — hachures AI, ombres douces = zones sans couleur claire
        if pa["gray_pct"] > 15:
            gray_pages.append(f"{img_path.name} ({pa['gray_pct']:.0f}% pixels gris)")

        # Pages trop vides (< 4% de trait = feuille presque blanche)
        if pa["fill_pct"] < 4:
            empty_pages.append(f"{img_path.name} ({pa['fill_pct']:.1f}% lignes)")

        # Pages surchargées (> 55% = zones trop petites, frustrant à colorier)
        if pa["fill_pct"] > 55:
            overfull_pages.append(f"{img_path.name} ({pa['fill_pct']:.0f}% lignes)")

        # Composition : bandes vides en haut/bas = sujet mal cadré
        bands = band_composition(img)
        top_fill = bands[0]["fill_pct"]
        bot_fill = bands[-1]["fill_pct"]
        if top_fill < 0.5 or bot_fill < 0.5:
            composition_bad.append(f"{img_path.name} (haut={top_fill}% bot={bot_fill}%)")

    # 2. RÉSOLUTION — critique pour impression
    if low_res_pages:
        pct = len(low_res_pages) / len(pages) * 100
        msg = (
            f"{len(low_res_pages)}/{len(pages)} pages ({pct:.0f}%) sous-résolues : "
            f"{', '.join(low_res_pages[:4])}. "
            f"KDP imprimera ces images floues — cause directe de 1★ 'qualité médiocre à l'impression'."
        )
        if pct >= 80:
            issues.append("BLOQUANT — " + msg)
            score -= 50
        elif pct >= 40:
            issues.append("MAJEUR — " + msg)
            score -= 25
        else:
            warnings.append(msg)
            score -= 10

    # 3. CONTAMINATION GRISE — lignes sales, zones non colorables
    if gray_pages:
        pct = len(gray_pages) / len(pages) * 100
        msg = (
            f"{len(gray_pages)} pages avec demi-tons gris (ombres/hachures AI) : "
            f"{', '.join(gray_pages[:4])}. "
            f"Ces zones grises ne sont pas colorables proprement — plainte consommateur typique : 'les lignes sont floues'."
        )
        if pct > 50:
            issues.append("CRITIQUE — " + msg)
            score -= 25
        elif pct > 20:
            issues.append(msg)
            score -= 12
        else:
            warnings.append(msg)
            score -= 5

    # 4. COHÉRENCE DE STYLE — variance de densité entre pages
    if len(fills) >= 5:
        fill_std = stdev(fills)
        fill_mean = mean(fills)
        if fill_std > 12:
            issues.append(
                f"INCOHÉRENCE DE STYLE DÉTECTÉE — densité de trait : moy={fill_mean:.0f}%, "
                f"écart-type={fill_std:.0f}% (seuil = 12%). "
                f"Les {len(pages)} pages semblent provenir de styles artistiques différents. "
                f"Un acheteur qui feuillette le 'Look Inside' Amazon verra un livre incohérent → refus d'achat."
            )
            score -= 25
        elif fill_std > 7:
            warnings.append(f"Style modérément variable (std={fill_std:.0f}%). Vérifier visuellement la cohérence.")
            score -= 8

    # 5. PAGES VIDES ET SURCHARGÉES
    if empty_pages:
        issues.append(
            f"{len(empty_pages)} pages quasi-vides : {', '.join(empty_pages[:3])}. "
            f"L'acheteur a l'impression de payer pour du papier blanc."
        )
        score -= 12 * len(empty_pages)

    if overfull_pages:
        warnings.append(
            f"{len(overfull_pages)} pages très chargées : {', '.join(overfull_pages[:3])}. "
            f"Les zones à colorier sont minuscules — frustrant avec des crayons normaux."
        )
        score -= 5

    # 6. COMPOSITION
    if len(composition_bad) > 3:
        warnings.append(
            f"{len(composition_bad)} pages mal cadrées (espace vide haut/bas) : "
            f"{', '.join(composition_bad[:4])}. Vérifier le cadrage."
        )
        score -= 10

    # 7. COUVERTURE
    cover = product_dir / "cover_front.png"
    if not cover.exists():
        cover = next(product_dir.glob("cover*.png"), None) or next(product_dir.glob("cover*.jpg"), None)
    if not cover:
        warnings.append("Pas de couverture trouvée. KDP exige une couverture séparée — sans ça le produit est incomplet.")
        score -= 15
    elif HAS_PIL:
        try:
            cimg = Image.open(cover)
            cw, ch = cimg.size
            if min(cw, ch) < 1400:
                warnings.append(f"Couverture sous-résolue ({cw}×{ch}px). KDP Cover Creator exige ≥300 DPI.")
                score -= 10
        except Exception:
            pass

    score = max(0, score)

    human_checks = [
        "Cohérence visuelle du style artistique sur toutes les pages (chibi vs botanique vs réaliste ?)",
        "Thème respecté à chaque page (ex: champignons présents sur TOUTES les pages ?)",
        "Lignes assez épaisses pour être visibles imprimées (tester une impression test)",
        "Niveau de difficulté approprié à l'audience cible (adulte = complexe, enfant = simple)",
        "Couverture suffisamment attractive face aux 100+ concurrents sur Amazon",
    ]

    return {
        "score": score,
        "nb_pages": len(pages),
        "fill_mean": round(mean(fills), 1) if fills else 0,
        "fill_std": round(stdev(fills), 1) if len(fills) >= 2 else 0,
        "gray_mean": round(mean(grays), 1) if grays else 0,
        "low_res_count": len(low_res_pages),
        "gray_pages_count": len(gray_pages),
        "empty_pages_count": len(empty_pages),
        "issues": issues,
        "warnings": warnings,
        "human_checks": human_checks,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT LOW-CONTENT KDP
# Critères consommateurs :
#   - "Trop peu de pages pour le prix" → count pages
#   - "Lignes trop légères pour écrire" → niveau gris des lignes
#   - "Pareil que les 1000 autres journaux" → élément différenciant
#   - "Marges coupées à l'impression" → zone de sécurité
#   - "PDF corrompu / vide" → validité fichier
# ═══════════════════════════════════════════════════════════════════════════════

def count_pdf_pages(pdf_path: Path) -> int:
    """Compte les pages d'un PDF sans dépendance externe."""
    try:
        content = pdf_path.read_bytes()
        # Compte les entrées /Page (hors /Pages)
        import re
        matches = re.findall(b"/Type\s*/Page[^s]", content)
        if matches:
            return len(matches)
        # Fallback: cherche /Count
        counts = re.findall(b"/Count\s+(\d+)", content)
        if counts:
            return int(counts[-1])
        return 0
    except Exception:
        return 0


def audit_lowcontent(product_dir: Path) -> dict:
    issues = []
    warnings = []
    score = 100
    meta = load_meta(product_dir)

    # 1. PDF présent et valide
    pdfs = list(product_dir.glob("*.pdf"))
    if not pdfs:
        issues.append("Aucun PDF trouvé — produit vide, impossible à uploader sur KDP.")
        score -= 60
        return {"score": max(0, score), "issues": issues, "warnings": warnings}

    pdf = pdfs[0]
    file_size_kb = pdf.stat().st_size / 1024

    if file_size_kb < 20:
        issues.append(f"PDF trop petit ({file_size_kb:.0f} KB) — probablement vide ou corrompu.")
        score -= 50

    # 2. NOMBRE DE PAGES — critère #1 de valeur perçue
    pages_from_meta = meta.get("pages_count", 0)
    pages_from_pdf = count_pdf_pages(pdf)
    pages = pages_from_meta or pages_from_pdf

    if pages == 0:
        warnings.append(f"Nombre de pages non détectable (PDF: {pages_from_pdf}, meta: {pages_from_meta}). Vérifier manuellement.")
        score -= 10
    elif pages < 80:
        issues.append(
            f"Seulement {pages} pages. Les acheteurs Amazon KDP comparent au prix : "
            f"à 7-9$ un journal doit avoir 100-120 pages minimum pour paraître 'valeur'. "
            f"En dessous, les avis disent 'trop cher pour si peu'."
        )
        score -= 30
    elif pages < 100:
        warnings.append(f"{pages} pages — acceptable mais 120+ serait idéal pour justifier le prix.")
        score -= 8

    # 3. TRIM SIZE — KDP standard
    trim = meta.get("trim_size", "")
    if trim and "6 x 9" not in trim and "5.5 x 8.5" not in trim and "8.5 x 11" not in trim:
        warnings.append(f"Format '{trim}' non-standard KDP. Les formats validés sont : 6×9, 5.5×8.5, 8.5×11.")
        score -= 5

    # 4. INTERIOR TYPE — critère de production
    interior = meta.get("interior_type", "")
    if "color" in interior.lower():
        warnings.append("Interior en couleur détecté — KDP color printing coûte ~3× plus cher, réduisant le royaltie à presque zéro. Recommandé : noir et blanc.")
        score -= 10

    # 5. DIFFÉRENCIATION — a-t-on un élément unique ?
    title = meta.get("title", "")
    subtitle = meta.get("subtitle", "")
    if not subtitle:
        warnings.append("Pas de sous-titre. Sur Amazon, le sous-titre est crucial pour expliquer la valeur unique vs les 10,000 autres journaux.")
        score -= 5

    # 6. MÉTADONNÉES KDP COMPLÈTES
    required_meta = ["title", "kdp_keywords", "categories", "price_kdp_suggested"]
    missing = [k for k in required_meta if not meta.get(k)]
    if missing:
        warnings.append(f"Métadonnées KDP incomplètes : {', '.join(missing)}. Impossible de créer la fiche produit.")
        score -= 5 * len(missing)

    keywords = meta.get("kdp_keywords", [])
    if len(keywords) < 7:
        warnings.append(f"Seulement {len(keywords)} mots-clés KDP. KDP autorise 7 — tous doivent être utilisés pour la visibilité.")
        score -= 8

    human_checks = [
        "Ouvrir le PDF et vérifier que les lignes/cases sont visibles et correctement espacées",
        "Vérifier que le texte (titres de section, en-têtes) est lisible à l'impression",
        "Comparer avec un concurrent bestseller : est-ce visuellement à la hauteur ?",
        "Vérifier les marges : aucun élément dans les 0.375\" (bleed) + 0.25\" (safe zone) KDP",
        "L'élément différenciant est-il réel et visible dès les premières pages ?",
    ]

    return {
        "score": max(0, score),
        "pdf_file": pdf.name,
        "file_size_kb": round(file_size_kb, 1),
        "pages": pages,
        "title": title,
        "issues": issues,
        "warnings": warnings,
        "human_checks": human_checks,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT STL 3D
# Critères consommateurs Cults3D/Printables :
#   - "Fichier non-manifold, impossible à trancher" → validité mesh basique
#   - "Trop grand pour ma imprimante" → dimensions
#   - "Juste 1 fichier pour 2€, arnaque" → quantité variants
#   - "Description vague, je sais pas quoi configurer" → metadata complète
#   - "Temps d'impression faux" → estimation cohérente
# ═══════════════════════════════════════════════════════════════════════════════

def parse_stl_basic(stl_path: Path) -> dict:
    """Lecture basique d'un STL binaire pour vérifier l'intégrité et les dimensions."""
    try:
        data = stl_path.read_bytes()
        if len(data) < 84:
            return {"valid": False, "error": "fichier trop petit"}

        # STL binaire : header 80 bytes + uint32 nb_triangles + triangles
        nb_triangles = struct.unpack_from("<I", data, 80)[0]
        expected_size = 84 + nb_triangles * 50

        if abs(len(data) - expected_size) > 10:
            # Peut-être STL ASCII
            if data[:5] == b"solid":
                nb_triangles = data.count(b"facet normal")
                return {"valid": True, "nb_triangles": nb_triangles, "format": "ascii"}
            return {"valid": False, "error": f"taille inattendue ({len(data)} vs {expected_size} attendu)"}

        if nb_triangles == 0:
            return {"valid": False, "error": "0 triangles — fichier vide"}

        # Extraire les coordonnées pour les dimensions
        xs, ys, zs = [], [], []
        offset = 84
        for _ in range(min(nb_triangles, 10000)):  # sample des 10000 premiers
            if offset + 50 > len(data):
                break
            offset += 12  # skip normal
            for _ in range(3):  # 3 sommets
                x, y, z = struct.unpack_from("<fff", data, offset)
                xs.append(x); ys.append(y); zs.append(z)
                offset += 12
            offset += 2  # attribute

        if xs:
            dims = {
                "x_mm": round(max(xs) - min(xs), 1),
                "y_mm": round(max(ys) - min(ys), 1),
                "z_mm": round(max(zs) - min(zs), 1),
            }
        else:
            dims = {}

        return {"valid": True, "nb_triangles": nb_triangles, "format": "binary", **dims}

    except Exception as e:
        return {"valid": False, "error": str(e)}


def audit_stl(product_dir: Path) -> dict:
    issues = []
    warnings = []
    score = 100

    stl_files = list(product_dir.rglob("*.stl"))
    json_files = list(product_dir.rglob("*.json"))

    # 1. QUANTITÉ DE FICHIERS — un seul STL = pas de valeur
    if not stl_files:
        issues.append("Aucun fichier STL trouvé. Le produit est vide.")
        return {"score": 0, "issues": issues, "warnings": warnings}

    if len(stl_files) < 3:
        warnings.append(
            f"Seulement {len(stl_files)} fichier(s) STL. Les listings Cults3D qui vendent bien "
            f"proposent ≥5 variants pour justifier le prix (différentes tailles, textes, versions)."
        )
        score -= 15

    # 2. VALIDITÉ DES FICHIERS STL
    invalid = []
    oversized = []  # > 250mm sur un côté = ne rentre pas dans la plupart des imprimantes
    undersized = []  # < 1mm = probablement un bug d'échelle

    for stl_path in stl_files[:20]:  # limite à 20 pour la performance
        size_kb = stl_path.stat().st_size / 1024
        if size_kb < 1:
            invalid.append(f"{stl_path.name} ({size_kb:.1f} KB — fichier vide)")
            continue

        info = parse_stl_basic(stl_path)
        if not info["valid"]:
            invalid.append(f"{stl_path.name} : {info.get('error', 'invalide')}")
        else:
            # Vérifier les dimensions
            x, y, z = info.get("x_mm", 0), info.get("y_mm", 0), info.get("z_mm", 0)
            max_dim = max(x, y, z)
            min_dim = min(d for d in [x, y, z] if d > 0) if any([x, y, z]) else 0

            if max_dim > 250:
                oversized.append(f"{stl_path.name} ({max_dim:.0f}mm > 250mm)")
            if 0 < min_dim < 1:
                undersized.append(f"{stl_path.name} (dimension {min_dim:.2f}mm — probablement mauvaise unité mm/m)")

    if invalid:
        issues.append(
            f"{len(invalid)} fichier(s) STL invalide(s) ou vide(s) : {', '.join(invalid[:4])}. "
            f"Les makers signalent les fichiers corrompus = 1★ 'impossible à imprimer'."
        )
        score -= 15 * len(invalid)

    if oversized:
        warnings.append(
            f"{len(oversized)} pièce(s) > 250mm : {', '.join(oversized[:3])}. "
            f"Ne rentrent pas dans la plupart des imprimantes. Proposer une version découpée."
        )
        score -= 10

    if undersized:
        issues.append(
            f"{len(undersized)} pièce(s) avec dimensions < 1mm : {', '.join(undersized[:3])}. "
            f"Probablement exporté en mètres au lieu de mm — crash immédiat dans le slicer."
        )
        score -= 20

    # 3. MÉTADONNÉES — titre, tags, description
    if not json_files:
        warnings.append("Aucune métadonnée JSON trouvée. Les titres/tags Cults3D doivent être préparés pour le listing.")
        score -= 10
    else:
        # Vérifier le premier JSON pour les champs obligatoires
        try:
            meta = json.loads(json_files[0].read_text())
            for field in ["title", "tags_cults3d", "price_cults3d_eur"]:
                if not meta.get(field):
                    warnings.append(f"Métadonnée manquante : '{field}' dans {json_files[0].name}")
                    score -= 5
            tags = meta.get("tags_cults3d", [])
            if len(tags) < 5:
                warnings.append(f"Seulement {len(tags)} tags Cults3D (5-10 recommandé pour la visibilité).")
                score -= 5
        except Exception:
            warnings.append(f"JSON illisible : {json_files[0].name}")
            score -= 5

    # 4. FICHIER CSV D'UPLOAD
    csv_files = list(product_dir.rglob("*.csv"))
    if not csv_files:
        warnings.append("Pas de fichier CSV d'upload préparé — le listing Cults3D devra être fait manuellement page par page.")

    human_checks = [
        "Importer UN fichier dans PrusaSlicer ou Cura et vérifier qu'il slice sans erreur",
        "Vérifier l'échelle : les dimensions affichées correspondent-elles à ce qui est annoncé ?",
        "Vérifier qu'aucun support excessif n'est nécessaire pour les pièces horizontales",
        "Les previews de rendu sont-elles attrayantes ? (Cults3D = premier critère visuel)",
        "Le prix est-il cohérent avec la valeur (nb de variants, complexité) ?",
    ]

    return {
        "score": max(0, score),
        "nb_stl": len(stl_files),
        "nb_invalid": len(invalid),
        "nb_oversized": len(oversized),
        "issues": issues,
        "warnings": warnings,
        "human_checks": human_checks,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT JEU DE CARTES
# Critères consommateurs Etsy / TGC :
#   - "Texte illisible sur les cartes" → résolution + taille police
#   - "Règles manquantes" → fichier règles présent
#   - "Pas assez de cartes pour jouer" → quantité
#   - "Images pixelisées imprimées" → résolution
#   - "Pas de zone de découpe indiquée" → bleed présent
# ═══════════════════════════════════════════════════════════════════════════════

def audit_card_game(product_dir: Path) -> dict:
    issues = []
    warnings = []
    score = 100
    meta = load_meta(product_dir)

    total_cards = meta.get("total_cards", 0)
    questions   = meta.get("questions", 0)
    answers     = meta.get("answers", 0)
    card_format = meta.get("card_format", "")

    # 1. NOMBRE DE CARTES
    if total_cards == 0:
        # Essayer de compter les images
        card_images = find_images(product_dir)
        total_cards = len(card_images)

    if total_cards < 30:
        issues.append(
            f"Seulement {total_cards} cartes. Un jeu de cartes viable sur Etsy/TGC nécessite "
            f"≥50 cartes pour justifier le prix. En dessous, les acheteurs disent 'trop peu de contenu'."
        )
        score -= 30
    elif total_cards < 50:
        warnings.append(f"{total_cards} cartes — acceptable, mais 54+ (deck standard) ou 100+ (party game) serait plus attractif.")
        score -= 10

    # 2. FORMAT ET BLEED
    if card_format:
        # Format standard Poker = 2.5×3.5" ou 825×1125px @300DPI avec 0.125" bleed
        if "825" not in card_format and "2.75" not in card_format and "poker" not in card_format.lower():
            warnings.append(
                f"Format '{card_format}' — vérifier que c'est compatible avec TGC/BoardGamesMaker "
                f"(Poker standard = 825×1125 avec bleed = 2.75×3.75\")."
            )
            score -= 5

    # 3. FICHIERS IMAGES — qualité des cartes
    if HAS_PIL:
        card_dirs = [d for d in product_dir.iterdir() if d.is_dir() and d.name not in ("__pycache__",)]
        sample_images = []
        for d in card_dirs[:3]:
            sample_images += list(d.glob("*.png"))[:3]
        if not sample_images:
            sample_images = list(product_dir.glob("*.png"))[:5]

        low_res_cards = []
        for img_path in sample_images[:10]:
            try:
                img = Image.open(img_path)
                w, h = img.size
                # Poker card @300DPI = 825×1125px au minimum
                if min(w, h) < 800:
                    low_res_cards.append(f"{img_path.name} ({w}×{h})")
            except Exception:
                pass

        if low_res_cards:
            issues.append(
                f"Cartes sous-résolues : {', '.join(low_res_cards[:4])}. "
                f"Un deck imprimé à 300 DPI (standard) nécessite ≥825×1125px par carte. "
                f"En dessous, le texte est illisible sur les cartes imprimées."
            )
            score -= 25

    # 4. RÈGLES DU JEU
    rules = list(product_dir.rglob("RULES*")) + list(product_dir.rglob("rules*")) + list(product_dir.rglob("*.md"))
    if not rules:
        issues.append(
            "Pas de fichier de règles trouvé. Un jeu de cartes DOIT inclure les règles — "
            "sans ça les acheteurs ne peuvent pas jouer, garantissant des avis négatifs."
        )
        score -= 20

    # 5. FICHIER CSV D'UPLOAD
    csv = list(product_dir.glob("*.csv"))
    if not csv:
        warnings.append("Pas de fichier CSV de listing préparé.")
        score -= 5

    human_checks = [
        "Imprimer 5-10 cartes test et vérifier la lisibilité du texte à taille réelle",
        "Vérifier que le bleed (zone de découpe) est bien présent et que les éléments importants ne sont pas dans la zone de découpe",
        "Les règles sont-elles claires pour quelqu'un qui découvre le jeu ?",
        "La cohérence graphique est-elle maintenue sur toutes les cartes ?",
        "Le thème de la couverture/back des cartes est-il cohérent ?",
    ]

    return {
        "score": max(0, score),
        "total_cards": total_cards,
        "issues": issues,
        "warnings": warnings,
        "human_checks": human_checks,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT ROMAN / NOVEL
# Critères consommateurs KDP :
#   - "Clairement généré par IA" → phrases types IA
#   - "Les personnages changent de caractère" → cohérence
#   - "Trop court pour le prix" → nombre de mots
#   - "Se répète" → taux de répétition
#   - "Aucun trope du genre n'est exploité" → structure narrative
# ═══════════════════════════════════════════════════════════════════════════════

AI_TELLS = [
    "nodded slowly", "couldn't help but", "felt a wave of", "eyes widened",
    "heart raced", "took a deep breath", "jaw dropped", "stomach dropped",
    "butterflies in", "breath caught", "tears pricked", "blinked back tears",
    "a smile tugged", "lips quirked", "pulse quickened", "throat tightened",
    "it was in this moment", "little did he know", "little did she know",
    "as if on cue", "at that exact moment", "he chuckled", "she chuckled",
    "he nodded", "she nodded", "he sighed", "she sighed",
    "tapestry of", "testament to", "a beacon of", "in the realm of",
    "delve into", "embark on", "navigate the", "bustling", "vibrant",
    "foster", "crucial", "straightforward", "commendable",
]


def audit_novel(product_dir: Path) -> dict:
    issues = []
    warnings = []
    score = 100
    meta = load_meta(product_dir)

    # Chercher le texte du roman
    text_files = list(product_dir.rglob("*.txt")) + list(product_dir.rglob("*.md"))
    text_files = [f for f in text_files if "CAHIER" not in f.name.upper() and f.stat().st_size > 1000]

    if not text_files:
        # Pas encore écrit — c'est un CdC ou une ébauche
        cdc_files = list(product_dir.rglob("cdc.json"))
        if cdc_files:
            try:
                cdc = json.loads(cdc_files[0].read_text())
                gate = cdc.get("gate_cdc", "unknown")
                if gate == "pending":
                    return {
                        "score": None,
                        "status": "pending_validation",
                        "message": f"CdC en attente de validation Hugo (gate_cdc=pending). Aucun texte produit.",
                        "issues": [], "warnings": [], "human_checks": [],
                    }
                elif gate == "approved":
                    return {
                        "score": None,
                        "status": "approved_not_written",
                        "message": "CdC approuvé mais roman pas encore écrit.",
                        "issues": [], "warnings": [], "human_checks": [],
                    }
            except Exception:
                pass
        return {
            "score": None,
            "status": "no_content",
            "message": "Aucun texte trouvé. Roman pas encore produit.",
            "issues": [], "warnings": [], "human_checks": [],
        }

    # Lire le texte
    full_text = ""
    for f in text_files[:3]:
        try:
            full_text += f.read_text(encoding="utf-8", errors="ignore") + "\n"
        except Exception:
            pass

    words = full_text.split()
    word_count = len(words)

    # 1. LONGUEUR — critère #1 de valeur perçue
    genre = meta.get("genre", "").lower()
    if "novella" in genre or "short" in genre:
        min_words = 20000
    else:
        min_words = 50000  # roman standard KDP

    if word_count < min_words * 0.5:
        issues.append(
            f"Texte trop court : {word_count:,} mots (minimum attendu {min_words:,} pour un roman KDP). "
            f"Les acheteurs vérifient la longueur — 'ébauche' dans les avis garantit 1★."
        )
        score -= 40
    elif word_count < min_words:
        warnings.append(f"{word_count:,} mots — en dessous du standard genre ({min_words:,}). Envisager 5-10 chapitres supplémentaires.")
        score -= 15

    # 2. PHRASES IA — tellement reconnaissables que les lecteurs le signalent
    text_lower = full_text.lower()
    found_tells = [tell for tell in AI_TELLS if tell in text_lower]
    tell_count = sum(text_lower.count(tell) for tell in found_tells)

    if tell_count > 30:
        issues.append(
            f"ALERTE IA : {tell_count} occurrences de phrases typiquement IA détectées "
            f"({', '.join(found_tells[:8])}...). "
            f"Les lecteurs de romance/fiction identifient ces tics instantanément → 1★ 'AI slop'."
        )
        score -= 30
    elif tell_count > 10:
        warnings.append(f"{tell_count} phrases IA détectées ({', '.join(found_tells[:5])}). Réviser avant publication.")
        score -= 12
    elif tell_count > 3:
        warnings.append(f"{tell_count} phrases-tics IA mineures ({', '.join(found_tells[:3])}). Acceptable.")
        score -= 5

    # 3. RÉPÉTITION — compter les bigrammes sur-utilisés
    if words:
        bigrams = [f"{words[i].lower()} {words[i+1].lower()}" for i in range(len(words)-1)]
        bigram_counts = Counter(bigrams)
        most_common_5 = bigram_counts.most_common(5)
        max_repeat = most_common_5[0][1] if most_common_5 else 0
        if word_count > 0:
            repeat_rate = max_repeat / max(word_count / 1000, 1)  # occurrences par 1000 mots
            if repeat_rate > 10:
                issues.append(
                    f"Répétition excessive : '{most_common_5[0][0]}' apparaît {max_repeat} fois. "
                    f"Taux de {repeat_rate:.0f}/1000 mots. Les lecteurs le remarquent et le signalent."
                )
                score -= 15
            elif repeat_rate > 5:
                warnings.append(f"Répétitions notables : {[f'{b} ({c}×)' for b, c in most_common_5[:3]]}.")
                score -= 7

    human_checks = [
        "Lire le premier chapitre entier — le hook est-il accrocheur ?",
        "Vérifier la cohérence des personnages sur 3-4 chapitres non consécutifs",
        "La voix narrative (1ère/3ème personne) est-elle maintenue tout au long ?",
        "Les tropes du genre (ex: grumpy-sunshine, second chance) sont-ils bien exécutés ?",
        "La progression de la relation/tension est-elle crédible ?",
        "Passer le texte dans ProWritingAid ou Grammarly pour détecter les erreurs restantes",
    ]

    return {
        "score": max(0, score),
        "word_count": word_count,
        "ai_tell_count": tell_count,
        "ai_tells_found": found_tells[:10],
        "issues": issues,
        "warnings": warnings,
        "human_checks": human_checks,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT GÉNÉRIQUE (iHeart, viral formats, bible_verses, cultural_arbitrage...)
# Critères : résolution, texte lisible, fichier présent
# ═══════════════════════════════════════════════════════════════════════════════

def audit_generic(product_dir: Path) -> dict:
    issues = []
    warnings = []
    score = 100
    meta = load_meta(product_dir)

    if not meta:
        return {"status": "skip", "reason": "no metadata.json"}

    # Trouver l'image principale
    preview = product_dir / "etsy_preview.jpg"
    if not preview.exists():
        preview = next(product_dir.glob("*.jpg"), None) or next(product_dir.glob("*.png"), None)
    if not preview:
        return {"status": "skip", "reason": "no image"}

    if not HAS_PIL:
        return {"score": 60, "issues": ["Pillow manquant"], "warnings": [], "human_checks": []}

    try:
        img = Image.open(preview).convert("RGB")
    except Exception as e:
        return {"score": 0, "issues": [f"Image illisible: {e}"], "warnings": [], "human_checks": []}

    stat = ImageStat.Stat(img)
    var = sum(stat.var) / 3
    lum = sum(stat.mean) / 3
    w, h = img.size

    if var < 100:
        issues.append("Image trop uniforme — composition vide ou répétitive.")
        score -= 30
    if lum < 30:
        issues.append("Image trop sombre.")
        score -= 30
    if lum > 245:
        issues.append("Image presque blanche — probablement vide.")
        score -= 30
    if min(w, h) < 800:
        issues.append(f"Résolution insuffisante ({w}×{h}px) — minimum 800px pour impression.")
        score -= 20

    # Texte lisible ?
    uses_overlay = meta.get("text_overlay_method") == "pillow"
    text_pipelines = {"viral_formats", "iheart", "iheart_v2", "cultural_arbitrage", "literal_idioms", "bible_verses"}
    pipeline = product_dir.parent.parent.name

    if uses_overlay:
        txt_score = 100
        txt_note = "Pillow overlay — texte garanti correct"
    elif pipeline in text_pipelines:
        ocr = ocr_text(preview)
        txt_score = text_score(ocr)
        txt_note = f"OCR: '{ocr[:80]}'" if ocr else "(pas d'OCR dispo)"
        if txt_score < 40:
            issues.append(f"Texte potentiellement gibberish (score={txt_score:.0f}) — {txt_note}")
            score -= 25
        elif txt_score < 65:
            warnings.append(f"Texte douteux ({txt_score:.0f}/100) — vérification manuelle.")
            score -= 10
    else:
        txt_score = 80
        txt_note = "pas de texte attendu"

    composite = score * 0.5 + txt_score * 0.5

    human_checks = [
        "Le visuel est-il attractif face à la concurrence sur Etsy/Redbubble ?",
        "Le texte est-il lisible en miniature (comme il apparaît dans les résultats de recherche) ?",
    ]

    return {
        "score": max(0, round(composite, 1)),
        "visual_score": score,
        "text_score": round(txt_score, 1),
        "resolution": f"{w}×{h}",
        "issues": issues,
        "warnings": warnings,
        "human_checks": human_checks,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DISPATCHER — Détecte le type et route vers le bon auditeur
# ═══════════════════════════════════════════════════════════════════════════════

def detect_type(product_dir: Path) -> str:
    parts = product_dir.relative_to(PRODUCTS_DIR).parts
    pipeline = parts[0] if parts else ""

    if pipeline == "coloring_books":
        return "coloring"
    if pipeline in ("lowcontent_kdp",):
        return "lowcontent"
    if pipeline == "stl_parametric":
        return "stl"
    if pipeline == "card_game":
        return "card_game"
    if pipeline == "novels":
        return "novel"
    return "generic"


def audit_product(product_dir: Path) -> dict:
    kind = detect_type(product_dir)
    dispatchers = {
        "coloring":  audit_coloring,
        "lowcontent": audit_lowcontent,
        "stl":       audit_stl,
        "card_game": audit_card_game,
        "novel":     audit_novel,
        "generic":   audit_generic,
    }
    result = dispatchers[kind](product_dir)
    result["product_type"] = kind
    result["design_path"] = str(product_dir.relative_to(PRODUCTS_DIR))

    score = result.get("score")
    has_blocking_issues = bool(result.get("issues"))

    if score is None:
        result["status"] = result.get("status", "pending")
    elif score < 45:
        result["status"] = "reject"
    elif score >= MIN_APPROVE and not has_blocking_issues:
        # APPROVE uniquement si aucun problème bloquant — sinon REVIEW
        result["status"] = "approve"
    else:
        result["status"] = "review"

    result["composite_score"] = score
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# ÉCRITURE DU RAPPORT
# ═══════════════════════════════════════════════════════════════════════════════

def write_audit_file(product_dir: Path, audit: dict) -> None:
    status = audit.get("status", "?").upper()
    score = audit.get("composite_score")
    kind = audit.get("product_type", "?")

    lines = [
        f"AUDIT v3 — {ts()}",
        f"Type produit : {kind.upper()}",
        "=" * 60,
        "",
        f"VERDICT : {status}",
        f"Score    : {score}/100" if score is not None else f"Statut   : {audit.get('message', '')}",
        "",
    ]

    issues = audit.get("issues", [])
    warnings = audit.get("warnings", [])
    human = audit.get("human_checks", [])

    if issues:
        lines.append("── PROBLÈMES BLOQUANTS (causes de 1★ Amazon/Etsy/Cults3D) ──")
        for iss in issues:
            lines.append(f"  ✗ {iss}")
        lines.append("")

    if warnings:
        lines.append("── AVERTISSEMENTS (à corriger avant upload idéalement) ──")
        for w in warnings:
            lines.append(f"  ⚠ {w}")
        lines.append("")

    if human:
        lines.append("── VÉRIFICATIONS MANUELLES OBLIGATOIRES (l'audit ne peut pas voir ça) ──")
        for h in human:
            lines.append(f"  → {h}")
        lines.append("")

    # Stats spécifiques par type
    if kind == "coloring":
        lines += [
            "── STATS PAGES ──",
            f"  Pages analysées : {audit.get('nb_pages', '?')}",
            f"  Densité trait   : moy={audit.get('fill_mean', '?')}%, std={audit.get('fill_std', '?')}%",
            f"  Gris moyen      : {audit.get('gray_mean', '?')}%",
            f"  Pages low-res   : {audit.get('low_res_count', 0)}",
            f"  Pages grises    : {audit.get('gray_pages_count', 0)}",
            "",
        ]
    elif kind == "lowcontent":
        lines += [
            "── STATS PRODUIT ──",
            f"  PDF : {audit.get('pdf_file', '?')} ({audit.get('file_size_kb', '?')} KB)",
            f"  Pages : {audit.get('pages', '?')}",
            f"  Titre : {audit.get('title', '?')}",
            "",
        ]
    elif kind == "stl":
        lines += [
            "── STATS STL ──",
            f"  Fichiers STL : {audit.get('nb_stl', '?')}",
            f"  Invalides    : {audit.get('nb_invalid', 0)}",
            f"  > 250mm      : {audit.get('nb_oversized', 0)}",
            "",
        ]
    elif kind == "card_game":
        lines += [f"  Cartes : {audit.get('total_cards', '?')}", ""]
    elif kind == "novel":
        lines += [
            f"  Mots      : {audit.get('word_count', '?'):,}" if audit.get("word_count") else "  Mots : N/A",
            f"  Phrases IA: {audit.get('ai_tell_count', '?')}",
            "",
        ]

    # Verdict final
    if status == "REJECT":
        lines.append("→ REJETÉ — Ne pas uploader. Corriger les problèmes critiques d'abord.")
        lines.append("  Ces défauts sont visibles par les acheteurs et entraîneront des 1★.")
    elif status == "REVIEW":
        lines.append("→ REVUE MANUELLE obligatoire avant toute décision d'upload.")
    elif status == "APPROVE":
        lines.append("→ Approuvé — viable commercialement sous réserve des vérifications manuelles ci-dessus.")
    elif status in ("PENDING_VALIDATION", "APPROVED_NOT_WRITTEN", "NO_CONTENT", "PENDING"):
        lines.append(f"→ {audit.get('message', 'En attente.')}")

    (product_dir / "AUDIT.txt").write_text("\n".join(lines), encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def discover_products(target_pipeline: str = "") -> list[Path]:
    """Trouve tous les dossiers produits à auditer."""
    products = []

    if not PRODUCTS_DIR.exists():
        return products

    for pipeline_dir in sorted(PRODUCTS_DIR.iterdir()):
        if not pipeline_dir.is_dir() or pipeline_dir.name.startswith("_"):
            continue
        if target_pipeline and pipeline_dir.name != target_pipeline:
            continue

        pipeline = pipeline_dir.name

        # Coloring books : un sous-dossier par livre
        if pipeline == "coloring_books":
            for book_dir in sorted(pipeline_dir.iterdir()):
                if book_dir.is_dir() and not book_dir.name.startswith("_"):
                    pages = find_images_pages(book_dir)
                    if pages:
                        products.append(book_dir)
            continue

        # STL : un sous-dossier par type de produit
        if pipeline == "stl_parametric":
            for type_dir in sorted(pipeline_dir.iterdir()):
                if type_dir.is_dir():
                    if list(type_dir.rglob("*.stl")):
                        products.append(type_dir)
            continue

        # Low-content / novels : un sous-dossier par produit
        if pipeline in ("lowcontent_kdp", "novels"):
            for prod_dir in sorted(pipeline_dir.iterdir()):
                if prod_dir.is_dir():
                    products.append(prod_dir)
            continue

        # Card game : un sous-dossier par deck
        if pipeline == "card_game":
            for deck_dir in sorted(pipeline_dir.iterdir()):
                if deck_dir.is_dir() and (deck_dir / "metadata.json").exists():
                    products.append(deck_dir)
            continue

        # Génériques : via metadata.json
        for meta_path in pipeline_dir.rglob("metadata.json"):
            products.append(meta_path.parent)

    return products


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    target_pipeline = os.environ.get("PIPELINE", "")
    auto_reject = os.environ.get("AUTO_REJECT") == "1"

    print("=" * 72)
    print("VISUAL AUDIT v3 — Critères consommateurs par type de produit")
    print("=" * 72)
    print(f"Pillow        : {'OK' if HAS_PIL else 'NON (installer Pillow)'}")
    print(f"Tesseract OCR : {'OK' if HAS_TESSERACT else 'NON (mode dégradé)'}")
    print(f"Auto-reject   : {auto_reject}")
    print(f"Seuil approve : {MIN_APPROVE}/100")
    if target_pipeline:
        print(f"Pipeline cible : {target_pipeline}")
    print()

    products = discover_products(target_pipeline)
    all_audits = []
    counters: Counter = Counter()
    by_type: dict[str, Counter] = {}

    for prod_dir in products:
        audit = audit_product(prod_dir)
        if audit.get("status") == "skip":
            continue

        all_audits.append(audit)
        status = audit["status"]
        counters[status] += 1

        kind = audit.get("product_type", "?")
        if kind not in by_type:
            by_type[kind] = Counter()
        by_type[kind][status] += 1

        write_audit_file(prod_dir, audit)

        score_str = f"{audit['composite_score']}/100" if audit["composite_score"] is not None else "N/A"
        icon = {"approve": "✓", "review": "⚠", "reject": "✗", "pending": "○",
                "pending_validation": "○", "approved_not_written": "○", "no_content": "○"}.get(status, "?")
        print(f"  {icon} [{kind:<11}] {str(prod_dir.relative_to(PRODUCTS_DIR)):<45} {score_str}")

        for iss in audit.get("issues", [])[:2]:
            print(f"       ↳ {iss[:100]}")

        if auto_reject and status == "reject":
            pipeline = audit["design_path"].split("/")[0]
            dest = REJECTED_DIR / audit["design_path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists():
                shutil.move(str(prod_dir), str(dest))
                print(f"       → Déplacé vers {dest}")

    # Rapport global
    report = {
        "audit_timestamp": ts(),
        "version": "v3",
        "total_audited": len(all_audits),
        "totals_by_status": dict(counters),
        "by_type": {t: dict(c) for t, c in by_type.items()},
        "audits": all_audits,
    }
    out = DATA_DIR / "visual_audit.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(f"\n{'=' * 72}")
    print(f"BILAN : {len(all_audits)} produits audités")
    print(f"  ✓ Approve  : {counters.get('approve', 0)}")
    print(f"  ⚠ Review   : {counters.get('review', 0)}")
    print(f"  ✗ Reject   : {counters.get('reject', 0)}")
    print(f"  ○ Pending  : {counters.get('pending', 0) + counters.get('pending_validation', 0)}")
    print(f"\nPar type de produit :")
    for t, c in sorted(by_type.items()):
        total = sum(c.values())
        pct = 100 * c.get("approve", 0) / max(total, 1)
        print(f"  {t:<15} {total:>4} produits  —  {pct:.0f}% approve")
    print(f"\n→ Rapport : {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
