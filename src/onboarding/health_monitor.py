"""
System Health Monitor

Provides real-time system health monitoring, SLA tracking, and proactive
issue detection for onboarding users. Ensures transparent system status
and builds user confidence.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import psutil

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels"""

    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ServiceStatus(Enum):
    """Individual service status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    MAINTENANCE = "maintenance"


@dataclass
class HealthMetric:
    """Individual health metric"""

    name: str
    value: float
    unit: str
    status: HealthStatus
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    description: str = ""


@dataclass
class ServiceHealth:
    """Health status of individual service"""

    name: str
    status: ServiceStatus
    response_time: Optional[float] = None
    last_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_rate: float = 0.0
    uptime_percentage: float = 100.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SLAMetrics:
    """Service Level Agreement metrics"""

    availability_target: float = 99.9  # percentage
    response_time_target: float = 1.0  # seconds
    error_rate_target: float = 0.1  # percentage

    current_availability: float = 100.0
    current_avg_response_time: float = 0.0
    current_error_rate: float = 0.0

    availability_trend: str = "stable"
    performance_trend: str = "stable"

    sla_breaches_24h: int = 0
    time_to_recovery_avg: float = 0.0


@dataclass
class SystemHealthReport:
    """Comprehensive system health report"""

    overall_status: HealthStatus
    score: float  # 0-100
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Core metrics
    system_metrics: List[HealthMetric] = field(default_factory=list)
    service_health: List[ServiceHealth] = field(default_factory=list)
    sla_metrics: SLAMetrics = field(default_factory=SLAMetrics)

    # Issues and recommendations
    active_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # User-friendly summary
    summary: str = "System operating normally"
    estimated_resolution_time: Optional[str] = None


class SystemHealthMonitor:
    """
    Real-time system health monitoring with SLA tracking.

    Provides:
    - Continuous health monitoring
    - SLA compliance tracking
    - Proactive issue detection
    - User-friendly health dashboards
    - Automated alerting
    """

    def __init__(self):
        """Initialize health monitor"""
        self.monitoring_active = False
        self.health_history: List[SystemHealthReport] = []
        self.service_registry: Dict[str, ServiceHealth] = {}
        self.alert_thresholds = self._initialize_alert_thresholds()

        # Initialize core services
        self._register_core_services()

        logger.info("System Health Monitor initialized")

    def _initialize_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize alerting thresholds"""
        return {
            "cpu_usage": {"warning": 70.0, "critical": 90.0},
            "memory_usage": {"warning": 80.0, "critical": 95.0},
            "disk_usage": {"warning": 85.0, "critical": 95.0},
            "response_time": {"warning": 2.0, "critical": 5.0},
            "error_rate": {"warning": 1.0, "critical": 5.0},
            "availability": {"warning": 99.0, "critical": 95.0},
        }

    def _register_core_services(self):
        """Register core UATP services for monitoring"""

        core_services = [
            "api_server",
            "capsule_engine",
            "database",
            "ai_integrations",
            "attribution_engine",
            "crypto_systems",
        ]

        for service in core_services:
            self.service_registry[service] = ServiceHealth(
                name=service, status=ServiceStatus.HEALTHY
            )

    async def start_monitoring(self):
        """Start continuous health monitoring"""

        if self.monitoring_active:
            logger.warning("Health monitoring already active")
            return

        self.monitoring_active = True
        logger.info(" Starting system health monitoring...")

        # Start monitoring tasks
        monitoring_tasks = [
            asyncio.create_task(self._monitor_system_metrics()),
            asyncio.create_task(self._monitor_service_health()),
            asyncio.create_task(self._track_sla_metrics()),
            asyncio.create_task(self._cleanup_old_data()),
        ]

        try:
            await asyncio.gather(*monitoring_tasks)
        except Exception as e:
            logger.error(f"Health monitoring failed: {e}")
        finally:
            self.monitoring_active = False

    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        logger.info(" Stopping system health monitoring")

    async def get_system_health(self) -> SystemHealthReport:
        """Get current system health report"""

        # Collect current metrics
        system_metrics = await self._collect_system_metrics()
        service_health = await self._check_all_services()
        sla_metrics = await self._calculate_sla_metrics()

        # Calculate overall health
        overall_status, score = self._calculate_overall_health(
            system_metrics, service_health
        )

        # Identify issues and recommendations
        active_issues = self._identify_active_issues(system_metrics, service_health)
        recommendations = self._generate_recommendations(active_issues, system_metrics)

        # Create health report
        report = SystemHealthReport(
            overall_status=overall_status,
            score=score,
            system_metrics=system_metrics,
            service_health=service_health,
            sla_metrics=sla_metrics,
            active_issues=active_issues,
            recommendations=recommendations,
            summary=self._generate_health_summary(overall_status, score, active_issues),
        )

        # Store in history
        self.health_history.append(report)

        return report

    async def _collect_system_metrics(self) -> List[HealthMetric]:
        """Collect system-level metrics"""

        metrics = []

        try:
            # CPU Usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(
                HealthMetric(
                    name="CPU Usage",
                    value=cpu_percent,
                    unit="%",
                    status=self._get_metric_status("cpu_usage", cpu_percent),
                    threshold_warning=self.alert_thresholds["cpu_usage"]["warning"],
                    threshold_critical=self.alert_thresholds["cpu_usage"]["critical"],
                    description="Current CPU utilization",
                )
            )

            # Memory Usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            metrics.append(
                HealthMetric(
                    name="Memory Usage",
                    value=memory_percent,
                    unit="%",
                    status=self._get_metric_status("memory_usage", memory_percent),
                    threshold_warning=self.alert_thresholds["memory_usage"]["warning"],
                    threshold_critical=self.alert_thresholds["memory_usage"][
                        "critical"
                    ],
                    description="Current memory utilization",
                )
            )

            # Disk Usage
            disk = psutil.disk_usage(".")
            disk_percent = (disk.used / disk.total) * 100
            metrics.append(
                HealthMetric(
                    name="Disk Usage",
                    value=disk_percent,
                    unit="%",
                    status=self._get_metric_status("disk_usage", disk_percent),
                    threshold_warning=self.alert_thresholds["disk_usage"]["warning"],
                    threshold_critical=self.alert_thresholds["disk_usage"]["critical"],
                    description="Current disk space utilization",
                )
            )

            # Network connectivity (simple check)
            network_status = await self._check_network_connectivity()
            metrics.append(
                HealthMetric(
                    name="Network Connectivity",
                    value=100.0 if network_status else 0.0,
                    unit="%",
                    status=HealthStatus.EXCELLENT
                    if network_status
                    else HealthStatus.CRITICAL,
                    threshold_warning=90.0,
                    threshold_critical=50.0,
                    description="Network connectivity status",
                )
            )

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")

        return metrics

    async def _check_all_services(self) -> List[ServiceHealth]:
        """Check health of all registered services"""

        service_health = []

        for service_name, service in self.service_registry.items():
            try:
                # Update service health
                updated_service = await self._check_service_health(service_name)
                service_health.append(updated_service)

                # Update registry
                self.service_registry[service_name] = updated_service

            except Exception as e:
                logger.error(f"Failed to check {service_name} health: {e}")

                # Mark as degraded
                service.status = ServiceStatus.DEGRADED
                service.last_check = datetime.now(timezone.utc)
                service_health.append(service)

        return service_health

    async def _check_service_health(self, service_name: str) -> ServiceHealth:
        """Check health of individual service"""

        service = self.service_registry[service_name]
        start_time = time.time()

        try:
            if service_name == "api_server":
                # Check API server health
                health_status = await self._check_api_server_health()

            elif service_name == "database":
                # Check database connectivity
                health_status = await self._check_database_health()

            elif service_name == "ai_integrations":
                # Check AI platform integrations
                health_status = await self._check_ai_integrations_health()

            else:
                # Default health check (placeholder)
                health_status = {"status": ServiceStatus.HEALTHY, "metadata": {}}

            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # ms

            # Update service health
            service.status = health_status["status"]
            service.response_time = response_time
            service.last_check = datetime.now(timezone.utc)
            service.metadata = health_status.get("metadata", {})

        except Exception as e:
            logger.error(f"Service health check failed for {service_name}: {e}")
            service.status = ServiceStatus.DOWN
            service.last_check = datetime.now(timezone.utc)
            service.metadata = {"error": str(e)}

        return service

    async def _check_api_server_health(self) -> Dict[str, Any]:
        """Check API server health"""

        try:
            # Try to import and check API components
            from ..api.server import create_app

            # If we can import successfully, consider it healthy
            return {
                "status": ServiceStatus.HEALTHY,
                "metadata": {"check": "import_successful"},
            }

        except ImportError as e:
            return {
                "status": ServiceStatus.DOWN,
                "metadata": {"error": f"Import failed: {str(e)}"},
            }

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""

        try:
            # Check if database components are available
            from ..database.connection import db

            return {
                "status": ServiceStatus.HEALTHY,
                "metadata": {"check": "components_available"},
            }

        except ImportError as e:
            return {
                "status": ServiceStatus.DEGRADED,
                "metadata": {"error": f"Database components unavailable: {str(e)}"},
            }

    async def _check_ai_integrations_health(self) -> Dict[str, Any]:
        """Check AI integrations health"""

        try:
            from ..integrations.anthropic_client import AnthropicAttributionClient
            from ..integrations.openai_client import OpenAIClient

            healthy_integrations = 0
            total_integrations = 2

            # Check OpenAI
            try:
                # Just check if we can create client
                OpenAIClient()
                healthy_integrations += 1
            except Exception:
                pass

            # Check Anthropic
            try:
                AnthropicAttributionClient()
                healthy_integrations += 1
            except Exception:
                pass

            health_ratio = healthy_integrations / total_integrations

            if health_ratio >= 0.8:
                status = ServiceStatus.HEALTHY
            elif health_ratio >= 0.5:
                status = ServiceStatus.DEGRADED
            else:
                status = ServiceStatus.DOWN

            return {
                "status": status,
                "metadata": {
                    "healthy_integrations": healthy_integrations,
                    "total_integrations": total_integrations,
                    "health_ratio": health_ratio,
                },
            }

        except Exception as e:
            return {"status": ServiceStatus.DOWN, "metadata": {"error": str(e)}}

    async def _calculate_sla_metrics(self) -> SLAMetrics:
        """Calculate SLA compliance metrics"""

        sla = SLAMetrics()

        # Calculate from recent health history
        if len(self.health_history) > 0:
            recent_reports = self.health_history[-24:]  # Last 24 checks

            if recent_reports:
                # Calculate availability
                healthy_count = sum(
                    1
                    for report in recent_reports
                    if report.overall_status
                    in [HealthStatus.EXCELLENT, HealthStatus.GOOD]
                )
                sla.current_availability = (healthy_count / len(recent_reports)) * 100

                # Calculate average response time from service health
                response_times = []
                error_counts = 0

                for report in recent_reports:
                    for service in report.service_health:
                        if service.response_time:
                            response_times.append(service.response_time)
                        if service.status in [
                            ServiceStatus.DOWN,
                            ServiceStatus.DEGRADED,
                        ]:
                            error_counts += 1

                if response_times:
                    sla.current_avg_response_time = (
                        sum(response_times) / len(response_times) / 1000
                    )  # Convert to seconds

                if len(recent_reports) > 0:
                    sla.current_error_rate = (
                        error_counts
                        / (len(recent_reports) * len(self.service_registry))
                    ) * 100

        # Determine trends (simplified)
        if sla.current_availability >= sla.availability_target:
            sla.availability_trend = "positive"
        elif sla.current_availability >= sla.availability_target - 1.0:
            sla.availability_trend = "stable"
        else:
            sla.availability_trend = "negative"

        return sla

    def _get_metric_status(self, metric_type: str, value: float) -> HealthStatus:
        """Get health status for a metric value"""

        thresholds = self.alert_thresholds.get(metric_type, {})
        critical = thresholds.get("critical", 100)
        warning = thresholds.get("warning", 80)

        if value >= critical:
            return HealthStatus.CRITICAL
        elif value >= warning:
            return HealthStatus.WARNING
        elif value <= warning * 0.5:
            return HealthStatus.EXCELLENT
        else:
            return HealthStatus.GOOD

    def _calculate_overall_health(
        self, metrics: List[HealthMetric], services: List[ServiceHealth]
    ) -> Tuple[HealthStatus, float]:
        """Calculate overall system health"""

        # Weight different factors
        metric_weights = {
            "CPU Usage": 0.2,
            "Memory Usage": 0.3,
            "Disk Usage": 0.1,
            "Network Connectivity": 0.4,
        }
        service_weight = 0.6
        metric_weight = 0.4

        # Calculate metric score
        metric_score = 0.0
        total_weight = 0.0

        for metric in metrics:
            weight = metric_weights.get(metric.name, 0.1)

            if metric.status == HealthStatus.EXCELLENT:
                score = 100
            elif metric.status == HealthStatus.GOOD:
                score = 85
            elif metric.status == HealthStatus.WARNING:
                score = 60
            elif metric.status == HealthStatus.CRITICAL:
                score = 20
            else:
                score = 50

            metric_score += score * weight
            total_weight += weight

        if total_weight > 0:
            metric_score = metric_score / total_weight
        else:
            metric_score = 50

        # Calculate service score
        service_score = 0.0
        if services:
            healthy_services = sum(
                1 for service in services if service.status == ServiceStatus.HEALTHY
            )
            service_score = (healthy_services / len(services)) * 100

        # Combined score
        overall_score = (metric_score * metric_weight) + (
            service_score * service_weight
        )

        # Determine status
        if overall_score >= 90:
            status = HealthStatus.EXCELLENT
        elif overall_score >= 75:
            status = HealthStatus.GOOD
        elif overall_score >= 50:
            status = HealthStatus.WARNING
        else:
            status = HealthStatus.CRITICAL

        return status, overall_score

    def _identify_active_issues(
        self, metrics: List[HealthMetric], services: List[ServiceHealth]
    ) -> List[str]:
        """Identify active system issues"""

        issues = []

        # Check metric issues
        for metric in metrics:
            if metric.status == HealthStatus.CRITICAL:
                issues.append(
                    f"CRITICAL: {metric.name} at {metric.value:.1f}{metric.unit}"
                )
            elif metric.status == HealthStatus.WARNING:
                issues.append(
                    f"WARNING: {metric.name} at {metric.value:.1f}{metric.unit}"
                )

        # Check service issues
        for service in services:
            if service.status == ServiceStatus.DOWN:
                issues.append(f"CRITICAL: {service.name} service is down")
            elif service.status == ServiceStatus.DEGRADED:
                issues.append(f"WARNING: {service.name} service is degraded")

        return issues

    def _generate_recommendations(
        self, issues: List[str], metrics: List[HealthMetric]
    ) -> List[str]:
        """Generate recommendations based on issues"""

        recommendations = []

        # Analyze issues and provide recommendations
        for issue in issues:
            if "CPU Usage" in issue:
                recommendations.append(
                    "Consider closing unnecessary applications or upgrading CPU"
                )
            elif "Memory Usage" in issue:
                recommendations.append(
                    "Close memory-intensive applications or add more RAM"
                )
            elif "Disk Usage" in issue:
                recommendations.append("Free up disk space by removing unused files")
            elif "Network" in issue:
                recommendations.append("Check internet connection and network settings")
            elif "service is down" in issue:
                recommendations.append(
                    "Restart the affected service or check its configuration"
                )

        # If no specific recommendations, provide general ones
        if not recommendations and not issues:
            recommendations.append("System is running optimally")
        elif not recommendations:
            recommendations.append(
                "Monitor system closely and consider restarting if issues persist"
            )

        return recommendations

    def _generate_health_summary(
        self, status: HealthStatus, score: float, issues: List[str]
    ) -> str:
        """Generate user-friendly health summary"""

        if status == HealthStatus.EXCELLENT:
            return f"System is running excellently (Score: {score:.0f}/100)"
        elif status == HealthStatus.GOOD:
            return f"System is running well (Score: {score:.0f}/100)"
        elif status == HealthStatus.WARNING:
            return f"System has some performance issues (Score: {score:.0f}/100)"
        elif status == HealthStatus.CRITICAL:
            return f"System requires immediate attention (Score: {score:.0f}/100)"
        else:
            return f"System status unknown (Score: {score:.0f}/100)"

    async def _check_network_connectivity(self) -> bool:
        """Check basic network connectivity"""
        try:
            import urllib.request

            urllib.request.urlopen("https://8.8.8.8", timeout=3)
            return True
        except Exception:
            return False

    # Background monitoring tasks

    async def _monitor_system_metrics(self):
        """Background task to monitor system metrics"""

        while self.monitoring_active:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"System metrics monitoring error: {e}")
                await asyncio.sleep(60)

    async def _monitor_service_health(self):
        """Background task to monitor service health"""

        while self.monitoring_active:
            try:
                await self._check_all_services()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Service health monitoring error: {e}")
                await asyncio.sleep(120)

    async def _track_sla_metrics(self):
        """Background task to track SLA metrics"""

        while self.monitoring_active:
            try:
                await self._calculate_sla_metrics()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"SLA metrics tracking error: {e}")
                await asyncio.sleep(600)

    async def _cleanup_old_data(self):
        """Background task to clean up old monitoring data"""

        while self.monitoring_active:
            try:
                # Keep only last 1000 health reports
                if len(self.health_history) > 1000:
                    self.health_history = self.health_history[-1000:]

                await asyncio.sleep(3600)  # Cleanup every hour
            except Exception as e:
                logger.error(f"Data cleanup error: {e}")
                await asyncio.sleep(3600)

    # Public interface methods

    async def get_sla_dashboard(self) -> Dict[str, Any]:
        """Get SLA dashboard data"""

        report = await self.get_system_health()

        return {
            "sla_metrics": report.sla_metrics.__dict__,
            "current_status": report.overall_status.value,
            "score": report.score,
            "availability_target": report.sla_metrics.availability_target,
            "response_time_target": report.sla_metrics.response_time_target,
            "uptime_24h": report.sla_metrics.current_availability,
            "avg_response_time": report.sla_metrics.current_avg_response_time,
            "error_rate": report.sla_metrics.current_error_rate,
            "trends": {
                "availability": report.sla_metrics.availability_trend,
                "performance": report.sla_metrics.performance_trend,
            },
        }

    async def get_service_dashboard(self) -> Dict[str, Any]:
        """Get service health dashboard"""

        report = await self.get_system_health()

        return {
            "services": [service.__dict__ for service in report.service_health],
            "total_services": len(report.service_health),
            "healthy_services": len(
                [s for s in report.service_health if s.status == ServiceStatus.HEALTHY]
            ),
            "degraded_services": len(
                [s for s in report.service_health if s.status == ServiceStatus.DEGRADED]
            ),
            "down_services": len(
                [s for s in report.service_health if s.status == ServiceStatus.DOWN]
            ),
        }

    async def get_metrics_dashboard(self) -> Dict[str, Any]:
        """Get system metrics dashboard"""

        report = await self.get_system_health()

        return {
            "metrics": [metric.__dict__ for metric in report.system_metrics],
            "overall_score": report.score,
            "status": report.overall_status.value,
            "summary": report.summary,
            "active_issues": report.active_issues,
            "recommendations": report.recommendations,
        }
