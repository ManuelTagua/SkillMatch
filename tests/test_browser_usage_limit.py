"""Tests for browser usage component payload validation."""

from src.skillmatch.adapters.browser_usage_limit import browser_usage_from_value


def test_missing_component_value_is_not_ready() -> None:
    usage = browser_usage_from_value(None)

    assert not usage.ready
    assert not usage.is_blocked


def test_component_value_calculates_remaining_usage() -> None:
    usage = browser_usage_from_value(
        {
            "ready": True,
            "used": 1,
            "remaining": 99,
            "limit": 2,
            "appliedToken": "analysis-1",
        }
    )

    assert usage.ready
    assert usage.used == 1
    assert usage.remaining == 1
    assert usage.applied_token == "analysis-1"


def test_component_value_clamps_usage_to_limit() -> None:
    usage = browser_usage_from_value({"ready": True, "used": 9, "limit": 2})

    assert usage.used == 2
    assert usage.remaining == 0
    assert usage.is_blocked
