"""
reasoning - Enhanced reasoning fidelity module for UATP Capsule Engine.
Provides structured reasoning formats, validation, analysis, and causal inference capabilities.
"""

from .analyzer import ReasoningAnalyzer

# Causal reasoning components
from .causal_graph import (
    CausalEdge,
    CausalGraph,
    CausalGraphBuilder,
    CausalPath,
    CausalVariable,
)
from .causal_reasoning_engine import (
    CausalAnalysisResult,
    CausalInsight,
    CausalQuery,
    CausalReasoningEngine,
)
from .structural_causal_model import (
    CausalEffect,
    CausalMechanism,
    CounterfactualQuery,
    Intervention,
    StructuralCausalModel,
    linear_mechanism,
    logical_and_mechanism,
    probabilistic_mechanism,
    threshold_mechanism,
)
from .trace import ReasoningStep, ReasoningTrace
from .validator import ReasoningValidator

__all__ = [
    # Original exports
    "ReasoningTrace",
    "ReasoningStep",
    "ReasoningValidator",
    "ReasoningAnalyzer",
    # Causal Graph
    "CausalGraph",
    "CausalGraphBuilder",
    "CausalVariable",
    "CausalEdge",
    "CausalPath",
    # Structural Causal Model
    "StructuralCausalModel",
    "CausalMechanism",
    "Intervention",
    "CounterfactualQuery",
    "CausalEffect",
    "linear_mechanism",
    "threshold_mechanism",
    "logical_and_mechanism",
    "probabilistic_mechanism",
    # Causal Reasoning Engine
    "CausalReasoningEngine",
    "CausalInsight",
    "CausalQuery",
    "CausalAnalysisResult",
]
