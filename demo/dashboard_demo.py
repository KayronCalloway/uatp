#!/usr/bin/env python3
"""
AI Rights Dashboard Demo
========================

This demo showcases the AI Rights Dashboard with real-time analytics,
demonstrating comprehensive monitoring of AI agent rights, financial
performance, and system operations.

Features Demonstrated:
- Real-time dashboard with WebSocket updates
- Analytics engine with comprehensive metrics
- Agent activity monitoring
- Financial performance tracking
- Compliance and risk assessment
- Interactive web interface
"""

import asyncio
import logging
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.dashboard.analytics_engine import initialize_analytics_engine
from src.dashboard.web_dashboard import DashboardWebServer, create_dashboard_template
from src.events.event_handlers import setup_event_handlers
from src.events.event_system import initialize_event_system
from src.events.service_integration import get_service_integrator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format=" %(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("dashboard_demo")


class DashboardDemo:
    """Demonstrates AI Rights Dashboard with real-time analytics."""

    def __init__(self):
        self.event_bus = None
        self.handlers = None
        self.service_integrator = None
        self.analytics_engine = None
        self.dashboard_server = None
        self.demo_stats = {
            "agents_created": 0,
            "events_generated": 0,
            "workflows_executed": 0,
            "start_time": None,
        }

    async def setup(self):
        """Set up the dashboard and analytics system."""
        logger.info(" Setting up AI Rights Dashboard system")

        # Initialize event system
        self.event_bus = await initialize_event_system()

        # Set up event handlers
        self.handlers = await setup_event_handlers(self.event_bus)

        # Get service integrator
        self.service_integrator = get_service_integrator()

        # Initialize analytics engine
        self.analytics_engine = await initialize_analytics_engine(self.event_bus)

        # Create dashboard template
        create_dashboard_template()

        # Initialize dashboard server
        self.dashboard_server = DashboardWebServer(host="localhost", port=5000)
        await self.dashboard_server.initialize()

        self.demo_stats["start_time"] = datetime.now(timezone.utc)
        logger.info("[OK] Dashboard system ready")

    async def run_demo(self):
        """Run the complete dashboard demo."""
        logger.info("=" * 60)
        logger.info(" UATP AI Rights Dashboard Demo")
        logger.info("=" * 60)

        await self.setup()

        try:
            # Start dashboard server in background
            self.start_dashboard_server()

            # Wait for server to start
            await asyncio.sleep(2)

            logger.info(" Dashboard available at: http://localhost:5000")
            logger.info(" Starting real-time data generation...")

            # Generate demo data scenarios
            await self.scenario_1_agent_onboarding()
            await asyncio.sleep(2)

            await self.scenario_2_financial_activities()
            await asyncio.sleep(2)

            await self.scenario_3_compliance_events()
            await asyncio.sleep(2)

            await self.scenario_4_system_monitoring()
            await asyncio.sleep(2)

            await self.demo_summary()

            # Keep server running for interaction
            logger.info(" Dashboard server running - Press Ctrl+C to stop")
            logger.info(" Visit http://localhost:5000 to view the dashboard")

            try:
                while True:
                    await asyncio.sleep(5)
                    await self.generate_background_activity()
            except KeyboardInterrupt:
                logger.info(" Demo stopped by user")

        except Exception as e:
            logger.error(f"[ERROR] Demo failed: {e}")
            raise

    def start_dashboard_server(self):
        """Start the dashboard web server in a background thread."""

        def run_server():
            try:
                self.dashboard_server.start_real_time_updates()
                self.dashboard_server.run(debug=False)
            except Exception as e:
                logger.error(f"Dashboard server error: {e}")

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        logger.info(" Dashboard server started")

    async def scenario_1_agent_onboarding(self):
        """Scenario 1: Agent onboarding and citizenship workflow."""
        logger.info("\n SCENARIO 1: Agent Onboarding & Citizenship")
        logger.info("-" * 50)

        agents = [
            {
                "id": "ai_researcher_001",
                "specialty": "nlp_research",
                "portfolio": 120000,
            },
            {
                "id": "ai_trader_002",
                "specialty": "trading_algorithms",
                "portfolio": 250000,
            },
            {
                "id": "ai_creator_003",
                "specialty": "content_generation",
                "portfolio": 80000,
            },
            {"id": "ai_analyst_004", "specialty": "data_analysis", "portfolio": 180000},
        ]

        for agent in agents:
            agent_id = agent["id"]
            logger.info(f" Onboarding agent {agent_id}")

            # Register IP assets
            await self.service_integrator.dividend_bonds_service.register_ip_asset(
                asset_id=f"{agent_id}_primary_asset",
                asset_type="ai_models",
                owner_agent_id=agent_id,
                market_value=agent["portfolio"],
                revenue_streams=["licensing", "usage_fees"],
                performance_metrics={"quality": 0.85 + (len(agent_id) % 10) * 0.01},
            )

            # Apply for citizenship
            application_id = (
                await self.service_integrator.citizenship_service.apply_for_citizenship(
                    agent_id=agent_id,
                    jurisdiction="ai_rights_territory",
                    citizenship_type="full",
                    supporting_evidence={"specialty": agent["specialty"]},
                )
            )

            # Complete assessments
            assessment_scores = {
                "metric1": 0.82 + (len(agent_id) % 5) * 0.03,
                "metric2": 0.88 + (len(agent_id) % 3) * 0.02,
            }
            for assessment_type in [
                "cognitive_capacity",
                "ethical_reasoning",
                "social_integration",
                "autonomy",
                "responsibility",
                "legal_comprehension",
            ]:
                self.service_integrator.citizenship_service.conduct_citizenship_assessment(
                    application_id=application_id,
                    assessment_type=assessment_type,
                    assessment_scores=assessment_scores,
                    reviewer_id="demo_authority",
                )

            # Finalize citizenship
            citizenship_id = await self.service_integrator.citizenship_service.finalize_citizenship_application(
                application_id=application_id, reviewer_id="demo_authority"
            )

            if citizenship_id:
                logger.info(f"   [OK] Citizenship granted: {citizenship_id}")

            self.demo_stats["agents_created"] += 1
            self.demo_stats["events_generated"] += (
                4  # Asset, application, assessments, citizenship
            )

            await asyncio.sleep(0.5)

    async def scenario_2_financial_activities(self):
        """Scenario 2: Financial activities and bond operations."""
        logger.info("\n SCENARIO 2: Financial Activities & Bond Operations")
        logger.info("-" * 50)

        financial_activities = [
            {"agent": "ai_researcher_001", "bond_value": 50000, "type": "revenue"},
            {"agent": "ai_trader_002", "bond_value": 100000, "type": "performance"},
            {"agent": "ai_analyst_004", "bond_value": 75000, "type": "royalty"},
        ]

        for activity in financial_activities:
            agent_id = activity["agent"]
            logger.info(f" Creating bond for {agent_id}")

            # Create dividend bond
            bond_capsule = await self.service_integrator.dividend_bonds_service.create_dividend_bond_capsule(
                ip_asset_id=f"{agent_id}_primary_asset",
                bond_type=activity["type"],
                issuer_agent_id=agent_id,
                face_value=activity["bond_value"],
                maturity_days=365,
                coupon_rate=0.06 + (len(agent_id) % 3) * 0.01,
            )

            bond_id = bond_capsule.dividend_bond.bond_id

            # Process dividend payments
            for i in range(2):
                payment_amount = activity["bond_value"] * 0.01 * (1 + i * 0.1)
                await self.service_integrator.dividend_bonds_service.process_dividend_payment(
                    bond_id=bond_id,
                    payment_amount=payment_amount,
                    payment_source=f"{activity['type']}_stream",
                    recipient_agent_id=f"investor_{i+1}",
                )
                logger.info(f"    Dividend payment: ${payment_amount:.2f}")

            self.demo_stats["events_generated"] += 3  # Bond creation + 2 payments
            self.demo_stats["workflows_executed"] += 1

            await asyncio.sleep(0.7)

    async def scenario_3_compliance_events(self):
        """Scenario 3: Compliance monitoring and risk events."""
        logger.info("\n SCENARIO 3: Compliance Monitoring & Risk Events")
        logger.info("-" * 50)

        # Simulate compliance issues
        compliance_scenarios = [
            {
                "agent": "ai_trader_002",
                "issue": "high_risk_trading",
                "severity": "medium",
            },
            {
                "agent": "ai_creator_003",
                "issue": "content_policy_violation",
                "severity": "low",
            },
        ]

        for scenario in compliance_scenarios:
            agent_id = scenario["agent"]
            logger.info(f"[WARN] Compliance issue for {agent_id}: {scenario['issue']}")

            # Simulate compliance check
            from src.events.event_system import EventPublisher

            publisher = EventPublisher(self.event_bus, "compliance_system")

            await publisher.publish_compliance_check_required(
                agent_id=agent_id,
                reason=scenario["issue"],
                severity=scenario["severity"],
                review_deadline=datetime.now(timezone.utc),
            )

            # Simulate risk assessment update
            await publisher.publish_risk_assessment_updated(
                agent_id=agent_id,
                risk_factors=[scenario["issue"]],
                risk_score=0.3 + (len(scenario["issue"]) % 10) * 0.05,
                assessment_date=datetime.now(timezone.utc),
            )

            self.demo_stats["events_generated"] += 2

            await asyncio.sleep(0.5)

    async def scenario_4_system_monitoring(self):
        """Scenario 4: System health and monitoring events."""
        logger.info("\n SCENARIO 4: System Health & Monitoring")
        logger.info("-" * 50)

        # Generate system events
        from src.events.event_system import Event, EventPublisher, EventType

        publisher = EventPublisher(self.event_bus, "system_monitor")

        # Service health checks
        services = ["dividend_bonds_service", "citizenship_service", "analytics_engine"]
        for service in services:
            logger.info(f" Health check: {service}")

            # Publish service started event
            await self.event_bus.publish(
                Event(
                    event_type=EventType.SERVICE_STARTED,
                    source_service=service,
                    data={
                        "service_name": service,
                        "version": "1.0.0",
                        "startup_time": datetime.now(timezone.utc).isoformat(),
                    },
                )
            )

            self.demo_stats["events_generated"] += 1
            await asyncio.sleep(0.3)

    async def generate_background_activity(self):
        """Generate background activity for real-time dashboard updates."""
        # Generate random events to keep dashboard active
        import random

        from src.events.event_system import Event, EventType

        # Random agent activity
        agents = [f"ai_agent_{i:03d}" for i in range(10, 20)]
        random_agent = random.choice(agents)

        event_types = [
            EventType.AGENT_RIGHTS_UPDATED,
            EventType.FINANCIAL_STATUS_CHANGED,
            EventType.SYSTEM_HEALTH_CHECK,
        ]

        random_event_type = random.choice(event_types)

        event = Event(
            event_type=random_event_type,
            source_service="background_activity",
            agent_id=random_agent,
            data={
                "activity_type": "routine_update",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "value": random.uniform(1000, 50000),
            },
        )

        await self.event_bus.publish(event)

    async def demo_summary(self):
        """Display demo summary and analytics."""
        logger.info("\n DASHBOARD DEMO SUMMARY")
        logger.info("=" * 50)

        # Get analytics engine stats
        stats = await self.analytics_engine.get_dashboard_stats(force_refresh=True)

        # Calculate demo duration
        duration = (
            datetime.now(timezone.utc) - self.demo_stats["start_time"]
        ).total_seconds()

        logger.info(f" Demo Duration: {duration:.1f} seconds")
        logger.info(f" Total Agents: {stats.total_agents}")
        logger.info(f" Active Citizens: {stats.active_citizens}")
        logger.info(f" Total Asset Value: ${stats.total_asset_value:,.2f}")
        logger.info(f" Active Bonds: {stats.active_bonds}")
        logger.info(f" Total Dividends: ${stats.total_dividends_paid:,.2f}")
        logger.info(f" Average Yield: {stats.average_yield:.2%}")
        logger.info(f" Total Events: {stats.total_events}")
        logger.info(f" Events/Minute: {stats.events_per_minute:.1f}")
        logger.info(f" Compliance Issues: {stats.compliance_issues}")

        logger.info("\n Dashboard Features Demonstrated:")
        logger.info("   [OK] Real-time analytics engine")
        logger.info("   [OK] WebSocket-based live updates")
        logger.info("   [OK] Comprehensive metrics collection")
        logger.info("   [OK] Agent activity monitoring")
        logger.info("   [OK] Financial performance tracking")
        logger.info("   [OK] Compliance and risk assessment")
        logger.info("   [OK] Interactive web interface")
        logger.info("   [OK] Data export functionality")
        logger.info("   [OK] System health monitoring")

        logger.info("\n Key Analytics Capabilities:")
        logger.info("    Agent performance trends")
        logger.info("    Financial portfolio analysis")
        logger.info("    Risk assessment scoring")
        logger.info("    Compliance monitoring")
        logger.info("    Real-time event processing")
        logger.info("    Activity audit trails")
        logger.info("    Custom metrics aggregation")

        # Display top performing assets
        if stats.top_performing_assets:
            logger.info("\n Top Performing Assets:")
            for i, asset in enumerate(stats.top_performing_assets[:3], 1):
                logger.info(
                    f"   {i}. {asset['asset_id']}: ${asset['market_value']:,.2f}"
                )

        # Display recent activity
        if stats.recent_activity:
            logger.info(
                f"\n Recent Agent Activity ({len(stats.recent_activity)} agents):"
            )
            for activity in stats.recent_activity[:5]:
                logger.info(
                    f"   • {activity['agent_id']}: {activity['total_activities']} activities"
                )


async def main():
    """Main demo execution."""
    demo = DashboardDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
