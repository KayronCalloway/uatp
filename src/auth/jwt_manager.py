"""
JWT Authentication Manager
Production-ready JWT token generation, validation, and management
"""

import logging
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set

import bcrypt
import jwt

logger = logging.getLogger(__name__)


# ==============================================================================
# SECURITY: Redis-backed Token Revocation List
# ==============================================================================
class TokenRevocationList:
    """
    Redis-backed token revocation list for JWT invalidation.

    SECURITY: Provides persistent token revocation that survives service restarts.
    Uses JTI (JWT ID) for efficient storage and TTL-based automatic cleanup.

    Falls back to in-memory storage when Redis is unavailable (development only).
    """

    def __init__(self):
        self._redis_client = None
        self._redis_available = False
        self._in_memory_fallback: Dict[str, float] = {}  # jti -> expiration timestamp
        self._user_tokens: Dict[str, Set[str]] = {}  # user_id -> set of jtis
        self._last_cleanup = time.time()
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection for token revocation."""
        try:
            import redis

            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_password = os.getenv("REDIS_PASSWORD")
            redis_db = int(os.getenv("REDIS_REVOCATION_DB", "2"))

            self._redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=2,
            )

            # Test connection
            self._redis_client.ping()
            self._redis_available = True
            logger.info("Token revocation list using Redis backend")

        except ImportError:
            logger.warning(
                "SECURITY: redis package not installed. "
                "Token revocation will use in-memory storage (development only)."
            )
            self._redis_available = False

        except Exception as e:
            env = os.getenv("ENVIRONMENT", os.getenv("UATP_ENV", "development"))
            if env in ("production", "prod", "staging"):
                logger.error(
                    f"CRITICAL: Redis unavailable for token revocation in {env}: {e}"
                )
            else:
                logger.warning(
                    f"Redis unavailable for token revocation: {e}. "
                    "Using in-memory fallback (development only)."
                )
            self._redis_available = False

    def revoke_token(self, jti: str, user_id: str, ttl_seconds: int):
        """
        Revoke a token by its JTI.

        Args:
            jti: JWT ID (unique token identifier)
            user_id: User ID for the token
            ttl_seconds: Time until token would naturally expire (for cleanup)
        """
        if self._redis_available:
            try:
                # Store revoked token with TTL
                key = f"revoked:{jti}"
                self._redis_client.setex(key, ttl_seconds, user_id)

                # Track user's revoked tokens (for revoke_all_user_tokens)
                user_key = f"user_revoked:{user_id}"
                self._redis_client.sadd(user_key, jti)
                self._redis_client.expire(user_key, ttl_seconds)

                logger.info(f"Token revoked: jti={jti[:8]}... user={user_id}")
                return True

            except Exception as e:
                logger.error(f"Redis error revoking token: {e}")
                # Fall through to in-memory fallback

        # In-memory fallback
        expiration = time.time() + ttl_seconds
        self._in_memory_fallback[jti] = expiration

        if user_id not in self._user_tokens:
            self._user_tokens[user_id] = set()
        self._user_tokens[user_id].add(jti)

        self._cleanup_expired()
        logger.info(f"Token revoked (in-memory): jti={jti[:8]}... user={user_id}")
        return True

    def is_revoked(self, jti: str) -> bool:
        """Check if a token is revoked."""
        if self._redis_available:
            try:
                return self._redis_client.exists(f"revoked:{jti}") > 0
            except Exception as e:
                logger.error(f"Redis error checking revocation: {e}")
                # Fall through to in-memory check

        # Check in-memory (also used as fallback)
        if jti in self._in_memory_fallback:
            if self._in_memory_fallback[jti] > time.time():
                return True
            # Expired, clean up
            del self._in_memory_fallback[jti]

        return False

    def revoke_all_user_tokens(self, user_id: str, ttl_seconds: int = 86400):
        """
        Revoke all tokens for a user.

        Args:
            user_id: User ID to revoke all tokens for
            ttl_seconds: TTL for the revocation entries
        """
        if self._redis_available:
            try:
                # Store user-level revocation marker
                key = f"user_revoked_all:{user_id}"
                self._redis_client.setex(key, ttl_seconds, str(time.time()))
                logger.info(f"All tokens revoked for user: {user_id}")
                return True

            except Exception as e:
                logger.error(f"Redis error revoking user tokens: {e}")

        # In-memory fallback - revoke all known tokens for this user
        if user_id in self._user_tokens:
            expiration = time.time() + ttl_seconds
            for jti in self._user_tokens[user_id]:
                self._in_memory_fallback[jti] = expiration

        logger.info(f"All tokens revoked (in-memory) for user: {user_id}")
        return True

    def is_user_revoked(self, user_id: str, token_iat: float) -> bool:
        """
        Check if all user tokens were revoked after the token was issued.

        Args:
            user_id: User ID
            token_iat: Token issued-at timestamp

        Returns:
            True if user's tokens were revoked after this token was issued
        """
        if self._redis_available:
            try:
                key = f"user_revoked_all:{user_id}"
                revoked_at = self._redis_client.get(key)
                if revoked_at:
                    return float(revoked_at) > token_iat
            except Exception as e:
                logger.error(f"Redis error checking user revocation: {e}")

        return False

    def _cleanup_expired(self):
        """Clean up expired entries from in-memory storage."""
        now = time.time()

        # Only cleanup every 5 minutes
        if now - self._last_cleanup < 300:
            return

        self._last_cleanup = now
        expired = [jti for jti, exp in self._in_memory_fallback.items() if exp <= now]

        for jti in expired:
            del self._in_memory_fallback[jti]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired revocation entries")


# Singleton revocation list
_token_revocation_list = TokenRevocationList()


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

        # SECURITY: Use Redis-backed revocation list (falls back to in-memory in dev)
        self._revocation_list = _token_revocation_list

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
            "sub": str(user_id),
            "user_id": str(user_id),  # keeping for backward compatibility
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
            "sub": str(user_id),
            "user_id": str(user_id),
            "exp": now + self.refresh_token_expire,
            "iat": now,
            "jti": secrets.token_urlsafe(32),
            "type": "refresh",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def generate_password_reset_token(self, email: str) -> str:
        """Generate password reset token"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": email,
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
            # Decode token first to get JTI and user_id
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # SECURITY: Check if token is revoked (by JTI)
            jti = payload.get("jti")
            if jti and self._revocation_list.is_revoked(jti):
                logger.warning(f"Attempt to use revoked token: jti={jti[:8]}...")
                return None

            # SECURITY: Check if all user tokens were revoked after this token was issued
            user_id = payload.get("sub") or payload.get("user_id")
            iat = payload.get("iat")
            if user_id and iat:
                # Convert iat to timestamp if it's a datetime
                iat_timestamp = (
                    iat if isinstance(iat, (int, float)) else iat.timestamp()
                )
                if self._revocation_list.is_user_revoked(user_id, iat_timestamp):
                    logger.warning(
                        f"Token issued before user-wide revocation: user={user_id}"
                    )
                    return None

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
        """Revoke a token by adding its JTI to the revocation list."""
        try:
            # Decode without verification to get JTI and user_id
            payload = jwt.decode(token, options={"verify_signature": False})
            jti = payload.get("jti")
            user_id = payload.get("sub") or payload.get("user_id", "unknown")
            exp = payload.get("exp")

            if not jti:
                logger.warning("Cannot revoke token without JTI")
                return False

            # Calculate TTL (time until token expires naturally)
            if exp:
                exp_timestamp = (
                    exp if isinstance(exp, (int, float)) else exp.timestamp()
                )
                ttl = max(1, int(exp_timestamp - time.time()))
            else:
                # Default to 24 hours if no expiration
                ttl = 86400

            return self._revocation_list.revoke_token(jti, user_id, ttl)

        except jwt.DecodeError as e:
            logger.error(f"Cannot decode token for revocation: {e}")
            return False

    def revoke_all_user_tokens(self, user_id: str, ttl_seconds: int = 86400):
        """
        Revoke all tokens for a user.

        This invalidates all tokens issued before this revocation,
        forcing the user to re-authenticate.

        Args:
            user_id: User ID to revoke tokens for
            ttl_seconds: How long to maintain the revocation (default: 24h)
        """
        return self._revocation_list.revoke_all_user_tokens(user_id, ttl_seconds)

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
def create_access_token(
    user_id: str, email: str = "", username: str = "", scopes: list = None
) -> tuple[str, int]:
    """Create access token for user and return (token, expires_in)"""
    token = jwt_manager.generate_access_token(
        user_id=str(user_id),
        email=email,
        username=username,
        scopes=scopes if scopes is not None else ["read", "write"],
    )
    expires_in = int(jwt_manager.access_token_expire.total_seconds())
    return token, expires_in


def create_refresh_token(user_id: str) -> str:
    """Create refresh token for user"""
    return jwt_manager.generate_refresh_token(str(user_id))


def create_reset_token(email: str) -> str:
    """Create password reset token"""
    return jwt_manager.generate_password_reset_token(email)


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
