"""Tests for skill extraction and synonym/alias handling."""

import pathlib

import pytest

from src.skillmatch.domain.services import extract_skills
from src.skillmatch.config.settings import SKILL_ALIASES, SKILL_SYNONYMS

# Helper to load demo text
DEMO_DIR = pathlib.Path(__file__).parents[1] / "data" / "demo"

@pytest.mark.parametrize(
    "filename,expected",
    [
        (
            "junior_backend_java.txt",
            {
                "Programming Languages": ["java"],
                "Frameworks": ["springboot"],
                "Testing": ["junit"],
                "DevOps": ["docker"],
                "Databases": ["mysql", "postgresql"],
                "Tools": ["git"],
            },
        ),
        (
            "junior_python_developer.txt",
            {
                "Programming Languages": ["python"],
                "Frameworks": ["flask"],
                "Testing": ["pytest"],
                "Databases": ["postgresql"],
                "DevOps": ["docker"],
                "Tools": ["git"],
            },
        ),
    ],
)
def test_extraction_from_demo_files(filename: str, expected: dict):
    path = DEMO_DIR / filename
    text = path.read_text(encoding="utf-8")
    _, categories = extract_skills(text)
    # Only compare categories present in expected
    for cat, skills in expected.items():
        assert cat in categories
        # Order is not guaranteed – compare as sets
        assert set(categories[cat]) == set(skills)

def test_alias_handling():
    text = "I love JS and use Git for version control."
    _, cat = extract_skills(text)
    assert "javascript" in cat.get("Programming Languages", [])
    assert "git" in cat.get("Tools", [])

def test_synonym_partial_match():
    # Spring is a synonym of springboot; should be extracted as springboot
    text = "Experience with Spring framework."
    _, cat = extract_skills(text)
    # The canonical skill is springboot (mapped via alias/synonym handling)
    assert "springboot" in cat.get("Frameworks", [])

def test_empty_input():
    flat, cat = extract_skills("")
    assert flat.skills == []
    assert cat == {}

def test_duplicate_skills():
    text = "Python, python, PYTHON!"
    flat, cat = extract_skills(text)
    # Duplicates should be deduplicated
    assert flat.skills == ["python"]
    assert cat["Programming Languages"] == ["python"]
