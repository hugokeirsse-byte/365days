#!/usr/bin/env python3
"""
Audit STL — audit qualité dédié aux produits d'impression 3D.

Vérifie ce qui compte pour les acheteurs sur Cults3D / Printables :
- Géométrie valide et imprimable (pas de mesh cassé)
- Texte réellement gravé (variantes physiquement distinctes)
- Dimensions dans les normes de printabilité
- Visuels de présentation présents et exploitables
- Métadonnées complètes pour le listing

Variables d'env :
  STL_DIR   — répertoire produit (chemin relatif ou absolu)
  AUDIT_ALL — si "1", audite tous les produits stl_3d
"""

import json
import os
import struct
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ============================================================
# SEUILS QUALITÉ — adaptés aux attentes acheteurs Cults3D/Printables
# ============================================================
# Acheteurs attendent : STL valides, texte visible, dimensions printables,
# photos propres, description complète.

MIN_TRIANGLES = 100           # Un objet réel a toujours > 100 triangles
MAX_DIM_MM = 300              # Max dimension raisonnable pour impression desktop
MIN_DIM_MM = 3                # Minimum cohérent (rien de moins de 3mm)
MIN_VARIANTS = 5              # Minimum de variantes pour un pack vendable
APPROVE_THRESHOLD = 75
REVIEW_THRESHOLD = 55


def parse_stl_binary(stl_path: Path) -> dict:
    """Parse un STL binaire. Retourne dict avec triangles, dimensions, validité."""
    result = {
        "valid": False,
        "triangles": 0,
        "dims_mm": None,
        "error": None,
    }

    try:
        size = stl_path.stat().st_size
        if size < 84:
            result["error"] = "Fichier trop petit (<84 bytes)"
            return result

        with open(stl_path, "rb") as f:
            header = f.read(80)
            count_bytes = f.read(4)
            if len(count_bytes) < 4:
                result["error"] = "Header tronqué"
                return result

            count = struct.unpack("<I", count_bytes)[0]
            expected_size = 84 + count * 50

            if count == 0:
                result["error"] = "0 triangles"
                return result

            if abs(size - expected_size) > size * 0.05:  # tolérance 5%
                result["error"] = f"Taille incohérente: {size} vs {expected_size} attendus"

            # Lire tous les sommets pour les dimensions
            xs, ys, zs = [], [], []
            for _ in range(min(count, 50000)):
                raw = f.read(50)
                if len(raw) < 50:
                    break
                # 3 floats normal + 3×3 floats sommets + 2 attr
                for vi in range(3):
                    offset = 12 + vi * 12
                    x, y, z = struct.unpack("<3f", raw[offset:offset + 12])
                    xs.append(x)
                    ys.append(y)
                    zs.append(z)

        if not xs:
            result["error"] = "Impossible de lire les sommets"
            return result

        dx = max(xs) - min(xs)
        dy = max(ys) - min(ys)
        dz = max(zs) - min(zs)
        result["triangles"] = count
        result["dims_mm"] = {"x": round(dx, 1), "y": round(dy, 1), "z": round(dz, 1)}
        result["valid"] = True

    except Exception as e:
        result["error"] = str(e)[:100]

    return result


def check_variants_distinct(stl_paths: list) -> tuple:
    """Vérifie que les variantes sont physiquement différentes (pas toutes identiques).

    Avec OpenSCAD, chaque texte différent produit un nombre de triangles différent.
    Si tous les STL ont exactement le même nombre de triangles → ils sont identiques.
    """
    counts = set()
    triangle_counts = []
    for p in stl_paths:
        info = parse_stl_binary(p)
        n = info.get("triangles", 0)
        triangle_counts.append(n)
        counts.add(n)

    if len(stl_paths) <= 1:
        return True, triangle_counts

    # Si toutes les variantes ont exactement le même triangle count → identiques
    all_same = (len(counts) == 1 and len(stl_paths) > 1)
    return not all_same, triangle_counts


def check_printability(dims: dict) -> list:
    """Vérifie que les dimensions sont printables sur une imprimante desktop standard."""
    issues = []
    if dims is None:
        return ["Dimensions illisibles"]

    x, y, z = dims.get("x", 0), dims.get("y", 0), dims.get("z", 0)
    max_dim = max(x, y, z)
    min_dim = min(x, y, z)

    if max_dim > MAX_DIM_MM:
        issues.append(f"Dimension {max_dim:.0f}mm dépasse {MAX_DIM_MM}mm (ne rentre pas dans la plupart des imprimantes desktop)")

    if min_dim < MIN_DIM_MM and min_dim > 0:
        issues.append(f"Dimension minimale {min_dim:.1f}mm trop petite (fragilité, difficile à imprimer proprement)")

    if x < 1 or y < 1 or z < 1:
        issues.append(f"Objet quasi-plat ou point ({x:.1f}×{y:.1f}×{z:.1f}mm) — export incorrect?")

    return issues


def audit_stl_product(product_dir: Path) -> dict:
    """Audite un produit STL complet."""
    score = 100
    blocking = []    # causes de mauvaises reviews
    warnings = []
    manual_checks = []
    stats = {}

    files_dir = product_dir / "files"
    renders_dir = product_dir / "renders"
    cdc_path = product_dir / "cdc.json"
    meta_path = product_dir / "metadata.json"

    # ── GATE CDC ──────────────────────────────────────────────────────────
    gate = "unknown"
    if cdc_path.exists():
        try:
            cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
            gate = cdc.get("gate_cdc", "unknown")
        except Exception:
            pass

    if gate == "pending":
        return {
            "verdict": "PENDING",
            "score": 0,
            "blocking": ["CdC non validé par Hugo (gate_cdc=pending)"],
            "warnings": [],
            "manual_checks": [],
            "stats": {"gate": "pending"},
        }

    # ── FICHIERS STL ──────────────────────────────────────────────────────
    stl_files = sorted(files_dir.glob("*.stl")) if files_dir.exists() else []
    stats["stl_count"] = len(stl_files)

    if not stl_files:
        blocking.append("Aucun fichier STL dans files/ — production non effectuée")
        score -= 50

    elif len(stl_files) < MIN_VARIANTS:
        warnings.append(f"Seulement {len(stl_files)} variantes (minimum recommandé: {MIN_VARIANTS}) — pack peu attractif")
        score -= 15

    # ── GÉOMÉTRIE STL ─────────────────────────────────────────────────────
    stl_details = []
    invalid_count = 0
    dim_issues = []
    all_triangle_counts = []

    for stl_path in stl_files:
        info = parse_stl_binary(stl_path)
        stl_details.append({"name": stl_path.name, **info})

        if not info["valid"] or info["triangles"] < MIN_TRIANGLES:
            invalid_count += 1
            if info.get("error"):
                blocking.append(f"STL invalide: {stl_path.name} — {info['error']}")

        if info.get("dims_mm"):
            all_triangle_counts.append(info["triangles"])
            pprint_issues = check_printability(info["dims_mm"])
            dim_issues.extend([f"{stl_path.name}: {i}" for i in pprint_issues])

    if invalid_count > 0:
        blocking.append(f"{invalid_count}/{len(stl_files)} STL invalides ou corrompus")
        score -= min(50, invalid_count * 10)

    if dim_issues:
        for di in dim_issues[:3]:
            blocking.append(f"Dimension non-printable — {di}")
        score -= 20

    stats["stl_invalid"] = invalid_count
    stats["triangle_counts_sample"] = all_triangle_counts[:5]

    # ── VARIANTES DISTINCTES ──────────────────────────────────────────────
    if len(stl_files) >= 2:
        distinct, tri_counts = check_variants_distinct(stl_files)
        stats["variants_distinct"] = distinct
        stats["all_triangle_counts_same"] = not distinct

        if not distinct:
            blocking.append(
                f"CRITIQUE: toutes les {len(stl_files)} variantes ont exactement "
                f"{tri_counts[0]} triangles — elles sont PHYSIQUEMENT IDENTIQUES. "
                "Le texte n'est pas gravé dans la géométrie. Produit invendable."
            )
            score -= 50

    # ── VISUELS DE PRÉSENTATION ────────────────────────────────────────────
    renders = list(renders_dir.glob("*.png")) if renders_dir.exists() else []
    stats["renders_count"] = len(renders)
    renders_per_variant = len(renders) / len(stl_files) if stl_files else 0

    if not renders:
        blocking.append(
            "Aucun visuel PNG dans renders/ — sans photo le produit ne se vend pas sur Cults3D"
        )
        score -= 30

    elif renders_per_variant < 2:
        warnings.append(
            f"Seulement {renders_per_variant:.1f} visuels/variante — prévoir au moins 3 angles"
        )
        score -= 10

    # Vérifier que les PNG ont une taille réaliste (pas des images vides)
    tiny_renders = [r for r in renders if r.stat().st_size < 10_000]
    if tiny_renders:
        warnings.append(
            f"{len(tiny_renders)} visuels semblent vides (<10 KB) : "
            f"{', '.join(r.name for r in tiny_renders[:3])}"
        )
        score -= 10

    # ── MÉTADONNÉES LISTING ────────────────────────────────────────────────
    if not meta_path.exists():
        warnings.append("metadata.json absent — listing incomplet pour Cults3D")
        score -= 10
    else:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            required = ["titre", "description", "tags", "categorie", "licence"]
            missing = [k for k in required if not meta.get(k)]
            if missing:
                warnings.append(f"Métadonnées incomplètes: {', '.join(missing)}")
                score -= len(missing) * 3

            tags = meta.get("tags", [])
            if len(tags) < 5:
                warnings.append(f"Seulement {len(tags)} tags (min 5 pour visibilité)")
                score -= 5
        except Exception:
            warnings.append("metadata.json illisible")
            score -= 8

    # ── VÉRIFICATIONS MANUELLES OBLIGATOIRES ─────────────────────────────
    manual_checks = [
        "→ Imprimer 1 exemplaire test avant mise en vente (texte lisible et net?)",
        "→ Vérifier dans Bambu Studio / PrusaSlicer: pas de warning, support non nécessaire",
        "→ Tester avec 0.2mm layer height + PLA (paramètres acheteurs standard)",
        "→ Le texte est-il lisible à l'impression (taille min ~5mm pour du FDM)?",
        "→ Les photos de présentation montrent-elles le texte gravé clairement?",
        "→ Comparer avec les 5 meilleurs vendeurs de la même niche sur Cults3D",
        "→ Le prix (2-4 USD) est-il aligné avec le marché?",
    ]

    # ── VERDICT ───────────────────────────────────────────────────────────
    score = max(0, score)

    if blocking:
        # Aucun produit bloquant ne peut être APPROVE
        verdict = "REJECT" if score < REVIEW_THRESHOLD else "REVIEW"
    elif score >= APPROVE_THRESHOLD:
        verdict = "APPROVE"
    elif score >= REVIEW_THRESHOLD:
        verdict = "REVIEW"
    else:
        verdict = "REJECT"

    return {
        "verdict": verdict,
        "score": score,
        "blocking": blocking,
        "warnings": warnings,
        "manual_checks": manual_checks,
        "stats": stats,
        "stl_details": stl_details[:10],
    }


def write_audit_report(product_dir: Path, result: dict):
    """Écrit le fichier AUDIT.txt dans le répertoire produit."""
    now = datetime.utcnow().isoformat() + "Z"
    lines = [
        f"AUDIT STL v1 — {now}",
        f"Produit : {product_dir.name}",
        "=" * 60,
        "",
        f"VERDICT : {result['verdict']}",
        f"Score    : {result['score']}/100",
        "",
    ]

    if result["blocking"]:
        lines.append("── PROBLÈMES BLOQUANTS (causes de mauvaises reviews) ──")
        for b in result["blocking"]:
            lines.append(f"  ✗ BLOQUANT — {b}")
        lines.append("")

    if result["warnings"]:
        lines.append("── AVERTISSEMENTS ──")
        for w in result["warnings"]:
            lines.append(f"  ⚠ {w}")
        lines.append("")

    lines.append("── VÉRIFICATIONS MANUELLES OBLIGATOIRES ──")
    for m in result["manual_checks"]:
        lines.append(f"  {m}")
    lines.append("")

    lines.append("── STATS ──")
    for k, v in result["stats"].items():
        lines.append(f"  {k}: {v}")
    lines.append("")

    if result["stl_details"]:
        lines.append("── DÉTAILS STL (10 premiers) ──")
        for d in result["stl_details"]:
            name = d["name"]
            tri = d.get("triangles", "?")
            dims = d.get("dims_mm", {}) or {}
            valid = "✓" if d.get("valid") else "✗"
            err = f" [{d['error']}]" if d.get("error") else ""
            dim_str = ""
            if dims:
                dim_str = f" | {dims.get('x',0):.0f}×{dims.get('y',0):.0f}×{dims.get('z',0):.0f}mm"
            lines.append(f"  {valid} {name}: {tri} triangles{dim_str}{err}")
        lines.append("")

    if result["verdict"] == "APPROVE":
        lines.append("→ APPROUVÉ — Prêt pour upload sur Cults3D.")
        lines.append("  Faire les vérifications manuelles puis uploader.")
    elif result["verdict"] == "REVIEW":
        lines.append("→ EN RÉVISION — Corriger les avertissements puis ré-auditer.")
    elif result["verdict"] == "REJECT":
        lines.append("→ REJETÉ — Ne pas uploader. Corriger les problèmes critiques d'abord.")
    elif result["verdict"] == "PENDING":
        lines.append("→ EN ATTENTE — Hugo doit valider le CdC (gate_cdc=pending).")

    audit_path = product_dir / "AUDIT.txt"
    audit_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[Audit STL] AUDIT.txt → {audit_path}")
    return audit_path


def run_audit():
    stl_dir_env = os.environ.get("STL_DIR", "")
    audit_all = os.environ.get("AUDIT_ALL", "0") == "1"

    if audit_all:
        stl_base = ROOT / "products" / "stl_3d"
        if not stl_base.exists():
            print("[Audit STL] Aucun répertoire products/stl_3d/")
            return

        dirs = [d for d in sorted(stl_base.iterdir()) if d.is_dir()]
        print(f"[Audit STL] {len(dirs)} produits à auditer")
        results = {}
        for d in dirs:
            r = audit_stl_product(d)
            write_audit_report(d, r)
            results[d.name] = r["verdict"]
            print(f"  {d.name}: {r['verdict']} ({r['score']}/100)")

        print(f"\n[Audit STL] Résumé: {results}")
        return

    if stl_dir_env:
        product_dir = ROOT / stl_dir_env if not Path(stl_dir_env).is_absolute() else Path(stl_dir_env)
    else:
        stl_base = ROOT / "products" / "stl_3d"
        if not stl_base.exists():
            print("[Audit STL] products/stl_3d/ introuvable")
            sys.exit(1)
        dirs = sorted(
            [d for d in stl_base.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        if not dirs:
            print("[Audit STL] Aucun produit stl_3d trouvé")
            sys.exit(0)
        product_dir = dirs[0]

    print(f"[Audit STL] Audit: {product_dir.name}")
    result = audit_stl_product(product_dir)
    write_audit_report(product_dir, result)

    print(f"\n[Audit STL] VERDICT: {result['verdict']} ({result['score']}/100)")
    if result["blocking"]:
        print("[Audit STL] Problèmes bloquants:")
        for b in result["blocking"]:
            print(f"  ✗ {b}")

    if result["verdict"] == "REJECT":
        sys.exit(1)


if __name__ == "__main__":
    run_audit()
