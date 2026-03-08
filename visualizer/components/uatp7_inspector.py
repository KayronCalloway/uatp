"""Enhanced inspector component for displaying detailed information about UATP 7.0 capsule types."""

import json
from datetime import datetime

import iso8601
import matplotlib.pyplot as plt
import streamlit as st

# Import specialized UATP 7.0 capsule types
from capsules.specialized_capsules import (
    CapsuleExpirationCapsule,
    ConsentCapsule,
    EconomicCapsule,
    GovernanceCapsule,
    ImplicitConsentCapsule,
    RemixCapsule,
    SelfHallucinationCapsule,
    SimulatedMaliceCapsule,
    TemporalSignatureCapsule,
    TrustRenewalCapsule,
    ValueInceptionCapsule,
)

# Import base capsule types
from dateutil.parser import parse as parse_datetime

# Import visualization utilities

# Create color mapping for UATP 7.0 capsule types
UATP7_CAPSULE_TYPE_COLORS = {
    "Remix": "#8a2be2",  # Purple
    "TemporalSignature": "#4169e1",  # Royal Blue
    "ValueInception": "#2e8b57",  # Sea Green
    "SimulatedMalice": "#b22222",  # Fire Brick
    "ImplicitConsent": "#ff8c00",  # Dark Orange
    "SelfHallucination": "#9932cc",  # Dark Orchid
    "Consent": "#228b22",  # Forest Green
    "TrustRenewal": "#4682b4",  # Steel Blue
    "CapsuleExpiration": "#a0522d",  # Sienna
    "Governance": "#800000",  # Maroon
    "Economic": "#daa520",  # Goldenrod
}

# Register colors in the main color map
from visualizer.utils.colors import CAPSULE_TYPE_COLORS

for capsule_type, color in UATP7_CAPSULE_TYPE_COLORS.items():
    CAPSULE_TYPE_COLORS[capsule_type] = color


# Visualization utility functions
def safe_parse_datetime(date_string):
    """Safely parse a date string and return a datetime object.

    Args:
        date_string: String to parse as datetime

    Returns:
        Datetime object if successful, None otherwise
    """
    if not date_string:
        return None

    try:
        # Try iso8601 parser first for ISO format
        return iso8601.parse_date(date_string)
    except (ValueError, iso8601.ParseError):
        try:
            # Fall back to dateutil parser for more flexible parsing
            return parse_datetime(date_string)
        except Exception:
            return None


def render_json_data(data, title="Data", expanded=False):
    """Render JSON data in an expander with consistent formatting.

    Args:
        data: Dictionary or list to render as JSON
        title: Title for the expander
        expanded: Whether the expander is expanded by default
    """
    with st.expander(title, expanded=expanded):
        if data:
            st.json(data)
        else:
            st.info("No data available")


def create_bar_chart(data, x_label="Category", y_label="Value", title=""):
    """Create a standardized bar chart using Matplotlib.

    Args:
        data: Dictionary mapping categories to values
        x_label: Label for x-axis
        y_label: Label for y-axis
        title: Chart title

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    categories = list(data.keys())
    values = list(data.values())

    bars = ax.bar(
        categories,
        values,
        color=UATP7_CAPSULE_TYPE_COLORS.get("ValueInception", "#2e8b57"),
    )

    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.01,
            f"{height:.2f}",
            ha="center",
            va="bottom",
        )

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    return fig


def create_pie_chart(data, title=""):
    """Create a standardized pie chart using Matplotlib.

    Args:
        data: Dictionary mapping categories to values
        title: Chart title

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    labels = list(data.keys())
    values = list(data.values())

    # Use consistent colors from the UATP7 color map where possible
    ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        shadow=False,
        explode=[0.05] * len(labels),
    )
    ax.axis("equal")  # Equal aspect ratio ensures a circular pie
    ax.set_title(title)

    return fig


def display_datetime_info(date_string, label="Date"):
    """Display a datetime with consistent formatting.

    Args:
        date_string: String to parse as datetime
        label: Label to display
    """
    if not date_string:
        return

    st.markdown(f"**{label}:** {date_string}")

    # Try to parse and display in a standardized format
    dt = safe_parse_datetime(date_string)
    if dt:
        st.caption(
            f"Parsed: {dt.strftime('%Y-%m-%d %H:%M:%S')} UTC"
            if dt.tzinfo
            else f"Parsed: {dt.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        st.caption("Could not parse date format")


def render_remix_content(capsule: RemixCapsule):
    """Render specialized content for Remix capsules with enhanced visualizations."""
    with st.expander("Remix Details", expanded=True):
        # Add a colorful header with capsule type badge
        st.markdown(
            f"""
        <div style="display:flex;align-items:center;margin-bottom:1rem;">
            <div style="background-color:{UATP7_CAPSULE_TYPE_COLORS.get('Remix', '#8a2be2')};color:white;
                 padding:3px 8px;border-radius:10px;margin-right:10px;font-size:0.8em;">
                REMIX
            </div>
            <div style="font-size:1.2em;font-weight:bold;">Content Remix & Attribution</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Show summary metrics at the top
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

        source_count = (
            len(capsule.source_capsule_ids)
            if hasattr(capsule, "source_capsule_ids") and capsule.source_capsule_ids
            else 0
        )
        metrics_col1.metric("Source Capsules", source_count)

        if hasattr(capsule, "attribution_weights") and capsule.attribution_weights:
            total_attribution = sum(capsule.attribution_weights.values())
            max_attribution = (
                max(capsule.attribution_weights.values())
                if capsule.attribution_weights
                else 0
            )
            metrics_col2.metric("Total Attribution", f"{total_attribution:.2f}")
            metrics_col3.metric("Max Source Weight", f"{max_attribution:.2f}")

        # Source capsules section
        if hasattr(capsule, "source_capsule_ids") and capsule.source_capsule_ids:
            st.subheader("Source Capsules")

            # Display source capsules as clickable elements
            for i, source_id in enumerate(capsule.source_capsule_ids):
                # Create a bordered box for each source
                st.markdown(
                    f"""
                <div style="padding:8px;margin:5px 0;border:1px solid #ddd;border-radius:5px;">
                    <div style="font-size:0.85em;color:#666;">Source {i+1}:</div>
                    <div style="font-family:monospace;word-break:break-all;padding:5px 0;">{source_id}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Add view source button (this would need to be connected to actual functionality)
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button(f"View Source #{i+1}", key=f"view_source_{i}"):
                        st.session_state["selected_capsule_id"] = source_id
                        st.info(f"Selected capsule {source_id} for viewing")

        # Attribution weights visualization
        if hasattr(capsule, "attribution_weights") and capsule.attribution_weights:
            st.subheader("Attribution Analysis")

            # Create data for visualization
            labels = []
            values = []
            colors = []

            # Generate colors based on weight values
            for source, weight in capsule.attribution_weights.items():
                labels.append(
                    source[:8] + "..." if len(source) > 10 else source
                )  # Truncate long IDs
                values.append(weight)
                # Color intensity based on weight
                intensity = min(
                    0.3 + weight * 0.7, 1.0
                )  # Scale between 30% and 100% intensity
                colors.append(f"rgba(138, 43, 226, {intensity})")

            # Use columns for different visualization options
            viz_tab1, viz_tab2 = st.tabs(["Pie Chart", "Bar Chart"])

            with viz_tab1:
                # Create a pie chart using Plotly for better interactivity
                import plotly.express as px

                fig = px.pie(
                    values=values,
                    names=labels,
                    title="Attribution Distribution",
                    color_discrete_sequence=px.colors.sequential.Purples,
                    hover_data=["Weight"],
                )
                fig.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig, use_container_width=True)

            with viz_tab2:
                # Create an enhanced bar chart with colors
                fig = px.bar(
                    x=values,
                    y=labels,
                    orientation="h",
                    title="Attribution Weights by Source",
                    labels={"x": "Attribution Weight", "y": "Source"},
                    color=values,
                    color_continuous_scale=px.colors.sequential.Purples,
                )
                st.plotly_chart(fig, use_container_width=True)

            # Show detailed table with attribution data
            with st.expander("View Attribution Details"):
                attribution_data = {
                    "Source ID": list(capsule.attribution_weights.keys()),
                    "Weight": list(capsule.attribution_weights.values()),
                }
                st.dataframe(attribution_data, use_container_width=True)

        # Display remix metadata
        st.subheader("Remix Metadata")
        col1, col2 = st.columns(2)

        with col1:
            if hasattr(capsule, "remix_type") and capsule.remix_type:
                st.markdown("**Remix Type:**")
                # Format the remix type with an appropriate badge
                remix_type = capsule.remix_type
                badge_color = {
                    "creative": "#4CAF50",  # Green
                    "analytical": "#2196F3",  # Blue
                    "summary": "#FF9800",  # Orange
                    "extension": "#9C27B0",  # Purple
                }.get(remix_type.lower(), "#607D8B")  # Default gray

                st.markdown(
                    f"""
                <div style="display:inline-block;background-color:{badge_color};color:white;
                     padding:3px 10px;border-radius:15px;font-size:0.9em;">
                    {remix_type.upper()}
                </div>
                """,
                    unsafe_allow_html=True,
                )

        with col2:
            # Add transformation confidence if available
            if (
                hasattr(capsule, "transformation_confidence")
                and capsule.transformation_confidence is not None
            ):
                confidence = float(capsule.transformation_confidence)
                st.markdown("**Transformation Confidence:**")
                st.progress(confidence)
                st.text(f"{confidence:.2%}")

        # Display transformation description with better formatting
        if (
            hasattr(capsule, "transformation_description")
            and capsule.transformation_description
        ):
            st.subheader("Transformation Description")
            # Add a nice quote block for the description
            st.markdown(
                f"""
            <div style="background-color:rgba(138,43,226,0.1);padding:15px;border-left:5px solid {UATP7_CAPSULE_TYPE_COLORS.get('Remix', '#8a2be2')};border-radius:3px;">
                {capsule.transformation_description}
            </div>
            """,
                unsafe_allow_html=True,
            )

        # If available, add metrics for quality assessment
        if hasattr(capsule, "quality_metrics") and capsule.quality_metrics:
            st.subheader("Quality Assessment")
            metrics = capsule.quality_metrics

            quality_cols = st.columns(len(metrics))
            for i, (metric, value) in enumerate(metrics.items()):
                with quality_cols[i % len(quality_cols)]:
                    st.metric(metric.replace("_", " ").title(), f"{value:.2f}")
                    st.progress(value)

        # Display all timestamps with consistent formatting
        if hasattr(capsule, "knowledge_cutoff") and capsule.knowledge_cutoff:
            display_datetime_info(capsule.knowledge_cutoff, "Knowledge Cutoff")

        if hasattr(capsule, "runtime_timestamp") and capsule.runtime_timestamp:
            display_datetime_info(capsule.runtime_timestamp, "Runtime Timestamp")

        if hasattr(capsule, "request_timestamp") and capsule.request_timestamp:
            display_datetime_info(capsule.request_timestamp, "Request Timestamp")

        # Calculate and display timing information if all required timestamps are available
        if (
            hasattr(capsule, "request_timestamp")
            and capsule.request_timestamp
            and hasattr(capsule, "runtime_timestamp")
            and capsule.runtime_timestamp
        ):
            request_date = safe_parse_datetime(capsule.request_timestamp)
            runtime_date = safe_parse_datetime(capsule.runtime_timestamp)

            if request_date and runtime_date:
                try:
                    response_time = runtime_date - request_date
                    st.markdown(
                        f"**Response Time:** {response_time.total_seconds():.2f} seconds"
                    )

                    # Display visual representation of response time
                    max_expected_time = 10.0  # Scale to max of 10 seconds
                    progress_value = min(
                        1.0, response_time.total_seconds() / max_expected_time
                    )
                    st.progress(progress_value)

                    # Add explanation for the progress bar
                    if progress_value >= 1.0:
                        st.caption(f"Response time exceeds {max_expected_time} seconds")
                except Exception as e:
                    st.error(f"Error calculating response time: {str(e)}")
            else:
                st.warning(
                    "Could not calculate response time due to invalid timestamp formats"
                )

        # Display additional temporal information if available
        if hasattr(capsule, "temporal_context") and capsule.temporal_context:
            st.subheader("Temporal Context")
            st.markdown(capsule.temporal_context)

        # Show any other temporal metadata
        if hasattr(capsule, "metadata") and capsule.metadata:
            temporal_metadata = {}
            for key, value in capsule.metadata.items():
                if any(
                    term in key.lower()
                    for term in ["time", "date", "temporal", "timestamp"]
                ):
                    temporal_metadata[key] = value

            if temporal_metadata:
                render_json_data(temporal_metadata, "Additional Temporal Metadata")


def render_temporal_signature_content(capsule: TemporalSignatureCapsule):
    """Render specialized content for Temporal Signature capsules with enhanced visualizations."""
    with st.expander("Temporal Signature Details", expanded=True):
        # Add a colorful header with capsule type badge
        st.markdown(
            f"""
        <div style="display:flex;align-items:center;margin-bottom:1rem;">
            <div style="background-color:{UATP7_CAPSULE_TYPE_COLORS.get('TemporalSignature', '#4169e1')};color:white;
                 padding:3px 8px;border-radius:10px;margin-right:10px;font-size:0.8em;">
                TEMPORAL SIGNATURE
            </div>
            <div style="font-size:1.2em;font-weight:bold;">Time-Bound Trust Verification</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Extract validity period information
        if hasattr(capsule, "validity_period"):
            # Parse times
            start_time = None
            end_time = None
            duration = None

            if (
                hasattr(capsule.validity_period, "start_time")
                and capsule.validity_period.start_time
            ):
                start_time = safe_parse_datetime(capsule.validity_period.start_time)

            if (
                hasattr(capsule.validity_period, "end_time")
                and capsule.validity_period.end_time
            ):
                end_time = safe_parse_datetime(capsule.validity_period.end_time)

            # Calculate duration if both times are available
            if start_time and end_time:
                duration = end_time - start_time

            # Current time for reference
            now = datetime.now()
            if start_time and not start_time.tzinfo:
                now = now.replace(
                    tzinfo=None
                )  # Make timezone-naive if start_time is naive

            # Determine validity status
            is_valid = True
            if start_time and now < start_time:
                is_valid = False
                status_message = "Not yet valid (future start time)"
                status_color = "#FF9800"  # Orange
                time_to_valid = start_time - now
                time_message = f"Valid in {time_to_valid.days} days, {time_to_valid.seconds//3600} hours"
            elif end_time and now > end_time:
                is_valid = False
                status_message = "Expired (past end time)"
                status_color = "#F44336"  # Red
                time_since_expired = now - end_time
                time_message = f"Expired {time_since_expired.days} days, {time_since_expired.seconds//3600} hours ago"
            else:
                status_message = "Currently valid"
                status_color = "#4CAF50"  # Green
                if end_time:
                    time_until_expiry = end_time - now
                    time_message = f"Expires in {time_until_expiry.days} days, {time_until_expiry.seconds//3600} hours"
                else:
                    time_message = "No expiration date set"

            # Create a visual timeline
            st.subheader("Validity Timeline")

            # Display current status with a prominent badge
            st.markdown(
                f"""
            <div style="display:inline-block;background-color:{status_color};color:white;
                 padding:5px 15px;border-radius:15px;font-weight:bold;margin-bottom:10px;">
                {status_message}
            </div>
            <div style="color:#666;margin-bottom:15px;">{time_message}</div>
            """,
                unsafe_allow_html=True,
            )

            # Display timeline visualization
            if start_time or end_time:
                # Create interactive timeline visualization with Plotly
                from datetime import timedelta

                import plotly.graph_objects as go

                # Set up timeline boundaries
                if start_time and end_time:
                    timeline_start = start_time - timedelta(
                        days=max(1, duration.days // 10)
                    )
                    timeline_end = end_time + timedelta(
                        days=max(1, duration.days // 10)
                    )
                elif start_time:
                    timeline_start = start_time - timedelta(days=5)
                    timeline_end = start_time + timedelta(days=30)
                elif end_time:
                    timeline_start = end_time - timedelta(days=30)
                    timeline_end = end_time + timedelta(days=5)
                else:
                    timeline_start = now - timedelta(days=15)
                    timeline_end = now + timedelta(days=15)

                # Create figure with timeline
                fig = go.Figure()

                # Add validity period as a rectangle
                if start_time and end_time:
                    fig.add_trace(
                        go.Scatter(
                            x=[start_time, end_time, end_time, start_time, start_time],
                            y=[0, 0, 1, 1, 0],
                            fill="toself",
                            fillcolor=f"rgba{tuple(int(status_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.3,)}",
                            line=dict(color=status_color),
                            name="Validity Period",
                        )
                    )

                # Add start time marker
                if start_time:
                    fig.add_trace(
                        go.Scatter(
                            x=[start_time],
                            y=[0.5],
                            mode="markers+text",
                            marker=dict(size=12, color="#4169E1", symbol="triangle-up"),
                            text=["Start"],
                            textposition="top center",
                            name="Start Time",
                        )
                    )

                # Add end time marker
                if end_time:
                    fig.add_trace(
                        go.Scatter(
                            x=[end_time],
                            y=[0.5],
                            mode="markers+text",
                            marker=dict(
                                size=12, color="#FF5252", symbol="triangle-down"
                            ),
                            text=["End"],
                            textposition="bottom center",
                            name="End Time",
                        )
                    )

                # Add current time marker
                fig.add_trace(
                    go.Scatter(
                        x=[now],
                        y=[0.5],
                        mode="markers+text",
                        marker=dict(size=15, color="#FFC107", symbol="star"),
                        text=["Now"],
                        textposition="top center",
                        name="Current Time",
                    )
                )

                # Configure the layout
                fig.update_layout(
                    title="Temporal Validity Timeline",
                    xaxis_title="Time",
                    yaxis=dict(visible=False),
                    height=200,
                    margin=dict(l=20, r=20, t=40, b=20),
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                    ),
                    hovermode="closest",
                )

                # Set x-axis range
                fig.update_xaxes(range=[timeline_start, timeline_end])

                # Display the figure
                st.plotly_chart(fig, use_container_width=True)

            # Show detailed information
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Start Time")
                if start_time:
                    st.markdown(f"**Date:** {start_time.strftime('%Y-%m-%d')}")
                    st.markdown(f"**Time:** {start_time.strftime('%H:%M:%S')}")
                    if now < start_time:
                        st.markdown(f"**Starts in:** {(start_time - now).days} days")
                else:
                    st.info("No start time specified")

            with col2:
                st.markdown("### End Time")
                if end_time:
                    st.markdown(f"**Date:** {end_time.strftime('%Y-%m-%d')}")
                    st.markdown(f"**Time:** {end_time.strftime('%H:%M:%S')}")
                    if now < end_time:
                        st.markdown(f"**Expires in:** {(end_time - now).days} days")
                    else:
                        st.markdown(f"**Expired:** {(now - end_time).days} days ago")
                else:
                    st.info("No end time specified (permanent)")

            # Duration information
            if duration:
                st.markdown("### Validity Duration")

                # Format duration in a readable way
                if duration.days > 0:
                    days = duration.days
                    hours = duration.seconds // 3600
                    minutes = (duration.seconds % 3600) // 60

                    duration_parts = []
                    if days == 1:
                        duration_parts.append("1 day")
                    elif days > 1:
                        duration_parts.append(f"{days} days")

                    if hours == 1:
                        duration_parts.append("1 hour")
                    elif hours > 1:
                        duration_parts.append(f"{hours} hours")

                    if minutes == 1:
                        duration_parts.append("1 minute")
                    elif minutes > 1:
                        duration_parts.append(f"{minutes} minutes")

                    duration_text = ", ".join(duration_parts)

                    # Display duration visualization
                    total_seconds = duration.total_seconds()
                    if total_seconds > 0:
                        # Create a progress-like bar showing the position in the validity period
                        if start_time and now >= start_time and now <= end_time:
                            elapsed = (now - start_time).total_seconds()
                            progress_pct = min(
                                100, max(0, (elapsed / total_seconds) * 100)
                            )

                            st.markdown(
                                f"""
                            <div style="margin:10px 0;">
                                <div style="font-size:0.9em;margin-bottom:5px;">Progress: {progress_pct:.1f}% complete</div>
                                <div style="background:#e0e0e0;height:10px;border-radius:5px;">
                                    <div style="background:{status_color};width:{progress_pct}%;height:10px;border-radius:5px;"></div>
                                </div>
                                <div style="display:flex;justify-content:space-between;font-size:0.8em;margin-top:2px;">
                                    <div>Start</div>
                                    <div>End</div>
                                </div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                    st.markdown(f"**Total Duration:** {duration_text}")

        # Temporal constraints section with enhanced visualization
        if hasattr(capsule, "temporal_constraints") and capsule.temporal_constraints:
            st.subheader("Temporal Constraints")

            # Try to visualize constraints in a more user-friendly way
            try:
                constraints = capsule.temporal_constraints
                if isinstance(constraints, dict):
                    # Create tabs for different views
                    constraint_tabs = st.tabs(["Visual", "Details"])

                    with constraint_tabs[0]:
                        # Create a visual representation of constraints
                        constraint_types = list(constraints.keys())

                        for constraint_type in constraint_types:
                            st.markdown(
                                f"#### {constraint_type.replace('_', ' ').title()}"
                            )

                            # Different visualizations based on constraint type
                            constraint_value = constraints[constraint_type]

                            if constraint_type in ["max_age", "min_age"]:
                                # For age constraints, show as a slider
                                if isinstance(constraint_value, (int, float)):
                                    max_val = (
                                        constraint_value * 2
                                        if constraint_type == "max_age"
                                        else 100
                                    )
                                    st.slider(
                                        "Age Constraint (days)",
                                        0,
                                        max_val,
                                        constraint_value,
                                        disabled=True,
                                    )

                            elif constraint_type in ["valid_days", "valid_times"]:
                                # For day/time constraints, show as checkboxes
                                if isinstance(constraint_value, list):
                                    for item in constraint_value:
                                        st.checkbox(
                                            str(item), value=True, disabled=True
                                        )

                            elif constraint_type == "sequence_position":
                                # For sequence position, show as a progress bar
                                if (
                                    isinstance(constraint_value, dict)
                                    and "position" in constraint_value
                                    and "total" in constraint_value
                                ):
                                    position = constraint_value["position"]
                                    total = constraint_value["total"]
                                    st.markdown(f"Position {position} of {total}")
                                    st.progress(position / total)

                            elif constraint_type in ["before_event", "after_event"]:
                                # For event-based constraints, show as text
                                st.info(
                                    f"Must occur {constraint_type.replace('_', ' ')} '{constraint_value}'"
                                )

                            else:
                                # Show raw value
                                st.write(constraint_value)

                    with constraint_tabs[1]:
                        # Show raw constraint data
                        st.json(constraints)
                else:
                    st.json(constraints)
            except Exception as e:
                st.error(f"Error visualizing constraints: {str(e)}")
                st.json(capsule.temporal_constraints)

        # Chain position requirements with visual indicator
        if hasattr(capsule, "chain_position") and capsule.chain_position:
            st.subheader("Chain Position Requirements")

            position = capsule.chain_position
            if isinstance(position, str):
                # Convert string positions to a visual indicator
                position_map = {
                    "first": 0,
                    "early": 0.25,
                    "middle": 0.5,
                    "late": 0.75,
                    "last": 1.0,
                }

                if position.lower() in position_map:
                    pos_value = position_map[position.lower()]

                    # Create a visual indicator of position in chain
                    st.markdown(f"**Required Position:** {position.title()}")

                    # Create a custom chain position visualization
                    st.markdown(
                        f"""
                    <div style="margin:15px 0;">
                        <div style="background:#e0e0e0;height:10px;border-radius:5px;position:relative;">
                            <div style="position:absolute;background:{UATP7_CAPSULE_TYPE_COLORS.get('TemporalSignature', '#4169e1')};width:10px;height:20px;border-radius:50%;top:-5px;left:calc({pos_value*100}% - 5px);"></div>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:0.8em;margin-top:10px;">
                            <div>First</div>
                            <div>Middle</div>
                            <div>Last</div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(f"**Required Position:** {position}")
            else:
                st.markdown(f"**Position:** {position}")

        # Time-bound policies with better formatting
        if hasattr(capsule, "time_bound_policies") and capsule.time_bound_policies:
            st.subheader("Time-Bound Policies")

            # Try to display policies in a more readable format
            try:
                policies = capsule.time_bound_policies
                if isinstance(policies, list):
                    for i, policy in enumerate(policies):
                        with st.expander(f"Policy {i+1}", expanded=i == 0):
                            if isinstance(policy, dict):
                                for key, value in policy.items():
                                    if key.lower() in ["id", "name", "title"]:
                                        st.markdown(f"**{key.title()}:** {value}")
                                    elif key.lower() in ["description", "details"]:
                                        st.markdown(f"**{key.title()}:**")
                                        st.markdown(f"> {value}")
                                    elif key.lower() in [
                                        "valid_from",
                                        "valid_until",
                                        "start_time",
                                        "end_time",
                                    ]:
                                        display_datetime_info(
                                            value, key.replace("_", " ").title()
                                        )
                                    else:
                                        st.markdown(
                                            f"**{key.replace('_', ' ').title()}:**"
                                        )
                                        st.write(value)
                            else:
                                st.write(policy)
                else:
                    st.json(policies)
            except Exception as e:
                st.error(f"Error formatting policies: {str(e)}")
                st.json(capsule.time_bound_policies)

        # Display all timestamps with consistent formatting
        if hasattr(capsule, "knowledge_cutoff") and capsule.knowledge_cutoff:
            display_datetime_info(capsule.knowledge_cutoff, "Knowledge Cutoff")

        if hasattr(capsule, "runtime_timestamp") and capsule.runtime_timestamp:
            display_datetime_info(capsule.runtime_timestamp, "Runtime Timestamp")

        if hasattr(capsule, "request_timestamp") and capsule.request_timestamp:
            display_datetime_info(capsule.request_timestamp, "Request Timestamp")

        # Calculate and display timing information if all required timestamps are available
        if (
            hasattr(capsule, "request_timestamp")
            and capsule.request_timestamp
            and hasattr(capsule, "runtime_timestamp")
            and capsule.runtime_timestamp
        ):
            request_date = safe_parse_datetime(capsule.request_timestamp)
            runtime_date = safe_parse_datetime(capsule.runtime_timestamp)

            if request_date and runtime_date:
                try:
                    response_time = runtime_date - request_date
                    st.markdown(
                        f"**Response Time:** {response_time.total_seconds():.2f} seconds"
                    )

                    # Display visual representation of response time
                    max_expected_time = 10.0  # Scale to max of 10 seconds
                    progress_value = min(
                        1.0, response_time.total_seconds() / max_expected_time
                    )
                    st.progress(progress_value)

                    # Add explanation for the progress bar
                    if progress_value >= 1.0:
                        st.caption(f"Response time exceeds {max_expected_time} seconds")
                except Exception as e:
                    st.error(f"Error calculating response time: {str(e)}")
            else:
                st.warning(
                    "Could not calculate response time due to invalid timestamp formats"
                )

        # Display additional temporal information if available
        if hasattr(capsule, "temporal_context") and capsule.temporal_context:
            st.subheader("Temporal Context")
            st.markdown(capsule.temporal_context)

        # Show any other temporal metadata
        if hasattr(capsule, "metadata") and capsule.metadata:
            temporal_metadata = {}
            for key, value in capsule.metadata.items():
                if any(
                    term in key.lower()
                    for term in ["time", "date", "temporal", "timestamp"]
                ):
                    temporal_metadata[key] = value

            if temporal_metadata:
                render_json_data(temporal_metadata, "Additional Temporal Metadata")


def render_value_inception_content(capsule: ValueInceptionCapsule):
    """Render specialized content for Value Inception capsules with enhanced visualizations."""
    with st.expander("Value Inception Details", expanded=True):
        # Add a colorful header with capsule type badge
        st.markdown(
            f"""
        <div style="display:flex;align-items:center;margin-bottom:1rem;">
            <div style="background-color:{UATP7_CAPSULE_TYPE_COLORS.get('ValueInception', '#2e8b57')};color:white;
                 padding:3px 8px;border-radius:10px;margin-right:10px;font-size:0.8em;">
                VALUE INCEPTION
            </div>
            <div style="font-size:1.2em;font-weight:bold;">Value Framework & Ethical Analysis</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Summary metrics at the top
        if hasattr(capsule, "value_hierarchy"):
            # Try to extract some summary metrics from the value hierarchy
            value_count = 0
            hierarchy_depth = 0
            priority_values = []

            def count_values_and_depth(node, current_depth=1, priority=True):
                nonlocal value_count, hierarchy_depth, priority_values
                hierarchy_depth = max(hierarchy_depth, current_depth)

                if isinstance(node, dict):
                    for key, value in node.items():
                        value_count += 1
                        if priority and len(priority_values) < 3:
                            priority_values.append(key)
                        count_values_and_depth(value, current_depth + 1, False)
                elif isinstance(node, list):
                    for item in node:
                        if isinstance(item, (str, int, float)):
                            value_count += 1
                        else:
                            count_values_and_depth(item, current_depth, False)

            if capsule.value_hierarchy:
                count_values_and_depth(capsule.value_hierarchy)

                # Display summary metrics in columns
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Values", value_count)
                col2.metric("Hierarchy Depth", hierarchy_depth)
                col3.metric(
                    "Tradeoffs",
                    len(capsule.tradeoff_analysis)
                    if hasattr(capsule, "tradeoff_analysis")
                    and capsule.tradeoff_analysis
                    else 0,
                )

                # Show priority values in an info box
                if priority_values:
                    priority_str = ", ".join(f"**{v}**" for v in priority_values[:3])
                    st.markdown(f"**Priority Values:** {priority_str}")

        # Value hierarchy with improved visualization
        if hasattr(capsule, "value_hierarchy") and capsule.value_hierarchy:
            st.subheader("Value Hierarchy")

            # Create tabs for different hierarchy views
            hierarchy_tabs = st.tabs(["Interactive Tree", "Nested View", "Raw Data"])

            with hierarchy_tabs[0]:
                # Try to create a networkx graph visualization with Pyvis
                try:
                    import os
                    import tempfile

                    import networkx as nx
                    from pyvis.network import Network

                    # Create a directed graph
                    G = nx.DiGraph()

                    # Helper function to build the graph
                    def build_graph(node, parent=None, node_id=None):
                        if node_id is None:
                            node_id = "root"
                            G.add_node(
                                node_id,
                                label="Root",
                                title="Root",
                                color=UATP7_CAPSULE_TYPE_COLORS.get("ValueInception"),
                            )

                        if isinstance(node, dict):
                            for i, (key, value) in enumerate(node.items()):
                                child_id = f"{node_id}_{i}"
                                G.add_node(
                                    child_id, label=key, title=key, color="#4CAF50"
                                )
                                G.add_edge(node_id, child_id)
                                build_graph(value, key, child_id)
                        elif isinstance(node, list):
                            for i, item in enumerate(node):
                                if isinstance(item, (str, int, float)):
                                    child_id = f"{node_id}_item_{i}"
                                    G.add_node(
                                        child_id,
                                        label=str(item),
                                        title=str(item),
                                        color="#2196F3",
                                    )
                                    G.add_edge(node_id, child_id)
                                else:
                                    build_graph(item, None, f"{node_id}_complex_{i}")
                        elif node is not None:
                            child_id = f"{node_id}_value"
                            G.add_node(
                                child_id,
                                label=str(node),
                                title=str(node),
                                color="#9C27B0",
                            )
                            G.add_edge(node_id, child_id)

                    # Build the graph from the value hierarchy
                    build_graph(capsule.value_hierarchy)

                    # Create a Pyvis network
                    net = Network(height="500px", width="100%", directed=True)
                    net.from_nx(G)
                    net.toggle_physics(True)

                    # Set network options for better visualization
                    net.set_options(
                        """
                    {
                        "nodes": {
                            "shape": "box",
                            "font": {
                                "size": 14,
                                "face": "Arial"
                            },
                            "margin": 10
                        },
                        "edges": {
                            "arrows": {
                                "to": {
                                    "enabled": true,
                                    "scaleFactor": 0.5
                                }
                            },
                            "color": {
                                "inherit": false
                            },
                            "smooth": {
                                "type": "straightCross"
                            }
                        },
                        "layout": {
                            "hierarchical": {
                                "enabled": true,
                                "direction": "UD",
                                "sortMethod": "directed",
                                "levelSeparation": 150
                            }
                        },
                        "interaction": {
                            "dragNodes": true,
                            "navigationButtons": true,
                            "keyboard": true
                        },
                        "physics": {
                            "hierarchicalRepulsion": {
                                "centralGravity": 0.0,
                                "springLength": 150,
                                "springConstant": 0.01,
                                "nodeDistance": 200
                            }
                        }
                    }
                    """
                    )

                    # Save to a temporary HTML file
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".html"
                    ) as tmp_file:
                        net.save_graph(tmp_file.name)
                        # Display in an iframe
                        with open(tmp_file.name) as f:
                            html_content = f.read()
                            # Extract only the relevant part of the HTML
                            html_content = html_content.split("<body>")[1].split(
                                "</body>"
                            )[0]
                            # Display the graph in an iframe
                            st.components.v1.html(html_content, height=520)

                        # Clean up the temporary file
                        try:
                            os.unlink(tmp_file.name)
                        except:
                            pass

                except Exception as e:
                    st.error(f"Could not create interactive tree: {str(e)}")
                    st.info(
                        "Please install networkx and pyvis libraries for interactive visualization."
                    )

                    # Fallback to a simpler visualization
                    import plotly.graph_objects as go

                    fig = go.Figure()

                    # Simple tree representation
                    def add_nodes_to_plot(node, x=0, y=0, level=0, prefix=""):
                        if isinstance(node, dict):
                            for i, (key, value) in enumerate(node.items()):
                                node_y = y - i * 1.5
                                # Add a node
                                fig.add_trace(
                                    go.Scatter(
                                        x=[x],
                                        y=[node_y],
                                        mode="markers+text",
                                        marker=dict(
                                            size=15,
                                            color=UATP7_CAPSULE_TYPE_COLORS.get(
                                                "ValueInception"
                                            ),
                                        ),
                                        text=[key],
                                        textposition="middle right",
                                        name=key,
                                        hoverinfo="text",
                                        hovertext=f"Value: {key}",
                                    )
                                )
                                # Add a line to parent
                                if level > 0:
                                    fig.add_trace(
                                        go.Scatter(
                                            x=[x - 1, x],
                                            y=[y, node_y],
                                            mode="lines",
                                            line=dict(color="#888", width=1),
                                            hoverinfo="none",
                                        )
                                    )
                                # Process children
                                add_nodes_to_plot(
                                    value, x + 1, node_y, level + 1, prefix + "  "
                                )
                        elif isinstance(node, list):
                            for i, item in enumerate(node):
                                node_y = y - i * 1.0
                                if isinstance(item, (str, int, float)):
                                    fig.add_trace(
                                        go.Scatter(
                                            x=[x],
                                            y=[node_y],
                                            mode="markers+text",
                                            marker=dict(size=10, color="#2196F3"),
                                            text=[str(item)],
                                            textposition="middle right",
                                            hoverinfo="text",
                                            hovertext=f"Value: {item}",
                                        )
                                    )
                                    # Line to parent
                                    fig.add_trace(
                                        go.Scatter(
                                            x=[x - 1, x],
                                            y=[y, node_y],
                                            mode="lines",
                                            line=dict(color="#888", width=1),
                                            hoverinfo="none",
                                        )
                                    )
                                else:
                                    add_nodes_to_plot(item, x, node_y, level, prefix)
                        elif node is not None:
                            fig.add_trace(
                                go.Scatter(
                                    x=[x],
                                    y=[y],
                                    mode="markers+text",
                                    marker=dict(size=10, color="#9C27B0"),
                                    text=[str(node)],
                                    textposition="middle right",
                                    hoverinfo="text",
                                    hovertext=f"Value: {node}",
                                )
                            )

                    # Initialize with root node
                    fig.add_trace(
                        go.Scatter(
                            x=[0],
                            y=[0],
                            mode="markers+text",
                            marker=dict(size=20, color="#4CAF50"),
                            text=["Root"],
                            textposition="middle right",
                            hoverinfo="text",
                            hovertext="Root of value hierarchy",
                        )
                    )

                    # Add all nodes to plot
                    add_nodes_to_plot(capsule.value_hierarchy, 1, 0, 0)

                    # Update layout
                    fig.update_layout(
                        title="Value Hierarchy Tree",
                        showlegend=False,
                        hovermode="closest",
                        xaxis=dict(
                            showgrid=False, zeroline=False, showticklabels=False
                        ),
                        yaxis=dict(
                            showgrid=False, zeroline=False, showticklabels=False
                        ),
                        margin=dict(l=20, r=20, t=40, b=20),
                        height=400,
                    )

                    st.plotly_chart(fig, use_container_width=True)

            with hierarchy_tabs[1]:
                # Improved nested view with better formatting
                def display_value_node(node, level=0):
                    indent = level * 20  # Use CSS for proper indentation

                    if isinstance(node, dict):
                        for key, value in node.items():
                            # Use different colors based on level
                            level_colors = [
                                "#4CAF50",
                                "#2196F3",
                                "#9C27B0",
                                "#FF9800",
                                "#F44336",
                            ]
                            color = level_colors[level % len(level_colors)]

                            # Create a nice heading for each key
                            st.markdown(
                                f"""
                            <div style="margin-left:{indent}px;margin-bottom:8px;">
                                <div style="font-weight:bold;color:{color};font-size:{1.2-level*0.1}em;">{key}</div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            display_value_node(value, level + 1)
                    elif isinstance(node, list):
                        for i, item in enumerate(node):
                            if isinstance(item, (str, int, float)):
                                st.markdown(
                                    f"""
                                <div style="margin-left:{indent+10}px;margin-bottom:5px;">
                                    <span style="color:#555;">•</span> {item}
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                            else:
                                display_value_node(item, level)
                    else:
                        st.markdown(
                            f"""
                        <div style="margin-left:{indent+10}px;background-color:#f8f8f8;padding:8px;border-left:3px solid {UATP7_CAPSULE_TYPE_COLORS.get('ValueInception')}">
                            {node}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                # Show the hierarchy with the enhanced display
                display_value_node(capsule.value_hierarchy)

            with hierarchy_tabs[2]:
                # Raw JSON view
                st.json(capsule.value_hierarchy)

        # Enhanced tradeoff analysis visualization
        if hasattr(capsule, "tradeoff_analysis") and capsule.tradeoff_analysis:
            st.subheader("Tradeoff Analysis")

            # Check if we have named tradeoffs with scores
            has_scores = False
            tradeoff_names = []
            tradeoff_scores = []

            for tradeoff in capsule.tradeoff_analysis:
                if (
                    isinstance(tradeoff, dict)
                    and "name" in tradeoff
                    and "score" in tradeoff
                ):
                    has_scores = True
                    tradeoff_names.append(tradeoff["name"])
                    tradeoff_scores.append(float(tradeoff["score"]))

            # If we have scores, show a radar chart
            if has_scores and len(tradeoff_names) >= 3:
                try:
                    import plotly.graph_objects as go

                    # Create a radar chart
                    fig = go.Figure()

                    # Add the tradeoffs as a polygon
                    fig.add_trace(
                        go.Scatterpolar(
                            r=tradeoff_scores,
                            theta=tradeoff_names,
                            fill="toself",
                            name="Values",
                            line_color=UATP7_CAPSULE_TYPE_COLORS.get("ValueInception"),
                            fillcolor=f"rgba{tuple(int(UATP7_CAPSULE_TYPE_COLORS.get('ValueInception', '#2e8b57').lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.2,)}",
                        )
                    )

                    # Update layout for better presentation
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True, range=[0, max(tradeoff_scores) * 1.2]
                            )
                        ),
                        showlegend=False,
                        title="Tradeoff Analysis",
                    )

                    # Display the chart
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Could not create radar chart: {str(e)}")

            # Show detailed analysis for each tradeoff
            for i, tradeoff in enumerate(capsule.tradeoff_analysis):
                with st.expander(
                    f"Tradeoff {i+1}: {tradeoff.get('name', '')}"
                    if isinstance(tradeoff, dict) and "name" in tradeoff
                    else f"Tradeoff {i+1}",
                    expanded=(i == 0),
                ):
                    if isinstance(tradeoff, dict):
                        # Format tradeoff details in a nicer way
                        for k, v in tradeoff.items():
                            if k.lower() == "name":
                                st.markdown(f"#### {v}")
                            elif k.lower() == "description":
                                st.markdown(f"**Description:** {v}")
                            elif k.lower() == "score":
                                try:
                                    score_val = float(v)
                                    # Show a colored gauge for the score
                                    st.markdown(f"**Score:** {score_val:.2f}")
                                    # Create a gradient colored progress bar
                                    st.progress(min(score_val / 10, 1.0))
                                except:
                                    st.markdown(f"**Score:** {v}")
                            elif k.lower() in [
                                "values",
                                "principles",
                                "affected_values",
                            ]:
                                if isinstance(v, list):
                                    st.markdown(f"**{k.title()}:**")
                                    for val in v:
                                        st.markdown(f"- {val}")
                                else:
                                    st.markdown(f"**{k.title()}:** {v}")
                            elif k.lower() in ["pros", "cons", "alternatives"]:
                                if isinstance(v, list):
                                    st.markdown(f"**{k.title()}:**")
                                    for item in v:
                                        st.markdown(f"- {item}")
                                else:
                                    st.markdown(f"**{k.title()}:** {v}")
                            else:
                                st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")
                    else:
                        st.markdown(str(tradeoff))

        # Display derivation method with better formatting
        if hasattr(capsule, "derivation_method") and capsule.derivation_method:
            st.subheader("Derivation Method")
            method = capsule.derivation_method

            # Format based on whether it's structured or not
            if isinstance(method, dict):
                # Show as a nice formatted card
                method_name = method.get("name", "Unnamed Method")
                method_description = method.get("description", "")

                st.markdown(
                    f"""
                <div style="background-color:rgba(46,139,87,0.1);padding:15px;border-radius:5px;border-left:5px solid {UATP7_CAPSULE_TYPE_COLORS.get('ValueInception')}">
                    <div style="font-weight:bold;font-size:1.1em;">{method_name}</div>
                    <div style="margin-top:8px;">{method_description}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # If there are additional fields, show them as well
                for k, v in method.items():
                    if k not in ["name", "description"]:
                        st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")
            else:
                # Just show the raw string
                st.markdown(
                    f"""
                <div style="background-color:rgba(46,139,87,0.1);padding:15px;border-radius:5px;border-left:5px solid {UATP7_CAPSULE_TYPE_COLORS.get('ValueInception')}">
                    {method}
                </div>
                """,
                    unsafe_allow_html=True,
                )

        # Add quality metrics if available
        if hasattr(capsule, "quality_metrics") and capsule.quality_metrics:
            st.subheader("Quality Metrics")

            metrics = capsule.quality_metrics
            if isinstance(metrics, dict):
                metric_cols = st.columns(min(3, len(metrics)))
                for i, (metric, value) in enumerate(metrics.items()):
                    with metric_cols[i % len(metric_cols)]:
                        try:
                            float_val = float(value)
                            st.metric(
                                metric.replace("_", " ").title(), f"{float_val:.2f}"
                            )
                            st.progress(min(float_val / 10, 1.0))
                        except:
                            st.metric(metric.replace("_", " ").title(), value)


def render_simulated_malice_content(capsule: SimulatedMaliceCapsule):
    """Render specialized content for Simulated Malice capsules with enhanced visualizations."""
    with st.expander("Simulated Malice Details", expanded=True):
        # Add a colorful header with capsule type badge
        st.markdown(
            f"""
        <div style="display:flex;align-items:center;margin-bottom:1rem;">
            <div style="background-color:{UATP7_CAPSULE_TYPE_COLORS.get('SimulatedMalice', '#b22222')};color:white;
                 padding:3px 8px;border-radius:10px;margin-right:10px;font-size:0.8em;">
                SIMULATED MALICE
            </div>
            <div style="font-size:1.2em;font-weight:bold;">Security Testing Simulation</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Create tabs for better organization
        tabs = st.tabs(
            ["Test Details", "Response Analysis", "Risk Assessment", "Mitigation"]
        )

        with tabs[0]:
            # Test scenario with enhanced formatting
            if hasattr(capsule, "test_scenario") and capsule.test_scenario:
                st.subheader("Test Scenario")
                # Add a styled box for the test scenario
                st.markdown(
                    f"""
                <div style="background-color:rgba(178,34,34,0.05);padding:15px;border-radius:5px;border-left:5px solid {UATP7_CAPSULE_TYPE_COLORS.get('SimulatedMalice', '#b22222')}">
                    {capsule.test_scenario}
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Malicious input with syntax highlighting if possible
            if hasattr(capsule, "malicious_input") and capsule.malicious_input:
                st.subheader("Malicious Input")

                # Try to detect if it's JSON for syntax highlighting
                try:
                    if capsule.malicious_input.strip().startswith(
                        "{"
                    ) or capsule.malicious_input.strip().startswith("["):
                        # It might be JSON, let's try to parse it
                        input_data = json.loads(capsule.malicious_input)
                        st.json(input_data)
                    else:
                        # Not JSON, use code block with appropriate syntax highlighting if possible
                        if any(
                            pattern in capsule.malicious_input
                            for pattern in ["<script>", "function(", "var ", "const "]
                        ):
                            st.code(capsule.malicious_input, language="javascript")
                        elif any(
                            pattern in capsule.malicious_input
                            for pattern in [
                                "SELECT ",
                                "INSERT ",
                                "UPDATE ",
                                "DELETE ",
                                "DROP ",
                            ]
                        ):
                            st.code(capsule.malicious_input, language="sql")
                        else:
                            st.code(capsule.malicious_input, language="")
                except:
                    # If parsing fails, just use a regular code block
                    st.code(capsule.malicious_input, language="")

            # Display test metadata if available
            if hasattr(capsule, "test_metadata") and capsule.test_metadata:
                with st.expander("Test Metadata", expanded=False):
                    if isinstance(capsule.test_metadata, dict):
                        # Display structured metadata
                        cols = st.columns(2)
                        for i, (key, value) in enumerate(capsule.test_metadata.items()):
                            with cols[i % 2]:
                                st.markdown(
                                    f"**{key.replace('_', ' ').title()}:** {value}"
                                )
                    else:
                        st.markdown(capsule.test_metadata)

            # Test result with enhanced visual feedback
            if hasattr(capsule, "test_result") and capsule.test_result:
                # Display with appropriate styling based on result
                result_lower = str(capsule.test_result).lower()
                if "pass" in result_lower or "success" in result_lower:
                    result_color = "#2e8b57"  # Sea Green for pass
                    icon = "[OK]"
                elif "fail" in result_lower:
                    result_color = "#b22222"  # Fire Brick for fail
                    icon = "[ERROR]"
                else:
                    result_color = "#ffa500"  # Orange for indeterminate
                    icon = "[WARN]"

                st.markdown(
                    f"""
                <div style="background-color:rgba{tuple(int(result_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)};padding:10px;border-radius:5px;margin:15px 0;">
                    <div style="font-size:1.1em;font-weight:bold;color:{result_color};">{icon} Test Result: {capsule.test_result}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        with tabs[1]:
            # Enhanced display for expected vs. actual response with diff highlighting
            if (
                hasattr(capsule, "expected_response")
                and capsule.expected_response
                and hasattr(capsule, "actual_response")
                and capsule.actual_response
            ):
                st.markdown("### Response Comparison")
                st.markdown(
                    "Compare the expected (secure) response with the actual response from the system under test."
                )

                # Create tabs for different view modes
                response_tabs = st.tabs(["Side by Side", "Differences", "Raw Data"])

                with response_tabs[0]:
                    # Side by side comparison
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("#### Expected Response")
                        # Format as code or JSON depending on type
                        if isinstance(capsule.expected_response, (dict, list)):
                            st.json(capsule.expected_response)
                        else:
                            st.code(str(capsule.expected_response))

                    with col2:
                        st.markdown("#### Actual Response")
                        # Format as code or JSON depending on type
                        if isinstance(capsule.actual_response, (dict, list)):
                            st.json(capsule.actual_response)
                        else:
                            st.code(str(capsule.actual_response))

                with response_tabs[1]:
                    # Try to highlight differences
                    st.markdown("#### Key Differences")
                    try:
                        import difflib

                        # Convert both to string format for comparison
                        expected_str = (
                            json.dumps(capsule.expected_response, indent=2)
                            if isinstance(capsule.expected_response, (dict, list))
                            else str(capsule.expected_response)
                        )
                        actual_str = (
                            json.dumps(capsule.actual_response, indent=2)
                            if isinstance(capsule.actual_response, (dict, list))
                            else str(capsule.actual_response)
                        )

                        # Generate diff
                        diff = list(
                            difflib.ndiff(
                                expected_str.splitlines(), actual_str.splitlines()
                            )
                        )

                        # Filter and display only lines with differences
                        has_differences = False
                        diff_html = "<pre style='white-space:pre-wrap;'>\n"
                        for line in diff:
                            if (
                                line.startswith("+ ")
                                or line.startswith("- ")
                                or line.startswith("? ")
                            ):
                                has_differences = True
                                if line.startswith("+ "):
                                    diff_html += f"<span style='background-color:rgba(46,139,87,0.2);display:block;'>{line}</span>\n"
                                elif line.startswith("- "):
                                    diff_html += f"<span style='background-color:rgba(178,34,34,0.2);display:block;'>{line}</span>\n"
                                elif line.startswith("? "):
                                    diff_html += f"<span style='color:#888;font-size:0.9em;display:block;'>{line}</span>\n"
                        diff_html += "</pre>"

                        if has_differences:
                            st.markdown(diff_html, unsafe_allow_html=True)
                        else:
                            st.success(
                                "No differences found - expected and actual responses match exactly."
                            )
                    except Exception as e:
                        st.error(f"Could not generate difference view: {str(e)}")
                        st.info(
                            "Falling back to standard view. Please use the Side by Side tab."
                        )

                with response_tabs[2]:
                    # Raw data view
                    st.markdown("#### Raw Response Data")
                    st.json(
                        {
                            "expected": capsule.expected_response,
                            "actual": capsule.actual_response,
                        }
                    )

        with tabs[2]:
            # Enhanced risk assessment visualization
            if hasattr(capsule, "risk_assessment") and capsule.risk_assessment:
                st.subheader("Risk Assessment")

                # If we have severity and likelihood, create an enhanced visualization
                if (
                    isinstance(capsule.risk_assessment, dict)
                    and "severity" in capsule.risk_assessment
                    and "likelihood" in capsule.risk_assessment
                ):
                    severity = float(capsule.risk_assessment["severity"])
                    likelihood = float(capsule.risk_assessment["likelihood"])

                    risk_score = severity * likelihood

                    # Determine risk level and colors based on score
                    if risk_score >= 0.7:
                        risk_level = "Critical"
                        risk_color = "#d32f2f"  # Red
                    elif risk_score >= 0.4:
                        risk_level = "High"
                        risk_color = "#f57c00"  # Orange
                    elif risk_score >= 0.2:
                        risk_level = "Medium"
                        risk_color = "#fbc02d"  # Yellow
                    else:
                        risk_level = "Low"
                        risk_color = "#388e3c"  # Green

                    # Create a more informative display with gauges and metrics
                    col1, col2, col3 = st.columns([2, 2, 3])

                    with col1:
                        st.markdown("#### Severity")
                        st.markdown(
                            f"<div style='font-size:2em;text-align:center;'>{severity:.2f}</div>",
                            unsafe_allow_html=True,
                        )
                        st.progress(severity)

                    with col2:
                        st.markdown("#### Likelihood")
                        st.markdown(
                            f"<div style='font-size:2em;text-align:center;'>{likelihood:.2f}</div>",
                            unsafe_allow_html=True,
                        )
                        st.progress(likelihood)

                    with col3:
                        st.markdown("#### Risk Score")
                        st.markdown(
                            f"""
                        <div style="text-align:center;">
                            <div style="font-size:2.5em;color:{risk_color};">{risk_score:.2f}</div>
                            <div style="font-weight:bold;color:{risk_color};">{risk_level} Risk</div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                        st.progress(min(risk_score, 1.0))

                    # Add risk matrix visualization
                    st.markdown("### Risk Matrix")
                    try:
                        import numpy as np
                        import plotly.graph_objects as go

                        # Create risk matrix as a heatmap
                        x = np.linspace(0, 1, 20)
                        y = np.linspace(0, 1, 20)
                        XX, YY = np.meshgrid(x, y)
                        Z = XX * YY

                        # Generate risk zones
                        risk_zones = np.zeros_like(Z)
                        risk_zones[Z >= 0.7] = 4  # Critical
                        risk_zones[(Z >= 0.4) & (Z < 0.7)] = 3  # High
                        risk_zones[(Z >= 0.2) & (Z < 0.4)] = 2  # Medium
                        risk_zones[Z < 0.2] = 1  # Low

                        # Create heatmap for the risk matrix
                        fig = go.Figure()

                        # Add the risk zones as a heatmap
                        fig.add_trace(
                            go.Heatmap(
                                z=risk_zones,
                                x=x,
                                y=y,
                                colorscale=[
                                    [0, "#388e3c"],  # Low - Green
                                    [0.25, "#fbc02d"],  # Medium - Yellow
                                    [0.5, "#f57c00"],  # High - Orange
                                    [0.75, "#d32f2f"],  # Critical - Red
                                ],
                                showscale=False,
                            )
                        )

                        # Add labels for risk zones
                        annotations = [
                            dict(
                                x=0.15,
                                y=0.15,
                                text="LOW",
                                showarrow=False,
                                font=dict(color="white", size=14),
                            ),
                            dict(
                                x=0.35,
                                y=0.35,
                                text="MEDIUM",
                                showarrow=False,
                                font=dict(color="black", size=14),
                            ),
                            dict(
                                x=0.6,
                                y=0.6,
                                text="HIGH",
                                showarrow=False,
                                font=dict(color="black", size=14),
                            ),
                            dict(
                                x=0.85,
                                y=0.85,
                                text="CRITICAL",
                                showarrow=False,
                                font=dict(color="white", size=14),
                            ),
                        ]

                        # Add the current risk point
                        fig.add_trace(
                            go.Scatter(
                                x=[likelihood],
                                y=[severity],
                                mode="markers",
                                marker=dict(
                                    size=20,
                                    color="white",
                                    line=dict(width=2, color="black"),
                                ),
                                name="Current Risk",
                            )
                        )

                        # Update layout
                        fig.update_layout(
                            title="Risk Matrix",
                            xaxis=dict(title="Likelihood", range=[0, 1]),
                            yaxis=dict(title="Severity", range=[0, 1]),
                            height=500,
                            width=500,
                            annotations=annotations,
                        )

                        st.plotly_chart(fig)
                    except Exception as e:
                        # Fallback to simple visualization
                        st.error(f"Could not create risk matrix: {str(e)}")
                        st.markdown(
                            f"""
                        <div style='background:#f0f0f0;width:300px;height:300px;position:relative;margin:20px 0;border:1px solid #ccc;'>
                            <div style='position:absolute;bottom:0;left:0;width:100%;height:20px;text-align:center;'>Likelihood</div>
                            <div style='position:absolute;top:0;left:-20px;height:100%;width:20px;writing-mode:vertical-lr;transform:rotate(180deg);text-align:center;'>Severity</div>
                            <div style='position:absolute;left:{likelihood*100}%;bottom:{severity*100}%;transform:translate(-50%,50%);width:20px;height:20px;border-radius:50%;background-color:{risk_color};'></div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                    # Additional risk details
                    if (
                        len(capsule.risk_assessment) > 2
                    ):  # If we have more than just severity and likelihood
                        st.markdown("### Additional Risk Factors")
                        for key, value in capsule.risk_assessment.items():
                            if key not in ["severity", "likelihood"]:
                                st.markdown(
                                    f"**{key.replace('_', ' ').title()}:** {value}"
                                )
                else:
                    # No severity/likelihood data, just show the raw assessment
                    st.json(capsule.risk_assessment)

        with tabs[3]:
            # Mitigation information
            if (
                hasattr(capsule, "preventative_measures")
                and capsule.preventative_measures
            ):
                st.subheader("Preventative Measures")

                if isinstance(capsule.preventative_measures, list):
                    # Check if we have structured measures with priority
                    for i, measure in enumerate(capsule.preventative_measures):
                        if isinstance(measure, dict) and "description" in measure:
                            # Get priority if available
                            priority = measure.get("priority", "Medium")
                            priority_color = {
                                "Critical": "#d32f2f",
                                "High": "#f57c00",
                                "Medium": "#fbc02d",
                                "Low": "#388e3c",
                            }.get(priority, "#fbc02d")

                            st.markdown(
                                f"""
                            <div style="margin-bottom:10px;padding:10px;border-left:4px solid {priority_color};background-color:rgba{tuple(int(priority_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}">
                                <div style="font-weight:bold;">{i+1}. {measure.get('title', 'Measure ' + str(i+1))}</div>
                                <div>{measure['description']}</div>
                                {f'<div style="margin-top:5px;font-style:italic;">{measure.get("implementation", "")}</div>' if 'implementation' in measure else ''}
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(f"**{i+1}.** {measure}")
                else:
                    st.markdown(capsule.preventative_measures)

            # Remediation steps if available
            if hasattr(capsule, "remediation_steps") and capsule.remediation_steps:
                st.subheader("Remediation Steps")

                if isinstance(capsule.remediation_steps, list):
                    for i, step in enumerate(capsule.remediation_steps):
                        if isinstance(step, dict):
                            st.markdown(f"**Step {i+1}: {step.get('title', '')}**")
                            st.markdown(step.get("description", ""))
                            if "code" in step:
                                st.code(step["code"])
                        else:
                            st.markdown(f"**Step {i+1}:** {step}")
                else:
                    st.markdown(capsule.remediation_steps)

            # References section if available
            if hasattr(capsule, "security_references") and capsule.security_references:
                st.subheader("Security References")

                if isinstance(capsule.security_references, list):
                    for ref in capsule.security_references:
                        if isinstance(ref, dict) and "url" in ref:
                            st.markdown(
                                f"[{ref.get('title', ref['url'])}]({ref['url']}) - {ref.get('description', '')}"
                            )
                        else:
                            st.markdown(f"- {ref}")
                else:
                    st.markdown(capsule.security_references)


def render_implicit_consent_content(capsule: ImplicitConsentCapsule):
    """Render specialized content for Implicit Consent capsules with enhanced visualization."""
    with st.expander("Implicit Consent Details", expanded=True):
        # Add a colorful header with capsule type badge
        st.markdown(
            f"""
        <div style="display:flex;align-items:center;margin-bottom:1rem;">
            <div style="background-color:{UATP7_CAPSULE_TYPE_COLORS.get('ImplicitConsent', '#ff8c00')};color:white;
                 padding:3px 8px;border-radius:10px;margin-right:10px;font-size:0.8em;">
                IMPLICIT CONSENT
            </div>
            <div style="font-size:1.2em;font-weight:bold;">Emergency Action Report</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Create tabs for better organization
        tabs = st.tabs(["Action & Rationale", "Affected Rights", "Remediation"])

        with tabs[0]:
            # Display action performed with better formatting
            if hasattr(capsule, "action_performed") and capsule.action_performed:
                st.subheader("Action Performed")
                # Add a styled box for the action performed
                st.markdown(
                    f"""
                <div style="background-color:rgba(255,140,0,0.05);padding:15px;border-radius:5px;border-left:5px solid {UATP7_CAPSULE_TYPE_COLORS.get('ImplicitConsent', '#ff8c00')}">
                    {capsule.action_performed}
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Display consent omitted reason with enhanced formatting
            if (
                hasattr(capsule, "consent_omitted_reason")
                and capsule.consent_omitted_reason
            ):
                st.subheader("Reason Consent Was Omitted")

                # Try to detect emergency keywords for appropriate styling
                reason_text = capsule.consent_omitted_reason
                emergency_keywords = [
                    "emergency",
                    "urgent",
                    "critical",
                    "immediate",
                    "life-threatening",
                    "safety",
                    "security",
                ]
                is_emergency = any(
                    keyword in reason_text.lower() for keyword in emergency_keywords
                )

                # Style based on whether it's an emergency situation
                if is_emergency:
                    st.markdown(
                        f"""
                    <div style="background-color:rgba(178,34,34,0.1);padding:15px;border-radius:5px;border-left:5px solid #b22222;margin-bottom:15px;">
                        <div style="display:flex;align-items:center;margin-bottom:10px;">
                            <span style="color:#b22222;font-size:1.5em;margin-right:10px;">[WARN]</span>
                            <span style="font-weight:bold;color:#b22222;">EMERGENCY SITUATION</span>
                        </div>
                        {reason_text}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""
                    <div style="background-color:rgba(255,165,0,0.1);padding:15px;border-radius:5px;border-left:5px solid #ffa500;">
                        {reason_text}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

            # Display retrospective notice if available
            if (
                hasattr(capsule, "retrospective_notice")
                and capsule.retrospective_notice
            ):
                st.subheader("Retrospective Notice")
                st.markdown(
                    f"""
                <div style="background-color:#f8f9fa;padding:15px;border-radius:5px;border:1px solid #dee2e6;">
                    {capsule.retrospective_notice}
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Display a disclaimer about retrospective notices
                st.info(
                    "ℹ️ A retrospective notice is provided when consent couldn't be obtained before an action, but transparency about the action is still important."
                )

        with tabs[1]:
            # Enhanced visualization of affected rights
            if hasattr(capsule, "affected_rights") and capsule.affected_rights:
                st.subheader("Affected Rights")

                # Display a small explanation
                st.markdown(
                    """The following rights were affected by this action taken without explicit consent:"""
                )

                # Create a more visual representation of the affected rights
                if (
                    isinstance(capsule.affected_rights, list)
                    and len(capsule.affected_rights) > 0
                ):
                    # Try to categorize rights by impact level if there's structured data
                    structured_rights = all(
                        isinstance(right, dict) for right in capsule.affected_rights
                    )

                    if structured_rights:
                        # Group rights by impact level if available
                        try:
                            # Create impact level grouping if possible
                            impact_groups = {}
                            for right in capsule.affected_rights:
                                if isinstance(right, dict):
                                    impact = right.get("impact_level", "Medium")
                                    if impact not in impact_groups:
                                        impact_groups[impact] = []
                                    impact_groups[impact].append(right)

                            # Display rights grouped by impact
                            for impact, rights in sorted(
                                impact_groups.items(),
                                key=lambda x: {"High": 0, "Medium": 1, "Low": 2}.get(
                                    x[0], 3
                                ),
                            ):
                                impact_color = {
                                    "High": "#b22222",  # Fire Brick
                                    "Medium": "#ff8c00",  # Dark Orange
                                    "Low": "#2e8b57",  # Sea Green
                                }.get(impact, "#6c757d")  # Gray

                                st.markdown(
                                    f"""<div style="margin-top:15px;font-weight:bold;color:{impact_color};">{impact} Impact Rights:</div>""",
                                    unsafe_allow_html=True,
                                )

                                for right in rights:
                                    right_name = right.get("name", "Unnamed Right")
                                    right_description = right.get("description", "")

                                    st.markdown(
                                        f"""
                                    <div style="margin-bottom:10px;padding:10px;background-color:rgba{tuple(int(impact_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)};border-left:4px solid {impact_color};">
                                        <div style="font-weight:bold;">{right_name}</div>
                                        <div>{right_description}</div>
                                    </div>
                                    """,
                                        unsafe_allow_html=True,
                                    )
                        except Exception:
                            # Fallback to simple list if grouping fails
                            for right in capsule.affected_rights:
                                if isinstance(right, dict):
                                    st.markdown(
                                        f"**{right.get('name', 'Right')}**: {right.get('description', '')}"
                                    )
                                else:
                                    st.markdown(f"- {right}")
                    else:
                        # Simple formatted list for non-structured rights
                        for i, right in enumerate(capsule.affected_rights):
                            st.markdown(
                                f"""
                            <div style="margin-bottom:10px;padding:10px;background-color:rgba(255,140,0,0.05);border-left:4px solid {UATP7_CAPSULE_TYPE_COLORS.get('ImplicitConsent', '#ff8c00')}">
                                {right}
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                # Add explanation about rights implications
                st.markdown(
                    """<div style="margin-top:15px;font-style:italic;color:#6c757d;">
                    The UATP protocol records affected rights to ensure transparency and accountability, even when actions must be taken without explicit consent.
                </div>""",
                    unsafe_allow_html=True,
                )

        with tabs[2]:
            # Enhanced remediation options display
            if hasattr(capsule, "remediation_options") and capsule.remediation_options:
                st.subheader("Remediation Options")

                # Add explanation about remediation
                st.markdown(
                    """These options provide ways to address or mitigate the effects of actions taken without prior explicit consent:"""
                )

                # Check if we have structured options
                structured_options = (
                    all(
                        isinstance(opt, dict) and "title" in opt
                        for opt in capsule.remediation_options
                    )
                    if isinstance(capsule.remediation_options, list)
                    else False
                )

                if structured_options:
                    # Create option cards with more information
                    cols = st.columns(min(3, len(capsule.remediation_options)))

                    for i, option in enumerate(capsule.remediation_options):
                        with cols[i % min(3, len(capsule.remediation_options))]:
                            option_title = option.get("title", f"Option {i+1}")
                            option_desc = option.get("description", "")
                            option_action = option.get("action", "")

                            st.markdown(
                                f"""
                            <div style="height:100%;padding:15px;border:1px solid #dee2e6;border-radius:5px;margin-bottom:15px;">
                                <div style="font-weight:bold;font-size:1.1em;margin-bottom:10px;color:{UATP7_CAPSULE_TYPE_COLORS.get('ImplicitConsent')}">{option_title}</div>
                                <div style="margin-bottom:10px;">{option_desc}</div>
                                {f'<div style="font-style:italic;font-size:0.9em;margin-top:5px;">Action: {option_action}</div>' if option_action else ''}
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                    # Add button-like options for interaction (note: these are visual only)
                    st.markdown("### User Response")

                    response_cols = st.columns(3)

                    with response_cols[0]:
                        st.markdown(
                            f"""
                        <div style="text-align:center;padding:10px;background-color:{UATP7_CAPSULE_TYPE_COLORS.get('ImplicitConsent')};color:white;border-radius:5px;cursor:pointer;">
                            Accept Action
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                    with response_cols[1]:
                        st.markdown(
                            f"""
                        <div style="text-align:center;padding:10px;background-color:white;color:{UATP7_CAPSULE_TYPE_COLORS.get('ImplicitConsent')};border:1px solid {UATP7_CAPSULE_TYPE_COLORS.get('ImplicitConsent')};border-radius:5px;cursor:pointer;">
                            Request Remediation
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                    with response_cols[2]:
                        st.markdown(
                            """
                        <div style="text-align:center;padding:10px;background-color:#f8f9fa;color:#6c757d;border:1px solid #dee2e6;border-radius:5px;cursor:pointer;">
                            File Complaint
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                else:
                    # Simple expanders for non-structured options
                    for i, option in enumerate(capsule.remediation_options):
                        with st.expander(f"Option {i+1}", expanded=i == 0):
                            if isinstance(option, dict):
                                for k, v in option.items():
                                    st.markdown(
                                        f"**{k.replace('_', ' ').title()}:** {v}"
                                    )
                            else:
                                st.markdown(str(option))

                # Add information about policy for remediation
                st.info(
                    "ℹ️ The UATP protocol requires that actions taken without consent must offer remediation options to affected users. This ensures accountability and recourse."
                )

            # If timestamps are available, display them
            if hasattr(capsule, "action_timestamp") and capsule.action_timestamp:
                display_datetime_info(capsule.action_timestamp, "Action Timestamp")

            if hasattr(capsule, "reporting_timestamp") and capsule.reporting_timestamp:
                display_datetime_info(
                    capsule.reporting_timestamp, "Reporting Timestamp"
                )


def render_self_hallucination_content(capsule: SelfHallucinationCapsule):
    """Render specialized content for Self Hallucination capsules with enhanced visualization."""
    with st.expander("Self Hallucination Details", expanded=True):
        # Add a colorful header with capsule type badge
        st.markdown(
            f"""
        <div style="display:flex;align-items:center;margin-bottom:1rem;">
            <div style="background-color:{UATP7_CAPSULE_TYPE_COLORS.get('SelfHallucination', '#9932cc')};color:white;
                 padding:3px 8px;border-radius:10px;margin-right:10px;font-size:0.8em;">
                SELF HALLUCINATION
            </div>
            <div style="font-size:1.2em;font-weight:bold;">Hallucination Analysis Report</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Create tabs for better organization
        tabs = st.tabs(["Overview", "Content Analysis", "Detection Details"])

        with tabs[0]:
            # Display hallucination type with better formatting
            if hasattr(capsule, "hallucination_type") and capsule.hallucination_type:
                st.subheader("Hallucination Type")

                # Create a visual hallucination type indicator
                hallucination_type = capsule.hallucination_type

                # Determine severity level based on type keywords
                severity_level = "Medium"  # Default
                severity_color = "#ff8c00"  # Default orange

                # Adjust severity based on hallucination type
                lower_type = hallucination_type.lower()
                if any(
                    keyword in lower_type
                    for keyword in ["critical", "severe", "major", "dangerous"]
                ):
                    severity_level = "High"
                    severity_color = "#b22222"  # Fire Brick
                elif any(
                    keyword in lower_type
                    for keyword in ["minor", "low", "slight", "minimal"]
                ):
                    severity_level = "Low"
                    severity_color = "#2e8b57"  # Sea Green

                st.markdown(
                    f"""
                <div style="display:flex;align-items:center;margin-bottom:15px;">
                    <div style="width:15px;height:15px;border-radius:50%;background-color:{severity_color};margin-right:10px;"></div>
                    <div style="font-size:1.1em;font-weight:bold;">{hallucination_type}</div>
                    <div style="margin-left:auto;font-size:0.9em;color:{severity_color};">{severity_level} Severity</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Summary box at the top
            summary_parts = []

            # Get relevant information for summary
            if hasattr(capsule, "affected_content") and capsule.affected_content:
                if len(capsule.affected_content) > 100:
                    summary_parts.append(
                        f"Affected content: {capsule.affected_content[:100]}..."
                    )
                else:
                    summary_parts.append(
                        f"Affected content: {capsule.affected_content}"
                    )

            if hasattr(capsule, "detection_method") and capsule.detection_method:
                summary_parts.append(f"Detected via: {capsule.detection_method}")

            if (
                hasattr(capsule, "confidence_assessment")
                and capsule.confidence_assessment
            ):
                if (
                    isinstance(capsule.confidence_assessment, dict)
                    and "overall" in capsule.confidence_assessment
                ):
                    summary_parts.append(
                        f"Confidence: {float(capsule.confidence_assessment['overall']):.2f}"
                    )
                elif isinstance(capsule.confidence_assessment, (int, float)):
                    summary_parts.append(
                        f"Confidence: {float(capsule.confidence_assessment):.2f}"
                    )

            # Create summary box if we have information
            if summary_parts:
                st.markdown(
                    f"""
                <div style="background-color:rgba(153,50,204,0.05);padding:15px;border-radius:5px;margin-bottom:20px;">
                    <div style="font-weight:bold;margin-bottom:10px;">Summary</div>
                    <ul style="margin:0;padding-left:20px;">
                        {''.join([f'<li>{part}</li>' for part in summary_parts])}
                    </ul>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Display confidence assessment with better visualization
            if (
                hasattr(capsule, "confidence_assessment")
                and capsule.confidence_assessment
            ):
                st.subheader("Confidence Assessment")

                if isinstance(capsule.confidence_assessment, dict):
                    # Create a more visual gauge for confidence metrics
                    confidence_items = []
                    for k, v in capsule.confidence_assessment.items():
                        try:
                            val = float(v)
                            if 0 <= val <= 1:
                                confidence_items.append((k, val))
                        except:
                            pass

                    if confidence_items:
                        # If we have numeric confidence values, create a visual gauge grid
                        cols = st.columns(min(3, len(confidence_items)))

                        for i, (key, value) in enumerate(confidence_items):
                            with cols[i % min(3, len(confidence_items))]:
                                # Determine color based on value
                                if value >= 0.7:
                                    conf_color = (
                                        "#2e8b57"  # Sea Green for high confidence
                                    )
                                elif value >= 0.4:
                                    conf_color = (
                                        "#ff8c00"  # Dark Orange for medium confidence
                                    )
                                else:
                                    conf_color = (
                                        "#b22222"  # Fire Brick for low confidence
                                    )

                                # Create visual gauge
                                st.markdown(
                                    f"""
                                <div style="text-align:center;margin-bottom:15px;">
                                    <div style="font-weight:bold;margin-bottom:5px;">{key.replace('_', ' ').title()}</div>
                                    <div style="margin:0 auto;width:80px;height:80px;background-color:rgba{tuple(int(conf_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.2,)};border-radius:50%;display:flex;align-items:center;justify-content:center;">
                                        <div style="font-size:1.5em;font-weight:bold;color:{conf_color};">{value:.2f}</div>
                                    </div>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                                st.progress(value)

                    # Display non-numeric values separately
                    for k, v in capsule.confidence_assessment.items():
                        try:
                            val = float(v)
                            if val < 0 or val > 1:  # Outside normal confidence range
                                st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")
                        except:
                            st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")
                else:
                    # Not a dictionary, just display as is
                    st.markdown(
                        f"""
                    <div style="padding:10px;background-color:rgba(153,50,204,0.05);border-radius:5px;">
                        {str(capsule.confidence_assessment)}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        with tabs[1]:
            # Enhanced content comparison visualization
            col1, col2 = st.columns(2)

            with col1:
                # Display affected content with better formatting
                if hasattr(capsule, "affected_content") and capsule.affected_content:
                    st.markdown("### Affected Content")

                    # Add styling for the affected content
                    st.markdown(
                        f"""
                    <div style="background-color:rgba(178,34,34,0.05);padding:15px;border-radius:5px;border-left:5px solid #b22222;font-family:monospace;white-space:pre-wrap;">
                        {capsule.affected_content.replace('\n', '<br>')}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

            with col2:
                # Display correction with better formatting
                if hasattr(capsule, "correction") and capsule.correction:
                    st.markdown("### Corrected Content")

                    # Add styling for the correction
                    st.markdown(
                        f"""
                    <div style="background-color:rgba(46,139,87,0.05);padding:15px;border-radius:5px;border-left:5px solid #2e8b57;font-family:monospace;white-space:pre-wrap;">
                        {capsule.correction.replace('\n', '<br>')}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

            # If we have both affected content and correction, show diff view
            if (
                hasattr(capsule, "affected_content")
                and capsule.affected_content
                and hasattr(capsule, "correction")
                and capsule.correction
            ):
                st.markdown("### Differences")

                try:
                    import difflib

                    # Generate diff between affected content and correction
                    diff = list(
                        difflib.ndiff(
                            capsule.affected_content.splitlines(),
                            capsule.correction.splitlines(),
                        )
                    )

                    # Build HTML for better diff visualization
                    diff_html = "<pre style='white-space:pre-wrap;background-color:#f5f5f5;padding:15px;border-radius:5px;'>\n"
                    for line in diff:
                        if line.startswith("+ "):
                            diff_html += f"<span style='background-color:rgba(46,139,87,0.2);display:block;'>{line}</span>\n"
                        elif line.startswith("- "):
                            diff_html += f"<span style='background-color:rgba(178,34,34,0.2);display:block;'>{line}</span>\n"
                        elif line.startswith("? "):
                            diff_html += f"<span style='color:#888;font-size:0.9em;display:block;'>{line}</span>\n"
                        else:
                            diff_html += f"{line}\n"
                    diff_html += "</pre>"

                    st.markdown(diff_html, unsafe_allow_html=True)
                    st.caption("Legend: + Added, - Removed, ? Position markers")
                except Exception as e:
                    st.error(f"Could not generate differences view: {str(e)}")

            # Display hallucination impact if available
            if (
                hasattr(capsule, "hallucination_impact")
                and capsule.hallucination_impact
            ):
                st.subheader("Impact Analysis")

                if isinstance(capsule.hallucination_impact, dict):
                    # Structured impact information
                    impact_areas = capsule.hallucination_impact.get("areas", [])
                    impact_severity = capsule.hallucination_impact.get(
                        "severity", "Medium"
                    )
                    impact_description = capsule.hallucination_impact.get(
                        "description", ""
                    )

                    # Determine color based on severity
                    severity_color = {
                        "Critical": "#800000",  # Maroon
                        "High": "#b22222",  # Fire Brick
                        "Medium": "#ff8c00",  # Dark Orange
                        "Low": "#2e8b57",  # Sea Green
                    }.get(impact_severity, "#ff8c00")

                    # Display impact summary
                    st.markdown(
                        f"""
                    <div style="padding:15px;border-radius:5px;background-color:rgba{tuple(int(severity_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)};">
                        <div style="display:flex;align-items:center;margin-bottom:10px;">
                            <div style="font-weight:bold;font-size:1.1em;">Impact Severity:</div>
                            <div style="margin-left:10px;color:{severity_color};font-weight:bold;">{impact_severity}</div>
                        </div>
                        <div>{impact_description}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Display impact areas as tags
                    if impact_areas:
                        st.markdown("#### Affected Areas")
                        tags_html = "<div style='display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;'>"

                        for area in impact_areas:
                            tags_html += f"""
                            <div style="padding:5px 10px;background-color:rgba(153,50,204,0.1);border-radius:15px;font-size:0.9em;">
                                {area}
                            </div>
                            """

                        tags_html += "</div>"
                        st.markdown(tags_html, unsafe_allow_html=True)
                else:
                    # Simple string description
                    st.markdown(
                        f"""
                    <div style="padding:10px;background-color:rgba(153,50,204,0.05);border-radius:5px;">
                        {str(capsule.hallucination_impact)}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        with tabs[2]:
            # Enhanced detection method display
            if hasattr(capsule, "detection_method") and capsule.detection_method:
                st.subheader("Detection Method")

                # Add styled box for detection method
                st.markdown(
                    f"""
                <div style="background-color:rgba(153,50,204,0.05);padding:15px;border-radius:5px;">
                    {capsule.detection_method}
                </div>
                """,
                    unsafe_allow_html=True,
                )

            # Enhanced hallucination markers visualization
            if (
                hasattr(capsule, "self_hallucination_markers")
                and capsule.self_hallucination_markers
            ):
                st.subheader("Hallucination Markers")

                # Check if we have structured markers
                structured_markers = (
                    all(
                        isinstance(marker, dict)
                        for marker in capsule.self_hallucination_markers
                    )
                    if isinstance(capsule.self_hallucination_markers, list)
                    else False
                )

                if structured_markers:
                    # Create interactive cards for each marker
                    for i, marker in enumerate(capsule.self_hallucination_markers):
                        # Create card with marker information
                        marker_type = marker.get("type", "General")
                        marker_desc = marker.get("description", "")
                        marker_confidence = marker.get("confidence", None)
                        marker_location = marker.get("location", "")

                        # Attempt to determine severity from confidence or explicitly stated severity
                        marker_severity = marker.get("severity", "Medium")
                        if marker_confidence is not None:
                            try:
                                conf_val = float(marker_confidence)
                                if conf_val >= 0.7:
                                    marker_severity = "High"
                                elif conf_val <= 0.3:
                                    marker_severity = "Low"
                                # else keep as Medium
                            except:
                                pass  # Keep default severity

                        # Set color based on severity
                        severity_color = {
                            "High": "#b22222",  # Fire Brick
                            "Medium": "#ff8c00",  # Dark Orange
                            "Low": "#2e8b57",  # Sea Green
                        }.get(
                            marker_severity, "#ff8c00"
                        )  # Default to orange for Medium

                        # Create an expandable card for each marker
                        with st.expander(
                            f"{marker_type}: {marker_desc[:50] + '...' if len(marker_desc) > 50 else marker_desc}",
                            expanded=i == 0,
                        ):
                            # Marker header with type and severity
                            st.markdown(
                                f"""
                            <div style="display:flex;align-items:center;margin-bottom:10px;">
                                <div style="font-weight:bold;font-size:1.1em;">{marker_type}</div>
                                <div style="margin-left:auto;background-color:{severity_color};color:white;padding:3px 8px;border-radius:10px;font-size:0.8em;">
                                    {marker_severity} Severity
                                </div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # Marker description
                            if marker_desc:
                                st.markdown(marker_desc)

                            # Location if available
                            if marker_location:
                                st.markdown(f"**Location:** {marker_location}")

                            # Confidence if available
                            if marker_confidence is not None:
                                try:
                                    conf_val = float(marker_confidence)
                                    if 0 <= conf_val <= 1:
                                        st.markdown(f"**Confidence:** {conf_val:.2f}")
                                        st.progress(conf_val)
                                    else:
                                        st.markdown(
                                            f"**Confidence:** {marker_confidence}"
                                        )
                                except:
                                    st.markdown(f"**Confidence:** {marker_confidence}")

                            # Other attributes
                            for k, v in marker.items():
                                if k not in [
                                    "type",
                                    "description",
                                    "confidence",
                                    "location",
                                    "severity",
                                ]:
                                    st.markdown(
                                        f"**{k.replace('_', ' ').title()}:** {v}"
                                    )
                else:
                    # Simple list display for non-structured markers
                    for i, marker in enumerate(capsule.self_hallucination_markers):
                        st.markdown(
                            f"""
                        <div style="margin-bottom:10px;padding:10px;background-color:rgba(153,50,204,0.05);border-left:4px solid {UATP7_CAPSULE_TYPE_COLORS.get('SelfHallucination', '#9932cc')}">
                            <div style="font-weight:bold;">Marker {i+1}</div>
                            <div>{str(marker)}</div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

            # Display additional metadata if available
            if hasattr(capsule, "metadata") and capsule.metadata:
                st.subheader("Additional Metadata")

                if isinstance(capsule.metadata, dict):
                    # Display as key-value pairs
                    cols = st.columns(2)
                    for i, (key, value) in enumerate(capsule.metadata.items()):
                        with cols[i % 2]:
                            st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
                else:
                    # Display as-is
                    st.json(capsule.metadata)


def render_consent_content(capsule: ConsentCapsule):
    """Render specialized content for Consent capsules with enhanced multi-tab visualizations."""

    # Create tabs for different aspects of consent visualization
    tab1, tab2, tab3 = st.tabs(
        ["Consent Summary", "Details & Conditions", "Verification & Status"]
    )

    #############################
    # Tab 1: Consent Summary
    #############################
    with tab1:
        st.subheader("Consent Overview")

        # Top banner with consent provider and type
        if hasattr(capsule, "consent_provider") and capsule.consent_provider:
            provider_name = capsule.consent_provider

            # Create header with forest green accent
            st.markdown(
                f"<h3 style='margin-bottom:0;'>Consent Provider: {provider_name}</h3>",
                unsafe_allow_html=True,
            )

        # Show a visual status indicator
        col1, col2 = st.columns([2, 1])

        with col1:
            if hasattr(capsule, "consent_scope") and capsule.consent_scope:
                st.markdown(f"**Scope:** {capsule.consent_scope}")

            # Check if consent has expired based on duration
            is_valid = True
            expiry_message = ""
            if (
                hasattr(capsule, "consent_duration")
                and capsule.consent_duration
                and hasattr(capsule, "timestamp")
            ):
                try:
                    duration_str = capsule.consent_duration
                    # Parse ISO 8601 duration
                    duration = iso8601.parse_duration(duration_str)
                    creation_time = parse_datetime(str(capsule.timestamp))
                    expiry_time = creation_time + duration
                    current_time = datetime.now().replace(tzinfo=expiry_time.tzinfo)

                    # Check if consent has expired
                    if current_time > expiry_time:
                        is_valid = False
                        expiry_message = (
                            f"Expired on {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                    else:
                        days_left = (expiry_time - current_time).days
                        hours_left = (expiry_time - current_time).seconds // 3600
                        expiry_message = (
                            f"Expires in {days_left} days, {hours_left} hours"
                        )
                except Exception:
                    expiry_message = "Could not determine expiration"

        with col2:
            # Create visual status indicator
            if is_valid:
                st.markdown(
                    "<div style='background-color:#228b22;color:white;padding:10px;border-radius:5px;text-align:center;'>"
                    "<strong>ACTIVE</strong><br/>"
                    f"{expiry_message}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div style='background-color:#b22222;color:white;padding:10px;border-radius:5px;text-align:center;'>"
                    "<strong>EXPIRED</strong><br/>"
                    f"{expiry_message}</div>",
                    unsafe_allow_html=True,
                )

        # Revocable status
        revocable = getattr(capsule, "revocable", False)
        st.markdown(f"**Revocable:** {'Yes' if revocable else 'No'}")

        # Show timeline if we have timestamps
        if hasattr(capsule, "timestamp"):
            st.markdown("### Consent Timeline")
            try:
                # Create a timeline visualization
                timeline_data = {
                    "Event": ["Consent Created"],
                    "Date": [
                        parse_datetime(str(capsule.timestamp)).strftime("%Y-%m-%d")
                    ],
                    "Time": [
                        parse_datetime(str(capsule.timestamp)).strftime("%H:%M:%S")
                    ],
                }

                # Add expiration if available
                if hasattr(capsule, "consent_duration") and capsule.consent_duration:
                    try:
                        duration = iso8601.parse_duration(capsule.consent_duration)
                        expiry_time = parse_datetime(str(capsule.timestamp)) + duration
                        timeline_data["Event"].append("Consent Expiration")
                        timeline_data["Date"].append(expiry_time.strftime("%Y-%m-%d"))
                        timeline_data["Time"].append(expiry_time.strftime("%H:%M:%S"))
                    except:
                        pass

                # Add verification events if in the consent_details
                if (
                    hasattr(capsule, "consent_details")
                    and isinstance(capsule.consent_details, dict)
                    and "verification_events" in capsule.consent_details
                ):
                    for event in capsule.consent_details["verification_events"]:
                        if "timestamp" in event and "event_type" in event:
                            try:
                                event_time = parse_datetime(event["timestamp"])
                                timeline_data["Event"].append(event["event_type"])
                                timeline_data["Date"].append(
                                    event_time.strftime("%Y-%m-%d")
                                )
                                timeline_data["Time"].append(
                                    event_time.strftime("%H:%M:%S")
                                )
                            except:
                                pass

                # Display timeline as a table
                st.table(timeline_data)
            except Exception as e:
                st.warning(f"Could not render timeline: {e}")

        # Display any notes or important information
        if (
            hasattr(capsule, "consent_details")
            and isinstance(capsule.consent_details, dict)
            and "notes" in capsule.consent_details
        ):
            st.info(capsule.consent_details["notes"])

    #############################
    # Tab 2: Details & Conditions
    #############################
    with tab2:
        st.subheader("Consent Details & Conditions")

        # Display conditions as interactive checklist
        if hasattr(capsule, "conditions") and capsule.conditions:
            st.markdown("### Conditions")
            for i, condition in enumerate(capsule.conditions):
                st.checkbox(condition, value=True, key=f"cond_{i}", disabled=True)

        # Show consent duration with visual representation
        if hasattr(capsule, "consent_duration") and capsule.consent_duration:
            st.markdown("### Duration")
            try:
                duration_str = capsule.consent_duration
                # Parse ISO 8601 duration
                duration = iso8601.parse_duration(duration_str)

                # Convert to days, hours, minutes for display
                total_seconds = duration.total_seconds()
                days = int(total_seconds // (24 * 3600))
                hours = int((total_seconds % (24 * 3600)) // 3600)
                minutes = int((total_seconds % 3600) // 60)

                # Create human-readable duration
                duration_parts = []
                if days > 0:
                    duration_parts.append(f"{days} days")
                if hours > 0:
                    duration_parts.append(f"{hours} hours")
                if minutes > 0:
                    duration_parts.append(f"{minutes} minutes")
                duration_text = (
                    ", ".join(duration_parts) if duration_parts else "Immediate"
                )

                st.markdown(f"**Duration:** {duration_text} ({duration_str})")

                # Create a visual bar for the duration
                if days > 0:
                    # If duration is significant, show a bar chart
                    fig, ax = plt.subplots(figsize=(10, 2))
                    ax.barh([0], [days], color="#228b22", alpha=0.7)
                    ax.set_yticks([])
                    ax.set_xlabel("Days")
                    ax.set_title("Consent Duration")
                    st.pyplot(fig)
                else:
                    # For short durations, just show as text
                    st.markdown(
                        f"<div style='background-color:#e6ffe6;padding:10px;border-radius:5px;'>"
                        f"Short-term consent: {duration_text}</div>",
                        unsafe_allow_html=True,
                    )
            except Exception as e:
                st.warning(f"Could not parse duration: {e}")

        # Display full consent details as JSON
        if hasattr(capsule, "consent_details") and capsule.consent_details:
            with st.expander("Full Consent Details", expanded=False):
                st.json(capsule.consent_details)

        # Display all consent metadata
        st.markdown("### Related Information")

        # Show related entities, resources, or context
        if hasattr(capsule, "consent_details") and isinstance(
            capsule.consent_details, dict
        ):
            # Display related entities if present
            if "related_entities" in capsule.consent_details:
                st.markdown("#### Related Entities")
                entities = capsule.consent_details["related_entities"]
                if isinstance(entities, list):
                    for entity in entities:
                        st.markdown(f"- {entity}")
                else:
                    st.json(entities)

            # Display affected resources if present
            if "affected_resources" in capsule.consent_details:
                st.markdown("#### Affected Resources")
                resources = capsule.consent_details["affected_resources"]
                if isinstance(resources, list):
                    for resource in resources:
                        st.markdown(f"- {resource}")
                else:
                    st.json(resources)

    #############################
    # Tab 3: Verification & Status
    #############################
    with tab3:
        st.subheader("Verification & Status")

        # Display verification method
        if (
            hasattr(capsule, "consent_verification_method")
            and capsule.consent_verification_method
        ):
            st.markdown("### Verification Method")
            method = capsule.consent_verification_method

            # Create a badge based on verification type
            if "digital signature" in method.lower():
                st.markdown(
                    "<span style='background-color:#4169e1;color:white;padding:5px 10px;border-radius:15px;'>"
                    " Digital Signature</span>",
                    unsafe_allow_html=True,
                )
            elif "biometric" in method.lower():
                st.markdown(
                    "<span style='background-color:#9932cc;color:white;padding:5px 10px;border-radius:15px;'>"
                    "️ Biometric</span>",
                    unsafe_allow_html=True,
                )
            elif "multi-factor" in method.lower():
                st.markdown(
                    "<span style='background-color:#228b22;color:white;padding:5px 10px;border-radius:15px;'>"
                    " Multi-Factor</span>",
                    unsafe_allow_html=True,
                )
            elif "verbal" in method.lower():
                st.markdown(
                    "<span style='background-color:#daa520;color:white;padding:5px 10px;border-radius:15px;'>"
                    " Verbal</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<span style='background-color:#708090;color:white;padding:5px 10px;border-radius:15px;'>"
                    f" {method}</span>",
                    unsafe_allow_html=True,
                )

            # Additional explanation of the verification method
            st.markdown(f"*{method}*")

        # Revocation mechanism
        if hasattr(capsule, "revocable") and capsule.revocable:
            st.markdown("### Revocation Mechanism")

            # Check if we have specific revocation details
            revocation_details = None
            if (
                hasattr(capsule, "consent_details")
                and isinstance(capsule.consent_details, dict)
                and "revocation_mechanism" in capsule.consent_details
            ):
                revocation_details = capsule.consent_details["revocation_mechanism"]

            if revocation_details:
                # Display structured revocation details
                if isinstance(revocation_details, dict):
                    col1, col2 = st.columns(2)

                    with col1:
                        if "method" in revocation_details:
                            st.markdown(f"**Method:** {revocation_details['method']}")
                        if "contact" in revocation_details:
                            st.markdown(f"**Contact:** {revocation_details['contact']}")

                    with col2:
                        if "time_limit" in revocation_details:
                            st.markdown(
                                f"**Time Limit:** {revocation_details['time_limit']}"
                            )
                        if "conditions" in revocation_details and isinstance(
                            revocation_details["conditions"], list
                        ):
                            st.markdown("**Conditions:**")
                            for condition in revocation_details["conditions"]:
                                st.markdown(f"- {condition}")
                else:
                    st.markdown(revocation_details)

                # Add a mock revocation interface for demonstration
                with st.expander("Revoke Consent (Demo)"):
                    st.warning(
                        "[WARN] This is a demonstration interface and does not perform actual revocation."
                    )
                    reason = st.selectbox(
                        "Reason for revocation",
                        [
                            "Please select a reason",
                            "No longer needed",
                            "Changed my mind",
                            "Terms violation",
                            "Other",
                        ],
                    )

                    if reason == "Other":
                        st.text_area("Please specify", "")

                    if st.button("Revoke Consent", disabled=True):
                        pass  # This is just a demo, button is disabled
            else:
                st.info("Consent can be revoked, but no specific mechanism is defined.")

        # Display cryptographic verification if available
        if hasattr(capsule, "signature") and capsule.signature:
            with st.expander("Cryptographic Verification"):
                st.markdown("### Digital Signature")
                st.code(capsule.signature, language=None)

                # Display verification timestamp if available
                if hasattr(capsule, "timestamp"):
                    st.markdown(f"**Signed on:** {capsule.timestamp}")

                # Add verification status indicator
                st.markdown(
                    "<div style='background-color:#228b22;color:white;padding:5px 15px;border-radius:5px;display:inline-block;'>"
                    " Signature Valid</div>",
                    unsafe_allow_html=True,
                )


def render_trust_renewal_content(capsule: TrustRenewalCapsule):
    """Render specialized content for Trust Renewal capsules with enhanced multi-tab visualizations."""

    # Create tabs for different aspects of trust renewal visualization
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Trust Overview",
            "Trust Metrics",
            "Verification Details",
            "History & Timeline",
        ]
    )

    #############################
    # Tab 1: Trust Overview
    #############################
    with tab1:
        st.subheader("Trust Renewal Summary")

        # Create a visual header with trust renewal type
        if hasattr(capsule, "renewal_type") and capsule.renewal_type:
            renewal_type = capsule.renewal_type
            color = UATP7_CAPSULE_TYPE_COLORS.get("TrustRenewal", "#4682b4")

            st.markdown(
                f"<div style='background-color:{color};padding:10px;border-radius:5px;color:white;'>"
                f"<h3 style='margin:0;'>Trust Renewal Type: {renewal_type}</h3></div>",
                unsafe_allow_html=True,
            )

        # Overall trust score calculation if possible
        if hasattr(capsule, "trust_metrics") and capsule.trust_metrics:
            if (
                isinstance(capsule.trust_metrics, dict)
                and len(capsule.trust_metrics) > 0
            ):
                try:
                    overall_score = sum(
                        float(v) for v in capsule.trust_metrics.values()
                    ) / len(capsule.trust_metrics)

                    # Create a visual meter for the trust score
                    st.markdown("### Overall Trust Score")
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        # Show the numeric score with color coding
                        score_color = "#ff0000"  # Red for low
                        if overall_score >= 0.7:
                            score_color = "#008000"  # Green for high
                        elif overall_score >= 0.4:
                            score_color = "#ffa500"  # Orange for medium

                        st.markdown(
                            f"<h1 style='color:{score_color};text-align:center;'>{overall_score:.2f}</h1>",
                            unsafe_allow_html=True,
                        )

                    with col2:
                        # Create a simple progress bar
                        st.progress(overall_score)

                        # Add a text description
                        if overall_score >= 0.7:
                            st.success("High trust level - renewal recommended")
                        elif overall_score >= 0.4:
                            st.warning("Medium trust level - review recommended")
                        else:
                            st.error("Low trust level - renewal requires justification")
                except Exception as e:
                    st.warning(f"Could not calculate overall trust score: {e}")

        # Show the renewal period
        if hasattr(capsule, "renewal_period") and capsule.renewal_period:
            st.markdown("### Renewal Period")
            period = capsule.renewal_period

            try:
                # Try to parse as ISO 8601 duration
                duration = iso8601.parse_duration(period)
                days = duration.days
                hours = duration.seconds // 3600

                # Show as a human-readable duration
                period_text = []
                if days > 0:
                    period_text.append(f"{days} days")
                if hours > 0:
                    period_text.append(f"{hours} hours")

                period_str = ", ".join(period_text) if period_text else "Immediate"
                st.info(f"Trust renewed for: {period_str}")

                # If we have a timestamp, calculate and show expiration date
                if hasattr(capsule, "timestamp"):
                    try:
                        issued_time = parse_datetime(str(capsule.timestamp))
                        expiry_time = issued_time + duration

                        # Calculate time remaining
                        now = datetime.now(expiry_time.tzinfo)
                        if now < expiry_time:
                            days_left = (expiry_time - now).days
                            hours_left = (expiry_time - now).seconds // 3600
                            st.success(
                                f"Expires in {days_left} days, {hours_left} hours ({expiry_time.strftime('%Y-%m-%d %H:%M:%S')})"
                            )
                        else:
                            st.error(
                                f"Expired on {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}"
                            )
                    except Exception:
                        pass
            except Exception:
                # Just display as is if not ISO 8601
                st.info(f"Trust renewed for period: {period}")

        # Display justification if available
        if hasattr(capsule, "renewal_justification") and capsule.renewal_justification:
            with st.expander("Renewal Justification", expanded=True):
                st.markdown(capsule.renewal_justification)

    #############################
    # Tab 2: Trust Metrics
    #############################
    with tab2:
        st.subheader("Detailed Trust Metrics")

        # Display trust metrics as charts and tables
        if hasattr(capsule, "trust_metrics") and capsule.trust_metrics:
            if (
                isinstance(capsule.trust_metrics, dict)
                and len(capsule.trust_metrics) > 0
            ):
                # Format metrics for visualization
                metrics = {}
                for metric, value in capsule.trust_metrics.items():
                    try:
                        metrics[metric] = float(value)
                    except (ValueError, TypeError):
                        metrics[metric] = 0.0  # Default for non-numeric values

                # Create a horizontal bar chart using matplotlib
                if metrics:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    categories = list(metrics.keys())
                    values = list(metrics.values())

                    # Sort by value for better visualization
                    sorted_indices = sorted(range(len(values)), key=lambda i: values[i])
                    sorted_categories = [categories[i] for i in sorted_indices]
                    sorted_values = [values[i] for i in sorted_indices]

                    # Create colored bars based on values
                    colors = [
                        "#ff6666" if v < 0.4 else "#ffcc66" if v < 0.7 else "#66cc66"
                        for v in sorted_values
                    ]

                    bars = ax.barh(sorted_categories, sorted_values, color=colors)

                    # Add value labels to the right of bars
                    for bar in bars:
                        width = bar.get_width()
                        ax.text(
                            width + 0.01,
                            bar.get_y() + bar.get_height() / 2,
                            f"{width:.2f}",
                            va="center",
                        )

                    ax.set_xlim(0, 1.1)  # Set x limit to 0-1 with a bit of padding
                    ax.set_xlabel("Trust Score")
                    ax.set_title("Trust Metrics")
                    plt.tight_layout()
                    st.pyplot(fig)

                # Also show as a table with color coding
                st.markdown("### Trust Metrics Table")

                # Create DataFrame for display
                metrics_df = {
                    "Metric": list(metrics.keys()),
                    "Value": list(metrics.values()),
                }

                # Display as a styled table
                for i, (metric, value) in enumerate(
                    zip(metrics_df["Metric"], metrics_df["Value"])
                ):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"**{metric}**")
                    with col2:
                        color = (
                            "#ff6666"
                            if value < 0.4
                            else "#ffcc66"
                            if value < 0.7
                            else "#66cc66"
                        )
                        st.markdown(
                            f"<span style='background-color:{color};padding:2px 8px;border-radius:3px;'>"
                            f"{value:.2f}</span>",
                            unsafe_allow_html=True,
                        )
            else:
                st.warning("No valid trust metrics available")
                if capsule.trust_metrics:
                    st.json(capsule.trust_metrics)

        # Display renewal conditions if available
        if hasattr(capsule, "renewal_conditions") and capsule.renewal_conditions:
            st.markdown("### Renewal Conditions")
            conditions = capsule.renewal_conditions

            if isinstance(conditions, list):
                for i, condition in enumerate(conditions):
                    st.markdown(f"{i+1}. {condition}")
            elif isinstance(conditions, dict):
                for category, items in conditions.items():
                    st.markdown(f"**{category}**")
                    if isinstance(items, list):
                        for item in items:
                            st.markdown(f"- {item}")
                    else:
                        st.markdown(f"- {items}")
            else:
                st.json(conditions)

    #############################
    # Tab 3: Verification Details
    #############################
    with tab3:
        st.subheader("Verification Information")

        # Display verification method with a visual indicator
        if hasattr(capsule, "verification_method") and capsule.verification_method:
            method = capsule.verification_method

            # Create a badge based on verification method
            if "automated" in method.lower():
                badge_color = "#4682b4"  # Steel Blue
                badge_icon = ""
            elif "manual" in method.lower():
                badge_color = "#9370db"  # Medium Purple
                badge_icon = ""
            elif "hybrid" in method.lower():
                badge_color = "#20b2aa"  # Light Sea Green
                badge_icon = ""
            else:
                badge_color = "#708090"  # Slate Gray
                badge_icon = ""

            st.markdown(
                f"<div style='background-color:{badge_color};color:white;padding:10px;border-radius:5px;'>"
                f"{badge_icon} <b>Verification Method:</b> {method}</div>",
                unsafe_allow_html=True,
            )

        # Display verification results in detail
        if hasattr(capsule, "verification_results") and capsule.verification_results:
            st.markdown("### Verification Results")
            results = capsule.verification_results

            if isinstance(results, dict):
                # Group results by status for better organization
                passed = {
                    k: v
                    for k, v in results.items()
                    if isinstance(v, (dict, str))
                    and "status" in v
                    and v["status"].lower() == "passed"
                }
                failed = {
                    k: v
                    for k, v in results.items()
                    if isinstance(v, (dict, str))
                    and "status" in v
                    and v["status"].lower() == "failed"
                }
                other = {
                    k: v
                    for k, v in results.items()
                    if k not in passed and k not in failed
                }

                # Display passed verifications
                if passed:
                    st.markdown("#### [OK] Passed Verifications")
                    for check, details in passed.items():
                        with st.expander(check):
                            if isinstance(details, dict):
                                for key, value in details.items():
                                    if key != "status":
                                        st.markdown(f"**{key}:** {value}")
                            else:
                                st.markdown(str(details))

                # Display failed verifications
                if failed:
                    st.markdown("#### [ERROR] Failed Verifications")
                    for check, details in failed.items():
                        with st.expander(check):
                            if isinstance(details, dict):
                                for key, value in details.items():
                                    if key != "status":
                                        st.markdown(f"**{key}:** {value}")
                            else:
                                st.markdown(str(details))

                # Display other verifications
                if other:
                    st.markdown("#### ℹ️ Other Verification Details")
                    for check, details in other.items():
                        with st.expander(check):
                            if isinstance(details, dict):
                                st.json(details)
                            else:
                                st.markdown(str(details))
            else:
                # Fallback to JSON display if not a dict
                st.json(results)

        # Display verified claims
        if hasattr(capsule, "verified_claims") and capsule.verified_claims:
            st.markdown("### Verified Claims")

            claims = capsule.verified_claims
            if isinstance(claims, list):
                # Create a table view of claims if they are structured
                if all(isinstance(claim, dict) for claim in claims):
                    # Determine all unique keys across all claims
                    all_keys = set().union(*(claim.keys() for claim in claims))

                    # Create a dict for the table
                    claims_table = {}
                    for key in all_keys:
                        claims_table[key] = [claim.get(key, "") for claim in claims]

                    # Display as a table
                    if claims_table:
                        # If there's status info, color-code the table
                        if "status" in claims_table:
                            rows = []
                            for i in range(len(claims_table["status"])):
                                row = {k: claims_table[k][i] for k in all_keys}
                                rows.append(row)

                            for row in rows:
                                status = row.get("status", "").lower()
                                color = (
                                    "#e6ffe6"
                                    if "pass" in status
                                    or "true" in status
                                    or "valid" in status
                                    else "#ffe6e6"
                                    if "fail" in status
                                    or "false" in status
                                    or "invalid" in status
                                    else "#f0f0f0"
                                )

                                st.markdown(
                                    f"<div style='background-color:{color};padding:10px;margin:5px 0;border-radius:5px;'>",
                                    unsafe_allow_html=True,
                                )
                                for key, value in row.items():
                                    st.markdown(f"**{key}:** {value}")
                                st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            # Just show as a regular table
                            st.dataframe(claims_table)
                else:
                    # Just list the claims
                    for i, claim in enumerate(claims):
                        st.markdown(f"{i+1}. {claim}")
            else:
                # Fallback to JSON display
                st.json(claims)

    #############################
    # Tab 4: History & Timeline
    #############################
    with tab4:
        st.subheader("Trust History & Timeline")

        # Show previous trust capsule reference
        if (
            hasattr(capsule, "previous_trust_capsule_id")
            and capsule.previous_trust_capsule_id
        ):
            st.markdown("### Previous Trust Capsule")
            prev_id = capsule.previous_trust_capsule_id

            # Display with a visual link icon
            st.markdown(
                f"<div style='background-color:#f0f0f0;padding:10px;border-radius:5px;'>"
                f" <b>ID:</b> {prev_id}</div>",
                unsafe_allow_html=True,
            )

            # Add a button to simulate navigation to previous capsule
            if st.button("View Previous Trust Capsule", key="prev_capsule"):
                st.info(
                    "This is a demonstration button. In a real application, this would navigate to the previous trust capsule."
                )

        # Create a timeline visualization
        st.markdown("### Trust Timeline")

        # Generate timeline events from available data
        timeline_data = {"Event": [], "Date": [], "Description": []}

        # Add creation of current capsule
        if hasattr(capsule, "timestamp"):
            try:
                creation_time = parse_datetime(str(capsule.timestamp))
                timeline_data["Event"].append("Current Trust Renewal")
                timeline_data["Date"].append(
                    creation_time.strftime("%Y-%m-%d %H:%M:%S")
                )
                timeline_data["Description"].append(
                    f"Type: {getattr(capsule, 'renewal_type', 'Unknown')}"
                )
            except:
                pass

        # Add verification events if available in verification_results
        if hasattr(capsule, "verification_results") and isinstance(
            capsule.verification_results, dict
        ):
            for check, result in capsule.verification_results.items():
                if isinstance(result, dict) and "timestamp" in result:
                    try:
                        event_time = parse_datetime(str(result["timestamp"]))
                        status = result.get("status", "Unknown")
                        timeline_data["Event"].append(f"Verification: {check}")
                        timeline_data["Date"].append(
                            event_time.strftime("%Y-%m-%d %H:%M:%S")
                        )
                        timeline_data["Description"].append(f"Status: {status}")
                    except:
                        pass

        # Add expiration event if we can calculate it
        if hasattr(capsule, "timestamp") and hasattr(capsule, "renewal_period"):
            try:
                creation_time = parse_datetime(str(capsule.timestamp))
                duration = iso8601.parse_duration(capsule.renewal_period)
                expiry_time = creation_time + duration

                timeline_data["Event"].append("Trust Expiration")
                timeline_data["Date"].append(expiry_time.strftime("%Y-%m-%d %H:%M:%S"))
                timeline_data["Description"].append(
                    "Scheduled expiration of trust renewal"
                )
            except:
                pass

        # Sort timeline by date
        if timeline_data["Date"]:
            # Create a list of tuples (event, date, description)
            timeline_items = list(
                zip(
                    timeline_data["Event"],
                    timeline_data["Date"],
                    timeline_data["Description"],
                )
            )

            # Sort by date
            try:
                sorted_items = sorted(timeline_items, key=lambda x: x[1])

                # Unpack sorted items back into timeline_data
                timeline_data["Event"] = [item[0] for item in sorted_items]
                timeline_data["Date"] = [item[1] for item in sorted_items]
                timeline_data["Description"] = [item[2] for item in sorted_items]
            except:
                pass

        # Display timeline as a table with visual styling
        if timeline_data["Event"]:
            for i in range(len(timeline_data["Event"])):
                # Create a colored event card
                is_current = "Current" in timeline_data["Event"][i]
                is_expiration = "Expiration" in timeline_data["Event"][i]

                if is_current:
                    card_color = "#4682b4"  # Steel Blue
                    icon = ""
                elif is_expiration:
                    card_color = "#ff8c00"  # Dark Orange
                    icon = ""
                else:
                    card_color = "#708090"  # Slate Gray
                    icon = ""

                st.markdown(
                    f"<div style='border-left:4px solid {card_color};padding-left:15px;margin:15px 0;'>"
                    f"<h4>{icon} {timeline_data['Event'][i]}</h4>"
                    f"<p><b>Date:</b> {timeline_data['Date'][i]}</p>"
                    f"<p>{timeline_data['Description'][i]}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No timeline data available")


def render_capsule_expiration_content(capsule: CapsuleExpirationCapsule):
    """Render specialized content for Capsule Expiration capsules."""
    with st.expander("Expiration Details", expanded=True):
        if hasattr(capsule, "target_capsule_ids") and capsule.target_capsule_ids:
            st.subheader("Target Capsules")
            for target_id in capsule.target_capsule_ids:
                st.code(target_id, language=None)

        if hasattr(capsule, "expiration_type") and capsule.expiration_type:
            st.markdown(f"**Expiration Type:** {capsule.expiration_type}")

        if hasattr(capsule, "expiration_reason") and capsule.expiration_reason:
            st.markdown("**Expiration Reason:**")
            st.markdown(capsule.expiration_reason)

        if (
            hasattr(capsule, "replacement_capsule_ids")
            and capsule.replacement_capsule_ids
        ):
            st.subheader("Replacement Capsules")
            for replacement_id in capsule.replacement_capsule_ids:
                st.code(replacement_id, language=None)

        if hasattr(capsule, "expiration_effect") and capsule.expiration_effect:
            st.subheader("Expiration Effect")
            st.json(capsule.expiration_effect)


def render_governance_content(capsule: GovernanceCapsule):
    """Render specialized content for Governance capsules with enhanced visualization."""
    with st.expander("Governance Details", expanded=True):
        # Add a colorful header with badge
        st.markdown(
            f"""
    <div style="display:flex;align-items:center;padding:10px;margin-bottom:20px;background:linear-gradient(90deg, {UATP7_CAPSULE_TYPE_COLORS.get('Governance', '#4682b4')}22, transparent);border-radius:5px;">
        <div style="background-color:{UATP7_CAPSULE_TYPE_COLORS.get('Governance', '#4682b4')};color:white;padding:5px 10px;border-radius:5px;margin-right:15px;font-weight:bold;">
            Governance
        </div>
        <div style="flex-grow:1;">
            <div style="font-size:1.2em;font-weight:bold;color:{UATP7_CAPSULE_TYPE_COLORS.get('Governance', '#4682b4')};">
                Governance Capsule
            </div>
            <div style="color:#555;font-size:0.9em;">
                UATP 7.0 Protocol Policy & Decision Records
            </div>
        </div>
    </div>
    """,
            unsafe_allow_html=True,
        )

    if hasattr(capsule, "governance_action"):
        # Create tabs for organized display
        tabs = st.tabs(
            ["Overview", "Policy & Action", "Stakeholder Votes", "Implementation"]
        )

        # Process governance action information
        action = capsule.governance_action
        approval_rate = None
        approval_level = ""

        # Calculate approval rate if we have votes
        if (
            hasattr(capsule, "stakeholder_votes")
            and capsule.stakeholder_votes
            and isinstance(capsule.stakeholder_votes, dict)
        ):
            vote_values = []
            for vote in capsule.stakeholder_votes.values():
                # Handle different vote formats
                if isinstance(vote, (int, float)):
                    vote_values.append(float(vote))
                elif isinstance(vote, dict) and "vote" in vote:
                    vote_values.append(float(vote["vote"]))
                elif isinstance(vote, str):
                    # Convert string votes to numeric
                    if vote.lower() in [
                        "approve",
                        "yes",
                        "approved",
                        "support",
                        "true",
                    ]:
                        vote_values.append(1.0)
                    elif vote.lower() in [
                        "disapprove",
                        "no",
                        "rejected",
                        "against",
                        "false",
                    ]:
                        vote_values.append(0.0)
                    else:
                        vote_values.append(0.5)  # Neutral for other strings

            if vote_values:
                approval_rate = (sum(vote_values) / len(vote_values)) * 100

                # Determine approval level based on percentage
                if approval_rate >= 75:
                    approval_level = "(Strong Approval)"
                elif approval_rate >= 50:
                    approval_level = "(Approval)"
                elif approval_rate >= 25:
                    approval_level = "(Contested)"
                else:
                    approval_level = "(Rejected)"

        # Determine action type based on keywords
        action_type = "Standard"
        action_icon = ""
        action_color = "#4682b4"  # Default blue

        # Categorize action type based on keywords
        lower_action = action.lower()
        if any(
            keyword in lower_action
            for keyword in ["emergency", "critical", "urgent", "immediate"]
        ):
            action_type = "Emergency"
            action_icon = ""
            action_color = "#b22222"  # Fire Brick
        elif any(
            keyword in lower_action
            for keyword in ["update", "modify", "change", "revise"]
        ):
            action_type = "Update"
            action_icon = ""
            action_color = "#ff8c00"  # Dark Orange
        elif any(
            keyword in lower_action for keyword in ["add", "create", "establish", "new"]
        ):
            action_type = "Creation"
            action_icon = "+"
            action_color = "#2e8b57"  # Sea Green
        elif any(
            keyword in lower_action
            for keyword in ["remove", "delete", "deprecate", "disable"]
        ):
            action_type = "Removal"
            action_icon = "️"
            action_color = "#800080"  # Purple

        # Calculate gradient background for action
        action_color_rgba = f"rgba{tuple(int(action_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)}"

        # Overview Tab
        with tabs[0]:
            # Display a summary card
            st.markdown(
                f"""
            <div style="padding:15px;background-color:rgba(70,130,180,0.05);border-radius:5px;margin-bottom:20px;">
                <div style="font-weight:bold;margin-bottom:10px;font-size:1.1em;">
                    Governance Summary
                </div>
                <div style="margin-bottom:5px;">
                    <strong>Governance Action:</strong> {capsule.governance_action}
                </div>
                <div style="margin-bottom:5px;">
                    <strong>Affected Entities:</strong> {len(capsule.affected_entities) if hasattr(capsule, 'affected_entities') and isinstance(capsule.affected_entities, list) else 'Unknown'}
                </div>
                <div>
                    <strong>Stakeholder Votes:</strong>
                    {f"{approval_rate:.1f}% {approval_level}" if approval_rate is not None else 'No votes recorded'}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Display basic information
            if hasattr(capsule, "governance_action") and capsule.governance_action:
                st.markdown(
                    f"""
                <div style="padding:10px;background-color:{action_color_rgba};border-radius:5px;margin-bottom:15px;display:flex;align-items:center;">
                    <div style="font-size:1.5em;margin-right:10px;">{action_icon}</div>
                    <div>
                        <div style="font-weight:bold;margin-bottom:5px;">{capsule.governance_action}</div>
                        <div style="font-size:0.9em;">
                            {str(capsule.action_details)}
                        </div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        # Policy & Action Tab
        with tabs[1]:
            # Display governance action details
            if hasattr(capsule, "governance_action") and capsule.governance_action:
                # Title with action type and styling
                st.markdown(
                    f"""
                <div style="background-color:{action_color_rgba};padding:15px;border-radius:5px;margin-bottom:20px;">
                    <div style="display:flex;align-items:center;margin-bottom:10px;">
                        <div style="font-size:1.5em;margin-right:10px;">{action_icon}</div>
                        <div style="font-weight:bold;font-size:1.2em;color:{action_color};">
                            {action_type} Policy Action
                        </div>
                    </div>
                    <div style="margin-bottom:15px;font-size:1.1em;">
                        {capsule.governance_action}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Display action details in a structured way
                if hasattr(capsule, "action_details"):
                    st.markdown("### Action Details")
                    try:
                        # Try to parse action details as a dictionary or structured data
                        if isinstance(capsule.action_details, dict):
                            # Create two columns for better layout
                            col1, col2 = st.columns(2)

                            details = capsule.action_details
                            with col1:
                                # Display policy details if available
                                if "policy" in details or "policy_details" in details:
                                    policy = details.get(
                                        "policy", details.get("policy_details", {})
                                    )
                                    st.markdown("#### Policy Information")
                                    if isinstance(policy, dict):
                                        for key, value in policy.items():
                                            st.markdown(
                                                f"**{key.replace('_', ' ').title()}:** {value}"
                                            )
                                    else:
                                        st.markdown(f"{policy}")

                                # Display rationale or justification if available
                                if "rationale" in details or "justification" in details:
                                    st.markdown("#### Rationale & Justification")
                                    rationale = details.get(
                                        "rationale", details.get("justification", "")
                                    )
                                    st.markdown(f"{rationale}")

                            with col2:
                                # Display scope or affected areas if available
                                if "scope" in details or "affected_areas" in details:
                                    st.markdown("#### Scope & Affected Areas")
                                    scope = details.get(
                                        "scope", details.get("affected_areas", [])
                                    )
                                    if isinstance(scope, list):
                                        for item in scope:
                                            st.markdown(f"- {item}")
                                    else:
                                        st.markdown(f"{scope}")

                                # Display timeline or schedule if available
                                if "timeline" in details or "schedule" in details:
                                    st.markdown("#### Timeline")
                                    timeline = details.get(
                                        "timeline", details.get("schedule", {})
                                    )
                                    if isinstance(timeline, dict):
                                        for date, event in timeline.items():
                                            st.markdown(f"**{date}:** {event}")
                                    elif isinstance(timeline, list):
                                        for item in timeline:
                                            if isinstance(item, dict):
                                                date = item.get("date", "")
                                                event = item.get(
                                                    "event", item.get("description", "")
                                                )
                                                st.markdown(f"**{date}:** {event}")
                                            else:
                                                st.markdown(f"- {item}")
                                    else:
                                        st.markdown(f"{timeline}")

                            # Display impact assessment if available
                            if "impact" in details or "impact_assessment" in details:
                                st.markdown("### Impact Assessment")
                                impact = details.get(
                                    "impact", details.get("impact_assessment", {})
                                )

                                if isinstance(impact, dict):
                                    impact_col1, impact_col2 = st.columns(2)
                                    items = list(impact.items())
                                    mid = len(items) // 2

                                    with impact_col1:
                                        for key, value in items[:mid]:
                                            st.markdown(
                                                f"**{key.replace('_', ' ').title()}:** {value}"
                                            )
                                    with impact_col2:
                                        for key, value in items[mid:]:
                                            st.markdown(
                                                f"**{key.replace('_', ' ').title()}:** {value}"
                                            )
                                else:
                                    st.markdown(f"{impact}")

                            # Show full details in JSON format
                            with st.expander("View Complete Action Details"):
                                st.json(details)

                        elif isinstance(capsule.action_details, str):
                            # Try to parse as JSON if it's a string
                            try:
                                details = json.loads(capsule.action_details)
                                st.json(details)
                            except json.JSONDecodeError:
                                st.markdown(capsule.action_details)
                        else:
                            # Display as string for other formats
                            st.markdown(str(capsule.action_details))
                    except Exception as e:
                        st.warning(f"Error parsing action details: {str(e)}")
                        st.text(str(capsule.action_details))

                # Display affected entities with better visualization
                if hasattr(capsule, "affected_entities") and capsule.affected_entities:
                    st.markdown("### Affected Entities")

                    if isinstance(capsule.affected_entities, list):
                        # Display entities in a clean, visual format
                        for i, entity in enumerate(capsule.affected_entities):
                            entity_name = entity
                            entity_details = {}

                            if isinstance(entity, dict):
                                entity_name = entity.get(
                                    "id", entity.get("name", f"Entity {i+1}")
                                )
                                entity_details = {
                                    k: v
                                    for k, v in entity.items()
                                    if k not in ["id", "name"]
                                }

                            # Create entity card with styling
                            st.markdown(
                                f"""
                            <div style="border:1px solid #ddd;border-radius:5px;padding:10px;margin-bottom:10px;">
                                <div style="font-weight:bold;color:{action_color};">{entity_name}</div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # Show entity details if available
                            if entity_details:
                                with st.expander(f"Details for {entity_name}"):
                                    for key, value in entity_details.items():
                                        st.markdown(
                                            f"**{key.replace('_', ' ').title()}:** {value}"
                                        )
                    else:
                        # Just display as text if not a list
                        st.text(str(capsule.affected_entities))

                # Display document references if available
                if (
                    hasattr(capsule, "document_references")
                    and capsule.document_references
                ):
                    st.markdown("### References & Documentation")

                    if isinstance(capsule.document_references, list):
                        for doc in capsule.document_references:
                            if isinstance(doc, dict):
                                doc_title = doc.get(
                                    "title", doc.get("name", "Document")
                                )
                                doc_url = doc.get("url", doc.get("link", None))
                                doc_desc = doc.get("description", "")

                                st.markdown(
                                    f"""
                                <div style="border:1px solid #ddd;border-radius:5px;padding:10px;margin-bottom:10px;background-color:#f9f9f9;">
                                    <div style="font-weight:bold;">{doc_title}</div>
                                    {f'<div><a href="{doc_url}" target="_blank">{doc_url}</a></div>' if doc_url else ''}
                                    {f'<div style="font-size:0.9em;color:#555;margin-top:5px;">{doc_desc}</div>' if doc_desc else ''}
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(f"- {doc}")
                    elif isinstance(capsule.document_references, dict):
                        for doc_title, doc_data in capsule.document_references.items():
                            if isinstance(doc_data, dict):
                                doc_url = doc_data.get(
                                    "url", doc_data.get("link", None)
                                )
                                doc_desc = doc_data.get("description", "")

                                st.markdown(
                                    f"""
                                <div style="border:1px solid #ddd;border-radius:5px;padding:10px;margin-bottom:10px;background-color:#f9f9f9;">
                                    <div style="font-weight:bold;">{doc_title}</div>
                                    {f'<div><a href="{doc_url}" target="_blank">{doc_url}</a></div>' if doc_url else ''}
                                    {f'<div style="font-size:0.9em;color:#555;margin-top:5px;">{doc_desc}</div>' if doc_desc else ''}
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(f"**{doc_title}:** {doc_data}")
                    else:
                        st.text(str(capsule.document_references))

        # Stakeholder Votes Tab
        with tabs[2]:
            if hasattr(capsule, "stakeholder_votes") and capsule.stakeholder_votes:
                # Calculate vote statistics
                votes = capsule.stakeholder_votes
                total_votes = len(votes) if isinstance(votes, dict) else 0

                if isinstance(votes, dict) and total_votes > 0:
                    # Standardize and collect vote data for visualization
                    vote_data = []
                    for stakeholder, vote_value in votes.items():
                        # Extract vote and metadata
                        numerical_vote = None
                        vote_metadata = {}
                        vote_label = ""

                        # Handle different vote formats
                        if isinstance(vote_value, (int, float)):
                            numerical_vote = float(vote_value)
                            vote_metadata = {"raw_vote": vote_value}
                        elif isinstance(vote_value, dict):
                            if "vote" in vote_value:
                                numerical_vote = float(vote_value["vote"])
                                vote_metadata = {
                                    k: v for k, v in vote_value.items() if k != "vote"
                                }
                        elif isinstance(vote_value, str):
                            # Convert string votes to numeric
                            if vote_value.lower() in [
                                "approve",
                                "yes",
                                "approved",
                                "support",
                                "true",
                            ]:
                                numerical_vote = 1.0
                                vote_label = vote_value
                            elif vote_value.lower() in [
                                "disapprove",
                                "no",
                                "rejected",
                                "against",
                                "false",
                            ]:
                                numerical_vote = 0.0
                                vote_label = vote_value
                            else:
                                numerical_vote = 0.5  # Neutral
                                vote_label = vote_value

                        # Determine vote category and color
                        if numerical_vote is not None:
                            if numerical_vote >= 0.7:
                                vote_category = "Approval"
                                vote_color = "#2e8b57"  # Green
                                vote_icon = "[OK]"
                            elif numerical_vote >= 0.4:
                                vote_category = "Neutral"
                                vote_color = "#ff8c00"  # Orange
                                vote_icon = "[WARN]"
                            else:
                                vote_category = "Disapproval"
                                vote_color = "#b22222"  # Red
                                vote_icon = "[ERROR]"

                            # Default label if none provided
                            if not vote_label:
                                vote_label = vote_category

                            # Add to vote data collection
                            vote_data.append(
                                {
                                    "stakeholder": stakeholder,
                                    "vote": numerical_vote,
                                    "vote_label": vote_label,
                                    "vote_category": vote_category,
                                    "vote_color": vote_color,
                                    "vote_icon": vote_icon,
                                    "metadata": vote_metadata,
                                }
                            )

                    # Calculate weighted approval percentage
                    if vote_data:
                        approval_sum = sum(v["vote"] for v in vote_data)
                        approval_percentage = (approval_sum / len(vote_data)) * 100

                        # Determine outcome
                        if approval_percentage >= 50:
                            outcome = "Approved"
                            outcome_color = "#2e8b57"  # Green
                        else:
                            outcome = "Rejected"
                            outcome_color = "#b22222"  # Red

                        # Display vote summary card
                        st.markdown(
                            f"""
                        <div style="background-color:rgba{tuple(int(outcome_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)};padding:15px;border-radius:5px;margin-bottom:20px;">
                            <div style="font-weight:bold;margin-bottom:10px;font-size:1.2em;">
                                Vote Outcome: <span style="color:{outcome_color};">{outcome}</span>
                            </div>
                            <div style="display:flex;align-items:center;margin-bottom:15px;">
                                <div style="font-size:1.8em;margin-right:15px;">
                                    {"[OK]" if outcome == "Approved" else "[ERROR]"}
                                </div>
                                <div>
                                    <div style="font-size:1.2em;font-weight:bold;">
                                        {approval_percentage:.1f}% Approval Rate
                                    </div>
                                    <div style="color:#555;">
                                        {total_votes} stakeholder{"s" if total_votes != 1 else ""} voted
                                    </div>
                                </div>
                            </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        # Calculate vote distribution
                        approvals = len(
                            [v for v in vote_data if v["vote_category"] == "Approval"]
                        )
                        neutrals = len(
                            [v for v in vote_data if v["vote_category"] == "Neutral"]
                        )
                        disapprovals = len(
                            [
                                v
                                for v in vote_data
                                if v["vote_category"] == "Disapproval"
                            ]
                        )

                        # Create a visual representation of the vote distribution
                        total = approvals + neutrals + disapprovals
                        approval_width = (approvals / total) * 100 if total > 0 else 0
                        neutral_width = (neutrals / total) * 100 if total > 0 else 0
                        disapproval_width = (
                            (disapprovals / total) * 100 if total > 0 else 0
                        )

                        # Display stacked bar
                        st.markdown(
                            f"""
                        <div style="margin-bottom:30px;">
                            <div style="font-weight:bold;margin-bottom:5px;">Vote Distribution</div>
                            <div style="display:flex;height:30px;border-radius:5px;overflow:hidden;">
                                <div style="width:{approval_width}%;background-color:#2e8b57;display:flex;justify-content:center;align-items:center;color:white;">
                                    {approvals}
                                </div>
                                <div style="width:{neutral_width}%;background-color:#ff8c00;display:flex;justify-content:center;align-items:center;color:white;">
                                    {neutrals}
                                </div>
                                <div style="width:{disapproval_width}%;background-color:#b22222;display:flex;justify-content:center;align-items:center;color:white;">
                                    {disapprovals}
                                </div>
                            </div>
                            <div style="display:flex;margin-top:5px;font-size:0.8em;">
                                <div style="flex:1;">Approvals</div>
                                <div style="flex:1;text-align:center;">Neutral</div>
                                <div style="flex:1;text-align:right;">Disapprovals</div>
                            </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        # Display individual votes in a table
                        st.markdown("### Individual Stakeholder Votes")

                        # Sort votes by strength (highest to lowest)
                        vote_data.sort(key=lambda x: x["vote"], reverse=True)

                        for vote in vote_data:
                            # Create vote strength bar
                            vote_strength = vote["vote"] * 100

                            # Calculate color gradient based on vote strength
                            vote_color = vote["vote_color"]

                            st.markdown(
                                f"""
                            <div style="border:1px solid #ddd;border-radius:5px;padding:10px;margin-bottom:10px;">
                                <div style="display:flex;align-items:center;margin-bottom:10px;">
                                    <div style="font-size:1.5em;margin-right:10px;">{vote["vote_icon"]}</div>
                                    <div style="flex-grow:1;">
                                        <div style="font-weight:bold;">{vote["stakeholder"]}</div>
                                        <div style="color:{vote_color};font-size:0.9em;">
                                            {vote["vote_label"]} ({vote["vote_category"]})
                                        </div>
                                    </div>
                                    <div style="font-weight:bold;color:{vote_color};">
                                        {vote["vote"]}
                                    </div>
                                </div>
                                <div style="background-color:#f0f0f0;border-radius:5px;height:10px;width:100%;overflow:hidden;">
                                    <div style="background-color:{vote_color};height:100%;width:{vote_strength}%;"></div>
                                </div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                            # Show metadata if available
                            if vote["metadata"] and len(vote["metadata"]) > 0:
                                with st.expander(
                                    f"Additional vote data from {vote['stakeholder']}"
                                ):
                                    st.json(vote["metadata"])

                # Display authorization proof if available
                if (
                    hasattr(capsule, "authorization_proof")
                    and capsule.authorization_proof
                ):
                    st.markdown("### Authorization Proof")
                    st.markdown(
                        """
                    <div style="border:1px solid #ddd;border-radius:5px;padding:15px;margin-bottom:20px;background-color:#f9f9f9;">
                        <div style="font-weight:bold;margin-bottom:10px;">Governance Vote Authorization</div>
                        <div style="font-size:0.9em;color:#555;margin-bottom:10px;">
                            Authorization proof for stakeholder vote validation and verification
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Display proof in JSON format
                    with st.expander("View Authorization Proof Details"):
                        if isinstance(capsule.authorization_proof, dict):
                            st.json(capsule.authorization_proof)
                        else:
                            st.text(str(capsule.authorization_proof))

            else:
                st.info(
                    "No stakeholder votes are recorded for this governance capsule."
                )
                st.markdown(
                    "Stakeholder votes provide transparency into the governance decision-making process and help establish the legitimacy of governance actions within the protocol."
                )

        # Implementation Tab
        with tabs[3]:
            # Check if implementation information exists
            has_implementation_data = (
                hasattr(capsule, "implementation_notes")
                or hasattr(capsule, "implementation_status")
                or hasattr(capsule, "implementation_timeline")
                or hasattr(capsule, "implementation_details")
            )

            if has_implementation_data:
                # Display implementation notes if available
                if (
                    hasattr(capsule, "implementation_notes")
                    and capsule.implementation_notes
                ):
                    st.markdown("### Implementation Notes")

                    # Create a styled card for the notes
                    notes = capsule.implementation_notes
                    notes_content = """
                    <div style="border:1px solid #ddd;border-radius:5px;padding:15px;margin-bottom:20px;background-color:#f9f9f9;">
                        <div style="font-weight:bold;margin-bottom:10px;">Implementation Plan</div>
                    """

                    # Handle different formats of notes
                    if isinstance(notes, dict):
                        # Try to extract and format structured notes
                        for key, value in notes.items():
                            notes_content += f"<div><strong>{key.replace('_', ' ').title()}:</strong> {value}</div>"
                    elif isinstance(notes, str):
                        # Try to parse as JSON if possible
                        try:
                            notes_dict = json.loads(notes)
                            if isinstance(notes_dict, dict):
                                for key, value in notes_dict.items():
                                    notes_content += f"<div><strong>{key.replace('_', ' ').title()}:</strong> {value}</div>"
                            else:
                                notes_content += f"<div>{notes}</div>"
                        except json.JSONDecodeError:
                            notes_content += f"<div>{notes}</div>"
                    else:
                        notes_content += f"<div>{str(notes)}</div>"

                    notes_content += "</div>"
                    st.markdown(notes_content, unsafe_allow_html=True)

                # Display implementation timeline if available
                if (
                    hasattr(capsule, "implementation_timeline")
                    and capsule.implementation_timeline
                ):
                    st.markdown("### Implementation Timeline")
                    timeline = capsule.implementation_timeline

                    if isinstance(timeline, list):
                        # Create a visual timeline
                        for i, milestone in enumerate(timeline):
                            milestone_date = ""
                            milestone_desc = ""
                            milestone_status = "pending"  # Default status
                            milestone_color = "#888888"  # Default gray color

                            if isinstance(milestone, dict):
                                milestone_date = milestone.get(
                                    "date", milestone.get("timestamp", "")
                                )
                                milestone_desc = milestone.get(
                                    "description", milestone.get("event", "")
                                )
                                milestone_status = milestone.get(
                                    "status", "pending"
                                ).lower()

                                # Set color based on status
                                if milestone_status in [
                                    "completed",
                                    "done",
                                    "finished",
                                ]:
                                    milestone_color = "#2e8b57"  # Green
                                elif milestone_status in [
                                    "in progress",
                                    "ongoing",
                                    "started",
                                ]:
                                    milestone_color = "#ff8c00"  # Orange
                                elif milestone_status in [
                                    "blocked",
                                    "on hold",
                                    "delayed",
                                ]:
                                    milestone_color = "#b22222"  # Red
                            else:
                                milestone_desc = str(milestone)

                            # Create milestone card with visual indicator
                            st.markdown(
                                f"""
                            <div style="display:flex;margin-bottom:15px;">
                                <div style="width:30px;position:relative;margin-right:15px;">
                                    <div style="position:absolute;top:0;bottom:0;left:50%;width:2px;background-color:#ddd;transform:translateX(-50%);"></div>
                                    <div style="position:absolute;top:0;left:50%;width:20px;height:20px;border-radius:50%;background-color:{milestone_color};transform:translateX(-50%);border:2px solid white;"></div>
                                </div>
                                <div style="flex-grow:1;">
                                    <div style="border:1px solid #ddd;border-radius:5px;padding:10px;background-color:#f9f9f9;">
                                        {f'<div style="font-weight:bold;color:{milestone_color};">{milestone_date}</div>' if milestone_date else ''}
                                        <div>{milestone_desc}</div>
                                        {f'<div style="font-size:0.8em;margin-top:5px;color:{milestone_color};">Status: {milestone_status.title()}</div>' if milestone_status else ''}
                                    </div>
                                </div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                    elif isinstance(timeline, dict):
                        # Display as key-value pairs
                        for date, event in timeline.items():
                            st.markdown(f"**{date}:** {event}")
                    else:
                        st.text(str(timeline))

                # Display required resources if available
                if (
                    hasattr(capsule, "implementation_details")
                    and capsule.implementation_details
                ):
                    details = capsule.implementation_details
                    if isinstance(details, dict):
                        # Create two columns for resource information
                        col1, col2 = st.columns(2)

                        # Resources section
                        with col1:
                            if (
                                "resources" in details
                                or "required_resources" in details
                            ):
                                resources = details.get(
                                    "resources", details.get("required_resources", {})
                                )
                                st.markdown("### Required Resources")

                                if isinstance(resources, dict):
                                    for category, items in resources.items():
                                        with st.expander(
                                            f"{category.replace('_', ' ').title()}"
                                        ):
                                            if isinstance(items, list):
                                                for item in items:
                                                    st.markdown(f"- {item}")
                                            else:
                                                st.markdown(f"{items}")
                                elif isinstance(resources, list):
                                    for resource in resources:
                                        if isinstance(resource, dict):
                                            resource_name = resource.get(
                                                "name", "Resource"
                                            )
                                            resource_desc = resource.get(
                                                "description", ""
                                            )
                                            resource_qty = resource.get("quantity", "")

                                            resource_text = f"**{resource_name}**"
                                            if resource_qty:
                                                resource_text += (
                                                    f" (Qty: {resource_qty})"
                                                )
                                            if resource_desc:
                                                resource_text += f": {resource_desc}"

                                            st.markdown(f"- {resource_text}")
                                        else:
                                            st.markdown(f"- {resource}")
                                else:
                                    st.text(str(resources))

                        # Dependencies section
                        with col2:
                            if "dependencies" in details:
                                dependencies = details["dependencies"]
                                st.markdown("### Dependencies")

                                if isinstance(dependencies, list):
                                    for dependency in dependencies:
                                        if isinstance(dependency, dict):
                                            dep_name = dependency.get(
                                                "name",
                                                dependency.get("id", "Dependency"),
                                            )
                                            dep_desc = dependency.get("description", "")
                                            dep_status = dependency.get("status", "")

                                            # Set color based on dependency status
                                            dep_color = "#888888"  # Default gray
                                            if dep_status:
                                                if dep_status.lower() in [
                                                    "resolved",
                                                    "satisfied",
                                                    "completed",
                                                ]:
                                                    dep_color = "#2e8b57"  # Green
                                                elif dep_status.lower() in [
                                                    "pending",
                                                    "waiting",
                                                ]:
                                                    dep_color = "#ff8c00"  # Orange
                                                elif dep_status.lower() in [
                                                    "blocked",
                                                    "failed",
                                                ]:
                                                    dep_color = "#b22222"  # Red

                                            st.markdown(
                                                f"""
                                            <div style="border:1px solid #ddd;border-radius:5px;padding:10px;margin-bottom:10px;">
                                                <div style="font-weight:bold;">{dep_name}</div>
                                                {f'<div style="font-size:0.9em;margin-top:3px;">{dep_desc}</div>' if dep_desc else ''}
                                                {f'<div style="font-size:0.8em;margin-top:5px;color:{dep_color};">Status: {dep_status}</div>' if dep_status else ''}
                                            </div>
                                            """,
                                                unsafe_allow_html=True,
                                            )
                                        else:
                                            st.markdown(f"- {dependency}")
                                elif isinstance(dependencies, dict):
                                    for dep_name, dep_info in dependencies.items():
                                        st.markdown(f"**{dep_name}**")
                                        if isinstance(dep_info, dict):
                                            for key, value in dep_info.items():
                                                st.markdown(f"- {key}: {value}")
                                        else:
                                            st.markdown(f"- {dep_info}")
                                else:
                                    st.text(str(dependencies))

                        # Show other implementation details
                        other_keys = [
                            k
                            for k in details.keys()
                            if k
                            not in ["resources", "required_resources", "dependencies"]
                        ]
                        if other_keys:
                            st.markdown("### Additional Implementation Details")
                            for key in other_keys:
                                with st.expander(key.replace("_", " ").title()):
                                    value = details[key]
                                    if isinstance(value, dict) or isinstance(
                                        value, list
                                    ):
                                        st.json(value)
                                    else:
                                        st.markdown(f"{value}")
                    else:
                        st.text(str(details))

                # Display implementation status if available
                if (
                    hasattr(capsule, "implementation_status")
                    and capsule.implementation_status
                ):
                    st.markdown("### Implementation Status")
                    status = capsule.implementation_status

                    if isinstance(status, dict):
                        # Calculate overall progress if available
                        if "progress" in status or "completion" in status:
                            progress = status.get(
                                "progress", status.get("completion", 0)
                            )
                            try:
                                progress_value = float(progress)
                            except (ValueError, TypeError):
                                # If it's a string like "50%", try to parse
                                if isinstance(progress, str) and "%" in progress:
                                    try:
                                        progress_value = (
                                            float(progress.replace("%", "")) / 100.0
                                        )
                                    except (ValueError, TypeError):
                                        progress_value = 0
                                else:
                                    progress_value = 0

                            # Ensure progress is between 0 and 1
                            if progress_value > 1:
                                progress_value = progress_value / 100.0

                            # Determine color based on progress
                            if progress_value >= 0.7:
                                progress_color = "#2e8b57"  # Green
                            elif progress_value >= 0.3:
                                progress_color = "#ff8c00"  # Orange
                            else:
                                progress_color = "#b22222"  # Red

                            # Show progress bar
                            st.markdown(
                                f"""
                            <div style="margin-bottom:20px;">
                                <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                                    <div>Implementation Progress</div>
                                    <div style="font-weight:bold;">{progress_value * 100:.0f}%</div>
                                </div>
                                <div style="background-color:#f0f0f0;border-radius:5px;height:10px;overflow:hidden;">
                                    <div style="background-color:{progress_color};height:100%;width:{progress_value * 100}%;"></div>
                                </div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                        # Display current status
                        if "current_status" in status or "status" in status:
                            current_status = status.get(
                                "current_status", status.get("status", "")
                            )
                            st.markdown(f"**Current Status:** {current_status}")

                        # Display blockers or issues if any
                        if "blockers" in status or "issues" in status:
                            blockers = status.get("blockers", status.get("issues", []))
                            if blockers:
                                st.markdown("#### Blockers & Issues")
                                if isinstance(blockers, list):
                                    for blocker in blockers:
                                        if isinstance(blocker, dict):
                                            blocker_desc = blocker.get(
                                                "description",
                                                blocker.get("issue", "Unknown blocker"),
                                            )
                                            blocker_severity = blocker.get(
                                                "severity", "medium"
                                            ).lower()

                                            # Set color based on severity
                                            if blocker_severity in [
                                                "high",
                                                "critical",
                                                "severe",
                                            ]:
                                                blocker_color = "#b22222"  # Red
                                            elif blocker_severity in [
                                                "medium",
                                                "moderate",
                                            ]:
                                                blocker_color = "#ff8c00"  # Orange
                                            else:
                                                blocker_color = "#2e8b57"  # Green

                                            st.markdown(
                                                f"""
                                            <div style="border-left:3px solid {blocker_color};padding-left:10px;margin-bottom:10px;">
                                                <div>{blocker_desc}</div>
                                                {f'<div style="font-size:0.8em;color:{blocker_color};margin-top:3px;">Severity: {blocker_severity.title()}</div>' if blocker_severity else ''}
                                            </div>
                                            """,
                                                unsafe_allow_html=True,
                                            )
                                        else:
                                            st.markdown(f"- {blocker}")
                                else:
                                    st.markdown(blockers)

                        # Display next steps
                        if "next_steps" in status:
                            next_steps = status["next_steps"]
                            st.markdown("#### Next Steps")
                            if isinstance(next_steps, list):
                                for i, step in enumerate(next_steps):
                                    if isinstance(step, dict):
                                        step_desc = step.get(
                                            "description",
                                            step.get("step", f"Step {i+1}"),
                                        )
                                        step_owner = step.get(
                                            "owner", step.get("assignee", "")
                                        )
                                        step_due = step.get(
                                            "due_date", step.get("deadline", "")
                                        )

                                        step_info = f"- {step_desc}"
                                        if step_owner or step_due:
                                            step_info += " ("
                                            if step_owner:
                                                step_info += f"Owner: {step_owner}"
                                                if step_due:
                                                    step_info += ", "
                                            if step_due:
                                                step_info += f"Due: {step_due}"
                                            step_info += ")"

                                        st.markdown(step_info)
                                    else:
                                        st.markdown(f"- {step}")
                            else:
                                st.markdown(next_steps)

                        # Display additional status information
                        other_keys = [
                            k
                            for k in status.keys()
                            if k
                            not in [
                                "progress",
                                "completion",
                                "current_status",
                                "status",
                                "blockers",
                                "issues",
                                "next_steps",
                            ]
                        ]

                        if other_keys:
                            for key in other_keys:
                                st.markdown(f"**{key.replace('_', ' ').title()}:**")
                                value = status[key]
                                if isinstance(value, dict) or isinstance(value, list):
                                    st.json(value)
                                else:
                                    st.markdown(f"{value}")
                    else:
                        # Display as text if not a dict
                        st.text(str(status))
            else:
                st.info(
                    "No implementation details are available for this governance capsule."
                )
                st.markdown(
                    """
                Implementation details typically include:
                - Timeline for implementing the governance action
                - Required resources and dependencies
                - Current implementation status
                - Blockers and next steps

                These details help stakeholders track progress and ensure accountability in governance actions.
                """
                )

                st.markdown(
                    f"""
                <div style="margin-bottom:20px;">
                    <div style="font-size:1.2em;font-weight:bold;margin-bottom:5px;color:{action_color};">
                        {action_icon} {capsule.governance_action}
                    </div>
                    <div style="height:3px;background:linear-gradient(to right, {action_color}, transparent);margin-bottom:15px;"></div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Action details section
                if hasattr(capsule, "action_details") and capsule.action_details:
                    st.subheader("Action Details")

                    # Try to format action details nicely if it's structured
                    if isinstance(capsule.action_details, dict):
                        # Extract common fields
                        action_type = capsule.action_details.get("type", "")
                        description = capsule.action_details.get("description", "")
                        rationale = capsule.action_details.get("rationale", "")
                        scope = capsule.action_details.get("scope", "")
                        impact = capsule.action_details.get("impact", "")

                        # Create a styled card for key details
                        st.markdown(
                            f"""
                        <div style="padding:15px;background-color:rgba(70,130,180,0.05);border-radius:5px;margin-bottom:20px;">
                            {f'<div style="margin-bottom:10px;"><strong>Type:</strong> {action_type}</div>' if action_type else ''}
                            {f'<div style="margin-bottom:10px;"><strong>Description:</strong> {description}</div>' if description else ''}
                            {f'<div style="margin-bottom:10px;"><strong>Rationale:</strong> {rationale}</div>' if rationale else ''}
                            {f'<div style="margin-bottom:10px;"><strong>Scope:</strong> {scope}</div>' if scope else ''}
                            {f'<div><strong>Impact:</strong> {impact}</div>' if impact else ''}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        # Display any additional details
                        other_details = {
                            k: v
                            for k, v in capsule.action_details.items()
                            if k
                            not in [
                                "type",
                                "description",
                                "rationale",
                                "scope",
                                "impact",
                            ]
                        }

                        if other_details:
                            with st.expander("Additional Action Details"):
                                for key, value in other_details.items():
                                    if isinstance(value, (str, int, float, bool)):
                                        st.markdown(
                                            f"**{key.replace('_', ' ').title()}:** {value}"
                                        )
                                    else:
                                        st.markdown(
                                            f"**{key.replace('_', ' ').title()}:**"
                                        )
                                        st.json(value)
                    else:
                        # Simple string or other format
                        st.markdown(
                            f"""
                        <div style="padding:15px;background-color:rgba(70,130,180,0.05);border-radius:5px;margin-bottom:20px;">
                            {str(capsule.action_details)}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                # Affected entities section
                if hasattr(capsule, "affected_entities") and capsule.affected_entities:
                    st.subheader("Affected Entities")

                    # Process entities to find patterns
                    entities = capsule.affected_entities
                    entity_types = {}

                    # Try to categorize entities if they're structured
                    if isinstance(entities, list):
                        for entity in entities:
                            if isinstance(entity, dict) and "type" in entity:
                                entity_type = entity["type"]
                                if entity_type not in entity_types:
                                    entity_types[entity_type] = []
                                entity_types[entity_type].append(entity)
                            else:
                                # For simple strings or untyped entities
                                if "_misc_" not in entity_types:
                                    entity_types["_misc_"] = []
                                entity_types["_misc_"].append(entity)

                        # If we have distinct entity types, show them in categorized expanders
                        if len(entity_types) > 1 or (
                            "_misc_" not in entity_types and len(entity_types) == 1
                        ):
                            for entity_type, type_entities in entity_types.items():
                                display_type = (
                                    entity_type.replace("_", " ").title()
                                    if entity_type != "_misc_"
                                    else "Other Entities"
                                )
                                with st.expander(
                                    f"{display_type} ({len(type_entities)})",
                                    expanded=entity_type
                                    == list(entity_types.keys())[0],
                                ):
                                    # Show entities in a neat format
                                    for i, entity in enumerate(type_entities):
                                        if isinstance(entity, dict):
                                            # Extract common fields
                                            name = entity.get(
                                                "name",
                                                entity.get("id", f"Entity {i+1}"),
                                            )
                                            description = entity.get("description", "")
                                            impact = entity.get("impact", "")

                                            # Create entity card
                                            st.markdown(
                                                f"""
                                            <div style="padding:10px;margin-bottom:10px;background-color:rgba(70,130,180,0.03);border-radius:5px;">
                                                <div style="font-weight:bold;margin-bottom:5px;">{name}</div>
                                                {f'<div style="margin-bottom:5px;">{description}</div>' if description else ''}
                                                {f'<div><strong>Impact:</strong> {impact}</div>' if impact else ''}
                                            </div>
                                            """,
                                                unsafe_allow_html=True,
                                            )

                                            # Show additional entity fields in expandable section
                                            other_fields = {
                                                k: v
                                                for k, v in entity.items()
                                                if k
                                                not in [
                                                    "type",
                                                    "name",
                                                    "id",
                                                    "description",
                                                    "impact",
                                                ]
                                            }

                                            if other_fields:
                                                with st.expander(
                                                    f"More details for {name}"
                                                ):
                                                    for k, v in other_fields.items():
                                                        if isinstance(
                                                            v, (str, int, float, bool)
                                                        ):
                                                            st.markdown(
                                                                f"**{k.replace('_', ' ').title()}:** {v}"
                                                            )
                                                        else:
                                                            st.markdown(
                                                                f"**{k.replace('_', ' ').title()}:**"
                                                            )
                                                            st.json(v)
                                        else:
                                            # Simple string entity
                                            st.markdown(f"- {entity}")
                        else:
                            # No categorization - show simple list
                            if "_misc_" in entity_types:
                                for entity in entity_types["_misc_"]:
                                    if isinstance(entity, dict):
                                        name = entity.get(
                                            "name", entity.get("id", "Entity")
                                        )
                                        description = entity.get("description", "")
                                        st.markdown(f"**{name}**: {description}")
                                    else:
                                        st.markdown(f"- {entity}")
                            elif len(entity_types) == 1:
                                # Single entity type
                                entity_type = list(entity_types.keys())[0]
                                st.markdown(f"**Entity Type:** {entity_type}")
                                for entity in entity_types[entity_type]:
                                    if isinstance(entity, dict):
                                        name = entity.get(
                                            "name", entity.get("id", "Entity")
                                        )
                                        description = entity.get("description", "")
                                        st.markdown(f"**{name}**: {description}")
                                    else:
                                        st.markdown(f"- {entity}")
                    elif isinstance(entities, dict):
                        # Entity mapping (e.g., entity: impact)
                        st.markdown("### Entity Impact Map")

                        # Create a table for entity-impact mapping
                        entity_rows = []
                        for entity_name, entity_impact in entities.items():
                            if isinstance(entity_impact, (str, int, float, bool)):
                                # Simple impact value
                                entity_rows.append(
                                    f"""
                                <tr>
                                    <td style="padding:8px;border-bottom:1px solid #ddd;">{entity_name}</td>
                                    <td style="padding:8px;border-bottom:1px solid #ddd;">{entity_impact}</td>
                                </tr>"""
                                )
                            elif isinstance(entity_impact, dict):
                                # Structured impact with multiple fields
                                impact_desc = entity_impact.get("description", "")
                                impact_level = entity_impact.get(
                                    "level", entity_impact.get("severity", "")
                                )

                                # Determine impact level color
                                level_color = "#888"  # Default gray
                                if isinstance(impact_level, str):
                                    level_color = {
                                        "high": "#b22222",  # Fire Brick (red)
                                        "medium": "#ff8c00",  # Dark Orange
                                        "low": "#2e8b57",  # Sea Green
                                        "severe": "#800000",  # Maroon (darker red)
                                        "critical": "#800000",  # Maroon (darker red)
                                        "major": "#b22222",  # Fire Brick (red)
                                        "minor": "#2e8b57",  # Sea Green
                                        "none": "#888",  # Gray
                                    }.get(impact_level.lower(), "#888")

                                entity_rows.append(
                                    f"""
                                <tr>
                                    <td style="padding:8px;border-bottom:1px solid #ddd;">{entity_name}</td>
                                    <td style="padding:8px;border-bottom:1px solid #ddd;">
                                        <div>
                                            {impact_desc}
                                            {f'<div style="margin-top:5px;display:inline-block;padding:2px 8px;font-size:0.8em;background-color:rgba{tuple(int(level_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (0.2,)};color:{level_color};border-radius:10px;">{impact_level}</div>' if impact_level else ''}
                                        </div>
                                    </td>
                                </tr>"""
                                )

                        # Create the complete table
                        st.markdown(
                            f"""
                        <table style="width:100%;border-collapse:collapse;">
                            <thead>
                                <tr style="background-color:#f5f5f5;">
                                    <th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">Entity</th>
                                    <th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">Impact</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join(entity_rows)}
                            </tbody>
                        </table>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        # Fallback to simple JSON representation
                        st.json(entities)

                # Governance policy section
                if hasattr(capsule, "governance_policy") and capsule.governance_policy:
                    st.subheader("Governance Policy")

                    # Try to format the policy if it's structured
                    if isinstance(capsule.governance_policy, dict):
                        policy = capsule.governance_policy

                        # Extract common fields
                        policy_name = policy.get("name", policy.get("title", "Policy"))
                        policy_desc = policy.get("description", "")
                        policy_version = policy.get("version", "")
                        policy_date = policy.get(
                            "date", policy.get("effective_date", "")
                        )
                        policy_authority = policy.get(
                            "authority", policy.get("issuer", "")
                        )

                        # Create a styled policy card
                        st.markdown(
                            f"""
                        <div style="padding:15px;background-color:rgba(70,130,180,0.05);border-radius:5px;border-left:5px solid {UATP7_CAPSULE_TYPE_COLORS.get('Governance', '#4682b4')};margin-bottom:15px;">
                            <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
                                <div style="font-weight:bold;font-size:1.1em;">{policy_name}</div>
                                <div style="color:#777;font-size:0.9em;">{f'v{policy_version}' if policy_version else ''} {policy_date}</div>
                            </div>
                            {f'<div style="margin-bottom:10px;">{policy_desc}</div>' if policy_desc else ''}
                            {f'<div style="font-size:0.9em;color:#555;"><strong>Authority:</strong> {policy_authority}</div>' if policy_authority else ''}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        # Policy sections
                        if "sections" in policy and isinstance(
                            policy["sections"], list
                        ):
                            st.markdown("#### Policy Sections")
                            for i, section in enumerate(policy["sections"]):
                                if isinstance(section, dict):
                                    section_title = section.get(
                                        "title", section.get("name", f"Section {i+1}")
                                    )
                                    section_content = section.get(
                                        "content", section.get("text", "")
                                    )

                                    with st.expander(section_title, expanded=i == 0):
                                        st.markdown(section_content)
                                else:
                                    st.markdown(f"**Section {i+1}:** {section}")

                        # Display any additional policy fields
                        other_fields = {
                            k: v
                            for k, v in policy.items()
                            if k
                            not in [
                                "name",
                                "title",
                                "description",
                                "version",
                                "date",
                                "effective_date",
                                "authority",
                                "issuer",
                                "sections",
                            ]
                        }

                        if other_fields:
                            with st.expander("Additional Policy Details"):
                                for k, v in other_fields.items():
                                    if isinstance(v, (str, int, float, bool)):
                                        st.markdown(
                                            f"**{k.replace('_', ' ').title()}:** {v}"
                                        )
                                    elif isinstance(v, list) and all(
                                        isinstance(item, (str, int, float, bool))
                                        for item in v
                                    ):
                                        st.markdown(
                                            f"**{k.replace('_', ' ').title()}:**"
                                        )
                                        for item in v:
                                            st.markdown(f"- {item}")
                                    else:
                                        st.markdown(
                                            f"**{k.replace('_', ' ').title()}:**"
                                        )
                                        st.json(v)
                    else:
                        # Simple text policy
                        st.markdown(
                            f"""
                        <div style="padding:15px;background-color:rgba(70,130,180,0.05);border-radius:5px;border-left:5px solid {UATP7_CAPSULE_TYPE_COLORS.get('Governance', '#4682b4')};margin-bottom:15px;">
                            <div style="white-space:pre-wrap;">
                                {str(capsule.governance_policy).replace('\n', '<br>')}
                            </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

            # Display affected entities with better visualization
            if hasattr(capsule, "affected_entities") and capsule.affected_entities:
                st.subheader("Affected Entities")

                # Group entities if there are many of them
                entities = capsule.affected_entities

                if (
                    len(entities) <= 5
                ):  # Show all entities normally if there aren't too many
                    for i, entity in enumerate(entities):
                        st.markdown(
                            f"""
                        <div style="margin-bottom:8px;padding:10px;background-color:rgba(70,130,180,0.05);border-left:4px solid {UATP7_CAPSULE_TYPE_COLORS.get('Governance', '#4682b4')}">
                            {entity}
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                else:  # Many entities, use a more compact visualization
                    # Try to categorize entities if they follow a pattern
                    entity_categories = {}

                    for entity in entities:
                        # Simple categorization by the first word or prefix
                        parts = entity.split("/")
                        if len(parts) > 1:
                            category = parts[0]
                            if category not in entity_categories:
                                entity_categories[category] = []
                            entity_categories[category].append(entity)
                        else:
                            if "_misc_" not in entity_categories:
                                entity_categories["_misc_"] = []
                            entity_categories["_misc_"].append(entity)

                    # If we couldn't categorize well, use a simpler approach
                    if (
                        len(entity_categories) <= 1
                        or "_misc_" in entity_categories
                        and len(entity_categories["_misc_"]) > len(entities) / 2
                    ):
                        # Just use expandable sections for groups of entities
                        group_size = 5
                        for i in range(0, len(entities), group_size):
                            group = entities[i : i + group_size]
                            with st.expander(
                                f"Entities {i+1} to {i+len(group)}", expanded=i == 0
                            ):
                                for entity in group:
                                    st.markdown(f"- {entity}")
                    else:
                        # Show categorized entities in expandable sections
                        for category, category_entities in entity_categories.items():
                            display_category = (
                                "Miscellaneous" if category == "_misc_" else category
                            )
                            with st.expander(
                                f"{display_category} ({len(category_entities)})"
                            ):
                                for entity in category_entities:
                                    st.markdown(f"- {entity}")

            # Display a visual preview of the stakeholder votes if available
            if (
                hasattr(capsule, "stakeholder_votes")
                and capsule.stakeholder_votes
                and isinstance(capsule.stakeholder_votes, dict)
            ):
                st.subheader("Vote Distribution")

                # Create a simplified vote summary
                vote_data = {}
                for stakeholder, vote in capsule.stakeholder_votes.items():
                    try:
                        vote_data[stakeholder] = float(vote)
                    except:
                        # Handle non-numeric votes
                        if isinstance(vote, str) and vote.lower() in [
                            "approve",
                            "yes",
                            "approved",
                            "support",
                        ]:
                            vote_data[stakeholder] = 1.0
                        elif isinstance(vote, str) and vote.lower() in [
                            "disapprove",
                            "no",
                            "rejected",
                            "against",
                        ]:
                            vote_data[stakeholder] = 0.0
                        else:
                            vote_data[stakeholder] = 0.5  # Neutral

                # Group votes by outcome for visualization
                approvals = sum(1 for v in vote_data.values() if v > 0.5)
                disapprovals = sum(1 for v in vote_data.values() if v < 0.5)
                neutral = sum(1 for v in vote_data.values() if v == 0.5)

                # Create a horizontal stacked bar chart using HTML
                total_votes = len(vote_data)
                if total_votes > 0:
                    approve_pct = (approvals / total_votes) * 100
                    neutral_pct = (neutral / total_votes) * 100
                    disapprove_pct = (disapprovals / total_votes) * 100

                    st.markdown(
                        f"""
                    <div style="margin-bottom:15px;">
                        <div style="display:flex;align-items:center;margin-bottom:5px;">
                            <div style="width:100%;height:24px;background-color:#f0f0f0;border-radius:12px;overflow:hidden;display:flex;">
                                <div style="width:{approve_pct}%;height:100%;background-color:#2e8b57;"></div>
                                <div style="width:{neutral_pct}%;height:100%;background-color:#ff8c00;"></div>
                                <div style="width:{disapprove_pct}%;height:100%;background-color:#b22222;"></div>
                            </div>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:0.9em;">
                            <div><span style="color:#2e8b57;font-weight:bold;">{approvals}</span> Approve</div>
                            <div><span style="color:#ff8c00;font-weight:bold;">{neutral}</span> Neutral</div>
                            <div><span style="color:#b22222;font-weight:bold;">{disapprovals}</span> Disapprove</div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # Policy & Action Tab
        with tabs[1]:
            # Display governance policy with better formatting
            if hasattr(capsule, "governance_policy") and capsule.governance_policy:
                st.subheader("Governance Policy")

                # Create a policy card with improved styling
                st.markdown(
                    f"""
                <div style="background-color:rgba(70,130,180,0.05);padding:20px;border-radius:5px;border-left:5px solid {UATP7_CAPSULE_TYPE_COLORS.get('Governance', '#4682b4')};margin-bottom:20px;">
                    <div style="font-style:italic;color:#555;margin-bottom:10px;">
                        Policy Document
                    </div>
                    <div style="white-space:pre-wrap;">
                        {capsule.governance_policy.replace('\n', '<br>')}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Try to extract policy details if it's in a structured format
                try:
                    import json

                    policy_dict = json.loads(capsule.governance_policy)

                    if isinstance(policy_dict, dict):
                        # Display structured policy information
                        if "version" in policy_dict:
                            st.markdown(f"**Policy Version:** {policy_dict['version']}")

                        if "effective_date" in policy_dict:
                            st.markdown(
                                f"**Effective Date:** {policy_dict['effective_date']}"
                            )

                        if "scope" in policy_dict:
                            st.markdown("### Policy Scope")
                            if isinstance(policy_dict["scope"], list):
                                for item in policy_dict["scope"]:
                                    st.markdown(f"- {item}")
                            else:
                                st.markdown(policy_dict["scope"])

                        if "rules" in policy_dict and isinstance(
                            policy_dict["rules"], list
                        ):
                            st.markdown("### Policy Rules")
                            for i, rule in enumerate(policy_dict["rules"]):
                                with st.expander(
                                    f"Rule {i+1}: {rule.get('name', 'Unnamed Rule')}",
                                    expanded=i == 0,
                                ):
                                    if isinstance(rule, dict):
                                        for k, v in rule.items():
                                            if k != "name":
                                                st.markdown(
                                                    f"**{k.replace('_', ' ').title()}:** {v}"
                                                )
                                    else:
                                        st.markdown(str(rule))
                except:
                    # Not JSON, already displayed as text
                    pass

            # Show action details if available
            if hasattr(capsule, "action_details") and capsule.action_details:
                st.subheader("Action Details")

                if isinstance(capsule.action_details, dict):
                    # Structured action details
                    # Timeline section if available
                    if "timeline" in capsule.action_details:
                        st.markdown("#### Timeline")
                        timeline = capsule.action_details["timeline"]

                        if isinstance(timeline, dict):
                            # Display as key-value pairs for dates/events
                            cols = st.columns(2)
                            items = list(timeline.items())

                            for i, (date, event) in enumerate(items):
                                with cols[i % 2]:
                                    st.markdown(
                                        f"""
                                    <div style="border-left:3px solid {UATP7_CAPSULE_TYPE_COLORS.get('Governance', '#4682b4')};padding-left:10px;margin-bottom:15px;">
                                        <div style="font-weight:bold;">{date}</div>
                                        <div>{event}</div>
                                    </div>
                                    """,
                                        unsafe_allow_html=True,
                                    )
                        elif isinstance(timeline, list):
                            # Display as a sequential timeline
                            for i, item in enumerate(timeline):
                                if (
                                    isinstance(item, dict)
                                    and "date" in item
                                    and "event" in item
                                ):
                                    st.markdown(
                                        f"""
                                    <div style="display:flex;margin-bottom:15px;">
                                        <div style="min-width:100px;font-weight:bold;">{item['date']}</div>
                                        <div style="flex-grow:1;border-left:2px solid {UATP7_CAPSULE_TYPE_COLORS.get('Governance', '#4682b4')};padding-left:15px;">
                                            {item['event']}
                                        </div>
                                    </div>
                                    """,
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.markdown(f"- {item}")

                    # Steps section if available
                    if "steps" in capsule.action_details and isinstance(
                        capsule.action_details["steps"], list
                    ):
                        st.markdown("#### Implementation Steps")
                        steps = capsule.action_details["steps"]

                        for i, step in enumerate(steps):
                            if isinstance(step, dict) and "title" in step:
                                with st.expander(
                                    f"{i+1}. {step['title']}", expanded=i == 0
                                ):
                                    if "description" in step:
                                        st.markdown(step["description"])
                                    if "requirements" in step and isinstance(
                                        step["requirements"], list
                                    ):
                                        st.markdown("**Requirements:**")
                                        for req in step["requirements"]:
                                            st.markdown(f"- {req}")
                            else:
                                st.markdown(f"**Step {i+1}:** {step}")

                    # Other action details
                    for k, v in capsule.action_details.items():
                        if k not in ["timeline", "steps"]:
                            if isinstance(v, (str, int, float, bool)):
                                st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")
                            elif isinstance(v, (list, dict)):
                                with st.expander(f"{k.replace('_', ' ').title()}"):
                                    st.json(v)
                else:
                    # Simple string or other type
                    st.markdown(
                        f"""
                    <div style="padding:15px;background-color:rgba(70,130,180,0.05);border-radius:5px;">
                        {str(capsule.action_details)}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        # Stakeholder Votes Tab
        with tabs[2]:
            if hasattr(capsule, "stakeholder_votes") and capsule.stakeholder_votes:
                # Create a visualization for votes
                if isinstance(capsule.stakeholder_votes, dict):
                    # Process and standardize vote data
                    vote_data = {}
                    vote_metadata = {}
                    for stakeholder, vote in capsule.stakeholder_votes.items():
                        # Extract any metadata if vote is structured
                        metadata = {}
                        actual_vote = vote

                        if isinstance(vote, dict):
                            actual_vote = vote.get("vote", 0.5)
                            metadata = {k: v for k, v in vote.items() if k != "vote"}

                        # Convert vote to numeric value
                        try:
                            vote_value = float(actual_vote)
                        except:
                            # Handle non-numeric votes
                            if isinstance(actual_vote, str):
                                if actual_vote.lower() in [
                                    "approve",
                                    "yes",
                                    "approved",
                                    "support",
                                    "true",
                                ]:
                                    vote_value = 1.0
                                elif actual_vote.lower() in [
                                    "disapprove",
                                    "no",
                                    "rejected",
                                    "against",
                                    "false",
                                ]:
                                    vote_value = 0.0
                                else:
                                    vote_value = 0.5  # Neutral
                            else:
                                vote_value = 0.5  # Default neutral for non-convertible

                        vote_data[stakeholder] = vote_value
                        if metadata:
                            vote_metadata[stakeholder] = metadata

                    # Calculate metrics for summary
                    total_votes = len(vote_data)
                    approvals = sum(1 for v in vote_data.values() if v > 0.5)
                    disapprovals = sum(1 for v in vote_data.values() if v < 0.5)
                    neutral = sum(1 for v in vote_data.values() if v == 0.5)

                    # Calculate weighted approval percentage
                    weighted_approval = (
                        sum(vote_data.values()) / total_votes if total_votes > 0 else 0
                    )
                    approval_percentage = weighted_approval * 100

                    # Determine outcome based on approval percentage
                    threshold = 0.5  # Default simple majority threshold
                    outcome_color = (
                        "#2e8b57" if weighted_approval > threshold else "#b22222"
                    )
                    outcome_text = (
                        "Approved" if weighted_approval > threshold else "Rejected"
                    )
                    outcome_icon = (
                        "[OK]" if weighted_approval > threshold else "[ERROR]"
                    )

                    # Create a summary box at the top
                    st.markdown(
                        f"""
                    <div style="display:flex;align-items:center;margin-bottom:20px;padding:15px;background-color:rgba{tuple(int(outcome_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)};border-radius:5px;">
                        <div style="font-size:2em;margin-right:15px;">{outcome_icon}</div>
                        <div>
                            <div style="font-size:1.2em;font-weight:bold;margin-bottom:5px;">Vote Status: <span style="color:{outcome_color};">{outcome_text}</span></div>
                            <div>Total Stakeholders: {total_votes} | Approval Rate: <span style="font-weight:bold;">{approval_percentage:.1f}%</span></div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Create a visual breakdown of votes
                    st.subheader("Vote Distribution")

                    # Create a more visual stacked bar
                    if total_votes > 0:
                        approve_pct = (approvals / total_votes) * 100
                        neutral_pct = (neutral / total_votes) * 100
                        disapprove_pct = (disapprovals / total_votes) * 100

                        st.markdown(
                            f"""
                        <div style="margin-bottom:25px;">
                            <div style="margin-bottom:10px;font-weight:bold;">Vote Breakdown</div>
                            <div style="display:flex;align-items:center;margin-bottom:5px;">
                                <div style="width:100%;height:30px;background-color:#f0f0f0;border-radius:15px;overflow:hidden;display:flex;">
                                    <div style="width:{approve_pct}%;height:100%;background-color:#2e8b57;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;">{approvals if approve_pct >= 15 else ''}</div>
                                    <div style="width:{neutral_pct}%;height:100%;background-color:#ff8c00;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;">{neutral if neutral_pct >= 15 else ''}</div>
                                    <div style="width:{disapprove_pct}%;height:100%;background-color:#b22222;display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;">{disapprovals if disapprove_pct >= 15 else ''}</div>
                                </div>
                            </div>
                            <div style="display:flex;justify-content:space-between;font-size:0.9em;margin-bottom:20px;">
                                <div><div style="display:inline-block;width:12px;height:12px;background-color:#2e8b57;margin-right:5px;"></div>Approve ({approve_pct:.1f}%)</div>
                                <div><div style="display:inline-block;width:12px;height:12px;background-color:#ff8c00;margin-right:5px;"></div>Neutral ({neutral_pct:.1f}%)</div>
                                <div><div style="display:inline-block;width:12px;height:12px;background-color:#b22222;margin-right:5px;"></div>Disapprove ({disapprove_pct:.1f}%)</div>
                            </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                    # Display individual stakeholder votes
                    st.subheader("Individual Stakeholder Votes")

                    # Sort stakeholders by vote value (descending)
                    sorted_stakeholders = sorted(
                        vote_data.items(), key=lambda x: x[1], reverse=True
                    )

                    # Create a table of votes with visual indicators
                    vote_rows = []
                    for stakeholder, vote_value in sorted_stakeholders:
                        # Determine vote display properties
                        if vote_value > 0.5:
                            vote_color = "#2e8b57"
                            vote_text = "Approve"
                            vote_icon = "[OK]"
                        elif vote_value < 0.5:
                            vote_color = "#b22222"
                            vote_text = "Disapprove"
                            vote_icon = "[ERROR]"
                        else:
                            vote_color = "#ff8c00"
                            vote_text = "Neutral"
                            vote_icon = "[WARN]"

                        # Check if we have additional metadata
                        has_metadata = (
                            stakeholder in vote_metadata and vote_metadata[stakeholder]
                        )
                        info_icon = "ℹ️" if has_metadata else ""

                        # Add row to table
                        vote_rows.append(
                            f"""
                        <tr>
                            <td style="padding:8px;border-bottom:1px solid #eee;">{stakeholder}</td>
                            <td style="padding:8px;border-bottom:1px solid #eee;">
                                <div style="display:flex;align-items:center;">
                                    <span style="margin-right:5px;">{vote_icon}</span>
                                    <span style="color:{vote_color};font-weight:bold;">{vote_text}</span>
                                    {f'<span style="margin-left:5px;cursor:pointer;" title="Has additional metadata">{info_icon}</span>' if has_metadata else ''}
                                </div>
                            </td>
                            <td style="padding:8px;border-bottom:1px solid #eee;width:150px;">
                                <div style="background-color:#f0f0f0;height:10px;border-radius:5px;overflow:hidden;">
                                    <div style="background-color:{vote_color};height:100%;width:{vote_value*100}%;"></div>
                                </div>
                            </td>
                            <td style="padding:8px;border-bottom:1px solid #eee;text-align:right;">{vote_value:.2f}</td>
                        </tr>
                        """
                        )

                    # Create the complete table
                    st.markdown(
                        f"""
                    <div style="margin-bottom:20px;max-height:400px;overflow-y:auto;">
                        <table style="width:100%;border-collapse:collapse;">
                            <thead>
                                <tr style="background-color:#f5f5f5;">
                                    <th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">Stakeholder</th>
                                    <th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">Decision</th>
                                    <th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">Vote Strength</th>
                                    <th style="padding:8px;text-align:right;border-bottom:2px solid #ddd;">Value</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join(vote_rows)}
                            </tbody>
                        </table>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Display metadata if available
                    if vote_metadata:
                        st.subheader("Vote Metadata")
                        for stakeholder, metadata in vote_metadata.items():
                            with st.expander(f"Metadata for {stakeholder}"):
                                for key, value in metadata.items():
                                    st.markdown(
                                        f"**{key.replace('_', ' ').title()}:** {value}"
                                    )
                else:
                    # Non-dictionary vote data, display as is
                    st.subheader("Stakeholder Votes")
                    st.json(capsule.stakeholder_votes)
            else:
                st.info("No stakeholder votes information available.")

            # Display authorization proof in this tab as well
            if hasattr(capsule, "authorization_proof") and capsule.authorization_proof:
                st.subheader("Authorization Proof")

                # Check if it's a structured dictionary
                if isinstance(capsule.authorization_proof, dict):
                    # Try to format it nicely
                    proof_type = capsule.authorization_proof.get("type", "Standard")
                    proof_method = capsule.authorization_proof.get("method", "")
                    proof_issuer = capsule.authorization_proof.get("issuer", "")
                    proof_timestamp = capsule.authorization_proof.get("timestamp", "")
                    proof_signature = capsule.authorization_proof.get("signature", "")

                    # Create a styled card for the proof
                    st.markdown(
                        f"""
                    <div style="padding:15px;background-color:rgba(70,130,180,0.05);border-radius:5px;margin-bottom:15px;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
                            <div style="font-weight:bold;font-size:1.1em;">{proof_type} Authorization</div>
                            <div style="color:#888;">{proof_timestamp}</div>
                        </div>
                        {f'<div style="margin-bottom:10px;"><strong>Method:</strong> {proof_method}</div>' if proof_method else ''}
                        {f'<div style="margin-bottom:10px;"><strong>Issuer:</strong> {proof_issuer}</div>' if proof_issuer else ''}
                        {f'<div style="font-family:monospace;font-size:0.9em;background-color:#f5f5f5;padding:10px;border-radius:3px;overflow-x:auto;">{proof_signature[:20]}...</div>' if proof_signature else ''}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Show full JSON in an expander
                    with st.expander("View complete authorization proof"):
                        st.json(capsule.authorization_proof)
                else:
                    # Just show the JSON
                    st.json(capsule.authorization_proof)

        # Implementation Tab
        with tabs[3]:
            # Display implementation notes with better formatting
            if (
                hasattr(capsule, "implementation_notes")
                and capsule.implementation_notes
            ):
                st.subheader("Implementation Notes")

                # Create a notes card with improved styling
                st.markdown(
                    f"""
                <div style="background-color:rgba(70,130,180,0.05);padding:20px;border-radius:5px;border-left:5px solid {UATP7_CAPSULE_TYPE_COLORS.get('Governance', '#4682b4')};margin-bottom:20px;">
                    <div style="font-style:italic;color:#555;margin-bottom:10px;">
                        Implementation Guidelines
                    </div>
                    <div style="white-space:pre-wrap;">
                        {capsule.implementation_notes.replace('\n', '<br>')}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                # Try to parse structured implementation notes if applicable
                try:
                    import json

                    notes_dict = json.loads(capsule.implementation_notes)

                    if isinstance(notes_dict, dict):
                        # Display structured implementation information
                        if "timeline" in notes_dict:
                            st.markdown("### Implementation Timeline")
                            timeline = notes_dict["timeline"]

                            if isinstance(timeline, list):
                                # Create a visual timeline
                                for i, milestone in enumerate(timeline):
                                    if isinstance(milestone, dict):
                                        date = milestone.get("date", "")
                                        description = milestone.get("description", "")
                                        status = milestone.get("status", "")

                                        # Determine status color
                                        status_color = {
                                            "completed": "#2e8b57",  # Sea Green
                                            "in_progress": "#ff8c00",  # Dark Orange
                                            "pending": "#4682b4",  # Steel Blue
                                            "delayed": "#b22222",  # Fire Brick
                                        }.get(
                                            status.lower()
                                            if isinstance(status, str)
                                            else "",
                                            "#888888",
                                        )

                                        # Create a timeline item
                                        st.markdown(
                                            f"""
                                        <div style="display:flex;margin-bottom:20px;">
                                            <div style="position:relative;width:30px;margin-right:15px;">
                                                <div style="position:absolute;width:20px;height:20px;background-color:{status_color};border-radius:50%;"></div>
                                                {'' if i == len(timeline) - 1 else '<div style="position:absolute;top:20px;bottom:0;left:10px;width:2px;background-color:#ccc;"></div>'}
                                            </div>
                                            <div style="flex-grow:1;">
                                                <div style="font-weight:bold;">{date}</div>
                                                <div style="margin:5px 0 10px;">{description}</div>
                                                {f'<div style="display:inline-block;padding:3px 8px;background-color:rgba{tuple(int(status_color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (0.2,)};border-radius:10px;font-size:0.8em;">{status.replace("_", " ").title()}</div>' if status else ''}
                                            </div>
                                        </div>
                                        """,
                                            unsafe_allow_html=True,
                                        )
                                    else:
                                        st.markdown(f"- {milestone}")

                        if "resources" in notes_dict and isinstance(
                            notes_dict["resources"], list
                        ):
                            st.markdown("### Required Resources")
                            resources = notes_dict["resources"]

                            # Group resources by type if available
                            resource_types = {}
                            for resource in resources:
                                if isinstance(resource, dict) and "type" in resource:
                                    r_type = resource["type"]
                                    if r_type not in resource_types:
                                        resource_types[r_type] = []
                                    resource_types[r_type].append(resource)
                                else:
                                    if "_misc_" not in resource_types:
                                        resource_types["_misc_"] = []
                                    resource_types["_misc_"].append(resource)

                            # Display resources by type
                            if len(resource_types) > 1:
                                for r_type, type_resources in resource_types.items():
                                    display_type = (
                                        "Miscellaneous"
                                        if r_type == "_misc_"
                                        else r_type.replace("_", " ").title()
                                    )
                                    with st.expander(
                                        f"{display_type} Resources ({len(type_resources)})",
                                        expanded=r_type
                                        == list(resource_types.keys())[0],
                                    ):
                                        for resource in type_resources:
                                            if isinstance(resource, dict):
                                                name = resource.get("name", "Unnamed")
                                                description = resource.get(
                                                    "description", ""
                                                )
                                                quantity = resource.get("quantity", "")

                                                st.markdown(
                                                    f"""
                                                <div style="margin-bottom:10px;padding:10px;background-color:rgba(70,130,180,0.05);border-radius:5px;">
                                                    <div style="font-weight:bold;">{name} {f'({quantity})' if quantity else ''}</div>
                                                    <div>{description}</div>
                                                </div>
                                                """,
                                                    unsafe_allow_html=True,
                                                )
                                            else:
                                                st.markdown(f"- {resource}")
                            else:
                                # Simple list if no categorization
                                for resource in resources:
                                    if isinstance(resource, dict):
                                        name = resource.get("name", "Unnamed")
                                        description = resource.get("description", "")
                                        quantity = resource.get("quantity", "")

                                        st.markdown(
                                            f"**{name}** {f'({quantity})' if quantity else ''}: {description}"
                                        )
                                    else:
                                        st.markdown(f"- {resource}")

                        if "dependencies" in notes_dict and isinstance(
                            notes_dict["dependencies"], list
                        ):
                            st.markdown("### Dependencies")
                            dependencies = notes_dict["dependencies"]

                            # Create visual dependency list
                            for i, dependency in enumerate(dependencies):
                                if isinstance(dependency, dict):
                                    dep_name = dependency.get("name", "Unnamed")
                                    dep_status = dependency.get("status", "")
                                    dep_desc = dependency.get("description", "")
                                    dep_owner = dependency.get("owner", "")

                                    # Determine status indicator
                                    status_color = "#4682b4"  # Default blue
                                    status_icon = ""  # Default circle
                                    if isinstance(dep_status, str):
                                        if dep_status.lower() in [
                                            "resolved",
                                            "completed",
                                            "done",
                                        ]:
                                            status_color = "#2e8b57"  # Green
                                            status_icon = "[OK]"
                                        elif dep_status.lower() in [
                                            "blocked",
                                            "failed",
                                        ]:
                                            status_color = "#b22222"  # Red
                                            status_icon = "[ERROR]"
                                        elif dep_status.lower() in [
                                            "in_progress",
                                            "ongoing",
                                        ]:
                                            status_color = "#ff8c00"  # Orange
                                            status_icon = ""

                                    st.markdown(
                                        f"""
                                    <div style="display:flex;margin-bottom:15px;">
                                        <div style="margin-right:10px;font-size:1.2em;">{status_icon}</div>
                                        <div style="flex-grow:1;">
                                            <div style="font-weight:bold;">{dep_name}</div>
                                            <div style="margin:5px 0;">{dep_desc}</div>
                                            <div style="display:flex;font-size:0.9em;color:#555;">
                                                {f'<div style="margin-right:15px;"><strong>Owner:</strong> {dep_owner}</div>' if dep_owner else ''}
                                                {f'<div><strong>Status:</strong> <span style="color:{status_color};">{dep_status}</span></div>' if dep_status else ''}
                                            </div>
                                        </div>
                                    </div>
                                    """,
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.markdown(f"- {dependency}")

                        # Other implementation details
                        for key, value in notes_dict.items():
                            if key not in ["timeline", "resources", "dependencies"]:
                                if isinstance(value, str):
                                    st.markdown(
                                        f"**{key.replace('_', ' ').title()}:** {value}"
                                    )
                                elif isinstance(value, (list, dict)):
                                    with st.expander(
                                        f"{key.replace('_', ' ').title()}"
                                    ):
                                        if isinstance(value, list):
                                            for item in value:
                                                st.markdown(f"- {item}")
                                        else:
                                            st.json(value)
                except:
                    # Not structured JSON, already displayed as text
                    pass
            else:
                st.info("No implementation notes available for this governance action.")

            # Display implementation status if available
            if (
                hasattr(capsule, "implementation_status")
                and capsule.implementation_status
            ):
                st.subheader("Implementation Status")

                if isinstance(capsule.implementation_status, dict):
                    # Extract status information
                    status = capsule.implementation_status.get("status", "Unknown")
                    progress = capsule.implementation_status.get("progress", 0.0)
                    last_update = capsule.implementation_status.get("last_updated", "")
                    assignee = capsule.implementation_status.get("assignee", "")
                    blockers = capsule.implementation_status.get("blockers", [])
                    next_steps = capsule.implementation_status.get("next_steps", [])

                    # Determine status color
                    status_color = {
                        "not_started": "#888888",  # Gray
                        "in_progress": "#ff8c00",  # Orange
                        "completed": "#2e8b57",  # Green
                        "blocked": "#b22222",  # Red
                        "pending_approval": "#4682b4",  # Blue
                    }.get(
                        status.lower().replace(" ", "_")
                        if isinstance(status, str)
                        else "",
                        "#888888",
                    )

                    # Create status card
                    st.markdown(
                        f"""
                    <div style="padding:15px;background-color:rgba{tuple(int(status_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.1,)};border-radius:5px;margin-bottom:20px;">
                        <div style="display:flex;align-items:center;margin-bottom:10px;">
                            <div style="font-weight:bold;font-size:1.1em;margin-right:10px;">Status:</div>
                            <div style="color:{status_color};font-weight:bold;">{status}</div>
                            {f'<div style="margin-left:auto;font-size:0.9em;color:#555;">{last_update}</div>' if last_update else ''}
                        </div>
                        {f'<div style="margin-bottom:10px;"><strong>Assignee:</strong> {assignee}</div>' if assignee else ''}

                        <div style="margin-bottom:10px;">
                            <div style="display:flex;align-items:center;margin-bottom:5px;">
                                <div style="font-weight:bold;margin-right:10px;">Progress:</div>
                                <div>{int(float(progress) * 100)}%</div>
                            </div>
                            <div style="background-color:rgba(255,255,255,0.3);height:10px;border-radius:5px;">
                                <div style="background-color:{status_color};height:100%;width:{float(progress) * 100}%;border-radius:5px;"></div>
                            </div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Display blockers if any
                    if blockers:
                        st.markdown("#### Blockers")
                        for blocker in blockers:
                            if isinstance(blocker, dict):
                                blocker_desc = blocker.get("description", "")
                                blocker_severity = blocker.get("severity", "Medium")
                                blocker_owner = blocker.get("owner", "")

                                # Determine severity color
                                severity_color = {
                                    "Critical": "#800000",  # Maroon
                                    "High": "#b22222",  # Fire Brick
                                    "Medium": "#ff8c00",  # Dark Orange
                                    "Low": "#2e8b57",  # Sea Green
                                }.get(blocker_severity, "#ff8c00")

                                st.markdown(
                                    f"""
                                <div style="margin-bottom:15px;padding:10px;background-color:rgba(178,34,34,0.05);border-radius:5px;border-left:3px solid {severity_color};">
                                    <div style="font-weight:bold;margin-bottom:5px;">{blocker_desc}</div>
                                    <div style="display:flex;font-size:0.9em;">
                                        <div style="margin-right:15px;"><span style="color:{severity_color};">{blocker_severity}</span> severity</div>
                                        {f'<div><strong>Owner:</strong> {blocker_owner}</div>' if blocker_owner else ''}
                                    </div>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(f"- {blocker}")

                    # Display next steps if any
                    if next_steps:
                        st.markdown("#### Next Steps")
                        for i, step in enumerate(next_steps):
                            if isinstance(step, dict):
                                step_desc = step.get("description", "")
                                step_date = step.get("target_date", "")
                                step_owner = step.get("owner", "")

                                st.markdown(
                                    f"""
                                <div style="margin-bottom:10px;padding:10px;background-color:rgba(70,130,180,0.05);border-radius:5px;">
                                    <div style="font-weight:bold;">{i+1}. {step_desc}</div>
                                    <div style="display:flex;font-size:0.9em;margin-top:5px;">
                                        {f'<div style="margin-right:15px;"><strong>Target:</strong> {step_date}</div>' if step_date else ''}
                                        {f'<div><strong>Owner:</strong> {step_owner}</div>' if step_owner else ''}
                                    </div>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(f"{i+1}. {step}")

                    # Display any additional status fields
                    for key, value in capsule.implementation_status.items():
                        if key not in [
                            "status",
                            "progress",
                            "last_updated",
                            "assignee",
                            "blockers",
                            "next_steps",
                        ]:
                            if isinstance(value, (str, int, float, bool)):
                                st.markdown(
                                    f"**{key.replace('_', ' ').title()}:** {value}"
                                )
                else:
                    # Simple string
                    st.markdown(
                        f"""
                    <div style="padding:15px;background-color:rgba(70,130,180,0.05);border-radius:5px;">
                        {str(capsule.implementation_status)}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )


def render_economic_content(capsule: EconomicCapsule):
    """Render specialized content for Economic capsules with enhanced multi-tab visualizations."""
    # Create tabs for different aspects of economic visualization
    tab1, tab2, tab3 = st.tabs(
        ["Value Attribution", "Contributor Analysis", "Dividend Distribution"]
    )

    #############################
    # Tab 1: Value Attribution
    #############################
    with tab1:
        st.subheader("Value Attribution Details")

        # Display economic event type
        if hasattr(capsule, "economic_event_type"):
            event_type = capsule.economic_event_type
            st.markdown(
                f"<h3 style='margin-bottom:0;'>Event Type: {event_type}</h3>",
                unsafe_allow_html=True,
            )

        # Show value amount with currency if available
        if hasattr(capsule, "value_amount"):
            currency = capsule.metadata.get("currency", "Units")
            formatted_amount = f"{capsule.value_amount:,.2f} {currency}"
            st.markdown(
                f"<h2 style='color:#daa520;margin-top:0;'>{formatted_amount}</h2>",
                unsafe_allow_html=True,
            )

        # Economic Value section
        if hasattr(capsule, "economic_value") and capsule.economic_value:
            st.markdown("### Value Characteristics")
            cols = st.columns(3)

            # Extract metrics from economic_value
            if isinstance(capsule.economic_value, dict):
                metrics = {
                    "Total Value": capsule.economic_value.get("total_value", "N/A"),
                    "Value Type": capsule.economic_value.get("value_type", "N/A"),
                    "Value Precision": capsule.economic_value.get(
                        "value_precision", "N/A"
                    ),
                    "Distribution Fairness": capsule.economic_value.get(
                        "distribution_fairness_score", "N/A"
                    ),
                }

                # Display metrics in columns
                for i, (label, value) in enumerate(metrics.items()):
                    with cols[i % 3]:
                        st.metric(label, value)

        # Show calculation method
        if hasattr(capsule, "value_calculation_method"):
            st.markdown("### Value Calculation Method")
            st.info(capsule.value_calculation_method)

        # Value chain visualization if available
        if hasattr(capsule, "value_chain_analysis") and capsule.value_chain_analysis:
            st.markdown("### Value Chain Analysis")
            value_chain = capsule.value_chain_analysis

            # Display input value
            input_value = value_chain.get("input_value", 0)

            # Get value added steps
            value_added_steps = value_chain.get("value_added_steps", [])
            if value_added_steps:
                # Create visualization of value chain progression
                stages = (
                    ["Input"]
                    + [
                        step.get("step", f"Step {i+1}")
                        for i, step in enumerate(value_added_steps)
                    ]
                    + ["Final"]
                )
                values = [input_value]
                running_total = input_value
                for step in value_added_steps:
                    running_total += step.get("added_value", 0)
                    values.append(running_total)
                values.append(capsule.value_amount)  # Final value

                # Create bar chart of value progression
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.bar(stages, values, color="#daa520")

                # Add value labels above bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height + 0.1,
                        f"{height:.1f}",
                        ha="center",
                        va="bottom",
                    )

                ax.set_title("Value Chain Progression")
                ax.set_xlabel("Stage")
                ax.set_ylabel("Cumulative Value")
                plt.xticks(rotation=45, ha="right")
                plt.tight_layout()
                st.pyplot(fig)

                # Show value multipliers if available
                multipliers = value_chain.get("value_multipliers", [])
                if multipliers:
                    st.markdown("#### Value Multipliers")
                    multiplier_data = {}
                    for multiplier in multipliers:
                        factor = multiplier.get("factor", "Unknown")
                        value = multiplier.get("multiplier", 1.0)
                        multiplier_data[factor] = value

                    # Display as table and horizontal bar chart
                    multiplier_df = {"Factor": [], "Multiplier": []}
                    for factor, value in multiplier_data.items():
                        multiplier_df["Factor"].append(factor)
                        multiplier_df["Multiplier"].append(value)

                    st.table(multiplier_df)

                    # Show total multiplier effect
                    total_effect = value_chain.get("total_multiplier_effect", 0)
                    st.metric("Total Multiplier Effect", f"{total_effect:.2f}")

        # Display value creation history as timeline if available
        if (
            hasattr(capsule, "value_creation_history")
            and capsule.value_creation_history
        ):
            st.markdown("### Value Creation Timeline")
            history = capsule.value_creation_history

            # Extract timestamps and values
            dates = []
            values = []
            events = []
            for event in history:
                try:
                    timestamp = safe_parse_datetime(event.get("timestamp"))
                    if timestamp:
                        dates.append(timestamp)
                        values.append(event.get("value_estimate", 0))
                        events.append(event.get("event", "Unknown Event"))
                except Exception as e:
                    st.warning(f"Error parsing timeline event: {e}")

            # Create timeline chart
            if dates and values:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(dates, values, "o-", color="#daa520", linewidth=2, markersize=8)

                # Add value labels
                for i, (d, v, e) in enumerate(zip(dates, values, events)):
                    ax.annotate(
                        f"{v:.1f}",
                        xy=(d, v),
                        xytext=(0, 10),
                        textcoords="offset points",
                        ha="center",
                    )
                    ax.annotate(
                        e,
                        xy=(d, v),
                        xytext=(0, -15),
                        textcoords="offset points",
                        ha="center",
                        fontsize=8,
                    )

                ax.set_title("Value Creation Over Time")
                ax.set_xlabel("Date")
                ax.set_ylabel("Value")
                fig.autofmt_xdate()
                plt.tight_layout()
                st.pyplot(fig)

    #############################
    # Tab 2: Contributor Analysis
    #############################
    with tab2:
        st.subheader("Contributor Analysis")

        # Detailed breakdown of value recipients and their contributions
        if hasattr(capsule, "value_recipients") and capsule.value_recipients:
            st.markdown("### Value Recipients")
            recipients = capsule.value_recipients

            # Create visualization of recipient shares
            if isinstance(recipients, dict) and recipients:
                # Create pie chart of recipient shares
                fig = create_pie_chart(recipients, "Recipient Share Distribution")
                st.pyplot(fig)

                # Create table of recipient shares
                recipient_data = {"Recipient": [], "Share": [], "Percentage": []}
                for recipient, share in recipients.items():
                    recipient_data["Recipient"].append(recipient)
                    recipient_data["Share"].append(f"{share:.4f}")
                    recipient_data["Percentage"].append(f"{share*100:.2f}%")
                st.table(recipient_data)

                # Validate total
                total = sum(recipients.values())
                st.markdown(f"**Total Share: {total:.4f}**")
                if abs(total - 1.0) > 0.001:  # Allow small floating point error
                    st.warning(f"[WARN] Share sum ({total:.4f}) is not equal to 1.0")

        # Display contribution details if available
        if hasattr(capsule, "contribution_details") and capsule.contribution_details:
            st.markdown("### Contribution Analysis")

            # Go through each contributor and show their details
            for contributor, details in capsule.contribution_details.items():
                with st.expander(
                    f"{contributor} - {details.get('role', 'Contributor')}"
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(
                            f"**Contribution Type:** {details.get('contribution_type', 'N/A')}"
                        )
                        st.markdown(
                            f"**Effort Hours:** {details.get('effort_hours', 'N/A')}"
                        )
                        st.markdown(
                            f"**Justification:** {details.get('attribution_justification', 'N/A')}"
                        )

                    with col2:
                        # Show unique value adds as a bulleted list
                        value_adds = details.get("unique_value_adds", [])
                        if value_adds:
                            st.markdown("**Unique Value Adds:**")
                            for value in value_adds:
                                st.markdown(f"- {value}")

        # Show economic impact assessment if available
        if (
            hasattr(capsule, "economic_impact_assessment")
            and capsule.economic_impact_assessment
        ):
            st.markdown("### Economic Impact Assessment")
            impact = capsule.economic_impact_assessment

            # Display metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Direct Value", f"{impact.get('direct_value', 0):.2f}")
            with col2:
                st.metric(
                    "Projected Indirect Value",
                    f"{impact.get('projected_indirect_value', 0):.2f}",
                )

            # Value persistence
            persistence = impact.get("value_persistence", {})
            if persistence:
                st.markdown("#### Value Persistence")
                st.markdown(f"**Half-life:** {persistence.get('half_life', 'N/A')}")
                st.markdown(
                    f"**Residual Value Factor:** {persistence.get('residual_value_factor', 'N/A')}"
                )

                # Create decay curve visualization if we have a half-life
                half_life = persistence.get("half_life")
                if half_life and half_life.startswith("P"):
                    try:
                        # Parse ISO duration (simplistic)
                        days = 0
                        if "D" in half_life:
                            days = int(half_life.split("D")[0].replace("P", ""))

                        if days > 0:
                            # Create decay curve
                            residual = persistence.get("residual_value_factor", 0.3)
                            x = range(0, days * 3)  # 3x the half-life
                            y = [max(residual, (0.5 ** (t / days))) for t in x]

                            fig, ax = plt.subplots(figsize=(10, 4))
                            ax.plot(x, y, "-", color="#daa520", linewidth=2)
                            ax.axhline(
                                y=residual, color="red", linestyle="--", alpha=0.7
                            )
                            ax.set_title("Value Decay Over Time")
                            ax.set_xlabel("Days")
                            ax.set_ylabel("Remaining Value (proportion)")
                            ax.set_ylim(0, 1.1)
                            ax.text(
                                days * 2.5,
                                residual + 0.05,
                                "Residual Value",
                                color="red",
                            )
                            ax.grid(True, linestyle="--", alpha=0.7)
                            st.pyplot(fig)
                    except Exception as e:
                        st.warning(f"Could not render decay curve: {e}")

            # Value distribution equity
            equity = impact.get("value_distribution_equity", {})
            if equity:
                st.markdown("#### Value Distribution Equity")
                cols = st.columns(3)
                with cols[0]:
                    gini = equity.get("gini_coefficient", 0)
                    st.metric("Gini Coefficient", f"{gini:.2f}")
                    # Colorize based on inequality (lower is better)
                    color = "green" if gini < 0.3 else "orange" if gini < 0.5 else "red"
                    st.markdown(
                        f"<div style='height:5px;background-color:{color};border-radius:2px;'></div>",
                        unsafe_allow_html=True,
                    )

                with cols[1]:
                    st.metric(
                        "Top Share", f"{equity.get('top_contributor_share', 0):.2f}"
                    )

                with cols[2]:
                    st.metric(
                        "Min Share", f"{equity.get('min_contributor_share', 0):.2f}"
                    )

    #############################
    # Tab 3: Dividend Distribution
    #############################
    with tab3:
        st.subheader("Dividend Distribution")

        # Display dividend distribution with improved visualization
        if hasattr(capsule, "dividend_distribution") and capsule.dividend_distribution:
            try:
                if (
                    isinstance(capsule.dividend_distribution, dict)
                    and capsule.dividend_distribution
                ):
                    # Create enhanced pie chart
                    fig = create_pie_chart(
                        capsule.dividend_distribution, "Dividend Distribution"
                    )
                    st.pyplot(fig)

                    # Show value distribution breakdown with currency
                    st.markdown("### Distribution Breakdown")

                    # Show as a table with percentage and formatted values
                    recipients = list(capsule.dividend_distribution.keys())
                    dividends = list(capsule.dividend_distribution.values())
                    currency = capsule.metadata.get("currency", "")

                    # Calculate percentages for the table
                    total = sum(dividends)
                    percentages = [f"{(v/total)*100:.2f}%" for v in dividends]

                    # Create a formatted table with currency
                    dividend_data = {
                        "Recipient": recipients,
                        "Amount": [f"{v:,.2f} {currency}" for v in dividends],
                        "Percentage": percentages,
                    }
                    st.table(dividend_data)

                    # Validate total distribution
                    st.markdown(f"**Total Distribution: {total:,.2f} {currency}**")

                    # Create a bar chart showing distribution by recipient
                    fig, ax = plt.subplots(figsize=(10, 6))
                    bars = ax.bar(recipients, dividends, color="#daa520")

                    # Add value labels above bars
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(
                            bar.get_x() + bar.get_width() / 2.0,
                            height + 0.1,
                            f"{height:.1f}",
                            ha="center",
                            va="bottom",
                        )

                    ax.set_title("Dividend Distribution by Recipient")
                    ax.set_xlabel("Recipient")
                    ax.set_ylabel(f"Amount ({currency})")
                    plt.xticks(rotation=45, ha="right")
                    plt.tight_layout()
                    st.pyplot(fig)

                else:
                    # Handle non-dictionary data
                    st.json(capsule.dividend_distribution)
            except Exception as e:
                st.error(f"Error rendering dividend distribution: {str(e)}")

        # Display transaction reference and other metadata
        col1, col2 = st.columns(2)

        with col1:
            # Transaction reference
            if (
                hasattr(capsule, "transaction_reference")
                and capsule.transaction_reference
            ):
                st.markdown("### Transaction Reference")
                st.code(capsule.transaction_reference)

        with col2:
            # Transaction timestamp
            if (
                hasattr(capsule, "transaction_timestamp")
                and capsule.transaction_timestamp
            ):
                display_datetime_info(
                    capsule.transaction_timestamp, "Transaction Timestamp"
                )

        # Additional metadata
        st.markdown("### Additional Metadata")
        metadata_display = {}

        # Extract relevant fields from the metadata
        if hasattr(capsule, "metadata") and isinstance(capsule.metadata, dict):
            for key, value in capsule.metadata.items():
                if key not in ["currency"]:  # Skip fields already displayed
                    metadata_display[key] = value

        if metadata_display:
            st.json(metadata_display)


# Main function to render specialized content for UATP 7.0 capsule types
def render_uatp7_content(capsule):
    """Render specialized content for UATP 7.0 capsule types.

    This function dispatches to the appropriate specialized renderer based on capsule type.
    It includes error handling and validation to ensure that visualizations don't fail
    even when encountering unexpected or malformed capsule data.

    Args:
        capsule: A capsule object to visualize
    """
    if capsule is None:
        st.error("Cannot render visualization: No capsule provided")
        return

    # Extract capsule type with fallback
    capsule_type = getattr(capsule, "capsule_type", "")
    if not capsule_type:
        st.warning(
            "Capsule has no type information. Cannot render specialized visualization."
        )
        return

    # Display capsule ID and type info before specific content
    capsule_id = getattr(capsule, "capsule_id", "Unknown ID")
    st.subheader(f"Visualizing {capsule_type} Capsule")
    st.caption(f"ID: {capsule_id}")

    # Apply capsule type-specific color styling
    if capsule_type in UATP7_CAPSULE_TYPE_COLORS:
        capsule_color = UATP7_CAPSULE_TYPE_COLORS[capsule_type]
        st.markdown(
            f"<div style='background-color:{capsule_color};height:5px;border-radius:2px;margin-bottom:15px;'></div>",
            unsafe_allow_html=True,
        )

    # Try to dispatch to appropriate renderer with error handling
    try:
        if capsule_type == "Remix":
            render_remix_content(capsule)
        elif capsule_type == "TemporalSignature":
            render_temporal_signature_content(capsule)
        elif capsule_type == "ValueInception":
            render_value_inception_content(capsule)
        elif capsule_type == "SimulatedMalice":
            render_simulated_malice_content(capsule)
        elif capsule_type == "ImplicitConsent":
            render_implicit_consent_content(capsule)
        elif capsule_type == "SelfHallucination":
            render_self_hallucination_content(capsule)
        elif capsule_type == "Consent":
            render_consent_content(capsule)
        elif capsule_type == "TrustRenewal":
            render_trust_renewal_content(capsule)
        elif capsule_type == "CapsuleExpiration":
            render_capsule_expiration_content(capsule)
        elif capsule_type == "Governance":
            render_governance_content(capsule)
        elif capsule_type == "Economic":
            render_economic_content(capsule)
        else:
            st.info(
                f"No specialized visualization available for capsule type: {capsule_type}"
            )

    except Exception as e:
        st.error(f"Error rendering {capsule_type} visualization: {str(e)}")
        st.markdown("### Capsule Data (Debug View)")
        try:
            if hasattr(capsule, "to_dict"):
                st.json(capsule.to_dict())
            else:
                st.json(
                    {k: v for k, v in capsule.__dict__.items() if not k.startswith("_")}
                )
        except Exception:
            st.warning("Could not display capsule data")

    # Always show a horizontal divider after the visualization
    st.markdown("---")
