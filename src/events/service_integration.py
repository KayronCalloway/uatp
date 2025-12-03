"""
Service Integration for Event-Driven Architecture
================================================

This module provides integration between existing UATP services and the
event system, enabling automatic event publishing when service actions occur.
"""

import logging
from typing import Optional, Dict, Any
from functools import wraps

from .event_system import EventBus, EventPublisher, get_event_bus
from src.services.dividend_bonds_service import dividend_bonds_service
from src.services.citizenship_service import citizenship_service

logger = logging.getLogger(__name__)


class EventIntegratedDividendBondsService:
    """Wrapper for DividendBondsService that publishes events."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()
        self.publisher = EventPublisher(self.event_bus, "dividend_bonds_service")
        self.service = dividend_bonds_service

    async def register_ip_asset(
        self,
        asset_id: str,
        asset_type: str,
        owner_agent_id: str,
        market_value: float,
        revenue_streams: list,
        performance_metrics: dict,
    ):
        """Register IP asset and publish event."""
        # Call original service
        asset = self.service.register_ip_asset(
            asset_id=asset_id,
            asset_type=asset_type,
            owner_agent_id=owner_agent_id,
            market_value=market_value,
            revenue_streams=revenue_streams,
            performance_metrics=performance_metrics,
        )

        # Publish event
        await self.publisher.publish_ip_asset_registered(
            agent_id=owner_agent_id,
            asset_id=asset_id,
            asset_type=asset_type,
            market_value=market_value,
        )

        return asset

    async def create_dividend_bond_capsule(
        self,
        ip_asset_id: str,
        bond_type: str,
        issuer_agent_id: str,
        face_value: float,
        maturity_days: int,
        coupon_rate: Optional[float] = None,
        minimum_investment: Optional[float] = None,
    ):
        """Create dividend bond and publish event."""
        # Call original service
        capsule = self.service.create_dividend_bond_capsule(
            ip_asset_id=ip_asset_id,
            bond_type=bond_type,
            issuer_agent_id=issuer_agent_id,
            face_value=face_value,
            maturity_days=maturity_days,
            coupon_rate=coupon_rate,
            minimum_investment=minimum_investment,
        )

        # Publish event
        await self.publisher.publish_dividend_bond_created(
            agent_id=issuer_agent_id,
            bond_id=capsule.dividend_bond.bond_id,
            asset_id=ip_asset_id,
            face_value=face_value,
            bond_type=bond_type,
        )

        return capsule

    async def process_dividend_payment(
        self,
        bond_id: str,
        payment_amount: float,
        payment_source: str,
        recipient_agent_id: str,
    ):
        """Process dividend payment and publish event."""
        # Call original service
        payment = self.service.process_dividend_payment(
            bond_id=bond_id,
            payment_amount=payment_amount,
            payment_source=payment_source,
            recipient_agent_id=recipient_agent_id,
        )

        # Get bond info to find issuer
        bonds = self.service.get_active_bonds()
        bond_info = next((b for b in bonds if b["bond_id"] == bond_id), None)
        issuer_agent_id = bond_info["issuer_agent_id"] if bond_info else "unknown"

        # Publish event
        await self.publisher.publish_dividend_payment_processed(
            agent_id=issuer_agent_id,
            bond_id=bond_id,
            payment_id=payment.payment_id,
            amount=payment_amount,
            recipient=recipient_agent_id,
        )

        return payment

    # Delegate all other methods to the original service
    def __getattr__(self, name):
        return getattr(self.service, name)


class EventIntegratedCitizenshipService:
    """Wrapper for CitizenshipService that publishes events."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()
        self.publisher = EventPublisher(self.event_bus, "citizenship_service")
        self.service = citizenship_service

    async def apply_for_citizenship(
        self,
        agent_id: str,
        jurisdiction: str,
        citizenship_type: str = "full",
        supporting_evidence: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Apply for citizenship and publish event."""
        # Call original service
        application_id = self.service.apply_for_citizenship(
            agent_id=agent_id,
            jurisdiction=jurisdiction,
            citizenship_type=citizenship_type,
            supporting_evidence=supporting_evidence,
        )

        # Publish event
        await self.publisher.publish_citizenship_application_submitted(
            agent_id=agent_id,
            application_id=application_id,
            jurisdiction=jurisdiction,
            citizenship_type=citizenship_type,
        )

        return application_id

    async def finalize_citizenship_application(
        self, application_id: str, reviewer_id: str
    ) -> Optional[str]:
        """Finalize citizenship application and publish event."""
        # Call original service
        citizenship_id = self.service.finalize_citizenship_application(
            application_id=application_id, reviewer_id=reviewer_id
        )

        # Get application details
        pending_apps = self.service.get_pending_applications()
        application = None
        for app in pending_apps:
            if app["application_id"] == application_id:
                application = app
                break

        # If application not in pending (was processed), get from registry
        if not application and citizenship_id:
            # Application was approved and moved to active citizenships
            for (
                agent_id,
                citizenship,
            ) in self.service.citizenship_registry.active_citizenships.items():
                if citizenship.get("citizenship_id") == citizenship_id:
                    application = {
                        "agent_id": agent_id,
                        "jurisdiction": citizenship["jurisdiction"],
                    }
                    break

        if citizenship_id and application:
            # Get jurisdiction info
            jurisdiction_obj = self.service.jurisdictions.get(
                application["jurisdiction"]
            )
            rights = jurisdiction_obj.rights_granted if jurisdiction_obj else []
            obligations = jurisdiction_obj.obligations if jurisdiction_obj else []

            # Publish citizenship granted event
            await self.publisher.publish_citizenship_granted(
                agent_id=application["agent_id"],
                citizenship_id=citizenship_id,
                jurisdiction=application["jurisdiction"],
                rights=rights,
                obligations=obligations,
            )

        return citizenship_id

    async def revoke_citizenship(
        self, agent_id: str, reason: str, authority_id: str
    ) -> bool:
        """Revoke citizenship and publish event."""
        # Get current citizenship info before revocation
        citizenship_status = self.service.get_citizenship_status(agent_id)

        # Call original service
        result = self.service.revoke_citizenship(
            agent_id=agent_id, reason=reason, authority_id=authority_id
        )

        if result and citizenship_status:
            # Publish citizenship revoked event
            from .event_system import Event, EventType

            event = Event(
                event_type=EventType.CITIZENSHIP_REVOKED,
                source_service="citizenship_service",
                agent_id=agent_id,
                data={
                    "citizenship_id": citizenship_status["citizenship_id"],
                    "jurisdiction": citizenship_status["jurisdiction"],
                    "reason": reason,
                    "authority_id": authority_id,
                },
            )
            await self.event_bus.publish(event)

        return result

    # Delegate all other methods to the original service
    def __getattr__(self, name):
        return getattr(self.service, name)


class ServiceEventIntegrator:
    """Main class for integrating services with the event system."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()

        # Create event-integrated service wrappers
        self.dividend_bonds_service = EventIntegratedDividendBondsService(
            self.event_bus
        )
        self.citizenship_service = EventIntegratedCitizenshipService(self.event_bus)

        logger.info("Service event integration initialized")

    def get_dividend_bonds_service(self) -> EventIntegratedDividendBondsService:
        """Get event-integrated dividend bonds service."""
        return self.dividend_bonds_service

    def get_citizenship_service(self) -> EventIntegratedCitizenshipService:
        """Get event-integrated citizenship service."""
        return self.citizenship_service


# Global service integrator instance
_global_service_integrator: Optional[ServiceEventIntegrator] = None


def get_service_integrator() -> ServiceEventIntegrator:
    """Get the global service integrator instance."""
    global _global_service_integrator
    if _global_service_integrator is None:
        _global_service_integrator = ServiceEventIntegrator()
    return _global_service_integrator


# Convenience functions for backward compatibility
def get_event_integrated_dividend_bonds_service() -> (
    EventIntegratedDividendBondsService
):
    """Get event-integrated dividend bonds service."""
    return get_service_integrator().get_dividend_bonds_service()


def get_event_integrated_citizenship_service() -> EventIntegratedCitizenshipService:
    """Get event-integrated citizenship service."""
    return get_service_integrator().get_citizenship_service()
