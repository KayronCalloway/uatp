"""Filter utilities for UATP 7.0 visualizations.

This module provides functions for filtering capsule chains based on various
criteria like capsule type, agent ID, time range, and text search.
"""

import datetime
from typing import Callable, List, Optional
from dateutil.parser import parse as parse_date
import streamlit as st
from capsule_schema import Capsule

from visualizer.components.visualization_shared_state import get_highlighted_capsule_id


def _get_capsule_datetime(c: Capsule) -> Optional[datetime.datetime]:
    """Safely get the timestamp as a datetime object from a capsule, which can be a dict or an object."""
    ts = None
    if isinstance(c, dict):
        ts = c.get("timestamp")
    else:
        ts = getattr(c, "timestamp", None)

    if ts is None:
        return None

    if isinstance(ts, datetime.datetime):
        return ts

    if isinstance(ts, datetime.date):
        return datetime.datetime.combine(ts, datetime.time.min)

    if isinstance(ts, str):
        try:
            return parse_date(ts)
        except (ValueError, TypeError):
            return None

    return None


def filter_capsules(
    capsules: List[Capsule],
    capsule_types: Optional[List[str]] = None,
    agent_ids: Optional[List[str]] = None,
    min_confidence: Optional[float] = None,
    date_range: Optional[tuple] = None,
    search_text: Optional[str] = None,
) -> List[Capsule]:
    """Filter a list of capsules based on multiple criteria.

    Args:
        capsules: List of capsules to filter
        capsule_types: Optional list of capsule types to include
        agent_ids: Optional list of agent IDs to include
        min_confidence: Optional minimum confidence threshold
        date_range: Optional tuple of (start_date, end_date) for filtering
        search_text: Optional text to search for in capsule content or metadata

    Returns:
        Filtered list of capsules
    """
    if not capsules:
        return []

    filtered_capsules = capsules.copy()

    # Filter by capsule type
    if capsule_types:
        filtered_capsules = [
            c
            for c in filtered_capsules
            if getattr(c, "capsule_type", None) in capsule_types
        ]

    # Filter by agent ID
    if agent_ids:
        filtered_capsules = [
            c for c in filtered_capsules if getattr(c, "agent_id", None) in agent_ids
        ]

    # Filter by confidence
    if min_confidence is not None:
        filtered_capsules = [
            c
            for c in filtered_capsules
            if getattr(c, "confidence", 0) >= min_confidence
        ]

    # Filter by date range
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        if start_date and end_date:
            filtered_capsules = [
                c
                for c in filtered_capsules
                if (
                    (dt := _get_capsule_datetime(c))
                    and start_date <= dt.replace(tzinfo=None) <= end_date
                )
            ]

    # Filter by search text
    if search_text:
        search_text = search_text.lower()
        filtered_capsules = []

        for capsule in capsules:
            # Search in capsule ID
            if (
                hasattr(capsule, "capsule_id")
                and search_text in str(capsule.capsule_id).lower()
            ):
                filtered_capsules.append(capsule)
                continue

            # Search in capsule content
            if (
                hasattr(capsule, "content")
                and search_text in str(capsule.content).lower()
            ):
                filtered_capsules.append(capsule)
                continue

            # Search in metadata if it exists
            if hasattr(capsule, "metadata"):
                metadata_str = str(capsule.metadata).lower()
                if search_text in metadata_str:
                    filtered_capsules.append(capsule)
                    continue

    return filtered_capsules


def render_filter_controls(
    capsules: List[Capsule], on_filter_change: Callable[[List[Capsule]], None] = None
) -> List[Capsule]:
    """Render filter controls for capsule visualizations.

    Args:
        capsules: List of all capsules
        on_filter_change: Optional callback when filters change

    Returns:
        Filtered list of capsules
    """
    if not capsules:
        return []

    with st.expander("Filter Capsules", expanded=False):
        st.markdown("### Apply Filters")

        # Extract unique values for filters
        all_capsule_types = sorted(
            list({getattr(c, "capsule_type", "Unknown") for c in capsules})
        )
        all_agent_ids = sorted(
            list({getattr(c, "agent_id", "Unknown") for c in capsules})
        )

        # Search text
        search_text = st.text_input(
            "Search in capsule content",
            placeholder="Enter text to search...",
            key="search_text_filter",
        )

        # Type filter
        st.markdown("#### Filter by Type")
        selected_types = st.multiselect(
            "Select capsule types",
            options=all_capsule_types,
            default=[],
            key="type_filter",
        )

        # Agent filter
        st.markdown("#### Filter by Agent")
        selected_agents = st.multiselect(
            "Select agent IDs", options=all_agent_ids, default=[], key="agent_filter"
        )

        # Confidence filter
        st.markdown("#### Filter by Confidence")
        min_confidence = st.slider(
            "Minimum confidence",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
            key="confidence_filter",
        )

        # Date range filter
        st.markdown("#### Filter by Date Range")

        # Extract min/max dates
        all_dates = [dt.date() for c in capsules if (dt := _get_capsule_datetime(c))]
        min_date = min(all_dates, default=datetime.date.today())
        max_date = max(all_dates, default=datetime.date.today())

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", min_date)
        with col2:
            end_date = st.date_input("End date", max_date)

        # Convert dates to datetime for comparison
        start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
        end_datetime = datetime.datetime.combine(end_date, datetime.time.max)

        # Additional filter options if needed
        st.markdown("#### Additional Actions")

        # Jump to highlighted capsule
        highlighted_id = get_highlighted_capsule_id()
        if highlighted_id:
            if st.button(f"Jump to highlighted capsule ({highlighted_id[:8]}...)"):
                st.session_state.filter_only_highlighted = True

        # Clear all filters button
        if st.button("Clear All Filters"):
            # Reset all filter values
            search_text = ""
            selected_types = []
            selected_agents = []
            min_confidence = 0.0
            start_datetime = datetime.datetime.combine(min_date, datetime.time.min)
            end_datetime = datetime.datetime.combine(max_date, datetime.time.max)

            # Clear session state flags
            if "filter_only_highlighted" in st.session_state:
                st.session_state.filter_only_highlighted = False

            # Force a rerun to reset the UI
            st.experimental_rerun()

    # Apply filters
    filtered_capsules = filter_capsules(
        capsules,
        capsule_types=selected_types if selected_types else None,
        agent_ids=selected_agents if selected_agents else None,
        min_confidence=min_confidence if min_confidence > 0 else None,
        date_range=(start_datetime, end_datetime),
        search_text=search_text if search_text else None,
    )

    # Special case: filter for only highlighted capsule if requested
    if st.session_state.get("filter_only_highlighted", False) and highlighted_id:
        filtered_capsules = [
            c for c in filtered_capsules if c.capsule_id == highlighted_id
        ]
        if not filtered_capsules:
            st.warning(
                f"Highlighted capsule {highlighted_id[:8]}... not found in current view"
            )
            # Reset the filter for next time
            st.session_state.filter_only_highlighted = False

    # Show filter summary
    filter_count = len(filtered_capsules)
    total_count = len(capsules)

    if filter_count < total_count:
        st.info(f"Showing {filter_count} of {total_count} capsules (filtered)")

    # Call the callback if provided
    if on_filter_change:
        on_filter_change(filtered_capsules)

    return filtered_capsules
