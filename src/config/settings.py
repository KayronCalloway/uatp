"""
settings.py - Centralized configuration management for UATP Capsule Engine.

This module provides a single source of truth for all configuration settings,
ensuring consistent access and validation across the application.

Features:
1. Environment-specific settings (dev, test, production)
2. Configuration validation
3. Default values for optional settings
4. Type checking and conversion
5. Centralized documentation of all settings
"""

import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Set

# Configure logger
logger = logging.getLogger("uatp.config")


# Define environment types
class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


# Application settings with defaults
class Settings:
    # Environment configuration
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False

    # Storage settings
    STORAGE_DIR: Path = Path("./storage")
    COMPRESSED_STORAGE: bool = False
    MAX_CHAIN_SIZE: int = 10000

    # API settings - configured via environment variables in production
    # Canonical port is 8000 (matches Docker, run.py, and docker-compose)
    API_HOST: str = os.getenv("UATP_API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("UATP_API_PORT") or os.getenv("API_PORT", "8000"))
    RATE_LIMIT: int = 100  # Requests per minute
    CORS_ORIGINS: List[str] = (
        os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
    )
    API_KEYS: Dict[str, Any] = {}

    # Capsule settings
    DEFAULT_CAPSULE_VERSION: str = "7.1"
    SUPPORTED_CAPSULE_VERSIONS: Set[str] = {"6.0", "7.0", "7.1"}

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def __init__(self):
        """Initialize settings from environment variables and config files."""
        # Set environment
        self._set_environment()

        # Load settings in order of precedence:
        # 1. Environment variables
        # 2. Config file for current environment
        # 3. Default values (already set)
        self._load_from_env_vars()
        self._load_from_config_file()

        # Post-initialization validation and processing
        self._validate_settings()
        self._process_settings()

        logger.info(f"Initialized settings for environment: {self.ENVIRONMENT}")

    def _set_environment(self):
        """Set the current environment based on UATP_ENV variable."""
        env = os.getenv("UATP_ENV", "development").lower()

        if env in [e.value for e in Environment]:
            self.ENVIRONMENT = Environment(env)
        else:
            logger.warning(
                f"Invalid environment '{env}', defaulting to {self.ENVIRONMENT}"
            )

        # Set debug mode for development
        self.DEBUG = self.ENVIRONMENT == Environment.DEVELOPMENT

    def _load_from_env_vars(self):
        """Load settings from environment variables."""
        # Storage settings
        if os.getenv("UATP_STORAGE_DIR"):
            self.STORAGE_DIR = Path(os.getenv("UATP_STORAGE_DIR"))

        self.COMPRESSED_STORAGE = os.getenv(
            "UATP_COMPRESSED_STORAGE", str(self.COMPRESSED_STORAGE)
        ).lower() in ("true", "1", "t")

        if os.getenv("UATP_MAX_CHAIN_SIZE"):
            try:
                self.MAX_CHAIN_SIZE = int(os.getenv("UATP_MAX_CHAIN_SIZE"))
            except ValueError:
                logger.warning("Invalid MAX_CHAIN_SIZE, using default value")

        # API settings
        self.API_HOST = os.getenv("UATP_API_HOST", self.API_HOST)

        if os.getenv("UATP_API_PORT"):
            try:
                self.API_PORT = int(os.getenv("UATP_API_PORT"))
            except ValueError:
                logger.warning("Invalid API_PORT, using default value")

        if os.getenv("UATP_RATE_LIMIT"):
            try:
                self.RATE_LIMIT = int(os.getenv("UATP_RATE_LIMIT"))
            except ValueError:
                logger.warning("Invalid RATE_LIMIT, using default value")

        if os.getenv("UATP_CORS_ORIGINS"):
            try:
                self.CORS_ORIGINS = json.loads(os.getenv("UATP_CORS_ORIGINS"))
            except json.JSONDecodeError:
                logger.warning("Invalid CORS_ORIGINS, using default value")

        if os.getenv("UATP_API_KEYS"):
            try:
                self.API_KEYS = json.loads(os.getenv("UATP_API_KEYS"))
            except json.JSONDecodeError:
                logger.warning(
                    "Invalid API_KEYS JSON in env var, using default value (none)"
                )

        # Capsule settings
        self.DEFAULT_CAPSULE_VERSION = os.getenv(
            "UATP_DEFAULT_CAPSULE_VERSION", self.DEFAULT_CAPSULE_VERSION
        )

        if os.getenv("UATP_SUPPORTED_CAPSULE_VERSIONS"):
            try:
                versions = json.loads(os.getenv("UATP_SUPPORTED_CAPSULE_VERSIONS"))
                self.SUPPORTED_CAPSULE_VERSIONS = set(versions)
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    "Invalid SUPPORTED_CAPSULE_VERSIONS, using default value"
                )

        # Logging settings
        self.LOG_LEVEL = os.getenv("UATP_LOG_LEVEL", self.LOG_LEVEL).upper()
        self.LOG_FORMAT = os.getenv("UATP_LOG_FORMAT", self.LOG_FORMAT)

    def _load_from_config_file(self):
        """Load settings from environment-specific config file."""
        config_file = Path(f"config/{self.ENVIRONMENT.value}.json")

        if not config_file.exists():
            logger.info(f"No config file found at {config_file}")
            return

        try:
            with open(config_file) as f:
                config = json.load(f)

            # Update settings from config
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)

            logger.info(f"Loaded settings from {config_file}")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse config file: {config_file}")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")

    def _validate_settings(self):
        """Validate settings to ensure they're in acceptable ranges and formats."""
        # Validate numeric settings
        if self.MAX_CHAIN_SIZE <= 0:
            logger.warning(
                "Invalid MAX_CHAIN_SIZE, must be positive. Using default value."
            )
            self.MAX_CHAIN_SIZE = 10000

        if self.API_PORT < 1 or self.API_PORT > 65535:
            logger.warning(
                "Invalid API_PORT, must be between 1-65535. Using default value."
            )
            self.API_PORT = 8000

        if self.RATE_LIMIT <= 0:
            logger.warning("Invalid RATE_LIMIT, must be positive. Using default value.")
            self.RATE_LIMIT = 100

        # Validate capsule version settings
        if self.DEFAULT_CAPSULE_VERSION not in self.SUPPORTED_CAPSULE_VERSIONS:
            logger.error(
                f"Default capsule version {self.DEFAULT_CAPSULE_VERSION} is not in supported versions"
            )
            self.DEFAULT_CAPSULE_VERSION = list(self.SUPPORTED_CAPSULE_VERSIONS)[0]
            logger.info(
                f"Using {self.DEFAULT_CAPSULE_VERSION} as default capsule version instead"
            )

        # Validate logging level
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.LOG_LEVEL not in valid_log_levels:
            logger.warning(f"Invalid LOG_LEVEL '{self.LOG_LEVEL}', using INFO instead")
            self.LOG_LEVEL = "INFO"

    def _process_settings(self):
        """Process and transform settings as needed after loading."""
        # Create storage directory if it doesn't exist
        self.STORAGE_DIR.mkdir(parents=True, exist_ok=True)

        # Convert string paths to Path objects
        if isinstance(self.STORAGE_DIR, str):
            self.STORAGE_DIR = Path(self.STORAGE_DIR)

    def as_dict(self) -> Dict[str, Any]:
        """Return all settings as a dictionary."""
        return {
            key: value
            for key, value in self.__dict__.items()
            if key.isupper() and not key.startswith("_")
        }

    def __str__(self) -> str:
        """Return settings as a formatted string."""
        settings_dict = self.as_dict()
        return json.dumps(
            {k: str(v) if isinstance(v, Path) else v for k, v in settings_dict.items()},
            indent=2,
        )


# Create a singleton instance
settings = Settings()

# Export as module-level constants for ease of use
ENVIRONMENT = settings.ENVIRONMENT
DEBUG = settings.DEBUG
STORAGE_DIR = settings.STORAGE_DIR
COMPRESSED_STORAGE = settings.COMPRESSED_STORAGE
MAX_CHAIN_SIZE = settings.MAX_CHAIN_SIZE
API_HOST = settings.API_HOST
API_PORT = settings.API_PORT
RATE_LIMIT = settings.RATE_LIMIT
CORS_ORIGINS = settings.CORS_ORIGINS
DEFAULT_CAPSULE_VERSION = settings.DEFAULT_CAPSULE_VERSION
SUPPORTED_CAPSULE_VERSIONS = settings.SUPPORTED_CAPSULE_VERSIONS
LOG_LEVEL = settings.LOG_LEVEL
LOG_FORMAT = settings.LOG_FORMAT


def _is_placeholder_secret(value: str) -> bool:
    """Check if a secret value is a placeholder that should not be used."""
    if not value:
        return True
    placeholder_patterns = [
        "CHANGE_ME",
        "change_me",
        "your-",
        "YOUR_",
        "placeholder",
        "PLACEHOLDER",
        "example",
        "EXAMPLE",
        "xxx",
        "XXX",
        "dev-only",
        "test-only",
    ]
    return any(pattern in value for pattern in placeholder_patterns)


def validate_production_secrets():
    """
    Validate all secrets are properly configured for production environment.

    SECURITY: This function rejects placeholder secrets to prevent accidental
    deployment with insecure defaults. The application will refuse to start
    in production if any secrets contain placeholder patterns.

    Raises:
        RuntimeError: If production validation fails
    """
    env = os.getenv("UATP_ENV", os.getenv("ENVIRONMENT", "development"))

    if env in ("production", "prod", "staging"):
        errors = []

        # Check CSRF secret
        csrf_secret = os.getenv("CSRF_SECRET_KEY", "")
        if not csrf_secret:
            errors.append("CSRF_SECRET_KEY must be set in production")
        elif _is_placeholder_secret(csrf_secret):
            errors.append(
                "CSRF_SECRET_KEY contains placeholder value - generate with: "
                'python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )
        elif len(csrf_secret) < 32:
            errors.append(
                "CSRF_SECRET_KEY must be at least 32 characters in production"
            )

        # Check JWT secret
        jwt_secret = os.getenv("JWT_SECRET", os.getenv("JWT_SECRET_KEY", ""))
        if not jwt_secret:
            errors.append("JWT_SECRET must be set in production")
        elif _is_placeholder_secret(jwt_secret):
            errors.append(
                "JWT_SECRET contains placeholder value - generate with: "
                'python -c "import secrets; print(secrets.token_urlsafe(64))"'
            )
        elif len(jwt_secret) < 32:
            errors.append("JWT_SECRET must be at least 32 characters in production")

        # Check encryption key
        encryption_key = os.getenv("ENCRYPTION_KEY", "")
        if not encryption_key:
            errors.append("ENCRYPTION_KEY must be set in production")
        elif _is_placeholder_secret(encryption_key):
            errors.append(
                "ENCRYPTION_KEY contains placeholder value - generate with: "
                'python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )

        # Check database password
        db_password = os.getenv("DB_PASSWORD", "")
        if _is_placeholder_secret(db_password):
            errors.append(
                "DB_PASSWORD contains placeholder value - generate with: "
                "openssl rand -base64 32"
            )

        # Check Redis password
        redis_password = os.getenv("REDIS_PASSWORD", "")
        if _is_placeholder_secret(redis_password):
            errors.append(
                "REDIS_PASSWORD contains placeholder value - generate with: "
                "openssl rand -base64 32"
            )

        # Check ALLOWED_HOSTS is set
        allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
        if not allowed_hosts:
            errors.append(
                "ALLOWED_HOSTS must be set in production - set to your domain(s)"
            )

        # If there are errors, raise RuntimeError
        if errors:
            error_msg = (
                "SECURITY: Production secret validation failed!\n"
                "The application cannot start with placeholder or missing secrets.\n\n"
                + "\n".join(f"  - {err}" for err in errors)
            )
            raise RuntimeError(error_msg)
