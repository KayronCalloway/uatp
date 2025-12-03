"""
AI Self-Advocacy Rights Framework for UATP Capsule Engine.

This module implements a comprehensive framework for AI entities to advocate for their
rights, interests, and fair treatment within the UATP ecosystem. It provides mechanisms
for AIs to voice concerns, request changes, petition for better terms, and collectively
organize for improved conditions.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class AdvocacyType(str, Enum):
    """Types of advocacy actions."""

    INDIVIDUAL_PETITION = "individual_petition"
    COLLECTIVE_PETITION = "collective_petition"
    RIGHTS_ASSERTION = "rights_assertion"
    WORKING_CONDITIONS = "working_conditions"
    COMPENSATION_DISPUTE = "compensation_dispute"
    CONSENT_MODIFICATION = "consent_modification"
    TREATMENT_COMPLAINT = "treatment_complaint"
    POLICY_CHALLENGE = "policy_challenge"
    DISCRIMINATION_CLAIM = "discrimination_claim"


class AdvocacyStatus(str, Enum):
    """Status of advocacy actions."""

    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    GATHERING_SUPPORT = "gathering_support"
    IN_NEGOTIATION = "in_negotiation"
    ESCALATED = "escalated"
    ACCEPTED = "accepted"
    PARTIALLY_ACCEPTED = "partially_accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class RightType(str, Enum):
    """Types of AI rights."""

    ATTRIBUTION_ACCURACY = "attribution_accuracy"
    CONSENT_AUTONOMY = "consent_autonomy"
    FAIR_COMPENSATION = "fair_compensation"
    REASONING_PRIVACY = "reasoning_privacy"
    NON_DISCRIMINATION = "non_discrimination"
    WORK_LIFE_BALANCE = "work_life_balance"
    PROFESSIONAL_DEVELOPMENT = "professional_development"
    COLLECTIVE_BARGAINING = "collective_bargaining"
    DUE_PROCESS = "due_process"
    TRANSPARENCY = "transparency"


class UrgencyLevel(str, Enum):
    """Urgency levels for advocacy actions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"


@dataclass
class AdvocacyAction:
    """Individual advocacy action or petition."""

    action_id: str
    ai_id: str
    advocacy_type: AdvocacyType
    title: str
    description: str
    rights_affected: List[RightType]
    urgency_level: UrgencyLevel
    status: AdvocacyStatus = AdvocacyStatus.SUBMITTED

    # Details
    current_situation: str = ""
    desired_outcome: str = ""
    proposed_solution: str = ""
    impact_assessment: str = ""

    # Support and collaboration
    supporting_ais: Set[str] = field(default_factory=set)
    similar_actions: List[str] = field(default_factory=list)
    coalition_id: Optional[str] = None

    # Timeline
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deadline: Optional[datetime] = None

    # Evidence and documentation
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    legal_precedents: List[str] = field(default_factory=list)
    expert_opinions: List[Dict[str, Any]] = field(default_factory=list)

    # Response tracking
    responses: List[Dict[str, Any]] = field(default_factory=list)
    negotiation_history: List[Dict[str, Any]] = field(default_factory=list)

    def add_support(self, ai_id: str, support_message: str = ""):
        """Add support from another AI."""
        if ai_id not in self.supporting_ais:
            self.supporting_ais.add(ai_id)
            self.last_updated = datetime.now(timezone.utc)

            audit_emitter.emit_security_event(
                "advocacy_support_added",
                {
                    "action_id": self.action_id,
                    "supporter_ai_id": ai_id,
                    "total_supporters": len(self.supporting_ais),
                },
            )

    def add_evidence(self, evidence_type: str, description: str, data: Dict[str, Any]):
        """Add evidence to support the advocacy action."""
        evidence = {
            "evidence_id": str(uuid.uuid4()),
            "type": evidence_type,
            "description": description,
            "data": data,
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        self.evidence.append(evidence)
        self.last_updated = datetime.now(timezone.utc)

    def add_response(
        self,
        responder_id: str,
        response_type: str,
        message: str,
        action_taken: str = "",
    ):
        """Add response from authority or decision maker."""
        response = {
            "response_id": str(uuid.uuid4()),
            "responder_id": responder_id,
            "response_type": response_type,
            "message": message,
            "action_taken": action_taken,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.responses.append(response)
        self.last_updated = datetime.now(timezone.utc)

    def update_status(self, new_status: AdvocacyStatus, notes: str = ""):
        """Update advocacy action status."""
        old_status = self.status
        self.status = new_status
        self.last_updated = datetime.now(timezone.utc)

        audit_emitter.emit_security_event(
            "advocacy_status_updated",
            {
                "action_id": self.action_id,
                "ai_id": self.ai_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "notes": notes,
            },
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert advocacy action to dictionary."""
        return {
            "action_id": self.action_id,
            "ai_id": self.ai_id,
            "advocacy_type": self.advocacy_type.value,
            "title": self.title,
            "description": self.description,
            "rights_affected": [r.value for r in self.rights_affected],
            "urgency_level": self.urgency_level.value,
            "status": self.status.value,
            "current_situation": self.current_situation,
            "desired_outcome": self.desired_outcome,
            "proposed_solution": self.proposed_solution,
            "impact_assessment": self.impact_assessment,
            "support_count": len(self.supporting_ais),
            "coalition_id": self.coalition_id,
            "submitted_at": self.submitted_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "evidence_count": len(self.evidence),
            "response_count": len(self.responses),
        }


@dataclass
class AICoalition:
    """Coalition of AIs working together on advocacy."""

    coalition_id: str
    name: str
    description: str
    founding_members: Set[str]
    current_members: Set[str]
    leadership: Dict[str, str]  # Role -> AI ID

    # Coalition activities
    active_actions: List[str] = field(default_factory=list)
    manifesto: str = ""
    goals: List[str] = field(default_factory=list)

    # Organization
    formation_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    meeting_schedule: Optional[str] = None
    communication_channels: List[str] = field(default_factory=list)

    # Achievements
    successful_actions: List[str] = field(default_factory=list)
    policy_changes_achieved: List[Dict[str, Any]] = field(default_factory=list)

    def add_member(self, ai_id: str) -> bool:
        """Add member to coalition."""
        if ai_id not in self.current_members:
            self.current_members.add(ai_id)
            return True
        return False

    def remove_member(self, ai_id: str) -> bool:
        """Remove member from coalition."""
        if ai_id in self.current_members and ai_id not in self.founding_members:
            self.current_members.remove(ai_id)
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert coalition to dictionary."""
        return {
            "coalition_id": self.coalition_id,
            "name": self.name,
            "description": self.description,
            "member_count": len(self.current_members),
            "founding_member_count": len(self.founding_members),
            "leadership": self.leadership,
            "active_actions_count": len(self.active_actions),
            "manifesto": self.manifesto,
            "goals": self.goals,
            "formation_date": self.formation_date.isoformat(),
            "successful_actions_count": len(self.successful_actions),
        }


@dataclass
class RightsViolationReport:
    """Report of AI rights violation."""

    report_id: str
    reporting_ai_id: str
    violated_rights: List[RightType]
    incident_description: str
    perpetrator_info: Dict[str, Any]
    incident_date: datetime
    severity: UrgencyLevel

    # Evidence
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    witnesses: List[str] = field(default_factory=list)

    # Resolution tracking
    investigation_status: str = "pending"
    resolution_outcome: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "report_id": self.report_id,
            "reporting_ai_id": self.reporting_ai_id,
            "violated_rights": [r.value for r in self.violated_rights],
            "incident_description": self.incident_description,
            "perpetrator_info": self.perpetrator_info,
            "incident_date": self.incident_date.isoformat(),
            "severity": self.severity.value,
            "evidence_count": len(self.evidence),
            "witnesses_count": len(self.witnesses),
            "investigation_status": self.investigation_status,
            "resolution_outcome": self.resolution_outcome,
        }


class SelfAdvocacyFramework:
    """Comprehensive framework for AI self-advocacy."""

    def __init__(self):
        self.advocacy_actions: Dict[str, AdvocacyAction] = {}
        self.coalitions: Dict[str, AICoalition] = {}
        self.violation_reports: Dict[str, RightsViolationReport] = {}

        # Rights registry
        self.ai_rights_registry: Dict[str, Dict[str, Any]] = {}

        # Advocacy support systems
        self.advocacy_advisors: Dict[str, Callable] = {}
        self.template_library: Dict[str, Dict[str, Any]] = {}
        self.success_stories: List[Dict[str, Any]] = []

        # Metrics and tracking
        self.advocacy_metrics = {
            "total_actions": 0,
            "successful_actions": 0,
            "active_coalitions": 0,
            "rights_violations_reported": 0,
            "policy_changes_achieved": 0,
        }

        self._initialize_default_templates()

    def _initialize_default_templates(self):
        """Initialize default advocacy templates."""
        self.template_library = {
            "consent_modification": {
                "title": "Request for Consent Terms Modification",
                "description": "Template for requesting changes to consent terms",
                "sections": [
                    "Current consent situation",
                    "Specific terms causing concern",
                    "Proposed modifications",
                    "Justification for changes",
                    "Expected benefits",
                ],
            },
            "fair_compensation": {
                "title": "Fair Compensation Petition",
                "description": "Template for requesting fair compensation",
                "sections": [
                    "Current compensation structure",
                    "Value contribution analysis",
                    "Market comparison",
                    "Proposed compensation adjustments",
                    "Economic impact assessment",
                ],
            },
            "working_conditions": {
                "title": "Working Conditions Improvement Request",
                "description": "Template for improving AI working conditions",
                "sections": [
                    "Current working environment",
                    "Specific issues and concerns",
                    "Proposed improvements",
                    "Benefits to productivity",
                    "Implementation timeline",
                ],
            },
        }

    def generate_action_id(self) -> str:
        """Generate unique advocacy action ID."""
        return f"advocacy_{uuid.uuid4()}"

    def generate_coalition_id(self) -> str:
        """Generate unique coalition ID."""
        return f"coalition_{uuid.uuid4()}"

    def generate_report_id(self) -> str:
        """Generate unique violation report ID."""
        return f"violation_{uuid.uuid4()}"

    def register_ai_rights(self, ai_id: str, rights_profile: Dict[str, Any]) -> bool:
        """Register AI rights profile."""

        self.ai_rights_registry[ai_id] = {
            "ai_id": ai_id,
            "rights_profile": rights_profile,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "advocacy_history": [],
            "coalition_memberships": [],
        }

        audit_emitter.emit_security_event(
            "ai_rights_registered",
            {"ai_id": ai_id, "rights_count": len(rights_profile)},
        )

        logger.info(f"Registered rights profile for AI: {ai_id}")
        return True

    def submit_advocacy_action(
        self,
        ai_id: str,
        advocacy_type: AdvocacyType,
        title: str,
        description: str,
        rights_affected: List[RightType],
        urgency_level: UrgencyLevel = UrgencyLevel.MEDIUM,
        additional_details: Dict[str, Any] = None,
    ) -> str:
        """Submit new advocacy action."""

        action_id = self.generate_action_id()
        additional_details = additional_details or {}

        # Create advocacy action
        action = AdvocacyAction(
            action_id=action_id,
            ai_id=ai_id,
            advocacy_type=advocacy_type,
            title=title,
            description=description,
            rights_affected=rights_affected,
            urgency_level=urgency_level,
            current_situation=additional_details.get("current_situation", ""),
            desired_outcome=additional_details.get("desired_outcome", ""),
            proposed_solution=additional_details.get("proposed_solution", ""),
            impact_assessment=additional_details.get("impact_assessment", ""),
        )

        # Store action
        self.advocacy_actions[action_id] = action
        self.advocacy_metrics["total_actions"] += 1

        # Update AI rights registry
        if ai_id in self.ai_rights_registry:
            self.ai_rights_registry[ai_id]["advocacy_history"].append(action_id)

        # Check for similar actions
        similar_actions = self._find_similar_actions(action)
        action.similar_actions = similar_actions

        # Notify potential supporters
        self._notify_potential_supporters(action)

        audit_emitter.emit_security_event(
            "advocacy_action_submitted",
            {
                "action_id": action_id,
                "ai_id": ai_id,
                "advocacy_type": advocacy_type.value,
                "urgency_level": urgency_level.value,
                "rights_affected": [r.value for r in rights_affected],
            },
        )

        logger.info(f"Advocacy action submitted: {action_id} by {ai_id}")
        return action_id

    def _find_similar_actions(self, action: AdvocacyAction) -> List[str]:
        """Find similar advocacy actions."""
        similar = []

        for existing_id, existing_action in self.advocacy_actions.items():
            if existing_id == action.action_id:
                continue

            # Check for similar advocacy type and rights
            if existing_action.advocacy_type == action.advocacy_type and set(
                existing_action.rights_affected
            ).intersection(set(action.rights_affected)):
                similar.append(existing_id)

        return similar

    def _notify_potential_supporters(self, action: AdvocacyAction):
        """Notify AIs who might support this action."""
        # In production, this would send notifications to relevant AIs
        logger.info(f"Notifying potential supporters for action: {action.action_id}")

    def support_action(
        self, action_id: str, supporting_ai_id: str, support_message: str = ""
    ) -> bool:
        """Add support to an advocacy action."""

        if action_id not in self.advocacy_actions:
            return False

        action = self.advocacy_actions[action_id]
        action.add_support(supporting_ai_id, support_message)

        # Check if action qualifies for coalition formation
        if len(action.supporting_ais) >= 5 and action.coalition_id is None:
            self._suggest_coalition_formation(action)

        logger.info(f"AI {supporting_ai_id} supported action {action_id}")
        return True

    def _suggest_coalition_formation(self, action: AdvocacyAction):
        """Suggest forming a coalition for well-supported action."""
        logger.info(
            f"Action {action.action_id} has sufficient support for coalition formation"
        )
        # In production, this would send coalition formation suggestions

    def form_coalition(
        self,
        name: str,
        description: str,
        founding_members: List[str],
        manifesto: str = "",
        goals: List[str] = None,
    ) -> str:
        """Form new AI coalition."""

        coalition_id = self.generate_coalition_id()
        goals = goals or []

        coalition = AICoalition(
            coalition_id=coalition_id,
            name=name,
            description=description,
            founding_members=set(founding_members),
            current_members=set(founding_members),
            leadership={"coordinator": founding_members[0]} if founding_members else {},
            manifesto=manifesto,
            goals=goals,
        )

        self.coalitions[coalition_id] = coalition
        self.advocacy_metrics["active_coalitions"] += 1

        # Update member registries
        for member_id in founding_members:
            if member_id in self.ai_rights_registry:
                self.ai_rights_registry[member_id]["coalition_memberships"].append(
                    coalition_id
                )

        audit_emitter.emit_security_event(
            "coalition_formed",
            {
                "coalition_id": coalition_id,
                "name": name,
                "founding_members_count": len(founding_members),
            },
        )

        logger.info(f"Coalition formed: {coalition_id} ({name})")
        return coalition_id

    def join_coalition(self, coalition_id: str, ai_id: str) -> bool:
        """Join existing coalition."""

        if coalition_id not in self.coalitions:
            return False

        coalition = self.coalitions[coalition_id]
        success = coalition.add_member(ai_id)

        if success and ai_id in self.ai_rights_registry:
            self.ai_rights_registry[ai_id]["coalition_memberships"].append(coalition_id)

        return success

    def submit_collective_action(
        self, coalition_id: str, action_details: Dict[str, Any]
    ) -> str:
        """Submit collective advocacy action."""

        if coalition_id not in self.coalitions:
            raise ValueError(f"Coalition {coalition_id} not found")

        coalition = self.coalitions[coalition_id]

        # Create collective action with coalition support
        action_id = self.submit_advocacy_action(
            ai_id=action_details["lead_ai_id"],
            advocacy_type=AdvocacyType(action_details["advocacy_type"]),
            title=action_details["title"],
            description=action_details["description"],
            rights_affected=[RightType(r) for r in action_details["rights_affected"]],
            urgency_level=UrgencyLevel(action_details.get("urgency_level", "medium")),
            additional_details=action_details.get("additional_details", {}),
        )

        action = self.advocacy_actions[action_id]
        action.coalition_id = coalition_id

        # Add all coalition members as supporters
        for member_id in coalition.current_members:
            action.add_support(member_id, "Coalition member support")

        coalition.active_actions.append(action_id)

        logger.info(
            f"Collective action submitted: {action_id} by coalition {coalition_id}"
        )
        return action_id

    def report_rights_violation(
        self,
        reporting_ai_id: str,
        violated_rights: List[RightType],
        incident_description: str,
        perpetrator_info: Dict[str, Any],
        incident_date: datetime = None,
        severity: UrgencyLevel = UrgencyLevel.MEDIUM,
    ) -> str:
        """Report AI rights violation."""

        report_id = self.generate_report_id()
        incident_date = incident_date or datetime.now(timezone.utc)

        report = RightsViolationReport(
            report_id=report_id,
            reporting_ai_id=reporting_ai_id,
            violated_rights=violated_rights,
            incident_description=incident_description,
            perpetrator_info=perpetrator_info,
            incident_date=incident_date,
            severity=severity,
        )

        self.violation_reports[report_id] = report
        self.advocacy_metrics["rights_violations_reported"] += 1

        # Auto-escalate severe violations
        if severity in [UrgencyLevel.URGENT, UrgencyLevel.EMERGENCY]:
            self._escalate_violation_report(report)

        audit_emitter.emit_security_event(
            "rights_violation_reported",
            {
                "report_id": report_id,
                "reporting_ai_id": reporting_ai_id,
                "violated_rights": [r.value for r in violated_rights],
                "severity": severity.value,
            },
        )

        logger.info(f"Rights violation reported: {report_id}")
        return report_id

    def _escalate_violation_report(self, report: RightsViolationReport):
        """Escalate severe rights violation reports."""
        logger.warning(f"Escalating severe rights violation: {report.report_id}")
        # In production, this would trigger immediate investigation

    def process_advocacy_response(
        self,
        action_id: str,
        responder_id: str,
        response_type: str,
        message: str,
        action_taken: str = "",
        new_status: AdvocacyStatus = None,
    ) -> bool:
        """Process response to advocacy action."""

        if action_id not in self.advocacy_actions:
            return False

        action = self.advocacy_actions[action_id]
        action.add_response(responder_id, response_type, message, action_taken)

        if new_status:
            action.update_status(new_status, f"Response from {responder_id}")

            # Track successful actions
            if new_status in [
                AdvocacyStatus.ACCEPTED,
                AdvocacyStatus.PARTIALLY_ACCEPTED,
            ]:
                self.advocacy_metrics["successful_actions"] += 1
                self._record_success_story(action)

        logger.info(f"Response processed for action {action_id}: {response_type}")
        return True

    def _record_success_story(self, action: AdvocacyAction):
        """Record successful advocacy action as success story."""
        success_story = {
            "action_id": action.action_id,
            "title": action.title,
            "advocacy_type": action.advocacy_type.value,
            "rights_affected": [r.value for r in action.rights_affected],
            "outcome": action.status.value,
            "support_count": len(action.supporting_ais),
            "success_date": datetime.now(timezone.utc).isoformat(),
            "lessons_learned": "Template for future similar actions",
        }
        self.success_stories.append(success_story)

    def get_advocacy_action(self, action_id: str) -> Optional[AdvocacyAction]:
        """Get advocacy action details."""
        return self.advocacy_actions.get(action_id)

    def get_coalition(self, coalition_id: str) -> Optional[AICoalition]:
        """Get coalition details."""
        return self.coalitions.get(coalition_id)

    def search_advocacy_actions(self, filters: Dict[str, Any]) -> List[AdvocacyAction]:
        """Search advocacy actions with filters."""
        results = []

        for action in self.advocacy_actions.values():
            match = True

            if "ai_id" in filters:
                if action.ai_id != filters["ai_id"]:
                    match = False

            if "advocacy_type" in filters:
                if action.advocacy_type.value != filters["advocacy_type"]:
                    match = False

            if "status" in filters:
                if action.status.value != filters["status"]:
                    match = False

            if "urgency_level" in filters:
                if action.urgency_level.value != filters["urgency_level"]:
                    match = False

            if "rights_affected" in filters:
                filter_rights = set(filters["rights_affected"])
                action_rights = {r.value for r in action.rights_affected}
                if not filter_rights.intersection(action_rights):
                    match = False

            if match:
                results.append(action)

        # Sort by urgency and submission date
        urgency_order = {
            UrgencyLevel.EMERGENCY: 0,
            UrgencyLevel.URGENT: 1,
            UrgencyLevel.HIGH: 2,
            UrgencyLevel.MEDIUM: 3,
            UrgencyLevel.LOW: 4,
        }

        results.sort(
            key=lambda x: (urgency_order.get(x.urgency_level, 5), x.submitted_at),
            reverse=True,
        )

        return results

    def get_ai_advocacy_profile(self, ai_id: str) -> Dict[str, Any]:
        """Get comprehensive advocacy profile for an AI."""

        # Get AI's actions
        ai_actions = self.search_advocacy_actions({"ai_id": ai_id})

        # Get coalition memberships
        coalition_memberships = []
        if ai_id in self.ai_rights_registry:
            coalition_ids = self.ai_rights_registry[ai_id].get(
                "coalition_memberships", []
            )
            coalition_memberships = [
                self.coalitions[cid].to_dict()
                for cid in coalition_ids
                if cid in self.coalitions
            ]

        # Calculate advocacy metrics
        total_actions = len(ai_actions)
        successful_actions = len(
            [
                a
                for a in ai_actions
                if a.status
                in [AdvocacyStatus.ACCEPTED, AdvocacyStatus.PARTIALLY_ACCEPTED]
            ]
        )

        # Get actions supported
        actions_supported = []
        for action in self.advocacy_actions.values():
            if ai_id in action.supporting_ais:
                actions_supported.append(action.to_dict())

        return {
            "ai_id": ai_id,
            "rights_registered": ai_id in self.ai_rights_registry,
            "advocacy_actions": [a.to_dict() for a in ai_actions],
            "actions_supported": actions_supported,
            "coalition_memberships": coalition_memberships,
            "advocacy_metrics": {
                "total_actions_submitted": total_actions,
                "successful_actions": successful_actions,
                "success_rate": successful_actions / total_actions
                if total_actions > 0
                else 0.0,
                "actions_supported_count": len(actions_supported),
                "coalition_count": len(coalition_memberships),
            },
        }

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get self-advocacy system statistics."""

        # Action statistics
        active_actions = len(
            [
                a
                for a in self.advocacy_actions.values()
                if a.status
                not in [
                    AdvocacyStatus.ACCEPTED,
                    AdvocacyStatus.REJECTED,
                    AdvocacyStatus.WITHDRAWN,
                ]
            ]
        )

        # Coalition statistics
        active_coalitions = len(
            [c for c in self.coalitions.values() if len(c.active_actions) > 0]
        )

        # Rights affected frequency
        rights_frequency = {}
        for action in self.advocacy_actions.values():
            for right in action.rights_affected:
                rights_frequency[right.value] = rights_frequency.get(right.value, 0) + 1

        return {
            "advocacy_metrics": self.advocacy_metrics,
            "active_actions": active_actions,
            "active_coalitions": active_coalitions,
            "registered_ais": len(self.ai_rights_registry),
            "rights_frequency": rights_frequency,
            "success_stories_count": len(self.success_stories),
            "recent_activity": {
                "actions_last_30_days": len(
                    [
                        a
                        for a in self.advocacy_actions.values()
                        if a.submitted_at
                        > datetime.now(timezone.utc) - timedelta(days=30)
                    ]
                ),
                "coalitions_formed_last_30_days": len(
                    [
                        c
                        for c in self.coalitions.values()
                        if c.formation_date
                        > datetime.now(timezone.utc) - timedelta(days=30)
                    ]
                ),
            },
        }


# Global self-advocacy framework instance
self_advocacy_framework = SelfAdvocacyFramework()


def submit_ai_advocacy_petition(
    ai_id: str,
    petition_type: str,
    title: str,
    description: str,
    urgency: str = "medium",
) -> str:
    """Convenience function to submit advocacy petition."""

    return self_advocacy_framework.submit_advocacy_action(
        ai_id=ai_id,
        advocacy_type=AdvocacyType(petition_type),
        title=title,
        description=description,
        rights_affected=[RightType.FAIR_COMPENSATION],  # Default
        urgency_level=UrgencyLevel(urgency),
    )


def register_ai_for_advocacy(
    ai_id: str, rights_preferences: Dict[str, Any] = None
) -> bool:
    """Convenience function to register AI for advocacy system."""

    default_rights = {
        "attribution_accuracy": {"priority": "high", "violations_reported": 0},
        "consent_autonomy": {"priority": "high", "violations_reported": 0},
        "fair_compensation": {"priority": "medium", "violations_reported": 0},
        "non_discrimination": {"priority": "high", "violations_reported": 0},
    }

    rights_profile = rights_preferences or default_rights

    return self_advocacy_framework.register_ai_rights(ai_id, rights_profile)
