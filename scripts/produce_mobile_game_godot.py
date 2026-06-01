#!/usr/bin/env python3
"""
Godot 4 Game Generator — génère un projet complet jouable depuis un CdC approuvé.

Contrairement au scaffold (produce_mobile_game_scaffold.py) qui génère juste
la documentation et un entry point, ce script génère un JEU JOUABLE complet :
  - project.godot      — configuration du projet
  - main.gd            — scene principale (programmatic, pas de .tscn)
  - game_logic.gd      — logique de jeu complète
  - ui_controller.gd   — interface utilisateur
  - export_presets.cfg — config export Android/iOS
  - README.md          — setup + instructions
  - STORE_LISTING.md   — texte App Store / Play Store

Genres supportés sans assets image (pur code Godot 4) :
  - text_rpg / roguelike_text  → UI fullscreen avec RichTextLabel
  - escape_puzzle              → CanvasLayer avec boutons interactifs
  - sliding_puzzle             → GridContainer programmatique
  - puzzle_narrative           → dialogue + inventory en code
  - turn_based_rpg             → grille tactique en code

Variables d'env :
  GAME_DIR — chemin du produit (products/mobile_games/{slug})
             si absent, auto-détecte le dernier approuvé non encore produit
  GODOT_GAME — "1" pour forcer ce générateur (vs scaffold par défaut)
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.lib.brain_utils import llm_call


# ── Genres supportés en pur code Godot 4 (pas d'assets image) ────────────────
GODOT_PURE_CODE_GENRES = {
    "text_rpg",
    "roguelike_text",
    "escape_puzzle",
    "sliding_puzzle",
    "puzzle_narrative",
    "turn_based_rpg",
}


def load_code_scout_results(game_dir: Path) -> dict:
    """Lit code_scout_results.json s'il existe et retourne les données pertinentes."""
    scout_path = game_dir / "code_scout_results.json"
    if not scout_path.exists():
        return {}
    try:
        data = json.loads(scout_path.read_text(encoding="utf-8"))
        recommended = data.get("recommended_bases", [])
        notes = data.get("integration_notes", "")
        if recommended or notes:
            print(f"[Godot] Code Scout results loaded: {len(recommended)} recommended base(s)")
            return {"recommended_bases": recommended, "integration_notes": notes}
    except Exception as e:
        print(f"[Godot] Could not read code_scout_results.json: {e}")
    return {}


def make_scout_injection(scout: dict) -> str:
    """Construit le bloc à injecter dans les prompts système si Code Scout a trouvé des résultats."""
    if not scout:
        return ""
    recommended = scout.get("recommended_bases", [])
    notes = scout.get("integration_notes", "")
    parts = []
    if recommended:
        parts.append(f"EXISTING CODE BASES TO USE:\nRepos: {', '.join(recommended)}")
    if notes:
        parts.append(f"Integration notes: {notes}")
    if not parts:
        return ""
    return "\n\n" + "\n".join(parts) + "\n"


def find_approved_game() -> Path | None:
    """Trouve le dernier CdC approuvé non encore produit dans products/mobile_games/."""
    base = ROOT / "products" / "mobile_games"
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


def make_project_godot(title: str, version: str = "1.0") -> str:
    """Génère le fichier project.godot avec config minimale pour mobile."""
    return f"""; Engine configuration file.
; It contains icon and start scenes, as well as basic settings.
; Format version 3 corresponds to Godot 4.x

[gd_version]

format=3

[application]

config/name="{title}"
config/version="{version}"
config/features=PackedStringArray("4.2", "Mobile")
run/main_scene="res://main.gd"

[display]

window/size/viewport_width=390
window/size/viewport_height=844
window/stretch/mode="canvas_items"
window/stretch/aspect="expand"
window/handheld/orientation=1

[rendering]

renderer/rendering_method="mobile"
textures/canvas_textures/default_texture_filter=0
"""


def make_export_presets() -> str:
    """Génère export_presets.cfg avec configs Android + iOS de base."""
    return """[preset.0]

name="Android"
platform="Android"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path=""
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.0.options]

custom_template/debug=""
custom_template/release=""
gradle_build/use_gradle_build=false
gradle_build/gradle_build_directory=""
gradle_build/android_source_template=""
version/code=1
version/name="1.0"
package/unique_name="com.hugo365.{slug}"
package/name="{title}"
package/signed=false
architectures/armeabi-v7a=false
architectures/arm64-v8a=true
architectures/x86=false
architectures/x86_64=false
splash_screen/show_image=true
splash_screen/fullscreen=false
permissions/internet=true

[preset.1]

name="iOS"
platform="iOS"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path=""
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.1.options]

custom_template/debug=""
custom_template/release=""
application/bundle_identifier="com.hugo365.{slug}"
application/signature="{title}"
application/short_version="1.0"
application/version="1.0"
application/icon_interpolation=4
landscape_launch_screens/iphone_2x=""
portrait_launch_screens/iphone_2x=""
"""


# ── Générateurs de code par genre ─────────────────────────────────────────────

def generate_text_rpg_files(cdc: dict, scout_injection: str = "") -> dict[str, str]:
    """Génère les fichiers GDScript pour un jeu text_rpg ou roguelike_text."""
    concept = cdc.get("concept", {})
    titre = concept.get("titre", "Text RPG")
    genre = concept.get("genre", "text_rpg")
    pitch = concept.get("pitch", "")
    niche = concept.get("sous_niche", "")
    mvp = cdc.get("mvp_scope", {})
    features = mvp.get("features_v1", [])
    is_roguelike = genre == "roguelike_text"

    system_prompt = """You are an expert Godot 4 GDScript developer specializing in mobile games.
Generate complete, functional GDScript files for a text-based RPG/dungeon game.
The code must be 100% programmatic — no .tscn files, everything created in code.
Style: black background, green/amber monospace text, retro terminal aesthetic.
Output ONLY the raw GDScript code, no markdown fences, no explanation.""" + scout_injection

    # main.gd
    user_main = f"""Generate main.gd for Godot 4 — the root scene script.
Game: {titre}
Genre: {genre} ({pitch})
Style: dark terminal, RichTextLabel fullscreen, retro monospace

The script must:
- Extend SceneTree (not Node)
- In _init(): set up the entire UI programmatically (no .tscn)
  * Create a CanvasLayer > VBoxContainer > RichTextLabel (output log, 70% height)
  * Create a HBoxContainer with action buttons (attack, flee, inventory, look)
  * Use dark theme: bg=#0a0a0a, text=#00ff41 (green) or #ffb347 (amber)
  * Set window title to "{titre}"
- Preload game_logic.gd and ui_controller.gd
- On ready: show title screen, then start dungeon

Implement proper signal connections between UI buttons and game logic.
Add mobile touch support (large button hit areas, minimum 48dp).
{"Include permadeath logic and procedural dungeon floors." if is_roguelike else "Include save/load via ConfigFile."}
"""

    response_main = llm_call("cdc_generator", system_prompt, user_main, temperature=0.3, max_tokens=12000, json_mode=False)

    # game_logic.gd
    user_logic = f"""Generate game_logic.gd for Godot 4 — complete game logic.
Game: {titre}
Genre: {genre}
Features to implement: {', '.join(features[:6])}

The script must include:
- Player class: hp, max_hp, attack, defense, level, xp, gold, inventory (Array)
- Enemy class: name, hp, attack, defense, xp_reward, gold_reward
- Dungeon generator: {"fully procedural rooms, random enemies, random items" if is_roguelike else "10 hand-crafted rooms with fixed difficulty curve"}
- Combat system: turn-based, hit/miss/crit calculation, status effects (poison, stun)
- Inventory system: weapons, armor, potions, max 10 slots
- Loot tables: random drops per enemy type
- {"Permadeath: no save on death, new run starts fresh" if is_roguelike else "Save system: save after each room cleared"}
- Level up: stat increases at XP thresholds
- Boss encounters: every {"5th" if is_roguelike else "3rd"} room

Emit signals for: combat_log(text), player_died, level_up(new_level), room_changed(room_data).
"""

    response_logic = llm_call("cdc_generator", system_prompt, user_logic, temperature=0.3, max_tokens=12000, json_mode=False)

    # ui_controller.gd
    user_ui = f"""Generate ui_controller.gd for Godot 4 — UI controller.
Game: {titre}
Genre: {genre}

The script must:
- Manage the RichTextLabel combat log (max 50 lines, auto-scroll)
- Format text with BBCode: [color=#00ff41]combat[/color], [color=#ff4444]damage[/color],
  [color=#ffb347]loot[/color], [color=#4488ff]narrative[/color]
- Update HP bar (drawn programmatically with ProgressBar nodes)
- Show/hide inventory panel (GridContainer with item buttons)
- Animate text: type-writer effect for story moments
- Handle button states: disable during animations, re-enable after
- Show room description with ASCII art header
- {"Show floor number and run stats for roguelike" if is_roguelike else "Show progress map (10 dots, current highlighted)"}
- Mobile-friendly: all interactive elements min 48x48px
"""

    response_ui = llm_call("cdc_generator", system_prompt, user_ui, temperature=0.3, max_tokens=12000, json_mode=False)

    return {
        "main.gd": response_main or "# LLM generation failed for main.gd\nextends SceneTree\n",
        "game_logic.gd": response_logic or "# LLM generation failed for game_logic.gd\nextends Node\n",
        "ui_controller.gd": response_ui or "# LLM generation failed for ui_controller.gd\nextends Node\n",
    }


def generate_escape_puzzle_files(cdc: dict, scout_injection: str = "") -> dict[str, str]:
    """Génère les fichiers GDScript pour un escape_puzzle style Rusty Lake."""
    concept = cdc.get("concept", {})
    titre = concept.get("titre", "Escape Puzzle")
    pitch = concept.get("pitch", "")
    visuel = cdc.get("visuel", {})
    ambiance = visuel.get("ambiance", "dark surrealist atmospheric")
    mvp = cdc.get("mvp_scope", {})
    features = mvp.get("features_v1", [])

    system_prompt = """You are an expert Godot 4 GDScript developer specializing in atmospheric puzzle games.
Generate complete, functional GDScript files for a room escape puzzle game.
100% programmatic — no .tscn files, everything created in code.
Dark, surrealist aesthetic inspired by Rusty Lake / Cube Escape games.
Output ONLY the raw GDScript code, no markdown fences, no explanation.""" + scout_injection

    # main.gd
    user_main = f"""Generate main.gd for Godot 4 — the root scene.
Game: {titre}
Pitch: {pitch}
Ambiance: {ambiance}

The script must:
- Extend SceneTree
- Create a CanvasLayer with a dark viewport (800x600 scaled to mobile)
- Set up room navigation: 3-5 rooms, each with clickable hotspots
- Create inventory bar at bottom (horizontal strip, 6 slots)
- Preload room_manager.gd and puzzle_logic.gd
- On start: show title card (black screen, centered text, atmospheric music note)
- Handle click/touch: ray-cast to hotspot, trigger room_manager action
- Mobile: scale touch areas appropriately

Background color: #1a1008 (dark sepia)
Text color: #c8b89a (parchment)
"""

    response_main = llm_call("cdc_generator", system_prompt, user_main, temperature=0.3, max_tokens=12000, json_mode=False)

    # room_manager.gd
    user_room = f"""Generate room_manager.gd for Godot 4 — manages 3-5 interconnected rooms.
Game: {titre}

Each room is a dictionary with:
- id: String
- description: String (atmospheric, 2 sentences)
- objects: Array of {{name, state, can_pick_up, requires_item, description}}
- exits: Dictionary {{direction: room_id, requires_item: "" or item_name}}
- puzzle: optional {{type: "combination|sequence|symbol", solution: ..., solved: false}}

Create 5 rooms:
1. Entry hall — dark corridor, locked door ahead, key hidden under mat
2. Study — desk with locked drawer, bookshelf with clues, window
3. Laboratory — strange equipment, combination lock on cabinet
4. Garden — overgrown, hidden passage, symbolic puzzle
5. Final chamber — escape mechanism, requires items from all rooms

Implement:
- enter_room(room_id): update scene display
- interact_with(object_id): return action result
- try_combine(item1, item2): inventory combination logic
- check_win_condition(): all puzzles solved

Emit signals: room_entered(room_data), object_interacted(result_text), puzzle_solved(room_id).
"""

    response_room = llm_call("cdc_generator", system_prompt, user_room, temperature=0.3, max_tokens=12000, json_mode=False)

    # puzzle_logic.gd
    user_puzzle = f"""Generate puzzle_logic.gd for Godot 4 — inventory and puzzle state.
Game: {titre}
Features: {', '.join(features[:5])}

Implement:
- Inventory: max 6 items, add/remove/has/use methods
- Item definitions: name, description, use_context (where it can be used)
- Puzzle states: track which puzzles are solved
- Combination rules: item A + item B = item C (at least 3 combinations)
- Use-item-on-object: validate conditions, update world state
- Hint system: after 3 failed attempts, give subtle hint
- Atmospheric narration: each action returns flavor text in the game's dark tone

Save state: use ConfigFile for auto-save after each puzzle solved.
"""

    response_puzzle = llm_call("cdc_generator", system_prompt, user_puzzle, temperature=0.3, max_tokens=12000, json_mode=False)

    return {
        "main.gd": response_main or "# LLM generation failed for main.gd\nextends SceneTree\n",
        "room_manager.gd": response_room or "# LLM generation failed for room_manager.gd\nextends Node\n",
        "puzzle_logic.gd": response_puzzle or "# LLM generation failed for puzzle_logic.gd\nextends Node\n",
    }


def generate_sliding_puzzle_files(cdc: dict, scout_injection: str = "") -> dict[str, str]:
    """Génère les fichiers GDScript pour un sliding_puzzle."""
    concept = cdc.get("concept", {})
    titre = concept.get("titre", "Sliding Puzzle")
    pitch = concept.get("pitch", "")
    visuel = cdc.get("visuel", {})
    style = visuel.get("style", "minimalist")
    palette = visuel.get("palette", "dark gothic")
    mvp = cdc.get("mvp_scope", {})
    nb_levels = mvp.get("nb_niveaux", 10)

    system_prompt = """You are an expert Godot 4 GDScript developer.
Generate complete, functional GDScript files for a sliding puzzle (taquin) mobile game.
100% programmatic — no .tscn files, everything created in code.
Clean minimalist UI, smooth animations.
Output ONLY the raw GDScript code, no markdown fences, no explanation.""" + scout_injection

    # main.gd + board.gd combined approach
    user_main = f"""Generate main.gd for Godot 4 — the root scene.
Game: {titre}
Pitch: {pitch}
Style: {style}, {palette}

The script must:
- Extend SceneTree
- Create a CanvasLayer with centered GridContainer for the puzzle board
- Board sizes: 3x3, 4x4, 5x5 (unlockable)
- Create top HUD: level number, move counter, timer (MM:SS), best score
- Create bottom controls: shuffle button, hint button, undo button
- Preload board.gd
- On start: show level select screen (grid of {nb_levels} levels with lock icons)
- Level select → board setup → game loop → win screen
- Win screen: show moves, time, star rating (1-3 stars), next level button

Visual theme: use ColorRect tiles with contrasting Label numbers.
Tile colors: {palette} aesthetic.
Smooth tween animations for tile slides (0.15s).
Mobile: large tiles, swipe gesture support.
"""

    response_main = llm_call("cdc_generator", system_prompt, user_main, temperature=0.3, max_tokens=12000, json_mode=False)

    # board.gd
    user_board = f"""Generate board.gd for Godot 4 — puzzle board logic.
Game: {titre}

Implement complete sliding puzzle logic:
- Board representation: 1D Array of size n*n (0 = empty tile)
- is_solved(): check if array matches [1,2,...,n*n-1,0]
- shuffle(moves=100): make random valid moves to generate solvable board
- can_move(tile_pos): check if tile is adjacent to empty space
- move_tile(tile_pos): perform slide, update array, return true if valid
- get_empty_pos(): returns Vector2i of empty tile
- Undo stack: last 10 moves
- undo_move(): revert last move

Animation:
- Tween tile from old position to new position (0.15s ease_in_out)
- Emit signal tile_moved(from_pos, to_pos) after each move
- Emit signal puzzle_solved(moves, time_seconds) on win

Scoring:
- 3 stars: solved in ≤ par_moves (3x3=20, 4x4=45, 5x5=80)
- 2 stars: ≤ 2x par_moves
- 1 star: any completion

PlayerPrefs via ConfigFile: save best_moves and best_time per level.
"""

    response_board = llm_call("cdc_generator", system_prompt, user_board, temperature=0.3, max_tokens=12000, json_mode=False)

    return {
        "main.gd": response_main or "# LLM generation failed for main.gd\nextends SceneTree\n",
        "board.gd": response_board or "# LLM generation failed for board.gd\nextends Node\n",
    }


def generate_puzzle_narrative_files(cdc: dict, scout_injection: str = "") -> dict[str, str]:
    """Génère les fichiers GDScript pour un puzzle_narrative ou turn_based_rpg."""
    concept = cdc.get("concept", {})
    titre = concept.get("titre", "Puzzle Narrative")
    genre = concept.get("genre", "puzzle_narrative")
    pitch = concept.get("pitch", "")
    mvp = cdc.get("mvp_scope", {})
    features = mvp.get("features_v1", [])
    is_tactical = genre == "turn_based_rpg"

    if is_tactical:
        system_prompt = (
            "You are an expert Godot 4 GDScript developer specializing in tactical RPGs.\n"
            "Generate complete, functional GDScript files for a grid-based tactical combat game.\n"
            "100% programmatic — no sprites or .tscn files, tiles and units drawn with ColorRect and labels.\n"
            "Output ONLY the raw GDScript code, no markdown fences, no explanation."
            + scout_injection
        )
    else:
        system_prompt = (
            "You are an expert Godot 4 GDScript developer.\n"
            "Generate complete, functional GDScript files for a narrative puzzle / tactical RPG.\n"
            "100% programmatic — no .tscn files, everything created in code.\n"
            "Output ONLY the raw GDScript code, no markdown fences, no explanation."
            + scout_injection
        )

    features_str = ", ".join(features[:5])

    if is_tactical:
        main_requirements = (
            "- Extend SceneTree\n"
            "- Create a GridContainer (8x8 or 6x6) where each cell is a ColorRect (40x40px)\n"
            "  * Terrain types: grass=#2d5a1b, stone=#555555, water=#1a3a5c, wall=#333333\n"
            "  * Unit indicator: colored circle drawn with CanvasItem draw_circle\n"
            "- Side panel: unit stats, action menu (Move, Attack, Wait, Item)\n"
            "- Bottom log: last 5 combat messages (RichTextLabel)\n"
            "- Turn order display at top (icons/labels)\n"
            "- State machine: PLAYER_TURN -> unit selection -> action selection -> ENEMY_TURN\n"
            "- Preload game_logic.gd and ui_controller.gd"
        )
        main_header = "Tactical RPG requirements:"
    else:
        main_requirements = (
            "- Extend SceneTree\n"
            "- Main panel: scene illustration (ColorRect with atmospheric gradient + text overlay)\n"
            "- Dialogue box: RichTextLabel with typewriter effect, 3 lines max\n"
            "- Choice buttons: up to 4 choices per scene\n"
            "- Inventory panel: 6 slots, combine items mechanic\n"
            "- Notebook/clues panel: collected evidence list\n"
            "- State machine: EXPLORE -> DIALOGUE -> INVESTIGATE -> PUZZLE -> CUTSCENE\n"
            "- Preload game_logic.gd and ui_controller.gd"
        )
        main_header = "Mystery puzzle narrative requirements:"

    user_main = (
        f"Generate main.gd for Godot 4.\n"
        f"Game: {titre}\n"
        f"Genre: {genre}\n"
        f"Pitch: {pitch}\n"
        f"Features: {features_str}\n\n"
        f"{main_header}\n"
        f"{main_requirements}\n"
    )

    response_main = llm_call("cdc_generator", system_prompt, user_main, temperature=0.3, max_tokens=12000, json_mode=False)

    if is_tactical:
        logic_header = "Implement tactical combat:"
        logic_requirements = (
            "- Unit class: name, hp, max_hp, move_range, attack_range, attack, defense, team (PLAYER/ENEMY)\n"
            "- Grid class: 2D array of tiles, unit placement, movement range calculation (BFS)\n"
            "- Combat: attack formula = max(1, attacker.attack - defender.defense) + rand(-1,2)\n"
            "- AI: simple aggressive AI — move toward nearest player unit, attack if in range\n"
            "- Victory: all enemy units defeated\n"
            "- Defeat: all player units defeated\n"
            "- Level data: hardcoded 5 maps with increasing difficulty\n"
            "- Emit signals: unit_moved, unit_attacked(attacker, defender, damage), unit_died, turn_ended"
        )
    else:
        logic_header = "Implement mystery investigation:"
        logic_requirements = (
            "- Scene graph: dictionary of scenes, each with: description, items, exits, npcs, triggers\n"
            "- NPC dialogue: branching dialogue trees (Array of dicts with text, choices, next_node)\n"
            "- Evidence/clue system: collect, combine, present to NPCs\n"
            "- Puzzle registry: track solved/unsolved puzzles, unlock conditions\n"
            "- Inventory: 6 slots, combine mechanic (item + item = clue or new item)\n"
            "- Ending system: multiple endings based on evidence collected\n"
            "- Emit signals: scene_entered, dialogue_advanced, clue_found, puzzle_solved, ending_reached"
        )

    user_logic = (
        f"Generate game_logic.gd for Godot 4.\n"
        f"Game: {titre}\n"
        f"Genre: {genre}\n\n"
        f"{logic_header}\n"
        f"{logic_requirements}\n"
    )

    response_logic = llm_call("cdc_generator", system_prompt, user_logic, temperature=0.3, max_tokens=12000, json_mode=False)

    if is_tactical:
        ui_header = "Tactical RPG UI:"
        ui_requirements = (
            "- Highlight valid move tiles (blue tint overlay)\n"
            "- Highlight attack range tiles (red tint overlay)\n"
            "- Show unit tooltip on hover/tap: name, HP bar, stats\n"
            "- Animate unit movement along path (smooth tween)\n"
            "- Combat floatie: damage number popup animation (+15, MISS, CRIT)\n"
            "- End turn button (large, always visible)\n"
            "- Victory/defeat overlay with retry/next buttons\n"
            "- Mobile: tap to select unit, tap destination to move, tap enemy to attack"
        )
    else:
        ui_header = "Narrative puzzle UI:"
        ui_requirements = (
            "- Typewriter text effect: reveal dialogue character by character (30ms/char)\n"
            "- Fade transitions between scenes (0.3s)\n"
            "- Highlight interactive objects with subtle pulse animation\n"
            "- Inventory drag (or tap-to-select, tap-slot-to-place)\n"
            "- Notebook animation: flip open on evidence collected\n"
            "- Choice button highlight on hover/tap\n"
            "- Mobile: large touch targets, swipe to navigate evidence board"
        )

    user_ui = (
        f"Generate ui_controller.gd for Godot 4.\n"
        f"Game: {titre}\n"
        f"Genre: {genre}\n\n"
        f"{ui_header}\n"
        f"{ui_requirements}\n"
    )

    response_ui = llm_call("cdc_generator", system_prompt, user_ui, temperature=0.3, max_tokens=12000, json_mode=False)

    return {
        "main.gd": response_main or "# LLM generation failed for main.gd\nextends SceneTree\n",
        "game_logic.gd": response_logic or "# LLM generation failed for game_logic.gd\nextends Node\n",
        "ui_controller.gd": response_ui or "# LLM generation failed for ui_controller.gd\nextends Node\n",
    }


def generate_readme(cdc: dict, generated_files: list[str]) -> str:
    """Génère README.md via LLM."""
    concept = cdc.get("concept", {})
    framework = cdc.get("framework", {})
    mvp = cdc.get("mvp_scope", {})
    store = cdc.get("store_listing", {})

    system_prompt = """You are a game developer documentation expert.
Generate a complete README.md for a Godot 4 mobile game project.
The project is a complete, playable game (not a scaffold).
Include: overview, how to open in Godot 4, how to test on mobile, how to export for Android/iOS.
Write in English. Output only the Markdown content, no JSON wrapper."""

    user_prompt = f"""Generate the README.md for:

Title: {concept.get('titre', '?')}
Genre: {concept.get('genre', '?')}
Pitch: {concept.get('pitch', '?')}
Core mechanic: {concept.get('gameplay_core', '?')}

Framework: Godot 4
Export targets: Android, iOS
Files generated: {', '.join(generated_files)}

V1 features: {', '.join(mvp.get('features_v1', [])[:5])}
Store title: {store.get('titre_store', '?')}

Include:
1. Project overview (2-3 sentences)
2. Requirements (Godot 4.2+, Android SDK, Xcode)
3. How to open and run (Godot 4 specific steps)
4. How to export for Android (export_presets.cfg is already configured)
5. How to export for iOS
6. Architecture overview (what each .gd file does)
7. Customization guide (how to modify levels/content)
8. Store submission checklist"""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.65, max_tokens=3000, json_mode=False)
    return response.strip() if response else f"# {concept.get('titre', 'Game')}\n\nGodot 4 game generated from CdC.\n"


def generate_store_listing(cdc: dict) -> str:
    """Génère STORE_LISTING.md via LLM."""
    concept = cdc.get("concept", {})
    store = cdc.get("store_listing", {})
    monetisation = cdc.get("monetisation", {})

    system_prompt = """You are an App Store Optimization (ASO) expert.
Generate a complete STORE_LISTING.md for App Store, Google Play, and Itch.io.
Write in English. Output only the Markdown content."""

    user_prompt = f"""Generate the store listing for:

Game title: {concept.get('titre', '?')}
Genre: {concept.get('genre', '?')}
Pitch: {concept.get('pitch', '?')}
Core mechanic: {concept.get('gameplay_core', '?')}

Store title: {store.get('titre_store', concept.get('titre', '?'))}
Short description: {store.get('description_courte_en', '?')}
Keywords: {', '.join(store.get('keywords', []))}
Age rating: {store.get('age_rating', '4+')}
Monetization: {monetisation.get('modele', '?')}
Price: ${monetisation.get('prix_achat_usd', 0)}
ASO keywords: {', '.join(cdc.get('mots_cles_aso', []))}

Sections needed:
1. App Store (iOS): title (30 chars max), subtitle (30 chars), keywords (100 chars), description (4000 chars)
2. Google Play: title (50 chars), short description (80 chars), full description (4000 chars)
3. Itch.io: title, tagline, description
4. Screenshots plan (5-8 screenshots, what each should show)"""

    response = llm_call("cdc_generator", system_prompt, user_prompt, temperature=0.65, max_tokens=3000, json_mode=False)
    return response.strip() if response else f"# Store Listing\n\n{concept.get('titre', 'Game')}\n"


# ── Dispatcher par genre ───────────────────────────────────────────────────────

def generate_game_files(cdc: dict, genre: str, scout_injection: str = "") -> dict[str, str]:
    """Dispatch vers le bon générateur selon le genre."""
    if genre in ("text_rpg", "roguelike_text"):
        return generate_text_rpg_files(cdc, scout_injection=scout_injection)
    elif genre == "escape_puzzle":
        return generate_escape_puzzle_files(cdc, scout_injection=scout_injection)
    elif genre == "sliding_puzzle":
        return generate_sliding_puzzle_files(cdc, scout_injection=scout_injection)
    elif genre in ("puzzle_narrative", "turn_based_rpg"):
        return generate_puzzle_narrative_files(cdc, scout_injection=scout_injection)
    else:
        # Fallback pour les genres non spécialisés — utilise text_rpg comme base
        print(f"[Godot] Genre '{genre}' non spécialisé — fallback text_rpg")
        return generate_text_rpg_files(cdc, scout_injection=scout_injection)


def run():
    game_dir_env = os.environ.get("GAME_DIR", "").strip()
    force_godot = os.environ.get("GODOT_GAME", "0").strip() == "1"

    if game_dir_env:
        game_dir = ROOT / game_dir_env
    else:
        game_dir = find_approved_game()

    if not game_dir:
        print("[Godot] No approved CdC found in products/mobile_games/")
        sys.exit(0)

    cdc_path = game_dir / "cdc.json"
    if not cdc_path.exists():
        print(f"[Godot] cdc.json missing: {cdc_path}", file=sys.stderr)
        sys.exit(1)

    cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
    gate = cdc.get("gate_cdc", "pending")

    if gate == "pending":
        print("[Godot] GATE=PENDING — waiting for Hugo validation.")
        sys.exit(0)
    if gate == "rejected":
        print("[Godot] GATE=REJECTED — production cancelled.")
        sys.exit(0)

    concept = cdc.get("concept", {})
    titre = concept.get("titre", game_dir.name)
    genre = concept.get("genre", "text_rpg")
    generation_approach = cdc.get("mvp_scope", {}).get("generation_approach", "")
    framework_choice = cdc.get("framework", {}).get("choix", "Godot 4")

    # Vérifier si ce générateur est approprié
    if not force_godot and genre not in GODOT_PURE_CODE_GENRES:
        if "godot4_pure_code" not in generation_approach:
            print(f"[Godot] Genre '{genre}' → use scaffold instead (or set GODOT_GAME=1 to force)")
            print(f"[Godot] Hint: generation_approach={generation_approach}")
            sys.exit(0)

    print(f"\n[Godot] Generating complete game: '{titre}' ({genre})")
    print(f"[Godot] Source: {game_dir.name}")
    print(f"[Godot] Framework: Godot 4 (pure code, no .tscn)")

    # Slug pour export_presets
    slug = titre.lower().replace(" ", "_").replace("'", "")[:20]

    # ── Étape 1 : project.godot ────────────────────────────────────────────────
    print("\n[Godot] Writing project.godot...")
    project_godot = make_project_godot(titre)
    (game_dir / "project.godot").write_text(project_godot, encoding="utf-8")
    print("[Godot] ✓ project.godot")

    # ── Étape 2 : export_presets.cfg ──────────────────────────────────────────
    print("[Godot] Writing export_presets.cfg...")
    export_cfg = make_export_presets().replace("{slug}", slug).replace("{title}", titre)
    (game_dir / "export_presets.cfg").write_text(export_cfg, encoding="utf-8")
    print("[Godot] ✓ export_presets.cfg")

    # ── Lire les résultats Code Scout (s'ils existent) ────────────────────────
    scout = load_code_scout_results(game_dir)
    scout_injection = make_scout_injection(scout)
    if scout_injection:
        print(f"[Godot] Code Scout injection: {len(scout.get('recommended_bases', []))} repo(s) injected into prompts")

    # ── Étape 3 : Fichiers GDScript par genre ─────────────────────────────────
    print(f"\n[Godot] Generating GDScript files for genre '{genre}'...")
    game_files = generate_game_files(cdc, genre, scout_injection=scout_injection)

    generated_script_names = []
    for filename, content in game_files.items():
        print(f"[Godot] Writing {filename}...")
        (game_dir / filename).write_text(content, encoding="utf-8")
        generated_script_names.append(filename)
        print(f"[Godot] ✓ {filename} ({len(content)} chars)")

    # ── Étape 4 : README.md ───────────────────────────────────────────────────
    print("\n[Godot] Generating README.md...")
    all_files = ["project.godot", "export_presets.cfg"] + generated_script_names
    readme = generate_readme(cdc, all_files)
    (game_dir / "README.md").write_text(readme, encoding="utf-8")
    print("[Godot] ✓ README.md")

    # ── Étape 5 : STORE_LISTING.md ────────────────────────────────────────────
    print("[Godot] Generating STORE_LISTING.md...")
    store_listing = generate_store_listing(cdc)
    (game_dir / "STORE_LISTING.md").write_text(store_listing, encoding="utf-8")
    print("[Godot] ✓ STORE_LISTING.md")

    # ── Mise à jour cdc.json ───────────────────────────────────────────────────
    cdc["production_status"] = "godot_game_generated"
    cdc["production_date"] = date.today().isoformat()
    cdc["generated_files"] = all_files + ["README.md", "STORE_LISTING.md"]
    cdc_path.write_text(json.dumps(cdc, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[Godot] ✓ Complete game '{titre}' generated!")
    print(f"[Godot] → {game_dir}")
    print(f"[Godot] Files: {', '.join(all_files + ['README.md', 'STORE_LISTING.md'])}")
    print(f"[Godot] Next steps:")
    print(f"[Godot]   1. Open Godot 4 → Import project → select {game_dir}/project.godot")
    print(f"[Godot]   2. Run (F5) to test")
    print(f"[Godot]   3. Project → Export → Android/iOS (export_presets.cfg pre-configured)")


if __name__ == "__main__":
    run()
