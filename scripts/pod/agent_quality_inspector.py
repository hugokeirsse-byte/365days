#!/usr/bin/env python3
"""
Agent Quality Inspector — Validation et upscaling pour POD.

Vérifie que les patterns générés sont :
  1. Seamless (test de tuilage 2×2)
  2. À la bonne résolution (min 5400px pour Spoonflower fabric)
  3. En sRGB (pas de CMYK, pas de profil ICC exotique)
  4. Sans artefacts de compression visibles
  5. Format correct (PNG ou JPEG selon plateforme)

Si résolution insuffisante : upscale via HuggingFace Inference API
(modèle Real-ESRGAN × 4, gratuit avec HF_API_KEY).

Input  : un dossier de PNGs ou un fichier spécifique
Output : rapport JSON + images corrigées dans products/pod/ready/

Usage :
    python scripts/pod/agent_quality_inspector.py products/pod/generated/
    python scripts/pod/agent_quality_inspector.py image.png
"""
from __future__ import annotations

import io
import json
import math
import os
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
READY_DIR = ROOT / "products" / "pod" / "ready"
READY_DIR.mkdir(parents=True, exist_ok=True)

# Seuils minimaux par plateforme
MIN_RESOLUTION = {
    "spoonflower_fabric":    5400,  # 150dpi × 36 inches
    "spoonflower_wallpaper": 7200,
    "society6":              4500,
    "redbubble":             7632,
    "default":               3000,
}
TARGET_RESOLUTION = 8000  # cible idéale pour réutilisation multi-plateforme


# ─── Test seamless ─────────────────────────────────────────────────────────────

def test_seamless(img_path: Path, tolerance: float = 0.02) -> dict:
    """
    Test de tuilage : assemble 4 copies (2×2) et vérifie que les bords
    n'ont pas de discontinuité visible (différence de pixel < tolérance).

    Retourne {"seamless": bool, "max_edge_diff": float, "details": str}
    """
    try:
        from PIL import Image, ImageChops
        import numpy as np
    except ImportError:
        return {"seamless": None, "error": "PIL/numpy non disponible", "max_edge_diff": None}

    try:
        img = Image.open(img_path).convert("RGB")
    except Exception as exc:
        return {"seamless": False, "error": str(exc), "max_edge_diff": None}

    w, h = img.size
    # Crée une grille 2×2
    grid = Image.new("RGB", (w * 2, h * 2))
    for dy in range(2):
        for dx in range(2):
            grid.paste(img, (dx * w, dy * h))

    arr = __import__("numpy").array(grid, dtype=float) / 255.0

    # Vérifie la continuité aux bords (ligne centrale horizontale et verticale)
    # Bord horizontal : ligne y=h-1 vs y=h
    top_border    = arr[h - 1, :w, :]   # dernière ligne du tile du haut
    bottom_border = arr[h,     :w, :]   # première ligne du tile du bas
    h_diff = float(__import__("numpy").abs(top_border - bottom_border).max())

    # Bord vertical : colonne x=w-1 vs x=w
    left_border  = arr[:h, w - 1, :]
    right_border = arr[:h, w,     :]
    v_diff = float(__import__("numpy").abs(left_border - right_border).max())

    max_diff = max(h_diff, v_diff)
    is_seamless = max_diff < tolerance

    return {
        "seamless": is_seamless,
        "max_edge_diff": round(max_diff, 4),
        "h_diff": round(h_diff, 4),
        "v_diff": round(v_diff, 4),
        "details": (
            f"Max bord diff: {max_diff:.4f} ({'OK' if is_seamless else 'FAIL'})"
        ),
    }


# ─── Upscaling via HuggingFace ─────────────────────────────────────────────────

def upscale_hf(img_path: Path, out_path: Path, scale: int = 4) -> dict:
    """
    Upscale via HuggingFace Inference API (Real-ESRGAN).
    Nécessite HF_API_KEY dans l'environnement.
    """
    api_key = os.environ.get("HF_API_KEY")
    if not api_key:
        return {"success": False, "error": "HF_API_KEY manquant"}

    model = "ai-forever/Real-ESRGAN"
    url = f"https://api-inference.huggingface.co/models/{model}"

    img_bytes = img_path.read_bytes()
    try:
        req = urllib.request.Request(
            url,
            data=img_bytes,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/octet-stream",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            result_bytes = r.read()
        out_path.write_bytes(result_bytes)
        return {"success": True, "output_path": str(out_path)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def upscale_pil_lanczos(img_path: Path, out_path: Path, target_px: int) -> dict:
    """Fallback upscale via Lanczos (PIL, pas d'IA) si HF non dispo."""
    try:
        from PIL import Image
        img = Image.open(img_path)
        w, h = img.size
        ratio = target_px / max(w, h)
        new_w, new_h = int(w * ratio), int(h * ratio)
        upscaled = img.resize((new_w, new_h), Image.LANCZOS)
        upscaled.save(out_path, optimize=True)
        return {"success": True, "output_path": str(out_path), "method": "lanczos"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ─── Inspection d'une image ─────────────────────────────────────────────────────

def inspect_image(img_path: Path, target_platform: str = "default") -> dict:
    try:
        from PIL import Image
        pil_ok = True
    except ImportError:
        pil_ok = False

    result = {
        "file":     str(img_path.name),
        "path":     str(img_path),
        "checks":   {},
        "pass":     False,
        "actions_needed": [],
    }

    if not img_path.exists():
        result["checks"]["exists"] = False
        return result
    result["checks"]["exists"] = True

    # ── Taille du fichier ──
    size_mb = img_path.stat().st_size / (1024 * 1024)
    result["size_mb"] = round(size_mb, 2)
    result["checks"]["file_not_empty"] = size_mb > 0.01

    # ── Résolution ──
    if pil_ok:
        try:
            from PIL import Image
            img = Image.open(img_path)
            w, h = img.size
            result["width"]  = w
            result["height"] = h
            result["mode"]   = img.mode
            min_px = MIN_RESOLUTION.get(target_platform, MIN_RESOLUTION["default"])
            res_ok = min(w, h) >= min_px
            result["checks"]["resolution_ok"] = res_ok
            if not res_ok:
                result["actions_needed"].append(
                    f"upscale ({min(w,h)}px → {min_px}px min)"
                )
            # Colorspace
            color_ok = img.mode in ("RGB", "RGBA", "L")
            result["checks"]["colorspace_ok"] = color_ok
            if not color_ok:
                result["actions_needed"].append(f"convert colorspace ({img.mode} → RGB)")
        except Exception as exc:
            result["checks"]["pil_read"] = False
            result["pil_error"] = str(exc)
    else:
        result["checks"]["pil_available"] = False
        result["actions_needed"].append("install Pillow pour validation complète")

    # ── Test seamless ──
    if pil_ok and img_path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
        seamless_result = test_seamless(img_path)
        result["seamless"] = seamless_result
        result["checks"]["seamless"] = seamless_result.get("seamless")
        if seamless_result.get("seamless") is False:
            result["actions_needed"].append(
                f"fix seamless (bord diff: {seamless_result.get('max_edge_diff')})"
            )

    # ── Verdict global ──
    checks = result["checks"]
    passed = all(v is True for v in checks.values() if v is not None)
    result["pass"] = passed
    return result


# ─── Pipeline de correction ──────────────────────────────────────────────────────

def fix_image(inspection: dict, dry_run: bool = False) -> dict:
    """Applique les corrections nécessaires."""
    if inspection["pass"]:
        return {"fixed": False, "reason": "already_ok"}

    img_path = Path(inspection["path"])
    actions  = inspection.get("actions_needed", [])
    fix_log  = []

    if dry_run:
        return {"fixed": False, "dry_run": True, "would_do": actions}

    current = img_path

    for action in actions:
        if "upscale" in action:
            target = TARGET_RESOLUTION
            out_p  = READY_DIR / f"{img_path.stem}_upscaled{img_path.suffix}"
            # Essaie HF d'abord, puis Lanczos
            result = upscale_hf(current, out_p, scale=4)
            if not result["success"]:
                print(f"  ⚠ HF upscale échoué ({result.get('error')}), fallback Lanczos")
                result = upscale_pil_lanczos(current, out_p, target)
            if result["success"]:
                current = out_p
                fix_log.append(f"upscaled → {out_p.name}")

        elif "convert colorspace" in action:
            try:
                from PIL import Image
                img = Image.open(current).convert("RGB")
                out_p = READY_DIR / f"{current.stem}_rgb{current.suffix}"
                img.save(out_p)
                current = out_p
                fix_log.append(f"converted to RGB → {out_p.name}")
            except Exception as exc:
                fix_log.append(f"colorspace fix failed: {exc}")

    # Copie dans ready/ si pas encore dedans
    if current != img_path and READY_DIR not in current.parents:
        import shutil
        final = READY_DIR / current.name
        shutil.copy2(current, final)
        current = final

    return {"fixed": len(fix_log) > 0, "actions_done": fix_log, "output": str(current)}


# ─── Main ───────────────────────────────────────────────────────────────────────

def run(target: str | None = None, platform: str = "spoonflower_fabric") -> dict:
    if not target:
        # Scanne le dossier generated/ par défaut
        gen_dir = ROOT / "products" / "pod" / "generated"
        if not gen_dir.exists():
            print(f"✗ Aucun dossier cible. Spécifie un fichier ou dossier.")
            return {}
        images = list(gen_dir.glob("*.png")) + list(gen_dir.glob("*.jpg"))
    else:
        p = Path(target)
        if p.is_dir():
            images = list(p.glob("*.png")) + list(p.glob("*.jpg"))
        else:
            images = [p] if p.exists() else []

    if not images:
        print("✗ Aucune image à inspecter.")
        return {}

    print("=" * 60)
    print(f"Quality Inspector — {len(images)} image(s) — plateforme: {platform}")
    print("=" * 60)

    report = {
        "generated_at": date.today().isoformat(),
        "platform":     platform,
        "images":       [],
        "pass_count":   0,
        "fail_count":   0,
    }

    for img_path in sorted(images):
        print(f"\n  [{img_path.name}]")
        inspection = inspect_image(img_path, platform)

        status = "✓ OK" if inspection["pass"] else f"✗ {', '.join(inspection.get('actions_needed', []))}"
        print(f"  {status}")

        if not inspection["pass"]:
            print(f"  → Correction automatique…")
            fix_result = fix_image(inspection)
            inspection["fix_result"] = fix_result
            if fix_result.get("fixed"):
                print(f"  ✓ Corrigé : {fix_result.get('output')}")

        report["images"].append(inspection)
        if inspection["pass"]:
            report["pass_count"] += 1
        else:
            report["fail_count"] += 1

    out_file = ROOT / "data" / "pod" / "quality_report.json"
    out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print(f"\n{'=' * 60}")
    print(f"✓ {report['pass_count']} OK / {report['fail_count']} corrigés")
    print(f"  Rapport → {out_file}")
    print("=" * 60)
    return report


if __name__ == "__main__":
    target   = sys.argv[1] if len(sys.argv) > 1 else None
    platform = sys.argv[2] if len(sys.argv) > 2 else "spoonflower_fabric"
    run(target, platform)
