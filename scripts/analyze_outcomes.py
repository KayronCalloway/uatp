#!/usr/bin/env python3
"""
Outcome Analysis Utilities
==========================

Analyze capsule outcomes to identify patterns and calibrate confidence.
"""

import asyncio
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.models.capsule import CapsuleModel

DATABASE_URL = "postgresql+asyncpg://uatp_user@localhost:5432/uatp_capsule_engine"


class OutcomeAnalyzer:
    """Analyze capsule outcomes for system improvement."""

    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_calibration_data(self) -> Dict[str, Any]:
        """
        Compare predicted confidence vs actual outcomes.

        Returns data for confidence calibration:
        - For each confidence bucket, what % actually succeeded?
        """
        async with self.async_session() as session:
            query = select(CapsuleModel).where(CapsuleModel.outcome_status.isnot(None))
            result = await session.execute(query)
            capsules = result.scalars().all()

            # Group by confidence buckets
            buckets = defaultdict(lambda: {"total": 0, "success": 0, "partial": 0})

            for capsule in capsules:
                payload = capsule.payload or {}
                confidence = payload.get("confidence", 0.5)

                # Create bucket (0.0-0.1, 0.1-0.2, etc.)
                bucket = round(confidence, 1)
                bucket_key = f"{bucket:.1f}"

                buckets[bucket_key]["total"] += 1
                if capsule.outcome_status == "success":
                    buckets[bucket_key]["success"] += 1
                elif capsule.outcome_status == "partial":
                    buckets[bucket_key]["partial"] += 1

            # Calculate actual success rates
            calibration = {}
            for bucket_key, data in sorted(buckets.items()):
                if data["total"] > 0:
                    actual_rate = (data["success"] + data["partial"] * 0.5) / data[
                        "total"
                    ]
                    calibration[bucket_key] = {
                        "predicted_confidence": float(bucket_key),
                        "actual_success_rate": round(actual_rate, 3),
                        "sample_size": data["total"],
                        "calibration_error": round(float(bucket_key) - actual_rate, 3),
                    }

            return {
                "calibration_by_bucket": calibration,
                "total_tracked": len(capsules),
            }

    async def get_failure_patterns(self) -> Dict[str, Any]:
        """
        Identify patterns in failed capsules.

        Look for:
        - Common topics that fail
        - Low confidence that still failed
        - Platform differences
        """
        async with self.async_session() as session:
            query = select(CapsuleModel).where(CapsuleModel.outcome_status == "failure")
            result = await session.execute(query)
            failures = result.scalars().all()

            patterns = {
                "topics": defaultdict(int),
                "platforms": defaultdict(int),
                "low_confidence_failures": 0,
                "high_confidence_failures": 0,
                "total_failures": len(failures),
            }

            for capsule in failures:
                payload = capsule.payload or {}
                session_meta = payload.get("session_metadata", {})

                # Track topics
                topics = session_meta.get("topics", [])
                for topic in topics:
                    patterns["topics"][topic] += 1

                # Track platforms
                platform = session_meta.get("platform", "unknown")
                patterns["platforms"][platform] += 1

                # Track by confidence
                confidence = payload.get("confidence", 0.5)
                if confidence < 0.6:
                    patterns["low_confidence_failures"] += 1
                elif confidence > 0.8:
                    patterns["high_confidence_failures"] += 1

            # Convert defaultdicts
            patterns["topics"] = dict(patterns["topics"])
            patterns["platforms"] = dict(patterns["platforms"])

            return patterns

    async def get_improvement_recommendations(self) -> List[str]:
        """Generate recommendations based on outcome data."""
        recommendations = []

        calibration = await self.get_calibration_data()
        failures = await self.get_failure_patterns()

        # Check for overconfidence
        for bucket, data in calibration.get("calibration_by_bucket", {}).items():
            if data["calibration_error"] > 0.15 and data["sample_size"] >= 5:
                recommendations.append(
                    f"[WARN] Overconfident at {bucket}: predicted {float(bucket):.0%}, "
                    f"actual {data['actual_success_rate']:.0%} (n={data['sample_size']})"
                )

        # Check for underconfidence
        for bucket, data in calibration.get("calibration_by_bucket", {}).items():
            if data["calibration_error"] < -0.15 and data["sample_size"] >= 5:
                recommendations.append(
                    f" Underconfident at {bucket}: predicted {float(bucket):.0%}, "
                    f"actual {data['actual_success_rate']:.0%} (n={data['sample_size']})"
                )

        # High confidence failures
        if failures.get("high_confidence_failures", 0) > 0:
            recommendations.append(
                f" {failures['high_confidence_failures']} failures with high confidence (>0.8) - "
                "review these cases for systematic issues"
            )

        # Topic-specific issues
        topic_failures = failures.get("topics", {})
        for topic, count in sorted(topic_failures.items(), key=lambda x: -x[1])[:3]:
            if count >= 2:
                recommendations.append(
                    f" Topic '{topic}' has {count} failures - may need more training data"
                )

        if not recommendations:
            recommendations.append(
                "[OK] No significant issues detected - continue collecting data"
            )

        return recommendations

    async def run_full_analysis(self):
        """Run complete outcome analysis."""
        print("=" * 60)
        print("Capsule Outcome Analysis")
        print("=" * 60)

        # Calibration
        print("\n CONFIDENCE CALIBRATION")
        print("-" * 40)
        calibration = await self.get_calibration_data()
        print(f"Total tracked capsules: {calibration['total_tracked']}")
        print("\nBy confidence bucket:")
        for bucket, data in calibration.get("calibration_by_bucket", {}).items():
            error_indicator = "[WARN]" if abs(data["calibration_error"]) > 0.15 else ""
            print(
                f"  {bucket}: predicted={float(bucket):.0%}, "
                f"actual={data['actual_success_rate']:.0%}, "
                f"n={data['sample_size']} {error_indicator}"
            )

        # Failure patterns
        print("\n[ERROR] FAILURE PATTERNS")
        print("-" * 40)
        failures = await self.get_failure_patterns()
        print(f"Total failures: {failures['total_failures']}")
        if failures["topics"]:
            print("By topic:", dict(list(failures["topics"].items())[:5]))
        if failures["platforms"]:
            print("By platform:", failures["platforms"])

        # Recommendations
        print("\n RECOMMENDATIONS")
        print("-" * 40)
        recommendations = await self.get_improvement_recommendations()
        for rec in recommendations:
            print(f"  {rec}")

        print("\n" + "=" * 60)


async def main():
    analyzer = OutcomeAnalyzer()
    await analyzer.run_full_analysis()


if __name__ == "__main__":
    asyncio.run(main())
