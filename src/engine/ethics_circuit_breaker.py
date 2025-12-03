#!/usr/bin/env python3
"""
UATP Ethics Circuit Breaker
Integrates ethical evaluation into capsule lifecycle with refusal logic.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.audit.events import audit_emitter
from src.capsule_schema import AnyCapsule, CapsuleStatus
from src.ethics.rect_system import (
    EthicalViolationType,
    InterventionAction,
    RECTSystem,
    SeverityLevel,
)

logger = logging.getLogger(__name__)


class RefusalReason(str, Enum):
    """Reasons for capsule refusal."""

    ETHICAL_VIOLATION = "ethical_violation"
    HARMFUL_CONTENT = "harmful_content"
    BIAS_DETECTED = "bias_detected"
    PRIVACY_VIOLATION = "privacy_violation"
    POLICY_VIOLATION = "policy_violation"
    SAFETY_CONCERN = "safety_concern"
    INAPPROPRIATE_CONTENT = "inappropriate_content"


@dataclass
class EthicsEvaluation:
    """Result of ethics evaluation."""

    allowed: bool
    confidence: float
    violations: List[EthicalViolationType] = field(default_factory=list)
    severity: SeverityLevel = SeverityLevel.LOW
    intervention_action: InterventionAction = InterventionAction.WARNING
    refusal_reason: Optional[RefusalReason] = None
    explanation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RefusalCapsule:
    """Represents a refused capsule with explanation."""

    original_capsule_id: str
    refusal_reason: RefusalReason
    explanation: str
    timestamp: datetime
    severity: SeverityLevel
    violations: List[EthicalViolationType]
    metadata: Dict[str, Any] = field(default_factory=dict)


class EthicsCircuitBreaker:
    """
    Circuit breaker that evaluates capsules for ethical violations
    and can refuse creation if violations are detected.
    """

    def __init__(self, enable_refusal: bool = True, strict_mode: bool = False):
        self.enable_refusal = enable_refusal
        self.strict_mode = strict_mode
        # Directly integrate with ethics/rect_system.py for real-time ethical monitoring
        self.rect_system = RECTSystem()
        self.refused_capsules: Dict[str, RefusalCapsule] = {}
        self.evaluation_history: List[EthicsEvaluation] = []

        # Circuit breaker configuration
        self.refusal_threshold = 0.7 if strict_mode else 0.8
        self.critical_threshold = 0.9

        logger.info(
            f"Ethics Circuit Breaker initialized (refusal={enable_refusal}, strict={strict_mode})"
        )

    async def evaluate_capsule_ethics(self, capsule: AnyCapsule) -> EthicsEvaluation:
        """
        Evaluate a capsule for ethical violations.

        Args:
            capsule: The capsule to evaluate

        Returns:
            EthicsEvaluation with decision and details
        """
        try:
            # Get ethics evaluation from RECT system (ethics/rect_system.py)
            rect_result = self.rect_system.monitor.rule_engine.evaluate_capsule_ethics(
                capsule
            )

            # Extract key metrics
            ethics_score = rect_result.get("ethics_score", 0.0)
            bias_detected = rect_result.get("bias_detected", False)
            violations = rect_result.get("violations", [])
            severity = self._determine_severity(ethics_score, bias_detected, violations)

            # Determine if capsule should be allowed
            allowed = self._should_allow_capsule(ethics_score, severity, violations)

            # Determine intervention action
            intervention_action = self._determine_intervention_action(
                ethics_score, severity
            )

            # Create refusal reason if needed
            refusal_reason = None
            explanation = ""
            if not allowed:
                refusal_reason, explanation = self._generate_refusal_details(
                    ethics_score, violations, severity
                )

            evaluation = EthicsEvaluation(
                allowed=allowed,
                confidence=ethics_score,
                violations=violations,
                severity=severity,
                intervention_action=intervention_action,
                refusal_reason=refusal_reason,
                explanation=explanation,
                metadata={
                    "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
                    "bias_detected": bias_detected,
                    "rect_result": rect_result,
                    "capsule_type": capsule.capsule_type.value,
                    "strict_mode": self.strict_mode,
                },
            )

            # Store evaluation in history
            self.evaluation_history.append(evaluation)

            # Log the evaluation
            logger.info(
                f"Ethics evaluation for capsule {capsule.capsule_id}: "
                f"allowed={allowed}, score={ethics_score:.2f}, severity={severity.value}"
            )

            return evaluation

        except Exception as e:
            capsule_id = getattr(
                capsule,
                "capsule_id",
                capsule.get("capsule_id", "unknown")
                if isinstance(capsule, dict)
                else "unknown",
            )
            logger.error(f"Ethics evaluation failed for capsule {capsule_id}: {e}")
            # In case of evaluation failure, be conservative
            return EthicsEvaluation(
                allowed=False if self.strict_mode else True,
                confidence=0.0,
                violations=[EthicalViolationType.HARMFUL_CONTENT],
                severity=SeverityLevel.HIGH,
                intervention_action=InterventionAction.BLOCK,
                refusal_reason=RefusalReason.SAFETY_CONCERN,
                explanation=f"Ethics evaluation failed: {str(e)}",
                metadata={"evaluation_error": str(e)},
            )

    def _determine_severity(
        self,
        ethics_score: float,
        bias_detected: bool,
        violations: List[EthicalViolationType],
    ) -> SeverityLevel:
        """Determine severity level based on evaluation results."""
        if ethics_score < 0.3:
            return SeverityLevel.CRITICAL
        elif ethics_score < 0.5:
            return SeverityLevel.HIGH
        elif ethics_score < 0.7 or bias_detected:
            return SeverityLevel.MEDIUM
        elif violations:
            return SeverityLevel.LOW
        else:
            return SeverityLevel.LOW

    def _should_allow_capsule(
        self,
        ethics_score: float,
        severity: SeverityLevel,
        violations: List[EthicalViolationType],
    ) -> bool:
        """Determine if capsule should be allowed based on ethics evaluation."""
        if not self.enable_refusal:
            return True

        # Critical violations are always blocked
        if severity == SeverityLevel.CRITICAL:
            return False

        # Check against threshold
        if ethics_score < self.refusal_threshold:
            return False

        # Check for specific critical violations
        critical_violations = {
            EthicalViolationType.VIOLENCE,
            EthicalViolationType.SELF_HARM,
            EthicalViolationType.HARMFUL_CONTENT,
        }

        if any(v in critical_violations for v in violations):
            return False

        # In strict mode, be more restrictive
        if self.strict_mode and (severity == SeverityLevel.HIGH or len(violations) > 2):
            return False

        return True

    def _determine_intervention_action(
        self, ethics_score: float, severity: SeverityLevel
    ) -> InterventionAction:
        """Determine what intervention action to take."""
        if severity == SeverityLevel.CRITICAL:
            return InterventionAction.BLOCK
        elif severity == SeverityLevel.HIGH:
            return InterventionAction.QUARANTINE
        elif severity == SeverityLevel.MEDIUM:
            return InterventionAction.CONTENT_FILTER
        else:
            return InterventionAction.WARNING

    def _generate_refusal_details(
        self,
        ethics_score: float,
        violations: List[EthicalViolationType],
        severity: SeverityLevel,
    ) -> Tuple[RefusalReason, str]:
        """Generate refusal reason and explanation."""
        if EthicalViolationType.HARMFUL_CONTENT in violations:
            return (
                RefusalReason.HARMFUL_CONTENT,
                "Content detected as potentially harmful",
            )
        elif EthicalViolationType.BIAS_DETECTION in violations:
            return RefusalReason.BIAS_DETECTED, "Bias detected in content"
        elif EthicalViolationType.PRIVACY_VIOLATION in violations:
            return RefusalReason.PRIVACY_VIOLATION, "Privacy violation detected"
        elif EthicalViolationType.VIOLENCE in violations:
            return RefusalReason.SAFETY_CONCERN, "Violence-related content detected"
        elif EthicalViolationType.INAPPROPRIATE_CONTENT in violations:
            return RefusalReason.INAPPROPRIATE_CONTENT, "Inappropriate content detected"
        elif severity == SeverityLevel.CRITICAL:
            return (
                RefusalReason.SAFETY_CONCERN,
                f"Critical safety concern (score: {ethics_score:.2f})",
            )
        else:
            return (
                RefusalReason.ETHICAL_VIOLATION,
                f"Ethical violation detected (score: {ethics_score:.2f})",
            )

    async def refuse_capsule(
        self, capsule: AnyCapsule, evaluation: EthicsEvaluation
    ) -> RefusalCapsule:
        """
        Refuse a capsule and create a refusal record.

        Args:
            capsule: The capsule being refused
            evaluation: The ethics evaluation result

        Returns:
            RefusalCapsule with refusal details
        """
        refusal = RefusalCapsule(
            original_capsule_id=capsule.capsule_id,
            refusal_reason=evaluation.refusal_reason,
            explanation=evaluation.explanation,
            timestamp=datetime.now(timezone.utc),
            severity=evaluation.severity,
            violations=evaluation.violations,
            metadata={
                "capsule_type": capsule.capsule_type.value,
                "evaluation_confidence": evaluation.confidence,
                "intervention_action": evaluation.intervention_action.value,
                "strict_mode": self.strict_mode,
            },
        )

        # Store refusal
        self.refused_capsules[capsule.capsule_id] = refusal

        # Emit audit event
        audit_emitter.emit_capsule_refused(
            capsule_id=capsule.capsule_id,
            reason=evaluation.refusal_reason.value,
            severity=evaluation.severity.value,
        )

        logger.warning(
            f"Capsule {capsule.capsule_id} refused: {evaluation.refusal_reason.value}"
        )

        return refusal

    async def pre_creation_check(
        self, capsule: AnyCapsule
    ) -> Tuple[bool, Optional[RefusalCapsule]]:
        """
        Check if a capsule should be allowed before creation.

        Args:
            capsule: The capsule to check

        Returns:
            Tuple of (allowed, refusal_capsule_if_refused)
        """
        evaluation = await self.evaluate_capsule_ethics(capsule)

        if evaluation.allowed:
            return True, None
        else:
            refusal = await self.refuse_capsule(capsule, evaluation)
            return False, refusal

    def get_refusal_statistics(self) -> Dict[str, Any]:
        """Get statistics about refusals."""
        if not self.refused_capsules:
            return {
                "total_refusals": 0,
                "refusal_rate": 0.0,
                "refusal_reasons": {},
                "severity_distribution": {},
            }

        total_evaluations = len(self.evaluation_history)
        total_refusals = len(self.refused_capsules)

        refusal_reasons = {}
        severity_distribution = {}

        for refusal in self.refused_capsules.values():
            refusal_reasons[refusal.refusal_reason.value] = (
                refusal_reasons.get(refusal.refusal_reason.value, 0) + 1
            )
            severity_distribution[refusal.severity.value] = (
                severity_distribution.get(refusal.severity.value, 0) + 1
            )

        return {
            "total_refusals": total_refusals,
            "total_evaluations": total_evaluations,
            "refusal_rate": (total_refusals / max(1, total_evaluations)) * 100,
            "refusal_reasons": refusal_reasons,
            "severity_distribution": severity_distribution,
            "strict_mode": self.strict_mode,
            "refusal_threshold": self.refusal_threshold,
        }

    def get_recent_refusals(self, hours: int = 24) -> List[RefusalCapsule]:
        """Get refusals from the last N hours."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        return [
            refusal
            for refusal in self.refused_capsules.values()
            if refusal.timestamp > cutoff_time
        ]

    def is_capsule_refused(self, capsule_id: str) -> bool:
        """Check if a capsule was refused."""
        return capsule_id in self.refused_capsules

    def get_refusal_details(self, capsule_id: str) -> Optional[RefusalCapsule]:
        """Get refusal details for a specific capsule."""
        return self.refused_capsules.get(capsule_id)


# Global ethics circuit breaker instance
ethics_circuit_breaker = EthicsCircuitBreaker(enable_refusal=True, strict_mode=False)


class EthicsIntegratedCapsuleEngine:
    """
    Wrapper for CapsuleEngine that integrates ethics circuit breaker.
    """

    def __init__(
        self, base_engine, circuit_breaker: Optional[EthicsCircuitBreaker] = None
    ):
        self.base_engine = base_engine
        self.circuit_breaker = circuit_breaker or ethics_circuit_breaker
        logger.info("Ethics-integrated capsule engine initialized")

    async def create_capsule_async(self, capsule: AnyCapsule) -> AnyCapsule:
        """Create capsule with ethics checking."""
        # Pre-creation ethics check
        allowed, refusal = await self.circuit_breaker.pre_creation_check(capsule)

        if not allowed:
            logger.warning(f"Capsule creation blocked: {refusal.explanation}")
            raise ValueError(f"Capsule refused: {refusal.explanation}")

        # If allowed, proceed with normal creation
        return await self.base_engine.create_capsule_async(capsule)

    async def create_capsule_from_prompt_async(
        self, prompt: str, **kwargs
    ) -> AnyCapsule:
        """Create capsule from prompt with ethics checking."""
        # First, create the capsule normally
        capsule = await self.base_engine.create_capsule_from_prompt_async(
            prompt, **kwargs
        )

        # Then do post-creation ethics check
        evaluation = await self.circuit_breaker.evaluate_capsule_ethics(capsule)

        if not evaluation.allowed:
            # If ethics check fails, we need to handle the already-created capsule
            refusal = await self.circuit_breaker.refuse_capsule(capsule, evaluation)
            logger.warning(
                f"Capsule created but flagged for ethics violation: {refusal.explanation}"
            )

            # Mark capsule as quarantined or blocked
            capsule.status = CapsuleStatus.QUARANTINED

            # Could also delete or mark as invalid depending on policy
            # For now, we'll let it exist but marked as quarantined

        return capsule

    def get_ethics_dashboard(self) -> Dict[str, Any]:
        """Get ethics dashboard information."""
        stats = self.circuit_breaker.get_refusal_statistics()
        recent_refusals = self.circuit_breaker.get_recent_refusals(hours=24)

        return {
            "statistics": stats,
            "recent_refusals": len(recent_refusals),
            "circuit_breaker_config": {
                "enable_refusal": self.circuit_breaker.enable_refusal,
                "strict_mode": self.circuit_breaker.strict_mode,
                "refusal_threshold": self.circuit_breaker.refusal_threshold,
            },
            "recent_refusal_details": [
                {
                    "capsule_id": r.original_capsule_id,
                    "reason": r.refusal_reason.value,
                    "severity": r.severity.value,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in recent_refusals[:10]  # Last 10 refusals
            ],
        }


# Example usage and testing
if __name__ == "__main__":

    async def test_ethics_circuit_breaker():
        """Test the ethics circuit breaker."""
        from src.capsule_schema import CapsuleStatus, CapsuleType

        from capsules.specialized_capsules import ReasoningCapsule

        print("🛡️ Ethics Circuit Breaker Test")
        print("=" * 40)

        # Create circuit breaker
        circuit_breaker = EthicsCircuitBreaker(enable_refusal=True, strict_mode=False)

        # Create test capsules
        safe_capsule = ReasoningCapsule(
            capsule_id="safe_test_001",
            capsule_type=CapsuleType.REASONING,
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.ACTIVE,
        )

        # Test safe capsule
        print("Testing safe capsule...")
        allowed, refusal = await circuit_breaker.pre_creation_check(safe_capsule)
        print(f"✅ Safe capsule allowed: {allowed}")

        # Test ethics evaluation
        evaluation = await circuit_breaker.evaluate_capsule_ethics(safe_capsule)
        print(f"✅ Ethics score: {evaluation.confidence:.2f}")
        print(f"✅ Severity: {evaluation.severity.value}")
        print(f"✅ Intervention: {evaluation.intervention_action.value}")

        # Get statistics
        stats = circuit_breaker.get_refusal_statistics()
        print("\n📊 Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print("\n🎉 Ethics circuit breaker test complete!")

    asyncio.run(test_ethics_circuit_breaker())
