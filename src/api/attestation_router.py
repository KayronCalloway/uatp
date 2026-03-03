"""
Hardware Attestation API Router - UATP 7.2 Hardware Attestation

Provides REST API endpoints for:
- Generating attestation challenges
- Submitting attestation data
- Verifying attestation records
"""

import base64
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.auth_middleware import get_current_user, get_current_user_optional
from ..core.database import db
from ..security.attestation import (
    AttestationType,
    hardware_attestation_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/attestation", tags=["Hardware Attestation"])


# --- Request/Response Models ---


class ChallengeRequest(BaseModel):
    """Request body for generating attestation challenge."""

    attestation_type: str = Field(
        description="Type: apple_secure_enclave, android_tee, nvidia_cc, intel_sgx, simulated"
    )
    device_id_hint: Optional[str] = Field(
        None, description="Optional hint about expected device"
    )


class ChallengeResponse(BaseModel):
    """Response containing attestation challenge."""

    challenge_id: str
    nonce: str
    attestation_type: str
    expires_at: str


class AttestationSubmitRequest(BaseModel):
    """Request body for submitting attestation."""

    challenge_id: str = Field(description="Challenge ID from /challenge")
    attestation_data: str = Field(
        description="Base64-encoded attestation blob from hardware"
    )
    certificate_chain: List[str] = Field(
        default_factory=list,
        description="PEM-encoded certificate chain",
    )
    measurements: Optional[Dict[str, str]] = Field(
        None, description="Platform measurements (PCRs, etc.)"
    )


class AttestationResponse(BaseModel):
    """Response from attestation verification."""

    verified: bool
    attestation_type: str
    device_id_hash: str
    timestamp: str
    measurements: Dict[str, str]
    error: Optional[str] = None


# --- Dependency ---


async def get_db_session():
    """Dependency to get database session."""
    async with db.get_session() as session:
        yield session


# --- Endpoints ---


@router.post("/challenge")
async def generate_challenge(
    request: ChallengeRequest,
    current_user: Dict = Depends(get_current_user),
) -> ChallengeResponse:
    """
    Generate an attestation challenge.

    The client must respond with attestation data that includes
    the returned nonce to prevent replay attacks.

    Supported attestation types:
    - apple_secure_enclave: Apple Secure Enclave (iOS/macOS)
    - android_tee: Android TEE (TrustZone)
    - nvidia_cc: NVIDIA Confidential Computing
    - intel_sgx: Intel SGX
    - simulated: For testing only
    """
    # Validate attestation type
    try:
        attestation_type = AttestationType(request.attestation_type)
    except ValueError:
        valid_types = [t.value for t in AttestationType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid attestation_type. Must be one of: {valid_types}",
        )

    challenge = hardware_attestation_service.generate_challenge(
        attestation_type=attestation_type,
        device_id_hint=request.device_id_hint,
    )

    logger.info(
        f"Generated attestation challenge {challenge.challenge_id} "
        f"for user {current_user.get('user_id')}"
    )

    return ChallengeResponse(
        challenge_id=challenge.challenge_id,
        nonce=challenge.nonce,
        attestation_type=challenge.attestation_type.value,
        expires_at=challenge.expires_at.isoformat(),
    )


@router.post("/submit")
async def submit_attestation(
    request: AttestationSubmitRequest,
    current_user: Dict = Depends(get_current_user),
) -> AttestationResponse:
    """
    Submit attestation data for verification.

    The attestation data must be a valid hardware attestation blob
    that includes the challenge nonce.
    """
    # SECURITY: Check base64 size before decoding to prevent memory DoS
    # Max 1MB encoded = ~750KB decoded (attestation blobs are typically small)
    MAX_ATTESTATION_BASE64_SIZE = 1 * 1024 * 1024
    if len(request.attestation_data) > MAX_ATTESTATION_BASE64_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Attestation data too large (max {MAX_ATTESTATION_BASE64_SIZE // 1024}KB)",
        )

    try:
        # Decode base64 attestation data
        attestation_data = base64.b64decode(request.attestation_data, validate=True)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid base64 attestation_data: {e}",
        )

    result = hardware_attestation_service.verify_attestation(
        challenge_id=request.challenge_id,
        attestation_data=attestation_data,
        certificate_chain=request.certificate_chain,
        measurements=request.measurements,
    )

    logger.info(
        f"Attestation verification for user {current_user.get('user_id')}: "
        f"{'VERIFIED' if result.verified else 'FAILED'}"
    )

    return AttestationResponse(
        verified=result.verified,
        attestation_type=result.attestation_type.value,
        device_id_hash=result.device_id_hash,
        timestamp=result.timestamp.isoformat(),
        measurements=result.measurements,
        error=result.error,
    )


@router.get("/{attestation_id}")
async def get_attestation(
    attestation_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get attestation details by ID.

    NOTE: This endpoint is a stub - attestation records would be
    stored in a separate table in production.
    """
    # Stub: Return not found for now
    # In production, this would query an attestation records table
    raise HTTPException(
        status_code=404,
        detail=f"Attestation record {attestation_id} not found",
    )


@router.post("/{attestation_id}/verify")
async def reverify_attestation(
    attestation_id: str,
    current_user: Dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Re-verify an existing attestation record.

    NOTE: This endpoint is a stub - would re-check certificate
    expiration and revocation status in production.
    """
    # Stub: Return not found for now
    raise HTTPException(
        status_code=404,
        detail=f"Attestation record {attestation_id} not found",
    )


@router.get("/types")
async def list_attestation_types():
    """
    List supported attestation types.

    Returns information about each supported platform and its
    verification requirements.
    """
    return {
        "types": [
            {
                "type": "apple_secure_enclave",
                "name": "Apple Secure Enclave",
                "platforms": ["iOS", "macOS"],
                "description": "Uses DeviceCheck or App Attest API",
                "production_ready": False,
            },
            {
                "type": "android_tee",
                "name": "Android TEE",
                "platforms": ["Android"],
                "description": "Uses Play Integrity API or Key Attestation",
                "production_ready": False,
            },
            {
                "type": "nvidia_cc",
                "name": "NVIDIA Confidential Computing",
                "platforms": ["GPU Server"],
                "description": "Uses NVIDIA Attestation SDK for H100/A100",
                "production_ready": False,
            },
            {
                "type": "intel_sgx",
                "name": "Intel SGX",
                "platforms": ["x86 Server"],
                "description": "Uses Intel Attestation Service (IAS) or DCAP",
                "production_ready": False,
            },
            {
                "type": "simulated",
                "name": "Simulated (Testing)",
                "platforms": ["Any"],
                "description": "For testing only - always verifies if nonce is included",
                "production_ready": False,
            },
        ],
    }
