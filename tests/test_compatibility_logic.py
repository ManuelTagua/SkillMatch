"""Tests for the compatibility calculation logic in SkillMatch.

These tests verify that:
* The compatibility percentage never exceeds 100.
* A frontend React job vs a backend-oriented candidate yields a medium/low score.
* A perfect match yields close to 100.
* No match yields near 0.
* Duplicate skills in the input do not inflate the score.
* Unrelated skills do not increase the compatibility.
"""

from src.skillmatch.domain.services import extract_skills, calculate_compatibility


def test_score_never_exceeds_100():
    job = "Python Java C#"
    profile = "Python Java C# Java"  # duplicate skill
    offer_set, offer_cat = extract_skills(job)
    result = calculate_compatibility(offer_set, profile, offer_cat, {})
    assert 0 <= result.percentage <= 100


def test_frontend_vs_backend_candidate():
    job = "JavaScript React HTML CSS REST APIs Git TypeScript"
    profile = "Java Spring Boot Python MySQL GitHub Postman REST APIs HTML CSS"
    offer_set, offer_cat = extract_skills(job)
    result = calculate_compatibility(offer_set, profile, offer_cat, {})
    # Expect a medium/low compatibility (roughly 40-65%)
    assert 40 <= result.percentage <= 65
    # Matched skills should include Git, REST APIs, HTML, CSS
    for skill in ["git", "restapi", "html", "css"]:
        # REST APIs normalise to the single canonical "restapi" skill.
        # The extractor normalises to lower-case; ensure they appear in matched.
        assert skill in result.matched
    # Missing should contain javascript, react, typescript
    for missing in ["javascript", "react", "typescript"]:
        assert missing in result.missing


def test_perfect_match():
    job = "Python Flask Docker Git"
    profile = "Python Flask Docker Git"
    offer_set, offer_cat = extract_skills(job)
    result = calculate_compatibility(offer_set, profile, offer_cat, {})
    assert result.percentage >= 95
    assert set(result.matched) == set(offer_set.skills)
    assert result.missing == []


def test_no_match():
    job = "Java Springboot Docker"
    profile = "Python Flask Git"
    offer_set, offer_cat = extract_skills(job)
    result = calculate_compatibility(offer_set, profile, offer_cat, {})
    assert result.percentage <= 5
    assert result.matched == []
    # All required skills should be listed as missing
    for skill in offer_set.skills:
        assert skill in result.missing


def test_unrelated_skills_do_not_inflate_score():
    job = "React JavaScript HTML CSS"
    profile = "C++ Rust Go"
    offer_set, offer_cat = extract_skills(job)
    result = calculate_compatibility(offer_set, profile, offer_cat, {})
    assert result.percentage == 0
    assert result.matched == []
    for skill in offer_set.skills:
        assert skill in result.missing
