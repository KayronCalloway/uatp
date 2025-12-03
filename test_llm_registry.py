#!/usr/bin/env python3
import asyncio
import sys

sys.path.append("src")
from src.integrations.llm_registry import LLMConfig, LLMProvider, LLMRegistry


async def test_local_only():
    registry = LLMRegistry()

    # Register only local model (no API key required)
    registry.register_config(
        "local_test",
        LLMConfig(provider=LLMProvider.LOCAL, model_name="test-model", max_tokens=100),
    )

    registry.set_default_provider(LLMProvider.LOCAL)

    print("🤖 LLM Registry Test (Local Only)")
    print("=" * 40)

    # Test local completion
    response = await registry.generate_completion("Hello world!", "local_test")
    print(f"✅ Provider: {response.provider.value}")
    print(f"✅ Model: {response.model}")
    print(f"✅ Response: {response.content}")
    print(f"✅ Tokens: {response.tokens_used}")
    print(f"✅ Cost: ${response.cost_usd:.4f}")
    print(f"✅ Time: {response.response_time:.2f}s")

    # Test registry stats
    stats = registry.get_registry_stats()
    print("\n📊 Registry Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


asyncio.run(test_local_only())
