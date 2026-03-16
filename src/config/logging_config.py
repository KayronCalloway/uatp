"""
Logging configuration for UATP Capsule Engine.

This module centralizes all logging configuration settings and provides
functions to configure loggers consistently across the application.
"""

import json
import logging
import os
from typing import Optional

from src.utils.timezone_utils import utc_now


class StructuredLogFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    Creates consistent JSON-formatted logs with metadata for better observability.
    """

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        log_data = {
            "timestamp": utc_now().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }

        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record if they exist
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint

        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        # Add extra data if provided
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            for key, value in record.extra_data.items():
                if key not in log_data:
                    log_data[key] = value

        return json.dumps(log_data)


# Default log levels
DEFAULT_APP_LOG_LEVEL = "INFO"
DEFAULT_DEV_LOG_LEVEL = "DEBUG"
DEFAULT_CACHE_LOG_LEVEL = "INFO"
DEFAULT_ENGINE_LOG_LEVEL = "INFO"
DEFAULT_API_LOG_LEVEL = "INFO"

# Log format settings
DEFAULT_LOG_FORMAT = (
    "[%(asctime)s] [%(levelname)s] [%(module)s:%(funcName)s:%(lineno)d] %(message)s"
)
JSON_LOG_FORMAT = None  # Uses StructuredLogFormatter from api.logger

# Environment-based settings
ENV_SETTINGS = {
    "production": {
        "log_level": "INFO",
        "structured_logs": True,
        "log_to_file": True,
    },
    "staging": {
        "log_level": "INFO",
        "structured_logs": True,
        "log_to_file": True,
    },
    "development": {
        "log_level": "DEBUG",
        "structured_logs": False,
        "log_to_file": False,
    },
    "testing": {
        "log_level": "DEBUG",
        "structured_logs": False,
        "log_to_file": False,
    },
}


def get_environment() -> str:
    """Get the current environment name from environment variable."""
    return os.getenv("FLASK_ENV", "development").lower()


def get_log_level(logger_name: str = "app") -> int:
    """
    Get the appropriate log level based on environment variables and defaults.

    Args:
        logger_name: Name of the logger to get level for ('app', 'cache', 'engine', 'api')

    Returns:
        The log level as an integer
    """
    env = get_environment()
    env_settings = ENV_SETTINGS.get(env, ENV_SETTINGS["development"])

    # Get environment variable name for this logger
    env_var_name = f"UATP_{logger_name.upper()}_LOG_LEVEL"

    # Get default for this logger type
    if logger_name == "cache":
        default_level = DEFAULT_CACHE_LOG_LEVEL
    elif logger_name == "engine":
        default_level = DEFAULT_ENGINE_LOG_LEVEL
    elif logger_name == "api":
        default_level = DEFAULT_API_LOG_LEVEL
    else:
        default_level = env_settings["log_level"]

    # Get log level name from environment or default
    log_level_name = os.getenv(env_var_name, default_level).upper()

    # Convert to integer log level
    return getattr(logging, log_level_name, logging.INFO)


def should_use_structured_logs() -> bool:
    """Determine if structured (JSON) logs should be used."""
    env = get_environment()
    env_settings = ENV_SETTINGS.get(env, ENV_SETTINGS["development"])

    # Environment variable override
    env_setting = os.getenv(
        "UATP_STRUCTURED_LOGS", str(env_settings["structured_logs"])
    ).lower()
    return env_setting in ("true", "1", "yes", "t")


def should_log_to_file() -> bool:
    """Determine if logs should also be written to file."""
    env = get_environment()
    env_settings = ENV_SETTINGS.get(env, ENV_SETTINGS["development"])

    # Environment variable override
    env_setting = os.getenv(
        "UATP_LOG_TO_FILE", str(env_settings["log_to_file"])
    ).lower()
    return env_setting in ("true", "1", "yes", "t")


def get_log_file_path(logger_name: str = "app") -> str:
    """Get the log file path for a given logger."""
    log_dir = os.getenv("UATP_LOG_DIR", "logs")

    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    return os.path.join(log_dir, f"{logger_name}.log")


def configure_logger(
    logger_name: str,
    log_level: Optional[int] = None,
    structured: Optional[bool] = None,
    log_to_file: Optional[bool] = None,
) -> logging.Logger:
    """
    Configure a logger with consistent settings.

    Args:
        logger_name: Name of the logger
        log_level: Override the log level
        structured: Override structured log setting
        log_to_file: Override file logging setting

    Returns:
        Configured logger
    """
    # Get logger instance
    logger = logging.getLogger(logger_name)

    # Clear existing handlers
    if logger.handlers:
        logger.handlers = []

    # Set log level
    if log_level is None:
        log_level = get_log_level(logger_name)
    logger.setLevel(log_level)

    # Determine if using structured logs
    if structured is None:
        structured = should_use_structured_logs()

    # Determine if logging to file
    if log_to_file is None:
        log_to_file = should_log_to_file()

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # Set formatter based on structured log setting
    if structured:
        formatter = StructuredLogFormatter()
    else:
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler if needed
    if log_to_file:
        file_handler = logging.FileHandler(get_log_file_path(logger_name))
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
