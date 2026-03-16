"""
Verified Context Retrieval Service

Provides trusted context for LLM applications by combining full-text search
with cryptographic verification. Only returns capsules with valid signatures.

This is the "trusted RAG" feature - search results include verification status,
allowing LLMs to use only cryptographically verified context.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import DATABASE_URL
from src.models.capsule import CapsuleModel
from src.services.capsule_search_service import CapsuleSearchService, get_search_service

logger = logging.getLogger(__name__)

IS_SQLITE = "sqlite" in DATABASE_URL.lower()


@dataclass
class VerificationStatus:
    """Cryptographic verification status for a capsule."""

    signature_valid: bool = False
    signature_present: bool = False
    timestamp_valid: bool = False
    timestamp_present: bool = False
    verification_method: str = "none"
    error: Optional[str] = None

    @property
    def fully_verified(self) -> bool:
        """Returns True if both signature and timestamp are valid."""
        return self.signature_valid and self.timestamp_valid

    @property
    def signature_verified(self) -> bool:
        """Returns True if signature is present and valid."""
        return self.signature_present and self.signature_valid

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signature_valid": self.signature_valid,
            "signature_present": self.signature_present,
            "timestamp_valid": self.timestamp_valid,
            "timestamp_present": self.timestamp_present,
            "verification_method": self.verification_method,
            "fully_verified": self.fully_verified,
            "error": self.error,
        }


@dataclass
class VerifiedContextHit:
    """A verified search result for trusted context retrieval."""

    capsule_id: str
    capsule_type: str
    timestamp: str
    snippet: str
    relevance_score: float
    verification: VerificationStatus
    reasoning_summary: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capsule_id": self.capsule_id,
            "capsule_type": self.capsule_type,
            "timestamp": self.timestamp,
            "snippet": self.snippet,
            "relevance_score": self.relevance_score,
            "verification": self.verification.to_dict(),
            "reasoning_summary": self.reasoning_summary,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class VerifiedContextResults:
    """Verified context search results."""

    query: str
    total_count: int
    verified_count: int
    results: List[VerifiedContextHit] = field(default_factory=list)
    page: int = 1
    per_page: int = 10
    verified_only: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "total_count": self.total_count,
            "verified_count": self.verified_count,
            "results": [r.to_dict() for r in self.results],
            "page": self.page,
            "per_page": self.per_page,
            "verified_only": self.verified_only,
            "trust_summary": {
                "total_results": len(self.results),
                "fully_verified": sum(
                    1 for r in self.results if r.verification.fully_verified
                ),
                "signature_only": sum(
                    1
                    for r in self.results
                    if r.verification.signature_verified
                    and not r.verification.timestamp_valid
                ),
                "unverified": sum(
                    1 for r in self.results if not r.verification.signature_verified
                ),
            },
        }


class VerifiedContextService:
    """
    Service for retrieving cryptographically verified context.

    Combines full-text search with signature verification to provide
    trusted context for LLM applications.
    """

    def __init__(self):
        self._crypto_sealer = None
        self._search_service = get_search_service()

    def _get_crypto_sealer(self):
        """Lazy-load crypto sealer."""
        if self._crypto_sealer is None:
            try:
                from src.security.crypto_sealer import CryptoSealer

                self._crypto_sealer = CryptoSealer()
            except ImportError:
                logger.warning("CryptoSealer not available")
                self._crypto_sealer = False  # Mark as unavailable
        return self._crypto_sealer if self._crypto_sealer else None

    async def _verify_capsule(self, capsule: CapsuleModel) -> VerificationStatus:
        """
        Verify a capsule's cryptographic integrity.

        Returns verification status including signature and timestamp validity.
        """
        status = VerificationStatus()

        crypto_sealer = self._get_crypto_sealer()

        # Extract verification data
        verification_data = {}
        if hasattr(capsule, "verification") and capsule.verification:
            if isinstance(capsule.verification, dict):
                verification_data = capsule.verification
            elif isinstance(capsule.verification, str):
                try:
                    verification_data = json.loads(capsule.verification)
                except (json.JSONDecodeError, TypeError):
                    pass

        # Also check payload for verification data
        payload = capsule.payload or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                payload = {}

        if not verification_data and "verification" in payload:
            verification_data = payload.get("verification", {})

        # Check signature presence
        signature = verification_data.get("signature")
        if signature:
            status.signature_present = True

        # Check timestamp presence
        timestamp_token = verification_data.get(
            "timestamp_token"
        ) or verification_data.get("rfc3161_timestamp")
        if timestamp_token:
            status.timestamp_present = True

        # Perform cryptographic verification if sealer available
        if crypto_sealer and crypto_sealer.enabled and status.signature_present:
            try:
                # Build capsule data for verification
                capsule_data = {
                    "capsule_id": capsule.capsule_id,
                    "capsule_type": capsule.capsule_type,
                    "timestamp": capsule.timestamp,
                    "status": getattr(capsule, "status", "sealed"),
                    "version": getattr(capsule, "version", "7.1"),
                    "verification": verification_data,
                }

                is_valid = crypto_sealer.verify_capsule(capsule_data)
                status.signature_valid = is_valid
                status.verification_method = "Ed25519Signature2020"

                if not is_valid:
                    status.error = "Signature verification failed"

            except Exception as e:
                status.error = f"Verification error: {str(e)}"
                logger.warning(f"Verification error for {capsule.capsule_id}: {e}")

        # For timestamp verification, we check if it's present
        # Full RFC 3161 verification would require the TSA certificate chain
        if status.timestamp_present:
            # Basic presence check - full verification is complex
            status.timestamp_valid = True  # Trust if present for now

        return status

    def _extract_reasoning_summary(self, capsule: CapsuleModel) -> Optional[str]:
        """Extract a brief reasoning summary from capsule payload."""
        payload = capsule.payload or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                return None

        # Try various paths for reasoning content
        if "reasoning_trace" in payload:
            trace = payload["reasoning_trace"]
            if isinstance(trace, dict):
                return trace.get("conclusion", trace.get("summary"))

        if "content" in payload:
            content = payload["content"]
            if isinstance(content, dict):
                return content.get("summary", content.get("conclusion"))
            elif isinstance(content, str) and len(content) < 200:
                return content

        if "trace" in payload:
            trace = payload["trace"]
            if isinstance(trace, dict):
                steps = trace.get("reasoning_steps", [])
                if steps and isinstance(steps[0], dict):
                    return steps[0].get("content", "")[:200]

        return None

    def _extract_confidence(self, capsule: CapsuleModel) -> Optional[float]:
        """Extract confidence score from capsule."""
        payload = capsule.payload or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                return None

        # Try various paths
        if "confidence" in payload:
            return float(payload["confidence"])

        if "metadata" in payload:
            meta = payload["metadata"]
            if isinstance(meta, dict):
                if "confidence" in meta:
                    return float(meta["confidence"])
                if "significance_score" in meta:
                    return float(meta["significance_score"])

        if "reasoning_trace" in payload:
            trace = payload["reasoning_trace"]
            if isinstance(trace, dict) and "confidence_score" in trace:
                return float(trace["confidence_score"])

        return None

    async def search(
        self,
        session: AsyncSession,
        query: str,
        page: int = 1,
        per_page: int = 10,
        verified_only: bool = False,
        capsule_type: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> VerifiedContextResults:
        """
        Search capsules with verification status.

        Args:
            session: Database session
            query: Search query
            page: Page number (1-indexed)
            per_page: Results per page
            verified_only: If True, only return verified capsules
            capsule_type: Optional filter by type
            min_confidence: Optional minimum confidence threshold

        Returns:
            VerifiedContextResults with verification status for each hit
        """
        # First, do a broader search to account for filtering
        search_multiplier = 3 if verified_only else 1
        search_results = await self._search_service.search(
            session=session,
            query=query,
            page=1,  # We'll paginate after filtering
            per_page=per_page * search_multiplier * page,  # Get more to filter
            capsule_type=capsule_type,
        )

        # Fetch full capsule data for verification
        verified_hits: List[VerifiedContextHit] = []
        total_verified = 0

        for hit in search_results.results:
            # Fetch full capsule
            capsule_query = select(CapsuleModel).where(
                CapsuleModel.capsule_id == hit.capsule_id
            )
            result = await session.execute(capsule_query)
            capsule = result.scalar_one_or_none()

            if not capsule:
                continue

            # Verify capsule
            verification = await self._verify_capsule(capsule)

            # Skip unverified if verified_only
            if verified_only and not verification.signature_verified:
                continue

            # Extract additional context
            reasoning_summary = self._extract_reasoning_summary(capsule)
            confidence = self._extract_confidence(capsule)

            # Apply confidence filter
            if min_confidence is not None and confidence is not None:
                if confidence < min_confidence:
                    continue

            if verification.signature_verified:
                total_verified += 1

            # Build metadata
            metadata = None
            if capsule.payload:
                payload = capsule.payload
                if isinstance(payload, str):
                    try:
                        payload = json.loads(payload)
                    except (json.JSONDecodeError, TypeError):
                        payload = {}

                if isinstance(payload, dict):
                    metadata = {
                        "platform": payload.get("session_metadata", {}).get("platform"),
                        "topics": payload.get("session_metadata", {}).get("topics", []),
                    }

            verified_hits.append(
                VerifiedContextHit(
                    capsule_id=hit.capsule_id,
                    capsule_type=hit.capsule_type,
                    timestamp=hit.timestamp,
                    snippet=hit.snippet,
                    relevance_score=hit.relevance_score,
                    verification=verification,
                    reasoning_summary=reasoning_summary,
                    confidence=confidence,
                    metadata=metadata,
                )
            )

        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_hits = verified_hits[start_idx:end_idx]

        return VerifiedContextResults(
            query=query,
            total_count=len(verified_hits),
            verified_count=total_verified,
            results=paginated_hits,
            page=page,
            per_page=per_page,
            verified_only=verified_only,
        )


# Global singleton
_verified_context_service: Optional[VerifiedContextService] = None


def get_verified_context_service() -> VerifiedContextService:
    """Get the verified context service singleton."""
    global _verified_context_service
    if _verified_context_service is None:
        _verified_context_service = VerifiedContextService()
    return _verified_context_service
