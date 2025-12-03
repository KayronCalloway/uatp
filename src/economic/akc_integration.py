"""
AKC Integration with FCDE Engine

This module integrates the Attribution Key Clustering (AKC) system with the
Fair Creator Dividend Engine (FCDE) to enable ancestral knowledge attribution
and post-labor economics.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from .fcde_engine import FCDEEngine, Contribution, ContributionType
from ..attribution.akc_system import AKCSystem, KnowledgeSource

logger = logging.getLogger(__name__)


class AKCFCDEIntegration:
    """Integration layer between AKC system and FCDE engine"""

    def __init__(self, akc_system: AKCSystem, fcde_engine: FCDEEngine):
        self.akc_system = akc_system
        self.fcde_engine = fcde_engine

    async def process_ancestral_contributions(
        self,
        capsule_id: str,
        total_revenue: Decimal,
        akc_contribution_percentage: Decimal = Decimal(
            "0.15"
        ),  # 15% to ancestral knowledge
    ) -> Dict[str, Decimal]:
        """
        Process ancestral knowledge contributions for a capsule and distribute
        appropriate dividends to knowledge source contributors.

        Args:
            capsule_id: ID of the capsule being used
            total_revenue: Total revenue generated from capsule usage
            akc_contribution_percentage: Percentage of revenue to allocate to ancestral knowledge

        Returns:
            Dictionary mapping contributor IDs to dividend amounts
        """
        logger.info(f"Processing ancestral contributions for capsule {capsule_id}")

        # Calculate AKC portion of revenue
        akc_revenue = total_revenue * akc_contribution_percentage

        # Get knowledge lineage for the capsule
        lineage = await self.akc_system.get_knowledge_lineage(capsule_id)

        if not lineage["sources"]:
            logger.info(
                f"No ancestral knowledge sources found for capsule {capsule_id}"
            )
            return {}

        # Calculate dividends for ancestral knowledge contributors
        ancestral_dividends = await self.akc_system.calculate_ancestral_dividends(
            total_revenue=float(akc_revenue), capsule_id=capsule_id
        )

        # Convert to Decimal for precision
        dividend_results = {}
        for contributor_id, amount in ancestral_dividends.items():
            dividend_results[contributor_id] = Decimal(str(amount))

        # Record contributions in FCDE for tracking
        await self._record_ancestral_contributions(
            capsule_id=capsule_id, lineage=lineage, total_akc_revenue=akc_revenue
        )

        logger.info(
            f"Distributed {akc_revenue} to {len(dividend_results)} ancestral contributors"
        )
        return dividend_results

    async def _record_ancestral_contributions(
        self, capsule_id: str, lineage: Dict, total_akc_revenue: Decimal
    ):
        """Record ancestral knowledge contributions in FCDE system"""

        timestamp = datetime.now(timezone.utc)

        # Create contributions for each knowledge source
        for source_data in lineage["sources"]:
            source_id = source_data["id"]

            # Get the actual source object
            if source_id not in self.akc_system.knowledge_sources:
                continue

            source = self.akc_system.knowledge_sources[source_id]

            # Create contribution for each author of the source
            for author in source.authors:
                contribution_id = f"akc_{source_id}_{author}_{timestamp.isoformat()}"

                # Calculate contribution value based on source metrics
                contribution_value = self._calculate_source_contribution_value(source)

                contribution = Contribution(
                    contribution_id=contribution_id,
                    contributor_id=author,
                    contribution_type=ContributionType.ANCESTRAL_KNOWLEDGE,
                    capsule_id=capsule_id,
                    timestamp=timestamp,
                    quality_score=Decimal(str(source.confidence_score)),
                    usage_count=source.usage_count,
                    verification_count=1
                    if source.verification_status.value == "verified"
                    else 0,
                    reward_multiplier=Decimal("1.0"),
                    metadata={
                        "source_id": source_id,
                        "source_type": source.type.value,
                        "source_title": source.title,
                        "doi": source.doi,
                        "url": source.url,
                        "verification_status": source.verification_status.value,
                        "akc_integration": True,
                    },
                )

                # Record in FCDE
                self.fcde_engine.record_contribution(contribution)

                # Record attribution
                if capsule_id not in self.fcde_engine.attributions:
                    self.fcde_engine.record_attribution(
                        capsule_id=capsule_id,
                        original_creator=author,
                        contributors=[author],
                        contribution_percentages={author: Decimal("100.0")},
                    )
                else:
                    # Add to existing attribution
                    attribution = self.fcde_engine.attributions[capsule_id]
                    if author not in attribution.contributors:
                        attribution.contributors.append(author)

                        # Recalculate contribution percentages
                        total_contributors = len(attribution.contributors)
                        new_percentage = Decimal("100.0") / Decimal(
                            str(total_contributors)
                        )
                        attribution.contribution_percentages = {
                            contributor: new_percentage
                            for contributor in attribution.contributors
                        }

    def _calculate_source_contribution_value(self, source: KnowledgeSource) -> Decimal:
        """Calculate the contribution value of a knowledge source"""

        # Base value depends on source type
        type_multipliers = {
            "academic_paper": Decimal("2.0"),
            "book": Decimal("1.5"),
            "code_repository": Decimal("1.8"),
            "dataset": Decimal("1.3"),
            "documentation": Decimal("1.0"),
            "blog_post": Decimal("0.8"),
            "patent": Decimal("2.2"),
            "expert_knowledge": Decimal("1.7"),
            "cultural_knowledge": Decimal("1.4"),
            "historical_record": Decimal("1.2"),
        }

        base_multiplier = type_multipliers.get(source.type.value, Decimal("1.0"))

        # Verification status affects value
        verification_multipliers = {
            "verified": Decimal("1.0"),
            "pending": Decimal("0.7"),
            "disputed": Decimal("0.3"),
            "rejected": Decimal("0.1"),
            "unknown": Decimal("0.5"),
        }

        verification_multiplier = verification_multipliers.get(
            source.verification_status.value, Decimal("0.5")
        )

        # Usage count affects value (logarithmic scaling)
        usage_multiplier = Decimal("1.0")
        if source.usage_count > 0:
            import math

            usage_multiplier = Decimal(
                str(1.0 + math.log10(source.usage_count + 1) * 0.2)
            )

        # Confidence score directly affects value
        confidence_multiplier = Decimal(str(source.confidence_score))

        # Calculate final value
        final_value = (
            base_multiplier
            * verification_multiplier
            * usage_multiplier
            * confidence_multiplier
        )

        return final_value

    async def update_source_usage_tracking(self, capsule_id: str, usage_value: Decimal):
        """Update usage tracking for knowledge sources associated with a capsule"""

        # Get knowledge lineage
        lineage = await self.akc_system.get_knowledge_lineage(capsule_id)

        if not lineage["sources"]:
            return

        # Track usage for each source
        source_ids = [source["id"] for source in lineage["sources"]]

        await self.akc_system.track_knowledge_usage(
            source_ids=source_ids,
            usage_context=f"Capsule usage: {usage_value}",
            capsule_id=capsule_id,
        )

        # Update FCDE usage tracking
        self.fcde_engine.record_usage(capsule_id, usage_value)

    async def get_ancestral_attribution_report(self, capsule_id: str) -> Dict:
        """Generate a comprehensive ancestral attribution report"""

        # Get knowledge lineage
        lineage = await self.akc_system.get_knowledge_lineage(capsule_id)

        # Get FCDE attribution
        fcde_attribution = self.fcde_engine.attributions.get(capsule_id)

        # Get ancestral contributions
        ancestral_contributions = [
            contrib
            for contrib in self.fcde_engine.contributions.values()
            if contrib.capsule_id == capsule_id
            and contrib.contribution_type == ContributionType.ANCESTRAL_KNOWLEDGE
        ]

        # Build report
        report = {
            "capsule_id": capsule_id,
            "lineage": lineage,
            "fcde_attribution": fcde_attribution.to_dict()
            if fcde_attribution
            else None,
            "ancestral_contributions": [
                {
                    "contribution_id": contrib.contribution_id,
                    "contributor_id": contrib.contributor_id,
                    "timestamp": contrib.timestamp.isoformat(),
                    "quality_score": float(contrib.quality_score),
                    "usage_count": contrib.usage_count,
                    "base_value": float(contrib.calculate_base_value()),
                    "metadata": contrib.metadata,
                }
                for contrib in ancestral_contributions
            ],
            "total_ancestral_contributors": len(
                set(contrib.contributor_id for contrib in ancestral_contributions)
            ),
            "total_ancestral_value": float(
                sum(
                    contrib.calculate_base_value()
                    for contrib in ancestral_contributions
                )
            ),
            "knowledge_sources_count": len(lineage["sources"]),
            "verified_sources_count": lineage["verified_sources"],
        }

        return report

    async def batch_process_ancestral_dividends(
        self,
        capsule_usages: List[Tuple[str, Decimal]],  # (capsule_id, revenue)
        akc_contribution_percentage: Decimal = Decimal("0.15"),
    ) -> Dict[str, Dict[str, Decimal]]:
        """Process ancestral dividends for multiple capsules in batch"""

        results = {}

        for capsule_id, revenue in capsule_usages:
            try:
                dividends = await self.process_ancestral_contributions(
                    capsule_id=capsule_id,
                    total_revenue=revenue,
                    akc_contribution_percentage=akc_contribution_percentage,
                )
                results[capsule_id] = dividends

            except Exception as e:
                logger.error(
                    f"Error processing ancestral contributions for {capsule_id}: {e}"
                )
                results[capsule_id] = {}

        return results

    async def get_contributor_ancestral_earnings(
        self,
        contributor_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Dict:
        """Get ancestral earnings for a specific contributor"""

        if period_end is None:
            period_end = datetime.now(timezone.utc)

        # Get all ancestral contributions for this contributor
        contributions = [
            contrib
            for contrib in self.fcde_engine.contributions.values()
            if contrib.contributor_id == contributor_id
            and contrib.contribution_type == ContributionType.ANCESTRAL_KNOWLEDGE
            and (period_start is None or contrib.timestamp >= period_start)
            and contrib.timestamp <= period_end
        ]

        if not contributions:
            return {
                "contributor_id": contributor_id,
                "total_earnings": 0.0,
                "total_contributions": 0,
                "knowledge_sources": [],
                "capsules_contributed_to": [],
            }

        # Calculate total earnings
        total_earnings = sum(
            contrib.calculate_base_value() for contrib in contributions
        )

        # Get unique knowledge sources
        knowledge_sources = list(
            set(
                contrib.metadata.get("source_id")
                for contrib in contributions
                if contrib.metadata.get("source_id")
            )
        )

        # Get unique capsules
        capsules = list(set(contrib.capsule_id for contrib in contributions))

        return {
            "contributor_id": contributor_id,
            "total_earnings": float(total_earnings),
            "total_contributions": len(contributions),
            "knowledge_sources": knowledge_sources,
            "capsules_contributed_to": capsules,
            "earnings_breakdown": [
                {
                    "contribution_id": contrib.contribution_id,
                    "capsule_id": contrib.capsule_id,
                    "timestamp": contrib.timestamp.isoformat(),
                    "earnings": float(contrib.calculate_base_value()),
                    "source_title": contrib.metadata.get("source_title", "Unknown"),
                    "source_type": contrib.metadata.get("source_type", "Unknown"),
                }
                for contrib in contributions
            ],
        }

    async def get_system_ancestral_stats(self) -> Dict:
        """Get system-wide ancestral knowledge statistics"""

        # Get all ancestral contributions
        ancestral_contributions = [
            contrib
            for contrib in self.fcde_engine.contributions.values()
            if contrib.contribution_type == ContributionType.ANCESTRAL_KNOWLEDGE
        ]

        if not ancestral_contributions:
            return {
                "total_ancestral_contributions": 0,
                "total_ancestral_value": 0.0,
                "unique_contributors": 0,
                "unique_knowledge_sources": 0,
                "capsules_with_ancestral_attribution": 0,
            }

        # Calculate statistics
        total_value = sum(
            contrib.calculate_base_value() for contrib in ancestral_contributions
        )
        unique_contributors = len(
            set(contrib.contributor_id for contrib in ancestral_contributions)
        )
        unique_sources = len(
            set(
                contrib.metadata.get("source_id")
                for contrib in ancestral_contributions
                if contrib.metadata.get("source_id")
            )
        )
        unique_capsules = len(
            set(contrib.capsule_id for contrib in ancestral_contributions)
        )

        return {
            "total_ancestral_contributions": len(ancestral_contributions),
            "total_ancestral_value": float(total_value),
            "unique_contributors": unique_contributors,
            "unique_knowledge_sources": unique_sources,
            "capsules_with_ancestral_attribution": unique_capsules,
            "average_contribution_value": float(total_value)
            / len(ancestral_contributions),
            "akc_system_stats": await self.akc_system.get_system_stats(),
        }
