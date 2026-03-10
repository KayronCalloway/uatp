"""
Feedback Module
===============

Components for automatic outcome inference and confidence calibration.

Modules:
- outcome_inference: Hybrid keyword + embedding outcome detection
- review_queue: Human-in-the-loop review queue for uncertain cases
- calibration: Bayesian confidence calibration with Platt scaling
"""

from .auto_outcome_tracker import (
    AutoOutcomeTracker,
    TrackedInteraction,
    get_auto_tracker,
    initialize_tracker,
)
from .calibration import (
    CalibrationManager,
    CalibrationMetrics,
    CalibrationPoint,
    PlattScaler,
    calibrate_confidence,
    get_calibration_manager,
)
from .outcome_inference import (
    OutcomeInference,
    OutcomeInferenceEngine,
    OutcomeStatus,
    get_inference_engine,
    infer_outcome,
)
from .review_queue import (
    ReviewPriority,
    ReviewQueueItem,
    ReviewQueueManager,
    ReviewQueueStats,
    ReviewStatus,
)

__all__ = [
    # Outcome inference
    "OutcomeInference",
    "OutcomeInferenceEngine",
    "OutcomeStatus",
    "get_inference_engine",
    "infer_outcome",
    # Review queue
    "ReviewPriority",
    "ReviewQueueItem",
    "ReviewQueueManager",
    "ReviewQueueStats",
    "ReviewStatus",
    # Calibration
    "CalibrationManager",
    "CalibrationMetrics",
    "CalibrationPoint",
    "PlattScaler",
    "calibrate_confidence",
    "get_calibration_manager",
    # Auto-outcome tracker
    "AutoOutcomeTracker",
    "TrackedInteraction",
    "get_auto_tracker",
    "initialize_tracker",
]
