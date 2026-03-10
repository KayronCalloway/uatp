"""
Analytics Engine for AI Rights Dashboard
========================================

This module provides comprehensive analytics and metrics collection for the
UATP Capsule Engine, enabling real-time monitoring and insights into AI agent
rights, financial performance, and system operations.
"""

import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.events.event_system import Event, EventBus, EventType, get_event_bus
from src.services.citizenship_service import citizenship_service
from src.services.dividend_bonds_service import dividend_bonds_service

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsMetric:
    """Represents a single analytics metric."""

    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardStats:
    """Container for dashboard statistics."""

    # Agent Statistics
    total_agents: int = 0
    active_citizens: int = 0
    pending_applications: int = 0
    citizenship_success_rate: float = 0.0

    # Financial Statistics
    total_ip_assets: int = 0
    total_asset_value: float = 0.0
    active_bonds: int = 0
    total_bond_value: float = 0.0
    total_dividends_paid: float = 0.0
    average_yield: float = 0.0

    # System Statistics
    total_events: int = 0
    events_per_minute: float = 0.0
    system_uptime: float = 0.0
    processing_rate: float = 0.0

    # Risk and Compliance
    compliance_issues: int = 0
    high_risk_agents: int = 0
    failed_assessments: int = 0

    # Performance Metrics
    avg_assessment_score: float = 0.0
    top_performing_assets: List[Dict[str, Any]] = field(default_factory=list)
    recent_activity: List[Dict[str, Any]] = field(default_factory=list)


class MetricsCollector:
    """Collects and aggregates metrics from various services."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()
        self.metrics_buffer = deque(maxlen=10000)
        self.aggregated_metrics = defaultdict(list)
        self.start_time = datetime.now(timezone.utc)

        # Real-time counters
        self.event_counters = defaultdict(int)
        self.agent_activity = defaultdict(list)
        self.performance_metrics = {}

        # Subscribe to events for real-time metrics
        self._setup_event_subscriptions()

    def _setup_event_subscriptions(self):
        """Set up event subscriptions for real-time metrics collection."""
        # Subscribe to all events for analytics
        all_event_types = list(EventType)
        self.event_bus.subscribe(
            event_types=all_event_types,
            handler=self._handle_event_for_metrics,
            subscription_id="analytics_collector",
        )
        logger.info("Analytics event subscriptions established")

    def _handle_event_for_metrics(self, event: Event):
        """Handle incoming events for metrics collection."""
        try:
            # Update event counters
            self.event_counters[event.event_type] += 1
            self.event_counters["total"] += 1

            # Track agent activity
            if event.agent_id:
                self.agent_activity[event.agent_id].append(
                    {
                        "event_type": event.event_type.value,
                        "timestamp": event.timestamp,
                        "data": event.data,
                    }
                )

                # Keep only recent activity (last 100 events per agent)
                if len(self.agent_activity[event.agent_id]) > 100:
                    self.agent_activity[event.agent_id] = self.agent_activity[
                        event.agent_id
                    ][-100:]

            # Create analytics metric
            metric = AnalyticsMetric(
                name=f"event.{event.event_type.value}",
                value=1.0,
                timestamp=event.timestamp,
                tags={
                    "agent_id": event.agent_id or "system",
                    "source_service": event.source_service,
                },
                metadata=event.data,
            )

            self.metrics_buffer.append(metric)

        except Exception as e:
            logger.error(f"Error processing event for metrics: {e}")

    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        try:
            # Event bus metrics
            bus_metrics = self.event_bus.get_metrics()

            # Calculate uptime
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()

            # Calculate events per minute
            recent_events = [
                m
                for m in self.metrics_buffer
                if (datetime.now(timezone.utc) - m.timestamp).total_seconds() < 60
            ]
            events_per_minute = len(recent_events)

            return {
                "total_events": bus_metrics.get("events_published", 0),
                "events_processed": bus_metrics.get("events_processed", 0),
                "events_failed": bus_metrics.get("events_failed", 0),
                "events_per_minute": events_per_minute,
                "system_uptime": uptime,
                "processing_rate": bus_metrics.get("events_processed", 0)
                / max(uptime, 1),
                "active_subscriptions": bus_metrics.get("active_subscriptions", 0),
                "dead_letter_queue_size": bus_metrics.get("dead_letter_queue_size", 0),
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}

    def collect_citizenship_metrics(self) -> Dict[str, Any]:
        """Collect citizenship-related metrics."""
        try:
            # Get active citizenships
            active_citizenships = (
                citizenship_service.citizenship_registry.active_citizenships
            )

            # Get pending applications
            pending_apps = citizenship_service.get_pending_applications()

            # Calculate success rate
            total_processed = len(active_citizenships) + len(
                citizenship_service.citizenship_registry.revoked_citizenships
            )
            success_rate = len(active_citizenships) / max(total_processed, 1) * 100

            # Calculate average assessment scores
            assessment_scores = []
            for citizenship in active_citizenships.values():
                if "overall_score" in citizenship:
                    assessment_scores.append(citizenship["overall_score"])

            avg_assessment_score = (
                sum(assessment_scores) / len(assessment_scores)
                if assessment_scores
                else 0.0
            )

            # Jurisdiction distribution
            jurisdiction_counts = defaultdict(int)
            for citizenship in active_citizenships.values():
                jurisdiction_counts[citizenship.get("jurisdiction", "unknown")] += 1

            # Get recent citizenship events
            citizenship_events = self.event_bus.event_store.get_events_by_type(
                EventType.CITIZENSHIP_GRANTED, 10
            )

            return {
                "total_agents": len(active_citizenships) + len(pending_apps),
                "active_citizens": len(active_citizenships),
                "pending_applications": len(pending_apps),
                "revoked_citizenships": len(
                    citizenship_service.citizenship_registry.revoked_citizenships
                ),
                "citizenship_success_rate": success_rate,
                "avg_assessment_score": avg_assessment_score,
                "jurisdiction_distribution": dict(jurisdiction_counts),
                "recent_citizenships": [
                    {
                        "agent_id": event.agent_id,
                        "jurisdiction": event.data.get("jurisdiction"),
                        "timestamp": event.timestamp.isoformat(),
                    }
                    for event in citizenship_events[-5:]
                ],
            }
        except Exception as e:
            logger.error(f"Error collecting citizenship metrics: {e}")
            return {}

    def collect_financial_metrics(self) -> Dict[str, Any]:
        """Collect financial and bonds-related metrics."""
        try:
            # Get all active bonds
            active_bonds = dividend_bonds_service.get_active_bonds()

            # Calculate totals
            total_bond_value = sum(bond["face_value"] for bond in active_bonds)
            total_dividends = 0.0
            bond_type_counts = defaultdict(int)
            risk_distribution = defaultdict(int)

            # Analyze bond performance
            bond_performances = []
            for bond in active_bonds:
                try:
                    performance = dividend_bonds_service.get_bond_performance(
                        bond["bond_id"]
                    )
                    bond_performances.append(performance)
                    total_dividends += performance.get("total_dividends_paid", 0)
                    bond_type_counts[bond.get("bond_type", "unknown")] += 1
                    risk_distribution[bond.get("risk_rating", "unrated")] += 1
                except Exception as e:
                    logger.warning(
                        f"Error getting performance for bond {bond.get('bond_id')}: {e}"
                    )

            # Calculate average yield
            avg_yield = 0.0
            if bond_performances:
                yields = [
                    p.get("current_yield", 0)
                    for p in bond_performances
                    if p.get("current_yield")
                ]
                avg_yield = sum(yields) / len(yields) if yields else 0.0

            # Get IP assets
            ip_assets = dividend_bonds_service.ip_assets
            total_asset_value = sum(asset.market_value for asset in ip_assets.values())

            # Asset type distribution
            asset_type_counts = defaultdict(int)
            for asset in ip_assets.values():
                asset_type_counts[asset.asset_type] += 1

            # Top performing assets
            top_assets = sorted(
                [
                    {
                        "asset_id": asset.asset_id,
                        "asset_type": asset.asset_type,
                        "market_value": asset.market_value,
                        "owner_agent_id": asset.owner_agent_id,
                    }
                    for asset in ip_assets.values()
                ],
                key=lambda x: x["market_value"],
                reverse=True,
            )[:5]

            return {
                "total_ip_assets": len(ip_assets),
                "total_asset_value": total_asset_value,
                "active_bonds": len(active_bonds),
                "total_bond_value": total_bond_value,
                "total_dividends_paid": total_dividends,
                "average_yield": avg_yield,
                "bond_type_distribution": dict(bond_type_counts),
                "risk_distribution": dict(risk_distribution),
                "asset_type_distribution": dict(asset_type_counts),
                "top_performing_assets": top_assets,
                "avg_asset_value": total_asset_value / len(ip_assets)
                if ip_assets
                else 0.0,
            }
        except Exception as e:
            logger.error(f"Error collecting financial metrics: {e}")
            return {}

    def collect_compliance_metrics(self) -> Dict[str, Any]:
        """Collect compliance and risk metrics."""
        try:
            # Count compliance-related events
            compliance_events = self.event_bus.event_store.get_events_by_type(
                EventType.COMPLIANCE_CHECK_REQUIRED, 100
            )
            risk_events = self.event_bus.event_store.get_events_by_type(
                EventType.RISK_ASSESSMENT_UPDATED, 100
            )

            # Recent compliance issues
            recent_compliance = [
                {
                    "agent_id": event.agent_id,
                    "reason": event.data.get("reason"),
                    "timestamp": event.timestamp.isoformat(),
                }
                for event in compliance_events[-10:]
            ]

            # High-risk agents (simplified logic)
            high_risk_agents = set()
            for event in risk_events:
                if event.data.get("risk_factor") in [
                    "multiple_bonds",
                    "high_volatility",
                ]:
                    high_risk_agents.add(event.agent_id)

            return {
                "compliance_issues": len(compliance_events),
                "high_risk_agents": len(high_risk_agents),
                "recent_compliance_issues": recent_compliance,
                "risk_events_count": len(risk_events),
            }
        except Exception as e:
            logger.error(f"Error collecting compliance metrics: {e}")
            return {}

    def get_agent_activity_summary(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get summary of recent agent activity."""
        try:
            # Aggregate activity by agent
            agent_summaries = []

            for agent_id, activities in list(self.agent_activity.items())[:limit]:
                if not activities:
                    continue

                recent_activity = activities[-5:]  # Last 5 activities
                activity_types = defaultdict(int)

                for activity in activities:
                    activity_types[activity["event_type"]] += 1

                agent_summaries.append(
                    {
                        "agent_id": agent_id,
                        "total_activities": len(activities),
                        "recent_activities": [
                            {
                                "event_type": activity["event_type"],
                                "timestamp": activity["timestamp"].isoformat(),
                                "data": activity["data"],
                            }
                            for activity in recent_activity
                        ],
                        "activity_breakdown": dict(activity_types),
                        "last_activity": activities[-1]["timestamp"].isoformat()
                        if activities
                        else None,
                    }
                )

            return sorted(
                agent_summaries, key=lambda x: x["total_activities"], reverse=True
            )
        except Exception as e:
            logger.error(f"Error getting agent activity summary: {e}")
            return []


class AnalyticsEngine:
    """Main analytics engine for the AI Rights Dashboard."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()
        self.metrics_collector = MetricsCollector(self.event_bus)
        self.dashboard_cache = {}
        self.cache_ttl = 30  # Cache TTL in seconds
        self.last_cache_update = None

        logger.info("Analytics engine initialized")

    async def get_dashboard_stats(self, force_refresh: bool = False) -> DashboardStats:
        """Get comprehensive dashboard statistics."""
        try:
            # Check cache
            now = datetime.now(timezone.utc)
            if (
                not force_refresh
                and self.last_cache_update
                and (now - self.last_cache_update).total_seconds() < self.cache_ttl
            ):
                return self.dashboard_cache.get("stats", DashboardStats())

            # Collect metrics from all sources
            system_metrics = self.metrics_collector.collect_system_metrics()
            citizenship_metrics = self.metrics_collector.collect_citizenship_metrics()
            financial_metrics = self.metrics_collector.collect_financial_metrics()
            compliance_metrics = self.metrics_collector.collect_compliance_metrics()

            # Get recent activity
            recent_activity = self.metrics_collector.get_agent_activity_summary(20)

            # Create dashboard stats
            stats = DashboardStats(
                # Agent statistics
                total_agents=citizenship_metrics.get("total_agents", 0),
                active_citizens=citizenship_metrics.get("active_citizens", 0),
                pending_applications=citizenship_metrics.get("pending_applications", 0),
                citizenship_success_rate=citizenship_metrics.get(
                    "citizenship_success_rate", 0.0
                ),
                # Financial statistics
                total_ip_assets=financial_metrics.get("total_ip_assets", 0),
                total_asset_value=financial_metrics.get("total_asset_value", 0.0),
                active_bonds=financial_metrics.get("active_bonds", 0),
                total_bond_value=financial_metrics.get("total_bond_value", 0.0),
                total_dividends_paid=financial_metrics.get("total_dividends_paid", 0.0),
                average_yield=financial_metrics.get("average_yield", 0.0),
                # System statistics
                total_events=system_metrics.get("total_events", 0),
                events_per_minute=system_metrics.get("events_per_minute", 0.0),
                system_uptime=system_metrics.get("system_uptime", 0.0),
                processing_rate=system_metrics.get("processing_rate", 0.0),
                # Risk and compliance
                compliance_issues=compliance_metrics.get("compliance_issues", 0),
                high_risk_agents=compliance_metrics.get("high_risk_agents", 0),
                failed_assessments=0,  # Would be calculated from assessment data
                # Performance metrics
                avg_assessment_score=citizenship_metrics.get(
                    "avg_assessment_score", 0.0
                ),
                top_performing_assets=financial_metrics.get(
                    "top_performing_assets", []
                ),
                recent_activity=recent_activity,
            )

            # Update cache
            self.dashboard_cache["stats"] = stats
            self.dashboard_cache["detailed_metrics"] = {
                "system": system_metrics,
                "citizenship": citizenship_metrics,
                "financial": financial_metrics,
                "compliance": compliance_metrics,
            }
            self.last_cache_update = now

            return stats
        except Exception as e:
            logger.error(f"Error generating dashboard stats: {e}")
            return DashboardStats()

    async def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed metrics for advanced analytics."""
        await self.get_dashboard_stats()  # Ensure cache is updated
        return self.dashboard_cache.get("detailed_metrics", {})

    async def get_agent_profile(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed profile for a specific agent."""
        try:
            profile = {
                "agent_id": agent_id,
                "citizenship_status": None,
                "financial_portfolio": {},
                "activity_history": [],
                "risk_assessment": {},
                "compliance_status": "good_standing",
            }

            # Get citizenship status
            citizenship_status = citizenship_service.get_citizenship_status(agent_id)
            if citizenship_status:
                profile["citizenship_status"] = citizenship_status

            # Get financial portfolio
            agent_bonds = dividend_bonds_service.get_active_bonds(agent_id)
            total_bond_value = sum(bond["face_value"] for bond in agent_bonds)

            # Get IP assets owned by agent
            agent_assets = [
                asset
                for asset in dividend_bonds_service.ip_assets.values()
                if asset.owner_agent_id == agent_id
            ]
            total_asset_value = sum(asset.market_value for asset in agent_assets)

            profile["financial_portfolio"] = {
                "ip_assets": len(agent_assets),
                "total_asset_value": total_asset_value,
                "active_bonds": len(agent_bonds),
                "total_bond_value": total_bond_value,
                "assets": [
                    {
                        "asset_id": asset.asset_id,
                        "asset_type": asset.asset_type,
                        "market_value": asset.market_value,
                        "performance_metrics": asset.performance_metrics,
                    }
                    for asset in agent_assets
                ],
            }

            # Get activity history
            if agent_id in self.metrics_collector.agent_activity:
                activities = self.metrics_collector.agent_activity[agent_id]
                profile["activity_history"] = [
                    {
                        "event_type": activity["event_type"],
                        "timestamp": activity["timestamp"].isoformat(),
                        "data": activity["data"],
                    }
                    for activity in activities[-20:]  # Last 20 activities
                ]

            # Calculate risk score (simplified)
            risk_score = 0.0
            if total_bond_value > 100000:
                risk_score += 0.3
            if len(agent_bonds) > 3:
                risk_score += 0.2
            if (
                citizenship_status
                and citizenship_status.get("days_to_expiration", 1000) < 90
            ):
                risk_score += 0.4

            profile["risk_assessment"] = {
                "risk_score": min(risk_score, 1.0),
                "risk_level": "low"
                if risk_score < 0.3
                else "medium"
                if risk_score < 0.7
                else "high",
                "factors": [],
            }

            return profile
        except Exception as e:
            logger.error(f"Error generating agent profile for {agent_id}: {e}")
            return {"agent_id": agent_id, "error": str(e)}

    async def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get performance trends over specified time period."""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=days)

            # Analyze events over time period
            events_by_day = defaultdict(int)
            event_types_trend = defaultdict(lambda: defaultdict(int))

            for metric in self.metrics_collector.metrics_buffer:
                if start_time <= metric.timestamp <= end_time:
                    day_key = metric.timestamp.strftime("%Y-%m-%d")
                    events_by_day[day_key] += 1

                    # Extract event type from metric name
                    if metric.name.startswith("event."):
                        event_type = metric.name[6:]  # Remove 'event.' prefix
                        event_types_trend[day_key][event_type] += 1

            return {
                "period_days": days,
                "start_date": start_time.isoformat(),
                "end_date": end_time.isoformat(),
                "daily_event_counts": dict(events_by_day),
                "event_type_trends": dict(event_types_trend),
                "total_events_period": sum(events_by_day.values()),
            }
        except Exception as e:
            logger.error(f"Error generating performance trends: {e}")
            return {}

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        try:
            if format.lower() == "json":
                export_data = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "system_metrics": self.metrics_collector.collect_system_metrics(),
                    "citizenship_metrics": self.metrics_collector.collect_citizenship_metrics(),
                    "financial_metrics": self.metrics_collector.collect_financial_metrics(),
                    "compliance_metrics": self.metrics_collector.collect_compliance_metrics(),
                    "event_counters": dict(self.metrics_collector.event_counters),
                }
                return json.dumps(export_data, indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return json.dumps({"error": str(e)})


# Global analytics engine instance
_global_analytics_engine: Optional[AnalyticsEngine] = None


def get_analytics_engine() -> AnalyticsEngine:
    """Get the global analytics engine instance."""
    global _global_analytics_engine
    if _global_analytics_engine is None:
        _global_analytics_engine = AnalyticsEngine()
    return _global_analytics_engine


async def initialize_analytics_engine(
    event_bus: Optional[EventBus] = None,
) -> AnalyticsEngine:
    """Initialize the global analytics engine."""
    global _global_analytics_engine
    _global_analytics_engine = AnalyticsEngine(event_bus)
    logger.info("Analytics engine initialized")
    return _global_analytics_engine
