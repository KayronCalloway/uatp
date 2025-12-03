import pytest
from core.database import db

# Import the model and the db object directly. This is the key.
# This ensures they are loaded and registered before we do anything.
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
async def test_table_creation_directly(db_engine):
    """
    A self-contained test that uses the setup_database fixture to prove
    that the SQLAlchemy Base, Metadata, and Model can create a table.
    """
    async with db_engine.begin() as conn:
        # We use the imported `db` object's metadata.
        await conn.run_sync(db.Base.metadata.create_all)

    async_session_factory = sessionmaker(
        bind=db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_factory() as session:
        query = text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='capsules'"
        )
        result = await session.execute(query)
        table = result.fetchone()

        assert table is not None, "The 'capsules' table was NOT created."
        assert table[0] == "capsules", f"Table found was not 'capsules': {table[0]}"
