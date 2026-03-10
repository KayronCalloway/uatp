"""
Critical Path Analysis for Reasoning Steps
Identifies which steps actually mattered vs. peripheral steps
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.rich_capsule_creator import RichReasoningStep


@dataclass
class CriticalPathAnalysis:
    """Complete analysis of critical path through reasoning."""

    critical_steps: List[int]
    bottleneck_steps: List[int]
    key_decision_points: List[int]
    confidence_chain: List[float]
    weakest_link: Dict[str, Any]
    critical_path_strength: float
    peripheral_steps: List[int]
    dependency_depth: int


class CriticalPathAnalyzer:
    """Analyzes reasoning steps to identify critical path."""

    @staticmethod
    def analyze(reasoning_steps: List[RichReasoningStep]) -> CriticalPathAnalysis:
        """
        Perform complete critical path analysis.

        Args:
            reasoning_steps: List of rich reasoning steps

        Returns:
            CriticalPathAnalysis with full metrics
        """
        if not reasoning_steps:
            return CriticalPathAnalysis(
                critical_steps=[],
                bottleneck_steps=[],
                key_decision_points=[],
                confidence_chain=[],
                weakest_link={},
                critical_path_strength=1.0,
                peripheral_steps=[],
                dependency_depth=0,
            )

        # Build step map for quick lookup
        step_map = {step.step: step for step in reasoning_steps}

        # Identify critical steps (depended upon by others)
        critical_steps = CriticalPathAnalyzer._identify_critical_steps(reasoning_steps)

        # Identify bottleneck steps (lowest confidence)
        bottleneck_steps = CriticalPathAnalyzer._identify_bottlenecks(reasoning_steps)

        # Identify decision points (steps with alternatives)
        decision_points = CriticalPathAnalyzer._identify_decision_points(
            reasoning_steps
        )

        # If no critical path from dependencies, use decision points
        if not critical_steps and decision_points:
            critical_steps = decision_points
        # If still nothing, all steps are critical
        elif not critical_steps:
            critical_steps = [s.step for s in reasoning_steps]

        # Build confidence chain for critical path
        confidence_chain = [
            step_map[step_id].confidence
            for step_id in critical_steps
            if step_id in step_map
        ]

        # Find weakest link
        weakest_link = CriticalPathAnalyzer._find_weakest_link(
            critical_steps, step_map, confidence_chain
        )

        # Calculate critical path strength
        path_strength = (
            sum(confidence_chain) / len(confidence_chain) if confidence_chain else 1.0
        )

        # Identify peripheral steps
        all_step_ids = {s.step for s in reasoning_steps}
        critical_set = set(critical_steps)
        peripheral_steps = sorted(list(all_step_ids - critical_set))

        # Calculate dependency depth
        dependency_depth = CriticalPathAnalyzer._calculate_dependency_depth(
            reasoning_steps
        )

        return CriticalPathAnalysis(
            critical_steps=critical_steps,
            bottleneck_steps=bottleneck_steps,
            key_decision_points=decision_points,
            confidence_chain=confidence_chain,
            weakest_link=weakest_link,
            critical_path_strength=path_strength,
            peripheral_steps=peripheral_steps,
            dependency_depth=dependency_depth,
        )

    @staticmethod
    def _identify_critical_steps(steps: List[RichReasoningStep]) -> List[int]:
        """Identify steps on the critical path (depended upon by others)."""
        depended_upon = set()

        for step in steps:
            if step.depends_on_steps:
                depended_upon.update(step.depends_on_steps)

        # Also include the last step (final conclusion)
        if steps:
            depended_upon.add(steps[-1].step)

        return sorted(list(depended_upon))

    @staticmethod
    def _identify_bottlenecks(steps: List[RichReasoningStep]) -> List[int]:
        """Identify bottleneck steps (lowest confidence)."""
        if not steps:
            return []

        # Sort by confidence
        sorted_steps = sorted(steps, key=lambda s: s.confidence)

        # Bottom quartile are bottlenecks
        bottleneck_count = max(1, len(steps) // 4)

        return [s.step for s in sorted_steps[:bottleneck_count]]

    @staticmethod
    def _identify_decision_points(steps: List[RichReasoningStep]) -> List[int]:
        """Identify decision points (steps where alternatives were considered)."""
        return [
            step.step
            for step in steps
            if step.alternatives_considered and len(step.alternatives_considered) > 0
        ]

    @staticmethod
    def _find_weakest_link(
        critical_steps: List[int],
        step_map: Dict[int, RichReasoningStep],
        confidence_chain: List[float],
    ) -> Dict[str, Any]:
        """Find the weakest link in the critical path."""
        if not confidence_chain or not critical_steps:
            return {}

        weakest_confidence = min(confidence_chain)
        weakest_idx = confidence_chain.index(weakest_confidence)
        weakest_step_id = critical_steps[weakest_idx]

        step = step_map[weakest_step_id]
        reasoning_preview = (
            step.reasoning[:100] + "..."
            if len(step.reasoning) > 100
            else step.reasoning
        )

        return {
            "step_id": weakest_step_id,
            "confidence": weakest_confidence,
            "reasoning": reasoning_preview,
            "operation": step.operation,
            "uncertainty_sources": step.uncertainty_sources
            if step.uncertainty_sources
            else [],
        }

    @staticmethod
    def _calculate_dependency_depth(steps: List[RichReasoningStep]) -> int:
        """Calculate maximum dependency depth (longest chain)."""
        if not steps:
            return 0

        # Build adjacency list
        graph: Dict[int, List[int]] = {}
        for step in steps:
            graph[step.step] = step.depends_on_steps if step.depends_on_steps else []

        # Calculate depth for each node using DFS
        def get_depth(node: int, visited: Set[int]) -> int:
            if node in visited:
                return 0  # Cycle detection
            visited.add(node)

            if node not in graph or not graph[node]:
                return 1

            max_child_depth = max(
                (get_depth(child, visited.copy()) for child in graph[node]), default=0
            )
            return 1 + max_child_depth

        max_depth = max((get_depth(step.step, set()) for step in steps), default=0)
        return max_depth

    @staticmethod
    def generate_improvement_recommendations(
        analysis: CriticalPathAnalysis, step_map: Dict[int, RichReasoningStep]
    ) -> List[str]:
        """Generate recommendations to improve reasoning quality."""
        recommendations = []

        # Recommend strengthening bottlenecks
        if analysis.bottleneck_steps:
            bottleneck_step = step_map.get(analysis.bottleneck_steps[0])
            if bottleneck_step:
                recommendations.append(
                    f"[WARN] Strengthen step {bottleneck_step.step} (confidence: {bottleneck_step.confidence:.2f}) - "
                    f"this is a bottleneck in your reasoning"
                )

        # Recommend addressing weakest link
        if analysis.weakest_link:
            step_id = analysis.weakest_link["step_id"]
            confidence = analysis.weakest_link["confidence"]
            if confidence < 0.7:
                recommendations.append(
                    f" Critical: Step {step_id} has low confidence ({confidence:.2f}) and is on the critical path. "
                    f"Consider gathering more evidence or exploring alternatives."
                )

        # Recommend for high uncertainty on critical path
        for step_id in analysis.critical_steps:
            step = step_map.get(step_id)
            if step and step.uncertainty_sources and len(step.uncertainty_sources) > 2:
                recommendations.append(
                    f" Step {step_id} has multiple uncertainty sources on critical path: "
                    f"{', '.join(step.uncertainty_sources[:2])}. Address these to strengthen reasoning."
                )

        # Recommend expanding shallow reasoning
        if analysis.dependency_depth < 3 and len(step_map) > 3:
            recommendations.append(
                " Reasoning is relatively shallow (low dependency depth). "
                "Consider breaking down complex steps into smaller, more explicit steps."
            )

        # Recommend for missing alternatives at decision points
        for step_id in analysis.key_decision_points:
            step = step_map.get(step_id)
            if step and (
                not step.alternatives_considered
                or len(step.alternatives_considered) < 2
            ):
                recommendations.append(
                    f" Step {step_id} is a decision point but only {len(step.alternatives_considered or [])} "
                    f"alternative(s) documented. Consider explicitly documenting rejected alternatives."
                )

        return recommendations[:5]  # Limit to top 5

    @staticmethod
    def to_dict(analysis: CriticalPathAnalysis) -> Dict[str, Any]:
        """Convert analysis to dictionary for storage."""
        return {
            "critical_steps": analysis.critical_steps,
            "bottleneck_steps": analysis.bottleneck_steps,
            "key_decision_points": analysis.key_decision_points,
            "confidence_chain": [round(c, 3) for c in analysis.confidence_chain],
            "weakest_link": analysis.weakest_link,
            "critical_path_strength": round(analysis.critical_path_strength, 3),
            "peripheral_steps": analysis.peripheral_steps,
            "dependency_depth": analysis.dependency_depth,
        }


# Example usage
if __name__ == "__main__":
    print("[OK] Critical Path Analyzer Ready")
    print("\nCapabilities:")
    print("  - Identify critical steps on dependency path")
    print("  - Find bottleneck steps (lowest confidence)")
    print("  - Locate key decision points")
    print("  - Calculate path strength")
    print("  - Find weakest link")
    print("  - Generate improvement recommendations")
