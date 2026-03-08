#!/usr/bin/env python3
"""
SQLite Database Capsule Creator
===============================

This module provides a SQLite-compatible capsule creator that stores capsules
in the SQLite database instead of JSONL files.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text

from src.core.database import db
from src.filters.capsule_creator import FilterCapsuleCreator

logger = logging.getLogger(__name__)


class SQLiteCapsuleCreator:
    """
    SQLite-compatible capsule creator for the universal filter system.
    """

    def __init__(self, fallback_to_jsonl: bool = True):
        self.fallback_to_jsonl = fallback_to_jsonl
        self.jsonl_creator = FilterCapsuleCreator() if fallback_to_jsonl else None
        self._db_connected = False

        logger.info(" SQLite Capsule Creator initialized")
        logger.info(f"   Fallback to JSONL: {fallback_to_jsonl}")

    async def initialize(self):
        """Initialize database connection."""
        try:
            # Initialize database
            db.init_app(None)

            # Test database connection
            async with db.get_session() as session:
                await session.execute(text("SELECT 1"))

            self._db_connected = True
            logger.info("[OK] SQLite capsule creator connected to database")

        except Exception as e:
            logger.error(f"[ERROR] Database connection failed: {e}")
            if not self.fallback_to_jsonl:
                raise
            logger.info(" Falling back to JSONL storage")
            self._db_connected = False

    async def create_capsule_from_filter_result(
        self,
        filter_result: Dict[str, Any],
        messages: List[Dict[str, Any]],
        user_id: str,
        platform: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a capsule from a filter result using SQLite storage.

        Args:
            filter_result: Result from the universal filter
            messages: Conversation messages
            user_id: User identifier
            platform: Platform name
            session_id: Session identifier

        Returns:
            Created capsule data
        """

        # Try database first
        if self._db_connected:
            try:
                return await self._create_sqlite_capsule(
                    filter_result, messages, user_id, platform, session_id
                )
            except Exception as e:
                logger.error(f"[ERROR] SQLite capsule creation failed: {e}")
                if not self.fallback_to_jsonl:
                    raise
                logger.info(" Falling back to JSONL storage")

        # Fallback to JSONL
        if self.jsonl_creator:
            return await self.jsonl_creator.create_capsule_from_filter_result(
                filter_result, messages, user_id, platform, session_id
            )

        raise RuntimeError("No storage backend available")

    async def _create_sqlite_capsule(
        self,
        filter_result: Dict[str, Any],
        messages: List[Dict[str, Any]],
        user_id: str,
        platform: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a capsule in SQLite database."""

        # Generate capsule ID
        capsule_id = (
            f"sqlite_filter_{platform}_{int(time.time())}_{str(time.time())[-4:]}"
        )

        # Create reasoning steps from filter result
        reasoning_steps = []
        for factor in filter_result.get("reasoning", []):
            reasoning_steps.append(
                {
                    "step_type": "significance_detection",
                    "content": factor,
                    "weight": 0.1,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Create capsule payload
        payload = {
            "steps": reasoning_steps,
            "parent_capsule_id": None,
            "analysis_metadata": {
                "filter_version": "1.0",
                "significance_score": filter_result.get("significance_score", 0.0),
                "confidence": filter_result.get("confidence", 0.8),
                "platform": platform,
                "user_id": user_id,
                "session_id": session_id,
                "conversation_length": len(messages),
                "auto_filtered": True,
                "storage_backend": "sqlite",
            },
        }

        # Create verification object
        verification = {
            "signer": f"{platform}-sqlite-filter-system",
            "verify_key": "",
            "hash": "",
            "signature": "",
        }

        # Store in database
        async with db.get_session() as session:
            await session.execute(
                text(
                    """
                INSERT INTO capsules_filter (
                    capsule_id, capsule_type, version, timestamp, status,
                    verification, payload
                ) VALUES (:capsule_id, :capsule_type, :version, :timestamp, :status, :verification, :payload)
            """
                ),
                {
                    "capsule_id": capsule_id,
                    "capsule_type": "reasoning_trace",
                    "version": "1.0",
                    "timestamp": datetime.now().isoformat(),
                    "status": "SEALED",
                    "verification": json.dumps(verification),
                    "payload": json.dumps(payload),
                },
            )

            # Also create attribution record
            await session.execute(
                text(
                    """
                INSERT INTO attributions_filter (
                    user_id, conversation_id, capsule_id, platform,
                    significance_score, timestamp, metadata
                ) VALUES (:user_id, :conversation_id, :capsule_id, :platform, :significance_score, :timestamp, :metadata)
            """
                ),
                {
                    "user_id": user_id,
                    "conversation_id": session_id or f"session_{int(time.time())}",
                    "capsule_id": capsule_id,
                    "platform": platform,
                    "significance_score": filter_result.get("significance_score", 0.0),
                    "timestamp": datetime.now().isoformat(),
                    "metadata": json.dumps(
                        {
                            "filter_decision": filter_result.get(
                                "decision", "encapsulate"
                            ),
                            "reasoning_factors": filter_result.get("reasoning", []),
                            "confidence": filter_result.get("confidence", 0.8),
                        }
                    ),
                },
            )

            await session.commit()

        # Create return data matching JSONL format
        capsule_data = {
            "capsule_id": capsule_id,
            "type": "reasoning_trace",
            "content": self._format_conversation_content(messages, platform),
            "input_data": self._extract_user_input(messages),
            "output": self._extract_ai_response(messages),
            "reasoning": reasoning_steps,
            "model_version": f"{platform}-sqlite-filter",
            "timestamp": datetime.now().isoformat(),
            "agent_id": f"{platform}-sqlite-filter-system",
            "status": "SEALED",
            "metadata": {
                "interaction_type": f"{platform}_sqlite_filtered",
                "session_id": session_id,
                "user_id": user_id,
                "filter_decision": filter_result.get("decision", "encapsulate"),
                "significance_score": filter_result.get("significance_score", 0.0),
                "confidence": filter_result.get("confidence", 0.8),
                "auto_encapsulated": True,
                "storage_backend": "sqlite",
                "filter_version": "1.0",
                "reasoning_factors": filter_result.get("reasoning", []),
                "platform_weight_applied": True,
                "conversation_length": len(messages),
                "created_by": "sqlite_filter_system",
            },
        }

        logger.info(f" Created SQLite capsule: {capsule_id}")
        logger.info(f"   Platform: {platform}")
        logger.info(
            f"   Significance: {filter_result.get('significance_score', 0.0):.2f}"
        )
        logger.info("   Storage: SQLite")

        return capsule_data

    def _format_conversation_content(
        self, messages: List[Dict[str, Any]], platform: str
    ) -> str:
        """Format conversation content for the capsule."""
        if not messages:
            return f"SQLite-filtered {platform} conversation"

        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if user_messages:
            first_msg = user_messages[0].get("content", "")
            if len(first_msg) > 100:
                summary = first_msg[:100] + "..."
            else:
                summary = first_msg
            return f"SQLite-filtered {platform.title()} interaction: {summary}"

        return f"SQLite-filtered {platform} conversation"

    def _extract_user_input(self, messages: List[Dict[str, Any]]) -> str:
        """Extract user input from conversation."""
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if user_messages:
            return user_messages[-1].get("content", "")
        return ""

    def _extract_ai_response(self, messages: List[Dict[str, Any]]) -> str:
        """Extract AI response from conversation."""
        ai_messages = [msg for msg in messages if msg.get("role") == "assistant"]
        if ai_messages:
            return ai_messages[-1].get("content", "")
        return ""

    async def get_capsule_stats(self) -> Dict[str, Any]:
        """Get statistics about capsules in SQLite database."""

        if not self._db_connected:
            # Fallback to JSONL stats
            if self.jsonl_creator:
                return self.jsonl_creator.get_chain_stats()
            return {
                "total_capsules": 0,
                "auto_filtered_capsules": 0,
                "database_size": 0,
                "storage_backend": "none",
            }

        try:
            async with db.get_session() as session:
                # Total capsules
                result = await session.execute(
                    text("SELECT COUNT(*) FROM capsules_filter")
                )
                total_count = result.scalar()

                # Auto-filtered capsules (all in this table are auto-filtered)
                auto_filtered_count = total_count

                # Platform distribution
                result = await session.execute(
                    text(
                        """
                    SELECT platform, COUNT(*) as count
                    FROM attributions_filter
                    GROUP BY platform
                """
                    )
                )

                platforms = {}
                for row in result.fetchall():
                    platforms[row[0]] = row[1]

                # Database size
                db_path = "./uatp_dev.db"
                db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

                return {
                    "total_capsules": total_count,
                    "auto_filtered_capsules": auto_filtered_count,
                    "database_size": db_size,
                    "platforms": platforms,
                    "storage_backend": "sqlite",
                }

        except Exception as e:
            logger.error(f"Error getting capsule stats: {e}")
            return {
                "total_capsules": 0,
                "auto_filtered_capsules": 0,
                "database_size": 0,
                "storage_backend": "sqlite_error",
            }

    async def get_recent_capsules(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent capsules from SQLite database."""

        if not self._db_connected:
            return []

        try:
            async with db.get_session() as session:
                result = await session.execute(
                    text(
                        """
                    SELECT c.capsule_id, c.capsule_type, c.timestamp, c.payload, a.platform, a.significance_score
                    FROM capsules_filter c
                    JOIN attributions_filter a ON c.capsule_id = a.capsule_id
                    ORDER BY c.timestamp DESC
                    LIMIT :limit
                """
                    ),
                    {"limit": limit},
                )

                capsules = []
                for row in result.fetchall():
                    payload = json.loads(row[3])
                    analysis_metadata = payload.get("analysis_metadata", {})

                    capsules.append(
                        {
                            "capsule_id": row[0],
                            "type": row[1],
                            "timestamp": row[2],
                            "platform": row[4],
                            "significance_score": row[5],
                            "user_id": analysis_metadata.get("user_id", "unknown"),
                            "session_id": analysis_metadata.get("session_id"),
                            "storage_backend": "sqlite",
                        }
                    )

                return capsules

        except Exception as e:
            logger.error(f"Error getting recent capsules: {e}")
            return []

    async def migrate_from_jsonl(self, jsonl_file: str) -> Dict[str, Any]:
        """Migrate existing JSONL capsules to SQLite database."""

        if not self._db_connected:
            raise RuntimeError("Database not connected")

        migration_stats = {
            "total_processed": 0,
            "successful_migrations": 0,
            "failed_migrations": 0,
            "skipped_duplicates": 0,
            "errors": [],
        }

        try:
            logger.info(f" Starting SQLite migration from {jsonl_file}")

            with open(jsonl_file, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue

                    migration_stats["total_processed"] += 1

                    try:
                        capsule_data = json.loads(line)
                        capsule_id = capsule_data.get("capsule_id")

                        if not capsule_id:
                            migration_stats["failed_migrations"] += 1
                            continue

                        # Check if capsule already exists
                        async with db.get_session() as session:
                            result = await session.execute(
                                text(
                                    "SELECT capsule_id FROM capsules_filter WHERE capsule_id = :capsule_id"
                                ),
                                {"capsule_id": capsule_id},
                            )

                            if result.fetchone():
                                migration_stats["skipped_duplicates"] += 1
                                continue

                        # Convert JSONL capsule to SQLite format
                        await self._migrate_single_capsule(capsule_data)
                        migration_stats["successful_migrations"] += 1

                    except Exception as e:
                        migration_stats["failed_migrations"] += 1
                        migration_stats["errors"].append(
                            {"line": line_num, "error": str(e)}
                        )
                        logger.error(f"Migration error on line {line_num}: {e}")

            logger.info("[OK] SQLite migration completed:")
            logger.info(f"   Total processed: {migration_stats['total_processed']}")
            logger.info(f"   Successful: {migration_stats['successful_migrations']}")
            logger.info(f"   Failed: {migration_stats['failed_migrations']}")
            logger.info(f"   Skipped: {migration_stats['skipped_duplicates']}")

        except Exception as e:
            logger.error(f"[ERROR] SQLite migration failed: {e}")
            migration_stats["errors"].append({"error": str(e)})

        return migration_stats

    async def _migrate_single_capsule(self, jsonl_capsule: Dict[str, Any]):
        """Migrate a single JSONL capsule to SQLite format."""

        capsule_id = jsonl_capsule.get("capsule_id")
        capsule_type = jsonl_capsule.get("type", "reasoning_trace")

        # Convert timestamp
        timestamp_str = jsonl_capsule.get("timestamp")
        if timestamp_str:
            timestamp = timestamp_str
        else:
            timestamp = datetime.now().isoformat()

        # Create verification object
        verification = {
            "signer": jsonl_capsule.get("agent_id", "unknown"),
            "verify_key": "",
            "hash": "",
            "signature": "",
        }

        # Create payload from JSONL data
        payload = {
            "steps": jsonl_capsule.get("reasoning", []),
            "parent_capsule_id": None,
            "analysis_metadata": {
                "filter_version": "1.0",
                "significance_score": jsonl_capsule.get("metadata", {}).get(
                    "significance_score", 0.0
                ),
                "confidence": jsonl_capsule.get("metadata", {}).get("confidence", 0.8),
                "platform": jsonl_capsule.get("metadata", {}).get(
                    "platform", "unknown"
                ),
                "user_id": jsonl_capsule.get("metadata", {}).get("user_id", "unknown"),
                "session_id": jsonl_capsule.get("metadata", {}).get("session_id"),
                "conversation_length": jsonl_capsule.get("metadata", {}).get(
                    "conversation_length", 0
                ),
                "auto_filtered": jsonl_capsule.get("metadata", {}).get(
                    "auto_encapsulated", False
                ),
                "migrated_from_jsonl": True,
                "storage_backend": "sqlite",
            },
        }

        # Insert into database
        async with db.get_session() as session:
            await session.execute(
                text(
                    """
                INSERT INTO capsules_filter (
                    capsule_id, capsule_type, version, timestamp, status,
                    verification, payload
                ) VALUES (:capsule_id, :capsule_type, :version, :timestamp, :status, :verification, :payload)
            """
                ),
                {
                    "capsule_id": capsule_id,
                    "capsule_type": capsule_type,
                    "version": "1.0",
                    "timestamp": timestamp,
                    "status": jsonl_capsule.get("status", "SEALED"),
                    "verification": json.dumps(verification),
                    "payload": json.dumps(payload),
                },
            )

            # Also create attribution record
            metadata = jsonl_capsule.get("metadata", {})
            await session.execute(
                text(
                    """
                INSERT INTO attributions_filter (
                    user_id, conversation_id, capsule_id, platform,
                    significance_score, timestamp, metadata
                ) VALUES (:user_id, :conversation_id, :capsule_id, :platform, :significance_score, :timestamp, :metadata)
            """
                ),
                {
                    "user_id": metadata.get("user_id", "unknown"),
                    "conversation_id": metadata.get(
                        "session_id", f"migrated_{int(time.time())}"
                    ),
                    "capsule_id": capsule_id,
                    "platform": metadata.get("platform", "unknown"),
                    "significance_score": metadata.get("significance_score", 0.0),
                    "timestamp": timestamp,
                    "metadata": json.dumps(
                        {"migrated_from_jsonl": True, "original_metadata": metadata}
                    ),
                },
            )

            await session.commit()


# Global instance
_sqlite_capsule_creator = None


def get_sqlite_capsule_creator() -> SQLiteCapsuleCreator:
    """Get the global SQLite capsule creator instance."""
    global _sqlite_capsule_creator
    if _sqlite_capsule_creator is None:
        _sqlite_capsule_creator = SQLiteCapsuleCreator()
    return _sqlite_capsule_creator


async def initialize_sqlite_capsule_creator():
    """Initialize the SQLite capsule creator."""
    creator = get_sqlite_capsule_creator()
    await creator.initialize()
    return creator
