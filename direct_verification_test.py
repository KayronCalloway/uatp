#!/usr/bin/env python3
"""
Direct verification test using the UATP engine directly.
"""

import asyncio
import sqlite3
import sys
import json

# Add src to path for imports
sys.path.insert(0, "/Users/kay/uatp-capsule-engine/src")

from src.engine.capsule_engine import CapsuleEngine
from src.core.database import DatabaseManager
from src.capsule_schema import ReasoningTraceCapsule


async def test_direct_verification():
    """Test verification directly through the engine."""
    print("🔍 Direct Capsule Verification Test")
    print("=" * 50)

    try:
        # Initialize database manager
        db_manager = DatabaseManager("sqlite:///./uatp_dev.db")
        await db_manager.initialize()

        # Initialize engine
        engine = CapsuleEngine(db_manager)

        # Get the latest capsule from database
        conn = sqlite3.connect("uatp_dev.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT capsule_id FROM capsules 
            WHERE capsule_id LIKE 'caps_2025_07_27_%'
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        )

        result = cursor.fetchone()
        conn.close()

        if not result:
            print("❌ No verified capsule found in database")
            return

        capsule_id = result[0]
        print(f"📋 Testing capsule: {capsule_id}")

        # Load capsule from database
        capsule = await engine.load_capsule_async(capsule_id)

        if not capsule:
            print("❌ Failed to load capsule from database")
            return

        print(f"✅ Loaded capsule: {capsule.capsule_type}")
        print(f"🔑 Signer: {capsule.verification.signer}")
        print(f"🔐 Hash: {capsule.verification.hash[:32]}...")
        print(f"✍️ Signature: {capsule.verification.signature[:32]}...")

        # Verify the capsule
        is_valid, reason = await engine.verify_capsule_async(capsule)

        print(f"\n🔍 Verification Result:")
        print(f"Status: {'✅ VERIFIED' if is_valid else '❌ UNVERIFIED'}")
        print(f"Reason: {reason}")

        if is_valid:
            print("\n🎉 SUCCESS: Capsule cryptographically verified!")
            print("Frontend should display: 'Verified' status")
        else:
            print(f"\n❌ FAILURE: {reason}")

        return is_valid, reason

    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False, str(e)


if __name__ == "__main__":
    asyncio.run(test_direct_verification())
