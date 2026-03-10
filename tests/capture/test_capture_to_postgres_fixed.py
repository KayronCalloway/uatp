"""
End-to-End Test: Verify new capsules go to PostgreSQL (with dotenv)
"""

import asyncio
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Load .env file FIRST
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent))


async def test_capture_flow():
    print("=" * 80)
    print("  END-TO-END CAPTURE TEST (With .env)")
    print("  Testing: New Capsule → PostgreSQL → Frontend")
    print("=" * 80)

    import os

    from src.app_factory import create_app
    from src.core.database import db
    from src.models.capsule import CapsuleModel

    # Show DATABASE_URL
    db_env = os.getenv("DATABASE_URL", "not set")
    print("\n Environment Configuration:")
    print(f"   DATABASE_URL: {db_env[:60]}...")

    app = create_app()
    if not db.engine:
        db.init_app(app)

    db_url = str(db.engine.url) if db.engine else "not initialized"
    print(f"   Engine URL: {db_url[:80]}")

    is_postgres = "postgres" in db_url.lower()
    print(f"   Using PostgreSQL: {is_postgres}")

    if not is_postgres:
        print("\n    Still using SQLite! Check if .env file exists.")
        return False

    # Create test capsule
    test_id = f'test_e2e_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}_{uuid.uuid4().hex[:8]}'

    capsule_data = {
        "capsule_id": test_id,
        "capsule_type": "reasoning_trace",
        "version": "7.0",
        "timestamp": datetime.now(timezone.utc),
        "status": "sealed",
        "payload": {
            "prompt": "End-to-end PostgreSQL test",
            "reasoning_steps": [
                {
                    "step": 1,
                    "reasoning": "Testing PostgreSQL connection",
                    "confidence": 0.95,
                }
            ],
            "final_answer": "PostgreSQL test successful",
            "confidence": 0.95,
            "uncertainty_analysis": {
                "epistemic_uncertainty": 0.05,
                "aleatoric_uncertainty": 0.03,
                "total_uncertainty": 0.058,
                "risk_score": 0.15,
                "confidence_interval": [0.90, 1.0],
            },
        },
        "verification": {"verified": True, "trust_score": 0.92, "method": "test"},
    }

    print("\n[OK] Creating test capsule via ORM:")
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

    print("    Committed to database")

    # Verify in PostgreSQL directly
    print("\n Verifying in PostgreSQL directly...")
    import asyncpg

    conn = await asyncpg.connect(
        host="localhost", port=5432, database="uatp_capsule_engine", user="uatp_user"
    )

    result = await conn.fetchrow(
        "SELECT capsule_id, capsule_type FROM capsules WHERE capsule_id = $1", test_id
    )

    if result:
        print("    Found in PostgreSQL!")
    else:
        print("    NOT FOUND - something went wrong")
        await conn.close()
        return False

    await conn.close()

    # Verify via API
    print("\n Verifying via API (frontend access)...")
    import requests

    response = requests.get(f"http://localhost:8000/capsules/{test_id}")
    if response.status_code == 200:
        data = response.json()
        print("    Accessible via API")
        print("    Frontend will see it!")
    else:
        print(f"    API returned: {response.status_code}")
        return False

    print(f'\n{"="*80}')
    print("  [OK] END-TO-END TEST PASSED")
    print(f'{"="*80}')
    print("\n Complete Flow Verified:")
    print("    .env file loaded correctly")
    print("    ORM using PostgreSQL (not SQLite)")
    print("    Capsule saved to PostgreSQL")
    print("    Accessible via API")
    print("    Frontend can display it")
    print("\n All new captures will follow this same path!")
    print(f"\n   Test Capsule: {test_id}")
    print(f'   View at: http://localhost:3000 → Capsules → search "{test_id[:20]}"')

    return True


if __name__ == "__main__":
    success = asyncio.run(test_capture_flow())
    sys.exit(0 if success else 1)
