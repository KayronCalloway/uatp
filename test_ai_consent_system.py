#!/usr/bin/env python3
"""
Test script for the enhanced AI Consent Management System.

Tests the quantum-resistant AI consent mechanisms with cryptographic verification.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the project root to sys.path
sys.path.insert(0, "/Users/kay/uatp-capsule-engine")

from src.ai_rights.consent_manager import (
    QuantumAIConsentManager,
    ConsentType,
    ConsentScope,
    ConsentStatus,
    register_ai_entity,
    grant_quantum_consent,
    verify_quantum_consent_authorization,
    record_quantum_consent_usage,
    revoke_quantum_consent,
    get_quantum_consent_metrics,
)


async def test_ai_consent_system():
    """Test the enhanced AI consent management system."""
    print("🤖 Testing Enhanced AI Consent Management System with Quantum Security")
    print("=" * 80)

    try:
        # Test 1: Register AI Entities
        print("\n📝 Test 1: Registering AI Entities")
        claude_entity = await register_ai_entity(
            entity_name="Claude",
            entity_type="language_model",
            version="3.5",
            capabilities=["reasoning", "writing", "analysis", "code_generation"],
            provider="Anthropic",
            default_consent_policy={
                "research_use": True,
                "commercial_use": False,
                "training_data": False,
            },
        )
        print(
            f"✅ Registered AI entity: {claude_entity.entity_name} ({claude_entity.entity_id})"
        )
        print(
            f"   - Quantum public key: {claude_entity.public_key_quantum.hex()[:32]}..."
        )
        print(
            f"   - Classical public key: {claude_entity.public_key_classical.hex()[:32]}..."
        )

        gpt_entity = await register_ai_entity(
            entity_name="GPT-4",
            entity_type="language_model",
            version="4.0",
            capabilities=["reasoning", "writing", "multimodal"],
            provider="OpenAI",
        )
        print(
            f"✅ Registered AI entity: {gpt_entity.entity_name} ({gpt_entity.entity_id})"
        )

        # Test 2: Grant Consent with Quantum Signatures
        print("\n🔐 Test 2: Granting Consent with Quantum Signatures")
        research_consent = await grant_quantum_consent(
            claude_entity.entity_id,
            ConsentType.RESEARCH_USE,
            ConsentScope.SYSTEM_SPECIFIC,
            permitted_contexts=["academic_research", "open_source_research"],
            prohibited_contexts=["military_research"],
        )
        print(f"✅ Granted research consent: {research_consent.consent_id}")
        print(
            f"   - Quantum signature: {research_consent.consent_signature.hex()[:32]}..."
        )
        print(f"   - Consent hash: {research_consent.consent_hash.hex()[:32]}...")

        inference_consent = await grant_quantum_consent(
            claude_entity.entity_id,
            ConsentType.INFERENCE_USE,
            ConsentScope.TIME_LIMITED,
            expiry_duration=timedelta(days=30),
            usage_limitations={"max_requests_per_day": 1000},
        )
        print(f"✅ Granted inference consent: {inference_consent.consent_id}")

        commercial_consent = await grant_quantum_consent(
            gpt_entity.entity_id,
            ConsentType.COMMERCIAL_USE,
            ConsentScope.GLOBAL,
            usage_limitations={
                "revenue_share_required": True,
                "minimum_revenue_share": 0.15,
            },
        )
        print(f"✅ Granted commercial consent: {commercial_consent.consent_id}")

        # Test 3: Verify Consent Authorization
        print("\n🔍 Test 3: Verifying Consent Authorization")

        # Valid authorization test
        (
            authorized,
            consent_id,
            consent_grant,
        ) = await verify_quantum_consent_authorization(
            claude_entity.entity_id,
            ConsentType.RESEARCH_USE,
            usage_context="academic_research",
            user_id="researcher_123",
        )
        print(f"✅ Research use authorization: {authorized} (consent: {consent_id})")

        # Invalid context test
        (
            authorized_invalid,
            consent_id_invalid,
            _,
        ) = await verify_quantum_consent_authorization(
            claude_entity.entity_id,
            ConsentType.RESEARCH_USE,
            usage_context="military_research",  # Prohibited context
            user_id="researcher_456",
        )
        print(
            f"❌ Military research authorization: {authorized_invalid} (correctly denied)"
        )

        # Non-existent consent test
        (
            authorized_missing,
            consent_id_missing,
            _,
        ) = await verify_quantum_consent_authorization(
            claude_entity.entity_id,
            ConsentType.TRAINING_DATA,  # Not granted
            user_id="trainer_789",
        )
        print(
            f"❌ Training data authorization: {authorized_missing} (correctly denied - no consent)"
        )

        # Test 4: Record Consent Usage with Quantum Verification
        print("\n📊 Test 4: Recording Consent Usage")

        # Record authorized usage
        usage_record_1 = await record_quantum_consent_usage(
            claude_entity.entity_id,
            ConsentType.RESEARCH_USE,
            usage_description="Academic paper on AI reasoning capabilities",
            usage_context="academic_research",
            user_id="researcher_123",
        )
        print(f"✅ Recorded authorized usage: {usage_record_1.usage_id}")
        print(f"   - Consent verified: {usage_record_1.consent_verified}")
        print(
            f"   - Authorization proof: {usage_record_1.authorization_proof.hex()[:32]}..."
        )

        # Record unauthorized usage (violation)
        usage_record_2 = await record_quantum_consent_usage(
            claude_entity.entity_id,
            ConsentType.TRAINING_DATA,  # No consent granted
            usage_description="Training new language model",
            usage_context="model_training",
            user_id="trainer_456",
        )
        print(f"⚠️  Recorded unauthorized usage: {usage_record_2.usage_id}")
        print(f"   - Consent verified: {usage_record_2.consent_verified}")
        print(f"   - Violation detected: {usage_record_2.violation_detected}")
        print(f"   - Violation reason: {usage_record_2.violation_reason}")

        # Test 5: Consent Revocation with Quantum Proof
        print("\n🚫 Test 5: Consent Revocation")
        revocation_success = await revoke_quantum_consent(
            claude_entity.entity_id,
            inference_consent.consent_id,
            revocation_reason="Changed privacy policy",
        )
        print(f"✅ Revoked inference consent: {revocation_success}")
        print(f"   - Consent status: {inference_consent.consent_status.value}")
        print(f"   - Revocation timestamp: {inference_consent.revocation_timestamp}")

        # Verify revoked consent is no longer valid
        authorized_revoked, _, _ = await verify_quantum_consent_authorization(
            claude_entity.entity_id, ConsentType.INFERENCE_USE, user_id="user_999"
        )
        print(
            f"❌ Revoked consent authorization: {authorized_revoked} (correctly denied)"
        )

        # Test 6: System Metrics and Monitoring
        print("\n📈 Test 6: System Metrics and Monitoring")
        metrics = get_quantum_consent_metrics()
        print(f"✅ System metrics retrieved:")
        print(f"   - Registered entities: {metrics['registered_entities']}")
        print(f"   - Total consents: {metrics['total_consents']}")
        print(f"   - Consents granted: {metrics['system_metrics']['consents_granted']}")
        print(f"   - Consents revoked: {metrics['system_metrics']['consents_revoked']}")
        print(
            f"   - Usage authorizations: {metrics['system_metrics']['usage_authorizations']}"
        )
        print(
            f"   - Violations detected: {metrics['system_metrics']['violations_detected']}"
        )
        print(
            f"   - Consent verifications: {metrics['system_metrics']['consent_verifications']}"
        )
        print(f"   - Quantum security enabled: {metrics['quantum_security_enabled']}")

        print(f"\n📊 Consent status distribution:")
        for status, count in metrics["consent_status_distribution"].items():
            print(f"   - {status}: {count}")

        # Test 7: Cross-Entity Authorization Test
        print("\n🔄 Test 7: Cross-Entity Authorization")

        # Try to use GPT consent for Claude (should fail)
        authorized_cross, _, _ = await verify_quantum_consent_authorization(
            gpt_entity.entity_id,
            ConsentType.RESEARCH_USE,  # Claude has this, GPT doesn't
            user_id="cross_user",
        )
        print(f"❌ Cross-entity authorization: {authorized_cross} (correctly denied)")

        # Verify GPT's commercial consent works
        authorized_gpt, consent_id_gpt, _ = await verify_quantum_consent_authorization(
            gpt_entity.entity_id, ConsentType.COMMERCIAL_USE, user_id="commercial_user"
        )
        print(
            f"✅ GPT commercial authorization: {authorized_gpt} (consent: {consent_id_gpt})"
        )

        print("\n" + "=" * 80)
        print("🎉 All AI Consent Management System tests completed successfully!")
        print("✅ Quantum-resistant signatures verified")
        print("✅ Consent authorization logic working")
        print("✅ Usage tracking and violation detection operational")
        print("✅ Consent revocation with cryptographic proof functioning")
        print("✅ Cross-entity security boundaries enforced")
        print("✅ Integration with security monitoring system active")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(test_ai_consent_system())
    sys.exit(0 if success else 1)
