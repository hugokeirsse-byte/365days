#!/usr/bin/env python3
"""
Pipeline STL OpenSCAD — génère de vrais fichiers STL avec texte gravé.

Chaque variante a un texte RÉELLEMENT gravé dans la géométrie 3D via OpenSCAD.
Contrairement à l'ancienne version numpy-stl, les variantes sont physiquement
distinctes — le texte est visible et tactile sur l'objet imprimé.

Variables d'env :
  STL_DIR    — chemin du produit (ex: products/stl_3d/stl_2026-05-27_bookmark_cottagecore)
  OPENSCAD   — chemin vers openscad (défaut: openscad)
  MAX_VARIANTS — limite le nombre de variantes générées (défaut: toutes)
"""

import csv
import json
import math
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ============================================================
# TEMPLATES OPENSCAD — texte VRAIMENT gravé dans la géométrie
# ============================================================

SCAD_BOOKMARK = """\
// Bookmark — {text}
// 365days STL Pipeline — OpenSCAD production
TEXT = "{text}";
FONT = "{font}";
W = {width};
H = {height};
T = {thickness};
R = {corner_radius};
HOLE_R = {hole_radius};
TXT_SZ = {text_size};
ENGRAVE = {engrave_depth};
$fn = 48;

difference() {{
    // Corps principal arrondi
    linear_extrude(height=T) {{
        offset(r=R) square([W-2*R, H-2*R], center=true);
    }}
    // Trou ruban en haut
    translate([0, H/2-10, -0.1])
        cylinder(h=T+0.2, r=HOLE_R);
    // Texte gravé au centre
    translate([0, -8, T-ENGRAVE])
        linear_extrude(height=ENGRAVE+0.1)
            text(TEXT, size=TXT_SZ, font=FONT, halign="center", valign="center");
    // Groove décoratif (cadre)
    translate([0, 0, T-0.35]) difference() {{
        linear_extrude(height=0.4) offset(r=R) square([W-2*R, H-2*R], center=true);
        linear_extrude(height=0.4) offset(r=R) square([W-2*R-3.5, H-2*R-3.5], center=true);
    }}
}}
"""

SCAD_KEYCHAIN = """\
// Keychain — {text}
// 365days STL Pipeline — OpenSCAD production
TEXT = "{text}";
FONT = "{font}";
W = {width};
H = {height};
T = {thickness};
R = {corner_radius};
HOLE_R = {hole_radius};
TXT_SZ = {text_size};
ENGRAVE = {engrave_depth};
$fn = 48;

difference() {{
    // Corps ovale arrondi
    linear_extrude(height=T) {{
        offset(r=R) square([W-2*R, H-2*R], center=true);
    }}
    // Trou anneau à gauche
    translate([-W/2+6, 0, -0.1])
        cylinder(h=T+0.2, r=HOLE_R);
    // Texte gravé (décalé à droite du trou)
    translate([3, 0, T-ENGRAVE])
        linear_extrude(height=ENGRAVE+0.1)
            text(TEXT, size=TXT_SZ, font=FONT, halign="center", valign="center");
}}
"""

SCAD_COASTER = """\
// Coaster — {text}
// 365days STL Pipeline — OpenSCAD production
TEXT = "{text}";
FONT = "{font}";
D = {diameter};
T = {thickness};
BORDER = {border_width};
TXT_SZ = {text_size};
ENGRAVE = {engrave_depth};
$fn = 64;

difference() {{
    // Disque principal
    cylinder(h=T, r=D/2);
    // Zone centrale en creux (pose de la tasse)
    translate([0, 0, T-ENGRAVE*2])
        cylinder(h=ENGRAVE*2+0.1, r=D/2-BORDER);
    // Texte gravé dans la zone centrale
    translate([0, 0, T-ENGRAVE])
        linear_extrude(height=ENGRAVE+0.1)
            text(TEXT, size=TXT_SZ, font=FONT, halign="center", valign="center");
}}
"""

SCAD_DOOR_PLATE = """\
// Door plate — {text}
// 365days STL Pipeline — OpenSCAD production
TEXT = "{text}";
FONT = "{font}";
W = {width};
H = {height};
T = {thickness};
R = {corner_radius};
VIS_R = {screw_radius};
TXT_SZ = {text_size};
ENGRAVE = {engrave_depth};
$fn = 32;

difference() {{
    // Corps
    linear_extrude(height=T) {{
        offset(r=R) square([W-2*R, H-2*R], center=true);
    }}
    // Trous de vis (2x)
    translate([-W/2+7, 0, -0.1]) cylinder(h=T+0.2, r=VIS_R);
    translate([ W/2-7, 0, -0.1]) cylinder(h=T+0.2, r=VIS_R);
    // Chanfrein pour tête de vis
    translate([-W/2+7, 0, T-1.5]) cylinder(h=1.6, r1=VIS_R*2, r2=VIS_R);
    translate([ W/2-7, 0, T-1.5]) cylinder(h=1.6, r1=VIS_R*2, r2=VIS_R);
    // Texte gravé au centre
    translate([0, 0, T-ENGRAVE])
        linear_extrude(height=ENGRAVE+0.1)
            text(TEXT, size=TXT_SZ, font=FONT, halign="center", valign="center");
    // Groove décoratif
    translate([0, 0, T-0.3]) difference() {{
        linear_extrude(height=0.4) offset(r=R) square([W-2*R, H-2*R], center=true);
        linear_extrude(height=0.4) offset(r=R) square([W-2*R-3, H-2*R-3], center=true);
    }}
}}
"""

SCAD_PLANT_MARKER = """\
// Plant marker — {text}
// 365days STL Pipeline — OpenSCAD production
TEXT = "{text}";
FONT = "{font}";
W = {width};
PANEL_H = {panel_height};
STAKE_H = {stake_height};
T = {thickness};
TXT_SZ = {text_size};
ENGRAVE = {engrave_depth};
$fn = 16;

union() {{
    // Panneau d'affichage
    difference() {{
        translate([0, STAKE_H, 0])
            linear_extrude(height=T)
                square([W, PANEL_H], center=true);
        // Texte gravé sur le panneau
        translate([0, STAKE_H, T-ENGRAVE])
            linear_extrude(height=ENGRAVE+0.1)
                text(TEXT, size=TXT_SZ, font=FONT, halign="center", valign="center");
    }}
    // Tige verticale
    linear_extrude(height=T)
        square([6, STAKE_H + PANEL_H/2], center=false);
    // Pointe
    translate([3, -10, 0])
        linear_extrude(height=T)
            polygon([[0,0], [-5,10], [5,10]]);
}}
"""

TEMPLATES = {
    "bookmark": SCAD_BOOKMARK,
    "keychain": SCAD_KEYCHAIN,
    "coaster": SCAD_COASTER,
    "door_plate": SCAD_DOOR_PLATE,
    "plant_marker": SCAD_PLANT_MARKER,
}


# ============================================================
# PARAMÈTRES PAR TYPE DE PRODUIT
# ============================================================

DEFAULT_SPECS = {
    "bookmark": {
        "width": 55, "height": 115, "thickness": 3,
        "corner_radius": 5, "hole_radius": 2.8, "engrave_depth": 0.8,
        "font": "Liberation Sans:style=Bold",
        "text_area_width": 44,
    },
    "keychain": {
        "width": 50, "height": 28, "thickness": 3,
        "corner_radius": 8, "hole_radius": 2.5, "engrave_depth": 0.8,
        "font": "Liberation Sans:style=Bold",
        "text_area_width": 35,
    },
    "coaster": {
        "diameter": 92, "thickness": 4, "border_width": 4,
        "engrave_depth": 1.0,
        "font": "Liberation Sans:style=Bold",
        "text_area_width": 70,
    },
    "door_plate": {
        "width": 110, "height": 32, "thickness": 4,
        "corner_radius": 3, "screw_radius": 2.0, "engrave_depth": 1.0,
        "font": "Liberation Sans:style=Bold",
        "text_area_width": 90,
    },
    "plant_marker": {
        "width": 52, "panel_height": 26, "stake_height": 65, "thickness": 2.5,
        "engrave_depth": 0.6,
        "font": "Liberation Sans:style=Bold",
        "text_area_width": 44,
    },
}


def compute_text_size(text: str, area_width_mm: float, min_size: float = 5.0, max_size: float = 12.0) -> float:
    """Calcule la taille de texte optimale pour tenir dans la zone."""
    chars = len(text)
    if chars == 0:
        return max_size
    # Largeur d'un caractère ≈ 0.6 × size pour Liberation Sans Bold
    estimated = area_width_mm / (chars * 0.60)
    return round(max(min_size, min(max_size, estimated)), 1)


def sanitize_scad_text(text: str) -> str:
    """Échappe les caractères spéciaux pour OpenSCAD."""
    return text.replace('"', "'").replace('\\', '/').replace('\n', ' ').strip()


def build_scad_params(product_type: str, text: str, spec_override: dict) -> dict:
    """Construit les paramètres SCAD à partir du type et du texte."""
    spec = {**DEFAULT_SPECS.get(product_type, {}), **spec_override}
    text_size = compute_text_size(text, spec.get("text_area_width", 40))
    params = {"text": sanitize_scad_text(text), "text_size": text_size}
    params.update({k: v for k, v in spec.items() if k != "text_area_width"})
    return params


def generate_scad(product_type: str, text: str, spec_override: dict) -> str:
    """Génère le contenu d'un fichier .scad pour une variante."""
    template = TEMPLATES.get(product_type)
    if not template:
        raise ValueError(f"Type inconnu: {product_type}. Disponibles: {list(TEMPLATES)}")
    params = build_scad_params(product_type, text, spec_override)
    return template.format(**params)


def run_openscad(scad_path: Path, stl_path: Path, openscad_bin: str = "openscad") -> bool:
    """Appelle OpenSCAD pour convertir .scad → .stl."""
    cmd = [openscad_bin, "--export-format", "stl", "-o", str(stl_path), str(scad_path)]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            print(f"  [SCAD ERROR] {scad_path.name}: {result.stderr[:200]}")
            return False
        return True
    except FileNotFoundError:
        print(f"  [ERREUR] OpenSCAD introuvable: '{openscad_bin}'")
        print("  → Installer: sudo apt-get install openscad")
        return False
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] OpenSCAD trop lent pour {scad_path.name}")
        return False


def generate_metadata(cdc: dict, out_dir: Path, variantes_produites: list):
    """Génère metadata.json et upload_list.csv pour Cults3D."""
    listing = cdc.get("listing_cults3d", {})
    concept = cdc.get("concept", {})

    metadata = {
        "stl_id": cdc.get("stl_id", ""),
        "date_production": date.today().isoformat(),
        "titre": listing.get("titre_listing", concept.get("titre", "")),
        "description": listing.get("description_longue", ""),
        "tags": listing.get("tags", []),
        "categorie": listing.get("categorie", ""),
        "licence": listing.get("licence", "CC BY-NC-ND"),
        "type_produit": concept.get("type_produit", ""),
        "niche": concept.get("niche", ""),
        "theme": concept.get("theme", ""),
        "nombre_variantes": len(variantes_produites),
        "variantes": variantes_produites,
        "print_settings": cdc.get("spec_openscad", {}).get("print_settings", {}),
        "gate_cdc": cdc.get("gate_cdc", ""),
    }

    meta_path = out_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [OK] metadata.json → {meta_path}")

    # CSV pour upload Cults3D
    csv_path = out_dir / "upload_list.csv"
    files_dir = out_dir / "files"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["slug", "texte", "fichier_stl", "prix_usd", "statut"])
        for v in variantes_produites:
            writer.writerow([
                v["slug"],
                v["texte"],
                str(files_dir / f"{v['slug']}.stl"),
                v.get("prix_cults3d_usd", 2.50),
                v.get("statut", "produit"),
            ])
    print(f"  [OK] upload_list.csv → {csv_path}")


def run_production():
    stl_dir = os.environ.get("STL_DIR", "")
    openscad_bin = os.environ.get("OPENSCAD", "openscad")
    max_variants = int(os.environ.get("MAX_VARIANTS", "999"))

    if not stl_dir:
        # Cherche le dernier produit stl_3d avec gate approved
        stl_base = ROOT / "products" / "stl_3d"
        if not stl_base.exists():
            print("[STL Production] Aucun répertoire products/stl_3d/")
            sys.exit(1)
        candidates = [
            d for d in sorted(stl_base.iterdir())
            if d.is_dir() and (d / "cdc.json").exists()
        ]
        approved = [
            d for d in candidates
            if (lambda c: c.get("gate_cdc") == "approved" and not c.get("production_status"))(
                json.loads((d / "cdc.json").read_text(encoding="utf-8"))
            )
        ]
        if not approved:
            print("[STL Production] Aucun produit avec gate_cdc=approved. Hugo doit valider.")
            sys.exit(0)
        product_dir = approved[-1]
    else:
        product_dir = ROOT / stl_dir if not Path(stl_dir).is_absolute() else Path(stl_dir)

    cdc_path = product_dir / "cdc.json"
    if not cdc_path.exists():
        print(f"[STL Production] cdc.json introuvable dans {product_dir}")
        sys.exit(1)

    cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
    gate = cdc.get("gate_cdc", "pending")

    if gate == "pending":
        print(f"[STL Production] GATE = pending. Hugo doit valider {product_dir.name} avant production.")
        sys.exit(0)
    elif gate == "rejected":
        print(f"[STL Production] GATE = rejected. Produit annulé.")
        sys.exit(0)

    concept = cdc.get("concept", {})
    product_type = concept.get("type_produit", "bookmark")
    spec_override = cdc.get("spec_openscad", {}).get("dimensions_mm", {})

    variantes = cdc.get("variantes", [])[:max_variants]
    if not variantes:
        print("[STL Production] Aucune variante dans le CdC.")
        sys.exit(1)

    print(f"[STL Production] Produit: {product_dir.name}")
    print(f"[STL Production] Type: {product_type} | {len(variantes)} variantes")
    print(f"[STL Production] GATE: {gate} ✓ — démarrage production")

    scad_dir = product_dir / "scad"
    files_dir = product_dir / "files"
    scad_dir.mkdir(parents=True, exist_ok=True)
    files_dir.mkdir(parents=True, exist_ok=True)

    variantes_produites = []
    ok = 0
    fail = 0

    for v in variantes:
        slug = v.get("slug", "variant")
        texte = v.get("texte", "")
        if not texte:
            continue

        print(f"  → [{slug}] '{texte}'")
        scad_path = scad_dir / f"{slug}.scad"
        stl_path = files_dir / f"{slug}.stl"

        # Génération SCAD
        try:
            scad_content = generate_scad(product_type, texte, spec_override)
            scad_path.write_text(scad_content, encoding="utf-8")
        except Exception as e:
            print(f"  [ERREUR] SCAD génération {slug}: {e}")
            fail += 1
            continue

        # Compilation STL
        success = run_openscad(scad_path, stl_path, openscad_bin)
        if success and stl_path.exists() and stl_path.stat().st_size > 1000:
            ok += 1
            variantes_produites.append({
                **v,
                "stl_path": str(stl_path.relative_to(ROOT)),
                "stl_size_bytes": stl_path.stat().st_size,
                "statut": "produit",
            })
            print(f"  [OK] {slug}.stl ({stl_path.stat().st_size // 1024} KB)")
        else:
            fail += 1
            variantes_produites.append({**v, "statut": "echec"})

    print(f"\n[STL Production] ✓ {ok} STL générés | {fail} échecs")

    if ok > 0:
        generate_metadata(cdc, product_dir, variantes_produites)
        # Update cdc.json with production status
        cdc["production_status"] = {
            "date": date.today().isoformat(),
            "stl_ok": ok,
            "stl_fail": fail,
            "gate_production": "done" if fail == 0 else "partial",
        }
        cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[STL Production] → {product_dir}")
    print("[STL Production] Prochaine étape: render_stl_matplotlib.py → audit")


if __name__ == "__main__":
    run_production()
