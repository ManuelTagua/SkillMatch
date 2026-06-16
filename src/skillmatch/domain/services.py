"""Domain services for SkillMatch (enhanced, production‑ready).

Key improvements:
* Robust tokenisation and normalisation (handles aliases, synonyms).
* Returns both flat ``SkillSet`` *and* a per‑category mapping.
* Weighted compatibility scoring with partial credit for synonyms.
* Compatibility percentages are now guaranteed to stay within 0‑100.
* Comprehensive type hints and documentation.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List, Tuple, Set

from .entities import SkillSet, CompatibilityResult
from ..config.settings import (
    FLATTENED_SKILL_SET,
    SKILL_ALIASES,
    SKILL_CATEGORIES,
    SKILL_SYNONYMS,
)

# ---------------------------------------------------------------------------
# Tokenisation / normalisation helpers
# ---------------------------------------------------------------------------
_TOKEN_RE = re.compile(r"[\w#+-]+")


def _normalize(token: str) -> str:
    """Lower‑case and strip a token; resolve known aliases."""
    t = token.lower().strip()
    return SKILL_ALIASES.get(t, t)


def _expand_with_synonyms(skill: str) -> Set[str]:
    """Return the skill itself plus any defined synonyms."""
    return {skill} | SKILL_SYNONYMS.get(skill, set())

# ---------------------------------------------------------------------------
# Public extraction API
# ---------------------------------------------------------------------------
def extract_skills(text: str) -> Tuple[SkillSet, Dict[str, List[str]]]:
    """Extract recognised skills from free‑form ``text``.

    Returns a tuple ``(flat_set, categorized)`` where:
    * ``flat_set`` – a ``SkillSet`` with unique canonical skill names.
    * ``categorized`` – ``{category: [skill, …]}`` preserving discovery order.
    """
    if not text:
        return SkillSet([]), {}

    seen: Set[str] = set()
    flat: List[str] = []
    categorized: Dict[str, List[str]] = defaultdict(list)

    for raw in _TOKEN_RE.findall(text):
        token = _normalize(raw)
        if token in FLATTENED_SKILL_SET and token not in seen:
            seen.add(token)
            flat.append(token)
            for cat, skills in SKILL_CATEGORIES.items():
                if token in skills:
                    categorized[cat].append(token)
    return SkillSet(flat), dict(categorized)

# ---------------------------------------------------------------------------
# Scoring helpers – guaranteed 0‑1 per‑category score
# ---------------------------------------------------------------------------
def _category_match_score(
    offer: List[str], profile: List[str], weight: float
) -> Tuple[float, List[str], List[str]]:
    """Calculate a weighted score for a single category.

    Returns ``(score, matched, missing)`` where ``score`` is already multiplied
    by the category ``weight``.  Credit is capped at the number of offered skills
    to avoid exceeding 100 % when synonyms add extra points.
    """
    if not offer:
        # No requirement → full weight contribution
        return weight, [], []

    matched: List[str] = []
    missing: List[str] = []
    credit = 0.0
    for skill in offer:
        if skill in profile:
            matched.append(skill)
            credit += 1.0
        else:
            # Synonym check gives half credit
            if any(s in profile for s in _expand_with_synonyms(skill)):
                matched.append(skill)
                credit += 0.5
            else:
                missing.append(skill)
    # Prevent credit > number of offered skills (possible with overlapping synonyms)
    credit = min(credit, len(offer))
    # Normalised proportion then weighted
    return (credit / len(offer)) * weight, matched, missing

# ---------------------------------------------------------------------------
# Compatibility calculation – final percentage capped at 100
# ---------------------------------------------------------------------------
def calculate_compatibility(
    offer_set: SkillSet,
    profile_set: SkillSet,
    offer_cat: Dict[str, List[str]] | None = None,
    profile_cat: Dict[str, List[str]] | None = None,
) -> CompatibilityResult:
    """Compute a weighted compatibility result (0‑100%)."""
    offer_cat = offer_cat or {}
    profile_cat = profile_cat or {}

    # Category weights – must sum to 1.0
    weights = {
        "Programming Languages": 0.25,
        "Frameworks": 0.20,
        "DevOps": 0.15,
        "Cloud": 0.10,
        "Databases": 0.10,
        "Tools": 0.05,
        "Testing": 0.05,
        "Soft Skills": 0.05,
    }

    total_score = 0.0
    overall_matched: Set[str] = set()
    overall_missing: Set[str] = set()

    for cat, weight in weights.items():
        cat_offer = offer_cat.get(cat, [])
        cat_profile = profile_cat.get(cat, [])
        cat_score, matched, missing = _category_match_score(cat_offer, cat_profile, weight)
        total_score += cat_score
        overall_matched.update(matched)
        overall_missing.update(missing)

    # Guard against floating‑point overshoot
    percentage = min(round(total_score * 100), 100)

    # Recommendations – up to three highest‑weight missing skills
    recommendations: List[str] = []
    for cat in ["Programming Languages", "Frameworks", "DevOps", "Cloud"]:
        for skill in offer_cat.get(cat, []):
            if skill in overall_missing and len(recommendations) < 3:
                recommendations.append(
                    f"Learn {skill.title()} ({cat}) to boost compatibility."
                )
        if len(recommendations) >= 3:
            break

    return CompatibilityResult(
        percentage=percentage,
        matched=sorted(overall_matched),
        missing=sorted(overall_missing),
        recommendations=recommendations,
    )
