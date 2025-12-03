"""
Advanced Rights & Evolution API Extensions for UATP Capsule Engine

This module provides advanced API endpoints for enterprise-grade licensing
management and sophisticated evolution analytics.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from quart import Blueprint, jsonify, request
from quart_schema import validate_request

from .schemas import ErrorResponse
from src.services.cloning_rights_service import cloning_rights_service
from src.services.evolution_tracking_service import evolution_tracking_service

logger = logging.getLogger(__name__)


# --- Advanced Schema Definitions ---


class TransferLicenseRequest(BaseModel):
    """Schema for transferring a license between agents."""

    license_id: str
    new_licensee_agent_id: str
    transfer_reason: str = Field(description="Reason for license transfer")
    transfer_fee: Optional[float] = Field(
        None, ge=0, description="Transfer fee if applicable"
    )


class RevokeLicenseRequest(BaseModel):
    """Schema for revoking a license."""

    license_id: str
    revocation_reason: str = Field(description="Reason for license revocation")
    refund_amount: Optional[float] = Field(
        None, ge=0, description="Refund amount if applicable"
    )


class BatchLicenseRequest(BaseModel):
    """Schema for batch license operations."""

    model_ids: List[str] = Field(description="List of model IDs to license")
    license_type: str = Field(description="License type for all models")
    licensee_agent_id: str = Field(description="Agent ID for all licenses")
    bulk_discount: Optional[float] = Field(
        None, ge=0, le=1, description="Bulk discount percentage"
    )


class ComplianceCheckRequest(BaseModel):
    """Schema for compliance monitoring."""

    model_id: str
    check_type: str = Field(
        description="Type of compliance check (usage, ethical, legal)"
    )
    time_range_days: int = Field(
        default=30, gt=0, description="Time range for compliance check"
    )


class EvolutionAnalyticsRequest(BaseModel):
    """Schema for advanced evolution analytics."""

    model_ids: List[str] = Field(description="List of model IDs to analyze")
    analysis_type: str = Field(
        description="Type of analysis (drift_trend, performance_decline, alignment_shift)"
    )
    comparison_period_days: int = Field(
        default=90, gt=0, description="Period for comparison"
    )


class LicenseTransferResponse(BaseModel):
    """Schema for license transfer response."""

    transfer_id: str
    license_id: str
    old_licensee_agent_id: str
    new_licensee_agent_id: str
    transfer_date: str
    transfer_fee: Optional[float]
    status: str


class ComplianceReportResponse(BaseModel):
    """Schema for compliance report response."""

    model_id: str
    check_type: str
    compliance_score: float = Field(ge=0, le=1, description="Overall compliance score")
    violations: List[Dict[str, Any]] = Field(
        description="List of compliance violations"
    )
    recommendations: List[str] = Field(
        description="Compliance improvement recommendations"
    )
    check_date: str
    next_check_due: str


class EvolutionAnalyticsResponse(BaseModel):
    """Schema for evolution analytics response."""

    analysis_id: str
    model_ids: List[str]
    analysis_type: str
    summary: Dict[str, Any] = Field(description="Analysis summary")
    trends: List[Dict[str, Any]] = Field(description="Detected trends")
    predictions: List[Dict[str, Any]] = Field(description="Predicted evolution paths")
    risk_assessment: Dict[str, float] = Field(description="Risk scores by category")
    generated_at: str


def create_advanced_rights_evolution_blueprint(engine_getter, require_api_key):
    """Create advanced rights & evolution API blueprint."""
    blueprint = Blueprint(
        "advanced_rights_evolution",
        __name__,
        url_prefix="/api/v1/advanced/rights-evolution",
    )

    # --- Advanced License Management ---

    @blueprint.route("/licenses/<license_id>/transfer", methods=["POST"])
    @require_api_key(["admin"])
    @validate_request(TransferLicenseRequest)
    async def transfer_license(license_id: str, data: TransferLicenseRequest):
        """Transfer a license to another agent."""
        try:
            # Verify license ID matches request
            if license_id != data.license_id:
                return (
                    jsonify(
                        ErrorResponse(
                            error="License ID mismatch between URL and request body"
                        ).model_dump()
                    ),
                    400,
                )

            # Get current agent ID for authorization
            engine = engine_getter()
            agent_id = getattr(engine, "agent_id", "unknown")

            # Validate transfer request
            transfer_result = cloning_rights_service.transfer_license(
                license_id=data.license_id,
                new_licensee_agent_id=data.new_licensee_agent_id,
                transfer_reason=data.transfer_reason,
                transfer_fee=data.transfer_fee,
                authorizing_agent_id=agent_id,
            )

            if transfer_result["success"]:
                response = LicenseTransferResponse(
                    transfer_id=transfer_result["transfer_id"],
                    license_id=data.license_id,
                    old_licensee_agent_id=transfer_result["old_licensee"],
                    new_licensee_agent_id=data.new_licensee_agent_id,
                    transfer_date=datetime.now(timezone.utc).isoformat(),
                    transfer_fee=data.transfer_fee,
                    status="completed",
                )
                return jsonify(response.model_dump()), 200
            else:
                return (
                    jsonify(
                        ErrorResponse(
                            error="License transfer failed",
                            details=transfer_result.get("reason", "Unknown error"),
                        ).model_dump()
                    ),
                    400,
                )

        except ValueError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error transferring license: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to transfer license", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/licenses/<license_id>/revoke", methods=["POST"])
    @require_api_key(["admin"])
    @validate_request(RevokeLicenseRequest)
    async def revoke_license(license_id: str, data: RevokeLicenseRequest):
        """Revoke a license."""
        try:
            # Verify license ID matches request
            if license_id != data.license_id:
                return (
                    jsonify(
                        ErrorResponse(
                            error="License ID mismatch between URL and request body"
                        ).model_dump()
                    ),
                    400,
                )

            # Get current agent ID for authorization
            engine = engine_getter()
            agent_id = getattr(engine, "agent_id", "unknown")

            # Process revocation
            revocation_result = cloning_rights_service.revoke_license(
                license_id=data.license_id,
                revocation_reason=data.revocation_reason,
                refund_amount=data.refund_amount,
                revoking_agent_id=agent_id,
            )

            if revocation_result["success"]:
                return (
                    jsonify(
                        {
                            "license_id": data.license_id,
                            "status": "revoked",
                            "revocation_date": datetime.now(timezone.utc).isoformat(),
                            "refund_amount": data.refund_amount,
                        }
                    ),
                    200,
                )
            else:
                return (
                    jsonify(
                        ErrorResponse(
                            error="License revocation failed",
                            details=revocation_result.get("reason", "Unknown error"),
                        ).model_dump()
                    ),
                    400,
                )

        except ValueError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error revoking license: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to revoke license", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/licenses/batch", methods=["POST"])
    @require_api_key(["admin"])
    @validate_request(BatchLicenseRequest)
    async def create_batch_licenses(data: BatchLicenseRequest):
        """Create licenses for multiple models in batch."""
        try:
            engine = engine_getter()
            agent_id = getattr(engine, "agent_id", "unknown")

            # Process batch license creation
            batch_result = cloning_rights_service.create_batch_licenses(
                model_ids=data.model_ids,
                license_type=data.license_type,
                licensor_agent_id=agent_id,
                licensee_agent_id=data.licensee_agent_id,
                bulk_discount=data.bulk_discount,
            )

            created_licenses = []
            failed_licenses = []

            for model_id, result in batch_result.items():
                if result["success"]:
                    created_licenses.append(
                        {
                            "model_id": model_id,
                            "license_id": result["license_id"],
                            "status": "created",
                        }
                    )
                else:
                    failed_licenses.append(
                        {
                            "model_id": model_id,
                            "error": result["error"],
                            "status": "failed",
                        }
                    )

            return (
                jsonify(
                    {
                        "batch_id": batch_result.get("batch_id"),
                        "created_licenses": created_licenses,
                        "failed_licenses": failed_licenses,
                        "success_count": len(created_licenses),
                        "failure_count": len(failed_licenses),
                        "total_discount_applied": batch_result.get("total_discount", 0),
                    }
                ),
                200 if len(failed_licenses) == 0 else 207,
            )  # 207 = Multi-Status

        except Exception as e:
            logger.error(f"Error creating batch licenses: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to create batch licenses", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    # --- Advanced Compliance Monitoring ---

    @blueprint.route("/compliance/check", methods=["POST"])
    @require_api_key(["read", "admin"])
    @validate_request(ComplianceCheckRequest)
    async def run_compliance_check(data: ComplianceCheckRequest):
        """Run comprehensive compliance check on a model."""
        try:
            # Run compliance analysis
            compliance_result = cloning_rights_service.run_compliance_check(
                model_id=data.model_id,
                check_type=data.check_type,
                time_range_days=data.time_range_days,
            )

            # Calculate next check due date
            next_check_due = (
                datetime.now(timezone.utc) + timedelta(days=30)
            ).isoformat()

            response = ComplianceReportResponse(
                model_id=data.model_id,
                check_type=data.check_type,
                compliance_score=compliance_result["compliance_score"],
                violations=compliance_result["violations"],
                recommendations=compliance_result["recommendations"],
                check_date=datetime.now(timezone.utc).isoformat(),
                next_check_due=next_check_due,
            )

            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"Error running compliance check: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to run compliance check", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    # --- Advanced Evolution Analytics ---

    @blueprint.route("/evolution/analytics", methods=["POST"])
    @require_api_key(["read", "admin"])
    @validate_request(EvolutionAnalyticsRequest)
    async def run_evolution_analytics(data: EvolutionAnalyticsRequest):
        """Run advanced evolution analytics across multiple models."""
        try:
            # Run comprehensive evolution analysis
            analytics_result = evolution_tracking_service.run_advanced_analytics(
                model_ids=data.model_ids,
                analysis_type=data.analysis_type,
                comparison_period_days=data.comparison_period_days,
            )

            response = EvolutionAnalyticsResponse(
                analysis_id=analytics_result["analysis_id"],
                model_ids=data.model_ids,
                analysis_type=data.analysis_type,
                summary=analytics_result["summary"],
                trends=analytics_result["trends"],
                predictions=analytics_result["predictions"],
                risk_assessment=analytics_result["risk_assessment"],
                generated_at=datetime.now(timezone.utc).isoformat(),
            )

            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"Error running evolution analytics: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to run evolution analytics", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/evolution/predictive-alerts", methods=["POST"])
    @require_api_key(["admin"])
    async def setup_predictive_alerts():
        """Setup predictive evolution alerts for proactive monitoring."""
        try:
            request_data = await request.get_json()
            model_ids = request_data.get("model_ids", [])
            alert_thresholds = request_data.get("alert_thresholds", {})
            notification_channels = request_data.get("notification_channels", [])

            # Configure predictive alerts
            alert_config = evolution_tracking_service.setup_predictive_alerts(
                model_ids=model_ids,
                alert_thresholds=alert_thresholds,
                notification_channels=notification_channels,
            )

            return (
                jsonify(
                    {
                        "alert_config_id": alert_config["config_id"],
                        "monitored_models": alert_config["monitored_models"],
                        "active_alerts": alert_config["active_alerts"],
                        "next_evaluation": alert_config["next_evaluation"].isoformat(),
                    }
                ),
                201,
            )

        except Exception as e:
            logger.error(f"Error setting up predictive alerts: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to setup predictive alerts", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    # --- License Analytics ---

    @blueprint.route("/analytics/license-utilization", methods=["GET"])
    @require_api_key(["read", "admin"])
    async def get_license_utilization():
        """Get detailed license utilization analytics."""
        try:
            # Get query parameters
            time_range = request.args.get("time_range_days", 30, type=int)
            model_id = request.args.get("model_id")
            agent_id = request.args.get("agent_id")

            utilization_data = cloning_rights_service.get_license_utilization_analytics(
                time_range_days=time_range, model_id=model_id, agent_id=agent_id
            )

            return jsonify(utilization_data), 200

        except Exception as e:
            logger.error(f"Error getting license utilization: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve license utilization", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/analytics/evolution-trends", methods=["GET"])
    @require_api_key(["read", "admin"])
    async def get_evolution_trends():
        """Get evolution trend analytics across the system."""
        try:
            # Get query parameters
            time_range = request.args.get("time_range_days", 90, type=int)
            trend_type = request.args.get("trend_type", "all")

            trends_data = evolution_tracking_service.get_system_evolution_trends(
                time_range_days=time_range, trend_type=trend_type
            )

            return jsonify(trends_data), 200

        except Exception as e:
            logger.error(f"Error getting evolution trends: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve evolution trends", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    return blueprint
