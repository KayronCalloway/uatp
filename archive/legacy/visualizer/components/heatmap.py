"""
Heatmap visualization component for the UATP Capsule Visualizer.
"""

from typing import Dict, List

import altair as alt
import pandas as pd
import streamlit as st
from capsule_schema import Capsule


def render_heatmap(capsules: List[Capsule], capsule_map: Dict[str, Capsule]):
    """Render a heatmap of capsule activity by time and agent/type."""
    st.header("Capsule Activity Heatmap")

    # Prepare data
    data = []
    for c in capsules:
        # Extract key fields
        ts = getattr(c, "timestamp", None)
        if ts is None:
            continue
        # Convert to date (day granularity)
        date = pd.to_datetime(ts).date()
        agent = getattr(c, "agent_id", "Unknown")
        ctype = getattr(c, "capsule_type", "Unknown")
        data.append({"date": date, "agent": agent, "type": ctype})
    if not data:
        st.warning("No capsule data available for heatmap.")
        return
    df = pd.DataFrame(data)

    # User selects grouping
    group_by = st.radio("Group by", ["Agent", "Capsule Type"], horizontal=True)
    if group_by == "Agent":
        group_col = "agent"
    else:
        group_col = "type"

    # Pivot table: rows=group, cols=date, values=count
    pivot = df.groupby([group_col, "date"]).size().reset_index(name="count")

    # Build heatmap
    chart = (
        alt.Chart(pivot)
        .mark_rect()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y(f"{group_col}:N", title=group_by),
            color=alt.Color(
                "count:Q",
                scale=alt.Scale(scheme="blues"),
                legend=alt.Legend(title="Capsules"),
            ),
            tooltip=["date", group_col, "count"],
        )
        .properties(width=650, height=30 * len(pivot[group_col].unique()))
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption(
        "Darker squares = more capsules. Group by agent or capsule type. Hover for details."
    )
