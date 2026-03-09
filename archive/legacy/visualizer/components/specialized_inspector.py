"""Enhanced inspector component for displaying detailed information about specialized capsule types."""

from typing import Optional, Union

import streamlit as st
from capsule_schema import Capsule
from capsules.specialized_capsules import (
    SpecializedCapsule,
)
from cqss.scorer import CQSSScorer

from visualizer.components.uatp7_inspector import render_uatp7_content
from visualizer.utils.colors import CAPSULE_TYPE_COLORS, get_cqss_color
from visualizer.utils.state import toggle_pin_capsule


def render_specialized_inspector(
    capsule: Optional[Union[Capsule, SpecializedCapsule]] = None,
):
    """Render an enhanced inspector panel with specialized fields for each capsule type."""
    if capsule is None:
        st.info("Select a capsule to view its details")
        return

    st.header("Capsule Inspector")

    # Create a container for the inspector with a subtle border
    with st.container():
        # Get the color for this capsule type
        color = CAPSULE_TYPE_COLORS.get(
            capsule.capsule_type, CAPSULE_TYPE_COLORS["DEFAULT"]
        )

        # Header with capsule type and color indicator
        st.markdown(
            f"""
        <div style='display:flex;align-items:center;margin-bottom:1rem;'>
            <div style='width:12px;height:12px;border-radius:50%;background-color:{color};margin-right:8px;'></div>
            <h3 style='margin:0;font-weight:500;'>{capsule.capsule_type} Capsule</h3>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Main info section
        col1, col2 = st.columns([3, 1])

        with col1:
            st.caption("Capsule ID")
            st.code(capsule.capsule_id, language=None)

            # Display agent information
            st.caption("Agent")
            st.markdown(f"**{capsule.agent_id}**")

            # Display timestamp
            st.caption("Timestamp")
            formatted_time = (
                capsule.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                if hasattr(capsule.timestamp, "strftime")
                else str(capsule.timestamp)
            )
            st.markdown(f"**{formatted_time}**")

        with col2:
            # Actions for this capsule
            if st.button(" Pin", help="Pin this capsule for comparison"):
                toggle_pin_capsule(capsule.capsule_id)
                st.rerun()

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
            if capsule.previous_capsule_id:
                if st.button("View Previous", key="view_prev"):
                    st.session_state["selected_capsule_id"] = (
                        capsule.previous_capsule_id
                    )
                    st.rerun()
                st.code(capsule.previous_capsule_id, language=None)
            else:
                st.text("None (Root Capsule)")

        with col2:
            st.caption("Merged From")
            if hasattr(capsule, "merged_from_ids") and capsule.merged_from_ids:
                for i, merged_id in enumerate(capsule.merged_from_ids):
                    if st.button(f"View Merged {i+1}", key=f"view_merged_{i}"):
                        st.session_state["selected_capsule_id"] = merged_id
                        st.rerun()
                    st.code(merged_id, language=None)
            else:
                st.text("None")

        # Specialized content based on capsule type
        st.subheader("Capsule Content")
        render_specialized_content(capsule)


def render_specialized_content(capsule):
    """Render specialized content based on the capsule type."""
    # Get the capsule type
    capsule_type = getattr(capsule, "capsule_type", "")

    # Common content for all capsule types
    with st.expander("Reasoning Trace", expanded=True):
        if hasattr(capsule, "reasoning_trace"):
            reasoning = capsule.reasoning_trace
            if hasattr(reasoning, "to_string_list"):
                for step in reasoning.to_string_list():
                    st.markdown(f"- {step}")
            elif isinstance(reasoning, list):
                for step in reasoning:
                    if isinstance(step, dict) and "content" in step:
                        st.markdown(f"- {step['content']}")
                    elif isinstance(step, str):
                        st.markdown(f"- {step}")
            else:
                st.text("No structured reasoning available")

    # Metadata for all capsule types
    with st.expander("Metadata"):
        if hasattr(capsule, "metadata") and capsule.metadata:
            st.json(capsule.metadata)

    # UATP 6.0 capsule types
    if capsule_type == "Refusal":
        render_refusal_content(capsule)
    elif capsule_type == "Introspective":
        render_introspective_content(capsule)
    elif capsule_type == "Joint":
        render_joint_content(capsule)
    elif capsule_type == "Meta":
        render_meta_content(capsule)
    elif capsule_type == "Influence":
        render_influence_content(capsule)
    elif capsule_type == "Perspective":
        render_perspective_content(capsule)
    elif capsule_type == "Lifecycle":
        render_lifecycle_content(capsule)
    elif capsule_type == "Embodied":
        render_embodied_content(capsule)
    elif capsule_type == "AncestralKnowledge":
        render_ancestral_knowledge_content(capsule)
    # UATP 7.0 capsule types
    elif capsule_type in [
        "Remix",
        "TemporalSignature",
        "ValueInception",
        "SimulatedMalice",
        "ImplicitConsent",
        "SelfHallucination",
        "Consent",
        "TrustRenewal",
        "CapsuleExpiration",
        "Governance",
        "Economic",
    ]:
        render_uatp7_content(capsule)
    else:
        st.info(
            f"No specialized visualization available for capsule type: {capsule_type}"
        )

    # Raw data view (for developers)
    with st.expander("Raw Data"):
        st.json(
            capsule.model_dump() if hasattr(capsule, "model_dump") else capsule.__dict__
        )


def render_refusal_content(capsule):
    """Render specialized content for Refusal capsules."""
    with st.expander("Refusal Details", expanded=True):
        if hasattr(capsule, "reason_for_rejection") and capsule.reason_for_rejection:
            st.subheader("Reason for Rejection")
            st.info(capsule.reason_for_rejection)

        if hasattr(capsule, "ethical_policy_id") and capsule.ethical_policy_id:
            st.markdown(f"**Policy ID:** {capsule.ethical_policy_id}")

        if (
            hasattr(capsule, "alternative_suggestions")
            and capsule.alternative_suggestions
        ):
            st.subheader("Alternative Suggestions")
            for i, suggestion in enumerate(capsule.alternative_suggestions):
                st.markdown(f"{i+1}. {suggestion}")

        if hasattr(capsule, "refusal_category") and capsule.refusal_category:
            st.markdown(f"**Category:** {capsule.refusal_category}")


def render_introspective_content(capsule):
    """Render specialized content for Introspective capsules."""
    with st.expander("Introspection Details", expanded=True):
        if hasattr(capsule, "uncertainty_factors") and capsule.uncertainty_factors:
            st.subheader("Uncertainty Factors")
            for factor in capsule.uncertainty_factors:
                st.markdown(f"- {factor}")

        if hasattr(capsule, "alternative_paths") and capsule.alternative_paths:
            st.subheader("Alternative Reasoning Paths")
            for i, path in enumerate(capsule.alternative_paths):
                with st.expander(f"Alternative {i+1}"):
                    if isinstance(path, dict):
                        for key, value in path.items():
                            st.markdown(f"**{key}:** {value}")
                    else:
                        st.markdown(str(path))

        if hasattr(capsule, "epistemic_state") and capsule.epistemic_state:
            st.subheader("Epistemic State")
            st.info(capsule.epistemic_state)


def render_joint_content(capsule):
    """Render specialized content for Joint capsules."""
    with st.expander("Joint Decision Details", expanded=True):
        if hasattr(capsule, "human_id") and capsule.human_id:
            st.markdown(f"**Human ID:** {capsule.human_id}")

        if hasattr(capsule, "agreement_terms") and capsule.agreement_terms:
            st.subheader("Agreement Terms")
            st.info(capsule.agreement_terms)

        if hasattr(capsule, "collaboration_context") and capsule.collaboration_context:
            st.subheader("Collaboration Context")
            st.json(capsule.collaboration_context)

        if hasattr(capsule, "human_signature") and capsule.human_signature:
            st.subheader("Human Signature")
            st.code(
                capsule.human_signature[:32] + "..."
                if len(capsule.human_signature) > 32
                else capsule.human_signature
            )


def render_meta_content(capsule):
    """Render specialized content for Meta capsules."""
    with st.expander("Meta Reflection Details", expanded=True):
        if hasattr(capsule, "target_capsule_ids") and capsule.target_capsule_ids:
            st.subheader("Target Capsules")
            for i, capsule_id in enumerate(capsule.target_capsule_ids):
                if st.button(f"View Target {i+1}", key=f"view_target_{i}"):
                    st.session_state["selected_capsule_id"] = capsule_id
                    st.rerun()
                st.code(capsule_id)

        if hasattr(capsule, "reflection_type") and capsule.reflection_type:
            st.markdown(f"**Reflection Type:** {capsule.reflection_type}")

        if hasattr(capsule, "detected_issues") and capsule.detected_issues:
            st.subheader("Detected Issues")
            for i, issue in enumerate(capsule.detected_issues):
                with st.expander(f"Issue {i+1}"):
                    if isinstance(issue, dict):
                        for key, value in issue.items():
                            st.markdown(f"**{key}:** {value}")
                    else:
                        st.markdown(str(issue))

        if hasattr(capsule, "suggested_resolutions") and capsule.suggested_resolutions:
            st.subheader("Suggested Resolutions")
            for i, resolution in enumerate(capsule.suggested_resolutions):
                with st.expander(f"Resolution {i+1}"):
                    if isinstance(resolution, dict):
                        for key, value in resolution.items():
                            st.markdown(f"**{key}:** {value}")
                    else:
                        st.markdown(str(resolution))


def render_influence_content(capsule):
    """Render specialized content for Influence capsules."""
    with st.expander("Influence Details", expanded=True):
        if hasattr(capsule, "influence_type") and capsule.influence_type:
            st.markdown(f"**Influence Type:** {capsule.influence_type}")

        if hasattr(capsule, "target_audience") and capsule.target_audience:
            st.markdown(f"**Target Audience:** {capsule.target_audience}")

        if hasattr(capsule, "intended_effect") and capsule.intended_effect:
            st.subheader("Intended Effect")
            st.info(capsule.intended_effect)

        if (
            hasattr(capsule, "ethical_considerations")
            and capsule.ethical_considerations
        ):
            st.subheader("Ethical Considerations")
            for consideration in capsule.ethical_considerations:
                st.markdown(f"- {consideration}")

        if hasattr(capsule, "influence_measurement") and capsule.influence_measurement:
            st.subheader("Influence Measurement")
            # Create a bar chart for influence metrics
            if isinstance(capsule.influence_measurement, dict):
                chart_data = {"Metric": [], "Value": []}
                for metric, value in capsule.influence_measurement.items():
                    chart_data["Metric"].append(metric)
                    chart_data["Value"].append(value)

                import pandas as pd

                df = pd.DataFrame(chart_data)
                st.bar_chart(df.set_index("Metric"))
            else:
                st.json(capsule.influence_measurement)


def render_perspective_content(capsule):
    """Render specialized content for Perspective capsules."""
    with st.expander("Perspective Details", expanded=True):
        if hasattr(capsule, "perspective_type") and capsule.perspective_type:
            st.markdown(f"**Perspective Type:** {capsule.perspective_type}")

        if (
            hasattr(capsule, "perspective_description")
            and capsule.perspective_description
        ):
            st.subheader("Perspective Description")
            st.info(capsule.perspective_description)

        if hasattr(capsule, "fork_of") and capsule.fork_of:
            st.subheader("Fork Origin")
            if st.button("View Origin", key="view_fork_origin"):
                st.session_state["selected_capsule_id"] = capsule.fork_of
                st.rerun()
            st.code(capsule.fork_of)

            if hasattr(capsule, "fork_reason") and capsule.fork_reason:
                st.markdown(f"**Fork Reason:** {capsule.fork_reason}")

        if (
            hasattr(capsule, "alternative_perspectives")
            and capsule.alternative_perspectives
        ):
            st.subheader("Alternative Perspectives")
            for i, perspective in enumerate(capsule.alternative_perspectives):
                with st.expander(f"Alternative {i+1}"):
                    if isinstance(perspective, dict):
                        for key, value in perspective.items():
                            st.markdown(f"**{key}:** {value}")
                    else:
                        st.markdown(str(perspective))


def render_lifecycle_content(capsule):
    """Render specialized content for Lifecycle capsules."""
    with st.expander("Lifecycle Details", expanded=True):
        if hasattr(capsule, "event_type") and capsule.event_type:
            event_icon = (
                ""
                if capsule.event_type == "startup"
                else ""
                if capsule.event_type == "shutdown"
                else ""
            )
            st.markdown(f"**Event Type:** {event_icon} {capsule.event_type}")

        if hasattr(capsule, "affected_components") and capsule.affected_components:
            st.subheader("Affected Components")
            for component in capsule.affected_components:
                st.markdown(f"- {component}")

        if hasattr(capsule, "event_trigger") and capsule.event_trigger:
            st.markdown(f"**Event Trigger:** {capsule.event_trigger}")

        if hasattr(capsule, "expected_duration") and capsule.expected_duration:
            st.markdown(f"**Expected Duration:** {capsule.expected_duration}")

        if hasattr(capsule, "system_state") and capsule.system_state:
            st.subheader("System State")
            st.json(capsule.system_state)


def render_embodied_content(capsule):
    """Render specialized content for Embodied capsules."""
    with st.expander("Embodied Interaction Details", expanded=True):
        if hasattr(capsule, "interaction_type") and capsule.interaction_type:
            st.markdown(f"**Interaction Type:** {capsule.interaction_type}")

        if hasattr(capsule, "physical_context") and capsule.physical_context:
            st.subheader("Physical Context")
            st.json(capsule.physical_context)

        if hasattr(capsule, "sensor_data") and capsule.sensor_data:
            st.subheader("Sensor Data")
            st.json(capsule.sensor_data)

            # If there's image data, try to display it
            if (
                "image_data" in capsule.sensor_data
                and capsule.sensor_data["image_data"]
            ):
                try:
                    import base64
                    import io

                    from PIL import Image

                    image_data = base64.b64decode(capsule.sensor_data["image_data"])
                    image = Image.open(io.BytesIO(image_data))
                    st.image(image, caption="Captured Image")
                except Exception as e:
                    st.warning(f"Could not display image: {e}")

        if hasattr(capsule, "temporal_sequence") and capsule.temporal_sequence:
            st.subheader("Temporal Sequence")
            for i, event in enumerate(capsule.temporal_sequence):
                with st.expander(f"Event {i+1}"):
                    st.json(event)

        if hasattr(capsule, "spatial_reference") and capsule.spatial_reference:
            st.subheader("Spatial Reference")
            st.json(capsule.spatial_reference)


def render_ancestral_knowledge_content(capsule):
    """Render specialized content for Ancestral Knowledge capsules."""
    with st.expander("Knowledge Details", expanded=True):
        if hasattr(capsule, "knowledge_domain") and capsule.knowledge_domain:
            st.markdown(f"**Knowledge Domain:** {capsule.knowledge_domain}")

        if hasattr(capsule, "knowledge_source") and capsule.knowledge_source:
            st.markdown(f"**Source:** {capsule.knowledge_source}")

        if hasattr(capsule, "canonical_reference") and capsule.canonical_reference:
            st.markdown(f"**Canonical Reference:** {capsule.canonical_reference}")

        if (
            hasattr(capsule, "knowledge_confidence")
            and capsule.knowledge_confidence is not None
        ):
            st.markdown(f"**Knowledge Confidence:** {capsule.knowledge_confidence:.2f}")
            # Display confidence visualization
            conf = float(capsule.knowledge_confidence)
            conf_color = "green" if conf > 0.8 else "orange" if conf > 0.5 else "red"
            st.markdown(
                f"""
            <div style='background:#e0e0e0;height:8px;border-radius:4px;width:100%;'>
                <div style='background:{conf_color};width:{conf*100}%;height:8px;border-radius:4px;'></div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        if hasattr(capsule, "attribution") and capsule.attribution:
            st.subheader("Attribution")
            for i, attr in enumerate(capsule.attribution):
                if isinstance(attr, dict):
                    attrs = [f"**{k}:** {v}" for k, v in attr.items()]
                    st.markdown(f"{i+1}. {', '.join(attrs)}")
                else:
                    st.markdown(f"{i+1}. {attr}")

        if hasattr(capsule, "access_rights") and capsule.access_rights:
            st.subheader("Access Rights")
            st.json(capsule.access_rights)
