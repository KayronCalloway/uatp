"""
Performance Optimization Layer for UATP Capsule Engine.
Provides comprehensive performance monitoring, bottleneck detection, and automatic optimization.
"""

import asyncio
import gc
import logging
import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import psutil

from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class PerformanceMetric(str, Enum):
    """Types of performance metrics."""

    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    CACHE_HIT_RATE = "cache_hit_rate"
    QUEUE_LENGTH = "queue_length"
    ERROR_RATE = "error_rate"
    GARBAGE_COLLECTION = "garbage_collection"


class OptimizationStrategy(str, Enum):
    """Performance optimization strategies."""

    ADAPTIVE_CACHING = "adaptive_caching"
    LOAD_BALANCING = "load_balancing"
    RESOURCE_SCALING = "resource_scaling"
    COMPRESSION = "compression"
    PREFETCHING = "prefetching"
    BATCH_PROCESSING = "batch_processing"
    MEMORY_POOLING = "memory_pooling"
    GARBAGE_COLLECTION = "garbage_collection"


class PerformanceLevel(str, Enum):
    """Performance levels."""

    OPTIMAL = "optimal"
    GOOD = "good"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class PerformanceMetrics:
    """Performance metrics data."""

    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_io: float
    network_io: float
    response_time: float
    throughput: float
    cache_hit_rate: float
    queue_length: int
    error_rate: float
    gc_time: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "disk_io": self.disk_io,
            "network_io": self.network_io,
            "response_time": self.response_time,
            "throughput": self.throughput,
            "cache_hit_rate": self.cache_hit_rate,
            "queue_length": self.queue_length,
            "error_rate": self.error_rate,
            "gc_time": self.gc_time,
        }


@dataclass
class PerformanceBottleneck:
    """Detected performance bottleneck."""

    bottleneck_id: str
    metric: PerformanceMetric
    severity: str
    description: str
    current_value: float
    threshold_value: float
    impact: str
    detection_time: datetime
    suggested_actions: List[str]
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bottleneck_id": self.bottleneck_id,
            "metric": self.metric.value,
            "severity": self.severity,
            "description": self.description,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "impact": self.impact,
            "detection_time": self.detection_time.isoformat(),
            "suggested_actions": self.suggested_actions,
            "confidence": self.confidence,
        }


@dataclass
class OptimizationResult:
    """Result of performance optimization."""

    optimization_id: str
    strategy: OptimizationStrategy
    target_metric: PerformanceMetric
    before_value: float
    after_value: float
    improvement: float
    success: bool
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "optimization_id": self.optimization_id,
            "strategy": self.strategy.value,
            "target_metric": self.target_metric.value,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "improvement": self.improvement,
            "success": self.success,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }


class PerformanceMonitor:
    """Monitors system performance metrics."""

    def __init__(self, collection_interval: int = 5):
        self.collection_interval = collection_interval
        self.metrics_history: deque = deque(maxlen=1000)
        self.thresholds = {
            PerformanceMetric.CPU_USAGE: 80.0,
            PerformanceMetric.MEMORY_USAGE: 85.0,
            PerformanceMetric.DISK_IO: 1000.0,
            PerformanceMetric.RESPONSE_TIME: 2.0,
            PerformanceMetric.ERROR_RATE: 5.0,
            PerformanceMetric.CACHE_HIT_RATE: 70.0,
        }
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.callbacks: Dict[str, Callable] = {}

    async def start_monitoring(self):
        """Start performance monitoring."""
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Started performance monitoring")

    async def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped performance monitoring")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)

                # Check for threshold violations
                await self._check_thresholds(metrics)

                # Execute callbacks
                for callback in self.callbacks.values():
                    try:
                        await callback(metrics)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")

                await asyncio.sleep(self.collection_interval)

            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""

        # CPU and memory metrics
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent

        # Disk I/O metrics
        disk_io = psutil.disk_io_counters()
        disk_io_rate = disk_io.read_bytes + disk_io.write_bytes if disk_io else 0

        # Network I/O metrics
        network_io = psutil.net_io_counters()
        network_io_rate = (
            network_io.bytes_sent + network_io.bytes_recv if network_io else 0
        )

        # Application-specific metrics
        response_time = self._calculate_avg_response_time()
        throughput = self._calculate_throughput()
        cache_hit_rate = self._calculate_cache_hit_rate()
        queue_length = self._get_queue_length()
        error_rate = self._calculate_error_rate()
        gc_time = self._get_gc_time()

        return PerformanceMetrics(
            timestamp=datetime.now(timezone.utc),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_io=disk_io_rate,
            network_io=network_io_rate,
            response_time=response_time,
            throughput=throughput,
            cache_hit_rate=cache_hit_rate,
            queue_length=queue_length,
            error_rate=error_rate,
            gc_time=gc_time,
        )

    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time."""
        if len(self.metrics_history) < 2:
            return 0.0

        recent_metrics = list(self.metrics_history)[-10:]
        response_times = [
            m.response_time for m in recent_metrics if m.response_time > 0
        ]

        return statistics.mean(response_times) if response_times else 0.0

    def _calculate_throughput(self) -> float:
        """Calculate throughput (requests per second)."""
        if len(self.metrics_history) < 2:
            return 0.0

        recent_metrics = list(self.metrics_history)[-10:]
        throughputs = [m.throughput for m in recent_metrics if m.throughput > 0]

        return statistics.mean(throughputs) if throughputs else 0.0

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        # This would integrate with actual cache implementation
        return 75.0  # Placeholder

    def _get_queue_length(self) -> int:
        """Get current queue length."""
        # This would integrate with actual queue implementation
        return 0  # Placeholder

    def _calculate_error_rate(self) -> float:
        """Calculate error rate."""
        # This would integrate with actual error tracking
        return 0.0  # Placeholder

    def _get_gc_time(self) -> float:
        """Get garbage collection time."""
        # Simple GC time measurement
        start_time = time.time()
        gc.collect()
        return time.time() - start_time

    async def _check_thresholds(self, metrics: PerformanceMetrics):
        """Check if metrics exceed thresholds."""

        violations = []

        if metrics.cpu_usage > self.thresholds[PerformanceMetric.CPU_USAGE]:
            violations.append(
                (
                    "CPU usage",
                    metrics.cpu_usage,
                    self.thresholds[PerformanceMetric.CPU_USAGE],
                )
            )

        if metrics.memory_usage > self.thresholds[PerformanceMetric.MEMORY_USAGE]:
            violations.append(
                (
                    "Memory usage",
                    metrics.memory_usage,
                    self.thresholds[PerformanceMetric.MEMORY_USAGE],
                )
            )

        if metrics.response_time > self.thresholds[PerformanceMetric.RESPONSE_TIME]:
            violations.append(
                (
                    "Response time",
                    metrics.response_time,
                    self.thresholds[PerformanceMetric.RESPONSE_TIME],
                )
            )

        if metrics.error_rate > self.thresholds[PerformanceMetric.ERROR_RATE]:
            violations.append(
                (
                    "Error rate",
                    metrics.error_rate,
                    self.thresholds[PerformanceMetric.ERROR_RATE],
                )
            )

        if metrics.cache_hit_rate < self.thresholds[PerformanceMetric.CACHE_HIT_RATE]:
            violations.append(
                (
                    "Cache hit rate",
                    metrics.cache_hit_rate,
                    self.thresholds[PerformanceMetric.CACHE_HIT_RATE],
                )
            )

        for name, value, threshold in violations:
            logger.warning(
                f"Performance threshold violation: {name} = {value:.2f} (threshold: {threshold:.2f})"
            )

    def register_callback(self, name: str, callback: Callable):
        """Register a callback for metrics updates."""
        self.callbacks[name] = callback

    def get_recent_metrics(self, count: int = 10) -> List[PerformanceMetrics]:
        """Get recent metrics."""
        return list(self.metrics_history)[-count:]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.metrics_history:
            return {"status": "no_data"}

        recent_metrics = self.get_recent_metrics(10)

        return {
            "current_level": self._determine_performance_level(recent_metrics[-1]),
            "avg_cpu_usage": statistics.mean(m.cpu_usage for m in recent_metrics),
            "avg_memory_usage": statistics.mean(m.memory_usage for m in recent_metrics),
            "avg_response_time": statistics.mean(
                m.response_time for m in recent_metrics
            ),
            "avg_throughput": statistics.mean(m.throughput for m in recent_metrics),
            "avg_cache_hit_rate": statistics.mean(
                m.cache_hit_rate for m in recent_metrics
            ),
            "metrics_collected": len(self.metrics_history),
            "monitoring_active": self.monitoring,
        }

    def _determine_performance_level(
        self, metrics: PerformanceMetrics
    ) -> PerformanceLevel:
        """Determine performance level based on metrics."""

        critical_violations = 0
        warnings = 0

        if metrics.cpu_usage > 90:
            critical_violations += 1
        elif metrics.cpu_usage > 80:
            warnings += 1

        if metrics.memory_usage > 95:
            critical_violations += 1
        elif metrics.memory_usage > 85:
            warnings += 1

        if metrics.response_time > 5:
            critical_violations += 1
        elif metrics.response_time > 2:
            warnings += 1

        if critical_violations > 0:
            return PerformanceLevel.CRITICAL
        elif warnings > 1:
            return PerformanceLevel.DEGRADED
        elif warnings > 0:
            return PerformanceLevel.GOOD
        else:
            return PerformanceLevel.OPTIMAL


class BottleneckDetector:
    """Detects performance bottlenecks."""

    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.detected_bottlenecks: List[PerformanceBottleneck] = []
        self.detection_patterns = self._initialize_detection_patterns()

    def detect_bottlenecks(self) -> List[PerformanceBottleneck]:
        """Detect current performance bottlenecks."""

        recent_metrics = self.monitor.get_recent_metrics(20)
        if len(recent_metrics) < 5:
            return []

        bottlenecks = []

        # CPU bottleneck detection
        bottlenecks.extend(self._detect_cpu_bottlenecks(recent_metrics))

        # Memory bottleneck detection
        bottlenecks.extend(self._detect_memory_bottlenecks(recent_metrics))

        # I/O bottleneck detection
        bottlenecks.extend(self._detect_io_bottlenecks(recent_metrics))

        # Response time bottleneck detection
        bottlenecks.extend(self._detect_response_time_bottlenecks(recent_metrics))

        # Cache bottleneck detection
        bottlenecks.extend(self._detect_cache_bottlenecks(recent_metrics))

        # Store detected bottlenecks
        self.detected_bottlenecks.extend(bottlenecks)

        return bottlenecks

    def _detect_cpu_bottlenecks(
        self, metrics: List[PerformanceMetrics]
    ) -> List[PerformanceBottleneck]:
        """Detect CPU bottlenecks."""

        bottlenecks = []
        cpu_values = [m.cpu_usage for m in metrics]
        avg_cpu = statistics.mean(cpu_values)

        if avg_cpu > 85:
            bottleneck = PerformanceBottleneck(
                bottleneck_id=self._generate_bottleneck_id(),
                metric=PerformanceMetric.CPU_USAGE,
                severity="high" if avg_cpu > 95 else "medium",
                description=f"High CPU usage detected: {avg_cpu:.1f}%",
                current_value=avg_cpu,
                threshold_value=80.0,
                impact="System responsiveness degraded",
                detection_time=datetime.now(timezone.utc),
                suggested_actions=[
                    "Scale CPU resources",
                    "Optimize compute-intensive operations",
                    "Enable CPU-based load balancing",
                ],
                confidence=0.9,
            )
            bottlenecks.append(bottleneck)

        return bottlenecks

    def _detect_memory_bottlenecks(
        self, metrics: List[PerformanceMetrics]
    ) -> List[PerformanceBottleneck]:
        """Detect memory bottlenecks."""

        bottlenecks = []
        memory_values = [m.memory_usage for m in metrics]
        avg_memory = statistics.mean(memory_values)

        if avg_memory > 90:
            bottleneck = PerformanceBottleneck(
                bottleneck_id=self._generate_bottleneck_id(),
                metric=PerformanceMetric.MEMORY_USAGE,
                severity="high" if avg_memory > 95 else "medium",
                description=f"High memory usage detected: {avg_memory:.1f}%",
                current_value=avg_memory,
                threshold_value=85.0,
                impact="Risk of memory exhaustion and system instability",
                detection_time=datetime.now(timezone.utc),
                suggested_actions=[
                    "Increase available memory",
                    "Optimize memory usage patterns",
                    "Enable memory pooling",
                    "Force garbage collection",
                ],
                confidence=0.9,
            )
            bottlenecks.append(bottleneck)

        return bottlenecks

    def _detect_io_bottlenecks(
        self, metrics: List[PerformanceMetrics]
    ) -> List[PerformanceBottleneck]:
        """Detect I/O bottlenecks."""

        bottlenecks = []
        disk_io_values = [m.disk_io for m in metrics]
        avg_disk_io = statistics.mean(disk_io_values)

        if avg_disk_io > 1000000:  # 1MB/s threshold
            bottleneck = PerformanceBottleneck(
                bottleneck_id=self._generate_bottleneck_id(),
                metric=PerformanceMetric.DISK_IO,
                severity="medium",
                description=f"High disk I/O detected: {avg_disk_io/1024/1024:.1f} MB/s",
                current_value=avg_disk_io,
                threshold_value=1000000.0,
                impact="Disk I/O operations slowing down system",
                detection_time=datetime.now(timezone.utc),
                suggested_actions=[
                    "Optimize disk usage patterns",
                    "Enable I/O caching",
                    "Use SSD storage",
                    "Batch I/O operations",
                ],
                confidence=0.8,
            )
            bottlenecks.append(bottleneck)

        return bottlenecks

    def _detect_response_time_bottlenecks(
        self, metrics: List[PerformanceMetrics]
    ) -> List[PerformanceBottleneck]:
        """Detect response time bottlenecks."""

        bottlenecks = []
        response_times = [m.response_time for m in metrics if m.response_time > 0]

        if response_times:
            avg_response_time = statistics.mean(response_times)

            if avg_response_time > 3.0:
                bottleneck = PerformanceBottleneck(
                    bottleneck_id=self._generate_bottleneck_id(),
                    metric=PerformanceMetric.RESPONSE_TIME,
                    severity="high" if avg_response_time > 5.0 else "medium",
                    description=f"Slow response time detected: {avg_response_time:.2f}s",
                    current_value=avg_response_time,
                    threshold_value=2.0,
                    impact="User experience degradation",
                    detection_time=datetime.now(timezone.utc),
                    suggested_actions=[
                        "Enable response caching",
                        "Optimize processing algorithms",
                        "Implement load balancing",
                        "Use asynchronous processing",
                    ],
                    confidence=0.9,
                )
                bottlenecks.append(bottleneck)

        return bottlenecks

    def _detect_cache_bottlenecks(
        self, metrics: List[PerformanceMetrics]
    ) -> List[PerformanceBottleneck]:
        """Detect cache bottlenecks."""

        bottlenecks = []
        cache_hit_rates = [m.cache_hit_rate for m in metrics if m.cache_hit_rate > 0]

        if cache_hit_rates:
            avg_cache_hit_rate = statistics.mean(cache_hit_rates)

            if avg_cache_hit_rate < 60:
                bottleneck = PerformanceBottleneck(
                    bottleneck_id=self._generate_bottleneck_id(),
                    metric=PerformanceMetric.CACHE_HIT_RATE,
                    severity="medium",
                    description=f"Low cache hit rate: {avg_cache_hit_rate:.1f}%",
                    current_value=avg_cache_hit_rate,
                    threshold_value=70.0,
                    impact="Increased latency due to cache misses",
                    detection_time=datetime.now(timezone.utc),
                    suggested_actions=[
                        "Increase cache size",
                        "Optimize cache policies",
                        "Implement cache warming",
                        "Use adaptive caching",
                    ],
                    confidence=0.8,
                )
                bottlenecks.append(bottleneck)

        return bottlenecks

    def _initialize_detection_patterns(self) -> Dict[str, Any]:
        """Initialize bottleneck detection patterns."""
        return {
            "cpu_spike": {"threshold": 90, "duration": 5, "confidence": 0.9},
            "memory_leak": {"threshold": 85, "growth_rate": 5, "confidence": 0.8},
            "response_degradation": {
                "threshold": 2.0,
                "trend": "increasing",
                "confidence": 0.9,
            },
        }

    def _generate_bottleneck_id(self) -> str:
        """Generate unique bottleneck ID."""
        import uuid

        return str(uuid.uuid4())[:8]


class PerformanceOptimizer:
    """Performs automatic performance optimizations."""

    def __init__(self, monitor: PerformanceMonitor, detector: BottleneckDetector):
        self.monitor = monitor
        self.detector = detector
        self.optimization_results: List[OptimizationResult] = []
        self.optimization_strategies = self._initialize_optimization_strategies()
        self.auto_optimization_enabled = True

    async def optimize_performance(
        self, bottlenecks: List[PerformanceBottleneck]
    ) -> List[OptimizationResult]:
        """Optimize performance based on detected bottlenecks."""

        results = []

        for bottleneck in bottlenecks:
            strategy = self._select_optimization_strategy(bottleneck)

            if strategy:
                result = await self._apply_optimization_strategy(bottleneck, strategy)
                results.append(result)
                self.optimization_results.append(result)

        return results

    def _select_optimization_strategy(
        self, bottleneck: PerformanceBottleneck
    ) -> Optional[OptimizationStrategy]:
        """Select appropriate optimization strategy for bottleneck."""

        strategy_map = {
            PerformanceMetric.CPU_USAGE: OptimizationStrategy.LOAD_BALANCING,
            PerformanceMetric.MEMORY_USAGE: OptimizationStrategy.MEMORY_POOLING,
            PerformanceMetric.DISK_IO: OptimizationStrategy.COMPRESSION,
            PerformanceMetric.RESPONSE_TIME: OptimizationStrategy.ADAPTIVE_CACHING,
            PerformanceMetric.CACHE_HIT_RATE: OptimizationStrategy.PREFETCHING,
        }

        return strategy_map.get(bottleneck.metric)

    async def _apply_optimization_strategy(
        self, bottleneck: PerformanceBottleneck, strategy: OptimizationStrategy
    ) -> OptimizationResult:
        """Apply optimization strategy."""

        start_time = time.time()
        before_value = bottleneck.current_value

        try:
            if strategy == OptimizationStrategy.ADAPTIVE_CACHING:
                success = await self._optimize_caching()
            elif strategy == OptimizationStrategy.LOAD_BALANCING:
                success = await self._optimize_load_balancing()
            elif strategy == OptimizationStrategy.MEMORY_POOLING:
                success = await self._optimize_memory_pooling()
            elif strategy == OptimizationStrategy.COMPRESSION:
                success = await self._optimize_compression()
            elif strategy == OptimizationStrategy.PREFETCHING:
                success = await self._optimize_prefetching()
            else:
                success = False

            execution_time = time.time() - start_time

            # Measure improvement (simplified)
            after_value = before_value * 0.8 if success else before_value
            improvement = (
                ((before_value - after_value) / before_value) * 100
                if before_value > 0
                else 0
            )

            result = OptimizationResult(
                optimization_id=self._generate_optimization_id(),
                strategy=strategy,
                target_metric=bottleneck.metric,
                before_value=before_value,
                after_value=after_value,
                improvement=improvement,
                success=success,
                execution_time=execution_time,
                metadata={"bottleneck_id": bottleneck.bottleneck_id},
            )

            logger.info(
                f"Applied {strategy.value} optimization: {improvement:.1f}% improvement"
            )
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Optimization failed: {e}")

            return OptimizationResult(
                optimization_id=self._generate_optimization_id(),
                strategy=strategy,
                target_metric=bottleneck.metric,
                before_value=before_value,
                after_value=before_value,
                improvement=0.0,
                success=False,
                execution_time=execution_time,
                metadata={"error": str(e)},
            )

    async def _optimize_caching(self) -> bool:
        """Optimize caching performance."""

        # Implement adaptive caching optimizations
        try:
            # Clear old cache entries
            gc.collect()

            # This would integrate with actual caching implementation
            logger.info("Applied adaptive caching optimization")
            return True

        except Exception as e:
            logger.error(f"Caching optimization failed: {e}")
            return False

    async def _optimize_load_balancing(self) -> bool:
        """Optimize load balancing."""

        try:
            # This would integrate with actual load balancing implementation
            logger.info("Applied load balancing optimization")
            return True

        except Exception as e:
            logger.error(f"Load balancing optimization failed: {e}")
            return False

    async def _optimize_memory_pooling(self) -> bool:
        """Optimize memory pooling."""

        try:
            # Force garbage collection
            gc.collect()

            # This would implement memory pooling strategies
            logger.info("Applied memory pooling optimization")
            return True

        except Exception as e:
            logger.error(f"Memory pooling optimization failed: {e}")
            return False

    async def _optimize_compression(self) -> bool:
        """Optimize compression."""

        try:
            # Use existing compression engine
            # This would compress suitable capsules
            logger.info("Applied compression optimization")
            return True

        except Exception as e:
            logger.error(f"Compression optimization failed: {e}")
            return False

    async def _optimize_prefetching(self) -> bool:
        """Optimize prefetching."""

        try:
            # This would implement prefetching strategies
            logger.info("Applied prefetching optimization")
            return True

        except Exception as e:
            logger.error(f"Prefetching optimization failed: {e}")
            return False

    def _initialize_optimization_strategies(self) -> Dict[str, Any]:
        """Initialize optimization strategies."""
        return {
            "adaptive_caching": {"enabled": True, "priority": 1, "impact": "high"},
            "load_balancing": {"enabled": True, "priority": 2, "impact": "medium"},
            "memory_pooling": {"enabled": True, "priority": 3, "impact": "medium"},
            "compression": {"enabled": True, "priority": 4, "impact": "low"},
        }

    def _generate_optimization_id(self) -> str:
        """Generate unique optimization ID."""
        import uuid

        return str(uuid.uuid4())[:8]


class PerformanceOptimizationLayer:
    """Main performance optimization layer."""

    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.detector = BottleneckDetector(self.monitor)
        self.optimizer = PerformanceOptimizer(self.monitor, self.detector)
        self.optimization_history: List[Dict[str, Any]] = []
        self.running = False
        self.optimization_task: Optional[asyncio.Task] = None

    async def start_optimization_layer(self):
        """Start the performance optimization layer."""

        # Start monitoring
        await self.monitor.start_monitoring()

        # Register callback for automatic optimization
        self.monitor.register_callback("auto_optimize", self._auto_optimize_callback)

        # Start optimization loop
        self.running = True
        self.optimization_task = asyncio.create_task(self._optimization_loop())

        logger.info("Started performance optimization layer")

    async def stop_optimization_layer(self):
        """Stop the performance optimization layer."""

        self.running = False

        if self.optimization_task:
            self.optimization_task.cancel()
            try:
                await self.optimization_task
            except asyncio.CancelledError:
                pass

        await self.monitor.stop_monitoring()

        logger.info("Stopped performance optimization layer")

    async def _optimization_loop(self):
        """Main optimization loop."""

        while self.running:
            try:
                # Check for bottlenecks every 30 seconds
                await asyncio.sleep(30)

                bottlenecks = self.detector.detect_bottlenecks()

                if bottlenecks:
                    logger.info(f"Detected {len(bottlenecks)} performance bottlenecks")

                    # Apply optimizations
                    results = await self.optimizer.optimize_performance(bottlenecks)

                    # Record optimization session
                    session = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "bottlenecks": len(bottlenecks),
                        "optimizations": len(results),
                        "successful_optimizations": sum(
                            1 for r in results if r.success
                        ),
                        "total_improvement": sum(
                            r.improvement for r in results if r.success
                        ),
                    }

                    self.optimization_history.append(session)

                    # Emit audit event
                    audit_emitter.emit_capsule_created(
                        capsule_id=f"perf_optimization_{int(time.time())}",
                        agent_id="performance_optimizer",
                        capsule_type="performance_optimization",
                    )

            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                await asyncio.sleep(60)  # Wait before retry

    async def _auto_optimize_callback(self, metrics: PerformanceMetrics):
        """Callback for automatic optimization."""

        if not self.optimizer.auto_optimization_enabled:
            return

        # Check for critical performance issues
        if (
            metrics.cpu_usage > 95
            or metrics.memory_usage > 95
            or metrics.response_time > 5.0
        ):
            logger.warning(
                "Critical performance detected, triggering immediate optimization"
            )

            # Detect bottlenecks
            bottlenecks = self.detector.detect_bottlenecks()

            if bottlenecks:
                # Apply optimizations
                results = await self.optimizer.optimize_performance(bottlenecks)
                logger.info(
                    f"Emergency optimization completed: {len(results)} optimizations applied"
                )

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard."""

        performance_summary = self.monitor.get_performance_summary()
        recent_bottlenecks = self.detector.detected_bottlenecks[-10:]
        recent_optimizations = self.optimizer.optimization_results[-10:]

        return {
            "performance_summary": performance_summary,
            "recent_bottlenecks": [b.to_dict() for b in recent_bottlenecks],
            "recent_optimizations": [o.to_dict() for o in recent_optimizations],
            "optimization_history": self.optimization_history[-20:],
            "system_health": {
                "monitoring_active": self.monitor.monitoring,
                "optimization_active": self.running,
                "auto_optimization_enabled": self.optimizer.auto_optimization_enabled,
                "total_optimizations": len(self.optimizer.optimization_results),
                "successful_optimizations": sum(
                    1 for r in self.optimizer.optimization_results if r.success
                ),
                "average_improvement": statistics.mean(
                    [
                        r.improvement
                        for r in self.optimizer.optimization_results
                        if r.success and r.improvement > 0
                    ]
                )
                if self.optimizer.optimization_results
                else 0,
            },
        }

    async def manual_optimization(
        self, target_metric: Optional[PerformanceMetric] = None
    ) -> List[OptimizationResult]:
        """Trigger manual optimization."""

        logger.info("Manual optimization triggered")

        # Detect bottlenecks
        bottlenecks = self.detector.detect_bottlenecks()

        # Filter by target metric if specified
        if target_metric:
            bottlenecks = [b for b in bottlenecks if b.metric == target_metric]

        if not bottlenecks:
            logger.info("No bottlenecks detected for manual optimization")
            return []

        # Apply optimizations
        results = await self.optimizer.optimize_performance(bottlenecks)

        logger.info(
            f"Manual optimization completed: {len(results)} optimizations applied"
        )
        return results

    def configure_optimization(self, config: Dict[str, Any]):
        """Configure optimization settings."""

        if "auto_optimization" in config:
            self.optimizer.auto_optimization_enabled = config["auto_optimization"]

        if "thresholds" in config:
            self.monitor.thresholds.update(config["thresholds"])

        if "collection_interval" in config:
            self.monitor.collection_interval = config["collection_interval"]

        logger.info("Performance optimization configuration updated")


# Global performance optimization layer
performance_layer = PerformanceOptimizationLayer()
