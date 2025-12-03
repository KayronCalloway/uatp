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
        from src.models.user_management import (
            UserSessionModel,
            IdentityVerificationModel,
        )  # noqa
        from src.insurance.models import (
            InsurancePolicy,
            InsuranceClaim,
            AILiabilityEventLog,
        )  # noqa

        async with self.engine.begin() as conn:
            await conn.run_sync(self.Base.metadata.create_all)

    def get_session(self) -> AsyncSession:
        if not self.session_factory:
            raise RuntimeError(
                "Database has not been initialized. Call init_app first."
            )
        return self.session_factory()


db = SQLAlchemyDB()
