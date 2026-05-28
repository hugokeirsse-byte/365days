#!/usr/bin/env python3
"""
Production Godot Assets depuis CdC validé — gate_cdc=approved requis.

Types gérés :
  sprite_pack / ui_kit / tileset → images via Pollinations + Pillow resize
  shader_pack / addon / game_template → code GDScript/GLSL via LLM

Produit la structure de dossiers attendue par Godot 4 :
  characters/ environment/ ui/ effects/ demo/ shaders/ addons/

Variables d'env :
  GODOT_DIR — chemin du produit (products/godot_assets/{slug})
              si absent, auto-détecte le dernier approuvé
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.lib.brain_utils import llm_call

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("[Godot] Pillow non disponible — images sans post-traitement")

# Tailles cibles par type
TARGET_SIZES = {
    "sprite_pack": (64, 64),
    "ui_kit": (256, 256),
    "tileset": (512, 512),   # tileset complet, sera découpé
}

# Pollinations: taille de génération (plus grand = meilleure qualité initiale)
GEN_SIZE = (512, 512)


def find_approved_godot() -> Path | None:
    base = ROOT / "products" / "godot_assets"
    if not base.exists():
        return None
    for d in sorted(base.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        cdc_path = d / "cdc.json"
        if not cdc_path.exists():
            continue
        try:
            cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
            if cdc.get("gate_cdc") == "approved" and not cdc.get("production_status"):
                return d
        except Exception:
            continue
    return None


def download_image(prompt: str, out_path: Path, width: int = 512, height: int = 512) -> bool:
    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}&nologo=true&model=flux"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = resp.read()
        out_path.write_bytes(data)
        return True
    except Exception as e:
        print(f"    ✗ Download: {e}")
        return False


def process_sprite(raw_path: Path, out_path: Path, size: tuple[int, int]):
    if not HAS_PILLOW:
        raw_path.rename(out_path)
        return
    img = Image.open(raw_path).convert("RGBA")
    img = img.resize(size, Image.LANCZOS)
    # Remove near-white background → transparent (for sprites)
    data = img.getdata()
    new_data = []
    for r, g, b, a in data:
        if r > 230 and g > 230 and b > 230:
            new_data.append((r, g, b, 0))
        else:
            new_data.append((r, g, b, a))
    img.putdata(new_data)
    img.save(out_path, "PNG")


def process_ui(raw_path: Path, out_path: Path, size: tuple[int, int]):
    if not HAS_PILLOW:
        raw_path.rename(out_path)
        return
    img = Image.open(raw_path).convert("RGBA")
    img = img.resize(size, Image.LANCZOS)
    img.save(out_path, "PNG")


def build_sprite_prompt(theme: str, categorie: str, exemple: str) -> str:
    return (
        f"pixel art sprite, {exemple}, {theme} style, {categorie}, "
        f"game asset, transparent background, clean edges, colorful, "
        f"top-down RPG style, 64x64 pixel art"
    )


def build_ui_prompt(theme: str, element: str) -> str:
    return (
        f"UI game element, {element}, {theme} interface design, "
        f"clean vector style, game UI component, white background, "
        f"professional game asset, high quality"
    )


def build_tileset_prompt(theme: str) -> str:
    return (
        f"tileset texture sheet, {theme}, game tiles, top-down RPG, "
        f"pixel art tileset, seamless tiles, various terrain types, "
        f"colorful game assets, clean grid layout"
    )


def produce_image_assets(godot_dir: Path, cdc: dict) -> dict:
    asset_type = cdc.get("type_asset", "sprite_pack")
    concept = cdc.get("concept", {})
    theme = concept.get("theme", "fantasy")
    contenu = cdc.get("contenu_pack", [])
    spec = cdc.get("spec_production", {})
    structure = spec.get("structure_dossiers", {})

    target_size = TARGET_SIZES.get(asset_type, (64, 64))
    generated = 0
    failed = []

    for folder_rel, description in structure.items():
        folder = godot_dir / folder_rel.rstrip("/")
        if folder_rel.rstrip("/") in ("demo", "ui") and asset_type == "sprite_pack":
            continue
        folder.mkdir(parents=True, exist_ok=True)

    raw_dir = godot_dir / "_raw"
    raw_dir.mkdir(exist_ok=True)

    for cat_info in contenu:
        categorie = cat_info.get("categorie", "assets")
        nb = int(cat_info.get("nb", 5))
        format_str = cat_info.get("format", "PNG 64x64px")
        exemples = cat_info.get("exemples", [])

        # Map categorie → subfolder
        folder_map = {
            "character": "characters", "personnage": "characters", "hero": "characters",
            "environment": "environment", "décor": "environment", "background": "environment",
            "ui": "ui", "interface": "ui", "button": "ui",
            "effect": "effects", "effet": "effects", "particle": "effects",
        }
        subfolder = "characters"
        for key, val in folder_map.items():
            if key in categorie.lower():
                subfolder = val
                break

        out_dir = godot_dir / subfolder
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"  [{categorie}] {nb} assets → {subfolder}/")

        for i in range(nb):
            slug = categorie.lower().replace(" ", "_")[:20]
            out_name = f"{slug}_{i+1:02d}.png"
            out_path = out_dir / out_name

            if out_path.exists():
                generated += 1
                continue

            exemple = exemples[i % len(exemples)] if exemples else f"{categorie} {i+1}"

            if asset_type == "sprite_pack":
                prompt = build_sprite_prompt(theme, categorie, exemple)
            elif asset_type == "ui_kit":
                prompt = build_ui_prompt(theme, exemple)
            else:
                prompt = build_tileset_prompt(theme)

            raw_path = raw_dir / f"{slug}_{i+1:02d}_raw.png"
            ok = download_image(prompt, raw_path, *GEN_SIZE)

            if not ok:
                failed.append(out_name)
                time.sleep(1)
                continue

            try:
                if asset_type in ("sprite_pack",):
                    process_sprite(raw_path, out_path, target_size)
                else:
                    process_ui(raw_path, out_path, target_size)
                generated += 1
                print(f"    [{i+1}/{nb}] {out_name} ✓")
            except Exception as e:
                print(f"    [{i+1}/{nb}] ✗ {e}")
                failed.append(out_name)

            time.sleep(0.5)

    return {"generated": generated, "failed": failed}


def generate_gdscript_code(cdc: dict, asset_type: str) -> dict:
    concept = cdc.get("concept", {})
    theme = concept.get("theme", "")
    titre = concept.get("titre", "")
    contenu = cdc.get("contenu_pack", [])

    if asset_type == "shader_pack":
        descriptions = [f"{c.get('categorie')}: {c.get('description')}" for c in contenu]
        system_prompt = """Tu es un expert Godot 4 et GLSL. Tu génères des shaders .gdshader fonctionnels.
FORMAT : JSON avec une liste de shaders, chacun ayant "nom", "description", "code_gdshader".
Le code doit être du GLSL valide pour Godot 4 (shader_type canvas_item ou spatial).
JSON uniquement."""
        user_prompt = f"""Génère {len(descriptions)} shaders Godot 4 pour le pack "{titre}" (thème: {theme}).
Shaders demandés:
{chr(10).join(descriptions)}

Chaque shader doit être unique, fonctionnel, et bien commenté.
Format JSON: {{"shaders": [{{"nom": "...", "description": "...", "code_gdshader": "shader_type canvas_item;\\n..."}}]}}"""

        response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.7, max_tokens=6000)
        if not response:
            return {}
        clean = response.strip()
        if clean.startswith("```"):
            parts = clean.split("```")
            clean = parts[1][4:] if parts[1].startswith("json") else parts[1]
        try:
            return json.loads(clean.strip())
        except Exception:
            return {}

    elif asset_type == "addon":
        system_prompt = """Tu es un expert Godot 4 GDScript. Tu génères des plugins/addons Godot 4 complets.
FORMAT : JSON avec "plugin_cfg", "main_script", "fichiers_supplementaires" (liste de {nom, contenu}).
JSON uniquement."""
        user_prompt = f"""Génère le code complet pour l'addon Godot 4 "{titre}" (thème: {theme}).
Description: {concept.get("description", "")}
Format: {{"plugin_cfg": "...", "main_script": "...", "fichiers_supplementaires": [{{"nom": "...", "contenu": "..."}}]}}"""

        response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.6, max_tokens=8000)
        if not response:
            return {}
        clean = response.strip()
        if clean.startswith("```"):
            parts = clean.split("```")
            clean = parts[1][4:] if parts[1].startswith("json") else parts[1]
        try:
            return json.loads(clean.strip())
        except Exception:
            return {}

    elif asset_type == "game_template":
        system_prompt = """Tu es un expert Godot 4 GDScript. Tu génères des templates de jeux complets.
FORMAT : JSON avec "project_godot", "scenes" (liste de {nom, contenu_tscn}), "scripts" (liste de {nom, contenu_gd}).
JSON uniquement."""
        user_prompt = f"""Génère le template Godot 4 complet "{titre}" (thème: {theme}).
Description: {concept.get("description", "")}
Format: {{"project_godot": "...", "scenes": [{{"nom": "Main.tscn", "contenu_tscn": "..."}}], "scripts": [{{"nom": "Player.gd", "contenu_gd": "..."}}]}}"""

        response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.6, max_tokens=8000)
        if not response:
            return {}
        clean = response.strip()
        if clean.startswith("```"):
            parts = clean.split("```")
            clean = parts[1][4:] if parts[1].startswith("json") else parts[1]
        try:
            return json.loads(clean.strip())
        except Exception:
            return {}

    return {}


def save_code_assets(godot_dir: Path, asset_type: str, code_data: dict) -> int:
    saved = 0

    if asset_type == "shader_pack":
        shaders_dir = godot_dir / "shaders"
        shaders_dir.mkdir(exist_ok=True)
        for shader in code_data.get("shaders", []):
            name = shader.get("nom", f"shader_{saved+1}").replace(" ", "_").lower()
            if not name.endswith(".gdshader"):
                name += ".gdshader"
            path = shaders_dir / name
            path.write_text(shader.get("code_gdshader", ""), encoding="utf-8")
            print(f"  ✓ {name}")
            saved += 1

    elif asset_type == "addon":
        addons_dir = godot_dir / "addons"
        addon_name = godot_dir.name.replace("-", "_").replace(" ", "_")[:30]
        plugin_dir = addons_dir / addon_name
        plugin_dir.mkdir(parents=True, exist_ok=True)

        plugin_cfg = code_data.get("plugin_cfg", f"[plugin]\nname=\"{addon_name}\"\ndescription=\"\"\nauthor=\"365days\"\nversion=\"1.0\"\nscript=\"plugin.gd\"")
        (plugin_dir / "plugin.cfg").write_text(plugin_cfg, encoding="utf-8")

        main_script = code_data.get("main_script", "@tool\nextends EditorPlugin\n\nfunc _enter_tree():\n\tpass\n\nfunc _exit_tree():\n\tpass\n")
        (plugin_dir / "plugin.gd").write_text(main_script, encoding="utf-8")

        for extra in code_data.get("fichiers_supplementaires", []):
            fname = extra.get("nom", "extra.gd")
            (plugin_dir / fname).write_text(extra.get("contenu", ""), encoding="utf-8")
            saved += 1
        saved += 2  # plugin.cfg + plugin.gd
        print(f"  ✓ addons/{addon_name}/ ({saved} fichiers)")

    elif asset_type == "game_template":
        proj = code_data.get("project_godot", "")
        if proj:
            (godot_dir / "project.godot").write_text(proj, encoding="utf-8")
            saved += 1

        scenes_dir = godot_dir / "scenes"
        scenes_dir.mkdir(exist_ok=True)
        for scene in code_data.get("scenes", []):
            fname = scene.get("nom", "Main.tscn")
            (scenes_dir / fname).write_text(scene.get("contenu_tscn", ""), encoding="utf-8")
            print(f"  ✓ scenes/{fname}")
            saved += 1

        scripts_dir = godot_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        for script in code_data.get("scripts", []):
            fname = script.get("nom", "Script.gd")
            (scripts_dir / fname).write_text(script.get("contenu_gd", ""), encoding="utf-8")
            print(f"  ✓ scripts/{fname}")
            saved += 1

    return saved


def generate_readme(godot_dir: Path, cdc: dict):
    concept = cdc.get("concept", {})
    asset_type = cdc.get("type_asset", "sprite_pack")
    listing = cdc.get("listing_itchio", {})

    readme = f"""# {concept.get("titre", godot_dir.name)}

**Type** : {asset_type} | **Thème** : {concept.get("theme", "?")}
**Compatibilité** : {concept.get("compatibilite", "Godot 4.x (4.2+)")}
**Assets** : {concept.get("nb_assets", "?")}

## Description

{concept.get("description", listing.get("description_courte", ""))}

## Contenu

"""
    for cat in cdc.get("contenu_pack", []):
        readme += f"- **{cat.get('categorie')}** × {cat.get('nb')} — {cat.get('description')} ({cat.get('format')})\n"

    readme += f"""
## Import dans Godot 4

1. Copier le dossier dans votre projet Godot 4
2. Dans Godot : FileSystem → glisser les assets dans votre scène
3. Voir la scène `demo/` pour des exemples d'utilisation

## Licence

{cdc.get("spec_production", {}).get("licence", "CC0 — Domaine public")}

## Itch.io

Prix : {listing.get("prix_usd", "?")} USD | Tags : {", ".join(listing.get("tags", [])[:5])}
"""
    (godot_dir / "README.md").write_text(readme, encoding="utf-8")


def run():
    godot_dir_env = os.environ.get("GODOT_DIR", "").strip()

    if godot_dir_env:
        godot_dir = ROOT / godot_dir_env
    else:
        godot_dir = find_approved_godot()

    if not godot_dir:
        print("[Godot] Aucun CdC approuvé trouvé dans products/godot_assets/")
        sys.exit(0)

    cdc_path = godot_dir / "cdc.json"
    if not cdc_path.exists():
        print(f"[Godot] cdc.json manquant: {cdc_path}")
        sys.exit(1)

    cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
    gate = cdc.get("gate_cdc", "pending")

    if gate == "pending":
        print(f"[Godot] GATE=PENDING — en attente validation Hugo.")
        sys.exit(0)
    if gate == "rejected":
        print("[Godot] GATE=REJECTED — production annulée.")
        sys.exit(0)

    asset_type = cdc.get("type_asset", "sprite_pack")
    concept = cdc.get("concept", {})
    titre = concept.get("titre", godot_dir.name)

    print(f"\n[Godot] Production: '{titre}' ({asset_type})")
    print(f"[Godot] Source: {godot_dir.name}")

    stats = {}

    if asset_type in ("sprite_pack", "ui_kit", "tileset"):
        print(f"\n[Godot] Génération images via Pollinations...")
        stats = produce_image_assets(godot_dir, cdc)

    elif asset_type in ("shader_pack", "addon", "game_template"):
        print(f"\n[Godot] Génération code via LLM...")
        code_data = generate_gdscript_code(cdc, asset_type)
        if code_data:
            saved = save_code_assets(godot_dir, asset_type, code_data)
            stats = {"generated": saved, "failed": []}
        else:
            print("[Godot] ✗ Génération LLM échouée")
            stats = {"generated": 0, "failed": ["LLM failed"]}

    generate_readme(godot_dir, cdc)

    cdc["production_status"] = {
        "date": str(__import__("datetime").date.today()),
        "assets_generes": stats.get("generated", 0),
        "assets_echoues": stats.get("failed", []),
    }
    cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[Godot] ✓ '{titre}' — {stats.get('generated', 0)} assets produits")
    print(f"[Godot] → {godot_dir}")
    print(f"[Godot] Prochaine étape: publier sur Itch.io ({cdc.get('listing_itchio', {}).get('prix_usd', '?')} USD)")


if __name__ == "__main__":
    run()
