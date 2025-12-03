#!/usr/bin/env python3
"""
Performance Regression Check for UATP Capsule Engine
===================================================

This script checks for performance regressions by comparing current
performance metrics with historical baselines.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "avg_response_time": 0.5,  # seconds
    "p95_response_time": 1.0,  # seconds
    "requests_per_second": 50,  # minimum RPS
    "error_rate": 0.05,  # maximum 5% error rate
    "memory_usage": 512,  # MB
    "cpu_usage": 70,  # percentage
}

# Regression tolerance (percentage increase allowed)
REGRESSION_TOLERANCE = {
    "avg_response_time": 20,  # 20% increase allowed
    "p95_response_time": 25,  # 25% increase allowed
    "requests_per_second": -10,  # 10% decrease allowed
    "error_rate": 100,  # 100% increase (double) allowed
    "memory_usage": 15,  # 15% increase allowed
    "cpu_usage": 10,  # 10% increase allowed
}


def load_performance_data(reports_dir: str = "reports") -> List[Dict[str, Any]]:
    """Load performance data from reports directory."""

    performance_data = []

    if not os.path.exists(reports_dir):
        print(f"⚠️ Reports directory not found: {reports_dir}")
        return performance_data

    # Find all performance report files
    for filename in os.listdir(reports_dir):
        if filename.startswith("performance_benchmark_") and filename.endswith(".json"):
            filepath = os.path.join(reports_dir, filename)

            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    data["filename"] = filename
                    performance_data.append(data)
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}")

    # Sort by timestamp
    performance_data.sort(key=lambda x: x.get("timestamp", ""))

    return performance_data


def extract_key_metrics(report: Dict[str, Any]) -> Dict[str, float]:
    """Extract key performance metrics from a report."""

    metrics = {}

    # Extract from benchmark results
    benchmark_results = report.get("benchmark_results", {})

    if benchmark_results:
        # Average response times
        response_times = []
        rps_values = []

        for operation, result in benchmark_results.items():
            if "avg_duration" in result:
                response_times.append(result["avg_duration"])

            # Extract throughput metrics
            for key in [
                "capsules_per_second",
                "retrievals_per_second",
                "searches_per_second",
                "operations_per_second",
            ]:
                if key in result:
                    rps_values.append(result[key])

        if response_times:
            metrics["avg_response_time"] = sum(response_times) / len(response_times)

        if rps_values:
            metrics["requests_per_second"] = sum(rps_values) / len(rps_values)

    # Extract system metrics
    system_info = report.get("system_info", {})
    if system_info:
        metrics["memory_total"] = system_info.get("memory_total", 0) / (
            1024 * 1024 * 1024
        )  # GB

    return metrics


def check_thresholds(metrics: Dict[str, float]) -> List[str]:
    """Check if metrics meet performance thresholds."""

    violations = []

    for metric, threshold in PERFORMANCE_THRESHOLDS.items():
        if metric in metrics:
            value = metrics[metric]

            if metric in [
                "avg_response_time",
                "p95_response_time",
                "error_rate",
                "memory_usage",
                "cpu_usage",
            ]:
                # Lower is better
                if value > threshold:
                    violations.append(
                        f"{metric}: {value:.3f} > {threshold} (threshold)"
                    )
            else:
                # Higher is better
                if value < threshold:
                    violations.append(
                        f"{metric}: {value:.3f} < {threshold} (threshold)"
                    )

    return violations


def check_regression(
    current_metrics: Dict[str, float], historical_metrics: List[Dict[str, float]]
) -> List[str]:
    """Check for performance regression."""

    if not historical_metrics:
        return []

    # Calculate baseline from last 5 reports
    baseline_metrics = {}
    recent_reports = historical_metrics[-5:]

    for metric in current_metrics:
        values = [report.get(metric) for report in recent_reports if metric in report]
        if values:
            baseline_metrics[metric] = sum(values) / len(values)

    regressions = []

    for metric, current_value in current_metrics.items():
        if metric in baseline_metrics:
            baseline_value = baseline_metrics[metric]
            tolerance = REGRESSION_TOLERANCE.get(metric, 10)

            if metric in [
                "avg_response_time",
                "p95_response_time",
                "error_rate",
                "memory_usage",
                "cpu_usage",
            ]:
                # Lower is better - check for increase
                percentage_change = (
                    (current_value - baseline_value) / baseline_value
                ) * 100
                if percentage_change > tolerance:
                    regressions.append(
                        f"{metric}: {current_value:.3f} vs {baseline_value:.3f} baseline "
                        f"(+{percentage_change:.1f}% > {tolerance}% tolerance)"
                    )
            else:
                # Higher is better - check for decrease
                percentage_change = (
                    (baseline_value - current_value) / baseline_value
                ) * 100
                if percentage_change > abs(tolerance):
                    regressions.append(
                        f"{metric}: {current_value:.3f} vs {baseline_value:.3f} baseline "
                        f"(-{percentage_change:.1f}% > {abs(tolerance)}% tolerance)"
                    )

    return regressions


def main():
    """Main performance regression check."""

    print("📊 UATP Performance Regression Check")
    print("=" * 50)

    # Load performance data
    performance_data = load_performance_data()

    if not performance_data:
        print("❌ No performance data found")
        sys.exit(1)

    print(f"📈 Found {len(performance_data)} performance reports")

    # Get current (latest) metrics
    current_report = performance_data[-1]
    current_metrics = extract_key_metrics(current_report)

    print(f"\\n🔍 Current Performance Metrics:")
    for metric, value in current_metrics.items():
        print(f"   {metric}: {value:.3f}")

    # Check thresholds
    threshold_violations = check_thresholds(current_metrics)

    if threshold_violations:
        print(f"\\n⚠️ Threshold Violations:")
        for violation in threshold_violations:
            print(f"   - {violation}")
    else:
        print(f"\\n✅ All performance thresholds met")

    # Check for regressions
    if len(performance_data) > 1:
        historical_data = [
            extract_key_metrics(report) for report in performance_data[:-1]
        ]
        regressions = check_regression(current_metrics, historical_data)

        if regressions:
            print(f"\\n🔴 Performance Regressions Detected:")
            for regression in regressions:
                print(f"   - {regression}")
        else:
            print(f"\\n✅ No performance regressions detected")
    else:
        print(f"\\n🔄 Not enough historical data for regression analysis")

    # Generate summary
    total_issues = (
        len(threshold_violations) + len(regressions)
        if len(performance_data) > 1
        else len(threshold_violations)
    )

    if total_issues == 0:
        print(f"\\n🎉 Performance check passed!")
        sys.exit(0)
    else:
        print(f"\\n❌ Performance check failed with {total_issues} issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
