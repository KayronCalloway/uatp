"""
Economic Circuit Breakers for UATP System.

This module implements automatic circuit breakers that halt economic operations
when attacks are detected, providing fail-safe mechanisms to protect the system
from financial exploitation and manipulation.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum, auto

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """States of economic circuit breakers."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit tripped, operations halted
    HALF_OPEN = "half_open"  # Testing if system is stable


class BreakCondition(Enum):
    """Conditions that can trigger circuit breakers."""

    HIGH_SIMILARITY_RATE = "high_similarity_rate"
    CONCENTRATION_VIOLATION = "concentration_violation"
    RAPID_ACCOUNT_CREATION = "rapid_account_creation"
    SUSPICIOUS_VOTING_PATTERN = "suspicious_voting_pattern"
    PAYMENT_ANOMALY = "payment_anomaly"
    GOVERNANCE_CAPTURE = "governance_capture"
    FLASH_LOAN_PATTERN = "flash_loan_pattern"
    SYSTEM_OVERLOAD = "system_overload"


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""

    name: str
    failure_threshold: int = 5  # Number of failures to trip
    time_window: timedelta = timedelta(minutes=5)  # Time window for counting failures
    recovery_time: timedelta = timedelta(minutes=30)  # Time before allowing half-open
    test_duration: timedelta = timedelta(minutes=5)  # Duration for half-open testing
    auto_reset: bool = True  # Whether to auto-reset after recovery


@dataclass
class CircuitBreakerState:
    """Current state of a circuit breaker."""

    circuit_id: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    trip_time: Optional[datetime] = None
    recovery_time: Optional[datetime] = None
    consecutive_successes: int = 0
    config: CircuitBreakerConfig = None
    blocked_operations: List[str] = field(default_factory=list)


class EconomicCircuitBreaker:
    """
    Individual circuit breaker for economic operations.

    Monitors operation success/failure rates and automatically trips
    when failure thresholds are exceeded, protecting the system from
    ongoing attacks or system failures.
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState(circuit_id=config.name, config=config)
        self.failure_history: deque = deque(maxlen=1000)
        self.success_history: deque = deque(maxlen=1000)
        self.callbacks: Dict[CircuitState, List[Callable]] = defaultdict(list)

    async def call(self, operation: Callable, *args, **kwargs):
        """
        Execute an operation through the circuit breaker.

        Args:
            operation: The function to execute
            *args, **kwargs: Arguments to pass to the operation

        Returns:
            Result of the operation if successful

        Raises:
            CircuitOpenException: If circuit is open
            Exception: Original exception from operation if it fails
        """
        current_time = datetime.now(timezone.utc)

        # Check if circuit should transition states
        await self._check_state_transitions(current_time)

        if self.state.state == CircuitState.OPEN:
            # Circuit is open, reject operation
            raise CircuitOpenException(
                f"Circuit breaker {self.config.name} is OPEN. "
                f"Next retry allowed at {self.state.recovery_time}"
            )

        try:
            # Execute the operation
            result = (
                await operation(*args, **kwargs)
                if asyncio.iscoroutinefunction(operation)
                else operation(*args, **kwargs)
            )

            # Record success
            await self._record_success(current_time)
            return result

        except Exception as e:
            # Record failure
            await self._record_failure(current_time, str(e))
            raise

    async def _record_success(self, timestamp: datetime):
        """Record a successful operation."""
        self.success_history.append(timestamp)
        self.state.consecutive_successes += 1

        # Reset failure count if in closed state
        if self.state.state == CircuitState.CLOSED:
            self.state.failure_count = 0

    async def _record_failure(self, timestamp: datetime, error: str):
        """Record a failed operation."""
        self.failure_history.append((timestamp, error))
        self.state.failure_count += 1
        self.state.last_failure_time = timestamp
        self.state.consecutive_successes = 0

        logger.warning(f"Circuit breaker {self.config.name} recorded failure: {error}")

        # Check if we should trip
        await self._evaluate_trip_condition(timestamp)

    async def _evaluate_trip_condition(self, current_time: datetime):
        """Evaluate if the circuit should trip based on recent failures."""
        if self.state.state != CircuitState.CLOSED:
            return

        # Count recent failures within the time window
        window_start = current_time - self.config.time_window
        recent_failures = [
            failure_time
            for failure_time, _ in self.failure_history
            if failure_time >= window_start
        ]

        if len(recent_failures) >= self.config.failure_threshold:
            await self._trip_circuit(current_time)

    async def _trip_circuit(self, current_time: datetime):
        """Trip the circuit breaker to OPEN state."""
        self.state.state = CircuitState.OPEN
        self.state.trip_time = current_time
        self.state.recovery_time = current_time + self.config.recovery_time

        logger.critical(
            f"CIRCUIT BREAKER TRIPPED: {self.config.name} - "
            f"Too many failures ({self.state.failure_count}) in time window. "
            f"Recovery time: {self.state.recovery_time}"
        )

        # Notify callbacks
        await self._notify_state_change(CircuitState.OPEN)

    async def _check_state_transitions(self, current_time: datetime):
        """Check if circuit should transition between states."""

        if self.state.state == CircuitState.OPEN:
            # Check if we can move to half-open
            if current_time >= self.state.recovery_time:
                await self._move_to_half_open(current_time)

        elif self.state.state == CircuitState.HALF_OPEN:
            # Check if we should close or re-open
            test_end_time = self.state.recovery_time + self.config.test_duration

            if current_time >= test_end_time:
                if (
                    self.state.consecutive_successes > 0
                    and self.state.failure_count == 0
                ):
                    await self._close_circuit(current_time)
                else:
                    # Re-trip if there were failures during test period
                    await self._trip_circuit(current_time)

    async def _move_to_half_open(self, current_time: datetime):
        """Move circuit to half-open state for testing."""
        self.state.state = CircuitState.HALF_OPEN
        self.state.failure_count = 0
        self.state.consecutive_successes = 0

        logger.info(
            f"Circuit breaker {self.config.name} moved to HALF_OPEN for testing"
        )
        await self._notify_state_change(CircuitState.HALF_OPEN)

    async def _close_circuit(self, current_time: datetime):
        """Move circuit back to closed state."""
        self.state.state = CircuitState.CLOSED
        self.state.failure_count = 0
        self.state.trip_time = None
        self.state.recovery_time = None

        logger.info(f"Circuit breaker {self.config.name} CLOSED - system recovered")
        await self._notify_state_change(CircuitState.CLOSED)

    async def _notify_state_change(self, new_state: CircuitState):
        """Notify registered callbacks of state changes."""
        for callback in self.callbacks[new_state]:
            try:
                await callback(self.state) if asyncio.iscoroutinefunction(
                    callback
                ) else callback(self.state)
            except Exception as e:
                logger.error(f"Circuit breaker callback error: {e}")

    def register_callback(self, state: CircuitState, callback: Callable):
        """Register a callback for state transitions."""
        self.callbacks[state].append(callback)

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the circuit breaker."""
        current_time = datetime.now(timezone.utc)

        # Calculate recent failure rate
        window_start = current_time - self.config.time_window
        recent_failures = len(
            [
                failure_time
                for failure_time, _ in self.failure_history
                if failure_time >= window_start
            ]
        )

        return {
            "circuit_id": self.state.circuit_id,
            "state": self.state.state.value,
            "failure_count": self.state.failure_count,
            "recent_failures": recent_failures,
            "consecutive_successes": self.state.consecutive_successes,
            "last_failure_time": self.state.last_failure_time.isoformat()
            if self.state.last_failure_time
            else None,
            "trip_time": self.state.trip_time.isoformat()
            if self.state.trip_time
            else None,
            "recovery_time": self.state.recovery_time.isoformat()
            if self.state.recovery_time
            else None,
            "time_until_recovery": str(self.state.recovery_time - current_time)
            if self.state.recovery_time and current_time < self.state.recovery_time
            else None,
        }


class CircuitOpenException(Exception):
    """Exception raised when a circuit breaker is open."""

    pass


class EconomicCircuitBreakerManager:
    """
    Manager for all economic circuit breakers in the UATP system.

    Coordinates multiple circuit breakers and provides system-wide
    protection against economic attacks and failures.
    """

    def __init__(self):
        self.circuit_breakers: Dict[str, EconomicCircuitBreaker] = {}
        self.global_emergency_state = False
        self.blocked_operations: Set[str] = set()
        self.operation_history: deque = deque(maxlen=10000)

        # Initialize standard circuit breakers
        self._initialize_standard_breakers()

    def _initialize_standard_breakers(self):
        """Initialize standard circuit breakers for UATP operations."""

        # Attribution system circuit breaker
        self.add_circuit_breaker(
            CircuitBreakerConfig(
                name="attribution_system",
                failure_threshold=10,
                time_window=timedelta(minutes=5),
                recovery_time=timedelta(minutes=15),
            )
        )

        # Dividend distribution circuit breaker
        self.add_circuit_breaker(
            CircuitBreakerConfig(
                name="dividend_distribution",
                failure_threshold=5,
                time_window=timedelta(minutes=10),
                recovery_time=timedelta(minutes=30),
            )
        )

        # Governance system circuit breaker
        self.add_circuit_breaker(
            CircuitBreakerConfig(
                name="governance_system",
                failure_threshold=3,
                time_window=timedelta(minutes=15),
                recovery_time=timedelta(hours=1),
            )
        )

        # Payment processing circuit breaker
        self.add_circuit_breaker(
            CircuitBreakerConfig(
                name="payment_processing",
                failure_threshold=5,
                time_window=timedelta(minutes=5),
                recovery_time=timedelta(minutes=20),
            )
        )

        # Account creation circuit breaker
        self.add_circuit_breaker(
            CircuitBreakerConfig(
                name="account_creation",
                failure_threshold=20,
                time_window=timedelta(minutes=10),
                recovery_time=timedelta(minutes=30),
            )
        )

        # High-value operation circuit breaker
        self.add_circuit_breaker(
            CircuitBreakerConfig(
                name="high_value_operations",
                failure_threshold=2,
                time_window=timedelta(minutes=5),
                recovery_time=timedelta(hours=2),
            )
        )

    def add_circuit_breaker(self, config: CircuitBreakerConfig):
        """Add a new circuit breaker with the given configuration."""
        breaker = EconomicCircuitBreaker(config)
        self.circuit_breakers[config.name] = breaker

        # Register emergency callbacks
        breaker.register_callback(CircuitState.OPEN, self._handle_circuit_open)
        breaker.register_callback(CircuitState.CLOSED, self._handle_circuit_closed)

        logger.info(f"Added circuit breaker: {config.name}")

    async def _handle_circuit_open(self, state: CircuitBreakerState):
        """Handle when a circuit breaker opens."""
        # Add to blocked operations
        self.blocked_operations.add(state.circuit_id)

        # Check if we should trigger global emergency
        open_critical_circuits = [
            name
            for name, breaker in self.circuit_breakers.items()
            if breaker.state.state == CircuitState.OPEN
            and name
            in {"governance_system", "high_value_operations", "payment_processing"}
        ]

        if len(open_critical_circuits) >= 2:
            await self._trigger_global_emergency()

    async def _handle_circuit_closed(self, state: CircuitBreakerState):
        """Handle when a circuit breaker closes."""
        # Remove from blocked operations
        self.blocked_operations.discard(state.circuit_id)

        # Check if we can exit global emergency
        if self.global_emergency_state:
            open_circuits = [
                name
                for name, breaker in self.circuit_breakers.items()
                if breaker.state.state == CircuitState.OPEN
            ]

            if len(open_circuits) == 0:
                await self._exit_global_emergency()

    async def _trigger_global_emergency(self):
        """Trigger global emergency mode - halt all high-risk operations."""
        if self.global_emergency_state:
            return

        self.global_emergency_state = True

        logger.critical(
            "GLOBAL ECONOMIC EMERGENCY TRIGGERED - Multiple critical circuit breakers open. "
            "Halting all high-risk economic operations."
        )

        # Force trip additional protective circuits
        for name in ["dividend_distribution", "account_creation"]:
            if name in self.circuit_breakers:
                breaker = self.circuit_breakers[name]
                if breaker.state.state == CircuitState.CLOSED:
                    await breaker._trip_circuit(datetime.now(timezone.utc))

        # Block critical operations globally
        self.blocked_operations.update(
            [
                "large_dividend_distributions",
                "governance_proposals",
                "high_value_payments",
                "new_account_creation",
                "stake_modifications",
            ]
        )

    async def _exit_global_emergency(self):
        """Exit global emergency mode."""
        self.global_emergency_state = False
        logger.info("Exiting global economic emergency mode - all circuits recovered")

    async def execute_protected_operation(
        self, circuit_name: str, operation: Callable, *args, **kwargs
    ):
        """
        Execute an operation through the specified circuit breaker.

        Args:
            circuit_name: Name of the circuit breaker to use
            operation: The operation to execute
            *args, **kwargs: Arguments for the operation

        Returns:
            Result of the operation

        Raises:
            CircuitOpenException: If circuit is open
            ValueError: If circuit breaker doesn't exist
        """
        if circuit_name not in self.circuit_breakers:
            raise ValueError(f"Circuit breaker '{circuit_name}' not found")

        # Check global emergency state
        if self.global_emergency_state and circuit_name in {
            "governance_system",
            "dividend_distribution",
            "high_value_operations",
        }:
            raise CircuitOpenException(
                "Global economic emergency active - critical operations blocked"
            )

        breaker = self.circuit_breakers[circuit_name]

        # Record operation attempt
        self.operation_history.append(
            {
                "timestamp": datetime.now(timezone.utc),
                "circuit": circuit_name,
                "operation": operation.__name__
                if hasattr(operation, "__name__")
                else str(operation),
            }
        )

        return await breaker.call(operation, *args, **kwargs)

    def is_operation_blocked(self, operation_type: str) -> bool:
        """Check if an operation type is currently blocked."""
        return operation_type in self.blocked_operations or self.global_emergency_state

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all circuit breakers."""
        circuit_statuses = {}
        for name, breaker in self.circuit_breakers.items():
            circuit_statuses[name] = breaker.get_status()

        # Calculate system health metrics
        total_circuits = len(self.circuit_breakers)
        open_circuits = sum(
            1
            for breaker in self.circuit_breakers.values()
            if breaker.state.state == CircuitState.OPEN
        )

        system_health = "healthy"
        if open_circuits > 0:
            if self.global_emergency_state:
                system_health = "emergency"
            elif open_circuits >= total_circuits * 0.5:
                system_health = "degraded"
            else:
                system_health = "impaired"

        return {
            "system_health": system_health,
            "global_emergency": self.global_emergency_state,
            "total_circuits": total_circuits,
            "open_circuits": open_circuits,
            "blocked_operations": list(self.blocked_operations),
            "circuit_details": circuit_statuses,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    def get_operation_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get operation statistics for the specified time period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        recent_operations = [
            op for op in self.operation_history if op["timestamp"] >= cutoff_time
        ]

        # Count operations by circuit
        circuit_counts = defaultdict(int)
        for op in recent_operations:
            circuit_counts[op["circuit"]] += 1

        return {
            "total_operations": len(recent_operations),
            "operations_by_circuit": dict(circuit_counts),
            "time_period_hours": hours,
            "average_operations_per_hour": len(recent_operations) / max(hours, 1),
        }

    async def force_reset_circuit(self, circuit_name: str, reason: str = ""):
        """Force reset a circuit breaker (emergency use only)."""
        if circuit_name not in self.circuit_breakers:
            raise ValueError(f"Circuit breaker '{circuit_name}' not found")

        breaker = self.circuit_breakers[circuit_name]
        await breaker._close_circuit(datetime.now(timezone.utc))

        logger.warning(
            f"FORCED RESET of circuit breaker {circuit_name}. Reason: {reason}"
        )

    async def emergency_shutdown(self, reason: str):
        """Emergency shutdown of all economic operations."""
        logger.critical(f"EMERGENCY SHUTDOWN initiated: {reason}")

        # Trip all circuit breakers
        current_time = datetime.now(timezone.utc)
        for breaker in self.circuit_breakers.values():
            if breaker.state.state != CircuitState.OPEN:
                await breaker._trip_circuit(current_time)

        # Activate global emergency
        await self._trigger_global_emergency()

        # Block all operations
        self.blocked_operations.update(
            [
                "all_economic_operations",
                "attribution_processing",
                "dividend_distribution",
                "governance_operations",
                "payment_processing",
                "account_management",
            ]
        )


# Global circuit breaker manager
circuit_breaker_manager = EconomicCircuitBreakerManager()


# Convenience functions for protected operations
async def execute_attribution_operation(operation: Callable, *args, **kwargs):
    """Execute an attribution operation with circuit breaker protection."""
    return await circuit_breaker_manager.execute_protected_operation(
        "attribution_system", operation, *args, **kwargs
    )


async def execute_dividend_operation(operation: Callable, *args, **kwargs):
    """Execute a dividend operation with circuit breaker protection."""
    return await circuit_breaker_manager.execute_protected_operation(
        "dividend_distribution", operation, *args, **kwargs
    )


async def execute_governance_operation(operation: Callable, *args, **kwargs):
    """Execute a governance operation with circuit breaker protection."""
    return await circuit_breaker_manager.execute_protected_operation(
        "governance_system", operation, *args, **kwargs
    )


async def execute_payment_operation(operation: Callable, *args, **kwargs):
    """Execute a payment operation with circuit breaker protection."""
    return await circuit_breaker_manager.execute_protected_operation(
        "payment_processing", operation, *args, **kwargs
    )


async def execute_high_value_operation(operation: Callable, *args, **kwargs):
    """Execute a high-value operation with circuit breaker protection."""
    return await circuit_breaker_manager.execute_protected_operation(
        "high_value_operations", operation, *args, **kwargs
    )


def is_system_healthy() -> bool:
    """Check if the economic system is healthy (no circuit breakers open)."""
    status = circuit_breaker_manager.get_system_status()
    return status["system_health"] == "healthy"


def get_blocked_operations() -> List[str]:
    """Get list of currently blocked operations."""
    return list(circuit_breaker_manager.blocked_operations)
