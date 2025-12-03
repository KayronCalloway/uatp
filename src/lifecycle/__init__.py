"""
Lifecycle module for UATP Capsule Engine.
Provides automated capsule lifecycle management and dependency tracking.
"""

from .automation import (
    AutomationTrigger,
    DependencyTracker,
    LifecycleAction,
    LifecycleAutomationEngine,
    LifecycleEvent,
    LifecycleExecutionResult,
    LifecycleRule,
    LifecycleTask,
    OrphanDetector,
    lifecycle_engine,
)

__all__ = [
    "LifecycleAutomationEngine",
    "DependencyTracker",
    "OrphanDetector",
    "LifecycleEvent",
    "AutomationTrigger",
    "LifecycleAction",
    "LifecycleRule",
    "LifecycleTask",
    "LifecycleExecutionResult",
    "lifecycle_engine",
]
