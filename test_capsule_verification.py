#!/usr/bin/env python3
"""
Test the verification of the created capsule via the API.
"""

import asyncio
import httpx
import json
import sqlite3


async def test_verification():
    # Get the latest capsule from database
    conn = sqlite3.connect("uatp_dev.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT capsule_id, json_extract(verification, '$.verify_key'), json_extract(verification, '$.signature')
        FROM capsules 
        WHERE capsule_id LIKE 'caps_2025_07_27_%'
        ORDER BY timestamp DESC 
        LIMIT 1
    """
    )

    result = cursor.fetchone()
    if not result:
        print("❌ No verified capsule found in database")
        return

    capsule_id, verify_key, signature = result
    conn.close()

    print(f"🔍 Testing verification for capsule: {capsule_id}")
    print(f"🔑 Verify Key: {verify_key[:32]}...")
    print(f"✍️ Signature: {signature[:32]}...")

    # Test the verification endpoint
    try:
        async with httpx.AsyncClient() as client:
            # Try the direct endpoint without auth first
            response = await client.get(
                f"http://localhost:9090/capsules/{capsule_id}/verify", timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ API Response: {result}")

                if result.get("verified"):
                    print("🎉 SUCCESS: Capsule shows as VERIFIED via API!")
                else:
                    print(
                        f"❌ FAILED: Capsule not verified: {result.get('reason', 'Unknown')}"
                    )
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("💡 Make sure the API server is running on http://localhost:8000")


if __name__ == "__main__":
    asyncio.run(test_verification())
