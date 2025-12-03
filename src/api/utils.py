"""Utility functions for the UATP API.

Provides common helpers for API utility functions.

This module contains utility functions for the API endpoints.
"""

import base64
import json
import logging
import zlib
from typing import Any, Dict

from src.engine.exceptions import (
    UATPEngineError,
)
from flask import jsonify


def create_error_response(
    error: Exception, error_type: str, status_code: int = 400
) -> tuple:
    """Create a standardized error response.

    Args:
        error: The exception that was raised
        error_type: Type of error (e.g., 'invalid_request', 'validation_error')
        status_code: HTTP status code to return

    Returns:
        A tuple of (response_json, status_code) for Flask to return
    """
    return (
        jsonify({"status": "error", "error": str(error), "error_type": error_type}),
        status_code,
    )


def handle_api_exception(e: Exception, logger: logging.Logger, context: str) -> tuple:
    """Handle exceptions in API endpoints with consistent logging and responses.

    Args:
        e: The exception that was raised
        logger: Logger instance to use for logging
        context: Context string for logging (e.g., 'creating remix capsule')

    Returns:
        A tuple of (response_json, status_code) for Flask to return
    """
    from src.engine.exceptions import (
        CapsuleLoggingError,
        InvalidCapsuleParameterError,
        InvalidRequestError,
        ValidationError,
    )

    if isinstance(e, InvalidRequestError):
        logger.warning(f"Invalid request when {context}: {e}")
        return create_error_response(e, "invalid_request", 400)

    if isinstance(e, InvalidCapsuleParameterError):
        logger.warning(f"Invalid parameter when {context}: {e}")
        return create_error_response(e, "invalid_parameter", 400)

    if isinstance(e, ValidationError):
        logger.warning(f"Validation error when {context}: {e}")
        return create_error_response(e, "validation_error", 400)

    if isinstance(e, CapsuleSigningError):
        logger.error(f"Signing error when {context}: {e}")
        return create_error_response("Failed to sign capsule", "signing_error", 500)

    if isinstance(e, CapsuleLoggingError):
        logger.error(f"Logging error when {context}: {e}")
        return create_error_response("Failed to log capsule", "logging_error", 500)

    if isinstance(e, UATPEngineError):
        logger.error(f"Engine error when {context}: {e}")
        return create_error_response(e, "engine_error", 500)

    # Fallback for unexpected exceptions
    logger.error(f"Unexpected error when {context}: {e}", exc_info=True)
    return create_error_response("Unexpected error occurred", "unexpected_error", 500)


def decompress_capsule(capsule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decompress a capsule if it's compressed.

    Args:
        capsule_data: Possibly compressed capsule data

    Returns:
        Decompressed capsule data
    """
    if capsule_data.get("compressed") and capsule_data.get("data"):
        # Decompress the data
        compressed_data = base64.b64decode(capsule_data["data"])
        decompressed_data = zlib.decompress(compressed_data)
        return json.loads(decompressed_data)
    return capsule_data
