import os

# Project Settings
PROJECT_NAME: str = "UATP Capsule Engine"
API_V1_STR: str = "/api/v1"

# Environment Configuration
# Determines if we are in a production or development environment.
# Defaults to 'development' if not set.
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Database Settings
# Supports both naming conventions for flexibility:
#   - DB_* (docker-compose convention, takes precedence)
#   - POSTGRES_* (legacy/alternative convention)
if ENVIRONMENT == "production":
    # In production, connect to a PostgreSQL database using environment variables.
    # Accept both DB_* (docker-compose) and POSTGRES_* (legacy) naming
    POSTGRES_USER = os.getenv("DB_USERNAME") or os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB")

    if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
        raise ValueError(
            "In production, database credentials must be set. "
            "Use either DB_USERNAME/DB_PASSWORD/DB_NAME or POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_DB."
        )

    DATABASE_URL = (
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
else:
    # In development, use a local SQLite database.
    # The DATABASE_URL can still be overridden by an environment variable.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./uatp_dev.db")
