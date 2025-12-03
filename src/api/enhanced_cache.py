"""
Advanced Multi-Layer Caching Infrastructure
==========================================

High-performance caching system with:
- Multi-layer caching (L1: in-memory, L2: Redis, L3: persistent)
- Intelligent cache warming for frequently accessed data
- Cache invalidation strategies with dependency tracking
- Performance metrics and hit rate monitoring
- Distributed cache coordination
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis
from quart import current_app

logger = logging.getLogger(__name__)


class CacheLayer(Enum):
    """Cache layer enumeration."""

    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_PERSISTENT = "l3_persistent"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    dependencies: Set[str] = None
    size_bytes: int = 0

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = set()
        if self.last_accessed is None:
            self.last_accessed = self.created_at


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    errors: int = 0
    total_size_bytes: int = 0
    avg_response_time_ms: float = 0.0
    hit_rate: float = 0.0

    def update_hit_rate(self):
        total = self.hits + self.misses
        self.hit_rate = (self.hits / total) * 100 if total > 0 else 0.0


class InMemoryCache:
    """High-performance in-memory cache (L1)."""

    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.data: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # For LRU eviction
        self.stats = CacheStats()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from L1 cache."""
        async with self._lock:
            if key not in self.data:
                self.stats.misses += 1
                return None

            entry = self.data[key]

            # Check expiration
            if entry.expires_at and datetime.now(timezone.utc) > entry.expires_at:
                await self._delete_entry(key)
                self.stats.misses += 1
                return None

            # Update access info
            entry.access_count += 1
            entry.last_accessed = datetime.now(timezone.utc)

            # Update LRU order
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

            self.stats.hits += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        dependencies: Optional[Set[str]] = None,
    ) -> bool:
        """Set value in L1 cache."""
        async with self._lock:
            # Calculate size
            try:
                size_bytes = len(pickle.dumps(value))
            except Exception:
                size_bytes = len(str(value).encode("utf-8"))

            # Check if we need to evict
            while (
                len(self.data) >= self.max_size
                or self.stats.total_size_bytes + size_bytes > self.max_memory_bytes
            ):
                if not self.access_order:
                    break
                await self._evict_lru()

            # Create cache entry
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=ttl) if ttl else None

            entry = CacheEntry(
                value=value,
                created_at=now,
                expires_at=expires_at,
                dependencies=dependencies or set(),
                size_bytes=size_bytes,
            )

            # Remove old entry if exists
            if key in self.data:
                await self._delete_entry(key)

            # Add new entry
            self.data[key] = entry
            self.access_order.append(key)
            self.stats.total_size_bytes += size_bytes
            self.stats.sets += 1

            return True

    async def delete(self, key: str) -> bool:
        """Delete key from L1 cache."""
        async with self._lock:
            if key in self.data:
                await self._delete_entry(key)
                self.stats.deletes += 1
                return True
            return False

    async def clear(self) -> None:
        """Clear all entries from L1 cache."""
        async with self._lock:
            self.data.clear()
            self.access_order.clear()
            self.stats.total_size_bytes = 0

    async def invalidate_dependencies(self, dependency: str) -> int:
        """Invalidate all entries with a specific dependency."""
        async with self._lock:
            keys_to_delete = []
            for key, entry in self.data.items():
                if dependency in entry.dependencies:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                await self._delete_entry(key)

            return len(keys_to_delete)

    async def _delete_entry(self, key: str) -> None:
        """Internal method to delete entry and update stats."""
        if key in self.data:
            entry = self.data[key]
            self.stats.total_size_bytes -= entry.size_bytes
            del self.data[key]

            if key in self.access_order:
                self.access_order.remove(key)

    async def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self.access_order:
            lru_key = self.access_order[0]
            await self._delete_entry(lru_key)
            self.stats.evictions += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get L1 cache statistics."""
        stats_dict = asdict(self.stats)
        stats_dict.update(
            {
                "entry_count": len(self.data),
                "memory_usage_mb": round(
                    self.stats.total_size_bytes / (1024 * 1024), 2
                ),
                "memory_usage_percent": round(
                    (self.stats.total_size_bytes / self.max_memory_bytes) * 100, 2
                ),
            }
        )
        stats_dict["hit_rate"] = self.stats.hit_rate
        self.stats.update_hit_rate()
        return stats_dict


class RedisCache:
    """Redis-based distributed cache (L2)."""

    def __init__(
        self, redis_url: str = "redis://localhost:6379", key_prefix: str = "uatp:"
    ):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.redis_client: Optional[redis.Redis] = None
        self.stats = CacheStats()
        self._connected = False

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
            await self.redis_client.ping()
            self._connected = True
            logger.info(f"Connected to Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Disconnected from Redis")

    def _make_key(self, key: str) -> str:
        """Create prefixed Redis key."""
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self._connected or not self.redis_client:
            self.stats.errors += 1
            return None

        try:
            start_time = time.time()
            redis_key = self._make_key(key)
            data = await self.redis_client.get(redis_key)

            if data is None:
                self.stats.misses += 1
                return None

            # Deserialize
            try:
                value = pickle.loads(data)
            except Exception:
                # Fallback to JSON
                value = json.loads(data.decode("utf-8"))

            response_time = (time.time() - start_time) * 1000
            self.stats.avg_response_time_ms = (
                self.stats.avg_response_time_ms * self.stats.hits + response_time
            ) / (self.stats.hits + 1)
            self.stats.hits += 1

            return value

        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            self.stats.errors += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        if not self._connected or not self.redis_client:
            self.stats.errors += 1
            return False

        try:
            redis_key = self._make_key(key)

            # Serialize
            try:
                data = pickle.dumps(value)
            except Exception:
                # Fallback to JSON
                data = json.dumps(value).encode("utf-8")

            if ttl:
                await self.redis_client.setex(redis_key, ttl, data)
            else:
                await self.redis_client.set(redis_key, data)

            self.stats.sets += 1
            return True

        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            self.stats.errors += 1
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        if not self._connected or not self.redis_client:
            self.stats.errors += 1
            return False

        try:
            redis_key = self._make_key(key)
            result = await self.redis_client.delete(redis_key)
            if result > 0:
                self.stats.deletes += 1
                return True
            return False

        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            self.stats.errors += 1
            return False

    async def clear(self) -> None:
        """Clear all keys with our prefix."""
        if not self._connected or not self.redis_client:
            return

        try:
            pattern = f"{self.key_prefix}*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} keys from Redis")
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            self.stats.errors += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        stats_dict = asdict(self.stats)
        stats_dict["connected"] = self._connected
        self.stats.update_hit_rate()
        return stats_dict


class MultiLayerCache:
    """Multi-layer cache coordinator."""

    def __init__(
        self,
        l1_enabled: bool = True,
        l2_enabled: bool = True,
        redis_url: Optional[str] = None,
        l1_max_size: int = 1000,
        l1_max_memory_mb: int = 100,
    ):
        self.l1_enabled = l1_enabled
        self.l2_enabled = l2_enabled

        # Initialize L1 cache
        self.l1_cache = (
            InMemoryCache(l1_max_size, l1_max_memory_mb) if l1_enabled else None
        )

        # Initialize L2 cache
        self.l2_cache = None
        if l2_enabled and redis_url:
            self.l2_cache = RedisCache(redis_url)

        # Dependency tracking
        self.dependency_map: Dict[str, Set[str]] = {}  # dependency -> set of keys

        # Cache warming
        self.warm_cache_functions: Dict[str, Callable] = {}
        self._warming_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Initialize all cache layers."""
        if self.l2_cache:
            try:
                await self.l2_cache.connect()
            except Exception as e:
                logger.error(f"Failed to initialize L2 cache: {e}")
                self.l2_cache = None

        # Start cache warming task
        if self.warm_cache_functions:
            self._warming_task = asyncio.create_task(self._cache_warming_loop())

        logger.info(
            f"Multi-layer cache initialized (L1: {self.l1_enabled}, L2: {self.l2_cache is not None})"
        )

    async def disconnect(self) -> None:
        """Disconnect from all cache layers."""
        if self._warming_task:
            self._warming_task.cancel()
            try:
                await self._warming_task
            except asyncio.CancelledError:
                pass

        if self.l2_cache:
            await self.l2_cache.disconnect()

    async def get(self, key: str, warm_on_miss: bool = True) -> Optional[Any]:
        """Get value from cache layers (L1 -> L2 -> warm if needed)."""
        # Try L1 first
        if self.l1_cache:
            value = await self.l1_cache.get(key)
            if value is not None:
                return value

        # Try L2
        if self.l2_cache:
            value = await self.l2_cache.get(key)
            if value is not None:
                # Populate L1 cache
                if self.l1_cache:
                    await self.l1_cache.set(key, value, ttl=300)  # 5 min TTL for L1
                return value

        # Cache warming on miss
        if warm_on_miss and key in self.warm_cache_functions:
            try:
                value = await self.warm_cache_functions[key]()
                if value is not None:
                    await self.set(key, value, ttl=3600)  # 1 hour TTL
                    return value
            except Exception as e:
                logger.error(f"Cache warming failed for key {key}: {e}")

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        dependencies: Optional[Set[str]] = None,
    ) -> bool:
        """Set value in all cache layers."""
        success = True

        # Set in L1
        if self.l1_cache:
            l1_success = await self.l1_cache.set(key, value, ttl, dependencies)
            success = success and l1_success

        # Set in L2
        if self.l2_cache:
            l2_success = await self.l2_cache.set(key, value, ttl)
            success = success and l2_success

        # Update dependency tracking
        if dependencies:
            for dep in dependencies:
                if dep not in self.dependency_map:
                    self.dependency_map[dep] = set()
                self.dependency_map[dep].add(key)

        return success

    async def delete(self, key: str) -> bool:
        """Delete key from all cache layers."""
        success = True

        if self.l1_cache:
            l1_success = await self.l1_cache.delete(key)
            success = success and l1_success

        if self.l2_cache:
            l2_success = await self.l2_cache.delete(key)
            success = success and l2_success

        # Clean up dependency tracking
        for dep_keys in self.dependency_map.values():
            dep_keys.discard(key)

        return success

    async def clear(self) -> None:
        """Clear all cache layers."""
        if self.l1_cache:
            await self.l1_cache.clear()

        if self.l2_cache:
            await self.l2_cache.clear()

        self.dependency_map.clear()

    async def invalidate_dependencies(self, dependency: str) -> int:
        """Invalidate all entries with a specific dependency."""
        invalidated_count = 0

        # Get keys to invalidate
        keys_to_invalidate = self.dependency_map.get(dependency, set())

        for key in keys_to_invalidate:
            await self.delete(key)
            invalidated_count += 1

        # Clean up dependency map
        if dependency in self.dependency_map:
            del self.dependency_map[dependency]

        logger.info(
            f"Invalidated {invalidated_count} cache entries for dependency: {dependency}"
        )
        return invalidated_count

    def register_warm_function(self, key: str, func: Callable) -> None:
        """Register a function to warm the cache for a specific key."""
        self.warm_cache_functions[key] = func
        logger.info(f"Registered cache warming function for key: {key}")

    async def _cache_warming_loop(self) -> None:
        """Background cache warming loop."""
        while True:
            try:
                await asyncio.sleep(300)  # Warm every 5 minutes

                for key, func in self.warm_cache_functions.items():
                    try:
                        # Check if key needs warming (not in any cache)
                        cached_value = await self.get(key, warm_on_miss=False)
                        if cached_value is None:
                            logger.info(f"Warming cache for key: {key}")
                            value = await func()
                            if value is not None:
                                await self.set(key, value, ttl=3600)
                    except Exception as e:
                        logger.error(f"Error warming cache for key {key}: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache warming loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from all cache layers."""
        stats = {
            "l1_enabled": self.l1_enabled,
            "l2_enabled": self.l2_enabled and self.l2_cache is not None,
            "dependency_count": len(self.dependency_map),
            "warm_functions_count": len(self.warm_cache_functions),
        }

        if self.l1_cache:
            stats["l1_stats"] = self.l1_cache.get_stats()

        if self.l2_cache:
            stats["l2_stats"] = self.l2_cache.get_stats()

        return stats


# Global cache instance
_global_cache: Optional[MultiLayerCache] = None


def get_cache() -> MultiLayerCache:
    """Get the global cache instance."""
    global _global_cache
    if _global_cache is None:
        raise RuntimeError("Cache not initialized. Call initialize_cache() first.")
    return _global_cache


async def initialize_cache(
    redis_url: Optional[str] = None,
    l1_enabled: bool = True,
    l2_enabled: bool = True,
    l1_max_size: int = 1000,
    l1_max_memory_mb: int = 100,
) -> MultiLayerCache:
    """Initialize the global cache."""
    global _global_cache

    _global_cache = MultiLayerCache(
        l1_enabled=l1_enabled,
        l2_enabled=l2_enabled,
        redis_url=redis_url,
        l1_max_size=l1_max_size,
        l1_max_memory_mb=l1_max_memory_mb,
    )

    await _global_cache.initialize()
    logger.info("Global cache initialized")
    return _global_cache


async def close_cache() -> None:
    """Close the global cache."""
    global _global_cache
    if _global_cache:
        await _global_cache.disconnect()
        _global_cache = None
        logger.info("Global cache closed")


# Convenience functions for common caching patterns
async def cache_capsule_data(capsule_id: str, data: Any, ttl: int = 1800) -> bool:
    """Cache capsule data with dependencies."""
    cache = get_cache()
    return await cache.set(
        f"capsule:{capsule_id}",
        data,
        ttl=ttl,
        dependencies={"capsules", f"capsule:{capsule_id}"},
    )


async def get_cached_capsule_data(capsule_id: str) -> Optional[Any]:
    """Get cached capsule data."""
    try:
        cache = get_cache()
        return await cache.get(f"capsule:{capsule_id}")
    except RuntimeError:
        return None


async def invalidate_capsule_cache(capsule_id: str = None) -> int:
    """Invalidate capsule-related cache entries."""
    try:
        cache = get_cache()
        if capsule_id:
            return await cache.invalidate_dependencies(f"capsule:{capsule_id}")
        else:
            return await cache.invalidate_dependencies("capsules")
    except RuntimeError:
        return 0


async def cache_ai_model_response(
    model: str, prompt_hash: str, response: Any, ttl: int = 3600
) -> bool:
    """Cache AI model response."""
    try:
        cache = get_cache()
        key = f"ai_model:{model}:{prompt_hash}"
        return await cache.set(
            key, response, ttl=ttl, dependencies={"ai_responses", f"model:{model}"}
        )
    except RuntimeError:
        return False


async def get_cached_ai_model_response(model: str, prompt_hash: str) -> Optional[Any]:
    """Get cached AI model response."""
    try:
        cache = get_cache()
        key = f"ai_model:{model}:{prompt_hash}"
        return await cache.get(key)
    except RuntimeError:
        return None


def create_prompt_hash(prompt: str, **kwargs) -> str:
    """Create a hash for caching AI prompts."""
    content = prompt + json.dumps(kwargs, sort_keys=True)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
