#!/usr/bin/env python3
"""
Simple verification of UATP 7.0 Envelope Structure

This script checks the most recent capsule in the database to verify
it has the proper UATP 7.0 envelope structure.
"""

import asyncio
import json
from src.core.database import db


async def verify_envelope_structure():
    """Check the most recent capsule for UATP 7.0 envelope structure."""

    print("🔍 Verifying UATP 7.0 Envelope Structure\n")
    print("=" * 70)

    # Query the database for the most recent capsule
    print("\n1️⃣ Querying database for the most recent capsule...")

    async with db.get_session() as session:
        from sqlalchemy import text

        query = text("""
            SELECT
                capsule_id,
                capsule_type,
                timestamp,
                payload
            FROM capsules
            ORDER BY timestamp DESC
            LIMIT 1
        """)

        result = await session.execute(query)
        row = result.fetchone()

        if not row:
            print("❌ ERROR: No capsules found in database!")
            return False

        capsule_id = row[0]
        capsule_type = row[1]
        timestamp = row[2]
        payload = row[3]

        print(f"✅ Found most recent capsule:")
        print(f"   ID: {capsule_id}")
        print(f"   Type: {capsule_type}")
        print(f"   Timestamp: {timestamp}")

        # Check for UATP 7.0 envelope structure
        print("\n2️⃣ Checking UATP 7.0 envelope structure...")

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

        # Check detailed structure if all fields are present
        if all_present:
            print("\n3️⃣ Checking detailed envelope structure...")
            print("\n✅ ALL REQUIRED FIELDS PRESENT!")

            # Verify content structure
            if "content" in payload:
                content = payload["content"]
                print(f"\n📦 Content Section:")
                print(f"   - capsule_type: {content.get('capsule_type', 'MISSING')}")
                print(f"   - format: {content.get('format', 'MISSING')}")
                print(f"   - encoding: {content.get('encoding', 'MISSING')}")
                if "data" in content:
                    data_keys = list(content["data"].keys())
                    print(f"   - data fields: {', '.join(data_keys[:5])}{' ...' if len(data_keys) > 5 else ''}")

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
                steps = trace.get('reasoning_steps', [])
                print(f"   - reasoning_steps: {len(steps)} steps")
                if steps:
                    print(f"   - First step: {steps[0].get('content', 'N/A')[:60]}...")
                print(f"   - decision_points: {len(trace.get('decision_points', []))} points")
                conf_levels = trace.get('confidence_levels', {})
                if conf_levels:
                    print(f"   - confidence_levels: {list(conf_levels.keys())}")

            # Verify attribution structure
            if "attribution" in payload:
                attribution = payload["attribution"]
                print(f"\n👥 Attribution Section:")
                contributors = attribution.get('contributors', [])
                print(f"   - contributors: {len(contributors)} contributors")
                if contributors:
                    print(f"   - First contributor: {contributors[0].get('agent_id', 'unknown')} ({contributors[0].get('role', 'unknown')})")
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
            print("New capsules have the proper envelope structure.\n")

        else:
            print("\n❌ VERIFICATION FAILED!")
            print("\nSome required UATP 7.0 fields are missing.")
            print("The most recent capsule does not have the envelope structure.\n")

            # Show the actual payload structure
            print("Actual payload top-level fields:")
            print(f"  {', '.join(list(payload.keys()))}\n")

            print("Note: This might be an older capsule created before the fix.")
            print("Try creating a new capsule to test the envelope wrapper.\n")

        return all_present


if __name__ == "__main__":
    result = asyncio.run(verify_envelope_structure())
    exit(0 if result else 1)
