#!/usr/bin/env python3
"""
Add demo capsules to PostgreSQL database for demo mode testing.
This populates the production database with demo data identified by 'demo-' prefix.
"""

import asyncio
import json
from datetime import datetime, timezone

import asyncpg


async def add_demo_capsules():
    """Add demo capsules to PostgreSQL database"""

    # Connect to PostgreSQL (using same credentials as the API)
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        database="uatp_capsule_engine",
        user="uatp_user",
        password="uatp_password",
    )

    try:
        # Demo capsule 1: Attribution capsule
        now = datetime.now(timezone.utc)
        demo_attribution = {
            "capsule_id": "demo-attribution-001",
            "capsule_type": "attribution",
            "version": "7.0.0",
            "timestamp": now,
            "status": "active",
            "verification": {
                "signature": "demo_signature_attribution",
                "chain_hash": "demo_chain_hash_attribution",
                "verified": True,
            },
            "payload": {
                "attribution_type": "conversation",
                "sources": [
                    {"source_id": "demo-user-001", "contribution_score": 0.6},
                    {"source_id": "demo-ai-001", "contribution_score": 0.4},
                ],
                "value_distribution": {
                    "direct": {"demo-user-001": 0.60, "demo-ai-001": 0.40},
                    "commons": 0.15,
                    "uba": 0.10,
                },
                "content_summary": "Demo conversation about machine learning fundamentals",
                "significance_score": 0.75,
            },
        }

        # Demo capsule 2: Economic capsule
        demo_economic = {
            "capsule_id": "demo-economic-001",
            "capsule_type": "economic",
            "version": "7.0.0",
            "timestamp": now,
            "status": "active",
            "verification": {
                "signature": "demo_signature_economic",
                "chain_hash": "demo_chain_hash_economic",
                "verified": True,
            },
            "payload": {
                "transaction_type": "attribution_payout",
                "amount": "10.50",
                "currency": "USD",
                "from_agent": "demo-platform",
                "to_agent": "demo-user-001",
                "attribution_reference": "demo-attribution-001",
                "economic_data": {
                    "payment_method": "demo_wallet",
                    "transaction_hash": "demo_tx_hash_001",
                    "status": "completed",
                },
            },
        }

        # Demo capsule 3: Reasoning capsule
        demo_reasoning = {
            "capsule_id": "demo-reasoning-001",
            "capsule_type": "reasoning",
            "version": "7.0.0",
            "timestamp": now,
            "status": "active",
            "verification": {
                "signature": "demo_signature_reasoning",
                "chain_hash": "demo_chain_hash_reasoning",
                "verified": True,
            },
            "payload": {
                "reasoning_type": "deductive",
                "steps": [
                    {
                        "step_number": 1,
                        "step_type": "premise",
                        "content": "All demo capsules have 'demo-' prefix",
                        "confidence": 1.0,
                    },
                    {
                        "step_number": 2,
                        "step_type": "premise",
                        "content": "This capsule has 'demo-' prefix",
                        "confidence": 1.0,
                    },
                    {
                        "step_number": 3,
                        "step_type": "conclusion",
                        "content": "Therefore, this is a demo capsule",
                        "confidence": 1.0,
                    },
                ],
                "conclusion": "Proper demo/live data separation",
                "confidence_score": 1.0,
                "metadata": {
                    "reasoning_engine": "demo_logic_v1",
                    "verification_status": "demo_verified",
                },
            },
        }

        # Demo capsule 4: Governance capsule
        demo_governance = {
            "capsule_id": "demo-governance-001",
            "capsule_type": "governance",
            "version": "7.0.0",
            "timestamp": now,
            "status": "active",
            "verification": {
                "signature": "demo_signature_governance",
                "chain_hash": "demo_chain_hash_governance",
                "verified": True,
            },
            "payload": {
                "governance_type": "policy_proposal",
                "proposal_id": "demo-proposal-001",
                "title": "Demo Mode Data Separation Policy",
                "description": "Proposal to maintain strict separation between demo and live data",
                "voting_status": "approved",
                "votes": {"for": 85, "against": 10, "abstain": 5},
                "implementation_status": "active",
            },
        }

        # Demo capsule 5: Conversation capsule
        demo_conversation = {
            "capsule_id": "demo-conversation-001",
            "capsule_type": "conversation",
            "version": "7.0.0",
            "timestamp": now,
            "status": "active",
            "verification": {
                "signature": "demo_signature_conversation",
                "chain_hash": "demo_chain_hash_conversation",
                "verified": True,
            },
            "payload": {
                "conversation_id": "demo-conv-001",
                "participants": ["demo-user-001", "demo-ai-assistant"],
                "messages": [
                    {
                        "role": "user",
                        "content": "What is the difference between demo and live data?",
                        "timestamp": now.isoformat(),
                    },
                    {
                        "role": "assistant",
                        "content": "Demo data uses 'demo-' prefix and is for testing, while live data is from actual auto-captured conversations.",
                        "timestamp": now.isoformat(),
                    },
                ],
                "significance_score": 0.65,
                "context_metadata": {
                    "topic": "demo_mode_explanation",
                    "auto_captured": False,
                    "demo_mode": True,
                },
            },
        }

        capsules = [
            demo_attribution,
            demo_economic,
            demo_reasoning,
            demo_governance,
            demo_conversation,
        ]

        # Insert capsules into database
        for capsule in capsules:
            await conn.execute(
                """
                INSERT INTO capsules (capsule_id, capsule_type, version, timestamp, status, verification, payload)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (capsule_id) DO UPDATE SET
                    capsule_type = EXCLUDED.capsule_type,
                    version = EXCLUDED.version,
                    timestamp = EXCLUDED.timestamp,
                    status = EXCLUDED.status,
                    verification = EXCLUDED.verification,
                    payload = EXCLUDED.payload
                """,
                capsule["capsule_id"],
                capsule["capsule_type"],
                capsule["version"],
                capsule["timestamp"],
                capsule["status"],
                json.dumps(capsule["verification"]),
                json.dumps(capsule["payload"]),
            )
            print(f"✅ Added demo capsule: {capsule['capsule_id']}")

        # Verify counts
        total_count = await conn.fetchval("SELECT COUNT(*) FROM capsules")
        demo_count = await conn.fetchval(
            "SELECT COUNT(*) FROM capsules WHERE capsule_id LIKE 'demo-%'"
        )
        real_count = await conn.fetchval(
            "SELECT COUNT(*) FROM capsules WHERE capsule_id NOT LIKE 'demo-%'"
        )

        print("\n📊 Database Summary:")
        print(f"   Total capsules: {total_count}")
        print(f"   Demo capsules: {demo_count}")
        print(f"   Real capsules: {real_count}")

        print("\n✅ Demo capsules added successfully!")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(add_demo_capsules())
