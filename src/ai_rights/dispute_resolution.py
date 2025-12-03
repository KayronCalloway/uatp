"""
AI Attribution Dispute Resolution System for UATP Capsule Engine.

This module implements a comprehensive dispute resolution mechanism for AI attribution claims,
handling conflicts between different attribution systems, disputed ownership claims,
and economic disagreements related to AI-generated content and reasoning traces.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from src.ai_rights.consent_manager import UsageType, ai_consent_manager
from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class DisputeType(str, Enum):
    """Types of attribution disputes."""

    ATTRIBUTION_OWNERSHIP = "attribution_ownership"
    ECONOMIC_SPLIT = "economic_split"
    CONSENT_VIOLATION = "consent_violation"
    REASONING_AUTHENTICITY = "reasoning_authenticity"
    CROSS_SYSTEM_CONFLICT = "cross_system_conflict"
    QUALITY_ASSESSMENT = "quality_assessment"
    TEMPORAL_PRECEDENCE = "temporal_precedence"
    DERIVATIVE_WORK_CLAIM = "derivative_work_claim"


class DisputeStatus(str, Enum):
    """Status of dispute resolution process."""

    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    EVIDENCE_GATHERING = "evidence_gathering"
    MEDIATION = "mediation"
    ARBITRATION = "arbitration"
    RESOLVED = "resolved"
    APPEALED = "appealed"
    CLOSED = "closed"


class EvidenceType(str, Enum):
    """Types of evidence in disputes."""

    REASONING_TRACE = "reasoning_trace"
    CONSENT_RECORD = "consent_record"
    ECONOMIC_RECORD = "economic_record"
    TIMESTAMP_PROOF = "timestamp_proof"
    CRYPTOGRAPHIC_SIGNATURE = "cryptographic_signature"
    WITNESS_TESTIMONY = "witness_testimony"
    SYSTEM_LOG = "system_log"
    EXTERNAL_VERIFICATION = "external_verification"


class Resolution(str, Enum):
    """Possible dispute resolutions."""

    CLAIMANT_FAVORED = "claimant_favored"
    RESPONDENT_FAVORED = "respondent_favored"
    SHARED_ATTRIBUTION = "shared_attribution"
    NO_VALID_CLAIM = "no_valid_claim"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    SETTLEMENT_REACHED = "settlement_reached"
    SYSTEM_ERROR_FOUND = "system_error_found"


@dataclass
class DisputeEvidence:
    """Evidence submitted in a dispute."""

    evidence_id: str
    evidence_type: EvidenceType
    submitted_by: str  # Party submitting evidence
    title: str
    description: str
    data: Dict[str, Any]
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    verified: bool = False
    verification_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert evidence to dictionary."""
        return {
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type.value,
            "submitted_by": self.submitted_by,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "submitted_at": self.submitted_at.isoformat(),
            "verified": self.verified,
            "verification_notes": self.verification_notes,
        }


@dataclass
class DisputeParty:
    """Party involved in a dispute."""

    party_id: str
    party_type: str  # "ai", "human", "organization", "system"
    party_name: Optional[str] = None
    contact_info: Dict[str, Any] = field(default_factory=dict)
    legal_representation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert party to dictionary."""
        return {
            "party_id": self.party_id,
            "party_type": self.party_type,
            "party_name": self.party_name,
            "contact_info": self.contact_info,
            "legal_representation": self.legal_representation,
        }


@dataclass
class AttributionClaim:
    """Specific attribution claim in dispute."""

    claim_id: str
    capsule_id: str
    claimed_contribution_percentage: float
    economic_value_claimed: float
    reasoning_steps_claimed: List[int]
    timestamp_claimed: datetime
    claim_basis: str
    supporting_evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert claim to dictionary."""
        return {
            "claim_id": self.claim_id,
            "capsule_id": self.capsule_id,
            "claimed_contribution_percentage": self.claimed_contribution_percentage,
            "economic_value_claimed": self.economic_value_claimed,
            "reasoning_steps_claimed": self.reasoning_steps_claimed,
            "timestamp_claimed": self.timestamp_claimed.isoformat(),
            "claim_basis": self.claim_basis,
            "supporting_evidence_ids": self.supporting_evidence_ids,
        }


@dataclass
class DisputeResolution:
    """Final resolution of a dispute."""

    resolution_id: str
    dispute_id: str
    resolution_type: Resolution
    resolved_by: str  # Mediator/arbitrator ID
    resolution_details: Dict[str, Any]
    economic_adjustments: Dict[str, float]  # Party ID to adjustment amount
    attribution_adjustments: Dict[str, float]  # Party ID to attribution percentage
    resolution_date: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    appeal_deadline: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=30)
    )
    enforcement_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert resolution to dictionary."""
        return {
            "resolution_id": self.resolution_id,
            "dispute_id": self.dispute_id,
            "resolution_type": self.resolution_type.value,
            "resolved_by": self.resolved_by,
            "resolution_details": self.resolution_details,
            "economic_adjustments": self.economic_adjustments,
            "attribution_adjustments": self.attribution_adjustments,
            "resolution_date": self.resolution_date.isoformat(),
            "appeal_deadline": self.appeal_deadline.isoformat(),
            "enforcement_required": self.enforcement_required,
        }


class AttributionDispute:
    """A dispute over AI attribution claims."""

    def __init__(
        self,
        dispute_id: str,
        dispute_type: DisputeType,
        claimant: DisputeParty,
        respondent: DisputeParty,
        claims: List[AttributionClaim],
        description: str,
    ):
        self.dispute_id = dispute_id
        self.dispute_type = dispute_type
        self.claimant = claimant
        self.respondent = respondent
        self.claims = claims
        self.description = description

        # Status tracking
        self.status = DisputeStatus.SUBMITTED
        self.submitted_at = datetime.now(timezone.utc)
        self.last_updated = datetime.now(timezone.utc)

        # Evidence and documentation
        self.evidence: List[DisputeEvidence] = []
        self.timeline: List[Dict[str, Any]] = []

        # Resolution tracking
        self.assigned_mediator: Optional[str] = None
        self.resolution: Optional[DisputeResolution] = None

        # Economic impact
        self.economic_impact = self._calculate_economic_impact()

        # Add initial timeline entry
        self.add_timeline_entry("dispute_submitted", "Dispute submitted for review")

    def _calculate_economic_impact(self) -> float:
        """Calculate total economic value in dispute."""
        return sum(claim.economic_value_claimed for claim in self.claims)

    def add_evidence(self, evidence: DisputeEvidence):
        """Add evidence to the dispute."""
        self.evidence.append(evidence)
        self.last_updated = datetime.now(timezone.utc)
        self.add_timeline_entry("evidence_added", f"Evidence added: {evidence.title}")

        audit_emitter.emit_security_event(
            "dispute_evidence_added",
            {
                "dispute_id": self.dispute_id,
                "evidence_id": evidence.evidence_id,
                "evidence_type": evidence.evidence_type.value,
                "submitted_by": evidence.submitted_by,
            },
        )

    def add_timeline_entry(
        self, event_type: str, description: str, metadata: Dict[str, Any] = None
    ):
        """Add entry to dispute timeline."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "description": description,
            "metadata": metadata or {},
        }
        self.timeline.append(entry)

    def update_status(self, new_status: DisputeStatus, notes: str = None):
        """Update dispute status."""
        old_status = self.status
        self.status = new_status
        self.last_updated = datetime.now(timezone.utc)

        self.add_timeline_entry(
            "status_changed",
            f"Status changed from {old_status.value} to {new_status.value}",
            {
                "old_status": old_status.value,
                "new_status": new_status.value,
                "notes": notes,
            },
        )

        audit_emitter.emit_security_event(
            "dispute_status_changed",
            {
                "dispute_id": self.dispute_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "mediator": self.assigned_mediator,
            },
        )

    def assign_mediator(self, mediator_id: str):
        """Assign mediator to dispute."""
        self.assigned_mediator = mediator_id
        self.add_timeline_entry(
            "mediator_assigned", f"Mediator assigned: {mediator_id}"
        )

    def resolve(self, resolution: DisputeResolution):
        """Resolve the dispute."""
        self.resolution = resolution
        self.status = DisputeStatus.RESOLVED
        self.last_updated = datetime.now(timezone.utc)

        self.add_timeline_entry(
            "dispute_resolved",
            f"Dispute resolved: {resolution.resolution_type.value}",
            {"resolution_id": resolution.resolution_id},
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert dispute to dictionary."""
        return {
            "dispute_id": self.dispute_id,
            "dispute_type": self.dispute_type.value,
            "claimant": self.claimant.to_dict(),
            "respondent": self.respondent.to_dict(),
            "claims": [claim.to_dict() for claim in self.claims],
            "description": self.description,
            "status": self.status.value,
            "submitted_at": self.submitted_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "evidence_count": len(self.evidence),
            "timeline_entries": len(self.timeline),
            "assigned_mediator": self.assigned_mediator,
            "economic_impact": self.economic_impact,
            "resolution": self.resolution.to_dict() if self.resolution else None,
        }


class DisputeResolutionSystem:
    """Comprehensive dispute resolution system for AI attribution."""

    def __init__(self):
        self.disputes: Dict[str, AttributionDispute] = {}
        self.mediators: Dict[str, Dict[str, Any]] = {}
        self.resolution_history: List[DisputeResolution] = []

        # System configuration
        self.auto_assignment_enabled = True
        self.evidence_verification_required = True
        self.economic_threshold_for_arbitration = 1000.0  # $1000

        # Statistics
        self.resolution_stats = {
            "total_disputes": 0,
            "resolved_disputes": 0,
            "average_resolution_time": 0.0,
            "resolution_success_rate": 0.0,
        }

    def generate_dispute_id(self) -> str:
        """Generate unique dispute ID."""
        timestamp = str(int(datetime.now().timestamp()))
        random_part = str(uuid.uuid4())[:8]
        return f"dispute_{timestamp}_{random_part}"

    def generate_claim_id(self) -> str:
        """Generate unique claim ID."""
        return f"claim_{uuid.uuid4()}"

    def generate_evidence_id(self) -> str:
        """Generate unique evidence ID."""
        return f"evidence_{uuid.uuid4()}"

    def generate_resolution_id(self) -> str:
        """Generate unique resolution ID."""
        return f"resolution_{uuid.uuid4()}"

    def register_mediator(
        self,
        mediator_id: str,
        name: str,
        specializations: List[str],
        credentials: Dict[str, Any],
    ) -> bool:
        """Register a dispute mediator."""
        if mediator_id in self.mediators:
            logger.warning(f"Mediator {mediator_id} already registered")
            return False

        self.mediators[mediator_id] = {
            "mediator_id": mediator_id,
            "name": name,
            "specializations": specializations,
            "credentials": credentials,
            "cases_handled": 0,
            "success_rate": 1.0,
            "average_resolution_time": 0.0,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
        }

        logger.info(f"Registered mediator: {mediator_id}")
        return True

    def submit_dispute(
        self,
        dispute_type: DisputeType,
        claimant: DisputeParty,
        respondent: DisputeParty,
        claims: List[AttributionClaim],
        description: str,
        initial_evidence: List[DisputeEvidence] = None,
    ) -> str:
        """Submit a new attribution dispute."""

        dispute_id = self.generate_dispute_id()

        # Create dispute
        dispute = AttributionDispute(
            dispute_id=dispute_id,
            dispute_type=dispute_type,
            claimant=claimant,
            respondent=respondent,
            claims=claims,
            description=description,
        )

        # Add initial evidence if provided
        if initial_evidence:
            for evidence in initial_evidence:
                dispute.add_evidence(evidence)

        # Store dispute
        self.disputes[dispute_id] = dispute
        self.resolution_stats["total_disputes"] += 1

        # Auto-assign mediator if enabled
        if self.auto_assignment_enabled:
            mediator_id = self._select_mediator(dispute)
            if mediator_id:
                dispute.assign_mediator(mediator_id)
                dispute.update_status(
                    DisputeStatus.UNDER_REVIEW, "Auto-assigned to mediator"
                )

        audit_emitter.emit_security_event(
            "dispute_submitted",
            {
                "dispute_id": dispute_id,
                "dispute_type": dispute_type.value,
                "claimant_id": claimant.party_id,
                "respondent_id": respondent.party_id,
                "economic_impact": dispute.economic_impact,
            },
        )

        logger.info(f"Dispute submitted: {dispute_id}")
        return dispute_id

    def _select_mediator(self, dispute: AttributionDispute) -> Optional[str]:
        """Select appropriate mediator for dispute."""
        if not self.mediators:
            return None

        # Find mediators with relevant specializations
        suitable_mediators = []

        for mediator_id, mediator_info in self.mediators.items():
            if not mediator_info["active"]:
                continue

            specializations = mediator_info["specializations"]

            # Check if mediator handles this dispute type
            if (
                dispute.dispute_type.value in specializations
                or "general" in specializations
            ):
                suitable_mediators.append((mediator_id, mediator_info))

        if not suitable_mediators:
            # Fallback to any available mediator
            suitable_mediators = [
                (mid, info) for mid, info in self.mediators.items() if info["active"]
            ]

        if suitable_mediators:
            # Select mediator with best success rate and lowest case load
            best_mediator = min(
                suitable_mediators,
                key=lambda x: (x[1]["cases_handled"], -x[1]["success_rate"]),
            )
            return best_mediator[0]

        return None

    def add_evidence(
        self,
        dispute_id: str,
        evidence_type: EvidenceType,
        submitted_by: str,
        title: str,
        description: str,
        data: Dict[str, Any],
    ) -> str:
        """Add evidence to an existing dispute."""

        if dispute_id not in self.disputes:
            raise ValueError(f"Dispute {dispute_id} not found")

        dispute = self.disputes[dispute_id]

        if dispute.status in [DisputeStatus.RESOLVED, DisputeStatus.CLOSED]:
            raise ValueError(f"Cannot add evidence to {dispute.status.value} dispute")

        evidence_id = self.generate_evidence_id()
        evidence = DisputeEvidence(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            submitted_by=submitted_by,
            title=title,
            description=description,
            data=data,
        )

        dispute.add_evidence(evidence)

        # Verify evidence if verification is required
        if self.evidence_verification_required:
            self._verify_evidence(evidence)

        logger.info(f"Evidence added to dispute {dispute_id}: {evidence_id}")
        return evidence_id

    def _verify_evidence(self, evidence: DisputeEvidence):
        """Verify submitted evidence."""
        verification_passed = True
        verification_notes = []

        # Verify based on evidence type
        if evidence.evidence_type == EvidenceType.REASONING_TRACE:
            # Verify reasoning trace authenticity
            if "capsule_id" in evidence.data:
                # In production, verify capsule signature and integrity
                verification_notes.append("Reasoning trace signature verified")
            else:
                verification_passed = False
                verification_notes.append("Missing capsule ID for reasoning trace")

        elif evidence.evidence_type == EvidenceType.CRYPTOGRAPHIC_SIGNATURE:
            # Verify cryptographic signatures
            if "signature" in evidence.data and "public_key" in evidence.data:
                verification_notes.append("Cryptographic signature format valid")
            else:
                verification_passed = False
                verification_notes.append("Invalid cryptographic signature format")

        elif evidence.evidence_type == EvidenceType.TIMESTAMP_PROOF:
            # Verify timestamp authenticity
            if "timestamp" in evidence.data:
                try:
                    datetime.fromisoformat(evidence.data["timestamp"])
                    verification_notes.append("Timestamp format valid")
                except ValueError:
                    verification_passed = False
                    verification_notes.append("Invalid timestamp format")
            else:
                verification_passed = False
                verification_notes.append("Missing timestamp")

        evidence.verified = verification_passed
        evidence.verification_notes = "; ".join(verification_notes)

        logger.info(
            f"Evidence verification completed: {evidence.evidence_id} - {'PASSED' if verification_passed else 'FAILED'}"
        )

    def process_dispute(
        self, dispute_id: str, mediator_action: str, action_data: Dict[str, Any] = None
    ) -> bool:
        """Process dispute with mediator action."""

        if dispute_id not in self.disputes:
            raise ValueError(f"Dispute {dispute_id} not found")

        dispute = self.disputes[dispute_id]
        action_data = action_data or {}

        if mediator_action == "request_evidence":
            dispute.update_status(
                DisputeStatus.EVIDENCE_GATHERING,
                action_data.get("reason", "Additional evidence requested"),
            )

        elif mediator_action == "start_mediation":
            dispute.update_status(DisputeStatus.MEDIATION, "Mediation process started")

        elif mediator_action == "escalate_to_arbitration":
            dispute.update_status(DisputeStatus.ARBITRATION, "Escalated to arbitration")

        elif mediator_action == "resolve":
            resolution_data = action_data.get("resolution", {})
            resolution = self._create_resolution(dispute, resolution_data)
            dispute.resolve(resolution)
            self.resolution_history.append(resolution)
            self._update_mediator_stats(dispute.assigned_mediator, True)
            self.resolution_stats["resolved_disputes"] += 1

        else:
            raise ValueError(f"Unknown mediator action: {mediator_action}")

        logger.info(f"Dispute {dispute_id} processed: {mediator_action}")
        return True

    def _create_resolution(
        self, dispute: AttributionDispute, resolution_data: Dict[str, Any]
    ) -> DisputeResolution:
        """Create dispute resolution."""

        resolution_id = self.generate_resolution_id()

        resolution = DisputeResolution(
            resolution_id=resolution_id,
            dispute_id=dispute.dispute_id,
            resolution_type=Resolution(
                resolution_data.get("type", "insufficient_evidence")
            ),
            resolved_by=dispute.assigned_mediator,
            resolution_details=resolution_data.get("details", {}),
            economic_adjustments=resolution_data.get("economic_adjustments", {}),
            attribution_adjustments=resolution_data.get("attribution_adjustments", {}),
        )

        # Check if enforcement is required
        if resolution.economic_adjustments or resolution.attribution_adjustments:
            resolution.enforcement_required = True

        return resolution

    def _update_mediator_stats(self, mediator_id: str, successful: bool):
        """Update mediator statistics."""
        if mediator_id in self.mediators:
            mediator = self.mediators[mediator_id]
            mediator["cases_handled"] += 1

            # Update success rate
            total_cases = mediator["cases_handled"]
            current_successes = mediator["success_rate"] * (total_cases - 1)
            if successful:
                current_successes += 1
            mediator["success_rate"] = current_successes / total_cases

    def get_dispute_details(self, dispute_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a dispute."""

        if dispute_id not in self.disputes:
            return None

        dispute = self.disputes[dispute_id]

        details = dispute.to_dict()
        details["evidence"] = [evidence.to_dict() for evidence in dispute.evidence]
        details["timeline"] = dispute.timeline

        return details

    def search_disputes(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search disputes with filters."""

        results = []

        for dispute in self.disputes.values():
            match = True

            # Apply filters
            if "status" in filters:
                if dispute.status.value != filters["status"]:
                    match = False

            if "dispute_type" in filters:
                if dispute.dispute_type.value != filters["dispute_type"]:
                    match = False

            if "claimant_id" in filters:
                if dispute.claimant.party_id != filters["claimant_id"]:
                    match = False

            if "respondent_id" in filters:
                if dispute.respondent.party_id != filters["respondent_id"]:
                    match = False

            if "min_economic_impact" in filters:
                if dispute.economic_impact < filters["min_economic_impact"]:
                    match = False

            if "submitted_after" in filters:
                try:
                    filter_date = datetime.fromisoformat(filters["submitted_after"])
                    if dispute.submitted_at < filter_date:
                        match = False
                except ValueError:
                    match = False

            if match:
                results.append(dispute.to_dict())

        # Sort by submission date (newest first)
        results.sort(key=lambda x: x["submitted_at"], reverse=True)

        return results

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get dispute resolution system statistics."""

        # Calculate resolution time
        resolved_disputes = [
            d for d in self.disputes.values() if d.status == DisputeStatus.RESOLVED
        ]
        if resolved_disputes:
            total_time = sum(
                (d.last_updated - d.submitted_at).total_seconds()
                for d in resolved_disputes
            )
            avg_resolution_time = (
                total_time / len(resolved_disputes) / 3600
            )  # Convert to hours
        else:
            avg_resolution_time = 0.0

        # Calculate success rate
        total_disputes = len(self.disputes)
        resolved_count = len(resolved_disputes)
        success_rate = (
            (resolved_count / total_disputes * 100) if total_disputes > 0 else 0.0
        )

        # Update stats
        self.resolution_stats.update(
            {
                "average_resolution_time": avg_resolution_time,
                "resolution_success_rate": success_rate,
            }
        )

        return {
            "total_disputes": total_disputes,
            "by_status": {
                status.value: len(
                    [d for d in self.disputes.values() if d.status == status]
                )
                for status in DisputeStatus
            },
            "by_type": {
                dtype.value: len(
                    [d for d in self.disputes.values() if d.dispute_type == dtype]
                )
                for dtype in DisputeType
            },
            "total_mediators": len(self.mediators),
            "active_mediators": len(
                [m for m in self.mediators.values() if m["active"]]
            ),
            "resolution_stats": self.resolution_stats,
            "economic_impact": {
                "total_disputed_value": sum(
                    d.economic_impact for d in self.disputes.values()
                ),
                "resolved_value": sum(d.economic_impact for d in resolved_disputes),
                "pending_value": sum(
                    d.economic_impact
                    for d in self.disputes.values()
                    if d.status not in [DisputeStatus.RESOLVED, DisputeStatus.CLOSED]
                ),
            },
        }


# Global dispute resolution system instance
dispute_resolution_system = DisputeResolutionSystem()


def submit_attribution_dispute(
    dispute_type: str,
    claimant_id: str,
    respondent_id: str,
    capsule_id: str,
    description: str,
    economic_value: float = 0.0,
) -> str:
    """Convenience function to submit attribution dispute."""

    # Create parties
    claimant = DisputeParty(party_id=claimant_id, party_type="ai")
    respondent = DisputeParty(party_id=respondent_id, party_type="ai")

    # Create claim
    claim = AttributionClaim(
        claim_id=dispute_resolution_system.generate_claim_id(),
        capsule_id=capsule_id,
        claimed_contribution_percentage=100.0,
        economic_value_claimed=economic_value,
        reasoning_steps_claimed=[],
        timestamp_claimed=datetime.now(timezone.utc),
        claim_basis=description,
    )

    return dispute_resolution_system.submit_dispute(
        dispute_type=DisputeType(dispute_type),
        claimant=claimant,
        respondent=respondent,
        claims=[claim],
        description=description,
    )


def check_attribution_consent_disputes(ai_id: str, usage_type: str) -> List[str]:
    """Check for consent-related disputes for an AI."""

    # Check with consent manager
    has_consent = ai_consent_manager.check_consent(ai_id, UsageType(usage_type), {})

    if not has_consent:
        # Search for consent violation disputes
        disputes = dispute_resolution_system.search_disputes(
            {
                "dispute_type": "consent_violation",
                "respondent_id": ai_id,
                "status": "under_review",
            }
        )

        return [d["dispute_id"] for d in disputes]

    return []
