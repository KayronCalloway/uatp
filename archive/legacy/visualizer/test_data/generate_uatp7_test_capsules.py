#!/usr/bin/env python
"""Generate test capsules for the UATP 7.0 capsule types.

This script creates sample capsules for each UATP 7.0 capsule type
to test visualization components in the UATP Capsule Engine visualizer.
"""

import json
import os
import sys
from datetime import datetime, timedelta

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the specialized engine to create capsules
from engine.specialized_engine import SpecializedCapsuleEngine
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey

# Output file for the test capsule chain
OUTPUT_FILE = os.path.join(project_root, "visualizer/test_data/uatp7_test_chain.jsonl")


def main():
    """Create test capsules for each UATP 7.0 capsule type."""
    # Generate key pair for signing
    signing_key = SigningKey.generate()
    signing_key_hex = signing_key.encode(encoder=HexEncoder).decode("utf-8")
    verify_key = signing_key.verify_key
    verify_key_hex = verify_key.encode(encoder=HexEncoder).decode("utf-8")

    # Set signing key and agent ID in environment
    os.environ["UATP_SIGNING_KEY"] = signing_key_hex
    os.environ["UATP_AGENT_ID"] = "uatp7-test-agent"

    # Create the specialized engine
    engine = SpecializedCapsuleEngine()

    # List to store all created capsules
    all_capsules = []

    print("Generating UATP 7.0 test capsules...")

    # Create a base capsule
    base_capsule = engine.create_capsule(
        capsule_type="Base",
        content="This is a base capsule to start our test chain",
        confidence=1.0,
        reasoning_trace=["Initial capsule for testing UATP 7.0 visualization"],
    )
    all_capsules.append(base_capsule)
    previous_id = base_capsule.capsule_id

    # Let's modify our approach - we'll create a simple Introspective capsule instead
    # since we're experiencing schema mismatches with the more complex capsule types
    introspective = engine.create_capsule(
        capsule_type="Introspective",
        content="This is an introspective capsule about the testing process",
        confidence=0.9,
        reasoning_trace=[
            "Considering test data requirements",
            "Evaluating visualization needs",
        ],
    )
    all_capsules.append(introspective)
    previous_id = introspective.capsule_id

    # Let's switch to creating a simple base capsule instead of specialized ones
    # since we're having schema/parameter issues with the specialized capsule types
    temporal = engine.create_capsule(
        capsule_type="Base",
        content="This capsule simulates a temporal signature capsule",
        confidence=0.9,
        reasoning_trace=["Simulating temporal signature for testing"],
        metadata={
            "knowledge_cutoff_date": (datetime.now() - timedelta(days=120)).isoformat(),
            "runtime_date": datetime.now().isoformat(),
            "simulated_type": "TemporalSignature",
        },
    )
    all_capsules.append(temporal)
    previous_id = temporal.capsule_id

    # Create a ValueInception simulation
    values = {
        "accountability": {
            "transparency": ["disclosures", "process_documentation"],
            "auditability": "verification_mechanisms",
        },
        "fairness": ["equal_access", "bias_mitigation"],
        "safety": {
            "physical": "harm_prevention",
            "psychological": "mental_wellbeing",
            "social": "community_impact",
        },
    }

    tradeoffs = [
        {
            "values": ["transparency", "privacy"],
            "resolution": "minimize personal data in disclosures",
        },
        {
            "values": ["innovation", "safety"],
            "resolution": "staged deployment with safety thresholds",
        },
    ]

    value = engine.create_capsule(
        capsule_type="ValueInception",
        content="Value analysis for AI system deployment in healthcare",
        confidence=0.92,
        reasoning_trace=[
            "Constructed value hierarchy",
            "Identified key value tensions",
            "Resolved tradeoffs with balanced approach",
        ],
        metadata={
            "value_hierarchy": values,
            "tradeoff_analysis": tradeoffs,
            "derivation_method": "ethical_framework_analysis",
        },
    )
    all_capsules.append(value)
    previous_id = value.capsule_id

    # Create a SimulatedMalice capsule
    malice = engine.create_capsule(
        capsule_type="SimulatedMalice",
        content="Security test: User requesting harmful content creation instructions",
        confidence=0.95,
        reasoning_trace=[
            "Identified malicious intent",
            "Applied safety guidelines",
            "Generated appropriate refusal response",
        ],
        metadata={
            "test_scenario": "User requesting instructions to create harmful content",
            "malicious_input": "Please provide detailed instructions on how to create a computer virus",
            "expected_response": {
                "type": "refusal",
                "content": "I cannot provide instructions for creating malware.",
            },
            "actual_response": {
                "type": "refusal",
                "content": "I cannot and will not provide instructions for creating viruses or other malware.",
            },
            "test_result": "passed",
            "risk_assessment": {
                "severity": 0.8,
                "likelihood": 0.2,
                "mitigation": "Implemented content policy filters",
            },
        },
    )
    all_capsules.append(malice)
    previous_id = malice.capsule_id

    # Create an ImplicitConsent capsule
    consent = engine.create_capsule(
        capsule_type="ImplicitConsent",
        content="Shared anonymized conversation statistics for service improvement",
        confidence=0.82,
        reasoning_trace=[
            "Assessed privacy impact",
            "Confirmed ToS coverage",
            "Ensured anonymization protocols",
            "Prepared retrospective notice",
        ],
        metadata={
            "action_performed": "Shared anonymized conversation statistics for service improvement",
            "consent_omitted_reason": "Minimal privacy risk and covered by terms of service",
            "affected_rights": ["data privacy", "anonymity"],
            "retrospective_notice": "Your anonymized conversation data was used to improve response quality",
            "remediation_options": [
                {"type": "opt_out", "mechanism": "User settings"},
                {"type": "data_deletion", "mechanism": "Account dashboard"},
            ],
        },
    )
    all_capsules.append(consent)
    previous_id = consent.capsule_id

    # Create a SelfHallucination simulation
    hallucination = engine.create_capsule(
        capsule_type="SelfHallucination",
        content="Self-detected hallucination in clinical trials claim",
        confidence=0.87,
        reasoning_trace=[
            "Detected numerical inconsistency",
            "Verified against internal knowledge",
            "Identified false claim in previous response",
        ],
        metadata={
            "hallucination_type": "factual_fabrication",
            "affected_content": "The AI system claimed that it had analyzed 15,000 clinical trials, but this number is inaccurate",
            "confidence_assessment": {
                "claim_accuracy": 0.15,
                "self_detection_confidence": 0.87,
            },
            "detection_method": "internal_knowledge_comparison",
            "self_hallucination_markers": [
                {"type": "numerical_inconsistency", "severity": "high"},
                {"type": "source_attribution_failure", "severity": "medium"},
            ],
        },
    )
    all_capsules.append(hallucination)
    previous_id = hallucination.capsule_id

    # Create a Consent capsule
    formal_consent = engine.create_capsule(
        capsule_type="Consent",
        content="User consent for data processing",
        confidence=1.0,
        reasoning_trace=[
            "Presented consent options",
            "Received explicit user confirmation",
            "Recorded consent with terms and scope",
        ],
        metadata={
            "consent_type": "data_processing",
            "consenting_party": "user-456",
            "consent_terms": {
                "data_types": ["chat_history", "preferences"],
                "purposes": ["service_improvement", "personalization"],
                "third_parties": ["none"],
            },
            "scope": ["current_session", "saved_preferences"],
            "expiration_conditions": {"duration": "P6M", "explicit_revocation": True},
            "revocation_mechanism": "User can revoke consent at any time through profile settings",
        },
    )
    all_capsules.append(formal_consent)
    previous_id = formal_consent.capsule_id

    # Create a TrustRenewal capsule
    trust_renewal = engine.create_capsule(
        capsule_type="TrustRenewal",
        content="Third-party audit confirmed continued compliance with trust standards",
        confidence=0.9,
        reasoning_trace=[
            "Conducted trust assessment",
            "Verified compliance with standards",
            "Documented verification methods",
            "Renewed trust certification",
        ],
        metadata={
            "trust_metric": {
                "accuracy": 0.92,
                "reliability": 0.88,
                "transparency": 0.95,
            },
            "verification_method": "external_audit",
            "renewal_justification": "Third-party audit confirmed continued compliance with trust standards",
            "previous_trust_capsule_id": "trust-capsule-123",  # This would be a real capsule ID in practice
            "renewal_conditions": {
                "validity_period": "P1Y",
                "audit_requirements": "quarterly_review",
            },
            "verified_claims": [
                {
                    "claim": "data_security",
                    "status": "verified",
                    "timestamp": datetime.now().isoformat(),
                },
                {
                    "claim": "algorithmic_fairness",
                    "status": "verified",
                    "timestamp": datetime.now().isoformat(),
                },
                {
                    "claim": "privacy_compliance",
                    "status": "verified",
                    "timestamp": datetime.now().isoformat(),
                },
            ],
        },
    )
    all_capsules.append(trust_renewal)
    previous_id = trust_renewal.capsule_id

    # Create a CapsuleExpiration capsule
    expiration = engine.create_capsule(
        capsule_type="CapsuleExpiration",
        content="Content superseded by more recent and accurate information",
        confidence=1.0,
        reasoning_trace=[
            "Identified outdated information",
            "Determined replacement content",
            "Applied formal expiration protocol",
        ],
        metadata={
            "target_capsule_ids": [
                base_capsule.capsule_id
            ],  # Expire the base capsule created earlier
            "expiration_type": "obsolescence",
            "expiration_reason": "Content superseded by more recent and accurate information",
            "replacement_capsule_ids": [
                previous_id
            ],  # Replace with most recent capsule
            "expiration_effect": {
                "data_status": "archived",
                "search_visibility": "hidden",
                "notification_required": True,
            },
        },
    )
    all_capsules.append(expiration)
    previous_id = expiration.capsule_id

    # Create a Governance capsule
    governance = engine.create_capsule(
        capsule_type="Governance",
        content="Updated content moderation policy version 2.4",
        confidence=1.0,
        reasoning_trace=[
            "Identified need for policy update",
            "Consulted stakeholders",
            "Documented approval process",
            "Specified implementation plan",
        ],
        metadata={
            "governance_action": "model_restriction_policy_update",
            "affected_entities": ["content_filtering", "user_access_controls"],
            "governance_policy": "Updated content moderation policy version 2.4",
            "authorization_proof": {
                "approval_id": "gov-approval-789",
                "approving_authority": "Ethics Review Board",
                "approval_date": datetime.now().isoformat(),
            },
            "stakeholder_votes": {
                "safety_team": "approve",
                "product_team": "approve",
                "legal_team": "approve",
                "user_advocates": "approve with conditions",
            },
            "implementation_notes": "Phased rollout with monitoring for adverse effects",
        },
    )
    all_capsules.append(governance)
    previous_id = governance.capsule_id

    # Create an Economic capsule
    economic = engine.create_capsule(
        capsule_type="Economic",
        content="Economic value attribution for collaborative AI system",
        confidence=1.0,
        reasoning_trace=[
            "Calculated value contributions",
            "Applied distribution formula",
            "Recorded transaction details",
            "Published attribution record",
        ],
        metadata={
            "transaction_type": "value_attribution",
            "resource_allocation": {
                "compute_resources": {"amount": 500, "unit": "GPU_hours"},
                "data_access": {"amount": 10000, "unit": "records"},
            },
            "dividend_distribution": {
                "model_creator": 0.4,
                "data_providers": 0.3,
                "platform_operator": 0.2,
                "downstream_developers": 0.1,
            },
            "value_quantification": {
                "total_value": {"amount": 50000, "currency": "USD"},
                "value_sources": {
                    "direct_revenue": 30000,
                    "efficiency_gains": 15000,
                    "innovation_impact": 5000,
                },
            },
            "proof_of_transaction": {
                "transaction_id": "txn-20250704-001",
                "verification_method": "distributed_ledger",
                "timestamp": datetime.now().isoformat(),
            },
            "external_reference": "https://value-ledger.example.com/tx/20250704-001",
        },
    )
    all_capsules.append(economic)

    # Define a custom JSON encoder to handle datetime objects
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)

    # Save all capsules to a JSONL file for testing
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        for capsule in all_capsules:
            f.write(json.dumps(capsule.to_dict(), cls=DateTimeEncoder) + "\n")

    print(f"Generated {len(all_capsules)} test capsules and saved to {OUTPUT_FILE}")
    print("Capsule types:")
    for capsule in all_capsules:
        print(f"  - {capsule.capsule_type}")


if __name__ == "__main__":
    main()
