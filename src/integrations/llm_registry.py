#!/usr/bin/env python3
"""
UATP Capsule Engine - Pluggable LLM Registry
Supports multiple LLM providers: OpenAI, Anthropic, Google Gemini, and local models
"""

import abc
import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LOCAL = "local"


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""

    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""

    content: str
    model: str
    provider: LLMProvider
    tokens_used: int
    cost_usd: float
    response_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMProviderInterface(abc.ABC):
    """Abstract interface for LLM providers."""

    @abc.abstractmethod
    async def generate_completion(self, prompt: str, config: LLMConfig) -> LLMResponse:
        """Generate a completion using the provider's API."""
        pass

    @abc.abstractmethod
    def validate_config(self, config: LLMConfig) -> bool:
        """Validate the configuration for this provider."""
        pass


class OpenAIProvider(LLMProviderInterface):
    """OpenAI provider implementation."""

    def __init__(self):
        self.client = None
        self.async_client = None

    async def generate_completion(self, prompt: str, config: LLMConfig) -> LLMResponse:
        """Generate completion using OpenAI API."""
        if not self.async_client:
            await self._initialize_client(config)

        start_time = datetime.now()

        try:
            response = await self.async_client.chat.completions.create(
                model=config.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                **config.extra_params,
            )

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            content = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if response.usage else 0
            cost_usd = self._calculate_openai_cost(response.usage, config.model_name)

            return LLMResponse(
                content=content,
                model=config.model_name,
                provider=LLMProvider.OPENAI,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                response_time=response_time,
                metadata={"response_id": response.id},
            )

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    def validate_config(self, config: LLMConfig) -> bool:
        """Validate OpenAI configuration."""
        if not config.api_key:
            logger.error("OpenAI API key is required")
            return False

        supported_models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        if config.model_name not in supported_models:
            logger.warning(f"Model {config.model_name} may not be supported by OpenAI")

        return True

    async def _initialize_client(self, config: LLMConfig):
        """Initialize OpenAI client."""
        try:
            from openai import AsyncOpenAI

            self.async_client = AsyncOpenAI(
                api_key=config.api_key, base_url=config.base_url, timeout=config.timeout
            )
        except ImportError:
            raise ImportError("openai package is required for OpenAI provider")

    def _calculate_openai_cost(self, usage: Any, model: str) -> float:
        """Calculate cost for OpenAI API usage."""
        if not usage:
            return 0.0

        # Pricing as of 2024 (USD per 1k tokens)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
        }

        model_pricing = pricing.get(model, pricing["gpt-4"])

        input_cost = (usage.prompt_tokens or 0) / 1000 * model_pricing["input"]
        output_cost = (usage.completion_tokens or 0) / 1000 * model_pricing["output"]

        return input_cost + output_cost


class AnthropicProvider(LLMProviderInterface):
    """Anthropic Claude provider implementation."""

    def __init__(self):
        self.client = None

    async def generate_completion(self, prompt: str, config: LLMConfig) -> LLMResponse:
        """Generate completion using Anthropic API."""
        if not self.client:
            await self._initialize_client(config)

        start_time = datetime.now()

        try:
            response = await self.client.messages.create(
                model=config.model_name,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                messages=[{"role": "user", "content": prompt}],
                **config.extra_params,
            )

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            content = response.content[0].text if response.content else ""
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost_usd = self._calculate_anthropic_cost(response.usage, config.model_name)

            return LLMResponse(
                content=content,
                model=config.model_name,
                provider=LLMProvider.ANTHROPIC,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                response_time=response_time,
                metadata={"response_id": response.id},
            )

        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise

    def validate_config(self, config: LLMConfig) -> bool:
        """Validate Anthropic configuration."""
        if not config.api_key:
            logger.error("Anthropic API key is required")
            return False

        supported_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
        if config.model_name not in supported_models:
            logger.warning(
                f"Model {config.model_name} may not be supported by Anthropic"
            )

        return True

    async def _initialize_client(self, config: LLMConfig):
        """Initialize Anthropic client."""
        try:
            from anthropic import AsyncAnthropic

            self.client = AsyncAnthropic(
                api_key=config.api_key, base_url=config.base_url, timeout=config.timeout
            )
        except ImportError:
            raise ImportError("anthropic package is required for Anthropic provider")

    def _calculate_anthropic_cost(self, usage: Any, model: str) -> float:
        """Calculate cost for Anthropic API usage."""
        if not usage:
            return 0.0

        # Pricing as of 2024 (USD per 1k tokens)
        pricing = {
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        }

        model_pricing = pricing.get(model, pricing["claude-3-sonnet-20240229"])

        input_cost = (usage.input_tokens or 0) / 1000 * model_pricing["input"]
        output_cost = (usage.output_tokens or 0) / 1000 * model_pricing["output"]

        return input_cost + output_cost


class GeminiProvider(LLMProviderInterface):
    """Google Gemini provider implementation."""

    def __init__(self):
        self.client = None

    async def generate_completion(self, prompt: str, config: LLMConfig) -> LLMResponse:
        """Generate completion using Gemini API."""
        if not self.client:
            await self._initialize_client(config)

        start_time = datetime.now()

        try:
            response = await self.client.generate_content_async(
                prompt,
                generation_config={
                    "max_output_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    **config.extra_params,
                },
            )

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            content = response.text if response.text else ""
            tokens_used = (
                response.usage_metadata.total_token_count
                if hasattr(response, "usage_metadata")
                else 0
            )
            cost_usd = self._calculate_gemini_cost(tokens_used, config.model_name)

            return LLMResponse(
                content=content,
                model=config.model_name,
                provider=LLMProvider.GEMINI,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                response_time=response_time,
                metadata={"response_id": getattr(response, "id", "unknown")},
            )

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise

    def validate_config(self, config: LLMConfig) -> bool:
        """Validate Gemini configuration."""
        if not config.api_key:
            logger.error("Google API key is required for Gemini")
            return False

        supported_models = ["gemini-pro", "gemini-pro-vision"]
        if config.model_name not in supported_models:
            logger.warning(f"Model {config.model_name} may not be supported by Gemini")

        return True

    async def _initialize_client(self, config: LLMConfig):
        """Initialize Gemini client."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=config.api_key)
            self.client = genai.GenerativeModel(config.model_name)
        except ImportError:
            raise ImportError(
                "google-generativeai package is required for Gemini provider"
            )

    def _calculate_gemini_cost(self, tokens_used: int, model: str) -> float:
        """Calculate cost for Gemini API usage."""
        # Pricing as of 2024 (USD per 1k tokens)
        pricing = {
            "gemini-pro": 0.0005,  # Per 1k tokens
            "gemini-pro-vision": 0.0025,  # Per 1k tokens
        }

        price_per_token = pricing.get(model, pricing["gemini-pro"])
        return tokens_used / 1000 * price_per_token


class LocalProvider(LLMProviderInterface):
    """Local model provider implementation."""

    def __init__(self):
        self.client = None

    async def generate_completion(self, prompt: str, config: LLMConfig) -> LLMResponse:
        """Generate completion using local model."""
        start_time = datetime.now()

        try:
            # Mock implementation for local models
            # In a real implementation, this would use something like:
            # - Hugging Face Transformers
            # - llama.cpp
            # - Ollama
            # - Custom model serving

            await asyncio.sleep(0.1)  # Simulate processing time

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            content = f"Local model response to: {prompt[:50]}..."
            tokens_used = len(content.split()) * 2  # Rough estimate
            cost_usd = 0.0  # Local models are free

            return LLMResponse(
                content=content,
                model=config.model_name,
                provider=LLMProvider.LOCAL,
                tokens_used=tokens_used,
                cost_usd=cost_usd,
                response_time=response_time,
                metadata={"model_path": config.base_url or "local"},
            )

        except Exception as e:
            logger.error(f"Local model call failed: {e}")
            raise

    def validate_config(self, config: LLMConfig) -> bool:
        """Validate local model configuration."""
        # For local models, we mainly need the model path/name
        if not config.model_name:
            logger.error("Model name/path is required for local models")
            return False

        return True


class LLMRegistry:
    """Registry for managing multiple LLM providers."""

    def __init__(self):
        self.providers: Dict[LLMProvider, LLMProviderInterface] = {
            LLMProvider.OPENAI: OpenAIProvider(),
            LLMProvider.ANTHROPIC: AnthropicProvider(),
            LLMProvider.GEMINI: GeminiProvider(),
            LLMProvider.LOCAL: LocalProvider(),
        }

        self.configs: Dict[str, LLMConfig] = {}
        self.default_provider: Optional[LLMProvider] = None

        logger.info("LLM Registry initialized with all providers")

    def register_config(self, name: str, config: LLMConfig) -> None:
        """Register a new LLM configuration."""
        provider = self.providers.get(config.provider)
        if not provider:
            raise ValueError(f"Unsupported provider: {config.provider}")

        if not provider.validate_config(config):
            raise ValueError(f"Invalid configuration for {config.provider}")

        self.configs[name] = config
        logger.info(
            f"Registered LLM config '{name}' for provider {config.provider.value}"
        )

    def set_default_provider(self, provider: LLMProvider) -> None:
        """Set the default provider."""
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")

        self.default_provider = provider
        logger.info(f"Set default provider to {provider.value}")

    def get_config(self, name: str) -> Optional[LLMConfig]:
        """Get a registered configuration."""
        return self.configs.get(name)

    def list_configs(self) -> List[str]:
        """List all registered configuration names."""
        return list(self.configs.keys())

    def list_providers(self) -> List[LLMProvider]:
        """List all supported providers."""
        return list(self.providers.keys())

    async def generate_completion(
        self, prompt: str, config_name: Optional[str] = None
    ) -> LLMResponse:
        """Generate completion using a registered configuration."""
        if config_name:
            config = self.configs.get(config_name)
            if not config:
                raise ValueError(f"Configuration '{config_name}' not found")
        else:
            # Use default provider if no config specified
            if not self.default_provider:
                raise ValueError("No default provider set and no config specified")

            # Find a config for the default provider
            config = None
            for cfg in self.configs.values():
                if cfg.provider == self.default_provider:
                    config = cfg
                    break

            if not config:
                raise ValueError(
                    f"No configuration found for default provider {self.default_provider.value}"
                )

        provider = self.providers[config.provider]
        return await provider.generate_completion(prompt, config)

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        provider_counts = {}
        for config in self.configs.values():
            provider_counts[config.provider.value] = (
                provider_counts.get(config.provider.value, 0) + 1
            )

        return {
            "total_configs": len(self.configs),
            "supported_providers": [p.value for p in self.providers.keys()],
            "provider_counts": provider_counts,
            "default_provider": self.default_provider.value
            if self.default_provider
            else None,
        }


# Example usage and configuration
def setup_example_registry() -> LLMRegistry:
    """Set up an example LLM registry with multiple providers."""
    registry = LLMRegistry()

    # Register OpenAI configurations
    registry.register_config(
        "openai_gpt4",
        LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-4",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=1000,
            temperature=0.7,
        ),
    )

    registry.register_config(
        "openai_gpt35",
        LLMConfig(
            provider=LLMProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY"),
            max_tokens=500,
            temperature=0.5,
        ),
    )

    # Register Anthropic configurations
    registry.register_config(
        "anthropic_claude",
        LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model_name="claude-3-sonnet-20240229",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=1000,
            temperature=0.7,
        ),
    )

    # Register Gemini configurations
    registry.register_config(
        "gemini_pro",
        LLMConfig(
            provider=LLMProvider.GEMINI,
            model_name="gemini-pro",
            api_key=os.getenv("GOOGLE_API_KEY"),
            max_tokens=1000,
            temperature=0.7,
        ),
    )

    # Register local model configurations
    registry.register_config(
        "local_llama",
        LLMConfig(
            provider=LLMProvider.LOCAL,
            model_name="llama-7b",
            base_url="/path/to/local/model",
            max_tokens=1000,
            temperature=0.7,
        ),
    )

    # Set default provider
    registry.set_default_provider(LLMProvider.OPENAI)

    return registry


# Testing and demonstration
if __name__ == "__main__":

    async def test_llm_registry():
        """Test the LLM registry with multiple providers."""
        registry = setup_example_registry()

        print(" LLM Registry Test")
        print("=" * 50)

        # Show registry stats
        stats = registry.get_registry_stats()
        print(" Registry Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print(f"\n Available configs: {registry.list_configs()}")

        # Test with local provider (always available)
        try:
            print("\n Testing local provider...")
            response = await registry.generate_completion(
                "What is the capital of France?", "local_llama"
            )
            print(f"[OK] Response: {response.content}")
            print(f"[OK] Tokens used: {response.tokens_used}")
            print(f"[OK] Cost: ${response.cost_usd:.4f}")
            print(f"[OK] Response time: {response.response_time:.2f}s")

        except Exception as e:
            print(f"[ERROR] Local provider test failed: {e}")

        # Test configuration listing
        print("\n Testing configuration management...")
        config = registry.get_config("local_llama")
        if config:
            print(
                f"[OK] Retrieved config: {config.model_name} ({config.provider.value})"
            )

        print("\n LLM Registry test complete!")

    asyncio.run(test_llm_registry())
