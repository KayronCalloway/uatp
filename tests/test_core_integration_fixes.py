"""
Core integration tests for critical fixes.

This module tests the essential fixes that were implemented:
1. CAPSULE_TYPE_MAP - Complete mapping of all capsule types
2. Database model integration - All capsule types supported
3. Blueprint module integrity - No import errors
4. Capsule deserialization - Factory methods work
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from src.capsule_schema import (
    CAPSULE_TYPE_MAP,
    CapsuleType,
    CloningRightsCapsule,
    CloningRightsPayload,
    EvolutionCapsule,
    EvolutionPayload,
    DividendBondCapsule,
    DividendBondPayload,
    CitizenshipCapsule,
    CitizenshipPayload,
    CapsuleStatus,
    Verification,
    Capsule,
)


class TestCapsuleTypeMapCore:
    """Core tests for CAPSULE_TYPE_MAP functionality."""

    def test_capsule_type_map_exists_and_complete(self):
        """Test that CAPSULE_TYPE_MAP exists and contains all capsule types."""
        # Verify map exists
        assert CAPSULE_TYPE_MAP is not None
        assert isinstance(CAPSULE_TYPE_MAP, dict)

        # Verify all capsule types are mapped
        all_capsule_types = list(CapsuleType)
        assert len(CAPSULE_TYPE_MAP) == len(all_capsule_types)

        for capsule_type in all_capsule_types:
            assert capsule_type in CAPSULE_TYPE_MAP
            assert CAPSULE_TYPE_MAP[capsule_type] is not None

    def test_new_capsule_types_properly_mapped(self):
        """Test that newly added capsule types are properly mapped."""
        critical_new_types = [
            (CapsuleType.CLONING_RIGHTS, CloningRightsCapsule),
            (CapsuleType.EVOLUTION, EvolutionCapsule),
            (CapsuleType.DIVIDEND_BOND, DividendBondCapsule),
            (CapsuleType.CITIZENSHIP, CitizenshipCapsule),
        ]

        for capsule_type, expected_class in critical_new_types:
            assert capsule_type in CAPSULE_TYPE_MAP
            assert CAPSULE_TYPE_MAP[capsule_type] == expected_class


class TestDatabaseModelCore:
    """Core tests for database model integration."""

    def test_database_models_exist(self):
        """Test that all database models exist and can be imported."""
        from src.models.capsule import (
            CapsuleModel,
            CloningRightsCapsuleModel,
            EvolutionCapsuleModel,
            DividendBondCapsuleModel,
            CitizenshipCapsuleModel,
        )

        # Verify all models exist
        assert CapsuleModel is not None
        assert CloningRightsCapsuleModel is not None
        assert EvolutionCapsuleModel is not None
        assert DividendBondCapsuleModel is not None
        assert CitizenshipCapsuleModel is not None

        # Verify they have correct polymorphic identities
        assert (
            CloningRightsCapsuleModel.__mapper_args__["polymorphic_identity"]
            == CapsuleType.CLONING_RIGHTS.value
        )
        assert (
            EvolutionCapsuleModel.__mapper_args__["polymorphic_identity"]
            == CapsuleType.EVOLUTION.value
        )
        assert (
            DividendBondCapsuleModel.__mapper_args__["polymorphic_identity"]
            == CapsuleType.DIVIDEND_BOND.value
        )
        assert (
            CitizenshipCapsuleModel.__mapper_args__["polymorphic_identity"]
            == CapsuleType.CITIZENSHIP.value
        )

    def test_capsule_model_basic_conversion(self):
        """Test basic capsule model conversion without database."""
        # Create a valid cloning rights capsule
        capsule = CloningRightsCapsule(
            capsule_id=f"caps_{datetime.now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.ACTIVE,
            verification=Verification(
                signature="ed25519:" + "0" * 128, merkle_root="sha256:" + "0" * 64
            ),
            cloning_rights=CloningRightsPayload(
                model_id="test-model",
                license_type="commercial",
                licensor_agent_id="test-agent",
                license_terms={"duration": "1 year"},
            ),
        )

        # Test conversion to database model
        from src.models.capsule import CapsuleModel

        db_model = CapsuleModel.from_pydantic(capsule)

        assert db_model is not None
        assert db_model.capsule_type == CapsuleType.CLONING_RIGHTS.value
        assert db_model.capsule_id == capsule.capsule_id
        assert db_model.payload is not None


class TestBlueprintCore:
    """Core tests for blueprint module integrity."""

    def test_blueprint_modules_importable(self):
        """Test that blueprint modules can be imported without errors."""
        # Test rights evolution API
        from src.api.rights_evolution_api import create_rights_evolution_api_blueprint

        assert create_rights_evolution_api_blueprint is not None

        # Test bonds citizenship API
        from src.api.bonds_citizenship_api import create_bonds_citizenship_api_blueprint

        assert create_bonds_citizenship_api_blueprint is not None

    def test_blueprint_creation_works(self):
        """Test that blueprints can be created with mock dependencies."""
        from src.api.rights_evolution_api import create_rights_evolution_api_blueprint
        from src.api.bonds_citizenship_api import create_bonds_citizenship_api_blueprint

        # Mock dependencies
        mock_engine_getter = Mock()
        mock_require_api_key = Mock()

        # Create blueprints
        rights_bp = create_rights_evolution_api_blueprint(
            mock_engine_getter, mock_require_api_key
        )
        bonds_bp = create_bonds_citizenship_api_blueprint(
            mock_engine_getter, mock_require_api_key
        )

        assert rights_bp is not None
        assert bonds_bp is not None
        assert rights_bp.name == "rights_evolution_api"
        assert bonds_bp.name == "bonds_citizenship_api"


class TestCapsuleDeserialization:
    """Core tests for capsule deserialization functionality."""

    def test_capsule_factory_basic_types(self):
        """Test that the Capsule factory works with basic data."""
        # Test with a simple cloning rights capsule
        capsule_data = {
            "capsule_id": f"caps_{datetime.now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}",
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "capsule_type": "cloning_rights",
            "status": "active",
            "verification": {
                "signature": "ed25519:" + "0" * 128,
                "merkle_root": "sha256:" + "0" * 64,
            },
            "cloning_rights": {
                "model_id": "test-model",
                "license_type": "commercial",
                "licensor_agent_id": "test-agent",
                "license_terms": {"duration": "1 year"},
            },
        }

        # Create capsule using factory
        capsule = Capsule(**capsule_data)

        assert capsule is not None
        assert isinstance(capsule, CloningRightsCapsule)
        assert capsule.capsule_type == CapsuleType.CLONING_RIGHTS
        assert capsule.cloning_rights.model_id == "test-model"

    def test_capsule_factory_dividend_bond(self):
        """Test capsule factory with dividend bond type."""
        capsule_data = {
            "capsule_id": f"caps_{datetime.now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}",
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "capsule_type": "dividend_bond",
            "status": "active",
            "verification": {
                "signature": "ed25519:" + "0" * 128,
                "merkle_root": "sha256:" + "0" * 64,
            },
            "dividend_bond": {
                "bond_id": "test-bond",
                "ip_asset_id": "test-asset",
                "bond_type": "revenue",
                "issuer_agent_id": "test-issuer",
                "face_value": 1000.0,
                "coupon_rate": 0.05,
                "maturity_date": datetime.now(timezone.utc).isoformat(),
                "dividend_source": "licensing",
                "payment_frequency": "quarterly",
                "yield_calculation_method": "simple",
                "performance_metrics": {"usage": 0.8},
                "risk_rating": "AA",
            },
        }

        capsule = Capsule(**capsule_data)

        assert capsule is not None
        assert isinstance(capsule, DividendBondCapsule)
        assert capsule.capsule_type == CapsuleType.DIVIDEND_BOND
        assert capsule.dividend_bond.bond_id == "test-bond"


class TestEngineHelperCore:
    """Core tests for engine helper method existence."""

    def test_engine_helper_methods_exist(self):
        """Test that engine helper methods exist and are callable."""
        from src.engine.capsule_engine import CapsuleEngine

        # Test that helper methods exist
        assert hasattr(CapsuleEngine, "create_cloning_rights_capsule")
        assert hasattr(CapsuleEngine, "create_evolution_capsule")
        assert hasattr(CapsuleEngine, "create_dividend_bond_capsule")
        assert hasattr(CapsuleEngine, "create_citizenship_capsule")

        # Test that they are callable
        assert callable(getattr(CapsuleEngine, "create_cloning_rights_capsule"))
        assert callable(getattr(CapsuleEngine, "create_evolution_capsule"))
        assert callable(getattr(CapsuleEngine, "create_dividend_bond_capsule"))
        assert callable(getattr(CapsuleEngine, "create_citizenship_capsule"))


class TestFederationCore:
    """Core tests for federation integration."""

    def test_federation_registry_importable(self):
        """Test that federation registry can be imported."""
        from src.integrations.federated_registry import FederatedModelRegistry

        assert FederatedModelRegistry is not None

    def test_federation_query_method_exists(self):
        """Test that federation query method exists."""
        from src.integrations.federated_registry import FederatedModelRegistry

        assert hasattr(FederatedModelRegistry, "_query_federated_traces")
        assert callable(getattr(FederatedModelRegistry, "_query_federated_traces"))

    def test_federation_demo_importable(self):
        """Test that federation demo can be imported."""
        from src.integrations.federation_demo import demo_federated_registry

        assert demo_federated_registry is not None
        assert callable(demo_federated_registry)


class TestServiceCore:
    """Core tests for service module integrity."""

    def test_all_services_importable(self):
        """Test that all service modules can be imported."""
        service_modules = [
            "src.services.cloning_rights_service",
            "src.services.evolution_tracking_service",
            "src.services.dividend_bonds_service",
            "src.services.citizenship_service",
        ]

        for module_name in service_modules:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

    def test_service_objects_exist(self):
        """Test that service objects exist and can be accessed."""
        from src.services.cloning_rights_service import cloning_rights_service
        from src.services.evolution_tracking_service import evolution_tracking_service
        from src.services.dividend_bonds_service import dividend_bonds_service
        from src.services.citizenship_service import citizenship_service

        assert cloning_rights_service is not None
        assert evolution_tracking_service is not None
        assert dividend_bonds_service is not None
        assert citizenship_service is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
