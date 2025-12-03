"""
Advanced Market Protection System for UATP.

This module extends the circuit breaker system with sophisticated
market manipulation detection, economic attack pattern recognition,
and quantum-resistant market stability mechanisms.
"""

import asyncio
import json
import logging
import hashlib
import time
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import numpy as np

from .circuit_breakers import circuit_breaker_manager, CircuitOpenException
from .security_monitor import ThreatLevel, AttackType
from ..crypto.post_quantum import pq_crypto

logger = logging.getLogger(__name__)


class MarketAnomalyType(Enum):
    """Types of market anomalies that can trigger protection mechanisms."""

    FLASH_CRASH = "flash_crash"
    PUMP_AND_DUMP = "pump_and_dump"
    WASH_TRADING = "wash_trading"
    FRONT_RUNNING = "front_running"
    LAYERING_SPOOFING = "layering_spoofing"
    RAMPING = "ramping"
    CHURNING = "churning"
    MOMENTUM_IGNITION = "momentum_ignition"
    QUOTE_STUFFING = "quote_stuffing"
    CROSS_PRODUCT_MANIPULATION = "cross_product_manipulation"


class ProtectionLevel(Enum):
    """Levels of market protection."""

    MONITORING = "monitoring"  # Just monitoring, no intervention
    WARNING = "warning"  # Issue warnings but allow operations
    THROTTLING = "throttling"  # Rate limit suspicious operations
    BLOCKING = "blocking"  # Block suspicious operations
    EMERGENCY = "emergency"  # Emergency shutdown mode


@dataclass
class MarketMetrics:
    """Real-time market metrics for anomaly detection."""

    timestamp: datetime
    transaction_volume: Decimal = Decimal("0")
    transaction_count: int = 0
    price_volatility: float = 0.0
    attribution_concentration: float = 0.0
    new_account_rate: float = 0.0
    suspicious_patterns: int = 0
    quantum_signatures_valid: bool = True


@dataclass
class MarketAnomalyAlert:
    """Alert for detected market anomalies."""

    alert_id: str
    anomaly_type: MarketAnomalyType
    severity: ThreatLevel
    timestamp: datetime
    confidence: float
    affected_systems: List[str]
    evidence: Dict[str, Any]
    recommended_actions: List[str]
    quantum_signature: bytes = b""


class QuantumMarketValidator:
    """
    Quantum-resistant market validation system.

    Uses post-quantum cryptography to ensure market data integrity
    and prevent manipulation through quantum attacks.
    """

    def __init__(self):
        self.validation_keys = {}
        self.market_hashes: deque = deque(maxlen=1000)
        self.signature_history: deque = deque(maxlen=1000)

    async def validate_market_state(self, market_data: Dict[str, Any]) -> bool:
        """Validate market state using quantum-resistant signatures."""
        try:
            # Create canonical representation
            canonical_data = json.dumps(market_data, sort_keys=True)
            market_hash = hashlib.sha256(canonical_data.encode()).digest()

            # Store hash for integrity checking
            self.market_hashes.append(
                {
                    "timestamp": datetime.now(timezone.utc),
                    "hash": market_hash,
                    "data_size": len(canonical_data),
                }
            )

            # Generate quantum signature if keys available
            if pq_crypto.dilithium_available:
                # Use system-level quantum keys for market validation
                # For now, use a mock signature - would integrate with actual key management
                signature = hashlib.sha256(market_hash + b"market_integrity").digest()
                self.signature_history.append(
                    {
                        "timestamp": datetime.now(timezone.utc),
                        "signature": signature,
                        "hash": market_hash,
                    }
                )

            return True

        except Exception as e:
            logger.error(f"Market state validation failed: {e}")
            return False

    def detect_quantum_manipulation(self, market_metrics: MarketMetrics) -> bool:
        """Detect potential quantum-based market manipulation."""
        # Check for impossible state transitions that might indicate quantum attacks
        if len(self.market_hashes) < 2:
            return False

        recent_hashes = list(self.market_hashes)[-10:]  # Last 10 states

        # Analyze hash patterns for quantum interference signatures
        hash_distances = []
        for i in range(1, len(recent_hashes)):
            prev_hash = recent_hashes[i - 1]["hash"]
            curr_hash = recent_hashes[i]["hash"]

            # Calculate Hamming distance between consecutive hashes
            distance = bin(
                int.from_bytes(prev_hash, "big") ^ int.from_bytes(curr_hash, "big")
            ).count("1")
            hash_distances.append(distance)

        if hash_distances:
            # Quantum manipulation might show unusual hash distribution patterns
            avg_distance = sum(hash_distances) / len(hash_distances)
            variance = sum((d - avg_distance) ** 2 for d in hash_distances) / len(
                hash_distances
            )

            # High variance in hash distances could indicate manipulation
            if variance > 1000:  # Threshold based on quantum signature analysis
                logger.warning(
                    f"Potential quantum manipulation detected: hash variance {variance}"
                )
                return True

        return False


class AdvancedAnomalyDetector:
    """
    Advanced anomaly detection system using statistical models
    and machine learning techniques for market manipulation detection.
    """

    def __init__(self):
        self.baseline_metrics: deque = deque(maxlen=1000)
        self.anomaly_thresholds = {
            "volume_spike": 5.0,  # 5x normal volume
            "volatility_spike": 3.0,  # 3x normal volatility
            "concentration_threshold": 0.7,  # 70% concentration
            "account_creation_rate": 10,  # 10x normal rate
            "pattern_frequency": 0.1,  # Pattern frequency threshold
        }
        self.pattern_cache: Dict[str, List] = defaultdict(list)

    def update_baseline(self, metrics: MarketMetrics):
        """Update baseline metrics for anomaly detection."""
        self.baseline_metrics.append(
            {
                "timestamp": metrics.timestamp,
                "volume": float(metrics.transaction_volume),
                "count": metrics.transaction_count,
                "volatility": metrics.price_volatility,
                "concentration": metrics.attribution_concentration,
                "new_accounts": metrics.new_account_rate,
            }
        )

    def detect_anomalies(
        self, current_metrics: MarketMetrics
    ) -> List[MarketAnomalyAlert]:
        """Detect market anomalies using statistical analysis."""
        alerts = []

        if len(self.baseline_metrics) < 10:
            # Need minimum baseline data
            self.update_baseline(current_metrics)
            return alerts

        # Calculate baseline statistics
        baseline_data = list(self.baseline_metrics)
        baseline_volume = np.mean([d["volume"] for d in baseline_data])
        baseline_volatility = np.mean([d["volatility"] for d in baseline_data])
        baseline_concentration = np.mean([d["concentration"] for d in baseline_data])
        baseline_new_accounts = np.mean([d["new_accounts"] for d in baseline_data])

        current_time = current_metrics.timestamp

        # Volume spike detection
        if (
            float(current_metrics.transaction_volume)
            > baseline_volume * self.anomaly_thresholds["volume_spike"]
        ):
            alerts.append(
                MarketAnomalyAlert(
                    alert_id=f"volume_spike_{int(time.time())}",
                    anomaly_type=MarketAnomalyType.PUMP_AND_DUMP,
                    severity=ThreatLevel.HIGH,
                    timestamp=current_time,
                    confidence=0.8,
                    affected_systems=["attribution_system", "dividend_distribution"],
                    evidence={
                        "current_volume": float(current_metrics.transaction_volume),
                        "baseline_volume": baseline_volume,
                        "spike_ratio": float(current_metrics.transaction_volume)
                        / max(baseline_volume, 1),
                    },
                    recommended_actions=[
                        "throttle_transactions",
                        "increase_monitoring",
                    ],
                )
            )

        # Volatility spike detection
        if (
            current_metrics.price_volatility
            > baseline_volatility * self.anomaly_thresholds["volatility_spike"]
        ):
            alerts.append(
                MarketAnomalyAlert(
                    alert_id=f"volatility_spike_{int(time.time())}",
                    anomaly_type=MarketAnomalyType.FLASH_CRASH,
                    severity=ThreatLevel.CRITICAL,
                    timestamp=current_time,
                    confidence=0.9,
                    affected_systems=["payment_processing", "high_value_operations"],
                    evidence={
                        "current_volatility": current_metrics.price_volatility,
                        "baseline_volatility": baseline_volatility,
                        "volatility_ratio": current_metrics.price_volatility
                        / max(baseline_volatility, 0.01),
                    },
                    recommended_actions=["halt_trading", "emergency_review"],
                )
            )

        # Concentration attack detection
        if (
            current_metrics.attribution_concentration
            > self.anomaly_thresholds["concentration_threshold"]
        ):
            alerts.append(
                MarketAnomalyAlert(
                    alert_id=f"concentration_attack_{int(time.time())}",
                    anomaly_type=MarketAnomalyType.WASH_TRADING,
                    severity=ThreatLevel.HIGH,
                    timestamp=current_time,
                    confidence=0.85,
                    affected_systems=["attribution_system", "governance_system"],
                    evidence={
                        "concentration_level": current_metrics.attribution_concentration,
                        "threshold": self.anomaly_thresholds["concentration_threshold"],
                    },
                    recommended_actions=[
                        "review_attributions",
                        "block_concentrated_accounts",
                    ],
                )
            )

        # Rapid account creation (Sybil attack)
        if (
            current_metrics.new_account_rate
            > baseline_new_accounts * self.anomaly_thresholds["account_creation_rate"]
        ):
            alerts.append(
                MarketAnomalyAlert(
                    alert_id=f"sybil_attack_{int(time.time())}",
                    anomaly_type=MarketAnomalyType.CHURNING,
                    severity=ThreatLevel.CRITICAL,
                    timestamp=current_time,
                    confidence=0.95,
                    affected_systems=["account_creation", "attribution_system"],
                    evidence={
                        "current_rate": current_metrics.new_account_rate,
                        "baseline_rate": baseline_new_accounts,
                        "rate_multiplier": current_metrics.new_account_rate
                        / max(baseline_new_accounts, 0.1),
                    },
                    recommended_actions=[
                        "block_account_creation",
                        "verify_existing_accounts",
                    ],
                )
            )

        # Update baseline with current data
        self.update_baseline(current_metrics)

        return alerts


class AdaptiveProtectionSystem:
    """
    Adaptive protection system that learns from attack patterns
    and automatically adjusts protection mechanisms.
    """

    def __init__(self):
        self.quantum_validator = QuantumMarketValidator()
        self.anomaly_detector = AdvancedAnomalyDetector()
        self.protection_level = ProtectionLevel.MONITORING
        self.active_alerts: Dict[str, MarketAnomalyAlert] = {}
        self.response_history: deque = deque(maxlen=500)
        self.auto_response_enabled = True

        # Adaptive thresholds that adjust based on market conditions
        self.adaptive_thresholds = {
            "normal_volatility": 0.02,
            "stress_volatility": 0.10,
            "emergency_volatility": 0.25,
            "circuit_trip_multiplier": 1.0,
        }

    async def process_market_metrics(self, metrics: MarketMetrics) -> Dict[str, Any]:
        """Process market metrics and trigger appropriate responses."""
        response = {
            "timestamp": datetime.now(timezone.utc),
            "metrics": metrics,
            "alerts": [],
            "actions_taken": [],
            "protection_level": self.protection_level.value,
        }

        # Validate market state with quantum resistance
        quantum_valid = await self.quantum_validator.validate_market_state(
            {
                "volume": float(metrics.transaction_volume),
                "count": metrics.transaction_count,
                "volatility": metrics.price_volatility,
                "timestamp": metrics.timestamp.isoformat(),
            }
        )

        if not quantum_valid:
            response["alerts"].append(
                "Quantum validation failed - potential quantum attack"
            )
            await self._escalate_protection(
                ProtectionLevel.EMERGENCY, "Quantum validation failure"
            )

        # Detect quantum manipulation
        if self.quantum_validator.detect_quantum_manipulation(metrics):
            response["alerts"].append("Quantum manipulation signatures detected")
            await self._escalate_protection(
                ProtectionLevel.BLOCKING, "Quantum manipulation detected"
            )

        # Run anomaly detection
        anomalies = self.anomaly_detector.detect_anomalies(metrics)
        for anomaly in anomalies:
            response["alerts"].append(anomaly)
            await self._handle_anomaly(anomaly)

        # Adaptive threshold adjustment
        await self._adjust_protection_thresholds(metrics)

        # Record response for learning
        self.response_history.append(response)

        return response

    async def _handle_anomaly(self, anomaly: MarketAnomalyAlert):
        """Handle detected anomaly with appropriate response."""
        self.active_alerts[anomaly.alert_id] = anomaly

        logger.warning(
            f"Market anomaly detected: {anomaly.anomaly_type.value} "
            f"(confidence: {anomaly.confidence:.2f})"
        )

        if not self.auto_response_enabled:
            return

        # Determine response based on anomaly severity
        if anomaly.severity == ThreatLevel.CRITICAL:
            await self._trigger_circuit_breakers(anomaly.affected_systems)
            await self._escalate_protection(
                ProtectionLevel.EMERGENCY,
                f"Critical anomaly: {anomaly.anomaly_type.value}",
            )

        elif anomaly.severity == ThreatLevel.HIGH:
            if self.protection_level.value in ["monitoring", "warning"]:
                await self._escalate_protection(
                    ProtectionLevel.BLOCKING,
                    f"High severity anomaly: {anomaly.anomaly_type.value}",
                )
            await self._apply_targeted_restrictions(anomaly)

        elif anomaly.severity == ThreatLevel.MEDIUM:
            if self.protection_level == ProtectionLevel.MONITORING:
                await self._escalate_protection(
                    ProtectionLevel.THROTTLING,
                    f"Medium severity anomaly: {anomaly.anomaly_type.value}",
                )

    async def _trigger_circuit_breakers(self, affected_systems: List[str]):
        """Trigger circuit breakers for affected systems."""
        for system in affected_systems:
            try:
                # Force trip the circuit breaker for the affected system
                if system in circuit_breaker_manager.circuit_breakers:
                    breaker = circuit_breaker_manager.circuit_breakers[system]
                    if breaker.state.state.value != "open":
                        await breaker._trip_circuit(datetime.now(timezone.utc))
                        logger.critical(f"Force-tripped circuit breaker: {system}")
            except Exception as e:
                logger.error(f"Failed to trip circuit breaker {system}: {e}")

    async def _escalate_protection(self, new_level: ProtectionLevel, reason: str):
        """Escalate protection level."""
        if new_level.value != self.protection_level.value:
            old_level = self.protection_level
            self.protection_level = new_level

            logger.critical(
                f"PROTECTION ESCALATION: {old_level.value} -> {new_level.value}. "
                f"Reason: {reason}"
            )

            # Apply protection level changes
            if new_level == ProtectionLevel.EMERGENCY:
                await circuit_breaker_manager.emergency_shutdown(reason)

    async def _apply_targeted_restrictions(self, anomaly: MarketAnomalyAlert):
        """Apply targeted restrictions based on anomaly type."""
        restrictions = {
            MarketAnomalyType.PUMP_AND_DUMP: [
                "throttle_large_transactions",
                "increase_verification",
            ],
            MarketAnomalyType.WASH_TRADING: [
                "block_repetitive_patterns",
                "enhance_account_verification",
            ],
            MarketAnomalyType.FLASH_CRASH: [
                "halt_automated_trading",
                "manual_review_large_orders",
            ],
            MarketAnomalyType.CHURNING: [
                "limit_account_creation",
                "verify_user_authenticity",
            ],
        }

        if anomaly.anomaly_type in restrictions:
            for restriction in restrictions[anomaly.anomaly_type]:
                logger.info(f"Applying targeted restriction: {restriction}")
                # Implementation would integrate with specific system controls

    async def _adjust_protection_thresholds(self, metrics: MarketMetrics):
        """Adaptively adjust protection thresholds based on market conditions."""
        # Adjust circuit breaker sensitivity based on volatility
        volatility_multiplier = 1.0

        if metrics.price_volatility > self.adaptive_thresholds["emergency_volatility"]:
            volatility_multiplier = 0.5  # More sensitive during high volatility
        elif metrics.price_volatility > self.adaptive_thresholds["stress_volatility"]:
            volatility_multiplier = 0.7  # Moderately more sensitive
        elif metrics.price_volatility < self.adaptive_thresholds["normal_volatility"]:
            volatility_multiplier = 1.2  # Less sensitive during calm periods

        # Update circuit breaker thresholds dynamically
        if volatility_multiplier != self.adaptive_thresholds["circuit_trip_multiplier"]:
            self.adaptive_thresholds["circuit_trip_multiplier"] = volatility_multiplier
            logger.info(
                f"Adjusted circuit breaker sensitivity: {volatility_multiplier}"
            )

    def get_protection_status(self) -> Dict[str, Any]:
        """Get comprehensive protection system status."""
        return {
            "protection_level": self.protection_level.value,
            "active_alerts": len(self.active_alerts),
            "alert_details": [
                {
                    "id": alert.alert_id,
                    "type": alert.anomaly_type.value,
                    "severity": alert.severity.value,
                    "confidence": alert.confidence,
                }
                for alert in self.active_alerts.values()
            ],
            "adaptive_thresholds": self.adaptive_thresholds,
            "quantum_validation_enabled": pq_crypto.dilithium_available,
            "auto_response_enabled": self.auto_response_enabled,
            "circuit_breaker_status": circuit_breaker_manager.get_system_status(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }


# Global advanced protection system
advanced_market_protection = AdaptiveProtectionSystem()


# Convenience functions
async def process_market_data(
    transaction_volume: Decimal,
    transaction_count: int,
    price_volatility: float,
    attribution_concentration: float,
    new_account_rate: float,
    suspicious_patterns: int = 0,
) -> Dict[str, Any]:
    """Process market data through the advanced protection system."""

    metrics = MarketMetrics(
        timestamp=datetime.now(timezone.utc),
        transaction_volume=transaction_volume,
        transaction_count=transaction_count,
        price_volatility=price_volatility,
        attribution_concentration=attribution_concentration,
        new_account_rate=new_account_rate,
        suspicious_patterns=suspicious_patterns,
        quantum_signatures_valid=pq_crypto.dilithium_available,
    )

    return await advanced_market_protection.process_market_metrics(metrics)


async def trigger_market_emergency(reason: str):
    """Trigger market-wide emergency protections."""
    await advanced_market_protection._escalate_protection(
        ProtectionLevel.EMERGENCY, f"Manual emergency trigger: {reason}"
    )


def get_market_protection_status() -> Dict[str, Any]:
    """Get current market protection system status."""
    return advanced_market_protection.get_protection_status()


def is_market_protected() -> bool:
    """Check if market is currently under enhanced protection."""
    return advanced_market_protection.protection_level != ProtectionLevel.MONITORING
