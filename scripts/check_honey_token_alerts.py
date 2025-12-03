"""
Check Honey Token Alerts

This script checks for recent honey token alerts (intrusion attempts).
Run this regularly to monitor for security breaches.

Usage:
    python scripts/check_honey_token_alerts.py
    python scripts/check_honey_token_alerts.py --count 50  # Check last 50 alerts
"""

import sys
from pathlib import Path
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.security.honey_tokens import HoneyTokenManager
import logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_alerts(count: int = 100, hours: int = 24):
    """
    Check recent honey token alerts.

    Args:
        count: Number of recent alerts to check
        hours: Only show alerts from last N hours
    """
    manager = HoneyTokenManager()

    logger.info(f"🔍 Checking last {count} honey token alerts (last {hours} hours)...")

    # Get recent alerts
    alerts = manager.get_recent_alerts(count=count)

    if not alerts:
        logger.info("✅ No honey token alerts found. System appears secure.")
        return

    # Filter by time window
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent_alerts = []

    for alert in alerts:
        alert_time = datetime.fromisoformat(alert.accessed_at)
        if alert_time >= cutoff_time:
            recent_alerts.append(alert)

    if not recent_alerts:
        logger.info(f"✅ No alerts in the last {hours} hours. System appears secure.")
        logger.info(f"   Total historical alerts: {len(alerts)}")
        return

    # Display alerts
    logger.critical(f"\n🚨 INTRUSION DETECTED 🚨")
    logger.critical(
        f"   {len(recent_alerts)} honey token alert(s) in the last {hours} hours!\n"
    )

    for i, alert in enumerate(recent_alerts, 1):
        logger.critical(f"--- Alert #{i} ---")
        logger.critical(f"   Alert ID: {alert.alert_id}")
        logger.critical(f"   Severity: {alert.alert_severity.upper()}")
        logger.critical(f"   Time: {alert.accessed_at}")
        logger.critical(f"   Token Type: {alert.token_type}")
        logger.critical(f"   Accessor IP: {alert.accessor_ip}")
        logger.critical(f"   User: {alert.accessor_user_id or 'Unknown'}")
        logger.critical(f"   Request: {alert.request_method} {alert.request_path}")
        logger.critical(f"   User Agent: {alert.accessor_user_agent or 'Unknown'}")
        logger.critical("")

    # Provide remediation advice
    logger.critical("⚠️  IMMEDIATE ACTIONS REQUIRED:")
    logger.critical("   1. Investigate the source IP addresses")
    logger.critical("   2. Review access logs for these time periods")
    logger.critical("   3. Check if legitimate users were compromised")
    logger.critical("   4. Rotate all real credentials immediately")
    logger.critical("   5. Block suspicious IPs at firewall")
    logger.critical("   6. Enable 2FA for all accounts")
    logger.critical("   7. Conduct full security audit")

    # Group by IP address
    ips = {}
    for alert in recent_alerts:
        ip = alert.accessor_ip or "Unknown"
        if ip not in ips:
            ips[ip] = 0
        ips[ip] += 1

    logger.critical(f"\n📊 Attacks by IP:")
    for ip, count in sorted(ips.items(), key=lambda x: x[1], reverse=True):
        logger.critical(f"   {ip}: {count} attempt(s)")


def main():
    parser = argparse.ArgumentParser(description="Check for honey token alerts")
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of recent alerts to check (default: 100)",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Only show alerts from last N hours (default: 24)",
    )

    args = parser.parse_args()

    check_alerts(count=args.count, hours=args.hours)


if __name__ == "__main__":
    main()
