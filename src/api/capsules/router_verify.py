"""
Capsules Router - Verification Operations
==========================================

Endpoints for cryptographic verification of capsules and chains.
"""

import hashlib

from fastapi import APIRouter

from ._shared import (
    Any,
    AsyncSession,
    CapsuleModel,
    Depends,
    Dict,
    HTTPException,
    Query,
    Request,
    get_current_user_optional,
    get_db_session,
    json,
    logger,
    select,
    verification_rate_limiter,
)

router = APIRouter()


@router.get("/{capsule_id}/verify")
async def verify_capsule(
    capsule_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Verify a specific capsule's cryptographic integrity.

    SECURITY: Rate limited to 10 requests/minute per IP to prevent:
    - Brute-force enumeration of capsule IDs
    - DoS via expensive cryptographic verification
    - Automated data scraping

    CRITICAL SECURITY FIX: Performs actual cryptographic verification
    using CryptoSealer.verify_capsule() instead of trusting metadata flags.
    """
    # SECURITY: Apply rate limiting to prevent enumeration attacks
    allowed, retry_after = verification_rate_limiter.is_allowed(request)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many verification requests. Limit: 10 per minute.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )

    # Optional auth (verification is public but we log who verifies)
    current_user = get_current_user_optional(request)
    current_user.get("user_id") if current_user else None

    try:
        # Import CryptoSealer for verification
        try:
            from src.security.crypto_sealer import CryptoSealer

            crypto_sealer = CryptoSealer()
        except ImportError:
            crypto_sealer = None
            logger.warning("CryptoSealer not available for verification")

        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalar_one_or_none()

        if not capsule:
            raise HTTPException(status_code=404, detail="Capsule not found")

        # Verification is public - anyone can verify cryptographic integrity
        # (This is by design: verification proves authenticity without exposing payload)

        # Build full capsule data for verification - MUST match what was signed
        # The Pydantic model_dump() returns these keys:
        # capsule_id, capsule_type, reasoning_trace, status, timestamp, verification, version
        capsule_data = {
            "capsule_id": capsule.capsule_id,
            "capsule_type": capsule.capsule_type,
            "timestamp": capsule.timestamp,
            "status": capsule.status if hasattr(capsule, "status") else "sealed",
            "version": getattr(capsule, "version", "7.1"),
            "verification": capsule.verification
            if hasattr(capsule, "verification") and capsule.verification
            else None,
        }
        # Add reasoning_trace if it exists (stored in payload for reasoning_trace capsules)
        if capsule.capsule_type == "reasoning_trace":
            # Extract reasoning_trace from payload if stored there
            payload = capsule.payload or {}
            if "reasoning_trace" in payload:
                capsule_data["reasoning_trace"] = payload["reasoning_trace"]
            else:
                # Construct from payload structure - handle various formats safely
                trace_data = (
                    payload.get("trace", {})
                    if isinstance(payload.get("trace"), dict)
                    else {}
                )
                content_data = (
                    payload.get("content", {})
                    if isinstance(payload.get("content"), dict)
                    else {}
                )
                metadata = (
                    payload.get("metadata", {})
                    if isinstance(payload.get("metadata"), dict)
                    else {}
                )

                # Try to extract conclusion from nested structure, fall back to simple content string
                conclusion = "Auto-captured"
                if isinstance(content_data, dict) and isinstance(
                    content_data.get("data"), dict
                ):
                    reasoning_steps = content_data.get("data", {}).get(
                        "reasoning_steps", []
                    )
                    if reasoning_steps and isinstance(reasoning_steps[0], dict):
                        conclusion = reasoning_steps[0].get("content", "Auto-captured")
                elif isinstance(payload.get("content"), str):
                    conclusion = payload.get("content", "Auto-captured")

                capsule_data["reasoning_trace"] = {
                    "steps": trace_data.get("reasoning_steps", [])
                    if isinstance(trace_data, dict)
                    else [],
                    "conclusion": conclusion,
                    "confidence_score": metadata.get("significance_score", 0.8)
                    if isinstance(metadata, dict)
                    else 0.8,
                    "alternatives_considered": [],
                }

        logger.debug(f"Verification data: {capsule_data.get('verification')}")

        payload = capsule.payload or {}

        # CRITICAL: Perform actual cryptographic verification
        verification_result = {"method": "none", "verified": False, "error": None}

        if crypto_sealer and crypto_sealer.enabled:
            # Check if capsule has signature (v7.0 stores in root-level verification.signature)
            verification_data = capsule_data.get("verification", {}) or payload.get(
                "verification", {}
            )
            # Ensure verification_data is a dict before checking for key
            has_signature = "signature" in payload or (
                isinstance(verification_data, dict) and "signature" in verification_data
            )

            if has_signature:
                try:
                    # Perform ACTUAL cryptographic verification
                    is_valid = crypto_sealer.verify_capsule(capsule_data)

                    verification_result = {
                        "method": "Ed25519Signature2020",
                        "verified": is_valid,
                        "error": None
                        if is_valid
                        else "Signature verification failed - content may have been tampered",
                    }

                    logger.info(
                        f" Cryptographic verification for {capsule_id}: {'VALID' if is_valid else 'INVALID'}"
                    )

                except Exception as verify_error:
                    verification_result = {
                        "method": "Ed25519Signature2020",
                        "verified": False,
                        "error": f"Verification exception: {str(verify_error)}",
                    }
                    logger.error(
                        f"[ERROR] Verification error for {capsule_id}: {verify_error}"
                    )
            else:
                verification_result = {
                    "method": "none",
                    "verified": False,
                    "error": "No cryptographic signature found in capsule",
                }
        else:
            verification_result = {
                "method": "none",
                "verified": False,
                "error": "CryptoSealer not available or disabled",
            }

        # Extract signature metadata for response (check both root and payload locations)
        signature_info = payload.get("signature", {})
        if not signature_info:
            # Check root-level verification (v7.0 format)
            verification_data = capsule_data.get("verification", {}) or payload.get(
                "verification", {}
            )
            # Ensure verification_data is a dict before calling .get()
            if verification_data and isinstance(verification_data, dict):
                signature_info = {
                    "signature": verification_data.get("signature"),
                    "signer": verification_data.get("signer"),
                    "verify_key": verification_data.get("verify_key"),
                    "hash": verification_data.get("hash"),
                }

        return {
            "capsule_id": capsule_id,
            "verified": verification_result["verified"],
            "verification_method": verification_result["method"],
            "verification_error": verification_result["error"],
            "signature_present": bool(
                signature_info and signature_info.get("signature")
            ),
            "signature_metadata": signature_info if signature_info else None,
            "message": f"Capsule signature {'VERIFIED' if verification_result['verified'] else 'NOT VERIFIED'}",
            "status": capsule.status,
            "timestamp": capsule.timestamp.isoformat() if capsule.timestamp else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verification endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")


@router.get("/{capsule_id}/verify-chain")
async def verify_capsule_chain(
    capsule_id: str,
    request: Request,
    depth: int = Query(10, ge=1, le=100, description="Max chain depth to verify"),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Verify the cryptographic hash chain integrity for a capsule.

    SECURITY: Rate limited to prevent enumeration attacks.

    Walks backward through prev_hash links and verifies each content_hash matches.
    If any capsule's content_hash doesn't match its computed hash, the chain is broken.
    """
    # SECURITY: Apply rate limiting to prevent enumeration attacks
    allowed, retry_after = verification_rate_limiter.is_allowed(request)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": "Too many verification requests. Limit: 10 per minute.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )

    try:
        # Start with the target capsule
        query = select(CapsuleModel).where(CapsuleModel.capsule_id == capsule_id)
        result = await session.execute(query)
        capsule = result.scalars().first()

        if not capsule:
            raise HTTPException(status_code=404, detail="Capsule not found")

        chain_verification = []
        current_capsule = capsule
        verified_count = 0
        broken_at = None

        for i in range(depth):
            # Compute content hash for current capsule
            payload_json = json.dumps(current_capsule.payload, sort_keys=True)
            computed_hash = hashlib.sha256(payload_json.encode()).hexdigest()

            # Check if stored content_hash matches
            stored_hash = current_capsule.content_hash
            hash_valid = stored_hash == computed_hash if stored_hash else None

            chain_verification.append(
                {
                    "capsule_id": current_capsule.capsule_id,
                    "position": i,
                    "content_hash": stored_hash,
                    "computed_hash": computed_hash,
                    "hash_valid": hash_valid,
                    "prev_hash": current_capsule.prev_hash,
                }
            )

            if hash_valid is False and broken_at is None:
                broken_at = current_capsule.capsule_id

            if hash_valid:
                verified_count += 1

            # Move to previous capsule in chain
            if not current_capsule.prev_hash:
                break  # Genesis capsule or end of chain

            # Find capsule with matching content_hash
            prev_query = select(CapsuleModel).where(
                CapsuleModel.content_hash == current_capsule.prev_hash
            )
            prev_result = await session.execute(prev_query)
            prev_capsule = prev_result.scalars().first()

            if not prev_capsule:
                chain_verification[-1]["chain_end_reason"] = "prev_capsule_not_found"
                break

            current_capsule = prev_capsule

        chain_intact = broken_at is None and all(
            c.get("hash_valid") in (True, None) for c in chain_verification
        )

        return {
            "capsule_id": capsule_id,
            "chain_intact": chain_intact,
            "verified_count": verified_count,
            "chain_length": len(chain_verification),
            "broken_at": broken_at,
            "chain": chain_verification,
            "message": "Chain integrity verified"
            if chain_intact
            else f"Chain broken at {broken_at}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chain verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Chain verification error: {str(e)}"
        )
