#!/usr/bin/env python3
"""
Debug script to test the signature verification issue.
"""

import asyncio
import sys
import json

sys.path.insert(0, "/Users/kay/uatp-capsule-engine")

from src.reasoning.chain_verifier import reasoning_chain_verifier
from src.reasoning.trace import ReasoningTrace, ReasoningStep, StepType
from src.ai_rights.consent_manager import (
    register_ai_entity,
    grant_quantum_consent,
    ConsentType,
    ConsentScope,
    quantum_ai_consent_manager,
)
from src.crypto.post_quantum import pq_crypto


async def debug_signature_verification():
    """Debug the signature verification process."""
    print("🔍 Debugging Signature Verification")
    print("=" * 50)

    # Register AI entity
    entity = await register_ai_entity(
        entity_name="Debug-Claude",
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
        entity.entity_id, trace
    )
    print(f"✅ Created chain: {chain.chain_id}")

    # Debug first step
    first_step = chain.verified_steps[0]
    print(f"\n🔍 Debugging first step: {first_step.step_id}")

    # Reconstruct signing payload
    step_payload = {
        "step_id": first_step.step_id,
        "chain_id": first_step.chain_id,
        "ai_entity_id": first_step.ai_entity_id,
        "step_hash": first_step.step_hash.hex(),
        "content": first_step.original_step.content,
        "step_type": first_step.original_step.step_type.value,
        "verification_timestamp": first_step.verification_timestamp.isoformat(),
    }

    payload_bytes = json.dumps(step_payload, sort_keys=True).encode()
    print(f"Payload bytes length: {len(payload_bytes)}")
    print(f"Payload preview: {payload_bytes[:100].decode()}...")

    # Check entity keys
    if first_step.ai_entity_id in quantum_ai_consent_manager.entity_keys:
        entity_keys = quantum_ai_consent_manager.entity_keys[first_step.ai_entity_id]
        print(f"✅ Found entity keys")
        print(f"Quantum public key length: {len(entity_keys['quantum_public'])}")
        print(f"Quantum signature length: {len(first_step.quantum_signature)}")

        # Test verification
        try:
            is_valid = pq_crypto.dilithium_verify(
                payload_bytes,
                first_step.quantum_signature,
                entity_keys["quantum_public"],
            )
            print(f"Manual verification result: {is_valid}")

            # Test the chain verifier's verification method
            step_valid = await reasoning_chain_verifier._verify_step_quantum_signature(
                first_step
            )
            print(f"Chain verifier verification: {step_valid}")

        except Exception as e:
            print(f"❌ Verification error: {e}")
    else:
        print(f"❌ No entity keys found for {first_step.ai_entity_id}")
        print(f"Available keys: {list(quantum_ai_consent_manager.entity_keys.keys())}")


if __name__ == "__main__":
    asyncio.run(debug_signature_verification())
