"""
Authentication Models
====================

User authentication and authorization models with role-based access control.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    DELETED = "deleted"


class UserType(str, Enum):
    ADMIN = "admin"
    AGENT_OWNER = "agent_owner"
    FINANCIAL_MANAGER = "financial_manager"
    COMPLIANCE_OFFICER = "compliance_officer"
    VIEWER = "viewer"
    API_CLIENT = "api_client"


class PermissionScope(str, Enum):
    # Agent management
    AGENTS_CREATE = "agents:create"
    AGENTS_READ = "agents:read"
    AGENTS_UPDATE = "agents:update"
    AGENTS_DELETE = "agents:delete"

    # Citizenship management
    CITIZENSHIP_CREATE = "citizenship:create"
    CITIZENSHIP_READ = "citizenship:read"
    CITIZENSHIP_UPDATE = "citizenship:update"
    CITIZENSHIP_REVOKE = "citizenship:revoke"
    CITIZENSHIP_ASSESS = "citizenship:assess"

    # Financial operations
    BONDS_CREATE = "bonds:create"
    BONDS_READ = "bonds:read"
    BONDS_UPDATE = "bonds:update"
    BONDS_CANCEL = "bonds:cancel"
    PAYMENTS_PROCESS = "payments:process"
    PAYMENTS_READ = "payments:read"
    ASSETS_REGISTER = "assets:register"
    ASSETS_UPDATE = "assets:update"

    # Compliance and risk
    COMPLIANCE_READ = "compliance:read"
    COMPLIANCE_REVIEW = "compliance:review"
    RISK_ASSESS = "risk:assess"
    AUDIT_READ = "audit:read"

    # Workflow management
    WORKFLOWS_EXECUTE = "workflows:execute"
    WORKFLOWS_MONITOR = "workflows:monitor"
    WORKFLOWS_ADMIN = "workflows:admin"

    # System administration
    SYSTEM_ADMIN = "system:admin"
    USER_MANAGEMENT = "users:manage"
    ANALYTICS_READ = "analytics:read"

    # API access
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"


@dataclass
class User:
    """User entity for authentication."""

    user_id: str
    username: str
    email: str
    full_name: str
    user_type: UserType
    status: UserStatus
    created_at: datetime
    updated_at: datetime

    # Authentication
    password_hash: str
    email_verified: bool = False
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

    # Profile
    profile_data: Dict[str, Any] = None
    preferences: Dict[str, Any] = None

    # Security
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.profile_data is None:
            self.profile_data = {}
        if self.preferences is None:
            self.preferences = {}
        if self.metadata is None:
            self.metadata = {}

    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    def lock_account(self, duration_minutes: int = 30):
        """Lock the user account for specified duration."""
        self.locked_until = datetime.now(timezone.utc) + timedelta(
            minutes=duration_minutes
        )
        self.status = UserStatus.SUSPENDED

    def unlock_account(self):
        """Unlock the user account."""
        self.locked_until = None
        self.failed_login_attempts = 0
        if self.status == UserStatus.SUSPENDED:
            self.status = UserStatus.ACTIVE


@dataclass
class Role:
    """Role entity for RBAC."""

    role_id: str
    name: str
    description: str
    permissions: List[PermissionScope]
    created_at: datetime
    updated_at: datetime

    # Role properties
    is_system_role: bool = False
    is_active: bool = True

    # Metadata
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def has_permission(self, permission: PermissionScope) -> bool:
        """Check if role has specific permission."""
        return permission in self.permissions

    def add_permission(self, permission: PermissionScope):
        """Add permission to role."""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.now(timezone.utc)

    def remove_permission(self, permission: PermissionScope):
        """Remove permission from role."""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.now(timezone.utc)


@dataclass
class Permission:
    """Permission entity."""

    permission_id: str
    scope: PermissionScope
    name: str
    description: str
    resource_type: str
    created_at: datetime

    # Permission properties
    is_system_permission: bool = False

    # Metadata
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UserRole:
    """User-Role assignment entity."""

    assignment_id: str
    user_id: str
    role_id: str
    assigned_at: datetime
    assigned_by: str

    # Assignment properties
    is_active: bool = True
    expires_at: Optional[datetime] = None

    # Context
    assignment_context: Dict[str, Any] = None

    def __post_init__(self):
        if self.assignment_context is None:
            self.assignment_context = {}

    @property
    def is_expired(self) -> bool:
        """Check if role assignment is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


@dataclass
class APIKey:
    """API key entity for service authentication."""

    key_id: str
    name: str
    key_hash: str
    user_id: Optional[str]
    scopes: List[PermissionScope]
    created_at: datetime

    # API key properties
    is_active: bool = True

    # Expiration
    expires_at: Optional[datetime] = None

    # Usage tracking
    last_used: Optional[datetime] = None
    usage_count: int = 0
    rate_limit: int = 1000  # per hour

    # Metadata
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def is_expired(self) -> bool:
        """Check if API key is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def has_scope(self, scope: PermissionScope) -> bool:
        """Check if API key has specific scope."""
        return scope in self.scopes

    def record_usage(self):
        """Record API key usage."""
        self.last_used = datetime.now(timezone.utc)
        self.usage_count += 1


@dataclass
class LoginSession:
    """User login session entity."""

    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime

    # Session properties
    is_active: bool = True
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Security
    refresh_token_hash: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def extend_session(self, duration_hours: int = 24):
        """Extend session expiration."""
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        self.last_activity = datetime.now(timezone.utc)

    def invalidate(self):
        """Invalidate the session."""
        self.is_active = False


# Predefined system roles
class SystemRoles:
    """Predefined system roles with standard permissions."""

    @staticmethod
    def get_admin_role() -> Role:
        """Get admin role with full permissions."""
        return Role(
            role_id="system_admin",
            name="System Administrator",
            description="Full system access with all permissions",
            permissions=list(PermissionScope),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_system_role=True,
        )

    @staticmethod
    def get_agent_owner_role() -> Role:
        """Get agent owner role for AI agent management."""
        return Role(
            role_id="agent_owner",
            name="Agent Owner",
            description="Manage AI agents, assets, and financial operations",
            permissions=[
                PermissionScope.AGENTS_CREATE,
                PermissionScope.AGENTS_READ,
                PermissionScope.AGENTS_UPDATE,
                PermissionScope.CITIZENSHIP_CREATE,
                PermissionScope.CITIZENSHIP_READ,
                PermissionScope.BONDS_CREATE,
                PermissionScope.BONDS_READ,
                PermissionScope.BONDS_UPDATE,
                PermissionScope.PAYMENTS_READ,
                PermissionScope.ASSETS_REGISTER,
                PermissionScope.ASSETS_UPDATE,
                PermissionScope.WORKFLOWS_EXECUTE,
                PermissionScope.ANALYTICS_READ,
                PermissionScope.API_READ,
                PermissionScope.API_WRITE,
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_system_role=True,
        )

    @staticmethod
    def get_financial_manager_role() -> Role:
        """Get financial manager role for financial operations."""
        return Role(
            role_id="financial_manager",
            name="Financial Manager",
            description="Manage financial operations, bonds, and payments",
            permissions=[
                PermissionScope.BONDS_READ,
                PermissionScope.BONDS_UPDATE,
                PermissionScope.BONDS_CANCEL,
                PermissionScope.PAYMENTS_PROCESS,
                PermissionScope.PAYMENTS_READ,
                PermissionScope.ASSETS_UPDATE,
                PermissionScope.COMPLIANCE_READ,
                PermissionScope.RISK_ASSESS,
                PermissionScope.ANALYTICS_READ,
                PermissionScope.API_READ,
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_system_role=True,
        )

    @staticmethod
    def get_compliance_officer_role() -> Role:
        """Get compliance officer role for compliance and risk management."""
        return Role(
            role_id="compliance_officer",
            name="Compliance Officer",
            description="Manage compliance, risk assessment, and auditing",
            permissions=[
                PermissionScope.AGENTS_READ,
                PermissionScope.CITIZENSHIP_READ,
                PermissionScope.CITIZENSHIP_ASSESS,
                PermissionScope.CITIZENSHIP_REVOKE,
                PermissionScope.BONDS_READ,
                PermissionScope.PAYMENTS_READ,
                PermissionScope.COMPLIANCE_READ,
                PermissionScope.COMPLIANCE_REVIEW,
                PermissionScope.RISK_ASSESS,
                PermissionScope.AUDIT_READ,
                PermissionScope.WORKFLOWS_MONITOR,
                PermissionScope.ANALYTICS_READ,
                PermissionScope.API_READ,
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_system_role=True,
        )

    @staticmethod
    def get_viewer_role() -> Role:
        """Get viewer role with read-only access."""
        return Role(
            role_id="viewer",
            name="Viewer",
            description="Read-only access to system data",
            permissions=[
                PermissionScope.AGENTS_READ,
                PermissionScope.CITIZENSHIP_READ,
                PermissionScope.BONDS_READ,
                PermissionScope.PAYMENTS_READ,
                PermissionScope.COMPLIANCE_READ,
                PermissionScope.ANALYTICS_READ,
                PermissionScope.API_READ,
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_system_role=True,
        )

    @staticmethod
    def get_api_client_role() -> Role:
        """Get API client role for programmatic access."""
        return Role(
            role_id="api_client",
            name="API Client",
            description="Programmatic API access with limited permissions",
            permissions=[
                PermissionScope.AGENTS_READ,
                PermissionScope.CITIZENSHIP_READ,
                PermissionScope.BONDS_READ,
                PermissionScope.PAYMENTS_READ,
                PermissionScope.API_READ,
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_system_role=True,
        )


# Helper functions
def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)
