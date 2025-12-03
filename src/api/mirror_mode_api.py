"""
Mirror Mode API Endpoints for UATP Capsule Engine

This module provides API endpoints for Mirror Mode audit/refusal functionality,
allowing explicit triggering of capsule audits and retrieval of audit results.
"""

import logging
from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List, Optional, Union

from .schemas import ErrorResponse
from src.capsule_schema import (
    AuditCapsule,
    RefusalCapsule,
    CapsuleStatus,
    Verification,
)
from pydantic import BaseModel, Field
from quart import Blueprint, Response, jsonify
from quart_schema import validate_request, validate_response

# --- Schema Definitions ---


class AuditRequest(BaseModel):
    """Schema for the /mirror/audit request."""

    capsule_id: str
    force: bool = Field(
        default=False, description="Force audit even if sample rate would skip it"
    )
    strict_mode: Optional[bool] = Field(
        default=None, description="Override default strict mode setting"
    )


class MirrorConfigRequest(BaseModel):
    """Schema for the /mirror/config request."""

    sample_rate: Optional[float] = Field(
        default=None, description="Probability (0-1) that a capsule will be audited"
    )
    strict_mode: Optional[bool] = Field(
        default=None, description="If True, applies stricter policy checks"
    )


class MirrorConfigResponse(BaseModel):
    """Schema for the /mirror/config response."""

    sample_rate: float
    strict_mode: bool
    enabled: bool


class AuditResultResponse(BaseModel):
    """Schema for the result of an audit."""

    capsule_id: str
    audit_capsule_id: Optional[str] = None
    refusal_capsule_id: Optional[str] = None
    status: str
    timestamp: str
    violations: List[Dict[str, Any]]
    audit_score: float


class ListAuditResultsResponse(BaseModel):
    """Schema for the /mirror/audits response."""

    results: List[AuditResultResponse]
    count: int


# Configure logging
logger = logging.getLogger(__name__)


def create_mirror_mode_api_blueprint(engine_getter, require_api_key):
    """Create and return the mirror mode API blueprint with injected dependencies."""
    mirror_bp = Blueprint("mirror_mode_api", __name__, url_prefix="/api/v1/mirror")

    @mirror_bp.route("/config", methods=["GET"])
    @require_api_key(["read"])
    async def get_mirror_config():
        """Get the current configuration of the Mirror Mode agent."""
        engine = engine_getter()
        try:
            if not hasattr(engine, "mirror_agent") or engine.mirror_agent is None:
                return (
                    jsonify(
                        ErrorResponse(
                            error="Mirror Mode is not available on this server."
                        ).model_dump()
                    ),
                    404,
                )

            config = MirrorConfigResponse(
                sample_rate=engine.mirror_agent.sample_rate,
                strict_mode=engine.mirror_agent.strict_mode,
                enabled=engine.mirror_agent.sample_rate > 0,
            )
            return jsonify(config.model_dump()), 200
        except Exception as e:
            logger.error(f"Error retrieving mirror config: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="An unexpected error occurred retrieving Mirror Mode configuration.",
                        details=str(e),
                    ).model_dump()
                ),
                500,
            )

    @mirror_bp.route("/config", methods=["PUT"])
    @require_api_key(["admin"])
    @validate_request(MirrorConfigRequest)
    async def update_mirror_config(data: MirrorConfigRequest):
        """Update the configuration of the Mirror Mode agent."""
        engine = engine_getter()
        try:
            if not hasattr(engine, "mirror_agent") or engine.mirror_agent is None:
                return (
                    jsonify(
                        ErrorResponse(
                            error="Mirror Mode is not available on this server."
                        ).model_dump()
                    ),
                    404,
                )

            if data.sample_rate is not None:
                if not 0 <= data.sample_rate <= 1:
                    return (
                        jsonify(
                            ErrorResponse(
                                error="Sample rate must be between 0 and 1."
                            ).model_dump()
                        ),
                        400,
                    )
                engine.mirror_agent.sample_rate = data.sample_rate

            if data.strict_mode is not None:
                engine.mirror_agent.strict_mode = data.strict_mode

            # Return the updated config
            config = MirrorConfigResponse(
                sample_rate=engine.mirror_agent.sample_rate,
                strict_mode=engine.mirror_agent.strict_mode,
                enabled=engine.mirror_agent.sample_rate > 0,
            )
            return jsonify(config.model_dump()), 200
        except Exception as e:
            logger.error(f"Error updating mirror config: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="An unexpected error occurred updating Mirror Mode configuration.",
                        details=str(e),
                    ).model_dump()
                ),
                500,
            )

    @mirror_bp.route("/audit", methods=["POST"])
    @require_api_key(["write"])
    @validate_request(AuditRequest)
    async def trigger_audit(data: AuditRequest):
        """Explicitly trigger an audit for a specific capsule."""
        engine = engine_getter()
        try:
            if not hasattr(engine, "mirror_agent") or engine.mirror_agent is None:
                return (
                    jsonify(
                        ErrorResponse(
                            error="Mirror Mode is not available on this server."
                        ).model_dump()
                    ),
                    404,
                )

            # Get the capsule to audit
            capsule = await engine.get_capsule_async(data.capsule_id)
            if capsule is None:
                return (
                    jsonify(
                        ErrorResponse(
                            error=f"Capsule with ID {data.capsule_id} not found."
                        ).model_dump()
                    ),
                    404,
                )

            # Override strict mode temporarily if specified
            original_strict_mode = None
            if data.strict_mode is not None:
                original_strict_mode = engine.mirror_agent.strict_mode
                engine.mirror_agent.strict_mode = data.strict_mode

            # Store original sample rate to restore it later
            original_sample_rate = engine.mirror_agent.sample_rate

            try:
                # Force audit by temporarily setting sample rate to 1.0
                if data.force:
                    engine.mirror_agent.sample_rate = 1.0

                # Run the audit synchronously (not in background)
                await engine.mirror_agent._run_audit(capsule)

                # Find the most recent audit or refusal capsule for this capsule
                audit_result = await _find_audit_result(engine, capsule.capsule_id)

                if audit_result:
                    return jsonify(audit_result.model_dump()), 200
                else:
                    return (
                        jsonify(
                            ErrorResponse(
                                error="Audit completed but no result was found."
                            ).model_dump()
                        ),
                        404,
                    )
            finally:
                # Restore original settings
                engine.mirror_agent.sample_rate = original_sample_rate
                if original_strict_mode is not None:
                    engine.mirror_agent.strict_mode = original_strict_mode

        except Exception as e:
            logger.error(f"Error triggering audit: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="An unexpected error occurred during audit.",
                        details=str(e),
                    ).model_dump()
                ),
                500,
            )

    @mirror_bp.route("/audits", methods=["GET"])
    @require_api_key(["read"])
    async def list_audit_results():
        """List all audit and refusal capsules."""
        engine = engine_getter()
        try:
            # Query for both audit and refusal capsules
            audit_capsules = await engine.query_capsules_async(
                {"capsule_type": "audit_capsule"}
            )
            refusal_capsules = await engine.query_capsules_async(
                {"capsule_type": "refusal_capsule"}
            )

            results = []

            # Process audit capsules
            for capsule in audit_capsules:
                audit_data = capsule.audit
                results.append(
                    AuditResultResponse(
                        capsule_id=audit_data.get("audited_capsule_id", "unknown"),
                        audit_capsule_id=capsule.capsule_id,
                        refusal_capsule_id=None,
                        status="PASS",
                        timestamp=capsule.timestamp.isoformat(),
                        violations=[],
                        audit_score=audit_data.get("audit_score", 1.0),
                    )
                )

            # Process refusal capsules
            for capsule in refusal_capsules:
                refusal_data = capsule.refusal
                results.append(
                    AuditResultResponse(
                        capsule_id=refusal_data.get("refused_capsule_id", "unknown"),
                        audit_capsule_id=None,
                        refusal_capsule_id=capsule.capsule_id,
                        status="FAIL",
                        timestamp=capsule.timestamp.isoformat(),
                        violations=refusal_data.get("violations", []),
                        audit_score=refusal_data.get("audit_score", 0.0),
                    )
                )

            # Sort by timestamp descending (newest first)
            results.sort(key=lambda x: x.timestamp, reverse=True)

            response = ListAuditResultsResponse(
                results=results,
                count=len(results),
            )
            return jsonify(response.model_dump()), 200
        except Exception as e:
            logger.error(f"Error listing audit results: {e}", exc_info=True)
            return (
                jsonify(
                    ErrorResponse(
                        error="An unexpected error occurred listing audit results.",
                        details=str(e),
                    ).model_dump()
                ),
                500,
            )

    async def _find_audit_result(
        engine, capsule_id: str
    ) -> Optional[AuditResultResponse]:
        """Find the most recent audit or refusal result for a given capsule ID."""
        # Query for audit capsules related to this capsule
        audit_capsules = await engine.query_capsules_async(
            {
                "capsule_type": "audit_capsule",
                "audit.audited_capsule_id": capsule_id,
            }
        )

        # Query for refusal capsules related to this capsule
        refusal_capsules = await engine.query_capsules_async(
            {
                "capsule_type": "refusal_capsule",
                "refusal.refused_capsule_id": capsule_id,
            }
        )

        # Find the most recent result (audit or refusal)
        most_recent = None
        most_recent_timestamp = None

        for capsule in audit_capsules:
            if (
                most_recent_timestamp is None
                or capsule.timestamp > most_recent_timestamp
            ):
                most_recent = AuditResultResponse(
                    capsule_id=capsule_id,
                    audit_capsule_id=capsule.capsule_id,
                    refusal_capsule_id=None,
                    status="PASS",
                    timestamp=capsule.timestamp.isoformat(),
                    violations=[],
                    audit_score=capsule.audit.get("audit_score", 1.0),
                )
                most_recent_timestamp = capsule.timestamp

        for capsule in refusal_capsules:
            if (
                most_recent_timestamp is None
                or capsule.timestamp > most_recent_timestamp
            ):
                most_recent = AuditResultResponse(
                    capsule_id=capsule_id,
                    audit_capsule_id=None,
                    refusal_capsule_id=capsule.capsule_id,
                    status="FAIL",
                    timestamp=capsule.timestamp.isoformat(),
                    violations=capsule.refusal.get("violations", []),
                    audit_score=capsule.refusal.get("audit_score", 0.0),
                )
                most_recent_timestamp = capsule.timestamp

        return most_recent

    return mirror_bp
