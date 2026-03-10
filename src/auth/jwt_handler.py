"""
JWT Token Handler
================

Production-grade JWT token handling with secure signing, validation,
and refresh token management.
"""

import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jwt

from .models import PermissionScope, User

logger = logging.getLogger(__name__)


@dataclass
class TokenConfig:
    """JWT token configuration."""

    def __init__(self):
        # JWT settings
        self.secret_key = os.getenv("JWT_SECRET_KEY", self._generate_secret_key())
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        )
        self.refresh_token_expire_days = int(
            os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30")
        )

        # Issuer and audience
        self.issuer = os.getenv("JWT_ISSUER", "uatp_capsule_engine")
        self.audience = os.getenv("JWT_AUDIENCE", "uatp_api")

        # Security settings
        self.require_exp = True
        self.require_iat = True
        self.require_nbf = False
        self.leeway = timedelta(seconds=10)  # Allow 10 seconds clock skew

        # Refresh token settings
        self.refresh_token_length = 32

    def _generate_secret_key(self) -> str:
        """Generate a secure secret key if none provided."""
        logger.warning(
            "JWT_SECRET_KEY not set, generating random key. Set JWT_SECRET_KEY in production!"
        )
        return secrets.token_urlsafe(64)


@dataclass
class TokenPayload:
    """JWT token payload structure."""

    sub: str  # Subject (user_id)
    iat: datetime  # Issued at
    exp: datetime  # Expiration time
    iss: str  # Issuer
    aud: str  # Audience
    jti: str  # JWT ID (unique token identifier)

    # Custom claims
    username: str
    email: str
    user_type: str
    permissions: List[str]
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert payload to dictionary for JWT encoding."""
        return {
            "sub": self.sub,
            "iat": int(self.iat.timestamp()),
            "exp": int(self.exp.timestamp()),
            "iss": self.iss,
            "aud": self.aud,
            "jti": self.jti,
            "username": self.username,
            "email": self.email,
            "user_type": self.user_type,
            "permissions": self.permissions,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenPayload":
        """Create payload from dictionary."""
        return cls(
            sub=data["sub"],
            iat=datetime.fromtimestamp(data["iat"], tz=timezone.utc),
            exp=datetime.fromtimestamp(data["exp"], tz=timezone.utc),
            iss=data["iss"],
            aud=data["aud"],
            jti=data["jti"],
            username=data["username"],
            email=data["email"],
            user_type=data["user_type"],
            permissions=data["permissions"],
            session_id=data.get("session_id"),
        )


class JWTHandler:
    """JWT token handler with production security features."""

    def __init__(self, config: Optional[TokenConfig] = None):
        self.config = config or TokenConfig()

        # Token blacklist (in production, use Redis or database)
        self._blacklisted_tokens = set()

        logger.info(f"JWT handler initialized with algorithm {self.config.algorithm}")

    def create_access_token(
        self,
        user: User,
        permissions: List[PermissionScope],
        session_id: Optional[str] = None,
    ) -> str:
        """Create a JWT access token for user."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=self.config.access_token_expire_minutes)

        # Create unique token ID
        jti = secrets.token_urlsafe(16)

        # Create payload
        payload = TokenPayload(
            sub=user.user_id,
            iat=now,
            exp=expires,
            iss=self.config.issuer,
            aud=self.config.audience,
            jti=jti,
            username=user.username,
            email=user.email,
            user_type=user.user_type.value,
            permissions=[p.value for p in permissions],
            session_id=session_id,
        )

        try:
            token = jwt.encode(
                payload.to_dict(),
                self.config.secret_key,
                algorithm=self.config.algorithm,
            )

            logger.debug(
                f"Created access token for user {user.username} (expires: {expires})"
            )
            return token

        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise

    def create_refresh_token(self) -> str:
        """Create a refresh token."""
        return secrets.token_urlsafe(self.config.refresh_token_length)

    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode JWT token."""
        try:
            # Check if token is blacklisted
            if token in self._blacklisted_tokens:
                raise jwt.InvalidTokenError("Token has been revoked")

            # Decode token
            payload_dict = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm],
                issuer=self.config.issuer,
                audience=self.config.audience,
                options={
                    "require_exp": self.config.require_exp,
                    "require_iat": self.config.require_iat,
                    "require_nbf": self.config.require_nbf,
                },
                leeway=self.config.leeway,
            )

            # Create payload object
            payload = TokenPayload.from_dict(payload_dict)

            logger.debug(f"Successfully verified token for user {payload.username}")
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidIssuerError:
            logger.warning("Invalid token issuer")
            raise jwt.InvalidTokenError("Invalid token issuer")
        except jwt.InvalidAudienceError:
            logger.warning("Invalid token audience")
            raise jwt.InvalidTokenError("Invalid token audience")
        except jwt.InvalidSignatureError:
            logger.warning("Invalid token signature")
            raise jwt.InvalidTokenError("Invalid token signature")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise jwt.InvalidTokenError("Token verification failed")

    def decode_token_unsafe(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode token without verification (for debugging/inspection)."""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            logger.error(f"Failed to decode token: {e}")
            return None

    def revoke_token(self, token: str) -> bool:
        """Revoke a token by adding it to blacklist."""
        try:
            # In production, store in Redis or database with TTL
            self._blacklisted_tokens.add(token)
            logger.info("Token revoked successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

    def is_token_revoked(self, token: str) -> bool:
        """Check if token is revoked."""
        return token in self._blacklisted_tokens

    def refresh_access_token(
        self,
        user: User,
        permissions: List[PermissionScope],
        session_id: Optional[str] = None,
    ) -> str:
        """Create a new access token (typically after refresh token validation)."""
        return self.create_access_token(user, permissions, session_id)

    def get_token_claims(self, token: str) -> Optional[Dict[str, Any]]:
        """Get token claims without full verification."""
        try:
            payload = self.verify_token(token)
            return payload.to_dict()
        except Exception:
            return None

    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """Get token expiration time."""
        claims = self.decode_token_unsafe(token)
        if claims and "exp" in claims:
            return datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        return None

    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired."""
        expiry = self.get_token_expiry(token)
        if expiry is None:
            return True
        return datetime.now(timezone.utc) > expiry

    def cleanup_blacklist(self):
        """Clean up expired tokens from blacklist."""
        # In production, this would be handled by Redis TTL or database cleanup job
        expired_tokens = set()

        for token in self._blacklisted_tokens:
            if self.is_token_expired(token):
                expired_tokens.add(token)

        self._blacklisted_tokens -= expired_tokens
        logger.debug(f"Cleaned up {len(expired_tokens)} expired tokens from blacklist")


# Global JWT handler instance
_global_jwt_handler: Optional[JWTHandler] = None


def get_jwt_handler() -> JWTHandler:
    """Get global JWT handler instance."""
    global _global_jwt_handler
    if _global_jwt_handler is None:
        _global_jwt_handler = JWTHandler()
    return _global_jwt_handler


def create_access_token(
    user: User, permissions: List[PermissionScope], session_id: Optional[str] = None
) -> str:
    """Convenience function to create access token."""
    handler = get_jwt_handler()
    return handler.create_access_token(user, permissions, session_id)


def verify_token(token: str) -> TokenPayload:
    """Convenience function to verify token."""
    handler = get_jwt_handler()
    return handler.verify_token(token)


def revoke_token(token: str) -> bool:
    """Convenience function to revoke token."""
    handler = get_jwt_handler()
    return handler.revoke_token(token)


# Token validation utilities
class TokenValidator:
    """Additional token validation utilities."""

    @staticmethod
    def validate_token_format(token: str) -> bool:
        """Validate basic token format."""
        if not token or not isinstance(token, str):
            return False

        parts = token.split(".")
        return len(parts) == 3  # Header.Payload.Signature

    @staticmethod
    def extract_user_id(token: str) -> Optional[str]:
        """Extract user ID from token without full verification."""
        handler = get_jwt_handler()
        claims = handler.decode_token_unsafe(token)
        return claims.get("sub") if claims else None

    @staticmethod
    def extract_permissions(token: str) -> List[str]:
        """Extract permissions from token without full verification."""
        handler = get_jwt_handler()
        claims = handler.decode_token_unsafe(token)
        return claims.get("permissions", []) if claims else []
