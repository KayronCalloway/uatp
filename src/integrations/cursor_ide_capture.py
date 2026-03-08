#!/usr/bin/env python3
"""
UATP Cursor IDE Integration
Captures development workflow, AI-assisted coding sessions, and decision traces from Cursor IDE
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

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.capsule_schema import CapsuleStatus
from src.engine.capsule_engine import CapsuleEngine
from src.live_capture.claude_code_capture import (
    ConversationMessage,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), "cursor_capture.log")
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class CursorWorkflowEvent:
    """Represents a single workflow event in Cursor IDE."""

    event_id: str
    session_id: str
    event_type: str  # 'ai_request', 'code_change', 'file_operation', 'decision_point'
    timestamp: datetime
    user_id: str
    content: str
    metadata: Dict[str, Any]
    significance_score: float = 0.0


@dataclass
class CursorSession:
    """Represents a complete Cursor IDE development session."""

    session_id: str
    user_id: str
    project_path: str
    start_time: datetime
    end_time: Optional[datetime] = None
    events: List[CursorWorkflowEvent] = None
    ai_interactions: List[ConversationMessage] = None
    files_modified: List[str] = None
    significance_score: float = 0.0
    capsule_created: bool = False

    def __post_init__(self):
        if self.events is None:
            self.events = []
        if self.ai_interactions is None:
            self.ai_interactions = []
        if self.files_modified is None:
            self.files_modified = []


class CursorIDECapture:
    """Main capture system for Cursor IDE development workflows."""

    def __init__(self):
        self.engine = CapsuleEngine()
        self.active_sessions: Dict[str, CursorSession] = {}
        self.db_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "cursor_capture.db"
        )
        self.monitoring_active = False
        self.init_database()
        logger.info(" Cursor IDE Capture System initialized")

    def init_database(self):
        """Initialize the Cursor IDE capture database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create cursor sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cursor_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    project_path TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    event_count INTEGER DEFAULT 0,
                    ai_interaction_count INTEGER DEFAULT 0,
                    files_modified_count INTEGER DEFAULT 0,
                    significance_score REAL DEFAULT 0.0,
                    capsule_created BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create workflow events table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cursor_events (
                    event_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    significance_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES cursor_sessions (session_id)
                )
            """
            )

            conn.commit()
            conn.close()
            logger.info("[OK] Cursor IDE database initialized successfully")
        except Exception as e:
            logger.error(f"[ERROR] Cursor IDE database initialization failed: {e}")

    def generate_session_id(self, project_path: str) -> str:
        """Generate a unique session ID for Cursor IDE session."""
        timestamp = datetime.now(timezone.utc).isoformat()
        project_name = Path(project_path).name
        raw = f"cursor-{timestamp}-{project_name}-{os.getpid()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    async def start_cursor_session(self, user_id: str, project_path: str) -> str:
        """Start a new Cursor IDE capture session."""
        session_id = self.generate_session_id(project_path)

        session = CursorSession(
            session_id=session_id,
            user_id=user_id,
            project_path=project_path,
            start_time=datetime.now(timezone.utc),
        )

        self.active_sessions[session_id] = session

        # Save to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO cursor_sessions
                (session_id, user_id, project_path, start_time)
                VALUES (?, ?, ?, ?)
            """,
                (session_id, user_id, project_path, session.start_time.isoformat()),
            )
            conn.commit()
            conn.close()
            logger.info(
                f" Started Cursor session: {session_id} for project: {Path(project_path).name}"
            )
        except Exception as e:
            logger.error(f"[ERROR] Failed to save Cursor session: {e}")

        return session_id

    async def capture_ai_interaction(
        self,
        session_id: str,
        user_query: str,
        ai_response: str,
        context: Dict[str, Any] = None,
    ) -> str:
        """Capture AI interaction within Cursor IDE."""
        if session_id not in self.active_sessions:
            logger.warning(f"[WARN] Cursor session {session_id} not found")
            return None

        session = self.active_sessions[session_id]

        # Create conversation messages
        user_msg = ConversationMessage(
            role="user",
            content=user_query,
            timestamp=datetime.now(timezone.utc),
            message_id=f"cursor_user_{len(session.ai_interactions)}",
            session_id=session_id,
            model_info="cursor-ide",
        )

        assistant_msg = ConversationMessage(
            role="assistant",
            content=ai_response,
            timestamp=datetime.now(timezone.utc),
            message_id=f"cursor_assistant_{len(session.ai_interactions)}",
            session_id=session_id,
            model_info="cursor-ide",
        )

        session.ai_interactions.extend([user_msg, assistant_msg])

        # Create workflow event
        event_id = f"ai_interaction_{datetime.now(timezone.utc).timestamp()}"
        event = CursorWorkflowEvent(
            event_id=event_id,
            session_id=session_id,
            event_type="ai_request",
            timestamp=datetime.now(timezone.utc),
            user_id=session.user_id,
            content=f"User: {user_query}\nAI: {ai_response}",
            metadata={
                "query_length": len(user_query),
                "response_length": len(ai_response),
                "context": context or {},
            },
            significance_score=self.calculate_interaction_significance(
                user_query, ai_response
            ),
        )

        session.events.append(event)

        # Save event to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO cursor_events
                (event_id, session_id, event_type, timestamp, user_id, content, metadata, significance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event_id,
                    session_id,
                    "ai_request",
                    event.timestamp.isoformat(),
                    session.user_id,
                    event.content,
                    json.dumps(event.metadata),
                    event.significance_score,
                ),
            )
            conn.commit()
            conn.close()
            logger.info(f" Captured AI interaction in Cursor session {session_id}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to save AI interaction: {e}")

        return event_id

    async def capture_code_change(
        self,
        session_id: str,
        file_path: str,
        change_type: str,
        content: str,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Capture code changes in Cursor IDE."""
        if session_id not in self.active_sessions:
            logger.warning(f"[WARN] Cursor session {session_id} not found")
            return None

        session = self.active_sessions[session_id]

        # Track modified files
        if file_path not in session.files_modified:
            session.files_modified.append(file_path)

        # Create workflow event
        event_id = f"code_change_{datetime.now(timezone.utc).timestamp()}"
        event = CursorWorkflowEvent(
            event_id=event_id,
            session_id=session_id,
            event_type="code_change",
            timestamp=datetime.now(timezone.utc),
            user_id=session.user_id,
            content=content,
            metadata={
                "file_path": file_path,
                "change_type": change_type,
                "file_extension": Path(file_path).suffix,
                **(metadata or {}),
            },
            significance_score=self.calculate_code_change_significance(
                change_type, content, file_path
            ),
        )

        session.events.append(event)

        # Save event to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO cursor_events
                (event_id, session_id, event_type, timestamp, user_id, content, metadata, significance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event_id,
                    session_id,
                    "code_change",
                    event.timestamp.isoformat(),
                    session.user_id,
                    event.content,
                    json.dumps(event.metadata),
                    event.significance_score,
                ),
            )
            conn.commit()
            conn.close()
            logger.info(f" Captured code change in {Path(file_path).name}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to save code change: {e}")

        return event_id

    def calculate_interaction_significance(
        self, user_query: str, ai_response: str
    ) -> float:
        """Calculate significance score for AI interaction."""
        score = 0.0

        # Query complexity
        query_keywords = [
            "implement",
            "refactor",
            "optimize",
            "debug",
            "architecture",
            "design",
            "algorithm",
        ]
        for keyword in query_keywords:
            if keyword.lower() in user_query.lower():
                score += 0.2

        # Response length and depth
        if len(ai_response) > 200:
            score += 0.3
        if "```" in ai_response:  # Code blocks
            score += 0.4

        # Technical depth indicators
        tech_indicators = [
            "function",
            "class",
            "method",
            "variable",
            "import",
            "async",
            "await",
        ]
        for indicator in tech_indicators:
            if indicator in ai_response.lower():
                score += 0.1

        return min(score, 1.0)

    def calculate_code_change_significance(
        self, change_type: str, content: str, file_path: str
    ) -> float:
        """Calculate significance score for code changes."""
        score = 0.0

        # Change type weight
        change_weights = {
            "create": 0.8,
            "major_edit": 0.6,
            "refactor": 0.7,
            "delete": 0.4,
            "minor_edit": 0.2,
        }
        score += change_weights.get(change_type, 0.3)

        # File type significance
        file_ext = Path(file_path).suffix.lower()
        important_files = {
            ".py": 0.3,
            ".js": 0.3,
            ".ts": 0.3,
            ".tsx": 0.3,
            ".jsx": 0.3,
            ".cpp": 0.2,
            ".java": 0.2,
            ".go": 0.2,
            ".rs": 0.2,
        }
        score += important_files.get(file_ext, 0.1)

        # Content analysis
        if len(content) > 100:
            score += 0.2

        return min(score, 1.0)

    async def calculate_session_significance(self, session: CursorSession) -> float:
        """Calculate overall significance score for Cursor session."""
        score = 0.0

        # AI interaction factor
        score += min(len(session.ai_interactions) * 0.1, 2.0)

        # Events factor
        score += min(len(session.events) * 0.05, 1.5)

        # Files modified factor
        score += min(len(session.files_modified) * 0.2, 2.0)

        # Duration factor
        if session.end_time and session.start_time:
            duration_minutes = (
                session.end_time - session.start_time
            ).total_seconds() / 60
            score += min(duration_minutes * 0.02, 1.0)

        # Event significance sum
        if session.events:
            avg_event_significance = sum(
                e.significance_score for e in session.events
            ) / len(session.events)
            score += avg_event_significance * 2.0

        return min(score / 8.0, 1.0)

    async def end_cursor_session(self, session_id: str) -> Optional[CursorSession]:
        """End a Cursor IDE session and calculate final metrics."""
        if session_id not in self.active_sessions:
            logger.warning(f"[WARN] Cursor session {session_id} not found")
            return None

        session = self.active_sessions[session_id]
        session.end_time = datetime.now(timezone.utc)
        session.significance_score = await self.calculate_session_significance(session)

        # Update database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE cursor_sessions SET
                end_time = ?, event_count = ?, ai_interaction_count = ?,
                files_modified_count = ?, significance_score = ?
                WHERE session_id = ?
            """,
                (
                    session.end_time.isoformat(),
                    len(session.events),
                    len(session.ai_interactions),
                    len(session.files_modified),
                    session.significance_score,
                    session_id,
                ),
            )
            conn.commit()
            conn.close()
            logger.info(
                f" Cursor session {session_id} ended. Significance: {session.significance_score:.2f}"
            )
        except Exception as e:
            logger.error(f"[ERROR] Failed to update Cursor session: {e}")

        # Remove from active sessions
        completed_session = self.active_sessions.pop(session_id)
        return completed_session

    async def should_create_capsule(self, session: CursorSession) -> bool:
        """Determine if a Cursor session warrants capsule creation."""
        # Minimum thresholds for development workflows
        min_significance = 0.4
        min_ai_interactions = 2
        min_events = 5

        if session.significance_score < min_significance:
            return False

        if len(session.ai_interactions) < min_ai_interactions:
            return False

        if len(session.events) < min_events:
            return False

        return True

    async def create_capsule_from_cursor_session(
        self, session: CursorSession
    ) -> Optional[str]:
        """Create a UATP capsule from a Cursor IDE session."""
        if not await self.should_create_capsule(session):
            logger.info(
                f" Cursor session {session.session_id} doesn't meet capsule criteria"
            )
            return None

        try:
            # Build reasoning trace from development workflow
            reasoning_steps = []

            # Add project context step
            reasoning_steps.append(
                {
                    "step_type": "context",
                    "content": f"Development session in {Path(session.project_path).name}",
                    "confidence": 0.9,
                    "evidence": [f"project_path_{session.project_path}"],
                    "metadata": {
                        "session_type": "cursor_ide",
                        "project_path": session.project_path,
                        "start_time": session.start_time.isoformat(),
                    },
                }
            )

            # Add workflow events as reasoning steps
            for event in session.events[-10:]:  # Last 10 events to avoid overwhelming
                reasoning_steps.append(
                    {
                        "step_type": event.event_type,
                        "content": event.content[:300] + "..."
                        if len(event.content) > 300
                        else event.content,
                        "confidence": event.significance_score,
                        "evidence": [
                            f"event_{event.event_id}",
                            f"timestamp_{event.timestamp.isoformat()}",
                        ],
                        "metadata": {
                            "event_type": event.event_type,
                            "event_id": event.event_id,
                            "significance": event.significance_score,
                            **event.metadata,
                        },
                    }
                )

            # Add summary step
            reasoning_steps.append(
                {
                    "step_type": "conclusion",
                    "content": f"Development session completed: {len(session.events)} workflow events, {len(session.ai_interactions)} AI interactions, {len(session.files_modified)} files modified",
                    "confidence": session.significance_score,
                    "evidence": [f"session_{session.session_id}"],
                    "metadata": {
                        "session_summary": True,
                        "total_events": len(session.events),
                        "ai_interactions": len(session.ai_interactions),
                        "files_modified": len(session.files_modified),
                        "significance_score": session.significance_score,
                    },
                }
            )

            reasoning_trace = {
                "query": f"Cursor IDE development session {session.session_id}",
                "steps": reasoning_steps,
                "conclusion": f"Development workflow completed with significance score {session.significance_score:.2f}",
                "confidence_score": session.significance_score,
                "metadata": {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "platform": "cursor-ide",
                    "project_path": session.project_path,
                    "start_time": session.start_time.isoformat(),
                    "end_time": session.end_time.isoformat()
                    if session.end_time
                    else None,
                    "total_events": len(session.events),
                    "ai_interactions": len(session.ai_interactions),
                    "files_modified": session.files_modified,
                    "workflow_type": "development_session",
                },
            }

            # Create capsule using engine
            capsule = await self.engine.create_reasoning_capsule_async(
                reasoning_trace=reasoning_trace, status=CapsuleStatus.VERIFIED
            )

            # Mark session as having capsule created
            session.capsule_created = True

            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE cursor_sessions SET capsule_created = TRUE
                WHERE session_id = ?
            """,
                (session.session_id,),
            )
            conn.commit()
            conn.close()

            logger.info(
                f" Created UATP capsule {capsule.capsule_id} from Cursor session {session.session_id}"
            )
            return capsule.capsule_id

        except Exception as e:
            logger.error(f"[ERROR] Failed to create capsule from Cursor session: {e}")
            return None

    async def get_active_cursor_sessions(self) -> List[Dict[str, Any]]:
        """Get information about currently active Cursor sessions."""
        sessions = []
        for session_id, session in self.active_sessions.items():
            sessions.append(
                {
                    "session_id": session_id,
                    "user_id": session.user_id,
                    "project_path": session.project_path,
                    "project_name": Path(session.project_path).name,
                    "start_time": session.start_time.isoformat(),
                    "event_count": len(session.events),
                    "ai_interaction_count": len(session.ai_interactions),
                    "files_modified_count": len(session.files_modified),
                    "significance_score": await self.calculate_session_significance(
                        session
                    ),
                    "should_create_capsule": await self.should_create_capsule(session),
                }
            )
        return sessions


# Global Cursor capture instance
cursor_capture_system = CursorIDECapture()


# API functions for integration
async def start_cursor_capture_session(user_id: str, project_path: str) -> str:
    """Start a new Cursor IDE capture session."""
    return await cursor_capture_system.start_cursor_session(user_id, project_path)


async def capture_cursor_ai_interaction(
    session_id: str, user_query: str, ai_response: str, context: Dict[str, Any] = None
) -> str:
    """Capture AI interaction in Cursor IDE."""
    return await cursor_capture_system.capture_ai_interaction(
        session_id, user_query, ai_response, context
    )


async def capture_cursor_code_change(
    session_id: str,
    file_path: str,
    change_type: str,
    content: str,
    metadata: Dict[str, Any] = None,
) -> str:
    """Capture code changes in Cursor IDE."""
    return await cursor_capture_system.capture_code_change(
        session_id, file_path, change_type, content, metadata
    )


async def end_cursor_capture_session(session_id: str) -> Optional[str]:
    """End a Cursor IDE capture session and potentially create a capsule."""
    session = await cursor_capture_system.end_cursor_session(session_id)
    if session:
        capsule_id = await cursor_capture_system.create_capsule_from_cursor_session(
            session
        )
        return capsule_id
    return None


if __name__ == "__main__":
    # Test the Cursor capture system
    async def test_cursor_capture():
        logger.info(" Testing Cursor IDE capture system...")

        # Start a session
        session_id = await start_cursor_capture_session(
            "test-user", os.path.dirname(os.path.dirname(__file__))
        )

        # Simulate development workflow
        await capture_cursor_ai_interaction(
            session_id,
            "Help me implement a function to calculate significance scores",
            "Here's a function that calculates significance based on multiple factors...",
        )

        await capture_cursor_code_change(
            session_id,
            "/Users/kay/uatp-capsule-engine/src/significance.py",
            "create",
            "def calculate_significance(content, metadata): ...",
            {"lines_added": 15, "complexity": "medium"},
        )

        await capture_cursor_ai_interaction(
            session_id,
            "How can I optimize this for better performance?",
            "You can optimize by caching results and using vectorized operations...",
        )

        # End session and create capsule
        capsule_id = await end_cursor_capture_session(session_id)
        if capsule_id:
            logger.info(f"[OK] Test completed - Capsule created: {capsule_id}")
        else:
            logger.info(" Test completed - No capsule created (didn't meet criteria)")

    # Run test
    asyncio.run(test_cursor_capture())
