"""
API Response Caching System
===========================

High-performance API response caching with:
- Response caching for expensive read operations
- Cache invalidation on data changes
- Conditional request handling (ETag, Last-Modified)
- Cache warming for popular endpoints
- Intelligent cache key generation
- Request fingerprinting and cache hit optimization
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass
from functools import wraps
import weakref

from quart import request, jsonify, Response, current_app
from werkzeug.http import parse_cache_control_header, generate_etag

from .enhanced_cache import get_cache, MultiLayerCache

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for API response caching."""

    ttl: int = 300  # 5 minutes default
    vary_headers: List[str] = None
    cache_query_params: bool = True
    cache_headers: List[str] = None
    invalidation_tags: Set[str] = None
    etag_enabled: bool = True
    last_modified_enabled: bool = True
    gzip_threshold: int = 1024  # Compress responses larger than 1KB

    def __post_init__(self):
        if self.vary_headers is None:
            self.vary_headers = ["Authorization", "Accept", "Content-Type"]
        if self.cache_headers is None:
            self.cache_headers = ["User-Agent", "Accept-Language"]
        if self.invalidation_tags is None:
            self.invalidation_tags = set()


class ResponseCacheManager:
    """Manages API response caching with intelligent cache strategies."""

    def __init__(self, cache: Optional[MultiLayerCache] = None):
        self.cache = cache
        self.endpoint_configs: Dict[str, CacheConfig] = {}
        self.cache_warming_functions: Dict[str, Callable] = {}
        self.request_patterns: Dict[
            str, int
        ] = {}  # Track request patterns for optimization
        self._warming_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_sets": 0,
            "conditional_hits": 0,  # ETag/Last-Modified hits
            "bytes_saved": 0,
            "response_time_saved_ms": 0.0,
        }

    def configure_endpoint(self, endpoint: str, config: CacheConfig) -> None:
        """Configure caching for a specific endpoint."""
        self.endpoint_configs[endpoint] = config
        logger.info(f"Configured caching for endpoint: {endpoint}")

    def register_warming_function(self, cache_key: str, func: Callable) -> None:
        """Register a function to warm specific cache entries."""
        self.cache_warming_functions[cache_key] = func
        logger.info(f"Registered cache warming for key: {cache_key}")

    def generate_cache_key(self, endpoint: str, config: CacheConfig) -> str:
        """Generate a cache key for the current request."""
        key_parts = [f"api_response:{endpoint}"]

        # Include query parameters if configured
        if config.cache_query_params and request.args:
            # Sort query params for consistent caching
            sorted_params = sorted(request.args.items())
            params_str = "&".join(f"{k}={v}" for k, v in sorted_params)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            key_parts.append(f"params:{params_hash}")

        # Include relevant headers
        header_parts = []
        for header in config.cache_headers:
            value = request.headers.get(header)
            if value:
                header_hash = hashlib.md5(value.encode()).hexdigest()[:8]
                header_parts.append(f"{header.lower()}:{header_hash}")

        if header_parts:
            key_parts.append("headers:" + "|".join(header_parts))

        # Include user context if authenticated
        if hasattr(request, "user_id") and request.user_id:
            key_parts.append(f"user:{request.user_id}")

        return ":".join(key_parts)

    def generate_etag(self, content: Any) -> str:
        """Generate ETag for response content."""
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, sort_keys=True)
        else:
            content_str = str(content)

        return generate_etag(content_str.encode("utf-8"))

    def check_conditional_request(
        self, etag: str, last_modified: Optional[datetime] = None
    ) -> bool:
        """Check if request can be satisfied with 304 Not Modified."""
        # Check If-None-Match (ETag)
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match:
            # Handle both quoted and unquoted ETags
            client_etags = [tag.strip('"') for tag in if_none_match.split(",")]
            server_etag = etag.strip('"')
            if server_etag in client_etags or "*" in client_etags:
                return True

        # Check If-Modified-Since
        if last_modified and request.headers.get("If-Modified-Since"):
            try:
                client_time = datetime.fromisoformat(
                    request.headers.get("If-Modified-Since").replace("GMT", "+0000")
                )
                if last_modified <= client_time:
                    return True
            except (ValueError, AttributeError):
                pass

        return False

    async def get_cached_response(
        self, cache_key: str, config: CacheConfig
    ) -> Optional[Tuple[Any, Dict[str, str]]]:
        """Get cached response data and metadata."""
        if not self.cache:
            return None

        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data is None:
                self.stats["cache_misses"] += 1
                return None

            # Cached data includes content and metadata
            content = cached_data.get("content")
            metadata = cached_data.get("metadata", {})

            self.stats["cache_hits"] += 1

            # Update request pattern tracking
            endpoint = cache_key.split(":")[1] if ":" in cache_key else cache_key
            self.request_patterns[endpoint] = self.request_patterns.get(endpoint, 0) + 1

            return content, metadata

        except Exception as e:
            logger.error(f"Error retrieving cached response: {e}")
            return None

    async def cache_response(
        self,
        cache_key: str,
        content: Any,
        config: CacheConfig,
        response_time_ms: float = 0.0,
    ) -> bool:
        """Cache response content with metadata."""
        if not self.cache:
            return False

        try:
            # Generate metadata
            now = datetime.now(timezone.utc)
            etag = self.generate_etag(content) if config.etag_enabled else None

            metadata = {
                "etag": etag,
                "last_modified": now.isoformat()
                if config.last_modified_enabled
                else None,
                "cached_at": now.isoformat(),
                "response_time_ms": response_time_ms,
                "endpoint": cache_key.split(":")[1] if ":" in cache_key else cache_key,
            }

            cached_data = {"content": content, "metadata": metadata}

            # Cache with dependencies for invalidation
            success = await self.cache.set(
                cache_key,
                cached_data,
                ttl=config.ttl,
                dependencies=config.invalidation_tags,
            )

            if success:
                self.stats["cache_sets"] += 1
                # Estimate bytes saved (rough approximation)
                if isinstance(content, (dict, list)):
                    size_estimate = len(json.dumps(content))
                else:
                    size_estimate = len(str(content))

                self.stats["bytes_saved"] += size_estimate
                self.stats["response_time_saved_ms"] += response_time_ms

            return success

        except Exception as e:
            logger.error(f"Error caching response: {e}")
            return False

    async def invalidate_cache(self, tags: Set[str]) -> int:
        """Invalidate cached responses by tags."""
        if not self.cache:
            return 0

        total_invalidated = 0
        for tag in tags:
            try:
                count = await self.cache.invalidate_dependencies(tag)
                total_invalidated += count
                logger.info(f"Invalidated {count} cache entries for tag: {tag}")
            except Exception as e:
                logger.error(f"Error invalidating cache for tag {tag}: {e}")

        return total_invalidated

    def get_stats(self) -> Dict[str, Any]:
        """Get response cache statistics."""
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = (
            (self.stats["cache_hits"] / total_requests * 100)
            if total_requests > 0
            else 0.0
        )

        avg_saved_time = 0.0
        if self.stats["cache_hits"] > 0:
            avg_saved_time = (
                self.stats["response_time_saved_ms"] / self.stats["cache_hits"]
            )

        return {
            "total_requests": total_requests,
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "conditional_hits": self.stats["conditional_hits"],
            "hit_rate_percent": round(hit_rate, 2),
            "bytes_saved": self.stats["bytes_saved"],
            "avg_time_saved_ms": round(avg_saved_time, 2),
            "total_time_saved_ms": round(self.stats["response_time_saved_ms"], 2),
            "endpoints_configured": len(self.endpoint_configs),
            "warming_functions": len(self.cache_warming_functions),
            "popular_endpoints": dict(
                sorted(self.request_patterns.items(), key=lambda x: x[1], reverse=True)[
                    :10
                ]
            ),
        }

    async def warm_popular_endpoints(self) -> None:
        """Warm cache for popular endpoints."""
        if not self.cache_warming_functions:
            return

        # Sort endpoints by popularity
        popular_endpoints = sorted(
            self.request_patterns.items(), key=lambda x: x[1], reverse=True
        )[
            :5
        ]  # Top 5 endpoints

        for endpoint, count in popular_endpoints:
            if endpoint in self.cache_warming_functions:
                try:
                    logger.info(
                        f"Warming cache for popular endpoint: {endpoint} ({count} requests)"
                    )
                    await self.cache_warming_functions[endpoint]()
                except Exception as e:
                    logger.error(f"Error warming cache for endpoint {endpoint}: {e}")

    async def start_background_tasks(self) -> None:
        """Start background cache warming and maintenance tasks."""
        self._warming_task = asyncio.create_task(self._cache_warming_loop())
        logger.info("Started response cache background tasks")

    async def stop_background_tasks(self) -> None:
        """Stop background tasks."""
        if self._warming_task:
            self._warming_task.cancel()
            try:
                await self._warming_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped response cache background tasks")

    async def _cache_warming_loop(self) -> None:
        """Background cache warming loop."""
        while True:
            try:
                await asyncio.sleep(600)  # Warm every 10 minutes
                await self.warm_popular_endpoints()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache warming loop error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error


# Global response cache manager
_response_cache_manager: Optional[ResponseCacheManager] = None


def get_response_cache_manager() -> ResponseCacheManager:
    """Get the global response cache manager."""
    global _response_cache_manager
    if _response_cache_manager is None:
        try:
            cache = get_cache()
            _response_cache_manager = ResponseCacheManager(cache)
        except RuntimeError:
            # Cache not initialized, create without cache backend
            _response_cache_manager = ResponseCacheManager()
    return _response_cache_manager


def cached_response(
    ttl: int = 300,
    vary_headers: List[str] = None,
    cache_query_params: bool = True,
    invalidation_tags: Set[str] = None,
    etag_enabled: bool = True,
    last_modified_enabled: bool = True,
):
    """
    Decorator for caching API responses.

    Args:
        ttl: Cache time-to-live in seconds
        vary_headers: Headers that affect cache key generation
        cache_query_params: Whether to include query parameters in cache key
        invalidation_tags: Tags for cache invalidation
        etag_enabled: Whether to generate ETags
        last_modified_enabled: Whether to include Last-Modified headers
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            # Get cache manager
            cache_manager = get_response_cache_manager()

            # Configure caching for this endpoint
            endpoint = f"{request.method}:{request.endpoint}"
            config = CacheConfig(
                ttl=ttl,
                vary_headers=vary_headers,
                cache_query_params=cache_query_params,
                invalidation_tags=invalidation_tags or set(),
                etag_enabled=etag_enabled,
                last_modified_enabled=last_modified_enabled,
            )

            cache_manager.configure_endpoint(endpoint, config)

            # Generate cache key
            cache_key = cache_manager.generate_cache_key(endpoint, config)

            # Try to get cached response
            cached_result = await cache_manager.get_cached_response(cache_key, config)

            if cached_result:
                content, metadata = cached_result

                # Check conditional requests
                etag = metadata.get("etag")
                last_modified_str = metadata.get("last_modified")
                last_modified = None

                if last_modified_str:
                    try:
                        last_modified = datetime.fromisoformat(last_modified_str)
                    except ValueError:
                        pass

                if etag and cache_manager.check_conditional_request(
                    etag, last_modified
                ):
                    cache_manager.stats["conditional_hits"] += 1
                    response = Response(status=304)
                    if etag:
                        response.headers["ETag"] = etag
                    if last_modified:
                        response.headers["Last-Modified"] = last_modified.strftime(
                            "%a, %d %b %Y %H:%M:%S GMT"
                        )
                    return response

                # Return cached content with appropriate headers
                if isinstance(content, dict):
                    response = jsonify(content)
                else:
                    response = Response(content)

                # Add cache headers
                if etag:
                    response.headers["ETag"] = etag
                if last_modified:
                    response.headers["Last-Modified"] = last_modified.strftime(
                        "%a, %d %b %Y %H:%M:%S GMT"
                    )

                response.headers["X-Cache"] = "HIT"
                response.headers["X-Cache-Key"] = cache_key

                return response

            # Cache miss - execute function
            try:
                result = await func(*args, **kwargs)
                response_time_ms = (time.time() - start_time) * 1000

                # Extract content for caching
                if hasattr(result, "get_json"):
                    # It's a Response object
                    content = result.get_json()
                elif isinstance(result, Response):
                    content = result.get_data(as_text=True)
                else:
                    content = result

                # Cache the result
                await cache_manager.cache_response(
                    cache_key, content, config, response_time_ms
                )

                # Add cache headers to response
                if isinstance(result, Response):
                    response = result
                else:
                    if isinstance(result, dict):
                        response = jsonify(result)
                    else:
                        response = Response(result)

                if config.etag_enabled:
                    etag = cache_manager.generate_etag(content)
                    response.headers["ETag"] = etag

                if config.last_modified_enabled:
                    now = datetime.now(timezone.utc)
                    response.headers["Last-Modified"] = now.strftime(
                        "%a, %d %b %Y %H:%M:%S GMT"
                    )

                response.headers["X-Cache"] = "MISS"
                response.headers["X-Cache-Key"] = cache_key
                response.headers["Cache-Control"] = f"max-age={ttl}, public"

                return response

            except Exception as e:
                logger.error(f"Error in cached function {func.__name__}: {e}")
                raise

        return wrapper

    return decorator


# Convenience functions for common invalidation patterns
async def invalidate_capsule_responses(capsule_id: str = None) -> int:
    """Invalidate cached responses related to capsules."""
    cache_manager = get_response_cache_manager()
    tags = {"capsules"}
    if capsule_id:
        tags.add(f"capsule:{capsule_id}")
    return await cache_manager.invalidate_cache(tags)


async def invalidate_ai_responses(model: str = None) -> int:
    """Invalidate cached AI responses."""
    cache_manager = get_response_cache_manager()
    tags = {"ai_responses"}
    if model:
        tags.add(f"model:{model}")
    return await cache_manager.invalidate_cache(tags)


async def invalidate_user_responses(user_id: str) -> int:
    """Invalidate cached responses for a specific user."""
    cache_manager = get_response_cache_manager()
    return await cache_manager.invalidate_cache({f"user:{user_id}"})


# Background task management
async def start_response_cache_tasks():
    """Start response cache background tasks."""
    cache_manager = get_response_cache_manager()
    await cache_manager.start_background_tasks()


async def stop_response_cache_tasks():
    """Stop response cache background tasks."""
    cache_manager = get_response_cache_manager()
    await cache_manager.stop_background_tasks()
