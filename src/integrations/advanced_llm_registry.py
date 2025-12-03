#!/usr/bin/env python3
"""
UATP Capsule Engine - Advanced LLM Registry
Supports multiple LLM providers with standardized reasoning trace capture
and UATP capsule integration.

Enhanced Features:
- Provider adapter pattern for extensibility
- Structured reasoning trace capture
- Trace chaining for multi-turn conversations
- Integration with UATP capsule signing workflow
"""

import abc
import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

import cohere
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey

# UATP Imports
from ..capsule_schema import (
    BaseCapsule,
    Capsule,
    CapsuleStatus,
    CapsuleType,
    ReasoningTracePayload,
)
from ..capsule_schema import ReasoningStep as UATPReasoningStep
from ..crypto_utils import hash_for_signature, sign_capsule

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelCapability(Enum):
    """Capabilities that models can have."""

    CHAT = auto()
    CODE = auto()
    VISION = auto()
    EMBEDDING = auto()
    FUNCTION_CALLING = auto()
    REASONING_TRACE = auto()
    MULTI_MODAL = auto()
    FINE_TUNING = auto()
    STREAMING = auto()


class ProviderTier(Enum):
    """Provider service tiers for different use cases."""

    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class ModelStatus(Enum):
    """Status of model availability."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    BETA = "beta"
    MAINTENANCE = "maintenance"


@dataclass
class ReasoningStep:
    """A single step in the reasoning process of an LLM."""

    type: str
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMOutput:
    """Standard output format from any LLM provider with reasoning trace."""

    content: str
    model_name: str
    provider_name: str
    tokens_used: int
    cost_usd: float
    reasoning_trace: List[ReasoningStep]
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_trace_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Backward-compatibility aliases (read-only properties)
    # ------------------------------------------------------------------
    @property
    def model(self) -> str:
        """Alias for ``model_name`` to maintain backward compatibility with tests expecting ``model``."""
        return self.model_name

    @property
    def provider(self) -> str:
        """Alias for ``provider_name`` (tests use ``provider``)."""
        return self.provider_name

    @property
    def total_tokens(self) -> int:
        """Alias for ``tokens_used`` (tests use ``total_tokens``)."""
        return self.tokens_used

    @property
    def cost(self) -> float:
        """Alias for ``cost_usd`` (tests use ``cost``)."""
        return self.cost_usd

    @property
    def reasoning_steps(self) -> List["ReasoningStep"]:
        """Alias for ``reasoning_trace`` (tests use ``reasoning_steps`` on ``MultiModalOutput`` as well)."""
        return self.reasoning_trace

    def _convert_to_uatp_reasoning_step(
        self, step: ReasoningStep, step_id: int
    ) -> UATPReasoningStep:
        """Converts our internal ReasoningStep to a UATP schema ReasoningStep."""
        # Ensure all required fields are present and properly mapped
        return UATPReasoningStep(
            step_id=step_id,
            operation=step.type,
            reasoning=step.content,
            confidence=step.details.get("confidence", 1.0),
            attribution_sources=None,
        )

    def to_uatp_reasoning_trace(self) -> ReasoningTracePayload:
        """Convert the reasoning trace to UATP format."""
        uatp_steps = []
        total_confidence = 1.0

        for i, step in enumerate(self.reasoning_trace):
            confidence = step.details.get("confidence", 0.95)
            total_confidence *= confidence

            # Create a properly formatted UATP ReasoningStep
            uatp_step = UATPReasoningStep(
                step_id=i + 1,  # 1-based indexing
                operation=step.type,  # map type to operation
                reasoning=step.content,  # map content to reasoning
                confidence=confidence,
                attribution_sources=step.details.get("sources", None),
            )
            uatp_steps.append(uatp_step)

        return ReasoningTracePayload(
            reasoning_steps=uatp_steps, total_confidence=total_confidence
        )


class LLMProviderAdapter(abc.ABC):
    """Abstract base class for LLM provider adapters."""

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Get the name of this provider."""
        pass

    @abc.abstractmethod
    async def list_models(self) -> List[Tuple[str, List[ModelCapability]]]:
        """List available models and their capabilities from this provider."""
        pass

    @abc.abstractmethod
    async def generate(self, model_name: str, prompt: str, **kwargs) -> LLMOutput:
        """Generate a response from the given model."""
        pass


class AdvancedLLMRegistry:
    """Registry for multiple LLM providers with standardized interfaces."""

    def __init__(self):
        self._providers: Dict[str, LLMProviderAdapter] = {}
        self._models: Dict[str, Dict[str, Any]] = {}

    def register_provider(self, provider_class: type, **kwargs) -> None:
        """Register a provider with the registry."""
        provider = provider_class(**kwargs)
        self._providers[provider.provider_name] = provider
        logger.info(f"Registered provider: {provider.provider_name}")

    async def discover_models(self, provider_name: str) -> List[str]:
        """Discover models from a specific provider."""
        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' not registered.")

        provider = self._providers[provider_name]
        model_info = await provider.list_models()

        model_aliases = []
        for model_name, capabilities in model_info:
            alias = f"{provider_name}:{model_name}"
            self._models[alias] = {
                "provider_name": provider_name,
                "model_name": model_name,
                "capabilities": capabilities,
                "status": ModelStatus.ACTIVE,
                "tier": ProviderTier.BASIC,
                "max_tokens": 4096,
                "cost_per_1k_tokens": 0.002,
                "supported_formats": ["text"],
                "rate_limits": {"requests_per_minute": 60, "tokens_per_minute": 150000},
            }
            model_aliases.append(alias)

        logger.info(
            f"Discovered {len(model_aliases)} models from provider '{provider_name}'"
        )
        return model_aliases

    def get_model_info(self, model_alias: str) -> Dict[str, Any]:
        """Get comprehensive information about a model."""
        if model_alias not in self._models:
            raise ValueError(f"Model alias '{model_alias}' not found.")
        return self._models[model_alias].copy()

    def get_provider_health(self, provider_name: str) -> Dict[str, Any]:
        """Get health status of a provider."""
        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' not registered.")

        provider = self._providers[provider_name]
        provider_models = [
            alias
            for alias in self._models.keys()
            if alias.startswith(f"{provider_name}:")
        ]

        return {
            "provider_name": provider_name,
            "status": "healthy",  # Could be enhanced with actual health checks
            "models_count": len(provider_models),
            "capabilities": list(
                set().union(
                    *[
                        model["capabilities"]
                        for model in self._models.values()
                        if model["provider_name"] == provider_name
                    ]
                )
            ),
            "last_checked": datetime.now(timezone.utc).isoformat(),
        }

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics."""
        provider_stats = {}
        for provider_name in self._providers.keys():
            provider_models = [
                alias
                for alias in self._models.keys()
                if alias.startswith(f"{provider_name}:")
            ]
            provider_stats[provider_name] = {
                "model_count": len(provider_models),
                "capabilities": list(
                    set().union(
                        *[
                            model["capabilities"]
                            for model in self._models.values()
                            if model["provider_name"] == provider_name
                        ]
                    )
                ),
            }

        return {
            "total_providers": len(self._providers),
            "total_models": len(self._models),
            "provider_breakdown": provider_stats,
            "capability_distribution": {
                cap.name: len(self.find_models_by_capability(cap))
                for cap in ModelCapability
            },
            "registry_uptime": datetime.now(timezone.utc).isoformat(),
        }

    async def generate(self, model_alias: str, prompt: str, **kwargs) -> LLMOutput:
        """Generates a response from the specified model."""
        if model_alias not in self._models:
            raise ValueError(f"Model alias '{model_alias}' not found.")

        model_info = self._models[model_alias]
        provider_name = model_info["provider_name"]
        model_name = model_info["model_name"]

        provider = self._providers[provider_name]
        output = await provider.generate(model_name, prompt, **kwargs)

        if "parent_trace_id" in kwargs:
            output.parent_trace_id = kwargs["parent_trace_id"]

        return output

    def find_models_by_capability(self, capability: ModelCapability) -> List[str]:
        """Finds all registered model aliases that have a given capability."""
        return [
            alias
            for alias, config in self._models.items()
            if capability in config["capabilities"]
        ]


class MockOpenAIAdapter(LLMProviderAdapter):
    """Mock adapter for OpenAI, used for testing and examples."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @property
    def provider_name(self) -> str:
        return "mock_openai"

    async def list_models(self) -> List[Tuple[str, List[ModelCapability]]]:
        """List available mock models."""
        return [
            ("gpt-4-mock", [ModelCapability.CHAT, ModelCapability.CODE]),
            ("gpt-3.5-turbo-mock", [ModelCapability.CHAT]),
        ]

    async def generate(self, model_name: str, prompt: str, **kwargs) -> LLMOutput:
        """Generate a mock response."""
        # Simulate processing time
        await asyncio.sleep(0.5)

        # Create a reasoning trace
        reasoning_trace = [
            ReasoningStep(type="input", content=f"Received prompt: {prompt}"),
            ReasoningStep(
                type="reasoning",
                content="Processing with mock joke generator",
                details={"tool_name": "mock_joke_generator"},
            ),
        ]

        # Create mock output
        return LLMOutput(
            content="This is a mock response from OpenAI.",
            model_name=model_name,
            provider_name=self.provider_name,
            tokens_used=50,
            cost_usd=0.001 * 50,  # $0.001 per token
            reasoning_trace=reasoning_trace,
        )


class MistralAIAdapter(LLMProviderAdapter):
    """Adapter for Mistral AI API."""

    def __init__(self, api_key: Optional[str] = None):
        import httpx

        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("Mistral API key not provided")
        self.client = httpx.AsyncClient(
            base_url="https://api.mistral.ai/v1",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )

        # Known models and their capabilities
        self._models = {
            "mistral-tiny": [ModelCapability.CHAT],
            "mistral-small": [ModelCapability.CHAT],
            "mistral-medium": [ModelCapability.CHAT, ModelCapability.CODE],
            "mistral-large": [
                ModelCapability.CHAT,
                ModelCapability.CODE,
                ModelCapability.FUNCTION_CALLING,
            ],
        }

    @property
    def provider_name(self) -> str:
        return "mistral"

    async def list_models(self) -> List[Tuple[str, List[ModelCapability]]]:
        """List available Mistral models."""
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            data = response.json()

            result = []
            for model in data.get("data", []):
                model_id = model.get("id")
                if model_id in self._models:
                    result.append((model_id, self._models[model_id]))

            return result
        except Exception as e:
            logger.error(f"Failed to list Mistral models: {e}")
            # Return known models as fallback
            return list(self._models.items())

    async def generate(self, model_name: str, prompt: str, **kwargs) -> LLMOutput:
        """Generate a response from Mistral AI."""
        messages = [{"role": "user", "content": prompt}]

        try:
            start_time = datetime.now()
            response = await self.client.post(
                "/chat/completions", json={"model": model_name, "messages": messages}
            )
            response.raise_for_status()
            data = response.json()
            end_time = datetime.now()

            # Extract response content
            content = data["choices"][0]["message"]["content"]

            # Extract token usage
            token_usage = data.get("usage", {})
            prompt_tokens = token_usage.get("prompt_tokens", 0)
            completion_tokens = token_usage.get("completion_tokens", 0)
            total_tokens = token_usage.get(
                "total_tokens", prompt_tokens + completion_tokens
            )

            # Calculate cost (approximation)
            # Prices as of July 2023
            if "large" in model_name:
                cost_per_token = 0.00008
            elif "medium" in model_name:
                cost_per_token = 0.00003
            else:  # small or tiny
                cost_per_token = 0.00002
            cost_usd = cost_per_token * total_tokens

            # Create reasoning trace
            reasoning_trace = [
                ReasoningStep(type="input", content=f"Received prompt: {prompt}"),
                ReasoningStep(
                    type="reasoning",
                    content=f"Processing with Mistral AI model: {model_name}",
                ),
            ]

            return LLMOutput(
                content=content,
                model_name=model_name,
                provider_name=self.provider_name,
                tokens_used=total_tokens,
                cost_usd=cost_usd,
                reasoning_trace=reasoning_trace,
            )

        except Exception as e:
            logger.error(f"Mistral AI generation failed: {e}")
            raise


class CohereAdapter(LLMProviderAdapter):
    """Adapter for Cohere API using their Python SDK."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError("Cohere API key not provided")
        self.client = cohere.Client(self.api_key)

        # Known models and their capabilities
        self._models = {
            "command": [ModelCapability.CHAT],
            "command-r": [ModelCapability.CHAT, ModelCapability.CODE],
            "command-r-plus": [
                ModelCapability.CHAT,
                ModelCapability.CODE,
                ModelCapability.FUNCTION_CALLING,
            ],
        }

    @property
    def provider_name(self) -> str:
        return "cohere"

    async def list_models(self) -> List[Tuple[str, List[ModelCapability]]]:
        """List available Cohere models."""
        # Cohere's SDK doesn't have a simple model listing endpoint
        # Return hardcoded known models
        return list(self._models.items())

    async def generate(self, model_name: str, prompt: str, **kwargs) -> LLMOutput:
        """Generate a response from Cohere."""
        try:
            # Run synchronous Cohere API call in a thread pool
            loop = asyncio.get_event_loop()
            start_time = datetime.now()

            # Use Cohere's chat API
            response = await loop.run_in_executor(
                None, lambda: self.client.chat(message=prompt, model=model_name)
            )

            end_time = datetime.now()

            # Extract response content
            content = response.text

            # Extract token usage
            token_usage = response.meta.get("tokenizer", {})
            total_tokens = token_usage.get("tokens", 30)  # Default to 30 if missing

            # Calculate cost (approximation)
            # Prices as of July 2023
            if "plus" in model_name:
                cost_per_token = 0.00015
            else:
                cost_per_token = 0.00005
            cost_usd = cost_per_token * total_tokens

            # Create reasoning trace
            reasoning_trace = [
                ReasoningStep(type="input", content=f"Received prompt: {prompt}"),
                ReasoningStep(
                    type="reasoning",
                    content=f"Processing with Cohere model: {model_name}",
                ),
            ]

            return LLMOutput(
                content=content,
                model_name=model_name,
                provider_name=self.provider_name,
                tokens_used=total_tokens,
                cost_usd=cost_usd,
                reasoning_trace=reasoning_trace,
            )

        except Exception as e:
            logger.error(f"Cohere generation failed: {e}")
            raise


def create_and_sign_reasoning_capsule(
    trace_chain: List[LLMOutput], signer_name: str, signing_key_hex: str
) -> BaseCapsule:
    """Combines a chain of reasoning traces and signs them into a UATP capsule."""
    logging.info("Creating and signing a new reasoning trace capsule...")

    # Combine all reasoning steps from the chain
    all_uatp_steps = []
    total_confidence = 1.0
    for output in trace_chain:
        uatp_trace = output.to_uatp_reasoning_trace()
        all_uatp_steps.extend(uatp_trace.reasoning_steps)
        total_confidence *= uatp_trace.total_confidence  # Combine confidences

    # Create the final payload
    payload = ReasoningTracePayload(
        reasoning_steps=all_uatp_steps, total_confidence=total_confidence
    )

    # Generate a capsule ID using timestamp and random ID
    import secrets

    timestamp = datetime.now(timezone.utc)
    random_id = secrets.token_hex(8)
    capsule_id = f"caps_{timestamp.year:04d}_{timestamp.month:02d}_{timestamp.day:02d}_{random_id}"

    # Create the verification object with proper format
    verification = {
        "signer": signer_name,
        "verify_key": None,  # Optional
        "hash": None,  # Will be filled by hash_for_signature
        "signature": f"ed25519:{secrets.token_hex(64)}",  # Placeholder that matches pattern
        "merkle_root": f"sha256:{secrets.token_hex(32)}",
    }

    # Create the capsule
    capsule = Capsule(
        capsule_id=capsule_id,
        timestamp=timestamp,
        capsule_type=CapsuleType.REASONING_TRACE,
        reasoning_trace=payload,
        status=CapsuleStatus.SEALED,  # Use a valid status: DRAFT, SEALED, VERIFIED, ARCHIVED
        verification=verification,
        version="7.0",
    )

    # Hash and sign the capsule
    capsule_dict = capsule.model_dump()
    hash_str = hash_for_signature(capsule_dict)

    # Update the hash and signature in the verification object
    capsule.verification.hash = hash_str
    capsule.verification.signature = sign_capsule(hash_str, signing_key_hex)

    logging.info(f"Capsule created and signed successfully. Hash: {hash_str}")

    # Log success
    return capsule


async def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Create the registry
    registry = AdvancedLLMRegistry()

    # Register mock adapter for testing
    registry.register_provider(MockOpenAIAdapter, api_key="test_key")

    # Discover models
    print("Discovering models from mock provider...")
    models = await registry.discover_models("mock_openai")
    print(f"Found models: {models}")

    # Generate a response
    model_alias = models[0]  # Use first model
    print(f"Generating response from {model_alias}...")
    try:
        output = await registry.generate(model_alias, "Tell me a joke about AI")
        print(f"Content: {output.content}")
        print(f"Model: {output.model_name}")
        print(f"Provider: {output.provider_name}")
        print(f"Tokens used: {output.tokens_used}")
        print(f"Cost: ${output.cost_usd:.6f}")
        print(f"Trace ID: {output.trace_id}")
    except Exception as e:
        logging.error(f"Failed to generate response from {model_alias}: {e}")
        return  # Exit if first generation fails

    # --- Chained Generation and Capsule Signing Example ---
    print("\n--- Simulating a chained conversation and signing the trace ---")
    try:
        # Second call, chained to the first
        output2 = await registry.generate(
            model_alias,
            "What are two good names for it?",
            parent_trace_id=output.trace_id,
        )
        print(f"Chained Content: {output2.content}")

        # Create a signing key for the capsule
        signing_key = SigningKey.generate()
        signer_name = "UATP-System"

        # Create and sign the capsule from the trace chain
        trace_chain = [output, output2]
        signed_capsule = create_and_sign_reasoning_capsule(
            trace_chain,
            signer_name,
            signing_key.encode(encoder=HexEncoder).decode("utf-8"),
        )

        print("\n--- Signed UATP Reasoning Capsule ---")
        print(signed_capsule.model_dump_json(indent=2))

    except Exception as e:
        logging.error(f"Failed during chained generation or capsule signing: {e}")


if __name__ == "__main__":
    asyncio.run(main())
