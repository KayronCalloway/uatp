#!/usr/bin/env python3
"""
Migrate Legacy Capsules to Gold Standard Layered Format
========================================================

This script upgrades existing capsules to the v1.1 layered architecture:
- Adds layers structure (events, evidence, interpretation, judgment)
- Adds trust_posture multi-dimensional assessment
- Converts compliance labels to honest gated versions
- Runs self-inspection to detect contradictions

Usage:
    python -m src.cli.migrate_to_layered [--dry-run] [--limit N] [--capsule-id ID]

Options:
    --dry-run       Show what would be migrated without making changes
    --limit N       Only migrate N capsules (default: all)
    --capsule-id    Migrate a specific capsule by ID
    --force         Re-migrate capsules that already have layers
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def migrate_capsule(capsule_row, dry_run: bool = False) -> dict:
    """
    Migrate a single capsule to the layered format.

    Returns migration result with status and details.
    """
    from src.core.contradiction_engine import ContradictionEngine
    from src.core.layered_capsule_builder import convert_legacy_capsule

    capsule_id = capsule_row.capsule_id
    payload = (
        capsule_row.payload
        if isinstance(capsule_row.payload, dict)
        else json.loads(capsule_row.payload or "{}")
    )
    verification = (
        capsule_row.verification
        if isinstance(capsule_row.verification, dict)
        else json.loads(capsule_row.verification or "{}")
    )

    # Check if already migrated
    if "layers" in payload and "schema_version" in payload:
        return {
            "capsule_id": capsule_id,
            "status": "skipped",
            "reason": "Already has layered structure",
        }

    # Build the legacy capsule dict
    legacy_capsule = {
        "capsule_id": capsule_id,
        "timestamp": capsule_row.timestamp.isoformat()
        if capsule_row.timestamp
        else None,
        "payload": payload,
        "verification": verification,
        "metadata": payload.get("metadata", {}),
    }

    # Convert to layered format
    layered = convert_legacy_capsule(legacy_capsule)

    # Run self-inspection
    contradictions = ContradictionEngine.analyze_capsule(legacy_capsule)
    critical_count = len([c for c in contradictions if c.severity == "critical"])
    warning_count = len([c for c in contradictions if c.severity == "warning"])

    # Add self-inspection results to payload
    layered["self_inspection"] = {
        "migrated_at": datetime.now(timezone.utc).isoformat(),
        "contradictions_found": len(contradictions),
        "critical_count": critical_count,
        "warning_count": warning_count,
        "issues": [
            {
                "category": c.category,
                "severity": c.severity,
                "description": c.description,
            }
            for c in contradictions
        ]
        if contradictions
        else [],
    }

    if dry_run:
        return {
            "capsule_id": capsule_id,
            "status": "would_migrate",
            "layers_added": list(layered.get("layers", {}).keys()),
            "trust_posture": layered.get("trust_posture", {}),
            "contradictions": len(contradictions),
            "data_richness": layered.get("metadata", {}).get(
                "data_richness", "standard"
            ),
        }

    return {
        "capsule_id": capsule_id,
        "status": "migrated",
        "new_payload": layered,
        "contradictions": len(contradictions),
    }


def run_migration(
    dry_run: bool = False,
    limit: int = None,
    capsule_id: str = None,
    force: bool = False,
):
    """
    Run the migration on the database.
    """
    import sqlite3

    db_path = "uatp_dev.db"
    logger.info(f"Connecting to database: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build query
    if capsule_id:
        cursor.execute(
            "SELECT id, capsule_id, timestamp, payload, verification FROM capsules WHERE capsule_id = ?",
            (capsule_id,),
        )
    else:
        query = "SELECT id, capsule_id, timestamp, payload, verification FROM capsules ORDER BY timestamp DESC"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)

    rows = cursor.fetchall()
    logger.info(f"Found {len(rows)} capsules to process")

    # Stats
    migrated = 0
    skipped = 0
    errors = 0
    total_contradictions = 0

    for row in rows:
        try:
            # Create a simple object to mimic SQLAlchemy model
            class CapsuleRow:
                pass

            capsule = CapsuleRow()
            capsule.capsule_id = row["capsule_id"]
            capsule.timestamp = (
                datetime.fromisoformat(row["timestamp"]) if row["timestamp"] else None
            )
            capsule.payload = json.loads(row["payload"]) if row["payload"] else {}
            capsule.verification = (
                json.loads(row["verification"]) if row["verification"] else {}
            )

            # Check if already has layers (skip unless force)
            if not force and "layers" in capsule.payload:
                skipped += 1
                logger.debug(f"Skipping {capsule.capsule_id} - already migrated")
                continue

            result = migrate_capsule(capsule, dry_run=dry_run)

            if result["status"] == "skipped":
                skipped += 1
                logger.debug(f"Skipped {capsule.capsule_id}: {result.get('reason')}")
            elif result["status"] in ("migrated", "would_migrate"):
                migrated += 1
                total_contradictions += result.get("contradictions", 0)

                if dry_run:
                    logger.info(
                        f"[DRY-RUN] Would migrate {capsule.capsule_id}: "
                        f"layers={result.get('layers_added')}, "
                        f"contradictions={result.get('contradictions')}, "
                        f"data_richness={result.get('data_richness')}"
                    )
                else:
                    # Actually update the database
                    new_payload = result["new_payload"]
                    cursor.execute(
                        "UPDATE capsules SET payload = ? WHERE capsule_id = ?",
                        (json.dumps(new_payload), capsule.capsule_id),
                    )
                    logger.info(
                        f"Migrated {capsule.capsule_id}: "
                        f"contradictions={result.get('contradictions')}"
                    )

        except Exception as e:
            errors += 1
            logger.error(f"Error migrating {row['capsule_id']}: {e}")

    if not dry_run:
        conn.commit()
        logger.info("Changes committed to database")

    conn.close()

    # Summary
    logger.info("")
    logger.info("=" * 50)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total processed: {len(rows)}")
    logger.info(f"Migrated: {migrated}")
    logger.info(f"Skipped: {skipped}")
    logger.info(f"Errors: {errors}")
    logger.info(f"Total contradictions found: {total_contradictions}")
    if dry_run:
        logger.info("")
        logger.info("This was a DRY RUN. No changes were made.")
        logger.info("Run without --dry-run to apply changes.")

    return {
        "total": len(rows),
        "migrated": migrated,
        "skipped": skipped,
        "errors": errors,
        "contradictions": total_contradictions,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Migrate legacy capsules to gold standard layered format"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only migrate N capsules (default: all)",
    )
    parser.add_argument(
        "--capsule-id",
        type=str,
        default=None,
        help="Migrate a specific capsule by ID",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-migrate capsules that already have layers",
    )

    args = parser.parse_args()

    logger.info("UATP v1.1 Gold Standard Migration")
    logger.info("=" * 50)

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")

    result = run_migration(
        dry_run=args.dry_run,
        limit=args.limit,
        capsule_id=args.capsule_id,
        force=args.force,
    )

    # Exit code based on errors
    sys.exit(1 if result["errors"] > 0 else 0)


if __name__ == "__main__":
    main()
