"""
Agent VISUAL AUDIT v2 — Auditeur strict qui rejette le contenu invendable.

Contrôles génériques (tous pipelines) :
  - Résolution insuffisante
  - Image trop sombre / trop blanche
  - Texte gibberish (OCR)

Contrôles spécifiques COLORING BOOK :
  - Contamination grise : les pages doivent être noir PUR sur blanc PUR.
    Trop de demi-tons (hachures, ombres AI) → page impossible à colorier.
  - Cohérence de style entre pages : si la densité de trait varie trop d'une
    page à l'autre, c'est un mélange de styles → invendable.
  - Pages vides / sur-remplies : en dehors de la plage 5-40% de pixels sombres.
  - Zones blanches vides en haut/bas (sujet mal cadré).
  - Nombre minimum de pages.

Verdict : APPROVE / REVIEW / REJECT
  REJECT = ne pas uploader, régénérer.
  REVIEW = audit humain requis.
  APPROVE = score > seuil, produit commercialement viable.

Variables d'env :
  AUTO_REJECT=1   déplace les rejected vers products/_rejected/
  MIN_SCORE=65    seuil approve (défaut 65)
"""

import json
import os
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean, stdev

try:
    from PIL import Image, ImageStat
except ImportError:
    print("ERREUR : Pillow non installé — pip install Pillow")
    sys.exit(2)

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

COMMON_ENGLISH = {
    "a", "the", "is", "of", "and", "to", "in", "i", "it", "you", "that",
    "he", "was", "for", "on", "are", "with", "as", "his", "they", "at",
    "be", "this", "have", "from", "or", "one", "had", "by", "but", "not",
    "what", "all", "were", "we", "when", "your", "can", "said", "love",
    "my", "me", "her", "him", "she", "an", "if", "do", "will", "no",
    "so", "out", "go", "up", "down", "got", "now", "back", "good", "best",
    "more", "less", "new", "old", "any", "way",
    "reading", "cat", "dog", "coffee", "tea", "wine", "yoga", "fishing",
    "hiking", "camping", "knitting", "crochet", "gardening", "horse",
    "chicken", "dnd", "chess", "baking", "music", "therapy", "certified",
    "professional", "official", "warning", "mom", "dad", "girl", "boy",
    "life", "joy", "hope", "faith", "peace", "strength", "wisdom", "grace",
}

# ─────────────────────────────────────────────────────────────────────────────
# Pixel-level analysis helpers
# ─────────────────────────────────────────────────────────────────────────────

def pixel_stats(img_gray) -> dict:
    """
    Analyse les pixels d'une image en niveaux de gris.
    Retourne des métriques sur la distribution noir/gris/blanc.
    """
    width, height = img_gray.size
    total = width * height

    pixels = list(img_gray.getdata())

    dark = sum(1 for p in pixels if p <= 40)          # lignes noires
    midtone = sum(1 for p in pixels if 41 <= p <= 214)  # gris (problème)
    light = sum(1 for p in pixels if p >= 215)         # blanc (fond)

    fill_pct = dark / total * 100
    gray_pct = midtone / total * 100
    purity_pct = (dark + light) / total * 100

    return {
        "fill_pct": round(fill_pct, 2),     # % pixels sombres (lignes)
        "gray_pct": round(gray_pct, 2),     # % pixels gris (contamination)
        "purity_pct": round(purity_pct, 2), # % pixels purs (noir ou blanc)
        "total_pixels": total,
        "width": width,
        "height": height,
    }


def check_composition(img_gray) -> dict:
    """
    Vérifie que le sujet remplit bien la page (pas de zones vides en haut/bas).
    Découpe l'image en 5 bandes horizontales, vérifie qu'aucune n'est quasi-vide.
    """
    width, height = img_gray.size
    band_h = height // 5
    issues = []
    band_fills = []

    for i in range(5):
        y0 = i * band_h
        y1 = y0 + band_h
        band = img_gray.crop((0, y0, width, y1))
        pixels = list(band.getdata())
        dark = sum(1 for p in pixels if p <= 40)
        fill = dark / len(pixels) * 100
        band_fills.append(fill)

        if fill < 0.5 and i in (0, 4):
            issues.append(f"bande {'haut' if i == 0 else 'bas'} quasi-vide ({fill:.1f}% lignes) → sujet mal cadré")
        elif fill < 0.3 and i in (1, 3):
            issues.append(f"bande {'haut-centre' if i == 1 else 'bas-centre'} quasi-vide → trop d'espace blanc")

    return {"band_fills": [round(b, 1) for b in band_fills], "issues": issues}


# ─────────────────────────────────────────────────────────────────────────────
# Coloring book specific audit
# ─────────────────────────────────────────────────────────────────────────────

# Seuils commerciaux — calibrés sur les bestsellers Amazon KDP coloring books
COLORING_THRESHOLDS = {
    "gray_pct_max": 15.0,      # > 15% gris = pages pas assez "propres" pour colorier
    "fill_pct_min": 5.0,       # < 5% = trop vide (pas assez de détail)
    "fill_pct_max": 50.0,      # > 50% = trop rempli (zones trop petites à colorier)
    "purity_pct_min": 78.0,    # < 78% de pixels purs → trop de demi-tons
    "style_std_max": 12.0,     # écart-type fill% entre pages > 12 → styles mélangés
    "min_pages": 20,            # un livre de coloriage KDP doit avoir ≥ 20 pages
    "min_resolution": 1400,     # px minimum (côté court) pour impression KDP
}


def audit_coloring_book(product_dir: Path) -> dict:
    """Audit spécifique livres de coloriage — lit TOUTES les pages."""
    pages_dir = product_dir / "pages"
    if not pages_dir.exists():
        # Chercher les images directement
        images = list(product_dir.glob("page_*.png")) + list(product_dir.glob("page_*.jpg"))
    else:
        images = sorted(pages_dir.glob("*.png")) + sorted(pages_dir.glob("*.jpg"))

    if not images:
        return {"score": 0, "issues": ["Aucune page trouvée"], "verdict_detail": "REJECT — pas d'images"}

    issues = []
    warnings = []
    page_stats = []
    score = 100
    thresholds = COLORING_THRESHOLDS

    # Check nombre de pages
    if len(images) < thresholds["min_pages"]:
        issues.append(f"Seulement {len(images)} pages — KDP exige ≥ {thresholds['min_pages']} pour un livre de coloriage viable")
        score -= 25

    # Analyser chaque page
    per_page_fills = []
    per_page_grays = []
    low_res_pages = []
    gray_contaminated = []
    empty_pages = []
    overfilled_pages = []
    composition_issues = []

    for img_path in images:
        try:
            img = Image.open(img_path).convert("L")  # niveaux de gris
        except Exception as e:
            issues.append(f"{img_path.name} : illisible ({e})")
            continue

        # Résolution
        w, h = img.size
        if min(w, h) < thresholds["min_resolution"]:
            low_res_pages.append(f"{img_path.name} ({w}x{h})")

        stats = pixel_stats(img)
        per_page_fills.append(stats["fill_pct"])
        per_page_grays.append(stats["gray_pct"])

        # Gray contamination (demi-tons AI)
        if stats["gray_pct"] > thresholds["gray_pct_max"]:
            gray_contaminated.append(f"{img_path.name} ({stats['gray_pct']:.0f}% gris)")

        # Pages trop vides
        if stats["fill_pct"] < thresholds["fill_pct_min"]:
            empty_pages.append(f"{img_path.name} ({stats['fill_pct']:.0f}% lignes)")

        # Pages trop remplies
        if stats["fill_pct"] > thresholds["fill_pct_max"]:
            overfilled_pages.append(f"{img_path.name} ({stats['fill_pct']:.0f}% lignes)")

        # Composition (zones vides)
        comp = check_composition(img)
        if comp["issues"]:
            composition_issues.extend([f"{img_path.name}: {iss}" for iss in comp["issues"]])

        page_stats.append({
            "page": img_path.name,
            "fill_pct": stats["fill_pct"],
            "gray_pct": stats["gray_pct"],
            "purity_pct": stats["purity_pct"],
            "resolution": f"{w}x{h}",
        })

    # Style consistency (variance cross-page)
    style_inconsistency_note = ""
    if len(per_page_fills) >= 3:
        fill_std = stdev(per_page_fills)
        fill_mean = mean(per_page_fills)
        if fill_std > thresholds["style_std_max"]:
            issues.append(
                f"INCOHÉRENCE DE STYLE MAJEURE — les {len(images)} pages n'ont pas le même style "
                f"(densité trait : moy={fill_mean:.0f}%, écart-type={fill_std:.0f}%). "
                f"Un client Amazon verra des illustrations complètement différentes → 1 étoile."
            )
            score -= 30
            style_inconsistency_note = f"std={fill_std:.0f}% (seuil max={thresholds['style_std_max']}%)"
    else:
        fill_std = 0
        fill_mean = mean(per_page_fills) if per_page_fills else 0

    # Gray contamination
    if gray_contaminated:
        pct = len(gray_contaminated) / max(len(images), 1) * 100
        msg = (
            f"{len(gray_contaminated)}/{len(images)} pages avec contamination grise ({pct:.0f}%) : "
            f"{', '.join(gray_contaminated[:5])}. "
            f"Les demi-tons AI (hachures, ombres) rendent les pages impossibles à colorier proprement."
        )
        if pct > 50:
            issues.append("CRITIQUE — " + msg)
            score -= 25
        elif pct > 25:
            issues.append("MAJEUR — " + msg)
            score -= 15
        else:
            warnings.append(msg)
            score -= 5

    # Résolution — critique pour impression KDP (300 DPI pour 6x9" = 1800x2700px)
    if low_res_pages:
        pct_low = len(low_res_pages) / max(len(images), 1) * 100
        msg = (
            f"{len(low_res_pages)}/{len(images)} pages sous-résolues (<{thresholds['min_resolution']}px) : "
            f"{', '.join(low_res_pages[:4])}. "
            f"KDP exige ≥300 DPI — ces images (~112 DPI) seront floues à l'impression, "
            f"garantissant 1 étoile et un potentiel retrait de la vente."
        )
        issues.append(msg)
        if pct_low >= 80:
            score -= 50  # Quasi-totalité des pages inutilisables → REJECT direct
        else:
            score -= 20 * (pct_low / 100)

    # Pages vides
    if empty_pages:
        issues.append(f"{len(empty_pages)} pages quasi-vides (<{thresholds['fill_pct_min']}% lignes) : {', '.join(empty_pages[:3])}")
        score -= 10 * len(empty_pages)

    # Pages sur-remplies
    if overfilled_pages:
        warnings.append(f"{len(overfilled_pages)} pages très remplies — zones trop petites pour des crayons")
        score -= 5

    # Composition
    if composition_issues:
        for ci in composition_issues[:5]:
            warnings.append(f"Cadrage — {ci}")
        score -= min(20, len(composition_issues) * 4)

    score = max(0, score)

    # Verdict
    if score >= 80:
        verdict = "APPROVE"
    elif score >= 55:
        verdict = "REVIEW"
    else:
        verdict = "REJECT"

    # Build detail message
    details = []
    if issues:
        details.append("PROBLÈMES CRITIQUES :")
        for iss in issues:
            details.append(f"  ✗ {iss}")
    if warnings:
        details.append("AVERTISSEMENTS :")
        for w in warnings:
            details.append(f"  ⚠ {w}")
    if style_inconsistency_note:
        details.append(f"  Style : {style_inconsistency_note}")

    # Avertissement systématique sur ce que l'audit pixels NE PEUT PAS détecter
    details += [
        "",
        "── CE QUE L'AUDIT PIXEL NE DÉTECTE PAS (vérification manuelle requise) ──",
        "  • Cohérence de style visuel entre pages (ex: mix chibi / botanique / réaliste)",
        "  • Qualité artistique et attrait commercial des illustrations",
        "  • Thème respecté sur toutes les pages (ex: champignons présents partout ?)",
        "  • Lignes trop fines pour l'impression (imperceptibles à l'oeil nu sans zoom)",
        "  → Hugo doit vérifier visuellement 5-8 pages représentatives avant upload.",
    ]

    return {
        "score": score,
        "verdict": verdict,
        "nb_pages": len(images),
        "nb_pages_gray_contaminated": len(gray_contaminated),
        "nb_pages_empty": len(empty_pages),
        "nb_low_res": len(low_res_pages),
        "fill_mean_pct": round(fill_mean, 1) if per_page_fills else 0,
        "fill_std_pct": round(fill_std, 1) if per_page_fills else 0,
        "gray_mean_pct": round(mean(per_page_grays), 1) if per_page_grays else 0,
        "issues": issues,
        "warnings": warnings,
        "detail_text": "\n".join(details),
        "per_page_stats": page_stats,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Generic (non-coloring) audit
# ─────────────────────────────────────────────────────────────────────────────

def score_visual_generic(image_path: Path) -> dict:
    """Audit visuel générique pour les pipelines non-coloriage."""
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        return {"score": 0, "issues": [f"image illisible: {e}"]}

    stat = ImageStat.Stat(img)
    variance_avg = sum(stat.var) / 3
    mean_avg = sum(stat.mean) / 3

    issues = []
    score = 100
    if variance_avg < 100:
        score -= 30
        issues.append("composition très uniforme (peut être vide ou répétitive)")
    if mean_avg < 30:
        score -= 30
        issues.append("image trop sombre — probablement inutilisable")
    if mean_avg > 245:
        score -= 30
        issues.append("image presque blanche — probablement vide")
    if img.width < 800 or img.height < 800:
        score -= 20
        issues.append(f"résolution insuffisante ({img.width}x{img.height}px)")

    return {"score": max(0, score), "issues": issues,
            "variance": round(variance_avg, 1), "luminosity": round(mean_avg, 1)}


def score_text_quality(text: str) -> float:
    if not text or len(text.strip()) < 3:
        return 50
    words = [w.lower().strip(".,!?;:") for w in text.split() if w.strip()]
    if not words:
        return 50
    matches = sum(1 for w in words if w in COMMON_ENGLISH or len(w) <= 2)
    ratio = matches / len(words)
    if len(words) >= 5 and ratio < 0.3:
        return 10
    if ratio < 0.5:
        return 35
    if ratio < 0.7:
        return 70
    return 90


def extract_text_ocr(image_path: Path) -> str:
    if not HAS_TESSERACT:
        return ""
    try:
        r = subprocess.run(
            ["tesseract", str(image_path), "-", "--psm", "6", "-l", "eng"],
            capture_output=True, timeout=30,
        )
        return r.stdout.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline detection & routing
# ─────────────────────────────────────────────────────────────────────────────

COLORING_PIPELINES = {"coloring_books"}

TEXT_DEPENDENT_PIPELINES = {
    "viral_formats", "iheart", "iheart_v2", "cultural_arbitrage",
    "literal_idioms", "bible_verses",
}


def detect_pipeline(design_dir: Path) -> str:
    try:
        parts = design_dir.relative_to(PRODUCTS_DIR).parts
        return parts[0] if parts else ""
    except ValueError:
        return ""


def audit_product(design_dir: Path) -> dict:
    """Dispatch vers l'auditeur adapté au type de produit."""
    pipeline = detect_pipeline(design_dir)

    # --- COLORING BOOK ---
    if pipeline in COLORING_PIPELINES:
        result = audit_coloring_book(design_dir)
        verdict = result["verdict"]
        composite = result["score"]
        return {
            "status": verdict.lower(),
            "composite_score": composite,
            "pipeline": pipeline,
            "product_type": "coloring_book",
            "coloring_audit": result,
            "text_score": None,
            "text_extracted": None,
        }

    # --- GENERIC ---
    meta_path = design_dir / "metadata.json"
    if not meta_path.exists():
        return {"status": "skip", "reason": "no metadata.json"}

    try:
        metadata = json.loads(meta_path.read_text())
    except Exception:
        metadata = {}

    preview = design_dir / "etsy_preview.jpg"
    if not preview.exists():
        preview = next(design_dir.glob("*.jpg"), None) or next(design_dir.glob("*.png"), None)
    if not preview:
        return {"status": "skip", "reason": "no image"}

    visual = score_visual_generic(preview)

    uses_overlay = metadata.get("text_overlay_method") == "pillow"
    if uses_overlay:
        text_score = 100
        text_extracted = "(pillow overlay — texte garanti correct)"
    elif pipeline in TEXT_DEPENDENT_PIPELINES:
        text_extracted = extract_text_ocr(preview)
        if text_extracted and HAS_TESSERACT:
            text_score = score_text_quality(text_extracted)
        else:
            text_score = 30
            text_extracted = "(Flux text rendering unreliable, no overlay)"
    else:
        text_score = 80
        text_extracted = "(pas de texte attendu dans ce pipeline)"

    composite = visual["score"] * 0.4 + text_score * 0.6

    min_score = float(os.environ.get("MIN_SCORE", "65"))
    if composite >= min_score:
        verdict = "approve"
    elif composite >= 45:
        verdict = "review"
    else:
        verdict = "reject"

    return {
        "status": verdict,
        "composite_score": round(composite, 1),
        "visual_score": visual["score"],
        "text_score": text_score,
        "text_extracted": text_extracted[:200],
        "pipeline": pipeline,
        "product_type": "generic",
        "visual_details": visual,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Report writing
# ─────────────────────────────────────────────────────────────────────────────

def write_audit_file(design_dir: Path, audit: dict) -> None:
    status = audit["status"].upper()
    score = audit.get("composite_score", 0)
    ts = datetime.utcnow().isoformat() + "Z"

    lines = [
        f"AUDIT VISUEL v2 — {ts}",
        "=" * 60,
        "",
        f"VERDICT : {status}",
        f"Score : {score}/100",
        "",
    ]

    if audit.get("product_type") == "coloring_book":
        ca = audit.get("coloring_audit", {})
        lines += [
            "── COLORIAGE BOOK CHECKS ──",
            f"  Pages analysées       : {ca.get('nb_pages', '?')}",
            f"  Pages contamination   : {ca.get('nb_pages_gray_contaminated', 0)} ({ca.get('gray_mean_pct', '?')}% gris moyen)",
            f"  Pages vides           : {ca.get('nb_pages_empty', 0)}",
            f"  Pages sous-résolues   : {ca.get('nb_low_res', 0)}",
            f"  Densité trait         : moy={ca.get('fill_mean_pct', '?')}%, écart-type={ca.get('fill_std_pct', '?')}%",
            "",
        ]
        detail = ca.get("detail_text", "")
        if detail:
            lines.append(detail)
    else:
        lines += [
            f"  Visual score  : {audit.get('visual_score', '?')}/100",
            f"  Text score    : {audit.get('text_score', '?')}/100",
        ]
        vd = audit.get("visual_details", {})
        if vd.get("issues"):
            lines.append(f"  Issues visuels : {vd['issues']}")

    lines += [""]
    if status == "REJECT":
        lines.append("→ REJETÉ. Ne pas uploader. Régénérer le contenu.")
        lines.append("  Les clients Amazon verront ces défauts et laisseront 1 étoile.")
    elif status == "REVIEW":
        lines.append("→ REVUE MANUELLE OBLIGATOIRE avant upload.")
    else:
        lines.append("→ Approuvé — viable pour upload.")

    (design_dir / "AUDIT.txt").write_text("\n".join(lines), encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PRODUCTS_DIR.exists():
        print(f"✗ {PRODUCTS_DIR} inexistant")
        return 1

    auto_reject = os.environ.get("AUTO_REJECT") == "1"
    target_pipeline = os.environ.get("PIPELINE", "")

    print("=" * 70)
    print("VISUAL AUDIT v2 — Auditeur strict (coloring books + générique)")
    print("=" * 70)
    print(f"Tesseract OCR : {'OK' if HAS_TESSERACT else 'NON (mode dégradé)'}")
    print(f"Auto-reject   : {auto_reject}")
    if target_pipeline:
        print(f"Pipeline cible : {target_pipeline}")
    print()

    all_audits = []
    counters = Counter()

    # Audit coloring books directement (structure différente — pas de metadata.json)
    coloring_dir = PRODUCTS_DIR / "coloring_books"
    if coloring_dir.exists() and (not target_pipeline or target_pipeline == "coloring_books"):
        for book_dir in sorted(coloring_dir.iterdir()):
            if not book_dir.is_dir() or book_dir.name.startswith("_"):
                continue
            has_pages = (book_dir / "pages").exists() or list(book_dir.glob("page_*.png"))
            if not has_pages:
                continue

            audit = audit_product(book_dir)
            audit["design_path"] = str(book_dir.relative_to(PRODUCTS_DIR))
            all_audits.append(audit)
            counters[audit["status"]] += 1
            write_audit_file(book_dir, audit)

            icon = {"approve": "✓", "review": "⚠", "reject": "✗"}.get(audit["status"], "?")
            print(f"  {icon} {audit['status']:<8} {str(book_dir.relative_to(PRODUCTS_DIR)):<50} score {audit['composite_score']}")

            if audit.get("coloring_audit", {}).get("issues"):
                for iss in audit["coloring_audit"]["issues"][:3]:
                    print(f"      ↳ {iss[:100]}")

            if auto_reject and audit["status"] == "reject":
                dest = REJECTED_DIR / "coloring_books" / book_dir.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    shutil.move(str(book_dir), str(dest))
                    print(f"      → Déplacé vers {dest}")

    # Autres pipelines (génériques — via metadata.json)
    for pipeline_dir in sorted(PRODUCTS_DIR.iterdir()):
        if not pipeline_dir.is_dir():
            continue
        if pipeline_dir.name in ("_rejected", "coloring_books"):
            continue
        if target_pipeline and pipeline_dir.name != target_pipeline:
            continue

        for meta_path in pipeline_dir.rglob("metadata.json"):
            design_dir = meta_path.parent
            audit = audit_product(design_dir)
            if audit.get("status") == "skip":
                continue
            audit["pipeline"] = pipeline_dir.name
            audit["design_path"] = str(design_dir.relative_to(PRODUCTS_DIR))
            all_audits.append(audit)
            counters[audit["status"]] += 1
            write_audit_file(design_dir, audit)

            icon = {"approve": "✓", "review": "⚠", "reject": "✗"}.get(audit["status"], "?")
            print(f"  {icon} {audit['status']:<8} {str(design_dir.relative_to(PRODUCTS_DIR)):<50} score {audit['composite_score']}")

            if auto_reject and audit["status"] == "reject":
                dest = REJECTED_DIR / pipeline_dir.name / design_dir.relative_to(pipeline_dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    shutil.move(str(design_dir), str(dest))

    # Stats
    by_pipeline: dict[str, Counter] = {}
    for a in all_audits:
        p = a.get("pipeline", a.get("design_path", "?").split("/")[0])
        if p not in by_pipeline:
            by_pipeline[p] = Counter()
        by_pipeline[p][a["status"]] += 1

    report = {
        "audit_timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "v2",
        "tesseract_available": HAS_TESSERACT,
        "auto_reject": auto_reject,
        "total_audited": len(all_audits),
        "totals_by_status": dict(counters),
        "by_pipeline": {p: dict(c) for p, c in by_pipeline.items()},
        "audits": all_audits,
    }
    out_path = DATA_DIR / "visual_audit.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(f"\n{'=' * 70}")
    print(f"BILAN : {len(all_audits)} produits audités")
    print(f"  ✓ Approve : {counters.get('approve', 0)}")
    print(f"  ⚠ Review  : {counters.get('review', 0)}")
    print(f"  ✗ Reject  : {counters.get('reject', 0)}")
    print(f"\n→ Rapport complet : {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
