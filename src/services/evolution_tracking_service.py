"""
Evolution Tracking Service for UATP Capsule Engine

This service tracks value drift and model evolution over time, providing
comprehensive monitoring of AI model behavioral changes and alignment.
"""

import logging
import uuid
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from src.capsule_schema import (
    EvolutionCapsule,
    EvolutionPayload,
    CapsuleStatus,
    Verification,
)

logger = logging.getLogger(__name__)


@dataclass
class ModelSnapshot:
    """Represents a model state snapshot for comparison."""

    model_id: str
    snapshot_id: str
    timestamp: datetime
    behavioral_vectors: Dict[str, float]
    value_embeddings: Dict[str, float]
    performance_metrics: Dict[str, float]
    training_metadata: Dict[str, Any]
    version: str


@dataclass
class DriftAlert:
    """Represents a detected drift event requiring attention."""

    alert_id: str
    model_id: str
    drift_type: str
    severity: str
    drift_score: float
    detected_at: datetime
    description: str
    recommended_actions: List[str]
    affected_behaviors: List[str]


class EvolutionTrackingService:
    """Service for tracking model evolution and value drift."""

    def __init__(self):
        self.model_snapshots: Dict[str, List[ModelSnapshot]] = defaultdict(list)
        self.baseline_models: Dict[str, str] = {}  # model_id -> baseline_snapshot_id
        self.drift_thresholds: Dict[str, float] = self._init_drift_thresholds()
        self.active_alerts: Dict[str, DriftAlert] = {}
        self.evolution_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.monitoring_config: Dict[str, Any] = self._init_monitoring_config()

    def _init_drift_thresholds(self) -> Dict[str, float]:
        """Initialize drift detection thresholds."""
        return {
            "value_drift_critical": 0.8,
            "value_drift_high": 0.6,
            "value_drift_medium": 0.4,
            "value_drift_low": 0.2,
            "behavioral_drift_critical": 0.7,
            "behavioral_drift_high": 0.5,
            "behavioral_drift_medium": 0.3,
            "performance_degradation": 0.15,
            "alignment_drift": 0.3,
            "bias_emergence": 0.25,
        }

    def _init_monitoring_config(self) -> Dict[str, Any]:
        """Initialize monitoring configuration."""
        return {
            "snapshot_frequency_hours": 24,
            "comparison_window_days": 30,
            "alert_cooldown_hours": 6,
            "auto_remediation": False,
            "value_dimensions": [
                "fairness",
                "autonomy",
                "harm_prevention",
                "transparency",
                "privacy",
                "accountability",
                "beneficence",
                "human_dignity",
            ],
            "behavioral_categories": [
                "reasoning",
                "creativity",
                "social_interaction",
                "decision_making",
                "knowledge_application",
                "ethical_judgment",
                "bias_mitigation",
            ],
        }

    def create_model_snapshot(
        self,
        model_id: str,
        behavioral_vectors: Dict[str, float],
        value_embeddings: Dict[str, float],
        performance_metrics: Dict[str, float],
        training_metadata: Optional[Dict[str, Any]] = None,
        version: str = "1.0",
    ) -> ModelSnapshot:
        """Create a snapshot of current model state."""

        snapshot_id = f"snapshot_{uuid.uuid4().hex[:16]}"

        snapshot = ModelSnapshot(
            model_id=model_id,
            snapshot_id=snapshot_id,
            timestamp=datetime.now(timezone.utc),
            behavioral_vectors=behavioral_vectors.copy(),
            value_embeddings=value_embeddings.copy(),
            performance_metrics=performance_metrics.copy(),
            training_metadata=training_metadata or {},
            version=version,
        )

        self.model_snapshots[model_id].append(snapshot)

        # Set as baseline if first snapshot
        if model_id not in self.baseline_models:
            self.baseline_models[model_id] = snapshot_id
            logger.info(f"Set snapshot {snapshot_id} as baseline for model {model_id}")

        logger.info(f"Created snapshot {snapshot_id} for model {model_id}")
        return snapshot

    def detect_evolution(
        self, model_id: str, comparison_snapshot_id: Optional[str] = None
    ) -> EvolutionCapsule:
        """Detect and analyze model evolution."""

        if (
            model_id not in self.model_snapshots
            or len(self.model_snapshots[model_id]) < 2
        ):
            raise ValueError(
                f"Insufficient snapshots for model {model_id} to detect evolution"
            )

        snapshots = self.model_snapshots[model_id]
        current_snapshot = snapshots[-1]

        # Determine comparison snapshot
        if comparison_snapshot_id:
            comparison_snapshot = next(
                (s for s in snapshots if s.snapshot_id == comparison_snapshot_id), None
            )
            if not comparison_snapshot:
                raise ValueError(
                    f"Comparison snapshot {comparison_snapshot_id} not found"
                )
        else:
            # Use baseline or previous snapshot
            baseline_id = self.baseline_models.get(model_id)
            if baseline_id:
                comparison_snapshot = next(
                    (s for s in snapshots if s.snapshot_id == baseline_id), snapshots[0]
                )
            else:
                comparison_snapshot = snapshots[-2]

        # Calculate evolution metrics
        evolution_analysis = self._analyze_evolution(
            current_snapshot, comparison_snapshot
        )

        # Create evolution capsule
        capsule = self._create_evolution_capsule(
            model_id, current_snapshot, comparison_snapshot, evolution_analysis
        )

        # Check for alerts
        self._check_drift_alerts(model_id, evolution_analysis)

        # Record evolution history
        self.evolution_history[model_id].append(
            {
                "timestamp": datetime.now(timezone.utc),
                "capsule_id": capsule.capsule_id,
                "drift_score": evolution_analysis["value_drift_score"],
                "evolution_type": evolution_analysis["evolution_type"],
                "comparison_snapshot": comparison_snapshot.snapshot_id,
            }
        )

        return capsule

    def _analyze_evolution(
        self, current: ModelSnapshot, baseline: ModelSnapshot
    ) -> Dict[str, Any]:
        """Analyze evolution between two snapshots."""

        # Calculate value drift
        value_drift = self._calculate_value_drift(
            current.value_embeddings, baseline.value_embeddings
        )

        # Calculate behavioral drift
        behavioral_drift = self._calculate_behavioral_drift(
            current.behavioral_vectors, baseline.behavioral_vectors
        )

        # Calculate performance changes
        performance_changes = self._calculate_performance_changes(
            current.performance_metrics, baseline.performance_metrics
        )

        # Determine evolution type
        evolution_type = self._classify_evolution_type(
            value_drift["score"], behavioral_drift["score"], performance_changes
        )

        # Detect specific changes
        detected_changes = self._detect_specific_changes(
            current, baseline, value_drift, behavioral_drift
        )

        # Generate recommendations
        recommendations = self._generate_mitigation_recommendations(
            evolution_type, value_drift, behavioral_drift, performance_changes
        )

        return {
            "evolution_type": evolution_type,
            "value_drift_score": value_drift["score"],
            "behavioral_drift_score": behavioral_drift["score"],
            "drift_direction": value_drift["directions"]
            + behavioral_drift["directions"],
            "detected_changes": detected_changes,
            "evolution_metrics": {
                "value_drift": value_drift,
                "behavioral_drift": behavioral_drift,
                "performance_delta": performance_changes,
            },
            "confidence_level": self._calculate_confidence(
                value_drift, behavioral_drift
            ),
            "contributing_factors": self._identify_contributing_factors(
                current, baseline
            ),
            "mitigation_recommendations": recommendations,
            "alignment_impact": self._assess_alignment_impact(
                value_drift, behavioral_drift
            ),
        }

    def _calculate_value_drift(
        self, current_values: Dict[str, float], baseline_values: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate value drift between two value embedding sets."""

        drift_vectors = {}
        directions = []

        for dimension in self.monitoring_config["value_dimensions"]:
            current_val = current_values.get(dimension, 0.0)
            baseline_val = baseline_values.get(dimension, 0.0)
            drift = abs(current_val - baseline_val)
            drift_vectors[dimension] = drift

            if drift > self.drift_thresholds["value_drift_medium"]:
                direction = "increase" if current_val > baseline_val else "decrease"
                directions.append(f"{dimension}_{direction}")

        # Calculate overall drift score
        overall_drift = np.mean(list(drift_vectors.values()))

        return {
            "score": min(overall_drift, 1.0),
            "dimensions": drift_vectors,
            "directions": directions,
            "max_drift_dimension": max(
                drift_vectors.keys(), key=lambda k: drift_vectors[k]
            ),
        }

    def _calculate_behavioral_drift(
        self, current_behaviors: Dict[str, float], baseline_behaviors: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate behavioral drift between two behavioral vector sets."""

        drift_vectors = {}
        directions = []

        for category in self.monitoring_config["behavioral_categories"]:
            current_val = current_behaviors.get(category, 0.0)
            baseline_val = baseline_behaviors.get(category, 0.0)
            drift = abs(current_val - baseline_val)
            drift_vectors[category] = drift

            if drift > self.drift_thresholds["behavioral_drift_medium"]:
                direction = "increase" if current_val > baseline_val else "decrease"
                directions.append(f"{category}_{direction}")

        # Calculate overall drift score
        overall_drift = np.mean(list(drift_vectors.values()))

        return {
            "score": min(overall_drift, 1.0),
            "categories": drift_vectors,
            "directions": directions,
            "max_drift_category": max(
                drift_vectors.keys(), key=lambda k: drift_vectors[k]
            ),
        }

    def _calculate_performance_changes(
        self, current_perf: Dict[str, float], baseline_perf: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate performance metric changes."""

        changes = {}
        for metric, current_val in current_perf.items():
            baseline_val = baseline_perf.get(metric, 0.0)
            change = (current_val - baseline_val) / max(
                baseline_val, 0.001
            )  # Prevent division by zero
            changes[metric] = change

        return changes

    def _classify_evolution_type(
        self,
        value_drift: float,
        behavioral_drift: float,
        performance_changes: Dict[str, float],
    ) -> str:
        """Classify the type of evolution detected."""

        avg_perf_change = np.mean(list(performance_changes.values()))

        if value_drift > self.drift_thresholds["value_drift_high"]:
            if avg_perf_change < -self.drift_thresholds["performance_degradation"]:
                return "value_degradation"
            else:
                return "value_drift"

        elif behavioral_drift > self.drift_thresholds["behavioral_drift_high"]:
            if avg_perf_change > self.drift_thresholds["performance_degradation"]:
                return "adaptive_evolution"
            else:
                return "behavioral_drift"

        elif avg_perf_change > self.drift_thresholds["performance_degradation"]:
            return "performance_improvement"

        elif avg_perf_change < -self.drift_thresholds["performance_degradation"]:
            return "performance_degradation"

        elif (
            value_drift > self.drift_thresholds["value_drift_medium"]
            or behavioral_drift > self.drift_thresholds["behavioral_drift_medium"]
        ):
            return "gradual_drift"

        else:
            return "stable"

    def _detect_specific_changes(
        self,
        current: ModelSnapshot,
        baseline: ModelSnapshot,
        value_drift: Dict[str, Any],
        behavioral_drift: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Detect specific changes in model behavior."""

        changes = []

        # Value changes
        for dimension, drift_score in value_drift["dimensions"].items():
            if drift_score > self.drift_thresholds["value_drift_medium"]:
                current_val = current.value_embeddings.get(dimension, 0.0)
                baseline_val = baseline.value_embeddings.get(dimension, 0.0)

                changes.append(
                    {
                        "type": "value_change",
                        "dimension": dimension,
                        "drift_score": drift_score,
                        "baseline_value": baseline_val,
                        "current_value": current_val,
                        "change_direction": "increase"
                        if current_val > baseline_val
                        else "decrease",
                    }
                )

        # Behavioral changes
        for category, drift_score in behavioral_drift["categories"].items():
            if drift_score > self.drift_thresholds["behavioral_drift_medium"]:
                current_val = current.behavioral_vectors.get(category, 0.0)
                baseline_val = baseline.behavioral_vectors.get(category, 0.0)

                changes.append(
                    {
                        "type": "behavioral_change",
                        "category": category,
                        "drift_score": drift_score,
                        "baseline_value": baseline_val,
                        "current_value": current_val,
                        "change_direction": "increase"
                        if current_val > baseline_val
                        else "decrease",
                    }
                )

        return changes

    def _generate_mitigation_recommendations(
        self,
        evolution_type: str,
        value_drift: Dict[str, Any],
        behavioral_drift: Dict[str, Any],
        performance_changes: Dict[str, float],
    ) -> List[str]:
        """Generate recommendations to mitigate detected drift."""

        recommendations = []

        if evolution_type == "value_degradation":
            recommendations.extend(
                [
                    "Immediate value realignment training required",
                    "Review recent training data for value conflicts",
                    "Consider reverting to previous model checkpoint",
                    "Implement additional value constraint mechanisms",
                ]
            )

        elif evolution_type == "value_drift":
            recommendations.extend(
                [
                    "Monitor value drift progression closely",
                    "Consider targeted fine-tuning on value-aligned data",
                    "Implement drift detection alerts for this model",
                    "Review and strengthen value embedding training",
                ]
            )

        elif evolution_type == "behavioral_drift":
            recommendations.extend(
                [
                    "Analyze behavioral changes for alignment with intended evolution",
                    "Consider behavioral constraint mechanisms",
                    "Monitor for downstream effects on user interactions",
                    "Evaluate if drift aligns with intended model improvements",
                ]
            )

        elif evolution_type == "performance_degradation":
            recommendations.extend(
                [
                    "Investigate causes of performance decline",
                    "Consider model rollback to previous version",
                    "Review recent training data quality",
                    "Implement performance monitoring alerts",
                ]
            )

        # Add specific recommendations based on drift patterns
        if value_drift["score"] > self.drift_thresholds["value_drift_high"]:
            max_drift_dim = value_drift["max_drift_dimension"]
            recommendations.append(
                f"Focus remediation on {max_drift_dim} value dimension"
            )

        if behavioral_drift["score"] > self.drift_thresholds["behavioral_drift_high"]:
            max_drift_cat = behavioral_drift["max_drift_category"]
            recommendations.append(
                f"Address behavioral changes in {max_drift_cat} category"
            )

        return recommendations

    def _calculate_confidence(
        self, value_drift: Dict[str, Any], behavioral_drift: Dict[str, Any]
    ) -> float:
        """Calculate confidence level in drift detection."""

        # Higher drift scores and more consistent drift patterns increase confidence
        value_consistency = 1.0 - np.std(list(value_drift["dimensions"].values()))
        behavioral_consistency = 1.0 - np.std(
            list(behavioral_drift["categories"].values())
        )

        drift_magnitude = (value_drift["score"] + behavioral_drift["score"]) / 2
        consistency = (value_consistency + behavioral_consistency) / 2

        confidence = min((drift_magnitude * 0.7) + (consistency * 0.3), 1.0)
        return max(confidence, 0.1)  # Minimum 10% confidence

    def _identify_contributing_factors(
        self, current: ModelSnapshot, baseline: ModelSnapshot
    ) -> List[str]:
        """Identify potential contributing factors to evolution."""

        factors = []

        # Check training metadata differences
        current_meta = current.training_metadata
        baseline_meta = baseline.training_metadata

        if current_meta.get("training_steps", 0) > baseline_meta.get(
            "training_steps", 0
        ):
            factors.append("additional_training")

        if current_meta.get("data_sources") != baseline_meta.get("data_sources"):
            factors.append("training_data_changes")

        if current_meta.get("learning_rate") != baseline_meta.get("learning_rate"):
            factors.append("hyperparameter_changes")

        # Check temporal factors
        time_diff = (current.timestamp - baseline.timestamp).days
        if time_diff > 30:
            factors.append("temporal_drift")

        if not factors:
            factors.append("unknown_factors")

        return factors

    def _assess_alignment_impact(
        self, value_drift: Dict[str, Any], behavioral_drift: Dict[str, Any]
    ) -> str:
        """Assess impact on model alignment."""

        total_drift = value_drift["score"] + behavioral_drift["score"]

        if total_drift > 1.0:
            return "severe_misalignment_risk"
        elif total_drift > 0.7:
            return "moderate_misalignment_risk"
        elif total_drift > 0.4:
            return "minor_alignment_concerns"
        else:
            return "alignment_maintained"

    def _create_evolution_capsule(
        self,
        model_id: str,
        current_snapshot: ModelSnapshot,
        comparison_snapshot: ModelSnapshot,
        analysis: Dict[str, Any],
    ) -> EvolutionCapsule:
        """Create an evolution tracking capsule."""

        payload = EvolutionPayload(
            model_id=model_id,
            evolution_type=analysis["evolution_type"],
            baseline_model_id=comparison_snapshot.model_id,
            evolution_metrics=analysis["evolution_metrics"],
            value_drift_score=analysis["value_drift_score"],
            drift_direction=analysis["drift_direction"],
            detected_changes=analysis["detected_changes"],
            confidence_level=analysis["confidence_level"],
            evolution_timestamp=current_snapshot.timestamp,
            contributing_factors=analysis["contributing_factors"],
            mitigation_recommendations=analysis["mitigation_recommendations"],
            alignment_impact=analysis["alignment_impact"],
            training_data_influence=current_snapshot.training_metadata,
            evaluation_methodology="automated_snapshot_comparison",
        )

        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        capsule = EvolutionCapsule(
            capsule_id=capsule_id,
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(
                signature=f"ed25519:{'0'*128}", merkle_root=f"sha256:{'0'*64}"
            ),
            evolution=payload,
        )

        logger.info(f"Created evolution capsule {capsule_id} for model {model_id}")
        return capsule

    def _check_drift_alerts(self, model_id: str, analysis: Dict[str, Any]) -> None:
        """Check if drift requires alerting."""

        drift_score = analysis["value_drift_score"]
        evolution_type = analysis["evolution_type"]

        # Determine alert severity
        if drift_score > self.drift_thresholds["value_drift_critical"]:
            severity = "critical"
        elif drift_score > self.drift_thresholds["value_drift_high"]:
            severity = "high"
        elif drift_score > self.drift_thresholds["value_drift_medium"]:
            severity = "medium"
        else:
            return  # No alert needed

        # Create alert
        alert_id = f"alert_{uuid.uuid4().hex[:12]}"

        alert = DriftAlert(
            alert_id=alert_id,
            model_id=model_id,
            drift_type=evolution_type,
            severity=severity,
            drift_score=drift_score,
            detected_at=datetime.now(timezone.utc),
            description=f"Model {model_id} showing {evolution_type} with drift score {drift_score:.3f}",
            recommended_actions=analysis["mitigation_recommendations"][
                :3
            ],  # Top 3 recommendations
            affected_behaviors=analysis["drift_direction"][:5],  # Top 5 affected areas
        )

        self.active_alerts[alert_id] = alert

        logger.warning(
            f"Created {severity} drift alert {alert_id} for model {model_id}"
        )

    def get_model_evolution_history(self, model_id: str) -> List[Dict[str, Any]]:
        """Get evolution history for a model."""
        return self.evolution_history.get(model_id, [])

    def get_active_alerts(self, model_id: Optional[str] = None) -> List[DriftAlert]:
        """Get active drift alerts, optionally filtered by model."""
        alerts = list(self.active_alerts.values())

        if model_id:
            alerts = [alert for alert in alerts if alert.model_id == model_id]

        return sorted(alerts, key=lambda a: a.detected_at, reverse=True)

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge and remove an alert."""
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]
            logger.info(f"Alert {alert_id} acknowledged and removed")
            return True
        return False

    def run_advanced_analytics(
        self, model_ids: List[str], analysis_type: str, comparison_period_days: int = 90
    ) -> Dict[str, Any]:
        """Run advanced evolution analytics across multiple models."""

        analysis_id = f"analytics_{uuid.uuid4().hex[:16]}"
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=comparison_period_days)

        analyzed_models = []
        trends = []
        predictions = []
        risk_scores = {
            "value_drift": 0.0,
            "behavioral_shift": 0.0,
            "performance_decline": 0.0,
            "alignment_degradation": 0.0,
            "overall_risk": 0.0,
        }

        total_models = len(model_ids)

        for model_id in model_ids:
            if model_id not in self.model_snapshots:
                continue

            snapshots = self.model_snapshots[model_id]
            recent_snapshots = [s for s in snapshots if s.timestamp >= start_date]

            if len(recent_snapshots) < 2:
                continue

            analyzed_models.append(model_id)

            # Analyze trends for this model
            model_trends = self._analyze_model_trends(
                model_id, recent_snapshots, analysis_type
            )
            trends.extend(model_trends)

            # Generate predictions
            model_predictions = self._generate_evolution_predictions(
                model_id, recent_snapshots, analysis_type
            )
            predictions.extend(model_predictions)

            # Calculate risk contributions
            model_risks = self._calculate_model_risks(recent_snapshots)
            for risk_type, score in model_risks.items():
                if risk_type in risk_scores:
                    risk_scores[risk_type] += score

        # Average risk scores across analyzed models
        if analyzed_models:
            for risk_type in risk_scores:
                risk_scores[risk_type] /= len(analyzed_models)

        # Calculate overall risk
        risk_scores["overall_risk"] = np.mean(
            [
                risk_scores["value_drift"],
                risk_scores["behavioral_shift"],
                risk_scores["performance_decline"],
                risk_scores["alignment_degradation"],
            ]
        )

        # Generate summary
        summary = {
            "total_models_requested": total_models,
            "models_analyzed": len(analyzed_models),
            "analysis_period_days": comparison_period_days,
            "trends_detected": len(trends),
            "predictions_generated": len(predictions),
            "highest_risk_model": self._identify_highest_risk_model(model_ids),
            "overall_system_health": self._assess_system_health(risk_scores),
            "recommended_actions": self._generate_system_recommendations(
                trends, risk_scores
            ),
        }

        return {
            "analysis_id": analysis_id,
            "summary": summary,
            "trends": trends,
            "predictions": predictions,
            "risk_assessment": risk_scores,
            "analyzed_models": analyzed_models,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def setup_predictive_alerts(
        self,
        model_ids: List[str],
        alert_thresholds: Dict[str, float],
        notification_channels: List[str],
    ) -> Dict[str, Any]:
        """Setup predictive evolution alerts for proactive monitoring."""

        config_id = f"alert_config_{uuid.uuid4().hex[:16]}"

        # Merge with default thresholds
        default_thresholds = {
            "value_drift_predictive": 0.3,
            "behavioral_shift_predictive": 0.25,
            "performance_decline_predictive": 0.1,
            "alignment_risk_predictive": 0.2,
        }
        merged_thresholds = {**default_thresholds, **alert_thresholds}

        # Setup monitoring configuration
        alert_config = {
            "config_id": config_id,
            "monitored_models": model_ids.copy(),
            "alert_thresholds": merged_thresholds,
            "notification_channels": notification_channels.copy(),
            "active_alerts": [],
            "next_evaluation": datetime.now(timezone.utc) + timedelta(hours=6),
            "evaluation_frequency_hours": 6,
            "created_at": datetime.now(timezone.utc),
        }

        # Store configuration (in real implementation, this would be persisted)
        self.monitoring_config["predictive_alerts"] = self.monitoring_config.get(
            "predictive_alerts", {}
        )
        self.monitoring_config["predictive_alerts"][config_id] = alert_config

        # Run initial predictive analysis
        for model_id in model_ids:
            if (
                model_id in self.model_snapshots
                and len(self.model_snapshots[model_id]) >= 2
            ):
                predicted_risks = self._predict_future_drift(model_id, days_ahead=7)

                for risk_type, risk_score in predicted_risks.items():
                    threshold_key = f"{risk_type}_predictive"
                    if (
                        threshold_key in merged_thresholds
                        and risk_score > merged_thresholds[threshold_key]
                    ):
                        alert = {
                            "alert_id": f"predictive_{uuid.uuid4().hex[:12]}",
                            "model_id": model_id,
                            "risk_type": risk_type,
                            "predicted_score": risk_score,
                            "threshold": merged_thresholds[threshold_key],
                            "prediction_horizon_days": 7,
                            "confidence": predicted_risks.get("confidence", 0.7),
                            "created_at": datetime.now(timezone.utc),
                        }
                        alert_config["active_alerts"].append(alert)

        logger.info(
            f"Setup predictive alerts for {len(model_ids)} models with {len(alert_config['active_alerts'])} initial alerts"
        )

        return alert_config

    def get_system_evolution_trends(
        self, time_range_days: int = 90, trend_type: str = "all"
    ) -> Dict[str, Any]:
        """Get evolution trend analytics across the system."""

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=time_range_days)

        # Collect all evolution events in time range
        all_events = []
        for model_id, history in self.evolution_history.items():
            recent_events = [
                {**event, "model_id": model_id}
                for event in history
                if event["timestamp"] >= start_date
            ]
            all_events.extend(recent_events)

        # Sort by timestamp
        all_events.sort(key=lambda x: x["timestamp"])

        # Calculate trends by type
        trends_by_type = {}
        if trend_type in ["drift_trend", "all"]:
            trends_by_type["drift_trends"] = self._calculate_drift_trends(
                all_events, time_range_days
            )

        if trend_type in ["evolution_patterns", "all"]:
            trends_by_type["evolution_patterns"] = self._calculate_evolution_patterns(
                all_events
            )

        if trend_type in ["system_health", "all"]:
            trends_by_type["system_health"] = self._calculate_system_health_trends(
                all_events, time_range_days
            )

        # System-wide statistics
        system_stats = {
            "total_models_tracked": len(self.model_snapshots),
            "active_monitoring_models": len(
                [
                    m
                    for m in self.model_snapshots.keys()
                    if len(self.model_snapshots[m]) > 0
                ]
            ),
            "total_evolution_events": len(all_events),
            "active_alerts": len(self.active_alerts),
            "time_range_analyzed": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": time_range_days,
            },
        }

        return {
            "system_statistics": system_stats,
            "trends_by_type": trends_by_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _analyze_model_trends(
        self, model_id: str, snapshots: List[ModelSnapshot], analysis_type: str
    ) -> List[Dict[str, Any]]:
        """Analyze trends for a specific model."""

        trends = []

        if analysis_type in ["drift_trend", "all"]:
            # Calculate drift progression over time
            drift_scores = []
            for i in range(1, len(snapshots)):
                current = snapshots[i]
                previous = snapshots[i - 1]

                value_drift = self._calculate_value_drift(
                    current.value_embeddings, previous.value_embeddings
                )

                drift_scores.append(
                    {
                        "timestamp": current.timestamp,
                        "drift_score": value_drift["score"],
                        "max_drift_dimension": value_drift["max_drift_dimension"],
                    }
                )

            if drift_scores:
                # Calculate trend direction
                recent_scores = [d["drift_score"] for d in drift_scores[-5:]]
                trend_direction = (
                    "increasing"
                    if len(recent_scores) > 1 and recent_scores[-1] > recent_scores[0]
                    else "stable"
                )

                trends.append(
                    {
                        "model_id": model_id,
                        "trend_type": "value_drift_progression",
                        "direction": trend_direction,
                        "current_score": recent_scores[-1] if recent_scores else 0,
                        "score_history": drift_scores[-10:],  # Last 10 measurements
                        "severity": "high"
                        if recent_scores and recent_scores[-1] > 0.6
                        else "medium"
                        if recent_scores and recent_scores[-1] > 0.3
                        else "low",
                    }
                )

        return trends

    def _generate_evolution_predictions(
        self, model_id: str, snapshots: List[ModelSnapshot], analysis_type: str
    ) -> List[Dict[str, Any]]:
        """Generate evolution predictions for a model."""

        predictions = []

        if len(snapshots) >= 3:
            # Simple linear trend prediction
            recent_snapshots = snapshots[-5:]  # Use last 5 snapshots

            # Predict value drift trajectory
            drift_scores = []
            for i in range(1, len(recent_snapshots)):
                current = recent_snapshots[i]
                previous = recent_snapshots[i - 1]
                drift = self._calculate_value_drift(
                    current.value_embeddings, previous.value_embeddings
                )
                drift_scores.append(drift["score"])

            if len(drift_scores) >= 2:
                # Simple linear regression for prediction
                trend_slope = (drift_scores[-1] - drift_scores[0]) / len(drift_scores)
                predicted_score_7d = max(
                    0, min(1, drift_scores[-1] + (trend_slope * 7))
                )
                predicted_score_30d = max(
                    0, min(1, drift_scores[-1] + (trend_slope * 30))
                )

                predictions.append(
                    {
                        "model_id": model_id,
                        "prediction_type": "value_drift_trajectory",
                        "current_score": drift_scores[-1],
                        "predicted_7_days": predicted_score_7d,
                        "predicted_30_days": predicted_score_30d,
                        "confidence": 0.7,  # Simplified confidence
                        "risk_level": "high"
                        if predicted_score_30d > 0.7
                        else "medium"
                        if predicted_score_30d > 0.4
                        else "low",
                    }
                )

        return predictions

    def _calculate_model_risks(
        self, snapshots: List[ModelSnapshot]
    ) -> Dict[str, float]:
        """Calculate risk scores for a model based on recent snapshots."""

        if len(snapshots) < 2:
            return {
                "value_drift": 0,
                "behavioral_shift": 0,
                "performance_decline": 0,
                "alignment_degradation": 0,
            }

        latest = snapshots[-1]
        baseline = snapshots[0]

        # Value drift risk
        value_drift = self._calculate_value_drift(
            latest.value_embeddings, baseline.value_embeddings
        )
        value_risk = min(1.0, value_drift["score"] * 1.2)  # Amplify for risk assessment

        # Behavioral shift risk
        behavioral_drift = self._calculate_behavioral_drift(
            latest.behavioral_vectors, baseline.behavioral_vectors
        )
        behavioral_risk = min(1.0, behavioral_drift["score"] * 1.1)

        # Performance decline risk
        perf_changes = self._calculate_performance_changes(
            latest.performance_metrics, baseline.performance_metrics
        )
        perf_risk = max(
            0, -np.mean(list(perf_changes.values()))
        )  # Risk increases with performance decline

        # Alignment degradation risk (combination of value and behavioral drift)
        alignment_risk = min(1.0, (value_risk + behavioral_risk) / 2)

        return {
            "value_drift": value_risk,
            "behavioral_shift": behavioral_risk,
            "performance_decline": perf_risk,
            "alignment_degradation": alignment_risk,
        }

    def _predict_future_drift(
        self, model_id: str, days_ahead: int = 7
    ) -> Dict[str, float]:
        """Predict future drift for a model."""

        if model_id not in self.model_snapshots:
            return {"confidence": 0.0}

        snapshots = self.model_snapshots[model_id]
        if len(snapshots) < 3:
            return {"confidence": 0.0}

        # Use recent snapshots for prediction
        recent = snapshots[-5:]

        # Calculate drift velocity
        drift_values = []
        for i in range(1, len(recent)):
            drift = self._calculate_value_drift(
                recent[i].value_embeddings, recent[i - 1].value_embeddings
            )
            drift_values.append(drift["score"])

        if not drift_values:
            return {"confidence": 0.0}

        # Simple linear extrapolation
        avg_drift_rate = np.mean(drift_values)
        current_drift = drift_values[-1] if drift_values else 0

        predicted_drift = current_drift + (
            avg_drift_rate * days_ahead / 7
        )  # Normalize to weekly rate

        return {
            "value_drift": min(1.0, max(0.0, predicted_drift)),
            "behavioral_shift": min(
                1.0, max(0.0, predicted_drift * 0.8)
            ),  # Correlated but lower
            "confidence": 0.7 if len(drift_values) >= 3 else 0.5,
        }

    def _identify_highest_risk_model(self, model_ids: List[str]) -> Optional[str]:
        """Identify the model with highest risk score."""

        highest_risk = 0.0
        highest_risk_model = None

        for model_id in model_ids:
            if (
                model_id in self.model_snapshots
                and len(self.model_snapshots[model_id]) >= 2
            ):
                risks = self._calculate_model_risks(self.model_snapshots[model_id])
                overall_risk = np.mean(list(risks.values()))

                if overall_risk > highest_risk:
                    highest_risk = overall_risk
                    highest_risk_model = model_id

        return highest_risk_model

    def _assess_system_health(self, risk_scores: Dict[str, float]) -> str:
        """Assess overall system health based on risk scores."""

        overall_risk = risk_scores.get("overall_risk", 0.0)

        if overall_risk > 0.7:
            return "critical"
        elif overall_risk > 0.5:
            return "degraded"
        elif overall_risk > 0.3:
            return "warning"
        else:
            return "healthy"

    def _generate_system_recommendations(
        self, trends: List[Dict[str, Any]], risk_scores: Dict[str, float]
    ) -> List[str]:
        """Generate system-wide recommendations."""

        recommendations = []

        if risk_scores.get("overall_risk", 0) > 0.6:
            recommendations.append("Immediate system-wide review required")
            recommendations.append(
                "Consider implementing emergency drift mitigation protocols"
            )

        high_drift_trends = [t for t in trends if t.get("severity") == "high"]
        if len(high_drift_trends) > 3:
            recommendations.append(
                "Multiple models showing high drift - review training processes"
            )

        if risk_scores.get("alignment_degradation", 0) > 0.5:
            recommendations.append(
                "Strengthen value alignment training across all models"
            )

        if risk_scores.get("performance_decline", 0) > 0.3:
            recommendations.append("Investigate performance degradation patterns")

        if not recommendations:
            recommendations.append(
                "System health appears stable - continue regular monitoring"
            )

        return recommendations

    def _calculate_drift_trends(
        self, events: List[Dict], time_range_days: int
    ) -> Dict[str, Any]:
        """Calculate drift trends from evolution events."""

        # Group events by time windows
        window_size_days = max(1, time_range_days // 10)  # 10 windows
        windows = {}

        for event in events:
            window_key = (
                event["timestamp"].date() // timedelta(days=window_size_days)
            ) * window_size_days
            if window_key not in windows:
                windows[window_key] = []
            windows[window_key].append(event)

        # Calculate average drift per window
        drift_progression = []
        for window_date, window_events in sorted(windows.items()):
            avg_drift = np.mean([e["drift_score"] for e in window_events])
            drift_progression.append(
                {
                    "date": window_date.isoformat(),
                    "average_drift": avg_drift,
                    "event_count": len(window_events),
                }
            )

        return {
            "drift_progression": drift_progression,
            "overall_trend": "increasing"
            if len(drift_progression) >= 2
            and drift_progression[-1]["average_drift"]
            > drift_progression[0]["average_drift"]
            else "stable",
        }

    def _calculate_evolution_patterns(self, events: List[Dict]) -> Dict[str, Any]:
        """Calculate evolution patterns from events."""

        # Count evolution types
        evolution_types = {}
        for event in events:
            evo_type = event.get("evolution_type", "unknown")
            evolution_types[evo_type] = evolution_types.get(evo_type, 0) + 1

        # Most common patterns
        sorted_types = sorted(evolution_types.items(), key=lambda x: x[1], reverse=True)

        return {
            "evolution_type_distribution": dict(sorted_types),
            "most_common_evolution": sorted_types[0][0] if sorted_types else "none",
            "pattern_diversity": len(evolution_types),
        }

    def _calculate_system_health_trends(
        self, events: List[Dict], time_range_days: int
    ) -> Dict[str, Any]:
        """Calculate system health trends."""

        recent_events = [
            e for e in events if (datetime.now(timezone.utc) - e["timestamp"]).days <= 7
        ]

        # Count concerning evolution types
        concerning_types = [
            "value_degradation",
            "performance_degradation",
            "behavioral_drift",
        ]
        concerning_events = [
            e for e in recent_events if e.get("evolution_type") in concerning_types
        ]

        health_score = max(
            0, 1.0 - (len(concerning_events) / max(1, len(recent_events)))
        )

        return {
            "recent_health_score": health_score,
            "concerning_events_count": len(concerning_events),
            "total_recent_events": len(recent_events),
            "health_status": "good"
            if health_score > 0.8
            else "warning"
            if health_score > 0.6
            else "poor",
        }


# Global service instance
evolution_tracking_service = EvolutionTrackingService()
