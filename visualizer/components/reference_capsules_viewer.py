"""
UATP Reference Capsules Viewer Component

This module provides a Streamlit interface for viewing reference high-quality capsules
that demonstrate optimal scoring in the CQSS system.
"""

from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from cqss.simulator import simulate_cqss_for_capsule

from visualizer.components.reference_capsules import (
    get_reference_capsule,
)


def render_reference_capsules_viewer():
    """Render a component for viewing reference high-quality capsules."""
    st.markdown("## Reference Capsules")
    st.markdown(
        """
    These reference capsules demonstrate ideal implementations with optimal CQSS scoring.
    Use them as examples of well-formed capsules for development and testing.
    """
    )

    # Add a banner with key information
    st.info(
        """
    **Reference Models Purpose**:
    - Demonstrate ideal UATP 7.0 capsule implementations
    - Serve as baseline for CQSS scoring comparison
    - Illustrate proper attribution and economic distribution
    - Provide templates for new capsule development
    """
    )

    # Create tabs for different types of reference capsules
    tabs = st.tabs(
        [
            "Ideal Capsule",
            "Economic Attribution",
            "Remix Attribution",
            "Comparative Analysis",
            "Compare Your Capsule",
        ]
    )

    # Tab 1: Ideal capsule with perfect CQSS score
    with tabs[0]:
        st.markdown("### Ideal Capsule Implementation")
        st.markdown(
            """
        This reference capsule demonstrates a perfect implementation with optimal:
        - Cryptographic signature
        - Detailed reasoning trace
        - High confidence scoring
        - Comprehensive ethical policy validation
        """
        )

        ideal_capsule = get_reference_capsule("ideal")
        if ideal_capsule:
            # Show CQSS score simulation
            st.markdown("#### CQSS Score Simulation")
            cqss_result = simulate_cqss_for_capsule(ideal_capsule)

            # Display components in columns
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Signature",
                    f"{cqss_result['signature_score']:.1f}/100",
                    delta="Excellent"
                    if cqss_result["signature_score"] > 80
                    else "Good",
                )

            with col2:
                st.metric(
                    "Reasoning",
                    f"{cqss_result['reasoning_score']:.1f}/100",
                    delta="Excellent"
                    if cqss_result["reasoning_score"] > 80
                    else "Good",
                )

            with col3:
                st.metric(
                    "Confidence",
                    f"{cqss_result['confidence_score']:.1f}/100",
                    delta="Excellent"
                    if cqss_result["confidence_score"] > 80
                    else "Good",
                )

            with col4:
                st.metric(
                    "Ethical Policy",
                    f"{cqss_result['ethical_score']:.1f}/100",
                    delta="Excellent" if cqss_result["ethical_score"] > 80 else "Good",
                )

            # Overall score
            overall_score = sum(
                [
                    cqss_result["signature_score"] * 0.25,
                    cqss_result["reasoning_score"] * 0.25,
                    cqss_result["confidence_score"] * 0.25,
                    cqss_result["ethical_score"] * 0.25,
                ]
            )

            st.markdown(f"#### Overall Score: {overall_score:.1f}/100")
            st.progress(overall_score / 100)

            # Display capsule details
            with st.expander("View Capsule Details"):
                # Basic info
                st.markdown(f"**ID:** `{ideal_capsule.capsule_id}`")
                st.markdown(f"**Type:** `{ideal_capsule.capsule_type}`")
                st.markdown(f"**Agent:** `{ideal_capsule.agent_id}`")
                st.markdown(f"**Timestamp:** `{ideal_capsule.timestamp}`")

                # Signature
                st.markdown("**Signature:**")
                st.code(ideal_capsule.signature[:50] + "...")

                # Metadata
                st.markdown("**Metadata:**")
                st.json(ideal_capsule.metadata)

            # Display reasoning trace
            with st.expander("View Reasoning Trace"):
                reasoning = ideal_capsule.metadata.get("reasoning_trace", {})

                # Show process
                st.markdown(f"**Process:** {reasoning.get('process', 'N/A')}")

                # Show steps
                st.markdown("**Steps:**")
                steps = reasoning.get("steps", [])
                for i, step in enumerate(steps):
                    st.markdown(
                        f"**Step {step.get('step')}:** {step.get('description')}"
                    )
                    st.markdown(f"- Outcome: {step.get('outcome')}")
                    st.markdown(f"- Confidence: {step.get('confidence'):.2f}")

                # Show justification
                st.markdown(
                    f"**Justification:** {reasoning.get('justification', 'N/A')}"
                )

                # Show citations
                citations = reasoning.get("citations", [])
                if citations:
                    st.markdown("**Citations:**")
                    for citation in citations:
                        st.markdown(
                            f"- {citation.get('source')}, Section {citation.get('section')}"
                        )

            # Display ethical policy validation
            with st.expander("View Ethical Policy Validation"):
                ethical = ideal_capsule.metadata.get("ethical_policy", {})

                # Show framework
                st.markdown(f"**Framework:** {ethical.get('framework', 'N/A')}")

                # Show policies checked
                policies = ethical.get("policies_checked", [])
                if policies:
                    st.markdown("**Policies Checked:**")
                    for policy in policies:
                        status = "[OK]" if policy.get("compliant") else "[ERROR]"
                        st.markdown(
                            f"{status} **{policy.get('policy')}**: {policy.get('evidence')}"
                        )

                # Show validation info
                st.markdown(
                    f"**Validation Level:** {ethical.get('validation_level', 'N/A')}"
                )
                st.markdown(
                    f"**Validation Timestamp:** {ethical.get('validation_timestamp', 'N/A')}"
                )
                st.markdown(
                    f"**Validation Authority:** {ethical.get('validation_authority', 'N/A')}"
                )
        else:
            st.error("Failed to generate ideal reference capsule")

    # Tab 2: Economic Attribution capsule
    with tabs[1]:
        st.markdown("### Economic Attribution Reference")
        st.markdown(
            """
        This reference economic capsule demonstrates optimal economic value attribution with:
        - Clear resource allocation model
        - Proportional value distribution
        - Transparent attribution structure
        - Well-defined residual rights
        """
        )

        economic_capsule = get_reference_capsule("economic")
        if economic_capsule:
            # Display economic event details
            st.markdown(
                f"**Economic Event Type:** {economic_capsule.economic_event_type}"
            )
            st.markdown(f"**Value Amount:** {economic_capsule.value_amount}")

            # Display resource allocation
            st.markdown("#### Resource Allocation")
            st.json(economic_capsule.resource_allocation)

            # Display value recipients in a table
            st.markdown("#### Value Recipients")

            recipients_df = pd.DataFrame(economic_capsule.value_recipients)

            # Add percentage column
            recipients_df["percentage"] = recipients_df["share"].apply(
                lambda x: f"{x*100:.1f}%"
            )

            # Display as table
            st.dataframe(recipients_df)

            # Display as pie chart
            fig, ax = plt.subplots()
            ax.pie(
                recipients_df["share"],
                labels=recipients_df["agent"],
                autopct="%1.1f%%",
                startangle=90,
            )
            ax.axis("equal")
            st.pyplot(fig)
        else:
            st.error("Failed to generate economic reference capsule")

    # Tab 3: Remix Attribution capsule
    with tabs[2]:
        st.markdown("### Remix Attribution Reference")
        st.markdown(
            """
        This reference remix capsule demonstrates proper attribution for derivative works with:
        - Clear identification of source material
        - Transparent transformation details
        - Fair attribution model
        - Well-structured contribution ratios
        """
        )

        remix_capsule = get_reference_capsule("remix")
        if remix_capsule:
            # Display remix details
            st.markdown(f"**Source Capsule:** `{remix_capsule.source_capsule_id}`")

            # Display attribution structure
            st.markdown("#### Attribution Structure")
            st.json(remix_capsule.attribution)

            # Show contribution visualization
            st.markdown("#### Contribution Breakdown")
            contrib_ratio = remix_capsule.attribution.get("contribution_ratio", 0.5)

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Original Contribution", f"{contrib_ratio*100:.1f}%")

            with col2:
                st.metric("New Elements", f"{(1-contrib_ratio)*100:.1f}%")

            # Progress bar visualization
            st.progress(contrib_ratio)

            # Show new elements
            new_elements = remix_capsule.attribution.get("new_elements", [])
            if new_elements:
                st.markdown("#### New Elements Added")
                for element in new_elements:
                    st.markdown(f"- {element}")
        else:
            st.error("Failed to generate remix reference capsule")

    # Tab 4: Comparative Analysis
    with tabs[3]:
        st.markdown("### Reference Capsule Comparison")
        st.markdown(
            """
        This analysis provides a side-by-side comparison of different reference capsule types.
        Use this to understand the unique features of each capsule type and how they contribute to CQSS scoring.
        """
        )

        # Get all reference capsules
        ideal_capsule = get_reference_capsule("ideal")
        economic_capsule = get_reference_capsule("economic")
        remix_capsule = get_reference_capsule("remix")

        # Ensure all capsules were generated
        if ideal_capsule and economic_capsule and remix_capsule:
            # Simulate CQSS scores for each capsule
            ideal_cqss = simulate_cqss_for_capsule(ideal_capsule)
            economic_cqss = simulate_cqss_for_capsule(economic_capsule)
            remix_cqss = simulate_cqss_for_capsule(remix_capsule)

            # Create comparison metrics
            st.markdown("#### CQSS Score Comparison")

            # Calculate overall scores
            ideal_score = sum(
                [
                    ideal_cqss["signature_score"] * 0.25,
                    ideal_cqss["reasoning_score"] * 0.25,
                    ideal_cqss["confidence_score"] * 0.25,
                    ideal_cqss["ethical_score"] * 0.25,
                ]
            )

            economic_score = sum(
                [
                    economic_cqss["signature_score"] * 0.25,
                    economic_cqss["reasoning_score"] * 0.25,
                    economic_cqss["confidence_score"] * 0.25,
                    economic_cqss["ethical_score"] * 0.25,
                ]
            )

            remix_score = sum(
                [
                    remix_cqss["signature_score"] * 0.25,
                    remix_cqss["reasoning_score"] * 0.25,
                    remix_cqss["confidence_score"] * 0.25,
                    remix_cqss["ethical_score"] * 0.25,
                ]
            )

            # Create comparison dataframe
            comparison_df = pd.DataFrame(
                {
                    "Metric": [
                        "Signature",
                        "Reasoning",
                        "Confidence",
                        "Ethical",
                        "Overall",
                    ],
                    "Ideal": [
                        ideal_cqss["signature_score"],
                        ideal_cqss["reasoning_score"],
                        ideal_cqss["confidence_score"],
                        ideal_cqss["ethical_score"],
                        ideal_score,
                    ],
                    "Economic": [
                        economic_cqss["signature_score"],
                        economic_cqss["reasoning_score"],
                        economic_cqss["confidence_score"],
                        economic_cqss["ethical_score"],
                        economic_score,
                    ],
                    "Remix": [
                        remix_cqss["signature_score"],
                        remix_cqss["reasoning_score"],
                        remix_cqss["confidence_score"],
                        remix_cqss["ethical_score"],
                        remix_score,
                    ],
                }
            )

            # Display comparison table
            st.dataframe(comparison_df.style.highlight_max(axis=1, color="#90EE90"))

            # Create a bar chart comparison
            st.markdown("#### Visual Score Comparison")

            fig, ax = plt.subplots(figsize=(10, 6))

            # Get data for plotting
            categories = comparison_df["Metric"].tolist()
            ideal_values = comparison_df["Ideal"].tolist()
            economic_values = comparison_df["Economic"].tolist()
            remix_values = comparison_df["Remix"].tolist()

            # Set width of bars
            barWidth = 0.25

            # Set positions of bars on X axis
            r1 = range(len(categories))
            r2 = [x + barWidth for x in r1]
            r3 = [x + barWidth for x in r2]

            # Create bars
            ax.bar(r1, ideal_values, width=barWidth, label="Ideal", color="#3498db")
            ax.bar(
                r2, economic_values, width=barWidth, label="Economic", color="#2ecc71"
            )
            ax.bar(r3, remix_values, width=barWidth, label="Remix", color="#e74c3c")

            # Add labels and title
            ax.set_xlabel("Metrics")
            ax.set_ylabel("Score")
            ax.set_title("Reference Capsule Score Comparison")
            ax.set_xticks([r + barWidth for r in range(len(categories))])
            ax.set_xticklabels(categories)
            ax.set_ylim(0, 100)
            ax.legend()

            # Display the chart
            st.pyplot(fig)

            # Display special features comparison
            st.markdown("#### Special Features Comparison")

            features_df = pd.DataFrame(
                {
                    "Feature": [
                        "Cryptographic Signature",
                        "Detailed Reasoning Trace",
                        "Economic Value Attribution",
                        "Source Attribution",
                        "Ethical Policy Validation",
                        "UATP 7.0 Compliance",
                    ],
                    "Ideal": ["[OK]", "[OK]", "[ERROR]", "[ERROR]", "[OK]", "[OK]"],
                    "Economic": ["[OK]", "[OK]", "[OK]", "[ERROR]", "[OK]", "[OK]"],
                    "Remix": ["[OK]", "[OK]", "[ERROR]", "[OK]", "[OK]", "[OK]"],
                }
            )

            st.dataframe(features_df)

            # Add usage recommendations
            st.markdown("#### Usage Recommendations")
            st.markdown(
                """
            | Capsule Type | Best Used For |
            |-------------|---------------|
            | **Ideal** | General content verification, baseline trust establishment |
            | **Economic** | Value distribution, reward allocation, incentive mechanisms |
            | **Remix** | Content attribution, derivative works, collaborative development |
            """
            )

        else:
            st.error(
                "Failed to generate one or more reference capsules for comparison."
            )

    # Tab 5: Compare Your Capsule
    with tabs[4]:
        st.markdown("### Compare Your Capsule to Reference Models")
        st.markdown(
            """
        This tool allows you to compare any capsule in your chain against the reference models.
        Select a capsule from your chain to see how it measures up against the ideal implementations.
        """
        )

        # Get the capsule map from session state (should be set in main app)
        capsule_map = st.session_state.get("capsule_map", {})

        if not capsule_map:
            st.warning(
                "No capsules found in your chain. Please add some capsules to compare."
            )
        else:
            # Display capsule selection
            capsule_ids = list(capsule_map.keys())
            selected_id = st.selectbox(
                "Select a capsule from your chain",
                capsule_ids,
                format_func=lambda x: f"{x[:8]}... ({capsule_map[x].capsule_type})"
                if x in capsule_map
                else x,
            )

            if selected_id and selected_id in capsule_map:
                user_capsule = capsule_map[selected_id]

                # Get the appropriate reference capsule based on user capsule type
                reference_type = "ideal"
                if hasattr(user_capsule, "economic_event_type"):
                    reference_type = "economic"
                elif hasattr(user_capsule, "source_capsule_id") and hasattr(
                    user_capsule, "attribution"
                ):
                    reference_type = "remix"

                reference_capsule = get_reference_capsule(reference_type)

                if reference_capsule:
                    # Show basic comparison
                    st.markdown(
                        f"#### Comparing Your {user_capsule.capsule_type} Capsule to {reference_type.capitalize()} Reference"
                    )

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("##### Your Capsule")
                        st.markdown(f"**ID:** `{user_capsule.capsule_id[:10]}...`")
                        st.markdown(f"**Type:** `{user_capsule.capsule_type}`")
                        st.markdown(f"**Agent:** `{user_capsule.agent_id}`")

                        # Show signature check
                        if (
                            hasattr(user_capsule, "signature")
                            and user_capsule.signature
                        ):
                            st.markdown("**Signature:** [OK] Present")
                        else:
                            st.markdown("**Signature:** [ERROR] Missing")

                        # Show reasoning trace check
                        if (
                            hasattr(user_capsule, "reasoning_trace")
                            and user_capsule.reasoning_trace
                        ):
                            st.markdown("**Reasoning Trace:** [OK] Present")
                        else:
                            st.markdown("**Reasoning Trace:** [ERROR] Missing")

                    with col2:
                        st.markdown("##### Reference Model")
                        st.markdown(f"**ID:** `{reference_capsule.capsule_id[:10]}...`")
                        st.markdown(f"**Type:** `{reference_capsule.capsule_type}`")
                        st.markdown(f"**Agent:** `{reference_capsule.agent_id}`")
                        st.markdown("**Signature:** [OK] Present")
                        st.markdown("**Reasoning Trace:** [OK] Present")

                    # Run CQSS simulation for both capsules
                    st.markdown("#### CQSS Score Comparison")

                    with st.spinner("Simulating CQSS scores..."):
                        try:
                            user_cqss = simulate_cqss_for_capsule(user_capsule)
                            ref_cqss = simulate_cqss_for_capsule(reference_capsule)

                            # Calculate overall scores
                            user_overall = sum(
                                [
                                    user_cqss.get("signature_score", 0) * 0.25,
                                    user_cqss.get("reasoning_score", 0) * 0.25,
                                    user_cqss.get("confidence_score", 0) * 0.25,
                                    user_cqss.get("ethical_score", 0) * 0.25,
                                ]
                            )

                            ref_overall = sum(
                                [
                                    ref_cqss.get("signature_score", 0) * 0.25,
                                    ref_cqss.get("reasoning_score", 0) * 0.25,
                                    ref_cqss.get("confidence_score", 0) * 0.25,
                                    ref_cqss.get("ethical_score", 0) * 0.25,
                                ]
                            )

                            # Display metrics side by side
                            (
                                metric_col1,
                                metric_col2,
                                metric_col3,
                                metric_col4,
                            ) = st.columns(4)

                            with metric_col1:
                                st.metric(
                                    "Signature",
                                    f"{user_cqss.get('signature_score', 0):.1f}/100",
                                    delta=f"{user_cqss.get('signature_score', 0) - ref_cqss.get('signature_score', 0):.1f}",
                                )

                            with metric_col2:
                                st.metric(
                                    "Reasoning",
                                    f"{user_cqss.get('reasoning_score', 0):.1f}/100",
                                    delta=f"{user_cqss.get('reasoning_score', 0) - ref_cqss.get('reasoning_score', 0):.1f}",
                                )

                            with metric_col3:
                                st.metric(
                                    "Confidence",
                                    f"{user_cqss.get('confidence_score', 0):.1f}/100",
                                    delta=f"{user_cqss.get('confidence_score', 0) - ref_cqss.get('confidence_score', 0):.1f}",
                                )

                            with metric_col4:
                                st.metric(
                                    "Ethical Policy",
                                    f"{user_cqss.get('ethical_score', 0):.1f}/100",
                                    delta=f"{user_cqss.get('ethical_score', 0) - ref_cqss.get('ethical_score', 0):.1f}",
                                )

                            # Overall score with progress bars
                            st.markdown("##### Overall Score Comparison")
                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown(f"**Your Capsule:** {user_overall:.1f}/100")
                                st.progress(user_overall / 100)

                            with col2:
                                st.markdown(
                                    f"**Reference Model:** {ref_overall:.1f}/100"
                                )
                                st.progress(ref_overall / 100)

                            # Visual comparison with bar chart
                            st.markdown("#### Visual Comparison")

                            fig, ax = plt.subplots(figsize=(10, 6))

                            # Define categories and values
                            categories = [
                                "Signature",
                                "Reasoning",
                                "Confidence",
                                "Ethical",
                                "Overall",
                            ]
                            user_values = [
                                user_cqss.get("signature_score", 0),
                                user_cqss.get("reasoning_score", 0),
                                user_cqss.get("confidence_score", 0),
                                user_cqss.get("ethical_score", 0),
                                user_overall,
                            ]
                            reference_values = [
                                ref_cqss.get("signature_score", 0),
                                ref_cqss.get("reasoning_score", 0),
                                ref_cqss.get("confidence_score", 0),
                                ref_cqss.get("ethical_score", 0),
                                ref_overall,
                            ]

                            # Set width and positions
                            barWidth = 0.35
                            r1 = range(len(categories))
                            r2 = [x + barWidth for x in r1]

                            # Create bars
                            ax.bar(
                                r1,
                                user_values,
                                width=barWidth,
                                label="Your Capsule",
                                color="#3498db",
                            )
                            ax.bar(
                                r2,
                                reference_values,
                                width=barWidth,
                                label="Reference Model",
                                color="#2ecc71",
                            )

                            # Styling
                            ax.set_xlabel("Metrics")
                            ax.set_ylabel("Score")
                            ax.set_title("Your Capsule vs Reference Model")
                            ax.set_xticks(
                                [r + barWidth / 2 for r in range(len(categories))]
                            )
                            ax.set_xticklabels(categories)
                            ax.set_ylim(0, 100)
                            ax.legend()

                            # Display chart
                            st.pyplot(fig)

                            # Display improvement recommendations
                            st.markdown("#### Improvement Recommendations")

                            # Generate recommendations based on score comparisons
                            recommendations = []

                            if (
                                user_cqss.get("signature_score", 0)
                                < ref_cqss.get("signature_score", 0) - 10
                            ):
                                recommendations.append(
                                    " **Signature Verification**: Ensure your capsule uses proper cryptographic signatures and key management."
                                )

                            if (
                                user_cqss.get("reasoning_score", 0)
                                < ref_cqss.get("reasoning_score", 0) - 10
                            ):
                                recommendations.append(
                                    " **Reasoning Trace**: Include more detailed reasoning steps with explicit confidence levels."
                                )

                            if (
                                user_cqss.get("confidence_score", 0)
                                < ref_cqss.get("confidence_score", 0) - 10
                            ):
                                recommendations.append(
                                    " **Confidence Scoring**: Improve confidence metrics and ensure they accurately reflect certainty levels."
                                )

                            if (
                                user_cqss.get("ethical_score", 0)
                                < ref_cqss.get("ethical_score", 0) - 10
                            ):
                                recommendations.append(
                                    " **Ethical Policy**: Add explicit ethical policy validations and framework references."
                                )

                            if not recommendations:
                                st.success(
                                    " Your capsule is performing well compared to the reference model!"
                                )
                            else:
                                for rec in recommendations:
                                    st.markdown(rec)

                        except Exception as e:
                            st.error(f"Error simulating CQSS scores: {str(e)}")
                else:
                    st.error("Failed to load reference capsule for comparison.")
            else:
                st.info("Please select a capsule to compare.")

        # Add explanation about the comparison
        with st.expander("About Capsule Comparison"):
            st.markdown(
                """
            This tool helps you understand how your capsules compare to reference implementations in terms of CQSS scoring.

            **How it works:**
            1. We simulate CQSS scoring for both your capsule and the appropriate reference model
            2. We compare the scores across key metrics (signature, reasoning, confidence, ethics)
            3. We identify areas for improvement based on score differences
            4. We provide targeted recommendations to enhance your capsule's quality

            **Key Metrics Explained:**
            - **Signature**: Evaluates the cryptographic integrity and verification
            - **Reasoning**: Assesses the quality and depth of the reasoning trace
            - **Confidence**: Measures appropriate confidence scoring and calibration
            - **Ethical Policy**: Evaluates adherence to ethical frameworks and policies
            - **Overall**: Weighted combination of all individual metrics

            Use these insights to iteratively improve your capsule implementations towards optimal CQSS scores.
            """
            )


def add_reference_capsule_to_chain(
    engine, capsule_type: str = "ideal"
) -> Optional[str]:
    """Add a reference capsule to the chain.

    Args:
        engine: The capsule engine instance
        capsule_type: Type of reference capsule to add

    Returns:
        The capsule ID if successful, None otherwise
    """
    capsule = get_reference_capsule(capsule_type)
    if capsule:
        try:
            engine.add_capsule_to_chain(capsule)
            return capsule.capsule_id
        except Exception as e:
            st.error(f"Failed to add reference capsule: {str(e)}")
            return None
    return None
