"""Polished Streamlit UI for SkillMatch (v3).

Features added in this iteration:
* Onboarding overlay explaining the app purpose and usage.
* "How it works" expander in the sidebar.
* Enhanced demo mode with selectable job offers and candidate profiles, each with a short description.
* Natural‑language recommendations that include priority levels.
* Interview‑preparation suggestions and a concise learning roadmap.
* Clean visual hierarchy and spacing.
"""

from __future__ import annotations

import json
import pathlib
from typing import Dict, List, Tuple

import streamlit as st

from ..domain.services import extract_skills, calculate_compatibility
from ..domain.entities import CompatibilityResult
from .plotters import compatibility_bar, skill_pie, category_radar

# ---------------------------------------------------------------------------
# Configuration – demo data paths and interview/question templates
# ---------------------------------------------------------------------------
DEMO_DIR = pathlib.Path(__file__).parents[3] / "data" / "demo"
DEMO_JOBS = {
    "Junior Backend Java": {
        "file": DEMO_DIR / "junior_backend_java.txt",
        "desc": "Classic Java backend role – Spring Boot, Docker, MySQL.",
    },
    "Junior Python Developer": {
        "file": DEMO_DIR / "junior_python_developer.txt",
        "desc": "Python backend – Flask/FastAPI, PostgreSQL, Docker.",
    },
    "Full‑Stack Junior": {
        "file": DEMO_DIR / "fullstack_junior.txt",
        "desc": "React front‑end plus Python/Node back‑end, DBs, Docker.",
    },
}
DEMO_PROFILES = {
    "Manuel (Full‑Stack)": {
        "file": DEMO_DIR / "manuel_profile.txt",
        "desc": "Manuel's real CV – mixes Python, JavaScript, Docker, Git.",
    }
}

# Simple interview question bank per category (can be expanded later)
INTERVIEW_QUESTIONS: Dict[str, List[str]] = {
    "Programming Languages": [
        "Explain the differences between static and dynamic typing.",
        "When would you choose Java over Python?",
    ],
    "Frameworks": [
        "What are the main advantages of using Spring Boot?",
        "How does FastAPI achieve high performance?",
    ],
    "DevOps": ["Describe the purpose of Docker containers.", "What is Kubernetes and when would you use it?"],
    "Databases": ["When would you prefer NoSQL over a relational database?"],
    "Soft Skills": ["Give an example of a time you demonstrated teamwork."],
}

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def _priority_label(weight: float) -> str:
    if weight >= 0.20:
        return "High"
    if weight >= 0.10:
        return "Medium"
    return "Low"

def _load_demo(file_path: pathlib.Path) -> str:
    return file_path.read_text(encoding="utf-8")

def _display_onboarding() -> None:
    """Render the landing hero section with a clear headline and value proposition.

    The hero occupies the top of the app, giving recruiters an immediate sense of
    purpose and professionalism within a few seconds.
    """
    st.title("SkillMatch – Match Jobs to Talent Instantly")
    st.subheader("Instantly see how a candidate fits a role, discover skill gaps, and get a clear learning roadmap.")
    st.info(
        "*Paste a job description on the left and a candidate profile on the right, then click **Analyze**.\n"
        "The dashboard instantly shows a compatibility score, matched & missing skills,\n"
        "priority‑ranked recommendations, interview tips, and a concise learning path.*"
    )
    st.markdown("---")

def _sidebar_how_it_works() -> None:
    with st.sidebar.expander("How it works", expanded=False):
        st.markdown(
            "1️⃣ **Paste a job offer** – copy the description from LinkedIn, Indeed, etc.\n"
            "2️⃣ **Paste a candidate profile** – upload your CV, a list of skills, or a personal summary.\n"
            "3️⃣ **Click Analyze** – the engine extracts skills, scores the match, and classifies gaps.\n"
            "4️⃣ **Review results** – see the compatibility percentage, matched/missing skills,\n"
            "   priority‑ranked recommendations, interview preparation tips, and a learning roadmap."
        )

def _sidebar_demo_selector() -> Tuple[str, str]:
    st.sidebar.markdown("## Demo mode (optional)")
    st.sidebar.caption("Select one of the predefined examples to quickly test the app.")
    job_option = st.sidebar.selectbox(
        "Job offer", ["-- none --"] + list(DEMO_JOBS.keys()), index=0
    )
    profile_option = st.sidebar.selectbox(
        "Candidate profile", ["-- none --"] + list(DEMO_PROFILES.keys()), index=0
    )
    return job_option, profile_option

def _display_demo_explanations(job_key: str, profile_key: str) -> None:
    if job_key != "-- none --":
        st.info(f"**Job demo:** {DEMO_JOBS[job_key]['desc']}")
    if profile_key != "-- none --":
        st.info(f"**Profile demo:** {DEMO_PROFILES[profile_key]['desc']}")

def _display_metrics(result: CompatibilityResult, category_scores: Dict[str, float]) -> None:
    """Display the top‑level metrics in a visual card layout.

    The three primary numbers – compatibility score, matched skill count and
    missing skill count – are shown side‑by‑side with prominent styling. The
    compatibility metric uses a background colour that reflects the overall
    match quality (green → excellent, red → poor)."""
    col1, col2, col3 = st.columns(3)
    # Compatibility card with colour cue
    if result.percentage >= 90:
        comp_color = "#d4edda"  # light green
    elif result.percentage >= 75:
        comp_color = "#c3e6cb"  # green
    elif result.percentage >= 60:
        comp_color = "#ffeeba"  # light orange
    elif result.percentage >= 40:
        comp_color = "#f8d7da"  # light red
    else:
        comp_color = "#f5c6cb"  # darker red
    with col1:
        st.markdown(f"<div style='background:{comp_color};padding:10px;border-radius:5px'>", unsafe_allow_html=True)
        st.metric("Compatibility", f"{result.percentage}%")
        st.markdown("</div>", unsafe_allow_html=True)
    # Matched skills card
    with col2:
        st.markdown("<div style='background:#e2e3e5;padding:10px;border-radius:5px'>", unsafe_allow_html=True)
        st.metric("Matched skills", len(result.matched))
        st.markdown("</div>", unsafe_allow_html=True)
    # Missing skills card
    with col3:
        st.markdown("<div style='background:#f8d7da;padding:10px;border-radius:5px'>", unsafe_allow_html=True)
        st.metric("Missing skills", len(result.missing))
        st.markdown("</div>", unsafe_allow_html=True)


def _final_assessment(percentage: int) -> Tuple[str, str]:
    if percentage >= 90:
        return "Excellent Match", "Your profile aligns very closely with the job requirements."
    if percentage >= 75:
        return "Strong Match", "You cover most of the core skills required."
    if percentage >= 60:
        return "Potential Match", "There are a few gaps to address for a stronger fit."
    if percentage >= 40:
        return "Weak Match", "Significant skill gaps exist; consider upskilling."
    return "Poor Match", "The current profile does not meet the majority of required skills."

def _recommendations_by_priority(
    missing: List[str],
    offer_cat: Dict[str, List[str]],
    category_weights: Dict[str, float],
) -> List[Tuple[str, str]]:
    recs: List[Tuple[str, str]] = []
    skill_weights: Dict[str, float] = {}
    for cat, skills in offer_cat.items():
        w = category_weights.get(cat, 0.0)
        for sk in skills:
            if sk in missing:
                skill_weights[sk] = w
    for skill, weight in sorted(skill_weights.items(), key=lambda x: -x[1])[:3]:
        priority = _priority_label(weight)
        recs.append((priority, f"Learn **{skill.title()}** ({priority} priority) to boost compatibility."))
    return recs

def _display_recommendations(recs: List[Tuple[str, str]]) -> None:
    st.subheader("Recommendations (by priority)")
    for _, text in recs:
        st.write(text)

def _interview_preparation(missing: List[str], offer_cat: Dict[str, List[str]]) -> None:
    st.subheader("Interview preparation tips")
    missing_cats = {cat for cat, skills in offer_cat.items() if any(s in missing for s in skills)}
    tips: List[str] = []
    for cat in missing_cats:
        tips.extend(INTERVIEW_QUESTIONS.get(cat, []))
    if tips:
        st.markdown("*Possible interview questions to study:*")
        for t in tips[:5]:
            st.write(f"- {t}")
    else:
        st.info("All core categories are covered – focus on soft‑skill questions.")

def _learning_roadmap(recs: List[Tuple[str, str]]) -> None:
    if not recs:
        return
    st.subheader("Suggested learning roadmap")
    steps = [text.split("**")[1].split("**")[0] for _, text in recs]
    for idx, skill in enumerate(steps, start=1):
        st.markdown(f"{idx}. **{skill}** – start with tutorials or official docs.")
    st.caption("After mastering the above, consider exploring adjacent technologies for deeper expertise.")

def _export_results(result: CompatibilityResult, job_text: str, profile_text: str) -> None:
    st.subheader("Export analysis")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export as Markdown"):
            md = (
                f"# SkillMatch Analysis\n\n"
                f"**Job description**\n\n```\n{job_text}\n```\n\n"
                f"**Candidate profile**\n\n```\n{profile_text}\n```\n\n"
                f"**Compatibility:** {result.percentage}%\n\n"
                f"**Matched skills**: {', '.join(result.matched)}\n"
                f"**Missing skills**: {', '.join(result.missing)}\n"
                f"**Recommendations**:\n"
                + "\n".join([f"- {r}" for r in result.recommendations])
                + "\n"
            )
            st.download_button(
                label="Download Markdown",
                data=md,
                file_name="skillmatch_report.md",
                mime="text/markdown",
            )
    with col2:
        if st.button("Export as JSON"):
            payload = {
                "job": job_text,
                "profile": profile_text,
                "percentage": result.percentage,
                "matched": result.matched,
                "missing": result.missing,
                "recommendations": result.recommendations,
            }
            st.download_button(
                label="Download JSON",
                data=json.dumps(payload, indent=2),
                file_name="skillmatch_report.json",
                mime="application/json",
            )

# ---------------------------------------------------------------------------
# Main app entry point
# ---------------------------------------------------------------------------
def run() -> None:
    st.set_page_config(page_title="SkillMatch", layout="wide", initial_sidebar_state="expanded")
    _sidebar_how_it_works()
    job_key, profile_key = _sidebar_demo_selector()
    _display_onboarding()
    job_text = ""
    profile_text = ""
    if job_key != "-- none --":
        job_text = _load_demo(DEMO_JOBS[job_key]["file"])
    if profile_key != "-- none --":
        profile_text = _load_demo(DEMO_PROFILES[profile_key]["file"])
    if job_key != "-- none --" or profile_key != "-- none --":
        _display_demo_explanations(job_key, profile_key)
    col1, col2 = st.columns(2)
    with col1:
        job_input = st.text_area(
            "Job description",
            value=job_text,
            height=250,
            placeholder="Paste the full job posting here...",
        )
    with col2:
        profile_input = st.text_area(
            "Candidate profile",
            value=profile_text,
            height=250,
            placeholder="Paste a CV, skill list, or personal summary...",
        )
    if st.button("Analyze"):
        if not job_input.strip() or not profile_input.strip():
            st.warning("Both the job description and candidate profile must contain text.")
            return
        offer_set, offer_cat = extract_skills(job_input)
        profile_set, profile_cat = extract_skills(profile_input)
        result = calculate_compatibility(offer_set, profile_set, offer_cat, profile_cat)
        category_weights = {
            "Programming Languages": 0.25,
            "Frameworks": 0.20,
            "DevOps": 0.15,
            "Cloud": 0.10,
            "Databases": 0.10,
            "Tools": 0.05,
            "Testing": 0.05,
            "Soft Skills": 0.05,
        }
        category_scores = {}
        for cat in category_weights:
            offer_sk = offer_cat.get(cat, [])
            profile_sk = profile_cat.get(cat, [])
            if not offer_sk:
                score = 1.0
            else:
                score = len(set(offer_sk).intersection(profile_sk)) / len(offer_sk)
            category_scores[cat] = score
        _display_metrics(result, category_scores)
        level, expl = _final_assessment(result.percentage)
        st.subheader(level)
        st.write(expl)
        col_match, col_missing = st.columns(2)
        with col_match:
            st.markdown("**Matched skills**")
            if result.matched:
                for s in result.matched:
                    st.write(f"- ✔ {s.title()}")
            else:
                st.info("No matches found.")
        with col_missing:
            st.markdown("**Missing skills**")
            if result.missing:
                for s in result.missing:
                    st.write(f"- ✘ {s.title()}")
            else:
                st.info("No missing skills – perfect match!")
        st.subheader("Charts")
        st.plotly_chart(compatibility_bar(result.percentage), use_container_width=True)
        st.plotly_chart(category_radar(category_scores), use_container_width=True)
        st.plotly_chart(skill_pie(result.matched, result.missing), use_container_width=True)
        recs = _recommendations_by_priority(result.missing, offer_cat, category_weights)
        _display_recommendations(recs)
        _interview_preparation(result.missing, offer_cat)
        _learning_roadmap(recs)
        _export_results(result, job_input, profile_input)
