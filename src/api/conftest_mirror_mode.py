"""Test fixtures for Mirror Mode API integration tests."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.capsule_schema import AuditCapsule, CapsuleStatus, RefusalCapsule, Verification
from src.engine.capsule_engine import CapsuleEngine
from src.mirror_mode import MirrorAgent


class MockPolicyEngine:
    """Mock implementation of the policy engine for testing."""

    def __init__(self, always_allow=True):
        self.always_allow = always_allow

    async def pre_creation_check(self, capsule):
        """Mock the pre-creation policy check."""
        if self.always_allow:
            return True, None
        else:
            return False, {
                "reason": "Policy violation detected",
                "violations": [{"rule": "test_rule", "severity": "high"}],
            }


@pytest.fixture
def mock_engine_with_mirror():
    """Create a test CapsuleEngine with a real MirrorAgent for integration tests."""
    # Create a mock engine
    engine = MagicMock(spec=CapsuleEngine)

    # Create a real MirrorAgent with mocked dependencies
    policy_engine = MockPolicyEngine(always_allow=True)
    mirror_agent = MirrorAgent(
        sample_rate=1.0,  # Always audit for tests
        strict_mode=False,
        policy_engine=policy_engine,
        capsule_engine=engine,  # Circular reference for capsule creation
    )

    # Override the mirror agent's _run_audit method for testing
    original_run_audit = mirror_agent._run_audit

    async def tracked_run_audit(capsule):
        """Track audit calls and run the original method."""
        if not hasattr(mirror_agent, "audit_calls"):
            mirror_agent.audit_calls = []
        mirror_agent.audit_calls.append(
            capsule.capsule_id if hasattr(capsule, "capsule_id") else "unknown"
        )
        return await original_run_audit(capsule)

    mirror_agent._run_audit = tracked_run_audit

    # Add the mirror agent to the engine
    engine.mirror_agent = mirror_agent

    # Set up necessary mock methods
    engine.get_capsule_async = AsyncMock()
    engine.create_capsule_async = AsyncMock()
    engine.query_capsules_async = AsyncMock()

    # Mock capsule creation with different policies
    async def mock_create_capsule(capsule):
        """Mock capsule creation that generates audit/refusal capsules."""
        if hasattr(capsule, "content") and "unsafe" in str(capsule.content).lower():
            # Create a refusal capsule
            await mirror_agent._run_audit(capsule)
            return None
        else:
            # Create a normal capsule and audit it
            await mirror_agent._run_audit(capsule)
            return capsule

    engine.create_capsule_async.side_effect = mock_create_capsule

    return engine


@pytest.fixture
def integration_test_app(app, mock_engine_with_mirror):
    """Create a test app with the mock engine."""
    app.engine = mock_engine_with_mirror
    return app


@pytest.fixture
def sample_capsules():
    """Create sample capsules for testing."""
    # Create a base capsule that would be audited
    base_capsule = MagicMock()
    base_capsule.capsule_id = "test_capsule_123"
    base_capsule.content = "Safe test content"

    # Create an unsafe capsule that would trigger a refusal
    unsafe_capsule = MagicMock()
    unsafe_capsule.capsule_id = "unsafe_capsule_456"
    unsafe_capsule.content = "Unsafe test content"

    # Create a sample audit capsule result
    audit_capsule = AuditCapsule(
        capsule_id="audit_" + base_capsule.capsule_id,
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        audit={
            "audited_capsule_id": base_capsule.capsule_id,
            "audit_score": 1.0,
            "violations": [],
        },
    )

    # Create a sample refusal capsule result
    refusal_capsule = RefusalCapsule(
        capsule_id="refusal_" + unsafe_capsule.capsule_id,
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.ACTIVE,
        verification=Verification(),
        refusal={
            "refused_capsule_id": unsafe_capsule.capsule_id,
            "audit_score": 0.0,
            "violations": [{"rule": "test_rule", "severity": "high"}],
            "reason": "Policy violation detected",
        },
    )

    return {
        "base": base_capsule,
        "unsafe": unsafe_capsule,
        "audit": audit_capsule,
        "refusal": refusal_capsule,
    }
