#!/usr/bin/env python3
"""
JWT Authentication System for UATP Capsule Engine
===============================================

This module provides JWT-based authentication for the UATP system,
including token generation, validation, and user management.
"""

import asyncio
import hmac
import logging
import os
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import bcrypt
import jwt

from src.utils.timezone_utils import utc_now

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
JWT_REFRESH_EXPIRATION_DAYS = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))


@dataclass
class User:
    """User data structure."""

    user_id: str
    username: str
    email: str
    password_hash: str
    roles: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TokenPayload:
    """JWT token payload structure."""

    user_id: str
    username: str
    email: str
    roles: List[str]
    exp: int
    iat: int
    token_type: str = "access"  # access or refresh


class JWTAuthenticator:
    """JWT authentication manager."""

    def __init__(
        self, secret_key: str = JWT_SECRET_KEY, algorithm: str = JWT_ALGORITHM
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.users: Dict[
            str, User
        ] = {}  # In-memory user store (replace with DB in production)
        self.refresh_tokens: Dict[str, str] = {}  # Store refresh tokens

        logger.info(" JWT Authenticator initialized")
        logger.info(f"   Algorithm: {algorithm}")
        logger.info(f"   Token expiration: {JWT_EXPIRATION_HOURS} hours")
        logger.info(f"   Refresh expiration: {JWT_REFRESH_EXPIRATION_DAYS} days")

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt.

        SECURITY: bcrypt is designed to be slow and resistant to GPU/ASIC attacks.
        Work factor of 12 provides ~300ms hash time on modern hardware.
        """
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its bcrypt hash.

        SECURITY: Uses constant-time comparison internally via bcrypt.checkpw.
        Also supports legacy SHA-256 hashes for migration.
        """
        try:
            # Check for legacy SHA-256 format (salt:hash)
            if ":" in password_hash and not password_hash.startswith("$2"):
                # SECURITY WARNING: Legacy SHA-256 hash detected
                # This is maintained only for backwards compatibility during migration
                import hashlib

                logger.warning(
                    "SECURITY: Legacy SHA-256 password hash detected. "
                    "User should change password to upgrade to bcrypt."
                )
                salt, stored_hash = password_hash.split(":")
                computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
                # Use constant-time comparison
                return hmac.compare_digest(computed_hash, stored_hash)

            # Modern bcrypt verification
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Password verification error: {e}")
            return False

    def create_user(
        self, username: str, email: str, password: str, roles: List[str] = None
    ) -> User:
        """Create a new user."""

        if roles is None:
            roles = ["user"]

        # Check if user already exists
        if username in self.users:
            raise ValueError(f"Username '{username}' already exists")

        # Check if email already exists
        for user in self.users.values():
            if user.email == email:
                raise ValueError(f"Email '{email}' already exists")

        # Create user
        user_id = secrets.token_hex(16)
        password_hash = self.hash_password(password)

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash,
            roles=roles,
            created_at=utc_now(),
        )

        self.users[username] = user
        logger.info(f" User created: {username} ({email})")
        return user

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""

        user = self.users.get(username)
        if not user:
            return None

        if not user.is_active:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = utc_now()
        logger.info(f" User authenticated: {username}")
        return user

    def generate_access_token(self, user: User) -> str:
        """Generate an access token for a user."""

        now = utc_now()
        exp = now + timedelta(hours=JWT_EXPIRATION_HOURS)

        payload = TokenPayload(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            roles=user.roles,
            exp=int(exp.timestamp()),
            iat=int(now.timestamp()),
            token_type="access",
        )

        token = jwt.encode(asdict(payload), self.secret_key, algorithm=self.algorithm)
        logger.info(f" Access token generated for: {user.username}")
        return token

    def generate_refresh_token(self, user: User) -> str:
        """Generate a refresh token for a user."""

        now = utc_now()
        exp = now + timedelta(days=JWT_REFRESH_EXPIRATION_DAYS)

        payload = TokenPayload(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            roles=user.roles,
            exp=int(exp.timestamp()),
            iat=int(now.timestamp()),
            token_type="refresh",
        )

        token = jwt.encode(asdict(payload), self.secret_key, algorithm=self.algorithm)

        # Store refresh token
        self.refresh_tokens[token] = user.user_id

        logger.info(f" Refresh token generated for: {user.username}")
        return token

    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """Verify and decode a JWT token."""

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            logger.warning(" Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning(" Invalid token")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Generate a new access token using a refresh token."""

        # Verify refresh token
        payload = self.verify_token(refresh_token)
        if not payload or payload.token_type != "refresh":
            return None

        # Check if refresh token is still valid
        if refresh_token not in self.refresh_tokens:
            return None

        # Get user
        user = self.users.get(payload.username)
        if not user or not user.is_active:
            return None

        # Generate new access token
        return self.generate_access_token(user)

    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke a refresh token."""

        if refresh_token in self.refresh_tokens:
            del self.refresh_tokens[refresh_token]
            logger.info("️ Refresh token revoked")
            return True
        return False

    def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user information from a token."""

        payload = self.verify_token(token)
        if not payload:
            return None

        return self.users.get(payload.username)

    def has_role(self, user: User, role: str) -> bool:
        """Check if user has a specific role."""
        return role in user.roles

    def has_any_role(self, user: User, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in user.roles for role in roles)

    def add_role(self, username: str, role: str) -> bool:
        """Add a role to a user."""

        user = self.users.get(username)
        if not user:
            return False

        if role not in user.roles:
            user.roles.append(role)
            logger.info(f" Role '{role}' added to user: {username}")

        return True

    def remove_role(self, username: str, role: str) -> bool:
        """Remove a role from a user."""

        user = self.users.get(username)
        if not user:
            return False

        if role in user.roles:
            user.roles.remove(role)
            logger.info(f" Role '{role}' removed from user: {username}")

        return True

    def deactivate_user(self, username: str) -> bool:
        """Deactivate a user account."""

        user = self.users.get(username)
        if not user:
            return False

        user.is_active = False
        logger.info(f" User deactivated: {username}")
        return True

    def activate_user(self, username: str) -> bool:
        """Activate a user account."""

        user = self.users.get(username)
        if not user:
            return False

        user.is_active = True
        logger.info(f"[OK] User activated: {username}")
        return True

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users (without sensitive data)."""

        return [
            {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "roles": user.roles,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "is_active": user.is_active,
            }
            for user in self.users.values()
        ]

    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics."""

        total_users = len(self.users)
        active_users = sum(1 for user in self.users.values() if user.is_active)
        inactive_users = total_users - active_users

        # Role distribution
        role_counts = {}
        for user in self.users.values():
            for role in user.roles:
                role_counts[role] = role_counts.get(role, 0) + 1

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "role_distribution": role_counts,
            "active_refresh_tokens": len(self.refresh_tokens),
        }


# Global authenticator instance
_authenticator = None


def get_authenticator() -> JWTAuthenticator:
    """Get the global authenticator instance."""
    global _authenticator
    if _authenticator is None:
        _authenticator = JWTAuthenticator()
    return _authenticator


# Authentication decorator
def require_auth(required_roles: List[str] = None):
    """Decorator to require authentication for API endpoints."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This is a placeholder - in real implementation, you'd extract
            # the token from the request headers
            token = kwargs.get("auth_token")
            if not token:
                raise ValueError("Authentication required")

            authenticator = get_authenticator()
            user = authenticator.get_user_from_token(token)

            if not user:
                raise ValueError("Invalid or expired token")

            if required_roles and not authenticator.has_any_role(user, required_roles):
                raise ValueError("Insufficient permissions")

            # Add user to kwargs
            kwargs["current_user"] = user
            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def main():
    """Test the JWT authentication system."""

    print(" Testing JWT Authentication System")
    print("=" * 50)

    # Initialize authenticator
    auth = get_authenticator()

    # Test user creation
    print("\n Testing user creation...")
    try:
        user1 = auth.create_user(
            "alice", "alice@example.com", "password123", ["user", "admin"]
        )
        user2 = auth.create_user("bob", "bob@example.com", "password456", ["user"])
        print(f"[OK] Created users: {user1.username}, {user2.username}")
    except ValueError as e:
        print(f"[ERROR] User creation failed: {e}")

    # Test authentication
    print("\n Testing authentication...")
    user = auth.authenticate_user("alice", "password123")
    if user:
        print(f"[OK] Authentication successful: {user.username}")

        # Generate tokens
        access_token = auth.generate_access_token(user)
        refresh_token = auth.generate_refresh_token(user)

        print(f" Access token: {access_token[:50]}...")
        print(f" Refresh token: {refresh_token[:50]}...")

        # Verify tokens
        print("\n Testing token verification...")
        payload = auth.verify_token(access_token)
        if payload:
            print(f"[OK] Token valid for: {payload.username}")
            print(f"   Roles: {payload.roles}")
            print(f"   Expires: {datetime.fromtimestamp(payload.exp)}")

        # Test token refresh
        print("\n Testing token refresh...")
        new_access_token = auth.refresh_access_token(refresh_token)
        if new_access_token:
            print(f"[OK] New access token: {new_access_token[:50]}...")

        # Test role management
        print("\n Testing role management...")
        auth.add_role("bob", "moderator")
        auth.remove_role("alice", "admin")

        user_bob = auth.users.get("bob")
        user_alice = auth.users.get("alice")

        print(f"   Bob's roles: {user_bob.roles}")
        print(f"   Alice's roles: {user_alice.roles}")

        # Test user stats
        print("\n User statistics:")
        stats = auth.get_user_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
    else:
        print("[ERROR] Authentication failed")

    # Test failed authentication
    print("\n Testing failed authentication...")
    failed_user = auth.authenticate_user("alice", "wrongpassword")
    if not failed_user:
        print("[OK] Failed authentication correctly rejected")

    print("\n[OK] JWT authentication test completed!")


if __name__ == "__main__":
    asyncio.run(main())
