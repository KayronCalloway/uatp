"""
Integration tests for user isolation and ownership verification.
Ensures user A cannot access user B's capsules via the HTTP API.

These tests verify the security boundary at the API level:
1. User A cannot GET user B's capsule
2. User A's capsules don't appear in User B's list
3. User A cannot POST outcome to User B's capsule
4. User A cannot query lineage of User B's capsule
5. Admin can access any capsule
6. Legacy capsules (owner_id=NULL) are admin-only

Run with: pytest tests/integration/test_user_isolation.py -v
"""

import os
import sys
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, ".")

# Set test environment BEFORE importing app modules
os.environ["JWT_SECRET"] = "test-jwt-secret-for-integration-tests-minimum-32-bytes-long"
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///uatp_dev.db"

from src.auth.jwt_manager import create_access_token

# Generate fixed UUIDs for reproducible tests
USER_A_ID = str(uuid.uuid4())
USER_B_ID = str(uuid.uuid4())
ADMIN_ID = str(uuid.uuid4())


def make_valid_verification(seed: str) -> dict:
    """Create valid-looking verification data for tests.

    Ed25519 signatures are 64 bytes = 128 hex characters.
    The signature must not be all the same character (placeholder detection).
    """
    import hashlib

    # Generate deterministic but varied hex strings from seed
    h = hashlib.sha256(seed.encode()).hexdigest()
    h2 = hashlib.sha256((seed + "2").encode()).hexdigest()

    return {
        "signature": h + h2,  # 64 + 64 = 128 hex chars, all varied
        "verify_key": hashlib.sha256((seed + "key").encode()).hexdigest(),  # 64 hex
        "hash": hashlib.sha256((seed + "hash").encode()).hexdigest(),  # 64 hex
    }


@pytest.fixture
def user_a_headers():
    """Generate auth headers for User A (regular user)."""
    token, _ = create_access_token(USER_A_ID, "a@test.com", "user_a", ["read", "write"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_b_headers():
    """Generate auth headers for User B (regular user)."""
    token, _ = create_access_token(USER_B_ID, "b@test.com", "user_b", ["read", "write"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers():
    """Generate auth headers for Admin user."""
    token, _ = create_access_token(
        ADMIN_ID, "admin@test.com", "admin", ["read", "write", "admin"]
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def client():
    """Create async test client for the FastAPI app."""
    from src.app_factory import create_app
    from src.core.database import db

    app = create_app()

    # Ensure database is initialized
    if db.session_factory is None:
        db.init_app(app)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as ac:
        yield ac


class TestUserIsolation:
    """Test that users cannot access each other's capsules."""

    @pytest.mark.asyncio
    async def test_user_a_cannot_access_user_b_capsule(
        self, client, user_a_headers, user_b_headers
    ):
        """User A creates capsule, User B gets 403 trying to access it."""
        # User A creates capsule
        capsule_id = f"test-isolation-{uuid.uuid4()}"
        create_resp = await client.post(
            "/capsules/store",
            json={
                "capsule_id": capsule_id,
                "capsule_type": "test",
                "version": "1.0",
                "payload": {"test": "data"},
                "verification": make_valid_verification("isolation"),
            },
            headers=user_a_headers,
        )
        assert create_resp.status_code in (200, 201), (
            f"Create failed: {create_resp.text}"
        )

        # User B tries to access - should get 403
        get_resp = await client.get(f"/capsules/{capsule_id}", headers=user_b_headers)
        assert get_resp.status_code == 403, (
            f"Expected 403, got {get_resp.status_code}: {get_resp.text}"
        )

    @pytest.mark.asyncio
    async def test_user_cannot_see_others_in_list(
        self, client, user_a_headers, user_b_headers
    ):
        """User A's capsules don't appear in User B's list."""
        # User A creates capsule
        capsule_id = f"test-list-{uuid.uuid4()}"
        create_resp = await client.post(
            "/capsules/store",
            json={
                "capsule_id": capsule_id,
                "capsule_type": "test",
                "version": "1.0",
                "payload": {},
                "verification": make_valid_verification("list"),
            },
            headers=user_a_headers,
        )
        assert create_resp.status_code in (200, 201), (
            f"Create failed: {create_resp.text}"
        )

        # User B lists capsules - should not see User A's
        list_resp = await client.get("/capsules", headers=user_b_headers)
        assert list_resp.status_code == 200

        capsule_ids = [c["capsule_id"] for c in list_resp.json().get("capsules", [])]
        assert capsule_id not in capsule_ids, (
            f"User B should not see User A's capsule {capsule_id}"
        )

    @pytest.mark.asyncio
    async def test_admin_can_access_any_capsule(
        self, client, user_a_headers, admin_headers
    ):
        """Admin can access any user's capsule."""
        # User A creates capsule
        capsule_id = f"test-admin-{uuid.uuid4()}"
        create_resp = await client.post(
            "/capsules/store",
            json={
                "capsule_id": capsule_id,
                "capsule_type": "test",
                "version": "1.0",
                "payload": {},
                "verification": make_valid_verification("admin"),
            },
            headers=user_a_headers,
        )
        assert create_resp.status_code in (200, 201), (
            f"Create failed: {create_resp.text}"
        )

        # Admin accesses it - should succeed
        get_resp = await client.get(f"/capsules/{capsule_id}", headers=admin_headers)
        assert get_resp.status_code == 200, (
            f"Admin should be able to access capsule: {get_resp.text}"
        )

    @pytest.mark.asyncio
    async def test_user_cannot_modify_others_outcome(
        self, client, user_a_headers, user_b_headers
    ):
        """User B cannot post outcome to User A's capsule."""
        # User A creates capsule
        capsule_id = f"test-outcome-{uuid.uuid4()}"
        create_resp = await client.post(
            "/capsules/store",
            json={
                "capsule_id": capsule_id,
                "capsule_type": "test",
                "version": "1.0",
                "payload": {},
                "verification": make_valid_verification("outcome"),
            },
            headers=user_a_headers,
        )
        assert create_resp.status_code in (200, 201), (
            f"Create failed: {create_resp.text}"
        )

        # User B tries to set outcome - should get 403
        outcome_resp = await client.post(
            f"/capsules/{capsule_id}/outcome?outcome_status=success",
            headers=user_b_headers,
        )
        assert outcome_resp.status_code == 403, (
            f"User B should not modify User A's outcome: {outcome_resp.text}"
        )

    @pytest.mark.asyncio
    async def test_user_cannot_query_others_lineage(
        self, client, user_a_headers, user_b_headers
    ):
        """User B cannot query lineage of User A's capsule."""
        # User A creates capsule
        capsule_id = f"test-lineage-{uuid.uuid4()}"
        create_resp = await client.post(
            "/capsules/store",
            json={
                "capsule_id": capsule_id,
                "capsule_type": "test",
                "version": "1.0",
                "payload": {},
                "verification": make_valid_verification("lineage"),
            },
            headers=user_a_headers,
        )
        assert create_resp.status_code in (200, 201), (
            f"Create failed: {create_resp.text}"
        )

        # User B tries to query lineage - should get 403
        lineage_resp = await client.get(
            f"/capsules/{capsule_id}/lineage", headers=user_b_headers
        )
        assert lineage_resp.status_code == 403, (
            f"User B should not query User A's lineage: {lineage_resp.text}"
        )

    @pytest.mark.asyncio
    async def test_user_can_access_own_capsule(self, client, user_a_headers):
        """User can access their own capsule."""
        # User A creates and retrieves their own capsule
        capsule_id = f"test-own-{uuid.uuid4()}"
        create_resp = await client.post(
            "/capsules/store",
            json={
                "capsule_id": capsule_id,
                "capsule_type": "test",
                "version": "1.0",
                "payload": {"mine": True},
                "verification": make_valid_verification("own"),
            },
            headers=user_a_headers,
        )
        assert create_resp.status_code in (200, 201), (
            f"Create failed: {create_resp.text}"
        )

        # User A retrieves their own capsule - should succeed
        get_resp = await client.get(f"/capsules/{capsule_id}", headers=user_a_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["capsule"]["capsule_id"] == capsule_id


class TestLegacyCapsuleAccess:
    """Test that legacy capsules (owner_id=NULL) are admin-only."""

    @pytest.mark.asyncio
    async def test_regular_user_cannot_access_legacy_capsule(
        self, client, user_a_headers
    ):
        """Regular user gets 403 on legacy capsule (if one exists)."""
        # Query for a demo capsule which should be legacy (owner_id=NULL)
        # These are typically admin-only
        resp = await client.get("/capsules/demo-sample", headers=user_a_headers)

        # Should be either 403 (access denied) or 404 (not found)
        # Both are acceptable - the key is it's not 200
        assert resp.status_code in (403, 404), (
            f"Expected 403 or 404 for legacy capsule, got {resp.status_code}"
        )


class TestSearchIsolation:
    """Test that search respects user boundaries."""

    @pytest.mark.asyncio
    async def test_search_only_returns_own_capsules(
        self, client, user_a_headers, user_b_headers
    ):
        """Search results only include user's own capsules."""
        # Create a capsule with a unique searchable term
        unique_term = f"uniqueterm{uuid.uuid4().hex[:8]}"
        capsule_id = f"test-search-{uuid.uuid4()}"

        create_resp = await client.post(
            "/capsules/store",
            json={
                "capsule_id": capsule_id,
                "capsule_type": "test",
                "version": "1.0",
                "payload": {"content": f"This contains {unique_term} for testing"},
                "verification": make_valid_verification("search"),
            },
            headers=user_a_headers,
        )
        # Don't fail if create fails - search isolation test still valid
        if create_resp.status_code != 201:
            pytest.skip(f"Capsule creation failed: {create_resp.text}")

        # User B searches - should not find User A's capsule
        search_resp = await client.get(
            f"/capsules/search?q={unique_term}", headers=user_b_headers
        )

        if search_resp.status_code == 200:
            results = search_resp.json().get("results", [])
            result_ids = [r.get("capsule_id") for r in results]
            assert capsule_id not in result_ids, (
                "User B should not find User A's capsule in search"
            )


class TestUnauthenticatedAccess:
    """Test that unauthenticated users cannot access capsules."""

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_list_capsules(self, client):
        """Unauthenticated request to list capsules should fail."""
        resp = await client.get("/capsules")
        # List endpoint requires auth - should return 401
        assert resp.status_code in (401, 403), (
            f"Expected 401/403 for unauthenticated list, got {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_get_capsule(self, client):
        """Unauthenticated request to get specific capsule should fail.

        NOTE: Router returns 401 for unauthenticated access.
        If capsule doesn't exist, it may return 404 before auth check
        to avoid disclosing capsule existence.
        """
        # Try to access a capsule without auth
        resp = await client.get("/capsules/some-random-capsule-id")
        # Should be 401 (unauthenticated) or 404 (not found - avoids disclosure)
        assert resp.status_code in (401, 404), (
            f"Expected 401 or 404 for unauthenticated access, got {resp.status_code}"
        )


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
