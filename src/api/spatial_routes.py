"""
Spatial Intelligence API Routes
Provides endpoints for spatial capsule creation and management
"""

from quart import Blueprint, jsonify, request
from typing import Dict, Any
import logging

from src.integrations.spatial_ai_integration import (
    spatial_ai_hub,
    PerceptionSystemWrapper,
    PlanningSystemWrapper,
    ControlSystemWrapper,
    NavigationSystemWrapper,
    ManipulationSystemWrapper,
)
from src.insurance.physical_ai_insurance import (
    physical_ai_risk_assessor,
    PhysicalAIType,
    PhysicalRiskCategory,
)

logger = logging.getLogger(__name__)

spatial_bp = Blueprint("spatial", __name__, url_prefix="/api/spatial")


@spatial_bp.route("/providers", methods=["GET"])
async def list_providers():
    """List all registered spatial AI providers"""
    try:
        providers = spatial_ai_hub.list_providers()
        return jsonify({"providers": providers, "total": len(providers)}), 200
    except Exception as e:
        logger.error(f"Error listing providers: {e}")
        return jsonify({"error": str(e)}), 500


@spatial_bp.route("/providers/register", methods=["POST"])
async def register_provider():
    """Register a new spatial AI provider"""
    try:
        data = await request.get_json()
        provider_id = data.get("provider_id")
        provider_name = data.get("provider_name")
        provider_type = data.get("provider_type")

        if not all([provider_id, provider_name, provider_type]):
            return jsonify({"error": "Missing required fields"}), 400

        # Create appropriate wrapper
        wrapper_map = {
            "perception": PerceptionSystemWrapper,
            "planning": PlanningSystemWrapper,
            "control": ControlSystemWrapper,
            "navigation": NavigationSystemWrapper,
            "manipulation": ManipulationSystemWrapper,
        }

        wrapper_class = wrapper_map.get(provider_type)
        if not wrapper_class:
            return jsonify({"error": f"Invalid provider type: {provider_type}"}), 400

        wrapper = wrapper_class(provider_name)
        spatial_ai_hub.register_provider(provider_id, wrapper)

        return (
            jsonify(
                {
                    "success": True,
                    "provider_id": provider_id,
                    "message": f"Provider {provider_name} registered successfully",
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Error registering provider: {e}")
        return jsonify({"error": str(e)}), 500


@spatial_bp.route("/capsules/perception", methods=["POST"])
async def create_perception_capsule():
    """Create a spatial perception capsule"""
    try:
        data = await request.get_json()
        provider_id = data.get("provider_id")
        sensor_data = data.get("sensor_data", {})
        detected_objects = data.get("detected_objects", [])
        scene_understanding = data.get("scene_understanding", {})
        confidence = data.get("confidence", 0.95)

        provider = spatial_ai_hub.get_provider(provider_id)
        if not provider:
            return jsonify({"error": f"Provider {provider_id} not found"}), 404

        capsule = provider.wrap_perception_output(
            sensor_data=sensor_data,
            detected_objects=detected_objects,
            scene_understanding=scene_understanding,
            confidence=confidence,
        )

        return jsonify({"success": True, "capsule": capsule}), 201

    except Exception as e:
        logger.error(f"Error creating perception capsule: {e}")
        return jsonify({"error": str(e)}), 500


@spatial_bp.route("/capsules/planning", methods=["POST"])
async def create_planning_capsule():
    """Create a spatial planning capsule"""
    try:
        data = await request.get_json()
        provider_id = data.get("provider_id")
        goal = data.get("goal", {})
        constraints = data.get("constraints", [])
        planned_trajectory = data.get("planned_trajectory", {})
        alternatives_considered = data.get("alternatives_considered", 1)
        computation_time = data.get("computation_time", 0.0)

        provider = spatial_ai_hub.get_provider(provider_id)
        if not provider:
            return jsonify({"error": f"Provider {provider_id} not found"}), 404

        capsule = provider.wrap_planning_output(
            goal=goal,
            constraints=constraints,
            planned_trajectory=planned_trajectory,
            alternatives_considered=alternatives_considered,
            computation_time=computation_time,
        )

        return jsonify({"success": True, "capsule": capsule}), 201

    except Exception as e:
        logger.error(f"Error creating planning capsule: {e}")
        return jsonify({"error": str(e)}), 500


@spatial_bp.route("/capsules/control", methods=["POST"])
async def create_control_capsule():
    """Create a spatial control capsule"""
    try:
        data = await request.get_json()
        provider_id = data.get("provider_id")
        commanded_action = data.get("commanded_action", {})
        executed_action = data.get("executed_action", {})
        physical_result = data.get("physical_result", {})
        execution_time = data.get("execution_time", 0.0)

        provider = spatial_ai_hub.get_provider(provider_id)
        if not provider:
            return jsonify({"error": f"Provider {provider_id} not found"}), 404

        capsule = provider.wrap_control_action(
            commanded_action=commanded_action,
            executed_action=executed_action,
            physical_result=physical_result,
            execution_time=execution_time,
        )

        return jsonify({"success": True, "capsule": capsule}), 201

    except Exception as e:
        logger.error(f"Error creating control capsule: {e}")
        return jsonify({"error": str(e)}), 500


@spatial_bp.route("/chains/create", methods=["POST"])
async def create_spatial_chain():
    """Create a complete spatial action chain"""
    try:
        data = await request.get_json()
        perception_capsules = data.get("perception_capsules", [])
        planning_capsules = data.get("planning_capsules", [])
        control_capsules = data.get("control_capsules", [])

        chain = spatial_ai_hub.create_spatial_chain(
            perception_capsules=perception_capsules,
            planning_capsules=planning_capsules,
            control_capsules=control_capsules,
        )

        return jsonify({"success": True, "chain": chain}), 201

    except Exception as e:
        logger.error(f"Error creating spatial chain: {e}")
        return jsonify({"error": str(e)}), 500


@spatial_bp.route("/insurance/assess", methods=["POST"])
async def assess_physical_risk():
    """Assess insurance risk for a physical AI system"""
    try:
        data = await request.get_json()
        ai_system_type = data.get("ai_system_type")
        ai_system_id = data.get("ai_system_id")
        operating_environment = data.get("operating_environment", {})
        capsule_chain = data.get("capsule_chain", [])
        historical_incidents = data.get("historical_incidents", [])

        # Convert string to enum
        try:
            system_type_enum = PhysicalAIType(ai_system_type)
        except ValueError:
            return jsonify({"error": f"Invalid AI system type: {ai_system_type}"}), 400

        assessment = physical_ai_risk_assessor.assess_physical_risk(
            ai_system_type=system_type_enum,
            ai_system_id=ai_system_id,
            operating_environment=operating_environment,
            capsule_chain=capsule_chain,
            historical_incidents=[],  # Would need to convert dict to PhysicalIncident objects
        )

        return jsonify({"success": True, "assessment": assessment}), 200

    except Exception as e:
        logger.error(f"Error assessing physical risk: {e}")
        return jsonify({"error": str(e)}), 500


@spatial_bp.route("/insurance/system-types", methods=["GET"])
async def list_system_types():
    """List available physical AI system types"""
    try:
        system_types = [
            {
                "value": st.value,
                "name": st.value.replace("_", " ").title(),
                "description": f"Physical AI system type: {st.value}",
            }
            for st in PhysicalAIType
        ]

        return jsonify({"system_types": system_types, "total": len(system_types)}), 200

    except Exception as e:
        logger.error(f"Error listing system types: {e}")
        return jsonify({"error": str(e)}), 500


@spatial_bp.route("/insurance/risk-categories", methods=["GET"])
async def list_risk_categories():
    """List available physical risk categories"""
    try:
        risk_categories = [
            {
                "value": rc.value,
                "name": rc.value.replace("_", " ").title(),
                "description": f"Physical risk: {rc.value}",
            }
            for rc in PhysicalRiskCategory
        ]

        return (
            jsonify(
                {"risk_categories": risk_categories, "total": len(risk_categories)}
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error listing risk categories: {e}")
        return jsonify({"error": str(e)}), 500


@spatial_bp.route("/stats", methods=["GET"])
async def spatial_stats():
    """Get spatial intelligence statistics"""
    try:
        providers = spatial_ai_hub.list_providers()

        # Count by provider type
        provider_types = {}
        for provider_id, info in providers.items():
            ptype = info["type"]
            provider_types[ptype] = provider_types.get(ptype, 0) + 1

        return (
            jsonify(
                {
                    "total_providers": len(providers),
                    "provider_types": provider_types,
                    "insurance_enabled": True,
                    "multi_sensor_fusion": True,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting spatial stats: {e}")
        return jsonify({"error": str(e)}), 500


# Initialize demo providers on startup
def init_spatial_providers():
    """Initialize demo spatial AI providers"""
    try:
        # Register demo providers
        spatial_ai_hub.register_provider(
            "zed_camera", PerceptionSystemWrapper("ZED Camera System")
        )
        spatial_ai_hub.register_provider(
            "velodyne_lidar", PerceptionSystemWrapper("Velodyne LiDAR")
        )
        spatial_ai_hub.register_provider(
            "moveit_planner", PlanningSystemWrapper("MoveIt Motion Planner")
        )
        spatial_ai_hub.register_provider(
            "ur5_controller", ControlSystemWrapper("UR5 Robot Controller")
        )
        spatial_ai_hub.register_provider(
            "gps_imu_fusion", NavigationSystemWrapper("GPS+IMU Navigation")
        )
        spatial_ai_hub.register_provider(
            "robotiq_gripper", ManipulationSystemWrapper("Robotiq 2F-85 Gripper")
        )

        logger.info(f"Initialized {len(spatial_ai_hub.providers)} spatial AI providers")
    except Exception as e:
        logger.error(f"Error initializing spatial providers: {e}")
