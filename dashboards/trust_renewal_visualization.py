from datetime import datetime, timedelta

import streamlit as st

from capsules.specialized_capsules import TrustRenewalCapsule
from visualizer.components.uatp7_inspector import render_trust_renewal_content


def main():
    """
    Test script to demonstrate the enhanced Trust Renewal capsule visualization.
    """
    st.set_page_config(
        page_title="UATP 7.0 Trust Renewal Visualization Test",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.title("🔄 Trust Renewal Capsule Visualization Test")
    st.markdown(
        """
    This test demonstrates the enhanced visualization components for UATP 7.0 Trust Renewal capsules.
    The visualization includes a multi-tab interface with:
    - **Trust Overview**: Summary of trust renewal status and overall trust score
    - **Trust Metrics**: Detailed visualization of trust metrics with interactive elements
    - **Verification Details**: Complete verification results and claims with visual indicators
    - **History & Timeline**: Historical context and timeline of trust-related events
    """
    )

    # Create a sample Trust Renewal capsule
    trust_renewal_capsule = create_sample_trust_renewal_capsule()

    # Add a divider
    st.markdown("---")
    st.subheader("Trust Renewal Capsule Visualization")

    # Render the capsule using the enhanced visualization
    render_trust_renewal_content(trust_renewal_capsule)


def create_sample_trust_renewal_capsule():
    """
    Create a sample Trust Renewal capsule with realistic data.
    """
    # Calculate timestamps
    now = datetime.now()
    verification_time = now - timedelta(hours=12)
    creation_time = verification_time - timedelta(hours=1)

    # Base capsule data
    capsule_data = {
        # Required base capsule fields
        "capsule_id": "trust_renewal_test_123456",
        "capsule_type": "TrustRenewal",
        "agent_id": "trust-verification-agent-001",
        "confidence": 0.92,
        "signature": "0x8a7bc982f56e7a97b4d762f9be28dc919c738817",
        "reasoning_trace": [
            "Periodic trust renewal triggered by time-based policy",
            "All verification checks passed with acceptable confidence levels",
        ],
        # Trust Renewal-specific fields
        "renewal_type": "Periodic",
        "previous_trust_capsule_id": "uatp_7_tr_93826401fe67bc3d",
        "trust_metrics": {
            "identity_confidence": 0.95,
            "behavior_consistency": 0.88,
            "historical_reliability": 0.92,
            "transparency_score": 0.85,
            "security_compliance": 0.91,
        },
        "renewal_period": "P90D",  # 90 days in ISO 8601 duration format
        "verification_method": "Hybrid Automated and Manual Review",
        # Additional Trust Renewal fields
        "verification_results": {
            "identity_verification": {
                "status": "passed",
                "confidence": 0.95,
                "method": "biometric",
                "timestamp": verification_time.isoformat(),
            },
            "credential_verification": {
                "status": "passed",
                "confidence": 0.98,
                "method": "cryptographic",
                "timestamp": verification_time.isoformat(),
            },
            "behavior_analysis": {
                "status": "passed",
                "confidence": 0.88,
                "anomalies_detected": "none",
                "timestamp": verification_time.isoformat(),
            },
            "compliance_check": {
                "status": "passed",
                "confidence": 0.91,
                "details": "All required security policies satisfied",
                "timestamp": verification_time.isoformat(),
            },
        },
        "verified_claims": [
            {
                "claim_type": "identity",
                "status": "verified",
                "timestamp": verification_time.isoformat(),
                "verification_method": "biometric",
            },
            {
                "claim_type": "credentials",
                "status": "verified",
                "timestamp": verification_time.isoformat(),
                "verification_method": "cryptographic",
            },
            {
                "claim_type": "permissions",
                "status": "verified",
                "timestamp": verification_time.isoformat(),
                "verification_method": "policy-based",
            },
            {
                "claim_type": "security_compliance",
                "status": "verified",
                "timestamp": verification_time.isoformat(),
                "verification_method": "automated",
            },
        ],
        "renewal_conditions": {
            "required_verifications": [
                "identity verification",
                "credential verification",
                "behavior analysis",
                "compliance check",
            ],
            "minimum_trust_score": 0.8,
            "required_claims": ["identity", "credentials", "permissions"],
        },
        "renewal_justification": """
        Trust renewal approved based on:
        1. All identity verification checks passed
        2. All credential verification checks passed
        3. Behavior analysis indicates normal patterns with no anomalies
        4. All security compliance requirements met
        5. Overall trust score remains above minimum threshold

        This renewal extends trust for a standard 90-day period with no restrictions.
        """,
        # Timestamp for timeline visualization
        "timestamp": creation_time.isoformat(),
    }

    # Create and return the capsule instance
    return TrustRenewalCapsule(**capsule_data)


if __name__ == "__main__":
    main()
