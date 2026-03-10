import pytest

# Direct imports to ensure they're loaded in a controlled order
from models.capsule import CapsuleModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
async def test_direct_table_creation(db_connection):
    """
    A self-contained test that uses the db_engine fixture to verify
    that tables are properly created, written to, and retrieved across sessions.
    """
    # The db_connection fixture provides a single, persistent connection.
    # We create a session factory bound to this connection.
    async_session_factory = sessionmaker(
        bind=db_connection, class_=AsyncSession, expire_on_commit=False
    )

    # 1. Insert a record in the first session
    async with async_session_factory() as session1:
        from datetime import datetime

        test_capsule = CapsuleModel(
            capsule_id="caps_2024_01_01_0123456789abcdef",
            agent_id="test-agent-direct",
            capsule_type="Test",
            timestamp=datetime.now(),
            input_data={"test": "data"},
            output={"result": "output"},
            reasoning={"logic": "test reasoning"},
            model_version="1.0-test",
            hash="test-hash-value",
        )
        session1.add(test_capsule)
        await session1.commit()

    # 2. Verify retrieval in a second, independent session on the same connection
    async with async_session_factory() as session2:
        from sqlalchemy import select

        result = await session2.execute(
            select(CapsuleModel).filter(CapsuleModel.capsule_id == "test-id-direct")
        )
        retrieved_capsule = result.scalar_one_or_none()
        assert (
            retrieved_capsule is not None
        ), "Failed to insert and retrieve test capsule"
        assert retrieved_capsule.agent_id == "test-agent-direct"
