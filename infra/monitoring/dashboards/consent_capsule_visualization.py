"""
Test script for visualizing a Consent capsule with the enhanced multi-tab visualization.

This script demonstrates the enhanced Consent capsule visualization with realistic test data.
Run this script with Streamlit to see the visualization:

    streamlit run tests/test_consent_capsule_visualization.py
"""

import uuid
from datetime import datetime, timezone

import streamlit as st
from visualizer.components.uatp7_inspector import render_consent_content

# Import the required modules
from capsules.specialized_capsules import ConsentCapsule

# Set page config
st.set_page_config(
    page_title="Consent Capsule Visualization Test",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main function to demonstrate the Consent capsule visualization."""
    st.title("UATP 7.0 Consent Capsule Visualization")
    st.markdown(
        "This demo shows the enhanced multi-tab visualization for the Consent capsule type."
    )

    # Create a realistic Consent capsule
    capsule = create_sample_consent_capsule()

    # Show tabs for different view options
    tab1, tab2 = st.tabs(["Enhanced Visualization", "Raw Capsule Data"])

    with tab1:
        st.subheader("Enhanced Multi-tab Consent Visualization")
        # Use the specialized visualization function
        render_consent_content(capsule)

    with tab2:
        st.subheader("Raw Capsule Data")
        st.json(capsule.to_dict())


def create_sample_consent_capsule():
    """Create a sample Consent capsule with realistic data."""

    # Generate a unique capsule ID
    capsule_id = str(uuid.uuid4())

    # Create the current timestamp
    timestamp = datetime.now(timezone.utc).isoformat()

    # Create detailed consent information
    consent_details = {
        "purpose": "Data processing for personalized AI responses",
        "notes": "This consent allows the system to process user data for providing personalized AI responses while respecting user privacy and ensuring data protection.",
        "legal_basis": "Explicit user consent",
        "related_entities": [
            "AI Assistant Provider",
            "Data Processing Service",
            "User Authentication Service",
        ],
        "affected_resources": [
            "User conversation history",
            "User preferences",
            "Usage patterns",
        ],
        "verification_events": [
            {
                "event_type": "Initial Verification",
                "timestamp": (datetime.now(timezone.utc)).isoformat(),
                "method": "Email confirmation",
            },
            {
                "event_type": "Secondary Verification",
                "timestamp": (datetime.now(timezone.utc)).isoformat(),
                "method": "SMS code",
            },
        ],
        "revocation_mechanism": {
            "method": "Self-service portal",
            "contact": "privacy@example.com",
            "time_limit": "30 days",
            "conditions": [
                "Revocation does not affect already processed data",
                "Backup data might take up to 30 days to be completely deleted",
            ],
        },
    }

    # Create base capsule data
    capsule_data = {
        "capsule_id": capsule_id,
        "capsule_type": "Consent",
        "timestamp": timestamp,
        "signature": "ed25519:7dKhGF8edHtFG5zH9LmP2KqS5vXyxZGF4etFGF5zZGFGz5xH5vSqK2PmL9zH5dKhGF8e",
        "previous_capsule_id": None,
        "metadata": {
            "version": "1.0",
            "creator": "Privacy Management System",
            "creation_context": "User Account Setup",
        },
        # Required base capsule fields
        "agent_id": "privacy-management-agent-001",
        "confidence": 0.95,
        "reasoning_trace": [
            "User explicitly provided consent through the privacy portal after reviewing all terms and conditions."
        ],
        # Consent-specific fields
        "consent_provider": "user12345",
        "consent_scope": "Data Processing for AI Services",
        "consent_duration": "P1Y",  # ISO 8601 duration: 1 year
        "revocable": True,
        "conditions": [
            "Data will be processed only for stated purposes",
            "Data will not be shared with third parties",
            "Data will be stored securely and encrypted",
            "Data will be deleted upon request or after consent expiration",
        ],
        "consent_verification_method": "Digital signature and multi-factor authentication",
        "consent_details": consent_details,
    }

    # Create and return the capsule
    return ConsentCapsule(**capsule_data)


if __name__ == "__main__":
    main()
