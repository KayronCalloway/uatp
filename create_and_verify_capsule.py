#!/usr/bin/env python3
"""
Create a test capsule and immediately verify UATP 7.0 envelope structure.
"""

import asyncio
import asyncpg
from datetime import datetime, timezone
from uuid import uuid4


async def create_and_verify():
    """Create a new capsule via database and verify envelope structure."""

    print("🔍 Creating Test Capsule and Verifying UATP 7.0 Envelope\n")
    print("=" * 70)

    # Connect to database
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        database='uatp_capsule_engine',
        user='uatp_user',
        password='uatp_password'
    )

    try:
        # Import the models to use the `from_pydantic` method with envelope wrapping
        import sys
        sys.path.insert(0, '/Users/kay/uatp-capsule-engine')

        from src.capsule_schema import ReasoningTraceCapsule, ReasoningTracePayload, Verification
        from src.models.capsule import CapsuleModel
        from src.core.database import db

        # Initialize database
        await db.init(
            host='localhost',
            port=5432,
            database='uatp_capsule_engine',
            username='uatp_user',
            password='uatp_password'
        )

        print("1️⃣ Creating new reasoning trace capsule...")

        # Create a Pydantic capsule object
        capsule_id = f"test_envelope_{uuid4().hex[:8]}"

        payload = ReasoningTracePayload(
            prompt="UATP 7.0 Envelope Verification Test - POST FIX",
            reasoning_steps=[
                {
                    "step": 1,
                    "content": "This capsule was created AFTER the envelope wrapper fix",
                    "step_type": "verification",
                    "metadata": {"test": True, "post_fix": True}
                }
            ],
            final_answer="Testing UATP 7.0 envelope structure implementation",
            confidence=1.0,
            model_used="verification-test-post-fix"
        )

        capsule = ReasoningTraceCapsule(
            capsule_id=capsule_id,
            version="7.0",
            timestamp=datetime.now(timezone.utc),
            status="verified",
            verification=Verification(
                hash="test_hash",
                signature="test_signature",
                signer="envelope_verifier",
                timestamp=datetime.now(timezone.utc)
            ),
            reasoning_trace=payload
        )

        print(f"   Capsule ID: {capsule_id}")

        # Convert to SQLAlchemy model (this is where envelope wrapping happens!)
        print("\n2️⃣ Converting to database model (applying envelope wrapper)...")
        model = CapsuleModel.from_pydantic(capsule)

        # Save to database
        print("\n3️⃣ Saving to database...")
        async with db.get_session() as session:
            session.add(model)
            await session.commit()

        print("   ✅ Capsule saved")

        # Query it back
        print("\n4️⃣ Querying capsule back from database...")
        row = await conn.fetchrow('''
            SELECT capsule_id, capsule_type, payload
            FROM capsules
            WHERE capsule_id = $1
        ''', capsule_id)

        if not row:
            print("   ❌ ERROR: Capsule not found!")
            return False

        payload_data = row['payload']

        # Check for UATP 7.0 envelope fields
        print("\n5️⃣ Checking UATP 7.0 envelope structure...")

        required_fields = ['content', 'metadata', 'trace', 'attribution', 'lineage', 'chain_context']

        print("\nRequired UATP 7.0 fields:")
        all_present = True
        for field in required_fields:
            is_present = field in payload_data
            status = '✅' if is_present else '❌'
            print(f"  {status} {field}")
            if not is_present:
                all_present = False

        print()
        print("=" * 70)
        if all_present:
            print("✅ ✅ ✅ VERIFICATION SUCCESSFUL! ✅ ✅ ✅")
            print("=" * 70)
            print("\nThe UATP 7.0 envelope wrapper is working correctly!")
            print("New capsules have the proper envelope structure.\n")

            # Show some details
            print("Envelope Details:")
            print(f"  - Platform: {payload_data.get('metadata', {}).get('platform', 'N/A')}")
            print(f"  - Envelope Version: {payload_data.get('metadata', {}).get('envelope_version', 'N/A')}")
            print(f"  - Created By: {payload_data.get('metadata', {}).get('created_by', 'N/A')}")
            print(f"  - Contributors: {len(payload_data.get('attribution', {}).get('contributors', []))}")
            print(f"  - Generation: {payload_data.get('lineage', {}).get('generation', 'N/A')}")
            print(f"  - Derivation Method: {payload_data.get('lineage', {}).get('derivation_method', 'N/A')}")
            print()
        else:
            print("❌ VERIFICATION FAILED!")
            print("=" * 70)
            print("\nThe envelope wrapper is NOT working.")
            print(f"Actual top-level fields: {list(payload_data.keys())}\n")

        return all_present

    finally:
        await conn.close()


if __name__ == "__main__":
    result = asyncio.run(create_and_verify())
    exit(0 if result else 1)
