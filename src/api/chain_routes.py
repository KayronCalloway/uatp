from datetime import timedelta
from typing import Union

from quart import Blueprint, Response, current_app, g
from quart_rate_limiter import rate_limit
from quart_schema import validate_querystring, validate_request, validate_response

from .dependencies import require_api_key
from .schemas import (
    ErrorResponse,
    SealChainRequest,
    SealChainResponse,
    VerifySealQuery,
    VerifySealResponse,
)

chain_bp = Blueprint("chain", __name__, url_prefix="/chain")


@chain_bp.route("/seal", methods=["POST"])
@require_api_key(["write", "admin"])
@rate_limit(5, timedelta(minutes=1))
@validate_request(SealChainRequest)
@validate_response(SealChainResponse, 200)
async def seal_chain(data: SealChainRequest) -> Union[SealChainResponse, Response]:
    """Create a finality signature for the chain."""
    try:
        # This is a placeholder for a real chain sealing implementation
        seal = {
            "chain_id": data.chain_id,
            "signer_id": getattr(g, "agent_id", "Unknown"),
            "note": data.note,
            "signature": "dummy-signature",
        }
        return SealChainResponse(status="success", seal=seal)
    except Exception as e:
        current_app.logger.error(f"Error sealing chain: {e}", exc_info=True)
        return ErrorResponse(error="Failed to seal chain", details=str(e)), 500


@chain_bp.route("/seals", methods=["GET", "OPTIONS"])
@require_api_key(["read"])
@rate_limit(60, timedelta(minutes=1))
async def list_chain_seals():
    """List all chain seals."""
    try:
        # Placeholder for listing seals - in real implementation, this would query a database
        mock_seals = [
            {
                "chain_id": "test-chain-001",
                "signer_id": "test-agent",
                "note": "Initial chain seal",
                "signature": "dummy-signature-001",
                "timestamp": "2024-01-15T10:30:00Z",
                "status": "sealed",
            },
            {
                "chain_id": "test-chain-002",
                "signer_id": "test-agent",
                "note": "Updated chain seal",
                "signature": "dummy-signature-002",
                "timestamp": "2024-01-15T11:45:00Z",
                "status": "sealed",
            },
        ]

        return {"success": True, "seals": mock_seals, "count": len(mock_seals)}
    except Exception as e:
        current_app.logger.error(f"Error listing seals: {e}", exc_info=True)
        return ErrorResponse(error="Failed to list seals", details=str(e)), 500


@chain_bp.route("/verify-seal/<chain_id>", methods=["GET"])
@require_api_key(["read"])
@rate_limit(60, timedelta(minutes=1))
@validate_querystring(VerifySealQuery)
@validate_response(VerifySealResponse, 200)
async def verify_chain_seal(
    chain_id: str, query_args: VerifySealQuery
) -> Union[VerifySealResponse, Response]:
    """Verify a chain seal."""
    try:
        # Placeholder for verification logic
        is_valid = query_args.verify_key == "valid-key"
        result = {
            "is_valid": is_valid,
            "message": "Seal is valid."
            if is_valid
            else "Seal is invalid or could not be verified.",
            "details": {},
        }
        return VerifySealResponse(**result)
    except Exception as e:
        current_app.logger.error(f"Error verifying seal: {e}", exc_info=True)
        return ErrorResponse(error="Failed to verify seal", details=str(e)), 500
