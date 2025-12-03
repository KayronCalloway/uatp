"""
Explainability System

Provides human-understandable explanations for AI decisions.

Components:
- Decision Explainer (src/explainability/decision_explainer.py)
- Confidence Breakdown
- Feature Importance Analysis
- Counterfactual Scenarios
- Reasoning Trace Interpretation

Usage:
    from src.explainability import decision_explainer

    # Explain a decision
    explanation = await decision_explainer.explain_decision(
        decision={
            "domain": "medical",
            "type": "diagnosis",
            "recommendation": "Type 2 Diabetes",
            "confidence": 0.92
        },
        model_features={
            "a1c_level": 7.2,
            "fasting_glucose": 140
        }
    )

    # Access explanation components
    print(explanation.natural_language_explanation)
    print(f"Confidence: {explanation.confidence_breakdown.overall_confidence:.2%}")
    for feature in explanation.feature_importance:
        print(f"- {feature.feature_name}: {feature.importance_score:.2f}")
"""

from .decision_explainer import (
    DecisionExplainer,
    decision_explainer,
    DecisionExplanation,
    ConfidenceBreakdown,
    FeatureImportance,
    CounterfactualScenario,
)

__all__ = [
    "DecisionExplainer",
    "decision_explainer",
    "DecisionExplanation",
    "ConfidenceBreakdown",
    "FeatureImportance",
    "CounterfactualScenario",
]
