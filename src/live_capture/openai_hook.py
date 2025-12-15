#!/usr/bin/env python3
"""
OpenAI Live Capture Integration
===============================

This module provides integration with OpenAI API for live conversation
capture and automatic capsule generation.

Refactored to use BaseHook for reduced duplication.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from src.live_capture.base_hook import BaseHook

logger = logging.getLogger(__name__)


class OpenAILiveCapture(BaseHook):
    """Live capture integration for OpenAI API."""

    def __init__(self, user_id: str = "openai_user", api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        super().__init__(platform="openai", user_id=user_id)

    def get_platform_emoji(self) -> str:
        return "🤖"

    def get_platform_specific_metadata(self, **kwargs) -> Dict[str, Any]:
        """Get OpenAI-specific metadata."""
        return {
            "openai_version": "1.0",
            "api_provider": "openai",
            "conversation_context": kwargs.get("conversation_context"),
            "usage_info": kwargs.get("usage_info"),
        }

    def _log_platform_specific_init(self) -> None:
        """Log OpenAI-specific initialization."""
        logger.info(f"   API Key: {'✅ Set' if self.api_key else '❌ Missing'}")

    def _log_platform_specific_success(self, capsule_id: str, **kwargs) -> None:
        """Log OpenAI-specific success info."""
        usage_info = kwargs.get("usage_info")
        if usage_info:
            logger.info(f"   Tokens: {usage_info.get('total_tokens', 'unknown')}")

    # Convenience methods for OpenAI-specific interactions

    async def capture_openai_interaction(
        self,
        user_input: str,
        assistant_response: str,
        model: str = "gpt-4",
        interaction_type: str = "chat_completion",
        conversation_context: Optional[List[Dict]] = None,
        usage_info: Optional[Dict] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Capture an OpenAI interaction and create capsule if significant.

        Thin wrapper around BaseHook.capture_interaction with OpenAI-specific parameters.
        """
        return await self.capture_interaction(
            user_input=user_input,
            assistant_response=assistant_response,
            model=model,
            interaction_type=interaction_type,
            conversation_context=conversation_context,
            usage_info=usage_info,
            **kwargs,
        )

    async def capture_chat_completion(
        self,
        messages: List[Dict[str, str]],
        response: str,
        model: str = "gpt-4",
        usage_info: Optional[Dict] = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture chat completion interaction."""
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        user_input = user_messages[-1].get("content", "") if user_messages else ""

        return await self.capture_openai_interaction(
            user_input=user_input,
            assistant_response=response,
            model=model,
            interaction_type="chat_completion",
            conversation_context=messages,
            usage_info=usage_info,
            **kwargs,
        )

    async def capture_completion(
        self,
        prompt: str,
        completion: str,
        model: str = "gpt-3.5-turbo-instruct",
        usage_info: Optional[Dict] = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture completion interaction."""
        return await self.capture_openai_interaction(
            user_input=prompt,
            assistant_response=completion,
            model=model,
            interaction_type="completion",
            usage_info=usage_info,
            **kwargs,
        )

    async def capture_code_generation(
        self,
        user_input: str,
        code_response: str,
        language: str = None,
        model: str = "gpt-4",
        **kwargs,
    ) -> Optional[str]:
        """Capture code generation interaction."""
        return await self.capture_openai_interaction(
            user_input=user_input,
            assistant_response=code_response,
            model=model,
            interaction_type="code_generation",
            language=language,
            **kwargs,
        )

    async def capture_embedding_interaction(
        self,
        input_text: str,
        embedding_result: List[float],
        model: str = "text-embedding-ada-002",
        **kwargs,
    ) -> Optional[str]:
        """Capture embedding interaction."""
        response = f"Generated embedding vector with {len(embedding_result)} dimensions using {model}"
        return await self.capture_openai_interaction(
            user_input=input_text,
            assistant_response=response,
            model=model,
            interaction_type="embedding",
            embedding_dimensions=len(embedding_result),
            **kwargs,
        )

    async def capture_function_calling(
        self,
        user_input: str,
        function_calls: List[Dict],
        function_responses: List[Dict],
        final_response: str,
        model: str = "gpt-4",
        **kwargs,
    ) -> Optional[str]:
        """Capture function calling interaction."""
        return await self.capture_openai_interaction(
            user_input=user_input,
            assistant_response=final_response,
            model=model,
            interaction_type="function_calling",
            function_calls=function_calls,
            function_responses=function_responses,
            **kwargs,
        )


# Global instance for easy access
_openai_capture = None


def get_openai_capture(
    user_id: str = "openai_user", api_key: Optional[str] = None
) -> OpenAILiveCapture:
    """Get the global OpenAI capture instance."""
    global _openai_capture
    if _openai_capture is None:
        _openai_capture = OpenAILiveCapture(user_id, api_key)
    return _openai_capture


async def capture_openai_interaction(
    user_input: str,
    assistant_response: str,
    model: str = "gpt-4",
    interaction_type: str = "chat_completion",
    conversation_context: Optional[List[Dict]] = None,
    usage_info: Optional[Dict] = None,
    user_id: str = "openai_user",
    **kwargs,
) -> Optional[str]:
    """
    Convenience function to capture OpenAI interactions.

    Args:
        user_input: User's message to OpenAI
        assistant_response: OpenAI's response
        model: OpenAI model used
        interaction_type: Type of interaction
        conversation_context: Full conversation history
        usage_info: Token usage information
        user_id: User identifier
        **kwargs: Additional metadata

    Returns:
        Capsule ID if created, None if not significant
    """
    capture = get_openai_capture(user_id)
    return await capture.capture_openai_interaction(
        user_input=user_input,
        assistant_response=assistant_response,
        model=model,
        interaction_type=interaction_type,
        conversation_context=conversation_context,
        usage_info=usage_info,
        **kwargs,
    )


# OpenAI API wrapper with automatic capturing
class CaptureEnabledOpenAI:
    """OpenAI API wrapper with automatic capsule generation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: str = "openai_user",
        auto_capture: bool = True,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.user_id = user_id
        self.auto_capture = auto_capture
        self.capture = get_openai_capture(user_id, api_key)

        # Try to import OpenAI client
        try:
            import openai

            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("✅ OpenAI client initialized with auto-capture")
        except ImportError:
            logger.warning(
                "⚠️ OpenAI library not installed, capture wrapper unavailable"
            )
            self.client = None

    async def chat_completion(
        self, messages: List[Dict[str, str]], model: str = "gpt-4", **kwargs
    ) -> Dict[str, Any]:
        """Chat completion with automatic capturing."""
        if not self.client:
            raise RuntimeError("OpenAI client not available")

        try:
            response = self.client.chat.completions.create(
                model=model, messages=messages, **kwargs
            )

            response_content = response.choices[0].message.content
            usage_info = response.usage.dict() if response.usage else None

            if self.auto_capture:
                await self.capture.capture_chat_completion(
                    messages=messages,
                    response=response_content,
                    model=model,
                    usage_info=usage_info,
                )

            return {
                "response": response_content,
                "usage": usage_info,
                "model": model,
                "raw_response": response,
            }

        except Exception as e:
            logger.error(f"❌ OpenAI chat completion failed: {e}")
            raise


async def main():
    """Test the OpenAI integration."""
    print("🤖 Testing OpenAI Live Capture Integration (with BaseHook)")
    print("=" * 50)

    # Test chat completion
    print("\n💬 Testing chat completion capture...")
    messages = [
        {
            "role": "user",
            "content": "Write a Python function to calculate Fibonacci using DP",
        }
    ]

    response = "Here's a Python function for Fibonacci using dynamic programming..."

    usage_info = {"prompt_tokens": 25, "completion_tokens": 350, "total_tokens": 375}

    capsule_id = await capture_openai_interaction(
        user_input=messages[0]["content"],
        assistant_response=response,
        model="gpt-4",
        interaction_type="chat_completion",
        conversation_context=messages,
        usage_info=usage_info,
        user_id="openai_developer",
    )

    if capsule_id:
        print(f"✅ OpenAI interaction captured: {capsule_id}")
    else:
        print("❌ No capsule created")

    print("\n✅ OpenAI integration test completed (with BaseHook refactoring)!")


if __name__ == "__main__":
    asyncio.run(main())
