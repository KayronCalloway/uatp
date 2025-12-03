"""
UATP Capsule Visualizer - Modern Unified Workspace

A sophisticated tool for visualizing and analyzing UATP capsule chains with
interactive visualizations, context-aware panels, and an intuitive UI.
"""

from pathlib import Path

import streamlit as st

# Import local modules
from visualizer.components.analysis import render_analysis
from visualizer.components.filters import render_filters
from visualizer.components.force_graph import render_force_graph
from visualizer.components.header import render_header
from visualizer.components.heatmap import render_heatmap
from visualizer.components.inspector import render_inspector
from visualizer.components.navigation import render_navigation
from visualizer.components.sankey import render_sankey
from visualizer.components.timeline import render_timeline
from visualizer.utils.data_loader import load_capsules
from visualizer.utils.state import initialize_state

# Configuration
CHAIN_PATH = "capsule_chain.jsonl"


def main():
    """Main function to run the UATP Capsule Visualizer."""
    # Page configuration
    st.set_page_config(
        page_title="UATP Visualizer",
        page_icon="🔄",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize application state
    initialize_state()

    # Load data
    try:
        capsules = load_capsules(CHAIN_PATH)
    except Exception as e:
        st.error(f"Error loading capsules: {e}")
        st.stop()

    if not capsules:
        st.warning(
            f"No capsules found in '{CHAIN_PATH}'. Create a capsule chain first."
        )
        st.stop()

    # Create a mapping for quick lookups
    capsule_map = {c.capsule_id: c for c in capsules}

    # Apply CSS and design
    with open(Path(__file__).parent / "visualizer/assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Render header
    render_header()

    # Create layout
    with st.sidebar:
        render_navigation()
        render_filters(capsules)

    # Main content area
    current_view = st.session_state.get("current_view", "overview")

    if current_view == "overview":
        col1, col2 = st.columns([2, 1])
        with col1:
            render_force_graph(capsules, capsule_map)
        with col2:
            selected_id = st.session_state.get("selected_capsule_id")
            if selected_id and selected_id in capsule_map:
                render_inspector(capsule_map.get(selected_id))
            else:
                st.info("Select a capsule to see details.")

    elif current_view == "timeline":
        render_timeline(capsules, capsule_map)

    elif current_view == "sankey":
        render_sankey(capsules, capsule_map)

    elif current_view == "heatmap":
        render_heatmap(capsules, capsule_map)

    elif current_view == "analysis":
        render_analysis(capsules, capsule_map)

    elif current_view == "settings":
        st.header("Visualizer Settings")
        # Settings UI
        st.info("Settings panel coming soon.")


if __name__ == "__main__":
    main()
