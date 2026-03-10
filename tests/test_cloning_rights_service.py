"""
Tests for Cloning Rights Service
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.capsule_schema import CloningRightsCapsule
from src.services.cloning_rights_service import (
    CloningRightsService,
    LicenseRegistry,
    ModelRights,
)


class TestCloningRightsService:
    """Test the Cloning Rights Service functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = CloningRightsService()

    def test_init_license_templates(self):
        """Test that license templates are properly initialized."""
        templates = self.service.license_templates

        # Check that all expected license types exist
        expected_types = [
            "exclusive",
            "non_exclusive",
            "research",
            "commercial",
            "open_source",
        ]
        for license_type in expected_types:
            assert license_type in templates

        # Verify exclusive license template
        exclusive = templates["exclusive"]
        assert exclusive["cloning_permitted"] is True
        assert exclusive["modification_permitted"] is True
        assert exclusive["redistribution_permitted"] is True
        assert exclusive["attribution_required"] is False
        assert exclusive["default_royalty"] == 0.0

        # Verify non-exclusive license template
        non_exclusive = templates["non_exclusive"]
        assert non_exclusive["cloning_permitted"] is False
        assert non_exclusive["attribution_required"] is True
        assert non_exclusive["default_royalty"] == 0.15
        assert "commercial_use_restricted" in non_exclusive["usage_restrictions"]

    def test_register_model_rights_success(self):
        """Test successful model rights registration."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"

        rights = self.service.register_model_rights(
            model_id=model_id,
            owner_agent_id=owner_agent_id,
            base_license_type="exclusive",
            moral_constraints=["no_harm", "respect_privacy"],
        )

        assert isinstance(rights, ModelRights)
        assert rights.model_id == model_id
        assert rights.owner_agent_id == owner_agent_id
        assert rights.base_license_type == "exclusive"
        assert "no_harm" in rights.moral_constraints
        assert "respect_privacy" in rights.moral_constraints
        assert rights.model_id in self.service.model_rights_db

    def test_register_model_rights_duplicate_fails(self):
        """Test that registering duplicate model rights fails."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"

        # Register once
        self.service.register_model_rights(
            model_id=model_id, owner_agent_id=owner_agent_id
        )

        # Try to register again - should fail
        with pytest.raises(ValueError, match="already has registered rights"):
            self.service.register_model_rights(
                model_id=model_id, owner_agent_id=owner_agent_id
            )

    def test_create_license_capsule_success(self):
        """Test successful license capsule creation."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"
        licensee_agent_id = "agent-licensee-789"

        # First register model rights
        self.service.register_model_rights(
            model_id=model_id,
            owner_agent_id=owner_agent_id,
            base_license_type="commercial",
        )

        # Create license capsule
        capsule = self.service.create_license_capsule(
            model_id=model_id,
            license_type="commercial",
            licensor_agent_id=owner_agent_id,
            licensee_agent_id=licensee_agent_id,
            license_fee=500.0,
            duration_days=365,
        )

        assert isinstance(capsule, CloningRightsCapsule)
        assert capsule.cloning_rights.model_id == model_id
        assert capsule.cloning_rights.licensor_agent_id == owner_agent_id
        assert capsule.cloning_rights.licensee_agent_id == licensee_agent_id
        assert capsule.cloning_rights.license_fee == 500.0
        assert capsule.cloning_rights.license_type == "commercial"

        # Check that license was registered
        licenses = self.service.get_model_licenses(model_id)
        assert len(licenses) == 1
        assert licenses[0]["license_type"] == "commercial"

    def test_create_license_capsule_model_not_found(self):
        """Test license creation fails when model not found."""
        with pytest.raises(ValueError, match="not found in rights database"):
            self.service.create_license_capsule(
                model_id="non-existent-model",
                license_type="commercial",
                licensor_agent_id="agent-123",
            )

    def test_create_license_capsule_wrong_owner(self):
        """Test license creation fails when licensor is not owner."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"
        fake_licensor = "agent-fake-789"

        # Register model with real owner
        self.service.register_model_rights(
            model_id=model_id, owner_agent_id=owner_agent_id
        )

        # Try to create license with fake licensor
        with pytest.raises(ValueError, match="does not own model"):
            self.service.create_license_capsule(
                model_id=model_id,
                license_type="commercial",
                licensor_agent_id=fake_licensor,
            )

    def test_create_license_capsule_unknown_license_type(self):
        """Test license creation fails with unknown license type."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"

        # Register model
        self.service.register_model_rights(
            model_id=model_id, owner_agent_id=owner_agent_id
        )

        # Try to create license with unknown type
        with pytest.raises(ValueError, match="Unknown license type"):
            self.service.create_license_capsule(
                model_id=model_id,
                license_type="unknown_license",
                licensor_agent_id=owner_agent_id,
            )

    def test_validate_usage_owner_access(self):
        """Test that model owner always has access."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"

        # Register model
        self.service.register_model_rights(
            model_id=model_id, owner_agent_id=owner_agent_id
        )

        # Validate owner usage
        result = self.service.validate_usage(
            model_id=model_id, agent_id=owner_agent_id, usage_type="any_usage"
        )

        assert result["allowed"] is True
        assert "owner has full rights" in result["reason"]
        assert result["license_id"] is None

    def test_validate_usage_model_not_found(self):
        """Test usage validation for non-existent model."""
        result = self.service.validate_usage(
            model_id="non-existent-model", agent_id="any-agent", usage_type="any_usage"
        )

        assert result["allowed"] is False
        assert "not found in rights database" in result["reason"]
        assert result["license_required"] is True

    def test_validate_usage_no_license(self):
        """Test usage validation without valid license."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"
        unlicensed_agent = "agent-unlicensed-789"

        # Register model
        self.service.register_model_rights(
            model_id=model_id, owner_agent_id=owner_agent_id
        )

        # Validate unlicensed agent usage
        result = self.service.validate_usage(
            model_id=model_id, agent_id=unlicensed_agent, usage_type="commercial_use"
        )

        assert result["allowed"] is False
        assert "No valid license found" in result["reason"]
        assert result["license_required"] is True

    def test_validate_usage_with_valid_license(self):
        """Test usage validation with valid license."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"
        licensee_agent_id = "agent-licensee-789"

        # Register model and create license
        self.service.register_model_rights(
            model_id=model_id, owner_agent_id=owner_agent_id
        )

        self.service.create_license_capsule(
            model_id=model_id,
            license_type="commercial",
            licensor_agent_id=owner_agent_id,
            licensee_agent_id=licensee_agent_id,
        )

        # Validate licensed usage
        result = self.service.validate_usage(
            model_id=model_id, agent_id=licensee_agent_id, usage_type="standard_use"
        )

        assert result["allowed"] is True
        assert "commercial license found" in result["reason"]
        assert result["license_id"] is not None

    def test_validate_usage_restricted_usage_type(self):
        """Test usage validation with restricted usage type."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"
        licensee_agent_id = "agent-licensee-789"

        # Register model and create research license (has restrictions)
        self.service.register_model_rights(
            model_id=model_id, owner_agent_id=owner_agent_id
        )

        self.service.create_license_capsule(
            model_id=model_id,
            license_type="research",
            licensor_agent_id=owner_agent_id,
            licensee_agent_id=licensee_agent_id,
        )

        # Try commercial use with research license
        result = self.service.validate_usage(
            model_id=model_id,
            agent_id=licensee_agent_id,
            usage_type="no_commercial_use",  # This is in research restrictions
        )

        assert result["allowed"] is False
        assert "restricted by license" in result["reason"]

    def test_validate_usage_expired_license(self):
        """Test usage validation with expired license."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"
        licensee_agent_id = "agent-licensee-789"

        # Register model and create license
        self.service.register_model_rights(
            model_id=model_id, owner_agent_id=owner_agent_id
        )

        self.service.create_license_capsule(
            model_id=model_id,
            license_type="commercial",
            licensor_agent_id=owner_agent_id,
            licensee_agent_id=licensee_agent_id,
            duration_days=1,  # Very short duration
        )

        # Manually expire the license
        for license_info in self.service.license_registry.active_licenses.values():
            if license_info["model_id"] == model_id:
                license_info["expiration_date"] = datetime.now(
                    timezone.utc
                ) - timedelta(days=1)
                break

        # Validate usage with expired license
        result = self.service.validate_usage(
            model_id=model_id, agent_id=licensee_agent_id, usage_type="standard_use"
        )

        assert result["allowed"] is False
        assert "No valid license found" in result["reason"]

    def test_license_priority_system(self):
        """Test that license priority system works correctly."""
        priorities = self.service._license_priority

        # Test priority ordering
        assert priorities("exclusive") > priorities("commercial")
        assert priorities("commercial") > priorities("open_source")
        assert priorities("open_source") > priorities("non_exclusive")
        assert priorities("non_exclusive") > priorities("research")
        assert priorities("unknown_type") == 0

    def test_log_usage(self):
        """Test usage logging functionality."""
        model_id = "test-model-123"
        agent_id = "agent-789"
        usage_type = "inference"
        license_id = "license-456"

        # Log usage
        self.service.log_usage(
            model_id=model_id,
            agent_id=agent_id,
            usage_type=usage_type,
            license_id=license_id,
        )

        # Check that usage was logged
        logs = self.service.license_registry.license_usage_logs
        assert model_id in logs
        assert len(logs[model_id]) == 1

        log_entry = logs[model_id][0]
        assert log_entry["model_id"] == model_id
        assert log_entry["agent_id"] == agent_id
        assert log_entry["usage_type"] == usage_type
        assert log_entry["license_id"] == license_id
        assert "timestamp" in log_entry

    def test_get_model_licenses(self):
        """Test getting licenses for a specific model."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"

        # Register model and create multiple licenses
        self.service.register_model_rights(
            model_id=model_id, owner_agent_id=owner_agent_id
        )

        self.service.create_license_capsule(
            model_id=model_id,
            license_type="commercial",
            licensor_agent_id=owner_agent_id,
            licensee_agent_id="agent-1",
        )

        self.service.create_license_capsule(
            model_id=model_id,
            license_type="research",
            licensor_agent_id=owner_agent_id,
            licensee_agent_id="agent-2",
        )

        # Get licenses
        licenses = self.service.get_model_licenses(model_id)

        assert len(licenses) == 2
        license_types = [lic["license_type"] for lic in licenses]
        assert "commercial" in license_types
        assert "research" in license_types

    def test_get_agent_licenses(self):
        """Test getting licenses for a specific agent."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"
        licensee_agent_id = "agent-licensee-789"

        # Register model and create license
        self.service.register_model_rights(
            model_id=model_id, owner_agent_id=owner_agent_id
        )

        self.service.create_license_capsule(
            model_id=model_id,
            license_type="commercial",
            licensor_agent_id=owner_agent_id,
            licensee_agent_id=licensee_agent_id,
        )

        # Get licenses for licensee
        licensee_licenses = self.service.get_agent_licenses(licensee_agent_id)
        assert len(licensee_licenses) == 1
        assert licensee_licenses[0]["licensee_agent_id"] == licensee_agent_id

        # Get licenses for licensor
        licensor_licenses = self.service.get_agent_licenses(owner_agent_id)
        assert len(licensor_licenses) == 1
        assert licensor_licenses[0]["licensor_agent_id"] == owner_agent_id

    def test_revoke_license(self):
        """Test license revocation functionality."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"
        licensee_agent_id = "agent-licensee-789"

        # Register model and create license
        self.service.register_model_rights(
            model_id=model_id, owner_agent_id=owner_agent_id
        )

        self.service.create_license_capsule(
            model_id=model_id,
            license_type="commercial",
            licensor_agent_id=owner_agent_id,
            licensee_agent_id=licensee_agent_id,
        )

        # Get the license ID
        licenses = self.service.get_model_licenses(model_id)
        license_id = licenses[0]["license_id"]

        # Revoke the license
        result = self.service.revoke_license(license_id, "Terms violation")
        assert result is True

        # Check that license is no longer active
        assert license_id not in self.service.license_registry.active_licenses
        assert license_id in self.service.license_registry.revoked_licenses

        revoked_license = self.service.license_registry.revoked_licenses[license_id]
        assert revoked_license["status"] == "revoked"
        assert revoked_license["revocation_reason"] == "Terms violation"

    def test_revoke_nonexistent_license(self):
        """Test revoking a non-existent license."""
        result = self.service.revoke_license("non-existent-license", "Test reason")
        assert result is False

    def test_license_with_custom_terms(self):
        """Test creating license with custom terms."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"

        # Register model
        self.service.register_model_rights(
            model_id=model_id, owner_agent_id=owner_agent_id
        )

        # Create license with custom terms
        custom_terms = {
            "max_queries_per_day": 1000,
            "allowed_regions": ["US", "EU"],
            "custom_restriction": "No military applications",
        }

        capsule = self.service.create_license_capsule(
            model_id=model_id,
            license_type="commercial",
            licensor_agent_id=owner_agent_id,
            custom_terms=custom_terms,
        )

        # Check that custom terms are included
        license_terms = capsule.cloning_rights.license_terms
        assert license_terms["max_queries_per_day"] == 1000
        assert "US" in license_terms["allowed_regions"]
        assert license_terms["custom_restriction"] == "No military applications"

    def test_license_with_expiration(self):
        """Test creating license with expiration date."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"

        # Register model
        self.service.register_model_rights(
            model_id=model_id, owner_agent_id=owner_agent_id
        )

        # Create license with 30-day duration
        capsule = self.service.create_license_capsule(
            model_id=model_id,
            license_type="commercial",
            licensor_agent_id=owner_agent_id,
            duration_days=30,
        )

        # Check that expiration date is set
        expiration = capsule.cloning_rights.expiration_date
        assert expiration is not None

        # Should be approximately 30 days from now
        expected_expiration = datetime.now(timezone.utc) + timedelta(days=30)
        time_diff = abs((expiration - expected_expiration).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance

    def test_model_rights_with_moral_constraints(self):
        """Test model rights with moral constraints."""
        model_id = "test-model-123"
        owner_agent_id = "agent-owner-456"
        moral_constraints = ["no_harmful_content", "respect_privacy", "no_bias"]

        # Register model with moral constraints
        rights = self.service.register_model_rights(
            model_id=model_id,
            owner_agent_id=owner_agent_id,
            moral_constraints=moral_constraints,
        )

        assert rights.moral_constraints == moral_constraints

        # Create license and verify constraints are inherited
        capsule = self.service.create_license_capsule(
            model_id=model_id,
            license_type="commercial",
            licensor_agent_id=owner_agent_id,
        )

        assert capsule.cloning_rights.moral_constraints == moral_constraints
