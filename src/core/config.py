import os

# Project Settings
PROJECT_NAME: str = "UATP Capsule Engine"
API_V1_STR: str = "/api/v1"

# Environment Configuration
# Determines if we are in a production or development environment.
# Defaults to 'development' if not set.
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Database Settings
if ENVIRONMENT == "production":
    # In production, connect to a PostgreSQL database using environment variables.
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv(
        "POSTGRES_HOST", "db"
    )  # 'db' is a common Docker Compose service name
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB")

    if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
        raise ValueError(
            "In production, POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB must be set."
        )

    DATABASE_URL = (
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
        f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
else:
    # In development, use a local SQLite database.
    # The DATABASE_URL can still be overridden by an environment variable.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./uatp_dev.db")
