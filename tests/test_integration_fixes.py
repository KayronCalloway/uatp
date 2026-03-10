"""
Integration tests for recent critical fixes.

This module tests the fixes implemented to resolve runtime integration issues:
1. CAPSULE_TYPE_MAP implementation
2. Blueprint integration fixes
3. Engine helper updates
4. Database model completeness
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

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
)
from src.models.capsule import CapsuleModel
from src.integrations.federated_registry import FederatedModelRegistry


class TestCapsuleTypeMap:
    """Test the CAPSULE_TYPE_MAP implementation."""

    def test_capsule_type_map_exists(self):
        """Test that CAPSULE_TYPE_MAP exists and is populated."""
        assert CAPSULE_TYPE_MAP is not None
        assert isinstance(CAPSULE_TYPE_MAP, dict)
        assert len(CAPSULE_TYPE_MAP) > 0

    def test_capsule_type_map_completeness(self):
        """Test that all capsule types are mapped."""
        # Get all capsule types from the enum
        all_capsule_types = list(CapsuleType)

        # Check that all types are in the map
        for capsule_type in all_capsule_types:
            assert (
                capsule_type in CAPSULE_TYPE_MAP
            ), f"Missing mapping for {capsule_type}"

    def test_capsule_type_map_validity(self):
        """Test that all mapped classes are valid."""
        for capsule_type, capsule_class in CAPSULE_TYPE_MAP.items():
            assert capsule_class is not None
            assert hasattr(capsule_class, "__name__")
            assert "Capsule" in capsule_class.__name__

    def test_new_capsule_types_mapped(self):
        """Test that newly added capsule types are properly mapped."""
        # Test cloning rights
        assert CapsuleType.CLONING_RIGHTS in CAPSULE_TYPE_MAP
        assert CAPSULE_TYPE_MAP[CapsuleType.CLONING_RIGHTS] == CloningRightsCapsule

        # Test evolution
        assert CapsuleType.EVOLUTION in CAPSULE_TYPE_MAP
        assert CAPSULE_TYPE_MAP[CapsuleType.EVOLUTION] == EvolutionCapsule

        # Test dividend bond
        assert CapsuleType.DIVIDEND_BOND in CAPSULE_TYPE_MAP
        assert CAPSULE_TYPE_MAP[CapsuleType.DIVIDEND_BOND] == DividendBondCapsule

        # Test citizenship
        assert CapsuleType.CITIZENSHIP in CAPSULE_TYPE_MAP
        assert CAPSULE_TYPE_MAP[CapsuleType.CITIZENSHIP] == CitizenshipCapsule


class TestDatabaseModelIntegration:
    """Test the database model integration with all capsule types."""

    def test_all_capsule_types_have_models(self):
        """Test that all capsule types have corresponding database models."""
        from src.models.capsule import (
            CloningRightsCapsuleModel,
            EvolutionCapsuleModel,
            DividendBondCapsuleModel,
            CitizenshipCapsuleModel,
        )

        # Test that model classes exist
        assert CloningRightsCapsuleModel is not None
        assert EvolutionCapsuleModel is not None
        assert DividendBondCapsuleModel is not None
        assert CitizenshipCapsuleModel is not None

    def test_capsule_model_from_pydantic(self):
        """Test that CapsuleModel.from_pydantic works with new capsule types."""
        # Create a cloning rights capsule
        cloning_rights_capsule = CloningRightsCapsule(
            capsule_id=f"caps_{datetime.now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.ACTIVE,
            verification=Verification(),
            cloning_rights=CloningRightsPayload(
                model_id="test-model",
                license_type="commercial",
                licensor_agent_id="test-agent",
                license_terms={"duration": "1 year"},
            ),
        )

        # Test conversion to database model
        db_model = CapsuleModel.from_pydantic(cloning_rights_capsule)
        assert db_model is not None
        assert db_model.capsule_type == CapsuleType.CLONING_RIGHTS.value
        assert db_model.capsule_id == cloning_rights_capsule.capsule_id

    def test_capsule_model_to_pydantic(self):
        """Test that CapsuleModel.to_pydantic works with new capsule types."""
        from src.models.capsule import CloningRightsCapsuleModel

        # Create a database model instance
        db_model = CloningRightsCapsuleModel(
            capsule_id=f"caps_{datetime.now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}",
            version="7.0",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.ACTIVE.value,
            verification={
                "signature": "ed25519:" + "0" * 128,
                "merkle_root": "sha256:" + "0" * 64,
            },
            payload={
                "model_id": "test-model",
                "license_type": "commercial",
                "licensor_agent_id": "test-agent",
                "license_terms": {"duration": "1 year"},
            },
        )

        # Test conversion to pydantic model
        pydantic_model = db_model.to_pydantic()
        assert pydantic_model is not None
        assert isinstance(pydantic_model, CloningRightsCapsule)
        assert pydantic_model.capsule_id == db_model.capsule_id


class TestBlueprintIntegration:
    """Test that blueprint modules can be imported and used."""

    def test_rights_evolution_api_import(self):
        """Test that rights evolution API can be imported."""
        from src.api.rights_evolution_api import create_rights_evolution_api_blueprint

        assert create_rights_evolution_api_blueprint is not None

        # Test blueprint creation
        mock_engine_getter = Mock()
        mock_require_api_key = Mock()
        blueprint = create_rights_evolution_api_blueprint(
            mock_engine_getter, mock_require_api_key
        )
        assert blueprint is not None
        assert blueprint.name == "rights_evolution_api"

    def test_bonds_citizenship_api_import(self):
        """Test that bonds citizenship API can be imported."""
        from src.api.bonds_citizenship_api import create_bonds_citizenship_api_blueprint

        assert create_bonds_citizenship_api_blueprint is not None

        # Test blueprint creation
        mock_engine_getter = Mock()
        mock_require_api_key = Mock()
        blueprint = create_bonds_citizenship_api_blueprint(
            mock_engine_getter, mock_require_api_key
        )
        assert blueprint is not None
        assert blueprint.name == "bonds_citizenship_api"

    def test_app_factory_integration(self):
        """Test that app factory can import and use blueprint modules."""
        try:
            from src.app_factory import create_app

            # This should not raise ImportError anymore
            assert create_app is not None
        except ImportError as e:
            pytest.fail(f"App factory failed to import blueprints: {e}")


class TestEngineHelperIntegration:
    """Test engine helper methods for new capsule types."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock engine for testing."""
        from src.engine.capsule_engine import CapsuleEngine

        # Create a mock engine with required attributes
        engine = Mock(spec=CapsuleEngine)
        engine.agent_id = "test-agent"
        engine.create_capsule_async = AsyncMock()

        return engine

    @pytest.mark.asyncio
    async def test_create_cloning_rights_capsule_helper(self, mock_engine):
        """Test the create_cloning_rights_capsule helper method."""
        # Test that the method exists
        from src.engine.capsule_engine import CapsuleEngine

        assert hasattr(CapsuleEngine, "create_cloning_rights_capsule")

        # Mock the service
        with patch(
            "src.services.cloning_rights_service.cloning_rights_service"
        ) as mock_service:
            mock_capsule = Mock()
            mock_service.create_license_capsule.return_value = mock_capsule
            mock_engine.create_capsule_async.return_value = mock_capsule

            # Test the helper method
            result = await CapsuleEngine.create_cloning_rights_capsule(
                mock_engine,
                model_id="test-model",
                license_type="commercial",
                licensor_agent_id="test-agent",
            )

            assert result == mock_capsule
            mock_service.create_license_capsule.assert_called_once()
            mock_engine.create_capsule_async.assert_called_once_with(mock_capsule)

    @pytest.mark.asyncio
    async def test_create_evolution_capsule_helper(self, mock_engine):
        """Test the create_evolution_capsule helper method."""
        # Test that the method exists
        from src.engine.capsule_engine import CapsuleEngine

        assert hasattr(CapsuleEngine, "create_evolution_capsule")

        # Mock the service
        with patch(
            "src.services.evolution_tracking_service.evolution_tracking_service"
        ) as mock_service:
            mock_capsule = Mock()
            mock_service.detect_evolution.return_value = mock_capsule
            mock_engine.create_capsule_async.return_value = mock_capsule

            # Test the helper method
            result = await CapsuleEngine.create_evolution_capsule(
                mock_engine, model_id="test-model"
            )

            assert result == mock_capsule
            mock_service.detect_evolution.assert_called_once()
            mock_engine.create_capsule_async.assert_called_once_with(mock_capsule)


class TestFederationIntegration:
    """Test federation registry integration fixes."""

    def test_federation_registry_import(self):
        """Test that federation registry can be imported."""
        from src.integrations.federated_registry import FederatedModelRegistry

        assert FederatedModelRegistry is not None

    @pytest.mark.asyncio
    async def test_query_federated_traces(self):
        """Test that _query_federated_traces is implemented."""
        # Create a mock federation registry
        registry = Mock(spec=FederatedModelRegistry)
        registry.members = {}
        registry.trust_config = Mock()
        registry.trust_config.trust_threshold = 0.7

        # Test the method exists and is callable
        from src.integrations.federated_registry import FederatedModelRegistry

        assert hasattr(FederatedModelRegistry, "_query_federated_traces")

        # Create a real instance for testing
        with patch(
            "src.integrations.federated_registry.FederationMember"
        ) as mock_member:
            mock_member.return_value.id = "test-member"
            mock_member.return_value.name = "Test Member"

            registry = FederatedModelRegistry(
                member_id="test-org",
                member_name="Test Organization",
                registry_path="./test_federation",
            )

            # Test the query method
            result = await registry._query_federated_traces({"provider": "test"})
            assert isinstance(result, list)

    def test_federation_demo_fixed(self):
        """Test that federation demo can be imported and doesn't have syntax errors."""
        try:
            from src.integrations.federation_demo import demo_federated_registry

            assert demo_federated_registry is not None
        except SyntaxError as e:
            pytest.fail(f"Federation demo has syntax errors: {e}")
        except ImportError as e:
            pytest.fail(f"Federation demo import failed: {e}")


class TestCapsuleDeserialization:
    """Test capsule deserialization using CAPSULE_TYPE_MAP."""

    def test_capsule_factory_with_new_types(self):
        """Test that the Capsule factory works with new capsule types."""
        from src.capsule_schema import Capsule

        # Test cloning rights capsule creation
        cloning_rights_data = {
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

        capsule = Capsule(**cloning_rights_data)
        assert isinstance(capsule, CloningRightsCapsule)
        assert capsule.capsule_type == CapsuleType.CLONING_RIGHTS

    def test_type_adapter_with_new_types(self):
        """Test that TypeAdapter works with new capsule types."""
        from src.capsule_schema import AnyCapsule
        from pydantic import TypeAdapter

        # Test evolution capsule creation
        evolution_data = {
            "capsule_id": f"caps_{datetime.now().strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}",
            "version": "7.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "capsule_type": "evolution",
            "status": "active",
            "verification": {
                "signature": "ed25519:" + "0" * 128,
                "merkle_root": "sha256:" + "0" * 64,
            },
            "evolution": {
                "model_id": "test-model",
                "evolution_type": "drift",
                "value_drift_score": 0.5,
                "drift_direction": ["conservative"],
                "detected_changes": [],
                "confidence_level": 0.8,
                "evolution_timestamp": datetime.now(timezone.utc).isoformat(),
                "evaluation_methodology": "statistical_analysis",
            },
        }

        adapter = TypeAdapter(AnyCapsule)
        capsule = adapter.validate_python(evolution_data)
        assert isinstance(capsule, EvolutionCapsule)
        assert capsule.capsule_type == CapsuleType.EVOLUTION


class TestRuntimeIntegration:
    """Test that the system can start without runtime errors."""

    def test_create_app_no_import_errors(self):
        """Test that create_app doesn't raise ImportError."""
        try:
            from src.app_factory import create_app

            # This should not raise any import errors
            assert create_app is not None
        except ImportError as e:
            pytest.fail(f"create_app raised ImportError: {e}")

    def test_capsule_engine_instantiation(self):
        """Test that CapsuleEngine can be instantiated with new types."""
        from src.engine.capsule_engine import CapsuleEngine

        # Mock the database manager
        mock_db_manager = Mock()

        # This should not raise any errors
        engine = CapsuleEngine(db_manager=mock_db_manager)
        assert engine is not None
        assert hasattr(engine, "create_cloning_rights_capsule")
        assert hasattr(engine, "create_evolution_capsule")
        assert hasattr(engine, "create_dividend_bond_capsule")
        assert hasattr(engine, "create_citizenship_capsule")

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
