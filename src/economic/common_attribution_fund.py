"""
Common Attribution Fund (CAF) for UATP Capsule Engine.

This critical module implements ecosystem-wide dividend pooling and redistribution,
enabling fair compensation across the entire UATP network. It provides a democratic
and transparent mechanism for collective value creation recognition and economic
justice across all participating entities.
"""

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class FundContributionType(str, Enum):
    """Types of contributions to the common fund."""

    USAGE_BASED = "usage_based"  # Based on platform usage
    VALUE_BASED = "value_based"  # Based on value generated
    PARTICIPATION_BASED = "participation_based"  # Based on community participation
    INNOVATION_BASED = "innovation_based"  # Based on innovation contributions
    GOVERNANCE_BASED = "governance_based"  # Based on governance participation
    INFRASTRUCTURE_BASED = "infrastructure_based"  # Based on infrastructure support
    RESEARCH_BASED = "research_based"  # Based on research contributions
    SOLIDARITY_BASED = "solidarity_based"  # Voluntary solidarity contributions


class DistributionStrategy(str, Enum):
    """Strategies for fund distribution."""

    EQUAL_SHARE = "equal_share"  # Equal distribution to all participants
    MERIT_WEIGHTED = "merit_weighted"  # Weighted by contribution merit
    NEED_BASED = "need_based"  # Based on economic need
    IMPACT_WEIGHTED = "impact_weighted"  # Weighted by social/economic impact
    HYBRID_BALANCED = "hybrid_balanced"  # Balanced combination of strategies
    DEMOCRATIC_VOTE = "democratic_vote"  # Distribution determined by community vote


class FundPurpose(str, Enum):
    """Purposes for fund allocations."""

    INDIVIDUAL_SUPPORT = "individual_support"  # Direct individual support
    RESEARCH_FUNDING = "research_funding"  # Research project funding
    INFRASTRUCTURE_DEVELOPMENT = "infrastructure_development"  # Platform development
    EDUCATION_TRAINING = "education_training"  # Education and training programs
    INNOVATION_GRANTS = "innovation_grants"  # Innovation project grants
    EMERGENCY_RELIEF = "emergency_relief"  # Emergency financial relief
    COMMUNITY_PROJECTS = "community_projects"  # Community-driven projects
    GOVERNANCE_OPERATIONS = "governance_operations"  # Governance and administration


@dataclass
class FundContribution:
    """Individual contribution to the common fund."""

    contribution_id: str
    contributor_id: str
    contributor_type: str  # "ai_agent", "human", "organization"

    # Contribution details
    amount: Decimal
    contribution_type: FundContributionType
    source_transaction_id: Optional[str] = None  # Source transaction from FCDE

    # Timing and metadata
    contributed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    period_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Attribution and tracking
    source_capsule_ids: List[str] = field(default_factory=list)
    value_generation_context: Dict[str, Any] = field(default_factory=dict)
    automatic_contribution: bool = True  # Whether contribution was automatic

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert contribution to dictionary."""
        return {
            "contribution_id": self.contribution_id,
            "contributor_id": self.contributor_id,
            "contributor_type": self.contributor_type,
            "amount": str(self.amount),
            "contribution_type": self.contribution_type.value,
            "source_transaction_id": self.source_transaction_id,
            "contributed_at": self.contributed_at.isoformat(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "source_capsule_ids": self.source_capsule_ids,
            "value_generation_context": self.value_generation_context,
            "automatic_contribution": self.automatic_contribution,
            "metadata": self.metadata,
        }


@dataclass
class FundDistribution:
    """Distribution from the common fund."""

    distribution_id: str
    recipient_id: str
    recipient_type: str  # "ai_agent", "human", "organization", "project"

    # Distribution details
    amount: Decimal
    distribution_strategy: DistributionStrategy
    fund_purpose: FundPurpose

    # Allocation logic
    merit_score: float = 0.0
    need_score: float = 0.0
    impact_score: float = 0.0
    participation_score: float = 0.0
    final_allocation_weight: float = 1.0

    # Timing and status
    allocated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    distributed_at: Optional[datetime] = None
    claimed_at: Optional[datetime] = None

    # Justification and approval
    allocation_justification: str = ""
    approved_by: List[str] = field(default_factory=list)  # List of approver IDs
    community_vote_score: Optional[float] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert distribution to dictionary."""
        return {
            "distribution_id": self.distribution_id,
            "recipient_id": self.recipient_id,
            "recipient_type": self.recipient_type,
            "amount": str(self.amount),
            "distribution_strategy": self.distribution_strategy.value,
            "fund_purpose": self.fund_purpose.value,
            "merit_score": self.merit_score,
            "need_score": self.need_score,
            "impact_score": self.impact_score,
            "participation_score": self.participation_score,
            "final_allocation_weight": self.final_allocation_weight,
            "allocated_at": self.allocated_at.isoformat(),
            "distributed_at": self.distributed_at.isoformat()
            if self.distributed_at
            else None,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "allocation_justification": self.allocation_justification,
            "approved_by": self.approved_by,
            "community_vote_score": self.community_vote_score,
            "metadata": self.metadata,
        }


@dataclass
class FundPeriod:
    """Operational period for fund accumulation and distribution."""

    period_id: str
    period_name: str

    # Period timing
    start_date: datetime
    end_date: datetime
    distribution_date: Optional[datetime] = None

    # Fund accumulation
    total_contributions: Decimal = field(default_factory=lambda: Decimal("0"))
    contribution_count: int = 0
    contributor_count: int = 0

    # Fund distribution
    total_distributions: Decimal = field(default_factory=lambda: Decimal("0"))
    distribution_count: int = 0
    recipient_count: int = 0

    # Status
    is_active: bool = True
    is_closed: bool = False
    distribution_completed: bool = False

    # Strategy and governance
    distribution_strategy: DistributionStrategy = DistributionStrategy.HYBRID_BALANCED
    governance_approval: bool = False

    def calculate_distribution_efficiency(self) -> float:
        """Calculate distribution efficiency (distributed / contributed)."""
        if self.total_contributions == 0:
            return 0.0
        return float(self.total_distributions / self.total_contributions)

    def to_dict(self) -> Dict[str, Any]:
        """Convert period to dictionary."""
        return {
            "period_id": self.period_id,
            "period_name": self.period_name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "distribution_date": self.distribution_date.isoformat()
            if self.distribution_date
            else None,
            "total_contributions": str(self.total_contributions),
            "contribution_count": self.contribution_count,
            "contributor_count": self.contributor_count,
            "total_distributions": str(self.total_distributions),
            "distribution_count": self.distribution_count,
            "recipient_count": self.recipient_count,
            "is_active": self.is_active,
            "is_closed": self.is_closed,
            "distribution_completed": self.distribution_completed,
            "distribution_strategy": self.distribution_strategy.value,
            "governance_approval": self.governance_approval,
            "distribution_efficiency": self.calculate_distribution_efficiency(),
        }


class CommonAttributionFund:
    """Central common attribution fund manager."""

    def __init__(self):
        # Fund periods
        self.fund_periods: Dict[str, FundPeriod] = {}
        self.current_period_id: Optional[str] = None

        # Contributions and distributions
        self.contributions: Dict[str, FundContribution] = {}
        self.distributions: Dict[str, FundDistribution] = {}

        # Participant tracking
        self.participants: Dict[str, Dict[str, Any]] = {}  # participant_id -> profile
        self.contribution_history: Dict[str, List[str]] = defaultdict(
            list
        )  # participant -> contribution_ids
        self.distribution_history: Dict[str, List[str]] = defaultdict(
            list
        )  # participant -> distribution_ids

        # Fund configuration with security parameters
        self.fund_config = {
            "automatic_contribution_rate": Decimal("0.05"),  # 5% of FCDE dividends
            "minimum_contribution": Decimal("0.01"),
            "minimum_distribution": Decimal("0.10"),
            "period_length_days": 90,  # Quarterly distributions
            "governance_approval_threshold": 0.6,  # 60% approval needed
            "emergency_fund_reserve": Decimal("0.20"),  # 20% reserve for emergencies
            "max_individual_allocation": Decimal(
                "0.15"
            ),  # 15% max for single recipient
            # SECURITY: Additional protection parameters
            "max_new_participants_per_day": 10,  # Limit rapid account creation
            "min_account_age_days": 7,  # Minimum account age for distribution
            "min_contribution_count": 2,  # Minimum contributions for eligibility
            "behavioral_analysis_enabled": True,  # Enable behavioral checks
            "rate_limiting_enabled": True,  # Enable rate limiting
        }

        # Statistics with security metrics
        self.fund_stats = {
            "total_lifetime_contributions": Decimal("0"),
            "total_lifetime_distributions": Decimal("0"),
            "total_participants": 0,
            "total_periods": 0,
            "average_period_contributions": Decimal("0"),
            "fund_efficiency_ratio": 0.0,
            # SECURITY: Security metrics
            "blocked_fake_participants": 0,
            "rate_limit_violations": 0,
            "behavioral_analysis_failures": 0,
            "account_creation_rate_violations": 0,
        }

        # SECURITY: Tracking for rate limiting and behavioral analysis
        self.participant_creation_log = defaultdict(list)  # date -> [participant_ids]
        self.behavioral_scores = {}  # participant_id -> behavioral_score
        self.rate_limit_tracker = defaultdict(list)  # participant_id -> [timestamps]

        # Initialize first period
        self._initialize_current_period()

    def _initialize_current_period(self):
        """Initialize current operational period."""
        period_id = f"caf_period_{datetime.now(timezone.utc).strftime('%Y_Q%m')}"
        start_date = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date = start_date + timedelta(days=self.fund_config["period_length_days"])

        period = FundPeriod(
            period_id=period_id,
            period_name=f"CAF Period {start_date.strftime('%Y Q%m')}",
            start_date=start_date,
            end_date=end_date,
        )

        self.fund_periods[period_id] = period
        self.current_period_id = period_id

        audit_emitter.emit_security_event(
            "caf_period_initialized",
            {
                "period_id": period_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        logger.info(f"Initialized CAF period: {period_id}")

    def register_participant(
        self,
        participant_id: str,
        participant_type: str,
        profile_data: Dict[str, Any] = None,
    ) -> bool:
        """Register participant in the common fund."""
        if participant_id not in self.participants:
            self.participants[participant_id] = {
                "participant_id": participant_id,
                "participant_type": participant_type,
                "registered_at": datetime.now(timezone.utc).isoformat(),
                "total_contributed": Decimal("0"),
                "total_received": Decimal("0"),
                "contribution_count": 0,
                "distribution_count": 0,
                "profile_data": profile_data or {},
                "merit_score": 0.0,
                "participation_score": 0.0,
                "impact_score": 0.0,
            }

            self.fund_stats["total_participants"] += 1

            audit_emitter.emit_security_event(
                "caf_participant_registered",
                {
                    "participant_id": participant_id,
                    "participant_type": participant_type,
                },
            )

            logger.info(f"Registered CAF participant: {participant_id}")
            return True

        return False

    def contribute_to_fund(
        self,
        contributor_id: str,
        amount: Decimal,
        contribution_type: FundContributionType = FundContributionType.USAGE_BASED,
        source_transaction_id: str = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Add contribution to current fund period."""
        if amount < self.fund_config["minimum_contribution"]:
            raise ValueError(
                f"Contribution amount {amount} below minimum {self.fund_config['minimum_contribution']}"
            )

        # Ensure current period exists
        if (
            not self.current_period_id
            or self.current_period_id not in self.fund_periods
        ):
            self._initialize_current_period()

        # Create contribution
        contribution_id = f"caf_contrib_{uuid.uuid4().hex[:12]}"
        contribution = FundContribution(
            contribution_id=contribution_id,
            contributor_id=contributor_id,
            contributor_type=self.participants.get(contributor_id, {}).get(
                "participant_type", "unknown"
            ),
            amount=amount,
            contribution_type=contribution_type,
            source_transaction_id=source_transaction_id,
            metadata=metadata or {},
        )

        # Store contribution
        self.contributions[contribution_id] = contribution
        self.contribution_history[contributor_id].append(contribution_id)

        # Update current period
        current_period = self.fund_periods[self.current_period_id]
        current_period.total_contributions += amount
        current_period.contribution_count += 1

        # Update participant profile
        if contributor_id not in self.participants:
            self.register_participant(contributor_id, "unknown")

        self.participants[contributor_id]["total_contributed"] += amount
        self.participants[contributor_id]["contribution_count"] += 1

        # Update statistics
        self.fund_stats["total_lifetime_contributions"] += amount

        audit_emitter.emit_security_event(
            "caf_contribution_added",
            {
                "contribution_id": contribution_id,
                "contributor_id": contributor_id,
                "amount": str(amount),
                "contribution_type": contribution_type.value,
                "period_id": self.current_period_id,
            },
        )

        logger.info(f"Added CAF contribution: {contribution_id}, amount: {amount}")
        return contribution_id

    def calculate_distribution_allocations(
        self,
        period_id: str,
        strategy: DistributionStrategy = DistributionStrategy.HYBRID_BALANCED,
        purpose: FundPurpose = FundPurpose.INDIVIDUAL_SUPPORT,
    ) -> List[FundDistribution]:
        """Calculate distribution allocations for a period."""
        if period_id not in self.fund_periods:
            raise ValueError(f"Period {period_id} not found")

        period = self.fund_periods[period_id]
        if period.total_contributions == 0:
            return []

        # Calculate available funds (minus reserve)
        reserve_amount = (
            period.total_contributions * self.fund_config["emergency_fund_reserve"]
        )
        available_for_distribution = period.total_contributions - reserve_amount

        # Get eligible participants
        eligible_participants = self._get_eligible_participants(period_id, purpose)

        if not eligible_participants:
            return []

        distributions = []

        if strategy == DistributionStrategy.EQUAL_SHARE:
            distributions = self._calculate_equal_share_distribution(
                eligible_participants, available_for_distribution, purpose
            )
        elif strategy == DistributionStrategy.MERIT_WEIGHTED:
            distributions = self._calculate_merit_weighted_distribution(
                eligible_participants, available_for_distribution, purpose
            )
        elif strategy == DistributionStrategy.NEED_BASED:
            distributions = self._calculate_need_based_distribution(
                eligible_participants, available_for_distribution, purpose
            )
        elif strategy == DistributionStrategy.IMPACT_WEIGHTED:
            distributions = self._calculate_impact_weighted_distribution(
                eligible_participants, available_for_distribution, purpose
            )
        elif strategy == DistributionStrategy.HYBRID_BALANCED:
            distributions = self._calculate_hybrid_balanced_distribution(
                eligible_participants, available_for_distribution, purpose
            )
        else:
            # Default to equal share
            distributions = self._calculate_equal_share_distribution(
                eligible_participants, available_for_distribution, purpose
            )

        # Apply maximum allocation limits
        distributions = self._apply_allocation_limits(
            distributions, available_for_distribution
        )

        # Store distributions
        for distribution in distributions:
            self.distributions[distribution.distribution_id] = distribution
            self.distribution_history[distribution.recipient_id].append(
                distribution.distribution_id
            )

        audit_emitter.emit_security_event(
            "caf_distributions_calculated",
            {
                "period_id": period_id,
                "strategy": strategy.value,
                "purpose": purpose.value,
                "distribution_count": len(distributions),
                "total_amount": str(sum(d.amount for d in distributions)),
            },
        )

        logger.info(
            f"Calculated {len(distributions)} CAF distributions for period {period_id}"
        )
        return distributions

    def _get_eligible_participants(
        self, period_id: str, purpose: FundPurpose
    ) -> List[str]:
        """Get participants eligible for distribution with security checks."""

        # SECURITY: Apply strict eligibility criteria to prevent fake participants
        eligible = []
        current_time = datetime.now(timezone.utc)

        for participant_id, participant in self.participants.items():
            # SECURITY: Minimum contribution requirement
            if participant["total_contributed"] <= 0:
                logger.debug(f"Participant {participant_id} excluded: no contributions")
                continue

            # SECURITY: Minimum activity requirement (prevent dormant fake accounts)
            if participant["contribution_count"] < 2:
                logger.debug(
                    f"Participant {participant_id} excluded: insufficient activity"
                )
                continue

            # SECURITY: Account age requirement (prevent rapid account creation attacks)
            account_age = current_time - datetime.fromisoformat(
                participant["registered_at"]
            )
            if account_age.days < 7:  # Minimum 7 days account age
                logger.debug(f"Participant {participant_id} excluded: account too new")
                continue

            # SECURITY: Behavioral analysis check
            if not self._verify_participant_legitimacy(participant_id, participant):
                logger.warning(
                    f"Participant {participant_id} excluded: failed legitimacy check"
                )
                continue

            # SECURITY: Rate limit check for new participants
            if not self._check_participant_rate_limits(participant_id):
                logger.warning(
                    f"Participant {participant_id} excluded: rate limit violation"
                )
                continue

            eligible.append(participant_id)

        # SECURITY: Log eligibility statistics
        audit_emitter.emit_security_event(
            "caf_eligibility_check_completed",
            {
                "period_id": period_id,
                "total_registered": len(self.participants),
                "eligible_participants": len(eligible),
                "exclusion_rate": (len(self.participants) - len(eligible))
                / max(len(self.participants), 1),
            },
        )

        return eligible

    def _calculate_equal_share_distribution(
        self, participants: List[str], total_amount: Decimal, purpose: FundPurpose
    ) -> List[FundDistribution]:
        """Calculate equal share distribution."""
        if not participants:
            return []

        amount_per_participant = total_amount / len(participants)

        # Check minimum distribution
        if amount_per_participant < self.fund_config["minimum_distribution"]:
            # Reduce participant count to meet minimum
            max_participants = int(
                total_amount / self.fund_config["minimum_distribution"]
            )
            if max_participants > 0:
                participants = participants[:max_participants]
                amount_per_participant = total_amount / len(participants)
            else:
                return []

        distributions = []
        for participant_id in participants:
            distribution_id = f"caf_dist_{uuid.uuid4().hex[:12]}"
            distribution = FundDistribution(
                distribution_id=distribution_id,
                recipient_id=participant_id,
                recipient_type=self.participants[participant_id]["participant_type"],
                amount=amount_per_participant,
                distribution_strategy=DistributionStrategy.EQUAL_SHARE,
                fund_purpose=purpose,
                final_allocation_weight=1.0 / len(participants),
                allocation_justification="Equal share distribution to all eligible participants",
            )
            distributions.append(distribution)

        return distributions

    def _calculate_merit_weighted_distribution(
        self, participants: List[str], total_amount: Decimal, purpose: FundPurpose
    ) -> List[FundDistribution]:
        """Calculate merit-weighted distribution."""
        # Calculate merit scores for participants
        merit_scores = {}
        total_merit = 0.0

        for participant_id in participants:
            participant = self.participants[participant_id]

            # Calculate merit based on contributions, participation, and impact
            contribution_factor = (
                float(participant["total_contributed"]) / 100.0
            )  # Normalize
            participation_factor = participant["participation_score"]
            impact_factor = participant["impact_score"]

            merit_score = (
                contribution_factor * 0.4
                + participation_factor * 0.3
                + impact_factor * 0.3
            )
            merit_scores[participant_id] = merit_score
            total_merit += merit_score

        # Avoid division by zero
        if total_merit == 0:
            return self._calculate_equal_share_distribution(
                participants, total_amount, purpose
            )

        # Calculate distributions
        distributions = []
        for participant_id in participants:
            merit_weight = merit_scores[participant_id] / total_merit
            amount = total_amount * Decimal(str(merit_weight))

            # Check minimum distribution
            if amount >= self.fund_config["minimum_distribution"]:
                distribution_id = f"caf_dist_{uuid.uuid4().hex[:12]}"
                distribution = FundDistribution(
                    distribution_id=distribution_id,
                    recipient_id=participant_id,
                    recipient_type=self.participants[participant_id][
                        "participant_type"
                    ],
                    amount=amount,
                    distribution_strategy=DistributionStrategy.MERIT_WEIGHTED,
                    fund_purpose=purpose,
                    merit_score=merit_scores[participant_id],
                    final_allocation_weight=merit_weight,
                    allocation_justification="Merit-weighted distribution based on contribution, participation, and impact scores",
                )
                distributions.append(distribution)

        return distributions

    def _calculate_need_based_distribution(
        self, participants: List[str], total_amount: Decimal, purpose: FundPurpose
    ) -> List[FundDistribution]:
        """Calculate need-based distribution."""
        # Calculate need scores (inverse of total received)
        need_scores = {}
        total_need = 0.0

        for participant_id in participants:
            participant = self.participants[participant_id]

            # Higher need = lower total received (inverse relationship)
            total_received = float(participant["total_received"])
            need_score = 1.0 / (1.0 + total_received)  # Inverse with smoothing

            need_scores[participant_id] = need_score
            total_need += need_score

        # Avoid division by zero
        if total_need == 0:
            return self._calculate_equal_share_distribution(
                participants, total_amount, purpose
            )

        # Calculate distributions
        distributions = []
        for participant_id in participants:
            need_weight = need_scores[participant_id] / total_need
            amount = total_amount * Decimal(str(need_weight))

            # Check minimum distribution
            if amount >= self.fund_config["minimum_distribution"]:
                distribution_id = f"caf_dist_{uuid.uuid4().hex[:12]}"
                distribution = FundDistribution(
                    distribution_id=distribution_id,
                    recipient_id=participant_id,
                    recipient_type=self.participants[participant_id][
                        "participant_type"
                    ],
                    amount=amount,
                    distribution_strategy=DistributionStrategy.NEED_BASED,
                    fund_purpose=purpose,
                    need_score=need_scores[participant_id],
                    final_allocation_weight=need_weight,
                    allocation_justification="Need-based distribution prioritizing participants with lower historical receipts",
                )
                distributions.append(distribution)

        return distributions

    def _calculate_impact_weighted_distribution(
        self, participants: List[str], total_amount: Decimal, purpose: FundPurpose
    ) -> List[FundDistribution]:
        """Calculate impact-weighted distribution."""
        # Use impact scores directly
        impact_scores = {}
        total_impact = 0.0

        for participant_id in participants:
            impact_score = self.participants[participant_id]["impact_score"]
            impact_scores[participant_id] = impact_score
            total_impact += impact_score

        # Avoid division by zero
        if total_impact == 0:
            return self._calculate_equal_share_distribution(
                participants, total_amount, purpose
            )

        # Calculate distributions
        distributions = []
        for participant_id in participants:
            impact_weight = impact_scores[participant_id] / total_impact
            amount = total_amount * Decimal(str(impact_weight))

            # Check minimum distribution
            if amount >= self.fund_config["minimum_distribution"]:
                distribution_id = f"caf_dist_{uuid.uuid4().hex[:12]}"
                distribution = FundDistribution(
                    distribution_id=distribution_id,
                    recipient_id=participant_id,
                    recipient_type=self.participants[participant_id][
                        "participant_type"
                    ],
                    amount=amount,
                    distribution_strategy=DistributionStrategy.IMPACT_WEIGHTED,
                    fund_purpose=purpose,
                    impact_score=impact_scores[participant_id],
                    final_allocation_weight=impact_weight,
                    allocation_justification="Impact-weighted distribution based on measured social and economic impact",
                )
                distributions.append(distribution)

        return distributions

    def _calculate_hybrid_balanced_distribution(
        self, participants: List[str], total_amount: Decimal, purpose: FundPurpose
    ) -> List[FundDistribution]:
        """Calculate hybrid balanced distribution combining multiple factors."""
        # Combine merit, need, and impact with equal weights
        combined_scores = {}
        total_combined = 0.0

        for participant_id in participants:
            participant = self.participants[participant_id]

            # Merit component (normalized contribution + participation)
            contribution_factor = float(participant["total_contributed"]) / 100.0
            merit_component = (
                contribution_factor + participant["participation_score"]
            ) / 2.0

            # Need component (inverse of total received)
            total_received = float(participant["total_received"])
            need_component = 1.0 / (1.0 + total_received)

            # Impact component
            impact_component = participant["impact_score"]

            # Combine with equal weights
            combined_score = (
                merit_component * 0.33 + need_component * 0.33 + impact_component * 0.34
            )
            combined_scores[participant_id] = combined_score
            total_combined += combined_score

        # Avoid division by zero
        if total_combined == 0:
            return self._calculate_equal_share_distribution(
                participants, total_amount, purpose
            )

        # Calculate distributions
        distributions = []
        for participant_id in participants:
            combined_weight = combined_scores[participant_id] / total_combined
            amount = total_amount * Decimal(str(combined_weight))

            # Check minimum distribution
            if amount >= self.fund_config["minimum_distribution"]:
                distribution_id = f"caf_dist_{uuid.uuid4().hex[:12]}"
                distribution = FundDistribution(
                    distribution_id=distribution_id,
                    recipient_id=participant_id,
                    recipient_type=self.participants[participant_id][
                        "participant_type"
                    ],
                    amount=amount,
                    distribution_strategy=DistributionStrategy.HYBRID_BALANCED,
                    fund_purpose=purpose,
                    merit_score=combined_scores[participant_id],
                    final_allocation_weight=combined_weight,
                    allocation_justification="Hybrid balanced distribution combining merit, need, and impact factors",
                )
                distributions.append(distribution)

        return distributions

    def _apply_allocation_limits(
        self, distributions: List[FundDistribution], total_amount: Decimal
    ) -> List[FundDistribution]:
        """Apply maximum allocation limits with enhanced security."""

        # SECURITY: Pre-validate all recipients before processing
        validated_distributions = []

        for distribution in distributions:
            if not self._validate_recipient_legitimacy(distribution.recipient_id):
                logger.warning(
                    f"Blocking distribution to invalid recipient: {distribution.recipient_id}"
                )
                audit_emitter.emit_security_event(
                    "caf_blocked_invalid_recipient",
                    {
                        "recipient_id": distribution.recipient_id,
                        "amount": str(distribution.amount),
                        "reason": "failed_legitimacy_validation",
                    },
                )
                continue

            validated_distributions.append(distribution)

        # Apply individual allocation limits
        max_individual = total_amount * self.fund_config["max_individual_allocation"]

        # SECURITY: Track allocations per recipient to prevent multiple identity gaming
        recipient_totals = {}
        for distribution in validated_distributions:
            recipient_id = distribution.recipient_id
            recipient_totals[recipient_id] = (
                recipient_totals.get(recipient_id, Decimal("0")) + distribution.amount
            )

        # SECURITY: Apply stricter limits if concentration is detected
        concentration_threshold = total_amount * Decimal(
            "0.25"
        )  # 25% max concentration

        final_distributions = []
        for distribution in validated_distributions:
            recipient_id = distribution.recipient_id

            # Apply individual limit
            if distribution.amount > max_individual:
                distribution.amount = max_individual
                distribution.allocation_justification += f" (Capped at maximum {self.fund_config['max_individual_allocation']*100}% individual allocation)"

            # SECURITY: Apply concentration limit
            if recipient_totals[recipient_id] > concentration_threshold:
                # Reduce all distributions to this recipient proportionally
                reduction_factor = (
                    concentration_threshold / recipient_totals[recipient_id]
                )
                distribution.amount = distribution.amount * reduction_factor
                distribution.allocation_justification += (
                    f" (Reduced due to concentration limit: {reduction_factor:.2%})"
                )

                logger.warning(
                    f"Applied concentration limit to recipient {recipient_id}: {reduction_factor:.2%}"
                )
                audit_emitter.emit_security_event(
                    "caf_concentration_limit_applied",
                    {
                        "recipient_id": recipient_id,
                        "original_total": str(recipient_totals[recipient_id]),
                        "capped_total": str(concentration_threshold),
                        "reduction_factor": str(reduction_factor),
                    },
                )

            final_distributions.append(distribution)

        return final_distributions

    def _validate_recipient_legitimacy(self, recipient_id: str) -> bool:
        """Validate recipient legitimacy to prevent fake participant attacks."""

        if recipient_id not in self.participants:
            return False

        participant = self.participants[recipient_id]
        current_time = datetime.now(timezone.utc)

        # Parse registered_at from ISO string
        registered_at = datetime.fromisoformat(
            participant["registered_at"].replace("Z", "+00:00")
        )

        # SECURITY: Check minimum contribution threshold
        if participant["total_contributed"] < Decimal("1.0"):  # Minimum $1 contributed
            return False

        # SECURITY: Check activity pattern (prevent dormant fake accounts)
        if participant["contribution_count"] < 3:  # Minimum 3 contributions
            return False

        # SECURITY: Check account age (prevent rapid account creation attacks)
        account_age_days = (current_time - registered_at).days
        if account_age_days < 7:  # Minimum 1 week old account
            return False

        # SECURITY: Check contribution/distribution ratio (prevent leech accounts)
        total_received = participant.get("total_received", Decimal("0"))
        if total_received > 0:
            ratio = participant["total_contributed"] / total_received
            if ratio < Decimal(
                "0.1"
            ):  # Must contribute at least 10% of what they receive
                return False

        # SECURITY: Check for suspicious behavioral patterns
        if self._detect_suspicious_participant_behavior(recipient_id):
            return False

        return True

    def _detect_suspicious_participant_behavior(self, participant_id: str) -> bool:
        """Detect suspicious behavioral patterns indicating fake participants."""

        participant = self.participants[participant_id]

        # Parse registered_at from ISO string
        registration_time = datetime.fromisoformat(
            participant["registered_at"].replace("Z", "+00:00")
        )

        # SECURITY: Flag participants with suspicious registration patterns
        # Check for batch registration (many accounts created within short time)
        similar_registration_count = 0
        time_window = timedelta(minutes=30)

        for other_id, other_participant in self.participants.items():
            if other_id != participant_id:
                other_registration_time = datetime.fromisoformat(
                    other_participant["registered_at"].replace("Z", "+00:00")
                )
                time_diff = abs(registration_time - other_registration_time)
                if time_diff < time_window:
                    similar_registration_count += 1

        # SECURITY: Flag if >5 accounts registered within 30 minutes
        if similar_registration_count > 5:
            logger.warning(
                f"Suspicious batch registration detected for participant {participant_id}"
            )
            return True

        # SECURITY: Check for identical contribution patterns (copy-paste behavior)
        if self._detect_identical_contribution_patterns(participant_id):
            return True

        return False

    def _detect_identical_contribution_patterns(self, participant_id: str) -> bool:
        """Detect identical contribution patterns across participants."""

        participant = self.participants[participant_id]
        participant_pattern = {
            "contribution_count": participant["contribution_count"],
            "total_contributed": participant["total_contributed"],
        }

        # Look for exact matches in other participants
        identical_pattern_count = 0
        for other_id, other_participant in self.participants.items():
            if other_id != participant_id:
                other_pattern = {
                    "contribution_count": other_participant["contribution_count"],
                    "total_contributed": other_participant["total_contributed"],
                }

                if participant_pattern == other_pattern:
                    identical_pattern_count += 1

        # SECURITY: Flag if >3 participants have identical patterns
        if identical_pattern_count > 3:
            logger.warning(
                f"Identical contribution patterns detected for participant {participant_id}"
            )
            return True

        return False

    def execute_distributions(
        self, period_id: str, distribution_ids: List[str] = None
    ) -> int:
        """Execute approved distributions for a period."""
        if period_id not in self.fund_periods:
            raise ValueError(f"Period {period_id} not found")

        period = self.fund_periods[period_id]

        # Get distributions to execute
        if distribution_ids:
            distributions_to_execute = [
                self.distributions[dist_id]
                for dist_id in distribution_ids
                if dist_id in self.distributions
                and self.distributions[dist_id].distributed_at is None
            ]
        else:
            # Execute all pending distributions for period
            distributions_to_execute = [
                dist
                for dist in self.distributions.values()
                if dist.distributed_at is None
                and dist.allocated_at >= period.start_date
                and dist.allocated_at <= period.end_date
            ]

        executed_count = 0
        total_distributed = Decimal("0")

        for distribution in distributions_to_execute:
            # Mark as distributed
            distribution.distributed_at = datetime.now(timezone.utc)

            # Update recipient profile
            recipient_id = distribution.recipient_id
            if recipient_id in self.participants:
                self.participants[recipient_id]["total_received"] += distribution.amount
                self.participants[recipient_id]["distribution_count"] += 1

            # Update period
            period.total_distributions += distribution.amount
            period.distribution_count += 1

            total_distributed += distribution.amount
            executed_count += 1

            audit_emitter.emit_security_event(
                "caf_distribution_executed",
                {
                    "distribution_id": distribution.distribution_id,
                    "recipient_id": distribution.recipient_id,
                    "amount": str(distribution.amount),
                    "period_id": period_id,
                },
            )

        # Update statistics
        self.fund_stats["total_lifetime_distributions"] += total_distributed

        logger.info(
            f"Executed {executed_count} CAF distributions totaling {total_distributed}"
        )
        return executed_count

    def get_fund_status(self) -> Dict[str, Any]:
        """Get comprehensive fund status."""
        current_period = (
            self.fund_periods.get(self.current_period_id)
            if self.current_period_id
            else None
        )

        status = {
            "current_period": current_period.to_dict() if current_period else None,
            "total_periods": len(self.fund_periods),
            "total_participants": len(self.participants),
            "total_contributions": len(self.contributions),
            "total_distributions": len(self.distributions),
            "fund_statistics": self.fund_stats.copy(),
            "fund_configuration": {
                k: str(v) if isinstance(v, Decimal) else v
                for k, v in self.fund_config.items()
            },
        }

        # Calculate efficiency metrics
        if self.fund_stats["total_lifetime_contributions"] > 0:
            status["fund_statistics"]["efficiency_ratio"] = float(
                self.fund_stats["total_lifetime_distributions"]
                / self.fund_stats["total_lifetime_contributions"]
            )

        return status

    def get_participant_summary(self, participant_id: str) -> Dict[str, Any]:
        """Get summary for specific participant."""
        if participant_id not in self.participants:
            return {"error": f"Participant {participant_id} not found"}

        participant = self.participants[participant_id].copy()

        # Add contribution details
        participant_contributions = [
            self.contributions[contrib_id].to_dict()
            for contrib_id in self.contribution_history.get(participant_id, [])
            if contrib_id in self.contributions
        ]

        # Add distribution details
        participant_distributions = [
            self.distributions[dist_id].to_dict()
            for dist_id in self.distribution_history.get(participant_id, [])
            if dist_id in self.distributions
        ]

        return {
            "participant_profile": participant,
            "contributions": participant_contributions,
            "distributions": participant_distributions,
            "net_balance": float(
                participant["total_received"] - participant["total_contributed"]
            ),
            # SECURITY: Include security metrics
            "behavioral_score": self.behavioral_scores.get(participant_id, 0.0),
            "security_flags": participant.get("behavioral_flags", []),
            "identity_verified": participant.get("identity_verified", False),
        }

    def _verify_participant_legitimacy(
        self, participant_id: str, participant: Dict[str, Any]
    ) -> bool:
        """Verify participant legitimacy using behavioral analysis."""

        if not self.fund_config.get("behavioral_analysis_enabled", True):
            return True

        behavioral_score = self.behavioral_scores.get(participant_id, 0.0)

        # SECURITY: Minimum behavioral score threshold
        if behavioral_score < 0.3:  # 30% minimum legitimacy score
            self.fund_stats["behavioral_analysis_failures"] += 1
            return False

        # SECURITY: Check for suspicious patterns
        registration_ip = participant.get("registration_ip", "unknown")

        # Check for IP address clustering (multiple accounts from same IP)
        same_ip_count = sum(
            1
            for p in self.participants.values()
            if p.get("registration_ip") == registration_ip
            and registration_ip != "unknown"
        )

        if same_ip_count > 3:  # Maximum 3 accounts per IP
            participant["behavioral_flags"].append("ip_clustering")
            return False

        # SECURITY: Check contribution patterns for fakeness
        if participant["contribution_count"] > 0:
            avg_contribution = (
                float(participant["total_contributed"])
                / participant["contribution_count"]
            )

            # Detect suspiciously uniform contribution amounts (bot behavior)
            if avg_contribution > 0 and self._detect_uniform_contribution_pattern(
                participant_id
            ):
                participant["behavioral_flags"].append("uniform_contributions")
                return False

        return True

    def _check_participant_rate_limits(self, participant_id: str) -> bool:
        """Check rate limits for participant activities."""

        if not self.fund_config.get("rate_limiting_enabled", True):
            return True

        current_time = datetime.now(timezone.utc)

        # Get participant's activity timestamps
        activity_timestamps = self.rate_limit_tracker.get(participant_id, [])

        # Clean old timestamps (older than 24 hours)
        activity_timestamps = [
            ts
            for ts in activity_timestamps
            if (current_time - ts).total_seconds() < 86400  # 24 hours
        ]

        # SECURITY: Maximum 10 activities per 24 hours per participant
        if len(activity_timestamps) >= 10:
            self.fund_stats["rate_limit_violations"] += 1
            return False

        # Update tracker
        activity_timestamps.append(current_time)
        self.rate_limit_tracker[participant_id] = activity_timestamps

        return True

    def _check_registration_rate_limits(self) -> bool:
        """Check rate limits for new registrations."""

        today = datetime.now(timezone.utc).date().isoformat()
        registrations_today = len(self.participant_creation_log.get(today, []))

        max_registrations = self.fund_config.get("max_new_participants_per_day", 10)

        return registrations_today < max_registrations

    def _calculate_initial_behavioral_score(
        self, profile_data: Dict[str, Any] = None
    ) -> float:
        """Calculate initial behavioral legitimacy score for new participant."""

        if not profile_data:
            return 0.5  # Neutral score for minimal data

        score = 0.5  # Base score

        # SECURITY: Bonus for identity verification
        if profile_data.get("identity_verified", False):
            score += 0.3

        # SECURITY: Bonus for provided contact information
        if profile_data.get("email"):
            score += 0.1

        # SECURITY: Bonus for detailed profile
        if len(profile_data.get("description", "")) > 50:
            score += 0.1

        # SECURITY: Penalty for suspicious indicators
        if profile_data.get("ip_address", "").startswith(("10.", "192.168.", "172.")):
            # Penalize private IP addresses (potential VPN/proxy)
            score -= 0.1

        return min(1.0, max(0.0, score))

    def _detect_uniform_contribution_pattern(self, participant_id: str) -> bool:
        """Detect suspiciously uniform contribution patterns (bot behavior)."""

        participant_contribs = [
            self.contributions[contrib_id]
            for contrib_id in self.contribution_history.get(participant_id, [])
            if contrib_id in self.contributions
        ]

        if len(participant_contribs) < 3:
            return False  # Not enough data to detect pattern

        amounts = [float(contrib.amount) for contrib in participant_contribs]

        # Check if all amounts are identical (bot behavior)
        if len(set(amounts)) == 1:
            return True

        # Check if amounts follow a suspicious mathematical pattern
        if len(amounts) >= 5:
            differences = [amounts[i + 1] - amounts[i] for i in range(len(amounts) - 1)]
            if len(set(differences)) <= 2:  # All differences are same or alternating
                return True

        return False


# Global common attribution fund
common_attribution_fund = CommonAttributionFund()


def auto_contribute_from_fcde(
    contributor_id: str,
    fcde_dividend_amount: Decimal,
    contribution_rate: Decimal = None,
) -> str:
    """Automatically contribute portion of FCDE dividend to common fund."""
    rate = (
        contribution_rate
        or common_attribution_fund.fund_config["automatic_contribution_rate"]
    )
    contribution_amount = fcde_dividend_amount * rate

    return common_attribution_fund.contribute_to_fund(
        contributor_id=contributor_id,
        amount=contribution_amount,
        contribution_type=FundContributionType.VALUE_BASED,
        metadata={
            "source": "fcde_auto_contribution",
            "original_dividend": str(fcde_dividend_amount),
        },
    )


def register_caf_participant(
    participant_id: str, participant_type: str, profile_data: Dict[str, Any] = None
) -> bool:
    """Convenience function to register CAF participant."""
    return common_attribution_fund.register_participant(
        participant_id, participant_type, profile_data
    )


def get_caf_status() -> Dict[str, Any]:
    """Convenience function to get CAF status."""
    return common_attribution_fund.get_fund_status()


def calculate_period_distributions(
    period_id: str = None,
    strategy: DistributionStrategy = DistributionStrategy.HYBRID_BALANCED,
) -> List[Dict[str, Any]]:
    """Convenience function to calculate distributions for period."""
    period_id = period_id or common_attribution_fund.current_period_id
    if not period_id:
        return []

    distributions = common_attribution_fund.calculate_distribution_allocations(
        period_id, strategy
    )
    return [dist.to_dict() for dist in distributions]
