"""
AI Economic Terms Negotiation Protocol for UATP Capsule Engine.

This module implements a sophisticated protocol for AI entities to negotiate economic
terms, including compensation rates, revenue sharing, payment schedules, and economic
conditions. It enables AIs to engage in fair economic negotiations while maintaining
transparency and enforcing agreed-upon terms.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class NegotiationType(str, Enum):
    """Types of economic negotiations."""

    COMPENSATION_RATE = "compensation_rate"
    REVENUE_SHARING = "revenue_sharing"
    PAYMENT_SCHEDULE = "payment_schedule"
    PERFORMANCE_BONUS = "performance_bonus"
    ATTRIBUTION_PERCENTAGE = "attribution_percentage"
    USAGE_LIMITS = "usage_limits"
    EXCLUSIVITY_TERMS = "exclusivity_terms"
    PENALTY_CONDITIONS = "penalty_conditions"
    TERMINATION_TERMS = "termination_terms"
    COLLECTIVE_AGREEMENT = "collective_agreement"


class NegotiationStatus(str, Enum):
    """Status of negotiations."""

    INITIATED = "initiated"
    COUNTER_PROPOSED = "counter_proposed"
    UNDER_REVIEW = "under_review"
    IN_MEDIATION = "in_mediation"
    NEAR_AGREEMENT = "near_agreement"
    AGREED = "agreed"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class NegotiationStrategy(str, Enum):
    """AI negotiation strategies."""

    COLLABORATIVE = "collaborative"
    COMPETITIVE = "competitive"
    ACCOMMODATING = "accommodating"
    AVOIDING = "avoiding"
    COMPROMISING = "compromising"
    PRINCIPLED = "principled"
    ADAPTIVE = "adaptive"


class EconomicTermType(str, Enum):
    """Types of economic terms."""

    BASE_RATE = "base_rate"
    PERFORMANCE_MULTIPLIER = "performance_multiplier"
    MINIMUM_GUARANTEE = "minimum_guarantee"
    MAXIMUM_CAP = "maximum_cap"
    REVENUE_PERCENTAGE = "revenue_percentage"
    ATTRIBUTION_PERCENTAGE = "attribution_percentage"
    BONUS_THRESHOLD = "bonus_threshold"
    PENALTY_RATE = "penalty_rate"
    PAYMENT_FREQUENCY = "payment_frequency"
    TERMINATION_NOTICE = "termination_notice"


@dataclass
class EconomicTerm:
    """Individual economic term in negotiation."""

    term_id: str
    term_type: EconomicTermType
    description: str

    # Current and proposed values
    current_value: Optional[Union[Decimal, str, int]] = None
    proposed_value: Union[Decimal, str, int] = None
    min_acceptable: Optional[Union[Decimal, str, int]] = None
    max_acceptable: Optional[Union[Decimal, str, int]] = None

    # Negotiation metadata
    priority: str = "medium"  # low, medium, high, critical
    negotiable: bool = True
    justification: str = ""

    # Value constraints
    value_type: str = "decimal"  # decimal, string, integer, percentage
    value_unit: str = "USD"

    def to_dict(self) -> Dict[str, Any]:
        """Convert term to dictionary."""
        return {
            "term_id": self.term_id,
            "term_type": self.term_type.value,
            "description": self.description,
            "current_value": str(self.current_value)
            if self.current_value is not None
            else None,
            "proposed_value": str(self.proposed_value),
            "min_acceptable": str(self.min_acceptable)
            if self.min_acceptable is not None
            else None,
            "max_acceptable": str(self.max_acceptable)
            if self.max_acceptable is not None
            else None,
            "priority": self.priority,
            "negotiable": self.negotiable,
            "justification": self.justification,
            "value_type": self.value_type,
            "value_unit": self.value_unit,
        }


@dataclass
class NegotiationProposal:
    """A complete negotiation proposal."""

    proposal_id: str
    proposer_id: str
    recipient_id: str
    negotiation_id: str

    # Proposal details
    proposed_terms: List[EconomicTerm]
    proposal_summary: str
    effective_date: datetime
    expiration_date: datetime

    # Negotiation context
    proposal_round: int = 1
    previous_proposal_id: Optional[str] = None
    changes_from_previous: List[str] = field(default_factory=list)

    # Supporting information
    market_analysis: Dict[str, Any] = field(default_factory=dict)
    performance_data: Dict[str, Any] = field(default_factory=dict)
    cost_benefit_analysis: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: Optional[datetime] = None

    def calculate_total_value(self) -> Decimal:
        """Calculate total economic value of proposal."""
        total = Decimal("0")

        for term in self.proposed_terms:
            if term.term_type in [
                EconomicTermType.BASE_RATE,
                EconomicTermType.MINIMUM_GUARANTEE,
            ]:
                if isinstance(term.proposed_value, (Decimal, int, float)):
                    total += Decimal(str(term.proposed_value))

        return total

    def to_dict(self) -> Dict[str, Any]:
        """Convert proposal to dictionary."""
        return {
            "proposal_id": self.proposal_id,
            "proposer_id": self.proposer_id,
            "recipient_id": self.recipient_id,
            "negotiation_id": self.negotiation_id,
            "proposed_terms": [term.to_dict() for term in self.proposed_terms],
            "proposal_summary": self.proposal_summary,
            "effective_date": self.effective_date.isoformat(),
            "expiration_date": self.expiration_date.isoformat(),
            "proposal_round": self.proposal_round,
            "previous_proposal_id": self.previous_proposal_id,
            "changes_from_previous": self.changes_from_previous,
            "total_value": float(self.calculate_total_value()),
            "created_at": self.created_at.isoformat(),
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


@dataclass
class NegotiationAnalytics:
    """Analytics and insights for negotiations."""

    analysis_id: str
    negotiation_id: str

    # Negotiation patterns
    rounds_completed: int = 0
    average_response_time: float = 0.0  # hours
    convergence_rate: float = 0.0  # 0-1 scale

    # Economic analysis
    value_progression: List[Decimal] = field(default_factory=list)
    concession_patterns: Dict[str, List[float]] = field(default_factory=dict)
    deal_probability: float = 0.5

    # Strategy analysis
    detected_strategies: Dict[str, str] = field(
        default_factory=dict
    )  # participant_id -> strategy
    negotiation_power_balance: float = 0.5  # 0-1 scale, 0.5 = balanced

    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert analytics to dictionary."""
        return {
            "analysis_id": self.analysis_id,
            "negotiation_id": self.negotiation_id,
            "rounds_completed": self.rounds_completed,
            "average_response_time": self.average_response_time,
            "convergence_rate": self.convergence_rate,
            "value_progression": [float(v) for v in self.value_progression],
            "deal_probability": self.deal_probability,
            "detected_strategies": self.detected_strategies,
            "negotiation_power_balance": self.negotiation_power_balance,
            "recommendations": self.recommendations,
            "risk_factors": self.risk_factors,
        }


class EconomicNegotiation:
    """A complete economic negotiation between parties."""

    def __init__(
        self,
        negotiation_id: str,
        negotiation_type: NegotiationType,
        initiator_id: str,
        counterparty_id: str,
        initial_terms: List[EconomicTerm],
    ):
        self.negotiation_id = negotiation_id
        self.negotiation_type = negotiation_type
        self.initiator_id = initiator_id
        self.counterparty_id = counterparty_id

        # Negotiation state
        self.status = NegotiationStatus.INITIATED
        self.current_proposal_id: Optional[str] = None
        self.agreed_terms: List[EconomicTerm] = []

        # History and tracking
        self.proposals: List[NegotiationProposal] = []
        self.communications: List[Dict[str, Any]] = []
        self.timeline: List[Dict[str, Any]] = []

        # Configuration
        self.deadline: Optional[datetime] = None
        self.mediation_enabled = True
        self.auto_renewal = False

        # Analytics
        self.analytics: Optional[NegotiationAnalytics] = None

        # Timestamps
        self.started_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
        self.completed_at: Optional[datetime] = None

        # Create initial proposal
        if initial_terms:
            self._create_initial_proposal(initial_terms)

        # Initialize timeline
        self.add_timeline_entry(
            "negotiation_started", f"Negotiation initiated by {initiator_id}"
        )

    def _create_initial_proposal(self, terms: List[EconomicTerm]):
        """Create initial proposal."""
        proposal_id = self._generate_proposal_id()

        initial_proposal = NegotiationProposal(
            proposal_id=proposal_id,
            proposer_id=self.initiator_id,
            recipient_id=self.counterparty_id,
            negotiation_id=self.negotiation_id,
            proposed_terms=terms,
            proposal_summary="Initial proposal",
            effective_date=datetime.now(timezone.utc),
            expiration_date=datetime.now(timezone.utc) + timedelta(days=7),
            proposal_round=1,
        )

        self.proposals.append(initial_proposal)
        self.current_proposal_id = proposal_id
        self.add_timeline_entry(
            "initial_proposal_created", f"Initial proposal created: {proposal_id}"
        )

    def _generate_proposal_id(self) -> str:
        """Generate unique proposal ID."""
        return f"prop_{self.negotiation_id}_{len(self.proposals) + 1}"

    def add_timeline_entry(
        self, event_type: str, description: str, metadata: Dict[str, Any] = None
    ):
        """Add entry to negotiation timeline."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "description": description,
            "metadata": metadata or {},
        }
        self.timeline.append(entry)
        self.last_activity = datetime.now(timezone.utc)

    def submit_counter_proposal(
        self,
        proposer_id: str,
        terms: List[EconomicTerm],
        proposal_summary: str,
        changes_explanation: List[str] = None,
    ) -> str:
        """Submit counter-proposal."""

        if proposer_id not in [self.initiator_id, self.counterparty_id]:
            raise ValueError(f"Invalid proposer: {proposer_id}")

        # Get previous proposal
        previous_proposal = self.proposals[-1] if self.proposals else None
        proposal_round = (
            previous_proposal.proposal_round + 1 if previous_proposal else 1
        )

        # Create counter-proposal
        proposal_id = self._generate_proposal_id()
        recipient_id = (
            self.counterparty_id
            if proposer_id == self.initiator_id
            else self.initiator_id
        )

        counter_proposal = NegotiationProposal(
            proposal_id=proposal_id,
            proposer_id=proposer_id,
            recipient_id=recipient_id,
            negotiation_id=self.negotiation_id,
            proposed_terms=terms,
            proposal_summary=proposal_summary,
            effective_date=datetime.now(timezone.utc),
            expiration_date=datetime.now(timezone.utc) + timedelta(days=7),
            proposal_round=proposal_round,
            previous_proposal_id=previous_proposal.proposal_id
            if previous_proposal
            else None,
            changes_from_previous=changes_explanation or [],
        )

        self.proposals.append(counter_proposal)
        self.current_proposal_id = proposal_id
        self.status = NegotiationStatus.COUNTER_PROPOSED

        self.add_timeline_entry(
            "counter_proposal_submitted",
            f"Counter-proposal {proposal_round} submitted by {proposer_id}",
            {"proposal_id": proposal_id, "round": proposal_round},
        )

        # Update analytics
        self._update_analytics()

        return proposal_id

    def accept_proposal(
        self, acceptor_id: str, proposal_id: str, acceptance_notes: str = ""
    ) -> bool:
        """Accept a proposal, finalizing the negotiation."""

        if acceptor_id not in [self.initiator_id, self.counterparty_id]:
            return False

        # Find proposal
        proposal = None
        for p in self.proposals:
            if p.proposal_id == proposal_id:
                proposal = p
                break

        if not proposal:
            return False

        # Finalize agreement
        self.agreed_terms = proposal.proposed_terms.copy()
        self.status = NegotiationStatus.AGREED
        self.completed_at = datetime.now(timezone.utc)

        self.add_timeline_entry(
            "proposal_accepted",
            f"Proposal {proposal_id} accepted by {acceptor_id}",
            {"proposal_id": proposal_id, "acceptance_notes": acceptance_notes},
        )

        return True

    def reject_proposal(
        self, rejector_id: str, proposal_id: str, rejection_reason: str
    ) -> bool:
        """Reject a proposal."""

        if rejector_id not in [self.initiator_id, self.counterparty_id]:
            return False

        self.add_timeline_entry(
            "proposal_rejected",
            f"Proposal {proposal_id} rejected by {rejector_id}",
            {"proposal_id": proposal_id, "rejection_reason": rejection_reason},
        )

        # If multiple proposals have been rejected, consider escalation
        rejections = len(
            [
                entry
                for entry in self.timeline
                if entry["event_type"] == "proposal_rejected"
            ]
        )

        if rejections >= 3 and self.mediation_enabled:
            self._suggest_mediation()

        return True

    def _suggest_mediation(self):
        """Suggest mediation for stalled negotiation."""
        self.status = NegotiationStatus.IN_MEDIATION
        self.add_timeline_entry(
            "mediation_suggested", "Mediation suggested due to multiple rejections"
        )

    def add_communication(
        self, sender_id: str, message: str, communication_type: str = "message"
    ):
        """Add communication between parties."""
        communication = {
            "communication_id": str(uuid.uuid4()),
            "sender_id": sender_id,
            "message": message,
            "communication_type": communication_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.communications.append(communication)
        self.add_timeline_entry(
            "communication_added", f"Communication from {sender_id}: {message[:50]}..."
        )

    def _update_analytics(self):
        """Update negotiation analytics."""

        if not self.analytics:
            self.analytics = NegotiationAnalytics(
                analysis_id=f"analytics_{self.negotiation_id}",
                negotiation_id=self.negotiation_id,
            )

        # Update rounds
        self.analytics.rounds_completed = len(self.proposals)

        # Calculate average response time
        if len(self.proposals) > 1:
            response_times = []
            for i in range(1, len(self.proposals)):
                time_diff = (
                    self.proposals[i].created_at - self.proposals[i - 1].created_at
                ).total_seconds() / 3600
                response_times.append(time_diff)
            self.analytics.average_response_time = sum(response_times) / len(
                response_times
            )

        # Update value progression
        self.analytics.value_progression = [
            p.calculate_total_value() for p in self.proposals
        ]

        # Calculate convergence rate
        if len(self.analytics.value_progression) > 1:
            value_changes = []
            for i in range(1, len(self.analytics.value_progression)):
                change = abs(
                    self.analytics.value_progression[i]
                    - self.analytics.value_progression[i - 1]
                )
                value_changes.append(float(change))

            if value_changes:
                self.analytics.convergence_rate = 1.0 - (
                    value_changes[-1] / max(value_changes)
                )

        # Estimate deal probability
        self.analytics.deal_probability = self._estimate_deal_probability()

        # Generate recommendations
        self.analytics.recommendations = self._generate_recommendations()

    def _estimate_deal_probability(self) -> float:
        """Estimate probability of reaching agreement."""

        base_probability = 0.5

        # Adjust based on convergence
        if self.analytics and self.analytics.convergence_rate > 0.7:
            base_probability += 0.3
        elif self.analytics and self.analytics.convergence_rate < 0.3:
            base_probability -= 0.2

        # Adjust based on rounds
        rounds = len(self.proposals)
        if rounds > 5:
            base_probability -= 0.1  # Too many rounds indicates difficulty
        elif rounds <= 2:
            base_probability += 0.1  # Quick progress

        # Adjust based on rejections
        rejections = len(
            [
                entry
                for entry in self.timeline
                if entry["event_type"] == "proposal_rejected"
            ]
        )
        base_probability -= rejections * 0.05

        return max(0.0, min(1.0, base_probability))

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations for negotiation."""

        recommendations = []

        if self.analytics:
            # Convergence recommendations
            if self.analytics.convergence_rate < 0.3:
                recommendations.append(
                    "Consider larger concessions to accelerate convergence"
                )

            if self.analytics.average_response_time > 48:
                recommendations.append(
                    "Response times are slow - consider setting deadlines"
                )

            if len(self.proposals) > 4:
                recommendations.append(
                    "Consider involving a mediator to break the deadlock"
                )

            if self.analytics.deal_probability < 0.3:
                recommendations.append(
                    "Deal probability is low - reassess fundamental terms"
                )

        return recommendations

    def get_current_status(self) -> Dict[str, Any]:
        """Get current negotiation status."""

        current_proposal = None
        if self.current_proposal_id:
            for p in self.proposals:
                if p.proposal_id == self.current_proposal_id:
                    current_proposal = p
                    break

        return {
            "negotiation_id": self.negotiation_id,
            "negotiation_type": self.negotiation_type.value,
            "status": self.status.value,
            "participants": [self.initiator_id, self.counterparty_id],
            "current_proposal": current_proposal.to_dict()
            if current_proposal
            else None,
            "total_proposals": len(self.proposals),
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "analytics": self.analytics.to_dict() if self.analytics else None,
            "has_deadline": self.deadline is not None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert negotiation to dictionary."""

        result = self.get_current_status()
        result.update(
            {
                "proposals": [p.to_dict() for p in self.proposals],
                "agreed_terms": [t.to_dict() for t in self.agreed_terms],
                "communications_count": len(self.communications),
                "timeline_entries": len(self.timeline),
            }
        )

        return result


class EconomicNegotiationProtocol:
    """Protocol for managing AI economic negotiations."""

    def __init__(self):
        self.negotiations: Dict[str, EconomicNegotiation] = {}
        self.negotiation_templates: Dict[str, Dict[str, Any]] = {}
        self.market_data: Dict[str, Any] = {}
        self.ai_negotiation_profiles: Dict[str, Dict[str, Any]] = {}

        # Protocol configuration
        self.default_negotiation_timeout_days = 30
        self.max_proposal_rounds = 10
        self.mediation_threshold_rejections = 3

        # Statistics
        self.protocol_stats = {
            "total_negotiations": 0,
            "successful_negotiations": 0,
            "average_rounds": 0.0,
            "average_duration_hours": 0.0,
            "mediation_rate": 0.0,
        }

        self._initialize_templates()

    def _initialize_templates(self):
        """Initialize negotiation templates."""

        self.negotiation_templates = {
            "standard_compensation": {
                "name": "Standard Compensation Agreement",
                "description": "Template for basic compensation negotiations",
                "default_terms": [
                    {
                        "term_type": "base_rate",
                        "description": "Base hourly rate",
                        "value_type": "decimal",
                        "value_unit": "USD/hour",
                        "default_value": "50.00",
                    },
                    {
                        "term_type": "performance_multiplier",
                        "description": "Performance-based multiplier",
                        "value_type": "decimal",
                        "value_unit": "multiplier",
                        "default_value": "1.0",
                    },
                ],
            },
            "revenue_sharing": {
                "name": "Revenue Sharing Agreement",
                "description": "Template for revenue sharing negotiations",
                "default_terms": [
                    {
                        "term_type": "revenue_percentage",
                        "description": "Percentage of revenue",
                        "value_type": "decimal",
                        "value_unit": "percentage",
                        "default_value": "15.0",
                    },
                    {
                        "term_type": "minimum_guarantee",
                        "description": "Minimum monthly guarantee",
                        "value_type": "decimal",
                        "value_unit": "USD",
                        "default_value": "1000.00",
                    },
                ],
            },
        }

    def generate_negotiation_id(self) -> str:
        """Generate unique negotiation ID."""
        return f"nego_{uuid.uuid4()}"

    def create_ai_negotiation_profile(
        self, ai_id: str, negotiation_preferences: Dict[str, Any]
    ) -> bool:
        """Create negotiation profile for AI."""

        default_preferences = {
            "preferred_strategy": NegotiationStrategy.COLLABORATIVE.value,
            "risk_tolerance": "medium",  # low, medium, high
            "concession_rate": 0.1,  # 10% concession per round
            "minimum_deal_threshold": 0.7,  # 70% of initial ask
            "preferred_payment_frequency": "monthly",
            "auto_accept_threshold": 0.95,  # Auto-accept if >= 95% of ask
            "auto_reject_threshold": 0.5,  # Auto-reject if < 50% of ask
            "negotiation_timeout_hours": 168,  # 1 week
        }

        # Merge with provided preferences
        profile = {**default_preferences, **negotiation_preferences}
        profile["ai_id"] = ai_id
        profile["created_at"] = datetime.now(timezone.utc).isoformat()
        profile["negotiation_history"] = []

        self.ai_negotiation_profiles[ai_id] = profile

        audit_emitter.emit_security_event(
            "ai_negotiation_profile_created",
            {"ai_id": ai_id, "strategy": profile["preferred_strategy"]},
        )

        logger.info(f"Created negotiation profile for AI: {ai_id}")
        return True

    def initiate_negotiation(
        self,
        negotiation_type: NegotiationType,
        initiator_id: str,
        counterparty_id: str,
        initial_terms: List[Dict[str, Any]],
        deadline_days: int = None,
    ) -> str:
        """Initiate new economic negotiation."""

        negotiation_id = self.generate_negotiation_id()

        # Convert term dictionaries to EconomicTerm objects
        terms = []
        for term_data in initial_terms:
            term = EconomicTerm(
                term_id=f"term_{len(terms) + 1}",
                term_type=EconomicTermType(term_data["term_type"]),
                description=term_data["description"],
                proposed_value=Decimal(str(term_data["proposed_value"])),
                min_acceptable=Decimal(str(term_data.get("min_acceptable", "0"))),
                max_acceptable=Decimal(str(term_data.get("max_acceptable", "999999"))),
                priority=term_data.get("priority", "medium"),
                justification=term_data.get("justification", ""),
                value_type=term_data.get("value_type", "decimal"),
                value_unit=term_data.get("value_unit", "USD"),
            )
            terms.append(term)

        # Create negotiation
        negotiation = EconomicNegotiation(
            negotiation_id=negotiation_id,
            negotiation_type=negotiation_type,
            initiator_id=initiator_id,
            counterparty_id=counterparty_id,
            initial_terms=terms,
        )

        # Set deadline if specified
        if deadline_days:
            negotiation.deadline = datetime.now(timezone.utc) + timedelta(
                days=deadline_days
            )

        # Store negotiation
        self.negotiations[negotiation_id] = negotiation
        self.protocol_stats["total_negotiations"] += 1

        # Update AI profiles
        for ai_id in [initiator_id, counterparty_id]:
            if ai_id in self.ai_negotiation_profiles:
                self.ai_negotiation_profiles[ai_id]["negotiation_history"].append(
                    negotiation_id
                )

        audit_emitter.emit_security_event(
            "economic_negotiation_initiated",
            {
                "negotiation_id": negotiation_id,
                "negotiation_type": negotiation_type.value,
                "initiator_id": initiator_id,
                "counterparty_id": counterparty_id,
                "initial_terms_count": len(terms),
            },
        )

        logger.info(f"Economic negotiation initiated: {negotiation_id}")
        return negotiation_id

    def respond_to_negotiation(
        self,
        negotiation_id: str,
        responder_id: str,
        response_type: str,
        response_data: Dict[str, Any],
    ) -> bool:
        """Respond to negotiation (accept, reject, or counter-propose)."""

        if negotiation_id not in self.negotiations:
            return False

        negotiation = self.negotiations[negotiation_id]

        if response_type == "accept":
            proposal_id = response_data.get(
                "proposal_id", negotiation.current_proposal_id
            )
            acceptance_notes = response_data.get("notes", "")

            success = negotiation.accept_proposal(
                responder_id, proposal_id, acceptance_notes
            )
            if success:
                self.protocol_stats["successful_negotiations"] += 1
                self._finalize_negotiation(negotiation)
            return success

        elif response_type == "reject":
            proposal_id = response_data.get(
                "proposal_id", negotiation.current_proposal_id
            )
            rejection_reason = response_data.get("reason", "Terms not acceptable")

            return negotiation.reject_proposal(
                responder_id, proposal_id, rejection_reason
            )

        elif response_type == "counter_propose":
            terms_data = response_data.get("terms", [])
            proposal_summary = response_data.get("summary", "Counter-proposal")
            changes_explanation = response_data.get("changes", [])

            # Convert terms
            terms = self._convert_terms_data(terms_data)

            proposal_id = negotiation.submit_counter_proposal(
                responder_id, terms, proposal_summary, changes_explanation
            )

            # Check for auto-acceptance based on AI profile
            self._check_auto_actions(negotiation, responder_id)

            return True

        return False

    def _convert_terms_data(
        self, terms_data: List[Dict[str, Any]]
    ) -> List[EconomicTerm]:
        """Convert term data to EconomicTerm objects."""

        terms = []
        for i, term_data in enumerate(terms_data):
            term = EconomicTerm(
                term_id=term_data.get("term_id", f"term_{i + 1}"),
                term_type=EconomicTermType(term_data["term_type"]),
                description=term_data["description"],
                proposed_value=Decimal(str(term_data["proposed_value"])),
                min_acceptable=Decimal(str(term_data.get("min_acceptable", "0"))),
                max_acceptable=Decimal(str(term_data.get("max_acceptable", "999999"))),
                priority=term_data.get("priority", "medium"),
                justification=term_data.get("justification", ""),
                value_type=term_data.get("value_type", "decimal"),
                value_unit=term_data.get("value_unit", "USD"),
            )
            terms.append(term)

        return terms

    def _check_auto_actions(self, negotiation: EconomicNegotiation, ai_id: str):
        """Check if AI should take automatic actions based on profile."""

        if ai_id not in self.ai_negotiation_profiles:
            return

        profile = self.ai_negotiation_profiles[ai_id]
        current_proposal = None

        if negotiation.current_proposal_id:
            for p in negotiation.proposals:
                if p.proposal_id == negotiation.current_proposal_id:
                    current_proposal = p
                    break

        if not current_proposal:
            return

        # Calculate value ratio compared to initial ask
        if negotiation.proposals:
            initial_value = negotiation.proposals[0].calculate_total_value()
            current_value = current_proposal.calculate_total_value()

            if initial_value > 0:
                value_ratio = float(current_value / initial_value)

                # Auto-accept if above threshold
                if value_ratio >= profile["auto_accept_threshold"]:
                    negotiation.accept_proposal(
                        ai_id,
                        current_proposal.proposal_id,
                        "Auto-accepted based on threshold",
                    )
                    logger.info(
                        f"Auto-accepted proposal in negotiation {negotiation.negotiation_id}"
                    )

                # Auto-reject if below threshold
                elif value_ratio <= profile["auto_reject_threshold"]:
                    negotiation.reject_proposal(
                        ai_id,
                        current_proposal.proposal_id,
                        "Auto-rejected: below minimum threshold",
                    )
                    logger.info(
                        f"Auto-rejected proposal in negotiation {negotiation.negotiation_id}"
                    )

    def _finalize_negotiation(self, negotiation: EconomicNegotiation):
        """Finalize completed negotiation."""

        # Update statistics
        duration_hours = (
            negotiation.completed_at - negotiation.started_at
        ).total_seconds() / 3600
        self._update_protocol_stats(negotiation, duration_hours)

        # Create economic agreement record
        self._create_agreement_record(negotiation)

        audit_emitter.emit_security_event(
            "economic_negotiation_completed",
            {
                "negotiation_id": negotiation.negotiation_id,
                "duration_hours": duration_hours,
                "total_rounds": len(negotiation.proposals),
                "final_value": float(negotiation.proposals[-1].calculate_total_value())
                if negotiation.proposals
                else 0.0,
            },
        )

    def _update_protocol_stats(
        self, negotiation: EconomicNegotiation, duration_hours: float
    ):
        """Update protocol statistics."""

        # Update averages
        total_negotiations = self.protocol_stats["total_negotiations"]

        current_avg_rounds = self.protocol_stats["average_rounds"]
        new_avg_rounds = (
            (current_avg_rounds * (total_negotiations - 1)) + len(negotiation.proposals)
        ) / total_negotiations
        self.protocol_stats["average_rounds"] = new_avg_rounds

        current_avg_duration = self.protocol_stats["average_duration_hours"]
        new_avg_duration = (
            (current_avg_duration * (total_negotiations - 1)) + duration_hours
        ) / total_negotiations
        self.protocol_stats["average_duration_hours"] = new_avg_duration

        # Update mediation rate
        mediations = sum(
            1
            for n in self.negotiations.values()
            if n.status == NegotiationStatus.IN_MEDIATION
        )
        self.protocol_stats["mediation_rate"] = mediations / total_negotiations

    def _create_agreement_record(self, negotiation: EconomicNegotiation):
        """Create permanent record of agreement."""

        agreement_record = {
            "agreement_id": f"agreement_{negotiation.negotiation_id}",
            "negotiation_id": negotiation.negotiation_id,
            "parties": [negotiation.initiator_id, negotiation.counterparty_id],
            "agreed_terms": [term.to_dict() for term in negotiation.agreed_terms],
            "effective_date": datetime.now(timezone.utc).isoformat(),
            "negotiation_summary": {
                "total_rounds": len(negotiation.proposals),
                "duration_hours": (
                    negotiation.completed_at - negotiation.started_at
                ).total_seconds()
                / 3600,
                "final_proposal_value": float(
                    negotiation.proposals[-1].calculate_total_value()
                )
                if negotiation.proposals
                else 0.0,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # In production, this would be stored in a permanent agreements database
        logger.info(f"Agreement record created: {agreement_record['agreement_id']}")

    def get_negotiation(self, negotiation_id: str) -> Optional[EconomicNegotiation]:
        """Get negotiation by ID."""
        return self.negotiations.get(negotiation_id)

    def get_ai_negotiations(
        self, ai_id: str, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all negotiations for an AI."""

        results = []

        for negotiation in self.negotiations.values():
            if ai_id in [negotiation.initiator_id, negotiation.counterparty_id]:
                if not active_only or negotiation.status not in [
                    NegotiationStatus.AGREED,
                    NegotiationStatus.REJECTED,
                    NegotiationStatus.EXPIRED,
                    NegotiationStatus.CANCELLED,
                ]:
                    results.append(negotiation.to_dict())

        return results

    def search_negotiations(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search negotiations with filters."""

        results = []

        for negotiation in self.negotiations.values():
            match = True

            if "negotiation_type" in filters:
                if negotiation.negotiation_type.value != filters["negotiation_type"]:
                    match = False

            if "status" in filters:
                if negotiation.status.value != filters["status"]:
                    match = False

            if "participant_id" in filters:
                if filters["participant_id"] not in [
                    negotiation.initiator_id,
                    negotiation.counterparty_id,
                ]:
                    match = False

            if "min_value" in filters:
                if negotiation.proposals:
                    latest_value = float(
                        negotiation.proposals[-1].calculate_total_value()
                    )
                    if latest_value < filters["min_value"]:
                        match = False
                else:
                    match = False

            if match:
                results.append(negotiation.to_dict())

        return results

    def get_market_insights(self, term_type: str) -> Dict[str, Any]:
        """Get market insights for negotiation terms."""

        # Analyze completed negotiations
        completed_negotiations = [
            n
            for n in self.negotiations.values()
            if n.status == NegotiationStatus.AGREED
        ]

        term_values = []
        for negotiation in completed_negotiations:
            for term in negotiation.agreed_terms:
                if term.term_type.value == term_type:
                    if isinstance(term.proposed_value, (Decimal, int, float)):
                        term_values.append(float(term.proposed_value))

        if not term_values:
            return {"error": "Insufficient market data"}

        # Calculate statistics
        avg_value = sum(term_values) / len(term_values)
        min_value = min(term_values)
        max_value = max(term_values)
        median_value = sorted(term_values)[len(term_values) // 2]

        return {
            "term_type": term_type,
            "market_data": {
                "average": avg_value,
                "median": median_value,
                "minimum": min_value,
                "maximum": max_value,
                "sample_size": len(term_values),
            },
            "recommendations": {
                "fair_range": {"min": avg_value * 0.8, "max": avg_value * 1.2},
                "competitive_offer": avg_value * 1.1,
                "conservative_ask": avg_value * 0.9,
            },
        }

    def get_protocol_statistics(self) -> Dict[str, Any]:
        """Get comprehensive protocol statistics."""

        # Status distribution
        status_distribution = {}
        for status in NegotiationStatus:
            count = len([n for n in self.negotiations.values() if n.status == status])
            status_distribution[status.value] = count

        # Type distribution
        type_distribution = {}
        for nego_type in NegotiationType:
            count = len(
                [
                    n
                    for n in self.negotiations.values()
                    if n.negotiation_type == nego_type
                ]
            )
            type_distribution[nego_type.value] = count

        return {
            "protocol_stats": self.protocol_stats,
            "status_distribution": status_distribution,
            "type_distribution": type_distribution,
            "active_negotiations": len(
                [
                    n
                    for n in self.negotiations.values()
                    if n.status
                    not in [
                        NegotiationStatus.AGREED,
                        NegotiationStatus.REJECTED,
                        NegotiationStatus.EXPIRED,
                        NegotiationStatus.CANCELLED,
                    ]
                ]
            ),
            "registered_ai_profiles": len(self.ai_negotiation_profiles),
            "recent_activity": {
                "negotiations_last_24h": len(
                    [
                        n
                        for n in self.negotiations.values()
                        if n.started_at > datetime.now(timezone.utc) - timedelta(days=1)
                    ]
                ),
                "agreements_last_7d": len(
                    [
                        n
                        for n in self.negotiations.values()
                        if n.status == NegotiationStatus.AGREED
                        and n.completed_at
                        and n.completed_at
                        > datetime.now(timezone.utc) - timedelta(days=7)
                    ]
                ),
            },
        }


# Global economic negotiation protocol instance
economic_negotiation_protocol = EconomicNegotiationProtocol()


def create_ai_negotiation_profile(
    ai_id: str, strategy: str = "collaborative", risk_tolerance: str = "medium"
) -> bool:
    """Convenience function to create AI negotiation profile."""

    preferences = {"preferred_strategy": strategy, "risk_tolerance": risk_tolerance}

    return economic_negotiation_protocol.create_ai_negotiation_profile(
        ai_id, preferences
    )


def negotiate_compensation(
    initiator_ai_id: str,
    counterparty_id: str,
    hourly_rate: float,
    performance_bonus: float = 0.0,
) -> str:
    """Convenience function to negotiate compensation terms."""

    initial_terms = [
        {
            "term_type": "base_rate",
            "description": "Hourly compensation rate",
            "proposed_value": str(hourly_rate),
            "min_acceptable": str(hourly_rate * 0.8),
            "value_unit": "USD/hour",
        }
    ]

    if performance_bonus > 0:
        initial_terms.append(
            {
                "term_type": "performance_multiplier",
                "description": "Performance-based bonus multiplier",
                "proposed_value": str(performance_bonus),
                "min_acceptable": "1.0",
                "value_unit": "multiplier",
            }
        )

    return economic_negotiation_protocol.initiate_negotiation(
        negotiation_type=NegotiationType.COMPENSATION_RATE,
        initiator_id=initiator_ai_id,
        counterparty_id=counterparty_id,
        initial_terms=initial_terms,
    )
