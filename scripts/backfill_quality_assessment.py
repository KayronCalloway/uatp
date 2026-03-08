#!/usr/bin/env python3
"""
Quality Assessment Backfill Script
==================================

Adds multi-dimensional quality assessment to existing capsules.

Evaluates 6 dimensions:
- Completeness: Are all necessary steps present?
- Coherence: Does the reasoning flow logically?
- Evidence Quality: Are claims backed by evidence?
- Logical Validity: Are there logical fallacies?
- Bias Detection: Are there signs of bias?
- Clarity: Is the reasoning clearly expressed?

Usage:
    python scripts/backfill_quality_assessment.py [--dry-run] [--limit N]
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from src.analysis.quality_assessment import QualityAssessor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def backfill_quality(dry_run: bool = False, limit: int = None):
    """Backfill quality assessment for capsules."""

    import aiosqlite

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uatp_dev.db")

    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return

    stats = {
        "total_checked": 0,
        "already_assessed": 0,
        "assessed": 0,
        "failed": 0,
        "grades": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
    }

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row

        # Find capsules without quality assessment (skip demo capsules)
        query = """
            SELECT id, capsule_id, payload
            FROM capsules
            WHERE json_extract(payload, '$.quality_assessment') IS NULL
            AND capsule_id NOT LIKE 'demo-%'
        """

        if limit:
            query += f" LIMIT {limit}"

        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()

        logger.info(f"Found {len(rows)} capsules without quality assessment")

        for row in rows:
            stats["total_checked"] += 1
            capsule_id = row["capsule_id"]

            try:
                payload = (
                    json.loads(row["payload"])
                    if isinstance(row["payload"], str)
                    else row["payload"]
                )
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Invalid payload JSON for {capsule_id}")
                stats["failed"] += 1
                continue

            # Check if already assessed
            if payload.get("quality_assessment"):
                stats["already_assessed"] += 1
                continue

            # Create capsule dict for assessment
            capsule = {"payload": payload}

            logger.info(f"Assessing {capsule_id}...")

            if dry_run:
                # Still run assessment to show what would happen
                try:
                    assessment = QualityAssessor.assess_capsule(capsule)
                    logger.info(
                        f"  [DRY RUN] Grade: {assessment.quality_grade} ({assessment.overall_quality:.2f})"
                    )
                    stats["grades"][assessment.quality_grade] += 1
                    stats["assessed"] += 1
                except Exception as e:
                    logger.warning(f"  [DRY RUN] Assessment failed: {e}")
                    stats["failed"] += 1
                continue

            # Perform assessment
            try:
                assessment = QualityAssessor.assess_capsule(capsule)

                # Add assessment to payload
                payload["quality_assessment"] = {
                    "overall_quality": round(assessment.overall_quality, 3),
                    "quality_grade": assessment.quality_grade,
                    "dimensions": {
                        dim: {
                            "score": round(score.score, 3),
                            "issues": score.issues,
                            "suggestions": score.suggestions[:2],
                        }
                        for dim, score in assessment.dimension_scores.items()
                    },
                    "strengths": assessment.strengths,
                    "weaknesses": assessment.weaknesses,
                    "improvement_priority": [
                        {"dimension": dim, "impact": round(impact, 3)}
                        for dim, impact in assessment.improvement_priority[:3]
                    ],
                    "assessed_at": datetime.now(timezone.utc).isoformat(),
                    "backfilled": True,
                }

                # Update database
                await db.execute(
                    "UPDATE capsules SET payload = ? WHERE id = ?",
                    (json.dumps(payload), row["id"]),
                )
                await db.commit()

                logger.info(
                    f"  [OK] Grade: {assessment.quality_grade} ({assessment.overall_quality:.2f})"
                )
                stats["grades"][assessment.quality_grade] += 1
                stats["assessed"] += 1

            except Exception as e:
                logger.error(f"  [ERROR] Assessment failed: {e}")
                stats["failed"] += 1

    # Print summary
    print("\n" + "=" * 50)
    print("QUALITY ASSESSMENT BACKFILL SUMMARY")
    print("=" * 50)
    print(f"  Total checked:      {stats['total_checked']}")
    print(f"  Already assessed:   {stats['already_assessed']}")
    print(f"  Newly assessed:     {stats['assessed']}")
    print(f"  Failed:             {stats['failed']}")
    print()
    print("  Grade Distribution:")
    for grade in ["A", "B", "C", "D", "F"]:
        count = stats["grades"][grade]
        bar = "█" * count + "░" * (10 - min(count, 10))
        print(f"    {grade}: {bar} {count}")
    print("=" * 50)

    if dry_run:
        print("\n[DRY RUN] No changes were made to the database.")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Backfill quality assessment for existing capsules"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying database",
    )
    parser.add_argument("--limit", type=int, help="Limit number of capsules to process")
    args = parser.parse_args()

    print("=" * 50)
    print("Quality Assessment Backfill")
    print("=" * 50)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    if args.limit:
        print(f"Limit: {args.limit} capsules")
    print()

    asyncio.run(backfill_quality(dry_run=args.dry_run, limit=args.limit))


if __name__ == "__main__":
    main()
