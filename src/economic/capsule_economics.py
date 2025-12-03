"""
Integration between UATP Capsule Engine and FCDE Economic System.
Provides economic attribution for capsule creation and usage.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from src.audit.events import audit_emitter
from src.capsule_schema import AnyCapsule, CapsuleStatus, CapsuleType
from src.economic.fcde_engine import (
    DEFAULT_QUALITY_SCORES,
    ContributionType,
    fcde_engine,
)

logger = logging.getLogger(__name__)


class CapsuleEconomics:
    """Manages economic aspects of capsule lifecycle."""

    def __init__(self):
        self.capsule_value_cache = {}
        self.usage_tracking = {}

    def register_capsule_creation(self, capsule: AnyCapsule, creator_id: str) -> str:
        """Register economic contribution for capsule creation."""

        # Determine contribution type based on capsule type
        contribution_type = self._map_capsule_type_to_contribution(capsule.capsule_type)

        # Calculate quality score based on capsule content
        quality_score = self._calculate_capsule_quality(capsule)

        # Register contribution with FCDE
        contribution_id = fcde_engine.register_contribution(
            capsule_id=capsule.capsule_id,
            contributor_id=creator_id,
            contribution_type=contribution_type,
            quality_score=quality_score,
            metadata={
                "capsule_type": capsule.capsule_type,
                "capsule_version": capsule.version,
                "creation_timestamp": capsule.timestamp.isoformat(),
                "status": capsule.status,
            },
        )

        # Cache initial value
        self.capsule_value_cache[capsule.capsule_id] = {
            "initial_value": float(quality_score),
            "current_value": float(quality_score),
            "usage_count": 0,
            "last_updated": datetime.now(timezone.utc),
        }

        # Emit audit event
        audit_emitter.emit(
            self._create_economic_audit_event(
                "capsule_creation_registered",
                capsule.capsule_id,
                creator_id,
                {
                    "contribution_id": contribution_id,
                    "contribution_type": contribution_type.value,
                    "quality_score": float(quality_score),
                },
            )
        )

        logger.info(f"Registered capsule creation economics: {contribution_id}")
        return contribution_id

    def record_capsule_usage(
        self,
        capsule_id: str,
        user_id: str,
        usage_type: str = "access",
        usage_value: Decimal = Decimal("1.0"),
    ):
        """Record economic value from capsule usage."""

        # Record usage with FCDE
        fcde_engine.record_capsule_usage(capsule_id, usage_value)

        # Update local tracking
        if capsule_id not in self.usage_tracking:
            self.usage_tracking[capsule_id] = {
                "total_usage": 0,
                "unique_users": set(),
                "usage_types": {},
                "last_accessed": None,
            }

        tracking = self.usage_tracking[capsule_id]
        tracking["total_usage"] += 1
        tracking["unique_users"].add(user_id)
        tracking["last_accessed"] = datetime.now(timezone.utc)

        if usage_type not in tracking["usage_types"]:
            tracking["usage_types"][usage_type] = 0
        tracking["usage_types"][usage_type] += 1

        # Update cached value
        if capsule_id in self.capsule_value_cache:
            cache_entry = self.capsule_value_cache[capsule_id]
            cache_entry["usage_count"] += 1
            cache_entry["current_value"] = float(
                Decimal(str(cache_entry["initial_value"]))
                * (1 + Decimal(str(cache_entry["usage_count"])) * Decimal("0.1"))
            )
            cache_entry["last_updated"] = datetime.now(timezone.utc)

        # Emit audit event
        audit_emitter.emit(
            self._create_economic_audit_event(
                "capsule_usage_recorded",
                capsule_id,
                user_id,
                {
                    "usage_type": usage_type,
                    "usage_value": float(usage_value),
                    "total_usage": tracking["total_usage"],
                },
            )
        )

        logger.info(f"Recorded capsule usage: {capsule_id} by {user_id}")

    def register_capsule_verification(
        self, capsule_id: str, verifier_id: str, verification_result: bool
    ):
        """Register economic contribution for capsule verification."""

        # Only reward successful verifications
        if verification_result:
            quality_score = DEFAULT_QUALITY_SCORES[
                ContributionType.CAPSULE_VERIFICATION
            ]

            contribution_id = fcde_engine.register_contribution(
                capsule_id=capsule_id,
                contributor_id=verifier_id,
                contribution_type=ContributionType.CAPSULE_VERIFICATION,
                quality_score=quality_score,
                metadata={
                    "verification_result": verification_result,
                    "verification_timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            # Emit audit event
            audit_emitter.emit(
                self._create_economic_audit_event(
                    "capsule_verification_registered",
                    capsule_id,
                    verifier_id,
                    {
                        "contribution_id": contribution_id,
                        "verification_result": verification_result,
                        "quality_score": float(quality_score),
                    },
                )
            )

            logger.info(f"Registered capsule verification economics: {contribution_id}")
            return contribution_id

        return None

    def calculate_capsule_roi(self, capsule_id: str) -> Dict[str, Any]:
        """Calculate return on investment for a capsule."""

        if capsule_id not in self.capsule_value_cache:
            return {"error": "Capsule not found in economic tracking"}

        cache_entry = self.capsule_value_cache[capsule_id]
        usage_data = self.usage_tracking.get(capsule_id, {})

        initial_value = cache_entry["initial_value"]
        current_value = cache_entry["current_value"]
        usage_count = cache_entry["usage_count"]

        # Calculate ROI metrics
        value_growth = current_value - initial_value
        roi_percentage = (
            (value_growth / initial_value) * 100 if initial_value > 0 else 0
        )

        # Calculate network effects
        unique_users = len(usage_data.get("unique_users", set()))
        network_multiplier = 1 + (unique_users * 0.1)  # 10% bonus per unique user

        # Calculate time-based metrics
        days_since_creation = (
            datetime.now(timezone.utc) - cache_entry["last_updated"]
        ).days
        daily_usage_rate = usage_count / max(days_since_creation, 1)

        return {
            "capsule_id": capsule_id,
            "initial_value": initial_value,
            "current_value": current_value,
            "value_growth": value_growth,
            "roi_percentage": roi_percentage,
            "total_usage": usage_count,
            "unique_users": unique_users,
            "network_multiplier": network_multiplier,
            "daily_usage_rate": daily_usage_rate,
            "days_since_creation": days_since_creation,
            "last_updated": cache_entry["last_updated"].isoformat(),
        }

    def get_creator_economic_summary(self, creator_id: str) -> Dict[str, Any]:
        """Get economic summary for a creator."""

        fcde_analytics = fcde_engine.get_creator_analytics(creator_id)

        if "error" in fcde_analytics:
            return fcde_analytics

        # Calculate additional metrics
        capsule_roi_data = []
        for contribution in fcde_analytics.get("recent_contributions", []):
            capsule_id = contribution["capsule_id"]
            roi_data = self.calculate_capsule_roi(capsule_id)
            if "error" not in roi_data:
                capsule_roi_data.append(roi_data)

        # Calculate average ROI
        if capsule_roi_data:
            avg_roi = sum(roi["roi_percentage"] for roi in capsule_roi_data) / len(
                capsule_roi_data
            )
            avg_daily_usage = sum(
                roi["daily_usage_rate"] for roi in capsule_roi_data
            ) / len(capsule_roi_data)
        else:
            avg_roi = 0
            avg_daily_usage = 0

        return {
            **fcde_analytics,
            "average_roi_percentage": avg_roi,
            "average_daily_usage": avg_daily_usage,
            "capsule_count": len(capsule_roi_data),
            "high_performing_capsules": [
                roi for roi in capsule_roi_data if roi["roi_percentage"] > 50
            ],
        }

    def process_periodic_dividends(self) -> str:
        """Process periodic dividend distribution."""

        # Calculate treasury contribution based on system usage
        total_system_usage = sum(
            data["total_usage"] for data in self.usage_tracking.values()
        )

        # Base dividend pool + usage-based bonus
        base_dividend = fcde_engine.system_treasury * fcde_engine.dividend_rate
        usage_bonus = Decimal(str(total_system_usage)) * Decimal("0.1")
        total_dividend_pool = base_dividend + usage_bonus

        # Process dividend distribution
        pool_id = fcde_engine.process_dividend_distribution(total_dividend_pool)

        # Emit audit event
        audit_emitter.emit(
            self._create_economic_audit_event(
                "dividend_distribution_processed",
                None,
                "system",
                {
                    "pool_id": pool_id,
                    "total_dividend_pool": float(total_dividend_pool),
                    "base_dividend": float(base_dividend),
                    "usage_bonus": float(usage_bonus),
                    "total_system_usage": total_system_usage,
                },
            )
        )

        logger.info(f"Processed periodic dividends: {pool_id}")
        return pool_id

    def _map_capsule_type_to_contribution(
        self, capsule_type: CapsuleType
    ) -> ContributionType:
        """Map capsule type to contribution type."""

        mapping = {
            CapsuleType.REASONING_TRACE: ContributionType.REASONING_QUALITY,
            CapsuleType.ECONOMIC_TRANSACTION: ContributionType.SYSTEM_MAINTENANCE,
            CapsuleType.GOVERNANCE_VOTE: ContributionType.GOVERNANCE_PARTICIPATION,
            CapsuleType.ETHICS_TRIGGER: ContributionType.SYSTEM_MAINTENANCE,
            CapsuleType.POST_QUANTUM_SIGNATURE: ContributionType.SYSTEM_MAINTENANCE,
            CapsuleType.CONSENT: ContributionType.GOVERNANCE_PARTICIPATION,
            CapsuleType.REMIX: ContributionType.KNOWLEDGE_PROVISION,
            CapsuleType.TRUST_RENEWAL: ContributionType.SYSTEM_MAINTENANCE,
            CapsuleType.SIMULATED_MALICE: ContributionType.SYSTEM_MAINTENANCE,
            CapsuleType.IMPLICIT_CONSENT: ContributionType.GOVERNANCE_PARTICIPATION,
            CapsuleType.TEMPORAL_JUSTICE: ContributionType.GOVERNANCE_PARTICIPATION,
            CapsuleType.UNCERTAINTY: ContributionType.REASONING_QUALITY,
            CapsuleType.CONFLICT_RESOLUTION: ContributionType.REASONING_QUALITY,
            CapsuleType.PERSPECTIVE: ContributionType.KNOWLEDGE_PROVISION,
            CapsuleType.FEEDBACK_ASSIMILATION: ContributionType.SYSTEM_MAINTENANCE,
            CapsuleType.KNOWLEDGE_EXPIRY: ContributionType.SYSTEM_MAINTENANCE,
            CapsuleType.EMOTIONAL_LOAD: ContributionType.REASONING_QUALITY,
            CapsuleType.MANIPULATION_ATTEMPT: ContributionType.SYSTEM_MAINTENANCE,
            CapsuleType.COMPUTE_FOOTPRINT: ContributionType.SYSTEM_MAINTENANCE,
            CapsuleType.HAND_OFF: ContributionType.SYSTEM_MAINTENANCE,
            CapsuleType.RETIREMENT: ContributionType.SYSTEM_MAINTENANCE,
            # Advanced Rights & Evolution capsule types
            CapsuleType.CLONING_RIGHTS: ContributionType.KNOWLEDGE_PROVISION,
            CapsuleType.EVOLUTION: ContributionType.REASONING_QUALITY,
            CapsuleType.DIVIDEND_BOND: ContributionType.SYSTEM_MAINTENANCE,
            CapsuleType.CITIZENSHIP: ContributionType.GOVERNANCE_PARTICIPATION,
        }

        return mapping.get(capsule_type, ContributionType.CAPSULE_CREATION)

    def _calculate_capsule_quality(self, capsule: AnyCapsule) -> Decimal:
        """Calculate quality score for a capsule."""

        base_score = Decimal("1.0")

        # Capsule type-specific quality factors
        if capsule.capsule_type == CapsuleType.REASONING_TRACE:
            if hasattr(capsule, "reasoning_trace") and capsule.reasoning_trace:
                step_count = len(capsule.reasoning_trace.reasoning_steps)
                # Bonus for more detailed reasoning
                base_score += Decimal(str(step_count)) * Decimal("0.1")

        elif capsule.capsule_type == CapsuleType.KNOWLEDGE_ASSERTION:
            # Knowledge assertions get higher base value
            base_score = Decimal("1.5")

        elif capsule.capsule_type == CapsuleType.UNCERTAINTY:
            if hasattr(capsule, "uncertainty") and capsule.uncertainty:
                # Bonus for explicit uncertainty quantification
                confidence = getattr(capsule.uncertainty, "confidence_score", 0.5)
                base_score += Decimal(str(confidence)) * Decimal("0.5")

        # Version-based quality bonus
        if capsule.version == "7.0":
            base_score *= Decimal("1.1")  # 10% bonus for latest version

        # Status-based adjustments
        if capsule.status == CapsuleStatus.SEALED:
            base_score *= Decimal("1.2")  # 20% bonus for sealed capsules
        elif capsule.status == CapsuleStatus.DRAFT:
            base_score *= Decimal("0.8")  # 20% penalty for draft capsules

        # Cap quality score
        return min(base_score, Decimal("3.0"))

    def _create_economic_audit_event(
        self,
        event_type: str,
        capsule_id: Optional[str],
        agent_id: str,
        metadata: Dict[str, Any],
    ):
        """Create economic audit event."""

        from src.audit.events import AuditEvent

        return AuditEvent(
            event_type=f"economic_{event_type}",
            capsule_id=capsule_id,
            agent_id=agent_id,
            metadata={"category": "economics", "fcde_engine": "active", **metadata},
        )


# Global capsule economics instance
capsule_economics = CapsuleEconomics()
