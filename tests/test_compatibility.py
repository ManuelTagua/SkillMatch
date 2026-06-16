"""Tests for the compatibility calculation logic."""

import pathlib

from src.skillmatch.domain.services import extract_skills, calculate_compatibility
from src.skillmatch.domain.entities import CompatibilityResult

DEMO_DIR = pathlib.Path(__file__).parents[1] / "data" / "demo"

def _load(name: str) -> str:
    return (DEMO_DIR / name).read_text(encoding="utf-8")

def test_compatibility_result_construction():
    """Test that CompatibilityResult can be constructed with all required fields."""
    result = CompatibilityResult(
        percentage=50,
        matched=['skill1'],
        weak=['skill2'],
        missing=['skill3'],
        recommendations=['Learn skill3']
    )
    assert result.percentage == 50
    assert result.matched == ['skill1']
    assert result.weak == ['skill2']
    assert result.missing == ['skill3']
    assert result.recommendations == ['Learn skill3']


def test_react_not_matched_when_not_worked():
    """Test that React is not matched when candidate says 'not worked deeply with React'."""
    job_text = "React Git REST APIs"
    profile_text = '''I have strong experience with Java, Spring Boot, and REST APIs. 
I also have Git and Docker experience. 
I have basic knowledge of HTML and CSS, but I have not worked deeply with React, TypeScript or modern frontend frameworks.
JavaScript is not in my main skill set.
I know MySQL and some Redis.'''
    
    offer_set, offer_cat = extract_skills(job_text)
    result = calculate_compatibility(offer_set, profile_text, offer_cat, {})
    
    # React should NOT be in matched skills
    assert 'react' not in result.matched, f"React should not be matched, but matched={result.matched}"
    assert 'react' in result.missing


def test_typescript_not_matched_when_not_worked():
    """Test that TypeScript is not matched when candidate says 'not worked deeply with TypeScript'."""
    job_text = "TypeScript Git REST APIs"
    profile_text = '''I have strong experience with Java, Spring Boot, and REST APIs. 
I also have Git and Docker experience. 
I have basic knowledge of HTML and CSS, but I have not worked deeply with React, TypeScript or modern frontend frameworks.
JavaScript is not in my main skill set.
I know MySQL and some Redis.'''
    
    offer_set, offer_cat = extract_skills(job_text)
    result = calculate_compatibility(offer_set, profile_text, offer_cat, {})
    
    # TypeScript should NOT be in matched skills
    assert 'typescript' not in result.matched, f"TypeScript should not be matched, but matched={result.matched}"
    assert 'typescript' in result.missing


def test_html_css_weak_when_basic_knowledge():
    """Test that HTML and CSS count as weak when candidate says 'basic knowledge of HTML and CSS'."""
    job_text = "HTML CSS React"
    profile_text = '''I have basic knowledge of HTML and CSS, but I have not worked deeply with React or modern frontend frameworks.'''
    
    offer_set, offer_cat = extract_skills(job_text)
    result = calculate_compatibility(offer_set, profile_text, offer_cat, {})
    
    assert 'html' in result.weak
    assert 'css' in result.weak
    assert 'html' not in result.matched
    assert 'css' not in result.matched


def test_score_never_exceeds_100():
    """Test that compatibility score never exceeds 100%."""
    job_text = _load("junior_backend_java.txt")
    profile_text = '''I have strong experience with Java, Spring Boot, REST APIs, Git, Docker, MySQL, PostgreSQL, JUnit, and everything else.'''
    
    offer_set, offer_cat = extract_skills(job_text)
    result = calculate_compatibility(offer_set, profile_text, offer_cat, {})
    
    assert 0 <= result.percentage <= 100, f"Score should be 0-100, but got {result.percentage}"


def test_score_reasonable_for_contextual_frontend_candidate():
    """Test the requested contextual matching scenario."""
    job_text = "JavaScript React HTML CSS REST APIs Git TypeScript"
    profile_text = '''I have strong experience with Java, Spring Boot, and REST APIs. 
I also have Git and Docker experience. 
I have basic knowledge of HTML and CSS, but I have not worked deeply with React, TypeScript or modern frontend frameworks.
JavaScript is not in my main skill set.
I know MySQL and some Redis.'''
    
    offer_set, offer_cat = extract_skills(job_text)
    result = calculate_compatibility(offer_set, profile_text, offer_cat, {})
    
    for skill in ['git', 'restapi']:
        assert skill in result.matched
    for skill in ['html', 'css']:
        assert skill in result.weak
    for skill in ['react', 'typescript', 'javascript']:
        assert skill not in result.matched
        assert skill in result.missing
    assert 40 <= result.percentage <= 60, f"Score should be around 40-60%, but got {result.percentage}%"


def test_basic_knowledge_of_javascript_is_weak():
    offer_set, offer_cat = extract_skills("JavaScript")
    result = calculate_compatibility(
        offer_set,
        "I have basic knowledge of JavaScript.",
        offer_cat,
        {},
    )
    assert result.matched == []
    assert result.weak == ["javascript"]
    assert result.missing == []


def test_some_experience_with_react_is_weak():
    offer_set, offer_cat = extract_skills("React")
    result = calculate_compatibility(
        offer_set,
        "I have some experience with React.",
        offer_cat,
        {},
    )
    assert result.matched == []
    assert result.weak == ["react"]
    assert result.missing == []


def test_not_worked_deeply_with_react_is_missing():
    offer_set, offer_cat = extract_skills("React")
    result = calculate_compatibility(
        offer_set,
        "I have not worked deeply with React.",
        offer_cat,
        {},
    )
    assert result.matched == []
    assert result.weak == []
    assert result.missing == ["react"]


def test_git_and_rest_apis_are_strong_single_concept():
    offer_set, offer_cat = extract_skills("Git REST APIs")
    result = calculate_compatibility(
        offer_set,
        "I worked with Git and REST APIs.",
        offer_cat,
        {},
    )
    assert offer_set.skills == ["git", "restapi"]
    assert result.matched == ["git", "restapi"]
    assert result.weak == []
    assert result.missing == []


def test_empty_inputs():
    """Test that empty inputs result in 0% compatibility."""
    offer_set, offer_cat = extract_skills("")
    profile_text = ""
    result = calculate_compatibility(offer_set, profile_text, offer_cat, {})
    assert result.percentage == 0
    assert result.matched == []
    assert result.missing == []
    assert result.recommendations == []


def test_no_duplicated_skills_in_score():
    """Test that duplicated skills do not inflate the score."""
    job_text = "Java Java Java Spring Spring REST APIs REST APIs"
    profile_text = "Java Spring REST APIs"
    
    offer_set, offer_cat = extract_skills(job_text)
    result = calculate_compatibility(offer_set, profile_text, offer_cat, {})
    
    assert result.percentage == 100
    assert result.matched == ["java", "restapi", "springboot"]


def test_matched_and_missing_disjoint():
    """Test that matched and missing skills are disjoint (no overlaps)."""
    job_text = _load("junior_backend_java.txt")
    profile_text = _load("junior_python_developer.txt")
    
    offer_set, offer_cat = extract_skills(job_text)
    result = calculate_compatibility(offer_set, profile_text, offer_cat, {})
    
    # Matched and missing should be disjoint
    overlap = set(result.matched).intersection(set(result.missing))
    assert not overlap, f"Matched and missing have overlap: {overlap}"
