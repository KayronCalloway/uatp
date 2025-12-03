"""
Real-time Economic Security Monitor for UATP System.

This module provides comprehensive monitoring and alerting for economic attacks
across all UATP components including attribution gaming, dividend manipulation,
governance attacks, and payment system exploits.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat levels for security alerts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackType(Enum):
    """Types of economic attacks being monitored."""

    ATTRIBUTION_GAMING = "attribution_gaming"
    DIVIDEND_MANIPULATION = "dividend_manipulation"
    SYBIL_ATTACK = "sybil_attack"
    FLASH_LOAN_ATTACK = "flash_loan_attack"
    GOVERNANCE_CAPTURE = "governance_capture"
    PAYMENT_EXPLOITATION = "payment_exploitation"
    CONCENTRATION_ATTACK = "concentration_attack"
    WASH_TRADING = "wash_trading"


@dataclass
class SecurityAlert:
    """Represents a security alert from the monitoring system."""

    alert_id: str
    attack_type: AttackType
    threat_level: ThreatLevel
    timestamp: datetime
    description: str
    affected_entities: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    recommended_actions: List[str] = field(default_factory=list)
    auto_mitigated: bool = False


@dataclass
class MetricSnapshot:
    """Snapshot of economic metrics at a point in time."""

    timestamp: datetime
    attribution_similarity_scores: Dict[str, float] = field(default_factory=dict)
    dividend_concentrations: Dict[str, float] = field(default_factory=dict)
    voting_power_distributions: Dict[str, float] = field(default_factory=dict)
    payment_transaction_volumes: Dict[str, Decimal] = field(default_factory=dict)
    account_creation_rates: Dict[str, int] = field(default_factory=dict)
    governance_participation_rates: Dict[str, float] = field(default_factory=dict)


class EconomicSecurityMonitor:
    """
    Real-time monitoring system for economic security threats.

    Monitors multiple attack vectors simultaneously and provides early warning
    system with automated response capabilities.
    """

    def __init__(self):
        self.alerts: List[SecurityAlert] = []
        self.active_threats: Dict[str, SecurityAlert] = {}
        self.metric_history: deque = deque(maxlen=1000)  # Last 1000 snapshots
        self.monitoring_active = False
        self.alert_callbacks: List[callable] = []

        # Monitoring thresholds
        self.thresholds = {
            "attribution_similarity_threshold": 0.95,
            "dividend_concentration_threshold": 0.25,
            "voting_power_concentration_threshold": 0.15,
            "account_creation_rate_threshold": 10,  # per hour
            "payment_volume_spike_threshold": 5.0,  # 5x normal volume
            "governance_capture_threshold": 0.30,
        }

        # Pattern detection windows
        self.detection_windows = {
            "attribution_gaming": timedelta(minutes=30),
            "sybil_attack": timedelta(hours=1),
            "flash_loan": timedelta(minutes=5),
            "governance_capture": timedelta(hours=24),
            "wash_trading": timedelta(hours=6),
        }

        # Real-time tracking
        self.attribution_events = deque(maxlen=1000)
        self.dividend_events = deque(maxlen=1000)
        self.governance_events = deque(maxlen=1000)
        self.payment_events = deque(maxlen=1000)
        self.account_creation_events = deque(maxlen=1000)

        # Suspicious entity tracking
        self.flagged_entities: Dict[str, Dict[str, Any]] = {}
        self.ip_tracking: Dict[str, List[datetime]] = defaultdict(list)
        self.entity_relationships: Dict[str, Set[str]] = defaultdict(set)

    async def start_monitoring(self):
        """Start the real-time monitoring system."""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return

        self.monitoring_active = True
        logger.info("Starting economic security monitoring")

        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_attribution_gaming()),
            asyncio.create_task(self._monitor_dividend_manipulation()),
            asyncio.create_task(self._monitor_sybil_attacks()),
            asyncio.create_task(self._monitor_flash_loan_attacks()),
            asyncio.create_task(self._monitor_governance_capture()),
            asyncio.create_task(self._monitor_payment_exploitation()),
            asyncio.create_task(self._generate_metric_snapshots()),
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            self.monitoring_active = False

    async def stop_monitoring(self):
        """Stop the monitoring system."""
        self.monitoring_active = False
        logger.info("Stopped economic security monitoring")

    def register_alert_callback(self, callback: callable):
        """Register a callback function to receive security alerts."""
        self.alert_callbacks.append(callback)

    async def record_attribution_event(self, event_data: Dict[str, Any]):
        """Record an attribution-related event for monitoring."""
        event_data["timestamp"] = datetime.now(timezone.utc)
        self.attribution_events.append(event_data)

        # Check for immediate threats
        await self._check_attribution_gaming_patterns()

    async def record_dividend_event(self, event_data: Dict[str, Any]):
        """Record a dividend-related event for monitoring."""
        event_data["timestamp"] = datetime.now(timezone.utc)
        self.dividend_events.append(event_data)

        # Check for immediate threats
        await self._check_dividend_manipulation_patterns()

    async def record_governance_event(self, event_data: Dict[str, Any]):
        """Record a governance-related event for monitoring."""
        event_data["timestamp"] = datetime.now(timezone.utc)
        self.governance_events.append(event_data)

        # Check for immediate threats
        await self._check_governance_capture_patterns()

    async def record_payment_event(self, event_data: Dict[str, Any]):
        """Record a payment-related event for monitoring."""
        event_data["timestamp"] = datetime.now(timezone.utc)
        self.payment_events.append(event_data)

        # Check for immediate threats
        await self._check_payment_exploitation_patterns()

    async def record_account_creation_event(self, event_data: Dict[str, Any]):
        """Record an account creation event for monitoring."""
        event_data["timestamp"] = datetime.now(timezone.utc)
        self.account_creation_events.append(event_data)

        # Track IP addresses for Sybil detection
        ip_address = event_data.get("ip_address")
        if ip_address:
            self.ip_tracking[ip_address].append(event_data["timestamp"])

        # Check for immediate threats
        await self._check_sybil_attack_patterns()

    async def _monitor_attribution_gaming(self):
        """Monitor for attribution gaming attacks."""
        while self.monitoring_active:
            try:
                await self._check_attribution_gaming_patterns()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Attribution gaming monitoring error: {e}")
                await asyncio.sleep(60)

    async def _check_attribution_gaming_patterns(self):
        """Check for attribution gaming attack patterns."""
        current_time = datetime.now(timezone.utc)
        window_start = current_time - self.detection_windows["attribution_gaming"]

        # Get recent attribution events
        recent_events = [
            event
            for event in self.attribution_events
            if event["timestamp"] >= window_start
        ]

        if not recent_events:
            return

        # Check for high similarity scores
        high_similarity_events = [
            event
            for event in recent_events
            if event.get("similarity_score", 0)
            > self.thresholds["attribution_similarity_threshold"]
        ]

        if len(high_similarity_events) >= 5:  # 5+ high similarity events in 30 minutes
            await self._create_alert(
                AttackType.ATTRIBUTION_GAMING,
                ThreatLevel.HIGH,
                f"Attribution gaming detected: {len(high_similarity_events)} high similarity events",
                affected_entities=[
                    event.get("content_hash") for event in high_similarity_events
                ],
                evidence={
                    "high_similarity_count": len(high_similarity_events),
                    "time_window": "30 minutes",
                    "similarity_scores": [
                        event.get("similarity_score")
                        for event in high_similarity_events
                    ],
                },
                recommended_actions=[
                    "Review flagged content for artificial similarity",
                    "Increase similarity detection strictness",
                    "Manual review of contributor patterns",
                ],
            )

    async def _monitor_dividend_manipulation(self):
        """Monitor for dividend manipulation attacks."""
        while self.monitoring_active:
            try:
                await self._check_dividend_manipulation_patterns()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Dividend manipulation monitoring error: {e}")
                await asyncio.sleep(120)

    async def _check_dividend_manipulation_patterns(self):
        """Check for dividend manipulation patterns."""
        current_time = datetime.now(timezone.utc)
        window_start = current_time - timedelta(hours=1)

        # Get recent dividend events
        recent_events = [
            event
            for event in self.dividend_events
            if event["timestamp"] >= window_start
        ]

        if not recent_events:
            return

        # Check for concentration violations
        recipient_totals = defaultdict(Decimal)
        for event in recent_events:
            recipient_id = event.get("recipient_id")
            amount = Decimal(str(event.get("amount", 0)))
            if recipient_id:
                recipient_totals[recipient_id] += amount

        total_distributed = sum(recipient_totals.values())
        if total_distributed > 0:
            for recipient_id, amount in recipient_totals.items():
                concentration = float(amount / total_distributed)
                if concentration > self.thresholds["dividend_concentration_threshold"]:
                    await self._create_alert(
                        AttackType.DIVIDEND_MANIPULATION,
                        ThreatLevel.HIGH,
                        f"Dividend concentration attack: {recipient_id} received {concentration:.1%}",
                        affected_entities=[recipient_id],
                        evidence={
                            "concentration_ratio": concentration,
                            "amount": str(amount),
                            "total_distributed": str(total_distributed),
                        },
                        recommended_actions=[
                            "Review recipient legitimacy",
                            "Implement stricter concentration limits",
                            "Investigate recipient relationships",
                        ],
                    )

    async def _monitor_sybil_attacks(self):
        """Monitor for Sybil attacks."""
        while self.monitoring_active:
            try:
                await self._check_sybil_attack_patterns()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Sybil attack monitoring error: {e}")
                await asyncio.sleep(120)

    async def _check_sybil_attack_patterns(self):
        """Check for Sybil attack patterns."""
        current_time = datetime.now(timezone.utc)
        window_start = current_time - self.detection_windows["sybil_attack"]

        # Check IP-based account creation patterns
        for ip_address, timestamps in self.ip_tracking.items():
            recent_creations = [ts for ts in timestamps if ts >= window_start]

            if (
                len(recent_creations)
                > self.thresholds["account_creation_rate_threshold"]
            ):
                await self._create_alert(
                    AttackType.SYBIL_ATTACK,
                    ThreatLevel.CRITICAL,
                    f"Sybil attack detected: {len(recent_creations)} accounts from IP {ip_address}",
                    affected_entities=[ip_address],
                    evidence={
                        "account_count": len(recent_creations),
                        "ip_address": ip_address,
                        "time_window": "1 hour",
                    },
                    recommended_actions=[
                        "Block IP address from creating new accounts",
                        "Review all accounts created from this IP",
                        "Implement additional identity verification",
                    ],
                )

    async def _monitor_flash_loan_attacks(self):
        """Monitor for flash loan-style attacks."""
        while self.monitoring_active:
            try:
                await self._check_flash_loan_patterns()
                await asyncio.sleep(15)  # Check every 15 seconds for rapid attacks
            except Exception as e:
                logger.error(f"Flash loan monitoring error: {e}")
                await asyncio.sleep(60)

    async def _check_flash_loan_patterns(self):
        """Check for flash loan attack patterns."""
        current_time = datetime.now(timezone.utc)
        window_start = current_time - self.detection_windows["flash_loan"]

        # Get recent high-value events across all systems
        recent_high_value_events = []

        for event in self.dividend_events:
            if event["timestamp"] >= window_start and Decimal(
                str(event.get("amount", 0))
            ) > Decimal("1000"):
                recent_high_value_events.append(event)

        for event in self.governance_events:
            if (
                event["timestamp"] >= window_start
                and event.get("event_type") == "large_stake_change"
            ):
                recent_high_value_events.append(event)

        # Check for rapid sequence of high-value events
        if len(recent_high_value_events) >= 3:  # 3+ high-value events in 5 minutes
            await self._create_alert(
                AttackType.FLASH_LOAN_ATTACK,
                ThreatLevel.CRITICAL,
                f"Flash loan attack pattern: {len(recent_high_value_events)} rapid high-value events",
                affected_entities=[
                    event.get("entity_id") for event in recent_high_value_events
                ],
                evidence={
                    "event_count": len(recent_high_value_events),
                    "time_window": "5 minutes",
                    "event_details": recent_high_value_events,
                },
                recommended_actions=[
                    "Immediately halt high-value transactions",
                    "Activate atomic state rollback procedures",
                    "Investigate transaction sequence for manipulation",
                ],
            )

    async def _monitor_governance_capture(self):
        """Monitor for governance capture attempts."""
        while self.monitoring_active:
            try:
                await self._check_governance_capture_patterns()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Governance capture monitoring error: {e}")
                await asyncio.sleep(600)

    async def _check_governance_capture_patterns(self):
        """Check for governance capture patterns."""
        current_time = datetime.now(timezone.utc)
        window_start = current_time - self.detection_windows["governance_capture"]

        # Get recent governance events
        recent_events = [
            event
            for event in self.governance_events
            if event["timestamp"] >= window_start
        ]

        if not recent_events:
            return

        # Check for coordinated voting patterns
        voting_clusters = defaultdict(list)
        for event in recent_events:
            if event.get("event_type") == "vote_cast":
                vote_time = event["timestamp"]
                voting_clusters[vote_time.replace(second=0, microsecond=0)].append(
                    event
                )

        # Look for suspicious voting synchronization
        for time_bucket, votes in voting_clusters.items():
            if len(votes) > 10:  # More than 10 votes in the same minute
                await self._create_alert(
                    AttackType.GOVERNANCE_CAPTURE,
                    ThreatLevel.HIGH,
                    f"Coordinated voting detected: {len(votes)} votes at {time_bucket}",
                    affected_entities=[vote.get("voter_id") for vote in votes],
                    evidence={
                        "synchronized_votes": len(votes),
                        "time_bucket": time_bucket.isoformat(),
                        "voter_ids": [vote.get("voter_id") for vote in votes],
                    },
                    recommended_actions=[
                        "Review voter relationships and coordination",
                        "Implement voting time randomization",
                        "Investigate potential vote buying",
                    ],
                )

    async def _monitor_payment_exploitation(self):
        """Monitor for payment system exploitation."""
        while self.monitoring_active:
            try:
                await self._check_payment_exploitation_patterns()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Payment exploitation monitoring error: {e}")
                await asyncio.sleep(120)

    async def _check_payment_exploitation_patterns(self):
        """Check for payment exploitation patterns."""
        current_time = datetime.now(timezone.utc)
        window_start = current_time - timedelta(minutes=15)

        # Get recent payment events
        recent_events = [
            event for event in self.payment_events if event["timestamp"] >= window_start
        ]

        if not recent_events:
            return

        # Check for webhook signature failures
        signature_failures = [
            event
            for event in recent_events
            if event.get("event_type") == "webhook_signature_failure"
        ]

        if len(signature_failures) >= 5:  # 5+ signature failures in 15 minutes
            await self._create_alert(
                AttackType.PAYMENT_EXPLOITATION,
                ThreatLevel.HIGH,
                f"Payment webhook attack: {len(signature_failures)} signature failures",
                affected_entities=[
                    event.get("ip_address") for event in signature_failures
                ],
                evidence={
                    "signature_failure_count": len(signature_failures),
                    "time_window": "15 minutes",
                    "ip_addresses": list(
                        set(event.get("ip_address") for event in signature_failures)
                    ),
                },
                recommended_actions=[
                    "Block suspicious IP addresses",
                    "Review webhook security configuration",
                    "Implement additional rate limiting",
                ],
            )

    async def _generate_metric_snapshots(self):
        """Generate periodic metric snapshots for analysis."""
        while self.monitoring_active:
            try:
                snapshot = MetricSnapshot(timestamp=datetime.now(timezone.utc))
                self.metric_history.append(snapshot)
                await asyncio.sleep(300)  # Generate snapshot every 5 minutes
            except Exception as e:
                logger.error(f"Metric snapshot generation error: {e}")
                await asyncio.sleep(600)

    async def _create_alert(
        self,
        attack_type: AttackType,
        threat_level: ThreatLevel,
        description: str,
        affected_entities: List[str] = None,
        evidence: Dict[str, Any] = None,
        recommended_actions: List[str] = None,
    ):
        """Create and distribute a security alert."""

        alert_id = f"{attack_type.value}_{int(time.time())}"

        alert = SecurityAlert(
            alert_id=alert_id,
            attack_type=attack_type,
            threat_level=threat_level,
            timestamp=datetime.now(timezone.utc),
            description=description,
            affected_entities=affected_entities or [],
            evidence=evidence or {},
            recommended_actions=recommended_actions or [],
        )

        self.alerts.append(alert)
        self.active_threats[alert_id] = alert

        # Log the alert
        logger.warning(f"SECURITY ALERT [{threat_level.value.upper()}]: {description}")

        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    def get_active_threats(self) -> List[SecurityAlert]:
        """Get all currently active security threats."""
        return list(self.active_threats.values())

    def get_threat_summary(self) -> Dict[str, Any]:
        """Get a summary of current threat landscape."""
        threat_counts = defaultdict(int)
        severity_counts = defaultdict(int)

        for alert in self.active_threats.values():
            threat_counts[alert.attack_type.value] += 1
            severity_counts[alert.threat_level.value] += 1

        return {
            "active_threats": len(self.active_threats),
            "threat_breakdown": dict(threat_counts),
            "severity_breakdown": dict(severity_counts),
            "monitoring_active": self.monitoring_active,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def resolve_alert(self, alert_id: str, resolution_notes: str = ""):
        """Mark an alert as resolved."""
        if alert_id in self.active_threats:
            alert = self.active_threats[alert_id]
            alert.auto_mitigated = True
            del self.active_threats[alert_id]
            logger.info(f"Resolved security alert {alert_id}: {resolution_notes}")

    def get_historical_metrics(self, hours: int = 24) -> List[MetricSnapshot]:
        """Get historical metrics for the specified time period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [
            snapshot
            for snapshot in self.metric_history
            if snapshot.timestamp >= cutoff_time
        ]


# Global security monitor instance
security_monitor = EconomicSecurityMonitor()


async def start_security_monitoring():
    """Start the global security monitoring system."""
    await security_monitor.start_monitoring()


async def stop_security_monitoring():
    """Stop the global security monitoring system."""
    await security_monitor.stop_monitoring()


# Convenience functions for recording events
async def record_attribution_event(**kwargs):
    """Record an attribution event for monitoring."""
    await security_monitor.record_attribution_event(kwargs)


async def record_dividend_event(**kwargs):
    """Record a dividend event for monitoring."""
    await security_monitor.record_dividend_event(kwargs)


async def record_governance_event(**kwargs):
    """Record a governance event for monitoring."""
    await security_monitor.record_governance_event(kwargs)


async def record_payment_event(**kwargs):
    """Record a payment event for monitoring."""
    await security_monitor.record_payment_event(kwargs)


async def record_account_creation_event(**kwargs):
    """Record an account creation event for monitoring."""
    await security_monitor.record_account_creation_event(kwargs)
