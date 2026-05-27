#!/usr/bin/env python3
"""
Gestionnaire de file CdC — maintient 10 CdC en attente par vertical.

Règle : chaque vertical a toujours TARGET_PENDING CdC avec gate=pending.
- Hugo en approuve 1 → 1 nouveau CdC se génère automatiquement
- Hugo en rejette 3 → 3 nouveaux CdC se génèrent
- À tout moment : exactement TARGET_PENDING CdC disponibles à valider

Ce script tourne en cron (toutes les 4h) et vérifie les niveaux.
Il est aussi déclenché quand Hugo pousse une modification de cdc.json.

Variables d'env :
  VERTICAL     — coloring|stl|lowcontent|roman|all (défaut: all)
  TARGET       — nombre de CdC cibles par vertical (défaut: 10)
  MAX_PER_RUN  — max générés par vertical par run (défaut: 5)
  DRY_RUN      — si "1", affiche seulement sans générer
"""

import json
import os
import random
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGET_PENDING = int(os.environ.get("TARGET", "10"))
MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", "5"))
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

# ── Pools de thèmes — diversité garantie, pas de répétition ──────────────────

POOLS = {
    "coloring": [
        # (theme, audience)
        ("botanical_garden", "adult"),
        ("ocean_depths", "adult"),
        ("enchanted_forest", "adult"),
        ("mandala_sacred_geometry", "adult"),
        ("art_nouveau_florals", "adult"),
        ("japanese_zen_garden", "adult"),
        ("geometric_patterns", "adult"),
        ("fairy_tale_kingdom", "child"),
        ("gothic_dark_florals", "adult"),
        ("celestial_moon_stars", "adult"),
        ("mushroom_kingdom", "adult"),
        ("tropical_birds_paradise", "adult"),
        ("cat_portraits_whimsical", "adult"),
        ("vintage_botanical_herbs", "adult"),
        ("underwater_coral_reef", "adult"),
        ("fantasy_dragons", "adult"),
        ("cottage_garden_flowers", "adult"),
        ("sea_creatures_cute", "child"),
        ("dinosaurs_adventure", "child"),
        ("forest_animals", "child"),
        ("succulent_cacti", "adult"),
        ("butterfly_garden", "adult"),
        ("celtic_knotwork", "adult"),
        ("peacock_feathers", "adult"),
        ("wildflower_meadow", "adult"),
    ],
    "stl": [
        # (type_produit, niche)
        ("bookmark", "cottagecore"),
        ("keychain", "dnd"),
        ("coaster", "botanical"),
        ("door_plate", "minimalist"),
        ("plant_marker", "gardening"),
        ("bookmark", "witchy"),
        ("keychain", "booklover"),
        ("coaster", "coffee"),
        ("bookmark", "gaming"),
        ("plant_marker", "botanical"),
        ("keychain", "cottagecore"),
        ("coaster", "witchy"),
        ("door_plate", "dnd"),
        ("bookmark", "minimalist"),
        ("keychain", "seasonal"),
        ("coaster", "gaming"),
        ("bookmark", "pet_lover"),
        ("plant_marker", "witchy"),
        ("door_plate", "cottagecore"),
        ("keychain", "pet_lover"),
    ],
    "lowcontent": [
        # (type, theme)
        ("journal", "mindfulness"),
        ("planner", "productivity"),
        ("tracker", "fitness"),
        ("habit_tracker", "wellness"),
        ("gratitude_journal", "spirituality"),
        ("reading_log", "booklover"),
        ("journal", "travel"),
        ("tracker", "sourdough_baking"),
        ("planner", "gardening"),
        ("journal", "creativity"),
        ("tracker", "pet_health"),
        ("planner", "meal_prep"),
        ("journal", "pregnancy"),
        ("tracker", "budget"),
        ("journal", "camping"),
        ("planner", "study"),
        ("tracker", "bird_watching"),
        ("gratitude_journal", "cottagecore"),
        ("habit_tracker", "morning_routine"),
        ("journal", "anxiety_management"),
    ],
    "roman": [
        # (genre, sous_genre, langue)
        ("romance", "small_town", "en"),
        ("romance", "enemies_to_lovers", "en"),
        ("cozy_mystery", "cat_sleuth", "en"),
        ("romance", "second_chance", "en"),
        ("contemporary_fiction", "workplace_romance", "en"),
        ("romance", "fake_dating", "en"),
        ("mystery", "cozy_amateur_sleuth", "en"),
        ("romance", "grumpy_sunshine", "en"),
        ("paranormal_romance", "fated_mates", "en"),
        ("romance", "age_gap", "en"),
        ("cozy_mystery", "bakery", "en"),
        ("romance", "friends_to_lovers", "en"),
        ("contemporary_fiction", "women_fiction", "en"),
        ("romance", "sports", "en"),
        ("cozy_mystery", "bookshop", "en"),
    ],
    "jeux_societe": [
        # (type_jeu, theme, mecanique)
        ("card_game", "dark humor infirmières", "questions réponses"),
        ("party_game", "soirée entre amis adultes", "défis et gages"),
        ("board_game", "exploration fantasy medieval", "tile placement"),
        ("card_game", "dark humor profs de lycée", "bluffing"),
        ("educational", "apprentissage anglais enfants", "memory matching"),
        ("rpg_accessory", "donjon fantasy D&D compatible", "narration collaborative"),
        ("dice_game", "apéro entre amis", "push your luck"),
        ("card_game", "dark humor développeurs", "questions réponses"),
        ("party_game", "team building entreprise", "créativité collective"),
        ("board_game", "gestion de ferme cozy", "resource management"),
        ("card_game", "culture générale décalée", "trivia quiz"),
        ("educational", "tables de multiplication gamifiées", "jeu de rapidité"),
        ("party_game", "soirée filles bachelorette", "défis humoristiques"),
        ("rpg_accessory", "feuilles de personnage universelles", "système custom"),
        ("card_game", "dark humor pompiers", "questions réponses"),
        ("board_game", "escape room imprimable", "coopératif déduction"),
        ("dice_game", "voyage road trip", "collecte et scoring"),
        ("educational", "histoire de France enfants", "quiz progression"),
        ("party_game", "Noël famille multigénérationnel", "questions nostalgie"),
        ("card_game", "dark humor avocat juriste", "questions réponses"),
    ],
    "merch_design": [
        # (concept, style)
        ("world proverbs translated to english funny literal illustration", "flat colorful illustration"),
        ("dark humor nurses profession quotes", "bold typography minimal"),
        ("introverts survival guide relatable humor", "flat illustration pastel"),
        ("cat owners obsessed relatable humor", "cute flat illustration"),
        ("coffee addiction morning survival quotes", "retro bold typography"),
        ("bookworm bibliophile literary humor", "vintage illustration"),
        ("plant parent crazy obsession humor", "botanical flat illustration"),
        ("programmer developer dark humor coding", "minimal tech illustration"),
        ("teacher appreciation funny truth quotes", "bold colorful typography"),
        ("dog dad mom unconditional love humor", "cute flat illustration"),
        ("astrology zodiac signs relatable humor", "celestial illustration mystical"),
        ("mental health self care gentle reminders", "pastel watercolor soft"),
        ("running marathon motivation dark humor", "flat sport illustration"),
        ("hiking outdoor adventure nature quotes", "vintage national park style"),
        ("chef cook foodie dark humor kitchen", "retro illustration bold"),
        ("anxiety overthinking relatable memes", "cute illustration soft"),
        ("wine o clock friday celebration humor", "elegant script typography"),
        ("retired no boss freedom humor", "flat colorful illustration"),
        ("new parent sleep deprivation survival", "cute illustration pastel"),
        ("gym workout fitness dark humor motivation", "bold sport typography"),
        ("witch cottagecore magic autumn vibes", "mystical botanical illustration"),
        ("french phrases everyday life humor", "chic illustration minimalist"),
        ("sarcastic motivational anti-hustle quotes", "bold typography flat"),
        ("dungeons dragons gamer nerdy humor", "fantasy pixel illustration"),
        ("tattoo artist dark humour studio life", "bold graphic illustration"),
    ],
    "godot_assets": [
        # (type_asset, theme)
        ("sprite_pack", "fantasy medieval characters"),
        ("ui_kit", "clean minimal rpg interface"),
        ("tileset", "top-down dungeon pixel art"),
        ("sprite_pack", "cute animals farm cozy"),
        ("shader_pack", "neon cyberpunk glow effects"),
        ("sprite_pack", "space shooter enemies bullets"),
        ("ui_kit", "horror dark gothic interface"),
        ("tileset", "platformer jungle tropical"),
        ("addon", "dialogue system visual novel"),
        ("game_template", "endless runner mobile"),
        ("sprite_pack", "chibi fantasy heroes"),
        ("tileset", "overworld rpg grass forest"),
        ("shader_pack", "water fire earth effects"),
        ("ui_kit", "cozy pastel cute interface"),
        ("sprite_pack", "zombie apocalypse survival"),
        ("addon", "inventory system drag drop"),
        ("tileset", "sci-fi space station interior"),
        ("game_template", "top-down rpg starter"),
        ("sprite_pack", "magical girl anime style"),
        ("shader_pack", "pixel art retro crt effects"),
    ],
}

# ── Config par vertical ───────────────────────────────────────────────────────

CONFIGS = {
    "coloring": {
        "products_dir": "products/coloring_books",
        "cdc_script": "scripts/agent_coloring_cdc.py",
        "build_env": lambda t: {
            "COLORING_THEME": t[0],
            "COLORING_AUDIENCE": t[1],
            "COLORING_PAGES": "30",
        },
        "theme_key": lambda cdc: (
            cdc.get("concept", {}).get("theme_principal", ""),
            cdc.get("concept", {}).get("audience", "adult"),
        ),
    },
    "stl": {
        "products_dir": "products/stl_3d",
        "cdc_script": "scripts/agent_stl_cdc.py",
        "build_env": lambda t: {
            "STL_TYPE": t[0],
            "STL_NICHE": t[1],
            "STL_NB_VARIANTES": "15",
        },
        "theme_key": lambda cdc: (
            cdc.get("concept", {}).get("type_produit", ""),
            cdc.get("concept", {}).get("niche", ""),
        ),
    },
    "lowcontent": {
        "products_dir": "products/lowcontent_kdp",
        "cdc_script": "scripts/agent_cdc_lowcontent.py",
        "build_env": lambda t: {
            "LC_TYPE": t[0],
            "LC_THEME": t[1],
            "LC_AUDIENCE": "adults",
        },
        "theme_key": lambda cdc: (
            cdc.get("concept", {}).get("type", ""),
            cdc.get("concept", {}).get("theme", ""),
        ),
    },
    "jeux_societe": {
        "products_dir": "products/jeux_societe",
        "cdc_script": "scripts/agent_jeux_societe_cdc.py",
        "build_env": lambda t: {
            "JEU_TYPE": t[0],
            "JEU_THEME": t[1],
            "JEU_MECANIQUE": t[2],
            "JEU_LANGUE": "fr",
        },
        "theme_key": lambda cdc: (
            cdc.get("type_jeu", ""),
            cdc.get("concept", {}).get("theme", ""),
        ),
    },
    "roman": {
        "products_dir": "products/novels",
        "cdc_script": "scripts/agent_cdc_roman.py",
        "build_env": lambda t: {
            "ROMAN_GENRE": t[0],
            "ROMAN_SOUS_GENRE": t[1],
            "ROMAN_LANGUE": t[2],
        },
        "theme_key": lambda cdc: (
            cdc.get("concept", {}).get("genre_exact", ""),
            cdc.get("concept", {}).get("sous_genre", ""),
        ),
    },
    "merch_design": {
        "products_dir": "products/merch",
        "cdc_script": "scripts/agent_merch_design_cdc.py",
        "build_env": lambda t: {
            "MERCH_CONCEPT": t[0],
            "MERCH_STYLE": t[1],
            "MERCH_NB_DESIGNS": "30",
            "MERCH_LANGUE": "en",
        },
        "theme_key": lambda cdc: (
            cdc.get("concept_theme", {}).get("titre", ""),
        ),
    },
    "godot_assets": {
        "products_dir": "products/godot_assets",
        "cdc_script": "scripts/agent_godot_cdc.py",
        "build_env": lambda t: {
            "GODOT_TYPE": t[0],
            "GODOT_THEME": t[1],
            "GODOT_NB_ASSETS": "30",
        },
        "theme_key": lambda cdc: (
            cdc.get("type_asset", ""),
            cdc.get("concept", {}).get("theme", ""),
        ),
    },
}


def scan_pending(products_dir: Path, theme_key_fn) -> tuple[int, list]:
    """Compte les CdC en attente et retourne leurs thèmes (pour éviter doublons)."""
    if not products_dir.exists():
        return 0, []

    pending_count = 0
    pending_themes = []

    for d in products_dir.iterdir():
        if not d.is_dir():
            continue
        cdc_path = d / "cdc.json"
        if not cdc_path.exists():
            continue
        try:
            cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
            if cdc.get("gate_cdc") == "pending":
                pending_count += 1
                try:
                    pending_themes.append(theme_key_fn(cdc))
                except Exception:
                    pass
        except Exception:
            continue

    return pending_count, pending_themes


def pick_next_theme(pool: list, already_pending: list, already_used: list) -> tuple | None:
    """Choisit le prochain thème en évitant les doublons."""
    used_set = set(map(str, already_pending + already_used))
    candidates = [t for t in pool if str(t) not in used_set]

    if not candidates:
        # Pool épuisé — recommencer depuis le début avec la pool complète
        all_pending_set = set(map(str, already_pending))
        candidates = [t for t in pool if str(t) not in all_pending_set]

    if not candidates:
        return None

    return random.choice(candidates)


def run_cdc_generator(cdc_script: Path, env_vars: dict) -> bool:
    """Lance un générateur de CdC en subprocess."""
    env = os.environ.copy()
    env.update(env_vars)
    # Injection d'un ID unique pour éviter les collisions de dossiers
    today = date.today().isoformat()
    import time
    ts = str(int(time.time()))[-5:]
    for k in env_vars:
        if "ID" in k:
            env[k] = env_vars[k] + f"_{ts}"

    try:
        result = subprocess.run(
            [sys.executable, str(cdc_script)],
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(ROOT),
        )
        if result.returncode == 0:
            # Extraire le nom du produit généré
            for line in result.stdout.splitlines():
                if "CdC généré" in line or "→ products" in line:
                    print(f"    ✓ {line.strip()}")
                    break
            else:
                print(f"    ✓ CdC généré (gate=pending)")
            return True
        else:
            print(f"    ✗ Erreur: {result.stderr[:150]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"    ✗ Timeout (180s)")
        return False
    except Exception as e:
        print(f"    ✗ Exception: {e}")
        return False


def fill_queue(vertical_name: str, config: dict) -> int:
    """Remplit la file d'un vertical jusqu'à TARGET_PENDING. Retourne nb générés."""
    products_dir = ROOT / config["products_dir"]
    cdc_script = ROOT / config["cdc_script"]
    pool = POOLS[vertical_name]

    pending_count, pending_themes = scan_pending(products_dir, config["theme_key"])
    need = max(0, TARGET_PENDING - pending_count)
    to_generate = min(need, MAX_PER_RUN)

    print(f"\n[Queue] ── {vertical_name.upper()} ──")
    print(f"  Pending: {pending_count}/{TARGET_PENDING} | À générer: {to_generate}")

    if to_generate == 0:
        print(f"  ✓ File pleine ({pending_count} CdC en attente)")
        return 0

    if not cdc_script.exists():
        print(f"  ✗ Script manquant: {cdc_script}")
        return 0

    generated = 0
    used_this_run = []

    for i in range(to_generate):
        theme = pick_next_theme(pool, pending_themes, used_this_run)
        if theme is None:
            print(f"  ✗ Pool épuisé pour {vertical_name}")
            break

        env_vars = config["build_env"](theme)
        theme_str = " + ".join(str(t) for t in theme)
        print(f"  → Génération {i+1}/{to_generate}: {theme_str}")

        if DRY_RUN:
            print(f"    [DRY RUN] Serait généré avec: {env_vars}")
            generated += 1
            used_this_run.append(theme)
            continue

        success = run_cdc_generator(cdc_script, env_vars)
        if success:
            generated += 1
            used_this_run.append(theme)
            # Rescan pour mettre à jour pending_themes
            pending_count, pending_themes = scan_pending(products_dir, config["theme_key"])

    print(f"  → {generated} CdC générés pour {vertical_name}")
    return generated


def print_queue_status():
    """Affiche l'état de toutes les files."""
    print("\n[Queue] ══ ÉTAT DES FILES CdC ══")
    total_pending = 0
    for vname, config in CONFIGS.items():
        products_dir = ROOT / config["products_dir"]
        pending_count, _ = scan_pending(products_dir, config["theme_key"])
        status = "✓" if pending_count >= TARGET_PENDING else f"⚠ ({pending_count}/{TARGET_PENDING})"
        print(f"  {vname:12s} : {pending_count:2d} pending  {status}")
        total_pending += pending_count
    print(f"  {'TOTAL':12s} : {total_pending:2d} CdC disponibles pour Hugo")
    print()


def run():
    vertical_filter = os.environ.get("VERTICAL", "all").lower()

    print(f"[Queue Manager] Cible: {TARGET_PENDING} CdC/vertical | Max/run: {MAX_PER_RUN} | Dry: {DRY_RUN}")
    print(f"[Queue Manager] Date: {date.today().isoformat()}")

    print_queue_status()

    targets = CONFIGS if vertical_filter == "all" else {
        k: v for k, v in CONFIGS.items() if k == vertical_filter
    }

    if not targets:
        print(f"[Queue Manager] Vertical inconnu: {vertical_filter}")
        sys.exit(1)

    total_generated = 0
    for vname, config in targets.items():
        n = fill_queue(vname, config)
        total_generated += n

    print(f"\n[Queue Manager] ✓ Total généré: {total_generated} nouveaux CdC")
    print_queue_status()

    if total_generated > 0 and not DRY_RUN:
        print("[Queue Manager] → Nouveaux CdC à valider par Hugo (gate=pending)")
        print("[Queue Manager] → Hugo: GitHub → products/*/CAHIER_DES_CHARGES.md")


if __name__ == "__main__":
    run()
