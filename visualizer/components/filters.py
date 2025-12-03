"""
Filters component for the UATP Capsule Visualizer.
"""

import datetime
from typing import List

import streamlit as st
from capsule_schema import Capsule
from cqss.scorer import CQSSScorer


def render_filters(capsules: List[Capsule]):
    """Render the filter controls for capsules."""
    st.markdown("## Filters")

    # Initialize filters in session state if not present
    if "filters" not in st.session_state:
        st.session_state["filters"] = {
            "capsule_types": [],
            "agents": [],
            "date_range": (None, None),
            "search_term": "",
            "min_cqss_score": 0.0,
        }

    # Extract unique capsule types and agents
    capsule_types = sorted({c.capsule_type for c in capsules})
    agents = sorted({c.agent_id for c in capsules})

    # Date range
    st.subheader("Date Range")
    # Find min and max dates in the capsules
    dates = []
    for c in capsules:
        if hasattr(c, "timestamp"):
            try:
                # Handle string timestamps and convert to datetime
                if isinstance(c.timestamp, str):
                    dates.append(
                        datetime.datetime.fromisoformat(
                            c.timestamp.replace("Z", "+00:00")
                        )
                    )
                elif isinstance(c.timestamp, datetime.datetime):
                    dates.append(c.timestamp)
            except (ValueError, AttributeError) as e:
                st.debug(
                    f"Error parsing timestamp for capsule {c.capsule_id[:8]}: {str(e)}"
                )

    if dates:
        try:
            min_date = min(dates).date()
            max_date = max(dates).date()

            date_range = st.date_input(
                "Select date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
            st.session_state["filters"]["date_range"] = (
                date_range if len(date_range) == 2 else (None, None)
            )
        except Exception as e:
            st.warning(f"Error setting up date range filter: {str(e)}")
            st.session_state["filters"]["date_range"] = (None, None)

    # Capsule type filter
    st.subheader("Capsule Types")
    selected_types = st.multiselect(
        "Select capsule types",
        options=capsule_types,
        default=[],
        placeholder="All types",
    )
    st.session_state["filters"]["capsule_types"] = selected_types

    # Agent filter
    st.subheader("Agents")
    selected_agents = st.multiselect(
        "Select agents", options=agents, default=[], placeholder="All agents"
    )
    st.session_state["filters"]["agents"] = selected_agents

    # CQSS score filter
    st.subheader("Quality Score (CQSS)")

    # Defensive check to handle incorrect value types in session state
    current_score_value = st.session_state.get("filters", {}).get("min_cqss_score", 0)
    if isinstance(current_score_value, list):
        current_score_value = current_score_value[0] if current_score_value else 0

    min_score = st.slider(
        "Minimum CQSS Score (0-100)",
        min_value=0,
        max_value=100,
        value=int(current_score_value),
        step=1,
        format="%d",
    )
    st.session_state["filters"]["min_cqss_score"] = min_score

    # Precompute CQSS scores only if they don't exist in the session state
    if "_capsule_scores" not in st.session_state.get("filters", {}):
        capsule_scores = {}
        for c in capsules:
            if isinstance(c, Capsule):
                try:
                    score_result = CQSSScorer.calculate_score(c)
                    if isinstance(score_result, dict) and "total_score" in score_result:
                        capsule_scores[c.capsule_id] = score_result["total_score"]
                    else:
                        st.warning(
                            f"Invalid score result format for capsule {c.capsule_id[:8]}"
                        )
                        capsule_scores[c.capsule_id] = 0
                except Exception as e:
                    st.debug(
                        f"Error calculating CQSS score for {c.capsule_id[:8]}: {str(e)}"
                    )
                    capsule_scores[c.capsule_id] = 0  # Assign a default score on error

        # Make sure filters key exists before setting capsule scores
        if "filters" not in st.session_state:
            st.session_state["filters"] = {}
        st.session_state["filters"]["_capsule_scores"] = capsule_scores

    # Text search
    st.subheader("Search")
    search_term = st.text_input(
        "Search in content",
        value=st.session_state["filters"]["search_term"],
        placeholder="Enter keywords...",
    )
    st.session_state["filters"]["search_term"] = search_term

    # Apply filters button
    if st.button("Apply Filters", type="primary"):
        st.rerun()

    # Reset filters button
    if st.button("Reset Filters"):
        st.session_state["filters"] = {
            "capsule_types": [],
            "agents": [],
            "date_range": (None, None),
            "search_term": "",
            "min_cqss_score": 0.0,
        }
        st.rerun()

    # Show current filter status
    active_filters = []

    if st.session_state["filters"]["capsule_types"]:
        types_str = ", ".join(st.session_state["filters"]["capsule_types"])
        active_filters.append(f"Types: {types_str}")

    if st.session_state["filters"]["agents"]:
        agents_str = ", ".join(st.session_state["filters"]["agents"])
        active_filters.append(f"Agents: {agents_str}")

    date_range = st.session_state["filters"]["date_range"]
    if date_range[0] and date_range[1]:
        active_filters.append(f"Dates: {date_range[0]} to {date_range[1]}")

    if st.session_state["filters"]["search_term"]:
        active_filters.append(f"Search: '{st.session_state['filters']['search_term']}'")

    if st.session_state["filters"]["min_cqss_score"] > 0:
        active_filters.append(
            f"Min Score: {st.session_state['filters']['min_cqss_score']}"
        )

    # Display active filters
    if active_filters:
        st.markdown("### Active Filters")
        for filter_str in active_filters:
            st.caption(f"• {filter_str}")
    else:
        st.caption("No active filters")
