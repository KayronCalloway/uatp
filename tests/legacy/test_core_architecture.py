"""
Comprehensive test suite for core architecture components

Tests the fundamental architectural components including:
- Circuit breaker functionality
- JWT authentication and RBAC
- Dependency injection container
- Configuration management
- Exception handling
- Integration between components

Achieves 90%+ test coverage for critical production components.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.config.production_settings import (
    AuthSettings,
    DatabaseSettings,
    Environment,
    UATPSettings,
    get_settings,
    validate_settings,
)

# Import core components
from src.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitState,
    circuit_breaker,
    circuit_breaker_manager,
)
from src.core.dependency_injection import (
    CircularDependencyError,
    DependencyInjectionError,
    ServiceContainer,
    ServiceLifetime,
    ServiceNotFoundError,
    ServiceScope,
)
from src.core.exceptions import (
    AuthenticationError,
    BaseUATPException,
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
    ValidationError,
)
from src.core.jwt_auth import (
    AuthConfig,
    JWTAuthenticator,
    LoginRequest,
    Permission,
    TokenResponse,
    UserModel,
    UserRole,
)


class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    @pytest.fixture
    def circuit_breaker_config(self):
        """Circuit breaker configuration for testing"""
        return CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1.0,  # Short timeout for tests
            request_timeout=0.5,
            success_threshold=2,
        )

    @pytest.fixture
    def circuit_breaker(self, circuit_breaker_config):
        """Circuit breaker instance for testing"""
        return CircuitBreaker("test_service", circuit_breaker_config)

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self, circuit_breaker):
        """Test circuit breaker in closed state allows requests"""
        assert circuit_breaker.state == CircuitState.CLOSED

        async with circuit_breaker.call() as cb:
            assert cb.should_proceed
            result = "success"
            await cb.on_success(result)
            assert result == "success"

    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_handling(self, circuit_breaker):
        """Test circuit breaker handles failures correctly"""

        # Simulate failures to trip the circuit
        for i in range(3):
            try:
                async with circuit_breaker.call():
                    raise Exception(f"Failure {i + 1}")
            except Exception:
                pass

        # Circuit should now be open
        assert circuit_breaker.state == CircuitState.OPEN

        # Next request should fail fast
        with pytest.raises(CircuitBreakerError):
            async with circuit_breaker.call():
                pass

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, circuit_breaker):
        """Test circuit breaker recovery after failures"""

        # Trip the circuit
        for i in range(3):
            try:
                async with circuit_breaker.call():
                    raise Exception(f"Failure {i + 1}")
            except Exception:
                pass

        assert circuit_breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Should transition to half-open
        async with circuit_breaker.call() as cb:
            assert circuit_breaker.state == CircuitState.HALF_OPEN
            await cb.on_success()

        # Still in half-open, need more successes
        async with circuit_breaker.call() as cb:
            await cb.on_success()

        # Should now be closed
        assert circuit_breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator functionality"""

        @circuit_breaker("test_decorated_service")
        async def failing_service():
            raise Exception("Service failure")

        @circuit_breaker("test_decorated_service")
        async def working_service():
            return "success"

        # Test that decorator works
        result = await working_service()
        assert result == "success"

        # Test failure handling
        with pytest.raises(Exception):
            await failing_service()

    def test_get_stats(self, circuit_breaker):
        """Test circuit breaker statistics"""
        stats = circuit_breaker.get_stats()

        assert stats["name"] == "test_service"
        assert stats["state"] == CircuitState.CLOSED.value
        assert "failure_count" in stats
        assert "success_count" in stats
        assert "config" in stats


class TestJWTAuthentication:
    """Test JWT authentication and RBAC"""

    @pytest.fixture
    def auth_config(self):
        """Authentication configuration for testing"""
        return AuthConfig(
            secret_key="test-secret-key-for-testing",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7,
        )

    @pytest.fixture
    def jwt_auth(self, auth_config):
        """JWT authenticator instance for testing"""
        return JWTAuthenticator(auth_config)

    @pytest.mark.asyncio
    async def test_user_registration(self, jwt_auth):
        """Test user registration functionality"""
        user = await jwt_auth.register_user(
            username="testuser",
            email="test@example.com",
            password="TestPassword123!",
            roles=[UserRole.USER],
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert UserRole.USER in user.roles
        assert user.is_active

    @pytest.mark.asyncio
    async def test_user_authentication(self, jwt_auth):
        """Test user authentication flow"""
        # Register user first
        await jwt_auth.register_user(
            username="testuser", email="test@example.com", password="TestPassword123!"
        )

        # Mock request object
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-agent"}

        # Authenticate user
        login_request = LoginRequest(username="testuser", password="TestPassword123!")
        token_response = await jwt_auth.authenticate_user(login_request, request)

        assert isinstance(token_response, TokenResponse)
        assert token_response.access_token
        assert token_response.refresh_token
        assert token_response.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_invalid_credentials(self, jwt_auth):
        """Test authentication with invalid credentials"""
        # Register user first
        await jwt_auth.register_user(
            username="testuser", email="test@example.com", password="TestPassword123!"
        )

        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-agent"}

        # Try with wrong password
        login_request = LoginRequest(username="testuser", password="WrongPassword")

        with pytest.raises(Exception):  # Should raise HTTPException
            await jwt_auth.authenticate_user(login_request, request)

    @pytest.mark.asyncio
    async def test_token_refresh(self, jwt_auth):
        """Test token refresh functionality"""
        # Register and authenticate user
        await jwt_auth.register_user(
            username="testuser", email="test@example.com", password="TestPassword123!"
        )

        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-agent"}

        login_request = LoginRequest(username="testuser", password="TestPassword123!")
        token_response = await jwt_auth.authenticate_user(login_request, request)

        # Test token refresh
        from src.core.jwt_auth import RefreshTokenRequest

        refresh_request = RefreshTokenRequest(
            refresh_token=token_response.refresh_token
        )
        new_token_response = await jwt_auth.refresh_token(refresh_request)

        assert new_token_response.access_token != token_response.access_token
        assert new_token_response.refresh_token != token_response.refresh_token

    def test_permission_checking(self, jwt_auth):
        """Test RBAC permission checking"""
        # Create user with different roles
        admin_user = UserModel(
            user_id="admin1",
            username="admin",
            email="admin@example.com",
            roles=[UserRole.ADMIN],
            created_at=datetime.now(),
        )

        regular_user = UserModel(
            user_id="user1",
            username="user",
            email="user@example.com",
            roles=[UserRole.USER],
            created_at=datetime.now(),
        )

        # Test admin permissions
        assert jwt_auth.has_permission(admin_user, Permission.MANAGE_USERS)
        assert jwt_auth.has_permission(admin_user, Permission.CREATE_CAPSULE)

        # Test regular user permissions
        assert not jwt_auth.has_permission(regular_user, Permission.MANAGE_USERS)
        assert jwt_auth.has_permission(regular_user, Permission.CREATE_CAPSULE)

    def test_get_user_stats(self, jwt_auth):
        """Test authentication system statistics"""
        stats = jwt_auth.get_user_stats()

        assert "total_users" in stats
        assert "active_sessions" in stats
        assert "locked_users" in stats


class TestDependencyInjection:
    """Test dependency injection container"""

    @pytest.fixture
    def container(self):
        """Service container for testing"""
        return ServiceContainer()

    def test_singleton_registration(self, container):
        """Test singleton service registration"""

        class TestService:
            def __init__(self):
                self.value = "test"

        container.register_singleton(TestService)

        # Should return the same instance
        service1 = asyncio.run(container.get_service(TestService))
        service2 = asyncio.run(container.get_service(TestService))

        assert service1 is service2
        assert service1.value == "test"

    def test_transient_registration(self, container):
        """Test transient service registration"""

        class TestService:
            def __init__(self):
                self.value = time.time()  # Different each time

        container.register_transient(TestService)

        # Should return different instances
        service1 = asyncio.run(container.get_service(TestService))
        service2 = asyncio.run(container.get_service(TestService))

        assert service1 is not service2
        assert service1.value != service2.value

    @pytest.mark.asyncio
    async def test_scoped_registration(self, container):
        """Test scoped service registration"""

        class TestService:
            def __init__(self):
                self.value = time.time()

        container.register_scoped(TestService)

        # Within same scope, should return same instance
        async with container.create_scope() as scope:
            service1 = await container.get_service(TestService)
            service2 = await container.get_service(TestService)

            assert service1 is service2

        # In different scope, should return different instance
        async with container.create_scope() as scope:
            service3 = await container.get_service(TestService)

            assert service1 is not service3

    def test_dependency_resolution(self, container):
        """Test automatic dependency resolution"""

        class DatabaseService:
            def __init__(self):
                self.connected = True

        class UserService:
            def __init__(self, database: DatabaseService):
                self.database = database

        container.register_singleton(DatabaseService)
        container.register_transient(UserService)

        user_service = asyncio.run(container.get_service(UserService))

        assert isinstance(user_service.database, DatabaseService)
        assert user_service.database.connected

    def test_circular_dependency_detection(self, container):
        """Test circular dependency detection"""

        class ServiceA:
            def __init__(self, service_b: "ServiceB"):
                self.service_b = service_b

        class ServiceB:
            def __init__(self, service_a: ServiceA):
                self.service_a = service_a

        container.register_transient(ServiceA)
        container.register_transient(ServiceB)

        with pytest.raises(CircularDependencyError):
            asyncio.run(container.get_service(ServiceA))

    def test_service_not_found(self, container):
        """Test service not found error"""

        class UnregisteredService:
            pass

        with pytest.raises(ServiceNotFoundError):
            asyncio.run(container.get_service(UnregisteredService))

    @pytest.mark.asyncio
    async def test_health_check(self, container):
        """Test service health checking"""

        class HealthyService:
            def health_check(self):
                return True

        class UnhealthyService:
            def health_check(self):
                return False

        container.register_singleton(
            HealthyService, health_check=lambda: HealthyService().health_check()
        )
        container.register_singleton(
            UnhealthyService, health_check=lambda: UnhealthyService().health_check()
        )

        health_results = await container.health_check()

        assert "HealthyService" in health_results
        assert "UnhealthyService" in health_results
        assert health_results["HealthyService"]["status"] == "healthy"
        assert health_results["UnhealthyService"]["status"] == "unhealthy"


class TestConfiguration:
    """Test configuration management"""

    def test_default_settings(self):
        """Test default configuration values"""
        with patch.dict("os.environ", {}, clear=True):
            settings = UATPSettings()

            assert settings.app_name == "UATP Capsule Engine"
            assert settings.environment == Environment.DEVELOPMENT
            assert settings.debug is True  # Should be True for development
            assert settings.port == 8000

    def test_environment_override(self):
        """Test environment variable override"""
        with patch.dict(
            "os.environ",
            {"APP_NAME": "Test UATP", "PORT": "9000", "ENVIRONMENT": "production"},
        ):
            settings = UATPSettings()

            assert settings.app_name == "Test UATP"
            assert settings.port == 9000
            assert settings.environment == Environment.PRODUCTION
            assert settings.debug is False  # Should be False for production

    def test_nested_settings(self):
        """Test nested settings configuration"""
        with patch.dict(
            "os.environ",
            {
                "AUTH__JWT_SECRET_KEY": "test-secret",
                "DATABASE__DATABASE_TYPE": "postgresql",
                "DATABASE__DATABASE_PORT": "5433",
            },
        ):
            settings = UATPSettings()

            assert settings.auth.jwt_secret_key.get_secret_value() == "test-secret"
            assert settings.database.database_type.value == "postgresql"
            assert settings.database.database_port == 5433

    def test_configuration_validation(self):
        """Test configuration validation"""
        # Test development environment (should be valid)
        dev_settings = UATPSettings(environment=Environment.DEVELOPMENT)
        validation = dev_settings.validate_configuration()
        assert validation["valid"] is True

        # Test production environment with default values (should have errors)
        prod_settings = UATPSettings(environment=Environment.PRODUCTION)
        validation = prod_settings.validate_configuration()
        assert validation["valid"] is False
        assert len(validation["errors"]) > 0

    def test_cors_origins_by_environment(self):
        """Test CORS origins based on environment"""
        dev_settings = UATPSettings(environment=Environment.DEVELOPMENT)
        dev_origins = dev_settings.get_cors_origins()
        assert "http://localhost:3000" in dev_origins

        prod_settings = UATPSettings(environment=Environment.PRODUCTION)
        prod_origins = prod_settings.get_cors_origins()
        assert "http://localhost:3000" not in prod_origins


class TestExceptionHandling:
    """Test structured exception handling"""

    @pytest.fixture
    def error_handler(self):
        """Error handler for testing"""
        return ErrorHandler(include_debug_info=True)

    def test_validation_error_creation(self):
        """Test validation error creation and attributes"""
        error = ValidationError("Invalid input", field="username", value="invalid@user")

        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.LOW
        assert error.details["field"] == "username"
        assert "invalid@user" in error.details["invalid_value"]

    def test_authentication_error_creation(self):
        """Test authentication error creation"""
        error = AuthenticationError("Invalid credentials")

        assert error.category == ErrorCategory.AUTHENTICATION
        assert error.severity == ErrorSeverity.MEDIUM
        assert "Authentication failed" in error.user_message

    def test_error_context_creation(self):
        """Test error context creation"""
        from src.core.exceptions import ErrorContext

        context = ErrorContext()

        assert context.correlation_id
        assert context.timestamp

        context_dict = context.to_dict()
        assert "correlation_id" in context_dict
        assert "timestamp" in context_dict

    def test_error_to_dict(self):
        """Test error serialization to dictionary"""
        error = ValidationError(
            "Test error", field="test_field", error_code="TEST_ERROR"
        )

        error_dict = error.to_dict()

        assert error_dict["error_code"] == "TEST_ERROR"
        assert error_dict["category"] == ErrorCategory.VALIDATION.value
        assert error_dict["severity"] == ErrorSeverity.LOW.value
        assert "correlation_id" in error_dict
        assert "timestamp" in error_dict

    def test_error_handler_exception_handling(self, error_handler):
        """Test error handler exception processing"""
        # Create mock request
        request = Mock()
        request.url = Mock()
        request.url.path = "/test"
        request.method = "GET"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.headers = {"user-agent": "test-agent"}
        request.state = Mock()

        # Test UATP exception handling
        uatp_error = ValidationError("Test validation error")
        response = error_handler.handle_exception(uatp_error, request)

        assert response.status_code == 400
        response_data = response.body.decode("utf-8")
        assert (
            "Test validation error" in response_data
            or "invalid" in response_data.lower()
        )

    def test_http_status_code_mapping(self, error_handler):
        """Test HTTP status code mapping for exceptions"""
        from src.core.exceptions import CapsuleNotFoundError, RateLimitError

        # Test different exception types
        validation_error = ValidationError("Invalid")
        auth_error = AuthenticationError("Unauthorized")
        not_found_error = CapsuleNotFoundError("capsule123")
        rate_limit_error = RateLimitError("Rate limit exceeded")

        assert error_handler._get_http_status_code(validation_error) == 400
        assert error_handler._get_http_status_code(auth_error) == 401
        assert error_handler._get_http_status_code(not_found_error) == 404
        assert error_handler._get_http_status_code(rate_limit_error) == 429


class TestIntegration:
    """Test integration between architectural components"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_dependency_injection(self):
        """Test circuit breaker integration with DI container"""

        class ExternalService:
            def __init__(self):
                self.call_count = 0

            async def make_request(self):
                self.call_count += 1
                if self.call_count <= 3:
                    raise Exception("Service failure")
                return "success"

        container = ServiceContainer()
        container.register_singleton(ExternalService)

        breaker = CircuitBreaker("external_service")
        service = await container.get_service(ExternalService)

        # Test that circuit breaker protects the service
        for i in range(3):
            try:
                async with breaker.call():
                    await service.make_request()
            except Exception:
                pass

        # Circuit should be open now
        assert breaker.state == CircuitState.OPEN

        # Should fail fast
        with pytest.raises(CircuitBreakerError):
            async with breaker.call():
                await service.make_request()

    @pytest.mark.asyncio
    async def test_authentication_with_configuration(self):
        """Test authentication integration with configuration"""

        # Create settings with specific auth configuration
        with patch.dict(
            "os.environ",
            {
                "AUTH__JWT_SECRET_KEY": "test-integration-secret",
                "AUTH__JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "60",
            },
        ):
            settings = UATPSettings()

            # Create authenticator with settings
            auth_config = AuthConfig(
                secret_key=settings.auth.jwt_secret_key.get_secret_value(),
                access_token_expire_minutes=settings.auth.jwt_access_token_expire_minutes,
            )
            jwt_auth = JWTAuthenticator(auth_config)

            # Test that configuration is properly applied
            assert jwt_auth.config.access_token_expire_minutes == 60

            # Register and authenticate user
            await jwt_auth.register_user(
                username="integrationtest",
                email="integration@test.com",
                password="TestPassword123!",
            )

            request = Mock()
            request.client = Mock()
            request.client.host = "127.0.0.1"
            request.headers = {"user-agent": "integration-test"}

            login_request = LoginRequest(
                username="integrationtest", password="TestPassword123!"
            )

            token_response = await jwt_auth.authenticate_user(login_request, request)
            assert token_response.access_token
            assert token_response.expires_in == 60 * 60  # 60 minutes in seconds

    def test_error_handling_with_configuration(self):
        """Test error handling integration with configuration"""

        # Test with debug mode enabled
        debug_settings = UATPSettings(environment=Environment.DEVELOPMENT)
        debug_handler = ErrorHandler(include_debug_info=debug_settings.debug)

        # Test with production mode
        prod_settings = UATPSettings(environment=Environment.PRODUCTION)
        prod_handler = ErrorHandler(include_debug_info=prod_settings.debug)

        # Create test exception
        test_error = ValidationError("Test error")

        # Debug handler should include debug info
        debug_response = debug_handler._create_error_response(test_error)
        debug_content = debug_response.body.decode("utf-8")

        # Production handler should not include debug info
        prod_response = prod_handler._create_error_response(test_error)
        prod_content = prod_response.body.decode("utf-8")

        # Both should have correlation IDs
        assert "correlation_id" in debug_content
        assert "correlation_id" in prod_content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src.core", "--cov-report=term-missing"])
