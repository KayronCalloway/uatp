"""
UATP Resilience Infrastructure

This module provides comprehensive resilience capabilities:
- Circuit breaker pattern for preventing cascading failures
- Retry mechanisms with exponential backoff
- Graceful degradation strategies
- Health monitoring for external dependencies
- Crisis response and civilization-grade resilience mechanisms
"""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitState,
    ExternalServiceClient,
    ExternalServiceError,
    circuit_registry,
)

from .crisis_response import crisis_resilience, CrisisResilienceInfrastructure

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitState",
    "ExternalServiceClient",
    "ExternalServiceError",
    "circuit_registry",
    "crisis_resilience",
    "CrisisResilienceInfrastructure",
]
