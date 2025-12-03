#!/usr/bin/env python3
"""
Comprehensive Test Runner for UATP Capsule Engine
=================================================

This script runs all types of tests including unit tests, integration tests,
load tests, and performance benchmarks.
"""

import asyncio
import json
import logging
import os
import sys
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestRunner:
    """Comprehensive test runner for UATP system."""

    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None

        logger.info("🧪 Test Runner initialized")

    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests."""

        logger.info("🔬 Running unit tests...")

        try:
            # Run pytest
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__) + "/..",
            )

            success = result.returncode == 0

            return {
                "type": "unit_tests",
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": 0,  # pytest doesn't provide duration easily
            }

        except Exception as e:
            logger.error(f"❌ Unit tests failed: {e}")
            return {
                "type": "unit_tests",
                "success": False,
                "error": str(e),
                "duration": 0,
            }

    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""

        logger.info("🔗 Running integration tests...")

        try:
            # Run specific integration tests
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/test_integration.py", "-v"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__) + "/..",
            )

            success = result.returncode == 0

            return {
                "type": "integration_tests",
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": 0,
            }

        except Exception as e:
            logger.error(f"❌ Integration tests failed: {e}")
            return {
                "type": "integration_tests",
                "success": False,
                "error": str(e),
                "duration": 0,
            }

    async def run_load_tests(self) -> Dict[str, Any]:
        """Run load tests."""

        logger.info("🔥 Running load tests...")

        try:
            # Import and run load tests
            from src.testing.load_testing import BenchmarkSuite

            benchmark = BenchmarkSuite()

            # Run quick benchmark
            quick_results = await benchmark.run_quick_benchmark()

            # Generate report
            report = benchmark.generate_benchmark_report(quick_results)

            success = all(
                result["success_rate"] > 0.8
                for result in report["test_results"].values()
            )

            return {
                "type": "load_tests",
                "success": success,
                "results": report,
                "duration": sum(
                    result.total_duration for result in quick_results.values()
                ),
            }

        except Exception as e:
            logger.error(f"❌ Load tests failed: {e}")
            return {
                "type": "load_tests",
                "success": False,
                "error": str(e),
                "duration": 0,
            }

    async def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarks."""

        logger.info("📊 Running performance benchmarks...")

        try:
            from src.testing.performance_benchmarks import PerformanceBenchmark

            benchmark = PerformanceBenchmark()

            # Run key benchmarks
            results = {}

            # Capsule creation benchmark
            results["capsule_creation"] = await benchmark.benchmark_capsule_creation(50)

            # Capsule retrieval benchmark
            results["capsule_retrieval"] = await benchmark.benchmark_capsule_retrieval(
                100
            )

            # Generate report
            report = benchmark.generate_report(results)

            # Check if performance is acceptable
            success = all(result["success_rate"] > 0.9 for result in results.values())

            return {
                "type": "performance_benchmarks",
                "success": success,
                "results": report,
                "duration": sum(result["total_time"] for result in results.values()),
            }

        except Exception as e:
            logger.error(f"❌ Performance benchmarks failed: {e}")
            return {
                "type": "performance_benchmarks",
                "success": False,
                "error": str(e),
                "duration": 0,
            }

    def run_health_checks(self) -> Dict[str, Any]:
        """Run health checks."""

        logger.info("🏥 Running health checks...")

        try:
            import asyncio
            from src.monitoring.health_checks import get_health_manager

            async def check_health():
                health_manager = get_health_manager()
                system_health = await health_manager.get_system_health()
                return system_health

            health_result = asyncio.run(check_health())

            success = health_result["overall_status"] in ["healthy", "degraded"]

            return {
                "type": "health_checks",
                "success": success,
                "results": health_result,
                "duration": 0,
            }

        except Exception as e:
            logger.error(f"❌ Health checks failed: {e}")
            return {
                "type": "health_checks",
                "success": False,
                "error": str(e),
                "duration": 0,
            }

    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests."""

        logger.info("🔒 Running security tests...")

        try:
            # Run security-focused tests
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-k", "security", "-v"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__) + "/..",
            )

            success = result.returncode == 0

            return {
                "type": "security_tests",
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": 0,
            }

        except Exception as e:
            logger.error(f"❌ Security tests failed: {e}")
            return {
                "type": "security_tests",
                "success": False,
                "error": str(e),
                "duration": 0,
            }

    async def run_all_tests(self, test_types: List[str] = None) -> Dict[str, Any]:
        """Run all or specified test types."""

        if test_types is None:
            test_types = [
                "unit_tests",
                "integration_tests",
                "health_checks",
                "security_tests",
                "load_tests",
                "performance_benchmarks",
            ]

        logger.info(f"🧪 Running test suite: {', '.join(test_types)}")

        self.start_time = datetime.now()
        results = {}

        # Run each test type
        for test_type in test_types:
            logger.info(f"▶️ Running {test_type}...")

            try:
                if test_type == "unit_tests":
                    results[test_type] = self.run_unit_tests()
                elif test_type == "integration_tests":
                    results[test_type] = self.run_integration_tests()
                elif test_type == "health_checks":
                    results[test_type] = self.run_health_checks()
                elif test_type == "security_tests":
                    results[test_type] = self.run_security_tests()
                elif test_type == "load_tests":
                    results[test_type] = await self.run_load_tests()
                elif test_type == "performance_benchmarks":
                    results[test_type] = await self.run_performance_benchmarks()
                else:
                    logger.warning(f"⚠️ Unknown test type: {test_type}")
                    continue

                # Log result
                if results[test_type]["success"]:
                    logger.info(f"✅ {test_type} passed")
                else:
                    logger.error(f"❌ {test_type} failed")

            except Exception as e:
                logger.error(f"❌ {test_type} crashed: {e}")
                results[test_type] = {
                    "type": test_type,
                    "success": False,
                    "error": str(e),
                    "duration": 0,
                }

        self.end_time = datetime.now()

        # Generate summary
        summary = self.generate_summary(results)

        return {
            "summary": summary,
            "results": results,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "total_duration": (self.end_time - self.start_time).total_seconds(),
        }

    def generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary."""

        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result["success"])
        failed_tests = total_tests - passed_tests

        success_rate = passed_tests / total_tests if total_tests > 0 else 0

        # Calculate total duration
        total_duration = sum(result.get("duration", 0) for result in results.values())

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "overall_status": "PASSED" if success_rate == 1.0 else "FAILED",
        }

    def save_results(self, results: Dict[str, Any], filename: str):
        """Save test results to file."""

        os.makedirs("reports", exist_ok=True)
        filepath = os.path.join("reports", filename)

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"📄 Test results saved to {filepath}")

    def print_summary(self, results: Dict[str, Any]):
        """Print test summary to console."""

        print("\n" + "=" * 60)
        print("🧪 TEST SUMMARY")
        print("=" * 60)

        summary = results["summary"]

        print(f"📊 Overall Status: {summary['overall_status']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1%}")
        print(f"✅ Passed: {summary['passed_tests']}")
        print(f"❌ Failed: {summary['failed_tests']}")
        print(f"⏱️ Total Duration: {summary['total_duration']:.1f}s")

        print("\n📋 Test Results:")
        for test_type, result in results["results"].items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = result.get("duration", 0)
            print(f"   {test_type}: {status} ({duration:.1f}s)")

            if not result["success"] and "error" in result:
                print(f"      Error: {result['error']}")

        print("\n" + "=" * 60)


async def main():
    """Main test runner function."""

    import argparse

    parser = argparse.ArgumentParser(description="UATP Test Runner")
    parser.add_argument(
        "--types",
        nargs="+",
        choices=[
            "unit_tests",
            "integration_tests",
            "health_checks",
            "security_tests",
            "load_tests",
            "performance_benchmarks",
        ],
        help="Test types to run",
    )
    parser.add_argument(
        "--output", default="test_results.json", help="Output file for test results"
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")

    args = parser.parse_args()

    # Configure logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    print("🧪 UATP Comprehensive Test Runner")
    print("=" * 50)

    runner = TestRunner()

    try:
        # Run tests
        results = await runner.run_all_tests(args.types)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        runner.save_results(results, filename)

        # Print summary
        runner.print_summary(results)

        # Exit with appropriate code
        exit_code = 0 if results["summary"]["overall_status"] == "PASSED" else 1
        sys.exit(exit_code)

    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
