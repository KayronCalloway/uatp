"""FastAPI dependency injection for API components."""

import logging
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# Create a SYNC database connection for FastAPI dependencies
# The main db object uses async, but auth routes use sync patterns
_SYNC_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./uatp_dev.db")
# Convert async URL to sync if needed
if "+aiosqlite" in _SYNC_DATABASE_URL:
    _SYNC_DATABASE_URL = _SYNC_DATABASE_URL.replace("+aiosqlite", "")
elif "+asyncpg" in _SYNC_DATABASE_URL:
    _SYNC_DATABASE_URL = _SYNC_DATABASE_URL.replace("+asyncpg", "+psycopg2")

_sync_engine = create_engine(
    _SYNC_DATABASE_URL,
    pool_pre_ping=True,
    # SQLite needs check_same_thread=False for FastAPI
    connect_args={"check_same_thread": False} if "sqlite" in _SYNC_DATABASE_URL else {},
)
_SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_sync_engine)


def get_db() -> Generator[Session, None, None]:
    """
    Get a SYNC database session for FastAPI dependency injection.

    Usage:
        @router.get("/items")
        async def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    session = _SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()
