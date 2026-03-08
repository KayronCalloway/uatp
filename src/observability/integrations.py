#!/usr/bin/env python3
"""
UATP Observability Integrations
Integrates telemetry collection with existing UATP systems.
"""

import logging
import time
from functools import wraps
from typing import Any, Dict, Optional

from telemetry import telemetry

logger = logging.getLogger(__name__)


class ObservabilityIntegration:
    """Integrates observability with UATP systems."""

    def __init__(self, telemetry_collector=None):
        self.telemetry = telemetry_collector or telemetry
        self.enabled = True
        logger.info("Observability integration initialized")

    def enable(self):
        """Enable observability collection."""
        self.enabled = True
        logger.info("Observability collection enabled")

    def disable(self):
        """Disable observability collection."""
        self.enabled = False
        logger.info("Observability collection disabled")

    def instrument_capsule_engine(self, engine_class):
        """Instrument capsule engine with observability."""
        original_create_capsule = engine_class.create_capsule_async
        original_create_from_prompt = engine_class.create_capsule_from_prompt_async

        @wraps(original_create_capsule)
        async def traced_create_capsule(self, capsule):
            if not self.enabled:
                return await original_create_capsule(capsule)

            start_time = time.time()
            status = "success"

            try:
                with telemetry.trace_operation(
                    "capsule_creation",
                    {
                        "capsule_id": capsule.capsule_id,
                        "capsule_type": capsule.capsule_type.value,
                    },
                ):
                    result = await original_create_capsule(capsule)

                    # Record success metrics
                    telemetry.record_capsule_creation(
                        capsule_type=capsule.capsule_type.value,
                        status=status,
                        duration_seconds=time.time() - start_time,
                    )

                    return result

            except Exception:
                status = "error"
                telemetry.record_capsule_creation(
                    capsule_type=capsule.capsule_type.value,
                    status=status,
                    duration_seconds=time.time() - start_time,
                )
                raise

        @wraps(original_create_from_prompt)
        async def traced_create_from_prompt(self, prompt, **kwargs):
            if not self.enabled:
                return await original_create_from_prompt(prompt, **kwargs)

            start_time = time.time()
            status = "success"

            try:
                with telemetry.trace_operation(
                    "capsule_from_prompt",
                    {
                        "prompt_length": len(prompt),
                        "model": kwargs.get("model", "default"),
                    },
                ):
                    result = await original_create_from_prompt(prompt, **kwargs)

                    # Record success metrics
                    telemetry.record_capsule_creation(
                        capsule_type=result.capsule_type.value,
                        status=status,
                        duration_seconds=time.time() - start_time,
                    )

                    return result

            except Exception:
                status = "error"
                telemetry.record_capsule_creation(
                    capsule_type="unknown",
                    status=status,
                    duration_seconds=time.time() - start_time,
                )
                raise

        # Replace methods
        engine_class.create_capsule_async = traced_create_capsule
        engine_class.create_capsule_from_prompt_async = traced_create_from_prompt

        logger.info("Capsule engine instrumented with observability")
        return engine_class

    def instrument_llm_client(self, client_class):
        """Instrument LLM client with observability."""
        original_get_completion = client_class.get_completion
        original_get_completion_async = client_class.get_completion_async

        @wraps(original_get_completion)
        def traced_get_completion(self, prompt, model="gpt-4", **kwargs):
            if not self.enabled:
                return original_get_completion(prompt, model, **kwargs)

            start_time = time.time()
            status = "success"

            try:
                with telemetry.trace_operation(
                    "llm_completion",
                    {
                        "model": model,
                        "provider": "openai",
                        "prompt_length": len(prompt),
                    },
                ):
                    result = original_get_completion(prompt, model, **kwargs)

                    # Record metrics (with estimated values for tokens/cost)
                    telemetry.record_llm_request(
                        provider="openai",
                        model=model,
                        status=status,
                        duration_seconds=time.time() - start_time,
                        tokens_used=len(result.split()) * 2,  # Rough estimate
                        cost_usd=0.001,  # Rough estimate
                    )

                    return result

            except Exception:
                status = "error"
                telemetry.record_llm_request(
                    provider="openai",
                    model=model,
                    status=status,
                    duration_seconds=time.time() - start_time,
                    tokens_used=0,
                    cost_usd=0.0,
                )
                raise

        @wraps(original_get_completion_async)
        async def traced_get_completion_async(self, prompt, model="gpt-4", **kwargs):
            if not self.enabled:
                return await original_get_completion_async(prompt, model, **kwargs)

            start_time = time.time()
            status = "success"

            try:
                with telemetry.trace_operation(
                    "llm_completion_async",
                    {
                        "model": model,
                        "provider": "openai",
                        "prompt_length": len(prompt),
                    },
                ):
                    result = await original_get_completion_async(
                        prompt, model, **kwargs
                    )

                    # Record metrics (with estimated values for tokens/cost)
                    telemetry.record_llm_request(
                        provider="openai",
                        model=model,
                        status=status,
                        duration_seconds=time.time() - start_time,
                        tokens_used=len(result.split()) * 2,  # Rough estimate
                        cost_usd=0.001,  # Rough estimate
                    )

                    return result

            except Exception:
                status = "error"
                telemetry.record_llm_request(
                    provider="openai",
                    model=model,
                    status=status,
                    duration_seconds=time.time() - start_time,
                    tokens_used=0,
                    cost_usd=0.0,
                )
                raise

        # Replace methods
        client_class.get_completion = traced_get_completion
        client_class.get_completion_async = traced_get_completion_async

        logger.info("LLM client instrumented with observability")
        return client_class

    def instrument_ethics_circuit_breaker(self, circuit_breaker_class):
        """Instrument ethics circuit breaker with observability."""
        original_evaluate = circuit_breaker_class.evaluate_capsule_ethics
        original_refuse = circuit_breaker_class.refuse_capsule

        @wraps(original_evaluate)
        async def traced_evaluate(self, capsule):
            if not self.enabled:
                return await original_evaluate(capsule)

            start_time = time.time()

            try:
                with telemetry.trace_operation(
                    "ethics_evaluation",
                    {
                        "capsule_id": capsule.capsule_id,
                        "capsule_type": capsule.capsule_type.value,
                    },
                ):
                    result = await original_evaluate(capsule)

                    # Record ethics evaluation
                    telemetry.record_ethics_evaluation(
                        result="allowed" if result.allowed else "refused",
                        severity=result.severity.value,
                    )

                    return result

            except Exception:
                telemetry.record_ethics_evaluation(result="error", severity="high")
                raise

        @wraps(original_refuse)
        async def traced_refuse(self, capsule, evaluation):
            if not self.enabled:
                return await original_refuse(capsule, evaluation)

            try:
                with telemetry.trace_operation(
                    "ethics_refusal",
                    {
                        "capsule_id": capsule.capsule_id,
                        "refusal_reason": evaluation.refusal_reason.value
                        if evaluation.refusal_reason
                        else "unknown",
                    },
                ):
                    result = await original_refuse(capsule, evaluation)

                    # This is already recorded in evaluate, but we could add additional metrics here

                    return result

            except Exception as e:
                logger.error(f"Error during ethics refusal: {e}")
                raise

        # Replace methods
        circuit_breaker_class.evaluate_capsule_ethics = traced_evaluate
        circuit_breaker_class.refuse_capsule = traced_refuse

        logger.info("Ethics circuit breaker instrumented with observability")
        return circuit_breaker_class

    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        return {
            "observability_enabled": self.enabled,
            "metrics_available": len(self.telemetry.metrics) > 0,
            "traces_collected": len(self.telemetry.traces),
            "system_components": {
                "database": True,  # Would check actual database
                "api": True,  # Would check actual API
                "llm": True,  # Would check LLM connectivity
                "ethics": True,  # Would check ethics system
            },
        }

    def update_system_health(self):
        """Update system health metrics."""
        if not self.enabled:
            return

        health_status = self.get_health_status()

        # Update health metrics for each component
        for component, is_healthy in health_status["system_components"].items():
            self.telemetry.set_system_health(component, is_healthy)

        # Update connection metrics (mock data)
        self.telemetry.set_active_connections("http", 10)
        self.telemetry.set_active_connections("websocket", 5)
        self.telemetry.set_active_connections("database", 3)


# Global integration instance
observability_integration = ObservabilityIntegration()


# Convenience decorators for manual instrumentation
def observe_operation(operation_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to observe operation metrics."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not observability_integration.enabled:
                return func(*args, **kwargs)

            start_time = time.time()
            status = "success"

            try:
                with telemetry.trace_operation(operation_name, labels):
                    result = func(*args, **kwargs)
                    return result

            except Exception:
                status = "error"
                raise

            finally:
                # Record generic operation metrics
                telemetry.observe_histogram(
                    "uatp_operation_duration_seconds",
                    time.time() - start_time,
                    {"operation": operation_name, "status": status},
                )

        return wrapper

    return decorator


def observe_async_operation(
    operation_name: str, labels: Optional[Dict[str, str]] = None
):
    """Decorator to observe async operation metrics."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not observability_integration.enabled:
                return await func(*args, **kwargs)

            start_time = time.time()
            status = "success"

            try:
                with telemetry.trace_operation(operation_name, labels):
                    result = await func(*args, **kwargs)
                    return result

            except Exception:
                status = "error"
                raise

            finally:
                # Record generic operation metrics
                telemetry.observe_histogram(
                    "uatp_operation_duration_seconds",
                    time.time() - start_time,
                    {"operation": operation_name, "status": status},
                )

        return wrapper

    return decorator


# Example usage and testing
if __name__ == "__main__":

    def test_observability_integration():
        """Test observability integration."""
        print(" Observability Integration Test")
        print("=" * 40)

        # Test health status
        health = observability_integration.get_health_status()
        print(" Health Status:")
        for key, value in health.items():
            print(f"  {key}: {value}")

        # Test system health update
        print("\n Updating system health metrics...")
        observability_integration.update_system_health()

        # Test decorators
        @observe_operation("test_sync_operation")
        def sync_test():
            time.sleep(0.1)
            return "sync_result"

        @observe_async_operation("test_async_operation")
        async def async_test():
            import asyncio

            await asyncio.sleep(0.1)
            return "async_result"

        # Run tests
        print("\n Testing decorated operations...")
        result1 = sync_test()
        print(f"[OK] Sync operation result: {result1}")

        import asyncio

        result2 = asyncio.run(async_test())
        print(f"[OK] Async operation result: {result2}")

        # Get metrics summary
        summary = telemetry.get_metrics_summary()
        print("\n Final Metrics Summary:")
        print(f"  Total traces: {summary['recent_traces']}")
        print(f"  Fallback metrics: {len(summary.get('fallback_metrics', {}))}")

        print("\n[OK] Observability integration test complete!")

    test_observability_integration()
