"""
UATP Python SDK - Economic Engine Module

Handles economic attribution, reward calculation, and payment distribution.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from decimal import Decimal

logger = logging.getLogger(__name__)


@dataclass
class RewardDistribution:
    """Represents a reward distribution event."""

    distribution_id: str
    user_id: str
    amount: Decimal
    currency: str
    source: str  # "attribution", "commons", "governance", "dividend"
    attribution_id: Optional[str]
    payment_status: str  # "pending", "processing", "completed", "failed"
    payment_method: Optional[str]
    transaction_hash: Optional[str]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "distribution_id": self.distribution_id,
            "user_id": self.user_id,
            "amount": str(self.amount),
            "currency": self.currency,
            "source": self.source,
            "attribution_id": self.attribution_id,
            "payment_status": self.payment_status,
            "payment_method": self.payment_method,
            "transaction_hash": self.transaction_hash,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class EconomicMetrics:
    """Global economic metrics from the UATP network."""

    total_attribution_value: Decimal
    total_rewards_distributed: Decimal
    commons_fund_balance: Decimal
    active_contributors: int
    attribution_volume_24h: int
    average_reward_per_attribution: Decimal
    uba_percentage: float  # Universal Basic Attribution percentage
    timestamp: datetime


class EconomicEngine:
    """Handles economic aspects of the UATP network."""

    def __init__(self, client):
        self.client = client
        self.metrics_cache = {}
        self.metrics_cache_ttl = 300  # 5 minutes
        logger.info("💰 Economic Engine initialized")

    async def get_global_metrics(self) -> EconomicMetrics:
        """Get current global economic metrics from the UATP network."""

        # Check cache
        now = datetime.utcnow()
        if "global_metrics" in self.metrics_cache:
            cached_data, cache_time = self.metrics_cache["global_metrics"]
            if (now - cache_time).total_seconds() < self.metrics_cache_ttl:
                return cached_data

        try:
            response = await self.client.http_client.get("/api/v1/economics/metrics")
            response.raise_for_status()

            data = response.json()
            metrics = EconomicMetrics(
                total_attribution_value=Decimal(
                    data.get("total_attribution_value", "0.0")
                ),
                total_rewards_distributed=Decimal(
                    data.get("total_rewards_distributed", "0.0")
                ),
                commons_fund_balance=Decimal(data.get("commons_fund_balance", "0.0")),
                active_contributors=data.get("active_contributors", 0),
                attribution_volume_24h=data.get("attribution_volume_24h", 0),
                average_reward_per_attribution=Decimal(
                    data.get("average_reward_per_attribution", "0.0")
                ),
                uba_percentage=data.get("uba_percentage", 0.15),
                timestamp=datetime.now(timezone.utc),
            )

            # Cache the result
            self.metrics_cache["global_metrics"] = (metrics, now)

            logger.info("📊 Retrieved global economic metrics")
            return metrics

        except Exception as e:
            logger.error(f"❌ Failed to get global metrics: {e}")

            # Return fallback metrics
            return EconomicMetrics(
                total_attribution_value=Decimal("0.0"),
                total_rewards_distributed=Decimal("0.0"),
                commons_fund_balance=Decimal("0.0"),
                active_contributors=0,
                attribution_volume_24h=0,
                average_reward_per_attribution=Decimal("0.0"),
                uba_percentage=0.15,
                timestamp=datetime.now(timezone.utc),
            )

    async def calculate_attribution_value(
        self,
        content_type: str,
        content_size: int,
        quality_score: Optional[float] = None,
        platform: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate the economic value of content for attribution.

        Args:
            content_type: Type of content ("text", "code", "image", "audio", "video")
            content_size: Size in bytes/tokens
            quality_score: Quality rating (0.0-1.0)
            platform: AI platform used
            model: AI model used

        Returns:
            Value calculation with breakdown
        """

        calculation_request = {
            "content_type": content_type,
            "content_size": content_size,
            "quality_score": quality_score,
            "platform": platform,
            "model": model,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/economics/calculate-value", json=calculation_request
            )
            response.raise_for_status()

            result = response.json()
            logger.info(
                f"💰 Calculated attribution value: ${result.get('total_value', 0.0)}"
            )
            return result

        except Exception as e:
            logger.error(f"❌ Value calculation failed: {e}")

            # Fallback calculation based on simple heuristics
            base_value = self._fallback_value_calculation(
                content_type, content_size, quality_score
            )
            return {
                "total_value": base_value,
                "creator_share": base_value * 0.3,
                "ai_platform_share": base_value * 0.55,
                "commons_share": base_value * 0.15,
                "calculation_method": "fallback_heuristic",
                "confidence": 0.5,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _fallback_value_calculation(
        self, content_type: str, content_size: int, quality_score: Optional[float]
    ) -> float:
        """Fallback value calculation using simple heuristics."""

        # Base rates per content type (in USD)
        base_rates = {
            "text": 0.001,  # $0.001 per 100 chars
            "code": 0.005,  # $0.005 per 100 chars
            "image": 0.01,  # $0.01 per image
            "audio": 0.002,  # $0.002 per second
            "video": 0.005,  # $0.005 per second
        }

        base_rate = base_rates.get(content_type, 0.001)
        size_factor = max(1, content_size / 100)
        quality_factor = quality_score if quality_score else 0.7

        return base_rate * size_factor * quality_factor

    async def get_commons_fund_status(self) -> Dict[str, Any]:
        """Get status of the Universal Basic Attribution commons fund."""

        try:
            response = await self.client.http_client.get(
                "/api/v1/economics/commons-fund"
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"❌ Failed to get commons fund status: {e}")
            return {
                "balance": "0.0",
                "monthly_distribution": "0.0",
                "eligible_recipients": 0,
                "distribution_method": "pro_rata",
                "next_distribution": None,
                "error": str(e),
            }

    async def estimate_monthly_uba(self, user_id: str) -> Dict[str, Any]:
        """Estimate monthly Universal Basic Attribution for a user."""

        try:
            params = {"user_id": user_id}
            response = await self.client.http_client.get(
                "/api/v1/economics/estimate-uba", params=params
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"❌ UBA estimation failed for user {user_id}: {e}")
            return {
                "estimated_monthly_uba": "0.0",
                "eligibility_status": "unknown",
                "contribution_score": 0.0,
                "payment_method": None,
                "error": str(e),
            }

    async def get_platform_economics(self, platform: str) -> Dict[str, Any]:
        """Get economic metrics for a specific AI platform."""

        try:
            params = {"platform": platform}
            response = await self.client.http_client.get(
                "/api/v1/economics/platform-metrics", params=params
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"❌ Failed to get platform economics for {platform}: {e}")
            return {
                "platform": platform,
                "total_attributions": 0,
                "total_value_generated": "0.0",
                "total_rewards_paid": "0.0",
                "attribution_efficiency": 0.0,
                "error": str(e),
            }


class RewardCalculator:
    """Handles reward calculations and payment processing."""

    def __init__(self, client):
        self.client = client
        self.payment_methods = ["usd", "crypto", "credits"]
        logger.info("💳 Reward Calculator initialized")

    async def get_user_rewards(
        self, user_id: str, time_period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get reward summary for a user over a time period.

        Args:
            user_id: User identifier
            time_period: "24h", "7d", "30d", "90d", "all"

        Returns:
            Comprehensive reward information
        """

        try:
            params = {"user_id": user_id, "time_period": time_period}

            response = await self.client.http_client.get(
                "/api/v1/rewards/user-summary", params=params
            )
            response.raise_for_status()

            result = response.json()
            logger.info(
                f"💰 Retrieved rewards for user {user_id}: ${result.get('total_earned', 0.0)}"
            )
            return result

        except Exception as e:
            logger.error(f"❌ Failed to get user rewards for {user_id}: {e}")
            return {
                "user_id": user_id,
                "time_period": time_period,
                "total_earned": "0.0",
                "pending_rewards": "0.0",
                "paid_rewards": "0.0",
                "attribution_count": 0,
                "sources": {},
                "payment_methods": {},
                "error": str(e),
            }

    async def get_reward_history(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[RewardDistribution]:
        """Get detailed reward history for a user."""

        try:
            params = {"user_id": user_id, "limit": limit, "offset": offset}

            response = await self.client.http_client.get(
                "/api/v1/rewards/history", params=params
            )
            response.raise_for_status()

            data = response.json()
            distributions = []

            for item in data.get("distributions", []):
                distribution = RewardDistribution(
                    distribution_id=item["distribution_id"],
                    user_id=item["user_id"],
                    amount=Decimal(item["amount"]),
                    currency=item["currency"],
                    source=item["source"],
                    attribution_id=item.get("attribution_id"),
                    payment_status=item["payment_status"],
                    payment_method=item.get("payment_method"),
                    transaction_hash=item.get("transaction_hash"),
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                )
                distributions.append(distribution)

            logger.info(
                f"📊 Retrieved {len(distributions)} reward distributions for user {user_id}"
            )
            return distributions

        except Exception as e:
            logger.error(f"❌ Failed to get reward history for {user_id}: {e}")
            return []

    async def estimate_value(
        self,
        content_type: str,
        content_size: int,
        quality_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Estimate attribution value before content submission.

        Args:
            content_type: Type of content
            content_size: Size in bytes/tokens
            quality_score: Quality rating (0.0-1.0)

        Returns:
            Value estimation with confidence intervals
        """

        estimation_request = {
            "content_type": content_type,
            "content_size": content_size,
            "quality_score": quality_score,
            "estimation_mode": True,
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/rewards/estimate", json=estimation_request
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"❌ Value estimation failed: {e}")

            # Fallback estimation
            base_value = self._estimate_base_value(
                content_type, content_size, quality_score
            )
            return {
                "estimated_value": base_value,
                "creator_reward": base_value * 0.3,
                "confidence_interval": {
                    "low": base_value * 0.7,
                    "high": base_value * 1.3,
                },
                "factors": {
                    "content_type": content_type,
                    "size_factor": content_size,
                    "quality_factor": quality_score or 0.7,
                },
                "method": "fallback_estimation",
            }

    def _estimate_base_value(
        self, content_type: str, content_size: int, quality_score: Optional[float]
    ) -> float:
        """Basic value estimation algorithm."""

        type_multipliers = {
            "text": 0.001,
            "code": 0.005,
            "image": 0.01,
            "audio": 0.002,
            "video": 0.005,
        }

        base_rate = type_multipliers.get(content_type, 0.001)
        size_factor = max(1, content_size / 1000)
        quality_factor = quality_score if quality_score else 0.7

        return base_rate * size_factor * quality_factor

    async def request_payout(
        self,
        user_id: str,
        amount: Union[str, Decimal],
        payment_method: str,
        currency: str = "USD",
    ) -> Dict[str, Any]:
        """Request payout of accumulated rewards."""

        payout_request = {
            "user_id": user_id,
            "amount": str(amount),
            "payment_method": payment_method,
            "currency": currency,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            response = await self.client.http_client.post(
                "/api/v1/rewards/payout", json=payout_request
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"💸 Payout requested for user {user_id}: ${amount}")
            return result

        except Exception as e:
            logger.error(f"❌ Payout request failed for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "payout_id": None,
                "estimated_processing_time": None,
            }

    async def get_payout_methods(self, user_id: str) -> List[Dict[str, Any]]:
        """Get available payout methods for a user."""

        try:
            params = {"user_id": user_id}
            response = await self.client.http_client.get(
                "/api/v1/rewards/payout-methods", params=params
            )
            response.raise_for_status()

            return response.json().get("methods", [])

        except Exception as e:
            logger.error(f"❌ Failed to get payout methods for user {user_id}: {e}")
            return [
                {
                    "method": "bank_transfer",
                    "currency": "USD",
                    "minimum_amount": "10.00",
                    "fee_percentage": 2.5,
                    "processing_time": "3-5 business days",
                }
            ]
