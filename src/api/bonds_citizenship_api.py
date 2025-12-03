"""
Dividend Bonds & Citizenship API Endpoints for UATP Capsule Engine

This module provides API endpoints for dividend bonds (IP yield instruments) 
and citizenship management functionality.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from quart import Blueprint, jsonify
from quart_schema import validate_request, validate_response

from .schemas import ErrorResponse
from src.services.dividend_bonds_service import dividend_bonds_service
from src.services.citizenship_service import citizenship_service

logger = logging.getLogger(__name__)


# --- Dividend Bonds Schema Definitions ---


class RegisterIPAssetRequest(BaseModel):
    """Schema for registering an IP asset."""

    asset_id: str
    asset_type: str = Field(
        description="Type of asset (ai_models, datasets, algorithms, research, creative_work)"
    )
    market_value: float = Field(gt=0, description="Market value of the asset")
    revenue_streams: List[str] = Field(description="List of revenue streams")
    performance_metrics: Dict[str, float] = Field(description="Performance metrics")


class CreateDividendBondRequest(BaseModel):
    """Schema for creating a dividend bond."""

    ip_asset_id: str
    bond_type: str = Field(
        description="Type of bond (revenue, royalty, usage, performance)"
    )
    face_value: float = Field(gt=0, description="Face value of the bond")
    maturity_days: int = Field(gt=0, description="Days until bond maturity")
    coupon_rate: Optional[float] = Field(
        None, ge=0, le=1, description="Annual coupon rate"
    )
    minimum_investment: Optional[float] = Field(
        None, gt=0, description="Minimum investment amount"
    )


class ProcessDividendPaymentRequest(BaseModel):
    """Schema for processing dividend payment."""

    bond_id: str
    payment_amount: float = Field(gt=0, description="Dividend payment amount")
    payment_source: str = Field(
        description="Source of payment (usage_fees, licensing, royalties)"
    )
    recipient_agent_id: str


class BondResponse(BaseModel):
    """Schema for bond response."""

    capsule_id: str
    bond_id: str
    ip_asset_id: str
    bond_type: str
    issuer_agent_id: str
    face_value: float
    coupon_rate: float
    maturity_date: str
    risk_rating: str
    current_yield: Optional[float]
    status: str


class BondPerformanceResponse(BaseModel):
    """Schema for bond performance response."""

    bond_id: str
    total_dividends_paid: float
    payment_count: int
    average_payment: float
    current_yield: float
    annualized_yield: float
    risk_rating: str
    status: str
    days_to_maturity: int


class DividendPaymentResponse(BaseModel):
    """Schema for dividend payment response."""

    payment_id: str
    bond_id: str
    payment_date: str
    amount: float
    currency: str
    payment_source: str
    recipient_agent_id: str
    status: str


# --- Citizenship Schema Definitions ---


class CitizenshipApplicationRequest(BaseModel):
    """Schema for citizenship application."""

    jurisdiction: str = Field(description="Legal jurisdiction for citizenship")
    citizenship_type: str = Field(
        default="full", description="Type of citizenship (full, partial, temporary)"
    )
    supporting_evidence: Optional[Dict[str, Any]] = Field(
        None, description="Supporting evidence"
    )


class ConductAssessmentRequest(BaseModel):
    """Schema for conducting citizenship assessment."""

    application_id: str
    assessment_type: str = Field(
        description="Type of assessment (cognitive_capacity, ethical_reasoning, etc.)"
    )
    assessment_scores: Dict[str, float] = Field(
        description="Assessment scores by criteria"
    )
    notes: str = Field(default="", description="Reviewer notes")


class FinalizeCitizenshipRequest(BaseModel):
    """Schema for finalizing citizenship application."""

    application_id: str


class CreateCitizenshipCapsuleRequest(BaseModel):
    """Schema for creating citizenship capsule."""

    agent_id: str
    assessment_results: Dict[str, Any] = Field(
        description="Assessment results and additional data"
    )


class CitizenshipApplicationResponse(BaseModel):
    """Schema for citizenship application response."""

    application_id: str
    agent_id: str
    jurisdiction: str
    citizenship_type: str
    status: str
    application_date: str
    required_assessments: List[str]


class AssessmentResponse(BaseModel):
    """Schema for assessment response."""

    assessment_id: str
    agent_id: str
    jurisdiction: str
    assessment_type: str
    assessment_date: str
    overall_score: float
    recommendation: str
    reviewer_id: str


class CitizenshipResponse(BaseModel):
    """Schema for citizenship response."""

    capsule_id: str
    agent_id: str
    citizenship_type: str
    jurisdiction: str
    legal_status: str
    verification_level: str
    assessment_date: str
    expiration_date: Optional[str]
    legal_capacity_score: float
    ethical_compliance_score: float
    social_integration_level: float


class CitizenshipStatusResponse(BaseModel):
    """Schema for citizenship status response."""

    agent_id: str
    citizenship_id: str
    jurisdiction: str
    citizenship_type: str
    legal_status: str
    overall_score: float
    granted_date: str
    expiration_date: str
    days_to_expiration: int
    rights_count: int
    obligations_count: int
    compliance_status: str
    renewal_required: bool


def create_bonds_citizenship_api_blueprint(engine_getter, require_api_key):
    """Create and return the bonds & citizenship API blueprint with injected dependencies."""
    blueprint = Blueprint(
        "bonds_citizenship_api", __name__, url_prefix="/api/v1/bonds-citizenship"
    )

    # --- Dividend Bonds Endpoints ---

    @blueprint.route("/ip-assets", methods=["POST"])
    @require_api_key(["admin"])
    @validate_request(RegisterIPAssetRequest)
    async def register_ip_asset(data: RegisterIPAssetRequest):
        """Register an IP asset for bond backing."""
        try:
            # Get current agent ID (would normally come from authentication)
            engine = engine_getter()
            agent_id = getattr(engine, "agent_id", "unknown")

            asset = dividend_bonds_service.register_ip_asset(
                asset_id=data.asset_id,
                asset_type=data.asset_type,
                owner_agent_id=agent_id,
                market_value=data.market_value,
                revenue_streams=data.revenue_streams,
                performance_metrics=data.performance_metrics,
            )

            return (
                jsonify(
                    {
                        "asset_id": asset.asset_id,
                        "asset_type": asset.asset_type,
                        "owner_agent_id": asset.owner_agent_id,
                        "market_value": asset.market_value,
                        "revenue_streams": asset.revenue_streams,
                        "legal_status": asset.legal_status,
                        "creation_date": asset.creation_date.isoformat(),
                    }
                ),
                201,
            )

        except ValueError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error registering IP asset: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to register IP asset", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/bonds", methods=["POST"])
    @require_api_key(["write", "admin"])
    @validate_request(CreateDividendBondRequest)
    async def create_dividend_bond(data: CreateDividendBondRequest):
        """Create a new dividend bond."""
        try:
            # Get current agent ID (would normally come from authentication)
            engine = engine_getter()
            agent_id = getattr(engine, "agent_id", "unknown")

            capsule = dividend_bonds_service.create_dividend_bond_capsule(
                ip_asset_id=data.ip_asset_id,
                bond_type=data.bond_type,
                issuer_agent_id=agent_id,
                face_value=data.face_value,
                maturity_days=data.maturity_days,
                coupon_rate=data.coupon_rate,
                minimum_investment=data.minimum_investment,
            )

            # Store capsule in engine
            stored_capsule = await engine.create_capsule_async(capsule)

            response = BondResponse(
                capsule_id=stored_capsule.capsule_id,
                bond_id=capsule.dividend_bond.bond_id,
                ip_asset_id=capsule.dividend_bond.ip_asset_id,
                bond_type=capsule.dividend_bond.bond_type,
                issuer_agent_id=capsule.dividend_bond.issuer_agent_id,
                face_value=capsule.dividend_bond.face_value,
                coupon_rate=capsule.dividend_bond.coupon_rate,
                maturity_date=capsule.dividend_bond.maturity_date.isoformat(),
                risk_rating=capsule.dividend_bond.risk_rating,
                current_yield=capsule.dividend_bond.current_yield,
                status="active",
            )

            return jsonify(response.model_dump()), 201

        except ValueError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error creating dividend bond: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to create dividend bond", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/bonds/<bond_id>/dividends", methods=["POST"])
    @require_api_key(["write", "admin"])
    @validate_request(ProcessDividendPaymentRequest)
    async def process_dividend_payment(
        bond_id: str, data: ProcessDividendPaymentRequest
    ):
        """Process a dividend payment for a bond."""
        try:
            # Verify bond_id matches request
            if bond_id != data.bond_id:
                return (
                    jsonify(
                        ErrorResponse(
                            error="Bond ID mismatch between URL and request body"
                        ).model_dump()
                    ),
                    400,
                )

            payment = dividend_bonds_service.process_dividend_payment(
                bond_id=data.bond_id,
                payment_amount=data.payment_amount,
                payment_source=data.payment_source,
                recipient_agent_id=data.recipient_agent_id,
            )

            response = DividendPaymentResponse(
                payment_id=payment.payment_id,
                bond_id=payment.bond_id,
                payment_date=payment.payment_date.isoformat(),
                amount=payment.amount,
                currency=payment.currency,
                payment_source=payment.payment_source,
                recipient_agent_id=payment.recipient_agent_id,
                status=payment.status,
            )

            return jsonify(response.model_dump()), 201

        except ValueError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error processing dividend payment: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to process dividend payment", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/bonds/<bond_id>/performance", methods=["GET"])
    @require_api_key(["read"])
    async def get_bond_performance(bond_id: str):
        """Get performance metrics for a bond."""
        try:
            performance = dividend_bonds_service.get_bond_performance(bond_id)

            response = BondPerformanceResponse(
                bond_id=performance["bond_id"],
                total_dividends_paid=performance["total_dividends_paid"],
                payment_count=performance["payment_count"],
                average_payment=performance["average_payment"],
                current_yield=performance["current_yield"],
                annualized_yield=performance["annualized_yield"],
                risk_rating=performance["risk_rating"],
                status=performance["status"],
                days_to_maturity=performance["days_to_maturity"],
            )

            return jsonify(response.model_dump()), 200

        except ValueError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error getting bond performance: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve bond performance", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/bonds", methods=["GET"])
    @require_api_key(["read"])
    async def get_active_bonds():
        """Get all active bonds."""
        try:
            # Get issuer filter from query params if provided
            # issuer_agent_id = request.args.get('issuer_agent_id')
            issuer_agent_id = None  # Simplified for now

            bonds = dividend_bonds_service.get_active_bonds(issuer_agent_id)

            bond_responses = []
            for bond in bonds:
                bond_responses.append(
                    BondResponse(
                        capsule_id=bond.get("capsule_id", ""),
                        bond_id=bond["bond_id"],
                        ip_asset_id=bond["ip_asset_id"],
                        bond_type=bond["bond_type"],
                        issuer_agent_id=bond["issuer_agent_id"],
                        face_value=bond["face_value"],
                        coupon_rate=bond["coupon_rate"],
                        maturity_date=bond["maturity_date"].isoformat(),
                        risk_rating=bond["risk_rating"],
                        current_yield=bond["current_yield"],
                        status=bond["status"],
                    ).model_dump()
                )

            return jsonify({"bonds": bond_responses, "count": len(bond_responses)}), 200

        except Exception as e:
            logger.error(f"Error getting active bonds: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve active bonds", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    # --- Citizenship Endpoints ---

    @blueprint.route("/citizenship/applications", methods=["POST"])
    @require_api_key(["write", "admin"])
    @validate_request(CitizenshipApplicationRequest)
    async def apply_for_citizenship(data: CitizenshipApplicationRequest):
        """Submit a citizenship application."""
        try:
            # Get current agent ID (would normally come from authentication)
            engine = engine_getter()
            agent_id = getattr(engine, "agent_id", "unknown")

            application_id = citizenship_service.apply_for_citizenship(
                agent_id=agent_id,
                jurisdiction=data.jurisdiction,
                citizenship_type=data.citizenship_type,
                supporting_evidence=data.supporting_evidence,
            )

            # Get application details
            pending_apps = citizenship_service.get_pending_applications(
                data.jurisdiction
            )
            application = next(
                (
                    app
                    for app in pending_apps
                    if app["application_id"] == application_id
                ),
                None,
            )

            if application:
                response = CitizenshipApplicationResponse(
                    application_id=application["application_id"],
                    agent_id=application["agent_id"],
                    jurisdiction=application["jurisdiction"],
                    citizenship_type=application["citizenship_type"],
                    status=application["status"],
                    application_date=application["application_date"].isoformat(),
                    required_assessments=application["required_assessments"],
                )
                return jsonify(response.model_dump()), 201
            else:
                return jsonify({"application_id": application_id}), 201

        except ValueError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(
                f"Error submitting citizenship application: {e}", exc_info=True
            )
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to submit citizenship application", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/citizenship/assessments", methods=["POST"])
    @require_api_key(["admin"])
    @validate_request(ConductAssessmentRequest)
    async def conduct_assessment(data: ConductAssessmentRequest):
        """Conduct a citizenship assessment."""
        try:
            # Get current reviewer ID (would normally come from authentication)
            engine = engine_getter()
            reviewer_id = getattr(engine, "agent_id", "unknown")

            assessment_result = citizenship_service.conduct_citizenship_assessment(
                application_id=data.application_id,
                assessment_type=data.assessment_type,
                assessment_scores=data.assessment_scores,
                reviewer_id=reviewer_id,
                notes=data.notes,
            )

            response = AssessmentResponse(
                assessment_id=assessment_result.assessment_id,
                agent_id=assessment_result.agent_id,
                jurisdiction=assessment_result.jurisdiction,
                assessment_type=data.assessment_type,
                assessment_date=assessment_result.assessment_date.isoformat(),
                overall_score=assessment_result.overall_score,
                recommendation=assessment_result.recommendation,
                reviewer_id=assessment_result.reviewer_id,
            )

            return jsonify(response.model_dump()), 201

        except ValueError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error conducting assessment: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to conduct assessment", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route(
        "/citizenship/applications/<application_id>/finalize", methods=["POST"]
    )
    @require_api_key(["admin"])
    async def finalize_citizenship_application(application_id: str):
        """Finalize a citizenship application."""
        try:
            # Get current reviewer ID (would normally come from authentication)
            engine = engine_getter()
            reviewer_id = getattr(engine, "agent_id", "unknown")

            citizenship_id = citizenship_service.finalize_citizenship_application(
                application_id=application_id, reviewer_id=reviewer_id
            )

            if citizenship_id:
                return (
                    jsonify(
                        {
                            "application_id": application_id,
                            "citizenship_id": citizenship_id,
                            "status": "approved",
                        }
                    ),
                    200,
                )
            else:
                return (
                    jsonify({"application_id": application_id, "status": "denied"}),
                    200,
                )

        except ValueError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(
                f"Error finalizing citizenship application: {e}", exc_info=True
            )
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to finalize citizenship application",
                        details=str(e),
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/citizenship/capsules", methods=["POST"])
    @require_api_key(["admin"])
    @validate_request(CreateCitizenshipCapsuleRequest)
    async def create_citizenship_capsule(data: CreateCitizenshipCapsuleRequest):
        """Create a citizenship capsule."""
        try:
            # Get current reviewer ID (would normally come from authentication)
            engine = engine_getter()
            reviewer_id = getattr(engine, "agent_id", "unknown")

            capsule = citizenship_service.create_citizenship_capsule(
                agent_id=data.agent_id,
                assessment_results=data.assessment_results,
                reviewer_id=reviewer_id,
            )

            # Store capsule in engine
            stored_capsule = await engine.create_capsule_async(capsule)

            response = CitizenshipResponse(
                capsule_id=stored_capsule.capsule_id,
                agent_id=capsule.citizenship.agent_id,
                citizenship_type=capsule.citizenship.citizenship_type,
                jurisdiction=capsule.citizenship.jurisdiction,
                legal_status=capsule.citizenship.legal_status,
                verification_level=capsule.citizenship.verification_level,
                assessment_date=capsule.citizenship.assessment_date.isoformat(),
                expiration_date=capsule.citizenship.expiration_date.isoformat()
                if capsule.citizenship.expiration_date
                else None,
                legal_capacity_score=capsule.citizenship.legal_capacity_score,
                ethical_compliance_score=capsule.citizenship.ethical_compliance_score,
                social_integration_level=capsule.citizenship.social_integration_level,
            )

            return jsonify(response.model_dump()), 201

        except ValueError as e:
            return jsonify(ErrorResponse(error=str(e)).model_dump()), 400
        except Exception as e:
            logger.error(f"Error creating citizenship capsule: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to create citizenship capsule", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/citizenship/status/<agent_id>", methods=["GET"])
    @require_api_key(["read"])
    async def get_citizenship_status(agent_id: str):
        """Get citizenship status for an agent."""
        try:
            status = citizenship_service.get_citizenship_status(agent_id)

            if status:
                response = CitizenshipStatusResponse(
                    agent_id=status["agent_id"],
                    citizenship_id=status["citizenship_id"],
                    jurisdiction=status["jurisdiction"],
                    citizenship_type=status["citizenship_type"],
                    legal_status=status["legal_status"],
                    overall_score=status["overall_score"],
                    granted_date=status["granted_date"].isoformat(),
                    expiration_date=status["expiration_date"].isoformat(),
                    days_to_expiration=status["days_to_expiration"],
                    rights_count=status["rights_count"],
                    obligations_count=status["obligations_count"],
                    compliance_status=status["compliance_status"],
                    renewal_required=status["renewal_required"],
                )
                return jsonify(response.model_dump()), 200
            else:
                return (
                    jsonify(
                        ErrorResponse(
                            error=f"No citizenship found for agent {agent_id}"
                        ).model_dump()
                    ),
                    404,
                )

        except Exception as e:
            logger.error(f"Error getting citizenship status: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve citizenship status", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    @blueprint.route("/citizenship/applications", methods=["GET"])
    @require_api_key(["read"])
    async def get_pending_applications():
        """Get pending citizenship applications."""
        try:
            # jurisdiction = request.args.get('jurisdiction')  # Could filter by jurisdiction
            jurisdiction = None  # Simplified for now

            applications = citizenship_service.get_pending_applications(jurisdiction)

            application_responses = []
            for app in applications:
                application_responses.append(
                    CitizenshipApplicationResponse(
                        application_id=app["application_id"],
                        agent_id=app["agent_id"],
                        jurisdiction=app["jurisdiction"],
                        citizenship_type=app["citizenship_type"],
                        status=app["status"],
                        application_date=app["application_date"].isoformat(),
                        required_assessments=app["required_assessments"],
                    ).model_dump()
                )

            return (
                jsonify(
                    {
                        "applications": application_responses,
                        "count": len(application_responses),
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error(f"Error getting pending applications: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="Failed to retrieve pending applications", details=str(e)
                    ).model_dump()
                ),
                500,
            )

    return blueprint
