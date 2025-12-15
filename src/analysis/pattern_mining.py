"""
Pattern Mining System
Discovers effective reasoning patterns across capsules for learning and reuse
"""

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ReasoningPattern:
    """A discovered reasoning pattern."""

    pattern_id: str
    pattern_type: str  # sequence, decision_tree, failure_mode, success_strategy
    pattern_name: str
    pattern_description: str
    pattern_structure: Dict[str, Any]

    success_rate: float
    usage_count: int
    applicable_domains: List[str]
    example_capsule_ids: List[str]

    confidence_impact: Optional[float] = (
        None  # How much this pattern affects confidence
    )


class PatternMiner:
    """Mines reasoning patterns from capsules."""

    # Minimum occurrences to consider a pattern
    MIN_PATTERN_OCCURRENCES = 3

    # Minimum success rate to consider a pattern valuable
    MIN_SUCCESS_RATE = 0.6

    @staticmethod
    def extract_step_sequence(capsule: Dict) -> List[str]:
        """
        Extract a sequence of operations from reasoning steps.

        Args:
            capsule: Capsule with reasoning_steps

        Returns:
            List of operation types in sequence
        """
        if "reasoning_steps" not in capsule.get("payload", {}):
            return []

        steps = capsule["payload"]["reasoning_steps"]

        sequence = []
        for step in steps:
            if isinstance(step, dict):
                operation = step.get("operation", "unknown")
                sequence.append(operation)
            elif isinstance(step, str):
                # Simple string step - classify based on keywords
                sequence.append("reasoning")

        return sequence

    @staticmethod
    def generate_pattern_id(pattern_structure: Dict) -> str:
        """Generate a unique ID for a pattern based on its structure."""
        pattern_str = json.dumps(pattern_structure, sort_keys=True)
        return hashlib.sha256(pattern_str.encode()).hexdigest()[:16]

    @classmethod
    def mine_sequence_patterns(
        cls,
        capsules_with_outcomes: List[Dict],
        min_length: int = 2,
        max_length: int = 5,
    ) -> List[ReasoningPattern]:
        """
        Mine common reasoning step sequences.

        Finds patterns like: [analysis -> measurement -> decision]

        Args:
            capsules_with_outcomes: Capsules with outcome data
            min_length: Minimum sequence length
            max_length: Maximum sequence length

        Returns:
            List of discovered sequence patterns
        """
        # Extract all sequences
        sequences_with_outcomes = []

        for capsule_data in capsules_with_outcomes:
            capsule = capsule_data.get("capsule", {})
            outcome_success = capsule_data.get("outcome_success", False)

            sequence = cls.extract_step_sequence(capsule)
            if len(sequence) >= min_length:
                sequences_with_outcomes.append(
                    {
                        "sequence": sequence,
                        "success": outcome_success,
                        "capsule_id": capsule.get("capsule_id", "unknown"),
                        "domain": capsule_data.get("domain", "general"),
                    }
                )

        # Find all subsequences
        pattern_occurrences = defaultdict(
            lambda: {"capsules": [], "successes": 0, "total": 0, "domains": Counter()}
        )

        for item in sequences_with_outcomes:
            sequence = item["sequence"]

            # Generate all subsequences of length min_length to max_length
            for length in range(min_length, min(len(sequence) + 1, max_length + 1)):
                for i in range(len(sequence) - length + 1):
                    subseq = tuple(sequence[i : i + length])

                    pattern_occurrences[subseq]["capsules"].append(item["capsule_id"])
                    pattern_occurrences[subseq]["total"] += 1
                    pattern_occurrences[subseq]["domains"][item["domain"]] += 1

                    if item["success"]:
                        pattern_occurrences[subseq]["successes"] += 1

        # Filter and create patterns
        patterns = []

        for sequence, data in pattern_occurrences.items():
            if data["total"] < cls.MIN_PATTERN_OCCURRENCES:
                continue

            success_rate = data["successes"] / data["total"]

            if success_rate < cls.MIN_SUCCESS_RATE:
                continue  # Only keep successful patterns

            pattern_structure = {"sequence": list(sequence), "length": len(sequence)}

            pattern_id = cls.generate_pattern_id(pattern_structure)

            # Generate pattern name
            pattern_name = " → ".join(sequence)

            # Generate description
            pattern_description = f"Reasoning sequence with {success_rate:.1%} success rate across {data['total']} uses"

            # Get top domains
            top_domains = [domain for domain, _ in data["domains"].most_common(3)]

            patterns.append(
                ReasoningPattern(
                    pattern_id=pattern_id,
                    pattern_type="sequence",
                    pattern_name=pattern_name,
                    pattern_description=pattern_description,
                    pattern_structure=pattern_structure,
                    success_rate=success_rate,
                    usage_count=data["total"],
                    applicable_domains=top_domains,
                    example_capsule_ids=data["capsules"][:5],
                    confidence_impact=cls._estimate_confidence_impact(success_rate),
                )
            )

        # Sort by success rate
        patterns.sort(key=lambda p: p.success_rate, reverse=True)

        return patterns

    @classmethod
    def mine_decision_patterns(
        cls, capsules_with_outcomes: List[Dict]
    ) -> List[ReasoningPattern]:
        """
        Mine effective decision-making patterns.

        Finds patterns where alternatives were considered and one was chosen successfully.

        Args:
            capsules_with_outcomes: Capsules with outcome data

        Returns:
            List of discovered decision patterns
        """
        decision_patterns = defaultdict(
            lambda: {"capsules": [], "successes": 0, "total": 0, "domains": Counter()}
        )

        for capsule_data in capsules_with_outcomes:
            capsule = capsule_data.get("capsule", {})
            outcome_success = capsule_data.get("outcome_success", False)

            steps = capsule.get("payload", {}).get("reasoning_steps", [])

            for step in steps:
                if not isinstance(step, dict):
                    continue

                # Look for steps with alternatives
                if (
                    step.get("alternatives_considered")
                    and len(step.get("alternatives_considered", [])) > 1
                ):
                    operation = step.get("operation", "decision")
                    num_alternatives = len(step["alternatives_considered"])

                    pattern_key = (operation, num_alternatives)

                    decision_patterns[pattern_key]["capsules"].append(
                        capsule.get("capsule_id", "unknown")
                    )
                    decision_patterns[pattern_key]["total"] += 1
                    decision_patterns[pattern_key]["domains"][
                        capsule_data.get("domain", "general")
                    ] += 1

                    if outcome_success:
                        decision_patterns[pattern_key]["successes"] += 1

        # Create patterns
        patterns = []

        for (operation, num_alternatives), data in decision_patterns.items():
            if data["total"] < cls.MIN_PATTERN_OCCURRENCES:
                continue

            success_rate = data["successes"] / data["total"]

            if success_rate < cls.MIN_SUCCESS_RATE:
                continue

            pattern_structure = {
                "decision_operation": operation,
                "alternatives_evaluated": num_alternatives,
            }

            pattern_id = cls.generate_pattern_id(pattern_structure)

            pattern_name = (
                f"{operation.capitalize()} with {num_alternatives} alternatives"
            )
            pattern_description = f"Decision pattern evaluating {num_alternatives} options with {success_rate:.1%} success rate"

            top_domains = [domain for domain, _ in data["domains"].most_common(3)]

            patterns.append(
                ReasoningPattern(
                    pattern_id=pattern_id,
                    pattern_type="decision_tree",
                    pattern_name=pattern_name,
                    pattern_description=pattern_description,
                    pattern_structure=pattern_structure,
                    success_rate=success_rate,
                    usage_count=data["total"],
                    applicable_domains=top_domains,
                    example_capsule_ids=data["capsules"][:5],
                    confidence_impact=cls._estimate_confidence_impact(success_rate),
                )
            )

        patterns.sort(key=lambda p: p.success_rate, reverse=True)

        return patterns

    @classmethod
    def mine_failure_modes(
        cls, capsules_with_outcomes: List[Dict]
    ) -> List[ReasoningPattern]:
        """
        Identify common failure patterns to avoid.

        Args:
            capsules_with_outcomes: Capsules with outcome data

        Returns:
            List of failure mode patterns
        """
        failure_patterns = defaultdict(
            lambda: {"capsules": [], "failures": 0, "total": 0, "domains": Counter()}
        )

        for capsule_data in capsules_with_outcomes:
            capsule = capsule_data.get("capsule", {})
            outcome_success = capsule_data.get("outcome_success", False)

            steps = capsule.get("payload", {}).get("reasoning_steps", [])

            # Look for problematic patterns
            for step in steps:
                if not isinstance(step, dict):
                    continue

                # Pattern: Low confidence + uncertainty sources
                if step.get("confidence", 1.0) < 0.7 and step.get(
                    "uncertainty_sources"
                ):
                    num_uncertainties = len(step.get("uncertainty_sources", []))
                    pattern_key = ("low_confidence_uncertain", num_uncertainties)

                    failure_patterns[pattern_key]["capsules"].append(
                        capsule.get("capsule_id", "unknown")
                    )
                    failure_patterns[pattern_key]["total"] += 1
                    failure_patterns[pattern_key]["domains"][
                        capsule_data.get("domain", "general")
                    ] += 1

                    if not outcome_success:
                        failure_patterns[pattern_key]["failures"] += 1

                # Pattern: No alternatives considered in decision
                if step.get("operation") == "decision" and not step.get(
                    "alternatives_considered"
                ):
                    pattern_key = ("decision_no_alternatives", 0)

                    failure_patterns[pattern_key]["capsules"].append(
                        capsule.get("capsule_id", "unknown")
                    )
                    failure_patterns[pattern_key]["total"] += 1
                    failure_patterns[pattern_key]["domains"][
                        capsule_data.get("domain", "general")
                    ] += 1

                    if not outcome_success:
                        failure_patterns[pattern_key]["failures"] += 1

        # Create failure patterns
        patterns = []

        for (failure_type, param), data in failure_patterns.items():
            if data["total"] < cls.MIN_PATTERN_OCCURRENCES:
                continue

            failure_rate = data["failures"] / data["total"]

            if failure_rate < 0.4:  # Only include patterns that fail frequently
                continue

            pattern_structure = {"failure_type": failure_type, "parameter": param}

            pattern_id = cls.generate_pattern_id(pattern_structure)

            if failure_type == "low_confidence_uncertain":
                pattern_name = f"Low confidence with {param} uncertainty sources"
                pattern_description = f"Failure mode: {failure_rate:.1%} failure rate when confidence < 0.7 and {param} uncertainties present"
            elif failure_type == "decision_no_alternatives":
                pattern_name = "Decision without alternatives"
                pattern_description = f"Failure mode: {failure_rate:.1%} failure rate when decisions lack alternative evaluation"
            else:
                pattern_name = f"Failure mode: {failure_type}"
                pattern_description = f"Failure rate: {failure_rate:.1%}"

            top_domains = [domain for domain, _ in data["domains"].most_common(3)]

            patterns.append(
                ReasoningPattern(
                    pattern_id=pattern_id,
                    pattern_type="failure_mode",
                    pattern_name=pattern_name,
                    pattern_description=pattern_description,
                    pattern_structure=pattern_structure,
                    success_rate=1.0 - failure_rate,  # Inverse for failure patterns
                    usage_count=data["total"],
                    applicable_domains=top_domains,
                    example_capsule_ids=data["capsules"][:5],
                    confidence_impact=-0.1,  # Negative impact for failure modes
                )
            )

        patterns.sort(key=lambda p: p.success_rate)  # Worst first for failure modes

        return patterns

    @staticmethod
    def _estimate_confidence_impact(success_rate: float) -> float:
        """
        Estimate how much a pattern should affect confidence.

        Args:
            success_rate: Success rate of pattern

        Returns:
            Confidence adjustment (+/- value)
        """
        # Map success rate to confidence impact
        if success_rate >= 0.9:
            return 0.05  # Strong positive pattern
        elif success_rate >= 0.8:
            return 0.03  # Moderate positive pattern
        elif success_rate >= 0.7:
            return 0.01  # Weak positive pattern
        elif success_rate >= 0.5:
            return 0.0  # Neutral
        else:
            return -0.03  # Negative pattern

    @classmethod
    def mine_all_patterns(
        cls, capsules_with_outcomes: List[Dict]
    ) -> Dict[str, List[ReasoningPattern]]:
        """
        Mine all pattern types in one pass.

        Args:
            capsules_with_outcomes: Capsules with outcome data

        Returns:
            Dict mapping pattern_type -> list of patterns
        """
        return {
            "sequence": cls.mine_sequence_patterns(capsules_with_outcomes),
            "decision_tree": cls.mine_decision_patterns(capsules_with_outcomes),
            "failure_mode": cls.mine_failure_modes(capsules_with_outcomes),
        }

    @staticmethod
    def match_pattern_to_capsule(
        capsule: Dict, patterns: List[ReasoningPattern]
    ) -> List[Tuple[ReasoningPattern, float]]:
        """
        Find which patterns match a given capsule.

        Args:
            capsule: Capsule to match
            patterns: List of patterns to check

        Returns:
            List of (pattern, match_score) tuples sorted by score
        """
        matches = []

        sequence = PatternMiner.extract_step_sequence(capsule)

        for pattern in patterns:
            match_score = 0.0

            if pattern.pattern_type == "sequence":
                # Check if pattern sequence is a subsequence of capsule sequence
                pattern_seq = pattern.pattern_structure.get("sequence", [])
                if cls._is_subsequence(pattern_seq, sequence):
                    match_score = 1.0

            elif pattern.pattern_type == "decision_tree":
                # Check if capsule has similar decision structures
                expected_alternatives = pattern.pattern_structure.get(
                    "alternatives_evaluated", 0
                )
                steps = capsule.get("payload", {}).get("reasoning_steps", [])

                for step in steps:
                    if isinstance(step, dict):
                        actual_alternatives = len(
                            step.get("alternatives_considered", [])
                        )
                        if actual_alternatives == expected_alternatives:
                            match_score = 1.0
                            break

            if match_score > 0:
                matches.append((pattern, match_score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    @staticmethod
    def _is_subsequence(pattern: List, sequence: List) -> bool:
        """Check if pattern is a subsequence of sequence."""
        if not pattern:
            return True

        pattern_idx = 0
        for item in sequence:
            if item == pattern[pattern_idx]:
                pattern_idx += 1
                if pattern_idx == len(pattern):
                    return True

        return False


# Example usage
if __name__ == "__main__":
    print("✅ Pattern Mining System Ready")
    print("\nCapabilities:")
    print("  - Mine reasoning step sequences")
    print("  - Discover decision-making patterns")
    print("  - Identify failure modes to avoid")
    print("  - Match patterns to new capsules")
    print("  - Estimate confidence impact of patterns")
