"""Shared state management for UATP 7.0 visualizations.

This module provides utilities for managing shared state between different
visualization components, enabling features like cross-view highlighting.
"""

from typing import Optional

import streamlit as st


def initialize_visualization_state():
    """Initialize shared state variables for visualizations if they don't exist."""
    if "highlighted_capsule_id" not in st.session_state:
        st.session_state.highlighted_capsule_id = None


def get_highlighted_capsule_id() -> Optional[str]:
    """Get the currently highlighted capsule ID.

    Returns:
        String ID of highlighted capsule or None if none is highlighted
    """
    initialize_visualization_state()
    return st.session_state.highlighted_capsule_id


def set_highlighted_capsule_id(capsule_id: Optional[str]):
    """Set the highlighted capsule ID.

    Args:
        capsule_id: ID of capsule to highlight, or None to clear highlight
    """
    initialize_visualization_state()
    st.session_state.highlighted_capsule_id = capsule_id


def render_highlight_controls():
    """Render UI controls for managing highlighted capsules."""
    initialize_visualization_state()

    st.markdown("### Highlight Capsule")

    # Show current highlighted capsule
    if st.session_state.highlighted_capsule_id:
        st.info(
            f"Currently highlighting: {st.session_state.highlighted_capsule_id[:8]}..."
        )

        # Add button to clear highlight
        if st.button("Clear Highlight"):
            st.session_state.highlighted_capsule_id = None
            st.experimental_rerun()
    else:
        st.write("Enter a capsule ID to highlight it across all visualizations.")

    # Allow manual entry of capsule ID to highlight
    highlight_id = st.text_input("Capsule ID to highlight:")
    if highlight_id and highlight_id != st.session_state.highlighted_capsule_id:
        st.session_state.highlighted_capsule_id = highlight_id
        st.experimental_rerun()
