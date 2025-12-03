"""
Production Deployment System for UATP Capsule Engine.
Comprehensive deployment orchestration, monitoring, and management for production environments.
"""

import asyncio
import hashlib
import json
import logging
import os
import secrets
import sqlite3
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from src.audit.events import audit_emitter
from src.crypto.post_quantum import post_quantum_crypto
from src.crypto.zero_knowledge import zk_system
from src.optimization.performance_layer import performance_layer

logger = logging.getLogger(__name__)


class DeploymentStage(str, Enum):
    """Deployment stages."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    DISASTER_RECOVERY = "disaster_recovery"


class ServiceType(str, Enum):
    """Service types in the deployment."""

    API_SERVER = "api_server"
    WORKER = "worker"
    DATABASE = "database"
    CACHE = "cache"
    LOAD_BALANCER = "load_balancer"
    MONITORING = "monitoring"
    BACKUP = "backup"


class DeploymentStatus(str, Enum):
    """Deployment status."""

    PENDING = "pending"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class HealthStatus(str, Enum):
    """Health status for services."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class DeploymentConfig:
    """Configuration for deployment."""

    environment: DeploymentStage
    version: str
    replicas: int
    resources: Dict[str, Any]
    environment_variables: Dict[str, str]
    secrets: Dict[str, str]
    health_check: Dict[str, Any]
    scaling_policy: Dict[str, Any]
    backup_policy: Dict[str, Any]
    security_policy: Dict[str, Any]
    networking: Dict[str, Any]
    storage: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "environment": self.environment.value,
            "version": self.version,
            "replicas": self.replicas,
            "resources": self.resources,
            "environment_variables": self.environment_variables,
            "secrets": self.secrets,
            "health_check": self.health_check,
            "scaling_policy": self.scaling_policy,
            "backup_policy": self.backup_policy,
            "security_policy": self.security_policy,
            "networking": self.networking,
            "storage": self.storage,
        }


@dataclass
class ServiceConfig:
    """Configuration for individual service."""

    service_name: str
    service_type: ServiceType
    image: str
    ports: List[int]
    environment: Dict[str, str]
    volumes: List[str]
    dependencies: List[str]
    health_check: Dict[str, Any]
    resources: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "service_name": self.service_name,
            "service_type": self.service_type.value,
            "image": self.image,
            "ports": self.ports,
            "environment": self.environment,
            "volumes": self.volumes,
            "dependencies": self.dependencies,
            "health_check": self.health_check,
            "resources": self.resources,
        }


@dataclass
class HealthCheck:
    """Health check configuration."""

    endpoint: str
    method: str
    expected_status: int
    timeout: int
    interval: int
    retries: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "expected_status": self.expected_status,
            "timeout": self.timeout,
            "interval": self.interval,
            "retries": self.retries,
        }


@dataclass
class ScalingPolicy:
    """Auto-scaling policy."""

    min_replicas: int
    max_replicas: int
    target_cpu_utilization: float
    target_memory_utilization: float
    scale_up_threshold: float
    scale_down_threshold: float
    cooldown_period: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "min_replicas": self.min_replicas,
            "max_replicas": self.max_replicas,
            "target_cpu_utilization": self.target_cpu_utilization,
            "target_memory_utilization": self.target_memory_utilization,
            "scale_up_threshold": self.scale_up_threshold,
            "scale_down_threshold": self.scale_down_threshold,
            "cooldown_period": self.cooldown_period,
        }


@dataclass
class BackupPolicy:
    """Backup policy configuration."""

    enabled: bool
    schedule: str
    retention_days: int
    backup_type: str
    storage_location: str
    encryption_enabled: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "schedule": self.schedule,
            "retention_days": self.retention_days,
            "backup_type": self.backup_type,
            "storage_location": self.storage_location,
            "encryption_enabled": self.encryption_enabled,
        }


@dataclass
class SecurityPolicy:
    """Security policy configuration."""

    tls_enabled: bool
    certificate_path: str
    authentication_required: bool
    authorization_enabled: bool
    rate_limiting: Dict[str, Any]
    firewall_rules: List[Dict[str, Any]]
    encryption_at_rest: bool
    encryption_in_transit: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tls_enabled": self.tls_enabled,
            "certificate_path": self.certificate_path,
            "authentication_required": self.authentication_required,
            "authorization_enabled": self.authorization_enabled,
            "rate_limiting": self.rate_limiting,
            "firewall_rules": self.firewall_rules,
            "encryption_at_rest": self.encryption_at_rest,
            "encryption_in_transit": self.encryption_in_transit,
        }


@dataclass
class DeploymentResult:
    """Result of deployment operation."""

    deployment_id: str
    status: DeploymentStatus
    message: str
    timestamp: datetime
    duration: float
    services_deployed: List[str]
    rollback_available: bool
    health_checks_passed: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "deployment_id": self.deployment_id,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "duration": self.duration,
            "services_deployed": self.services_deployed,
            "rollback_available": self.rollback_available,
            "health_checks_passed": self.health_checks_passed,
            "metadata": self.metadata,
        }


class DatabaseMigrator:
    """Handles database migrations for deployment."""

    def __init__(self, db_path: str = "deployment.db"):
        self.db_path = db_path
        self.migrations_applied: Set[str] = set()
        self._initialize_database()

    def _initialize_database(self):
        """Initialize deployment database."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create deployment tracking table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deployment_id TEXT UNIQUE NOT NULL,
                environment TEXT NOT NULL,
                version TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                duration REAL,
                metadata TEXT
            )
        """
        )

        # Create service tracking table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                service_type TEXT NOT NULL,
                deployment_id TEXT NOT NULL,
                status TEXT NOT NULL,
                health_status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (deployment_id) REFERENCES deployments (deployment_id)
            )
        """
        )

        # Create migrations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                migration_name TEXT UNIQUE NOT NULL,
                applied_at TEXT NOT NULL,
                checksum TEXT NOT NULL
            )
        """
        )

        conn.commit()
        conn.close()

        logger.info("Database initialized for deployment tracking")

    async def apply_migrations(self, migrations_dir: str = "migrations") -> List[str]:
        """Apply database migrations."""

        applied_migrations = []

        if not os.path.exists(migrations_dir):
            logger.info("No migrations directory found")
            return applied_migrations

        # Get migration files
        migration_files = sorted(
            [f for f in os.listdir(migrations_dir) if f.endswith(".sql")]
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for migration_file in migration_files:
            # Check if migration already applied
            cursor.execute(
                "SELECT COUNT(*) FROM migrations WHERE migration_name = ?",
                (migration_file,),
            )

            if cursor.fetchone()[0] > 0:
                continue

            # Read migration file
            migration_path = os.path.join(migrations_dir, migration_file)

            try:
                with open(migration_path) as f:
                    migration_sql = f.read()

                # Calculate checksum
                checksum = hashlib.sha256(migration_sql.encode()).hexdigest()

                # Apply migration
                cursor.executescript(migration_sql)

                # Record migration
                cursor.execute(
                    "INSERT INTO migrations (migration_name, applied_at, checksum) VALUES (?, ?, ?)",
                    (migration_file, datetime.now(timezone.utc).isoformat(), checksum),
                )

                applied_migrations.append(migration_file)
                self.migrations_applied.add(migration_file)

                logger.info(f"Applied migration: {migration_file}")

            except Exception as e:
                logger.error(f"Failed to apply migration {migration_file}: {e}")
                conn.rollback()
                break

        conn.commit()
        conn.close()

        return applied_migrations

    def record_deployment(self, deployment_result: DeploymentResult):
        """Record deployment in database."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO deployments
            (deployment_id, environment, version, status, timestamp, duration, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                deployment_result.deployment_id,
                deployment_result.metadata.get("environment", "unknown"),
                deployment_result.metadata.get("version", "unknown"),
                deployment_result.status.value,
                deployment_result.timestamp.isoformat(),
                deployment_result.duration,
                json.dumps(deployment_result.metadata),
            ),
        )

        conn.commit()
        conn.close()

    def get_deployment_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get deployment history."""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT deployment_id, environment, version, status, timestamp, duration, metadata
            FROM deployments
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "deployment_id": row[0],
                    "environment": row[1],
                    "version": row[2],
                    "status": row[3],
                    "timestamp": row[4],
                    "duration": row[5],
                    "metadata": json.loads(row[6]) if row[6] else {},
                }
            )

        conn.close()
        return results


class HealthMonitor:
    """Monitors health of deployed services."""

    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.service_health: Dict[str, HealthStatus] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.health_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.alert_callbacks: List[Callable] = []

    def add_health_check(self, service_name: str, health_check: HealthCheck):
        """Add health check for service."""
        self.health_checks[service_name] = health_check
        self.service_health[service_name] = HealthStatus.UNKNOWN

    async def start_monitoring(self, service_name: str):
        """Start monitoring a service."""

        if service_name not in self.health_checks:
            logger.warning(f"No health check configured for service: {service_name}")
            return

        if service_name in self.monitoring_tasks:
            logger.warning(f"Already monitoring service: {service_name}")
            return

        # Start monitoring task
        task = asyncio.create_task(self._monitor_service(service_name))
        self.monitoring_tasks[service_name] = task

        logger.info(f"Started health monitoring for service: {service_name}")

    async def stop_monitoring(self, service_name: str):
        """Stop monitoring a service."""

        if service_name in self.monitoring_tasks:
            task = self.monitoring_tasks[service_name]
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            del self.monitoring_tasks[service_name]
            logger.info(f"Stopped health monitoring for service: {service_name}")

    async def _monitor_service(self, service_name: str):
        """Monitor service health."""

        health_check = self.health_checks[service_name]

        while True:
            try:
                # Perform health check
                health_status = await self._perform_health_check(
                    service_name, health_check
                )

                # Update service health
                previous_status = self.service_health.get(service_name)
                self.service_health[service_name] = health_status

                # Record health history
                health_record = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": health_status.value,
                    "service": service_name,
                }
                self.health_history[service_name].append(health_record)

                # Keep only recent history
                if len(self.health_history[service_name]) > 100:
                    self.health_history[service_name] = self.health_history[
                        service_name
                    ][-100:]

                # Check for status changes
                if previous_status and previous_status != health_status:
                    logger.info(
                        f"Service {service_name} health changed: {previous_status.value} -> {health_status.value}"
                    )

                    # Trigger alerts if unhealthy
                    if health_status == HealthStatus.UNHEALTHY:
                        await self._trigger_alerts(service_name, health_status)

                await asyncio.sleep(health_check.interval)

            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                self.service_health[service_name] = HealthStatus.UNKNOWN
                await asyncio.sleep(health_check.interval)

    async def _perform_health_check(
        self, service_name: str, health_check: HealthCheck
    ) -> HealthStatus:
        """Perform health check for service."""

        try:
            # Simulate health check (in production, this would make HTTP requests)
            # For now, we'll simulate based on service uptime

            import random

            # Simulate occasional health issues
            if random.random() < 0.1:  # 10% chance of temporary issues
                return HealthStatus.DEGRADED
            elif random.random() < 0.05:  # 5% chance of health issues
                return HealthStatus.UNHEALTHY
            else:
                return HealthStatus.HEALTHY

        except Exception as e:
            logger.error(f"Health check error for {service_name}: {e}")
            return HealthStatus.UNKNOWN

    async def _trigger_alerts(self, service_name: str, health_status: HealthStatus):
        """Trigger alerts for unhealthy services."""

        alert_data = {
            "service_name": service_name,
            "health_status": health_status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": "high" if health_status == HealthStatus.UNHEALTHY else "medium",
        }

        # Execute alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def add_alert_callback(self, callback: Callable):
        """Add alert callback."""
        self.alert_callbacks.append(callback)

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for all services."""

        total_services = len(self.service_health)
        healthy_services = sum(
            1
            for status in self.service_health.values()
            if status == HealthStatus.HEALTHY
        )
        degraded_services = sum(
            1
            for status in self.service_health.values()
            if status == HealthStatus.DEGRADED
        )
        unhealthy_services = sum(
            1
            for status in self.service_health.values()
            if status == HealthStatus.UNHEALTHY
        )

        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "degraded_services": degraded_services,
            "unhealthy_services": unhealthy_services,
            "overall_health": "healthy"
            if unhealthy_services == 0 and degraded_services == 0
            else "degraded"
            if unhealthy_services == 0
            else "unhealthy",
            "service_status": {
                name: status.value for name, status in self.service_health.items()
            },
        }


class AutoScaler:
    """Handles automatic scaling of services."""

    def __init__(self, health_monitor: HealthMonitor):
        self.health_monitor = health_monitor
        self.scaling_policies: Dict[str, ScalingPolicy] = {}
        self.current_replicas: Dict[str, int] = {}
        self.scaling_history: List[Dict[str, Any]] = []
        self.cooldown_end_times: Dict[str, datetime] = {}

    def add_scaling_policy(self, service_name: str, policy: ScalingPolicy):
        """Add scaling policy for service."""
        self.scaling_policies[service_name] = policy
        self.current_replicas[service_name] = policy.min_replicas

    async def evaluate_scaling(
        self, service_name: str, metrics: Dict[str, float]
    ) -> Optional[int]:
        """Evaluate if scaling is needed for service."""

        if service_name not in self.scaling_policies:
            return None

        policy = self.scaling_policies[service_name]
        current_replicas = self.current_replicas.get(service_name, policy.min_replicas)

        # Check cooldown period
        if service_name in self.cooldown_end_times:
            if datetime.now(timezone.utc) < self.cooldown_end_times[service_name]:
                return None

        # Get metrics
        cpu_utilization = metrics.get("cpu_utilization", 0)
        memory_utilization = metrics.get("memory_utilization", 0)

        # Scale up conditions
        if (
            cpu_utilization > policy.scale_up_threshold
            or memory_utilization > policy.scale_up_threshold
        ):
            if current_replicas < policy.max_replicas:
                new_replicas = min(current_replicas + 1, policy.max_replicas)
                return await self._apply_scaling(service_name, new_replicas, "scale_up")

        # Scale down conditions
        elif (
            cpu_utilization < policy.scale_down_threshold
            and memory_utilization < policy.scale_down_threshold
        ):
            if current_replicas > policy.min_replicas:
                new_replicas = max(current_replicas - 1, policy.min_replicas)
                return await self._apply_scaling(
                    service_name, new_replicas, "scale_down"
                )

        return None

    async def _apply_scaling(
        self, service_name: str, new_replicas: int, action: str
    ) -> int:
        """Apply scaling action."""

        old_replicas = self.current_replicas.get(service_name, 1)

        try:
            # Simulate scaling operation
            # In production, this would interact with orchestration platform
            await asyncio.sleep(1)  # Simulate scaling delay

            self.current_replicas[service_name] = new_replicas

            # Set cooldown period
            policy = self.scaling_policies[service_name]
            self.cooldown_end_times[service_name] = datetime.now(
                timezone.utc
            ) + timedelta(seconds=policy.cooldown_period)

            # Record scaling event
            scaling_event = {
                "service_name": service_name,
                "action": action,
                "old_replicas": old_replicas,
                "new_replicas": new_replicas,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            self.scaling_history.append(scaling_event)

            logger.info(
                f"Scaled {service_name}: {old_replicas} -> {new_replicas} replicas ({action})"
            )

            return new_replicas

        except Exception as e:
            logger.error(f"Scaling failed for {service_name}: {e}")
            return old_replicas

    def get_scaling_summary(self) -> Dict[str, Any]:
        """Get scaling summary."""

        return {
            "services_with_scaling": len(self.scaling_policies),
            "current_replicas": dict(self.current_replicas),
            "recent_scaling_events": self.scaling_history[-10:],
            "services_in_cooldown": len(self.cooldown_end_times),
            "total_scaling_events": len(self.scaling_history),
        }


class LoadBalancer:
    """Manages load balancing for services."""

    def __init__(self):
        self.service_endpoints: Dict[str, List[str]] = {}
        self.load_balancing_strategy: str = "round_robin"
        self.current_index: Dict[str, int] = {}
        self.endpoint_health: Dict[str, Dict[str, bool]] = {}

    def register_service(self, service_name: str, endpoints: List[str]):
        """Register service endpoints."""
        self.service_endpoints[service_name] = endpoints
        self.current_index[service_name] = 0
        self.endpoint_health[service_name] = {endpoint: True for endpoint in endpoints}

    def get_endpoint(self, service_name: str) -> Optional[str]:
        """Get next endpoint for service."""

        if service_name not in self.service_endpoints:
            return None

        endpoints = self.service_endpoints[service_name]
        healthy_endpoints = [
            ep for ep in endpoints if self.endpoint_health[service_name].get(ep, False)
        ]

        if not healthy_endpoints:
            logger.warning(f"No healthy endpoints for service: {service_name}")
            return None

        # Round-robin load balancing
        if self.load_balancing_strategy == "round_robin":
            current_idx = self.current_index[service_name]
            endpoint = healthy_endpoints[current_idx % len(healthy_endpoints)]
            self.current_index[service_name] = (current_idx + 1) % len(
                healthy_endpoints
            )
            return endpoint

        # For other strategies, return first healthy endpoint
        return healthy_endpoints[0]

    def update_endpoint_health(self, service_name: str, endpoint: str, healthy: bool):
        """Update endpoint health status."""

        if service_name in self.endpoint_health:
            self.endpoint_health[service_name][endpoint] = healthy

    def get_load_balancing_summary(self) -> Dict[str, Any]:
        """Get load balancing summary."""

        return {
            "services_registered": len(self.service_endpoints),
            "total_endpoints": sum(
                len(endpoints) for endpoints in self.service_endpoints.values()
            ),
            "healthy_endpoints": sum(
                sum(1 for healthy in health_status.values() if healthy)
                for health_status in self.endpoint_health.values()
            ),
            "load_balancing_strategy": self.load_balancing_strategy,
            "service_endpoints": dict(self.service_endpoints),
            "endpoint_health": dict(self.endpoint_health),
        }


class BackupManager:
    """Manages backups for production deployment."""

    def __init__(self):
        self.backup_policies: Dict[str, BackupPolicy] = {}
        self.backup_history: List[Dict[str, Any]] = []
        self.backup_tasks: Dict[str, asyncio.Task] = {}

    def add_backup_policy(self, service_name: str, policy: BackupPolicy):
        """Add backup policy for service."""
        self.backup_policies[service_name] = policy

    async def start_backup_scheduler(self):
        """Start backup scheduler."""

        for service_name, policy in self.backup_policies.items():
            if policy.enabled:
                task = asyncio.create_task(self._schedule_backups(service_name, policy))
                self.backup_tasks[service_name] = task

        logger.info("Backup scheduler started")

    async def stop_backup_scheduler(self):
        """Stop backup scheduler."""

        for task in self.backup_tasks.values():
            task.cancel()

        await asyncio.gather(*self.backup_tasks.values(), return_exceptions=True)
        self.backup_tasks.clear()

        logger.info("Backup scheduler stopped")

    async def _schedule_backups(self, service_name: str, policy: BackupPolicy):
        """Schedule backups for service."""

        while True:
            try:
                # Parse schedule (simplified - in production use cron parsing)
                if policy.schedule == "daily":
                    interval = 86400  # 24 hours
                elif policy.schedule == "hourly":
                    interval = 3600  # 1 hour
                else:
                    interval = 86400  # Default to daily

                await asyncio.sleep(interval)

                # Perform backup
                await self._perform_backup(service_name, policy)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Backup scheduling error for {service_name}: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry

    async def _perform_backup(self, service_name: str, policy: BackupPolicy):
        """Perform backup for service."""

        backup_id = f"backup_{service_name}_{int(time.time())}"

        try:
            # Simulate backup operation
            await asyncio.sleep(2)  # Simulate backup time

            # Create backup record
            backup_record = {
                "backup_id": backup_id,
                "service_name": service_name,
                "backup_type": policy.backup_type,
                "storage_location": policy.storage_location,
                "encryption_enabled": policy.encryption_enabled,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "size": 1024 * 1024 * 10,  # Simulate 10MB backup
                "status": "completed",
            }

            self.backup_history.append(backup_record)

            # Clean up old backups
            await self._cleanup_old_backups(service_name, policy)

            logger.info(f"Backup completed for {service_name}: {backup_id}")

        except Exception as e:
            logger.error(f"Backup failed for {service_name}: {e}")

            # Record failed backup
            backup_record = {
                "backup_id": backup_id,
                "service_name": service_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "failed",
                "error": str(e),
            }

            self.backup_history.append(backup_record)

    async def _cleanup_old_backups(self, service_name: str, policy: BackupPolicy):
        """Clean up old backups based on retention policy."""

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=policy.retention_days)

        # Find old backups
        old_backups = [
            backup
            for backup in self.backup_history
            if (
                backup["service_name"] == service_name
                and datetime.fromisoformat(backup["timestamp"]) < cutoff_date
            )
        ]

        # Remove old backups
        for backup in old_backups:
            self.backup_history.remove(backup)
            logger.info(f"Cleaned up old backup: {backup['backup_id']}")

    def get_backup_summary(self) -> Dict[str, Any]:
        """Get backup summary."""

        recent_backups = [
            b
            for b in self.backup_history
            if datetime.fromisoformat(b["timestamp"])
            > datetime.now(timezone.utc) - timedelta(days=7)
        ]

        successful_backups = [b for b in recent_backups if b["status"] == "completed"]
        failed_backups = [b for b in recent_backups if b["status"] == "failed"]

        return {
            "backup_policies": len(self.backup_policies),
            "recent_backups": len(recent_backups),
            "successful_backups": len(successful_backups),
            "failed_backups": len(failed_backups),
            "backup_success_rate": len(successful_backups)
            / max(1, len(recent_backups))
            * 100,
            "total_backup_history": len(self.backup_history),
            "backup_status": {
                service: policy.enabled
                for service, policy in self.backup_policies.items()
            },
        }


class SecurityHardener:
    """Handles security hardening for production deployment."""

    def __init__(self):
        self.security_policies: Dict[str, SecurityPolicy] = {}
        self.security_scans: List[Dict[str, Any]] = []
        self.security_issues: List[Dict[str, Any]] = []

    def add_security_policy(self, service_name: str, policy: SecurityPolicy):
        """Add security policy for service."""
        self.security_policies[service_name] = policy

    async def apply_security_hardening(self, service_name: str) -> Dict[str, Any]:
        """Apply security hardening for service."""

        if service_name not in self.security_policies:
            return {"status": "error", "message": "No security policy found"}

        policy = self.security_policies[service_name]
        hardening_results = []

        # Apply TLS configuration
        if policy.tls_enabled:
            result = await self._configure_tls(service_name, policy)
            hardening_results.append(result)

        # Apply authentication
        if policy.authentication_required:
            result = await self._configure_authentication(service_name, policy)
            hardening_results.append(result)

        # Apply firewall rules
        if policy.firewall_rules:
            result = await self._configure_firewall(service_name, policy)
            hardening_results.append(result)

        # Apply encryption
        if policy.encryption_at_rest:
            result = await self._configure_encryption(service_name, policy)
            hardening_results.append(result)

        # Apply rate limiting
        if policy.rate_limiting:
            result = await self._configure_rate_limiting(service_name, policy)
            hardening_results.append(result)

        return {
            "status": "completed",
            "service_name": service_name,
            "hardening_results": hardening_results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def _configure_tls(
        self, service_name: str, policy: SecurityPolicy
    ) -> Dict[str, Any]:
        """Configure TLS for service."""

        try:
            # Simulate TLS configuration
            await asyncio.sleep(0.5)

            # Generate or use provided certificates
            if policy.certificate_path:
                # Use provided certificate
                cert_source = "provided"
            else:
                # Generate self-signed certificate for development
                cert_source = "generated"

            return {
                "component": "tls",
                "status": "configured",
                "certificate_source": cert_source,
                "tls_version": "1.3",
            }

        except Exception as e:
            return {"component": "tls", "status": "failed", "error": str(e)}

    async def _configure_authentication(
        self, service_name: str, policy: SecurityPolicy
    ) -> Dict[str, Any]:
        """Configure authentication for service."""

        try:
            # Simulate authentication configuration
            await asyncio.sleep(0.3)

            # Integrate with post-quantum crypto
            auth_keys = post_quantum_crypto.generate_dilithium_keypair()

            return {
                "component": "authentication",
                "status": "configured",
                "auth_method": "post_quantum",
                "key_algorithm": auth_keys.algorithm,
            }

        except Exception as e:
            return {"component": "authentication", "status": "failed", "error": str(e)}

    async def _configure_firewall(
        self, service_name: str, policy: SecurityPolicy
    ) -> Dict[str, Any]:
        """Configure firewall for service."""

        try:
            # Simulate firewall configuration
            await asyncio.sleep(0.2)

            rules_applied = len(policy.firewall_rules)

            return {
                "component": "firewall",
                "status": "configured",
                "rules_applied": rules_applied,
                "default_policy": "deny",
            }

        except Exception as e:
            return {"component": "firewall", "status": "failed", "error": str(e)}

    async def _configure_encryption(
        self, service_name: str, policy: SecurityPolicy
    ) -> Dict[str, Any]:
        """Configure encryption for service."""

        try:
            # Simulate encryption configuration
            await asyncio.sleep(0.4)

            # Use zero-knowledge system for privacy
            zk_proof = zk_system.generate_system_proof()

            return {
                "component": "encryption",
                "status": "configured",
                "encryption_at_rest": policy.encryption_at_rest,
                "encryption_in_transit": policy.encryption_in_transit,
                "zk_privacy": True,
            }

        except Exception as e:
            return {"component": "encryption", "status": "failed", "error": str(e)}

    async def _configure_rate_limiting(
        self, service_name: str, policy: SecurityPolicy
    ) -> Dict[str, Any]:
        """Configure rate limiting for service."""

        try:
            # Simulate rate limiting configuration
            await asyncio.sleep(0.2)

            return {
                "component": "rate_limiting",
                "status": "configured",
                "rate_limit": policy.rate_limiting,
                "enforcement": "enabled",
            }

        except Exception as e:
            return {"component": "rate_limiting", "status": "failed", "error": str(e)}

    async def perform_security_scan(self, service_name: str) -> Dict[str, Any]:
        """Perform security scan for service."""

        scan_id = f"scan_{service_name}_{int(time.time())}"

        try:
            # Simulate security scan
            await asyncio.sleep(2)

            # Simulate scan results
            vulnerabilities = []

            # Simulate finding some issues
            import random

            if random.random() < 0.3:  # 30% chance of finding issues
                vulnerabilities.append(
                    {
                        "type": "configuration",
                        "severity": "medium",
                        "description": "Weak cipher configuration detected",
                        "recommendation": "Update to stronger cipher suite",
                    }
                )

            if random.random() < 0.1:  # 10% chance of critical issue
                vulnerabilities.append(
                    {
                        "type": "access_control",
                        "severity": "high",
                        "description": "Overly permissive access controls",
                        "recommendation": "Implement principle of least privilege",
                    }
                )

            scan_result = {
                "scan_id": scan_id,
                "service_name": service_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "vulnerabilities": vulnerabilities,
                "security_score": 90 - (len(vulnerabilities) * 10),
                "status": "completed",
            }

            self.security_scans.append(scan_result)

            # Add to security issues if vulnerabilities found
            for vuln in vulnerabilities:
                issue = {
                    "scan_id": scan_id,
                    "service_name": service_name,
                    "issue": vuln,
                    "status": "open",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                self.security_issues.append(issue)

            return scan_result

        except Exception as e:
            return {
                "scan_id": scan_id,
                "service_name": service_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "failed",
                "error": str(e),
            }

    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary."""

        recent_scans = [
            s
            for s in self.security_scans
            if datetime.fromisoformat(s["timestamp"])
            > datetime.now(timezone.utc) - timedelta(days=7)
        ]

        open_issues = [i for i in self.security_issues if i["status"] == "open"]
        critical_issues = [i for i in open_issues if i["issue"]["severity"] == "high"]

        return {
            "security_policies": len(self.security_policies),
            "recent_scans": len(recent_scans),
            "open_security_issues": len(open_issues),
            "critical_issues": len(critical_issues),
            "average_security_score": sum(
                s.get("security_score", 0) for s in recent_scans
            )
            / max(1, len(recent_scans)),
            "services_with_hardening": list(self.security_policies.keys()),
            "security_status": "secure"
            if len(critical_issues) == 0
            else "needs_attention",
        }


class ServiceOrchestrator:
    """Orchestrates deployment of services."""

    def __init__(self):
        self.services: Dict[str, ServiceConfig] = {}
        self.service_status: Dict[str, DeploymentStatus] = {}
        self.deployment_order: List[str] = []

    def add_service(self, service_config: ServiceConfig):
        """Add service to orchestrator."""
        self.services[service_config.service_name] = service_config
        self.service_status[service_config.service_name] = DeploymentStatus.PENDING

    def calculate_deployment_order(self) -> List[str]:
        """Calculate deployment order based on dependencies."""

        # Simple topological sort
        visited = set()
        temp_visited = set()
        order = []

        def visit(service_name: str):
            if service_name in temp_visited:
                raise ValueError(
                    f"Circular dependency detected involving {service_name}"
                )
            if service_name in visited:
                return

            temp_visited.add(service_name)

            # Visit dependencies first
            service = self.services.get(service_name)
            if service:
                for dep in service.dependencies:
                    if dep in self.services:
                        visit(dep)

            temp_visited.remove(service_name)
            visited.add(service_name)
            order.append(service_name)

        # Visit all services
        for service_name in self.services:
            if service_name not in visited:
                visit(service_name)

        self.deployment_order = order
        return order

    async def deploy_service(self, service_name: str) -> bool:
        """Deploy a specific service."""

        if service_name not in self.services:
            logger.error(f"Service not found: {service_name}")
            return False

        service = self.services[service_name]

        try:
            self.service_status[service_name] = DeploymentStatus.DEPLOYING

            # Check dependencies
            for dep in service.dependencies:
                if dep in self.service_status:
                    if self.service_status[dep] != DeploymentStatus.DEPLOYED:
                        logger.error(
                            f"Dependency {dep} not deployed for {service_name}"
                        )
                        self.service_status[service_name] = DeploymentStatus.FAILED
                        return False

            # Simulate deployment
            await asyncio.sleep(1)  # Simulate deployment time

            self.service_status[service_name] = DeploymentStatus.DEPLOYED
            logger.info(f"Service deployed successfully: {service_name}")

            return True

        except Exception as e:
            logger.error(f"Service deployment failed for {service_name}: {e}")
            self.service_status[service_name] = DeploymentStatus.FAILED
            return False

    async def deploy_all_services(self) -> Dict[str, bool]:
        """Deploy all services in dependency order."""

        deployment_order = self.calculate_deployment_order()
        results = {}

        for service_name in deployment_order:
            result = await self.deploy_service(service_name)
            results[service_name] = result

            if not result:
                logger.error(
                    f"Deployment failed for {service_name}, stopping deployment"
                )
                break

        return results

    def get_deployment_status(self) -> Dict[str, Any]:
        """Get deployment status for all services."""

        return {
            "services": len(self.services),
            "deployed_services": sum(
                1
                for status in self.service_status.values()
                if status == DeploymentStatus.DEPLOYED
            ),
            "failed_services": sum(
                1
                for status in self.service_status.values()
                if status == DeploymentStatus.FAILED
            ),
            "pending_services": sum(
                1
                for status in self.service_status.values()
                if status == DeploymentStatus.PENDING
            ),
            "deployment_order": self.deployment_order,
            "service_status": {
                name: status.value for name, status in self.service_status.items()
            },
        }


class DeploymentManager:
    """Main deployment manager."""

    def __init__(self):
        self.orchestrator = ServiceOrchestrator()
        self.health_monitor = HealthMonitor()
        self.auto_scaler = AutoScaler(self.health_monitor)
        self.load_balancer = LoadBalancer()
        self.backup_manager = BackupManager()
        self.security_hardener = SecurityHardener()
        self.db_migrator = DatabaseMigrator()
        self.deployment_history: List[DeploymentResult] = []

    async def deploy(self, config: DeploymentConfig) -> DeploymentResult:
        """Deploy using configuration."""

        deployment_id = f"deployment_{int(time.time())}"
        start_time = datetime.now(timezone.utc)

        try:
            # Apply database migrations
            migrations_applied = await self.db_migrator.apply_migrations()

            # Deploy services
            deployment_results = await self.orchestrator.deploy_all_services()

            # Start health monitoring
            for service_name in self.orchestrator.services:
                health_check = self._create_default_health_check(service_name)
                self.health_monitor.add_health_check(service_name, health_check)
                await self.health_monitor.start_monitoring(service_name)

            # Configure auto-scaling
            for service_name in self.orchestrator.services:
                scaling_policy = self._create_default_scaling_policy()
                self.auto_scaler.add_scaling_policy(service_name, scaling_policy)

            # Configure load balancing
            for service_name in self.orchestrator.services:
                endpoints = [
                    f"http://localhost:800{i}" for i in range(3)
                ]  # Mock endpoints
                self.load_balancer.register_service(service_name, endpoints)

            # Apply security hardening
            for service_name in self.orchestrator.services:
                security_policy = self._create_default_security_policy()
                self.security_hardener.add_security_policy(
                    service_name, security_policy
                )
                await self.security_hardener.apply_security_hardening(service_name)

            # Configure backups
            for service_name in self.orchestrator.services:
                backup_policy = self._create_default_backup_policy()
                self.backup_manager.add_backup_policy(service_name, backup_policy)

            # Start backup scheduler
            await self.backup_manager.start_backup_scheduler()

            # Start performance monitoring integration
            await performance_layer.start_optimization_layer()

            # Determine deployment success
            successful_services = sum(
                1 for success in deployment_results.values() if success
            )
            total_services = len(deployment_results)

            deployment_success = successful_services == total_services

            # Create deployment result
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            result = DeploymentResult(
                deployment_id=deployment_id,
                status=DeploymentStatus.DEPLOYED
                if deployment_success
                else DeploymentStatus.FAILED,
                message=f"Deployed {successful_services}/{total_services} services successfully",
                timestamp=end_time,
                duration=duration,
                services_deployed=list(deployment_results.keys()),
                rollback_available=True,
                health_checks_passed=deployment_success,
                metadata={
                    "environment": config.environment.value,
                    "version": config.version,
                    "migrations_applied": migrations_applied,
                    "deployment_results": deployment_results,
                },
            )

            # Record deployment
            self.deployment_history.append(result)
            self.db_migrator.record_deployment(result)

            # Emit audit event
            audit_emitter.emit_capsule_created(
                capsule_id=deployment_id,
                agent_id="deployment_manager",
                capsule_type="deployment",
            )

            logger.info(f"Deployment {deployment_id} completed: {result.message}")

            return result

        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            result = DeploymentResult(
                deployment_id=deployment_id,
                status=DeploymentStatus.FAILED,
                message=f"Deployment failed: {str(e)}",
                timestamp=end_time,
                duration=duration,
                services_deployed=[],
                rollback_available=False,
                health_checks_passed=False,
                metadata={"error": str(e)},
            )

            self.deployment_history.append(result)
            logger.error(f"Deployment {deployment_id} failed: {e}")

            return result

    def _create_default_health_check(self, service_name: str) -> HealthCheck:
        """Create default health check for service."""
        return HealthCheck(
            endpoint="/health",
            method="GET",
            expected_status=200,
            timeout=30,
            interval=30,
            retries=3,
        )

    def _create_default_scaling_policy(self) -> ScalingPolicy:
        """Create default scaling policy."""
        return ScalingPolicy(
            min_replicas=1,
            max_replicas=10,
            target_cpu_utilization=70.0,
            target_memory_utilization=80.0,
            scale_up_threshold=85.0,
            scale_down_threshold=30.0,
            cooldown_period=300,
        )

    def _create_default_security_policy(self) -> SecurityPolicy:
        """Create default security policy."""
        return SecurityPolicy(
            tls_enabled=True,
            certificate_path="",
            authentication_required=True,
            authorization_enabled=True,
            rate_limiting={"requests_per_minute": 100},
            firewall_rules=[
                {"action": "allow", "port": 80},
                {"action": "allow", "port": 443},
            ],
            encryption_at_rest=True,
            encryption_in_transit=True,
        )

    def _create_default_backup_policy(self) -> BackupPolicy:
        """Create default backup policy."""
        return BackupPolicy(
            enabled=True,
            schedule="daily",
            retention_days=30,
            backup_type="incremental",
            storage_location="/backups",
            encryption_enabled=True,
        )

    async def rollback_deployment(self, deployment_id: str) -> bool:
        """Rollback a deployment."""

        try:
            # Find deployment
            deployment = next(
                (
                    d
                    for d in self.deployment_history
                    if d.deployment_id == deployment_id
                ),
                None,
            )

            if not deployment:
                logger.error(f"Deployment not found: {deployment_id}")
                return False

            if not deployment.rollback_available:
                logger.error(f"Rollback not available for deployment: {deployment_id}")
                return False

            # Simulate rollback
            await asyncio.sleep(2)

            # Update deployment status
            deployment.status = DeploymentStatus.ROLLED_BACK

            logger.info(f"Deployment {deployment_id} rolled back successfully")
            return True

        except Exception as e:
            logger.error(f"Rollback failed for deployment {deployment_id}: {e}")
            return False

    def get_deployment_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive deployment dashboard."""

        return {
            "deployment_summary": {
                "total_deployments": len(self.deployment_history),
                "successful_deployments": sum(
                    1
                    for d in self.deployment_history
                    if d.status == DeploymentStatus.DEPLOYED
                ),
                "failed_deployments": sum(
                    1
                    for d in self.deployment_history
                    if d.status == DeploymentStatus.FAILED
                ),
                "recent_deployments": [
                    d.to_dict() for d in self.deployment_history[-5:]
                ],
            },
            "service_orchestration": self.orchestrator.get_deployment_status(),
            "health_monitoring": self.health_monitor.get_health_summary(),
            "auto_scaling": self.auto_scaler.get_scaling_summary(),
            "load_balancing": self.load_balancer.get_load_balancing_summary(),
            "backup_management": self.backup_manager.get_backup_summary(),
            "security_hardening": self.security_hardener.get_security_summary(),
            "database_migrations": {
                "migrations_applied": len(self.db_migrator.migrations_applied),
                "deployment_history": len(self.db_migrator.get_deployment_history()),
            },
        }


class ProductionDeploymentSystem:
    """Main production deployment system."""

    def __init__(self):
        self.deployment_manager = DeploymentManager()
        self.default_configs = self._initialize_default_configs()
        self.system_initialized = False

    async def initialize_system(self):
        """Initialize the production deployment system."""

        if self.system_initialized:
            return

        # Initialize default services
        await self._initialize_default_services()

        # Set up alert callbacks
        self._setup_alert_callbacks()

        self.system_initialized = True
        logger.info("Production deployment system initialized")

    async def _initialize_default_services(self):
        """Initialize default services for UATP system."""

        # API Server
        api_service = ServiceConfig(
            service_name="uatp-api",
            service_type=ServiceType.API_SERVER,
            image="uatp-api:latest",
            ports=[8000],
            environment={"ENVIRONMENT": "production", "LOG_LEVEL": "INFO"},
            volumes=["/app/data:/data"],
            dependencies=[],
            health_check={"endpoint": "/health", "timeout": 30},
            resources={"cpu": "1000m", "memory": "2Gi"},
        )

        # Worker Service
        worker_service = ServiceConfig(
            service_name="uatp-worker",
            service_type=ServiceType.WORKER,
            image="uatp-worker:latest",
            ports=[],
            environment={"ENVIRONMENT": "production", "WORKER_CONCURRENCY": "10"},
            volumes=["/app/data:/data"],
            dependencies=["uatp-api"],
            health_check={"endpoint": "/worker/health", "timeout": 30},
            resources={"cpu": "500m", "memory": "1Gi"},
        )

        # Database Service
        db_service = ServiceConfig(
            service_name="uatp-database",
            service_type=ServiceType.DATABASE,
            image="postgres:14",
            ports=[5432],
            environment={
                "POSTGRES_DB": "uatp",
                "POSTGRES_USER": "uatp",
                "POSTGRES_PASSWORD": "secure_password",
            },
            volumes=["/var/lib/postgresql/data:/var/lib/postgresql/data"],
            dependencies=[],
            health_check={"endpoint": "/", "timeout": 30},
            resources={"cpu": "2000m", "memory": "4Gi"},
        )

        # Cache Service
        cache_service = ServiceConfig(
            service_name="uatp-cache",
            service_type=ServiceType.CACHE,
            image="redis:7",
            ports=[6379],
            environment={},
            volumes=["/data:/data"],
            dependencies=[],
            health_check={"endpoint": "/", "timeout": 30},
            resources={"cpu": "500m", "memory": "1Gi"},
        )

        # Add services to orchestrator
        self.deployment_manager.orchestrator.add_service(api_service)
        self.deployment_manager.orchestrator.add_service(worker_service)
        self.deployment_manager.orchestrator.add_service(db_service)
        self.deployment_manager.orchestrator.add_service(cache_service)

    def _setup_alert_callbacks(self):
        """Set up alert callbacks for health monitoring."""

        async def health_alert_callback(alert_data: Dict[str, Any]):
            """Handle health alerts."""
            logger.warning(f"Health alert: {alert_data}")

            # In production, this would send alerts to monitoring systems
            # For now, we'll just log the alert

            # Emit audit event
            audit_emitter.emit_capsule_created(
                capsule_id=f"health_alert_{int(time.time())}",
                agent_id="health_monitor",
                capsule_type="health_alert",
            )

        self.deployment_manager.health_monitor.add_alert_callback(health_alert_callback)

    def _initialize_default_configs(self) -> Dict[str, DeploymentConfig]:
        """Initialize default deployment configurations."""

        production_config = DeploymentConfig(
            environment=DeploymentStage.PRODUCTION,
            version="1.0.0",
            replicas=3,
            resources={"cpu": "2000m", "memory": "4Gi"},
            environment_variables={
                "ENVIRONMENT": "production",
                "LOG_LEVEL": "INFO",
                "DATABASE_URL": "postgresql://uatp:secure_password@uatp-database:5432/uatp",
                "REDIS_URL": "redis://uatp-cache:6379",
            },
            secrets={"JWT_SECRET": secrets.token_urlsafe(32)},
            health_check={
                "endpoint": "/health",
                "timeout": 30,
                "interval": 30,
                "retries": 3,
            },
            scaling_policy={
                "min_replicas": 2,
                "max_replicas": 10,
                "target_cpu_utilization": 70.0,
            },
            backup_policy={"enabled": True, "schedule": "daily", "retention_days": 30},
            security_policy={
                "tls_enabled": True,
                "authentication_required": True,
                "rate_limiting": {"requests_per_minute": 1000},
            },
            networking={"load_balancer": True, "ssl_termination": True},
            storage={"persistent_volume": True, "storage_class": "ssd"},
        )

        staging_config = DeploymentConfig(
            environment=DeploymentStage.STAGING,
            version="1.0.0-staging",
            replicas=1,
            resources={"cpu": "500m", "memory": "1Gi"},
            environment_variables={
                "ENVIRONMENT": "staging",
                "LOG_LEVEL": "DEBUG",
                "DATABASE_URL": "postgresql://uatp:password@uatp-database:5432/uatp_staging",
            },
            secrets={"JWT_SECRET": secrets.token_urlsafe(32)},
            health_check={
                "endpoint": "/health",
                "timeout": 30,
                "interval": 60,
                "retries": 2,
            },
            scaling_policy={
                "min_replicas": 1,
                "max_replicas": 3,
                "target_cpu_utilization": 80.0,
            },
            backup_policy={"enabled": True, "schedule": "daily", "retention_days": 7},
            security_policy={
                "tls_enabled": False,
                "authentication_required": False,
                "rate_limiting": {"requests_per_minute": 100},
            },
            networking={"load_balancer": False, "ssl_termination": False},
            storage={"persistent_volume": False, "storage_class": "standard"},
        )

        return {"production": production_config, "staging": staging_config}

    async def deploy_to_production(self, version: str = "latest") -> DeploymentResult:
        """Deploy to production environment."""

        await self.initialize_system()

        config = self.default_configs["production"]
        config.version = version

        return await self.deployment_manager.deploy(config)

    async def deploy_to_staging(self, version: str = "latest") -> DeploymentResult:
        """Deploy to staging environment."""

        await self.initialize_system()

        config = self.default_configs["staging"]
        config.version = version

        return await self.deployment_manager.deploy(config)

    async def deploy_with_config(self, config: DeploymentConfig) -> DeploymentResult:
        """Deploy with custom configuration."""

        await self.initialize_system()

        return await self.deployment_manager.deploy(config)

    async def rollback_deployment(self, deployment_id: str) -> bool:
        """Rollback a deployment."""

        return await self.deployment_manager.rollback_deployment(deployment_id)

    def get_system_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive system dashboard."""

        dashboard = self.deployment_manager.get_deployment_dashboard()

        # Add system-wide metrics
        dashboard["system_overview"] = {
            "system_initialized": self.system_initialized,
            "available_environments": list(self.default_configs.keys()),
            "deployment_system_version": "1.0.0",
            "uptime": "N/A",  # Would track actual uptime in production
            "system_health": "operational",
        }

        return dashboard

    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform system-wide health check."""

        health_summary = self.deployment_manager.health_monitor.get_health_summary()

        return {
            "system_health": "healthy"
            if health_summary["overall_health"] == "healthy"
            else "unhealthy",
            "components": health_summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks_performed": len(health_summary["service_status"]),
        }

    async def shutdown_system(self):
        """Gracefully shutdown the deployment system."""

        logger.info("Shutting down production deployment system...")

        # Stop backup scheduler
        await self.deployment_manager.backup_manager.stop_backup_scheduler()

        # Stop health monitoring
        for service_name in list(
            self.deployment_manager.health_monitor.monitoring_tasks.keys()
        ):
            await self.deployment_manager.health_monitor.stop_monitoring(service_name)

        # Stop performance layer
        await performance_layer.stop_optimization_layer()

        self.system_initialized = False
        logger.info("Production deployment system shutdown completed")


# Global deployment system instance
deployment_system = ProductionDeploymentSystem()
