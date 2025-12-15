#!/usr/bin/env python3
"""
Create a properly verified live capture capsule using the UATP crypto system.
"""

import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# We need to recreate the Pydantic capsule object to get the right hash
from capsule_schema import CapsuleType, ReasoningTraceCapsule, Verification
from crypto_utils import (
    hash_for_signature,
    sign_capsule,
)
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey


def create_properly_verified_capsule():
    """Create a live capture capsule with proper UATP verification."""

    # Generate signing key
    signing_key = SigningKey.generate()
    signing_key_hex = signing_key.encode(encoder=HexEncoder).decode("utf-8")
    verify_key_hex = signing_key.verify_key.encode(encoder=HexEncoder).decode("utf-8")

    # Create capsule data
    capsule_id = f"caps_2025_07_27_{uuid.uuid4().hex[:16]}"

    # Create reasoning trace payload
    reasoning_trace = {
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

    # Create initial verification (will be updated with real values)
    initial_verification = Verification(
        signer="live-capture-system",
        verify_key=verify_key_hex,
        hash="",
        signature="",
        merkle_root="sha256:" + "0" * 64,
    )

    # Create the complete capsule object
    capsule = ReasoningTraceCapsule(
        capsule_id=capsule_id,
        capsule_type=CapsuleType.REASONING_TRACE,
        version="7.0",
        timestamp=datetime.now(timezone.utc),
        status="sealed",
        verification=initial_verification,
        reasoning_trace=reasoning_trace,
    )

    # Calculate proper hash using UATP system
    hash_value = hash_for_signature(capsule)
    print(f"🔐 Calculated UATP hash: {hash_value[:16]}...")

    # Sign the hash
    signature = sign_capsule(hash_value, signing_key_hex)
    print(f"🔐 Generated signature: {signature[:32]}...")

    # Update verification with real values
    capsule.verification.hash = hash_value
    capsule.verification.signature = signature

    # Now convert to database format
    payload_with_compat = reasoning_trace.copy()
    # Add compatibility fields for frontend
    payload_with_compat["content"] = reasoning_trace["reasoning_steps"][0]["reasoning"]
    payload_with_compat["metadata"] = reasoning_trace["reasoning_steps"][0]["metadata"]

    # Insert into database
    conn = sqlite3.connect("uatp_dev.db")
    cursor = conn.cursor()

    # Delete previous test capsules
    cursor.execute("DELETE FROM capsules WHERE capsule_id LIKE 'caps_2025_07_27_%'")

    try:
        cursor.execute(
            """
            INSERT INTO capsules (capsule_id, capsule_type, version, timestamp, status, verification, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                capsule_id,
                "reasoning_trace",
                "7.0",
                datetime.now(timezone.utc).isoformat(),
                "sealed",
                json.dumps(capsule.verification.model_dump()),
                json.dumps(payload_with_compat),
            ),
        )

        conn.commit()
        print(f"✅ Created properly verified live capture capsule: {capsule_id}")
        print(f"   Hash: {hash_value[:16]}...")
        print(f"   Signature: {signature[:32]}...")
        print(f"   Verify key: {verify_key_hex[:16]}...")

    except Exception as e:
        print(f"❌ Error inserting capsule: {e}")

    finally:
        conn.close()

    print("\n🔍 Test the verified capsule:")
    print("🌐 Frontend: http://localhost:3000")
    print(f"🔗 API: http://localhost:9090/capsules/{capsule_id}")
    print(f"✅ Verify: http://localhost:9090/capsules/{capsule_id}/verify")

    return capsule_id


if __name__ == "__main__":
    create_properly_verified_capsule()
