"""
Spatial data structures for embodied AI and robotics
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
from enum import Enum


class CoordinateFrame(Enum):
    """Standard coordinate frame references"""

    WORLD = "world"
    MAP = "map"
    ODOM = "odom"
    ROBOT_BASE = "robot_base"
    SENSOR = "sensor"
    CAMERA = "camera"


@dataclass
class SpatialCoordinate:
    """
    3D coordinate with reference frame and uncertainty
    """

    x: float
    y: float
    z: float
    frame_id: str = "world"
    timestamp: Optional[datetime] = None
    uncertainty: Optional[float] = None  # meters
    covariance: Optional[np.ndarray] = None  # 3x3 covariance matrix

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "uncertainty": self.uncertainty,
            "covariance": self.covariance.tolist()
            if self.covariance is not None
            else None,
        }

    def distance_to(self, other: "SpatialCoordinate") -> float:
        """Calculate Euclidean distance to another coordinate"""
        if self.frame_id != other.frame_id:
            raise ValueError(
                f"Cannot calculate distance between different frames: {self.frame_id} vs {other.frame_id}"
            )

        return np.sqrt(
            (self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2
        )


@dataclass
class Orientation:
    """
    3D orientation as roll, pitch, yaw (Euler angles in radians)
    """

    roll: float  # Rotation around X axis
    pitch: float  # Rotation around Y axis
    yaw: float  # Rotation around Z axis
    frame_id: str = "world"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "roll": self.roll,
            "pitch": self.pitch,
            "yaw": self.yaw,
            "frame_id": self.frame_id,
        }

    def to_quaternion(self) -> Tuple[float, float, float, float]:
        """Convert to quaternion (x, y, z, w)"""
        cy = np.cos(self.yaw * 0.5)
        sy = np.sin(self.yaw * 0.5)
        cp = np.cos(self.pitch * 0.5)
        sp = np.sin(self.pitch * 0.5)
        cr = np.cos(self.roll * 0.5)
        sr = np.sin(self.roll * 0.5)

        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy

        return (x, y, z, w)


@dataclass
class PhysicalObject:
    """
    Representation of a physical object in 3D space
    """

    id: str
    object_class: str  # "person", "vehicle", "obstacle", "tool", etc.
    position: SpatialCoordinate
    orientation: Orientation
    dimensions: Tuple[float, float, float]  # length, width, height in meters
    velocity: Optional[Tuple[float, float, float]] = None  # m/s in x, y, z
    angular_velocity: Optional[Tuple[float, float, float]] = None  # rad/s
    mass: Optional[float] = None  # kg
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.95
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "object_class": self.object_class,
            "position": self.position.to_dict(),
            "orientation": self.orientation.to_dict(),
            "dimensions": list(self.dimensions),
            "velocity": list(self.velocity) if self.velocity else None,
            "angular_velocity": list(self.angular_velocity)
            if self.angular_velocity
            else None,
            "mass": self.mass,
            "properties": self.properties,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def volume(self) -> float:
        """Calculate object volume in cubic meters"""
        return self.dimensions[0] * self.dimensions[1] * self.dimensions[2]

    def bounding_box(self) -> Dict[str, SpatialCoordinate]:
        """Get axis-aligned bounding box corners"""
        half_x, half_y, half_z = [d / 2 for d in self.dimensions]

        return {
            "min": SpatialCoordinate(
                x=self.position.x - half_x,
                y=self.position.y - half_y,
                z=self.position.z - half_z,
                frame_id=self.position.frame_id,
            ),
            "max": SpatialCoordinate(
                x=self.position.x + half_x,
                y=self.position.y + half_y,
                z=self.position.z + half_z,
                frame_id=self.position.frame_id,
            ),
        }


@dataclass
class SpatialScene:
    """
    Complete spatial scene representation at a point in time
    """

    timestamp: datetime
    frame_id: str
    objects: List[PhysicalObject] = field(default_factory=list)
    terrain: Dict[str, Any] = field(default_factory=dict)
    occupancy_grid: Optional[np.ndarray] = None  # 2D or 3D occupancy grid
    semantic_map: Dict[str, Any] = field(default_factory=dict)
    free_space: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "frame_id": self.frame_id,
            "objects": [obj.to_dict() for obj in self.objects],
            "terrain": self.terrain,
            "occupancy_grid_shape": self.occupancy_grid.shape
            if self.occupancy_grid is not None
            else None,
            "semantic_map": self.semantic_map,
            "free_space": self.free_space,
            "metadata": self.metadata,
            "object_count": len(self.objects),
        }

    def find_object_by_id(self, object_id: str) -> Optional[PhysicalObject]:
        """Find object by ID"""
        for obj in self.objects:
            if obj.id == object_id:
                return obj
        return None

    def find_objects_by_class(self, object_class: str) -> List[PhysicalObject]:
        """Find all objects of a given class"""
        return [obj for obj in self.objects if obj.object_class == object_class]

    def objects_in_radius(
        self, center: SpatialCoordinate, radius: float
    ) -> List[PhysicalObject]:
        """Find all objects within radius of a point"""
        nearby = []
        for obj in self.objects:
            if obj.position.frame_id != center.frame_id:
                continue

            distance = center.distance_to(obj.position)
            if distance <= radius:
                nearby.append(obj)

        return nearby


@dataclass
class SensorData:
    """
    Generic sensor data container
    """

    sensor_id: str
    sensor_type: str  # "lidar", "camera", "imu", "gps", "radar", etc.
    timestamp: datetime
    frame_id: str
    data: Any  # Actual sensor data (point cloud, image, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.95
    calibrated: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "timestamp": self.timestamp.isoformat(),
            "frame_id": self.frame_id,
            "data_type": type(self.data).__name__,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "calibrated": self.calibrated,
        }


@dataclass
class ActionTrajectory:
    """
    Trajectory for physical actions
    """

    waypoints: List[SpatialCoordinate]
    orientations: List[Orientation]
    timestamps: List[datetime]
    velocities: Optional[List[Tuple[float, float, float]]] = None
    accelerations: Optional[List[Tuple[float, float, float]]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "waypoints": [wp.to_dict() for wp in self.waypoints],
            "orientations": [ori.to_dict() for ori in self.orientations],
            "timestamps": [ts.isoformat() for ts in self.timestamps],
            "velocities": [list(v) for v in self.velocities]
            if self.velocities
            else None,
            "accelerations": [list(a) for a in self.accelerations]
            if self.accelerations
            else None,
            "total_waypoints": len(self.waypoints),
            "duration": (self.timestamps[-1] - self.timestamps[0]).total_seconds()
            if len(self.timestamps) > 1
            else 0,
        }

    def total_distance(self) -> float:
        """Calculate total path length"""
        if len(self.waypoints) < 2:
            return 0.0

        total = 0.0
        for i in range(1, len(self.waypoints)):
            total += self.waypoints[i - 1].distance_to(self.waypoints[i])

        return total


@dataclass
class PhysicalConstraint:
    """
    Constraint for physical actions
    """

    constraint_type: str  # "collision_avoidance", "force_limit", "velocity_limit", etc.
    parameters: Dict[str, Any]
    priority: int = 1  # Higher = more important
    hard_constraint: bool = True  # True = must satisfy, False = soft preference

    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_type": self.constraint_type,
            "parameters": self.parameters,
            "priority": self.priority,
            "hard_constraint": self.hard_constraint,
        }


@dataclass
class SpatialRelationship:
    """
    Relationship between two spatial entities
    """

    subject_id: str
    object_id: str
    relationship_type: str  # "above", "below", "left_of", "right_of", "near", "far", etc.
    distance: Optional[float] = None
    confidence: float = 0.95

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "object_id": self.object_id,
            "relationship_type": self.relationship_type,
            "distance": self.distance,
            "confidence": self.confidence,
        }
