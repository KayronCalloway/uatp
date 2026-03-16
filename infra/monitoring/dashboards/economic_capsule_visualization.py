#!/usr/bin/env python3
"""
Test script for Economic Capsule visualization in the UATP 7.0 capsule engine.
This script creates a sample Economic capsule and launches a Streamlit
visualization server to display it with enhanced visualizations.
"""

import json
from datetime import datetime, timedelta

import streamlit as st
from visualizer.components.uatp7_inspector import render_uatp7_content

# Import required modules from the project
from capsules.specialized_capsules import EconomicCapsule

# Set page configuration
st.set_page_config(
    page_title="Economic Capsule Visualization Test",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


def create_test_economic_capsule():
    """Create a sample Economic capsule with realistic test data."""

    # Define basic economic capsule data
    capsule_data = {
        # Base capsule fields required by all specialized capsules
        "capsule_id": "ec-123456789",
        "capsule_type": "Economic",
        "timestamp": datetime.now().isoformat(),
        "creator_id": "creator-789",
        "creator_name": "Value Distribution System",
        "agent_id": "agent-456",
        "confidence": 0.95,
        "reasoning_trace": [
            "Analyzed contributor time logs and effort metrics",
            "Applied expertise multipliers based on role and experience",
            "Calculated proportional value attribution per contributor",
            "Validated distribution against fairness criteria",
        ],
        "signature": "sig_7e8f9a1b2c3d",
        # Economic capsule specific fields
        "economic_event_type": "Collaborative Content Creation",
        "value_amount": 1250.00,
        "value_calculation_method": "Time-weighted contribution analysis with expertise multiplier",
        "transaction_reference": "tx_48c76a9e3d21",
        "transaction_timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        # Required distribution fields
        "dividend_distribution": {
            "Alice": 550.00,
            "Bob": 375.00,
            "Carol": 225.00,
            "Dave": 100.00,
        },
        # Required recipients and their shares (normalized to sum to 1.0)
        "value_recipients": {"Alice": 0.44, "Bob": 0.30, "Carol": 0.18, "Dave": 0.08},
        # Required economic value metadata
        "economic_value": {
            "total_value": 1250.00,
            "value_type": "Monetary",
            "value_precision": "High",
            "distribution_fairness_score": 0.82,
            "value_creation_date": datetime.now().isoformat(),
        },
        # Additional metadata for enhanced visualizations
        "metadata": {
            "currency": "USD",
            "project_id": "proj-2023-article-series",
            "payment_status": "Completed",
            "value_category": "Content Creation",
        },
        # Detailed contribution analysis
        "contribution_details": {
            "Alice": {
                "role": "Lead Author",
                "contribution_type": "Original Content",
                "effort_hours": 15,
                "attribution_justification": "Primary research and drafting",
                "unique_value_adds": [
                    "Original research",
                    "Subject matter expertise",
                    "Quality assurance",
                ],
            },
            "Bob": {
                "role": "Co-Author",
                "contribution_type": "Content Development",
                "effort_hours": 10,
                "attribution_justification": "Extended analysis and technical review",
                "unique_value_adds": [
                    "Technical validation",
                    "Data analysis",
                    "Visualization creation",
                ],
            },
            "Carol": {
                "role": "Editor",
                "contribution_type": "Quality Enhancement",
                "effort_hours": 6,
                "attribution_justification": "Editorial refinement and fact-checking",
                "unique_value_adds": [
                    "Structural improvement",
                    "Clarity enhancement",
                    "Fact verification",
                ],
            },
            "Dave": {
                "role": "Graphics Designer",
                "contribution_type": "Visual Enhancement",
                "effort_hours": 4,
                "attribution_justification": "Created supporting visuals",
                "unique_value_adds": ["Custom illustrations", "Design elements"],
            },
        },
        # Value chain analysis
        "value_chain_analysis": {
            "input_value": 250.0,
            "value_added_steps": [
                {"step": "Research", "added_value": 300.0, "contributor": "Alice"},
                {
                    "step": "Content Creation",
                    "added_value": 350.0,
                    "contributor": "Alice and Bob",
                },
                {"step": "Editing", "added_value": 200.0, "contributor": "Carol"},
                {"step": "Visual Design", "added_value": 150.0, "contributor": "Dave"},
            ],
            "value_multipliers": [
                {"factor": "Accessibility", "multiplier": 1.2},
                {"factor": "Originality", "multiplier": 1.3},
                {"factor": "Authority", "multiplier": 1.15},
            ],
            "total_multiplier_effect": 1.8,
        },
        # Economic impact assessment
        "economic_impact_assessment": {
            "direct_value": 1250.0,
            "projected_indirect_value": 3750.0,
            "value_persistence": {
                "half_life": "P180D",  # ISO8601 duration format - 180 days
                "residual_value_factor": 0.25,
            },
            "value_distribution_equity": {
                "gini_coefficient": 0.28,
                "top_contributor_share": 0.44,
                "min_contributor_share": 0.08,
            },
        },
        # Value creation timeline
        "value_creation_history": [
            {
                "timestamp": (datetime.now() - timedelta(days=14)).isoformat(),
                "event": "Project Initiation",
                "value_estimate": 0,
            },
            {
                "timestamp": (datetime.now() - timedelta(days=10)).isoformat(),
                "event": "Research Complete",
                "value_estimate": 300,
            },
            {
                "timestamp": (datetime.now() - timedelta(days=7)).isoformat(),
                "event": "First Draft",
                "value_estimate": 600,
            },
            {
                "timestamp": (datetime.now() - timedelta(days=4)).isoformat(),
                "event": "Review & Edits",
                "value_estimate": 950,
            },
            {
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "event": "Final Delivery",
                "value_estimate": 1250,
            },
        ],
    }

    # Create the Economic capsule from the data
    return EconomicCapsule(**capsule_data)


def main():
    """Main function to run the visualization test."""
    st.title(" Economic Capsule Visualization Test")

    st.markdown(
        """
    This test demonstrates the enhanced visualization capabilities for UATP 7.0 Economic capsules.

    The visualization includes:
    - Multi-tab interface for different aspects of economic data
    - Interactive charts for value distribution and timeline
    - Contributor analysis with detailed breakdown
    - Value chain visualization
    """
    )

    # Create a test capsule
    economic_capsule = create_test_economic_capsule()

    # Display capsule as JSON for reference
    with st.expander("Economic Capsule Data (Raw)", expanded=False):
        # Use model_dump_json for Pydantic v2 compatibility
        if hasattr(economic_capsule, "model_dump_json"):
            capsule_json = economic_capsule.model_dump_json(indent=2)
        # Fallback for older Pydantic versions
        elif hasattr(economic_capsule, "json"):
            capsule_json = economic_capsule.json(indent=2)
        else:
            capsule_json = json.dumps(economic_capsule.__dict__, indent=2, default=str)

        st.json(json.loads(capsule_json))

    st.markdown("## Visualization")
    st.markdown("---")

    # Render the capsule using the enhanced visualization
    render_uatp7_content(economic_capsule)


if __name__ == "__main__":
    main()
