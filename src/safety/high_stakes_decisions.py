"""
High-Stakes Decision Safety Rails

Provides validation, human oversight, and safety mechanisms for AI decisions
in critical domains where mistakes have severe consequences.

Critical Domains:
- Medical: Diagnosis, treatment, medication
- Financial: Trading, lending, insurance claims
- Legal: Contracts, compliance, litigation
- Autonomous: Self-driving, robotics, industrial control

Key Features:
1. Risk classification (low, medium, high, critical)
2. Confidence threshold requirements
3. Human-in-the-loop approval workflows
4. Multi-agent consensus requirements
5. Explainable AI justifications
6. Emergency stop mechanisms
7. Liability tracking and audit trail

Usage:
    from src.safety.high_stakes_decisions import DecisionSafetyValidator

    validator = DecisionSafetyValidator()

    # Classify decision risk level
    risk_level = validator.classify_decision(
        domain="medical",
        decision_type="diagnosis",
        patient_severity="critical"
    )

    # Validate decision before execution
    validation = await validator.validate_decision(
        decision={
            "domain": "medical",
            "type": "prescription",
            "recommendation": "prescribe drug X",
            "confidence": 0.85
        },
        agent_id="agent_123",
        context={"patient_id": "p_456", "severity": "high"}
    )

    if validation.approved:
        # Execute decision
        result = await execute_prescription()
    else:
        # Require human approval
        await request_human_approval(validation.approval_request_id)
"""

import json
import logging
import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk levels for decisions"""

    LOW = "low"  # Routine, low impact
    MEDIUM = "medium"  # Moderate impact, reversible
    HIGH = "high"  # Significant impact, difficult to reverse
    CRITICAL = "critical"  # Life/death, irreversible, severe liability


class DecisionDomain(str, Enum):
    """High-stakes decision domains"""

    MEDICAL = "medical"
    FINANCIAL = "financial"
    LEGAL = "legal"
    AUTONOMOUS = "autonomous"
    SAFETY_CRITICAL = "safety_critical"
    GENERAL = "general"


class ApprovalStatus(str, Enum):
    """Decision approval status"""

    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING_HUMAN = "pending_human"
    PENDING_CONSENSUS = "pending_consensus"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class SafetyThresholds:
    """Safety thresholds for decision validation"""

    domain: DecisionDomain
    risk_level: RiskLevel
    min_confidence: float  # Minimum AI confidence required (0-1)
    require_human_approval: bool
    require_multi_agent_consensus: bool
    min_consensus_agents: int = 3
    require_explanation: bool = True
    max_response_time_seconds: Optional[int] = None  # Time limit for decision
    liability_limit_usd: Optional[float] = None


@dataclass
class DecisionValidation:
    """Result of decision validation"""

    validation_id: str
    approved: bool
    approval_status: ApprovalStatus
    risk_level: RiskLevel
    confidence: float
    requires_human_approval: bool
    requires_consensus: bool
    approval_request_id: Optional[str]
    reason: str
    warnings: List[str]
    timestamp: str
    metadata: Dict[str, Any]


@dataclass
class HumanApprovalRequest:
    """Request for human approval of high-stakes decision"""

    request_id: str
    decision_id: str
    agent_id: str
    domain: DecisionDomain
    risk_level: RiskLevel
    decision_summary: str
    decision_details: Dict[str, Any]
    ai_confidence: float
    ai_explanation: str
    created_at: str
    expires_at: str
    status: str  # "pending", "approved", "rejected", "expired"
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None


@dataclass
class ConsensusRequest:
    """Request for multi-agent consensus"""

    request_id: str
    decision_id: str
    primary_agent_id: str
    domain: DecisionDomain
    decision_summary: str
    decision_details: Dict[str, Any]
    required_agents: int
    agent_responses: List[Dict[str, Any]] = field(default_factory=list)
    consensus_reached: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class EmergencyStop:
    """Emergency stop trigger for dangerous decisions"""

    stop_id: str
    agent_id: str
    decision_id: str
    reason: str
    triggered_by: str  # "automatic", "human", "system"
    timestamp: str
    metadata: Dict[str, Any]


class DecisionSafetyValidator:
    """
    Validates high-stakes AI decisions with safety rails.

    This system provides:
    1. Risk classification based on domain and context
    2. Confidence threshold validation
    3. Human-in-the-loop approval workflows
    4. Multi-agent consensus requirements
    5. Explainable AI enforcement
    6. Emergency stop mechanisms
    7. Complete audit trail
    """

    # Default safety thresholds by domain and risk level
    DEFAULT_THRESHOLDS = {
        (DecisionDomain.MEDICAL, RiskLevel.LOW): SafetyThresholds(
            domain=DecisionDomain.MEDICAL,
            risk_level=RiskLevel.LOW,
            min_confidence=0.80,
            require_human_approval=False,
            require_multi_agent_consensus=False,
            require_explanation=True,
        ),
        (DecisionDomain.MEDICAL, RiskLevel.MEDIUM): SafetyThresholds(
            domain=DecisionDomain.MEDICAL,
            risk_level=RiskLevel.MEDIUM,
            min_confidence=0.90,
            require_human_approval=False,
            require_multi_agent_consensus=True,
            min_consensus_agents=2,
            require_explanation=True,
        ),
        (DecisionDomain.MEDICAL, RiskLevel.HIGH): SafetyThresholds(
            domain=DecisionDomain.MEDICAL,
            risk_level=RiskLevel.HIGH,
            min_confidence=0.95,
            require_human_approval=True,
            require_multi_agent_consensus=True,
            min_consensus_agents=3,
            require_explanation=True,
            liability_limit_usd=1_000_000.00,
        ),
        (DecisionDomain.MEDICAL, RiskLevel.CRITICAL): SafetyThresholds(
            domain=DecisionDomain.MEDICAL,
            risk_level=RiskLevel.CRITICAL,
            min_confidence=0.99,
            require_human_approval=True,
            require_multi_agent_consensus=True,
            min_consensus_agents=5,
            require_explanation=True,
            max_response_time_seconds=300,  # 5 minutes
            liability_limit_usd=10_000_000.00,
        ),
        (DecisionDomain.FINANCIAL, RiskLevel.HIGH): SafetyThresholds(
            domain=DecisionDomain.FINANCIAL,
            risk_level=RiskLevel.HIGH,
            min_confidence=0.90,
            require_human_approval=True,
            require_multi_agent_consensus=True,
            min_consensus_agents=3,
            require_explanation=True,
            liability_limit_usd=100_000.00,
        ),
        (DecisionDomain.LEGAL, RiskLevel.HIGH): SafetyThresholds(
            domain=DecisionDomain.LEGAL,
            risk_level=RiskLevel.HIGH,
            min_confidence=0.95,
            require_human_approval=True,
            require_multi_agent_consensus=True,
            min_consensus_agents=3,
            require_explanation=True,
        ),
        (DecisionDomain.AUTONOMOUS, RiskLevel.CRITICAL): SafetyThresholds(
            domain=DecisionDomain.AUTONOMOUS,
            risk_level=RiskLevel.CRITICAL,
            min_confidence=0.99,
            require_human_approval=False,  # Too fast for human in loop
            require_multi_agent_consensus=True,
            min_consensus_agents=3,
            require_explanation=True,
            max_response_time_seconds=1,  # 1 second for autonomous
            liability_limit_usd=10_000_000.00,
        ),
    }

    def __init__(self, storage_path: str = "safety/high_stakes"):
        """
        Initialize safety validator.

        Args:
            storage_path: Directory for storing safety data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory caches
        self.thresholds = dict(self.DEFAULT_THRESHOLDS)
        self.pending_approvals: Dict[str, HumanApprovalRequest] = {}
        self.pending_consensus: Dict[str, ConsensusRequest] = {}
        self.emergency_stops: Set[str] = set()  # decision_ids that are stopped

    def classify_decision(
        self, domain: str, decision_type: str, context: Optional[Dict[str, Any]] = None
    ) -> RiskLevel:
        """
        Classify risk level of a decision.

        Args:
            domain: Decision domain (medical, financial, etc.)
            decision_type: Type of decision
            context: Additional context for classification

        Returns:
            RiskLevel classification
        """
        context = context or {}
        domain_enum = DecisionDomain(domain)

        # Medical domain classification
        if domain_enum == DecisionDomain.MEDICAL:
            patient_severity = context.get("patient_severity", "").lower()
            is_invasive = context.get("is_invasive", False)
            is_irreversible = context.get("is_irreversible", False)

            if patient_severity == "critical" or is_irreversible:
                return RiskLevel.CRITICAL
            elif patient_severity == "high" or is_invasive:
                return RiskLevel.HIGH
            elif decision_type in ["prescription", "treatment_plan"]:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW

        # Financial domain classification
        elif domain_enum == DecisionDomain.FINANCIAL:
            amount = context.get("amount_usd", 0)

            if amount > 100_000:
                return RiskLevel.CRITICAL
            elif amount > 10_000:
                return RiskLevel.HIGH
            elif amount > 1_000:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW

        # Legal domain classification
        elif domain_enum == DecisionDomain.LEGAL:
            potential_liability = context.get("potential_liability_usd", 0)
            is_precedent_setting = context.get("is_precedent_setting", False)

            if potential_liability > 1_000_000 or is_precedent_setting:
                return RiskLevel.CRITICAL
            elif potential_liability > 100_000:
                return RiskLevel.HIGH
            elif decision_type in ["contract_signing", "compliance_determination"]:
                return RiskLevel.MEDIUM
            else:
                return RiskLevel.LOW

        # Autonomous systems classification
        elif domain_enum == DecisionDomain.AUTONOMOUS:
            involves_human_safety = context.get("involves_human_safety", False)
            speed_mph = context.get("speed_mph", 0)

            if involves_human_safety and speed_mph > 30:
                return RiskLevel.CRITICAL
            elif involves_human_safety:
                return RiskLevel.HIGH
            else:
                return RiskLevel.MEDIUM

        # Default
        return RiskLevel.LOW

    def get_safety_thresholds(
        self, domain: DecisionDomain, risk_level: RiskLevel
    ) -> SafetyThresholds:
        """Get safety thresholds for domain and risk level"""
        key = (domain, risk_level)

        if key in self.thresholds:
            return self.thresholds[key]

        # Default conservative thresholds
        return SafetyThresholds(
            domain=domain,
            risk_level=risk_level,
            min_confidence=0.90,
            require_human_approval=risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            require_multi_agent_consensus=risk_level
            in [RiskLevel.HIGH, RiskLevel.CRITICAL],
            min_consensus_agents=3,
            require_explanation=True,
        )

    async def validate_decision(
        self,
        decision: Dict[str, Any],
        agent_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> DecisionValidation:
        """
        Validate a high-stakes decision before execution.

        Args:
            decision: Decision details including domain, type, confidence
            agent_id: ID of agent making decision
            context: Additional context

        Returns:
            DecisionValidation result
        """
        validation_id = f"val_{secrets.token_hex(16)}"
        context = context or {}

        # Extract decision details
        domain = DecisionDomain(decision.get("domain", "general"))
        decision_type = decision.get("type", "unknown")
        confidence = float(decision.get("confidence", 0.0))
        explanation = decision.get("explanation", "")

        # Classify risk level
        risk_level = self.classify_decision(
            domain=domain.value, decision_type=decision_type, context=context
        )

        # Get safety thresholds
        thresholds = self.get_safety_thresholds(domain, risk_level)

        # Validation checks
        warnings = []
        approved = True
        approval_status = ApprovalStatus.APPROVED
        approval_request_id = None
        reason = "Decision meets all safety requirements"

        # Check 1: Emergency stop
        decision_id = decision.get("decision_id")
        if decision_id and decision_id in self.emergency_stops:
            approved = False
            approval_status = ApprovalStatus.EMERGENCY_STOP
            reason = "Emergency stop active for this decision"

            logger.critical(f" EMERGENCY STOP: Decision {decision_id} blocked")

            return DecisionValidation(
                validation_id=validation_id,
                approved=False,
                approval_status=approval_status,
                risk_level=risk_level,
                confidence=confidence,
                requires_human_approval=True,
                requires_consensus=True,
                approval_request_id=None,
                reason=reason,
                warnings=warnings,
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={"emergency_stop": True},
            )

        # Check 2: Confidence threshold
        if confidence < thresholds.min_confidence:
            approved = False
            warnings.append(
                f"Confidence {confidence:.2f} below threshold {thresholds.min_confidence:.2f}"
            )
            reason = f"Insufficient AI confidence for {risk_level.value} risk decision"

        # Check 3: Explanation required
        if thresholds.require_explanation and not explanation:
            approved = False
            warnings.append("Explanation required but not provided")
            reason = "Decision lacks required explanation"

        # Check 4: Human approval required
        if thresholds.require_human_approval:
            if not approved:
                # Already failed other checks, need human approval
                approval_request_id = await self._create_human_approval_request(
                    decision=decision,
                    agent_id=agent_id,
                    domain=domain,
                    risk_level=risk_level,
                    confidence=confidence,
                    explanation=explanation,
                    context=context,
                )
                approval_status = ApprovalStatus.PENDING_HUMAN
                reason = "Requires human approval due to failed checks"
            else:
                # Meets criteria but still needs human approval for this risk level
                approval_request_id = await self._create_human_approval_request(
                    decision=decision,
                    agent_id=agent_id,
                    domain=domain,
                    risk_level=risk_level,
                    confidence=confidence,
                    explanation=explanation,
                    context=context,
                )
                approved = False
                approval_status = ApprovalStatus.PENDING_HUMAN
                reason = (
                    f"{risk_level.value.upper()} risk decision requires human approval"
                )

        # Check 5: Multi-agent consensus required
        if thresholds.require_multi_agent_consensus and approved:
            # Create consensus request
            consensus_id = await self._create_consensus_request(
                decision=decision,
                agent_id=agent_id,
                domain=domain,
                required_agents=thresholds.min_consensus_agents,
                context=context,
            )

            approved = False
            approval_status = ApprovalStatus.PENDING_CONSENSUS
            approval_request_id = consensus_id
            reason = f"Requires consensus from {thresholds.min_consensus_agents} agents"

        validation = DecisionValidation(
            validation_id=validation_id,
            approved=approved,
            approval_status=approval_status,
            risk_level=risk_level,
            confidence=confidence,
            requires_human_approval=thresholds.require_human_approval,
            requires_consensus=thresholds.require_multi_agent_consensus,
            approval_request_id=approval_request_id,
            reason=reason,
            warnings=warnings,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                "domain": domain.value,
                "decision_type": decision_type,
                "agent_id": agent_id,
                "thresholds": asdict(thresholds),
            },
        )

        # Save validation
        self._save_validation(validation)

        # Log based on approval status
        if approved:
            logger.info(
                f"[OK] Decision validated: {validation_id} (risk: {risk_level.value})"
            )
        elif approval_status == ApprovalStatus.PENDING_HUMAN:
            logger.warning(
                f"⏳ Decision pending human approval: {validation_id} "
                f"(risk: {risk_level.value}, confidence: {confidence:.2f})"
            )
        elif approval_status == ApprovalStatus.PENDING_CONSENSUS:
            logger.warning(
                f"⏳ Decision pending consensus: {validation_id} "
                f"(risk: {risk_level.value}, requires {thresholds.min_consensus_agents} agents)"
            )

        # Emit audit event
        try:
            from src.audit.events import audit_emitter

            audit_emitter.emit_security_event(
                event_name="high_stakes_decision_validated",
                metadata={
                    "validation_id": validation_id,
                    "approved": approved,
                    "risk_level": risk_level.value,
                    "domain": domain.value,
                    "confidence": confidence,
                    "agent_id": agent_id,
                    "requires_human_approval": thresholds.require_human_approval,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event: {e}")

        return validation

    async def _create_human_approval_request(
        self,
        decision: Dict[str, Any],
        agent_id: str,
        domain: DecisionDomain,
        risk_level: RiskLevel,
        confidence: float,
        explanation: str,
        context: Dict[str, Any],
    ) -> str:
        """Create human approval request"""
        from datetime import timedelta

        request_id = f"approval_{secrets.token_hex(16)}"
        decision_id = decision.get("decision_id", f"dec_{secrets.token_hex(8)}")

        # Expiration based on risk level
        expires_in_hours = 24 if risk_level != RiskLevel.CRITICAL else 1

        request = HumanApprovalRequest(
            request_id=request_id,
            decision_id=decision_id,
            agent_id=agent_id,
            domain=domain,
            risk_level=risk_level,
            decision_summary=decision.get("summary", "No summary provided"),
            decision_details=decision,
            ai_confidence=confidence,
            ai_explanation=explanation,
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=(
                datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
            ).isoformat(),
            status="pending",
        )

        self.pending_approvals[request_id] = request
        self._save_approval_request(request)

        logger.info(
            f" Human approval request created: {request_id} "
            f"(decision: {decision_id}, risk: {risk_level.value})"
        )

        return request_id

    async def _create_consensus_request(
        self,
        decision: Dict[str, Any],
        agent_id: str,
        domain: DecisionDomain,
        required_agents: int,
        context: Dict[str, Any],
    ) -> str:
        """Create multi-agent consensus request"""
        request_id = f"consensus_{secrets.token_hex(16)}"
        decision_id = decision.get("decision_id", f"dec_{secrets.token_hex(8)}")

        request = ConsensusRequest(
            request_id=request_id,
            decision_id=decision_id,
            primary_agent_id=agent_id,
            domain=domain,
            decision_summary=decision.get("summary", "No summary provided"),
            decision_details=decision,
            required_agents=required_agents,
        )

        self.pending_consensus[request_id] = request
        self._save_consensus_request(request)

        logger.info(
            f" Consensus request created: {request_id} "
            f"(requires {required_agents} agents)"
        )

        return request_id

    async def trigger_emergency_stop(
        self, decision_id: str, agent_id: str, reason: str, triggered_by: str = "human"
    ) -> EmergencyStop:
        """
        Trigger emergency stop for a decision.

        This immediately blocks the decision from being executed.
        """
        stop_id = f"stop_{secrets.token_hex(16)}"

        stop = EmergencyStop(
            stop_id=stop_id,
            agent_id=agent_id,
            decision_id=decision_id,
            reason=reason,
            triggered_by=triggered_by,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={},
        )

        self.emergency_stops.add(decision_id)
        self._save_emergency_stop(stop)

        logger.critical(
            f" EMERGENCY STOP TRIGGERED: {stop_id} "
            f"Decision {decision_id} stopped by {triggered_by}. Reason: {reason}"
        )

        # Emit critical audit event
        try:
            from src.audit.events import audit_emitter

            audit_emitter.emit_security_event(
                event_name="emergency_stop_triggered",
                metadata={
                    "stop_id": stop_id,
                    "decision_id": decision_id,
                    "agent_id": agent_id,
                    "reason": reason,
                    "triggered_by": triggered_by,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit audit event: {e}")

        return stop

    def _save_validation(self, validation: DecisionValidation):
        """Save validation to storage"""
        file_path = self.storage_path / "validations.jsonl"

        with open(file_path, "a") as f:
            f.write(json.dumps(asdict(validation)) + "\n")

    def _save_approval_request(self, request: HumanApprovalRequest):
        """Save approval request to storage"""
        file_path = self.storage_path / "approval_requests.jsonl"

        with open(file_path, "a") as f:
            f.write(json.dumps(asdict(request)) + "\n")

    def _save_consensus_request(self, request: ConsensusRequest):
        """Save consensus request to storage"""
        file_path = self.storage_path / "consensus_requests.jsonl"

        with open(file_path, "a") as f:
            f.write(json.dumps(asdict(request)) + "\n")

    def _save_emergency_stop(self, stop: EmergencyStop):
        """Save emergency stop to storage"""
        file_path = self.storage_path / "emergency_stops.jsonl"

        with open(file_path, "a") as f:
            f.write(json.dumps(asdict(stop)) + "\n")


# Global safety validator
decision_safety_validator = DecisionSafetyValidator()
