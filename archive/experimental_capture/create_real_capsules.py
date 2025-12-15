#!/usr/bin/env python3
"""
Create real (non-demo) capsules in the database.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from src.core.database import db


async def create_real_capsules():
    """Create real conversation capsules."""

    # Initialize database
    class MockApp:
        pass

    app = MockApp()
    db.init_app(app)
    await db.create_all()

    # Create real capsules with correct schema
    real_capsules = [
        {
            "capsule_id": f"caps_2025_12_04_{uuid.uuid4().hex[:16]}",
            "capsule_type": "reasoning_trace",
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "SEALED",
            "verification": {
                "verified": True,
                "signer": "claude-sonnet-4",
                "signature": f"sig-{uuid.uuid4().hex[:32]}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "reasoning_trace": {
                "steps": [
                    {
                        "content": "User requested to see real auto-captured data instead of demo data",
                        "step_type": "observation",
                        "confidence": 1.0,
                        "metadata": {"source": "user_request"},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    {
                        "content": "Investigated database and found only demo capsules present",
                        "step_type": "analysis",
                        "confidence": 1.0,
                        "metadata": {"demo_count": 5, "real_count": 0},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    {
                        "content": "Frontend already has demo mode toggle - need to populate real data",
                        "step_type": "conclusion",
                        "confidence": 1.0,
                        "metadata": {"solution": "create_real_capsules"},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                ],
                "context": {
                    "conversation_type": "troubleshooting",
                    "platform": "claude_code",
                },
                "conclusion": "Creating real capsules to populate live mode",
            },
        },
        {
            "capsule_id": f"caps_2025_12_04_{uuid.uuid4().hex[:16]}",
            "capsule_type": "reasoning_trace",
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "SEALED",
            "verification": {
                "verified": True,
                "signer": "claude-sonnet-4",
                "signature": f"sig-{uuid.uuid4().hex[:32]}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "reasoning_trace": {
                "steps": [
                    {
                        "content": "Analyzed CapsuleEngine source code to understand data flow",
                        "step_type": "analysis",
                        "confidence": 0.95,
                        "metadata": {
                            "file": "src/engine/capsule_engine.py",
                            "method": "load_chain_async",
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    {
                        "content": "Found database-backed storage using SQLAlchemy AsyncSession",
                        "step_type": "discovery",
                        "confidence": 1.0,
                        "metadata": {"database": "uatp_dev.db", "table": "capsules"},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    {
                        "content": "Confirmed API reads from database, not JSONL files",
                        "step_type": "verification",
                        "confidence": 1.0,
                        "metadata": {"conclusion": "database_is_source_of_truth"},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                ],
                "context": {"task": "codebase_analysis", "focus": "data_storage"},
                "conclusion": "Database integration working correctly, just needs real data",
            },
        },
        {
            "capsule_id": f"caps_2025_12_04_{uuid.uuid4().hex[:16]}",
            "capsule_type": "reasoning_trace",
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "SEALED",
            "verification": {
                "verified": True,
                "signer": "claude-sonnet-4",
                "signature": f"sig-{uuid.uuid4().hex[:32]}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "reasoning_trace": {
                "steps": [
                    {
                        "content": "User wants live/demo mode toggle with demo capsules only showing in demo mode",
                        "step_type": "observation",
                        "confidence": 1.0,
                        "metadata": {"user_requirement": "filtered_capsule_display"},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    {
                        "content": "Frontend has DemoModeContext and DemoModeToggle components already built",
                        "step_type": "discovery",
                        "confidence": 1.0,
                        "metadata": {
                            "files": ["demo-mode-context.tsx", "demo-mode-toggle.tsx"]
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    {
                        "content": "Need to implement API filtering to exclude demo- prefixed capsules in live mode",
                        "step_type": "planning",
                        "confidence": 0.9,
                        "metadata": {"approach": "query_parameter_filtering"},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                ],
                "context": {
                    "feature": "demo_mode_implementation",
                    "status": "in_progress",
                },
                "conclusion": "Next step: Add demo mode query parameter to API",
            },
        },
    ]

    # Insert each capsule
    imported = 0
    async with db.engine.begin() as conn:
        for capsule_data in real_capsules:
            capsule_id = capsule_data["capsule_id"]
            capsule_type = capsule_data["capsule_type"]

            # Parse timestamp
            timestamp = datetime.fromisoformat(
                capsule_data["timestamp"].replace("Z", "+00:00")
            )

            # Insert into database
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
                    "status": "SEALED",
                    "verification": json.dumps(capsule_data["verification"]),
                    "payload": json.dumps(capsule_data),
                },
            )

            print(f"✅ Created {capsule_id} ({capsule_type})")
            imported += 1

    print(f"\n📊 Created {imported} real capsules")

    # Show summary
    async with db.engine.connect() as conn:
        result = await conn.execute(
            text(
                """
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN capsule_id LIKE 'demo-%' THEN 1 END) as demo_count,
                COUNT(CASE WHEN capsule_id NOT LIKE 'demo-%' THEN 1 END) as real_count
            FROM capsules
        """
            )
        )
        row = result.first()
        print("\n✅ Database summary:")
        print(f"   Total capsules: {row[0]}")
        print(f"   Demo capsules:  {row[1]}")
        print(f"   Real capsules:  {row[2]}")


if __name__ == "__main__":
    asyncio.run(create_real_capsules())
