"""Agent #28 — Skeleton Scout (Chasseur de squelettes de code).

On lui donne un CodeSearchBrief (type de projet OU fonction à améliorer +
contraintes), il recherche sur GitHub (+ web), évalue chaque candidat selon la
grille 6 critères /18 de LIBRARIES_AND_REPOS.md, et retourne un
SkeletonCandidateReport prêt à présenter à Hugo (gate Module S) ou à exploiter.

Implémentation des appels GitHub déférée (comme llm_router) : la recherche
réelle utilise l'API GitHub au runtime (token GITHUB_TOKEN) ou les outils MCP
github. Ce module fournit :
  - la validation du brief
  - la grille de scoring déterministe (testable sans réseau)
  - la logique de verdict + recommandation de mode d'intégration + combo MIX

Aucun secret dans le code.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_LICENSE_ALLOW = {
    "MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "CC0-1.0", "Unlicense",
}
DEFAULT_LICENSE_BLOCK = {
    "GPL-3.0", "GPL-2.0", "AGPL-3.0", "CC-BY-NC-4.0", "CC-BY-NC-SA-4.0",
}

ADOPT_THRESHOLD = 12  # /18


@dataclass
class RepoMeta:
    """Métadonnées brutes d'un repo (remplies par la couche de recherche GitHub)."""
    repo: str
    license: str
    stars: int
    last_pushed: str  # YYYY-MM-DD
    engine_or_stack: str = "any"
    what_it_provides: str = ""
    has_tests: bool = False
    has_ci: bool = False
    has_docs: bool = False
    has_types: bool = False
    heavy_deps: bool = False
    fit: int = 2  # 0-3, estimé par la couche recherche / LLM


def license_ok(license_id: str, allow: set[str], block: set[str]) -> bool:
    if license_id in block:
        return False
    return license_id in allow


def _score_license(license_id: str, allow: set[str], block: set[str]) -> int:
    if license_id in block:
        return 0
    if license_id in {"MIT", "BSD-3-Clause", "BSD-2-Clause", "CC0-1.0", "Unlicense"}:
        return 3
    if license_id == "Apache-2.0":
        return 2
    if license_id.startswith("LGPL"):
        return 1
    return 0


def _score_maintenance(last_pushed: str) -> int:
    try:
        pushed = date.fromisoformat(last_pushed)
    except ValueError:
        return 0
    days = (date.today() - pushed).days
    if days <= 90:
        return 3
    if days <= 365:
        return 2
    if days <= 730:
        return 1
    return 0


def _score_popularity(stars: int) -> int:
    if stars > 10000:
        return 3
    if stars >= 1000:
        return 2
    if stars >= 100:
        return 1
    return 0


def _score_quality(meta: RepoMeta) -> int:
    score = 0
    if meta.has_tests:
        score += 1
    if meta.has_ci:
        score += 1
    if meta.has_docs or meta.has_types:
        score += 1
    return min(score, 3)


def _score_lightness(meta: RepoMeta) -> int:
    return 1 if meta.heavy_deps else 3


@dataclass
class CandidateEvaluation:
    repo: str
    license: str
    license_ok_commercial: bool
    stars: int
    last_pushed: str
    engine_or_stack: str
    what_it_provides: str
    scores: dict[str, int]
    score_total: int
    recommended_integration_mode: str
    verdict: str
    risks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "repo": self.repo,
            "license": self.license,
            "license_ok_commercial": self.license_ok_commercial,
            "stars": self.stars,
            "last_pushed": self.last_pushed,
            "engine_or_stack": self.engine_or_stack,
            "what_it_provides": self.what_it_provides,
            "scores": self.scores,
            "score_total": self.score_total,
            "recommended_integration_mode": self.recommended_integration_mode,
            "verdict": self.verdict,
            "risks": self.risks,
        }


def evaluate_candidate(
    meta: RepoMeta,
    intent: str = "full_skeleton",
    allow: set[str] | None = None,
    block: set[str] | None = None,
) -> CandidateEvaluation:
    """Évalue un repo candidat selon la grille 6 critères /18."""
    allow = allow or DEFAULT_LICENSE_ALLOW
    block = block or DEFAULT_LICENSE_BLOCK

    scores = {
        "license": _score_license(meta.license, allow, block),
        "maintenance": _score_maintenance(meta.last_pushed),
        "popularite": _score_popularity(meta.stars),
        "qualite_code": _score_quality(meta),
        "fit_besoin": max(0, min(3, meta.fit)),
        "legerete_deps": _score_lightness(meta),
    }
    total = sum(scores.values())
    lic_ok = license_ok(meta.license, allow, block)

    risks: list[str] = []
    if not lic_ok:
        risks.append(f"License '{meta.license}' interdite pour usage commercial")
    if scores["maintenance"] == 0:
        risks.append("Repo non maintenu (dernier commit > 2 ans)")
    if not meta.has_tests:
        risks.append("Pas de tests visibles")

    # Verdict
    if not lic_ok:
        verdict = "REJECT"
    elif total >= ADOPT_THRESHOLD:
        verdict = "ADOPT" if intent == "full_skeleton" else "ADOPT_AS_MIX_PART"
    elif total >= ADOPT_THRESHOLD - 3:
        verdict = "INSPIRE_ONLY"
    else:
        verdict = "REJECT"

    # Mode d'intégration recommandé
    if intent == "improve_function":
        mode = "mix" if verdict == "ADOPT_AS_MIX_PART" else "inspire"
    elif intent == "find_library":
        mode = "depend"
    elif verdict == "ADOPT":
        mode = "fork"
    else:
        mode = "inspire"

    return CandidateEvaluation(
        repo=meta.repo,
        license=meta.license,
        license_ok_commercial=lic_ok,
        stars=meta.stars,
        last_pushed=meta.last_pushed,
        engine_or_stack=meta.engine_or_stack,
        what_it_provides=meta.what_it_provides,
        scores=scores,
        score_total=total,
        recommended_integration_mode=mode,
        verdict=verdict,
        risks=risks,
    )


def build_report(
    brief_id: str,
    candidates_meta: list[RepoMeta],
    intent: str = "full_skeleton",
    allow: set[str] | None = None,
    block: set[str] | None = None,
    needs_hugo_decision: bool = False,
) -> dict:
    """Construit le SkeletonCandidateReport (conforme au schéma)."""
    evals = [
        evaluate_candidate(m, intent=intent, allow=allow, block=block)
        for m in candidates_meta
    ]
    evals.sort(key=lambda e: e.score_total, reverse=True)

    report = {
        "brief_id": brief_id,
        "candidates": [e.to_dict() for e in evals],
        "needs_hugo_decision": needs_hugo_decision,
    }

    # Combo MIX recommandé : si plusieurs ADOPT_AS_MIX_PART de même engine + licences compatibles
    mix_parts = [e for e in evals if e.verdict == "ADOPT_AS_MIX_PART"]
    if len(mix_parts) >= 2:
        engines = {e.engine_or_stack for e in mix_parts}
        report["recommended_combo"] = {
            "base_repo": mix_parts[0].repo,
            "mix_parts": [{"repo": e.repo, "part": e.what_it_provides} for e in mix_parts[1:]],
            "license_compatibility_ok": all(e.license_ok_commercial for e in mix_parts),
            "engine_consistent": len(engines) == 1,
        }

    return report


def validate_brief(brief: dict) -> list[str]:
    """Validation minimale d'un CodeSearchBrief (sans jsonschema)."""
    errors: list[str] = []
    if "id" not in brief:
        errors.append("champ 'id' manquant")
    if brief.get("intent") not in {"full_skeleton", "improve_function", "find_assets", "find_library"}:
        errors.append("champ 'intent' invalide")
    if "target" not in brief or "description" not in brief.get("target", {}):
        errors.append("champ 'target.description' manquant")
    return errors


if __name__ == "__main__":
    # Démo offline : évalue 3 candidats fictifs pour un brief idle game.
    demo = [
        RepoMeta("foo/godot-idle-kit", "MIT", 1800, "2026-03-01", "Godot 4",
                 "offline earnings + prestige", has_tests=True, has_ci=True, fit=3),
        RepoMeta("bar/incremental-save", "Apache-2.0", 420, "2025-11-10", "Godot 4",
                 "save/load system", has_tests=False, fit=2),
        RepoMeta("baz/old-clicker", "GPL-3.0", 6000, "2021-01-01", "Godot 3",
                 "clicker UI", heavy_deps=True, fit=1),
    ]
    report = build_report("brief_2026-05-20_idle_demo", demo,
                          intent="improve_function", needs_hugo_decision=True)
    print(json.dumps(report, indent=2, ensure_ascii=False))
