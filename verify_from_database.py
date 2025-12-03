#!/usr/bin/env python3
"""
Verify the capsule directly from the database using crypto_utils.
"""

import json
import logging
import sqlite3
import sys

# Add src to path for imports
sys.path.insert(0, "/Users/kay/uatp-capsule-engine/src")

# Configure logging first to avoid conflicts
logging.basicConfig(level=logging.ERROR)

from src.crypto_utils import verify_capsule
from src.capsule_schema import ReasoningTraceCapsule


def test_verification_from_database():
    """Test verification by loading from database and using crypto_utils directly."""
    print("🔍 Database Capsule Verification Test")
    print("=" * 50)

    try:
        # Connect to database
        conn = sqlite3.connect("uatp_dev.db")
        cursor = conn.cursor()

        # Get the latest capsule
        cursor.execute(
            """
            SELECT capsule_id, payload, verification
            FROM capsules 
            WHERE capsule_id LIKE 'caps_2025_07_27_%'
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        )

        result = cursor.fetchone()
        conn.close()

        if not result:
            print("❌ No verified capsule found in database")
            return False, "No capsule found"

        capsule_id, payload_json, verification_json = result
        print(f"📋 Testing capsule: {capsule_id}")

        # Parse JSON data
        try:
            payload_data = json.loads(payload_json)
            verification_data = json.loads(verification_json)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return False, "JSON parsing failed"

        # Extract verification details
        verify_key = verification_data.get("verify_key", "")
        signature = verification_data.get("signature", "")
        hash_value = verification_data.get("hash", "")
        signer = verification_data.get("signer", "")

        print(f"🔑 Signer: {signer}")
        print(f"🔐 Hash: {hash_value[:32]}...")
        print(f"✍️ Signature: {signature[:32]}...")
        print(f"🗝️ Verify Key: {verify_key[:32]}...")

        # Reconstruct capsule object
        try:
            capsule = ReasoningTraceCapsule.model_validate(payload_data)
        except Exception as e:
            print(f"❌ Capsule reconstruction error: {e}")
            return False, "Capsule reconstruction failed"

        print(f"✅ Capsule reconstructed: {capsule.capsule_type}")

        # Verify using crypto_utils directly
        print("\n🔍 Performing cryptographic verification...")
        is_valid, reason = verify_capsule(capsule, verify_key, signature)

        print(f"\n{'='*50}")
        print(f"Status: {'✅ VERIFIED' if is_valid else '❌ UNVERIFIED'}")
        print(f"Reason: {reason}")
        print(f"{'='*50}")

        if is_valid:
            print("\n🎉 SUCCESS: Capsule is cryptographically verified!")
            print("✅ Ed25519 signature validation: PASSED")
            print("✅ Hash integrity check: PASSED")
            print("✅ Replay protection: PASSED")
            print("✅ Format validation: PASSED")
            print("\n🖥️ Frontend should display: 'Verified' status")
        else:
            print(f"\n❌ FAILURE: Verification failed")
            print(f"   Reason: {reason}")

        return is_valid, reason

    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False, str(e)


if __name__ == "__main__":
    test_verification_from_database()
