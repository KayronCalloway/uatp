"""
Attribution Tracking Middleware
Real-time middleware for intercepting and tracking AI conversations
"""

import asyncio
import inspect
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

from ..economic.capsule_economics import capsule_economics
from ..economic.fcde_engine import ContributionType, fcde_engine
from ..integrations.ai_platform_framework import AIAttributionOrchestrator, AIProvider
from ..integrations.openai_attribution import AttributionContext, AttributionResult
from ..user_management.dashboard import UserDashboard
from ..user_management.user_service import UserService

logger = logging.getLogger(__name__)


@dataclass
class MiddlewareConfig:
    """Configuration for attribution middleware"""

    enabled: bool = True
    track_all_requests: bool = True
    minimum_attribution_amount: float = 0.001
    store_conversation_history: bool = True
    enable_real_time_notifications: bool = True
    batch_size: int = 10
    flush_interval: int = 30  # seconds


@dataclass
class RequestContext:
    """Context for individual requests"""

    request_id: str
    user_id: str
    timestamp: datetime
    platform: str
    model: str
    conversation_id: str
    prompt: str
    metadata: Dict[str, Any]


class AttributionMiddleware:
    """Middleware for tracking AI conversations and attributions"""

    def __init__(
        self,
        ai_orchestrator: AIAttributionOrchestrator,
        user_service: UserService,
        user_dashboard: UserDashboard,
        config: Optional[MiddlewareConfig] = None,
    ):
        self.ai_orchestrator = ai_orchestrator
        self.user_service = user_service
        self.user_dashboard = user_dashboard
        self.config = config or MiddlewareConfig()

        # Request tracking
        self.active_requests: Dict[str, RequestContext] = {}
        self.request_queue: List[Dict[str, Any]] = []
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}

        # Start background tasks
        self._background_tasks = []
        if self.config.enabled:
            self._start_background_tasks()

    def _start_background_tasks(self):
        """Start background processing tasks"""

        # Batch processing task
        batch_task = asyncio.create_task(self._batch_processor())
        self._background_tasks.append(batch_task)

        # Cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_processor())
        self._background_tasks.append(cleanup_task)

        logger.info("Attribution middleware background tasks started")

    async def _batch_processor(self):
        """Process attribution requests in batches"""

        while True:
            try:
                if len(self.request_queue) >= self.config.batch_size:
                    # Process batch
                    batch = self.request_queue[: self.config.batch_size]
                    self.request_queue = self.request_queue[self.config.batch_size :]

                    await self._process_attribution_batch(batch)

                await asyncio.sleep(self.config.flush_interval)

            except Exception as e:
                logger.error(f"Batch processor error: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def _cleanup_processor(self):
        """Clean up expired requests and conversations"""

        while True:
            try:
                now = datetime.now(timezone.utc)

                # Clean up old active requests (> 1 hour)
                expired_requests = [
                    req_id
                    for req_id, context in self.active_requests.items()
                    if (now - context.timestamp).total_seconds() > 3600
                ]

                for req_id in expired_requests:
                    del self.active_requests[req_id]

                # Clean up old conversation history (> 24 hours)
                for conv_id, messages in list(self.conversation_history.items()):
                    if (
                        messages
                        and (
                            now
                            - datetime.fromisoformat(
                                messages[-1]["timestamp"].replace("Z", "+00:00")
                            )
                        ).total_seconds()
                        > 86400
                    ):
                        del self.conversation_history[conv_id]

                await asyncio.sleep(3600)  # Run every hour

            except Exception as e:
                logger.error(f"Cleanup processor error: {e}")
                await asyncio.sleep(300)  # Wait before retrying

    async def _process_attribution_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of attribution requests"""

        for request_data in batch:
            try:
                await self._process_single_attribution(request_data)
            except Exception as e:
                logger.error(f"Error processing attribution: {e}")

    async def _process_single_attribution(self, request_data: Dict[str, Any]):
        """Process a single attribution request"""

        user_id = request_data["user_id"]
        platform = request_data["platform"]
        model = request_data["model"]
        conversation_id = request_data["conversation_id"]
        prompt = request_data["prompt"]
        completion = request_data["completion"]
        metadata = request_data.get("metadata", {})

        # Create attribution context
        context = AttributionContext(
            user_id=user_id,
            conversation_id=conversation_id,
            prompt_sources=metadata.get("prompt_sources", ["user_input"]),
            training_data_sources=metadata.get(
                "training_data_sources", ["web_crawl", "books"]
            ),
            attribution_metadata={
                "platform": platform,
                "model": model,
                "middleware_processed": True,
                **metadata,
            },
        )

        # Calculate attribution using AI orchestrator
        provider = self._get_provider_from_platform(platform)
        if provider in self.ai_orchestrator.clients:
            # Use existing attribution calculation
            attribution_result = await self._calculate_attribution_direct(
                prompt, completion, context, platform, model
            )

            # Record in dashboard
            await self.user_dashboard.record_attribution_activity(
                user_id=user_id,
                platform=platform,
                model=model,
                conversation_id=conversation_id,
                prompt=prompt,
                attribution_result=attribution_result,
            )

            # Integrate with FCDE economic engine
            await self._process_fcde_attribution(
                user_id=user_id,
                conversation_id=conversation_id,
                platform=platform,
                attribution_result=attribution_result,
                metadata=metadata,
            )

            logger.info(
                f"Attribution processed: {user_id} - ${attribution_result.total_value}"
            )

    def _get_provider_from_platform(self, platform: str) -> AIProvider:
        """Map platform string to AIProvider enum"""

        platform_map = {
            "openai": AIProvider.OPENAI,
            "anthropic": AIProvider.ANTHROPIC,
            "claude": AIProvider.ANTHROPIC,
            "huggingface": AIProvider.HUGGINGFACE,
            "google": AIProvider.GOOGLE,
            "cohere": AIProvider.COHERE,
        }

        return platform_map.get(platform.lower(), AIProvider.GENERIC)

    async def _calculate_attribution_direct(
        self,
        prompt: str,
        completion: str,
        context: AttributionContext,
        platform: str,
        model: str,
    ) -> AttributionResult:
        """Calculate attribution directly without API call"""

        # This is a simplified attribution calculation
        # In production, this would use the full economic engine

        from decimal import Decimal

        # Estimate value based on token count and model
        estimated_tokens = len(prompt.split()) + len(completion.split())

        # Simple cost estimation
        cost_per_token = {
            "gpt-4": 0.00003,
            "gpt-3.5-turbo": 0.000001,
            "claude-3-5-sonnet": 0.000015,
            "claude-3-haiku": 0.0000005,
        }

        estimated_cost = estimated_tokens * cost_per_token.get(model, 0.00001)

        # Create attribution result
        total_value = Decimal(str(estimated_cost))
        uba_allocation = total_value * Decimal("0.15")
        commons_allocation = total_value * Decimal("0.25")
        direct_attributions = {
            "user_input": total_value - uba_allocation - commons_allocation
        }

        return AttributionResult(
            total_value=total_value,
            direct_attributions=direct_attributions,
            commons_allocation=commons_allocation,
            uba_allocation=uba_allocation,
            confidence_scores={"user_input": 0.75},
            attribution_breakdown={
                "platform": platform,
                "model": model,
                "estimated_tokens": estimated_tokens,
                "middleware_calculated": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def _process_fcde_attribution(
        self,
        user_id: str,
        conversation_id: str,
        platform: str,
        attribution_result: AttributionResult,
        metadata: Dict[str, Any],
    ):
        """Process attribution through FCDE economic engine"""

        try:
            # Create contributions for different stakeholders
            capsule_id = f"conv_{conversation_id}_{int(datetime.now().timestamp())}"

            # Register user contribution (prompt/interaction)
            user_contribution_id = fcde_engine.register_contribution(
                capsule_id=capsule_id,
                contributor_id=user_id,
                contribution_type=ContributionType.KNOWLEDGE_PROVISION,
                quality_score=attribution_result.confidence_scores.get(
                    "user_input", 1.0
                ),
                metadata={
                    "platform": platform,
                    "conversation_id": conversation_id,
                    "attribution_total": float(attribution_result.total_value),
                    **metadata,
                },
            )

            # Register platform provider contribution
            provider_contribution_id = fcde_engine.register_contribution(
                capsule_id=capsule_id,
                contributor_id=f"platform_{platform}",
                contribution_type=ContributionType.COMPUTATION_RESOURCE,
                quality_score=1.0,
                metadata={
                    "platform": platform,
                    "model_used": metadata.get("model", "unknown"),
                    "processing_cost": float(attribution_result.total_value),
                },
            )

            # Process direct attributions to content creators
            for source, value in attribution_result.direct_attributions.items():
                if value > 0:
                    source_contribution_id = fcde_engine.register_contribution(
                        capsule_id=capsule_id,
                        contributor_id=f"source_{source}",
                        contribution_type=ContributionType.CONTENT_CREATION,
                        quality_score=1.0,
                        metadata={
                            "source_identifier": source,
                            "attributed_value": float(value),
                            "attribution_type": "direct",
                        },
                    )

            # Record usage in capsule economics
            economic_value = float(attribution_result.total_value)
            capsule_economics.record_usage(
                capsule_id=capsule_id,
                user_id=user_id,
                usage_type="ai_interaction",
                value=economic_value,
                metadata={
                    "platform": platform,
                    "attribution_breakdown": attribution_result.attribution_breakdown,
                    "commons_allocation": float(attribution_result.commons_allocation),
                    "uba_allocation": float(attribution_result.uba_allocation),
                },
            )

            logger.info(f"FCDE attribution processed: {capsule_id} - ${economic_value}")

        except Exception as e:
            logger.error(f"FCDE attribution processing failed: {e}")
            # Don't raise - attribution should continue even if FCDE fails

    def track_request(
        self,
        user_id: str,
        platform: str,
        model: str,
        conversation_id: str,
        prompt: str,
        **metadata,
    ) -> str:
        """Track a new request"""

        request_id = f"req_{int(datetime.now().timestamp())}_{user_id[-6:]}"

        context = RequestContext(
            request_id=request_id,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            platform=platform,
            model=model,
            conversation_id=conversation_id,
            prompt=prompt,
            metadata=metadata,
        )

        self.active_requests[request_id] = context

        # Store in conversation history
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []

        self.conversation_history[conversation_id].append(
            {
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
            }
        )

        logger.debug(f"Request tracked: {request_id}")
        return request_id

    async def complete_request(self, request_id: str, completion: str, **metadata):
        """Complete a tracked request with attribution"""

        if request_id not in self.active_requests:
            logger.warning(f"Request not found: {request_id}")
            return

        context = self.active_requests[request_id]

        # Add completion to conversation history
        if context.conversation_id in self.conversation_history:
            self.conversation_history[context.conversation_id].append(
                {
                    "role": "assistant",
                    "content": completion,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": request_id,
                }
            )

        # Queue for attribution processing
        if self.config.enabled:
            attribution_request = {
                "request_id": request_id,
                "user_id": context.user_id,
                "platform": context.platform,
                "model": context.model,
                "conversation_id": context.conversation_id,
                "prompt": context.prompt,
                "completion": completion,
                "metadata": {**context.metadata, **metadata},
            }

            self.request_queue.append(attribution_request)

        # Clean up active request
        del self.active_requests[request_id]

        logger.debug(f"Request completed: {request_id}")

    def middleware_decorator(self, platform: str, model: str = None):
        """Decorator for automatic attribution tracking"""

        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Extract user context
                user_id = kwargs.get("user_id") or getattr(args[0], "user_id", None)
                conversation_id = kwargs.get(
                    "conversation_id", f"conv_{int(datetime.now().timestamp())}"
                )
                prompt = kwargs.get("prompt", "")
                model_name = model or kwargs.get("model", "unknown")

                if not user_id:
                    # If no user_id, just call the function normally
                    return await func(*args, **kwargs)

                # Track request
                request_id = self.track_request(
                    user_id=user_id,
                    platform=platform,
                    model=model_name,
                    conversation_id=conversation_id,
                    prompt=prompt,
                    function_name=func.__name__,
                )

                try:
                    # Call the original function
                    result = await func(*args, **kwargs)

                    # Extract completion from result
                    completion = result
                    if isinstance(result, tuple):
                        completion = result[0]
                    elif isinstance(result, dict):
                        completion = result.get("completion", str(result))

                    # Complete request tracking
                    await self.complete_request(request_id, str(completion))

                    return result

                except Exception as e:
                    # Clean up on error
                    if request_id in self.active_requests:
                        del self.active_requests[request_id]
                    raise e

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # For synchronous functions, we can't do full tracking
                # but we can at least log the interaction
                logger.info(f"Sync function called: {func.__name__}")
                return func(*args, **kwargs)

            return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

        return decorator

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return self.conversation_history.get(conversation_id, [])

    def get_active_requests(self) -> Dict[str, RequestContext]:
        """Get currently active requests"""
        return self.active_requests.copy()

    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status"""
        return {
            "queue_size": len(self.request_queue),
            "active_requests": len(self.active_requests),
            "conversations": len(self.conversation_history),
            "config": {
                "enabled": self.config.enabled,
                "batch_size": self.config.batch_size,
                "flush_interval": self.config.flush_interval,
            },
        }

    async def flush_queue(self):
        """Manually flush the attribution queue"""
        if self.request_queue:
            await self._process_attribution_batch(self.request_queue)
            self.request_queue.clear()
            logger.info("Attribution queue flushed")

    async def shutdown(self):
        """Shutdown the middleware"""

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        # Process remaining queue
        if self.request_queue:
            await self._process_attribution_batch(self.request_queue)

        logger.info("Attribution middleware shutdown")


# Context manager for attribution tracking
class AttributionContext:
    """Context manager for attribution tracking"""

    def __init__(
        self,
        middleware: AttributionMiddleware,
        user_id: str,
        platform: str,
        model: str,
        conversation_id: str,
        prompt: str,
        **metadata,
    ):
        self.middleware = middleware
        self.user_id = user_id
        self.platform = platform
        self.model = model
        self.conversation_id = conversation_id
        self.prompt = prompt
        self.metadata = metadata
        self.request_id = None

    def __enter__(self):
        self.request_id = self.middleware.track_request(
            user_id=self.user_id,
            platform=self.platform,
            model=self.model,
            conversation_id=self.conversation_id,
            prompt=self.prompt,
            **self.metadata,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.request_id and self.request_id in self.middleware.active_requests:
            # Clean up if not completed
            del self.middleware.active_requests[self.request_id]

    async def complete(self, completion: str, **metadata):
        """Complete the attribution tracking"""
        if self.request_id:
            await self.middleware.complete_request(
                self.request_id, completion, **metadata
            )


# Factory function
def create_attribution_middleware(
    ai_orchestrator: AIAttributionOrchestrator,
    user_service: UserService,
    user_dashboard: UserDashboard,
    config: Optional[MiddlewareConfig] = None,
) -> AttributionMiddleware:
    """Create an attribution middleware instance"""

    return AttributionMiddleware(
        ai_orchestrator=ai_orchestrator,
        user_service=user_service,
        user_dashboard=user_dashboard,
        config=config,
    )


# Example usage
if __name__ == "__main__":

    async def demo_middleware():
        """Demonstrate the attribution middleware"""

        from ..integrations.ai_platform_framework import create_ai_orchestrator
        from ..user_management.dashboard import create_user_dashboard
        from ..user_management.user_service import create_user_service

        # Create services
        user_service = create_user_service()
        ai_orchestrator = create_ai_orchestrator()
        user_dashboard = create_user_dashboard(user_service, ai_orchestrator)

        # Create middleware
        middleware = create_attribution_middleware(
            ai_orchestrator=ai_orchestrator,
            user_service=user_service,
            user_dashboard=user_dashboard,
        )

        # Register test user
        user_result = await user_service.register_user(
            email="test@example.com",
            username="testuser",
            password="TestPass123!",
            full_name="Test User",
        )

        if user_result["success"]:
            user_id = user_result["user_id"]

            # Test attribution tracking
            request_id = middleware.track_request(
                user_id=user_id,
                platform="openai",
                model="gpt-4",
                conversation_id="test_conv",
                prompt="What is AI?",
            )

            # Complete the request
            await middleware.complete_request(
                request_id=request_id, completion="AI is artificial intelligence..."
            )

            # Check queue status
            status = middleware.get_queue_status()
            print(f"Queue Status: {status}")

            # Flush queue
            await middleware.flush_queue()

            # Get conversation history
            history = middleware.get_conversation_history("test_conv")
            print(f"Conversation History: {history}")

            # Shutdown
            await middleware.shutdown()

    asyncio.run(demo_middleware())
