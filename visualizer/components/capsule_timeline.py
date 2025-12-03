"""Timeline visualization component for UATP 7.0 capsules.

This module provides visualization tools for displaying capsules in a
chronological timeline view, making it easier to understand temporal relationships
and evolution of capsule chains as defined in the UATP 7.0 white paper.
"""

from datetime import datetime
from typing import List, Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Import capsule types
from capsule_schema import Capsule
from plotly import graph_objects as go

from visualizer.components.capsule_network import extract_capsule_relationships

# Import color utilities
from visualizer.utils.colors import CAPSULE_TYPE_COLORS


def parse_capsule_datetime(timestamp_str: str) -> datetime:
    """Parse capsule timestamp string into datetime object.

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        Datetime object
    """
    try:
        # Try to parse ISO format with milliseconds
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        try:
            # Try to parse ISO format without milliseconds
            return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
        except (ValueError, AttributeError):
            # Return current time as fallback
            return datetime.now()


def extract_timeline_data(capsules: List[Capsule]) -> pd.DataFrame:
    """Extract timeline data from capsules.

    Args:
        capsules: List of capsules to include in the timeline

    Returns:
        Pandas DataFrame with timeline data
    """
    timeline_data = []

    for capsule in capsules:
        if not hasattr(capsule, "capsule_id"):
            continue

        # Extract timestamp and parse to datetime
        timestamp = (
            parse_capsule_datetime(capsule.timestamp)
            if hasattr(capsule, "timestamp")
            else datetime.now()
        )

        # Extract capsule type and other attributes
        capsule_type = getattr(capsule, "capsule_type", "Unknown")

        # Safely convert confidence to float
        try:
            confidence_val = getattr(capsule, "confidence", 0.0)
            # Handle both numeric and string confidence values
            if isinstance(confidence_val, (int, float)):
                confidence = float(confidence_val)
            elif (
                isinstance(confidence_val, str)
                and confidence_val.replace(".", "", 1).isdigit()
            ):
                confidence = float(confidence_val)
            else:
                confidence = 0.0  # Default if conversion not possible
        except (ValueError, TypeError):
            confidence = 0.0

        agent_id = getattr(capsule, "agent_id", "Unknown")

        # Get color for capsule type
        color = CAPSULE_TYPE_COLORS.get(capsule_type, CAPSULE_TYPE_COLORS["DEFAULT"])

        # Append data
        timeline_data.append(
            {
                "capsule_id": capsule.capsule_id,
                "timestamp": timestamp,
                "capsule_type": capsule_type,
                "agent_id": agent_id,
                "confidence": confidence,
                "color": color,
                "previous_capsule_id": getattr(capsule, "previous_capsule_id", None),
            }
        )

    # Convert to DataFrame and sort by timestamp
    df = pd.DataFrame(timeline_data)
    if not df.empty:
        df = df.sort_values("timestamp")

    return df


def render_timeline_matplotlib(
    capsules: List[Capsule], highlighted_capsule_id: Optional[str] = None
):
    """Render a capsule timeline visualization using Matplotlib.

    Args:
        capsules: List of capsules to include in the timeline
        highlighted_capsule_id: Optional ID of capsule to highlight
    """
    if not capsules:
        st.warning("No capsules available to visualize timeline")
        return

    # Extract timeline data
    df = extract_timeline_data(capsules)

    if df.empty:
        st.warning("No valid capsules found with proper timestamps")
        return

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create y-positions for each capsule type (staggered for readability)
    capsule_types = df["capsule_type"].unique()
    type_positions = {t: i for i, t in enumerate(capsule_types)}

    # Plot each capsule as a point
    for _, row in df.iterrows():
        y_pos = type_positions[row["capsule_type"]]
        marker_size = 100  # Default size
        alpha = 0.8  # Default opacity
        edgecolor = "black"  # Default edge color
        linewidth = 1  # Default edge width

        # Highlight the selected capsule if provided
        if highlighted_capsule_id and row["capsule_id"] == highlighted_capsule_id:
            marker_size = 150
            alpha = 1.0
            edgecolor = "white"
            linewidth = 2

        # Plot the capsule
        ax.scatter(
            row["timestamp"],
            y_pos,
            s=marker_size,
            color=row["color"],
            alpha=alpha,
            edgecolor=edgecolor,
            linewidth=linewidth,
            zorder=3,
        )

        # Add capsule ID label
        ax.text(
            row["timestamp"],
            y_pos + 0.15,
            row["capsule_id"][:8] + "...",
            fontsize=8,
            ha="center",
            va="bottom",
            rotation=45,
            alpha=0.8,
        )

    # Add connections between capsules based on previous_capsule_id
    for _, row in df.iterrows():
        if pd.notna(row["previous_capsule_id"]):
            # Find the previous capsule
            prev_rows = df[df["capsule_id"] == row["previous_capsule_id"]]
            if not prev_rows.empty:
                prev_row = prev_rows.iloc[0]

                # Draw an arrow from previous to current
                ax.annotate(
                    "",
                    xy=(row["timestamp"], type_positions[row["capsule_type"]]),
                    xytext=(
                        prev_row["timestamp"],
                        type_positions[prev_row["capsule_type"]],
                    ),
                    arrowprops=dict(arrowstyle="->", color="gray", alpha=0.6),
                    zorder=1,
                )

    # Configure axes
    ax.set_yticks(list(type_positions.values()))
    ax.set_yticklabels(list(type_positions.keys()))
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Capsule Type")

    # Format x-axis as dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    plt.xticks(rotation=45)

    # Add grid
    ax.grid(True, linestyle="--", alpha=0.7)

    # Title
    plt.title("Capsule Chain Timeline")
    plt.tight_layout()

    # Display the figure
    st.pyplot(fig)


def render_timeline_plotly(
    capsules: List[Capsule],
    highlighted_capsule_id: Optional[str] = None,
    max_capsules_per_page: int = 50,
):
    """Render an interactive capsule timeline visualization using Plotly.

    Args:
        capsules: List of capsules to include in the timeline
        highlighted_capsule_id: Optional ID of capsule to highlight
    """
    if not capsules:
        st.warning("No capsules available to visualize timeline")
        return

    # Extract timeline data
    df = extract_timeline_data(capsules)

    if df.empty:
        st.warning("No valid capsules found with proper timestamps")
        return

    relationships = extract_capsule_relationships(capsules)

    # Pagination controls if needed
    total_capsules = len(df)
    total_pages = (total_capsules + max_capsules_per_page - 1) // max_capsules_per_page

    # Only show pagination if we have more than max_capsules_per_page capsules
    current_page = 0
    if total_pages > 1:
        st.write(f"Showing {total_capsules} capsules across {total_pages} pages")

        # Create pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            page_options = [f"Page {i+1} of {total_pages}" for i in range(total_pages)]
            page_selector = st.selectbox(
                "Select page", page_options, key="timeline_page"
            )
            current_page = (
                int(page_selector.split()[1]) - 1
            )  # Convert from 1-indexed to 0-indexed

        # Calculate slice indices for current page
        start_idx = current_page * max_capsules_per_page
        end_idx = min(start_idx + max_capsules_per_page, total_capsules)

        # Slice the dataframe for current page
        df_page = df.iloc[start_idx:end_idx]

        # Display page info
        st.caption(
            f"Displaying capsules {start_idx+1} to {end_idx} (Page {current_page+1} of {total_pages})"
        )
    else:
        # If no pagination needed, use all data
        df_page = df

    # Create a figure
    fig = go.Figure()

    # Get unique capsule types and assign positions
    capsule_types = df["capsule_type"].unique()
    type_positions = {ctype: i for i, ctype in enumerate(sorted(capsule_types))}

    # Add previous_capsule connections (parent-child relationships) for the current page only
    for idx, row in df_page.iterrows():
        if pd.notna(row["previous_capsule_id"]):
            # Find the parent capsule
            parent_rows = df[
                df["capsule_id"] == row["previous_capsule_id"]
            ]  # Search in full df
            if not parent_rows.empty:
                parent_row = parent_rows.iloc[0]
                # Draw a line from parent to child
                fig.add_trace(
                    go.Scatter(
                        x=[parent_row["timestamp"], row["timestamp"]],
                        y=[
                            type_positions[parent_row["capsule_type"]],
                            type_positions[row["capsule_type"]],
                        ],
                        mode="lines",
                        line=dict(color="rgba(0,0,0,0.3)", width=1),
                        hoverinfo="none",
                        showlegend=False,
                    )
                )

    # Add other relationship lines for the current page only
    for rel_type, edges in relationships.items():
        # Get style for this relationship type
        style = RELATIONSHIP_STYLES.get(rel_type, {"color": "gray", "style": "-"})
        color = style["color"]
        dash = "solid"
        if style["style"] == "--":
            dash = "dash"
        elif style["style"] == ":":
            dash = "dot"
        elif style["style"] == "-.":
            dash = "dashdot"

        for source_id, target_id in edges:
            # Only include if either source or target is on the current page
            source_in_page = source_id in df_page["capsule_id"].values
            target_in_page = target_id in df_page["capsule_id"].values

            if source_in_page or target_in_page:
                # Find source and target in full dataframe
                source_rows = df[df["capsule_id"] == source_id]
                target_rows = df[df["capsule_id"] == target_id]

                if not source_rows.empty and not target_rows.empty:
                    source_row = source_rows.iloc[0]
                    target_row = target_rows.iloc[0]

                    # Draw a line for the relationship
                    fig.add_trace(
                        go.Scatter(
                            x=[source_row["timestamp"], target_row["timestamp"]],
                            y=[
                                type_positions[source_row["capsule_type"]],
                                type_positions[target_row["capsule_type"]],
                            ],
                            mode="lines",
                            line=dict(color=color, width=1, dash=dash),
                            name=rel_type,
                            hoverinfo="text",
                            text=rel_type,
                            showlegend=False,
                        )
                    )

    # Create hover text for each capsule
    df_page["hover_text"] = df_page.apply(
        lambda row: f"ID: {row['capsule_id']}<br>Type: {row['capsule_type']}<br>"
        + f"Time: {row['timestamp'].strftime('%Y-%m-%d %H:%M')}<br>"
        + f"Agent: {row['agent_id']}<br>"
        + f"Confidence: {row['confidence']}",
        axis=1,
    )

    # Set marker sizes based on confidence
    marker_size = 12
    if "confidence" in df_page.columns:
        # Scale marker size between 8 and 20 based on confidence
        df_page["marker_size"] = df_page["confidence"] * 12 + 8
        marker_size = df_page["marker_size"].tolist()

    # Create highlight indices
    highlight_indices = []
    if highlighted_capsule_id:
        highlight_indices = df_page.index[
            df_page["capsule_id"] == highlighted_capsule_id
        ].tolist()

    # Add traces for each capsule type
    for capsule_type in sorted(type_positions.keys()):
        # Filter data for this type on the current page
        subset = df_page[df_page["capsule_type"] == capsule_type]

        if len(subset) > 0:  # Only add traces for types that exist on this page
            # Create marker line settings
            marker_line = dict(width=1, color="rgba(0,0,0,0.5)")
            if highlight_indices and len(subset) > 0:
                marker_line = [
                    dict(width=2, color="white")
                    if i in highlight_indices
                    else dict(width=1, color="rgba(0,0,0,0.5)")
                    for i in range(len(subset))
                ]

            # Add the trace
            fig.add_trace(
                go.Scatter(
                    x=subset["timestamp"],
                    y=[type_positions[capsule_type]] * len(subset),
                    mode="markers",
                    marker=dict(
                        size=marker_size,
                        color=subset["color"],
                        line=marker_line,
                        opacity=0.8,
                    ),
                    name=capsule_type,
                    text=subset["hover_text"],
                    hoverinfo="text",
                    showlegend=True,
                )
            )

    # Configure layout
    page_title = "UATP 7.0 Capsule Timeline"
    if total_pages > 1:
        page_title += f" (Page {current_page+1} of {total_pages})"

    fig.update_layout(
        title=page_title,
        xaxis=dict(title="Timestamp", type="date"),
        yaxis=dict(
            title="Capsule Type",
            tickmode="array",
            tickvals=list(type_positions.values()),
            ticktext=list(type_positions.keys()),
        ),
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=600,
        margin=dict(l=50, r=50, t=80, b=50),
    )

    # Add gridlines
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)")

    # Display the figure
    st.plotly_chart(fig, use_container_width=True)


def render_capsule_timeline(
    capsules: List[Capsule],
    interactive: bool = True,
    highlighted_capsule_id: Optional[str] = None,
):
    """Render a capsule timeline visualization.

    Args:
        capsules: List of capsules to include in the timeline
        interactive: Whether to use interactive Plotly (True) or static Matplotlib (False)
        highlighted_capsule_id: Optional ID of capsule to highlight
    """
    st.subheader("Capsule Timeline")
    st.caption("Visualizing capsule creation over time and their relationships")

    # Import the legends module
    from visualizer.components.visualization_legends import render_visualization_legends

    # Add the legends in an expander
    render_visualization_legends()

    # Advanced options in an expander
    with st.expander("Timeline Visualization Options", expanded=False):
        # Performance options
        st.markdown("### Performance Options")

        # Pagination settings for large timelines
        capsules_per_page = st.slider(
            "Capsules per page",
            min_value=10,
            max_value=100,
            value=50,
            step=10,
            help="Number of capsules to show per page in the timeline view",
        )

        # Node limit warning
        if len(capsules) > 50:
            st.warning(
                f"⚠️ Large capsule chain detected ({len(capsules)} capsules). Pagination is enabled for better performance."
            )
        if min_date != max_date:
            st.markdown("### Filter by Date Range")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", min_date)
            with col2:
                end_date = st.date_input("End Date", max_date)

            # Filter capsules by date range
            filtered_capsules = []
            for capsule in capsules:
                if not hasattr(capsule, "timestamp"):
                    continue

                timestamp = parse_capsule_datetime(capsule.timestamp)
                capsule_date = timestamp.date()

                if start_date <= capsule_date <= end_date:
                    filtered_capsules.append(capsule)

            # Update capsules list
            capsules = filtered_capsules

    # Render appropriate visualization
    try:
        if interactive:
            render_timeline_plotly(
                capsules,
                highlighted_capsule_id,
                max_capsules_per_page=capsules_per_page,
            )
        else:
            render_timeline_matplotlib(capsules, highlighted_capsule_id)
    except Exception as e:
        st.error(f"Error rendering timeline visualization: {str(e)}")
