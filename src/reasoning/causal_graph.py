"""
Causal Graph Construction
Builds directed acyclic graphs (DAGs) representing causal relationships from capsule reasoning
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class CausalVariable:
    """A variable in the causal graph."""

    name: str
    var_type: str  # 'action', 'condition', 'outcome', 'context'
    description: str
    confidence: float = 1.0
    domain: Optional[str] = None
    observed_values: List[Any] = field(default_factory=list)


@dataclass
class CausalEdge:
    """A causal relationship between two variables."""

    source: str  # Variable name
    target: str  # Variable name
    edge_type: str  # 'direct_cause', 'confounding', 'mediating'
    strength: float  # 0.0 to 1.0
    evidence_count: int = 1
    evidence_capsule_ids: List[str] = field(default_factory=list)


@dataclass
class CausalPath:
    """A causal path from one variable to another."""

    start: str
    end: str
    path: List[str]  # Sequence of variables
    total_strength: float
    path_type: str  # 'direct', 'indirect', 'confounded'


class CausalGraph:
    """
    A directed acyclic graph representing causal relationships.

    Nodes are variables (actions, conditions, outcomes).
    Edges represent causal influence from one variable to another.
    """

    def __init__(self):
        self.variables: Dict[str, CausalVariable] = {}
        self.edges: List[CausalEdge] = []
        self.adjacency: Dict[str, List[str]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)

    def add_variable(self, variable: CausalVariable) -> None:
        """Add a variable to the graph."""
        self.variables[variable.name] = variable

    def add_edge(self, edge: CausalEdge) -> None:
        """Add a causal edge to the graph."""
        # Check for cycles
        if self._would_create_cycle(edge.source, edge.target):
            raise ValueError(
                f"Adding edge {edge.source} -> {edge.target} would create a cycle"
            )

        # Check if edge already exists
        existing_edge = self._find_edge(edge.source, edge.target)
        if existing_edge:
            # Update existing edge
            existing_edge.evidence_count += 1
            existing_edge.evidence_capsule_ids.extend(edge.evidence_capsule_ids)
            # Update strength as weighted average
            existing_edge.strength = (
                existing_edge.strength * (existing_edge.evidence_count - 1)
                + edge.strength
            ) / existing_edge.evidence_count
        else:
            # Add new edge
            self.edges.append(edge)
            self.adjacency[edge.source].append(edge.target)
            self.reverse_adjacency[edge.target].append(edge.source)

    def _find_edge(self, source: str, target: str) -> Optional[CausalEdge]:
        """Find an existing edge between two variables."""
        for edge in self.edges:
            if edge.source == source and edge.target == target:
                return edge
        return None

    def _would_create_cycle(self, source: str, target: str) -> bool:
        """Check if adding an edge would create a cycle."""
        # If target can reach source, adding source -> target creates a cycle
        return self._can_reach(target, source)

    def _can_reach(self, start: str, end: str) -> bool:
        """Check if there's a path from start to end."""
        if start == end:
            return True

        visited = set()
        stack = [start]

        while stack:
            current = stack.pop()
            if current in visited:
                continue

            visited.add(current)

            if current == end:
                return True

            for neighbor in self.adjacency.get(current, []):
                if neighbor not in visited:
                    stack.append(neighbor)

        return False

    def get_parents(self, variable: str) -> List[str]:
        """Get direct causes of a variable."""
        return self.reverse_adjacency.get(variable, [])

    def get_children(self, variable: str) -> List[str]:
        """Get direct effects of a variable."""
        return self.adjacency.get(variable, [])

    def get_ancestors(self, variable: str) -> Set[str]:
        """Get all variables that causally influence this variable."""
        ancestors = set()
        stack = [variable]

        while stack:
            current = stack.pop()
            parents = self.get_parents(current)

            for parent in parents:
                if parent not in ancestors:
                    ancestors.add(parent)
                    stack.append(parent)

        return ancestors

    def get_descendants(self, variable: str) -> Set[str]:
        """Get all variables causally influenced by this variable."""
        descendants = set()
        stack = [variable]

        while stack:
            current = stack.pop()
            children = self.get_children(current)

            for child in children:
                if child not in descendants:
                    descendants.add(child)
                    stack.append(child)

        return descendants

    def find_all_paths(
        self, start: str, end: str, max_length: int = 10
    ) -> List[CausalPath]:
        """Find all causal paths from start to end."""
        paths = []

        def dfs(current: str, target: str, path: List[str], visited: Set[str]):
            if len(path) > max_length:
                return

            if current == target and len(path) > 1:
                # Calculate path strength (product of edge strengths)
                strength = 1.0
                for i in range(len(path) - 1):
                    edge = self._find_edge(path[i], path[i + 1])
                    if edge:
                        strength *= edge.strength

                # Determine path type
                path_type = "direct" if len(path) == 2 else "indirect"

                paths.append(
                    CausalPath(
                        start=start,
                        end=end,
                        path=path.copy(),
                        total_strength=strength,
                        path_type=path_type,
                    )
                )
                return

            for neighbor in self.get_children(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    dfs(neighbor, target, path, visited)
                    path.pop()
                    visited.remove(neighbor)

        if start in self.variables and end in self.variables:
            dfs(start, end, [start], {start})

        # Sort by strength
        paths.sort(key=lambda p: p.total_strength, reverse=True)
        return paths

    def get_root_causes(self) -> List[str]:
        """Get variables with no parents (root causes)."""
        return [var for var in self.variables if not self.get_parents(var)]

    def get_terminal_effects(self) -> List[str]:
        """Get variables with no children (terminal effects)."""
        return [var for var in self.variables if not self.get_children(var)]

    def topological_sort(self) -> List[str]:
        """Get variables in topological order (causes before effects)."""
        in_degree = {var: len(self.get_parents(var)) for var in self.variables}
        queue = [var for var, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for child in self.get_children(current):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary representation."""
        return {
            "variables": {
                name: {
                    "type": var.var_type,
                    "description": var.description,
                    "confidence": var.confidence,
                    "domain": var.domain,
                }
                for name, var in self.variables.items()
            },
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.edge_type,
                    "strength": edge.strength,
                    "evidence_count": edge.evidence_count,
                }
                for edge in self.edges
            ],
            "statistics": {
                "num_variables": len(self.variables),
                "num_edges": len(self.edges),
                "root_causes": self.get_root_causes(),
                "terminal_effects": self.get_terminal_effects(),
            },
        }


class CausalGraphBuilder:
    """
    Constructs causal graphs from capsule reasoning data.
    """

    # Patterns for identifying causal relationships
    CAUSAL_INDICATORS = [
        r"because\s+",
        r"due\s+to\s+",
        r"caused\s+by\s+",
        r"leads\s+to\s+",
        r"results\s+in\s+",
        r"therefore\s+",
        r"consequently\s+",
        r"as\s+a\s+result\s+",
        r"if\s+.*\s+then\s+",
    ]

    @classmethod
    def build_from_capsules(cls, capsules: List[Dict]) -> CausalGraph:
        """
        Build a causal graph from multiple capsules.

        Args:
            capsules: List of capsule dictionaries with reasoning steps

        Returns:
            CausalGraph representing causal relationships
        """
        graph = CausalGraph()

        for capsule in capsules:
            cls._extract_from_capsule(capsule, graph)

        return graph

    @classmethod
    def _extract_from_capsule(cls, capsule: Dict, graph: CausalGraph) -> None:
        """Extract causal relationships from a single capsule."""
        capsule_id = capsule.get("capsule_id", "unknown")

        # Extract from reasoning steps
        steps = capsule.get("payload", {}).get("reasoning_steps", [])

        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                continue

            # Extract variables from this step
            step_vars = cls._extract_variables_from_step(step, i, capsule_id)

            # Add variables to graph
            for var in step_vars:
                if var.name not in graph.variables:
                    graph.add_variable(var)

            # Extract causal edges from step
            step_edges = cls._extract_edges_from_step(step, step_vars, capsule_id)

            # Add edges to graph
            for edge in step_edges:
                try:
                    graph.add_edge(edge)
                except ValueError:
                    # Skip edges that would create cycles
                    pass

            # Connect sequential steps with causal edges
            if i > 0:
                prev_step = steps[i - 1]
                if isinstance(prev_step, dict):
                    cls._connect_sequential_steps(
                        prev_step, step, i - 1, i, graph, capsule_id
                    )

    @classmethod
    def _extract_variables_from_step(
        cls, step: Dict, step_index: int, capsule_id: str
    ) -> List[CausalVariable]:
        """Extract causal variables from a reasoning step."""
        variables = []

        # Extract from operation type
        operation = step.get("operation", "reasoning")

        # Create variable for the step itself
        var_name = f"step_{step_index}_{operation}"
        var_type = cls._classify_variable_type(operation, step)

        description = step.get("content", "")[:100]
        confidence = step.get("confidence", 0.8)

        variables.append(
            CausalVariable(
                name=var_name,
                var_type=var_type,
                description=description,
                confidence=confidence,
            )
        )

        # Extract from measurements
        if "measurements" in step:
            measurements = step["measurements"]
            for metric, value in measurements.items():
                if isinstance(value, (int, float)):
                    var = CausalVariable(
                        name=f"{var_name}_{metric}",
                        var_type="measurement",
                        description=f"{metric} measurement",
                        confidence=confidence,
                        observed_values=[value],
                    )
                    variables.append(var)

        return variables

    @classmethod
    def _classify_variable_type(cls, operation: str, step: Dict) -> str:
        """Classify a variable as action, condition, outcome, or context."""
        operation_lower = operation.lower()

        if any(
            keyword in operation_lower for keyword in ["decision", "choice", "action"]
        ):
            return "action"
        elif any(
            keyword in operation_lower for keyword in ["check", "verify", "validate"]
        ):
            return "condition"
        elif any(
            keyword in operation_lower
            for keyword in ["result", "outcome", "conclusion"]
        ):
            return "outcome"
        else:
            return "context"

    @classmethod
    def _extract_edges_from_step(
        cls, step: Dict, step_vars: List[CausalVariable], capsule_id: str
    ) -> List[CausalEdge]:
        """Extract causal edges from a step's content."""
        edges = []

        content = step.get("content", "")
        confidence = step.get("confidence", 0.8)

        # Check for explicit causal language
        has_causal_language = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in cls.CAUSAL_INDICATORS
        )

        if has_causal_language and len(step_vars) >= 2:
            # Create edge between variables in this step
            edge = CausalEdge(
                source=step_vars[0].name,
                target=step_vars[-1].name,
                edge_type="direct_cause",
                strength=confidence * 0.8,  # Discount for uncertainty
                evidence_capsule_ids=[capsule_id],
            )
            edges.append(edge)

        # Extract from alternatives considered (decision steps)
        if step.get("alternatives_considered"):
            main_var = step_vars[0] if step_vars else None
            if main_var:
                # Decision variables influence outcomes
                edge_type = "direct_cause"
                strength = confidence * 0.9

                for var in step_vars[1:]:
                    edge = CausalEdge(
                        source=main_var.name,
                        target=var.name,
                        edge_type=edge_type,
                        strength=strength,
                        evidence_capsule_ids=[capsule_id],
                    )
                    edges.append(edge)

        return edges

    @classmethod
    def _connect_sequential_steps(
        cls,
        prev_step: Dict,
        current_step: Dict,
        prev_index: int,
        current_index: int,
        graph: CausalGraph,
        capsule_id: str,
    ) -> None:
        """Create causal edges between sequential reasoning steps."""
        prev_operation = prev_step.get("operation", "reasoning")
        current_operation = current_step.get("operation", "reasoning")

        prev_var_name = f"step_{prev_index}_{prev_operation}"
        current_var_name = f"step_{current_index}_{current_operation}"

        # Check if both variables exist
        if (
            prev_var_name not in graph.variables
            or current_var_name not in graph.variables
        ):
            return

        # Determine edge strength based on confidence
        prev_confidence = prev_step.get("confidence", 0.8)
        current_confidence = current_step.get("confidence", 0.8)
        strength = (prev_confidence + current_confidence) / 2

        # Sequential steps have moderate causal influence
        edge = CausalEdge(
            source=prev_var_name,
            target=current_var_name,
            edge_type="direct_cause",
            strength=strength * 0.7,  # Discount for sequential uncertainty
            evidence_capsule_ids=[capsule_id],
        )

        try:
            graph.add_edge(edge)
        except ValueError:
            # Skip if would create cycle
            pass


# Example usage
if __name__ == "__main__":
    print("✅ Causal Graph Construction Ready")
    print("\nCapabilities:")
    print("  - Build causal DAGs from reasoning capsules")
    print("  - Extract causal variables and relationships")
    print("  - Find causal paths between variables")
    print("  - Identify root causes and terminal effects")
    print("  - Topological sorting of causal dependencies")
    print("  - Cycle detection and validation")
