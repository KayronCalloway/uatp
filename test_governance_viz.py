"""
Test script for the Governance capsule visualization component.

This script creates a test governance capsule and launches the visualizer
to see how the governance visualization components render.
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

# Add the project root to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from capsules.specialized_capsules import GovernanceCapsule
from visualizer.components.uatp7_inspector import render_governance_content


def create_sample_governance_capsule():
    """
    Create a sample governance capsule with realistic test data
    """
    capsule_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    # Create a sample governance capsule
    capsule = GovernanceCapsule(
        schema_version="1.0",
        capsule_id=capsule_id,
        capsule_type="Governance",
        agent_id="test-agent-001",
        timestamp=timestamp,
        previous_capsule_id=None,  # Root capsule
        confidence=0.95,
        reasoning_trace=[
            "Identified protocol governance issue requiring stakeholder vote",
            "Analyzed impact on affected entities and protocol security",
            "Formulated governance action with clear implementation steps",
            "Collected stakeholder votes and calculated approval rating",
            "Documented implementation plan with timeline and resources",
        ],
        metadata={
            "governance_version": "1.2",
            "priority_level": "High",
            "governance_domain": "Protocol Security",
            "initiated_by": "Security Council",
        },
        # Required fields based on GovernanceCapsule schema
        governance_type="Protocol Update",
        policy_id="SEC-AUTH-2025-003",
        decision_makers=[
            "Security Council",
            "API Team",
            "Client SDK Team",
            "Operations",
            "Compliance",
            "Client Relations",
            "Legacy Systems",
            "Finance",
        ],
        decision_rationale="Enhance security posture and meet new compliance requirements by implementing OAuth 2.0 with MFA",
        affected_scopes=["authentication", "security", "api", "sdk"],
        governance_details={
            "version": "1.2",
            "priority": "High",
            "domain": "Protocol Security",
            "initiated_by": "Security Council",
        },
        # Optional fields
        voting_results={
            "total_votes": 8,
            "approval_votes": 5,
            "neutral_votes": 2,
            "disapproval_votes": 1,
            "quorum_achieved": True,
            "decision": "approved",
        },
        # Additional fields for visualization
        governance_action="Update UATP authentication mechanism to implement OAuth 2.0 and MFA requirements",
        action_details={
            "policy_information": {
                "policy_id": "SEC-AUTH-2025-003",
                "policy_name": "Enhanced Authentication Security Policy",
                "policy_version": "1.0",
                "effective_date": "2025-08-01T00:00:00Z",
                "expiration_date": "2028-08-01T00:00:00Z",
            },
            "rationale": {
                "security_considerations": "Current authentication mechanism vulnerable to replay attacks",
                "compliance_requirements": "New industry standard requires OAuth 2.0 with MFA for critical systems",
                "incident_references": ["INC-2025-042", "INC-2025-067"],
            },
            "scope": {
                "affected_components": ["API Gateway", "Auth Service", "Client SDKs"],
                "excluded_systems": ["Legacy connectors (deprecated)"],
                "implementation_phases": 3,
            },
            "timeline": {
                "planning_phase": "2025-07-15 to 2025-07-30",
                "development_phase": "2025-08-01 to 2025-08-31",
                "testing_phase": "2025-09-01 to 2025-09-15",
                "rollout_phase": "2025-09-16 to 2025-10-01",
            },
            "impact_assessment": {
                "service_disruption": "Minimal (rolling updates)",
                "client_impact": "SDK updates required for all clients",
                "backward_compatibility": "Temporary compatibility layer for 90 days",
            },
        },
        affected_entities=[
            {
                "entity_id": "component-auth-service",
                "entity_type": "service",
                "impact_level": "high",
            },
            {
                "entity_id": "component-api-gateway",
                "entity_type": "service",
                "impact_level": "high",
            },
            {
                "entity_id": "sdk-python",
                "entity_type": "client",
                "impact_level": "medium",
            },
            {
                "entity_id": "sdk-javascript",
                "entity_type": "client",
                "impact_level": "medium",
            },
            {
                "entity_id": "sdk-java",
                "entity_type": "client",
                "impact_level": "medium",
            },
            {"entity_id": "sdk-go", "entity_type": "client", "impact_level": "medium"},
            {
                "entity_id": "legacy-connectors",
                "entity_type": "deprecated",
                "impact_level": "low",
            },
        ],
        stakeholder_votes={
            "Security Council": {
                "vote": 1.0,
                "comments": "Strongly approve - critical security upgrade",
            },
            "API Team": {
                "vote": 0.9,
                "comments": "Support with minor implementation concerns",
            },
            "Client SDK Team": {
                "vote": 0.8,
                "comments": "Approve, but timeline is aggressive",
            },
            "Operations": {
                "vote": 0.7,
                "comments": "Support with monitoring recommendations",
            },
            "Compliance": {
                "vote": 1.0,
                "comments": "Required for regulatory compliance",
            },
            "Client Relations": {
                "vote": 0.6,
                "comments": "Some client disruption expected",
            },
            "Legacy Systems": {
                "vote": 0.4,
                "comments": "Concerns about legacy adapter compatibility",
            },
            "Finance": {
                "vote": 0.5,
                "comments": "Neutral - budget implications need review",
            },
        },
        authorization_proof={
            "vote_hash": "7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b",
            "quorum_achieved": True,
            "voting_period": {
                "start": "2025-06-15T00:00:00Z",
                "end": "2025-06-30T23:59:59Z",
            },
            "authorized_by": "Governance Smart Contract 0x123...abc",
            "verification_method": "Multi-signature threshold 6/8",
        },
        implementation_status={
            "current_status": "Planning Phase",
            "progress": 0.15,
            "last_updated": "2025-07-03T14:30:00Z",
            "blockers": [
                {
                    "description": "SDK versioning strategy needs finalization",
                    "severity": "medium",
                },
                {
                    "description": "MFA provider selection pending legal review",
                    "severity": "high",
                },
            ],
            "next_steps": [
                {
                    "description": "Finalize MFA provider selection",
                    "owner": "Security Team",
                    "due_date": "2025-07-10",
                },
                {
                    "description": "Draft SDK upgrade documentation",
                    "owner": "Documentation Team",
                    "due_date": "2025-07-15",
                },
                {
                    "description": "Create client migration plan",
                    "owner": "Client Relations",
                    "due_date": "2025-07-20",
                },
            ],
        },
        implementation_timeline=[
            {
                "date": "2025-07-15",
                "description": "Planning phase complete",
                "status": "pending",
            },
            {
                "date": "2025-07-30",
                "description": "Development starts",
                "status": "pending",
            },
            {
                "date": "2025-08-15",
                "description": "API changes implemented",
                "status": "pending",
            },
            {
                "date": "2025-08-31",
                "description": "SDK updates complete",
                "status": "pending",
            },
            {
                "date": "2025-09-15",
                "description": "Testing complete",
                "status": "pending",
            },
            {
                "date": "2025-10-01",
                "description": "Full rollout complete",
                "status": "pending",
            },
        ],
        implementation_details={
            "resources": {
                "development": [
                    {
                        "name": "Backend Engineer",
                        "quantity": 2,
                        "description": "For API Gateway and Auth Service modifications",
                    },
                    {
                        "name": "SDK Developer",
                        "quantity": 4,
                        "description": "One per supported SDK language",
                    },
                ],
                "infrastructure": [
                    "OAuth provider subscription",
                    "MFA service integration",
                    "Additional testing environment",
                ],
            },
            "dependencies": [
                {
                    "name": "OAuth Provider Selection",
                    "status": "pending",
                    "description": "Must select and contract with OAuth service provider",
                },
                {
                    "name": "MFA Implementation Decision",
                    "status": "pending",
                    "description": "Choose between SMS, app-based, or hardware token approaches",
                },
                {
                    "name": "Legal Review",
                    "status": "in progress",
                    "description": "Compliance review of authentication changes",
                },
            ],
            "documentation_updates": [
                "API Reference Documentation",
                "SDK Integration Guides",
                "Migration Tutorials",
                "Security Best Practices",
            ],
        },
        document_references={
            "Technical Specification": "SPEC-AUTH-2025-003",
            "Security Assessment": "SEC-ASSESSMENT-2025-042",
            "Compliance Requirements": "COMP-REQ-2025-OAuth-MFA",
        },
        # Required for GovernanceCapsule but not used in visualization
        signature="test_signature_placeholder",
    )

    # The signature would normally be generated cryptographically
    # but we're using a placeholder for testing purposes
    return capsule


def main():
    """
    Main function to test the governance capsule visualization
    """
    st.set_page_config(layout="wide", page_title="UATP Governance Capsule Test")

    st.title("UATP 7.0 Governance Capsule Visualization Test")

    # Create a sample governance capsule
    capsule = create_sample_governance_capsule()

    # Use the governance visualization component
    render_governance_content(capsule)

    # Add some helpful debugging information
    with st.expander("Raw Capsule Data"):
        st.json(json.loads(capsule.model_dump_json()))


if __name__ == "__main__":
    main()
