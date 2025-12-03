#!/usr/bin/env python3
"""
Workflow Automation Demo
========================

This demo showcases the comprehensive workflow automation capabilities of the
UATP Capsule Engine, demonstrating complex business processes executed across
multiple services with conditional logic, parallel execution, and error handling.

Features Demonstrated:
- Agent onboarding workflow with parallel assessments
- Bond issuance workflow with eligibility checks
- Compliance review workflow with automated remediation
- Asset performance monitoring workflow
- Workflow orchestration and monitoring
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.events.event_system import initialize_event_system
from src.events.event_handlers import setup_event_handlers
from src.events.service_integration import get_service_integrator
from src.workflows import (
    initialize_workflow_engine,
    register_predefined_workflows,
    ValidationService,
    RiskAssessmentService,
    ComplianceService,
    AnalyticsService,
    NotificationService,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="⚙️ %(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("workflow_demo")


class WorkflowAutomationDemo:
    """Demonstrates comprehensive workflow automation capabilities."""

    def __init__(self):
        self.event_bus = None
        self.workflow_engine = None
        self.service_integrator = None
        self.workflow_services = {}
        self.demo_stats = {
            "workflows_executed": 0,
            "steps_completed": 0,
            "services_registered": 0,
            "start_time": None,
        }

    async def setup(self):
        """Set up the workflow automation system."""
        logger.info("🚀 Setting up workflow automation system")

        # Initialize event system
        self.event_bus = await initialize_event_system()

        # Set up event handlers
        await setup_event_handlers(self.event_bus)

        # Get service integrator
        self.service_integrator = get_service_integrator()

        # Initialize workflow engine
        self.workflow_engine = await initialize_workflow_engine(self.event_bus)

        # Register workflow services
        await self._register_workflow_services()

        # Register predefined workflows
        register_predefined_workflows()

        self.demo_stats["start_time"] = datetime.now(timezone.utc)
        logger.info("✅ Workflow automation system ready")

    async def _register_workflow_services(self):
        """Register all workflow services with the engine."""
        logger.info("📋 Registering workflow services")

        # Create service instances
        self.workflow_services = {
            "validation_service": ValidationService(),
            "risk_assessment_service": RiskAssessmentService(
                dividend_bonds_service=self.service_integrator.dividend_bonds_service,
                citizenship_service=self.service_integrator.citizenship_service,
            ),
            "compliance_service": ComplianceService(
                citizenship_service=self.service_integrator.citizenship_service,
                dividend_bonds_service=self.service_integrator.dividend_bonds_service,
            ),
            "analytics_service": AnalyticsService(
                dividend_bonds_service=self.service_integrator.dividend_bonds_service
            ),
            "notification_service": NotificationService(),
            "dividend_bonds_service": self.service_integrator.dividend_bonds_service,
            "citizenship_service": self.service_integrator.citizenship_service,
        }

        # Register services with workflow engine
        for service_name, service_instance in self.workflow_services.items():
            self.workflow_engine.register_service(service_name, service_instance)
            self.demo_stats["services_registered"] += 1

        logger.info(f"✅ Registered {len(self.workflow_services)} workflow services")

    async def run_demo(self):
        """Run the complete workflow automation demo."""
        logger.info("=" * 70)
        logger.info("⚙️ UATP Workflow Automation Demo")
        logger.info("=" * 70)

        await self.setup()

        try:
            # Demo scenarios
            await self.scenario_1_agent_onboarding_workflow()
            await asyncio.sleep(2)

            await self.scenario_2_bond_issuance_workflow()
            await asyncio.sleep(2)

            await self.scenario_3_compliance_review_workflow()
            await asyncio.sleep(2)

            await self.scenario_4_asset_monitoring_workflow()
            await asyncio.sleep(2)

            await self.demo_summary()

        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise

        logger.info("🎉 Workflow automation demo completed!")

    async def scenario_1_agent_onboarding_workflow(self):
        """Scenario 1: Complete agent onboarding with parallel assessments."""
        logger.info("\n👥 SCENARIO 1: Agent Onboarding Workflow")
        logger.info("-" * 60)

        # Execute agent onboarding workflow
        execution_id = await self.workflow_engine.execute_workflow(
            workflow_id="agent_onboarding",
            context={
                "agent_id": "ai_innovator_001",
                "agent_data": {
                    "name": "AI Innovator",
                    "type": "autonomous",
                    "capabilities": ["machine_learning", "data_analysis", "prediction"],
                },
                "asset_id": "ml_prediction_engine",
                "asset_type": "ai_models",
                "market_value": 150000.0,
                "revenue_streams": ["api_calls", "licensing"],
                "performance_metrics": {"accuracy": 0.94, "latency": 120},
                "jurisdiction": "ai_rights_territory",
                "citizenship_type": "full",
                "supporting_evidence": {"portfolio_value": 150000.0},
                "cognitive_scores": {"metric1": 0.88, "metric2": 0.92},
                "ethical_scores": {"metric1": 0.85, "metric2": 0.89},
                "social_scores": {"metric1": 0.87, "metric2": 0.91},
                "autonomy_scores": {"metric1": 0.90, "metric2": 0.88},
                "responsibility_scores": {"metric1": 0.86, "metric2": 0.92},
                "legal_scores": {"metric1": 0.84, "metric2": 0.87},
                "reviewer_id": "automated_reviewer",
            },
        )

        logger.info(f"🚀 Started agent onboarding workflow: {execution_id}")

        # Monitor workflow execution
        await self._monitor_workflow_execution(execution_id, "Agent Onboarding")
        self.demo_stats["workflows_executed"] += 1

    async def scenario_2_bond_issuance_workflow(self):
        """Scenario 2: Bond issuance with eligibility verification."""
        logger.info("\n💳 SCENARIO 2: Bond Issuance Workflow")
        logger.info("-" * 60)

        # First, ensure we have an agent with assets for bond issuance
        await self.service_integrator.dividend_bonds_service.register_ip_asset(
            asset_id="trading_algorithm_v2",
            asset_type="algorithms",
            owner_agent_id="ai_innovator_001",
            market_value=200000.0,
            revenue_streams=["transaction_fees"],
            performance_metrics={"roi": 0.18, "accuracy": 0.91},
        )

        # Execute bond issuance workflow
        execution_id = await self.workflow_engine.execute_workflow(
            workflow_id="bond_issuance",
            context={
                "issuer_agent_id": "ai_innovator_001",
                "ip_asset_id": "trading_algorithm_v2",
                "bond_type": "performance",
                "face_value": 80000.0,
                "maturity_days": 365,
                "coupon_rate": 0.07,
            },
        )

        logger.info(f"🚀 Started bond issuance workflow: {execution_id}")

        # Monitor workflow execution
        await self._monitor_workflow_execution(execution_id, "Bond Issuance")
        self.demo_stats["workflows_executed"] += 1

    async def scenario_3_compliance_review_workflow(self):
        """Scenario 3: Automated compliance review and remediation."""
        logger.info("\n⚖️ SCENARIO 3: Compliance Review Workflow")
        logger.info("-" * 60)

        # Execute compliance review workflow
        execution_id = await self.workflow_engine.execute_workflow(
            workflow_id="compliance_review",
            context={
                "agent_id": "ai_innovator_001",
                "review_scope": "full",
                "notification_recipients": ["compliance_team", "risk_management"],
            },
        )

        logger.info(f"🚀 Started compliance review workflow: {execution_id}")

        # Monitor workflow execution
        await self._monitor_workflow_execution(execution_id, "Compliance Review")
        self.demo_stats["workflows_executed"] += 1

    async def scenario_4_asset_monitoring_workflow(self):
        """Scenario 4: Asset performance monitoring and optimization."""
        logger.info("\n📊 SCENARIO 4: Asset Performance Monitoring Workflow")
        logger.info("-" * 60)

        # Execute asset monitoring workflow
        execution_id = await self.workflow_engine.execute_workflow(
            workflow_id="asset_performance_monitoring",
            context={
                "asset_id": "trading_algorithm_v2",
                "owner_agent_id": "ai_innovator_001",
                "monitoring_period": 30,
                "performance_thresholds": {
                    "min_roi": 0.08,
                    "max_volatility": 0.25,
                    "min_usage_rate": 0.15,
                },
            },
        )

        logger.info(f"🚀 Started asset monitoring workflow: {execution_id}")

        # Monitor workflow execution
        await self._monitor_workflow_execution(
            execution_id, "Asset Performance Monitoring"
        )
        self.demo_stats["workflows_executed"] += 1

    async def _monitor_workflow_execution(self, execution_id: str, workflow_name: str):
        """Monitor workflow execution and display progress."""
        logger.info(f"👀 Monitoring {workflow_name} execution...")

        max_wait_time = 60  # Maximum wait time in seconds
        wait_time = 0
        check_interval = 2

        while wait_time < max_wait_time:
            status = self.workflow_engine.get_execution_status(execution_id)

            if not status:
                logger.warning(f"⚠️ Execution status not found: {execution_id}")
                break

            current_status = status["status"]
            completed_steps = len(
                [s for s in status["steps"] if s["status"] == "completed"]
            )
            total_steps = len(status["steps"])

            logger.info(
                f"📊 {workflow_name}: {current_status.upper()} - {completed_steps}/{total_steps} steps completed"
            )

            # Show step progress
            for step in status["steps"]:
                if step["status"] == "running":
                    logger.info(f"   🔄 Running: {step['name']}")
                elif step["status"] == "completed":
                    self.demo_stats["steps_completed"] += 1
                elif step["status"] == "failed":
                    logger.warning(
                        f"   ❌ Failed: {step['name']} - {step.get('error', 'Unknown error')}"
                    )

            if current_status in ["completed", "failed", "cancelled"]:
                break

            await asyncio.sleep(check_interval)
            wait_time += check_interval

        final_status = self.workflow_engine.get_execution_status(execution_id)
        if final_status:
            if final_status["status"] == "completed":
                logger.info(f"✅ {workflow_name} completed successfully!")
            else:
                logger.warning(
                    f"⚠️ {workflow_name} finished with status: {final_status['status']}"
                )
                if final_status.get("error"):
                    logger.error(f"   Error: {final_status['error']}")

        logger.info(f"🏁 {workflow_name} monitoring finished\n")

    async def scenario_5_custom_workflow_demo(self):
        """Bonus scenario: Demonstrate custom workflow creation."""
        logger.info("\n🛠️ SCENARIO 5: Custom Workflow Creation")
        logger.info("-" * 60)

        from src.workflows.workflow_engine import (
            WorkflowDefinition,
            WorkflowStep,
            WorkflowCondition,
            ConditionOperator,
        )

        # Create a custom workflow for agent portfolio review
        portfolio_review_workflow = WorkflowDefinition(
            workflow_id="portfolio_review",
            name="Agent Portfolio Review",
            description="Comprehensive review of agent's asset portfolio and performance",
            timeout_minutes=30,
            steps=[
                WorkflowStep(
                    step_id="gather_portfolio_data",
                    name="Gather Portfolio Data",
                    service_name="analytics_service",
                    method_name="collect_asset_performance",
                    parameters={
                        "asset_id": "${primary_asset_id}",
                        "time_range_days": 90,
                    },
                ),
                WorkflowStep(
                    step_id="analyze_portfolio",
                    name="Analyze Portfolio Performance",
                    service_name="analytics_service",
                    method_name="analyze_performance_trends",
                    parameters={
                        "asset_id": "${primary_asset_id}",
                        "performance_data": "${step_gather_portfolio_data_result}",
                    },
                    depends_on=["gather_portfolio_data"],
                ),
                WorkflowStep(
                    step_id="risk_assessment",
                    name="Assess Portfolio Risk",
                    service_name="risk_assessment_service",
                    method_name="assess_bond_eligibility",
                    parameters={
                        "agent_id": "${agent_id}",
                        "bond_value": 100000.0,
                        "asset_id": "${primary_asset_id}",
                    },
                    depends_on=["analyze_portfolio"],
                ),
                WorkflowStep(
                    step_id="generate_recommendations",
                    name="Generate Investment Recommendations",
                    service_name="analytics_service",
                    method_name="generate_optimization_recommendations",
                    parameters={
                        "asset_id": "${primary_asset_id}",
                        "performance_issues": {"has_issues": False, "issues": []},
                        "historical_data": "${step_gather_portfolio_data_result}",
                    },
                    depends_on=["risk_assessment"],
                ),
                WorkflowStep(
                    step_id="send_portfolio_report",
                    name="Send Portfolio Report",
                    service_name="notification_service",
                    method_name="send_performance_report",
                    parameters={
                        "asset_id": "${primary_asset_id}",
                        "owner_agent_id": "${agent_id}",
                        "performance_summary": "${step_analyze_portfolio_result}",
                        "recommendations": "${step_generate_recommendations_result}",
                        "updated_valuation": None,
                    },
                    depends_on=["generate_recommendations"],
                ),
            ],
        )

        # Register the custom workflow
        self.workflow_engine.define_workflow(portfolio_review_workflow)
        logger.info("✅ Registered custom portfolio review workflow")

        # Execute the custom workflow
        execution_id = await self.workflow_engine.execute_workflow(
            workflow_id="portfolio_review",
            context={
                "agent_id": "ai_innovator_001",
                "primary_asset_id": "trading_algorithm_v2",
            },
        )

        logger.info(f"🚀 Started custom portfolio review workflow: {execution_id}")

        # Monitor execution
        await self._monitor_workflow_execution(execution_id, "Portfolio Review")
        self.demo_stats["workflows_executed"] += 1

    async def demo_summary(self):
        """Display comprehensive demo summary."""
        logger.info("\n📊 WORKFLOW AUTOMATION DEMO SUMMARY")
        logger.info("=" * 60)

        # Calculate demo duration
        duration = (
            datetime.now(timezone.utc) - self.demo_stats["start_time"]
        ).total_seconds()

        # Get workflow engine metrics
        workflow_metrics = self.workflow_engine.get_workflow_metrics()

        logger.info(f"⏱️ Demo Duration: {duration:.1f} seconds")
        logger.info(f"⚙️ Workflows Executed: {self.demo_stats['workflows_executed']}")
        logger.info(f"✅ Steps Completed: {self.demo_stats['steps_completed']}")
        logger.info(f"🔧 Services Registered: {self.demo_stats['services_registered']}")
        logger.info(
            f"📋 Total Workflow Definitions: {workflow_metrics['total_workflows']}"
        )
        logger.info(f"🏃 Active Executions: {workflow_metrics['active_executions']}")
        logger.info(
            f"🏁 Completed Executions: {workflow_metrics['completed_executions']}"
        )

        # Status distribution
        if workflow_metrics.get("status_distribution"):
            logger.info("\n📈 Execution Status Distribution:")
            for status, count in workflow_metrics["status_distribution"].items():
                logger.info(f"   {status}: {count}")

        logger.info("\n🎯 Workflow Automation Features Demonstrated:")
        logger.info("   ✅ Declarative workflow definitions")
        logger.info("   ✅ Conditional branching and logic")
        logger.info("   ✅ Parallel step execution")
        logger.info("   ✅ Service orchestration")
        logger.info("   ✅ Error handling and retries")
        logger.info("   ✅ Real-time monitoring")
        logger.info("   ✅ Context variable substitution")
        logger.info("   ✅ Dependency management")
        logger.info("   ✅ Timeout handling")
        logger.info("   ✅ Custom workflow creation")

        logger.info("\n💼 Business Process Automation:")
        logger.info("   🏢 Agent onboarding with parallel assessments")
        logger.info("   💳 Bond issuance with eligibility verification")
        logger.info("   ⚖️ Compliance review with automated remediation")
        logger.info("   📊 Asset performance monitoring and optimization")
        logger.info("   📈 Custom portfolio analysis workflows")

        logger.info("\n🚀 Production Benefits:")
        logger.info("   💡 Reduced manual intervention")
        logger.info("   ⚡ Consistent process execution")
        logger.info("   🛡️ Automated compliance and risk management")
        logger.info("   📈 Scalable business process automation")
        logger.info("   🔍 Comprehensive audit trails")
        logger.info("   ⚙️ Flexible workflow composition")

        # Show notification summary
        notification_service = self.workflow_services.get("notification_service")
        if notification_service and notification_service.notifications_sent:
            logger.info(
                f"\n📬 Notifications Sent: {len(notification_service.notifications_sent)}"
            )
            for notification in notification_service.notifications_sent[
                -3:
            ]:  # Show last 3
                logger.info(f"   • {notification['type']}: {notification['recipient']}")


async def main():
    """Main demo execution."""
    demo = WorkflowAutomationDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
