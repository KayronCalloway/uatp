"""
ML Pipeline Metrics Monitoring
==============================

Monitors the health of the ML training pipeline:
- Embedding coverage (what % of capsules have embeddings)
- Outcome tracking (what % have outcomes recorded)
- Export endpoint health
- Data quality alerts

Usage:
    from src.monitoring.ml_metrics import MLMetricsMonitor

    monitor = MLMetricsMonitor()
    health = await monitor.check_health()

    if health["alerts"]:
        for alert in health["alerts"]:
            logger.warning(f"ML Alert: {alert}")
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select

logger = logging.getLogger(__name__)


@dataclass
class MLHealthAlert:
    """Represents an ML pipeline health alert."""

    severity: str  # "critical", "warning", "info"
    metric: str
    message: str
    current_value: float
    threshold: float
    timestamp: datetime


class MLMetricsMonitor:
    """
    Monitors ML pipeline health metrics.

    Thresholds are configurable - these are sensible defaults:
    - Embedding coverage: warn < 50%, critical < 20%
    - Outcome coverage: warn < 10% (outcomes take time to accumulate)
    - Export success: critical if any failures
    """

    def __init__(
        self,
        embedding_warn_threshold: float = 0.5,
        embedding_critical_threshold: float = 0.2,
        outcome_warn_threshold: float = 0.1,
        min_capsules_for_alerts: int = 50,
    ):
        self.embedding_warn_threshold = embedding_warn_threshold
        self.embedding_critical_threshold = embedding_critical_threshold
        self.outcome_warn_threshold = outcome_warn_threshold
        self.min_capsules_for_alerts = min_capsules_for_alerts

    async def get_metrics(self, session) -> Dict[str, Any]:
        """
        Get current ML pipeline metrics.

        Returns:
            Dict with metrics including:
            - total_capsules
            - with_embeddings (count and percentage)
            - with_outcomes (count and percentage)
            - outcome_breakdown (success/failure/partial counts)
        """
        from src.models.capsule import CapsuleModel

        # Total capsules (excluding demo)
        total_query = select(func.count(CapsuleModel.id)).where(
            ~CapsuleModel.capsule_id.like("demo-%")
        )
        total_result = await session.execute(total_query)
        total = total_result.scalar() or 0

        # With embeddings
        embedding_query = select(func.count(CapsuleModel.id)).where(
            and_(
                CapsuleModel.embedding.isnot(None),
                ~CapsuleModel.capsule_id.like("demo-%"),
            )
        )
        embedding_result = await session.execute(embedding_query)
        with_embeddings = embedding_result.scalar() or 0

        # With outcomes
        outcome_query = select(func.count(CapsuleModel.id)).where(
            and_(
                CapsuleModel.outcome_status.isnot(None),
                ~CapsuleModel.capsule_id.like("demo-%"),
            )
        )
        outcome_result = await session.execute(outcome_query)
        with_outcomes = outcome_result.scalar() or 0

        # Outcome breakdown
        outcome_breakdown = {}
        for status in ["success", "failure", "partial"]:
            status_query = select(func.count(CapsuleModel.id)).where(
                and_(
                    CapsuleModel.outcome_status == status,
                    ~CapsuleModel.capsule_id.like("demo-%"),
                )
            )
            status_result = await session.execute(status_query)
            outcome_breakdown[status] = status_result.scalar() or 0

        # Calculate percentages
        embedding_pct = (with_embeddings / total * 100) if total > 0 else 0
        outcome_pct = (with_outcomes / total * 100) if total > 0 else 0

        return {
            "total_capsules": total,
            "with_embeddings": with_embeddings,
            "embedding_coverage_pct": round(embedding_pct, 1),
            "with_outcomes": with_outcomes,
            "outcome_coverage_pct": round(outcome_pct, 1),
            "outcome_breakdown": outcome_breakdown,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def check_health(self, session) -> Dict[str, Any]:
        """
        Check ML pipeline health and return any alerts.

        Returns:
            Dict with:
            - metrics: current metrics
            - alerts: list of MLHealthAlert objects
            - status: "healthy", "warning", or "critical"
        """
        metrics = await self.get_metrics(session)
        alerts: List[MLHealthAlert] = []
        now = datetime.now(timezone.utc)

        # Only alert if we have enough data
        if metrics["total_capsules"] >= self.min_capsules_for_alerts:
            # Check embedding coverage
            embedding_ratio = metrics["with_embeddings"] / metrics["total_capsules"]

            if embedding_ratio < self.embedding_critical_threshold:
                alerts.append(
                    MLHealthAlert(
                        severity="critical",
                        metric="embedding_coverage",
                        message=f"Embedding coverage critically low: {metrics['embedding_coverage_pct']}%",
                        current_value=embedding_ratio,
                        threshold=self.embedding_critical_threshold,
                        timestamp=now,
                    )
                )
            elif embedding_ratio < self.embedding_warn_threshold:
                alerts.append(
                    MLHealthAlert(
                        severity="warning",
                        metric="embedding_coverage",
                        message=f"Embedding coverage below target: {metrics['embedding_coverage_pct']}%",
                        current_value=embedding_ratio,
                        threshold=self.embedding_warn_threshold,
                        timestamp=now,
                    )
                )

            # Check outcome coverage (0% is always a problem after enough capsules)
            if metrics["with_outcomes"] == 0:
                alerts.append(
                    MLHealthAlert(
                        severity="critical",
                        metric="outcome_coverage",
                        message=f"No outcomes recorded despite {metrics['total_capsules']} capsules - check outcome inference",
                        current_value=0,
                        threshold=self.outcome_warn_threshold,
                        timestamp=now,
                    )
                )
            elif metrics["outcome_coverage_pct"] < self.outcome_warn_threshold * 100:
                alerts.append(
                    MLHealthAlert(
                        severity="warning",
                        metric="outcome_coverage",
                        message=f"Outcome coverage low: {metrics['outcome_coverage_pct']}%",
                        current_value=metrics["outcome_coverage_pct"] / 100,
                        threshold=self.outcome_warn_threshold,
                        timestamp=now,
                    )
                )

        # Determine overall status
        if any(a.severity == "critical" for a in alerts):
            status = "critical"
        elif any(a.severity == "warning" for a in alerts):
            status = "warning"
        else:
            status = "healthy"

        return {
            "metrics": metrics,
            "alerts": [
                {
                    "severity": a.severity,
                    "metric": a.metric,
                    "message": a.message,
                    "current_value": a.current_value,
                    "threshold": a.threshold,
                }
                for a in alerts
            ],
            "status": status,
            "checked_at": now.isoformat(),
        }

    async def log_health_status(self, session) -> None:
        """Log current health status to logger."""
        health = await self.check_health(session)

        if health["status"] == "healthy":
            logger.info(
                f"ML Pipeline healthy: {health['metrics']['total_capsules']} capsules, "
                f"{health['metrics']['embedding_coverage_pct']}% embedded, "
                f"{health['metrics']['outcome_coverage_pct']}% with outcomes"
            )
        else:
            for alert in health["alerts"]:
                if alert["severity"] == "critical":
                    logger.error(f"ML CRITICAL: {alert['message']}")
                else:
                    logger.warning(f"ML WARNING: {alert['message']}")


# Singleton instance
_monitor: Optional[MLMetricsMonitor] = None


def get_ml_monitor() -> MLMetricsMonitor:
    """Get singleton MLMetricsMonitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = MLMetricsMonitor()
    return _monitor
