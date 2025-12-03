"""
Integration Layer for Universal Filter
======================================

This module provides integration points for all AI platforms to connect
to the universal filter system.

Supported Platforms:
- OpenAI (GPT-4, GPT-3.5, etc.)
- Anthropic (Claude)
- Claude Code
- Windsurf IDE
- Cursor
- Any custom AI platform

Usage:
    from filters.integration_layer import process_ai_interaction
    
    result = await process_ai_interaction(
        messages=conversation_messages,
        user_id="kay",
        platform="openai",
        context={"model": "gpt-4"}
    )
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.filters.universal_filter import (
    get_universal_filter,
    FilterResult,
    FilterDecision,
)
from src.filters.capsule_creator import get_capsule_creator

# from src.engine.capsule_engine import CapsuleEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AIInteraction:
    """Standardized AI interaction format."""

    messages: List[Dict[str, Any]]
    user_id: str
    platform: str
    context: Dict[str, Any]
    timestamp: datetime
    session_id: Optional[str] = None
    model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "messages": self.messages,
            "user_id": self.user_id,
            "platform": self.platform,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "model": self.model,
        }


class IntegrationLayer:
    """Integration layer that connects all AI platforms to the universal filter."""

    def __init__(self):
        self.universal_filter = get_universal_filter()
        self.capsule_creator = get_capsule_creator()
        self.active_sessions: Dict[str, List[AIInteraction]] = {}

        # Set up filter callbacks
        self.universal_filter.add_callback(
            FilterDecision.ENCAPSULATE, self._handle_encapsulation
        )
        self.universal_filter.add_callback(FilterDecision.REVIEW, self._handle_review)

        logger.info("🔗 Integration layer initialized")

    async def process_ai_interaction(
        self,
        messages: List[Dict[str, Any]],
        user_id: str,
        platform: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> FilterResult:
        """
        Process an AI interaction through the universal filter.

        Args:
            messages: List of conversation messages
            user_id: User identifier
            platform: Platform name (openai, claude, etc.)
            context: Additional context information
            session_id: Session identifier
            model: AI model used

        Returns:
            FilterResult with decision and metadata
        """

        # Create standardized interaction
        interaction = AIInteraction(
            messages=messages,
            user_id=user_id,
            platform=platform,
            context=context or {},
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            model=model,
        )

        # Add to active sessions
        if session_id:
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = []
            self.active_sessions[session_id].append(interaction)

        # Process through universal filter
        interaction_data = {
            "messages": messages,
            "context": {
                **interaction.context,
                "session_id": session_id,
                "model": model,
                "timestamp": interaction.timestamp.isoformat(),
            },
        }

        result = await self.universal_filter.process_interaction(
            interaction_data=interaction_data, user_id=user_id, platform=platform
        )

        # Log the interaction
        await self._log_interaction(interaction, result)

        return result

    async def _handle_encapsulation(
        self, result: FilterResult, interaction_data: Dict[str, Any]
    ):
        """Handle encapsulation decision by creating a capsule."""

        try:
            # Extract data for capsule creation
            messages = interaction_data.get("messages", [])
            context = interaction_data.get("context", {})

            # Get user and platform info
            user_id = result.metadata.get("user_id", "unknown")
            platform = result.metadata.get("platform", "unknown")
            session_id = context.get("session_id")

            # Create the capsule
            capsule_data = await self.capsule_creator.create_capsule_from_filter_result(
                filter_result=result.to_dict(),
                messages=messages,
                user_id=user_id,
                platform=platform,
                session_id=session_id,
            )

            logger.info(f"✅ Successfully created capsule: {capsule_data['capsule_id']}")

        except Exception as e:
            logger.error(f"❌ Error creating capsule: {e}")

    async def _handle_review(
        self, result: FilterResult, interaction_data: Dict[str, Any]
    ):
        """Handle review decision by queuing for manual review."""

        # In a production system, this would queue for human review
        logger.info(
            f"👁️ Interaction queued for review - Score: {result.significance_score:.2f}"
        )

        # For now, just log the details
        messages = interaction_data.get("messages", [])
        if messages:
            preview = messages[0].get("content", "")[:100] + "..."
            logger.info(f"   Preview: {preview}")

    async def _log_interaction(self, interaction: AIInteraction, result: FilterResult):
        """Log the interaction and filter result."""

        log_entry = {
            "timestamp": interaction.timestamp.isoformat(),
            "user_id": interaction.user_id,
            "platform": interaction.platform,
            "session_id": interaction.session_id,
            "model": interaction.model,
            "message_count": len(interaction.messages),
            "decision": result.decision.value,
            "significance_score": result.significance_score,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
        }

        # In production, this would go to a proper logging system
        logger.debug(f"📊 Interaction logged: {json.dumps(log_entry, indent=2)}")

    def _format_conversation_content(
        self, messages: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> str:
        """Format conversation content for capsule."""

        if not messages:
            return "Empty conversation"

        # Get the main topic from first user message
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if user_messages:
            first_msg = user_messages[0].get("content", "")
            platform = context.get("platform", "AI")

            # Create a concise summary
            if len(first_msg) > 150:
                summary = first_msg[:150] + "..."
            else:
                summary = first_msg

            return f"{platform.title()} interaction: {summary}"

        return f"AI conversation on {context.get('platform', 'unknown platform')}"

    def get_session_history(self, session_id: str) -> List[AIInteraction]:
        """Get interaction history for a session."""
        return self.active_sessions.get(session_id, [])

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions."""

        cutoff_time = datetime.now(timezone.utc)
        cutoff_time = cutoff_time.replace(hour=cutoff_time.hour - max_age_hours)

        expired_sessions = []
        for session_id, interactions in self.active_sessions.items():
            if interactions and interactions[-1].timestamp < cutoff_time:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.active_sessions[session_id]

        if expired_sessions:
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")


# Global integration layer instance
_integration_layer = None


def get_integration_layer() -> IntegrationLayer:
    """Get the global integration layer instance."""
    global _integration_layer
    if _integration_layer is None:
        _integration_layer = IntegrationLayer()
    return _integration_layer


# Convenience functions for different platforms
async def process_ai_interaction(
    messages: List[Dict[str, Any]],
    user_id: str,
    platform: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    model: Optional[str] = None,
) -> FilterResult:
    """Process any AI interaction through the universal filter."""

    integration_layer = get_integration_layer()
    return await integration_layer.process_ai_interaction(
        messages=messages,
        user_id=user_id,
        platform=platform,
        context=context,
        session_id=session_id,
        model=model,
    )


async def process_openai_interaction(
    messages: List[Dict[str, Any]],
    user_id: str,
    model: str = "gpt-4",
    session_id: Optional[str] = None,
) -> FilterResult:
    """Process OpenAI interaction through the filter."""

    return await process_ai_interaction(
        messages=messages,
        user_id=user_id,
        platform="openai",
        context={"model": model, "provider": "openai"},
        session_id=session_id,
        model=model,
    )


async def process_claude_interaction(
    messages: List[Dict[str, Any]],
    user_id: str,
    model: str = "claude-3",
    session_id: Optional[str] = None,
) -> FilterResult:
    """Process Claude interaction through the filter."""

    return await process_ai_interaction(
        messages=messages,
        user_id=user_id,
        platform="claude",
        context={"model": model, "provider": "anthropic"},
        session_id=session_id,
        model=model,
    )


async def process_claude_code_interaction(
    messages: List[Dict[str, Any]], user_id: str, session_id: Optional[str] = None
) -> FilterResult:
    """Process Claude Code interaction through the filter."""

    return await process_ai_interaction(
        messages=messages,
        user_id=user_id,
        platform="claude_code",
        context={"provider": "anthropic", "interface": "claude_code"},
        session_id=session_id,
        model="claude-sonnet-4",
    )


# Auto-capture decorator
def auto_capture(platform: str, user_id: str = "default"):
    """Decorator to automatically capture AI interactions."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Execute the original function
            result = await func(*args, **kwargs)

            # Try to extract messages from the result
            messages = []
            if hasattr(result, "messages"):
                messages = result.messages
            elif isinstance(result, dict) and "messages" in result:
                messages = result["messages"]

            # Process through filter if we have messages
            if messages:
                await process_ai_interaction(
                    messages=messages,
                    user_id=user_id,
                    platform=platform,
                    context={"auto_captured": True},
                )

            return result

        return wrapper

    return decorator
