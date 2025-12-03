#!/usr/bin/env python3
"""
Monitoring API for UATP Capsule Engine
======================================

This module provides REST API endpoints for monitoring, health checks,
and metrics collection for the UATP system.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from quart import request, jsonify, g
from werkzeug.exceptions import BadRequest, NotFound
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from .custom_quart import CustomQuart
from monitoring.health_checks import get_health_manager, HealthStatus
from monitoring.metrics import get_metrics_collector, get_performance_monitor

logger = logging.getLogger(__name__)

# Initialize Quart app
app = CustomQuart(__name__)

# Configure app
app.config.update(
    {"SECRET_KEY": os.getenv("SECRET_KEY", "dev-secret-key"), "TESTING": False}
)


@app.route("/health", methods=["GET"])
async def health_check():
    """Basic health check endpoint."""
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "uatp-monitoring",
            }
        ),
        200,
    )


@app.route("/health/detailed", methods=["GET"])
async def detailed_health_check():
    """Detailed health check with all services."""

    try:
        health_manager = get_health_manager()
        system_health = await health_manager.get_system_health()

        return jsonify(system_health), 200

    except Exception as e:
        logger.error(f"❌ Detailed health check failed: {e}")
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            500,
        )


@app.route("/health/<service>", methods=["GET"])
async def service_health_check(service: str):
    """Health check for a specific service."""

    try:
        health_manager = get_health_manager()
        result = await health_manager.run_check(service)

        if result.status == HealthStatus.UNKNOWN:
            return (
                jsonify(
                    {
                        "error": f"Service {service} not found",
                        "available_services": list(health_manager.checks.keys()),
                    }
                ),
                404,
            )

        return jsonify(result.to_dict()), 200

    except Exception as e:
        logger.error(f"❌ Service health check failed for {service}: {e}")
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            500,
        )


@app.route("/health/history", methods=["GET"])
async def health_history():
    """Get health check history."""

    try:
        health_manager = get_health_manager()

        # Get query parameters
        service = request.args.get("service")
        hours = int(request.args.get("hours", 24))

        history = health_manager.get_check_history(service, hours)

        return (
            jsonify(
                {
                    "history": history,
                    "service": service,
                    "hours": hours,
                    "total_checks": len(history),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"❌ Health history request failed: {e}")
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500


@app.route("/health/uptime", methods=["GET"])
async def uptime_stats():
    """Get uptime statistics."""

    try:
        health_manager = get_health_manager()

        service = request.args.get("service")
        uptime = health_manager.get_uptime_stats(service)

        return (
            jsonify(
                {
                    "uptime": uptime,
                    "service": service,
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"❌ Uptime stats request failed: {e}")
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500


@app.route("/metrics", methods=["GET"])
async def get_metrics():
    """Get all metrics."""

    try:
        metrics_collector = get_metrics_collector()

        # Get query parameters
        format_type = request.args.get("format", "json")

        if format_type == "prometheus":
            return await _get_prometheus_metrics()
        else:
            metrics = metrics_collector.get_all_metrics()

            return (
                jsonify(
                    {
                        "metrics": metrics,
                        "timestamp": datetime.now().isoformat(),
                        "format": format_type,
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(f"❌ Metrics request failed: {e}")
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500


@app.route("/metrics/summary", methods=["GET"])
async def metrics_summary():
    """Get metrics summary."""

    try:
        metrics_collector = get_metrics_collector()
        summary = metrics_collector.get_summary()

        return (
            jsonify({"summary": summary, "timestamp": datetime.now().isoformat()}),
            200,
        )

    except Exception as e:
        logger.error(f"❌ Metrics summary request failed: {e}")
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500


@app.route("/metrics/<metric_name>", methods=["GET"])
async def get_metric(metric_name: str):
    """Get a specific metric."""

    try:
        metrics_collector = get_metrics_collector()

        # Parse labels from query parameters
        labels = {}
        for key, value in request.args.items():
            if key.startswith("label_"):
                label_name = key[6:]  # Remove 'label_' prefix
                labels[label_name] = value

        metric_points = metrics_collector.get_metric(metric_name, labels)

        if not metric_points:
            return (
                jsonify({"error": f"Metric {metric_name} not found", "labels": labels}),
                404,
            )

        return (
            jsonify(
                {
                    "metric": metric_name,
                    "labels": labels,
                    "points": [point.to_dict() for point in metric_points],
                    "count": len(metric_points),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"❌ Metric request failed for {metric_name}: {e}")
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500


@app.route("/metrics/<metric_name>/histogram", methods=["GET"])
async def get_histogram_summary(metric_name: str):
    """Get histogram summary for a metric."""

    try:
        metrics_collector = get_metrics_collector()

        # Parse labels from query parameters
        labels = {}
        for key, value in request.args.items():
            if key.startswith("label_"):
                label_name = key[6:]  # Remove 'label_' prefix
                labels[label_name] = value

        summary = metrics_collector.get_histogram_summary(metric_name, labels)

        if not summary:
            return (
                jsonify(
                    {
                        "error": f"Histogram {metric_name} not found or empty",
                        "labels": labels,
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "metric": metric_name,
                    "labels": labels,
                    "histogram_summary": summary,
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"❌ Histogram request failed for {metric_name}: {e}")
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500


@app.route("/metrics/record", methods=["POST"])
async def record_metric():
    """Record a custom metric."""

    try:
        data = await request.get_json()
        if not data:
            raise BadRequest("Request body required")

        metrics_collector = get_metrics_collector()

        metric_name = data.get("name")
        metric_type = data.get("type", "gauge")
        metric_value = data.get("value")
        labels = data.get("labels", {})

        if not metric_name or metric_value is None:
            raise BadRequest("Metric name and value are required")

        # Record based on type
        if metric_type == "counter":
            metrics_collector.record_counter(metric_name, metric_value, labels)
        elif metric_type == "gauge":
            metrics_collector.record_gauge(metric_name, metric_value, labels)
        elif metric_type == "histogram":
            metrics_collector.record_histogram(metric_name, metric_value, labels)
        else:
            raise BadRequest(f"Unsupported metric type: {metric_type}")

        return (
            jsonify(
                {
                    "message": "Metric recorded successfully",
                    "metric": {
                        "name": metric_name,
                        "type": metric_type,
                        "value": metric_value,
                        "labels": labels,
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            201,
        )

    except BadRequest:
        raise
    except Exception as e:
        logger.error(f"❌ Record metric failed: {e}")
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500


@app.route("/monitoring/dashboard", methods=["GET"])
async def monitoring_dashboard():
    """Get monitoring dashboard data."""

    try:
        health_manager = get_health_manager()
        metrics_collector = get_metrics_collector()

        # Get system health
        system_health = await health_manager.get_system_health()

        # Get metrics summary
        metrics_summary = metrics_collector.get_summary()

        # Get uptime stats
        uptime_stats = health_manager.get_uptime_stats()

        # Get recent metrics
        recent_metrics = {}
        for metric_name in [
            "uatp_capsules_total",
            "uatp_active_sessions",
            "system_cpu_percent",
            "system_memory_percent",
        ]:
            points = metrics_collector.get_metric(metric_name)
            if points:
                recent_metrics[metric_name] = points[-1].to_dict()

        return (
            jsonify(
                {
                    "dashboard": {
                        "system_health": system_health,
                        "metrics_summary": metrics_summary,
                        "uptime_stats": uptime_stats,
                        "recent_metrics": recent_metrics,
                        "timestamp": datetime.now().isoformat(),
                    }
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"❌ Dashboard request failed: {e}")
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500


async def _get_prometheus_metrics():
    """Get metrics in Prometheus format."""

    try:
        metrics_collector = get_metrics_collector()
        summary = metrics_collector.get_summary()

        prometheus_output = []

        # Add counters
        for metric_key, value in summary["counters"].items():
            prometheus_output.append(f"# TYPE {metric_key} counter")
            prometheus_output.append(f"{metric_key} {value}")

        # Add gauges
        for metric_key, value in summary["gauges"].items():
            prometheus_output.append(f"# TYPE {metric_key} gauge")
            prometheus_output.append(f"{metric_key} {value}")

        # Add histogram summaries
        for metric_key, stats in summary["histogram_summaries"].items():
            prometheus_output.append(f"# TYPE {metric_key} histogram")
            prometheus_output.append(f"{metric_key}_count {stats['count']}")
            prometheus_output.append(f"{metric_key}_sum {stats['sum']}")
            prometheus_output.append(
                f"{metric_key}_bucket{{le=\"+Inf\"}} {stats['count']}"
            )

        return (
            "\n".join(prometheus_output) + "\n",
            200,
            {"Content-Type": "text/plain; version=0.0.4"},
        )

    except Exception as e:
        logger.error(f"❌ Prometheus metrics failed: {e}")
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500


# Error handlers
@app.errorhandler(BadRequest)
async def handle_bad_request(e):
    return jsonify({"error": str(e.description)}), 400


@app.errorhandler(NotFound)
async def handle_not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
async def handle_internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


async def main():
    """Run the monitoring API server."""

    print("🏥 Starting Monitoring API Server")
    print("=" * 40)

    # Start metrics collectors
    from monitoring.metrics import get_system_collector, get_app_collector

    system_collector = get_system_collector()
    app_collector = get_app_collector()

    try:
        # Start collectors
        await system_collector.start()
        await app_collector.start()

        logger.info("📊 Metrics collectors started")

        # Run the server
        await app.run_task(host="0.0.0.0", port=5003, debug=True)

    finally:
        # Stop collectors
        await system_collector.stop()
        await app_collector.stop()
        logger.info("📊 Metrics collectors stopped")


if __name__ == "__main__":
    asyncio.run(main())
