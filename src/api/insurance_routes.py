"""
Insurance API Routes for UATP Capsule Engine

Endpoints:
- POST /api/v1/insurance/risk-assessment - Get risk assessment for capsule chain
- POST /api/v1/insurance/policies - Create new insurance policy
- GET /api/v1/insurance/policies - List user's policies
- GET /api/v1/insurance/policies/{policy_id} - Get policy details
- PUT /api/v1/insurance/policies/{policy_id}/renew - Renew policy
- PUT /api/v1/insurance/policies/{policy_id}/cancel - Cancel policy
- POST /api/v1/insurance/claims - File new claim
- GET /api/v1/insurance/claims - List user's claims
- GET /api/v1/insurance/claims/{claim_id} - Get claim details
- PUT /api/v1/insurance/claims/{claim_id}/appeal - Appeal denied claim
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ValidationError,
    conint,
    constr,
    field_validator,
)
from quart import Blueprint, jsonify, request

from ..insurance.claims_processor import (
    ClaimEvidence,
    ClaimsProcessor,
    ClaimType,
)
from ..insurance.policy_manager import (
    PolicyHolder,
    PolicyManager,
    PolicyStatus,
    PolicyTerms,
)
from ..insurance.risk_assessor import DecisionCategory, RiskAssessor
from ..utils.timezone_utils import utc_now
from .auth_utils import AuthorizationError, get_current_user, require_auth
from .rate_limiting import rate_limit

# Create blueprint
insurance_bp = Blueprint("insurance", __name__)

# Initialize components (will be properly initialized in app factory)
risk_assessor = RiskAssessor()
policy_manager = PolicyManager()
claims_processor = ClaimsProcessor(policy_manager=policy_manager)


# Request/Response Models


class RiskAssessmentRequest(BaseModel):
    """Request for risk assessment"""

    capsule_chain: List[Dict] = Field(
        ..., min_items=1, max_items=1000, description="Capsule chain to assess"
    )
    decision_category: constr(min_length=1, max_length=100) = Field(
        ..., description="Type of AI decision"
    )
    requested_coverage: conint(ge=1000, le=10_000_000) = Field(
        default=100000, description="Coverage amount in USD (1K-10M)"
    )
    user_id: Optional[constr(min_length=1, max_length=255)] = None

    @field_validator("capsule_chain")
    @classmethod
    def validate_capsule_chain(cls, v):
        """Ensure each capsule has minimum required fields"""
        if not v:
            raise ValueError("Capsule chain cannot be empty")
        for i, capsule in enumerate(v):
            if not isinstance(capsule, dict):
                raise ValueError(f"Capsule {i} must be a dictionary")
            if "capsule_id" not in capsule:
                raise ValueError(f"Capsule {i} missing required field: capsule_id")
        return v


class PolicyCreationRequest(BaseModel):
    """Request to create insurance policy"""

    user_id: constr(min_length=1, max_length=255)
    user_name: constr(min_length=1, max_length=255)
    user_email: EmailStr
    organization: Optional[constr(max_length=255)] = None
    contact_phone: Optional[constr(min_length=10, max_length=20)] = None

    # Policy terms
    coverage_amount: conint(ge=1000, le=10_000_000) = Field(
        ..., description="Coverage amount (1K-10M)"
    )
    decision_category: constr(min_length=1, max_length=100)
    deductible: conint(ge=0, le=100_000) = Field(
        default=1000, description="Deductible amount"
    )
    term_months: conint(ge=1, le=60) = Field(
        default=12, description="Policy term in months (1-60)"
    )

    # Payment
    payment_method_id: Optional[constr(max_length=255)] = None
    auto_activate: bool = False

    @field_validator("contact_phone")
    @classmethod
    def validate_phone(cls, v):
        """Basic phone validation"""
        if v is not None:
            # Remove common formatting characters
            digits = "".join(c for c in v if c.isdigit())
            if len(digits) < 10 or len(digits) > 15:
                raise ValueError("Phone must contain 10-15 digits")
        return v

    @field_validator("deductible")
    @classmethod
    def validate_deductible(cls, v, values):
        """Ensure deductible is reasonable compared to coverage"""
        if "coverage_amount" in values and v > values["coverage_amount"]:
            raise ValueError("Deductible cannot exceed coverage amount")
        return v


class ClaimSubmissionRequest(BaseModel):
    """Request to file insurance claim"""

    policy_id: constr(min_length=1, max_length=255)
    claim_type: constr(min_length=1, max_length=100)
    claimed_amount: conint(ge=1, le=10_000_000) = Field(
        ..., description="Amount claimed (1-10M)"
    )

    # Evidence
    capsule_chain: List[Dict] = Field(..., min_items=1, max_items=1000)
    incident_description: constr(min_length=10, max_length=5000) = Field(
        ..., description="Detailed incident description"
    )
    incident_date: str = Field(..., description="ISO 8601 date of incident")
    harm_description: constr(min_length=10, max_length=5000) = Field(
        ..., description="Description of harm caused"
    )
    financial_impact: Optional[conint(ge=0, le=10_000_000)] = None
    supporting_documents: List[constr(max_length=1000)] = Field(
        default_factory=list, max_items=50
    )
    witness_statements: List[constr(max_length=5000)] = Field(
        default_factory=list, max_items=20
    )

    @field_validator("capsule_chain")
    @classmethod
    def validate_capsule_chain(cls, v):
        """Ensure each capsule has minimum required fields"""
        if not v:
            raise ValueError("Capsule chain cannot be empty")
        for i, capsule in enumerate(v):
            if not isinstance(capsule, dict):
                raise ValueError(f"Capsule {i} must be a dictionary")
            if "capsule_id" not in capsule:
                raise ValueError(f"Capsule {i} missing required field: capsule_id")
        return v

    @field_validator("incident_date")
    @classmethod
    def validate_incident_date(cls, v):
        """Validate incident date format and reasonableness"""
        try:
            incident_dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            # Cannot be in the future
            if incident_dt > utc_now():
                raise ValueError("Incident date cannot be in the future")
            # Cannot be more than 2 years old
            from datetime import timedelta

            if incident_dt < utc_now() - timedelta(days=730):
                raise ValueError("Incident date cannot be more than 2 years old")
        except ValueError as e:
            if "Incident date" in str(e):
                raise
            raise ValueError(f"Invalid date format: {v}. Use ISO 8601 format")
        return v


class ClaimAppealRequest(BaseModel):
    """Request to appeal denied claim"""

    appeal_reason: constr(min_length=20, max_length=5000) = Field(
        ..., description="Detailed reason for appeal (min 20 chars)"
    )
    additional_evidence: Optional[Dict] = Field(
        default=None, description="Additional evidence to support appeal"
    )

    @field_validator("appeal_reason")
    @classmethod
    def validate_appeal_reason(cls, v):
        """Ensure appeal reason is substantive"""
        if not v or v.strip() == "":
            raise ValueError("Appeal reason cannot be empty")
        # Check for minimum word count (at least 5 words)
        words = v.split()
        if len(words) < 5:
            raise ValueError("Appeal reason must contain at least 5 words")
        return v.strip()


# Routes


@insurance_bp.route("/health", methods=["GET"])
async def insurance_health():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "service": "insurance_api",
            "timestamp": utc_now().isoformat(),
            "version": "1.0.0",
        }
    )


@insurance_bp.route("/risk-assessment", methods=["POST"])
@require_auth
@rate_limit(requests_per_minute=30, burst_size=50)
async def assess_risk():
    """
    Perform risk assessment on capsule chain.

    Returns risk score, level, and premium estimate.
    """
    try:
        data = await request.get_json()
        try:
            req = RiskAssessmentRequest(**data)
        except ValidationError as e:
            return jsonify({"error": "Validation failed", "details": e.errors()}), 422

        # Validate decision category
        try:
            category = DecisionCategory(req.decision_category.lower())
        except ValueError:
            return (
                jsonify(
                    {
                        "error": f"Invalid decision_category: {req.decision_category}",
                        "valid_categories": [c.value for c in DecisionCategory],
                    }
                ),
                400,
            )

        # Perform assessment
        assessment = await risk_assessor.assess_capsule_chain(
            capsule_chain=req.capsule_chain,
            decision_category=category,
            requested_coverage=req.requested_coverage,
            user_id=req.user_id,
        )

        # Format response
        return jsonify(
            {
                "assessment": {
                    "risk_score": assessment.overall_score,
                    "risk_level": assessment.risk_level.value,
                    "confidence": assessment.confidence,
                    "premium_estimate": assessment.premium_estimate,
                    "coverage_recommended": assessment.coverage_recommended,
                    "policy_term_months": assessment.policy_term_months,
                },
                "factors": [
                    {
                        "name": f.name,
                        "score": f.score,
                        "weight": f.weight,
                        "description": f.description,
                        "details": f.details,
                    }
                    for f in assessment.factors
                ],
                "conditions": assessment.conditions,
                "exclusions": assessment.exclusions,
                "timestamp": assessment.timestamp.isoformat(),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@insurance_bp.route("/policies", methods=["POST"])
@require_auth
@rate_limit(requests_per_minute=10, burst_size=20)
async def create_policy():
    """
    Create a new insurance policy.

    Requires risk assessment first. Premium is based on risk level.
    """
    try:
        data = await request.get_json()
        try:
            req = PolicyCreationRequest(**data)
        except ValidationError as e:
            return jsonify({"error": "Validation failed", "details": e.errors()}), 422

        # Validate decision category
        try:
            category = DecisionCategory(req.decision_category.lower())
        except ValueError:
            return (
                jsonify(
                    {
                        "error": f"Invalid decision_category: {req.decision_category}",
                    }
                ),
                400,
            )

        # Note: In production, you would fetch risk assessment from recent request
        # For now, we'll create a default risk level
        from ..insurance.risk_assessor import RiskLevel

        # Create policy holder
        holder = PolicyHolder(
            user_id=req.user_id,
            name=req.user_name,
            email=req.user_email,
            organization=req.organization,
            contact_phone=req.contact_phone,
        )

        # Create policy terms
        # In production, these would come from risk assessment
        terms = PolicyTerms(
            coverage_amount=req.coverage_amount,
            deductible=req.deductible,
            premium_monthly=50.0,  # Placeholder
            term_months=req.term_months,
            decision_category=category,
            risk_level=RiskLevel.MEDIUM,  # Placeholder
            conditions=[
                "All AI decisions must be captured in UATP capsules",
                "Capsule chain must be verifiable upon claim",
            ],
            exclusions=[
                "Intentional misuse or manipulation",
                "Decisions without proper documentation",
            ],
        )

        # Create policy
        policy = await policy_manager.create_policy(
            holder=holder,
            terms=terms,
            auto_activate=req.auto_activate,
        )

        return (
            jsonify(
                {
                    "policy_id": policy.policy_id,
                    "status": policy.status.value,
                    "holder": {
                        "user_id": policy.holder.user_id,
                        "name": policy.holder.name,
                        "email": policy.holder.email,
                    },
                    "terms": {
                        "coverage_amount": policy.terms.coverage_amount,
                        "deductible": policy.terms.deductible,
                        "premium_monthly": policy.terms.premium_monthly,
                        "term_months": policy.terms.term_months,
                        "decision_category": policy.terms.decision_category.value,
                        "risk_level": policy.terms.risk_level.value,
                    },
                    "created_at": policy.created_at.isoformat(),
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@insurance_bp.route("/policies", methods=["GET"])
@require_auth
@rate_limit()  # Use default: 60/min
async def list_policies():
    """List insurance policies for a user"""
    try:
        # Get current user from JWT
        current_user = await get_current_user()
        current_user_id = current_user.get("user_id")
        is_admin = "admin" in current_user.get("scopes", [])

        # Filter by current user unless admin
        user_id = request.args.get("user_id")
        if not is_admin:
            user_id = current_user_id  # Force filter to current user

        status = request.args.get("status")
        limit = int(request.args.get("limit", 100))

        # Parse status if provided
        status_filter = None
        if status:
            try:
                status_filter = PolicyStatus(status.lower())
            except ValueError:
                return (
                    jsonify(
                        {
                            "error": f"Invalid status: {status}",
                            "valid_statuses": [s.value for s in PolicyStatus],
                        }
                    ),
                    400,
                )

        policies = await policy_manager.list_policies(
            user_id=user_id,
            status=status_filter,
            limit=limit,
        )

        return jsonify(
            {
                "policies": [
                    {
                        "policy_id": p.policy_id,
                        "status": p.status.value,
                        "holder": {
                            "user_id": p.holder.user_id,
                            "name": p.holder.name,
                        },
                        "coverage_amount": p.terms.coverage_amount,
                        "premium_monthly": p.terms.premium_monthly,
                        "created_at": p.created_at.isoformat(),
                        "expires_at": p.expires_at.isoformat()
                        if p.expires_at
                        else None,
                        "claims_filed": p.claims_filed,
                        "total_paid_out": p.total_paid_out,
                    }
                    for p in policies
                ],
                "count": len(policies),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@insurance_bp.route("/policies/<policy_id>", methods=["GET"])
@require_auth
async def get_policy(policy_id: str):
    """Get detailed policy information"""
    try:
        # Get current user from JWT
        user = await get_current_user()
        user_id = user.get("user_id")

        policy = await policy_manager.get_policy(policy_id)

        # Authorization check: user must own the policy or be an admin
        if policy.holder.user_id != user_id and "admin" not in user.get("scopes", []):
            raise AuthorizationError("You do not have permission to view this policy")

        return jsonify(
            {
                "policy_id": policy.policy_id,
                "status": policy.status.value,
                "holder": {
                    "user_id": policy.holder.user_id,
                    "name": policy.holder.name,
                    "email": policy.holder.email,
                    "organization": policy.holder.organization,
                },
                "terms": {
                    "coverage_amount": policy.terms.coverage_amount,
                    "deductible": policy.terms.deductible,
                    "premium_monthly": policy.terms.premium_monthly,
                    "term_months": policy.terms.term_months,
                    "decision_category": policy.terms.decision_category.value,
                    "risk_level": policy.terms.risk_level.value,
                    "conditions": policy.terms.conditions,
                    "exclusions": policy.terms.exclusions,
                    "max_claims_per_year": policy.terms.max_claims_per_year,
                },
                "coverage_status": {
                    "claims_filed": policy.claims_filed,
                    "total_paid_out": policy.total_paid_out,
                    "remaining_coverage": policy.terms.coverage_amount
                    - policy.total_paid_out,
                },
                "dates": {
                    "created_at": policy.created_at.isoformat(),
                    "activated_at": policy.activated_at.isoformat()
                    if policy.activated_at
                    else None,
                    "expires_at": policy.expires_at.isoformat()
                    if policy.expires_at
                    else None,
                    "next_payment_due": policy.next_payment_due.isoformat()
                    if policy.next_payment_due
                    else None,
                },
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 404


@insurance_bp.route("/policies/<policy_id>/renew", methods=["PUT"])
@require_auth
async def renew_policy(policy_id: str):
    """Renew an expiring policy"""
    try:
        # Get current user from JWT
        user = await get_current_user()
        user_id = user.get("user_id")

        # Fetch policy to check ownership
        policy = await policy_manager.get_policy(policy_id)

        # Authorization check: user must own the policy or be an admin
        if policy.holder.user_id != user_id and "admin" not in user.get("scopes", []):
            raise AuthorizationError("You do not have permission to renew this policy")

        data = await request.get_json() or {}
        new_term_months = data.get("term_months")

        policy = await policy_manager.renew_policy(
            policy_id=policy_id,
            new_term_months=new_term_months,
        )

        return jsonify(
            {
                "policy_id": policy.policy_id,
                "status": policy.status.value,
                "expires_at": policy.expires_at.isoformat()
                if policy.expires_at
                else None,
                "message": "Policy renewed successfully",
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@insurance_bp.route("/policies/<policy_id>/cancel", methods=["PUT"])
@require_auth
async def cancel_policy(policy_id: str):
    """Cancel a policy"""
    try:
        # Get current user from JWT
        user = await get_current_user()
        user_id = user.get("user_id")

        # Fetch policy to check ownership
        policy = await policy_manager.get_policy(policy_id)

        # Authorization check: user must own the policy or be an admin
        if policy.holder.user_id != user_id and "admin" not in user.get("scopes", []):
            raise AuthorizationError("You do not have permission to cancel this policy")

        data = await request.get_json()
        reason = data.get("reason", "User requested cancellation")
        refund_prorated = data.get("refund_prorated", True)

        policy = await policy_manager.cancel_policy(
            policy_id=policy_id,
            reason=reason,
            refund_prorated=refund_prorated,
        )

        return jsonify(
            {
                "policy_id": policy.policy_id,
                "status": policy.status.value,
                "cancelled_at": policy.cancelled_at.isoformat()
                if policy.cancelled_at
                else None,
                "cancellation_reason": policy.cancellation_reason,
                "message": "Policy cancelled successfully",
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@insurance_bp.route("/claims", methods=["POST"])
@require_auth
@rate_limit(requests_per_minute=5, burst_size=10)  # Stricter for claim submissions
async def submit_claim():
    """File a new insurance claim"""
    try:
        # Get current user from JWT
        current_user = await get_current_user()
        current_user_id = current_user.get("user_id")

        data = await request.get_json()
        try:
            req = ClaimSubmissionRequest(**data)
        except ValidationError as e:
            return jsonify({"error": "Validation failed", "details": e.errors()}), 422

        # Fetch policy and check ownership
        policy = await policy_manager.get_policy(req.policy_id)

        # Authorization check: user must own the policy or be an admin
        if policy.holder.user_id != current_user_id and "admin" not in current_user.get(
            "scopes", []
        ):
            raise AuthorizationError(
                "You do not have permission to submit a claim for this policy"
            )

        # Validate claim type
        try:
            claim_type = ClaimType(req.claim_type.lower())
        except ValueError:
            return (
                jsonify(
                    {
                        "error": f"Invalid claim_type: {req.claim_type}",
                        "valid_types": [t.value for t in ClaimType],
                    }
                ),
                400,
            )

        # Parse incident date
        try:
            incident_date = datetime.fromisoformat(
                req.incident_date.replace("Z", "+00:00")
            )
        except:
            return (
                jsonify({"error": "Invalid incident_date format (use ISO 8601)"}),
                400,
            )

        # Create evidence
        evidence = ClaimEvidence(
            capsule_chain=req.capsule_chain,
            incident_description=req.incident_description,
            incident_date=incident_date,
            harm_description=req.harm_description,
            financial_impact=req.financial_impact,
            supporting_documents=req.supporting_documents,
            witness_statements=req.witness_statements,
        )

        # Use policy holder's user ID
        user_id = policy.holder.user_id

        # Submit claim
        claim = await claims_processor.submit_claim(
            policy_id=req.policy_id,
            claimant_user_id=user_id,
            claim_type=claim_type,
            claimed_amount=req.claimed_amount,
            evidence=evidence,
        )

        return (
            jsonify(
                {
                    "claim_id": claim.claim_id,
                    "policy_id": claim.policy_id,
                    "status": claim.status.value,
                    "claim_type": claim.claim_type.value,
                    "claimed_amount": claim.claimed_amount,
                    "submitted_at": claim.submitted_at.isoformat(),
                    "message": "Claim submitted successfully and under review",
                }
            ),
            201,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@insurance_bp.route("/claims", methods=["GET"])
@require_auth
async def list_claims():
    """List insurance claims"""
    try:
        # Get current user from JWT
        current_user = await get_current_user()
        current_user_id = current_user.get("user_id")
        is_admin = "admin" in current_user.get("scopes", [])

        policy_id = request.args.get("policy_id")
        user_id = request.args.get("user_id")

        # Filter by current user unless admin
        if not is_admin:
            user_id = current_user_id  # Force filter to current user

        status = request.args.get("status")
        limit = int(request.args.get("limit", 100))

        # Parse status if provided
        from ..insurance.claims_processor import ClaimStatus

        status_filter = None
        if status:
            try:
                status_filter = ClaimStatus(status.lower())
            except ValueError:
                return (
                    jsonify(
                        {
                            "error": f"Invalid status: {status}",
                        }
                    ),
                    400,
                )

        claims = await claims_processor.list_claims(
            policy_id=policy_id,
            user_id=user_id,
            status=status_filter,
            limit=limit,
        )

        return jsonify(
            {
                "claims": [
                    {
                        "claim_id": c.claim_id,
                        "policy_id": c.policy_id,
                        "status": c.status.value,
                        "claim_type": c.claim_type.value,
                        "claimed_amount": c.claimed_amount,
                        "approved_amount": c.approved_amount,
                        "submitted_at": c.submitted_at.isoformat(),
                        "resolved_at": c.resolved_at.isoformat()
                        if c.resolved_at
                        else None,
                    }
                    for c in claims
                ],
                "count": len(claims),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@insurance_bp.route("/claims/<claim_id>", methods=["GET"])
@require_auth
async def get_claim(claim_id: str):
    """Get detailed claim information"""
    try:
        # Get current user from JWT
        user = await get_current_user()
        user_id = user.get("user_id")

        claim = await claims_processor.get_claim(claim_id)

        # Get policy to check ownership
        policy = await policy_manager.get_policy(claim.policy_id)

        # Authorization check: user must own the policy or be an admin
        if policy.holder.user_id != user_id and "admin" not in user.get("scopes", []):
            raise AuthorizationError("You do not have permission to view this claim")

        return jsonify(
            {
                "claim_id": claim.claim_id,
                "policy_id": claim.policy_id,
                "status": claim.status.value,
                "claim_type": claim.claim_type.value,
                "claimed_amount": claim.claimed_amount,
                "approved_amount": claim.approved_amount,
                "evidence": {
                    "incident_description": claim.evidence.incident_description,
                    "incident_date": claim.evidence.incident_date.isoformat(),
                    "harm_description": claim.evidence.harm_description,
                    "financial_impact": claim.evidence.financial_impact,
                    "chain_length": len(claim.evidence.capsule_chain),
                },
                "investigation": {
                    "chain_verified": claim.investigation.chain_verified,
                    "fault_party": claim.investigation.fault_party,
                    "recommended_payout": claim.investigation.recommended_payout,
                    "findings": claim.investigation.findings,
                }
                if claim.investigation
                else None,
                "dates": {
                    "submitted_at": claim.submitted_at.isoformat(),
                    "reviewed_at": claim.reviewed_at.isoformat()
                    if claim.reviewed_at
                    else None,
                    "resolved_at": claim.resolved_at.isoformat()
                    if claim.resolved_at
                    else None,
                },
                "denial_reason": claim.denial_reason,
                "payout_transaction_id": claim.payout_transaction_id,
                "notes": claim.notes,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 404


@insurance_bp.route("/claims/<claim_id>/appeal", methods=["PUT"])
@require_auth
async def appeal_claim(claim_id: str):
    """Appeal a denied claim"""
    try:
        # Get current user from JWT
        user = await get_current_user()
        user_id = user.get("user_id")

        # Fetch claim to check ownership
        claim = await claims_processor.get_claim(claim_id)

        # Get policy to check ownership
        policy = await policy_manager.get_policy(claim.policy_id)

        # Authorization check: user must own the policy or be an admin
        if policy.holder.user_id != user_id and "admin" not in user.get("scopes", []):
            raise AuthorizationError("You do not have permission to appeal this claim")

        data = await request.get_json()
        try:
            req = ClaimAppealRequest(**data)
        except ValidationError as e:
            return jsonify({"error": "Validation failed", "details": e.errors()}), 422

        claim = await claims_processor.appeal_claim(
            claim_id=claim_id,
            appeal_reason=req.appeal_reason,
            additional_evidence=req.additional_evidence,
        )

        return jsonify(
            {
                "claim_id": claim.claim_id,
                "status": claim.status.value,
                "message": "Appeal submitted successfully and under review",
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Export blueprint
__all__ = ["insurance_bp"]
