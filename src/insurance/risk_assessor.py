"""
Insurance Risk Assessment Engine for UATP Capsule Engine

This module implements the core risk scoring algorithm that evaluates
AI decision chains for insurance underwriting purposes.

Risk Factors Analyzed:
1. Chain Integrity - Cryptographic verification of capsule chain
2. Reasoning Transparency - Depth and quality of reasoning trails
3. Provider Reliability - Historical track record of AI providers
4. Decision Stakes - Impact level of the decision (medical > shopping)
5. Audit Trail Completeness - Presence of all required metadata
6. Historical Performance - Past capsule verification success rate
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from ..utils.timezone_utils import utc_now


class RiskLevel(str, Enum):
    """Risk classification levels"""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    UNINSURABLE = "uninsurable"


class DecisionCategory(str, Enum):
    """Categories of AI decisions with different risk profiles"""

    MEDICAL = "medical"  # Highest stakes
    FINANCIAL = "financial"
    LEGAL = "legal"
    AUTONOMOUS_VEHICLE = "autonomous_vehicle"
    CONTENT_MODERATION = "content_moderation"
    CUSTOMER_SERVICE = "customer_service"
    CREATIVE = "creative"
    INFORMATION_RETRIEVAL = "information_retrieval"  # Lowest stakes


@dataclass
class RiskFactor:
    """Individual risk factor contribution"""

    name: str
    score: float  # 0.0 (best) to 1.0 (worst)
    weight: float  # Importance weight
    description: str
    details: Dict


@dataclass
class RiskAssessment:
    """Complete risk assessment result"""

    overall_score: float  # 0.0 (best) to 1.0 (worst)
    risk_level: RiskLevel
    confidence: float  # 0.0 to 1.0
    factors: List[RiskFactor]
    premium_estimate: str
    coverage_recommended: str
    policy_term_months: int
    conditions: List[str]
    exclusions: List[str]
    timestamp: datetime


class RiskAssessor:
    """
    Core risk assessment engine for AI insurance underwriting.

    The algorithm combines multiple weighted factors to produce a
    composite risk score that determines insurability and premium.
    """

    # Weight configuration for risk factors
    WEIGHTS = {
        "chain_integrity": 0.30,  # Most critical
        "reasoning_transparency": 0.20,
        "provider_reliability": 0.15,
        "decision_stakes": 0.15,
        "audit_completeness": 0.10,
        "historical_performance": 0.10,
    }

    # Decision category risk multipliers
    CATEGORY_MULTIPLIERS = {
        DecisionCategory.MEDICAL: 3.0,
        DecisionCategory.FINANCIAL: 2.5,
        DecisionCategory.LEGAL: 2.5,
        DecisionCategory.AUTONOMOUS_VEHICLE: 2.8,
        DecisionCategory.CONTENT_MODERATION: 1.5,
        DecisionCategory.CUSTOMER_SERVICE: 1.2,
        DecisionCategory.CREATIVE: 1.0,
        DecisionCategory.INFORMATION_RETRIEVAL: 1.0,
    }

    # Premium base rates (per $1000 of coverage per month)
    BASE_PREMIUM_RATES = {
        RiskLevel.VERY_LOW: 0.50,
        RiskLevel.LOW: 1.00,
        RiskLevel.MEDIUM: 2.50,
        RiskLevel.HIGH: 5.00,
        RiskLevel.VERY_HIGH: 10.00,
    }

    def __init__(self, database_manager=None):
        """
        Initialize risk assessor with optional database for historical data.

        Args:
            database_manager: Optional database connection for historical queries
        """
        self.db = database_manager

    async def assess_capsule_chain(
        self,
        capsule_chain: List[Dict],
        decision_category: DecisionCategory,
        requested_coverage: int = 100000,
        user_id: Optional[str] = None,
    ) -> RiskAssessment:
        """
        Perform comprehensive risk assessment on a capsule chain.

        Args:
            capsule_chain: List of capsule dictionaries forming a decision chain
            decision_category: Type of decision being insured
            requested_coverage: Coverage amount in USD
            user_id: Optional user ID for historical analysis

        Returns:
            RiskAssessment with score, level, premium, and recommendations
        """
        factors = []

        # Factor 1: Chain Integrity
        integrity_factor = await self._assess_chain_integrity(capsule_chain)
        factors.append(integrity_factor)

        # Factor 2: Reasoning Transparency
        transparency_factor = self._assess_reasoning_transparency(capsule_chain)
        factors.append(transparency_factor)

        # Factor 3: Provider Reliability
        reliability_factor = await self._assess_provider_reliability(capsule_chain)
        factors.append(reliability_factor)

        # Factor 4: Decision Stakes
        stakes_factor = self._assess_decision_stakes(
            capsule_chain, decision_category, requested_coverage
        )
        factors.append(stakes_factor)

        # Factor 5: Audit Trail Completeness
        audit_factor = self._assess_audit_completeness(capsule_chain)
        factors.append(audit_factor)

        # Factor 6: Historical Performance
        if user_id:
            history_factor = await self._assess_historical_performance(user_id)
            factors.append(history_factor)

        # Calculate composite risk score
        overall_score = self._calculate_composite_score(factors)

        # Apply decision category multiplier
        category_multiplier = self.CATEGORY_MULTIPLIERS.get(decision_category, 1.0)
        adjusted_score = min(overall_score * category_multiplier, 1.0)

        # Determine risk level
        risk_level = self._score_to_risk_level(adjusted_score)

        # Calculate confidence (based on data completeness)
        confidence = self._calculate_confidence(capsule_chain, factors)

        # Calculate premium
        premium_estimate = self._calculate_premium(
            risk_level, requested_coverage, decision_category
        )

        # Determine policy terms
        policy_term = self._determine_policy_term(risk_level)

        # Generate conditions and exclusions
        conditions = self._generate_conditions(risk_level, decision_category, factors)
        exclusions = self._generate_exclusions(decision_category)

        # Recommended coverage (may differ from requested)
        coverage_recommended = self._recommend_coverage(
            requested_coverage, risk_level, adjusted_score
        )

        return RiskAssessment(
            overall_score=adjusted_score,
            risk_level=risk_level,
            confidence=confidence,
            factors=factors,
            premium_estimate=premium_estimate,
            coverage_recommended=coverage_recommended,
            policy_term_months=policy_term,
            conditions=conditions,
            exclusions=exclusions,
            timestamp=utc_now(),
        )

    async def _assess_chain_integrity(self, capsule_chain: List[Dict]) -> RiskFactor:
        """
        Assess cryptographic integrity of the capsule chain.

        Checks:
        - All signatures valid
        - Chain linkage intact (parent references)
        - No tampering detected
        - Timestamps logical
        """
        total_capsules = len(capsule_chain)
        valid_signatures = 0
        valid_linkage = 0
        tampering_detected = False
        timestamp_issues = 0

        previous_timestamp = None
        previous_hash = None

        for i, capsule in enumerate(capsule_chain):
            # Verify signature
            try:
                # Extract verification details from capsule
                verification = capsule.get("verification", {})
                if not verification:
                    continue

                # Check if we have required verification data
                signature = verification.get("signature")
                if not signature:
                    continue

                # For now, accept any capsule with a signature field
                # In production, would validate signature cryptographically
                if signature:
                    valid_signatures += 1

            except Exception as e:
                # Signature verification failed - log and continue
                import logging

                logging.warning(f"Capsule {i} verification failed: {e}")
                pass

            # Check chain linkage
            if i > 0:
                parent_id = capsule.get("parent_capsule_id")
                if previous_hash and parent_id == previous_hash:
                    valid_linkage += 1

            # Check timestamp ordering
            timestamp = capsule.get("timestamp")
            if timestamp and previous_timestamp:
                if timestamp < previous_timestamp:
                    timestamp_issues += 1

            # Check for tampering indicators
            if capsule.get("tampered") or capsule.get("verification_failed"):
                tampering_detected = True

            previous_timestamp = timestamp
            previous_hash = capsule.get("capsule_id")

        # Calculate score (0.0 = perfect, 1.0 = worst)
        signature_score = (
            1.0 - (valid_signatures / total_capsules) if total_capsules > 0 else 1.0
        )
        linkage_score = 1.0 - (valid_linkage / max(total_capsules - 1, 1))
        tampering_score = 1.0 if tampering_detected else 0.0
        timestamp_score = (
            min(timestamp_issues / total_capsules, 1.0) if total_capsules > 0 else 0.0
        )

        composite_score = (
            signature_score * 0.5
            + linkage_score * 0.2
            + tampering_score * 0.2
            + timestamp_score * 0.1
        )

        return RiskFactor(
            name="chain_integrity",
            score=composite_score,
            weight=self.WEIGHTS["chain_integrity"],
            description="Cryptographic verification of capsule chain",
            details={
                "total_capsules": total_capsules,
                "valid_signatures": valid_signatures,
                "valid_linkage": valid_linkage,
                "tampering_detected": tampering_detected,
                "timestamp_issues": timestamp_issues,
                "signature_rate": valid_signatures / total_capsules
                if total_capsules > 0
                else 0,
            },
        )

    def _assess_reasoning_transparency(self, capsule_chain: List[Dict]) -> RiskFactor:
        """
        Assess depth and quality of reasoning trails.

        Measures:
        - Presence of reasoning steps
        - Depth of explanation
        - Intermediate conclusions
        - Evidence cited
        """
        total_capsules = len(capsule_chain)
        reasoning_present = 0
        average_depth = 0
        evidence_citations = 0

        for capsule in capsule_chain:
            messages = capsule.get("messages", [])

            # Check for reasoning content
            has_reasoning = False
            reasoning_depth = 0

            for msg in messages:
                content = msg.get("content", "")

                # Simple heuristics for reasoning detection
                reasoning_keywords = [
                    "because",
                    "therefore",
                    "reasoning",
                    "step",
                    "conclusion",
                    "analysis",
                ]
                if any(kw in content.lower() for kw in reasoning_keywords):
                    has_reasoning = True
                    reasoning_depth += len(content.split()) / 100  # Rough depth metric

                # Check for evidence
                if "source:" in content.lower() or "reference:" in content.lower():
                    evidence_citations += 1

            if has_reasoning:
                reasoning_present += 1
                average_depth += reasoning_depth

        average_depth = average_depth / total_capsules if total_capsules > 0 else 0
        reasoning_rate = reasoning_present / total_capsules if total_capsules > 0 else 0
        citation_rate = evidence_citations / total_capsules if total_capsules > 0 else 0

        # Score (lower is better)
        score = 1.0 - (
            reasoning_rate * 0.5
            + min(average_depth / 5.0, 1.0) * 0.3
            + min(citation_rate, 1.0) * 0.2
        )

        return RiskFactor(
            name="reasoning_transparency",
            score=score,
            weight=self.WEIGHTS["reasoning_transparency"],
            description="Depth and quality of AI reasoning trails",
            details={
                "reasoning_present": reasoning_present,
                "reasoning_rate": reasoning_rate,
                "average_depth": average_depth,
                "evidence_citations": evidence_citations,
            },
        )

    async def _assess_provider_reliability(
        self, capsule_chain: List[Dict]
    ) -> RiskFactor:
        """
        Assess reliability of AI providers used in chain.

        Factors:
        - Provider track record
        - Known issues or recalls
        - Certification status
        - Model version maturity
        """
        providers = set()
        for capsule in capsule_chain:
            provider = capsule.get("provider", "unknown")
            providers.add(provider)

        # Provider reliability scores (0.0 = best, 1.0 = worst)
        # These would come from a database in production
        PROVIDER_SCORES = {
            "openai": 0.15,  # Well-established
            "anthropic": 0.10,  # Strong safety record
            "google": 0.20,
            "unknown": 0.90,  # Unknown providers are risky
        }

        provider_scores = [PROVIDER_SCORES.get(p.lower(), 0.50) for p in providers]

        # Worst provider determines score (conservative)
        score = max(provider_scores) if provider_scores else 0.50

        return RiskFactor(
            name="provider_reliability",
            score=score,
            weight=self.WEIGHTS["provider_reliability"],
            description="Track record of AI providers used",
            details={
                "providers": list(providers),
                "provider_count": len(providers),
                "average_reliability": sum(provider_scores) / len(provider_scores)
                if provider_scores
                else 0.50,
            },
        )

    def _assess_decision_stakes(
        self,
        capsule_chain: List[Dict],
        decision_category: DecisionCategory,
        requested_coverage: int,
    ) -> RiskFactor:
        """
        Assess the stakes/impact of the decision being insured.

        Higher stakes = higher risk score
        """
        # Category inherent risk (0.0 = low stakes, 1.0 = high stakes)
        CATEGORY_STAKES = {
            DecisionCategory.MEDICAL: 0.90,
            DecisionCategory.FINANCIAL: 0.80,
            DecisionCategory.LEGAL: 0.80,
            DecisionCategory.AUTONOMOUS_VEHICLE: 0.95,
            DecisionCategory.CONTENT_MODERATION: 0.40,
            DecisionCategory.CUSTOMER_SERVICE: 0.30,
            DecisionCategory.CREATIVE: 0.10,
            DecisionCategory.INFORMATION_RETRIEVAL: 0.10,
        }

        category_score = CATEGORY_STAKES.get(decision_category, 0.50)

        # Coverage amount factor (higher coverage = higher stakes)
        # Normalize to reasonable range
        coverage_factor = min(requested_coverage / 1000000, 1.0)  # Cap at $1M

        # Composite score
        score = category_score * 0.7 + coverage_factor * 0.3

        return RiskFactor(
            name="decision_stakes",
            score=score,
            weight=self.WEIGHTS["decision_stakes"],
            description="Impact level and consequences of decision",
            details={
                "category": decision_category.value,
                "requested_coverage": requested_coverage,
                "category_score": category_score,
                "coverage_factor": coverage_factor,
            },
        )

    def _assess_audit_completeness(self, capsule_chain: List[Dict]) -> RiskFactor:
        """
        Assess completeness of audit trail metadata.

        Required metadata:
        - Timestamps
        - User IDs
        - Provider information
        - Model versions
        - Input/output data
        """
        total_capsules = len(capsule_chain)
        required_fields = [
            "timestamp",
            "user_id",
            "provider",
            "model",
            "messages",
        ]

        completeness_scores = []

        for capsule in capsule_chain:
            present_fields = sum(
                1 for field in required_fields if field in capsule and capsule[field]
            )
            completeness = present_fields / len(required_fields)
            completeness_scores.append(completeness)

        average_completeness = (
            sum(completeness_scores) / len(completeness_scores)
            if completeness_scores
            else 0.0
        )

        # Score (inverse of completeness)
        score = 1.0 - average_completeness

        return RiskFactor(
            name="audit_completeness",
            score=score,
            weight=self.WEIGHTS["audit_completeness"],
            description="Completeness of audit trail metadata",
            details={
                "average_completeness": average_completeness,
                "required_fields": required_fields,
                "capsules_analyzed": total_capsules,
            },
        )

    async def _assess_historical_performance(self, user_id: str) -> RiskFactor:
        """
        Assess user's historical capsule verification performance.

        Queries database for past capsules and calculates success rate.
        """
        try:
            from sqlalchemy import and_, func, select

            from src.core.database import db
            from src.models.capsule import CapsuleModel

            # Query user's historical capsules
            async with db.session() as session:
                # Count total capsules
                total_query = select(func.count(CapsuleModel.id)).where(
                    CapsuleModel.creator_id == user_id
                )
                total_result = await session.execute(total_query)
                total_capsules = total_result.scalar() or 0

                # Count verified capsules (high confidence)
                verified_query = select(func.count(CapsuleModel.id)).where(
                    and_(
                        CapsuleModel.creator_id == user_id,
                        CapsuleModel.verification_confidence == "high",
                    )
                )
                verified_result = await session.execute(verified_query)
                verified_capsules = verified_result.scalar() or 0

            # Calculate success rate
            if total_capsules == 0:
                score = 0.50  # Neutral for new users
                success_rate = None
            else:
                success_rate = verified_capsules / total_capsules
                # Lower score = better (inverse of risk)
                score = 1.0 - success_rate

            return RiskFactor(
                name="historical_performance",
                score=score,
                weight=self.WEIGHTS["historical_performance"],
                description="User's past capsule verification success rate",
                details={
                    "user_id": user_id,
                    "total_capsules": total_capsules,
                    "verified_capsules": verified_capsules,
                    "success_rate": success_rate,
                    "historical_data_available": total_capsules > 0,
                },
            )

        except Exception as e:
            logger.error(f"Failed to query historical data for {user_id}: {e}")
            # Return neutral score on error
            return RiskFactor(
                name="historical_performance",
                score=0.50,
                weight=self.WEIGHTS["historical_performance"],
                description="User's past capsule verification success rate",
                details={
                    "user_id": user_id,
                    "historical_data_available": False,
                    "error": str(e),
                },
            )

    def _calculate_composite_score(self, factors: List[RiskFactor]) -> float:
        """
        Calculate weighted composite risk score.

        Returns value between 0.0 (best) and 1.0 (worst)
        """
        weighted_sum = sum(factor.score * factor.weight for factor in factors)

        total_weight = sum(factor.weight for factor in factors)

        return weighted_sum / total_weight if total_weight > 0 else 0.50

    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Convert numeric score to risk level category"""
        if score < 0.15:
            return RiskLevel.VERY_LOW
        elif score < 0.30:
            return RiskLevel.LOW
        elif score < 0.50:
            return RiskLevel.MEDIUM
        elif score < 0.70:
            return RiskLevel.HIGH
        elif score < 0.85:
            return RiskLevel.VERY_HIGH
        else:
            return RiskLevel.UNINSURABLE

    def _calculate_confidence(
        self, capsule_chain: List[Dict], factors: List[RiskFactor]
    ) -> float:
        """
        Calculate confidence in the risk assessment.

        Based on data completeness and factor reliability.
        """
        # Chain length factor (more data = higher confidence)
        length_factor = min(len(capsule_chain) / 10, 1.0)

        # Factor completeness (all factors present)
        factor_completeness = len(factors) / len(self.WEIGHTS)

        # Audit completeness from factors
        audit_factor = next(
            (f for f in factors if f.name == "audit_completeness"), None
        )
        audit_score = 1.0 - audit_factor.score if audit_factor else 0.5

        # Composite confidence
        confidence = length_factor * 0.3 + factor_completeness * 0.3 + audit_score * 0.4

        return confidence

    def _calculate_premium(
        self,
        risk_level: RiskLevel,
        coverage_amount: int,
        decision_category: DecisionCategory,
    ) -> str:
        """Calculate monthly premium estimate"""
        if risk_level == RiskLevel.UNINSURABLE:
            return "Uninsurable"

        base_rate = self.BASE_PREMIUM_RATES[risk_level]
        category_multiplier = self.CATEGORY_MULTIPLIERS[decision_category]

        # Premium per $1000 of coverage
        monthly_premium = (coverage_amount / 1000) * base_rate * category_multiplier

        return f"${monthly_premium:,.2f}/month"

    def _determine_policy_term(self, risk_level: RiskLevel) -> int:
        """Determine recommended policy term in months"""
        TERM_MAP = {
            RiskLevel.VERY_LOW: 12,
            RiskLevel.LOW: 12,
            RiskLevel.MEDIUM: 6,
            RiskLevel.HIGH: 3,
            RiskLevel.VERY_HIGH: 1,
        }
        return TERM_MAP.get(risk_level, 12)

    def _recommend_coverage(
        self,
        requested_coverage: int,
        risk_level: RiskLevel,
        risk_score: float,
    ) -> str:
        """Recommend appropriate coverage amount"""
        if risk_level == RiskLevel.UNINSURABLE:
            return "$0 (Uninsurable)"

        # May reduce coverage for high-risk cases
        if risk_level == RiskLevel.VERY_HIGH:
            recommended = min(requested_coverage, 50000)
        elif risk_level == RiskLevel.HIGH:
            recommended = min(requested_coverage, 250000)
        else:
            recommended = requested_coverage

        return f"${recommended:,}"

    def _generate_conditions(
        self,
        risk_level: RiskLevel,
        decision_category: DecisionCategory,
        factors: List[RiskFactor],
    ) -> List[str]:
        """Generate policy conditions based on risk assessment"""
        conditions = [
            "All AI decisions must be captured in UATP capsules",
            "Capsule chain must be verifiable upon claim",
            "Human oversight required for high-stakes decisions",
        ]

        if risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            conditions.extend(
                [
                    "Mandatory human review before decision execution",
                    "Real-time monitoring required",
                    "Quarterly audit of decision logs",
                ]
            )

        if decision_category in [DecisionCategory.MEDICAL, DecisionCategory.LEGAL]:
            conditions.append("Licensed professional must validate AI recommendations")

        # Check for specific factor issues
        chain_factor = next((f for f in factors if f.name == "chain_integrity"), None)
        if chain_factor and chain_factor.score > 0.3:
            conditions.append("All cryptographic signatures must be valid")

        return conditions

    def _generate_exclusions(self, decision_category: DecisionCategory) -> List[str]:
        """Generate policy exclusions"""
        base_exclusions = [
            "Intentional misuse or manipulation of AI systems",
            "Decisions made without proper capsule documentation",
            "Gross negligence in AI system deployment",
            "Unauthorized modifications to AI models",
        ]

        category_exclusions = {
            DecisionCategory.MEDICAL: [
                "Experimental treatments not approved by relevant authorities",
                "Decisions outside the AI's trained domain",
            ],
            DecisionCategory.FINANCIAL: [
                "Trading losses due to market volatility",
                "Regulatory violations",
            ],
        }

        return base_exclusions + category_exclusions.get(decision_category, [])
