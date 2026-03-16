"""
validator.py - Reasoning trace validation for UATP Capsule Engine.

This module provides validation capabilities for reasoning traces to ensure
they meet quality standards for completeness, coherence, and structure.
"""

from typing import Any, Dict

from .trace import ReasoningTrace, StepType


class ValidationResult:
    """Result of a reasoning trace validation."""

    def __init__(self):
        self.is_valid = True
        self.score = 0.0
        self.issues = []
        self.suggestions = []

    def add_issue(self, issue: str, severity: str = "warning"):
        """Add an issue to the validation result."""
        self.issues.append({"message": issue, "severity": severity})
        if severity == "error":
            self.is_valid = False

    def add_suggestion(self, suggestion: str):
        """Add a suggestion to the validation result."""
        self.suggestions.append(suggestion)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "score": self.score,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }


class ReasoningValidator:
    """
    Validates reasoning traces against quality criteria.
    """

    @staticmethod
    def validate(trace: ReasoningTrace) -> ValidationResult:
        """
        Validate a reasoning trace against multiple criteria.

        Args:
            trace: The reasoning trace to validate

        Returns:
            ValidationResult object with validation details
        """
        result = ValidationResult()

        # Run all validation checks
        ReasoningValidator._validate_completeness(trace, result)
        ReasoningValidator._validate_coherence(trace, result)
        ReasoningValidator._validate_confidence(trace, result)
        ReasoningValidator._validate_structure(trace, result)

        # Calculate overall score (0-100)
        result.score = ReasoningValidator._calculate_score(trace, result)

        return result

    @staticmethod
    def _validate_completeness(trace: ReasoningTrace, result: ValidationResult) -> None:
        """Check if the trace is complete with necessary step types."""
        # Check minimum length
        if len(trace) < 3:
            result.add_issue(
                "Reasoning trace is too short (less than 3 steps)", "warning"
            )
            result.add_suggestion("Expand the reasoning trace with more detailed steps")

        # Check for conclusion
        if not trace.has_conclusion():
            result.add_issue("Reasoning trace lacks a conclusion step", "warning")
            result.add_suggestion("Add a conclusion step to summarize the reasoning")

        # Check for variety of step types
        step_types = trace.get_step_types()
        if len([t for t, count in step_types.items() if count > 0]) < 3:
            result.add_issue("Reasoning trace uses limited step types", "warning")
            result.add_suggestion(
                "Use a variety of step types for more comprehensive reasoning"
            )

    @staticmethod
    def _validate_coherence(trace: ReasoningTrace, result: ValidationResult) -> None:
        """Check if the trace is coherent and logical."""
        # This is a simplified check - in a real system, this would use more sophisticated
        # NLP techniques to analyze coherence between steps

        # Check for abrupt shifts in reasoning
        for i in range(1, len(trace)):
            prev_step = trace[i - 1]
            curr_step = trace[i]

            # Check for logical flow between certain step types
            if (
                prev_step.step_type == StepType.HYPOTHESIS
                and curr_step.step_type == StepType.CONCLUSION
            ):
                # Hypothesis should be followed by evidence before conclusion
                if i == 1 or trace[i - 2].step_type != StepType.EVIDENCE:
                    result.add_issue(
                        f"Step {i + 1}: Conclusion follows hypothesis without supporting evidence",
                        "warning",
                    )
                    result.add_suggestion(
                        "Add evidence steps between hypothesis and conclusion"
                    )

    @staticmethod
    def _validate_confidence(trace: ReasoningTrace, result: ValidationResult) -> None:
        """Check if confidence values are reasonable and consistent."""
        # Check for unreasonably high confidence
        high_confidence_steps = [
            i
            for i, step in enumerate(trace)
            if step.confidence > 0.95
            and step.step_type in (StepType.INFERENCE, StepType.HYPOTHESIS)
        ]

        if high_confidence_steps:
            step_indices = ", ".join(str(i + 1) for i in high_confidence_steps)
            result.add_issue(
                f"Unreasonably high confidence in inference/hypothesis steps: {step_indices}",
                "warning",
            )
            result.add_suggestion(
                "Consider reducing confidence for speculative reasoning steps"
            )

        # Check for low confidence conclusion
        conclusion_steps = trace.get_conclusion_steps()
        if conclusion_steps and any(step.confidence < 0.7 for step in conclusion_steps):
            result.add_issue("Low confidence conclusion detected", "warning")
            result.add_suggestion(
                "Either increase confidence in conclusion or add more supporting evidence"
            )

    @staticmethod
    def _validate_structure(trace: ReasoningTrace, result: ValidationResult) -> None:
        """Check if the trace has a logical structure."""
        # Check if conclusion appears too early
        for i, step in enumerate(trace):
            if (
                step.step_type == StepType.CONCLUSION
                and i < len(trace) // 2
                and len(trace) > 3
            ):
                result.add_issue(
                    f"Conclusion appears too early in reasoning (step {i + 1})",
                    "warning",
                )
                result.add_suggestion(
                    "Move conclusion steps toward the end of the reasoning trace"
                )

        # Check for reflection steps
        has_reflection = any(step.step_type == StepType.REFLECTION for step in trace)
        if len(trace) > 5 and not has_reflection:
            result.add_suggestion(
                "Consider adding reflection steps for more thorough reasoning"
            )

    @staticmethod
    def _calculate_score(trace: ReasoningTrace, result: ValidationResult) -> float:
        """Calculate an overall quality score for the reasoning trace."""
        # Base score
        score = 60.0

        # Length bonus (up to +10)
        length_bonus = min(10, len(trace) * 2)
        score += length_bonus

        # Step type variety bonus (up to +10)
        step_types = trace.get_step_types()
        variety_count = len([t for t, count in step_types.items() if count > 0])
        variety_bonus = min(10, variety_count * 2)
        score += variety_bonus

        # Structure bonus (up to +10)
        structure_bonus = 0
        if trace.has_conclusion():
            structure_bonus += 5
        if any(step.step_type == StepType.REFLECTION for step in trace):
            structure_bonus += 5
        score += structure_bonus

        # Confidence consistency (up to +10)
        avg_confidence = trace.get_average_confidence()
        if 0.6 <= avg_confidence <= 0.9:  # Reasonable confidence range
            confidence_bonus = 10
        else:
            confidence_bonus = 0
        score += confidence_bonus

        # Penalty for issues
        error_count = len([i for i in result.issues if i["severity"] == "error"])
        warning_count = len([i for i in result.issues if i["severity"] == "warning"])

        score -= error_count * 15
        score -= warning_count * 5

        # Ensure score is in range 0-100
        return max(0, min(100, score))
