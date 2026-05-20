"""Tests pour l'Opportunist / niche scorer (Module 8)."""
from scripts.lib import niche_scorer as ns


def _full(demande=3, conc=3, marge=3, legal=3, effort=3, levier=3):
    return {
        "demande": demande,
        "concurrence_inversee": conc,
        "marge_par_unite": marge,
        "legalite": legal,
        "effort_production": effort,
        "levier_cross_canal": levier,
    }


def test_strong_niche_validated():
    r = ns.score_niche("Köhler plants", _full(4, 3, 3, 4, 4, 4))
    assert r.verdict == "VALIDE"
    assert r.score_normalise_100 >= 75


def test_legal_veto():
    r = ns.score_niche("Mickey coloring", _full(4, 1, 3, 0, 4, 4))
    assert "VETO" in r.verdict
    assert r.verdict.startswith("REJETE")


def test_weak_niche_rejected():
    r = ns.score_niche("Saturated audio packs", _full(1, 1, 1, 3, 1, 1))
    assert r.verdict == "REJETE"


def test_score_normalized_range():
    r = ns.score_niche("max", _full(4, 4, 4, 4, 4, 4))
    assert r.score_normalise_100 == 100


def test_missing_criterion_treated_as_zero():
    r = ns.score_niche("incomplete", {"demande": 4})
    assert r.scores_raw["legalite"] == 0
    assert any("manquant" in n for n in r.notes)


def test_out_of_range_clamped():
    r = ns.score_niche("weird", _full(demande=9, legal=2))
    assert r.scores_raw["demande"] == 4


def test_ranking_orders_desc():
    candidates = [
        {"niche": "weak", "scores": _full(1, 1, 1, 3, 1, 1)},
        {"niche": "strong", "scores": _full(4, 4, 4, 4, 4, 4)},
        {"niche": "mid", "scores": _full(2, 2, 2, 3, 2, 2)},
    ]
    ranked = ns.rank_niches(candidates)
    assert ranked[0].niche == "strong"
    assert ranked[-1].niche == "weak"
