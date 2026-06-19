"""Streamlit UI for AI-assisted SkillMatch analysis."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from html import escape
from typing import Dict, List

import streamlit as st

from ..ai.gemini_client import GeminiClient, GeminiExtractionError
from ..ai.schemas import AIAnalysisGuidance, AICompatibilityScore
from ..ai.scoring import score_ai_compatibility
from ..domain.entities import CompatibilityResult
from .browser_usage_limit import BrowserUsage, get_browser_usage


CATEGORY_ORDER = [
    "Programming Languages",
    "Frameworks",
    "Databases",
    "DevOps",
    "Tools",
    "Testing",
    "Cloud",
    "Soft Skills",
]

SKILL_LABELS = {
    "restapi": "REST API",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "html": "HTML",
    "css": "CSS",
    "aws": "AWS",
    "gcp": "GCP",
    "sql server": "SQL Server",
}

SCORE_BANDS = {
    "low": {"label": "Low", "color": "#ef4444"},
    "potential": {"label": "Potential", "color": "#f97316"},
    "good": {"label": "Good", "color": "#eab308"},
    "strong": {"label": "Strong", "color": "#22c55e"},
    "neutral": {"label": "Not scored", "color": "#94a3b8"},
}


@dataclass(frozen=True)
class AnalysisView:
    """Successful analysis retained while the browser confirms quota use."""

    result: CompatibilityResult
    score: AICompatibilityScore
    guidance: AIAnalysisGuidance
    job_text: str
    profile_text: str


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.6rem;
            padding-bottom: 3rem;
            max-width: 1120px;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.2rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li {
            font-size: 0.88rem;
            line-height: 1.45;
        }
        .ai-status {
            border: 1px solid rgba(148, 163, 184, 0.24);
            background: rgba(148, 163, 184, 0.06);
            border-radius: 8px;
            padding: 0.8rem 0.85rem;
            margin-bottom: 0.75rem;
        }
        .status-row {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.92rem;
            font-weight: 650;
        }
        .status-detail {
            color: rgba(148, 163, 184, 0.95);
            font-size: 0.8rem;
            margin-top: 0.22rem;
        }
        .status-dot {
            display: inline-block;
            width: 0.55rem;
            height: 0.55rem;
            border-radius: 999px;
            background: #22c55e;
            box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.14);
        }
        .status-missing .status-dot {
            background: #f97316;
            box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.14);
        }
        .skillmatch-hero {
            border: 1px solid rgba(148, 163, 184, 0.22);
            background: rgba(148, 163, 184, 0.055);
            border-radius: 8px;
            padding: 1.2rem 1.35rem;
            margin-bottom: 1rem;
        }
        .skillmatch-hero h1 {
            margin: 0 0 0.35rem 0;
            font-size: 2.15rem;
            line-height: 1.15;
            letter-spacing: 0;
        }
        .skillmatch-hero p {
            margin: 0;
            color: rgba(148, 163, 184, 0.95);
            font-size: 1.02rem;
            max-width: 720px;
        }
        div[data-testid="stTextArea"] textarea {
            border-radius: 8px;
            border-color: rgba(148, 163, 184, 0.28);
            font-size: 0.94rem;
        }
        div[data-testid="stButton"] > button {
            border-radius: 8px;
            border: 1px solid rgba(148, 163, 184, 0.28);
            background: rgba(226, 232, 240, 0.92);
            color: #0f172a;
            font-weight: 650;
            min-height: 2.8rem;
            margin-top: 0.25rem;
        }
        div[data-testid="stButton"] > button:hover {
            border-color: rgba(226, 232, 240, 0.65);
            background: #f8fafc;
            color: #020617;
        }
        .score-card {
            border: 1px solid rgba(148, 163, 184, 0.22);
            background: rgba(148, 163, 184, 0.08);
            border-radius: 8px;
            padding: 0.95rem;
            min-height: 116px;
        }
        .score-card-primary {
            background: rgba(226, 232, 240, 0.11);
            border-color: rgba(226, 232, 240, 0.34);
            min-height: 128px;
        }
        .score-card-accent {
            height: 4px;
            border-radius: 999px;
            margin: 0.2rem 0 0.7rem 0;
        }
        .score-card-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0;
            color: rgba(148, 163, 184, 0.95);
            margin-bottom: 0.45rem;
        }
        .score-card-value {
            font-size: 2rem;
            line-height: 1;
            font-weight: 700;
            margin-bottom: 0.65rem;
        }
        .score-card-primary .score-card-value {
            font-size: 2.65rem;
        }
        .score-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.18rem 0.55rem;
            font-size: 0.78rem;
            font-weight: 600;
            color: #020617;
        }
        .mode-banner {
            border: 1px solid rgba(148, 163, 184, 0.24);
            border-radius: 8px;
            padding: 0.8rem 1rem;
            margin: 0.65rem 0 1rem 0;
            background: rgba(34, 197, 94, 0.08);
            font-size: 0.94rem;
        }
        .assessment-card {
            border: 1px solid rgba(148, 163, 184, 0.22);
            background: rgba(148, 163, 184, 0.06);
            border-radius: 8px;
            padding: 1.1rem 1.2rem;
            margin: 0.8rem 0 1rem 0;
        }
        .assessment-card h2 {
            margin: 0 0 0.35rem 0;
            letter-spacing: 0;
        }
        .assessment-card p {
            margin: 0;
            color: rgba(148, 163, 184, 0.95);
        }
        .skill-chip {
            display: inline-block;
            border: 1px solid rgba(148, 163, 184, 0.28);
            border-radius: 999px;
            padding: 0.3rem 0.68rem;
            margin: 0.16rem 0.2rem 0.16rem 0;
            background: rgba(148, 163, 184, 0.08);
            font-size: 0.88rem;
            line-height: 1.4;
        }
        .chip-strong {
            border-color: rgba(34, 197, 94, 0.45);
            background: rgba(34, 197, 94, 0.1);
        }
        .chip-weak {
            border-color: rgba(234, 179, 8, 0.5);
            background: rgba(234, 179, 8, 0.12);
        }
        .chip-missing {
            border-color: rgba(239, 68, 68, 0.45);
            background: rgba(239, 68, 68, 0.1);
        }
        .category-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 0.75rem;
            margin-bottom: 0.2rem;
        }
        .category-name {
            font-weight: 600;
        }
        .category-score {
            color: rgba(148, 163, 184, 0.95);
            font-variant-numeric: tabular-nums;
        }
        .empty-state {
            border: 1px dashed rgba(148, 163, 184, 0.32);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            margin-top: 1.2rem;
            background: rgba(148, 163, 184, 0.05);
        }
        .empty-state h3 {
            margin: 0 0 0.4rem 0;
            letter-spacing: 0;
        }
        .empty-state p {
            margin: 0;
            color: rgba(148, 163, 184, 0.95);
        }
        [data-testid="stExpander"] {
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 8px;
            background: rgba(148, 163, 184, 0.04);
        }
        div[data-testid="stDownloadButton"] > button {
            border-radius: 8px;
            border-color: rgba(148, 163, 184, 0.28);
            min-height: 2.65rem;
            font-weight: 600;
        }
        @media (max-width: 760px) {
            .block-container {
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .skillmatch-hero {
                padding: 1rem;
            }
            .skillmatch-hero h1 {
                font-size: 1.75rem;
            }
            .score-card,
            .score-card-primary {
                min-height: 104px;
            }
            .score-card-value,
            .score-card-primary .score-card-value {
                font-size: 2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _score_band(score: int | float | None) -> Dict[str, str]:
    if score is None:
        return SCORE_BANDS["neutral"]
    if score <= 25:
        return SCORE_BANDS["low"]
    if score <= 50:
        return SCORE_BANDS["potential"]
    if score <= 75:
        return SCORE_BANDS["good"]
    return SCORE_BANDS["strong"]


def _score_text(score: int | float | None) -> str:
    if score is None:
        return "N/A"
    return f"{round(score)}%"


def _score_card(label: str, score: int | float | None, primary: bool = False) -> None:
    band = _score_band(score)
    card_class = "score-card score-card-primary" if primary else "score-card"
    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="score-card-label">{escape(label)}</div>
            <div class="score-card-accent" style="background:{band['color']}"></div>
            <div class="score-card-value">{_score_text(score)}</div>
            <span class="score-pill" style="background:{band['color']}">{band['label']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _skill_label(skill: str) -> str:
    return SKILL_LABELS.get(skill.lower(), skill.title())


def _sorted_skills(skills: List[str]) -> List[str]:
    return sorted(skills, key=_skill_label)


def _skill_chips(skills: List[str], chip_class: str) -> str:
    return "".join(
        f'<span class="skill-chip {chip_class}">{escape(_skill_label(skill))}</span>'
        for skill in _sorted_skills(skills)
    )


def _result_from_ai_score(score: AICompatibilityScore) -> CompatibilityResult:
    return CompatibilityResult(
        percentage=score.final_score,
        matched=score.strong_skills,
        weak=score.weak_skills,
        missing=score.missing_skills,
        recommendations=score.recommendations,
    )


def _final_assessment(percentage: int, has_weak: bool = False) -> tuple[str, str]:
    if percentage >= 76:
        return "Strong Match", "The profile covers most of the role requirements."
    if percentage >= 51:
        return "Good Match", "The profile aligns with several important role requirements."
    if percentage >= 26:
        return "Potential Match", "Relevant foundations are present, with gaps to close."
    return "Low Match", "The profile has limited evidence for this role."


def _display_saas_onboarding() -> None:
    st.markdown(
        """
        <div class="skillmatch-hero">
            <h1>SkillMatch</h1>
            <p>AI-powered candidate screening with transparent scoring and hiring insights.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _ai_status_panel() -> GeminiClient:
    client = GeminiClient()
    status_class = "status-ready" if client.is_configured else "status-missing"
    status_label = "AI Connected" if client.is_configured else "AI Configuration Required"
    status_detail = (
        "AI extraction active"
        if client.is_configured
        else "AI service not configured"
    )
    st.sidebar.markdown(
        f"""
        <div class="ai-status {status_class}">
            <div class="status-row">
                <span class="status-dot"></span>
                <span>{escape(status_label)}</span>
            </div>
            <div class="status-detail">{escape(status_detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return client


def _sidebar_how_it_works_panel() -> None:
    with st.sidebar.expander("How it works", expanded=False):
        st.markdown(
            "1. Paste a job description.\n"
            "2. Paste a candidate profile or CV.\n"
            "3. Advanced AI extracts structured requirements.\n"
            "4. Python calculates skills, experience and seniority scores.\n"
            "5. Review hiring insights and recommendations."
        )


def _display_mode_banner() -> None:
    st.markdown(
        '<div class="mode-banner">AI-assisted analysis: Advanced language models extract role requirements and Python calculates the compatibility score.</div>',
        unsafe_allow_html=True,
    )


def _display_score_summary(result: CompatibilityResult, score: AICompatibilityScore) -> None:
    st.subheader("Result summary")
    col1, col2, col3, col4 = st.columns([1.35, 1, 1, 1], gap="medium")
    with col1:
        _score_card("Final Score", score.final_score, primary=True)
    with col2:
        _score_card("Skills Score", score.skills_score)
    with col3:
        _score_card("Experience Score", score.experience_score)
    with col4:
        _score_card("Seniority Score", score.seniority_score)
    st.caption(f"Candidate level: {score.candidate_seniority} | Role level: {score.role_seniority}")


def _display_assessment_card(level: str, explanation: str) -> None:
    st.markdown(
        f"""
        <div class="assessment-card">
            <h2>{escape(level)}</h2>
            <p>{escape(explanation)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _display_skill_card(
    title: str,
    skills: List[str],
    chip_class: str,
    empty_message: str,
) -> None:
    with st.container(border=True):
        st.markdown(f"### {title} ({len(skills)})")
        if skills:
            st.markdown(_skill_chips(skills, chip_class), unsafe_allow_html=True)
        else:
            st.info(empty_message)


def _display_why_card(sentences: List[str]) -> None:
    with st.container(border=True):
        st.markdown("### Why This Score")
        for sentence in sentences[:3]:
            st.write(sentence)


def _display_result_sections(result: CompatibilityResult, why_sentences: List[str]) -> None:
    st.subheader("Skill analysis")
    col_match, col_weak, col_missing = st.columns(3, gap="medium")
    with col_match:
        _display_skill_card(
            "Strong Matches",
            result.matched,
            "chip-strong",
            "No strong matches detected.",
        )
    with col_weak:
        _display_skill_card(
            "Partial Matches",
            result.weak,
            "chip-weak",
            "No partial matches detected.",
        )
    with col_missing:
        missing_empty = (
            "No completely missing skills, but some skills are only partial."
            if result.weak
            else "No missing skills detected."
        )
        _display_skill_card("Missing Skills", result.missing, "chip-missing", missing_empty)
    _display_why_card(why_sentences)


def _display_category_progress(category_scores: Dict[str, float]) -> None:
    st.subheader("Category breakdown")
    st.caption("Role fit by skill category.")
    left, right = st.columns(2, gap="medium")
    columns = [left, right]
    for index, category in enumerate(CATEGORY_ORDER):
        score = float(category_scores.get(category, 0.0))
        band = _score_band(score)
        with columns[index % 2]:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="category-row">
                        <span class="category-name">{escape(category)}</span>
                        <span class="category-score">{round(score)}%</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.progress(min(max(score / 100, 0), 1), text=band["label"])


def _display_empty_state(is_configured: bool) -> None:
    mode_note = (
        "AI analysis will score skills, experience, and seniority with intelligent extraction."
        if is_configured
        else "AI analysis requires configuration. Configure the AI service to enable analysis."
    )
    st.markdown(
        f"""
        <div class="empty-state">
            <h3>Ready for analysis</h3>
            <p>{escape(mode_note)} Add both texts above and run the comparison.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _display_ai_guidance(guidance: AIAnalysisGuidance) -> None:
    if not (guidance.recommendations or guidance.interview_tips or guidance.roadmap):
        return
    st.subheader("Hiring guidance")
    col1, col2, col3 = st.columns(3, gap="medium")
    if guidance.recommendations:
        with col1:
            with st.container(border=True):
                st.markdown("### Recommendations")
                for item in guidance.recommendations[:3]:
                    st.write(f"- {item}")
    if guidance.interview_tips:
        with col2:
            with st.container(border=True):
                st.markdown("### Interview tips")
                for item in guidance.interview_tips[:4]:
                    st.write(f"- {item}")
    if guidance.roadmap:
        with col3:
            with st.container(border=True):
                st.markdown("### Learning roadmap")
                for idx, item in enumerate(guidance.roadmap[:5], start=1):
                    st.write(f"{idx}. {item}")


def _display_usage_status(usage: BrowserUsage, consume_pending: bool) -> None:
    if usage.error:
        st.error(
            "No se puede acceder al contador de este navegador. "
            "Comprueba que localStorage esté habilitado."
        )
        return
    if not usage.ready:
        st.caption("Cargando los usos disponibles de este navegador...")
        return

    st.caption(f"Análisis gratuitos disponibles: {usage.remaining}/{usage.limit}")
    if usage.is_blocked:
        st.error(
            "Has alcanzado el límite de 2 análisis gratuitos en 24 horas. "
            "Vuelve a intentarlo más tarde."
        )
    elif consume_pending:
        st.caption("Actualizando el contador de usos...")


def _display_analysis(view: AnalysisView) -> None:
    _display_score_summary(view.result, view.score)
    level, explanation = _final_assessment(
        view.result.percentage,
        bool(view.result.weak),
    )
    _display_assessment_card(level, explanation)
    _display_result_sections(view.result, view.score.why_sentences)
    _display_category_progress(view.score.category_scores)
    _display_ai_guidance(view.guidance)
    _export_results(view.result, view.job_text, view.profile_text)


def _export_results(result: CompatibilityResult, job_text: str, profile_text: str) -> None:
    md = (
        f"# SkillMatch Analysis\n\n"
        f"**Job description**\n\n```\n{job_text}\n```\n\n"
        f"**Candidate profile**\n\n```\n{profile_text}\n```\n\n"
        f"**Compatibility:** {result.percentage}%\n\n"
        f"**Strong matches:** {', '.join(_skill_label(s) for s in _sorted_skills(result.matched))}\n"
        f"**Weak matches:** {', '.join(_skill_label(s) for s in _sorted_skills(result.weak))}\n"
        f"**Missing skills:** {', '.join(_skill_label(s) for s in _sorted_skills(result.missing))}\n"
        f"**Recommendations:**\n"
        + "\n".join([f"- {r}" for r in result.recommendations])
        + "\n"
    )
    payload = {
        "job": job_text,
        "profile": profile_text,
        "percentage": result.percentage,
        "matched": result.matched,
        "weak": result.weak,
        "missing": result.missing,
        "recommendations": result.recommendations,
    }
    with st.container(border=True):
        st.markdown("### Export analysis")
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            st.download_button(
                label="Download Markdown",
                data=md,
                file_name="skillmatch_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                label="Download JSON",
                data=json.dumps(payload, indent=2),
                file_name="skillmatch_report.json",
                mime="application/json",
                use_container_width=True,
            )


def run() -> None:
    st.set_page_config(page_title="SkillMatch", layout="wide", initial_sidebar_state="expanded")
    _inject_styles()

    gemini_client = _ai_status_panel()
    _sidebar_how_it_works_panel()
    _display_saas_onboarding()

    pending_token = st.session_state.get("analysis_usage_consume_token")
    if not isinstance(pending_token, str):
        pending_token = None
    usage = get_browser_usage(pending_token)
    if pending_token and usage.applied_token == pending_token:
        del st.session_state["analysis_usage_consume_token"]
        pending_token = None
    consume_pending = pending_token is not None

    col1, col2 = st.columns(2)
    with col1:
        job_input = st.text_area(
            "Job description",
            value="",
            height=260,
            placeholder="Paste the full job posting here...",
        )
    with col2:
        profile_input = st.text_area(
            "Candidate profile",
            value="",
            height=260,
            placeholder="Paste a CV, skill list, or personal summary...",
        )

    if not gemini_client.is_configured:
        st.warning(
            "AI service not configured. Add the required environment variable, then restart the app."
        )

    _display_usage_status(usage, consume_pending)

    analyze = st.button(
        "Analyze",
        type="primary",
        use_container_width=True,
        disabled=(
            not gemini_client.is_configured
            or not usage.ready
            or usage.is_blocked
            or consume_pending
        ),
    )
    if not analyze:
        last_analysis = st.session_state.get("last_analysis")
        if isinstance(last_analysis, AnalysisView):
            _display_analysis(last_analysis)
        else:
            _display_empty_state(gemini_client.is_configured)
        return

    if not job_input.strip() or not profile_input.strip():
        st.warning("Both the job description and candidate profile must contain text.")
        return

    _display_mode_banner()
    try:
        with st.spinner("Running intelligent analysis..."):
            ai_job = gemini_client.extract_job(job_input)
            ai_candidate = gemini_client.extract_candidate(profile_input)
            ai_score = score_ai_compatibility(ai_job, ai_candidate)
            ai_guidance = gemini_client.generate_guidance(ai_job, ai_candidate, ai_score)
    except GeminiExtractionError:
        st.error(
            "AI analysis failed. The analysis service may be unavailable, timed out, "
            "or returned an invalid response. Please retry later."
        )
        return

    result = _result_from_ai_score(ai_score)
    if ai_guidance.recommendations:
        result = CompatibilityResult(
            percentage=result.percentage,
            matched=result.matched,
            weak=result.weak,
            missing=result.missing,
            recommendations=ai_guidance.recommendations,
        )

    st.session_state["last_analysis"] = AnalysisView(
        result=result,
        score=ai_score,
        guidance=ai_guidance,
        job_text=job_input,
        profile_text=profile_input,
    )
    st.session_state["analysis_usage_consume_token"] = uuid.uuid4().hex
    st.rerun()
