"""
Monitoring API endpoints for performance and security metrics.
Provides real-time visibility into system health, query performance, and security events.
"""

from quart import Blueprint, jsonify, request
from typing import Dict, Any

from src.observability.performance_monitor import get_monitor
from src.observability.security_monitor import get_security_monitor
from src.database.connection import get_database_manager

monitoring_bp = Blueprint("monitoring", __name__, url_prefix="/api/v1/monitoring")


@monitoring_bp.route("/health", methods=["GET"])
async def health_check():
    """
    Comprehensive system health check.

    Returns:
        - Database connectivity
        - Performance metrics
        - Security alerts
        - System status
    """
    try:
        # Database health
        db_manager = get_database_manager()
        db_health = await db_manager.health_check()

        # Performance metrics
        perf_monitor = get_monitor()
        perf_stats = perf_monitor.get_stats()
        perf_alerts = perf_monitor.check_alerts()

        # Security metrics
        sec_monitor = get_security_monitor()
        sec_stats = sec_monitor.get_stats()
        sec_alerts = sec_monitor.check_alerts()

        # Overall status
        status = "healthy"
        if db_health["status"] != "healthy" or perf_alerts or sec_alerts:
            status = "degraded"
        if db_health["status"] == "unhealthy" or any(
            "CRITICAL" in alert for alert in perf_alerts + sec_alerts
        ):
            status = "unhealthy"

        return (
            jsonify(
                {
                    "status": status,
                    "timestamp": db_health.get("last_check"),
                    "database": db_health,
                    "performance": {**perf_stats, "alerts": perf_alerts},
                    "security": {
                        "total_events": sec_stats["total_events"],
                        "events_last_hour": sec_stats["events_last_hour"],
                        "by_severity": sec_stats["by_severity"],
                        "alerts": sec_alerts,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@monitoring_bp.route("/performance", methods=["GET"])
async def performance_metrics():
    """
    Detailed performance metrics.

    Query params:
        - detailed: Include query breakdown (default: false)
    """
    perf_monitor = get_monitor()

    response = {
        "stats": perf_monitor.get_stats(),
        "alerts": perf_monitor.check_alerts(),
    }

    # Include detailed breakdown if requested
    if request.args.get("detailed", "").lower() == "true":
        response["query_breakdown"] = perf_monitor.get_query_breakdown()

    return jsonify(response), 200


@monitoring_bp.route("/security", methods=["GET"])
async def security_metrics():
    """
    Detailed security metrics.

    Query params:
        - recent_limit: Number of recent events to return (default: 50, max: 200)
    """
    sec_monitor = get_security_monitor()

    limit = min(int(request.args.get("recent_limit", 50)), 200)

    response = {
        "stats": sec_monitor.get_stats(),
        "alerts": sec_monitor.check_alerts(),
        "recent_events": sec_monitor.get_recent_events(limit=limit),
    }

    return jsonify(response), 200


@monitoring_bp.route("/database", methods=["GET"])
async def database_metrics():
    """
    Detailed database metrics.

    Returns:
        - Connection pool status
        - Query statistics
        - Health information
    """
    db_manager = get_database_manager()

    metrics = db_manager.get_metrics()
    health = await db_manager.health_check()

    return jsonify({"metrics": metrics, "health": health}), 200


@monitoring_bp.route("/alerts", methods=["GET"])
async def all_alerts():
    """
    Get all current system alerts.

    Returns alerts from:
        - Performance monitoring (query latency, pool utilization)
        - Security monitoring (attacks, validation failures)
        - Database health
    """
    perf_monitor = get_monitor()
    sec_monitor = get_security_monitor()
    db_manager = get_database_manager()

    perf_alerts = perf_monitor.check_alerts()
    sec_alerts = sec_monitor.check_alerts()

    db_health = await db_manager.health_check()
    db_alerts = []
    if db_health["status"] != "healthy":
        db_alerts.append(
            f"Database unhealthy: {db_health.get('error', 'Unknown error')}"
        )

    all_alerts = {
        "performance": perf_alerts,
        "security": sec_alerts,
        "database": db_alerts,
        "total_count": len(perf_alerts) + len(sec_alerts) + len(db_alerts),
        "has_critical": any(
            "CRITICAL" in alert for alert in perf_alerts + sec_alerts + db_alerts
        ),
    }

    return jsonify(all_alerts), 200


@monitoring_bp.route("/summary", methods=["GET"])
async def monitoring_summary():
    """
    Quick monitoring summary for dashboards.

    Returns:
        - Overall system status
        - Key metrics at a glance
        - Alert counts
    """
    try:
        perf_monitor = get_monitor()
        sec_monitor = get_security_monitor()
        db_manager = get_database_manager()

        perf_stats = perf_monitor.get_stats()
        sec_stats = sec_monitor.get_stats()
        db_health = await db_manager.health_check()

        perf_alerts = perf_monitor.check_alerts()
        sec_alerts = sec_monitor.check_alerts()

        # Determine overall status
        status = "healthy"
        if perf_alerts or sec_alerts or db_health["status"] != "healthy":
            status = "warning"
        if (
            any("CRITICAL" in a for a in perf_alerts + sec_alerts)
            or db_health["status"] == "unhealthy"
        ):
            status = "critical"

        return (
            jsonify(
                {
                    "status": status,
                    "summary": {
                        "database": {
                            "status": db_health["status"],
                            "pool_utilization": f"{((db_health['pool']['size'] - db_health['pool']['idle_size']) / db_health['pool']['max_size'] * 100):.1f}%",
                            "response_time_ms": db_health["response_time_ms"],
                        },
                        "performance": {
                            "p95_latency_ms": perf_stats["latency"]["p95_ms"],
                            "total_queries": perf_stats["total_queries"],
                            "success_rate": perf_stats["success_rate"],
                            "slow_queries": perf_stats["slow_queries"],
                        },
                        "security": {
                            "events_last_hour": sec_stats["events_last_hour"],
                            "critical_events": sec_stats["by_severity"].get(
                                "critical", 0
                            ),
                            "top_ip": sec_stats["top_offending_ips"][0]
                            if sec_stats["top_offending_ips"]
                            else None,
                        },
                        "alerts": {
                            "performance": len(perf_alerts),
                            "security": len(sec_alerts),
                            "database": 0 if db_health["status"] == "healthy" else 1,
                        },
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
