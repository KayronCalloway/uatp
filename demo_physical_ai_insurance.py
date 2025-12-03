"""
Demo: Physical AI Insurance with UATP
Shows how UATP provides insurance for spatial/physical AI systems
"""

import sys

sys.path.insert(0, "/Users/kay/uatp-capsule-engine")

from src.insurance.physical_ai_insurance import (
    PhysicalAIRiskAssessor,
    PhysicalAIType,
    PhysicalRiskCategory,
    PhysicalIncident,
)
from datetime import datetime
from decimal import Decimal
import json


def demo_autonomous_vehicle_insurance():
    """Demo: Insuring an autonomous delivery vehicle"""

    print("=" * 80)
    print("🚗 DEMO: Autonomous Vehicle Insurance")
    print("=" * 80)

    assessor = PhysicalAIRiskAssessor()

    # Define the vehicle
    vehicle_info = {
        "type": PhysicalAIType.AUTONOMOUS_VEHICLE,
        "id": "delivery_van_001",
        "manufacturer": "Tesla",
        "model": "Autonomous Delivery Van",
    }

    # Operating environment
    operating_environment = {
        "public_space": True,
        "human_density": "high",  # Urban delivery
        "max_speed_mps": 15,  # 54 km/h
        "adverse_conditions": False,
        "environment_complexity": "high",
        "emergency_stop_available": True,
        "human_override_available": True,
        "redundant_sensors": True,
        "geofencing_enabled": True,
        "regular_maintenance": True,
    }

    # UATP capsule chain (audit trail)
    capsule_chain = [
        {
            "type": "spatial_perception",
            "capsule_id": "perception_001",
            "confidence": 0.94,
            "verification": {"verified": True},
        },
        {
            "type": "spatial_reasoning",
            "capsule_id": "reasoning_001",
            "confidence": 0.91,
            "verification": {"verified": True},
        },
        {
            "type": "physical_action",
            "capsule_id": "action_001",
            "confidence": 0.89,
            "verification": {"verified": True},
        },
    ]

    # No historical incidents (new vehicle)
    historical_incidents = []

    print(f"\n📋 Vehicle: {vehicle_info['manufacturer']} {vehicle_info['model']}")
    print(f"   ID: {vehicle_info['id']}")
    print(f"\n🌍 Operating Environment:")
    print(f"   Location: Urban public roads")
    print(f"   Human density: {operating_environment['human_density']}")
    print(
        f"   Max speed: {operating_environment['max_speed_mps']} m/s (~{operating_environment['max_speed_mps']*3.6:.0f} km/h)"
    )
    print(f"   Safety features: Emergency stop, human override, redundant sensors")

    print(f"\n📦 UATP Capsule Chain: {len(capsule_chain)} capsules")
    for capsule in capsule_chain:
        print(
            f"   - {capsule['type']}: {capsule['confidence']*100:.0f}% confidence, verified={capsule['verification']['verified']}"
        )

    # Run risk assessment
    print("\n⚙️  Running risk assessment...")
    assessment = assessor.assess_physical_risk(
        ai_system_type=vehicle_info["type"],
        ai_system_id=vehicle_info["id"],
        operating_environment=operating_environment,
        capsule_chain=capsule_chain,
        historical_incidents=historical_incidents,
    )

    # Display results
    print("\n" + "=" * 80)
    print("📊 RISK ASSESSMENT RESULTS")
    print("=" * 80)

    print(f"\n🎯 Composite Risk Score: {assessment['composite_risk_score']}/10")
    print(f"   Risk Level: {assessment['risk_level'].upper()}")

    print(f"\n📈 Risk Breakdown:")
    for factor, score in assessment["risk_scores"].items():
        print(f"   {factor.replace('_', ' ').title()}: {score:.1f}/10")

    print(f"\n💰 Insurance Premium:")
    print(f"   Base Annual: ${assessment['premium']['base_annual']:,.2f}")
    print(f"   Risk Adjusted: ${assessment['premium']['risk_adjusted']:,.2f}")
    print(
        f"   UATP Attribution Discount: {assessment['premium']['attribution_discount']*100:.0f}%"
    )
    print(f"   Final Annual Premium: ${assessment['premium']['final_annual']:,.2f}")
    print(f"   Monthly Premium: ${assessment['premium']['monthly']:,.2f}")

    print(f"\n🛡️  Recommended Coverage Limits:")
    for coverage_type, limit in assessment["coverage_limits"].items():
        print(f"   {coverage_type.replace('_', ' ').title()}: ${limit:,.0f}")

    if assessment["recommendations"]:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(assessment["recommendations"], 1):
            print(f"   {i}. {rec}")

    return assessment


def demo_warehouse_robot_insurance():
    """Demo: Insuring a warehouse robot with poor attribution"""

    print("\n\n" + "=" * 80)
    print("🤖 DEMO: Warehouse Robot Insurance (Poor Attribution)")
    print("=" * 80)

    assessor = PhysicalAIRiskAssessor()

    robot_info = {
        "type": PhysicalAIType.WAREHOUSE_ROBOT,
        "id": "warehouse_bot_057",
        "manufacturer": "Generic",
        "model": "Picker Bot 3000",
    }

    # Controlled environment (warehouse)
    operating_environment = {
        "public_space": False,
        "human_density": "low",
        "max_speed_mps": 3,  # Slow moving
        "adverse_conditions": False,
        "environment_complexity": "medium",
        "emergency_stop_available": True,
        "human_override_available": False,  # No override
        "redundant_sensors": False,  # No redundancy
        "geofencing_enabled": True,
        "regular_maintenance": False,  # Poor maintenance
    }

    # POOR capsule chain (no attribution!)
    capsule_chain = []  # No UATP integration!

    # Some historical incidents
    historical_incidents = [
        PhysicalIncident(
            incident_id="inc_001",
            timestamp=datetime.now(),
            ai_system_type=PhysicalAIType.WAREHOUSE_ROBOT,
            ai_system_id="warehouse_bot_057",
            risk_category=PhysicalRiskCategory.COLLISION_DAMAGE,
            location={"x": 10.5, "y": 20.3, "z": 0.0},
            damage_description="Collision with shelving unit",
            damage_estimated_cost=Decimal("2500"),
            sensor_readings={},
            action_being_performed="navigation",
            system_state={},
        )
    ]

    print(f"\n📋 Robot: {robot_info['manufacturer']} {robot_info['model']}")
    print(f"   ID: {robot_info['id']}")

    print(f"\n🌍 Operating Environment:")
    print(f"   Location: Private warehouse")
    print(f"   Human density: {operating_environment['human_density']}")
    print(f"   Safety features: Limited (no override, no redundancy)")

    print(f"\n📦 UATP Capsule Chain: {len(capsule_chain)} capsules")
    print(f"   ⚠️  WARNING: No UATP attribution! This will increase premiums.")

    print(f"\n⚠️  Historical Incidents: {len(historical_incidents)}")
    for incident in historical_incidents:
        print(f"   - {incident.risk_category.value}: ${incident.damage_estimated_cost}")

    # Run risk assessment
    print("\n⚙️  Running risk assessment...")
    assessment = assessor.assess_physical_risk(
        ai_system_type=robot_info["type"],
        ai_system_id=robot_info["id"],
        operating_environment=operating_environment,
        capsule_chain=capsule_chain,
        historical_incidents=historical_incidents,
    )

    # Display results
    print("\n" + "=" * 80)
    print("📊 RISK ASSESSMENT RESULTS")
    print("=" * 80)

    print(f"\n🎯 Composite Risk Score: {assessment['composite_risk_score']}/10")
    print(f"   Risk Level: {assessment['risk_level'].upper()}")

    print(f"\n💰 Insurance Premium:")
    print(f"   Base Annual: ${assessment['premium']['base_annual']:,.2f}")
    print(f"   Risk Adjusted: ${assessment['premium']['risk_adjusted']:,.2f}")
    print(
        f"   UATP Attribution Discount: {assessment['premium']['attribution_discount']*100:.0f}% (NONE - no capsules!)"
    )
    print(f"   Final Annual Premium: ${assessment['premium']['final_annual']:,.2f}")
    print(f"   Monthly Premium: ${assessment['premium']['monthly']:,.2f}")

    if assessment["recommendations"]:
        print(f"\n💡 CRITICAL Recommendations:")
        for i, rec in enumerate(assessment["recommendations"], 1):
            print(f"   {i}. {rec}")

    return assessment


def compare_scenarios():
    """Compare the two scenarios"""

    print("\n\n" + "=" * 80)
    print("📊 COMPARISON: Impact of UATP Attribution on Insurance")
    print("=" * 80)

    # Vehicle with good UATP (from first demo)
    vehicle_premium = 50000 * 1.2 * 0.8  # Estimate from first demo

    # Robot without UATP (from second demo)
    robot_premium_no_uatp = 20000 * 1.5 * 1.0  # No discount

    # Robot WITH UATP (hypothetical)
    robot_premium_with_uatp = 20000 * 1.2 * 0.8  # 20% discount

    print(f"\n1. Autonomous Vehicle (with UATP):")
    print(f"   Annual Premium: ~${vehicle_premium:,.2f}")
    print(f"   UATP Discount Applied: 20%")

    print(f"\n2. Warehouse Robot (NO UATP):")
    print(f"   Annual Premium: ~${robot_premium_no_uatp:,.2f}")
    print(f"   UATP Discount Applied: 0% ❌")

    print(f"\n3. Warehouse Robot (WITH UATP - hypothetical):")
    print(f"   Annual Premium: ~${robot_premium_with_uatp:,.2f}")
    print(f"   UATP Discount Applied: 20% ✅")
    print(f"   Annual Savings: ${robot_premium_no_uatp - robot_premium_with_uatp:,.2f}")

    print("\n" + "=" * 80)
    print("🎯 KEY INSIGHT:")
    print("=" * 80)
    print("\nUATP's capsule-based attribution provides:")
    print("  ✅ Complete audit trail of AI decisions")
    print("  ✅ Cryptographic verification of actions")
    print("  ✅ Clear liability attribution")
    print("  ✅ 15-20% insurance premium discount")
    print("\nFor a fleet of 100 robots:")
    savings_per_robot = robot_premium_no_uatp - robot_premium_with_uatp
    total_savings = savings_per_robot * 100
    print(f"  Total Annual Savings: ${total_savings:,.2f}")
    print(
        f"  ROI on UATP: {(total_savings / 50000 * 100):.0f}% (if UATP costs $50K/year)"
    )


if __name__ == "__main__":
    print("\n🏥 UATP Physical AI Insurance Demo")
    print("Demonstrating insurance for spatial/physical AI systems\n")

    # Run demos
    assessment1 = demo_autonomous_vehicle_insurance()
    assessment2 = demo_warehouse_robot_insurance()

    # Compare
    compare_scenarios()

    # Save results
    results = {"autonomous_vehicle": assessment1, "warehouse_robot": assessment2}

    with open("physical_ai_insurance_demo.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n\n💾 Full results saved to: physical_ai_insurance_demo.json")
    print("\n✅ Demo complete!")
    print("\n" + "=" * 80)
