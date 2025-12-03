"""
Machine Learning module for UATP Capsule Engine.
Provides intelligent analytics, predictions, and automated insights.
"""

from .analytics_engine import (
    AnalyticsCategory,
    AnalyticsResult,
    FeatureExtractor,
    MLAnalyticsEngine,
    MLModel,
    ModelType,
    PredictiveAnalyzer,
    ml_analytics,
)

__all__ = [
    "MLAnalyticsEngine",
    "FeatureExtractor",
    "PredictiveAnalyzer",
    "ModelType",
    "AnalyticsCategory",
    "AnalyticsResult",
    "MLModel",
    "ml_analytics",
]
