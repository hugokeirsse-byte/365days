"""Tests pour l'Anti-Slop Textuel (Module 20)."""
from scripts.lib import anti_slop_text as slop


def test_unleash_detected():
    v = slop.check_text("Unleash your creativity today")
    assert v.passed is False
    assert v.lexical_hits


def test_tapestry_detected():
    v = slop.check_text("A rich tapestry of designs")
    assert v.passed is False


def test_dive_into_detected():
    v = slop.check_text("Dive into this whimsical journey")
    assert v.passed is False


def test_prompt_leak_detected():
    v = slop.check_text("Here is the description. Let me know if you'd like changes.")
    assert v.passed is False
    assert v.prompt_leaks


def test_as_an_ai_leak():
    v = slop.check_text("As an AI language model, I cannot do that.")
    assert v.passed is False
    assert v.prompt_leaks


def test_clean_text_passes():
    v = slop.check_text("100 botanical plants to color, printed on thick paper.")
    assert v.passed is True
    assert not v.lexical_hits
    assert not v.prompt_leaks


def test_empty_passes():
    assert slop.check_text("").passed is True
    assert slop.check_text("   ").passed is True


def test_metadata_bundle_aggregates():
    v = slop.check_metadata_bundle(
        title="Botanical Coloring",
        description="Discover the magical world of plants",
        bullets=["thick paper", "100 pages"],
    )
    # "Discover the" est une signature
    assert v.passed is False
