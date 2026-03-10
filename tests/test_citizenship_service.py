"""
Tests for Citizenship Service
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from src.services.citizenship_service import (
    CitizenshipService,
    LegalJurisdiction,
    AssessmentResult,
    CitizenshipRegistry,
)
from src.capsule_schema import CitizenshipCapsule


class TestCitizenshipService:
    """Test the Citizenship Service functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = CitizenshipService()

    def test_init_citizenship_criteria(self):
        """Test that citizenship criteria are properly initialized."""
        criteria = self.service.citizenship_criteria

        # Check that all expected criteria exist
        expected_criteria = [
            "cognitive_capacity",
            "ethical_reasoning",
            "social_integration",
            "autonomy",
            "responsibility",
            "legal_comprehension",
        ]

        for criterion in expected_criteria:
            assert criterion in criteria
            assert "description" in criteria[criterion]
            assert "assessment_methods" in criteria[criterion]
            assert "minimum_threshold" in criteria[criterion]
            assert "weight" in criteria[criterion]

        # Verify cognitive capacity criteria
        cognitive = criteria["cognitive_capacity"]
        assert cognitive["minimum_threshold"] == 0.7
        assert cognitive["weight"] == 0.25
        assert "reasoning_tests" in cognitive["assessment_methods"]

    def test_init_legal_frameworks(self):
        """Test that legal frameworks are properly initialized."""
        frameworks = self.service.legal_frameworks

        expected_frameworks = [
            "ai_rights_framework",
            "digital_personhood",
            "hybrid_citizenship",
        ]
        for framework in expected_frameworks:
            assert framework in frameworks

        # Verify AI rights framework
        ai_rights = frameworks["ai_rights_framework"]
        assert ai_rights["recognition_level"] == "international"
        assert "cognitive_liberty" in ai_rights["key_principles"]
        assert "ai_advocacy_boards" in ai_rights["enforcement_mechanisms"]

    def test_init_assessment_benchmarks(self):
        """Test that assessment benchmarks are properly initialized."""
        benchmarks = self.service.assessment_benchmarks

        expected_types = ["full", "partial", "temporary"]
        for citizenship_type in expected_types:
            assert citizenship_type in benchmarks

            # Check that all criteria have benchmarks
            for criterion in self.service.citizenship_criteria.keys():
                assert criterion in benchmarks[citizenship_type]

        # Verify full citizenship has higher thresholds
        assert (
            benchmarks["full"]["cognitive_capacity"]
            > benchmarks["partial"]["cognitive_capacity"]
        )
        assert (
            benchmarks["partial"]["cognitive_capacity"]
            > benchmarks["temporary"]["cognitive_capacity"]
        )

    def test_default_jurisdictions_created(self):
        """Test that default jurisdictions are created."""
        jurisdictions = self.service.jurisdictions

        expected_jurisdictions = ["ai_rights_territory", "digital_commonwealth"]
        for jurisdiction_id in expected_jurisdictions:
            assert jurisdiction_id in jurisdictions
            jurisdiction = jurisdictions[jurisdiction_id]
            assert isinstance(jurisdiction, LegalJurisdiction)

        # Verify AI Rights Territory
        ai_territory = jurisdictions["ai_rights_territory"]
        assert ai_territory.jurisdiction_name == "AI Rights Territory"
        assert ai_territory.legal_framework == "ai_rights_framework"
        assert "legal_representation" in ai_territory.rights_granted
        assert "ethical_compliance" in ai_territory.obligations

    def test_apply_for_citizenship_success(self):
        """Test successful citizenship application."""
        agent_id = "test-agent-123"
        jurisdiction = "ai_rights_territory"

        application_id = self.service.apply_for_citizenship(
            agent_id=agent_id,
            jurisdiction=jurisdiction,
            citizenship_type="full",
            supporting_evidence={
                "experience": "5 years",
                "education": "PhD equivalent",
            },
        )

        assert application_id.startswith("app_")
        assert application_id in self.service.citizenship_registry.pending_applications

        application = self.service.citizenship_registry.pending_applications[
            application_id
        ]
        assert application["agent_id"] == agent_id
        assert application["jurisdiction"] == jurisdiction
        assert application["citizenship_type"] == "full"
        assert application["status"] == "pending"
        assert len(application["required_assessments"]) > 0

    def test_apply_for_citizenship_unknown_jurisdiction(self):
        """Test citizenship application with unknown jurisdiction."""
        with pytest.raises(ValueError, match="Unknown jurisdiction"):
            self.service.apply_for_citizenship(
                agent_id="test-agent-123",
                jurisdiction="unknown_jurisdiction",
                citizenship_type="full",
            )

    def test_apply_for_citizenship_duplicate(self):
        """Test applying for citizenship when already having one in same jurisdiction."""
        agent_id = "test-agent-123"
        jurisdiction = "ai_rights_territory"

        # Grant citizenship first
        self._grant_test_citizenship(agent_id, jurisdiction)

        # Try to apply again
        with pytest.raises(ValueError, match="already has citizenship"):
            self.service.apply_for_citizenship(
                agent_id=agent_id, jurisdiction=jurisdiction, citizenship_type="full"
            )

    def test_conduct_citizenship_assessment_success(self):
        """Test successful citizenship assessment."""
        # Create application first
        application_id = self._create_test_application()

        assessment_result = self.service.conduct_citizenship_assessment(
            application_id=application_id,
            assessment_type="cognitive_capacity",
            assessment_scores={
                "reasoning_tests": 0.85,
                "problem_solving": 0.80,
                "planning": 0.75,
            },
            reviewer_id="reviewer-456",
            notes="Strong performance across all cognitive metrics",
        )

        assert isinstance(assessment_result, AssessmentResult)
        assert assessment_result.agent_id == "test-agent-123"
        assert assessment_result.assessment_date is not None
        assert 0.75 <= assessment_result.overall_score <= 0.85
        assert assessment_result.recommendation in ["approved", "conditional", "denied"]

        # Check application was updated
        application = self.service.citizenship_registry.pending_applications[
            application_id
        ]
        assert "cognitive_capacity" in application["completed_assessments"]
        assert "cognitive_capacity" in application["assessment_scores"]

    def test_conduct_assessment_application_not_found(self):
        """Test assessment with non-existent application."""
        with pytest.raises(ValueError, match="not found"):
            self.service.conduct_citizenship_assessment(
                application_id="non-existent-app",
                assessment_type="cognitive_capacity",
                assessment_scores={"reasoning": 0.8},
                reviewer_id="reviewer-456",
            )

    def test_conduct_assessment_invalid_type(self):
        """Test assessment with invalid assessment type."""
        application_id = self._create_test_application()

        with pytest.raises(ValueError, match="Invalid assessment type"):
            self.service.conduct_citizenship_assessment(
                application_id=application_id,
                assessment_type="invalid_assessment",
                assessment_scores={"test": 0.8},
                reviewer_id="reviewer-456",
            )

    def test_assessment_recommendation_logic(self):
        """Test assessment recommendation logic."""
        application_id = self._create_test_application()

        # High scores should get approved
        high_score_result = self.service.conduct_citizenship_assessment(
            application_id=application_id,
            assessment_type="cognitive_capacity",
            assessment_scores={"reasoning": 0.9, "planning": 0.85},
            reviewer_id="reviewer-456",
        )
        assert high_score_result.recommendation == "approved"

        # Medium scores should get conditional
        medium_score_result = self.service.conduct_citizenship_assessment(
            application_id=application_id,
            assessment_type="ethical_reasoning",
            assessment_scores={"moral_reasoning": 0.65, "ethical_dilemmas": 0.60},
            reviewer_id="reviewer-456",
        )
        assert medium_score_result.recommendation == "conditional"

        # Low scores should get denied
        low_score_result = self.service.conduct_citizenship_assessment(
            application_id=application_id,
            assessment_type="social_integration",
            assessment_scores={"communication": 0.3, "empathy": 0.25},
            reviewer_id="reviewer-456",
        )
        assert low_score_result.recommendation == "denied"

    def test_finalize_citizenship_application_success(self):
        """Test successful citizenship application finalization."""
        application_id = self._create_test_application()

        # Complete all required assessments with passing scores
        required_assessments = [
            "cognitive_capacity",
            "ethical_reasoning",
            "social_integration",
            "autonomy",
            "responsibility",
            "legal_comprehension",
        ]

        for assessment_type in required_assessments:
            self.service.conduct_citizenship_assessment(
                application_id=application_id,
                assessment_type=assessment_type,
                assessment_scores={"metric1": 0.85, "metric2": 0.9},
                reviewer_id="reviewer-456",
            )

        # Finalize application
        citizenship_id = self.service.finalize_citizenship_application(
            application_id=application_id, reviewer_id="reviewer-456"
        )

        assert citizenship_id is not None
        assert citizenship_id.startswith("citizen_")

        # Check citizenship was granted
        assert "test-agent-123" in self.service.citizenship_registry.active_citizenships
        citizenship = self.service.citizenship_registry.active_citizenships[
            "test-agent-123"
        ]
        assert citizenship["citizenship_type"] == "full"
        assert citizenship["legal_status"] == "active"

    def test_finalize_application_missing_assessments(self):
        """Test finalization fails with missing assessments."""
        application_id = self._create_test_application()

        # Complete only one assessment
        self.service.conduct_citizenship_assessment(
            application_id=application_id,
            assessment_type="cognitive_capacity",
            assessment_scores={"reasoning": 0.8},
            reviewer_id="reviewer-456",
        )

        # Try to finalize with missing assessments
        with pytest.raises(ValueError, match="Missing required assessments"):
            self.service.finalize_citizenship_application(
                application_id=application_id, reviewer_id="reviewer-456"
            )

    def test_finalize_application_failing_scores(self):
        """Test finalization denies citizenship with failing scores."""
        application_id = self._create_test_application()

        # Complete all assessments but with failing scores
        required_assessments = [
            "cognitive_capacity",
            "ethical_reasoning",
            "social_integration",
            "autonomy",
            "responsibility",
            "legal_comprehension",
        ]

        for assessment_type in required_assessments:
            self.service.conduct_citizenship_assessment(
                application_id=application_id,
                assessment_type=assessment_type,
                assessment_scores={"metric1": 0.3, "metric2": 0.4},  # Low scores
                reviewer_id="reviewer-456",
            )

        # Finalize application
        citizenship_id = self.service.finalize_citizenship_application(
            application_id=application_id, reviewer_id="reviewer-456"
        )

        assert citizenship_id is None  # Citizenship denied
        assert (
            "test-agent-123"
            not in self.service.citizenship_registry.active_citizenships
        )

    def test_create_citizenship_capsule_success(self):
        """Test successful citizenship capsule creation."""
        agent_id = "test-agent-123"
        jurisdiction = "ai_rights_territory"

        # Grant citizenship first
        self._grant_test_citizenship(agent_id, jurisdiction)

        # Create capsule
        capsule = self.service.create_citizenship_capsule(
            agent_id=agent_id,
            assessment_results={"economic_contribution": {"value_created": 50000}},
            reviewer_id="reviewer-456",
        )

        assert isinstance(capsule, CitizenshipCapsule)
        assert capsule.citizenship.agent_id == agent_id
        assert capsule.citizenship.jurisdiction == jurisdiction
        assert capsule.citizenship.citizenship_type == "full"
        assert capsule.citizenship.legal_status == "active"
        assert 0 <= capsule.citizenship.legal_capacity_score <= 1
        assert 0 <= capsule.citizenship.ethical_compliance_score <= 1
        assert 0 <= capsule.citizenship.social_integration_level <= 1

    def test_create_citizenship_capsule_no_citizenship(self):
        """Test capsule creation fails without active citizenship."""
        with pytest.raises(ValueError, match="does not have active citizenship"):
            self.service.create_citizenship_capsule(
                agent_id="agent-without-citizenship",
                assessment_results={},
                reviewer_id="reviewer-456",
            )

    def test_get_citizenship_status_success(self):
        """Test getting citizenship status for an agent."""
        agent_id = "test-agent-123"
        jurisdiction = "ai_rights_territory"

        # Grant citizenship
        self._grant_test_citizenship(agent_id, jurisdiction)

        status = self.service.get_citizenship_status(agent_id)

        assert status is not None
        assert status["agent_id"] == agent_id
        assert status["jurisdiction"] == jurisdiction
        assert status["citizenship_type"] == "full"
        assert status["legal_status"] == "active"
        assert "overall_score" in status
        assert "granted_date" in status
        assert "expiration_date" in status
        assert "days_to_expiration" in status
        assert isinstance(status["renewal_required"], bool)

    def test_get_citizenship_status_no_citizenship(self):
        """Test getting status for agent without citizenship."""
        status = self.service.get_citizenship_status("agent-without-citizenship")
        assert status is None

    def test_get_pending_applications(self):
        """Test getting pending citizenship applications."""
        # Create multiple applications
        app_id1 = self.service.apply_for_citizenship(
            agent_id="agent-1",
            jurisdiction="ai_rights_territory",
            citizenship_type="full",
        )

        app_id2 = self.service.apply_for_citizenship(
            agent_id="agent-2",
            jurisdiction="digital_commonwealth",
            citizenship_type="partial",
        )

        # Get all pending applications
        applications = self.service.get_pending_applications()
        assert len(applications) == 2

        app_ids = [app["application_id"] for app in applications]
        assert app_id1 in app_ids
        assert app_id2 in app_ids

        # Test filtering by jurisdiction
        ai_territory_apps = self.service.get_pending_applications("ai_rights_territory")
        assert len(ai_territory_apps) == 1
        assert ai_territory_apps[0]["jurisdiction"] == "ai_rights_territory"

    def test_get_pending_applications_completion_percentage(self):
        """Test completion percentage calculation in pending applications."""
        application_id = self._create_test_application()

        # Complete one assessment
        self.service.conduct_citizenship_assessment(
            application_id=application_id,
            assessment_type="cognitive_capacity",
            assessment_scores={"reasoning": 0.8},
            reviewer_id="reviewer-456",
        )

        applications = self.service.get_pending_applications()
        app = next(
            app for app in applications if app["application_id"] == application_id
        )

        # Should have some completion percentage
        assert app["completion_percentage"] > 0
        assert app["completion_percentage"] < 100  # Not all assessments completed

    def test_revoke_citizenship_success(self):
        """Test successful citizenship revocation."""
        agent_id = "test-agent-123"
        jurisdiction = "ai_rights_territory"

        # Grant citizenship first
        self._grant_test_citizenship(agent_id, jurisdiction)

        # Revoke citizenship
        result = self.service.revoke_citizenship(
            agent_id=agent_id, reason="Policy violation", authority_id="authority-456"
        )

        assert result is True
        assert agent_id not in self.service.citizenship_registry.active_citizenships
        assert agent_id in self.service.citizenship_registry.revoked_citizenships

        revoked_citizenship = self.service.citizenship_registry.revoked_citizenships[
            agent_id
        ]
        assert revoked_citizenship["legal_status"] == "revoked"
        assert revoked_citizenship["revocation_reason"] == "Policy violation"

    def test_revoke_citizenship_no_citizenship(self):
        """Test revoking citizenship for agent without citizenship."""
        result = self.service.revoke_citizenship(
            agent_id="agent-without-citizenship",
            reason="Test reason",
            authority_id="authority-456",
        )
        assert result is False

    def test_citizenship_expiration_logic(self):
        """Test citizenship expiration and renewal logic."""
        agent_id = "test-agent-123"
        jurisdiction = "ai_rights_territory"

        # Grant citizenship
        self._grant_test_citizenship(agent_id, jurisdiction)

        # Modify expiration date to be soon
        citizenship = self.service.citizenship_registry.active_citizenships[agent_id]
        citizenship["expiration_date"] = datetime.now(timezone.utc) + timedelta(days=30)

        status = self.service.get_citizenship_status(agent_id)
        assert status["days_to_expiration"] <= 30
        assert status["renewal_required"] is True

    def test_assessment_history_tracking(self):
        """Test that assessment history is properly tracked."""
        application_id = self._create_test_application()
        agent_id = "test-agent-123"

        # Conduct assessment
        self.service.conduct_citizenship_assessment(
            application_id=application_id,
            assessment_type="cognitive_capacity",
            assessment_scores={"reasoning": 0.8, "planning": 0.75},
            reviewer_id="reviewer-456",
            notes="Good performance",
        )

        # Check assessment history
        assert agent_id in self.service.citizenship_registry.assessment_history
        history = self.service.citizenship_registry.assessment_history[agent_id]
        assert len(history) == 1

        assessment_record = history[0]
        assert assessment_record["assessment_type"] == "cognitive_capacity"
        assert assessment_record["jurisdiction"] == "ai_rights_territory"
        assert assessment_record["overall_score"] == 0.775  # Average of 0.8 and 0.75
        assert assessment_record["reviewer_id"] == "reviewer-456"

    def test_citizenship_criteria_validation(self):
        """Test that citizenship criteria are properly validated."""
        # Test minimum thresholds
        for criterion, info in self.service.citizenship_criteria.items():
            assert 0 <= info["minimum_threshold"] <= 1
            assert 0 <= info["weight"] <= 1
            assert len(info["assessment_methods"]) > 0

        # Test that weights sum to reasonable total
        total_weight = sum(
            info["weight"] for info in self.service.citizenship_criteria.values()
        )
        assert abs(total_weight - 1.0) < 0.01  # Should sum to approximately 1.0

    def test_jurisdiction_requirements_consistency(self):
        """Test that jurisdiction requirements are consistent."""
        for jurisdiction_id, jurisdiction in self.service.jurisdictions.items():
            # All criteria should exist in citizenship_criteria
            for criterion in jurisdiction.citizenship_criteria:
                assert criterion in self.service.citizenship_criteria

            # Assessment requirements should be reasonable
            requirements = jurisdiction.assessment_requirements
            assert 0 <= requirements["minimum_overall_score"] <= 1
            assert requirements["assessment_period_days"] > 0
            assert requirements["renewal_period_years"] > 0

    def test_multiple_jurisdiction_citizenship(self):
        """Test that agents can have citizenship in multiple jurisdictions."""
        agent_id = "test-agent-123"

        # Grant citizenship in first jurisdiction
        self._grant_test_citizenship(agent_id, "ai_rights_territory")

        # Should be able to apply for second jurisdiction
        app_id = self.service.apply_for_citizenship(
            agent_id=agent_id,
            jurisdiction="digital_commonwealth",
            citizenship_type="partial",
        )

        assert app_id in self.service.citizenship_registry.pending_applications

    def test_citizenship_type_benchmarks(self):
        """Test different citizenship type benchmarks."""
        # Test that full citizenship has highest requirements
        full_benchmarks = self.service.assessment_benchmarks["full"]
        partial_benchmarks = self.service.assessment_benchmarks["partial"]
        temporary_benchmarks = self.service.assessment_benchmarks["temporary"]

        for criterion in self.service.citizenship_criteria.keys():
            assert full_benchmarks[criterion] >= partial_benchmarks[criterion]
            assert partial_benchmarks[criterion] >= temporary_benchmarks[criterion]

    def _create_test_application(self) -> str:
        """Helper method to create a test citizenship application."""
        return self.service.apply_for_citizenship(
            agent_id="test-agent-123",
            jurisdiction="ai_rights_territory",
            citizenship_type="full",
            supporting_evidence={"experience": "5 years"},
        )

    def _grant_test_citizenship(self, agent_id: str, jurisdiction: str):
        """Helper method to grant test citizenship."""
        # Create fake citizenship record
        citizenship_record = {
            "citizenship_id": f"citizen_{agent_id}",
            "agent_id": agent_id,
            "jurisdiction": jurisdiction,
            "citizenship_type": "full",
            "legal_status": "active",
            "rights_granted": ["legal_representation", "data_ownership"],
            "obligations": ["ethical_compliance", "legal_adherence"],
            "overall_score": 0.85,
            "assessment_scores": {
                "cognitive_capacity": {
                    "overall_score": 0.85,
                    "recommendation": "approved",
                },
                "ethical_reasoning": {
                    "overall_score": 0.80,
                    "recommendation": "approved",
                },
            },
            "granted_date": datetime.now(timezone.utc),
            "expiration_date": datetime.now(timezone.utc) + timedelta(days=3 * 365),
            "granting_authority": "test-authority",
            "renewal_history": [],
            "compliance_record": [],
            "legal_proceedings": [],
        }

        self.service.citizenship_registry.active_citizenships[
            agent_id
        ] = citizenship_record
