"""
Learning Module
Meta-learning and strategy extraction from successful reasoning patterns
"""

from .meta_learning import (
    LearningUpdate,
    MetaLearningSystem,
    ReasoningStrategy,
    StrategyRecommendation,
)

__all__ = [
    "MetaLearningSystem",
    "ReasoningStrategy",
    "StrategyRecommendation",
    "LearningUpdate",
]
