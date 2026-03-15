"""
Basic functionality tests to verify core components work.
"""

from datetime import datetime, timezone

import pytest
import pytest_asyncio

from src.capsule_schema import (
    CapsuleStatus,
    CapsuleType,
    ReasoningTraceCapsule,
    Verification,
)


def test_capsule_schema_imports():
    """Test that we can import all the basic schema classes."""
    assert CapsuleType.REASONING_TRACE == "reasoning_trace"
    assert CapsuleStatus.SEALED == "sealed"


def test_basic_capsule_creation():
    """Test creating a basic reasoning trace capsule."""
    verification = Verification(
        signature="ed25519:" + "a" * 128, merkle_root="sha256:" + "0" * 64
    )

    capsule = ReasoningTraceCapsule(
        capsule_id="caps_2025_07_09_abcdef1234567890",
        version="7.2",
        timestamp=datetime.now(timezone.utc),
        status=CapsuleStatus.DRAFT,
        verification=verification,
        reasoning_trace={
            "reasoning_steps": [
                {
                    "step_id": 1,
                    "operation": "observation",
                    "reasoning": "Test reasoning",
                    "confidence": 0.9,
                }
            ],
            "total_confidence": 0.9,
        },
    )

    assert capsule.capsule_type == CapsuleType.REASONING_TRACE
    assert capsule.capsule_id == "caps_2025_07_09_abcdef1234567890"


@pytest_asyncio.fixture
async def simple_engine():
    """Create a simple engine for testing without complex setup."""
    from src.engine.capsule_engine import CapsuleEngine
    from tests.mock_openai_client import MockOpenAIClient

    # Create engine without database for basic tests
    engine = CapsuleEngine(
        openai_client=MockOpenAIClient(),
        db_manager=None,  # Skip database for now
    )
    return engine


@pytest.mark.asyncio
async def test_engine_creation(simple_engine):
    """Test that we can create an engine instance."""
    assert simple_engine is not None
    assert hasattr(simple_engine, "agent_id")
    assert hasattr(simple_engine, "signing_key")
