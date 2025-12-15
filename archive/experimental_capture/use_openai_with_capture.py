#!/usr/bin/env python3
"""
Example: Using OpenAI API with Automatic UATP Capture
======================================================

This script shows how to use OpenAI API while automatically capturing
all conversations as UATP capsules.

Every API call you make will be saved to the database automatically.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from src.live_capture.openai_hook import CaptureEnabledOpenAI


async def example_chat():
    """Example: Simple chat with automatic capture."""

    print("=" * 70)
    print("  OpenAI + UATP Auto-Capture Example")
    print("=" * 70)
    print()

    # Initialize the capture-enabled OpenAI client
    # This is a drop-in replacement for the normal OpenAI client
    client = CaptureEnabledOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),  # Your OpenAI API key
        user_id="kay",  # Your user ID
        auto_capture=True,  # Automatically capture all interactions
    )

    print("✅ Capture-enabled OpenAI client initialized")
    print("   Every API call will be saved to UATP database")
    print()

    # Example 1: Simple chat
    print("📝 Example 1: Simple Chat")
    print("-" * 70)

    messages = [
        {
            "role": "user",
            "content": "What are the key principles of test-driven development?",
        }
    ]

    result = await client.chat_completion(messages=messages, model="gpt-4")

    print(f"Response: {result['response'][:200]}...")
    print(f"Tokens used: {result['usage']['total_tokens']}")
    print("✅ Conversation automatically saved to UATP!")
    print()

    # Example 2: Multi-turn conversation
    print("📝 Example 2: Multi-turn Conversation")
    print("-" * 70)

    conversation = [
        {"role": "user", "content": "Explain quantum computing in simple terms"},
    ]

    result = await client.chat_completion(messages=conversation, model="gpt-4")

    # Continue the conversation
    conversation.append({"role": "assistant", "content": result["response"]})
    conversation.append(
        {"role": "user", "content": "How does it differ from classical computing?"}
    )

    result = await client.chat_completion(messages=conversation, model="gpt-4")

    print(f"Response: {result['response'][:200]}...")
    print("✅ Multi-turn conversation automatically saved!")
    print()

    print("=" * 70)
    print("🎯 View your captured conversations at: http://localhost:3000")
    print("=" * 70)


async def example_code_generation():
    """Example: Code generation with capture."""

    print()
    print("📝 Example 3: Code Generation")
    print("-" * 70)

    client = CaptureEnabledOpenAI(user_id="kay", auto_capture=True)

    messages = [
        {
            "role": "user",
            "content": "Write a Python function to validate email addresses using regex",
        }
    ]

    result = await client.chat_completion(messages=messages, model="gpt-4")

    print(f"Generated code (preview): {result['response'][:300]}...")
    print("✅ Code generation automatically captured!")
    print()


async def example_alternative_api():
    """Example: Using the lower-level capture API directly."""

    print()
    print("📝 Example 4: Manual Capture (if you have existing OpenAI code)")
    print("-" * 70)

    from openai import OpenAI

    from src.live_capture.openai_hook import capture_openai_interaction

    # Your existing OpenAI code
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    messages = [{"role": "user", "content": "Hello, how are you?"}]

    response = client.chat.completions.create(model="gpt-4", messages=messages)

    # Manually capture the interaction
    capsule_id = await capture_openai_interaction(
        user_input=messages[0]["content"],
        assistant_response=response.choices[0].message.content,
        model="gpt-4",
        interaction_type="chat_completion",
        conversation_context=messages,
        usage_info={
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
        user_id="kay",
    )

    if capsule_id:
        print(f"✅ Manually captured to capsule: {capsule_id}")
    print()


async def main():
    """Run all examples."""

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print()
        print("To use this:")
        print("1. Add to .env file: OPENAI_API_KEY=sk-...")
        print("2. Or export: export OPENAI_API_KEY=sk-...")
        return

    try:
        await example_chat()
        await example_code_generation()
        await example_alternative_api()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
