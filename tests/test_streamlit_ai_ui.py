"""Streamlit UI tests for AI-only analysis behavior."""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from src.skillmatch.ai.gemini_client import GeminiExtractionError, GeminiClient
from src.skillmatch.ai.schemas import (
    AIAnalysisGuidance,
    AICandidateExtraction,
    AICandidateSkill,
    AIJobExtraction,
    AIRequiredSkill,
)
from src.skillmatch.adapters import streamlit_ui
from src.skillmatch.adapters.browser_usage_limit import BrowserUsage
from src.skillmatch.adapters.streamlit_ui import _final_assessment


@pytest.fixture(autouse=True)
def browser_usage_is_available(monkeypatch: pytest.MonkeyPatch) -> None:
    def available_usage(consume_token: str | None = None) -> BrowserUsage:
        return BrowserUsage(
            ready=True,
            applied_token=consume_token,
        )

    monkeypatch.setattr(streamlit_ui, "get_browser_usage", available_usage)


def _markdown_values(app: AppTest) -> list[str]:
    return [str(item.value) for item in app.markdown]


def test_match_label_ranges() -> None:
    assert _final_assessment(0)[0] == "Low Match"
    assert _final_assessment(25)[0] == "Low Match"
    assert _final_assessment(26)[0] == "Potential Match"
    assert _final_assessment(50)[0] == "Potential Match"
    assert _final_assessment(51)[0] == "Good Match"
    assert _final_assessment(75)[0] == "Good Match"
    assert _final_assessment(76)[0] == "Strong Match"
    assert _final_assessment(100)[0] == "Strong Match"


def test_ui_has_no_rule_based_mode_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    app = AppTest.from_file("app.py", default_timeout=20)
    app.run()

    text = "\n".join(_markdown_values(app))
    warnings = [str(item.value) for item in app.warning]
    assert len(app.exception) == 0
    assert len(app.radio) == 0
    assert len(app.selectbox) == 0
    assert app.button[0].label == "Analyze"
    assert app.button[0].disabled
    assert "Rule-based" not in text
    assert "Demo mode" not in text
    assert "AI service not configured" in text
    assert "Gemini" not in text
    assert all("Gemini" not in warning for warning in warnings)


def test_gemini_failure_does_not_render_fallback_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    def fail_extract_job(self: GeminiClient, job_description: str) -> object:
        raise GeminiExtractionError("Gemini API request failed with HTTP 503.")

    monkeypatch.setattr(GeminiClient, "extract_job", fail_extract_job)

    app = AppTest.from_file("app.py", default_timeout=20)
    app.run()
    app.text_area[0].set_value("Java Spring Boot role")
    app.text_area[1].set_value("Java projects and internship")
    app.button[0].click().run()

    text = "\n".join(_markdown_values(app))
    errors = [str(item.value) for item in app.error]
    assert len(app.exception) == 0
    assert any("AI analysis failed" in error for error in errors)
    assert all("Gemini" not in error for error in errors)
    assert "Result summary" not in text
    assert "Rule-based" not in text
    assert "Gemini" not in text


def test_gemini_failure_does_not_consume_browser_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    consume_tokens: list[str | None] = []

    def available_usage(consume_token: str | None = None) -> BrowserUsage:
        consume_tokens.append(consume_token)
        return BrowserUsage(ready=True, applied_token=consume_token)

    def fail_extract_job(self: GeminiClient, job_description: str) -> object:
        raise GeminiExtractionError("Gemini API request failed with HTTP 503.")

    monkeypatch.setattr(streamlit_ui, "get_browser_usage", available_usage)
    monkeypatch.setattr(GeminiClient, "extract_job", fail_extract_job)

    app = AppTest.from_file("app.py", default_timeout=20)
    app.run()
    app.text_area[0].set_value("Java Spring Boot role")
    app.text_area[1].set_value("Java projects and internship")
    app.button[0].click().run()

    assert consume_tokens
    assert all(token is None for token in consume_tokens)


def test_successful_analysis_consumes_one_browser_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    consume_tokens: list[str | None] = []

    def browser_usage(consume_token: str | None = None) -> BrowserUsage:
        consume_tokens.append(consume_token)
        used = 1 if consume_token else 0
        return BrowserUsage(
            ready=True,
            used=used,
            remaining=2 - used,
            applied_token=consume_token,
        )

    monkeypatch.setattr(streamlit_ui, "get_browser_usage", browser_usage)
    monkeypatch.setattr(
        GeminiClient,
        "extract_job",
        lambda self, text: AIJobExtraction(
            role_title="Backend Developer",
            seniority="junior",
            required_skills=[AIRequiredSkill(name="Java")],
        ),
    )
    monkeypatch.setattr(
        GeminiClient,
        "extract_candidate",
        lambda self, text: AICandidateExtraction(
            estimated_seniority="junior",
            skills=[AICandidateSkill(name="Java", level="junior")],
        ),
    )
    monkeypatch.setattr(
        GeminiClient,
        "generate_guidance",
        lambda self, job, candidate, score: AIAnalysisGuidance(),
    )

    app = AppTest.from_file("app.py", default_timeout=20)
    app.run()
    app.text_area[0].set_value("Junior Java developer")
    app.text_area[1].set_value("Junior developer with Java projects")
    app.button[0].click().run()

    assert any(token for token in consume_tokens)
    assert any("Result summary" in str(item.value) for item in app.subheader)
    assert any("1/2" in str(item.value) for item in app.caption)


def test_limit_blocks_analysis_and_shows_clear_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setattr(
        streamlit_ui,
        "get_browser_usage",
        lambda consume_token=None: BrowserUsage(
            ready=True,
            used=2,
            remaining=0,
        ),
    )

    app = AppTest.from_file("app.py", default_timeout=20)
    app.run()

    errors = [str(item.value) for item in app.error]
    assert app.button[0].disabled
    assert any("Has alcanzado el límite de 2 análisis gratuitos" in item for item in errors)
    assert any("0/2" in str(item.value) for item in app.caption)
