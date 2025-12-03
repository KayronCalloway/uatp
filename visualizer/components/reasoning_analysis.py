"""
Reasoning Analysis component for the UATP Capsule Visualizer.

This component provides detailed analysis and visualization of reasoning traces
within capsules, leveraging the ReasoningValidator and ReasoningAnalyzer modules.
"""

from typing import Optional

import altair as alt
import pandas as pd
import streamlit as st
from capsule_schema import Capsule
from reasoning.analyzer import ReasoningAnalyzer
from reasoning.trace import ReasoningTrace
from reasoning.validator import ReasoningValidator


def render_reasoning_analysis(
    capsule: Optional[Capsule] = None, comparison_capsule: Optional[Capsule] = None
):
    """
    Render detailed reasoning analysis for a capsule.

    Args:
        capsule: The primary capsule to analyze
        comparison_capsule: Optional second capsule for comparison
    """
    st.header("Reasoning Analysis")

    if capsule is None:
        st.info("Select a capsule to analyze its reasoning trace")
        return

    # Get the reasoning trace in structured format
    trace = capsule.get_reasoning_trace_as_structured()

    # Check if there are reasoning steps to analyze
    if not trace.steps:
        st.warning("This capsule doesn't have a reasoning trace to analyze.")
        return

    # Create tab layout for different analysis views
    tabs = ["Validation", "Pattern Analysis", "Step Flow", "Comparison"]

    if comparison_capsule is None:
        tabs = tabs[:-1]  # Remove comparison tab if no comparison capsule

    selected_tab = st.radio("Analysis View", tabs, horizontal=True)

    if selected_tab == "Validation":
        render_validation_view(trace, capsule.capsule_id)
    elif selected_tab == "Pattern Analysis":
        render_pattern_analysis(trace, capsule.capsule_id)
    elif selected_tab == "Step Flow":
        render_step_flow(trace)
    elif selected_tab == "Comparison" and comparison_capsule is not None:
        comparison_trace = comparison_capsule.get_reasoning_trace_as_structured()
        render_comparison_view(
            trace, comparison_trace, capsule.capsule_id, comparison_capsule.capsule_id
        )


def render_validation_view(trace: ReasoningTrace, capsule_id: str):
    """Render the validation results for a reasoning trace."""
    st.subheader("Reasoning Validation")

    # Get validation results
    validation_result = ReasoningValidator.validate(trace)

    # Display the overall score with a gauge
    score = validation_result.score
    color = get_score_color(score)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Quality Score")
        st.markdown(
            f"""
        <div style='text-align:center;'>
            <div style='font-size:2.5rem;font-weight:bold;color:{color};'>
                {score:.1f}
            </div>
            <div style='font-size:1rem;color:gray;'>out of 100</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        # Create a gauge chart for the score
        chart_data = pd.DataFrame(
            {"value": [score], "color": [color], "category": ["Score"]}
        )

        base = alt.Chart(chart_data).encode(
            theta=alt.Theta("value:Q", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("color:N", scale=None),
        )

        arc = base.mark_arc(innerRadius=70, outerRadius=100)
        text = base.mark_text(align="center", baseline="middle", fontSize=20).encode(
            text="value:Q"
        )

        st.altair_chart(arc + text, use_container_width=True)

    # Display validation issues and suggestions
    if validation_result.issues:
        st.subheader("Issues Identified")
        for issue in validation_result.issues:
            severity = issue["severity"]
            icon = "🔴" if severity == "error" else "🟡"
            st.markdown(f"{icon} **{severity.upper()}:** {issue['message']}")
    else:
        st.success("No issues found in the reasoning trace.")

    if validation_result.suggestions:
        st.subheader("Improvement Suggestions")
        for suggestion in validation_result.suggestions:
            st.markdown(f"💡 {suggestion}")


def render_pattern_analysis(trace: ReasoningTrace, capsule_id: str):
    """Render pattern analysis for a reasoning trace."""
    st.subheader("Reasoning Pattern Analysis")

    # Get analysis results
    analysis = ReasoningAnalyzer.analyze_trace(trace)

    # Display step type distribution
    st.markdown("### Step Type Distribution")

    # Convert step type distribution to DataFrame
    types_data = []
    for step_type, percentage in analysis["type_distribution"].items():
        types_data.append({"Step Type": step_type, "Percentage": percentage * 100})

    df_types = pd.DataFrame(types_data)
    if not df_types.empty:
        chart = (
            alt.Chart(df_types)
            .mark_bar()
            .encode(
                x=alt.X("Step Type:N", sort="-y"),
                y=alt.Y("Percentage:Q", title="Percentage (%)"),
                color=alt.Color("Step Type:N"),
                tooltip=["Step Type", "Percentage"],
            )
            .properties(height=200)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No step type distribution data available.")

    # Display detected patterns
    if "patterns" in analysis and analysis["patterns"]:
        st.markdown("### Detected Reasoning Patterns")
        for pattern in analysis["patterns"]:
            st.markdown(f"✓ **{pattern.replace('_', ' ').title()}**")
    else:
        st.info("No specific reasoning patterns detected.")

    # Display confidence information
    if "average_confidence" in analysis:
        st.markdown("### Confidence Analysis")
        avg_confidence = analysis["average_confidence"] * 100
        color = get_score_color(avg_confidence)

        st.markdown(
            f"""
        <div style='display:flex;align-items:center;'>
            <div style='margin-right:10px;'>Average Confidence:</div>
            <div style='font-weight:bold;color:{color};'>{avg_confidence:.1f}%</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_step_flow(trace: ReasoningTrace):
    """Render the flow of reasoning steps as a directed graph."""
    st.subheader("Reasoning Step Flow")

    # Generate flow analysis
    analysis = ReasoningAnalyzer.analyze_trace(trace)
    flow_analysis = analysis.get("flow", {})

    # Display flow quality information
    if flow_analysis:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Flow Quality")
            quality = flow_analysis.get("flow_quality", "unknown")
            quality_color = "#4CAF50" if quality == "good" else "#FFA726"
            st.markdown(
                f"""
            <div style='font-size:1.2rem;font-weight:bold;color:{quality_color};text-transform:capitalize;'>
                {quality}
            </div>
            """,
                unsafe_allow_html=True,
            )

            confidence_trend = flow_analysis.get("confidence_trend", "unknown")
            st.markdown(
                f"**Confidence Trend:** {confidence_trend.replace('_', ' ').title()}"
            )

        with col2:
            st.markdown("### Step Placement")
            early_placement = flow_analysis.get("early_step_placement", "unknown")
            late_placement = flow_analysis.get("late_step_placement", "unknown")

            early_color = "#4CAF50" if early_placement == "good" else "#FFA726"
            late_color = "#4CAF50" if late_placement == "good" else "#FFA726"

            st.markdown(
                f"""
            <div>Early steps: <span style='color:{early_color};font-weight:bold;text-transform:capitalize;'>{early_placement}</span></div>
            <div>Late steps: <span style='color:{late_color};font-weight:bold;text-transform:capitalize;'>{late_placement}</span></div>
            """,
                unsafe_allow_html=True,
            )

    # Create step flow visualization
    st.markdown("### Step Flow Visualization")

    # Create a DataFrame for the steps
    steps_data = []
    for i, step in enumerate(trace):
        steps_data.append(
            {
                "step": i + 1,
                "content": step.content[:50]
                + ("..." if len(step.content) > 50 else ""),
                "type": step.step_type.value,
                "confidence": step.confidence * 100,
            }
        )

    df_steps = pd.DataFrame(steps_data)

    # Create a visualization that shows the flow of steps with confidence
    chart = (
        alt.Chart(df_steps)
        .mark_line(point=True)
        .encode(
            x=alt.X("step:O", title="Step Number"),
            y=alt.Y(
                "confidence:Q", title="Confidence (%)", scale=alt.Scale(domain=[0, 100])
            ),
            color=alt.Color("type:N", title="Step Type"),
            tooltip=["step", "type", "confidence", "content"],
        )
        .properties(height=300)
    )

    st.altair_chart(chart, use_container_width=True)

    # Display the step sequence table
    st.markdown("### Step Sequence")
    st.table(df_steps[["step", "type", "confidence", "content"]])


def render_comparison_view(
    trace1: ReasoningTrace, trace2: ReasoningTrace, capsule_id1: str, capsule_id2: str
):
    """Render a comparison between two reasoning traces."""
    st.subheader("Reasoning Trace Comparison")

    # Get comparison results
    comparison = ReasoningAnalyzer.compare_traces(trace1, trace2)

    # Display basic comparison metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Step Count Difference", comparison["step_count_diff"])
    with col2:
        st.metric(
            "Confidence Difference", f"{comparison['confidence_diff'] * 100:.1f}%"
        )
    with col3:
        common_patterns = len(comparison.get("common_patterns", []))
        st.metric("Common Patterns", common_patterns)

    # Display type distribution differences
    st.markdown("### Step Type Distribution Differences")

    type_diffs = []
    for step_type, diff in comparison["type_distribution_diffs"].items():
        type_diffs.append(
            {
                "Step Type": step_type,
                "Difference": diff * 100,
                "Higher In": "Trace 2"
                if diff > 0
                else "Trace 1"
                if diff < 0
                else "Equal",
            }
        )

    df_diffs = pd.DataFrame(type_diffs)
    if not df_diffs.empty:
        chart = (
            alt.Chart(df_diffs)
            .mark_bar()
            .encode(
                x=alt.X("Step Type:N"),
                y=alt.Y("Difference:Q", title="Difference (%)"),
                color=alt.Color(
                    "Higher In:N",
                    scale=alt.Scale(
                        domain=["Trace 1", "Trace 2", "Equal"],
                        range=["#2196F3", "#FF5722", "#9E9E9E"],
                    ),
                ),
                tooltip=["Step Type", "Difference", "Higher In"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No type distribution difference data available.")

    # Display pattern differences
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Common Patterns")
        common_patterns = comparison.get("common_patterns", [])
        if common_patterns:
            for pattern in common_patterns:
                st.markdown(f"✓ {pattern.replace('_', ' ').title()}")
        else:
            st.info("No common patterns found.")

    with col2:
        st.markdown("### Unique Patterns")
        unique_patterns = comparison.get("unique_patterns", {})

        st.markdown(f"**In Trace 1 ({capsule_id1[:8]}...):**")
        trace1_patterns = unique_patterns.get("trace1", [])
        if trace1_patterns:
            for pattern in trace1_patterns:
                st.markdown(f"- {pattern.replace('_', ' ').title()}")
        else:
            st.info("No unique patterns.")

        st.markdown(f"**In Trace 2 ({capsule_id2[:8]}...):**")
        trace2_patterns = unique_patterns.get("trace2", [])
        if trace2_patterns:
            for pattern in trace2_patterns:
                st.markdown(f"- {pattern.replace('_', ' ').title()}")
        else:
            st.info("No unique patterns.")


def get_score_color(score: float) -> str:
    """Return a color based on a score (0-100)."""
    if score >= 80:
        return "#4CAF50"  # Green
    elif score >= 60:
        return "#2196F3"  # Blue
    elif score >= 40:
        return "#FFC107"  # Amber
    elif score >= 20:
        return "#FF9800"  # Orange
    else:
        return "#F44336"  # Red
