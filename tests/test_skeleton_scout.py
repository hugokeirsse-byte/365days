"""Tests pour l'Agent #28 Skeleton Scout."""
from scripts.lib import skeleton_scout as ss


def test_gpl_rejected_despite_popularity():
    meta = ss.RepoMeta("x/popular-gpl", "GPL-3.0", 9000, "2026-04-01", fit=3,
                       has_tests=True, has_ci=True)
    ev = ss.evaluate_candidate(meta)
    assert ev.license_ok_commercial is False
    assert ev.verdict == "REJECT"


def test_mit_well_maintained_adopted():
    meta = ss.RepoMeta("x/great-kit", "MIT", 2000, "2026-04-01", fit=3,
                       has_tests=True, has_ci=True, has_docs=True)
    ev = ss.evaluate_candidate(meta, intent="full_skeleton")
    assert ev.verdict == "ADOPT"
    assert ev.score_total >= 12
    assert ev.recommended_integration_mode == "fork"


def test_improve_function_uses_mix():
    meta = ss.RepoMeta("x/snippet", "MIT", 1500, "2026-04-01", fit=3,
                       has_tests=True, has_ci=True)
    ev = ss.evaluate_candidate(meta, intent="improve_function")
    assert ev.verdict == "ADOPT_AS_MIX_PART"
    assert ev.recommended_integration_mode == "mix"


def test_abandoned_repo_low_maintenance_score():
    meta = ss.RepoMeta("x/dead", "MIT", 500, "2020-01-01", fit=2)
    ev = ss.evaluate_candidate(meta)
    assert ev.scores["maintenance"] == 0
    assert any("non maintenu" in r for r in ev.risks)


def test_report_sorted_and_combo():
    metas = [
        ss.RepoMeta("a/kit", "MIT", 1800, "2026-03-01", "Godot 4",
                    "offline earnings", has_tests=True, has_ci=True, fit=3),
        ss.RepoMeta("b/save", "Apache-2.0", 1200, "2026-02-01", "Godot 4",
                    "save system", has_tests=True, has_ci=True, fit=3),
        ss.RepoMeta("c/junk", "GPL-3.0", 100, "2019-01-01", "Godot 3", "ui", fit=1),
    ]
    report = ss.build_report("brief_test", metas, intent="improve_function")
    # Trié par score décroissant
    totals = [c["score_total"] for c in report["candidates"]]
    assert totals == sorted(totals, reverse=True)
    # Combo MIX recommandé car 2 ADOPT_AS_MIX_PART même engine
    assert "recommended_combo" in report
    assert report["recommended_combo"]["engine_consistent"] is True


def test_validate_brief_catches_missing():
    errors = ss.validate_brief({"intent": "full_skeleton"})
    assert errors  # manque id + target.description


def test_validate_brief_ok():
    brief = {"id": "brief_2026-05-20_x", "intent": "full_skeleton",
             "target": {"description": "idle game"}}
    assert ss.validate_brief(brief) == []
