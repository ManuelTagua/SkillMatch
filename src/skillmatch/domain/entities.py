"""Domain entities used by SkillMatch.

All entities are simple dataclasses – they contain no behaviour, only data.
The business logic lives in ``services.py`` so the core can be unit‑tested
without any Streamlit or Plotly dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class SkillSet:
    """A collection of extracted skill tokens (lower‑case strings)."""

    skills: List[str]

    def as_set(self) -> set[str]:
        return set(self.skills)


@dataclass(frozen=True)
class CompatibilityResult:
    """Result of the compatibility calculation.

    * ``percentage`` – integer 0‑100
    * ``matched`` – list of skill strings present in both offer and profile
    * ``missing`` – list of skills required by the offer but absent from the profile
    * ``recommendations`` – short strings suggesting what to learn next
    """

    percentage: int
    matched: List[str]
    missing: List[str]
    recommendations: List[str]
