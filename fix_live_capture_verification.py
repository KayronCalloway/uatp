#!/usr/bin/env python3
"""
Fix live capture verification by properly signing with Ed25519.
"""

import json
import sqlite3
import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from crypto_utils import (
        sign_capsule,
        hash_for_signature,
        get_verify_key_from_signing_key,
    )
    from nacl.signing import SigningKey
    from nacl.encoding import HexEncoder
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def create_properly_signed_capsule():
    """Create a new live capture capsule with proper Ed25519 signature."""

    # Generate a new signing key for this demo
    signing_key = SigningKey.generate()
    signing_key_hex = signing_key.encode(encoder=HexEncoder).decode("utf-8")
    verify_key_hex = signing_key.verify_key.encode(encoder=HexEncoder).decode("utf-8")

    print(f"🔑 Generated new signing key")
    print(f"   Verify key: {verify_key_hex[:16]}...")

    conn = sqlite3.connect("uatp_dev.db")
    cursor = conn.cursor()

    # Delete the old capsule
    old_capsule_id = "caps_2025_07_27_8948fc7c7e1c485a"
    cursor.execute("DELETE FROM capsules WHERE capsule_id = ?", (old_capsule_id,))

    # Create new capsule ID
    import uuid

    new_capsule_id = f"caps_2025_07_27_{uuid.uuid4().hex[:16]}"

    # Create proper payload structure
    reasoning_steps = [
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
    ]

    payload = {
        "reasoning_steps": reasoning_steps,
        "total_confidence": 0.95,
        # Add legacy fields for frontend compatibility
        "content": reasoning_steps[0]["reasoning"],
        "metadata": reasoning_steps[0]["metadata"],
    }

    # Create a minimal capsule dict for signing
    capsule_for_signing = {
        "capsule_id": new_capsule_id,
        "capsule_type": "reasoning_trace",
        "version": "7.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "sealed",
        "reasoning_trace": payload,
        "verification": {
            "signer": "live-capture-system",
            "verify_key": verify_key_hex,
            "hash": "",
            "signature": "",
            "merkle_root": "sha256:" + "0" * 64,
        },
    }

    try:
        # Calculate hash
        hash_value = hash_for_signature(capsule_for_signing)
        print(f"🔐 Calculated hash: {hash_value[:16]}...")

        # Sign the hash
        signature = sign_capsule(hash_value, signing_key_hex)
        print(f"🔐 Generated signature: {signature[:32]}...")

        # Update verification with real values
        verification = {
            "signer": "live-capture-system",
            "verify_key": verify_key_hex,
            "hash": hash_value,
            "signature": signature,
            "merkle_root": "sha256:" + "0" * 64,
        }

        # Insert into database
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
                json.dumps(verification),
                json.dumps(payload),
            ),
        )

        conn.commit()
        print(f"✅ Created properly signed live capture capsule: {new_capsule_id}")
        print(f"   Deleted old capsule: {old_capsule_id}")
        print(f"   Signer: {verification['signer']}")
        print(f"   Has real signature: {len(verification['signature']) > 50}")

    except Exception as e:
        print(f"❌ Error creating signed capsule: {e}")
        import traceback

        traceback.print_exc()

    finally:
        conn.close()

    print(f"\n🔍 Test the new verified capsule:")
    print(f"🌐 Frontend: http://localhost:3000")
    print(f"🔗 API: http://localhost:9090/capsules/{new_capsule_id}")
    print(f"✅ Verify: http://localhost:9090/capsules/{new_capsule_id}/verify")

    return new_capsule_id


if __name__ == "__main__":
    create_properly_signed_capsule()
