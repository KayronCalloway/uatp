#!/usr/bin/env python3
"""
Enhanced Universal Auto-Capture System
Consolidates and improves all UATP auto-capture mechanisms with advanced significance detection
"""

import asyncio
import hashlib
import json
import logging
import os
import sqlite3

# Add parent directory to path for imports
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

sys.path.append(str(Path(__file__).parent.parent))

from src.integrations.cursor_ide_capture import cursor_capture_system
from src.live_capture.claude_code_capture import capture_system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), "enhanced_auto_capture.log")
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class EnhancedSignificanceEngine:
    """Advanced significance detection engine for automatic capture decisions."""

    def __init__(self):
        self.significance_cache = {}
        self.learning_data = []
        self.thresholds = {
            "auto_capture": 0.6,
            "high_priority": 0.8,
            "capsule_creation": 0.7,
            "immediate_process": 0.9,
        }

        # Enhanced keyword sets with weights
        self.technical_keywords = {
            # High significance (weight: 0.4)
            "implement": 0.4,
            "architecture": 0.4,
            "algorithm": 0.4,
            "optimize": 0.4,
            "debug": 0.4,
            "refactor": 0.4,
            "design": 0.4,
            "system": 0.4,
            # Medium significance (weight: 0.3)
            "function": 0.3,
            "class": 0.3,
            "method": 0.3,
            "api": 0.3,
            "database": 0.3,
            "server": 0.3,
            "client": 0.3,
            "network": 0.3,
            # AI/ML specific (weight: 0.5)
            "uatp": 0.5,
            "capsule": 0.5,
            "attribution": 0.5,
            "ai": 0.3,
            "machine learning": 0.4,
            "neural": 0.3,
            "model": 0.3,
            "training": 0.3,
            # Development workflow (weight: 0.3)
            "test": 0.2,
            "deploy": 0.3,
            "build": 0.2,
            "configure": 0.2,
            "setup": 0.2,
            "install": 0.2,
            "version": 0.1,
            "update": 0.2,
        }

        self.code_patterns = {
            "```": 0.4,  # Code blocks
            "def ": 0.3,
            "function ": 0.3,
            "class ": 0.3,
            "async ": 0.3,
            "await ": 0.3,
            "import ": 0.2,
            "from ": 0.2,
            "if __name__": 0.3,
            "#!/usr/bin": 0.2,
        }

        self.complexity_indicators = {
            "error": 0.3,
            "exception": 0.3,
            "bug": 0.3,
            "issue": 0.3,
            "problem": 0.3,
            "solution": 0.4,
            "fix": 0.3,
            "performance": 0.3,
            "optimization": 0.4,
            "efficiency": 0.3,
            "scalability": 0.4,
            "architecture": 0.4,
            "design pattern": 0.4,
        }

    def calculate_content_significance(
        self, content: str, metadata: Dict[str, Any] = None
    ) -> float:
        """Calculate significance score for text content."""
        if not content or len(content.strip()) < 20:
            return 0.0

        content_lower = content.lower()
        score = 0.0

        # 1. Technical keyword analysis
        for keyword, weight in self.technical_keywords.items():
            if keyword in content_lower:
                score += weight

        # 2. Code pattern detection
        for pattern, weight in self.code_patterns.items():
            if pattern in content:
                score += weight

        # 3. Complexity indicators
        for indicator, weight in self.complexity_indicators.items():
            if indicator in content_lower:
                score += weight

        # 4. Length and structure bonus
        if len(content) > 200:
            score += 0.2
        if len(content) > 500:
            score += 0.3
        if len(content) > 1000:
            score += 0.4

        # 5. Question-answer pattern bonus
        if "?" in content:
            score += 0.1

        # 6. URL/reference bonus
        if (
            "http" in content
            or "github" in content_lower
            or "stackoverflow" in content_lower
        ):
            score += 0.2

        # 7. Metadata factors
        if metadata:
            # Platform-specific bonuses
            platform = metadata.get("platform", "").lower()
            if "cursor" in platform or "vscode" in platform:
                score += 0.2  # Development-focused platforms

            # Source-specific bonuses
            source = metadata.get("source", "").lower()
            if "ai_interaction" in source or "code_change" in source:
                score += 0.3

            # Session duration bonus
            duration = metadata.get("session_duration", 0)
            if duration > 300:  # 5+ minutes
                score += 0.2

            # File type bonus
            file_ext = metadata.get("file_extension", "").lower()
            important_extensions = [
                ".py",
                ".js",
                ".ts",
                ".tsx",
                ".jsx",
                ".cpp",
                ".java",
                ".go",
                ".rs",
            ]
            if file_ext in important_extensions:
                score += 0.3

        # 8. Normalize to 0-1 range
        normalized_score = min(score / 5.0, 1.0)

        # Cache result for learning
        content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        self.significance_cache[content_hash] = normalized_score

        return normalized_score

    def calculate_conversation_significance(
        self, messages: List[Dict], metadata: Dict[str, Any] = None
    ) -> float:
        """Calculate significance for entire conversation."""
        if not messages:
            return 0.0

        # Individual message scores
        message_scores = []
        for msg in messages:
            content = msg.get("content", "")
            msg_metadata = {**(metadata or {}), **msg.get("metadata", {})}
            score = self.calculate_content_significance(content, msg_metadata)
            message_scores.append(score)

        # Base score from average
        avg_score = sum(message_scores) / len(message_scores)

        # Conversation-level bonuses
        bonus = 0.0

        # Multi-turn conversation bonus
        if len(messages) >= 3:
            bonus += 0.2
        if len(messages) >= 6:
            bonus += 0.3

        # User-assistant interaction pattern
        roles = [msg.get("role", "") for msg in messages]
        if "user" in roles and "assistant" in roles:
            bonus += 0.3

        # Technical discussion pattern
        technical_exchanges = 0
        for i in range(len(messages) - 1):
            if (
                messages[i].get("role") == "user"
                and messages[i + 1].get("role") == "assistant"
                and self.calculate_content_significance(messages[i].get("content", ""))
                > 0.5
            ):
                technical_exchanges += 1

        if technical_exchanges >= 2:
            bonus += 0.4

        # Metadata bonuses
        if metadata:
            # Platform-specific
            platform = metadata.get("platform", "").lower()
            if any(p in platform for p in ["cursor", "vscode", "claude-code"]):
                bonus += 0.2

            # Duration bonus
            duration = metadata.get("duration_minutes", 0)
            if duration > 10:
                bonus += 0.3

            # Token count bonus
            tokens = metadata.get("total_tokens", 0)
            if tokens > 500:
                bonus += 0.2

        final_score = min(avg_score + bonus, 1.0)
        return final_score

    def should_auto_capture(
        self,
        content: str = None,
        messages: List[Dict] = None,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Determine if content should be auto-captured and at what priority."""

        if messages:
            significance = self.calculate_conversation_significance(messages, metadata)
        elif content:
            significance = self.calculate_content_significance(content, metadata)
        else:
            return {"capture": False, "reason": "No content provided"}

        decision = {
            "capture": significance >= self.thresholds["auto_capture"],
            "create_capsule": significance >= self.thresholds["capsule_creation"],
            "high_priority": significance >= self.thresholds["high_priority"],
            "immediate_process": significance >= self.thresholds["immediate_process"],
            "significance_score": significance,
            "reason": self._get_significance_reason(significance),
        }

        return decision

    def _get_significance_reason(self, score: float) -> str:
        """Get human-readable reason for significance score."""
        if score >= 0.9:
            return "Extremely significant: Complex technical discussion with high implementation value"
        elif score >= 0.8:
            return "Highly significant: Advanced technical content requiring expert knowledge"
        elif score >= 0.7:
            return "Very significant: Technical implementation or problem-solving discussion"
        elif score >= 0.6:
            return "Significant: Technical content with development insights"
        elif score >= 0.4:
            return (
                "Moderately significant: Technical references or basic implementation"
            )
        elif score >= 0.2:
            return "Low significance: Some technical content but limited depth"
        else:
            return (
                "Minimal significance: General discussion with minimal technical value"
            )


class UniversalAutoCapture:
    """Universal auto-capture system that integrates all capture methods."""

    def __init__(self):
        self.significance_engine = EnhancedSignificanceEngine()
        self.active_monitors = {}
        self.capture_stats = {
            "total_captured": 0,
            "auto_captured": 0,
            "capsules_created": 0,
            "high_priority_captures": 0,
            "last_capture": None,
        }
        self.api_base = "http://localhost:8000"
        self.running = False

        # Initialize database for tracking
        self.db_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "auto_capture_tracking.db"
        )
        self.init_tracking_database()

        logger.info(" Enhanced Universal Auto-Capture System initialized")

    def init_tracking_database(self):
        """Initialize tracking database for auto-capture analytics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS auto_captures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    platform TEXT,
                    significance_score REAL,
                    decision_reason TEXT,
                    content_preview TEXT,
                    metadata TEXT,
                    capsule_created BOOLEAN DEFAULT FALSE,
                    capsule_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS capture_analytics (
                    date TEXT PRIMARY KEY,
                    total_captures INTEGER,
                    auto_captures INTEGER,
                    significance_avg REAL,
                    capsules_created INTEGER,
                    top_platforms TEXT
                )
            """
            )

            conn.commit()
            conn.close()
            logger.info("[OK] Auto-capture tracking database initialized")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize tracking database: {e}")

    async def process_content(
        self,
        content: str,
        source: str,
        platform: str = None,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Process content through enhanced significance engine."""

        # Enhance metadata with context
        enhanced_metadata = {
            "source": source,
            "platform": platform or "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content_length": len(content) if content else 0,
            **(metadata or {}),
        }

        # Get significance decision
        decision = self.significance_engine.should_auto_capture(
            content=content, metadata=enhanced_metadata
        )

        # Log decision
        self.log_capture_decision(content, decision, enhanced_metadata)

        # Auto-capture if significant
        if decision["capture"]:
            result = await self.auto_capture_content(
                content, enhanced_metadata, decision
            )
            decision["capture_result"] = result

        return decision

    async def process_conversation(
        self,
        messages: List[Dict],
        source: str,
        platform: str = None,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Process conversation through enhanced significance engine."""

        # Enhance metadata with conversation context
        enhanced_metadata = {
            "source": source,
            "platform": platform or "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message_count": len(messages),
            "total_length": sum(len(msg.get("content", "")) for msg in messages),
            **(metadata or {}),
        }

        # Get significance decision
        decision = self.significance_engine.should_auto_capture(
            messages=messages, metadata=enhanced_metadata
        )

        # Log decision
        content_preview = f"{len(messages)} messages: " + " | ".join(
            [
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')[:50]}..."
                for msg in messages[:2]
            ]
        )
        self.log_capture_decision(content_preview, decision, enhanced_metadata)

        # Auto-capture if significant
        if decision["capture"]:
            result = await self.auto_capture_conversation(
                messages, enhanced_metadata, decision
            )
            decision["capture_result"] = result

        return decision

    async def auto_capture_content(
        self, content: str, metadata: Dict[str, Any], decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Automatically capture significant content."""
        try:
            # Determine capture method based on source
            source = metadata.get("source", "unknown")
            platform = metadata.get("platform", "unknown")

            if "cursor" in source.lower():
                # Use Cursor IDE capture system
                session_id = await cursor_capture_system.start_cursor_session(
                    user_id=metadata.get("user_id", "auto-user"),
                    project_path=metadata.get("project_path", "/tmp/auto-capture"),
                )

                await cursor_capture_system.capture_code_change(
                    session_id=session_id,
                    file_path=metadata.get("file_path", "auto_capture.txt"),
                    change_type="auto_capture",
                    content=content,
                    metadata=metadata,
                )

                result = {
                    "success": True,
                    "method": "cursor_capture",
                    "session_id": session_id,
                }

            else:
                # Use general live capture system
                session_id = await capture_system.start_session(
                    user_id=metadata.get("user_id", "auto-user")
                )

                await capture_system.capture_message(
                    session_id=session_id,
                    role="user",
                    content=content,
                    metadata=metadata,
                )

                result = {
                    "success": True,
                    "method": "live_capture",
                    "session_id": session_id,
                }

            # Create capsule if highly significant
            if decision.get("create_capsule", False):
                # Implementation depends on capture method
                result["capsule_eligible"] = True

                # Update stats
                self.capture_stats["capsules_created"] += 1

            # Update stats
            self.capture_stats["auto_captured"] += 1
            self.capture_stats["total_captured"] += 1
            self.capture_stats["last_capture"] = datetime.now().isoformat()

            if decision.get("high_priority", False):
                self.capture_stats["high_priority_captures"] += 1

            logger.info(
                f"[OK] Auto-captured {source} content (significance: {decision['significance_score']:.2f})"
            )
            return result

        except Exception as e:
            logger.error(f"[ERROR] Auto-capture failed: {e}")
            return {"success": False, "error": str(e)}

    async def auto_capture_conversation(
        self, messages: List[Dict], metadata: Dict[str, Any], decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Automatically capture significant conversation."""
        try:
            # Start capture session
            session_id = await capture_system.start_session(
                user_id=metadata.get("user_id", "auto-user")
            )

            # Capture all messages
            for msg in messages:
                await capture_system.capture_message(
                    session_id=session_id,
                    role=msg.get("role", "user"),
                    content=msg.get("content", ""),
                    metadata={**metadata, **msg.get("metadata", {})},
                )

            # End session and potentially create capsule
            if decision.get("create_capsule", False):
                completed_session = await capture_system.end_session(session_id)
                capsule_id = await capture_system.create_capsule_from_session(
                    completed_session
                )

                if capsule_id:
                    self.capture_stats["capsules_created"] += 1
                    result = {
                        "success": True,
                        "method": "conversation_capture",
                        "session_id": session_id,
                        "capsule_id": capsule_id,
                    }
                else:
                    result = {
                        "success": True,
                        "method": "conversation_capture",
                        "session_id": session_id,
                        "capsule_eligible": False,
                    }
            else:
                result = {
                    "success": True,
                    "method": "conversation_capture",
                    "session_id": session_id,
                }

            # Update stats
            self.capture_stats["auto_captured"] += 1
            self.capture_stats["total_captured"] += 1
            self.capture_stats["last_capture"] = datetime.now().isoformat()

            if decision.get("high_priority", False):
                self.capture_stats["high_priority_captures"] += 1

            logger.info(
                f"[OK] Auto-captured conversation with {len(messages)} messages (significance: {decision['significance_score']:.2f})"
            )
            return result

        except Exception as e:
            logger.error(f"[ERROR] Conversation auto-capture failed: {e}")
            return {"success": False, "error": str(e)}

    def log_capture_decision(
        self, content_preview: str, decision: Dict[str, Any], metadata: Dict[str, Any]
    ):
        """Log capture decision for analytics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO auto_captures
                (timestamp, source, platform, significance_score, decision_reason,
                 content_preview, metadata, capsule_created)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now().isoformat(),
                    metadata.get("source", "unknown"),
                    metadata.get("platform", "unknown"),
                    decision.get("significance_score", 0.0),
                    decision.get("reason", ""),
                    content_preview[:200] + "..."
                    if len(content_preview) > 200
                    else content_preview,
                    json.dumps(metadata),
                    decision.get("create_capsule", False),
                ),
            )

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[ERROR] Failed to log capture decision: {e}")

    def get_capture_analytics(self) -> Dict[str, Any]:
        """Get analytics about auto-capture performance."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get recent captures
            cursor.execute(
                """
                SELECT source, platform, significance_score, decision_reason, timestamp
                FROM auto_captures
                ORDER BY timestamp DESC
                LIMIT 20
            """
            )
            recent_captures = cursor.fetchall()

            # Get daily stats
            cursor.execute(
                """
                SELECT DATE(timestamp) as date,
                       COUNT(*) as captures,
                       AVG(significance_score) as avg_significance,
                       SUM(CASE WHEN capsule_created THEN 1 ELSE 0 END) as capsules
                FROM auto_captures
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """
            )
            daily_stats = cursor.fetchall()

            conn.close()

            return {
                "current_stats": self.capture_stats,
                "recent_captures": [
                    {
                        "source": row[0],
                        "platform": row[1],
                        "significance": row[2],
                        "reason": row[3],
                        "timestamp": row[4],
                    }
                    for row in recent_captures
                ],
                "daily_stats": [
                    {
                        "date": row[0],
                        "captures": row[1],
                        "avg_significance": row[2],
                        "capsules": row[3],
                    }
                    for row in daily_stats
                ],
            }
        except Exception as e:
            logger.error(f"[ERROR] Failed to get analytics: {e}")
            return {"current_stats": self.capture_stats}


# Global instance
universal_auto_capture = UniversalAutoCapture()


# API functions for integration
async def analyze_content_significance(
    content: str,
    source: str = "unknown",
    platform: str = None,
    metadata: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Analyze content significance and auto-capture if warranted."""
    return await universal_auto_capture.process_content(
        content, source, platform, metadata
    )


async def analyze_conversation_significance(
    messages: List[Dict],
    source: str = "unknown",
    platform: str = None,
    metadata: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Analyze conversation significance and auto-capture if warranted."""
    return await universal_auto_capture.process_conversation(
        messages, source, platform, metadata
    )


def get_auto_capture_analytics() -> Dict[str, Any]:
    """Get auto-capture analytics and performance metrics."""
    return universal_auto_capture.get_capture_analytics()


if __name__ == "__main__":
    # Test the enhanced system
    async def test_enhanced_capture():
        logger.info(" Testing Enhanced Universal Auto-Capture System...")

        # Test content significance
        test_content = """
        I need to implement a UATP capsule creation system that automatically detects
        significant conversations and creates attribution capsules. Here's my approach:

        ```python
        def create_capsule_from_conversation(conversation):
            significance = calculate_significance_score(conversation)
            if significance >= 0.7:
                return create_attribution_capsule(conversation)
            return None
        ```

        The system should use machine learning to improve its detection over time.
        """

        decision = await analyze_content_significance(
            content=test_content,
            source="test",
            platform="claude-code",
            metadata={"user_id": "test-user", "file_path": "test.py"},
        )

        print(f"[OK] Content significance analysis: {decision}")

        # Test conversation significance
        test_messages = [
            {
                "role": "user",
                "content": "How do I implement real-time UATP attribution?",
            },
            {
                "role": "assistant",
                "content": "To implement real-time UATP attribution, you need to capture conversations as they happen and analyze their significance...",
            },
            {
                "role": "user",
                "content": "Can you show me the code for the significance scoring algorithm?",
            },
            {
                "role": "assistant",
                "content": "Here's a comprehensive significance scoring implementation:\n\n```python\ndef calculate_significance(messages):\n    # Implementation here\n    return score\n```",
            },
        ]

        decision = await analyze_conversation_significance(
            messages=test_messages,
            source="test",
            platform="claude-code",
            metadata={"session_duration": 600, "total_tokens": 1500},
        )

        print(f"[OK] Conversation significance analysis: {decision}")

        # Show analytics
        analytics = get_auto_capture_analytics()
        print(f"[OK] Analytics: {analytics}")

    # Run test
    asyncio.run(test_enhanced_capture())
