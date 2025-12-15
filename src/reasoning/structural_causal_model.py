"""
Structural Causal Model (SCM)
Mathematical framework for causal reasoning, interventions, and counterfactuals
"""

import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class CausalMechanism:
    """
    A causal mechanism defines how a variable is determined by its parents.

    For variable Y with parents X1, X2, ...:
    Y = f(X1, X2, ..., U_Y)

    where U_Y is unobserved noise/randomness
    """

    variable: str
    parents: List[str]
    mechanism: Callable[
        [Dict[str, Any]], Any
    ]  # Function: parent_values -> variable_value
    mechanism_type: str  # 'deterministic', 'probabilistic', 'learned'
    noise_distribution: Optional[str] = None  # 'gaussian', 'uniform', etc.
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Intervention:
    """
    An intervention sets a variable to a specific value, breaking its normal causal mechanism.

    In do-calculus: do(X = x) means "set X to x regardless of its parents"
    """

    variable: str
    value: Any
    description: str = ""


@dataclass
class CounterfactualQuery:
    """
    A counterfactual query asks: "What would Y have been if X had been x?"

    Given observed values (factual world), compute what would have happened
    under a different intervention (counterfactual world).
    """

    query_variable: str  # What we want to know
    intervention: Intervention  # What we change
    observed_values: Dict[str, Any]  # What actually happened
    description: str = ""


@dataclass
class CausalEffect:
    """Result of estimating a causal effect."""

    intervention: Intervention
    target_variable: str
    average_effect: float
    effect_distribution: List[float]  # Distribution of effects
    confidence_interval: Tuple[float, float]
    sample_size: int


class StructuralCausalModel:
    """
    A Structural Causal Model (SCM) consists of:
    1. A set of endogenous variables (determined by the model)
    2. A set of exogenous variables (external inputs/noise)
    3. A set of structural equations (causal mechanisms)
    4. A directed acyclic graph structure

    The SCM allows us to:
    - Simulate what happens under normal conditions
    - Intervene (do-calculus)
    - Answer counterfactual queries
    """

    def __init__(self, name: str = ""):
        self.name = name
        self.mechanisms: Dict[str, CausalMechanism] = {}
        self.exogenous_vars: Dict[str, Any] = {}  # External variables
        self.variable_order: List[str] = []  # Topological order

    def add_mechanism(self, mechanism: CausalMechanism) -> None:
        """Add a causal mechanism to the model."""
        self.mechanisms[mechanism.variable] = mechanism
        self._recompute_order()

    def add_exogenous(self, variable: str, distribution: Callable[[], Any]) -> None:
        """Add an exogenous (external) variable with its distribution."""
        self.exogenous_vars[variable] = distribution

    def _recompute_order(self) -> None:
        """Compute topological order of variables (parents before children)."""
        in_degree = defaultdict(int)
        graph = defaultdict(list)

        # Build adjacency list
        for var, mech in self.mechanisms.items():
            for parent in mech.parents:
                graph[parent].append(var)
                in_degree[var] += 1

        # Topological sort
        queue = [var for var in self.mechanisms if in_degree[var] == 0]
        order = []

        while queue:
            current = queue.pop(0)
            order.append(current)

            for child in graph[current]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        self.variable_order = order

    def simulate(
        self, interventions: Optional[List[Intervention]] = None, num_samples: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Simulate the SCM to generate samples.

        Args:
            interventions: Optional list of interventions (do-calculus)
            num_samples: Number of samples to generate

        Returns:
            List of dictionaries mapping variable names to values
        """
        intervention_dict = {}
        if interventions:
            intervention_dict = {i.variable: i.value for i in interventions}

        samples = []

        for _ in range(num_samples):
            values = {}

            # Sample exogenous variables
            for var, dist in self.exogenous_vars.items():
                values[var] = dist()

            # Compute endogenous variables in topological order
            for var in self.variable_order:
                if var in intervention_dict:
                    # Intervention: set to specified value
                    values[var] = intervention_dict[var]
                else:
                    # Normal: compute from mechanism
                    mechanism = self.mechanisms[var]
                    parent_values = {p: values.get(p) for p in mechanism.parents}

                    # Handle missing parent values
                    if any(v is None for v in parent_values.values()):
                        # Use default or skip
                        values[var] = None
                    else:
                        values[var] = mechanism.mechanism(parent_values)

            samples.append(values)

        return samples

    def estimate_causal_effect(
        self, intervention: Intervention, target_variable: str, num_samples: int = 1000
    ) -> CausalEffect:
        """
        Estimate the causal effect of an intervention on a target variable.

        Compares:
        - E[Y | do(X = x)] (intervened)
        - E[Y] (baseline)

        Args:
            intervention: The intervention to apply
            target_variable: The variable to measure
            num_samples: Number of Monte Carlo samples

        Returns:
            CausalEffect with average effect and distribution
        """
        # Baseline (no intervention)
        baseline_samples = self.simulate(interventions=None, num_samples=num_samples)
        baseline_values = [
            s[target_variable]
            for s in baseline_samples
            if s.get(target_variable) is not None
        ]

        # Intervention
        intervened_samples = self.simulate(
            interventions=[intervention], num_samples=num_samples
        )
        intervened_values = [
            s[target_variable]
            for s in intervened_samples
            if s.get(target_variable) is not None
        ]

        # Calculate effects
        if not baseline_values or not intervened_values:
            return CausalEffect(
                intervention=intervention,
                target_variable=target_variable,
                average_effect=0.0,
                effect_distribution=[],
                confidence_interval=(0.0, 0.0),
                sample_size=0,
            )

        baseline_mean = sum(baseline_values) / len(baseline_values)
        intervened_mean = sum(intervened_values) / len(intervened_values)

        average_effect = intervened_mean - baseline_mean
        effect_distribution = [
            i - b for i, b in zip(intervened_values, baseline_values)
        ]

        # 95% confidence interval
        sorted_effects = sorted(effect_distribution)
        lower_idx = int(0.025 * len(sorted_effects))
        upper_idx = int(0.975 * len(sorted_effects))
        confidence_interval = (sorted_effects[lower_idx], sorted_effects[upper_idx])

        return CausalEffect(
            intervention=intervention,
            target_variable=target_variable,
            average_effect=average_effect,
            effect_distribution=effect_distribution,
            confidence_interval=confidence_interval,
            sample_size=len(effect_distribution),
        )

    def answer_counterfactual(
        self, query: CounterfactualQuery, num_samples: int = 1000
    ) -> Dict[str, Any]:
        """
        Answer a counterfactual query: "What would Y have been if X had been x?"

        Three-step process:
        1. Abduction: Infer the exogenous variables from observed values
        2. Action: Apply the intervention
        3. Prediction: Compute the query variable under the intervention

        Args:
            query: The counterfactual query
            num_samples: Number of samples for approximation

        Returns:
            Dictionary with counterfactual result and confidence
        """
        # Step 1: Abduction - infer unobserved variables
        # For now, use observed values as constraints

        # Step 2: Action - apply intervention
        # Step 3: Prediction - simulate with intervention

        # Simplified approach: simulate with intervention and observed constraints
        counterfactual_samples = []

        for _ in range(num_samples):
            values = {}

            # Sample exogenous variables
            for var, dist in self.exogenous_vars.items():
                values[var] = dist()

            # Set observed values (factual world constraints)
            for var, val in query.observed_values.items():
                if var != query.intervention.variable:
                    values[var] = val

            # Apply intervention
            values[query.intervention.variable] = query.intervention.value

            # Compute downstream variables
            for var in self.variable_order:
                if var in values:
                    continue  # Already set

                mechanism = self.mechanisms.get(var)
                if not mechanism:
                    continue

                parent_values = {p: values.get(p) for p in mechanism.parents}

                if any(v is None for v in parent_values.values()):
                    values[var] = None
                else:
                    values[var] = mechanism.mechanism(parent_values)

            if query.query_variable in values:
                counterfactual_samples.append(values[query.query_variable])

        if not counterfactual_samples:
            return {
                "query": query.description,
                "result": None,
                "confidence": 0.0,
                "message": "Could not compute counterfactual",
            }

        # Aggregate results
        if isinstance(counterfactual_samples[0], (int, float)):
            mean_result = sum(counterfactual_samples) / len(counterfactual_samples)
            result = mean_result
        else:
            # Categorical: most common value
            from collections import Counter

            counter = Counter(counterfactual_samples)
            result = counter.most_common(1)[0][0]

        # Estimate confidence based on consistency
        if isinstance(result, (int, float)):
            variance = sum((x - result) ** 2 for x in counterfactual_samples) / len(
                counterfactual_samples
            )
            confidence = 1.0 / (1.0 + variance)  # Higher variance = lower confidence
        else:
            # Categorical: proportion of most common
            from collections import Counter

            counter = Counter(counterfactual_samples)
            confidence = counter.most_common(1)[0][1] / len(counterfactual_samples)

        return {
            "query": query.description,
            "result": result,
            "confidence": confidence,
            "factual_value": query.observed_values.get(query.query_variable),
            "samples": len(counterfactual_samples),
        }

    def find_minimal_intervention_set(
        self,
        target_variable: str,
        target_value: Any,
        candidate_variables: List[str],
        num_samples: int = 500,
    ) -> List[Intervention]:
        """
        Find the minimal set of interventions to achieve a target value.

        Args:
            target_variable: The variable we want to influence
            target_value: The desired value
            candidate_variables: Variables we can intervene on
            num_samples: Samples per intervention test

        Returns:
            List of interventions that best achieve the target
        """
        best_interventions = []
        best_score = float("-inf")

        # Try individual interventions
        for var in candidate_variables:
            # Test intervention
            intervention = Intervention(variable=var, value=target_value)
            samples = self.simulate(
                interventions=[intervention], num_samples=num_samples
            )

            # Score: proportion of samples achieving target
            successes = sum(
                1 for s in samples if s.get(target_variable) == target_value
            )
            score = successes / num_samples

            if score > best_score:
                best_score = score
                best_interventions = [intervention]

        return best_interventions

    def to_dict(self) -> Dict[str, Any]:
        """Convert SCM to dictionary representation."""
        return {
            "name": self.name,
            "variables": list(self.mechanisms.keys()),
            "exogenous_variables": list(self.exogenous_vars.keys()),
            "mechanisms": {
                var: {
                    "parents": mech.parents,
                    "type": mech.mechanism_type,
                    "noise": mech.noise_distribution,
                    "parameters": mech.parameters,
                }
                for var, mech in self.mechanisms.items()
            },
            "variable_order": self.variable_order,
        }


# Helper functions for creating common mechanisms


def linear_mechanism(
    coefficients: Dict[str, float], intercept: float = 0.0
) -> Callable:
    """Create a linear causal mechanism: Y = intercept + sum(coef * parent)"""

    def mechanism(parent_values: Dict[str, Any]) -> float:
        result = intercept
        for var, coef in coefficients.items():
            result += coef * parent_values.get(var, 0.0)
        return result

    return mechanism


def threshold_mechanism(threshold: float, parent: str) -> Callable:
    """Create a threshold mechanism: Y = 1 if parent > threshold else 0"""

    def mechanism(parent_values: Dict[str, Any]) -> int:
        return 1 if parent_values.get(parent, 0.0) > threshold else 0

    return mechanism


def logical_and_mechanism(parents: List[str]) -> Callable:
    """Create a logical AND mechanism: Y = 1 if all parents are True"""

    def mechanism(parent_values: Dict[str, Any]) -> bool:
        return all(parent_values.get(p, False) for p in parents)

    return mechanism


def probabilistic_mechanism(parents: List[str], probability_fn: Callable) -> Callable:
    """Create a probabilistic mechanism with custom probability function"""

    def mechanism(parent_values: Dict[str, Any]) -> bool:
        prob = probability_fn(parent_values)
        return random.random() < prob

    return mechanism


# Example usage
if __name__ == "__main__":
    print("✅ Structural Causal Model Ready")
    print("\nCapabilities:")
    print("  - Define causal mechanisms mathematically")
    print("  - Simulate SCM under normal conditions")
    print("  - Perform interventions (do-calculus)")
    print("  - Answer counterfactual queries")
    print("  - Estimate causal effects")
    print("  - Find minimal intervention sets")
    print("  - Support linear, threshold, logical, and probabilistic mechanisms")
