#!/usr/bin/env python3
"""
Load Testing Framework for UATP Capsule Engine
==============================================

This module provides comprehensive load testing capabilities for the UATP system,
including stress testing, performance benchmarking, and scalability analysis.
"""

import asyncio
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from statistics import mean, median, stdev
import threading
import random
import string

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Individual test result."""

    operation: str
    duration: float
    success: bool
    error: Optional[str] = None
    timestamp: datetime = None
    response_size: int = 0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class LoadTestConfig:
    """Load test configuration."""

    name: str
    target_url: str
    concurrent_users: int
    duration_seconds: int
    ramp_up_seconds: int = 0
    operations: List[str] = None
    auth_token: Optional[str] = None

    def __post_init__(self):
        if self.operations is None:
            self.operations = ["read", "write", "search"]


@dataclass
class LoadTestReport:
    """Load test report."""

    config: LoadTestConfig
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration: float
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    errors: Dict[str, int]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class LoadTestRunner:
    """Load test runner for UATP system."""

    def __init__(self):
        self.results: List[TestResult] = []
        self.running = False
        self.start_time = None
        self.end_time = None
        self.lock = threading.Lock()

        logger.info("🔥 Load Test Runner initialized")

    async def run_load_test(self, config: LoadTestConfig) -> LoadTestReport:
        """Run a load test with the given configuration."""

        logger.info(f"🚀 Starting load test: {config.name}")
        logger.info(f"   Target: {config.target_url}")
        logger.info(f"   Concurrent users: {config.concurrent_users}")
        logger.info(f"   Duration: {config.duration_seconds}s")
        logger.info(f"   Ramp up: {config.ramp_up_seconds}s")

        self.results = []
        self.running = True
        self.start_time = time.time()

        try:
            # Create tasks for concurrent users
            tasks = []
            for user_id in range(config.concurrent_users):
                # Calculate delay for ramp-up
                delay = (
                    (config.ramp_up_seconds * user_id) / config.concurrent_users
                    if config.ramp_up_seconds > 0
                    else 0
                )

                task = asyncio.create_task(
                    self._user_simulation(user_id, config, delay)
                )
                tasks.append(task)

            # Wait for test duration
            await asyncio.sleep(config.duration_seconds + config.ramp_up_seconds)

            # Stop all tasks
            self.running = False
            for task in tasks:
                task.cancel()

            # Wait for tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

            self.end_time = time.time()

            # Generate report
            report = self._generate_report(config)

            logger.info(f"✅ Load test completed: {config.name}")
            logger.info(f"   Total requests: {report.total_requests}")
            logger.info(f"   Success rate: {(1 - report.error_rate) * 100:.1f}%")
            logger.info(f"   RPS: {report.requests_per_second:.1f}")
            logger.info(f"   Avg response time: {report.avg_response_time:.3f}s")

            return report

        except Exception as e:
            logger.error(f"❌ Load test failed: {e}")
            raise

    async def _user_simulation(
        self, user_id: int, config: LoadTestConfig, delay: float
    ):
        """Simulate a single user's load."""

        if delay > 0:
            await asyncio.sleep(delay)

        import aiohttp

        async with aiohttp.ClientSession() as session:
            while self.running:
                try:
                    # Choose random operation
                    operation = random.choice(config.operations)

                    # Execute operation
                    result = await self._execute_operation(
                        session, operation, config, user_id
                    )

                    # Record result
                    with self.lock:
                        self.results.append(result)

                    # Small delay between requests
                    await asyncio.sleep(random.uniform(0.1, 0.5))

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    # Record error
                    with self.lock:
                        self.results.append(
                            TestResult(
                                operation="error",
                                duration=0.0,
                                success=False,
                                error=str(e),
                            )
                        )

    async def _execute_operation(
        self,
        session: aiohttp.ClientSession,
        operation: str,
        config: LoadTestConfig,
        user_id: int,
    ) -> TestResult:
        """Execute a single operation."""

        start_time = time.time()

        try:
            headers = {}
            if config.auth_token:
                headers["Authorization"] = f"Bearer {config.auth_token}"

            if operation == "read":
                # Test capsule listing
                async with session.get(
                    f"{config.target_url}/api/capsules", headers=headers, timeout=30
                ) as response:
                    content = await response.text()
                    success = response.status == 200

                    return TestResult(
                        operation="read",
                        duration=time.time() - start_time,
                        success=success,
                        response_size=len(content),
                        error=None if success else f"HTTP {response.status}",
                    )

            elif operation == "write":
                # Test capsule creation
                test_capsule = {
                    "capsule_id": f"load_test_{user_id}_{int(time.time() * 1000)}",
                    "type": "interaction_capsule",
                    "platform": "load_test",
                    "user_id": f"test_user_{user_id}",
                    "user_message": f"Load test message from user {user_id}",
                    "ai_response": f"Response to load test message {random.randint(1, 1000)}",
                    "significance_score": random.uniform(0.5, 5.0),
                    "timestamp": datetime.now().isoformat(),
                }

                async with session.post(
                    f"{config.target_url}/api/capsules",
                    json=test_capsule,
                    headers=headers,
                    timeout=30,
                ) as response:
                    content = await response.text()
                    success = response.status in [200, 201]

                    return TestResult(
                        operation="write",
                        duration=time.time() - start_time,
                        success=success,
                        response_size=len(content),
                        error=None if success else f"HTTP {response.status}",
                    )

            elif operation == "search":
                # Test capsule search
                search_terms = ["test", "load", "capsule", "message", "response"]
                query = random.choice(search_terms)

                async with session.get(
                    f"{config.target_url}/api/capsules/search",
                    params={"q": query, "limit": 10},
                    headers=headers,
                    timeout=30,
                ) as response:
                    content = await response.text()
                    success = response.status == 200

                    return TestResult(
                        operation="search",
                        duration=time.time() - start_time,
                        success=success,
                        response_size=len(content),
                        error=None if success else f"HTTP {response.status}",
                    )

            elif operation == "health":
                # Test health check
                async with session.get(
                    f"{config.target_url}/health", timeout=10
                ) as response:
                    content = await response.text()
                    success = response.status == 200

                    return TestResult(
                        operation="health",
                        duration=time.time() - start_time,
                        success=success,
                        response_size=len(content),
                        error=None if success else f"HTTP {response.status}",
                    )

            else:
                return TestResult(
                    operation=operation,
                    duration=0.0,
                    success=False,
                    error=f"Unknown operation: {operation}",
                )

        except Exception as e:
            return TestResult(
                operation=operation,
                duration=time.time() - start_time,
                success=False,
                error=str(e),
            )

    def _generate_report(self, config: LoadTestConfig) -> LoadTestReport:
        """Generate load test report."""

        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r.success)
        failed_requests = total_requests - successful_requests

        if total_requests == 0:
            return LoadTestReport(
                config=config,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                total_duration=0.0,
                avg_response_time=0.0,
                median_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                requests_per_second=0.0,
                error_rate=0.0,
                errors={},
            )

        # Calculate timing statistics
        response_times = [r.duration for r in self.results]
        response_times.sort()

        avg_response_time = mean(response_times)
        median_response_time = median(response_times)
        p95_response_time = response_times[int(len(response_times) * 0.95)]
        p99_response_time = response_times[int(len(response_times) * 0.99)]

        # Calculate throughput
        total_duration = self.end_time - self.start_time
        requests_per_second = (
            total_requests / total_duration if total_duration > 0 else 0
        )

        # Calculate error rate
        error_rate = failed_requests / total_requests if total_requests > 0 else 0

        # Count errors
        errors = {}
        for result in self.results:
            if not result.success and result.error:
                errors[result.error] = errors.get(result.error, 0) + 1

        return LoadTestReport(
            config=config,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_duration=total_duration,
            avg_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            errors=errors,
        )


class BenchmarkSuite:
    """Benchmark suite for UATP system."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.runner = LoadTestRunner()

        logger.info("🏃 Benchmark Suite initialized")

    async def run_quick_benchmark(self) -> Dict[str, LoadTestReport]:
        """Run quick benchmark tests."""

        logger.info("⚡ Running quick benchmark suite...")

        tests = [
            LoadTestConfig(
                name="quick_read_test",
                target_url=self.base_url,
                concurrent_users=5,
                duration_seconds=30,
                ramp_up_seconds=5,
                operations=["read"],
            ),
            LoadTestConfig(
                name="quick_write_test",
                target_url=self.base_url,
                concurrent_users=3,
                duration_seconds=30,
                ramp_up_seconds=5,
                operations=["write"],
            ),
            LoadTestConfig(
                name="quick_mixed_test",
                target_url=self.base_url,
                concurrent_users=5,
                duration_seconds=30,
                ramp_up_seconds=5,
                operations=["read", "write", "search"],
            ),
        ]

        results = {}
        for test_config in tests:
            report = await self.runner.run_load_test(test_config)
            results[test_config.name] = report

        return results

    async def run_stress_test(self) -> Dict[str, LoadTestReport]:
        """Run stress test to find breaking points."""

        logger.info("💪 Running stress test suite...")

        tests = [
            LoadTestConfig(
                name="stress_low_load",
                target_url=self.base_url,
                concurrent_users=10,
                duration_seconds=60,
                ramp_up_seconds=10,
                operations=["read", "write", "search"],
            ),
            LoadTestConfig(
                name="stress_medium_load",
                target_url=self.base_url,
                concurrent_users=25,
                duration_seconds=60,
                ramp_up_seconds=15,
                operations=["read", "write", "search"],
            ),
            LoadTestConfig(
                name="stress_high_load",
                target_url=self.base_url,
                concurrent_users=50,
                duration_seconds=60,
                ramp_up_seconds=20,
                operations=["read", "write", "search"],
            ),
        ]

        results = {}
        for test_config in tests:
            report = await self.runner.run_load_test(test_config)
            results[test_config.name] = report

            # Check if system is failing
            if report.error_rate > 0.1:  # 10% error rate
                logger.warning(f"⚠️ High error rate detected: {report.error_rate:.1%}")
                logger.warning("Stopping stress test to prevent system damage")
                break

        return results

    async def run_endurance_test(self) -> LoadTestReport:
        """Run endurance test for sustained load."""

        logger.info("🏃‍♂️ Running endurance test...")

        config = LoadTestConfig(
            name="endurance_test",
            target_url=self.base_url,
            concurrent_users=10,
            duration_seconds=300,  # 5 minutes
            ramp_up_seconds=30,
            operations=["read", "write", "search"],
        )

        return await self.runner.run_load_test(config)

    async def run_spike_test(self) -> LoadTestReport:
        """Run spike test with sudden load increases."""

        logger.info("⚡ Running spike test...")

        config = LoadTestConfig(
            name="spike_test",
            target_url=self.base_url,
            concurrent_users=50,
            duration_seconds=60,
            ramp_up_seconds=5,  # Very fast ramp up
            operations=["read", "write", "search"],
        )

        return await self.runner.run_load_test(config)

    def generate_benchmark_report(
        self, results: Dict[str, LoadTestReport]
    ) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""

        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "summary": {
                "total_tests": len(results),
                "total_requests": sum(r.total_requests for r in results.values()),
                "overall_success_rate": 0.0,
                "average_rps": 0.0,
                "average_response_time": 0.0,
            },
            "test_results": {},
        }

        if results:
            # Calculate summary metrics
            total_requests = sum(r.total_requests for r in results.values())
            successful_requests = sum(r.successful_requests for r in results.values())

            report["summary"]["overall_success_rate"] = (
                successful_requests / total_requests if total_requests > 0 else 0.0
            )

            report["summary"]["average_rps"] = mean(
                [r.requests_per_second for r in results.values()]
            )
            report["summary"]["average_response_time"] = mean(
                [r.avg_response_time for r in results.values()]
            )

            # Add individual test results
            for test_name, test_result in results.items():
                report["test_results"][test_name] = {
                    "total_requests": test_result.total_requests,
                    "success_rate": 1 - test_result.error_rate,
                    "requests_per_second": test_result.requests_per_second,
                    "avg_response_time": test_result.avg_response_time,
                    "p95_response_time": test_result.p95_response_time,
                    "p99_response_time": test_result.p99_response_time,
                    "errors": test_result.errors,
                }

        return report

    def save_report(self, report: Dict[str, Any], filename: str):
        """Save benchmark report to file."""

        os.makedirs("reports", exist_ok=True)
        filepath = os.path.join("reports", filename)

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"📊 Benchmark report saved to {filepath}")


async def main():
    """Run load testing and benchmarks."""

    print("🔥 UATP Load Testing & Benchmarks")
    print("=" * 50)

    # Check if server is running
    import aiohttp

    base_url = "http://localhost:8000"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/health", timeout=5) as response:
                if response.status != 200:
                    print("❌ Server not responding properly")
                    return
    except Exception as e:
        print(f"❌ Server not reachable at {base_url}: {e}")
        print("Please start the UATP server first:")
        print("python3 src/api/server.py")
        return

    print(f"✅ Server is running at {base_url}")

    # Initialize benchmark suite
    benchmark = BenchmarkSuite(base_url)

    # Run quick benchmark
    print("\n⚡ Running quick benchmark...")
    quick_results = await benchmark.run_quick_benchmark()

    # Run stress test
    print("\n💪 Running stress test...")
    stress_results = await benchmark.run_stress_test()

    # Combine results
    all_results = {**quick_results, **stress_results}

    # Generate comprehensive report
    print("\n📊 Generating benchmark report...")
    report = benchmark.generate_benchmark_report(all_results)

    # Display summary
    print("\n🎯 Benchmark Summary:")
    print(f"   Total tests: {report['summary']['total_tests']}")
    print(f"   Total requests: {report['summary']['total_requests']}")
    print(f"   Overall success rate: {report['summary']['overall_success_rate']:.1%}")
    print(f"   Average RPS: {report['summary']['average_rps']:.1f}")
    print(
        f"   Average response time: {report['summary']['average_response_time']:.3f}s"
    )

    # Show individual test results
    print("\n📋 Individual Test Results:")
    for test_name, test_result in report["test_results"].items():
        print(f"   {test_name}:")
        print(f"     Requests: {test_result['total_requests']}")
        print(f"     Success Rate: {test_result['success_rate']:.1%}")
        print(f"     RPS: {test_result['requests_per_second']:.1f}")
        print(f"     Avg Response: {test_result['avg_response_time']:.3f}s")
        print(f"     P95 Response: {test_result['p95_response_time']:.3f}s")

        if test_result["errors"]:
            print(f"     Errors: {test_result['errors']}")

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"benchmark_report_{timestamp}.json"
    benchmark.save_report(report, filename)

    print(f"\n✅ Load testing and benchmarking completed!")
    print(f"📄 Full report saved to reports/{filename}")


if __name__ == "__main__":
    asyncio.run(main())
