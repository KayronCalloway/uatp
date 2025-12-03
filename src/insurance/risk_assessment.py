"""
Insurance Risk Assessment API for AI Interactions in UATP Capsule Engine.

This module provides comprehensive risk assessment capabilities for AI-related
insurance products, analyzing interaction patterns, attribution risks, consent
compliance, and economic exposure to generate risk profiles and premium calculations.
"""

import logging
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from src.ai_rights.consent_manager import ai_consent_manager
from src.ai_rights.dispute_resolution import dispute_resolution_system
from src.audit.events import audit_emitter

logger = logging.getLogger(__name__)


class RiskCategory(str, Enum):
    """Categories of insurance risk."""

    ATTRIBUTION_LIABILITY = "attribution_liability"
    CONSENT_VIOLATION = "consent_violation"
    ECONOMIC_LOSS = "economic_loss"
    TECHNICAL_FAILURE = "technical_failure"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    DATA_BREACH = "data_breach"
    OPERATIONAL_DISRUPTION = "operational_disruption"


class RiskLevel(str, Enum):
    """Risk severity levels."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"


class InsuranceProduct(str, Enum):
    """Types of AI insurance products."""

    AI_LIABILITY = "ai_liability"
    ATTRIBUTION_PROTECTION = "attribution_protection"
    CONSENT_COMPLIANCE = "consent_compliance"
    ECONOMIC_LOSS_COVERAGE = "economic_loss_coverage"
    COMPREHENSIVE_AI = "comprehensive_ai"
    CYBER_LIABILITY = "cyber_liability"
    PROFESSIONAL_INDEMNITY = "professional_indemnity"


@dataclass
class RiskFactor:
    """Individual risk factor in assessment."""

    factor_id: str
    category: RiskCategory
    description: str
    severity: float  # 0.0 to 1.0
    probability: float  # 0.0 to 1.0
    potential_impact: float  # Economic impact in USD
    mitigation_measures: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)

    @property
    def risk_score(self) -> float:
        """Calculate combined risk score."""
        return (
            self.severity * self.probability * min(1.0, self.potential_impact / 10000.0)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert risk factor to dictionary."""
        return {
            "factor_id": self.factor_id,
            "category": self.category.value,
            "description": self.description,
            "severity": self.severity,
            "probability": self.probability,
            "potential_impact": self.potential_impact,
            "risk_score": self.risk_score,
            "mitigation_measures": self.mitigation_measures,
            "evidence": self.evidence,
        }


@dataclass
class InteractionPattern:
    """Pattern of AI interactions for risk assessment."""

    pattern_id: str
    ai_entity_id: str
    interaction_count: int
    time_period_days: int
    usage_types: List[str]
    consent_compliance_rate: float
    attribution_accuracy: float
    dispute_rate: float
    economic_volume: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "ai_entity_id": self.ai_entity_id,
            "interaction_count": self.interaction_count,
            "time_period_days": self.time_period_days,
            "usage_types": self.usage_types,
            "consent_compliance_rate": self.consent_compliance_rate,
            "attribution_accuracy": self.attribution_accuracy,
            "dispute_rate": self.dispute_rate,
            "economic_volume": self.economic_volume,
        }


@dataclass
class RiskProfile:
    """Comprehensive risk profile for an entity."""

    profile_id: str
    entity_id: str
    entity_type: str  # "ai", "organization", "platform"
    assessment_date: datetime
    overall_risk_level: RiskLevel
    overall_risk_score: float
    risk_factors: List[RiskFactor]
    interaction_patterns: List[InteractionPattern]
    historical_claims: List[Dict[str, Any]] = field(default_factory=list)
    compliance_score: float = 1.0

    @property
    def category_scores(self) -> Dict[str, float]:
        """Get risk scores by category."""
        category_scores = {}
        for factor in self.risk_factors:
            category = factor.category.value
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(factor.risk_score)

        return {
            category: sum(scores) / len(scores) if scores else 0.0
            for category, scores in category_scores.items()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return {
            "profile_id": self.profile_id,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "assessment_date": self.assessment_date.isoformat(),
            "overall_risk_level": self.overall_risk_level.value,
            "overall_risk_score": self.overall_risk_score,
            "compliance_score": self.compliance_score,
            "category_scores": self.category_scores,
            "risk_factors_count": len(self.risk_factors),
            "interaction_patterns_count": len(self.interaction_patterns),
            "historical_claims_count": len(self.historical_claims),
        }


@dataclass
class PremiumCalculation:
    """Insurance premium calculation."""

    calculation_id: str
    entity_id: str
    product_type: InsuranceProduct
    base_premium: Decimal
    risk_multiplier: float
    final_premium: Decimal
    coverage_amount: Decimal
    deductible: Decimal
    calculation_factors: Dict[str, Any]
    valid_until: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert calculation to dictionary."""
        return {
            "calculation_id": self.calculation_id,
            "entity_id": self.entity_id,
            "product_type": self.product_type.value,
            "base_premium": float(self.base_premium),
            "risk_multiplier": self.risk_multiplier,
            "final_premium": float(self.final_premium),
            "coverage_amount": float(self.coverage_amount),
            "deductible": float(self.deductible),
            "calculation_factors": self.calculation_factors,
            "valid_until": self.valid_until.isoformat(),
        }


class RiskAssessmentEngine:
    """Core risk assessment engine for AI insurance."""

    def __init__(self):
        self.risk_profiles: Dict[str, RiskProfile] = {}
        self.premium_calculations: Dict[str, PremiumCalculation] = {}
        self.assessment_history: List[Dict[str, Any]] = []

        # Risk thresholds and weights
        self.risk_thresholds = {
            RiskLevel.VERY_LOW: 0.1,
            RiskLevel.LOW: 0.25,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.75,
            RiskLevel.VERY_HIGH: 0.9,
            RiskLevel.CRITICAL: 1.0,
        }

        # Premium base rates by product (annual premium per $1000 coverage)
        self.base_premium_rates = {
            InsuranceProduct.AI_LIABILITY: Decimal("5.00"),
            InsuranceProduct.ATTRIBUTION_PROTECTION: Decimal("3.50"),
            InsuranceProduct.CONSENT_COMPLIANCE: Decimal("2.50"),
            InsuranceProduct.ECONOMIC_LOSS_COVERAGE: Decimal("4.00"),
            InsuranceProduct.COMPREHENSIVE_AI: Decimal("8.00"),
            InsuranceProduct.CYBER_LIABILITY: Decimal("6.00"),
            InsuranceProduct.PROFESSIONAL_INDEMNITY: Decimal("3.00"),
        }

    def generate_profile_id(self) -> str:
        """Generate unique profile ID."""
        return f"profile_{uuid.uuid4()}"

    def generate_calculation_id(self) -> str:
        """Generate unique calculation ID."""
        return f"calc_{uuid.uuid4()}"

    async def assess_entity_risk(
        self, entity_id: str, entity_type: str, assessment_scope: Dict[str, Any] = None
    ) -> RiskProfile:
        """Perform comprehensive risk assessment for an entity."""

        logger.info(f"Starting risk assessment for {entity_type} entity: {entity_id}")

        assessment_scope = assessment_scope or {}
        profile_id = self.generate_profile_id()

        # Gather risk factors
        risk_factors = []

        # Assess attribution liability risk
        attribution_risk = await self._assess_attribution_risk(entity_id)
        if attribution_risk:
            risk_factors.append(attribution_risk)

        # Assess consent compliance risk
        consent_risk = await self._assess_consent_risk(entity_id)
        if consent_risk:
            risk_factors.append(consent_risk)

        # Assess economic exposure risk
        economic_risk = await self._assess_economic_risk(entity_id)
        if economic_risk:
            risk_factors.append(economic_risk)

        # Assess technical failure risk
        technical_risk = await self._assess_technical_risk(entity_id)
        if technical_risk:
            risk_factors.append(technical_risk)

        # Assess regulatory compliance risk
        regulatory_risk = await self._assess_regulatory_risk(entity_id)
        if regulatory_risk:
            risk_factors.append(regulatory_risk)

        # Analyze interaction patterns
        interaction_patterns = await self._analyze_interaction_patterns(entity_id)

        # Calculate overall risk score
        overall_risk_score = self._calculate_overall_risk_score(risk_factors)
        overall_risk_level = self._determine_risk_level(overall_risk_score)

        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(entity_id)

        # Get historical claims
        historical_claims = self._get_historical_claims(entity_id)

        # Create risk profile
        risk_profile = RiskProfile(
            profile_id=profile_id,
            entity_id=entity_id,
            entity_type=entity_type,
            assessment_date=datetime.now(timezone.utc),
            overall_risk_level=overall_risk_level,
            overall_risk_score=overall_risk_score,
            risk_factors=risk_factors,
            interaction_patterns=interaction_patterns,
            historical_claims=historical_claims,
            compliance_score=compliance_score,
        )

        # Store profile
        self.risk_profiles[entity_id] = risk_profile

        # Record assessment
        self.assessment_history.append(
            {
                "assessment_id": str(uuid.uuid4()),
                "entity_id": entity_id,
                "entity_type": entity_type,
                "assessment_date": datetime.now(timezone.utc).isoformat(),
                "risk_level": overall_risk_level.value,
                "risk_score": overall_risk_score,
                "factors_count": len(risk_factors),
            }
        )

        audit_emitter.emit_security_event(
            "risk_assessment_completed",
            {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "risk_level": overall_risk_level.value,
                "risk_score": overall_risk_score,
            },
        )

        logger.info(
            f"Risk assessment completed for {entity_id}: {overall_risk_level.value}"
        )
        return risk_profile

    async def _assess_attribution_risk(self, entity_id: str) -> Optional[RiskFactor]:
        """Assess attribution liability risk."""

        # Search for attribution disputes involving this entity
        disputes = dispute_resolution_system.search_disputes(
            {"respondent_id": entity_id, "dispute_type": "attribution_ownership"}
        )

        dispute_count = len(disputes)
        recent_disputes = len(
            [
                d
                for d in disputes
                if datetime.fromisoformat(d["submitted_at"])
                > datetime.now(timezone.utc) - timedelta(days=90)
            ]
        )

        # Calculate risk factors
        if dispute_count == 0:
            severity = 0.1
            probability = 0.05
        elif dispute_count <= 2:
            severity = 0.3
            probability = 0.2
        elif dispute_count <= 5:
            severity = 0.6
            probability = 0.4
        else:
            severity = 0.9
            probability = 0.7

        # Increase risk for recent disputes
        if recent_disputes > 0:
            severity = min(1.0, severity + 0.2)
            probability = min(1.0, probability + 0.3)

        potential_impact = dispute_count * 5000.0  # Estimated legal costs per dispute

        return RiskFactor(
            factor_id=f"attr_risk_{entity_id}",
            category=RiskCategory.ATTRIBUTION_LIABILITY,
            description=f"Attribution liability risk based on {dispute_count} historical disputes",
            severity=severity,
            probability=probability,
            potential_impact=potential_impact,
            evidence={
                "total_disputes": dispute_count,
                "recent_disputes": recent_disputes,
                "dispute_details": disputes[-3:] if disputes else [],  # Last 3 disputes
            },
        )

    async def _assess_consent_risk(self, entity_id: str) -> Optional[RiskFactor]:
        """Assess consent compliance risk."""

        # Check consent profile with consent manager
        consent_summary = ai_consent_manager.get_consent_summary(entity_id)

        if "error" in consent_summary:
            # No consent profile - high risk
            return RiskFactor(
                factor_id=f"consent_risk_{entity_id}",
                category=RiskCategory.CONSENT_VIOLATION,
                description="No consent profile found - high compliance risk",
                severity=0.8,
                probability=0.6,
                potential_impact=10000.0,
                evidence={"consent_profile_exists": False},
            )

        # Analyze consent preferences
        preferences = consent_summary.get("preferences", {})

        # Calculate risk based on consent restrictiveness
        opt_out_count = sum(
            1 for p in preferences.values() if p["consent_level"] == "opt_out"
        )
        conditional_count = sum(
            1
            for p in preferences.values()
            if p["consent_level"] == "conditional_consent"
        )

        total_preferences = len(preferences)
        if total_preferences == 0:
            risk_ratio = 1.0
        else:
            risk_ratio = (opt_out_count * 2 + conditional_count) / (
                total_preferences * 2
            )

        severity = risk_ratio * 0.7
        probability = risk_ratio * 0.5
        potential_impact = risk_ratio * 15000.0

        return RiskFactor(
            factor_id=f"consent_risk_{entity_id}",
            category=RiskCategory.CONSENT_VIOLATION,
            description=f"Consent compliance risk (restrictiveness: {risk_ratio:.2f})",
            severity=severity,
            probability=probability,
            potential_impact=potential_impact,
            evidence={
                "total_preferences": total_preferences,
                "opt_out_count": opt_out_count,
                "conditional_count": conditional_count,
                "risk_ratio": risk_ratio,
            },
        )

    async def _assess_economic_risk(self, entity_id: str) -> Optional[RiskFactor]:
        """Assess economic exposure risk."""

        # This would integrate with economic attribution system
        # For now, simulate based on entity activity

        # Estimate economic exposure based on entity type and activity
        estimated_monthly_volume = 5000.0  # Placeholder
        annual_exposure = estimated_monthly_volume * 12

        # Higher exposure = higher risk
        if annual_exposure < 10000:
            severity = 0.2
            probability = 0.1
        elif annual_exposure < 50000:
            severity = 0.4
            probability = 0.2
        elif annual_exposure < 200000:
            severity = 0.6
            probability = 0.3
        else:
            severity = 0.8
            probability = 0.4

        potential_impact = annual_exposure * 0.1  # 10% of exposure

        return RiskFactor(
            factor_id=f"economic_risk_{entity_id}",
            category=RiskCategory.ECONOMIC_LOSS,
            description=f"Economic exposure risk (annual volume: ${annual_exposure:,.0f})",
            severity=severity,
            probability=probability,
            potential_impact=potential_impact,
            evidence={
                "estimated_annual_volume": annual_exposure,
                "monthly_volume": estimated_monthly_volume,
            },
        )

    async def _assess_technical_risk(self, entity_id: str) -> Optional[RiskFactor]:
        """Assess technical failure risk."""

        # Simulate technical risk assessment
        # In production, this would analyze system reliability metrics

        return RiskFactor(
            factor_id=f"technical_risk_{entity_id}",
            category=RiskCategory.TECHNICAL_FAILURE,
            description="Technical system failure risk",
            severity=0.3,
            probability=0.15,
            potential_impact=25000.0,
            evidence={
                "system_uptime": "99.5%",
                "failure_modes": [
                    "attribution_calculation_error",
                    "consent_system_outage",
                ],
            },
        )

    async def _assess_regulatory_risk(self, entity_id: str) -> Optional[RiskFactor]:
        """Assess regulatory compliance risk."""

        return RiskFactor(
            factor_id=f"regulatory_risk_{entity_id}",
            category=RiskCategory.REGULATORY_COMPLIANCE,
            description="Regulatory compliance risk",
            severity=0.4,
            probability=0.2,
            potential_impact=50000.0,
            evidence={
                "applicable_regulations": ["GDPR", "CCPA", "AI_ACT"],
                "compliance_framework": "UATP_STANDARDS",
            },
        )

    async def _analyze_interaction_patterns(
        self, entity_id: str
    ) -> List[InteractionPattern]:
        """Analyze entity interaction patterns."""

        # Simulate interaction pattern analysis
        # In production, this would query actual interaction data

        pattern = InteractionPattern(
            pattern_id=f"pattern_{entity_id}_{datetime.now().strftime('%Y%m')}",
            ai_entity_id=entity_id,
            interaction_count=1500,
            time_period_days=30,
            usage_types=["reasoning_visibility", "commercial_usage", "research_usage"],
            consent_compliance_rate=0.92,
            attribution_accuracy=0.88,
            dispute_rate=0.02,
            economic_volume=12500.0,
        )

        return [pattern]

    def _calculate_overall_risk_score(self, risk_factors: List[RiskFactor]) -> float:
        """Calculate overall risk score from individual factors."""

        if not risk_factors:
            return 0.0

        # Weight factors by category
        category_weights = {
            RiskCategory.ATTRIBUTION_LIABILITY: 0.25,
            RiskCategory.CONSENT_VIOLATION: 0.20,
            RiskCategory.ECONOMIC_LOSS: 0.20,
            RiskCategory.TECHNICAL_FAILURE: 0.15,
            RiskCategory.REGULATORY_COMPLIANCE: 0.15,
            RiskCategory.INTELLECTUAL_PROPERTY: 0.05,
        }

        weighted_scores = []
        for factor in risk_factors:
            weight = category_weights.get(factor.category, 0.1)
            weighted_scores.append(factor.risk_score * weight)

        return min(1.0, sum(weighted_scores))

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from risk score."""

        for level, threshold in reversed(list(self.risk_thresholds.items())):
            if risk_score >= threshold:
                return level

        return RiskLevel.VERY_LOW

    def _calculate_compliance_score(self, entity_id: str) -> float:
        """Calculate compliance score for entity."""

        # Check consent compliance
        consent_summary = ai_consent_manager.get_consent_summary(entity_id)
        consent_score = 0.8 if "error" not in consent_summary else 0.3

        # Check dispute history
        disputes = dispute_resolution_system.search_disputes(
            {"respondent_id": entity_id}
        )
        dispute_penalty = min(0.5, len(disputes) * 0.1)
        dispute_score = max(0.0, 1.0 - dispute_penalty)

        # Combine scores
        return consent_score * 0.6 + dispute_score * 0.4

    def _get_historical_claims(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get historical insurance claims for entity."""

        # Simulate historical claims
        # In production, this would query claims database
        return []

    def calculate_premium(
        self,
        entity_id: str,
        product_type: InsuranceProduct,
        coverage_amount: Decimal,
        custom_parameters: Dict[str, Any] = None,
    ) -> PremiumCalculation:
        """Calculate insurance premium for entity and product."""

        if entity_id not in self.risk_profiles:
            raise ValueError(f"Risk profile not found for entity {entity_id}")

        risk_profile = self.risk_profiles[entity_id]
        custom_parameters = custom_parameters or {}

        # Get base premium rate
        base_rate = self.base_premium_rates.get(product_type, Decimal("5.00"))
        base_premium = (coverage_amount / Decimal("1000")) * base_rate

        # Calculate risk multiplier
        risk_multiplier = self._calculate_risk_multiplier(risk_profile, product_type)

        # Apply custom adjustments
        if "discount_factor" in custom_parameters:
            risk_multiplier *= custom_parameters["discount_factor"]

        if "surcharge_factor" in custom_parameters:
            risk_multiplier *= custom_parameters["surcharge_factor"]

        # Calculate final premium
        final_premium = base_premium * Decimal(str(risk_multiplier))

        # Determine deductible
        deductible = self._calculate_deductible(coverage_amount, risk_profile)

        # Create calculation
        calculation = PremiumCalculation(
            calculation_id=self.generate_calculation_id(),
            entity_id=entity_id,
            product_type=product_type,
            base_premium=base_premium,
            risk_multiplier=risk_multiplier,
            final_premium=final_premium,
            coverage_amount=coverage_amount,
            deductible=deductible,
            calculation_factors={
                "risk_level": risk_profile.overall_risk_level.value,
                "risk_score": risk_profile.overall_risk_score,
                "compliance_score": risk_profile.compliance_score,
                "category_scores": risk_profile.category_scores,
                "custom_parameters": custom_parameters,
            },
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
        )

        # Store calculation
        self.premium_calculations[calculation.calculation_id] = calculation

        audit_emitter.emit_security_event(
            "premium_calculated",
            {
                "entity_id": entity_id,
                "product_type": product_type.value,
                "coverage_amount": float(coverage_amount),
                "final_premium": float(final_premium),
                "risk_multiplier": risk_multiplier,
            },
        )

        logger.info(
            f"Premium calculated for {entity_id}: ${final_premium:.2f} ({product_type.value})"
        )
        return calculation

    def _calculate_risk_multiplier(
        self, risk_profile: RiskProfile, product_type: InsuranceProduct
    ) -> float:
        """Calculate risk multiplier for premium calculation."""

        base_multiplier = 1.0

        # Risk level adjustments
        risk_adjustments = {
            RiskLevel.VERY_LOW: 0.7,
            RiskLevel.LOW: 0.85,
            RiskLevel.MEDIUM: 1.0,
            RiskLevel.HIGH: 1.5,
            RiskLevel.VERY_HIGH: 2.0,
            RiskLevel.CRITICAL: 3.0,
        }

        risk_multiplier = risk_adjustments.get(risk_profile.overall_risk_level, 1.0)

        # Compliance score adjustment
        compliance_adjustment = 2.0 - risk_profile.compliance_score  # Range: 1.0 to 2.0

        # Product-specific adjustments
        if product_type == InsuranceProduct.ATTRIBUTION_PROTECTION:
            # Focus on attribution liability risk
            attr_score = risk_profile.category_scores.get("attribution_liability", 0.0)
            risk_multiplier *= 1.0 + attr_score

        elif product_type == InsuranceProduct.CONSENT_COMPLIANCE:
            # Focus on consent violation risk
            consent_score = risk_profile.category_scores.get("consent_violation", 0.0)
            risk_multiplier *= 1.0 + consent_score

        # Combine factors
        final_multiplier = base_multiplier * risk_multiplier * compliance_adjustment

        # Cap multiplier
        return min(5.0, max(0.5, final_multiplier))

    def _calculate_deductible(
        self, coverage_amount: Decimal, risk_profile: RiskProfile
    ) -> Decimal:
        """Calculate deductible amount."""

        # Base deductible: 5% of coverage
        base_deductible = coverage_amount * Decimal("0.05")

        # Adjust based on risk level
        risk_adjustments = {
            RiskLevel.VERY_LOW: Decimal("0.02"),
            RiskLevel.LOW: Decimal("0.03"),
            RiskLevel.MEDIUM: Decimal("0.05"),
            RiskLevel.HIGH: Decimal("0.08"),
            RiskLevel.VERY_HIGH: Decimal("0.12"),
            RiskLevel.CRITICAL: Decimal("0.20"),
        }

        risk_rate = risk_adjustments.get(
            risk_profile.overall_risk_level, Decimal("0.05")
        )
        adjusted_deductible = coverage_amount * risk_rate

        # Minimum deductible: $500
        return max(Decimal("500"), adjusted_deductible)

    def get_risk_profile(self, entity_id: str) -> Optional[RiskProfile]:
        """Get risk profile for entity."""
        return self.risk_profiles.get(entity_id)

    def get_premium_calculation(
        self, calculation_id: str
    ) -> Optional[PremiumCalculation]:
        """Get premium calculation by ID."""
        return self.premium_calculations.get(calculation_id)

    def search_risk_profiles(self, filters: Dict[str, Any]) -> List[RiskProfile]:
        """Search risk profiles with filters."""

        results = []

        for profile in self.risk_profiles.values():
            match = True

            if "entity_type" in filters:
                if profile.entity_type != filters["entity_type"]:
                    match = False

            if "risk_level" in filters:
                if profile.overall_risk_level.value != filters["risk_level"]:
                    match = False

            if "min_risk_score" in filters:
                if profile.overall_risk_score < filters["min_risk_score"]:
                    match = False

            if "max_risk_score" in filters:
                if profile.overall_risk_score > filters["max_risk_score"]:
                    match = False

            if match:
                results.append(profile)

        return results

    def get_assessment_statistics(self) -> Dict[str, Any]:
        """Get risk assessment system statistics."""

        total_profiles = len(self.risk_profiles)

        if total_profiles == 0:
            return {
                "total_profiles": 0,
                "risk_level_distribution": {},
                "average_risk_score": 0.0,
                "assessment_history_count": len(self.assessment_history),
            }

        # Risk level distribution
        risk_distribution = {}
        risk_scores = []

        for profile in self.risk_profiles.values():
            level = profile.overall_risk_level.value
            risk_distribution[level] = risk_distribution.get(level, 0) + 1
            risk_scores.append(profile.overall_risk_score)

        return {
            "total_profiles": total_profiles,
            "risk_level_distribution": risk_distribution,
            "average_risk_score": statistics.mean(risk_scores),
            "median_risk_score": statistics.median(risk_scores),
            "assessment_history_count": len(self.assessment_history),
            "premium_calculations_count": len(self.premium_calculations),
        }


# Global risk assessment engine instance
risk_assessment_engine = RiskAssessmentEngine()


async def assess_ai_insurance_risk(
    ai_id: str, coverage_amount: float = 100000.0
) -> Dict[str, Any]:
    """Convenience function to assess AI insurance risk."""

    # Perform risk assessment
    risk_profile = await risk_assessment_engine.assess_entity_risk(ai_id, "ai")

    # Calculate premiums for different products
    coverage_decimal = Decimal(str(coverage_amount))
    premium_quotes = {}

    for product in [
        InsuranceProduct.AI_LIABILITY,
        InsuranceProduct.ATTRIBUTION_PROTECTION,
        InsuranceProduct.CONSENT_COMPLIANCE,
    ]:
        try:
            calculation = risk_assessment_engine.calculate_premium(
                ai_id, product, coverage_decimal
            )
            premium_quotes[product.value] = calculation.to_dict()
        except Exception as e:
            logger.warning(f"Failed to calculate premium for {product.value}: {e}")

    return {
        "risk_profile": risk_profile.to_dict(),
        "premium_quotes": premium_quotes,
        "assessment_summary": {
            "entity_id": ai_id,
            "risk_level": risk_profile.overall_risk_level.value,
            "risk_score": risk_profile.overall_risk_score,
            "compliance_score": risk_profile.compliance_score,
            "insurability": "standard"
            if risk_profile.overall_risk_score < 0.7
            else "high_risk",
        },
    }


def get_risk_assessment_dashboard() -> Dict[str, Any]:
    """Get comprehensive risk assessment dashboard."""

    stats = risk_assessment_engine.get_assessment_statistics()

    # Recent assessments
    recent_assessments = risk_assessment_engine.assessment_history[-10:]

    # High risk entities
    high_risk_profiles = risk_assessment_engine.search_risk_profiles(
        {"min_risk_score": 0.7}
    )

    return {
        "system_statistics": stats,
        "recent_assessments": recent_assessments,
        "high_risk_entities": [p.to_dict() for p in high_risk_profiles[:5]],
        "product_coverage": {
            "available_products": [p.value for p in InsuranceProduct],
            "premium_calculations_today": len(
                [
                    c
                    for c in risk_assessment_engine.premium_calculations.values()
                    if c.valid_until.date() == datetime.now().date()
                ]
            ),
        },
    }
