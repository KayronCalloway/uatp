"""
User Service for UATP Authentication and User Management.

Provides user authentication, profile management, and permission checking
for the governance and economic systems.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class User:
    """A user in the UATP system."""

    user_id: str
    username: str
    email: str
    full_name: str
    roles: Set[str]
    permissions: Set[str]
    created_at: datetime
    last_active: datetime
    is_active: bool = True
    reputation_score: float = 0.5
    governance_stake: float = 0.0


class UserService:
    """Service for managing users in the UATP system."""

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.username_to_id: Dict[str, str] = {}
        logger.info(" User Service initialized")

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        user_id = self.username_to_id.get(username)
        if user_id:
            return self.users.get(user_id)
        return None

    def create_user(
        self,
        user_id: str,
        username: str,
        email: str,
        full_name: str,
        roles: Set[str] = None,
        permissions: Set[str] = None,
    ) -> User:
        """Create a new user."""

        if user_id in self.users:
            raise ValueError(f"User {user_id} already exists")

        if username in self.username_to_id:
            raise ValueError(f"Username {username} already taken")

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            full_name=full_name,
            roles=roles or set(),
            permissions=permissions or set(),
            created_at=datetime.now(timezone.utc),
            last_active=datetime.now(timezone.utc),
        )

        self.users[user_id] = user
        self.username_to_id[username] = user_id

        logger.info(f" Created user: {username} ({user_id})")
        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password."""
        # In a real implementation, this would verify the password hash
        # For now, return the user if they exist
        user = self.get_user_by_username(username)
        if user and user.is_active:
            user.last_active = datetime.now(timezone.utc)
            return user
        return None

    def has_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has a specific permission."""
        user = self.get_user(user_id)
        if not user or not user.is_active:
            return False
        return permission in user.permissions

    def has_role(self, user_id: str, role: str) -> bool:
        """Check if user has a specific role."""
        user = self.get_user(user_id)
        if not user or not user.is_active:
            return False
        return role in user.roles

    def add_role(self, user_id: str, role: str) -> bool:
        """Add a role to a user."""
        user = self.get_user(user_id)
        if user:
            user.roles.add(role)
            logger.info(f" Added role {role} to user {user.username}")
            return True
        return False

    def remove_role(self, user_id: str, role: str) -> bool:
        """Remove a role from a user."""
        user = self.get_user(user_id)
        if user and role in user.roles:
            user.roles.remove(role)
            logger.info(f" Removed role {role} from user {user.username}")
            return True
        return False

    def update_reputation(self, user_id: str, reputation_score: float) -> bool:
        """Update a user's reputation score."""
        user = self.get_user(user_id)
        if user:
            user.reputation_score = max(0.0, min(1.0, reputation_score))
            logger.info(
                f" Updated reputation for {user.username}: {user.reputation_score}"
            )
            return True
        return False

    def update_governance_stake(self, user_id: str, stake: float) -> bool:
        """Update a user's governance stake."""
        user = self.get_user(user_id)
        if user:
            user.governance_stake = max(0.0, stake)
            logger.info(
                f" Updated governance stake for {user.username}: {user.governance_stake}"
            )
            return True
        return False

    def get_users_with_role(self, role: str) -> List[User]:
        """Get all users with a specific role."""
        return [
            user
            for user in self.users.values()
            if role in user.roles and user.is_active
        ]

    def get_users_with_permission(self, permission: str) -> List[User]:
        """Get all users with a specific permission."""
        return [
            user
            for user in self.users.values()
            if permission in user.permissions and user.is_active
        ]

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account."""
        user = self.get_user(user_id)
        if user:
            user.is_active = False
            logger.info(f" Deactivated user: {user.username}")
            return True
        return False

    def get_all_active_users(self) -> List[User]:
        """Get all active users."""
        return [user for user in self.users.values() if user.is_active]


# Global user service instance
user_service = UserService()

# Create some default users for governance system
try:
    # Create system administrator
    user_service.create_user(
        user_id="system_admin",
        username="admin",
        email="admin@uatp.system",
        full_name="System Administrator",
        roles={"admin", "governance_member", "economic_participant"},
        permissions={
            "governance_vote",
            "emergency_powers",
            "user_management",
            "system_config",
        },
    )

    # Create governance coordinator
    user_service.create_user(
        user_id="governance_coordinator",
        username="governance",
        email="governance@uatp.system",
        full_name="Governance Coordinator",
        roles={"governance_member", "constitutional_guardian"},
        permissions={"governance_vote", "proposal_creation", "constitutional_review"},
    )

    # Create economic oversight
    user_service.create_user(
        user_id="economic_oversight",
        username="economics",
        email="economics@uatp.system",
        full_name="Economic Oversight Committee",
        roles={"economic_participant", "governance_member"},
        permissions={"governance_vote", "economic_parameters", "attribution_review"},
    )

    logger.info("[OK] Default users created for governance system")

except ValueError as e:
    # Users might already exist
    logger.info(f"Default users already exist: {e}")
