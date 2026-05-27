#!/usr/bin/env python3
"""
Optimiseur perpétuel par vertical — boucle de feedback autonome.

Pour chaque vertical actif, ce cerveau :
1. Lit les AUDIT.txt récents (ce qui a APPROVE/REVIEW/REJECT et pourquoi)
2. Lit les CdC passés (ce qui a été produit)
3. Lit les rapports de tendances de ce vertical
4. Génère le PROCHAIN CdC avec des ajustements basés sur les retours
5. Le soumet avec gate=pending → Hugo valide en 1 minute

Ce script remplace le besoin d'intervention manuelle de Claude pour
l'optimisation courante. Il apprend de chaque production.

Variables d'env :
  VERTICAL  — coloring|lowcontent|stl|roman|card_game|all (défaut: all)
  DRY_RUN   — si "1", affiche les recommandations sans générer de CdC
"""

import json
import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.lib.brain_utils import llm_call

ROOT = Path(__file__).resolve().parent.parent

# ── Configuration des verticaux ───────────────────────────────────────────────

VERTICALS = {
    "jeux_societe": {
        "products_dir": "products/jeux_societe",
        "brain_dir": "data/brain/jeux_societe",
        "cdc_script": "scripts/agent_jeux_societe_cdc.py",
        "cdc_env_vars": {
            "JEU_TYPE": "type_from_llm",
            "JEU_THEME": "theme_from_llm",
            "JEU_MECANIQUE": "mecanique_from_llm",
        },
        "audit_verdict_field": "VERDICT",
        "platform": "Etsy / DriveThruRPG / Itch.io",
        "product_description": "jeu de société print-and-play (cartes, plateau, party, éducatif, RPG)",
    },
    "coloring": {
        "products_dir": "products/coloring_books",
        "brain_dir": "data/brain/coloring",
        "cdc_script": "scripts/agent_coloring_cdc.py",
        "cdc_env_vars": {
            "COLORING_THEME": "theme_from_llm",
            "COLORING_AUDIENCE": "adult",
            "COLORING_PAGES": "30",
        },
        "audit_verdict_field": "VERDICT",
        "platform": "Amazon KDP",
        "product_description": "livre de coloriage adulte/enfant KDP",
    },
    "stl": {
        "products_dir": "products/stl_3d",
        "brain_dir": "data/brain/stl",
        "cdc_script": "scripts/agent_stl_cdc.py",
        "cdc_env_vars": {
            "STL_TYPE": "type_from_llm",
            "STL_NICHE": "niche_from_llm",
            "STL_NB_VARIANTES": "15",
        },
        "audit_verdict_field": "VERDICT",
        "platform": "Cults3D / Printables",
        "product_description": "fichier STL impression 3D",
    },
    "lowcontent": {
        "products_dir": "products/lowcontent_kdp",
        "brain_dir": "data/brain/lowcontent",
        "cdc_script": "scripts/agent_cdc_lowcontent.py",
        "cdc_env_vars": {
            "LC_TYPE": "type_from_llm",
            "LC_THEME": "theme_from_llm",
            "LC_AUDIENCE": "adults",
        },
        "audit_verdict_field": "VERDICT",
        "platform": "Amazon KDP",
        "product_description": "journal/planner low-content KDP",
    },
    "roman": {
        "products_dir": "products/novels",
        "brain_dir": "data/brain/roman",
        "cdc_script": "scripts/agent_cdc_roman.py",
        "cdc_env_vars": {
            "ROMAN_GENRE": "genre_from_llm",
            "ROMAN_SOUS_GENRE": "sous_genre_from_llm",
            "ROMAN_LANGUE": "en",
        },
        "audit_verdict_field": "VERDICT",
        "platform": "Amazon KDP",
        "product_description": "roman KDP eBook + paperback",
    },
    "merch_design": {
        "products_dir": "products/merch",
        "brain_dir": "data/brain/merch",
        "cdc_script": "scripts/agent_merch_design_cdc.py",
        "cdc_env_vars": {
            "MERCH_CONCEPT": "concept_from_llm",
            "MERCH_STYLE": "flat colorful illustration",
            "MERCH_NB_DESIGNS": "30",
            "MERCH_LANGUE": "en",
        },
        "audit_verdict_field": "VERDICT",
        "platform": "Redbubble / Merch by Amazon / Society6 / Etsy+Printful",
        "product_description": "collection de designs merch (t-shirts, mugs, stickers, posters)",
    },
    "godot_assets": {
        "products_dir": "products/godot_assets",
        "brain_dir": "data/brain/godot",
        "cdc_script": "scripts/agent_godot_cdc.py",
        "cdc_env_vars": {
            "GODOT_TYPE": "type_from_llm",
            "GODOT_THEME": "theme_from_llm",
            "GODOT_NB_ASSETS": "30",
        },
        "audit_verdict_field": "VERDICT",
        "platform": "Itch.io / Godot Asset Library",
        "product_description": "asset pack Godot 4 (sprites, tilesets, UI kits, shaders, addons)",
    },
}


def scan_audits(products_dir: Path) -> dict:
    """Lit tous les AUDIT.txt d'un vertical et extrait les résultats."""
    results = {
        "approve": [],
        "review": [],
        "reject": [],
        "pending": [],
        "no_audit": [],
    }

    if not products_dir.exists():
        return results

    for product_dir in sorted(products_dir.iterdir()):
        if not product_dir.is_dir():
            continue

        audit_path = product_dir / "AUDIT.txt"
        if not audit_path.exists():
            results["no_audit"].append(product_dir.name)
            continue

        content = audit_path.read_text(encoding="utf-8", errors="ignore")

        # Extraire le verdict
        verdict = "unknown"
        for line in content.splitlines():
            if line.startswith("VERDICT"):
                verdict = line.split(":")[-1].strip().upper()
                break

        # Extraire le score
        score = 0
        for line in content.splitlines():
            if line.startswith("Score"):
                try:
                    score = int(line.split(":")[1].strip().split("/")[0])
                except Exception:
                    pass
                break

        # Extraire les problèmes bloquants
        blocking = []
        in_blocking = False
        for line in content.splitlines():
            if "PROBLÈMES BLOQUANTS" in line or "BLOQUANT" in line.upper():
                in_blocking = True
            elif in_blocking and line.strip().startswith("✗"):
                blocking.append(line.strip()[1:].strip()[:120])
            elif in_blocking and line.strip() == "":
                in_blocking = False

        entry = {
            "name": product_dir.name,
            "score": score,
            "blocking": blocking[:3],
        }

        if verdict == "APPROVE":
            results["approve"].append(entry)
        elif verdict == "REVIEW":
            results["review"].append(entry)
        elif verdict == "REJECT":
            results["reject"].append(entry)
        elif verdict == "PENDING":
            results["pending"].append(entry)
        else:
            results["no_audit"].append(product_dir.name)

    return results


def read_trends(brain_dir: Path) -> str:
    """Lit le dernier rapport de tendances pour ce vertical."""
    brain_path = ROOT / brain_dir
    if not brain_path.exists():
        return "Aucun rapport de tendances disponible."

    reports = sorted(
        list(brain_path.glob("*.json")) + list(brain_path.glob("*.md")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not reports:
        return "Aucun rapport de tendances disponible."

    latest = reports[0]
    content = latest.read_text(encoding="utf-8", errors="ignore")
    return content[:2500]


def read_past_cdcs(products_dir: Path, max_cdcs: int = 5) -> list:
    """Lit les derniers CdC pour éviter les répétitions."""
    if not products_dir.exists():
        return []

    cdcs = []
    for d in sorted(products_dir.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        cdc_path = d / "cdc.json"
        if not cdc_path.exists():
            continue
        try:
            cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
            concept = cdc.get("concept", {})
            cdcs.append({
                "nom": d.name,
                "titre": concept.get("titre", concept.get("titre_principal", "?")),
                "theme": concept.get("theme", concept.get("genre_exact", "?")),
                "gate": cdc.get("gate_cdc", "?"),
            })
        except Exception:
            pass
        if len(cdcs) >= max_cdcs:
            break

    return cdcs


def optimize_vertical(vertical_name: str, config: dict, dry_run: bool = False) -> dict | None:
    """Analyse un vertical et génère une recommandation de prochain CdC."""
    today = date.today().isoformat()
    products_dir = ROOT / config["products_dir"]
    brain_dir = config["brain_dir"]

    print(f"\n[Optimizer] ── {vertical_name.upper()} ──────────────────")

    audit_results = scan_audits(products_dir)
    trends = read_trends(brain_dir)
    past_cdcs = read_past_cdcs(products_dir)

    n_approve = len(audit_results["approve"])
    n_review = len(audit_results["review"])
    n_reject = len(audit_results["reject"])
    n_pending = len(audit_results["pending"])
    n_total = n_approve + n_review + n_reject

    print(f"  Audits: {n_approve} APPROVE | {n_review} REVIEW | {n_reject} REJECT | {n_pending} en attente")

    if n_pending >= 2:
        print(f"  [SKIP] {n_pending} CdC déjà en attente de validation Hugo. Pas de nouveau CdC.")
        return None

    # Construire le contexte pour le LLM
    audit_summary = json.dumps(audit_results, ensure_ascii=False, indent=2)[:2000]
    past_cdcs_txt = json.dumps(past_cdcs, ensure_ascii=False, indent=2)

    system_prompt = f"""Tu es l'IA optimisatrice du vertical '{vertical_name}' ({config['product_description']}).

Tu as accès à :
1. Les résultats d'audit de tous les produits passés
2. Les tendances marché actuelles pour ce vertical
3. La liste des CdC déjà produits (à ne pas répéter)

Ta mission : analyser les données et recommander le PROCHAIN produit à créer,
en apprenant des succès et des échecs.

Plateforme cible : {config['platform']}
Type de produit : {config['product_description']}

FORMAT RÉPONSE — JSON STRICTEMENT :
{{
  "analyse": {{
    "ce_qui_a_marche": "...",
    "ce_qui_a_echoue": "raisons d'échec identifiées",
    "opportunite_detectee": "..."
  }},
  "prochain_cdc": {{
    "justification": "Pourquoi CE produit maintenant?",
    "parametres_cdc": {{
      "theme": "...",
      "type": "...",
      "niche": "...",
      "audience": "..."
    }},
    "priorite": "haute|normale|basse",
    "revenu_estime": "...",
    "risques": "..."
  }},
  "actions_a_eviter": ["...", "..."]
}}
JSON uniquement."""

    user_prompt = f"""Vertical : {vertical_name}

AUDITS RÉCENTS :
{audit_summary}

TENDANCES MARCHÉ :
{trends}

CdC DÉJÀ PRODUITS (ne pas répéter) :
{past_cdcs_txt}

Analyse ces données et recommande le prochain produit à créer.
Apprends des échecs (REJECT) et capitalise sur les succès (APPROVE)."""

    print(f"  Appel LLM pour analyse et recommandation...")
    response = llm_call("stratege", system_prompt, user_prompt, temperature=0.7, max_tokens=2000)

    if not response:
        print(f"  [ERREUR] LLM sans réponse pour {vertical_name}")
        return None

    clean = response.strip()
    if clean.startswith("```"):
        parts = clean.split("```")
        clean = parts[1][4:] if parts[1].startswith("json") else parts[1]
    clean = clean.strip()

    try:
        rec = json.loads(clean)
    except Exception as e:
        print(f"  [ERREUR] JSON invalide: {e}")
        return None

    prochain = rec.get("prochain_cdc", {})
    analyse = rec.get("analyse", {})
    params = prochain.get("parametres_cdc", {})

    print(f"  Analyse: {analyse.get('ce_qui_a_marche', '?')[:80]}")
    print(f"  Opportunité: {analyse.get('opportunite_detectee', '?')[:80]}")
    print(f"  Prochain: {params}")
    print(f"  Priorité: {prochain.get('priorite', '?')} | {prochain.get('justification', '')[:60]}")

    # Sauvegarder le rapport d'optimisation
    report_dir = ROOT / "data" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"rapport_optimizer_{vertical_name}_{today}.json"
    report_path.write_text(json.dumps({
        "date": today,
        "vertical": vertical_name,
        "recommendation": rec,
        "audit_summary": {
            "approve": n_approve,
            "review": n_review,
            "reject": n_reject,
        },
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    if dry_run:
        print(f"  [DRY RUN] Recommandation sauvegardée → {report_path}")
        return rec

    # Lancer la génération du CdC avec les paramètres recommandés
    print(f"  → Génération automatique du CdC...")
    cdc_script = ROOT / config["cdc_script"]
    if not cdc_script.exists():
        print(f"  [SKIP] Script CdC introuvable: {cdc_script}")
        return rec

    env = os.environ.copy()
    for env_key, default_val in config["cdc_env_vars"].items():
        # Mapper les paramètres LLM aux variables d'env
        if "merch_concept" in env_key.lower():
            env[env_key] = params.get("concept", params.get("theme", default_val))
        elif "godot_type" in env_key.lower():
            env[env_key] = params.get("type", params.get("type_asset", default_val))
        elif "theme" in env_key.lower():
            env[env_key] = params.get("theme", default_val)
        elif "type" in env_key.lower() or "lc_type" in env_key.lower():
            env[env_key] = params.get("type", default_val)
        elif "niche" in env_key.lower():
            env[env_key] = params.get("niche", default_val)
        elif "audience" in env_key.lower():
            env[env_key] = params.get("audience", default_val)
        elif "genre" in env_key.lower():
            env[env_key] = params.get("genre", params.get("theme", default_val))
        elif "sous_genre" in env_key.lower():
            env[env_key] = params.get("sous_genre", "contemporary")
        else:
            env[env_key] = default_val

    try:
        result = subprocess.run(
            [sys.executable, str(cdc_script)],
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(ROOT),
        )
        print(result.stdout[-500:] if result.stdout else "")
        if result.returncode != 0:
            print(f"  [ERREUR] CdC script: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] Script CdC trop lent")
    except Exception as e:
        print(f"  [ERREUR] Lancement CdC: {e}")

    return rec


def run():
    vertical = os.environ.get("VERTICAL", "all").lower()
    dry_run = os.environ.get("DRY_RUN", "0") == "1"

    print(f"[Optimizer] Vertical: {vertical} | Dry run: {dry_run}")
    print(f"[Optimizer] Date: {date.today().isoformat()}")

    targets = VERTICALS if vertical == "all" else {
        k: v for k, v in VERTICALS.items() if k == vertical
    }

    if not targets:
        print(f"[Optimizer] Vertical inconnu: {vertical}. Disponibles: {list(VERTICALS)}")
        sys.exit(1)

    results = {}
    for vname, config in targets.items():
        try:
            rec = optimize_vertical(vname, config, dry_run=dry_run)
            results[vname] = "ok" if rec else "skip"
        except Exception as e:
            print(f"  [ERREUR] {vname}: {e}")
            results[vname] = "error"

    print(f"\n[Optimizer] ✓ Terminé: {results}")
    print("[Optimizer] Rapports → data/reports/rapport_optimizer_*.json")
    print("[Optimizer] CdC générés avec gate=pending → Hugo valide sur GitHub")


if __name__ == "__main__":
    run()
