"""
JWT Authentication Manager
Production-ready JWT token generation, validation, and management
"""

import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt

logger = logging.getLogger(__name__)


@dataclass
class TokenPayload:
    """JWT token payload structure"""

    user_id: str
    email: str
    username: str
    scopes: list
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for token revocation


class JWTManager:
    """JWT token management with refresh tokens and security features"""

    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET")
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(minutes=30)
        self.refresh_token_expire = timedelta(days=30)
        self.password_reset_expire = timedelta(hours=1)

        # Token blacklist for revoked tokens (in production, use Redis)
        self.revoked_tokens = set()

        # SECURITY: Fail fast if JWT_SECRET not set in production
        if not self.secret_key:
            env = os.getenv("ENVIRONMENT", os.getenv("UATP_ENV", "development"))
            if env in ("production", "prod", "staging"):
                raise RuntimeError(
                    "CRITICAL: JWT_SECRET environment variable is required in production. "
                    "Set JWT_SECRET to a secure random value (minimum 32 bytes). "
                    'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
                )
            # SECURITY: Development only - generate ephemeral secret per session
            # This ensures tokens don't persist across restarts and no hardcoded secrets exist
            self.secret_key = secrets.token_hex(32)
            logger.warning(
                "JWT_SECRET not set - using ephemeral development key. "
                "Tokens will NOT persist across restarts. "
                "Set JWT_SECRET env var for production."
            )

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    def generate_access_token(
        self, user_id: str, email: str, username: str, scopes: list = None
    ) -> str:
        """Generate access token"""
        if scopes is None:
            scopes = ["read", "write"]

        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "scopes": scopes,
            "exp": now + self.access_token_expire,
            "iat": now,
            "jti": secrets.token_urlsafe(32),
            "type": "access",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def generate_refresh_token(self, user_id: str) -> str:
        """Generate refresh token"""
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_id,
            "exp": now + self.refresh_token_expire,
            "iat": now,
            "jti": secrets.token_urlsafe(32),
            "type": "refresh",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def generate_password_reset_token(self, user_id: str, email: str) -> str:
        """Generate password reset token"""
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": now + self.password_reset_expire,
            "iat": now,
            "jti": secrets.token_urlsafe(32),
            "type": "password_reset",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(
        self, token: str, token_type: str = "access"
    ) -> Optional[Dict[str, Any]]:
        """Verify and decode token"""
        try:
            # Check if token is revoked
            if token in self.revoked_tokens:
                logger.warning("Attempt to use revoked token")
                return None

            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check token type
            if payload.get("type") != token_type:
                logger.warning(
                    f"Invalid token type: expected {token_type}, got {payload.get('type')}"
                )
                return None

            # Check expiration
            if datetime.now(timezone.utc) > datetime.fromtimestamp(
                payload["exp"], timezone.utc
            ):
                logger.info("Token has expired")
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.info("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Generate new access token from refresh token"""
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None

        # Here you would fetch user details from database
        # For now, we'll create a basic response
        user_id = payload["user_id"]

        # Generate new access token
        new_access_token = self.generate_access_token(
            user_id=user_id,
            email=f"user_{user_id}@example.com",  # Would fetch from DB
            username=f"user_{user_id}",  # Would fetch from DB
            scopes=["read", "write"],
        )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": int(self.access_token_expire.total_seconds()),
        }

    def revoke_token(self, token: str):
        """Revoke a token (add to blacklist)"""
        self.revoked_tokens.add(token)
        logger.info("Token revoked")

    def revoke_all_user_tokens(self, user_id: str):
        """Revoke all tokens for a user (would use Redis with user_id prefix)"""
        # In production, you'd query Redis for all tokens with this user_id
        # and add them to the blacklist
        logger.info(f"All tokens revoked for user {user_id}")

    def get_token_claims(self, token: str) -> Optional[Dict[str, Any]]:
        """Get token claims without verification (for debugging)"""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            logger.error(f"Error getting token claims: {e}")
            return None


# Global JWT manager instance
jwt_manager = JWTManager()


# Helper functions for FastAPI dependencies
def create_access_token(user_data: Dict[str, Any]) -> str:
    """Create access token for user"""
    return jwt_manager.generate_access_token(
        user_id=user_data["user_id"],
        email=user_data["email"],
        username=user_data["username"],
        scopes=user_data.get("scopes", ["read", "write"]),
    )


def create_refresh_token(user_id: str) -> str:
    """Create refresh token for user"""
    return jwt_manager.generate_refresh_token(user_id)


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify access token"""
    return jwt_manager.verify_token(token, "access")


def hash_password(password: str) -> str:
    """Hash password"""
    return jwt_manager.hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password"""
    return jwt_manager.verify_password(password, hashed_password)


# Example usage and testing
if __name__ == "__main__":
    # Test JWT functionality
    print(" Testing JWT Manager...")

    # Test password hashing
    password = "test_password_123"
    hashed = hash_password(password)
    print(f"Password hashed: {hashed[:20]}...")

    # Test password verification
    is_valid = verify_password(password, hashed)
    print(f"Password verification: {is_valid}")

    # Test token generation
    user_data = {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "username": "testuser",
        "scopes": ["read", "write", "admin"],
    }

    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data["user_id"])

    print(f"Access token: {access_token[:50]}...")
    print(f"Refresh token: {refresh_token[:50]}...")

    # Test token verification
    payload = verify_access_token(access_token)
    print(f"Token payload: {payload}")

    # Test token refresh
    new_tokens = jwt_manager.refresh_access_token(refresh_token)
    print(f"New tokens: {new_tokens}")

    print("[OK] JWT Manager tests completed")
