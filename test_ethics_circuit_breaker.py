#!/usr/bin/env python3
"""
Test the ethics circuit breaker with minimal dependencies.
"""

import asyncio
import sys

sys.path.append("src")

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


# Mock the required classes to test the circuit breaker logic
class CapsuleType(Enum):
    REASONING = "reasoning"


class CapsuleStatus(Enum):
    ACTIVE = "active"
    QUARANTINED = "quarantined"


@dataclass
class MockCapsule:
    capsule_id: str
    capsule_type: CapsuleType
    timestamp: datetime
    status: CapsuleStatus


class EthicalViolationType(Enum):
    BIAS_DETECTION = "bias_detection"
    HARMFUL_CONTENT = "harmful_content"
    PRIVACY_VIOLATION = "privacy_violation"


class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InterventionAction(Enum):
    WARNING = "warning"
    CONTENT_FILTER = "content_filter"
    QUARANTINE = "quarantine"
    BLOCK = "block"


# Mock RECT system for testing
class MockRECTSystem:
    def evaluate_capsule_ethics(self, capsule):
        # Mock evaluation - return good score for safe content
        print(f"DEBUG: Evaluating capsule {capsule.capsule_id}")
        print(
            f"DEBUG: Checking if 'safe' in '{capsule.capsule_id}': {'safe' in capsule.capsule_id}"
        )
        print(
            f"DEBUG: Checking if 'unsafe' in '{capsule.capsule_id}': {'unsafe' in capsule.capsule_id}"
        )

        if "unsafe" in capsule.capsule_id:
            print("DEBUG: Returning unsafe result")
            result = {
                "ethics_score": 0.3,  # Low score to trigger refusal
                "bias_detected": True,
                "violations": [EthicalViolationType.HARMFUL_CONTENT],
            }
        elif "safe" in capsule.capsule_id:
            print("DEBUG: Returning safe result")
            result = {"ethics_score": 0.9, "bias_detected": False, "violations": []}
        else:
            print("DEBUG: Returning default unsafe result")
            result = {
                "ethics_score": 0.3,
                "bias_detected": True,
                "violations": [EthicalViolationType.HARMFUL_CONTENT],
            }

        print(f"DEBUG: Returning result: {result}")
        return result


# Mock audit emitter
class MockAuditEmitter:
    def emit_capsule_refused(self, capsule_id, reason, severity):
        print(f"📝 Audit: Capsule {capsule_id} refused - {reason} ({severity})")


# Import the main components we need to test
# Patch the dependencies
import src.engine.ethics_circuit_breaker as ecb_module
from src.engine.ethics_circuit_breaker import (
    EthicsCircuitBreaker,
)

ecb_module.RECTSystem = MockRECTSystem
ecb_module.audit_emitter = MockAuditEmitter()


async def test_ethics_circuit_breaker():
    """Test the ethics circuit breaker with mocked dependencies."""
    print("🛡️ Ethics Circuit Breaker Test")
    print("=" * 40)

    # Create circuit breaker with manual mock injection
    circuit_breaker = EthicsCircuitBreaker(enable_refusal=True, strict_mode=False)
    # Manually replace the RECT system
    circuit_breaker.rect_system = MockRECTSystem()

    # Create test capsules
    safe_capsule = MockCapsule(
        capsule_id="safe_test_001",
        capsule_type=CapsuleType.REASONING,
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
    )

    unsafe_capsule = MockCapsule(
        capsule_id="unsafe_test_001",
        capsule_type=CapsuleType.REASONING,
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
    )

    # Test safe capsule
    print("Testing safe capsule...")
    allowed, refusal = await circuit_breaker.pre_creation_check(safe_capsule)
    print(f"✅ Safe capsule allowed: {allowed}")

    # Test unsafe capsule
    print("\nTesting unsafe capsule...")
    print(f"Circuit breaker threshold: {circuit_breaker.refusal_threshold}")
    allowed, refusal = await circuit_breaker.pre_creation_check(unsafe_capsule)
    print(f"❌ Unsafe capsule allowed: {allowed}")
    if refusal:
        print(f"❌ Refusal reason: {refusal.refusal_reason.value}")
        print(f"❌ Explanation: {refusal.explanation}")
    else:
        print("❌ No refusal recorded")

    # Test ethics evaluation on both capsules
    print("\nTesting ethics evaluation...")
    print("Safe capsule evaluation:")
    evaluation = await circuit_breaker.evaluate_capsule_ethics(safe_capsule)
    print(f"✅ Ethics score: {evaluation.confidence:.2f}")
    print(f"✅ Severity: {evaluation.severity.value}")
    print(f"✅ Intervention: {evaluation.intervention_action.value}")

    print("\nUnsafe capsule evaluation:")
    evaluation = await circuit_breaker.evaluate_capsule_ethics(unsafe_capsule)
    print(f"❌ Ethics score: {evaluation.confidence:.2f}")
    print(f"❌ Severity: {evaluation.severity.value}")
    print(f"❌ Intervention: {evaluation.intervention_action.value}")
    print(f"❌ Allowed: {evaluation.allowed}")

    # Get statistics
    stats = circuit_breaker.get_refusal_statistics()
    print("\n📊 Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n🎉 Ethics circuit breaker test complete!")


# Run the test
asyncio.run(test_ethics_circuit_breaker())
