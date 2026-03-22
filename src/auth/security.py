"""
Security Utilities
==================

Production-grade security utilities for password hashing, validation,
encryption, and other security-related operations.
"""

import base64
import hashlib
import logging
import os
import re
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration management."""

    def __init__(self):
        # Password requirements
        self.min_password_length = int(os.getenv("MIN_PASSWORD_LENGTH", "8"))
        self.require_uppercase = (
            os.getenv("REQUIRE_UPPERCASE", "true").lower() == "true"
        )
        self.require_lowercase = (
            os.getenv("REQUIRE_LOWERCASE", "true").lower() == "true"
        )
        self.require_numbers = os.getenv("REQUIRE_NUMBERS", "true").lower() == "true"
        self.require_special_chars = (
            os.getenv("REQUIRE_SPECIAL_CHARS", "true").lower() == "true"
        )

        # Account lockout
        self.max_failed_attempts = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
        self.lockout_duration_minutes = int(os.getenv("LOCKOUT_DURATION_MINUTES", "30"))

        # Session security
        self.session_timeout_hours = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
        self.max_concurrent_sessions = int(os.getenv("MAX_CONCURRENT_SESSIONS", "3"))

        # Encryption
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        if not self.encryption_key:
            logger.warning("ENCRYPTION_KEY not set, generating random key")
            self.encryption_key = Fernet.generate_key().decode()


class PasswordValidator:
    """Password validation and strength checking."""

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()

    def validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password against security requirements."""
        errors = []
        score = 0

        # Length check
        if len(password) < self.config.min_password_length:
            errors.append(
                f"Password must be at least {self.config.min_password_length} characters long"
            )
        else:
            score += 1

        # Character requirements
        if self.config.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        else:
            score += 1

        if self.config.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        else:
            score += 1

        if self.config.require_numbers and not re.search(r"\d", password):
            errors.append("Password must contain at least one number")
        else:
            score += 1

        if self.config.require_special_chars and not re.search(
            r'[!@#$%^&*(),.?":{}|<>]', password
        ):
            errors.append("Password must contain at least one special character")
        else:
            score += 1

        # Additional strength checks
        if len(password) >= 12:
            score += 1

        if re.search(r"[A-Z].*[A-Z]", password):  # Multiple uppercase
            score += 1

        if re.search(r"\d.*\d", password):  # Multiple numbers
            score += 1

        if re.search(
            r'[!@#$%^&*(),.?":{}|<>].*[!@#$%^&*(),.?":{}|<>]', password
        ):  # Multiple special chars
            score += 1

        # Common patterns to avoid
        common_patterns = [
            r"123456",
            r"password",
            r"qwerty",
            r"abcdef",
            r"(.)\1{2,}",  # Repeated characters
        ]

        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                errors.append("Password contains common patterns or sequences")
                score -= 1
                break

        # Determine strength
        if score >= 7:
            strength = "strong"
        elif score >= 5:
            strength = "medium"
        elif score >= 3:
            strength = "weak"
        else:
            strength = "very_weak"

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": strength,
            "score": max(0, score),
        }

    def is_common_password(self, password: str) -> bool:
        """Check if password is in common passwords list."""
        # In production, this would check against a comprehensive list
        common_passwords = {
            "password",
            "123456",
            "123456789",
            "qwerty",
            "abc123",
            "password123",
            "admin",
            "letmein",
            "welcome",
            "monkey",
            "dragon",
            "master",
            "shadow",
            "football",
            "baseball",
        }
        return password.lower() in common_passwords


class PasswordHasher:
    """Secure password hashing using bcrypt."""

    def __init__(self, rounds: int = 12):
        self.rounds = rounds

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        try:
            salt = bcrypt.gensalt(rounds=self.rounds)
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False

    def needs_rehash(self, hashed: str) -> bool:
        """Check if password hash needs to be updated."""
        try:
            # Extract rounds from hash
            parts = hashed.split("$")
            if len(parts) >= 3:
                current_rounds = int(parts[2])
                return current_rounds < self.rounds
            return True
        except Exception:
            return True


class APIKeyGenerator:
    """Generate and validate API keys."""

    def __init__(self, key_length: int = 32):
        self.key_length = key_length

    def generate_api_key(self) -> Dict[str, str]:
        """Generate a new API key."""
        # Generate key
        key = secrets.token_urlsafe(self.key_length)

        # Generate key ID for identification
        key_id = f"ak_{secrets.token_urlsafe(8)}"

        # Hash the key for storage
        hasher = PasswordHasher()
        key_hash = hasher.hash_password(key)

        return {"key_id": key_id, "key": key, "key_hash": key_hash}

    def verify_api_key(self, key: str, stored_hash: str) -> bool:
        """Verify an API key against its stored hash."""
        hasher = PasswordHasher()
        return hasher.verify_password(key, stored_hash)


class DataEncryption:
    """Symmetric encryption for sensitive data."""

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self._fernet = None

    def _get_fernet(self) -> Fernet:
        """Get Fernet instance for encryption/decryption."""
        if self._fernet is None:
            if isinstance(self.config.encryption_key, str):
                key = self.config.encryption_key.encode()
            else:
                key = self.config.encryption_key
            self._fernet = Fernet(key)
        return self._fernet

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        try:
            fernet = self._get_fernet()
            encrypted = fernet.encrypt(data.encode("utf-8"))
            return base64.b64encode(encrypted).decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        try:
            fernet = self._get_fernet()
            decoded = base64.b64decode(encrypted_data.encode("utf-8"))
            decrypted = fernet.decrypt(decoded)
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    @staticmethod
    def derive_key_from_password(password: str, salt: bytes) -> bytes:
        """Derive encryption key from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480_000,  # OWASP recommends 310,000+ for SHA256
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))


class SecurityManager:
    """Main security manager coordinating all security operations."""

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.password_validator = PasswordValidator(self.config)
        self.password_hasher = PasswordHasher()
        self.api_key_generator = APIKeyGenerator()
        self.data_encryption = DataEncryption(self.config)

        logger.info("Security manager initialized")

    def validate_and_hash_password(self, password: str) -> Dict[str, Any]:
        """Validate password and return hash if valid."""
        validation = self.password_validator.validate_password(password)

        if validation["valid"]:
            validation["hash"] = self.password_hasher.hash_password(password)

        return validation

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return self.password_hasher.verify_password(password, hashed)

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a secure random token."""
        return secrets.token_urlsafe(length)

    def generate_otp(self, length: int = 6) -> str:
        """Generate a numeric OTP."""
        return "".join(secrets.choice("0123456789") for _ in range(length))

    def hash_data(self, data: str, algorithm: str = "sha256") -> str:
        """Hash data using specified algorithm."""
        if algorithm == "sha256":
            return hashlib.sha256(data.encode()).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(data.encode()).hexdigest()
        elif algorithm == "md5":
            raise ValueError("MD5 is insecure and no longer supported")
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    def constant_time_compare(self, a: str, b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks."""
        if len(a) != len(b):
            return False

        result = 0
        for x, y in zip(a, b, strict=False):
            result |= ord(x) ^ ord(y)
        return result == 0

    def sanitize_input(self, input_str: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        # Remove null bytes
        sanitized = input_str.replace("\x00", "")

        # Remove control characters (except newline and tab)
        sanitized = "".join(
            char for char in sanitized if ord(char) >= 32 or char in "\n\t"
        )

        return sanitized.strip()

    def validate_email(self, email: str) -> bool:
        """Validate email address format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def get_security_headers(self) -> Dict[str, str]:
        """Get recommended security headers (modern set, no deprecated headers)."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }


# Global security manager instance
_global_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Get the global security manager instance."""
    global _global_security_manager
    if _global_security_manager is None:
        _global_security_manager = SecurityManager()
    return _global_security_manager


def hash_password(password: str) -> str:
    """Convenience function to hash a password."""
    security_manager = get_security_manager()
    return security_manager.password_hasher.hash_password(password)


def verify_password(password: str, hashed: str) -> bool:
    """Convenience function to verify a password."""
    security_manager = get_security_manager()
    return security_manager.verify_password(password, hashed)


def validate_password(password: str) -> Dict[str, Any]:
    """Convenience function to validate a password."""
    security_manager = get_security_manager()
    return security_manager.password_validator.validate_password(password)


def generate_api_key() -> Dict[str, str]:
    """Convenience function to generate an API key."""
    security_manager = get_security_manager()
    return security_manager.api_key_generator.generate_api_key()


class SecurityAudit:
    """Security audit and logging utilities."""

    @staticmethod
    def log_security_event(
        event_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict] = None,
    ):
        """Log security-related events."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details or {},
        }

        # In production, this would go to a security audit log
        logger.info(f"Security Event: {log_entry}")

    @staticmethod
    def log_failed_login(username: str, ip_address: str, reason: str):
        """Log failed login attempts."""
        SecurityAudit.log_security_event(
            "failed_login",
            user_id=username,
            ip_address=ip_address,
            details={"reason": reason},
        )

    @staticmethod
    def log_successful_login(user_id: str, ip_address: str):
        """Log successful login."""
        SecurityAudit.log_security_event(
            "successful_login", user_id=user_id, ip_address=ip_address
        )

    @staticmethod
    def log_permission_denied(
        user_id: str, resource: str, action: str, ip_address: str
    ):
        """Log permission denied events."""
        SecurityAudit.log_security_event(
            "permission_denied",
            user_id=user_id,
            ip_address=ip_address,
            details={"resource": resource, "action": action},
        )
