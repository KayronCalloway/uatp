"""
Compliance API for UATP Capsule Engine

This module provides API endpoints for regulatory compliance management,
including compliance assessments, reporting, and monitoring.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from quart import Blueprint, jsonify, request
from quart_schema import validate_request

from .schemas import ErrorResponse
from compliance.regulatory_compliance_framework import (
    ComplianceStatus,
    RegulatoryFramework,
    ComplianceRisk,
    create_regulatory_compliance_framework,
)

logger = logging.getLogger(__name__)


# --- Schema Definitions ---


class ComplianceAssessmentRequest(BaseModel):
    """Schema for initiating compliance assessment."""

    framework: str = Field(
        description="Regulatory framework (gdpr, ai_act, nist_ai_rmf)"
    )
    system_id: str = Field(description="System ID to assess")
    assessor_id: str = Field(default="system", description="Assessor identifier")
    evidence: Optional[Dict[str, Any]] = Field(None, description="Supporting evidence")


class ComplianceReportRequest(BaseModel):
    """Schema for generating compliance report."""

    reporting_period_days: int = Field(
        default=90, gt=0, le=365, description="Reporting period in days"
    )
    frameworks: Optional[List[str]] = Field(None, description="Frameworks to include")
    include_trends: bool = Field(default=True, description="Include trend analysis")


class ScheduleAssessmentRequest(BaseModel):
    """Schema for scheduling compliance assessment."""

    framework: str = Field(description="Regulatory framework")
    system_id: str = Field(description="System ID")
    scheduled_date: str = Field(description="Scheduled date (ISO format)")
    assessor_id: str = Field(default="system", description="Assessor identifier")
    notify_stakeholders: bool = Field(default=True, description="Send notifications")


class ComplianceAssessmentResponse(BaseModel):
    """Schema for compliance assessment response."""

    assessment_id: str
    framework: str
    system_id: str
    status: str
    score: float = Field(ge=0, le=1, description="Compliance score (0-1)")
    requirements_total: int
    requirements_met: int
    requirements_failed: int
    risk_level: str
    critical_findings: List[Dict[str, Any]]
    recommendations: List[str]
    assessed_at: str
    next_assessment_due: Optional[str]


class ComplianceReportResponse(BaseModel):
    """Schema for compliance report response."""

    report_id: str
    generated_at: str
    reporting_period_start: str
    reporting_period_end: str
    overall_status: str
    overall_score: float = Field(ge=0, le=1)
    frameworks_assessed: List[str]
    high_risk_items: List[Dict[str, Any]]
    mitigation_plans: List[Dict[str, Any]]
    improvement_recommendations: List[str]


class ComplianceStatusResponse(BaseModel):
    """Schema for compliance status response."""

    system_id: Optional[str]
    status: str
    frameworks: List[Dict[str, Any]]
    last_updated: str


class ComplianceRequirementsResponse(BaseModel):
    """Schema for compliance requirements response."""

    framework: str
    requirements: List[Dict[str, Any]]
    total_requirements: int
    mandatory_requirements: int


def create_compliance_api_blueprint(engine_getter, require_api_key):
    """Create and return the compliance API blueprint."""
    blueprint = Blueprint("compliance_api", __name__, url_prefix="/api/v1/compliance")

    # Initialize compliance framework
    compliance_framework = create_regulatory_compliance_framework()

    # --- Core Compliance Endpoints ---

    @blueprint.route("/assessments", methods=["POST"])
    @require_api_key(["admin"])
    @validate_request(ComplianceAssessmentRequest)
    async def conduct_compliance_assessment(data: ComplianceAssessmentRequest):
        """Conduct a compliance assessment."""
        try:
            # Validate framework
            try:
                framework = RegulatoryFramework(data.framework.lower())
            except ValueError:
                return (
                    jsonify(
                        ErrorResponse(
                            error=f"Invalid framework: {data.framework}",
                            details="Supported frameworks: gdpr, ai_act, nist_ai_rmf",
                        ).model_dump()
                    ),
                    400,
                )

            # Conduct assessment
            assessment = await compliance_framework.conduct_compliance_assessment(
                framework=framework,
                system_id=data.system_id,
                assessor_id=data.assessor_id,
                evidence=data.evidence,
            )

            response = ComplianceAssessmentResponse(
                assessment_id=assessment.assessment_id,
                framework=assessment.framework.value,
                system_id=assessment.system_id,
                status=assessment.status.value,
                score=assessment.score,
                requirements_total=assessment.requirements_total,
                requirements_met=assessment.requirements_met,
                requirements_failed=assessment.requirements_failed,
                risk_level=assessment.risk_level.value,
                critical_findings=assessment.critical_findings,
                recommendations=assessment.recommendations,
                assessed_at=assessment.assessed_at.isoformat(),
                next_assessment_due=assessment.next_assessment_due.isoformat()
                if assessment.next_assessment_due
                else None,
            )

            return jsonify(response.model_dump()), 201

        except Exception as e:
            logger.error(f"Error conducting compliance assessment: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to conduct compliance assessment", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/reports", methods=["POST"])
    @require_api_key(["read", "admin"])
    @validate_request(ComplianceReportRequest)
    async def generate_compliance_report(data: ComplianceReportRequest):
        """Generate a comprehensive compliance report."""
        try:
            # Parse frameworks if provided
            frameworks = None
            if data.frameworks:
                try:
                    frameworks = [
                        RegulatoryFramework(f.lower()) for f in data.frameworks
                    ]
                except ValueError as e:
                    return (
                        jsonify(
                            ErrorResponse(
                                error="Invalid framework in list", details=str(e)
                            ).model_dump()
                        ),
                        400,
                    )

            # Generate report
            report = await compliance_framework.generate_compliance_report(
                reporting_period_days=data.reporting_period_days,
                include_frameworks=frameworks,
            )

            response = ComplianceReportResponse(
                report_id=report.report_id,
                generated_at=report.generated_at.isoformat(),
                reporting_period_start=report.reporting_period_start.isoformat(),
                reporting_period_end=report.reporting_period_end.isoformat(),
                overall_status=report.overall_status.value,
                overall_score=report.overall_score,
                frameworks_assessed=[
                    f.value for f in report.framework_assessments.keys()
                ],
                high_risk_items=report.high_risk_items,
                mitigation_plans=report.mitigation_plans,
                improvement_recommendations=report.improvement_recommendations,
            )

            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"Error generating compliance report: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to generate compliance report", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/status", methods=["GET"])
    @require_api_key(["read", "admin"])
    async def get_compliance_status():
        """Get compliance status."""
        try:
            system_id = request.args.get("system_id")

            status = compliance_framework.get_compliance_status(system_id)

            response = ComplianceStatusResponse(
                system_id=system_id,
                status=status.get("status", "unknown"),
                frameworks=status.get("frameworks", []),
                last_updated=datetime.now(timezone.utc).isoformat(),
            )

            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"Error getting compliance status: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve compliance status", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/requirements/<framework>", methods=["GET"])
    @require_api_key(["read", "admin"])
    async def get_compliance_requirements(framework: str):
        """Get compliance requirements for a specific framework."""
        try:
            # Validate framework
            try:
                framework_enum = RegulatoryFramework(framework.lower())
            except ValueError:
                return (
                    jsonify(
                        ErrorResponse(
                            error=f"Invalid framework: {framework}",
                            details="Supported frameworks: gdpr, ai_act, nist_ai_rmf",
                        ).model_dump()
                    ),
                    400,
                )

            requirements = compliance_framework.get_compliance_requirements(
                framework_enum
            )

            response = ComplianceRequirementsResponse(
                framework=framework_enum.value,
                requirements=requirements,
                total_requirements=len(requirements),
                mandatory_requirements=len(
                    [r for r in requirements if r.get("mandatory", True)]
                ),
            )

            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"Error getting compliance requirements: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve compliance requirements",
                        details=str(e),
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/assessments/schedule", methods=["POST"])
    @require_api_key(["admin"])
    @validate_request(ScheduleAssessmentRequest)
    async def schedule_compliance_assessment(data: ScheduleAssessmentRequest):
        """Schedule a compliance assessment."""
        try:
            # Validate framework
            try:
                framework = RegulatoryFramework(data.framework.lower())
            except ValueError:
                return (
                    jsonify(
                        ErrorResponse(
                            error=f"Invalid framework: {data.framework}"
                        ).model_dump()
                    ),
                    400,
                )

            # Parse scheduled date
            try:
                scheduled_date = datetime.fromisoformat(
                    data.scheduled_date.replace("Z", "+00:00")
                )
            except ValueError:
                return (
                    jsonify(
                        ErrorResponse(
                            error="Invalid date format",
                            details="Use ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)",
                        ).model_dump()
                    ),
                    400,
                )

            # Validate date is in the future
            if scheduled_date <= datetime.now(timezone.utc):
                return (
                    jsonify(
                        ErrorResponse(
                            error="Scheduled date must be in the future"
                        ).model_dump()
                    ),
                    400,
                )

            # Schedule assessment
            schedule_id = await compliance_framework.schedule_assessment(
                framework=framework,
                system_id=data.system_id,
                scheduled_date=scheduled_date,
                assessor_id=data.assessor_id,
            )

            return (
                jsonify(
                    {
                        "schedule_id": schedule_id,
                        "framework": framework.value,
                        "system_id": data.system_id,
                        "scheduled_date": scheduled_date.isoformat(),
                        "assessor_id": data.assessor_id,
                        "status": "scheduled",
                    }
                ),
                201,
            )

        except Exception as e:
            logger.error(f"Error scheduling assessment: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to schedule assessment", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/assessments/<assessment_id>", methods=["GET"])
    @require_api_key(["read", "admin"])
    async def get_assessment_details(assessment_id: str):
        """Get details of a specific assessment."""
        try:
            if assessment_id not in compliance_framework.assessments:
                return (
                    jsonify(
                        ErrorResponse(
                            error=f"Assessment {assessment_id} not found"
                        ).model_dump()
                    ),
                    404,
                )

            assessment = compliance_framework.assessments[assessment_id]

            response = ComplianceAssessmentResponse(
                assessment_id=assessment.assessment_id,
                framework=assessment.framework.value,
                system_id=assessment.system_id,
                status=assessment.status.value,
                score=assessment.score,
                requirements_total=assessment.requirements_total,
                requirements_met=assessment.requirements_met,
                requirements_failed=assessment.requirements_failed,
                risk_level=assessment.risk_level.value,
                critical_findings=assessment.critical_findings,
                recommendations=assessment.recommendations,
                assessed_at=assessment.assessed_at.isoformat(),
                next_assessment_due=assessment.next_assessment_due.isoformat()
                if assessment.next_assessment_due
                else None,
            )

            return jsonify(response.model_dump()), 200

        except Exception as e:
            logger.error(f"Error getting assessment details: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve assessment details", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/frameworks", methods=["GET"])
    @require_api_key(["read", "admin"])
    async def get_supported_frameworks():
        """Get list of supported regulatory frameworks."""
        try:
            frameworks = [
                {
                    "framework": framework.value,
                    "name": framework.value.replace("_", " ").title(),
                    "active": framework in compliance_framework.active_frameworks,
                    "requirements_count": len(
                        compliance_framework.requirements.get(framework, [])
                    ),
                }
                for framework in RegulatoryFramework
            ]

            return (
                jsonify(
                    {
                        "supported_frameworks": frameworks,
                        "active_count": len(compliance_framework.active_frameworks),
                        "total_count": len(RegulatoryFramework),
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error(f"Error getting supported frameworks: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve supported frameworks", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/health", methods=["GET"])
    async def compliance_health_check():
        """Check compliance system health."""
        try:
            status = compliance_framework.get_compliance_status()

            health_status = {
                "compliance_system": "healthy",
                "active_frameworks": len(compliance_framework.active_frameworks),
                "total_assessments": len(compliance_framework.assessments),
                "monitoring_active": compliance_framework.monitoring_active,
                "last_global_assessment": compliance_framework.last_global_assessment.isoformat()
                if compliance_framework.last_global_assessment
                else None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return jsonify(health_status), 200

        except Exception as e:
            logger.error(f"Error checking compliance health: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to check compliance health", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    return blueprint
