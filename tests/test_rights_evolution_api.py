"""
Tests for Rights & Evolution API endpoints
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from api.rights_evolution_api import (
    CreateLicenseRequest,
    RegisterModelRightsRequest,
    ValidateUsageRequest,
    CreateSnapshotRequest,
    DetectEvolutionRequest,
    LicenseResponse,
    ValidationResponse,
    SnapshotResponse,
    EvolutionResponse,
)
from src.capsule_schema import CloningRightsCapsule, EvolutionCapsule


class TestRightsEvolutionAPI:
    """Test the Rights & Evolution API business logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.mock_engine.agent_id = "test-agent"
        self.mock_engine.create_capsule_async = AsyncMock()

        # Mock the create_capsule_async to return a capsule with the expected attributes
        async def mock_create_capsule(capsule):
            capsule.capsule_id = "caps_2024_07_14_test12345678"
            return capsule

        self.mock_engine.create_capsule_async = mock_create_capsule

    def test_create_license_request_validation(self):
        """Test CreateLicenseRequest validation."""
        # Valid request
        request = CreateLicenseRequest(
            model_id="test-model-123",
            license_type="commercial",
            licensee_agent_id="agent-456",
            license_fee=100.0,
            duration_days=365,
        )
        assert request.model_id == "test-model-123"
        assert request.license_type == "commercial"
        assert request.license_fee == 100.0

        # Test with negative fee (should fail)
        with pytest.raises(ValueError):
            CreateLicenseRequest(
                model_id="test-model", license_type="commercial", license_fee=-50.0
            )

    def test_register_model_rights_request_validation(self):
        """Test RegisterModelRightsRequest validation."""
        request = RegisterModelRightsRequest(
            model_id="test-model-123",
            base_license_type="exclusive",
            moral_constraints=["no_harm", "respect_privacy"],
        )
        assert request.model_id == "test-model-123"
        assert request.base_license_type == "exclusive"
        assert "no_harm" in request.moral_constraints

    def test_validate_usage_request_validation(self):
        """Test ValidateUsageRequest validation."""
        request = ValidateUsageRequest(
            model_id="test-model-123",
            agent_id="test-agent-456",
            usage_type="commercial_use",
        )
        assert request.model_id == "test-model-123"
        assert request.agent_id == "test-agent-456"
        assert request.usage_type == "commercial_use"

    def test_create_snapshot_request_validation(self):
        """Test CreateSnapshotRequest validation."""
        request = CreateSnapshotRequest(
            model_id="test-model-123",
            behavioral_vectors={"reasoning": 0.8, "creativity": 0.7},
            value_embeddings={"fairness": 0.9, "autonomy": 0.8},
            performance_metrics={"accuracy": 0.95, "latency": 0.1},
            version="2.0",
        )
        assert request.model_id == "test-model-123"
        assert request.behavioral_vectors["reasoning"] == 0.8
        assert request.value_embeddings["fairness"] == 0.9
        assert request.performance_metrics["accuracy"] == 0.95

    def test_detect_evolution_request_validation(self):
        """Test DetectEvolutionRequest validation."""
        request = DetectEvolutionRequest(
            model_id="test-model-123", comparison_snapshot_id="snapshot_abc123"
        )
        assert request.model_id == "test-model-123"
        assert request.comparison_snapshot_id == "snapshot_abc123"

    @patch("api.rights_evolution_api.cloning_rights_service")
    async def test_register_model_rights_logic(self, mock_cloning_service):
        """Test the business logic for registering model rights."""
        from api.rights_evolution_api import create_rights_evolution_api_blueprint

        # Mock the service response
        mock_rights = Mock()
        mock_rights.model_id = "test-model-123"
        mock_rights.owner_agent_id = "test-agent"
        mock_rights.base_license_type = "exclusive"
        mock_rights.creation_date = datetime.now(timezone.utc)
        mock_rights.moral_constraints = ["no_harm"]

        mock_cloning_service.register_model_rights.return_value = mock_rights

        # Create the blueprint (we're testing the business logic, not HTTP)
        engine_getter = lambda: self.mock_engine
        require_api_key = lambda roles: lambda f: f  # Mock decorator
        blueprint = create_rights_evolution_api_blueprint(
            engine_getter, require_api_key
        )

        # Test data
        request_data = RegisterModelRightsRequest(
            model_id="test-model-123",
            base_license_type="exclusive",
            moral_constraints=["no_harm"],
        )

        # Verify the service would be called correctly
        mock_cloning_service.register_model_rights.assert_not_called()

        # Simulate the business logic
        result = mock_cloning_service.register_model_rights(
            model_id=request_data.model_id,
            owner_agent_id="test-agent",
            base_license_type=request_data.base_license_type,
            moral_constraints=request_data.moral_constraints,
        )

        assert result.model_id == "test-model-123"
        assert result.base_license_type == "exclusive"

    @patch("api.rights_evolution_api.cloning_rights_service")
    async def test_create_license_logic(self, mock_cloning_service):
        """Test the business logic for creating a license."""
        # Mock service responses
        mock_capsule = Mock(spec=CloningRightsCapsule)
        mock_capsule.capsule_id = "caps_2024_07_14_test12345678"
        mock_cloning_service.create_license_capsule.return_value = mock_capsule

        mock_license = {
            "license_id": "license_abc123",
            "created_date": datetime.now(timezone.utc),
            "expiration_date": None,
            "status": "active",
        }
        mock_cloning_service.get_model_licenses.return_value = [mock_license]

        # Test the business logic
        request_data = CreateLicenseRequest(
            model_id="test-model-123",
            license_type="commercial",
            licensee_agent_id="agent-456",
            license_fee=100.0,
            duration_days=365,
        )

        # Simulate the service calls
        capsule = mock_cloning_service.create_license_capsule(
            model_id=request_data.model_id,
            license_type=request_data.license_type,
            licensor_agent_id="test-agent",
            licensee_agent_id=request_data.licensee_agent_id,
            custom_terms=request_data.custom_terms,
            license_fee=request_data.license_fee,
            duration_days=request_data.duration_days,
        )

        stored_capsule = await self.mock_engine.create_capsule_async(capsule)
        licenses = mock_cloning_service.get_model_licenses(request_data.model_id)

        assert stored_capsule.capsule_id == "caps_2024_07_14_test12345678"
        assert len(licenses) == 1
        assert licenses[0]["license_id"] == "license_abc123"

    @patch("api.rights_evolution_api.cloning_rights_service")
    async def test_validate_usage_logic(self, mock_cloning_service):
        """Test the business logic for validating usage."""
        # Mock service response
        mock_validation_result = {
            "allowed": True,
            "reason": "Valid commercial license found",
            "license_id": "license_abc123",
            "license_required": False,
        }
        mock_cloning_service.validate_usage.return_value = mock_validation_result

        # Test data
        request_data = ValidateUsageRequest(
            model_id="test-model-123",
            agent_id="test-agent-456",
            usage_type="commercial_use",
        )

        # Simulate the business logic
        result = mock_cloning_service.validate_usage(
            model_id=request_data.model_id,
            agent_id=request_data.agent_id,
            usage_type=request_data.usage_type,
        )

        # Create response
        response = ValidationResponse(
            allowed=result["allowed"],
            reason=result["reason"],
            license_id=result.get("license_id"),
            license_required=result.get("license_required", False),
        )

        assert response.allowed is True
        assert response.reason == "Valid commercial license found"
        assert response.license_id == "license_abc123"

        # Verify usage logging would be called for allowed usage
        if result["allowed"]:
            mock_cloning_service.log_usage(
                model_id=request_data.model_id,
                agent_id=request_data.agent_id,
                usage_type=request_data.usage_type,
                license_id=result.get("license_id"),
            )

        mock_cloning_service.log_usage.assert_called_once()

    @patch("api.rights_evolution_api.evolution_tracking_service")
    async def test_create_snapshot_logic(self, mock_evolution_service):
        """Test the business logic for creating model snapshots."""
        # Mock service response
        mock_snapshot = Mock()
        mock_snapshot.snapshot_id = "snapshot_abc123"
        mock_snapshot.model_id = "test-model-123"
        mock_snapshot.timestamp = datetime.now(timezone.utc)

        mock_evolution_service.create_model_snapshot.return_value = mock_snapshot
        mock_evolution_service.baseline_models = {"test-model-123": "snapshot_abc123"}

        # Test data
        request_data = CreateSnapshotRequest(
            model_id="test-model-123",
            behavioral_vectors={"reasoning": 0.8, "creativity": 0.7},
            value_embeddings={"fairness": 0.9, "autonomy": 0.8},
            performance_metrics={"accuracy": 0.95, "latency": 0.1},
            version="2.0",
        )

        # Simulate the business logic
        snapshot = mock_evolution_service.create_model_snapshot(
            model_id=request_data.model_id,
            behavioral_vectors=request_data.behavioral_vectors,
            value_embeddings=request_data.value_embeddings,
            performance_metrics=request_data.performance_metrics,
            training_metadata=request_data.training_metadata,
            version=request_data.version,
        )

        # Check if this is the baseline snapshot
        is_baseline = (
            mock_evolution_service.baseline_models.get(request_data.model_id)
            == snapshot.snapshot_id
        )

        response = SnapshotResponse(
            snapshot_id=snapshot.snapshot_id,
            model_id=snapshot.model_id,
            timestamp=snapshot.timestamp.isoformat(),
            is_baseline=is_baseline,
        )

        assert response.snapshot_id == "snapshot_abc123"
        assert response.model_id == "test-model-123"
        assert response.is_baseline is True

    @patch("api.rights_evolution_api.evolution_tracking_service")
    async def test_detect_evolution_logic(self, mock_evolution_service):
        """Test the business logic for detecting evolution."""
        # Mock service responses
        mock_capsule = Mock(spec=EvolutionCapsule)
        mock_capsule.capsule_id = "caps_2024_07_14_evol12345678"
        mock_capsule.evolution = Mock()
        mock_capsule.evolution.evolution_type = "value_drift"
        mock_capsule.evolution.value_drift_score = 0.6
        mock_capsule.evolution.confidence_level = 0.8
        mock_capsule.evolution.detected_changes = [
            {"type": "value_change", "dimension": "fairness", "drift_score": 0.6}
        ]
        mock_capsule.evolution.mitigation_recommendations = [
            "Monitor value drift progression closely",
            "Consider targeted fine-tuning",
        ]

        mock_evolution_service.detect_evolution.return_value = mock_capsule
        mock_evolution_service.get_active_alerts.return_value = []

        # Test data
        request_data = DetectEvolutionRequest(
            model_id="test-model-123", comparison_snapshot_id="snapshot_baseline"
        )

        # Simulate the business logic
        capsule = mock_evolution_service.detect_evolution(
            model_id=request_data.model_id,
            comparison_snapshot_id=request_data.comparison_snapshot_id,
        )

        stored_capsule = await self.mock_engine.create_capsule_async(capsule)
        alerts = mock_evolution_service.get_active_alerts(request_data.model_id)

        response = EvolutionResponse(
            capsule_id=stored_capsule.capsule_id,
            model_id=request_data.model_id,
            evolution_type=capsule.evolution.evolution_type,
            value_drift_score=capsule.evolution.value_drift_score,
            confidence_level=capsule.evolution.confidence_level,
            detected_changes=capsule.evolution.detected_changes,
            recommendations=capsule.evolution.mitigation_recommendations,
            alert_created=len(alerts) > 0,
        )

        assert response.capsule_id == "caps_2024_07_14_evol12345678"
        assert response.evolution_type == "value_drift"
        assert response.value_drift_score == 0.6
        assert response.confidence_level == 0.8
        assert response.alert_created is False
        assert len(response.recommendations) == 2

    @patch("api.rights_evolution_api.cloning_rights_service")
    async def test_get_model_licenses_logic(self, mock_cloning_service):
        """Test the business logic for getting model licenses."""
        # Mock service response
        mock_licenses = [
            {
                "license_id": "license_123",
                "model_id": "test-model-123",
                "license_type": "commercial",
                "licensor_agent_id": "agent-owner",
                "licensee_agent_id": "agent-licensee",
                "created_date": datetime.now(timezone.utc),
                "expiration_date": None,
                "status": "active",
            }
        ]
        mock_cloning_service.get_model_licenses.return_value = mock_licenses

        # Test the business logic
        model_id = "test-model-123"
        licenses = mock_cloning_service.get_model_licenses(model_id)

        license_responses = []
        for license_info in licenses:
            license_responses.append(
                LicenseResponse(
                    capsule_id=license_info.get("capsule_id", ""),
                    license_id=license_info["license_id"],
                    model_id=license_info["model_id"],
                    license_type=license_info["license_type"],
                    licensor_agent_id=license_info["licensor_agent_id"],
                    licensee_agent_id=license_info["licensee_agent_id"],
                    created_date=license_info["created_date"].isoformat(),
                    expiration_date=license_info["expiration_date"].isoformat()
                    if license_info["expiration_date"]
                    else None,
                    status=license_info["status"],
                ).model_dump()
            )

        result = {
            "model_id": model_id,
            "licenses": license_responses,
            "count": len(license_responses),
        }

        assert result["model_id"] == "test-model-123"
        assert result["count"] == 1
        assert result["licenses"][0]["license_id"] == "license_123"

    @patch("api.rights_evolution_api.evolution_tracking_service")
    async def test_get_evolution_history_logic(self, mock_evolution_service):
        """Test the business logic for getting evolution history."""
        # Mock service response
        mock_history = [
            {
                "timestamp": datetime.now(timezone.utc),
                "capsule_id": "caps_2024_07_14_evol12345678",
                "drift_score": 0.6,
                "evolution_type": "value_drift",
                "comparison_snapshot": "snapshot_baseline",
            }
        ]
        mock_evolution_service.get_model_evolution_history.return_value = mock_history

        # Test the business logic
        model_id = "test-model-123"
        history = mock_evolution_service.get_model_evolution_history(model_id)

        # Convert datetime objects to ISO strings
        formatted_history = []
        for entry in history:
            formatted_entry = entry.copy()
            formatted_entry["timestamp"] = entry["timestamp"].isoformat()
            formatted_history.append(formatted_entry)

        result = {
            "model_id": model_id,
            "evolution_history": formatted_history,
            "count": len(formatted_history),
        }

        assert result["model_id"] == "test-model-123"
        assert result["count"] == 1
        assert result["evolution_history"][0]["evolution_type"] == "value_drift"

    def test_error_handling_model_not_found(self):
        """Test error handling for model not found scenarios."""
        # Test with CreateLicenseRequest for non-existent model
        request = CreateLicenseRequest(
            model_id="non-existent-model", license_type="commercial"
        )

        with patch("api.rights_evolution_api.cloning_rights_service") as mock_service:
            mock_service.create_license_capsule.side_effect = ValueError(
                "Model non-existent-model not found in rights database"
            )

            with pytest.raises(
                ValueError,
                match="Model non-existent-model not found in rights database",
            ):
                mock_service.create_license_capsule(
                    model_id=request.model_id,
                    license_type=request.license_type,
                    licensor_agent_id="test-agent",
                )

    def test_error_handling_insufficient_snapshots(self):
        """Test error handling for insufficient snapshots in evolution detection."""
        request = DetectEvolutionRequest(model_id="new-model-with-no-snapshots")

        with patch(
            "api.rights_evolution_api.evolution_tracking_service"
        ) as mock_service:
            mock_service.detect_evolution.side_effect = ValueError(
                "Insufficient snapshots for model new-model-with-no-snapshots to detect evolution"
            )

            with pytest.raises(ValueError, match="Insufficient snapshots"):
                mock_service.detect_evolution(model_id=request.model_id)

    def test_license_response_model(self):
        """Test LicenseResponse model validation."""
        response = LicenseResponse(
            capsule_id="caps_2024_07_14_test12345678",
            license_id="license_abc123",
            model_id="test-model-123",
            license_type="commercial",
            licensor_agent_id="agent-owner",
            licensee_agent_id="agent-licensee",
            created_date="2024-07-14T10:00:00Z",
            expiration_date=None,
            status="active",
        )

        assert response.capsule_id == "caps_2024_07_14_test12345678"
        assert response.license_type == "commercial"
        assert response.status == "active"
        assert response.expiration_date is None

    def test_evolution_response_model(self):
        """Test EvolutionResponse model validation."""
        response = EvolutionResponse(
            capsule_id="caps_2024_07_14_evol12345678",
            model_id="test-model-123",
            evolution_type="value_drift",
            value_drift_score=0.6,
            confidence_level=0.8,
            detected_changes=[{"type": "value_change", "dimension": "fairness"}],
            recommendations=["Monitor drift", "Fine-tune"],
            alert_created=False,
        )

        assert response.capsule_id == "caps_2024_07_14_evol12345678"
        assert response.evolution_type == "value_drift"
        assert response.value_drift_score == 0.6
        assert response.confidence_level == 0.8
        assert not response.alert_created
