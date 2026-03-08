#!/usr/bin/env python3
"""
Performance Benchmarks for UATP Capsule Engine
==============================================

This module provides detailed performance benchmarks for core UATP operations
including capsule creation, filtering, storage, and retrieval.
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime
from statistics import mean, median, stdev
from typing import Any, Dict, List

import psutil

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Performance benchmark runner for UATP core operations."""

    def __init__(self):
        self.results = {}
        self.system_stats = []
        self.monitoring = False

        logger.info(" Performance Benchmark initialized")

    def monitor_system(self):
        """Monitor system resources during benchmarks."""

        while self.monitoring:
            try:
                stats = {
                    "timestamp": time.time(),
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_io": psutil.disk_io_counters()._asdict()
                    if psutil.disk_io_counters()
                    else {},
                    "network_io": psutil.net_io_counters()._asdict()
                    if psutil.net_io_counters()
                    else {},
                }
                self.system_stats.append(stats)
                time.sleep(1)
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                break

    def start_monitoring(self):
        """Start system monitoring."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_system)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop system monitoring."""
        self.monitoring = False
        if hasattr(self, "monitor_thread"):
            self.monitor_thread.join(timeout=1)

    async def benchmark_capsule_creation(self, count: int = 1000) -> Dict[str, Any]:
        """Benchmark capsule creation performance."""

        logger.info(f" Benchmarking capsule creation ({count} capsules)...")

        try:
            from live_capture.real_time_capsule_generator import (
                capture_live_interaction,
            )

            durations = []
            success_count = 0

            self.start_monitoring()
            start_time = time.time()

            for i in range(count):
                capsule_start = time.time()

                try:
                    capsule_id = await capture_live_interaction(
                        session_id=f"bench_session_{i}",
                        user_message=f"Benchmark test message {i}",
                        ai_response=f"This is benchmark response {i} for performance testing",
                        user_id="benchmark_user",
                        platform="benchmark",
                        model="benchmark-model",
                        metadata={"test": True, "iteration": i},
                    )

                    duration = time.time() - capsule_start
                    durations.append(duration)

                    if capsule_id:
                        success_count += 1

                except Exception as e:
                    logger.error(f"Capsule creation failed at iteration {i}: {e}")
                    durations.append(time.time() - capsule_start)

            total_time = time.time() - start_time
            self.stop_monitoring()

            # Calculate statistics
            avg_duration = mean(durations)
            median_duration = median(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            std_duration = stdev(durations) if len(durations) > 1 else 0

            capsules_per_second = count / total_time
            success_rate = success_count / count

            result = {
                "operation": "capsule_creation",
                "count": count,
                "total_time": total_time,
                "success_count": success_count,
                "success_rate": success_rate,
                "capsules_per_second": capsules_per_second,
                "avg_duration": avg_duration,
                "median_duration": median_duration,
                "min_duration": min_duration,
                "max_duration": max_duration,
                "std_duration": std_duration,
                "system_stats": self._analyze_system_stats(),
            }

            logger.info("[OK] Capsule creation benchmark completed")
            logger.info(f"   Success rate: {success_rate:.1%}")
            logger.info(f"   Capsules/sec: {capsules_per_second:.1f}")
            logger.info(f"   Avg duration: {avg_duration:.3f}s")

            return result

        except Exception as e:
            logger.error(f"[ERROR] Capsule creation benchmark failed: {e}")
            self.stop_monitoring()
            raise

    async def benchmark_capsule_retrieval(self, count: int = 1000) -> Dict[str, Any]:
        """Benchmark capsule retrieval performance."""

        logger.info(f" Benchmarking capsule retrieval ({count} operations)...")

        try:
            from config.database_config import get_database_adapter

            adapter = get_database_adapter()
            if not adapter:
                raise RuntimeError("Database adapter not available")

            # First, create some test capsules
            await self._create_test_capsules(adapter, min(count, 100))

            # Get recent capsules for testing
            recent_capsules = await adapter.get_recent_capsules(100)
            if not recent_capsules:
                raise RuntimeError("No capsules available for retrieval testing")

            durations = []
            success_count = 0

            self.start_monitoring()
            start_time = time.time()

            for i in range(count):
                retrieval_start = time.time()

                try:
                    # Pick a random capsule to retrieve
                    import random

                    capsule_id = random.choice(recent_capsules)["capsule_id"]

                    result = await adapter.get_capsule(capsule_id)

                    duration = time.time() - retrieval_start
                    durations.append(duration)

                    if result:
                        success_count += 1

                except Exception as e:
                    logger.error(f"Capsule retrieval failed at iteration {i}: {e}")
                    durations.append(time.time() - retrieval_start)

            total_time = time.time() - start_time
            self.stop_monitoring()

            # Calculate statistics
            avg_duration = mean(durations)
            median_duration = median(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            std_duration = stdev(durations) if len(durations) > 1 else 0

            retrievals_per_second = count / total_time
            success_rate = success_count / count

            result = {
                "operation": "capsule_retrieval",
                "count": count,
                "total_time": total_time,
                "success_count": success_count,
                "success_rate": success_rate,
                "retrievals_per_second": retrievals_per_second,
                "avg_duration": avg_duration,
                "median_duration": median_duration,
                "min_duration": min_duration,
                "max_duration": max_duration,
                "std_duration": std_duration,
                "system_stats": self._analyze_system_stats(),
            }

            logger.info("[OK] Capsule retrieval benchmark completed")
            logger.info(f"   Success rate: {success_rate:.1%}")
            logger.info(f"   Retrievals/sec: {retrievals_per_second:.1f}")
            logger.info(f"   Avg duration: {avg_duration:.3f}s")

            return result

        except Exception as e:
            logger.error(f"[ERROR] Capsule retrieval benchmark failed: {e}")
            self.stop_monitoring()
            raise

    async def benchmark_capsule_search(self, count: int = 500) -> Dict[str, Any]:
        """Benchmark capsule search performance."""

        logger.info(f" Benchmarking capsule search ({count} operations)...")

        try:
            from config.database_config import get_database_adapter

            adapter = get_database_adapter()
            if not adapter:
                raise RuntimeError("Database adapter not available")

            # Create test capsules with searchable content
            await self._create_searchable_test_capsules(adapter, 200)

            search_terms = [
                "test",
                "benchmark",
                "performance",
                "capsule",
                "message",
                "response",
            ]
            durations = []
            success_count = 0

            self.start_monitoring()
            start_time = time.time()

            for i in range(count):
                search_start = time.time()

                try:
                    # Pick a random search term
                    import random

                    query = random.choice(search_terms)

                    results = await adapter.search_capsules(query, limit=20)

                    duration = time.time() - search_start
                    durations.append(duration)

                    if results is not None:
                        success_count += 1

                except Exception as e:
                    logger.error(f"Capsule search failed at iteration {i}: {e}")
                    durations.append(time.time() - search_start)

            total_time = time.time() - start_time
            self.stop_monitoring()

            # Calculate statistics
            avg_duration = mean(durations)
            median_duration = median(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            std_duration = stdev(durations) if len(durations) > 1 else 0

            searches_per_second = count / total_time
            success_rate = success_count / count

            result = {
                "operation": "capsule_search",
                "count": count,
                "total_time": total_time,
                "success_count": success_count,
                "success_rate": success_rate,
                "searches_per_second": searches_per_second,
                "avg_duration": avg_duration,
                "median_duration": median_duration,
                "min_duration": min_duration,
                "max_duration": max_duration,
                "std_duration": std_duration,
                "system_stats": self._analyze_system_stats(),
            }

            logger.info("[OK] Capsule search benchmark completed")
            logger.info(f"   Success rate: {success_rate:.1%}")
            logger.info(f"   Searches/sec: {searches_per_second:.1f}")
            logger.info(f"   Avg duration: {avg_duration:.3f}s")

            return result

        except Exception as e:
            logger.error(f"[ERROR] Capsule search benchmark failed: {e}")
            self.stop_monitoring()
            raise

    async def benchmark_concurrent_operations(
        self, concurrent_users: int = 10, operations_per_user: int = 100
    ) -> Dict[str, Any]:
        """Benchmark concurrent operations."""

        logger.info(
            f" Benchmarking concurrent operations ({concurrent_users} users, {operations_per_user} ops each)..."
        )

        try:
            from config.database_config import get_database_adapter

            adapter = get_database_adapter()
            if not adapter:
                raise RuntimeError("Database adapter not available")

            # Create test data
            await self._create_test_capsules(adapter, 100)

            user_results = []

            self.start_monitoring()
            start_time = time.time()

            # Create concurrent user tasks
            tasks = []
            for user_id in range(concurrent_users):
                task = asyncio.create_task(
                    self._user_concurrent_operations(
                        adapter, user_id, operations_per_user
                    )
                )
                tasks.append(task)

            # Wait for all tasks to complete
            user_results = await asyncio.gather(*tasks)

            total_time = time.time() - start_time
            self.stop_monitoring()

            # Aggregate results
            total_operations = sum(len(results) for results in user_results)
            all_durations = []
            total_success = 0

            for user_result in user_results:
                for operation_result in user_result:
                    all_durations.append(operation_result["duration"])
                    if operation_result["success"]:
                        total_success += 1

            # Calculate statistics
            avg_duration = mean(all_durations) if all_durations else 0
            median_duration = median(all_durations) if all_durations else 0
            min_duration = min(all_durations) if all_durations else 0
            max_duration = max(all_durations) if all_durations else 0
            std_duration = stdev(all_durations) if len(all_durations) > 1 else 0

            operations_per_second = total_operations / total_time
            success_rate = (
                total_success / total_operations if total_operations > 0 else 0
            )

            result = {
                "operation": "concurrent_operations",
                "concurrent_users": concurrent_users,
                "operations_per_user": operations_per_user,
                "total_operations": total_operations,
                "total_time": total_time,
                "success_count": total_success,
                "success_rate": success_rate,
                "operations_per_second": operations_per_second,
                "avg_duration": avg_duration,
                "median_duration": median_duration,
                "min_duration": min_duration,
                "max_duration": max_duration,
                "std_duration": std_duration,
                "system_stats": self._analyze_system_stats(),
            }

            logger.info("[OK] Concurrent operations benchmark completed")
            logger.info(f"   Success rate: {success_rate:.1%}")
            logger.info(f"   Operations/sec: {operations_per_second:.1f}")
            logger.info(f"   Avg duration: {avg_duration:.3f}s")

            return result

        except Exception as e:
            logger.error(f"[ERROR] Concurrent operations benchmark failed: {e}")
            self.stop_monitoring()
            raise

    async def _user_concurrent_operations(
        self, adapter, user_id: int, operations_count: int
    ) -> List[Dict[str, Any]]:
        """Simulate concurrent user operations."""

        results = []

        for i in range(operations_count):
            start_time = time.time()
            success = False

            try:
                # Mix of operations
                import random

                operation_type = random.choice(["create", "read", "search"])

                if operation_type == "create":
                    capsule_data = {
                        "capsule_id": f"concurrent_test_{user_id}_{i}_{int(time.time() * 1000)}",
                        "type": "interaction_capsule",
                        "platform": "benchmark",
                        "user_id": f"user_{user_id}",
                        "user_message": f"Concurrent test message {i} from user {user_id}",
                        "ai_response": f"Response {i} from user {user_id}",
                        "significance_score": random.uniform(0.5, 3.0),
                        "timestamp": datetime.now().isoformat(),
                    }

                    result = await adapter.create_capsule(capsule_data)
                    success = result is not None

                elif operation_type == "read":
                    recent_capsules = await adapter.get_recent_capsules(10)
                    if recent_capsules:
                        capsule_id = random.choice(recent_capsules)["capsule_id"]
                        result = await adapter.get_capsule(capsule_id)
                        success = result is not None

                elif operation_type == "search":
                    search_terms = ["test", "concurrent", "user", "message"]
                    query = random.choice(search_terms)
                    results_list = await adapter.search_capsules(query, limit=10)
                    success = results_list is not None

            except Exception as e:
                logger.error(f"Concurrent operation failed for user {user_id}: {e}")

            duration = time.time() - start_time
            results.append(
                {
                    "user_id": user_id,
                    "operation": operation_type,
                    "duration": duration,
                    "success": success,
                }
            )

        return results

    async def _create_test_capsules(self, adapter, count: int):
        """Create test capsules for benchmarking."""

        logger.info(f" Creating {count} test capsules...")

        for i in range(count):
            capsule_data = {
                "capsule_id": f"test_capsule_{i}_{int(time.time() * 1000)}",
                "type": "interaction_capsule",
                "platform": "test",
                "user_id": "benchmark_user",
                "user_message": f"Test message {i} for benchmarking",
                "ai_response": f"Test response {i} for benchmarking purposes",
                "significance_score": 1.0 + (i % 5),
                "timestamp": datetime.now().isoformat(),
            }

            await adapter.create_capsule(capsule_data)

    async def _create_searchable_test_capsules(self, adapter, count: int):
        """Create searchable test capsules for search benchmarking."""

        logger.info(f" Creating {count} searchable test capsules...")

        content_templates = [
            "This is a test message about performance benchmarking",
            "Capsule search functionality testing with various keywords",
            "Benchmark performance analysis for search operations",
            "Test data for capsule retrieval and search capabilities",
            "Performance measurement message for system evaluation",
        ]

        for i in range(count):
            import random

            content = random.choice(content_templates)

            capsule_data = {
                "capsule_id": f"searchable_capsule_{i}_{int(time.time() * 1000)}",
                "type": "interaction_capsule",
                "platform": "test",
                "user_id": "benchmark_user",
                "user_message": f"{content} - iteration {i}",
                "ai_response": f"Response to {content} - iteration {i}",
                "significance_score": 1.0 + (i % 5),
                "timestamp": datetime.now().isoformat(),
            }

            await adapter.create_capsule(capsule_data)

    def _analyze_system_stats(self) -> Dict[str, Any]:
        """Analyze system statistics collected during benchmark."""

        if not self.system_stats:
            return {}

        cpu_values = [s["cpu_percent"] for s in self.system_stats]
        memory_values = [s["memory_percent"] for s in self.system_stats]

        return {
            "cpu_avg": mean(cpu_values),
            "cpu_max": max(cpu_values),
            "cpu_min": min(cpu_values),
            "memory_avg": mean(memory_values),
            "memory_max": max(memory_values),
            "memory_min": min(memory_values),
            "samples": len(self.system_stats),
        }

    def generate_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive performance report."""

        report = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "python_version": sys.version,
            },
            "benchmark_results": results,
            "summary": {
                "total_benchmarks": len(results),
                "overall_performance": "good",  # Will be calculated based on results
            },
        }

        return report

    def save_report(self, report: Dict[str, Any], filename: str):
        """Save performance report to file."""

        os.makedirs("reports", exist_ok=True)
        filepath = os.path.join("reports", filename)

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f" Performance report saved to {filepath}")


async def main():
    """Run performance benchmarks."""

    print(" UATP Performance Benchmarks")
    print("=" * 50)

    benchmark = PerformanceBenchmark()
    results = {}

    try:
        # Run capsule creation benchmark
        print("\n Running capsule creation benchmark...")
        results["capsule_creation"] = await benchmark.benchmark_capsule_creation(100)

        # Run capsule retrieval benchmark
        print("\n Running capsule retrieval benchmark...")
        results["capsule_retrieval"] = await benchmark.benchmark_capsule_retrieval(200)

        # Run capsule search benchmark
        print("\n Running capsule search benchmark...")
        results["capsule_search"] = await benchmark.benchmark_capsule_search(100)

        # Run concurrent operations benchmark
        print("\n Running concurrent operations benchmark...")
        results[
            "concurrent_operations"
        ] = await benchmark.benchmark_concurrent_operations(5, 50)

        # Generate and save report
        print("\n Generating performance report...")
        report = benchmark.generate_report(results)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_benchmark_{timestamp}.json"
        benchmark.save_report(report, filename)

        # Display summary
        print("\n Performance Summary:")
        for name, result in results.items():
            print(f"   {name}:")
            print(f"     Success rate: {result['success_rate']:.1%}")
            if "capsules_per_second" in result:
                print(f"     Throughput: {result['capsules_per_second']:.1f} ops/sec")
            elif "retrievals_per_second" in result:
                print(f"     Throughput: {result['retrievals_per_second']:.1f} ops/sec")
            elif "searches_per_second" in result:
                print(f"     Throughput: {result['searches_per_second']:.1f} ops/sec")
            elif "operations_per_second" in result:
                print(f"     Throughput: {result['operations_per_second']:.1f} ops/sec")
            print(f"     Avg duration: {result['avg_duration']:.3f}s")
            print(f"     P95 duration: {result.get('p95_duration', 0):.3f}s")

        print("\n[OK] Performance benchmarks completed!")
        print(f" Full report saved to reports/{filename}")

    except Exception as e:
        print(f"[ERROR] Benchmark failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
