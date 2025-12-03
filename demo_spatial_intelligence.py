"""
Spatial Intelligence Demo for UATP
Demonstrates embodied AI attribution with a simulated robot pick-and-place task
"""

import asyncio
from datetime import datetime
import uuid
from typing import Dict, Any
import json

# Import spatial data structures (direct import to avoid module issues)
import sys
import os

sys.path.insert(0, "/Users/kay/uatp-capsule-engine")
os.chdir("/Users/kay/uatp-capsule-engine")

# Import just the data structures file directly
import importlib.util

spec = importlib.util.spec_from_file_location(
    "data_structures", "/Users/kay/uatp-capsule-engine/src/spatial/data_structures.py"
)
data_structures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data_structures)

SpatialCoordinate = data_structures.SpatialCoordinate
Orientation = data_structures.Orientation
PhysicalObject = data_structures.PhysicalObject
SpatialScene = data_structures.SpatialScene
ActionTrajectory = data_structures.ActionTrajectory
PhysicalConstraint = data_structures.PhysicalConstraint


class SimulatedRobotArm:
    """Simulated robot arm for demonstration"""

    def __init__(self, robot_id: str):
        self.robot_id = robot_id
        self.current_pose = SpatialCoordinate(
            x=0.0, y=0.0, z=0.5, frame_id="robot_base"
        )
        self.current_orientation = Orientation(roll=0.0, pitch=0.0, yaw=0.0)

    async def pick_object(self, obj: PhysicalObject) -> Dict[str, Any]:
        """Simulate picking up an object"""
        print(f"\n🤖 [{self.robot_id}] Planning grasp for {obj.id}...")

        # Generate trajectory
        trajectory = ActionTrajectory(
            waypoints=[
                self.current_pose,
                SpatialCoordinate(
                    x=obj.position.x,
                    y=obj.position.y,
                    z=obj.position.z + 0.1,
                    frame_id=obj.position.frame_id,
                ),
                obj.position,
            ],
            orientations=[
                self.current_orientation,
                Orientation(roll=0.0, pitch=1.57, yaw=0.0),  # 90 degrees pitch
                Orientation(roll=0.0, pitch=1.57, yaw=0.0),
            ],
            timestamps=[datetime.now(), datetime.now(), datetime.now()],
        )

        # Simulate execution
        await asyncio.sleep(0.5)  # Simulate motion time

        result = {
            "success": True,
            "execution_time": 2.3,  # seconds
            "trajectory": trajectory.to_dict(),
            "grasp_force": 12.5,  # newtons
            "pose_error": 0.015,  # meters
            "object_secured": True,
        }

        self.current_pose = obj.position

        print(f"✓ [{self.robot_id}] Object {obj.id} grasped successfully!")
        print(f"  Grasp force: {result['grasp_force']}N")
        print(f"  Pose error: {result['pose_error']*1000:.1f}mm")

        return result

    async def place_object(self, target: SpatialCoordinate) -> Dict[str, Any]:
        """Simulate placing an object"""
        print(f"\n🤖 [{self.robot_id}] Moving to placement position...")

        trajectory = ActionTrajectory(
            waypoints=[
                self.current_pose,
                SpatialCoordinate(
                    x=target.x, y=target.y, z=target.z + 0.1, frame_id=target.frame_id
                ),
                target,
            ],
            orientations=[
                self.current_orientation,
                Orientation(roll=0.0, pitch=1.57, yaw=0.0),
                Orientation(roll=0.0, pitch=1.57, yaw=0.0),
            ],
            timestamps=[datetime.now(), datetime.now(), datetime.now()],
        )

        await asyncio.sleep(0.5)

        result = {
            "success": True,
            "execution_time": 2.1,  # seconds
            "trajectory": trajectory.to_dict(),
            "release_successful": True,
            "final_pose_error": 0.012,  # meters
        }

        self.current_pose = target

        print(f"✓ [{self.robot_id}] Object placed successfully!")
        print(f"  Final position error: {result['final_pose_error']*1000:.1f}mm")

        return result


class SpatialCapsuleCreator:
    """Creates UATP capsules for spatial/physical actions"""

    @staticmethod
    def create_spatial_perception_capsule(
        scene: SpatialScene, agent_id: str
    ) -> Dict[str, Any]:
        """Create a spatial perception capsule"""
        capsule = {
            "type": "spatial_perception",
            "capsule_id": f"spatial_perception_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "spatial_scene": scene.to_dict(),
            "perception_quality": {
                "object_detection_confidence": 0.94,
                "scene_completeness": 0.88,
                "sensor_coverage": ["camera_rgb", "depth_sensor", "lidar"],
            },
            "verification": {
                "sensor_fusion_valid": True,
                "calibration_status": "valid",
                "multi_sensor_consensus": 0.92,
            },
            "metadata": {
                "processing_time_ms": 45,
                "num_objects_detected": len(scene.objects),
            },
        }

        return capsule

    @staticmethod
    def create_physical_action_capsule(
        action_type: str,
        planning: Dict[str, Any],
        execution: Dict[str, Any],
        agent_id: str,
    ) -> Dict[str, Any]:
        """Create a physical action capsule"""
        capsule = {
            "type": "physical_action",
            "capsule_id": f"physical_action_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "action": {
                "type": action_type,
                "planning": planning,
                "execution_result": execution,
            },
            "reasoning": {
                "goal": planning.get("goal", "unknown"),
                "constraints_satisfied": planning.get("constraints", []),
                "alternatives_considered": planning.get("alternatives", 1),
                "confidence": planning.get("confidence", 0.90),
            },
            "verification": {
                "action_verified": execution.get("success", False),
                "physical_outcome_confirmed": True,
                "witness_sensors": ["camera_1", "camera_2", "force_sensor"],
                "execution_quality": SpatialCapsuleCreator._calculate_execution_quality(
                    execution
                ),
            },
            "attribution": {
                "task_value": 10.0,  # USD
                "execution_quality_bonus": 2.5,
                "energy_cost": 0.15,
                "time_cost": execution.get("execution_time", 0)
                * 0.50,  # $0.50 per second
            },
        }

        return capsule

    @staticmethod
    def _calculate_execution_quality(execution: Dict[str, Any]) -> float:
        """Calculate execution quality score"""
        if not execution.get("success", False):
            return 0.0

        # Perfect execution = 1.0, degrade based on errors
        pose_error = execution.get("pose_error", 0.0)
        quality = 1.0 - min(pose_error / 0.05, 0.5)  # 5cm error = 50% quality loss

        return max(0.0, min(1.0, quality))

    @staticmethod
    def create_spatial_reasoning_capsule(
        reasoning_task: str, steps: list, result: Dict[str, Any], agent_id: str
    ) -> Dict[str, Any]:
        """Create a spatial reasoning capsule"""
        capsule = {
            "type": "spatial_reasoning",
            "capsule_id": f"spatial_reasoning_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "reasoning_task": reasoning_task,
            "reasoning_steps": steps,
            "final_result": result,
            "verification": {
                "reasoning_valid": True,
                "constraints_satisfied": result.get("constraints_satisfied", True),
                "safety_verified": result.get("safety_score", 0.0) > 0.8,
            },
            "attribution": {
                "reasoning_complexity": len(steps),
                "computation_time": result.get("computation_time", 0),
                "value_contribution": "medium",
            },
        }

        return capsule


async def demo_pick_and_place_with_spatial_capsules():
    """
    Demonstrate a complete pick-and-place task with spatial intelligence capsules
    """

    print("=" * 80)
    print("🌍 UATP SPATIAL INTELLIGENCE DEMO")
    print("Simulated Robot Pick-and-Place Task with Attribution")
    print("=" * 80)

    # Create simulated environment
    print("\n📦 Step 1: Building spatial scene...")

    # Create objects in the scene
    target_object = PhysicalObject(
        id="blue_cube_01",
        object_class="cube",
        position=SpatialCoordinate(x=0.5, y=0.3, z=0.1, frame_id="world"),
        orientation=Orientation(roll=0.0, pitch=0.0, yaw=0.0),
        dimensions=(0.05, 0.05, 0.05),  # 5cm cube
        mass=0.1,  # 100g
        properties={"color": "blue", "material": "plastic"},
        confidence=0.95,
        timestamp=datetime.now(),
    )

    obstacle = PhysicalObject(
        id="red_cylinder_01",
        object_class="cylinder",
        position=SpatialCoordinate(x=0.4, y=0.2, z=0.1, frame_id="world"),
        orientation=Orientation(roll=0.0, pitch=0.0, yaw=0.0),
        dimensions=(0.08, 0.08, 0.15),  # 8cm diameter, 15cm height
        mass=0.3,
        properties={"color": "red", "material": "metal"},
        confidence=0.93,
    )

    # Build spatial scene
    scene = SpatialScene(
        timestamp=datetime.now(),
        frame_id="world",
        objects=[target_object, obstacle],
        terrain={"type": "flat", "material": "wood_table"},
        metadata={"lighting": "good", "visibility": "clear"},
    )

    print(f"✓ Scene created with {len(scene.objects)} objects")
    for obj in scene.objects:
        print(
            f"  - {obj.id}: {obj.object_class} at ({obj.position.x:.2f}, {obj.position.y:.2f}, {obj.position.z:.2f})"
        )

    # Create spatial perception capsule
    capsule_creator = SpatialCapsuleCreator()
    perception_capsule = capsule_creator.create_spatial_perception_capsule(
        scene=scene, agent_id="robot_perception_system"
    )

    print(f"\n📋 Created spatial_perception capsule: {perception_capsule['capsule_id']}")
    print(
        f"  Detection confidence: {perception_capsule['perception_quality']['object_detection_confidence']:.2%}"
    )

    # Step 2: Spatial reasoning - Plan the action
    print("\n🧠 Step 2: Spatial reasoning...")

    reasoning_steps = [
        {
            "step": 1,
            "operation": "object_identification",
            "target": "blue_cube_01",
            "confidence": 0.95,
        },
        {
            "step": 2,
            "operation": "collision_detection",
            "obstacles_detected": ["red_cylinder_01"],
            "clearance": 0.12,  # 12cm clearance
        },
        {
            "step": 3,
            "operation": "grasp_planning",
            "grasp_type": "top_grasp",
            "approach_angle": 90.0,  # degrees
        },
        {
            "step": 4,
            "operation": "path_planning",
            "algorithm": "RRT_connect",
            "path_length": 0.85,  # meters
            "computation_time": 0.23,  # seconds
        },
    ]

    reasoning_result = {
        "plan_valid": True,
        "safety_score": 0.94,
        "constraints_satisfied": True,
        "computation_time": 0.23,
    }

    reasoning_capsule = capsule_creator.create_spatial_reasoning_capsule(
        reasoning_task="pick_and_place_planning",
        steps=reasoning_steps,
        result=reasoning_result,
        agent_id="robot_motion_planner",
    )

    print(f"✓ Planning complete: {len(reasoning_steps)} reasoning steps")
    print(f"  Safety score: {reasoning_result['safety_score']:.2%}")
    print(f"📋 Created spatial_reasoning capsule: {reasoning_capsule['capsule_id']}")

    # Step 3: Execute physical action
    print("\n⚙️  Step 3: Executing physical action...")

    robot = SimulatedRobotArm("robot_arm_01")

    # Pick phase
    pick_planning = {
        "goal": "grasp blue_cube_01",
        "constraints": ["stable_grasp", "avoid_collision"],
        "confidence": 0.92,
        "alternatives": 3,
    }

    pick_result = await robot.pick_object(target_object)

    pick_capsule = capsule_creator.create_physical_action_capsule(
        action_type="pick",
        planning=pick_planning,
        execution=pick_result,
        agent_id="robot_arm_01",
    )

    print(f"📋 Created physical_action capsule (pick): {pick_capsule['capsule_id']}")
    print(
        f"  Execution quality: {pick_capsule['verification']['execution_quality']:.2%}"
    )
    print(f"  Economic value: ${pick_capsule['attribution']['task_value']:.2f}")

    # Place phase
    target_position = SpatialCoordinate(x=0.7, y=0.5, z=0.1, frame_id="world")

    place_planning = {
        "goal": "place object at target location",
        "constraints": ["controlled_release", "stable_placement"],
        "confidence": 0.90,
        "alternatives": 2,
    }

    place_result = await robot.place_object(target_position)

    place_capsule = capsule_creator.create_physical_action_capsule(
        action_type="place",
        planning=place_planning,
        execution=place_result,
        agent_id="robot_arm_01",
    )

    print(f"📋 Created physical_action capsule (place): {place_capsule['capsule_id']}")
    print(
        f"  Execution quality: {place_capsule['verification']['execution_quality']:.2%}"
    )
    print(f"  Economic value: ${place_capsule['attribution']['task_value']:.2f}")

    # Step 4: Calculate attribution
    print("\n💰 Step 4: Economic attribution...")

    total_capsules = [
        perception_capsule,
        reasoning_capsule,
        pick_capsule,
        place_capsule,
    ]

    total_task_value = 50.0  # Task worth $50
    attribution_breakdown = {
        "robot_perception_system": {
            "contribution": "spatial_perception",
            "value": total_task_value * 0.15,  # 15% for perception
            "capsules": [perception_capsule["capsule_id"]],
        },
        "robot_motion_planner": {
            "contribution": "spatial_reasoning",
            "value": total_task_value * 0.25,  # 25% for planning
            "capsules": [reasoning_capsule["capsule_id"]],
        },
        "robot_arm_01": {
            "contribution": "physical_execution",
            "value": total_task_value * 0.60,  # 60% for execution
            "capsules": [pick_capsule["capsule_id"], place_capsule["capsule_id"]],
        },
    }

    print("\n📊 Attribution Breakdown:")
    for agent_id, attribution in attribution_breakdown.items():
        print(f"\n  {agent_id}:")
        print(f"    Contribution: {attribution['contribution']}")
        print(f"    Value: ${attribution['value']:.2f}")
        print(f"    Capsules: {len(attribution['capsules'])}")

    # Step 5: Summary
    print("\n" + "=" * 80)
    print("✅ TASK COMPLETE - Spatial Intelligence Demo")
    print("=" * 80)

    summary = {
        "task": "pick_and_place",
        "success": True,
        "capsules_created": len(total_capsules),
        "agents_involved": len(attribution_breakdown),
        "total_economic_value": total_task_value,
        "execution_time": pick_result["execution_time"]
        + place_result["execution_time"],
        "capsule_breakdown": {
            "spatial_perception": 1,
            "spatial_reasoning": 1,
            "physical_action": 2,
        },
    }

    print(f"\n📈 Summary:")
    print(f"  Total capsules: {summary['capsules_created']}")
    print(f"  Agents involved: {summary['agents_involved']}")
    print(f"  Economic value: ${summary['total_economic_value']:.2f}")
    print(f"  Execution time: {summary['execution_time']:.1f}s")

    print(f"\n📦 Capsule Types Created:")
    for capsule_type, count in summary["capsule_breakdown"].items():
        print(f"  - {capsule_type}: {count}")

    # Save capsules to file
    output_file = "spatial_intelligence_demo_capsules.json"
    with open(output_file, "w") as f:
        json.dump(
            {
                "demo_summary": summary,
                "capsules": total_capsules,
                "attribution": attribution_breakdown,
            },
            f,
            indent=2,
        )

    print(f"\n💾 Capsules saved to: {output_file}")
    print("\n" + "=" * 80)

    return total_capsules, attribution_breakdown


if __name__ == "__main__":
    print("Starting Spatial Intelligence Demo...\n")
    asyncio.run(demo_pick_and_place_with_spatial_capsules())
    print("\n🎉 Demo complete!")
