"""
Tests for Dividend Bonds Service
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from src.services.dividend_bonds_service import (
    DividendBondsService,
    IPAsset,
    DividendPayment,
    BondRegistry,
)
from src.capsule_schema import DividendBondCapsule


class TestDividendBondsService:
    """Test the Dividend Bonds Service functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = DividendBondsService()

    def test_init_bond_templates(self):
        """Test that bond templates are properly initialized."""
        templates = self.service.bond_templates

        # Check that all expected bond types exist
        expected_types = ["revenue", "royalty", "usage", "performance"]
        for bond_type in expected_types:
            assert bond_type in templates

        # Verify revenue bond template
        revenue = templates["revenue"]
        assert revenue["payment_frequency"] == "quarterly"
        assert revenue["yield_calculation_method"] == "revenue_percentage"
        assert revenue["default_coupon_rate"] == 0.05
        assert revenue["minimum_investment"] == 1000.0

        # Verify royalty bond template
        royalty = templates["royalty"]
        assert royalty["payment_frequency"] == "monthly"
        assert royalty["default_coupon_rate"] == 0.04
        assert "active_licenses" in royalty["collateral_requirements"]

    def test_init_market_data(self):
        """Test that market data is properly initialized."""
        market_data = self.service.market_data

        assert "risk_free_rate" in market_data
        assert "market_risk_premium" in market_data
        assert "currency_rates" in market_data
        assert "sector_multiples" in market_data

        # Check currency rates
        assert market_data["currency_rates"]["UATP"] == 1.0

        # Check sector multiples
        assert "ai_models" in market_data["sector_multiples"]
        assert market_data["sector_multiples"]["ai_models"] == 1.2

    def test_register_ip_asset_success(self):
        """Test successful IP asset registration."""
        asset_id = "test-model-123"
        asset_type = "ai_models"
        owner_agent_id = "agent-owner-456"
        market_value = 50000.0
        revenue_streams = ["inference_fees", "licensing"]
        performance_metrics = {"accuracy": 0.95, "usage_count": 1000}

        asset = self.service.register_ip_asset(
            asset_id=asset_id,
            asset_type=asset_type,
            owner_agent_id=owner_agent_id,
            market_value=market_value,
            revenue_streams=revenue_streams,
            performance_metrics=performance_metrics,
        )

        assert isinstance(asset, IPAsset)
        assert asset.asset_id == asset_id
        assert asset.asset_type == asset_type
        assert asset.owner_agent_id == owner_agent_id
        assert asset.market_value == market_value
        assert asset.revenue_streams == revenue_streams
        assert asset.performance_metrics == performance_metrics
        assert asset.legal_status == "verified"
        assert asset_id in self.service.ip_assets

    def test_register_ip_asset_duplicate_fails(self):
        """Test that registering duplicate IP asset fails."""
        asset_id = "test-model-123"

        # Register once
        self.service.register_ip_asset(
            asset_id=asset_id,
            asset_type="ai_models",
            owner_agent_id="agent-owner-456",
            market_value=50000.0,
            revenue_streams=["inference_fees"],
            performance_metrics={"accuracy": 0.95},
        )

        # Try to register again - should fail
        with pytest.raises(ValueError, match="already registered"):
            self.service.register_ip_asset(
                asset_id=asset_id,
                asset_type="ai_models",
                owner_agent_id="agent-owner-456",
                market_value=50000.0,
                revenue_streams=["inference_fees"],
                performance_metrics={"accuracy": 0.95},
            )

    def test_create_dividend_bond_capsule_success(self):
        """Test successful dividend bond capsule creation."""
        # First register IP asset
        asset_id = "test-model-123"
        owner_agent_id = "agent-owner-456"

        self.service.register_ip_asset(
            asset_id=asset_id,
            asset_type="ai_models",
            owner_agent_id=owner_agent_id,
            market_value=50000.0,
            revenue_streams=["inference_fees", "licensing"],
            performance_metrics={"accuracy": 0.95, "usage_count": 1000},
        )

        # Create bond
        capsule = self.service.create_dividend_bond_capsule(
            ip_asset_id=asset_id,
            bond_type="revenue",
            issuer_agent_id=owner_agent_id,
            face_value=10000.0,
            maturity_days=365,
            coupon_rate=0.06,
            minimum_investment=500.0,
        )

        assert isinstance(capsule, DividendBondCapsule)
        assert capsule.dividend_bond.ip_asset_id == asset_id
        assert capsule.dividend_bond.issuer_agent_id == owner_agent_id
        assert capsule.dividend_bond.face_value == 10000.0
        assert capsule.dividend_bond.bond_type == "revenue"
        assert capsule.dividend_bond.coupon_rate == 0.06
        assert capsule.dividend_bond.minimum_investment == 500.0

        # Check that bond was registered
        bonds = self.service.get_active_bonds()
        assert len(bonds) == 1
        assert bonds[0]["bond_type"] == "revenue"

    def test_create_dividend_bond_asset_not_found(self):
        """Test bond creation fails when IP asset not found."""
        with pytest.raises(ValueError, match="not found"):
            self.service.create_dividend_bond_capsule(
                ip_asset_id="non-existent-asset",
                bond_type="revenue",
                issuer_agent_id="agent-123",
                face_value=10000.0,
                maturity_days=365,
            )

    def test_create_dividend_bond_wrong_owner(self):
        """Test bond creation fails when issuer is not asset owner."""
        # Register asset with real owner
        asset_id = "test-model-123"
        real_owner = "agent-owner-456"
        fake_issuer = "agent-fake-789"

        self.service.register_ip_asset(
            asset_id=asset_id,
            asset_type="ai_models",
            owner_agent_id=real_owner,
            market_value=50000.0,
            revenue_streams=["inference_fees"],
            performance_metrics={"accuracy": 0.95},
        )

        # Try to create bond with fake issuer
        with pytest.raises(ValueError, match="does not own"):
            self.service.create_dividend_bond_capsule(
                ip_asset_id=asset_id,
                bond_type="revenue",
                issuer_agent_id=fake_issuer,
                face_value=10000.0,
                maturity_days=365,
            )

    def test_create_dividend_bond_unknown_type(self):
        """Test bond creation fails with unknown bond type."""
        # Register asset
        asset_id = "test-model-123"
        owner_agent_id = "agent-owner-456"

        self.service.register_ip_asset(
            asset_id=asset_id,
            asset_type="ai_models",
            owner_agent_id=owner_agent_id,
            market_value=50000.0,
            revenue_streams=["inference_fees"],
            performance_metrics={"accuracy": 0.95},
        )

        # Try to create bond with unknown type
        with pytest.raises(ValueError, match="Unknown bond type"):
            self.service.create_dividend_bond_capsule(
                ip_asset_id=asset_id,
                bond_type="unknown_bond_type",
                issuer_agent_id=owner_agent_id,
                face_value=10000.0,
                maturity_days=365,
            )

    def test_calculate_dividend_payment_revenue_percentage(self):
        """Test dividend payment calculation with revenue percentage method."""
        # Create bond with revenue percentage method
        bond_id = self._create_test_bond("revenue")

        # Calculate dividend payment
        payment_amount = self.service.calculate_dividend_payment(
            bond_id=bond_id, period_revenue=5000.0, period_metrics={"usage_count": 500}
        )

        # Should be base amount (face_value * coupon_rate) + revenue bonus (10% of revenue)
        # Base: 10000 * 0.05 = 500, Revenue bonus: 5000 * 0.1 = 500, Total: 1000
        assert payment_amount > 900  # Account for risk adjustment
        assert payment_amount < 1100

    def test_calculate_dividend_payment_royalty_percentage(self):
        """Test dividend payment calculation with royalty percentage method."""
        bond_id = self._create_test_bond("royalty")

        payment_amount = self.service.calculate_dividend_payment(
            bond_id=bond_id,
            period_revenue=2000.0,
            period_metrics={"licensing_count": 10},
        )

        # Should be period_revenue * coupon_rate = 2000 * 0.04 = 80
        assert payment_amount > 70  # Account for risk adjustment
        assert payment_amount < 90

    def test_calculate_dividend_payment_usage_volume(self):
        """Test dividend payment calculation with usage volume method."""
        bond_id = self._create_test_bond("usage")

        payment_amount = self.service.calculate_dividend_payment(
            bond_id=bond_id,
            period_revenue=1000.0,
            period_metrics={"usage_count": 10000},
        )

        # Should be base amount + usage bonus: 600 + (10000 * 0.001) = 610
        assert payment_amount > 550  # Account for risk adjustment
        assert payment_amount < 650

    def test_calculate_dividend_payment_performance_metrics(self):
        """Test dividend payment calculation with performance metrics method."""
        bond_id = self._create_test_bond("performance")

        payment_amount = self.service.calculate_dividend_payment(
            bond_id=bond_id,
            period_revenue=3000.0,
            period_metrics={"accuracy": 0.9, "efficiency": 0.8},
        )

        # Should be base amount * performance_multiplier
        # Base: 10000 * 0.08 = 800, Performance avg: 0.85, Multiplier: 0.85
        # Total: 800 * 0.85 = 680
        assert payment_amount > 600
        assert payment_amount < 750

    def test_calculate_dividend_payment_bond_not_found(self):
        """Test dividend calculation fails for non-existent bond."""
        with pytest.raises(ValueError, match="not found"):
            self.service.calculate_dividend_payment(
                bond_id="non-existent-bond", period_revenue=1000.0, period_metrics={}
            )

    def test_process_dividend_payment(self):
        """Test processing a dividend payment."""
        bond_id = self._create_test_bond("revenue")

        payment = self.service.process_dividend_payment(
            bond_id=bond_id,
            payment_amount=500.0,
            payment_source="inference_fees",
            recipient_agent_id="agent-investor-789",
        )

        assert isinstance(payment, DividendPayment)
        assert payment.bond_id == bond_id
        assert payment.amount == 500.0
        assert payment.payment_source == "inference_fees"
        assert payment.recipient_agent_id == "agent-investor-789"
        assert payment.status == "completed"

        # Check that payment was recorded
        performance = self.service.get_bond_performance(bond_id)
        assert performance["total_dividends_paid"] == 500.0
        assert performance["payment_count"] == 1

    def test_get_bond_performance(self):
        """Test getting bond performance metrics."""
        bond_id = self._create_test_bond("revenue")

        # Process some payments
        self.service.process_dividend_payment(
            bond_id=bond_id,
            payment_amount=400.0,
            payment_source="licensing",
            recipient_agent_id="agent-investor-789",
        )

        self.service.process_dividend_payment(
            bond_id=bond_id,
            payment_amount=600.0,
            payment_source="inference_fees",
            recipient_agent_id="agent-investor-789",
        )

        performance = self.service.get_bond_performance(bond_id)

        assert performance["bond_id"] == bond_id
        assert performance["total_dividends_paid"] == 1000.0
        assert performance["payment_count"] == 2
        assert performance["average_payment"] == 500.0
        assert performance["current_yield"] == 0.1  # 1000 / 10000
        assert performance["annualized_yield"] == 0.4  # quarterly * 4

    def test_get_active_bonds(self):
        """Test getting active bonds."""
        # Create multiple bonds
        bond_id1 = self._create_test_bond("revenue")
        bond_id2 = self._create_test_bond("royalty")

        bonds = self.service.get_active_bonds()

        assert len(bonds) == 2
        bond_ids = [bond["bond_id"] for bond in bonds]
        assert bond_id1 in bond_ids
        assert bond_id2 in bond_ids

    def test_get_active_bonds_filtered_by_issuer(self):
        """Test getting active bonds filtered by issuer."""
        # Create bonds with different issuers
        asset_id1 = "asset-1"
        asset_id2 = "asset-2"
        issuer1 = "issuer-1"
        issuer2 = "issuer-2"

        # Register assets and create bonds
        self.service.register_ip_asset(
            asset_id=asset_id1,
            asset_type="ai_models",
            owner_agent_id=issuer1,
            market_value=50000.0,
            revenue_streams=["inference_fees"],
            performance_metrics={"accuracy": 0.95},
        )

        self.service.register_ip_asset(
            asset_id=asset_id2,
            asset_type="ai_models",
            owner_agent_id=issuer2,
            market_value=30000.0,
            revenue_streams=["licensing"],
            performance_metrics={"accuracy": 0.90},
        )

        self.service.create_dividend_bond_capsule(
            ip_asset_id=asset_id1,
            bond_type="revenue",
            issuer_agent_id=issuer1,
            face_value=10000.0,
            maturity_days=365,
        )

        self.service.create_dividend_bond_capsule(
            ip_asset_id=asset_id2,
            bond_type="royalty",
            issuer_agent_id=issuer2,
            face_value=5000.0,
            maturity_days=180,
        )

        # Get bonds for specific issuer
        issuer1_bonds = self.service.get_active_bonds(issuer1)
        assert len(issuer1_bonds) == 1
        assert issuer1_bonds[0]["issuer_agent_id"] == issuer1

    def test_mature_bond(self):
        """Test bond maturation."""
        bond_id = self._create_test_bond("revenue")

        # Mature the bond
        result = self.service.mature_bond(bond_id)
        assert result is True

        # Check bond moved to matured registry
        assert bond_id not in self.service.bond_registry.active_bonds
        assert bond_id in self.service.bond_registry.matured_bonds

        matured_bond = self.service.bond_registry.matured_bonds[bond_id]
        assert matured_bond["status"] == "matured"

    def test_mature_nonexistent_bond(self):
        """Test maturing non-existent bond."""
        result = self.service.mature_bond("non-existent-bond")
        assert result is False

    def test_assess_asset_risks_ai_models(self):
        """Test risk assessment for AI models."""
        performance_metrics = {
            "accuracy": 0.75,  # Below 0.8 threshold
            "usage_trend": -0.1,  # Negative trend
            "market_share": 0.05,  # Low market share
        }

        risks = self.service._assess_asset_risks("ai_models", performance_metrics)

        assert "low_performance" in risks
        assert "declining_usage" in risks
        assert "low_market_penetration" in risks

    def test_assess_asset_risks_datasets(self):
        """Test risk assessment for datasets."""
        performance_metrics = {
            "quality_score": 0.6,  # Below 0.7 threshold
            "age_months": 30,  # Over 24 months
            "market_share": 0.15,  # Good market share
        }

        risks = self.service._assess_asset_risks("datasets", performance_metrics)

        assert "data_quality_issues" in risks
        assert "dataset_staleness" in risks
        assert "low_market_penetration" not in risks

    def test_calculate_risk_rating(self):
        """Test risk rating calculation."""
        # High quality asset
        high_quality_asset = IPAsset(
            asset_id="high-quality",
            asset_type="ai_models",
            owner_agent_id="owner",
            market_value=100000.0,
            revenue_streams=["inference"],
            performance_metrics={"accuracy": 0.95, "efficiency": 0.90},
            risk_factors=[],
            legal_status="verified",
            creation_date=datetime.now(timezone.utc),
            last_valuation=datetime.now(timezone.utc),
        )

        rating = self.service._calculate_risk_rating(high_quality_asset)
        assert rating in ["AAA", "AA", "A"]

        # Low quality asset
        low_quality_asset = IPAsset(
            asset_id="low-quality",
            asset_type="ai_models",
            owner_agent_id="owner",
            market_value=1000.0,
            revenue_streams=["inference"],
            performance_metrics={"accuracy": 0.60, "efficiency": 0.50},
            risk_factors=["low_performance"],
            legal_status="verified",
            creation_date=datetime.now(timezone.utc),
            last_valuation=datetime.now(timezone.utc),
        )

        rating = self.service._calculate_risk_rating(low_quality_asset)
        assert rating in ["B", "CCC"]

    def test_calculate_current_yield(self):
        """Test current yield calculation."""
        asset = IPAsset(
            asset_id="test-asset",
            asset_type="ai_models",
            owner_agent_id="owner",
            market_value=50000.0,
            revenue_streams=["inference"],
            performance_metrics={"accuracy": 0.8, "efficiency": 0.7},  # Average: 0.75
            risk_factors=[],
            legal_status="verified",
            creation_date=datetime.now(timezone.utc),
            last_valuation=datetime.now(timezone.utc),
        )

        yield_rate = self.service._calculate_current_yield(asset, 0.05)

        # Should be 0.05 + (0.75 - 0.5) * 0.1 = 0.05 + 0.025 = 0.075
        assert abs(yield_rate - 0.075) < 0.001

    def test_calculate_risk_adjustment(self):
        """Test risk adjustment factor calculation."""
        # Test different risk ratings
        assert self.service._calculate_risk_adjustment("AAA") == 1.0
        assert self.service._calculate_risk_adjustment("AA") == 0.98
        assert self.service._calculate_risk_adjustment("A") == 0.95
        assert self.service._calculate_risk_adjustment("CCC") == 0.75
        assert self.service._calculate_risk_adjustment("unknown") == 0.8

    def test_get_annualization_factor(self):
        """Test annualization factor calculation."""
        assert self.service._get_annualization_factor("monthly") == 12.0
        assert self.service._get_annualization_factor("quarterly") == 4.0
        assert self.service._get_annualization_factor("annually") == 1.0
        assert self.service._get_annualization_factor("semi_annually") == 2.0
        assert self.service._get_annualization_factor("unknown") == 4.0

    def test_bond_with_custom_parameters(self):
        """Test creating bond with custom parameters."""
        # Register asset
        asset_id = "test-model-123"
        owner_agent_id = "agent-owner-456"

        self.service.register_ip_asset(
            asset_id=asset_id,
            asset_type="ai_models",
            owner_agent_id=owner_agent_id,
            market_value=50000.0,
            revenue_streams=["inference_fees"],
            performance_metrics={"accuracy": 0.95},
        )

        # Create bond with custom parameters
        capsule = self.service.create_dividend_bond_capsule(
            ip_asset_id=asset_id,
            bond_type="performance",
            issuer_agent_id=owner_agent_id,
            face_value=25000.0,
            maturity_days=730,  # 2 years
            coupon_rate=0.12,  # 12% custom rate
            minimum_investment=2500.0,
        )

        assert capsule.dividend_bond.face_value == 25000.0
        assert capsule.dividend_bond.coupon_rate == 0.12
        assert capsule.dividend_bond.minimum_investment == 2500.0

        # Check maturity date is approximately 2 years from now
        expected_maturity = datetime.now(timezone.utc) + timedelta(days=730)
        actual_maturity = capsule.dividend_bond.maturity_date
        time_diff = abs((actual_maturity - expected_maturity).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance

    def test_bond_registry_structure(self):
        """Test that bond registry maintains proper structure."""
        bond_id = self._create_test_bond("revenue")

        # Check active bonds registry
        assert bond_id in self.service.bond_registry.active_bonds
        bond_record = self.service.bond_registry.active_bonds[bond_id]

        required_fields = [
            "capsule_id",
            "bond_id",
            "ip_asset_id",
            "bond_type",
            "issuer_agent_id",
            "face_value",
            "coupon_rate",
            "maturity_date",
            "payment_frequency",
            "risk_rating",
            "status",
            "created_date",
        ]

        for field in required_fields:
            assert field in bond_record

    def _create_test_bond(self, bond_type: str = "revenue") -> str:
        """Helper method to create a test bond."""
        # Register IP asset
        asset_id = f"test-asset-{bond_type}"
        owner_agent_id = "agent-owner-456"

        self.service.register_ip_asset(
            asset_id=asset_id,
            asset_type="ai_models",
            owner_agent_id=owner_agent_id,
            market_value=50000.0,
            revenue_streams=["inference_fees"],
            performance_metrics={"accuracy": 0.95},
        )

        # Create bond
        capsule = self.service.create_dividend_bond_capsule(
            ip_asset_id=asset_id,
            bond_type=bond_type,
            issuer_agent_id=owner_agent_id,
            face_value=10000.0,
            maturity_days=365,
        )

        return capsule.dividend_bond.bond_id
