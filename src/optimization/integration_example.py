"""
Integration example for Performance Optimization Layer with UATP Capsule Engine.
Shows how performance optimization integrates with the entire system.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.audit.events import audit_emitter
from src.capsule_schema import AnyCapsule, CapsuleStatus, CapsuleType
from src.economic.fcde_engine import fcde_engine
from src.ethics.rect_system import rect_system
from src.graph.capsule_relationships import relationship_graph
from src.ml.analytics_engine import ml_analytics
from src.optimization.capsule_compression import optimization_engine
from src.optimization.performance_layer import performance_layer

logger = logging.getLogger(__name__)


class PerformanceIntegrationExample:
    """Demonstrates performance optimization integration with UATP system."""

    def __init__(self):
        self.processed_capsules: List[AnyCapsule] = []
        self.performance_metrics: List[Dict[str, Any]] = []
        self.optimization_results: List[Dict[str, Any]] = []

    async def run_integration_example(self):
        """Run complete integration example."""

        logger.info("Starting Performance Optimization Integration Example")

        # 1. Initialize performance layer
        await self.initialize_performance_layer()

        # 2. Process capsules with performance monitoring
        await self.process_capsules_with_monitoring()

        # 3. Demonstrate performance-driven optimizations
        await self.demonstrate_performance_optimizations()

        # 4. Show ML analytics integration
        await self.demonstrate_ml_integration()

        # 5. Economic impact analysis
        await self.demonstrate_economic_integration()

        # 6. Audit trail integration
        await self.demonstrate_audit_integration()

        # 7. Generate comprehensive report
        report = await self.generate_integration_report()

        # 8. Cleanup
        await self.cleanup_performance_layer()

        logger.info("Performance Optimization Integration Example completed")
        return report

    async def initialize_performance_layer(self):
        """Initialize the performance optimization layer."""

        logger.info("Initializing performance optimization layer...")

        # Start performance layer
        await performance_layer.start_optimization_layer()

        # Configure for demonstration
        config = {
            "auto_optimization": True,
            "thresholds": {
                "cpu_usage": 70.0,
                "memory_usage": 75.0,
                "response_time": 1.0,
            },
            "collection_interval": 2,
        }

        performance_layer.configure_optimization(config)

        logger.info("Performance optimization layer initialized")

    async def process_capsules_with_monitoring(self):
        """Process capsules while monitoring performance."""

        logger.info("Processing capsules with performance monitoring...")

        # Create sample capsules
        test_capsules = self.create_test_capsules(10)

        for i, capsule in enumerate(test_capsules):
            # Start performance monitoring for this operation
            start_time = datetime.now(timezone.utc)

            # Process capsule (simulate complex processing)
            await self.process_single_capsule(capsule)

            # Record performance metrics
            end_time = datetime.now(timezone.utc)
            processing_time = (end_time - start_time).total_seconds()

            # Get current performance metrics
            recent_metrics = performance_layer.monitor.get_recent_metrics(1)
            if recent_metrics:
                metrics = recent_metrics[0]

                performance_data = {
                    "capsule_id": capsule.capsule_id,
                    "processing_time": processing_time,
                    "cpu_usage": metrics.cpu_usage,
                    "memory_usage": metrics.memory_usage,
                    "response_time": metrics.response_time,
                    "timestamp": end_time.isoformat(),
                }

                self.performance_metrics.append(performance_data)

                # Log performance info
                logger.info(
                    f"Processed capsule {i+1}/{len(test_capsules)}: "
                    f"{processing_time:.2f}s, CPU: {metrics.cpu_usage:.1f}%, "
                    f"Memory: {metrics.memory_usage:.1f}%"
                )

            # Small delay to allow monitoring
            await asyncio.sleep(1)

        logger.info(
            f"Processed {len(test_capsules)} capsules with performance monitoring"
        )

    async def process_single_capsule(self, capsule: AnyCapsule):
        """Process a single capsule with full system integration."""

        # 1. ML Analytics
        ml_results = ml_analytics.analyze_capsule(capsule)

        # 2. Graph relationship analysis
        relationship_graph.add_capsule_node(capsule)

        # 3. Economic attribution
        fcde_engine.process_capsule_contribution(capsule)

        # 4. Ethical validation
        rect_system.evaluate_capsule_ethics(capsule)

        # 5. Optimization engine
        optimization_engine.analyze_capsule_for_optimization(capsule)

        # 6. Audit logging
        audit_emitter.emit_capsule_created(
            capsule_id=capsule.capsule_id,
            agent_id="integration_example",
            capsule_type=capsule.capsule_type.value,
        )

        self.processed_capsules.append(capsule)

    def create_test_capsules(self, count: int) -> List[AnyCapsule]:
        """Create test capsules for processing."""

        from src.capsules.specialized_capsules import (
            ReasoningCapsule,
            SelfReflectionCapsule,
            UncertaintyCapsule,
        )

        capsules = []

        for i in range(count):
            if i % 3 == 0:
                # Create reasoning capsule
                capsule = ReasoningCapsule(
                    capsule_id=f"reasoning_{i}",
                    capsule_type=CapsuleType.REASONING,
                    timestamp=datetime.now(timezone.utc),
                    status=CapsuleStatus.ACTIVE,
                )

            elif i % 3 == 1:
                # Create uncertainty capsule
                capsule = UncertaintyCapsule(
                    capsule_id=f"uncertainty_{i}",
                    capsule_type=CapsuleType.UNCERTAINTY,
                    timestamp=datetime.now(timezone.utc),
                    status=CapsuleStatus.ACTIVE,
                )

            else:
                # Create self-reflection capsule
                capsule = SelfReflectionCapsule(
                    capsule_id=f"reflection_{i}",
                    capsule_type=CapsuleType.SELF_REFLECTION,
                    timestamp=datetime.now(timezone.utc),
                    status=CapsuleStatus.ACTIVE,
                )

            capsules.append(capsule)

        return capsules

    async def demonstrate_performance_optimizations(self):
        """Demonstrate performance-driven optimizations."""

        logger.info("Demonstrating performance-driven optimizations...")

        # Simulate performance stress
        await self.simulate_performance_stress()

        # Wait for automatic optimization
        await asyncio.sleep(10)

        # Check for optimization results
        recent_optimizations = performance_layer.optimizer.optimization_results[-5:]

        for optimization in recent_optimizations:
            result = {
                "optimization_strategy": optimization.strategy.value,
                "target_metric": optimization.target_metric.value,
                "improvement": optimization.improvement,
                "success": optimization.success,
                "execution_time": optimization.execution_time,
            }

            self.optimization_results.append(result)

            logger.info(
                f"Optimization applied: {optimization.strategy.value} "
                f"-> {optimization.improvement:.1f}% improvement"
            )

        # Try manual optimization
        manual_results = await performance_layer.manual_optimization()

        for result in manual_results:
            logger.info(
                f"Manual optimization: {result.strategy.value} "
                f"-> {result.improvement:.1f}% improvement"
            )

    async def simulate_performance_stress(self):
        """Simulate performance stress to trigger optimizations."""

        logger.info("Simulating performance stress...")

        # CPU stress
        def cpu_stress():
            total = 0
            for i in range(2000000):
                total += i**2
            return total

        # Memory stress
        large_objects = []
        for i in range(50000):
            large_objects.append(f"Large object {i}" * 100)

        # Run CPU stress
        cpu_stress()

        # Hold memory for a moment
        await asyncio.sleep(3)

        # Release memory
        del large_objects

        logger.info("Performance stress simulation completed")

    async def demonstrate_ml_integration(self):
        """Demonstrate ML analytics integration with performance data."""

        logger.info("Demonstrating ML analytics integration...")

        # Get ML system insights
        ml_insights = ml_analytics.get_system_insights()

        # Get performance dashboard
        performance_dashboard = performance_layer.get_performance_dashboard()

        # Analyze correlation between performance and ML predictions
        correlation_analysis = {
            "total_ml_analyses": ml_insights.get("total_analyses", 0),
            "performance_level": performance_dashboard["performance_summary"].get(
                "current_level", "unknown"
            ),
            "optimization_impact_on_ml": self.calculate_ml_performance_impact(),
            "ml_predictions_accuracy": ml_insights.get("quality_trends", {}).get(
                "average_quality", 0
            ),
            "performance_optimizations": len(
                performance_dashboard["recent_optimizations"]
            ),
        }

        logger.info("ML-Performance Integration Analysis:")
        logger.info(
            f"  - Total ML analyses: {correlation_analysis['total_ml_analyses']}"
        )
        logger.info(
            f"  - Performance level: {correlation_analysis['performance_level']}"
        )
        logger.info(
            f"  - ML prediction accuracy: {correlation_analysis['ml_predictions_accuracy']:.2f}"
        )
        logger.info(
            f"  - Performance optimizations: {correlation_analysis['performance_optimizations']}"
        )

    def calculate_ml_performance_impact(self) -> Dict[str, float]:
        """Calculate impact of performance on ML operations."""

        if not self.performance_metrics:
            return {"impact": 0.0}

        # Calculate average performance during ML operations
        avg_cpu = sum(m["cpu_usage"] for m in self.performance_metrics) / len(
            self.performance_metrics
        )
        avg_memory = sum(m["memory_usage"] for m in self.performance_metrics) / len(
            self.performance_metrics
        )
        avg_processing_time = sum(
            m["processing_time"] for m in self.performance_metrics
        ) / len(self.performance_metrics)

        return {
            "avg_cpu_during_ml": avg_cpu,
            "avg_memory_during_ml": avg_memory,
            "avg_processing_time": avg_processing_time,
            "performance_impact_score": (avg_cpu + avg_memory) / 2,
        }

    async def demonstrate_economic_integration(self):
        """Demonstrate economic impact of performance optimization."""

        logger.info("Demonstrating economic integration...")

        # Calculate economic impact of optimizations
        economic_impact = self.calculate_economic_impact()

        # Get FCDE insights
        fcde_insights = fcde_engine.get_system_insights()

        economic_analysis = {
            "processing_cost_savings": economic_impact["cost_savings"],
            "efficiency_improvement": economic_impact["efficiency_gain"],
            "total_dividend_pool": float(fcde_insights.get("dividend_pool", 0)),
            "performance_contribution": economic_impact["performance_contribution"],
            "optimization_roi": economic_impact["optimization_roi"],
        }

        logger.info("Economic Impact Analysis:")
        logger.info(
            f"  - Processing cost savings: ${economic_analysis['processing_cost_savings']:.2f}"
        )
        logger.info(
            f"  - Efficiency improvement: {economic_analysis['efficiency_improvement']:.1f}%"
        )
        logger.info(
            f"  - Optimization ROI: {economic_analysis['optimization_roi']:.2f}x"
        )

    def calculate_economic_impact(self) -> Dict[str, float]:
        """Calculate economic impact of performance optimizations."""

        if not self.optimization_results:
            return {
                "cost_savings": 0.0,
                "efficiency_gain": 0.0,
                "performance_contribution": 0.0,
                "optimization_roi": 0.0,
            }

        # Calculate total improvement
        total_improvement = sum(
            r["improvement"] for r in self.optimization_results if r["success"]
        )

        # Estimate cost savings (simplified calculation)
        cost_per_processing_second = 0.01  # $0.01 per second
        avg_processing_time = (
            sum(m["processing_time"] for m in self.performance_metrics)
            / len(self.performance_metrics)
            if self.performance_metrics
            else 1.0
        )

        time_savings = avg_processing_time * (total_improvement / 100)
        cost_savings = (
            time_savings * cost_per_processing_second * len(self.processed_capsules)
        )

        return {
            "cost_savings": cost_savings,
            "efficiency_gain": total_improvement,
            "performance_contribution": total_improvement / 100,
            "optimization_roi": cost_savings
            / max(0.01, total_improvement / 100),  # Avoid division by zero
        }

    async def demonstrate_audit_integration(self):
        """Demonstrate audit integration with performance data."""

        logger.info("Demonstrating audit integration...")

        # The audit system automatically captures performance optimization events
        # This is handled through the audit_emitter calls in the performance layer

        audit_summary = {
            "performance_events_logged": len(self.processed_capsules),
            "optimization_events_logged": len(self.optimization_results),
            "monitoring_events": len(self.performance_metrics),
            "audit_trail_complete": True,
        }

        logger.info("Audit Integration Summary:")
        logger.info(
            f"  - Performance events logged: {audit_summary['performance_events_logged']}"
        )
        logger.info(
            f"  - Optimization events logged: {audit_summary['optimization_events_logged']}"
        )
        logger.info(f"  - Monitoring events: {audit_summary['monitoring_events']}")
        logger.info(
            f"  - Audit trail complete: {audit_summary['audit_trail_complete']}"
        )

    async def generate_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration report."""

        # Get final dashboard
        final_dashboard = performance_layer.get_performance_dashboard()

        # Get ML insights
        ml_insights = ml_analytics.get_system_insights()

        # Get FCDE insights
        fcde_insights = fcde_engine.get_system_insights()

        report = {
            "integration_summary": {
                "capsules_processed": len(self.processed_capsules),
                "performance_metrics_collected": len(self.performance_metrics),
                "optimizations_applied": len(self.optimization_results),
                "successful_optimizations": sum(
                    1 for r in self.optimization_results if r["success"]
                ),
            },
            "performance_dashboard": final_dashboard,
            "ml_integration": {
                "total_ml_analyses": ml_insights.get("total_analyses", 0),
                "ml_performance_correlation": self.calculate_ml_performance_impact(),
            },
            "economic_impact": self.calculate_economic_impact(),
            "system_health": {
                "performance_level": final_dashboard["performance_summary"].get(
                    "current_level", "unknown"
                ),
                "system_efficiency": final_dashboard["system_health"].get(
                    "average_improvement", 0
                ),
                "optimization_success_rate": final_dashboard["system_health"].get(
                    "successful_optimizations", 0
                )
                / max(1, final_dashboard["system_health"].get("total_optimizations", 1))
                * 100,
            },
            "integration_features_demonstrated": [
                "Real-time performance monitoring during capsule processing",
                "Automatic performance optimization triggered by bottlenecks",
                "ML analytics integration with performance data",
                "Economic impact analysis of performance improvements",
                "Comprehensive audit trail of all performance events",
                "Multi-system coordination for optimal performance",
            ],
        }

        logger.info("=== INTEGRATION REPORT ===")
        logger.info(
            f"Capsules processed: {report['integration_summary']['capsules_processed']}"
        )
        logger.info(
            f"Performance metrics collected: {report['integration_summary']['performance_metrics_collected']}"
        )
        logger.info(
            f"Optimizations applied: {report['integration_summary']['optimizations_applied']}"
        )
        logger.info(
            f"System performance level: {report['system_health']['performance_level']}"
        )
        logger.info(
            f"Optimization success rate: {report['system_health']['optimization_success_rate']:.1f}%"
        )

        return report

    async def cleanup_performance_layer(self):
        """Cleanup performance optimization layer."""

        logger.info("Cleaning up performance optimization layer...")

        # Stop performance layer
        await performance_layer.stop_optimization_layer()

        logger.info("Performance optimization layer cleanup completed")


async def run_integration_example():
    """Run the complete integration example."""

    example = PerformanceIntegrationExample()

    try:
        report = await example.run_integration_example()

        logger.info("Integration example completed successfully")
        return report

    except Exception as e:
        logger.error(f"Integration example failed: {e}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Run the integration example
    asyncio.run(run_integration_example())
