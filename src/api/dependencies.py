"""FastAPI dependency injection for API components."""

import logging
from typing import Generator

from sqlalchemy.orm import Session

from src.core.database import db

logger = logging.getLogger(__name__)


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session for FastAPI dependency injection.

    Usage:
        @router.get("/items")
        async def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()
