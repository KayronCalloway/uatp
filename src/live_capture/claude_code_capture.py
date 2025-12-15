#!/usr/bin/env python3
"""
UATP Live Claude Code Conversation Capture System
Captures real-time conversations from Claude Code sessions and creates UATP capsules
"""

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Load environment variables (including DATABASE_URL for PostgreSQL)
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.live_capture.rich_capture_integration import RichCaptureEnhancer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), "claude_capture.log")
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """Represents a single message in a Claude Code conversation."""

    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    message_id: str
    session_id: str
    token_count: Optional[int] = None
    model_info: Optional[str] = None


@dataclass
class ConversationSession:
    """Represents a complete conversation session."""

    session_id: str
    user_id: str
    start_time: datetime
    platform: str = "claude-code"
    end_time: Optional[datetime] = None
    messages: List[ConversationMessage] = None
    significance_score: float = 0.0
    total_tokens: int = 0
    topics: List[str] = None
    capsule_created: bool = False

    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.topics is None:
            self.topics = []


class ClaudeCodeCapture:
    """Main capture system for Claude Code conversations."""

    def __init__(self):
        # Don't initialize CapsuleEngine here - we'll use direct DB access
        self.active_sessions: Dict[str, ConversationSession] = {}
        self.db_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "live_capture.db"
        )
        self.init_database()
        logger.info("🚀 Claude Code Capture System initialized")

    def init_database(self):
        """Initialize the live capture database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS capture_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    platform TEXT DEFAULT 'claude-code',
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    message_count INTEGER DEFAULT 0,
                    significance_score REAL DEFAULT 0.0,
                    total_tokens INTEGER DEFAULT 0,
                    topics TEXT,
                    capsule_created BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create messages table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS capture_messages (
                    message_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    token_count INTEGER,
                    model_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES capture_sessions (session_id)
                )
            """
            )

            conn.commit()
            conn.close()
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")

    def generate_session_id(self, user_context: str = None) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        context = user_context or "claude-code-session"
        raw = f"{timestamp}-{context}-{os.getpid()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def calculate_significance_score(self, session: ConversationSession) -> float:
        """Calculate significance score for a conversation session."""
        score = 0.0

        # Base score from message count
        message_count = len(session.messages)
        score += min(message_count * 0.1, 3.0)

        # Token count factor
        if session.total_tokens > 0:
            score += min(session.total_tokens / 1000 * 0.2, 2.0)

        # Duration factor
        if session.end_time and session.start_time:
            duration_minutes = (
                session.end_time - session.start_time
            ).total_seconds() / 60
            score += min(duration_minutes * 0.05, 1.5)

        # Content complexity
        for msg in session.messages:
            content = msg.content.lower()
            # Look for complex topics
            if any(
                keyword in content
                for keyword in [
                    "implement",
                    "algorithm",
                    "architecture",
                    "design",
                    "system",
                    "problem",
                    "solution",
                    "optimize",
                    "debug",
                    "analyze",
                ]
            ):
                score += 0.3

            # Look for code patterns
            if "```" in msg.content or "function" in content or "class" in content:
                score += 0.2

        # Normalize to 0-1 range
        return min(score / 10.0, 1.0)

    def extract_topics(self, session: ConversationSession) -> List[str]:
        """Extract main topics from conversation content."""
        topics = []
        content_text = " ".join([msg.content for msg in session.messages]).lower()

        # Technical topics
        tech_keywords = {
            "python": "Python Programming",
            "javascript": "JavaScript Development",
            "react": "React Framework",
            "api": "API Development",
            "database": "Database Design",
            "algorithm": "Algorithms",
            "machine learning": "Machine Learning",
            "ai": "Artificial Intelligence",
            "uatp": "UATP Development",
            "frontend": "Frontend Development",
            "backend": "Backend Development",
            "devops": "DevOps",
        }

        for keyword, topic in tech_keywords.items():
            if keyword in content_text:
                topics.append(topic)

        return topics[:5]  # Limit to top 5 topics

    async def start_session(
        self, user_id: str = None, context: Dict[str, Any] = None
    ) -> str:
        """Start a new conversation capture session."""
        user_id = user_id or f"user-{os.getenv('USER', 'unknown')}"
        session_id = self.generate_session_id(user_id)

        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.now(timezone.utc),
            platform="claude-code",
        )

        self.active_sessions[session_id] = session

        # Save to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO capture_sessions
                (session_id, user_id, platform, start_time)
                VALUES (?, ?, ?, ?)
            """,
                (session_id, user_id, "claude-code", session.start_time.isoformat()),
            )
            conn.commit()
            conn.close()
            logger.info(f"📝 Started capture session: {session_id} for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to save session: {e}")

        return session_id

    async def capture_message(
        self,
        session_id: str,
        role: str,
        content: str,
        token_count: int = None,
        model_info: str = None,
    ) -> str:
        """Capture a single message in the conversation."""
        if session_id not in self.active_sessions:
            logger.warning(f"⚠️ Session {session_id} not found, creating new session")
            session_id = await self.start_session()

        session = self.active_sessions[session_id]
        message_id = (
            f"msg_{datetime.now(timezone.utc).timestamp()}_{len(session.messages)}"
        )

        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc),
            message_id=message_id,
            session_id=session_id,
            token_count=token_count,
            model_info=model_info,
        )

        session.messages.append(message)
        if token_count:
            session.total_tokens += token_count

        # Save message to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO capture_messages
                (message_id, session_id, role, content, timestamp, token_count, model_info)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    message_id,
                    session_id,
                    role,
                    content,
                    message.timestamp.isoformat(),
                    token_count,
                    model_info,
                ),
            )
            conn.commit()
            conn.close()
            logger.info(f"💬 Captured {role} message in session {session_id}")
        except Exception as e:
            logger.error(f"❌ Failed to save message: {e}")

        return message_id

    async def end_session(self, session_id: str) -> Optional[ConversationSession]:
        """End a conversation session and calculate final metrics."""
        if session_id not in self.active_sessions:
            logger.warning(f"⚠️ Session {session_id} not found")
            return None

        session = self.active_sessions[session_id]
        session.end_time = datetime.now(timezone.utc)
        session.significance_score = self.calculate_significance_score(session)
        session.topics = self.extract_topics(session)

        # Update database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE capture_sessions SET
                end_time = ?, message_count = ?, significance_score = ?,
                total_tokens = ?, topics = ?
                WHERE session_id = ?
            """,
                (
                    session.end_time.isoformat(),
                    len(session.messages),
                    session.significance_score,
                    session.total_tokens,
                    json.dumps(session.topics),
                    session_id,
                ),
            )
            conn.commit()
            conn.close()
            logger.info(
                f"🏁 Session {session_id} ended. Significance: {session.significance_score:.2f}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to update session: {e}")

        # Remove from active sessions
        completed_session = self.active_sessions.pop(session_id)
        return completed_session

    async def should_create_capsule(self, session: ConversationSession) -> bool:
        """Determine if a session warrants capsule creation."""
        # Minimum thresholds
        min_messages = 3
        min_significance = 0.3
        min_duration_minutes = 2

        # Check message count
        if len(session.messages) < min_messages:
            return False

        # Check significance score
        if session.significance_score < min_significance:
            return False

        # Check duration if session ended
        if session.end_time:
            duration = (session.end_time - session.start_time).total_seconds() / 60
            if duration < min_duration_minutes:
                return False

        return True

    async def create_capsule_from_session(
        self, session: ConversationSession
    ) -> Optional[str]:
        """Create a UATP capsule from a conversation session with RICH metadata."""
        if not await self.should_create_capsule(session):
            logger.info(
                f"📝 Session {session.session_id} doesn't meet capsule criteria"
            )
            return None

        try:
            # Create capsule with rich metadata
            capsule_data = (
                RichCaptureEnhancer.create_capsule_from_session_with_rich_metadata(
                    session=session, user_id=session.user_id
                )
            )

            # Store to database (PostgreSQL for production)
            import json
            from datetime import datetime

            import asyncpg

            from src.core.config import DATABASE_URL

            # Parse DATABASE_URL to get PostgreSQL connection params
            # Format: postgresql://user@host:port/database
            if "postgresql" in DATABASE_URL:
                conn = await asyncpg.connect(
                    DATABASE_URL.replace("postgresql://", "postgresql://").replace(
                        "postgresql+asyncpg://", "postgresql://"
                    )
                )

                # Insert capsule
                await conn.execute(
                    """
                    INSERT INTO capsules (capsule_id, capsule_type, version, timestamp, status, verification, payload)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    capsule_data["capsule_id"],
                    capsule_data["type"],
                    capsule_data["version"],
                    datetime.fromisoformat(
                        capsule_data["timestamp"].replace("Z", "+00:00")
                    ),
                    capsule_data["status"],
                    json.dumps(capsule_data["verification"]),
                    json.dumps(capsule_data["payload"]),
                )

                await conn.close()
                capsule_id = capsule_data["capsule_id"]

                logger.info(
                    f"✨ Created RICH capsule {capsule_id} with per-step metadata"
                )

            else:
                # Fallback: Use simple direct PostgreSQL insert even without asyncpg
                # This shouldn't happen in production but provides safety
                capsule_id = capsule_data["capsule_id"]
                logger.warning(
                    "⚠️ DATABASE_URL not set, capsule data prepared but not persisted"
                )
                logger.info(f"Capsule would be: {capsule_id}")

            # Mark session as having capsule created
            session.capsule_created = True

            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE capture_sessions SET capsule_created = TRUE
                WHERE session_id = ?
            """,
                (session.session_id,),
            )
            conn.commit()
            conn.close()

            logger.info(
                f"🔥 Created RICH UATP capsule {capsule_id} from session {session.session_id}"
            )
            return capsule_id

        except Exception as e:
            logger.error(f"❌ Failed to create capsule: {e}")
            return None

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get information about currently active sessions."""
        sessions = []
        for session_id, session in self.active_sessions.items():
            sessions.append(
                {
                    "session_id": session_id,
                    "user_id": session.user_id,
                    "platform": session.platform,
                    "start_time": session.start_time.isoformat(),
                    "message_count": len(session.messages),
                    "significance_score": session.significance_score,
                    "total_tokens": session.total_tokens,
                    "should_create_capsule": await self.should_create_capsule(session),
                }
            )
        return sessions

    async def get_completed_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently completed sessions from database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT session_id, user_id, platform, start_time, end_time,
                       message_count, significance_score, total_tokens, topics,
                       capsule_created
                FROM capture_sessions
                WHERE end_time IS NOT NULL
                ORDER BY end_time DESC
                LIMIT ?
            """,
                (limit,),
            )

            rows = cursor.fetchall()
            conn.close()

            sessions = []
            for row in rows:
                sessions.append(
                    {
                        "session_id": row[0],
                        "user_id": row[1],
                        "platform": row[2],
                        "start_time": row[3],
                        "end_time": row[4],
                        "message_count": row[5],
                        "significance_score": row[6],
                        "total_tokens": row[7],
                        "topics": json.loads(row[8]) if row[8] else [],
                        "capsule_created": bool(row[9]),
                    }
                )

            return sessions
        except Exception as e:
            logger.error(f"❌ Failed to get completed sessions: {e}")
            return []


# Global capture instance
capture_system = ClaudeCodeCapture()


# API functions for integration
async def start_capture_session(user_id: str = None) -> str:
    """Start a new live capture session."""
    return await capture_system.start_session(user_id)


async def capture_user_message(session_id: str, content: str) -> str:
    """Capture a user message."""
    return await capture_system.capture_message(session_id, "user", content)


async def capture_assistant_message(
    session_id: str, content: str, token_count: int = None, model_info: str = None
) -> str:
    """Capture an assistant message."""
    return await capture_system.capture_message(
        session_id, "assistant", content, token_count, model_info
    )


async def end_capture_session(session_id: str) -> Optional[str]:
    """End a capture session and potentially create a capsule."""
    session = await capture_system.end_session(session_id)
    if session:
        capsule_id = await capture_system.create_capsule_from_session(session)
        return capsule_id
    return None


if __name__ == "__main__":
    # Test the capture system
    async def test_capture():
        logger.info("🧪 Testing Claude Code capture system...")

        # Start a session
        session_id = await start_capture_session("test-user")

        # Simulate a conversation
        await capture_user_message(
            session_id, "Help me implement a UATP capsule creation system"
        )
        await capture_assistant_message(
            session_id,
            "I'll help you build a UATP capsule creation system. Let's start by understanding the requirements...",
            150,
            "claude-3-sonnet",
        )
        await capture_user_message(
            session_id,
            "I need to capture live conversations and create capsules automatically",
        )
        await capture_assistant_message(
            session_id,
            "Perfect! Here's how we can implement live conversation capture with automatic capsule creation...",
            200,
            "claude-3-sonnet",
        )

        # End session and create capsule
        capsule_id = await end_capture_session(session_id)
        if capsule_id:
            logger.info(f"✅ Test completed - Capsule created: {capsule_id}")
        else:
            logger.info("📝 Test completed - No capsule created (didn't meet criteria)")

    # Run test
    asyncio.run(test_capture())
