"""
Event Handlers for Cross-Service Integration
===========================================

This module contains event handlers that enable cross-service integration
and automated workflows between Dividend Bonds and Citizenship services.
"""

import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timezone

from .event_system import Event, EventType, EventBus, EventPublisher
from src.services.dividend_bonds_service import dividend_bonds_service
from src.services.citizenship_service import citizenship_service

logger = logging.getLogger(__name__)


class CitizenshipEventHandler:
    """Handles citizenship-related events and triggers cross-service actions."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.publisher = EventPublisher(event_bus, "citizenship_handler")
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        """Set up event subscriptions."""
        # Subscribe to citizenship events
        self.event_bus.subscribe(
            event_types=[
                EventType.CITIZENSHIP_GRANTED,
                EventType.CITIZENSHIP_REVOKED,
                EventType.CITIZENSHIP_STATUS_UPDATED,
            ],
            handler=self.handle_citizenship_event,
            subscription_id="citizenship_handler",
        )

        # Subscribe to IP asset events for citizenship qualification
        self.event_bus.subscribe(
            event_types=[EventType.IP_ASSET_REGISTERED],
            handler=self.handle_asset_registration,
            subscription_id="citizenship_asset_handler",
        )

    async def handle_citizenship_event(self, event: Event) -> None:
        """Handle citizenship-related events."""
        try:
            if event.event_type == EventType.CITIZENSHIP_GRANTED:
                await self._on_citizenship_granted(event)
            elif event.event_type == EventType.CITIZENSHIP_REVOKED:
                await self._on_citizenship_revoked(event)
            elif event.event_type == EventType.CITIZENSHIP_STATUS_UPDATED:
                await self._on_citizenship_status_updated(event)
        except Exception as e:
            logger.error(f"Error handling citizenship event {event.event_id}: {e}")

    async def _on_citizenship_granted(self, event: Event) -> None:
        """Handle citizenship granted event."""
        agent_id = event.agent_id
        rights = event.data.get("rights", [])

        logger.info(f"Processing citizenship granted for agent {agent_id}")

        # Publish agent rights updated event
        await self.publisher.publish_agent_rights_updated(
            agent_id=agent_id, new_rights=rights, context="citizenship_granted"
        )

        # Check if agent qualifies for bond creation privileges
        if "legal_representation" in rights and "contractual_capacity" in rights:
            logger.info(f"Agent {agent_id} now qualifies for bond creation")

            # Trigger bond eligibility check
            await self._check_bond_eligibility(agent_id)

    async def _on_citizenship_revoked(self, event: Event) -> None:
        """Handle citizenship revoked event."""
        agent_id = event.agent_id

        logger.info(f"Processing citizenship revocation for agent {agent_id}")

        # Get active bonds for this agent
        active_bonds = dividend_bonds_service.get_active_bonds(agent_id)

        if active_bonds:
            logger.warning(
                f"Agent {agent_id} has {len(active_bonds)} active bonds - review required"
            )

            # Trigger compliance check
            compliance_event = Event(
                event_type=EventType.COMPLIANCE_CHECK_REQUIRED,
                source_service="citizenship_handler",
                agent_id=agent_id,
                data={
                    "reason": "citizenship_revoked",
                    "active_bonds": [bond["bond_id"] for bond in active_bonds],
                    "review_required": True,
                },
            )
            await self.event_bus.publish(compliance_event)

    async def _on_citizenship_status_updated(self, event: Event) -> None:
        """Handle citizenship status update event."""
        agent_id = event.agent_id
        logger.info(f"Processing citizenship status update for agent {agent_id}")

        # Update agent's financial status based on citizenship changes
        await self._update_financial_status(agent_id)

    async def handle_asset_registration(self, event: Event) -> None:
        """Handle IP asset registration for citizenship qualification."""
        agent_id = event.agent_id
        asset_value = event.data.get("market_value", 0)

        # Check if this asset registration qualifies agent for citizenship upgrade
        if asset_value > 100000:  # High-value asset threshold
            logger.info(
                f"High-value asset registered for agent {agent_id}: ${asset_value:,.2f}"
            )

            # Check current citizenship status
            citizenship_status = citizenship_service.get_citizenship_status(agent_id)

            if not citizenship_status:
                logger.info(
                    f"Agent {agent_id} with high-value asset has no citizenship - suggesting application"
                )

                # Could trigger automated citizenship application recommendation
                # For demo purposes, we'll just log this
                logger.info(
                    f"Recommending citizenship application for agent {agent_id}"
                )

    async def _check_bond_eligibility(self, agent_id: str) -> None:
        """Check if agent is eligible for bond creation."""
        # Get agent's IP assets
        bonds = dividend_bonds_service.get_active_bonds(agent_id)

        if not bonds:
            logger.info(
                f"Agent {agent_id} has no bonds but now has rights - eligible for bond creation"
            )

            # Trigger bond creation suggestion (in real system, might notify agent)
            logger.info(f"Agent {agent_id} is now eligible to create dividend bonds")

    async def _update_financial_status(self, agent_id: str) -> None:
        """Update agent's financial status based on citizenship changes."""
        # Get current financial position
        bonds = dividend_bonds_service.get_active_bonds(agent_id)
        citizenship_status = citizenship_service.get_citizenship_status(agent_id)

        total_bond_value = sum(bond["face_value"] for bond in bonds)

        status_data = {
            "agent_id": agent_id,
            "total_bond_value": total_bond_value,
            "bond_count": len(bonds),
            "citizenship_active": citizenship_status is not None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Publish financial status change event
        financial_event = Event(
            event_type=EventType.FINANCIAL_STATUS_CHANGED,
            source_service="citizenship_handler",
            agent_id=agent_id,
            data=status_data,
        )
        await self.event_bus.publish(financial_event)


class BondsEventHandler:
    """Handles dividend bonds events and triggers cross-service actions."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.publisher = EventPublisher(event_bus, "bonds_handler")
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        """Set up event subscriptions."""
        # Subscribe to bonds events
        self.event_bus.subscribe(
            event_types=[
                EventType.DIVIDEND_BOND_CREATED,
                EventType.DIVIDEND_PAYMENT_PROCESSED,
                EventType.BOND_MATURED,
            ],
            handler=self.handle_bonds_event,
            subscription_id="bonds_handler",
        )

        # Subscribe to agent rights updates
        self.event_bus.subscribe(
            event_types=[EventType.AGENT_RIGHTS_UPDATED],
            handler=self.handle_rights_update,
            subscription_id="bonds_rights_handler",
        )

    async def handle_bonds_event(self, event: Event) -> None:
        """Handle bonds-related events."""
        try:
            if event.event_type == EventType.DIVIDEND_BOND_CREATED:
                await self._on_bond_created(event)
            elif event.event_type == EventType.DIVIDEND_PAYMENT_PROCESSED:
                await self._on_dividend_payment(event)
            elif event.event_type == EventType.BOND_MATURED:
                await self._on_bond_matured(event)
        except Exception as e:
            logger.error(f"Error handling bonds event {event.event_id}: {e}")

    async def _on_bond_created(self, event: Event) -> None:
        """Handle bond creation event."""
        agent_id = event.agent_id
        bond_id = event.data.get("bond_id")
        face_value = event.data.get("face_value")

        logger.info(f"Processing bond creation for agent {agent_id}: {bond_id}")

        # Update agent's financial status
        await self._update_agent_financial_profile(agent_id)

        # Check if bond creation affects citizenship scoring
        await self._assess_citizenship_impact(agent_id, face_value)

    async def _on_dividend_payment(self, event: Event) -> None:
        """Handle dividend payment event."""
        agent_id = event.agent_id
        amount = event.data.get("amount")

        logger.info(f"Processing dividend payment for agent {agent_id}: ${amount}")

        # Update financial tracking
        await self._track_dividend_income(agent_id, amount)

        # Check if payment patterns affect risk assessment
        await self._assess_payment_risk(agent_id)

    async def _on_bond_matured(self, event: Event) -> None:
        """Handle bond maturation event."""
        agent_id = event.agent_id
        bond_id = event.data.get("bond_id")

        logger.info(f"Processing bond maturation for agent {agent_id}: {bond_id}")

        # Update agent's portfolio
        await self._update_agent_financial_profile(agent_id)

    async def handle_rights_update(self, event: Event) -> None:
        """Handle agent rights updates affecting bond privileges."""
        agent_id = event.agent_id
        new_rights = event.data.get("new_rights", [])

        logger.info(f"Processing rights update for agent {agent_id}")

        # Check if new rights affect bond creation privileges
        if "contractual_capacity" in new_rights:
            logger.info(
                f"Agent {agent_id} gained contractual capacity - updating bond privileges"
            )

            # Update risk assessment for existing bonds
            bonds = dividend_bonds_service.get_active_bonds(agent_id)
            for bond in bonds:
                await self._reassess_bond_risk(bond["bond_id"])

    async def _update_agent_financial_profile(self, agent_id: str) -> None:
        """Update agent's financial profile."""
        bonds = dividend_bonds_service.get_active_bonds(agent_id)

        total_value = sum(bond["face_value"] for bond in bonds)
        total_dividends = 0

        for bond in bonds:
            performance = dividend_bonds_service.get_bond_performance(bond["bond_id"])
            total_dividends += performance["total_dividends_paid"]

        profile_data = {
            "agent_id": agent_id,
            "total_bond_value": total_value,
            "total_dividends_earned": total_dividends,
            "active_bonds_count": len(bonds),
            "financial_score": self._calculate_financial_score(
                total_value, total_dividends
            ),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Publish financial status update
        financial_event = Event(
            event_type=EventType.FINANCIAL_STATUS_CHANGED,
            source_service="bonds_handler",
            agent_id=agent_id,
            data=profile_data,
        )
        await self.event_bus.publish(financial_event)

    async def _assess_citizenship_impact(
        self, agent_id: str, bond_value: float
    ) -> None:
        """Assess if bond creation impacts citizenship status."""
        if bond_value > 50000:  # Significant bond value
            citizenship_status = citizenship_service.get_citizenship_status(agent_id)

            if citizenship_status and citizenship_status.get("renewal_required"):
                logger.info(
                    f"High-value bond creation may positively impact citizenship renewal for agent {agent_id}"
                )

                # Could trigger citizenship review process
                logger.info(
                    f"Suggesting citizenship review for economic contribution: agent {agent_id}"
                )

    async def _track_dividend_income(self, agent_id: str, amount: float) -> None:
        """Track dividend income for financial profiling."""
        # In a real system, this would update a financial tracking database
        logger.info(f"Tracking dividend income: agent {agent_id}, amount ${amount}")

    async def _assess_payment_risk(self, agent_id: str) -> None:
        """Assess payment patterns for risk evaluation."""
        bonds = dividend_bonds_service.get_active_bonds(agent_id)

        # Simple risk assessment based on payment consistency
        if len(bonds) > 3:  # Multiple bonds = higher complexity
            risk_event = Event(
                event_type=EventType.RISK_ASSESSMENT_UPDATED,
                source_service="bonds_handler",
                agent_id=agent_id,
                data={
                    "risk_factor": "multiple_bonds",
                    "bond_count": len(bonds),
                    "assessment_reason": "payment_pattern_analysis",
                },
            )
            await self.event_bus.publish(risk_event)

    async def _reassess_bond_risk(self, bond_id: str) -> None:
        """Reassess risk for a specific bond."""
        logger.info(f"Reassessing risk for bond {bond_id} due to rights update")

        # In a real system, this would update bond risk ratings
        # based on the issuer's updated legal status

    def _calculate_financial_score(
        self, total_value: float, total_dividends: float
    ) -> float:
        """Calculate a simple financial score."""
        if total_value == 0:
            return 0.0

        dividend_ratio = total_dividends / total_value

        # Simple scoring: base score + dividend performance
        base_score = min(total_value / 100000, 1.0)  # Normalize to 1.0 at $100K
        performance_score = min(dividend_ratio * 10, 1.0)  # Normalize dividend ratio

        return (base_score + performance_score) / 2


class SystemEventHandler:
    """Handles system-wide events and monitoring."""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.publisher = EventPublisher(event_bus, "system_handler")
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        """Set up event subscriptions."""
        # Subscribe to all events for monitoring
        self.event_bus.subscribe(
            event_types=[
                EventType.COMPLIANCE_CHECK_REQUIRED,
                EventType.RISK_ASSESSMENT_UPDATED,
                EventType.FINANCIAL_STATUS_CHANGED,
            ],
            handler=self.handle_system_event,
            subscription_id="system_monitor",
        )

    async def handle_system_event(self, event: Event) -> None:
        """Handle system-wide events."""
        try:
            if event.event_type == EventType.COMPLIANCE_CHECK_REQUIRED:
                await self._process_compliance_check(event)
            elif event.event_type == EventType.RISK_ASSESSMENT_UPDATED:
                await self._process_risk_update(event)
            elif event.event_type == EventType.FINANCIAL_STATUS_CHANGED:
                await self._process_financial_update(event)
        except Exception as e:
            logger.error(f"Error handling system event {event.event_id}: {e}")

    async def _process_compliance_check(self, event: Event) -> None:
        """Process compliance check requirements."""
        agent_id = event.agent_id
        reason = event.data.get("reason")

        logger.info(f"Processing compliance check for agent {agent_id}: {reason}")

        # In a real system, this would trigger regulatory compliance workflows
        # For demo, we just log the action
        logger.info(f"Compliance review initiated for agent {agent_id} due to {reason}")

    async def _process_risk_update(self, event: Event) -> None:
        """Process risk assessment updates."""
        agent_id = event.agent_id
        risk_factor = event.data.get("risk_factor")

        logger.info(f"Processing risk update for agent {agent_id}: {risk_factor}")

        # Could trigger automated risk mitigation workflows
        logger.info(f"Risk assessment updated for agent {agent_id}")

    async def _process_financial_update(self, event: Event) -> None:
        """Process financial status updates."""
        agent_id = event.agent_id
        financial_score = event.data.get("financial_score", 0)

        logger.info(
            f"Processing financial update for agent {agent_id}: score {financial_score:.2f}"
        )

        # Could trigger financial advisory or portfolio optimization


async def setup_event_handlers(event_bus: EventBus) -> Dict[str, Any]:
    """Set up all event handlers."""
    handlers = {
        "citizenship": CitizenshipEventHandler(event_bus),
        "bonds": BondsEventHandler(event_bus),
        "system": SystemEventHandler(event_bus),
    }

    logger.info("Event handlers initialized")
    return handlers
