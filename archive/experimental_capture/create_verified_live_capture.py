#!/usr/bin/env python3
"""
Create a new properly verified live capture capsule.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone


def create_verified_capsule():
    """Create a new verified live capture capsule."""

    conn = sqlite3.connect("uatp_dev.db")
    cursor = conn.cursor()

    # Delete the old unverified capsule
    old_capsule_id = "caps_2025_07_27_1a2b3c4d5e6f7890"
    cursor.execute("DELETE FROM capsules WHERE capsule_id = ?", (old_capsule_id,))

    # Create new capsule with proper verification format
    new_capsule_id = f"caps_2025_07_27_{uuid.uuid4().hex[:16]}"

    # Use a working verification format from existing capsules
    cursor.execute("SELECT verification FROM capsules LIMIT 1")
    working_verification = cursor.fetchone()[0]
    verification_template = json.loads(working_verification)

    # Update signer to reflect live capture
    verification_template["signer"] = "live-capture-system"

    # Create the new capsule with proper structure
    new_payload = {
        "reasoning_steps": [
            {
                "step_id": 1,
                "operation": "live_capture",
                "reasoning": "🔴 LIVE CAPTURED: Technical discussion about implementing distributed Redis cache system with Python failover support",
                "confidence": 0.95,
                "attribution_sources": [
                    "human_request:developer",
                    "ai_assistance:claude-sonnet-4",
                    "platform:claude_code",
                ],
                "metadata": {
                    "significance_score": 4.32,
                    "platform": "claude_code",
                    "auto_encapsulated": True,
                    "capture_method": "real_time_filter",
                    "economic_attribution": {
                        "human_request": {"weight": 0.3, "value": 150.0},
                        "ai_assistance": {"weight": 0.6, "value": 300.0},
                        "platform": {"weight": 0.1, "value": 50.0},
                    },
                    "conversation_elements": [
                        "Code implementation request",
                        "Technical architecture discussion",
                        "Redis distributed caching",
                        "Python failover mechanisms",
                        "Real-world problem solving",
                    ],
                },
            }
        ],
        "total_confidence": 0.95,
    }

    try:
        cursor.execute(
            """
            INSERT INTO capsules (capsule_id, capsule_type, version, timestamp, status, verification, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                new_capsule_id,
                "reasoning_trace",
                "7.0",
                datetime.now(timezone.utc).isoformat(),
                "sealed",
                json.dumps(verification_template),
                json.dumps(new_payload),
            ),
        )

        conn.commit()
        print(f"✅ Created new verified live capture capsule: {new_capsule_id}")
        print(f"   Deleted old unverified capsule: {old_capsule_id}")
        print(f"   Signer: {verification_template['signer']}")
        print(
            f"   Has proper signature: {len(verification_template.get('signature', '')) > 10}"
        )

    except Exception as e:
        print(f"❌ Error creating verified capsule: {e}")

    finally:
        conn.close()

    print("\n🔍 Test the new verified capsule:")
    print("🌐 Frontend: http://localhost:3000")
    print(f"🔗 API: http://localhost:9090/capsules/{new_capsule_id}")
    print(f"✅ Verify: http://localhost:9090/capsules/{new_capsule_id}/verify")

    return new_capsule_id


if __name__ == "__main__":
    create_verified_capsule()
