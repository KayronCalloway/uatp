"""
Reasoning Step Schema with Confidence Tracking
Supports hybrid approach: simple strings or detailed confidence tracking
"""

from typing import Optional, List, Union, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class ReasoningStep(BaseModel):
    """
    Detailed reasoning step with confidence tracking.

    Use this for steps that involve:
    - Decisions with uncertainty
    - Performance estimates
    - Security assessments
    - Architectural choices
    - Measured results
    - Assumptions
    """

    step: int = Field(..., description="Step number in the reasoning sequence")
    reasoning: str = Field(..., description="The reasoning text or decision made")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence level in this step (0.0 to 1.0)"
    )

    # Uncertainty tracking
    uncertainty_sources: Optional[List[str]] = Field(
        None, description="Sources of uncertainty in this step"
    )
    confidence_basis: Optional[str] = Field(
        None,
        description="How confidence was determined (e.g., 'measured', 'estimated', 'expert judgment')",
    )

    # Supporting evidence
    measurements: Optional[dict] = Field(
        None, description="Any measurements or data supporting this step"
    )
    alternatives_considered: Optional[List[str]] = Field(
        None, description="Alternative approaches that were considered"
    )

    # Dependencies
    depends_on_steps: Optional[List[int]] = Field(
        None, description="Step numbers this step depends on"
    )

    # Metadata
    operation: Optional[str] = Field(
        None,
        description="Type of operation (e.g., 'decision', 'measurement', 'estimation')",
    )
    attribution_sources: Optional[List[str]] = Field(
        None, description="Attribution for this step (who contributed)"
    )
    timestamp: Optional[datetime] = Field(
        None, description="When this step was executed"
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


class ConfidenceMethodology(BaseModel):
    """Describes how overall confidence was computed from step confidences."""

    method: Literal[
        "weakest_critical_link",  # Min of critical path
        "weighted_average",  # Weighted by importance
        "monte_carlo",  # Simulation-based
        "manual",  # Manually assessed
    ] = Field(..., description="Method used to compute overall confidence")

    critical_path_steps: Optional[List[int]] = Field(
        None,
        description="Steps that form the critical path (for weakest_critical_link)",
    )

    step_weights: Optional[dict[int, float]] = Field(
        None, description="Importance weights per step (for weighted_average)"
    )

    explanation: Optional[str] = Field(
        None, description="Human-readable explanation of confidence computation"
    )


class ReasoningTrace(BaseModel):
    """
    Complete reasoning trace with hybrid step support.

    Steps can be:
    - Simple strings for factual/deterministic steps
    - ReasoningStep objects for uncertain/critical steps
    """

    reasoning_steps: List[Union[str, ReasoningStep]] = Field(
        ..., description="List of reasoning steps (strings or detailed objects)"
    )

    overall_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Overall confidence in the reasoning trace"
    )

    confidence_methodology: Optional[ConfidenceMethodology] = Field(
        None, description="How overall confidence was computed"
    )

    @property
    def detailed_steps(self) -> List[ReasoningStep]:
        """Get only the detailed steps with confidence tracking."""
        return [
            step for step in self.reasoning_steps if isinstance(step, ReasoningStep)
        ]

    @property
    def simple_steps(self) -> List[str]:
        """Get only the simple string steps."""
        return [step for step in self.reasoning_steps if isinstance(step, str)]

    def get_step(self, step_number: int) -> Optional[Union[str, ReasoningStep]]:
        """Get a specific step by number."""
        if isinstance(self.reasoning_steps[step_number], ReasoningStep):
            return self.reasoning_steps[step_number]
        return None

    def compute_confidence(
        self,
        method: Literal[
            "weakest_critical_link", "weighted_average", "manual"
        ] = "weakest_critical_link",
        critical_steps: Optional[List[int]] = None,
        weights: Optional[dict[int, float]] = None,
    ) -> float:
        """
        Compute overall confidence from step confidences.

        Args:
            method: Computation method
            critical_steps: Critical path step numbers (for weakest_critical_link)
            weights: Step importance weights (for weighted_average)

        Returns:
            Overall confidence score
        """
        detailed = self.detailed_steps
        if not detailed:
            return self.overall_confidence

        if method == "weakest_critical_link":
            if critical_steps:
                critical = [s for s in detailed if s.step in critical_steps]
                return min(s.confidence for s in critical) if critical else 1.0
            else:
                return min(s.confidence for s in detailed)

        elif method == "weighted_average":
            if weights:
                total = sum(s.confidence * weights.get(s.step, 1.0) for s in detailed)
                weight_sum = sum(weights.get(s.step, 1.0) for s in detailed)
                return total / weight_sum if weight_sum > 0 else 1.0
            else:
                return sum(s.confidence for s in detailed) / len(detailed)

        else:  # manual
            return self.overall_confidence


# Utility functions for creating reasoning traces


def create_simple_trace(steps: List[str], confidence: float = 1.0) -> ReasoningTrace:
    """Create a reasoning trace with only simple string steps."""
    return ReasoningTrace(reasoning_steps=steps, overall_confidence=confidence)


def create_hybrid_trace(
    steps: List[Union[str, dict]],
    method: str = "weakest_critical_link",
    critical_steps: Optional[List[int]] = None,
) -> ReasoningTrace:
    """
    Create a hybrid reasoning trace.

    Args:
        steps: List of strings or dicts (dicts will be converted to ReasoningStep)
        method: Confidence computation method
        critical_steps: Critical path step numbers

    Returns:
        ReasoningTrace with computed overall confidence
    """
    processed_steps = []
    detailed_steps = []

    for i, step in enumerate(steps):
        if isinstance(step, str):
            processed_steps.append(step)
        elif isinstance(step, dict):
            step_obj = ReasoningStep(step=i + 1, **step)
            processed_steps.append(step_obj)
            detailed_steps.append(step_obj)
        else:
            processed_steps.append(step)
            if isinstance(step, ReasoningStep):
                detailed_steps.append(step)

    # Compute overall confidence
    if detailed_steps:
        if method == "weakest_critical_link":
            if critical_steps:
                critical = [s for s in detailed_steps if s.step in critical_steps]
                overall = min(s.confidence for s in critical) if critical else 1.0
            else:
                overall = min(s.confidence for s in detailed_steps)
        else:
            overall = sum(s.confidence for s in detailed_steps) / len(detailed_steps)
    else:
        overall = 1.0

    methodology = ConfidenceMethodology(
        method=method,
        critical_path_steps=critical_steps,
        explanation=f"Computed using {method} method",
    )

    return ReasoningTrace(
        reasoning_steps=processed_steps,
        overall_confidence=overall,
        confidence_methodology=methodology,
    )
