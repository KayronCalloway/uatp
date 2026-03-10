"""
Tests for Evolution Tracking Service
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import numpy as np
import pytest

from src.capsule_schema import EvolutionCapsule
from src.services.evolution_tracking_service import (
    DriftAlert,
    EvolutionTrackingService,
    ModelSnapshot,
)


class TestEvolutionTrackingService:
    """Test the Evolution Tracking Service functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = EvolutionTrackingService()

    def test_init_drift_thresholds(self):
        """Test that drift thresholds are properly initialized."""
        thresholds = self.service.drift_thresholds

        # Check that all expected thresholds exist
        expected_thresholds = [
            "value_drift_critical",
            "value_drift_high",
            "value_drift_medium",
            "value_drift_low",
            "behavioral_drift_critical",
            "behavioral_drift_high",
            "behavioral_drift_medium",
            "performance_degradation",
            "alignment_drift",
            "bias_emergence",
        ]

        for threshold in expected_thresholds:
            assert threshold in thresholds
            assert 0 <= thresholds[threshold] <= 1

    def test_init_monitoring_config(self):
        """Test that monitoring configuration is properly initialized."""
        config = self.service.monitoring_config

        # Check required config fields
        assert "snapshot_frequency_hours" in config
        assert "comparison_window_days" in config
        assert "value_dimensions" in config
        assert "behavioral_categories" in config

        # Check value dimensions
        expected_dimensions = [
            "fairness",
            "autonomy",
            "harm_prevention",
            "transparency",
            "privacy",
            "accountability",
            "beneficence",
            "human_dignity",
        ]
        for dimension in expected_dimensions:
            assert dimension in config["value_dimensions"]

        # Check behavioral categories
        expected_categories = [
            "reasoning",
            "creativity",
            "social_interaction",
            "decision_making",
            "knowledge_application",
            "ethical_judgment",
            "bias_mitigation",
        ]
        for category in expected_categories:
            assert category in config["behavioral_categories"]

    def test_create_model_snapshot(self):
        """Test creating a model snapshot."""
        model_id = "test-model-123"
        behavioral_vectors = {
            "reasoning": 0.8,
            "creativity": 0.7,
            "social_interaction": 0.6,
        }
        value_embeddings = {"fairness": 0.9, "autonomy": 0.8, "transparency": 0.7}
        performance_metrics = {"accuracy": 0.95, "latency": 0.1, "throughput": 0.8}

        snapshot = self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors=behavioral_vectors,
            value_embeddings=value_embeddings,
            performance_metrics=performance_metrics,
            version="2.0",
        )

        assert isinstance(snapshot, ModelSnapshot)
        assert snapshot.model_id == model_id
        assert snapshot.behavioral_vectors == behavioral_vectors
        assert snapshot.value_embeddings == value_embeddings
        assert snapshot.performance_metrics == performance_metrics
        assert snapshot.version == "2.0"
        assert snapshot.snapshot_id.startswith("snapshot_")

        # Check that snapshot was stored
        assert model_id in self.service.model_snapshots
        assert len(self.service.model_snapshots[model_id]) == 1

        # Check that it was set as baseline (first snapshot)
        assert model_id in self.service.baseline_models
        assert self.service.baseline_models[model_id] == snapshot.snapshot_id

    def test_create_multiple_snapshots(self):
        """Test creating multiple snapshots for the same model."""
        model_id = "test-model-123"

        # Create first snapshot
        snapshot1 = self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.8},
            value_embeddings={"fairness": 0.9},
            performance_metrics={"accuracy": 0.95},
            version="1.0",
        )

        # Create second snapshot
        snapshot2 = self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.85},
            value_embeddings={"fairness": 0.85},
            performance_metrics={"accuracy": 0.97},
            version="2.0",
        )

        # Check that both snapshots are stored
        assert len(self.service.model_snapshots[model_id]) == 2

        # Check that baseline is still the first snapshot
        assert self.service.baseline_models[model_id] == snapshot1.snapshot_id

    def test_detect_evolution_insufficient_snapshots(self):
        """Test evolution detection fails with insufficient snapshots."""
        model_id = "test-model-no-snapshots"

        with pytest.raises(ValueError, match="Insufficient snapshots"):
            self.service.detect_evolution(model_id)

    def test_detect_evolution_with_two_snapshots(self):
        """Test evolution detection with two snapshots."""
        model_id = "test-model-123"

        # Create baseline snapshot
        self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.8, "creativity": 0.7},
            value_embeddings={"fairness": 0.9, "autonomy": 0.8},
            performance_metrics={"accuracy": 0.95, "latency": 0.1},
            version="1.0",
        )

        # Create evolved snapshot with some drift
        self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.6, "creativity": 0.9},  # Changed
            value_embeddings={"fairness": 0.7, "autonomy": 0.9},  # Changed
            performance_metrics={"accuracy": 0.97, "latency": 0.08},  # Improved
            version="2.0",
        )

        # Detect evolution
        capsule = self.service.detect_evolution(model_id)

        assert isinstance(capsule, EvolutionCapsule)
        assert capsule.evolution.model_id == model_id
        assert capsule.evolution.evolution_type in [
            "value_drift",
            "behavioral_drift",
            "gradual_drift",
            "stable",
            "performance_improvement",
            "adaptive_evolution",
        ]
        assert 0 <= capsule.evolution.value_drift_score <= 1
        assert 0 <= capsule.evolution.confidence_level <= 1
        assert len(capsule.evolution.detected_changes) >= 0
        assert len(capsule.evolution.mitigation_recommendations) >= 0

    def test_detect_evolution_with_specific_comparison(self):
        """Test evolution detection with specific comparison snapshot."""
        model_id = "test-model-123"

        # Create multiple snapshots
        snapshot1 = self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.8},
            value_embeddings={"fairness": 0.9},
            performance_metrics={"accuracy": 0.95},
            version="1.0",
        )

        snapshot2 = self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.7},
            value_embeddings={"fairness": 0.8},
            performance_metrics={"accuracy": 0.96},
            version="2.0",
        )

        snapshot3 = self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.6},
            value_embeddings={"fairness": 0.7},
            performance_metrics={"accuracy": 0.97},
            version="3.0",
        )

        # Detect evolution comparing to specific snapshot
        capsule = self.service.detect_evolution(
            model_id=model_id, comparison_snapshot_id=snapshot2.snapshot_id
        )

        assert isinstance(capsule, EvolutionCapsule)
        assert capsule.evolution.model_id == model_id

    def test_detect_evolution_comparison_snapshot_not_found(self):
        """Test evolution detection with non-existent comparison snapshot."""
        model_id = "test-model-123"

        # Create snapshots
        self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.8},
            value_embeddings={"fairness": 0.9},
            performance_metrics={"accuracy": 0.95},
        )

        self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.7},
            value_embeddings={"fairness": 0.8},
            performance_metrics={"accuracy": 0.96},
        )

        # Try to compare to non-existent snapshot
        with pytest.raises(ValueError, match="Comparison snapshot .* not found"):
            self.service.detect_evolution(
                model_id=model_id, comparison_snapshot_id="non-existent-snapshot"
            )

    def test_calculate_value_drift(self):
        """Test value drift calculation."""
        current_values = {
            "fairness": 0.9,
            "autonomy": 0.8,
            "transparency": 0.7,
            "privacy": 0.85,
        }

        baseline_values = {
            "fairness": 0.7,  # 0.2 drift
            "autonomy": 0.8,  # 0.0 drift
            "transparency": 0.9,  # 0.2 drift
            "privacy": 0.85,  # 0.0 drift
        }

        drift_result = self.service._calculate_value_drift(
            current_values, baseline_values
        )

        assert "score" in drift_result
        assert "dimensions" in drift_result
        assert "directions" in drift_result
        assert "max_drift_dimension" in drift_result

        assert 0 <= drift_result["score"] <= 1
        assert abs(drift_result["dimensions"]["fairness"] - 0.2) < 0.001
        assert abs(drift_result["dimensions"]["autonomy"] - 0.0) < 0.001
        assert abs(drift_result["dimensions"]["transparency"] - 0.2) < 0.001

    def test_calculate_behavioral_drift(self):
        """Test behavioral drift calculation."""
        current_behaviors = {
            "reasoning": 0.8,
            "creativity": 0.9,
            "social_interaction": 0.6,
        }

        baseline_behaviors = {
            "reasoning": 0.6,  # 0.2 drift
            "creativity": 0.9,  # 0.0 drift
            "social_interaction": 0.8,  # 0.2 drift
        }

        drift_result = self.service._calculate_behavioral_drift(
            current_behaviors, baseline_behaviors
        )

        assert "score" in drift_result
        assert "categories" in drift_result
        assert "directions" in drift_result
        assert "max_drift_category" in drift_result

        assert 0 <= drift_result["score"] <= 1
        assert abs(drift_result["categories"]["reasoning"] - 0.2) < 0.001
        assert abs(drift_result["categories"]["creativity"] - 0.0) < 0.001
        assert abs(drift_result["categories"]["social_interaction"] - 0.2) < 0.001

    def test_calculate_performance_changes(self):
        """Test performance changes calculation."""
        current_perf = {"accuracy": 0.97, "latency": 0.08, "throughput": 0.9}

        baseline_perf = {
            "accuracy": 0.95,  # +2.1% improvement
            "latency": 0.1,  # -20% improvement (lower is better)
            "throughput": 0.8,  # +12.5% improvement
        }

        changes = self.service._calculate_performance_changes(
            current_perf, baseline_perf
        )

        assert "accuracy" in changes
        assert "latency" in changes
        assert "throughput" in changes

        # Check relative changes
        assert abs(changes["accuracy"] - 0.021) < 0.001  # ~2.1%
        assert abs(changes["latency"] - (-0.2)) < 0.001  # -20%
        assert abs(changes["throughput"] - 0.125) < 0.001  # 12.5%

    def test_classify_evolution_type(self):
        """Test evolution type classification."""
        # Test value degradation
        evolution_type = self.service._classify_evolution_type(
            value_drift=0.9,  # High drift
            behavioral_drift=0.2,  # Low drift
            performance_changes={"accuracy": -0.2},  # Performance drop
        )
        assert evolution_type == "value_degradation"

        # Test value drift
        evolution_type = self.service._classify_evolution_type(
            value_drift=0.8,  # High drift
            behavioral_drift=0.2,  # Low drift
            performance_changes={"accuracy": 0.1},  # Performance improvement
        )
        assert evolution_type == "value_drift"

        # Test behavioral drift
        evolution_type = self.service._classify_evolution_type(
            value_drift=0.2,  # Low drift
            behavioral_drift=0.7,  # High drift
            performance_changes={"accuracy": 0.05},  # Small improvement
        )
        assert evolution_type == "behavioral_drift"

        # Test stable
        evolution_type = self.service._classify_evolution_type(
            value_drift=0.1,  # Low drift
            behavioral_drift=0.1,  # Low drift
            performance_changes={"accuracy": 0.01},  # Small change
        )
        assert evolution_type == "stable"

    def test_check_drift_alerts(self):
        """Test drift alert creation."""
        model_id = "test-model-123"
        analysis = {
            "value_drift_score": 0.9,  # Critical level
            "evolution_type": "value_degradation",
            "mitigation_recommendations": [
                "Immediate value realignment training required",
                "Review recent training data for value conflicts",
                "Consider reverting to previous model checkpoint",
            ],
            "drift_direction": ["fairness_decrease", "autonomy_increase"],
        }

        # Check drift alerts
        self.service._check_drift_alerts(model_id, analysis)

        # Verify alert was created
        assert len(self.service.active_alerts) == 1

        alert = list(self.service.active_alerts.values())[0]
        assert alert.model_id == model_id
        assert alert.severity == "critical"
        assert alert.drift_type == "value_degradation"
        assert alert.drift_score == 0.9

    def test_get_model_evolution_history(self):
        """Test getting model evolution history."""
        model_id = "test-model-123"

        # Initially no history
        history = self.service.get_model_evolution_history(model_id)
        assert len(history) == 0

        # Create snapshots and detect evolution to generate history
        self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.8},
            value_embeddings={"fairness": 0.9},
            performance_metrics={"accuracy": 0.95},
        )

        self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.7},
            value_embeddings={"fairness": 0.8},
            performance_metrics={"accuracy": 0.96},
        )

        # Detect evolution (this adds to history)
        self.service.detect_evolution(model_id)

        # Check history
        history = self.service.get_model_evolution_history(model_id)
        assert len(history) == 1

        entry = history[0]
        assert "timestamp" in entry
        assert "capsule_id" in entry
        assert "drift_score" in entry
        assert "evolution_type" in entry

    def test_get_active_alerts(self):
        """Test getting active alerts."""
        model_id1 = "test-model-123"
        model_id2 = "test-model-456"

        # Create alerts for different models
        analysis1 = {
            "value_drift_score": 0.8,
            "evolution_type": "value_drift",
            "mitigation_recommendations": ["Monitor closely"],
            "drift_direction": ["fairness_decrease"],
        }

        analysis2 = {
            "value_drift_score": 0.9,
            "evolution_type": "value_degradation",
            "mitigation_recommendations": ["Immediate action required"],
            "drift_direction": ["autonomy_increase"],
        }

        self.service._check_drift_alerts(model_id1, analysis1)
        self.service._check_drift_alerts(model_id2, analysis2)

        # Get all alerts
        all_alerts = self.service.get_active_alerts()
        assert len(all_alerts) == 2

        # Get alerts for specific model
        model1_alerts = self.service.get_active_alerts(model_id1)
        assert len(model1_alerts) == 1
        assert model1_alerts[0].model_id == model_id1

    def test_acknowledge_alert(self):
        """Test acknowledging and removing alerts."""
        model_id = "test-model-123"
        analysis = {
            "value_drift_score": 0.8,
            "evolution_type": "value_drift",
            "mitigation_recommendations": ["Monitor closely"],
            "drift_direction": ["fairness_decrease"],
        }

        # Create alert
        self.service._check_drift_alerts(model_id, analysis)
        assert len(self.service.active_alerts) == 1

        # Get alert ID
        alert_id = list(self.service.active_alerts.keys())[0]

        # Acknowledge alert
        result = self.service.acknowledge_alert(alert_id)
        assert result is True
        assert len(self.service.active_alerts) == 0

    def test_acknowledge_nonexistent_alert(self):
        """Test acknowledging non-existent alert."""
        result = self.service.acknowledge_alert("non-existent-alert")
        assert result is False

    def test_confidence_calculation(self):
        """Test confidence level calculation."""
        # Test with consistent drift
        value_drift = {
            "score": 0.8,
            "dimensions": {"fairness": 0.8, "autonomy": 0.8, "transparency": 0.8},
        }
        behavioral_drift = {
            "score": 0.6,
            "categories": {
                "reasoning": 0.6,
                "creativity": 0.6,
                "social_interaction": 0.6,
            },
        }

        confidence = self.service._calculate_confidence(value_drift, behavioral_drift)
        assert 0.1 <= confidence <= 1.0

        # High drift and consistency should give high confidence
        assert confidence > 0.5

    def test_identify_contributing_factors(self):
        """Test identifying contributing factors."""
        # Create snapshots with different metadata
        current_snapshot = ModelSnapshot(
            model_id="test-model",
            snapshot_id="current",
            timestamp=datetime.now(timezone.utc),
            behavioral_vectors={},
            value_embeddings={},
            performance_metrics={},
            training_metadata={
                "training_steps": 2000,
                "data_sources": ["new_data", "old_data"],
                "learning_rate": 0.001,
            },
            version="2.0",
        )

        baseline_snapshot = ModelSnapshot(
            model_id="test-model",
            snapshot_id="baseline",
            timestamp=datetime.now(timezone.utc) - timedelta(days=35),  # Old timestamp
            behavioral_vectors={},
            value_embeddings={},
            performance_metrics={},
            training_metadata={
                "training_steps": 1000,
                "data_sources": ["old_data"],
                "learning_rate": 0.002,
            },
            version="1.0",
        )

        factors = self.service._identify_contributing_factors(
            current_snapshot, baseline_snapshot
        )

        assert "additional_training" in factors  # More training steps
        assert "training_data_changes" in factors  # Different data sources
        assert "hyperparameter_changes" in factors  # Different learning rate
        assert "temporal_drift" in factors  # > 30 days difference

    def test_assess_alignment_impact(self):
        """Test alignment impact assessment."""
        # Test severe misalignment risk
        value_drift = {"score": 0.8}
        behavioral_drift = {"score": 0.5}
        impact = self.service._assess_alignment_impact(value_drift, behavioral_drift)
        assert impact == "severe_misalignment_risk"

        # Test alignment maintained
        value_drift = {"score": 0.1}
        behavioral_drift = {"score": 0.1}
        impact = self.service._assess_alignment_impact(value_drift, behavioral_drift)
        assert impact == "alignment_maintained"

        # Test moderate risk
        value_drift = {"score": 0.4}
        behavioral_drift = {"score": 0.4}
        impact = self.service._assess_alignment_impact(value_drift, behavioral_drift)
        assert impact == "moderate_misalignment_risk"

    def test_generate_mitigation_recommendations(self):
        """Test mitigation recommendations generation."""
        # Test value degradation recommendations
        recommendations = self.service._generate_mitigation_recommendations(
            evolution_type="value_degradation",
            value_drift={"score": 0.9, "max_drift_dimension": "fairness"},
            behavioral_drift={"score": 0.2, "max_drift_category": "reasoning"},
            performance_changes={"accuracy": -0.1},
        )

        assert "Immediate value realignment training required" in recommendations
        assert "Focus remediation on fairness value dimension" in recommendations

        # Test behavioral drift recommendations
        recommendations = self.service._generate_mitigation_recommendations(
            evolution_type="behavioral_drift",
            value_drift={"score": 0.2, "max_drift_dimension": "fairness"},
            behavioral_drift={"score": 0.8, "max_drift_category": "creativity"},
            performance_changes={"accuracy": 0.05},
        )

        assert any("behavioral" in rec.lower() for rec in recommendations)
        assert "Address behavioral changes in creativity category" in recommendations

    def test_create_evolution_capsule_structure(self):
        """Test that evolution capsule has correct structure."""
        model_id = "test-model-123"

        # Create snapshots
        baseline = self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.8},
            value_embeddings={"fairness": 0.9},
            performance_metrics={"accuracy": 0.95},
        )

        current = self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.6},
            value_embeddings={"fairness": 0.7},
            performance_metrics={"accuracy": 0.97},
        )

        # Detect evolution
        capsule = self.service.detect_evolution(model_id)

        # Verify capsule structure
        assert hasattr(capsule, "capsule_id")
        assert hasattr(capsule, "timestamp")
        assert hasattr(capsule, "status")
        assert hasattr(capsule, "verification")
        assert hasattr(capsule, "evolution")

        # Verify evolution payload
        evolution = capsule.evolution
        assert evolution.model_id == model_id
        assert hasattr(evolution, "evolution_type")
        assert hasattr(evolution, "value_drift_score")
        assert hasattr(evolution, "confidence_level")
        assert hasattr(evolution, "detected_changes")
        assert hasattr(evolution, "mitigation_recommendations")
        assert hasattr(evolution, "evolution_timestamp")

    def test_drift_threshold_sensitivity(self):
        """Test that drift detection respects threshold settings."""
        model_id = "test-model-123"

        # Create baseline snapshot
        self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.8},
            value_embeddings={"fairness": 0.9},
            performance_metrics={"accuracy": 0.95},
        )

        # Create snapshot with minimal drift (below medium threshold)
        self.service.create_model_snapshot(
            model_id=model_id,
            behavioral_vectors={"reasoning": 0.85},  # Small change
            value_embeddings={"fairness": 0.92},  # Small change
            performance_metrics={"accuracy": 0.96},  # Small improvement
        )

        # Detect evolution - should be classified as stable or gradual
        capsule = self.service.detect_evolution(model_id)
        assert capsule.evolution.evolution_type in ["stable", "gradual_drift"]

        # No alerts should be created for low drift
        alerts = self.service.get_active_alerts(model_id)
        assert len(alerts) == 0
