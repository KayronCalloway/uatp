"""
Advanced Governance Capsule System for UATP Engine.
Implements decentralized decision-making, voting, and consensus mechanisms.
"""

import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from src.audit.events import audit_emitter
from src.crypto.post_quantum import pq_crypto

logger = logging.getLogger(__name__)


class ProposalType(str, Enum):
    """Types of governance proposals."""

    POLICY_CHANGE = "policy_change"
    SYSTEM_UPGRADE = "system_upgrade"
    RESOURCE_ALLOCATION = "resource_allocation"
    PARAMETER_UPDATE = "parameter_update"
    EMERGENCY_ACTION = "emergency_action"
    RULE_AMENDMENT = "rule_amendment"
    MEMBERSHIP_CHANGE = "membership_change"


class ProposalStatus(str, Enum):
    """Status of governance proposals."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    VOTING = "voting"
    PASSED = "passed"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"


class VoteType(str, Enum):
    """Types of votes."""

    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"


class VotingMethod(str, Enum):
    """Voting methods for proposals."""

    SIMPLE_MAJORITY = "simple_majority"
    SUPERMAJORITY = "supermajority"
    UNANIMOUS = "unanimous"
    QUADRATIC = "quadratic"
    WEIGHTED = "weighted"
    RANKED_CHOICE = "ranked_choice"


class ConsensusAlgorithm(str, Enum):
    """Consensus algorithms for decision making."""

    PROOF_OF_STAKE = "proof_of_stake"
    PROOF_OF_AUTHORITY = "proof_of_authority"
    DELEGATED_PROOF_OF_STAKE = "delegated_proof_of_stake"
    PRACTICAL_BYZANTINE_FAULT_TOLERANCE = "pbft"
    RAFT = "raft"


@dataclass
class Stakeholder:
    """Represents a stakeholder in the governance system."""

    stakeholder_id: str
    stake_amount: float
    reputation_score: float
    participation_rate: float
    joined_date: datetime
    last_activity: datetime
    delegated_to: Optional[str] = None
    is_validator: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def voting_power(self) -> float:
        """Calculate effective voting power based on stake, reputation, and participation."""
        base_power = self.stake_amount
        # Reputation contributes up to 2×; never fall below 0.1× so zero-rep doesn’t nullify power.
        reputation_multiplier = max(min(self.reputation_score / 100.0, 2.0), 0.1)
        # Participation up to 1.5×; floor at 0.1× so freshly-joined or inactive accounts still retain minimal weight.
        participation_multiplier = max(min(self.participation_rate, 1.5), 0.1)

        return base_power * reputation_multiplier * participation_multiplier

    def calculate_voting_power(self) -> float:
        """Calculate effective voting power based on stake, reputation, and participation."""
        return self.voting_power


@dataclass
class Vote:
    """Represents a vote on a proposal."""

    vote_id: str
    proposal_id: str
    voter_id: str
    vote_type: VoteType
    voting_power: float
    timestamp: datetime
    signature: str
    justification: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def verify_signature(self, public_key: str) -> bool:
        """Verify the vote signature."""
        vote_data = f"{self.proposal_id}:{self.voter_id}:{self.vote_type.value}:{self.timestamp.isoformat()}"
        return pq_crypto.dilithium_verify(
            vote_data.encode(), bytes.fromhex(self.signature), bytes.fromhex(public_key)
        )


@dataclass
class Proposal:
    """Represents a governance proposal."""

    proposal_id: str
    title: str
    description: str
    proposal_type: ProposalType
    proposer_id: str
    created_at: datetime
    voting_start: datetime
    voting_end: datetime
    voting_method: VotingMethod
    required_threshold: float
    status: ProposalStatus
    votes: List[Vote] = field(default_factory=list)
    execution_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_vote_tally(self) -> Dict[VoteType, float]:
        """Get current vote tally."""
        tally = {VoteType.FOR: 0.0, VoteType.AGAINST: 0.0, VoteType.ABSTAIN: 0.0}

        for vote in self.votes:
            tally[vote.vote_type] += vote.voting_power

        return tally

    def is_passed(self) -> bool:
        """Check if proposal has passed."""
        if self.status != ProposalStatus.VOTING:
            return self.status == ProposalStatus.PASSED

        tally = self.get_vote_tally()
        total_votes = sum(tally.values())

        if total_votes == 0:
            return False

        if self.voting_method == VotingMethod.SIMPLE_MAJORITY:
            return tally[VoteType.FOR] > tally[VoteType.AGAINST]
        elif self.voting_method == VotingMethod.SUPERMAJORITY:
            return tally[VoteType.FOR] / total_votes >= self.required_threshold
        elif self.voting_method == VotingMethod.UNANIMOUS:
            return tally[VoteType.AGAINST] == 0 and tally[VoteType.FOR] > 0

        return False

    def is_expired(self) -> bool:
        """Check if proposal has expired."""
        return datetime.now(timezone.utc) > self.voting_end


@dataclass
class GovernanceAction:
    """Represents an executed governance action."""

    action_id: str
    proposal_id: str
    action_type: str
    executor_id: str
    executed_at: datetime
    success: bool
    result: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConstitutionalFramework:
    """Enforces immutable constitutional principles."""

    IMMUTABLE_PRINCIPLES = [
        "Attribution rights are inalienable",
        "Transparency is mandatory",
        "Democratic participation is protected",
        "Economic justice is enforced",
        "Minority rights are protected",
        "Stake concentration limits cannot be overridden",
    ]

    CONSTITUTIONAL_PROPOSAL_TYPES = {
        ProposalType.RULE_AMENDMENT,
        ProposalType.SYSTEM_UPGRADE,
        ProposalType.PARAMETER_UPDATE,
    }

    @classmethod
    def validate_proposal_constitutionality(
        cls, proposal: "Proposal"
    ) -> Tuple[bool, Optional[str]]:
        """Check if proposal violates immutable principles."""
        if proposal.proposal_type in cls.CONSTITUTIONAL_PROPOSAL_TYPES:
            # Constitutional changes require supermajority
            if proposal.required_threshold < 0.75:
                return False, "Constitutional changes require 75% supermajority"

        # Check proposal content against immutable principles
        description_lower = proposal.description.lower()

        if "attribution" in description_lower and (
            "remove" in description_lower or "eliminate" in description_lower
        ):
            return (
                False,
                "Cannot remove attribution rights - violates immutable principle",
            )

        if "transparency" in description_lower and (
            "disable" in description_lower or "eliminate" in description_lower
        ):
            return False, "Cannot disable transparency - violates immutable principle"

        if (
            "stake" in description_lower
            and "concentration" in description_lower
            and "increase" in description_lower
        ):
            return (
                False,
                "Cannot increase stake concentration limits - violates immutable principle",
            )

        return True, None

    @classmethod
    def requires_judicial_review(cls, proposal: "Proposal") -> bool:
        """Check if proposal requires judicial review."""
        return proposal.proposal_type in cls.CONSTITUTIONAL_PROPOSAL_TYPES


class GovernanceDAOEngine:
    """Decentralized Autonomous Organization engine for governance."""

    # CRITICAL GOVERNANCE PROTECTION CONSTANTS
    MAX_INDIVIDUAL_VOTING_POWER = 0.15  # 15% maximum per individual
    MAX_COORDINATED_VOTING_POWER = 0.25  # 25% for known associates
    CONCENTRATION_CHECK_ENABLED = True
    MIN_REPUTATION_FOR_VOTING = 50.0  # Minimum reputation to vote
    MIN_STAKE_FOR_PROPOSAL = 1000.0  # Minimum stake to create proposals
    # Note: Sybil detection is enforced via dependency injection (no boolean flag)

    def __init__(self, sybil_detector: Optional["SybilDetector"] = None):
        """Initialize governance engine with dependency injection.

        Args:
            sybil_detector: SybilDetector implementation for stakeholder validation.
                          Defaults to RealSybilDetector() for production.
                          Tests can inject TestSybilDetector() or MockSybilDetector().
        """
        # Import here to avoid circular dependencies
        from src.security.sybil_detection import RealSybilDetector

        self.stakeholders: Dict[str, Stakeholder] = {}
        self.proposals: Dict[str, Proposal] = {}
        self.executed_actions: Dict[str, GovernanceAction] = {}
        self.governance_parameters = self._initialize_parameters()
        self.consensus_algorithm = ConsensusAlgorithm.PROOF_OF_STAKE
        self.governance_stats = {
            "total_proposals": 0,
            "passed_proposals": 0,
            "rejected_proposals": 0,
            "total_votes": 0,
            "unique_voters": 0,
        }
        self.constitutional_framework = ConstitutionalFramework()
        self.stake_groups: Dict[str, Set[str]] = {}  # Track coordinated stakeholders
        self.identity_verifications: Dict[
            str, Dict[str, Any]
        ] = {}  # Sybil resistance data
        self.voting_power_history: Dict[
            str, List[Tuple[datetime, float]]
        ] = {}  # Track power changes
        self.minority_protection_enabled = True

        # Dependency injection: Use provided detector or default to production implementation
        self.sybil_detector = sybil_detector or RealSybilDetector()

    def register_stakeholder(
        self,
        stakeholder_id: str,
        initial_stake: float,
        identity_proof: Optional[Dict[str, Any]] = None,
    ) -> Stakeholder:
        """Register a new stakeholder with identity verification."""

        # Sybil resistance checks using injected detector
        is_valid, reason = self.sybil_detector.check(stakeholder_id, identity_proof)
        if not is_valid:
            raise ValueError(f"Sybil resistance check failed: {reason}")

        # Enforce stake concentration limits
        concentration_check = self.enforce_voting_power_limits(
            stakeholder_id, initial_stake
        )
        if not concentration_check[0]:
            raise ValueError(
                f"Stake concentration limit violated: {concentration_check[1]}"
            )

        stakeholder = Stakeholder(
            stakeholder_id=stakeholder_id,
            stake_amount=initial_stake,
            reputation_score=100.0,  # Starting reputation
            participation_rate=1.0,  # Assume new stakeholders intend to participate; start at 1.0 (100 %).
            joined_date=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
        )

        self.stakeholders[stakeholder_id] = stakeholder

        # Record identity verification data
        if identity_proof:
            self.identity_verifications[stakeholder_id] = {
                "verified_at": datetime.now(timezone.utc),
                "verification_method": identity_proof.get("method", "unknown"),
                "verification_score": identity_proof.get("score", 0.0),
                "unique_identifiers": identity_proof.get("identifiers", []),
            }

        # Initialize voting power history
        self.voting_power_history[stakeholder_id] = [
            (datetime.now(timezone.utc), stakeholder.calculate_voting_power())
        ]

        # Track stake groups for concentration monitoring
        self._update_stake_group_tracking(stakeholder_id, initial_stake)

        # SECURITY: Monitor for suspicious staking patterns
        self._monitor_staking_patterns(stakeholder_id, initial_stake)

        # Emit audit event
        audit_emitter.emit_capsule_created(
            capsule_id=f"stakeholder_registration_{stakeholder_id}",
            agent_id=stakeholder_id,
            capsule_type="governance_stakeholder",
        )

        logger.info(
            f"Registered stakeholder {stakeholder_id} with stake {initial_stake}"
        )
        return stakeholder

    def create_proposal(
        self,
        title: str,
        description: str,
        proposal_type: ProposalType,
        proposer_id: str,
        voting_duration: timedelta = timedelta(days=7),
        voting_method: VotingMethod = VotingMethod.SIMPLE_MAJORITY,
        required_threshold: float = 0.5,
        execution_data: Optional[Dict[str, Any]] = None,
    ) -> Proposal:
        """Create a new governance proposal with constitutional checks."""

        # Validate proposer
        if proposer_id not in self.stakeholders:
            raise ValueError(f"Proposer {proposer_id} is not a registered stakeholder")

        proposer = self.stakeholders[proposer_id]

        # Check minimum stake requirement
        if proposer.stake_amount < self.MIN_STAKE_FOR_PROPOSAL:
            raise ValueError(
                f"Proposer must have at least {self.MIN_STAKE_FOR_PROPOSAL} stake to create proposals"
            )

        # Check reputation requirement
        if proposer.reputation_score < self.MIN_REPUTATION_FOR_VOTING:
            raise ValueError(
                f"Proposer must have at least {self.MIN_REPUTATION_FOR_VOTING} reputation to create proposals"
            )

        proposal_id = self._generate_proposal_id()
        current_time = datetime.now(timezone.utc)

        # Adjust voting parameters based on proposal type
        if proposal_type == ProposalType.EMERGENCY_ACTION:
            voting_duration = timedelta(hours=24)  # Shorter duration for emergencies
            voting_method = VotingMethod.SUPERMAJORITY
            required_threshold = 0.75
        elif proposal_type == ProposalType.SYSTEM_UPGRADE:
            voting_method = VotingMethod.SUPERMAJORITY
            required_threshold = 0.67

        # Add mandatory delay for non-emergency proposals (time-based protection)
        proposal_delay = (
            timedelta(hours=24)
            if proposal_type != ProposalType.EMERGENCY_ACTION
            else timedelta(hours=1)
        )

        proposal = Proposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposal_type=proposal_type,
            proposer_id=proposer_id,
            created_at=current_time,
            voting_start=current_time
            + proposal_delay,  # Mandatory delay for reflection
            voting_end=current_time + proposal_delay + voting_duration,
            voting_method=voting_method,
            required_threshold=required_threshold,
            status=ProposalStatus.SUBMITTED,
            execution_data=execution_data,
        )

        # Constitutional validation
        constitutional_check = (
            self.constitutional_framework.validate_proposal_constitutionality(proposal)
        )
        if not constitutional_check[0]:
            raise ValueError(
                f"Proposal violates constitutional principles: {constitutional_check[1]}"
            )

        # Check if judicial review is required
        if self.constitutional_framework.requires_judicial_review(proposal):
            proposal.metadata["requires_judicial_review"] = True
            proposal.required_threshold = max(
                proposal.required_threshold, 0.75
            )  # Supermajority for constitutional changes

        self.proposals[proposal_id] = proposal
        self.governance_stats["total_proposals"] += 1

        # Emit audit event
        audit_emitter.emit_capsule_created(
            capsule_id=f"proposal_{proposal_id}",
            agent_id=proposer_id,
            capsule_type="governance_proposal",
        )

        logger.info(f"Created proposal {proposal_id}: {title}")
        return proposal

    def cast_vote(
        self,
        proposal_id: str,
        voter_id: str,
        vote_type: VoteType,
        private_key: str,
        justification: Optional[str] = None,
    ) -> Vote:
        """Cast a vote on a proposal with democratic protections."""

        # Validate inputs
        if proposal_id not in self.proposals:
            raise ValueError(f"Proposal {proposal_id} not found")

        if voter_id not in self.stakeholders:
            raise ValueError(f"Voter {voter_id} is not a registered stakeholder")

        proposal = self.proposals[proposal_id]
        stakeholder = self.stakeholders[voter_id]

        # Check reputation requirement for voting
        if stakeholder.reputation_score < self.MIN_REPUTATION_FOR_VOTING:
            raise ValueError(
                f"Voter must have at least {self.MIN_REPUTATION_FOR_VOTING} reputation to vote"
            )

        # Sybil resistance check (always enforced via injected detector)
        if voter_id not in self.identity_verifications:
            raise ValueError(
                "Voter must complete identity verification to participate in governance"
            )

        verification = self.identity_verifications[voter_id]
        if verification["verification_score"] < 0.7:
            raise ValueError("Insufficient identity verification score for voting")

        # Check if voting is open
        current_time = datetime.now(timezone.utc)
        if current_time < proposal.voting_start:
            raise ValueError("Voting has not started yet")

        if current_time > proposal.voting_end:
            raise ValueError("Voting has ended")

        # Check if already voted
        existing_vote = next(
            (v for v in proposal.votes if v.voter_id == voter_id), None
        )
        if existing_vote:
            raise ValueError(f"Voter {voter_id} has already voted on this proposal")

        # Handle delegation
        effective_voter_id = voter_id
        if stakeholder.delegated_to:
            effective_voter_id = stakeholder.delegated_to
            if effective_voter_id not in self.stakeholders:
                raise ValueError(f"Delegate {effective_voter_id} not found")

        # SECURITY: Check for vote buying patterns before casting vote
        vote_buying_check = self._detect_vote_buying_patterns(
            voter_id, proposal_id, vote_type
        )
        if vote_buying_check["suspicious"]:
            logger.warning(
                f"Suspicious vote buying pattern detected for voter {voter_id}: {vote_buying_check['reason']}"
            )
            # In production, this could block the vote or require additional verification

        # Calculate voting power with concentration limits
        base_voting_power = stakeholder.calculate_voting_power()
        voting_power = self._apply_voting_power_limits(voter_id, base_voting_power)

        # SECURITY: Validate stake legitimacy before applying voting power
        stake_legitimacy_check = self._validate_stake_legitimacy(voter_id)
        if not stake_legitimacy_check["legitimate"]:
            raise ValueError(
                f"Stake legitimacy validation failed: {stake_legitimacy_check['reason']}"
            )

        # Check for minority protection requirements
        if self.minority_protection_enabled and self._requires_minority_protection(
            proposal
        ):
            minority_veto_check = self._check_minority_veto_rights(
                proposal, vote_type, voting_power
            )
            if not minority_veto_check[0]:
                logger.warning(
                    f"Minority protection triggered: {minority_veto_check[1]}"
                )

        # Create and sign vote
        vote_id = self._generate_vote_id()
        vote_data = (
            f"{proposal_id}:{voter_id}:{vote_type.value}:{current_time.isoformat()}"
        )
        signature = pq_crypto.dilithium_sign(
            vote_data.encode(), bytes.fromhex(private_key)
        )

        vote = Vote(
            vote_id=vote_id,
            proposal_id=proposal_id,
            voter_id=voter_id,
            vote_type=vote_type,
            voting_power=voting_power,
            timestamp=current_time,
            signature=signature.hex(),
            justification=justification,
        )

        proposal.votes.append(vote)

        # Update stakeholder activity
        stakeholder.last_activity = current_time

        # Update voting power history
        if voter_id in self.voting_power_history:
            self.voting_power_history[voter_id].append((current_time, voting_power))

        # Update stats
        self.governance_stats["total_votes"] += 1
        if voter_id not in [
            v.voter_id for v in proposal.votes[:-1]
        ]:  # First vote from this voter
            self.governance_stats["unique_voters"] += 1

        # Emit audit event
        audit_emitter.emit_capsule_created(
            capsule_id=f"vote_{vote_id}",
            agent_id=voter_id,
            capsule_type="governance_vote",
        )

        logger.info(
            f"Vote cast by {voter_id} on proposal {proposal_id}: {vote_type.value}"
        )
        return vote

    def finalize_proposal(self, proposal_id: str) -> bool:
        """Finalize a proposal after voting period."""

        if proposal_id not in self.proposals:
            raise ValueError(f"Proposal {proposal_id} not found")

        proposal = self.proposals[proposal_id]

        # Check if voting period has ended
        if not proposal.is_expired():
            raise ValueError("Voting period has not ended")

        # Determine result
        if proposal.is_passed():
            proposal.status = ProposalStatus.PASSED
            self.governance_stats["passed_proposals"] += 1

            # Execute proposal if execution data provided
            if proposal.execution_data:
                self._execute_proposal(proposal)

            logger.info(f"Proposal {proposal_id} passed")
            return True
        else:
            proposal.status = ProposalStatus.REJECTED
            self.governance_stats["rejected_proposals"] += 1
            logger.info(f"Proposal {proposal_id} rejected")
            return False

    def delegate_voting_power(self, delegator_id: str, delegate_id: str) -> bool:
        """Delegate voting power to another stakeholder."""

        if delegator_id not in self.stakeholders:
            raise ValueError(f"Delegator {delegator_id} not found")

        if delegate_id not in self.stakeholders:
            raise ValueError(f"Delegate {delegate_id} not found")

        if delegator_id == delegate_id:
            raise ValueError("Cannot delegate to yourself")

        # Check for circular delegation
        if self._would_create_circular_delegation(delegator_id, delegate_id):
            raise ValueError("Circular delegation detected")

        self.stakeholders[delegator_id].delegated_to = delegate_id

        # Emit audit event
        audit_emitter.emit_capsule_created(
            capsule_id=f"delegation_{delegator_id}_{delegate_id}",
            agent_id=delegator_id,
            capsule_type="governance_delegation",
        )

        logger.info(f"Voting power delegated from {delegator_id} to {delegate_id}")
        return True

    def revoke_delegation(self, delegator_id: str) -> bool:
        """Revoke voting power delegation."""

        if delegator_id not in self.stakeholders:
            raise ValueError(f"Delegator {delegator_id} not found")

        self.stakeholders[delegator_id].delegated_to = None

        logger.info(f"Delegation revoked for {delegator_id}")
        return True

    def get_proposal_status(self, proposal_id: str) -> Dict[str, Any]:
        """Get detailed status of a proposal."""

        if proposal_id not in self.proposals:
            raise ValueError(f"Proposal {proposal_id} not found")

        proposal = self.proposals[proposal_id]
        tally = proposal.get_vote_tally()

        return {
            "proposal_id": proposal_id,
            "title": proposal.title,
            "status": proposal.status.value,
            "proposal_type": proposal.proposal_type.value,
            "voting_method": proposal.voting_method.value,
            "required_threshold": proposal.required_threshold,
            "created_at": proposal.created_at.isoformat(),
            "voting_start": proposal.voting_start.isoformat(),
            "voting_end": proposal.voting_end.isoformat(),
            "is_expired": proposal.is_expired(),
            "is_passed": proposal.is_passed(),
            "vote_tally": {k.value: v for k, v in tally.items()},
            "total_votes": len(proposal.votes),
            "participation_rate": self._calculate_participation_rate(proposal),
        }

    def get_governance_analytics(self) -> Dict[str, Any]:
        """Get comprehensive governance analytics."""

        # Active proposals
        active_proposals = [
            p for p in self.proposals.values() if p.status == ProposalStatus.VOTING
        ]

        # Stakeholder participation
        participation_stats = {}
        for stakeholder_id, stakeholder in self.stakeholders.items():
            votes_cast = sum(
                1
                for p in self.proposals.values()
                for v in p.votes
                if v.voter_id == stakeholder_id
            )
            participation_stats[stakeholder_id] = {
                "stake_amount": stakeholder.stake_amount,
                "voting_power": stakeholder.calculate_voting_power(),
                "votes_cast": votes_cast,
                "participation_rate": votes_cast / max(len(self.proposals), 1),
            }

        # Proposal type distribution
        proposal_types = defaultdict(int)
        for proposal in self.proposals.values():
            proposal_types[proposal.proposal_type.value] += 1

        return {
            "governance_stats": dict(self.governance_stats),
            "active_proposals": len(active_proposals),
            "total_stakeholders": len(self.stakeholders),
            "proposal_type_distribution": dict(proposal_types),
            "participation_stats": participation_stats,
            "consensus_algorithm": self.consensus_algorithm.value,
            "governance_parameters": self.governance_parameters,
        }

    def _execute_proposal(self, proposal: Proposal):
        """Execute a passed proposal."""

        try:
            action_id = self._generate_action_id()

            # Execute based on proposal type
            if proposal.proposal_type == ProposalType.PARAMETER_UPDATE:
                result = self._execute_parameter_update(proposal.execution_data)
            elif proposal.proposal_type == ProposalType.POLICY_CHANGE:
                result = self._execute_policy_change(proposal.execution_data)
            elif proposal.proposal_type == ProposalType.EMERGENCY_ACTION:
                result = self._execute_emergency_action(proposal.execution_data)
            else:
                result = {"message": "Execution not implemented for this proposal type"}

            # Record execution
            action = GovernanceAction(
                action_id=action_id,
                proposal_id=proposal.proposal_id,
                action_type=proposal.proposal_type.value,
                executor_id="governance_engine",
                executed_at=datetime.now(timezone.utc),
                success=True,
                result=result,
            )

            self.executed_actions[action_id] = action
            proposal.status = ProposalStatus.EXECUTED

            logger.info(f"Executed proposal {proposal.proposal_id}")

        except Exception as e:
            logger.error(f"Failed to execute proposal {proposal.proposal_id}: {e}")

            # Record failed execution
            action = GovernanceAction(
                action_id=self._generate_action_id(),
                proposal_id=proposal.proposal_id,
                action_type=proposal.proposal_type.value,
                executor_id="governance_engine",
                executed_at=datetime.now(timezone.utc),
                success=False,
                result={"error": str(e)},
            )

            self.executed_actions[action.action_id] = action

    def _execute_parameter_update(
        self, execution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute parameter update."""
        parameter_name = execution_data.get("parameter_name")
        new_value = execution_data.get("new_value")

        if parameter_name in self.governance_parameters:
            old_value = self.governance_parameters[parameter_name]
            self.governance_parameters[parameter_name] = new_value

            return {
                "parameter_name": parameter_name,
                "old_value": old_value,
                "new_value": new_value,
            }

        raise ValueError(f"Parameter {parameter_name} not found")

    def _execute_policy_change(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute policy change."""
        policy_id = execution_data.get("policy_id")
        policy_changes = execution_data.get("changes", {})

        return {
            "policy_id": policy_id,
            "changes_applied": policy_changes,
            "message": "Policy changes applied",
        }

    def _execute_emergency_action(
        self, execution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute emergency action."""
        action_type = execution_data.get("action_type")
        parameters = execution_data.get("parameters", {})

        return {
            "action_type": action_type,
            "parameters": parameters,
            "message": "Emergency action executed",
        }

    def _would_create_circular_delegation(
        self, delegator_id: str, delegate_id: str
    ) -> bool:
        """Check if delegation would create a circular reference."""
        visited = set()
        current = delegate_id

        while current and current not in visited:
            visited.add(current)
            if current == delegator_id:
                return True
            current = self.stakeholders.get(current, {}).delegated_to

        return False

    def _calculate_participation_rate(self, proposal: Proposal) -> float:
        """Calculate participation rate for a proposal."""
        total_stakeholders = len(self.stakeholders)
        unique_voters = len({v.voter_id for v in proposal.votes})

        if total_stakeholders == 0:
            return 0.0

        return unique_voters / total_stakeholders

    def _initialize_parameters(self) -> Dict[str, Any]:
        """Initialize governance parameters."""
        return {
            "min_stake_to_propose": 1000.0,
            "min_voting_period": 24,  # hours
            "max_voting_period": 168,  # hours (1 week)
            "quorum_threshold": 0.3,
            "reputation_decay_rate": 0.95,
            "delegation_max_depth": 3,
        }

    def _generate_proposal_id(self) -> str:
        """Generate unique proposal ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        hash_input = f"proposal_{timestamp}_{len(self.proposals)}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _generate_vote_id(self) -> str:
        """Generate unique vote ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        hash_input = f"vote_{timestamp}_{self.governance_stats['total_votes']}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _generate_action_id(self) -> str:
        """Generate unique action ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        hash_input = f"action_{timestamp}_{len(self.executed_actions)}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def enforce_voting_power_limits(
        self, participant_id: str, requested_stake: float
    ) -> Tuple[bool, Optional[str]]:
        """Enforce stake concentration limits to prevent system capture."""
        if not self.CONCENTRATION_CHECK_ENABLED:
            return True, None

        # Check individual limit
        total_stake = sum(s.stake_amount for s in self.stakeholders.values())
        if total_stake == 0:
            return True, None

        individual_percentage = requested_stake / (total_stake + requested_stake)
        if individual_percentage > self.MAX_INDIVIDUAL_VOTING_POWER:
            return (
                False,
                f"Individual stake would exceed {self.MAX_INDIVIDUAL_VOTING_POWER*100}% limit",
            )

        # SECURITY: Check for coordinated voting power concentration
        if self._check_coordinated_concentration(participant_id, requested_stake):
            return (
                False,
                f"Coordinated stake concentration would exceed {self.MAX_COORDINATED_VOTING_POWER*100}% limit",
            )

        return True, None

    def _check_coordinated_concentration(
        self, participant_id: str, additional_stake: float
    ) -> bool:
        """Check for coordinated stake concentration attacks."""

        # Get all known associates/coordinated stakeholders
        coordinated_group = self._get_coordinated_stakeholders(participant_id)

        if not coordinated_group:
            return False  # No coordination detected

        # Calculate total coordinated stake including new stake
        total_coordinated_stake = additional_stake
        for stakeholder_id in coordinated_group:
            if stakeholder_id in self.stakeholders:
                total_coordinated_stake += self.stakeholders[
                    stakeholder_id
                ].stake_amount

        # Calculate percentage of total system stake
        total_system_stake = (
            sum(s.stake_amount for s in self.stakeholders.values()) + additional_stake
        )
        if total_system_stake == 0:
            return False

        coordinated_percentage = total_coordinated_stake / total_system_stake

        return coordinated_percentage > self.MAX_COORDINATED_VOTING_POWER

    def _get_coordinated_stakeholders(self, participant_id: str) -> Set[str]:
        """Identify potentially coordinated stakeholders."""

        coordinated = set()

        # Check stake groups (manually identified coordination)
        for group_id, members in self.stake_groups.items():
            if participant_id in members:
                coordinated.update(members)

        # SECURITY: Automated coordination detection
        if participant_id in self.stakeholders:
            participant = self.stakeholders[participant_id]

            # Check for IP address clustering
            participant_verification = self.identity_verifications.get(
                participant_id, {}
            )
            participant_ip = participant_verification.get("unique_identifiers", {}).get(
                "ip_address"
            )

            if participant_ip:
                for other_id, other_verification in self.identity_verifications.items():
                    if other_id != participant_id:
                        other_ip = other_verification.get("unique_identifiers", {}).get(
                            "ip_address"
                        )
                        if other_ip == participant_ip:
                            coordinated.add(other_id)

            # Check for simultaneous registration patterns
            registration_time = participant.joined_date
            time_window = timedelta(
                hours=1
            )  # 1-hour window for suspicious registrations

            for other_id, other_stakeholder in self.stakeholders.items():
                if other_id != participant_id:
                    time_diff = abs(
                        (
                            registration_time - other_stakeholder.joined_date
                        ).total_seconds()
                    )
                    if time_diff <= time_window.total_seconds():
                        coordinated.add(other_id)

        return coordinated

    def _perform_sybil_check(
        self, stakeholder_id: str, identity_proof: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """Perform Sybil resistance checks."""

        if not identity_proof:
            return False, "Identity proof required for Sybil resistance"

        # SECURITY: Check identity verification score
        verification_score = identity_proof.get("score", 0.0)
        if verification_score < 0.7:  # Minimum 70% verification score
            return False, f"Identity verification score too low: {verification_score}"

        # SECURITY: Check for unique identifiers
        unique_identifiers = identity_proof.get("identifiers", {})

        # Check for duplicate email addresses
        email = unique_identifiers.get("email")
        if email:
            for (
                existing_id,
                existing_verification,
            ) in self.identity_verifications.items():
                existing_email = existing_verification.get(
                    "unique_identifiers", {}
                ).get("email")
                if existing_email == email:
                    return False, f"Email address already registered: {email}"

        # Check for duplicate phone numbers
        phone = unique_identifiers.get("phone")
        if phone:
            for (
                existing_id,
                existing_verification,
            ) in self.identity_verifications.items():
                existing_phone = existing_verification.get(
                    "unique_identifiers", {}
                ).get("phone")
                if existing_phone == phone:
                    return False, f"Phone number already registered: {phone}"

        # SECURITY: Check for IP address clustering
        ip_address = unique_identifiers.get("ip_address")
        if ip_address:
            same_ip_count = sum(
                1
                for verification in self.identity_verifications.values()
                if verification.get("unique_identifiers", {}).get("ip_address")
                == ip_address
            )
            if same_ip_count >= 3:  # Maximum 3 accounts per IP
                return False, f"Too many accounts from IP address: {ip_address}"

        return True, None

    def validate_stake_legitimacy(
        self, stakeholder_id: str, stake_amount: float
    ) -> bool:
        """Validate stake legitimacy and prevent manipulation."""

        if stakeholder_id not in self.stakeholders:
            return False

        stakeholder = self.stakeholders[stakeholder_id]

        # SECURITY: Check for rapid stake changes (stake washing)
        if self.detect_stake_washing(stakeholder_id):
            return False

        # SECURITY: Verify stake amount is reasonable
        if stake_amount <= 0:
            return False

        # SECURITY: Check for artificial stake inflation
        verification = self.identity_verifications.get(stakeholder_id, {})
        verification_score = verification.get("verification_score", 0.0)

        # Higher stakes require higher verification scores
        required_verification = min(0.9, 0.5 + (stake_amount / 10000) * 0.4)
        if verification_score < required_verification:
            return False

        return True

    def detect_stake_washing(self, stakeholder_id: str) -> bool:
        """Detect stake washing patterns (rapid stake changes to manipulate voting)."""

        if stakeholder_id not in self.voting_power_history:
            return False

        history = self.voting_power_history[stakeholder_id]
        if len(history) < 3:
            return False  # Not enough history

        # SECURITY: Check for rapid stake changes
        recent_changes = history[-10:]  # Last 10 changes
        time_diffs = []
        stake_diffs = []

        for i in range(1, len(recent_changes)):
            prev_time, prev_power = recent_changes[i - 1]
            curr_time, curr_power = recent_changes[i]

            time_diff = (curr_time - prev_time).total_seconds() / 3600  # Hours
            stake_diff = abs(curr_power - prev_power)

            time_diffs.append(time_diff)
            stake_diffs.append(stake_diff)

        # SECURITY: Detect patterns indicating washing
        # Pattern 1: Rapid back-and-forth changes
        if len(stake_diffs) >= 4:
            alternating_pattern = True
            for i in range(2, len(stake_diffs)):
                # Check if changes alternate direction
                if (stake_diffs[i] > 0) == (stake_diffs[i - 2] > 0):
                    alternating_pattern = False
                    break

            if alternating_pattern and max(time_diffs) < 24:  # Within 24 hours
                return True

        # Pattern 2: Sudden large increases before voting
        avg_stake_diff = sum(stake_diffs) / len(stake_diffs) if stake_diffs else 0
        max_stake_diff = max(stake_diffs) if stake_diffs else 0

        if max_stake_diff > avg_stake_diff * 5:  # 5x average increase
            corresponding_time_diff = time_diffs[stake_diffs.index(max_stake_diff)]
            if corresponding_time_diff < 1:  # Within 1 hour
                return True

        return False

    def _apply_voting_power_limits(
        self, voter_id: str, base_voting_power: float
    ) -> float:
        """Apply voting power limits to prevent concentration attacks."""

        if not self.CONCENTRATION_CHECK_ENABLED:
            return base_voting_power

        # Calculate total system voting power
        total_system_power = sum(
            s.calculate_voting_power() for s in self.stakeholders.values()
        )

        if total_system_power == 0:
            return base_voting_power

        # SECURITY: Cap individual voting power
        max_individual_power = total_system_power * self.MAX_INDIVIDUAL_VOTING_POWER
        capped_individual_power = min(base_voting_power, max_individual_power)

        # SECURITY: Check coordinated power limits
        coordinated_group = self._get_coordinated_stakeholders(voter_id)
        if coordinated_group:
            # Calculate total coordinated power
            total_coordinated_power = sum(
                self.stakeholders[member_id].calculate_voting_power()
                for member_id in coordinated_group
                if member_id in self.stakeholders
            )

            # Apply coordinated limit
            max_coordinated_power = (
                total_system_power * self.MAX_COORDINATED_VOTING_POWER
            )
            if total_coordinated_power > max_coordinated_power:
                # Proportionally reduce power for all group members
                reduction_factor = max_coordinated_power / total_coordinated_power
                capped_individual_power *= reduction_factor

        return capped_individual_power

    def _requires_minority_protection(self, proposal: "Proposal") -> bool:
        """Check if proposal requires minority protection."""

        # Constitutional changes always require protection
        if proposal.proposal_type in {
            ProposalType.RULE_AMENDMENT,
            ProposalType.SYSTEM_UPGRADE,
        }:
            return True

        # High-impact economic changes
        if proposal.proposal_type == ProposalType.RESOURCE_ALLOCATION:
            # Check if allocation amount is significant
            allocation_amount = (
                proposal.execution_data.get("amount", 0)
                if proposal.execution_data
                else 0
            )
            if allocation_amount > 100000:  # $100k threshold
                return True

        return False

    def _check_minority_veto_rights(
        self, proposal: "Proposal", vote_type: VoteType, voting_power: float
    ) -> Tuple[bool, Optional[str]]:
        """Check minority veto rights for constitutional protection."""

        if vote_type != VoteType.AGAINST:
            return True, None  # Only AGAINST votes can trigger minority protection

        # Calculate current minority voting power
        total_against_power = sum(
            vote.voting_power
            for vote in proposal.votes
            if vote.vote_type == VoteType.AGAINST
        )

        total_voting_power = sum(vote.voting_power for vote in proposal.votes)

        if total_voting_power == 0:
            return True, None

        minority_percentage = total_against_power / total_voting_power

        # SECURITY: If minority exceeds 25%, they have veto power on constitutional changes
        if minority_percentage > 0.25 and self._requires_minority_protection(proposal):
            return (
                False,
                f"Minority veto triggered: {minority_percentage:.1%} opposition on constitutional change",
            )

        return True, None

    def enforce_voting_power_limits(
        self, participant_id: str, requested_stake: float
    ) -> Tuple[bool, Optional[str]]:
        """Enforce stake concentration limits to prevent system capture."""
        if not self.CONCENTRATION_CHECK_ENABLED:
            return True, None

        # Check individual limit
        total_stake = sum(s.stake_amount for s in self.stakeholders.values())
        if total_stake == 0:
            return True, None

        individual_percentage = requested_stake / (total_stake + requested_stake)
        if individual_percentage > self.MAX_INDIVIDUAL_VOTING_POWER:
            return (
                False,
                f"Individual stake would exceed {self.MAX_INDIVIDUAL_VOTING_POWER*100}% limit",
            )

        # Check coordinated group limits
        coordinated_stake = self._calculate_coordinated_stake(
            participant_id, requested_stake
        )
        coordinated_percentage = coordinated_stake / (total_stake + requested_stake)
        if coordinated_percentage > self.MAX_COORDINATED_VOTING_POWER:
            return (
                False,
                f"Coordinated group stake would exceed {self.MAX_COORDINATED_VOTING_POWER*100}% limit",
            )

        return True, None

    def _calculate_coordinated_stake(
        self, participant_id: str, additional_stake: float = 0
    ) -> float:
        """Calculate total stake controlled by coordinated group."""
        coordinated_participants = self._identify_coordinated_participants(
            participant_id
        )
        total_coordinated_stake = additional_stake

        for coord_id in coordinated_participants:
            if coord_id in self.stakeholders:
                total_coordinated_stake += self.stakeholders[coord_id].stake_amount

        return total_coordinated_stake

    def _identify_coordinated_participants(self, participant_id: str) -> Set[str]:
        """Identify potentially coordinated participants based on various signals."""
        coordinated = {participant_id}

        # Check for same registration patterns, timing, etc.
        if participant_id in self.stakeholders:
            participant = self.stakeholders[participant_id]

            for other_id, other_stakeholder in self.stakeholders.items():
                if other_id == participant_id:
                    continue

                # Check for similar registration timing (potential batch creation)
                time_diff = abs(
                    (
                        participant.joined_date - other_stakeholder.joined_date
                    ).total_seconds()
                )
                if time_diff < 3600:  # Within 1 hour
                    coordinated.add(other_id)

                # Check for delegation relationships
                if (
                    other_stakeholder.delegated_to == participant_id
                    or participant.delegated_to == other_id
                ):
                    coordinated.add(other_id)

        # Check stake groups
        for group_id, group_members in self.stake_groups.items():
            if participant_id in group_members:
                coordinated.update(group_members)

        return coordinated

    def _update_stake_group_tracking(self, stakeholder_id: str, stake_amount: float):
        """Update stake group tracking for concentration monitoring."""
        # Simple heuristic: group stakeholders with similar stake amounts registered around same time
        stakeholder = self.stakeholders[stakeholder_id]

        for group_id, group_members in self.stake_groups.items():
            if len(group_members) < 10:  # Don't let groups get too large
                # Check if this stakeholder fits the group pattern
                sample_member_id = next(iter(group_members))
                if sample_member_id in self.stakeholders:
                    sample_member = self.stakeholders[sample_member_id]
                    stake_similarity = abs(
                        stake_amount - sample_member.stake_amount
                    ) / max(stake_amount, sample_member.stake_amount)
                    time_diff = abs(
                        (
                            stakeholder.joined_date - sample_member.joined_date
                        ).total_seconds()
                    )

                    if (
                        stake_similarity < 0.1 and time_diff < 7200
                    ):  # Similar stakes, within 2 hours
                        group_members.add(stakeholder_id)
                        return

        # Create new group if no existing group fits
        new_group_id = f"stake_group_{len(self.stake_groups)}"
        self.stake_groups[new_group_id] = {stakeholder_id}

    def _perform_sybil_check(
        self, stakeholder_id: str, identity_proof: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """Perform Sybil resistance check."""
        if not identity_proof:
            return False, "Identity proof required for governance participation"

        verification_method = identity_proof.get("method", "")
        verification_score = identity_proof.get("score", 0.0)
        unique_identifiers = identity_proof.get("identifiers", [])

        # Check minimum verification score
        if verification_score < 0.7:
            return False, "Insufficient identity verification score for governance"

        # Check for duplicate identifiers (potential Sybil accounts)
        for existing_id, existing_verification in self.identity_verifications.items():
            if existing_id == stakeholder_id:
                continue

            existing_identifiers = existing_verification.get("unique_identifiers", [])
            overlap = set(unique_identifiers) & set(existing_identifiers)
            if len(overlap) > 0:
                return (
                    False,
                    f"Identity overlap detected with existing participant {existing_id}",
                )

        # Check behavioral patterns for bot-like activity
        behavioral_score = self._calculate_behavioral_authenticity_score(
            stakeholder_id, identity_proof
        )
        if behavioral_score < 0.5:
            return False, "Behavioral patterns suggest automated/inauthentic account"

        return True, None

    def _calculate_behavioral_authenticity_score(
        self, stakeholder_id: str, identity_proof: Dict[str, Any]
    ) -> float:
        """Calculate behavioral authenticity score to detect bots/fake accounts."""
        score = 1.0

        # Check for human-like interaction patterns
        interaction_history = identity_proof.get("interaction_history", [])
        if len(interaction_history) == 0:
            score -= 0.3  # No interaction history is suspicious

        # Check for temporal patterns (bots often have very regular timing)
        timestamps = identity_proof.get("activity_timestamps", [])
        if len(timestamps) > 5:
            intervals = [
                timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)
            ]
            if len(set(intervals)) == 1:  # All intervals identical - very suspicious
                score -= 0.4

        # Check for diversity in actions
        action_types = identity_proof.get("action_types", [])
        if len(set(action_types)) < 3:  # Very limited action diversity
            score -= 0.2

        return max(0.0, score)

    def _apply_voting_power_limits(
        self, voter_id: str, base_voting_power: float
    ) -> float:
        """Apply voting power concentration limits."""
        if not self.CONCENTRATION_CHECK_ENABLED:
            return base_voting_power

        total_voting_power = sum(
            s.calculate_voting_power() for s in self.stakeholders.values()
        )
        if total_voting_power == 0:
            return base_voting_power

        individual_percentage = base_voting_power / total_voting_power

        # Cap individual voting power
        if individual_percentage > self.MAX_INDIVIDUAL_VOTING_POWER:
            capped_power = total_voting_power * self.MAX_INDIVIDUAL_VOTING_POWER
            logger.warning(
                f"Voting power capped for {voter_id}: {base_voting_power} -> {capped_power}"
            )
            return capped_power

        return base_voting_power

    def _requires_minority_protection(self, proposal: Proposal) -> bool:
        """Check if proposal requires minority protection mechanisms."""
        # Constitutional changes always require minority protection
        if (
            proposal.proposal_type
            in ConstitutionalFramework.CONSTITUTIONAL_PROPOSAL_TYPES
        ):
            return True

        # Proposals affecting fundamental rights
        rights_keywords = [
            "attribution",
            "consent",
            "transparency",
            "participation",
            "economic",
        ]
        description_lower = proposal.description.lower()
        for keyword in rights_keywords:
            if keyword in description_lower:
                return True

        # High-impact proposals based on economic impact
        if (
            proposal.execution_data
            and proposal.execution_data.get("economic_impact", 0) > 10000
        ):
            return True

        return False

    def _check_minority_veto_rights(
        self, proposal: Proposal, vote_type: VoteType, voting_power: float
    ) -> Tuple[bool, Optional[str]]:
        """Check minority veto rights for fundamental changes."""
        if not self._requires_minority_protection(proposal):
            return True, None

        # Calculate minority threshold (need 25% of total voting power to veto)
        total_voting_power = sum(
            s.calculate_voting_power() for s in self.stakeholders.values()
        )
        minority_veto_threshold = total_voting_power * 0.25

        # Check current opposition voting power
        current_opposition_power = sum(
            v.voting_power for v in proposal.votes if v.vote_type == VoteType.AGAINST
        )

        if vote_type == VoteType.AGAINST:
            current_opposition_power += voting_power

        # If minority reaches veto threshold, flag for special review
        if current_opposition_power >= minority_veto_threshold:
            return (
                True,
                f"Minority veto threshold reached: {current_opposition_power}/{minority_veto_threshold}",
            )

        return True, None

    def add_stake_vesting_period(
        self, stakeholder_id: str, stake_amount: float, vesting_period_days: int = 30
    ) -> bool:
        """Add vesting period for new stakes to prevent rapid manipulation."""
        if stakeholder_id not in self.stakeholders:
            return False

        stakeholder = self.stakeholders[stakeholder_id]
        vesting_end = datetime.now(timezone.utc) + timedelta(days=vesting_period_days)

        # Track vesting stakes
        if not hasattr(stakeholder, "vesting_stakes"):
            stakeholder.vesting_stakes = []

        stakeholder.vesting_stakes.append(
            {
                "amount": stake_amount,
                "vesting_end": vesting_end,
                "initial_date": datetime.now(timezone.utc),
            }
        )

        logger.info(
            f"Added vesting period for {stakeholder_id}: {stake_amount} stake vesting until {vesting_end}"
        )
        return True

    def calculate_vested_voting_power(self, stakeholder_id: str) -> float:
        """Calculate voting power considering vesting periods."""
        if stakeholder_id not in self.stakeholders:
            return 0.0

        stakeholder = self.stakeholders[stakeholder_id]
        base_power = stakeholder.calculate_voting_power()

        # Reduce power for unvested stakes
        if hasattr(stakeholder, "vesting_stakes"):
            current_time = datetime.now(timezone.utc)
            unvested_amount = sum(
                vs["amount"]
                for vs in stakeholder.vesting_stakes
                if current_time < vs["vesting_end"]
            )

            # Unvested stakes have 50% voting power
            vesting_penalty = unvested_amount * 0.5
            return max(0.0, base_power - vesting_penalty)

        return base_power

    def implement_emergency_governance_protection(
        self, threat_type: str, severity: float
    ) -> bool:
        """Implement emergency governance protections during detected attacks."""
        if severity > 0.8:  # Critical threat level
            logger.critical(
                f"CRITICAL GOVERNANCE THREAT: {threat_type} (severity: {severity})"
            )

            # Activate emergency lockdown
            self.implement_emergency_governance_lockdown(
                reason=f"Critical threat detected: {threat_type}",
                duration_hours=72,  # 3-day lockdown for critical threats
            )

            # Freeze high-risk accounts
            self._freeze_suspicious_accounts()

            # Require supermajority for all decisions
            self._activate_supermajority_mode()

            return True

        return False

    def _freeze_suspicious_accounts(self):
        """Freeze accounts showing suspicious coordination patterns."""
        for participant_id, stakeholder in self.stakeholders.items():
            if stakeholder.byzantine_behavior_score > 0.7:
                # Temporarily freeze voting power
                stakeholder.vote_weight *= 0.1  # Reduce to 10% voting power
                logger.warning(f"Frozen suspicious account: {participant_id}")

    def _activate_supermajority_mode(self):
        """Activate supermajority requirements for all proposals."""
        self.governance_parameters["emergency_supermajority_mode"] = {
            "active": True,
            "activated_at": datetime.now(timezone.utc),
            "min_threshold": 0.75,  # Require 75% supermajority
        }
        logger.critical(
            "EMERGENCY: Activated supermajority mode for all governance decisions"
        )

    def detect_governance_capture_attempt(self) -> Tuple[bool, float, str]:
        """Detect coordinated attempts to capture governance system."""

        # Calculate total coordinated power across all groups
        total_coordinated_power = 0.0
        max_group_power = 0.0
        threat_details = []

        for group_id, group_members in self.stake_groups.items():
            group_power = sum(
                self.stakeholders[member_id].calculate_voting_power()
                for member_id in group_members
                if member_id in self.stakeholders
            )
            total_coordinated_power += group_power
            max_group_power = max(max_group_power, group_power)

            if group_power > 0.15:  # Group exceeds 15% threshold
                threat_details.append(
                    f"Group {group_id}: {group_power:.2%} voting power"
                )

        total_system_power = sum(
            s.calculate_voting_power() for s in self.stakeholders.values()
        )

        if total_system_power == 0:
            return False, 0.0, "No voting power in system"

        coordination_ratio = total_coordinated_power / total_system_power
        capture_threat_score = min(
            1.0, coordination_ratio / self.GOVERNANCE_LOCKDOWN_THRESHOLD
        )

        is_capture_attempt = coordination_ratio > self.GOVERNANCE_LOCKDOWN_THRESHOLD

        if is_capture_attempt:
            threat_summary = (
                f"Governance capture detected: {coordination_ratio:.2%} coordinated power. "
                + "; ".join(threat_details)
            )
            logger.critical(f"GOVERNANCE CAPTURE ATTEMPT: {threat_summary}")

            # Trigger emergency protections
            self.implement_emergency_governance_protection(
                "Coordinated governance capture", capture_threat_score
            )

            return True, capture_threat_score, threat_summary

        return (
            False,
            capture_threat_score,
            f"Coordination level: {coordination_ratio:.2%}",
        )

    def enforce_constitutional_immutability(self) -> Dict[str, Any]:
        """Enforce immutable constitutional principles that cannot be changed."""

        immutable_protections = {
            "max_individual_voting_power": self.MAX_INDIVIDUAL_VOTING_POWER,
            "concentration_checks_enabled": True,
            "sybil_detection_enabled": True,
            "democratic_participation_protected": True,
            "minority_veto_rights": True,
            "attribution_rights_inalienable": True,
            "transparency_mandatory": True,
            "economic_justice_enforced": True,
        }

        # Verify no attempts to modify immutable constants
        current_max_power = getattr(self, "MAX_INDIVIDUAL_VOTING_POWER", 0.15)
        if current_max_power != 0.15:
            logger.critical(
                f"CONSTITUTIONAL VIOLATION: Attempt to modify MAX_INDIVIDUAL_VOTING_POWER to {current_max_power}"
            )
            # Restore immutable value
            self.MAX_INDIVIDUAL_VOTING_POWER = 0.15

        current_concentration_check = getattr(self, "CONCENTRATION_CHECK_ENABLED", True)
        if not current_concentration_check:
            logger.critical(
                "CONSTITUTIONAL VIOLATION: Attempt to disable concentration checks"
            )
            # Restore immutable value
            self.CONCENTRATION_CHECK_ENABLED = True

        # Note: Sybil detection is enforced via dependency injection at construction time
        # and cannot be disabled at runtime (no boolean flag to tamper with)

        return immutable_protections

    def implement_emergency_governance_lockdown(
        self, reason: str, duration_hours: int = 24
    ) -> bool:
        """Implement emergency lockdown to prevent governance capture during attacks."""
        lockdown_end = datetime.now(timezone.utc) + timedelta(hours=duration_hours)

        self.governance_parameters["emergency_lockdown"] = {
            "active": True,
            "reason": reason,
            "start_time": datetime.now(timezone.utc),
            "end_time": lockdown_end,
            "initiated_by": "security_system",
        }

        # Pause all non-emergency proposals
        for proposal in self.proposals.values():
            if (
                proposal.status == ProposalStatus.VOTING
                and proposal.proposal_type != ProposalType.EMERGENCY_ACTION
            ):
                proposal.status = ProposalStatus.SUBMITTED
                proposal.voting_start = lockdown_end
                proposal.voting_end = lockdown_end + timedelta(days=7)

        logger.critical(
            f"Emergency governance lockdown activated: {reason} (duration: {duration_hours}h)"
        )
        return True

    def _monitor_staking_patterns(self, stakeholder_id: str, stake_amount: float):
        """Monitor for suspicious staking patterns that might indicate attacks."""

        current_time = datetime.now(timezone.utc)

        # SECURITY: Check for rapid large stake accumulation (wash trading)
        recent_stakes = []
        for other_id, other_stakeholder in self.stakeholders.items():
            if other_id != stakeholder_id:
                time_diff = current_time - other_stakeholder.joined_date
                if time_diff.total_seconds() < 3600:  # Within last hour
                    recent_stakes.append((other_id, other_stakeholder.stake_amount))

        if len(recent_stakes) > 5:  # More than 5 large stakes in an hour
            total_recent_stake = sum(stake for _, stake in recent_stakes)
            if total_recent_stake > 10000:  # Threshold for suspicious activity
                logger.warning(
                    f"Suspicious rapid staking pattern detected: {len(recent_stakes)} stakes totaling {total_recent_stake}"
                )

                # Flag for manual review in production
                audit_emitter.emit_security_event(
                    "suspicious_staking_pattern",
                    {
                        "stakeholder_id": stakeholder_id,
                        "stake_amount": stake_amount,
                        "recent_stakes_count": len(recent_stakes),
                        "total_recent_stake": total_recent_stake,
                    },
                )

    def _detect_vote_buying_patterns(
        self, voter_id: str, proposal_id: str, vote_type: VoteType
    ) -> Dict[str, Any]:
        """Detect potential vote buying patterns."""

        result = {"suspicious": False, "reason": "", "confidence": 0.0}

        if voter_id not in self.stakeholders:
            return result

        stakeholder = self.stakeholders[voter_id]

        # SECURITY: Check for sudden stake increases before important votes
        if proposal_id in self.proposals:
            proposal = self.proposals[proposal_id]

            # Check if stake was increased shortly before proposal
            voting_power_history = self.voting_power_history.get(voter_id, [])
            if len(voting_power_history) >= 2:
                recent_power = voting_power_history[-1][1]
                previous_power = voting_power_history[-2][1]
                power_increase = recent_power - previous_power

                # Flag suspicious power increases >500% shortly before voting
                if power_increase > previous_power * 5:
                    time_diff = (
                        proposal.voting_start - voting_power_history[-1][0]
                    ).total_seconds()
                    if time_diff < 86400:  # Increased within 24 hours of voting
                        result["suspicious"] = True
                        result["reason"] = (
                            f"Suspicious {power_increase:.1f} voting power increase 24h before voting"
                        )
                        result["confidence"] = 0.8

        # SECURITY: Check for coordinated voting patterns
        if self._detect_coordinated_voting_behavior(voter_id, proposal_id):
            result["suspicious"] = True
            result["reason"] = "Coordinated voting behavior detected"
            result["confidence"] = max(result["confidence"], 0.7)

        # SECURITY: Check for abnormal voting frequency
        if self._detect_abnormal_voting_frequency(voter_id):
            result["suspicious"] = True
            result["reason"] = "Abnormal voting frequency pattern"
            result["confidence"] = max(result["confidence"], 0.6)

        return result

    def _detect_coordinated_voting_behavior(
        self, voter_id: str, proposal_id: str
    ) -> bool:
        """Detect coordinated voting behavior that might indicate vote buying."""

        if proposal_id not in self.proposals:
            return False

        proposal = self.proposals[proposal_id]

        # Get votes cast within similar timeframes
        voter_vote_time = None
        for vote in proposal.votes:
            if vote.voter_id == voter_id:
                voter_vote_time = vote.timestamp
                break

        if not voter_vote_time:
            return False

        # SECURITY: Check for suspiciously synchronized voting
        synchronized_votes = 0
        time_window = timedelta(minutes=5)  # 5-minute window

        for vote in proposal.votes:
            if vote.voter_id != voter_id:
                time_diff = abs((vote.timestamp - voter_vote_time).total_seconds())
                if time_diff <= time_window.total_seconds():
                    synchronized_votes += 1

        # Flag if >10 votes within 5 minutes (indicates coordination)
        return synchronized_votes > 10

    def _detect_abnormal_voting_frequency(self, voter_id: str) -> bool:
        """Detect abnormal voting frequency that might indicate automated behavior."""

        # Count votes in the last 30 days
        current_time = datetime.now(timezone.utc)
        thirty_days_ago = current_time - timedelta(days=30)

        recent_votes = 0
        for proposal in self.proposals.values():
            for vote in proposal.votes:
                if vote.voter_id == voter_id and vote.timestamp >= thirty_days_ago:
                    recent_votes += 1

        # SECURITY: Flag voters with >50 votes in 30 days (abnormally high)
        return recent_votes > 50

    def _validate_stake_legitimacy(self, voter_id: str) -> Dict[str, Any]:
        """Validate the legitimacy of a voter's stake."""

        result = {"legitimate": True, "reason": ""}

        if voter_id not in self.stakeholders:
            result["legitimate"] = False
            result["reason"] = "Voter not found"
            return result

        stakeholder = self.stakeholders[voter_id]
        current_time = datetime.now(timezone.utc)

        # SECURITY: Check minimum stake holding period (prevent flash staking)
        account_age = current_time - stakeholder.joined_date
        if account_age.total_seconds() < 86400:  # Less than 24 hours old
            if stakeholder.stake_amount > 1000:  # Large stake in new account
                result["legitimate"] = False
                result["reason"] = "Large stake in account less than 24 hours old"
                return result

        # SECURITY: Check for stake washing patterns
        voting_power_history = self.voting_power_history.get(voter_id, [])
        if len(voting_power_history) >= 3:
            # Look for rapid stake changes (potential washing)
            power_changes = []
            for i in range(1, len(voting_power_history)):
                prev_power = voting_power_history[i - 1][1]
                curr_power = voting_power_history[i][1]
                change_ratio = abs(curr_power - prev_power) / max(prev_power, 1)
                power_changes.append(change_ratio)

            # Flag if average change >200% (indicates manipulation)
            if power_changes and sum(power_changes) / len(power_changes) > 2.0:
                result["legitimate"] = False
                result["reason"] = "Suspicious stake manipulation patterns detected"
                return result

        # SECURITY: Check reputation vs stake alignment
        expected_min_reputation = min(
            100, stakeholder.stake_amount / 100
        )  # 1 rep per 100 stake
        if stakeholder.reputation_score < expected_min_reputation * 0.5:
            result["legitimate"] = False
            result["reason"] = (
                f"Reputation {stakeholder.reputation_score} too low for stake {stakeholder.stake_amount}"
            )
            return result

        return result


# Global governance engine instance
governance_engine = GovernanceDAOEngine()
