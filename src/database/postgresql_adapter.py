#!/usr/bin/env python3
"""
PostgreSQL Adapter for UATP Capsule Engine
==========================================

This module provides a PostgreSQL adapter that implements the same interface
as the existing database modules, enabling seamless migration from SQLite.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from database.postgresql_schema import get_postgresql_manager, PostgreSQLManager

logger = logging.getLogger(__name__)


class PostgreSQLCapsuleAdapter:
    """PostgreSQL adapter for capsule operations."""

    def __init__(self, pg_manager: PostgreSQLManager = None):
        self.pg_manager = pg_manager or get_postgresql_manager()
        self.initialized = False

        logger.info("🐘 PostgreSQL Capsule Adapter initialized")

    async def initialize(self):
        """Initialize the PostgreSQL adapter."""
        if not self.initialized:
            if not self.pg_manager.pool:
                await self.pg_manager.create_connection_pool()
            self.initialized = True
            logger.info("✅ PostgreSQL adapter initialized")

    async def create_capsule(self, capsule_data: Dict[str, Any]) -> Optional[str]:
        """Create a new capsule in PostgreSQL."""

        await self.initialize()

        try:
            async with self.pg_manager.pool.acquire() as conn:
                # Get or create user
                user_id = await self._get_or_create_user(
                    conn, capsule_data.get("user_id", "system")
                )

                # Insert capsule
                capsule_id = await conn.fetchval(
                    """
                    INSERT INTO capsules (
                        capsule_id, type, platform, user_id, session_id, model,
                        user_message, ai_response, content, reasoning_trace,
                        metadata, significance_score, confidence_score,
                        created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                    ) RETURNING capsule_id
                """,
                    capsule_data.get("capsule_id"),
                    capsule_data.get("type", "interaction_capsule"),
                    capsule_data.get("platform", "other"),
                    user_id,
                    capsule_data.get("session_id"),
                    capsule_data.get("model"),
                    capsule_data.get("user_message"),
                    capsule_data.get("ai_response"),
                    capsule_data.get("content"),
                    json.dumps(capsule_data.get("reasoning_trace", {})),
                    json.dumps(capsule_data.get("metadata", {})),
                    capsule_data.get("significance_score", 0.0),
                    capsule_data.get("confidence_score", 0.0),
                    datetime.fromisoformat(
                        capsule_data.get("timestamp", datetime.now().isoformat())
                    ),
                )

                logger.info(f"✅ Created capsule: {capsule_id}")
                return capsule_id

        except Exception as e:
            logger.error(f"❌ Failed to create capsule: {e}")
            return None

    async def get_capsule(self, capsule_id: str) -> Optional[Dict[str, Any]]:
        """Get a capsule by ID."""

        await self.initialize()

        try:
            async with self.pg_manager.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT 
                        c.*,
                        u.username,
                        u.email
                    FROM capsules c
                    LEFT JOIN users u ON c.user_id = u.id
                    WHERE c.capsule_id = $1 AND c.status = 'active'
                """,
                    capsule_id,
                )

                if row:
                    return self._row_to_dict(row)
                return None

        except Exception as e:
            logger.error(f"❌ Failed to get capsule {capsule_id}: {e}")
            return None

    async def list_capsules(
        self,
        user_id: str = None,
        platform: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List capsules with optional filtering."""

        await self.initialize()

        try:
            async with self.pg_manager.pool.acquire() as conn:
                query = """
                    SELECT 
                        c.*,
                        u.username,
                        u.email
                    FROM capsules c
                    LEFT JOIN users u ON c.user_id = u.id
                    WHERE c.status = 'active'
                """
                params = []
                param_count = 0

                if user_id:
                    param_count += 1
                    query += f" AND u.username = ${param_count}"
                    params.append(user_id)

                if platform:
                    param_count += 1
                    query += f" AND c.platform = ${param_count}"
                    params.append(platform)

                query += f" ORDER BY c.created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
                params.extend([limit, offset])

                rows = await conn.fetch(query, *params)
                return [self._row_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Failed to list capsules: {e}")
            return []

    async def search_capsules(
        self,
        query: str,
        platform: str = None,
        user_id: str = None,
        min_significance: float = 0.0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search capsules using full-text search."""

        await self.initialize()

        try:
            async with self.pg_manager.pool.acquire() as conn:
                # Get user UUID if user_id is provided
                user_uuid = None
                if user_id:
                    user_uuid = await conn.fetchval(
                        "SELECT id FROM users WHERE username = $1", user_id
                    )

                # Use the search function
                rows = await conn.fetch(
                    """
                    SELECT * FROM search_capsules($1, $2, $3, $4, $5)
                """,
                    query,
                    platform,
                    user_uuid,
                    min_significance,
                    limit,
                )

                return [self._search_row_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Failed to search capsules: {e}")
            return []

    async def get_capsule_stats(self, user_id: str = None) -> Dict[str, Any]:
        """Get capsule statistics."""

        await self.initialize()

        try:
            async with self.pg_manager.pool.acquire() as conn:
                # Get user UUID if user_id is provided
                user_uuid = None
                if user_id:
                    user_uuid = await conn.fetchval(
                        "SELECT id FROM users WHERE username = $1", user_id
                    )

                # Use the stats function
                row = await conn.fetchrow(
                    """
                    SELECT * FROM get_capsule_stats($1)
                """,
                    user_uuid,
                )

                if row:
                    return {
                        "total_capsules": row["total_capsules"],
                        "active_capsules": row["active_capsules"],
                        "avg_significance": row["avg_significance"],
                        "platforms": row["platforms"] or {},
                        "types": row["types"] or {},
                        "storage_backend": "postgresql",
                    }

                return {
                    "total_capsules": 0,
                    "active_capsules": 0,
                    "avg_significance": 0.0,
                    "platforms": {},
                    "types": {},
                    "storage_backend": "postgresql",
                }

        except Exception as e:
            logger.error(f"❌ Failed to get capsule stats: {e}")
            return {}

    async def update_capsule(self, capsule_id: str, updates: Dict[str, Any]) -> bool:
        """Update a capsule."""

        await self.initialize()

        try:
            async with self.pg_manager.pool.acquire() as conn:
                # Build dynamic update query
                set_clauses = []
                params = []
                param_count = 0

                for key, value in updates.items():
                    if key in [
                        "user_message",
                        "ai_response",
                        "content",
                        "significance_score",
                        "confidence_score",
                    ]:
                        param_count += 1
                        set_clauses.append(f"{key} = ${param_count}")
                        params.append(value)
                    elif key in ["metadata", "reasoning_trace"]:
                        param_count += 1
                        set_clauses.append(f"{key} = ${param_count}")
                        params.append(json.dumps(value))

                if not set_clauses:
                    return False

                param_count += 1
                params.append(capsule_id)

                query = f"""
                    UPDATE capsules 
                    SET {', '.join(set_clauses)}, updated_at = NOW()
                    WHERE capsule_id = ${param_count}
                """

                result = await conn.execute(query, *params)
                return result == "UPDATE 1"

        except Exception as e:
            logger.error(f"❌ Failed to update capsule {capsule_id}: {e}")
            return False

    async def delete_capsule(self, capsule_id: str) -> bool:
        """Delete a capsule (soft delete)."""

        await self.initialize()

        try:
            async with self.pg_manager.pool.acquire() as conn:
                result = await conn.execute(
                    """
                    UPDATE capsules 
                    SET status = 'deleted', updated_at = NOW()
                    WHERE capsule_id = $1
                """,
                    capsule_id,
                )

                return result == "UPDATE 1"

        except Exception as e:
            logger.error(f"❌ Failed to delete capsule {capsule_id}: {e}")
            return False

    async def get_recent_capsules(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent capsules."""

        await self.initialize()

        try:
            async with self.pg_manager.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT 
                        c.*,
                        u.username,
                        u.email
                    FROM capsules c
                    LEFT JOIN users u ON c.user_id = u.id
                    WHERE c.status = 'active'
                    ORDER BY c.created_at DESC
                    LIMIT $1
                """,
                    limit,
                )

                return [self._row_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"❌ Failed to get recent capsules: {e}")
            return []

    async def _get_or_create_user(self, conn, username: str) -> UUID:
        """Get or create a user, return UUID."""

        # Check if user exists
        user_id = await conn.fetchval(
            "SELECT id FROM users WHERE username = $1", username
        )

        if user_id:
            return user_id

        # Create new user
        user_id = await conn.fetchval(
            """
            INSERT INTO users (username, email, password_hash, roles)
            VALUES ($1, $2, $3, $4)
            RETURNING id
        """,
            username,
            f"{username}@system.uatp",
            "system",
            ["system"],
        )

        return user_id

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary."""

        return {
            "capsule_id": row["capsule_id"],
            "type": row["type"],
            "platform": row["platform"],
            "user_id": row["username"],
            "session_id": row["session_id"],
            "model": row["model"],
            "user_message": row["user_message"],
            "ai_response": row["ai_response"],
            "content": row["content"],
            "reasoning_trace": row["reasoning_trace"],
            "metadata": row["metadata"],
            "significance_score": row["significance_score"],
            "confidence_score": row["confidence_score"],
            "timestamp": row["created_at"].isoformat(),
            "storage_backend": "postgresql",
        }

    def _search_row_to_dict(self, row) -> Dict[str, Any]:
        """Convert search result row to dictionary."""

        return {
            "capsule_id": row["capsule_id"],
            "type": row["type"],
            "platform": row["platform"],
            "user_message": row["user_message"],
            "ai_response": row["ai_response"],
            "significance_score": row["significance_score"],
            "timestamp": row["created_at"].isoformat(),
            "rank": row["rank"],
            "storage_backend": "postgresql",
        }


# Global adapter instance
_pg_adapter = None


def get_postgresql_adapter() -> PostgreSQLCapsuleAdapter:
    """Get the global PostgreSQL adapter instance."""
    global _pg_adapter
    if _pg_adapter is None:
        _pg_adapter = PostgreSQLCapsuleAdapter()
    return _pg_adapter


async def main():
    """Test PostgreSQL adapter."""

    print("🐘 Testing PostgreSQL Adapter")
    print("=" * 40)

    # Initialize adapter
    adapter = get_postgresql_adapter()

    try:
        # Test capsule creation
        print("\n📦 Testing capsule creation...")
        test_capsule = {
            "capsule_id": "test_pg_capsule_001",
            "type": "interaction_capsule",
            "platform": "anthropic",
            "user_id": "test_user",
            "session_id": "test_session_001",
            "model": "claude-3-sonnet",
            "user_message": "Test message for PostgreSQL adapter",
            "ai_response": "This is a test response from the PostgreSQL adapter",
            "significance_score": 2.5,
            "confidence_score": 0.85,
            "timestamp": datetime.now().isoformat(),
            "metadata": {"test": True, "source": "adapter_test"},
        }

        capsule_id = await adapter.create_capsule(test_capsule)
        if capsule_id:
            print(f"✅ Created capsule: {capsule_id}")

            # Test capsule retrieval
            print("\n🔍 Testing capsule retrieval...")
            retrieved = await adapter.get_capsule(capsule_id)
            if retrieved:
                print(f"✅ Retrieved capsule: {retrieved['capsule_id']}")
                print(f"   Platform: {retrieved['platform']}")
                print(f"   Significance: {retrieved['significance_score']}")

        # Test capsule listing
        print("\n📋 Testing capsule listing...")
        capsules = await adapter.list_capsules(limit=5)
        print(f"✅ Found {len(capsules)} capsules")

        # Test statistics
        print("\n📊 Testing statistics...")
        stats = await adapter.get_capsule_stats()
        print(
            f"✅ Stats: {stats['total_capsules']} total, {stats['active_capsules']} active"
        )

        # Test search
        print("\n🔍 Testing search...")
        results = await adapter.search_capsules("test", limit=3)
        print(f"✅ Search found {len(results)} results")

    except Exception as e:
        print(f"❌ PostgreSQL adapter test failed: {e}")
        print("Make sure PostgreSQL is running and schema is created")

    print("\n✅ PostgreSQL adapter test completed!")


if __name__ == "__main__":
    asyncio.run(main())
