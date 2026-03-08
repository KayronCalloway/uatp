"""
Navigation component for the UATP Capsule Visualizer.
"""

import streamlit as st

from visualizer.utils.config import nav_options
from visualizer.utils.state import set_view


def render_navigation():
    """Render the main navigation component."""
    st.markdown("## Navigation")

    current_view = st.session_state.get("current_view", "overview")

    # Create a cleaner navigation with icons
    col1, col2 = st.columns(2)

    with col1:
        for item in nav_options[:2]:
            button_label = f"{item['icon']} {item['label']}"
            if st.button(
                button_label,
                key=f"nav_{item['view']}",
                use_container_width=True,
                type="primary" if current_view == item["view"] else "secondary",
            ):
                set_view(item["view"])

    with col2:
        for item in nav_options[2:]:
            button_label = f"{item['icon']} {item['label']}"
            if st.button(
                button_label,
                key=f"nav_{item['view']}",
                use_container_width=True,
                type="primary" if current_view == item["view"] else "secondary",
            ):
                set_view(item["view"])

    # Display current selected capsule information
    st.markdown("---")
    selected_id = st.session_state.get("selected_capsule_id")
    if selected_id:
        # Make sure we're working with a string before slicing
        if isinstance(selected_id, str):
            display_id = f"{selected_id[:8]}..."
        else:
            display_id = str(selected_id)
        st.markdown(f"**Selected:** `{display_id}`")

        if st.button("Clear Selection"):
            st.session_state["selected_capsule_id"] = None
            st.rerun()

    # Pinned capsules section
    st.markdown("### Pinned Capsules")
    pinned = st.session_state.get("pinned_capsules", [])

    if not pinned:
        st.caption("Pin capsules for comparison (up to 3)")
    else:
        for pin_id in pinned:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"`{pin_id[:8]}...`")
            with col2:
                if st.button(
                    "[ERROR]", key=f"unpin_{pin_id}", help="Unpin this capsule"
                ):
                    pinned.remove(pin_id)
                    st.session_state["pinned_capsules"] = pinned
                    st.rerun()
