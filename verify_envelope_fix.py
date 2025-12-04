#!/usr/bin/env python3
"""
Verify UATP 7.0 Envelope Structure Fix

This script creates a test capsule and verifies that it has the proper
UATP 7.0 envelope structure with all required fields.
"""

import asyncio
import json
from datetime import datetime, timezone
from src.engine.capsule_engine import CapsuleEngine
from src.core.database import db


async def verify_envelope_fix():
    """Create a test capsule and verify its UATP 7.0 envelope structure."""

    print("🔍 Verifying UATP 7.0 Envelope Fix\n")
    print("=" * 70)

    # Initialize the capsule engine
    engine = CapsuleEngine()

    # Create a test reasoning capsule
    print("\n1️⃣ Creating test reasoning capsule...")

    capsule_data = {
        "prompt": "Test verification of UATP 7.0 envelope structure",
        "reasoning_steps": [
            {
                "step": 1,
                "content": "This is a test capsule to verify envelope wrapping",
                "step_type": "analysis",
                "metadata": {"test": True}
            }
        ],
        "final_answer": "UATP 7.0 envelope test",
        "confidence": 0.95,
        "model_used": "test-model",
        "session_metadata": {
            "test": True,
            "purpose": "verify_envelope_structure",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

    # Create the capsule using the engine
    capsule = await engine.create_reasoning_capsule(
        prompt=capsule_data["prompt"],
        reasoning_steps=capsule_data["reasoning_steps"],
        final_answer=capsule_data["final_answer"],
        confidence=capsule_data["confidence"],
        model_used=capsule_data["model_used"],
        session_metadata=capsule_data["session_metadata"]
    )

    capsule_id = capsule.capsule_id
    print(f"✅ Created capsule: {capsule_id}")

    # Query the database to get the raw stored data
    print("\n2️⃣ Querying database for capsule structure...")

    async with db.get_session() as session:
        from sqlalchemy import text

        query = text("""
            SELECT
                capsule_id,
                capsule_type,
                payload
            FROM capsules
            WHERE capsule_id = :capsule_id
        """)

        result = await session.execute(query, {"capsule_id": capsule_id})
        row = result.fetchone()

        if not row:
            print("❌ ERROR: Capsule not found in database!")
            return

        payload = row[2]  # The JSON payload

        print(f"✅ Found capsule in database")
        print(f"   Type: {row[1]}")

        # Check for UATP 7.0 envelope structure
        print("\n3️⃣ Checking UATP 7.0 envelope structure...")

        required_fields = {
            "content": "Content section (capsule data)",
            "metadata": "Metadata section (creation info)",
            "trace": "Trace section (reasoning steps)",
            "attribution": "Attribution section (contributors)",
            "lineage": "Lineage section (parent capsules)",
            "chain_context": "Chain context section (blockchain info)"
        }

        all_present = True
        print("\nRequired UATP 7.0 fields:")
        for field, description in required_fields.items():
            is_present = field in payload
            status = "✅" if is_present else "❌"
            print(f"  {status} {field:20s} - {description}")
            if not is_present:
                all_present = False

        # Check detailed structure
        print("\n4️⃣ Checking detailed envelope structure...")

        if all_present:
            print("\n✅ ALL REQUIRED FIELDS PRESENT!")

            # Verify content structure
            if "content" in payload:
                content = payload["content"]
                print(f"\n📦 Content Section:")
                print(f"   - capsule_type: {content.get('capsule_type', 'MISSING')}")
                print(f"   - format: {content.get('format', 'MISSING')}")
                print(f"   - encoding: {content.get('encoding', 'MISSING')}")
                print(f"   - data keys: {list(content.get('data', {}).keys())[:5]}")

            # Verify metadata structure
            if "metadata" in payload:
                metadata = payload["metadata"]
                print(f"\n📋 Metadata Section:")
                print(f"   - capsule_id: {metadata.get('capsule_id', 'MISSING')}")
                print(f"   - platform: {metadata.get('platform', 'MISSING')}")
                print(f"   - envelope_version: {metadata.get('envelope_version', 'MISSING')}")
                print(f"   - created_by: {metadata.get('created_by', 'MISSING')}")
                print(f"   - significance_score: {metadata.get('significance_score', 'MISSING')}")

            # Verify trace structure
            if "trace" in payload:
                trace = payload["trace"]
                print(f"\n🔍 Trace Section:")
                print(f"   - reasoning_steps: {len(trace.get('reasoning_steps', []))} steps")
                print(f"   - decision_points: {len(trace.get('decision_points', []))} points")
                print(f"   - confidence_levels: {list(trace.get('confidence_levels', {}).keys())}")

            # Verify attribution structure
            if "attribution" in payload:
                attribution = payload["attribution"]
                print(f"\n👥 Attribution Section:")
                print(f"   - contributors: {len(attribution.get('contributors', []))} contributors")
                print(f"   - weights: {list(attribution.get('weights', {}).keys())}")
                print(f"   - upstream_capsules: {len(attribution.get('upstream_capsules', []))} upstream")

            # Verify lineage structure
            if "lineage" in payload:
                lineage = payload["lineage"]
                print(f"\n🌳 Lineage Section:")
                print(f"   - parent_capsules: {len(lineage.get('parent_capsules', []))} parents")
                print(f"   - derivation_method: {lineage.get('derivation_method', 'MISSING')}")
                print(f"   - generation: {lineage.get('generation', 'MISSING')}")
                print(f"   - transformation_log: {len(lineage.get('transformation_log', []))} entries")

            # Verify chain context structure
            if "chain_context" in payload:
                chain_context = payload["chain_context"]
                print(f"\n⛓️  Chain Context Section:")
                print(f"   - chain_id: {chain_context.get('chain_id', 'MISSING')}")
                print(f"   - position: {chain_context.get('position', 'MISSING')}")
                print(f"   - previous_hash: {chain_context.get('previous_hash', 'MISSING')}")
                print(f"   - consensus_method: {chain_context.get('consensus_method', 'MISSING')}")

            print("\n" + "=" * 70)
            print("✅ VERIFICATION SUCCESSFUL!")
            print("=" * 70)
            print("\nThe UATP 7.0 envelope wrapper is working correctly.")
            print("All new capsules will have the proper envelope structure.\n")

        else:
            print("\n❌ VERIFICATION FAILED!")
            print("\nSome required UATP 7.0 fields are missing.")
            print("The envelope wrapper may not be working correctly.\n")

            # Show the actual payload structure
            print("Actual payload structure:")
            print(json.dumps(list(payload.keys()), indent=2))

        return all_present


if __name__ == "__main__":
    result = asyncio.run(verify_envelope_fix())
    exit(0 if result else 1)
