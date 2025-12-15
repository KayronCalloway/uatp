"""
Anthropic Claude Client with Attribution Integration
Real-time attribution tracking for Anthropic Claude API interactions
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

from ..capsule_schema import CapsuleStatus, CapsuleType
from ..capsules.specialized_capsules import AttributionCapsule, EconomicCapsule
from ..engine.economic_engine import UatpEconomicEngine as EconomicEngine
from .openai_attribution import AttributionContext, AttributionResult

logger = logging.getLogger(__name__)


@dataclass
class ClaudeUsageMetrics:
    """Tracks Claude API usage and costs"""

    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost: Decimal = field(default_factory=lambda: Decimal("0.00"))
    request_count: int = 0
    error_count: int = 0
    last_request_time: Optional[datetime] = None

    def add_usage(self, input_tokens: int, output_tokens: int, model: str) -> None:
        """Add usage data from a Claude response"""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += input_tokens + output_tokens
        self.total_cost += self._calculate_cost(input_tokens, output_tokens, model)
        self.request_count += 1
        self.last_request_time = datetime.now(timezone.utc)

    def _calculate_cost(
        self, input_tokens: int, output_tokens: int, model: str
    ) -> Decimal:
        """Calculate cost based on Claude pricing"""
        # Pricing as of 2024 (in USD per million tokens)
        pricing = {
            "claude-3-5-sonnet-20241022": {
                "input": Decimal("3.00"),
                "output": Decimal("15.00"),
            },
            "claude-3-opus-20240229": {
                "input": Decimal("15.00"),
                "output": Decimal("75.00"),
            },
            "claude-3-haiku-20240307": {
                "input": Decimal("0.25"),
                "output": Decimal("1.25"),
            },
        }

        model_pricing = pricing.get(model, pricing["claude-3-5-sonnet-20241022"])

        input_cost = (Decimal(str(input_tokens)) / 1000000) * model_pricing["input"]
        output_cost = (Decimal(str(output_tokens)) / 1000000) * model_pricing["output"]

        return input_cost + output_cost


class AnthropicAttributionClient:
    """Claude client with real-time attribution tracking"""

    def __init__(self, attribution_engine: Optional[EconomicEngine] = None):
        """Initialize the Claude attribution client"""

        if not ANTHROPIC_AVAILABLE:
            logger.warning("Anthropic package not available, running in demo mode")
            self.api_key = None
            self.client = None
            self.async_client = None
        else:
            # Get API key from environment
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
            if self.api_key:
                try:
                    # Initialize clients with error handling for SDK compatibility
                    self.client = anthropic.Anthropic(api_key=self.api_key)
                    self.async_client = anthropic.AsyncAnthropic(api_key=self.api_key)
                except TypeError as e:
                    # Handle SDK compatibility issues (e.g., 'proxies' parameter error)
                    logger.warning(
                        f"Failed to initialize Anthropic client (SDK compatibility issue): {e}. "
                        f"Running in demo mode. Consider updating the anthropic package."
                    )
                    self.client = None
                    self.async_client = None
                except Exception as e:
                    # Handle any other initialization errors
                    logger.error(
                        f"Unexpected error initializing Anthropic client: {e}. "
                        f"Running in demo mode."
                    )
                    self.client = None
                    self.async_client = None
            else:
                logger.warning("ANTHROPIC_API_KEY not set, running in demo mode")
                self.client = None
                self.async_client = None

        # Initialize components
        self.attribution_engine = attribution_engine or EconomicEngine()
        self.usage_metrics = ClaudeUsageMetrics()
        self.attribution_sessions = {}

        logger.info("Anthropic Claude attribution client initialized")

    async def get_completion_with_attribution(
        self,
        prompt: str,
        attribution_context: AttributionContext,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1024,
        **kwargs,
    ) -> tuple[str, AttributionResult]:
        """
        Get completion with real-time attribution tracking

        Args:
            prompt: The input prompt
            attribution_context: Context for attribution calculation
            model: Claude model to use
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Claude parameters

        Returns:
            Tuple of (completion_text, attribution_result)
        """

        # Track session start
        session_id = (
            f"{attribution_context.conversation_id}_{datetime.now().timestamp()}"
        )
        self.attribution_sessions[session_id] = {
            "start_time": datetime.now(timezone.utc),
            "context": attribution_context,
        }

        try:
            if not self.async_client:
                # Demo mode - create mock response
                completion = f"This is a mock Claude response to: {prompt[:50]}..."
                input_tokens = len(prompt.split()) * 1.3
                output_tokens = len(completion.split()) * 1.3
            else:
                # Get completion from Claude
                response = await self.async_client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                    **kwargs,
                )

                # Extract completion text
                completion = response.content[0].text if response.content else ""
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens

            # Track usage
            self.usage_metrics.add_usage(
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                model=model,
            )

            # Calculate attribution
            attribution_result = await self._calculate_attribution(
                prompt=prompt,
                completion=completion,
                context=attribution_context,
                model=model,
                session_id=session_id,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )

            # Create attribution capsule
            await self._create_attribution_capsule(
                session_id=session_id,
                attribution_result=attribution_result,
                context=attribution_context,
            )

            return completion, attribution_result

        except Exception as e:
            logger.error(f"Claude attribution completion failed: {e}")
            self.usage_metrics.error_count += 1
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
        input_tokens: int,
        output_tokens: int,
    ) -> AttributionResult:
        """Calculate attribution for the Claude interaction"""

        # Calculate interaction cost
        usage_cost = float(
            self.usage_metrics._calculate_cost(input_tokens, output_tokens, model)
        )

        # Prepare attribution data
        attribution_data = {
            "prompt": prompt,
            "completion": completion,
            "prompt_sources": context.prompt_sources,
            "training_data_sources": context.training_data_sources,
            "metadata": {
                **context.attribution_metadata,
                "platform": "anthropic",
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
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
                "usage_cost": usage_cost,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "attribution_method": "semantic_similarity",
                "platform": "anthropic",
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
                capsule_id=f"claude_attribution_{session_id}",
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
            economic_capsule = EconomicCapsule(
                capsule_id=f"claude_economic_{session_id}",
                capsule_type=CapsuleType.ECONOMIC,
                timestamp=datetime.now(timezone.utc),
                status=CapsuleStatus.ACTIVE,
                transaction_type="claude_attribution",
                amount=attribution_result.total_value,
                from_agent=f"claude_{context.conversation_id}",
                to_agent=context.user_id,
                attribution_reference=attribution_capsule.capsule_id,
                economic_data={
                    "platform": "anthropic",
                    "model": attribution_result.attribution_breakdown["model"],
                    "input_tokens": attribution_result.attribution_breakdown[
                        "input_tokens"
                    ],
                    "output_tokens": attribution_result.attribution_breakdown[
                        "output_tokens"
                    ],
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

            logger.info(f"Created Claude attribution capsules for session {session_id}")

        except Exception as e:
            logger.error(f"Failed to create Claude attribution capsules: {e}")

    async def track_conversation_attribution(
        self,
        conversation_id: str,
        messages: List[Dict[str, str]],
        attribution_context: AttributionContext,
    ) -> List[AttributionResult]:
        """Track attribution for an entire Claude conversation"""

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
                        model="claude-3-5-sonnet-20241022",
                    )

                    attribution_results.append(attribution_result)

        return attribution_results

    async def get_user_attribution_summary(
        self, user_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get Claude attribution summary for a user"""

        # This would typically query the capsule chain or database
        # For now, return a placeholder structure
        return {
            "user_id": user_id,
            "platform": "anthropic",
            "period_days": days,
            "total_attributed_value": 0.0,
            "direct_attributions": 0.0,
            "commons_contributions": 0.0,
            "uba_received": 0.0,
            "attribution_count": 0,
            "average_confidence": 0.0,
            "top_sources": [],
            "total_input_tokens": 0,
            "total_output_tokens": 0,
        }

    def get_usage_metrics(self) -> ClaudeUsageMetrics:
        """Get current usage metrics"""
        return self.usage_metrics

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of usage metrics"""
        return {
            "total_requests": self.usage_metrics.request_count,
            "total_errors": self.usage_metrics.error_count,
            "success_rate": (
                (self.usage_metrics.request_count - self.usage_metrics.error_count)
                / max(1, self.usage_metrics.request_count)
            )
            * 100,
            "total_tokens": self.usage_metrics.total_tokens,
            "input_tokens": self.usage_metrics.input_tokens,
            "output_tokens": self.usage_metrics.output_tokens,
            "total_cost_usd": float(self.usage_metrics.total_cost),
            "average_cost_per_request": (
                float(self.usage_metrics.total_cost)
                / max(1, self.usage_metrics.request_count)
            ),
            "last_request_time": self.usage_metrics.last_request_time.isoformat()
            if self.usage_metrics.last_request_time
            else None,
        }


# Factory function for easy instantiation
def create_claude_attribution_client(
    attribution_engine: Optional[EconomicEngine] = None,
) -> AnthropicAttributionClient:
    """Create a Claude attribution client with default configuration"""

    return AnthropicAttributionClient(attribution_engine=attribution_engine)


# Example usage
if __name__ == "__main__":

    async def demo_claude_attribution():
        """Demonstrate Claude attribution tracking"""

        try:
            # Create attribution client
            client = create_claude_attribution_client()

            # Create attribution context
            context = AttributionContext(
                user_id="user123",
                conversation_id="claude_conv456",
                prompt_sources=["user_knowledge", "previous_context"],
                training_data_sources=["web_crawl", "books", "papers"],
                attribution_metadata={
                    "platform": "anthropic",
                    "session_type": "interactive",
                },
            )

            # Get completion with attribution
            (
                completion,
                attribution_result,
            ) = await client.get_completion_with_attribution(
                prompt="Explain the concept of emergence in complex systems.",
                attribution_context=context,
                model="claude-3-5-sonnet-20241022",
            )

            print(f"Claude Completion: {completion}")
            print(f"Attribution Result: {attribution_result}")

            # Get user summary
            summary = await client.get_user_attribution_summary("user123")
            print(f"User Summary: {summary}")

            # Get usage metrics
            metrics = client.get_usage_summary()
            print(f"Usage Metrics: {metrics}")

        except Exception as e:
            print(f"Demo failed: {e}")

    asyncio.run(demo_claude_attribution())
