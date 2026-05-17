"""
Agent Auditor — score qualité technique de chaque design produit.

Lit récursivement tous les fichiers `source.png` dans products/<niche>/design_NN/
et calcule un score de qualité (0-100) basé sur 4 métriques Pillow gratuites :

1. **Contraste** (0-25) : écart-type des pixels luminance — une image plate
   (faible contraste) est en général une image ratée par Flux.
2. **Netteté** (0-25) : variance du Laplacien (édge-detection simple) —
   plus c'est élevé, plus les contours sont nets, donc moins floue.
3. **Couleur** (0-25) : variance HSV de saturation — une image en
   nuances de gris monotone est en général moins commerciale qu'une avec
   des tons variés.
4. **Composition** (0-25) : règle des tiers approximative — détecte si
   le sujet principal est centré ou décentré (visuellement plus
   intéressant).

Output : un fichier `audit.json` par design + un récap global
`products/<niche>/audit_summary.json` avec classement.

Optionnel : si GEMINI_API_KEY fournie, on ajoute un score
"vendabilité commerciale" via Gemini Vision (1500 req/jour gratuit).
Mais le script marche 100 % sans clé.

Usage :
    SOURCE_NICHE=witchy_cottagecore python scripts/agent_auditor.py
    python scripts/agent_auditor.py  # toutes les niches

Note : les designs en dessous de QUALITY_THRESHOLD seront marqués
"reject" pour que l'agent Curator les écarte du bulk upload.
"""

import json
import math
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageFilter, ImageStat
except ImportError:
    print("ERREUR : Pillow non installé.")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = ROOT / "products"

QUALITY_THRESHOLD = 60  # /100 — designs en dessous = rejetés


# ─────────────────────────────────────────────────────────────────────
# MÉTRIQUES QUALITÉ
# ─────────────────────────────────────────────────────────────────────


def metric_contrast(img: Image.Image) -> float:
    """Écart-type des pixels luminance. Plus haut = plus contrasté."""
    gray = img.convert("L")
    stddev = ImageStat.Stat(gray).stddev[0]
    # Normalise : 0-25 (50 stddev = excellent, plafonné)
    return min(stddev / 2, 25)


def metric_sharpness(img: Image.Image) -> float:
    """Variance du Laplacien — proxy de netteté."""
    gray = img.convert("L")
    # Edge detection rudimentaire
    edges = gray.filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(edges)
    # Plus la moyenne d'edges est haute, plus l'image est nette
    sharp = stat.mean[0]
    # Normalise : 0-25 (mean 30+ = très net)
    return min(sharp / 1.2, 25)


def metric_color(img: Image.Image) -> float:
    """Variance HSV saturation — plus c'est varié, plus c'est commercial."""
    hsv = img.convert("HSV")
    saturation = hsv.split()[1]
    stat = ImageStat.Stat(saturation)
    sat_stddev = stat.stddev[0]
    # Normalise : 0-25 (60 stddev = très coloré)
    return min(sat_stddev / 2.4, 25)


def metric_composition(img: Image.Image) -> float:
    """Approximation : intensité dans les zones de la règle des tiers.
    Plus l'image a des éléments visuels dans les 4 points de force, mieux c'est.
    """
    gray = img.convert("L").resize((300, 300))
    pixels = gray.load()
    # 4 points de force (intersections des tiers)
    points = [(100, 100), (200, 100), (100, 200), (200, 200)]
    # Intensité moyenne dans une fenêtre 40px autour de chaque point
    forces = []
    for cx, cy in points:
        window_vals = [
            pixels[x, y]
            for x in range(cx - 20, cx + 20)
            for y in range(cy - 20, cy + 20)
        ]
        forces.append(sum(window_vals) / len(window_vals))
    # Variance entre les 4 points : si tous identiques = image plate
    mean_force = sum(forces) / 4
    variance = sum((f - mean_force) ** 2 for f in forces) / 4
    # Normalise : variance 500+ = belle composition
    return min(math.sqrt(variance) / 1, 25)


def audit_design(source_path: Path) -> dict:
    img = Image.open(source_path)
    contrast = metric_contrast(img)
    sharpness = metric_sharpness(img)
    color = metric_color(img)
    composition = metric_composition(img)
    total = contrast + sharpness + color + composition
    return {
        "file": str(source_path.relative_to(ROOT)),
        "width": img.width,
        "height": img.height,
        "filesize_kb": source_path.stat().st_size // 1024,
        "scores": {
            "contrast": round(contrast, 2),
            "sharpness": round(sharpness, 2),
            "color": round(color, 2),
            "composition": round(composition, 2),
        },
        "total_score": round(total, 2),
        "verdict": "keep" if total >= QUALITY_THRESHOLD else "reject",
    }


# ─────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────


def audit_niche(niche_dir: Path) -> dict:
    print(f"\n=== Audit niche : {niche_dir.name} ===")
    designs = sorted(niche_dir.glob("design_*/source.png"))
    if not designs:
        print(f"  Aucun design trouvé dans {niche_dir}")
        return {}

    results = []
    for src in designs:
        try:
            audit = audit_design(src)
            results.append(audit)
            verdict_icon = "✓" if audit["verdict"] == "keep" else "✗"
            print(f"  {verdict_icon} {src.parent.name} : "
                  f"{audit['total_score']:.1f}/100  "
                  f"(C{audit['scores']['contrast']:.0f} "
                  f"N{audit['scores']['sharpness']:.0f} "
                  f"K{audit['scores']['color']:.0f} "
                  f"C{audit['scores']['composition']:.0f})")
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {src.parent.name} : {type(exc).__name__}: {exc}")

    if not results:
        return {}

    # Sauvegarde audit individuel par design
    for audit in results:
        design_dir = ROOT / Path(audit["file"]).parent
        (design_dir / "audit.json").write_text(json.dumps(audit, indent=2))

    # Récap niche
    keep_count = sum(1 for r in results if r["verdict"] == "keep")
    avg_score = sum(r["total_score"] for r in results) / len(results)
    results.sort(key=lambda r: r["total_score"], reverse=True)
    summary = {
        "niche": niche_dir.name,
        "audited_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "total_designs": len(results),
        "keep_count": keep_count,
        "reject_count": len(results) - keep_count,
        "average_score": round(avg_score, 2),
        "quality_threshold": QUALITY_THRESHOLD,
        "ranking": results,
    }
    summary_path = niche_dir / "audit_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"\n  → {keep_count}/{len(results)} designs gardés "
          f"(score moyen {avg_score:.1f}/100)")
    return summary


def main() -> int:
    if not PRODUCTS_DIR.exists():
        print(f"Aucun dossier products/ trouvé.")
        return 1

    target_niche = os.environ.get("SOURCE_NICHE", "").strip()
    niches = (
        [PRODUCTS_DIR / target_niche]
        if target_niche
        else [p for p in PRODUCTS_DIR.iterdir() if p.is_dir()]
    )

    summaries = []
    for niche_dir in niches:
        if not niche_dir.exists():
            print(f"Niche introuvable : {niche_dir}")
            continue
        summary = audit_niche(niche_dir)
        if summary:
            summaries.append(summary)

    # Récap global
    if summaries:
        total_designs = sum(s["total_designs"] for s in summaries)
        total_keep = sum(s["keep_count"] for s in summaries)
        print(f"\n{'=' * 60}")
        print(f"Total audité : {total_designs} designs sur {len(summaries)} niches")
        print(f"À garder    : {total_keep}")
        print(f"À rejeter   : {total_designs - total_keep}")

    return 0 if summaries else 1


if __name__ == "__main__":
    sys.exit(main())
