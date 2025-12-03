"""
Circuit Breaker Pattern Implementation for UATP

Provides resilience patterns for external service calls including:
- Circuit breaker to prevent cascading failures
- Exponential backoff retry logic
- Graceful degradation strategies
- Health monitoring for external dependencies
"""

import asyncio
import time
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, Union

import structlog
from tenacity import (
    AsyncRetrying,
    RetryError,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""

    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: int = 60  # Seconds before trying to close
    success_threshold: int = 3  # Successes needed to close from half-open
    timeout: int = 30  # Request timeout in seconds
    retry_attempts: int = 3  # Number of retry attempts
    retry_min_wait: int = 1  # Minimum wait between retries (seconds)
    retry_max_wait: int = 10  # Maximum wait between retries (seconds)


class CircuitBreakerError(Exception):
    """Circuit breaker is open"""

    pass


class ExternalServiceError(Exception):
    """External service error"""

    pass


class CircuitBreaker:
    """Circuit breaker implementation with async support"""

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0
        self._next_attempt_time = 0

        self.logger = logger.bind(circuit_breaker=name)

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed"""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open"""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open"""
        return self._state == CircuitState.HALF_OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        return (
            self._state == CircuitState.OPEN and time.time() >= self._next_attempt_time
        )

    def _record_success(self):
        """Record a successful call"""
        self._failure_count = 0

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._close_circuit()
        elif self._state == CircuitState.OPEN:
            self._state = CircuitState.HALF_OPEN
            self._success_count = 1
            self.logger.info("Circuit breaker transitioned to half-open")

    def _record_failure(self):
        """Record a failed call"""
        self._failure_count += 1
        self._last_failure_time = time.time()
        self._success_count = 0

        if self._state == CircuitState.HALF_OPEN:
            self._open_circuit()
        elif (
            self._state == CircuitState.CLOSED
            and self._failure_count >= self.config.failure_threshold
        ):
            self._open_circuit()

    def _open_circuit(self):
        """Open the circuit"""
        self._state = CircuitState.OPEN
        self._next_attempt_time = time.time() + self.config.recovery_timeout

        self.logger.warning(
            "Circuit breaker opened",
            failure_count=self._failure_count,
            recovery_timeout=self.config.recovery_timeout,
        )

    def _close_circuit(self):
        """Close the circuit"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0

        self.logger.info("Circuit breaker closed")

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute a function with circuit breaker protection"""

        # Check if circuit is open
        if self._state == CircuitState.OPEN:
            if not self._should_attempt_reset():
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is open. "
                    f"Next attempt allowed at {self._next_attempt_time}"
                )
            else:
                self._state = CircuitState.HALF_OPEN
                self.logger.info(
                    "Circuit breaker transitioned to half-open for testing"
                )

        try:
            # Execute with timeout and retry logic
            result = await self._execute_with_retry(func, *args, **kwargs)
            self._record_success()
            return result

        except Exception as e:
            self._record_failure()
            self.logger.error(
                "Circuit breaker call failed",
                error=str(e),
                failure_count=self._failure_count,
                state=self._state.value,
            )
            raise

    async def _execute_with_retry(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with retry logic"""

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.config.retry_attempts),
            wait=wait_exponential(
                multiplier=1,
                min=self.config.retry_min_wait,
                max=self.config.retry_max_wait,
            ),
            retry=retry_if_exception_type(
                (
                    ExternalServiceError,
                    asyncio.TimeoutError,
                    ConnectionError,
                )
            ),
        ):
            with attempt:
                try:
                    # Apply timeout
                    result = await asyncio.wait_for(
                        func(*args, **kwargs), timeout=self.config.timeout
                    )
                    return result

                except asyncio.TimeoutError as e:
                    self.logger.warning(
                        "Function call timed out",
                        timeout=self.config.timeout,
                        attempt=attempt.retry_state.attempt_number,
                    )
                    raise ExternalServiceError(
                        f"Call timed out after {self.config.timeout}s"
                    ) from e

                except Exception as e:
                    self.logger.warning(
                        "Function call failed",
                        error=str(e),
                        attempt=attempt.retry_state.attempt_number,
                    )
                    # Re-raise as ExternalServiceError if it's a recoverable error
                    if self._is_recoverable_error(e):
                        raise ExternalServiceError(str(e)) from e
                    else:
                        # Non-recoverable errors should fail immediately
                        raise

        # This should never be reached due to tenacity behavior
        raise ExternalServiceError("Maximum retry attempts exceeded")

    def _is_recoverable_error(self, error: Exception) -> bool:
        """Determine if an error is recoverable and should be retried"""
        recoverable_errors = (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        )

        # Check for HTTP errors that might be recoverable
        if hasattr(error, "status_code"):
            # Server errors are typically recoverable
            if 500 <= error.status_code < 600:
                return True
            # Rate limiting might be recoverable
            if error.status_code == 429:
                return True
            # Client errors are typically not recoverable
            if 400 <= error.status_code < 500:
                return False

        return isinstance(error, recoverable_errors)

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "next_attempt_time": self._next_attempt_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
            },
        }


class ExternalServiceClient(ABC):
    """Abstract base class for external service clients with circuit breaker"""

    def __init__(self, service_name: str, config: CircuitBreakerConfig = None):
        self.service_name = service_name
        self.circuit_breaker = CircuitBreaker(service_name, config)
        self.logger = logger.bind(service=service_name)

    @abstractmethod
    async def _make_request(self, *args, **kwargs) -> Any:
        """Make the actual request to external service"""
        pass

    async def call(self, *args, **kwargs) -> Any:
        """Make a call with circuit breaker protection"""
        return await self.circuit_breaker.call(self._make_request, *args, **kwargs)

    @asynccontextmanager
    async def graceful_degradation(self, fallback_value: Any = None):
        """Context manager for graceful degradation"""
        try:
            yield self
        except (CircuitBreakerError, ExternalServiceError) as e:
            self.logger.warning(
                "External service unavailable, using fallback",
                error=str(e),
                fallback_value=fallback_value,
            )
            yield _FallbackClient(fallback_value)

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the external service"""
        stats = self.circuit_breaker.get_stats()

        # Determine health based on circuit state
        if stats["state"] == CircuitState.CLOSED.value:
            health = "healthy"
        elif stats["state"] == CircuitState.HALF_OPEN.value:
            health = "degraded"
        else:
            health = "unhealthy"

        return {
            "service": self.service_name,
            "health": health,
            "circuit_breaker": stats,
        }


class _FallbackClient:
    """Fallback client that returns predefined values"""

    def __init__(self, fallback_value: Any):
        self.fallback_value = fallback_value

    async def _make_request(self, *args, **kwargs) -> Any:
        return self.fallback_value

    async def call(self, *args, **kwargs) -> Any:
        return self.fallback_value


# Circuit breaker registry for managing multiple circuits
class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""

    def __init__(self):
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.logger = logger.bind(component="circuit_breaker_registry")

    def get_or_create(
        self, name: str, config: CircuitBreakerConfig = None
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one"""
        if name not in self._circuit_breakers:
            self._circuit_breakers[name] = CircuitBreaker(name, config)
            self.logger.info("Created new circuit breaker", name=name)

        return self._circuit_breakers[name]

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {name: cb.get_stats() for name, cb in self._circuit_breakers.items()}

    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        all_stats = self.get_all_stats()

        healthy_count = sum(
            1
            for stats in all_stats.values()
            if stats["state"] == CircuitState.CLOSED.value
        )

        degraded_count = sum(
            1
            for stats in all_stats.values()
            if stats["state"] == CircuitState.HALF_OPEN.value
        )

        unhealthy_count = sum(
            1
            for stats in all_stats.values()
            if stats["state"] == CircuitState.OPEN.value
        )

        total_count = len(all_stats)

        if total_count == 0:
            overall_health = "unknown"
        elif unhealthy_count > 0:
            overall_health = "degraded"
        elif degraded_count > 0:
            overall_health = "degraded"
        else:
            overall_health = "healthy"

        return {
            "overall_health": overall_health,
            "total_circuits": total_count,
            "healthy": healthy_count,
            "degraded": degraded_count,
            "unhealthy": unhealthy_count,
            "circuits": all_stats,
        }


# Global registry instance
circuit_registry = CircuitBreakerRegistry()
