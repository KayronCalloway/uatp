"""
Production Database Optimization for UATP Capsule Engine

Provides:
- Advanced connection pooling
- Query performance monitoring
- Index recommendations
- Connection lifecycle management
- Read replica support
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

logger = logging.getLogger(__name__)


class ProductionDatabaseConfig:
    """Production-optimized database configuration."""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 40,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        echo: bool = False,
        read_replica_url: Optional[str] = None,
    ):
        """
        Initialize production database configuration.

        Args:
            database_url: Primary database connection string
            pool_size: Number of connections to maintain (default: 20)
            max_overflow: Max connections beyond pool_size (default: 40)
            pool_timeout: Seconds to wait for connection (default: 30)
            pool_recycle: Recycle connections after N seconds (default: 3600)
            pool_pre_ping: Test connections before use (default: True)
            echo: Log all SQL statements (default: False)
            read_replica_url: Optional read replica connection string
        """
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.echo = echo
        self.read_replica_url = read_replica_url

        # Performance metrics
        self.slow_query_threshold = 1.0  # seconds
        self.query_count = 0
        self.slow_query_count = 0
        self.total_query_time = 0.0

    def create_primary_engine(self) -> AsyncEngine:
        """Create primary database engine (read/write)."""

        # Determine if SQLite (no pooling) or real DB
        is_sqlite = "sqlite" in self.database_url

        if is_sqlite:
            logger.info("Creating SQLite engine with NullPool")
            engine = create_async_engine(
                self.database_url,
                poolclass=NullPool,
                echo=self.echo,
            )
        else:
            logger.info(
                f"Creating PostgreSQL engine: pool_size={self.pool_size}, "
                f"max_overflow={self.max_overflow}"
            )
            engine = create_async_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                pool_pre_ping=self.pool_pre_ping,
                echo=self.echo,
                # PostgreSQL-specific optimizations
                connect_args={
                    "server_settings": {
                        "application_name": "uatp_capsule_engine",
                        "jit": "off",  # Disable JIT for faster query planning
                    },
                    "command_timeout": 60,  # 60 second query timeout
                },
            )

        # Add event listeners for monitoring
        self._add_performance_listeners(engine)

        return engine

    def create_read_replica_engine(self) -> Optional[AsyncEngine]:
        """Create read replica engine if configured."""
        if not self.read_replica_url:
            return None

        logger.info("Creating read replica engine")

        is_sqlite = "sqlite" in self.read_replica_url

        if is_sqlite:
            engine = create_async_engine(
                self.read_replica_url,
                poolclass=NullPool,
                echo=self.echo,
            )
        else:
            engine = create_async_engine(
                self.read_replica_url,
                poolclass=QueuePool,
                pool_size=self.pool_size // 2,  # Smaller pool for replica
                max_overflow=self.max_overflow // 2,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                pool_pre_ping=self.pool_pre_ping,
                echo=self.echo,
            )

        return engine

    def _add_performance_listeners(self, engine: AsyncEngine):
        """Add event listeners for query performance monitoring."""

        @event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Record query start time."""
            context._query_start_time = time.time()

        @event.listens_for(engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Log slow queries and update metrics."""
            total_time = time.time() - context._query_start_time

            self.query_count += 1
            self.total_query_time += total_time

            if total_time > self.slow_query_threshold:
                self.slow_query_count += 1
                logger.warning(
                    f"Slow query detected ({total_time:.3f}s): {statement[:200]}..."
                )

        @event.listens_for(engine.sync_engine, "connect")
        def on_connect(dbapi_conn, connection_record):
            """Configure connection on creation."""
            logger.debug("New database connection established")

    def get_performance_metrics(self) -> dict:
        """Get database performance metrics."""
        avg_query_time = (
            self.total_query_time / self.query_count if self.query_count > 0 else 0
        )

        return {
            "total_queries": self.query_count,
            "slow_queries": self.slow_query_count,
            "slow_query_rate": (
                self.slow_query_count / self.query_count if self.query_count > 0 else 0
            ),
            "avg_query_time_seconds": avg_query_time,
            "total_query_time_seconds": self.total_query_time,
        }


class OptimizedDatabaseManager:
    """
    Production database manager with read replica support and performance monitoring.
    """

    def __init__(self, config: ProductionDatabaseConfig):
        """Initialize database manager with production config."""
        self.config = config
        self.primary_engine: Optional[AsyncEngine] = None
        self.replica_engine: Optional[AsyncEngine] = None
        self.primary_session_factory = None
        self.replica_session_factory = None

    async def initialize(self):
        """Initialize database engines and session factories."""
        # Create primary engine (read/write)
        self.primary_engine = self.config.create_primary_engine()
        self.primary_session_factory = sessionmaker(
            self.primary_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create read replica engine if configured
        self.replica_engine = self.config.create_read_replica_engine()
        if self.replica_engine:
            self.replica_session_factory = sessionmaker(
                self.replica_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

        logger.info("Database manager initialized")

    @asynccontextmanager
    async def get_session(
        self, read_only: bool = False
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with automatic transaction management.

        Args:
            read_only: If True and replica configured, use read replica

        Yields:
            AsyncSession: Database session
        """
        # Choose engine based on read_only flag and replica availability
        if read_only and self.replica_session_factory:
            session_factory = self.replica_session_factory
        else:
            session_factory = self.primary_session_factory

        if not session_factory:
            raise RuntimeError("Database not initialized")

        session = session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def health_check(self) -> dict:
        """
        Perform database health check.

        Returns:
            dict: Health status including connection test and metrics
        """
        try:
            # Test primary database
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))

            primary_healthy = True
        except Exception as e:
            logger.error(f"Primary database health check failed: {e}")
            primary_healthy = False

        # Test replica if configured
        replica_healthy = None
        if self.replica_session_factory:
            try:
                async with self.get_session(read_only=True) as session:
                    await session.execute(text("SELECT 1"))
                replica_healthy = True
            except Exception as e:
                logger.error(f"Replica database health check failed: {e}")
                replica_healthy = False

        return {
            "primary_healthy": primary_healthy,
            "replica_healthy": replica_healthy,
            "metrics": self.config.get_performance_metrics(),
        }

    async def get_pool_status(self) -> dict:
        """Get connection pool status."""
        if not self.primary_engine:
            return {"error": "Database not initialized"}

        pool = self.primary_engine.pool

        return {
            "pool_size": getattr(pool, "size", lambda: 0)(),
            "checked_in": getattr(pool, "checkedin", lambda: 0)(),
            "checked_out": getattr(pool, "checkedout", lambda: 0)(),
            "overflow": getattr(pool, "overflow", lambda: 0)(),
            "pool_status": str(pool),
        }

    async def close(self):
        """Close all database connections."""
        if self.primary_engine:
            await self.primary_engine.dispose()
            logger.info("Primary database engine disposed")

        if self.replica_engine:
            await self.replica_engine.dispose()
            logger.info("Replica database engine disposed")


# Indexes to create for production performance
PRODUCTION_INDEXES = """
-- Indexes for CapsuleModel
CREATE INDEX IF NOT EXISTS idx_capsules_timestamp ON capsules(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_capsules_status ON capsules(status);
CREATE INDEX IF NOT EXISTS idx_capsules_type ON capsules(capsule_type);
CREATE INDEX IF NOT EXISTS idx_capsules_signer ON capsules(signer);
CREATE INDEX IF NOT EXISTS idx_capsules_timestamp_status ON capsules(timestamp DESC, status);

-- Indexes for WebAuthn credentials (if table exists)
-- CREATE INDEX IF NOT EXISTS idx_webauthn_user_id ON webauthn_credentials(user_id);
-- CREATE INDEX IF NOT EXISTS idx_webauthn_credential_id ON webauthn_credentials(credential_id);

-- Indexes for mobile device tracking (if table exists)
-- CREATE INDEX IF NOT EXISTS idx_mobile_devices_user_id ON mobile_devices(user_id);
-- CREATE INDEX IF NOT EXISTS idx_mobile_devices_device_id ON mobile_devices(device_id);
"""


async def apply_production_indexes(engine: AsyncEngine):
    """Apply production indexes to database."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text(PRODUCTION_INDEXES))
        logger.info("Production indexes applied successfully")
    except Exception as e:
        logger.error(f"Failed to apply production indexes: {e}")


async def analyze_query_performance(session: AsyncSession, query_sql: str) -> dict:
    """
    Analyze query performance using EXPLAIN ANALYZE.

    Args:
        session: Database session
        query_sql: SQL query to analyze

    Returns:
        dict: Query execution plan and performance metrics
    """
    try:
        # Run EXPLAIN ANALYZE
        result = await session.execute(text(f"EXPLAIN ANALYZE {query_sql}"))
        explain_output = result.fetchall()

        return {
            "query": query_sql,
            "explain_plan": [str(row) for row in explain_output],
        }
    except Exception as e:
        logger.error(f"Query analysis failed: {e}")
        return {"error": str(e)}
