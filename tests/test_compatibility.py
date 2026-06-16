"""Tests for the compatibility calculation logic."""

import pathlib

import pytest

from src.skillmatch.domain.services import extract_skills, calculate_compatibility

DEMO_DIR = pathlib.Path(__file__).parents[1] / "data" / "demo"

def _load(name: str) -> str:
    return (DEMO_DIR / name).read_text(encoding="utf-8")

@pytest.mark.parametrize(
    "job_file,profile_file,expected_range",
    [
        ("junior_backend_java.txt", "manuel_profile.txt", (70, 100)),
        ("junior_python_developer.txt", "manuel_profile.txt", (50, 90)),
    ],
)
def test_compatibility_score(job_file: str, profile_file: str, expected_range: tuple):
    job_text = _load(job_file)
    profile_text = _load(profile_file)
    offer_set, offer_cat = extract_skills(job_text)
    profile_set, profile_cat = extract_skills(profile_text)
    result = calculate_compatibility(offer_set, profile_set, offer_cat, profile_cat)
    # Ensure a percentage within a plausible range for the demo data
    assert expected_range[0] <= result.percentage <= expected_range[1]
    # Matched and missing should be disjoint
    assert set(result.matched).isdisjoint(set(result.missing))
    # Recommendations should not be empty when there are missing skills
    if result.missing:
        assert result.recommendations

def test_empty_inputs():
    offer_set, offer_cat = extract_skills("")
    profile_set, profile_cat = extract_skills("")
    result = calculate_compatibility(offer_set, profile_set, offer_cat, profile_cat)
    assert result.percentage == 0
    assert result.matched == []
    assert result.missing == []
    assert result.recommendations == []
