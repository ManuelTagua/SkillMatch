"""Tests for deterministic scoring of AI-extracted data."""

from src.skillmatch.ai.schemas import (
    AICandidateExtraction,
    AICandidateSkill,
    AIJobExtraction,
    AIRequiredSkill,
)
from src.skillmatch.ai.scoring import score_ai_compatibility


def test_required_years_turn_skill_into_partial_match():
    job = AIJobExtraction(
        role_title="Java Backend Developer",
        seniority="mid",
        required_total_experience_years=4,
        required_skills=[
            AIRequiredSkill(
                name="Java",
                importance="required",
                years_required=4,
                category="Programming Languages",
            )
        ],
    )
    candidate = AICandidateExtraction(
        estimated_total_experience_months=4,
        estimated_seniority="junior",
        skills=[
            AICandidateSkill(
                name="Java",
                level="junior",
                evidence="projects and internships",
                estimated_years=0.5,
                category="Programming Languages",
            )
        ],
    )

    result = score_ai_compatibility(job, candidate)

    assert result.strong_skills == []
    assert result.weak_skills == ["Java"]
    assert result.missing_skills == []
    assert result.skills_score == 65
    assert result.experience_score == 35
    assert 40 <= result.final_score <= 60
    assert result.candidate_seniority == "Junior"
    assert result.role_seniority == "Mid"
    assert result.required_experience_years == 4
    assert result.detected_experience_years == 0.5
    assert any("4 years of Java experience" in sentence for sentence in result.why_sentences)
    assert any("internship-level and project-level" in sentence for sentence in result.why_sentences)


def test_unknown_technology_can_match_dynamically():
    job = AIJobExtraction(
        required_skills=[
            AIRequiredSkill(
                name="Kafka Streams",
                importance="required",
                category="Tools",
            )
        ],
    )
    candidate = AICandidateExtraction(
        skills=[
            AICandidateSkill(
                name="Kafka Streams",
                level="senior",
                estimated_years=3,
                category="Tools",
            )
        ],
    )

    result = score_ai_compatibility(job, candidate)

    assert result.strong_skills == ["Kafka Streams"]
    assert result.weak_skills == []
    assert result.missing_skills == []
    assert result.skills_score == 100
    assert result.why_sentences


def test_relevant_junior_foundations_land_in_potential_range():
    job = AIJobExtraction(
        role_title="Java Backend Developer",
        seniority="mid",
        required_total_experience_years=4,
        required_skills=[
            AIRequiredSkill(
                name="Java",
                importance="required",
                years_required=4,
                category="Programming Languages",
            ),
            AIRequiredSkill(
                name="Spring Boot",
                importance="required",
                years_required=4,
                category="Frameworks",
            ),
            AIRequiredSkill(
                name="Microservices",
                importance="required",
                category="Frameworks",
            ),
        ],
    )
    candidate = AICandidateExtraction(
        estimated_total_experience_months=4,
        estimated_seniority="junior",
        skills=[
            AICandidateSkill(
                name="Java",
                level="junior",
                evidence="DAM projects and internships",
                estimated_years=0.5,
                category="Programming Languages",
            ),
            AICandidateSkill(
                name="Spring Boot",
                level="junior",
                evidence="portfolio projects and internships",
                estimated_years=0.5,
                category="Frameworks",
            ),
            AICandidateSkill(
                name="REST APIs",
                level="junior",
                evidence="portfolio API projects",
                estimated_years=0.5,
                category="Tools",
            ),
        ],
    )

    result = score_ai_compatibility(job, candidate)

    assert result.weak_skills == ["Java", "Spring Boot"]
    assert result.missing_skills == ["Microservices"]
    assert 26 <= result.final_score <= 50
    assert result.final_score < 76


def test_missing_nice_to_have_has_lower_weight_than_required_skill():
    job = AIJobExtraction(
        required_skills=[
            AIRequiredSkill(name="Python", importance="required"),
            AIRequiredSkill(name="GraphQL", importance="nice_to_have"),
        ],
    )
    candidate = AICandidateExtraction(
        skills=[AICandidateSkill(name="Python", level="senior")]
    )

    result = score_ai_compatibility(job, candidate)

    assert result.strong_skills == ["Python"]
    assert result.missing_skills == []
    assert result.skills_score >= 70
    assert result.final_score >= 80
