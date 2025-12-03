"""Logging configuration for UATP Capsule Engine API.

This module configures structured logging for the API with different log levels
and formatting for development and production environments.
"""

import logging
import os

from src.config.logging_config import StructuredLogFormatter


def configure_logging(app_name: str = "uatp_capsule_engine") -> logging.Logger:
    """Configure logging for the application.

    Args:
        app_name: The name of the application for the logger

    Returns:
        The configured logger
    """
    logger = logging.getLogger(app_name)

    # Clear existing handlers if any
    if logger.handlers:
        logger.handlers = []

    # Set log level based on environment
    env = os.getenv("FLASK_ENV", "development")
    log_level_name = os.getenv("LOG_LEVEL", "INFO" if env == "production" else "DEBUG")
    log_level = getattr(logging, log_level_name)
    logger.setLevel(log_level)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # Use JSON formatter for production, more readable format for development
    if env == "production":
        formatter = StructuredLogFormatter()
    else:
        format_str = "[%(asctime)s] [%(levelname)s] [%(module)s:%(funcName)s:%(lineno)d] %(message)s"
        if os.getenv("STRUCTURED_LOGS", "false").lower() == "true":
            formatter = StructuredLogFormatter()
        else:
            formatter = logging.Formatter(format_str)

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
