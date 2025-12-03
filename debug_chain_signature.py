#!/usr/bin/env python3
"""
Debug script to test chain signature verification specifically.
"""

import asyncio
import sys
import json

sys.path.insert(0, "/Users/kay/uatp-capsule-engine")

from src.reasoning.chain_verifier import (
    reasoning_chain_verifier,
    ReasoningVerificationLevel,
)
from src.reasoning.trace import ReasoningTrace, ReasoningStep, StepType
from src.ai_rights.consent_manager import (
    register_ai_entity,
    grant_quantum_consent,
    ConsentType,
    ConsentScope,
    quantum_ai_consent_manager,
)
from src.crypto.post_quantum import pq_crypto


async def debug_chain_signature():
    """Debug the chain signature verification process."""
    print("🔍 Debugging Chain Signature Verification")
    print("=" * 50)

    # Register AI entity
    entity = await register_ai_entity(
        entity_name="ChainDebug-Claude",
        entity_type="reasoning_model",
        version="1.0",
        capabilities=["reasoning"],
        provider="Debug",
    )
    print(f"✅ Registered entity: {entity.entity_id}")

    # Grant consent
    consent = await grant_quantum_consent(
        entity.entity_id,
        ConsentType.REASONING_VERIFICATION,
        ConsentScope.SYSTEM_SPECIFIC,
    )
    print(f"✅ Granted consent: {consent.consent_id}")

    # Create a simple reasoning trace
    simple_steps = [
        ReasoningStep("Test observation", StepType.OBSERVATION, 0.9),
        ReasoningStep("Test conclusion", StepType.CONCLUSION, 0.8),
    ]
    trace = ReasoningTrace(simple_steps)

    # Create verified chain
    chain = await reasoning_chain_verifier.create_verified_reasoning_chain(
        entity.entity_id, trace, ReasoningVerificationLevel.ENHANCED
    )
    print(f"✅ Created chain: {chain.chain_id}")

    # Debug chain signature
    print(f"\n🔍 Debugging chain signature")
    print(f"Chain signature length: {len(chain.chain_signature)}")
    print(f"Verification timestamp: {chain.verification_timestamp}")
    print(f"Chain hash: {chain.chain_hash.hex()[:32]}...")
    print(f"Merkle root: {chain.merkle_root.hex()[:32]}...")
    print(f"Overall quality score: {chain.overall_quality_score}")

    # Manually verify chain signature like the verification method does
    chain_payload = {
        "chain_id": chain.chain_id,
        "ai_entity_id": chain.ai_entity_id,
        "chain_hash": chain.chain_hash.hex(),
        "merkle_root": chain.merkle_root.hex(),
        "steps_count": len(chain.verified_steps),
        "overall_quality_score": chain.overall_quality_score,
        "verification_timestamp": chain.verification_timestamp.isoformat()
        if chain.verification_timestamp
        else None,
    }

    payload_bytes = json.dumps(chain_payload, sort_keys=True).encode()
    print(f"\nPayload for verification:")
    print(f"Length: {len(payload_bytes)}")
    print(f"Preview: {payload_bytes[:150].decode()}...")

    # Check entity keys
    if chain.ai_entity_id in quantum_ai_consent_manager.entity_keys:
        entity_keys = quantum_ai_consent_manager.entity_keys[chain.ai_entity_id]
        print(f"✅ Found entity keys")

        # Test manual verification
        try:
            is_valid = pq_crypto.dilithium_verify(
                payload_bytes, chain.chain_signature, entity_keys["quantum_public"]
            )
            print(f"Manual chain signature verification: {is_valid}")

            # Test the verifier's method
            chain_valid = await reasoning_chain_verifier._verify_chain_signature(chain)
            print(f"Chain verifier method: {chain_valid}")

        except Exception as e:
            print(f"❌ Chain signature verification error: {e}")
    else:
        print(f"❌ No entity keys found for {chain.ai_entity_id}")


if __name__ == "__main__":
    asyncio.run(debug_chain_signature())
