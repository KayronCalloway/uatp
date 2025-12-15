#!/usr/bin/env python3
"""
Create demo capsules that will actually validate and display in the frontend.
"""

import asyncio
import json
from datetime import datetime, timezone

from sqlalchemy import text

from src.core.database import db


async def create_demo_capsules():
    """Create working demo capsules."""

    # Initialize database connection
    class MockApp:
        pass

    app = MockApp()
    db.init_app(app)

    # Create tables if they don't exist
    await db.create_all()

    # Clear existing capsules
    async with db.engine.begin() as conn:
        await conn.execute(text("DELETE FROM capsules"))
        print("🧹 Cleared existing capsules")

    # Create demo capsules with correct schema
    demo_capsules = [
        {
            "capsule_id": "demo-reasoning-001",
            "capsule_type": "reasoning_trace",
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "SEALED",
            "verification": {
                "verified": True,
                "signer": "demo-agent-001",
                "signature": "demo-signature-001",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "reasoning_trace": {
                "steps": [
                    {
                        "content": "Analyzing user query about AI attribution",
                        "step_type": "observation",
                        "confidence": 0.95,
                        "metadata": {},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    {
                        "content": "Determining best approach for response",
                        "step_type": "reasoning",
                        "confidence": 0.9,
                        "metadata": {},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                ],
                "context": {"topic": "AI Attribution", "complexity": "medium"},
                "conclusion": "Provided comprehensive explanation of attribution systems",
            },
        },
        {
            "capsule_id": "demo-economic-001",
            "capsule_type": "economic_transaction",
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "SEALED",
            "verification": {
                "verified": True,
                "signer": "demo-agent-002",
                "signature": "demo-signature-002",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "economic_transaction": {
                "transaction_id": "txn-001",
                "amount": 10.50,
                "currency": "USD",
                "from_agent": "user-alice",
                "to_agent": "agent-bob",
                "purpose": "Attribution payment for AI assistance",
                "status": "completed",
            },
        },
        {
            "capsule_id": "demo-consent-001",
            "capsule_type": "consent",
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "SEALED",
            "verification": {
                "verified": True,
                "signer": "demo-agent-003",
                "signature": "demo-signature-003",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "consent": {
                "consent_given": True,
                "scope": ["data_processing", "model_training"],
                "expiration": "2026-01-01T00:00:00Z",
                "revocable": True,
                "grantor": "user-charlie",
            },
        },
        {
            "capsule_id": "demo-governance-001",
            "capsule_type": "governance_vote",
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "SEALED",
            "verification": {
                "verified": True,
                "signer": "demo-agent-004",
                "signature": "demo-signature-004",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "governance_vote": {
                "proposal_id": "prop-001",
                "vote": "approve",
                "voter_id": "voter-diana",
                "weight": 1.0,
                "rationale": "This proposal improves system transparency",
            },
        },
        {
            "capsule_id": "demo-reasoning-002",
            "capsule_type": "reasoning_trace",
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "SEALED",
            "verification": {
                "verified": True,
                "signer": "demo-agent-005",
                "signature": "demo-signature-005",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "reasoning_trace": {
                "steps": [
                    {
                        "content": "User requested code review for Python function",
                        "step_type": "observation",
                        "confidence": 1.0,
                        "metadata": {"language": "python"},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    {
                        "content": "Identified potential security vulnerability in input handling",
                        "step_type": "analysis",
                        "confidence": 0.85,
                        "metadata": {"issue": "SQL injection risk"},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                    {
                        "content": "Recommended parameterized queries",
                        "step_type": "conclusion",
                        "confidence": 0.95,
                        "metadata": {},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                ],
                "context": {"task": "code_review", "risk_level": "high"},
                "conclusion": "Provided security recommendations",
            },
        },
    ]

    # Import each capsule
    imported = 0
    async with db.engine.begin() as conn:
        for capsule_data in demo_capsules:
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

    print(f"\n📊 Created {imported} demo capsules")

    # Verify
    async with db.engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) as count FROM capsules"))
        total_count = result.scalar()
        print(f"✅ Database now contains {total_count} capsules")


if __name__ == "__main__":
    asyncio.run(create_demo_capsules())
