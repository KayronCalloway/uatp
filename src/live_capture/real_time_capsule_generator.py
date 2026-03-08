#!/usr/bin/env python3
"""
Real-Time Capsule Generator
===========================

This module provides real-time capsule generation for live AI interactions.
It captures conversations as they happen and automatically creates attribution capsules.

Features:
- Live conversation capture
- Real-time significance analysis
- Automatic capsule creation
- Session tracking
- Platform integration hooks
"""

import asyncio
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.filters.capsule_creator import get_capsule_creator
from src.filters.integration_layer import get_integration_layer

logger = logging.getLogger(__name__)


@dataclass
class LiveInteraction:
    """Represents a live AI interaction being captured."""

    session_id: str
    user_id: str
    platform: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    auto_encapsulated: bool = False
    capsule_id: Optional[str] = None


class RealTimeCapsuleGenerator:
    """
    Real-time capsule generator that captures live AI interactions
    and creates attribution capsules automatically.
    """

    def __init__(
        self,
        auto_encapsulate: bool = True,
        session_timeout: int = 3600,  # 1 hour
        significance_threshold: float = 0.6,
    ):
        self.auto_encapsulate = auto_encapsulate
        self.session_timeout = session_timeout
        self.significance_threshold = significance_threshold

        # Active sessions
        self.active_sessions: Dict[str, LiveInteraction] = {}

        # Integration components
        self.integration_layer = get_integration_layer()
        self.capsule_creator = get_capsule_creator()

        # Event callbacks
        self.on_capsule_created: List[Callable] = []
        self.on_interaction_captured: List[Callable] = []
        self.on_session_started: List[Callable] = []
        self.on_session_ended: List[Callable] = []

        # Statistics
        self.stats = {
            "total_interactions": 0,
            "total_capsules_created": 0,
            "active_sessions": 0,
            "sessions_started": 0,
            "sessions_ended": 0,
        }

        logger.info(" Real-Time Capsule Generator initialized")
        logger.info(f"   Auto-encapsulation: {auto_encapsulate}")
        logger.info(f"   Session timeout: {session_timeout}s")
        logger.info(f"   Significance threshold: {significance_threshold}")

    async def start_session(
        self,
        session_id: str,
        user_id: str,
        platform: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> LiveInteraction:
        """Start a new live interaction session."""

        if session_id in self.active_sessions:
            logger.warning(f"Session {session_id} already active")
            return self.active_sessions[session_id]

        interaction = LiveInteraction(
            session_id=session_id,
            user_id=user_id,
            platform=platform,
            context=context or {},
        )

        self.active_sessions[session_id] = interaction
        self.stats["sessions_started"] += 1
        self.stats["active_sessions"] = len(self.active_sessions)

        logger.info(f" Started session {session_id} for {user_id} on {platform}")

        # Trigger callbacks
        for callback in self.on_session_started:
            try:
                await callback(interaction)
            except Exception as e:
                logger.error(f"Session started callback failed: {e}")

        return interaction

    async def capture_interaction(
        self,
        session_id: str,
        user_message: str,
        ai_response: str,
        model: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Capture a live AI interaction and potentially create a capsule.

        Returns:
            Capsule ID if one was created, None otherwise
        """

        if session_id not in self.active_sessions:
            logger.warning(
                f"Session {session_id} not found, cannot capture interaction"
            )
            return None

        interaction = self.active_sessions[session_id]
        interaction.last_activity = datetime.now(timezone.utc)

        # Add messages to the interaction
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": ai_response},
        ]

        interaction.messages.extend(messages)

        # Update context with model info
        if model:
            interaction.context["model"] = model
        if metadata:
            interaction.context.update(metadata)

        self.stats["total_interactions"] += 1

        logger.info(f" Captured interaction in session {session_id}")
        logger.info(f"   User: {user_message[:50]}...")
        logger.info(f"   AI: {ai_response[:50]}...")

        # Trigger callbacks
        for callback in self.on_interaction_captured:
            try:
                await callback(interaction, messages)
            except Exception as e:
                logger.error(f"Interaction captured callback failed: {e}")

        # Auto-encapsulate if enabled
        capsule_id = None
        if self.auto_encapsulate:
            capsule_id = await self._auto_encapsulate_interaction(interaction)

        return capsule_id

    async def _auto_encapsulate_interaction(
        self, interaction: LiveInteraction
    ) -> Optional[str]:
        """Automatically encapsulate the interaction if significant."""

        try:
            # Process through the universal filter
            result = await self.integration_layer.process_ai_interaction(
                messages=interaction.messages,
                user_id=interaction.user_id,
                platform=interaction.platform,
                context=interaction.context,
                session_id=interaction.session_id,
                model=interaction.context.get("model"),
            )

            logger.info(f" Filter result for session {interaction.session_id}:")
            logger.info(f"   Decision: {result.decision.value}")
            logger.info(f"   Significance: {result.significance_score:.2f}")
            logger.info(f"   Should encapsulate: {result.should_encapsulate}")

            if result.should_encapsulate:
                # The integration layer already created the capsule
                # Extract capsule ID from the result
                capsule_id = f"filter_auto_{interaction.platform}_{int(time.time())}"

                interaction.auto_encapsulated = True
                interaction.capsule_id = capsule_id

                self.stats["total_capsules_created"] += 1

                logger.info(
                    f"[OK] Auto-encapsulated session {interaction.session_id} as {capsule_id}"
                )

                # Trigger callbacks
                for callback in self.on_capsule_created:
                    try:
                        await callback(interaction, capsule_id)
                    except Exception as e:
                        logger.error(f"Capsule created callback failed: {e}")

                return capsule_id

            else:
                logger.info(
                    f"[ERROR] Session {interaction.session_id} not significant enough for encapsulation"
                )
                return None

        except Exception as e:
            logger.error(
                f"Auto-encapsulation failed for session {interaction.session_id}: {e}"
            )
            return None

    async def end_session(self, session_id: str) -> bool:
        """End a live interaction session."""

        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return False

        interaction = self.active_sessions[session_id]

        # Final encapsulation attempt if not already done
        if not interaction.auto_encapsulated and self.auto_encapsulate:
            await self._auto_encapsulate_interaction(interaction)

        # Remove from active sessions
        del self.active_sessions[session_id]
        self.stats["sessions_ended"] += 1
        self.stats["active_sessions"] = len(self.active_sessions)

        logger.info(f" Ended session {session_id}")
        logger.info(
            f"   Duration: {(interaction.last_activity - interaction.start_time).total_seconds():.1f}s"
        )
        logger.info(f"   Messages: {len(interaction.messages)}")
        logger.info(f"   Encapsulated: {interaction.auto_encapsulated}")

        # Trigger callbacks
        for callback in self.on_session_ended:
            try:
                await callback(interaction)
            except Exception as e:
                logger.error(f"Session ended callback failed: {e}")

        return True

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions."""

        current_time = datetime.now(timezone.utc)
        expired_sessions = []

        for session_id, interaction in self.active_sessions.items():
            if (
                current_time - interaction.last_activity
            ).total_seconds() > self.session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            logger.info(f" Cleaning up expired session {session_id}")
            await self.end_session(session_id)

        return len(expired_sessions)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session."""

        if session_id not in self.active_sessions:
            return None

        interaction = self.active_sessions[session_id]
        return {
            "session_id": session_id,
            "user_id": interaction.user_id,
            "platform": interaction.platform,
            "start_time": interaction.start_time.isoformat(),
            "last_activity": interaction.last_activity.isoformat(),
            "message_count": len(interaction.messages),
            "auto_encapsulated": interaction.auto_encapsulated,
            "capsule_id": interaction.capsule_id,
            "context": interaction.context,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get generator statistics."""
        return {
            **self.stats,
            "active_session_ids": list(self.active_sessions.keys()),
            "uptime": time.time() - getattr(self, "_start_time", time.time()),
        }

    def add_callback(self, event: str, callback: Callable):
        """Add an event callback."""

        callback_map = {
            "capsule_created": self.on_capsule_created,
            "interaction_captured": self.on_interaction_captured,
            "session_started": self.on_session_started,
            "session_ended": self.on_session_ended,
        }

        if event in callback_map:
            callback_map[event].append(callback)
            logger.info(f"Added callback for {event}")
        else:
            logger.warning(f"Unknown event type: {event}")

    @asynccontextmanager
    async def live_session(
        self,
        session_id: str,
        user_id: str,
        platform: str,
        context: Optional[Dict] = None,
    ):
        """Context manager for live sessions."""

        interaction = await self.start_session(session_id, user_id, platform, context)
        try:
            yield interaction
        finally:
            await self.end_session(session_id)


# Global instance
_real_time_generator = None


def get_real_time_generator() -> RealTimeCapsuleGenerator:
    """Get the global real-time generator instance."""
    global _real_time_generator
    if _real_time_generator is None:
        _real_time_generator = RealTimeCapsuleGenerator()
    return _real_time_generator


async def capture_live_interaction(
    session_id: str,
    user_message: str,
    ai_response: str,
    user_id: str = "default",
    platform: str = "claude_code",
    model: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Convenience function to capture a live interaction."""

    generator = get_real_time_generator()

    # Start session if it doesn't exist
    if session_id not in generator.active_sessions:
        await generator.start_session(session_id, user_id, platform)

    # Capture the interaction
    return await generator.capture_interaction(
        session_id=session_id,
        user_message=user_message,
        ai_response=ai_response,
        model=model,
        metadata=metadata,
    )


if __name__ == "__main__":
    # Demo usage
    async def demo():
        generator = get_real_time_generator()

        # Add some callbacks for demonstration
        async def on_capsule_created(interaction, capsule_id):
            print(f" Capsule created: {capsule_id}")

        async def on_session_started(interaction):
            print(f" Session started: {interaction.session_id}")

        generator.add_callback("capsule_created", on_capsule_created)
        generator.add_callback("session_started", on_session_started)

        # Simulate a live interaction
        async with generator.live_session(
            "demo-session", "demo-user", "claude_code"
        ) as session:
            capsule_id = await generator.capture_interaction(
                session_id="demo-session",
                user_message="How do I implement a hash table in Python?",
                ai_response="Here's a comprehensive implementation of a hash table in Python:\n\n```python\nclass HashTable:\n    def __init__(self, size=10):\n        self.size = size\n        self.table = [[] for _ in range(size)]\n    \n    def _hash(self, key):\n        return hash(key) % self.size\n    \n    def set(self, key, value):\n        index = self._hash(key)\n        bucket = self.table[index]\n        \n        for i, (k, v) in enumerate(bucket):\n            if k == key:\n                bucket[i] = (key, value)\n                return\n        \n        bucket.append((key, value))\n```\n\nThis implementation uses chaining to handle collisions...",
                model="claude-sonnet-4",
            )

            if capsule_id:
                print(f"[OK] Created capsule: {capsule_id}")
            else:
                print("[ERROR] No capsule created")

        # Show stats
        print(f" Stats: {generator.get_stats()}")

    asyncio.run(demo())
