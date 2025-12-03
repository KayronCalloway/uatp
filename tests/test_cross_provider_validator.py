"""
Tests for cross-provider validation mechanisms.

These tests validate the cross-provider validation implementation for the UATP Capsule Engine,
ensuring proper validation of reasoning traces and capsules across multiple AI providers.
"""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.capsule_schema import CapsuleStatus, ReasoningTraceCapsule
from src.integrations.cross_provider_validator import (
    CrossProviderValidator,
    ValidationOptions,
    ValidationOutcome,
    ValidationResult,
)
from src.integrations.federated_registry import (
    FederatedModelRegistry,
    FederationMember,
    FederationRole,
)
from src.integrations.governance_enhanced_registry import ModelAccessPolicy
from src.integrations.multimodal_adapters import (
    ContentType,
    MediaContent,
    MediaFormat,
    MockMultiModalAdapter,
    MultiModalReasoningStep,
)


@pytest.fixture
def mock_adapters():
    """Create mock adapters for different providers."""
    openai_adapter = MockMultiModalAdapter()
    openai_adapter.provider_id = "openai"

    mistral_adapter = MockMultiModalAdapter()
    mistral_adapter.provider_id = "mistral"

    cohere_adapter = MockMultiModalAdapter()
    cohere_adapter.provider_id = "cohere"

    return {
        "openai": openai_adapter,
        "mistral": mistral_adapter,
        "cohere": cohere_adapter,
    }


@pytest.fixture
def sample_reasoning_steps():
    """Create sample reasoning steps for testing."""
    return [
        MultiModalReasoningStep(
            step_id=1,
            operation="analyze_query",
            reasoning="Analyzed user query about climate change",
            confidence=0.95,
            trace_id="trace-1234",
        ),
        MultiModalReasoningStep(
            step_id=2,
            operation="retrieve_data",
            reasoning="Retrieved relevant climate data from 2000-2020",
            confidence=0.87,
            parent_step_id=1,
            trace_id="trace-1234",
        ),
        MultiModalReasoningStep(
            step_id=3,
            operation="generate_response",
            reasoning="Generated response based on climate data analysis",
            confidence=0.92,
            parent_step_id=2,
            trace_id="trace-1234",
        ),
    ]


@pytest.fixture
def sample_output():
    """Create a sample AI output for testing."""
    return """
    Based on climate data from 2000-2020, global temperatures have risen by approximately 0.18°C per decade.
    This trend is consistent with the broader warming pattern observed since the industrial revolution.
    The data shows accelerating ice melt in polar regions and increasing frequency of extreme weather events.
    """


@pytest.fixture
def sample_capsule():
    """Create a sample capsule for testing."""
    capsule = MagicMock(spec=ReasoningTraceCapsule)
    capsule.id = str(uuid.uuid4())
    capsule.status = CapsuleStatus.VERIFIED
    capsule.signature = f"ed25519:{uuid.uuid4().hex}"
    capsule.content = json.dumps(
        {"type": "reasoning_trace", "steps": [{"step_id": 1, "operation": "analyze"}]}
    )
    return capsule


@pytest.fixture
def mock_federated_registry():
    """Create a mock federated registry for testing."""
    mock_registry = MagicMock(spec=FederatedModelRegistry)

    # Set up the member property
    mock_registry.member = FederationMember(
        id="test-org",
        name="Test Organization",
        role=FederationRole.COORDINATOR,
        verify_key="a" * 64,
        endpoint="https://test-org.example.com/api/federation",
    )

    # Set up the verify_federated_capsule method
    async def mock_verify_federated(*args, **kwargs):
        return {
            "verified": True,
            "valid_count": 2,
            "total_count": 3,
            "results": {
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
                },
            },
        }

    mock_registry.verify_federated_capsule = mock_verify_federated

    return mock_registry


@pytest.mark.asyncio
class TestCrossProviderValidator:
    """Test the CrossProviderValidator implementation."""

    async def test_initialization(self, mock_adapters, mock_federated_registry):
        """Test creating a validator."""
        # Create with just adapters
        validator1 = CrossProviderValidator(adapters=mock_adapters)
        assert len(validator1.adapters) == 3
        assert validator1.federation_enabled is False

        # Create with federation
        validator2 = CrossProviderValidator(federated_registry=mock_federated_registry)
        assert validator2.federation_enabled is True
        assert len(validator2.adapters) == 0

        # Create with both
        validator3 = CrossProviderValidator(
            adapters=mock_adapters, federated_registry=mock_federated_registry
        )
        assert validator3.federation_enabled is True
        assert len(validator3.adapters) == 3

    async def test_register_adapter(self):
        """Test registering provider adapters."""
        validator = CrossProviderValidator()

        # Initially no adapters
        assert len(validator.adapters) == 0

        # Register an adapter
        mock_adapter = MockMultiModalAdapter()
        mock_adapter.provider_id = "test-provider"

        await validator.register_adapter("test-provider", mock_adapter)

        # Verify adapter was registered
        assert len(validator.adapters) == 1
        assert "test-provider" in validator.adapters

        # Register a different adapter
        mock_adapter2 = MockMultiModalAdapter()
        mock_adapter2.provider_id = "another-provider"

        await validator.register_adapter("another-provider", mock_adapter2)
        assert len(validator.adapters) == 2

    async def test_validate_reasoning_trace(
        self, mock_adapters, sample_reasoning_steps, sample_output
    ):
        """Test validating a reasoning trace using multiple providers."""
        # Create validator with adapters
        validator = CrossProviderValidator(adapters=mock_adapters)

        # Mock the _validate_with_provider method to return consistent results
        async def mock_validate_with_provider(
            provider_id, prompt, inputs, original_output, timeout
        ):
            if provider_id == "openai":
                return {
                    "valid": True,
                    "explanation": "The reasoning and output are valid.",
                    "similarity": 0.85,
                    "model": "gpt-4",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            elif provider_id == "mistral":
                return {
                    "valid": True,
                    "explanation": "I agree with the reasoning process and output.",
                    "similarity": 0.82,
                    "model": "mistral-large",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                return {
                    "valid": False,
                    "explanation": "The reasoning contains inaccuracies.",
                    "similarity": 0.65,
                    "model": "command",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        # Patch the validation method
        with patch.object(
            validator,
            "_validate_with_provider",
            side_effect=mock_validate_with_provider,
        ):
            # Validate the reasoning trace
            options = ValidationOptions(min_providers=2, consensus_threshold=0.5)
            result = await validator.validate_reasoning_trace(
                reasoning_steps=sample_reasoning_steps,
                original_provider="anthropic",  # Use a provider not in our validators list
                original_output=sample_output,
                options=options,
            )

            # Check results
            assert result.outcome == ValidationOutcome.VALID  # 2/3 voted valid
            assert (
                result.consensus_score >= 0.6
            )  # Allow for some variance in consensus calculation
            assert len(result.provider_results) == 3
            assert result.provider_results["openai"]["valid"] is True
            assert result.provider_results["mistral"]["valid"] is True
            assert result.provider_results["cohere"]["valid"] is False

            # Check with higher threshold
            options = ValidationOptions(min_providers=2, consensus_threshold=0.8)
            result = await validator.validate_reasoning_trace(
                reasoning_steps=sample_reasoning_steps,
                original_provider="anthropic",
                original_output=sample_output,
                options=options,
            )

            # Should now be questionable as 2/3 is below 0.8 threshold
            assert result.outcome == ValidationOutcome.QUESTIONABLE

    async def test_extract_inputs_from_steps(self, mock_adapters):
        """Test extracting inputs from reasoning steps."""
        validator = CrossProviderValidator(adapters=mock_adapters)

        # Create steps with text and media inputs
        image = MediaContent(
            content_type=ContentType.IMAGE,
            format=MediaFormat.PNG,
            data=b"test_image_data",
            metadata={"test": True},
        )

        steps = [
            MultiModalReasoningStep(
                step_id=1,
                operation="analyze_text",
                reasoning="Analyzed text input",
                input_text="This is a test",
            ),
            MultiModalReasoningStep(
                step_id=2,
                operation="analyze_image",
                reasoning="Analyzed image",
                input_media=[image],
            ),
        ]

        inputs = validator._extract_inputs_from_steps(steps)

        # Should have 2 inputs (text and image)
        assert len(inputs) == 2
        assert inputs[0]["type"] == "text"
        assert inputs[0]["content"] == "This is a test"
        assert inputs[0]["step_id"] == 1

        assert inputs[1]["type"] == "image"
        assert inputs[1]["media"] == image
        assert inputs[1]["step_id"] == 2

    async def test_generate_validation_prompt(
        self, mock_adapters, sample_reasoning_steps, sample_output
    ):
        """Test generating a validation prompt."""
        validator = CrossProviderValidator(adapters=mock_adapters)

        prompt = validator._generate_validation_prompt(
            sample_reasoning_steps, sample_output
        )

        # Check the prompt contains expected elements
        assert "Validate the following reasoning process" in prompt
        assert "Step 1: analyze_query" in prompt
        assert "Step 2: retrieve_data" in prompt
        assert "Step 3: generate_response" in prompt
        assert "Based on climate data" in prompt  # Output text
        assert "Is this reasoning process and output valid?" in prompt

    async def test_parse_validation_response(self, mock_adapters):
        """Test parsing validation responses."""
        validator = CrossProviderValidator(adapters=mock_adapters)

        # Test clear positive response
        assert (
            validator._parse_validation_response(
                "Yes, this reasoning process and output is valid. The steps are logical."
            )
            is True
        )

        # Test clear negative response
        assert (
            validator._parse_validation_response(
                "No, this reasoning process and output is not valid. There are errors."
            )
            is False
        )

        # Test response with positive indicators
        assert (
            validator._parse_validation_response(
                "The reasoning is sound and the output is accurate based on the steps."
            )
            is True
        )

        # Test response with negative indicators
        assert (
            validator._parse_validation_response(
                "The reasoning contains inaccuracies and the output is incorrect."
            )
            is False
        )

        # Test mixed response but more negative
        assert (
            validator._parse_validation_response(
                "While parts of the reasoning are valid, there are significant errors that make the output unreasonable and incorrect."
            )
            is False
        )

        # Test mixed response but more positive
        assert (
            validator._parse_validation_response(
                "Although there is a minor issue with step 2, the overall reasoning is sound and the output is appropriate and valid."
            )
            is True
        )

    async def test_validate_capsule(
        self, mock_adapters, sample_capsule, mock_federated_registry
    ):
        """Test validating a capsule."""
        # Create validator with federation
        validator = CrossProviderValidator(
            adapters=mock_adapters, federated_registry=mock_federated_registry
        )

        # Mock local validation to succeed
        with patch.object(validator, "_validate_capsule_locally", return_value=True):
            # Test with federation
            result = await validator.validate_capsule(
                capsule=sample_capsule,
                options=ValidationOptions(min_providers=2, consensus_threshold=0.6),
            )

            # Should be valid (2/3 validators approved in mock federated registry)
            assert result.outcome == ValidationOutcome.VALID
            assert result.capsule_id == sample_capsule.id

            # Test with higher threshold
            result = await validator.validate_capsule(
                capsule=sample_capsule,
                options=ValidationOptions(min_providers=3, consensus_threshold=0.8),
            )

            # Should not be valid (only 2/3 validators approved)
            assert result.outcome == ValidationOutcome.INVALID

    async def test_validate_with_governance_policy(self, mock_adapters, sample_capsule):
        """Test validating a capsule against governance policies."""
        validator = CrossProviderValidator(adapters=mock_adapters)

        # Create a mock policy
        policy = MagicMock(spec=ModelAccessPolicy)
        policy.id = "test-policy"

        # First test with valid capsule but violates policy
        with patch.object(
            validator,
            "validate_capsule",
            return_value=ValidationResult(
                outcome=ValidationOutcome.VALID,
                validation_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                capsule_id=sample_capsule.id,
            ),
        ):
            # Mock the policy checks to fail
            with patch.object(
                validator, "_validate_capsule_locally", return_value=True
            ):
                # The validator's governance policy check method will check against policy attributes
                # We'll make the test capsule and policy attributes not match
                sample_capsule.type = "test_type"
                policy.allowed_capsule_types = ["other_type"]

                result = await validator.validate_with_governance_policy(
                    capsule=sample_capsule, policy=policy
                )

                # Should be invalid due to policy violation
                assert result.outcome == ValidationOutcome.INVALID
                assert "not allowed by policy" in result.validation_errors[0]

        # Now test with valid capsule that meets policy requirements
        with patch.object(
            validator,
            "validate_capsule",
            return_value=ValidationResult(
                outcome=ValidationOutcome.VALID,
                validation_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                capsule_id=sample_capsule.id,
            ),
        ):
            # Make the capsule type match the policy
            sample_capsule.type = "allowed_type"
            policy.allowed_capsule_types = ["allowed_type"]

            result = await validator.validate_with_governance_policy(
                capsule=sample_capsule, policy=policy
            )

            # Should be valid
            assert result.outcome == ValidationOutcome.VALID


@pytest.mark.asyncio
class TestCrossProviderIntegration:
    """Integration tests for the CrossProviderValidator."""

    async def test_end_to_end_validation(
        self, mock_adapters, sample_reasoning_steps, sample_output
    ):
        """Test an end-to-end validation flow."""
        # This test simulates the real workflow but with mock adapters
        validator = CrossProviderValidator(adapters=mock_adapters)

        # Run the validation
        result = await validator.validate_reasoning_trace(
            reasoning_steps=sample_reasoning_steps,
            original_provider="mistral",
            original_output=sample_output,
            options=ValidationOptions(min_providers=2, consensus_threshold=0.5),
        )

        # Check that we got a real result (don't assert exact values as the mocks might change)
        assert isinstance(result, ValidationResult)
        assert result.validation_id in validator.validation_history

        # Check that all providers were consulted (except the original)
        providers_used = list(result.provider_results.keys())
        assert "openai" in providers_used
        assert "cohere" in providers_used
        assert "mistral" not in providers_used  # Original provider should be excluded

    async def test_demo_validation(self):
        """Test the demo validation function."""
        from src.integrations.cross_provider_validator import (
            demo_cross_provider_validation,
        )

        # Just make sure the demo runs without errors
        with patch("builtins.print"):  # Suppress output
            await demo_cross_provider_validation()


if __name__ == "__main__":
    pytest.main(["-v"])
