#!/usr/bin/env python3
"""
Create rich demo capsules with full metadata for frontend display testing.
"""

import asyncio
import json
from datetime import datetime

from sqlalchemy import text

from src.core.database import db
from src.utils.rich_capsule_creator import (
    RichReasoningStep,
    create_rich_economic_capsule,
    create_rich_reasoning_capsule,
)


async def create_rich_demos():
    """Create rich demo capsules with all metadata."""

    # Initialize database
    class MockApp:
        pass

    app = MockApp()
    db.init_app(app)
    await db.create_all()

    print("🚀 Creating rich demo capsules...\n")

    # Demo 1: Architecture Decision with Full Metadata
    reasoning_demo_1 = create_rich_reasoning_capsule(
        capsule_id="caps_2025_12_05_rich_demo_001",
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
            RichReasoningStep(
                step=4,
                reasoning="Decided on asyncpg with helper functions for common queries",
                confidence=0.92,
                operation="conclusion",
                confidence_basis="balanced analysis",
                measurements={
                    "expected_performance_gain": 3.3,
                    "estimated_dev_overhead": 0.2,
                },
                attribution_sources=["Kay (User)", "Claude Sonnet 4.5"],
                depends_on_steps=[3],
            ),
        ],
        final_answer="Use asyncpg for raw SQL performance with helper layer for developer experience",
        overall_confidence=0.92,
        model_used="Claude Sonnet 4.5",
        created_by="Claude Code Session",
        session_metadata={
            "session_date": "2025-12-05",
            "session_type": "Architecture Decision",
            "collaborators": ["Kay (User)", "Claude (Sonnet 4.5)"],
            "context": "UATP performance optimization",
        },
        confidence_methodology={
            "method": "weakest_critical_link",
            "critical_path_steps": [3],
            "explanation": "Confidence limited by uncertainty in step 3 (trade-off evaluation)",
        },
    )

    # Demo 2: Security Analysis with Uncertainty Tracking
    reasoning_demo_2 = create_rich_reasoning_capsule(
        capsule_id="caps_2025_12_05_rich_demo_002",
        prompt="Analyze SQL injection vulnerability in user input handling",
        reasoning_steps=[
            RichReasoningStep(
                step=1,
                reasoning="Identified user input concatenated directly into SQL query",
                confidence=1.0,
                operation="observation",
                confidence_basis="code inspection",
                measurements={"vulnerability_count": 3},
            ),
            RichReasoningStep(
                step=2,
                reasoning="Assessed risk level as CRITICAL due to direct database access",
                confidence=0.98,
                operation="risk_assessment",
                confidence_basis="OWASP guidelines",
                uncertainty_sources=["Unknown attack surface exposure"],
                measurements={
                    "cvss_score": 9.8,
                    "exploitability": "high",
                    "impact": "critical",
                },
            ),
            RichReasoningStep(
                step=3,
                reasoning="Recommended parameterized queries and input validation",
                confidence=0.99,
                operation="recommendation",
                confidence_basis="security best practices",
                alternatives_considered=[
                    "ORM with built-in protection",
                    "Input sanitization only",
                    "Parameterized queries + validation",
                ],
                depends_on_steps=[1, 2],
            ),
            RichReasoningStep(
                step=4,
                reasoning="Implemented fix and verified with security tests",
                confidence=0.97,
                operation="implementation",
                confidence_basis="measured",
                uncertainty_sources=["Edge cases in input validation"],
                measurements={"test_coverage": 0.95, "attack_attempts_blocked": 1000},
                attribution_sources=["Claude Code", "OWASP SQL Injection Prevention"],
            ),
        ],
        final_answer="Critical SQL injection vulnerability fixed with parameterized queries and validation",
        overall_confidence=0.97,
        confidence_methodology={
            "method": "weighted_average",
            "step_weights": {1: 1.0, 2: 1.5, 3: 1.2, 4: 1.8},
            "explanation": "Higher weight on implementation verification",
        },
    )

    # Demo 3: Economic Transaction with Work Details
    economic_demo = create_rich_economic_capsule(
        capsule_id="caps_2025_12_05_rich_demo_003",
        transaction_type="development_contribution",
        description="Implemented rich reasoning capture system with confidence tracking",
        parties={
            "contributor": "Claude (Anthropic) - Sonnet 4.5",
            "beneficiary": "UATP Project / Kay",
            "contribution_type": "Architecture & Implementation",
        },
        work_details={
            "components_created": [
                "RichReasoningStep class (src/utils/rich_capsule_creator.py) - 120 LOC",
                "create_rich_reasoning_capsule function - 80 LOC",
                "Demo capsule creation script - 200 LOC",
            ],
            "components_modified": [
                "Frontend capsule-detail.tsx - already supports rich display"
            ],
            "features_added": [
                "Per-step confidence tracking",
                "Uncertainty source capture",
                "Measurement data storage",
                "Alternative consideration tracking",
                "Step dependency tracking",
                "Confidence methodology documentation",
            ],
            "total_loc": 400,
            "files_created": 2,
            "files_modified": 0,
            "test_coverage": "100%",
            "performance_characteristics": {
                "capture_overhead_ms": 0.5,
                "storage_overhead_kb": 2.5,
                "query_time_ms": 15,
            },
        },
        amount_usd=0.0,
        alignment_with_requirements={
            "rich_metadata": "✅ Full confidence tracking implemented",
            "uncertainty_capture": "✅ Uncertainty sources tracked per step",
            "performance_data": "✅ Measurements captured and stored",
            "attribution": "✅ Attribution sources recorded",
            "frontend_compatibility": "✅ Matches frontend expectations exactly",
        },
    )

    # Insert into database
    capsules = [reasoning_demo_1, reasoning_demo_2, economic_demo]

    imported = 0
    async with db.engine.begin() as conn:
        for capsule_data in capsules:
            capsule_id = capsule_data["capsule_id"]
            capsule_type = capsule_data["type"]

            # Parse timestamp
            timestamp = datetime.fromisoformat(
                capsule_data["timestamp"].replace("Z", "+00:00")
            )

            # Insert
            await conn.execute(
                text(
                    """
                    INSERT INTO capsules (
                        capsule_id, capsule_type, version, timestamp,
                        status, verification, payload
                    ) VALUES (
                        :capsule_id, :capsule_type, :version, :timestamp,
                        :status, :verification, :payload
                    )
                """
                ),
                {
                    "capsule_id": capsule_id,
                    "capsule_type": capsule_type,
                    "version": "7.0",
                    "timestamp": timestamp,
                    "status": "sealed",
                    "verification": json.dumps(capsule_data["verification"]),
                    "payload": json.dumps(capsule_data["payload"]),
                },
            )

            print(f"✅ Created {capsule_id} ({capsule_type})")
            if capsule_type == "reasoning_trace":
                step_count = len(capsule_data["payload"]["reasoning_steps"])
                print(f"   → {step_count} reasoning steps with full metadata")
            imported += 1

    print(f"\n📊 Successfully created {imported} rich demo capsules")

    # Verify
    async with db.engine.connect() as conn:
        result = await conn.execute(
            text("SELECT COUNT(*) FROM capsules WHERE capsule_id LIKE '%rich_demo%'")
        )
        count = result.scalar()
        print(f"✅ Database contains {count} rich demo capsules")

        # Show one example
        result = await conn.execute(
            text(
                "SELECT payload FROM capsules WHERE capsule_id = 'caps_2025_12_05_rich_demo_001'"
            )
        )
        row = result.fetchone()
        if row:
            payload = json.loads(row[0])
            print("\n📝 Example: Rich Demo 001")
            print(f"   Steps: {len(payload['reasoning_steps'])}")
            print("   First step has:")
            step = payload["reasoning_steps"][0]
            if "uncertainty_sources" in step:
                print(f"   - Uncertainty sources: {step['uncertainty_sources']}")
            if "measurements" in step:
                print(f"   - Measurements: {step['measurements']}")
            if "alternatives_considered" in step:
                print(f"   - Alternatives: {step['alternatives_considered']}")


if __name__ == "__main__":
    asyncio.run(create_rich_demos())
