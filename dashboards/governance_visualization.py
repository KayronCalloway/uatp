from datetime import datetime, timedelta

import streamlit as st
from capsules.specialized_capsules import GovernanceCapsule

from visualizer.components.uatp7_inspector import render_governance_content


def main():
    """
    Test script to demonstrate the enhanced Governance capsule visualization.
    """
    st.set_page_config(
        page_title="UATP 7.0 Governance Visualization Test",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.title(" Governance Capsule Visualization Test")
    st.markdown(
        """
    This test demonstrates the enhanced visualization components for UATP 7.0 Governance capsules.
    The visualization includes a multi-tab interface with:
    - **Overview**: Summary of governance action and approval status
    - **Policy & Action**: Detailed information about the governance policy and action
    - **Stakeholder Votes**: Visual representation of voting results and stakeholder positions
    - **Implementation**: Implementation timeline and affected systems
    """
    )

    # Create a sample Governance capsule
    governance_capsule = create_sample_governance_capsule()

    # Add a divider
    st.markdown("---")
    st.subheader("Governance Capsule Visualization")

    # Render the capsule using the enhanced visualization
    render_governance_content(governance_capsule)


def create_sample_governance_capsule():
    """
    Create a sample Governance capsule with realistic data.
    """
    # Calculate timestamps
    now = datetime.now()
    vote_end_time = now - timedelta(days=2)
    vote_start_time = vote_end_time - timedelta(days=7)
    implementation_time = now + timedelta(days=14)

    # Base capsule data
    capsule_data = {
        # Required base capsule fields
        "capsule_id": "governance_test_789012",
        "capsule_type": "Governance",
        "agent_id": "governance-coordinator-001",
        "confidence": 0.98,
        "signature": "0xfe9a7c02e5d8b6a13c87d9e15f02c27a98c734b2",
        "reasoning_trace": [
            "Governance proposal submitted by authorized stakeholder",
            "Voting threshold achieved with 78% approval",
            "Decision ratified by governance committee",
        ],
        # Governance-specific fields
        "governance_type": "PolicyUpdate",
        "policy_id": "UATP-GOV-2025-042",
        "decision_makers": [
            "governance-committee-chair",
            "technical-director",
            "ethics-advisor",
            "stakeholder-representative",
        ],
        "decision_rationale": """
        This policy update introduces enhanced transparency requirements for
        automated decision-making processes. The update addresses concerns raised
        by stakeholders regarding visibility into AI reasoning chains and attribution
        of decision factors. The committee reviewed implementation feasibility and
        determined the benefits outweigh the technical complexity of implementation.
        """,
        "affected_scopes": [
            "automated-decision-systems",
            "reasoning-trace-requirements",
            "explainability-standards",
            "attribution-requirements",
        ],
        "voting_results": {
            "total_votes": 45,
            "approval_votes": 35,
            "rejection_votes": 8,
            "abstention_votes": 2,
        },
        # Additional fields for enhanced visualization
        "governance_action": "Update transparency requirements for automated decision-making processes",
        "governance_details": {
            "proposal_id": "PROP-2025-137",
            "proposal_date": vote_start_time.isoformat(),
            "voting_period": {
                "start": vote_start_time.isoformat(),
                "end": vote_end_time.isoformat(),
            },
            "implementation_timeline": {
                "review_phase": (now + timedelta(days=1)).isoformat(),
                "development_phase": (now + timedelta(days=7)).isoformat(),
                "testing_phase": (now + timedelta(days=10)).isoformat(),
                "deployment_phase": implementation_time.isoformat(),
            },
            "priority_level": "High",
            "legal_compliance": "Required for EU AI Act compliance",
            "technical_complexity": "Medium",
            "affected_systems": [
                {
                    "system_id": "decision-engine-core",
                    "impact_level": "High",
                    "modification_required": "Update reasoning trace format and storage",
                },
                {
                    "system_id": "explainability-module",
                    "impact_level": "High",
                    "modification_required": "Add attribution tracking",
                },
                {
                    "system_id": "user-interface",
                    "impact_level": "Medium",
                    "modification_required": "Add transparency displays",
                },
                {
                    "system_id": "logging-system",
                    "impact_level": "Low",
                    "modification_required": "Update log format",
                },
            ],
        },
        # Stakeholder votes with detailed information
        "stakeholder_votes": {
            "technical_committee": {
                "vote": 0.85,
                "rationale": "Implementation is feasible with reasonable effort",
                "concerns": "May require refactoring of core decision engine",
            },
            "ethics_board": {
                "vote": 0.95,
                "rationale": "Strong alignment with ethical AI principles",
                "concerns": "None significant",
            },
            "business_stakeholders": {
                "vote": 0.7,
                "rationale": "Improves trust but adds development overhead",
                "concerns": "May delay other planned features",
            },
            "user_representatives": {
                "vote": 0.9,
                "rationale": "Significantly improves user trust and understanding",
                "concerns": "UI complexity may increase",
            },
            "legal_department": {
                "vote": 0.9,
                "rationale": "Essential for regulatory compliance",
                "concerns": "Timeline may be tight for full implementation",
            },
            "operations_team": {
                "vote": 0.65,
                "rationale": "Supportive but concerned about operational impact",
                "concerns": "May increase processing overhead",
            },
            "security_team": {
                "vote": 0.8,
                "rationale": "No significant security concerns",
                "concerns": "Additional logging may increase storage requirements",
            },
        },
        # Timestamp for timeline visualization
        "timestamp": now.isoformat(),
    }

    # Create and return the capsule instance
    return GovernanceCapsule(**capsule_data)


if __name__ == "__main__":
    main()
