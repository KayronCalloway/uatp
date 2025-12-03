"""
Advanced Audit Analytics for UATP Capsule Engine.
Provides pattern detection, anomaly analysis, and comprehensive audit insights.
"""

import logging
import statistics
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from src.audit.events import AuditEvent, audit_emitter

logger = logging.getLogger(__name__)


class AnalyticsType(str, Enum):
    """Types of audit analytics."""

    PATTERN_DETECTION = "pattern_detection"
    ANOMALY_DETECTION = "anomaly_detection"
    TREND_ANALYSIS = "trend_analysis"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    COMPLIANCE_ANALYSIS = "compliance_analysis"


class AlertSeverity(str, Enum):
    """Severity levels for analytics alerts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditPattern:
    """Represents a detected pattern in audit events."""

    pattern_id: str
    pattern_type: str
    description: str
    event_types: List[str]
    frequency: int
    confidence: float
    first_seen: datetime
    last_seen: datetime
    agents_involved: Set[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "event_types": self.event_types,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "agents_involved": list(self.agents_involved),
            "metadata": self.metadata,
        }


@dataclass
class AuditAnomaly:
    """Represents an anomaly detected in audit events."""

    anomaly_id: str
    anomaly_type: str
    severity: AlertSeverity
    description: str
    event_data: Dict[str, Any]
    detection_timestamp: datetime
    confidence: float
    agent_id: Optional[str] = None
    capsule_id: Optional[str] = None
    related_events: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "anomaly_id": self.anomaly_id,
            "anomaly_type": self.anomaly_type,
            "severity": self.severity.value,
            "description": self.description,
            "event_data": self.event_data,
            "detection_timestamp": self.detection_timestamp.isoformat(),
            "confidence": self.confidence,
            "agent_id": self.agent_id,
            "capsule_id": self.capsule_id,
            "related_events": self.related_events,
        }


@dataclass
class AuditTrend:
    """Represents a trend in audit data."""

    trend_id: str
    metric: str
    trend_type: str  # "increasing", "decreasing", "stable", "volatile"
    time_window: timedelta
    change_percentage: float
    statistical_significance: float
    data_points: List[Tuple[datetime, float]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trend_id": self.trend_id,
            "metric": self.metric,
            "trend_type": self.trend_type,
            "time_window": str(self.time_window),
            "change_percentage": self.change_percentage,
            "statistical_significance": self.statistical_significance,
            "data_points_count": len(self.data_points),
        }


class AuditEventProcessor:
    """Processes audit events for analytics."""

    def __init__(self, max_events: int = 100000):
        self.events_buffer: deque = deque(maxlen=max_events)
        self.event_counts: Dict[str, int] = defaultdict(int)
        self.agent_activity: Dict[str, List[datetime]] = defaultdict(list)
        self.capsule_activity: Dict[str, List[datetime]] = defaultdict(list)
        self.event_sequences: Dict[str, List[AuditEvent]] = defaultdict(list)

    def process_event(self, event: AuditEvent):
        """Process a new audit event."""
        self.events_buffer.append(event)
        self.event_counts[event.event_type.value] += 1

        # Track agent activity
        if event.agent_id:
            self.agent_activity[event.agent_id].append(event.timestamp)

            # Keep only recent activity (last 24 hours)
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            self.agent_activity[event.agent_id] = [
                ts for ts in self.agent_activity[event.agent_id] if ts >= cutoff
            ]

        # Track capsule activity
        if event.capsule_id:
            self.capsule_activity[event.capsule_id].append(event.timestamp)

            # Keep only recent activity
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            self.capsule_activity[event.capsule_id] = [
                ts for ts in self.capsule_activity[event.capsule_id] if ts >= cutoff
            ]

        # Track event sequences for pattern detection
        sequence_key = f"{event.agent_id}_{event.capsule_id}"
        self.event_sequences[sequence_key].append(event)

        # Keep only recent sequences
        if len(self.event_sequences[sequence_key]) > 50:
            self.event_sequences[sequence_key] = self.event_sequences[sequence_key][
                -50:
            ]

    def get_recent_events(self, time_window: timedelta) -> List[AuditEvent]:
        """Get events from the specified time window."""
        cutoff = datetime.now(timezone.utc) - time_window
        return [event for event in self.events_buffer if event.timestamp >= cutoff]

    def get_events_by_type(
        self, event_type: str, time_window: timedelta
    ) -> List[AuditEvent]:
        """Get events of a specific type from time window."""
        recent_events = self.get_recent_events(time_window)
        return [
            event for event in recent_events if event.event_type.value == event_type
        ]

    def get_agent_events(
        self, agent_id: str, time_window: timedelta
    ) -> List[AuditEvent]:
        """Get events for a specific agent."""
        recent_events = self.get_recent_events(time_window)
        return [event for event in recent_events if event.agent_id == agent_id]

    def get_capsule_events(
        self, capsule_id: str, time_window: timedelta
    ) -> List[AuditEvent]:
        """Get events for a specific capsule."""
        recent_events = self.get_recent_events(time_window)
        return [event for event in recent_events if event.capsule_id == capsule_id]


class PatternDetector:
    """Detects patterns in audit events."""

    def __init__(self):
        self.known_patterns: Dict[str, AuditPattern] = {}
        self.pattern_templates = self._initialize_pattern_templates()

    def detect_patterns(self, processor: AuditEventProcessor) -> List[AuditPattern]:
        """Detect patterns in audit events."""
        patterns = []

        # Detect sequence patterns
        patterns.extend(self._detect_sequence_patterns(processor))

        # Detect frequency patterns
        patterns.extend(self._detect_frequency_patterns(processor))

        # Detect temporal patterns
        patterns.extend(self._detect_temporal_patterns(processor))

        # Detect behavioral patterns
        patterns.extend(self._detect_behavioral_patterns(processor))

        # Update known patterns
        for pattern in patterns:
            self.known_patterns[pattern.pattern_id] = pattern

        return patterns

    def _detect_sequence_patterns(
        self, processor: AuditEventProcessor
    ) -> List[AuditPattern]:
        """Detect sequential patterns in events."""
        patterns = []

        for sequence_key, events in processor.event_sequences.items():
            if len(events) < 3:
                continue

            # Look for common sequences
            event_types = [event.event_type.value for event in events]

            # Detect create->verify->access patterns
            if self._has_subsequence(
                event_types, ["capsule_created", "capsule_verified", "capsule_accessed"]
            ):
                pattern = AuditPattern(
                    pattern_id=f"create_verify_access_{sequence_key}",
                    pattern_type="sequential",
                    description="Standard capsule lifecycle pattern",
                    event_types=[
                        "capsule_created",
                        "capsule_verified",
                        "capsule_accessed",
                    ],
                    frequency=self._count_subsequence(
                        event_types,
                        ["capsule_created", "capsule_verified", "capsule_accessed"],
                    ),
                    confidence=0.9,
                    first_seen=events[0].timestamp,
                    last_seen=events[-1].timestamp,
                    agents_involved={
                        event.agent_id for event in events if event.agent_id
                    },
                )
                patterns.append(pattern)

            # Detect rapid-fire patterns (many events in short time)
            recent_events = [
                e
                for e in events
                if (datetime.now(timezone.utc) - e.timestamp).total_seconds() < 300
            ]
            if len(recent_events) > 10:
                pattern = AuditPattern(
                    pattern_id=f"rapid_fire_{sequence_key}",
                    pattern_type="frequency",
                    description="Rapid-fire event pattern detected",
                    event_types=list(set(event_types)),
                    frequency=len(recent_events),
                    confidence=0.8,
                    first_seen=recent_events[0].timestamp,
                    last_seen=recent_events[-1].timestamp,
                    agents_involved={
                        event.agent_id for event in recent_events if event.agent_id
                    },
                )
                patterns.append(pattern)

        return patterns

    def _detect_frequency_patterns(
        self, processor: AuditEventProcessor
    ) -> List[AuditPattern]:
        """Detect frequency-based patterns."""
        patterns = []

        # Analyze event frequency over time
        recent_events = processor.get_recent_events(timedelta(hours=1))

        if len(recent_events) > 100:  # High activity period
            event_type_counts = Counter(
                event.event_type.value for event in recent_events
            )

            for event_type, count in event_type_counts.items():
                if count > 20:  # Threshold for high frequency
                    pattern = AuditPattern(
                        pattern_id=f"high_frequency_{event_type}",
                        pattern_type="frequency",
                        description=f"High frequency {event_type} events",
                        event_types=[event_type],
                        frequency=count,
                        confidence=0.7,
                        first_seen=recent_events[0].timestamp,
                        last_seen=recent_events[-1].timestamp,
                        agents_involved={
                            event.agent_id
                            for event in recent_events
                            if event.agent_id and event.event_type.value == event_type
                        },
                    )
                    patterns.append(pattern)

        return patterns

    def _detect_temporal_patterns(
        self, processor: AuditEventProcessor
    ) -> List[AuditPattern]:
        """Detect temporal patterns in events."""
        patterns = []

        # Analyze activity by hour
        hourly_activity = defaultdict(int)

        for event in processor.get_recent_events(timedelta(days=7)):
            hourly_activity[event.timestamp.hour] += 1

        # Detect off-hours activity
        off_hours = [0, 1, 2, 3, 4, 5, 22, 23]
        off_hours_activity = sum(hourly_activity[hour] for hour in off_hours)
        total_activity = sum(hourly_activity.values())

        if total_activity > 0 and off_hours_activity / total_activity > 0.3:
            pattern = AuditPattern(
                pattern_id="off_hours_activity",
                pattern_type="temporal",
                description="Significant off-hours activity detected",
                event_types=list(processor.event_counts.keys()),
                frequency=off_hours_activity,
                confidence=0.8,
                first_seen=datetime.now(timezone.utc) - timedelta(days=7),
                last_seen=datetime.now(timezone.utc),
                agents_involved=set(),
            )
            patterns.append(pattern)

        return patterns

    def _detect_behavioral_patterns(
        self, processor: AuditEventProcessor
    ) -> List[AuditPattern]:
        """Detect behavioral patterns."""
        patterns = []

        # Analyze agent behavior
        for agent_id, activity_times in processor.agent_activity.items():
            if len(activity_times) > 50:  # Active agent
                # Calculate activity intervals
                intervals = []
                for i in range(1, len(activity_times)):
                    interval = (
                        activity_times[i] - activity_times[i - 1]
                    ).total_seconds()
                    intervals.append(interval)

                if intervals:
                    avg_interval = statistics.mean(intervals)

                    # Detect automated behavior (very regular intervals)
                    if avg_interval < 10 and statistics.stdev(intervals) < 2:
                        pattern = AuditPattern(
                            pattern_id=f"automated_behavior_{agent_id}",
                            pattern_type="behavioral",
                            description=f"Automated behavior pattern for agent {agent_id}",
                            event_types=[],
                            frequency=len(activity_times),
                            confidence=0.9,
                            first_seen=activity_times[0],
                            last_seen=activity_times[-1],
                            agents_involved={agent_id},
                        )
                        patterns.append(pattern)

        return patterns

    def _has_subsequence(self, sequence: List[str], subsequence: List[str]) -> bool:
        """Check if subsequence exists in sequence."""
        if len(subsequence) > len(sequence):
            return False

        for i in range(len(sequence) - len(subsequence) + 1):
            if sequence[i : i + len(subsequence)] == subsequence:
                return True

        return False

    def _count_subsequence(self, sequence: List[str], subsequence: List[str]) -> int:
        """Count occurrences of subsequence in sequence."""
        count = 0
        for i in range(len(sequence) - len(subsequence) + 1):
            if sequence[i : i + len(subsequence)] == subsequence:
                count += 1
        return count

    def _initialize_pattern_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize pattern detection templates."""
        return {
            "normal_lifecycle": {
                "sequence": ["capsule_created", "capsule_verified", "capsule_accessed"],
                "description": "Normal capsule lifecycle",
                "confidence": 0.9,
            },
            "failed_verification": {
                "sequence": ["capsule_created", "signature_failed"],
                "description": "Failed capsule verification",
                "confidence": 0.8,
            },
            "rapid_access": {
                "frequency_threshold": 10,
                "time_window": 60,
                "description": "Rapid capsule access pattern",
                "confidence": 0.7,
            },
        }


class AnomalyDetector:
    """Detects anomalies in audit events."""

    def __init__(self):
        self.baseline_metrics: Dict[str, float] = {}
        self.anomaly_thresholds: Dict[str, float] = {}
        self.detected_anomalies: List[AuditAnomaly] = []

    def detect_anomalies(self, processor: AuditEventProcessor) -> List[AuditAnomaly]:
        """Detect anomalies in audit events."""
        anomalies = []

        # Update baseline metrics
        self._update_baseline_metrics(processor)

        # Detect volume anomalies
        anomalies.extend(self._detect_volume_anomalies(processor))

        # Detect timing anomalies
        anomalies.extend(self._detect_timing_anomalies(processor))

        # Detect behavioral anomalies
        anomalies.extend(self._detect_behavioral_anomalies(processor))

        # Detect security anomalies
        anomalies.extend(self._detect_security_anomalies(processor))

        # Store detected anomalies
        self.detected_anomalies.extend(anomalies)

        return anomalies

    def _update_baseline_metrics(self, processor: AuditEventProcessor):
        """Update baseline metrics for anomaly detection."""
        recent_events = processor.get_recent_events(timedelta(hours=24))

        if recent_events:
            # Calculate baseline event rates
            event_types = [event.event_type.value for event in recent_events]
            type_counts = Counter(event_types)

            for event_type, count in type_counts.items():
                hourly_rate = count / 24  # Events per hour
                self.baseline_metrics[f"{event_type}_rate"] = hourly_rate
                self.anomaly_thresholds[f"{event_type}_rate"] = (
                    hourly_rate * 3
                )  # 3x baseline as threshold

    def _detect_volume_anomalies(
        self, processor: AuditEventProcessor
    ) -> List[AuditAnomaly]:
        """Detect volume-based anomalies."""
        anomalies = []

        # Check recent hour against baseline
        recent_hour = processor.get_recent_events(timedelta(hours=1))
        event_types = [event.event_type.value for event in recent_hour]
        type_counts = Counter(event_types)

        for event_type, count in type_counts.items():
            baseline_key = f"{event_type}_rate"

            if baseline_key in self.baseline_metrics:
                baseline_rate = self.baseline_metrics[baseline_key]
                threshold = self.anomaly_thresholds.get(baseline_key, baseline_rate * 3)

                if count > threshold:
                    anomaly = AuditAnomaly(
                        anomaly_id=self._generate_anomaly_id(),
                        anomaly_type="volume_spike",
                        severity=AlertSeverity.HIGH,
                        description=f"Volume spike in {event_type} events: {count} vs baseline {baseline_rate:.1f}",
                        event_data={
                            "event_type": event_type,
                            "count": count,
                            "baseline": baseline_rate,
                        },
                        detection_timestamp=datetime.now(timezone.utc),
                        confidence=min(0.95, (count - threshold) / threshold),
                    )
                    anomalies.append(anomaly)

        return anomalies

    def _detect_timing_anomalies(
        self, processor: AuditEventProcessor
    ) -> List[AuditAnomaly]:
        """Detect timing-based anomalies."""
        anomalies = []

        # Check for events at unusual times
        recent_events = processor.get_recent_events(timedelta(hours=1))

        for event in recent_events:
            hour = event.timestamp.hour

            # Flag events between 2 AM and 5 AM as potentially anomalous
            if 2 <= hour <= 5:
                anomaly = AuditAnomaly(
                    anomaly_id=self._generate_anomaly_id(),
                    anomaly_type="unusual_timing",
                    severity=AlertSeverity.MEDIUM,
                    description=f"Event at unusual time: {hour}:00",
                    event_data={"event_type": event.event_type.value, "hour": hour},
                    detection_timestamp=datetime.now(timezone.utc),
                    confidence=0.6,
                    agent_id=event.agent_id,
                    capsule_id=event.capsule_id,
                )
                anomalies.append(anomaly)

        return anomalies

    def _detect_behavioral_anomalies(
        self, processor: AuditEventProcessor
    ) -> List[AuditAnomaly]:
        """Detect behavioral anomalies."""
        anomalies = []

        # Analyze agent behavior
        for agent_id, activity_times in processor.agent_activity.items():
            if len(activity_times) > 100:  # High activity
                # Calculate time intervals
                intervals = []
                for i in range(1, len(activity_times)):
                    interval = (
                        activity_times[i] - activity_times[i - 1]
                    ).total_seconds()
                    intervals.append(interval)

                if intervals:
                    avg_interval = statistics.mean(intervals)

                    # Detect suspiciously regular behavior
                    if avg_interval < 5 and len(intervals) > 50:
                        anomaly = AuditAnomaly(
                            anomaly_id=self._generate_anomaly_id(),
                            anomaly_type="suspicious_regularity",
                            severity=AlertSeverity.HIGH,
                            description=f"Suspiciously regular behavior from agent {agent_id}",
                            event_data={
                                "agent_id": agent_id,
                                "avg_interval": avg_interval,
                                "event_count": len(intervals),
                            },
                            detection_timestamp=datetime.now(timezone.utc),
                            confidence=0.8,
                            agent_id=agent_id,
                        )
                        anomalies.append(anomaly)

        return anomalies

    def _detect_security_anomalies(
        self, processor: AuditEventProcessor
    ) -> List[AuditAnomaly]:
        """Detect security-related anomalies."""
        anomalies = []

        # Check for multiple failed authentications
        recent_events = processor.get_recent_events(timedelta(hours=1))
        failed_auth_events = [
            event
            for event in recent_events
            if event.event_type.value == "authentication_failed"
        ]

        if len(failed_auth_events) > 5:
            anomaly = AuditAnomaly(
                anomaly_id=self._generate_anomaly_id(),
                anomaly_type="multiple_auth_failures",
                severity=AlertSeverity.CRITICAL,
                description=f"Multiple authentication failures: {len(failed_auth_events)} in last hour",
                event_data={"failure_count": len(failed_auth_events)},
                detection_timestamp=datetime.now(timezone.utc),
                confidence=0.9,
            )
            anomalies.append(anomaly)

        # Check for signature verification failures
        sig_failed_events = [
            event
            for event in recent_events
            if event.event_type.value == "signature_failed"
        ]

        if len(sig_failed_events) > 3:
            anomaly = AuditAnomaly(
                anomaly_id=self._generate_anomaly_id(),
                anomaly_type="signature_verification_failures",
                severity=AlertSeverity.HIGH,
                description=f"Multiple signature verification failures: {len(sig_failed_events)}",
                event_data={"failure_count": len(sig_failed_events)},
                detection_timestamp=datetime.now(timezone.utc),
                confidence=0.8,
            )
            anomalies.append(anomaly)

        return anomalies

    def _generate_anomaly_id(self) -> str:
        """Generate unique anomaly ID."""
        import uuid

        return str(uuid.uuid4())[:12]


class TrendAnalyzer:
    """Analyzes trends in audit data."""

    def __init__(self):
        self.trend_cache: Dict[str, AuditTrend] = {}
        self.metric_history: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)

    def analyze_trends(self, processor: AuditEventProcessor) -> List[AuditTrend]:
        """Analyze trends in audit data."""
        trends = []

        # Update metric history
        self._update_metric_history(processor)

        # Analyze event volume trends
        trends.extend(self._analyze_volume_trends())

        # Analyze agent activity trends
        trends.extend(self._analyze_agent_trends(processor))

        # Analyze performance trends
        trends.extend(self._analyze_performance_trends(processor))

        # Cache trends
        for trend in trends:
            self.trend_cache[trend.trend_id] = trend

        return trends

    def _update_metric_history(self, processor: AuditEventProcessor):
        """Update metric history for trend analysis."""
        current_time = datetime.now(timezone.utc)

        # Update event volume metrics
        recent_events = processor.get_recent_events(timedelta(hours=1))
        event_volume = len(recent_events)

        self.metric_history["event_volume"].append((current_time, event_volume))

        # Update event type metrics
        event_types = [event.event_type.value for event in recent_events]
        type_counts = Counter(event_types)

        for event_type, count in type_counts.items():
            self.metric_history[f"{event_type}_count"].append((current_time, count))

        # Keep only last 24 hours of data
        cutoff = current_time - timedelta(hours=24)
        for metric, data_points in self.metric_history.items():
            self.metric_history[metric] = [
                (timestamp, value)
                for timestamp, value in data_points
                if timestamp >= cutoff
            ]

    def _analyze_volume_trends(self) -> List[AuditTrend]:
        """Analyze event volume trends."""
        trends = []

        if "event_volume" in self.metric_history:
            data_points = self.metric_history["event_volume"]

            if len(data_points) >= 5:
                trend = self._calculate_trend(
                    "event_volume", data_points, timedelta(hours=24)
                )
                if trend:
                    trends.append(trend)

        return trends

    def _analyze_agent_trends(self, processor: AuditEventProcessor) -> List[AuditTrend]:
        """Analyze agent activity trends."""
        trends = []

        # Analyze agent activity over time
        for agent_id, activity_times in processor.agent_activity.items():
            if len(activity_times) >= 10:
                # Create hourly activity data
                hourly_activity = defaultdict(int)
                for timestamp in activity_times:
                    hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
                    hourly_activity[hour_key] += 1

                # Convert to data points
                data_points = [
                    (timestamp, count) for timestamp, count in hourly_activity.items()
                ]
                data_points.sort(key=lambda x: x[0])

                if len(data_points) >= 3:
                    trend = self._calculate_trend(
                        f"agent_{agent_id}_activity", data_points, timedelta(hours=24)
                    )
                    if trend:
                        trends.append(trend)

        return trends

    def _analyze_performance_trends(
        self, processor: AuditEventProcessor
    ) -> List[AuditTrend]:
        """Analyze performance trends."""
        trends = []

        # This would analyze performance metrics if available
        # For now, return empty list

        return trends

    def _calculate_trend(
        self,
        metric: str,
        data_points: List[Tuple[datetime, float]],
        time_window: timedelta,
    ) -> Optional[AuditTrend]:
        """Calculate trend for a metric."""

        if len(data_points) < 3:
            return None

        # Sort by timestamp
        data_points.sort(key=lambda x: x[0])

        # Extract values
        values = [value for _, value in data_points]

        # Calculate trend
        if len(values) >= 2:
            first_value = values[0]
            last_value = values[-1]

            if first_value == 0:
                change_percentage = 0.0
            else:
                change_percentage = ((last_value - first_value) / first_value) * 100

            # Determine trend type
            if abs(change_percentage) < 5:
                trend_type = "stable"
            elif change_percentage > 20:
                trend_type = "increasing"
            elif change_percentage < -20:
                trend_type = "decreasing"
            else:
                trend_type = "stable"

            # Calculate statistical significance (simplified)
            significance = min(0.95, abs(change_percentage) / 100)

            return AuditTrend(
                trend_id=f"trend_{metric}_{int(datetime.now(timezone.utc).timestamp())}",
                metric=metric,
                trend_type=trend_type,
                time_window=time_window,
                change_percentage=change_percentage,
                statistical_significance=significance,
                data_points=data_points,
            )

        return None


class AdvancedAuditAnalytics:
    """Main advanced audit analytics engine."""

    def __init__(self):
        self.event_processor = AuditEventProcessor()
        self.pattern_detector = PatternDetector()
        self.anomaly_detector = AnomalyDetector()
        self.trend_analyzer = TrendAnalyzer()
        self.analysis_results: Dict[str, Any] = {}
        self.alerts: List[Dict[str, Any]] = []

    def process_audit_event(self, event: AuditEvent):
        """Process a new audit event."""
        self.event_processor.process_event(event)

        # Run real-time analysis
        self._run_realtime_analysis(event)

    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive audit analysis."""

        results = {
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "patterns": [],
            "anomalies": [],
            "trends": [],
            "summary": {},
        }

        # Detect patterns
        patterns = self.pattern_detector.detect_patterns(self.event_processor)
        results["patterns"] = [pattern.to_dict() for pattern in patterns]

        # Detect anomalies
        anomalies = self.anomaly_detector.detect_anomalies(self.event_processor)
        results["anomalies"] = [anomaly.to_dict() for anomaly in anomalies]

        # Analyze trends
        trends = self.trend_analyzer.analyze_trends(self.event_processor)
        results["trends"] = [trend.to_dict() for trend in trends]

        # Generate summary
        results["summary"] = self._generate_analysis_summary(
            patterns, anomalies, trends
        )

        # Store results
        self.analysis_results[datetime.now(timezone.utc).isoformat()] = results

        # Generate alerts
        self._generate_alerts(anomalies, patterns)

        return results

    def _run_realtime_analysis(self, event: AuditEvent):
        """Run real-time analysis on new event."""

        # Check for immediate anomalies
        recent_events = self.event_processor.get_recent_events(timedelta(minutes=5))

        # Check for rapid-fire events
        if len(recent_events) > 20:
            anomaly = AuditAnomaly(
                anomaly_id=self.anomaly_detector._generate_anomaly_id(),
                anomaly_type="rapid_fire_events",
                severity=AlertSeverity.HIGH,
                description=f"Rapid-fire events detected: {len(recent_events)} in 5 minutes",
                event_data={"event_count": len(recent_events)},
                detection_timestamp=datetime.now(timezone.utc),
                confidence=0.8,
            )

            self.alerts.append(
                {
                    "type": "anomaly",
                    "severity": anomaly.severity.value,
                    "description": anomaly.description,
                    "timestamp": anomaly.detection_timestamp.isoformat(),
                }
            )

    def _generate_analysis_summary(
        self,
        patterns: List[AuditPattern],
        anomalies: List[AuditAnomaly],
        trends: List[AuditTrend],
    ) -> Dict[str, Any]:
        """Generate analysis summary."""

        # Event statistics
        recent_events = self.event_processor.get_recent_events(timedelta(hours=24))
        event_counts = Counter(event.event_type.value for event in recent_events)

        # Active agents
        active_agents = {event.agent_id for event in recent_events if event.agent_id}

        # Anomaly severity distribution
        anomaly_severities = Counter(anomaly.severity.value for anomaly in anomalies)

        return {
            "total_events_24h": len(recent_events),
            "unique_event_types": len(event_counts),
            "active_agents": len(active_agents),
            "patterns_detected": len(patterns),
            "anomalies_detected": len(anomalies),
            "trends_identified": len(trends),
            "event_type_distribution": dict(event_counts),
            "anomaly_severity_distribution": dict(anomaly_severities),
            "most_common_event_type": event_counts.most_common(1)[0][0]
            if event_counts
            else None,
            "analysis_health": "healthy"
            if len(anomalies) == 0
            else "concerns_detected",
        }

    def _generate_alerts(
        self, anomalies: List[AuditAnomaly], patterns: List[AuditPattern]
    ):
        """Generate alerts from analysis results."""

        # Generate alerts for critical anomalies
        for anomaly in anomalies:
            if anomaly.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                alert = {
                    "type": "anomaly",
                    "severity": anomaly.severity.value,
                    "description": anomaly.description,
                    "timestamp": anomaly.detection_timestamp.isoformat(),
                    "confidence": anomaly.confidence,
                    "anomaly_id": anomaly.anomaly_id,
                }
                self.alerts.append(alert)

        # Generate alerts for concerning patterns
        for pattern in patterns:
            if pattern.confidence > 0.8 and pattern.frequency > 50:
                alert = {
                    "type": "pattern",
                    "severity": "medium",
                    "description": f"High-frequency pattern detected: {pattern.description}",
                    "timestamp": pattern.last_seen.isoformat(),
                    "confidence": pattern.confidence,
                    "pattern_id": pattern.pattern_id,
                }
                self.alerts.append(alert)

    def get_analytics_dashboard(self) -> Dict[str, Any]:
        """Get analytics dashboard data."""

        recent_events = self.event_processor.get_recent_events(timedelta(hours=24))

        return {
            "event_volume": {
                "last_24h": len(recent_events),
                "last_hour": len(
                    self.event_processor.get_recent_events(timedelta(hours=1))
                ),
                "event_rate": len(recent_events) / 24,  # Events per hour
            },
            "agent_activity": {
                "active_agents": len(self.event_processor.agent_activity),
                "most_active_agent": max(
                    self.event_processor.agent_activity.items(), key=lambda x: len(x[1])
                )[0]
                if self.event_processor.agent_activity
                else None,
            },
            "recent_patterns": len(self.pattern_detector.known_patterns),
            "recent_anomalies": len(self.anomaly_detector.detected_anomalies),
            "active_alerts": len(
                [
                    alert
                    for alert in self.alerts
                    if alert["severity"] in ["high", "critical"]
                ]
            ),
            "system_health": self._calculate_system_health(),
            "top_event_types": Counter(
                event.event_type.value for event in recent_events
            ).most_common(5),
        }

    def _calculate_system_health(self) -> str:
        """Calculate overall system health score."""

        # Simple health calculation
        recent_anomalies = len(self.anomaly_detector.detected_anomalies)
        critical_alerts = len(
            [alert for alert in self.alerts if alert["severity"] == "critical"]
        )

        if critical_alerts > 0:
            return "critical"
        elif recent_anomalies > 10:
            return "warning"
        elif recent_anomalies > 5:
            return "caution"
        else:
            return "healthy"


# Global advanced audit analytics instance
advanced_audit_analytics = AdvancedAuditAnalytics()


# Hook into the audit emitter to process events
class AnalyticsAuditHandler:
    """Audit handler that feeds events to analytics."""

    def handle(self, event: AuditEvent):
        """Handle audit event for analytics."""
        advanced_audit_analytics.process_audit_event(event)


# Add analytics handler to audit emitter
audit_emitter.add_handler(AnalyticsAuditHandler())
