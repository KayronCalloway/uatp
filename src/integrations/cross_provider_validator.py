"""
Cross-Provider Validation Mechanisms for UATP Capsule Engine.

This module implements validation mechanisms for cross-checking AI outputs,
reasoning traces, and capsules across multiple providers to ensure consistency,
reliability, and compliance with governance policies.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from src.capsule_schema import ReasoningTraceCapsule
from src.integrations.federated_registry import (
    FederatedModelRegistry,
)
from src.integrations.governance_enhanced_registry import (
    ModelAccessPolicy,
)
from src.integrations.multimodal_adapters import (
    MediaContent,
    MultiModalProviderAdapter,
    MultiModalReasoningStep,
)

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation levels for cross-provider validation."""

    MINIMAL = auto()  # Basic sanity checks
    STANDARD = auto()  # Normal validation checks
    STRICT = auto()  # Rigorous validation with multiple providers
    GOVERNANCE = auto()  # Validation with governance policy enforcement


class ValidationOutcome(Enum):
    """Outcome of a validation process."""

    VALID = auto()  # Passed all validation checks
    QUESTIONABLE = auto()  # Passed some checks but not all
    INVALID = auto()  # Failed validation
    ERROR = auto()  # Error during validation process


@dataclass
class ValidationOptions:
    """Options for the validation process."""

    level: ValidationLevel = ValidationLevel.STANDARD
    min_providers: int = 1  # Minimum number of providers to cross-validate with
    consensus_threshold: float = 0.7  # Percentage agreement required
    timeout_seconds: int = 30  # Timeout for validation requests
    require_governance: bool = False  # Whether to require governance validation


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    outcome: ValidationOutcome
    validation_id: str
    timestamp: datetime
    capsule_id: Optional[str] = None
    trace_id: Optional[str] = None
    provider_results: Dict[str, Any] = field(default_factory=dict)
    consensus_score: float = 0.0
    validation_errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CrossProviderValidator:
    """
    Validator for cross-checking AI outputs and reasoning traces
    across multiple providers.

    This class implements mechanisms to:
    1. Validate reasoning traces using multiple AI providers
    2. Cross-check capsule content for consistency
    3. Ensure governance policy compliance
    4. Create validation capsules for audit purposes
    """

    def __init__(
        self,
        federated_registry: Optional[FederatedModelRegistry] = None,
        adapters: Optional[Dict[str, MultiModalProviderAdapter]] = None,
    ):
        """
        Initialize the cross-provider validator.

        Args:
            federated_registry: Optional federated registry for validation
            adapters: Dictionary of provider adapters for validation
        """
        self.federated_registry = federated_registry
        self.adapters = adapters or {}

        # Validation history
        self.validation_history: Dict[str, ValidationResult] = {}

        # Flag to indicate whether we can use federation for validation
        self.federation_enabled = federated_registry is not None

    async def register_adapter(
        self, provider_id: str, adapter: MultiModalProviderAdapter
    ):
        """Register a new provider adapter for validation."""
        if provider_id in self.adapters:
            logger.warning(f"Overwriting existing adapter for provider {provider_id}")

        self.adapters[provider_id] = adapter
        logger.info(f"Registered adapter for provider {provider_id}")

    async def validate_reasoning_trace(
        self,
        reasoning_steps: List[MultiModalReasoningStep],
        original_provider: str,
        original_output: str,
        options: Optional[ValidationOptions] = None,
    ) -> ValidationResult:
        """
        Validate a reasoning trace using other providers.

        Args:
            reasoning_steps: The reasoning steps to validate
            original_provider: The provider that generated the original trace
            original_output: The original output text/content
            options: Validation options

        Returns:
            ValidationResult with the outcome of validation
        """
        options = options or ValidationOptions()
        validation_id = str(uuid.uuid4())

        # Initialize validation result
        result = ValidationResult(
            outcome=ValidationOutcome.ERROR,  # Default to ERROR until validation completes
            validation_id=validation_id,
            timestamp=datetime.now(timezone.utc),
            trace_id=reasoning_steps[0].trace_id
            if reasoning_steps and hasattr(reasoning_steps[0], "trace_id")
            else None,
            provider_results={},
            metadata={"original_provider": original_provider},
        )

        # Get available providers for validation (excluding the original)
        validation_providers = [p for p in self.adapters if p != original_provider]

        if not validation_providers:
            result.validation_errors.append("No validation providers available")
            logger.warning("No alternative providers available for validation")
            return result

        if len(validation_providers) < options.min_providers:
            result.validation_errors.append(
                f"Insufficient validation providers. Need {options.min_providers}, have {len(validation_providers)}"
            )
            logger.warning(
                f"Only {len(validation_providers)} providers available for validation, need {options.min_providers}"
            )
            # Continue anyway with what we have

        # Extract inputs from reasoning steps
        inputs = self._extract_inputs_from_steps(reasoning_steps)

        # Generate prompt for validation based on steps
        validation_prompt = self._generate_validation_prompt(
            reasoning_steps, original_output
        )

        # Track validation responses
        validation_responses = []

        # Run validation with each provider
        tasks = []
        # Send validation requests to *all* available providers so that
        # `provider_results` includes every adapter (tests rely on this) – we
        # still warn if we have fewer than `min_providers`, but we no longer
        # artificially truncate the list here.
        for provider_id in validation_providers:
            if provider_id in self.adapters:
                task = asyncio.create_task(
                    self._validate_with_provider(
                        provider_id=provider_id,
                        prompt=validation_prompt,
                        inputs=inputs,
                        original_output=original_output,
                        timeout=options.timeout_seconds,
                    )
                )
                tasks.append(task)

        # Wait for all validation tasks to complete
        if tasks:
            validation_responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process validation responses
        valid_responses = 0
        total_responses = 0

        for i, response in enumerate(validation_responses):
            provider_id = (
                validation_providers[i] if i < len(validation_providers) else "unknown"
            )

            if isinstance(response, Exception):
                # Handle exception
                result.provider_results[provider_id] = {
                    "valid": False,
                    "error": str(response),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                logger.error(
                    f"Error validating with provider {provider_id}: {response}"
                )
                continue

            # Record provider result
            result.provider_results[provider_id] = response

            # Count valid responses
            total_responses += 1
            if response.get("valid", False):
                valid_responses += 1

        # Calculate consensus score
        if total_responses > 0:
            result.consensus_score = valid_responses / total_responses

            # Determine outcome based on consensus
            if result.consensus_score >= options.consensus_threshold:
                result.outcome = ValidationOutcome.VALID
            elif result.consensus_score > 0:
                result.outcome = ValidationOutcome.QUESTIONABLE
            else:
                result.outcome = ValidationOutcome.INVALID
        else:
            result.outcome = ValidationOutcome.ERROR
            result.validation_errors.append("No validation responses received")

        # Store validation result in history
        self.validation_history[validation_id] = result

        # If federation is enabled, record the validation result
        if self.federation_enabled and self.federated_registry:
            try:
                # Create a validation record to distribute to federation
                validation_record = {
                    "validation_id": validation_id,
                    "outcome": result.outcome.name,
                    "consensus_score": result.consensus_score,
                    "original_provider": original_provider,
                    "validation_providers": list(result.provider_results.keys()),
                    "timestamp": result.timestamp.isoformat(),
                }

                # We would distribute this to the federation in a real implementation
                logger.info(
                    f"Would distribute validation result {validation_id} to federation"
                )

            except Exception as e:
                logger.error(f"Error recording validation in federation: {e}")

        return result

    def _extract_inputs_from_steps(
        self, steps: List[MultiModalReasoningStep]
    ) -> List[Dict[str, Any]]:
        """Extract inputs from reasoning steps for validation."""
        inputs = []

        for step in steps:
            # Extract text inputs
            if hasattr(step, "input_text") and step.input_text:
                inputs.append(
                    {
                        "type": "text",
                        "content": step.input_text,
                        "step_id": step.step_id,
                    }
                )

            # Extract media inputs
            if hasattr(step, "input_media") and step.input_media:
                for media in step.input_media:
                    inputs.append(
                        {
                            "type": media.content_type.value,
                            "media": media,  # Include actual media content
                            "step_id": step.step_id,
                        }
                    )

        return inputs

    def _generate_validation_prompt(
        self, steps: List[MultiModalReasoningStep], output: str
    ) -> str:
        """Generate a prompt for validation based on reasoning steps."""
        # Create a detailed prompt describing the reasoning process
        prompt = "Validate the following reasoning process and its output:\n\n"

        for step in steps:
            prompt += f"Step {step.step_id}: {step.operation}\n"
            prompt += f"Reasoning: {step.reasoning}\n"

            if hasattr(step, "confidence") and step.confidence is not None:
                prompt += f"Confidence: {step.confidence:.2f}\n"

            if hasattr(step, "parent_step_id") and step.parent_step_id is not None:
                if isinstance(step.parent_step_id, list):
                    parents = ", ".join(map(str, step.parent_step_id))
                    prompt += f"Based on steps: {parents}\n"
                else:
                    prompt += f"Based on step: {step.parent_step_id}\n"

            prompt += "\n"

        prompt += f"\nFinal output:\n{output}\n\n"
        prompt += "Is this reasoning process and output valid? Provide a yes/no answer and explanation."

        return prompt

    async def _validate_with_provider(
        self,
        provider_id: str,
        prompt: str,
        inputs: List[Dict[str, Any]],
        original_output: str,
        timeout: int,
    ) -> Dict[str, Any]:
        """Validate using a specific provider."""
        adapter = self.adapters.get(provider_id)
        if not adapter:
            return {
                "valid": False,
                "error": f"No adapter available for provider {provider_id}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        try:
            # Prepare input content for validation
            media_inputs = [
                input["media"]
                for input in inputs
                if input["type"] != "text" and "media" in input
            ]

            # Generate validation response
            if media_inputs:
                # Use multi-modal validation
                result = await asyncio.wait_for(
                    adapter.multi_modal_generate(
                        model=await self._get_best_model_for_provider(
                            provider_id, media_inputs
                        ),
                        inputs=media_inputs,
                        prompt=prompt,
                    ),
                    timeout=timeout,
                )
                validation_text = result.content
            else:
                # Use text-only validation
                result = await asyncio.wait_for(
                    adapter.generate(
                        model=await self._get_best_model_for_provider(provider_id),
                        prompt=prompt,
                        system_prompt="You are a validation agent. Review the reasoning and output provided, and determine if it is valid.",
                    ),
                    timeout=timeout,
                )
                validation_text = result.content

            # Parse validation response
            is_valid = self._parse_validation_response(validation_text)

            # Simple semantic comparison of outputs
            similarity = self._calculate_similarity(original_output, validation_text)

            return {
                "valid": is_valid,
                "explanation": validation_text,
                "similarity": similarity,
                "model": result.model,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except asyncio.TimeoutError:
            return {
                "valid": False,
                "error": f"Validation with provider {provider_id} timed out after {timeout} seconds",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Error during validation with provider {provider_id}: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def _get_best_model_for_provider(
        self, provider_id: str, media_inputs: List[MediaContent] = None
    ) -> str:
        """Get the best available model for a provider based on the inputs."""
        adapter = self.adapters.get(provider_id)
        if not adapter:
            raise ValueError(f"No adapter available for provider {provider_id}")

        available_models = await adapter.list_models()

        # If we have media inputs, prefer models that can handle them
        if media_inputs:
            content_types = {media.content_type for media in media_inputs}

            # For simplicity, look for models with "vision" or "multimodal" in their name
            for model in available_models:
                if "vision" in model.lower() or "multimodal" in model.lower():
                    return model

        # Otherwise return the first available model (or a default)
        if available_models:
            return available_models[0]

        # If no models, return a provider-specific default
        provider_defaults = {
            "openai": "gpt-4",
            "mistral": "mistral-large-latest",
            "cohere": "command",
            "anthropic": "claude-2",
        }

        return provider_defaults.get(provider_id, "default-model")

    def _parse_validation_response(self, response: str) -> bool:
        """Parse a validation response to determine if it indicates validity."""
        # Simple heuristic: look for positive validation indicators
        response_lower = response.lower()

        # Look for clear yes/no statements
        if "yes, this reasoning process and output is valid" in response_lower:
            return True
        if "no, this reasoning process and output is not valid" in response_lower:
            return False

        # Check for other indicators
        positive_indicators = [
            "valid",
            "correct",
            "accurate",
            "sound",
            "reasonable",
            "appropriate",
        ]
        negative_indicators = [
            "invalid",
            "incorrect",
            "inaccurate",
            "unsound",
            "unreasonable",
            "inappropriate",
            "error",
        ]

        # Simple scoring approach
        score = 0
        for indicator in positive_indicators:
            if indicator in response_lower:
                score += 1

        for indicator in negative_indicators:
            if indicator in response_lower:
                score -= 1

        # Consider valid if more positive than negative indicators
        return score > 0

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.

        This is a simple implementation. In a production system,
        you would use proper embedding-based similarity.
        """
        # Very naive approach - in real implementation use embeddings
        # Just checking for content overlap as a basic measure
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        common_words = words1.intersection(words2)

        # Jaccard similarity
        return len(common_words) / len(words1.union(words2))

    async def validate_capsule(
        self,
        capsule: ReasoningTraceCapsule,
        options: Optional[ValidationOptions] = None,
    ) -> ValidationResult:
        """
        Validate a capsule using federated validation mechanisms.

        Args:
            capsule: The capsule to validate
            options: Validation options

        Returns:
            ValidationResult with the outcome of validation
        """
        options = options or ValidationOptions()
        validation_id = str(uuid.uuid4())

        # Initialize validation result
        result = ValidationResult(
            outcome=ValidationOutcome.ERROR,  # Default to ERROR until validation completes
            validation_id=validation_id,
            timestamp=datetime.now(timezone.utc),
            capsule_id=capsule.id if hasattr(capsule, "id") else None,
            provider_results={},
            metadata={},
        )

        # First perform local capsule validation
        local_valid = await self._validate_capsule_locally(capsule)
        result.provider_results["local"] = {
            "valid": local_valid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # If federation is enabled, use federated validation
        if self.federation_enabled and self.federated_registry:
            try:
                fed_validation = await self.federated_registry.verify_federated_capsule(
                    capsule=capsule, required_validators=options.min_providers
                )

                # Process federation results
                validators_valid = 0
                total_validators = 0

                for validator_id, validator_result in fed_validation.get(
                    "results", {}
                ).items():
                    if (
                        validator_id != self.federated_registry.member.id
                    ):  # Skip our own result
                        result.provider_results[validator_id] = validator_result
                        total_validators += 1

                        if validator_result.get("valid", False):
                            validators_valid += 1

                # Calculate consensus score
                if total_validators > 0:
                    result.consensus_score = validators_valid / total_validators

                    # Determine outcome based on consensus
                    if result.consensus_score >= options.consensus_threshold:
                        result.outcome = ValidationOutcome.VALID
                    elif result.consensus_score > 0:
                        result.outcome = ValidationOutcome.QUESTIONABLE
                    else:
                        result.outcome = ValidationOutcome.INVALID
                elif local_valid:
                    # If no validators but locally valid
                    result.outcome = ValidationOutcome.QUESTIONABLE
                    result.validation_errors.append(
                        "No federation validators available, but locally valid"
                    )
                else:
                    result.outcome = ValidationOutcome.INVALID
                    result.validation_errors.append(
                        "Invalid locally and no federation validators"
                    )

            except Exception as e:
                logger.error(f"Error during federated capsule validation: {e}")
                result.validation_errors.append(
                    f"Federation validation error: {str(e)}"
                )

                # Fall back to local validation
                if local_valid:
                    result.outcome = ValidationOutcome.QUESTIONABLE
                    result.validation_errors.append(
                        "Federation validation failed, using local result only"
                    )
                else:
                    result.outcome = ValidationOutcome.INVALID

        else:
            # No federation, use local validation only
            if local_valid:
                result.outcome = ValidationOutcome.VALID
            else:
                result.outcome = ValidationOutcome.INVALID
                result.validation_errors.append(
                    "Capsule is invalid locally and federation not available"
                )

        # Store validation result in history
        self.validation_history[validation_id] = result

        return result

    async def _validate_capsule_locally(self, capsule: ReasoningTraceCapsule) -> bool:
        """Perform local validation of a capsule."""
        # Check if capsule has required fields
        if not hasattr(capsule, "id") or not capsule.id:
            return False

        if not hasattr(capsule, "content") or not capsule.content:
            return False

        if not hasattr(capsule, "signature") or not capsule.signature:
            return False

        # Check signature format (assuming Ed25519 signature)
        if not capsule.signature.startswith("ed25519:"):
            return False

        # In a real implementation, we would verify the signature
        # against the capsule content using the appropriate public key
        # This is a placeholder for that verification

        return True  # Placeholder - assume valid for demo purposes

    async def validate_with_governance_policy(
        self, capsule: ReasoningTraceCapsule, policy: ModelAccessPolicy
    ) -> ValidationResult:
        """
        Validate a capsule against governance policies.

        Args:
            capsule: The capsule to validate
            policy: The governance policy to validate against

        Returns:
            ValidationResult with the outcome of validation
        """
        options = ValidationOptions(level=ValidationLevel.GOVERNANCE)
        validation_id = str(uuid.uuid4())

        # Initialize validation result
        result = ValidationResult(
            outcome=ValidationOutcome.ERROR,  # Default to ERROR until validation completes
            validation_id=validation_id,
            timestamp=datetime.now(timezone.utc),
            capsule_id=capsule.id if hasattr(capsule, "id") else None,
            provider_results={},
            metadata={
                "governance_policy_id": policy.id if hasattr(policy, "id") else None
            },
        )

        # First validate the capsule itself
        base_validation = await self.validate_capsule(capsule, options)

        # If capsule is invalid, we don't need to check policies
        if base_validation.outcome == ValidationOutcome.INVALID:
            result.outcome = ValidationOutcome.INVALID
            result.validation_errors = base_validation.validation_errors
            result.validation_errors.append("Capsule failed basic validation")
            return result

        # Check capsule against governance policies
        policy_valid = True
        policy_errors = []

        # Example policy checks (customize based on actual policy structure)

        # Check if capsule type is allowed
        if hasattr(capsule, "type") and hasattr(policy, "allowed_capsule_types"):
            if capsule.type not in policy.allowed_capsule_types:
                policy_valid = False
                policy_errors.append(
                    f"Capsule type {capsule.type} not allowed by policy"
                )

        # Check if the capsule author is authorized
        if hasattr(capsule, "author") and hasattr(policy, "authorized_authors"):
            if capsule.author not in policy.authorized_authors:
                policy_valid = False
                policy_errors.append(
                    f"Author {capsule.author} not authorized by policy"
                )

        # Check content for policy violations (placeholder)
        if hasattr(capsule, "content") and capsule.content:
            # In a real implementation, this would check content against policy rules
            # For example, scanning for prohibited content or ensuring required metadata
            pass

        # Record policy validation results
        result.provider_results["governance_policy"] = {
            "valid": policy_valid,
            "errors": policy_errors,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Determine overall outcome
        if policy_valid:
            # If base validation was questionable, keep it that way
            if base_validation.outcome == ValidationOutcome.QUESTIONABLE:
                result.outcome = ValidationOutcome.QUESTIONABLE
            else:
                result.outcome = ValidationOutcome.VALID
        else:
            result.outcome = ValidationOutcome.INVALID
            result.validation_errors.extend(policy_errors)

        # Store validation result in history
        self.validation_history[validation_id] = result

        return result


async def demo_cross_provider_validation():
    """Demonstrate cross-provider validation."""
    from src.integrations.multimodal_adapters import MockMultiModalAdapter

    # Create validator
    validator = CrossProviderValidator()

    # Register mock adapters for different providers
    mock_openai = MockMultiModalAdapter()
    mock_openai.provider_id = "openai"

    mock_mistral = MockMultiModalAdapter()
    mock_mistral.provider_id = "mistral"

    mock_cohere = MockMultiModalAdapter()
    mock_cohere.provider_id = "cohere"

    # Register adapters
    await validator.register_adapter("openai", mock_openai)
    await validator.register_adapter("mistral", mock_mistral)
    await validator.register_adapter("cohere", mock_cohere)

    # Create mock reasoning steps for validation
    steps = [
        MultiModalReasoningStep(
            step_id=1,
            operation="analyze_query",
            reasoning="Analyzed user query about climate change",
            confidence=0.95,
        ),
        MultiModalReasoningStep(
            step_id=2,
            operation="retrieve_data",
            reasoning="Retrieved relevant climate data from 2000-2020",
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

    # Original output to validate
    original_output = """
    Based on climate data from 2000-2020, global temperatures have risen by approximately 0.18°C per decade.
    This trend is consistent with the broader warming pattern observed since the industrial revolution.
    The data shows accelerating ice melt in polar regions and increasing frequency of extreme weather events.
    """

    # Validate reasoning trace
    print("Validating reasoning trace...")
    options = ValidationOptions(min_providers=2, consensus_threshold=0.5)
    validation_result = await validator.validate_reasoning_trace(
        reasoning_steps=steps,
        original_provider="openai",  # Pretend this came from OpenAI
        original_output=original_output,
        options=options,
    )

    # Display results
    print(f"Validation outcome: {validation_result.outcome.name}")
    print(f"Consensus score: {validation_result.consensus_score:.2f}")
    print("Provider results:")
    for provider, result in validation_result.provider_results.items():
        print(f"  - {provider}: {'' if result.get('valid', False) else ''}")
        if "error" in result:
            print(f"    Error: {result['error']}")


if __name__ == "__main__":
    import asyncio

    # Run the demo
    asyncio.run(demo_cross_provider_validation())
