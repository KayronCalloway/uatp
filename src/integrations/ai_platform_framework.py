"""
Generic AI Platform Integration Framework
Unified attribution tracking across multiple AI platforms
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from ..engine.economic_engine import UatpEconomicEngine as EconomicEngine
from .anthropic_client import AnthropicAttributionClient
from .openai_attribution import (
    AttributionContext,
    AttributionResult,
    OpenAIAttributionClient,
)

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Supported AI providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    GOOGLE = "google"
    COHERE = "cohere"
    GENERIC = "generic"


@dataclass
class PlatformConfig:
    """Configuration for AI platform integration"""

    provider: AIProvider
    api_key: str
    model_name: str
    max_tokens: int = 1024
    temperature: float = 0.7
    additional_params: Dict[str, Any] = field(default_factory=dict)


class AIClientProtocol(Protocol):
    """Protocol for AI client implementations"""

    async def get_completion_with_attribution(
        self,
        prompt: str,
        attribution_context: AttributionContext,
        model: str = None,
        max_tokens: int = None,
        **kwargs,
    ) -> tuple[str, AttributionResult]:
        """Get completion with attribution tracking"""
        ...

    async def get_user_attribution_summary(
        self, user_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get attribution summary for a user"""
        ...

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage metrics summary"""
        ...


class BaseAIClient(ABC):
    """Base class for AI platform clients"""

    def __init__(
        self,
        config: PlatformConfig,
        attribution_engine: Optional[EconomicEngine] = None,
    ):
        self.config = config
        self.attribution_engine = attribution_engine or EconomicEngine()
        self.attribution_sessions = {}

    @abstractmethod
    async def get_completion_with_attribution(
        self,
        prompt: str,
        attribution_context: AttributionContext,
        model: str = None,
        max_tokens: int = None,
        **kwargs,
    ) -> tuple[str, AttributionResult]:
        """Get completion with attribution tracking"""
        pass

    @abstractmethod
    async def get_user_attribution_summary(
        self, user_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get attribution summary for a user"""
        pass

    @abstractmethod
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage metrics summary"""
        pass


class HuggingFaceClient(BaseAIClient):
    """HuggingFace client with attribution tracking"""

    def __init__(
        self,
        config: PlatformConfig,
        attribution_engine: Optional[EconomicEngine] = None,
    ):
        super().__init__(config, attribution_engine)

        # Initialize HuggingFace client
        try:
            from huggingface_hub import InferenceClient

            self.client = InferenceClient(token=config.api_key)
            self.usage_metrics = {"requests": 0, "errors": 0, "total_cost": 0.0}
            logger.info("HuggingFace client initialized")
        except ImportError:
            raise ImportError(
                "huggingface_hub not installed. Install with: pip install huggingface_hub"
            )

    async def get_completion_with_attribution(
        self,
        prompt: str,
        attribution_context: AttributionContext,
        model: str = None,
        max_tokens: int = None,
        **kwargs,
    ) -> tuple[str, AttributionResult]:
        """Get completion with attribution tracking"""

        model = model or self.config.model_name
        max_tokens = max_tokens or self.config.max_tokens

        session_id = (
            f"{attribution_context.conversation_id}_{datetime.now().timestamp()}"
        )

        try:
            # Get completion from HuggingFace
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.text_generation(
                    prompt=prompt,
                    model=model,
                    max_new_tokens=max_tokens,
                    temperature=self.config.temperature,
                    **kwargs,
                ),
            )

            completion = (
                response.generated_text
                if hasattr(response, "generated_text")
                else str(response)
            )

            # Calculate attribution (simplified for HuggingFace)
            attribution_result = await self._calculate_attribution(
                prompt=prompt,
                completion=completion,
                context=attribution_context,
                model=model,
                session_id=session_id,
            )

            self.usage_metrics["requests"] += 1
            return completion, attribution_result

        except Exception as e:
            logger.error(f"HuggingFace completion failed: {e}")
            self.usage_metrics["errors"] += 1
            raise

    async def _calculate_attribution(
        self,
        prompt: str,
        completion: str,
        context: AttributionContext,
        model: str,
        session_id: str,
    ) -> AttributionResult:
        """Calculate attribution for HuggingFace interaction"""

        # Simplified cost calculation (HuggingFace pricing varies)
        estimated_cost = 0.001  # Placeholder

        # Calculate attribution scores
        attribution_scores = await self.attribution_engine.calculate_attribution(
            content=completion,
            sources=context.prompt_sources + context.training_data_sources,
            metadata={"platform": "huggingface", "model": model},
        )

        # Simple distribution
        total_value = Decimal(str(estimated_cost))
        uba_allocation = total_value * Decimal("0.15")
        commons_allocation = total_value * Decimal("0.5")
        direct_attributions = {
            source: total_value * Decimal("0.35") / len(attribution_scores)
            for source in attribution_scores
        }

        return AttributionResult(
            total_value=total_value,
            direct_attributions=direct_attributions,
            commons_allocation=commons_allocation,
            uba_allocation=uba_allocation,
            confidence_scores=attribution_scores,
            attribution_breakdown={
                "session_id": session_id,
                "model": model,
                "platform": "huggingface",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def get_user_attribution_summary(
        self, user_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get attribution summary for a user"""
        return {
            "user_id": user_id,
            "platform": "huggingface",
            "period_days": days,
            "total_attributed_value": 0.0,
            "attribution_count": 0,
        }

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage metrics summary"""
        return {
            "platform": "huggingface",
            "total_requests": self.usage_metrics["requests"],
            "total_errors": self.usage_metrics["errors"],
            "success_rate": (
                (self.usage_metrics["requests"] - self.usage_metrics["errors"])
                / max(1, self.usage_metrics["requests"])
            )
            * 100,
        }


class AIAttributionOrchestrator:
    """Orchestrates attribution tracking across multiple AI platforms"""

    def __init__(self, attribution_engine: Optional[EconomicEngine] = None):
        self.attribution_engine = attribution_engine or EconomicEngine()
        self.clients: Dict[AIProvider, AIClientProtocol] = {}
        self.default_provider = AIProvider.OPENAI

    def register_client(self, provider: AIProvider, client: AIClientProtocol):
        """Register an AI client for a specific provider"""
        self.clients[provider] = client
        logger.info(f"Registered client for {provider.value}")

    def set_default_provider(self, provider: AIProvider):
        """Set the default AI provider"""
        if provider not in self.clients:
            raise ValueError(f"Provider {provider.value} not registered")
        self.default_provider = provider
        logger.info(f"Set default provider to {provider.value}")

    async def get_completion_with_attribution(
        self,
        prompt: str,
        attribution_context: AttributionContext,
        provider: Optional[AIProvider] = None,
        model: str = None,
        max_tokens: int = None,
        **kwargs,
    ) -> tuple[str, AttributionResult]:
        """Get completion with attribution from specified or default provider"""

        provider = provider or self.default_provider

        if provider not in self.clients:
            raise ValueError(f"Provider {provider.value} not registered")

        client = self.clients[provider]

        # Add provider info to attribution context
        enhanced_context = AttributionContext(
            user_id=attribution_context.user_id,
            conversation_id=attribution_context.conversation_id,
            prompt_sources=attribution_context.prompt_sources,
            training_data_sources=attribution_context.training_data_sources,
            attribution_metadata={
                **attribution_context.attribution_metadata,
                "provider": provider.value,
            },
        )

        return await client.get_completion_with_attribution(
            prompt=prompt,
            attribution_context=enhanced_context,
            model=model,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def get_multi_platform_completion(
        self,
        prompt: str,
        attribution_context: AttributionContext,
        providers: List[AIProvider],
        model: str = None,
        max_tokens: int = None,
        **kwargs,
    ) -> Dict[AIProvider, tuple[str, AttributionResult]]:
        """Get completions from multiple providers for comparison"""

        tasks = []
        for provider in providers:
            if provider in self.clients:
                task = self.get_completion_with_attribution(
                    prompt=prompt,
                    attribution_context=attribution_context,
                    provider=provider,
                    model=model,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                tasks.append((provider, task))

        results = {}
        for provider, task in tasks:
            try:
                result = await task
                results[provider] = result
            except Exception as e:
                logger.error(
                    f"Multi-platform completion failed for {provider.value}: {e}"
                )
                results[provider] = (f"Error: {str(e)}", None)

        return results

    async def get_user_attribution_summary(
        self, user_id: str, days: int = 30, providers: Optional[List[AIProvider]] = None
    ) -> Dict[AIProvider, Dict[str, Any]]:
        """Get attribution summary across platforms"""

        providers = providers or list(self.clients.keys())
        summaries = {}

        for provider in providers:
            if provider in self.clients:
                try:
                    summary = await self.clients[provider].get_user_attribution_summary(
                        user_id, days
                    )
                    summaries[provider] = summary
                except Exception as e:
                    logger.error(f"Failed to get summary for {provider.value}: {e}")
                    summaries[provider] = {"error": str(e)}

        return summaries

    def get_platform_usage_summary(self) -> Dict[AIProvider, Dict[str, Any]]:
        """Get usage summary for all registered platforms"""

        summaries = {}
        for provider, client in self.clients.items():
            try:
                summaries[provider] = client.get_usage_summary()
            except Exception as e:
                logger.error(f"Failed to get usage summary for {provider.value}: {e}")
                summaries[provider] = {"error": str(e)}

        return summaries

    async def track_cross_platform_conversation(
        self,
        conversation_id: str,
        messages: List[Dict[str, str]],
        attribution_context: AttributionContext,
        provider_rotation: Optional[List[AIProvider]] = None,
    ) -> Dict[str, Any]:
        """Track attribution across multiple platforms in a single conversation"""

        provider_rotation = provider_rotation or [self.default_provider]
        results = {
            "conversation_id": conversation_id,
            "messages": [],
            "total_attribution": {},
            "platform_breakdown": {},
        }

        provider_index = 0
        for i, message in enumerate(messages):
            if message["role"] == "user":
                # Select provider for this interaction
                provider = provider_rotation[provider_index % len(provider_rotation)]
                provider_index += 1

                # Create context for this message
                msg_context = AttributionContext(
                    user_id=attribution_context.user_id,
                    conversation_id=f"{conversation_id}_msg_{i}",
                    prompt_sources=attribution_context.prompt_sources,
                    training_data_sources=attribution_context.training_data_sources,
                    attribution_metadata={
                        **attribution_context.attribution_metadata,
                        "message_index": i,
                        "provider": provider.value,
                    },
                )

                try:
                    # Get completion and attribution
                    (
                        completion,
                        attribution_result,
                    ) = await self.get_completion_with_attribution(
                        prompt=message["content"],
                        attribution_context=msg_context,
                        provider=provider,
                    )

                    # Record results
                    results["messages"].append(
                        {
                            "index": i,
                            "provider": provider.value,
                            "prompt": message["content"],
                            "completion": completion,
                            "attribution": attribution_result,
                        }
                    )

                    # Update totals
                    if provider not in results["platform_breakdown"]:
                        results["platform_breakdown"][provider] = {
                            "total_value": 0.0,
                            "request_count": 0,
                            "attribution_count": 0,
                        }

                    results["platform_breakdown"][provider]["total_value"] += float(
                        attribution_result.total_value
                    )
                    results["platform_breakdown"][provider]["request_count"] += 1
                    results["platform_breakdown"][provider]["attribution_count"] += len(
                        attribution_result.direct_attributions
                    )

                except Exception as e:
                    logger.error(f"Cross-platform tracking failed for message {i}: {e}")
                    results["messages"].append(
                        {"index": i, "provider": provider.value, "error": str(e)}
                    )

        return results


# Factory functions for easy setup
def create_ai_orchestrator() -> AIAttributionOrchestrator:
    """Create an AI attribution orchestrator with default configuration"""
    return AIAttributionOrchestrator()


def setup_multi_platform_attribution(
    openai_key: Optional[str] = None,
    anthropic_key: Optional[str] = None,
    huggingface_key: Optional[str] = None,
) -> AIAttributionOrchestrator:
    """Set up multi-platform attribution with available keys"""

    orchestrator = create_ai_orchestrator()

    # Register OpenAI client
    if openai_key:
        openai_client = OpenAIAttributionClient()
        orchestrator.register_client(AIProvider.OPENAI, openai_client)

    # Register Anthropic client
    if anthropic_key:
        anthropic_client = AnthropicAttributionClient()
        orchestrator.register_client(AIProvider.ANTHROPIC, anthropic_client)

    # Register HuggingFace client
    if huggingface_key:
        hf_config = PlatformConfig(
            provider=AIProvider.HUGGINGFACE, api_key=huggingface_key, model_name="gpt2"
        )
        hf_client = HuggingFaceClient(hf_config)
        orchestrator.register_client(AIProvider.HUGGINGFACE, hf_client)

    return orchestrator


# Example usage
if __name__ == "__main__":

    async def demo_multi_platform():
        """Demonstrate multi-platform attribution"""

        # Set up orchestrator
        orchestrator = setup_multi_platform_attribution(
            openai_key=os.getenv("OPENAI_API_KEY"),
            anthropic_key=os.getenv("ANTHROPIC_API_KEY"),
        )

        # Create attribution context
        context = AttributionContext(
            user_id="user123",
            conversation_id="multi_platform_conv",
            prompt_sources=["user_knowledge"],
            training_data_sources=["web_data"],
            attribution_metadata={"session_type": "multi_platform"},
        )

        # Get completion from default provider
        completion, attribution = await orchestrator.get_completion_with_attribution(
            prompt="What is the future of AI?", attribution_context=context
        )

        print(f"Completion: {completion}")
        print(f"Attribution: {attribution}")

        # Get usage summary
        usage_summary = orchestrator.get_platform_usage_summary()
        print(f"Usage Summary: {usage_summary}")

    import os

    asyncio.run(demo_multi_platform())
