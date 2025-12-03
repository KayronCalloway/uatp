"""
Database Read Replica Manager
============================

Production-grade read replica management system with:
- Automatic query routing (writes to primary, reads to replicas)
- Health monitoring for replica lag and availability
- Failover mechanisms when replicas are unavailable
- Load balancing across multiple read replicas
- Connection pooling per replica
- Performance metrics and monitoring
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, AsyncGenerator, Tuple
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
import asyncpg
from asyncpg import Pool, Connection

from .connection import DatabaseConfig, DatabaseManager

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Query type classification."""

    READ = "read"
    WRITE = "write"
    UNKNOWN = "unknown"


@dataclass
class ReplicaConfig:
    """Configuration for a read replica."""

    host: str
    port: int
    database: str
    username: str
    password: str
    max_lag_seconds: float = 5.0
    priority: int = 1  # Higher priority = preferred for reads
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    ssl_ca_path: Optional[str] = None


@dataclass
class ReplicaStatus:
    """Status information for a read replica."""

    host: str
    port: int
    is_healthy: bool = False
    lag_seconds: float = 0.0
    last_check: Optional[datetime] = None
    error_count: int = 0
    response_time_ms: float = 0.0
    connections_active: int = 0
    total_queries: int = 0


class ReplicaManager:
    """Manages individual read replica connections and health."""

    def __init__(self, config: ReplicaConfig, pool_config: DatabaseConfig):
        self.config = config
        self.pool_config = pool_config
        self.pool: Optional[Pool] = None
        self.status = ReplicaStatus(host=config.host, port=config.port)
        self._health_check_task: Optional[asyncio.Task] = None
        self._connected = False

    async def connect(self) -> None:
        """Establish connection pool to replica."""
        if self.pool is not None:
            logger.warning(
                f"Replica {self.config.host}:{self.config.port} already connected"
            )
            return

        try:
            logger.info(
                f"Connecting to read replica {self.config.host}:{self.config.port}"
            )

            connection_kwargs = {
                "host": self.config.host,
                "port": self.config.port,
                "database": self.config.database,
                "user": self.config.username,
                "password": self.config.password,
                "command_timeout": self.pool_config.command_timeout,
                "server_settings": {
                    "application_name": "uatp_capsule_engine_replica",
                    "timezone": "UTC",
                },
            }

            if self.config.ssl_enabled:
                connection_kwargs["ssl"] = "require"
                if self.config.ssl_cert_path:
                    connection_kwargs["ssl_cert"] = self.config.ssl_cert_path
                if self.config.ssl_key_path:
                    connection_kwargs["ssl_key"] = self.config.ssl_key_path
                if self.config.ssl_ca_path:
                    connection_kwargs["ssl_ca"] = self.config.ssl_ca_path

            self.pool = await asyncpg.create_pool(
                **connection_kwargs,
                min_size=max(
                    1, self.pool_config.min_connections // 2
                ),  # Fewer connections for replicas
                max_size=max(2, self.pool_config.max_connections // 2),
                max_inactive_connection_lifetime=self.pool_config.max_inactive_connection_lifetime,
                init=self._init_connection,
            )

            self._connected = True
            logger.info(
                f"Connected to read replica {self.config.host}:{self.config.port}"
            )

            # Start health monitoring
            self._health_check_task = asyncio.create_task(self._health_check_loop())

        except Exception as e:
            logger.error(
                f"Failed to connect to replica {self.config.host}:{self.config.port}: {e}"
            )
            self._connected = False
            self.status.is_healthy = False
            raise

    async def disconnect(self) -> None:
        """Disconnect from replica."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        if self.pool:
            await self.pool.close()
            self.pool = None
            self._connected = False
            self.status.is_healthy = False
            logger.info(
                f"Disconnected from replica {self.config.host}:{self.config.port}"
            )

    async def _init_connection(self, conn: Connection) -> None:
        """Initialize replica connections."""
        await conn.execute("SET timezone TO 'UTC'")
        await conn.execute("SET search_path TO public")
        await conn.execute("SET default_transaction_isolation TO 'read committed'")
        await conn.execute("SET transaction_read_only TO on")  # Ensure read-only

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get a connection from this replica's pool."""
        if not self.pool or not self.status.is_healthy:
            raise RuntimeError(
                f"Replica {self.config.host}:{self.config.port} is not available"
            )

        async with self.pool.acquire() as conn:
            try:
                self.status.connections_active += 1
                yield conn
                self.status.total_queries += 1
            except Exception as e:
                self.status.error_count += 1
                logger.error(
                    f"Error using replica {self.config.host}:{self.config.port}: {e}"
                )
                raise
            finally:
                self.status.connections_active = max(
                    0, self.status.connections_active - 1
                )

    async def health_check(self) -> ReplicaStatus:
        """Perform health check on this replica."""
        start_time = time.time()

        try:
            if not self.pool:
                self.status.is_healthy = False
                self.status.error_count += 1
                return self.status

            async with self.pool.acquire() as conn:
                # Test basic connectivity
                await conn.execute("SELECT 1")

                # Check replication lag
                lag_query = """
                SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds
                """
                try:
                    lag_result = await conn.fetchval(lag_query)
                    self.status.lag_seconds = (
                        float(lag_result) if lag_result is not None else 0.0
                    )
                except Exception:
                    # If we can't get lag info, assume it's acceptable
                    self.status.lag_seconds = 0.0

                # Check if lag is acceptable
                lag_acceptable = self.status.lag_seconds <= self.config.max_lag_seconds

                response_time = (time.time() - start_time) * 1000
                self.status.response_time_ms = response_time
                self.status.is_healthy = lag_acceptable
                self.status.last_check = datetime.now(timezone.utc)

                if not lag_acceptable:
                    logger.warning(
                        f"Replica {self.config.host}:{self.config.port} lag too high: "
                        f"{self.status.lag_seconds:.2f}s > {self.config.max_lag_seconds}s"
                    )

        except Exception as e:
            self.status.is_healthy = False
            self.status.error_count += 1
            self.status.last_check = datetime.now(timezone.utc)
            logger.error(
                f"Health check failed for replica {self.config.host}:{self.config.port}: {e}"
            )

        return self.status

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                await self.health_check()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"Health check loop error for replica {self.config.host}:{self.config.port}: {e}"
                )
                await asyncio.sleep(30)  # Wait longer on error


class ReadReplicaManager:
    """High-level manager for multiple read replicas with intelligent routing."""

    def __init__(self, primary_manager: DatabaseManager):
        self.primary_manager = primary_manager
        self.replicas: List[ReplicaManager] = []
        self.read_query_patterns = {
            # Common read-only query prefixes
            "select",
            "show",
            "describe",
            "explain",
            "with",
        }
        self.write_query_patterns = {
            # Write operation prefixes
            "insert",
            "update",
            "delete",
            "create",
            "drop",
            "alter",
            "truncate",
            "grant",
            "revoke",
        }

        # Performance metrics
        self.metrics = {
            "read_queries_routed": 0,
            "write_queries_routed": 0,
            "replica_failovers": 0,
            "total_read_time": 0.0,
            "total_write_time": 0.0,
        }

    async def add_replica(self, replica_config: ReplicaConfig) -> None:
        """Add a new read replica."""
        replica_manager = ReplicaManager(replica_config, self.primary_manager.config)
        await replica_manager.connect()
        self.replicas.append(replica_manager)
        logger.info(f"Added read replica: {replica_config.host}:{replica_config.port}")

    async def remove_replica(self, host: str, port: int) -> None:
        """Remove a read replica."""
        for i, replica in enumerate(self.replicas):
            if replica.config.host == host and replica.config.port == port:
                await replica.disconnect()
                self.replicas.pop(i)
                logger.info(f"Removed read replica: {host}:{port}")
                break

    async def disconnect_all(self) -> None:
        """Disconnect from all replicas."""
        for replica in self.replicas:
            await replica.disconnect()
        self.replicas.clear()
        logger.info("Disconnected from all read replicas")

    def classify_query(self, query: str) -> QueryType:
        """Classify query as read or write operation."""
        query_lower = query.strip().lower()

        # Extract first significant word
        words = query_lower.split()
        if not words:
            return QueryType.UNKNOWN

        first_word = words[0]

        # Handle common SQL syntax
        if first_word in self.read_query_patterns:
            return QueryType.READ
        elif first_word in self.write_query_patterns:
            return QueryType.WRITE
        elif first_word == "begin" or first_word == "start":
            # Transaction start - assume write to be safe
            return QueryType.WRITE
        elif first_word == "commit" or first_word == "rollback":
            # Transaction end - route to primary
            return QueryType.WRITE

        return QueryType.UNKNOWN

    def get_best_replica(self) -> Optional[ReplicaManager]:
        """Select the best available replica for read operations."""
        healthy_replicas = [r for r in self.replicas if r.status.is_healthy]

        if not healthy_replicas:
            return None

        # Sort by priority (higher first), then by response time and lag
        healthy_replicas.sort(
            key=lambda r: (
                -r.config.priority,  # Higher priority first (negative for reverse sort)
                r.status.response_time_ms,  # Lower response time first
                r.status.lag_seconds,  # Lower lag first
            )
        )

        # Use weighted random selection among top candidates
        top_replicas = healthy_replicas[
            : min(3, len(healthy_replicas))
        ]  # Top 3 candidates

        if len(top_replicas) == 1:
            return top_replicas[0]

        # Weight by inverse of response time and lag
        weights = []
        for replica in top_replicas:
            weight = 1.0 / (
                1.0
                + replica.status.response_time_ms / 100.0
                + replica.status.lag_seconds
            )
            weights.append(weight)

        # Weighted random selection
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(top_replicas)

        r = random.uniform(0, total_weight)
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if r <= cumulative:
                return top_replicas[i]

        return top_replicas[-1]  # Fallback

    @asynccontextmanager
    async def get_connection(
        self, query: str = ""
    ) -> AsyncGenerator[Tuple[Connection, str], None]:
        """Get a connection for the given query, routing to replica or primary."""
        query_type = self.classify_query(query) if query else QueryType.UNKNOWN
        start_time = time.time()

        try:
            if query_type == QueryType.READ:
                # Try to use a read replica
                replica = self.get_best_replica()
                if replica:
                    try:
                        async with replica.get_connection() as conn:
                            self.metrics["read_queries_routed"] += 1
                            yield conn, "replica"
                            self.metrics["total_read_time"] += time.time() - start_time
                            return
                    except Exception as e:
                        logger.warning(
                            f"Failed to use replica, falling back to primary: {e}"
                        )
                        self.metrics["replica_failovers"] += 1
                        # Fall through to primary

                # Fallback to primary for reads
                async with self.primary_manager.get_connection() as conn:
                    self.metrics["read_queries_routed"] += 1
                    yield conn, "primary"
                    self.metrics["total_read_time"] += time.time() - start_time

            else:
                # Use primary for writes and unknown queries
                async with self.primary_manager.get_connection() as conn:
                    if query_type == QueryType.WRITE:
                        self.metrics["write_queries_routed"] += 1
                        self.metrics["total_write_time"] += time.time() - start_time
                    yield conn, "primary"

        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise

    @asynccontextmanager
    async def get_transaction(self) -> AsyncGenerator[Connection, None]:
        """Get a transaction connection (always uses primary)."""
        async with self.primary_manager.get_transaction() as conn:
            yield conn

    async def execute(self, query: str, *args) -> str:
        """Execute a query with automatic routing."""
        async with self.get_connection(query) as (conn, source):
            result = await conn.execute(query, *args)
            logger.debug(f"Executed query on {source}: {query[:100]}...")
            return result

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows with automatic routing."""
        async with self.get_connection(query) as (conn, source):
            result = await conn.fetch(query, *args)
            logger.debug(f"Fetched {len(result)} rows from {source}")
            return result

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row with automatic routing."""
        async with self.get_connection(query) as (conn, source):
            result = await conn.fetchrow(query, *args)
            logger.debug(f"Fetched row from {source}")
            return result

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value with automatic routing."""
        async with self.get_connection(query) as (conn, source):
            result = await conn.fetchval(query, *args)
            logger.debug(f"Fetched value from {source}")
            return result

    def get_replica_status(self) -> List[Dict[str, Any]]:
        """Get status of all replicas."""
        return [
            {
                "host": replica.config.host,
                "port": replica.config.port,
                "is_healthy": replica.status.is_healthy,
                "lag_seconds": replica.status.lag_seconds,
                "response_time_ms": replica.status.response_time_ms,
                "error_count": replica.status.error_count,
                "connections_active": replica.status.connections_active,
                "total_queries": replica.status.total_queries,
                "priority": replica.config.priority,
                "max_lag_seconds": replica.config.max_lag_seconds,
                "last_check": replica.status.last_check.isoformat()
                if replica.status.last_check
                else None,
            }
            for replica in self.replicas
        ]

    def get_metrics(self) -> Dict[str, Any]:
        """Get read replica performance metrics."""
        total_queries = (
            self.metrics["read_queries_routed"] + self.metrics["write_queries_routed"]
        )

        avg_read_time = 0.0
        avg_write_time = 0.0

        if self.metrics["read_queries_routed"] > 0:
            avg_read_time = (
                self.metrics["total_read_time"] / self.metrics["read_queries_routed"]
            )

        if self.metrics["write_queries_routed"] > 0:
            avg_write_time = (
                self.metrics["total_write_time"] / self.metrics["write_queries_routed"]
            )

        return {
            "total_queries": total_queries,
            "read_queries": self.metrics["read_queries_routed"],
            "write_queries": self.metrics["write_queries_routed"],
            "read_percentage": self.metrics["read_queries_routed"]
            / max(total_queries, 1)
            * 100,
            "replica_failovers": self.metrics["replica_failovers"],
            "avg_read_time_ms": round(avg_read_time * 1000, 2),
            "avg_write_time_ms": round(avg_write_time * 1000, 2),
            "healthy_replicas": sum(1 for r in self.replicas if r.status.is_healthy),
            "total_replicas": len(self.replicas),
        }

    async def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.metrics = {
            "read_queries_routed": 0,
            "write_queries_routed": 0,
            "replica_failovers": 0,
            "total_read_time": 0.0,
            "total_write_time": 0.0,
        }
        logger.info("Read replica metrics reset")


# Factory function for easy integration
async def create_read_replica_manager(
    primary_manager: DatabaseManager, replica_configs: List[ReplicaConfig]
) -> ReadReplicaManager:
    """Create and configure a read replica manager."""
    replica_manager = ReadReplicaManager(primary_manager)

    for config in replica_configs:
        try:
            await replica_manager.add_replica(config)
        except Exception as e:
            logger.error(f"Failed to add replica {config.host}:{config.port}: {e}")
            # Continue with other replicas

    logger.info(
        f"Read replica manager created with {len(replica_manager.replicas)} replicas"
    )
    return replica_manager
