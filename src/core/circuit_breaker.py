"""
Circuit Breaker Pattern Implementation

Provides protection against cascading failures when calling external services.
Implements the circuit breaker pattern with configurable failure thresholds,
timeout periods, and recovery mechanisms.

Key Features:
- Automatic failure detection and circuit opening
- Configurable failure thresholds and timeouts
- Half-open state for gradual recovery
- Metrics collection for monitoring
- Support for async operations
- Integration with structured logging
"""

import asyncio
import time
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar, Union
from dataclasses import dataclass
from functools import wraps

import structlog
from prometheus_client import Counter, Histogram, Gauge

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""

    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: float = 60.0  # Seconds before trying half-open
    request_timeout: float = 30.0  # Timeout for individual requests
    success_threshold: int = 3  # Successes needed to close from half-open
    monitor_window: float = 300.0  # Window for monitoring failures (seconds)
    max_retries: int = 3  # Maximum retry attempts


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""

    def __init__(self, service_name: str, state: CircuitState):
        self.service_name = service_name
        self.state = state
        super().__init__(f"Circuit breaker for {service_name} is {state.value}")


class CircuitBreaker:
    """
    Circuit breaker implementation with monitoring and metrics
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()

        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.last_request_time = 0.0

        # Metrics
        self._setup_metrics()

        # Lock for thread safety
        self._lock = asyncio.Lock()

        logger.info(
            "Circuit breaker initialized", name=name, config=self.config.__dict__
        )

    def _setup_metrics(self):
        """Setup Prometheus metrics"""
        self.metrics = {
            "requests_total": Counter(
                f"circuit_breaker_requests_total",
                "Total requests through circuit breaker",
                ["service", "state", "result"],
            ),
            "failures_total": Counter(
                f"circuit_breaker_failures_total",
                "Total failures",
                ["service", "error_type"],
            ),
            "state_changes_total": Counter(
                f"circuit_breaker_state_changes_total",
                "Circuit breaker state changes",
                ["service", "from_state", "to_state"],
            ),
            "request_duration": Histogram(
                f"circuit_breaker_request_duration_seconds",
                "Request duration through circuit breaker",
                ["service", "state"],
            ),
            "current_state": Gauge(
                f"circuit_breaker_current_state",
                "Current circuit breaker state (0=closed, 1=open, 2=half_open)",
                ["service"],
            ),
        }

        # Set initial state metric
        self._update_state_metric()

    def _update_state_metric(self):
        """Update the current state metric"""
        state_values = {
            CircuitState.CLOSED: 0,
            CircuitState.OPEN: 1,
            CircuitState.HALF_OPEN: 2,
        }
        self.metrics["current_state"].labels(service=self.name).set(
            state_values[self.state]
        )

    async def _change_state(self, new_state: CircuitState, reason: str = ""):
        """Change circuit breaker state with logging and metrics"""
        if new_state != self.state:
            old_state = self.state
            self.state = new_state

            # Update metrics
            self.metrics["state_changes_total"].labels(
                service=self.name, from_state=old_state.value, to_state=new_state.value
            ).inc()
            self._update_state_metric()

            # Log state change
            logger.info(
                "Circuit breaker state changed",
                service=self.name,
                old_state=old_state.value,
                new_state=new_state.value,
                reason=reason,
                failure_count=self.failure_count,
                success_count=self.success_count,
            )

            # Reset counters based on new state
            if new_state == CircuitState.HALF_OPEN:
                self.success_count = 0
            elif new_state == CircuitState.CLOSED:
                self.failure_count = 0
                self.success_count = 0

    async def _should_allow_request(self) -> bool:
        """Determine if request should be allowed based on current state"""
        current_time = time.time()

        if self.state == CircuitState.CLOSED:
            return True

        elif self.state == CircuitState.OPEN:
            # Check if enough time has passed to try recovery
            if current_time - self.last_failure_time >= self.config.recovery_timeout:
                await self._change_state(
                    CircuitState.HALF_OPEN, "Recovery timeout reached"
                )
                return True
            return False

        elif self.state == CircuitState.HALF_OPEN:
            # Allow limited requests to test recovery
            return True

        return False

    async def _on_success(self):
        """Handle successful request"""
        async with self._lock:
            self.metrics["requests_total"].labels(
                service=self.name, state=self.state.value, result="success"
            ).inc()

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    await self._change_state(
                        CircuitState.CLOSED,
                        f"Reached success threshold ({self.success_count})",
                    )
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0

    async def _on_failure(self, error: Exception):
        """Handle failed request"""
        async with self._lock:
            current_time = time.time()
            self.failure_count += 1
            self.last_failure_time = current_time

            # Update metrics
            self.metrics["requests_total"].labels(
                service=self.name, state=self.state.value, result="failure"
            ).inc()

            self.metrics["failures_total"].labels(
                service=self.name, error_type=type(error).__name__
            ).inc()

            # Determine if circuit should open
            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    await self._change_state(
                        CircuitState.OPEN,
                        f"Failure threshold reached ({self.failure_count})",
                    )
            elif self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open state goes back to open
                await self._change_state(
                    CircuitState.OPEN, "Failure during half-open state"
                )

    @asynccontextmanager
    async def call(self):
        """
        Context manager for making calls through the circuit breaker

        Usage:
            async with circuit_breaker.call() as cb:
                if cb.should_proceed:
                    result = await some_external_service()
                    cb.on_success(result)
                    return result
        """
        async with self._lock:
            should_allow = await self._should_allow_request()

        if not should_allow:
            raise CircuitBreakerError(self.name, self.state)

        start_time = time.time()
        call_context = CircuitBreakerCallContext(self, start_time)

        try:
            yield call_context

            # If we get here without exception, it's a success
            if not call_context._handled:
                await self._on_success()

        except Exception as e:
            if not call_context._handled:
                await self._on_failure(e)
            raise

        finally:
            # Record duration
            duration = time.time() - start_time
            self.metrics["request_duration"].labels(
                service=self.name, state=self.state.value
            ).observe(duration)

    async def call_async(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        """
        Call an async function through the circuit breaker
        """
        async with self.call() as cb:
            result = await func(*args, **kwargs)
            return result

    def get_stats(self) -> Dict[str, Any]:
        """Get current circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "config": self.config.__dict__,
        }


class CircuitBreakerCallContext:
    """Context for a single call through the circuit breaker"""

    def __init__(self, circuit_breaker: CircuitBreaker, start_time: float):
        self.circuit_breaker = circuit_breaker
        self.start_time = start_time
        self.should_proceed = True
        self._handled = False

    async def on_success(self, result: Any = None):
        """Mark the call as successful"""
        if not self._handled:
            await self.circuit_breaker._on_success()
            self._handled = True
        return result

    async def on_failure(self, error: Exception):
        """Mark the call as failed"""
        if not self._handled:
            await self.circuit_breaker._on_failure(error)
            self._handled = True


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers for different services
    """

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._default_config = CircuitBreakerConfig()

    def get_breaker(
        self, service_name: str, config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker for a service"""
        if service_name not in self._breakers:
            self._breakers[service_name] = CircuitBreaker(
                service_name, config or self._default_config
            )
        return self._breakers[service_name]

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}

    async def reset_breaker(self, service_name: str):
        """Reset a circuit breaker to closed state"""
        if service_name in self._breakers:
            breaker = self._breakers[service_name]
            async with breaker._lock:
                await breaker._change_state(CircuitState.CLOSED, "Manual reset")
                breaker.failure_count = 0
                breaker.success_count = 0


# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()


def circuit_breaker(service_name: str, config: Optional[CircuitBreakerConfig] = None):
    """
    Decorator for automatic circuit breaker protection

    Usage:
        @circuit_breaker("external_api")
        async def call_external_api():
            # This will be protected by circuit breaker
            pass
    """

    def decorator(func):
        breaker = circuit_breaker_manager.get_breaker(service_name, config)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call_async(func, *args, **kwargs)

        return wrapper

    return decorator


# Convenience function for common external services
def get_http_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get a circuit breaker configured for HTTP services"""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30.0,
        request_timeout=10.0,
        success_threshold=2,
    )
    return circuit_breaker_manager.get_breaker(service_name, config)


def get_database_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get a circuit breaker configured for database services"""
    config = CircuitBreakerConfig(
        failure_threshold=2,
        recovery_timeout=10.0,
        request_timeout=5.0,
        success_threshold=1,
    )
    return circuit_breaker_manager.get_breaker(service_name, config)
