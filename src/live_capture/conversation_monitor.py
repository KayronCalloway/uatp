"""
Real-time conversation monitoring and capsule generation system.
This module captures live AI interactions and creates attribution capsules.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import capsule engine
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))


from src.engine.capsule_engine import CapsuleEngine
from src.feedback.outcome_inference import OutcomeInferenceEngine
from src.integrations.openai_client import OpenAIClient
from src.live_capture.claude_code_capture import (
    ConversationMessage,
    ConversationSession,
)
from src.live_capture.rich_capture_integration import RichCaptureEnhancer
from src.reasoning.fixed_analyzer import analyze_conversation_significance

# Initialize outcome inference for auto-tracking
_outcome_engine = None
def get_outcome_engine():
    global _outcome_engine
    if _outcome_engine is None:
        _outcome_engine = OutcomeInferenceEngine()
    return _outcome_engine

# Calibration integration for recursive learning
_calibration_manager = None
def get_calibration_manager():
    """Get calibration manager for recording outcomes."""
    global _calibration_manager
    if _calibration_manager is None:
        try:
            from src.feedback.calibration import get_calibration_manager as get_cal
            _calibration_manager = get_cal()
        except Exception as e:
            logger.debug(f"Calibration manager not available: {e}")
    return _calibration_manager

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
    # Real-time capsule tracking - create capsules periodically, not just once
    last_capsule_time: Optional[datetime] = None
    last_capsule_message_count: int = 0
    capsules_created: int = 0  # Total capsules created for this session


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
        logger.info("🔄 Monitor loop started")
        while True:
            try:
                logger.info(f"🔄 Monitor tick (instance {id(self)}): {len(self.active_conversations)} conversations: {list(self.active_conversations.keys())}")
                # Check each active conversation
                for session_id, context in list(self.active_conversations.items()):
                    should_check = self.should_check_conversation(context)
                    logger.info(f"🔍 Checking {session_id}: should_check={should_check}, messages={len(context.messages)}, capsules_created={context.capsules_created}")
                    if should_check:
                        logger.info(f"📊 Analyzing conversation {session_id}")
                        await self.analyze_conversation_significance(context)

                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Error in conversation monitoring: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
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

            # REAL-TIME CAPSULE CREATION
            # Create capsules periodically: every 5 new messages OR every 2 minutes
            current_time = datetime.now(timezone.utc)
            messages_since_last = len(context.messages) - context.last_capsule_message_count

            should_create_capsule = False
            reason = ""

            # First capsule for this session
            if context.last_capsule_time is None:
                should_create_capsule = True
                reason = "first capsule"
            # Every 5 new messages
            elif messages_since_last >= 5:
                should_create_capsule = True
                reason = f"{messages_since_last} new messages"
            # Every 2 minutes of activity
            elif (current_time - context.last_capsule_time).total_seconds() >= 120:
                should_create_capsule = True
                reason = "2 minute checkpoint"

            if should_create_capsule:
                logger.info(
                    f"📝 Creating real-time capsule ({reason}, significance: {context.significance_score:.2f})"
                )
                await self.create_conversation_capsule(context, significance_result)

                # Update tracking
                context.last_capsule_time = current_time
                context.last_capsule_message_count = len(context.messages)
                context.capsules_created += 1

        except Exception as e:
            logger.error(f"Error analyzing conversation significance: {e}")

    async def create_conversation_capsule(
        self, context: ConversationContext, significance_result: Dict
    ):
        """Create a RICH capsule for any conversation (UNIVERSAL CAPTURE).

        Uses RichCaptureEnhancer for full court-admissible, insurance-ready data.
        Significance is stored as economic weight, not used as filter.
        """
        try:
            # Convert ConversationContext messages to ConversationMessage objects
            rich_messages = []
            for i, msg in enumerate(context.messages):
                # Parse timestamp - handle both string and datetime
                msg_timestamp = msg.get("timestamp")
                if isinstance(msg_timestamp, str):
                    try:
                        msg_timestamp = datetime.fromisoformat(msg_timestamp.replace("Z", "+00:00"))
                    except:
                        msg_timestamp = datetime.now(timezone.utc)
                elif not isinstance(msg_timestamp, datetime):
                    msg_timestamp = datetime.now(timezone.utc)

                # Estimate token count from content length
                content = msg.get("content", "")
                estimated_tokens = int(len(content.split()) * 1.3)

                rich_messages.append(ConversationMessage(
                    role=msg.get("role", "user"),
                    content=content,
                    timestamp=msg_timestamp,
                    message_id=f"msg_{context.session_id}_{i}",
                    session_id=context.session_id,
                    token_count=estimated_tokens,
                    model_info=msg.get("metadata", {}).get("model", f"{context.platform}-model"),
                ))

            # Extract topics from conversation content
            topics = self._extract_topics(context)

            # Calculate total tokens
            total_tokens = sum(m.token_count or 0 for m in rich_messages)

            # Create ConversationSession for RichCaptureEnhancer
            session = ConversationSession(
                session_id=context.session_id,
                user_id=context.user_id,
                start_time=context.start_time,
                platform=context.platform,
                end_time=context.last_activity,
                messages=rich_messages,
                significance_score=context.significance_score,
                total_tokens=total_tokens,
                topics=topics,
                capsule_created=False,
            )

            # Use RichCaptureEnhancer to create RICH capsule with full metadata
            logger.info(f"🔥 Creating RICH capsule for session {context.session_id}")
            capsule_data = RichCaptureEnhancer.create_capsule_from_session_with_rich_metadata(
                session=session,
                user_id=context.user_id
            )

            # Add universal capture metadata
            if "metadata" not in capsule_data:
                capsule_data["metadata"] = {}
            capsule_data["metadata"]["auto_captured"] = True
            capsule_data["metadata"]["capture_philosophy"] = "universal"
            capsule_data["metadata"]["economic_weight"] = context.significance_score

            # Store to database via engine
            if self.engine:
                # Create capsule using the engine's direct storage method
                stored_capsule = await self.engine.store_rich_capsule_async(capsule_data)
                logger.info(f"✅ Created RICH capsule: {capsule_data.get('capsule_id')} with {len(rich_messages)} messages")
                logger.info(f"   Topics: {topics}")
                logger.info(f"   Confidence: {capsule_data.get('confidence', 'N/A')}")
            else:
                logger.warning("⚠️ Engine not available - capsule data prepared but not stored")
                logger.info(f"   Capsule ID: {capsule_data.get('capsule_id')}")

        except Exception as e:
            import traceback
            logger.error(f"Error creating RICH conversation capsule: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

    def _extract_topics(self, context: ConversationContext) -> List[str]:
        """Extract topics from conversation content."""
        topics = []
        all_content = " ".join([msg.get("content", "") for msg in context.messages]).lower()

        topic_keywords = {
            "python": "Python Programming",
            "javascript": "JavaScript Development",
            "api": "API Development",
            "database": "Database Design",
            "uatp": "UATP Development",
            "capsule": "Capsule System",
            "capture": "Data Capture",
            "insurance": "Insurance Integration",
            "security": "Security",
            "verification": "Verification",
            "machine learning": "Machine Learning",
            "ai": "Artificial Intelligence",
        }

        for keyword, topic in topic_keywords.items():
            if keyword in all_content:
                topics.append(topic)

        return topics[:5] if topics else ["General Discussion"]

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
        logger.info(f"📨 Adding message to monitor instance {id(self)}, conversations: {list(self.active_conversations.keys())}")
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

        # AUTO-OUTCOME TRACKING: Infer outcome from user follow-ups
        # This is the RECURSIVE LEARNING loop - outcomes feed back to calibration
        if role == "user" and len(context.messages) >= 2:
            # Check if previous message was from AI
            prev_msg = context.messages[-2]
            if prev_msg.get("role") == "assistant":
                try:
                    engine = get_outcome_engine()
                    result = engine.infer_outcome(
                        ai_response=prev_msg.get("content", ""),
                        follow_up=content
                    )

                    # Store inference result
                    if not hasattr(context, 'outcome_inference'):
                        context.outcome_inference = []
                    context.outcome_inference.append({
                        "outcome": result.outcome,
                        "confidence": result.confidence,
                        "signals": result.signals,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                    # HIGH CONFIDENCE: Feed to calibration (RECURSIVE LEARNING)
                    # Lowered from 0.7 to 0.5 to capture more training data
                    if result.confidence >= 0.5:
                        logger.info(f"🎯 Auto-outcome: {result.outcome} (conf: {result.confidence:.2f}) - {result.signals[:2]}")

                        # CALIBRATION UPDATE: This is where the system LEARNS
                        # Map outcome to numeric value for calibration
                        outcome_map = {"success": 1.0, "partial": 0.5, "failure": 0.0}
                        if result.outcome in outcome_map:
                            cal_manager = get_calibration_manager()
                            if cal_manager:
                                # Get predicted confidence from capsule (estimate if not available)
                                predicted_conf = prev_msg.get("metadata", {}).get("confidence", 0.5)
                                actual_outcome = outcome_map[result.outcome]

                                # Record for calibration - THIS IS THE LEARNING STEP
                                cal_manager.record_outcome(
                                    predicted_confidence=predicted_conf,
                                    actual_outcome=actual_outcome,
                                    domain=context.platform,  # Use platform as domain
                                )
                                logger.info(f"📈 Calibration updated: predicted={predicted_conf:.2f}, actual={actual_outcome:.2f}, domain={context.platform}")

                                # Track total calibration points for this session
                                if not hasattr(context, 'calibration_points'):
                                    context.calibration_points = 0
                                context.calibration_points += 1

                        # Update latest capsule outcome if we have a capsule
                        if context.last_capsule_time and self.engine:
                            try:
                                # Mark the outcome on the most recent capsule for this session
                                asyncio.create_task(self._update_capsule_outcome_async(
                                    session_id=session_id,
                                    outcome=result.outcome,
                                    confidence=result.confidence,
                                    signals=result.signals,
                                ))
                            except Exception as e:
                                logger.debug(f"Capsule outcome update queued: {e}")

                    # LOW CONFIDENCE: Log for potential human review
                    elif result.confidence >= 0.4:
                        logger.debug(f"📊 Low-confidence outcome: {result.outcome} (conf: {result.confidence:.2f}) - may need review")

                except Exception as e:
                    logger.debug(f"Outcome inference skipped: {e}")

    async def _update_capsule_outcome_async(
        self,
        session_id: str,
        outcome: str,
        confidence: float,
        signals: List[str],
    ):
        """
        Update the most recent capsule for a session with outcome data.

        This is part of the RECURSIVE LEARNING loop:
        1. AI responds → capsule created
        2. User follows up → outcome inferred
        3. Capsule updated with outcome → calibration learns
        """
        try:
            if not self.engine or not self.engine.db_manager:
                logger.debug("No engine/db_manager for capsule outcome update")
                return

            # Find the most recent capsule for this session
            # Update its outcome_status field
            async with self.engine.db_manager.session() as session:
                from sqlalchemy import update, desc
                from src.models.capsule import CapsuleModel

                # Update the most recent capsule matching this session
                result = await session.execute(
                    update(CapsuleModel)
                    .where(CapsuleModel.payload["session_metadata"]["session_id"].astext == session_id)
                    .values(
                        outcome_status=outcome,
                        outcome_timestamp=datetime.now(timezone.utc),
                        outcome_notes=f"Auto-inferred (conf: {confidence:.2f})",
                        outcome_metrics={"signals": signals, "inference_confidence": confidence},
                    )
                )
                await session.commit()

                if result.rowcount > 0:
                    logger.info(f"✅ Updated {result.rowcount} capsule(s) with outcome: {outcome}")
                else:
                    logger.debug(f"No capsules found for session {session_id}")

        except Exception as e:
            logger.warning(f"Failed to update capsule outcome: {e}")

    def get_conversation_status(self, session_id: str) -> Optional[Dict]:
        """Get the current status of a conversation."""
        if session_id not in self.active_conversations:
            return None

        context = self.active_conversations[session_id]
        # Include calibration stats if available
        calibration_points = getattr(context, 'calibration_points', 0)
        outcome_inferences = len(getattr(context, 'outcome_inference', []))

        return {
            "session_id": session_id,
            "user_id": context.user_id,
            "platform": context.platform,
            "message_count": len(context.messages),
            "significance_score": context.significance_score,
            "capsules_created": context.capsules_created,
            "last_capsule_time": context.last_capsule_time.isoformat() if context.last_capsule_time else None,
            "last_activity": context.last_activity.isoformat(),
            # Recursive learning stats
            "calibration_points": calibration_points,
            "outcome_inferences": outcome_inferences,
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
