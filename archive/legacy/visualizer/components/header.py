"""
Header component for the UATP Capsule Visualizer.
"""

import streamlit as st

from visualizer.utils.state import toggle_dark_mode


def render_header():
    """Render the application header."""
    # Create columns for the header layout
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.title("UATP Capsule Visualizer")
        st.caption("Analyze and explore UATP capsule chains")

    with col2:
        # Dark mode toggle with a more refined appearance
        dark_mode = st.session_state.get("dark_mode", False)
        if st.toggle("Dark Mode", value=dark_mode, key="dark_mode_toggle"):
            if not dark_mode:  # Only toggle if state changed
                toggle_dark_mode()
                st.rerun()

    with col3:
        # Version information
        st.markdown(
            """
        <div style='text-align:right;margin-top:1.5rem;'>
            <span style='color:var(--text-muted);font-size:0.8rem;'>v1.0.0</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Subtle separator
    st.markdown(
        "<hr style='margin:0.5rem 0 1.5rem 0;opacity:0.2;'>", unsafe_allow_html=True
    )
