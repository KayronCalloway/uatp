"""
Timestamp Router - RFC 3161 Timestamping API

Provides trusted timestamps from external Time Stamping Authorities (TSA).
This is the endpoint the SDK calls when request_timestamp=True.

Security: Only receives content hash, never the content itself.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/timestamp", tags=["Timestamping"])


class TimestampRequest(BaseModel):
    """Request for RFC 3161 timestamp."""

    hash: str = Field(..., description="SHA-256 hash of content to timestamp")


class TimestampResponse(BaseModel):
    """Response containing RFC 3161 timestamp."""

    success: bool
    hash: str
    tsa: str | None = None
    timestamp: str | None = None
    rfc3161: Dict[str, Any] | None = None
    error: str | None = None


@router.post("", response_model=TimestampResponse)
async def create_timestamp(request: TimestampRequest) -> TimestampResponse:
    """
    Create an RFC 3161 timestamp for a content hash.

    ZERO-TRUST: Only the hash is received, never the content.
    The timestamp proves the hash existed at this point in time,
    verified by an external Time Stamping Authority.

    Args:
        request: Contains the SHA-256 hash to timestamp

    Returns:
        TimestampResponse with RFC 3161 token from external TSA
    """
    try:
        # Import timestamper
        from src.security.rfc3161_timestamps import RFC3161Timestamper

        timestamper = RFC3161Timestamper()

        # Request timestamp from external TSA
        result = timestamper.timestamp_hash(request.hash)

        if result.success:
            logger.info(
                f"Timestamp created for hash {request.hash[:16]}... via {result.tsa}"
            )
            return TimestampResponse(
                success=True,
                hash=request.hash,
                tsa=result.tsa,
                timestamp=result.timestamp.isoformat() if result.timestamp else None,
                rfc3161={
                    "token": result.token_b64,
                    "tsa": result.tsa,
                    "timestamp": result.timestamp.isoformat()
                    if result.timestamp
                    else None,
                    "hash_algorithm": "sha256",
                },
            )
        else:
            logger.warning(f"Timestamp request failed: {result.error}")
            return TimestampResponse(
                success=False,
                hash=request.hash,
                error=result.error or "Timestamp request failed",
            )

    except ImportError as e:
        logger.error(f"RFC 3161 module not available: {e}")
        return TimestampResponse(
            success=False,
            hash=request.hash,
            error="Timestamping service not available",
        )
    except Exception as e:
        logger.error(f"Timestamp error: {e}")
        return TimestampResponse(
            success=False,
            hash=request.hash,
            error=str(e),
        )


@router.get("/status")
async def timestamp_status() -> Dict[str, Any]:
    """Check timestamping service status."""
    try:
        from src.security.rfc3161_timestamps import RFC3161Timestamper

        timestamper = RFC3161Timestamper()
        return {
            "available": True,
            "tsa_url": timestamper.tsa_url,
            "tsa_name": timestamper.tsa_name,
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }
