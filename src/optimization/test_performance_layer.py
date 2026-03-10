"""
Test suite for the Performance Optimization Layer.
Demonstrates comprehensive performance monitoring, bottleneck detection, and optimization.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from .performance_layer import (
    PerformanceMetric,
    performance_layer,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceLayerDemo:
    """Demonstrates the Performance Optimization Layer functionality."""

    def __init__(self):
        self.layer = performance_layer
        self.demo_results: List[Dict[str, Any]] = []

    async def run_comprehensive_demo(self):
        """Run comprehensive performance layer demonstration."""

        logger.info("Starting Performance Optimization Layer Demo")

        # 1. Start the performance optimization layer
        await self.demo_layer_startup()

        # 2. Monitor performance metrics
        await self.demo_performance_monitoring()

        # 3. Simulate performance bottlenecks
        await self.demo_bottleneck_simulation()

        # 4. Demonstrate automatic optimization
        await self.demo_automatic_optimization()

        # 5. Show manual optimization
        await self.demo_manual_optimization()

        # 6. Display performance dashboard
        await self.demo_performance_dashboard()

        # 7. Configure optimization settings
        await self.demo_configuration()

        # 8. Cleanup
        await self.demo_layer_shutdown()

        logger.info("Performance Optimization Layer Demo completed")

    async def demo_layer_startup(self):
        """Demonstrate layer startup."""

        logger.info("=== Performance Layer Startup Demo ===")

        start_time = time.time()

        # Start the performance optimization layer
        await self.layer.start_optimization_layer()

        startup_time = time.time() - start_time

        result = {
            "demo": "layer_startup",
            "startup_time": startup_time,
            "monitoring_active": self.layer.monitor.monitoring,
            "optimization_active": self.layer.running,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.demo_results.append(result)
        logger.info(f"Performance layer started in {startup_time:.2f} seconds")

        # Wait a bit for monitoring to collect initial data
        await asyncio.sleep(2)

    async def demo_performance_monitoring(self):
        """Demonstrate performance monitoring."""

        logger.info("=== Performance Monitoring Demo ===")

        # Let monitoring run for a few cycles
        await asyncio.sleep(10)

        # Get recent metrics
        recent_metrics = self.layer.monitor.get_recent_metrics(5)

        if recent_metrics:
            latest_metrics = recent_metrics[-1]

            result = {
                "demo": "performance_monitoring",
                "metrics_collected": len(recent_metrics),
                "latest_metrics": latest_metrics.to_dict(),
                "performance_level": self.layer.monitor._determine_performance_level(
                    latest_metrics
                ).value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            self.demo_results.append(result)
            logger.info(f"Collected {len(recent_metrics)} performance metrics")
            logger.info(f"Latest CPU usage: {latest_metrics.cpu_usage:.1f}%")
            logger.info(f"Latest memory usage: {latest_metrics.memory_usage:.1f}%")
            logger.info(
                f"Performance level: {self.layer.monitor._determine_performance_level(latest_metrics).value}"
            )
        else:
            logger.warning("No performance metrics collected yet")

    async def demo_bottleneck_simulation(self):
        """Demonstrate bottleneck detection."""

        logger.info("=== Bottleneck Detection Demo ===")

        # Simulate CPU intensive task
        await self.simulate_cpu_load()

        # Simulate memory intensive task
        await self.simulate_memory_load()

        # Wait for metrics to be collected
        await asyncio.sleep(5)

        # Detect bottlenecks
        bottlenecks = self.layer.detector.detect_bottlenecks()

        result = {
            "demo": "bottleneck_detection",
            "bottlenecks_detected": len(bottlenecks),
            "bottlenecks": [b.to_dict() for b in bottlenecks],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.demo_results.append(result)
        logger.info(f"Detected {len(bottlenecks)} performance bottlenecks")

        for bottleneck in bottlenecks:
            logger.info(
                f"Bottleneck: {bottleneck.description} (severity: {bottleneck.severity})"
            )

    async def simulate_cpu_load(self):
        """Simulate CPU intensive load."""

        logger.info("Simulating CPU intensive task...")

        # CPU intensive calculation
        def cpu_intensive_task():
            total = 0
            for i in range(1000000):
                total += i * i
            return total

        # Run CPU intensive task
        start_time = time.time()
        cpu_intensive_task()
        duration = time.time() - start_time

        logger.info(f"CPU intensive task completed in {duration:.2f} seconds")

    async def simulate_memory_load(self):
        """Simulate memory intensive load."""

        logger.info("Simulating memory intensive task...")

        # Allocate some memory
        large_data = []
        for i in range(100000):
            large_data.append(f"Data item {i}" * 10)

        # Hold memory for a moment
        await asyncio.sleep(2)

        # Release memory
        del large_data

        logger.info("Memory intensive task completed")

    async def demo_automatic_optimization(self):
        """Demonstrate automatic optimization."""

        logger.info("=== Automatic Optimization Demo ===")

        # Wait for automatic optimization cycle
        await asyncio.sleep(35)  # Wait for optimization loop to run

        # Get optimization results
        recent_optimizations = self.layer.optimizer.optimization_results[-5:]

        result = {
            "demo": "automatic_optimization",
            "optimizations_performed": len(recent_optimizations),
            "optimizations": [o.to_dict() for o in recent_optimizations],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.demo_results.append(result)
        logger.info(
            f"Automatic optimization performed {len(recent_optimizations)} optimizations"
        )

        for optimization in recent_optimizations:
            logger.info(
                f"Optimization: {optimization.strategy.value} - {optimization.improvement:.1f}% improvement"
            )

    async def demo_manual_optimization(self):
        """Demonstrate manual optimization."""

        logger.info("=== Manual Optimization Demo ===")

        # Trigger manual optimization
        optimization_results = await self.layer.manual_optimization()

        result = {
            "demo": "manual_optimization",
            "optimizations_applied": len(optimization_results),
            "results": [r.to_dict() for r in optimization_results],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.demo_results.append(result)
        logger.info(
            f"Manual optimization applied {len(optimization_results)} optimizations"
        )

        # Try optimization for specific metric
        cpu_optimizations = await self.layer.manual_optimization(
            PerformanceMetric.CPU_USAGE
        )
        logger.info(
            f"CPU-specific optimization applied {len(cpu_optimizations)} optimizations"
        )

    async def demo_performance_dashboard(self):
        """Demonstrate performance dashboard."""

        logger.info("=== Performance Dashboard Demo ===")

        # Get comprehensive dashboard data
        dashboard = self.layer.get_performance_dashboard()

        result = {
            "demo": "performance_dashboard",
            "dashboard_data": dashboard,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.demo_results.append(result)

        # Display key dashboard metrics
        logger.info("Performance Dashboard Summary:")
        logger.info(
            f"  - Performance Level: {dashboard['performance_summary'].get('current_level', 'unknown')}"
        )
        logger.info(
            f"  - Average CPU Usage: {dashboard['performance_summary'].get('avg_cpu_usage', 0):.1f}%"
        )
        logger.info(
            f"  - Average Memory Usage: {dashboard['performance_summary'].get('avg_memory_usage', 0):.1f}%"
        )
        logger.info(f"  - Recent Bottlenecks: {len(dashboard['recent_bottlenecks'])}")
        logger.info(
            f"  - Recent Optimizations: {len(dashboard['recent_optimizations'])}"
        )
        logger.info(
            f"  - Total Optimizations: {dashboard['system_health']['total_optimizations']}"
        )
        logger.info(
            f"  - Success Rate: {dashboard['system_health']['successful_optimizations']}/{dashboard['system_health']['total_optimizations']}"
        )

    async def demo_configuration(self):
        """Demonstrate configuration options."""

        logger.info("=== Configuration Demo ===")

        # Configure optimization settings
        config = {
            "auto_optimization": True,
            "thresholds": {
                PerformanceMetric.CPU_USAGE: 75.0,
                PerformanceMetric.MEMORY_USAGE: 80.0,
                PerformanceMetric.RESPONSE_TIME: 1.5,
            },
            "collection_interval": 3,
        }

        self.layer.configure_optimization(config)

        result = {
            "demo": "configuration",
            "configuration_applied": config,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.demo_results.append(result)
        logger.info("Performance optimization configuration updated")

    async def demo_layer_shutdown(self):
        """Demonstrate layer shutdown."""

        logger.info("=== Performance Layer Shutdown Demo ===")

        start_time = time.time()

        # Stop the performance optimization layer
        await self.layer.stop_optimization_layer()

        shutdown_time = time.time() - start_time

        result = {
            "demo": "layer_shutdown",
            "shutdown_time": shutdown_time,
            "monitoring_active": self.layer.monitor.monitoring,
            "optimization_active": self.layer.running,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.demo_results.append(result)
        logger.info(f"Performance layer stopped in {shutdown_time:.2f} seconds")

    def generate_demo_report(self) -> Dict[str, Any]:
        """Generate comprehensive demo report."""

        return {
            "demo_completed": True,
            "total_demos": len(self.demo_results),
            "demo_results": self.demo_results,
            "summary": {
                "demos_run": [r["demo"] for r in self.demo_results],
                "total_runtime": sum(
                    r.get("startup_time", 0) + r.get("shutdown_time", 0)
                    for r in self.demo_results
                ),
                "performance_layer_features": [
                    "Real-time performance monitoring",
                    "Automatic bottleneck detection",
                    "Adaptive optimization strategies",
                    "Manual optimization controls",
                    "Comprehensive performance dashboard",
                    "Configurable thresholds and settings",
                ],
            },
        }


async def run_performance_demo():
    """Run the performance optimization layer demonstration."""

    demo = PerformanceLayerDemo()

    try:
        await demo.run_comprehensive_demo()

        # Generate and display report
        report = demo.generate_demo_report()

        logger.info("=== DEMO REPORT ===")
        logger.info(f"Total demos completed: {report['total_demos']}")
        logger.info(f"Demos run: {', '.join(report['summary']['demos_run'])}")
        logger.info("Performance layer features demonstrated:")
        for feature in report["summary"]["performance_layer_features"]:
            logger.info(f"  - {feature}")

        return report

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    # Run the demo
    asyncio.run(run_performance_demo())
