"""
Enhanced Configuration Management for UATP Capsule Engine

Provides production-ready configuration management with validation, secrets handling,
environment-specific settings, and integration with dependency injection.

Features:
- Pydantic-based validation and type safety
- Environment-specific configuration
- Secrets management integration
- Configuration hot-reloading
- Health checks for configuration validity
- Logging configuration
- Database and external service configuration
- Security and authentication settings
- Performance and scaling configuration
"""

import json
import os
import secrets
from datetime import timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from functools import lru_cache

from pydantic import Field, field_validator, SecretStr, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
import structlog

logger = structlog.get_logger("uatp.config")


class Environment(str, Enum):
    """Application environment types"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging level options"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseType(str, Enum):
    """Supported database types"""

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class CacheType(str, Enum):
    """Supported cache types"""

    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"


class AuthSettings(BaseSettings):
    """Authentication and security settings"""

    # JWT Configuration
    jwt_secret_key: SecretStr = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="JWT signing secret key",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    jwt_access_token_expire_minutes: int = Field(
        default=30, ge=5, le=1440, description="Access token expiry in minutes"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, ge=1, le=30, description="Refresh token expiry in days"
    )

    # Password Policy
    password_min_length: int = Field(default=8, ge=6, le=128)
    password_require_uppercase: bool = Field(default=True)
    password_require_lowercase: bool = Field(default=True)
    password_require_numbers: bool = Field(default=True)
    password_require_special: bool = Field(default=True)

    # Account Security
    max_login_attempts: int = Field(default=5, ge=3, le=10)
    lockout_duration_minutes: int = Field(default=15, ge=5, le=60)
    require_email_verification: bool = Field(default=True)
    max_concurrent_sessions: int = Field(default=3, ge=1, le=10)
    session_timeout_minutes: int = Field(default=60, ge=15, le=1440)

    # API Security
    api_key_length: int = Field(default=32, ge=16, le=64)
    rate_limit_per_minute: int = Field(default=100, ge=10, le=10000)
    cors_allowed_origins: List[str] = Field(
        default_factory=lambda: ["https://uatp.app"], description="CORS allowed origins"
    )
    cors_allow_credentials: bool = Field(default=True)

    # Security Headers
    enable_hsts: bool = Field(default=True)
    hsts_max_age: int = Field(default=31536000)  # 1 year
    enable_csp: bool = Field(default=True)
    csp_policy: str = Field(
        default="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    )

    model_config = SettingsConfigDict(env_prefix="AUTH_")


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""

    # Database Connection
    database_type: DatabaseType = Field(default=DatabaseType.POSTGRESQL)
    database_url: Optional[str] = Field(default=None, description="Full database URL")
    database_host: str = Field(default="localhost")
    database_port: int = Field(default=5432, ge=1, le=65535)
    database_name: str = Field(default="uatp_capsule_engine")
    database_username: str = Field(default="uatp_user")
    database_password: SecretStr = Field(default="changeme")

    # Connection Pool Settings
    database_pool_size: int = Field(default=20, ge=1, le=100)
    database_max_overflow: int = Field(default=30, ge=0, le=100)
    database_pool_timeout: int = Field(default=30, ge=5, le=300)
    database_pool_recycle: int = Field(default=3600, ge=300, le=86400)

    # Query Settings
    database_echo_sql: bool = Field(default=False)
    database_query_timeout: int = Field(default=30, ge=5, le=300)

    # Migration Settings
    run_migrations_on_startup: bool = Field(default=True)
    create_tables_on_startup: bool = Field(default=False)

    @field_validator("database_url", mode="before")
    @classmethod
    def build_database_url(cls, v, info: ValidationInfo):
        """Build database URL from components if not provided"""
        if v:
            return v

        db_type = info.data.get("database_type", DatabaseType.POSTGRESQL)
        username = info.data.get("database_username", "uatp_user")
        password = info.data.get("database_password", "changeme")
        host = info.data.get("database_host", "localhost")
        port = info.data.get("database_port", 5432)
        name = info.data.get("database_name", "uatp_capsule_engine")

        if db_type == DatabaseType.POSTGRESQL:
            return f"postgresql://{username}:{password}@{host}:{port}/{name}"
        elif db_type == DatabaseType.MYSQL:
            return f"mysql://{username}:{password}@{host}:{port}/{name}"
        elif db_type == DatabaseType.SQLITE:
            return f"sqlite:///./{name}.db"

        return None

    model_config = SettingsConfigDict(env_prefix="DB_")


class CacheSettings(BaseSettings):
    """Cache configuration settings"""

    # Cache Type and Connection
    cache_type: CacheType = Field(default=CacheType.REDIS)
    cache_url: Optional[str] = Field(default=None, description="Full cache URL")
    cache_host: str = Field(default="localhost")
    cache_port: int = Field(default=6379, ge=1, le=65535)
    cache_database: int = Field(default=0, ge=0, le=15)
    cache_password: Optional[SecretStr] = Field(default=None)

    # Cache Settings
    cache_default_ttl: int = Field(default=3600, ge=60, le=86400)  # 1 hour
    cache_max_memory: str = Field(default="256mb")
    cache_eviction_policy: str = Field(default="allkeys-lru")

    # Connection Pool
    cache_pool_size: int = Field(default=10, ge=1, le=100)
    cache_pool_timeout: int = Field(default=5, ge=1, le=30)

    @field_validator("cache_url", mode="before")
    @classmethod
    def build_cache_url(cls, v, info: ValidationInfo):
        """Build cache URL from components if not provided"""
        if v:
            return v

        cache_type = info.data.get("cache_type", CacheType.REDIS)
        if cache_type != CacheType.REDIS:
            return None

        host = info.data.get("cache_host", "localhost")
        port = info.data.get("cache_port", 6379)
        database = info.data.get("cache_database", 0)
        password = info.data.get("cache_password")

        if password:
            return f"redis://:{password.get_secret_value()}@{host}:{port}/{database}"
        else:
            return f"redis://{host}:{port}/{database}"

    model_config = SettingsConfigDict(env_prefix="CACHE_")


class AIServiceSettings(BaseSettings):
    """AI service configuration"""

    # Provider API Keys
    openai_api_key: Optional[SecretStr] = Field(default=None)
    anthropic_api_key: Optional[SecretStr] = Field(default=None)
    google_api_key: Optional[SecretStr] = Field(default=None)
    cohere_api_key: Optional[SecretStr] = Field(default=None)

    # Service Configuration
    default_ai_provider: str = Field(default="openai")
    max_tokens_per_request: int = Field(default=4000, ge=100, le=32000)
    request_timeout_seconds: int = Field(default=30, ge=5, le=300)

    # Rate Limiting
    ai_requests_per_minute: int = Field(default=60, ge=1, le=1000)
    ai_requests_per_day: int = Field(default=10000, ge=100, le=1000000)

    # Circuit Breaker Settings
    ai_failure_threshold: int = Field(default=5, ge=2, le=20)
    ai_recovery_timeout_seconds: int = Field(default=60, ge=10, le=300)

    model_config = SettingsConfigDict(env_prefix="AI_")


class MonitoringSettings(BaseSettings):
    """Monitoring and observability settings"""

    # Metrics
    enable_metrics: bool = Field(default=True)
    metrics_endpoint: str = Field(default="/metrics")
    prometheus_port: int = Field(default=9090, ge=1, le=65535)

    # Logging
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_format: str = Field(default="json", pattern="^(json|text)$")
    log_file: Optional[str] = Field(default=None)
    log_max_size: str = Field(default="10MB")
    log_backup_count: int = Field(default=5, ge=1, le=10)

    # Health Checks
    health_check_interval_seconds: int = Field(default=30, ge=5, le=300)
    health_check_timeout_seconds: int = Field(default=5, ge=1, le=30)

    # Tracing
    enable_tracing: bool = Field(default=False)
    jaeger_endpoint: Optional[str] = Field(default=None)
    trace_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)

    # Alerts
    enable_alerts: bool = Field(default=True)
    alert_webhook_url: Optional[str] = Field(default=None)
    error_threshold_per_minute: int = Field(default=10, ge=1, le=1000)

    model_config = SettingsConfigDict(env_prefix="MONITORING_")


class PerformanceSettings(BaseSettings):
    """Performance and scaling settings"""

    # API Performance
    api_max_request_size: int = Field(
        default=10485760, ge=1048576, le=104857600
    )  # 10MB
    api_max_concurrent_requests: int = Field(default=1000, ge=10, le=10000)
    api_timeout_seconds: int = Field(default=30, ge=5, le=300)

    # Worker Configuration
    worker_processes: int = Field(default=4, ge=1, le=32)
    worker_threads: int = Field(default=1, ge=1, le=8)
    worker_max_requests: int = Field(default=1000, ge=100, le=10000)
    worker_timeout_seconds: int = Field(default=30, ge=5, le=300)

    # Background Tasks
    task_queue_size: int = Field(default=1000, ge=10, le=10000)
    task_worker_concurrency: int = Field(default=10, ge=1, le=100)
    task_retry_attempts: int = Field(default=3, ge=0, le=10)

    # Memory Management
    max_memory_usage_mb: int = Field(default=1024, ge=128, le=8192)
    garbage_collection_threshold: int = Field(default=1000, ge=100, le=10000)

    model_config = SettingsConfigDict(env_prefix="PERFORMANCE_")


class UATPSettings(BaseSettings):
    """Main UATP application settings"""

    # Application
    app_name: str = Field(default="UATP Capsule Engine")
    app_version: str = Field(default="7.1.0")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    reload: bool = Field(default=False)

    # Storage
    storage_dir: Path = Field(default=Path("./storage"))
    max_file_size_mb: int = Field(default=100, ge=1, le=1000)

    # Capsule Configuration
    default_capsule_version: str = Field(default="7.1")
    supported_capsule_versions: Set[str] = Field(default={"6.0", "7.0", "7.1"})
    max_capsule_chain_length: int = Field(default=10000, ge=100, le=1000000)

    # Feature Flags
    enable_ai_attribution: bool = Field(default=True)
    enable_economic_engine: bool = Field(default=True)
    enable_governance: bool = Field(default=True)
    enable_insurance: bool = Field(default=False)

    # Nested Settings
    auth: AuthSettings = Field(default_factory=AuthSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    ai_services: AIServiceSettings = Field(default_factory=AIServiceSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)

    @field_validator("storage_dir", mode="before")
    @classmethod
    def create_storage_dir(cls, v):
        """Ensure storage directory exists"""
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("debug", mode="before")
    @classmethod
    def set_debug_based_on_environment(cls, v, info: ValidationInfo):
        """Set debug mode based on environment"""
        env = info.data.get("environment", Environment.DEVELOPMENT)
        if env == Environment.DEVELOPMENT:
            return True
        elif env == Environment.PRODUCTION:
            return False
        return v

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT

    def get_cors_origins(self) -> List[str]:
        """Get CORS origins based on environment"""
        if self.is_development():
            return self.auth.cors_allowed_origins + [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://127.1.0.1:3000",
                "http://127.1.0.1:8080",
            ]
        return self.auth.cors_allowed_origins

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration and return validation results"""
        results = {"valid": True, "errors": [], "warnings": []}

        # Check required fields for production
        if self.is_production():
            if not self.auth.jwt_secret_key.get_secret_value():
                results["errors"].append("JWT secret key is required in production")
                results["valid"] = False

            if self.database.database_password.get_secret_value() == "changeme":
                results["errors"].append(
                    "Default database password should be changed in production"
                )
                results["valid"] = False

            if self.debug:
                results["warnings"].append("Debug mode is enabled in production")

        # Check AI service configuration
        if self.enable_ai_attribution:
            if not any(
                [
                    self.ai_services.openai_api_key,
                    self.ai_services.anthropic_api_key,
                    self.ai_services.google_api_key,
                ]
            ):
                results["warnings"].append("No AI service API keys configured")

        return results

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> UATPSettings:
    """Get cached settings instance"""
    return UATPSettings()


def validate_settings() -> Dict[str, Any]:
    """Validate current settings"""
    settings = get_settings()
    return settings.validate_configuration()


def reload_settings():
    """Reload settings (clear cache)"""
    get_settings.cache_clear()
    logger.info("Settings cache cleared and reloaded")


# Configuration health check
async def configuration_health_check() -> Dict[str, Any]:
    """Perform health check on configuration"""
    try:
        settings = get_settings()
        validation_results = settings.validate_configuration()

        return {
            "status": "healthy" if validation_results["valid"] else "unhealthy",
            "environment": settings.environment.value,
            "validation": validation_results,
            "features": {
                "ai_attribution": settings.enable_ai_attribution,
                "economic_engine": settings.enable_economic_engine,
                "governance": settings.enable_governance,
                "insurance": settings.enable_insurance,
            },
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# Environment-specific configuration files
def load_environment_config(environment: Environment) -> Dict[str, Any]:
    """Load environment-specific configuration from file"""
    config_file = Path(f"config/{environment.value}.json")

    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_file}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")

    return {}


# Example configuration templates
EXAMPLE_CONFIGS = {
    Environment.DEVELOPMENT: {
        "debug": True,
        "database__database_url": "sqlite:///./development.db",
        "cache__cache_type": "memory",
        "monitoring__log_level": "DEBUG",
        "auth__require_email_verification": False,
    },
    Environment.PRODUCTION: {
        "debug": False,
        "database__database_type": "postgresql",
        "cache__cache_type": "redis",
        "monitoring__log_level": "INFO",
        "monitoring__enable_metrics": True,
        "auth__require_email_verification": True,
        "performance__worker_processes": 4,
    },
}


def create_example_config(environment: Environment, output_file: Optional[Path] = None):
    """Create example configuration file for environment"""
    config = EXAMPLE_CONFIGS.get(environment, {})

    if output_file is None:
        output_file = Path(f"config/{environment.value}.example.json")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(config, f, indent=2)

    logger.info(f"Created example configuration at {output_file}")


# Export main settings instance
settings = get_settings()
