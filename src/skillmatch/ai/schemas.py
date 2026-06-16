"""Data schemas for AI-assisted SkillMatch analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def _as_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


@dataclass(frozen=True)
class AIRequiredSkill:
    name: str
    importance: str = "required"
    years_required: Optional[float] = None
    category: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIRequiredSkill":
        importance = _as_str(data.get("importance"), "required").lower()
        if importance not in {"required", "nice_to_have"}:
            importance = "required"
        return cls(
            name=_as_str(data.get("name")),
            importance=importance,
            years_required=_as_float(data.get("years_required")),
            category=_as_str(data.get("category")) or None,
        )


@dataclass(frozen=True)
class AIJobExtraction:
    role_title: str = ""
    seniority: str = ""
    required_total_experience_years: Optional[float] = None
    required_skills: List[AIRequiredSkill] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIJobExtraction":
        return cls(
            role_title=_as_str(data.get("role_title")),
            seniority=_as_str(data.get("seniority")).lower(),
            required_total_experience_years=_as_float(
                data.get("required_total_experience_years")
            ),
            required_skills=[
                AIRequiredSkill.from_dict(item)
                for item in _as_list(data.get("required_skills"))
                if isinstance(item, dict) and _as_str(item.get("name"))
            ],
        )


@dataclass(frozen=True)
class AICandidateSkill:
    name: str
    level: str = ""
    evidence: str = ""
    estimated_years: Optional[float] = None
    category: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AICandidateSkill":
        return cls(
            name=_as_str(data.get("name")),
            level=_as_str(data.get("level")).lower(),
            evidence=_as_str(data.get("evidence")),
            estimated_years=_as_float(data.get("estimated_years")),
            category=_as_str(data.get("category")) or None,
        )


@dataclass(frozen=True)
class AICandidateExtraction:
    estimated_total_experience_months: Optional[float] = None
    estimated_seniority: str = ""
    skills: List[AICandidateSkill] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AICandidateExtraction":
        return cls(
            estimated_total_experience_months=_as_float(
                data.get("estimated_total_experience_months")
            ),
            estimated_seniority=_as_str(data.get("estimated_seniority")).lower(),
            skills=[
                AICandidateSkill.from_dict(item)
                for item in _as_list(data.get("skills"))
                if isinstance(item, dict) and _as_str(item.get("name"))
            ],
        )


@dataclass(frozen=True)
class AISkillAssessment:
    name: str
    status: str
    importance: str
    score: float
    explanation: str
    category: str = "Tools"


@dataclass(frozen=True)
class AICompatibilityScore:
    skills_score: int
    experience_score: int
    seniority_score: int
    final_score: int
    explanation: str
    strong_skills: List[str]
    weak_skills: List[str]
    missing_skills: List[str]
    recommendations: List[str]
    skill_assessments: List[AISkillAssessment]
    category_scores: Dict[str, float]
    why_sentences: List[str] = field(default_factory=list)
    candidate_seniority: str = "Unknown"
    role_seniority: str = "Unknown"
    required_experience_years: Optional[float] = None
    detected_experience_years: Optional[float] = None


@dataclass(frozen=True)
class AIAnalysisGuidance:
    recommendations: List[str] = field(default_factory=list)
    interview_tips: List[str] = field(default_factory=list)
    roadmap: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIAnalysisGuidance":
        return cls(
            recommendations=[
                _as_str(item)
                for item in _as_list(data.get("recommendations"))[:3]
                if _as_str(item)
            ],
            interview_tips=[
                _as_str(item)
                for item in _as_list(data.get("interview_tips"))[:4]
                if _as_str(item)
            ],
            roadmap=[
                _as_str(item)
                for item in _as_list(data.get("roadmap"))[:5]
                if _as_str(item)
            ],
        )
