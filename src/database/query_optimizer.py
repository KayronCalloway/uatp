"""
Database Query Optimization and Caching Layer
Advanced query optimization with intelligent caching strategies
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict

import redis
from sqlalchemy import and_, text
from sqlalchemy.orm import Query, Session

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Advanced query optimization and caching system"""

    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client
        self.cache_prefix = "uatp:query_cache:"
        self.default_ttl = 300  # 5 minutes
        self.stats = {"cache_hits": 0, "cache_misses": 0, "queries_optimized": 0}

    def cache_key(self, query: str, params: Dict = None) -> str:
        """Generate cache key for query and parameters"""
        key_data = {"query": query, "params": params or {}}
        key_json = json.dumps(key_data, sort_keys=True)
        return self.cache_prefix + hashlib.md5(key_json.encode()).hexdigest()

    def cached_query(self, ttl: int = None):
        """Decorator for caching query results"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.redis_client:
                    return func(*args, **kwargs)

                # Generate cache key
                cache_key = self.cache_key(str(func.__name__), kwargs)

                # Try cache first
                try:
                    cached_result = self.redis_client.get(cache_key)
                    if cached_result:
                        self.stats["cache_hits"] += 1
                        return json.loads(cached_result)
                except Exception as e:
                    logger.warning(f"Cache read error: {e}")

                # Execute query
                result = func(*args, **kwargs)
                self.stats["cache_misses"] += 1

                # Cache result
                try:
                    cache_ttl = ttl or self.default_ttl
                    self.redis_client.setex(
                        cache_key, cache_ttl, json.dumps(result, default=str)
                    )
                except Exception as e:
                    logger.warning(f"Cache write error: {e}")

                return result

            return wrapper

        return decorator

    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        if not self.redis_client:
            return

        try:
            keys = self.redis_client.keys(f"{self.cache_prefix}{pattern}*")
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")

    def optimize_capsule_queries(self, session: Session) -> Dict[str, Any]:
        """Optimize common capsule queries with indexes and caching"""

        # Add indexes for common query patterns
        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_capsules_type_status ON capsules(type, status)",
            "CREATE INDEX IF NOT EXISTS idx_capsules_timestamp ON capsules(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_capsules_creator ON capsules(creator_id)",
            "CREATE INDEX IF NOT EXISTS idx_verification_merkle ON verification(merkle_root)",
            "CREATE INDEX IF NOT EXISTS idx_reasoning_capsule ON reasoning_steps(capsule_id)",
        ]

        created_indexes = []
        for statement in index_statements:
            try:
                session.execute(text(statement))
                created_indexes.append(statement.split()[-1])  # Extract index name
                self.stats["queries_optimized"] += 1
            except Exception as e:
                logger.warning(f"Index creation skipped: {e}")

        session.commit()
        return {"indexes_created": created_indexes}

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get query optimization and cache statistics"""
        cache_hit_rate = 0
        total_queries = self.stats["cache_hits"] + self.stats["cache_misses"]

        if total_queries > 0:
            cache_hit_rate = (self.stats["cache_hits"] / total_queries) * 100

        return {
            "cache_stats": {
                "hits": self.stats["cache_hits"],
                "misses": self.stats["cache_misses"],
                "hit_rate_percent": round(cache_hit_rate, 2),
                "total_queries": total_queries,
            },
            "optimization_stats": {
                "queries_optimized": self.stats["queries_optimized"]
            },
            "redis_status": self.redis_client is not None,
            "timestamp": datetime.utcnow().isoformat(),
        }


class CapsuleQueryBuilder:
    """Specialized query builder for capsule operations"""

    def __init__(self, optimizer: QueryOptimizer = None):
        self.optimizer = optimizer

    @staticmethod
    def build_capsule_search(
        session: Session,
        capsule_type: str = None,
        status: str = None,
        creator_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Query:
        """Build optimized capsule search query"""

        # Import here to avoid circular imports
        from .models import Capsule

        query = session.query(Capsule)

        # Add filters
        filters = []
        if capsule_type:
            filters.append(Capsule.type == capsule_type)
        if status:
            filters.append(Capsule.status == status)
        if creator_id:
            filters.append(Capsule.creator_id == creator_id)
        if start_date:
            filters.append(Capsule.timestamp >= start_date)
        if end_date:
            filters.append(Capsule.timestamp <= end_date)

        if filters:
            query = query.filter(and_(*filters))

        # Optimize ordering and pagination
        query = query.order_by(Capsule.timestamp.desc())
        query = query.offset(offset).limit(limit)

        return query

    def get_capsule_analytics(self, session: Session, days: int = 30) -> Dict[str, Any]:
        """Get capsule analytics with caching"""

        @ self.optimizer.cached_query(ttl=600) if self.optimizer else lambda x: x
        def _get_analytics():
            from .models import Capsule

            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Total capsules
            total_query = session.query(Capsule).filter(Capsule.timestamp >= start_date)
            total_capsules = total_query.count()

            # Capsules by type
            type_stats = session.execute(
                text(
                    """
                SELECT type, COUNT(*) as count
                FROM capsules
                WHERE timestamp >= :start_date
                GROUP BY type
            """
                ),
                {"start_date": start_date},
            ).fetchall()

            # Capsules by status
            status_stats = session.execute(
                text(
                    """
                SELECT status, COUNT(*) as count
                FROM capsules
                WHERE timestamp >= :start_date
                GROUP BY status
            """
                ),
                {"start_date": start_date},
            ).fetchall()

            # Daily capsule creation
            daily_stats = session.execute(
                text(
                    """
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM capsules
                WHERE timestamp >= :start_date
                GROUP BY DATE(timestamp)
                ORDER BY date
            """
                ),
                {"start_date": start_date},
            ).fetchall()

            return {
                "total_capsules": total_capsules,
                "type_breakdown": {row[0]: row[1] for row in type_stats},
                "status_breakdown": {row[0]: row[1] for row in status_stats},
                "daily_creation": [
                    {"date": str(row[0]), "count": row[1]} for row in daily_stats
                ],
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days,
                },
            }

        return _get_analytics()


# Global instances
query_optimizer = QueryOptimizer()
capsule_query_builder = CapsuleQueryBuilder(query_optimizer)


def setup_query_optimization(redis_client: redis.Redis = None):
    """Setup global query optimization with Redis client"""
    global query_optimizer, capsule_query_builder

    query_optimizer = QueryOptimizer(redis_client)
    capsule_query_builder = CapsuleQueryBuilder(query_optimizer)

    logger.info("Query optimization system initialized")
    return query_optimizer
