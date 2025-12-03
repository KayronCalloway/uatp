#!/usr/bin/env python3
"""
Database-Enabled Capsule Creator
================================

This module provides a database-enabled capsule creator that stores capsules
in PostgreSQL instead of JSONL files, while maintaining compatibility with
the universal filter system.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.database.connection import get_database_manager
from src.models.capsule import CapsuleModel
from src.capsule_schema import (
    ReasoningTraceCapsule,
    ReasoningTracePayload,
    ReasoningStep,
    Verification,
    CapsuleStatus,
)
from src.filters.capsule_creator import FilterCapsuleCreator
import uuid

logger = logging.getLogger(__name__)


@dataclass
class CapsuleStats:
    """Statistics for database capsule operations."""

    total_capsules: int
    auto_filtered_capsules: int
    database_size: int
    oldest_capsule: Optional[datetime]
    newest_capsule: Optional[datetime]
    platforms: Dict[str, int]
    significance_distribution: Dict[str, int]


class DatabaseCapsuleCreator:
    """
    Database-enabled capsule creator that stores capsules in PostgreSQL.
    Provides same interface as FilterCapsuleCreator but with database backend.
    """

    def __init__(self, fallback_to_jsonl: bool = True):
        self.fallback_to_jsonl = fallback_to_jsonl
        self.db_manager = get_database_manager()
        self.jsonl_creator = FilterCapsuleCreator() if fallback_to_jsonl else None
        self._db_connected = False

        logger.info("🗄️  Database Capsule Creator initialized")
        logger.info(f"   Fallback to JSONL: {fallback_to_jsonl}")

    async def initialize(self):
        """Initialize database connection."""
        try:
            if not self.db_manager._connected:
                await self.db_manager.connect()

            # Test database connection
            await self.db_manager.execute("SELECT 1")
            self._db_connected = True
            logger.info("✅ Database capsule creator connected to PostgreSQL")

        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            if not self.fallback_to_jsonl:
                raise
            logger.info("🔄 Falling back to JSONL storage")
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
        Create a capsule from a filter result using database storage.

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
                return await self._create_database_capsule(
                    filter_result, messages, user_id, platform, session_id
                )
            except Exception as e:
                logger.error(f"❌ Database capsule creation failed: {e}")
                if not self.fallback_to_jsonl:
                    raise
                logger.info("🔄 Falling back to JSONL storage")

        # Fallback to JSONL
        if self.jsonl_creator:
            return await self.jsonl_creator.create_capsule_from_filter_result(
                filter_result, messages, user_id, platform, session_id
            )

        raise RuntimeError("No storage backend available")

    async def _create_database_capsule(
        self,
        filter_result: Dict[str, Any],
        messages: List[Dict[str, Any]],
        user_id: str,
        platform: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a capsule in the database."""

        # Generate capsule ID
        capsule_id = f"db_filter_{platform}_{int(time.time())}_{str(uuid.uuid4())[:8]}"

        # Create reasoning steps from filter result
        reasoning_steps = []
        for factor in filter_result.get("reasoning", []):
            reasoning_steps.append(
                ReasoningStep(
                    content=factor,
                    step_type="significance_detection",
                    weight=0.1,
                    timestamp=datetime.now(timezone.utc),
                )
            )

        # Create reasoning trace payload
        reasoning_payload = ReasoningTracePayload(
            steps=reasoning_steps,
            parent_capsule_id=None,
            analysis_metadata={
                "filter_version": "1.0",
                "significance_score": filter_result.get("significance_score", 0.0),
                "confidence": filter_result.get("confidence", 0.8),
                "platform": platform,
                "user_id": user_id,
                "session_id": session_id,
                "conversation_length": len(messages),
                "auto_filtered": True,
            },
        )

        # Create full capsule
        capsule = ReasoningTraceCapsule(
            capsule_id=capsule_id,
            version="1.0",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.SEALED,
            verification=Verification(
                signer=f"{platform}-database-filter-system",
                verify_key="",
                hash="",
                signature="",
            ),
            reasoning_trace=reasoning_payload,
        )

        # Store in database
        async with self.db_manager.get_transaction() as conn:
            # Convert to database model
            capsule_model = CapsuleModel.from_pydantic(capsule)

            # Insert into database
            await conn.execute(
                """
                INSERT INTO capsules (
                    capsule_id, capsule_type, version, timestamp, status, 
                    verification, payload
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                capsule_model.capsule_id,
                capsule_model.capsule_type,
                capsule_model.version,
                capsule_model.timestamp,
                capsule_model.status,
                json.dumps(capsule_model.verification),
                json.dumps(capsule_model.payload),
            )

        # Create return data matching JSONL format
        capsule_data = {
            "capsule_id": capsule_id,
            "type": "reasoning_trace",
            "content": self._format_conversation_content(messages, platform),
            "input_data": self._extract_user_input(messages),
            "output": self._extract_ai_response(messages),
            "reasoning": [step.dict() for step in reasoning_steps],
            "model_version": f"{platform}-database-filter",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": f"{platform}-database-filter-system",
            "status": "SEALED",
            "metadata": {
                "interaction_type": f"{platform}_database_filtered",
                "session_id": session_id,
                "user_id": user_id,
                "filter_decision": filter_result.get("decision", "encapsulate"),
                "significance_score": filter_result.get("significance_score", 0.0),
                "confidence": filter_result.get("confidence", 0.8),
                "auto_encapsulated": True,
                "storage_backend": "postgresql",
                "filter_version": "1.0",
                "reasoning_factors": filter_result.get("reasoning", []),
                "platform_weight_applied": True,
                "conversation_length": len(messages),
                "created_by": "database_filter_system",
            },
        }

        logger.info(f"🗄️  Created database capsule: {capsule_id}")
        logger.info(f"   Platform: {platform}")
        logger.info(
            f"   Significance: {filter_result.get('significance_score', 0.0):.2f}"
        )
        logger.info(f"   Storage: PostgreSQL")

        return capsule_data

    def _format_conversation_content(
        self, messages: List[Dict[str, Any]], platform: str
    ) -> str:
        """Format conversation content for the capsule."""
        if not messages:
            return f"Database-filtered {platform} conversation"

        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if user_messages:
            first_msg = user_messages[0].get("content", "")
            if len(first_msg) > 100:
                summary = first_msg[:100] + "..."
            else:
                summary = first_msg
            return f"Database-filtered {platform.title()} interaction: {summary}"

        return f"Database-filtered {platform} conversation"

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

    async def get_capsule_stats(self) -> CapsuleStats:
        """Get statistics about capsules in the database."""

        if not self._db_connected:
            # Fallback to JSONL stats
            if self.jsonl_creator:
                jsonl_stats = self.jsonl_creator.get_chain_stats()
                return CapsuleStats(
                    total_capsules=jsonl_stats.get("total_capsules", 0),
                    auto_filtered_capsules=jsonl_stats.get("auto_filtered_capsules", 0),
                    database_size=jsonl_stats.get("file_size", 0),
                    oldest_capsule=None,
                    newest_capsule=None,
                    platforms={},
                    significance_distribution={},
                )
            return CapsuleStats(0, 0, 0, None, None, {}, {})

        try:
            async with self.db_manager.get_connection() as conn:
                # Total capsules
                total_count = await conn.fetchval("SELECT COUNT(*) FROM capsules")

                # Auto-filtered capsules
                auto_filtered_count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM capsules 
                    WHERE payload->>'analysis_metadata'->>'auto_filtered' = 'true'
                """
                )

                # Database size (approximate)
                db_size = await conn.fetchval(
                    """
                    SELECT pg_total_relation_size('capsules')
                """
                )

                # Oldest and newest capsules
                oldest = await conn.fetchval("SELECT MIN(timestamp) FROM capsules")
                newest = await conn.fetchval("SELECT MAX(timestamp) FROM capsules")

                # Platform distribution
                platform_stats = await conn.fetch(
                    """
                    SELECT 
                        payload->>'analysis_metadata'->>'platform' as platform,
                        COUNT(*) as count
                    FROM capsules 
                    WHERE payload->>'analysis_metadata'->>'platform' IS NOT NULL
                    GROUP BY platform
                """
                )

                platforms = {row["platform"]: row["count"] for row in platform_stats}

                # Significance distribution
                significance_stats = await conn.fetch(
                    """
                    SELECT 
                        CASE 
                            WHEN (payload->>'analysis_metadata'->>'significance_score')::float < 0.6 THEN 'low'
                            WHEN (payload->>'analysis_metadata'->>'significance_score')::float < 1.0 THEN 'medium'
                            WHEN (payload->>'analysis_metadata'->>'significance_score')::float < 2.0 THEN 'high'
                            ELSE 'very_high'
                        END as significance_level,
                        COUNT(*) as count
                    FROM capsules 
                    WHERE payload->>'analysis_metadata'->>'significance_score' IS NOT NULL
                    GROUP BY significance_level
                """
                )

                significance_distribution = {
                    row["significance_level"]: row["count"]
                    for row in significance_stats
                }

                return CapsuleStats(
                    total_capsules=total_count,
                    auto_filtered_capsules=auto_filtered_count,
                    database_size=db_size,
                    oldest_capsule=oldest,
                    newest_capsule=newest,
                    platforms=platforms,
                    significance_distribution=significance_distribution,
                )

        except Exception as e:
            logger.error(f"Error getting capsule stats: {e}")
            return CapsuleStats(0, 0, 0, None, None, {}, {})

    async def get_recent_capsules(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent capsules from the database."""

        if not self._db_connected:
            return []

        try:
            async with self.db_manager.get_connection() as conn:
                rows = await conn.fetch(
                    """
                    SELECT capsule_id, capsule_type, timestamp, payload
                    FROM capsules 
                    WHERE payload->>'analysis_metadata'->>'auto_filtered' = 'true'
                    ORDER BY timestamp DESC 
                    LIMIT $1
                """,
                    limit,
                )

                capsules = []
                for row in rows:
                    payload = json.loads(row["payload"])
                    analysis_metadata = payload.get("analysis_metadata", {})

                    capsules.append(
                        {
                            "capsule_id": row["capsule_id"],
                            "type": row["capsule_type"],
                            "timestamp": row["timestamp"].isoformat(),
                            "platform": analysis_metadata.get("platform", "unknown"),
                            "significance_score": analysis_metadata.get(
                                "significance_score", 0.0
                            ),
                            "user_id": analysis_metadata.get("user_id", "unknown"),
                            "session_id": analysis_metadata.get("session_id"),
                            "storage_backend": "postgresql",
                        }
                    )

                return capsules

        except Exception as e:
            logger.error(f"Error getting recent capsules: {e}")
            return []

    async def migrate_from_jsonl(self, jsonl_file: str) -> Dict[str, Any]:
        """Migrate existing JSONL capsules to database."""

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
            logger.info(f"🔄 Starting migration from {jsonl_file}")

            with open(jsonl_file, "r", encoding="utf-8") as f:
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
                        existing = await self.db_manager.fetchval(
                            "SELECT capsule_id FROM capsules WHERE capsule_id = $1",
                            capsule_id,
                        )

                        if existing:
                            migration_stats["skipped_duplicates"] += 1
                            continue

                        # Convert JSONL capsule to database format
                        await self._migrate_single_capsule(capsule_data)
                        migration_stats["successful_migrations"] += 1

                    except Exception as e:
                        migration_stats["failed_migrations"] += 1
                        migration_stats["errors"].append(
                            {"line": line_num, "error": str(e)}
                        )
                        logger.error(f"Migration error on line {line_num}: {e}")

            logger.info(f"✅ Migration completed:")
            logger.info(f"   Total processed: {migration_stats['total_processed']}")
            logger.info(f"   Successful: {migration_stats['successful_migrations']}")
            logger.info(f"   Failed: {migration_stats['failed_migrations']}")
            logger.info(f"   Skipped: {migration_stats['skipped_duplicates']}")

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            migration_stats["errors"].append({"error": str(e)})

        return migration_stats

    async def _migrate_single_capsule(self, jsonl_capsule: Dict[str, Any]):
        """Migrate a single JSONL capsule to database format."""

        # Extract basic information
        capsule_id = jsonl_capsule.get("capsule_id")
        capsule_type = jsonl_capsule.get("type", "reasoning_trace")

        # Convert timestamp
        timestamp_str = jsonl_capsule.get("timestamp")
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            timestamp = datetime.now(timezone.utc)

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
            },
        }

        # Insert into database
        async with self.db_manager.get_transaction() as conn:
            await conn.execute(
                """
                INSERT INTO capsules (
                    capsule_id, capsule_type, version, timestamp, status, 
                    verification, payload
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                capsule_id,
                capsule_type,
                "1.0",
                timestamp,
                jsonl_capsule.get("status", "SEALED"),
                json.dumps(verification),
                json.dumps(payload),
            )


# Global instance
_database_capsule_creator = None


def get_database_capsule_creator() -> DatabaseCapsuleCreator:
    """Get the global database capsule creator instance."""
    global _database_capsule_creator
    if _database_capsule_creator is None:
        _database_capsule_creator = DatabaseCapsuleCreator()
    return _database_capsule_creator


async def initialize_database_capsule_creator():
    """Initialize the database capsule creator."""
    creator = get_database_capsule_creator()
    await creator.initialize()
    return creator
