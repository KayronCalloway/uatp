# How to Add a New AI Provider

This guide walks you through adding a new AI provider to the UATP Capsule Engine's attribution system.

## Overview

The UATP platform uses a unified attribution framework that supports multiple AI providers through a common interface. Adding a new provider involves:

1. Creating a provider-specific client
2. Implementing the attribution interface
3. Registering the provider in the platform framework
4. Adding configuration support
5. Writing tests

## Step 1: Create the Provider Client

### 1.1 Create the base client file

Create `src/integrations/your_provider_client.py`:

```python
"""
Your Provider Integration Client
Basic API interaction with YourProvider
"""

import asyncio
import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)

@dataclass
class YourProviderUsageMetrics:
    """Usage metrics for cost tracking"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float

class YourProviderClient:
    """Basic client for YourProvider API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("YOUR_PROVIDER_API_KEY")
        self.base_url = "https://api.yourprovider.com/v1"
        self.client = httpx.AsyncClient()

    async def get_completion(
        self,
        prompt: str,
        model: str = "your-model-name",
        max_tokens: int = 150,
        temperature: float = 0.7,
        **kwargs
    ) -> tuple[str, YourProviderUsageMetrics]:
        """
        Get completion from YourProvider API

        Returns:
            Tuple of (completion_text, usage_metrics)
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        response = await self.client.post(
            f"{self.base_url}/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()

        data = response.json()

        # Extract completion text (adjust based on API response format)
        completion_text = data["choices"][0]["text"]

        # Extract usage metrics
        usage = data.get("usage", {})
        metrics = YourProviderUsageMetrics(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            estimated_cost=self._calculate_cost(usage, model)
        )

        return completion_text, metrics

    def _calculate_cost(self, usage: Dict, model: str) -> float:
        """Calculate estimated cost based on usage and model pricing"""
        # Implement based on your provider's pricing model
        prompt_cost_per_1k = 0.001  # Example rate
        completion_cost_per_1k = 0.002  # Example rate

        prompt_cost = (usage.get("prompt_tokens", 0) / 1000) * prompt_cost_per_1k
        completion_cost = (usage.get("completion_tokens", 0) / 1000) * completion_cost_per_1k

        return prompt_cost + completion_cost
```

### 1.2 Create the attribution wrapper

Create `src/integrations/your_provider_attribution.py`:

```python
"""
YourProvider Attribution Integration
Real-time attribution tracking for YourProvider API interactions
"""

import logging
from typing import Dict, Optional, Any
from decimal import Decimal
from datetime import datetime, timezone

from .your_provider_client import YourProviderClient, YourProviderUsageMetrics
from .openai_attribution import AttributionContext, AttributionResult
from ..engine.economic_engine import UatpEconomicEngine as EconomicEngine
from ..capsule_schema import CapsuleType, CapsuleStatus
from ..capsules.specialized_capsules import AttributionCapsule, EconomicCapsule

logger = logging.getLogger(__name__)

class YourProviderAttributionClient(YourProviderClient):
    """Enhanced YourProvider client with real-time attribution tracking"""

    def __init__(self, attribution_engine: Optional[EconomicEngine] = None, **kwargs):
        super().__init__(**kwargs)
        self.attribution_engine = attribution_engine or EconomicEngine()
        self.attribution_sessions = {}

    async def get_completion_with_attribution(
        self,
        prompt: str,
        attribution_context: AttributionContext,
        model: str = "your-default-model",
        max_tokens: int = 150,
        **kwargs
    ) -> tuple[str, AttributionResult]:
        """
        Get completion with real-time attribution tracking

        Args:
            prompt: The input prompt
            attribution_context: Context for attribution calculation
            model: YourProvider model to use
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Tuple of (completion_text, attribution_result)
        """
        # Track session start
        session_id = f"{attribution_context.conversation_id}_{datetime.now().timestamp()}"
        self.attribution_sessions[session_id] = {
            'start_time': datetime.now(timezone.utc),
            'context': attribution_context
        }

        try:
            # Get completion from base client
            completion, usage_metrics = await self.get_completion(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                **kwargs
            )

            # Calculate attribution
            attribution_result = await self._calculate_attribution(
                attribution_context,
                usage_metrics,
                model,
                completion
            )

            # Create capsules for tracking
            await self._create_attribution_capsules(
                session_id,
                attribution_context,
                attribution_result,
                usage_metrics
            )

            logger.info(f"YourProvider completion with attribution: {len(completion)} chars")
            return completion, attribution_result

        except Exception as e:
            logger.error(f"YourProvider attribution error: {e}")
            raise
        finally:
            # Clean up session
            self.attribution_sessions.pop(session_id, None)

    async def _calculate_attribution(
        self,
        context: AttributionContext,
        usage_metrics: YourProviderUsageMetrics,
        model: str,
        completion: str
    ) -> AttributionResult:
        """Calculate attribution based on usage and context"""

        # Base value calculation
        total_value = Decimal(str(usage_metrics.estimated_cost))

        # Attribution distribution
        direct_attributions = {}
        for source in context.prompt_sources:
            # Distribute based on contribution (simplified example)
            direct_attributions[source] = total_value * Decimal("0.3")

        # Commons and UBA allocation
        commons_allocation = total_value * Decimal("0.4")
        uba_allocation = total_value * Decimal("0.3")

        # Confidence scoring based on your provider's capabilities
        confidence_scores = {
            "source_identification": 0.85,
            "value_attribution": 0.90,
            "economic_calculation": 0.95
        }

        return AttributionResult(
            total_value=total_value,
            direct_attributions=direct_attributions,
            commons_allocation=commons_allocation,
            uba_allocation=uba_allocation,
            confidence_scores=confidence_scores,
            attribution_breakdown={
                "model": model,
                "provider": "YourProvider",
                "tokens_used": usage_metrics.total_tokens,
                "estimated_cost": usage_metrics.estimated_cost
            }
        )

    async def _create_attribution_capsules(
        self,
        session_id: str,
        context: AttributionContext,
        attribution_result: AttributionResult,
        usage_metrics: YourProviderUsageMetrics
    ):
        """Create capsules to track this attribution event"""

        # Attribution capsule
        attribution_capsule = AttributionCapsule(
            capsule_id=f"attr_{session_id}",
            attribution_data={
                "provider": "YourProvider",
                "user_id": context.user_id,
                "conversation_id": context.conversation_id,
                "total_value": float(attribution_result.total_value),
                "direct_attributions": {k: float(v) for k, v in attribution_result.direct_attributions.items()},
                "commons_allocation": float(attribution_result.commons_allocation),
                "uba_allocation": float(attribution_result.uba_allocation),
                "confidence_scores": attribution_result.confidence_scores
            },
            status=CapsuleStatus.VALIDATED,
            created_at=datetime.now(timezone.utc)
        )

        # Economic capsule
        economic_capsule = EconomicCapsule(
            capsule_id=f"econ_{session_id}",
            economic_data={
                "provider": "YourProvider",
                "usage_metrics": {
                    "prompt_tokens": usage_metrics.prompt_tokens,
                    "completion_tokens": usage_metrics.completion_tokens,
                    "total_tokens": usage_metrics.total_tokens,
                    "estimated_cost": usage_metrics.estimated_cost
                },
                "attribution_breakdown": attribution_result.attribution_breakdown
            },
            status=CapsuleStatus.VALIDATED,
            created_at=datetime.now(timezone.utc)
        )

        # Store capsules (integrate with your storage system)
        logger.info(f"Created attribution capsules for session {session_id}")
```

## Step 2: Register in the Platform Framework

### 2.1 Add to AIProvider enum

Edit `src/integrations/ai_platform_framework.py`:

```python
class AIProvider(Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    GOOGLE = "google"
    COHERE = "cohere"
    YOUR_PROVIDER = "your_provider"  # Add your provider
    GENERIC = "generic"
```

### 2.2 Update the platform orchestrator

In the same file, update the `MultiPlatformAttributionOrchestrator`:

```python
def _create_client(self, config: PlatformConfig) -> Any:
    """Create appropriate client based on provider"""
    if config.provider == AIProvider.OPENAI:
        from .openai_attribution import OpenAIAttributionClient
        return OpenAIAttributionClient(
            attribution_engine=self.economic_engine,
            api_key=config.api_key
        )
    elif config.provider == AIProvider.ANTHROPIC:
        from .anthropic_client import AnthropicAttributionClient
        return AnthropicAttributionClient(
            attribution_engine=self.economic_engine,
            api_key=config.api_key
        )
    elif config.provider == AIProvider.YOUR_PROVIDER:  # Add this
        from .your_provider_attribution import YourProviderAttributionClient
        return YourProviderAttributionClient(
            attribution_engine=self.economic_engine,
            api_key=config.api_key
        )
    else:
        raise ValueError(f"Unsupported provider: {config.provider}")
```

## Step 3: Add Configuration Support

### 3.1 Update app factory

Edit `src/app_factory.py` to support your provider's API key:

```python
app.state.ai_orchestrator = setup_multi_platform_attribution(
    openai_key=os.getenv("OPENAI_API_KEY"),
    anthropic_key=os.getenv("ANTHROPIC_API_KEY"),
    your_provider_key=os.getenv("YOUR_PROVIDER_API_KEY"),  # Add this
)
```

### 3.2 Update configuration documentation

Add to `docs/configuration.md`:

```markdown
- **`YOUR_PROVIDER_API_KEY`** - YourProvider API key
  - Format: (describe format)
  - Used for: YourProvider AI processing and attribution
```

## Step 4: Write Tests

Create `tests/test_your_provider_integration.py`:

```python
"""Tests for YourProvider integration"""

import pytest
from unittest.mock import Mock, AsyncMock
from decimal import Decimal

from src.integrations.your_provider_attribution import YourProviderAttributionClient
from src.integrations.openai_attribution import AttributionContext


@pytest.fixture
def mock_your_provider_client():
    """Mock YourProvider client"""
    client = YourProviderAttributionClient(api_key="test-key")
    client.get_completion = AsyncMock()
    return client


@pytest.fixture
def sample_attribution_context():
    """Sample attribution context for testing"""
    return AttributionContext(
        user_id="test_user",
        conversation_id="test_conversation",
        prompt_sources=["source1", "source2"],
        training_data_sources=["training1"],
        attribution_metadata={"test": "metadata"}
    )


@pytest.mark.asyncio
async def test_completion_with_attribution(mock_your_provider_client, sample_attribution_context):
    """Test completion with attribution tracking"""

    # Mock the base completion call
    mock_usage = Mock()
    mock_usage.prompt_tokens = 50
    mock_usage.completion_tokens = 30
    mock_usage.total_tokens = 80
    mock_usage.estimated_cost = 0.001

    mock_your_provider_client.get_completion.return_value = ("Test completion", mock_usage)

    # Test completion with attribution
    completion, attribution = await mock_your_provider_client.get_completion_with_attribution(
        prompt="Test prompt",
        attribution_context=sample_attribution_context,
        model="test-model"
    )

    # Assertions
    assert completion == "Test completion"
    assert isinstance(attribution.total_value, Decimal)
    assert attribution.total_value > 0
    assert len(attribution.direct_attributions) > 0
    assert attribution.commons_allocation > 0
    assert attribution.uba_allocation > 0


@pytest.mark.asyncio
async def test_attribution_calculation(mock_your_provider_client, sample_attribution_context):
    """Test attribution calculation logic"""

    # Create mock usage metrics
    from src.integrations.your_provider_client import YourProviderUsageMetrics
    usage = YourProviderUsageMetrics(
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        estimated_cost=0.002
    )

    # Test attribution calculation
    attribution = await mock_your_provider_client._calculate_attribution(
        sample_attribution_context,
        usage,
        "test-model",
        "test completion"
    )

    # Verify attribution structure
    assert attribution.total_value == Decimal("0.002")
    assert len(attribution.confidence_scores) > 0
    assert "provider" in attribution.attribution_breakdown
    assert attribution.attribution_breakdown["provider"] == "YourProvider"
```

## Step 5: Add to Multimodal Adapters (Optional)

If your provider supports multimodal capabilities, add to `src/integrations/multimodal_adapters.py`:

```python
class YourProviderMultimodalAdapter(MultimodalAdapter):
    """Multimodal adapter for YourProvider"""

    async def process_image_with_text(
        self,
        image_data: bytes,
        text_prompt: str,
        attribution_context: AttributionContext
    ) -> MultimodalResult:
        """Process image and text through YourProvider"""
        # Implement multimodal processing
        pass
```

## Step 6: Integration Example

Here's how to use your new provider:

```python
from src.integrations.ai_platform_framework import (
    MultiPlatformAttributionOrchestrator,
    PlatformConfig,
    AIProvider
)
from src.integrations.openai_attribution import AttributionContext

# Configure your provider
config = PlatformConfig(
    provider=AIProvider.YOUR_PROVIDER,
    api_key="your-api-key",
    model_name="your-model-name",
    max_tokens=200,
    temperature=0.7
)

# Create orchestrator and add provider
orchestrator = MultiPlatformAttributionOrchestrator()
orchestrator.add_platform("your_provider", config)

# Use with attribution
context = AttributionContext(
    user_id="user123",
    conversation_id="conv456",
    prompt_sources=["source1", "source2"]
)

completion, attribution = await orchestrator.get_completion_with_attribution(
    provider_id="your_provider",
    prompt="Your prompt here",
    attribution_context=context
)
```

## Testing Checklist

- [ ] Basic API client works independently
- [ ] Attribution calculation produces reasonable results
- [ ] Capsules are created correctly
- [ ] Error handling works properly
- [ ] Configuration is loaded correctly
- [ ] Integration tests pass
- [ ] Multimodal support (if applicable)

## Best Practices

1. **Error Handling**: Implement robust error handling for API failures
2. **Rate Limiting**: Respect provider rate limits
3. **Cost Tracking**: Accurate cost calculation for economic attribution
4. **Security**: Never log API keys or sensitive data
5. **Testing**: Comprehensive unit and integration tests
6. **Documentation**: Update all relevant documentation

## Common Pitfalls

- **API Response Format**: Each provider has different response structures
- **Rate Limits**: Don't forget to implement proper backoff strategies
- **Cost Calculation**: Pricing models vary significantly between providers
- **Authentication**: Each provider has different auth mechanisms
- **Model Names**: Use consistent model naming conventions

For additional help, see existing integrations in `src/integrations/` or reach out to the development team.
