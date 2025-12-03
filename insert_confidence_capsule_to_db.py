#!/usr/bin/env python3
"""Insert the confidence demo capsule into the database."""

import asyncio
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.models.capsule import CapsuleModel
from src.core.config import DATABASE_URL


async def insert_capsule():
    """Insert the confidence demo capsule into the database."""
    # Read the capsule from JSON file
    with open("confidence_demo_capsule.json", "r") as f:
        capsule_data = json.load(f)

    print(f"📦 Loading capsule: {capsule_data['capsule_id']}")
    print(f"   Type: {capsule_data['capsule_type']}")
    print()

    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)

    # Create async session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Check if capsule already exists
            from sqlalchemy import select

            result = await session.execute(
                select(CapsuleModel).where(
                    CapsuleModel.capsule_id == capsule_data["capsule_id"]
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(
                    f'⚠️  Capsule {capsule_data["capsule_id"]} already exists, updating...'
                )
                # Update existing
                existing.capsule_type = capsule_data["capsule_type"]
                existing.payload = capsule_data.get("reasoning_trace", {})
                existing.timestamp = datetime.fromisoformat(
                    capsule_data["timestamp"].replace("Z", "+00:00")
                )
                existing.status = capsule_data.get("status", "active")
                existing.verification = capsule_data.get("verification", {})
                existing.version = capsule_data["version"]
            else:
                print(f'✨ Inserting new capsule {capsule_data["capsule_id"]}...')
                # Create new capsule model
                capsule_model = CapsuleModel(
                    capsule_id=capsule_data["capsule_id"],
                    capsule_type=capsule_data["capsule_type"],
                    payload=capsule_data.get("reasoning_trace", {}),
                    timestamp=datetime.fromisoformat(
                        capsule_data["timestamp"].replace("Z", "+00:00")
                    ),
                    status=capsule_data.get("status", "active"),
                    verification=capsule_data.get("verification", {}),
                    version=capsule_data["version"],
                )
                session.add(capsule_model)

            await session.commit()

            print("✅ Capsule inserted/updated successfully!")
            print(f'📦 Capsule ID: {capsule_data["capsule_id"]}')
            print(f'📊 Type: {capsule_data["capsule_type"]}')

            # Verify it has reasoning_trace
            if "reasoning_trace" in capsule_data:
                steps = capsule_data["reasoning_trace"].get("reasoning_steps", [])
                print(f"✅ Reasoning steps: {len(steps)}")
                confidence = capsule_data["reasoning_trace"].get("total_confidence", 0)
                print(f"📈 Overall confidence: {confidence * 100:.1f}%")

                # Show per-step confidence
                print()
                print("🎯 Per-Step Confidence:")
                for step in steps:
                    conf = step.get("confidence", 0)
                    emoji = (
                        "🟢"
                        if conf >= 0.9
                        else "🔵"
                        if conf >= 0.7
                        else "🟡"
                        if conf >= 0.5
                        else "🔴"
                    )
                    print(
                        f'   {emoji} Step {step.get("step_id")}: {conf * 100:.1f}% - {step.get("operation")}'
                    )

                methodology = capsule_data["reasoning_trace"].get(
                    "confidence_methodology", {}
                )
                if methodology:
                    print()
                    print(f'📊 Methodology: {methodology.get("method")}')
                    print(f'🔗 Critical path: {methodology.get("critical_path_steps")}')

            print()
            print(
                f'🌐 View in frontend: http://localhost:3000/capsules/{capsule_data["capsule_id"]}'
            )
            print(
                f'🔗 View via API: http://localhost:8000/api/capsules/{capsule_data["capsule_id"]}'
            )

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()
            await session.rollback()
            raise
        finally:
            await session.close()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(insert_capsule())
