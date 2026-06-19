"""Tests for Gemini client error handling."""

from __future__ import annotations

import json
import socket
import urllib.error

import pytest

from src.skillmatch.ai.gemini_client import GeminiClient, GeminiExtractionError
from src.skillmatch.ai.scoring import score_ai_compatibility
from src.skillmatch.ai.schemas import (
    AICandidateExtraction,
    AICandidateSkill,
    AIJobExtraction,
    AIRequiredSkill,
)


class _FakeResponse:
    def __init__(self, data: dict) -> None:
        self.data = data

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.data).encode("utf-8")


def _gemini_payload(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def _http_503() -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="https://example.test",
        code=503,
        msg="Service Unavailable",
        hdrs=None,
        fp=None,
    )


def test_retries_http_503_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    def fake_urlopen(*args: object, **kwargs: object) -> _FakeResponse:
        calls["count"] += 1
        if calls["count"] < 3:
            raise _http_503()
        return _FakeResponse(_gemini_payload('{"role_title": "Backend"}'))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    client = GeminiClient(api_key="test-key", max_retries=2, retry_delay=0)
    data = client._generate_json("prompt")

    assert calls["count"] == 3
    assert data == {"role_title": "Backend"}


def test_http_503_after_retries_raises_clear_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"count": 0}

    def fake_urlopen(*args: object, **kwargs: object) -> _FakeResponse:
        calls["count"] += 1
        raise _http_503()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    client = GeminiClient(api_key="test-key", max_retries=2, retry_delay=0)
    with pytest.raises(GeminiExtractionError, match="temporarily unavailable"):
        client._generate_json("prompt")

    assert calls["count"] == 3


def test_timeout_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(*args: object, **kwargs: object) -> _FakeResponse:
        raise socket.timeout("timed out")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    client = GeminiClient(api_key="test-key", max_retries=2, retry_delay=0)
    with pytest.raises(GeminiExtractionError, match="timed out"):
        client._generate_json("prompt")


def test_malformed_response_raises_clear_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(*args: object, **kwargs: object) -> _FakeResponse:
        return _FakeResponse(_gemini_payload("not json"))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    client = GeminiClient(api_key="test-key", retry_delay=0)
    with pytest.raises(GeminiExtractionError, match="did not contain JSON"):
        client._generate_json("prompt")


def test_google_api_key_is_used_when_gemini_key_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")

    client = GeminiClient()

    assert client.api_key == "google-key"
    assert client.is_configured


def test_google_api_key_takes_precedence_over_gemini_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")

    client = GeminiClient()

    assert client.api_key == "google-key"


def test_gemini_api_key_is_used_as_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")

    client = GeminiClient()

    assert client.api_key == "gemini-key"


def test_generate_guidance_parses_limited_practical_lists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "recommendations": [
            "Build a Spring Boot microservices project.",
            "Practice REST API design interviews.",
            "Create integration tests for persistence.",
            "Extra item should be ignored.",
        ],
        "interview_tips": [
            "Explain transaction boundaries.",
            "Compare REST status code choices.",
            "Discuss service decomposition.",
            "Walk through a debugging example.",
            "Extra tip should be ignored.",
        ],
        "roadmap": [
            "Create a backend API.",
            "Add database persistence.",
            "Add authentication.",
            "Containerize with Docker.",
            "Deploy and document it.",
            "Extra roadmap should be ignored.",
        ],
    }

    def fake_urlopen(*args: object, **kwargs: object) -> _FakeResponse:
        return _FakeResponse(_gemini_payload(json.dumps(payload)))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    job = AIJobExtraction(
        role_title="Backend Developer",
        seniority="mid",
        required_skills=[AIRequiredSkill(name="Spring Boot")],
    )
    candidate = AICandidateExtraction(
        estimated_seniority="junior",
        skills=[AICandidateSkill(name="Spring Boot", level="junior")],
    )
    score = score_ai_compatibility(job, candidate)

    client = GeminiClient(api_key="test-key", retry_delay=0)
    guidance = client.generate_guidance(job, candidate, score)

    assert guidance.recommendations == payload["recommendations"][:3]
    assert guidance.interview_tips == payload["interview_tips"][:4]
    assert guidance.roadmap == payload["roadmap"][:5]
