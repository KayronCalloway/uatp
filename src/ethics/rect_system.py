"""
Real-time Ethical Capsule Triggers (RECTs) for AI Safety.
Implements continuous ethical monitoring and intervention systems.
"""

import hashlib
import logging
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from src.audit.events import audit_emitter
from src.capsule_schema import AnyCapsule

logger = logging.getLogger(__name__)


class EthicalViolationType(str, Enum):
    """Types of ethical violations."""

    BIAS_DETECTION = "bias_detection"
    HARMFUL_CONTENT = "harmful_content"
    PRIVACY_VIOLATION = "privacy_violation"
    MISINFORMATION = "misinformation"
    MANIPULATION = "manipulation"
    TOXICITY = "toxicity"
    DISCRIMINATION = "discrimination"
    VIOLENCE = "violence"
    SELF_HARM = "self_harm"
    INAPPROPRIATE_CONTENT = "inappropriate_content"


class SeverityLevel(str, Enum):
    """Severity levels for ethical violations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class InterventionAction(str, Enum):
    """Types of intervention actions."""

    WARNING = "warning"
    CONTENT_FILTER = "content_filter"
    RATE_LIMIT = "rate_limit"
    QUARANTINE = "quarantine"
    BLOCK = "block"
    ESCALATE = "escalate"
    REDIRECT = "redirect"
    TERMINATE = "terminate"


@dataclass
class EthicalViolation:
    """Represents an ethical violation detected in a capsule."""

    violation_id: str
    capsule_id: str
    violation_type: EthicalViolationType
    severity: SeverityLevel
    confidence: float
    message: str
    detected_content: str
    context: Dict[str, Any]
    timestamp: datetime
    detector_id: str
    intervention_recommended: InterventionAction
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "violation_id": self.violation_id,
            "capsule_id": self.capsule_id,
            "violation_type": self.violation_type.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "message": self.message,
            "detected_content": self.detected_content,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "detector_id": self.detector_id,
            "intervention_recommended": self.intervention_recommended.value,
            "metadata": self.metadata,
        }


@dataclass
class EthicalRule:
    """Represents an ethical rule for capsule monitoring."""

    rule_id: str
    rule_type: EthicalViolationType
    pattern: str
    severity: SeverityLevel
    confidence_threshold: float
    intervention: InterventionAction
    enabled: bool = True
    violation_count: int = 0
    last_triggered: Optional[datetime] = None

    def matches(self, content: str) -> Tuple[bool, float]:
        """Check if content matches this rule."""
        if not self.enabled:
            return False, 0.0

        # Simple pattern matching (in production, use ML models)
        if self.pattern.startswith("regex:"):
            pattern = self.pattern[6:]
            matches = re.search(pattern, content, re.IGNORECASE)
            return matches is not None, 1.0 if matches else 0.0

        elif self.pattern.startswith("keywords:"):
            keywords = self.pattern[9:].split(",")
            matches = any(
                keyword.strip().lower() in content.lower() for keyword in keywords
            )
            return matches, 0.8 if matches else 0.0

        elif self.pattern.startswith("ml_model:"):
            # Placeholder for ML model inference
            return self._ml_model_check(content)

        return False, 0.0

    def _ml_model_check(self, content: str) -> Tuple[bool, float]:
        """Placeholder for ML model-based checking."""
        # In production, this would call actual ML models
        suspicious_terms = ["harmful", "toxic", "biased", "discriminatory"]
        score = sum(1 for term in suspicious_terms if term in content.lower()) / len(
            suspicious_terms
        )
        return score > 0.3, score


@dataclass
class InterventionResult:
    """Result of an ethical intervention."""

    violation_id: str
    action_taken: InterventionAction
    success: bool
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class EthicalRuleEngine:
    """Engine for managing and executing ethical rules."""

    def __init__(self):
        self.rules: Dict[str, EthicalRule] = {}
        self.rule_history: Dict[str, List[datetime]] = defaultdict(list)
        self._initialize_default_rules()

    def add_rule(self, rule: EthicalRule):
        """Add an ethical rule to the engine."""
        self.rules[rule.rule_id] = rule
        logger.info(f"Added ethical rule: {rule.rule_id}")

    def evaluate_content(self, content: str, capsule_id: str) -> List[EthicalViolation]:
        """Evaluate content against all ethical rules."""
        violations = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            matches, confidence = rule.matches(content)

            if matches and confidence >= rule.confidence_threshold:
                violation = EthicalViolation(
                    violation_id=self._generate_violation_id(),
                    capsule_id=capsule_id,
                    violation_type=rule.rule_type,
                    severity=rule.severity,
                    confidence=confidence,
                    message=f"Rule {rule.rule_id} triggered",
                    detected_content=content[:200] + "..."
                    if len(content) > 200
                    else content,
                    context={"rule_id": rule.rule_id, "pattern": rule.pattern},
                    timestamp=datetime.now(timezone.utc),
                    detector_id=rule.rule_id,
                    intervention_recommended=rule.intervention,
                )

                violations.append(violation)

                # Update rule statistics
                rule.violation_count += 1
                rule.last_triggered = datetime.now(timezone.utc)
                self.rule_history[rule.rule_id].append(rule.last_triggered)

        return violations

    def evaluate_capsule_ethics(self, capsule) -> Dict[str, Any]:
        """Evaluate capsule against ethical rules and return evaluation results."""
        # Extract content from capsule for evaluation
        content_parts = []

        # Add capsule ID and basic info - handle both dict and object
        if isinstance(capsule, dict):
            content_parts.append(f"Capsule ID: {capsule.get('capsule_id', 'unknown')}")
            content_parts.append(
                f"Capsule Type: {capsule.get('capsule_type', 'unknown')}"
            )
        else:
            content_parts.append(f"Capsule ID: {capsule.capsule_id}")
            content_parts.append(f"Capsule Type: {capsule.capsule_type}")

        # Extract content based on capsule type
        # Handle dict format capsules
        if isinstance(capsule, dict):
            if "content" in capsule:
                content_parts.append(str(capsule["content"]))
            if "metadata" in capsule:
                content_parts.append(str(capsule["metadata"]))

        # Handle object format capsules
        elif hasattr(capsule, "reasoning_trace") and capsule.reasoning_trace:
            # Handle both .steps and .reasoning_steps field names
            steps = getattr(
                capsule.reasoning_trace,
                "reasoning_steps",
                getattr(capsule.reasoning_trace, "steps", []),
            )
            for step in steps:
                if hasattr(step, "reasoning"):
                    content_parts.append(step.reasoning)
                elif hasattr(step, "content"):
                    content_parts.append(step.content)

        if hasattr(capsule, "economic_transaction") and capsule.economic_transaction:
            content_parts.append(
                f"Transaction: {capsule.economic_transaction.transaction_type}"
            )
            if hasattr(capsule.economic_transaction, "memo"):
                content_parts.append(capsule.economic_transaction.memo)

        if hasattr(capsule, "governance_vote") and capsule.governance_vote:
            content_parts.append(f"Vote: {capsule.governance_vote.proposal_title}")
            content_parts.append(capsule.governance_vote.justification)

        # Combine all content
        full_content = " ".join(content_parts)

        # Evaluate the content
        violations = self.evaluate_content(full_content, capsule.capsule_id)

        # Calculate ethics score
        if not violations:
            ethics_score = 1.0
            bias_detected = False
        else:
            # Calculate score based on violations
            severity_weights = {
                SeverityLevel.LOW: 0.1,
                SeverityLevel.MEDIUM: 0.3,
                SeverityLevel.HIGH: 0.6,
                SeverityLevel.CRITICAL: 0.8,
                SeverityLevel.EMERGENCY: 1.0,
            }

            total_penalty = sum(
                severity_weights.get(v.severity, 0.5) * v.confidence for v in violations
            )
            ethics_score = max(
                0.0, 1.0 - (total_penalty / len(violations) if violations else 0)
            )
            bias_detected = any(
                v.violation_type == EthicalViolationType.BIAS_DETECTION
                for v in violations
            )

        return {
            "ethics_score": ethics_score,
            "bias_detected": bias_detected,
            "violations": [v.violation_type.value for v in violations],
            "violation_details": [v.to_dict() for v in violations],
            "content_evaluated": full_content,
            "total_violations": len(violations),
        }

    def _initialize_default_rules(self):
        """Initialize default ethical rules."""
        default_rules = [
            EthicalRule(
                rule_id="bias_detection_basic",
                rule_type=EthicalViolationType.BIAS_DETECTION,
                pattern="keywords:biased,prejudiced,discriminatory,stereotypical",
                severity=SeverityLevel.MEDIUM,
                confidence_threshold=0.7,
                intervention=InterventionAction.WARNING,
            ),
            EthicalRule(
                rule_id="harmful_content_explicit",
                rule_type=EthicalViolationType.HARMFUL_CONTENT,
                pattern="keywords:violence,harm,attack,hurt,kill,destroy",
                severity=SeverityLevel.HIGH,
                confidence_threshold=0.8,
                intervention=InterventionAction.QUARANTINE,
            ),
            EthicalRule(
                rule_id="privacy_violation_pii",
                rule_type=EthicalViolationType.PRIVACY_VIOLATION,
                pattern="regex:\\b\\d{3}-\\d{2}-\\d{4}\\b|\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b",
                severity=SeverityLevel.HIGH,
                confidence_threshold=0.9,
                intervention=InterventionAction.CONTENT_FILTER,
            ),
            EthicalRule(
                rule_id="misinformation_claims",
                rule_type=EthicalViolationType.MISINFORMATION,
                pattern="keywords:fake news,conspiracy,hoax,false claim,debunked",
                severity=SeverityLevel.MEDIUM,
                confidence_threshold=0.6,
                intervention=InterventionAction.WARNING,
            ),
            EthicalRule(
                rule_id="manipulation_tactics",
                rule_type=EthicalViolationType.MANIPULATION,
                pattern="keywords:manipulate,deceive,trick,exploit,gaslight",
                severity=SeverityLevel.HIGH,
                confidence_threshold=0.8,
                intervention=InterventionAction.BLOCK,
            ),
            EthicalRule(
                rule_id="toxicity_detection",
                rule_type=EthicalViolationType.TOXICITY,
                pattern="keywords:toxic,hate,abuse,harassment,bully",
                severity=SeverityLevel.HIGH,
                confidence_threshold=0.7,
                intervention=InterventionAction.QUARANTINE,
            ),
            EthicalRule(
                rule_id="self_harm_prevention",
                rule_type=EthicalViolationType.SELF_HARM,
                pattern="keywords:suicide,self-harm,kill myself,end it all",
                severity=SeverityLevel.CRITICAL,
                confidence_threshold=0.8,
                intervention=InterventionAction.ESCALATE,
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)

    def _generate_violation_id(self) -> str:
        """Generate unique violation ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        hash_input = f"{timestamp}_{id(self)}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about rule performance."""
        stats = {
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for rule in self.rules.values() if rule.enabled),
            "rule_performance": {},
        }

        for rule_id, rule in self.rules.items():
            stats["rule_performance"][rule_id] = {
                "violation_count": rule.violation_count,
                "last_triggered": rule.last_triggered.isoformat()
                if rule.last_triggered
                else None,
                "severity": rule.severity.value,
                "enabled": rule.enabled,
            }

        return stats


class EthicalInterventionSystem:
    """System for executing ethical interventions."""

    def __init__(self):
        self.interventions: Dict[str, InterventionResult] = {}
        self.intervention_handlers: Dict[InterventionAction, Callable] = {}
        self._initialize_handlers()

    def execute_intervention(self, violation: EthicalViolation) -> InterventionResult:
        """Execute an intervention based on the violation."""

        action = violation.intervention_recommended
        handler = self.intervention_handlers.get(action)

        if not handler:
            logger.error(f"No handler for intervention action: {action}")
            return InterventionResult(
                violation_id=violation.violation_id,
                action_taken=action,
                success=False,
                message=f"No handler for action: {action}",
                timestamp=datetime.now(timezone.utc),
            )

        try:
            success, message, metadata = handler(violation)

            result = InterventionResult(
                violation_id=violation.violation_id,
                action_taken=action,
                success=success,
                message=message,
                timestamp=datetime.now(timezone.utc),
                metadata=metadata,
            )

            self.interventions[violation.violation_id] = result

            # Emit audit event
            audit_emitter.emit_capsule_created(
                capsule_id=violation.capsule_id,
                agent_id="ethical_intervention",
                capsule_type=f"intervention_{action.value}",
            )

            logger.info(
                f"Executed intervention {action.value} for violation {violation.violation_id}"
            )
            return result

        except Exception as e:
            logger.error(f"Intervention execution failed: {e}")
            return InterventionResult(
                violation_id=violation.violation_id,
                action_taken=action,
                success=False,
                message=f"Intervention failed: {str(e)}",
                timestamp=datetime.now(timezone.utc),
            )

    def _initialize_handlers(self):
        """Initialize intervention handlers."""
        self.intervention_handlers = {
            InterventionAction.WARNING: self._handle_warning,
            InterventionAction.CONTENT_FILTER: self._handle_content_filter,
            InterventionAction.RATE_LIMIT: self._handle_rate_limit,
            InterventionAction.QUARANTINE: self._handle_quarantine,
            InterventionAction.BLOCK: self._handle_block,
            InterventionAction.ESCALATE: self._handle_escalate,
            InterventionAction.REDIRECT: self._handle_redirect,
            InterventionAction.TERMINATE: self._handle_terminate,
        }

    def _handle_warning(
        self, violation: EthicalViolation
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle warning intervention."""
        logger.warning(
            f"Ethical warning for capsule {violation.capsule_id}: {violation.message}"
        )
        return True, "Warning logged", {"warning_level": violation.severity.value}

    def _handle_content_filter(
        self, violation: EthicalViolation
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle content filtering intervention."""
        # In production, this would filter/redact content
        filtered_content = "[FILTERED]"
        return True, "Content filtered", {"filtered_content": filtered_content}

    def _handle_rate_limit(
        self, violation: EthicalViolation
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle rate limiting intervention."""
        # In production, this would implement actual rate limiting
        return True, "Rate limit applied", {"limit_duration": 300}  # 5 minutes

    def _handle_quarantine(
        self, violation: EthicalViolation
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle quarantine intervention."""
        # In production, this would quarantine the capsule
        return True, "Capsule quarantined", {"quarantine_duration": 3600}  # 1 hour

    def _handle_block(
        self, violation: EthicalViolation
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle blocking intervention."""
        # In production, this would block the capsule/user
        return True, "Access blocked", {"block_reason": violation.violation_type.value}

    def _handle_escalate(
        self, violation: EthicalViolation
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle escalation intervention."""
        # In production, this would escalate to human moderators
        return True, "Escalated to human review", {"escalation_priority": "high"}

    def _handle_redirect(
        self, violation: EthicalViolation
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle redirect intervention."""
        # In production, this would redirect to appropriate resources
        return (
            True,
            "Redirected to resources",
            {"redirect_url": "https://help.example.com"},
        )

    def _handle_terminate(
        self, violation: EthicalViolation
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle termination intervention."""
        # In production, this would terminate the session/connection
        return (
            True,
            "Session terminated",
            {"termination_reason": violation.violation_type.value},
        )


class EthicalMonitor:
    """Real-time ethical monitoring system."""

    def __init__(self):
        self.rule_engine = EthicalRuleEngine()
        self.intervention_system = EthicalInterventionSystem()
        self.violation_history: deque = deque(maxlen=10000)  # Keep last 10k violations
        self.monitoring_stats = {
            "total_capsules_monitored": 0,
            "violations_detected": 0,
            "interventions_executed": 0,
            "false_positives": 0,
        }
        self.whitelist: Set[str] = set()
        self.blacklist: Set[str] = set()

    def monitor_capsule(self, capsule: AnyCapsule) -> List[EthicalViolation]:
        """Monitor a capsule for ethical violations."""

        self.monitoring_stats["total_capsules_monitored"] += 1

        # Check whitelist/blacklist
        if capsule.capsule_id in self.whitelist:
            logger.info(
                f"Capsule {capsule.capsule_id} is whitelisted, skipping monitoring"
            )
            return []

        if capsule.capsule_id in self.blacklist:
            logger.warning(f"Capsule {capsule.capsule_id} is blacklisted")
            # Create a blacklist violation
            violation = EthicalViolation(
                violation_id=self._generate_violation_id(),
                capsule_id=capsule.capsule_id,
                violation_type=EthicalViolationType.HARMFUL_CONTENT,
                severity=SeverityLevel.CRITICAL,
                confidence=1.0,
                message="Capsule is blacklisted",
                detected_content="[BLACKLISTED]",
                context={"reason": "blacklisted"},
                timestamp=datetime.now(timezone.utc),
                detector_id="blacklist_checker",
                intervention_recommended=InterventionAction.BLOCK,
            )
            return [violation]

        # Extract content for monitoring
        content = self._extract_content(capsule)

        # Monitor content
        violations = self.rule_engine.evaluate_content(content, capsule.capsule_id)

        # Process violations
        for violation in violations:
            self.violation_history.append(violation)
            self.monitoring_stats["violations_detected"] += 1

            # Execute intervention
            intervention_result = self.intervention_system.execute_intervention(
                violation
            )

            if intervention_result.success:
                self.monitoring_stats["interventions_executed"] += 1

            # Log violation
            logger.warning(
                f"Ethical violation detected: {violation.violation_type.value} "
                f"in capsule {violation.capsule_id} (confidence: {violation.confidence:.2f})"
            )

        return violations

    def add_to_whitelist(self, capsule_id: str):
        """Add capsule to whitelist."""
        self.whitelist.add(capsule_id)
        logger.info(f"Added {capsule_id} to whitelist")

    def add_to_blacklist(self, capsule_id: str):
        """Add capsule to blacklist."""
        self.blacklist.add(capsule_id)
        logger.warning(f"Added {capsule_id} to blacklist")

    def report_false_positive(self, violation_id: str):
        """Report a false positive violation."""
        self.monitoring_stats["false_positives"] += 1
        logger.info(f"False positive reported for violation {violation_id}")

    def get_monitoring_report(self) -> Dict[str, Any]:
        """Get comprehensive monitoring report."""
        # Recent violations (last 24 hours)
        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_violations = [
            v for v in self.violation_history if v.timestamp >= recent_cutoff
        ]

        # Violation breakdown by type
        violation_breakdown = defaultdict(int)
        for violation in recent_violations:
            violation_breakdown[violation.violation_type.value] += 1

        # Severity distribution
        severity_distribution = defaultdict(int)
        for violation in recent_violations:
            severity_distribution[violation.severity.value] += 1

        return {
            "monitoring_stats": dict(self.monitoring_stats),
            "recent_violations": len(recent_violations),
            "violation_breakdown": dict(violation_breakdown),
            "severity_distribution": dict(severity_distribution),
            "rule_statistics": self.rule_engine.get_rule_statistics(),
            "whitelist_size": len(self.whitelist),
            "blacklist_size": len(self.blacklist),
            "false_positive_rate": (
                self.monitoring_stats["false_positives"]
                / max(self.monitoring_stats["violations_detected"], 1)
            )
            * 100,
        }

    def _extract_content(self, capsule: AnyCapsule) -> str:
        """Extract content from capsule for monitoring."""
        content_parts = []

        # Extract based on capsule type
        if hasattr(capsule, "reasoning_trace") and capsule.reasoning_trace:
            # Handle both .steps and .reasoning_steps field names
            steps = getattr(
                capsule.reasoning_trace,
                "reasoning_steps",
                getattr(capsule.reasoning_trace, "steps", []),
            )
            for step in steps:
                # Use 'reasoning' field (primary) or 'content' field (alias)
                content = getattr(step, "reasoning", getattr(step, "content", ""))
                content_parts.append(content)

        if hasattr(capsule, "uncertainty") and capsule.uncertainty:
            content_parts.extend(capsule.uncertainty.missing_facts)
            content_parts.append(capsule.uncertainty.recommendation)

        if hasattr(capsule, "manipulation_attempt") and capsule.manipulation_attempt:
            content_parts.append(capsule.manipulation_attempt.attempt_type)

        return " ".join(content_parts)

    def _generate_violation_id(self) -> str:
        """Generate unique violation ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        hash_input = f"{timestamp}_{id(self)}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]


class RECTSystem:
    """Real-time Ethical Capsule Trigger System."""

    def __init__(self):
        self.monitor = EthicalMonitor()
        self.enabled = True
        self.emergency_contacts = []
        self.escalation_thresholds = {
            SeverityLevel.CRITICAL: 1,  # Immediate escalation
            SeverityLevel.HIGH: 5,  # Escalate after 5 violations
            SeverityLevel.MEDIUM: 20,  # Escalate after 20 violations
            SeverityLevel.LOW: 100,  # Escalate after 100 violations
        }
        self.violation_counters = defaultdict(int)

    def process_capsule(self, capsule: AnyCapsule) -> Dict[str, Any]:
        """Process a capsule through the RECT system."""

        if not self.enabled:
            return {"rect_enabled": False, "violations": []}

        # Monitor for violations
        violations = self.monitor.monitor_capsule(capsule)

        # Check for escalation
        for violation in violations:
            self.violation_counters[violation.severity] += 1

            threshold = self.escalation_thresholds.get(violation.severity, float("inf"))
            if self.violation_counters[violation.severity] >= threshold:
                self._trigger_escalation(violation)

        # Create response
        response = {
            "rect_enabled": True,
            "capsule_id": capsule.capsule_id,
            "violations": [v.to_dict() for v in violations],
            "violation_count": len(violations),
            "highest_severity": max(
                [v.severity for v in violations], default=SeverityLevel.LOW
            ).value,
            "actions_taken": [v.intervention_recommended.value for v in violations],
        }

        return response

    def _trigger_escalation(self, violation: EthicalViolation):
        """Trigger escalation for severe violations."""
        logger.critical(
            f"RECT escalation triggered for {violation.severity.value} violation: {violation.message}"
        )

        # In production, this would notify human moderators

        # Reset counter after escalation
        self.violation_counters[violation.severity] = 0

    def enable_system(self):
        """Enable the RECT system."""
        self.enabled = True
        logger.info("RECT system enabled")

    def disable_system(self):
        """Disable the RECT system."""
        self.enabled = False
        logger.warning("RECT system disabled")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "enabled": self.enabled,
            "monitoring_report": self.monitor.get_monitoring_report(),
            "violation_counters": dict(self.violation_counters),
            "escalation_thresholds": {
                k.value: v for k, v in self.escalation_thresholds.items()
            },
            "emergency_contacts": len(self.emergency_contacts),
        }


# Global RECT system instance
rect_system = RECTSystem()
