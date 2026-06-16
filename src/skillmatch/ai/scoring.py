"""Deterministic scoring for AI-extracted SkillMatch data."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from .schemas import (
    AICandidateExtraction,
    AICandidateSkill,
    AICompatibilityScore,
    AIJobExtraction,
    AIRequiredSkill,
    AISkillAssessment,
)


CATEGORY_ORDER = [
    "Programming Languages",
    "Frameworks",
    "Databases",
    "DevOps",
    "Tools",
    "Testing",
    "Cloud",
    "Soft Skills",
]

SENIORITY_RANK = {
    "unknown": 0,
    "intern": 1,
    "entry": 1,
    "junior": 1,
    "mid": 2,
    "middle": 2,
    "senior": 3,
    "lead": 4,
    "principal": 5,
}

LEVEL_SCORE = {
    "basic": 0.45,
    "junior": 0.65,
    "intermediate": 0.7,
    "mid": 0.82,
    "middle": 0.82,
    "senior": 1.0,
    "expert": 1.0,
}


def score_ai_compatibility(
    job: AIJobExtraction,
    candidate: AICandidateExtraction,
) -> AICompatibilityScore:
    assessments = _score_skills(job.required_skills, candidate.skills)
    skills_score = _weighted_skill_score(assessments)
    experience_score = _experience_score(job, candidate)
    seniority_score = _seniority_score(job, candidate)
    required_experience_years = job.required_total_experience_years
    detected_experience_years = _detected_experience_years(candidate)
    candidate_seniority = _candidate_seniority_label(candidate)
    role_seniority = _seniority_label(job.seniority)
    final_score = _clamp_percent(
        round(skills_score * 0.60 + experience_score * 0.25 + seniority_score * 0.15)
    )
    strong = sorted([item.name for item in assessments if item.status == "strong"])
    weak = sorted([item.name for item in assessments if item.status == "partial"])
    missing = sorted(
        [
            item.name
            for item in assessments
            if item.status == "missing" and item.importance == "required"
        ]
    )
    recommendations = _recommendations(assessments)
    why_sentences = _why_sentences(
        assessments,
        skills_score,
        experience_score,
        seniority_score,
        required_experience_years,
        detected_experience_years,
        candidate_seniority,
        role_seniority,
        _foundation_phrase(candidate),
    )
    explanation = " ".join(why_sentences)
    return AICompatibilityScore(
        skills_score=skills_score,
        experience_score=experience_score,
        seniority_score=seniority_score,
        final_score=final_score,
        explanation=explanation,
        strong_skills=strong,
        weak_skills=weak,
        missing_skills=missing,
        recommendations=recommendations,
        skill_assessments=assessments,
        category_scores=_category_scores(assessments),
        why_sentences=why_sentences,
        candidate_seniority=candidate_seniority,
        role_seniority=role_seniority,
        required_experience_years=required_experience_years,
        detected_experience_years=detected_experience_years,
    )


def _score_skills(
    required_skills: List[AIRequiredSkill],
    candidate_skills: List[AICandidateSkill],
) -> List[AISkillAssessment]:
    candidate_index = {_canonical_name(skill.name): skill for skill in candidate_skills}
    assessments: List[AISkillAssessment] = []
    for required in required_skills:
        candidate_skill = candidate_index.get(_canonical_name(required.name))
        category = _category(required.category, candidate_skill.category if candidate_skill else None)
        if not candidate_skill:
            assessments.append(
                AISkillAssessment(
                    name=required.name,
                    status="missing",
                    importance=required.importance,
                    score=0.0,
                    explanation=f"{required.name} was not found in the candidate profile.",
                    category=category,
                )
            )
            continue

        score = _candidate_skill_score(required, candidate_skill)
        status = "strong" if score >= 0.8 else "partial"
        years = candidate_skill.estimated_years
        assessments.append(
            AISkillAssessment(
                name=required.name,
                status=status,
                importance=required.importance,
                score=score,
                explanation=_skill_explanation(required, candidate_skill, score, years),
                category=category,
            )
        )
    return assessments


def _candidate_skill_score(
    required: AIRequiredSkill,
    candidate: AICandidateSkill,
) -> float:
    level_score = LEVEL_SCORE.get(candidate.level, 0.65)
    return round(level_score, 2)


def _weighted_skill_score(assessments: List[AISkillAssessment]) -> int:
    if not assessments:
        return 0
    total_weight = 0.0
    earned = 0.0
    for item in assessments:
        weight = 1.0 if item.importance == "required" else 0.35
        total_weight += weight
        earned += item.score * weight
    if total_weight == 0:
        return 0
    return _clamp_percent(round((earned / total_weight) * 100))


def _experience_score(
    job: AIJobExtraction,
    candidate: AICandidateExtraction,
) -> int:
    required_years = job.required_total_experience_years
    if not required_years or required_years <= 0:
        return 100
    candidate_months = _candidate_experience_months(candidate)
    required_months = required_years * 12
    raw_score = 0
    if candidate_months and candidate_months > 0:
        raw_score = round((candidate_months / required_months) * 100)
    foundation_floor = _foundation_experience_floor(candidate, required_years)
    return _clamp_percent(max(raw_score, foundation_floor))


def _seniority_score(
    job: AIJobExtraction,
    candidate: AICandidateExtraction,
) -> int:
    required_rank = SENIORITY_RANK.get((job.seniority or "unknown").lower(), 0)
    if required_rank == 0:
        return 100
    candidate_rank = SENIORITY_RANK.get(
        (candidate.estimated_seniority or "").lower(),
        0,
    )
    if candidate_rank == 0:
        candidate_rank = _infer_seniority_rank(candidate.estimated_total_experience_months)
    if candidate_rank == 0 and _has_foundation_evidence(candidate):
        candidate_rank = SENIORITY_RANK["junior"]
    if candidate_rank >= required_rank:
        return 100
    gap = required_rank - candidate_rank
    return max(0, 100 - gap * 30)


def _category_scores(assessments: List[AISkillAssessment]) -> Dict[str, float]:
    scores = {cat: 0.0 for cat in CATEGORY_ORDER}
    grouped: Dict[str, List[AISkillAssessment]] = {cat: [] for cat in CATEGORY_ORDER}
    for item in assessments:
        grouped.setdefault(item.category, []).append(item)
    for category in CATEGORY_ORDER:
        items = grouped.get(category, [])
        if not items:
            continue
        total_weight = sum(1.0 if item.importance == "required" else 0.35 for item in items)
        earned = sum(
            item.score * (1.0 if item.importance == "required" else 0.35)
            for item in items
        )
        scores[category] = round((earned / total_weight) * 100, 1) if total_weight else 0.0
    return scores


def _recommendations(assessments: List[AISkillAssessment]) -> List[str]:
    missing_required = [
        item for item in assessments if item.status == "missing" and item.importance == "required"
    ]
    partial_required = [
        item for item in assessments if item.status == "partial" and item.importance == "required"
    ]
    recs = [
        f"{item.name} is required for this role and currently appears as missing."
        for item in missing_required[:3]
    ]
    remaining = max(0, 3 - len(recs))
    recs.extend(
        f"{item.name} is required for this role, but the candidate evidence suggests a partial match."
        for item in partial_required[:remaining]
    )
    return recs


def _why_sentences(
    assessments: List[AISkillAssessment],
    skills_score: int,
    experience_score: int,
    seniority_score: int,
    required_experience_years: Optional[float],
    detected_experience_years: Optional[float],
    candidate_seniority: str,
    role_seniority: str,
    foundation_phrase: str,
) -> List[str]:
    sentences: List[str] = []
    missing_required = [
        item.name
        for item in assessments
        if item.status == "missing" and item.importance == "required"
    ]
    partial_required = [
        item.name
        for item in assessments
        if item.status == "partial" and item.importance == "required"
    ]
    if required_experience_years and experience_score < 100:
        focus = _experience_focus(assessments)
        sentences.append(
            f"The main limitation is the requested {required_experience_years:g} years of {focus} experience; an experience gap is detected."
        )
    if foundation_phrase and any(item.status != "missing" for item in assessments):
        sentences.append(f"The profile demonstrates relevant foundations through {foundation_phrase}.")
    if seniority_score < 100:
        sentences.append(
            f"The role appears {_level_phrase(role_seniority)} while the candidate profile is closer to {_level_phrase(candidate_seniority)}."
        )
    if missing_required:
        shown = ", ".join(missing_required[:3])
        sentences.append(f"Several required skills are missing: {shown}.")
    elif partial_required:
        shown = ", ".join(partial_required[:3])
        sentences.append(f"Most key technologies are present, but {shown} appears partial.")
    elif skills_score >= 80:
        sentences.append("Most required skills appear to match the role.")
    if not sentences:
        sentences.append("The available evidence suggests a cautious match for this role.")
    return sentences[:3]


def _experience_focus(assessments: List[AISkillAssessment]) -> str:
    required_names = [
        item.name
        for item in assessments
        if item.importance == "required" and item.status != "missing"
    ]
    if not required_names:
        required_names = [
            item.name for item in assessments if item.importance == "required"
        ]
    if not required_names:
        return "role-relevant"
    shown = required_names[:2]
    if len(shown) == 1:
        return shown[0]
    return " and ".join(shown)


def _level_phrase(label: str) -> str:
    normalized = label.strip().lower()
    if not normalized or normalized == "unknown":
        return "an unknown level"
    return f"{normalized}-level"


def _skill_explanation(
    required: AIRequiredSkill,
    candidate: AICandidateSkill,
    score: float,
    years: Optional[float],
) -> str:
    if required.years_required and years is not None and years < required.years_required:
        return (
            f"{required.name} is present, but estimated experience "
            f"({years:g} years) is below the required {required.years_required:g} years."
        )
    if score < 0.8:
        return f"{required.name} is present but appears below the required depth."
    return f"{required.name} appears to meet the role requirement."


def _canonical_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _category(*values: Optional[str]) -> str:
    for value in values:
        if value in CATEGORY_ORDER:
            return value
    return "Tools"


def _months_from_skills(skills: List[AICandidateSkill]) -> Optional[float]:
    years = [skill.estimated_years for skill in skills if skill.estimated_years is not None]
    if not years:
        return None
    return max(years) * 12


def _candidate_experience_months(candidate: AICandidateExtraction) -> Optional[float]:
    skill_months = _months_from_skills(candidate.skills)
    if candidate.estimated_total_experience_months is None:
        return skill_months
    if skill_months is None:
        return candidate.estimated_total_experience_months
    return max(candidate.estimated_total_experience_months, skill_months)


def _evidence_text(candidate: AICandidateExtraction) -> str:
    return " ".join(skill.evidence.lower() for skill in candidate.skills if skill.evidence)


def _has_internship_evidence(candidate: AICandidateExtraction) -> bool:
    evidence = _evidence_text(candidate)
    return any(term in evidence for term in ("internship", "internships", "intern", "placement"))


def _has_project_evidence(candidate: AICandidateExtraction) -> bool:
    evidence = _evidence_text(candidate)
    return any(
        term in evidence
        for term in (
            "project",
            "projects",
            "portfolio",
            "coursework",
            "academic",
            "bootcamp",
            "dam",
        )
    )


def _has_foundation_evidence(candidate: AICandidateExtraction) -> bool:
    return bool(candidate.skills) or _has_internship_evidence(candidate) or _has_project_evidence(candidate)


def _foundation_experience_floor(
    candidate: AICandidateExtraction,
    required_years: float,
) -> int:
    has_internship = _has_internship_evidence(candidate)
    has_projects = _has_project_evidence(candidate)
    if has_internship and has_projects:
        floor = 35
    elif has_internship:
        floor = 30
    elif has_projects:
        floor = 25
    elif candidate.skills:
        floor = 15
    else:
        floor = 0
    if required_years >= 6:
        return min(floor, 25)
    return floor


def _foundation_phrase(candidate: AICandidateExtraction) -> str:
    has_internship = _has_internship_evidence(candidate)
    has_projects = _has_project_evidence(candidate)
    if has_internship and has_projects:
        return "internship-level and project-level experience"
    if has_internship:
        return "internship-level experience"
    if has_projects:
        return "project-level experience"
    if candidate.skills:
        return "technology foundations"
    return ""


def _detected_experience_years(candidate: AICandidateExtraction) -> Optional[float]:
    months = _candidate_experience_months(candidate)
    return round(months / 12, 1) if months is not None else None


def _candidate_seniority_label(candidate: AICandidateExtraction) -> str:
    if candidate.estimated_seniority:
        return _seniority_label(candidate.estimated_seniority)
    rank = _infer_seniority_rank(candidate.estimated_total_experience_months)
    if rank == 0 and _has_foundation_evidence(candidate):
        rank = SENIORITY_RANK["junior"]
    labels = {1: "Junior", 2: "Mid", 3: "Senior"}
    return labels.get(rank, "Unknown")


def _seniority_label(value: str | None) -> str:
    normalized = (value or "unknown").replace("_", "-").strip().lower()
    labels = {
        "intern": "Intern",
        "entry": "Junior",
        "junior": "Junior",
        "mid": "Mid",
        "middle": "Mid",
        "mid-senior": "Mid-Senior",
        "senior": "Senior",
        "lead": "Lead",
        "principal": "Principal",
        "unknown": "Unknown",
    }
    return labels.get(normalized, normalized.title() if normalized else "Unknown")


def _infer_seniority_rank(months: Optional[float]) -> int:
    if months is None:
        return 0
    if months < 24:
        return SENIORITY_RANK["junior"]
    if months < 60:
        return SENIORITY_RANK["mid"]
    return SENIORITY_RANK["senior"]


def _clamp_percent(value: int) -> int:
    return max(0, min(100, value))
