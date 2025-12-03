"""
Real-time conversation monitoring and capsule generation system.
This module captures live AI interactions and creates attribution capsules.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Import capsule engine
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.engine.capsule_engine import CapsuleEngine
from src.integrations.openai_client import OpenAIClient
from src.reasoning.fixed_analyzer import analyze_conversation_significance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """Context for a live conversation being monitored."""

    session_id: str
    user_id: str
    platform: str  # 'openai', 'anthropic', 'claude_code', etc.
    start_time: datetime
    messages: List[Dict[str, Any]]
    last_activity: datetime
    significance_score: float = 0.0
    capsule_created: bool = (
        False  # Track if capsule created (not "should" - we capture ALL)
    )


class LiveConversationMonitor:
    """Monitors live AI conversations and generates capsules in real-time."""

    def __init__(self, db_manager=None, agent_id: str = "live-monitor"):
        self.agent_id = agent_id
        # Initialize engine with db_manager if provided
        if db_manager:
            self.engine = CapsuleEngine(db_manager=db_manager, agent_id=agent_id)
        else:
            # For testing or standalone use, create a simple mock engine
            self.engine = None
        self.openai_client = OpenAIClient()
        self.active_conversations: Dict[str, ConversationContext] = {}
        # UNIVERSAL CAPTURE: No threshold - capture ALL interactions
        # Significance is used as economic WEIGHT, not a gate
        # See: UNIVERSAL_CAPTURE_PHILOSOPHY.md
        self.significance_threshold = 0.0  # Capture everything (was 0.6 - elitist)
        self.capture_all = True  # Democratic capture principle

        # Load API keys
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_key:
            logger.warning("OpenAI API key not found - OpenAI monitoring disabled")

    async def start_monitoring(self):
        """Start the live monitoring system."""
        logger.info("🚀 Starting live conversation monitoring...")

        # Start background tasks
        tasks = [
            asyncio.create_task(self.monitor_conversations()),
            asyncio.create_task(self.process_capsule_queue()),
            asyncio.create_task(self.cleanup_expired_conversations()),
        ]

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")

    async def monitor_conversations(self):
        """Monitor active conversations for significance."""
        while True:
            try:
                # Check each active conversation
                for session_id, context in list(self.active_conversations.items()):
                    if self.should_check_conversation(context):
                        await self.analyze_conversation_significance(context)

                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Error in conversation monitoring: {e}")
                await asyncio.sleep(10)

    def should_check_conversation(self, context: ConversationContext) -> bool:
        """Determine if a conversation should be checked for significance."""
        # Check if conversation has new activity
        time_since_activity = (
            datetime.now(timezone.utc) - context.last_activity
        ).total_seconds()

        # Check every 30 seconds if there's been recent activity
        return time_since_activity < 30 and len(context.messages) > 0

    async def analyze_conversation_significance(self, context: ConversationContext):
        """Analyze conversation significance and create capsule (UNIVERSAL CAPTURE)."""
        try:
            # Get recent messages for analysis
            recent_messages = context.messages[-5:]  # Last 5 messages

            # Analyze significance
            significance_result = await analyze_conversation_significance(
                messages=recent_messages,
                context={
                    "session_id": context.session_id,
                    "user_id": context.user_id,
                    "platform": context.platform,
                    "conversation_length": len(context.messages),
                },
            )

            context.significance_score = significance_result.get("score", 0.0)

            # UNIVERSAL CAPTURE: Create capsule for ALL conversations
            # Significance is stored as economic WEIGHT, not used as filter
            if not context.capsule_created:
                context.capsule_created = True
                logger.info(
                    f"📝 Capturing conversation (significance: {context.significance_score:.2f})"
                )

                # Create capsule regardless of significance
                # The significance score determines economic weight, not whether to capture
                await self.create_conversation_capsule(context, significance_result)

        except Exception as e:
            logger.error(f"Error analyzing conversation significance: {e}")

    async def create_conversation_capsule(
        self, context: ConversationContext, significance_result: Dict
    ):
        """Create a capsule for any conversation (UNIVERSAL CAPTURE).

        Significance is stored as economic weight, not used as filter.
        See: UNIVERSAL_CAPTURE_PHILOSOPHY.md
        """
        try:
            # Prepare capsule data
            capsule_data = {
                "type": "reasoning_trace",
                "content": self.format_conversation_content(context),
                "input_data": self.extract_user_input(context),
                "output": self.extract_ai_response(context),
                "reasoning": significance_result.get("reasoning_steps", []),
                "model_version": f"{context.platform}-conversation-monitor",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": f"{context.platform}-auto-capsule-system",
                "status": "SEALED",
                "metadata": {
                    "interaction_type": f"{context.platform}_conversation",
                    "session_id": context.session_id,
                    # Significance as ECONOMIC WEIGHT, not capture filter
                    "significance_score": context.significance_score,
                    "economic_weight": context.significance_score,  # Used for value distribution
                    "decision_factors": significance_result.get("factors", []),
                    "confidence": significance_result.get("confidence", 0.8),
                    "auto_captured": True,  # Universal capture - all conversations
                    "user_id": context.user_id,
                    "conversation_length": len(context.messages),
                    "reasoning_quality": "automated_significance_analysis",
                    "capture_philosophy": "universal",  # Captures ALL interactions
                },
            }

            # Create capsule using engine
            capsule = await self.engine.create_capsule_async(
                capsule_type="reasoning_trace",
                content=capsule_data["content"],
                confidence=significance_result.get("confidence", 0.8),
                reasoning_trace=capsule_data["reasoning"],
                metadata=capsule_data["metadata"],
            )

            logger.info(f"✅ Created capsule for conversation: {capsule.capsule_id}")

        except Exception as e:
            logger.error(f"Error creating conversation capsule: {e}")

    def format_conversation_content(self, context: ConversationContext) -> str:
        """Format conversation content for capsule."""
        if not context.messages:
            return f"{context.platform.title()} conversation"

        last_user_msg = next(
            (msg for msg in reversed(context.messages) if msg.get("role") == "user"),
            None,
        )
        last_ai_msg = next(
            (
                msg
                for msg in reversed(context.messages)
                if msg.get("role") == "assistant"
            ),
            None,
        )

        user_preview = (
            last_user_msg.get("content", "")[:100] + "..." if last_user_msg else ""
        )
        ai_preview = last_ai_msg.get("content", "")[:100] + "..." if last_ai_msg else ""

        return f"{context.platform.title()} interaction: {user_preview}"

    def extract_user_input(self, context: ConversationContext) -> str:
        """Extract the user's input from conversation."""
        user_messages = [msg for msg in context.messages if msg.get("role") == "user"]
        if user_messages:
            return user_messages[-1].get("content", "")
        return ""

    def extract_ai_response(self, context: ConversationContext) -> str:
        """Extract the AI's response from conversation."""
        ai_messages = [
            msg for msg in context.messages if msg.get("role") == "assistant"
        ]
        if ai_messages:
            return ai_messages[-1].get("content", "")
        return ""

    async def process_capsule_queue(self):
        """Process queued capsules for creation."""
        while True:
            try:
                # This could be expanded to handle a queue of capsules
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error processing capsule queue: {e}")

    async def cleanup_expired_conversations(self):
        """Clean up expired conversations."""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                expired_sessions = []

                for session_id, context in self.active_conversations.items():
                    # Remove conversations older than 1 hour
                    if (current_time - context.last_activity).total_seconds() > 3600:
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    logger.info(f"🧹 Cleaning up expired conversation: {session_id}")
                    del self.active_conversations[session_id]

                await asyncio.sleep(300)  # Clean up every 5 minutes

            except Exception as e:
                logger.error(f"Error in cleanup: {e}")

    # Public API methods
    def add_conversation_message(
        self,
        session_id: str,
        user_id: str,
        platform: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ):
        """Add a message to a conversation being monitored."""
        if session_id not in self.active_conversations:
            self.active_conversations[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                platform=platform,
                start_time=datetime.now(timezone.utc),
                messages=[],
                last_activity=datetime.now(timezone.utc),
            )

        context = self.active_conversations[session_id]
        context.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
            }
        )
        context.last_activity = datetime.now(timezone.utc)

        logger.info(f"📨 Added message to conversation {session_id}: {role}")

    def get_conversation_status(self, session_id: str) -> Optional[Dict]:
        """Get the current status of a conversation."""
        if session_id not in self.active_conversations:
            return None

        context = self.active_conversations[session_id]
        return {
            "session_id": session_id,
            "user_id": context.user_id,
            "platform": context.platform,
            "message_count": len(context.messages),
            "significance_score": context.significance_score,
            "capsule_created": context.capsule_created,
            "last_activity": context.last_activity.isoformat(),
        }


# Global monitor instance
_monitor_instance = None


def get_monitor(db_manager=None) -> LiveConversationMonitor:
    """Get the global monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = LiveConversationMonitor(db_manager=db_manager)
    return _monitor_instance


async def main():
    """Run the live monitoring system."""
    monitor = get_monitor()
    await monitor.start_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
