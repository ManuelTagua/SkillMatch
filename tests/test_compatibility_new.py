"""Additional compatibility tests for the revised algorithm."""

from src.skillmatch.domain.services import extract_skills, calculate_compatibility


def _run(job: str, profile: str):
    offer_set, offer_cat = extract_skills(job)
    return calculate_compatibility(offer_set, profile, offer_cat, {})


def test_frontend_backend_mismatch():
    job = "JavaScript React HTML CSS REST APIs Git TypeScript"
    profile = "Java Spring Boot Python MySQL GitHub Postman REST APIs HTML CSS"
    result = _run(job, profile)
    assert 40 <= result.percentage <= 70
    for missing in ["javascript", "react", "typescript"]:
        assert missing in result.missing
    for skill in ["git", "restapi", "html", "css"]:
        # REST APIs normalise to the single canonical "restapi" skill.
        assert skill in result.matched


def test_perfect_match_range():
    job = "Python Flask Docker Git"
    profile = "Python Flask Docker Git"
    result = _run(job, profile)
    assert 90 <= result.percentage <= 100
    assert result.missing == []


def test_no_match_range():
    job = "Java Springboot Docker"
    profile = "Python Flask Git"
    result = _run(job, profile)
    assert 0 <= result.percentage <= 20
    assert result.matched == []


def test_duplicate_skills_not_inflate():
    job = "Python Java C#"
    profile = "Python Java C# Python"
    result = _run(job, profile)
    assert result.percentage == 100
    assert len(result.matched) == 3
    assert result.missing == []
