"""Plotly visualisation helpers for SkillMatch (v2).

The helpers provide:
* Compatibility gauge bar (horizontal)
* Skill breakdown pie chart
* Category radar/spider chart showing match ratio per category
* Simple metric‑card style figures (used as Streamlit st.metric placeholders)
"""

from __future__ import annotations

import plotly.graph_objects as go
from typing import Dict, List, Tuple


def compatibility_bar(percentage: int) -> go.Figure:
    """Horizontal bar displaying the overall compatibility percentage.

    Green for >=70 %, orange otherwise.
    """
    color = "#2ecc71" if percentage >= 70 else "#e67e22"
    fig = go.Figure(
        go.Bar(
            x=[percentage],
            y=[""],
            orientation="h",
            marker=dict(color=color),
            width=0.4,
            hoverinfo="skip",
            text=f"{percentage}%",
            textposition="inside",
            textfont=dict(color="white"),
        )
    )
    fig.update_layout(
        xaxis=dict(range=[0, 100], visible=False, fixedrange=True),
        yaxis=dict(showticklabels=False, visible=False),
        margin=dict(l=0, r=0, t=10, b=10),
        height=80,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


def skill_pie(matched: List[str], missing: List[str]) -> go.Figure:
    """Pie chart with two slices – matched vs missing skills. """
    values = [len(matched), len(missing)]
    labels = [f"Matched ({len(matched)})", f"Missing ({len(missing)})"]
    colors = ["#2ecc71", "#e74c3c"]
    fig = go.Figure(
        go.Pie(
            values=values,
            labels=labels,
            marker=dict(colors=colors),
            hole=0.5,
            textinfo="label+percent",
        )
    )
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
    return fig


def category_radar(category_scores: Dict[str, float]) -> go.Figure:
    """Radar (spider) chart showing match ratio per category.

    ``category_scores`` should contain values between 0 and 1.
    """
    categories = list(category_scores.keys())
    scores = [category_scores[c] for c in categories]
    # Close the radar shape by repeating the first value
    categories += [categories[0]]
    scores += [scores[0]]
    fig = go.Figure(
        go.Scatterpolar(r=scores, theta=categories, fill="toself", name="Match", line=dict(color="#3498db"))
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1], tickformat=".0%")),
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig
