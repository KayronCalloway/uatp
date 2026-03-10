"""
Event-Driven System for UATP Capsule Engine
==========================================

This module provides a comprehensive event-driven architecture for cross-service
integration, enabling real-time communication and automated workflows between
Dividend Bonds, Citizenship, and other UATP services.

Key Features:
- Asynchronous event publishing and subscription
- Event persistence and replay capabilities
- Dead letter queue for failed events
- Event filtering and routing
- Metrics and monitoring
"""

import asyncio
import logging
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Enumeration of all event types in the UATP system."""

    # Citizenship Events
    CITIZENSHIP_APPLICATION_SUBMITTED = "citizenship.application.submitted"
    CITIZENSHIP_ASSESSMENT_COMPLETED = "citizenship.assessment.completed"
    CITIZENSHIP_GRANTED = "citizenship.granted"
    CITIZENSHIP_DENIED = "citizenship.denied"
    CITIZENSHIP_REVOKED = "citizenship.revoked"
    CITIZENSHIP_STATUS_UPDATED = "citizenship.status.updated"

    # Dividend Bonds Events
    IP_ASSET_REGISTERED = "bonds.asset.registered"
    DIVIDEND_BOND_CREATED = "bonds.bond.created"
    DIVIDEND_PAYMENT_PROCESSED = "bonds.payment.processed"
    BOND_MATURED = "bonds.bond.matured"
    BOND_DEFAULTED = "bonds.bond.defaulted"

    # Cross-Service Events
    AGENT_RIGHTS_UPDATED = "agent.rights.updated"
    FINANCIAL_STATUS_CHANGED = "agent.financial.status_changed"
    COMPLIANCE_CHECK_REQUIRED = "compliance.check.required"
    RISK_ASSESSMENT_UPDATED = "risk.assessment.updated"

    # System Events
    SERVICE_STARTED = "system.service.started"
    SERVICE_STOPPED = "system.service.stopped"
    HEALTH_CHECK_FAILED = "system.health.check_failed"


@dataclass
class Event:
    """Base event class for all UATP events."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.SERVICE_STARTED
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_service: str = "unknown"
    agent_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        event_dict = asdict(self)
        event_dict["event_type"] = self.event_type.value
        event_dict["timestamp"] = self.timestamp.isoformat()
        return event_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        data = data.copy()
        data["event_type"] = EventType(data["event_type"])
        data["timestamp"] = datetime.fromisoformat(
            data["timestamp"].replace("Z", "+00:00")
        )
        return cls(**data)


@dataclass
class EventSubscription:
    """Represents an event subscription."""

    subscription_id: str
    event_types: Set[EventType]
    handler: Callable[[Event], Any]
    filter_func: Optional[Callable[[Event], bool]] = None
    max_retries: int = 3
    retry_count: int = 0
    active: bool = True


class EventStore:
    """Simple in-memory event store with persistence capabilities."""

    def __init__(self, max_events: int = 10000):
        self.events: deque = deque(maxlen=max_events)
        self.events_by_type: Dict[EventType, List[Event]] = defaultdict(list)
        self.events_by_agent: Dict[str, List[Event]] = defaultdict(list)
        self.dead_letter_queue: deque = deque(maxlen=1000)

    def store_event(self, event: Event) -> None:
        """Store an event in the event store."""
        self.events.append(event)
        self.events_by_type[event.event_type].append(event)

        if event.agent_id:
            self.events_by_agent[event.agent_id].append(event)

        logger.debug(f"Stored event {event.event_id} of type {event.event_type.value}")

    def get_events_by_type(
        self, event_type: EventType, limit: int = 100
    ) -> List[Event]:
        """Get events by type."""
        return list(self.events_by_type[event_type])[-limit:]

    def get_events_by_agent(self, agent_id: str, limit: int = 100) -> List[Event]:
        """Get events for a specific agent."""
        return list(self.events_by_agent[agent_id])[-limit:]

    def get_recent_events(self, limit: int = 100) -> List[Event]:
        """Get most recent events."""
        return list(self.events)[-limit:]

    def add_to_dead_letter_queue(self, event: Event, error: str) -> None:
        """Add failed event to dead letter queue."""
        dead_event = {
            "event": event.to_dict(),
            "error": error,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }
        self.dead_letter_queue.append(dead_event)
        logger.warning(f"Added event {event.event_id} to dead letter queue: {error}")


class EventBus:
    """Central event bus for publishing and subscribing to events."""

    def __init__(self, event_store: Optional[EventStore] = None):
        self.event_store = event_store or EventStore()
        self.subscriptions: Dict[str, EventSubscription] = {}
        self.subscribers_by_type: Dict[EventType, List[str]] = defaultdict(list)
        self.metrics = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "subscriptions_active": 0,
        }
        self._running = False

    async def start(self) -> None:
        """Start the event bus."""
        self._running = True
        logger.info("Event bus started")

    async def stop(self) -> None:
        """Stop the event bus."""
        self._running = False
        logger.info("Event bus stopped")

    def subscribe(
        self,
        event_types: List[EventType],
        handler: Callable[[Event], Any],
        subscription_id: Optional[str] = None,
        filter_func: Optional[Callable[[Event], bool]] = None,
    ) -> str:
        """Subscribe to events."""
        if not subscription_id:
            subscription_id = f"sub_{uuid.uuid4().hex[:8]}"

        subscription = EventSubscription(
            subscription_id=subscription_id,
            event_types=set(event_types),
            handler=handler,
            filter_func=filter_func,
        )

        self.subscriptions[subscription_id] = subscription

        for event_type in event_types:
            self.subscribers_by_type[event_type].append(subscription_id)

        self.metrics["subscriptions_active"] = len(
            [s for s in self.subscriptions.values() if s.active]
        )

        logger.info(
            f"Created subscription {subscription_id} for events: {[e.value for e in event_types]}"
        )
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        if subscription_id not in self.subscriptions:
            return False

        subscription = self.subscriptions[subscription_id]
        subscription.active = False

        # Remove from type mappings
        for event_type in subscription.event_types:
            if subscription_id in self.subscribers_by_type[event_type]:
                self.subscribers_by_type[event_type].remove(subscription_id)

        del self.subscriptions[subscription_id]
        self.metrics["subscriptions_active"] = len(
            [s for s in self.subscriptions.values() if s.active]
        )

        logger.info(f"Unsubscribed {subscription_id}")
        return True

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        if not self._running:
            logger.warning("Event bus not running, event not published")
            return

        # Store event
        self.event_store.store_event(event)
        self.metrics["events_published"] += 1

        # Find subscribers
        subscriber_ids = self.subscribers_by_type.get(event.event_type, [])

        if not subscriber_ids:
            logger.debug(f"No subscribers for event type {event.event_type.value}")
            return

        # Process subscribers
        tasks = []
        for subscriber_id in subscriber_ids:
            if subscriber_id in self.subscriptions:
                subscription = self.subscriptions[subscriber_id]
                if subscription.active:
                    tasks.append(self._handle_event(event, subscription))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.debug(f"Published event {event.event_id} to {len(tasks)} subscribers")

    async def _handle_event(
        self, event: Event, subscription: EventSubscription
    ) -> None:
        """Handle event for a specific subscription."""
        try:
            # Apply filter if present
            if subscription.filter_func and not subscription.filter_func(event):
                return

            # Call handler
            if asyncio.iscoroutinefunction(subscription.handler):
                await subscription.handler(event)
            else:
                subscription.handler(event)

            self.metrics["events_processed"] += 1
            subscription.retry_count = 0  # Reset on success

        except Exception as e:
            self.metrics["events_failed"] += 1
            subscription.retry_count += 1

            error_msg = (
                f"Handler failed for subscription {subscription.subscription_id}: {e}"
            )
            logger.error(error_msg)

            if subscription.retry_count >= subscription.max_retries:
                self.event_store.add_to_dead_letter_queue(event, error_msg)
                subscription.active = False
                logger.error(
                    f"Subscription {subscription.subscription_id} disabled after max retries"
                )

    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics."""
        return {
            **self.metrics,
            "event_store_size": len(self.event_store.events),
            "dead_letter_queue_size": len(self.event_store.dead_letter_queue),
            "active_subscriptions": len(
                [s for s in self.subscriptions.values() if s.active]
            ),
        }


class EventPublisher:
    """Helper class for publishing domain-specific events."""

    def __init__(self, event_bus: EventBus, source_service: str):
        self.event_bus = event_bus
        self.source_service = source_service

    async def publish_citizenship_application_submitted(
        self,
        agent_id: str,
        application_id: str,
        jurisdiction: str,
        citizenship_type: str,
    ) -> None:
        """Publish citizenship application submitted event."""
        event = Event(
            event_type=EventType.CITIZENSHIP_APPLICATION_SUBMITTED,
            source_service=self.source_service,
            agent_id=agent_id,
            data={
                "application_id": application_id,
                "jurisdiction": jurisdiction,
                "citizenship_type": citizenship_type,
            },
        )
        await self.event_bus.publish(event)

    async def publish_citizenship_granted(
        self,
        agent_id: str,
        citizenship_id: str,
        jurisdiction: str,
        rights: List[str],
        obligations: List[str],
    ) -> None:
        """Publish citizenship granted event."""
        event = Event(
            event_type=EventType.CITIZENSHIP_GRANTED,
            source_service=self.source_service,
            agent_id=agent_id,
            data={
                "citizenship_id": citizenship_id,
                "jurisdiction": jurisdiction,
                "rights": rights,
                "obligations": obligations,
            },
        )
        await self.event_bus.publish(event)

    async def publish_ip_asset_registered(
        self, agent_id: str, asset_id: str, asset_type: str, market_value: float
    ) -> None:
        """Publish IP asset registered event."""
        event = Event(
            event_type=EventType.IP_ASSET_REGISTERED,
            source_service=self.source_service,
            agent_id=agent_id,
            data={
                "asset_id": asset_id,
                "asset_type": asset_type,
                "market_value": market_value,
            },
        )
        await self.event_bus.publish(event)

    async def publish_dividend_bond_created(
        self,
        agent_id: str,
        bond_id: str,
        asset_id: str,
        face_value: float,
        bond_type: str,
    ) -> None:
        """Publish dividend bond created event."""
        event = Event(
            event_type=EventType.DIVIDEND_BOND_CREATED,
            source_service=self.source_service,
            agent_id=agent_id,
            data={
                "bond_id": bond_id,
                "asset_id": asset_id,
                "face_value": face_value,
                "bond_type": bond_type,
            },
        )
        await self.event_bus.publish(event)

    async def publish_dividend_payment_processed(
        self,
        agent_id: str,
        bond_id: str,
        payment_id: str,
        amount: float,
        recipient: str,
    ) -> None:
        """Publish dividend payment processed event."""
        event = Event(
            event_type=EventType.DIVIDEND_PAYMENT_PROCESSED,
            source_service=self.source_service,
            agent_id=agent_id,
            data={
                "bond_id": bond_id,
                "payment_id": payment_id,
                "amount": amount,
                "recipient": recipient,
            },
        )
        await self.event_bus.publish(event)

    async def publish_agent_rights_updated(
        self, agent_id: str, new_rights: List[str], context: str
    ) -> None:
        """Publish agent rights updated event."""
        event = Event(
            event_type=EventType.AGENT_RIGHTS_UPDATED,
            source_service=self.source_service,
            agent_id=agent_id,
            data={"new_rights": new_rights, "context": context},
        )
        await self.event_bus.publish(event)

    # Workflow-related event publishers
    async def publish_workflow_started(
        self, execution_id: str, workflow_id: str, context: Dict[str, Any]
    ) -> None:
        """Publish workflow started event."""
        event = Event(
            event_type=EventType.SERVICE_STARTED,
            source_service=self.source_service,
            data={
                "workflow_execution_id": execution_id,
                "workflow_id": workflow_id,
                "context": context,
                "event_subtype": "workflow_started",
            },
        )
        await self.event_bus.publish(event)

    async def publish_workflow_status_changed(
        self, execution_id: str, status: str, context: Dict[str, Any]
    ) -> None:
        """Publish workflow status changed event."""
        event = Event(
            event_type=EventType.SERVICE_STARTED,
            source_service=self.source_service,
            data={
                "workflow_execution_id": execution_id,
                "status": status,
                "context": context,
                "event_subtype": "workflow_status_changed",
            },
        )
        await self.event_bus.publish(event)

    async def publish_workflow_completed(
        self,
        execution_id: str,
        workflow_id: str,
        result: Dict[str, Any],
        duration: float,
    ) -> None:
        """Publish workflow completed event."""
        event = Event(
            event_type=EventType.SERVICE_STARTED,
            source_service=self.source_service,
            data={
                "workflow_execution_id": execution_id,
                "workflow_id": workflow_id,
                "result": result,
                "duration": duration,
                "event_subtype": "workflow_completed",
            },
        )
        await self.event_bus.publish(event)

    async def publish_workflow_failed(
        self, execution_id: str, workflow_id: str, error: str, context: Dict[str, Any]
    ) -> None:
        """Publish workflow failed event."""
        event = Event(
            event_type=EventType.HEALTH_CHECK_FAILED,
            source_service=self.source_service,
            data={
                "workflow_execution_id": execution_id,
                "workflow_id": workflow_id,
                "error": error,
                "context": context,
                "event_subtype": "workflow_failed",
            },
        )
        await self.event_bus.publish(event)

    async def publish_workflow_step_started(
        self, execution_id: str, step_id: str, step_name: str
    ) -> None:
        """Publish workflow step started event."""
        event = Event(
            event_type=EventType.SERVICE_STARTED,
            source_service=self.source_service,
            data={
                "workflow_execution_id": execution_id,
                "step_id": step_id,
                "step_name": step_name,
                "event_subtype": "workflow_step_started",
            },
        )
        await self.event_bus.publish(event)

    async def publish_workflow_step_completed(
        self, execution_id: str, step_id: str, step_name: str, result: Any
    ) -> None:
        """Publish workflow step completed event."""
        event = Event(
            event_type=EventType.SERVICE_STARTED,
            source_service=self.source_service,
            data={
                "workflow_execution_id": execution_id,
                "step_id": step_id,
                "step_name": step_name,
                "result": result,
                "event_subtype": "workflow_step_completed",
            },
        )
        await self.event_bus.publish(event)

    async def publish_workflow_step_failed(
        self, execution_id: str, step_id: str, step_name: str, error: str
    ) -> None:
        """Publish workflow step failed event."""
        event = Event(
            event_type=EventType.HEALTH_CHECK_FAILED,
            source_service=self.source_service,
            data={
                "workflow_execution_id": execution_id,
                "step_id": step_id,
                "step_name": step_name,
                "error": error,
                "event_subtype": "workflow_step_failed",
            },
        )
        await self.event_bus.publish(event)


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


async def initialize_event_system() -> EventBus:
    """Initialize the global event system."""
    global _global_event_bus
    _global_event_bus = EventBus()
    await _global_event_bus.start()
    logger.info("Event system initialized")
    return _global_event_bus
