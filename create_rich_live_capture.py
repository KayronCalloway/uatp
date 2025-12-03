#!/usr/bin/env python3
"""
Create a rich live capture example with full attribution details.
"""

import json
import sqlite3
from datetime import datetime, timezone
import uuid


def create_rich_live_capture():
    """Create a comprehensive live capture example."""

    conn = sqlite3.connect("uatp_dev.db")
    cursor = conn.cursor()

    capsule_id = f"caps_2025_07_27_{uuid.uuid4().hex[:16]}"

    # Rich live capture with complete attribution
    capsule_data = {
        "capsule_id": capsule_id,
        "capsule_type": "reasoning_trace",
        "version": "7.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "sealed",
        "verification": {
            "signer": "live-capture-system",
            "verify_key": "04a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2",
            "hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
            "signature": "ed25519:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
            "merkle_root": "sha256:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
        },
        "reasoning_trace": {
            "reasoning_steps": [
                {
                    "step_id": 1,
                    "operation": "technical_request_analysis",
                    "reasoning": "🔴 LIVE: User requested help implementing a distributed cache system using Redis with Python. This is a high-value technical implementation requiring system architecture knowledge.",
                    "confidence": 0.94,
                    "attribution_sources": [
                        "human_expertise:user_kay",
                        "technical_domain:distributed_systems",
                        "platform:claude_code",
                    ],
                    "metadata": {
                        "request_type": "technical_implementation",
                        "complexity_level": "high",
                        "economic_value": 500.0,
                        "attribution_breakdown": {
                            "human_problem_definition": 0.4,
                            "ai_solution_design": 0.6,
                        },
                    },
                },
                {
                    "step_id": 2,
                    "operation": "solution_architecture",
                    "reasoning": "🔴 LIVE: Provided comprehensive Redis implementation with connection pooling, failover mechanisms, and distributed locking. Included production-ready error handling and monitoring.",
                    "confidence": 0.91,
                    "attribution_sources": [
                        "ai_technical_knowledge:claude_sonnet_4",
                        "code_generation:automated",
                        "best_practices:industry_standard",
                    ],
                    "metadata": {
                        "solution_components": [
                            "Redis connection pooling",
                            "Failover mechanisms",
                            "Distributed locking",
                            "Error handling",
                            "Performance monitoring",
                        ],
                        "code_lines_generated": 147,
                        "economic_value": 750.0,
                        "attribution_breakdown": {
                            "ai_architecture_design": 0.7,
                            "established_patterns": 0.3,
                        },
                    },
                },
                {
                    "step_id": 3,
                    "operation": "collaborative_refinement",
                    "reasoning": "🔴 LIVE: User asked follow-up questions about distributed locking mechanisms. Provided detailed explanation with additional implementation examples.",
                    "confidence": 0.88,
                    "attribution_sources": [
                        "human_clarification:user_kay",
                        "ai_explanation:claude_sonnet_4",
                        "iterative_improvement:collaborative",
                    ],
                    "metadata": {
                        "interaction_type": "follow_up",
                        "knowledge_transfer": True,
                        "economic_value": 250.0,
                        "attribution_breakdown": {
                            "human_guided_learning": 0.5,
                            "ai_knowledge_transfer": 0.5,
                        },
                    },
                },
            ],
            "total_confidence": 0.91,
            "live_capture_metadata": {
                "session_id": "claude_code_live_session_12345",
                "capture_timestamp": datetime.now(timezone.utc).isoformat(),
                "significance_score": 4.86,
                "platforms_involved": ["claude_code"],
                "real_world_interaction": True,
                "economic_summary": {
                    "total_value_created": 1500.0,
                    "human_attribution": 450.0,
                    "ai_attribution": 1050.0,
                    "attribution_method": "weighted_contribution",
                },
                "conversation_quality": {
                    "technical_depth": "high",
                    "practical_applicability": "high",
                    "educational_value": "high",
                },
            },
        },
    }

    try:
        cursor.execute(
            """
            INSERT INTO capsules (capsule_id, capsule_type, version, timestamp, status, verification, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                capsule_data["capsule_id"],
                capsule_data["capsule_type"],
                capsule_data["version"],
                capsule_data["timestamp"],
                capsule_data["status"],
                json.dumps(capsule_data["verification"]),
                json.dumps(capsule_data["reasoning_trace"]),
            ),
        )

        conn.commit()
        print(f"✅ Created rich live capture: {capsule_id}")
        print(
            f"   💰 Total Value: ${capsule_data['reasoning_trace']['live_capture_metadata']['economic_summary']['total_value_created']}"
        )
        print(
            f"   🧠 Significance: {capsule_data['reasoning_trace']['live_capture_metadata']['significance_score']}"
        )
        print(f"   🔗 Steps: {len(capsule_data['reasoning_trace']['reasoning_steps'])}")
        print(f"   🌟 Confidence: {capsule_data['reasoning_trace']['total_confidence']}")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        conn.close()

    print(f"\n🎯 View in frontend: http://localhost:3000")
    print(f"🔗 API Access: http://localhost:9090/capsules/{capsule_id}")

    return capsule_id


if __name__ == "__main__":
    create_rich_live_capture()
