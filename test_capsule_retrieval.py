#!/usr/bin/env python3
"""Test capsule retrieval from database."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.models.capsule import CapsuleModel
from src.core.config import DATABASE_URL


async def test_retrieval():
    """Test retrieving the confidence capsule."""
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)

    # Create async session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            select(CapsuleModel).where(
                CapsuleModel.capsule_id == "caps_2025_01_19_841f49678906e7df"
            )
        )
        capsule_model = result.scalars().first()

        if not capsule_model:
            print("❌ Capsule not found in database")
            return

        print(f"✅ Found capsule in database")
        print(f"   ID: {capsule_model.capsule_id}")
        print(f"   Type: {capsule_model.capsule_type}")
        print(f"   Version: {capsule_model.version}")
        print()

        # Check payload
        if capsule_model.payload:
            print(f"📦 Payload keys: {list(capsule_model.payload.keys())}")
            if "reasoning_steps" in capsule_model.payload:
                steps = capsule_model.payload["reasoning_steps"]
                print(f"   Reasoning steps: {len(steps)}")
                if steps:
                    print(
                        f"   First step confidence: {steps[0].get('confidence', 'N/A')}"
                    )
        print()

        # Convert to Pydantic
        print("🔄 Converting to Pydantic...")
        try:
            pydantic_capsule = capsule_model.to_pydantic()
            print(f"✅ Conversion successful")
            print(f"   Pydantic type: {type(pydantic_capsule).__name__}")
            print(f"   Capsule type: {pydantic_capsule.capsule_type}")

            # Check if reasoning_trace is present
            if hasattr(pydantic_capsule, "reasoning_trace"):
                print(f"   Has reasoning_trace: ✅")
                if pydantic_capsule.reasoning_trace:
                    steps = pydantic_capsule.reasoning_trace.reasoning_steps
                    print(f"   Reasoning steps: {len(steps)}")
                    print(
                        f"   Total confidence: {pydantic_capsule.reasoning_trace.total_confidence * 100:.1f}%"
                    )
            else:
                print(f"   Has reasoning_trace: ❌")
                print(
                    f"   Available attributes: {[attr for attr in dir(pydantic_capsule) if not attr.startswith('_')]}"
                )

        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            import traceback

            traceback.print_exc()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_retrieval())
