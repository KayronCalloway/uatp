"""
Explainable AI Layer

Provides detailed explanations, confidence scoring, and reasoning traces for AI decisions.

Key Features:
1. Decision justification generation
2. Confidence score breakdown
3. Feature importance analysis
4. Reasoning trace visualization
5. Counterfactual explanations ("what if" scenarios)
6. Model uncertainty quantification

Usage:
    from src.explainability import DecisionExplainer

    explainer = DecisionExplainer()

    # Explain a decision
    explanation = await explainer.explain_decision(
        decision={
            "domain": "medical",
            "type": "diagnosis",
            "recommendation": "Type 2 Diabetes",
            "confidence": 0.92
        },
        reasoning_trace=[...],
        model_features={
            "a1c_level": 7.2,
            "fasting_glucose": 140,
            "symptoms": ["polyuria", "polydipsia"]
        }
    )

    # Result:
    # - Natural language explanation
    # - Confidence breakdown by factor
    # - Feature importance scores
    # - Alternative scenarios
    # - Uncertainty quantification
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
import json
import logging
import secrets

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceBreakdown:
    """Breakdown of confidence score by contributing factors"""

    overall_confidence: float
    factors: List[Dict[str, Any]]  # [{name, score, weight, description}]
    uncertainty_sources: List[str]
    confidence_interval: Tuple[float, float]  # (lower, upper)


@dataclass
class FeatureImportance:
    """Importance scores for input features"""

    feature_name: str
    importance_score: float  # 0-1
    feature_value: Any
    impact_direction: str  # "positive", "negative", "neutral"
    explanation: str


@dataclass
class CounterfactualScenario:
    """Alternative scenario analysis"""

    scenario_id: str
    description: str
    changed_features: Dict[str, Any]
    predicted_outcome: str
    confidence: float
    explanation: str


@dataclass
class DecisionExplanation:
    """Complete explanation of an AI decision"""

    explanation_id: str
    decision_summary: str
    natural_language_explanation: str
    confidence_breakdown: ConfidenceBreakdown
    feature_importance: List[FeatureImportance]
    reasoning_steps: List[str]
    key_evidence: List[str]
    counterfactuals: List[CounterfactualScenario]
    limitations: List[str]
    recommended_actions: List[str]
    timestamp: str
    metadata: Dict[str, Any]


class DecisionExplainer:
    """
    Generates human-understandable explanations for AI decisions.

    This system provides:
    1. Natural language explanations
    2. Confidence score breakdowns
    3. Feature importance analysis
    4. Reasoning trace interpretation
    5. Counterfactual scenarios
    6. Uncertainty quantification
    """

    def __init__(self, storage_path: str = "explainability/explanations"):
        """
        Initialize decision explainer.

        Args:
            storage_path: Directory for storing explanations
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def explain_decision(
        self,
        decision: Dict[str, Any],
        reasoning_trace: Optional[List[Dict[str, Any]]] = None,
        model_features: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> DecisionExplanation:
        """
        Generate comprehensive explanation for a decision.

        Args:
            decision: Decision details (domain, type, recommendation, confidence)
            reasoning_trace: Step-by-step reasoning process
            model_features: Input features used in decision
            context: Additional context

        Returns:
            DecisionExplanation object
        """
        explanation_id = f"exp_{secrets.token_hex(16)}"
        reasoning_trace = reasoning_trace or []
        model_features = model_features or {}
        context = context or {}

        # Extract decision details
        domain = decision.get("domain", "general")
        decision_type = decision.get("type", "unknown")
        recommendation = decision.get("recommendation", "")
        confidence = float(decision.get("confidence", 0.0))

        # Generate natural language explanation
        nl_explanation = self._generate_natural_language_explanation(
            domain=domain,
            decision_type=decision_type,
            recommendation=recommendation,
            model_features=model_features,
            reasoning_trace=reasoning_trace,
        )

        # Analyze confidence
        confidence_breakdown = self._analyze_confidence(
            confidence=confidence,
            model_features=model_features,
            reasoning_trace=reasoning_trace,
        )

        # Calculate feature importance
        feature_importance = self._calculate_feature_importance(
            model_features=model_features, decision=decision
        )

        # Extract reasoning steps
        reasoning_steps = self._extract_reasoning_steps(reasoning_trace)

        # Identify key evidence
        key_evidence = self._identify_key_evidence(
            model_features=model_features, feature_importance=feature_importance
        )

        # Generate counterfactuals
        counterfactuals = self._generate_counterfactuals(
            decision=decision,
            model_features=model_features,
            feature_importance=feature_importance,
        )

        # Identify limitations
        limitations = self._identify_limitations(
            confidence=confidence, model_features=model_features, domain=domain
        )

        # Generate recommendations
        recommended_actions = self._generate_recommendations(
            decision=decision, confidence_breakdown=confidence_breakdown, domain=domain
        )

        explanation = DecisionExplanation(
            explanation_id=explanation_id,
            decision_summary=f"{domain.upper()}: {recommendation}",
            natural_language_explanation=nl_explanation,
            confidence_breakdown=confidence_breakdown,
            feature_importance=feature_importance,
            reasoning_steps=reasoning_steps,
            key_evidence=key_evidence,
            counterfactuals=counterfactuals,
            limitations=limitations,
            recommended_actions=recommended_actions,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                "domain": domain,
                "decision_type": decision_type,
                "confidence": confidence,
            },
        )

        # Save explanation
        self._save_explanation(explanation)

        logger.info(
            f"Generated explanation {explanation_id} for {domain} decision "
            f"(confidence: {confidence:.2%})"
        )

        return explanation

    def _generate_natural_language_explanation(
        self,
        domain: str,
        decision_type: str,
        recommendation: str,
        model_features: Dict[str, Any],
        reasoning_trace: List[Dict[str, Any]],
    ) -> str:
        """Generate human-readable explanation"""

        # Domain-specific explanation templates
        if domain == "medical":
            return self._medical_explanation(
                decision_type, recommendation, model_features, reasoning_trace
            )
        elif domain == "financial":
            return self._financial_explanation(
                decision_type, recommendation, model_features, reasoning_trace
            )
        elif domain == "legal":
            return self._legal_explanation(
                decision_type, recommendation, model_features, reasoning_trace
            )
        elif domain == "autonomous":
            return self._autonomous_explanation(
                decision_type, recommendation, model_features, reasoning_trace
            )
        else:
            return self._generic_explanation(
                decision_type, recommendation, model_features, reasoning_trace
            )

    def _medical_explanation(
        self,
        decision_type: str,
        recommendation: str,
        features: Dict[str, Any],
        trace: List[Dict[str, Any]],
    ) -> str:
        """Generate medical decision explanation"""

        explanation_parts = [
            f"The AI recommends: {recommendation}",
            "",
            "This recommendation is based on:",
        ]

        # Add feature-based reasoning
        if "a1c_level" in features:
            explanation_parts.append(
                f"- A1C level of {features['a1c_level']}% (elevated above normal range of 4.0-5.6%)"
            )

        if "fasting_glucose" in features:
            explanation_parts.append(
                f"- Fasting glucose of {features['fasting_glucose']} mg/dL (above normal range of 70-99 mg/dL)"
            )

        if "symptoms" in features:
            symptoms = features["symptoms"]
            if isinstance(symptoms, list):
                explanation_parts.append(
                    f"- Patient-reported symptoms: {', '.join(symptoms)}"
                )

        if "vital_signs" in features:
            explanation_parts.append(f"- Vital signs: {features['vital_signs']}")

        # Add reasoning trace summary
        if trace:
            explanation_parts.append("")
            explanation_parts.append("Clinical reasoning process:")
            for i, step in enumerate(trace[:3], 1):  # Show first 3 steps
                content = step.get("content", "")
                if content:
                    explanation_parts.append(f"{i}. {content}")

        return "\n".join(explanation_parts)

    def _financial_explanation(
        self,
        decision_type: str,
        recommendation: str,
        features: Dict[str, Any],
        trace: List[Dict[str, Any]],
    ) -> str:
        """Generate financial decision explanation"""

        explanation_parts = [
            f"The AI recommends: {recommendation}",
            "",
            "This recommendation is based on:",
        ]

        if "amount_usd" in features:
            explanation_parts.append(
                f"- Transaction amount: ${features['amount_usd']:,.2f}"
            )

        if "risk_score" in features:
            explanation_parts.append(
                f"- Risk assessment score: {features['risk_score']}/100"
            )

        if "market_conditions" in features:
            explanation_parts.append(
                f"- Market conditions: {features['market_conditions']}"
            )

        if "portfolio_impact" in features:
            explanation_parts.append(
                f"- Portfolio impact: {features['portfolio_impact']}"
            )

        return "\n".join(explanation_parts)

    def _legal_explanation(
        self,
        decision_type: str,
        recommendation: str,
        features: Dict[str, Any],
        trace: List[Dict[str, Any]],
    ) -> str:
        """Generate legal decision explanation"""

        explanation_parts = [
            f"The AI recommends: {recommendation}",
            "",
            "This recommendation is based on:",
        ]

        if "contract_type" in features:
            explanation_parts.append(f"- Contract type: {features['contract_type']}")

        if "jurisdiction" in features:
            explanation_parts.append(f"- Jurisdiction: {features['jurisdiction']}")

        if "precedents" in features:
            precedents = features["precedents"]
            if isinstance(precedents, list):
                explanation_parts.append(
                    f"- Relevant precedents: {len(precedents)} cases reviewed"
                )

        if "compliance_issues" in features:
            explanation_parts.append(
                f"- Compliance considerations: {features['compliance_issues']}"
            )

        return "\n".join(explanation_parts)

    def _autonomous_explanation(
        self,
        decision_type: str,
        recommendation: str,
        features: Dict[str, Any],
        trace: List[Dict[str, Any]],
    ) -> str:
        """Generate autonomous system explanation"""

        explanation_parts = [
            f"The AI recommends: {recommendation}",
            "",
            "This recommendation is based on:",
        ]

        if "speed_mph" in features:
            explanation_parts.append(f"- Current speed: {features['speed_mph']} mph")

        if "obstacle_distance" in features:
            explanation_parts.append(
                f"- Obstacle distance: {features['obstacle_distance']} meters"
            )

        if "lane_status" in features:
            explanation_parts.append(f"- Lane status: {features['lane_status']}")

        if "sensor_data" in features:
            explanation_parts.append(
                f"- Sensor confidence: {features.get('sensor_confidence', 'high')}"
            )

        return "\n".join(explanation_parts)

    def _generic_explanation(
        self,
        decision_type: str,
        recommendation: str,
        features: Dict[str, Any],
        trace: List[Dict[str, Any]],
    ) -> str:
        """Generate generic decision explanation"""

        explanation_parts = [
            f"The AI recommends: {recommendation}",
            "",
            "This recommendation is based on the following factors:",
        ]

        for key, value in features.items():
            explanation_parts.append(f"- {key.replace('_', ' ').title()}: {value}")

        return "\n".join(explanation_parts)

    def _analyze_confidence(
        self,
        confidence: float,
        model_features: Dict[str, Any],
        reasoning_trace: List[Dict[str, Any]],
    ) -> ConfidenceBreakdown:
        """Analyze and break down confidence score"""

        factors = []

        # Data quality factor
        data_completeness = len(model_features) / max(10, len(model_features))
        factors.append(
            {
                "name": "Data Quality",
                "score": min(data_completeness, 1.0),
                "weight": 0.3,
                "description": f"{len(model_features)} features available for analysis",
            }
        )

        # Model certainty factor
        model_certainty = confidence
        factors.append(
            {
                "name": "Model Certainty",
                "score": model_certainty,
                "weight": 0.4,
                "description": f"Model is {confidence:.1%} confident in this prediction",
            }
        )

        # Reasoning depth factor
        reasoning_depth = min(len(reasoning_trace) / 5, 1.0) if reasoning_trace else 0.5
        factors.append(
            {
                "name": "Reasoning Depth",
                "score": reasoning_depth,
                "weight": 0.3,
                "description": f"Analysis included {len(reasoning_trace)} reasoning steps",
            }
        )

        # Identify uncertainty sources
        uncertainty_sources = []
        if confidence < 0.9:
            uncertainty_sources.append("Model confidence below 90%")
        if len(model_features) < 5:
            uncertainty_sources.append("Limited input data available")
        if not reasoning_trace:
            uncertainty_sources.append("No detailed reasoning trace available")

        # Calculate confidence interval
        margin = (1.0 - confidence) * 0.5
        confidence_interval = (
            max(0.0, confidence - margin),
            min(1.0, confidence + margin),
        )

        return ConfidenceBreakdown(
            overall_confidence=confidence,
            factors=factors,
            uncertainty_sources=uncertainty_sources,
            confidence_interval=confidence_interval,
        )

    def _calculate_feature_importance(
        self, model_features: Dict[str, Any], decision: Dict[str, Any]
    ) -> List[FeatureImportance]:
        """Calculate importance of each feature"""

        feature_importance_list = []

        # Simple heuristic-based importance (in production, use SHAP or LIME)
        for feature_name, feature_value in model_features.items():
            # Estimate importance based on feature type and value
            importance_score = 0.5  # Default

            # Domain-specific importance
            domain = decision.get("domain", "")

            if domain == "medical":
                if "a1c" in feature_name.lower():
                    importance_score = 0.9
                elif "glucose" in feature_name.lower():
                    importance_score = 0.85
                elif "symptom" in feature_name.lower():
                    importance_score = 0.7

            elif domain == "financial":
                if "amount" in feature_name.lower():
                    importance_score = 0.9
                elif "risk" in feature_name.lower():
                    importance_score = 0.85

            # Determine impact direction
            impact_direction = "positive"  # Simplified

            # Generate explanation
            explanation = (
                f"{feature_name.replace('_', ' ').title()} contributes to the decision"
            )

            feature_importance_list.append(
                FeatureImportance(
                    feature_name=feature_name,
                    importance_score=importance_score,
                    feature_value=feature_value,
                    impact_direction=impact_direction,
                    explanation=explanation,
                )
            )

        # Sort by importance
        feature_importance_list.sort(key=lambda x: x.importance_score, reverse=True)

        return feature_importance_list

    def _extract_reasoning_steps(
        self, reasoning_trace: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract clear reasoning steps from trace"""

        steps = []

        for trace_item in reasoning_trace:
            content = trace_item.get("content", "")
            if content and isinstance(content, str):
                # Clean and format step
                step = content.strip()
                if step and not step.startswith("Step"):
                    step = f"Step {len(steps) + 1}: {step}"
                steps.append(step)

        return steps[:10]  # Return first 10 steps

    def _identify_key_evidence(
        self,
        model_features: Dict[str, Any],
        feature_importance: List[FeatureImportance],
    ) -> List[str]:
        """Identify most important evidence for decision"""

        evidence = []

        # Take top 5 most important features
        for feat in feature_importance[:5]:
            evidence.append(
                f"{feat.feature_name.replace('_', ' ').title()}: {feat.feature_value}"
            )

        return evidence

    def _generate_counterfactuals(
        self,
        decision: Dict[str, Any],
        model_features: Dict[str, Any],
        feature_importance: List[FeatureImportance],
    ) -> List[CounterfactualScenario]:
        """Generate 'what if' alternative scenarios"""

        counterfactuals = []

        # Generate 2-3 counterfactual scenarios based on top features
        for i, feat in enumerate(feature_importance[:3], 1):
            scenario_id = f"cf_{secrets.token_hex(8)}"

            # Create alternative scenario
            if isinstance(feat.feature_value, (int, float)):
                # Numerical feature - show what if it was different
                alternative_value = feat.feature_value * 0.8  # 20% lower

                counterfactuals.append(
                    CounterfactualScenario(
                        scenario_id=scenario_id,
                        description=f"What if {feat.feature_name} was {alternative_value:.1f} instead?",
                        changed_features={feat.feature_name: alternative_value},
                        predicted_outcome="Different recommendation likely",
                        confidence=0.7,
                        explanation=f"Reducing {feat.feature_name} might change the recommendation",
                    )
                )

        return counterfactuals

    def _identify_limitations(
        self, confidence: float, model_features: Dict[str, Any], domain: str
    ) -> List[str]:
        """Identify limitations of the decision"""

        limitations = []

        if confidence < 0.95:
            limitations.append(
                f"Model confidence is {confidence:.1%}, indicating some uncertainty"
            )

        if len(model_features) < 5:
            limitations.append("Limited input data may affect decision quality")

        # Domain-specific limitations
        if domain == "medical":
            limitations.append(
                "AI recommendations should be reviewed by licensed medical professionals"
            )
            limitations.append(
                "Individual patient circumstances may require different approaches"
            )

        elif domain == "financial":
            limitations.append(
                "Market conditions can change rapidly, affecting recommendation validity"
            )

        elif domain == "legal":
            limitations.append(
                "Legal advice should be reviewed by qualified legal counsel"
            )

        elif domain == "autonomous":
            limitations.append(
                "Sensor data quality and environmental conditions affect decision reliability"
            )

        return limitations

    def _generate_recommendations(
        self,
        decision: Dict[str, Any],
        confidence_breakdown: ConfidenceBreakdown,
        domain: str,
    ) -> List[str]:
        """Generate recommended actions based on decision"""

        recommendations = []

        confidence = confidence_breakdown.overall_confidence

        if confidence < 0.9:
            recommendations.append(
                "Consider seeking additional expert review due to moderate confidence level"
            )

        if confidence_breakdown.uncertainty_sources:
            recommendations.append(
                "Address uncertainty sources: "
                + ", ".join(confidence_breakdown.uncertainty_sources[:2])
            )

        # Domain-specific recommendations
        if domain == "medical":
            recommendations.append(
                "Consult with medical professional before implementing recommendation"
            )
            recommendations.append(
                "Monitor patient response and adjust treatment as needed"
            )

        elif domain == "financial":
            recommendations.append("Review current market conditions before executing")
            recommendations.append("Consider portfolio diversification impact")

        elif domain == "legal":
            recommendations.append("Have legal counsel review before finalizing")

        elif domain == "autonomous":
            recommendations.append("Verify sensor data accuracy")
            recommendations.append("Have backup plan ready if conditions change")

        return recommendations

    def _save_explanation(self, explanation: DecisionExplanation):
        """Save explanation to storage"""
        file_path = self.storage_path / "explanations.jsonl"

        # Convert to dict for JSON serialization
        exp_dict = asdict(explanation)

        with open(file_path, "a") as f:
            f.write(json.dumps(exp_dict) + "\n")


# Global decision explainer
decision_explainer = DecisionExplainer()
