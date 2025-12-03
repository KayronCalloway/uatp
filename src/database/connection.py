"""
Database Connection Management
==============================

Production-grade PostgreSQL connection management with connection pooling,
health monitoring, and automatic reconnection capabilities.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, AsyncGenerator
from contextlib import asynccontextmanager
import asyncpg
from asyncpg import Pool, Connection

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration management."""

    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.database = os.getenv("DB_NAME", "uatp_capsule_engine")
        self.username = os.getenv("DB_USERNAME", "uatp_user")
        self.password = os.getenv("DB_PASSWORD", "uatp_password")

        # Connection pool settings
        self.min_connections = int(os.getenv("DB_MIN_CONNECTIONS", "5"))
        self.max_connections = int(os.getenv("DB_MAX_CONNECTIONS", "20"))
        self.max_inactive_connection_lifetime = float(
            os.getenv("DB_MAX_INACTIVE_TIME", "300.0")
        )

        # Connection timeout settings
        self.connection_timeout = float(os.getenv("DB_CONNECTION_TIMEOUT", "60.0"))
        self.command_timeout = float(os.getenv("DB_COMMAND_TIMEOUT", "60.0"))

        # SSL and security
        self.ssl_enabled = os.getenv("DB_SSL_ENABLED", "false").lower() == "true"
        self.ssl_cert_path = os.getenv("DB_SSL_CERT_PATH")
        self.ssl_key_path = os.getenv("DB_SSL_KEY_PATH")
        self.ssl_ca_path = os.getenv("DB_SSL_CA_PATH")

    @property
    def dsn(self) -> str:
        """Get database connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_connection_kwargs(self) -> Dict[str, Any]:
        """Get connection parameters for asyncpg."""
        kwargs = {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.username,
            "password": self.password,
            "command_timeout": self.command_timeout,
            "server_settings": {
                "application_name": "uatp_capsule_engine",
                "timezone": "UTC",
            },
        }

        if self.ssl_enabled:
            kwargs["ssl"] = "require"
            if self.ssl_cert_path:
                kwargs["ssl_cert"] = self.ssl_cert_path
            if self.ssl_key_path:
                kwargs["ssl_key"] = self.ssl_key_path
            if self.ssl_ca_path:
                kwargs["ssl_ca"] = self.ssl_ca_path

        return kwargs


class DatabaseManager:
    """Production-grade database manager with connection pooling."""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.pool: Optional[Pool] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._connected = False

        # Metrics
        self.connection_count = 0
        self.query_count = 0
        self.error_count = 0
        self.last_health_check = None

    def initialize(self) -> None:
        """Synchronous wrapper for initializing the connection pool.

        In non-async (CLI) contexts we can't await the async ``connect`` method
        directly, so this helper calls it via ``asyncio.run``.  If an event loop
        is already running, we raise an error to avoid the ``asyncio.run`` nested
        event-loop issue – callers in an async context should instead use
        ``await db_manager.connect()``.
        """
        if self._connected:
            return  # Already connected – nothing to do.

        # If we're already in an event loop we shouldn't call asyncio.run().
        try:
            running_loop = asyncio.get_running_loop()
            if running_loop.is_running():
                raise RuntimeError(
                    "DatabaseManager.initialize() called from within an active "
                    "event loop. Use `await db_manager.connect()` instead."
                )
        except RuntimeError:
            # No running loop detected, safe to use asyncio.run()
            pass

        asyncio.run(self.connect())

    async def connect(self) -> None:
        """Establish database connection pool."""
        if self.pool is not None:
            logger.warning("Database pool already exists")
            return

        try:
            logger.info(
                f"Connecting to PostgreSQL at {self.config.host}:{self.config.port}"
            )

            # Create connection pool
            self.pool = await asyncpg.create_pool(
                **self.config.get_connection_kwargs(),
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                max_inactive_connection_lifetime=self.config.max_inactive_connection_lifetime,
                init=self._init_connection,
            )

            self._connected = True
            logger.info(
                f"Database pool created with {self.config.min_connections}-{self.config.max_connections} connections"
            )

            # Start health check task
            self._health_check_task = asyncio.create_task(self._health_check_loop())

            # Verify connection with test query
            async with self.get_connection() as conn:
                await conn.execute("SELECT 1")
                logger.info("Database connection verified")

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self._connected = False
            raise

    async def disconnect(self) -> None:
        """Close database connection pool."""
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
            logger.info("Database pool closed")

    async def _init_connection(self, conn: Connection) -> None:
        """Initialize new database connections."""
        # Set up connection-specific settings
        await conn.execute("SET timezone TO 'UTC'")
        await conn.execute("SET search_path TO public")

        # Register custom types if needed
        # await conn.set_type_codec('json', encoder=json.dumps, decoder=json.loads, schema='pg_catalog')

        self.connection_count += 1
        logger.debug(f"Initialized database connection #{self.connection_count}")

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get a database connection from the pool."""
        if not self.pool:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            try:
                yield conn
            except Exception as e:
                self.error_count += 1
                logger.error(f"Database operation failed: {e}")
                raise

    @asynccontextmanager
    async def get_transaction(self) -> AsyncGenerator[Connection, None]:
        """Get a database transaction."""
        async with self.get_connection() as conn:
            async with conn.transaction():
                yield conn

    async def execute(self, query: str, *args) -> str:
        """Execute a query and return the status."""
        from src.observability.performance_monitor import get_monitor

        async def _execute():
            async with self.get_connection() as conn:
                result = await conn.execute(query, *args)
                self.query_count += 1
                return result

        # Track performance
        return await get_monitor().track_query("execute", _execute())

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Fetch multiple rows."""
        from src.observability.performance_monitor import get_monitor

        async def _fetch():
            async with self.get_connection() as conn:
                result = await conn.fetch(query, *args)
                self.query_count += 1
                # Update pool metrics
                get_monitor().update_pool_metrics(
                    pool_size=self.pool.get_size(),
                    active_connections=self.pool.get_size() - self.pool.get_idle_size(),
                )
                return result

        # Track performance
        return await get_monitor().track_query("fetch", _fetch())

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Fetch a single row."""
        from src.observability.performance_monitor import get_monitor

        async def _fetchrow():
            async with self.get_connection() as conn:
                result = await conn.fetchrow(query, *args)
                self.query_count += 1
                return result

        # Track performance
        return await get_monitor().track_query("fetchrow", _fetchrow())

    async def fetchval(self, query: str, *args) -> Any:
        """Fetch a single value."""
        from src.observability.performance_monitor import get_monitor

        async def _fetchval():
            async with self.get_connection() as conn:
                result = await conn.fetchval(query, *args)
                self.query_count += 1
                return result

        # Track performance
        return await get_monitor().track_query("fetchval", _fetchval())

    async def execute_many(self, query: str, args_list: List[tuple]) -> None:
        """Execute a query multiple times with different parameters."""
        async with self.get_connection() as conn:
            await conn.executemany(query, args_list)
            self.query_count += len(args_list)

    async def copy_from_table(
        self, table_name: str, *, output, columns=None, schema_name=None, delimiter="\t"
    ):
        """Copy data from a table to a file-like object."""
        async with self.get_connection() as conn:
            return await conn.copy_from_table(
                table_name,
                output=output,
                columns=columns,
                schema_name=schema_name,
                delimiter=delimiter,
            )

    async def copy_to_table(
        self, table_name: str, *, source, columns=None, schema_name=None, delimiter="\t"
    ):
        """Copy data from a file-like object to a table."""
        async with self.get_connection() as conn:
            return await conn.copy_to_table(
                table_name,
                source=source,
                columns=columns,
                schema_name=schema_name,
                delimiter=delimiter,
            )

    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            start_time = datetime.now(timezone.utc)

            async with self.get_connection() as conn:
                # Test basic connectivity
                await conn.execute("SELECT 1")

                # Check database version
                version = await conn.fetchval("SELECT version()")

                # Check pool status
                pool_info = {
                    "size": self.pool.get_size(),
                    "min_size": self.pool.get_min_size(),
                    "max_size": self.pool.get_max_size(),
                    "idle_size": self.pool.get_idle_size(),
                }

                response_time = (
                    datetime.now(timezone.utc) - start_time
                ).total_seconds()

                self.last_health_check = datetime.now(timezone.utc)

                return {
                    "status": "healthy",
                    "connected": self._connected,
                    "version": version,
                    "pool": pool_info,
                    "response_time_ms": round(response_time * 1000, 2),
                    "connection_count": self.connection_count,
                    "query_count": self.query_count,
                    "error_count": self.error_count,
                    "last_check": self.last_health_check.isoformat(),
                }

        except Exception as e:
            self.error_count += 1
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "last_check": datetime.now(timezone.utc).isoformat(),
            }

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                health = await self.health_check()

                if health["status"] != "healthy":
                    logger.warning(f"Database health check failed: {health}")
                else:
                    logger.debug(
                        f"Database health check passed: {health['response_time_ms']}ms"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def get_metrics(self) -> Dict[str, Any]:
        """Get database metrics."""
        pool_metrics = {}
        if self.pool:
            pool_metrics = {
                "pool_size": self.pool.get_size(),
                "pool_min_size": self.pool.get_min_size(),
                "pool_max_size": self.pool.get_max_size(),
                "pool_idle_size": self.pool.get_idle_size(),
            }

        return {
            "connected": self._connected,
            "connection_count": self.connection_count,
            "query_count": self.query_count,
            "error_count": self.error_count,
            "last_health_check": self.last_health_check.isoformat()
            if self.last_health_check
            else None,
            **pool_metrics,
        }

    async def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.connection_count = 0
        self.query_count = 0
        self.error_count = 0
        logger.info("Database statistics reset")


# Global database manager instance
_global_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _global_db_manager
    if _global_db_manager is None:
        _global_db_manager = DatabaseManager()
    return _global_db_manager


async def initialize_database(
    config: Optional[DatabaseConfig] = None,
) -> DatabaseManager:
    """Initialize the global database manager."""
    global _global_db_manager
    _global_db_manager = DatabaseManager(config)
    await _global_db_manager.connect()
    logger.info("Database manager initialized")
    return _global_db_manager


async def close_database() -> None:
    """Close the global database manager."""
    global _global_db_manager
    if _global_db_manager:
        await _global_db_manager.disconnect()
        _global_db_manager = None
        logger.info("Database manager closed")
