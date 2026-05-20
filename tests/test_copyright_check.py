"""Tests pour le Censeur Copyright (Module 19)."""
from scripts.lib import copyright_check as cc


def test_disney_blocked():
    verdict = cc.check_asset(title="Disney Princess Coloring Book")
    assert verdict.passed is False
    assert verdict.matched_blacklist_patterns


def test_mickey_blocked():
    verdict = cc.check_asset(title="Mickey Mouse Fun Pages")
    assert verdict.passed is False


def test_elsa_frozen_blocked():
    verdict = cc.check_asset(description="A magical Elsa Frozen adventure")
    assert verdict.passed is False


def test_marvel_blocked():
    verdict = cc.check_asset(title="Spider-Man Web Slinger")
    assert verdict.passed is False


def test_clean_title_passes():
    verdict = cc.check_asset(
        title="Köhler Medicinal Plants Heritage Coloring",
        description="100 botanical illustrations to color",
    )
    assert verdict.passed is True
    assert not verdict.matched_blacklist_patterns


def test_known_pd_parent_passes():
    verdict = cc.check_asset(
        title="Forgotten Heroes Babies",
        parents_pd=["stardust_super_wizard", "phantom_lady_quality"],
    )
    # Parents whitelistés → pas de unknown
    assert verdict.unknown_pd_parents == []


def test_unknown_pd_parent_flagged():
    verdict = cc.check_asset(
        title="Mystery Hero",
        parents_pd=["some_random_unverified_character"],
    )
    assert "some_random_unverified_character" in verdict.unknown_pd_parents
    assert verdict.passed is False


def test_empty_input_passes():
    verdict = cc.check_asset()
    assert verdict.passed is True


def test_keywords_scanned():
    verdict = cc.check_asset(title="Cute animals", keywords=["pokemon", "pikachu"])
    assert verdict.passed is False
