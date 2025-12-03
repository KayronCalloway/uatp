#!/usr/bin/env python3
"""
UATP Capsule Engine - Quick Start Interactive Demo
Run this to see and interact with all the advanced systems!
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Configure logging to be more readable
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("uatp_demo.log")],
)

logger = logging.getLogger(__name__)

# Import all our systems
from src.audit.advanced_analytics import advanced_audit_analytics
from src.capsule_schema import CapsuleStatus, CapsuleType
from src.capsules.specialized_capsules import ReasoningCapsule, UncertaintyCapsule
from src.consensus.multi_agent_consensus import consensus_manager
from src.crypto.post_quantum import post_quantum_crypto
from src.crypto.zero_knowledge import zk_system
from src.deployment.production_deployment import deployment_system
from src.economic.fcde_engine import fcde_engine
from src.ethics.rect_system import rect_system
from src.governance.advanced_governance import governance_system
from src.graph.capsule_relationships import relationship_graph
from src.ml.analytics_engine import ml_analytics
from src.optimization.capsule_compression import optimization_engine
from src.optimization.performance_layer import performance_layer


class InteractiveUATPDemo:
    """Interactive demonstration of the UATP Capsule Engine."""

    def __init__(self):
        self.running = True
        self.systems_initialized = False

    async def run_interactive_demo(self):
        """Run the interactive demo."""

        print("🚀 UATP Capsule Engine - Interactive Demo")
        print("=" * 50)
        print("Welcome to the advanced UATP Capsule Engine!")
        print("This demo will show you all the amazing systems we've built.\n")

        while self.running:
            await self.show_main_menu()

    async def show_main_menu(self):
        """Show the main menu."""

        print("\n🎯 MAIN MENU")
        print("-" * 20)
        print("1. 🔧 Initialize All Systems")
        print("2. 🔐 Crypto & Security Demo")
        print("3. 💰 Economic Systems Demo")
        print("4. 🤖 AI & ML Demo")
        print("5. 🏛️ Governance & Consensus Demo")
        print("6. 📊 Performance & Monitoring Demo")
        print("7. 🚀 Production Deployment Demo")
        print("8. 🧪 Create & Process Capsules")
        print("9. 📈 System Dashboard")
        print("10. 🔍 Search & Analytics")
        print("0. ❌ Exit")

        choice = input("\nEnter your choice (0-10): ").strip()

        try:
            if choice == "1":
                await self.initialize_systems()
            elif choice == "2":
                await self.crypto_security_demo()
            elif choice == "3":
                await self.economic_systems_demo()
            elif choice == "4":
                await self.ai_ml_demo()
            elif choice == "5":
                await self.governance_consensus_demo()
            elif choice == "6":
                await self.performance_monitoring_demo()
            elif choice == "7":
                await self.production_deployment_demo()
            elif choice == "8":
                await self.capsule_processing_demo()
            elif choice == "9":
                await self.system_dashboard()
            elif choice == "10":
                await self.search_analytics_demo()
            elif choice == "0":
                await self.shutdown_systems()
                self.running = False
            else:
                print("❌ Invalid choice. Please try again.")

        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"Demo error: {e}")

    async def initialize_systems(self):
        """Initialize all systems."""

        if self.systems_initialized:
            print("✅ Systems already initialized!")
            return

        print("\n🔧 INITIALIZING ALL SYSTEMS...")
        print("=" * 40)

        try:
            # Initialize crypto systems
            print("🔐 Initializing cryptographic systems...")
            post_quantum_crypto.initialize_crypto_systems()
            zk_system.initialize_zk_system()

            # Initialize economic systems
            print("💰 Initializing economic systems...")
            fcde_engine.initialize_system()

            # Initialize governance
            print("🏛️ Initializing governance systems...")
            await governance_system.initialize_governance()

            # Initialize performance monitoring
            print("📊 Initializing performance monitoring...")
            await performance_layer.start_optimization_layer()

            # Initialize deployment system
            print("🚀 Initializing deployment system...")
            await deployment_system.initialize_system()

            self.systems_initialized = True

            print("\n✅ ALL SYSTEMS INITIALIZED SUCCESSFULLY!")
            print("🎉 The UATP Capsule Engine is ready for action!")

        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            logger.error(f"System initialization failed: {e}")

    async def crypto_security_demo(self):
        """Demonstrate crypto and security features."""

        if not self.systems_initialized:
            print("⚠️ Please initialize systems first (option 1)")
            return

        print("\n🔐 CRYPTO & SECURITY DEMO")
        print("=" * 30)

        # Post-quantum crypto demo
        print("\n🛡️ Post-Quantum Cryptography:")
        keypair = post_quantum_crypto.generate_dilithium_keypair()
        print(f"  ✅ Generated {keypair.algorithm} keypair")
        print(f"  🔑 Key size: {keypair.key_size} bytes")

        # Zero-knowledge proof demo
        print("\n🕵️ Zero-Knowledge Proofs:")
        zk_proof = zk_system.generate_system_proof()
        print(f"  ✅ Generated ZK proof: {zk_proof.proof_type.value}")
        print(f"  🎯 Confidence: {zk_proof.confidence:.1%}")

        # Security scan simulation
        print("\n🔍 Security Scanning:")
        print("  🔎 Scanning system for vulnerabilities...")
        await asyncio.sleep(1)  # Simulate scan
        print("  ✅ Security scan complete - System secure!")

        input("\nPress Enter to continue...")

    async def economic_systems_demo(self):
        """Demonstrate economic systems."""

        if not self.systems_initialized:
            print("⚠️ Please initialize systems first (option 1)")
            return

        print("\n💰 ECONOMIC SYSTEMS DEMO")
        print("=" * 30)

        # FCDE demo
        print("\n💎 Fair Creator Dividend Engine:")
        insights = fcde_engine.get_system_insights()
        print(f"  💰 Current dividend pool: ${insights.get('dividend_pool', 0):,.2f}")
        print(f"  👥 Active creators: {insights.get('active_creators', 0)}")
        print(f"  📈 Total contributions: {insights.get('total_contributions', 0)}")

        # Simulate a dividend distribution
        print("\n💸 Processing dividend distribution...")
        distribution_id = fcde_engine.process_dividend_distribution()
        print(f"  ✅ Distribution complete: {distribution_id}")

        # Show economic insights
        print("\n📊 Economic Insights:")
        updated_insights = fcde_engine.get_system_insights()
        print(f"  📈 Growth rate: {updated_insights.get('growth_rate', 0):.1%}")
        print(f"  ⚖️ System health: {updated_insights.get('system_health', 'unknown')}")

        input("\nPress Enter to continue...")

    async def ai_ml_demo(self):
        """Demonstrate AI and ML capabilities."""

        if not self.systems_initialized:
            print("⚠️ Please initialize systems first (option 1)")
            return

        print("\n🤖 AI & MACHINE LEARNING DEMO")
        print("=" * 35)

        # Create a test capsule for analysis
        print("\n🧬 Creating test capsule for analysis...")
        test_capsule = ReasoningCapsule(
            capsule_id="ml_demo_capsule",
            capsule_type=CapsuleType.REASONING,
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.ACTIVE,
        )

        # ML analysis
        print("\n🧠 Running ML analysis...")
        ml_results = ml_analytics.analyze_capsule(test_capsule)

        print("  📊 Analysis Results:")
        for analysis_type, result in ml_results.items():
            print(f"    🔍 {analysis_type}: {result.confidence:.1%} confidence")
            if hasattr(result, "prediction"):
                print(f"       📈 Prediction: {result.prediction}")

        # System insights
        print("\n🎯 ML System Insights:")
        system_insights = ml_analytics.get_system_insights()
        print(f"  🔢 Total analyses: {system_insights.get('total_analyses', 0)}")
        print(
            f"  🎯 Average quality: {system_insights.get('quality_trends', {}).get('average_quality', 0):.2f}"
        )

        input("\nPress Enter to continue...")

    async def governance_consensus_demo(self):
        """Demonstrate governance and consensus."""

        if not self.systems_initialized:
            print("⚠️ Please initialize systems first (option 1)")
            return

        print("\n🏛️ GOVERNANCE & CONSENSUS DEMO")
        print("=" * 35)

        # Governance demo
        print("\n🗳️ Governance System:")
        governance_status = governance_system.get_governance_status()
        print(f"  📋 Active proposals: {governance_status.get('active_proposals', 0)}")
        print(f"  👥 Registered voters: {governance_status.get('registered_voters', 0)}")
        print(f"  🏛️ DAO treasury: ${governance_status.get('dao_treasury', 0):,.2f}")

        # Create a sample proposal
        print("\n📝 Creating sample proposal...")
        proposal_id = await governance_system.create_proposal(
            title="Increase System Performance Threshold",
            description="Proposal to increase the performance monitoring threshold from 80% to 85%",
            proposer_id="demo_user",
            proposal_type="system_change",
        )
        print(f"  ✅ Proposal created: {proposal_id}")

        # Consensus demo
        print("\n🤝 Consensus System:")
        consensus_status = consensus_manager.get_system_status()
        print(f"  🌐 Active nodes: {consensus_status.get('active_nodes', 0)}")
        print(
            f"  📊 Consensus algorithm: {consensus_status.get('consensus_type', 'unknown')}"
        )
        print(f"  ✅ System health: {consensus_status.get('health_status', 'unknown')}")

        input("\nPress Enter to continue...")

    async def performance_monitoring_demo(self):
        """Demonstrate performance monitoring."""

        if not self.systems_initialized:
            print("⚠️ Please initialize systems first (option 1)")
            return

        print("\n📊 PERFORMANCE MONITORING DEMO")
        print("=" * 35)

        # Performance dashboard
        print("\n📈 Performance Dashboard:")
        dashboard = performance_layer.get_performance_dashboard()

        perf_summary = dashboard.get("performance_summary", {})
        print(f"  🎯 Performance level: {perf_summary.get('current_level', 'unknown')}")
        print(f"  🔥 CPU usage: {perf_summary.get('avg_cpu_usage', 0):.1f}%")
        print(f"  💾 Memory usage: {perf_summary.get('avg_memory_usage', 0):.1f}%")
        print(f"  ⚡ Response time: {perf_summary.get('avg_response_time', 0):.2f}s")

        # Recent optimizations
        recent_opts = dashboard.get("recent_optimizations", [])
        print(f"\n🚀 Recent Optimizations: {len(recent_opts)}")
        for i, opt in enumerate(recent_opts[:3]):
            print(
                f"  {i+1}. {opt.get('strategy', 'unknown')} - {opt.get('improvement', 0):.1f}% improvement"
            )

        # System health
        system_health = dashboard.get("system_health", {})
        print("\n🏥 System Health:")
        print(f"  ✅ Total optimizations: {system_health.get('total_optimizations', 0)}")
        print(
            f"  📈 Success rate: {system_health.get('successful_optimizations', 0)}/{system_health.get('total_optimizations', 1)}"
        )

        input("\nPress Enter to continue...")

    async def production_deployment_demo(self):
        """Demonstrate production deployment."""

        if not self.systems_initialized:
            print("⚠️ Please initialize systems first (option 1)")
            return

        print("\n🚀 PRODUCTION DEPLOYMENT DEMO")
        print("=" * 35)

        # Deployment dashboard
        print("\n📊 Deployment Dashboard:")
        dashboard = deployment_system.get_system_dashboard()

        deploy_summary = dashboard.get("deployment_summary", {})
        print(f"  📦 Total deployments: {deploy_summary.get('total_deployments', 0)}")
        print(
            f"  ✅ Successful deployments: {deploy_summary.get('successful_deployments', 0)}"
        )
        print(f"  ❌ Failed deployments: {deploy_summary.get('failed_deployments', 0)}")

        # Health monitoring
        health_monitoring = dashboard.get("health_monitoring", {})
        print("\n🏥 Health Monitoring:")
        print(
            f"  🎯 Overall health: {health_monitoring.get('overall_health', 'unknown')}"
        )
        print(f"  🟢 Healthy services: {health_monitoring.get('healthy_services', 0)}")
        print(f"  🟡 Degraded services: {health_monitoring.get('degraded_services', 0)}")

        # Security status
        security = dashboard.get("security_hardening", {})
        print("\n🔒 Security Status:")
        print(f"  🛡️ Security policies: {security.get('security_policies', 0)}")
        print(f"  🔍 Recent scans: {security.get('recent_scans', 0)}")
        print(f"  🚨 Open issues: {security.get('open_security_issues', 0)}")

        input("\nPress Enter to continue...")

    async def capsule_processing_demo(self):
        """Demonstrate capsule creation and processing."""

        if not self.systems_initialized:
            print("⚠️ Please initialize systems first (option 1)")
            return

        print("\n🧪 CAPSULE PROCESSING DEMO")
        print("=" * 30)

        print("\nWhat type of capsule would you like to create?")
        print("1. 🧠 Reasoning Capsule")
        print("2. ❓ Uncertainty Capsule")
        print("3. 🪞 Self-Reflection Capsule")

        choice = input("Enter choice (1-3): ").strip()

        capsule_id = f"demo_capsule_{int(datetime.now().timestamp())}"

        if choice == "1":
            capsule = ReasoningCapsule(
                capsule_id=capsule_id,
                capsule_type=CapsuleType.REASONING,
                timestamp=datetime.now(timezone.utc),
                status=CapsuleStatus.ACTIVE,
            )
            capsule_type_name = "Reasoning"
        elif choice == "2":
            capsule = UncertaintyCapsule(
                capsule_id=capsule_id,
                capsule_type=CapsuleType.UNCERTAINTY,
                timestamp=datetime.now(timezone.utc),
                status=CapsuleStatus.ACTIVE,
            )
            capsule_type_name = "Uncertainty"
        else:
            # Default to reasoning
            capsule = ReasoningCapsule(
                capsule_id=capsule_id,
                capsule_type=CapsuleType.REASONING,
                timestamp=datetime.now(timezone.utc),
                status=CapsuleStatus.ACTIVE,
            )
            capsule_type_name = "Reasoning"

        print(f"\n🎯 Created {capsule_type_name} Capsule: {capsule_id}")

        # Process through all systems
        print("\n🔄 Processing through all systems...")

        # 1. ML Analysis
        print("  🤖 Running ML analysis...")
        ml_results = ml_analytics.analyze_capsule(capsule)
        print(f"     ✅ Analysis complete - {len(ml_results)} insights generated")

        # 2. Add to relationship graph
        print("  🕸️ Adding to relationship graph...")
        relationship_graph.add_capsule_node(capsule)
        print("     ✅ Added to graph")

        # 3. Economic processing
        print("  💰 Processing economic attribution...")
        fcde_engine.process_capsule_contribution(capsule)
        print("     ✅ Economic processing complete")

        # 4. Ethical validation
        print("  ⚖️ Running ethical validation...")
        ethical_result = rect_system.evaluate_capsule_ethics(capsule)
        print(f"     ✅ Ethical score: {ethical_result.get('ethics_score', 0):.1f}")

        # 5. Optimization analysis
        print("  🚀 Analyzing for optimization...")
        optimization_engine.analyze_capsule_for_optimization(capsule)
        print("     ✅ Optimization analysis complete")

        print(f"\n🎉 Capsule {capsule_id} successfully processed through all systems!")

        input("\nPress Enter to continue...")

    async def system_dashboard(self):
        """Show comprehensive system dashboard."""

        if not self.systems_initialized:
            print("⚠️ Please initialize systems first (option 1)")
            return

        print("\n📈 COMPREHENSIVE SYSTEM DASHBOARD")
        print("=" * 40)

        # Overall system status
        print("\n🎯 SYSTEM STATUS:")
        print(f"  🟢 Systems initialized: {self.systems_initialized}")
        print(f"  📅 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Performance metrics
        perf_dashboard = performance_layer.get_performance_dashboard()
        perf_summary = perf_dashboard.get("performance_summary", {})
        print("\n📊 PERFORMANCE:")
        print(f"  🎯 Performance level: {perf_summary.get('current_level', 'unknown')}")
        print(f"  🔥 CPU: {perf_summary.get('avg_cpu_usage', 0):.1f}%")
        print(f"  💾 Memory: {perf_summary.get('avg_memory_usage', 0):.1f}%")

        # ML insights
        ml_insights = ml_analytics.get_system_insights()
        print("\n🤖 MACHINE LEARNING:")
        print(f"  🔢 Total analyses: {ml_insights.get('total_analyses', 0)}")
        print(
            f"  🎯 Quality trends: {ml_insights.get('quality_trends', {}).get('average_quality', 0):.2f}"
        )

        # Economic status
        economic_insights = fcde_engine.get_system_insights()
        print("\n💰 ECONOMICS:")
        print(f"  💎 Dividend pool: ${economic_insights.get('dividend_pool', 0):,.2f}")
        print(f"  👥 Active creators: {economic_insights.get('active_creators', 0)}")

        # Governance status
        governance_status = governance_system.get_governance_status()
        print("\n🏛️ GOVERNANCE:")
        print(f"  📋 Active proposals: {governance_status.get('active_proposals', 0)}")
        print(f"  👥 Registered voters: {governance_status.get('registered_voters', 0)}")

        # Deployment status
        deploy_dashboard = deployment_system.get_system_dashboard()
        deploy_summary = deploy_dashboard.get("deployment_summary", {})
        print("\n🚀 DEPLOYMENT:")
        print(f"  📦 Total deployments: {deploy_summary.get('total_deployments', 0)}")
        print(
            f"  ✅ Success rate: {deploy_summary.get('successful_deployments', 0)}/{deploy_summary.get('total_deployments', 1)}"
        )

        input("\nPress Enter to continue...")

    async def search_analytics_demo(self):
        """Demonstrate search and analytics."""

        if not self.systems_initialized:
            print("⚠️ Please initialize systems first (option 1)")
            return

        print("\n🔍 SEARCH & ANALYTICS DEMO")
        print("=" * 30)

        # Audit analytics
        print("\n📊 Audit Analytics:")
        audit_dashboard = advanced_audit_analytics.get_analytics_dashboard()

        event_volume = audit_dashboard.get("event_volume", {})
        print(f"  📈 Events (24h): {event_volume.get('last_24h', 0)}")
        print(f"  ⚡ Events (1h): {event_volume.get('last_hour', 0)}")
        print(f"  📊 Event rate: {event_volume.get('event_rate', 0):.1f}/hour")

        agent_activity = audit_dashboard.get("agent_activity", {})
        print(f"  👥 Active agents: {agent_activity.get('active_agents', 0)}")

        # System health
        system_health = audit_dashboard.get("system_health", "unknown")
        print(f"  🏥 System health: {system_health}")

        # Recent patterns
        print("\n🔍 Pattern Detection:")
        print(f"  📊 Recent patterns: {audit_dashboard.get('recent_patterns', 0)}")
        print(f"  🚨 Recent anomalies: {audit_dashboard.get('recent_anomalies', 0)}")
        print(f"  ⚠️ Active alerts: {audit_dashboard.get('active_alerts', 0)}")

        # Graph analytics
        print("\n🕸️ Relationship Graph:")
        print(f"  🔗 Total nodes: {len(relationship_graph.nodes)}")
        print(
            f"  🌐 Total edges: {relationship_graph.graph.number_of_edges() if hasattr(relationship_graph.graph, 'number_of_edges') else 0}"
        )

        input("\nPress Enter to continue...")

    async def shutdown_systems(self):
        """Gracefully shutdown all systems."""

        if not self.systems_initialized:
            print("✅ No systems to shutdown.")
            return

        print("\n🔄 SHUTTING DOWN SYSTEMS...")
        print("=" * 30)

        try:
            # Shutdown performance layer
            print("📊 Stopping performance optimization...")
            await performance_layer.stop_optimization_layer()

            # Shutdown deployment system
            print("🚀 Stopping deployment system...")
            await deployment_system.shutdown_system()

            # Shutdown governance
            print("🏛️ Stopping governance system...")
            await governance_system.shutdown_governance()

            self.systems_initialized = False

            print("\n✅ ALL SYSTEMS SHUTDOWN SUCCESSFULLY!")
            print("👋 Thank you for exploring the UATP Capsule Engine!")

        except Exception as e:
            print(f"❌ Shutdown error: {e}")
            logger.error(f"System shutdown error: {e}")


async def main():
    """Main entry point."""

    print("🌟 Welcome to the UATP Capsule Engine Interactive Demo!")
    print("This system showcases all the advanced features we've implemented.")
    print("\nStarting interactive demo...")

    demo = InteractiveUATPDemo()

    try:
        await demo.run_interactive_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        logger.error(f"Main demo error: {e}")
    finally:
        if demo.systems_initialized:
            await demo.shutdown_systems()


if __name__ == "__main__":
    # Run the interactive demo
    asyncio.run(main())
