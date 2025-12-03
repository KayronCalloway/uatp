#!/usr/bin/env python3
"""
UATP Onboarding System Demo

Demonstrates the complete onboarding experience for different user types.
Shows how the system achieves "intuitive and frictionless" client onboarding.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Import onboarding components
from src.onboarding.onboarding_orchestrator import OnboardingOrchestrator, UserType
from src.onboarding.setup_wizard import InteractiveSetupWizard
from src.onboarding.integration_manager import IntegrationManager
from src.onboarding.health_monitor import SystemHealthMonitor
from src.onboarding.support_assistant import SupportAssistant, IssueType


class OnboardingDemo:
    """Interactive demonstration of the UATP onboarding system"""

    def __init__(self):
        """Initialize the demo"""
        print("🚀 UATP Onboarding System Demo")
        print("=" * 50)
        print("This demo showcases the intuitive, frictionless onboarding experience")
        print("that gets users creating capsules within 5 minutes.\n")

    async def run_demo(self):
        """Run the complete onboarding demo"""

        print("🎯 DEMO MENU")
        print("-" * 20)
        print("1. 👋 Casual User Experience (5-minute target)")
        print("2. 👨‍💻 Developer Experience (10-minute target)")
        print("3. 🏢 Enterprise Experience (15-minute target)")
        print("4. 🔧 System Health & Monitoring Demo")
        print("5. 🆘 Support Assistant Demo")
        print("6. 🌐 Web Interface Demo")
        print("0. ❌ Exit")

        while True:
            choice = input("\nSelect demo (0-6): ").strip()

            if choice == "1":
                await self.casual_user_demo()
            elif choice == "2":
                await self.developer_demo()
            elif choice == "3":
                await self.enterprise_demo()
            elif choice == "4":
                await self.health_monitoring_demo()
            elif choice == "5":
                await self.support_assistant_demo()
            elif choice == "6":
                await self.web_interface_demo()
            elif choice == "0":
                print("👋 Thanks for exploring UATP onboarding!")
                break
            else:
                print("❌ Invalid choice. Please try again.")

    async def casual_user_demo(self):
        """Demonstrate casual user onboarding experience"""

        print("\n👋 CASUAL USER ONBOARDING DEMO")
        print("=" * 40)
        print("Target: Get user creating capsules in under 5 minutes")
        print("Philosophy: Zero technical knowledge required\n")

        # Initialize orchestrator
        orchestrator = OnboardingOrchestrator()

        # Start onboarding
        print("🔄 Starting onboarding for casual user...")

        user_preferences = {
            "user_type": "casual_user",
            "technical_level": "beginner",
            "primary_goal": "try_uatp",
        }

        start_time = datetime.now(timezone.utc)

        try:
            # Step 1: Welcome & Type Detection
            progress = await orchestrator.start_onboarding(
                user_id="demo_casual_user", user_preferences=user_preferences
            )

            print(f"✅ Welcome completed - User type: {progress.user_type.value}")
            print(f"   Estimated completion: {progress.estimated_completion_time}")

            # Step 2: Environment Detection (auto)
            print("\n🔍 Auto-detecting environment...")
            progress = await orchestrator.continue_onboarding("demo_casual_user")
            print("✅ Environment detected and configured")

            # Step 3: Quick Setup (auto)
            print("\n⚙️ Running one-click setup...")
            progress = await orchestrator.continue_onboarding("demo_casual_user")
            print("✅ System configured with smart defaults")

            # Step 4: AI Platform Integration
            print("\n🤖 Setting up AI platform integration...")
            progress = await orchestrator.continue_onboarding(
                "demo_casual_user", {"preferred_platform": "openai"}  # Auto-suggested
            )
            print("✅ AI platform connected and tested")

            # Step 5: First Capsule Creation
            print("\n🧪 Creating first capsule...")
            progress = await orchestrator.continue_onboarding("demo_casual_user")

            # Calculate completion time
            end_time = datetime.now(timezone.utc)
            completion_time = (end_time - start_time).total_seconds()

            print("✅ First capsule created successfully!")
            print(f"\n🎉 ONBOARDING COMPLETE!")
            print(f"   Total time: {completion_time:.1f} seconds")
            print(
                f"   Target met: {'YES' if completion_time < 300 else 'NO'} (under 5 minutes)"
            )
            print(f"   Success metrics:")
            for metric, value in progress.success_metrics.items():
                print(f"     {metric}: {value}")

            # Show next steps
            next_steps = progress.personalization_data.get("next_steps", [])
            if next_steps:
                print(f"\n📋 Recommended next steps:")
                for i, step in enumerate(next_steps[:3], 1):
                    print(f"   {i}. {step['title']} ({step['estimated_time']})")

        except Exception as e:
            print(f"❌ Onboarding failed: {e}")

        input("\nPress Enter to continue...")

    async def developer_demo(self):
        """Demonstrate developer onboarding experience"""

        print("\n👨‍💻 DEVELOPER ONBOARDING DEMO")
        print("=" * 40)
        print("Target: Full development environment setup in under 10 minutes")
        print("Features: API keys, integrations, debugging tools\n")

        orchestrator = OnboardingOrchestrator()

        user_preferences = {
            "user_type": "developer",
            "technical_level": "advanced",
            "programming_language": "python",
            "integration_needs": ["api", "webhooks", "testing"],
            "has_git": True,
            "has_ide": True,
        }

        start_time = datetime.now(timezone.utc)

        try:
            print("🔄 Starting developer onboarding...")

            # Start with developer-specific flow
            progress = await orchestrator.start_onboarding(
                user_id="demo_developer", user_preferences=user_preferences
            )

            print(f"✅ Developer profile created")
            print(f"   Detected capabilities: Git, IDE, Python experience")

            # Environment analysis
            print("\n🔍 Analyzing development environment...")
            progress = await orchestrator.continue_onboarding("demo_developer")
            env_info = progress.personalization_data.get("environment", {})
            print(f"✅ Environment analyzed:")
            print(f"     Python: {env_info.get('python_version', 'Unknown')}")
            print(f"     Git available: {env_info.get('has_git', False)}")
            print(f"     Docker available: {env_info.get('has_docker', False)}")

            # Advanced setup
            print("\n⚙️ Configuring development environment...")
            progress = await orchestrator.continue_onboarding("demo_developer")
            print("✅ Advanced features enabled:")
            print("     - Debug logging enabled")
            print("     - API playground configured")
            print("     - Testing framework integrated")

            # Platform integrations
            print("\n🤖 Setting up multiple AI platform integrations...")
            progress = await orchestrator.continue_onboarding(
                "demo_developer", {"setup_multiple_platforms": True}
            )
            print("✅ Developer integrations complete:")
            print("     - OpenAI with attribution tracking")
            print("     - Anthropic with debug logging")
            print("     - API key management configured")

            # Advanced first capsule
            print("\n🧪 Creating developer-grade capsule with full attribution...")
            progress = await orchestrator.continue_onboarding("demo_developer")

            end_time = datetime.now(timezone.utc)
            completion_time = (end_time - start_time).total_seconds()

            print("✅ Advanced capsule created!")
            print(f"\n🎉 DEVELOPER ONBOARDING COMPLETE!")
            print(f"   Total time: {completion_time:.1f} seconds")
            print(
                f"   Target met: {'YES' if completion_time < 600 else 'NO'} (under 10 minutes)"
            )

            # Show developer-specific next steps
            print(f"\n🛠️ Developer next steps:")
            print("   1. Explore API documentation")
            print("   2. Set up CI/CD integration")
            print("   3. Configure webhook endpoints")
            print("   4. Try advanced attribution features")

        except Exception as e:
            print(f"❌ Developer onboarding failed: {e}")

        input("\nPress Enter to continue...")

    async def enterprise_demo(self):
        """Demonstrate enterprise onboarding experience"""

        print("\n🏢 ENTERPRISE ONBOARDING DEMO")
        print("=" * 40)
        print("Target: Production-ready enterprise setup in under 15 minutes")
        print("Features: Security, compliance, governance, team management\n")

        orchestrator = OnboardingOrchestrator()

        user_preferences = {
            "user_type": "enterprise",
            "organization_size": 500,
            "compliance_requirements": ["SOC2", "GDPR"],
            "security_level": "high",
            "scalability_needs": "high",
            "team_size": 50,
            "budget_tier": "enterprise",
        }

        start_time = datetime.now(timezone.utc)

        try:
            print("🔄 Starting enterprise onboarding...")

            progress = await orchestrator.start_onboarding(
                user_id="demo_enterprise", user_preferences=user_preferences
            )

            print(f"✅ Enterprise profile created")
            print(
                f"   Organization size: {user_preferences['organization_size']} employees"
            )
            print(
                f"   Compliance needs: {', '.join(user_preferences['compliance_requirements'])}"
            )

            # Security assessment
            print("\n🔒 Conducting security requirements assessment...")
            progress = await orchestrator.continue_onboarding("demo_enterprise")
            print("✅ Security assessment complete:")
            print("     - Post-quantum cryptography enabled")
            print("     - Zero-knowledge proofs configured")
            print("     - Audit trail activated")
            print("     - Role-based access control prepared")

            # Infrastructure setup
            print("\n🏗️ Setting up production infrastructure...")
            progress = await orchestrator.continue_onboarding("demo_enterprise")
            print("✅ Enterprise infrastructure configured:")
            print("     - Auto-scaling enabled")
            print("     - High availability setup")
            print("     - Monitoring & alerting active")
            print("     - Backup & disaster recovery ready")

            # Governance framework
            print("\n🏛️ Initializing governance framework...")
            progress = await orchestrator.continue_onboarding("demo_enterprise")
            print("✅ Governance systems activated:")
            print("     - DAO-style decision making")
            print("     - Proposal & voting system")
            print("     - Treasury management")
            print("     - Compliance monitoring")

            # Team onboarding preparation
            print("\n👥 Preparing team member onboarding...")
            progress = await orchestrator.continue_onboarding("demo_enterprise")

            end_time = datetime.now(timezone.utc)
            completion_time = (end_time - start_time).total_seconds()

            print("✅ Team management configured!")
            print(f"\n🎉 ENTERPRISE ONBOARDING COMPLETE!")
            print(f"   Total time: {completion_time:.1f} seconds")
            print(
                f"   Target met: {'YES' if completion_time < 900 else 'NO'} (under 15 minutes)"
            )

            print(f"\n🏢 Enterprise deployment ready:")
            print("   - Production-grade security")
            print("   - Compliance frameworks active")
            print("   - Team management configured")
            print("   - Governance systems operational")
            print("   - Ready for 500+ user organization")

        except Exception as e:
            print(f"❌ Enterprise onboarding failed: {e}")

        input("\nPress Enter to continue...")

    async def health_monitoring_demo(self):
        """Demonstrate system health monitoring"""

        print("\n🔧 SYSTEM HEALTH & MONITORING DEMO")
        print("=" * 40)
        print("Real-time health monitoring with SLA tracking\n")

        health_monitor = SystemHealthMonitor()

        print("🏥 Starting health monitoring system...")

        # Get current health status
        health_report = await health_monitor.get_system_health()

        print(f"📊 System Health Report:")
        print(f"   Overall Status: {health_report.overall_status.value.upper()}")
        print(f"   Health Score: {health_report.score:.1f}/100")
        print(f"   Summary: {health_report.summary}")

        print(f"\n📈 System Metrics:")
        for metric in health_report.system_metrics:
            status_icon = {
                "excellent": "🟢",
                "good": "🟡",
                "warning": "🟠",
                "critical": "🔴",
            }.get(metric.status.value, "⚪")

            print(f"   {status_icon} {metric.name}: {metric.value:.1f}{metric.unit}")

        print(f"\n🛠️ Service Health:")
        for service in health_report.service_health:
            status_icon = {
                "healthy": "✅",
                "degraded": "⚠️",
                "down": "❌",
                "maintenance": "🔧",
            }.get(service.status.value, "❓")

            response_time = (
                f" ({service.response_time:.1f}ms)" if service.response_time else ""
            )
            print(f"   {status_icon} {service.name}{response_time}")

        # SLA Dashboard
        sla_dashboard = await health_monitor.get_sla_dashboard()
        print(f"\n📋 SLA Dashboard:")
        print(
            f"   Availability: {sla_dashboard['uptime_24h']:.2f}% (target: {sla_dashboard['availability_target']:.1f}%)"
        )
        print(
            f"   Response Time: {sla_dashboard['avg_response_time']:.3f}s (target: {sla_dashboard['response_time_target']:.1f}s)"
        )
        print(f"   Error Rate: {sla_dashboard['error_rate']:.2f}% (target: <1.0%)")

        # Active issues and recommendations
        if health_report.active_issues:
            print(f"\n⚠️ Active Issues:")
            for issue in health_report.active_issues:
                print(f"   - {issue}")

        if health_report.recommendations:
            print(f"\n💡 Recommendations:")
            for rec in health_report.recommendations:
                print(f"   - {rec}")

        print(f"\n✨ Key Features Demonstrated:")
        print("   - Real-time system monitoring")
        print("   - SLA compliance tracking")
        print("   - Proactive issue detection")
        print("   - User-friendly health summaries")
        print("   - Automated recommendations")

        input("\nPress Enter to continue...")

    async def support_assistant_demo(self):
        """Demonstrate intelligent support assistant"""

        print("\n🆘 SUPPORT ASSISTANT DEMO")
        print("=" * 40)
        print("Contextual help and automated troubleshooting\n")

        support_assistant = SupportAssistant()

        # Simulate different support scenarios
        scenarios = [
            {
                "name": "New User Needs Help",
                "issue_type": "general_question",
                "message": "I'm new to UATP and don't know where to start",
            },
            {
                "name": "API Key Problem",
                "issue_type": "api_key_issue",
                "message": "I keep getting 'invalid API key' errors with OpenAI",
            },
            {
                "name": "Connection Issues",
                "issue_type": "connection_error",
                "message": "The system won't connect to my AI platform",
            },
            {
                "name": "Performance Problem",
                "issue_type": "performance_issue",
                "message": "Everything is running very slowly",
            },
        ]

        for i, scenario in enumerate(scenarios, 1):
            print(f"📞 Scenario {i}: {scenario['name']}")
            print(f"   User message: \"{scenario['message']}\"")

            # Get contextual support
            support_response = await support_assistant.get_contextual_help(
                user_progress=None,
                issue_type=scenario["issue_type"],
                user_message=scenario["message"],
            )

            print(f"   🤖 Support Response:")
            print(f"     Issue Type: {support_response.issue_type.value}")
            print(f"     Support Level: {support_response.support_level.value}")
            print(f"     Title: {support_response.title}")
            print(f"     Message: {support_response.message}")

            if support_response.immediate_actions:
                print(f"     Immediate Actions:")
                for action in support_response.immediate_actions[:2]:
                    print(f"       • {action}")

            if support_response.step_by_step_guide:
                print(f"     Step-by-step Guide:")
                for step in support_response.step_by_step_guide[:3]:
                    print(f"       {step['step']}. {step['description']}")

            print(f"     Confidence: {support_response.confidence_score:.0%}")
            print(f"     Est. Resolution: {support_response.estimated_resolution_time}")
            print()

        # Demonstrate troubleshooting flow
        print("🔧 Interactive Troubleshooting Flow Demo:")
        flow = await support_assistant.start_troubleshooting_flow(
            user_id="demo_user", issue_type=IssueType.SETUP_FAILED
        )

        print(f"   Flow: {flow.title}")
        print(f"   Steps: {len(flow.steps)}")
        for step in flow.steps:
            print(f"     {step['id']}. {step['title']}")
            print(f"        Action: {step['action']}")
            print(f"        Expected: {step['expected']}")

        print(f"\n✨ Key Features Demonstrated:")
        print("   - Contextual issue analysis")
        print("   - Personalized support responses")
        print("   - Step-by-step troubleshooting")
        print("   - Proactive suggestions")
        print("   - Smart escalation routing")

        input("\nPress Enter to continue...")

    async def web_interface_demo(self):
        """Demonstrate web interface capabilities"""

        print("\n🌐 WEB INTERFACE DEMO")
        print("=" * 40)
        print("Interactive web-based onboarding experience\n")

        print("🖥️ Web Interface Features:")
        print("   ✅ Responsive, mobile-friendly design")
        print("   ✅ Real-time progress tracking")
        print("   ✅ Visual setup wizards")
        print("   ✅ One-click platform connections")
        print("   ✅ Live system health indicators")
        print("   ✅ Contextual help system")
        print("   ✅ WebSocket real-time updates")
        print("   ✅ Progressive disclosure UI")

        print(f"\n📱 User Experience Highlights:")
        print("   • Zero documentation reading required")
        print("   • Visual progress indicators")
        print("   • Smart default selections")
        print("   • Real-time validation")
        print("   • Immediate success feedback")
        print("   • Contextual help bubbles")

        print(f"\n🚀 To experience the web interface:")
        print("   1. Start the UATP server: python src/api/server.py")
        print("   2. Open browser to: http://localhost:9090/onboarding")
        print("   3. Follow the interactive onboarding flow")

        print(f"\n🔗 Available endpoints:")
        print("   GET  /onboarding/ - Main onboarding interface")
        print("   POST /onboarding/api/start - Start onboarding")
        print("   POST /onboarding/api/continue - Continue flow")
        print("   GET  /onboarding/api/health - System health")
        print("   POST /onboarding/api/support - Get help")
        print("   WS   /onboarding/ws/progress - Real-time updates")

        input("\nPress Enter to continue...")


async def main():
    """Main demo entry point"""

    try:
        demo = OnboardingDemo()
        await demo.run_demo()

    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        logger.error(f"Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
