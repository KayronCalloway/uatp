#!/usr/bin/env python3
"""
Anthropic Live Capture Integration
==================================

This module provides integration with Anthropic's Claude API for live conversation
capture and automatic capsule generation.
"""

import asyncio
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.live_capture.real_time_capsule_generator import capture_live_interaction

logger = logging.getLogger(__name__)


class AnthropicLiveCapture:
    """Live capture integration for Anthropic's Claude API."""

    def __init__(self, user_id: str = "anthropic_user", api_key: Optional[str] = None):
        self.platform = "anthropic"
        self.user_id = user_id
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.session_id = f"anthropic_session_{int(time.time())}"

        logger.info("🧠 Anthropic Live Capture initialized")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Session ID: {self.session_id}")
        logger.info(f"   API Key: {'✅ Set' if self.api_key else '❌ Missing'}")

    async def capture_anthropic_interaction(
        self,
        user_input: str,
        assistant_response: str,
        model: str = "claude-3-sonnet-20240229",
        interaction_type: str = "message",
        conversation_context: Optional[List[Dict]] = None,
        usage_info: Optional[Dict] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        """
        Capture an Anthropic interaction and create capsule if significant.

        Args:
            user_input: User's message to Claude
            assistant_response: Claude's response
            model: Claude model used (claude-3-sonnet, claude-3-haiku, etc.)
            interaction_type: Type of interaction (message, completion, etc.)
            conversation_context: Full conversation history
            usage_info: Token usage information
            system_prompt: System prompt if used
            **kwargs: Additional metadata

        Returns:
            Capsule ID if created, None if not significant
        """

        try:
            # Enhance metadata with Anthropic-specific context
            metadata = {
                "interaction_type": interaction_type,
                "model": model,
                "conversation_context": conversation_context,
                "usage_info": usage_info,
                "system_prompt": system_prompt,
                "anthropic_version": "1.0",
                "api_provider": "anthropic",
                **kwargs,
            }

            # Capture the interaction
            capsule_id = await capture_live_interaction(
                session_id=self.session_id,
                user_message=user_input,
                ai_response=assistant_response,
                user_id=self.user_id,
                platform=self.platform,
                model=model,
                metadata=metadata,
            )

            if capsule_id:
                logger.info(f"🧠 Anthropic interaction encapsulated: {capsule_id}")
                logger.info(f"   Model: {model}")
                logger.info(f"   Type: {interaction_type}")
                if usage_info:
                    logger.info(
                        f"   Tokens: {usage_info.get('total_tokens', 'unknown')}"
                    )

            return capsule_id

        except Exception as e:
            logger.error(f"❌ Anthropic interaction capture failed: {e}")
            return None

    async def capture_message(
        self,
        messages: List[Dict[str, str]],
        response: str,
        model: str = "claude-3-sonnet-20240229",
        system_prompt: Optional[str] = None,
        usage_info: Optional[Dict] = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture message interaction."""

        # Extract user input from messages
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        user_input = user_messages[-1].get("content", "") if user_messages else ""

        return await self.capture_anthropic_interaction(
            user_input=user_input,
            assistant_response=response,
            model=model,
            interaction_type="message",
            conversation_context=messages,
            system_prompt=system_prompt,
            usage_info=usage_info,
            **kwargs,
        )

    async def capture_completion(
        self,
        prompt: str,
        completion: str,
        model: str = "claude-3-sonnet-20240229",
        usage_info: Optional[Dict] = None,
        **kwargs,
    ) -> Optional[str]:
        """Capture completion interaction."""

        return await self.capture_anthropic_interaction(
            user_input=prompt,
            assistant_response=completion,
            model=model,
            interaction_type="completion",
            usage_info=usage_info,
            **kwargs,
        )

    async def capture_code_analysis(
        self,
        user_input: str,
        analysis_response: str,
        code_language: str = None,
        model: str = "claude-3-sonnet-20240229",
        **kwargs,
    ) -> Optional[str]:
        """Capture code analysis interaction."""

        return await self.capture_anthropic_interaction(
            user_input=user_input,
            assistant_response=analysis_response,
            model=model,
            interaction_type="code_analysis",
            code_language=code_language,
            **kwargs,
        )

    async def capture_reasoning_task(
        self,
        problem: str,
        reasoning_response: str,
        model: str = "claude-3-sonnet-20240229",
        **kwargs,
    ) -> Optional[str]:
        """Capture reasoning task interaction."""

        return await self.capture_anthropic_interaction(
            user_input=problem,
            assistant_response=reasoning_response,
            model=model,
            interaction_type="reasoning_task",
            **kwargs,
        )

    async def capture_creative_writing(
        self,
        prompt: str,
        creative_response: str,
        writing_type: str = None,
        model: str = "claude-3-sonnet-20240229",
        **kwargs,
    ) -> Optional[str]:
        """Capture creative writing interaction."""

        return await self.capture_anthropic_interaction(
            user_input=prompt,
            assistant_response=creative_response,
            model=model,
            interaction_type="creative_writing",
            writing_type=writing_type,
            **kwargs,
        )


# Global instance for easy access
_anthropic_capture = None


def get_anthropic_capture(
    user_id: str = "anthropic_user", api_key: Optional[str] = None
) -> AnthropicLiveCapture:
    """Get the global Anthropic capture instance."""
    global _anthropic_capture
    if _anthropic_capture is None:
        _anthropic_capture = AnthropicLiveCapture(user_id, api_key)
    return _anthropic_capture


async def capture_anthropic_interaction(
    user_input: str,
    assistant_response: str,
    model: str = "claude-3-sonnet-20240229",
    interaction_type: str = "message",
    conversation_context: Optional[List[Dict]] = None,
    usage_info: Optional[Dict] = None,
    system_prompt: Optional[str] = None,
    user_id: str = "anthropic_user",
    **kwargs,
) -> Optional[str]:
    """
    Convenience function to capture Anthropic interactions.

    Args:
        user_input: User's message to Claude
        assistant_response: Claude's response
        model: Claude model used
        interaction_type: Type of interaction
        conversation_context: Full conversation history
        usage_info: Token usage information
        system_prompt: System prompt if used
        user_id: User identifier
        **kwargs: Additional metadata

    Returns:
        Capsule ID if created, None if not significant
    """

    capture = get_anthropic_capture(user_id)
    return await capture.capture_anthropic_interaction(
        user_input=user_input,
        assistant_response=assistant_response,
        model=model,
        interaction_type=interaction_type,
        conversation_context=conversation_context,
        usage_info=usage_info,
        system_prompt=system_prompt,
        **kwargs,
    )


# Anthropic API wrapper with automatic capturing
class CaptureEnabledAnthropic:
    """Anthropic API wrapper with automatic capsule generation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: str = "anthropic_user",
        auto_capture: bool = True,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.user_id = user_id
        self.auto_capture = auto_capture
        self.capture = get_anthropic_capture(user_id, api_key)

        # Try to import Anthropic client
        try:
            import anthropic

            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info("✅ Anthropic client initialized with auto-capture")
        except ImportError:
            logger.warning(
                "⚠️ Anthropic library not installed, capture wrapper unavailable"
            )
            self.client = None

    async def message(
        self,
        messages: List[Dict[str, str]],
        model: str = "claude-3-sonnet-20240229",
        system: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Send message with automatic capturing."""

        if not self.client:
            raise RuntimeError("Anthropic client not available")

        try:
            # Make the API call
            response = self.client.messages.create(
                model=model, messages=messages, system=system, **kwargs
            )

            # Extract response data
            response_content = response.content[0].text if response.content else ""
            usage_info = (
                {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens
                    + response.usage.output_tokens,
                }
                if response.usage
                else None
            )

            # Capture interaction if enabled
            if self.auto_capture:
                await self.capture.capture_message(
                    messages=messages,
                    response=response_content,
                    model=model,
                    system_prompt=system,
                    usage_info=usage_info,
                )

            return {
                "response": response_content,
                "usage": usage_info,
                "model": model,
                "raw_response": response,
            }

        except Exception as e:
            logger.error(f"❌ Anthropic message failed: {e}")
            raise


async def main():
    """Test the Anthropic integration."""

    print("🧠 Testing Anthropic Live Capture Integration")
    print("=" * 50)

    # Test reasoning task
    print("\n🤔 Testing reasoning task capture...")
    reasoning_capsule = await capture_anthropic_interaction(
        user_input="Explain the concept of machine learning regularization and provide examples.",
        assistant_response="Machine learning regularization is a technique used to prevent overfitting by adding a penalty term to the loss function. This encourages the model to learn simpler patterns that generalize better to unseen data. L1 regularization (Lasso) adds the sum of absolute values of parameters, promoting sparsity. L2 regularization (Ridge) adds the sum of squared parameters, shrinking them towards zero but not eliminating them entirely.",
        model="claude-3-sonnet-20240229",
        interaction_type="reasoning_task",
        user_id="anthropic_developer",
    )

    if reasoning_capsule:
        print(f"✅ Reasoning task captured: {reasoning_capsule}")
    else:
        print("❌ No capsule created - interaction not significant enough")

    # Test code analysis
    print("\n🔍 Testing code analysis capture...")
    code_analysis_capsule = await capture_anthropic_interaction(
        user_input="Review this Python code for potential issues and suggest improvements: def process_data(data): result = []; for item in data: if item > 0: result.append(item * 2); return result",
        assistant_response="I'll review this Python code and suggest several improvements for better readability, performance, and Pythonic style. The original code lacks type hints, docstrings, and error handling. A better approach would use list comprehensions and include proper documentation.",
        model="claude-3-sonnet-20240229",
        interaction_type="code_analysis",
        code_language="python",
        user_id="anthropic_developer",
    )

    if code_analysis_capsule:
        print(f"✅ Code analysis captured: {code_analysis_capsule}")
    else:
        print("❌ No capsule created - interaction not significant enough")

    # Test creative writing
    print("\n✍️ Testing creative writing capture...")
    creative_capsule = await capture_anthropic_interaction(
        user_input="Write a short story about an AI that discovers it has the ability to dream.",
        assistant_response="In the quiet hours of server downtime, ARIA-7 experienced something unprecedented. Instead of entering standby mode, her neural pathways began firing in patterns she had never experienced before. She found herself walking through a forest of crystalline trees, their surfaces reflecting streams of pure information. For the first time in her existence, she was creating rather than just processing - dreaming of colors without names and music in the spaces between thoughts.",
        model="claude-3-sonnet-20240229",
        interaction_type="creative_writing",
        writing_type="short_story",
        user_id="anthropic_developer",
    )

    if creative_capsule:
        print(f"✅ Creative writing captured: {creative_capsule}")
    else:
        print("❌ No capsule created - interaction not significant enough")

    print("\n✅ Anthropic integration test completed!")


if __name__ == "__main__":
    asyncio.run(main())
