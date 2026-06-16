"""Gemini API client for optional AI-assisted extraction."""

from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from typing import Any, Dict

from .prompts import candidate_extraction_prompt, guidance_prompt, job_extraction_prompt
from .schemas import (
    AIAnalysisGuidance,
    AICandidateExtraction,
    AICompatibilityScore,
    AIJobExtraction,
)


class GeminiExtractionError(RuntimeError):
    """Raised when Gemini extraction cannot return usable JSON."""


def _guidance_payload(
    job: AIJobExtraction,
    candidate: AICandidateExtraction,
    score: AICompatibilityScore,
) -> Dict[str, Any]:
    return {
        "job": {
            "role_title": job.role_title,
            "seniority": job.seniority,
            "required_total_experience_years": job.required_total_experience_years,
            "required_skills": [
                {
                    "name": skill.name,
                    "importance": skill.importance,
                    "years_required": skill.years_required,
                    "category": skill.category,
                }
                for skill in job.required_skills
            ],
        },
        "candidate": {
            "estimated_total_experience_months": candidate.estimated_total_experience_months,
            "estimated_seniority": candidate.estimated_seniority,
            "skills": [
                {
                    "name": skill.name,
                    "level": skill.level,
                    "evidence": skill.evidence,
                    "estimated_years": skill.estimated_years,
                    "category": skill.category,
                }
                for skill in candidate.skills
            ],
        },
        "score": {
            "skills_score": score.skills_score,
            "experience_score": score.experience_score,
            "seniority_score": score.seniority_score,
            "final_score": score.final_score,
            "strong_skills": score.strong_skills,
            "weak_skills": score.weak_skills,
            "missing_skills": score.missing_skills,
            "why": score.why_sentences,
            "candidate_seniority": score.candidate_seniority,
            "role_seniority": score.role_seniority,
        },
    }


class GeminiClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: int = 30,
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key.strip())

    def extract_job(self, job_description: str) -> AIJobExtraction:
        data = self._generate_json(job_extraction_prompt(job_description))
        return AIJobExtraction.from_dict(data)

    def extract_candidate(self, candidate_profile: str) -> AICandidateExtraction:
        data = self._generate_json(candidate_extraction_prompt(candidate_profile))
        return AICandidateExtraction.from_dict(data)

    def generate_guidance(
        self,
        job: AIJobExtraction,
        candidate: AICandidateExtraction,
        score: AICompatibilityScore,
    ) -> AIAnalysisGuidance:
        data = self._generate_json(guidance_prompt(_guidance_payload(job, candidate, score)))
        return AIAnalysisGuidance.from_dict(data)

    def _generate_json(self, prompt: str) -> Dict[str, Any]:
        if not self.is_configured:
            raise GeminiExtractionError(
                "Gemini API key is not configured. Set GEMINI_API_KEY or GOOGLE_API_KEY."
            )

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )

        response_data = self._request_with_retries(request)

        text = self._response_text(response_data)
        return self._parse_json_text(text)

    def _request_with_retries(
        self,
        request: urllib.request.Request,
    ) -> Dict[str, Any]:
        last_http_error: urllib.error.HTTPError | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code != 503:
                    raise GeminiExtractionError(
                        f"Gemini API request failed with HTTP {exc.code}."
                    ) from exc
                last_http_error = exc
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                raise GeminiExtractionError(
                    "Gemini API is temporarily unavailable after retries."
                ) from last_http_error
            except (TimeoutError, socket.timeout) as exc:
                raise GeminiExtractionError("Gemini API request timed out.") from exc
            except urllib.error.URLError as exc:
                if isinstance(exc.reason, TimeoutError | socket.timeout):
                    raise GeminiExtractionError("Gemini API request timed out.") from exc
                raise GeminiExtractionError("Gemini API request failed.") from exc
            except json.JSONDecodeError as exc:
                raise GeminiExtractionError("Gemini API returned invalid JSON.") from exc
        raise GeminiExtractionError("Gemini API request failed.")

    @staticmethod
    def _response_text(response_data: Dict[str, Any]) -> str:
        try:
            parts = response_data["candidates"][0]["content"]["parts"]
            return "".join(part.get("text", "") for part in parts)
        except (KeyError, IndexError, TypeError) as exc:
            raise GeminiExtractionError(
                "Gemini API response did not include generated text."
            ) from exc

    @staticmethod
    def _parse_json_text(text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise GeminiExtractionError("Gemini response did not contain JSON.")
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise GeminiExtractionError("Gemini response JSON could not be parsed.") from exc
        if not isinstance(parsed, dict):
            raise GeminiExtractionError("Gemini response JSON must be an object.")
        return parsed
