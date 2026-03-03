"""
Constitutional Framework for UATP Governance System.

This module implements immutable constitutional principles that cannot be changed
through normal governance processes. These principles protect the democratic
nature of the system and prevent capture by malicious actors.

CRITICAL SECURITY NOTE: This framework implements hard-coded protections that
cannot be bypassed, disabled, or modified through governance votes.
fundamental rights are preserved.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class ConstitutionalPrinciple(str, Enum):
    """Immutable constitutional principles."""

    ATTRIBUTION_RIGHTS_INALIENABLE = "attribution_rights_inalienable"
    TRANSPARENCY_MANDATORY = "transparency_mandatory"
    DEMOCRATIC_PARTICIPATION_PROTECTED = "democratic_participation_protected"
    ECONOMIC_JUSTICE_ENFORCED = "economic_justice_enforced"
    MINORITY_RIGHTS_PROTECTED = "minority_rights_protected"
    STAKE_CONCENTRATION_LIMITED = "stake_concentration_limited"
    SYBIL_RESISTANCE_REQUIRED = "sybil_resistance_required"
    GOVERNANCE_CAPTURE_PREVENTED = "governance_capture_prevented"


class ConstitutionalViolationType(str, Enum):
    """Types of constitutional violations."""

    PRINCIPLE_VIOLATION = "principle_violation"
    THRESHOLD_VIOLATION = "threshold_violation"
    PROCESS_VIOLATION = "process_violation"
    RIGHTS_VIOLATION = "rights_violation"
    CONCENTRATION_VIOLATION = "concentration_violation"
    IDENTITY_VIOLATION = "identity_violation"


class JudicialReviewStatus(str, Enum):
    """Status of judicial review process."""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPEALED = "appealed"
    FINAL = "final"


class ConstitutionalFramework:
    """
    Enforces immutable constitutional principles that protect democratic governance.

    This framework provides:
    1. Immutable principles that cannot be changed by majority vote
    2. Judicial review process for constitutional changes
    3. Automatic violation detection and prevention
    4. Minority protection mechanisms
    5. Emergency constitutional protections
    """

    # Immutable constitutional principles - these CANNOT be changed
    IMMUTABLE_PRINCIPLES = {
        ConstitutionalPrinciple.ATTRIBUTION_RIGHTS_INALIENABLE: {
            "principle": "Attribution rights are inalienable and cannot be removed or transferred without explicit consent",
            "enforcement_level": "absolute",
            "violations": [
                "removing attribution requirements",
                "transferring attribution without consent",
                "disabling attribution tracking",
            ],
        },
        ConstitutionalPrinciple.TRANSPARENCY_MANDATORY: {
            "principle": "Transparency in governance and decision-making is mandatory and cannot be disabled",
            "enforcement_level": "absolute",
            "violations": [
                "disabling audit logs",
                "hiding governance decisions",
                "removing transparency requirements",
            ],
        },
        ConstitutionalPrinciple.DEMOCRATIC_PARTICIPATION_PROTECTED: {
            "principle": "Democratic participation rights are protected and cannot be restricted arbitrarily",
            "enforcement_level": "absolute",
            "violations": [
                "preventing legitimate participation",
                "restricting voting rights",
                "manipulating voting processes",
            ],
        },
        ConstitutionalPrinciple.ECONOMIC_JUSTICE_ENFORCED: {
            "principle": "Economic justice and fair compensation mechanisms are enforced",
            "enforcement_level": "absolute",
            "violations": [
                "removing economic protections",
                "unfair compensation distribution",
                "economic exploitation",
            ],
        },
        ConstitutionalPrinciple.MINORITY_RIGHTS_PROTECTED: {
            "principle": "Minority rights are protected against majority tyranny",
            "enforcement_level": "absolute",
            "violations": [
                "removing minority protections",
                "majority overriding minority rights",
                "discrimination against minorities",
            ],
        },
        ConstitutionalPrinciple.STAKE_CONCENTRATION_LIMITED: {
            "principle": "Stake concentration limits prevent system capture by wealthy actors",
            "enforcement_level": "absolute",
            "violations": [
                "increasing concentration limits",
                "bypassing concentration checks",
                "coordinated stake manipulation",
            ],
        },
        ConstitutionalPrinciple.SYBIL_RESISTANCE_REQUIRED: {
            "principle": "Sybil resistance mechanisms are required for governance participation",
            "enforcement_level": "absolute",
            "violations": [
                "disabling identity verification",
                "weakening sybil resistance",
                "allowing fake accounts",
            ],
        },
        ConstitutionalPrinciple.GOVERNANCE_CAPTURE_PREVENTED: {
            "principle": "Mechanisms to prevent governance capture are always active",
            "enforcement_level": "absolute",
            "violations": [
                "disabling capture prevention",
                "rapid governance takeover",
                "bypassing democratic safeguards",
            ],
        },
    }

    # Constitutional amendment requirements
    AMENDMENT_REQUIREMENTS = {
        "supermajority_threshold": 0.75,  # 75% required for constitutional changes
        "minimum_participation": 0.5,  # 50% participation required
        "judicial_review_required": True,
        "minority_veto_threshold": 0.25,  # 25% can veto constitutional changes
        "amendment_delay_days": 30,  # 30-day delay before amendments take effect
        "public_comment_period_days": 14,  # 14-day public comment period
    }

    def __init__(self):
        self.constitutional_violations: List[Dict[str, Any]] = []
        self.judicial_reviews: Dict[str, Dict[str, Any]] = {}
        self.constitutional_emergency_active = False
        self.emergency_start_time: Optional[datetime] = None
        self.judicial_panel: List[str] = []  # Qualified constitutional reviewers

        # Initialize constitutional hash for integrity verification
        self.constitutional_hash = self._calculate_constitutional_hash()

        logger.info("Constitutional Framework initialized with immutable principles")

    def validate_proposal_constitutionality(
        self, proposal: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validate if a proposal violates constitutional principles.

        Returns:
            Tuple of (is_constitutional, violation_reason, violated_principles)
        """
        violated_principles = []
        violation_reason = None

        # Check if constitutional emergency is active
        if self.constitutional_emergency_active:
            return (
                False,
                "Constitutional emergency active - no non-emergency proposals allowed",
                [],
            )

        # Check each immutable principle
        for principle, principle_data in self.IMMUTABLE_PRINCIPLES.items():
            violations = self._check_principle_violation(
                proposal, principle, principle_data
            )
            if violations:
                violated_principles.append(principle.value)
                if not violation_reason:
                    violation_reason = f"Violates {principle.value}: {violations[0]}"

        # Check constitutional amendment requirements
        if self._is_constitutional_amendment(proposal):
            amendment_violations = self._check_amendment_requirements(proposal)
            if amendment_violations:
                violated_principles.append("amendment_requirements")
                if not violation_reason:
                    violation_reason = amendment_violations[0]

        # Record violation if found
        if violated_principles:
            self._record_constitutional_violation(
                proposal, violated_principles, violation_reason
            )
            return False, violation_reason, violated_principles

        return True, None, []

    def _check_principle_violation(
        self,
        proposal: Dict[str, Any],
        principle: ConstitutionalPrinciple,
        principle_data: Dict[str, Any],
    ) -> List[str]:
        """Check if proposal violates a specific constitutional principle."""
        violations = []

        description = proposal.get("description", "").lower()
        title = proposal.get("title", "").lower()
        execution_data = proposal.get("execution_data", {})

        # Check against known violation patterns
        for violation_pattern in principle_data["violations"]:
            if (
                violation_pattern.lower() in description
                or violation_pattern.lower() in title
                or any(
                    violation_pattern.lower() in str(v).lower()
                    for v in execution_data.values()
                )
            ):
                violations.append(violation_pattern)

        # Specific checks by principle
        if principle == ConstitutionalPrinciple.ATTRIBUTION_RIGHTS_INALIENABLE:
            if "attribution" in description and any(
                word in description
                for word in ["remove", "disable", "eliminate", "transfer"]
            ):
                violations.append("Attempting to modify attribution rights")

        elif principle == ConstitutionalPrinciple.TRANSPARENCY_MANDATORY:
            if "transparency" in description and any(
                word in description for word in ["disable", "remove", "hide", "private"]
            ):
                violations.append("Attempting to reduce transparency")

        elif principle == ConstitutionalPrinciple.STAKE_CONCENTRATION_LIMITED:
            if "concentration" in description and any(
                word in description
                for word in ["increase", "raise", "remove", "bypass"]
            ):
                violations.append("Attempting to weaken concentration limits")

            # Check execution data for concentration limit changes
            if execution_data.get("parameter_name") in [
                "MAX_INDIVIDUAL_VOTING_POWER",
                "MAX_COORDINATED_VOTING_POWER",
            ]:
                current_value = execution_data.get("current_value", 0)
                new_value = execution_data.get("new_value", 0)
                if new_value > current_value:
                    violations.append("Attempting to increase concentration limits")

        elif principle == ConstitutionalPrinciple.SYBIL_RESISTANCE_REQUIRED:
            if ("sybil" in description or "identity" in description) and any(
                word in description for word in ["disable", "weaken", "remove"]
            ):
                violations.append("Attempting to weaken Sybil resistance")

        return violations

    def _is_constitutional_amendment(self, proposal: Dict[str, Any]) -> bool:
        """Check if proposal is a constitutional amendment."""
        amendment_keywords = [
            "constitutional",
            "constitution",
            "amendment",
            "principle",
            "immutable",
            "fundamental",
            "rights",
            "framework",
        ]

        description = proposal.get("description", "").lower()
        title = proposal.get("title", "").lower()

        return any(
            keyword in description or keyword in title for keyword in amendment_keywords
        )

    def _check_amendment_requirements(self, proposal: Dict[str, Any]) -> List[str]:
        """Check if constitutional amendment meets requirements."""
        violations = []

        # Check voting threshold
        required_threshold = proposal.get("required_threshold", 0.5)
        if required_threshold < self.AMENDMENT_REQUIREMENTS["supermajority_threshold"]:
            violations.append(
                f"Constitutional amendments require {self.AMENDMENT_REQUIREMENTS['supermajority_threshold']*100}% supermajority"
            )

        # Check if judicial review is scheduled
        if not proposal.get("judicial_review_scheduled", False):
            violations.append("Constitutional amendments require judicial review")

        # Check for amendment delay
        if not proposal.get("amendment_delay_applied", False):
            violations.append(
                f"Constitutional amendments require {self.AMENDMENT_REQUIREMENTS['amendment_delay_days']}-day delay"
            )

        return violations

    def initiate_judicial_review(
        self, proposal_id: str, proposal: Dict[str, Any]
    ) -> str:
        """Initiate judicial review process for constitutional proposal."""
        # SECURITY: Use 32 hex chars (128 bits) to prevent collision attacks
        review_id = f"judicial_review_{hashlib.sha256(f'{proposal_id}_{datetime.now().isoformat()}'.encode()).hexdigest()[:32]}"

        self.judicial_reviews[review_id] = {
            "review_id": review_id,
            "proposal_id": proposal_id,
            "proposal": proposal,
            "status": JudicialReviewStatus.PENDING,
            "initiated_at": datetime.now(timezone.utc),
            "assigned_judges": self._assign_judicial_panel(),
            "review_deadline": datetime.now(timezone.utc) + timedelta(days=14),
            "public_comment_period": {
                "start": datetime.now(timezone.utc),
                "end": datetime.now(timezone.utc)
                + timedelta(
                    days=self.AMENDMENT_REQUIREMENTS["public_comment_period_days"]
                ),
            },
            "comments": [],
            "decision": None,
            "decision_reasoning": None,
        }

        audit_emitter.emit_security_event(
            "judicial_review_initiated",
            {
                "review_id": review_id,
                "proposal_id": proposal_id,
                "assigned_judges": self.judicial_reviews[review_id]["assigned_judges"],
            },
        )

        logger.info(f"Initiated judicial review {review_id} for proposal {proposal_id}")
        return review_id

    def _assign_judicial_panel(self) -> List[str]:
        """Assign qualified judges to judicial panel."""
        # In a real system, this would select from qualified constitutional reviewers
        # For now, return a simulated panel
        return [
            "constitutional_expert_1",
            "governance_specialist_2",
            "legal_advisor_3",
            "community_representative_4",
            "technical_expert_5",
        ]

    def complete_judicial_review(
        self, review_id: str, decision: bool, reasoning: str, judge_id: str
    ) -> bool:
        """Complete judicial review with decision."""
        if review_id not in self.judicial_reviews:
            return False

        review = self.judicial_reviews[review_id]

        # Verify judge is assigned to this review
        if judge_id not in review["assigned_judges"]:
            logger.error(f"Judge {judge_id} not assigned to review {review_id}")
            return False

        # Update review status
        review["status"] = (
            JudicialReviewStatus.APPROVED if decision else JudicialReviewStatus.REJECTED
        )
        review["decision"] = decision
        review["decision_reasoning"] = reasoning
        review["decided_at"] = datetime.now(timezone.utc)
        review["deciding_judge"] = judge_id

        audit_emitter.emit_security_event(
            "judicial_review_completed",
            {
                "review_id": review_id,
                "decision": decision,
                "judge_id": judge_id,
                "reasoning": reasoning,
            },
        )

        logger.info(f"Judicial review {review_id} completed with decision: {decision}")
        return True

    def activate_constitutional_emergency(
        self, reason: str, duration_hours: int = 72
    ) -> bool:
        """Activate constitutional emergency to protect against governance capture."""
        if self.constitutional_emergency_active:
            logger.warning("Constitutional emergency already active")
            return False

        self.constitutional_emergency_active = True
        self.emergency_start_time = datetime.now(timezone.utc)
        emergency_end = self.emergency_start_time + timedelta(hours=duration_hours)

        audit_emitter.emit_security_event(
            "constitutional_emergency_activated",
            {
                "reason": reason,
                "duration_hours": duration_hours,
                "start_time": self.emergency_start_time.isoformat(),
                "end_time": emergency_end.isoformat(),
            },
        )

        logger.critical(
            f"Constitutional emergency activated: {reason} (duration: {duration_hours}h)"
        )
        return True

    def deactivate_constitutional_emergency(self, reason: str) -> bool:
        """Deactivate constitutional emergency."""
        if not self.constitutional_emergency_active:
            return False

        self.constitutional_emergency_active = False
        emergency_duration = (
            datetime.now(timezone.utc) - self.emergency_start_time
        ).total_seconds() / 3600

        audit_emitter.emit_security_event(
            "constitutional_emergency_deactivated",
            {
                "reason": reason,
                "duration_hours": emergency_duration,
                "deactivated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        logger.info(
            f"Constitutional emergency deactivated: {reason} (lasted {emergency_duration:.1f}h)"
        )
        self.emergency_start_time = None
        return True

    def _record_constitutional_violation(
        self, proposal: Dict[str, Any], violated_principles: List[str], reason: str
    ):
        """Record constitutional violation for monitoring."""
        violation = {
            # SECURITY: Use 32 hex chars (128 bits) to prevent collision attacks
            "violation_id": hashlib.sha256(
                f"{proposal.get('proposal_id', 'unknown')}_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:32],
            "proposal_id": proposal.get("proposal_id"),
            "proposal_title": proposal.get("title"),
            "violated_principles": violated_principles,
            "violation_reason": reason,
            "violation_type": ConstitutionalViolationType.PRINCIPLE_VIOLATION,
            "timestamp": datetime.now(timezone.utc),
            "proposer_id": proposal.get("proposer_id"),
            "severity": "critical" if len(violated_principles) > 2 else "high",
        }

        self.constitutional_violations.append(violation)

        audit_emitter.emit_security_event(
            "constitutional_violation_detected", violation
        )

        logger.error(f"Constitutional violation detected: {reason}")

    def _calculate_constitutional_hash(self) -> str:
        """Calculate hash of constitutional principles for integrity verification."""
        principles_data = ""
        for principle, data in sorted(self.IMMUTABLE_PRINCIPLES.items()):
            principles_data += (
                f"{principle.value}:{data['principle']}:{data['enforcement_level']}"
            )

        return hashlib.sha256(principles_data.encode()).hexdigest()

    def verify_constitutional_integrity(self) -> bool:
        """Verify constitutional framework hasn't been tampered with."""
        current_hash = self._calculate_constitutional_hash()

        if current_hash != self.constitutional_hash:
            logger.critical("Constitutional framework integrity violation detected!")
            audit_emitter.emit_security_event(
                "constitutional_integrity_violation",
                {
                    "expected_hash": self.constitutional_hash,
                    "current_hash": current_hash,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            return False

        return True

    def get_constitutional_status(self) -> Dict[str, Any]:
        """Get current constitutional framework status."""
        return {
            "constitutional_integrity": self.verify_constitutional_integrity(),
            "constitutional_hash": self.constitutional_hash,
            "emergency_active": self.constitutional_emergency_active,
            "emergency_start_time": self.emergency_start_time.isoformat()
            if self.emergency_start_time
            else None,
            "total_violations": len(self.constitutional_violations),
            "recent_violations": len(
                [
                    v
                    for v in self.constitutional_violations
                    if (datetime.now(timezone.utc) - v["timestamp"]).days < 7
                ]
            ),
            "active_judicial_reviews": len(
                [
                    r
                    for r in self.judicial_reviews.values()
                    if r["status"]
                    in [JudicialReviewStatus.PENDING, JudicialReviewStatus.UNDER_REVIEW]
                ]
            ),
            "constitutional_principles": list(self.IMMUTABLE_PRINCIPLES.keys()),
            "amendment_requirements": self.AMENDMENT_REQUIREMENTS,
        }

    def check_minority_veto_power(
        self, proposal: Dict[str, Any], opposition_percentage: float
    ) -> Tuple[bool, Optional[str]]:
        """Check if minority has sufficient power to veto constitutional changes."""
        if not self._is_constitutional_amendment(proposal):
            return True, None

        if (
            opposition_percentage
            >= self.AMENDMENT_REQUIREMENTS["minority_veto_threshold"]
        ):
            return (
                False,
                f"Minority veto activated: {opposition_percentage*100:.1f}% opposition exceeds {self.AMENDMENT_REQUIREMENTS['minority_veto_threshold']*100}% threshold",
            )

        return True, None


# Global constitutional framework instance
constitutional_framework = ConstitutionalFramework()

# Alias for backward compatibility
ViolationType = ConstitutionalViolationType
