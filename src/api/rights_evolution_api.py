"""
Rights & Evolution API Endpoints for UATP Capsule Engine

This module provides API endpoints for Cloning Rights and Evolution tracking functionality,
including licensing management and value drift monitoring.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from quart import Blueprint, jsonify
from quart_schema import validate_request, validate_response

from .schemas import ErrorResponse
from src.services.cloning_rights_service import cloning_rights_service
from src.services.evolution_tracking_service import evolution_tracking_service

logger = logging.getLogger(__name__)


# --- Schema Definitions ---


class CreateLicenseRequest(BaseModel):
    """Schema for creating a new model license."""

    model_id: str
    license_type: str = Field(
        description="Type of license (exclusive, non_exclusive, research, commercial, open_source)"
    )
    licensee_agent_id: Optional[str] = Field(
        None, description="Specific licensee agent ID"
    )
    custom_terms: Optional[Dict[str, Any]] = Field(
        None, description="Custom license terms"
    )
    license_fee: Optional[float] = Field(None, ge=0, description="License fee amount")
    duration_days: Optional[int] = Field(
        None, gt=0, description="License duration in days"
    )


class RegisterModelRightsRequest(BaseModel):
    """Schema for registering model rights."""

    model_id: str
    base_license_type: str = Field(
        default="non_exclusive", description="Base license type for the model"
    )
    moral_constraints: Optional[List[str]] = Field(
        None, description="Moral constraints on model usage"
    )


class ValidateUsageRequest(BaseModel):
    """Schema for validating model usage."""

    model_id: str
    agent_id: str
    usage_type: str = Field(description="Type of usage to validate")


class CreateSnapshotRequest(BaseModel):
    """Schema for creating a model snapshot."""

    model_id: str
    behavioral_vectors: Dict[str, float] = Field(
        description="Behavioral characteristic vectors"
    )
    value_embeddings: Dict[str, float] = Field(description="Value system embeddings")
    performance_metrics: Dict[str, float] = Field(description="Performance metrics")
    training_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Training metadata"
    )
    version: str = Field(default="1.0", description="Model version")


class DetectEvolutionRequest(BaseModel):
    """Schema for detecting model evolution."""

    model_id: str
    comparison_snapshot_id: Optional[str] = Field(
        None, description="Specific snapshot to compare against"
    )


class LicenseResponse(BaseModel):
    """Schema for license response."""

    capsule_id: str
    license_id: str
    model_id: str
    license_type: str
    licensor_agent_id: str
    licensee_agent_id: Optional[str]
    created_date: str
    expiration_date: Optional[str]
    status: str


class ValidationResponse(BaseModel):
    """Schema for usage validation response."""

    allowed: bool
    reason: str
    license_id: Optional[str]
    license_required: bool = False


class SnapshotResponse(BaseModel):
    """Schema for snapshot creation response."""

    snapshot_id: str
    model_id: str
    timestamp: str
    is_baseline: bool


class EvolutionResponse(BaseModel):
    """Schema for evolution detection response."""

    capsule_id: str
    model_id: str
    evolution_type: str
    value_drift_score: float
    confidence_level: float
    detected_changes: List[Dict[str, Any]]
    recommendations: List[str]
    alert_created: bool


class AlertResponse(BaseModel):
    """Schema for drift alert response."""

    alert_id: str
    model_id: str
    drift_type: str
    severity: str
    drift_score: float
    detected_at: str
    description: str
    recommended_actions: List[str]


def create_rights_evolution_api_blueprint(engine_getter, require_api_key):
    """Create and return the rights & evolution API blueprint with injected dependencies."""
    blueprint = Blueprint(
        "rights_evolution_api", __name__, url_prefix="/api/v1/rights-evolution"
    )

    # --- Cloning Rights Endpoints ---

    @blueprint.route("/models/<model_id>/rights", methods=["POST"])
    @require_api_key(["admin"])
    @validate_request(RegisterModelRightsRequest)
    async def register_model_rights(model_id: str, data: RegisterModelRightsRequest):
        """Register rights for a new model."""
        try:
            # Verify model_id matches request
            if model_id != data.model_id:
                return (
                    jsonify(
                        ErrorResponse(
                            error="Model ID mismatch between URL and request body"
                        ).model_dump()
                    ),
                    400,
                )

            # Get current agent ID (would normally come from authentication)
            engine = engine_getter()
            agent_id = getattr(engine, "agent_id", "unknown")

            rights = cloning_rights_service.register_model_rights(
                model_id=data.model_id,
                owner_agent_id=agent_id,
                base_license_type=data.base_license_type,
                moral_constraints=data.moral_constraints,
            )

            return (
                jsonify(
                    {
                        "model_id": rights.model_id,
                        "owner_agent_id": rights.owner_agent_id,
                        "base_license_type": rights.base_license_type,
                        "creation_date": rights.creation_date.isoformat(),
                        "moral_constraints": rights.moral_constraints,
                    }
                ),
                201,
            )

        except ValueError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error registering model rights: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to register model rights", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/licenses", methods=["POST"])
    @require_api_key(["write", "admin"])
    @validate_request(CreateLicenseRequest)
    async def create_license(data: CreateLicenseRequest):
        """Create a new model license."""
        try:
            # Get current agent ID (would normally come from authentication)
            engine = engine_getter()
            agent_id = getattr(engine, "agent_id", "unknown")

            stored_capsule = await engine.create_cloning_rights_capsule(
                model_id=data.model_id,
                license_type=data.license_type,
                licensor_agent_id=agent_id,
                licensee_agent_id=data.licensee_agent_id,
                custom_terms=data.custom_terms,
                license_fee=data.license_fee,
                duration_days=data.duration_days,
            )
            capsule = stored_capsule

            # Get license info
            licenses = cloning_rights_service.get_model_licenses(data.model_id)
            latest_license = licenses[0] if licenses else None

            if latest_license:
                response = LicenseResponse(
                    capsule_id=stored_capsule.capsule_id,
                    license_id=latest_license["license_id"],
                    model_id=data.model_id,
                    license_type=data.license_type,
                    licensor_agent_id=agent_id,
                    licensee_agent_id=data.licensee_agent_id,
                    created_date=latest_license["created_date"].isoformat(),
                    expiration_date=latest_license["expiration_date"].isoformat()
                    if latest_license["expiration_date"]
                    else None,
                    status=latest_license["status"],
                )
                return jsonify(response.model_dump()), 201
            else:
                return (
                    jsonify(
                        {
                            "capsule_id": stored_capsule.capsule_id,
                            "model_id": data.model_id,
                            "license_type": data.license_type,
                        }
                    ),
                    201,
                )

        except ValueError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error creating license: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to create license", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/usage/validate", methods=["POST"])
    @require_api_key(["read", "write"])
    @validate_request(ValidateUsageRequest)
    async def validate_usage(data: ValidateUsageRequest):
        """Validate if an agent can use a model."""
        try:
            result = cloning_rights_service.validate_usage(
                model_id=data.model_id,
                agent_id=data.agent_id,
                usage_type=data.usage_type,
            )

            response = ValidationResponse(
                allowed=result["allowed"],
                reason=result["reason"],
                license_id=result.get("license_id"),
                license_required=result.get("license_required", False),
            )

            # Log usage if allowed
            if result["allowed"]:
                cloning_rights_service.log_usage(
                    model_id=data.model_id,
                    agent_id=data.agent_id,
                    usage_type=data.usage_type,
                    license_id=result.get("license_id"),
                )

            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"Error validating usage: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to validate usage", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/models/<model_id>/licenses", methods=["GET"])
    @require_api_key(["read"])
    async def get_model_licenses(model_id: str):
        """Get all licenses for a specific model."""
        try:
            licenses = cloning_rights_service.get_model_licenses(model_id)

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

            return (
                jsonify(
                    {
                        "model_id": model_id,
                        "licenses": license_responses,
                        "count": len(license_responses),
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error(f"Error getting model licenses: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve model licenses", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/agents/<agent_id>/licenses", methods=["GET"])
    @require_api_key(["read"])
    async def get_agent_licenses(agent_id: str):
        """Get all licenses for a specific agent."""
        try:
            licenses = cloning_rights_service.get_agent_licenses(agent_id)

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

            return (
                jsonify(
                    {
                        "agent_id": agent_id,
                        "licenses": license_responses,
                        "count": len(license_responses),
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error(f"Error getting agent licenses: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve agent licenses", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    # --- Evolution Tracking Endpoints ---

    @blueprint.route("/evolution/snapshots", methods=["POST"])
    @require_api_key(["write", "admin"])
    @validate_request(CreateSnapshotRequest)
    async def create_snapshot(data: CreateSnapshotRequest):
        """Create a model snapshot for evolution tracking."""
        try:
            snapshot = evolution_tracking_service.create_model_snapshot(
                model_id=data.model_id,
                behavioral_vectors=data.behavioral_vectors,
                value_embeddings=data.value_embeddings,
                performance_metrics=data.performance_metrics,
                training_metadata=data.training_metadata,
                version=data.version,
            )

            # Check if this is the baseline snapshot
            is_baseline = (
                evolution_tracking_service.baseline_models.get(data.model_id)
                == snapshot.snapshot_id
            )

            response = SnapshotResponse(
                snapshot_id=snapshot.snapshot_id,
                model_id=snapshot.model_id,
                timestamp=snapshot.timestamp.isoformat(),
                is_baseline=is_baseline,
            )

            return jsonify(response.model_dump()), 201

        except Exception as e:
            logger.error(f"Error creating snapshot: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to create snapshot", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/evolution/detect", methods=["POST"])
    @require_api_key(["write", "admin"])
    @validate_request(DetectEvolutionRequest)
    async def detect_evolution(data: DetectEvolutionRequest):
        """Detect evolution in a model."""
        try:
            engine = engine_getter()
            capsule = await engine.create_evolution_capsule(
                model_id=data.model_id,
                comparison_snapshot_id=data.comparison_snapshot_id,
            )
            stored_capsule = await engine.create_capsule_async(capsule)

            # Check if any alerts were created
            alerts = evolution_tracking_service.get_active_alerts(data.model_id)
            alert_created = len(alerts) > 0

            response = EvolutionResponse(
                capsule_id=stored_capsule.capsule_id,
                model_id=data.model_id,
                evolution_type=capsule.evolution.evolution_type,
                value_drift_score=capsule.evolution.value_drift_score,
                confidence_level=capsule.evolution.confidence_level,
                detected_changes=capsule.evolution.detected_changes,
                recommendations=capsule.evolution.mitigation_recommendations,
                alert_created=alert_created,
            )

            return jsonify(response.model_dump()), 200

        except ValueError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error detecting evolution: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to detect evolution", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/evolution/models/<model_id>/history", methods=["GET"])
    @require_api_key(["read"])
    async def get_evolution_history(model_id: str):
        """Get evolution history for a model."""
        try:
            history = evolution_tracking_service.get_model_evolution_history(model_id)

            # Convert datetime objects to ISO strings
            formatted_history = []
            for entry in history:
                formatted_entry = entry.copy()
                formatted_entry["timestamp"] = entry["timestamp"].isoformat()
                formatted_history.append(formatted_entry)

            return (
                jsonify(
                    {
                        "model_id": model_id,
                        "evolution_history": formatted_history,
                        "count": len(formatted_history),
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error(f"Error getting evolution history: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve evolution history", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/evolution/alerts", methods=["GET"])
    @require_api_key(["read"])
    async def get_alerts():
        """Get active drift alerts."""
        try:
            model_id = None  # Could be extracted from query params if needed
            alerts = evolution_tracking_service.get_active_alerts(model_id)

            alert_responses = []
            for alert in alerts:
                alert_responses.append(
                    AlertResponse(
                        alert_id=alert.alert_id,
                        model_id=alert.model_id,
                        drift_type=alert.drift_type,
                        severity=alert.severity,
                        drift_score=alert.drift_score,
                        detected_at=alert.detected_at.isoformat(),
                        description=alert.description,
                        recommended_actions=alert.recommended_actions,
                    ).model_dump()
                )

            return (
                jsonify({"alerts": alert_responses, "count": len(alert_responses)}),
                200,
            )

        except Exception as e:
            logger.error(f"Error getting alerts: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve alerts", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/evolution/alerts/<alert_id>", methods=["DELETE"])
    @require_api_key(["admin"])
    async def acknowledge_alert(alert_id: str):
        """Acknowledge and remove an alert."""
        try:
            success = evolution_tracking_service.acknowledge_alert(alert_id)

            if success:
                return jsonify({"acknowledged": True, "alert_id": alert_id}), 200
            else:
                return (
                    jsonify(
                        ErrorResponse(error=f"Alert {alert_id} not found").model_dump()
                    ),
                    404,
                )

        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to acknowledge alert", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    return blueprint
