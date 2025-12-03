#!/usr/bin/env python3
"""
Debug each step verification to find which one is failing.
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
)


async def debug_step_by_step():
    """Debug each step verification individually."""
    print("🔍 Debugging Step-by-Step Verification")
    print("=" * 50)

    # Register AI entity
    entity = await register_ai_entity(
        entity_name="StepTest-Claude",
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

    # Create a reasoning trace with multiple steps
    steps = [
        ReasoningStep("Step 1: Initial observation", StepType.OBSERVATION, 0.9),
        ReasoningStep("Step 2: Hypothesis formation", StepType.HYPOTHESIS, 0.8),
        ReasoningStep("Step 3: Evidence gathering", StepType.EVIDENCE, 0.85),
        ReasoningStep("Step 4: Final conclusion", StepType.CONCLUSION, 0.9),
    ]
    trace = ReasoningTrace(steps)

    # Create verified chain
    chain = await reasoning_chain_verifier.create_verified_reasoning_chain(
        entity.entity_id, trace, ReasoningVerificationLevel.STANDARD
    )
    print(f"✅ Created chain with {len(chain.verified_steps)} steps")

    # Test each step individually
    print(f"\n🔍 Testing each step individually:")
    for i, step in enumerate(chain.verified_steps):
        try:
            step_valid = await reasoning_chain_verifier._verify_step_quantum_signature(
                step
            )
            print(
                f"   Step {i+1}: {'✅' if step_valid else '❌'} - {step.original_step.content[:50]}..."
            )
            if not step_valid:
                print(f"      Step ID: {step.step_id}")
                print(f"      Chain ID: {step.chain_id}")
                print(f"      AI Entity ID: {step.ai_entity_id}")
                print(f"      Signature length: {len(step.quantum_signature)}")
        except Exception as e:
            print(f"   Step {i+1}: ❌ ERROR - {e}")

    # Now test the combined verification
    print(
        f"\n🔍 Testing combined verification (like in verify_reasoning_chain_integrity):"
    )
    quantum_signatures_valid = True
    for i, step in enumerate(chain.verified_steps):
        try:
            step_valid = await reasoning_chain_verifier._verify_step_quantum_signature(
                step
            )
            print(f"   Step {i+1} in loop: {'✅' if step_valid else '❌'}")
            if not step_valid:
                quantum_signatures_valid = False
                print(f"   Breaking at step {i+1}")
                break
        except Exception as e:
            print(f"   Step {i+1} in loop: ❌ ERROR - {e}")
            quantum_signatures_valid = False
            break

    print(f"Overall quantum signatures valid: {quantum_signatures_valid}")


if __name__ == "__main__":
    asyncio.run(debug_step_by_step())
