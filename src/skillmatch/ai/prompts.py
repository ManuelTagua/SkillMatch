"""Prompts used by AI-assisted extraction."""

from __future__ import annotations

import json


CATEGORY_INSTRUCTIONS = (
    "Use one category when possible: Programming Languages, Frameworks, "
    "Databases, DevOps, Tools, Testing, Cloud, Soft Skills."
)


def job_extraction_prompt(job_description: str) -> str:
    return f"""
Extract structured hiring requirements from this job description.

Return valid JSON only. Do not include markdown.
Do not invent requirements that are not supported by the text.
Use null when years are not stated.
Infer seniority from title, wording, and years when explicit labels are absent.
{CATEGORY_INSTRUCTIONS}

Schema:
{{
  "role_title": "Java Backend Developer",
  "seniority": "junior|mid|senior|lead|unknown",
  "required_total_experience_years": 4,
  "required_skills": [
    {{
      "name": "Java",
      "importance": "required|nice_to_have",
      "years_required": 4,
      "category": "Programming Languages"
    }}
  ]
}}

Job description:
{job_description}
""".strip()


def candidate_extraction_prompt(candidate_profile: str) -> str:
    return f"""
Extract structured candidate experience from this profile.

Return valid JSON only. Do not include markdown.
Do not overstate experience. Projects, internships, coursework, and basic
knowledge should not be treated as full professional experience.
Do not treat internships or real portfolio projects as zero experience.
When projects or internships are meaningful but years are not stated, estimate
conservative partial experience and describe it as project-level or
internship-level evidence.
Infer seniority from evidence, education, internships, projects, and years.
Use null when years are not stated.
{CATEGORY_INSTRUCTIONS}

Schema:
{{
  "estimated_total_experience_months": 4,
  "estimated_seniority": "junior|mid|senior|lead|unknown",
  "skills": [
    {{
      "name": "Java",
      "level": "basic|junior|mid|senior|expert",
      "evidence": "projects and internships",
      "estimated_years": 0.5,
      "category": "Programming Languages"
    }}
  ]
}}

Candidate profile:
{candidate_profile}
""".strip()


def guidance_prompt(analysis: dict) -> str:
    return f"""
Generate practical hiring analysis guidance from the structured scoring data.

Return valid JSON only. Do not include markdown.
Keep each item concise, specific, and action-oriented.
Do not use vague phrases like "read tutorials" or "study more".
Use the exact technologies and gaps from the data.

Limits:
- recommendations: max 3
- interview_tips: max 4
- roadmap: max 5

Each item must mention a concrete role technology, missing/partial skill,
interview topic, or project artifact from the scoring data.
Avoid generic items such as "start with tutorials", "study more", or
"review the basics".

Schema:
{{
  "recommendations": [
    "Build a Spring Boot microservices project with persistence and tests."
  ],
  "interview_tips": [
    "Practice explaining REST API design tradeoffs and error handling."
  ],
  "roadmap": [
    "Create a React application consuming a backend API."
  ]
}}

Scoring data:
{json.dumps(analysis, ensure_ascii=False)}
""".strip()
