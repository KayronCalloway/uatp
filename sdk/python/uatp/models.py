"""
UATP Rich Data Models - Court-admissible, Insurance-ready formats
"""

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class OutcomeStatus(Enum):
    """Outcome status for tracked decisions."""

    SUCCESSFUL = "successful"
    FAILED = "failed"
    PARTIAL = "partial"
    PENDING = "pending"
    UNKNOWN = "unknown"


@dataclass
class DataSource:
    """
    Provenance tracking for data used in AI decision.

    Required for court admissibility (Daubert standard).
    """

    source: str  # e.g., "Experian Credit Bureau", "Hospital Scheduling API"
    value: Any  # The actual data retrieved
    timestamp: Optional[str] = None  # When data was retrieved
    api_endpoint: Optional[str] = None
    api_version: Optional[str] = None
    query: Optional[str] = None
    response_time_ms: Optional[int] = None
    verification: Optional[Dict[str, Any]] = None  # Cross-check with other sources
    audit_trail: Optional[str] = None  # Request ID, user, etc.
    schema_version: str = "2.0"  # NEW: For safe schema evolution

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, removing None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Alternative:
    """
    Alternative option that was considered but not selected.

    Required for showing decision methodology.
    """

    option: str  # Description of alternative
    score: Optional[float] = None  # How it scored vs. chosen option
    why_not_chosen: str = ""  # Explanation for rejection
    data: Optional[Dict[str, Any]] = None  # Supporting data
    schema_version: str = "2.0"  # NEW: For safe schema evolution

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class RiskAssessment:
    """
    Quantitative risk analysis for insurance and compliance.

    Required for actuarial modeling and enterprise risk management.
    """

    probability_correct: float  # e.g., 0.87 = 87% likely correct
    probability_wrong: float  # e.g., 0.13 = 13% likely wrong

    # Financial impact
    expected_value: Optional[float] = None  # Expected financial outcome
    value_at_risk_95: Optional[float] = None  # 95% worst case scenario
    expected_loss_if_wrong: Optional[float] = None
    expected_gain_if_correct: Optional[float] = None

    # Risk factors
    key_risk_factors: Optional[List[str]] = None
    safeguards: Optional[List[str]] = None
    failure_modes: Optional[List[Dict[str, Any]]] = None

    # Historical context
    similar_decisions_count: Optional[int] = None
    historical_accuracy: Optional[float] = None
    schema_version: str = "2.0"  # NEW: For safe schema evolution

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ReasoningStep:
    """
    Enhanced reasoning step with full provenance and methodology.

    This is the court-admissible version.
    """

    step: int
    action: str  # What the AI did (e.g., "Verified credit score")
    confidence: float

    # Data provenance (REQUIRED for Daubert)
    data_sources: Optional[List[DataSource]] = None

    # Methodology (REQUIRED for Daubert)
    decision_criteria: Optional[List[str]] = None
    alternatives_evaluated: Optional[List[Alternative]] = None

    # Explanation
    reasoning: str = ""  # Technical explanation
    plain_language: str = ""  # Non-technical explanation

    # Confidence basis
    confidence_basis: Optional[str] = None
    uncertainty_factors: Optional[List[str]] = None

    # Additional context
    metadata: Optional[Dict[str, Any]] = None
    schema_version: str = "2.0"  # NEW: For safe schema evolution

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict with proper serialization."""
        result = {
            "step": self.step,
            "action": self.action,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }

        if self.plain_language:
            result["plain_language"] = self.plain_language

        if self.data_sources:
            result["data_sources"] = [ds.to_dict() for ds in self.data_sources]

        if self.decision_criteria:
            result["decision_criteria"] = self.decision_criteria

        if self.alternatives_evaluated:
            result["alternatives_evaluated"] = [
                alt.to_dict() for alt in self.alternatives_evaluated
            ]

        if self.confidence_basis:
            result["confidence_basis"] = self.confidence_basis

        if self.uncertainty_factors:
            result["uncertainty_factors"] = self.uncertainty_factors

        if self.metadata:
            result["metadata"] = self.metadata

        return result


@dataclass
class Outcome:
    """
    Actual outcome of the AI decision (ground truth).

    Required for machine learning improvement and insurance claims.
    """

    occurred: bool  # Did the predicted event happen?
    timestamp: str  # When was outcome recorded
    result: OutcomeStatus

    # Validation
    ai_was_correct: Optional[bool] = None
    actual_vs_predicted: Optional[str] = None

    # Impact assessment
    financial_impact: Optional[float] = None
    customer_satisfaction: Optional[float] = None  # 1-5 scale
    business_impact: Optional[str] = None

    # Additional context
    complications: Optional[List[str]] = None
    lessons_learned: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if isinstance(result.get("result"), OutcomeStatus):
            result["result"] = result["result"].value
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class PlainLanguageSummary:
    """
    Non-technical explanation for EU AI Act Article 13 compliance.

    Required for user transparency and regulatory compliance.
    """

    decision: str  # What was decided
    why: str  # Why this decision was made (simple terms)
    key_factors: List[str]  # Main factors that influenced decision

    what_if_different: Optional[str] = None  # What would cause different decision
    your_rights: Optional[str] = None  # User rights (for EU AI Act)
    how_to_appeal: Optional[str] = None
    schema_version: str = "2.0"  # NEW: For safe schema evolution

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


def create_simple_reasoning_step(
    step: int, thought: str, confidence: float
) -> Dict[str, Any]:
    """
    Helper to create basic reasoning step (backward compatible).

    For quick adoption, allows old format but encourages upgrade.
    """
    return {
        "step": step,
        "thought": thought,
        "confidence": confidence,
        "_note": "⚠️ Using simple format. Upgrade to ReasoningStep for court admissibility.",
    }


def create_rich_reasoning_step(
    step: int,
    action: str,
    confidence: float,
    data_sources: List[DataSource],
    reasoning: str,
    plain_language: str = "",
    alternatives: Optional[List[Alternative]] = None,
    confidence_basis: Optional[str] = None,
) -> ReasoningStep:
    """
    Helper to create rich reasoning step (recommended).

    This is the court-admissible, insurance-ready format.
    """
    return ReasoningStep(
        step=step,
        action=action,
        confidence=confidence,
        data_sources=data_sources,
        reasoning=reasoning,
        plain_language=plain_language,
        alternatives_evaluated=alternatives,
        confidence_basis=confidence_basis,
    )
