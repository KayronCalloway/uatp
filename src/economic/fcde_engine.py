"""
Fair Creator Dividend Engine (FCDE) for UATP Capsule Engine.
Implements economic attribution and dividend distribution for capsule creators.
"""

import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, getcontext
from enum import Enum
from typing import Dict, List, Set, Tuple

# Set high precision for financial calculations
getcontext().prec = 28

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when security checks fail."""

    pass


class RateLimitError(Exception):
    """Raised when rate limits are exceeded."""

    pass


class ContributionType(str, Enum):
    """Types of contributions to the UATP ecosystem."""

    CAPSULE_CREATION = "capsule_creation"
    CAPSULE_VERIFICATION = "capsule_verification"
    KNOWLEDGE_PROVISION = "knowledge_provision"
    REASONING_QUALITY = "reasoning_quality"
    SYSTEM_MAINTENANCE = "system_maintenance"
    GOVERNANCE_PARTICIPATION = "governance_participation"
    ANCESTRAL_KNOWLEDGE = "ancestral_knowledge"  # AKC integration


class RewardMetric(str, Enum):
    """Metrics for calculating rewards."""

    USAGE_FREQUENCY = "usage_frequency"
    QUALITY_SCORE = "quality_score"
    LONGEVITY_BONUS = "longevity_bonus"
    NETWORK_EFFECT = "network_effect"
    VERIFICATION_ACCURACY = "verification_accuracy"


@dataclass
class Contribution:
    """Represents a contribution to the UATP ecosystem."""

    contribution_id: str
    contributor_id: str
    contribution_type: ContributionType
    capsule_id: str
    timestamp: datetime
    quality_score: Decimal
    usage_count: int = 0
    verification_count: int = 0
    reward_multiplier: Decimal = Decimal("1.0")
    metadata: Dict[str, any] = field(default_factory=dict)

    def calculate_base_value(self) -> Decimal:
        """Calculate base value of the contribution."""
        base_values = {
            ContributionType.CAPSULE_CREATION: Decimal("100.0"),
            ContributionType.CAPSULE_VERIFICATION: Decimal("10.0"),
            ContributionType.KNOWLEDGE_PROVISION: Decimal("50.0"),
            ContributionType.REASONING_QUALITY: Decimal("75.0"),
            ContributionType.SYSTEM_MAINTENANCE: Decimal("25.0"),
            ContributionType.GOVERNANCE_PARTICIPATION: Decimal("20.0"),
            ContributionType.ANCESTRAL_KNOWLEDGE: Decimal("30.0"),  # AKC integration
        }

        base_value = base_values.get(self.contribution_type, Decimal("10.0"))
        # Incorporate usage directly into the value calculation
        usage_factor = Decimal("1.0") + (Decimal(self.usage_count) * Decimal("0.1"))
        return base_value * self.quality_score * self.reward_multiplier * usage_factor


@dataclass
class AttributionRecord:
    """Records attribution for a capsule or contribution."""

    record_id: str
    capsule_id: str
    original_creator: str
    contributors: List[str]
    contribution_percentages: Dict[str, Decimal]
    total_value_generated: Decimal
    creation_timestamp: datetime
    last_updated: datetime

    def validate_percentages(self) -> bool:
        """Validate that contribution percentages sum to 100%."""
        total = sum(self.contribution_percentages.values())
        return abs(total - Decimal("100.0")) < Decimal("0.01")


@dataclass
class DividendPool:
    """Manages dividend pool for a specific time period."""

    pool_id: str
    period_start: datetime
    period_end: datetime
    total_contributions: Decimal
    total_usage_value: Decimal
    available_dividends: Decimal
    distributed_dividends: Decimal
    contributors: Set[str] = field(default_factory=set)

    def calculate_dividend_per_contribution(self) -> Decimal:
        """Calculate dividend per contribution unit."""
        if self.total_contributions == 0:
            return Decimal("0.0")
        return self.available_dividends / self.total_contributions


@dataclass
class CreatorAccount:
    """Represents a creator's account in the FCDE system."""

    creator_id: str
    total_contributions: Decimal
    total_dividends_earned: Decimal
    total_dividends_claimed: Decimal
    unclaimed_dividends: Decimal
    contribution_history: List[str] = field(default_factory=list)
    reputation_score: Decimal = Decimal("100.0")
    account_created: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    # SECURITY: Additional security and tracking fields
    metadata: Dict[str, any] = field(default_factory=dict)

    def update_unclaimed_dividends(self, amount: Decimal):
        """Update unclaimed dividends."""
        self.unclaimed_dividends += amount
        self.total_dividends_earned += amount


class FCDEEngine:
    """Fair Creator Dividend Engine for economic attribution and rewards."""

    def __init__(self):
        self.contributions: Dict[str, Contribution] = {}
        self.attributions: Dict[str, AttributionRecord] = {}
        self.dividend_pools: Dict[str, DividendPool] = {}
        self.creator_accounts: Dict[str, CreatorAccount] = {}
        self.system_treasury: Decimal = Decimal("1000000.0")  # Initial treasury
        self.dividend_rate: Decimal = Decimal("0.05")  # 5% dividend rate
        self.current_period_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # SECURITY: Sybil resistance and rate limiting data structures
        self.account_creation_log: Dict[str, List[Tuple[datetime, str]]] = defaultdict(
            list
        )  # IP -> [(timestamp, contributor_id)]
        self.security_config = {
            "max_accounts_per_ip_per_day": 3,  # Maximum accounts per IP per day
            "max_accounts_per_ip_total": 10,  # Maximum accounts per IP total
            "identity_verification_required": True,  # Require identity verification
            "behavioral_analysis_enabled": True,  # Enable behavioral analysis
            "min_account_age_for_dividends": 24,  # Hours before eligible for dividends
            "rate_limit_window_hours": 24,  # Rate limiting window
        }

        # SECURITY: Security statistics
        self.security_stats = {
            "blocked_sybil_attempts": 0,
            "rate_limit_violations": 0,
            "identity_verification_failures": 0,
            "behavioral_analysis_flags": 0,
        }

    def register_contribution(
        self,
        capsule_id: str,
        contributor_id: str,
        contribution_type: ContributionType,
        quality_score: Decimal = Decimal("1.0"),
        metadata: Dict[str, any] = None,
    ) -> str:
        """Register a new contribution to the system with Sybil resistance."""

        # SECURITY: Verify contributor legitimacy before account creation
        if contributor_id not in self.creator_accounts:
            if not self.verify_contributor_legitimacy(contributor_id, metadata):
                raise SecurityError(
                    f"Contributor verification failed for {contributor_id}"
                )

            # SECURITY: Enforce rate limits on account creation
            contributor_ip = (
                metadata.get("ip_address", "unknown") if metadata else "unknown"
            )
            if self.check_account_creation_rate_limit(contributor_ip):
                raise RateLimitError(
                    f"Too many accounts created from source {contributor_ip}"
                )

        contribution_id = self._generate_contribution_id(capsule_id, contributor_id)

        contribution = Contribution(
            contribution_id=contribution_id,
            contributor_id=contributor_id,
            contribution_type=contribution_type,
            capsule_id=capsule_id,
            timestamp=datetime.now(timezone.utc),
            quality_score=quality_score,
            metadata=metadata or {},
        )

        self.contributions[contribution_id] = contribution

        # Create or update creator account with security tracking
        if contributor_id not in self.creator_accounts:
            self.creator_accounts[contributor_id] = CreatorAccount(
                creator_id=contributor_id,
                total_contributions=Decimal("0.0"),
                total_dividends_earned=Decimal("0.0"),
                total_dividends_claimed=Decimal("0.0"),
                unclaimed_dividends=Decimal("0.0"),
                metadata={
                    "registration_ip": contributor_ip,
                    "first_contribution_timestamp": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "identity_verified": metadata.get("identity_verified", False)
                    if metadata
                    else False,
                    "behavioral_flags": [],
                },
            )

            # SECURITY: Track account creation by IP for rate limiting
            self._track_account_creation(contributor_ip, contributor_id)

        account = self.creator_accounts[contributor_id]
        account.contribution_history.append(contribution_id)
        account.total_contributions += contribution.calculate_base_value()

        # Create attribution record
        self._create_attribution_record(capsule_id, contributor_id, contribution)

        logger.info(f"Registered contribution {contribution_id} for {contributor_id}")
        return contribution_id

    def record_capsule_usage(
        self, capsule_id: str, usage_value: Decimal = Decimal("1.0")
    ):
        """Record usage of a capsule for dividend calculations."""

        if capsule_id not in self.attributions:
            logger.warning(f"No attribution record found for capsule {capsule_id}")
            return

        attribution = self.attributions[capsule_id]
        attribution.total_value_generated += usage_value
        attribution.last_updated = datetime.now(timezone.utc)

        # Update contribution usage counts based on actual usage value
        for contributor_id in attribution.contributors:
            for contribution in self.contributions.values():
                if (
                    contribution.contributor_id == contributor_id
                    and contribution.capsule_id == capsule_id
                ):
                    # Use usage_value to influence usage_count more significantly
                    usage_increment = max(
                        1, int(usage_value / Decimal("10"))
                    )  # Scale usage appropriately
                    contribution.usage_count += usage_increment

        logger.info(f"Recorded usage for capsule {capsule_id}: {usage_value}")

    def calculate_quality_multiplier(self, capsule_id: str) -> Decimal:
        """Calculate quality multiplier based on capsule metrics."""

        if capsule_id not in self.attributions:
            return Decimal("1.0")

        attribution = self.attributions[capsule_id]

        # Base quality metrics - minimum of 1.0 for new contributions
        usage_score = max(
            Decimal("1.0"),
            min(
                Decimal(str(attribution.total_value_generated)) / Decimal("100.0"),
                Decimal("2.0"),
            ),
        )

        # Time-based longevity bonus
        age_days = (datetime.now(timezone.utc) - attribution.creation_timestamp).days
        longevity_bonus = Decimal("1.0") + (
            Decimal(str(age_days)) / Decimal("365.0")
        ) * Decimal("0.1")

        # Network effect multiplier
        network_multiplier = Decimal("1.0") + (
            Decimal(str(len(attribution.contributors))) * Decimal("0.05")
        )

        total_multiplier = usage_score * longevity_bonus * network_multiplier
        return min(total_multiplier, Decimal("5.0"))  # Cap at 5x

    def process_dividend_distribution(self, pool_value: Decimal = None) -> str:
        """Process dividend distribution for the current period."""

        if pool_value is None:
            pool_value = self.system_treasury * self.dividend_rate

        period_end = datetime.now(timezone.utc)
        pool_id = (
            f"pool_{self.current_period_start.isoformat()}_{period_end.isoformat()}"
        )

        # Identify contributions for this period
        period_contributions = [
            c
            for c in self.contributions.values()
            if self.current_period_start <= c.timestamp <= period_end
        ]

        if not period_contributions:
            logger.info("No contributions in this period. No dividends distributed.")
            return pool_id

        # Update reward multipliers and calculate total contribution value
        total_contributions = Decimal("0.0")
        for contribution in period_contributions:
            quality_multiplier = self.calculate_quality_multiplier(
                contribution.capsule_id
            )
            contribution.reward_multiplier = quality_multiplier
            total_contributions += contribution.calculate_base_value()

        # Create dividend pool
        dividend_pool = DividendPool(
            pool_id=pool_id,
            period_start=self.current_period_start,
            period_end=period_end,
            total_contributions=total_contributions,
            total_usage_value=Decimal("0.0"),  # Could be calculated from usage records
            available_dividends=pool_value,
            distributed_dividends=Decimal("0.0"),
            contributors={c.contributor_id for c in period_contributions},
        )

        # Distribute dividends
        if total_contributions > 0:
            for contribution in period_contributions:
                contribution_value = contribution.calculate_base_value()
                # Calculate dividend proportional to contribution value
                dividend_amount = (
                    contribution_value / total_contributions
                ) * pool_value

                # Add to creator account using the proper method that updates both counters
                creator_account = self.creator_accounts[contribution.contributor_id]
                creator_account.update_unclaimed_dividends(dividend_amount)

                dividend_pool.distributed_dividends += dividend_amount

        self.dividend_pools[pool_id] = dividend_pool
        self.system_treasury -= pool_value

        # Start new period
        self.current_period_start = period_end

        logger.info(
            f"Processed dividend distribution: {pool_id}, distributed: {dividend_pool.distributed_dividends}"
        )
        return pool_id

    def claim_dividends(
        self, creator_id: str, amount: Decimal = None
    ) -> Tuple[Decimal, str]:
        """Allow creator to claim their dividends."""

        if creator_id not in self.creator_accounts:
            raise ValueError(f"Creator {creator_id} not found.")

        account = self.creator_accounts[creator_id]

        amount_to_claim = amount or account.unclaimed_dividends

        if amount_to_claim > account.unclaimed_dividends:
            raise ValueError(
                f"Cannot claim {amount_to_claim}, only {account.unclaimed_dividends} available."
            )

        if amount_to_claim <= 0:
            return Decimal("0.0"), "No dividends to claim."

        account.unclaimed_dividends -= amount_to_claim
        account.total_dividends_claimed += amount_to_claim

        logger.info(f"Creator {creator_id} claimed dividends: {amount_to_claim}")
        message = f"Successfully claimed {amount_to_claim:.4f} dividends."
        return amount_to_claim, message

    def get_creator_analytics(self, creator_id: str) -> Dict[str, any]:
        """Get analytics for a creator."""

        if creator_id not in self.creator_accounts:
            return {"error": "Creator not found"}

        account = self.creator_accounts[creator_id]

        # Calculate contribution breakdown
        contribution_breakdown = {}
        for contribution_id in account.contribution_history:
            if contribution_id in self.contributions:
                contribution = self.contributions[contribution_id]
                contrib_type = contribution.contribution_type.value
                if contrib_type not in contribution_breakdown:
                    contribution_breakdown[contrib_type] = {
                        "count": 0,
                        "total_value": Decimal("0.0"),
                    }
                contribution_breakdown[contrib_type]["count"] += 1
                contribution_breakdown[contrib_type][
                    "total_value"
                ] += contribution.calculate_base_value()

        # Calculate recent activity
        recent_contributions = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

        for contribution_id in account.contribution_history:
            if contribution_id in self.contributions:
                contribution = self.contributions[contribution_id]
                if contribution.timestamp >= cutoff_date:
                    recent_contributions.append(
                        {
                            "contribution_id": contribution_id,
                            "type": contribution.contribution_type.value,
                            "capsule_id": contribution.capsule_id,
                            "value": float(contribution.calculate_base_value()),
                            "timestamp": contribution.timestamp.isoformat(),
                        }
                    )

        return {
            "creator_id": creator_id,
            "account_created": account.account_created.isoformat(),
            "total_contributions": float(account.total_contributions),
            "total_dividends_earned": float(account.total_dividends_earned),
            "total_dividends_claimed": float(account.total_dividends_claimed),
            "unclaimed_dividends": float(account.unclaimed_dividends),
            "reputation_score": float(account.reputation_score),
            "contribution_breakdown": {
                k: {"count": v["count"], "total_value": float(v["total_value"])}
                for k, v in contribution_breakdown.items()
            },
            "recent_contributions": recent_contributions,
        }

    def get_system_analytics(self) -> Dict[str, any]:
        """Get system-wide analytics."""

        total_contributions = len(self.contributions)
        total_creators = len(self.creator_accounts)
        total_treasury = float(self.system_treasury)

        total_dividends_distributed = sum(
            float(pool.distributed_dividends) for pool in self.dividend_pools.values()
        )

        # Top contributors
        top_contributors = sorted(
            self.creator_accounts.items(),
            key=lambda x: x[1].total_contributions,
            reverse=True,
        )[:10]

        # Contribution type distribution
        contribution_types = {}
        for contribution in self.contributions.values():
            contrib_type = contribution.contribution_type.value
            if contrib_type not in contribution_types:
                contribution_types[contrib_type] = 0
            contribution_types[contrib_type] += 1

        return {
            "total_contributions": total_contributions,
            "total_creators": total_creators,
            "system_treasury": total_treasury,
            "total_dividends_distributed": total_dividends_distributed,
            "dividend_pools": len(self.dividend_pools),
            "top_contributors": [
                {
                    "creator_id": creator_id,
                    "total_contributions": float(account.total_contributions),
                    "total_dividends_earned": float(account.total_dividends_earned),
                }
                for creator_id, account in top_contributors
            ],
            "contribution_type_distribution": contribution_types,
            "current_dividend_rate": float(self.dividend_rate),
        }

    def _generate_contribution_id(self, capsule_id: str, contributor_id: str) -> str:
        """Generate unique contribution ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        combined = f"{capsule_id}:{contributor_id}:{timestamp}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _create_attribution_record(
        self, capsule_id: str, contributor_id: str, contribution: Contribution
    ):
        """Create or update attribution record for a capsule."""

        if capsule_id not in self.attributions:
            # Create new attribution record
            self.attributions[capsule_id] = AttributionRecord(
                record_id=f"attr_{capsule_id}",
                capsule_id=capsule_id,
                original_creator=contributor_id,
                contributors=[contributor_id],
                contribution_percentages={contributor_id: Decimal("100.0")},
                total_value_generated=Decimal("0.0"),
                creation_timestamp=contribution.timestamp,
                last_updated=contribution.timestamp,
            )
        else:
            # Update existing attribution record
            attribution = self.attributions[capsule_id]
            if contributor_id not in attribution.contributors:
                attribution.contributors.append(contributor_id)

                # Recalculate contribution percentages
                # For simplicity, distribute evenly among contributors
                num_contributors = len(attribution.contributors)
                percentage_per_contributor = Decimal("100.0") / Decimal(
                    str(num_contributors)
                )

                attribution.contribution_percentages = {
                    contrib_id: percentage_per_contributor
                    for contrib_id in attribution.contributors
                }

                attribution.last_updated = contribution.timestamp

    def update_treasury(self, amount: Decimal, description: str = "Treasury update"):
        """Update system treasury."""
        self.system_treasury += amount
        logger.info(
            f"Treasury updated: {amount} ({description}). New balance: {self.system_treasury}"
        )

    def verify_contributor_legitimacy(
        self, contributor_id: str, metadata: Dict[str, any] = None
    ) -> bool:
        """Verify contributor legitimacy to prevent Sybil attacks."""

        if not self.security_config.get("behavioral_analysis_enabled", True):
            return True

        # SECURITY: Check identity verification requirement
        if self.security_config.get("identity_verification_required", True):
            if not metadata or not metadata.get("identity_verified", False):
                logger.warning(
                    f"Identity verification failed for contributor {contributor_id}"
                )
                self.security_stats["identity_verification_failures"] += 1
                return False

        # SECURITY: Basic behavioral analysis
        if metadata:
            # Check for suspicious patterns in metadata
            if self._detect_suspicious_metadata_patterns(metadata):
                logger.warning(
                    f"Suspicious metadata patterns detected for contributor {contributor_id}"
                )
                self.security_stats["behavioral_analysis_flags"] += 1
                return False

        return True

    def check_account_creation_rate_limit(self, ip_address: str) -> bool:
        """Check if account creation rate limit is exceeded for IP address."""

        if ip_address == "unknown":
            return False  # Allow unknown IPs but log them

        current_time = datetime.now(timezone.utc)
        rate_limit_window = timedelta(
            hours=self.security_config["rate_limit_window_hours"]
        )

        # Get account creation history for this IP
        ip_history = self.account_creation_log.get(ip_address, [])

        # Remove old entries outside the rate limit window
        recent_history = [
            (timestamp, contributor_id)
            for timestamp, contributor_id in ip_history
            if current_time - timestamp <= rate_limit_window
        ]

        # Update the cleaned history
        self.account_creation_log[ip_address] = recent_history

        # SECURITY: Check daily rate limit
        daily_count = len(recent_history)
        max_daily = self.security_config["max_accounts_per_ip_per_day"]

        if daily_count >= max_daily:
            logger.warning(
                f"Daily account creation rate limit exceeded for IP {ip_address}: {daily_count}/{max_daily}"
            )
            self.security_stats["rate_limit_violations"] += 1
            return True  # Rate limit exceeded

        # SECURITY: Check total accounts from this IP
        total_count = len(ip_history)
        max_total = self.security_config["max_accounts_per_ip_total"]

        if total_count >= max_total:
            logger.warning(
                f"Total account creation limit exceeded for IP {ip_address}: {total_count}/{max_total}"
            )
            self.security_stats["blocked_sybil_attempts"] += 1
            return True  # Rate limit exceeded

        return False  # Rate limit not exceeded

    def _track_account_creation(self, ip_address: str, contributor_id: str):
        """Track account creation for rate limiting and Sybil detection."""

        current_time = datetime.now(timezone.utc)
        self.account_creation_log[ip_address].append((current_time, contributor_id))

        logger.info(f"Tracked account creation: {contributor_id} from IP {ip_address}")

    def _detect_suspicious_metadata_patterns(self, metadata: Dict[str, any]) -> bool:
        """Detect suspicious patterns in contribution metadata."""

        # SECURITY: Check for obviously fake or template-like data
        suspicious_patterns = [
            "test",
            "fake",
            "bot",
            "auto",
            "generated",
            "temp",
            "spam",
        ]

        # Check contributor name/description for suspicious terms
        description = str(metadata.get("description", "")).lower()
        name = str(metadata.get("name", "")).lower()

        for pattern in suspicious_patterns:
            if pattern in description or pattern in name:
                return True

        # SECURITY: Check for minimal/template descriptions
        if len(description) < 10 and description.strip():
            return True  # Too short to be legitimate

        # SECURITY: Check for repeated character patterns (bot behavior)
        if description and len(set(description.replace(" ", ""))) < 3:
            return True  # Too few unique characters

        return False

    def get_security_analytics(self) -> Dict[str, any]:
        """Get security-related analytics and statistics."""

        # Account creation patterns by IP
        ip_analysis = {}
        for ip, history in self.account_creation_log.items():
            ip_analysis[ip] = {
                "total_accounts": len(history),
                "recent_accounts": len(
                    [
                        h
                        for h in history
                        if (datetime.now(timezone.utc) - h[0]).total_seconds()
                        < 86400  # Last 24 hours
                    ]
                ),
                "first_account": min(h[0] for h in history).isoformat()
                if history
                else None,
                "last_account": max(h[0] for h in history).isoformat()
                if history
                else None,
            }

        # High-risk IPs (those with many accounts)
        high_risk_ips = [
            ip
            for ip, analysis in ip_analysis.items()
            if analysis["total_accounts"]
            >= self.security_config["max_accounts_per_ip_per_day"]
        ]

        return {
            "security_stats": self.security_stats.copy(),
            "security_config": self.security_config.copy(),
            "ip_analysis": ip_analysis,
            "high_risk_ips": high_risk_ips,
            "total_unique_ips": len(self.account_creation_log),
            "accounts_with_identity_verification": sum(
                1
                for account in self.creator_accounts.values()
                if account.metadata.get("identity_verified", False)
            ),
        }

    def set_dividend_rate(self, new_rate: Decimal):
        """Set new dividend rate."""
        if not (Decimal("0.0") <= new_rate <= Decimal("1.0")):
            raise ValueError("Dividend rate must be between 0.0 and 1.0")

        self.dividend_rate = new_rate
        logger.info(f"Dividend rate updated to: {new_rate}")

    def is_eligible_for_dividends(self, creator_id: str) -> Tuple[bool, str]:
        """Check if creator is eligible for dividend distribution."""

        if creator_id not in self.creator_accounts:
            return False, "Creator account not found"

        account = self.creator_accounts[creator_id]
        current_time = datetime.now(timezone.utc)

        # SECURITY: Check minimum account age
        account_created = datetime.fromisoformat(
            account.metadata.get(
                "first_contribution_timestamp", current_time.isoformat()
            )
        )
        account_age_hours = (current_time - account_created).total_seconds() / 3600
        min_age_hours = self.security_config["min_account_age_for_dividends"]

        if account_age_hours < min_age_hours:
            return (
                False,
                f"Account too new: {account_age_hours:.1f}h < {min_age_hours}h required",
            )

        # SECURITY: Check for behavioral flags
        behavioral_flags = account.metadata.get("behavioral_flags", [])
        if behavioral_flags:
            return False, f"Account flagged for suspicious behavior: {behavioral_flags}"

        # SECURITY: Verify identity if required
        if self.security_config.get("identity_verification_required", True):
            if not account.metadata.get("identity_verified", False):
                return False, "Identity verification required for dividend eligibility"

        return True, "Eligible for dividends"


# Global FCDE engine instance
fcde_engine = FCDEEngine()

# Default contribution quality scores
DEFAULT_QUALITY_SCORES = {
    ContributionType.CAPSULE_CREATION: Decimal("1.0"),
    ContributionType.CAPSULE_VERIFICATION: Decimal("0.8"),
    ContributionType.KNOWLEDGE_PROVISION: Decimal("1.2"),
    ContributionType.REASONING_QUALITY: Decimal("1.5"),
    ContributionType.SYSTEM_MAINTENANCE: Decimal("0.7"),
    ContributionType.GOVERNANCE_PARTICIPATION: Decimal("0.9"),
}
