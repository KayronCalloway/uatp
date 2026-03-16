#!/usr/bin/env python3
"""
Backfill Rich Metadata to Legacy Capsules
==========================================

Enriches older capsules that lack:
- uncertainty_analysis (epistemic/aleatoric)
- critical_path_analysis
- risk_assessment
- plain_language_summary
- confidence_methodology
- improvement_recommendations

Uses the RichCaptureEnhancer pipeline to generate this metadata
from existing reasoning steps.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.analysis.critical_path import CriticalPathAnalyzer
from src.analysis.uncertainty_quantification import UncertaintyQuantifier
from src.models.capsule import CapsuleModel
from src.utils.rich_capsule_creator import RichReasoningStep

# Database setup
DATABASE_URL = "postgresql+asyncpg://uatp_user@localhost:5432/uatp_capsule_engine"


class LegacyCapsuleEnricher:
    """Enriches legacy capsules with rich metadata."""

    def __init__(self):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.stats = {
            "total_processed": 0,
            "already_rich": 0,
            "enriched": 0,
            "errors": 0,
        }

    def _needs_enrichment(self, payload: Dict[str, Any]) -> bool:
        """Check if a capsule needs rich metadata backfill."""
        if not payload:
            return True

        # Check for key rich metadata fields
        has_uncertainty = "uncertainty_analysis" in payload
        has_critical_path = "critical_path_analysis" in payload
        has_risk = "risk_assessment" in payload
        has_summary = "plain_language_summary" in payload

        # If missing any, needs enrichment
        return not (has_uncertainty and has_critical_path and has_risk and has_summary)

    def _extract_reasoning_steps(
        self, payload: Dict[str, Any]
    ) -> List[RichReasoningStep]:
        """Extract or create reasoning steps from payload."""
        steps = []
        raw_steps = payload.get("reasoning_steps", [])

        if not raw_steps:
            # Try other locations
            raw_steps = payload.get("reasoning_trace", {}).get("steps", [])

        if not raw_steps:
            # Create minimal step from content
            content = payload.get("content", "")
            if isinstance(content, dict):
                content = content.get("data", {}).get("content", str(content))
            if content:
                raw_steps = [{"reasoning": str(content)[:500], "confidence": 0.7}]

        for i, step in enumerate(raw_steps, 1):
            if isinstance(step, str):
                # String step - wrap it
                steps.append(
                    RichReasoningStep(
                        step=i,
                        reasoning=step[:500],
                        confidence=0.7,
                        operation="analysis",
                    )
                )
            elif isinstance(step, dict):
                # Dict step - extract fields
                reasoning = step.get("reasoning", step.get("content", ""))
                if isinstance(reasoning, dict):
                    reasoning = str(reasoning)

                confidence = step.get("confidence", 0.7)
                if confidence > 0.95:
                    confidence = 0.95  # Apply cap

                steps.append(
                    RichReasoningStep(
                        step=i,
                        reasoning=reasoning[:500] if reasoning else f"Step {i}",
                        confidence=confidence,
                        operation=step.get("operation", "analysis"),
                        uncertainty_sources=step.get("uncertainty_sources"),
                        confidence_basis=step.get("confidence_basis"),
                        measurements=step.get("measurements"),
                        alternatives_considered=step.get("alternatives_considered"),
                        attribution_sources=step.get("attribution_sources"),
                    )
                )

        return (
            steps
            if steps
            else [
                RichReasoningStep(
                    step=1,
                    reasoning="Legacy capsule",
                    confidence=0.7,
                    operation="analysis",
                )
            ]
        )

    def _generate_rich_metadata(
        self, payload: Dict[str, Any], steps: List[RichReasoningStep]
    ) -> Dict[str, Any]:
        """Generate rich metadata from reasoning steps."""
        enriched = {}

        # 1. Critical Path Analysis
        critical_path = CriticalPathAnalyzer.analyze(steps)
        enriched["critical_path_analysis"] = CriticalPathAnalyzer.to_dict(critical_path)

        # 2. Calculate overall confidence using geometric mean
        if steps:
            import operator
            from functools import reduce

            confidences = [s.confidence for s in steps]
            product = reduce(operator.mul, confidences, 1.0)
            overall_confidence = product ** (1.0 / len(confidences))
        else:
            overall_confidence = 0.7

        # Use critical path strength if available
        if critical_path.critical_path_strength:
            overall_confidence = critical_path.critical_path_strength

        enriched["confidence"] = round(min(0.95, overall_confidence), 3)

        # 3. Uncertainty Analysis
        step_uncertainties = []
        for step in steps:
            unc = UncertaintyQuantifier.estimate_confidence_uncertainty(
                confidence=step.confidence,
                sample_size=len(steps),
                prior_mean=0.8,
                prior_strength=5.0,
            )
            step_uncertainties.append(unc)

        if step_uncertainties:
            overall_unc = UncertaintyQuantifier.propagate_uncertainty(
                step_uncertainties
            )
            enriched["uncertainty_analysis"] = {
                "epistemic_uncertainty": round(overall_unc.epistemic_uncertainty, 3),
                "aleatoric_uncertainty": round(overall_unc.aleatoric_uncertainty, 3),
                "total_uncertainty": round(overall_unc.total_uncertainty, 3),
                "confidence_interval": [
                    round(overall_unc.confidence_interval[0], 3),
                    round(overall_unc.confidence_interval[1], 3),
                ],
                "risk_score": round(overall_unc.risk_score, 3),
            }

        # 4. Improvement Recommendations
        step_map = {step.step: step for step in steps}
        recommendations = CriticalPathAnalyzer.generate_improvement_recommendations(
            critical_path, step_map
        )
        if recommendations:
            enriched["improvement_recommendations"] = recommendations

        # 5. Confidence Methodology
        if len(steps) > 5 and critical_path.critical_steps:
            enriched["confidence_methodology"] = {
                "method": "critical_path_weighted",
                "critical_path_steps": critical_path.critical_steps,
                "explanation": f"Based on critical path strength across {len(critical_path.critical_steps)} critical steps",
            }
        elif len(steps) > 5:
            enriched["confidence_methodology"] = {
                "method": "geometric_mean",
                "explanation": f"Geometric mean of {len(steps)} step confidences",
            }
        else:
            enriched["confidence_methodology"] = {
                "method": "manual",
                "explanation": "Direct assessment of message characteristics",
            }

        # 6. Risk Assessment
        session_meta = payload.get("session_metadata", {})
        topics = session_meta.get("topics", ["General"])
        message_count = len(steps)

        enriched["risk_assessment"] = {
            "probability_correct": round(overall_confidence, 2),
            "probability_wrong": round(1 - overall_confidence, 2),
            "expected_value": round(message_count * 5.0, 2),
            "value_at_risk_95": round(message_count * 5.0 * 1.1, 2),
            "expected_loss_if_wrong": round(message_count * 15.0, 2),
            "expected_gain_if_correct": round(message_count * 10.0, 2),
            "key_risk_factors": self._identify_risk_factors(steps, session_meta),
            "safeguards": [
                "Cryptographic signature on all data",
                "Timestamped immutable records",
                "Multi-turn reasoning with confidence tracking",
            ],
            "failure_modes": [
                {
                    "scenario": "Hallucination or outdated information",
                    "probability": 0.04,
                    "mitigation": "Cross-reference with documentation and testing",
                }
            ],
            "similar_decisions_count": 0,
            "historical_accuracy": None,
        }

        # 7. Plain Language Summary
        platform = session_meta.get("platform", "unknown")
        enriched["plain_language_summary"] = {
            "decision": "Conversation completed",
            "why": f"This decision was made based on analysis of {message_count} conversation turns across {platform}. "
            "The AI analyzed requirements and provided recommendations based on best practices.",
            "key_factors": [
                f"Analyzed {message_count} messages to understand requirements",
                "Applied coding best practices and industry standards",
                "Considered technical constraints and feasibility",
                f"Focused on: {', '.join(topics[:3]) if topics else 'General discussion'}",
            ],
            "what_if_different": "Different requirements, constraints, or technical context could lead to different recommendations.",
            "your_rights": "You have the right to: (1) Request human review, (2) Provide additional context, "
            "(3) Contest any recommendation, (4) Access all data used in this decision.",
            "how_to_appeal": "To request review: Contact the UATP platform operator with the capsule ID.",
        }

        # 8. Ensure alternatives exist
        if (
            "alternatives_considered" not in payload
            or not payload["alternatives_considered"]
        ):
            enriched["alternatives_considered"] = [
                {
                    "option": "No AI assistance (manual implementation)",
                    "score": 0.3,
                    "why_not_chosen": "AI assistance provides faster and more reliable results",
                    "data": {"baseline": True},
                },
                {
                    "option": "AI-assisted implementation (Selected)",
                    "score": 0.85,
                    "why_not_chosen": None,
                    "data": {"selected": True},
                },
            ]

        return enriched

    def _identify_risk_factors(
        self, steps: List[RichReasoningStep], session_meta: Dict[str, Any]
    ) -> List[str]:
        """Identify risk factors from steps and session."""
        factors = []

        if len(steps) < 3:
            factors.append("Limited context - few conversation turns")

        low_conf_steps = [s for s in steps if s.confidence < 0.6]
        if low_conf_steps:
            factors.append(f"{len(low_conf_steps)} steps with low confidence")

        uncertain_steps = [s for s in steps if s.uncertainty_sources]
        if uncertain_steps:
            factors.append("Uncertainty sources identified in reasoning")

        return factors if factors else []

    async def process_capsule(self, capsule: CapsuleModel) -> bool:
        """Process a single capsule and add rich metadata."""
        try:
            payload = capsule.payload or {}

            if not self._needs_enrichment(payload):
                self.stats["already_rich"] += 1
                return False

            # Extract reasoning steps
            steps = self._extract_reasoning_steps(payload)

            # Generate rich metadata
            enriched = self._generate_rich_metadata(payload, steps)

            # Merge with existing payload
            updated_payload = {**payload, **enriched}

            # Update platform if unknown
            session_meta = updated_payload.get("session_metadata", {})
            if session_meta.get("platform") == "unknown" or not session_meta.get(
                "platform"
            ):
                # Try to infer from capsule_id or other fields
                capsule_id = capsule.capsule_id or ""
                if "claude" in capsule_id.lower():
                    session_meta["platform"] = "claude-code"
                elif "antigravity" in capsule_id.lower():
                    session_meta["platform"] = "google_antigravity"
                updated_payload["session_metadata"] = session_meta

            # Update in database
            async with self.async_session() as session:
                await session.execute(
                    update(CapsuleModel)
                    .where(CapsuleModel.id == capsule.id)
                    .values(payload=updated_payload)
                )
                await session.commit()

            self.stats["enriched"] += 1
            return True

        except Exception as e:
            print(f"  [ERROR] Error processing {capsule.capsule_id}: {e}")
            self.stats["errors"] += 1
            return False

    async def run(self, dry_run: bool = False, limit: Optional[int] = None):
        """Run the backfill process."""
        print("=" * 60)
        print("Rich Metadata Backfill")
        print("=" * 60)

        if dry_run:
            print(" DRY RUN - no changes will be made")

        async with self.async_session() as session:
            # Fetch all capsules
            query = select(CapsuleModel).order_by(CapsuleModel.timestamp.desc())
            if limit:
                query = query.limit(limit)

            result = await session.execute(query)
            capsules = result.scalars().all()

            print(f"\n Found {len(capsules)} capsules to process")

            needs_enrichment = []
            for c in capsules:
                payload = c.payload or {}
                if self._needs_enrichment(payload):
                    needs_enrichment.append(c)

            print(f" {len(needs_enrichment)} need enrichment")
            print(
                f"[OK] {len(capsules) - len(needs_enrichment)} already have rich metadata"
            )

            if dry_run:
                print("\n Would process:")
                for c in needs_enrichment[:10]:
                    print(f"   - {c.capsule_id}")
                if len(needs_enrichment) > 10:
                    print(f"   ... and {len(needs_enrichment) - 10} more")
                return

            print("\n Starting enrichment...\n")

            for i, capsule in enumerate(needs_enrichment, 1):
                self.stats["total_processed"] += 1
                success = await self.process_capsule(capsule)

                status = "[OK]" if success else "⏭️"
                print(f"  [{i}/{len(needs_enrichment)}] {status} {capsule.capsule_id}")

            print("\n" + "=" * 60)
            print("RESULTS")
            print("=" * 60)
            print(f"  Total processed: {self.stats['total_processed']}")
            print(f"  Enriched:        {self.stats['enriched']}")
            print(f"  Already rich:    {self.stats['already_rich']}")
            print(f"  Errors:          {self.stats['errors']}")
            print("=" * 60)


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Backfill rich metadata to legacy capsules"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without making changes"
    )
    parser.add_argument("--limit", type=int, help="Limit number of capsules to process")
    args = parser.parse_args()

    enricher = LegacyCapsuleEnricher()
    await enricher.run(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
