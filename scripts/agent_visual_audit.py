"""
Agent VISUAL AUDIT — détecte automatiquement les designs invendables.

Scanne products/ et flag les designs qui posent problème :
1. Texte gibberish dans l'image (OCR + détection de mots non-dictionnaires)
2. Composition off-topic (image trop sombre, trop floue, trop vide)
3. Métadonnées manquantes / corrompues

Pour chaque pipeline, génère :
- data/visual_audit.json : rapport global avec stats
- products/<pipeline>/<design>/AUDIT.txt : verdict détaillé par design

Mode dégradé sans tesseract OCR : utilise uniquement les heuristiques
visuelles (variance pixels, distribution couleurs).

Variables d'env :
  AUTO_REJECT=1     déplace les designs rejected vers products/_rejected/
  MIN_SCORE=50      seuil de rejet (0-100)
"""

import json
import os
import shutil
import sys
from collections import Counter
from pathlib import Path

try:
    from PIL import Image, ImageStat
except ImportError:
    print("ERREUR : Pillow non installé")
    sys.exit(2)

# Tesseract est optionnel — on tente sans planter si absent
HAS_TESSERACT = False
try:
    import subprocess
    result = subprocess.run(["tesseract", "--version"],
                             capture_output=True, timeout=5)
    HAS_TESSERACT = result.returncode == 0
except Exception:  # noqa: BLE001
    HAS_TESSERACT = False

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"
DATA_DIR = ROOT / "data"
REJECTED_DIR = PRODUCTS_DIR / "_rejected"

# Dictionnaire anglais minimal pour détecter texte gibberish
# (mots courants — si <30% des mots OCR sont dedans, suspicion de gibberish)
COMMON_ENGLISH = {
    "a", "the", "is", "of", "and", "to", "in", "i", "it", "you", "that",
    "he", "was", "for", "on", "are", "with", "as", "his", "they", "at",
    "be", "this", "have", "from", "or", "one", "had", "by", "word", "but",
    "not", "what", "all", "were", "we", "when", "your", "can", "said",
    "love", "my", "me", "her", "him", "she", "an", "if", "do", "will",
    "no", "so", "out", "go", "up", "down", "got", "now", "back", "good",
    "best", "more", "less", "new", "old", "all", "any", "way",
    # vocabulaire ciblé merch/niches
    "reading", "cat", "dog", "coffee", "tea", "wine", "yoga", "fishing",
    "hiking", "camping", "knitting", "crochet", "embroidery", "gardening",
    "horse", "chicken", "dnd", "chess", "baking", "music", "therapy",
    "diagnosed", "warning", "official", "certified", "professional",
    "patiently", "department", "union", "member", "personality", "powered",
    "grid", "born", "replaced", "addicted", "license", "first", "last",
    "morning", "night", "day", "week", "year", "summer", "winter",
    "spring", "fall", "autumn", "mom", "dad", "girl", "boy", "life",
    "love", "joy", "hope", "faith", "peace", "fear", "strength", "rest",
    "wisdom", "grace", "mercy", "spirit", "trust",
}


def has_text_overlay_in_metadata(meta_dir: Path) -> bool:
    """Si le design utilise Pillow overlay (cover KDP, future v2), pas besoin
    d'auditer le texte généré."""
    meta_path = meta_dir / "metadata.json"
    if not meta_path.exists():
        return False
    try:
        meta = json.loads(meta_path.read_text())
        return meta.get("text_overlay_method") == "pillow"
    except Exception:
        return False


def extract_text_ocr(image_path: Path) -> str:
    """Tente OCR via tesseract CLI si disponible."""
    if not HAS_TESSERACT:
        return ""
    try:
        result = subprocess.run(
            ["tesseract", str(image_path), "-", "--psm", "6", "-l", "eng"],
            capture_output=True, timeout=30,
        )
        return result.stdout.decode("utf-8", errors="ignore").strip()
    except Exception:  # noqa: BLE001
        return ""


def score_text_quality(text: str) -> float:
    """Note la qualité textuelle (0=gibberish total, 100=parfait)."""
    if not text or len(text.strip()) < 3:
        return 50  # neutre — pas de texte détecté
    words = [w.lower().strip(".,!?;:") for w in text.split() if w.strip()]
    if not words:
        return 50
    # Compte les mots qui matchent l'anglais courant
    matches = sum(1 for w in words if w in COMMON_ENGLISH or len(w) <= 2)
    ratio = matches / len(words)

    # Heuristique : si on a plus de 8 mots ET <30% sont valides → gibberish
    if len(words) >= 5 and ratio < 0.3:
        return 10
    if ratio < 0.5:
        return 35
    if ratio < 0.7:
        return 70
    return 90


def score_visual_quality(image_path: Path) -> dict:
    """Score visuel basique : variance pixels, distribution couleurs."""
    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as exc:  # noqa: BLE001
        return {"score": 0, "reason": f"image illisible: {exc}"}

    stat = ImageStat.Stat(img)
    # Variance par canal (sur 0-128 environ, plus c'est varié plus c'est riche)
    variance_avg = sum(stat.var) / 3
    # Luminosité moyenne (évite tout-noir/tout-blanc)
    mean_avg = sum(stat.mean) / 3

    issues = []
    score = 100
    if variance_avg < 100:
        score -= 30
        issues.append("composition très uniforme (peut être vide)")
    if mean_avg < 30:
        score -= 30
        issues.append("image trop sombre")
    if mean_avg > 245:
        score -= 30
        issues.append("image presque blanche")
    if img.width < 800 or img.height < 800:
        score -= 20
        issues.append(f"résolution faible ({img.width}x{img.height})")

    return {
        "score": max(0, score),
        "variance_avg": round(variance_avg, 1),
        "luminosity_avg": round(mean_avg, 1),
        "dimensions": f"{img.width}x{img.height}",
        "issues": issues,
    }


def audit_design(design_dir: Path) -> dict:
    """Audit complet d'un dossier de design."""
    meta_path = design_dir / "metadata.json"
    if not meta_path.exists():
        return {"status": "skip", "reason": "no metadata.json"}

    try:
        metadata = json.loads(meta_path.read_text())
    except Exception:
        metadata = {}

    # Trouve l'image principale à auditer
    preview = design_dir / "etsy_preview.jpg"
    if not preview.exists():
        preview = next(design_dir.glob("*.jpg"), None) \
            or next(design_dir.glob("*.png"), None)
    if not preview or not preview.exists():
        return {"status": "skip", "reason": "no image"}

    visual = score_visual_quality(preview)

    # Pipelines qui généraient du texte via Flux SANS overlay Pillow
    # → présupposer que le texte est probablement gibberish (Flux ne sait
    # pas faire de texte fiable). Sauf si métadonnée explicite "text_overlay_method=pillow".
    text_dependent_pipelines = {
        "viral_formats", "iheart", "iheart_v2", "cultural_arbitrage",
        "literal_idioms", "bible_verses",
    }
    pipeline = detect_pipeline(design_dir)
    uses_overlay = metadata.get("text_overlay_method") == "pillow"

    if uses_overlay:
        text_score = 100
        text_extracted = "(pillow overlay, texte garanti correct)"
    elif pipeline in text_dependent_pipelines:
        # Sans overlay, on présume gibberish jusqu'à preuve OCR du contraire
        text_extracted = extract_text_ocr(preview)
        if text_extracted and HAS_TESSERACT:
            text_score = score_text_quality(text_extracted)
        else:
            # Pas d'OCR dispo : on flag en review systématique pour ces pipelines
            text_score = 30
            text_extracted = "(Flux text rendering = unreliable, no overlay → suspected gibberish)"
    else:
        # Pipelines sans texte (tumbler patterns, coloring, STL) : OK par défaut
        text_score = 80
        text_extracted = "(no text expected in this pipeline)"

    composite_score = (visual["score"] * 0.4 + text_score * 0.6)

    verdict = "approve" if composite_score >= 65 else \
              "review" if composite_score >= 45 else \
              "reject"

    return {
        "status": verdict,
        "composite_score": round(composite_score, 1),
        "visual_score": visual["score"],
        "text_score": text_score,
        "uses_overlay": uses_overlay,
        "pipeline": pipeline,
        "visual_details": visual,
        "text_extracted": text_extracted[:200],
        "image_audited": str(preview.relative_to(PRODUCTS_DIR)),
    }


def detect_pipeline(design_dir: Path) -> str:
    parts = design_dir.relative_to(PRODUCTS_DIR).parts
    return parts[0] if parts else ""


def write_audit_file(design_dir: Path, audit: dict) -> None:
    txt = (
        f"AUDIT VISUEL — {datetime_str()}\n"
        f"{'=' * 60}\n\n"
        f"VERDICT : {audit['status'].upper()}\n"
        f"Score composite : {audit.get('composite_score', 0)}/100\n"
        f"  - Visual : {audit.get('visual_score', 0)}/100\n"
        f"  - Text   : {audit.get('text_score', 0)}/100\n\n"
        f"Détails visuels :\n"
        f"  {audit.get('visual_details', {}).get('issues', []) or 'aucun problème'}\n\n"
        f"Texte OCR extrait :\n"
        f"  « {audit.get('text_extracted', '(rien)')} »\n\n"
    )
    if audit["status"] == "reject":
        txt += "→ NE PAS UPLOADER. Régénérer le design ou supprimer.\n"
    elif audit["status"] == "review":
        txt += "→ REVUE MANUELLE recommandée avant upload.\n"
    else:
        txt += "→ OK à uploader.\n"
    (design_dir / "AUDIT.txt").write_text(txt, encoding="utf-8")


def datetime_str() -> str:
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PRODUCTS_DIR.exists():
        print(f"✗ {PRODUCTS_DIR} inexistant")
        return 1

    auto_reject = os.environ.get("AUTO_REJECT") == "1"
    min_score = float(os.environ.get("MIN_SCORE", "0") or "0")

    print("=" * 70)
    print("VISUAL AUDIT — scanne products/ et flag les designs invendables")
    print("=" * 70)
    print(f"Tesseract OCR : {'OK' if HAS_TESSERACT else 'NON (mode dégradé)'}")
    print(f"Auto-reject : {auto_reject}")
    print()

    all_audits = []
    counters = Counter()

    for pipeline_dir in sorted(PRODUCTS_DIR.iterdir()):
        if not pipeline_dir.is_dir() or pipeline_dir.name == "_rejected":
            continue
        pipeline_name = pipeline_dir.name
        for meta_path in pipeline_dir.rglob("metadata.json"):
            design_dir = meta_path.parent
            audit = audit_design(design_dir)
            if audit.get("status") == "skip":
                continue
            audit["pipeline"] = pipeline_name
            audit["design_path"] = str(design_dir.relative_to(PRODUCTS_DIR))
            all_audits.append(audit)
            counters[audit["status"]] += 1

            write_audit_file(design_dir, audit)

            # Auto-reject : déplace les designs rejected vers _rejected/
            if auto_reject and audit["status"] == "reject":
                dest = REJECTED_DIR / pipeline_name / design_dir.relative_to(
                    pipeline_dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                if not dest.exists():
                    shutil.move(str(design_dir), str(dest))
                    print(f"  ⛔ REJECT  {design_dir.relative_to(PRODUCTS_DIR)} "
                          f"(score {audit['composite_score']})")
            else:
                icon = {"approve": "✓", "review": "⚠", "reject": "✗"}[audit["status"]]
                print(f"  {icon} {audit['status']:<8} "
                      f"{str(design_dir.relative_to(PRODUCTS_DIR)):<60} "
                      f"score {audit['composite_score']}")

    # Stats par pipeline
    by_pipeline = {}
    for a in all_audits:
        p = a["pipeline"]
        if p not in by_pipeline:
            by_pipeline[p] = Counter()
        by_pipeline[p][a["status"]] += 1

    report = {
        "audit_timestamp": datetime_str(),
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
    print(f"BILAN : {len(all_audits)} designs audités")
    print(f"  ✓ Approve : {counters['approve']}")
    print(f"  ⚠ Review  : {counters['review']}")
    print(f"  ✗ Reject  : {counters['reject']}")
    print(f"\nPar pipeline :")
    for p, c in sorted(by_pipeline.items()):
        total = sum(c.values())
        approve_pct = 100 * c.get("approve", 0) / max(total, 1)
        print(f"  {p:<25} {total:>4} designs, "
              f"{approve_pct:>5.0f}% approve")
    print(f"\n→ Rapport : {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
