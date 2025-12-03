#!/usr/bin/env python3
"""Debug script to understand capsule loading issues."""

import asyncio
import json
import sqlite3
from src.models.capsule import CapsuleModel
from src.core.database import db
from src.engine.capsule_engine import CapsuleEngine
from sqlalchemy import select


async def debug_capsule_loading():
    """Debug the capsule loading process."""
    print("=== Debug Capsule Loading ===")

    # First, check what's in the database directly
    conn = sqlite3.connect("uatp_dev.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT capsule_id, capsule_type, payload FROM capsules WHERE capsule_id = 'caps_2025_07_27_ba74c513c27d4fd1'"
    )
    row = cursor.fetchone()

    if row:
        capsule_id, capsule_type, payload_json = row
        print(f"Raw database entry:")
        print(f"  capsule_id: {capsule_id}")
        print(f"  capsule_type: {capsule_type}")
        print(f"  payload JSON: {payload_json[:200]}...")

        # Parse the payload
        payload = json.loads(payload_json)
        print(f"\nParsed payload keys: {list(payload.keys())}")

        if "reasoning_trace" in payload:
            print(f"reasoning_trace keys: {list(payload['reasoning_trace'].keys())}")
            if "reasoning_steps" in payload["reasoning_trace"]:
                print(
                    f"reasoning_steps length: {len(payload['reasoning_trace']['reasoning_steps'])}"
                )

    conn.close()

    # Now try to load using the engine
    print("\n=== Testing Engine Loading ===")

    # Initialize the database and engine
    await db.init_db("sqlite:///./uatp_dev.db")
    engine = CapsuleEngine(db_manager=db)

    try:
        # Load the capsule
        capsule = await engine.load_capsule_async("caps_2025_07_27_ba74c513c27d4fd1")
        if capsule:
            print(f"Successfully loaded capsule: {capsule.capsule_id}")
            print(f"Capsule type: {capsule.capsule_type}")
            print(f"Available attributes: {dir(capsule)}")
        else:
            print("Failed to load capsule - not found")
    except Exception as e:
        print(f"Error loading capsule: {e}")
        import traceback

        traceback.print_exc()

    await db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(debug_capsule_loading())
