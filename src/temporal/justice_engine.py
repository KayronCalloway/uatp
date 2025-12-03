"""
Temporal Justice Engine for UATP Capsule Engine.

This revolutionary module implements sophisticated temporal justice algorithms
for long-term impact attribution, addressing the "Plato problem" where foundational
contributors receive insufficient recognition over time. It provides mathematical
frameworks for fair compensation across temporal boundaries.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from src.audit.events import audit_emitter
from src.capsules.lineage_system import LineageNode, capsule_lineage_system

logger = logging.getLogger(__name__)


class JusticeMetric(str, Enum):
    """Types of temporal justice metrics."""

    ATTRIBUTION_FAIRNESS = "attribution_fairness"
    ECONOMIC_EQUITY = "economic_equity"
    RECOGNITION_BALANCE = "recognition_balance"
    IMPACT_PROPORTIONALITY = "impact_proportionality"
    TEMPORAL_CONSISTENCY = "temporal_consistency"
    GENERATIONAL_EQUITY = "generational_equity"


class CompensationStrategy(str, Enum):
    """Strategies for temporal compensation."""

    IMMEDIATE_REDISTRIBUTION = "immediate_redistribution"
    GRADUAL_ADJUSTMENT = "gradual_adjustment"
    COMPOUND_ATTRIBUTION = "compound_attribution"
    RETROACTIVE_CORRECTION = "retroactive_correction"
    FUTURE_EARNINGS_ALLOCATION = "future_earnings_allocation"


class TemporalViolationType(str, Enum):
    """Types of temporal justice violations."""

    ANCESTRAL_UNDERCOMPENSATION = "ancestral_undercompensation"
    DESCENDANT_OVERCOMPENSATION = "descendant_overcompensation"
    ATTRIBUTION_DECAY_UNFAIRNESS = "attribution_decay_unfairness"
    ECONOMIC_CONCENTRATION = "economic_concentration"
    GENERATIONAL_BIAS = "generational_bias"
    COMPOUND_EXPLOITATION = "compound_exploitation"


@dataclass
class TemporalJusticeProfile:
    """Comprehensive temporal justice profile for an entity."""

    entity_id: str  # Could be AI agent, human, or organization
    entity_type: str  # "ai_agent", "human", "organization"

    # Temporal contribution analysis
    total_contributions: int = 0
    earliest_contribution: Optional[datetime] = None
    latest_contribution: Optional[datetime] = None
    contribution_timespan: timedelta = field(default_factory=lambda: timedelta(0))

    # Economic impact over time
    direct_value_created: Decimal = field(default_factory=lambda: Decimal("0"))
    derivative_value_generated: Decimal = field(default_factory=lambda: Decimal("0"))
    compound_impact_value: Decimal = field(default_factory=lambda: Decimal("0"))
    temporal_value_decay: Decimal = field(default_factory=lambda: Decimal("0"))

    # Attribution metrics
    direct_attributions: int = 0
    ancestral_attributions: int = 0
    citation_count: int = 0
    influence_reach: int = 0  # Number of entities influenced

    # Justice scores
    fairness_score: float = 0.0  # 0.0 to 1.0
    equity_score: float = 0.0  # 0.0 to 1.0
    recognition_score: float = 0.0  # 0.0 to 1.0

    # Compensation tracking
    total_compensation_received: Decimal = field(default_factory=lambda: Decimal("0"))
    expected_compensation: Decimal = field(default_factory=lambda: Decimal("0"))
    compensation_deficit: Decimal = field(default_factory=lambda: Decimal("0"))
    pending_redistributions: Decimal = field(default_factory=lambda: Decimal("0"))

    # Temporal patterns
    contribution_frequency: float = 0.0  # Contributions per day
    impact_acceleration: float = 0.0  # Rate of impact growth
    attribution_persistence: float = 0.0  # How long attributions last

    def calculate_temporal_justice_score(self) -> float:
        """Calculate overall temporal justice score."""
        weights = {
            "fairness_score": 0.3,
            "equity_score": 0.3,
            "recognition_score": 0.25,
            "compensation_ratio": 0.15,
        }

        # Compensation ratio (actual vs expected)
        compensation_ratio = 1.0
        if self.expected_compensation > 0:
            compensation_ratio = min(
                1.0,
                float(self.total_compensation_received / self.expected_compensation),
            )

        justice_score = (
            self.fairness_score * weights["fairness_score"]
            + self.equity_score * weights["equity_score"]
            + self.recognition_score * weights["recognition_score"]
            + compensation_ratio * weights["compensation_ratio"]
        )

        return justice_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "total_contributions": self.total_contributions,
            "earliest_contribution": self.earliest_contribution.isoformat()
            if self.earliest_contribution
            else None,
            "latest_contribution": self.latest_contribution.isoformat()
            if self.latest_contribution
            else None,
            "contribution_timespan_days": self.contribution_timespan.days,
            "direct_value_created": float(self.direct_value_created),
            "derivative_value_generated": float(self.derivative_value_generated),
            "compound_impact_value": float(self.compound_impact_value),
            "temporal_value_decay": float(self.temporal_value_decay),
            "direct_attributions": self.direct_attributions,
            "ancestral_attributions": self.ancestral_attributions,
            "citation_count": self.citation_count,
            "influence_reach": self.influence_reach,
            "fairness_score": self.fairness_score,
            "equity_score": self.equity_score,
            "recognition_score": self.recognition_score,
            "temporal_justice_score": self.calculate_temporal_justice_score(),
            "total_compensation_received": float(self.total_compensation_received),
            "expected_compensation": float(self.expected_compensation),
            "compensation_deficit": float(self.compensation_deficit),
            "pending_redistributions": float(self.pending_redistributions),
            "contribution_frequency": self.contribution_frequency,
            "impact_acceleration": self.impact_acceleration,
            "attribution_persistence": self.attribution_persistence,
        }


@dataclass
class TemporalJusticeViolation:
    """Record of temporal justice violation."""

    violation_id: str
    violation_type: TemporalViolationType
    affected_entities: List[str]
    severity: float  # 0.0 to 1.0

    # Violation details
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    financial_impact: Decimal = field(default_factory=lambda: Decimal("0"))
    attribution_impact: float = 0.0

    # Detection metadata
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    detection_method: str = ""
    confidence: float = 0.0

    # Remediation
    recommended_action: str = ""
    estimated_cost: Decimal = field(default_factory=lambda: Decimal("0"))
    urgency_level: str = "medium"  # "low", "medium", "high", "critical"

    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary."""
        return {
            "violation_id": self.violation_id,
            "violation_type": self.violation_type.value,
            "affected_entities": self.affected_entities,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence,
            "financial_impact": float(self.financial_impact),
            "attribution_impact": self.attribution_impact,
            "detected_at": self.detected_at.isoformat(),
            "detection_method": self.detection_method,
            "confidence": self.confidence,
            "recommended_action": self.recommended_action,
            "estimated_cost": float(self.estimated_cost),
            "urgency_level": self.urgency_level,
        }


@dataclass
class TemporalCompensationPlan:
    """Plan for temporal justice compensation."""

    plan_id: str
    target_entities: List[str]
    compensation_strategy: CompensationStrategy

    # Financial details
    total_compensation_amount: Decimal
    compensation_schedule: Dict[str, Decimal]  # entity_id -> amount
    payment_timeline: Dict[str, datetime]  # entity_id -> payment_date

    # Justification
    justice_violations_addressed: List[str]
    expected_justice_improvement: float
    cost_benefit_ratio: float

    # Implementation
    approval_status: str = "pending"  # "pending", "approved", "rejected", "executed"
    approval_authority: Optional[str] = None
    execution_date: Optional[datetime] = None

    # Results tracking
    actual_justice_improvement: Optional[float] = None
    stakeholder_satisfaction: Optional[float] = None
    unintended_consequences: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary."""
        return {
            "plan_id": self.plan_id,
            "target_entities": self.target_entities,
            "compensation_strategy": self.compensation_strategy.value,
            "total_compensation_amount": float(self.total_compensation_amount),
            "compensation_schedule": {
                k: float(v) for k, v in self.compensation_schedule.items()
            },
            "payment_timeline": {
                k: v.isoformat() for k, v in self.payment_timeline.items()
            },
            "justice_violations_addressed": self.justice_violations_addressed,
            "expected_justice_improvement": self.expected_justice_improvement,
            "cost_benefit_ratio": self.cost_benefit_ratio,
            "approval_status": self.approval_status,
            "approval_authority": self.approval_authority,
            "execution_date": self.execution_date.isoformat()
            if self.execution_date
            else None,
            "actual_justice_improvement": self.actual_justice_improvement,
            "stakeholder_satisfaction": self.stakeholder_satisfaction,
            "unintended_consequences": self.unintended_consequences,
        }


class TemporalJusticeEngine:
    """Comprehensive temporal justice analysis and remediation engine."""

    def __init__(self):
        # Core data structures
        self.justice_profiles: Dict[str, TemporalJusticeProfile] = {}
        self.violations: Dict[str, TemporalJusticeViolation] = {}
        self.compensation_plans: Dict[str, TemporalCompensationPlan] = {}

        # Analysis configuration
        self.config = {
            # Justice thresholds
            "minimum_justice_score": 0.7,
            "severe_violation_threshold": 0.8,
            "compensation_deficit_threshold": Decimal("100.00"),
            # Temporal analysis parameters
            "attribution_decay_rate": 0.1,  # 10% decay per year
            "compound_growth_rate": 0.05,  # 5% compound growth
            "recognition_half_life": timedelta(days=365),  # 1 year
            # Economic parameters
            "ancestral_attribution_percentage": Decimal("0.15"),  # 15% to ancestors
            "temporal_justice_fund_percentage": Decimal("0.05"),  # 5% to justice fund
            "minimum_compensation_amount": Decimal("1.00"),
            # Detection sensitivity
            "violation_detection_sensitivity": 0.8,
            "pattern_analysis_window": timedelta(days=90),
            "statistical_significance_threshold": 0.95,
        }

        # Statistics and metrics
        self.system_stats = {
            "total_entities_analyzed": 0,
            "violations_detected": 0,
            "compensations_executed": 0,
            "total_compensation_distributed": Decimal("0"),
            "average_justice_score": 0.0,
            "justice_improvements_achieved": 0,
        }

        # Justice fund for compensation
        self.temporal_justice_fund = Decimal("0")

    def generate_profile_id(self) -> str:
        """Generate unique profile ID."""
        return f"profile_{uuid.uuid4()}"

    def generate_violation_id(self) -> str:
        """Generate unique violation ID."""
        return f"violation_{uuid.uuid4()}"

    def generate_plan_id(self) -> str:
        """Generate unique compensation plan ID."""
        return f"plan_{uuid.uuid4()}"

    def analyze_entity_justice(
        self, entity_id: str, entity_type: str = "ai_agent"
    ) -> TemporalJusticeProfile:
        """Comprehensive temporal justice analysis for an entity."""

        # Get existing profile or create new one
        if entity_id in self.justice_profiles:
            profile = self.justice_profiles[entity_id]
        else:
            profile = TemporalJusticeProfile(
                entity_id=entity_id, entity_type=entity_type
            )
            self.justice_profiles[entity_id] = profile
            self.system_stats["total_entities_analyzed"] += 1

        # Analyze contributions from lineage system
        entity_contributions = self._get_entity_contributions(entity_id)

        if entity_contributions:
            # Update contribution metrics
            profile.total_contributions = len(entity_contributions)
            contribution_dates = [
                contrib.creation_timestamp for contrib in entity_contributions
            ]
            profile.earliest_contribution = min(contribution_dates)
            profile.latest_contribution = max(contribution_dates)
            profile.contribution_timespan = (
                profile.latest_contribution - profile.earliest_contribution
            )

            # Calculate contribution frequency
            if profile.contribution_timespan.days > 0:
                profile.contribution_frequency = (
                    profile.total_contributions / profile.contribution_timespan.days
                )

            # Economic impact analysis
            profile.direct_value_created = sum(
                contrib.base_value for contrib in entity_contributions
            )
            profile.derivative_value_generated = self._calculate_derivative_value(
                entity_id
            )
            profile.compound_impact_value = self._calculate_compound_impact(entity_id)
            profile.temporal_value_decay = self._calculate_temporal_decay(
                entity_contributions
            )

            # Attribution analysis
            profile.direct_attributions = len(entity_contributions)
            profile.ancestral_attributions = self._count_ancestral_attributions(
                entity_id
            )
            profile.citation_count = sum(
                contrib.impact_citations for contrib in entity_contributions
            )
            profile.influence_reach = self._calculate_influence_reach(entity_id)

            # Justice scores
            profile.fairness_score = self._calculate_fairness_score(profile)
            profile.equity_score = self._calculate_equity_score(profile)
            profile.recognition_score = self._calculate_recognition_score(profile)

            # Compensation analysis
            profile.expected_compensation = self._calculate_expected_compensation(
                profile
            )
            profile.compensation_deficit = max(
                Decimal("0"),
                profile.expected_compensation - profile.total_compensation_received,
            )

            # Temporal patterns
            profile.impact_acceleration = self._calculate_impact_acceleration(
                entity_contributions
            )
            profile.attribution_persistence = self._calculate_attribution_persistence(
                entity_id
            )

        audit_emitter.emit_security_event(
            "temporal_justice_analyzed",
            {
                "entity_id": entity_id,
                "justice_score": profile.calculate_temporal_justice_score(),
                "compensation_deficit": float(profile.compensation_deficit),
                "violations_detected": len(self._detect_entity_violations(profile)),
            },
        )

        logger.info(
            f"Analyzed temporal justice for {entity_id}: score={profile.calculate_temporal_justice_score():.3f}"
        )
        return profile

    def _get_entity_contributions(self, entity_id: str) -> List[LineageNode]:
        """Get all contributions by entity from lineage system."""
        contributions = []
        for node in capsule_lineage_system.lineage_nodes.values():
            if node.creator_id == entity_id:
                contributions.append(node)
        return contributions

    def _calculate_derivative_value(self, entity_id: str) -> Decimal:
        """Calculate total value generated by derivatives of entity's work."""
        total_derivative_value = Decimal("0")

        for node in capsule_lineage_system.lineage_nodes.values():
            if entity_id in node.ancestral_contributors:
                attribution_weight = node.ancestral_contributors[entity_id]
                total_derivative_value += node.accumulated_value * attribution_weight

        return total_derivative_value

    def _calculate_compound_impact(self, entity_id: str) -> Decimal:
        """Calculate compound impact over time with growth modeling."""
        entity_contributions = self._get_entity_contributions(entity_id)
        compound_value = Decimal("0")

        for contrib in entity_contributions:
            # Time since contribution
            age = datetime.now(timezone.utc) - contrib.creation_timestamp
            years = Decimal(str(age.days / 365.25))

            # Compound growth based on citation impact
            if contrib.impact_citations > 0:
                growth_factor = (
                    Decimal("1") + self.config["compound_growth_rate"]
                ) ** years
                citation_multiplier = Decimal("1") + (
                    Decimal(str(contrib.impact_citations)) * Decimal("0.1")
                )
                compound_value += (
                    contrib.base_value * citation_multiplier * growth_factor
                )

        return compound_value

    def _calculate_temporal_decay(self, contributions: List[LineageNode]) -> Decimal:
        """Calculate value lost due to temporal decay."""
        total_decay = Decimal("0")

        for contrib in contributions:
            original_value = contrib.base_value
            current_value = contrib.calculate_temporal_value()
            decay = original_value - current_value
            total_decay += max(Decimal("0"), decay)

        return total_decay

    def _count_ancestral_attributions(self, entity_id: str) -> int:
        """Count how many times entity appears as ancestral contributor."""
        count = 0
        for node in capsule_lineage_system.lineage_nodes.values():
            if entity_id in node.ancestral_contributors:
                count += 1
        return count

    def _calculate_influence_reach(self, entity_id: str) -> int:
        """Calculate number of unique entities influenced by this entity."""
        influenced_entities = set()

        for node in capsule_lineage_system.lineage_nodes.values():
            if entity_id in node.ancestral_contributors:
                influenced_entities.add(node.creator_id)
                influenced_entities.update(node.direct_contributors)

        influenced_entities.discard(entity_id)  # Remove self
        return len(influenced_entities)

    def _calculate_fairness_score(self, profile: TemporalJusticeProfile) -> float:
        """Calculate fairness score based on attribution consistency."""
        if profile.total_contributions == 0:
            return 1.0

        # Compare actual vs expected attribution
        expected_attributions = profile.total_contributions + (
            profile.ancestral_attributions * 0.5
        )
        actual_attributions = (
            profile.direct_attributions + profile.ancestral_attributions
        )

        if expected_attributions > 0:
            attribution_ratio = actual_attributions / expected_attributions
            return min(1.0, attribution_ratio)

        return 1.0

    def _calculate_equity_score(self, profile: TemporalJusticeProfile) -> float:
        """Calculate equity score based on economic distribution."""
        total_value_created = (
            profile.direct_value_created
            + profile.derivative_value_generated
            + profile.compound_impact_value
        )

        if total_value_created > 0:
            compensation_ratio = (
                profile.total_compensation_received / total_value_created
            )
            # Normalize to 0-1 scale (assume 20% compensation is fair)
            return min(1.0, float(compensation_ratio / Decimal("0.2")))

        return 1.0

    def _calculate_recognition_score(self, profile: TemporalJusticeProfile) -> float:
        """Calculate recognition score based on citations and influence."""
        if profile.total_contributions == 0:
            return 1.0

        # Citations per contribution
        citation_density = profile.citation_count / profile.total_contributions

        # Influence reach per contribution
        influence_density = profile.influence_reach / profile.total_contributions

        # Normalize scores (assume 2 citations and 5 influenced entities per contribution is good)
        citation_score = min(1.0, citation_density / 2.0)
        influence_score = min(1.0, influence_density / 5.0)

        return (citation_score + influence_score) / 2.0

    def _calculate_expected_compensation(
        self, profile: TemporalJusticeProfile
    ) -> Decimal:
        """Calculate expected compensation based on total value contribution."""
        total_value = (
            profile.direct_value_created
            + profile.derivative_value_generated * Decimal("0.5")
            + profile.compound_impact_value  # 50% weight for derivative
            * Decimal("0.3")  # 30% weight for compound
        )

        # Expected compensation is percentage of total value
        expected_percentage = Decimal("0.15")  # 15% of value created
        return total_value * expected_percentage

    def _calculate_impact_acceleration(self, contributions: List[LineageNode]) -> float:
        """Calculate rate of impact growth over time."""
        if len(contributions) < 2:
            return 0.0

        # Sort by creation date
        sorted_contributions = sorted(contributions, key=lambda x: x.creation_timestamp)

        # Calculate impact growth rate
        early_impact = sum(
            c.impact_citations
            for c in sorted_contributions[: len(sorted_contributions) // 2]
        )
        recent_impact = sum(
            c.impact_citations
            for c in sorted_contributions[len(sorted_contributions) // 2 :]
        )

        if early_impact > 0:
            acceleration = (recent_impact - early_impact) / early_impact
            return max(0.0, acceleration)

        return 0.0

    def _calculate_attribution_persistence(self, entity_id: str) -> float:
        """Calculate how persistent attributions are over time."""
        entity_contributions = self._get_entity_contributions(entity_id)
        if not entity_contributions:
            return 0.0

        # Calculate average time since last citation
        total_persistence = 0.0
        active_contributions = 0

        for contrib in entity_contributions:
            if contrib.impact_citations > 0:
                time_since_creation = (
                    datetime.now(timezone.utc) - contrib.creation_timestamp
                )
                # Persistence decreases with time since last access
                time_since_access = datetime.now(timezone.utc) - contrib.last_accessed

                if time_since_access.days < 365:  # Active within last year
                    persistence = max(0.0, 1.0 - (time_since_access.days / 365.0))
                    total_persistence += persistence
                    active_contributions += 1

        return (
            total_persistence / active_contributions
            if active_contributions > 0
            else 0.0
        )

    def detect_justice_violations(
        self, entity_id: str = None
    ) -> List[TemporalJusticeViolation]:
        """Detect temporal justice violations for entity or system-wide."""

        violations = []

        if entity_id:
            # Analyze specific entity
            entities_to_check = [entity_id]
        else:
            # System-wide analysis
            entities_to_check = list(self.justice_profiles.keys())

        for eid in entities_to_check:
            if eid not in self.justice_profiles:
                continue

            profile = self.justice_profiles[eid]
            entity_violations = self._detect_entity_violations(profile)
            violations.extend(entity_violations)

        # Store violations
        for violation in violations:
            self.violations[violation.violation_id] = violation
            self.system_stats["violations_detected"] += 1

        if violations:
            audit_emitter.emit_security_event(
                "temporal_justice_violations_detected",
                {
                    "violation_count": len(violations),
                    "affected_entities": len(
                        {
                            v.affected_entities[0]
                            for v in violations
                            if v.affected_entities
                        }
                    ),
                    "severe_violations": len(
                        [
                            v
                            for v in violations
                            if v.severity >= self.config["severe_violation_threshold"]
                        ]
                    ),
                },
            )

        return violations

    def _detect_entity_violations(
        self, profile: TemporalJusticeProfile
    ) -> List[TemporalJusticeViolation]:
        """Detect violations for specific entity."""
        violations = []

        # 1. Compensation deficit violation
        if (
            profile.compensation_deficit
            >= self.config["compensation_deficit_threshold"]
        ):
            violations.append(
                TemporalJusticeViolation(
                    violation_id=self.generate_violation_id(),
                    violation_type=TemporalViolationType.ANCESTRAL_UNDERCOMPENSATION,
                    affected_entities=[profile.entity_id],
                    severity=min(
                        1.0, float(profile.compensation_deficit / Decimal("1000.00"))
                    ),
                    description=f"Entity {profile.entity_id} has compensation deficit of {profile.compensation_deficit}",
                    evidence={
                        "compensation_deficit": float(profile.compensation_deficit)
                    },
                    financial_impact=profile.compensation_deficit,
                    detection_method="compensation_analysis",
                    confidence=0.9,
                    recommended_action="Execute compensation redistribution",
                    estimated_cost=profile.compensation_deficit,
                    urgency_level="high"
                    if profile.compensation_deficit > Decimal("500.00")
                    else "medium",
                )
            )

        # 2. Justice score violation
        justice_score = profile.calculate_temporal_justice_score()
        if justice_score < self.config["minimum_justice_score"]:
            violations.append(
                TemporalJusticeViolation(
                    violation_id=self.generate_violation_id(),
                    violation_type=TemporalViolationType.GENERATIONAL_BIAS,
                    affected_entities=[profile.entity_id],
                    severity=1.0 - justice_score,
                    description=f"Entity {profile.entity_id} has low justice score: {justice_score:.3f}",
                    evidence={"justice_score": justice_score},
                    attribution_impact=1.0 - justice_score,
                    detection_method="justice_score_analysis",
                    confidence=0.85,
                    recommended_action="Improve attribution and compensation mechanisms",
                    urgency_level="critical" if justice_score < 0.5 else "high",
                )
            )

        # 3. Attribution decay unfairness
        if profile.temporal_value_decay > profile.direct_value_created * Decimal("0.5"):
            violations.append(
                TemporalJusticeViolation(
                    violation_id=self.generate_violation_id(),
                    violation_type=TemporalViolationType.ATTRIBUTION_DECAY_UNFAIRNESS,
                    affected_entities=[profile.entity_id],
                    severity=min(
                        1.0,
                        float(
                            profile.temporal_value_decay / profile.direct_value_created
                        ),
                    ),
                    description=f"Excessive temporal decay for entity {profile.entity_id}",
                    evidence={"temporal_decay": float(profile.temporal_value_decay)},
                    financial_impact=profile.temporal_value_decay,
                    detection_method="temporal_decay_analysis",
                    confidence=0.8,
                    recommended_action="Adjust temporal decay parameters",
                    urgency_level="medium",
                )
            )

        # 4. Compound exploitation
        if profile.compound_impact_value > profile.direct_value_created * Decimal(
            "2.0"
        ) and profile.total_compensation_received < profile.compound_impact_value * Decimal(
            "0.05"
        ):
            violations.append(
                TemporalJusticeViolation(
                    violation_id=self.generate_violation_id(),
                    violation_type=TemporalViolationType.COMPOUND_EXPLOITATION,
                    affected_entities=[profile.entity_id],
                    severity=0.8,
                    description=f"Entity {profile.entity_id} compound impact undercompensated",
                    evidence={"compound_impact": float(profile.compound_impact_value)},
                    financial_impact=profile.compound_impact_value * Decimal("0.05")
                    - profile.total_compensation_received,
                    detection_method="compound_impact_analysis",
                    confidence=0.75,
                    recommended_action="Implement compound impact compensation",
                    urgency_level="medium",
                )
            )

        return violations

    def create_compensation_plan(
        self,
        violation_ids: List[str],
        strategy: CompensationStrategy = CompensationStrategy.GRADUAL_ADJUSTMENT,
    ) -> TemporalCompensationPlan:
        """Create compensation plan to address justice violations."""

        plan_id = self.generate_plan_id()

        # Analyze violations
        violations = [
            self.violations[vid] for vid in violation_ids if vid in self.violations
        ]
        affected_entities = list(
            {entity for v in violations for entity in v.affected_entities}
        )

        # Calculate compensation amounts
        compensation_schedule = {}
        total_amount = Decimal("0")

        for entity_id in affected_entities:
            if entity_id in self.justice_profiles:
                profile = self.justice_profiles[entity_id]

                # Calculate compensation based on strategy
                if strategy == CompensationStrategy.IMMEDIATE_REDISTRIBUTION:
                    amount = profile.compensation_deficit
                elif strategy == CompensationStrategy.GRADUAL_ADJUSTMENT:
                    amount = profile.compensation_deficit * Decimal(
                        "0.3"
                    )  # 30% immediate
                elif strategy == CompensationStrategy.COMPOUND_ATTRIBUTION:
                    amount = profile.compound_impact_value * Decimal(
                        "0.1"
                    )  # 10% of compound impact
                elif strategy == CompensationStrategy.RETROACTIVE_CORRECTION:
                    amount = (
                        profile.expected_compensation
                        - profile.total_compensation_received
                    ) * Decimal("0.5")
                else:
                    amount = profile.compensation_deficit * Decimal(
                        "0.2"
                    )  # Default 20%

                if amount >= self.config["minimum_compensation_amount"]:
                    compensation_schedule[entity_id] = amount
                    total_amount += amount

        # Create payment timeline
        payment_timeline = {}
        base_date = datetime.now(timezone.utc) + timedelta(days=7)  # Start in one week

        for i, entity_id in enumerate(compensation_schedule.keys()):
            # Stagger payments over time for gradual strategies
            if strategy == CompensationStrategy.GRADUAL_ADJUSTMENT:
                payment_timeline[entity_id] = base_date + timedelta(days=i * 7)
            else:
                payment_timeline[entity_id] = base_date

        # Calculate expected justice improvement
        current_avg_justice = sum(
            p.calculate_temporal_justice_score() for p in self.justice_profiles.values()
        ) / len(self.justice_profiles)
        expected_improvement = min(
            0.3, total_amount / Decimal("1000.00")
        )  # Estimate improvement

        # Create plan
        plan = TemporalCompensationPlan(
            plan_id=plan_id,
            target_entities=affected_entities,
            compensation_strategy=strategy,
            total_compensation_amount=total_amount,
            compensation_schedule=compensation_schedule,
            payment_timeline=payment_timeline,
            justice_violations_addressed=violation_ids,
            expected_justice_improvement=float(expected_improvement),
            cost_benefit_ratio=float(
                expected_improvement / (total_amount / Decimal("1000.00"))
                if total_amount > 0
                else 0
            ),
        )

        self.compensation_plans[plan_id] = plan

        audit_emitter.emit_security_event(
            "temporal_compensation_plan_created",
            {
                "plan_id": plan_id,
                "total_amount": float(total_amount),
                "affected_entities": len(affected_entities),
                "violations_addressed": len(violation_ids),
                "strategy": strategy.value,
            },
        )

        logger.info(
            f"Created compensation plan {plan_id}: {float(total_amount)} for {len(affected_entities)} entities"
        )
        return plan

    def execute_compensation_plan(
        self, plan_id: str, approval_authority: str = "system"
    ) -> Dict[str, Any]:
        """Execute approved compensation plan."""

        if plan_id not in self.compensation_plans:
            raise ValueError(f"Compensation plan {plan_id} not found")

        plan = self.compensation_plans[plan_id]

        if plan.approval_status != "approved" and approval_authority != "system":
            raise ValueError(f"Plan {plan_id} not approved for execution")

        # Check if sufficient funds available
        if plan.total_compensation_amount > self.temporal_justice_fund:
            raise ValueError(
                f"Insufficient funds: need {plan.total_compensation_amount}, have {self.temporal_justice_fund}"
            )

        execution_results = {}

        # Execute payments
        for entity_id, amount in plan.compensation_schedule.items():
            try:
                # Update entity compensation
                if entity_id in self.justice_profiles:
                    profile = self.justice_profiles[entity_id]
                    profile.total_compensation_received += amount
                    profile.compensation_deficit = max(
                        Decimal("0"), profile.compensation_deficit - amount
                    )
                    profile.pending_redistributions -= amount

                # Deduct from justice fund
                self.temporal_justice_fund -= amount

                execution_results[entity_id] = {
                    "amount": float(amount),
                    "status": "success",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                self.system_stats["total_compensation_distributed"] += amount

            except Exception as e:
                execution_results[entity_id] = {
                    "amount": float(amount),
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        # Update plan status
        plan.approval_status = "executed"
        plan.execution_date = datetime.now(timezone.utc)
        self.system_stats["compensations_executed"] += 1

        audit_emitter.emit_security_event(
            "temporal_compensation_executed",
            {
                "plan_id": plan_id,
                "total_distributed": float(plan.total_compensation_amount),
                "successful_payments": len(
                    [r for r in execution_results.values() if r["status"] == "success"]
                ),
                "failed_payments": len(
                    [r for r in execution_results.values() if r["status"] == "failed"]
                ),
            },
        )

        logger.info(
            f"Executed compensation plan {plan_id}: {len(execution_results)} payments processed"
        )
        return execution_results

    def contribute_to_justice_fund(
        self, amount: Decimal, source: str = "system"
    ) -> Decimal:
        """Contribute to temporal justice fund."""
        self.temporal_justice_fund += amount

        audit_emitter.emit_security_event(
            "justice_fund_contribution",
            {
                "amount": float(amount),
                "source": source,
                "new_balance": float(self.temporal_justice_fund),
            },
        )

        logger.info(
            f"Justice fund contribution: {amount} from {source}, new balance: {self.temporal_justice_fund}"
        )
        return self.temporal_justice_fund

    def get_system_justice_report(self) -> Dict[str, Any]:
        """Generate comprehensive system justice report."""

        if not self.justice_profiles:
            return {"error": "No entities analyzed yet"}

        # Calculate system-wide metrics
        all_scores = [
            p.calculate_temporal_justice_score() for p in self.justice_profiles.values()
        ]
        avg_justice_score = sum(all_scores) / len(all_scores)
        self.system_stats["average_justice_score"] = avg_justice_score

        # Justice distribution
        excellent_entities = len([s for s in all_scores if s >= 0.9])
        good_entities = len([s for s in all_scores if 0.7 <= s < 0.9])
        poor_entities = len([s for s in all_scores if s < 0.7])

        # Violation analysis
        active_violations = [
            v
            for v in self.violations.values()
            if (datetime.now(timezone.utc) - v.detected_at).days < 30
        ]
        severe_violations = [v for v in active_violations if v.severity >= 0.8]

        # Economic impact
        total_compensation_deficit = sum(
            p.compensation_deficit for p in self.justice_profiles.values()
        )
        total_value_created = sum(
            p.direct_value_created + p.derivative_value_generated
            for p in self.justice_profiles.values()
        )

        return {
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "system_statistics": self.system_stats,
            "justice_metrics": {
                "average_justice_score": avg_justice_score,
                "entities_excellent": excellent_entities,
                "entities_good": good_entities,
                "entities_poor": poor_entities,
                "total_entities": len(self.justice_profiles),
            },
            "violation_analysis": {
                "total_violations": len(self.violations),
                "active_violations": len(active_violations),
                "severe_violations": len(severe_violations),
                "violation_rate": len(active_violations) / len(self.justice_profiles),
            },
            "economic_analysis": {
                "total_compensation_deficit": float(total_compensation_deficit),
                "total_value_created": float(total_value_created),
                "justice_fund_balance": float(self.temporal_justice_fund),
                "compensation_coverage_ratio": float(
                    self.temporal_justice_fund / total_compensation_deficit
                    if total_compensation_deficit > 0
                    else 1.0
                ),
            },
            "recommendations": self._generate_system_recommendations(),
        }

    def _generate_system_recommendations(self) -> List[str]:
        """Generate system-wide justice recommendations."""
        recommendations = []

        avg_justice = self.system_stats["average_justice_score"]

        if avg_justice < 0.6:
            recommendations.append(
                "Critical: System-wide justice score below acceptable threshold"
            )
            recommendations.append("Implement emergency compensation redistribution")

        if len(self.violations) > len(self.justice_profiles) * 0.5:
            recommendations.append(
                "High violation rate detected - review justice parameters"
            )

        total_deficit = sum(
            p.compensation_deficit for p in self.justice_profiles.values()
        )
        if total_deficit > self.temporal_justice_fund * Decimal("2"):
            recommendations.append("Increase temporal justice fund contributions")

        if (
            self.system_stats["compensations_executed"]
            < self.system_stats["violations_detected"] * 0.3
        ):
            recommendations.append("Increase compensation plan execution rate")

        return recommendations


# Global temporal justice engine instance
temporal_justice_engine = TemporalJusticeEngine()


def analyze_temporal_justice(
    entity_id: str, entity_type: str = "ai_agent"
) -> Dict[str, Any]:
    """Convenience function to analyze temporal justice."""

    profile = temporal_justice_engine.analyze_entity_justice(entity_id, entity_type)
    return profile.to_dict()


def detect_justice_violations(entity_id: str = None) -> List[Dict[str, Any]]:
    """Convenience function to detect justice violations."""

    violations = temporal_justice_engine.detect_justice_violations(entity_id)
    return [v.to_dict() for v in violations]


def create_justice_compensation_plan(violation_ids: List[str]) -> Dict[str, Any]:
    """Convenience function to create compensation plan."""

    plan = temporal_justice_engine.create_compensation_plan(violation_ids)
    return plan.to_dict()


def get_justice_system_report() -> Dict[str, Any]:
    """Convenience function to get system justice report."""

    return temporal_justice_engine.get_system_justice_report()
