"""
Inspector component for displaying detailed information about selected capsules.
"""

import datetime
from typing import Optional

import streamlit as st
from capsule_schema import Capsule
from cqss.scorer import CQSSScorer

from visualizer.components.reasoning_analysis import render_reasoning_analysis
from visualizer.utils.capsule_compat import (
    capsule_to_dict,
    get_capsule_attr,
    get_capsule_id,
    get_capsule_metadata,
    get_capsule_type,
    get_confidence_score,
    get_parent_capsule_id,
    get_reasoning_steps,
)
from visualizer.utils.colors import CAPSULE_TYPE_COLORS, get_cqss_color
from visualizer.utils.state import get_pinned_capsule, toggle_pin_capsule


def render_inspector(capsule: Optional[Capsule] = None):
    """Render the capsule inspector panel with detailed information."""
    st.header("Capsule Inspector")

    if capsule is None:
        st.info("Select a capsule to view its details")
        return

    # Add error handling for the entire inspector
    try:
        # Create a container for the inspector with a subtle border
        with st.container():
            # Get the color for this capsule type
            capsule_type = get_capsule_type(capsule)
            color = CAPSULE_TYPE_COLORS.get(
                capsule_type, CAPSULE_TYPE_COLORS["DEFAULT"]
            )

            # Header with capsule type and color indicator
            st.markdown(
                f"""
            <div style='display:flex;align-items:center;margin-bottom:1rem;'>
                <div style='width:12px;height:12px;border-radius:50%;background-color:{color};margin-right:8px;'></div>
                <h3 style='margin:0;font-weight:500;'>{capsule_type.replace('_', ' ').title()} Capsule</h3>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Main info section
            col1, col2 = st.columns([3, 1])

            with col1:
                st.caption("Capsule ID")
                capsule_id = get_capsule_id(capsule)
                st.code(capsule_id or "Unknown", language=None)

                # Display agent information
                st.caption("Agent")
                agent_id = get_capsule_attr(capsule, "agent_id", default="Unknown")
                st.markdown(f"**{agent_id}**")

                # Display timestamp
                st.caption("Timestamp")
                timestamp = get_capsule_attr(capsule, "timestamp")
                if timestamp:
                    if isinstance(timestamp, datetime.datetime):
                        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        formatted_time = str(timestamp)
                    st.markdown(f"**{formatted_time}**")
                else:
                    st.markdown("**Unknown**")

            with col2:
                # Actions for this capsule
                if st.button(" Pin", help="Pin this capsule for comparison"):
                    toggle_pin_capsule(get_capsule_id(capsule))
                    st.rerun()

                # Display confidence score from metadata if available
                confidence_score = get_confidence_score(capsule)

                if confidence_score is not None:
                    st.caption("Confidence Score")
                    confidence_color = get_cqss_color(confidence_score * 100)
                    st.markdown(
                        f"""
                    <div style='text-align:center;'>
                        <div style='font-size:1.2rem;font-weight:bold;color:{confidence_color};'>
                            {confidence_score:.2%}
                        </div>
                        <div style='background:#e0e0e0;height:4px;border-radius:2px;margin-top:3px;'>
                            <div style='background:{confidence_color};width:{confidence_score * 100}%;height:4px;border-radius:2px;'></div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                # Calculate and display CQSS Score
                try:
                    result = CQSSScorer.calculate_score(capsule)
                    score = result["total_score"]
                    breakdown = result["breakdown"]

                    st.caption("CQSS Score")
                    score_color = get_cqss_color(score)
                    st.markdown(
                        f"""
                    <div style='text-align:center;'>
                        <div style='font-size:1.5rem;font-weight:bold;color:{score_color};'>
                            {score:.2f}
                        </div>
                        <div style='background:#e0e0e0;height:6px;border-radius:3px;margin-top:5px;'>
                            <div style='background:{score_color};width:{score}%;height:6px;border-radius:3px;'></div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                    # Show breakdown in expander
                    with st.expander("Score Breakdown"):
                        st.json(breakdown)
                except Exception as e:
                    st.caption("CQSS Score")
                    st.error(f"Error calculating score: {str(e)}")

            # Chain relationship section
            st.subheader("Chain Relationships")
            col1, col2 = st.columns(2)

            with col1:
                st.caption("Previous Capsule")

                # Robust capsule parent handling (dict vs object compatibility)
                previous_capsule_id = get_parent_capsule_id(capsule)

                if previous_capsule_id:
                    if st.button("View Previous", key="view_prev"):
                        st.session_state["selected_capsule_id"] = previous_capsule_id
                        st.rerun()
                    st.code(previous_capsule_id, language=None)
                else:
                    st.text("None (Root Capsule)")

            with col2:
                st.caption("Merged From")

                # Robust merged capsule handling
                merged_from_ids = get_capsule_attr(capsule, "merged_from_ids")

                if merged_from_ids:
                    for i, merged_id in enumerate(merged_from_ids):
                        if st.button(f"View Merged {i+1}", key=f"view_merged_{i}"):
                            st.session_state["selected_capsule_id"] = merged_id
                            st.rerun()
                        st.code(merged_id, language=None)
                else:
                    st.text("None")

            # Content section with expandable areas
            st.subheader("Capsule Content")

            # Determine what content to show based on capsule type
            content = get_capsule_attr(capsule, "content")
            if content:
                with st.expander("Content", expanded=True):
                    st.markdown(content)

            # Use the compatibility function for reasoning traces
            reasoning_steps = get_reasoning_steps(capsule)
            if reasoning_steps:
                with st.expander("Reasoning Trace", expanded=True):
                    # Display as structured steps
                    st.markdown("### Reasoning Steps")
                    for i, step in enumerate(reasoning_steps, 1):
                        if isinstance(step, dict):
                            step_type = step.get("step_type", "unknown")
                            content = step.get("content", "")
                            confidence = step.get("confidence", step.get("weight", 1.0))

                            # Color code by step type
                            type_colors = {
                                "analysis": "#2196F3",
                                "consideration": "#FF9800",
                                "conclusion": "#4CAF50",
                                "problem_detection": "#F44336",
                                "technical_content": "#9C27B0",
                                "debugging_content": "#FF5722",
                                "significance_detection": "#607D8B",
                            }
                            step_color = type_colors.get(step_type, "#90A4AE")

                            st.markdown(
                                f"""
                            <div style='margin-bottom: 1rem; padding: 1rem; border-left: 4px solid {step_color}; background-color: #f8f9fa;'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                                    <div style='font-weight: bold; color: {step_color}; text-transform: capitalize;'>
                                        Step {i}: {step_type.replace('_', ' ')}
                                    </div>
                                    <div style='font-size: 0.9rem; color: #666;'>
                                        Confidence: {confidence:.1%}
                                    </div>
                                </div>
                                <div style='color: #333;'>
                                    {content}
                                </div>
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(f"**Step {i}:** {step}")

            metadata = get_capsule_metadata(capsule)
            if metadata:
                with st.expander("Metadata"):
                    st.json(metadata)

            # Raw data view (for developers)
            with st.expander("Raw Data"):
                # Convert to serializable format for display
                serializable_data = capsule_to_dict(capsule)
                st.json(serializable_data)

            # Add tabs for different views of the capsule
            st.markdown("---")
            inspector_tabs = ["Content", "Reasoning Analysis"]
            selected_tab = st.radio("View", inspector_tabs, horizontal=True)

            if selected_tab == "Reasoning Analysis":
                # Check if we have a reasoning trace to analyze
                reasoning_trace = get_capsule_attr(capsule, "reasoning_trace")
                if reasoning_trace:
                    # Get pinned capsule for comparison if available
                    pinned_capsule_id = st.session_state.get("pinned_capsule_id")
                    comparison_capsule = None

                    if pinned_capsule_id and pinned_capsule_id != get_capsule_id(
                        capsule
                    ):
                        comparison_capsule = get_pinned_capsule()

                    # Render the reasoning analysis component
                    render_reasoning_analysis(capsule, comparison_capsule)
                else:
                    st.info("This capsule doesn't have a reasoning trace to analyze.")
            else:
                # Default content view is already rendered above
                pass

    except Exception as e:
        st.error(f"Error rendering capsule inspector: {str(e)}")
        st.error(
            "This may be due to capsule format compatibility issues. Please check the console for details."
        )
        # For debugging, show the raw capsule data
        with st.expander("Debug Information"):
            st.write(f"Capsule type: {type(capsule)}")
            if hasattr(capsule, "__dict__"):
                st.json(capsule.__dict__)
            else:
                st.write(str(capsule))
