"""
Database-aware data loading utilities for the UATP Capsule Visualizer.
This module provides data loading from both SQLite database and JSONL fallback.
"""

import asyncio
import datetime
import json
import logging
import os
import sqlite3
import sys
from typing import List, Dict, Optional, Any, Union

import streamlit as st

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.filters.sqlite_capsule_creator import (
    get_sqlite_capsule_creator,
    initialize_sqlite_capsule_creator,
)
from src.core.database import db
from sqlalchemy import text

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)


def convert_to_serializable(obj):
    """Convert objects to JSON-serializable format, handling datetime objects."""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    else:
        return obj


class DatabaseCapsuleLoader:
    """Database-aware capsule loader with JSONL fallback."""

    def __init__(
        self,
        database_path: str = "./uatp_dev.db",
        jsonl_path: str = "./capsule_chain.jsonl",
    ):
        self.database_path = database_path
        self.jsonl_path = jsonl_path
        self.capsule_creator = None
        self._initialized = False

    async def initialize(self):
        """Initialize the database connection."""
        if self._initialized:
            return

        try:
            self.capsule_creator = await initialize_sqlite_capsule_creator()
            self._initialized = True
            logger.info("✅ Database capsule loader initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            self._initialized = False

    def _load_from_jsonl(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load capsules from JSONL file as fallback."""
        capsules = []

        try:
            with open(self.jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            capsule_data = json.loads(line)
                            capsules.append(capsule_data)

                            if limit and len(capsules) >= limit:
                                break
                        except json.JSONDecodeError:
                            continue

            # Sort by timestamp (most recent first)
            capsules.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            logger.info(f"📄 Loaded {len(capsules)} capsules from JSONL")

        except FileNotFoundError:
            logger.warning(f"⚠️ JSONL file not found: {self.jsonl_path}")
        except Exception as e:
            logger.error(f"❌ Error loading JSONL: {e}")

        return capsules

    async def _load_from_database(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Load capsules from SQLite database."""
        if not self._initialized:
            await self.initialize()

        if not self.capsule_creator or not self.capsule_creator._db_connected:
            logger.warning("⚠️ Database not connected, using JSONL fallback")
            return self._load_from_jsonl(limit)

        try:
            # Get recent capsules from database
            recent_capsules = await self.capsule_creator.get_recent_capsules(
                limit or 100
            )

            # Convert to standard format
            formatted_capsules = []
            for capsule in recent_capsules:
                formatted_capsule = {
                    "capsule_id": capsule.get("capsule_id"),
                    "type": capsule.get("type", "reasoning_trace"),
                    "timestamp": capsule.get("timestamp"),
                    "platform": capsule.get("platform"),
                    "significance_score": capsule.get("significance_score", 0.0),
                    "user_id": capsule.get("user_id"),
                    "session_id": capsule.get("session_id"),
                    "storage_backend": capsule.get("storage_backend", "sqlite"),
                    "metadata": {
                        "platform": capsule.get("platform"),
                        "significance_score": capsule.get("significance_score", 0.0),
                        "user_id": capsule.get("user_id"),
                        "session_id": capsule.get("session_id"),
                        "storage_backend": "sqlite",
                    },
                }
                formatted_capsules.append(formatted_capsule)

            logger.info(f"💾 Loaded {len(formatted_capsules)} capsules from database")
            return formatted_capsules

        except Exception as e:
            logger.error(f"❌ Database loading failed: {e}")
            return self._load_from_jsonl(limit)

    async def load_capsules(
        self, limit: Optional[int] = None, use_database: bool = True
    ) -> List[Dict[str, Any]]:
        """Load capsules from database or JSONL fallback."""
        if use_database:
            return await self._load_from_database(limit)
        else:
            return self._load_from_jsonl(limit)

    async def get_capsule_stats(self) -> Dict[str, Any]:
        """Get capsule statistics from database or JSONL."""
        if not self._initialized:
            await self.initialize()

        if self.capsule_creator and self.capsule_creator._db_connected:
            try:
                return await self.capsule_creator.get_capsule_stats()
            except Exception as e:
                logger.error(f"❌ Database stats failed: {e}")

        # Fallback to JSONL stats
        capsules = self._load_from_jsonl()
        platforms = {}
        total_capsules = len(capsules)

        for capsule in capsules:
            platform = capsule.get("metadata", {}).get("platform", "unknown")
            if platform not in platforms:
                platforms[platform] = 0
            platforms[platform] += 1

        return {
            "total_capsules": total_capsules,
            "auto_filtered_capsules": total_capsules,  # Assume all are auto-filtered
            "platforms": platforms,
            "storage_backend": "jsonl_fallback",
        }

    async def search_capsules(
        self,
        query: str = "",
        platform: Optional[str] = None,
        min_significance: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search capsules with filters."""
        capsules = await self.load_capsules(limit=limit)

        filtered_capsules = []

        for capsule in capsules:
            # Text search
            if query:
                searchable_text = json.dumps(capsule).lower()
                if query.lower() not in searchable_text:
                    continue

            # Platform filter
            if platform and capsule.get("platform") != platform:
                continue

            # Significance filter
            if min_significance is not None:
                significance = capsule.get("significance_score", 0.0)
                if significance < min_significance:
                    continue

            filtered_capsules.append(capsule)

        return filtered_capsules


# Global loader instance
_loader = None


def get_loader() -> DatabaseCapsuleLoader:
    """Get the global database loader instance."""
    global _loader
    if _loader is None:
        _loader = DatabaseCapsuleLoader()
    return _loader


@st.cache_data
def load_capsules_cached(
    limit: Optional[int] = None, use_database: bool = True
) -> List[Dict[str, Any]]:
    """Load capsules with caching support."""
    loader = get_loader()

    # Run async function in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        loader.load_capsules(limit=limit, use_database=use_database)
    )


@st.cache_data
def get_capsule_stats_cached() -> Dict[str, Any]:
    """Get capsule statistics with caching support."""
    loader = get_loader()

    # Run async function in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(loader.get_capsule_stats())


def search_capsules_cached(
    query: str = "",
    platform: Optional[str] = None,
    min_significance: Optional[float] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Search capsules with caching support."""
    loader = get_loader()

    # Run async function in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        loader.search_capsules(
            query=query,
            platform=platform,
            min_significance=min_significance,
            limit=limit,
        )
    )


# Legacy compatibility functions
def load_capsules(path: str) -> List[Dict[str, Any]]:
    """Legacy function for backward compatibility."""
    return load_capsules_cached(use_database=True)


def get_capsule_count() -> int:
    """Get total capsule count."""
    stats = get_capsule_stats_cached()
    return stats.get("total_capsules", 0)


def get_platform_distribution() -> Dict[str, int]:
    """Get platform distribution."""
    stats = get_capsule_stats_cached()
    return stats.get("platforms", {})


def get_storage_backend() -> str:
    """Get current storage backend."""
    stats = get_capsule_stats_cached()
    return stats.get("storage_backend", "unknown")


# Test function
async def test_database_loader():
    """Test the database loader functionality."""
    print("🧪 Testing Database Capsule Loader")
    print("=" * 40)

    loader = DatabaseCapsuleLoader()

    # Test initialization
    await loader.initialize()
    print(f"✅ Initialization: {'Success' if loader._initialized else 'Failed'}")

    # Test loading capsules
    capsules = await loader.load_capsules(limit=5)
    print(f"📦 Loaded capsules: {len(capsules)}")

    if capsules:
        print(f"   Latest: {capsules[0].get('capsule_id', 'unknown')}")
        print(f"   Platform: {capsules[0].get('platform', 'unknown')}")
        print(f"   Significance: {capsules[0].get('significance_score', 0.0):.2f}")

    # Test stats
    stats = await loader.get_capsule_stats()
    print(f"📊 Stats: {stats.get('total_capsules', 0)} capsules")
    print(f"   Backend: {stats.get('storage_backend', 'unknown')}")
    print(f"   Platforms: {list(stats.get('platforms', {}).keys())}")

    # Test search
    search_results = await loader.search_capsules(query="code", limit=3)
    print(f"🔍 Search results: {len(search_results)}")

    print("\n✅ Database loader test completed!")


if __name__ == "__main__":
    asyncio.run(test_database_loader())
