#!/usr/bin/env python3
"""
Create a live capture capsule using the engine's built-in methods to ensure proper hash calculation.
"""

import asyncio
import os
import sys

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Set required environment variables
os.environ["UATP_DATABASE_URL"] = "sqlite:///uatp_dev.db"
os.environ["UATP_AGENT_ID"] = "live-capture-demo"


async def create_verified_live_capture():
    """Create a verified live capture capsule using the engine."""

    try:
        from engine.capsule_engine import CapsuleEngine
        from nacl.encoding import HexEncoder
        from nacl.signing import SigningKey

        # Generate signing key
        signing_key = SigningKey.generate()
        signing_key_hex = signing_key.encode(encoder=HexEncoder).decode("utf-8")

        # Set signing key in environment for engine
        os.environ["UATP_SIGNING_KEY"] = signing_key_hex

        # Create engine
        engine = CapsuleEngine()

        # Create reasoning trace data
        reasoning_trace = {
            "reasoning_steps": [
                {
                    "step_id": 1,
                    "operation": "live_capture",
                    "reasoning": "🔴 LIVE CAPTURED: Technical discussion about verification system debugging and implementation of distributed Redis cache system with Python failover support",
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
                            "Verification system debugging",
                            "Hash calculation methodology",
                            "Cryptographic signature validation",
                            "Redis distributed caching implementation",
                            "Python failover mechanisms",
                            "Real-world problem solving",
                        ],
                    },
                }
            ],
            "total_confidence": 0.95,
        }

        # Create capsule using engine (this will use proper UATP hash calculation)
        capsule = await engine.create_reasoning_trace_capsule_async(
            reasoning_steps=reasoning_trace["reasoning_steps"],
            total_confidence=reasoning_trace["total_confidence"],
        )

        print(f"✅ Created verified capsule using engine: {capsule.capsule_id}")
        print(f"   Hash: {capsule.verification.hash[:16]}...")
        print(f"   Signature: {capsule.verification.signature[:32]}...")
        print(f"   Verify key: {capsule.verification.verify_key[:16]}...")

        # Verify the capsule
        is_valid, reason = await engine.verify_capsule_async(capsule)
        if is_valid:
            print("🎉 Capsule verification PASSED!")
        else:
            print(f"❌ Capsule verification FAILED: {reason}")

        # Now add frontend compatibility fields to the database
        import json
        import sqlite3

        conn = sqlite3.connect("uatp_dev.db")
        cursor = conn.cursor()

        # Get the current payload
        cursor.execute(
            "SELECT payload FROM capsules WHERE capsule_id = ?", (capsule.capsule_id,)
        )
        row = cursor.fetchone()
        if row:
            payload = json.loads(row[0])
            # Add compatibility fields
            payload["content"] = reasoning_trace["reasoning_steps"][0]["reasoning"]
            payload["metadata"] = reasoning_trace["reasoning_steps"][0]["metadata"]

            # Update the database
            cursor.execute(
                "UPDATE capsules SET payload = ? WHERE capsule_id = ?",
                (json.dumps(payload), capsule.capsule_id),
            )
            conn.commit()
            print("✅ Added frontend compatibility fields")

        conn.close()

        print("\n🔍 Test the verified capsule:")
        print("🌐 Frontend: http://localhost:3000")
        print(f"🔗 API: http://localhost:9090/capsules/{capsule.capsule_id}")
        print(f"✅ Verify: http://localhost:9090/capsules/{capsule.capsule_id}/verify")

        return capsule.capsule_id

    except Exception as e:
        print(f"❌ Error creating verified capsule: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(create_verified_live_capture())
