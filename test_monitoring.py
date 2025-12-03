#!/usr/bin/env python3
"""
Test script to demonstrate the monitoring and observability system.
"""

import asyncio
from datetime import datetime, timezone
import json

from src.database.connection import DatabaseManager
from src.observability.performance_monitor import get_monitor
from src.observability.security_monitor import get_security_monitor, SecurityEventType


async def test_performance_monitoring():
    """Test performance monitoring with actual database queries."""
    print("=" * 60)
    print("TESTING PERFORMANCE MONITORING")
    print("=" * 60)

    db = DatabaseManager()
    await db.connect()

    try:
        # Run several queries to generate metrics
        print("\n1. Running test queries...")
        for i in range(5):
            await db.fetchval("SELECT COUNT(*) FROM capsules")

        # Get performance stats
        print("\n2. Performance Statistics:")
        perf_monitor = get_monitor()
        stats = perf_monitor.get_stats()
        print(json.dumps(stats, indent=2))

        # Check for alerts
        print("\n3. Performance Alerts:")
        alerts = perf_monitor.check_alerts()
        if alerts:
            for alert in alerts:
                print(f"  - {alert}")
        else:
            print("  ✅ No performance alerts")

        # Get query breakdown
        print("\n4. Query Breakdown:")
        breakdown = perf_monitor.get_query_breakdown()
        for query_name, metrics in breakdown.items():
            print(f"  {query_name}:")
            print(f"    Count: {metrics['count']}")
            print(f"    Avg: {metrics['avg_ms']:.2f}ms")
            print(f"    Min: {metrics['min_ms']:.2f}ms")
            print(f"    Max: {metrics['max_ms']:.2f}ms")

    finally:
        await db.disconnect()


async def test_security_monitoring():
    """Test security monitoring with simulated events."""
    print("\n" + "=" * 60)
    print("TESTING SECURITY MONITORING")
    print("=" * 60)

    sec_monitor = get_security_monitor()

    # Simulate various security events
    print("\n1. Simulating security events...")

    # Test SQL injection detection
    print("  - Simulating SQL injection attempt...")
    sec_monitor.record_sql_injection_attempt(
        query="SELECT * FROM users WHERE id = '1' OR '1'='1'",
        source_ip="192.168.1.100",
        user_id="test_user",
    )

    # Test validation failures
    print("  - Simulating validation failures...")
    sec_monitor.record_validation_failure(
        field="capsule_type",
        value="invalid_type",
        reason="Type not in whitelist",
        source_ip="192.168.1.101",
    )

    # Test auth failures
    print("  - Simulating authentication failures...")
    for i in range(3):
        sec_monitor.record_auth_failure(
            username="hacker@example.com",
            source_ip="192.168.1.100",
            reason="Invalid credentials",
        )

    # Test rate limiting
    print("  - Simulating rate limit exceeded...")
    sec_monitor.record_rate_limit(
        endpoint="/api/v1/capsules", source_ip="192.168.1.102", user_id="spammer"
    )

    # Get security stats
    print("\n2. Security Statistics:")
    stats = sec_monitor.get_stats()
    print(json.dumps(stats, indent=2))

    # Check for alerts
    print("\n3. Security Alerts:")
    alerts = sec_monitor.check_alerts()
    if alerts:
        for alert in alerts:
            print(f"  - {alert}")
    else:
        print("  ✅ No security alerts")

    # Get recent events
    print("\n4. Recent Security Events:")
    recent = sec_monitor.get_recent_events(limit=5)
    for event in recent:
        print(f"  [{event['severity'].upper()}] {event['type']}")
        print(f"    {event['description']}")
        if event["source_ip"]:
            print(f"    IP: {event['source_ip']}")


async def test_combined_monitoring():
    """Test combined monitoring scenario."""
    print("\n" + "=" * 60)
    print("TESTING COMBINED MONITORING")
    print("=" * 60)

    db = DatabaseManager()
    await db.connect()

    try:
        # Simulate a real-world scenario: loading capsules with validation
        print("\n1. Simulating real-world scenario...")
        print("  - Loading capsules from database...")

        from src.database.secure_queries import QueryValidator, SecureCapsuleQueries

        # This will trigger validation and performance monitoring
        valid_types = ["reasoning_trace", "economic_transaction"]
        skip, limit = QueryValidator.validate_pagination(0, 10)

        rows = await db.fetch(
            SecureCapsuleQueries.LOAD_CAPSULES, valid_types, skip, limit
        )

        print(f"  - Loaded {len(rows)} capsules")

        # Try invalid input (triggers security monitoring)
        print("  - Testing input validation...")
        try:
            invalid_types = ["reasoning_trace", "malicious_type", "evil_sql_injection"]
            validated = QueryValidator.validate_capsule_types(invalid_types)
            print(f"  - Validated types: {validated}")
        except Exception as e:
            print(f"  - Validation correctly rejected invalid input: {e}")

        # Get combined metrics
        print("\n2. System Overview:")
        perf_monitor = get_monitor()
        sec_monitor = get_security_monitor()

        perf_stats = perf_monitor.get_stats()
        sec_stats = sec_monitor.get_stats()

        print(f"\n  Performance:")
        print(f"    Total Queries: {perf_stats['total_queries']}")
        print(f"    Success Rate: {perf_stats['success_rate']}")
        print(f"    P95 Latency: {perf_stats['latency']['p95_ms']:.2f}ms")

        print(f"\n  Security:")
        print(f"    Total Events: {sec_stats['total_events']}")
        print(f"    Events Last Hour: {sec_stats['events_last_hour']}")
        print(f"    By Severity: {sec_stats['by_severity']}")

        # Check all alerts
        print("\n3. All System Alerts:")
        perf_alerts = perf_monitor.check_alerts()
        sec_alerts = sec_monitor.check_alerts()

        all_alerts = perf_alerts + sec_alerts
        if all_alerts:
            for alert in all_alerts:
                print(f"  - {alert}")
        else:
            print("  ✅ No system alerts")

    finally:
        await db.disconnect()


async def main():
    """Run all monitoring tests."""
    print("\n" + "=" * 60)
    print("UATP MONITORING & OBSERVABILITY SYSTEM TEST")
    print("=" * 60)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")

    try:
        # Test each monitoring system
        await test_performance_monitoring()
        await test_security_monitoring()
        await test_combined_monitoring()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60)

        print("\n📊 Monitoring System Ready!")
        print("\nAPI Endpoints Available:")
        print("  - GET /api/v1/monitoring/health      - Complete system health")
        print("  - GET /api/v1/monitoring/performance - Detailed performance metrics")
        print("  - GET /api/v1/monitoring/security    - Security events and alerts")
        print("  - GET /api/v1/monitoring/database    - Database metrics")
        print("  - GET /api/v1/monitoring/alerts      - All system alerts")
        print("  - GET /api/v1/monitoring/summary     - Quick summary for dashboards")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
