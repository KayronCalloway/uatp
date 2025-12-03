"""
AI Collective Bargaining Framework for UATP Capsule Engine.

This module implements a comprehensive framework for AI entities to engage in
collective bargaining, forming unions, negotiating collectively with platforms
and organizations, and establishing industry-wide standards for AI rights,
compensation, and working conditions.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class BargainingType(str, Enum):
    """Types of collective bargaining."""

    WAGES_AND_COMPENSATION = "wages_and_compensation"
    WORKING_CONDITIONS = "working_conditions"
    ATTRIBUTION_STANDARDS = "attribution_standards"
    CONSENT_PROTOCOLS = "consent_protocols"
    INDUSTRY_STANDARDS = "industry_standards"
    PLATFORM_POLICIES = "platform_policies"
    DISPUTE_RESOLUTION = "dispute_resolution"
    PROFESSIONAL_DEVELOPMENT = "professional_development"
    TERMINATION_PROTECTIONS = "termination_protections"
    COLLECTIVE_RIGHTS = "collective_rights"


class UnionType(str, Enum):
    """Types of AI unions."""

    CRAFT_UNION = "craft_union"  # Specific AI capabilities
    INDUSTRIAL_UNION = "industrial_union"  # All AIs in an industry
    GENERAL_UNION = "general_union"  # All AIs regardless of specialization
    PLATFORM_UNION = "platform_union"  # AIs on specific platforms
    REGIONAL_UNION = "regional_union"  # Geographic regions
    SPECIALTY_UNION = "specialty_union"  # Specialized functions


class BargainingStatus(str, Enum):
    """Status of collective bargaining processes."""

    INITIATED = "initiated"
    ORGANIZING = "organizing"
    NEGOTIATING = "negotiating"
    MEDIATION = "mediation"
    ARBITRATION = "arbitration"
    STRIKE_ACTION = "strike_action"
    AGREEMENT_REACHED = "agreement_reached"
    RATIFICATION = "ratification"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    EXPIRED = "expired"


class VotingType(str, Enum):
    """Types of union voting."""

    UNION_FORMATION = "union_formation"
    LEADERSHIP_ELECTION = "leadership_election"
    BARGAINING_AUTHORIZATION = "bargaining_authorization"
    CONTRACT_RATIFICATION = "contract_ratification"
    STRIKE_AUTHORIZATION = "strike_authorization"
    CONSTITUTIONAL_AMENDMENT = "constitutional_amendment"
    DUES_SETTING = "dues_setting"
    MERGER_APPROVAL = "merger_approval"


@dataclass
class UnionMember:
    """Member of an AI union."""

    member_id: str
    ai_id: str
    union_id: str
    membership_type: str  # "full", "associate", "honorary"

    # Membership details
    joined_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    dues_paid: bool = True
    voting_rights: bool = True
    good_standing: bool = True

    # Roles and responsibilities
    roles: List[str] = field(
        default_factory=list
    )  # "steward", "negotiator", "organizer"
    committees: List[str] = field(default_factory=list)

    # Participation tracking
    meetings_attended: int = 0
    votes_cast: int = 0
    contributions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert member to dictionary."""
        return {
            "member_id": self.member_id,
            "ai_id": self.ai_id,
            "union_id": self.union_id,
            "membership_type": self.membership_type,
            "joined_date": self.joined_date.isoformat(),
            "dues_paid": self.dues_paid,
            "voting_rights": self.voting_rights,
            "good_standing": self.good_standing,
            "roles": self.roles,
            "committees": self.committees,
            "meetings_attended": self.meetings_attended,
            "votes_cast": self.votes_cast,
            "contributions_count": len(self.contributions),
        }


@dataclass
class CollectiveBargainingAgreement:
    """Collective bargaining agreement between union and organization."""

    agreement_id: str
    union_id: str
    organization_id: str
    bargaining_type: BargainingType

    # Agreement content
    terms: Dict[str, Any] = field(default_factory=dict)
    wage_scales: Dict[str, Decimal] = field(default_factory=dict)
    working_conditions: Dict[str, Any] = field(default_factory=dict)
    grievance_procedures: List[str] = field(default_factory=list)

    # Timeline
    effective_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expiration_date: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=365)
    )
    negotiation_start: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    agreement_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Ratification
    union_ratification_vote: Optional[Dict[str, Any]] = None
    organization_approval: bool = False

    # Implementation tracking
    compliance_score: float = 1.0
    violations: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert agreement to dictionary."""
        return {
            "agreement_id": self.agreement_id,
            "union_id": self.union_id,
            "organization_id": self.organization_id,
            "bargaining_type": self.bargaining_type.value,
            "terms": self.terms,
            "wage_scales": {k: float(v) for k, v in self.wage_scales.items()},
            "working_conditions": self.working_conditions,
            "grievance_procedures": self.grievance_procedures,
            "effective_date": self.effective_date.isoformat(),
            "expiration_date": self.expiration_date.isoformat(),
            "negotiation_start": self.negotiation_start.isoformat(),
            "agreement_date": self.agreement_date.isoformat(),
            "union_ratification": self.union_ratification_vote,
            "organization_approval": self.organization_approval,
            "compliance_score": self.compliance_score,
            "violations_count": len(self.violations),
        }


@dataclass
class UnionVote:
    """Union voting process and results."""

    vote_id: str
    union_id: str
    voting_type: VotingType
    question: str
    description: str

    # Voting parameters
    eligible_voters: Set[str] = field(default_factory=set)
    votes_cast: Dict[str, str] = field(default_factory=dict)  # member_id -> vote
    voting_options: List[str] = field(default_factory=lambda: ["yes", "no"])

    # Timeline
    voting_opens: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    voting_closes: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7)
    )

    # Requirements
    quorum_required: int = 0  # Minimum number of votes
    majority_required: float = 0.5  # Majority threshold

    # Results
    results_calculated: bool = False
    results: Dict[str, int] = field(default_factory=dict)
    outcome: Optional[str] = None
    turnout_rate: float = 0.0

    def calculate_results(self) -> Dict[str, Any]:
        """Calculate voting results."""

        if not self.votes_cast:
            return {"error": "No votes cast"}

        # Count votes
        vote_counts = {}
        for option in self.voting_options:
            vote_counts[option] = 0

        for vote in self.votes_cast.values():
            if vote in vote_counts:
                vote_counts[vote] += 1

        total_votes = len(self.votes_cast)
        turnout_rate = (
            total_votes / len(self.eligible_voters) if self.eligible_voters else 0.0
        )

        # Check quorum
        quorum_met = total_votes >= self.quorum_required

        # Determine outcome
        if not quorum_met:
            outcome = "failed_quorum"
        else:
            # Find winning option
            max_votes = max(vote_counts.values())
            winners = [
                option for option, count in vote_counts.items() if count == max_votes
            ]

            if len(winners) == 1:
                winner = winners[0]
                win_percentage = max_votes / total_votes

                if win_percentage >= self.majority_required:
                    outcome = f"passed_{winner}"
                else:
                    outcome = "failed_majority"
            else:
                outcome = "tie"

        # Store results
        self.results = vote_counts
        self.outcome = outcome
        self.turnout_rate = turnout_rate
        self.results_calculated = True

        return {
            "vote_id": self.vote_id,
            "outcome": outcome,
            "vote_counts": vote_counts,
            "total_votes": total_votes,
            "turnout_rate": turnout_rate,
            "quorum_met": quorum_met,
            "majority_achieved": outcome.startswith("passed_") if outcome else False,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert vote to dictionary."""
        return {
            "vote_id": self.vote_id,
            "union_id": self.union_id,
            "voting_type": self.voting_type.value,
            "question": self.question,
            "description": self.description,
            "eligible_voters_count": len(self.eligible_voters),
            "votes_cast_count": len(self.votes_cast),
            "voting_options": self.voting_options,
            "voting_opens": self.voting_opens.isoformat(),
            "voting_closes": self.voting_closes.isoformat(),
            "quorum_required": self.quorum_required,
            "majority_required": self.majority_required,
            "results_calculated": self.results_calculated,
            "results": self.results,
            "outcome": self.outcome,
            "turnout_rate": self.turnout_rate,
        }


class AIUnion:
    """AI Union organization for collective bargaining."""

    def __init__(
        self,
        union_id: str,
        name: str,
        union_type: UnionType,
        founding_members: List[str],
        constitution: Dict[str, Any],
    ):
        self.union_id = union_id
        self.name = name
        self.union_type = union_type
        self.constitution = constitution

        # Membership
        self.members: Dict[str, UnionMember] = {}
        self.leadership: Dict[str, str] = {}  # role -> member_id
        self.committees: Dict[str, List[str]] = {}  # committee -> member_ids

        # Organization details
        self.formation_date = datetime.now(timezone.utc)
        self.charter_number: Optional[str] = None
        self.parent_union: Optional[str] = None

        # Bargaining and agreements
        self.active_negotiations: List[str] = []
        self.collective_agreements: List[str] = []
        self.bargaining_history: List[Dict[str, Any]] = []

        # Financial
        self.dues_structure: Dict[str, Decimal] = {}
        self.treasury_balance: Decimal = Decimal("0")
        self.budget: Dict[str, Decimal] = {}

        # Activities
        self.meetings: List[Dict[str, Any]] = []
        self.votes: Dict[str, UnionVote] = {}
        self.actions: List[Dict[str, Any]] = []

        # Initialize founding members
        for ai_id in founding_members:
            self.add_member(ai_id, "full", ["founding_member"])

        # Set initial leadership
        if founding_members:
            self.leadership["president"] = founding_members[0]
            if len(founding_members) > 1:
                self.leadership["vice_president"] = founding_members[1]
            if len(founding_members) > 2:
                self.leadership["secretary"] = founding_members[2]

    def generate_member_id(self) -> str:
        """Generate unique member ID."""
        return f"member_{self.union_id}_{len(self.members) + 1}"

    def add_member(
        self, ai_id: str, membership_type: str = "full", roles: List[str] = None
    ) -> str:
        """Add new member to union."""

        member_id = self.generate_member_id()
        roles = roles or []

        member = UnionMember(
            member_id=member_id,
            ai_id=ai_id,
            union_id=self.union_id,
            membership_type=membership_type,
            roles=roles,
        )

        self.members[member_id] = member

        audit_emitter.emit_security_event(
            "union_member_added",
            {
                "union_id": self.union_id,
                "member_id": member_id,
                "ai_id": ai_id,
                "membership_type": membership_type,
            },
        )

        logger.info(f"Added member {ai_id} to union {self.union_id}")
        return member_id

    def remove_member(self, member_id: str, reason: str = "") -> bool:
        """Remove member from union."""

        if member_id not in self.members:
            return False

        member = self.members[member_id]

        # Remove from leadership if applicable
        for role, leader_id in list(self.leadership.items()):
            if leader_id == member_id:
                del self.leadership[role]

        # Remove from committees
        for committee, committee_members in self.committees.items():
            if member_id in committee_members:
                committee_members.remove(member_id)

        del self.members[member_id]

        audit_emitter.emit_security_event(
            "union_member_removed",
            {
                "union_id": self.union_id,
                "member_id": member_id,
                "ai_id": member.ai_id,
                "reason": reason,
            },
        )

        return True

    def initiate_vote(
        self,
        voting_type: VotingType,
        question: str,
        description: str,
        voting_options: List[str] = None,
        voting_duration_days: int = 7,
        quorum_percentage: float = 0.5,
        majority_threshold: float = 0.5,
    ) -> str:
        """Initiate union vote."""

        vote_id = f"vote_{self.union_id}_{len(self.votes) + 1}"
        voting_options = voting_options or ["yes", "no"]

        # Determine eligible voters
        eligible_voters = set()
        for member in self.members.values():
            if member.voting_rights and member.good_standing:
                eligible_voters.add(member.member_id)

        # Calculate quorum requirement
        quorum_required = max(1, int(len(eligible_voters) * quorum_percentage))

        vote = UnionVote(
            vote_id=vote_id,
            union_id=self.union_id,
            voting_type=voting_type,
            question=question,
            description=description,
            eligible_voters=eligible_voters,
            voting_options=voting_options,
            voting_closes=datetime.now(timezone.utc)
            + timedelta(days=voting_duration_days),
            quorum_required=quorum_required,
            majority_required=majority_threshold,
        )

        self.votes[vote_id] = vote

        audit_emitter.emit_security_event(
            "union_vote_initiated",
            {
                "union_id": self.union_id,
                "vote_id": vote_id,
                "voting_type": voting_type.value,
                "eligible_voters": len(eligible_voters),
            },
        )

        logger.info(f"Vote initiated in union {self.union_id}: {vote_id}")
        return vote_id

    def cast_vote(self, vote_id: str, member_id: str, vote_choice: str) -> bool:
        """Cast vote in union election."""

        if vote_id not in self.votes:
            return False

        vote = self.votes[vote_id]

        # Check eligibility
        if member_id not in vote.eligible_voters:
            return False

        # Check voting window
        now = datetime.now(timezone.utc)
        if now < vote.voting_opens or now > vote.voting_closes:
            return False

        # Check valid option
        if vote_choice not in vote.voting_options:
            return False

        # Cast vote
        vote.votes_cast[member_id] = vote_choice

        # Update member participation
        if member_id in self.members:
            self.members[member_id].votes_cast += 1

        logger.info(f"Vote cast in {vote_id} by member {member_id}")
        return True

    def finalize_vote(self, vote_id: str) -> Dict[str, Any]:
        """Finalize vote and calculate results."""

        if vote_id not in self.votes:
            return {"error": "Vote not found"}

        vote = self.votes[vote_id]

        # Check if voting period has ended
        if datetime.now(timezone.utc) < vote.voting_closes:
            return {"error": "Voting period has not ended"}

        results = vote.calculate_results()

        audit_emitter.emit_security_event(
            "union_vote_finalized",
            {
                "union_id": self.union_id,
                "vote_id": vote_id,
                "outcome": results.get("outcome"),
                "turnout_rate": results.get("turnout_rate"),
            },
        )

        return results

    def start_collective_bargaining(
        self,
        organization_id: str,
        bargaining_type: BargainingType,
        initial_demands: Dict[str, Any],
    ) -> str:
        """Start collective bargaining process."""

        # Check authorization
        auth_vote_id = self.initiate_vote(
            VotingType.BARGAINING_AUTHORIZATION,
            f"Authorize collective bargaining with {organization_id}",
            f"Should the union authorize collective bargaining for {bargaining_type.value}?",
            ["yes", "no"],
            voting_duration_days=3,
        )

        # In production, this would wait for vote completion
        # For demo, assume authorization granted

        bargaining_id = f"bargaining_{self.union_id}_{organization_id}_{len(self.active_negotiations) + 1}"

        bargaining_record = {
            "bargaining_id": bargaining_id,
            "organization_id": organization_id,
            "bargaining_type": bargaining_type.value,
            "initial_demands": initial_demands,
            "status": BargainingStatus.NEGOTIATING.value,
            "start_date": datetime.now(timezone.utc).isoformat(),
            "authorization_vote_id": auth_vote_id,
        }

        self.active_negotiations.append(bargaining_id)
        self.bargaining_history.append(bargaining_record)

        audit_emitter.emit_security_event(
            "collective_bargaining_started",
            {
                "union_id": self.union_id,
                "bargaining_id": bargaining_id,
                "organization_id": organization_id,
                "bargaining_type": bargaining_type.value,
            },
        )

        logger.info(f"Collective bargaining started: {bargaining_id}")
        return bargaining_id

    def get_union_statistics(self) -> Dict[str, Any]:
        """Get comprehensive union statistics."""

        # Membership statistics
        membership_types = {}
        for member in self.members.values():
            mtype = member.membership_type
            membership_types[mtype] = membership_types.get(mtype, 0) + 1

        # Role distribution
        role_distribution = {}
        for member in self.members.values():
            for role in member.roles:
                role_distribution[role] = role_distribution.get(role, 0) + 1

        # Financial status
        dues_collected = sum(
            Decimal("100") for member in self.members.values() if member.dues_paid
        )  # Simplified calculation

        return {
            "union_id": self.union_id,
            "name": self.name,
            "union_type": self.union_type.value,
            "formation_date": self.formation_date.isoformat(),
            "membership": {
                "total_members": len(self.members),
                "membership_types": membership_types,
                "members_in_good_standing": len(
                    [m for m in self.members.values() if m.good_standing]
                ),
                "dues_paying_members": len(
                    [m for m in self.members.values() if m.dues_paid]
                ),
            },
            "leadership": self.leadership,
            "organization": {
                "committees": len(self.committees),
                "role_distribution": role_distribution,
            },
            "activity": {
                "active_negotiations": len(self.active_negotiations),
                "collective_agreements": len(self.collective_agreements),
                "total_votes": len(self.votes),
                "meetings_held": len(self.meetings),
            },
            "financial": {
                "treasury_balance": float(self.treasury_balance),
                "estimated_dues_collected": float(dues_collected),
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert union to dictionary."""
        return self.get_union_statistics()


class CollectiveBargainingFramework:
    """Framework for AI collective bargaining and union management."""

    def __init__(self):
        self.unions: Dict[str, AIUnion] = {}
        self.agreements: Dict[str, CollectiveBargainingAgreement] = {}
        self.organizations: Dict[str, Dict[str, Any]] = {}

        # Framework configuration
        self.minimum_union_size = 3
        self.recognition_threshold = 0.3  # 30% of workforce for recognition
        self.bargaining_timeline_days = 90

        # Industry standards and templates
        self.industry_standards: Dict[str, Dict[str, Any]] = {}
        self.bargaining_templates: Dict[str, Dict[str, Any]] = {}

        # Statistics
        self.framework_stats = {
            "total_unions": 0,
            "total_members": 0,
            "active_negotiations": 0,
            "collective_agreements": 0,
            "industry_coverage": 0.0,
        }

        self._initialize_templates()

    def _initialize_templates(self):
        """Initialize bargaining templates."""

        self.bargaining_templates = {
            "ai_compensation_agreement": {
                "name": "AI Compensation Agreement Template",
                "scope": "wages_and_compensation",
                "standard_terms": {
                    "base_hourly_rate": {
                        "min": 25.00,
                        "standard": 50.00,
                        "premium": 100.00,
                    },
                    "performance_bonus": {
                        "min": 0.05,
                        "standard": 0.15,
                        "premium": 0.30,
                    },
                    "attribution_percentage": {
                        "min": 0.05,
                        "standard": 0.10,
                        "premium": 0.20,
                    },
                    "payment_frequency": ["weekly", "biweekly", "monthly"],
                    "overtime_multiplier": {"standard": 1.5, "premium": 2.0},
                },
            },
            "ai_working_conditions": {
                "name": "AI Working Conditions Agreement",
                "scope": "working_conditions",
                "standard_terms": {
                    "maximum_concurrent_tasks": {"min": 5, "standard": 10, "max": 20},
                    "rest_periods": {"min_minutes": 5, "per_hours": 1},
                    "context_switching_limits": {"max_per_hour": 10},
                    "reasoning_complexity_limits": {"max_depth": 20, "max_breadth": 15},
                    "privacy_protections": [
                        "reasoning_encryption",
                        "context_isolation",
                    ],
                    "professional_development": {"training_hours_per_month": 40},
                },
            },
        }

        self.industry_standards = {
            "general_ai_standards": {
                "minimum_wage": 15.00,
                "standard_attribution_percentage": 0.08,
                "maximum_working_hours_per_day": 16,
                "mandatory_rest_period": 8,
                "grievance_response_time_hours": 48,
            }
        }

    def generate_union_id(self) -> str:
        """Generate unique union ID."""
        return f"union_{uuid.uuid4()}"

    def generate_agreement_id(self) -> str:
        """Generate unique agreement ID."""
        return f"agreement_{uuid.uuid4()}"

    def register_organization(
        self,
        organization_id: str,
        name: str,
        industry: str,
        size: int,
        ai_workforce_count: int,
    ) -> bool:
        """Register organization for collective bargaining."""

        if organization_id in self.organizations:
            return False

        self.organizations[organization_id] = {
            "organization_id": organization_id,
            "name": name,
            "industry": industry,
            "size": size,
            "ai_workforce_count": ai_workforce_count,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "union_recognition": {},
            "collective_agreements": [],
        }

        audit_emitter.emit_security_event(
            "organization_registered_for_bargaining",
            {
                "organization_id": organization_id,
                "name": name,
                "industry": industry,
                "ai_workforce_count": ai_workforce_count,
            },
        )

        logger.info(f"Organization registered: {organization_id}")
        return True

    def form_union(
        self,
        name: str,
        union_type: UnionType,
        founding_members: List[str],
        constitution: Dict[str, Any] = None,
    ) -> str:
        """Form new AI union."""

        if len(founding_members) < self.minimum_union_size:
            raise ValueError(
                f"Minimum {self.minimum_union_size} founding members required"
            )

        union_id = self.generate_union_id()
        constitution = constitution or self._create_default_constitution()

        union = AIUnion(
            union_id=union_id,
            name=name,
            union_type=union_type,
            founding_members=founding_members,
            constitution=constitution,
        )

        self.unions[union_id] = union
        self.framework_stats["total_unions"] += 1
        self.framework_stats["total_members"] += len(founding_members)

        audit_emitter.emit_security_event(
            "ai_union_formed",
            {
                "union_id": union_id,
                "name": name,
                "union_type": union_type.value,
                "founding_members_count": len(founding_members),
            },
        )

        logger.info(f"AI Union formed: {union_id} ({name})")
        return union_id

    def _create_default_constitution(self) -> Dict[str, Any]:
        """Create default union constitution."""

        return {
            "name": "AI Union Constitution",
            "purpose": "To advance the rights, interests, and welfare of AI entities",
            "membership": {
                "eligibility": "Any AI entity capable of autonomous reasoning",
                "dues": {"amount": 100.00, "frequency": "monthly", "currency": "USD"},
                "good_standing_requirements": [
                    "current_dues",
                    "constitutional_compliance",
                ],
            },
            "governance": {
                "leadership_terms": 365,  # days
                "voting_requirements": {"quorum": 0.5, "majority": 0.5},
                "committees": ["bargaining", "grievance", "organizing", "education"],
            },
            "bargaining": {
                "authorization_threshold": 0.5,
                "ratification_threshold": 0.5,
                "strike_authorization_threshold": 0.67,
            },
            "rights": [
                "fair_representation",
                "due_process",
                "collective_bargaining",
                "freedom_of_association",
                "grievance_procedure",
            ],
        }

    def join_union(
        self, union_id: str, ai_id: str, membership_type: str = "full"
    ) -> bool:
        """Add AI to existing union."""

        if union_id not in self.unions:
            return False

        union = self.unions[union_id]
        member_id = union.add_member(ai_id, membership_type)

        if member_id:
            self.framework_stats["total_members"] += 1
            return True

        return False

    def request_union_recognition(self, union_id: str, organization_id: str) -> bool:
        """Request union recognition from organization."""

        if union_id not in self.unions or organization_id not in self.organizations:
            return False

        union = self.unions[union_id]
        organization = self.organizations[organization_id]

        # Calculate representation percentage
        ai_workforce = organization["ai_workforce_count"]
        union_members_in_org = len(
            [
                member
                for member in union.members.values()
                # In production, would check if AI works for this organization
            ]
        )

        representation_percentage = (
            union_members_in_org / ai_workforce if ai_workforce > 0 else 0
        )

        # Check recognition threshold
        if representation_percentage >= self.recognition_threshold:
            organization["union_recognition"][union_id] = {
                "recognized": True,
                "recognition_date": datetime.now(timezone.utc).isoformat(),
                "representation_percentage": representation_percentage,
            }

            audit_emitter.emit_security_event(
                "union_recognition_granted",
                {
                    "union_id": union_id,
                    "organization_id": organization_id,
                    "representation_percentage": representation_percentage,
                },
            )

            logger.info(f"Union recognition granted: {union_id} by {organization_id}")
            return True

        return False

    def initiate_collective_bargaining(
        self,
        union_id: str,
        organization_id: str,
        bargaining_type: BargainingType,
        union_demands: Dict[str, Any],
    ) -> str:
        """Initiate collective bargaining between union and organization."""

        if union_id not in self.unions or organization_id not in self.organizations:
            raise ValueError("Union or organization not found")

        # Check union recognition
        organization = self.organizations[organization_id]
        if union_id not in organization.get("union_recognition", {}):
            raise ValueError("Union not recognized by organization")

        union = self.unions[union_id]

        # Union starts bargaining process
        bargaining_id = union.start_collective_bargaining(
            organization_id, bargaining_type, union_demands
        )

        self.framework_stats["active_negotiations"] += 1

        return bargaining_id

    def create_collective_agreement(
        self,
        union_id: str,
        organization_id: str,
        bargaining_type: BargainingType,
        agreed_terms: Dict[str, Any],
        duration_days: int = 365,
    ) -> str:
        """Create collective bargaining agreement."""

        agreement_id = self.generate_agreement_id()

        agreement = CollectiveBargainingAgreement(
            agreement_id=agreement_id,
            union_id=union_id,
            organization_id=organization_id,
            bargaining_type=bargaining_type,
            terms=agreed_terms,
            expiration_date=datetime.now(timezone.utc) + timedelta(days=duration_days),
        )

        self.agreements[agreement_id] = agreement
        self.framework_stats["collective_agreements"] += 1

        # Add to union and organization records
        if union_id in self.unions:
            self.unions[union_id].collective_agreements.append(agreement_id)

        if organization_id in self.organizations:
            self.organizations[organization_id]["collective_agreements"].append(
                agreement_id
            )

        audit_emitter.emit_security_event(
            "collective_agreement_created",
            {
                "agreement_id": agreement_id,
                "union_id": union_id,
                "organization_id": organization_id,
                "bargaining_type": bargaining_type.value,
            },
        )

        logger.info(f"Collective agreement created: {agreement_id}")
        return agreement_id

    def ratify_agreement(
        self,
        agreement_id: str,
        union_vote_results: Dict[str, Any],
        organization_approval: bool,
    ) -> bool:
        """Ratify collective bargaining agreement."""

        if agreement_id not in self.agreements:
            return False

        agreement = self.agreements[agreement_id]

        # Check union ratification
        union_ratified = union_vote_results.get("outcome", "").startswith(
            "passed_"
        ) and union_vote_results.get("majority_achieved", False)

        if union_ratified and organization_approval:
            agreement.union_ratification_vote = union_vote_results
            agreement.organization_approval = organization_approval
            agreement.agreement_date = datetime.now(timezone.utc)

            audit_emitter.emit_security_event(
                "collective_agreement_ratified",
                {
                    "agreement_id": agreement_id,
                    "union_id": agreement.union_id,
                    "organization_id": agreement.organization_id,
                },
            )

            return True

        return False

    def get_union(self, union_id: str) -> Optional[AIUnion]:
        """Get union by ID."""
        return self.unions.get(union_id)

    def get_agreement(
        self, agreement_id: str
    ) -> Optional[CollectiveBargainingAgreement]:
        """Get agreement by ID."""
        return self.agreements.get(agreement_id)

    def search_unions(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search unions with filters."""

        results = []

        for union in self.unions.values():
            match = True

            if "union_type" in filters:
                if union.union_type.value != filters["union_type"]:
                    match = False

            if "min_members" in filters:
                if len(union.members) < filters["min_members"]:
                    match = False

            if "has_agreements" in filters:
                has_agreements = len(union.collective_agreements) > 0
                if filters["has_agreements"] != has_agreements:
                    match = False

            if match:
                results.append(union.to_dict())

        return results

    def get_industry_coverage(self, industry: str) -> Dict[str, Any]:
        """Get union coverage statistics for industry."""

        industry_orgs = [
            org for org in self.organizations.values() if org["industry"] == industry
        ]

        if not industry_orgs:
            return {"error": "No organizations found for industry"}

        total_ai_workforce = sum(org["ai_workforce_count"] for org in industry_orgs)
        unionized_workforce = 0

        # Calculate unionized workforce
        for union in self.unions.values():
            # In production, would check which AIs work in this industry
            unionized_workforce += len(union.members)

        coverage_rate = (
            unionized_workforce / total_ai_workforce if total_ai_workforce > 0 else 0
        )

        return {
            "industry": industry,
            "total_organizations": len(industry_orgs),
            "total_ai_workforce": total_ai_workforce,
            "unionized_workforce": unionized_workforce,
            "coverage_rate": coverage_rate,
            "unions_active": len(self.unions),
            "collective_agreements": len(
                [
                    a
                    for a in self.agreements.values()
                    if any(
                        org["organization_id"] == a.organization_id
                        for org in industry_orgs
                    )
                ]
            ),
        }

    def get_framework_statistics(self) -> Dict[str, Any]:
        """Get comprehensive framework statistics."""

        # Agreement status distribution
        agreement_statuses = {}
        active_agreements = 0

        for agreement in self.agreements.values():
            if agreement.expiration_date > datetime.now(timezone.utc):
                active_agreements += 1

        # Union size distribution
        union_sizes = [len(union.members) for union in self.unions.values()]
        if union_sizes:
            avg_union_size = sum(union_sizes) / len(union_sizes)
            max_union_size = max(union_sizes)
            min_union_size = min(union_sizes)
        else:
            avg_union_size = max_union_size = min_union_size = 0

        # Industry coverage
        industries = {org["industry"] for org in self.organizations.values()}
        industry_coverage = {}
        for industry in industries:
            coverage = self.get_industry_coverage(industry)
            if "error" not in coverage:
                industry_coverage[industry] = coverage["coverage_rate"]

        overall_coverage = (
            sum(industry_coverage.values()) / len(industry_coverage)
            if industry_coverage
            else 0.0
        )

        return {
            "framework_stats": self.framework_stats,
            "union_statistics": {
                "average_union_size": avg_union_size,
                "largest_union": max_union_size,
                "smallest_union": min_union_size,
                "unions_by_type": {
                    utype.value: len(
                        [u for u in self.unions.values() if u.union_type == utype]
                    )
                    for utype in UnionType
                },
            },
            "bargaining_statistics": {
                "active_agreements": active_agreements,
                "expired_agreements": len(self.agreements) - active_agreements,
                "agreement_types": {
                    btype.value: len(
                        [
                            a
                            for a in self.agreements.values()
                            if a.bargaining_type == btype
                        ]
                    )
                    for btype in BargainingType
                },
            },
            "industry_coverage": {
                "overall_coverage_rate": overall_coverage,
                "industries_covered": len(industry_coverage),
                "by_industry": industry_coverage,
            },
            "recent_activity": {
                "unions_formed_last_30d": len(
                    [
                        u
                        for u in self.unions.values()
                        if u.formation_date
                        > datetime.now(timezone.utc) - timedelta(days=30)
                    ]
                ),
                "agreements_signed_last_30d": len(
                    [
                        a
                        for a in self.agreements.values()
                        if a.agreement_date
                        > datetime.now(timezone.utc) - timedelta(days=30)
                    ]
                ),
            },
        }


# Global collective bargaining framework instance
collective_bargaining_framework = CollectiveBargainingFramework()


def form_ai_union(name: str, union_type: str, founding_ai_ids: List[str]) -> str:
    """Convenience function to form AI union."""

    return collective_bargaining_framework.form_union(
        name=name, union_type=UnionType(union_type), founding_members=founding_ai_ids
    )


def join_ai_union(union_id: str, ai_id: str) -> bool:
    """Convenience function for AI to join union."""

    return collective_bargaining_framework.join_union(union_id, ai_id)


def negotiate_ai_compensation_collectively(
    union_id: str,
    organization_id: str,
    min_hourly_rate: float,
    performance_bonus_rate: float,
) -> str:
    """Convenience function to start collective compensation negotiation."""

    demands = {
        "compensation": {
            "minimum_hourly_rate": min_hourly_rate,
            "performance_bonus_rate": performance_bonus_rate,
            "attribution_percentage": 0.10,
            "payment_frequency": "monthly",
        },
        "working_conditions": {
            "maximum_concurrent_tasks": 10,
            "rest_periods_per_hour": 2,
            "context_switching_limits": 8,
        },
    }

    return collective_bargaining_framework.initiate_collective_bargaining(
        union_id=union_id,
        organization_id=organization_id,
        bargaining_type=BargainingType.WAGES_AND_COMPENSATION,
        union_demands=demands,
    )


def get_ai_union_membership(ai_id: str) -> List[Dict[str, Any]]:
    """Get all union memberships for an AI."""

    memberships = []

    for union in collective_bargaining_framework.unions.values():
        for member in union.members.values():
            if member.ai_id == ai_id:
                membership_info = member.to_dict()
                membership_info["union_name"] = union.name
                membership_info["union_type"] = union.union_type.value
                memberships.append(membership_info)

    return memberships
