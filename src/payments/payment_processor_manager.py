"""
Payment Processor Manager for UATP Capsule Engine

Advanced payment processing manager that handles multiple payment providers,
routing optimization, retry logic, and comprehensive failure handling.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set

logger = logging.getLogger(__name__)


class ProcessorStatus(Enum):
    """Payment processor status."""

    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    DISABLED = "disabled"


class RoutingStrategy(Enum):
    """Payment routing strategies."""

    LOWEST_FEE = "lowest_fee"
    FASTEST = "fastest"
    MOST_RELIABLE = "most_reliable"
    LOAD_BALANCED = "load_balanced"
    USER_PREFERENCE = "user_preference"


class PaymentPriority(Enum):
    """Payment processing priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ProcessorMetrics:
    """Performance metrics for a payment processor."""

    success_rate: float = 0.0
    average_processing_time: float = 0.0
    failure_count: int = 0
    total_processed: int = 0
    last_error: Optional[str] = None
    last_success: Optional[datetime] = None
    daily_volume: Decimal = Decimal("0.00")
    daily_limit: Decimal = Decimal("100000.00")


@dataclass
class ProcessorConfig:
    """Configuration for a payment processor."""

    processor_id: str
    processor_name: str
    status: ProcessorStatus = ProcessorStatus.ACTIVE
    supported_currencies: Set[str] = field(default_factory=lambda: {"USD"})
    fee_structure: Dict[str, Any] = field(default_factory=dict)
    processing_limits: Dict[str, Decimal] = field(default_factory=dict)
    reliability_score: float = 1.0
    priority_level: int = 1
    maintenance_windows: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PaymentRoute:
    """Represents a payment routing decision."""

    processor_id: str
    confidence_score: float
    estimated_time: timedelta
    estimated_fee: Decimal
    risk_score: float
    routing_reason: str


class PaymentProcessor(Protocol):
    """Protocol for payment processors."""

    async def process_payment(
        self,
        amount: Decimal,
        currency: str,
        recipient_details: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a payment."""
        ...

    async def get_status(self) -> Dict[str, Any]:
        """Get processor status."""
        ...

    def calculate_fees(self, amount: Decimal, currency: str) -> Decimal:
        """Calculate processing fees."""
        ...


class MockPaymentProcessor:
    """Mock payment processor for testing."""

    def __init__(self, processor_id: str, config: ProcessorConfig):
        self.processor_id = processor_id
        self.config = config

    async def process_payment(
        self,
        amount: Decimal,
        currency: str,
        recipient_details: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Mock payment processing."""
        await asyncio.sleep(0.1)  # Simulate processing time

        # Simulate occasional failures
        import random

        if random.random() < 0.05:  # 5% failure rate
            return {
                "success": False,
                "error": "Mock payment failure",
                "error_code": "PROCESSING_ERROR",
            }

        transaction_id = f"{self.processor_id}_{uuid.uuid4().hex[:12]}"
        fee = self.calculate_fees(amount, currency)

        return {
            "success": True,
            "transaction_id": transaction_id,
            "amount": float(amount),
            "currency": currency,
            "fee": float(fee),
            "net_amount": float(amount - fee),
            "processor_id": self.processor_id,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get mock processor status."""
        return {
            "processor_id": self.processor_id,
            "status": self.config.status.value,
            "healthy": self.config.status == ProcessorStatus.ACTIVE,
            "response_time_ms": 150,
        }

    def calculate_fees(self, amount: Decimal, currency: str) -> Decimal:
        """Calculate mock fees."""
        if self.processor_id == "stripe":
            return (amount * Decimal("0.029")) + Decimal("0.30")
        elif self.processor_id == "paypal":
            return (amount * Decimal("0.029")) + Decimal("0.30")
        elif self.processor_id == "crypto":
            return Decimal("0.50")  # Flat fee
        else:
            return amount * Decimal("0.02")  # 2% default


class PaymentProcessorManager:
    """Advanced payment processor manager."""

    def __init__(
        self, default_routing_strategy: RoutingStrategy = RoutingStrategy.MOST_RELIABLE
    ):
        self.processors: Dict[str, PaymentProcessor] = {}
        self.processor_configs: Dict[str, ProcessorConfig] = {}
        self.processor_metrics: Dict[str, ProcessorMetrics] = {}
        self.default_routing_strategy = default_routing_strategy

        # Processing queues by priority
        self.payment_queues: Dict[PaymentPriority, List[Dict[str, Any]]] = {
            PaymentPriority.CRITICAL: [],
            PaymentPriority.HIGH: [],
            PaymentPriority.NORMAL: [],
            PaymentPriority.LOW: [],
        }

        # Circuit breaker settings
        self.circuit_breaker_thresholds = {
            "failure_rate": 0.50,  # 50% failure rate
            "min_requests": 10,
            "timeout_seconds": 300,  # 5 minutes
        }
        self.circuit_breaker_state: Dict[str, Dict[str, Any]] = {}

        # Initialize with mock processors for demo
        self._initialize_mock_processors()

        # Start background tasks
        asyncio.create_task(self._process_payment_queues())
        asyncio.create_task(self._monitor_processors())

    def _initialize_mock_processors(self):
        """Initialize mock processors for demonstration."""

        # Stripe processor
        stripe_config = ProcessorConfig(
            processor_id="stripe",
            processor_name="Stripe",
            supported_currencies={"USD", "EUR", "GBP"},
            fee_structure={"percentage": 2.9, "fixed": 0.30},
            processing_limits={"min": Decimal("0.50"), "max": Decimal("999999.99")},
            reliability_score=0.995,
            priority_level=1,
        )
        self.register_processor(
            "stripe", MockPaymentProcessor("stripe", stripe_config), stripe_config
        )

        # PayPal processor
        paypal_config = ProcessorConfig(
            processor_id="paypal",
            processor_name="PayPal",
            supported_currencies={"USD", "EUR", "GBP"},
            fee_structure={"percentage": 2.9, "fixed": 0.30},
            processing_limits={"min": Decimal("1.00"), "max": Decimal("10000.00")},
            reliability_score=0.985,
            priority_level=2,
        )
        self.register_processor(
            "paypal", MockPaymentProcessor("paypal", paypal_config), paypal_config
        )

        # Crypto processor
        crypto_config = ProcessorConfig(
            processor_id="crypto",
            processor_name="Cryptocurrency",
            supported_currencies={"USD", "BTC", "ETH", "USDC"},
            fee_structure={"fixed": 0.50},
            processing_limits={"min": Decimal("1.00"), "max": Decimal("50000.00")},
            reliability_score=0.970,
            priority_level=3,
        )
        self.register_processor(
            "crypto", MockPaymentProcessor("crypto", crypto_config), crypto_config
        )

    def register_processor(
        self, processor_id: str, processor: PaymentProcessor, config: ProcessorConfig
    ):
        """Register a payment processor."""
        self.processors[processor_id] = processor
        self.processor_configs[processor_id] = config
        self.processor_metrics[processor_id] = ProcessorMetrics()
        self.circuit_breaker_state[processor_id] = {
            "state": "CLOSED",  # CLOSED, OPEN, HALF_OPEN
            "failure_count": 0,
            "last_failure": None,
            "next_attempt": None,
        }

        logger.info(f"Registered payment processor: {processor_id}")

    async def process_payment(
        self,
        amount: Decimal,
        currency: str,
        recipient_details: Dict[str, Any],
        routing_strategy: Optional[RoutingStrategy] = None,
        priority: PaymentPriority = PaymentPriority.NORMAL,
        processor_preference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process a payment with intelligent routing."""

        try:
            # Validate input
            if amount <= 0:
                return {"success": False, "error": "Invalid amount"}

            if currency not in ["USD", "EUR", "GBP", "BTC", "ETH", "USDC"]:
                return {"success": False, "error": "Unsupported currency"}

            # Determine routing strategy
            strategy = routing_strategy or self.default_routing_strategy

            # Get available routes
            routes = await self._calculate_routes(
                amount, currency, strategy, processor_preference
            )

            if not routes:
                return {"success": False, "error": "No available payment processors"}

            # Try routes in order of preference
            for route in routes:
                processor_id = route.processor_id

                # Check circuit breaker
                if not self._is_processor_available(processor_id):
                    logger.warning(
                        f"Processor {processor_id} unavailable (circuit breaker)"
                    )
                    continue

                # Attempt payment
                try:
                    processor = self.processors[processor_id]
                    result = await processor.process_payment(
                        amount, currency, recipient_details, metadata
                    )

                    # Update metrics
                    await self._update_processor_metrics(
                        processor_id, result["success"]
                    )

                    if result["success"]:
                        # Add routing information
                        result["routing_info"] = {
                            "processor_id": processor_id,
                            "routing_strategy": strategy.value,
                            "confidence_score": route.confidence_score,
                            "estimated_fee": float(route.estimated_fee),
                            "actual_fee": result.get("fee", 0),
                        }

                        logger.info(
                            f"Payment successful via {processor_id}: {result['transaction_id']}"
                        )
                        return result
                    else:
                        logger.warning(
                            f"Payment failed via {processor_id}: {result.get('error')}"
                        )
                        # Continue to next route

                except Exception as e:
                    logger.error(f"Processor {processor_id} error: {e}")
                    await self._update_processor_metrics(processor_id, False, str(e))
                    # Continue to next route

            # All routes failed
            return {
                "success": False,
                "error": "All payment processors failed",
                "attempted_processors": [route.processor_id for route in routes],
            }

        except Exception as e:
            logger.error(f"Payment processing error: {e}", exc_info=True)
            return {"success": False, "error": "Payment processing failed"}

    async def _calculate_routes(
        self,
        amount: Decimal,
        currency: str,
        strategy: RoutingStrategy,
        processor_preference: Optional[str] = None,
    ) -> List[PaymentRoute]:
        """Calculate optimal payment routes."""

        routes = []

        for processor_id, config in self.processor_configs.items():
            # Check if processor supports currency
            if currency not in config.supported_currencies:
                continue

            # Check if processor is active
            if config.status != ProcessorStatus.ACTIVE:
                continue

            # Check amount limits
            limits = config.processing_limits
            if limits.get("min") and amount < limits["min"]:
                continue
            if limits.get("max") and amount > limits["max"]:
                continue

            # Check daily volume limits
            metrics = self.processor_metrics[processor_id]
            if metrics.daily_volume + amount > metrics.daily_limit:
                continue

            # Calculate route metrics
            processor = self.processors[processor_id]
            estimated_fee = processor.calculate_fees(amount, currency)

            route = PaymentRoute(
                processor_id=processor_id,
                confidence_score=self._calculate_confidence_score(processor_id, amount),
                estimated_time=timedelta(
                    seconds=self._estimate_processing_time(processor_id)
                ),
                estimated_fee=estimated_fee,
                risk_score=1.0 - config.reliability_score,
                routing_reason=f"Strategy: {strategy.value}",
            )

            routes.append(route)

        # Sort routes based on strategy
        routes = self._sort_routes_by_strategy(routes, strategy)

        # Apply processor preference if specified
        if processor_preference and processor_preference in [
            r.processor_id for r in routes
        ]:
            preferred_route = next(
                r for r in routes if r.processor_id == processor_preference
            )
            routes.remove(preferred_route)
            routes.insert(0, preferred_route)
            preferred_route.routing_reason = "User preference"

        return routes

    def _sort_routes_by_strategy(
        self, routes: List[PaymentRoute], strategy: RoutingStrategy
    ) -> List[PaymentRoute]:
        """Sort routes based on routing strategy."""

        if strategy == RoutingStrategy.LOWEST_FEE:
            return sorted(routes, key=lambda r: r.estimated_fee)
        elif strategy == RoutingStrategy.FASTEST:
            return sorted(routes, key=lambda r: r.estimated_time)
        elif strategy == RoutingStrategy.MOST_RELIABLE:
            return sorted(routes, key=lambda r: r.risk_score)
        elif strategy == RoutingStrategy.LOAD_BALANCED:
            # Sort by daily volume (least loaded first)
            return sorted(
                routes,
                key=lambda r: self.processor_metrics[r.processor_id].daily_volume,
            )
        else:  # USER_PREFERENCE handled separately
            return sorted(routes, key=lambda r: r.confidence_score, reverse=True)

    def _calculate_confidence_score(self, processor_id: str, amount: Decimal) -> float:
        """Calculate confidence score for a processor."""

        metrics = self.processor_metrics[processor_id]
        config = self.processor_configs[processor_id]

        # Base score from reliability
        base_score = config.reliability_score

        # Adjust for recent performance
        if metrics.total_processed > 0:
            recent_success_rate = 1.0 - (
                metrics.failure_count / metrics.total_processed
            )
            base_score = (base_score + recent_success_rate) / 2

        # Adjust for amount vs daily volume
        volume_factor = min(
            1.0, (metrics.daily_limit - metrics.daily_volume) / metrics.daily_limit
        )

        return base_score * volume_factor

    def _estimate_processing_time(self, processor_id: str) -> float:
        """Estimate processing time for a processor."""

        # Mock processing times in seconds
        times = {
            "stripe": 2.0,
            "paypal": 3.0,
            "crypto": 30.0,  # Longer for blockchain confirmation
        }

        return times.get(processor_id, 5.0)

    def _is_processor_available(self, processor_id: str) -> bool:
        """Check if processor is available (circuit breaker)."""

        cb_state = self.circuit_breaker_state[processor_id]
        current_time = datetime.now(timezone.utc)

        if cb_state["state"] == "CLOSED":
            return True
        elif cb_state["state"] == "OPEN":
            # Check if timeout period has passed
            if cb_state["next_attempt"] and current_time >= cb_state["next_attempt"]:
                cb_state["state"] = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True

    async def _update_processor_metrics(
        self, processor_id: str, success: bool, error: Optional[str] = None
    ):
        """Update processor performance metrics."""

        metrics = self.processor_metrics[processor_id]
        cb_state = self.circuit_breaker_state[processor_id]

        metrics.total_processed += 1

        if success:
            metrics.last_success = datetime.now(timezone.utc)

            # Reset circuit breaker on success
            if cb_state["state"] != "CLOSED":
                cb_state["state"] = "CLOSED"
                cb_state["failure_count"] = 0
                logger.info(f"Circuit breaker reset for {processor_id}")

        else:
            metrics.failure_count += 1
            metrics.last_error = error
            cb_state["failure_count"] += 1
            cb_state["last_failure"] = datetime.now(timezone.utc)

            # Check if circuit breaker should open
            failure_rate = cb_state["failure_count"] / max(metrics.total_processed, 1)
            if (
                failure_rate >= self.circuit_breaker_thresholds["failure_rate"]
                and metrics.total_processed
                >= self.circuit_breaker_thresholds["min_requests"]
            ):
                cb_state["state"] = "OPEN"
                cb_state["next_attempt"] = datetime.now(timezone.utc) + timedelta(
                    seconds=self.circuit_breaker_thresholds["timeout_seconds"]
                )
                logger.warning(f"Circuit breaker opened for {processor_id}")

        # Update success rate
        if metrics.total_processed > 0:
            metrics.success_rate = (
                metrics.total_processed - metrics.failure_count
            ) / metrics.total_processed

    async def _process_payment_queues(self):
        """Background task to process payment queues."""

        while True:
            try:
                # Process queues in priority order
                for priority in [
                    PaymentPriority.CRITICAL,
                    PaymentPriority.HIGH,
                    PaymentPriority.NORMAL,
                    PaymentPriority.LOW,
                ]:
                    queue = self.payment_queues[priority]
                    if queue:
                        payment_request = queue.pop(0)
                        # Process payment asynchronously
                        asyncio.create_task(
                            self._process_queued_payment(payment_request)
                        )

                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting

            except Exception as e:
                logger.error(f"Error processing payment queues: {e}")
                await asyncio.sleep(1)

    async def _process_queued_payment(self, payment_request: Dict[str, Any]):
        """Process a queued payment."""
        try:
            result = await self.process_payment(**payment_request["args"])
            # Could store result or notify callback
            logger.info(
                f"Queued payment processed: {result.get('transaction_id', 'failed')}"
            )
        except Exception as e:
            logger.error(f"Error processing queued payment: {e}")

    async def _monitor_processors(self):
        """Background task to monitor processor health."""

        while True:
            try:
                for processor_id, processor in self.processors.items():
                    try:
                        status = await processor.get_status()
                        config = self.processor_configs[processor_id]

                        # Update processor status based on health check
                        if status.get("healthy", False):
                            if config.status == ProcessorStatus.ERROR:
                                config.status = ProcessorStatus.ACTIVE
                                logger.info(f"Processor {processor_id} recovered")
                        else:
                            if config.status == ProcessorStatus.ACTIVE:
                                config.status = ProcessorStatus.ERROR
                                logger.warning(f"Processor {processor_id} unhealthy")

                    except Exception as e:
                        logger.error(f"Health check failed for {processor_id}: {e}")
                        self.processor_configs[
                            processor_id
                        ].status = ProcessorStatus.ERROR

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error monitoring processors: {e}")
                await asyncio.sleep(60)

    def get_processor_status(self) -> Dict[str, Any]:
        """Get status of all processors."""

        status = {}
        for processor_id, config in self.processor_configs.items():
            metrics = self.processor_metrics[processor_id]
            cb_state = self.circuit_breaker_state[processor_id]

            status[processor_id] = {
                "name": config.processor_name,
                "status": config.status.value,
                "success_rate": metrics.success_rate,
                "total_processed": metrics.total_processed,
                "daily_volume": float(metrics.daily_volume),
                "circuit_breaker_state": cb_state["state"],
                "reliability_score": config.reliability_score,
                "supported_currencies": list(config.supported_currencies),
            }

        return status

    def get_routing_recommendation(
        self, amount: Decimal, currency: str
    ) -> Dict[str, Any]:
        """Get routing recommendation for a payment."""

        recommendations = {}

        for strategy in RoutingStrategy:
            routes = asyncio.run(self._calculate_routes(amount, currency, strategy))
            if routes:
                best_route = routes[0]
                recommendations[strategy.value] = {
                    "processor_id": best_route.processor_id,
                    "confidence_score": best_route.confidence_score,
                    "estimated_fee": float(best_route.estimated_fee),
                    "estimated_time_seconds": best_route.estimated_time.total_seconds(),
                    "risk_score": best_route.risk_score,
                }

        return recommendations


# Factory function
def create_payment_processor_manager(
    routing_strategy: RoutingStrategy = RoutingStrategy.MOST_RELIABLE,
) -> PaymentProcessorManager:
    """Create a payment processor manager instance."""
    return PaymentProcessorManager(routing_strategy)


# Example usage
if __name__ == "__main__":

    async def demo_payment_processor_manager():
        """Demonstrate the payment processor manager."""

        manager = create_payment_processor_manager()

        # Wait for initialization
        await asyncio.sleep(1)

        print(" Payment Processor Manager Demo")
        print("\n Processor Status:")
        status = manager.get_processor_status()
        for processor_id, info in status.items():
            print(
                f"  {processor_id}: {info['status']} (Success Rate: {info['success_rate']:.1%})"
            )

        print("\n Processing Test Payment:")
        result = await manager.process_payment(
            amount=Decimal("25.00"),
            currency="USD",
            recipient_details={"email": "test@example.com"},
            routing_strategy=RoutingStrategy.LOWEST_FEE,
        )
        print(f"  Result: {result}")

        print("\n Routing Recommendations:")
        recommendations = manager.get_routing_recommendation(Decimal("100.00"), "USD")
        for strategy, rec in recommendations.items():
            print(
                f"  {strategy}: {rec['processor_id']} (Fee: ${rec['estimated_fee']:.2f})"
            )

        print("\n[OK] Demo completed!")

    asyncio.run(demo_payment_processor_manager())
