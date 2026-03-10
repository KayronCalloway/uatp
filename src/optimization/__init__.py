"""
Optimization module for UATP Capsule Engine.
Provides compression, deduplication, pruning, and performance optimization capabilities.
"""

from .capsule_compression import (
    CapsuleCompressor,
    CapsuleDeduplicator,
    CapsuleOptimizationEngine,
    CapsulePruner,
    CompressedCapsule,
    CompressionMethod,
    CompressionResult,
    DuplicationAnalysis,
    PruningDecision,
    PruningStrategy,
    optimization_engine,
)
from .performance_layer import (
    BottleneckDetector,
    OptimizationResult,
    OptimizationStrategy,
    PerformanceBottleneck,
    PerformanceLevel,
    PerformanceMetric,
    PerformanceMetrics,
    PerformanceMonitor,
    PerformanceOptimizationLayer,
    PerformanceOptimizer,
    performance_layer,
)

__all__ = [
    "CapsuleOptimizationEngine",
    "CapsuleCompressor",
    "CapsuleDeduplicator",
    "CapsulePruner",
    "CompressionMethod",
    "PruningStrategy",
    "CompressionResult",
    "CompressedCapsule",
    "PruningDecision",
    "DuplicationAnalysis",
    "optimization_engine",
    "PerformanceOptimizationLayer",
    "PerformanceMonitor",
    "BottleneckDetector",
    "PerformanceOptimizer",
    "PerformanceMetric",
    "OptimizationStrategy",
    "PerformanceLevel",
    "PerformanceMetrics",
    "PerformanceBottleneck",
    "OptimizationResult",
    "performance_layer",
]
