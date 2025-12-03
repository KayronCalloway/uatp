"""
Physical AI Insurance Extension for UATP
Adds spatial/physical risk assessment for robotics, autonomous vehicles, etc.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from decimal import Decimal

from .risk_assessment import RiskCategory, RiskLevel, InsuranceProduct

logger = logging.getLogger(__name__)


class PhysicalRiskCategory(str, Enum):
    """Physical AI-specific risk categories"""

    COLLISION_DAMAGE = "collision_damage"
    PROPERTY_DAMAGE = "property_damage"
    PERSONAL_INJURY = "personal_injury"
    NAVIGATION_FAILURE = "navigation_failure"
    MANIPULATION_ERROR = "manipulation_error"
    SENSOR_MALFUNCTION = "sensor_malfunction"
    AUTONOMOUS_DECISION_ERROR = "autonomous_decision_error"
    PHYSICAL_SYSTEM_FAILURE = "physical_system_failure"
    ENVIRONMENTAL_HAZARD = "environmental_hazard"
    SAFETY_PROTOCOL_VIOLATION = "safety_protocol_violation"


class PhysicalAIType(str, Enum):
    """Types of physical AI systems"""

    AUTONOMOUS_VEHICLE = "autonomous_vehicle"
    ROBOT_ARM = "robot_arm"
    MOBILE_ROBOT = "mobile_robot"
    DRONE = "drone"
    HUMANOID_ROBOT = "humanoid_robot"
    SURGICAL_ROBOT = "surgical_robot"
    WAREHOUSE_ROBOT = "warehouse_robot"
    AGRICULTURAL_ROBOT = "agricultural_robot"
    CONSTRUCTION_ROBOT = "construction_robot"


@dataclass
class PhysicalIncident:
    """Physical AI incident data"""

    incident_id: str
    timestamp: datetime
    ai_system_type: PhysicalAIType
    ai_system_id: str
    risk_category: PhysicalRiskCategory

    # Physical details
    location: Dict[str, float]  # {x, y, z, lat, lon, etc.}
    damage_description: str
    damage_estimated_cost: Decimal

    # Sensor data at time of incident
    sensor_readings: Dict[str, Any]
    action_being_performed: str
    system_state: Dict[str, Any]

    # Capsule references
    perception_capsule_id: Optional[str] = None
    reasoning_capsule_id: Optional[str] = None
    action_capsule_id: Optional[str] = None

    # Liability
    human_intervention_available: bool = False
    safety_protocols_active: bool = True
    environmental_factors: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "timestamp": self.timestamp.isoformat(),
            "ai_system_type": self.ai_system_type.value,
            "ai_system_id": self.ai_system_id,
            "risk_category": self.risk_category.value,
            "location": self.location,
            "damage_description": self.damage_description,
            "damage_estimated_cost": float(self.damage_estimated_cost),
            "action_being_performed": self.action_being_performed,
            "capsule_references": {
                "perception": self.perception_capsule_id,
                "reasoning": self.reasoning_capsule_id,
                "action": self.action_capsule_id,
            },
            "safety_context": {
                "human_intervention_available": self.human_intervention_available,
                "safety_protocols_active": self.safety_protocols_active,
                "environmental_factors": self.environmental_factors or [],
            },
        }


class PhysicalAIRiskAssessor:
    """
    Risk assessment for physical/spatial AI systems
    Integrates with existing UATP insurance infrastructure
    """

    def __init__(self):
        self.incident_history: List[PhysicalIncident] = []

        # Risk multipliers by AI system type
        self.system_type_risk_multipliers = {
            PhysicalAIType.AUTONOMOUS_VEHICLE: 3.0,  # High risk
            PhysicalAIType.SURGICAL_ROBOT: 5.0,  # Very high risk
            PhysicalAIType.HUMANOID_ROBOT: 2.5,
            PhysicalAIType.DRONE: 2.0,
            PhysicalAIType.ROBOT_ARM: 1.5,
            PhysicalAIType.MOBILE_ROBOT: 1.8,
            PhysicalAIType.WAREHOUSE_ROBOT: 1.3,
            PhysicalAIType.AGRICULTURAL_ROBOT: 1.2,
            PhysicalAIType.CONSTRUCTION_ROBOT: 2.2,
        }

    def assess_physical_risk(
        self,
        ai_system_type: PhysicalAIType,
        ai_system_id: str,
        operating_environment: Dict[str, Any],
        capsule_chain: List[Dict[str, Any]],
        historical_incidents: List[PhysicalIncident] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive physical AI risk assessment
        """

        # 1. Base risk from system type
        base_risk_multiplier = self.system_type_risk_multipliers.get(
            ai_system_type, 2.0  # Default moderate-high risk
        )

        # 2. Environment risk factors
        env_risk_score = self._assess_environment_risk(operating_environment)

        # 3. Capsule chain analysis (audit trail quality)
        capsule_quality_score = self._assess_capsule_chain_quality(capsule_chain)

        # 4. Historical incident analysis
        incident_risk_score = self._assess_historical_incidents(
            historical_incidents or [], ai_system_id
        )

        # 5. Safety protocol verification
        safety_score = self._assess_safety_protocols(operating_environment)

        # Calculate overall risk
        risk_scores = {
            "base_risk": base_risk_multiplier,
            "environment_risk": env_risk_score,
            "capsule_quality": capsule_quality_score,
            "historical_incidents": incident_risk_score,
            "safety_protocols": safety_score,
        }

        # Weighted composite risk score (0-10 scale)
        composite_risk = (
            base_risk_multiplier * 0.25
            + env_risk_score * 0.20
            + (10 - capsule_quality_score) * 0.25
            + incident_risk_score * 0.20  # Invert: better capsules = lower risk
            + (10 - safety_score) * 0.10  # Invert: better safety = lower risk
        )

        # Determine risk level
        if composite_risk >= 8.0:
            risk_level = RiskLevel.CRITICAL
        elif composite_risk >= 6.5:
            risk_level = RiskLevel.VERY_HIGH
        elif composite_risk >= 5.0:
            risk_level = RiskLevel.HIGH
        elif composite_risk >= 3.5:
            risk_level = RiskLevel.MEDIUM
        elif composite_risk >= 2.0:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.VERY_LOW

        # Calculate premium
        base_annual_premium = self._calculate_base_premium(
            ai_system_type, operating_environment
        )

        # Calculate risk-adjusted reference (not a quote - for insurer analysis only)
        risk_adjusted_reference = base_annual_premium * (
            Decimal(str(composite_risk)) / Decimal("5.0")
        )

        # Provide capsule quality data for insurers to assess
        # Note: Actual premium adjustments determined by insurance underwriters
        attribution_quality_tier = self._get_attribution_quality_tier(
            capsule_quality_score
        )

        return {
            "assessment_id": f"physical_ai_risk_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "ai_system": {"type": ai_system_type.value, "id": ai_system_id},
            "risk_scores": risk_scores,
            "composite_risk_score": round(composite_risk, 2),
            "risk_level": risk_level.value,
            "attribution_quality": {
                "score": round(capsule_quality_score, 2),
                "tier": attribution_quality_tier,
                "capsule_chain_complete": len(capsule_chain) >= 3,
                "capsule_count": len(capsule_chain),
                "verification_rate": sum(
                    1
                    for c in capsule_chain
                    if c.get("verification", {}).get("verified", False)
                )
                / len(capsule_chain)
                if capsule_chain
                else 0,
            },
            "risk_reference": {
                "base_annual": float(base_annual_premium),
                "risk_adjusted_reference": float(risk_adjusted_reference),
                "note": "Reference values only. Actual premiums determined by insurance underwriters based on their actuarial models.",
            },
            "recommendations": self._generate_recommendations(
                risk_level, risk_scores, capsule_quality_score
            ),
            "coverage_limits": self._recommend_coverage_limits(
                ai_system_type, composite_risk
            ),
        }

    def _assess_environment_risk(self, environment: Dict[str, Any]) -> float:
        """Assess risk based on operating environment"""
        risk = 5.0  # Base medium risk

        # Public vs private space
        if environment.get("public_space", False):
            risk += 2.0

        # Human presence
        human_density = environment.get("human_density", "low")
        if human_density == "high":
            risk += 2.0
        elif human_density == "medium":
            risk += 1.0

        # Speed/velocity capabilities
        max_speed = environment.get("max_speed_mps", 0)
        if max_speed > 20:  # >70 km/h
            risk += 2.0
        elif max_speed > 10:  # >36 km/h
            risk += 1.0

        # Weather/conditions
        if environment.get("adverse_conditions", False):
            risk += 1.0

        # Complexity of environment
        complexity = environment.get("environment_complexity", "medium")
        if complexity == "high":
            risk += 1.5
        elif complexity == "low":
            risk -= 1.0

        return min(10.0, max(0.0, risk))

    def _assess_capsule_chain_quality(
        self, capsule_chain: List[Dict[str, Any]]
    ) -> float:
        """Assess quality of UATP capsule chain (audit trail)"""
        if not capsule_chain:
            return 0.0  # No audit trail = maximum risk

        quality = 5.0

        # Check for key capsule types
        has_perception = any(
            c.get("type") == "spatial_perception" for c in capsule_chain
        )
        has_reasoning = any(c.get("type") == "spatial_reasoning" for c in capsule_chain)
        has_action = any(c.get("type") == "physical_action" for c in capsule_chain)

        if has_perception:
            quality += 1.5
        if has_reasoning:
            quality += 1.5
        if has_action:
            quality += 1.0

        # Verification status
        all_verified = all(
            c.get("verification", {}).get("verified", False) for c in capsule_chain
        )
        if all_verified:
            quality += 2.0

        # Chain completeness
        avg_confidence = sum(c.get("confidence", 0.5) for c in capsule_chain) / len(
            capsule_chain
        )

        if avg_confidence >= 0.9:
            quality += 1.0
        elif avg_confidence >= 0.8:
            quality += 0.5

        return min(10.0, quality)

    def _assess_historical_incidents(
        self, incidents: List[PhysicalIncident], system_id: str
    ) -> float:
        """Assess risk based on historical incidents"""
        if not incidents:
            return 3.0  # Neutral risk (no history)

        # Filter incidents for this system
        system_incidents = [i for i in incidents if i.ai_system_id == system_id]

        if not system_incidents:
            return 3.0

        # Recent incidents are weighted more heavily
        recent_incidents = [
            i for i in system_incidents if (datetime.now() - i.timestamp).days <= 90
        ]

        risk = 3.0

        # Recent incident count
        if len(recent_incidents) > 5:
            risk += 3.0
        elif len(recent_incidents) > 2:
            risk += 1.5
        elif len(recent_incidents) == 0:
            risk -= 1.0

        # Severity of incidents
        if system_incidents:
            avg_cost = sum(i.damage_estimated_cost for i in system_incidents) / len(
                system_incidents
            )

            if avg_cost > 100000:  # >$100K average
                risk += 2.0
            elif avg_cost > 10000:  # >$10K average
                risk += 1.0

        return min(10.0, max(0.0, risk))

    def _assess_safety_protocols(self, environment: Dict[str, Any]) -> float:
        """Assess safety protocol implementation"""
        safety_score = 5.0

        # Emergency stop capability
        if environment.get("emergency_stop_available", False):
            safety_score += 2.0

        # Human override
        if environment.get("human_override_available", False):
            safety_score += 1.5

        # Redundant sensors
        if environment.get("redundant_sensors", False):
            safety_score += 1.0

        # Geofencing/operational boundaries
        if environment.get("geofencing_enabled", False):
            safety_score += 1.0

        # Regular maintenance
        if environment.get("regular_maintenance", False):
            safety_score += 0.5

        return min(10.0, safety_score)

    def _calculate_base_premium(
        self, ai_system_type: PhysicalAIType, environment: Dict[str, Any]
    ) -> Decimal:
        """Calculate base annual premium"""

        # Base premiums by system type (annual)
        base_premiums = {
            PhysicalAIType.AUTONOMOUS_VEHICLE: Decimal("50000"),
            PhysicalAIType.SURGICAL_ROBOT: Decimal("150000"),
            PhysicalAIType.HUMANOID_ROBOT: Decimal("75000"),
            PhysicalAIType.DRONE: Decimal("15000"),
            PhysicalAIType.ROBOT_ARM: Decimal("25000"),
            PhysicalAIType.MOBILE_ROBOT: Decimal("30000"),
            PhysicalAIType.WAREHOUSE_ROBOT: Decimal("20000"),
            PhysicalAIType.AGRICULTURAL_ROBOT: Decimal("18000"),
            PhysicalAIType.CONSTRUCTION_ROBOT: Decimal("40000"),
        }

        return base_premiums.get(ai_system_type, Decimal("30000"))

    def _generate_recommendations(
        self,
        risk_level: RiskLevel,
        risk_scores: Dict[str, float],
        capsule_quality: float,
    ) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []

        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.CRITICAL]:
            recommendations.append(
                "HIGH RISK: Consider enhanced safety protocols and additional monitoring"
            )

        if risk_scores["environment_risk"] > 7.0:
            recommendations.append(
                "Reduce operational speed or limit operations in high-risk environments"
            )

        if capsule_quality < 6.0:
            recommendations.append(
                "CRITICAL: Improve UATP capsule chain quality for better risk assessment data"
            )
            recommendations.append(
                "Implement comprehensive perception, planning, and control capsules"
            )

        if risk_scores["historical_incidents"] > 6.0:
            recommendations.append(
                "Address recurring incident patterns through system upgrades or retraining"
            )

        if risk_scores["safety_protocols"] < 6.0:
            recommendations.append(
                "Enhance safety protocols: emergency stops, human override, redundant sensors"
            )

        return recommendations

    def _recommend_coverage_limits(
        self, ai_system_type: PhysicalAIType, composite_risk: float
    ) -> Dict[str, Any]:
        """Recommend insurance coverage limits"""

        # Base coverage by system type
        if ai_system_type == PhysicalAIType.SURGICAL_ROBOT:
            base_coverage = 10_000_000  # $10M
        elif ai_system_type == PhysicalAIType.AUTONOMOUS_VEHICLE:
            base_coverage = 5_000_000  # $5M
        elif ai_system_type in [
            PhysicalAIType.HUMANOID_ROBOT,
            PhysicalAIType.CONSTRUCTION_ROBOT,
        ]:
            base_coverage = 3_000_000  # $3M
        else:
            base_coverage = 1_000_000  # $1M

        # Adjust for risk
        if composite_risk > 7.0:
            recommended_coverage = base_coverage * 2
        elif composite_risk > 5.0:
            recommended_coverage = base_coverage * 1.5
        else:
            recommended_coverage = base_coverage

        return {
            "general_liability": recommended_coverage,
            "property_damage": recommended_coverage * 0.5,
            "bodily_injury": recommended_coverage,
            "cyber_liability": recommended_coverage * 0.3,
            "total_recommended": recommended_coverage * 2.8,
        }

    def _get_attribution_quality_tier(self, capsule_quality_score: float) -> str:
        """Classify attribution quality for insurance assessment"""
        if capsule_quality_score >= 8.0:
            return "excellent"
        elif capsule_quality_score >= 6.0:
            return "good"
        elif capsule_quality_score >= 4.0:
            return "fair"
        else:
            return "poor"

    def record_incident(self, incident: PhysicalIncident):
        """Record a physical AI incident"""
        self.incident_history.append(incident)
        logger.warning(
            f"Physical AI incident recorded: {incident.incident_id} - "
            f"{incident.risk_category.value} - "
            f"Estimated cost: ${incident.damage_estimated_cost}"
        )


# Global instance
physical_ai_risk_assessor = PhysicalAIRiskAssessor()
