import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import DATABASE_URL


class SQLAlchemyDB:
    def __init__(self, engine=None):
        self.engine = engine
        self.session_factory = None
        self.Base = declarative_base()

        if self.engine:
            self.session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

    def init_app(self, app):
        # Get pool settings from environment variables with defaults
        pool_size = int(os.getenv("UATP_DB_POOL_SIZE", 5))
        max_overflow = int(os.getenv("UATP_DB_MAX_OVERFLOW", 10))
        pool_recycle = int(os.getenv("UATP_DB_POOL_RECYCLE", 3600))

        # Build engine kwargs conditionally – SQLite (aiosqlite) does not support
        # pool_size / max_overflow arguments. Attempting to pass them triggers:
        # "Invalid argument(s) 'pool_size','max_overflow'".
        engine_kwargs = {
            "pool_pre_ping": True,
        }

        if not DATABASE_URL.startswith("sqlite") and "sqlite" not in DATABASE_URL:
            # For real DB backends (e.g., Postgres, MySQL) we keep pool tuning params.
            engine_kwargs.update(
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_recycle=pool_recycle,
            )
        else:
            # Ensure SQLite uses a NullPool to avoid lingering connections in tests.
            from sqlalchemy.pool import NullPool

            engine_kwargs.update(poolclass=NullPool)

        self.engine = create_async_engine(
            DATABASE_URL,
            **engine_kwargs,
        )
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_all(self):
        # Import all models here before calling create_all
        # to ensure they are registered on the metadata.
        from src.models.capsule import CapsuleModel  # noqa
        from src.models.payment import PayoutMethodModel, TransactionModel  # noqa
        from src.models.user import UserModel  # noqa

        async with self.engine.begin() as conn:
            await conn.run_sync(self.Base.metadata.create_all)

    def get_session(self) -> AsyncSession:
        if not self.session_factory:
            raise RuntimeError(
                "Database has not been initialized. Call init_app first."
            )
        return self.session_factory()

    async def fetch(self, query: str, *args):
        """
        Execute a raw SQL query and fetch all results.
        Compatible with asyncpg-style queries for CapsuleEngine.

        Args:
            query: SQL query string (asyncpg format with $1, $2, etc.)
            *args: Query parameters

        Returns:
            List of Row objects (dict-like) with column names as keys
        """
        import logging
        import re

        from sqlalchemy import text

        logger = logging.getLogger(__name__)

        if not self.engine:
            raise RuntimeError("Database engine not initialized")

        #  Handle PostgreSQL array syntax FIRST (e.g., ANY($1::text[]))
        # Convert to SQLAlchemy compatible IN clause
        converted_query = query
        converted_query = re.sub(
            r"=\s*ANY\(\$(\d+)::text\[\]\)", r"IN (:\1)", converted_query
        )

        # Convert all asyncpg-style placeholders ($1, $2, etc.) to SQLAlchemy style (:1, :2, etc.)
        # We use numbered placeholders to avoid name conflicts
        for i in range(
            len(args), 0, -1
        ):  # Process in reverse to avoid replacing $1 in $10
            converted_query = converted_query.replace(f"${i}", f":{i}")

        # Build params dict with numbered keys
        params = {str(i): arg for i, arg in enumerate(args, 1)}

        # For list/array parameters (like the capsule_types list), we need special handling
        # SQLAlchemy's IN clause can handle lists directly
        for key, value in list(params.items()):
            if isinstance(value, (list, tuple)):
                # Convert list to comma-separated placeholders
                placeholders = [f":{key}_{j}" for j in range(len(value))]
                converted_query = converted_query.replace(
                    f":{key}", ", ".join(placeholders)
                )
                # Add individual values to params
                for j, item in enumerate(value):
                    params[f"{key}_{j}"] = item
                # Remove the original list param
                del params[key]

        # Debug logging to trace SQL conversion
        logger.info(f"🔍 DATABASE FETCH - Original query: {query[:200]}...")
        logger.info(f"🔍 DATABASE FETCH - Converted query: {converted_query[:200]}...")
        logger.info(f"🔍 DATABASE FETCH - Params: {params}")

        async with self.engine.connect() as conn:
            result = await conn.execute(text(converted_query), params)
            # Convert to list of dict-like objects similar to asyncpg Records
            rows = []
            for row in result:
                # Convert Row to dict
                row_dict = dict(row._mapping)
                rows.append(row_dict)
            logger.info(f"🔍 DATABASE FETCH - Retrieved {len(rows)} rows")
            return rows


db = SQLAlchemyDB()
