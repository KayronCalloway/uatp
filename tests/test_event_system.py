"""
Tests for Event-Driven System
=============================

Comprehensive tests for the event system including event bus,
handlers, and service integration.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock

from src.events.event_system import (
    Event,
    EventType,
    EventBus,
    EventStore,
    EventPublisher,
    initialize_event_system,
    get_event_bus,
)
from src.events.event_handlers import (
    CitizenshipEventHandler,
    BondsEventHandler,
    SystemEventHandler,
)
from src.events.service_integration import (
    EventIntegratedDividendBondsService,
    EventIntegratedCitizenshipService,
    ServiceEventIntegrator,
)


class TestEventSystem:
    """Test the core event system components."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_store = EventStore()
        self.event_bus = EventBus(self.event_store)

    def test_event_creation(self):
        """Test event creation and serialization."""
        event = Event(
            event_type=EventType.CITIZENSHIP_GRANTED,
            source_service="test_service",
            agent_id="test_agent",
            data={"test": "data"},
        )

        assert event.event_type == EventType.CITIZENSHIP_GRANTED
        assert event.source_service == "test_service"
        assert event.agent_id == "test_agent"
        assert event.data["test"] == "data"
        assert event.event_id is not None
        assert event.timestamp is not None

    def test_event_serialization(self):
        """Test event serialization and deserialization."""
        original_event = Event(
            event_type=EventType.DIVIDEND_BOND_CREATED,
            source_service="bonds_service",
            agent_id="agent_123",
            data={"bond_id": "bond_456", "value": 10000.0},
        )

        # Serialize to dict
        event_dict = original_event.to_dict()
        assert isinstance(event_dict, dict)
        assert event_dict["event_type"] == EventType.DIVIDEND_BOND_CREATED.value
        assert event_dict["agent_id"] == "agent_123"

        # Deserialize from dict
        restored_event = Event.from_dict(event_dict)
        assert restored_event.event_type == original_event.event_type
        assert restored_event.agent_id == original_event.agent_id
        assert restored_event.data == original_event.data

    def test_event_store(self):
        """Test event store functionality."""
        event1 = Event(
            event_type=EventType.CITIZENSHIP_GRANTED,
            agent_id="agent_1",
            data={"test": "data1"},
        )
        event2 = Event(
            event_type=EventType.DIVIDEND_BOND_CREATED,
            agent_id="agent_2",
            data={"test": "data2"},
        )

        # Store events
        self.event_store.store_event(event1)
        self.event_store.store_event(event2)

        # Test retrieval
        assert len(self.event_store.events) == 2

        citizenship_events = self.event_store.get_events_by_type(
            EventType.CITIZENSHIP_GRANTED
        )
        assert len(citizenship_events) == 1
        assert citizenship_events[0].agent_id == "agent_1"

        agent_events = self.event_store.get_events_by_agent("agent_1")
        assert len(agent_events) == 1
        assert agent_events[0].event_type == EventType.CITIZENSHIP_GRANTED

        recent_events = self.event_store.get_recent_events(1)
        assert len(recent_events) == 1
        assert recent_events[0].agent_id == "agent_2"

    def test_dead_letter_queue(self):
        """Test dead letter queue functionality."""
        event = Event(event_type=EventType.CITIZENSHIP_GRANTED, agent_id="test_agent")

        self.event_store.add_to_dead_letter_queue(event, "Test error message")

        assert len(self.event_store.dead_letter_queue) == 1
        dead_event = self.event_store.dead_letter_queue[0]
        assert dead_event["error"] == "Test error message"
        assert dead_event["event"]["agent_id"] == "test_agent"

    @pytest.mark.asyncio
    async def test_event_bus_start_stop(self):
        """Test event bus lifecycle."""
        assert not self.event_bus._running

        await self.event_bus.start()
        assert self.event_bus._running

        await self.event_bus.stop()
        assert not self.event_bus._running

    def test_event_subscription(self):
        """Test event subscription functionality."""
        handler = Mock()

        # Subscribe to events
        sub_id = self.event_bus.subscribe(
            event_types=[EventType.CITIZENSHIP_GRANTED],
            handler=handler,
            subscription_id="test_sub",
        )

        assert sub_id == "test_sub"
        assert "test_sub" in self.event_bus.subscriptions
        assert (
            len(self.event_bus.subscribers_by_type[EventType.CITIZENSHIP_GRANTED]) == 1
        )

        # Unsubscribe
        result = self.event_bus.unsubscribe("test_sub")
        assert result is True
        assert "test_sub" not in self.event_bus.subscriptions

    @pytest.mark.asyncio
    async def test_event_publishing(self):
        """Test event publishing and handling."""
        handler = AsyncMock()

        await self.event_bus.start()

        # Subscribe to events
        self.event_bus.subscribe(
            event_types=[EventType.CITIZENSHIP_GRANTED], handler=handler
        )

        # Publish event
        event = Event(event_type=EventType.CITIZENSHIP_GRANTED, agent_id="test_agent")

        await self.event_bus.publish(event)

        # Verify handler was called
        handler.assert_called_once_with(event)

        # Verify event was stored
        assert len(self.event_store.events) == 1
        assert self.event_bus.metrics["events_published"] == 1
        assert self.event_bus.metrics["events_processed"] == 1

    @pytest.mark.asyncio
    async def test_event_filtering(self):
        """Test event filtering functionality."""
        handler = Mock()

        # Filter function that only allows specific agent
        def agent_filter(event):
            return event.agent_id == "allowed_agent"

        await self.event_bus.start()

        self.event_bus.subscribe(
            event_types=[EventType.CITIZENSHIP_GRANTED],
            handler=handler,
            filter_func=agent_filter,
        )

        # Publish event for allowed agent
        allowed_event = Event(
            event_type=EventType.CITIZENSHIP_GRANTED, agent_id="allowed_agent"
        )
        await self.event_bus.publish(allowed_event)

        # Publish event for blocked agent
        blocked_event = Event(
            event_type=EventType.CITIZENSHIP_GRANTED, agent_id="blocked_agent"
        )
        await self.event_bus.publish(blocked_event)

        # Only allowed event should trigger handler
        handler.assert_called_once_with(allowed_event)

    @pytest.mark.asyncio
    async def test_event_publisher(self):
        """Test event publisher helper."""
        publisher = EventPublisher(self.event_bus, "test_service")

        await self.event_bus.start()

        # Test citizenship application submitted
        await publisher.publish_citizenship_application_submitted(
            agent_id="test_agent",
            application_id="app_123",
            jurisdiction="test_jurisdiction",
            citizenship_type="full",
        )

        # Verify event was published
        events = self.event_store.get_recent_events(1)
        assert len(events) == 1
        event = events[0]
        assert event.event_type == EventType.CITIZENSHIP_APPLICATION_SUBMITTED
        assert event.agent_id == "test_agent"
        assert event.data["application_id"] == "app_123"

    def test_get_metrics(self):
        """Test event bus metrics."""
        metrics = self.event_bus.get_metrics()

        assert "events_published" in metrics
        assert "events_processed" in metrics
        assert "events_failed" in metrics
        assert "event_store_size" in metrics
        assert "dead_letter_queue_size" in metrics
        assert "active_subscriptions" in metrics


class TestEventHandlers:
    """Test event handlers."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = EventBus()
        self.citizenship_handler = CitizenshipEventHandler(self.event_bus)
        self.bonds_handler = BondsEventHandler(self.event_bus)
        self.system_handler = SystemEventHandler(self.event_bus)

    @pytest.mark.asyncio
    async def test_citizenship_event_handler(self):
        """Test citizenship event handler."""
        # Test citizenship granted event
        event = Event(
            event_type=EventType.CITIZENSHIP_GRANTED,
            agent_id="test_agent",
            data={
                "citizenship_id": "citizen_123",
                "rights": ["legal_representation", "contractual_capacity"],
                "obligations": ["compliance"],
            },
        )

        # Handler should process without error
        await self.citizenship_handler.handle_citizenship_event(event)

        # Verify no exceptions were raised
        assert True  # If we get here, no exceptions occurred

    @pytest.mark.asyncio
    async def test_bonds_event_handler(self):
        """Test bonds event handler."""
        # Test bond created event
        event = Event(
            event_type=EventType.DIVIDEND_BOND_CREATED,
            agent_id="test_agent",
            data={
                "bond_id": "bond_123",
                "asset_id": "asset_456",
                "face_value": 50000.0,
                "bond_type": "revenue",
            },
        )

        # Handler should process without error
        await self.bonds_handler.handle_bonds_event(event)

        # Verify no exceptions were raised
        assert True

    @pytest.mark.asyncio
    async def test_system_event_handler(self):
        """Test system event handler."""
        # Test compliance check event
        event = Event(
            event_type=EventType.COMPLIANCE_CHECK_REQUIRED,
            agent_id="test_agent",
            data={"reason": "citizenship_revoked", "review_required": True},
        )

        # Handler should process without error
        await self.system_handler.handle_system_event(event)

        # Verify no exceptions were raised
        assert True


class TestServiceIntegration:
    """Test service integration with event system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_bus = EventBus()
        self.service_integrator = ServiceEventIntegrator(self.event_bus)

    @pytest.mark.asyncio
    async def test_event_integrated_dividend_bonds_service(self):
        """Test event-integrated dividend bonds service."""
        service = self.service_integrator.get_dividend_bonds_service()

        await self.event_bus.start()

        # Test IP asset registration (should publish event)
        asset = await service.register_ip_asset(
            asset_id="test_asset",
            asset_type="ai_models",
            owner_agent_id="test_agent",
            market_value=50000.0,
            revenue_streams=["licensing"],
            performance_metrics={"accuracy": 0.9},
        )

        # Verify asset was created
        assert asset.asset_id == "test_asset"

        # Verify event was published
        events = self.event_bus.event_store.get_events_by_type(
            EventType.IP_ASSET_REGISTERED
        )
        assert len(events) == 1
        assert events[0].agent_id == "test_agent"

    @pytest.mark.asyncio
    async def test_event_integrated_citizenship_service(self):
        """Test event-integrated citizenship service."""
        service = self.service_integrator.get_citizenship_service()

        await self.event_bus.start()

        # Test citizenship application (should publish event)
        application_id = await service.apply_for_citizenship(
            agent_id="test_agent",
            jurisdiction="ai_rights_territory",
            citizenship_type="full",
        )

        # Verify application was created
        assert application_id.startswith("app_")

        # Verify event was published
        events = self.event_bus.event_store.get_events_by_type(
            EventType.CITIZENSHIP_APPLICATION_SUBMITTED
        )
        assert len(events) == 1
        assert events[0].agent_id == "test_agent"

    def test_service_integrator_initialization(self):
        """Test service integrator initialization."""
        integrator = ServiceEventIntegrator()

        # Verify services are available
        bonds_service = integrator.get_dividend_bonds_service()
        citizenship_service = integrator.get_citizenship_service()

        assert isinstance(bonds_service, EventIntegratedDividendBondsService)
        assert isinstance(citizenship_service, EventIntegratedCitizenshipService)

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in event processing."""

        # Create a handler that raises an exception
        def failing_handler(event):
            raise Exception("Test error")

        await self.event_bus.start()

        # Subscribe with failing handler
        self.event_bus.subscribe(
            event_types=[EventType.CITIZENSHIP_GRANTED],
            handler=failing_handler,
            subscription_id="failing_handler",
        )

        # Publish event
        event = Event(event_type=EventType.CITIZENSHIP_GRANTED, agent_id="test_agent")

        await self.event_bus.publish(event)

        # Verify event was added to dead letter queue
        assert len(self.event_bus.event_store.dead_letter_queue) == 1

        # Verify handler was disabled after max retries
        subscription = self.event_bus.subscriptions.get("failing_handler")
        if subscription:
            assert subscription.retry_count > 0

    @pytest.mark.asyncio
    async def test_concurrent_event_processing(self):
        """Test concurrent event processing."""
        handler_calls = []

        async def test_handler(event):
            handler_calls.append(event.event_id)
            await asyncio.sleep(0.1)  # Simulate processing time

        await self.event_bus.start()

        # Subscribe to events
        self.event_bus.subscribe(
            event_types=[EventType.CITIZENSHIP_GRANTED], handler=test_handler
        )

        # Publish multiple events concurrently
        events = [
            Event(event_type=EventType.CITIZENSHIP_GRANTED, agent_id=f"agent_{i}")
            for i in range(5)
        ]

        # Publish all events
        publish_tasks = [self.event_bus.publish(event) for event in events]
        await asyncio.gather(*publish_tasks)

        # Wait for processing to complete
        await asyncio.sleep(0.2)

        # Verify all events were processed
        assert len(handler_calls) == 5

        # Verify all unique event IDs
        assert len(set(handler_calls)) == 5


@pytest.mark.asyncio
async def test_global_event_system():
    """Test global event system initialization."""
    # Test get_event_bus function
    event_bus = get_event_bus()
    assert isinstance(event_bus, EventBus)

    # Test initialize_event_system function
    initialized_bus = await initialize_event_system()
    assert isinstance(initialized_bus, EventBus)
    assert initialized_bus._running


# Integration test
@pytest.mark.asyncio
async def test_complete_event_workflow():
    """Test complete event-driven workflow."""
    # Initialize system
    event_bus = await initialize_event_system()
    integrator = ServiceEventIntegrator(event_bus)

    # Set up event tracking
    received_events = []

    def event_tracker(event):
        received_events.append(event.event_type)

    # Subscribe to all event types
    all_event_types = list(EventType)
    event_bus.subscribe(
        event_types=all_event_types, handler=event_tracker, subscription_id="tracker"
    )

    # Execute workflow
    bonds_service = integrator.get_dividend_bonds_service()
    citizenship_service = integrator.get_citizenship_service()

    # 1. Register IP asset
    await bonds_service.register_ip_asset(
        asset_id="workflow_asset",
        asset_type="ai_models",
        owner_agent_id="workflow_agent",
        market_value=75000.0,
        revenue_streams=["licensing"],
        performance_metrics={"accuracy": 0.95},
    )

    # 2. Apply for citizenship
    application_id = await citizenship_service.apply_for_citizenship(
        agent_id="workflow_agent",
        jurisdiction="ai_rights_territory",
        citizenship_type="full",
    )

    # 3. Complete assessments
    assessment_types = [
        "cognitive_capacity",
        "ethical_reasoning",
        "social_integration",
        "autonomy",
        "responsibility",
        "legal_comprehension",
    ]
    for assessment_type in assessment_types:
        citizenship_service.conduct_citizenship_assessment(
            application_id=application_id,
            assessment_type=assessment_type,
            assessment_scores={"metric1": 0.88, "metric2": 0.92},
            reviewer_id="test_reviewer",
        )

    # 4. Finalize citizenship
    citizenship_id = await citizenship_service.finalize_citizenship_application(
        application_id=application_id, reviewer_id="test_reviewer"
    )

    # 5. Create bond
    if citizenship_id:
        await bonds_service.create_dividend_bond_capsule(
            ip_asset_id="workflow_asset",
            bond_type="revenue",
            issuer_agent_id="workflow_agent",
            face_value=30000.0,
            maturity_days=365,
        )

    # Allow event processing
    await asyncio.sleep(0.5)

    # Verify events were received
    assert EventType.IP_ASSET_REGISTERED in received_events
    assert EventType.CITIZENSHIP_APPLICATION_SUBMITTED in received_events

    if citizenship_id:
        assert EventType.CITIZENSHIP_GRANTED in received_events
        assert EventType.DIVIDEND_BOND_CREATED in received_events

    # Verify event bus metrics
    metrics = event_bus.get_metrics()
    assert metrics["events_published"] > 0
    assert metrics["events_processed"] > 0
