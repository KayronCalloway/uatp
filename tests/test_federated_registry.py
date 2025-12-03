"""
Tests for federated AI model registry functionality.

These tests validate the federated registry implementation for the UATP Capsule Engine,
ensuring proper member management, model registration, and trace distribution.
"""

import os
import tempfile
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.capsule_schema import CapsuleStatus, ReasoningTraceCapsule
from src.integrations.federated_registry import (
    FederatedModelRegistry,
    FederationMember,
    FederationRole,
    FederationTrustConfig,
)
from src.integrations.multimodal_adapters import MultiModalReasoningStep


@pytest.fixture
def mock_signing_key():
    """Create a mock signing key for tests."""
    # Return a test hex key (not a real private key)
    return "f" * 64  # 32 bytes (64 hex chars)


@pytest.fixture
def mock_verify_key():
    """Create a mock verify key for tests."""
    # Return a test hex key (not a real public key)
    return "a" * 64


@pytest.fixture
def temp_registry_path():
    """Create a temporary directory for the registry data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_member():
    """Create a sample federation member for testing."""
    return FederationMember(
        id="test-org",
        name="Test Organization",
        role=FederationRole.VALIDATOR,
        verify_key="a" * 64,
        endpoint="https://test-org.example.com/api/federation",
    )


@pytest.fixture
def sample_members():
    """Create multiple sample federation members for testing."""
    return [
        FederationMember(
            id="org1",
            name="Organization 1",
            role=FederationRole.COORDINATOR,
            verify_key="b" * 64,
            endpoint="https://org1.example.com/api/federation",
        ),
        FederationMember(
            id="org2",
            name="Organization 2",
            role=FederationRole.MEMBER,
            verify_key="c" * 64,
            endpoint="https://org2.example.com/api/federation",
        ),
        FederationMember(
            id="org3",
            name="Organization 3",
            role=FederationRole.OBSERVER,
            verify_key="d" * 64,
            endpoint="https://org3.example.com/api/federation",
        ),
    ]


@pytest.fixture
def sample_reasoning_steps():
    """Create sample reasoning steps for testing."""
    return [
        MultiModalReasoningStep(
            step_id=1,
            operation="analyze_query",
            reasoning="Analyzed user query about climate change",
            confidence=0.95,
        ),
        MultiModalReasoningStep(
            step_id=2,
            operation="retrieve_data",
            reasoning="Retrieved relevant climate data",
            confidence=0.87,
            parent_step_id=1,
        ),
        MultiModalReasoningStep(
            step_id=3,
            operation="generate_response",
            reasoning="Generated response based on climate data analysis",
            confidence=0.92,
            parent_step_id=2,
        ),
    ]


@pytest.fixture
def mock_capsule_engine():
    """Create a mock capsule engine for testing."""
    mock_engine = MagicMock()

    # Mock the create_capsule method to return a capsule with an ID
    async def mock_create_capsule(*args, **kwargs):
        capsule = MagicMock(spec=ReasoningTraceCapsule)
        capsule.id = str(uuid.uuid4())
        capsule.status = CapsuleStatus.VERIFIED
        capsule.signature = f"ed25519:{uuid.uuid4().hex}"
        return capsule

    # Mock the verify_capsule method to return True
    async def mock_verify_capsule(capsule):
        return True

    mock_engine.create_capsule = mock_create_capsule
    mock_engine.verify_capsule = mock_verify_capsule
    return mock_engine


@pytest.mark.asyncio
class TestFederatedModelRegistry:
    """Test the FederatedModelRegistry implementation."""

    async def test_initialization(
        self, temp_registry_path, mock_signing_key, mock_capsule_engine
    ):
        """Test creating a federated registry."""
        # Set environment variable for signing key
        with patch.dict(os.environ, {"UATP_SIGNING_KEY": mock_signing_key}):
            registry = FederatedModelRegistry(
                member_id="test-org",
                member_name="Test Organization",
                registry_path=temp_registry_path,
                capsule_engine=mock_capsule_engine,
            )

            assert registry.member.id == "test-org"
            assert registry.member.name == "Test Organization"
            assert registry.member.role == FederationRole.COORDINATOR  # Default role
            assert registry.registry_path == temp_registry_path
            assert len(registry.members) == 1  # Should contain self as member

    async def test_add_federation_member(
        self, temp_registry_path, mock_signing_key, sample_member, mock_capsule_engine
    ):
        """Test adding a federation member."""
        with patch.dict(os.environ, {"UATP_SIGNING_KEY": mock_signing_key}):
            registry = FederatedModelRegistry(
                member_id="host-org",
                member_name="Host Organization",
                registry_path=temp_registry_path,
                capsule_engine=mock_capsule_engine,
            )

            # Add a federation member
            await registry.add_federation_member(sample_member)

            # Verify member was added
            assert len(registry.members) == 2  # Self + added member
            assert "test-org" in registry.members
            assert registry.members["test-org"].name == "Test Organization"
            assert registry.members["test-org"].role == FederationRole.VALIDATOR

    async def test_remove_federation_member(
        self, temp_registry_path, mock_signing_key, sample_member, mock_capsule_engine
    ):
        """Test removing a federation member."""
        with patch.dict(os.environ, {"UATP_SIGNING_KEY": mock_signing_key}):
            registry = FederatedModelRegistry(
                member_id="host-org",
                member_name="Host Organization",
                registry_path=temp_registry_path,
                capsule_engine=mock_capsule_engine,
            )

            # Add and then remove a federation member
            await registry.add_federation_member(sample_member)
            assert "test-org" in registry.members

            await registry.remove_federation_member("test-org")

            # Verify member was removed
            assert len(registry.members) == 1  # Only self remains
            assert "test-org" not in registry.members

    async def test_register_model_with_federation(
        self, temp_registry_path, mock_signing_key, sample_members, mock_capsule_engine
    ):
        """Test registering a model with the federation."""
        with patch.dict(os.environ, {"UATP_SIGNING_KEY": mock_signing_key}):
            # Create registry with multiple members
            registry = FederatedModelRegistry(
                member_id="host-org",
                member_name="Host Organization",
                registry_path=temp_registry_path,
                capsule_engine=mock_capsule_engine,
            )

            # Add some federation members
            for member in sample_members:
                await registry.add_federation_member(member)

            # Mock the distribute_capsule method to avoid HTTP requests
            with patch.object(registry, "_distribute_capsule", return_value=True):
                # Register a model
                model_id = "gpt-4"
                provider = "openai"

                # Register the model
                capsule_id = await registry.register_model_with_federation(
                    model_id=model_id,
                    provider=provider,
                    access_level="restricted",
                    metadata={"capabilities": ["text"]},
                )

                # Verify a capsule ID was returned
                assert capsule_id is not None

                # The model should be in the registry's models
                assert model_id in registry.models
                assert registry.models[model_id]["provider"] == provider
                assert registry.models[model_id]["access_level"] == "restricted"

    async def test_distribute_reasoning_trace(
        self,
        temp_registry_path,
        mock_signing_key,
        sample_members,
        sample_reasoning_steps,
        mock_capsule_engine,
    ):
        """Test distributing a reasoning trace to federation members."""
        with patch.dict(os.environ, {"UATP_SIGNING_KEY": mock_signing_key}):
            # Create registry with multiple members
            registry = FederatedModelRegistry(
                member_id="host-org",
                member_name="Host Organization",
                registry_path=temp_registry_path,
                capsule_engine=mock_capsule_engine,
            )

            # Add some federation members
            for member in sample_members:
                await registry.add_federation_member(member)

            # Mock the distribute_capsule method to avoid HTTP requests
            with patch.object(registry, "_distribute_capsule", return_value=True):
                # Distribute a reasoning trace
                trace_id = str(uuid.uuid4())
                provider = "openai"

                capsule_id = await registry.distribute_reasoning_trace(
                    trace_id=trace_id,
                    provider=provider,
                    reasoning_steps=sample_reasoning_steps,
                    metadata={"query": "What is climate change?"},
                )

                # Verify a capsule ID was returned
                assert capsule_id is not None

                # The trace should be in the registry's traces
                assert trace_id in registry.traces
                assert registry.traces[trace_id]["provider"] == provider

                # Verify the trace contains the reasoning steps
                trace_content = registry.traces[trace_id]["content"]
                assert len(trace_content["reasoning_steps"]) == len(
                    sample_reasoning_steps
                )

    async def test_aggregate_federated_traces(
        self, temp_registry_path, mock_signing_key, mock_capsule_engine
    ):
        """Test aggregating traces from federation members."""
        with patch.dict(os.environ, {"UATP_SIGNING_KEY": mock_signing_key}):
            registry = FederatedModelRegistry(
                member_id="host-org",
                member_name="Host Organization",
                registry_path=temp_registry_path,
                capsule_engine=mock_capsule_engine,
            )

            # Mock trace data to simulate stored traces
            trace_id1 = str(uuid.uuid4())
            trace_id2 = str(uuid.uuid4())

            registry.traces = {
                trace_id1: {
                    "id": trace_id1,
                    "provider": "openai",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "content": {"reasoning_steps": [{"step_id": 1}]},
                },
                trace_id2: {
                    "id": trace_id2,
                    "provider": "mistral",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "content": {"reasoning_steps": [{"step_id": 1}, {"step_id": 2}]},
                },
            }

            # Mock external trace responses
            mock_external_traces = [
                {
                    "id": str(uuid.uuid4()),
                    "provider": "openai",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "content": {"reasoning_steps": [{"step_id": 3}]},
                }
            ]

            # Mock the query_federated_traces method
            with patch.object(
                registry, "_query_federated_traces", return_value=mock_external_traces
            ):
                # Query with a filter for openai provider
                results = await registry.aggregate_federated_traces(
                    {"provider": "openai"}
                )

                # Should include local openai trace and the external one
                assert len(results) == 2
                providers = [r.get("provider") for r in results]
                assert all(p == "openai" for p in providers)

    async def test_verify_federated_capsule(
        self, temp_registry_path, mock_signing_key, sample_members, mock_capsule_engine
    ):
        """Test verifying a capsule with federation members."""
        with patch.dict(os.environ, {"UATP_SIGNING_KEY": mock_signing_key}):
            # Create registry with multiple members
            registry = FederatedModelRegistry(
                member_id="host-org",
                member_name="Host Organization",
                registry_path=temp_registry_path,
                capsule_engine=mock_capsule_engine,
            )

            # Add some federation validator members
            for member in sample_members:
                await registry.add_federation_member(member)

            # Create a mock capsule
            mock_capsule = MagicMock(spec=ReasoningTraceCapsule)
            mock_capsule.id = str(uuid.uuid4())
            mock_capsule.status = CapsuleStatus.VERIFIED
            mock_capsule.signature = f"ed25519:{uuid.uuid4().hex}"

            # Mock validation responses from federation members
            mock_validation_responses = {
                "org1": {
                    "valid": True,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "org2": {
                    "valid": True,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                "org3": {
                    "valid": False,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": "Invalid signature",
                },
            }

            # Mock the request_capsule_verification method
            with patch.object(
                registry,
                "_request_capsule_verification",
                side_effect=lambda member_id, capsule: mock_validation_responses.get(
                    member_id, {"valid": False}
                ),
            ):
                # Verify the capsule
                result = await registry.verify_federated_capsule(
                    capsule=mock_capsule, required_validators=2
                )

                # Check the result format
                assert "results" in result
                assert len(result["results"]) == len(mock_validation_responses)
                assert result["valid_count"] == 2  # Two valid responses
                assert (
                    result["verified"] is True
                )  # Should be verified as we got 2 valid responses

                # Test with higher required validators
                result = await registry.verify_federated_capsule(
                    capsule=mock_capsule, required_validators=3
                )

                assert result["valid_count"] == 2
                assert (
                    result["verified"] is False
                )  # Should not be verified as we needed 3


@pytest.mark.asyncio
class TestFederationTrustConfig:
    """Test the FederationTrustConfig implementation."""

    async def test_trust_scoring(self, sample_members):
        """Test trust scoring for federation members."""
        # Create a trust config
        trust_config = FederationTrustConfig()

        # Add trust scores for members
        for i, member in enumerate(sample_members):
            trust_config.set_trust_score(member.id, 0.5 + i * 0.1)  # 0.5, 0.6, 0.7

        # Test getting trust scores
        assert trust_config.get_trust_score("org1") == 0.5
        assert trust_config.get_trust_score("org2") == 0.6
        assert trust_config.get_trust_score("org3") == 0.7

        # Test default for unknown member
        assert trust_config.get_trust_score("unknown") == 0.0

        # Test calculating weighted trust
        verification_results = {
            "org1": {"valid": True},
            "org2": {"valid": False},
            "org3": {"valid": True},
        }

        # Weighted score should be (0.5*1 + 0.6*0 + 0.7*1) / (0.5+0.6+0.7)
        expected_score = (0.5 * 1 + 0.6 * 0 + 0.7 * 1) / (0.5 + 0.6 + 0.7)
        actual_score = trust_config.calculate_weighted_trust(verification_results)

        assert (
            abs(actual_score - expected_score) < 0.001
        )  # Allow small float rounding errors


if __name__ == "__main__":
    pytest.main(["-v"])
