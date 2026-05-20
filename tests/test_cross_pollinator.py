"""Tests pour l'Arbitragiste Cross-canal (Module 10)."""
from scripts.lib import cross_pollinator as cp


def test_domain_public_plan():
    plan = cp.plan_pollination("domain_public_acquisition", "Köhler plants")
    assert plan.primary_pipeline == "produce_coloring_book"
    assert "produce_merch_batch" in plan.cascade_pipelines
    assert plan.brand_id == "heritage_coloring"


def test_progeny_plan():
    plan = cp.plan_pollination("progeny_combo_validated", "baby heroes")
    assert plan.primary_pipeline == "produce_progeny_pack"
    assert plan.brand_id == "iconic_offspring"


def test_primary_not_duplicated_in_cascade():
    plan = cp.plan_pollination("merch_tshirt_bestseller", "vintage botanical")
    assert plan.primary_pipeline not in plan.cascade_pipelines


def test_exclude_pipelines():
    plan = cp.plan_pollination(
        "domain_public_acquisition",
        "Audubon birds",
        exclude_pipelines=["produce_merch_batch"],
    )
    assert "produce_merch_batch" not in plan.cascade_pipelines


def test_brand_override():
    plan = cp.plan_pollination("pinterest_trend", "cottagecore", brand_id="modern_cozy")
    assert plan.brand_id == "modern_cozy"


def test_unknown_signal_safe_default():
    plan = cp.plan_pollination("unknown_signal_xyz", "whatever")
    # Pas de crash, cascade vide, brand par défaut
    assert plan.cascade_pipelines == []
    assert plan.brand_id == "modern_cozy"
