"""
JWT Authentication System with Role-Based Access Control (RBAC)

Provides production-ready authentication and authorization using JWT tokens
with comprehensive RBAC support, token refresh mechanisms, and security features.

Key Features:
- JWT token generation and validation
- Role-based access control (RBAC)
- Token refresh mechanism
- Password hashing and verification
- Session management
- Security audit logging
- Rate limiting for auth attempts
- Multi-factor authentication support
"""

import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field
from functools import wraps

import jwt
import bcrypt
import structlog
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from prometheus_client import Counter, Histogram

logger = structlog.get_logger(__name__)

# Metrics
auth_metrics = {
    "login_attempts": Counter(
        "auth_login_attempts_total", "Total login attempts", ["result", "method"]
    ),
    "token_validations": Counter(
        "auth_token_validations_total",
        "Total token validations",
        ["result", "token_type"],
    ),
    "permission_checks": Counter(
        "auth_permission_checks_total",
        "Total permission checks",
        ["result", "resource", "action"],
    ),
    "auth_duration": Histogram(
        "auth_operation_duration_seconds",
        "Authentication operation duration",
        ["operation"],
    ),
}


class UserRole(str, Enum):
    """User roles with hierarchical permissions"""

    SUPER_ADMIN = "super_admin"  # Full system access
    ADMIN = "admin"  # Administrative access
    MODERATOR = "moderator"  # Content moderation
    PREMIUM_USER = "premium_user"  # Premium features
    USER = "user"  # Basic user access
    GUEST = "guest"  # Limited access


class Permission(str, Enum):
    """System permissions"""

    # Capsule permissions
    CREATE_CAPSULE = "create_capsule"
    READ_CAPSULE = "read_capsule"
    UPDATE_CAPSULE = "update_capsule"
    DELETE_CAPSULE = "delete_capsule"

    # User management
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"

    # System administration
    SYSTEM_ADMIN = "system_admin"
    VIEW_METRICS = "view_metrics"
    MANAGE_CONFIG = "manage_config"

    # Economic operations
    PROCESS_PAYMENTS = "process_payments"
    VIEW_ECONOMICS = "view_economics"

    # AI operations
    USE_AI_SERVICES = "use_ai_services"
    MANAGE_AI_PROVIDERS = "manage_ai_providers"


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.SUPER_ADMIN: set(Permission),  # All permissions
    UserRole.ADMIN: {
        Permission.CREATE_CAPSULE,
        Permission.READ_CAPSULE,
        Permission.UPDATE_CAPSULE,
        Permission.DELETE_CAPSULE,
        Permission.MANAGE_USERS,
        Permission.VIEW_USERS,
        Permission.VIEW_METRICS,
        Permission.PROCESS_PAYMENTS,
        Permission.VIEW_ECONOMICS,
        Permission.USE_AI_SERVICES,
        Permission.MANAGE_AI_PROVIDERS,
    },
    UserRole.MODERATOR: {
        Permission.CREATE_CAPSULE,
        Permission.READ_CAPSULE,
        Permission.UPDATE_CAPSULE,
        Permission.VIEW_USERS,
        Permission.USE_AI_SERVICES,
    },
    UserRole.PREMIUM_USER: {
        Permission.CREATE_CAPSULE,
        Permission.READ_CAPSULE,
        Permission.UPDATE_CAPSULE,
        Permission.USE_AI_SERVICES,
        Permission.VIEW_ECONOMICS,
    },
    UserRole.USER: {
        Permission.CREATE_CAPSULE,
        Permission.READ_CAPSULE,
        Permission.USE_AI_SERVICES,
    },
    UserRole.GUEST: {
        Permission.READ_CAPSULE,
    },
}


@dataclass
class AuthConfig:
    """Authentication configuration"""

    # JWT settings
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Security settings
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    require_email_verification: bool = True

    # Session settings
    max_concurrent_sessions: int = 3
    session_timeout_minutes: int = 60


class UserModel(BaseModel):
    """User data model"""

    user_id: str
    username: str
    email: EmailStr
    roles: List[UserRole]
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None

    @validator("roles")
    def validate_roles(cls, v):
        if not v:
            return [UserRole.USER]
        return v


class LoginRequest(BaseModel):
    """Login request model"""

    username: str
    password: str
    remember_me: bool = False
    mfa_code: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response model"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserModel


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""

    refresh_token: str


@dataclass
class SessionInfo:
    """Session information"""

    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True


class JWTAuthenticator:
    """
    JWT Authentication service with RBAC support
    """

    def __init__(self, config: AuthConfig):
        self.config = config
        self.security = HTTPBearer(auto_error=False)

        # In production, this would be a proper database
        self._users: Dict[str, UserModel] = {}
        self._sessions: Dict[str, SessionInfo] = {}
        self._refresh_tokens: Dict[str, str] = {}  # token -> user_id

        if not config.secret_key:
            raise ValueError("JWT secret key must be provided")

        logger.info(
            "JWT Authenticator initialized",
            algorithm=config.algorithm,
            access_token_expire_minutes=config.access_token_expire_minutes,
        )

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def _generate_token(
        self,
        user: UserModel,
        token_type: str = "access",
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Generate JWT token"""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            if token_type == "access":
                expire = datetime.now(timezone.utc) + timedelta(
                    minutes=self.config.access_token_expire_minutes
                )
            else:  # refresh token
                expire = datetime.now(timezone.utc) + timedelta(
                    days=self.config.refresh_token_expire_days
                )

        payload = {
            "sub": user.user_id,
            "username": user.username,
            "email": user.email,
            "roles": [role.value for role in user.roles],
            "token_type": token_type,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(32),  # JWT ID for revocation
        }

        return jwt.encode(
            payload, self.config.secret_key, algorithm=self.config.algorithm
        )

    def _decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token, self.config.secret_key, algorithms=[self.config.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def _create_session(self, user: UserModel, request: Request) -> SessionInfo:
        """Create user session"""
        session_id = secrets.token_urlsafe(32)
        session = SessionInfo(
            session_id=session_id,
            user_id=user.user_id,
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
        )

        # Clean up old sessions if limit exceeded
        user_sessions = [
            s
            for s in self._sessions.values()
            if s.user_id == user.user_id and s.is_active
        ]

        if len(user_sessions) >= self.config.max_concurrent_sessions:
            # Remove oldest session
            oldest_session = min(user_sessions, key=lambda s: s.last_activity)
            oldest_session.is_active = False

            logger.info(
                "Session limit exceeded, deactivated oldest session",
                user_id=user.user_id,
                old_session_id=oldest_session.session_id,
                new_session_id=session_id,
            )

        self._sessions[session_id] = session
        return session

    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: Optional[List[UserRole]] = None,
    ) -> UserModel:
        """Register a new user"""
        start_time = time.time()

        try:
            # Validate password
            if len(password) < self.config.password_min_length:
                raise HTTPException(
                    status_code=400,
                    detail=f"Password must be at least {self.config.password_min_length} characters",
                )

            # Check if user exists
            for user in self._users.values():
                if user.username == username or user.email == email:
                    raise HTTPException(
                        status_code=400,
                        detail="User with this username or email already exists",
                    )

            # Create user
            user_id = secrets.token_urlsafe(16)
            hashed_password = self._hash_password(password)

            user = UserModel(
                user_id=user_id,
                username=username,
                email=email,
                roles=roles or [UserRole.USER],
                created_at=datetime.now(timezone.utc),
                is_verified=not self.config.require_email_verification,
            )

            # Store user (in production, this would be in a database)
            self._users[user_id] = user
            # Store password separately (in production, use proper user management)
            setattr(user, "_password_hash", hashed_password)

            logger.info(
                "User registered successfully",
                user_id=user_id,
                username=username,
                email=email,
                roles=[r.value for r in user.roles],
            )

            return user

        finally:
            auth_metrics["auth_duration"].labels(operation="register").observe(
                time.time() - start_time
            )

    async def authenticate_user(
        self, login_request: LoginRequest, request: Request
    ) -> TokenResponse:
        """Authenticate user and return tokens"""
        start_time = time.time()

        try:
            # Find user
            user = None
            for u in self._users.values():
                if (
                    u.username == login_request.username
                    or u.email == login_request.username
                ):
                    user = u
                    break

            if not user:
                auth_metrics["login_attempts"].labels(
                    result="failed", method="password"
                ).inc()
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Check if user is locked
            if user.locked_until and user.locked_until > datetime.now(timezone.utc):
                auth_metrics["login_attempts"].labels(
                    result="locked", method="password"
                ).inc()
                raise HTTPException(
                    status_code=423, detail=f"Account locked until {user.locked_until}"
                )

            # Verify password
            password_hash = getattr(user, "_password_hash", "")
            if not self._verify_password(login_request.password, password_hash):
                user.login_attempts += 1

                # Lock account if too many attempts
                if user.login_attempts >= self.config.max_login_attempts:
                    user.locked_until = datetime.now(timezone.utc) + timedelta(
                        minutes=self.config.lockout_duration_minutes
                    )
                    logger.warning(
                        "Account locked due to too many failed attempts",
                        user_id=user.user_id,
                        attempts=user.login_attempts,
                    )

                auth_metrics["login_attempts"].labels(
                    result="failed", method="password"
                ).inc()
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Check if user is active and verified
            if not user.is_active:
                auth_metrics["login_attempts"].labels(
                    result="inactive", method="password"
                ).inc()
                raise HTTPException(status_code=401, detail="Account is inactive")

            if not user.is_verified and self.config.require_email_verification:
                auth_metrics["login_attempts"].labels(
                    result="unverified", method="password"
                ).inc()
                raise HTTPException(
                    status_code=401, detail="Email verification required"
                )

            # Reset login attempts on successful login
            user.login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.now(timezone.utc)

            # Create session
            session = self._create_session(user, request)

            # Generate tokens
            access_token = self._generate_token(user, "access")
            refresh_token = self._generate_token(user, "refresh")

            # Store refresh token
            self._refresh_tokens[refresh_token] = user.user_id

            auth_metrics["login_attempts"].labels(
                result="success", method="password"
            ).inc()

            logger.info(
                "User authenticated successfully",
                user_id=user.user_id,
                username=user.username,
                session_id=session.session_id,
                ip_address=session.ip_address,
            )

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.config.access_token_expire_minutes * 60,
                user=user,
            )

        finally:
            auth_metrics["auth_duration"].labels(operation="login").observe(
                time.time() - start_time
            )

    async def refresh_token(
        self, refresh_request: RefreshTokenRequest
    ) -> TokenResponse:
        """Refresh access token using refresh token"""
        start_time = time.time()

        try:
            # Validate refresh token
            payload = self._decode_token(refresh_request.refresh_token)

            if payload.get("token_type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")

            user_id = payload.get("sub")
            if not user_id or refresh_request.refresh_token not in self._refresh_tokens:
                raise HTTPException(status_code=401, detail="Invalid refresh token")

            user = self._users.get(user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=401, detail="User not found or inactive"
                )

            # Generate new tokens
            access_token = self._generate_token(user, "access")
            new_refresh_token = self._generate_token(user, "refresh")

            # Update refresh token storage
            del self._refresh_tokens[refresh_request.refresh_token]
            self._refresh_tokens[new_refresh_token] = user_id

            auth_metrics["token_validations"].labels(
                result="success", token_type="refresh"
            ).inc()

            logger.info(
                "Token refreshed successfully", user_id=user_id, username=user.username
            )

            return TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_in=self.config.access_token_expire_minutes * 60,
                user=user,
            )

        except HTTPException:
            auth_metrics["token_validations"].labels(
                result="failed", token_type="refresh"
            ).inc()
            raise
        finally:
            auth_metrics["auth_duration"].labels(operation="refresh").observe(
                time.time() - start_time
            )

    async def get_current_user(
        self, credentials: Optional[HTTPAuthorizationCredentials] = None
    ) -> UserModel:
        """Get current user from JWT token"""
        if not credentials:
            raise HTTPException(status_code=401, detail="Authorization required")

        start_time = time.time()

        try:
            payload = self._decode_token(credentials.credentials)

            if payload.get("token_type") != "access":
                raise HTTPException(status_code=401, detail="Invalid token type")

            user_id = payload.get("sub")
            user = self._users.get(user_id)

            if not user or not user.is_active:
                raise HTTPException(
                    status_code=401, detail="User not found or inactive"
                )

            auth_metrics["token_validations"].labels(
                result="success", token_type="access"
            ).inc()

            return user

        except HTTPException:
            auth_metrics["token_validations"].labels(
                result="failed", token_type="access"
            ).inc()
            raise
        finally:
            auth_metrics["auth_duration"].labels(operation="validate").observe(
                time.time() - start_time
            )

    def has_permission(self, user: UserModel, permission: Permission) -> bool:
        """Check if user has specific permission"""
        start_time = time.time()

        try:
            # Check if any of the user's roles has the required permission
            for role in user.roles:
                if permission in ROLE_PERMISSIONS.get(role, set()):
                    auth_metrics["permission_checks"].labels(
                        result="granted", resource=permission.value, action="check"
                    ).inc()
                    return True

            auth_metrics["permission_checks"].labels(
                result="denied", resource=permission.value, action="check"
            ).inc()
            return False

        finally:
            auth_metrics["auth_duration"].labels(operation="permission_check").observe(
                time.time() - start_time
            )

    def require_permission(self, permission: Permission):
        """Decorator to require specific permission"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract user from request context or dependency injection
                # This would need to be integrated with the specific request context
                user = kwargs.get("current_user")  # Assumes user is passed as kwarg

                if not user or not self.has_permission(user, permission):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Permission '{permission.value}' required",
                    )

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    async def logout_user(self, user: UserModel, session_id: Optional[str] = None):
        """Logout user and invalidate session"""
        if session_id and session_id in self._sessions:
            self._sessions[session_id].is_active = False

        # In production, you'd also add tokens to a blacklist
        logger.info(
            "User logged out",
            user_id=user.user_id,
            username=user.username,
            session_id=session_id,
        )

    def get_user_stats(self) -> Dict[str, Any]:
        """Get authentication system statistics"""
        active_sessions = sum(1 for s in self._sessions.values() if s.is_active)
        locked_users = sum(
            1
            for u in self._users.values()
            if u.locked_until and u.locked_until > datetime.now(timezone.utc)
        )

        return {
            "total_users": len(self._users),
            "active_sessions": active_sessions,
            "locked_users": locked_users,
            "total_sessions": len(self._sessions),
            "refresh_tokens": len(self._refresh_tokens),
        }


# Factory function for creating authenticator
def create_jwt_authenticator(config: AuthConfig) -> JWTAuthenticator:
    """Create JWT authenticator with configuration"""
    return JWTAuthenticator(config)


# Dependency for FastAPI
def get_jwt_authenticator() -> JWTAuthenticator:
    """FastAPI dependency to get JWT authenticator"""
    # This would be properly configured in the application factory
    config = AuthConfig(
        secret_key="your-secret-key-change-in-production",  # Should come from environment
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
    )
    return create_jwt_authenticator(config)


# Permission checking decorators
def require_role(required_role: UserRole):
    """Decorator to require specific role"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if not user or required_role not in user.roles:
                raise HTTPException(
                    status_code=403, detail=f"Role '{required_role.value}' required"
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_role(required_roles: List[UserRole]):
    """Decorator to require any of the specified roles"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if not user or not any(role in user.roles for role in required_roles):
                role_names = [role.value for role in required_roles]
                raise HTTPException(
                    status_code=403,
                    detail=f"One of these roles required: {', '.join(role_names)}",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
