"""
Unit tests for Causal Graph.
"""

import pytest

from src.reasoning.causal_graph import (
    CausalEdge,
    CausalGraph,
    CausalGraphBuilder,
    CausalPath,
    CausalVariable,
)


class TestCausalVariable:
    """Tests for CausalVariable dataclass."""

    def test_create_variable(self):
        """Test creating a causal variable."""
        var = CausalVariable(
            name="temperature",
            var_type="condition",
            description="Room temperature",
        )

        assert var.name == "temperature"
        assert var.var_type == "condition"
        assert var.description == "Room temperature"
        assert var.confidence == 1.0
        assert var.domain is None
        assert var.observed_values == []

    def test_variable_with_all_fields(self):
        """Test creating variable with all fields."""
        var = CausalVariable(
            name="action_1",
            var_type="action",
            description="User action",
            confidence=0.85,
            domain="user_behavior",
            observed_values=[1, 2, 3],
        )

        assert var.confidence == 0.85
        assert var.domain == "user_behavior"
        assert var.observed_values == [1, 2, 3]

    def test_variable_types(self):
        """Test different variable types."""
        types = ["action", "condition", "outcome", "context"]

        for var_type in types:
            var = CausalVariable(
                name=f"var_{var_type}",
                var_type=var_type,
                description=f"A {var_type} variable",
            )
            assert var.var_type == var_type


class TestCausalEdge:
    """Tests for CausalEdge dataclass."""

    def test_create_edge(self):
        """Test creating a causal edge."""
        edge = CausalEdge(
            source="cause",
            target="effect",
            edge_type="direct_cause",
            strength=0.9,
        )

        assert edge.source == "cause"
        assert edge.target == "effect"
        assert edge.edge_type == "direct_cause"
        assert edge.strength == 0.9
        assert edge.evidence_count == 1
        assert edge.evidence_capsule_ids == []

    def test_edge_with_evidence(self):
        """Test edge with evidence."""
        edge = CausalEdge(
            source="A",
            target="B",
            edge_type="confounding",
            strength=0.7,
            evidence_count=5,
            evidence_capsule_ids=["cap_1", "cap_2"],
        )

        assert edge.evidence_count == 5
        assert len(edge.evidence_capsule_ids) == 2

    def test_edge_types(self):
        """Test different edge types."""
        types = ["direct_cause", "confounding", "mediating"]

        for edge_type in types:
            edge = CausalEdge(
                source="X",
                target="Y",
                edge_type=edge_type,
                strength=0.5,
            )
            assert edge.edge_type == edge_type


class TestCausalPath:
    """Tests for CausalPath dataclass."""

    def test_create_path(self):
        """Test creating a causal path."""
        path = CausalPath(
            start="A",
            end="C",
            path=["A", "B", "C"],
            total_strength=0.72,
            path_type="indirect",
        )

        assert path.start == "A"
        assert path.end == "C"
        assert path.path == ["A", "B", "C"]
        assert path.total_strength == 0.72
        assert path.path_type == "indirect"

    def test_direct_path(self):
        """Test direct path."""
        path = CausalPath(
            start="X",
            end="Y",
            path=["X", "Y"],
            total_strength=0.9,
            path_type="direct",
        )

        assert len(path.path) == 2
        assert path.path_type == "direct"


class TestCausalGraph:
    """Tests for CausalGraph class."""

    @pytest.fixture
    def empty_graph(self):
        """Create an empty graph."""
        return CausalGraph()

    @pytest.fixture
    def simple_graph(self):
        """Create a simple graph: A -> B -> C."""
        graph = CausalGraph()

        # Add variables
        graph.add_variable(CausalVariable("A", "condition", "Variable A"))
        graph.add_variable(CausalVariable("B", "action", "Variable B"))
        graph.add_variable(CausalVariable("C", "outcome", "Variable C"))

        # Add edges
        graph.add_edge(CausalEdge("A", "B", "direct_cause", 0.9))
        graph.add_edge(CausalEdge("B", "C", "direct_cause", 0.8))

        return graph

    def test_create_empty_graph(self, empty_graph):
        """Test creating an empty graph."""
        assert len(empty_graph.variables) == 0
        assert len(empty_graph.edges) == 0

    def test_add_variable(self, empty_graph):
        """Test adding a variable."""
        var = CausalVariable("X", "action", "Test variable")
        empty_graph.add_variable(var)

        assert "X" in empty_graph.variables
        assert empty_graph.variables["X"].var_type == "action"

    def test_add_edge(self, empty_graph):
        """Test adding an edge."""
        empty_graph.add_variable(CausalVariable("A", "condition", "A"))
        empty_graph.add_variable(CausalVariable("B", "outcome", "B"))

        edge = CausalEdge("A", "B", "direct_cause", 0.8)
        empty_graph.add_edge(edge)

        assert len(empty_graph.edges) == 1
        assert empty_graph.adjacency["A"] == ["B"]
        assert empty_graph.reverse_adjacency["B"] == ["A"]

    def test_add_duplicate_edge_updates(self, empty_graph):
        """Test adding duplicate edge updates existing."""
        empty_graph.add_variable(CausalVariable("A", "condition", "A"))
        empty_graph.add_variable(CausalVariable("B", "outcome", "B"))

        empty_graph.add_edge(CausalEdge("A", "B", "direct_cause", 0.8))
        empty_graph.add_edge(
            CausalEdge("A", "B", "direct_cause", 0.6, evidence_capsule_ids=["cap_1"])
        )

        assert len(empty_graph.edges) == 1
        edge = empty_graph.edges[0]
        assert edge.evidence_count == 2
        assert "cap_1" in edge.evidence_capsule_ids

    def test_cycle_detection(self, empty_graph):
        """Test cycle detection prevents cycles."""
        empty_graph.add_variable(CausalVariable("A", "action", "A"))
        empty_graph.add_variable(CausalVariable("B", "action", "B"))
        empty_graph.add_variable(CausalVariable("C", "action", "C"))

        empty_graph.add_edge(CausalEdge("A", "B", "direct_cause", 0.8))
        empty_graph.add_edge(CausalEdge("B", "C", "direct_cause", 0.8))

        # Adding C -> A would create a cycle
        with pytest.raises(ValueError, match="would create a cycle"):
            empty_graph.add_edge(CausalEdge("C", "A", "direct_cause", 0.8))

    def test_get_parents(self, simple_graph):
        """Test getting parents of a variable."""
        parents_a = simple_graph.get_parents("A")
        parents_b = simple_graph.get_parents("B")
        parents_c = simple_graph.get_parents("C")

        assert parents_a == []
        assert parents_b == ["A"]
        assert parents_c == ["B"]

    def test_get_children(self, simple_graph):
        """Test getting children of a variable."""
        children_a = simple_graph.get_children("A")
        children_b = simple_graph.get_children("B")
        children_c = simple_graph.get_children("C")

        assert children_a == ["B"]
        assert children_b == ["C"]
        assert children_c == []

    def test_get_ancestors(self, simple_graph):
        """Test getting all ancestors."""
        ancestors_c = simple_graph.get_ancestors("C")

        assert "A" in ancestors_c
        assert "B" in ancestors_c
        assert len(ancestors_c) == 2

    def test_get_descendants(self, simple_graph):
        """Test getting all descendants."""
        descendants_a = simple_graph.get_descendants("A")

        assert "B" in descendants_a
        assert "C" in descendants_a
        assert len(descendants_a) == 2

    def test_find_all_paths(self, simple_graph):
        """Test finding all paths."""
        paths = simple_graph.find_all_paths("A", "C")

        assert len(paths) == 1
        assert paths[0].path == ["A", "B", "C"]
        assert paths[0].path_type == "indirect"

    def test_find_all_paths_direct(self, empty_graph):
        """Test finding direct path."""
        empty_graph.add_variable(CausalVariable("X", "action", "X"))
        empty_graph.add_variable(CausalVariable("Y", "outcome", "Y"))
        empty_graph.add_edge(CausalEdge("X", "Y", "direct_cause", 0.9))

        paths = empty_graph.find_all_paths("X", "Y")

        assert len(paths) == 1
        assert paths[0].path == ["X", "Y"]
        assert paths[0].path_type == "direct"

    def test_find_all_paths_no_path(self, simple_graph):
        """Test finding paths when none exist."""
        paths = simple_graph.find_all_paths("C", "A")

        assert len(paths) == 0

    def test_find_all_paths_nonexistent_variable(self, simple_graph):
        """Test finding paths with nonexistent variable."""
        paths = simple_graph.find_all_paths("A", "Z")

        assert len(paths) == 0

    def test_get_root_causes(self, simple_graph):
        """Test getting root causes."""
        roots = simple_graph.get_root_causes()

        assert roots == ["A"]

    def test_get_terminal_effects(self, simple_graph):
        """Test getting terminal effects."""
        terminals = simple_graph.get_terminal_effects()

        assert terminals == ["C"]

    def test_topological_sort(self, simple_graph):
        """Test topological sorting."""
        sorted_vars = simple_graph.topological_sort()

        # A must come before B, B must come before C
        assert sorted_vars.index("A") < sorted_vars.index("B")
        assert sorted_vars.index("B") < sorted_vars.index("C")

    def test_to_dict(self, simple_graph):
        """Test converting graph to dictionary."""
        result = simple_graph.to_dict()

        assert "variables" in result
        assert "edges" in result
        assert "statistics" in result

        assert len(result["variables"]) == 3
        assert len(result["edges"]) == 2
        assert result["statistics"]["num_variables"] == 3
        assert result["statistics"]["num_edges"] == 2

    def test_can_reach(self, simple_graph):
        """Test reachability check."""
        assert simple_graph._can_reach("A", "C") is True
        assert simple_graph._can_reach("C", "A") is False
        assert simple_graph._can_reach("A", "A") is True

    def test_find_edge(self, simple_graph):
        """Test finding an edge."""
        edge = simple_graph._find_edge("A", "B")

        assert edge is not None
        assert edge.source == "A"
        assert edge.target == "B"

    def test_find_edge_nonexistent(self, simple_graph):
        """Test finding nonexistent edge."""
        edge = simple_graph._find_edge("A", "C")

        assert edge is None


class TestCausalGraphComplex:
    """Tests for complex graph structures."""

    def test_diamond_structure(self):
        """Test diamond DAG: A -> B, A -> C, B -> D, C -> D."""
        graph = CausalGraph()

        for name in ["A", "B", "C", "D"]:
            graph.add_variable(CausalVariable(name, "action", f"Var {name}"))

        graph.add_edge(CausalEdge("A", "B", "direct_cause", 0.9))
        graph.add_edge(CausalEdge("A", "C", "direct_cause", 0.8))
        graph.add_edge(CausalEdge("B", "D", "direct_cause", 0.7))
        graph.add_edge(CausalEdge("C", "D", "direct_cause", 0.6))

        # Test paths
        paths = graph.find_all_paths("A", "D")
        assert len(paths) == 2

        # Test ancestors/descendants
        assert graph.get_ancestors("D") == {"A", "B", "C"}
        assert graph.get_descendants("A") == {"B", "C", "D"}

    def test_multiple_root_causes(self):
        """Test graph with multiple root causes."""
        graph = CausalGraph()

        for name in ["R1", "R2", "M", "E"]:
            graph.add_variable(CausalVariable(name, "action", f"Var {name}"))

        graph.add_edge(CausalEdge("R1", "M", "direct_cause", 0.8))
        graph.add_edge(CausalEdge("R2", "M", "direct_cause", 0.7))
        graph.add_edge(CausalEdge("M", "E", "direct_cause", 0.9))

        roots = graph.get_root_causes()
        assert set(roots) == {"R1", "R2"}

    def test_path_strength_calculation(self):
        """Test that path strength is calculated correctly."""
        graph = CausalGraph()

        for name in ["A", "B", "C"]:
            graph.add_variable(CausalVariable(name, "action", f"Var {name}"))

        graph.add_edge(CausalEdge("A", "B", "direct_cause", 0.8))
        graph.add_edge(CausalEdge("B", "C", "direct_cause", 0.5))

        paths = graph.find_all_paths("A", "C")

        assert len(paths) == 1
        # Strength should be 0.8 * 0.5 = 0.4
        assert paths[0].total_strength == pytest.approx(0.4, rel=0.01)


class TestCausalGraphBuilder:
    """Tests for CausalGraphBuilder class."""

    def test_causal_indicators_defined(self):
        """Test causal indicator patterns are defined."""
        assert len(CausalGraphBuilder.CAUSAL_INDICATORS) > 0

        # Check common patterns exist
        patterns_str = " ".join(CausalGraphBuilder.CAUSAL_INDICATORS)
        assert "because" in patterns_str
        assert "leads" in patterns_str

    def test_build_from_empty_capsules(self):
        """Test building from empty capsule list."""
        graph = CausalGraphBuilder.build_from_capsules([])

        assert len(graph.variables) == 0
        assert len(graph.edges) == 0

    def test_build_from_simple_capsule(self):
        """Test building from a simple capsule."""
        capsule = {
            "capsule_id": "cap_001",
            "payload": {
                "reasoning_steps": [
                    {
                        "operation": "observation",
                        "content": "Initial observation",
                        "confidence": 0.9,
                    },
                    {
                        "operation": "conclusion",
                        "content": "Final conclusion",
                        "confidence": 0.85,
                    },
                ]
            },
        }

        graph = CausalGraphBuilder.build_from_capsules([capsule])

        assert len(graph.variables) >= 2

    def test_classify_variable_type_action(self):
        """Test classifying action variable."""
        var_type = CausalGraphBuilder._classify_variable_type(
            "decision_made", {"content": "test"}
        )
        assert var_type == "action"

    def test_classify_variable_type_condition(self):
        """Test classifying condition variable."""
        var_type = CausalGraphBuilder._classify_variable_type(
            "validate_input", {"content": "test"}
        )
        assert var_type == "condition"

    def test_classify_variable_type_outcome(self):
        """Test classifying outcome variable."""
        var_type = CausalGraphBuilder._classify_variable_type(
            "final_result", {"content": "test"}
        )
        assert var_type == "outcome"

    def test_classify_variable_type_context(self):
        """Test classifying context variable."""
        var_type = CausalGraphBuilder._classify_variable_type(
            "analysis", {"content": "test"}
        )
        assert var_type == "context"

    def test_extract_variables_from_step(self):
        """Test extracting variables from a step."""
        step = {
            "operation": "decision",
            "content": "Make a decision about X",
            "confidence": 0.9,
        }

        variables = CausalGraphBuilder._extract_variables_from_step(step, 0, "cap_1")

        assert len(variables) >= 1
        assert variables[0].name == "step_0_decision"
        assert variables[0].var_type == "action"

    def test_extract_variables_with_measurements(self):
        """Test extracting variables from step with measurements."""
        step = {
            "operation": "analysis",
            "content": "Analyze metrics",
            "confidence": 0.8,
            "measurements": {"accuracy": 0.95, "latency": 150},
        }

        variables = CausalGraphBuilder._extract_variables_from_step(step, 0, "cap_1")

        # Should have main variable + measurement variables
        assert len(variables) >= 3

    def test_extract_edges_with_causal_language(self):
        """Test extracting edges from step with causal language."""
        step = {
            "operation": "analysis",
            "content": "This happens because of X",
            "confidence": 0.8,
        }

        variables = [
            CausalVariable("var1", "action", "Var 1"),
            CausalVariable("var2", "outcome", "Var 2"),
        ]

        edges = CausalGraphBuilder._extract_edges_from_step(step, variables, "cap_1")

        assert len(edges) >= 1

    def test_build_preserves_capsule_ids(self):
        """Test that capsule IDs are preserved in edges."""
        capsule = {
            "capsule_id": "test_capsule_123",
            "payload": {
                "reasoning_steps": [
                    {
                        "operation": "start",
                        "content": "Because X leads to Y",
                        "confidence": 0.9,
                    },
                    {
                        "operation": "end",
                        "content": "Therefore conclusion",
                        "confidence": 0.85,
                    },
                ]
            },
        }

        graph = CausalGraphBuilder.build_from_capsules([capsule])

        # Check that edges have capsule ID
        for edge in graph.edges:
            assert "test_capsule_123" in edge.evidence_capsule_ids


class TestCausalGraphBuilderIntegration:
    """Integration tests for building graphs from multiple capsules."""

    def test_build_from_multiple_capsules(self):
        """Test building from multiple capsules."""
        capsules = [
            {
                "capsule_id": "cap_1",
                "payload": {
                    "reasoning_steps": [
                        {
                            "operation": "observation",
                            "content": "Observed A",
                            "confidence": 0.9,
                        },
                    ]
                },
            },
            {
                "capsule_id": "cap_2",
                "payload": {
                    "reasoning_steps": [
                        {
                            "operation": "observation",
                            "content": "Observed B",
                            "confidence": 0.85,
                        },
                    ]
                },
            },
        ]

        graph = CausalGraphBuilder.build_from_capsules(capsules)

        # Variables use step index + operation for naming, so same index/op
        # across capsules will be the same variable (expected behavior)
        assert len(graph.variables) >= 1

    def test_handles_non_dict_steps(self):
        """Test handling of non-dict reasoning steps."""
        capsule = {
            "capsule_id": "cap_1",
            "payload": {
                "reasoning_steps": [
                    "string step",  # Non-dict
                    123,  # Non-dict
                    {"operation": "valid", "content": "Valid step", "confidence": 0.9},
                ]
            },
        }

        # Should not raise
        graph = CausalGraphBuilder.build_from_capsules([capsule])

        # Should have processed the valid step
        assert len(graph.variables) >= 1

    def test_handles_missing_payload(self):
        """Test handling capsule without payload."""
        capsule = {"capsule_id": "cap_1"}

        # Should not raise
        graph = CausalGraphBuilder.build_from_capsules([capsule])

        assert len(graph.variables) == 0
