"""
Spatial Intelligence Module for UATP
Supports embodied AI, robotics, and physical world attribution
"""

from .data_structures import SpatialCoordinate, PhysicalObject, SpatialScene, SensorData

from .capsule_types import (
    SpatialPerceptionCapsule,
    PhysicalActionCapsule,
    SpatialReasoningCapsule,
    EmbodiedLearningCapsule,
    SensorFusionCapsule,
)

from .verification import PhysicalWorldVerifier, SensorConsensus, PhysicsValidator

from .attribution import (
    PhysicalOutcomeAttribution,
    MultiRobotAttribution,
    EmbodiedLaborEconomics,
)

__all__ = [
    # Data structures
    "SpatialCoordinate",
    "PhysicalObject",
    "SpatialScene",
    "SensorData",
    # Capsule types
    "SpatialPerceptionCapsule",
    "PhysicalActionCapsule",
    "SpatialReasoningCapsule",
    "EmbodiedLearningCapsule",
    "SensorFusionCapsule",
    # Verification
    "PhysicalWorldVerifier",
    "SensorConsensus",
    "PhysicsValidator",
    # Attribution
    "PhysicalOutcomeAttribution",
    "MultiRobotAttribution",
    "EmbodiedLaborEconomics",
]
