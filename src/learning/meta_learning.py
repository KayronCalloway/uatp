"""
Meta-Learning System
Learns reasoning strategies from successful capsules and applies them to new problems
"""

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set


@dataclass
class ReasoningStrategy:
    """A learned reasoning strategy."""

    strategy_id: str
    strategy_name: str
    strategy_description: str
    strategy_pattern: Dict[str, Any]  # Pattern structure

    # Performance metrics
    success_rate: float
    usage_count: int
    average_confidence: float
    average_quality_score: float

    # Applicability
    applicable_domains: List[str]
    applicable_problem_types: List[str]
    required_context: List[str]

    # Evidence
    example_capsule_ids: List[str]
    discovered_at: str = ""


@dataclass
class StrategyRecommendation:
    """A recommendation to use a specific strategy."""

    strategy: ReasoningStrategy
    match_score: float  # How well the strategy matches the current situation
    rationale: str  # Why this strategy is recommended
    expected_confidence_boost: float
    expected_success_probability: float


@dataclass
class LearningUpdate:
    """An update to the meta-learning system based on new evidence."""

    update_type: str  # 'new_strategy', 'strategy_refined', 'confidence_adjusted'
    strategy_id: Optional[str]
    description: str
    impact: float  # Estimated impact on future performance


class MetaLearningSystem:
    """
    Meta-learning system that learns how to learn.

    Extracts high-level strategies from successful reasoning patterns
    and recommends them for future use.
    """

    # Minimum success rate to consider a strategy valuable
    MIN_SUCCESS_RATE = 0.7

    # Minimum usage count to trust a strategy
    MIN_USAGE_COUNT = 3

    def __init__(self):
        self.strategies: Dict[str, ReasoningStrategy] = {}
        self.domain_strategies: Dict[str, List[str]] = defaultdict(
            list
        )  # domain -> strategy_ids

    def learn_from_capsules(
        self, capsules_with_outcomes: List[Dict]
    ) -> List[LearningUpdate]:
        """
        Learn new strategies from capsules with outcomes.

        Args:
            capsules_with_outcomes: List of dicts with capsule and outcome data

        Returns:
            List of learning updates describing what was learned
        """
        updates = []

        # Group capsules by success
        successful = [
            c for c in capsules_with_outcomes if c.get("outcome_success", False)
        ]
        failed = [
            c for c in capsules_with_outcomes if not c.get("outcome_success", False)
        ]

        # Extract strategies from successful capsules
        new_strategies = self._extract_strategies(successful)

        for strategy in new_strategies:
            if strategy.success_rate >= self.MIN_SUCCESS_RATE:
                existing = self.strategies.get(strategy.strategy_id)

                if existing:
                    # Refine existing strategy
                    updated = self._refine_strategy(existing, strategy)
                    self.strategies[strategy.strategy_id] = updated

                    update = LearningUpdate(
                        update_type="strategy_refined",
                        strategy_id=strategy.strategy_id,
                        description=f"Refined strategy '{strategy.strategy_name}' with {strategy.usage_count} new examples",
                        impact=0.1 * (updated.success_rate - existing.success_rate),
                    )
                    updates.append(update)
                else:
                    # Add new strategy
                    self.strategies[strategy.strategy_id] = strategy

                    # Index by domain
                    for domain in strategy.applicable_domains:
                        self.domain_strategies[domain].append(strategy.strategy_id)

                    update = LearningUpdate(
                        update_type="new_strategy",
                        strategy_id=strategy.strategy_id,
                        description=f"Discovered new strategy '{strategy.strategy_name}' with {strategy.success_rate:.1%} success rate",
                        impact=strategy.success_rate,
                    )
                    updates.append(update)

        return updates

    def _extract_strategies(self, capsules: List[Dict]) -> List[ReasoningStrategy]:
        """
        Extract reasoning strategies from capsules.

        A strategy is a repeatable pattern of reasoning steps that leads to success.
        """
        strategies = []

        # Group capsules by structural similarity
        strategy_groups = defaultdict(list)

        for capsule_data in capsules:
            capsule = capsule_data.get("capsule", {})

            # Extract strategy signature
            signature = self._extract_strategy_signature(capsule)

            if signature:
                strategy_groups[signature].append(capsule_data)

        # Create strategies from groups
        for signature, group in strategy_groups.items():
            if len(group) < self.MIN_USAGE_COUNT:
                continue

            strategy = self._create_strategy_from_group(signature, group)
            strategies.append(strategy)

        return strategies

    def _extract_strategy_signature(self, capsule: Dict) -> Optional[str]:
        """
        Extract a signature representing the reasoning strategy used.

        Signature includes:
        - Sequence of operation types
        - Decision points
        - Problem-solving approach
        """
        steps = capsule.get("payload", {}).get("reasoning_steps", [])

        if not steps:
            return None

        # Extract operation sequence
        operations = []
        has_alternatives = False
        has_measurements = False

        for step in steps:
            if isinstance(step, dict):
                op = step.get("operation", "reasoning")
                operations.append(op)

                if step.get("alternatives_considered"):
                    has_alternatives = True

                if step.get("measurements"):
                    has_measurements = True

        # Create signature
        signature_dict = {
            "operation_sequence": operations,
            "considers_alternatives": has_alternatives,
            "uses_measurements": has_measurements,
            "sequence_length": len(operations),
        }

        # Hash to create stable ID
        signature_str = json.dumps(signature_dict, sort_keys=True)
        return hashlib.sha256(signature_str.encode()).hexdigest()[:16]

    def _create_strategy_from_group(
        self, signature: str, capsules: List[Dict]
    ) -> ReasoningStrategy:
        """Create a strategy from a group of similar capsules."""

        # Aggregate metrics
        success_count = sum(1 for c in capsules if c.get("outcome_success", False))
        success_rate = success_count / len(capsules)

        confidences = [
            c.get("capsule", {}).get("payload", {}).get("confidence", 0.8)
            for c in capsules
        ]
        avg_confidence = sum(confidences) / len(confidences)

        quality_scores = [
            c.get("outcome_quality_score", 0.8)
            for c in capsules
            if c.get("outcome_quality_score") is not None
        ]
        avg_quality = (
            sum(quality_scores) / len(quality_scores) if quality_scores else 0.8
        )

        # Extract domains
        domains = []
        for c in capsules:
            domain = c.get("domain", "general")
            domains.append(domain)

        domain_counter = Counter(domains)
        top_domains = [d for d, _ in domain_counter.most_common(3)]

        # Extract problem types
        problem_types = self._extract_problem_types(capsules)

        # Extract common pattern
        pattern = self._extract_common_pattern(capsules)

        # Generate name and description
        name = self._generate_strategy_name(pattern)
        description = self._generate_strategy_description(pattern, success_rate)

        # Extract context requirements
        required_context = self._extract_required_context(capsules)

        return ReasoningStrategy(
            strategy_id=signature,
            strategy_name=name,
            strategy_description=description,
            strategy_pattern=pattern,
            success_rate=success_rate,
            usage_count=len(capsules),
            average_confidence=avg_confidence,
            average_quality_score=avg_quality,
            applicable_domains=top_domains,
            applicable_problem_types=problem_types,
            required_context=required_context,
            example_capsule_ids=[
                c.get("capsule", {}).get("capsule_id", "") for c in capsules[:5]
            ],
        )

    def _extract_problem_types(self, capsules: List[Dict]) -> List[str]:
        """Extract problem types from capsules."""
        types = []

        for c in capsules:
            problem_type = (
                c.get("capsule", {})
                .get("payload", {})
                .get("session_metadata", {})
                .get("problem_type", "general")
            )
            types.append(problem_type)

        counter = Counter(types)
        return [t for t, _ in counter.most_common(3)]

    def _extract_common_pattern(self, capsules: List[Dict]) -> Dict[str, Any]:
        """Extract common structural pattern from capsules."""
        # Analyze first capsule for pattern
        if not capsules:
            return {}

        first_capsule = capsules[0].get("capsule", {})
        steps = first_capsule.get("payload", {}).get("reasoning_steps", [])

        operations = []
        for step in steps:
            if isinstance(step, dict):
                operations.append(step.get("operation", "reasoning"))

        return {
            "operation_sequence": operations,
            "typical_length": len(operations),
            "uses_measurements": any(
                isinstance(s, dict) and s.get("measurements")
                for capsule in capsules
                for s in capsule.get("capsule", {})
                .get("payload", {})
                .get("reasoning_steps", [])
            ),
        }

    def _generate_strategy_name(self, pattern: Dict[str, Any]) -> str:
        """Generate a human-readable name for the strategy."""
        operations = pattern.get("operation_sequence", [])

        if not operations:
            return "General Reasoning Strategy"

        # Create name from operations
        if len(operations) <= 3:
            return " → ".join(op.capitalize() for op in operations)
        else:
            return f"{operations[0].capitalize()} ... {operations[-1].capitalize()} ({len(operations)} steps)"

    def _generate_strategy_description(
        self, pattern: Dict[str, Any], success_rate: float
    ) -> str:
        """Generate a description of the strategy."""
        operations = pattern.get("operation_sequence", [])
        length = len(operations)

        desc = (
            f"A {length}-step reasoning strategy with {success_rate:.1%} success rate. "
        )

        if pattern.get("uses_measurements"):
            desc += "Includes measurements and validation. "

        return desc

    def _extract_required_context(self, capsules: List[Dict]) -> List[str]:
        """Extract context elements required for this strategy."""
        context_elements = set()

        for c in capsules:
            metadata = (
                c.get("capsule", {}).get("payload", {}).get("session_metadata", {})
            )

            if metadata.get("files_involved"):
                context_elements.add("file_access")

            if metadata.get("tools_used"):
                context_elements.add("tool_execution")

            if metadata.get("constraints"):
                context_elements.add("constraints")

        return list(context_elements)

    def _refine_strategy(
        self, existing: ReasoningStrategy, new: ReasoningStrategy
    ) -> ReasoningStrategy:
        """Refine an existing strategy with new evidence."""

        total_usage = existing.usage_count + new.usage_count

        # Weighted averages
        refined_success_rate = (
            existing.success_rate * existing.usage_count
            + new.success_rate * new.usage_count
        ) / total_usage

        refined_confidence = (
            existing.average_confidence * existing.usage_count
            + new.average_confidence * new.usage_count
        ) / total_usage

        refined_quality = (
            existing.average_quality_score * existing.usage_count
            + new.average_quality_score * new.usage_count
        ) / total_usage

        # Merge domains and examples
        merged_domains = list(set(existing.applicable_domains + new.applicable_domains))
        merged_examples = existing.example_capsule_ids + new.example_capsule_ids
        merged_examples = merged_examples[:10]  # Keep top 10

        return ReasoningStrategy(
            strategy_id=existing.strategy_id,
            strategy_name=existing.strategy_name,
            strategy_description=existing.strategy_description,
            strategy_pattern=existing.strategy_pattern,
            success_rate=refined_success_rate,
            usage_count=total_usage,
            average_confidence=refined_confidence,
            average_quality_score=refined_quality,
            applicable_domains=merged_domains,
            applicable_problem_types=existing.applicable_problem_types,
            required_context=existing.required_context,
            example_capsule_ids=merged_examples,
            discovered_at=existing.discovered_at,
        )

    def recommend_strategies(
        self, context: Dict[str, Any], top_k: int = 3
    ) -> List[StrategyRecommendation]:
        """
        Recommend strategies for a given context.

        Args:
            context: Current problem context (domain, type, etc.)
            top_k: Number of recommendations to return

        Returns:
            List of strategy recommendations
        """
        domain = context.get("domain", "general")
        problem_type = context.get("problem_type", "general")
        available_context = set(context.get("context_elements", []))

        recommendations = []

        # Get strategies for this domain
        candidate_strategy_ids = self.domain_strategies.get(domain, [])

        # Also consider general strategies
        candidate_strategy_ids.extend(self.domain_strategies.get("general", []))

        for strategy_id in set(candidate_strategy_ids):
            strategy = self.strategies.get(strategy_id)

            if not strategy:
                continue

            # Calculate match score
            match_score = self._calculate_match_score(
                strategy, domain, problem_type, available_context
            )

            if match_score > 0.3:  # Threshold
                # Estimate confidence boost
                confidence_boost = (strategy.average_confidence - 0.8) * match_score

                # Estimate success probability
                success_probability = strategy.success_rate * match_score

                rationale = self._generate_rationale(strategy, match_score, context)

                recommendation = StrategyRecommendation(
                    strategy=strategy,
                    match_score=match_score,
                    rationale=rationale,
                    expected_confidence_boost=confidence_boost,
                    expected_success_probability=success_probability,
                )

                recommendations.append(recommendation)

        # Sort by match score
        recommendations.sort(key=lambda r: r.match_score, reverse=True)

        return recommendations[:top_k]

    def _calculate_match_score(
        self,
        strategy: ReasoningStrategy,
        domain: str,
        problem_type: str,
        available_context: Set[str],
    ) -> float:
        """Calculate how well a strategy matches the current context."""
        score = 0.0

        # Domain match
        if domain in strategy.applicable_domains:
            score += 0.4
        elif "general" in strategy.applicable_domains:
            score += 0.2

        # Problem type match
        if problem_type in strategy.applicable_problem_types:
            score += 0.3

        # Context availability
        required = set(strategy.required_context)
        if required:
            context_match = len(required & available_context) / len(required)
            score += 0.3 * context_match
        else:
            score += 0.3  # No requirements

        return min(1.0, score)

    def _generate_rationale(
        self, strategy: ReasoningStrategy, match_score: float, context: Dict[str, Any]
    ) -> str:
        """Generate explanation for why this strategy is recommended."""
        rationale = f"Strategy '{strategy.strategy_name}' has {strategy.success_rate:.1%} success rate "
        rationale += f"across {strategy.usage_count} uses. "

        if match_score > 0.8:
            rationale += "Strong match for current context. "
        elif match_score > 0.5:
            rationale += "Good match for current context. "

        rationale += (
            f"Expected to boost confidence by {strategy.average_confidence - 0.8:.2f}."
        )

        return rationale

    def export_learned_knowledge(self) -> Dict[str, Any]:
        """Export learned strategies for persistence."""
        return {
            "strategies": {
                strategy_id: {
                    "name": s.strategy_name,
                    "description": s.strategy_description,
                    "pattern": s.strategy_pattern,
                    "success_rate": s.success_rate,
                    "usage_count": s.usage_count,
                    "domains": s.applicable_domains,
                    "problem_types": s.applicable_problem_types,
                }
                for strategy_id, s in self.strategies.items()
            },
            "total_strategies": len(self.strategies),
            "domains_covered": list(self.domain_strategies.keys()),
        }


# Example usage
if __name__ == "__main__":
    print("[OK] Meta-Learning System Ready")
    print("\nCapabilities:")
    print("  - Learn reasoning strategies from successful capsules")
    print("  - Refine strategies with new evidence")
    print("  - Recommend strategies for new problems")
    print("  - Estimate expected performance improvements")
    print("  - Export learned knowledge for persistence")
    print("  - Track strategy effectiveness across domains")
