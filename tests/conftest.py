"""
Pytest configuration and shared fixtures for UATP testing

Provides common fixtures, test configuration, and utilities for
comprehensive testing of the UATP Capsule Engine architecture.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.config.production_settings import Environment, UATPSettings

# Import core components for testing
from src.core.circuit_breaker import CircuitBreakerConfig, CircuitBreakerManager
from src.core.dependency_injection import ServiceContainer
from src.core.jwt_auth import AuthConfig, JWTAuthenticator


@pytest.fixture(scope="session")
def event_loop_policy():
    """Return the default event loop policy for async tests."""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_env_vars():
    """Clean environment variables for testing"""
    # Store original values
    original_env = dict(os.environ)

    # Clear environment
    os.environ.clear()

    # Set test defaults
    test_env = {
        "ENVIRONMENT": "testing",
        "DEBUG": "true",
        "AUTH__JWT_SECRET_KEY": "test-secret-key-for-testing-only",
        "DATABASE__DATABASE_URL": "sqlite:///test.db",
        "CACHE__CACHE_TYPE": "memory",
    }

    os.environ.update(test_env)

    yield test_env

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def test_settings(test_env_vars):
    """Test configuration settings"""
    # Clear any cached settings
    from src.config.production_settings import get_settings

    get_settings.cache_clear()

    settings = UATPSettings(
        environment=Environment.TESTING,
        debug=True,
        storage_dir=Path("./test_storage"),
        database={"database_url": "sqlite:///test.db"},
        auth={"jwt_secret_key": "test-secret-key"},
    )

    yield settings

    # Clean up test storage
    import shutil

    if settings.storage_dir.exists():
        shutil.rmtree(settings.storage_dir)


@pytest.fixture
def mock_request():
    """Mock FastAPI request object"""
    request = Mock()
    request.url = Mock()
    request.url.path = "/test"
    request.method = "GET"
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.headers = {
        "user-agent": "test-client",
        "x-correlation-id": "test-correlation-id",
    }
    request.state = Mock()
    return request


@pytest.fixture
def circuit_breaker_config():
    """Circuit breaker configuration for testing"""
    return CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=0.1,  # Very short for testing
        request_timeout=0.5,
        success_threshold=2,
        monitor_window=10.0,
    )


@pytest.fixture
def circuit_breaker_manager():
    """Circuit breaker manager for testing"""
    return CircuitBreakerManager()


@pytest.fixture
def auth_config():
    """Authentication configuration for testing"""
    return AuthConfig(
        secret_key="test-secret-key-for-testing-only-do-not-use-in-production",
        algorithm="HS256",
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
        password_min_length=8,
        max_login_attempts=5,
        lockout_duration_minutes=15,
    )


@pytest.fixture
def jwt_authenticator(auth_config):
    """JWT authenticator for testing"""
    return JWTAuthenticator(auth_config)


@pytest.fixture
async def authenticated_user(jwt_authenticator, mock_request):
    """Create an authenticated test user"""
    user = await jwt_authenticator.register_user(
        username="testuser",
        email="test@example.com",
        password="TestPassword123!",
        roles=["user"],
    )

    from src.core.jwt_auth import LoginRequest

    login_request = LoginRequest(username="testuser", password="TestPassword123!")

    token_response = await jwt_authenticator.authenticate_user(
        login_request, mock_request
    )

    return {"user": user, "tokens": token_response}


@pytest.fixture
def service_container():
    """Service container for testing"""
    return ServiceContainer()


@pytest.fixture
def configured_container(service_container, jwt_authenticator):
    """Pre-configured service container with common services"""

    # Register common services
    service_container.register_singleton(JWTAuthenticator, instance=jwt_authenticator)

    # Mock database service
    class MockDatabaseService:
        def __init__(self):
            self.connected = True
            self.data = {}

        async def connect(self):
            self.connected = True

        async def disconnect(self):
            self.connected = False

        async def health_check(self):
            return self.connected

        async def get(self, key: str):
            return self.data.get(key)

        async def set(self, key: str, value: Any):
            self.data[key] = value

    service_container.register_singleton(MockDatabaseService)

    # Mock cache service
    class MockCacheService:
        def __init__(self):
            self.cache = {}

        async def get(self, key: str):
            return self.cache.get(key)

        async def set(self, key: str, value: Any, ttl: int = None):
            self.cache[key] = value

        async def delete(self, key: str):
            self.cache.pop(key, None)

        async def health_check(self):
            return True

    service_container.register_singleton(MockCacheService)

    return service_container


@pytest.fixture
def test_app(configured_container, test_settings):
    """FastAPI test application with configured services"""

    app = FastAPI(title="UATP Test Application", version="test", debug=True)

    # Add test routes
    @app.get("/test/health")
    async def test_health():
        return {"status": "healthy", "environment": "testing"}

    @app.get("/test/error")
    async def test_error():
        raise Exception("Test error for testing error handling")

    @app.get("/test/validation-error")
    async def test_validation_error():
        from src.core.exceptions import ValidationError

        raise ValidationError("Test validation error", field="test_field")

    # Store container in app state
    app.state.container = configured_container
    app.state.settings = test_settings

    return app


@pytest.fixture
def test_client(test_app):
    """Test client for FastAPI application"""
    return TestClient(test_app)


@pytest.fixture
def mock_external_service():
    """Mock external service for testing circuit breakers"""

    class MockExternalService:
        def __init__(self):
            self.call_count = 0
            self.should_fail = False
            self.failure_count = 0

        async def make_request(self, data=None):
            self.call_count += 1

            if self.should_fail:
                self.failure_count += 1
                raise Exception(f"External service failure #{self.failure_count}")

            return {"status": "success", "data": data, "call_count": self.call_count}

        def set_failure_mode(self, should_fail: bool):
            self.should_fail = should_fail

        def reset(self):
            self.call_count = 0
            self.failure_count = 0
            self.should_fail = False

    return MockExternalService()


@pytest.fixture
def sample_test_data():
    """Sample test data for various test scenarios"""
    return {
        "users": [
            {
                "username": "admin_user",
                "email": "admin@test.com",
                "password": "AdminPassword123!",
                "roles": ["admin"],
            },
            {
                "username": "regular_user",
                "email": "user@test.com",
                "password": "UserPassword123!",
                "roles": ["user"],
            },
            {
                "username": "premium_user",
                "email": "premium@test.com",
                "password": "PremiumPassword123!",
                "roles": ["premium_user"],
            },
        ],
        "capsules": [
            {
                "capsule_id": "test-capsule-1",
                "content": "Test capsule content",
                "version": "7.0",
                "author": "test_user",
            },
            {
                "capsule_id": "test-capsule-2",
                "content": "Another test capsule",
                "version": "7.0",
                "author": "admin_user",
            },
        ],
        "api_requests": [
            {"method": "GET", "path": "/api/v1/capsules", "expected_status": 200},
            {
                "method": "POST",
                "path": "/api/v1/capsules",
                "data": {"content": "New capsule"},
                "expected_status": 201,
            },
            {
                "method": "GET",
                "path": "/api/v1/capsules/nonexistent",
                "expected_status": 404,
            },
        ],
    }


@pytest.fixture
async def database_with_test_data(configured_container, sample_test_data):
    """Database populated with test data"""

    db_service = await configured_container.get_service("MockDatabaseService")

    # Populate with test users
    for user_data in sample_test_data["users"]:
        await db_service.set(f"user:{user_data['username']}", user_data)

    # Populate with test capsules
    for capsule_data in sample_test_data["capsules"]:
        await db_service.set(f"capsule:{capsule_data['capsule_id']}", capsule_data)

    return db_service


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Generate data for performance testing"""
    return {
        "large_user_set": [
            {
                "username": f"user_{i}",
                "email": f"user_{i}@test.com",
                "password": f"Password{i}!",
                "roles": ["user"],
            }
            for i in range(1000)
        ],
        "concurrent_requests": 100,
        "load_test_duration": 10,  # seconds
    }


# Error testing fixtures
@pytest.fixture
def error_scenarios():
    """Common error scenarios for testing"""
    return {
        "validation_errors": [
            {
                "field": "email",
                "value": "invalid-email",
                "error": "invalid email format",
            },
            {"field": "password", "value": "123", "error": "password too short"},
            {"field": "username", "value": "", "error": "username required"},
        ],
        "authentication_errors": [
            {
                "username": "nonexistent",
                "password": "password",
                "error": "user not found",
            },
            {"username": "testuser", "password": "wrong", "error": "invalid password"},
        ],
        "authorization_errors": [
            {"action": "delete_user", "role": "user", "error": "permission denied"},
            {
                "action": "view_admin",
                "role": "guest",
                "error": "insufficient privileges",
            },
        ],
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatic cleanup after each test"""
    yield

    # Clear any global state
    from src.core.circuit_breaker import circuit_breaker_manager

    circuit_breaker_manager._breakers.clear()

    # Clear configuration cache
    from src.config.production_settings import get_settings

    get_settings.cache_clear()


# Async testing utilities
@pytest.fixture
def async_test_timeout():
    """Timeout for async tests"""
    return 10.0  # 10 seconds


# Mock implementations for external dependencies
@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""

    class MockOpenAIClient:
        def __init__(self):
            self.request_count = 0

        async def chat_completions_create(self, **kwargs):
            self.request_count += 1
            return {
                "choices": [
                    {
                        "message": {
                            "content": f"Mock response #{self.request_count} for: {kwargs.get('messages', [{}])[-1].get('content', 'no input')}"
                        }
                    }
                ],
                "usage": {"total_tokens": 100},
            }

    return MockOpenAIClient()


@pytest_asyncio.fixture
async def engine():
    """CapsuleEngine instance for testing"""
    import os

    from src.core.database import db
    from src.engine.capsule_engine import CapsuleEngine

    # Set test database URL
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

    # Initialize database
    db.init_app(None)
    await db.create_all()

    # Create engine instance
    test_engine = CapsuleEngine(db_manager=db)

    yield test_engine

    # Cleanup
    if db.engine:
        await db.engine.dispose()


@pytest_asyncio.fixture
async def engine_with_signed_capsules():
    """Create engine with pre-created signed capsules for testing"""
    import os
    import uuid
    from datetime import datetime, timezone

    from src.capsule_schema import (
        CapsuleStatus,
        ReasoningStep,
        ReasoningTraceCapsule,
        ReasoningTracePayload,
        Verification,
    )
    from src.core.database import db
    from src.engine.capsule_engine import CapsuleEngine

    # Set test database URL
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

    # Initialize database
    db.init_app(None)
    await db.create_all()

    # Create engine instance
    test_engine = CapsuleEngine(db_manager=db)

    created_capsules = []

    # Create 3 test capsules with signatures
    for i in range(3):
        # Create unsigned capsule
        unsigned_capsule = ReasoningTraceCapsule(
            capsule_id=f"caps_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}_{uuid.uuid4().hex[:16]}",
            timestamp=datetime.now(timezone.utc),
            status=CapsuleStatus.DRAFT,
            verification=Verification(
                signature=f"ed25519:{'0' * 128}", merkle_root=f"sha256:{'0' * 64}"
            ),
            reasoning_trace=ReasoningTracePayload(
                reasoning_steps=[
                    ReasoningStep(
                        step_id=1,
                        operation="observation",
                        reasoning=f"Test reasoning step for capsule {i}",
                        confidence=0.9,
                    )
                ],
                total_confidence=0.9,
            ),
        )
        # Sign and store capsule
        signed_capsule = await test_engine.create_capsule_async(unsigned_capsule)
        created_capsules.append(signed_capsule)

    yield test_engine, created_capsules

    # Cleanup
    if db.engine:
        await db.engine.dispose()


@pytest_asyncio.fixture
async def async_session_factory():
    """Create a database manager for testing (async session factory)"""
    import os

    from src.core.database import db

    # Set test database URL
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

    # Initialize database
    db.init_app(None)
    await db.create_all()

    yield db

    # Cleanup
    if db.engine:
        await db.engine.dispose()


@pytest.fixture
def mock_policy_manager(mock_db_manager):
    """PolicyManager instance for testing"""
    import uuid
    from datetime import datetime

    from src.insurance.policy_manager import (
        Policy,
        PolicyHolder,
        PolicyManager,
        PolicyStatus,
        PolicyTerms,
    )
    from src.insurance.risk_assessor import DecisionCategory, RiskLevel

    manager = PolicyManager(database_manager=mock_db_manager)

    # Create a sample policy for get_policy calls
    sample_policy = Policy(
        policy_id="POL-TEST123",
        holder=PolicyHolder(
            user_id=str(uuid.uuid4()),
            name="Test User",
            email="test@example.com",
            organization="Test Org",
        ),
        terms=PolicyTerms(
            coverage_amount=100000,
            deductible=1000,
            premium_monthly=150.0,
            term_months=12,
            decision_category=DecisionCategory.CUSTOMER_SERVICE,
            risk_level=RiskLevel.LOW,
            conditions=[],
            exclusions=[],
            max_claims_per_year=3,
            max_payout_per_claim=50000,
        ),
        status=PolicyStatus.ACTIVE,
        created_at=datetime.utcnow(),
        activated_at=datetime.utcnow(),
    )

    # Mock database methods to avoid real DB calls
    manager.get_policy = AsyncMock(return_value=sample_policy)
    manager._fetch_policy = AsyncMock(return_value=sample_policy)
    manager._store_policy = AsyncMock()
    manager._update_policy = AsyncMock()

    return manager


@pytest.fixture
def mock_database_connection():
    """Mock database connection for testing"""

    class MockDatabaseConnection:
        def __init__(self):
            self.connected = False
            self.transactions = []

        async def connect(self):
            self.connected = True

        async def disconnect(self):
            self.connected = False

        async def execute(self, query: str, params=None):
            if not self.connected:
                raise Exception("Database not connected")

            self.transactions.append({"query": query, "params": params})
            return {"affected_rows": 1}

        async def fetch_one(self, query: str, params=None):
            if not self.connected:
                raise Exception("Database not connected")

            return {"id": 1, "result": "mock_data"}

        async def fetch_all(self, query: str, params=None):
            if not self.connected:
                raise Exception("Database not connected")

            return [
                {"id": 1, "result": "mock_data_1"},
                {"id": 2, "result": "mock_data_2"},
            ]

    return MockDatabaseConnection()


# Test markers for categorizing tests
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "security: mark test as a security test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
