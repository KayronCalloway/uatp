"""
quality_decay_detector.py - Quality Decay Detection and Remediation System

This module implements automated detection and remediation of long-term quality degradation
in the UATP capsule chain. Provides early warning systems, trend analysis, and automated
quality improvement mechanisms to maintain chain integrity over time.

Key Features:
- Historical quality trend analysis with degradation detection
- Automated quality remediation when degradation detected
- Quality improvement suggestions and automated optimization
- Preventive quality maintenance mechanisms
- Economic feedback loops for quality incentivization
- Machine learning-based quality prediction
- Multi-dimensional quality assessment
"""

import asyncio
import json
import logging
import statistics
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
import numpy as np
from scipy import signal
import warnings

from .cqss import CQSSResult, compute_cqss
from ..economic.fcde_engine import fcde_engine

# Suppress scipy warnings for production
warnings.filterwarnings("ignore", category=RuntimeWarning)

logger = logging.getLogger(__name__)


class DecayPattern(str, Enum):
    """Types of quality decay patterns."""

    LINEAR_DECLINE = "linear_decline"
    EXPONENTIAL_DECAY = "exponential_decay"
    SUDDEN_DROP = "sudden_drop"
    CYCLICAL_DEGRADATION = "cyclical_degradation"
    RANDOM_NOISE = "random_noise"
    PLATEAU_THEN_DECLINE = "plateau_then_decline"
    OSCILLATING_DECLINE = "oscillating_decline"


class RemediationStrategy(str, Enum):
    """Strategies for quality remediation."""

    ECONOMIC_INCENTIVES = "economic_incentives"
    AUTOMATED_OPTIMIZATION = "automated_optimization"
    COMMUNITY_INTERVENTION = "community_intervention"
    SYSTEM_PARAMETER_TUNING = "system_parameter_tuning"
    CONTENT_FILTERING = "content_filtering"
    AGENT_RETRAINING = "agent_retraining"
    EMERGENCY_LOCKDOWN = "emergency_lockdown"


class QualityAlert(str, Enum):
    """Quality alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class QualityTrendPoint:
    """Single point in quality trend history."""

    timestamp: datetime
    overall_score: float
    integrity_score: float
    trust_score: float
    complexity_score: float
    diversity_score: float
    verification_ratio: float
    chain_length: int
    capsule_count_delta: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecayDetectionResult:
    """Result of quality decay detection analysis."""

    decay_detected: bool
    decay_pattern: DecayPattern
    severity_score: float  # 0.0 = no decay, 1.0 = critical decay
    confidence: float  # Confidence in detection
    time_to_critical: Optional[timedelta]  # Estimated time until critical failure
    affected_dimensions: List[str]
    trend_points: List[QualityTrendPoint]
    statistical_analysis: Dict[str, float]
    recommended_actions: List[RemediationStrategy]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RemediationAction:
    """Action taken to remediate quality decay."""

    action_id: str
    strategy: RemediationStrategy
    timestamp: datetime
    target_dimensions: List[str]
    expected_improvement: float
    actual_improvement: Optional[float] = None
    cost: float = 0.0
    success: Optional[bool] = None
    duration: Optional[timedelta] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class QualityDecayDetector:
    """
    Automated quality decay detection and remediation system.

    Monitors chain quality over time, detects degradation patterns,
    and implements automated remediation strategies to maintain
    long-term system health and quality standards.
    """

    def __init__(
        self,
        trend_window_hours: int = 168,  # 1 week
        detection_sensitivity: float = 0.7,
        min_trend_points: int = 10,
        economic_engine=None,
    ):
        """Initialize the quality decay detector.

        Args:
            trend_window_hours: Hours of history to consider for trend analysis
            detection_sensitivity: Sensitivity threshold for decay detection (0.0-1.0)
            min_trend_points: Minimum points needed for reliable trend analysis
            economic_engine: Economic engine for remediation actions
        """
        self.trend_window_hours = trend_window_hours
        self.detection_sensitivity = detection_sensitivity
        self.min_trend_points = min_trend_points
        self.economic_engine = economic_engine or fcde_engine

        # Quality trend history
        self.quality_history: deque = deque(maxlen=1000)  # Store up to 1000 points
        self.trend_analysis_cache: Dict[str, Any] = {}
        self.cache_ttl_minutes = 15

        # Decay detection state
        self.last_analysis_time: Optional[datetime] = None
        self.current_decay_state: Optional[DecayDetectionResult] = None
        self.active_remediations: Dict[str, RemediationAction] = {}
        self.remediation_history: List[RemediationAction] = []

        # Alert system
        self.alert_callbacks: List[
            Callable[[QualityAlert, str, Dict[str, Any]], None]
        ] = []
        self.alert_history: List[Dict[str, Any]] = []

        # Configuration parameters
        self.decay_thresholds = {
            DecayPattern.LINEAR_DECLINE: 0.1,  # 10% decline over window
            DecayPattern.EXPONENTIAL_DECAY: 0.2,  # 20% exponential decay
            DecayPattern.SUDDEN_DROP: 0.15,  # 15% sudden drop
            DecayPattern.CYCLICAL_DEGRADATION: 0.08,  # 8% cyclical degradation
            DecayPattern.PLATEAU_THEN_DECLINE: 0.12,  # 12% after plateau
            DecayPattern.OSCILLATING_DECLINE: 0.1,  # 10% oscillating decline
        }

        # Remediation effectiveness tracking
        self.remediation_effectiveness: Dict[RemediationStrategy, float] = defaultdict(
            float
        )
        self.remediation_costs: Dict[RemediationStrategy, float] = defaultdict(float)

        logger.info(
            f"Initialized quality decay detector with {trend_window_hours}h window"
        )

    async def record_quality_measurement(self, quality_result: CQSSResult) -> bool:
        """Record a new quality measurement for trend analysis.

        Args:
            quality_result: CQSS quality result to record

        Returns:
            True if recorded successfully
        """
        try:
            if not quality_result or not quality_result.metrics:
                return False

            # Create trend point
            trend_point = QualityTrendPoint(
                timestamp=datetime.now(timezone.utc),
                overall_score=quality_result.get_overall_score() or 0.0,
                integrity_score=quality_result.metrics.get("integrity_score", 0.0),
                trust_score=quality_result.metrics.get("trust_score", 0.0),
                complexity_score=quality_result.metrics.get("complexity_score", 0.0),
                diversity_score=quality_result.metrics.get("diversity_score", 0.0),
                verification_ratio=quality_result.metrics.get(
                    "verification_ratio", 0.0
                ),
                chain_length=quality_result.metrics.get("chain_length", 0),
                capsule_count_delta=self._calculate_capsule_delta(),
                metadata={
                    "fork_count": quality_result.metrics.get("fork_count", 0),
                    "unique_agents": quality_result.metrics.get("unique_agents", 0),
                    "avg_confidence": quality_result.metrics.get("avg_confidence", 0.0),
                },
            )

            # Add to history
            self.quality_history.append(trend_point)

            # Clear cache to force re-analysis
            self.trend_analysis_cache.clear()

            logger.debug(
                f"Recorded quality measurement: overall={trend_point.overall_score:.3f}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to record quality measurement: {e}")
            return False

    async def analyze_quality_trends(self) -> Optional[DecayDetectionResult]:
        """Analyze quality trends and detect decay patterns.

        Returns:
            Decay detection result or None if insufficient data
        """
        if len(self.quality_history) < self.min_trend_points:
            logger.debug(
                f"Insufficient data for trend analysis: {len(self.quality_history)}/{self.min_trend_points}"
            )
            return None

        # Check cache
        cache_key = f"trend_analysis_{len(self.quality_history)}"
        now = datetime.now(timezone.utc)

        if (
            cache_key in self.trend_analysis_cache
            and self.last_analysis_time
            and (now - self.last_analysis_time).seconds < self.cache_ttl_minutes * 60
        ):
            return self.trend_analysis_cache[cache_key]

        try:
            # Filter to analysis window
            cutoff_time = now - timedelta(hours=self.trend_window_hours)
            recent_points = [
                point
                for point in self.quality_history
                if point.timestamp >= cutoff_time
            ]

            if len(recent_points) < self.min_trend_points:
                logger.debug(
                    f"Insufficient recent data: {len(recent_points)}/{self.min_trend_points}"
                )
                return None

            # Sort by timestamp
            recent_points.sort(key=lambda p: p.timestamp)

            # Perform statistical analysis
            statistical_analysis = await self._perform_statistical_analysis(
                recent_points
            )

            # Detect decay patterns
            decay_pattern, confidence = await self._detect_decay_pattern(
                recent_points, statistical_analysis
            )

            # Calculate severity
            severity_score = await self._calculate_decay_severity(
                recent_points, decay_pattern, statistical_analysis
            )

            # Estimate time to critical failure
            time_to_critical = await self._estimate_time_to_critical(
                recent_points, decay_pattern, severity_score
            )

            # Identify affected dimensions
            affected_dimensions = await self._identify_affected_dimensions(
                recent_points, statistical_analysis
            )

            # Generate recommended actions
            recommended_actions = await self._generate_remediation_recommendations(
                decay_pattern, severity_score, affected_dimensions
            )

            # Create result
            result = DecayDetectionResult(
                decay_detected=severity_score > self.detection_sensitivity,
                decay_pattern=decay_pattern,
                severity_score=severity_score,
                confidence=confidence,
                time_to_critical=time_to_critical,
                affected_dimensions=affected_dimensions,
                trend_points=recent_points[-20:],  # Include last 20 points
                statistical_analysis=statistical_analysis,
                recommended_actions=recommended_actions,
                metadata={
                    "analysis_window_hours": self.trend_window_hours,
                    "points_analyzed": len(recent_points),
                    "analysis_timestamp": now.isoformat(),
                },
            )

            # Cache result
            self.trend_analysis_cache[cache_key] = result
            self.last_analysis_time = now
            self.current_decay_state = result

            # Trigger alerts if decay detected
            if result.decay_detected:
                await self._trigger_decay_alert(result)

            return result

        except Exception as e:
            logger.error(f"Failed to analyze quality trends: {e}")
            return None

    async def implement_remediation(
        self, strategy: RemediationStrategy, target_dimensions: List[str] = None
    ) -> Optional[str]:
        """Implement a quality remediation strategy.

        Args:
            strategy: Remediation strategy to implement
            target_dimensions: Specific quality dimensions to target

        Returns:
            Action ID if successful, None otherwise
        """
        try:
            action_id = f"remediation_{strategy.value}_{int(datetime.now(timezone.utc).timestamp())}"

            # Calculate expected improvement
            expected_improvement = await self._estimate_remediation_effectiveness(
                strategy, target_dimensions
            )

            # Calculate cost
            cost = await self._calculate_remediation_cost(strategy, target_dimensions)

            # Create remediation action
            action = RemediationAction(
                action_id=action_id,
                strategy=strategy,
                timestamp=datetime.now(timezone.utc),
                target_dimensions=target_dimensions or [],
                expected_improvement=expected_improvement,
                cost=cost,
                metadata={"initiated_by": "quality_decay_detector"},
            )

            # Execute strategy
            success = await self._execute_remediation_strategy(action)

            if success:
                action.success = True
                self.active_remediations[action_id] = action
                logger.info(
                    f"Implemented remediation strategy: {strategy.value} (ID: {action_id})"
                )

                # Schedule effectiveness evaluation
                asyncio.create_task(
                    self._evaluate_remediation_after_delay(action_id, delay_hours=1)
                )

                return action_id
            else:
                action.success = False
                self.remediation_history.append(action)
                logger.error(
                    f"Failed to implement remediation strategy: {strategy.value}"
                )
                return None

        except Exception as e:
            logger.error(f"Error implementing remediation {strategy.value}: {e}")
            return None

    async def _perform_statistical_analysis(
        self, points: List[QualityTrendPoint]
    ) -> Dict[str, float]:
        """Perform statistical analysis on trend points.

        Args:
            points: Quality trend points to analyze

        Returns:
            Dictionary with statistical metrics
        """
        if len(points) < 2:
            return {}

        # Extract time series data
        timestamps = [p.timestamp for p in points]
        overall_scores = [p.overall_score for p in points]
        integrity_scores = [p.integrity_score for p in points]
        trust_scores = [p.trust_score for p in points]

        # Calculate basic statistics
        analysis = {
            "overall_mean": statistics.mean(overall_scores),
            "overall_stdev": statistics.stdev(overall_scores)
            if len(overall_scores) > 1
            else 0.0,
            "overall_trend_slope": self._calculate_trend_slope(
                timestamps, overall_scores
            ),
            "integrity_mean": statistics.mean(integrity_scores),
            "integrity_trend_slope": self._calculate_trend_slope(
                timestamps, integrity_scores
            ),
            "trust_mean": statistics.mean(trust_scores),
            "trust_trend_slope": self._calculate_trend_slope(timestamps, trust_scores),
        }

        # Calculate advanced metrics
        if len(points) >= 5:
            # Moving averages
            overall_ma5 = self._calculate_moving_average(overall_scores, 5)
            analysis["overall_ma5_slope"] = self._calculate_trend_slope(
                timestamps[-len(overall_ma5) :], overall_ma5
            )

            # Volatility
            returns = [
                (overall_scores[i] - overall_scores[i - 1])
                / max(overall_scores[i - 1], 0.001)
                for i in range(1, len(overall_scores))
            ]
            analysis["volatility"] = (
                statistics.stdev(returns) if len(returns) > 1 else 0.0
            )

            # Momentum indicators
            analysis["momentum"] = (overall_scores[-1] - overall_scores[-5]) / max(
                overall_scores[-5], 0.001
            )

        # Correlation analysis
        if len(points) >= 10:
            analysis["integrity_trust_correlation"] = self._calculate_correlation(
                integrity_scores, trust_scores
            )

        return analysis

    def _calculate_trend_slope(
        self, timestamps: List[datetime], values: List[float]
    ) -> float:
        """Calculate the slope of a trend line.

        Args:
            timestamps: Time points
            values: Corresponding values

        Returns:
            Slope of the trend line
        """
        if len(timestamps) < 2:
            return 0.0

        # Convert timestamps to numeric values (hours since first point)
        base_time = timestamps[0]
        x_values = [(t - base_time).total_seconds() / 3600 for t in timestamps]

        # Calculate linear regression slope
        n = len(x_values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_x2 = sum(x * x for x in x_values)

        denominator = n * sum_x2 - sum_x * sum_x
        if abs(denominator) < 1e-10:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def _calculate_moving_average(
        self, values: List[float], window: int
    ) -> List[float]:
        """Calculate moving average of values.

        Args:
            values: Input values
            window: Moving average window size

        Returns:
            List of moving average values
        """
        if len(values) < window:
            return values

        ma_values = []
        for i in range(window - 1, len(values)):
            window_values = values[i - window + 1 : i + 1]
            ma_values.append(statistics.mean(window_values))

        return ma_values

    def _calculate_correlation(
        self, x_values: List[float], y_values: List[float]
    ) -> float:
        """Calculate correlation coefficient between two series.

        Args:
            x_values: First series
            y_values: Second series

        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0

        try:
            x_mean = statistics.mean(x_values)
            y_mean = statistics.mean(y_values)

            numerator = sum(
                (x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values)
            )

            x_var = sum((x - x_mean) ** 2 for x in x_values)
            y_var = sum((y - y_mean) ** 2 for y in y_values)

            denominator = (x_var * y_var) ** 0.5

            if abs(denominator) < 1e-10:
                return 0.0

            return numerator / denominator

        except Exception:
            return 0.0

    async def _detect_decay_pattern(
        self, points: List[QualityTrendPoint], stats: Dict[str, float]
    ) -> Tuple[DecayPattern, float]:
        """Detect the specific pattern of quality decay.

        Args:
            points: Quality trend points
            stats: Statistical analysis results

        Returns:
            Tuple of (detected pattern, confidence)
        """
        overall_scores = [p.overall_score for p in points]

        # Check for sudden drop
        if len(overall_scores) >= 5:
            recent_drop = overall_scores[-1] - max(overall_scores[-5:-1])
            if recent_drop < -0.15:  # 15% drop
                return DecayPattern.SUDDEN_DROP, 0.9

        # Check for linear decline
        trend_slope = stats.get("overall_trend_slope", 0.0)
        if trend_slope < -0.01:  # Negative slope
            # Check if it's consistently declining
            declining_points = 0
            for i in range(1, len(overall_scores)):
                if overall_scores[i] < overall_scores[i - 1]:
                    declining_points += 1

            decline_ratio = declining_points / (len(overall_scores) - 1)
            if decline_ratio > 0.6:  # More than 60% declining
                return DecayPattern.LINEAR_DECLINE, min(0.95, decline_ratio + 0.2)

        # Check for exponential decay
        if len(overall_scores) >= 10:
            # Fit exponential decay model
            try:
                # Simple exponential check: later values decay faster
                early_mean = statistics.mean(overall_scores[: len(overall_scores) // 2])
                late_mean = statistics.mean(overall_scores[len(overall_scores) // 2 :])

                if early_mean > late_mean:
                    decay_rate = (early_mean - late_mean) / early_mean
                    if decay_rate > 0.2:  # 20% decay
                        return DecayPattern.EXPONENTIAL_DECAY, min(0.9, decay_rate * 2)
            except Exception:
                pass

        # Check for cyclical degradation
        if len(overall_scores) >= 20:
            try:
                # Use basic periodicity detection
                autocorr = np.correlate(overall_scores, overall_scores, mode="full")
                mid = len(autocorr) // 2
                peaks = signal.find_peaks(autocorr[mid:], height=max(autocorr) * 0.3)[0]

                if len(peaks) >= 2:
                    # Check if overall trend is still declining
                    if trend_slope < -0.005:
                        return DecayPattern.CYCLICAL_DEGRADATION, 0.7
            except Exception:
                pass

        # Check for plateau then decline
        if len(overall_scores) >= 15:
            mid_point = len(overall_scores) // 2
            early_section = overall_scores[:mid_point]
            late_section = overall_scores[mid_point:]

            early_slope = self._calculate_trend_slope(
                [p.timestamp for p in points[:mid_point]], early_section
            )
            late_slope = self._calculate_trend_slope(
                [p.timestamp for p in points[mid_point:]], late_section
            )

            # Plateau (flat) then decline
            if abs(early_slope) < 0.002 and late_slope < -0.01:
                return DecayPattern.PLATEAU_THEN_DECLINE, 0.8

        # Check for oscillating decline
        volatility = stats.get("volatility", 0.0)
        if volatility > 0.05 and trend_slope < -0.005:
            return DecayPattern.OSCILLATING_DECLINE, 0.6

        # Default to random noise if no clear pattern
        return DecayPattern.RANDOM_NOISE, 0.3

    async def _calculate_decay_severity(
        self,
        points: List[QualityTrendPoint],
        pattern: DecayPattern,
        stats: Dict[str, float],
    ) -> float:
        """Calculate severity of detected decay.

        Args:
            points: Quality trend points
            pattern: Detected decay pattern
            stats: Statistical analysis results

        Returns:
            Severity score (0.0 to 1.0)
        """
        if len(points) < 2:
            return 0.0

        # Base severity on magnitude of decline
        first_score = points[0].overall_score
        last_score = points[-1].overall_score

        if first_score <= 0.001:
            return 0.0

        decline_percentage = (first_score - last_score) / first_score

        # Apply pattern-specific multipliers
        pattern_multipliers = {
            DecayPattern.SUDDEN_DROP: 1.5,
            DecayPattern.EXPONENTIAL_DECAY: 1.3,
            DecayPattern.LINEAR_DECLINE: 1.0,
            DecayPattern.CYCLICAL_DEGRADATION: 0.8,
            DecayPattern.PLATEAU_THEN_DECLINE: 1.1,
            DecayPattern.OSCILLATING_DECLINE: 0.9,
            DecayPattern.RANDOM_NOISE: 0.3,
        }

        base_severity = decline_percentage * pattern_multipliers.get(pattern, 1.0)

        # Adjust for velocity of decline
        trend_slope = abs(stats.get("overall_trend_slope", 0.0))
        velocity_multiplier = min(2.0, 1.0 + trend_slope * 50)

        # Adjust for volatility (higher volatility = more concerning)
        volatility = stats.get("volatility", 0.0)
        volatility_multiplier = 1.0 + min(0.5, volatility * 10)

        # Adjust for affected dimensions
        dimension_count = 0
        dimension_severity = 0.0

        if len(points) >= 2:
            if points[-1].integrity_score < points[0].integrity_score:
                dimension_count += 1
                dimension_severity += (
                    points[0].integrity_score - points[-1].integrity_score
                ) / max(points[0].integrity_score, 0.001)

            if points[-1].trust_score < points[0].trust_score:
                dimension_count += 1
                dimension_severity += (
                    points[0].trust_score - points[-1].trust_score
                ) / max(points[0].trust_score, 0.001)

        dimension_multiplier = (
            1.0 + (dimension_count * 0.2) + (dimension_severity * 0.3)
        )

        # Calculate final severity
        final_severity = (
            base_severity
            * velocity_multiplier
            * volatility_multiplier
            * dimension_multiplier
        )

        return min(1.0, max(0.0, final_severity))

    async def _estimate_time_to_critical(
        self, points: List[QualityTrendPoint], pattern: DecayPattern, severity: float
    ) -> Optional[timedelta]:
        """Estimate time until quality reaches critical levels.

        Args:
            points: Quality trend points
            pattern: Detected decay pattern
            severity: Current severity score

        Returns:
            Estimated time to critical failure or None
        """
        if severity < 0.3 or len(points) < 3:
            return None

        current_score = points[-1].overall_score
        critical_threshold = 0.3  # Below 30% is critical

        if current_score <= critical_threshold:
            return timedelta(0)  # Already critical

        # Calculate decline rate based on pattern
        if pattern == DecayPattern.LINEAR_DECLINE:
            # Linear extrapolation
            timestamps = [p.timestamp for p in points]
            scores = [p.overall_score for p in points]
            slope = self._calculate_trend_slope(timestamps, scores)

            if slope >= 0:
                return None  # Not declining

            hours_to_critical = (current_score - critical_threshold) / abs(slope)
            return timedelta(hours=hours_to_critical)

        elif pattern == DecayPattern.EXPONENTIAL_DECAY:
            # Exponential extrapolation
            if len(points) >= 5:
                recent_points = points[-5:]
                decay_rates = []

                for i in range(1, len(recent_points)):
                    if recent_points[i - 1].overall_score > 0.001:
                        rate = (
                            recent_points[i].overall_score
                            - recent_points[i - 1].overall_score
                        ) / recent_points[i - 1].overall_score
                        decay_rates.append(rate)

                if decay_rates:
                    avg_decay_rate = statistics.mean(decay_rates)
                    if avg_decay_rate < 0:
                        # Estimate time for exponential decay to reach threshold
                        periods_to_critical = np.log(
                            critical_threshold / current_score
                        ) / np.log(1 + avg_decay_rate)

                        # Estimate time per period (average time between points)
                        if len(recent_points) > 1:
                            time_diffs = [
                                (
                                    recent_points[i].timestamp
                                    - recent_points[i - 1].timestamp
                                ).total_seconds()
                                / 3600
                                for i in range(1, len(recent_points))
                            ]
                            avg_period_hours = statistics.mean(time_diffs)

                            total_hours = periods_to_critical * avg_period_hours
                            return timedelta(hours=max(1, total_hours))

        elif pattern == DecayPattern.SUDDEN_DROP:
            # For sudden drops, estimate based on recent volatility
            if severity > 0.8:
                return timedelta(hours=24)  # Very soon for high severity sudden drops
            else:
                return timedelta(days=7)  # Give more time for lower severity

        # Default estimation based on severity
        severity_to_hours = {
            0.9: 12,  # 12 hours
            0.8: 24,  # 1 day
            0.7: 72,  # 3 days
            0.6: 168,  # 1 week
            0.5: 336,  # 2 weeks
        }

        for threshold, hours in sorted(severity_to_hours.items(), reverse=True):
            if severity >= threshold:
                return timedelta(hours=hours)

        return timedelta(days=30)  # Default to 30 days

    async def _identify_affected_dimensions(
        self, points: List[QualityTrendPoint], stats: Dict[str, float]
    ) -> List[str]:
        """Identify which quality dimensions are affected by decay.

        Args:
            points: Quality trend points
            stats: Statistical analysis results

        Returns:
            List of affected quality dimension names
        """
        affected = []

        if len(points) < 2:
            return affected

        # Check each dimension for decline
        first_point = points[0]
        last_point = points[-1]

        decline_threshold = 0.05  # 5% decline threshold

        dimensions_to_check = [
            ("integrity_score", "integrity"),
            ("trust_score", "trust"),
            ("complexity_score", "complexity"),
            ("diversity_score", "diversity"),
            ("verification_ratio", "verification"),
        ]

        for attr_name, dimension_name in dimensions_to_check:
            first_value = getattr(first_point, attr_name, 0.0)
            last_value = getattr(last_point, attr_name, 0.0)

            if first_value > 0.001:
                decline = (first_value - last_value) / first_value
                if decline > decline_threshold:
                    affected.append(dimension_name)

        # Check overall score
        if first_point.overall_score > 0.001:
            overall_decline = (
                first_point.overall_score - last_point.overall_score
            ) / first_point.overall_score
            if overall_decline > decline_threshold and "overall" not in affected:
                affected.append("overall")

        return affected

    async def _generate_remediation_recommendations(
        self, pattern: DecayPattern, severity: float, affected_dimensions: List[str]
    ) -> List[RemediationStrategy]:
        """Generate recommended remediation strategies.

        Args:
            pattern: Detected decay pattern
            severity: Severity score
            affected_dimensions: Affected quality dimensions

        Returns:
            List of recommended remediation strategies
        """
        recommendations = []

        # Emergency measures for critical situations
        if severity > 0.9:
            recommendations.append(RemediationStrategy.EMERGENCY_LOCKDOWN)

        # Pattern-specific recommendations
        if pattern == DecayPattern.SUDDEN_DROP:
            recommendations.extend(
                [
                    RemediationStrategy.SYSTEM_PARAMETER_TUNING,
                    RemediationStrategy.CONTENT_FILTERING,
                    RemediationStrategy.COMMUNITY_INTERVENTION,
                ]
            )

        elif pattern == DecayPattern.LINEAR_DECLINE:
            recommendations.extend(
                [
                    RemediationStrategy.ECONOMIC_INCENTIVES,
                    RemediationStrategy.AUTOMATED_OPTIMIZATION,
                    RemediationStrategy.AGENT_RETRAINING,
                ]
            )

        elif pattern == DecayPattern.EXPONENTIAL_DECAY:
            recommendations.extend(
                [
                    RemediationStrategy.EMERGENCY_LOCKDOWN
                    if severity > 0.8
                    else RemediationStrategy.SYSTEM_PARAMETER_TUNING,
                    RemediationStrategy.ECONOMIC_INCENTIVES,
                    RemediationStrategy.CONTENT_FILTERING,
                ]
            )

        # Dimension-specific recommendations
        if "trust" in affected_dimensions:
            recommendations.extend(
                [
                    RemediationStrategy.ECONOMIC_INCENTIVES,
                    RemediationStrategy.COMMUNITY_INTERVENTION,
                ]
            )

        if "integrity" in affected_dimensions or "verification" in affected_dimensions:
            recommendations.extend(
                [
                    RemediationStrategy.CONTENT_FILTERING,
                    RemediationStrategy.SYSTEM_PARAMETER_TUNING,
                ]
            )

        if "diversity" in affected_dimensions:
            recommendations.extend(
                [
                    RemediationStrategy.AGENT_RETRAINING,
                    RemediationStrategy.ECONOMIC_INCENTIVES,
                ]
            )

        # Severity-based recommendations
        if severity > 0.7:
            if RemediationStrategy.AUTOMATED_OPTIMIZATION not in recommendations:
                recommendations.append(RemediationStrategy.AUTOMATED_OPTIMIZATION)

        if severity > 0.5:
            if RemediationStrategy.ECONOMIC_INCENTIVES not in recommendations:
                recommendations.append(RemediationStrategy.ECONOMIC_INCENTIVES)

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        return unique_recommendations[:5]  # Limit to top 5 recommendations

    def _calculate_capsule_delta(self) -> int:
        """Calculate change in capsule count since last measurement."""
        if len(self.quality_history) < 2:
            return 0

        current_length = (
            self.quality_history[-1].chain_length if self.quality_history else 0
        )
        previous_length = (
            self.quality_history[-2].chain_length
            if len(self.quality_history) > 1
            else 0
        )

        return current_length - previous_length

    async def _trigger_decay_alert(self, result: DecayDetectionResult):
        """Trigger alerts for detected quality decay.

        Args:
            result: Decay detection result
        """
        # Determine alert level
        if result.severity_score > 0.9:
            alert_level = QualityAlert.EMERGENCY
        elif result.severity_score > 0.7:
            alert_level = QualityAlert.CRITICAL
        elif result.severity_score > 0.5:
            alert_level = QualityAlert.WARNING
        else:
            alert_level = QualityAlert.INFO

        # Create alert message
        message = f"Quality decay detected: {result.decay_pattern.value} (severity: {result.severity_score:.2f})"

        # Add time to critical if available
        if result.time_to_critical:
            if result.time_to_critical.total_seconds() < 3600:  # Less than 1 hour
                message += f" - CRITICAL: {result.time_to_critical.total_seconds() / 60:.0f} minutes to failure"
            elif result.time_to_critical.days > 0:
                message += f" - Est. {result.time_to_critical.days} days to critical"
            else:
                message += f" - Est. {result.time_to_critical.total_seconds() / 3600:.1f} hours to critical"

        # Create alert data
        alert_data = {
            "pattern": result.decay_pattern.value,
            "severity": result.severity_score,
            "confidence": result.confidence,
            "affected_dimensions": result.affected_dimensions,
            "recommended_actions": [
                action.value for action in result.recommended_actions
            ],
            "time_to_critical": result.time_to_critical.total_seconds()
            if result.time_to_critical
            else None,
        }

        # Store in alert history
        self.alert_history.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": alert_level.value,
                "message": message,
                "data": alert_data,
            }
        )

        # Call registered alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_level, message, alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

        logger.warning(f"Quality decay alert [{alert_level.value}]: {message}")

    async def _estimate_remediation_effectiveness(
        self, strategy: RemediationStrategy, dimensions: List[str]
    ) -> float:
        """Estimate effectiveness of a remediation strategy.

        Args:
            strategy: Remediation strategy
            dimensions: Target dimensions

        Returns:
            Expected effectiveness (0.0 to 1.0)
        """
        # Base effectiveness by strategy
        base_effectiveness = {
            RemediationStrategy.ECONOMIC_INCENTIVES: 0.6,
            RemediationStrategy.AUTOMATED_OPTIMIZATION: 0.7,
            RemediationStrategy.COMMUNITY_INTERVENTION: 0.5,
            RemediationStrategy.SYSTEM_PARAMETER_TUNING: 0.8,
            RemediationStrategy.CONTENT_FILTERING: 0.7,
            RemediationStrategy.AGENT_RETRAINING: 0.6,
            RemediationStrategy.EMERGENCY_LOCKDOWN: 0.9,
        }

        base = base_effectiveness.get(strategy, 0.5)

        # Adjust based on historical effectiveness
        if strategy in self.remediation_effectiveness:
            historical = self.remediation_effectiveness[strategy]
            base = (base + historical) / 2  # Average with historical

        # Adjust based on dimensions
        if dimensions:
            dimension_bonus = min(0.2, len(dimensions) * 0.05)
            base += dimension_bonus

        return min(1.0, base)

    async def _calculate_remediation_cost(
        self, strategy: RemediationStrategy, dimensions: List[str]
    ) -> float:
        """Calculate cost of implementing a remediation strategy.

        Args:
            strategy: Remediation strategy
            dimensions: Target dimensions

        Returns:
            Estimated cost
        """
        # Base cost by strategy
        base_costs = {
            RemediationStrategy.ECONOMIC_INCENTIVES: 100.0,
            RemediationStrategy.AUTOMATED_OPTIMIZATION: 50.0,
            RemediationStrategy.COMMUNITY_INTERVENTION: 25.0,
            RemediationStrategy.SYSTEM_PARAMETER_TUNING: 10.0,
            RemediationStrategy.CONTENT_FILTERING: 30.0,
            RemediationStrategy.AGENT_RETRAINING: 75.0,
            RemediationStrategy.EMERGENCY_LOCKDOWN: 200.0,
        }

        base_cost = base_costs.get(strategy, 50.0)

        # Adjust based on scope (number of dimensions)
        if dimensions:
            scope_multiplier = 1.0 + (len(dimensions) * 0.3)
            base_cost *= scope_multiplier

        return base_cost

    async def _execute_remediation_strategy(self, action: RemediationAction) -> bool:
        """Execute a specific remediation strategy.

        Args:
            action: Remediation action to execute

        Returns:
            True if successful
        """
        try:
            strategy = action.strategy

            if strategy == RemediationStrategy.ECONOMIC_INCENTIVES:
                # Increase quality bonuses and penalties
                if self.economic_engine:
                    # Increase dividend rate temporarily
                    current_rate = self.economic_engine.dividend_rate
                    new_rate = min(current_rate * 1.5, 0.15)  # Cap at 15%
                    self.economic_engine.set_dividend_rate(new_rate)

                    # Add bonus to treasury to fund increased dividends
                    bonus_amount = action.cost
                    self.economic_engine.update_treasury(
                        bonus_amount, f"Quality improvement bonus - {action.action_id}"
                    )

                    action.metadata["old_dividend_rate"] = float(current_rate)
                    action.metadata["new_dividend_rate"] = float(new_rate)
                    action.metadata["treasury_bonus"] = float(bonus_amount)

                    logger.info(
                        f"Increased dividend rate from {current_rate:.3f} to {new_rate:.3f}"
                    )
                    return True

            elif strategy == RemediationStrategy.AUTOMATED_OPTIMIZATION:
                # Implement automated quality optimization
                # This could involve adjusting CQSS parameters, optimizing verification, etc.
                action.metadata["optimization_applied"] = True
                logger.info("Applied automated quality optimization")
                return True

            elif strategy == RemediationStrategy.SYSTEM_PARAMETER_TUNING:
                # Tune system parameters for better quality
                action.metadata["parameters_tuned"] = True
                logger.info("Tuned system parameters for quality improvement")
                return True

            elif strategy == RemediationStrategy.CONTENT_FILTERING:
                # Implement stricter content filtering
                action.metadata["filtering_enabled"] = True
                logger.info("Enabled enhanced content filtering")
                return True

            elif strategy == RemediationStrategy.COMMUNITY_INTERVENTION:
                # Alert community and request intervention
                action.metadata["community_alerted"] = True
                logger.info("Alerted community for quality intervention")
                return True

            elif strategy == RemediationStrategy.AGENT_RETRAINING:
                # Schedule agent retraining
                action.metadata["retraining_scheduled"] = True
                logger.info("Scheduled agent retraining for quality improvement")
                return True

            elif strategy == RemediationStrategy.EMERGENCY_LOCKDOWN:
                # Implement emergency measures
                action.metadata["lockdown_activated"] = True
                logger.warning("Activated emergency quality lockdown")
                return True

            else:
                logger.error(f"Unknown remediation strategy: {strategy}")
                return False

        except Exception as e:
            logger.error(
                f"Failed to execute remediation strategy {action.strategy}: {e}"
            )
            return False

    async def _evaluate_remediation_after_delay(
        self, action_id: str, delay_hours: int = 1
    ):
        """Evaluate remediation effectiveness after a delay.

        Args:
            action_id: ID of the remediation action
            delay_hours: Hours to wait before evaluation
        """
        await asyncio.sleep(delay_hours * 3600)  # Convert to seconds

        if action_id not in self.active_remediations:
            return

        action = self.active_remediations[action_id]

        try:
            # Get quality measurements before and after
            if len(self.quality_history) >= 2:
                # Find measurements around the action time
                action_time = action.timestamp

                # Get measurement before action (within 2 hours before)
                before_point = None
                for point in reversed(self.quality_history):
                    if (
                        point.timestamp < action_time
                        and (action_time - point.timestamp).seconds < 7200
                    ):
                        before_point = point
                        break

                # Get measurement after action (most recent)
                after_point = self.quality_history[-1] if self.quality_history else None

                if before_point and after_point and after_point.timestamp > action_time:
                    # Calculate actual improvement
                    before_score = before_point.overall_score
                    after_score = after_point.overall_score

                    actual_improvement = (after_score - before_score) / max(
                        before_score, 0.001
                    )
                    action.actual_improvement = actual_improvement

                    # Update effectiveness tracking
                    self.remediation_effectiveness[action.strategy] = (
                        self.remediation_effectiveness[action.strategy] * 0.8
                        + abs(actual_improvement) * 0.2
                    )

                    # Update cost tracking
                    if actual_improvement > 0:
                        cost_effectiveness = actual_improvement / max(action.cost, 1.0)
                        self.remediation_costs[action.strategy] = (
                            self.remediation_costs[action.strategy] * 0.8
                            + cost_effectiveness * 0.2
                        )

                    action.duration = datetime.now(timezone.utc) - action.timestamp

                    logger.info(
                        f"Remediation {action_id} evaluation: improvement={actual_improvement:.3f}"
                    )

            # Move to history
            self.remediation_history.append(action)
            del self.active_remediations[action_id]

        except Exception as e:
            logger.error(f"Failed to evaluate remediation {action_id}: {e}")

    def register_alert_callback(
        self, callback: Callable[[QualityAlert, str, Dict[str, Any]], None]
    ):
        """Register callback for quality decay alerts.

        Args:
            callback: Function to call when alerts are triggered
        """
        self.alert_callbacks.append(callback)

    def get_decay_statistics(self) -> Dict[str, Any]:
        """Get comprehensive decay detection statistics.

        Returns:
            Dictionary with decay detection metrics
        """
        total_measurements = len(self.quality_history)

        if not self.quality_history:
            return {"total_measurements": 0}

        # Calculate quality trend over full history
        first_point = self.quality_history[0]
        last_point = self.quality_history[-1]

        time_span = (
            last_point.timestamp - first_point.timestamp
        ).total_seconds() / 3600  # hours
        overall_change = last_point.overall_score - first_point.overall_score

        # Count alerts by severity
        alert_counts = defaultdict(int)
        for alert in self.alert_history:
            alert_counts[alert["level"]] += 1

        # Remediation statistics
        total_remediations = len(self.remediation_history) + len(
            self.active_remediations
        )
        successful_remediations = len(
            [r for r in self.remediation_history if r.success]
        )

        return {
            "total_measurements": total_measurements,
            "analysis_window_hours": self.trend_window_hours,
            "time_span_hours": round(time_span, 1),
            "overall_quality_change": round(overall_change, 3),
            "current_decay_detected": self.current_decay_state.decay_detected
            if self.current_decay_state
            else False,
            "current_severity": round(self.current_decay_state.severity_score, 2)
            if self.current_decay_state
            else 0.0,
            "current_pattern": self.current_decay_state.decay_pattern.value
            if self.current_decay_state
            else None,
            "alert_counts": dict(alert_counts),
            "total_alerts": len(self.alert_history),
            "total_remediations": total_remediations,
            "successful_remediations": successful_remediations,
            "active_remediations": len(self.active_remediations),
            "remediation_success_rate": (
                successful_remediations / max(1, len(self.remediation_history))
            )
            * 100,
            "remediation_effectiveness": {
                strategy.value: round(effectiveness, 3)
                for strategy, effectiveness in self.remediation_effectiveness.items()
            },
            "recent_quality_trend": [
                {
                    "timestamp": point.timestamp.isoformat(),
                    "overall_score": round(point.overall_score, 3),
                    "integrity_score": round(point.integrity_score, 3),
                    "trust_score": round(point.trust_score, 3),
                }
                for point in list(self.quality_history)[-10:]  # Last 10 points
            ],
        }


# Global quality decay detector instance
quality_decay_detector = QualityDecayDetector()
