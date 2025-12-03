"""
Dividend Bonds Service for UATP Capsule Engine

This service manages IP yield instruments and intellectual property bonds,
providing comprehensive financial instruments for AI model intellectual property.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from decimal import Decimal

from src.capsule_schema import (
    DividendBondCapsule,
    DividendBondPayload,
    CapsuleStatus,
    Verification,
)

logger = logging.getLogger(__name__)


@dataclass
class BondRegistry:
    """Registry for tracking active bonds and their performance."""

    active_bonds: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    matured_bonds: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    defaulted_bonds: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    dividend_payments: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    performance_history: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)


@dataclass
class IPAsset:
    """Represents an IP asset that can back dividend bonds."""

    asset_id: str
    asset_type: str  # model, dataset, algorithm, research, creative_work
    owner_agent_id: str
    market_value: float
    revenue_streams: List[str]
    performance_metrics: Dict[str, float]
    risk_factors: List[str]
    legal_status: str
    creation_date: datetime
    last_valuation: datetime


@dataclass
class DividendPayment:
    """Represents a dividend payment to bondholders."""

    payment_id: str
    bond_id: str
    payment_date: datetime
    amount: float
    currency: str
    payment_source: str
    recipient_agent_id: str
    status: str
    transaction_hash: Optional[str] = None


class DividendBondsService:
    """Service for managing IP-backed dividend bonds and yield instruments."""

    def __init__(self):
        self.bond_registry = BondRegistry()
        self.ip_assets: Dict[str, IPAsset] = {}
        self.bond_types: Dict[str, Dict[str, Any]] = self._init_bond_types()
        self.risk_models: Dict[str, Dict[str, Any]] = self._init_risk_models()
        self.market_data: Dict[str, float] = self._init_market_data()

    def _init_bond_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize bond type definitions."""
        return {
            "revenue": {
                "description": "Bonds backed by revenue from IP asset usage",
                "payment_frequency": "quarterly",
                "yield_calculation": "revenue_percentage",
                "default_coupon_rate": 0.08,
                "risk_category": "medium",
                "minimum_investment": 1000.0,
            },
            "royalty": {
                "description": "Bonds paying royalties from IP licensing",
                "payment_frequency": "monthly",
                "yield_calculation": "royalty_percentage",
                "default_coupon_rate": 0.12,
                "risk_category": "high",
                "minimum_investment": 5000.0,
            },
            "usage": {
                "description": "Bonds tied to usage metrics of IP assets",
                "payment_frequency": "monthly",
                "yield_calculation": "usage_based",
                "default_coupon_rate": 0.06,
                "risk_category": "low",
                "minimum_investment": 500.0,
            },
            "performance": {
                "description": "Bonds tied to performance metrics of AI models",
                "payment_frequency": "quarterly",
                "yield_calculation": "performance_based",
                "default_coupon_rate": 0.10,
                "risk_category": "high",
                "minimum_investment": 2000.0,
            },
        }

    def _init_risk_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize risk assessment models."""
        return {
            "ai_models": {
                "base_risk": 0.15,
                "factors": {
                    "model_age_months": {"weight": 0.1, "threshold": 12},
                    "usage_volatility": {"weight": 0.2, "threshold": 0.3},
                    "market_adoption": {"weight": 0.15, "threshold": 0.7},
                    "regulatory_risk": {"weight": 0.25, "threshold": 0.2},
                    "technical_obsolescence": {"weight": 0.3, "threshold": 0.4},
                },
            },
            "datasets": {
                "base_risk": 0.12,
                "factors": {
                    "data_quality": {"weight": 0.3, "threshold": 0.8},
                    "privacy_compliance": {"weight": 0.25, "threshold": 0.9},
                    "licensing_clarity": {"weight": 0.2, "threshold": 0.8},
                    "demand_stability": {"weight": 0.25, "threshold": 0.7},
                },
            },
            "algorithms": {
                "base_risk": 0.18,
                "factors": {
                    "innovation_level": {"weight": 0.2, "threshold": 0.8},
                    "patent_protection": {"weight": 0.3, "threshold": 0.9},
                    "competition_risk": {"weight": 0.25, "threshold": 0.3},
                    "implementation_complexity": {"weight": 0.25, "threshold": 0.6},
                },
            },
        }

    def _init_market_data(self) -> Dict[str, float]:
        """Initialize market data for yield calculations."""
        return {
            "risk_free_rate": 0.03,
            "ai_market_premium": 0.08,
            "ip_liquidity_discount": 0.02,
            "technology_risk_premium": 0.05,
            "default_inflation_rate": 0.025,
        }

    def register_ip_asset(
        self,
        asset_id: str,
        asset_type: str,
        owner_agent_id: str,
        market_value: float,
        revenue_streams: List[str],
        performance_metrics: Dict[str, float],
    ) -> IPAsset:
        """Register an IP asset for potential bond backing."""

        if asset_id in self.ip_assets:
            raise ValueError(f"IP asset {asset_id} already registered")

        # Assess risk factors based on asset type
        risk_factors = self._assess_asset_risks(asset_type, performance_metrics)

        asset = IPAsset(
            asset_id=asset_id,
            asset_type=asset_type,
            owner_agent_id=owner_agent_id,
            market_value=market_value,
            revenue_streams=revenue_streams,
            performance_metrics=performance_metrics,
            risk_factors=risk_factors,
            legal_status="registered",
            creation_date=datetime.now(timezone.utc),
            last_valuation=datetime.now(timezone.utc),
        )

        self.ip_assets[asset_id] = asset

        logger.info(
            f"Registered IP asset {asset_id} of type {asset_type} valued at {market_value}"
        )
        return asset

    def create_dividend_bond_capsule(
        self,
        ip_asset_id: str,
        bond_type: str,
        issuer_agent_id: str,
        face_value: float,
        maturity_days: int,
        coupon_rate: Optional[float] = None,
        minimum_investment: Optional[float] = None,
    ) -> DividendBondCapsule:
        """Create a dividend bond backed by an IP asset."""

        # Validate IP asset exists and issuer owns it
        if ip_asset_id not in self.ip_assets:
            raise ValueError(f"IP asset {ip_asset_id} not found")

        ip_asset = self.ip_assets[ip_asset_id]
        if ip_asset.owner_agent_id != issuer_agent_id:
            raise ValueError(
                f"Agent {issuer_agent_id} does not own IP asset {ip_asset_id}"
            )

        # Validate bond type
        if bond_type not in self.bond_types:
            raise ValueError(f"Unknown bond type: {bond_type}")

        bond_config = self.bond_types[bond_type]

        # Use defaults if not provided
        if coupon_rate is None:
            coupon_rate = bond_config["default_coupon_rate"]
        if minimum_investment is None:
            minimum_investment = bond_config["minimum_investment"]

        # Calculate risk rating and current yield
        risk_rating = self._calculate_risk_rating(ip_asset)
        current_yield = self._calculate_current_yield(ip_asset, bond_type, coupon_rate)

        # Calculate maturity date
        maturity_date = datetime.now(timezone.utc) + timedelta(days=maturity_days)

        # Create bond payload
        bond_id = f"bond_{uuid.uuid4().hex[:16]}"

        payload = DividendBondPayload(
            bond_id=bond_id,
            ip_asset_id=ip_asset_id,
            bond_type=bond_type,
            issuer_agent_id=issuer_agent_id,
            face_value=face_value,
            coupon_rate=coupon_rate,
            maturity_date=maturity_date,
            payment_frequency=bond_config["payment_frequency"],
            yield_calculation_method=bond_config["yield_calculation"],
            risk_rating=risk_rating,
            minimum_investment=minimum_investment,
            asset_backing_details={
                "asset_type": ip_asset.asset_type,
                "market_value": ip_asset.market_value,
                "revenue_streams": ip_asset.revenue_streams,
                "risk_factors": ip_asset.risk_factors,
            },
            current_yield=current_yield,
            total_payments_made=0.0,
            outstanding_principal=face_value,
            default_probability=self._calculate_default_probability(ip_asset),
            regulatory_compliance=self._check_regulatory_compliance(ip_asset),
            liquidity_terms=self._generate_liquidity_terms(bond_type, face_value),
        )

        # Create capsule
        capsule_id = f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}"

        capsule = DividendBondCapsule(
            capsule_id=capsule_id,
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(
                signature=f"ed25519:{'0'*128}", merkle_root=f"sha256:{'0'*64}"
            ),
            dividend_bond=payload,
        )

        # Register bond
        self._register_bond(capsule)

        logger.info(
            f"Created {bond_type} dividend bond {bond_id} for IP asset {ip_asset_id}"
        )
        return capsule

    def process_dividend_payment(
        self,
        bond_id: str,
        payment_amount: float,
        payment_source: str,
        recipient_agent_id: str,
    ) -> DividendPayment:
        """Process a dividend payment to bondholders."""

        if bond_id not in self.bond_registry.active_bonds:
            raise ValueError(f"Bond {bond_id} not found or not active")

        bond_info = self.bond_registry.active_bonds[bond_id]

        # Validate payment amount
        if payment_amount <= 0:
            raise ValueError("Payment amount must be positive")

        # Create payment record
        payment_id = f"payment_{uuid.uuid4().hex[:16]}"

        payment = DividendPayment(
            payment_id=payment_id,
            bond_id=bond_id,
            payment_date=datetime.now(timezone.utc),
            amount=payment_amount,
            currency="USD",  # Default currency
            payment_source=payment_source,
            recipient_agent_id=recipient_agent_id,
            status="completed",
            transaction_hash=f"tx_{uuid.uuid4().hex[:32]}",
        )

        # Record payment
        if bond_id not in self.bond_registry.dividend_payments:
            self.bond_registry.dividend_payments[bond_id] = []

        self.bond_registry.dividend_payments[bond_id].append(
            {
                "payment_id": payment_id,
                "payment_date": payment.payment_date,
                "amount": payment_amount,
                "currency": payment.currency,
                "payment_source": payment_source,
                "recipient_agent_id": recipient_agent_id,
                "status": payment.status,
                "transaction_hash": payment.transaction_hash,
            }
        )

        # Update bond info
        bond_info["total_payments_made"] += payment_amount
        bond_info["last_payment_date"] = payment.payment_date
        bond_info["payment_count"] = bond_info.get("payment_count", 0) + 1

        # Update current yield based on payment history
        self._update_bond_yield(bond_id)

        logger.info(
            f"Processed dividend payment of {payment_amount} for bond {bond_id}"
        )
        return payment

    def get_bond_performance(self, bond_id: str) -> Dict[str, Any]:
        """Get performance metrics for a bond."""

        if bond_id not in self.bond_registry.active_bonds:
            raise ValueError(f"Bond {bond_id} not found")

        bond_info = self.bond_registry.active_bonds[bond_id]
        payments = self.bond_registry.dividend_payments.get(bond_id, [])

        # Calculate performance metrics
        total_dividends = sum(p["amount"] for p in payments)
        payment_count = len(payments)
        average_payment = total_dividends / payment_count if payment_count > 0 else 0.0

        # Calculate yields
        face_value = bond_info["face_value"]
        current_yield = total_dividends / face_value if face_value > 0 else 0.0

        # Annualize yield based on bond age
        bond_age_days = (datetime.now(timezone.utc) - bond_info["issue_date"]).days
        if bond_age_days > 0:
            annualized_yield = current_yield * (365.25 / bond_age_days)
        else:
            annualized_yield = 0.0

        # Calculate days to maturity
        days_to_maturity = (
            bond_info["maturity_date"] - datetime.now(timezone.utc)
        ).days

        return {
            "bond_id": bond_id,
            "total_dividends_paid": total_dividends,
            "payment_count": payment_count,
            "average_payment": average_payment,
            "current_yield": current_yield,
            "annualized_yield": annualized_yield,
            "risk_rating": bond_info["risk_rating"],
            "status": bond_info["status"],
            "days_to_maturity": max(0, days_to_maturity),
            "face_value": face_value,
            "outstanding_principal": bond_info.get("outstanding_principal", face_value),
        }

    def get_active_bonds(
        self, issuer_agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all active bonds, optionally filtered by issuer."""

        bonds = []
        for bond_id, bond_info in self.bond_registry.active_bonds.items():
            if issuer_agent_id and bond_info["issuer_agent_id"] != issuer_agent_id:
                continue

            bonds.append(
                {
                    "bond_id": bond_id,
                    "ip_asset_id": bond_info["ip_asset_id"],
                    "bond_type": bond_info["bond_type"],
                    "issuer_agent_id": bond_info["issuer_agent_id"],
                    "face_value": bond_info["face_value"],
                    "coupon_rate": bond_info["coupon_rate"],
                    "maturity_date": bond_info["maturity_date"],
                    "risk_rating": bond_info["risk_rating"],
                    "current_yield": bond_info.get("current_yield", 0.0),
                    "status": bond_info["status"],
                    "issue_date": bond_info["issue_date"],
                    "payment_count": bond_info.get("payment_count", 0),
                }
            )

        return sorted(bonds, key=lambda b: b["issue_date"], reverse=True)

    def _assess_asset_risks(
        self, asset_type: str, performance_metrics: Dict[str, float]
    ) -> List[str]:
        """Assess risk factors for an IP asset."""

        risks = []

        if asset_type in self.risk_models:
            risk_model = self.risk_models[asset_type]

            for factor, config in risk_model["factors"].items():
                if factor in performance_metrics:
                    metric_value = performance_metrics[factor]
                    threshold = config["threshold"]

                    # Risk logic depends on the factor
                    if factor in [
                        "usage_volatility",
                        "regulatory_risk",
                        "technical_obsolescence",
                        "competition_risk",
                    ]:
                        # Higher values = higher risk
                        if metric_value > threshold:
                            risks.append(factor)
                    else:
                        # Lower values = higher risk
                        if metric_value < threshold:
                            risks.append(factor)

        # Add general risks
        if not risks:
            risks.append("standard_market_risk")

        return risks

    def _calculate_risk_rating(self, ip_asset: IPAsset) -> str:
        """Calculate risk rating for an IP asset."""

        asset_type = ip_asset.asset_type
        if asset_type not in self.risk_models:
            return "medium"

        risk_model = self.risk_models[asset_type]
        base_risk = risk_model["base_risk"]

        # Calculate risk score based on factors
        risk_score = base_risk
        for factor, config in risk_model["factors"].items():
            if factor in ip_asset.performance_metrics:
                metric_value = ip_asset.performance_metrics[factor]
                weight = config["weight"]
                threshold = config["threshold"]

                # Adjust risk based on factor
                if factor in [
                    "usage_volatility",
                    "regulatory_risk",
                    "technical_obsolescence",
                    "competition_risk",
                ]:
                    if metric_value > threshold:
                        risk_score += weight * (metric_value - threshold)
                else:
                    if metric_value < threshold:
                        risk_score += weight * (threshold - metric_value)

        # Convert to rating
        if risk_score < 0.1:
            return "AAA"
        elif risk_score < 0.15:
            return "AA"
        elif risk_score < 0.2:
            return "A"
        elif risk_score < 0.25:
            return "BBB"
        elif risk_score < 0.3:
            return "BB"
        elif risk_score < 0.4:
            return "B"
        else:
            return "C"

    def _calculate_current_yield(
        self, ip_asset: IPAsset, bond_type: str, coupon_rate: float
    ) -> float:
        """Calculate current yield for a bond."""

        # Base yield from coupon rate
        base_yield = coupon_rate

        # Adjust based on asset performance
        performance_adjustment = 0.0
        if "revenue_growth" in ip_asset.performance_metrics:
            growth = ip_asset.performance_metrics["revenue_growth"]
            performance_adjustment += growth * 0.5  # 50% of growth rate

        # Adjust based on market conditions
        market_adjustment = self.market_data.get("ai_market_premium", 0.0)

        # Risk adjustment
        risk_factors_count = len(ip_asset.risk_factors)
        risk_adjustment = risk_factors_count * 0.01  # 1% per risk factor

        current_yield = (
            base_yield + performance_adjustment + market_adjustment + risk_adjustment
        )

        return max(0.0, min(1.0, current_yield))  # Cap between 0% and 100%

    def _calculate_default_probability(self, ip_asset: IPAsset) -> float:
        """Calculate default probability for a bond."""

        base_default_rate = 0.05  # 5% base default rate

        # Adjust based on asset age
        asset_age_months = (
            datetime.now(timezone.utc) - ip_asset.creation_date
        ).days / 30.44
        age_adjustment = min(0.02, asset_age_months * 0.001)  # Slight increase with age

        # Adjust based on risk factors
        risk_adjustment = len(ip_asset.risk_factors) * 0.01

        # Adjust based on market value stability
        value_stability = ip_asset.performance_metrics.get("value_stability", 0.8)
        stability_adjustment = (1.0 - value_stability) * 0.05

        default_probability = (
            base_default_rate + age_adjustment + risk_adjustment + stability_adjustment
        )

        return min(0.5, max(0.001, default_probability))  # Cap between 0.1% and 50%

    def _check_regulatory_compliance(self, ip_asset: IPAsset) -> List[str]:
        """Check regulatory compliance for an IP asset."""

        compliance_items = ["securities_regulations", "ip_laws", "data_protection"]

        # Add asset-specific compliance requirements
        if ip_asset.asset_type == "ai_models":
            compliance_items.extend(["ai_ethics", "algorithmic_transparency"])
        elif ip_asset.asset_type == "datasets":
            compliance_items.extend(["privacy_laws", "data_licensing"])

        return compliance_items

    def _generate_liquidity_terms(
        self, bond_type: str, face_value: float
    ) -> Dict[str, Any]:
        """Generate liquidity terms for a bond."""

        base_liquidity = self.bond_types[bond_type].get("minimum_investment", 1000)

        return {
            "tradeable": True,
            "minimum_trade_amount": min(base_liquidity, face_value * 0.1),
            "settlement_period_days": 3,
            "early_redemption_allowed": bond_type in ["usage", "revenue"],
            "early_redemption_penalty": 0.02
            if bond_type in ["royalty", "performance"]
            else 0.0,
        }

    def _register_bond(self, capsule: DividendBondCapsule):
        """Register a bond in the active bonds registry."""

        bond = capsule.dividend_bond

        bond_record = {
            "bond_id": bond.bond_id,
            "capsule_id": capsule.capsule_id,
            "ip_asset_id": bond.ip_asset_id,
            "bond_type": bond.bond_type,
            "issuer_agent_id": bond.issuer_agent_id,
            "face_value": bond.face_value,
            "coupon_rate": bond.coupon_rate,
            "maturity_date": bond.maturity_date,
            "risk_rating": bond.risk_rating,
            "current_yield": bond.current_yield,
            "status": "active",
            "issue_date": capsule.timestamp,
            "total_payments_made": 0.0,
            "payment_count": 0,
            "outstanding_principal": bond.face_value,
        }

        self.bond_registry.active_bonds[bond.bond_id] = bond_record

    def _update_bond_yield(self, bond_id: str):
        """Update bond yield based on payment history."""

        if bond_id not in self.bond_registry.active_bonds:
            return

        bond_info = self.bond_registry.active_bonds[bond_id]
        payments = self.bond_registry.dividend_payments.get(bond_id, [])

        if not payments:
            return

        # Calculate yield based on payment history
        total_payments = sum(p["amount"] for p in payments)
        face_value = bond_info["face_value"]

        # Simple yield calculation
        if face_value > 0:
            payment_yield = total_payments / face_value

            # Annualize based on bond age
            bond_age_days = (datetime.now(timezone.utc) - bond_info["issue_date"]).days
            if bond_age_days > 0:
                annualized_yield = payment_yield * (365.25 / bond_age_days)
                bond_info["current_yield"] = min(1.0, annualized_yield)


# Global service instance
dividend_bonds_service = DividendBondsService()
