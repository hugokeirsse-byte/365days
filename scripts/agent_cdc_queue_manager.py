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
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGET_PENDING = int(os.environ.get("TARGET", "10"))
MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", "5"))
# 60s entre CdC : safe pour Groq (primary, 30 RPM) et Gemini fallback (15 RPM = 4s/req).
# 30s entre verticals : laisse la fenêtre RPM se réinitialiser.
# Calcul : 11 verticals × 3 CdC × 60s + 11 × 30s = ~2310s = ~38 min/run. OK pour cron 6h.
THROTTLE_SECONDS = int(os.environ.get("THROTTLE_SECONDS", "60"))
INTER_VERTICAL_DELAY = int(os.environ.get("INTER_VERTICAL_DELAY", "30"))
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"

# ── Pools de thèmes — diversité garantie, pas de répétition ────────────────────────────────

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
    "game_assets": [
        # Asset packs pour game devs (itch.io, Unity Asset Store, GameDev Market)
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
    "mobile_games": [
        # (genre, niche)
        ("hyper_casual", "satisfying merge puzzle"),
        ("puzzle", "word game dark humor"),
        ("idle", "cute animals farm"),
        ("platformer", "precision indie hardcore"),
        ("hyper_casual", "brain training reflex"),
        ("simulation", "cozy life management"),
        ("arcade", "survival endless runner"),
        ("puzzle", "logic grid minimalist"),
        ("idle", "space exploration incremental"),
        ("platformer", "retro pixel art adventure"),
        ("hyper_casual", "color sorting calming"),
        ("rpg", "roguelike dungeon minimal"),
        ("simulation", "restaurant management casual"),
        ("arcade", "rhythm music tapping"),
        ("puzzle", "physics sandbox creative"),
        # Escape puzzle (style Rusty Lake — dark, surréaliste, atmosphérique)
        ("escape_puzzle", "dark surrealist rusty lake atmospheric"),
        ("escape_puzzle", "minimalist black white geometric abstract"),
        ("escape_puzzle", "retro pixel mysterious horror room"),
        # Sliding puzzles
        ("sliding_puzzle", "classic 15 puzzle dark gothic minimal"),
        ("sliding_puzzle", "hex grid zen nature calming"),
        # Text RPG / Dungeon crawler
        ("text_rpg", "dungeon crawler dnd dark fantasy turn based"),
        ("text_rpg", "branching narrative survival horror choice"),
        ("roguelike_text", "procedural dungeon roguelike minimalist"),
        # Puzzle narratif
        ("puzzle_narrative", "mystery noir detective investigation"),
        ("turn_based_rpg", "grid tactical fantasy minimal no sprites"),
    ],
    "mobile_apps": [
        # (category, niche)
        ("productivity", "task manager anxiety-friendly"),
        ("health", "sleep tracker minimalist"),
        ("finance", "expense tracker no-ads"),
        ("lifestyle", "habit tracker cute gamification"),
        ("tools", "password manager offline"),
        ("creativity", "quick sketch doodle journal"),
        ("education", "language flashcards spaced repetition"),
        ("health", "water intake reminder gentle"),
        ("productivity", "pomodoro timer focus"),
        ("finance", "bill splitter friends"),
        ("lifestyle", "mood journal private no-cloud"),
        ("tools", "unit converter offline"),
        ("education", "speed reading trainer"),
        ("creativity", "daily writing prompt journal"),
        ("health", "breathing exercise anxiety"),
    ],
    "svg_packs": [
        # (type_pack, niche)
        ("mandala", "boho wildflowers"),
        ("floral", "cottagecore botanical"),
        ("monogram", "wedding elegant script"),
        ("seasonal", "halloween gothic witch"),
        ("animal", "farmhouse rooster buffalo"),
        ("geometric", "sacred geometry boho"),
        ("quote_frame", "motivational vintage banner"),
        ("bundle_mix", "christmas holiday mega bundle"),
        ("mandala", "celestial moon phases"),
        ("floral", "tropical leaves exotic"),
        ("seasonal", "easter spring bunny"),
        ("animal", "forest woodland deer fox"),
        ("geometric", "art deco geometric seamless"),
        ("monogram", "minimalist modern alphabet"),
        ("quote_frame", "sunflower farmhouse frame"),
    ],
    "vintage_pd": [
        # (collection, sujet, type_produit)
        ("kohler_medizinal", "lavandula_officinalis", "coloring_page"),
        ("kohler_medizinal", "rosa_canina", "merch_tshirt"),
        ("kohler_medizinal", "mentha_piperita", "educational_coloring_book"),
        ("kohler_medizinal", "chamomilla_recutita", "merch_mug"),
        ("kohler_medizinal", "digitalis_purpurea", "merch_tote"),
        ("redoute_roses", "rosa_centifolia", "coloring_page"),
        ("redoute_roses", "rosa_gallica", "merch_tshirt"),
        ("audubon_birds", "northern_cardinal", "coloring_page"),
        ("audubon_birds", "american_flamingo", "merch_tshirt"),
        ("audubon_birds", "great_blue_heron", "merch_tote"),
        ("haeckel_kunstformen", "radiolaria", "coloring_page"),
        ("haeckel_kunstformen", "sea_anemones_actiniae", "merch_tshirt"),
        ("haeckel_kunstformen", "jellyfish_medusae", "coloring_page"),
        ("haeckel_kunstformen", "orchids_tropical", "merch_tote"),
        ("maria_sibylla_merian", "metamorphose_surinam_butterflies", "coloring_page"),
        ("donovan_british_insects", "papillons_exotiques", "merch_tshirt"),
        ("gould_birds_europe", "birds_of_paradise", "coloring_page"),
        ("audubon_quadrupeds", "american_bison", "merch_mug"),
        ("brehm_tierleben", "owls_hiboux", "coloring_page"),
        ("gray_anatomy_1858", "human_skull_scientific", "merch_tshirt"),
        ("kohler_medizinal", "valeriana_officinalis", "educational_coloring_book"),
        ("redoute_lilies", "lilium_candidum", "coloring_page"),
        ("wilson_american_ornithology", "woodpecker_species", "coloring_page"),
        ("blaeu_atlas_1662", "ornate_world_map_detail", "kdp_journal_cover"),
        ("haeckel_kunstformen", "cacti_desert_forms", "merch_mug"),
    ],
}

# ── Config par vertical ──────────────────────────────────────────────────

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
            cdc.get("concept_theme", {}).get("titre", "").lower()[:40],
            cdc.get("style_visuel", {}).get("style_illustration", ""),
        ),
    },
    "game_assets": {
        "products_dir": "products/game_assets",
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
    "mobile_games": {
        "products_dir": "products/mobile_games",
        "cdc_script": "scripts/agent_mobile_games_cdc.py",
        "build_env": lambda t: {
            "GAME_GENRE": t[0],
            "GAME_NICHE": t[1],
        },
        "theme_key": lambda cdc: (
            cdc.get("concept", {}).get("genre", ""),
            cdc.get("concept", {}).get("sous_niche", ""),
        ),
    },
    "mobile_apps": {
        "products_dir": "products/mobile_apps",
        "cdc_script": "scripts/agent_mobile_apps_cdc.py",
        "build_env": lambda t: {
            "APP_CATEGORY": t[0],
            "APP_NICHE": t[1],
        },
        "theme_key": lambda cdc: (
            cdc.get("concept", {}).get("categorie", ""),
            cdc.get("concept", {}).get("sous_niche", cdc.get("concept", {}).get("valeur_unique", "")[:30]),
        ),
    },
    "svg_packs": {
        "products_dir": "products/svg_packs",
        "cdc_script": "scripts/agent_svg_cdc.py",
        "build_env": lambda t: {
            "SVG_TYPE": t[0],
            "SVG_NICHE": t[1],
            "SVG_NB_ELEMENTS": "20",
        },
        "theme_key": lambda cdc: (
            cdc.get("concept", {}).get("type_pack", ""),
            cdc.get("concept", {}).get("niche", ""),
        ),
    },
    "vintage_pd": {
        "products_dir": "products/vintage_pd",
        "cdc_script": "scripts/agent_vintage_pd_cdc.py",
        "build_env": lambda t: {
            "VPD_COLLECTION": t[0],
            "VPD_SUJET": t[1],
            "VPD_PRODUCT_TYPE": t[2],
        },
        "theme_key": lambda cdc: (
            cdc.get("source", {}).get("collection", ""),
            cdc.get("source", {}).get("sujet", ""),
            cdc.get("produit", {}).get("type", ""),
        ),
    },
}


# ── Pont Brain → CdC ──────────────────────────────────────────────────
# Pour chaque vertical disposant d'un cerveau (trends), on déclare où lire ses
# propositions et comment les convertir en tuples au format de la pool.
# Les recommandations Gemini sont ainsi RÉELLEMENT injectées dans la génération,
# avec priorité sur les pools statiques (fallback). Les verticaux sans extracteur
# (coloring, mobile_*) continuent d'utiliser uniquement leur pool statique.

def _stl_brain(d):
    out = []
    r = d.get("recommandation_cdc", {})
    if r.get("type_produit") and r.get("niche"):
        out.append((r["type_produit"], r["niche"]))
    for p in d.get("produits_gagnants", []):
        if p.get("type_objet") and p.get("texte_ou_theme"):
            out.append((p["type_objet"], p["texte_ou_theme"]))
    return out

def _lowcontent_brain(d):
    r = d.get("recommandation_cdc", {})
    return [(r["type"], r["theme"])] if r.get("type") and r.get("theme") else []

def _jeux_brain(d):
    r = d.get("recommandation_cdc", {})
    if r.get("type_jeu") and r.get("theme"):
        return [(r["type_jeu"], r["theme"], r.get("mecanique", "deck-building"))]
    return []

def _roman_brain(d):
    r = d.get("recommandation_prochain_roman", {})
    if r.get("genre") and r.get("sous_genre"):
        return [(r["genre"], r["sous_genre"], r.get("langue", "en"))]
    return []

def _merch_brain(d):
    out = []
    r = d.get("recommandation_production", {})
    if r.get("niche"):
        out.append((r["niche"], "flat colorful illustration"))
    return out

def _godot_brain(d):
    r = d.get("recommandation_prochain_pack", {})
    return [(r["type"], r["theme"])] if r.get("type") and r.get("theme") else []

def _vpd_brain(d):
    r = d.get("recommandation_cdc_prioritaire", {})
    if r.get("collection") and r.get("sujet") and r.get("type_produit"):
        return [(r["collection"], r["sujet"], r["type_produit"])]
    return []

_BRAIN_BRIDGE = {
    "stl":          ("data/brain/stl",          _stl_brain),
    "lowcontent":   ("data/brain/lowcontent",   _lowcontent_brain),
    "jeux_societe": ("data/brain/jeux_societe", _jeux_brain),
    "roman":        ("data/brain/roman",        _roman_brain),
    "merch_design": ("data/brain/merch",        _merch_brain),
    "game_assets":  ("data/brain/game_assets",   _godot_brain),
    "vintage_pd":   ("data/brain/vintage_pd",   _vpd_brain),
}

for _vk, (_bdir, _bfn) in _BRAIN_BRIDGE.items():
    if _vk in CONFIGS:
        CONFIGS[_vk]["brain_dir"] = _bdir
        CONFIGS[_vk]["brain_extract"] = _bfn


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


def pick_next_theme(pool: list, already_pending: list, already_used: list,
                    recycle: bool = True) -> tuple | None:
    """Choisit le prochain thème en évitant les doublons.

    recycle=True  : si tout est consommé, on repart de la pool complète (statique).
    recycle=False : si tout est consommé, on retourne None (themes brain : épuisés
                    une fois utilisés, on bascule alors sur la pool statique).
    """
    used_set = set(map(str, already_pending + already_used))
    candidates = [t for t in pool if str(t) not in used_set]

    if not candidates and recycle:
        # Pool épuisé — recommencer depuis le début avec la pool complète
        all_pending_set = set(map(str, already_pending))
        candidates = [t for t in pool if str(t) not in all_pending_set]

    if not candidates:
        return None

    return random.choice(candidates)


def _brain_themes(vertical_name: str, config: dict) -> list:
    """Lit les propositions des cerveaux (trends) d'un vertical et les convertit
    en tuples au format de la pool. Renvoie [] si aucun cerveau/extracteur.

    C'est le pont Brain → CdC : les recommandations Gemini alimentent réellement
    la génération de CdC, au lieu de se limiter aux pools statiques.
    """
    extractor = config.get("brain_extract")
    brain_dir = config.get("brain_dir")
    if not extractor or not brain_dir:
        return []
    bdir = ROOT / brain_dir
    if not bdir.exists():
        return []

    # latest en priorité, puis quelques fichiers datés récents
    files = list(bdir.glob("*_latest.json"))
    dated = sorted([f for f in bdir.glob("*.json") if "_latest" not in f.name],
                   reverse=True)[:6]
    files += dated

    themes, seen = [], set()
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        try:
            extracted = extractor(data) or []
        except Exception:
            extracted = []
        for t in extracted:
            if not t or not all(str(x).strip() for x in t):
                continue
            key = str(t)
            if key in seen:
                continue
            seen.add(key)
            themes.append(tuple(t))
    return themes


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
            timeout=300,
            cwd=str(ROOT),
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "CdC généré" in line or "→ products" in line:
                    print(f"    ✓ {line.strip()}")
                    break
            else:
                print(f"    ✓ CdC généré (gate=pending)")
            return True
        else:
            full = (result.stdout + result.stderr).strip()
            print(f"    ✗ Erreur (rc={result.returncode}): {full[-800:]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"    ✗ Timeout (300s)")
        return False
    except Exception as e:
        print(f"    ✗ Exception: {e}")
        return False


def fill_queue(vertical_name: str, config: dict) -> int:
    """Remplit la file d'un vertical jusqu'à TARGET_PENDING. Retourne nb générés."""
    products_dir = ROOT / config["products_dir"]
    cdc_script = ROOT / config["cdc_script"]
    pool = POOLS[vertical_name]
    brain_pool = _brain_themes(vertical_name, config)

    pending_count, pending_themes = scan_pending(products_dir, config["theme_key"])
    need = max(0, TARGET_PENDING - pending_count)
    to_generate = min(need, MAX_PER_RUN)

    print(f"\n[Queue] ── {vertical_name.upper()} ──")
    print(f"  Pending: {pending_count}/{TARGET_PENDING} | À générer: {to_generate}"
          + (f" | Brain: {len(brain_pool)} propositions" if brain_pool else ""))

    if to_generate == 0:
        print(f"  ✓ File pleine ({pending_count} CdC en attente)")
        return 0

    if not cdc_script.exists():
        print(f"  ✗ Script manquant: {cdc_script}")
        return 0

    generated = 0
    used_this_run = []

    for i in range(to_generate):
        # Priorité aux propositions des cerveaux (Brain → CdC), puis pool statique
        theme = pick_next_theme(brain_pool, pending_themes, used_this_run, recycle=False)
        source = "🧠 brain"
        if theme is None:
            theme = pick_next_theme(pool, pending_themes, used_this_run)
            source = "pool"
        if theme is None:
            print(f"  ✗ Pool épuisé pour {vertical_name}")
            break

        env_vars = config["build_env"](theme)
        theme_str = " + ".join(str(t) for t in theme)
        print(f"  → Génération {i+1}/{to_generate} [{source}]: {theme_str}")

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

        # Throttle entre générations pour rester sous la limite RPM de Gemini
        # free tier (~10 req/min). Évite les rafales qui déclenchent les 429.
        if i < to_generate - 1:
            time.sleep(THROTTLE_SECONDS)

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
    verticals_list = list(targets.items())
    for idx, (vname, config) in enumerate(verticals_list):
        n = fill_queue(vname, config)
        total_generated += n
        # Pause inter-vertical : laisse la fenêtre RPM Gemini se réinitialiser
        # avant d'attaquer le prochain vertical, sauf après le dernier.
        if idx < len(verticals_list) - 1 and n > 0 and not DRY_RUN:
            print(f"  [pause inter-vertical {INTER_VERTICAL_DELAY}s avant {verticals_list[idx+1][0]}]")
            time.sleep(INTER_VERTICAL_DELAY)

    print(f"\n[Queue Manager] ✓ Total généré: {total_generated} nouveaux CdC")
    print_queue_status()

    if total_generated > 0 and not DRY_RUN:
        print("[Queue Manager] → Nouveaux CdC à valider par Hugo (gate=pending)")
        print("[Queue Manager] → Hugo: GitHub → products/*/CAHIER_DES_CHARGES.md")


if __name__ == "__main__":
    run()
