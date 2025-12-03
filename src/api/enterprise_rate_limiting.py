"""
Enterprise API Rate Limiting and Quota Management
=================================================

Tiered rate limiting system with organization-based quotas, usage analytics,
overage billing, and SLA monitoring for enterprise clients.
"""

import json
import logging
import time
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import hashlib
import redis.asyncio as redis
from collections import defaultdict, deque

from pydantic import BaseModel, Field
from fastapi import Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class OrganizationTier(Enum):
    """Organization subscription tiers."""

    STARTUP = "startup"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    PREMIUM = "premium"
    CUSTOM = "custom"


class RateLimitType(Enum):
    """Types of rate limiting."""

    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_DAY = "requests_per_day"
    REQUESTS_PER_MONTH = "requests_per_month"
    BANDWIDTH_PER_MINUTE = "bandwidth_per_minute"
    BANDWIDTH_PER_HOUR = "bandwidth_per_hour"
    CONCURRENT_REQUESTS = "concurrent_requests"
    QUOTA_MONTHLY = "quota_monthly"
    QUOTA_YEARLY = "quota_yearly"


class QuotaType(Enum):
    """Types of usage quotas."""

    API_CALLS = "api_calls"
    DATA_TRANSFER = "data_transfer"
    STORAGE = "storage"
    USERS = "users"
    CAPSULES = "capsules"
    REPORTS = "reports"
    INTEGRATIONS = "integrations"


class UsageMetricType(Enum):
    """Usage metric types for billing."""

    API_REQUEST = "api_request"
    DATA_INGRESS = "data_ingress"
    DATA_EGRESS = "data_egress"
    STORAGE_GB_HOUR = "storage_gb_hour"
    COMPUTE_HOUR = "compute_hour"
    USER_SEAT = "user_seat"


@dataclass
class RateLimit:
    """Rate limit configuration."""

    limit_type: RateLimitType
    limit_value: int
    window_seconds: int
    burst_limit: Optional[int] = None
    enabled: bool = True


@dataclass
class UsageQuota:
    """Usage quota configuration."""

    quota_type: QuotaType
    quota_value: int
    period_days: int
    overage_allowed: bool = True
    overage_rate: float = 0.0  # Cost per unit over quota
    soft_limit_percent: float = 80.0  # Warning threshold


@dataclass
class OrganizationPlan:
    """Organization subscription plan."""

    plan_id: str
    organization_id: str
    tier: OrganizationTier
    plan_name: str
    rate_limits: List[RateLimit]
    quotas: List[UsageQuota]
    features: List[str]
    price_per_month: float
    billing_cycle: str = "monthly"
    auto_scale: bool = False
    priority_support: bool = False
    dedicated_resources: bool = False
    custom_sla: Optional[Dict[str, Any]] = None
    effective_date: datetime = field(default_factory=datetime.utcnow)
    expiry_date: Optional[datetime] = None


class UsageRecord(BaseModel):
    """Usage tracking record."""

    record_id: str = Field(default_factory=lambda: str(time.time_ns()))
    organization_id: str
    user_id: Optional[str] = None
    metric_type: UsageMetricType
    endpoint: str
    method: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    quantity: float = 1.0
    request_size: int = 0
    response_size: int = 0
    processing_time_ms: int = 0
    status_code: int = 200
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RateLimitStatus(BaseModel):
    """Current rate limit status."""

    organization_id: str
    limit_type: RateLimitType
    current_usage: int
    limit_value: int
    window_start: datetime
    window_end: datetime
    remaining: int
    reset_timestamp: int
    blocked_requests: int = 0


class QuotaStatus(BaseModel):
    """Current quota status."""

    organization_id: str
    quota_type: QuotaType
    current_usage: float
    quota_value: float
    period_start: datetime
    period_end: datetime
    usage_percent: float
    overage_amount: float = 0.0
    estimated_cost: float = 0.0
    projected_usage: Optional[float] = None


class BillingEvent(BaseModel):
    """Billing event for usage tracking."""

    event_id: str = Field(default_factory=lambda: str(time.time_ns()))
    organization_id: str
    metric_type: UsageMetricType
    quantity: float
    unit_cost: float
    total_cost: float
    billing_period: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EnterpriseRateLimiter:
    """Enterprise-grade rate limiting system."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client

        # In-memory storage for development/testing
        self.rate_limit_cache = defaultdict(lambda: defaultdict(deque))
        self.usage_cache = defaultdict(lambda: defaultdict(float))
        self.blocked_requests = defaultdict(int)

        # Organization plans
        self.organization_plans: Dict[str, OrganizationPlan] = {}

        # Usage tracking
        self.usage_records: List[UsageRecord] = []
        self.billing_events: List[BillingEvent] = []

        # Rate limiting windows
        self.rate_windows: Dict[str, Dict[str, Any]] = {}

        # Initialize default plans
        self._initialize_default_plans()

    def _initialize_default_plans(self):
        """Initialize default organization plans."""

        # Startup Plan
        startup_plan = OrganizationPlan(
            plan_id="startup_001",
            organization_id="startup_default",
            tier=OrganizationTier.STARTUP,
            plan_name="Startup Plan",
            rate_limits=[
                RateLimit(RateLimitType.REQUESTS_PER_MINUTE, 100, 60),
                RateLimit(RateLimitType.REQUESTS_PER_HOUR, 1000, 3600),
                RateLimit(RateLimitType.CONCURRENT_REQUESTS, 10, 0),
            ],
            quotas=[
                UsageQuota(
                    QuotaType.API_CALLS,
                    10000,
                    30,
                    overage_allowed=True,
                    overage_rate=0.001,
                ),
                UsageQuota(
                    QuotaType.DATA_TRANSFER,
                    1000000000,
                    30,
                    overage_allowed=True,
                    overage_rate=0.0001,
                ),  # 1GB
                UsageQuota(
                    QuotaType.USERS, 5, 30, overage_allowed=True, overage_rate=10.0
                ),
            ],
            features=["basic_support", "standard_sla", "basic_analytics"],
            price_per_month=99.0,
        )

        # Professional Plan
        professional_plan = OrganizationPlan(
            plan_id="professional_001",
            organization_id="professional_default",
            tier=OrganizationTier.PROFESSIONAL,
            plan_name="Professional Plan",
            rate_limits=[
                RateLimit(RateLimitType.REQUESTS_PER_MINUTE, 500, 60),
                RateLimit(RateLimitType.REQUESTS_PER_HOUR, 10000, 3600),
                RateLimit(RateLimitType.CONCURRENT_REQUESTS, 50, 0),
            ],
            quotas=[
                UsageQuota(
                    QuotaType.API_CALLS,
                    100000,
                    30,
                    overage_allowed=True,
                    overage_rate=0.0008,
                ),
                UsageQuota(
                    QuotaType.DATA_TRANSFER,
                    10000000000,
                    30,
                    overage_allowed=True,
                    overage_rate=0.00008,
                ),  # 10GB
                UsageQuota(
                    QuotaType.USERS, 25, 30, overage_allowed=True, overage_rate=8.0
                ),
            ],
            features=[
                "business_support",
                "enhanced_sla",
                "advanced_analytics",
                "custom_integrations",
            ],
            price_per_month=299.0,
        )

        # Enterprise Plan
        enterprise_plan = OrganizationPlan(
            plan_id="enterprise_001",
            organization_id="enterprise_default",
            tier=OrganizationTier.ENTERPRISE,
            plan_name="Enterprise Plan",
            rate_limits=[
                RateLimit(RateLimitType.REQUESTS_PER_MINUTE, 2000, 60),
                RateLimit(RateLimitType.REQUESTS_PER_HOUR, 50000, 3600),
                RateLimit(RateLimitType.CONCURRENT_REQUESTS, 200, 0),
            ],
            quotas=[
                UsageQuota(
                    QuotaType.API_CALLS,
                    1000000,
                    30,
                    overage_allowed=True,
                    overage_rate=0.0005,
                ),
                UsageQuota(
                    QuotaType.DATA_TRANSFER,
                    100000000000,
                    30,
                    overage_allowed=True,
                    overage_rate=0.00005,
                ),  # 100GB
                UsageQuota(
                    QuotaType.USERS, 100, 30, overage_allowed=True, overage_rate=5.0
                ),
            ],
            features=[
                "premium_support",
                "enterprise_sla",
                "comprehensive_analytics",
                "custom_integrations",
                "dedicated_success_manager",
                "priority_processing",
            ],
            price_per_month=999.0,
            priority_support=True,
        )

        # Premium Plan
        premium_plan = OrganizationPlan(
            plan_id="premium_001",
            organization_id="premium_default",
            tier=OrganizationTier.PREMIUM,
            plan_name="Premium Enterprise Plan",
            rate_limits=[
                RateLimit(RateLimitType.REQUESTS_PER_MINUTE, 5000, 60),
                RateLimit(RateLimitType.REQUESTS_PER_HOUR, 200000, 3600),
                RateLimit(RateLimitType.CONCURRENT_REQUESTS, 500, 0),
            ],
            quotas=[
                UsageQuota(
                    QuotaType.API_CALLS,
                    10000000,
                    30,
                    overage_allowed=True,
                    overage_rate=0.0003,
                ),
                UsageQuota(
                    QuotaType.DATA_TRANSFER,
                    1000000000000,
                    30,
                    overage_allowed=True,
                    overage_rate=0.00003,
                ),  # 1TB
                UsageQuota(
                    QuotaType.USERS, 500, 30, overage_allowed=True, overage_rate=3.0
                ),
            ],
            features=[
                "white_glove_support",
                "custom_sla",
                "real_time_analytics",
                "unlimited_integrations",
                "dedicated_infrastructure",
                "99.99_uptime",
            ],
            price_per_month=2999.0,
            priority_support=True,
            dedicated_resources=True,
            auto_scale=True,
        )

        self.organization_plans.update(
            {
                "startup_default": startup_plan,
                "professional_default": professional_plan,
                "enterprise_default": enterprise_plan,
                "premium_default": premium_plan,
            }
        )

    async def check_rate_limit(
        self, organization_id: str, endpoint: str, method: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limits."""

        plan = self.get_organization_plan(organization_id)
        if not plan:
            # Default to startup limits for unknown organizations
            plan = self.organization_plans["startup_default"]

        current_time = time.time()
        results = {}

        for rate_limit in plan.rate_limits:
            if not rate_limit.enabled:
                continue

            limit_key = (
                f"{organization_id}:{rate_limit.limit_type.value}:{endpoint}:{method}"
            )

            # Check rate limit
            allowed, status = await self._check_individual_rate_limit(
                limit_key, rate_limit, current_time
            )

            results[rate_limit.limit_type.value] = status

            if not allowed:
                await self._log_rate_limit_violation(
                    organization_id, endpoint, method, rate_limit
                )
                return False, results

        return True, results

    async def _check_individual_rate_limit(
        self, limit_key: str, rate_limit: RateLimit, current_time: float
    ) -> Tuple[bool, RateLimitStatus]:
        """Check individual rate limit."""

        if self.redis:
            return await self._check_redis_rate_limit(
                limit_key, rate_limit, current_time
            )
        else:
            return await self._check_memory_rate_limit(
                limit_key, rate_limit, current_time
            )

    async def _check_redis_rate_limit(
        self, limit_key: str, rate_limit: RateLimit, current_time: float
    ) -> Tuple[bool, RateLimitStatus]:
        """Check rate limit using Redis."""

        window_start = (
            int(current_time // rate_limit.window_seconds) * rate_limit.window_seconds
        )
        window_key = f"{limit_key}:{window_start}"

        # Get current count
        current_count = await self.redis.get(window_key)
        current_count = int(current_count) if current_count else 0

        # Create status
        status = RateLimitStatus(
            organization_id=limit_key.split(":")[0],
            limit_type=rate_limit.limit_type,
            current_usage=current_count,
            limit_value=rate_limit.limit_value,
            window_start=datetime.fromtimestamp(window_start),
            window_end=datetime.fromtimestamp(window_start + rate_limit.window_seconds),
            remaining=max(0, rate_limit.limit_value - current_count),
            reset_timestamp=int(window_start + rate_limit.window_seconds),
        )

        # Check if limit exceeded
        if current_count >= rate_limit.limit_value:
            return False, status

        # Increment count
        pipe = self.redis.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, rate_limit.window_seconds)
        await pipe.execute()

        status.current_usage = current_count + 1
        status.remaining = max(0, rate_limit.limit_value - status.current_usage)

        return True, status

    async def _check_memory_rate_limit(
        self, limit_key: str, rate_limit: RateLimit, current_time: float
    ) -> Tuple[bool, RateLimitStatus]:
        """Check rate limit using in-memory storage."""

        window_start = (
            int(current_time // rate_limit.window_seconds) * rate_limit.window_seconds
        )
        window_end = window_start + rate_limit.window_seconds

        # Clean old entries
        request_times = self.rate_limit_cache[limit_key][rate_limit.limit_type.value]
        while request_times and request_times[0] < window_start:
            request_times.popleft()

        current_count = len(request_times)

        # Create status
        status = RateLimitStatus(
            organization_id=limit_key.split(":")[0],
            limit_type=rate_limit.limit_type,
            current_usage=current_count,
            limit_value=rate_limit.limit_value,
            window_start=datetime.fromtimestamp(window_start),
            window_end=datetime.fromtimestamp(window_end),
            remaining=max(0, rate_limit.limit_value - current_count),
            reset_timestamp=int(window_end),
        )

        # Check if limit exceeded
        if current_count >= rate_limit.limit_value:
            return False, status

        # Add current request
        request_times.append(current_time)
        status.current_usage = current_count + 1
        status.remaining = max(0, rate_limit.limit_value - status.current_usage)

        return True, status

    async def check_quota(
        self, organization_id: str, quota_type: QuotaType, usage_amount: float = 1.0
    ) -> Tuple[bool, QuotaStatus]:
        """Check if usage is within quota limits."""

        plan = self.get_organization_plan(organization_id)
        if not plan:
            plan = self.organization_plans["startup_default"]

        # Find relevant quota
        quota = None
        for q in plan.quotas:
            if q.quota_type == quota_type:
                quota = q
                break

        if not quota:
            # No quota defined, allow usage
            return True, QuotaStatus(
                organization_id=organization_id,
                quota_type=quota_type,
                current_usage=0,
                quota_value=float("inf"),
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow() + timedelta(days=30),
                usage_percent=0.0,
            )

        # Calculate current usage in the quota period
        current_time = datetime.utcnow()
        period_start = current_time.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        period_end = period_start + timedelta(days=quota.period_days)

        current_usage = await self._get_quota_usage(
            organization_id, quota_type, period_start, period_end
        )
        projected_usage = current_usage + usage_amount

        usage_percent = (
            (current_usage / quota.quota_value) * 100 if quota.quota_value > 0 else 0
        )

        # Calculate overage
        overage_amount = max(0, projected_usage - quota.quota_value)
        estimated_cost = (
            overage_amount * quota.overage_rate if quota.overage_allowed else 0
        )

        status = QuotaStatus(
            organization_id=organization_id,
            quota_type=quota_type,
            current_usage=current_usage,
            quota_value=quota.quota_value,
            period_start=period_start,
            period_end=period_end,
            usage_percent=usage_percent,
            overage_amount=overage_amount,
            estimated_cost=estimated_cost,
            projected_usage=projected_usage,
        )

        # Check if usage would exceed quota
        if not quota.overage_allowed and projected_usage > quota.quota_value:
            return False, status

        return True, status

    async def _get_quota_usage(
        self,
        organization_id: str,
        quota_type: QuotaType,
        period_start: datetime,
        period_end: datetime,
    ) -> float:
        """Get current quota usage for the period."""

        usage = 0.0

        # Sum usage records for the period
        for record in self.usage_records:
            if (
                record.organization_id == organization_id
                and period_start <= record.timestamp <= period_end
            ):
                if (
                    quota_type == QuotaType.API_CALLS
                    and record.metric_type == UsageMetricType.API_REQUEST
                ):
                    usage += record.quantity
                elif quota_type == QuotaType.DATA_TRANSFER:
                    if record.metric_type in [
                        UsageMetricType.DATA_INGRESS,
                        UsageMetricType.DATA_EGRESS,
                    ]:
                        usage += record.quantity
                elif (
                    quota_type == QuotaType.STORAGE
                    and record.metric_type == UsageMetricType.STORAGE_GB_HOUR
                ):
                    usage += record.quantity

        return usage

    async def record_usage(
        self,
        organization_id: str,
        user_id: Optional[str],
        endpoint: str,
        method: str,
        request_size: int = 0,
        response_size: int = 0,
        processing_time_ms: int = 0,
        status_code: int = 200,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record API usage for billing and analytics."""

        # Create usage record
        usage_record = UsageRecord(
            organization_id=organization_id,
            user_id=user_id,
            metric_type=UsageMetricType.API_REQUEST,
            endpoint=endpoint,
            method=method,
            quantity=1.0,
            request_size=request_size,
            response_size=response_size,
            processing_time_ms=processing_time_ms,
            status_code=status_code,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
        )

        self.usage_records.append(usage_record)

        # Record data transfer usage
        if request_size > 0:
            ingress_record = UsageRecord(
                organization_id=organization_id,
                user_id=user_id,
                metric_type=UsageMetricType.DATA_INGRESS,
                endpoint=endpoint,
                method=method,
                quantity=request_size,
            )
            self.usage_records.append(ingress_record)

        if response_size > 0:
            egress_record = UsageRecord(
                organization_id=organization_id,
                user_id=user_id,
                metric_type=UsageMetricType.DATA_EGRESS,
                endpoint=endpoint,
                method=method,
                quantity=response_size,
            )
            self.usage_records.append(egress_record)

        # Generate billing events if needed
        await self._generate_billing_events(usage_record)

    async def _generate_billing_events(self, usage_record: UsageRecord):
        """Generate billing events for usage."""

        plan = self.get_organization_plan(usage_record.organization_id)
        if not plan:
            return

        # Calculate costs based on plan and usage
        unit_cost = self._get_unit_cost(plan, usage_record.metric_type)
        total_cost = usage_record.quantity * unit_cost

        if total_cost > 0:
            billing_event = BillingEvent(
                organization_id=usage_record.organization_id,
                metric_type=usage_record.metric_type,
                quantity=usage_record.quantity,
                unit_cost=unit_cost,
                total_cost=total_cost,
                billing_period=f"{datetime.utcnow().year}-{datetime.utcnow().month:02d}",
                metadata={
                    "endpoint": usage_record.endpoint,
                    "method": usage_record.method,
                    "status_code": usage_record.status_code,
                },
            )

            self.billing_events.append(billing_event)

    def _get_unit_cost(
        self, plan: OrganizationPlan, metric_type: UsageMetricType
    ) -> float:
        """Get unit cost for metric type based on plan."""

        # Base costs per metric type
        base_costs = {
            UsageMetricType.API_REQUEST: 0.001,
            UsageMetricType.DATA_INGRESS: 0.0001,
            UsageMetricType.DATA_EGRESS: 0.0001,
            UsageMetricType.STORAGE_GB_HOUR: 0.02,
            UsageMetricType.COMPUTE_HOUR: 0.10,
        }

        base_cost = base_costs.get(metric_type, 0.0)

        # Apply tier-based multipliers
        tier_multipliers = {
            OrganizationTier.STARTUP: 1.0,
            OrganizationTier.PROFESSIONAL: 0.8,
            OrganizationTier.ENTERPRISE: 0.6,
            OrganizationTier.PREMIUM: 0.4,
        }

        multiplier = tier_multipliers.get(plan.tier, 1.0)
        return base_cost * multiplier

    async def _log_rate_limit_violation(
        self, organization_id: str, endpoint: str, method: str, rate_limit: RateLimit
    ):
        """Log rate limit violation."""

        violation_key = (
            f"{organization_id}:{endpoint}:{method}:{rate_limit.limit_type.value}"
        )
        self.blocked_requests[violation_key] += 1

        logger.warning(
            f"Rate limit exceeded for {organization_id} on {method} {endpoint} "
            f"({rate_limit.limit_type.value}: {rate_limit.limit_value})"
        )

    def get_organization_plan(self, organization_id: str) -> Optional[OrganizationPlan]:
        """Get organization plan by ID."""

        # First check for exact match
        if organization_id in self.organization_plans:
            return self.organization_plans[organization_id]

        # Then check by tier mapping (simplified)
        # In production, this would query a database
        tier_mapping = {
            "startup": "startup_default",
            "professional": "professional_default",
            "enterprise": "enterprise_default",
            "premium": "premium_default",
        }

        for tier_key, plan_key in tier_mapping.items():
            if tier_key in organization_id.lower():
                return self.organization_plans[plan_key]

        return None

    async def get_usage_analytics(
        self, organization_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get usage analytics for organization."""

        # Filter usage records
        records = [
            record
            for record in self.usage_records
            if (
                record.organization_id == organization_id
                and start_date <= record.timestamp <= end_date
            )
        ]

        # Calculate metrics
        total_requests = len(
            [r for r in records if r.metric_type == UsageMetricType.API_REQUEST]
        )
        total_data_transfer = sum(
            r.quantity
            for r in records
            if r.metric_type
            in [UsageMetricType.DATA_INGRESS, UsageMetricType.DATA_EGRESS]
        )

        # Group by endpoint
        endpoint_stats = defaultdict(
            lambda: {"requests": 0, "avg_response_time": 0, "error_rate": 0}
        )
        for record in records:
            if record.metric_type == UsageMetricType.API_REQUEST:
                key = f"{record.method} {record.endpoint}"
                endpoint_stats[key]["requests"] += 1
                endpoint_stats[key]["avg_response_time"] += record.processing_time_ms
                if record.status_code >= 400:
                    endpoint_stats[key]["errors"] = (
                        endpoint_stats[key].get("errors", 0) + 1
                    )

        # Calculate averages and rates
        for endpoint, stats in endpoint_stats.items():
            if stats["requests"] > 0:
                stats["avg_response_time"] = (
                    stats["avg_response_time"] / stats["requests"]
                )
                stats["error_rate"] = stats.get("errors", 0) / stats["requests"] * 100

        # Get billing information
        billing_records = [
            event
            for event in self.billing_events
            if (
                event.organization_id == organization_id
                and start_date <= event.timestamp <= end_date
            )
        ]

        total_cost = sum(event.total_cost for event in billing_records)

        return {
            "organization_id": organization_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "summary": {
                "total_requests": total_requests,
                "total_data_transfer_bytes": int(total_data_transfer),
                "total_cost": total_cost,
                "avg_requests_per_day": total_requests
                / max(1, (end_date - start_date).days),
            },
            "endpoint_stats": dict(endpoint_stats),
            "quota_status": await self._get_all_quota_status(organization_id),
            "rate_limit_violations": self._get_rate_limit_violations(organization_id),
            "billing_breakdown": self._get_billing_breakdown(billing_records),
        }

    async def _get_all_quota_status(self, organization_id: str) -> Dict[str, Any]:
        """Get status for all quotas."""

        plan = self.get_organization_plan(organization_id)
        if not plan:
            return {}

        quota_status = {}
        for quota in plan.quotas:
            _, status = await self.check_quota(organization_id, quota.quota_type, 0)
            quota_status[quota.quota_type.value] = {
                "current_usage": status.current_usage,
                "quota_value": status.quota_value,
                "usage_percent": status.usage_percent,
                "overage_amount": status.overage_amount,
                "estimated_cost": status.estimated_cost,
            }

        return quota_status

    def _get_rate_limit_violations(self, organization_id: str) -> Dict[str, int]:
        """Get rate limit violations for organization."""

        violations = {}
        for key, count in self.blocked_requests.items():
            if key.startswith(organization_id):
                violations[key] = count

        return violations

    def _get_billing_breakdown(
        self, billing_records: List[BillingEvent]
    ) -> Dict[str, Any]:
        """Get billing breakdown by metric type."""

        breakdown = defaultdict(lambda: {"quantity": 0, "cost": 0})

        for record in billing_records:
            metric_type = record.metric_type.value
            breakdown[metric_type]["quantity"] += record.quantity
            breakdown[metric_type]["cost"] += record.total_cost

        return dict(breakdown)

    async def update_organization_plan(
        self, organization_id: str, plan: OrganizationPlan
    ):
        """Update organization plan."""

        self.organization_plans[organization_id] = plan
        logger.info(
            f"Updated plan for organization {organization_id} to {plan.plan_name}"
        )

    async def get_sla_metrics(
        self, organization_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get SLA metrics for organization."""

        plan = self.get_organization_plan(organization_id)
        if not plan or not plan.custom_sla:
            return {"message": "No SLA defined"}

        records = [
            record
            for record in self.usage_records
            if (
                record.organization_id == organization_id
                and start_date <= record.timestamp <= end_date
                and record.metric_type == UsageMetricType.API_REQUEST
            )
        ]

        if not records:
            return {"message": "No data available"}

        # Calculate SLA metrics
        total_requests = len(records)
        successful_requests = len([r for r in records if r.status_code < 400])
        avg_response_time = sum(r.processing_time_ms for r in records) / total_requests

        availability = (successful_requests / total_requests) * 100

        # Get SLA targets
        sla_targets = plan.custom_sla or {
            "availability_percent": 99.9,
            "avg_response_time_ms": 200,
            "max_response_time_ms": 1000,
        }

        return {
            "organization_id": organization_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "metrics": {
                "availability": {
                    "actual": availability,
                    "target": sla_targets.get("availability_percent", 99.9),
                    "compliant": availability
                    >= sla_targets.get("availability_percent", 99.9),
                },
                "avg_response_time": {
                    "actual": avg_response_time,
                    "target": sla_targets.get("avg_response_time_ms", 200),
                    "compliant": avg_response_time
                    <= sla_targets.get("avg_response_time_ms", 200),
                },
            },
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": total_requests - successful_requests,
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits on API requests."""

    def __init__(self, app, rate_limiter: EnterpriseRateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to request."""

        # Extract organization ID from request
        organization_id = await self._extract_organization_id(request)
        if not organization_id:
            organization_id = "default"

        # Get request details
        endpoint = request.url.path
        method = request.method

        # Check rate limits
        allowed, rate_limit_status = await self.rate_limiter.check_rate_limit(
            organization_id, endpoint, method
        )

        if not allowed:
            # Create rate limit exceeded response
            response_data = {
                "error": "Rate limit exceeded",
                "message": "API rate limit has been exceeded for your organization",
                "organization_id": organization_id,
                "rate_limits": {
                    limit_type: {
                        "current_usage": status.current_usage,
                        "limit_value": status.limit_value,
                        "reset_timestamp": status.reset_timestamp,
                        "remaining": status.remaining,
                    }
                    for limit_type, status in rate_limit_status.items()
                },
            }

            # Add rate limit headers
            headers = {}
            for limit_type, status in rate_limit_status.items():
                headers[f"X-RateLimit-{limit_type.replace('_', '-')}-Limit"] = str(
                    status.limit_value
                )
                headers[f"X-RateLimit-{limit_type.replace('_', '-')}-Remaining"] = str(
                    status.remaining
                )
                headers[f"X-RateLimit-{limit_type.replace('_', '-')}-Reset"] = str(
                    status.reset_timestamp
                )

            return JSONResponse(status_code=429, content=response_data, headers=headers)

        # Process request
        start_time = time.time()
        response = await call_next(request)
        processing_time = int((time.time() - start_time) * 1000)

        # Record usage
        await self.rate_limiter.record_usage(
            organization_id=organization_id,
            user_id=await self._extract_user_id(request),
            endpoint=endpoint,
            method=method,
            request_size=await self._get_request_size(request),
            response_size=self._get_response_size(response),
            processing_time_ms=processing_time,
            status_code=response.status_code,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
        )

        # Add rate limit headers to response
        for limit_type, status in rate_limit_status.items():
            response.headers[f"X-RateLimit-{limit_type.replace('_', '-')}-Limit"] = str(
                status.limit_value
            )
            response.headers[
                f"X-RateLimit-{limit_type.replace('_', '-')}-Remaining"
            ] = str(status.remaining)
            response.headers[f"X-RateLimit-{limit_type.replace('_', '-')}-Reset"] = str(
                status.reset_timestamp
            )

        return response

    async def _extract_organization_id(self, request: Request) -> Optional[str]:
        """Extract organization ID from request."""

        # Check authorization header for JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # This would decode JWT and extract org_id
                # For now, use a placeholder
                return "example_org"
            except:
                pass

        # Check API key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # This would map API key to organization
            return "example_org"

        # Check query parameter
        return request.query_params.get("org_id")

    async def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request."""

        # Similar to organization ID extraction
        return request.headers.get("X-User-ID")

    async def _get_request_size(self, request: Request) -> int:
        """Get request body size."""

        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                return int(content_length)
            except ValueError:
                pass

        return 0

    def _get_response_size(self, response) -> int:
        """Get response body size."""

        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                return int(content_length)
            except ValueError:
                pass

        return 0
