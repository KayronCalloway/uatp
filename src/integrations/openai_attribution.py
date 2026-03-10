"""
OpenAI Attribution Integration
Real-time attribution tracking for OpenAI API interactions
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..capsule_schema import CapsuleStatus, CapsuleType
from ..capsules.specialized_capsules import AttributionCapsule, EconomicCapsule
from ..engine.economic_engine import UatpEconomicEngine as EconomicEngine
from .openai_client import OpenAIClient

logger = logging.getLogger(__name__)


@dataclass
class AttributionContext:
    """Context for attribution tracking"""

    user_id: str
    conversation_id: str
    prompt_sources: List[str] = field(default_factory=list)
    training_data_sources: List[str] = field(default_factory=list)
    attribution_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttributionResult:
    """Result of attribution calculation"""

    total_value: Decimal
    direct_attributions: Dict[str, Decimal]
    commons_allocation: Decimal
    uba_allocation: Decimal
    confidence_scores: Dict[str, float]
    attribution_breakdown: Dict[str, Any]


class OpenAIAttributionClient(OpenAIClient):
    """Enhanced OpenAI client with real-time attribution tracking"""

    def __init__(self, attribution_engine: Optional[EconomicEngine] = None, **kwargs):
        super().__init__(**kwargs)
        self.attribution_engine = attribution_engine or EconomicEngine()
        self.attribution_sessions = {}

    async def get_completion_with_attribution(
        self,
        prompt: str,
        attribution_context: AttributionContext,
        model: str = "gpt-4",
        max_tokens: int = 150,
        **kwargs,
    ) -> tuple[str, AttributionResult]:
        """
        Get completion with real-time attribution tracking

        Args:
            prompt: The input prompt
            attribution_context: Context for attribution calculation
            model: OpenAI model to use
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI parameters

        Returns:
            Tuple of (completion_text, attribution_result)
        """
        # Ensure API key is loaded
        await self._ensure_api_key_loaded()

        # Track session start
        session_id = (
            f"{attribution_context.conversation_id}_{datetime.now().timestamp()}"
        )
        self.attribution_sessions[session_id] = {
            "start_time": datetime.now(timezone.utc),
            "context": attribution_context,
        }

        try:
            # Get completion from OpenAI
            completion = await self.get_completion_async(
                prompt=prompt, model=model, max_tokens=max_tokens, **kwargs
            )

            # Calculate attribution
            attribution_result = await self._calculate_attribution(
                prompt=prompt,
                completion=completion,
                context=attribution_context,
                model=model,
                session_id=session_id,
            )

            # Create attribution capsule
            await self._create_attribution_capsule(
                session_id=session_id,
                attribution_result=attribution_result,
                context=attribution_context,
            )

            return completion, attribution_result

        except Exception as e:
            logger.error(f"Attribution completion failed: {e}")
            raise
        finally:
            # Clean up session
            if session_id in self.attribution_sessions:
                del self.attribution_sessions[session_id]

    async def _calculate_attribution(
        self,
        prompt: str,
        completion: str,
        context: AttributionContext,
        model: str,
        session_id: str,
    ) -> AttributionResult:
        """Calculate attribution for the interaction"""

        # Get usage metrics for this session
        usage_cost = self._estimate_interaction_cost(prompt, completion, model)

        # Prepare attribution data
        attribution_data = {
            "prompt": prompt,
            "completion": completion,
            "prompt_sources": context.prompt_sources,
            "training_data_sources": context.training_data_sources,
            "metadata": context.attribution_metadata,
        }

        # Calculate attribution using economic engine
        attribution_scores = await self.attribution_engine.calculate_attribution(
            content=completion,
            sources=context.prompt_sources + context.training_data_sources,
            metadata=attribution_data,
        )

        # Calculate value distribution
        total_value = Decimal(str(usage_cost))
        uba_allocation = total_value * Decimal("0.15")  # 15% for UBA
        remaining_value = total_value - uba_allocation

        # Distribute remaining value based on attribution scores
        direct_attributions = {}
        commons_allocation = Decimal("0")

        for source, score in attribution_scores.items():
            if score > 0.8:  # High confidence
                attribution_amount = remaining_value * Decimal(str(score * 0.8))
                direct_attributions[source] = attribution_amount
                remaining_value -= attribution_amount
            elif score > 0.5:  # Medium confidence
                attribution_amount = remaining_value * Decimal(str(score * 0.5))
                direct_attributions[source] = attribution_amount
                remaining_value -= attribution_amount
            # Low confidence goes to commons

        commons_allocation = remaining_value

        return AttributionResult(
            total_value=total_value,
            direct_attributions=direct_attributions,
            commons_allocation=commons_allocation,
            uba_allocation=uba_allocation,
            confidence_scores=attribution_scores,
            attribution_breakdown={
                "session_id": session_id,
                "model": model,
                "usage_cost": float(usage_cost),
                "attribution_method": "semantic_similarity",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _create_attribution_capsule(
        self,
        session_id: str,
        attribution_result: AttributionResult,
        context: AttributionContext,
    ):
        """Create attribution capsule for the interaction"""

        try:
            # Create attribution capsule
            attribution_capsule = AttributionCapsule(
                capsule_id=f"attribution_{session_id}",
                capsule_type=CapsuleType.ATTRIBUTION,
                timestamp=datetime.now(timezone.utc),
                status=CapsuleStatus.ACTIVE,
                user_id=context.user_id,
                conversation_id=context.conversation_id,
                attribution_scores=attribution_result.confidence_scores,
                value_distribution={
                    "direct": {
                        k: float(v)
                        for k, v in attribution_result.direct_attributions.items()
                    },
                    "commons": float(attribution_result.commons_allocation),
                    "uba": float(attribution_result.uba_allocation),
                },
                metadata=attribution_result.attribution_breakdown,
            )

            # Create economic capsule for value transfers
            EconomicCapsule(
                capsule_id=f"economic_{session_id}",
                capsule_type=CapsuleType.ECONOMIC,
                timestamp=datetime.now(timezone.utc),
                status=CapsuleStatus.ACTIVE,
                transaction_type="ai_attribution",
                amount=attribution_result.total_value,
                from_agent=f"openai_{context.conversation_id}",
                to_agent=context.user_id,
                attribution_reference=attribution_capsule.capsule_id,
                economic_data={
                    "platform": "openai",
                    "model": attribution_result.attribution_breakdown["model"],
                    "value_breakdown": {
                        "direct_attributions": float(
                            sum(attribution_result.direct_attributions.values())
                        ),
                        "commons_allocation": float(
                            attribution_result.commons_allocation
                        ),
                        "uba_allocation": float(attribution_result.uba_allocation),
                    },
                },
            )

            logger.info(f"Created attribution capsules for session {session_id}")

        except Exception as e:
            logger.error(f"Failed to create attribution capsules: {e}")

    def _estimate_interaction_cost(
        self, prompt: str, completion: str, model: str
    ) -> float:
        """Estimate cost of the interaction"""

        # Rough token estimation (more sophisticated tokenization could be used)
        prompt_tokens = len(prompt.split()) * 1.3  # Rough approximation
        completion_tokens = len(completion.split()) * 1.3

        # Cost estimation based on model
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
        }

        model_pricing = pricing.get(model, pricing["gpt-4"])

        input_cost = (prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (completion_tokens / 1000) * model_pricing["output"]

        return input_cost + output_cost

    async def get_user_attribution_summary(
        self, user_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get attribution summary for a user"""

        # This would typically query the capsule chain or database
        # For now, return a placeholder structure
        return {
            "user_id": user_id,
            "period_days": days,
            "total_attributed_value": 0.0,
            "direct_attributions": 0.0,
            "commons_contributions": 0.0,
            "uba_received": 0.0,
            "attribution_count": 0,
            "average_confidence": 0.0,
            "top_sources": [],
        }

    async def track_conversation_attribution(
        self,
        conversation_id: str,
        messages: List[Dict[str, str]],
        attribution_context: AttributionContext,
    ) -> List[AttributionResult]:
        """Track attribution for an entire conversation"""

        attribution_results = []

        for i, message in enumerate(messages):
            if message["role"] == "user":
                # Find corresponding assistant response
                if i + 1 < len(messages) and messages[i + 1]["role"] == "assistant":
                    context = AttributionContext(
                        user_id=attribution_context.user_id,
                        conversation_id=f"{conversation_id}_msg_{i}",
                        prompt_sources=attribution_context.prompt_sources,
                        training_data_sources=attribution_context.training_data_sources,
                        attribution_metadata={
                            **attribution_context.attribution_metadata,
                            "message_index": i,
                            "conversation_id": conversation_id,
                        },
                    )

                    # Calculate attribution for this exchange
                    _, attribution_result = await self.get_completion_with_attribution(
                        prompt=message["content"],
                        attribution_context=context,
                        model="gpt-4",  # Default model
                    )

                    attribution_results.append(attribution_result)

        return attribution_results


# Factory function for easy instantiation
def create_attribution_client(
    attribution_engine: Optional[EconomicEngine] = None, **kwargs
) -> OpenAIAttributionClient:
    """Create an OpenAI attribution client with default configuration"""

    return OpenAIAttributionClient(attribution_engine=attribution_engine, **kwargs)


# Example usage
if __name__ == "__main__":

    async def demo_attribution():
        """Demonstrate attribution tracking"""

        # Create attribution client
        client = create_attribution_client()

        # Create attribution context
        context = AttributionContext(
            user_id="user123",
            conversation_id="conv456",
            prompt_sources=["user_knowledge", "training_data"],
            training_data_sources=["web_crawl", "books", "papers"],
            attribution_metadata={"platform": "openai", "session_type": "interactive"},
        )

        # Get completion with attribution
        completion, attribution_result = await client.get_completion_with_attribution(
            prompt="What are the key principles of sustainable development?",
            attribution_context=context,
            model="gpt-3.5-turbo",
        )

        print(f"Completion: {completion}")
        print(f"Attribution Result: {attribution_result}")

        # Get user summary
        summary = await client.get_user_attribution_summary("user123")
        print(f"User Summary: {summary}")

    asyncio.run(demo_attribution())
