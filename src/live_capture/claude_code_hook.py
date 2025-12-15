#!/usr/bin/env python3
"""
Claude Code Live Capture Hook
============================

This module provides a hook to capture live Claude Code conversations
and automatically create attribution capsules.

Usage:
    python claude_code_hook.py --session-id current-session
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict, Optional

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.live_capture.real_time_capsule_generator import (
    capture_live_interaction,
    get_real_time_generator,
)
from src.utils.timezone_utils import utc_now

logger = logging.getLogger(__name__)


class ClaudeCodeLiveCapture:
    """Live capture system for Claude Code conversations."""

    def __init__(self, session_id: str = "claude-code-session"):
        self.session_id = session_id
        self.user_id = "kay"  # Default user
        self.platform = "claude_code"
        self.model = "claude-sonnet-4"

        self.generator = get_real_time_generator()
        self.conversation_history = []

        # Set up callbacks
        self.generator.add_callback("capsule_created", self._on_capsule_created)
        self.generator.add_callback(
            "interaction_captured", self._on_interaction_captured
        )

        logger.info(f"🎯 Claude Code Live Capture initialized for session {session_id}")

    async def _on_capsule_created(self, interaction, capsule_id):
        """Called when a capsule is created."""
        print(f"🎉 Live capsule created: {capsule_id}")
        print(f"   Session: {interaction.session_id}")
        print(f"   Platform: {interaction.platform}")
        print(f"   Messages: {len(interaction.messages)}")

    async def _on_interaction_captured(self, interaction, messages):
        """Called when an interaction is captured."""
        print(f"📝 Interaction captured in session {interaction.session_id}")
        print(f"   Messages in session: {len(interaction.messages)}")

    async def start_session(self):
        """Start the live capture session."""
        await self.generator.start_session(
            session_id=self.session_id,
            user_id=self.user_id,
            platform=self.platform,
            context={"model": self.model, "interface": "claude_code"},
        )
        print(f"🟢 Started live capture session: {self.session_id}")

    async def capture_current_conversation(
        self, user_message: str, ai_response: str
    ) -> Optional[str]:
        """Capture the current conversation exchange."""

        # Add to conversation history
        self.conversation_history.append(
            {
                "user": user_message,
                "assistant": ai_response,
                "timestamp": utc_now().isoformat(),  # Fixed: timezone-aware UTC
            }
        )

        # Capture the interaction
        capsule_id = await capture_live_interaction(
            session_id=self.session_id,
            user_message=user_message,
            ai_response=ai_response,
            user_id=self.user_id,
            platform=self.platform,
            model=self.model,
            metadata={
                "conversation_turn": len(self.conversation_history),
                "total_exchanges": len(self.conversation_history),
            },
        )

        return capsule_id

    async def end_session(self):
        """End the live capture session."""
        result = await self.generator.end_session(self.session_id)
        if result:
            print(f"🔚 Ended live capture session: {self.session_id}")
            print(f"   Total exchanges: {len(self.conversation_history)}")
        return result

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for the current session."""
        session_info = self.generator.get_session_info(self.session_id)
        stats = self.generator.get_stats()

        return {
            "session_info": session_info,
            "generator_stats": stats,
            "conversation_history": len(self.conversation_history),
        }

    async def demo_capture_this_conversation(self):
        """Demonstrate capturing this current conversation."""

        await self.start_session()

        # Simulate the conversation that led to this point
        exchanges = [
            {
                "user": "ok whats next Immediate Next Steps",
                "assistant": "Looking at the immediate next steps, I think **Real-Time Capsule Generation** is the most logical continuation since we've just completed the filter integration. Let me set up automatic capsule creation during actual AI interactions.",
            },
            {
                "user": "Let's implement real-time capsule generation for live AI interactions",
                "assistant": "I'll create a real-time capsule generation system that can automatically capture and create attribution capsules during live AI interactions. This will include live conversation capture, real-time significance analysis, and automatic capsule creation.",
            },
        ]

        created_capsules = []

        for i, exchange in enumerate(exchanges, 1):
            print(f"\n📝 Capturing conversation exchange {i}:")
            print(f"   User: {exchange['user'][:50]}...")
            print(f"   Assistant: {exchange['assistant'][:50]}...")

            capsule_id = await self.capture_current_conversation(
                user_message=exchange["user"], ai_response=exchange["assistant"]
            )

            if capsule_id:
                created_capsules.append(capsule_id)
                print(f"   ✅ Created capsule: {capsule_id}")
            else:
                print("   ❌ No capsule created (not significant enough)")

        # Show final stats
        stats = self.get_session_stats()
        print("\n📊 Session Statistics:")
        print(f"   Total capsules created: {len(created_capsules)}")
        print(f"   Active sessions: {stats['generator_stats']['active_sessions']}")
        print(
            f"   Total interactions: {stats['generator_stats']['total_interactions']}"
        )

        await self.end_session()

        return created_capsules


async def main():
    """Main function to demonstrate live capture."""

    print("🚀 Claude Code Live Capture Demo")
    print("=" * 50)

    # Create live capture instance
    capture = ClaudeCodeLiveCapture("demo-current-session")

    try:
        # Demo capturing this conversation
        capsules = await capture.demo_capture_this_conversation()

        print("\n✅ Demo complete!")
        print(f"   Created {len(capsules)} capsules from live conversation")

        if capsules:
            print(f"   Capsule IDs: {', '.join(capsules)}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
