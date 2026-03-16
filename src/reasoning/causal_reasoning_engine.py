"""
Causal Reasoning Engine
High-level API for causal analysis of capsule reasoning
"""

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .causal_graph import CausalGraph, CausalGraphBuilder, CausalPath
from .structural_causal_model import (
    CausalEffect,
    CausalMechanism,
    CounterfactualQuery,
    Intervention,
    StructuralCausalModel,
    linear_mechanism,
    threshold_mechanism,
)


@dataclass
class CausalInsight:
    """An insight discovered through causal analysis."""

    insight_type: str  # 'root_cause', 'critical_path', 'intervention', 'counterfactual'
    description: str
    confidence: float
    variables_involved: List[str]
    supporting_evidence: List[str]  # Capsule IDs
    actionable_recommendation: Optional[str] = None


@dataclass
class CausalQuery:
    """A high-level causal question about capsules."""

    query_type: str  # 'what_caused', 'what_if', 'why', 'how_to_achieve'
    query: str
    variables: Dict[str, Any] = None


@dataclass
class CausalAnalysisResult:
    """Result of causal analysis."""

    query: CausalQuery
    insights: List[CausalInsight]
    causal_paths: List[CausalPath]
    estimated_effects: List[CausalEffect]
    recommendations: List[str]


class CausalReasoningEngine:
    """
    High-level causal reasoning engine for capsule analysis.

    Combines causal graphs and structural causal models to:
    - Identify root causes of outcomes
    - Predict effects of interventions
    - Answer counterfactual questions
    - Provide actionable recommendations
    """

    def __init__(self):
        self.causal_graph: Optional[CausalGraph] = None
        self.scm: Optional[StructuralCausalModel] = None
        self.capsules: List[Dict] = []

    def ingest_capsules(self, capsules: List[Dict]) -> None:
        """
        Ingest capsules and build causal models.

        Args:
            capsules: List of capsule dictionaries
        """
        self.capsules = capsules

        # Build causal graph
        self.causal_graph = CausalGraphBuilder.build_from_capsules(capsules)

        # Build SCM from graph
        self.scm = self._build_scm_from_graph(self.causal_graph)

    def _build_scm_from_graph(self, graph: CausalGraph) -> StructuralCausalModel:
        """
        Build a Structural Causal Model from a causal graph.

        Creates mechanisms based on graph structure and observed data.
        """
        scm = StructuralCausalModel(name="capsule_reasoning_scm")

        # Add exogenous variables (root causes)
        root_causes = graph.get_root_causes()
        for root in root_causes:
            # Simple uniform distribution for root causes
            scm.add_exogenous(root, lambda: random.uniform(0, 1))

        # Add mechanisms for each variable
        for var_name, variable in graph.variables.items():
            parents = graph.get_parents(var_name)

            if not parents:
                # Root cause - no mechanism needed (exogenous)
                continue

            # Create mechanism based on variable type
            if variable.var_type == "action":
                # Actions: threshold-based on conditions
                mechanism = CausalMechanism(
                    variable=var_name,
                    parents=parents,
                    mechanism=threshold_mechanism(0.5, parents[0])
                    if parents
                    else lambda x: 0,
                    mechanism_type="threshold",
                    parameters={"threshold": 0.5},
                )
            elif variable.var_type == "outcome":
                # Outcomes: weighted sum of actions
                weights = {p: 1.0 / len(parents) for p in parents}
                mechanism = CausalMechanism(
                    variable=var_name,
                    parents=parents,
                    mechanism=linear_mechanism(weights),
                    mechanism_type="linear",
                    parameters={"weights": weights},
                )
            else:
                # Default: average of parents
                def average_mechanism(parent_values: Dict[str, Any]) -> float:
                    values = [v for v in parent_values.values() if v is not None]
                    return sum(values) / len(values) if values else 0.0

                mechanism = CausalMechanism(
                    variable=var_name,
                    parents=parents,
                    mechanism=average_mechanism,
                    mechanism_type="average",
                )

            scm.add_mechanism(mechanism)

        return scm

    def find_root_causes(
        self, outcome_variable: str, min_confidence: float = 0.7
    ) -> List[CausalInsight]:
        """
        Identify root causes of an outcome.

        Args:
            outcome_variable: The outcome to analyze
            min_confidence: Minimum confidence threshold

        Returns:
            List of root cause insights
        """
        if not self.causal_graph:
            return []

        insights = []

        # Find all paths to outcome
        root_causes = self.causal_graph.get_root_causes()

        for root in root_causes:
            paths = self.causal_graph.find_all_paths(root, outcome_variable)

            if paths:
                # This root cause influences the outcome
                strongest_path = paths[0]  # Already sorted by strength

                if strongest_path.total_strength >= min_confidence:
                    # Get supporting evidence (capsules)
                    evidence = self._find_supporting_capsules(strongest_path.path)

                    insight = CausalInsight(
                        insight_type="root_cause",
                        description=f"{root} is a root cause of {outcome_variable}",
                        confidence=strongest_path.total_strength,
                        variables_involved=strongest_path.path,
                        supporting_evidence=evidence,
                        actionable_recommendation=f"To influence {outcome_variable}, consider modifying {root}",
                    )
                    insights.append(insight)

        # Sort by confidence
        insights.sort(key=lambda i: i.confidence, reverse=True)
        return insights

    def predict_intervention_effect(
        self,
        intervention_var: str,
        intervention_value: Any,
        outcome_var: str,
        num_samples: int = 1000,
    ) -> CausalInsight:
        """
        Predict the effect of an intervention.

        Args:
            intervention_var: Variable to intervene on
            intervention_value: Value to set
            outcome_var: Variable to measure
            num_samples: Monte Carlo samples

        Returns:
            Insight about intervention effect
        """
        if not self.scm:
            return CausalInsight(
                insight_type="intervention",
                description="No SCM available",
                confidence=0.0,
                variables_involved=[],
                supporting_evidence=[],
            )

        intervention = Intervention(
            variable=intervention_var,
            value=intervention_value,
            description=f"Set {intervention_var} to {intervention_value}",
        )

        effect = self.scm.estimate_causal_effect(
            intervention=intervention,
            target_variable=outcome_var,
            num_samples=num_samples,
        )

        # Convert effect to insight
        if effect.average_effect > 0:
            direction = "increases"
        elif effect.average_effect < 0:
            direction = "decreases"
        else:
            direction = "does not affect"

        description = (
            f"Setting {intervention_var} to {intervention_value} {direction} "
            f"{outcome_var} by {abs(effect.average_effect):.3f} "
            f"(95% CI: [{effect.confidence_interval[0]:.3f}, {effect.confidence_interval[1]:.3f}])"
        )

        confidence = min(
            1.0,
            1.0
            / (
                1.0 + abs(effect.confidence_interval[1] - effect.confidence_interval[0])
            ),
        )

        return CausalInsight(
            insight_type="intervention",
            description=description,
            confidence=confidence,
            variables_involved=[intervention_var, outcome_var],
            supporting_evidence=[],
            actionable_recommendation=f"Consider intervening on {intervention_var} to achieve desired outcome",
        )

    def answer_counterfactual(
        self,
        query: str,
        intervention_var: str,
        intervention_value: Any,
        query_var: str,
        observed_values: Dict[str, Any],
    ) -> CausalInsight:
        """
        Answer a counterfactual question.

        Args:
            query: Natural language query
            intervention_var: Variable to change
            intervention_value: Hypothetical value
            query_var: Variable to compute
            observed_values: What actually happened

        Returns:
            Counterfactual insight
        """
        if not self.scm:
            return CausalInsight(
                insight_type="counterfactual",
                description="No SCM available",
                confidence=0.0,
                variables_involved=[],
                supporting_evidence=[],
            )

        cf_query = CounterfactualQuery(
            query_variable=query_var,
            intervention=Intervention(
                variable=intervention_var, value=intervention_value
            ),
            observed_values=observed_values,
            description=query,
        )

        result = self.scm.answer_counterfactual(cf_query)

        description = (
            f"Counterfactual: {query}\n"
            f"Result: {query_var} would have been {result['result']} "
            f"(actual: {result.get('factual_value', 'unknown')})"
        )

        return CausalInsight(
            insight_type="counterfactual",
            description=description,
            confidence=result["confidence"],
            variables_involved=[intervention_var, query_var],
            supporting_evidence=[],
        )

    def find_intervention_strategy(
        self, target_var: str, target_value: Any, candidate_vars: List[str]
    ) -> List[CausalInsight]:
        """
        Find the best intervention strategy to achieve a target.

        Args:
            target_var: Variable to influence
            target_value: Desired value
            candidate_vars: Variables available for intervention

        Returns:
            List of intervention strategies ranked by effectiveness
        """
        if not self.scm:
            return []

        insights = []

        # Test each candidate intervention
        for var in candidate_vars:
            intervention = Intervention(
                variable=var,
                value=target_value,
                description=f"Set {var} to {target_value}",
            )

            self.scm.estimate_causal_effect(
                intervention=intervention, target_variable=target_var, num_samples=500
            )

            # How close does this get us to target?
            samples = self.scm.simulate(interventions=[intervention], num_samples=100)
            successes = sum(
                1 for s in samples if abs(s.get(target_var, 0) - target_value) < 0.1
            )
            success_rate = successes / len(samples)

            description = (
                f"Intervening on {var} achieves {target_var}={target_value} "
                f"in {success_rate:.1%} of cases"
            )

            insight = CausalInsight(
                insight_type="intervention",
                description=description,
                confidence=success_rate,
                variables_involved=[var, target_var],
                supporting_evidence=[],
                actionable_recommendation=f"Set {var} to {target_value} to achieve target",
            )
            insights.append(insight)

        # Sort by confidence (success rate)
        insights.sort(key=lambda i: i.confidence, reverse=True)
        return insights

    def analyze_causal_query(self, query: CausalQuery) -> CausalAnalysisResult:
        """
        Analyze a high-level causal query.

        Args:
            query: The causal question to answer

        Returns:
            Comprehensive analysis result
        """
        insights = []
        causal_paths = []
        estimated_effects = []
        recommendations = []

        if query.query_type == "what_caused":
            # Find root causes
            outcome_var = query.variables.get("outcome")
            if outcome_var:
                insights = self.find_root_causes(outcome_var)
                recommendations.append(
                    f"Focus on the top {len(insights)} root causes identified"
                )

        elif query.query_type == "what_if":
            # Intervention analysis
            intervention_var = query.variables.get("intervention_var")
            intervention_value = query.variables.get("intervention_value")
            outcome_var = query.variables.get("outcome_var")

            if intervention_var and outcome_var:
                insight = self.predict_intervention_effect(
                    intervention_var, intervention_value, outcome_var
                )
                insights.append(insight)
                recommendations.append(insight.actionable_recommendation)

        elif query.query_type == "how_to_achieve":
            # Find intervention strategy
            target_var = query.variables.get("target_var")
            target_value = query.variables.get("target_value")
            candidates = query.variables.get("candidates", [])

            if target_var and candidates:
                insights = self.find_intervention_strategy(
                    target_var, target_value, candidates
                )
                if insights:
                    recommendations.append(
                        f"Best strategy: {insights[0].actionable_recommendation}"
                    )

        return CausalAnalysisResult(
            query=query,
            insights=insights,
            causal_paths=causal_paths,
            estimated_effects=estimated_effects,
            recommendations=recommendations,
        )

    def _find_supporting_capsules(self, variable_path: List[str]) -> List[str]:
        """Find capsule IDs that contain evidence for a causal path."""
        supporting_capsules = []

        for capsule in self.capsules:
            capsule_id = capsule.get("capsule_id", "unknown")

            # Check if capsule contains variables in path
            steps = capsule.get("payload", {}).get("reasoning_steps", [])
            capsule_vars = set()

            for i, step in enumerate(steps):
                if isinstance(step, dict):
                    operation = step.get("operation", "reasoning")
                    var_name = f"step_{i}_{operation}"
                    capsule_vars.add(var_name)

            # If capsule contains path variables, it's supporting evidence
            if any(var in capsule_vars for var in variable_path):
                supporting_capsules.append(capsule_id)

        return supporting_capsules

    def export_causal_knowledge(self) -> Dict[str, Any]:
        """
        Export learned causal knowledge for reuse.

        Returns:
            Dictionary with causal graph and SCM
        """
        return {
            "causal_graph": self.causal_graph.to_dict() if self.causal_graph else {},
            "scm": self.scm.to_dict() if self.scm else {},
            "num_capsules": len(self.capsules),
            "root_causes": self.causal_graph.get_root_causes()
            if self.causal_graph
            else [],
            "terminal_effects": self.causal_graph.get_terminal_effects()
            if self.causal_graph
            else [],
        }


# Example usage
if __name__ == "__main__":
    print("[OK] Causal Reasoning Engine Ready")
    print("\nCapabilities:")
    print("  - Ingest capsules and build causal models")
    print("  - Identify root causes of outcomes")
    print("  - Predict effects of interventions")
    print("  - Answer counterfactual questions")
    print("  - Find optimal intervention strategies")
    print("  - Export learned causal knowledge")
    print("  - Provide actionable recommendations")
