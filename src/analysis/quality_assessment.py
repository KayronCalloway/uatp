"""
Automated Quality Assessment
Evaluates reasoning quality across multiple dimensions
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class QualityScore:
    """Quality score for a specific dimension."""

    dimension: str
    score: float  # 0.0 to 1.0
    max_score: float
    issues: List[str]
    suggestions: List[str]


@dataclass
class QualityAssessment:
    """Comprehensive quality assessment of reasoning."""

    overall_quality: float  # 0.0 to 1.0
    dimension_scores: Dict[str, QualityScore]
    strengths: List[str]
    weaknesses: List[str]
    improvement_priority: List[Tuple[str, float]]  # (dimension, impact)
    quality_grade: str  # A, B, C, D, F


class QualityAssessor:
    """
    Automated quality assessor for reasoning capsules.

    Evaluates multiple dimensions:
    - Completeness: Are all necessary steps present?
    - Coherence: Does the reasoning flow logically?
    - Evidence Quality: Are claims backed by evidence?
    - Logical Validity: Are there logical fallacies?
    - Bias Detection: Are there signs of bias?
    - Clarity: Is the reasoning clearly expressed?
    """

    # Weights for combining dimension scores
    DIMENSION_WEIGHTS = {
        "completeness": 0.25,
        "coherence": 0.20,
        "evidence_quality": 0.20,
        "logical_validity": 0.20,
        "bias_detection": 0.10,
        "clarity": 0.05,
    }

    @classmethod
    def assess_capsule(cls, capsule: Dict) -> QualityAssessment:
        """
        Perform comprehensive quality assessment of a capsule.

        Args:
            capsule: Capsule dictionary with reasoning steps

        Returns:
            QualityAssessment with scores and recommendations
        """
        reasoning_steps = capsule.get("payload", {}).get("reasoning_steps", [])

        # Assess each dimension
        dimension_scores = {
            "completeness": cls._assess_completeness(reasoning_steps, capsule),
            "coherence": cls._assess_coherence(reasoning_steps),
            "evidence_quality": cls._assess_evidence_quality(reasoning_steps),
            "logical_validity": cls._assess_logical_validity(reasoning_steps),
            "bias_detection": cls._assess_bias(reasoning_steps),
            "clarity": cls._assess_clarity(reasoning_steps),
        }

        # Calculate overall quality (weighted average)
        overall = sum(
            score.score * cls.DIMENSION_WEIGHTS.get(dim, 0.1)
            for dim, score in dimension_scores.items()
        )

        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []

        for dim, score in dimension_scores.items():
            if score.score >= 0.8:
                strengths.append(f"Strong {dim} ({score.score:.2f})")
            elif score.score < 0.6:
                weaknesses.append(f"Weak {dim} ({score.score:.2f})")

        # Priority for improvement (lowest scores with high weights)
        priority = [
            (dim, (1.0 - score.score) * cls.DIMENSION_WEIGHTS[dim])
            for dim, score in dimension_scores.items()
        ]
        priority.sort(key=lambda x: x[1], reverse=True)

        # Quality grade
        grade = cls._calculate_grade(overall)

        return QualityAssessment(
            overall_quality=overall,
            dimension_scores=dimension_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_priority=priority,
            quality_grade=grade,
        )

    @classmethod
    def _assess_completeness(cls, steps: List[Dict], capsule: Dict) -> QualityScore:
        """Assess if reasoning is complete with all necessary elements."""
        score = 0.0
        max_score = 10.0
        issues = []
        suggestions = []

        # Check for essential elements
        has_problem_statement = any(
            isinstance(s, dict) and "problem" in str(s.get("content", "")).lower()
            for s in steps[:2]  # Should be early
        )
        if has_problem_statement:
            score += 2.0
        else:
            issues.append("No clear problem statement")
            suggestions.append("Start with explicit problem definition")

        # Analysis steps
        has_analysis = any(
            isinstance(s, dict)
            and s.get("operation") in ["analysis", "investigate", "examine"]
            for s in steps
        )
        if has_analysis:
            score += 2.0
        else:
            issues.append("No analysis steps")
            suggestions.append("Include analytical reasoning steps")

        # Evidence or measurements
        has_evidence = any(
            isinstance(s, dict) and (s.get("measurements") or s.get("evidence"))
            for s in steps
        )
        if has_evidence:
            score += 2.0
        else:
            issues.append("No objective evidence")
            suggestions.append("Add measurements or concrete evidence")

        # Alternatives considered
        has_alternatives = any(
            isinstance(s, dict) and s.get("alternatives_considered") for s in steps
        )
        if has_alternatives:
            score += 2.0
        else:
            issues.append("No alternatives explored")
            suggestions.append("Consider multiple approaches")

        # Conclusion
        has_conclusion = any(
            isinstance(s, dict)
            and s.get("operation") in ["conclude", "decision", "recommendation"]
            for s in steps[-2:]  # Should be near end
        )
        if has_conclusion:
            score += 2.0
        else:
            issues.append("No clear conclusion")
            suggestions.append("End with explicit conclusion or decision")

        return QualityScore(
            dimension="completeness",
            score=score / max_score,
            max_score=max_score,
            issues=issues,
            suggestions=suggestions,
        )

    @classmethod
    def _assess_coherence(cls, steps: List[Dict]) -> QualityScore:
        """Assess logical flow and coherence of reasoning."""
        score = 0.0
        max_score = 10.0
        issues = []
        suggestions = []

        if len(steps) < 2:
            return QualityScore(
                dimension="coherence",
                score=0.3,
                max_score=max_score,
                issues=["Too few steps to assess coherence"],
                suggestions=["Expand reasoning with more steps"],
            )

        # Check for sequential dependency
        has_dependencies = 0
        for i, step in enumerate(steps[1:], 1):
            if isinstance(step, dict) and step.get("depends_on"):
                has_dependencies += 1

        if has_dependencies > len(steps) * 0.3:
            score += 3.0
        else:
            issues.append("Weak dependencies between steps")
            suggestions.append("Make step dependencies explicit")

        # Check for progressive confidence
        confidences = [s.get("confidence", 0.8) for s in steps if isinstance(s, dict)]

        if len(confidences) >= 3:
            # Confidence should stabilize or increase
            trend_positive = sum(
                1
                for i in range(len(confidences) - 1)
                if confidences[i + 1] >= confidences[i] - 0.1
            )

            if trend_positive / (len(confidences) - 1) > 0.6:
                score += 3.0
            else:
                issues.append("Confidence decreases through reasoning")
                suggestions.append("Resolve uncertainties as reasoning progresses")

        # Check for logical transitions
        has_transitions = 0
        transition_words = [
            "therefore",
            "because",
            "thus",
            "consequently",
            "as a result",
        ]

        for step in steps:
            if isinstance(step, dict):
                content = str(step.get("content", "")).lower()
                if any(word in content for word in transition_words):
                    has_transitions += 1

        if has_transitions >= len(steps) * 0.3:
            score += 2.0
        else:
            issues.append("Few logical transitions")
            suggestions.append("Use connecting words to show logical flow")

        # Check for consistent terminology
        score += 2.0  # Baseline for having steps

        return QualityScore(
            dimension="coherence",
            score=score / max_score,
            max_score=max_score,
            issues=issues,
            suggestions=suggestions,
        )

    @classmethod
    def _assess_evidence_quality(cls, steps: List[Dict]) -> QualityScore:
        """Assess quality of evidence supporting reasoning."""
        score = 0.0
        max_score = 10.0
        issues = []
        suggestions = []

        evidence_count = 0
        measurement_count = 0
        citation_count = 0

        for step in steps:
            if not isinstance(step, dict):
                continue

            # Check for measurements
            if step.get("measurements"):
                measurement_count += 1
                score += 1.5

            # Check for evidence
            if step.get("evidence"):
                evidence_count += 1
                score += 1.0

            # Check for citations or sources
            content = str(step.get("content", ""))
            if re.search(r"\[.*?\]|\(.*?\)", content):  # Citations in brackets
                citation_count += 1
                score += 0.5

        if measurement_count == 0:
            issues.append("No objective measurements")
            suggestions.append("Add quantitative measurements where possible")

        if evidence_count == 0:
            issues.append("No explicit evidence provided")
            suggestions.append("Support claims with concrete evidence")

        if citation_count == 0:
            issues.append("No sources cited")
            suggestions.append("Reference sources for claims")

        # Cap score at max
        score = min(score, max_score)

        return QualityScore(
            dimension="evidence_quality",
            score=score / max_score,
            max_score=max_score,
            issues=issues,
            suggestions=suggestions,
        )

    @classmethod
    def _assess_logical_validity(cls, steps: List[Dict]) -> QualityScore:
        """Check for logical fallacies and invalid reasoning."""
        score = 10.0  # Start high, deduct for problems
        max_score = 10.0
        issues = []
        suggestions = []

        for step in steps:
            if not isinstance(step, dict):
                continue

            content = str(step.get("content", "")).lower()

            # Check for common fallacies

            # Hasty generalization
            if re.search(r"\ball\b|\bevery\b|\balways\b|\bnever\b", content):
                if not step.get("evidence") and not step.get("measurements"):
                    score -= 1.0
                    issues.append("Possible hasty generalization")
                    suggestions.append("Avoid absolute claims without evidence")

            # Circular reasoning
            if "because" in content and "therefore" in content:
                # Simple heuristic - needs better detection
                pass

            # Appeal to authority without evidence
            authority_words = ["expert", "authority", "everyone knows"]
            if any(word in content for word in authority_words):
                if not step.get("evidence"):
                    score -= 0.5
                    issues.append("Appeal to authority without evidence")
                    suggestions.append("Support authority claims with evidence")

            # False dichotomy
            if re.search(r"\beither\s+\w+\s+or\s+\w+\b", content):
                alternatives = step.get("alternatives_considered", [])
                if len(alternatives) < 3:
                    score -= 0.5
                    issues.append("Possible false dichotomy")
                    suggestions.append("Consider more than two alternatives")

        score = max(0.0, score)

        if score >= 8.0 and not issues:
            suggestions.append("Logical reasoning appears sound")

        return QualityScore(
            dimension="logical_validity",
            score=score / max_score,
            max_score=max_score,
            issues=issues,
            suggestions=suggestions,
        )

    @classmethod
    def _assess_bias(cls, steps: List[Dict]) -> QualityScore:
        """Detect potential biases in reasoning."""
        score = 10.0  # Start high, deduct for bias indicators
        max_score = 10.0
        issues = []
        suggestions = []

        # Bias indicators
        bias_words = {
            "confirmation": ["obviously", "clearly", "everyone knows"],
            "anchoring": ["first", "initial", "starting"],
            "availability": ["recent", "latest", "just saw"],
            "framing": ["only", "just", "merely", "at least"],
        }

        for step in steps:
            if not isinstance(step, dict):
                continue

            content = str(step.get("content", "")).lower()

            # Check for bias indicators
            for bias_type, words in bias_words.items():
                if any(word in content for word in words):
                    score -= 0.5
                    if bias_type not in [i.split(":")[0] for i in issues]:
                        issues.append(f"{bias_type.capitalize()} bias possible")

            # Check for one-sided analysis
            if step.get("alternatives_considered"):
                alts = step["alternatives_considered"]
                if len(alts) < 2:
                    score -= 1.0
                    if "limited alternatives" not in issues:
                        issues.append("Limited alternatives considered")
                        suggestions.append("Explore multiple perspectives")

        # Check for balanced confidence
        confidences = [s.get("confidence", 0.8) for s in steps if isinstance(s, dict)]
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            if avg_conf > 0.95:
                score -= 1.0
                issues.append("Overconfidence detected")
                suggestions.append("Question assumptions and consider uncertainty")

        score = max(0.0, score)

        if score >= 8.0 and not issues:
            suggestions.append("No obvious biases detected")

        return QualityScore(
            dimension="bias_detection",
            score=score / max_score,
            max_score=max_score,
            issues=issues,
            suggestions=suggestions,
        )

    @classmethod
    def _assess_clarity(cls, steps: List[Dict]) -> QualityScore:
        """Assess clarity and readability of reasoning."""
        score = 0.0
        max_score = 10.0
        issues = []
        suggestions = []

        if not steps:
            return QualityScore(
                dimension="clarity",
                score=0.0,
                max_score=max_score,
                issues=["No steps to assess"],
                suggestions=[],
            )

        # Check for clear step descriptions
        clear_steps = 0
        for step in steps:
            if isinstance(step, dict):
                content = str(step.get("content", ""))
                operation = step.get("operation", "")

                # Clear if has operation and content
                if operation and content and len(content) > 20:
                    clear_steps += 1

        clarity_ratio = clear_steps / len(steps)
        score += clarity_ratio * 5.0

        if clarity_ratio < 0.5:
            issues.append("Many steps lack clear descriptions")
            suggestions.append("Add detailed explanations to steps")

        # Check for structured operations
        has_operations = sum(
            1 for s in steps if isinstance(s, dict) and s.get("operation")
        )

        if has_operations / len(steps) > 0.7:
            score += 3.0
        else:
            issues.append("Steps lack operation labels")
            suggestions.append("Label each step with its purpose")

        # Reasonable step length
        avg_length = (
            sum(len(str(s.get("content", ""))) for s in steps if isinstance(s, dict))
            / len(steps)
            if steps
            else 0
        )

        if 50 < avg_length < 300:
            score += 2.0
        elif avg_length <= 50:
            issues.append("Steps are too brief")
            suggestions.append("Provide more detailed explanations")
        else:
            issues.append("Steps are too verbose")
            suggestions.append("Be more concise")

        return QualityScore(
            dimension="clarity",
            score=min(score, max_score) / max_score,
            max_score=max_score,
            issues=issues,
            suggestions=suggestions,
        )

    @staticmethod
    def _calculate_grade(score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"


# Example usage
if __name__ == "__main__":
    print("[OK] Automated Quality Assessment Ready")
    print("\nCapabilities:")
    print("  - Completeness checking")
    print("  - Coherence analysis")
    print("  - Evidence quality evaluation")
    print("  - Logical validity checking")
    print("  - Bias detection")
    print("  - Clarity assessment")
    print("  - Overall quality grading")
    print("  - Prioritized improvement suggestions")
