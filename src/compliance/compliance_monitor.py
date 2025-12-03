"""
Continuous Compliance Monitoring System
Real-time compliance validation and automated audit controls
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Union

logger = logging.getLogger(__name__)


class MonitoringType(Enum):
    """Types of compliance monitoring"""

    REAL_TIME = "real_time"
    SCHEDULED = "scheduled"
    TRIGGERED = "triggered"
    MANUAL = "manual"


class ComplianceStatus(Enum):
    """Compliance status levels"""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    AT_RISK = "at_risk"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MonitoringScope(Enum):
    """Scope of monitoring activities"""

    SYSTEM_WIDE = "system_wide"
    USER_SPECIFIC = "user_specific"
    DATA_CATEGORY = "data_category"
    REGULATION_SPECIFIC = "regulation_specific"
    PROCESS_SPECIFIC = "process_specific"


@dataclass
class ComplianceMetric:
    """Individual compliance metric"""

    metric_id: str
    metric_name: str
    regulation_type: str
    description: str

    # Measurement
    target_value: float
    current_value: float
    threshold_warning: float
    threshold_critical: float

    # Calculation
    calculation_method: str
    data_sources: List[str] = field(default_factory=list)
    calculation_frequency: str = "hourly"  # hourly, daily, weekly, monthly

    # Status
    status: ComplianceStatus = ComplianceStatus.UNKNOWN
    last_calculated: Optional[datetime] = None
    trend: str = "stable"  # improving, stable, declining

    # Metadata
    unit: str = "percentage"
    category: str = "general"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceAlert:
    """Compliance monitoring alert"""

    alert_id: str
    alert_type: str
    severity: AlertSeverity
    created_at: datetime

    # Alert details
    title: str
    description: str
    regulation_type: str
    affected_metrics: List[str] = field(default_factory=list)

    # Context
    scope: MonitoringScope = MonitoringScope.SYSTEM_WIDE
    affected_users: List[str] = field(default_factory=list)
    affected_systems: List[str] = field(default_factory=list)

    # Status
    status: str = "open"  # open, investigating, resolved, false_positive
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    # Actions
    recommended_actions: List[str] = field(default_factory=list)
    automated_actions: List[str] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringRule:
    """Compliance monitoring rule"""

    rule_id: str
    rule_name: str
    description: str
    regulation_type: str

    # Rule configuration
    monitoring_type: MonitoringType
    scope: MonitoringScope
    frequency: str  # cron expression or interval

    # Conditions
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    aggregation_period: str = "1h"  # 1h, 24h, 7d, 30d

    # Actions
    alert_threshold: float = 0.8
    alert_severity: AlertSeverity = AlertSeverity.MEDIUM
    auto_remediate: bool = False
    escalation_rules: List[Dict[str, Any]] = field(default_factory=list)

    # Status
    is_active: bool = True
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    false_positive_count: int = 0

    # Metadata
    created_by: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ComplianceAuditTrail:
    """Compliance audit trail entry"""

    audit_id: str
    timestamp: datetime

    # Event details
    event_type: str
    event_description: str
    user_id: Optional[str] = None
    system_component: str = ""

    # Compliance context
    regulation_type: str = ""
    compliance_requirement: str = ""

    # Changes
    before_state: Dict[str, Any] = field(default_factory=dict)
    after_state: Dict[str, Any] = field(default_factory=dict)
    change_reason: str = ""

    # Validation
    compliance_validated: bool = False
    validation_results: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceDashboard:
    """Compliance dashboard data"""

    dashboard_id: str
    generated_at: datetime

    # Overall status
    overall_compliance_score: float
    compliant_frameworks: int
    non_compliant_frameworks: int
    at_risk_frameworks: int

    # Metrics summary
    total_metrics: int
    healthy_metrics: int
    warning_metrics: int
    critical_metrics: int

    # Alerts summary
    open_alerts: int
    critical_alerts: int
    recent_alerts: int

    # Trends
    compliance_trend: str  # improving, stable, declining
    trend_period_days: int = 30

    # Framework breakdown
    framework_scores: Dict[str, float] = field(default_factory=dict)
    framework_status: Dict[str, str] = field(default_factory=dict)

    # Recent activity
    recent_violations: List[Dict[str, Any]] = field(default_factory=list)
    recent_resolutions: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContinuousComplianceMonitor:
    """Continuous compliance monitoring and alerting system"""

    def __init__(self):
        self.metrics: Dict[str, ComplianceMetric] = {}
        self.alerts: Dict[str, ComplianceAlert] = {}
        self.monitoring_rules: Dict[str, MonitoringRule] = {}
        self.audit_trail: List[ComplianceAuditTrail] = []

        # Monitoring components
        self.metric_calculators: Dict[str, Callable] = {}
        self.alert_handlers: Dict[str, Callable] = {}
        self.remediation_actions: Dict[str, Callable] = {}

        # Statistics
        self.monitoring_stats = {
            "total_metrics": 0,
            "active_rules": 0,
            "alerts_generated": 0,
            "violations_detected": 0,
            "auto_remediations": 0,
            "compliance_score": 0.0,
        }

        # Initialize default metrics and rules
        self._initialize_default_metrics()
        self._initialize_default_rules()

        # Monitoring state
        self.monitoring_active = False
        self.monitoring_tasks: List[asyncio.Task] = []

    def _initialize_default_metrics(self):
        """Initialize default compliance metrics"""

        default_metrics = [
            ComplianceMetric(
                metric_id="gdpr_data_retention_compliance",
                metric_name="GDPR Data Retention Compliance",
                regulation_type="GDPR",
                description="Percentage of data records complying with retention policies",
                target_value=100.0,
                current_value=0.0,
                threshold_warning=95.0,
                threshold_critical=90.0,
                calculation_method="retention_analysis",
                data_sources=["data_retention_enforcer"],
                calculation_frequency="daily",
                category="data_protection",
            ),
            ComplianceMetric(
                metric_id="gdpr_consent_coverage",
                metric_name="GDPR Consent Coverage",
                regulation_type="GDPR",
                description="Percentage of data processing activities with valid consent",
                target_value=100.0,
                current_value=0.0,
                threshold_warning=98.0,
                threshold_critical=95.0,
                calculation_method="consent_analysis",
                data_sources=["consent_manager"],
                calculation_frequency="hourly",
                category="consent_management",
            ),
            ComplianceMetric(
                metric_id="gdpr_breach_notification_compliance",
                metric_name="GDPR Breach Notification Compliance",
                regulation_type="GDPR",
                description="Percentage of breaches notified within 72 hours",
                target_value=100.0,
                current_value=0.0,
                threshold_warning=100.0,
                threshold_critical=99.0,
                calculation_method="breach_notification_analysis",
                data_sources=["breach_notification_system"],
                calculation_frequency="hourly",
                category="incident_response",
            ),
            ComplianceMetric(
                metric_id="kyc_verification_rate",
                metric_name="KYC Verification Rate",
                regulation_type="AML",
                description="Percentage of users with completed KYC verification",
                target_value=100.0,
                current_value=0.0,
                threshold_warning=95.0,
                threshold_critical=90.0,
                calculation_method="kyc_analysis",
                data_sources=["financial_compliance_engine"],
                calculation_frequency="daily",
                category="financial_compliance",
            ),
            ComplianceMetric(
                metric_id="transaction_monitoring_coverage",
                metric_name="Transaction Monitoring Coverage",
                regulation_type="AML",
                description="Percentage of transactions monitored for suspicious activity",
                target_value=100.0,
                current_value=0.0,
                threshold_warning=99.0,
                threshold_critical=95.0,
                calculation_method="transaction_monitoring_analysis",
                data_sources=["financial_compliance_engine"],
                calculation_frequency="hourly",
                category="financial_compliance",
            ),
            ComplianceMetric(
                metric_id="cross_border_transfer_compliance",
                metric_name="Cross-Border Transfer Compliance",
                regulation_type="GDPR",
                description="Percentage of international transfers with valid legal basis",
                target_value=100.0,
                current_value=0.0,
                threshold_warning=100.0,
                threshold_critical=99.0,
                calculation_method="transfer_compliance_analysis",
                data_sources=["transfer_compliance_controller"],
                calculation_frequency="daily",
                category="data_protection",
            ),
            ComplianceMetric(
                metric_id="pci_dss_encryption_compliance",
                metric_name="PCI DSS Encryption Compliance",
                regulation_type="PCI_DSS",
                description="Percentage of payment data properly encrypted",
                target_value=100.0,
                current_value=0.0,
                threshold_warning=100.0,
                threshold_critical=99.0,
                calculation_method="encryption_analysis",
                data_sources=["payment_system"],
                calculation_frequency="hourly",
                category="payment_security",
            ),
            ComplianceMetric(
                metric_id="hipaa_access_control_compliance",
                metric_name="HIPAA Access Control Compliance",
                regulation_type="HIPAA",
                description="Percentage of PHI access requests with proper authorization",
                target_value=100.0,
                current_value=0.0,
                threshold_warning=98.0,
                threshold_critical=95.0,
                calculation_method="access_control_analysis",
                data_sources=["access_control_system"],
                calculation_frequency="hourly",
                category="healthcare_compliance",
            ),
        ]

        for metric in default_metrics:
            self.metrics[metric.metric_id] = metric

        self.monitoring_stats["total_metrics"] = len(self.metrics)

    def _initialize_default_rules(self):
        """Initialize default monitoring rules"""

        default_rules = [
            MonitoringRule(
                rule_id="gdpr_consent_expiry_warning",
                rule_name="GDPR Consent Expiry Warning",
                description="Alert when user consents are approaching expiry",
                regulation_type="GDPR",
                monitoring_type=MonitoringType.SCHEDULED,
                scope=MonitoringScope.SYSTEM_WIDE,
                frequency="0 8 * * *",  # Daily at 8 AM
                conditions=[
                    {"metric": "gdpr_consent_coverage", "operator": "lt", "value": 98.0}
                ],
                alert_severity=AlertSeverity.MEDIUM,
                auto_remediate=False,
            ),
            MonitoringRule(
                rule_id="gdpr_data_retention_violation",
                rule_name="GDPR Data Retention Violation",
                description="Alert when data retention policies are violated",
                regulation_type="GDPR",
                monitoring_type=MonitoringType.REAL_TIME,
                scope=MonitoringScope.SYSTEM_WIDE,
                frequency="continuous",
                conditions=[
                    {
                        "metric": "gdpr_data_retention_compliance",
                        "operator": "lt",
                        "value": 95.0,
                    }
                ],
                alert_severity=AlertSeverity.HIGH,
                auto_remediate=True,
            ),
            MonitoringRule(
                rule_id="gdpr_breach_notification_deadline",
                rule_name="GDPR Breach Notification Deadline",
                description="Critical alert when breach notification deadline is missed",
                regulation_type="GDPR",
                monitoring_type=MonitoringType.REAL_TIME,
                scope=MonitoringScope.SYSTEM_WIDE,
                frequency="continuous",
                conditions=[
                    {
                        "metric": "gdpr_breach_notification_compliance",
                        "operator": "lt",
                        "value": 100.0,
                    }
                ],
                alert_severity=AlertSeverity.CRITICAL,
                auto_remediate=False,
            ),
            MonitoringRule(
                rule_id="kyc_verification_backlog",
                rule_name="KYC Verification Backlog",
                description="Alert when KYC verification rate drops",
                regulation_type="AML",
                monitoring_type=MonitoringType.SCHEDULED,
                scope=MonitoringScope.SYSTEM_WIDE,
                frequency="0 */4 * * *",  # Every 4 hours
                conditions=[
                    {"metric": "kyc_verification_rate", "operator": "lt", "value": 95.0}
                ],
                alert_severity=AlertSeverity.MEDIUM,
                auto_remediate=False,
            ),
            MonitoringRule(
                rule_id="transaction_monitoring_failure",
                rule_name="Transaction Monitoring Failure",
                description="Alert when transaction monitoring coverage drops",
                regulation_type="AML",
                monitoring_type=MonitoringType.REAL_TIME,
                scope=MonitoringScope.SYSTEM_WIDE,
                frequency="continuous",
                conditions=[
                    {
                        "metric": "transaction_monitoring_coverage",
                        "operator": "lt",
                        "value": 99.0,
                    }
                ],
                alert_severity=AlertSeverity.HIGH,
                auto_remediate=True,
            ),
            MonitoringRule(
                rule_id="pci_dss_encryption_failure",
                rule_name="PCI DSS Encryption Failure",
                description="Critical alert when payment data encryption fails",
                regulation_type="PCI_DSS",
                monitoring_type=MonitoringType.REAL_TIME,
                scope=MonitoringScope.SYSTEM_WIDE,
                frequency="continuous",
                conditions=[
                    {
                        "metric": "pci_dss_encryption_compliance",
                        "operator": "lt",
                        "value": 100.0,
                    }
                ],
                alert_severity=AlertSeverity.CRITICAL,
                auto_remediate=True,
            ),
        ]

        for rule in default_rules:
            self.monitoring_rules[rule.rule_id] = rule

        self.monitoring_stats["active_rules"] = len(
            [r for r in self.monitoring_rules.values() if r.is_active]
        )

    def generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"alert_{timestamp}_{hash(timestamp) % 10000:04d}"

    def generate_audit_id(self) -> str:
        """Generate unique audit ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"audit_{timestamp}_{hash(timestamp) % 10000:04d}"

    def generate_dashboard_id(self) -> str:
        """Generate unique dashboard ID"""
        timestamp = str(int(datetime.now().timestamp()))
        return f"dash_{timestamp}_{hash(timestamp) % 10000:04d}"

    async def start_monitoring(self):
        """Start continuous compliance monitoring"""

        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return

        self.monitoring_active = True
        logger.info("Starting continuous compliance monitoring")

        try:
            # Start metric calculation tasks
            for metric_id in self.metrics.keys():
                task = asyncio.create_task(self._metric_calculation_loop(metric_id))
                self.monitoring_tasks.append(task)

            # Start rule execution tasks
            for rule_id in self.monitoring_rules.keys():
                task = asyncio.create_task(self._rule_execution_loop(rule_id))
                self.monitoring_tasks.append(task)

            # Start dashboard update task
            task = asyncio.create_task(self._dashboard_update_loop())
            self.monitoring_tasks.append(task)

            # Wait for all tasks
            await asyncio.gather(*self.monitoring_tasks)

        except asyncio.CancelledError:
            logger.info("Monitoring cancelled")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
        finally:
            self.monitoring_active = False

    async def stop_monitoring(self):
        """Stop continuous compliance monitoring"""

        self.monitoring_active = False

        # Cancel all monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)

        self.monitoring_tasks.clear()
        logger.info("Compliance monitoring stopped")

    async def _metric_calculation_loop(self, metric_id: str):
        """Continuous metric calculation loop"""

        metric = self.metrics.get(metric_id)
        if not metric:
            return

        while self.monitoring_active:
            try:
                # Calculate metric value
                await self._calculate_metric(metric_id)

                # Sleep based on calculation frequency
                sleep_duration = self._get_sleep_duration(metric.calculation_frequency)
                await asyncio.sleep(sleep_duration)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error calculating metric {metric_id}: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

    async def _rule_execution_loop(self, rule_id: str):
        """Continuous rule execution loop"""

        rule = self.monitoring_rules.get(rule_id)
        if not rule or not rule.is_active:
            return

        while self.monitoring_active:
            try:
                # Execute monitoring rule
                await self._execute_monitoring_rule(rule_id)

                # Sleep based on frequency
                if rule.monitoring_type == MonitoringType.REAL_TIME:
                    await asyncio.sleep(30)  # 30 seconds for real-time
                else:
                    sleep_duration = self._get_sleep_duration(rule.frequency)
                    await asyncio.sleep(sleep_duration)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error executing rule {rule_id}: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry

    async def _dashboard_update_loop(self):
        """Dashboard update loop"""

        while self.monitoring_active:
            try:
                # Update compliance dashboard
                await self._update_compliance_dashboard()

                # Update every 5 minutes
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error updating dashboard: {e}")
                await asyncio.sleep(300)

    def _get_sleep_duration(self, frequency: str) -> int:
        """Get sleep duration in seconds based on frequency"""

        frequency_map = {
            "continuous": 10,
            "hourly": 3600,
            "daily": 86400,
            "weekly": 604800,
            "monthly": 2592000,
        }

        return frequency_map.get(frequency, 3600)  # Default to hourly

    async def _calculate_metric(self, metric_id: str):
        """Calculate compliance metric value"""

        metric = self.metrics.get(metric_id)
        if not metric:
            return

        try:
            # Get calculator function
            calculator = self.metric_calculators.get(metric.calculation_method)

            if calculator:
                # Use custom calculator
                new_value = await calculator(metric)
            else:
                # Use default calculation based on method
                new_value = await self._default_metric_calculation(metric)

            # Update metric
            old_value = metric.current_value
            metric.current_value = new_value
            metric.last_calculated = datetime.now(timezone.utc)

            # Determine status
            if new_value >= metric.target_value:
                metric.status = ComplianceStatus.COMPLIANT
            elif new_value >= metric.threshold_warning:
                metric.status = ComplianceStatus.AT_RISK
            else:
                metric.status = ComplianceStatus.NON_COMPLIANT

            # Determine trend
            if new_value > old_value:
                metric.trend = "improving"
            elif new_value < old_value:
                metric.trend = "declining"
            else:
                metric.trend = "stable"

            logger.debug(
                f"Metric calculated: {metric_id} = {new_value:.2f}% (was {old_value:.2f}%)"
            )

        except Exception as e:
            logger.error(f"Failed to calculate metric {metric_id}: {e}")
            metric.status = ComplianceStatus.UNKNOWN

    async def _default_metric_calculation(self, metric: ComplianceMetric) -> float:
        """Default metric calculation (mock implementation)"""

        # Mock calculation based on metric type
        import random

        if "retention" in metric.metric_id:
            # Simulate data retention compliance
            return random.uniform(92.0, 99.5)
        elif "consent" in metric.metric_id:
            # Simulate consent coverage
            return random.uniform(95.0, 100.0)
        elif "breach" in metric.metric_id:
            # Simulate breach notification compliance
            return random.uniform(98.0, 100.0)
        elif "kyc" in metric.metric_id:
            # Simulate KYC verification rate
            return random.uniform(90.0, 98.0)
        elif "transaction" in metric.metric_id:
            # Simulate transaction monitoring
            return random.uniform(97.0, 100.0)
        elif "transfer" in metric.metric_id:
            # Simulate transfer compliance
            return random.uniform(99.0, 100.0)
        elif "encryption" in metric.metric_id:
            # Simulate encryption compliance
            return random.uniform(99.5, 100.0)
        elif "access" in metric.metric_id:
            # Simulate access control compliance
            return random.uniform(96.0, 100.0)
        else:
            return random.uniform(85.0, 100.0)

    async def _execute_monitoring_rule(self, rule_id: str):
        """Execute monitoring rule and generate alerts if needed"""

        rule = self.monitoring_rules.get(rule_id)
        if not rule or not rule.is_active:
            return

        try:
            rule.last_executed = datetime.now(timezone.utc)
            rule.execution_count += 1

            # Check rule conditions
            violations = []

            for condition in rule.conditions:
                metric_id = condition.get("metric")
                operator = condition.get("operator")
                threshold = condition.get("value")

                metric = self.metrics.get(metric_id)
                if not metric:
                    continue

                # Evaluate condition
                if self._evaluate_condition(metric.current_value, operator, threshold):
                    violations.append(
                        {
                            "metric_id": metric_id,
                            "metric_name": metric.metric_name,
                            "current_value": metric.current_value,
                            "threshold": threshold,
                            "operator": operator,
                        }
                    )

            # Generate alert if violations found
            if violations:
                await self._generate_compliance_alert(rule, violations)

            logger.debug(f"Rule executed: {rule_id} - Violations: {len(violations)}")

        except Exception as e:
            logger.error(f"Failed to execute rule {rule_id}: {e}")

    def _evaluate_condition(
        self, value: float, operator: str, threshold: float
    ) -> bool:
        """Evaluate monitoring condition"""

        if operator == "lt":
            return value < threshold
        elif operator == "le":
            return value <= threshold
        elif operator == "gt":
            return value > threshold
        elif operator == "ge":
            return value >= threshold
        elif operator == "eq":
            return value == threshold
        elif operator == "ne":
            return value != threshold
        else:
            return False

    async def _generate_compliance_alert(
        self, rule: MonitoringRule, violations: List[Dict[str, Any]]
    ):
        """Generate compliance alert"""

        alert_id = self.generate_alert_id()
        now = datetime.now(timezone.utc)

        # Create alert
        alert = ComplianceAlert(
            alert_id=alert_id,
            alert_type=rule.rule_name.lower().replace(" ", "_"),
            severity=rule.alert_severity,
            created_at=now,
            title=f"Compliance Violation: {rule.rule_name}",
            description=rule.description,
            regulation_type=rule.regulation_type,
            affected_metrics=[v["metric_id"] for v in violations],
        )

        # Add violation details
        violation_details = []
        for violation in violations:
            violation_details.append(
                f"{violation['metric_name']}: {violation['current_value']:.2f}% (threshold: {violation['threshold']:.2f}%)"
            )

        alert.description += f"\n\nViolations:\n" + "\n".join(violation_details)

        # Add recommended actions
        if rule.alert_severity == AlertSeverity.CRITICAL:
            alert.recommended_actions.extend(
                [
                    "Immediate investigation required",
                    "Escalate to compliance team",
                    "Document remediation actions",
                ]
            )
        elif rule.alert_severity == AlertSeverity.HIGH:
            alert.recommended_actions.extend(
                [
                    "Investigate root cause",
                    "Implement corrective measures",
                    "Monitor for improvement",
                ]
            )
        else:
            alert.recommended_actions.extend(
                [
                    "Review compliance procedures",
                    "Schedule compliance review",
                ]
            )

        # Store alert
        self.alerts[alert_id] = alert
        self.monitoring_stats["alerts_generated"] += 1

        # Execute automated remediation if configured
        if rule.auto_remediate:
            await self._execute_auto_remediation(alert, rule)

        # Call alert handlers
        for handler in self.alert_handlers.values():
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

        logger.warning(
            f"Compliance alert generated: {alert_id} - {alert.title} - Severity: {alert.severity.value}"
        )

    async def _execute_auto_remediation(
        self, alert: ComplianceAlert, rule: MonitoringRule
    ):
        """Execute automated remediation actions"""

        try:
            remediation_actions = []

            # Rule-specific remediation
            if "retention" in rule.rule_id:
                remediation_actions.append("Triggered automated data cleanup")
                # Would trigger data retention enforcer

            elif "consent" in rule.rule_id:
                remediation_actions.append("Initiated consent renewal process")
                # Would trigger consent renewal workflow

            elif "transaction" in rule.rule_id:
                remediation_actions.append("Restarted transaction monitoring service")
                # Would restart monitoring components

            elif "encryption" in rule.rule_id:
                remediation_actions.append("Validated encryption configurations")
                # Would check and fix encryption settings

            # Execute custom remediation actions
            remediation_handler = self.remediation_actions.get(rule.rule_id)
            if remediation_handler:
                custom_actions = await remediation_handler(alert, rule)
                remediation_actions.extend(custom_actions)

            # Update alert with automated actions
            alert.automated_actions = remediation_actions
            self.monitoring_stats["auto_remediations"] += 1

            logger.info(
                f"Auto-remediation executed for alert {alert.alert_id}: {len(remediation_actions)} actions"
            )

        except Exception as e:
            logger.error(f"Auto-remediation failed for alert {alert.alert_id}: {e}")

    async def _update_compliance_dashboard(self):
        """Update compliance dashboard"""

        try:
            # Calculate overall compliance score
            total_score = 0.0
            compliant_count = 0

            for metric in self.metrics.values():
                if metric.status == ComplianceStatus.COMPLIANT:
                    compliant_count += 1
                    total_score += metric.current_value
                elif metric.status == ComplianceStatus.AT_RISK:
                    total_score += metric.current_value * 0.8
                elif metric.status == ComplianceStatus.NON_COMPLIANT:
                    total_score += metric.current_value * 0.5

            overall_score = total_score / max(1, len(self.metrics))
            self.monitoring_stats["compliance_score"] = overall_score

            logger.debug(
                f"Compliance dashboard updated - Overall score: {overall_score:.2f}%"
            )

        except Exception as e:
            logger.error(f"Failed to update compliance dashboard: {e}")

    async def log_audit_event(
        self,
        event_type: str,
        event_description: str,
        user_id: Optional[str] = None,
        system_component: str = "",
        regulation_type: str = "",
        compliance_requirement: str = "",
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        change_reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log compliance audit event"""

        audit_id = self.generate_audit_id()
        now = datetime.now(timezone.utc)

        # Create audit trail entry
        audit_entry = ComplianceAuditTrail(
            audit_id=audit_id,
            timestamp=now,
            event_type=event_type,
            event_description=event_description,
            user_id=user_id,
            system_component=system_component,
            regulation_type=regulation_type,
            compliance_requirement=compliance_requirement,
            before_state=before_state or {},
            after_state=after_state or {},
            change_reason=change_reason,
            metadata=metadata or {},
        )

        # Store audit entry
        self.audit_trail.append(audit_entry)

        # Keep only last 10,000 entries
        if len(self.audit_trail) > 10000:
            self.audit_trail = self.audit_trail[-10000:]

        logger.info(
            f"Audit event logged: {audit_id} - {event_type} - {event_description}"
        )

        return audit_id

    async def get_compliance_dashboard(self) -> ComplianceDashboard:
        """Get current compliance dashboard"""

        dashboard_id = self.generate_dashboard_id()
        now = datetime.now(timezone.utc)

        # Calculate framework scores
        framework_scores = {}
        framework_status = {}

        frameworks = set(metric.regulation_type for metric in self.metrics.values())

        for framework in frameworks:
            framework_metrics = [
                m for m in self.metrics.values() if m.regulation_type == framework
            ]

            if framework_metrics:
                avg_score = sum(m.current_value for m in framework_metrics) / len(
                    framework_metrics
                )
                framework_scores[framework] = avg_score

                if avg_score >= 95.0:
                    framework_status[framework] = "compliant"
                elif avg_score >= 90.0:
                    framework_status[framework] = "at_risk"
                else:
                    framework_status[framework] = "non_compliant"

        # Count metrics by status
        healthy_metrics = len(
            [m for m in self.metrics.values() if m.status == ComplianceStatus.COMPLIANT]
        )
        warning_metrics = len(
            [m for m in self.metrics.values() if m.status == ComplianceStatus.AT_RISK]
        )
        critical_metrics = len(
            [
                m
                for m in self.metrics.values()
                if m.status == ComplianceStatus.NON_COMPLIANT
            ]
        )

        # Count alerts
        open_alerts = len([a for a in self.alerts.values() if a.status == "open"])
        critical_alerts = len(
            [
                a
                for a in self.alerts.values()
                if a.severity == AlertSeverity.CRITICAL and a.status == "open"
            ]
        )

        # Recent alerts (last 24 hours)
        yesterday = now - timedelta(days=1)
        recent_alerts = len(
            [a for a in self.alerts.values() if a.created_at >= yesterday]
        )

        # Recent violations
        recent_violations = [
            {
                "alert_id": alert.alert_id,
                "title": alert.title,
                "severity": alert.severity.value,
                "regulation_type": alert.regulation_type,
                "created_at": alert.created_at.isoformat(),
            }
            for alert in sorted(
                self.alerts.values(), key=lambda x: x.created_at, reverse=True
            )[:5]
            if alert.status == "open"
        ]

        # Create dashboard
        dashboard = ComplianceDashboard(
            dashboard_id=dashboard_id,
            generated_at=now,
            overall_compliance_score=self.monitoring_stats["compliance_score"],
            compliant_frameworks=len(
                [s for s in framework_status.values() if s == "compliant"]
            ),
            non_compliant_frameworks=len(
                [s for s in framework_status.values() if s == "non_compliant"]
            ),
            at_risk_frameworks=len(
                [s for s in framework_status.values() if s == "at_risk"]
            ),
            total_metrics=len(self.metrics),
            healthy_metrics=healthy_metrics,
            warning_metrics=warning_metrics,
            critical_metrics=critical_metrics,
            open_alerts=open_alerts,
            critical_alerts=critical_alerts,
            recent_alerts=recent_alerts,
            compliance_trend="stable",  # Would calculate based on historical data
            framework_scores=framework_scores,
            framework_status=framework_status,
            recent_violations=recent_violations,
        )

        return dashboard

    async def get_alert_details(self, alert_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed alert information"""

        alert = self.alerts.get(alert_id)
        if not alert:
            return None

        return {
            "alert_id": alert.alert_id,
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity.value,
            "status": alert.status,
            "regulation_type": alert.regulation_type,
            "created_at": alert.created_at.isoformat(),
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "affected_metrics": alert.affected_metrics,
            "recommended_actions": alert.recommended_actions,
            "automated_actions": alert.automated_actions,
            "assigned_to": alert.assigned_to,
            "resolution_notes": alert.resolution_notes,
        }

    async def resolve_alert(
        self, alert_id: str, resolved_by: str, resolution_notes: str
    ) -> bool:
        """Resolve compliance alert"""

        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        alert.status = "resolved"
        alert.resolved_at = datetime.now(timezone.utc)
        alert.assigned_to = resolved_by
        alert.resolution_notes = resolution_notes

        # Log resolution
        await self.log_audit_event(
            event_type="alert_resolved",
            event_description=f"Alert {alert_id} resolved: {alert.title}",
            user_id=resolved_by,
            regulation_type=alert.regulation_type,
            change_reason=resolution_notes,
        )

        logger.info(f"Alert resolved: {alert_id} by {resolved_by}")

        return True

    def register_metric_calculator(self, calculation_method: str, calculator: Callable):
        """Register custom metric calculator"""

        self.metric_calculators[calculation_method] = calculator
        logger.info(f"Metric calculator registered: {calculation_method}")

    def register_alert_handler(self, handler_name: str, handler: Callable):
        """Register custom alert handler"""

        self.alert_handlers[handler_name] = handler
        logger.info(f"Alert handler registered: {handler_name}")

    def register_remediation_action(self, rule_id: str, action: Callable):
        """Register custom remediation action"""

        self.remediation_actions[rule_id] = action
        logger.info(f"Remediation action registered for rule: {rule_id}")


# Factory function
def create_continuous_compliance_monitor() -> ContinuousComplianceMonitor:
    """Create continuous compliance monitor instance"""
    return ContinuousComplianceMonitor()
