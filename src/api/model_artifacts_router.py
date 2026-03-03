"""
Model Artifacts API Router - UATP 7.2 Model Registry Protocol

Provides REST API endpoints for:
- Registering model artifacts
- Content-addressed retrieval
- License management
- Compliance verification
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..auth.auth_middleware import get_current_user, get_current_user_optional
from ..core.database import db
from ..services.content_addressed_storage import (
    content_addressed_storage,
)
from ..services.license_verifier import (
    UsageType,
    license_verifier,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["Model Artifacts"])


# --- Request/Response Models ---


class ArtifactRegisterRequest(BaseModel):
    """Request to register a model artifact."""

    artifact_type: str = Field(
        description="Type: weights, config, tokenizer, adapter, checkpoint"
    )
    content_hash: str = Field(description="SHA-256 hash of artifact content")
    size_bytes: int = Field(description="Size in bytes")
    storage_uri: str = Field(description="URI to artifact storage location")
    storage_backend: str = Field(default="local", description="Storage backend")
    format: Optional[str] = Field(None, description="File format")
    compression: Optional[str] = Field(None, description="Compression type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ArtifactResponse(BaseModel):
    """Response for artifact operations."""

    artifact_id: str
    model_id: str
    artifact_type: str
    content_hash: str
    size_bytes: int
    storage_uri: str
    format: Optional[str]
    upload_status: str
    created_at: str


class LicenseAttachRequest(BaseModel):
    """Request to attach a license to a model."""

    license_type: str = Field(description="License type: MIT, Apache-2.0, etc.")
    license_name: Optional[str] = Field(None, description="Human-readable name")
    license_url: Optional[str] = Field(None, description="URL to license text")
    license_text: Optional[str] = Field(None, description="Full license text")
    permissions: List[str] = Field(
        default_factory=list,
        description="Allowed uses: commercial_use, derivative_works, etc.",
    )
    restrictions: List[str] = Field(
        default_factory=list,
        description="Restrictions: no_commercial, attribution_required, etc.",
    )
    conditions: Optional[List[str]] = Field(
        None, description="Conditions: include_license, state_changes, etc."
    )
    attribution_requirements: Optional[Dict[str, Any]] = Field(
        None, description="Required attribution format"
    )
    effective_date: Optional[str] = Field(
        None, description="When license becomes effective (ISO 8601)"
    )
    expiration_date: Optional[str] = Field(
        None, description="When license expires (ISO 8601)"
    )


class LicenseResponse(BaseModel):
    """Response for license operations."""

    license_id: str
    model_id: str
    license_type: str
    license_name: Optional[str]
    license_url: Optional[str]
    permissions: List[str]
    restrictions: List[str]
    is_active: bool
    effective_date: str
    expiration_date: Optional[str]


class ComplianceCheckRequest(BaseModel):
    """Request to verify license compliance."""

    usage_type: str = Field(
        description="Usage: commercial, derivative_work, distribution, etc."
    )


class ComplianceCheckResponse(BaseModel):
    """Response from compliance verification."""

    status: str
    compliant: bool
    usage_type: str
    license_type: str
    violations: List[str]
    warnings: List[str]
    required_actions: List[str]
    attribution: Optional[Dict[str, Any]]


class CompatibilityCheckRequest(BaseModel):
    """Request to check license compatibility."""

    source_model_ids: List[str] = Field(description="Source model IDs")
    target_license: str = Field(description="Intended license for derivative")


class CompatibilityCheckResponse(BaseModel):
    """Response from compatibility check."""

    compatible: bool
    source_licenses: List[str]
    target_license: str
    issues: List[str]
    recommendations: List[str]


# --- Dependency ---


async def get_db_session():
    """Dependency to get database session."""
    async with db.get_session() as session:
        yield session


# --- Artifact Endpoints ---


@router.post("/{model_id}/artifacts")
async def register_artifact(
    model_id: str,
    request: ArtifactRegisterRequest,
    current_user: Dict = Depends(get_current_user),
) -> ArtifactResponse:
    """
    Register a model artifact.

    The artifact content should already be uploaded to storage.
    This endpoint registers the artifact metadata and content hash.
    """
    import hashlib
    import time
    from datetime import datetime, timezone

    # Generate artifact ID
    # SECURITY: Use 32 hex chars (128 bits) to prevent collision attacks
    artifact_id = f"art_{hashlib.sha256(f'{model_id}_{request.content_hash}_{time.time()}'.encode()).hexdigest()[:32]}"

    # In production, would verify:
    # 1. Model exists
    # 2. Content hash matches uploaded content
    # 3. User has permission

    logger.info(
        f"Registered artifact {artifact_id} for model {model_id}: "
        f"{request.artifact_type}, {request.size_bytes} bytes"
    )

    return ArtifactResponse(
        artifact_id=artifact_id,
        model_id=model_id,
        artifact_type=request.artifact_type,
        content_hash=request.content_hash,
        size_bytes=request.size_bytes,
        storage_uri=request.storage_uri,
        format=request.format,
        upload_status="completed",
        created_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/{model_id}/artifacts")
async def list_artifacts(
    model_id: str,
    artifact_type: Optional[str] = Query(None, description="Filter by type"),
    current_user: Dict = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    List artifacts for a model.
    """
    # Stub: Would query database
    return {
        "model_id": model_id,
        "artifacts": [],
        "total": 0,
    }


@router.get("/artifacts/{content_hash}")
async def get_artifact_by_hash(
    content_hash: str,
    current_user: Dict = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    Get artifact by content hash (content-addressed lookup).
    """
    # Check if content exists in storage
    exists = await content_addressed_storage.exists(content_hash)

    if not exists:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact with hash {content_hash} not found",
        )

    # Get metadata
    metadata = await content_addressed_storage.get_metadata(content_hash)

    return {
        "content_hash": content_hash,
        "exists": True,
        "metadata": metadata,
    }


@router.post("/artifacts/{content_hash}/verify")
async def verify_artifact_integrity(
    content_hash: str,
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Verify artifact content integrity.
    """
    from datetime import datetime, timezone

    verified = await content_addressed_storage.verify(content_hash)

    return {
        "content_hash": content_hash,
        "verified": verified,
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }


# --- License Endpoints ---


@router.post("/{model_id}/license")
async def attach_license(
    model_id: str,
    request: LicenseAttachRequest,
    current_user: Dict = Depends(get_current_user),
) -> LicenseResponse:
    """
    Attach a license to a model.
    """
    import hashlib
    import time
    from datetime import datetime, timezone

    # Generate license ID
    # SECURITY: Use 32 hex chars (128 bits) to prevent collision attacks
    license_id = f"lic_{hashlib.sha256(f'{model_id}_{request.license_type}_{time.time()}'.encode()).hexdigest()[:32]}"

    # Parse dates
    effective = datetime.now(timezone.utc)
    if request.effective_date:
        effective = datetime.fromisoformat(
            request.effective_date.replace("Z", "+00:00")
        )

    expiration = None
    if request.expiration_date:
        expiration = datetime.fromisoformat(
            request.expiration_date.replace("Z", "+00:00")
        )

    logger.info(
        f"Attached license {license_id} to model {model_id}: {request.license_type}"
    )

    return LicenseResponse(
        license_id=license_id,
        model_id=model_id,
        license_type=request.license_type,
        license_name=request.license_name,
        license_url=request.license_url,
        permissions=request.permissions,
        restrictions=request.restrictions,
        is_active=True,
        effective_date=effective.isoformat(),
        expiration_date=expiration.isoformat() if expiration else None,
    )


@router.get("/{model_id}/license")
async def get_model_license(
    model_id: str,
    current_user: Dict = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    Get active license for a model.
    """
    # Stub: Would query database
    return {
        "model_id": model_id,
        "license": None,
        "message": "No active license found",
    }


@router.post("/{model_id}/verify-license")
async def verify_license_compliance(
    model_id: str,
    request: ComplianceCheckRequest,
    current_user: Dict = Depends(get_current_user),
) -> ComplianceCheckResponse:
    """
    Verify license compliance for a specific usage type.
    """
    try:
        usage = UsageType(request.usage_type)
    except ValueError:
        valid_types = [t.value for t in UsageType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid usage_type. Must be one of: {valid_types}",
        )

    # In production, would fetch actual license from database
    # For now, use MIT as example
    result = license_verifier.verify_compliance(
        license_type="MIT",
        usage_type=usage,
    )

    return ComplianceCheckResponse(
        status=result.status.value,
        compliant=result.compliant,
        usage_type=result.usage_type.value,
        license_type=result.license_type,
        violations=result.violations,
        warnings=result.warnings,
        required_actions=result.required_actions,
        attribution=result.attribution,
    )


@router.post("/check-compatibility")
async def check_license_compatibility(
    request: CompatibilityCheckRequest,
    current_user: Dict = Depends(get_current_user),
) -> CompatibilityCheckResponse:
    """
    Check if source model licenses are compatible with target license.

    Use this before creating derivative models to ensure license compliance.
    """
    # In production, would fetch licenses for source models
    # For now, assume MIT for all sources
    source_licenses = ["MIT"] * len(request.source_model_ids)

    result = license_verifier.check_compatibility(
        source_licenses=source_licenses,
        target_license=request.target_license,
    )

    return CompatibilityCheckResponse(
        compatible=result.compatible,
        source_licenses=result.source_licenses,
        target_license=result.target_license,
        issues=result.issues,
        recommendations=result.recommendations,
    )


@router.get("/licenses/supported")
async def list_supported_licenses() -> Dict[str, Any]:
    """
    List all supported license types with their definitions.
    """
    licenses = []
    for license_type in license_verifier.list_supported_licenses():
        info = license_verifier.get_license_info(license_type)
        licenses.append(
            {
                "type": license_type,
                "permissions": info.get("permissions", []),
                "restrictions": info.get("restrictions", []),
                "conditions": info.get("conditions", []),
                "copyleft": info.get("copyleft", False),
            }
        )

    return {
        "licenses": licenses,
        "total": len(licenses),
    }


@router.post("/{model_id}/generate-attribution")
async def generate_attribution_notice(
    model_id: str,
    copyright_holder: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Generate attribution notice for a model.
    """
    # In production, would fetch model and license from database
    notice = license_verifier.generate_attribution_notice(
        model_name=model_id,
        license_type="MIT",
        copyright_holder=copyright_holder,
        license_url="https://opensource.org/licenses/MIT",
    )

    return {
        "model_id": model_id,
        "attribution_notice": notice,
    }
