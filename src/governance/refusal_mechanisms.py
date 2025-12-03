"""
Advanced Governance Refusal Mechanisms
Implements sophisticated refusal handling and governance oversight
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ..audit.events import audit_emitter
from .advanced_governance import ProposalType, VotingMethod, governance_engine

logger = logging.getLogger(__name__)


class RefusalType(str, Enum):
    """Types of refusal decisions"""

    ETHICAL_VIOLATION = "ethical_violation"
    POLICY_VIOLATION = "policy_violation"
    SAFETY_CONCERN = "safety_concern"
    LEGAL_RESTRICTION = "legal_restriction"
    RESOURCE_LIMITATION = "resource_limitation"
    QUALITY_THRESHOLD = "quality_threshold"
    CONTENT_MODERATION = "content_moderation"
    GOVERNANCE_OVERRIDE = "governance_override"


class RefusalSeverity(str, Enum):
    """Severity levels for refusal decisions"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AppealStatus(str, Enum):
    """Status of refusal appeals"""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


@dataclass
class RefusalDecision:
    """Represents a refusal decision"""

    refusal_id: str
    request_id: str
    user_id: str
    refusal_type: RefusalType
    severity: RefusalSeverity
    reason: str
    decision_timestamp: datetime
    decision_maker: str  # system, human_moderator, governance_vote
    confidence_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Appeal information
    is_appealable: bool = True
    appeal_deadline: Optional[datetime] = None
    appeal_status: Optional[AppealStatus] = None
    appeal_id: Optional[str] = None


@dataclass
class RefusalAppeal:
    """Represents an appeal of a refusal decision"""

    appeal_id: str
    refusal_id: str
    user_id: str
    appeal_reason: str
    submitted_at: datetime
    status: AppealStatus
    reviewer_id: Optional[str] = None
    review_notes: Optional[str] = None
    decision_timestamp: Optional[datetime] = None
    governance_proposal_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RefusalGovernanceEngine:
    """Advanced refusal mechanism with governance oversight"""

    def __init__(self):
        self.refusal_decisions: Dict[str, RefusalDecision] = {}
        self.appeals: Dict[str, RefusalAppeal] = {}
        self.refusal_patterns: Dict[str, List[RefusalDecision]] = defaultdict(list)
        self.escalation_thresholds = self._initialize_thresholds()
        self.automatic_reviewers: List[Callable] = []

        # Statistics tracking
        self.refusal_stats = {
            "total_refusals": 0,
            "appeals_submitted": 0,
            "appeals_approved": 0,
            "governance_escalations": 0,
            "pattern_violations": 0,
        }

    def _initialize_thresholds(self) -> Dict[str, Any]:
        """Initialize escalation and review thresholds"""
        return {
            "appeal_deadline_hours": 72,
            "auto_escalation_threshold": 5,  # Appeals for same user/type
            "pattern_analysis_window": 24,  # Hours
            "governance_vote_threshold": 0.6,
            "quality_review_confidence": 0.8,
            "human_review_severity": RefusalSeverity.HIGH,
        }

    def register_refusal(
        self,
        request_id: str,
        user_id: str,
        refusal_type: RefusalType,
        reason: str,
        severity: RefusalSeverity = RefusalSeverity.MEDIUM,
        decision_maker: str = "system",
        confidence_score: float = 1.0,
        metadata: Dict[str, Any] = None,
    ) -> RefusalDecision:
        """Register a new refusal decision"""

        refusal_id = f"refusal_{int(datetime.now().timestamp())}_{user_id[-6:]}"
        current_time = datetime.now(timezone.utc)

        # Calculate appeal deadline
        appeal_deadline = None
        if severity in [RefusalSeverity.LOW, RefusalSeverity.MEDIUM]:
            appeal_deadline = current_time + timedelta(
                hours=self.escalation_thresholds["appeal_deadline_hours"]
            )

        refusal = RefusalDecision(
            refusal_id=refusal_id,
            request_id=request_id,
            user_id=user_id,
            refusal_type=refusal_type,
            severity=severity,
            reason=reason,
            decision_timestamp=current_time,
            decision_maker=decision_maker,
            confidence_score=confidence_score,
            metadata=metadata or {},
            appeal_deadline=appeal_deadline,
        )

        self.refusal_decisions[refusal_id] = refusal
        self.refusal_patterns[user_id].append(refusal)
        self.refusal_stats["total_refusals"] += 1

        # Trigger pattern analysis
        self._analyze_refusal_patterns(user_id)

        # Emit audit event
        audit_emitter.emit_capsule_created(
            capsule_id=f"refusal_{refusal_id}",
            agent_id=decision_maker,
            capsule_type="governance_refusal",
        )

        logger.info(
            f"Refusal registered: {refusal_id} - {refusal_type.value} for user {user_id}"
        )
        return refusal

    def submit_appeal(
        self,
        refusal_id: str,
        user_id: str,
        appeal_reason: str,
        metadata: Dict[str, Any] = None,
    ) -> RefusalAppeal:
        """Submit an appeal for a refusal decision"""

        if refusal_id not in self.refusal_decisions:
            raise ValueError(f"Refusal {refusal_id} not found")

        refusal = self.refusal_decisions[refusal_id]

        # Validate appeal eligibility
        if not refusal.is_appealable:
            raise ValueError("This refusal is not appealable")

        if refusal.user_id != user_id:
            raise ValueError("Only the affected user can appeal this refusal")

        current_time = datetime.now(timezone.utc)
        if refusal.appeal_deadline and current_time > refusal.appeal_deadline:
            raise ValueError("Appeal deadline has passed")

        if refusal.appeal_status in [AppealStatus.PENDING, AppealStatus.UNDER_REVIEW]:
            raise ValueError("Appeal already submitted for this refusal")

        # Create appeal
        appeal_id = f"appeal_{int(current_time.timestamp())}_{user_id[-6:]}"

        appeal = RefusalAppeal(
            appeal_id=appeal_id,
            refusal_id=refusal_id,
            user_id=user_id,
            appeal_reason=appeal_reason,
            submitted_at=current_time,
            status=AppealStatus.PENDING,
            metadata=metadata or {},
        )

        self.appeals[appeal_id] = appeal
        refusal.appeal_status = AppealStatus.PENDING
        refusal.appeal_id = appeal_id
        self.refusal_stats["appeals_submitted"] += 1

        # Check for auto-escalation
        self._check_appeal_escalation(appeal)

        # Emit audit event
        audit_emitter.emit_capsule_created(
            capsule_id=f"appeal_{appeal_id}",
            agent_id=user_id,
            capsule_type="governance_appeal",
        )

        logger.info(f"Appeal submitted: {appeal_id} for refusal {refusal_id}")
        return appeal

    def review_appeal(
        self,
        appeal_id: str,
        reviewer_id: str,
        decision: AppealStatus,
        review_notes: str,
        metadata: Dict[str, Any] = None,
    ) -> RefusalAppeal:
        """Review and decide on an appeal"""

        if appeal_id not in self.appeals:
            raise ValueError(f"Appeal {appeal_id} not found")

        appeal = self.appeals[appeal_id]

        if appeal.status != AppealStatus.UNDER_REVIEW:
            if appeal.status == AppealStatus.PENDING:
                appeal.status = AppealStatus.UNDER_REVIEW
            else:
                raise ValueError(f"Appeal {appeal_id} is not under review")

        # Update appeal
        appeal.reviewer_id = reviewer_id
        appeal.review_notes = review_notes
        appeal.decision_timestamp = datetime.now(timezone.utc)
        appeal.status = decision

        if metadata:
            appeal.metadata.update(metadata)

        # Update original refusal
        refusal = self.refusal_decisions[appeal.refusal_id]
        refusal.appeal_status = decision

        # Update statistics
        if decision == AppealStatus.APPROVED:
            self.refusal_stats["appeals_approved"] += 1

        # Emit audit event
        audit_emitter.emit_capsule_created(
            capsule_id=f"appeal_review_{appeal_id}",
            agent_id=reviewer_id,
            capsule_type="governance_appeal_review",
        )

        logger.info(f"Appeal reviewed: {appeal_id} - {decision.value} by {reviewer_id}")
        return appeal

    def escalate_to_governance(
        self, appeal_id: str, escalation_reason: str, urgency: str = "normal"
    ) -> str:
        """Escalate an appeal to governance voting"""

        if appeal_id not in self.appeals:
            raise ValueError(f"Appeal {appeal_id} not found")

        appeal = self.appeals[appeal_id]
        refusal = self.refusal_decisions[appeal.refusal_id]

        # Create governance proposal
        proposal_title = f"Appeal Review: {refusal.refusal_type.value} Refusal"
        proposal_description = f"""
        Appeal ID: {appeal_id}
        Refusal ID: {appeal.refusal_id}
        User: {appeal.user_id}
        Original Refusal: {refusal.reason}
        Appeal Reason: {appeal.appeal_reason}
        Escalation Reason: {escalation_reason}

        This appeal requires governance review and voting.
        """

        # Determine voting parameters based on urgency
        voting_duration = timedelta(days=3)
        voting_method = VotingMethod.SIMPLE_MAJORITY

        if urgency == "urgent":
            voting_duration = timedelta(hours=24)
            voting_method = VotingMethod.SUPERMAJORITY

        proposal = governance_engine.create_proposal(
            title=proposal_title,
            description=proposal_description,
            proposal_type=ProposalType.POLICY_CHANGE,
            proposer_id="refusal_governance_system",
            voting_duration=voting_duration,
            voting_method=voting_method,
            execution_data={
                "action_type": "appeal_decision",
                "appeal_id": appeal_id,
                "refusal_id": appeal.refusal_id,
            },
        )

        # Update appeal status
        appeal.status = AppealStatus.ESCALATED
        appeal.governance_proposal_id = proposal.proposal_id
        refusal.appeal_status = AppealStatus.ESCALATED

        self.refusal_stats["governance_escalations"] += 1

        logger.info(
            f"Appeal escalated to governance: {appeal_id} -> proposal {proposal.proposal_id}"
        )
        return proposal.proposal_id

    def _analyze_refusal_patterns(self, user_id: str):
        """Analyze refusal patterns for suspicious behavior"""

        user_refusals = self.refusal_patterns[user_id]
        if len(user_refusals) < 3:
            return  # Need minimum refusals for pattern analysis

        # Analyze recent refusals
        cutoff_time = datetime.now(timezone.utc) - timedelta(
            hours=self.escalation_thresholds["pattern_analysis_window"]
        )
        recent_refusals = [
            r for r in user_refusals if r.decision_timestamp >= cutoff_time
        ]

        if (
            len(recent_refusals)
            >= self.escalation_thresholds["auto_escalation_threshold"]
        ):
            # Pattern detected - flag for review
            self._flag_pattern_violation(user_id, recent_refusals)

    def _flag_pattern_violation(self, user_id: str, refusals: List[RefusalDecision]):
        """Flag a pattern violation for governance review"""

        pattern_types = [r.refusal_type for r in refusals]
        severity_levels = [r.severity for r in refusals]

        # Create governance proposal for pattern review
        proposal_title = f"Pattern Violation Review: User {user_id}"
        proposal_description = f"""
        User {user_id} has triggered pattern detection with {len(refusals)} refusals in the last 24 hours.

        Refusal Types: {', '.join([t.value for t in pattern_types])}
        Severity Levels: {', '.join([s.value for s in severity_levels])}

        This pattern requires governance review for potential policy violations or systemic issues.
        """

        proposal = governance_engine.create_proposal(
            title=proposal_title,
            description=proposal_description,
            proposal_type=ProposalType.MEMBERSHIP_CHANGE,
            proposer_id="pattern_detection_system",
            voting_duration=timedelta(days=2),
            voting_method=VotingMethod.SIMPLE_MAJORITY,
            execution_data={
                "action_type": "pattern_review",
                "user_id": user_id,
                "refusal_ids": [r.refusal_id for r in refusals],
            },
        )

        self.refusal_stats["pattern_violations"] += 1

        logger.warning(
            f"Pattern violation flagged for user {user_id}: proposal {proposal.proposal_id}"
        )

    def _check_appeal_escalation(self, appeal: RefusalAppeal):
        """Check if appeal should be automatically escalated"""

        refusal = self.refusal_decisions[appeal.refusal_id]

        # Auto-escalate high severity refusals
        if refusal.severity == RefusalSeverity.CRITICAL:
            self.escalate_to_governance(
                appeal.appeal_id, "Critical severity auto-escalation", "urgent"
            )
            return

        # Auto-escalate low confidence decisions
        if (
            refusal.confidence_score
            < self.escalation_thresholds["quality_review_confidence"]
        ):
            self.escalate_to_governance(
                appeal.appeal_id, "Low confidence decision review"
            )
            return

        # Check user appeal history
        user_appeals = [a for a in self.appeals.values() if a.user_id == appeal.user_id]
        if len(user_appeals) >= self.escalation_thresholds["auto_escalation_threshold"]:
            self.escalate_to_governance(appeal.appeal_id, "Multiple appeals from user")

    def get_refusal_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive refusal analytics"""

        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        recent_refusals = [
            r
            for r in self.refusal_decisions.values()
            if r.decision_timestamp >= cutoff_time
        ]

        # Type breakdown
        type_stats = defaultdict(int)
        for refusal in recent_refusals:
            type_stats[refusal.refusal_type.value] += 1

        # Severity breakdown
        severity_stats = defaultdict(int)
        for refusal in recent_refusals:
            severity_stats[refusal.severity.value] += 1

        # Decision maker breakdown
        decision_maker_stats = defaultdict(int)
        for refusal in recent_refusals:
            decision_maker_stats[refusal.decision_maker] += 1

        # Appeal statistics
        recent_appeals = [
            a for a in self.appeals.values() if a.submitted_at >= cutoff_time
        ]
        appeal_outcome_stats = defaultdict(int)
        for appeal in recent_appeals:
            appeal_outcome_stats[appeal.status.value] += 1

        return {
            "period_days": days,
            "total_refusals": len(recent_refusals),
            "total_appeals": len(recent_appeals),
            "refusal_by_type": dict(type_stats),
            "refusal_by_severity": dict(severity_stats),
            "refusal_by_decision_maker": dict(decision_maker_stats),
            "appeal_outcomes": dict(appeal_outcome_stats),
            "appeal_rate": len(recent_appeals) / max(len(recent_refusals), 1),
            "escalation_stats": {
                "governance_votes": self.refusal_stats["governance_escalations"],
                "pattern_violations": self.refusal_stats["pattern_violations"],
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_user_refusal_history(
        self, user_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get refusal history for a specific user"""

        user_refusals = self.refusal_patterns.get(user_id, [])
        user_refusals.sort(key=lambda r: r.decision_timestamp, reverse=True)

        history = []
        for refusal in user_refusals[:limit]:
            appeal_info = None
            if refusal.appeal_id and refusal.appeal_id in self.appeals:
                appeal = self.appeals[refusal.appeal_id]
                appeal_info = {
                    "appeal_id": appeal.appeal_id,
                    "status": appeal.status.value,
                    "submitted_at": appeal.submitted_at.isoformat(),
                    "appeal_reason": appeal.appeal_reason,
                }

            history.append(
                {
                    "refusal_id": refusal.refusal_id,
                    "refusal_type": refusal.refusal_type.value,
                    "severity": refusal.severity.value,
                    "reason": refusal.reason,
                    "timestamp": refusal.decision_timestamp.isoformat(),
                    "decision_maker": refusal.decision_maker,
                    "confidence_score": refusal.confidence_score,
                    "appeal_info": appeal_info,
                }
            )

        return history


# Global refusal governance engine
refusal_governance = RefusalGovernanceEngine()


def register_automatic_reviewer(
    reviewer_func: Callable[[RefusalDecision], Optional[str]],
):
    """Register an automatic reviewer function"""
    refusal_governance.automatic_reviewers.append(reviewer_func)


# Built-in automatic reviewers
def ethics_reviewer(refusal: RefusalDecision) -> Optional[str]:
    """Automatic ethics review for certain refusal types"""
    if (
        refusal.refusal_type == RefusalType.ETHICAL_VIOLATION
        and refusal.confidence_score < 0.7
    ):
        return "Low confidence ethical violation requires human review"
    return None


def safety_reviewer(refusal: RefusalDecision) -> Optional[str]:
    """Automatic safety review for safety concerns"""
    if (
        refusal.refusal_type == RefusalType.SAFETY_CONCERN
        and refusal.severity == RefusalSeverity.CRITICAL
    ):
        return "Critical safety concern requires immediate escalation"
    return None


# Register built-in reviewers
register_automatic_reviewer(ethics_reviewer)
register_automatic_reviewer(safety_reviewer)
