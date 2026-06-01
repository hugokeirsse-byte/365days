#!/usr/bin/env python3
"""
Code Scout — recherche des bases de code open-source avant génération.

Pour chaque CdC approuvé, cherche sur GitHub et Godot Asset Library
des repos dont les mécaniques correspondent au projet. Le générateur
utilisera ces bases plutôt que d'écrire depuis zéro.

Variables d'env :
  PRODUCT_DIR   — répertoire du produit (products/mobile_games/...)
  GITHUB_TOKEN  — token API GitHub (optionnel, augmente limite à 5000 req/h)
  GEMINI_API_KEY / GROQ_API_KEY — LLM pour analyse pertinence
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.lib.brain_utils import llm_call, extract_json

# ── Licences open-source acceptables ─────────────────────────────────────────
OPEN_LICENSES = {"mit", "apache-2.0", "gpl-3.0", "cc0-1.0", "mpl-2.0", "bsd-2-clause", "bsd-3-clause", "lgpl-2.1", "lgpl-3.0"}

# ── Genres Godot ─────────────────────────────────────────────────────────────
GODOT_GENRES = {"text_rpg", "roguelike_text", "escape_puzzle", "sliding_puzzle", "puzzle_narrative", "turn_based_rpg"}


# ── Helpers HTTP ──────────────────────────────────────────────────────────────

def _http_get(url: str, headers: dict | None = None, timeout: int = 20) -> dict | list | None:
    """GET JSON from URL. Returns parsed JSON or None on error."""
    req_headers = {"User-Agent": "365days-code-scout/1.0", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            print(f"[CodeScout] Rate-limit {e.code} on {url[:80]} — waiting 10s and retrying once")
            time.sleep(10)
            try:
                req2 = urllib.request.Request(url, headers=req_headers)
                with urllib.request.urlopen(req2, timeout=timeout) as resp2:
                    return json.loads(resp2.read().decode("utf-8"))
            except Exception as e2:
                print(f"[CodeScout] Retry failed: {e2}")
                return None
        print(f"[CodeScout] HTTP {e.code} fetching {url[:80]}: {e}")
        return None
    except Exception as e:
        print(f"[CodeScout] Error fetching {url[:80]}: {e}")
        return None


# ── Étape 1 : Extraire les mécaniques via LLM ─────────────────────────────────

def extract_mechanics(cdc: dict) -> list[str]:
    """Utilise un LLM pour extraire les mécaniques techniques implémentables du CdC."""
    concept = cdc.get("concept", {})
    mvp = cdc.get("mvp_scope", {})

    genre = concept.get("genre", "")
    pitch = concept.get("pitch", "")
    gameplay_core = concept.get("gameplay_core", "")
    features = mvp.get("features_v1", [])

    system_prompt = (
        "You are a game developer analyzing a game design document. "
        "Extract the core technical mechanics that could be found as open-source implementations on GitHub. "
        "Focus on implementable systems, not abstract concepts. "
        "Return a JSON object with a single key 'mechanics' containing a list of 3-7 short technical search terms. "
        "Examples: 'inventory system', 'tile sliding puzzle', 'dialogue system', 'combat log', "
        "'room state machine', 'procedural dungeon', 'turn-based combat grid', 'save load system', "
        "'npc dialogue tree', 'pathfinding grid', 'card deck system'. "
        "Each term must be 2-4 words, in English, suitable for a GitHub search query."
    )

    user_prompt = (
        f"Game genre: {genre}\n"
        f"Pitch: {pitch}\n"
        f"Core gameplay: {gameplay_core}\n"
        f"V1 features: {', '.join(features[:8])}\n\n"
        "Extract 3-7 technical mechanics as short GitHub-searchable terms."
    )

    print("[CodeScout] Extracting mechanics via LLM...")
    raw = llm_call("code_scout", system_prompt, user_prompt, temperature=0.3, max_tokens=500, json_mode=True)

    if not raw:
        print("[CodeScout] LLM failed for mechanics extraction — using genre-based fallback")
        return _fallback_mechanics(genre, features)

    try:
        data = json.loads(extract_json(raw))
        mechanics = data.get("mechanics", [])
        if isinstance(mechanics, list) and mechanics:
            result = [str(m).strip() for m in mechanics if m and str(m).strip()][:7]
            print(f"[CodeScout] Mechanics extracted: {result}")
            return result
    except Exception as e:
        print(f"[CodeScout] Failed to parse LLM mechanics response: {e}")

    return _fallback_mechanics(genre, features)


def _fallback_mechanics(genre: str, features: list) -> list[str]:
    """Retourne des mécaniques par défaut selon le genre."""
    GENRE_MECHANICS = {
        "text_rpg": ["text rpg engine", "inventory system", "combat log", "dungeon generator"],
        "roguelike_text": ["roguelike engine", "procedural dungeon", "permadeath system", "combat log"],
        "escape_puzzle": ["escape room game", "inventory puzzle", "room state machine", "item combination"],
        "sliding_puzzle": ["sliding puzzle", "tile puzzle game", "15 puzzle solver", "puzzle board"],
        "puzzle_narrative": ["dialogue system", "inventory puzzle", "npc dialogue tree", "mystery game"],
        "turn_based_rpg": ["turn based combat", "tactical grid rpg", "unit movement grid", "combat system"],
    }
    base = GENRE_MECHANICS.get(genre, ["game engine", "inventory system", "save load system"])
    # Ajouter mécaniques tirées des features si disponibles
    extra = [f.lower() for f in features[:2] if len(f) > 4]
    return (base + extra)[:6]


# ── Étape 2 : Recherche GitHub ────────────────────────────────────────────────

def search_github(mechanics: list[str], is_godot: bool, github_token: str | None) -> list[dict]:
    """Cherche sur GitHub les repos pertinents pour chaque mécanique."""
    headers = {}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    all_repos: dict[str, dict] = {}  # full_name → repo data (dédupliqués)

    for mechanic in mechanics:
        if is_godot:
            query = f"{mechanic} godot game"
        else:
            query = f"{mechanic} game"

        import urllib.parse
        q_encoded = urllib.parse.quote(query)
        url = f"https://api.github.com/search/repositories?q={q_encoded}&sort=stars&order=desc&per_page=5"

        print(f"[CodeScout] GitHub search: '{query}'")
        data = _http_get(url, headers=headers)
        if not data or "items" not in data:
            continue

        for item in data.get("items", []):
            full_name = item.get("full_name", "")
            if not full_name or full_name in all_repos:
                continue

            # Filtrer par licence
            license_info = item.get("license") or {}
            license_key = (license_info.get("spdx_id") or license_info.get("key") or "").lower()
            if license_key and license_key not in OPEN_LICENSES:
                print(f"[CodeScout] Skipping {full_name} — license: {license_key}")
                continue

            # Filtrer par stars (minimum 10)
            stars = item.get("stargazers_count", 0)
            if stars < 10:
                continue

            all_repos[full_name] = {
                "name": item.get("name", ""),
                "full_name": full_name,
                "url": item.get("html_url", f"https://github.com/{full_name}"),
                "stars": stars,
                "license": license_key or "unknown",
                "description": (item.get("description") or "")[:300],
                "topics": item.get("topics", []),
                "language": item.get("language") or "",
            }

    # Trier par stars et garder les 10 meilleurs
    results = sorted(all_repos.values(), key=lambda r: r["stars"], reverse=True)[:10]
    print(f"[CodeScout] GitHub: {len(results)} repos found (after dedup + filter)")
    return results


# ── Étape 3 : Godot Asset Library ────────────────────────────────────────────

def search_godot_assets(mechanics: list[str]) -> list[dict]:
    """Cherche sur la Godot Asset Library les assets pertinents."""
    all_assets: dict[str, dict] = {}

    for mechanic in mechanics[:4]:  # Limiter à 4 termes pour éviter trop de requêtes
        import urllib.parse
        q_encoded = urllib.parse.quote(mechanic)
        url = f"https://godotengine.org/asset-library/api/asset?filter={q_encoded}&godot_version=4&max_results=3"

        print(f"[CodeScout] Godot Asset Library search: '{mechanic}'")
        data = _http_get(url, timeout=15)
        if not data:
            continue

        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("result", data.get("assets", []))

        for item in items:
            if not isinstance(item, dict):
                continue
            asset_id = str(item.get("asset_id", item.get("id", "")))
            if not asset_id or asset_id in all_assets:
                continue

            title = item.get("title", "")
            if not title:
                continue

            # Godot Asset Library : vérifier la licence si disponible
            cost = (item.get("cost") or "").lower()
            # cost vide ou "free" ou "GPL-3.0" etc. — on garde tout sauf commercial évident
            if "commercial" in cost or ("$" in cost and "0" not in cost):
                continue

            all_assets[asset_id] = {
                "name": title,
                "full_name": f"godot-asset/{asset_id}",
                "url": f"https://godotengine.org/asset-library/asset/{asset_id}",
                "stars": item.get("rating", 0),
                "license": cost or "free",
                "description": (item.get("description") or item.get("blurb") or "")[:300],
                "source": "godot_asset_library",
                "category": item.get("category", ""),
                "author": item.get("author", ""),
            }

    results = list(all_assets.values())[:3]
    print(f"[CodeScout] Godot Asset Library: {len(results)} assets found")
    return results


# ── Étape 4 : Analyse LLM de pertinence ──────────────────────────────────────

def analyze_relevance(cdc: dict, repos: list[dict]) -> list[dict]:
    """Analyse la pertinence de chaque repo via LLM et enrichit les données."""
    if not repos:
        return []

    concept = cdc.get("concept", {})
    mvp = cdc.get("mvp_scope", {})

    cdc_summary = {
        "genre": concept.get("genre", ""),
        "pitch": concept.get("pitch", ""),
        "gameplay_core": concept.get("gameplay_core", ""),
        "features_v1": mvp.get("features_v1", [])[:6],
    }

    repos_summary = [
        {
            "full_name": r.get("full_name", ""),
            "description": r.get("description", ""),
            "stars": r.get("stars", 0),
            "license": r.get("license", ""),
            "language": r.get("language", ""),
            "topics": r.get("topics", [])[:8],
            "source": r.get("source", "github"),
        }
        for r in repos
    ]

    system_prompt = (
        "You are a senior game developer evaluating open-source code bases for reuse. "
        "Analyze each repository and assess its relevance to the game project described. "
        "Return a JSON object with key 'evaluations', an array of objects with these fields:\n"
        "  - full_name: string (exactly as given)\n"
        "  - relevance_score: float 0.0-1.0 (how useful is this repo for implementing the game)\n"
        "  - relevant_mechanics: array of strings (which mechanics from this repo can be reused)\n"
        "  - key_files: array of strings (suggested filenames to focus on, e.g. 'inventory.gd')\n"
        "  - llm_summary: string (1-2 sentences in French explaining why/how to use it)\n"
        "Score 0.0 = completely irrelevant, 1.0 = perfect match. Be realistic."
    )

    user_prompt = (
        f"Game project:\n{json.dumps(cdc_summary, ensure_ascii=False, indent=2)}\n\n"
        f"Repos to evaluate:\n{json.dumps(repos_summary, ensure_ascii=False, indent=2)}\n\n"
        "Evaluate each repo's relevance for implementing this specific game."
    )

    print(f"[CodeScout] Analyzing relevance of {len(repos)} repos via LLM...")
    raw = llm_call("code_scout", system_prompt, user_prompt, temperature=0.2, max_tokens=3000, json_mode=True)

    if not raw:
        print("[CodeScout] LLM failed for relevance analysis — repos returned without scoring")
        for r in repos:
            r.setdefault("relevance_score", 0.0)
            r.setdefault("relevant_mechanics", [])
            r.setdefault("key_files", [])
            r.setdefault("llm_summary", "Analyse LLM non disponible.")
        return repos

    try:
        data = json.loads(extract_json(raw))
        evaluations = data.get("evaluations", [])

        # Merge evaluations back into repos
        eval_map = {e.get("full_name", ""): e for e in evaluations if isinstance(e, dict)}

        for repo in repos:
            fn = repo.get("full_name", "")
            ev = eval_map.get(fn, {})
            repo["relevance_score"] = float(ev.get("relevance_score", 0.0))
            repo["relevant_mechanics"] = ev.get("relevant_mechanics", [])
            repo["key_files"] = ev.get("key_files", [])
            repo["llm_summary"] = ev.get("llm_summary", "")

        # Trier par score
        repos.sort(key=lambda r: r.get("relevance_score", 0.0), reverse=True)
        print(f"[CodeScout] Relevance analysis done. Top score: {repos[0].get('relevance_score', 0):.2f}" if repos else "")
        return repos

    except Exception as e:
        print(f"[CodeScout] Failed to parse LLM relevance response: {e}")
        for r in repos:
            r.setdefault("relevance_score", 0.0)
            r.setdefault("relevant_mechanics", [])
            r.setdefault("key_files", [])
            r.setdefault("llm_summary", "Analyse LLM non disponible.")
        return repos


# ── Étape 5 : Générer les notes d'intégration ─────────────────────────────────

def generate_integration_notes(cdc: dict, repos: list[dict]) -> tuple[list[str], str]:
    """Génère recommended_bases et integration_notes via LLM."""
    # Repos avec score > 0.3
    good_repos = [r for r in repos if r.get("relevance_score", 0) >= 0.3]
    if not good_repos:
        return [], "Aucune base existante pertinente trouvée — générer from scratch."

    recommended = [r["full_name"] for r in good_repos[:3]]

    concept = cdc.get("concept", {})
    system_prompt = (
        "You are a game developer writing integration instructions. "
        "Write 2-4 concise sentences in French explaining which repos to use and how to integrate them. "
        "Be specific: mention file names, which mechanics to copy, what to adapt. "
        "Return a JSON object with key 'notes': string."
    )

    top_repos_info = [
        {
            "full_name": r["full_name"],
            "url": r["url"],
            "relevant_mechanics": r.get("relevant_mechanics", []),
            "key_files": r.get("key_files", []),
            "llm_summary": r.get("llm_summary", ""),
        }
        for r in good_repos[:3]
    ]

    user_prompt = (
        f"Game: {concept.get('titre', '')} ({concept.get('genre', '')})\n"
        f"Top repos:\n{json.dumps(top_repos_info, ensure_ascii=False, indent=2)}\n\n"
        "Write integration_notes: how to use these repos to build the game."
    )

    print("[CodeScout] Generating integration notes via LLM...")
    raw = llm_call("code_scout", system_prompt, user_prompt, temperature=0.4, max_tokens=600, json_mode=True)

    notes = ""
    if raw:
        try:
            data = json.loads(extract_json(raw))
            notes = data.get("notes", "")
        except Exception:
            pass

    if not notes:
        # Fallback manuel
        summaries = [r.get("llm_summary", r["full_name"]) for r in good_repos[:3]]
        notes = " | ".join(summaries)

    return recommended, notes


# ── Entry point ───────────────────────────────────────────────────────────────

def run():
    product_dir_env = os.environ.get("PRODUCT_DIR", "").strip()
    github_token = os.environ.get("GITHUB_TOKEN", "").strip() or None

    if not product_dir_env:
        print("[CodeScout] PRODUCT_DIR not set — nothing to do", file=sys.stderr)
        sys.exit(0)

    product_dir = ROOT / product_dir_env if not Path(product_dir_env).is_absolute() else Path(product_dir_env)

    if not product_dir.exists():
        print(f"[CodeScout] PRODUCT_DIR does not exist: {product_dir}", file=sys.stderr)
        sys.exit(0)

    cdc_path = product_dir / "cdc.json"
    if not cdc_path.exists():
        print(f"[CodeScout] cdc.json not found in {product_dir}", file=sys.stderr)
        sys.exit(0)

    try:
        cdc = json.loads(cdc_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[CodeScout] Failed to read cdc.json: {e}", file=sys.stderr)
        sys.exit(0)

    gate = cdc.get("gate_cdc", "pending")
    if gate != "approved":
        print(f"[CodeScout] gate_cdc={gate} — skipping code scout (only runs on approved CdC)")
        sys.exit(0)

    concept = cdc.get("concept", {})
    genre = concept.get("genre", "")
    is_godot = genre in GODOT_GENRES

    print(f"\n[CodeScout] === Code Scout ===")
    print(f"[CodeScout] Product: {product_dir.name}")
    print(f"[CodeScout] Genre: {genre} | Godot: {is_godot}")
    print(f"[CodeScout] GitHub token: {'yes' if github_token else 'no (rate limit 60 req/h)'}")

    output_path = product_dir / "code_scout_results.json"

    try:
        # ── 1. Extraire les mécaniques ──────────────────────────────────────────
        mechanics = extract_mechanics(cdc)

        # ── 2. Recherche GitHub ─────────────────────────────────────────────────
        github_repos = search_github(mechanics, is_godot, github_token)

        # ── 3. Godot Asset Library (si Godot) ───────────────────────────────────
        godot_assets = []
        if is_godot:
            godot_assets = search_godot_assets(mechanics)

        all_repos = github_repos + godot_assets

        # ── 4. Analyse LLM de pertinence ────────────────────────────────────────
        if all_repos:
            all_repos = analyze_relevance(cdc, all_repos)
        else:
            print("[CodeScout] No repos found — skipping LLM relevance analysis")

        # ── 5. Notes d'intégration ──────────────────────────────────────────────
        if all_repos:
            recommended_bases, integration_notes = generate_integration_notes(cdc, all_repos)
        else:
            recommended_bases = []
            integration_notes = "Aucune base existante trouvée — générer from scratch."

        # ── 6. Sauvegarder ──────────────────────────────────────────────────────
        result = {
            "searched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "product_dir": str(product_dir_env),
            "mechanics_extracted": mechanics,
            "repos_found": all_repos,
            "recommended_bases": recommended_bases,
            "integration_notes": integration_notes,
        }

        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"\n[CodeScout] ✓ Results saved: {output_path}")
        print(f"[CodeScout] Mechanics: {mechanics}")
        print(f"[CodeScout] Repos found: {len(all_repos)}")
        print(f"[CodeScout] Recommended bases: {recommended_bases}")

    except Exception as e:
        print(f"[CodeScout] Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Sauvegarder quand même un résultat minimal pour ne pas bloquer le générateur
        fallback = {
            "searched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "product_dir": str(product_dir_env),
            "mechanics_extracted": [],
            "repos_found": [],
            "recommended_bases": [],
            "integration_notes": "Aucune base existante trouvée — générer from scratch.",
            "error": str(e),
        }
        try:
            output_path.write_text(json.dumps(fallback, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[CodeScout] Fallback results saved: {output_path}")
        except Exception:
            pass


if __name__ == "__main__":
    run()
