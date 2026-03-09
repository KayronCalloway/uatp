"""
Analysis Dashboard component for the UATP Capsule Visualizer.

This component provides high-level metrics and visualizations of the capsule chain.
"""

from typing import Dict, List

import altair as alt
import pandas as pd
import streamlit as st
from capsule_schema import Capsule

from visualizer.utils.colors import CAPSULE_TYPE_COLORS


def render_analysis(capsules: List[Capsule], capsule_map: Dict[str, Capsule]):
    """Render the analysis dashboard with metrics and charts."""
    st.header("Analysis Dashboard")

    if not capsules:
        st.warning("No capsule data available for analysis.")
        return

    df = pd.DataFrame([c.dict() for c in capsules])
    cqss_scores = st.session_state.get("filters", {}).get("_capsule_scores", {})
    df["cqss_score"] = df["capsule_id"].map(cqss_scores)

    # --- High-Level Metrics ---
    st.subheader("Chain Overview")
    total_capsules = len(df)
    total_agents = df["agent_id"].nunique()
    total_forks = df["previous_capsule_id"].value_counts().gt(1).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Capsules", total_capsules)
    col2.metric("Unique Agents", total_agents)
    col3.metric("Chain Forks", total_forks)

    st.markdown("---")

    # --- Visualizations ---
    col1, col2 = st.columns(2)

    with col1:
        # Capsule Type Distribution (Pie Chart)
        st.subheader("Capsule Types")
        type_counts = df["capsule_type"].value_counts().reset_index()
        type_counts.columns = ["capsule_type", "count"]

        chart = (
            alt.Chart(type_counts)
            .mark_arc(innerRadius=50)
            .encode(
                theta=alt.Theta(field="count", type="quantitative"),
                color=alt.Color(
                    field="capsule_type",
                    type="nominal",
                    scale=alt.Scale(
                        domain=list(CAPSULE_TYPE_COLORS.keys()),
                        range=list(CAPSULE_TYPE_COLORS.values()),
                    ),
                    legend=alt.Legend(title="Capsule Type"),
                ),
                tooltip=["capsule_type", "count"],
            )
            .properties(width=300, height=300)
        )
        st.altair_chart(chart, use_container_width=True)

    with col2:
        # CQSS Score Distribution (Histogram)
        st.subheader("CQSS Distribution")
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                alt.X("cqss_score:Q", bin=alt.Bin(maxbins=20), title="CQSS Score"),
                alt.Y("count()", title="Number of Capsules"),
                tooltip=[
                    alt.Tooltip("count()", title="Count"),
                    alt.Tooltip("cqss_score:Q", title="Score Range"),
                ],
            )
            .properties(width=300, height=300)
        )
        st.altair_chart(chart, use_container_width=True)

    # Agent Activity (Bar Chart)
    st.subheader("Agent Activity")
    agent_activity = df["agent_id"].value_counts().reset_index()
    agent_activity.columns = ["agent_id", "count"]
    chart = (
        alt.Chart(agent_activity)
        .mark_bar()
        .encode(
            x=alt.X("agent_id:N", title="Agent ID", sort="-y"),
            y=alt.Y("count:Q", title="Capsules Created"),
            color=alt.Color("agent_id:N", legend=None),
            tooltip=["agent_id", "count"],
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)
