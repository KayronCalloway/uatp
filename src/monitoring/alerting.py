#!/usr/bin/env python3
"""
Alerting System for UATP Capsule Engine
=======================================

This module provides alerting capabilities for monitoring the UATP system,
including rule-based alerts, notification channels, and alert management.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from monitoring.health_checks import get_health_manager, HealthStatus
from monitoring.metrics import get_metrics_collector

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""

    ACTIVE = "active"
    RESOLVED = "resolved"
    SILENCED = "silenced"


@dataclass
class Alert:
    """Alert data structure."""

    id: str
    name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    timestamp: datetime
    metric_name: str = None
    metric_value: float = None
    threshold: float = None
    service: str = None
    labels: Dict[str, str] = None
    resolved_at: Optional[datetime] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["severity"] = self.severity.value
        result["status"] = self.status.value
        result["timestamp"] = self.timestamp.isoformat()
        if self.resolved_at:
            result["resolved_at"] = self.resolved_at.isoformat()
        return result


@dataclass
class AlertRule:
    """Alert rule definition."""

    name: str
    metric_name: str
    threshold: float
    comparison: str  # '>', '<', '>=', '<=', '==', '!='
    severity: AlertSeverity
    duration: int = 60  # seconds
    message_template: str = None
    labels: Dict[str, str] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}
        if self.message_template is None:
            self.message_template = (
                f"{self.metric_name} {self.comparison} {self.threshold}"
            )


class NotificationChannel:
    """Base class for notification channels."""

    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert notification."""
        raise NotImplementedError


class LogNotificationChannel(NotificationChannel):
    """Log-based notification channel."""

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to logs."""
        try:
            log_level = {
                AlertSeverity.INFO: logging.INFO,
                AlertSeverity.WARNING: logging.WARNING,
                AlertSeverity.ERROR: logging.ERROR,
                AlertSeverity.CRITICAL: logging.CRITICAL,
            }.get(alert.severity, logging.INFO)

            logger.log(
                log_level,
                f"🚨 ALERT [{alert.severity.value.upper()}] {alert.name}: {alert.message}",
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send log alert: {e}")
            return False


class WebhookNotificationChannel(NotificationChannel):
    """Webhook-based notification channel."""

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to webhook."""
        try:
            import aiohttp

            webhook_url = self.config.get("webhook_url")
            if not webhook_url:
                logger.error("Webhook URL not configured")
                return False

            payload = {
                "alert": alert.to_dict(),
                "timestamp": datetime.now().isoformat(),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url, json=payload, timeout=10
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ Webhook alert sent: {alert.name}")
                        return True
                    else:
                        logger.error(f"❌ Webhook alert failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"❌ Failed to send webhook alert: {e}")
            return False


class EmailNotificationChannel(NotificationChannel):
    """Email-based notification channel."""

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via email."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_server = self.config.get("smtp_server")
            smtp_port = self.config.get("smtp_port", 587)
            username = self.config.get("username")
            password = self.config.get("password")
            to_email = self.config.get("to_email")

            if not all([smtp_server, username, password, to_email]):
                logger.error("Email configuration incomplete")
                return False

            # Create message
            msg = MIMEMultipart()
            msg["From"] = username
            msg["To"] = to_email
            msg["Subject"] = f"UATP Alert: {alert.name}"

            body = f"""
            Alert: {alert.name}
            Severity: {alert.severity.value.upper()}
            Message: {alert.message}
            Time: {alert.timestamp.isoformat()}
            Service: {alert.service or 'Unknown'}
            
            Metric: {alert.metric_name}
            Value: {alert.metric_value}
            Threshold: {alert.threshold}
            """

            msg.attach(MIMEText(body, "plain"))

            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()

            logger.info(f"✅ Email alert sent: {alert.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email alert: {e}")
            return False


class AlertManager:
    """Alert manager for UATP system."""

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.rule_states: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.evaluation_interval = 30  # seconds
        self.max_history = 1000

        # Default notification channel
        self.notification_channels["log"] = LogNotificationChannel("log")

        logger.info("🚨 Alert Manager initialized")

    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.rules.append(rule)
        self.rule_states[rule.name] = {
            "triggered_at": None,
            "last_value": None,
            "consecutive_triggers": 0,
        }
        logger.info(f"📋 Added alert rule: {rule.name}")

    def add_notification_channel(self, channel: NotificationChannel):
        """Add a notification channel."""
        self.notification_channels[channel.name] = channel
        logger.info(f"📢 Added notification channel: {channel.name}")

    async def start(self):
        """Start alert monitoring."""
        if self.running:
            return

        self.running = True
        self.evaluation_task = asyncio.create_task(self._evaluation_loop())
        logger.info("🚨 Alert monitoring started")

    async def stop(self):
        """Stop alert monitoring."""
        self.running = False
        if hasattr(self, "evaluation_task"):
            self.evaluation_task.cancel()
            try:
                await self.evaluation_task
            except asyncio.CancelledError:
                pass
        logger.info("🚨 Alert monitoring stopped")

    async def _evaluation_loop(self):
        """Main evaluation loop."""
        while self.running:
            try:
                await self._evaluate_rules()
                await asyncio.sleep(self.evaluation_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in alert evaluation: {e}")
                await asyncio.sleep(self.evaluation_interval)

    async def _evaluate_rules(self):
        """Evaluate all alert rules."""

        metrics_collector = get_metrics_collector()
        health_manager = get_health_manager()

        for rule in self.rules:
            try:
                await self._evaluate_rule(rule, metrics_collector, health_manager)
            except Exception as e:
                logger.error(f"❌ Error evaluating rule {rule.name}: {e}")

    async def _evaluate_rule(self, rule: AlertRule, metrics_collector, health_manager):
        """Evaluate a single alert rule."""

        rule_state = self.rule_states[rule.name]
        current_time = datetime.now()

        # Get metric value
        metric_value = await self._get_metric_value(
            rule, metrics_collector, health_manager
        )

        if metric_value is None:
            return

        rule_state["last_value"] = metric_value

        # Check threshold
        triggered = self._check_threshold(metric_value, rule.threshold, rule.comparison)

        if triggered:
            # Rule is triggered
            if rule_state["triggered_at"] is None:
                rule_state["triggered_at"] = current_time
                rule_state["consecutive_triggers"] = 1
            else:
                rule_state["consecutive_triggers"] += 1

                # Check if duration threshold is met
                duration_met = (
                    current_time - rule_state["triggered_at"]
                ).total_seconds() >= rule.duration

                if duration_met and rule.name not in self.active_alerts:
                    # Create alert
                    alert = Alert(
                        id=f"{rule.name}_{int(current_time.timestamp())}",
                        name=rule.name,
                        severity=rule.severity,
                        status=AlertStatus.ACTIVE,
                        message=rule.message_template.format(
                            metric_name=rule.metric_name,
                            value=metric_value,
                            threshold=rule.threshold,
                        ),
                        timestamp=current_time,
                        metric_name=rule.metric_name,
                        metric_value=metric_value,
                        threshold=rule.threshold,
                        labels=rule.labels,
                    )

                    await self._fire_alert(alert)
        else:
            # Rule is not triggered
            if rule_state["triggered_at"] is not None:
                # Was previously triggered, now resolved
                if rule.name in self.active_alerts:
                    await self._resolve_alert(rule.name)

                rule_state["triggered_at"] = None
                rule_state["consecutive_triggers"] = 0

    async def _get_metric_value(
        self, rule: AlertRule, metrics_collector, health_manager
    ) -> Optional[float]:
        """Get metric value for rule evaluation."""

        # Try to get from metrics collector
        metric_points = metrics_collector.get_metric(rule.metric_name, rule.labels)

        if metric_points:
            # Get the latest value
            return metric_points[-1].value

        # Try to get from health checks
        if rule.metric_name.startswith("health_"):
            service_name = rule.metric_name.replace("health_", "")
            result = await health_manager.run_check(service_name)

            if result.status == HealthStatus.HEALTHY:
                return 1.0
            elif result.status == HealthStatus.DEGRADED:
                return 0.5
            else:
                return 0.0

        return None

    def _check_threshold(self, value: float, threshold: float, comparison: str) -> bool:
        """Check if value meets threshold condition."""

        if comparison == ">":
            return value > threshold
        elif comparison == "<":
            return value < threshold
        elif comparison == ">=":
            return value >= threshold
        elif comparison == "<=":
            return value <= threshold
        elif comparison == "==":
            return value == threshold
        elif comparison == "!=":
            return value != threshold
        else:
            return False

    async def _fire_alert(self, alert: Alert):
        """Fire an alert."""

        # Add to active alerts
        self.active_alerts[alert.name] = alert

        # Add to history
        self.alert_history.append(alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)

        # Send notifications
        await self._send_notifications(alert)

        logger.warning(f"🚨 Alert fired: {alert.name} - {alert.message}")

    async def _resolve_alert(self, alert_name: str):
        """Resolve an alert."""

        if alert_name in self.active_alerts:
            alert = self.active_alerts[alert_name]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()

            # Remove from active alerts
            del self.active_alerts[alert_name]

            # Send resolution notification
            await self._send_notifications(alert)

            logger.info(f"✅ Alert resolved: {alert_name}")

    async def _send_notifications(self, alert: Alert):
        """Send alert notifications to all channels."""

        for channel_name, channel in self.notification_channels.items():
            try:
                await channel.send_alert(alert)
            except Exception as e:
                logger.error(f"❌ Failed to send notification via {channel_name}: {e}")

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts."""
        return [alert.to_dict() for alert in self.active_alerts.values()]

    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            alert.to_dict()
            for alert in self.alert_history
            if alert.timestamp > cutoff_time
        ]

    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""

        total_alerts = len(self.alert_history)
        active_count = len(self.active_alerts)

        # Count by severity
        severity_counts = {}
        for alert in self.alert_history:
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_alerts": total_alerts,
            "active_alerts": active_count,
            "severity_distribution": severity_counts,
            "rules_count": len(self.rules),
            "notification_channels": len(self.notification_channels),
        }


# Create default alert rules
def create_default_rules() -> List[AlertRule]:
    """Create default alert rules."""

    return [
        AlertRule(
            name="high_cpu_usage",
            metric_name="system_cpu_percent",
            threshold=80.0,
            comparison=">",
            severity=AlertSeverity.WARNING,
            duration=300,  # 5 minutes
            message_template="CPU usage is {value:.1f}%, exceeding threshold of {threshold}%",
        ),
        AlertRule(
            name="high_memory_usage",
            metric_name="system_memory_percent",
            threshold=85.0,
            comparison=">",
            severity=AlertSeverity.WARNING,
            duration=300,  # 5 minutes
            message_template="Memory usage is {value:.1f}%, exceeding threshold of {threshold}%",
        ),
        AlertRule(
            name="high_disk_usage",
            metric_name="system_disk_percent",
            threshold=90.0,
            comparison=">",
            severity=AlertSeverity.ERROR,
            duration=60,  # 1 minute
            message_template="Disk usage is {value:.1f}%, exceeding threshold of {threshold}%",
        ),
        AlertRule(
            name="database_unhealthy",
            metric_name="health_database",
            threshold=0.5,
            comparison="<",
            severity=AlertSeverity.CRITICAL,
            duration=30,  # 30 seconds
            message_template="Database health check failed",
        ),
        AlertRule(
            name="low_capsule_creation",
            metric_name="uatp_capsules_total",
            threshold=1.0,
            comparison="<",
            severity=AlertSeverity.INFO,
            duration=3600,  # 1 hour
            message_template="No capsules created in the last hour",
        ),
    ]


# Global alert manager
_alert_manager = None


def get_alert_manager() -> AlertManager:
    """Get the global alert manager."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()

        # Add default rules
        default_rules = create_default_rules()
        for rule in default_rules:
            _alert_manager.add_rule(rule)

    return _alert_manager


async def main():
    """Test alerting system."""

    print("🚨 Testing Alerting System")
    print("=" * 40)

    # Get alert manager
    alert_manager = get_alert_manager()

    # Add webhook channel (example)
    webhook_channel = WebhookNotificationChannel(
        "webhook", {"webhook_url": "https://httpbin.org/post"}
    )
    alert_manager.add_notification_channel(webhook_channel)

    # Start alert monitoring
    await alert_manager.start()

    # Let it run for a bit
    print("⏳ Running alert evaluation for 10 seconds...")
    await asyncio.sleep(10)

    # Show statistics
    stats = alert_manager.get_alert_stats()
    print(f"\n📊 Alert Statistics:")
    print(f"   Total alerts: {stats['total_alerts']}")
    print(f"   Active alerts: {stats['active_alerts']}")
    print(f"   Rules: {stats['rules_count']}")
    print(f"   Notification channels: {stats['notification_channels']}")

    # Show active alerts
    active_alerts = alert_manager.get_active_alerts()
    if active_alerts:
        print(f"\n🚨 Active Alerts:")
        for alert in active_alerts:
            print(f"   - {alert['name']}: {alert['message']}")
    else:
        print("\n✅ No active alerts")

    # Stop alert monitoring
    await alert_manager.stop()

    print("\n✅ Alerting system test completed!")


if __name__ == "__main__":
    asyncio.run(main())
