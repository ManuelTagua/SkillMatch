# Release Notes – SkillMatch v3.0

## What SkillMatch does
SkillMatch is a lightweight SaaS‑style MVP that lets developers compare a **job description** with a **candidate profile** (CV, skill list, personal summary). It extracts technical skills, computes a weighted compatibility score, highlights matches and gaps, and provides actionable recommendations.

## Main features (v3)
- **On‑boarding UI** that instantly explains the purpose and workflow.
- **Demo mode** with realistic job offers and candidate profiles, each with a short description.
- **Category‑aware skill extraction** supporting aliases (e.g. `js` → `javascript`) and synonyms (e.g. `spring` ↔ `springboot`).
- **Weighted compatibility algorithm** that accounts for core vs secondary categories and gives partial credit for related technologies.
- **Priority‑based recommendations** (high/medium/low) for missing skills.
- **Interview preparation** tips with sample questions per missing category.
- **Learning roadmap** suggesting the next skills to acquire.
- **Export** of the analysis as Markdown or JSON.
- **Polished Streamlit dashboard** with metric cards, radar chart, pie chart and clear visual hierarchy.
- Full **pytest** test suite covering extraction, alias/synonym handling, scoring, edge cases and empty inputs.
- Proper project metadata (`pyproject.toml`), a make‑style command guide (`COMMANDS.md`), and a clean `.gitignore`.

## Technical stack
- **Python 3.9+**
- **Streamlit** – UI framework
- **Pandas** – data handling (currently lightweight, future extensions)
- **Plotly** – interactive charts (compatibility bar, skill pie, category radar)
- **Pytest** – automated tests
- **Ruff** – linting configuration (via `pyproject.toml`)

## Current limitations
- Skill extraction relies on a static dictionary; no NLP or AI‑based parsing.
- No persistent storage – analyses are in‑memory only.
- No user authentication or multi‑user profiles.
- Recommendations are simple heuristics; they do not consider seniority or years of experience.

## Future improvements (roadmap)
- Integration with a SQLite database to store historical analyses and user profiles.
- More sophisticated NLP parsing (e.g., spaCy) for implicit skill detection.
- AI‑assisted recommendations and natural‑language explanations.
- User accounts, profile management, and LinkedIn/Resume import capabilities.
- CI/CD pipeline with automated linting, type checking and test coverage reporting.

---
*Version 3.0* is ready for a production‑grade GitHub release. All functionality is covered by tests and the app can be launched with `streamlit run app.py`.
