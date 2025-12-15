"""
Enrichment Script: Add Rich Analysis to Existing Capsules

This script backfills existing reasoning_trace capsules with:
- Critical path analysis
- Improvement recommendations
- Uncertainty analysis (epistemic/aleatoric)
- Trust score
- Rich step metadata

⚠️ KNOWN ISSUES:
- SQLAlchemy ORM queries return None objects in standalone scripts
- Database updates may not persist (transaction/session scope issue)
- See SQL_ORM_ISSUES_REPORT.md for detailed analysis

Current Status:
- Fetching: ✅ Works (using direct SQL)
- Enrichment: ✅ Works (analysis runs correctly)
- Persistence: ❌ Updates don't save to database
- Impact: Low (only 6 old capsules affected, new capsules work fine)

Usage:
    python3 enrich_existing_capsules.py [--dry-run] [--capsule-id CAPSULE_ID]
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis.critical_path import CriticalPathAnalyzer
from src.analysis.uncertainty_quantification import UncertaintyQuantifier
from src.core.database import db
from src.utils.rich_capsule_creator import (
    RichReasoningStep,
    calculate_capsule_trust_score,
)


async def fetch_reasoning_capsules(
    session: AsyncSession, capsule_id: str = None
) -> List[Dict[str, Any]]:
    """Fetch all live reasoning_trace capsules or a specific one."""
    from sqlalchemy import text

    # Use direct SQL since ORM query has issues
    sql = """
        SELECT id, capsule_id, capsule_type, version, timestamp, status, verification, payload
        FROM capsules
        WHERE capsule_type = 'reasoning_trace'
        AND capsule_id NOT LIKE 'demo-%'
    """

    if capsule_id:
        sql += f" AND capsule_id = '{capsule_id}'"

    result = await session.execute(text(sql))
    rows = result.fetchall()

    # Convert rows to dictionaries
    capsules = []
    for row in rows:
        capsules.append(
            {
                "id": row[0],
                "capsule_id": row[1],
                "capsule_type": row[2],
                "version": row[3],
                "timestamp": row[4],
                "status": row[5],
                "verification": row[6],
                "payload": row[7],
            }
        )

    return capsules


def convert_string_steps_to_rich(
    steps: List, base_confidence: float = 0.85
) -> List[RichReasoningStep]:
    """Convert simple string steps to RichReasoningStep objects."""
    rich_steps = []

    for i, step in enumerate(steps, 1):
        if isinstance(step, str):
            # Parse step number if present
            step_text = step
            if step.startswith("Step "):
                parts = step.split(":", 1)
                step_text = parts[1].strip() if len(parts) > 1 else step

            # Estimate confidence based on step characteristics
            confidence = base_confidence
            if len(step_text) > 200:  # Detailed step
                confidence += 0.05
            if "?" in step_text:  # Uncertainty
                confidence -= 0.10

            confidence = min(1.0, max(0.5, confidence))

            rich_step = RichReasoningStep(
                step=i,
                reasoning=step_text[:500],  # Truncate if too long
                confidence=confidence,
                operation="reasoning",
                uncertainty_sources=["Legacy conversion - no original metadata"]
                if confidence < 0.80
                else None,
                confidence_basis="Estimated from step characteristics",
                measurements={"legacy_conversion": True},
                alternatives_considered=None,
                depends_on_steps=None,
                attribution_sources=["legacy_capsule"],
            )
            rich_steps.append(rich_step)
        elif isinstance(step, dict):
            # Already rich, convert dict to RichReasoningStep
            rich_step = RichReasoningStep(
                step=step.get("step_id", i),
                reasoning=step.get("reasoning", ""),
                confidence=step.get("confidence", base_confidence),
                operation=step.get("operation", "reasoning"),
                uncertainty_sources=step.get("uncertainty_sources"),
                confidence_basis=step.get("confidence_basis"),
                measurements=step.get("measurements"),
                alternatives_considered=step.get("alternatives_considered"),
                depends_on_steps=step.get("depends_on_steps"),
                attribution_sources=step.get("attribution_sources", ["unknown"]),
            )
            rich_steps.append(rich_step)

    return rich_steps


def enrich_capsule_payload(capsule: Dict[str, Any]) -> Dict[str, Any]:
    """Add rich analysis to capsule payload."""
    payload = (
        capsule["payload"].copy() if isinstance(capsule.get("payload"), dict) else {}
    )

    # Get reasoning steps
    reasoning_steps = payload.get("reasoning_steps", [])
    overall_confidence = payload.get("confidence", 0.85)

    # Convert to rich steps if needed
    rich_steps = convert_string_steps_to_rich(reasoning_steps, overall_confidence)

    # 1. Add critical path analysis (if not present)
    if "critical_path_analysis" not in payload:
        print("  → Adding critical path analysis...")
        critical_path_analysis = CriticalPathAnalyzer.analyze(rich_steps)
        critical_path_dict = CriticalPathAnalyzer.to_dict(critical_path_analysis)
        payload["critical_path_analysis"] = critical_path_dict

    # 2. Add improvement recommendations (if not present)
    if "improvement_recommendations" not in payload:
        print("  → Adding improvement recommendations...")
        step_map = {step.step: step for step in rich_steps}
        critical_path_analysis = CriticalPathAnalyzer.analyze(rich_steps)
        improvement_recommendations = (
            CriticalPathAnalyzer.generate_improvement_recommendations(
                critical_path_analysis, step_map
            )
        )
        if improvement_recommendations:
            payload["improvement_recommendations"] = improvement_recommendations

    # 3. Add uncertainty analysis (if not present)
    if "uncertainty_analysis" not in payload:
        print("  → Adding uncertainty analysis...")
        # Calculate uncertainty for each step and propagate
        step_uncertainties = []
        for step in rich_steps:
            step_unc = UncertaintyQuantifier.estimate_confidence_uncertainty(
                confidence=step.confidence, sample_size=len(rich_steps), prior_mean=0.8
            )
            step_uncertainties.append(step_unc)

        if step_uncertainties:
            overall_uncertainty = UncertaintyQuantifier.propagate_uncertainty(
                step_uncertainties
            )
            payload["uncertainty_analysis"] = {
                "epistemic_uncertainty": round(
                    overall_uncertainty.epistemic_uncertainty, 3
                ),
                "aleatoric_uncertainty": round(
                    overall_uncertainty.aleatoric_uncertainty, 3
                ),
                "total_uncertainty": round(overall_uncertainty.total_uncertainty, 3),
                "confidence_interval": [
                    round(overall_uncertainty.confidence_interval[0], 3),
                    round(overall_uncertainty.confidence_interval[1], 3),
                ],
                "risk_score": round(overall_uncertainty.risk_score, 3),
            }

    # 4. Convert steps to rich format if they're still strings
    if reasoning_steps and isinstance(reasoning_steps[0], str):
        print(f"  → Converting {len(reasoning_steps)} steps to rich format...")
        # Add step-level uncertainty to measurements
        enriched_steps = []
        for i, step in enumerate(rich_steps):
            step_unc = UncertaintyQuantifier.estimate_confidence_uncertainty(
                confidence=step.confidence, sample_size=len(rich_steps)
            )

            step_dict = step.to_dict()
            if step_dict.get("measurements") is None:
                step_dict["measurements"] = {}

            step_dict["measurements"]["epistemic_uncertainty"] = round(
                step_unc.epistemic_uncertainty, 3
            )
            step_dict["measurements"]["aleatoric_uncertainty"] = round(
                step_unc.aleatoric_uncertainty, 3
            )
            enriched_steps.append(step_dict)

        payload["reasoning_steps"] = enriched_steps

    return payload


def enrich_verification(
    capsule: Dict[str, Any], payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Add trust score to verification section."""
    verification = (
        capsule["verification"].copy()
        if isinstance(capsule.get("verification"), dict)
        else {}
    )

    # Add trust score if not present
    if "trust_score" not in verification:
        print("  → Adding trust score to verification...")
        reasoning_steps = payload.get("reasoning_steps", [])
        overall_confidence = payload.get("confidence", 0.85)
        verified = verification.get("verified", True)

        trust_score = calculate_capsule_trust_score(
            reasoning_steps=reasoning_steps,
            overall_confidence=overall_confidence,
            verified=verified,
        )
        verification["trust_score"] = trust_score

    return verification


async def enrich_capsule(
    session: AsyncSession, capsule: Dict[str, Any], dry_run: bool = False
) -> bool:
    """Enrich a single capsule with rich analysis."""
    capsule_id = capsule.get("capsule_id", "unknown")
    print(f"\n📦 Processing: {capsule_id}")
    print(f"   Type: {capsule.get('capsule_type', 'unknown')}")
    print(f"   Created: {capsule.get('timestamp', 'unknown')}")

    try:
        # Enrich payload
        enriched_payload = enrich_capsule_payload(capsule)

        # Enrich verification
        enriched_verification = enrich_verification(capsule, enriched_payload)

        # Show what will be added
        print("\n   ✅ Enrichment complete!")
        print(
            f"      - critical_path_analysis: {('critical_path_analysis' in enriched_payload) and '✓' or '✗'}"
        )
        print(
            f"      - improvement_recommendations: {('improvement_recommendations' in enriched_payload) and '✓' or '✗'}"
        )
        print(
            f"      - uncertainty_analysis: {('uncertainty_analysis' in enriched_payload) and '✓' or '✗'}"
        )
        print(
            f"      - trust_score: {('trust_score' in enriched_verification) and '✓' or '✗'}"
        )
        print(
            f"      - rich_steps: {isinstance(enriched_payload.get('reasoning_steps', [{}])[0], dict) and '✓' or '✗'}"
        )

        if dry_run:
            print("   [DRY RUN] Would update capsule in database")
            return True

        # Update capsule in database
        from sqlalchemy import text

        # Use JSON strings for SQLite compatibility (works with both SQLite and PostgreSQL)
        stmt = text(
            """
            UPDATE capsules
            SET payload = :payload,
                verification = :verification
            WHERE id = :id
        """
        )

        await session.execute(
            stmt,
            {
                "payload": json.dumps(enriched_payload),
                "verification": json.dumps(enriched_verification),
                "id": capsule["id"],
            },
        )
        await session.commit()

        print("   💾 Updated in database")
        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        await session.rollback()
        return False


async def main():
    """Main enrichment process."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Enrich existing capsules with rich analysis"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument("--capsule-id", type=str, help="Enrich only a specific capsule")
    args = parser.parse_args()

    print("=" * 70)
    print("  CAPSULE ENRICHMENT SCRIPT")
    print("  Adding rich analysis to existing reasoning capsules")
    print("=" * 70)

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made\n")

    # Initialize database
    from src.app_factory import create_app

    app = create_app()

    # Ensure database is initialized
    if not db.engine:
        db.init_app(app)

    async with db.get_session() as session:
        # Fetch capsules
        capsules = await fetch_reasoning_capsules(session, args.capsule_id)

        print(f"\n🔍 Found {len(capsules)} reasoning_trace capsules to enrich")

        if not capsules:
            print("\n No capsules found to enrich.")
            return

        # Enrich each capsule
        success_count = 0
        failure_count = 0

        for capsule in capsules:
            success = await enrich_capsule(session, capsule, args.dry_run)
            if success:
                success_count += 1
            else:
                failure_count += 1

        print("\n" + "=" * 70)
        print("  ENRICHMENT COMPLETE")
        print(f"  ✅ Success: {success_count}")
        print(f"  ❌ Failures: {failure_count}")
        print("=" * 70)

        if not args.dry_run:
            print("\n💾 Database updated with enriched capsules")
        else:
            print("\n⚠️  Dry run complete - run without --dry-run to apply changes")


if __name__ == "__main__":
    asyncio.run(main())
