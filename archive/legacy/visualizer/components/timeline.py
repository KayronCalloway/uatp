"""
Timeline visualization component for the UATP Capsule Visualizer.
"""

from datetime import datetime
from typing import Dict, List

import altair as alt
import pandas as pd
import streamlit as st
from capsule_schema import Capsule

from visualizer.utils.colors import CAPSULE_TYPE_COLORS
from visualizer.utils.state import select_capsule


def render_timeline(capsules: List[Capsule], capsule_map: Dict[str, Capsule]):
    """Render an interactive timeline view of capsules."""
    st.header("Capsule Timeline")

    # Get CQSS filter from session state
    filters = st.session_state.get("filters", {})
    min_cqss = filters.get("min_cqss_score", 0)
    capsule_scores = filters.get("_capsule_scores", {})

    # Filter capsules by CQSS score if set
    if min_cqss > 0 and capsule_scores:
        capsules = [
            c for c in capsules if capsule_scores.get(c.capsule_id, 0) >= min_cqss
        ]

    # Configuration options
    col1, col2 = st.columns([1, 2])
    with col1:
        view_type = st.radio(
            "View Type",
            ["Swimlanes", "Combined"],
            help="Swimlanes: Group by type/agent | Combined: Show all in one timeline",
        )
    with col2:
        grouping = st.radio(
            "Group By",
            ["Capsule Type", "Agent"],
            horizontal=True,
            help="Group timeline entries by capsule type or agent",
        )

    # Prepare data for visualization
    timeline_data = []
    for capsule in capsules:
        # Get timestamp and ensure it's a datetime
        timestamp = capsule.timestamp
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                # Use current time if we can't parse
                timestamp = datetime.now()

        # Determine grouping category
        if grouping == "Capsule Type":
            category = capsule.capsule_type
        else:  # Group by Agent
            category = capsule.agent_id

        # Get appropriate color
        color = CAPSULE_TYPE_COLORS.get(
            capsule.capsule_type, CAPSULE_TYPE_COLORS["DEFAULT"]
        )

        # Create data entry
        timeline_data.append(
            {
                "id": capsule.capsule_id,
                "timestamp": timestamp,
                "category": category,
                "type": capsule.capsule_type,
                "title": f"{capsule.capsule_type[:3]}... {capsule.capsule_id[:6]}...",
                "color": color,
            }
        )

    if not timeline_data:
        st.warning("No capsule data available for timeline.")
        return

    # Create DataFrame and sort by timestamp
    df = pd.DataFrame(timeline_data)
    df = df.sort_values(by="timestamp")

    # Render appropriate visualization based on view type
    if view_type == "Swimlanes":
        render_swimlane_timeline(df)
    else:
        render_combined_timeline(df)

    # Additional timeline controls and filters
    st.subheader("Timeline Filters")
    col1, col2 = st.columns(2)

    with col1:
        # Date range selector
        min_date = df["timestamp"].min().date()
        max_date = df["timestamp"].max().date()
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

    with col2:
        # Category filter (dynamically generated based on grouping)
        categories = sorted(df["category"].unique())
        selected_categories = st.multiselect(
            f"Filter {grouping}", options=categories, default=categories
        )

    # Apply filters if specified
    filtered_df = df.copy()
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df["timestamp"].dt.date >= start_date)
            & (filtered_df["timestamp"].dt.date <= end_date)
        ]

    if selected_categories:
        filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]

    # Display the filtered timeline data
    st.subheader("Timeline Details")
    # Convert timestamp to a more readable format
    filtered_df["formatted_time"] = filtered_df["timestamp"].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # Display the data table with interactive selection
    st.dataframe(
        filtered_df[["formatted_time", "category", "type", "id"]],
        use_container_width=True,
        column_config={
            "id": st.column_config.Column("Capsule ID"),
            "category": st.column_config.Column(grouping),
            "type": st.column_config.Column("Capsule Type"),
            "formatted_time": st.column_config.Column("Timestamp"),
        },
        hide_index=True,
    )

    # Interactive selection from the table
    selected_capsule_id = st.selectbox(
        "Select a capsule to view details",
        options=filtered_df["id"].tolist(),
        format_func=lambda x: f"{x[:8]}... ({filtered_df[filtered_df['id']==x]['type'].iloc[0]})",
    )

    if selected_capsule_id and st.button("View Selected Capsule"):
        select_capsule(selected_capsule_id)
        # Switch to overview to see the details
        st.session_state["current_view"] = "overview"
        st.rerun()


def render_swimlane_timeline(df):
    """Render the timeline in swimlanes grouped by category."""
    # Create chart
    chart = (
        alt.Chart(df)
        .mark_circle(size=100)
        .encode(
            x=alt.X("timestamp:T", axis=alt.Axis(title="Time", grid=True)),
            y=alt.Y("category:N", axis=alt.Axis(title=None)),
            color=alt.Color(
                "type:N",
                scale=alt.Scale(
                    domain=list(CAPSULE_TYPE_COLORS.keys()),
                    range=list(CAPSULE_TYPE_COLORS.values()),
                ),
            ),
            tooltip=["id", "type", "timestamp"],
            size=alt.value(80),
        )
        .properties(
            height=30
            * len(df["category"].unique()),  # Dynamic height based on categories
            width=650,
        )
        .interactive()
    )

    # Add text labels
    text = chart.mark_text(align="left", baseline="middle", dx=15, fontSize=10).encode(
        text="title"
    )

    # Combine the chart and text marks
    final_chart = (
        (chart + text)
        .configure_view(strokeWidth=0)
        .configure_axis(labelFontSize=12, titleFontSize=14)
    )

    st.altair_chart(final_chart, use_container_width=True)


def render_combined_timeline(df):
    """Render all capsules in a single combined timeline."""
    # Create a scatter plot with point color by capsule type
    scatter = (
        alt.Chart(df)
        .mark_circle()
        .encode(
            x=alt.X("timestamp:T", axis=alt.Axis(title="Time", grid=True)),
            y=alt.Y("jitter:Q", title=None, axis=None),
            color=alt.Color(
                "type:N",
                scale=alt.Scale(
                    domain=list(CAPSULE_TYPE_COLORS.keys()),
                    range=list(CAPSULE_TYPE_COLORS.values()),
                ),
            ),
            size=alt.value(100),
            tooltip=["id", "type", "category", "timestamp"],
        )
        .transform_calculate(
            # Add some jitter on the y-axis
            jitter="random() * 0.6"
        )
        .properties(height=180)
        .interactive()
    )

    # Create a rule mark for time axis
    rule = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule().encode(y="y")

    # Combine the chart elements
    combined_chart = (
        (scatter + rule)
        .configure_view(strokeWidth=0)
        .configure_axis(labelFontSize=12, titleFontSize=14)
    )

    st.altair_chart(combined_chart, use_container_width=True)
