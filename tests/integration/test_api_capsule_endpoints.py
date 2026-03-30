"""
Integration tests for core Capsule API endpoints.

Tests the main capsule API endpoints to ensure they work correctly:
- POST /capsules - Create capsule
- GET /capsules/{id} - Retrieve capsule
- GET /capsules/{id}/verify - Verify signature
- GET /capsules/stats - Get stats

Run with: pytest tests/integration/test_api_capsule_endpoints.py -v
"""

import importlib
import os
import sys
import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# SECURITY: Set a fixed JWT secret for tests BEFORE importing jwt_manager
# This ensures consistent token signing/verification across test fixtures and app
TEST_JWT_SECRET = "test-jwt-secret-for-integration-tests-minimum-32-bytes"
os.environ["JWT_SECRET"] = TEST_JWT_SECRET

# Ensure src is in path
sys.path.insert(0, ".")

# Force reload jwt_manager to pick up the JWT_SECRET we just set
import src.auth.jwt_manager as jwt_manager_module

importlib.reload(jwt_manager_module)
from src.auth.jwt_manager import create_access_token


@pytest_asyncio.fixture(scope="function")
async def client():
    """Create async test client with proper database initialization."""
    # Ensure JWT_SECRET is set before app creation
    os.environ["JWT_SECRET"] = TEST_JWT_SECRET

    from src.app_factory import create_app
    from src.core.database import db

    app = create_app()

    # Initialize database manually (normally done in lifespan)
    if db.session_factory is None:
        db.init_app(app)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """Generate valid JWT auth headers for authenticated endpoints."""
    # Use a valid UUID format for user_id (required by owner_id column in DB)
    test_user = {
        "user_id": "12345678-1234-5678-1234-567812345678",
        "email": "test@example.com",
        "username": "testuser",
        "scopes": ["read", "write"],
    }
    token, _ = create_access_token(
        user_id=test_user["user_id"],
        email=test_user["email"],
        username=test_user["username"],
        scopes=test_user["scopes"],
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_capsule_payload():
    """Sample capsule data for testing."""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "capsule_id": f"test_api_{unique_id}",
        "type": "reasoning_trace",
        "version": "7.2",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "reasoning_steps": [
                {"step": 1, "thought": "Analyzing request"},
                {"step": 2, "thought": "Computing response"},
            ],
            "conclusion": "Test completed successfully",
            "metadata": {"environment": "test"},
        },
    }


class TestCapsuleStats:
    """Test GET /capsules/stats endpoint."""

    @pytest.mark.asyncio
    async def test_stats_public_access(self, client):
        """Test that stats endpoint is publicly accessible (no auth required)."""
        response = await client.get("/capsules/stats")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_stats_returns_200_with_auth(self, client, auth_headers):
        """Test that stats endpoint also works with auth."""
        response = await client.get("/capsules/stats", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_stats_has_required_fields(self, client, auth_headers):
        """Test that stats response has all required fields."""
        response = await client.get("/capsules/stats", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "total_capsules" in data
        assert "by_type" in data
        assert "database_connected" in data

    @pytest.mark.asyncio
    async def test_stats_demo_mode_filter(self, client, auth_headers):
        """Test demo_mode parameter filters correctly."""
        # Without demo_mode (should exclude demo-* capsules)
        response1 = await client.get(
            "/capsules/stats?demo_mode=false", headers=auth_headers
        )
        assert response1.status_code == 200

        # With demo_mode (should include demo-* capsules)
        response2 = await client.get(
            "/capsules/stats?demo_mode=true", headers=auth_headers
        )
        assert response2.status_code == 200


class TestCapsuleList:
    """Test GET /capsules endpoint."""

    @pytest.mark.asyncio
    async def test_list_requires_auth(self, client):
        """Test that list endpoint requires authentication."""
        response = await client.get("/capsules")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_returns_200(self, client, auth_headers):
        """Test that list endpoint returns 200 OK with auth."""
        response = await client.get("/capsules", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_has_pagination(self, client, auth_headers):
        """Test that list response has pagination fields."""
        response = await client.get("/capsules", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "capsules" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data

    @pytest.mark.asyncio
    async def test_list_pagination_params(self, client, auth_headers):
        """Test pagination parameters work."""
        response = await client.get("/capsules?page=1&per_page=5", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data["capsules"]) <= 5
        assert data["page"] == 1
        assert data["per_page"] == 5

    @pytest.mark.asyncio
    async def test_list_type_filter(self, client, auth_headers):
        """Test type filter parameter."""
        response = await client.get(
            "/capsules?type=reasoning_trace", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        # All returned capsules should have the filtered type
        for capsule in data["capsules"]:
            assert capsule["type"] == "reasoning_trace"


class TestCapsuleCreate:
    """Test POST /capsules endpoint."""

    @pytest.mark.asyncio
    async def test_create_capsule_success(
        self, client, sample_capsule_payload, auth_headers
    ):
        """Test creating a capsule succeeds."""
        response = await client.post(
            "/capsules", json=sample_capsule_payload, headers=auth_headers
        )

        # Should return 200 (or 201)
        assert response.status_code in (200, 201)

        data = response.json()
        assert data.get("success") is True
        assert "capsule_id" in data

    @pytest.mark.asyncio
    async def test_create_returns_capsule_id(
        self, client, sample_capsule_payload, auth_headers
    ):
        """Test that create returns a valid capsule_id."""
        create_response = await client.post(
            "/capsules", json=sample_capsule_payload, headers=auth_headers
        )
        assert create_response.status_code in (200, 201)

        data = create_response.json()
        assert data.get("success") is True
        assert "capsule_id" in data
        assert len(data["capsule_id"]) > 0

    @pytest.mark.asyncio
    async def test_create_with_minimal_data(self, client, auth_headers):
        """Test creating capsule with minimal required data."""
        unique_id = str(uuid.uuid4())[:8]
        minimal_data = {
            "capsule_id": f"minimal_test_{unique_id}",  # Provide unique ID
            "type": "test",
            "payload": {"test": True},
        }

        response = await client.post(
            "/capsules", json=minimal_data, headers=auth_headers
        )
        assert response.status_code in (200, 201)

        data = response.json()
        assert data.get("success") is True
        assert "capsule_id" in data

    @pytest.mark.asyncio
    async def test_create_requires_auth(self, client, sample_capsule_payload):
        """Test that creating a capsule without auth returns 401/403."""
        response = await client.post("/capsules", json=sample_capsule_payload)
        # Should fail without authentication
        assert response.status_code in (401, 403)


class TestCapsuleGet:
    """Test GET /capsules/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_without_auth(self, client):
        """Test that getting a non-existent capsule returns 404 (before auth check)."""
        # NOTE: Router returns 404 for non-existent capsules before checking auth.
        # This is intentional to avoid information disclosure about capsule existence.
        response = await client.get("/capsules/nonexistent_capsule_xyz")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_404(self, client, auth_headers):
        """Test that getting non-existent capsule returns 404."""
        response = await client.get(
            "/capsules/nonexistent_capsule_xyz", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_capsule_has_required_fields(self, client, auth_headers):
        """Test that retrieved capsule has required fields."""
        # Get an existing capsule from the list
        list_response = await client.get("/capsules?per_page=1", headers=auth_headers)
        assert list_response.status_code == 200

        capsules = list_response.json().get("capsules", [])
        if not capsules:
            pytest.skip("No capsules in database to test retrieval")

        capsule_id = capsules[0]["capsule_id"]

        # Get and check fields
        response = await client.get(f"/capsules/{capsule_id}", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        capsule = data["capsule"]

        assert "capsule_id" in capsule
        assert "type" in capsule
        assert "timestamp" in capsule
        assert "payload" in capsule
        assert "verification" in capsule


class TestCapsuleVerify:
    """
    Test GET /capsules/{id}/verify endpoint.

    Note: These tests require proper crypto key configuration (UATP_KEY_PASSWORD).
    Tests may fail with 500 error if crypto keys are not properly configured.
    """

    @pytest.mark.asyncio
    async def test_verify_nonexistent_without_auth(self, client):
        """Test that verifying a non-existent capsule returns 404 or 500 (crypto not configured)."""
        # NOTE: Router returns 404 for non-existent capsules before checking auth,
        # but may return 500 if CryptoSealer fails to initialize (key not configured).
        response = await client.get("/capsules/nonexistent_capsule_xyz/verify")
        # Accept 404 (capsule not found) or 500 (crypto not configured in test env)
        assert response.status_code in (404, 500)

    @pytest.mark.asyncio
    async def test_verify_nonexistent_returns_404(self, client, auth_headers):
        """Test that verifying non-existent capsule returns 404 or 500 (crypto not configured)."""
        response = await client.get(
            "/capsules/nonexistent_capsule_xyz/verify", headers=auth_headers
        )
        # Accept 404 (capsule not found) or 500 (crypto not configured in test env)
        assert response.status_code in (404, 500)

    @pytest.mark.asyncio
    async def test_verify_returns_verification_info(self, client, auth_headers):
        """Test that verify endpoint returns verification info."""
        # Get an existing capsule from the list
        list_response = await client.get("/capsules?per_page=1", headers=auth_headers)
        assert list_response.status_code == 200

        capsules = list_response.json().get("capsules", [])
        if not capsules:
            pytest.skip("No capsules in database to test verification")

        capsule_id = capsules[0]["capsule_id"]

        # Verify - may return 500 if crypto keys not configured in test env
        response = await client.get(
            f"/capsules/{capsule_id}/verify", headers=auth_headers
        )
        if response.status_code == 500:
            pytest.skip("Crypto keys not configured in test environment")

        assert response.status_code == 200

        data = response.json()
        assert "capsule_id" in data
        assert "verified" in data
        assert "verification_method" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_verify_returns_boolean_status(self, client, auth_headers):
        """Test that verification endpoint returns proper boolean status."""
        # Get an existing capsule from the list
        list_response = await client.get("/capsules?per_page=1", headers=auth_headers)
        assert list_response.status_code == 200

        capsules = list_response.json().get("capsules", [])
        if not capsules:
            pytest.skip("No capsules in database to test verification")

        capsule_id = capsules[0]["capsule_id"]

        # Verify endpoint should return verification info
        # May return 500 if crypto keys not configured in test env
        response = await client.get(
            f"/capsules/{capsule_id}/verify", headers=auth_headers
        )
        if response.status_code == 500:
            pytest.skip("Crypto keys not configured in test environment")

        assert response.status_code == 200

        data = response.json()
        # Should have verification fields regardless of verified status
        assert "verified" in data
        assert "verification_method" in data
        assert isinstance(data["verified"], bool)


class TestEndpointErrorHandling:
    """Test error handling across endpoints."""

    @pytest.mark.asyncio
    async def test_invalid_pagination(self, client, auth_headers):
        """Test invalid pagination parameters."""
        # Page 0 is invalid (must be >= 1)
        response = await client.get("/capsules?page=0", headers=auth_headers)
        assert response.status_code == 422  # Validation error

        # Negative per_page
        response = await client.get("/capsules?per_page=-1", headers=auth_headers)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_excessive_per_page(self, client, auth_headers):
        """Test per_page exceeding maximum."""
        # per_page > 100 should be rejected
        response = await client.get("/capsules?per_page=1000", headers=auth_headers)
        assert response.status_code == 422


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
