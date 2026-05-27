#!/usr/bin/env python3
"""
Render STL — génère des visuels PNG propres à partir de fichiers STL.

Utilise matplotlib 3D (headless, aucune dépendance externe au-delà de numpy).
3 angles par modèle : face, oblique 45°, vue de dessus.

Variables d'env :
  STL_DIR  — répertoire produit (ex: products/stl_3d/stl_2026-05-27_bookmark_cottagecore)
  RENDER_ALL — si "1", rend tous les produits stl_3d avec des STL
"""

import json
import os
import struct
import sys
from pathlib import Path

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
except ImportError:
    print("[Render] ERREUR: matplotlib non installé. pip install matplotlib")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent

# Couleurs style impression 3D plastique mat
FACE_COLOR = "#DDD8F0"    # lavande clair (neutre, élégant)
EDGE_COLOR = "#BBB6D8"
BG_COLOR = "white"


def load_stl(path: Path):
    """Charge un STL binaire, renvoie (triangles, (xmin, xmax, ymin, ymax, zmin, zmax))."""
    with open(path, "rb") as f:
        f.read(80)
        count_bytes = f.read(4)
        if len(count_bytes) < 4:
            return [], None
        count = struct.unpack("<I", count_bytes)[0]
        if count == 0 or count > 2_000_000:
            return [], None

        triangles = []
        all_x, all_y, all_z = [], [], []

        for _ in range(count):
            f.read(12)  # normal
            tri = []
            for _ in range(3):
                data = f.read(12)
                if len(data) < 12:
                    break
                x, y, z = struct.unpack("<3f", data)
                tri.append((x, y, z))
                all_x.append(x)
                all_y.append(y)
                all_z.append(z)
            f.read(2)  # attr
            if len(tri) == 3:
                triangles.append(tri)

    if not triangles:
        return [], None

    bounds = (min(all_x), max(all_x), min(all_y), max(all_y), min(all_z), max(all_z))
    return triangles, bounds


def render_angle(triangles: list, bounds: tuple, output_path: Path,
                 elev: float = 25, azim: float = 45, title: str = ""):
    """Rend un angle de vue et sauvegarde en PNG."""
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    cx = (xmin + xmax) / 2
    cy = (ymin + ymax) / 2
    cz = (zmin + zmax) / 2
    scale = max(xmax - xmin, ymax - ymin, zmax - zmin)

    # Centrer les triangles
    centered = [
        [(x - cx, y - cy, z - cz) for (x, y, z) in tri]
        for tri in triangles
    ]

    fig = plt.figure(figsize=(7, 7), facecolor=BG_COLOR)
    ax = fig.add_subplot(111, projection="3d", facecolor=BG_COLOR)

    # Sous-échantillonner si trop de triangles (performance)
    display_tris = centered
    if len(centered) > 20000:
        step = len(centered) // 15000
        display_tris = centered[::step]

    poly = Poly3DCollection(display_tris, alpha=0.95, zsort="min")
    poly.set_facecolor(FACE_COLOR)
    poly.set_edgecolor(EDGE_COLOR)
    poly.set_linewidth(0.3)
    ax.add_collection3d(poly)

    r = scale * 0.55
    ax.set_xlim(-r, r)
    ax.set_ylim(-r, r)
    ax.set_zlim(-r * 0.4, r * 0.4)

    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()

    # Fond neutre propre
    ax.set_facecolor(BG_COLOR)
    fig.patch.set_facecolor(BG_COLOR)

    plt.tight_layout(pad=0)
    plt.savefig(str(output_path), dpi=180, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close(fig)


def render_stl(stl_path: Path, renders_dir: Path) -> list:
    """Rend 3 angles d'un STL. Retourne la liste des PNG créés."""
    slug = stl_path.stem
    print(f"  → Render: {slug}.stl")

    triangles, bounds = load_stl(stl_path)
    if not triangles or bounds is None:
        print(f"    [SKIP] STL invalide ou vide: {stl_path.name}")
        return []

    renders_dir.mkdir(parents=True, exist_ok=True)
    created = []

    angles = [
        ("front", 20, 0),
        ("oblique", 30, 45),
        ("top", 80, 0),
    ]

    for angle_name, elev, azim in angles:
        out = renders_dir / f"{slug}_{angle_name}.png"
        try:
            render_angle(triangles, bounds, out, elev=elev, azim=azim)
            created.append(out)
            print(f"    [OK] {out.name}")
        except Exception as e:
            print(f"    [ERREUR] {angle_name}: {e}")

    return created


def run_render():
    stl_dir_env = os.environ.get("STL_DIR", "")
    render_all = os.environ.get("RENDER_ALL", "0") == "1"

    if render_all:
        # Rend tous les produits stl_3d avec des fichiers STL
        stl_base = ROOT / "products" / "stl_3d"
        if not stl_base.exists():
            print("[Render] Aucun répertoire products/stl_3d/")
            return

        dirs = [d for d in stl_base.iterdir() if d.is_dir() and (d / "files").exists()]
        print(f"[Render] {len(dirs)} produits à rendre")
        for product_dir in dirs:
            _render_product(product_dir)
        return

    if stl_dir_env:
        product_dir = ROOT / stl_dir_env if not Path(stl_dir_env).is_absolute() else Path(stl_dir_env)
    else:
        # Dernier produit stl_3d avec des STL
        stl_base = ROOT / "products" / "stl_3d"
        if not stl_base.exists():
            print("[Render] products/stl_3d/ introuvable")
            sys.exit(1)
        dirs = sorted(
            [d for d in stl_base.iterdir() if d.is_dir() and (d / "files").exists()],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        if not dirs:
            print("[Render] Aucun produit stl_3d avec fichiers STL")
            sys.exit(0)
        product_dir = dirs[0]

    _render_product(product_dir)


def _render_product(product_dir: Path):
    files_dir = product_dir / "files"
    renders_dir = product_dir / "renders"

    stl_files = sorted(files_dir.glob("*.stl"))
    if not stl_files:
        print(f"[Render] Aucun STL dans {files_dir}")
        return

    print(f"[Render] {product_dir.name}: {len(stl_files)} STL à rendre")
    total_renders = 0

    for stl_path in stl_files:
        created = render_stl(stl_path, renders_dir)
        total_renders += len(created)

    print(f"[Render] ✓ {total_renders} PNG générés dans {renders_dir}")

    # Mise à jour du metadata.json
    meta_path = product_dir / "metadata.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["renders_count"] = total_renders
            meta["renders_dir"] = str(renders_dir.relative_to(ROOT))
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass


if __name__ == "__main__":
    run_render()
