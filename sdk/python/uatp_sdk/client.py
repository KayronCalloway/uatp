"""
UATP Python SDK - Main Client

The primary interface for developers to integrate with UATP infrastructure.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from .attribution import AttributionResult, AttributionTracker
from .economics import EconomicEngine, RewardCalculator
from .federation import FederationClient
from .governance import GovernanceClient
from .privacy import PrivacyEngine
from .watermarking import WatermarkEngine

logger = logging.getLogger(__name__)


@dataclass
class UATPConfig:
    """Configuration for UATP client."""

    api_key: str
    base_url: str = "https://api.uatp.global"
    timeout: int = 30
    retry_attempts: int = 3
    enable_privacy: bool = True
    enable_watermarking: bool = True
    enable_governance: bool = True
    federation_node: Optional[str] = None


class UATP:
    """
    The main UATP SDK client for developers.

    Provides a simple, unified interface to UATP's civilization-grade infrastructure
    for AI attribution, economic coordination, and democratic governance.
    """

    def __init__(self, api_key: str = None, config: UATPConfig = None, **kwargs):
        """
        Initialize UATP client.

        Args:
            api_key: Your UATP API key
            config: Complete configuration object
            **kwargs: Configuration options (base_url, timeout, etc.)
        """

        if config:
            self.config = config
        else:
            self.config = UATPConfig(
                api_key=api_key or kwargs.get("api_key"),
                base_url=kwargs.get("base_url", "https://api.uatp.global"),
                timeout=kwargs.get("timeout", 30),
                retry_attempts=kwargs.get("retry_attempts", 3),
                enable_privacy=kwargs.get("enable_privacy", True),
                enable_watermarking=kwargs.get("enable_watermarking", True),
                enable_governance=kwargs.get("enable_governance", True),
                federation_node=kwargs.get("federation_node"),
            )

        if not self.config.api_key:
            raise ValueError(
                "UATP API key is required. Get one at https://uatp.global/developers"
            )

        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "User-Agent": "UATP-Python-SDK/1.0.0",
                "Content-Type": "application/json",
            },
        )

        # Initialize specialized engines
        self.attribution = AttributionTracker(self)
        self.economics = EconomicEngine(self)
        self.rewards = RewardCalculator(self)

        if self.config.enable_governance:
            self.governance = GovernanceClient(self)

        if self.config.enable_privacy:
            self.privacy = PrivacyEngine(self)

        if self.config.enable_watermarking:
            self.watermarking = WatermarkEngine(self)

        if self.config.federation_node:
            self.federation = FederationClient(self, self.config.federation_node)

        logger.info(f" UATP SDK initialized with endpoint: {self.config.base_url}")

    async def track_ai_interaction(
        self,
        prompt: str,
        response: str,
        platform: str,
        model: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AttributionResult:
        """
        Track an AI interaction for attribution and economic rewards.

        Args:
            prompt: The user's prompt/question
            response: The AI's response
            platform: AI platform used ("openai", "anthropic", "huggingface", etc.)
            model: Specific model used ("gpt-4", "claude-3-5-sonnet", etc.)
            user_id: User identifier for attribution
            metadata: Additional metadata

        Returns:
            AttributionResult with capsule ID, rewards, and verification
        """

        return await self.attribution.track_interaction(
            prompt=prompt,
            response=response,
            platform=platform,
            model=model,
            user_id=user_id,
            metadata=metadata or {},
        )

    async def get_attribution_rewards(
        self, user_id: str, time_period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get attribution rewards for a user.

        Args:
            user_id: User identifier
            time_period: Time period ("24h", "7d", "30d", "all")

        Returns:
            Dictionary with reward amounts, sources, and payment status
        """

        return await self.rewards.get_user_rewards(user_id, time_period)

    async def create_capsule(
        self,
        capsule_type: str,
        content: Dict[str, Any],
        with_privacy: bool = None,
        with_watermark: bool = None,
    ) -> Dict[str, Any]:
        """
        Create a UATP capsule with optional privacy and watermarking.

        Args:
            capsule_type: Type of capsule ("reasoning", "economic", "governance")
            content: Capsule content
            with_privacy: Enable zero-knowledge privacy proofs
            with_watermark: Enable watermarking

        Returns:
            Created capsule with verification data
        """

        # Apply default privacy/watermarking settings
        enable_privacy = (
            with_privacy if with_privacy is not None else self.config.enable_privacy
        )
        enable_watermark = (
            with_watermark
            if with_watermark is not None
            else self.config.enable_watermarking
        )

        # Create base capsule
        capsule_data = {
            "capsule_type": capsule_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "sdk_version": "1.0.0",
        }

        # Add privacy proof if enabled
        if enable_privacy and self.privacy:
            privacy_proof = await self.privacy.create_proof(capsule_data)
            capsule_data["privacy_proof"] = privacy_proof

        # Add watermark if enabled
        if enable_watermark and self.watermarking:
            watermark_result = await self.watermarking.apply_watermark(content)
            capsule_data["watermark"] = watermark_result

        # Submit to UATP network
        response = await self.http_client.post("/api/v1/capsules", json=capsule_data)
        response.raise_for_status()

        result = response.json()
        logger.info(f"[OK] Created capsule: {result.get('capsule_id')}")

        return result

    async def verify_capsule(self, capsule_id: str) -> Dict[str, Any]:
        """
        Verify a capsule's cryptographic integrity and authenticity.

        Args:
            capsule_id: ID of capsule to verify

        Returns:
            Verification result with validity, signatures, and trust metrics
        """

        response = await self.http_client.get(f"/api/v1/capsules/{capsule_id}/verify")
        response.raise_for_status()

        return response.json()

    async def participate_in_governance(
        self,
        action: str,
        proposal_id: Optional[str] = None,
        vote: Optional[str] = None,
        proposal_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Participate in UATP democratic governance.

        Args:
            action: "vote", "propose", "delegate"
            proposal_id: ID of proposal (for voting)
            vote: "approve", "reject", "abstain"
            proposal_data: Data for new proposals

        Returns:
            Governance action result
        """

        if not self.config.enable_governance:
            raise ValueError("Governance is disabled in configuration")

        if action == "vote":
            return await self.governance.cast_vote(proposal_id, vote)
        elif action == "propose":
            return await self.governance.create_proposal(proposal_data)
        else:
            raise ValueError(f"Unknown governance action: {action}")

    async def get_network_status(self) -> Dict[str, Any]:
        """
        Get status of the global UATP network.

        Returns:
            Network health, node count, transaction volume, governance activity
        """

        response = await self.http_client.get("/api/v1/network/status")
        response.raise_for_status()

        return response.json()

    async def get_economic_metrics(self) -> Dict[str, Any]:
        """
        Get global economic metrics from the UATP network.

        Returns:
            Attribution volume, reward distributions, commons fund status
        """

        return await self.economics.get_global_metrics()

    async def estimate_attribution_value(
        self,
        content_type: str,
        content_size: int,
        quality_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Estimate the attribution value of content before submission.

        Args:
            content_type: "text", "code", "image", "audio", "video"
            content_size: Size in bytes/tokens
            quality_score: Quality rating (0.0-1.0)

        Returns:
            Estimated reward amounts and confidence intervals
        """

        return await self.rewards.estimate_value(
            content_type, content_size, quality_score
        )

    # Context manager support
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the UATP client and cleanup resources."""
        await self.http_client.aclose()
        logger.info(" UATP SDK client closed")


# Synchronous wrapper for easier use
class UATPSync:
    """Synchronous wrapper for UATP client."""

    def __init__(self, *args, **kwargs):
        self._async_client = UATP(*args, **kwargs)
        self._loop = None

    def _get_loop(self):
        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def track_ai_interaction(self, *args, **kwargs):
        """Synchronous version of track_ai_interaction."""
        return self._get_loop().run_until_complete(
            self._async_client.track_ai_interaction(*args, **kwargs)
        )

    def get_attribution_rewards(self, *args, **kwargs):
        """Synchronous version of get_attribution_rewards."""
        return self._get_loop().run_until_complete(
            self._async_client.get_attribution_rewards(*args, **kwargs)
        )

    def create_capsule(self, *args, **kwargs):
        """Synchronous version of create_capsule."""
        return self._get_loop().run_until_complete(
            self._async_client.create_capsule(*args, **kwargs)
        )

    def verify_capsule(self, *args, **kwargs):
        """Synchronous version of verify_capsule."""
        return self._get_loop().run_until_complete(
            self._async_client.verify_capsule(*args, **kwargs)
        )

    def get_network_status(self):
        """Synchronous version of get_network_status."""
        return self._get_loop().run_until_complete(
            self._async_client.get_network_status()
        )

    def close(self):
        """Close the synchronous client."""
        if self._loop:
            self._loop.run_until_complete(self._async_client.close())
