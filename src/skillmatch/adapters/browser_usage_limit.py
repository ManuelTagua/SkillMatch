"""Browser-backed quota state for the Streamlit analysis action."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import streamlit.components.v1 as components


ANALYSIS_LIMIT = 2
ANALYSIS_WINDOW_MS = 24 * 60 * 60 * 1000

_COMPONENT_PATH = Path(__file__).with_name("browser_usage_limit_component")
_browser_usage_component = components.declare_component(
    "skillmatch_browser_usage_limit",
    path=_COMPONENT_PATH,
)


@dataclass(frozen=True)
class BrowserUsage:
    """Current analysis allowance reported by this browser."""

    ready: bool
    used: int = 0
    remaining: int = ANALYSIS_LIMIT
    limit: int = ANALYSIS_LIMIT
    applied_token: str | None = None
    error: str | None = None

    @property
    def is_blocked(self) -> bool:
        return self.ready and self.remaining <= 0


def _to_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def browser_usage_from_value(value: Any) -> BrowserUsage:
    """Convert the component payload into a safe quota state."""

    if not isinstance(value, Mapping):
        return BrowserUsage(ready=False)

    error = value.get("error")
    if error:
        return BrowserUsage(ready=False, error=str(error))
    if value.get("ready") is not True:
        return BrowserUsage(ready=False)

    limit = max(_to_int(value.get("limit"), ANALYSIS_LIMIT), 1)
    used = min(max(_to_int(value.get("used"), 0), 0), limit)
    applied_token = value.get("appliedToken")
    return BrowserUsage(
        ready=True,
        used=used,
        remaining=limit - used,
        limit=limit,
        applied_token=str(applied_token) if applied_token else None,
    )


def get_browser_usage(consume_token: str | None = None) -> BrowserUsage:
    """Read the quota and optionally consume one successful analysis."""

    value = _browser_usage_component(
        storage_key="skillmatch.analysis-usage.v1",
        limit=ANALYSIS_LIMIT,
        window_ms=ANALYSIS_WINDOW_MS,
        consume_token=consume_token,
        default=None,
        key="skillmatch_analysis_usage",
    )
    return browser_usage_from_value(value)
