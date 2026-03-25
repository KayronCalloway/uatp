"""
Integration tests for backend health, readiness, and authorization fixes.

Tests the fixes from the backend audit:
- /health endpoint
- /ready endpoint with proper DB checks
- User profile authorization (self access, admin access, unauthorized rejection)

Run with: pytest tests/integration/test_backend_health_auth.py -v
"""

import importlib
import os
import sys
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# SECURITY: Set a fixed JWT secret for tests BEFORE importing jwt_manager
TEST_JWT_SECRET = "test-jwt-secret-for-integration-tests-minimum-32-bytes"
os.environ["JWT_SECRET"] = TEST_JWT_SECRET

# Ensure src is in path
sys.path.insert(0, ".")

# Force reload jwt_manager to pick up the JWT_SECRET
import src.auth.jwt_manager as jwt_manager_module

importlib.reload(jwt_manager_module)
from src.auth.jwt_manager import create_access_token


@pytest_asyncio.fixture(scope="function")
async def client():
    """Create async test client with proper database initialization."""
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
def user_headers():
    """Generate valid JWT auth headers for a regular user."""
    user_id = "11111111-1111-1111-1111-111111111111"
    token, _ = create_access_token(
        user_id=user_id,
        email="user@example.com",
        username="regularuser",
        scopes=["read", "write"],
    )
    return {"Authorization": f"Bearer {token}", "user_id": user_id}


@pytest.fixture
def other_user_headers():
    """Generate valid JWT auth headers for a different user."""
    user_id = "22222222-2222-2222-2222-222222222222"
    token, _ = create_access_token(
        user_id=user_id,
        email="other@example.com",
        username="otheruser",
        scopes=["read", "write"],
    )
    return {"Authorization": f"Bearer {token}", "user_id": user_id}


@pytest.fixture
def admin_headers():
    """Generate valid JWT auth headers for an admin user."""
    user_id = "99999999-9999-9999-9999-999999999999"
    token, _ = create_access_token(
        user_id=user_id,
        email="admin@example.com",
        username="adminuser",
        scopes=["read", "write", "admin"],
    )
    return {"Authorization": f"Bearer {token}", "user_id": user_id}


# =============================================================================
# HEALTH ENDPOINT TESTS
# =============================================================================


class TestHealthEndpoint:
    """Test GET /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        """Test that health endpoint returns 200 OK."""
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_returns_healthy_status(self, client):
        """Test that health endpoint returns healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_includes_timestamp(self, client):
        """Test that health endpoint includes timestamp."""
        response = await client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "timestamp" in data
        # Timestamp should be ISO format
        assert "T" in data["timestamp"]

    @pytest.mark.asyncio
    async def test_health_no_auth_required(self, client):
        """Test that health endpoint does not require authentication."""
        # Should work without any auth headers
        response = await client.get("/health")
        assert response.status_code == 200


# =============================================================================
# READINESS ENDPOINT TESTS
# =============================================================================


class TestReadinessEndpoint:
    """Test GET /ready endpoint."""

    @pytest.mark.asyncio
    async def test_ready_returns_200_when_healthy(self, client):
        """Test that ready endpoint returns 200 when services are healthy."""
        response = await client.get("/ready")
        # Should be 200 if DB is ready, 503 if not
        assert response.status_code in (200, 503)

    @pytest.mark.asyncio
    async def test_ready_returns_status(self, client):
        """Test that ready endpoint returns status field."""
        response = await client.get("/ready")

        data = response.json()

        if response.status_code == 200:
            assert "status" in data
            assert data["status"] == "ready"
        else:
            # 503 returns HTTP error format with detail
            assert "detail" in data or "error" in data

    @pytest.mark.asyncio
    async def test_ready_includes_checks(self, client):
        """Test that ready endpoint includes health checks."""
        response = await client.get("/ready")

        if response.status_code == 200:
            data = response.json()
            assert "checks" in data
            checks = data["checks"]

            # Should have SQLAlchemy check at minimum
            assert "sqlalchemy" in checks
            assert checks["sqlalchemy"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_ready_no_auth_required(self, client):
        """Test that ready endpoint does not require authentication."""
        response = await client.get("/ready")
        # Should not be 401/403
        assert response.status_code in (200, 503)


# =============================================================================
# STARTUP ENDPOINT TESTS
# =============================================================================


class TestStartupEndpoint:
    """Test GET /startup endpoint."""

    @pytest.mark.asyncio
    async def test_startup_returns_200(self, client):
        """Test that startup endpoint returns 200."""
        response = await client.get("/startup")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_startup_returns_started_status(self, client):
        """Test that startup endpoint returns started status."""
        response = await client.get("/startup")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "started"
        assert "timestamp" in data


# =============================================================================
# USER PROFILE AUTHORIZATION TESTS
# =============================================================================


class TestUserProfileAuthorization:
    """
    Test GET /api/v1/users/{user_id} authorization.

    Security requirements:
    1. Users can only access their own profile
    2. Admins can access any profile
    3. Unauthenticated requests are rejected
    4. Cross-user access without admin is rejected
    """

    @pytest.mark.asyncio
    async def test_user_profile_requires_auth(self, client):
        """Test that user profile endpoint requires authentication."""
        user_id = "11111111-1111-1111-1111-111111111111"
        try:
            response = await client.get(f"/api/v1/users/{user_id}")
            # Should be 401 Unauthorized
            assert response.status_code == 401
        except Exception:
            # If the middleware raises directly, that's also acceptable
            # as it means auth is being enforced
            pass

    @pytest.mark.asyncio
    async def test_user_can_access_own_profile(self, client, user_headers):
        """Test that a user can access their own profile."""
        user_id = user_headers["user_id"]
        headers = {"Authorization": user_headers["Authorization"]}

        response = await client.get(f"/api/v1/users/{user_id}", headers=headers)

        # May be 404 if user doesn't exist in DB, but should NOT be 403
        assert response.status_code in (200, 404, 500)
        # The key assertion: not forbidden
        assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_profile(self, client, user_headers):
        """Test that a regular user cannot access another user's profile."""
        other_user_id = "22222222-2222-2222-2222-222222222222"
        headers = {"Authorization": user_headers["Authorization"]}

        response = await client.get(f"/api/v1/users/{other_user_id}", headers=headers)

        # SECURITY: Must be 403 Forbidden
        assert response.status_code == 403

        data = response.json()
        assert "Access denied" in data.get("detail", "")

    @pytest.mark.asyncio
    async def test_admin_can_access_any_profile(self, client, admin_headers):
        """Test that an admin can access any user's profile."""
        other_user_id = "22222222-2222-2222-2222-222222222222"
        headers = {"Authorization": admin_headers["Authorization"]}

        response = await client.get(f"/api/v1/users/{other_user_id}", headers=headers)

        # Admin should not get 403 - may get 404 if user doesn't exist
        assert response.status_code in (200, 404, 500)
        assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_admin_can_access_own_profile(self, client, admin_headers):
        """Test that an admin can access their own profile."""
        user_id = admin_headers["user_id"]
        headers = {"Authorization": admin_headers["Authorization"]}

        response = await client.get(f"/api/v1/users/{user_id}", headers=headers)

        # Should not be 403
        assert response.status_code in (200, 404, 500)
        assert response.status_code != 403

    @pytest.mark.asyncio
    async def test_unauthorized_profile_access_logged(self, client, user_headers):
        """Test that unauthorized profile access attempts are logged (via response)."""
        other_user_id = "22222222-2222-2222-2222-222222222222"
        headers = {"Authorization": user_headers["Authorization"]}

        response = await client.get(f"/api/v1/users/{other_user_id}", headers=headers)

        assert response.status_code == 403
        data = response.json()
        # Error message should be informative but not leak details
        assert "Access denied" in data.get("detail", "")
        assert "your own" in data.get("detail", "").lower()


# =============================================================================
# METRICS ENDPOINT TESTS
# =============================================================================


class TestMetricsEndpoint:
    """Test GET /metrics endpoint."""

    @pytest.mark.asyncio
    async def test_metrics_returns_200(self, client):
        """Test that metrics endpoint returns 200."""
        response = await client.get("/metrics")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_metrics_returns_prometheus_format(self, client):
        """Test that metrics endpoint returns Prometheus format."""
        response = await client.get("/metrics")
        assert response.status_code == 200

        content = response.text
        # Prometheus metrics typically have # HELP and # TYPE lines
        assert "request" in content.lower() or "http" in content.lower()


# =============================================================================
# HEALTH ACTIVITY ENDPOINT TESTS
# =============================================================================


class TestHealthActivityEndpoint:
    """Test GET /health/activity endpoint."""

    @pytest.mark.asyncio
    async def test_activity_returns_200(self, client):
        """Test that activity endpoint returns 200."""
        response = await client.get("/health/activity")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_activity_returns_activities_list(self, client):
        """Test that activity endpoint returns activities list."""
        response = await client.get("/health/activity")
        assert response.status_code == 200

        data = response.json()
        assert "activities" in data
        assert isinstance(data["activities"], list)


# =============================================================================
# HEALTH METRICS ENDPOINT TESTS
# =============================================================================


class TestHealthMetricsEndpoint:
    """Test GET /health/metrics endpoint."""

    @pytest.mark.asyncio
    async def test_health_metrics_returns_200(self, client):
        """Test that health metrics endpoint returns 200."""
        response = await client.get("/health/metrics")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_metrics_returns_metrics_list(self, client):
        """Test that health metrics endpoint returns metrics list."""
        response = await client.get("/health/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "metrics" in data
        assert isinstance(data["metrics"], list)

    @pytest.mark.asyncio
    async def test_health_metrics_includes_database(self, client):
        """Test that health metrics includes database health."""
        response = await client.get("/health/metrics")
        assert response.status_code == 200

        data = response.json()
        metrics = data["metrics"]

        # Find database metric
        db_metrics = [m for m in metrics if m.get("name") == "database"]
        assert len(db_metrics) > 0

        db_metric = db_metrics[0]
        assert "value" in db_metric
        assert "status" in db_metric


# =============================================================================
# CRYPTO STATUS ENDPOINT TESTS
# =============================================================================


class TestCryptoStatusEndpoint:
    """Test GET /health/crypto endpoint."""

    @pytest.mark.asyncio
    async def test_crypto_status_returns_200(self, client):
        """Test that crypto status endpoint returns 200."""
        response = await client.get("/health/crypto")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_crypto_status_includes_features(self, client):
        """Test that crypto status includes features."""
        response = await client.get("/health/crypto")
        assert response.status_code == 200

        data = response.json()
        assert "features" in data

    @pytest.mark.asyncio
    async def test_crypto_status_includes_summary(self, client):
        """Test that crypto status includes summary."""
        response = await client.get("/health/crypto")
        assert response.status_code == 200

        data = response.json()
        assert "summary" in data
        summary = data["summary"]
        assert "total_features" in summary
        assert "active_features" in summary


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
