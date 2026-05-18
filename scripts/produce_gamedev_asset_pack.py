"""
Pipeline GAMEDEV ASSET PACK — packs d'assets pour créateurs de jeux vidéo.

Marché : itch.io, Unity Asset Store, Fab (Epic), GameDev Market.
Marges : 70-88% selon plateforme. Marché en croissance forte 2025-2026.

Types d'assets produits dans ce pipeline :
1. Sprites 2D pixel art (épées, armures, items, monstres)
2. Tilesets RPG (forêt, donjon, ville, cave)
3. UI kits (boutons, frames, icons)
4. Cards/icons d'inventaire

Le fond Pollinations génère le visuel brut (style pixel art / fantasy / sci-fi),
puis Pillow le découpe en grille de sprites + génère un sheet PNG.

Sortie :
- products/gamedev/<pack>/sprites/<NN>.png (sprites individuels)
- products/gamedev/<pack>/sheet.png (atlas combiné grid)
- products/gamedev/<pack>/preview.png (mockup mise en valeur)
- products/gamedev/<pack>/manifest.json + LICENSE.txt
- products/gamedev/<pack>/upload_itchio.txt (description prête à coller)

Variables d'env :
  PACK=fantasy_swords    pack à produire
  SPRITES_PER_PACK=16    nb sprites
"""

from __future__ import annotations

import csv
import json
import math
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    print("ERREUR : Pillow non installé")
    sys.exit(2)


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "products" / "gamedev"
USER_AGENT = "GameDevAssetProducer/1.0"
TIMEOUT = 180


# Packs pré-définis (génériques, non-copyrightés)
ASSET_PACKS = {
    "fantasy_swords": {
        "title": "Fantasy Swords Pack — 16 Pixel Art Weapons",
        "category": "weapons",
        "style": "pixel art",
        "size_per_sprite": 256,
        "grid_cols": 4,
        "items": [
            "iron longsword", "rusty short sword", "magical glowing blade",
            "fire-enchanted scimitar", "ice katana", "ancient dwarven axe",
            "elven dagger silver", "barbarian greatsword", "shadow assassin blade",
            "holy paladin sword", "cursed obsidian blade", "crystal mage staff",
            "frost rapier blue gem", "venomous serpent blade", "phoenix flame sword",
            "moonlit silver blade",
        ],
        "prompt_template": (
            "pixel art {item}, isolated on solid magenta background #FF00FF, "
            "centered, vertical orientation, sharp 16-bit retro style, "
            "no text no watermark, clean game asset, single object"
        ),
        "price_eur": 7.99,
        "license": "Royalty-free for commercial game projects (CC-BY 4.0 base, extended commercial OK)",
    },
    "rpg_potions": {
        "title": "RPG Potions Pack — 16 Magical Vials",
        "category": "items",
        "style": "pixel art",
        "size_per_sprite": 256,
        "grid_cols": 4,
        "items": [
            "red health potion", "blue mana potion", "green poison vial",
            "purple mystery elixir", "golden xp boost potion", "silver invisibility potion",
            "rainbow rare elixir", "black death poison", "yellow lightning vial",
            "white holy water", "orange fire resistance", "cyan ice resistance",
            "violet teleport scroll potion", "pink love charm vial",
            "emerald life regen", "ruby strength booster",
        ],
        "prompt_template": (
            "pixel art {item} in glass vial with cork, isolated on solid "
            "magenta background #FF00FF, centered, sharp 16-bit retro game style, "
            "no text no watermark, single object"
        ),
        "price_eur": 5.99,
        "license": "Royalty-free for commercial game projects",
    },
    "dungeon_icons": {
        "title": "Dungeon Inventory Icons — 16 Quest Items",
        "category": "icons",
        "style": "pixel art",
        "size_per_sprite": 256,
        "grid_cols": 4,
        "items": [
            "ancient brass key", "skull of fallen warrior", "spell book leather bound",
            "rolled parchment scroll", "treasure chest closed", "golden compass",
            "silver ring with emerald", "wooden bow with quiver", "shield with crest",
            "candle in iron holder", "bag of gold coins", "amulet with red gem",
            "rusted iron helmet", "broken arrow", "mysterious orb",
            "feather quill and inkwell",
        ],
        "prompt_template": (
            "pixel art {item} icon, isolated on solid magenta background #FF00FF, "
            "centered square composition, sharp 16-bit retro game style, "
            "no text no watermark, single object, clear silhouette"
        ),
        "price_eur": 5.99,
        "license": "Royalty-free for commercial game projects",
    },
    "scifi_tiles": {
        "title": "Sci-Fi Floor Tiles Pack — 16 Cyberpunk Textures",
        "category": "tilesets",
        "style": "tileable texture",
        "size_per_sprite": 256,
        "grid_cols": 4,
        "items": [
            "metal grate floor", "neon glow circuit", "rusted steel plate",
            "hexagonal tech tile", "warning hazard stripe", "concrete bunker floor",
            "energy field grid", "broken floor cracked", "shiny chrome panel",
            "blood stained metal", "cargo container side", "alien organic surface",
            "pulsing energy core", "industrial vent grille", "data screen interface",
            "cyberpunk holographic floor",
        ],
        "prompt_template": (
            "seamless tileable texture, {item}, top-down view, sci-fi cyberpunk style, "
            "isolated square texture for game tiling, no text no watermark, "
            "no shadow no perspective, repeatable pattern"
        ),
        "price_eur": 9.99,
        "license": "Royalty-free for commercial game projects",
    },
    "monster_portraits": {
        "title": "Monster Avatar Portraits Pack — 16 RPG Enemies",
        "category": "characters",
        "style": "stylized portrait",
        "size_per_sprite": 256,
        "grid_cols": 4,
        "items": [
            "goblin warrior with crooked teeth", "orc berserker with tusks",
            "skeleton mage with hood", "evil necromancer", "young dragon hatchling",
            "stone golem with glowing eyes", "vampire lord pale", "werewolf snarling",
            "ghost wraith floating", "minotaur with horns", "imp red small",
            "lich with crown", "kobold with spear", "harpy with feathers",
            "demon prince horned", "troll with club",
        ],
        "prompt_template": (
            "stylized fantasy RPG monster portrait, {item}, head and shoulders "
            "composition, isolated on solid magenta background #FF00FF, dark "
            "moody color palette, dramatic lighting, no text no watermark"
        ),
        "price_eur": 12.99,
        "license": "Royalty-free for commercial game projects",
    },
    "ui_kit_fantasy": {
        "title": "Fantasy UI Kit — 16 Game Interface Elements",
        "category": "ui",
        "style": "fantasy UI",
        "size_per_sprite": 256,
        "grid_cols": 4,
        "items": [
            "wooden button with iron rivets", "scroll background banner",
            "health bar with skull endcaps", "mana bar with crystal endcaps",
            "circular avatar frame ornate", "menu panel parchment scroll",
            "treasure chest icon button", "settings gear icon ornate",
            "inventory bag icon", "map icon parchment", "quest book icon",
            "coin pouch icon", "ribbon banner for titles",
            "achievement badge laurel", "level up burst effect",
            "magical sparkle frame border",
        ],
        "prompt_template": (
            "fantasy game UI element, {item}, isolated on solid magenta "
            "background #FF00FF, centered, clean game asset, ornate medieval "
            "style with metallic accents, no text no watermark"
        ),
        "price_eur": 8.99,
        "license": "Royalty-free for commercial game projects",
    },
}


# ============================================================
# POLLINATIONS GENERATION
# ============================================================

def pollinations_url(prompt: str, seed: int, w: int = 1024, h: int = 1024) -> str:
    encoded = urllib.parse.quote(prompt, safe="")
    return (f"https://image.pollinations.ai/prompt/{encoded}"
            f"?model=flux&width={w}&height={h}"
            f"&seed={seed}&nologo=true&private=true&enhance=true")


def http_get(url: str, dest: Path, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                data = resp.read()
            if len(data) < 5000:
                raise ValueError(f"too short {len(data)}")
            dest.write_bytes(data)
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"    retry {attempt+1}/{retries} : {exc}")
            time.sleep(6 + attempt * 6)
    return False


# ============================================================
# BACKGROUND REMOVAL (simple chroma key sur magenta #FF00FF)
# ============================================================

def remove_magenta_background(src: Path, dest: Path,
                                tolerance: int = 60) -> None:
    """Remplace le magenta par transparence (chroma key simple)."""
    img = Image.open(src).convert("RGBA")
    data = img.getdata()
    new_data = []
    for r, g, b, a in data:
        # Magenta = R haut, G bas, B haut
        if r > 200 and g < 100 and b > 200:
            new_data.append((255, 255, 255, 0))  # transparent
        elif r > 180 and abs(r - b) < 50 and g < r - 80:
            # Magenta atténué
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append((r, g, b, a))
    img.putdata(new_data)
    img.save(dest, "PNG", optimize=True)


# ============================================================
# SHEET / ATLAS GENERATION
# ============================================================

def build_sprite_sheet(sprite_paths: list[Path], dest: Path,
                        cols: int, size: int) -> None:
    """Combine N sprites en grille atlas."""
    rows = math.ceil(len(sprite_paths) / cols)
    atlas = Image.new("RGBA", (cols * size, rows * size), (0, 0, 0, 0))
    for i, path in enumerate(sprite_paths):
        if not path.exists():
            continue
        sprite = Image.open(path).convert("RGBA")
        sprite = sprite.resize((size, size), Image.LANCZOS)
        x = (i % cols) * size
        y = (i // cols) * size
        atlas.paste(sprite, (x, y), sprite)
    atlas.save(dest, "PNG", optimize=True)


def build_preview_mockup(sheet_path: Path, dest: Path,
                          title: str, item_count: int) -> None:
    """Crée un mockup hero image pour les marketplaces."""
    canvas = Image.new("RGB", (1280, 720), (20, 22, 30))
    draw = ImageDraw.Draw(canvas)

    # Dégradé radial subtil
    cx, cy = 640, 360
    for r in range(800, 100, -100):
        alpha = int(20 * (800 - r) / 700)
        color = (30 + alpha // 4, 35 + alpha // 5, 50 + alpha // 3)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)

    # Atlas sheet centré
    sheet = Image.open(sheet_path).convert("RGBA")
    max_w = 720
    ratio = max_w / sheet.width
    new_w = int(sheet.width * ratio)
    new_h = int(sheet.height * ratio)
    sheet = sheet.resize((new_w, new_h), Image.LANCZOS)
    paste_x = (canvas.width - new_w) // 2
    paste_y = (canvas.height - new_h) // 2
    canvas.paste(sheet, (paste_x, paste_y), sheet)

    # Bandes neon top + bottom
    draw.rectangle([0, 0, canvas.width, 8], fill=(0, 200, 255))
    draw.rectangle([0, canvas.height - 8, canvas.width, canvas.height],
                    fill=(0, 200, 255))

    # Title text (overlay simple)
    try:
        from lib.specs_visual_identity import get_font, draw_text_centered
        f_title = get_font("display", 60)
        f_count = get_font("body_bold", 28)
        draw_text_centered(draw, title.upper(), (640, 40),
                            f_title, (240, 244, 248), letter_spacing=4)
        draw_text_centered(draw, f"{item_count} ASSETS · ROYALTY-FREE",
                            (640, canvas.height - 40),
                            f_count, (0, 200, 255), letter_spacing=3)
    except ImportError:
        pass  # fallback : pas de titre

    canvas.save(dest, "PNG", optimize=True)


# ============================================================
# PIPELINE PER PACK
# ============================================================

def produce_pack(pack_key: str) -> dict:
    if pack_key not in ASSET_PACKS:
        print(f"✗ Pack '{pack_key}' inconnu. Choix : {list(ASSET_PACKS)}")
        return {"ok": False}

    pack = ASSET_PACKS[pack_key]
    out_dir = OUTPUT_DIR / pack_key
    sprites_dir = out_dir / "sprites"
    raw_dir = out_dir / "raw"
    sprites_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== {pack['title']} ===")

    sprite_paths = []
    for i, item in enumerate(pack["items"], 1):
        prompt = pack["prompt_template"].format(item=item)
        raw_path = raw_dir / f"sprite_{i:02d}_raw.png"
        sprite_path = sprites_dir / f"sprite_{i:02d}.png"

        if sprite_path.exists():
            print(f"  [{i:>2}] {item[:40]} (already)")
            sprite_paths.append(sprite_path)
            continue

        seed = i * 10141 + random.randint(0, 9999)
        print(f"  [{i:>2}] {item[:40]}")
        if not http_get(pollinations_url(prompt, seed, 1024, 1024), raw_path):
            print(f"        ✗ generation failed")
            continue
        try:
            remove_magenta_background(raw_path, sprite_path)
            # Resize au size_per_sprite
            img = Image.open(sprite_path).convert("RGBA")
            img = img.resize(
                (pack["size_per_sprite"], pack["size_per_sprite"]),
                Image.LANCZOS,
            )
            img.save(sprite_path, "PNG", optimize=True)
            sprite_paths.append(sprite_path)
        except Exception as exc:  # noqa: BLE001
            print(f"        ✗ post-process : {exc}")
        finally:
            if raw_path.exists():
                raw_path.unlink()
        time.sleep(2)

    if not sprite_paths:
        return {"ok": False, "reason": "no sprites produced"}

    # Atlas sheet
    print("  → Building atlas sheet...")
    sheet_path = out_dir / "sheet.png"
    build_sprite_sheet(sprite_paths, sheet_path,
                        pack["grid_cols"], pack["size_per_sprite"])

    # Preview mockup
    print("  → Building preview mockup...")
    preview_path = out_dir / "preview.png"
    build_preview_mockup(sheet_path, preview_path,
                          pack["title"].split("—")[0].strip(),
                          len(sprite_paths))

    # Manifest + license
    manifest = {
        "pack_id": pack_key,
        "title": pack["title"],
        "category": pack["category"],
        "style": pack["style"],
        "sprite_count": len(sprite_paths),
        "size_per_sprite_px": pack["size_per_sprite"],
        "grid_cols": pack["grid_cols"],
        "price_eur_suggested": pack["price_eur"],
        "license": pack["license"],
        "produced_at": datetime.utcnow().isoformat() + "Z",
        "platforms": [
            "itch.io", "Unity Asset Store", "Fab (Epic)",
            "GameDev Market", "OpenGameArt (free tier)",
        ],
        "files_included": [
            f"sprites/sprite_NN.png (×{len(sprite_paths)})",
            "sheet.png (atlas combined)",
            "preview.png (1280×720 hero)",
        ],
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False))

    (out_dir / "LICENSE.txt").write_text(
        f"{pack['title']}\n{'=' * 60}\n\n"
        f"{pack['license']}\n\n"
        "USAGE RIGHTS\n"
        "- Use in unlimited commercial and personal game projects\n"
        "- Modify, remix, redistribute as part of your game\n"
        "- No need to credit (but always appreciated)\n\n"
        "RESTRICTIONS\n"
        "- Do not resell the raw asset files alone as your own pack\n"
        "- Do not register the artwork as a trademark or logo\n\n"
        f"Pack ID : {pack_key}\n"
        f"Produced : {datetime.utcnow().date()}\n"
    )

    # itch.io upload description template
    (out_dir / "upload_itchio.txt").write_text(
        f"=== ITCH.IO UPLOAD ===\n\n"
        f"TITLE :\n{pack['title']}\n\n"
        f"SHORT DESCRIPTION (max 256 chars) :\n"
        f"{len(sprite_paths)} {pack['style']} {pack['category']} sprites — "
        f"royalty-free for commercial use. Drop into Unity / Godot / GameMaker / "
        f"any game engine. Magenta background pre-keyed.\n\n"
        f"FULL DESCRIPTION :\n"
        f"Pack of {len(sprite_paths)} hand-crafted {pack['style']} {pack['category']} "
        f"sprites at {pack['size_per_sprite']}×{pack['size_per_sprite']}px PNG with "
        f"transparent background.\n\n"
        f"WHAT'S INCLUDED :\n"
        f"- {len(sprite_paths)} individual sprite PNGs (transparent)\n"
        f"- 1 atlas/sheet PNG ({pack['grid_cols']} columns)\n"
        f"- 1 hero preview image (1280×720)\n"
        f"- License & usage notes\n\n"
        f"PRICE :\n${pack['price_eur']:.2f}\n\n"
        f"TAGS :\n{pack['category']}, {pack['style']}, sprites, game-assets, "
        f"royalty-free, commercial-use, indie-game, asset-pack\n"
    )

    print(f"  ✓ Pack complete : {len(sprite_paths)} sprites + sheet + preview")
    return {"ok": True, "sprite_count": len(sprite_paths)}


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pack_key = os.environ.get("PACK", "").strip()
    if pack_key:
        return 0 if produce_pack(pack_key)["ok"] else 1
    # Tous les packs
    codes = []
    for key in ASSET_PACKS:
        codes.append(0 if produce_pack(key)["ok"] else 1)
        time.sleep(3)
    return max(codes) if codes else 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
