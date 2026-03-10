"""
End-to-End Test: Verify new capsules go to PostgreSQL (frontend database)
"""

import asyncio
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


async def test_capture_flow():
    print("=" * 80)
    print("  END-TO-END CAPTURE TEST")
    print("  Testing: New Capsule → PostgreSQL → Frontend")
    print("=" * 80)

    # Step 1: Create a test capsule using the capture system

    from src.app_factory import create_app
    from src.core.database import db
    from src.models.capsule import CapsuleModel

    app = create_app()
    if not db.engine:
        db.init_app(app)

    # Check which database we're using
    db_url = str(db.engine.url) if db.engine else "not initialized"
    print("\n Database Configuration:")
    print(f"   Engine: {db_url[:80]}")

    # Create test capsule
    test_id = f"test_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    capsule_data = {
        "capsule_id": test_id,
        "capsule_type": "reasoning_trace",
        "version": "7.0",
        "timestamp": datetime.utcnow(),
        "status": "sealed",
        "payload": {
            "prompt": "End-to-end test capture",
            "reasoning_steps": [
                {"step": 1, "reasoning": "Test step 1", "confidence": 0.9}
            ],
            "final_answer": "Test complete",
            "confidence": 0.9,
        },
        "verification": {"verified": True, "trust_score": 0.9, "method": "test"},
    }

    print("\n[OK] Creating test capsule:")
    print(f"   ID: {test_id}")

    async with db.get_session() as session:
        capsule_model = CapsuleModel(
            capsule_id=capsule_data["capsule_id"],
            capsule_type=capsule_data["capsule_type"],
            version=capsule_data["version"],
            timestamp=capsule_data["timestamp"],
            status=capsule_data["status"],
            payload=capsule_data["payload"],
            verification=capsule_data["verification"],
        )
        session.add(capsule_model)
        await session.commit()

    print("    Saved to database via ORM")

    # Step 2: Verify it's in PostgreSQL (not SQLite)
    print("\n Verifying in PostgreSQL...")

    try:
        import asyncpg

        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database="uatp_capsule_engine",
            user="uatp_user",
        )

        result = await conn.fetchrow(
            "SELECT capsule_id, capsule_type FROM capsules WHERE capsule_id = $1",
            test_id,
        )

        if result:
            print(f"    Found in PostgreSQL: {result['capsule_id']}")
        else:
            print("    NOT FOUND in PostgreSQL - WRONG DATABASE!")
            await conn.close()
            return False

        await conn.close()
    except Exception as e:
        print(f"    PostgreSQL check failed: {e}")
        return False

    # Step 3: Verify it's accessible via API (what frontend uses)
    print("\n Verifying via API (frontend access)...")

    import requests

    try:
        response = requests.get(f"http://localhost:8000/capsules/{test_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"    Accessible via API: {data['capsule']['capsule_id']}")
        else:
            print(f"    API returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"    API check failed: {e}")
        return False

    # Step 4: Summary
    print(f"\n{'=' * 80}")
    print("  [OK] END-TO-END TEST PASSED")
    print(f"{'=' * 80}")
    print("\n Test Results:")
    print("    Capsule created via ORM")
    print("    Stored in PostgreSQL (not SQLite)")
    print("    Accessible via API")
    print("    Frontend will be able to see it")
    print(f"\n Test Capsule ID: {test_id}")
    print(f"   View in frontend: http://localhost:3000 → Capsules → {test_id}")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_capture_flow())
    sys.exit(0 if success else 1)
