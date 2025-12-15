#!/usr/bin/env python3
"""
Add live capture capsules to the database so they appear in the frontend.
"""

import json
import sqlite3
from datetime import datetime, timezone


def add_live_capture_to_db():
    """Add our live capture example to the database."""

    # Connect to the same database the API server uses
    conn = sqlite3.connect("uatp_dev.db")
    cursor = conn.cursor()

    # Create a realistic live capture capsule
    capsule_data = {
        "capsule_id": "caps_2025_07_27_1a2b3c4d5e6f7890",
        "capsule_type": "reasoning_trace",
        "version": "7.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "sealed",
        "verification": {
            "signer": "live-capture-system",
            "verify_key": "",
            "hash": "0000000000000000000000000000000000000000000000000000000000000000",
            "signature": "ed25519:00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
            "merkle_root": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        },
        "payload": {
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
                        "auto_encapsulated": True,
                        "platform": "claude_code",
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
            "live_capture_metadata": {
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "session_id": "live-technical-session",
                "original_significance": 4.32,
                "filter_decision": "encapsulate",
                "real_world_interaction": True,
            },
        },
    }

    # Insert into database
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
                json.dumps(capsule_data["payload"]),
            ),
        )

        conn.commit()
        print(f"✅ Added live capture capsule: {capsule_data['capsule_id']}")
        print(
            f"   Significance: {capsule_data['payload']['live_capture_metadata']['original_significance']}"
        )
        print(
            f"   Real-world: {capsule_data['payload']['live_capture_metadata']['real_world_interaction']}"
        )

    except Exception as e:
        print(f"❌ Error adding capsule: {e}")

    finally:
        conn.close()

    # Verify it was added
    conn = sqlite3.connect("uatp_dev.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM capsules WHERE capsule_id = ?",
        (capsule_data["capsule_id"],),
    )
    count = cursor.fetchone()[0]
    conn.close()

    if count > 0:
        print("🎉 Live capture capsule successfully added to database!")
        print("📍 Visit http://localhost:3000 to see it in the frontend")
        print(f"🔗 API: http://localhost:9090/capsules/{capsule_data['capsule_id']}")
    else:
        print("❌ Capsule was not added successfully")


if __name__ == "__main__":
    add_live_capture_to_db()
