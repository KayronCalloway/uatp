#!/usr/bin/env python3
"""
RFC 3161 Timestamp Backfill Script
==================================

Upgrades existing capsules with local_clock timestamps to RFC 3161 trusted timestamps.
This makes historical capsules court-admissible by adding independently verifiable timestamps.

The script:
1. Finds all capsules with local_clock or local_clock_fallback timestamps
2. Uses the existing content hash (doesn't re-hash, preserving signature validity)
3. Requests RFC 3161 timestamp from DigiCert TSA
4. Updates the verification.timestamp field in the database

Usage:
    python scripts/backfill_rfc3161_timestamps.py [--dry-run] [--limit N]
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from src.security.timestamp_authority import TimestampAuthority

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def backfill_timestamps(dry_run: bool = False, limit: int = None):
    """Backfill RFC 3161 timestamps for capsules with local timestamps."""

    import aiosqlite

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uatp_dev.db")

    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return

    # Initialize TSA client
    tsa = TimestampAuthority(mode="online")  # Require real TSA, don't fall back
    logger.info(f"TSA URL: {tsa.tsa_url}")
    logger.info(f"ASN1 available: {tsa._asn1_available}")

    if not tsa._asn1_available:
        logger.error("asn1crypto not available - cannot create RFC 3161 requests")
        return

    # Stats
    stats = {
        "total_checked": 0,
        "already_trusted": 0,
        "upgraded": 0,
        "failed": 0,
        "skipped_no_hash": 0,
    }

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        # Find capsules with local timestamps
        query = """
            SELECT id, capsule_id, verification
            FROM capsules
            WHERE json_extract(verification, '$.timestamp.method') IN ('local_clock', 'local_clock_fallback')
               OR json_extract(verification, '$.timestamp.trusted') = 0
               OR json_extract(verification, '$.timestamp.trusted') = 'false'
        """

        if limit:
            query += f" LIMIT {limit}"

        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()

        logger.info(f"Found {len(rows)} capsules with local timestamps")

        for row in rows:
            stats["total_checked"] += 1
            capsule_id = row["capsule_id"]

            try:
                verification = (
                    json.loads(row["verification"])
                    if isinstance(row["verification"], str)
                    else row["verification"]
                )
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Invalid verification JSON for {capsule_id}")
                stats["failed"] += 1
                continue

            # Check if already trusted
            ts_info = verification.get("timestamp", {})
            if ts_info.get("trusted"):
                stats["already_trusted"] += 1
                continue

            # Get the content hash
            content_hash = verification.get("hash")
            if not content_hash:
                logger.warning(f"No content hash for {capsule_id} - cannot timestamp")
                stats["skipped_no_hash"] += 1
                continue

            # Convert hex hash to bytes
            try:
                hash_bytes = bytes.fromhex(content_hash)
            except ValueError:
                logger.warning(
                    f"Invalid hash format for {capsule_id}: {content_hash[:20]}..."
                )
                stats["failed"] += 1
                continue

            logger.info(f"Timestamping {capsule_id} (hash: {content_hash[:16]}...)")

            if dry_run:
                logger.info("  [DRY RUN] Would request RFC 3161 timestamp")
                stats["upgraded"] += 1
                continue

            # Request RFC 3161 timestamp
            try:
                new_timestamp = tsa.timestamp_hash(hash_bytes)

                if new_timestamp.get("trusted"):
                    # Update verification with new timestamp
                    verification["timestamp"] = new_timestamp

                    # Also add upgrade metadata
                    verification["timestamp"]["upgraded_from"] = ts_info.get(
                        "method", "unknown"
                    )
                    verification["timestamp"]["upgrade_time"] = datetime.now(
                        timezone.utc
                    ).isoformat()

                    # Update database
                    await db.execute(
                        "UPDATE capsules SET verification = ? WHERE id = ?",
                        (json.dumps(verification), row["id"]),
                    )
                    await db.commit()

                    logger.info(
                        f"  [OK] Upgraded to RFC 3161 (TSA: {new_timestamp.get('tsa_url')})"
                    )
                    stats["upgraded"] += 1
                else:
                    logger.warning("  [ERROR] TSA returned untrusted timestamp")
                    stats["failed"] += 1

            except Exception as e:
                logger.error(f"  [ERROR] Timestamp request failed: {e}")
                stats["failed"] += 1

    # Print summary
    print("\n" + "=" * 50)
    print("TIMESTAMP BACKFILL SUMMARY")
    print("=" * 50)
    print(f"  Total checked:     {stats['total_checked']}")
    print(f"  Already trusted:   {stats['already_trusted']}")
    print(f"  Upgraded:          {stats['upgraded']}")
    print(f"  Failed:            {stats['failed']}")
    print(f"  Skipped (no hash): {stats['skipped_no_hash']}")
    print("=" * 50)

    if dry_run:
        print("\n[DRY RUN] No changes were made to the database.")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Backfill RFC 3161 timestamps for existing capsules"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying database",
    )
    parser.add_argument("--limit", type=int, help="Limit number of capsules to process")
    args = parser.parse_args()

    print("=" * 50)
    print("RFC 3161 Timestamp Backfill")
    print("=" * 50)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    if args.limit:
        print(f"Limit: {args.limit} capsules")
    print()

    asyncio.run(backfill_timestamps(dry_run=args.dry_run, limit=args.limit))


if __name__ == "__main__":
    main()
