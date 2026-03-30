"""
Capsules Router - Layered Architecture Operations
==================================================

Endpoints for accessing the gold standard layered capsule structure.
"""

from fastapi import APIRouter

from src.core.contradiction_engine import ContradictionEngine, format_contradictions

# Import gold standard modules
from src.core.layered_capsule_builder import (
    LayeredCapsuleBuilder,
    convert_legacy_capsule,
)

from ._shared import (
    Any,
    AsyncSession,
    CapsuleModel,
    Depends,
    Dict,
    HTTPException,
    List,
    Optional,
    Query,
    Request,
    get_current_user,
    get_current_user_optional,
    get_db_session,
    json,
    logger,
    select,
)

router = APIRouter()


@router.get("/{capsule_id}/layers")
async def get_capsule_layers(
    capsule_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: Optional[Dict] = Depends(get_current_user_optional),
):
    """
    Get the layered structure of a capsule.

    Returns the gold standard structure:
    - events: What literally happened (tool_verified)
    - evidence: What artifacts prove (crypto_verified)
    - interpretation: What the model thinks (model_generated, unverified)
    - judgment: Gated labels (only when earned)
    - trust_posture: Multi-dimensional trust assessment
    """
    # Fetch capsule
    stmt = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
    result = await session.execute(stmt)
    capsule = result.scalar_one_or_none()

    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")

    # Build capsule dict
    capsule_dict = {
        "capsule_id": capsule.capsule_id,
        "timestamp": capsule.timestamp.isoformat() if capsule.timestamp else None,
        "payload": capsule.payload
        if isinstance(capsule.payload, dict)
        else json.loads(capsule.payload or "{}"),
        "verification": capsule.verification
        if isinstance(capsule.verification, dict)
        else json.loads(capsule.verification or "{}"),
        "metadata": {},
    }

    # Check if capsule already has layered structure
    payload = capsule_dict["payload"]
    if "layers" in payload:
        # Already has gold standard structure
        return {
            "capsule_id": capsule_id,
            "schema_version": payload.get("schema_version", "2.0_layered"),
            "layers": payload["layers"],
            "trust_posture": payload.get("trust_posture", {}),
            "verification": capsule_dict["verification"],
            "is_legacy": False,
        }

    # Convert legacy capsule to layered structure
    layered = convert_legacy_capsule(capsule_dict)

    return {
        "capsule_id": capsule_id,
        "schema_version": layered.get("schema_version", "2.0_layered"),
        "layers": layered.get("layers", {}),
        "trust_posture": layered.get("trust_posture", {}),
        "verification": layered.get("verification", {}),
        "is_legacy": True,
        "note": "This capsule was converted from legacy format. Some layer data may be incomplete.",
    }


@router.get("/{capsule_id}/self-inspection")
async def get_capsule_self_inspection(
    capsule_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: Optional[Dict] = Depends(get_current_user_optional),
):
    """
    Run self-inspection on a capsule to detect contradictions.

    Returns:
    - contradictions_found: Number of issues detected
    - critical_count: Number of critical issues
    - warning_count: Number of warnings
    - info_count: Number of info-level issues
    - issues: Detailed list of contradictions
    - formatted: Human-readable summary
    """
    # Fetch capsule
    stmt = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
    result = await session.execute(stmt)
    capsule = result.scalar_one_or_none()

    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")

    # Build capsule dict for analysis
    capsule_dict = {
        "capsule_id": capsule.capsule_id,
        "timestamp": capsule.timestamp.isoformat() if capsule.timestamp else None,
        "payload": capsule.payload
        if isinstance(capsule.payload, dict)
        else json.loads(capsule.payload or "{}"),
        "verification": capsule.verification
        if isinstance(capsule.verification, dict)
        else json.loads(capsule.verification or "{}"),
        "metadata": {},
    }

    # Run contradiction detection
    contradictions = ContradictionEngine.analyze_capsule(capsule_dict)

    # Categorize by severity
    critical = [c for c in contradictions if c.severity == "critical"]
    warnings = [c for c in contradictions if c.severity == "warning"]
    infos = [c for c in contradictions if c.severity == "info"]

    return {
        "capsule_id": capsule_id,
        "contradictions_found": len(contradictions),
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "info_count": len(infos),
        "status": "clean" if len(contradictions) == 0 else "issues_found",
        "issues": [
            {
                "category": c.category,
                "severity": c.severity,
                "description": c.description,
                "field_a": c.field_a,
                "field_b": c.field_b,
                "recommendation": c.recommendation,
            }
            for c in contradictions
        ],
        "formatted": format_contradictions(contradictions),
    }


@router.get("/{capsule_id}/compliance")
async def get_capsule_compliance(
    capsule_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: Optional[Dict] = Depends(get_current_user_optional),
):
    """
    Get honest compliance assessment for a capsule.

    Returns which compliance gates have passed and which are blocking.
    Labels are only claimed when verification gates actually pass.
    """
    # Fetch capsule
    stmt = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
    result = await session.execute(stmt)
    capsule = result.scalar_one_or_none()

    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")

    # Parse data
    payload = (
        capsule.payload
        if isinstance(capsule.payload, dict)
        else json.loads(capsule.payload or "{}")
    )
    verification = (
        capsule.verification
        if isinstance(capsule.verification, dict)
        else json.loads(capsule.verification or "{}")
    )

    # Check gates
    has_signature = bool(verification.get("signature"))
    has_trusted_timestamp = verification.get("timestamp", {}).get("trusted", False)
    has_plain_language = bool(payload.get("plain_language_summary", {}).get("decision"))

    # Run contradiction check for semantic drift
    capsule_dict = {
        "payload": payload,
        "verification": verification,
        "metadata": {},
    }
    contradictions = ContradictionEngine.analyze_capsule(capsule_dict)
    has_semantic_drift = any(c.category == "semantic_drift" for c in contradictions)

    # Build gates passed list
    gates_passed = []
    gates_failed = []

    if has_signature:
        gates_passed.append("signature_verified")
    else:
        gates_failed.append("signature_verified")

    if has_trusted_timestamp:
        gates_passed.append("timestamp_verified")
    else:
        gates_failed.append("timestamp_verified")

    if has_plain_language:
        gates_passed.append("plain_language_summary")
    else:
        gates_failed.append("plain_language_summary")

    if not has_semantic_drift:
        gates_passed.append("no_semantic_drift")
    else:
        gates_failed.append("no_semantic_drift")

    # Determine compliance levels
    is_court_admissible = (
        has_signature and has_trusted_timestamp and not has_semantic_drift
    )

    # Insurance ready requires historical accuracy (we don't have this yet)
    risk_assessment = payload.get("risk_assessment", {})
    is_insurance_ready = (
        bool(risk_assessment.get("historical_accuracy"))
        and risk_assessment.get("similar_decisions_count", 0) >= 3
    )

    # Build blockers list
    blockers = []
    if not has_signature:
        blockers.append("Missing cryptographic signature")
    if not has_trusted_timestamp:
        blockers.append("Missing trusted RFC 3161 timestamp")
    if has_semantic_drift:
        blockers.append("Semantic drift detected (summary doesn't address question)")
    if not is_insurance_ready:
        blockers.append("Insufficient historical accuracy data for insurance readiness")

    return {
        "capsule_id": capsule_id,
        "gates_passed": gates_passed,
        "gates_failed": gates_failed,
        "compliance": {
            "court_admissible": is_court_admissible,
            "insurance_ready": is_insurance_ready,
            "eu_ai_act_article_13": has_plain_language,
            "daubert_standard": is_court_admissible,
        },
        "data_richness": (
            "court_admissible"
            if is_court_admissible
            else "enhanced"
            if has_signature
            else "standard"
        ),
        "blockers": blockers if blockers else None,
        "note": "Labels are only claimed when verification gates actually pass.",
    }
