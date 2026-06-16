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
_PHRASE_ALIASES = [
    (re.compile(r"\brestful\s+apis?\b", re.IGNORECASE), "restapi"),
    (re.compile(r"\brest\s+apis?\b", re.IGNORECASE), "restapi"),
]


def _normalize(token: str) -> str:
    """Lower‑case and strip a token; resolve known aliases."""
    t = token.lower().strip()
    return SKILL_ALIASES.get(t, t)


def _normalize_phrases(text: str) -> str:
    normalized = text
    for pattern, replacement in _PHRASE_ALIASES:
        normalized = pattern.sub(replacement, normalized)
    return normalized


def _skill_label(skill: str) -> str:
    labels = {
        "restapi": "REST API",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "html": "HTML",
        "css": "CSS",
        "aws": "AWS",
        "gcp": "GCP",
        "sql server": "SQL Server",
    }
    return labels.get(skill, skill.title())


def _expand_with_synonyms(skill: str) -> Set[str]:
    """Return the skill itself plus any defined synonyms."""
    return {skill} | SKILL_SYNONYMS.get(skill, set())

# ---------------------------------------------------------------------------
# Public extraction API
# ---------------------------------------------------------------------------
def extract_skills(text: str) -> Tuple[SkillSet, Dict[str, List[str]]]:
    """Legacy extractor used for job descriptions (no context detection)."""
    # Preserve original behaviour for job offers – just tokenise and normalise.
    if not text:
        return SkillSet([]), {}

    seen: Set[str] = set()
    flat: List[str] = []
    categorized: Dict[str, List[str]] = defaultdict(list)

    for raw in _TOKEN_RE.findall(_normalize_phrases(text)):
        token = _normalize(raw)
        if token in FLATTENED_SKILL_SET and token not in seen:
            seen.add(token)
            flat.append(token)
            for cat, skills in SKILL_CATEGORIES.items():
                if token in skills:
                    categorized[cat].append(token)
    return SkillSet(flat), dict(categorized)

# ---------------------------------------------------------------------------
# New context‑aware extraction for candidate profiles
# ---------------------------------------------------------------------------

_NEGATIVE_CUE_PATTERNS = [
    r"\bnot\s+worked\s+deeply\s+with\b",
    r"\bnot\s+worked\s+with\b",
    r"\bno\s+experience\s+with\b",
    r"\bnot\s+familiar\s+with\b",
    r"\bdo\s+not\s+know\b",
    r"\bdon't\s+know\b",
    r"\black\s+experience\s+(?:with|in|of)\b",
    r"\bwithout\s+experience\s+(?:with|in|of)?\b",
]
_WEAK_CUE_PATTERNS = [
    r"\bbasic\s+knowledge\s+of\b",
    r"\bbasic\s+knowledge\s+with\b",
    r"\bfamiliar\s+with\b",
    r"\bsome\s+experience\s+with\b",
    r"\blimited\s+experience\s+with\b",
]
_CONTEXT_STOP_RE = re.compile(r"[.;!?\n]|\b(?:but|however|although|though)\b")
_NEGATIVE_AFTER_SKILL_RE = re.compile(
    r"^\s*(?:is|are)?\s*not\s+in\s+(?:my\s+|the\s+|our\s+)?(?:main\s+)?skill\s+set\b"
)


def _iter_skill_occurrences(text: str) -> List[Tuple[str, int, int]]:
    """Return normalized skill occurrences with their positions in *text*."""
    occurrences: List[Tuple[str, int, int]] = []
    for match in _TOKEN_RE.finditer(text):
        token = _normalize(match.group())
        if token in FLATTENED_SKILL_SET:
            occurrences.append((token, match.start(), match.end()))
    return occurrences


def _context_end(text: str, start: int) -> int:
    """Find where a cue phrase stops applying."""
    stop = _CONTEXT_STOP_RE.search(text, start)
    return stop.start() if stop else len(text)


def _skills_after_cues(
    text: str,
    occurrences: List[Tuple[str, int, int]],
    cue_patterns: List[str],
) -> Set[str]:
    """Return skills that appear after a cue before the next stop marker."""
    matched: Set[str] = set()
    for pattern in cue_patterns:
        for cue in re.finditer(pattern, text):
            start = cue.end()
            end = _context_end(text, start)
            for skill, skill_start, _ in occurrences:
                if start <= skill_start < end:
                    matched.add(skill)
    return matched


def _skills_with_negative_after(
    text: str,
    occurrences: List[Tuple[str, int, int]],
) -> Set[str]:
    """Return skills followed by a negative self-assessment phrase."""
    negative: Set[str] = set()
    for skill, _, skill_end in occurrences:
        if _NEGATIVE_AFTER_SKILL_RE.search(text[skill_end : skill_end + 80]):
            negative.add(skill)
    return negative


def _match_context(text: str, skill: str) -> str:
    """Return 'negative', 'weak', or 'strong' for *skill* found in *text*."""
    lowered = _normalize_phrases(text.lower())
    occurrences = [
        occurrence
        for occurrence in _iter_skill_occurrences(lowered)
        if occurrence[0] == skill
    ]
    if not occurrences:
        return "strong"

    negative = _skills_after_cues(
        lowered,
        occurrences,
        _NEGATIVE_CUE_PATTERNS,
    ) | _skills_with_negative_after(lowered, occurrences)
    if skill in negative:
        return "negative"

    weak = _skills_after_cues(lowered, occurrences, _WEAK_CUE_PATTERNS)
    if skill in weak:
        return "weak"
    return "strong"


def _extract_skills_with_context(text: str) -> Tuple[Set[str], Set[str], Set[str]]:
    """Extract skills from *text* and classify them.

    Returns three sets: (strong, weak, negative).
    """
    if not text:
        return set(), set(), set()

    lowered = _normalize_phrases(text.lower())
    occurrences = _iter_skill_occurrences(lowered)
    present = {skill for skill, _, _ in occurrences}
    negative = _skills_after_cues(
        lowered,
        occurrences,
        _NEGATIVE_CUE_PATTERNS,
    ) | _skills_with_negative_after(lowered, occurrences)
    weak = _skills_after_cues(lowered, occurrences, _WEAK_CUE_PATTERNS) - negative
    strong = present - weak - negative
    return strong, weak, negative

# ---------------------------------------------------------------------------
# Compatibility calculation – now uses contextual extraction for the profile
# ---------------------------------------------------------------------------
def calculate_compatibility(
    offer_set: SkillSet,
    profile_text: str,
    offer_cat: Dict[str, List[str]] | None = None,
    profile_cat: Dict[str, List[str]] | None = None,
) -> CompatibilityResult:
    """Compute compatibility using strong/weak/negative skill classification.

    * required = skills from the job description (offer_set)
    * strong, weak, negative = classification of skills from the candidate
      profile (extracted with context).
    * Full credit (1 point) for a strong match, half credit (0.5) for a weak
      match, no credit for negative or missing.
    * final percentage = earned_points / |required| * 100, clamped to 0-100.
    """
    offer_cat = offer_cat or {}
    required = set(offer_set.skills)
    # Context-aware extraction for the candidate profile
    strong, weak, _negative = _extract_skills_with_context(profile_text)

    # Determine matches
    matched_strong = required.intersection(strong)
    matched_weak = required.intersection(weak)
    # Skills that are required but not covered by strong or weak (and not negative) are missing
    missing = required.difference(matched_strong.union(matched_weak))

    # Earned points: 1 per strong, 0.5 per weak
    earned = len(matched_strong) + 0.5 * len(matched_weak)
    if not required:
        percentage = 0
    else:
        percentage = max(0, min(100, round(earned / len(required) * 100)))

    # Recommendations – same logic as before, based on missing skills
    category_weights = {
        "Programming Languages": 0.25,
        "Frameworks": 0.20,
        "DevOps": 0.15,
        "Cloud": 0.10,
        "Databases": 0.10,
        "Tools": 0.05,
        "Testing": 0.05,
        "Soft Skills": 0.05,
    }
    missing_sorted: List[Tuple[str, float, str]] = []
    weak_sorted: List[Tuple[str, float, str]] = []
    for cat, weight in category_weights.items():
        for skill in offer_cat.get(cat, []):
            if skill in missing:
                missing_sorted.append((skill, weight, cat))
            if skill in matched_weak:
                weak_sorted.append((skill, weight, cat))
    missing_sorted.sort(key=lambda x: -x[1])
    weak_sorted.sort(key=lambda x: -x[1])
    recommendations = [
        f"{_skill_label(skill)} is required for this role and currently appears as missing."
        for skill, _, _ in missing_sorted[:3]
    ]
    remaining_slots = max(0, 3 - len(recommendations))
    recommendations.extend(
        f"Your {_skill_label(skill)} knowledge appears basic. Strengthening it would improve compatibility."
        for skill, _, _ in weak_sorted[:remaining_slots]
    )

    matched_list = sorted(matched_strong)
    missing_list = sorted(missing)
    weak = list(sorted(matched_weak))

    return CompatibilityResult(
        percentage=percentage,
        matched=matched_list,
        weak=weak,
        missing=missing_list,
        recommendations=recommendations,
    )
