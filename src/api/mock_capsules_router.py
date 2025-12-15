"""
Mock Capsules Router - FastAPI
Provides demo capsule data until full migration is complete
"""

import random
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query

from src.utils.timezone_utils import utc_now

router = APIRouter(prefix="/capsules", tags=["Capsules"])


# Generate mock capsule data
def generate_mock_capsules(count: int = 100):
    capsules = []
    capsule_types = ["chat", "joint", "reasoning", "refusal", "consent", "perspective"]
    agents = [f"agent-{i:03d}" for i in range(1, 21)]

    content_samples = {
        "chat": "Hello, how can I help you today?",
        "joint": "I can assist with various tasks including code review and analysis.",
        "reasoning": "Let me break down this problem step by step...",
        "refusal": "I cannot provide that information as it may be harmful.",
        "consent": "User has provided explicit consent for data processing.",
        "perspective": "From my perspective, this approach would work best because...",
    }

    base_time = utc_now()

    for i in range(count):
        capsule_type = random.choice(capsule_types)
        timestamp = base_time - timedelta(hours=random.randint(0, 720))

        capsules.append(
            {
                "id": f"capsule-{i+1:04d}",
                "capsule_id": f"capsule-{i+1:04d}",
                "type": capsule_type,
                "timestamp": timestamp.isoformat() + "Z",
                "status": "SEALED",
                "verification": {
                    "hash": f"sha256:{random.randint(10**63, 10**64-1):064x}",
                    "verified": True,
                    "signer": random.choice(agents),
                    "signature": f"ed25519:{random.randint(10**127, 10**128-1):0128x}",
                    "merkle_root": f"sha256:{random.randint(10**63, 10**64-1):064x}",
                },
                "payload": {
                    "type": capsule_type,
                    "content": content_samples[capsule_type],
                    "analysis_metadata": {
                        "platform": random.choice(
                            ["claude-code", "openai-api", "anthropic-api"]
                        ),
                        "user_id": f"user-{random.randint(1, 50):03d}",
                        "significance_score": round(random.uniform(0.5, 1.0), 3),
                        "auto_filtered": random.choice([True, False]),
                    },
                },
                "lineage": {
                    "parent_id": f"capsule-{random.randint(1, max(1, i)):04d}"
                    if i > 0 and random.random() > 0.3
                    else None,
                    "depth": random.randint(0, 5),
                },
                "agent_id": random.choice(agents),
                "trust_score": round(random.uniform(0.75, 0.99), 3),
            }
        )

    return capsules


# Generate once at module load
MOCK_CAPSULES = generate_mock_capsules(100)


@router.get("/stats")
async def get_capsule_stats():
    """Get capsule statistics"""
    capsule_types = {}
    agents = {}
    platforms = {}
    total_significance = 0

    for capsule in MOCK_CAPSULES:
        # Count by type
        capsule_type = capsule["type"]
        capsule_types[capsule_type] = capsule_types.get(capsule_type, 0) + 1

        # Count by agent
        agent_id = capsule["agent_id"]
        agents[agent_id] = agents.get(agent_id, 0) + 1

        # Count by platform
        platform = capsule["payload"]["analysis_metadata"]["platform"]
        platforms[platform] = platforms.get(platform, 0) + 1

        # Sum significance
        total_significance += capsule["payload"]["analysis_metadata"][
            "significance_score"
        ]

    return {
        "total_capsules": len(MOCK_CAPSULES),
        "by_type": capsule_types,
        "by_agent": agents,
        "by_platform": platforms,
        "recent_activity": {
            "last_24h": len(
                [
                    c
                    for c in MOCK_CAPSULES
                    if (
                        utc_now()
                        - datetime.fromisoformat(c["timestamp"].replace("Z", ""))
                    ).days
                    == 0
                ]
            ),
            "last_week": len(
                [
                    c
                    for c in MOCK_CAPSULES
                    if (
                        utc_now()
                        - datetime.fromisoformat(c["timestamp"].replace("Z", ""))
                    ).days
                    < 7
                ]
            ),
            "last_month": len(MOCK_CAPSULES),
        },
        "average_trust_score": round(
            sum(c["trust_score"] for c in MOCK_CAPSULES) / len(MOCK_CAPSULES), 3
        ),
        "average_significance": round(total_significance / len(MOCK_CAPSULES), 3),
    }


@router.get("")
async def list_capsules(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    type: Optional[str] = None,
    agent_id: Optional[str] = None,
):
    """List capsules with pagination and filtering"""
    filtered_capsules = MOCK_CAPSULES

    # Apply filters
    if type:
        filtered_capsules = [c for c in filtered_capsules if c["type"] == type]

    if agent_id:
        filtered_capsules = [c for c in filtered_capsules if c["agent_id"] == agent_id]

    # Pagination
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "capsules": filtered_capsules[start:end],
        "total": len(filtered_capsules),
        "page": page,
        "per_page": per_page,
        "total_pages": (len(filtered_capsules) + per_page - 1) // per_page,
    }


@router.get("/{capsule_id}")
async def get_capsule(capsule_id: str):
    """Get a specific capsule by ID"""
    capsule = next((c for c in MOCK_CAPSULES if c["id"] == capsule_id), None)

    if not capsule:
        return {"error": "Capsule not found"}, 404

    return {"capsule": capsule, "verification": capsule["verification"]}
