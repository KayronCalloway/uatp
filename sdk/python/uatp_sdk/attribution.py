"""
UATP Python SDK - Attribution Tracking Module

Provides attribution tracking functionality for AI interactions and content generation.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AttributionResult:
    """Result of attribution tracking for an AI interaction."""

    capsule_id: str
    attribution_id: str
    confidence_score: float
    creator_attribution: Dict[str, Any]
    ai_attribution: Dict[str, Any]
    economic_impact: Dict[str, Any]
    verification_status: str
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "capsule_id": self.capsule_id,
            "attribution_id": self.attribution_id,
            "confidence_score": self.confidence_score,
            "creator_attribution": self.creator_attribution,
            "ai_attribution": self.ai_attribution,
            "economic_impact": self.economic_impact,
            "verification_status": self.verification_status,
            "timestamp": self.timestamp.isoformat(),
        }


class AttributionTracker:
    """Handles attribution tracking for AI interactions."""

    def __init__(self, client):
        self.client = client
        self.attribution_cache = {}
        logger.info(" Attribution Tracker initialized")

    async def track_interaction(
        self,
        prompt: str,
        response: str,
        platform: str,
        model: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AttributionResult:
        """
        Track an AI interaction for attribution.

        Args:
            prompt: The user's input prompt
            response: The AI's response
            platform: AI platform used ("openai", "anthropic", "huggingface")
            model: Specific model ("gpt-4", "claude-3-5-sonnet", etc.)
            user_id: User identifier for attribution
            metadata: Additional metadata

        Returns:
            AttributionResult with detailed attribution information
        """

        # Generate interaction hash for uniqueness
        interaction_data = {
            "prompt": prompt,
            "response": response,
            "platform": platform,
            "model": model,
            "timestamp": datetime.utcnow().isoformat(),
        }

        interaction_hash = hashlib.sha256(
            json.dumps(interaction_data, sort_keys=True).encode()
        ).hexdigest()[:16]

        # Build attribution request
        attribution_request = {
            "interaction_hash": interaction_hash,
            "prompt": prompt,
            "response": response,
            "platform": platform,
            "model": model,
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
            "sdk_version": "1.0.0",
        }

        try:
            # Submit to UATP attribution service
            response = await self.client.http_client.post(
                "/api/v1/attribution/track", json=attribution_request
            )
            response.raise_for_status()

            result_data = response.json()

            # Create attribution result
            attribution_result = AttributionResult(
                capsule_id=result_data.get("capsule_id", f"cap_{interaction_hash}"),
                attribution_id=result_data.get(
                    "attribution_id", f"attr_{interaction_hash}"
                ),
                confidence_score=result_data.get("confidence_score", 0.85),
                creator_attribution=result_data.get(
                    "creator_attribution",
                    {
                        "user_id": user_id,
                        "contribution_type": "human_input",
                        "attribution_percentage": result_data.get(
                            "creator_percentage", 0.3
                        ),
                    },
                ),
                ai_attribution=result_data.get(
                    "ai_attribution",
                    {
                        "platform": platform,
                        "model": model,
                        "attribution_percentage": result_data.get("ai_percentage", 0.7),
                    },
                ),
                economic_impact=result_data.get(
                    "economic_impact",
                    {
                        "estimated_value": result_data.get("estimated_value", 0.0),
                        "creator_reward": result_data.get("creator_reward", 0.0),
                        "commons_contribution": result_data.get(
                            "commons_contribution", 0.0
                        ),
                    },
                ),
                verification_status=result_data.get("verification_status", "verified"),
                timestamp=datetime.now(timezone.utc),
            )

            # Cache the result
            self.attribution_cache[attribution_result.attribution_id] = (
                attribution_result
            )

            logger.info(
                f"[OK] Tracked attribution: {attribution_result.attribution_id}"
            )
            return attribution_result

        except Exception as e:
            logger.error(f"[ERROR] Attribution tracking failed: {e}")

            # Return fallback attribution result
            return AttributionResult(
                capsule_id=f"fallback_cap_{interaction_hash}",
                attribution_id=f"fallback_attr_{interaction_hash}",
                confidence_score=0.5,
                creator_attribution={
                    "user_id": user_id,
                    "contribution_type": "human_input",
                    "attribution_percentage": 0.3,
                },
                ai_attribution={
                    "platform": platform,
                    "model": model,
                    "attribution_percentage": 0.7,
                },
                economic_impact={
                    "estimated_value": 0.0,
                    "creator_reward": 0.0,
                    "commons_contribution": 0.0,
                },
                verification_status="pending",
                timestamp=datetime.now(timezone.utc),
            )

    async def get_attribution(self, attribution_id: str) -> Optional[AttributionResult]:
        """Get attribution result by ID."""

        # Check cache first
        if attribution_id in self.attribution_cache:
            return self.attribution_cache[attribution_id]

        try:
            response = await self.client.http_client.get(
                f"/api/v1/attribution/{attribution_id}"
            )
            response.raise_for_status()

            result_data = response.json()

            attribution_result = AttributionResult(
                capsule_id=result_data["capsule_id"],
                attribution_id=result_data["attribution_id"],
                confidence_score=result_data["confidence_score"],
                creator_attribution=result_data["creator_attribution"],
                ai_attribution=result_data["ai_attribution"],
                economic_impact=result_data["economic_impact"],
                verification_status=result_data["verification_status"],
                timestamp=datetime.fromisoformat(result_data["timestamp"]),
            )

            # Cache the result
            self.attribution_cache[attribution_id] = attribution_result
            return attribution_result

        except Exception as e:
            logger.error(f"[ERROR] Failed to get attribution {attribution_id}: {e}")
            return None

    async def update_attribution(
        self, attribution_id: str, updates: Dict[str, Any]
    ) -> bool:
        """Update an existing attribution with new information."""

        try:
            response = await self.client.http_client.patch(
                f"/api/v1/attribution/{attribution_id}", json=updates
            )
            response.raise_for_status()

            # Clear from cache to force refresh
            if attribution_id in self.attribution_cache:
                del self.attribution_cache[attribution_id]

            logger.info(f"[OK] Updated attribution: {attribution_id}")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Failed to update attribution {attribution_id}: {e}")
            return False

    async def get_user_attributions(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[AttributionResult]:
        """Get all attributions for a specific user."""

        try:
            params = {"user_id": user_id, "limit": limit, "offset": offset}

            response = await self.client.http_client.get(
                "/api/v1/attribution/user", params=params
            )
            response.raise_for_status()

            data = response.json()
            attributions = []

            for item in data.get("attributions", []):
                attribution = AttributionResult(
                    capsule_id=item["capsule_id"],
                    attribution_id=item["attribution_id"],
                    confidence_score=item["confidence_score"],
                    creator_attribution=item["creator_attribution"],
                    ai_attribution=item["ai_attribution"],
                    economic_impact=item["economic_impact"],
                    verification_status=item["verification_status"],
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                )
                attributions.append(attribution)

            logger.info(
                f" Retrieved {len(attributions)} attributions for user {user_id}"
            )
            return attributions

        except Exception as e:
            logger.error(f"[ERROR] Failed to get user attributions for {user_id}: {e}")
            return []

    async def verify_attribution(self, attribution_id: str) -> Dict[str, Any]:
        """Verify the cryptographic integrity of an attribution."""

        try:
            response = await self.client.http_client.post(
                f"/api/v1/attribution/{attribution_id}/verify"
            )
            response.raise_for_status()

            verification_result = response.json()
            logger.info(f" Verified attribution: {attribution_id}")
            return verification_result

        except Exception as e:
            logger.error(
                f"[ERROR] Attribution verification failed for {attribution_id}: {e}"
            )
            return {
                "verified": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def estimate_attribution_value(
        self, prompt: str, response: str, platform: str, model: str
    ) -> Dict[str, Any]:
        """Estimate the economic value of an attribution before tracking."""

        estimation_request = {
            "prompt": prompt,
            "response": response,
            "platform": platform,
            "model": model,
            "estimation_only": True,
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/attribution/estimate", json=estimation_request
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"[ERROR] Attribution value estimation failed: {e}")
            return {
                "estimated_value": 0.0,
                "creator_reward": 0.0,
                "commons_contribution": 0.0,
                "confidence": 0.0,
                "error": str(e),
            }

    def get_cached_attributions(self) -> List[AttributionResult]:
        """Get all cached attribution results."""
        return list(self.attribution_cache.values())

    def clear_cache(self):
        """Clear the attribution cache."""
        self.attribution_cache.clear()
        logger.info(" Attribution cache cleared")
