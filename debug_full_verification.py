#!/usr/bin/env python3
"""
Debug full verification process to understand the signature issue.
"""

import asyncio
import sys

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


async def debug_full_verification():
    """Debug the complete verification process."""
    print("🔍 Debugging Full Verification Process")
    print("=" * 50)

    # Register AI entity
    entity = await register_ai_entity(
        entity_name="Test-Claude",
        entity_type="reasoning_model",
        version="1.0",
        capabilities=["reasoning"],
        provider="Test",
    )
    print(f"✅ Registered entity: {entity.entity_id}")

    # Grant consent
    consent = await grant_quantum_consent(
        entity.entity_id,
        ConsentType.REASONING_VERIFICATION,
        ConsentScope.SYSTEM_SPECIFIC,
    )
    print(f"✅ Granted consent: {consent.consent_id}")

    # Check entity keys are available
    print(
        f"Available entity keys: {list(quantum_ai_consent_manager.entity_keys.keys())}"
    )
    if entity.entity_id in quantum_ai_consent_manager.entity_keys:
        print("✅ Entity keys are available after registration")
    else:
        print("❌ Entity keys are NOT available after registration")
        return

    # Create a simple reasoning trace
    steps = [
        ReasoningStep("Test observation", StepType.OBSERVATION, 0.9),
        ReasoningStep("Test inference", StepType.INFERENCE, 0.8),
        ReasoningStep("Test conclusion", StepType.CONCLUSION, 0.85),
    ]
    trace = ReasoningTrace(steps)

    # Create verified chain
    chain = await reasoning_chain_verifier.create_verified_reasoning_chain(
        entity.entity_id, trace, ReasoningVerificationLevel.STANDARD
    )
    print(f"✅ Created chain: {chain.chain_id}")
    print(f"Chain status: {chain.integrity_status.value}")

    # Check entity keys are still available
    print(
        f"Entity keys after chain creation: {list(quantum_ai_consent_manager.entity_keys.keys())}"
    )
    if entity.entity_id in quantum_ai_consent_manager.entity_keys:
        print("✅ Entity keys still available after chain creation")
    else:
        print("❌ Entity keys LOST after chain creation")

    # Now run verification
    print(f"\n🔍 Running integrity verification...")
    verification_result = (
        await reasoning_chain_verifier.verify_reasoning_chain_integrity(chain.chain_id)
    )

    print(f"Verification result: {verification_result['verified']}")
    for check_name, result in verification_result.get("checks", {}).items():
        print(f"   - {check_name}: {'✅' if result else '❌'}")

    # Check entity keys after verification
    print(
        f"Entity keys after verification: {list(quantum_ai_consent_manager.entity_keys.keys())}"
    )
    if entity.entity_id in quantum_ai_consent_manager.entity_keys:
        print("✅ Entity keys still available after verification")
    else:
        print("❌ Entity keys LOST after verification")

    # Test step-by-step verification
    print(f"\n🔍 Testing individual step verification...")
    first_step = chain.verified_steps[0]
    step_valid = await reasoning_chain_verifier._verify_step_quantum_signature(
        first_step
    )
    print(f"First step signature valid: {step_valid}")


if __name__ == "__main__":
    asyncio.run(debug_full_verification())
