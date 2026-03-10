"""
Role-Based Access Control (RBAC) Manager
=======================================

Production-grade RBAC system for managing user roles, permissions,
and access control throughout the UATP Capsule Engine.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from .models import (
    Permission,
    PermissionScope,
    Role,
    SystemRoles,
    User,
    UserRole,
    UserType,
)

logger = logging.getLogger(__name__)


@dataclass
class AccessContext:
    """Context information for access control decisions."""

    user_id: str
    resource_type: str
    resource_id: str
    action: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_context: Dict[str, Any] = None

    def __post_init__(self):
        if self.additional_context is None:
            self.additional_context = {}


@dataclass
class AccessDecision:
    """Result of an access control decision."""

    allowed: bool
    reason: str
    required_permissions: List[str]
    user_permissions: List[str]
    context: AccessContext


class RBACManager:
    """Role-Based Access Control manager."""

    def __init__(self):
        # In production, these would be loaded from database
        self._users: Dict[str, User] = {}
        self._roles: Dict[str, Role] = {}
        self._permissions: Dict[str, Permission] = {}
        self._user_roles: Dict[str, List[UserRole]] = {}

        # Cache for performance
        self._user_permissions_cache: Dict[str, Set[str]] = {}
        self._role_permissions_cache: Dict[str, Set[str]] = {}

        # Initialize system roles
        self._initialize_system_roles()

        logger.info("RBAC Manager initialized")

    def _initialize_system_roles(self):
        """Initialize system roles with default permissions."""
        system_roles = [
            SystemRoles.get_admin_role(),
            SystemRoles.get_agent_owner_role(),
            SystemRoles.get_financial_manager_role(),
            SystemRoles.get_compliance_officer_role(),
            SystemRoles.get_viewer_role(),
            SystemRoles.get_api_client_role(),
        ]

        for role in system_roles:
            self._roles[role.role_id] = role
            self._role_permissions_cache[role.role_id] = set(
                p.value for p in role.permissions
            )

        logger.info(f"Initialized {len(system_roles)} system roles")

    # User Management
    def add_user(self, user: User) -> bool:
        """Add a user to the RBAC system."""
        try:
            self._users[user.user_id] = user
            logger.info(f"Added user {user.username} ({user.user_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to add user {user.username}: {e}")
            return False

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self._users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    def update_user(self, user: User) -> bool:
        """Update user information."""
        try:
            if user.user_id not in self._users:
                logger.warning(f"User {user.user_id} not found for update")
                return False

            user.updated_at = datetime.now(timezone.utc)
            self._users[user.user_id] = user

            # Clear cache
            self._clear_user_cache(user.user_id)

            logger.info(f"Updated user {user.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to update user {user.username}: {e}")
            return False

    # Role Management
    def add_role(self, role: Role) -> bool:
        """Add a role to the system."""
        try:
            self._roles[role.role_id] = role
            self._role_permissions_cache[role.role_id] = set(
                p.value for p in role.permissions
            )
            logger.info(f"Added role {role.name} ({role.role_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to add role {role.name}: {e}")
            return False

    def get_role(self, role_id: str) -> Optional[Role]:
        """Get role by ID."""
        return self._roles.get(role_id)

    def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        for role in self._roles.values():
            if role.name == name:
                return role
        return None

    def update_role(self, role: Role) -> bool:
        """Update role information."""
        try:
            if role.role_id not in self._roles:
                logger.warning(f"Role {role.role_id} not found for update")
                return False

            role.updated_at = datetime.now(timezone.utc)
            self._roles[role.role_id] = role
            self._role_permissions_cache[role.role_id] = set(
                p.value for p in role.permissions
            )

            # Clear user caches for all users with this role
            self._clear_role_cache(role.role_id)

            logger.info(f"Updated role {role.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update role {role.name}: {e}")
            return False

    # User-Role Assignment
    def assign_role_to_user(
        self,
        user_id: str,
        role_id: str,
        assigned_by: str,
        expires_at: Optional[datetime] = None,
    ) -> bool:
        """Assign a role to a user."""
        try:
            if user_id not in self._users:
                logger.warning(f"User {user_id} not found")
                return False

            if role_id not in self._roles:
                logger.warning(f"Role {role_id} not found")
                return False

            # Check if assignment already exists
            user_roles = self._user_roles.get(user_id, [])
            for user_role in user_roles:
                if user_role.role_id == role_id and user_role.is_active:
                    logger.warning(f"Role {role_id} already assigned to user {user_id}")
                    return False

            # Create assignment
            assignment = UserRole(
                assignment_id=f"{user_id}_{role_id}_{datetime.now().timestamp()}",
                user_id=user_id,
                role_id=role_id,
                assigned_at=datetime.now(timezone.utc),
                assigned_by=assigned_by,
                expires_at=expires_at,
            )

            if user_id not in self._user_roles:
                self._user_roles[user_id] = []
            self._user_roles[user_id].append(assignment)

            # Clear cache
            self._clear_user_cache(user_id)

            logger.info(f"Assigned role {role_id} to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to assign role {role_id} to user {user_id}: {e}")
            return False

    def revoke_role_from_user(self, user_id: str, role_id: str) -> bool:
        """Revoke a role from a user."""
        try:
            user_roles = self._user_roles.get(user_id, [])

            for user_role in user_roles:
                if user_role.role_id == role_id and user_role.is_active:
                    user_role.is_active = False

                    # Clear cache
                    self._clear_user_cache(user_id)

                    logger.info(f"Revoked role {role_id} from user {user_id}")
                    return True

            logger.warning(f"Active role {role_id} not found for user {user_id}")
            return False

        except Exception as e:
            logger.error(f"Failed to revoke role {role_id} from user {user_id}: {e}")
            return False

    def get_user_roles(self, user_id: str) -> List[Role]:
        """Get all active roles for a user."""
        user_roles = self._user_roles.get(user_id, [])
        active_roles = []

        for user_role in user_roles:
            if user_role.is_active and not user_role.is_expired:
                role = self._roles.get(user_role.role_id)
                if role:
                    active_roles.append(role)

        return active_roles

    # Permission Management
    def get_user_permissions(self, user_id: str) -> Set[str]:
        """Get all permissions for a user (from all assigned roles)."""
        # Check cache first
        if user_id in self._user_permissions_cache:
            return self._user_permissions_cache[user_id]

        permissions = set()
        user_roles = self.get_user_roles(user_id)

        for role in user_roles:
            permissions.update(p.value for p in role.permissions)

        # Cache the result
        self._user_permissions_cache[user_id] = permissions
        return permissions

    def has_permission(self, user_id: str, permission: PermissionScope) -> bool:
        """Check if user has a specific permission."""
        user_permissions = self.get_user_permissions(user_id)
        return permission.value in user_permissions

    def has_any_permission(
        self, user_id: str, permissions: List[PermissionScope]
    ) -> bool:
        """Check if user has any of the specified permissions."""
        user_permissions = self.get_user_permissions(user_id)
        required_permissions = set(p.value for p in permissions)
        return bool(user_permissions.intersection(required_permissions))

    def has_all_permissions(
        self, user_id: str, permissions: List[PermissionScope]
    ) -> bool:
        """Check if user has all of the specified permissions."""
        user_permissions = self.get_user_permissions(user_id)
        required_permissions = set(p.value for p in permissions)
        return required_permissions.issubset(user_permissions)

    # Access Control
    def check_access(self, context: AccessContext) -> AccessDecision:
        """Comprehensive access control check."""
        user = self.get_user(context.user_id)
        if not user:
            return AccessDecision(
                allowed=False,
                reason="User not found",
                required_permissions=[],
                user_permissions=[],
                context=context,
            )

        if not user.is_active:
            return AccessDecision(
                allowed=False,
                reason="User account is inactive",
                required_permissions=[],
                user_permissions=[],
                context=context,
            )

        if user.is_locked:
            return AccessDecision(
                allowed=False,
                reason="User account is locked",
                required_permissions=[],
                user_permissions=[],
                context=context,
            )

        # Get user permissions
        user_permissions = list(self.get_user_permissions(context.user_id))

        # Determine required permissions based on resource and action
        required_permissions = self._get_required_permissions(
            context.resource_type, context.action
        )

        # Check permissions
        has_required_permissions = all(
            perm in user_permissions for perm in required_permissions
        )

        if not has_required_permissions:
            return AccessDecision(
                allowed=False,
                reason="Insufficient permissions",
                required_permissions=required_permissions,
                user_permissions=user_permissions,
                context=context,
            )

        # Additional context-based checks
        if not self._check_resource_access(context, user):
            return AccessDecision(
                allowed=False,
                reason="Resource access denied",
                required_permissions=required_permissions,
                user_permissions=user_permissions,
                context=context,
            )

        return AccessDecision(
            allowed=True,
            reason="Access granted",
            required_permissions=required_permissions,
            user_permissions=user_permissions,
            context=context,
        )

    def _get_required_permissions(self, resource_type: str, action: str) -> List[str]:
        """Get required permissions for a resource and action."""
        permission_map = {
            "agents": {
                "create": [PermissionScope.AGENTS_CREATE.value],
                "read": [PermissionScope.AGENTS_READ.value],
                "update": [PermissionScope.AGENTS_UPDATE.value],
                "delete": [PermissionScope.AGENTS_DELETE.value],
            },
            "citizenship": {
                "create": [PermissionScope.CITIZENSHIP_CREATE.value],
                "read": [PermissionScope.CITIZENSHIP_READ.value],
                "update": [PermissionScope.CITIZENSHIP_UPDATE.value],
                "revoke": [PermissionScope.CITIZENSHIP_REVOKE.value],
                "assess": [PermissionScope.CITIZENSHIP_ASSESS.value],
            },
            "bonds": {
                "create": [PermissionScope.BONDS_CREATE.value],
                "read": [PermissionScope.BONDS_READ.value],
                "update": [PermissionScope.BONDS_UPDATE.value],
                "cancel": [PermissionScope.BONDS_CANCEL.value],
            },
            "payments": {
                "process": [PermissionScope.PAYMENTS_PROCESS.value],
                "read": [PermissionScope.PAYMENTS_READ.value],
            },
        }

        return permission_map.get(resource_type, {}).get(action, [])

    def _check_resource_access(self, context: AccessContext, user: User) -> bool:
        """Additional resource-specific access checks."""
        # Admin users have access to everything
        if user.user_type == UserType.ADMIN:
            return True

        # Resource-specific checks would go here
        # For example, checking if user owns the agent, citizenship, etc.
        # This would typically involve database queries

        return True

    # Cache Management
    def _clear_user_cache(self, user_id: str):
        """Clear cache for a specific user."""
        self._user_permissions_cache.pop(user_id, None)

    def _clear_role_cache(self, role_id: str):
        """Clear cache for all users with a specific role."""
        # Find all users with this role and clear their cache
        for user_id, user_roles in self._user_roles.items():
            for user_role in user_roles:
                if user_role.role_id == role_id and user_role.is_active:
                    self._clear_user_cache(user_id)
                    break

    def clear_all_cache(self):
        """Clear all permission caches."""
        self._user_permissions_cache.clear()
        logger.info("Cleared all RBAC caches")

    # Utility Methods
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get RBAC system statistics."""
        total_users = len(self._users)
        active_users = sum(1 for user in self._users.values() if user.is_active)
        total_roles = len(self._roles)
        total_assignments = sum(
            len(assignments) for assignments in self._user_roles.values()
        )
        active_assignments = sum(
            sum(
                1
                for assignment in assignments
                if assignment.is_active and not assignment.is_expired
            )
            for assignments in self._user_roles.values()
        )

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_roles": total_roles,
            "total_assignments": total_assignments,
            "active_assignments": active_assignments,
            "cache_size": len(self._user_permissions_cache),
        }


# Global RBAC manager instance
_global_rbac_manager: Optional[RBACManager] = None


def get_rbac_manager() -> RBACManager:
    """Get the global RBAC manager instance."""
    global _global_rbac_manager
    if _global_rbac_manager is None:
        _global_rbac_manager = RBACManager()
    return _global_rbac_manager


def check_permission(user_id: str, permission: PermissionScope) -> bool:
    """Convenience function to check user permission."""
    rbac = get_rbac_manager()
    return rbac.has_permission(user_id, permission)


def check_access(
    user_id: str, resource_type: str, resource_id: str, action: str, **kwargs
) -> AccessDecision:
    """Convenience function for access control check."""
    context = AccessContext(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        **kwargs,
    )
    rbac = get_rbac_manager()
    return rbac.check_access(context)
