#!/usr/bin/env python3
"""
PostgreSQL Database Schema for UATP Capsule Engine
=================================================

This module defines the PostgreSQL database schema and migration utilities
for the UATP system, providing scalable storage for production environments.
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

import asyncpg

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://uatp:uatp@localhost:5432/uatp")
MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS", "20"))
MIN_CONNECTIONS = int(os.getenv("DB_MIN_CONNECTIONS", "5"))


@dataclass
class PostgreSQLConfig:
    """PostgreSQL configuration."""

    host: str = "localhost"
    port: int = 5432
    database: str = "uatp"
    user: str = "uatp"
    password: str = "uatp"
    max_connections: int = MAX_CONNECTIONS
    min_connections: int = MIN_CONNECTIONS


class PostgreSQLManager:
    """PostgreSQL database manager for UATP system."""

    def __init__(self, config: PostgreSQLConfig = None):
        self.config = config or PostgreSQLConfig()
        self.pool = None

        logger.info(" PostgreSQL Manager initialized")
        logger.info(f"   Host: {self.config.host}:{self.config.port}")
        logger.info(f"   Database: {self.config.database}")
        logger.info(f"   User: {self.config.user}")
        logger.info(
            f"   Connection pool: {self.config.min_connections}-{self.config.max_connections}"
        )

    async def create_connection_pool(self):
        """Create PostgreSQL connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=30,
            )
            logger.info("[OK] PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"[ERROR] Failed to create connection pool: {e}")
            raise

    async def close_connection_pool(self):
        """Close PostgreSQL connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info(" PostgreSQL connection pool closed")

    async def create_schema(self):
        """Create the complete database schema."""

        schema_sql = """
        -- Enable UUID extension
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";

        -- Create custom types
        CREATE TYPE capsule_type AS ENUM (
            'interaction_capsule',
            'reasoning_capsule',
            'consent_capsule',
            'perspective_capsule',
            'economic_capsule',
            'specialized_capsule'
        );

        CREATE TYPE capsule_status AS ENUM (
            'active',
            'archived',
            'deleted',
            'under_review'
        );

        CREATE TYPE platform_type AS ENUM (
            'openai',
            'anthropic',
            'cursor',
            'windsurf',
            'claude_code',
            'other'
        );

        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            roles TEXT[] DEFAULT ARRAY['user'],
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_login TIMESTAMP WITH TIME ZONE,
            metadata JSONB DEFAULT '{}'::jsonb,

            -- Indexes
            CONSTRAINT users_username_check CHECK (length(username) >= 3),
            CONSTRAINT users_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')
        );

        -- Capsules table
        CREATE TABLE IF NOT EXISTS capsules (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            capsule_id VARCHAR(255) UNIQUE NOT NULL,
            type capsule_type NOT NULL,
            status capsule_status DEFAULT 'active',
            platform platform_type NOT NULL,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            session_id VARCHAR(255),
            model VARCHAR(100),

            -- Content fields
            user_message TEXT,
            ai_response TEXT,
            content TEXT,
            reasoning_trace JSONB,
            metadata JSONB DEFAULT '{}'::jsonb,

            -- Scoring and quality
            significance_score FLOAT DEFAULT 0.0,
            confidence_score FLOAT DEFAULT 0.0,
            quality_score FLOAT DEFAULT 0.0,

            -- Relationships
            parent_capsule_id UUID REFERENCES capsules(id),
            merged_from_ids UUID[],

            -- Timestamps
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

            -- Constraints
            CONSTRAINT capsules_significance_score_check CHECK (significance_score >= 0.0 AND significance_score <= 10.0),
            CONSTRAINT capsules_confidence_score_check CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
            CONSTRAINT capsules_quality_score_check CHECK (quality_score >= 0.0 AND quality_score <= 100.0)
        );

        -- Capsule chains table
        CREATE TABLE IF NOT EXISTS capsule_chains (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            chain_id VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255),
            description TEXT,
            root_capsule_id UUID REFERENCES capsules(id),
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            metadata JSONB DEFAULT '{}'::jsonb,
            is_active BOOLEAN DEFAULT TRUE
        );

        -- Chain seals table
        CREATE TABLE IF NOT EXISTS chain_seals (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            chain_id UUID REFERENCES capsule_chains(id) ON DELETE CASCADE,
            seal_id VARCHAR(255) UNIQUE NOT NULL,
            capsule_id UUID REFERENCES capsules(id),
            seal_hash VARCHAR(255) NOT NULL,
            signature TEXT,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            sealed_by UUID REFERENCES users(id),
            metadata JSONB DEFAULT '{}'::jsonb
        );

        -- Sessions table
        CREATE TABLE IF NOT EXISTS sessions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            session_id VARCHAR(255) UNIQUE NOT NULL,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            platform platform_type NOT NULL,
            started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            ended_at TIMESTAMP WITH TIME ZONE,
            last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            capsule_count INTEGER DEFAULT 0,
            total_significance FLOAT DEFAULT 0.0,
            metadata JSONB DEFAULT '{}'::jsonb,
            is_active BOOLEAN DEFAULT TRUE
        );

        -- Refresh tokens table
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            token_hash VARCHAR(255) UNIQUE NOT NULL,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            revoked_at TIMESTAMP WITH TIME ZONE,
            is_active BOOLEAN DEFAULT TRUE
        );

        -- Audit log table
        CREATE TABLE IF NOT EXISTS audit_log (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES users(id),
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(50) NOT NULL,
            resource_id VARCHAR(255),
            details JSONB DEFAULT '{}'::jsonb,
            ip_address INET,
            user_agent TEXT,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Performance metrics table
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            metric_name VARCHAR(100) NOT NULL,
            metric_value FLOAT NOT NULL,
            metric_unit VARCHAR(20),
            labels JSONB DEFAULT '{}'::jsonb,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """

        async with self.pool.acquire() as conn:
            await conn.execute(schema_sql)
            logger.info("[OK] PostgreSQL schema created successfully")

    async def create_indexes(self):
        """Create database indexes for performance."""

        indexes_sql = """
        -- Users indexes
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
        CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

        -- Capsules indexes
        CREATE INDEX IF NOT EXISTS idx_capsules_capsule_id ON capsules(capsule_id);
        CREATE INDEX IF NOT EXISTS idx_capsules_type ON capsules(type);
        CREATE INDEX IF NOT EXISTS idx_capsules_status ON capsules(status);
        CREATE INDEX IF NOT EXISTS idx_capsules_platform ON capsules(platform);
        CREATE INDEX IF NOT EXISTS idx_capsules_user_id ON capsules(user_id);
        CREATE INDEX IF NOT EXISTS idx_capsules_session_id ON capsules(session_id);
        CREATE INDEX IF NOT EXISTS idx_capsules_significance_score ON capsules(significance_score);
        CREATE INDEX IF NOT EXISTS idx_capsules_created_at ON capsules(created_at);
        CREATE INDEX IF NOT EXISTS idx_capsules_parent_capsule_id ON capsules(parent_capsule_id);

        -- Composite indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_capsules_user_platform ON capsules(user_id, platform);
        CREATE INDEX IF NOT EXISTS idx_capsules_type_significance ON capsules(type, significance_score);
        CREATE INDEX IF NOT EXISTS idx_capsules_platform_created ON capsules(platform, created_at);

        -- JSONB indexes for metadata queries
        CREATE INDEX IF NOT EXISTS idx_capsules_metadata_gin ON capsules USING gin(metadata);
        CREATE INDEX IF NOT EXISTS idx_capsules_reasoning_trace_gin ON capsules USING gin(reasoning_trace);

        -- Sessions indexes
        CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_platform ON sessions(platform);
        CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at);
        CREATE INDEX IF NOT EXISTS idx_sessions_is_active ON sessions(is_active);

        -- Chain seals indexes
        CREATE INDEX IF NOT EXISTS idx_chain_seals_chain_id ON chain_seals(chain_id);
        CREATE INDEX IF NOT EXISTS idx_chain_seals_seal_id ON chain_seals(seal_id);
        CREATE INDEX IF NOT EXISTS idx_chain_seals_capsule_id ON chain_seals(capsule_id);
        CREATE INDEX IF NOT EXISTS idx_chain_seals_timestamp ON chain_seals(timestamp);

        -- Refresh tokens indexes
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
        CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

        -- Audit log indexes
        CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
        CREATE INDEX IF NOT EXISTS idx_audit_log_resource_type ON audit_log(resource_type);
        CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);

        -- Performance metrics indexes
        CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON performance_metrics(metric_name);
        CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
        """

        async with self.pool.acquire() as conn:
            await conn.execute(indexes_sql)
            logger.info("[OK] PostgreSQL indexes created successfully")

    async def create_functions(self):
        """Create database functions and triggers."""

        functions_sql = """
        -- Function to update the updated_at timestamp
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        -- Triggers for updated_at columns
        CREATE OR REPLACE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        CREATE OR REPLACE TRIGGER update_capsules_updated_at
            BEFORE UPDATE ON capsules
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        CREATE OR REPLACE TRIGGER update_capsule_chains_updated_at
            BEFORE UPDATE ON capsule_chains
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();

        -- Function to calculate capsule statistics
        CREATE OR REPLACE FUNCTION get_capsule_stats(user_id_param UUID DEFAULT NULL)
        RETURNS TABLE(
            total_capsules BIGINT,
            active_capsules BIGINT,
            avg_significance FLOAT,
            platforms JSONB,
            types JSONB
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT
                COUNT(*)::BIGINT as total_capsules,
                COUNT(CASE WHEN status = 'active' THEN 1 END)::BIGINT as active_capsules,
                AVG(significance_score)::FLOAT as avg_significance,
                jsonb_object_agg(platform, platform_count) as platforms,
                jsonb_object_agg(type, type_count) as types
            FROM (
                SELECT
                    c.*,
                    COUNT(*) OVER (PARTITION BY c.platform) as platform_count,
                    COUNT(*) OVER (PARTITION BY c.type) as type_count
                FROM capsules c
                WHERE (user_id_param IS NULL OR c.user_id = user_id_param)
                AND c.status = 'active'
            ) stats;
        END;
        $$ LANGUAGE plpgsql;

        -- Function to search capsules with full-text search
        CREATE OR REPLACE FUNCTION search_capsules(
            search_query TEXT,
            platform_filter platform_type DEFAULT NULL,
            user_id_param UUID DEFAULT NULL,
            min_significance FLOAT DEFAULT 0.0,
            limit_param INT DEFAULT 50
        )
        RETURNS TABLE(
            id UUID,
            capsule_id VARCHAR(255),
            type capsule_type,
            platform platform_type,
            user_message TEXT,
            ai_response TEXT,
            significance_score FLOAT,
            created_at TIMESTAMP WITH TIME ZONE,
            rank FLOAT
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT
                c.id,
                c.capsule_id,
                c.type,
                c.platform,
                c.user_message,
                c.ai_response,
                c.significance_score,
                c.created_at,
                ts_rank(
                    to_tsvector('english', COALESCE(c.user_message, '') || ' ' || COALESCE(c.ai_response, '')),
                    plainto_tsquery('english', search_query)
                ) as rank
            FROM capsules c
            WHERE
                c.status = 'active'
                AND (platform_filter IS NULL OR c.platform = platform_filter)
                AND (user_id_param IS NULL OR c.user_id = user_id_param)
                AND c.significance_score >= min_significance
                AND (
                    to_tsvector('english', COALESCE(c.user_message, '') || ' ' || COALESCE(c.ai_response, ''))
                    @@ plainto_tsquery('english', search_query)
                )
            ORDER BY rank DESC, c.created_at DESC
            LIMIT limit_param;
        END;
        $$ LANGUAGE plpgsql;
        """

        async with self.pool.acquire() as conn:
            await conn.execute(functions_sql)
            logger.info("[OK] PostgreSQL functions created successfully")

    async def migrate_from_sqlite(self, sqlite_file: str = "capsule_chain.jsonl"):
        """Migrate data from SQLite/JSONL to PostgreSQL."""

        logger.info(f" Starting migration from {sqlite_file}")

        # Read existing data
        capsules_data = []

        # Try to read from JSONL file
        if os.path.exists(sqlite_file):
            with open(sqlite_file) as f:
                for line in f:
                    try:
                        capsule = json.loads(line.strip())
                        capsules_data.append(capsule)
                    except json.JSONDecodeError:
                        continue

        logger.info(f" Found {len(capsules_data)} capsules to migrate")

        if not capsules_data:
            logger.info("No data to migrate")
            return

        # Create default user if not exists
        async with self.pool.acquire() as conn:
            # Check if default user exists
            user_exists = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE username = 'system'"
            )

            if user_exists == 0:
                await conn.execute(
                    """
                    INSERT INTO users (username, email, password_hash, roles)
                    VALUES ('system', 'system@uatp.com', 'system', ARRAY['system'])
                """
                )
                logger.info(" Created system user")

            # Get system user ID
            system_user_id = await conn.fetchval(
                "SELECT id FROM users WHERE username = 'system'"
            )

            # Migrate capsules
            migrated_count = 0

            for capsule in capsules_data:
                try:
                    # Map capsule data to PostgreSQL format
                    await conn.execute(
                        """
                        INSERT INTO capsules (
                            capsule_id, type, platform, user_id, session_id, model,
                            user_message, ai_response, content, reasoning_trace,
                            metadata, significance_score, confidence_score,
                            created_at
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                        ) ON CONFLICT (capsule_id) DO NOTHING
                    """,
                        capsule.get("capsule_id", f"migrated_{migrated_count}"),
                        capsule.get("type", "interaction_capsule"),
                        capsule.get("platform", "other"),
                        system_user_id,
                        capsule.get("session_id"),
                        capsule.get("model"),
                        capsule.get("user_message"),
                        capsule.get("ai_response"),
                        capsule.get("content"),
                        json.dumps(capsule.get("reasoning_trace", {})),
                        json.dumps(capsule.get("metadata", {})),
                        capsule.get("significance_score", 0.0),
                        capsule.get("confidence_score", 0.0),
                        datetime.fromisoformat(
                            capsule.get("timestamp", datetime.now().isoformat())
                        ),
                    )

                    migrated_count += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to migrate capsule {capsule.get('capsule_id', 'unknown')}: {e}"
                    )
                    continue

        logger.info(f"[OK] Migration completed: {migrated_count} capsules migrated")

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""

        async with self.pool.acquire() as conn:
            # Get table sizes
            table_sizes = await conn.fetch(
                """
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY size_bytes DESC
            """
            )

            # Get record counts
            # SECURITY: Table names are hardcoded constants - validated against allowlist
            ALLOWED_TABLES = frozenset(
                ["users", "capsules", "sessions", "chain_seals", "audit_log"]
            )
            record_counts = {}
            for table in ALLOWED_TABLES:
                # Table name is validated constant - safe for interpolation
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                record_counts[table] = count

            # Get database size
            db_size = await conn.fetchval(
                """
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """
            )

            return {
                "database_size": db_size,
                "table_sizes": [dict(row) for row in table_sizes],
                "record_counts": record_counts,
                "connection_pool": {
                    "size": self.pool.get_size(),
                    "max_size": self.pool.get_max_size(),
                    "min_size": self.pool.get_min_size(),
                },
            }

    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""

        try:
            async with self.pool.acquire() as conn:
                # Test basic connectivity
                result = await conn.fetchval("SELECT 1")

                # Check database version
                version = await conn.fetchval("SELECT version()")

                # Check if schema exists
                tables = await conn.fetch(
                    """
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                """
                )

                return {
                    "status": "healthy",
                    "connectivity": result == 1,
                    "version": version,
                    "tables": [row["tablename"] for row in tables],
                    "pool_status": {
                        "size": self.pool.get_size(),
                        "max_size": self.pool.get_max_size(),
                        "min_size": self.pool.get_min_size(),
                    },
                }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "connectivity": False}


# Global manager instance
_pg_manager = None


def get_postgresql_manager() -> PostgreSQLManager:
    """Get the global PostgreSQL manager instance."""
    global _pg_manager
    if _pg_manager is None:
        _pg_manager = PostgreSQLManager()
    return _pg_manager


async def main():
    """Test PostgreSQL setup and migration."""

    print(" Testing PostgreSQL Setup")
    print("=" * 40)

    # Initialize manager
    pg_manager = get_postgresql_manager()

    try:
        # Create connection pool
        print("\n Creating connection pool...")
        await pg_manager.create_connection_pool()

        # Create schema
        print("\n Creating database schema...")
        await pg_manager.create_schema()

        # Create indexes
        print("\n Creating indexes...")
        await pg_manager.create_indexes()

        # Create functions
        print("\n Creating functions...")
        await pg_manager.create_functions()

        # Test migration
        print("\n Testing migration...")
        await pg_manager.migrate_from_sqlite()

        # Get database stats
        print("\n Database statistics:")
        stats = await pg_manager.get_database_stats()
        print(f"   Database size: {stats['database_size']}")
        print(f"   Record counts: {stats['record_counts']}")

        # Health check
        print("\n Health check:")
        health = await pg_manager.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Tables: {len(health.get('tables', []))}")

    except Exception as e:
        print(f"[ERROR] PostgreSQL setup failed: {e}")
        print("Make sure PostgreSQL is running and accessible")

    finally:
        # Clean up
        await pg_manager.close_connection_pool()

    print("\n[OK] PostgreSQL setup test completed!")


if __name__ == "__main__":
    asyncio.run(main())
