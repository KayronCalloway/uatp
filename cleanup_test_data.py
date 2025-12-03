#!/usr/bin/env python3
"""
Clean up test/training data from production database.
This script identifies and handles test capsules to maintain data integrity.
"""
import asyncio
import sys
import os
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to path
sys.path.insert(0, "/Users/kay/uatp-capsule-engine")

# Force use of PostgreSQL production database
os.environ[
    "DATABASE_URL"
] = "postgresql+asyncpg://uatp_user:uatp_password@localhost:5432/uatp_capsule_engine"

from src.core.database import db
from src.models.capsule import CapsuleModel


async def identify_test_capsules():
    """Identify test capsules based on patterns"""
    test_patterns = [
        "filter_auto_",  # Auto-generated test capsules
        "test_",  # Explicitly named test capsules
        "mock_",  # Mock data capsules
        "demo_",  # Demo capsules
    ]

    async with db.get_session() as session:
        query = select(CapsuleModel)
        result = await session.execute(query)
        all_capsules = result.scalars().all()

        test_capsules = []
        production_capsules = []

        for capsule in all_capsules:
            is_test = False

            # Check ID patterns
            for pattern in test_patterns:
                if capsule.capsule_id.startswith(pattern):
                    is_test = True
                    break

            # Check timestamps (capsules from July 2025 are likely tests from development)
            if capsule.timestamp.year == 2025 and capsule.timestamp.month <= 7:
                is_test = True

            # Check payload for test indicators
            if capsule.payload:
                payload_str = str(capsule.payload).lower()
                if any(
                    word in payload_str for word in ["test", "mock", "demo", "example"]
                ):
                    is_test = True

            if is_test:
                test_capsules.append(capsule)
            else:
                production_capsules.append(capsule)

        return test_capsules, production_capsules


async def display_analysis():
    """Display analysis of test vs production capsules"""
    test_capsules, production_capsules = await identify_test_capsules()

    print("=" * 80)
    print("UATP Database Cleanup Analysis")
    print("=" * 80)
    print(f"\nTotal Capsules: {len(test_capsules) + len(production_capsules)}")
    print(f"Test Capsules: {len(test_capsules)}")
    print(f"Production Capsules: {len(production_capsules)}")
    print("\n" + "=" * 80)

    if test_capsules:
        print("\nTest Capsules Identified:")
        print("-" * 80)
        for capsule in test_capsules[:10]:  # Show first 10
            print(
                f"  ID: {capsule.capsule_id[:40]:<40} | Type: {capsule.capsule_type:<20} | Date: {capsule.timestamp.strftime('%Y-%m-%d')}"
            )
        if len(test_capsules) > 10:
            print(f"  ... and {len(test_capsules) - 10} more")

    if production_capsules:
        print("\n" + "=" * 80)
        print("\nProduction Capsules:")
        print("-" * 80)
        for capsule in production_capsules[:10]:  # Show first 10
            print(
                f"  ID: {capsule.capsule_id[:40]:<40} | Type: {capsule.capsule_type:<20} | Date: {capsule.timestamp.strftime('%Y-%m-%d')}"
            )
        if len(production_capsules) > 10:
            print(f"  ... and {len(production_capsules) - 10} more")

    return test_capsules, production_capsules


async def delete_test_capsules(dry_run=True):
    """Delete test capsules from database"""
    test_capsules, production_capsules = await identify_test_capsules()

    if not test_capsules:
        print("\n✅ No test capsules found!")
        return

    print(
        f"\n{'DRY RUN: Would delete' if dry_run else 'DELETING'} {len(test_capsules)} test capsules..."
    )

    if not dry_run:
        async with db.get_session() as session:
            for capsule in test_capsules:
                await session.delete(capsule)
            await session.commit()
        print(f"✅ Successfully deleted {len(test_capsules)} test capsules")
    else:
        print("✅ Dry run complete. Use --execute to actually delete.")

    print(f"\n📊 After cleanup: {len(production_capsules)} production capsules remain")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up test data from UATP database"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze and display test vs production data",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete test capsules (dry run by default)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute deletion (use with --delete)",
    )

    args = parser.parse_args()

    # Initialize database - use init_app() to set up the engine
    db.init_app(None)

    try:
        if args.analyze or (not args.delete):
            # Default action: analyze
            await display_analysis()

            if not args.delete:
                print("\n" + "=" * 80)
                print("OPTIONS:")
                print("  python3 cleanup_test_data.py --analyze     # Show analysis")
                print("  python3 cleanup_test_data.py --delete      # Dry run deletion")
                print(
                    "  python3 cleanup_test_data.py --delete --execute  # Actually delete"
                )
                print("=" * 80)

        if args.delete:
            await delete_test_capsules(dry_run=not args.execute)

    finally:
        # Dispose of the database engine to clean up connections
        if db.engine:
            await db.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
