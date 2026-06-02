"""
BrightOwl Learning — TPT Product Factory
=========================================
Point d'entrée unique pour tous les générateurs.
Appelé par GitHub Actions, ou en local.

Usage:
  python scripts/tpt/run_all.py                         # tous les générateurs
  GENERATORS=mystery_picture,task_cards python ...      # sélection
  THEMES=halloween,christmas python ...                 # filtre thème
  OUT_DIR=products/tpt python ...                       # sortie custom

Pour ajouter un nouveau type de produit :
  1. Créer scripts/tpt/generators/<nom>.py
  2. Le script doit exporter : build_all(out_dir, themes, gemini_key)
  3. L'ajouter dans REGISTRY ci-dessous — c'est tout.
"""
from __future__ import annotations

import importlib
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# ─────────────────────────────────────────────────────────────────────────────
# REGISTRY — liste de tous les générateurs actifs
# Ajouter une ligne ici pour enregistrer un nouveau type de produit.
# ─────────────────────────────────────────────────────────────────────────────
REGISTRY = [
    # (module_name,         display_name,               active)
    ("tpt.generators.mystery_picture",   "Mystery Picture",          True),
    ("tpt.generators.math_drills",       "Math Drills",              True),
    ("tpt.generators.task_cards",        "Task Cards",               True),
    ("tpt.generators.exit_tickets",      "Exit Tickets",             True),
    ("tpt.generators.bingo_cards",       "Bingo Cards",              True),
    ("tpt.generators.math_sort",         "Math Sort",                True),
    ("tpt.generators.roll_cover_game",   "Roll & Cover Game",        True),
    ("tpt.generators.anchor_charts",     "Anchor Charts",            True),
    ("tpt.generators.word_problems",     "Word Problems",            True),
    ("tpt.generators.number_sense",      "Number Sense",             True),
    # Futurs générateurs — décommenter quand prêts :
    # ("tpt.generators.morning_work",    "Morning Work",             False),
    # ("tpt.generators.sub_plans",       "Sub Plans",                False),
    # ("tpt.generators.phonics_pack",    "Phonics Pack",             False),
]

# ─────────────────────────────────────────────────────────────────────────────

def run():
    out_dir  = Path(os.environ.get("OUT_DIR",  str(ROOT / "products" / "tpt")))
    gemini   = os.environ.get("GEMINI_API_KEY", "").strip()
    only_gen = [g.strip() for g in os.environ.get("GENERATORS", "").split(",") if g.strip()]
    themes   = [t.strip() for t in os.environ.get("THEMES",     "").split(",") if t.strip()]

    out_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "═"*60)
    print("  BrightOwl Learning — TPT Product Factory")
    print("═"*60)
    print(f"  Output   : {out_dir}")
    print(f"  Gemini   : {'✓' if gemini else '✗ absent (listings en template)'}")
    print(f"  Filtre   : {only_gen or 'tous'}")
    print(f"  Thèmes   : {themes or 'tous'}")
    print("═"*60 + "\n")

    results = []

    for module_path, display_name, active in REGISTRY:
        gen_id = module_path.split(".")[-1]

        if not active:
            continue
        if only_gen and gen_id not in only_gen:
            continue

        print(f"▶  {display_name} ({gen_id})")
        t0 = time.time()

        try:
            mod = importlib.import_module(module_path)
            if hasattr(mod, "build_all"):
                mod.build_all(out_dir, themes or None, gemini or None)
            elif hasattr(mod, "main"):
                # Compatibilité avec les anciens générateurs (math_drills, pipeline_cbc)
                old_env = {k: os.environ.get(k) for k in ("OUT_DIR", "THEME", "THEMES", "GEMINI_API_KEY")}
                os.environ["OUT_DIR"] = str(out_dir / gen_id)
                if themes:
                    os.environ["THEMES"] = ",".join(themes)
                    os.environ["THEME"]  = themes[0]
                if gemini:
                    os.environ["GEMINI_API_KEY"] = gemini
                mod.main()
                for k, v in old_env.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
            else:
                print(f"   ✗ {gen_id} n'expose pas build_all() ni main() — ignoré")
                results.append((display_name, "skip", 0))
                continue

            elapsed = time.time() - t0
            print(f"   ✓ terminé en {elapsed:.1f}s\n")
            results.append((display_name, "ok", elapsed))

        except Exception as exc:
            elapsed = time.time() - t0
            print(f"   ✗ ERREUR : {exc}")
            traceback.print_exc()
            results.append((display_name, "error", elapsed))

    # ── Résumé ──
    print("\n" + "═"*60)
    print("  RÉSUMÉ")
    print("═"*60)
    ok  = [r for r in results if r[1] == "ok"]
    err = [r for r in results if r[1] == "error"]
    skp = [r for r in results if r[1] == "skip"]
    for name, status, t in results:
        icon = {"ok": "✓", "error": "✗", "skip": "○"}[status]
        print(f"  {icon}  {name:<30} {t:.1f}s" if status != "skip" else f"  {icon}  {name}")
    print("═"*60)
    print(f"  ✓ {len(ok)} réussis  |  ✗ {len(err)} erreurs  |  ○ {len(skp)} ignorés")

    # Compter les fichiers produits
    pdfs = list(out_dir.rglob("*.pdf"))
    zips = list(out_dir.rglob("*.zip"))
    print(f"  📄 {len(pdfs)} PDFs  |  🗜 {len(zips)} ZIPs  →  {out_dir}")
    print("═"*60 + "\n")

    return len(err)


if __name__ == "__main__":
    sys.exit(run())
