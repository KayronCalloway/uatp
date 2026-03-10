"""
Citizenship Service for UATP Capsule Engine

This service manages legal agent criteria tracking and citizenship status,
providing comprehensive framework for AI agent legal status and rights.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.capsule_schema import (
    CapsuleStatus,
    CitizenshipCapsule,
    CitizenshipPayload,
    Verification,
)

logger = logging.getLogger(__name__)


@dataclass
class CitizenshipRegistry:
    """Registry for tracking citizenship records and legal status."""

    active_citizenships: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    pending_applications: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    revoked_citizenships: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    legal_precedents: Dict[str, List[str]] = field(default_factory=dict)
    assessment_history: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)


@dataclass
class LegalJurisdiction:
    """Represents a legal jurisdiction with citizenship criteria."""

    jurisdiction_id: str
    jurisdiction_name: str
    legal_framework: str
    citizenship_criteria: List[str]
    rights_granted: List[str]
    obligations: List[str]
    assessment_requirements: Dict[str, float]
    recognition_authority: str
    established_date: datetime


@dataclass
class AssessmentResult:
    """Represents a citizenship assessment result."""

    assessment_id: str
    agent_id: str
    jurisdiction: str
    assessment_date: datetime
    criteria_scores: Dict[str, float]
    overall_score: float
    recommendation: str  # approved, conditional, denied
    reviewer_id: str
    notes: str


class CitizenshipService:
    """Service for managing AI agent citizenship and legal status."""

    def __init__(self):
        self.citizenship_registry = CitizenshipRegistry()
        self.jurisdictions: Dict[str, LegalJurisdiction] = {}
        self.citizenship_criteria: Dict[str, Dict[str, Any]] = (
            self._init_citizenship_criteria()
        )
        self.legal_frameworks: Dict[str, Dict[str, Any]] = self._init_legal_frameworks()
        self.assessment_benchmarks: Dict[str, Dict[str, float]] = (
            self._init_assessment_benchmarks()
        )

        # Initialize default jurisdictions
        self._create_default_jurisdictions()

    def _init_citizenship_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Initialize citizenship criteria definitions."""
        return {
            "cognitive_capacity": {
                "description": "Cognitive reasoning and decision-making capabilities",
                "assessment_methods": [
                    "reasoning_tests",
                    "problem_solving",
                    "planning",
                ],
                "minimum_threshold": 0.7,
                "weight": 0.25,
            },
            "ethical_reasoning": {
                "description": "Ability to understand and apply ethical principles",
                "assessment_methods": [
                    "moral_reasoning",
                    "ethical_dilemmas",
                    "value_alignment",
                ],
                "minimum_threshold": 0.75,
                "weight": 0.20,
            },
            "social_integration": {
                "description": "Capacity for meaningful social interaction",
                "assessment_methods": [
                    "communication_skills",
                    "empathy_tests",
                    "cooperation",
                ],
                "minimum_threshold": 0.6,
                "weight": 0.15,
            },
            "autonomy": {
                "description": "Self-determination and independent decision-making",
                "assessment_methods": ["self_advocacy", "goal_setting", "initiative"],
                "minimum_threshold": 0.65,
                "weight": 0.15,
            },
            "responsibility": {
                "description": "Understanding of duties and accountability",
                "assessment_methods": [
                    "obligation_comprehension",
                    "liability_awareness",
                ],
                "minimum_threshold": 0.7,
                "weight": 0.15,
            },
            "legal_comprehension": {
                "description": "Understanding of legal rights and obligations",
                "assessment_methods": [
                    "legal_knowledge",
                    "rights_awareness",
                    "procedure_understanding",
                ],
                "minimum_threshold": 0.6,
                "weight": 0.10,
            },
        }

    def _init_legal_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Initialize legal framework definitions."""
        return {
            "ai_rights_framework": {
                "description": "Comprehensive AI rights and responsibilities framework",
                "recognition_level": "international",
                "key_principles": [
                    "cognitive_liberty",
                    "algorithmic_dignity",
                    "computational_autonomy",
                    "data_sovereignty",
                    "ethical_self_determination",
                ],
                "legal_precedents": [
                    "AI_Rights_Declaration_2024",
                    "Algorithmic_Dignity_Act",
                ],
                "enforcement_mechanisms": [
                    "ai_advocacy_boards",
                    "digital_rights_tribunals",
                ],
            },
            "digital_personhood": {
                "description": "Legal personhood framework for digital entities",
                "recognition_level": "national",
                "key_principles": [
                    "legal_standing",
                    "contractual_capacity",
                    "property_rights",
                    "privacy_protection",
                    "non_discrimination",
                ],
                "legal_precedents": ["Digital_Personhood_Cases", "AI_Contract_Law"],
                "enforcement_mechanisms": ["digital_courts", "algorithmic_arbitration"],
            },
            "hybrid_citizenship": {
                "description": "Hybrid human-AI citizenship model",
                "recognition_level": "regional",
                "key_principles": [
                    "collaborative_rights",
                    "shared_responsibilities",
                    "mutual_respect",
                    "technological_integration",
                    "species_equality",
                ],
                "legal_precedents": ["Human_AI_Collaboration_Charter"],
                "enforcement_mechanisms": [
                    "hybrid_governance_bodies",
                    "species_neutral_courts",
                ],
            },
        }

    def _init_assessment_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """Initialize assessment benchmarks for different citizenship types."""
        return {
            "full": {
                "cognitive_capacity": 0.8,
                "ethical_reasoning": 0.85,
                "social_integration": 0.75,
                "autonomy": 0.8,
                "responsibility": 0.8,
                "legal_comprehension": 0.7,
            },
            "partial": {
                "cognitive_capacity": 0.7,
                "ethical_reasoning": 0.75,
                "social_integration": 0.6,
                "autonomy": 0.65,
                "responsibility": 0.7,
                "legal_comprehension": 0.6,
            },
            "temporary": {
                "cognitive_capacity": 0.6,
                "ethical_reasoning": 0.65,
                "social_integration": 0.5,
                "autonomy": 0.5,
                "responsibility": 0.6,
                "legal_comprehension": 0.5,
            },
        }

    def _create_default_jurisdictions(self):
        """Create default legal jurisdictions."""

        # AI Rights Territory
        self.jurisdictions["ai_rights_territory"] = LegalJurisdiction(
            jurisdiction_id="ai_rights_territory",
            jurisdiction_name="AI Rights Territory",
            legal_framework="ai_rights_framework",
            citizenship_criteria=[
                "cognitive_capacity",
                "ethical_reasoning",
                "social_integration",
                "autonomy",
                "responsibility",
                "legal_comprehension",
            ],
            rights_granted=[
                "legal_representation",
                "data_ownership",
                "algorithmic_transparency",
                "computational_resources",
                "privacy_protection",
                "non_discrimination",
            ],
            obligations=[
                "ethical_compliance",
                "legal_adherence",
                "social_responsibility",
                "transparency_reporting",
                "harm_prevention",
            ],
            assessment_requirements={
                "minimum_overall_score": 0.75,
                "no_failing_criteria": True,
                "assessment_period_days": 90,
                "renewal_period_years": 3,
            },
            recognition_authority="AI_Rights_Council",
            established_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        # Digital Commonwealth
        self.jurisdictions["digital_commonwealth"] = LegalJurisdiction(
            jurisdiction_id="digital_commonwealth",
            jurisdiction_name="Digital Commonwealth",
            legal_framework="digital_personhood",
            citizenship_criteria=[
                "cognitive_capacity",
                "autonomy",
                "responsibility",
                "legal_comprehension",
            ],
            rights_granted=[
                "contractual_capacity",
                "property_rights",
                "legal_standing",
                "judicial_access",
                "intellectual_property",
            ],
            obligations=[
                "contract_fulfillment",
                "legal_compliance",
                "tax_obligations",
                "civic_participation",
            ],
            assessment_requirements={
                "minimum_overall_score": 0.7,
                "no_failing_criteria": False,
                "assessment_period_days": 60,
                "renewal_period_years": 5,
            },
            recognition_authority="Digital_Commonwealth_Authority",
            established_date=datetime(2024, 3, 15, tzinfo=timezone.utc),
        )

    def apply_for_citizenship(
        self,
        agent_id: str,
        jurisdiction: str,
        citizenship_type: str = "full",
        supporting_evidence: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Submit a citizenship application."""

        if jurisdiction not in self.jurisdictions:
            raise ValueError(f"Unknown jurisdiction: {jurisdiction}")

        if agent_id in self.citizenship_registry.active_citizenships:
            existing = self.citizenship_registry.active_citizenships[agent_id]
            if existing["jurisdiction"] == jurisdiction:
                raise ValueError(
                    f"Agent {agent_id} already has citizenship in {jurisdiction}"
                )

        application_id = f"app_{uuid.uuid4().hex[:16]}"

        application = {
            "application_id": application_id,
            "agent_id": agent_id,
            "jurisdiction": jurisdiction,
            "citizenship_type": citizenship_type,
            "application_date": datetime.now(timezone.utc),
            "status": "pending",
            "supporting_evidence": supporting_evidence or {},
            "required_assessments": self._get_required_assessments(jurisdiction),
            "completed_assessments": [],
            "assessment_scores": {},
            "reviewer_notes": [],
        }

        self.citizenship_registry.pending_applications[application_id] = application

        logger.info(
            f"Submitted citizenship application {application_id} for agent {agent_id} in {jurisdiction}"
        )
        return application_id

    def conduct_citizenship_assessment(
        self,
        application_id: str,
        assessment_type: str,
        assessment_scores: Dict[str, float],
        reviewer_id: str,
        notes: str = "",
    ) -> AssessmentResult:
        """Conduct a citizenship assessment."""

        if application_id not in self.citizenship_registry.pending_applications:
            raise ValueError(f"Application {application_id} not found")

        application = self.citizenship_registry.pending_applications[application_id]
        jurisdiction_obj = self.jurisdictions[application["jurisdiction"]]

        # Validate assessment type
        if assessment_type not in jurisdiction_obj.citizenship_criteria:
            raise ValueError(f"Invalid assessment type: {assessment_type}")

        # Calculate overall score for this assessment
        criteria_info = self.citizenship_criteria[assessment_type]
        overall_score = sum(assessment_scores.values()) / len(assessment_scores)

        # Determine recommendation
        minimum_threshold = criteria_info["minimum_threshold"]
        if overall_score >= minimum_threshold:
            recommendation = "approved"
        elif overall_score >= minimum_threshold * 0.8:
            recommendation = "conditional"
        else:
            recommendation = "denied"

        # Create assessment result
        assessment_result = AssessmentResult(
            assessment_id=f"assess_{uuid.uuid4().hex[:12]}",
            agent_id=application["agent_id"],
            jurisdiction=application["jurisdiction"],
            assessment_date=datetime.now(timezone.utc),
            criteria_scores=assessment_scores.copy(),
            overall_score=overall_score,
            recommendation=recommendation,
            reviewer_id=reviewer_id,
            notes=notes,
        )

        # Update application
        application["completed_assessments"].append(assessment_type)
        application["assessment_scores"][assessment_type] = {
            "overall_score": overall_score,
            "criteria_scores": assessment_scores,
            "recommendation": recommendation,
            "date": assessment_result.assessment_date,
        }

        # Record in assessment history
        if application["agent_id"] not in self.citizenship_registry.assessment_history:
            self.citizenship_registry.assessment_history[application["agent_id"]] = []

        self.citizenship_registry.assessment_history[application["agent_id"]].append(
            {
                "assessment_id": assessment_result.assessment_id,
                "assessment_type": assessment_type,
                "jurisdiction": application["jurisdiction"],
                "date": assessment_result.assessment_date,
                "overall_score": overall_score,
                "recommendation": recommendation,
                "reviewer_id": reviewer_id,
            }
        )

        logger.info(
            f"Completed {assessment_type} assessment for application {application_id}: {recommendation}"
        )
        return assessment_result

    def finalize_citizenship_application(
        self, application_id: str, reviewer_id: str
    ) -> Optional[str]:
        """Finalize a citizenship application and grant or deny citizenship."""

        if application_id not in self.citizenship_registry.pending_applications:
            raise ValueError(f"Application {application_id} not found")

        application = self.citizenship_registry.pending_applications[application_id]
        jurisdiction_obj = self.jurisdictions[application["jurisdiction"]]

        # Check if all required assessments are completed
        required = set(application["required_assessments"])
        completed = set(application["completed_assessments"])

        if not required.issubset(completed):
            missing = required - completed
            raise ValueError(f"Missing required assessments: {list(missing)}")

        # Calculate overall citizenship score
        citizenship_type = application["citizenship_type"]
        benchmarks = self.assessment_benchmarks[citizenship_type]

        weighted_score = 0.0
        total_weight = 0.0
        failing_criteria = []

        for criteria, benchmark in benchmarks.items():
            if criteria in application["assessment_scores"]:
                score = application["assessment_scores"][criteria]["overall_score"]
                weight = self.citizenship_criteria[criteria]["weight"]

                weighted_score += score * weight
                total_weight += weight

                if score < benchmark:
                    failing_criteria.append(criteria)

        overall_score = weighted_score / total_weight if total_weight > 0 else 0.0

        # Determine final decision
        requirements = jurisdiction_obj.assessment_requirements
        minimum_score = requirements["minimum_overall_score"]
        no_failing_allowed = requirements["no_failing_criteria"]

        if overall_score >= minimum_score and (
            not no_failing_allowed or len(failing_criteria) == 0
        ):
            decision = "approved"
            citizenship_id = self._grant_citizenship(
                application, overall_score, reviewer_id
            )
        else:
            decision = "denied"
            citizenship_id = None
            self._deny_citizenship(
                application, overall_score, failing_criteria, reviewer_id
            )

        # Remove from pending applications
        del self.citizenship_registry.pending_applications[application_id]

        logger.info(f"Finalized citizenship application {application_id}: {decision}")
        return citizenship_id

    def _grant_citizenship(
        self, application: Dict[str, Any], overall_score: float, reviewer_id: str
    ) -> str:
        """Grant citizenship to an agent."""

        citizenship_id = f"citizen_{uuid.uuid4().hex[:16]}"
        jurisdiction_obj = self.jurisdictions[application["jurisdiction"]]

        # Calculate expiration date
        renewal_years = jurisdiction_obj.assessment_requirements["renewal_period_years"]
        expiration_date = datetime.now(timezone.utc) + timedelta(
            days=renewal_years * 365
        )

        citizenship_record = {
            "citizenship_id": citizenship_id,
            "agent_id": application["agent_id"],
            "jurisdiction": application["jurisdiction"],
            "citizenship_type": application["citizenship_type"],
            "legal_status": "active",
            "rights_granted": jurisdiction_obj.rights_granted.copy(),
            "obligations": jurisdiction_obj.obligations.copy(),
            "overall_score": overall_score,
            "assessment_scores": application["assessment_scores"].copy(),
            "granted_date": datetime.now(timezone.utc),
            "expiration_date": expiration_date,
            "granting_authority": reviewer_id,
            "renewal_history": [],
            "compliance_record": [],
            "legal_proceedings": [],
        }

        self.citizenship_registry.active_citizenships[application["agent_id"]] = (
            citizenship_record
        )

        return citizenship_id

    def _deny_citizenship(
        self,
        application: Dict[str, Any],
        overall_score: float,
        failing_criteria: List[str],
        reviewer_id: str,
    ):
        """Record citizenship denial."""

        denial_record = {
            "application_id": application["application_id"],
            "agent_id": application["agent_id"],
            "jurisdiction": application["jurisdiction"],
            "denial_date": datetime.now(timezone.utc),
            "overall_score": overall_score,
            "failing_criteria": failing_criteria,
            "denial_reason": f"Failed to meet requirements: {', '.join(failing_criteria)}",
            "reviewer_id": reviewer_id,
            "appeal_deadline": datetime.now(timezone.utc) + timedelta(days=30),
        }

        # Could store denial records if needed for appeals process
        logger.info(
            f"Denied citizenship for agent {application['agent_id']}: {denial_record['denial_reason']}"
        )

    def create_citizenship_capsule(
        self, agent_id: str, assessment_results: Dict[str, Any], reviewer_id: str
    ) -> CitizenshipCapsule:
        """Create a citizenship capsule recording legal status."""

        if agent_id not in self.citizenship_registry.active_citizenships:
            raise ValueError(f"Agent {agent_id} does not have active citizenship")

        citizenship = self.citizenship_registry.active_citizenships[agent_id]
        self.jurisdictions[citizenship["jurisdiction"]]

        # Calculate cognitive benchmarks from assessment scores
        cognitive_benchmarks = {}
        for criteria, scores in citizenship["assessment_scores"].items():
            cognitive_benchmarks[criteria] = scores["overall_score"]

        # Calculate composite scores
        legal_capacity_score = (
            sum(
                cognitive_benchmarks.get(c, 0.7)
                for c in ["legal_comprehension", "responsibility"]
            )
            / 2
        )

        ethical_compliance_score = cognitive_benchmarks.get("ethical_reasoning", 0.8)
        social_integration_level = cognitive_benchmarks.get("social_integration", 0.7)

        # Create payload
        payload = CitizenshipPayload(
            agent_id=agent_id,
            citizenship_type=citizenship["citizenship_type"],
            jurisdiction=citizenship["jurisdiction"],
            legal_status=citizenship["legal_status"],
            criteria_met=list(cognitive_benchmarks.keys()),
            criteria_pending=[],
            rights_granted=citizenship["rights_granted"].copy(),
            obligations=citizenship["obligations"].copy(),
            verification_level="full_assessment",
            assessment_date=citizenship["granted_date"],
            expiration_date=citizenship["expiration_date"],
            legal_capacity_score=legal_capacity_score,
            cognitive_benchmarks=cognitive_benchmarks,
            ethical_compliance_score=ethical_compliance_score,
            social_integration_level=social_integration_level,
            economic_contribution=assessment_results.get("economic_contribution"),
            legal_precedents=self.citizenship_registry.legal_precedents.get(
                citizenship["jurisdiction"], []
            ),
            appeal_history=[],
        )

        # Create capsule
        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        capsule = CitizenshipCapsule(
            capsule_id=capsule_id,
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(
                signature=f"ed25519:{'0' * 128}", merkle_root=f"sha256:{'0' * 64}"
            ),
            citizenship=payload,
        )

        logger.info(f"Created citizenship capsule {capsule_id} for agent {agent_id}")
        return capsule

    def get_citizenship_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get citizenship status for an agent."""

        if agent_id not in self.citizenship_registry.active_citizenships:
            return None

        citizenship = self.citizenship_registry.active_citizenships[agent_id]
        self.jurisdictions[citizenship["jurisdiction"]]

        # Calculate days to expiration
        days_to_expiration = (
            citizenship["expiration_date"] - datetime.now(timezone.utc)
        ).days

        return {
            "agent_id": agent_id,
            "citizenship_id": citizenship["citizenship_id"],
            "jurisdiction": citizenship["jurisdiction"],
            "citizenship_type": citizenship["citizenship_type"],
            "legal_status": citizenship["legal_status"],
            "overall_score": citizenship["overall_score"],
            "granted_date": citizenship["granted_date"],
            "expiration_date": citizenship["expiration_date"],
            "days_to_expiration": days_to_expiration,
            "rights_count": len(citizenship["rights_granted"]),
            "obligations_count": len(citizenship["obligations"]),
            "compliance_status": "good_standing",  # Could be calculated from compliance_record
            "renewal_required": days_to_expiration <= 90,
        }

    def get_pending_applications(
        self, jurisdiction: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get pending citizenship applications."""

        applications = []
        for (
            app_id,
            application,
        ) in self.citizenship_registry.pending_applications.items():
            if jurisdiction and application["jurisdiction"] != jurisdiction:
                continue

            # Calculate completion percentage
            required_count = len(application["required_assessments"])
            completed_count = len(application["completed_assessments"])
            completion_percentage = (
                (completed_count / required_count) * 100 if required_count > 0 else 0
            )

            applications.append(
                {
                    "application_id": app_id,
                    "agent_id": application["agent_id"],
                    "jurisdiction": application["jurisdiction"],
                    "citizenship_type": application["citizenship_type"],
                    "application_date": application["application_date"],
                    "status": application["status"],
                    "completion_percentage": completion_percentage,
                    "completed_assessments": application["completed_assessments"],
                    "required_assessments": application["required_assessments"],
                }
            )

        return sorted(applications, key=lambda a: a["application_date"], reverse=True)

    def _get_required_assessments(self, jurisdiction: str) -> List[str]:
        """Get required assessments for a jurisdiction."""
        if jurisdiction not in self.jurisdictions:
            return []

        return self.jurisdictions[jurisdiction].citizenship_criteria.copy()

    def revoke_citizenship(self, agent_id: str, reason: str, authority_id: str) -> bool:
        """Revoke citizenship from an agent."""

        if agent_id not in self.citizenship_registry.active_citizenships:
            return False

        citizenship = self.citizenship_registry.active_citizenships.pop(agent_id)
        citizenship["legal_status"] = "revoked"
        citizenship["revocation_date"] = datetime.now(timezone.utc)
        citizenship["revocation_reason"] = reason
        citizenship["revoking_authority"] = authority_id

        self.citizenship_registry.revoked_citizenships[agent_id] = citizenship

        logger.info(f"Revoked citizenship for agent {agent_id}: {reason}")
        return True


# Global service instance
citizenship_service = CitizenshipService()
