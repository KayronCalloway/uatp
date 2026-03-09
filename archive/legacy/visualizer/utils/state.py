"""
State management utilities for the UATP Capsule Visualizer.
"""

from typing import Any, Dict, Optional

import streamlit as st

from visualizer.utils.config import nav_options


def initialize_state():
    """Initialize or update the application state in session state."""
    # Navigation state
    if "current_view" not in st.session_state:
        st.session_state["current_view"] = "overview"

    # UI preferences
    if "dark_mode" not in st.session_state:
        st.session_state["dark_mode"] = False

    # Selection state
    if "selected_capsule_id" not in st.session_state:
        st.session_state["selected_capsule_id"] = None

    # Comparison state
    if "pinned_capsules" not in st.session_state:
        st.session_state["pinned_capsules"] = []

    # Filter state
    if "filters" not in st.session_state:
        st.session_state["filters"] = {
            "capsule_types": [],
            "agents": [],
            "date_range": (None, None),
            "search_term": "",
            "min_cqss_score": 0.0,
        }

    # Visualization settings
    if "viz_settings" not in st.session_state:
        st.session_state["viz_settings"] = {
            "detail_level": "medium",
            "graph_physics": True,
            "show_timestamps": True,
            "show_reasoning": False,
        }


def get_state() -> Dict[str, Any]:
    """Get the current application state."""
    return {
        "current_view": st.session_state.get("current_view", "overview"),
        "dark_mode": st.session_state.get("dark_mode", False),
        "selected_capsule_id": st.session_state.get("selected_capsule_id", None),
        "pinned_capsules": st.session_state.get("pinned_capsules", []),
        "filters": st.session_state.get("filters", {}),
        "viz_settings": st.session_state.get("viz_settings", {}),
    }


def update_state(key: str, value: Any):
    """Update a specific state value."""
    if key in st.session_state:
        st.session_state[key] = value
    else:
        raise KeyError(f"Invalid state key: {key}")


def select_capsule(capsule_id: str):
    """Select a capsule by ID."""
    st.session_state["selected_capsule_id"] = capsule_id


def toggle_pin_capsule(capsule_id: str):
    """Toggle whether a capsule is pinned for comparison."""
    if capsule_id in st.session_state["pinned_capsules"]:
        st.session_state["pinned_capsules"].remove(capsule_id)
        st.session_state["pinned_capsule_id"] = None
    else:
        if len(st.session_state["pinned_capsules"]) < 3:  # Limit to 3 pinned capsules
            st.session_state["pinned_capsules"].append(capsule_id)
            st.session_state["pinned_capsule_id"] = capsule_id


def get_pinned_capsule() -> Optional[Any]:
    """Get the currently pinned capsule for comparison.

    Returns:
        The pinned capsule object, or None if no capsule is pinned
    """
    pinned_id = st.session_state.get("pinned_capsule_id")
    if not pinned_id:
        return None

    # Access the capsule_map from session state
    capsule_map = st.session_state.get("capsule_map", {})
    return capsule_map.get(pinned_id)


def set_view(view_name: str):
    """Set the current view, validating against the single source of truth in navigation.py."""
    valid_views = [item["view"] for item in nav_options]
    if view_name in valid_views:
        st.session_state["current_view"] = view_name
    else:
        raise ValueError(f"Invalid view name: {view_name}")


def toggle_dark_mode():
    """Toggle dark mode on/off."""
    st.session_state["dark_mode"] = not st.session_state["dark_mode"]
