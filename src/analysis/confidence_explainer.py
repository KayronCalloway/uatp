"""
Confidence Explanation System
Makes confidence scores interpretable by explaining what contributed to them
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConfidenceExplanation:
    """Detailed explanation of a confidence score."""

    confidence: float
    confidence_factors: Dict[str, float] = field(default_factory=dict)
    boosting_factors: List[str] = field(default_factory=list)
    limiting_factors: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    factor_breakdown: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "confidence": round(self.confidence, 3),
            "confidence_factors": {
                k: round(v, 3) for k, v in self.confidence_factors.items()
            },
            "boosting_factors": self.boosting_factors,
            "limiting_factors": self.limiting_factors,
            "improvement_suggestions": self.improvement_suggestions,
        }


class ConfidenceExplainer:
    """Explains confidence scores and suggests improvements."""

    @staticmethod
    def explain_message_confidence(
        role: str,
        content_length: int,
        token_count: Optional[int],
        has_code: bool = False,
        has_questions: bool = False,
        uncertainty_language: Optional[List[str]] = None,
    ) -> ConfidenceExplanation:
        """
        Calculate confidence AND provide detailed explanation.

        Args:
            role: Message role (user/assistant)
            content_length: Length of content in characters
            token_count: Number of tokens (if available)
            has_code: Whether code is included
            has_questions: Whether clarifying questions are present
            uncertainty_language: Detected uncertainty phrases

        Returns:
            ConfidenceExplanation with full breakdown
        """
        # Start with base confidence
        base_confidence = 0.85 if role == "assistant" else 0.70
        confidence = base_confidence

        factors = {"base": base_confidence}
        boosting = []
        limiting = []
        suggestions = []

        # Factor 1: Content length
        if content_length > 1000:
            adjustment = 0.05
            confidence += adjustment
            factors["detailed_response"] = adjustment
            boosting.append("Detailed response with thorough explanation")
        elif content_length < 100:
            adjustment = -0.10
            confidence += adjustment
            factors["brief_response"] = adjustment
            limiting.append("Very brief response - may lack important details")
            suggestions.append(
                "Provide more detailed explanation with examples and reasoning"
            )

        # Factor 2: Code presence
        if has_code:
            adjustment = 0.08
            confidence += adjustment
            factors["code_examples"] = adjustment
            boosting.append("Concrete code examples provided for clarity")
        elif role == "assistant":
            suggestions.append(
                "Consider providing code examples to make guidance more concrete"
            )

        # Factor 3: Clarifying questions
        if has_questions:
            adjustment = -0.05
            confidence += adjustment
            factors["clarifying_questions"] = adjustment
            limiting.append("Clarifying questions indicate incomplete information")
            suggestions.append("Gather more context to reduce need for clarification")

        # Factor 4: Token count (substantial content)
        if token_count and token_count > 500:
            adjustment = 0.02
            confidence += adjustment
            factors["substantial_content"] = adjustment
            boosting.append("Substantial content demonstrates thoroughness")

        # Factor 5: Uncertainty language
        if uncertainty_language and len(uncertainty_language) > 0:
            adjustment = -0.03 * len(uncertainty_language)
            adjustment = max(adjustment, -0.15)  # Cap at -0.15
            confidence += adjustment
            factors["uncertainty_language"] = adjustment
            limiting.append(
                f"Uncertainty language detected: {', '.join(uncertainty_language[:2])}"
            )
            suggestions.append(
                "Reduce speculative language by gathering concrete evidence"
            )

        # Factor 6: Response completeness (inferred from length + code)
        if content_length > 500 and has_code:
            adjustment = 0.03
            confidence += adjustment
            factors["complete_response"] = adjustment
            boosting.append(
                "Response appears complete with both explanation and implementation"
            )

        # Clamp confidence to valid range
        confidence = min(1.0, max(0.0, confidence))

        # Generate summary
        factor_breakdown = ConfidenceExplainer._generate_factor_breakdown(factors)

        return ConfidenceExplanation(
            confidence=confidence,
            confidence_factors=factors,
            boosting_factors=boosting,
            limiting_factors=limiting,
            improvement_suggestions=suggestions if limiting else [],
            factor_breakdown=factor_breakdown,
        )

    @staticmethod
    def explain_step_confidence(
        step_confidence: float,
        has_measurements: bool,
        has_alternatives: bool,
        has_dependencies: bool,
        uncertainty_count: int,
        operation_type: str,
    ) -> ConfidenceExplanation:
        """
        Explain confidence for a reasoning step.

        Args:
            step_confidence: The calculated confidence
            has_measurements: Whether measurements are present
            has_alternatives: Whether alternatives were considered
            has_dependencies: Whether step has dependencies
            uncertainty_count: Number of uncertainty sources
            operation_type: Type of operation (analysis, decision, etc.)

        Returns:
            ConfidenceExplanation
        """
        factors = {}
        boosting = []
        limiting = []
        suggestions = []

        # Factor: Measurements
        if has_measurements:
            boosting.append("Backed by concrete measurements")
            factors["measurements_present"] = 0.05
        else:
            suggestions.append("Add quantitative measurements to increase confidence")

        # Factor: Alternatives
        if has_alternatives:
            boosting.append("Multiple alternatives were evaluated")
            factors["alternatives_evaluated"] = 0.03
        elif operation_type == "decision":
            limiting.append("No alternative options documented for this decision")
            suggestions.append("Document alternative approaches that were considered")

        # Factor: Dependencies
        if has_dependencies:
            boosting.append("Builds on previous reasoning steps")
            factors["dependency_chain"] = 0.02

        # Factor: Uncertainty
        if uncertainty_count > 0:
            limiting.append(f"{uncertainty_count} uncertainty source(s) identified")
            factors["uncertainty_present"] = -0.02 * uncertainty_count
            suggestions.append("Address uncertainty sources to strengthen this step")

        # Factor: Operation-specific confidence
        if operation_type == "measurement":
            boosting.append("Measurement-based operation (typically high confidence)")
            factors["measurement_operation"] = 0.05
        elif operation_type == "estimation":
            limiting.append("Estimation-based operation (inherent uncertainty)")
            factors["estimation_operation"] = -0.05

        factor_breakdown = ConfidenceExplainer._generate_factor_breakdown(factors)

        return ConfidenceExplanation(
            confidence=step_confidence,
            confidence_factors=factors,
            boosting_factors=boosting,
            limiting_factors=limiting,
            improvement_suggestions=suggestions,
            factor_breakdown=factor_breakdown,
        )

    @staticmethod
    def explain_overall_confidence(
        overall_confidence: float,
        step_confidences: List[float],
        methodology: str,
        critical_steps: Optional[List[int]] = None,
    ) -> ConfidenceExplanation:
        """
        Explain overall confidence calculation.

        Args:
            overall_confidence: The overall confidence score
            step_confidences: Confidence of each step
            methodology: Method used (weakest_link, weighted_average, etc.)
            critical_steps: Critical path steps (if applicable)

        Returns:
            ConfidenceExplanation
        """
        factors = {}
        boosting = []
        limiting = []
        suggestions = []

        if not step_confidences:
            return ConfidenceExplanation(
                confidence=overall_confidence,
                confidence_factors={},
                boosting_factors=[],
                limiting_factors=["No step-level confidence data available"],
                improvement_suggestions=[],
            )

        # Calculate statistics
        min_conf = min(step_confidences)
        max_conf = max(step_confidences)
        avg_conf = sum(step_confidences) / len(step_confidences)
        variance = sum((c - avg_conf) ** 2 for c in step_confidences) / len(
            step_confidences
        )

        # Methodology explanation
        if methodology == "weakest_critical_link":
            factors["methodology"] = "Based on weakest link in critical path"
            if min_conf < 0.7:
                limiting.append(f"Weakest link has low confidence: {min_conf:.2f}")
                suggestions.append(
                    "Strengthen the weakest link to improve overall confidence"
                )
        elif methodology == "weighted_average":
            factors["methodology"] = "Weighted average of all steps"
            if variance > 0.05:
                limiting.append(
                    "High variance in step confidences indicates inconsistency"
                )
                suggestions.append(
                    "Reduce variance by strengthening lower-confidence steps"
                )

        # Check confidence distribution
        low_confidence_steps = sum(1 for c in step_confidences if c < 0.7)
        if low_confidence_steps > 0:
            limiting.append(
                f"{low_confidence_steps} step(s) have low confidence (<0.7)"
            )
            factors["low_confidence_steps"] = -0.05 * low_confidence_steps

        high_confidence_steps = sum(1 for c in step_confidences if c >= 0.9)
        if high_confidence_steps > len(step_confidences) / 2:
            boosting.append(
                f"{high_confidence_steps} steps have high confidence (≥0.9)"
            )
            factors["high_confidence_steps"] = 0.02

        # Check for consistent high quality
        if min_conf >= 0.8:
            boosting.append("All steps have strong confidence (≥0.8)")
            factors["consistent_quality"] = 0.05

        # Critical path analysis
        if critical_steps:
            factors["critical_path_focused"] = (
                "Confidence based on critical path analysis"
            )
            boosting.append("Focused on steps that actually matter")

        factor_breakdown = ConfidenceExplainer._generate_factor_breakdown(factors)

        return ConfidenceExplanation(
            confidence=overall_confidence,
            confidence_factors=factors,
            boosting_factors=boosting,
            limiting_factors=limiting,
            improvement_suggestions=suggestions,
            factor_breakdown=factor_breakdown,
        )

    @staticmethod
    def _generate_factor_breakdown(factors: Dict[str, Any]) -> str:
        """Generate human-readable factor breakdown."""
        if not factors:
            return "No detailed factor breakdown available"

        parts = []
        for name, value in factors.items():
            if isinstance(value, (int, float)):
                sign = "+" if value >= 0 else ""
                parts.append(f"{name}: {sign}{value:.3f}")
            else:
                parts.append(f"{name}: {value}")

        return " | ".join(parts)

    @staticmethod
    def compare_confidences(
        confidence1: float,
        explanation1: ConfidenceExplanation,
        confidence2: float,
        explanation2: ConfidenceExplanation,
    ) -> Dict[str, Any]:
        """
        Compare two confidence scores and explain the difference.

        Returns:
            Dictionary with comparison analysis
        """
        diff = confidence2 - confidence1
        diff_pct = (diff / confidence1 * 100) if confidence1 > 0 else 0

        analysis = {
            "confidence_difference": round(diff, 3),
            "difference_percentage": round(diff_pct, 1),
            "direction": "improved"
            if diff > 0
            else "decreased"
            if diff < 0
            else "unchanged",
        }

        # Find factors that changed
        factors1_keys = set(explanation1.confidence_factors.keys())
        factors2_keys = set(explanation2.confidence_factors.keys())

        new_factors = factors2_keys - factors1_keys
        removed_factors = factors1_keys - factors2_keys
        changed_factors = {}

        for key in factors1_keys & factors2_keys:
            val1 = explanation1.confidence_factors[key]
            val2 = explanation2.confidence_factors[key]
            if abs(val2 - val1) > 0.01:
                changed_factors[key] = {
                    "before": val1,
                    "after": val2,
                    "change": val2 - val1,
                }

        analysis["new_factors"] = list(new_factors)
        analysis["removed_factors"] = list(removed_factors)
        analysis["changed_factors"] = changed_factors

        return analysis


# Example usage
if __name__ == "__main__":
    print("✅ Confidence Explainer Ready")
    print("\nCapabilities:")
    print("  - Explain message-level confidence")
    print("  - Explain step-level confidence")
    print("  - Explain overall confidence methodology")
    print("  - Generate improvement suggestions")
    print("  - Compare confidence scores")
    print("  - Factor breakdown analysis")
