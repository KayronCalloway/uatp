#!/usr/bin/env python3
"""
Import rich capsules using the ORM so the API can see them.
"""

import asyncio
from datetime import datetime

from src.core.database import db
from src.models.capsule import CapsuleModel
from src.utils.rich_capsule_creator import (
    RichReasoningStep,
    create_rich_reasoning_capsule,
)


async def import_via_orm():
    """Import capsules using the ORM."""

    class MockApp:
        pass

    app = MockApp()
    db.init_app(app)

    print("🚀 Importing rich capsules via ORM...\n")

    # Create capsules
    reasoning_demo_1 = create_rich_reasoning_capsule(
        capsule_id="caps_2025_12_05_orm_rich_001",
        prompt="Should we use asyncpg or SQLAlchemy ORM for the database layer?",
        reasoning_steps=[
            RichReasoningStep(
                step=1,
                reasoning="Analyzed performance requirements: millions of capsules need fast queries",
                confidence=0.95,
                operation="analysis",
                confidence_basis="user requirements",
                measurements={
                    "expected_capsule_count": 10000000,
                    "target_query_time_ms": 50,
                },
                alternatives_considered=["SQLAlchemy ORM", "asyncpg raw SQL", "Prisma"],
            ),
            RichReasoningStep(
                step=2,
                reasoning="Benchmarked asyncpg vs SQLAlchemy ORM",
                confidence=0.99,
                operation="measurement",
                confidence_basis="measured",
                measurements={
                    "asyncpg_queries_per_sec": 25000,
                    "sqlalchemy_queries_per_sec": 7500,
                    "performance_ratio": 3.33,
                },
                attribution_sources=["PostgreSQL documentation", "asyncpg benchmarks"],
            ),
            RichReasoningStep(
                step=3,
                reasoning="Evaluated trade-offs: performance vs developer experience",
                confidence=0.87,
                operation="decision",
                uncertainty_sources=[
                    "Team familiarity with raw SQL",
                    "Future schema changes complexity",
                ],
                confidence_basis="expert judgment",
                alternatives_considered=[
                    "Pure ORM for simplicity",
                    "Hybrid approach",
                    "Pure raw SQL for speed",
                ],
                depends_on_steps=[1, 2],
            ),
        ],
        final_answer="Use asyncpg for raw SQL performance with helper layer for developer experience",
        overall_confidence=0.92,
        confidence_methodology={
            "method": "weakest_critical_link",
            "critical_path_steps": [3],
            "explanation": "Confidence limited by uncertainty in step 3",
        },
    )

    # Use ORM to insert
    async with db.get_session() as session:
        async with session.begin():
            # Create ORM object
            capsule_orm = CapsuleModel(
                capsule_id=reasoning_demo_1["capsule_id"],
                capsule_type=reasoning_demo_1["type"],
                version=reasoning_demo_1["version"],
                timestamp=datetime.fromisoformat(
                    reasoning_demo_1["timestamp"].replace("Z", "+00:00")
                ),
                status=reasoning_demo_1["status"],
                verification=reasoning_demo_1["verification"],
                payload=reasoning_demo_1["payload"],
            )

            session.add(capsule_orm)

        await session.commit()
        print(f"✅ Imported {reasoning_demo_1['capsule_id']}")
        print(f"   Steps: {len(reasoning_demo_1['payload']['reasoning_steps'])}")

    # Verify it's there
    async with db.get_session() as session:
        from sqlalchemy import select

        query = select(CapsuleModel).where(
            CapsuleModel.capsule_id == "caps_2025_12_05_orm_rich_001"
        )
        result = await session.execute(query)
        capsule = result.scalar_one_or_none()

        if capsule:
            print("\n✅ Verified: Capsule accessible via ORM")
            print(f"   Payload keys: {list(capsule.payload.keys())}")
            if "reasoning_steps" in capsule.payload:
                print(f"   Reasoning steps: {len(capsule.payload['reasoning_steps'])}")
                step1 = capsule.payload["reasoning_steps"][0]
                print(f"   Step 1 keys: {list(step1.keys())}")
        else:
            print("\n❌ ERROR: Capsule not found via ORM query!")


if __name__ == "__main__":
    asyncio.run(import_via_orm())
