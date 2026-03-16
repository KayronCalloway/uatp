"""
Chain Sealing FastAPI Router for UATP Capsule Engine.

UATP 7.2: Provides endpoints for chain sealing and verification using
real cryptographic signatures instead of mock data.

Chain seals provide:
- Legal admissibility (timestamped, signed evidence)
- Tamper detection (chain_state_hash comparison)
- Audit trail (who sealed, when, why)
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.chain_sealer import ChainSealer
from src.core.database import db
from src.models.capsule import CapsuleModel
from src.models.chain_seal import ChainSealModel


# Stub for archived capsule_lifecycle_service
class _LifecycleServiceStub:
    """Stub for archived capsule_lifecycle_service."""

    def get_chain_capsules(self, chain_id: str) -> list:
        return []

    def compute_chain_hash(self, chain_id: str) -> str:
        return ""


capsule_lifecycle_service = _LifecycleServiceStub()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chain", tags=["Chain Sealing"])

# Real ChainSealer instance
_chain_sealer = ChainSealer()


# Pydantic models
class SealChainRequest(BaseModel):
    """Request to seal a chain."""

    chain_id: str
    signer_id: Optional[str] = "system"
    note: Optional[str] = None
    capsule_ids: Optional[List[str]] = None  # Optional explicit list of capsule IDs


class ChainSeal(BaseModel):
    """Chain seal data."""

    seal_id: str
    chain_id: str
    signer_id: str
    note: Optional[str]
    signature: str
    verify_key: str
    chain_state_hash: str
    timestamp: str
    capsule_count: int


class SealChainResponse(BaseModel):
    """Response from sealing a chain."""

    status: str
    seal: Dict[str, Any]
    persisted: bool


class VerifySealResponse(BaseModel):
    """Response from verifying a seal."""

    valid: bool
    chain_id: str
    seal_id: Optional[str]
    signature: Optional[str]
    verified_at: str
    chain_unchanged: Optional[bool] = None
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


async def get_db_session():
    """Dependency to get database session."""
    async with db.get_session() as session:
        yield session


@router.get("/seals")
async def list_chain_seals(
    chain_id: Optional[str] = Query(None, description="Filter by chain ID"),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    List all chain seals from the database.

    Args:
        chain_id: Optional filter by chain ID

    Returns:
        List of persisted chain seals
    """
    try:
        query = select(ChainSealModel)
        if chain_id:
            query = query.where(ChainSealModel.chain_id == chain_id)
        query = query.order_by(ChainSealModel.timestamp.desc())

        result = await session.execute(query)
        seals = result.scalars().all()

        seal_list = [seal.to_dict() for seal in seals]

        return {
            "success": True,
            "seals": seal_list,
            "count": len(seal_list),
        }

    except Exception as e:
        logger.error(f"Error listing chain seals: {e}")
        # Fallback to ChainSealer's file-based storage
        seals = _chain_sealer.list_seals(chain_id)
        return {
            "success": True,
            "seals": seals,
            "count": len(seals),
            "source": "file_storage",
        }


@router.post("/seal")
async def seal_chain(
    request: SealChainRequest,
    session: AsyncSession = Depends(get_db_session),
) -> SealChainResponse:
    """
    Create a cryptographic seal for a chain.

    This endpoint:
    1. Gathers capsule data from the chain (tracked or provided)
    2. Creates an Ed25519 cryptographic signature
    3. Persists the seal to the database
    4. Returns the seal data

    Args:
        request: Seal request with chain_id, signer_id, optional note and capsule_ids

    Returns:
        Seal response with cryptographic seal data
    """
    try:
        # Get capsule IDs for the chain
        capsule_ids = request.capsule_ids or []

        # If no capsule_ids provided, try to get from lifecycle service
        if not capsule_ids:
            capsule_ids = capsule_lifecycle_service.get_chain_capsules(request.chain_id)

        # If still empty, try to find capsules in DB by querying chain_id patterns
        if not capsule_ids:
            # Query capsules that might belong to this chain
            # (looking in payload for chain_context.chain_id)
            cap_query = select(CapsuleModel).where(
                CapsuleModel.capsule_id.like(f"{request.chain_id}%")
            )
            result = await session.execute(cap_query)
            capsules = result.scalars().all()
            capsule_ids = [cap.capsule_id for cap in capsules]

        # Build chain_data for sealing
        chain_data = []
        if capsule_ids:
            for cap_id in capsule_ids:
                cap_query = select(CapsuleModel).where(
                    CapsuleModel.capsule_id == cap_id
                )
                result = await session.execute(cap_query)
                capsule = result.scalars().first()
                if capsule:
                    chain_data.append(
                        {
                            "capsule_id": capsule.capsule_id,
                            "capsule_type": capsule.capsule_type,
                            "timestamp": capsule.timestamp.isoformat()
                            if capsule.timestamp
                            else None,
                            "verification": capsule.verification,
                        }
                    )

        # Create seal using real ChainSealer
        seal_data = _chain_sealer.seal_chain(
            chain_id=request.chain_id,
            signer_id=request.signer_id or "system",
            seal_note=request.note or "Chain sealed via API",
            chain_data=chain_data if chain_data else None,
        )

        # Persist seal to database
        persisted = False
        try:
            chain_seal = ChainSealModel(
                seal_id=seal_data["seal_id"],
                chain_id=seal_data["chain_id"],
                timestamp=datetime.fromisoformat(
                    seal_data["timestamp"].replace("Z", "+00:00")
                ),
                signer_id=seal_data["signer_id"],
                chain_state_hash=seal_data["chain_state_hash"],
                signature=seal_data["signature"],
                verify_key=seal_data["verify_key"],
                note=seal_data.get("note"),
                capsule_count=len(chain_data),
                capsule_ids=json.dumps(capsule_ids) if capsule_ids else None,
            )
            session.add(chain_seal)
            await session.commit()
            persisted = True
            logger.info(f"Persisted chain seal {seal_data['seal_id']} to database")
        except Exception as persist_error:
            logger.warning(
                f"Failed to persist seal to database (file storage used): {persist_error}"
            )

        # Add capsule count to response
        seal_data["capsule_count"] = len(chain_data)
        seal_data["status"] = "sealed"

        return SealChainResponse(
            status="success",
            seal=seal_data,
            persisted=persisted,
        )

    except Exception as e:
        logger.error(f"Error sealing chain: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to seal chain: {str(e)}")


@router.get("/verify-seal/{chain_id}")
async def verify_chain_seal(
    chain_id: str,
    seal_id: Optional[str] = Query(None, description="Specific seal ID to verify"),
    verify_key: Optional[str] = Query(None, description="Verification key (optional)"),
    session: AsyncSession = Depends(get_db_session),
) -> VerifySealResponse:
    """
    Verify a chain seal's cryptographic signature.

    This endpoint:
    1. Finds the seal (specific or most recent)
    2. Verifies the Ed25519 signature
    3. Optionally checks if chain state has changed

    Args:
        chain_id: Chain ID to verify
        seal_id: Optional specific seal ID
        verify_key: Optional verification key (uses seal's key if not provided)

    Returns:
        Verification result with validity status
    """
    try:
        # Try to find seal in database first
        query = select(ChainSealModel).where(ChainSealModel.chain_id == chain_id)
        if seal_id:
            query = query.where(ChainSealModel.seal_id == seal_id)
        query = query.order_by(ChainSealModel.timestamp.desc())

        result = await session.execute(query)
        db_seal = result.scalars().first()

        if db_seal:
            # Use verification key from database if not provided
            key_to_use = verify_key or db_seal.verify_key

            # Verify using ChainSealer
            verification_result = _chain_sealer.verify_seal(
                chain_id=chain_id,
                verify_key_hex=key_to_use,
                seal_id=db_seal.seal_id,
            )

            return VerifySealResponse(
                valid=verification_result.get("verified", False),
                chain_id=chain_id,
                seal_id=db_seal.seal_id,
                signature=db_seal.signature,
                verified_at=datetime.now(timezone.utc).isoformat(),
                chain_unchanged=verification_result.get("chain_unchanged"),
                details={
                    "signer_id": db_seal.signer_id,
                    "sealed_at": db_seal.timestamp.isoformat()
                    if db_seal.timestamp
                    else None,
                    "note": db_seal.note,
                    "capsule_count": db_seal.capsule_count,
                    "chain_state_hash": db_seal.chain_state_hash,
                },
                error=verification_result.get("error"),
            )

        # Fallback to file-based verification
        if not verify_key:
            # Get verify key from ChainSealer
            verify_key = _chain_sealer.verify_key_hex

        verification_result = _chain_sealer.verify_seal(
            chain_id=chain_id,
            verify_key_hex=verify_key,
            seal_id=seal_id,
        )

        if not verification_result.get("verified", False):
            return VerifySealResponse(
                valid=False,
                chain_id=chain_id,
                seal_id=seal_id,
                signature=None,
                verified_at=datetime.now(timezone.utc).isoformat(),
                error=verification_result.get("error", "Seal not found"),
            )

        return VerifySealResponse(
            valid=True,
            chain_id=chain_id,
            seal_id=verification_result.get("seal_id"),
            signature=None,  # Don't expose in response
            verified_at=datetime.now(timezone.utc).isoformat(),
            chain_unchanged=verification_result.get("chain_unchanged"),
            details={
                "signer_id": verification_result.get("signer_id"),
                "sealed_at": verification_result.get("timestamp"),
                "note": verification_result.get("note"),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying chain seal: {e}")
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")


@router.get("/status")
async def get_chain_sealer_status() -> Dict[str, Any]:
    """
    Get the status of the chain sealer service.

    Returns:
        Status information including verify key for independent verification
    """
    return _chain_sealer.get_chain_sealer_status()


@router.get("/{chain_id}/capsules")
async def get_chain_capsules(
    chain_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Get capsules tracked in a chain.

    Args:
        chain_id: Chain ID to query

    Returns:
        List of capsule IDs and chain metadata
    """
    # Get from lifecycle service
    capsule_ids = capsule_lifecycle_service.get_chain_capsules(chain_id)

    # Compute current merkle root
    merkle_root = capsule_lifecycle_service.compute_chain_hash(chain_id)

    return {
        "chain_id": chain_id,
        "capsule_ids": capsule_ids,
        "capsule_count": len(capsule_ids),
        "merkle_root": merkle_root,
    }
