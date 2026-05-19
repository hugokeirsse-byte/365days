"""Module 8 — Opportunist : scoring d'une niche selon scoring_matrix.json.

Lit `data/config/scoring_matrix.json` et applique la grille 6 critères.
Retourne un score normalisé /100 + verdict.

Aucun appel LLM.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORING_PATH = REPO_ROOT / "data" / "config" / "scoring_matrix.json"

CRITERIA_KEYS = (
    "demande",
    "concurrence_inversee",
    "marge_par_unite",
    "legalite",
    "effort_production",
    "levier_cross_canal",
)


@dataclass
class NicheScore:
    niche: str
    scores_raw: dict[str, int]
    total_pondere: float
    score_normalise_100: int
    verdict: str
    seuil_validation: int
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "niche": self.niche,
            "scores_raw": self.scores_raw,
            "total_pondere": round(self.total_pondere, 2),
            "score_normalise_100": self.score_normalise_100,
            "verdict": self.verdict,
            "seuil_validation": self.seuil_validation,
            "notes": self.notes,
        }


def _load_matrix() -> dict:
    return json.loads(SCORING_PATH.read_text(encoding="utf-8"))


def score_niche(niche: str, scores_raw: dict[str, int]) -> NicheScore:
    """Score une niche selon la matrice. `scores_raw` = {critere_id: 0-4}."""
    matrix = _load_matrix()
    criteria_by_id = {c["id"]: c for c in matrix["criteres"]}

    notes: list[str] = []
    total_pondere = 0.0
    max_theorique = 0.0

    for key in CRITERIA_KEYS:
        if key not in scores_raw:
            notes.append(f"Critère manquant : {key} — traité comme 0")
            score_val = 0
        else:
            score_val = int(scores_raw[key])
            if score_val < 0 or score_val > 4:
                notes.append(f"Score hors plage pour {key} : {score_val} — clampé")
                score_val = max(0, min(4, score_val))
        weight = criteria_by_id[key]["poids"]
        total_pondere += score_val * weight
        max_theorique += 4 * weight

    seuil = matrix["_seuil_validation"]
    score_norm = round((total_pondere / max_theorique) * 100)

    if total_pondere >= seuil:
        verdict = "VALIDE"
    elif total_pondere >= seuil * 0.85:
        verdict = "BORDERLINE — à revoir manuellement"
    else:
        verdict = "REJETE"

    # Veto légal : si legalite == 0, automatiquement REJETE
    if scores_raw.get("legalite", 0) == 0:
        verdict = "REJETE — VETO LEGAL"
        notes.append("Veto légal absolu : la niche ne peut pas être produite")

    return NicheScore(
        niche=niche,
        scores_raw={k: int(scores_raw.get(k, 0)) for k in CRITERIA_KEYS},
        total_pondere=total_pondere,
        score_normalise_100=score_norm,
        verdict=verdict,
        seuil_validation=seuil,
        notes=notes,
    )


def rank_niches(candidates: list[dict]) -> list[NicheScore]:
    """Trie une liste de candidats par score décroissant.

    Chaque candidat = {"niche": "...", "scores": {critere: 0-4}}.
    """
    results = [score_niche(c["niche"], c["scores"]) for c in candidates]
    results.sort(key=lambda r: r.score_normalise_100, reverse=True)
    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python -m scripts.lib.niche_scorer "
            "'{\"niche\": \"X\", \"scores\": {\"demande\":3,...}}'",
            file=sys.stderr,
        )
        sys.exit(2)
    payload = json.loads(sys.argv[1])
    result = score_niche(payload["niche"], payload["scores"])
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    sys.exit(0 if result.verdict.startswith("VALIDE") else 1)
