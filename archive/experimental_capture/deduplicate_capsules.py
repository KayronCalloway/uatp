"""
Capsule Deduplication Script

This script identifies and removes duplicate capsules based on payload content.
It keeps the oldest copy of each unique capsule and removes duplicates.

⚠️ IMPORTANT:
- Always run with --dry-run first to preview changes
- Uses direct SQL queries (workaround for ORM issues)
- Focuses on live capsules only (excludes demo-* capsules)

Current Status:
- Target: 32 duplicate "monitoring implementation" capsules
- Result: Will reduce 34 reasoning_trace capsules → 3 unique capsules

Usage:
    # Preview changes (RECOMMENDED FIRST STEP)
    python3 deduplicate_capsules.py --dry-run

    # Apply deduplication to all capsule types
    python3 deduplicate_capsules.py

    # Only deduplicate reasoning_trace capsules
    python3 deduplicate_capsules.py --capsule-type reasoning_trace
"""

import asyncio
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import db


def compute_payload_hash(payload: Any) -> str:
    """Compute a hash of the payload to identify duplicates.

    Excludes fields that may vary between otherwise identical capsules:
    - timestamp
    - capsule_id
    - version
    """
    # Parse payload if it's a string
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            # If parsing fails, hash the raw string
            return hashlib.sha256(payload.encode()).hexdigest()

    # Create a copy and remove variable fields
    normalized = payload.copy() if isinstance(payload, dict) else payload

    # Fields to exclude from hash (metadata that doesn't affect content)
    if isinstance(normalized, dict):
        excluded_fields = {"timestamp", "created_at", "updated_at", "id"}
        for field in excluded_fields:
            normalized.pop(field, None)

    # Sort keys for consistent hashing
    payload_json = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(payload_json.encode()).hexdigest()


async def fetch_live_capsules(
    session: AsyncSession, capsule_type: str = None
) -> List[Dict[str, Any]]:
    """Fetch all live capsules (excluding demo capsules)."""

    sql = """
        SELECT id, capsule_id, capsule_type, timestamp, payload
        FROM capsules
        WHERE capsule_id NOT LIKE 'demo-%'
    """

    if capsule_type:
        sql += f" AND capsule_type = '{capsule_type}'"

    sql += " ORDER BY timestamp ASC"  # Oldest first

    result = await session.execute(text(sql))
    rows = result.fetchall()

    capsules = []
    for row in rows:
        capsules.append(
            {
                "id": row[0],
                "capsule_id": row[1],
                "capsule_type": row[2],
                "timestamp": row[3],
                "payload": row[4],
            }
        )

    return capsules


def identify_duplicates(
    capsules: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group capsules by payload hash to identify duplicates.

    Returns:
        Dict mapping payload_hash -> list of capsules with that hash
        (ordered by timestamp, oldest first)
    """
    hash_groups = defaultdict(list)

    for capsule in capsules:
        payload_hash = compute_payload_hash(capsule["payload"])
        hash_groups[payload_hash].append(capsule)

    # Only return groups with duplicates (more than 1 capsule)
    duplicates = {
        hash_key: capsules_list
        for hash_key, capsules_list in hash_groups.items()
        if len(capsules_list) > 1
    }

    return duplicates


async def delete_capsules(
    session: AsyncSession, capsule_ids: List[int], dry_run: bool = False
) -> int:
    """Delete capsules by their database ID."""

    if not capsule_ids:
        return 0

    if dry_run:
        print(f"   [DRY RUN] Would delete {len(capsule_ids)} capsule(s)")
        return len(capsule_ids)

    # Delete in batches of 100
    batch_size = 100
    total_deleted = 0

    for i in range(0, len(capsule_ids), batch_size):
        batch = capsule_ids[i : i + batch_size]
        placeholders = ",".join(["?" for _ in batch])
        sql = f"DELETE FROM capsules WHERE id IN ({placeholders})"

        await session.execute(text(sql), batch)
        total_deleted += len(batch)

    await session.commit()
    return total_deleted


def print_duplicate_group(group_num: int, capsules: List[Dict[str, Any]]):
    """Pretty print a group of duplicate capsules."""
    print(f"\n{'='*70}")
    print(f"📦 Duplicate Group #{group_num}")
    print(f"{'='*70}")

    # Show common info
    first = capsules[0]
    print(f"Type: {first['capsule_type']}")
    print(f"Prompt: {first['payload'].get('prompt', 'N/A')[:80]}...")
    print(f"Total copies: {len(capsules)}")
    print()

    # Show each capsule
    for i, capsule in enumerate(capsules, 1):
        marker = "🔵 KEEP" if i == 1 else "🔴 DELETE"
        print(f"  {marker} [{i}/{len(capsules)}]")
        print(f"     Capsule ID: {capsule['capsule_id']}")
        print(f"     Created: {capsule['timestamp']}")
        print(f"     DB ID: {capsule['id']}")
        print()


async def main():
    """Main deduplication process."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Remove duplicate capsules from database"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without making changes",
    )
    parser.add_argument(
        "--capsule-type",
        type=str,
        help="Only deduplicate this capsule type (e.g., reasoning_trace)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  CAPSULE DEDUPLICATION SCRIPT")
    print("  Identify and remove duplicate capsules")
    print("=" * 70)

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made\n")
    else:
        print("\n🔥 LIVE MODE - Duplicates will be permanently deleted\n")

    # Initialize database
    from src.app_factory import create_app

    app = create_app()

    if not db.engine:
        db.init_app(app)

    async with db.get_session() as session:
        # Fetch all live capsules
        print("🔍 Fetching capsules from database...")
        if args.capsule_type:
            print(f"   Filtering by type: {args.capsule_type}")

        capsules = await fetch_live_capsules(session, args.capsule_type)
        print(f"   Found {len(capsules)} live capsules")

        if not capsules:
            print("\n✅ No capsules found to process.")
            return

        # Identify duplicates
        print("\n🔍 Analyzing for duplicates...")
        duplicate_groups = identify_duplicates(capsules)

        if not duplicate_groups:
            print("\n✅ No duplicates found! All capsules are unique.")
            return

        # Calculate statistics
        total_duplicates = sum(len(group) - 1 for group in duplicate_groups.values())
        print("\n📊 Duplicate Analysis:")
        print(f"   Unique content items: {len(duplicate_groups)}")
        print(f"   Total duplicate copies: {total_duplicates}")
        print(f"   Capsules to delete: {total_duplicates}")
        print(f"   Capsules to keep: {len(duplicate_groups)}")

        # Show detailed breakdown by type
        type_stats = defaultdict(lambda: {"groups": 0, "duplicates": 0})
        for group in duplicate_groups.values():
            capsule_type = group[0]["capsule_type"]
            type_stats[capsule_type]["groups"] += 1
            type_stats[capsule_type]["duplicates"] += len(group) - 1

        print("\n📋 By Capsule Type:")
        for capsule_type, stats in sorted(type_stats.items()):
            print(f"   {capsule_type}:")
            print(f"      - {stats['groups']} unique content(s)")
            print(f"      - {stats['duplicates']} duplicate(s) to remove")

        # Show each duplicate group
        print(f"\n{'='*70}")
        print("DETAILED DUPLICATE GROUPS")
        print(f"{'='*70}")

        for i, (hash_key, group) in enumerate(duplicate_groups.items(), 1):
            print_duplicate_group(i, group)

        # Collect IDs to delete (all except oldest in each group)
        ids_to_delete = []
        for group in duplicate_groups.values():
            # Keep first (oldest), delete rest
            for capsule in group[1:]:
                ids_to_delete.append(capsule["id"])

        # Delete duplicates
        print(f"\n{'='*70}")
        print("DEDUPLICATION SUMMARY")
        print(f"{'='*70}")

        if args.dry_run:
            print(
                f"\n⚠️  DRY RUN - Would delete {len(ids_to_delete)} duplicate capsule(s)"
            )
            print("   Run without --dry-run to apply changes")
        else:
            print(f"\n🔥 Deleting {len(ids_to_delete)} duplicate capsule(s)...")
            deleted_count = await delete_capsules(session, ids_to_delete, dry_run=False)
            print(f"   ✅ Successfully deleted {deleted_count} capsule(s)")
            print("\n💾 Database updated - duplicates removed")

        print(f"\n{'='*70}")
        print("  DEDUPLICATION COMPLETE")
        print(f"  Original: {len(capsules)} capsules")
        print(f"  Duplicates: {total_duplicates} removed")
        print(f"  Final: {len(capsules) - total_duplicates} unique capsules")
        print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
