import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion

# Import circuit breaker
from src.resilience import (
    CircuitBreakerConfig,
    ExternalServiceClient,
    ExternalServiceError,
)

# Load environment variables from .env file
load_dotenv()

# Import secrets manager
try:
    from security.secrets_manager import SecretsManager
except ImportError:
    # Fallback if secrets manager is not available
    SecretsManager = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UsageMetrics:
    """Tracks OpenAI API usage and costs."""

    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: Decimal = field(default_factory=lambda: Decimal("0.00"))
    request_count: int = 0
    error_count: int = 0
    last_request_time: Optional[datetime] = None

    def add_usage(self, response: ChatCompletion, model: str) -> None:
        """Add usage data from an OpenAI response."""
        if response.usage:
            self.total_tokens += response.usage.total_tokens or 0
            self.prompt_tokens += response.usage.prompt_tokens or 0
            self.completion_tokens += response.usage.completion_tokens or 0
            self.total_cost += self._calculate_cost(response.usage, model)

        self.request_count += 1
        self.last_request_time = datetime.now(timezone.utc)

    def _calculate_cost(self, usage: Any, model: str) -> Decimal:
        """Calculate cost based on OpenAI pricing."""
        # Pricing as of 2024 (in USD per 1k tokens)
        pricing = {
            "gpt-4": {"input": Decimal("0.03"), "output": Decimal("0.06")},
            "gpt-4-turbo": {"input": Decimal("0.01"), "output": Decimal("0.03")},
            "gpt-3.5-turbo": {"input": Decimal("0.001"), "output": Decimal("0.002")},
        }

        model_pricing = pricing.get(model, pricing["gpt-4"])  # Default to gpt-4 pricing

        input_cost = (Decimal(str(usage.prompt_tokens or 0)) / 1000) * model_pricing[
            "input"
        ]
        output_cost = (
            Decimal(str(usage.completion_tokens or 0)) / 1000
        ) * model_pricing["output"]

        return input_cost + output_cost


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Base for exponential backoff
    jitter: bool = True  # Add random jitter to avoid thundering herd


class OpenAIClient(ExternalServiceClient):
    """A hardened client for interacting with the OpenAI API with circuit breaker, retry logic and cost tracking."""

    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None,
    ):
        """
        Initializes the hardened OpenAI client.

        Args:
            retry_config: Configuration for retry behavior. Uses defaults if None.
            circuit_config: Configuration for circuit breaker. Uses defaults if None.

        Raises:
            ValueError: If the OPENAI_API_KEY environment variable is not set.
        """
        # Initialize circuit breaker with service name
        circuit_config = circuit_config or CircuitBreakerConfig(
            failure_threshold=3, recovery_timeout=30, timeout=60, retry_attempts=3
        )
        super().__init__("openai_api", circuit_config)

        # Initialize secrets manager if available
        try:
            from security.secrets_manager import LocalSecretsBackend

            default_backend = LocalSecretsBackend()
            self.secrets_manager = (
                SecretsManager(backend=default_backend) if SecretsManager else None
            )
        except Exception:
            self.secrets_manager = None

        # API key will be loaded on demand
        self.api_key = None
        self.client = None
        self.async_client = None

        # Initialize retry configuration and usage tracking
        self.retry_config = retry_config or RetryConfig()
        self.usage_metrics = UsageMetrics()

        logger.info(
            "OpenAI client initialized with circuit breaker and retry configuration"
        )

    async def _ensure_api_key_loaded(self) -> None:
        """Ensure API key is loaded from vault or environment."""
        if not self.api_key:
            # Try to get from secrets manager first
            if self.secrets_manager:
                self.api_key = await self.secrets_manager.get_secret("OPENAI_API_KEY")

            # Fallback to environment variable
            if not self.api_key:
                self.api_key = os.getenv("OPENAI_API_KEY")

            if not self.api_key:
                raise ValueError(
                    "OPENAI_API_KEY not found in vault or environment variables. Please configure it."
                )

            # Initialize clients now that we have the API key
            self.client = OpenAI(api_key=self.api_key)  # proxies removed
            self.async_client = AsyncOpenAI(api_key=self.api_key)

    def get_completion(
        self, prompt: str, model: str = "gpt-4", max_tokens: int = 150, **kwargs
    ) -> str:
        """
        Gets a completion from the specified OpenAI model with circuit breaker protection. (Synchronous)

        Args:
            prompt (str): The prompt to send to the model.
            model (str): The model to use for generation (e.g., "gpt-4").
            max_tokens (int): The maximum number of tokens to generate.

        Returns:
            str: The generated text.

        Raises:
            Exception: If the API call fails after all retries or circuit breaker is open.
        """
        # Use asyncio.run to call the async version
        return asyncio.run(
            self.get_completion_async(prompt, model, max_tokens, **kwargs)
        )

    async def get_completion_async(
        self, prompt: str, model: str = "gpt-4", max_tokens: int = 150, **kwargs
    ) -> str:
        """
        Gets a completion from the specified OpenAI model with circuit breaker protection. (Asynchronous)

        Args:
            prompt (str): The prompt to send to the model.
            model (str): The model to use for generation (e.g., "gpt-4").
            max_tokens (int): The maximum number of tokens to generate.

        Returns:
            str: The generated text.

        Raises:
            Exception: If the API call fails after all retries or circuit breaker is open.
        """
        # Use circuit breaker to make the call
        return await self.call(prompt, model, max_tokens, **kwargs)

    async def _make_request(
        self, prompt: str, model: str = "gpt-4", max_tokens: int = 150, **kwargs
    ) -> str:
        """
        Make the actual request to OpenAI API. This is called by the circuit breaker.

        Args:
            prompt (str): The prompt to send to the model.
            model (str): The model to use for generation (e.g., "gpt-4").
            max_tokens (int): The maximum number of tokens to generate.

        Returns:
            str: The generated text.

        Raises:
            ExternalServiceError: If the API call fails.
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]

        # Ensure API key is loaded
        await self._ensure_api_key_loaded()

        try:
            logger.info("Making OpenAI API call with circuit breaker protection")

            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                **kwargs,
            )

            # Track usage metrics
            self.usage_metrics.add_usage(response, model)

            logger.info(
                f"OpenAI API call successful. Total cost: ${self.usage_metrics.total_cost}"
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            self.usage_metrics.error_count += 1
            logger.error(f"OpenAI API call failed: {e}")

            # Convert to ExternalServiceError for circuit breaker handling
            raise ExternalServiceError(f"OpenAI API error: {str(e)}") from e

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff with jitter."""
        import random

        delay = min(
            self.retry_config.base_delay
            * (self.retry_config.exponential_base**attempt),
            self.retry_config.max_delay,
        )

        if self.retry_config.jitter:
            # Add random jitter (±25% of delay)
            jitter = delay * 0.25 * (2 * random.random() - 1)
            delay += jitter

        return max(0, delay)

    def get_usage_metrics(self) -> UsageMetrics:
        """Get current usage metrics."""
        return self.usage_metrics

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of usage metrics including circuit breaker status."""
        base_summary = {
            "total_requests": self.usage_metrics.request_count,
            "total_errors": self.usage_metrics.error_count,
            "success_rate": (
                (self.usage_metrics.request_count - self.usage_metrics.error_count)
                / max(1, self.usage_metrics.request_count)
            )
            * 100,
            "total_tokens": self.usage_metrics.total_tokens,
            "prompt_tokens": self.usage_metrics.prompt_tokens,
            "completion_tokens": self.usage_metrics.completion_tokens,
            "total_cost_usd": float(self.usage_metrics.total_cost),
            "average_cost_per_request": (
                float(self.usage_metrics.total_cost)
                / max(1, self.usage_metrics.request_count)
            ),
            "last_request_time": self.usage_metrics.last_request_time.isoformat()
            if self.usage_metrics.last_request_time
            else None,
        }

        # Add circuit breaker health status
        base_summary["circuit_breaker"] = self.get_health_status()

        return base_summary

    def reset_usage_metrics(self) -> None:
        """Reset usage metrics to zero."""
        self.usage_metrics = UsageMetrics()
        logger.info("Usage metrics reset")


# Example usage and testing
if __name__ == "__main__":

    async def test_hardened_client():
        """Test the hardened OpenAI client."""
        # Create client with custom retry configuration
        retry_config = RetryConfig(max_retries=2, base_delay=0.5, max_delay=30.0)

        client = OpenAIClient(retry_config)

        try:
            # Test synchronous call
            print("Testing synchronous call...")
            response = client.get_completion("What is 2+2?", model="gpt-3.5-turbo")
            print(f"Response: {response}")

            # Test asynchronous call
            print("\nTesting asynchronous call...")
            async_response = await client.get_completion_async(
                "What is the capital of France?", model="gpt-3.5-turbo"
            )
            print(f"Async Response: {async_response}")

            # Show usage metrics
            print("\nUsage Summary:")
            summary = client.get_usage_summary()
            for key, value in summary.items():
                print(f"  {key}: {value}")

        except Exception as e:
            print(f"Error during testing: {e}")

    # Run test if script is executed directly
    import asyncio

    asyncio.run(test_hardened_client())
