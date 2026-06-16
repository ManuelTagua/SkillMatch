"""Streamlit UI tests for AI-only analysis behavior."""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from src.skillmatch.ai.gemini_client import GeminiExtractionError, GeminiClient
from src.skillmatch.adapters.streamlit_ui import _final_assessment


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
    assert len(app.exception) == 0
    assert len(app.radio) == 0
    assert len(app.selectbox) == 0
    assert app.button[0].label == "Analyze"
    assert app.button[0].disabled
    assert "Rule-based" not in text
    assert "Demo mode" not in text
    assert "AI analysis requires Gemini" in text


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
    assert "Result summary" not in text
    assert "Rule-based" not in text
