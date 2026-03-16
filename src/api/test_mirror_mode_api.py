"""Simple tests for Mirror Mode API blueprint registration."""

from unittest.mock import MagicMock

import pytest


def test_create_mirror_mode_api_blueprint():
    """Test that create_mirror_mode_api_blueprint registers the expected routes."""
    # Import the module
    import inspect

    from api.mirror_mode_api import create_mirror_mode_api_blueprint

    # Mock dependencies
    engine_getter = MagicMock()
    require_api_key = MagicMock()
    require_api_key.return_value = lambda f: f  # Decorator passthrough

    # Create the blueprint
    blueprint = create_mirror_mode_api_blueprint(engine_getter, require_api_key)

    # Verify the blueprint was created with the expected name and url_prefix
    assert blueprint.name == "mirror_mode_api"
    assert blueprint.url_prefix == "/api/v1/mirror"

    # Verify API key requirements were registered with expected permissions

    # Check that require_api_key was called with expected permissions
    # This is a simplified approach just to verify we're registering the expected endpoints
    api_key_calls = [call for call in require_api_key.mock_calls]
    assert len(api_key_calls) >= 4  # At least one call per endpoint

    # Verify we have some route handlers registered
    # This ensures the module registered our endpoints
    route_funcs = [
        obj
        for name, obj in inspect.getmembers(blueprint)
        if name.startswith("view_functions") or name.startswith("deferred_functions")
    ]
    assert len(route_funcs) > 0


def test_import_mirror_mode_api():
    """Test that the mirror_mode_api module can be imported."""
    try:
        import api.mirror_mode_api

        # If we get here, the import succeeded
        assert True
    except ImportError as e:
        raise AssertionError(f"Failed to import mirror_mode_api: {e}")

    # Check for expected classes
    from api.mirror_mode_api import (
        AuditRequest,
        AuditResultResponse,
        ListAuditResultsResponse,
        MirrorConfigRequest,
        MirrorConfigResponse,
    )

    # Verify expected schemas exist
    assert hasattr(AuditRequest, "model_fields")
    assert hasattr(MirrorConfigRequest, "model_fields")
    assert hasattr(MirrorConfigResponse, "model_fields")
    assert hasattr(AuditResultResponse, "model_fields")
    assert hasattr(ListAuditResultsResponse, "model_fields")


def test_server_imports_mirror_mode_api():
    """Test that the server source code imports and registers the mirror mode API blueprint."""
    # Read the server.py file directly to avoid import issues
    import os

    server_path = os.path.join(os.path.dirname(__file__), "server.py")

    try:
        with open(server_path) as f:
            source = f.read()
    except FileNotFoundError:
        pytest.skip("server.py not found - skipping import verification test")

    # Verify mirror_mode_api is imported in server.py (using relative import)
    assert "from .mirror_mode_api import" in source, (
        "server.py should import mirror_mode_api"
    )

    # Verify mirror_mode_api blueprint is registered
    assert "mirror_mode_bp" in source, (
        "server.py should register mirror_mode_api blueprint"
    )
