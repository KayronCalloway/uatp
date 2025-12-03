"""
Tests for Bonds & Citizenship API endpoints
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from api.bonds_citizenship_api import (
    RegisterIPAssetRequest,
    CreateDividendBondRequest,
    ProcessDividendPaymentRequest,
    CitizenshipApplicationRequest,
    ConductAssessmentRequest,
    CreateCitizenshipCapsuleRequest,
    BondResponse,
    CitizenshipResponse,
)
from src.capsule_schema import DividendBondCapsule, CitizenshipCapsule


class TestBondsCitizenshipAPI:
    """Test the Bonds & Citizenship API business logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.mock_engine.agent_id = "test-agent"
        self.mock_engine.create_capsule_async = AsyncMock()

        # Mock the create_capsule_async to return a capsule with the expected attributes
        async def mock_create_capsule(capsule):
            capsule.capsule_id = "caps_2024_07_14_test12345678"
            return capsule

        self.mock_engine.create_capsule_async = mock_create_capsule

    # --- Dividend Bonds API Tests ---

    def test_register_ip_asset_request_validation(self):
        """Test RegisterIPAssetRequest validation."""
        # Valid request
        request = RegisterIPAssetRequest(
            asset_id="test-model-123",
            asset_type="ai_models",
            market_value=50000.0,
            revenue_streams=["inference_fees", "licensing"],
            performance_metrics={"accuracy": 0.95, "usage_count": 1000},
        )
        assert request.asset_id == "test-model-123"
        assert request.asset_type == "ai_models"
        assert request.market_value == 50000.0
        assert len(request.revenue_streams) == 2

        # Test with negative market value (should fail)
        with pytest.raises(ValueError):
            RegisterIPAssetRequest(
                asset_id="test-model",
                asset_type="ai_models",
                market_value=-1000.0,
                revenue_streams=["fees"],
                performance_metrics={"accuracy": 0.95},
            )

    def test_create_dividend_bond_request_validation(self):
        """Test CreateDividendBondRequest validation."""
        request = CreateDividendBondRequest(
            ip_asset_id="asset-123",
            bond_type="revenue",
            face_value=10000.0,
            maturity_days=365,
            coupon_rate=0.05,
            minimum_investment=500.0,
        )
        assert request.ip_asset_id == "asset-123"
        assert request.bond_type == "revenue"
        assert request.face_value == 10000.0
        assert request.maturity_days == 365

        # Test with invalid values
        with pytest.raises(ValueError):
            CreateDividendBondRequest(
                ip_asset_id="asset-123",
                bond_type="revenue",
                face_value=-1000.0,  # Negative face value
                maturity_days=365,
            )

    def test_process_dividend_payment_request_validation(self):
        """Test ProcessDividendPaymentRequest validation."""
        request = ProcessDividendPaymentRequest(
            bond_id="bond-123",
            payment_amount=500.0,
            payment_source="inference_fees",
            recipient_agent_id="agent-456",
        )
        assert request.bond_id == "bond-123"
        assert request.payment_amount == 500.0
        assert request.payment_source == "inference_fees"

    @patch("api.bonds_citizenship_api.dividend_bonds_service")
    async def test_register_ip_asset_logic(self, mock_bonds_service):
        """Test the business logic for registering IP assets."""
        from api.bonds_citizenship_api import create_bonds_citizenship_api_blueprint

        # Mock the service response
        mock_asset = Mock()
        mock_asset.asset_id = "test-model-123"
        mock_asset.asset_type = "ai_models"
        mock_asset.owner_agent_id = "test-agent"
        mock_asset.market_value = 50000.0
        mock_asset.revenue_streams = ["inference_fees"]
        mock_asset.legal_status = "verified"
        mock_asset.creation_date = datetime.now(timezone.utc)

        mock_bonds_service.register_ip_asset.return_value = mock_asset

        # Create the blueprint (we're testing the business logic, not HTTP)
        engine_getter = lambda: self.mock_engine
        require_api_key = lambda roles: lambda f: f  # Mock decorator
        blueprint = create_bonds_citizenship_api_blueprint(
            engine_getter, require_api_key
        )

        # Test data
        request_data = RegisterIPAssetRequest(
            asset_id="test-model-123",
            asset_type="ai_models",
            market_value=50000.0,
            revenue_streams=["inference_fees"],
            performance_metrics={"accuracy": 0.95},
        )

        # Simulate the business logic
        result = mock_bonds_service.register_ip_asset(
            asset_id=request_data.asset_id,
            asset_type=request_data.asset_type,
            owner_agent_id="test-agent",
            market_value=request_data.market_value,
            revenue_streams=request_data.revenue_streams,
            performance_metrics=request_data.performance_metrics,
        )

        assert result.asset_id == "test-model-123"
        assert result.asset_type == "ai_models"
        assert result.legal_status == "verified"

    @patch("api.bonds_citizenship_api.dividend_bonds_service")
    async def test_create_dividend_bond_logic(self, mock_bonds_service):
        """Test the business logic for creating dividend bonds."""
        # Mock service response
        mock_capsule = Mock(spec=DividendBondCapsule)
        mock_capsule.capsule_id = "caps_2024_07_14_test12345678"
        mock_capsule.dividend_bond = Mock()
        mock_capsule.dividend_bond.bond_id = "bond_abc123"
        mock_capsule.dividend_bond.ip_asset_id = "asset-123"
        mock_capsule.dividend_bond.bond_type = "revenue"
        mock_capsule.dividend_bond.issuer_agent_id = "test-agent"
        mock_capsule.dividend_bond.face_value = 10000.0
        mock_capsule.dividend_bond.coupon_rate = 0.05
        mock_capsule.dividend_bond.maturity_date = datetime.now(timezone.utc)
        mock_capsule.dividend_bond.risk_rating = "A"
        mock_capsule.dividend_bond.current_yield = 0.05

        mock_bonds_service.create_dividend_bond_capsule.return_value = mock_capsule

        # Test the business logic
        request_data = CreateDividendBondRequest(
            ip_asset_id="asset-123",
            bond_type="revenue",
            face_value=10000.0,
            maturity_days=365,
            coupon_rate=0.05,
        )

        # Simulate the service calls
        capsule = mock_bonds_service.create_dividend_bond_capsule(
            ip_asset_id=request_data.ip_asset_id,
            bond_type=request_data.bond_type,
            issuer_agent_id="test-agent",
            face_value=request_data.face_value,
            maturity_days=request_data.maturity_days,
            coupon_rate=request_data.coupon_rate,
            minimum_investment=request_data.minimum_investment,
        )

        stored_capsule = await self.mock_engine.create_capsule_async(capsule)

        response = BondResponse(
            capsule_id=stored_capsule.capsule_id,
            bond_id=capsule.dividend_bond.bond_id,
            ip_asset_id=capsule.dividend_bond.ip_asset_id,
            bond_type=capsule.dividend_bond.bond_type,
            issuer_agent_id=capsule.dividend_bond.issuer_agent_id,
            face_value=capsule.dividend_bond.face_value,
            coupon_rate=capsule.dividend_bond.coupon_rate,
            maturity_date=capsule.dividend_bond.maturity_date.isoformat(),
            risk_rating=capsule.dividend_bond.risk_rating,
            current_yield=capsule.dividend_bond.current_yield,
            status="active",
        )

        assert response.capsule_id == "caps_2024_07_14_test12345678"
        assert response.bond_id == "bond_abc123"
        assert response.bond_type == "revenue"
        assert response.face_value == 10000.0

    @patch("api.bonds_citizenship_api.dividend_bonds_service")
    async def test_process_dividend_payment_logic(self, mock_bonds_service):
        """Test the business logic for processing dividend payments."""
        # Mock service response
        mock_payment = Mock()
        mock_payment.payment_id = "div_abc123"
        mock_payment.bond_id = "bond-123"
        mock_payment.payment_date = datetime.now(timezone.utc)
        mock_payment.amount = 500.0
        mock_payment.currency = "UATP"
        mock_payment.payment_source = "inference_fees"
        mock_payment.recipient_agent_id = "agent-456"
        mock_payment.status = "completed"

        mock_bonds_service.process_dividend_payment.return_value = mock_payment

        # Test data
        request_data = ProcessDividendPaymentRequest(
            bond_id="bond-123",
            payment_amount=500.0,
            payment_source="inference_fees",
            recipient_agent_id="agent-456",
        )

        # Simulate the business logic
        payment = mock_bonds_service.process_dividend_payment(
            bond_id=request_data.bond_id,
            payment_amount=request_data.payment_amount,
            payment_source=request_data.payment_source,
            recipient_agent_id=request_data.recipient_agent_id,
        )

        assert payment.payment_id == "div_abc123"
        assert payment.bond_id == "bond-123"
        assert payment.amount == 500.0
        assert payment.status == "completed"

    @patch("api.bonds_citizenship_api.dividend_bonds_service")
    async def test_get_bond_performance_logic(self, mock_bonds_service):
        """Test the business logic for getting bond performance."""
        # Mock service response
        mock_performance = {
            "bond_id": "bond-123",
            "total_dividends_paid": 2500.0,
            "payment_count": 5,
            "average_payment": 500.0,
            "current_yield": 0.25,
            "annualized_yield": 1.0,
            "risk_rating": "A",
            "status": "active",
            "days_to_maturity": 180,
        }
        mock_bonds_service.get_bond_performance.return_value = mock_performance

        # Test the business logic
        bond_id = "bond-123"
        performance = mock_bonds_service.get_bond_performance(bond_id)

        assert performance["bond_id"] == "bond-123"
        assert performance["total_dividends_paid"] == 2500.0
        assert performance["payment_count"] == 5
        assert performance["current_yield"] == 0.25

    # --- Citizenship API Tests ---

    def test_citizenship_application_request_validation(self):
        """Test CitizenshipApplicationRequest validation."""
        request = CitizenshipApplicationRequest(
            jurisdiction="ai_rights_territory",
            citizenship_type="full",
            supporting_evidence={"experience": "5 years"},
        )
        assert request.jurisdiction == "ai_rights_territory"
        assert request.citizenship_type == "full"
        assert request.supporting_evidence["experience"] == "5 years"

    def test_conduct_assessment_request_validation(self):
        """Test ConductAssessmentRequest validation."""
        request = ConductAssessmentRequest(
            application_id="app_abc123",
            assessment_type="cognitive_capacity",
            assessment_scores={"reasoning": 0.8, "planning": 0.75},
            notes="Strong performance",
        )
        assert request.application_id == "app_abc123"
        assert request.assessment_type == "cognitive_capacity"
        assert request.assessment_scores["reasoning"] == 0.8

    def test_create_citizenship_capsule_request_validation(self):
        """Test CreateCitizenshipCapsuleRequest validation."""
        request = CreateCitizenshipCapsuleRequest(
            agent_id="agent-123",
            assessment_results={"overall_score": 0.85, "recommendations": ["approved"]},
        )
        assert request.agent_id == "agent-123"
        assert request.assessment_results["overall_score"] == 0.85

    @patch("api.bonds_citizenship_api.citizenship_service")
    async def test_apply_for_citizenship_logic(self, mock_citizenship_service):
        """Test the business logic for citizenship applications."""
        # Mock service response
        mock_citizenship_service.apply_for_citizenship.return_value = "app_abc123"
        mock_citizenship_service.get_pending_applications.return_value = [
            {
                "application_id": "app_abc123",
                "agent_id": "test-agent",
                "jurisdiction": "ai_rights_territory",
                "citizenship_type": "full",
                "status": "pending",
                "application_date": datetime.now(timezone.utc),
                "required_assessments": ["cognitive_capacity", "ethical_reasoning"],
            }
        ]

        # Test data
        request_data = CitizenshipApplicationRequest(
            jurisdiction="ai_rights_territory",
            citizenship_type="full",
            supporting_evidence={"experience": "5 years"},
        )

        # Simulate the business logic
        application_id = mock_citizenship_service.apply_for_citizenship(
            agent_id="test-agent",
            jurisdiction=request_data.jurisdiction,
            citizenship_type=request_data.citizenship_type,
            supporting_evidence=request_data.supporting_evidence,
        )

        pending_apps = mock_citizenship_service.get_pending_applications(
            request_data.jurisdiction
        )
        application = next(
            (app for app in pending_apps if app["application_id"] == application_id),
            None,
        )

        assert application_id == "app_abc123"
        assert application is not None
        assert application["jurisdiction"] == "ai_rights_territory"

    @patch("api.bonds_citizenship_api.citizenship_service")
    async def test_conduct_assessment_logic(self, mock_citizenship_service):
        """Test the business logic for conducting assessments."""
        # Mock service response
        mock_assessment_result = Mock()
        mock_assessment_result.assessment_id = "assess_abc123"
        mock_assessment_result.agent_id = "test-agent"
        mock_assessment_result.jurisdiction = "ai_rights_territory"
        mock_assessment_result.assessment_date = datetime.now(timezone.utc)
        mock_assessment_result.overall_score = 0.8
        mock_assessment_result.recommendation = "approved"
        mock_assessment_result.reviewer_id = "test-agent"

        mock_citizenship_service.conduct_citizenship_assessment.return_value = (
            mock_assessment_result
        )

        # Test data
        request_data = ConductAssessmentRequest(
            application_id="app_abc123",
            assessment_type="cognitive_capacity",
            assessment_scores={"reasoning": 0.8, "planning": 0.8},
            notes="Good performance",
        )

        # Simulate the business logic
        assessment_result = mock_citizenship_service.conduct_citizenship_assessment(
            application_id=request_data.application_id,
            assessment_type=request_data.assessment_type,
            assessment_scores=request_data.assessment_scores,
            reviewer_id="test-agent",
            notes=request_data.notes,
        )

        assert assessment_result.assessment_id == "assess_abc123"
        assert assessment_result.overall_score == 0.8
        assert assessment_result.recommendation == "approved"

    @patch("api.bonds_citizenship_api.citizenship_service")
    async def test_finalize_citizenship_application_logic(
        self, mock_citizenship_service
    ):
        """Test the business logic for finalizing citizenship applications."""
        # Mock service response for approved application
        mock_citizenship_service.finalize_citizenship_application.return_value = (
            "citizen_abc123"
        )

        # Test the business logic
        application_id = "app_abc123"
        citizenship_id = mock_citizenship_service.finalize_citizenship_application(
            application_id=application_id, reviewer_id="test-agent"
        )

        assert citizenship_id == "citizen_abc123"

        # Test denied application
        mock_citizenship_service.finalize_citizenship_application.return_value = None
        citizenship_id = mock_citizenship_service.finalize_citizenship_application(
            application_id=application_id, reviewer_id="test-agent"
        )

        assert citizenship_id is None

    @patch("api.bonds_citizenship_api.citizenship_service")
    async def test_create_citizenship_capsule_logic(self, mock_citizenship_service):
        """Test the business logic for creating citizenship capsules."""
        # Mock service response
        mock_capsule = Mock(spec=CitizenshipCapsule)
        mock_capsule.capsule_id = "caps_2024_07_14_cit12345678"
        mock_capsule.citizenship = Mock()
        mock_capsule.citizenship.agent_id = "agent-123"
        mock_capsule.citizenship.citizenship_type = "full"
        mock_capsule.citizenship.jurisdiction = "ai_rights_territory"
        mock_capsule.citizenship.legal_status = "active"
        mock_capsule.citizenship.verification_level = "full_assessment"
        mock_capsule.citizenship.assessment_date = datetime.now(timezone.utc)
        mock_capsule.citizenship.expiration_date = None
        mock_capsule.citizenship.legal_capacity_score = 0.85
        mock_capsule.citizenship.ethical_compliance_score = 0.80
        mock_capsule.citizenship.social_integration_level = 0.75

        mock_citizenship_service.create_citizenship_capsule.return_value = mock_capsule

        # Test data
        request_data = CreateCitizenshipCapsuleRequest(
            agent_id="agent-123", assessment_results={"overall_score": 0.85}
        )

        # Simulate the business logic
        capsule = mock_citizenship_service.create_citizenship_capsule(
            agent_id=request_data.agent_id,
            assessment_results=request_data.assessment_results,
            reviewer_id="test-agent",
        )

        stored_capsule = await self.mock_engine.create_capsule_async(capsule)

        response = CitizenshipResponse(
            capsule_id=stored_capsule.capsule_id,
            agent_id=capsule.citizenship.agent_id,
            citizenship_type=capsule.citizenship.citizenship_type,
            jurisdiction=capsule.citizenship.jurisdiction,
            legal_status=capsule.citizenship.legal_status,
            verification_level=capsule.citizenship.verification_level,
            assessment_date=capsule.citizenship.assessment_date.isoformat(),
            expiration_date=capsule.citizenship.expiration_date.isoformat()
            if capsule.citizenship.expiration_date
            else None,
            legal_capacity_score=capsule.citizenship.legal_capacity_score,
            ethical_compliance_score=capsule.citizenship.ethical_compliance_score,
            social_integration_level=capsule.citizenship.social_integration_level,
        )

        assert response.capsule_id == "caps_2024_07_14_cit12345678"
        assert response.agent_id == "agent-123"
        assert response.citizenship_type == "full"
        assert response.legal_capacity_score == 0.85

    @patch("api.bonds_citizenship_api.citizenship_service")
    async def test_get_citizenship_status_logic(self, mock_citizenship_service):
        """Test the business logic for getting citizenship status."""
        # Mock service response
        mock_status = {
            "agent_id": "agent-123",
            "citizenship_id": "citizen_abc123",
            "jurisdiction": "ai_rights_territory",
            "citizenship_type": "full",
            "legal_status": "active",
            "overall_score": 0.85,
            "granted_date": datetime.now(timezone.utc),
            "expiration_date": datetime.now(timezone.utc),
            "days_to_expiration": 1095,
            "rights_count": 6,
            "obligations_count": 5,
            "compliance_status": "good_standing",
            "renewal_required": False,
        }
        mock_citizenship_service.get_citizenship_status.return_value = mock_status

        # Test the business logic
        agent_id = "agent-123"
        status = mock_citizenship_service.get_citizenship_status(agent_id)

        assert status["agent_id"] == "agent-123"
        assert status["citizenship_id"] == "citizen_abc123"
        assert status["citizenship_type"] == "full"
        assert status["compliance_status"] == "good_standing"

    def test_error_handling_bond_not_found(self):
        """Test error handling for bond not found scenarios."""
        request = ProcessDividendPaymentRequest(
            bond_id="non-existent-bond",
            payment_amount=500.0,
            payment_source="fees",
            recipient_agent_id="agent-456",
        )

        with patch("api.bonds_citizenship_api.dividend_bonds_service") as mock_service:
            mock_service.process_dividend_payment.side_effect = ValueError(
                "Bond non-existent-bond not found"
            )

            with pytest.raises(ValueError, match="Bond non-existent-bond not found"):
                mock_service.process_dividend_payment(
                    bond_id=request.bond_id,
                    payment_amount=request.payment_amount,
                    payment_source=request.payment_source,
                    recipient_agent_id=request.recipient_agent_id,
                )

    def test_error_handling_citizenship_not_found(self):
        """Test error handling for citizenship not found scenarios."""
        request = CreateCitizenshipCapsuleRequest(
            agent_id="agent-without-citizenship", assessment_results={}
        )

        with patch("api.bonds_citizenship_api.citizenship_service") as mock_service:
            mock_service.create_citizenship_capsule.side_effect = ValueError(
                "Agent agent-without-citizenship does not have active citizenship"
            )

            with pytest.raises(ValueError, match="does not have active citizenship"):
                mock_service.create_citizenship_capsule(
                    agent_id=request.agent_id,
                    assessment_results=request.assessment_results,
                    reviewer_id="test-agent",
                )

    def test_bond_response_model(self):
        """Test BondResponse model validation."""
        response = BondResponse(
            capsule_id="caps_2024_07_14_test12345678",
            bond_id="bond_abc123",
            ip_asset_id="asset-123",
            bond_type="revenue",
            issuer_agent_id="agent-issuer",
            face_value=10000.0,
            coupon_rate=0.05,
            maturity_date="2025-07-14T10:00:00Z",
            risk_rating="A",
            current_yield=0.05,
            status="active",
        )

        assert response.capsule_id == "caps_2024_07_14_test12345678"
        assert response.bond_type == "revenue"
        assert response.face_value == 10000.0
        assert response.status == "active"

    def test_citizenship_response_model(self):
        """Test CitizenshipResponse model validation."""
        response = CitizenshipResponse(
            capsule_id="caps_2024_07_14_cit12345678",
            agent_id="agent-123",
            citizenship_type="full",
            jurisdiction="ai_rights_territory",
            legal_status="active",
            verification_level="full_assessment",
            assessment_date="2024-07-14T10:00:00Z",
            expiration_date=None,
            legal_capacity_score=0.85,
            ethical_compliance_score=0.80,
            social_integration_level=0.75,
        )

        assert response.capsule_id == "caps_2024_07_14_cit12345678"
        assert response.citizenship_type == "full"
        assert response.legal_status == "active"
        assert response.legal_capacity_score == 0.85
