"""
secrets.py - Centralized secrets management for UATP Capsule Engine.

This module provides secure access to sensitive configuration data, including API keys,
private signing keys, and other credentials. It implements best practices for secrets
management:

1. No hardcoded secrets
2. Environment variable validation
3. Clear error messages for missing required secrets
4. Typed return values with proper validation
5. Audit logging for secret access
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Configure logger
logger = logging.getLogger("uatp.secrets")


class SecretNotFoundError(Exception):
    """Exception raised when a required secret is not available."""

    pass


class SecretValidationError(Exception):
    """Exception raised when a secret fails validation."""

    pass


# Define environment variable names for all secrets
ENV_API_KEYS = "UATP_API_KEYS"
ENV_ED25519_PRIVATE_KEY = "UATP_ED25519_PRIVATE_KEY"
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"

# Define secrets file path (alternative to environment variables)
DEFAULT_SECRETS_FILE = Path(os.path.expanduser("~/.uatp/secrets.json"))


def _load_secrets_from_file(filepath: Path = DEFAULT_SECRETS_FILE) -> Dict[str, Any]:
    """Load secrets from a JSON file."""
    if not filepath.exists():
        logger.warning(f"Secrets file not found: {filepath}")
        return {}

    try:
        with open(filepath) as f:
            secrets = json.load(f)
        logger.info(f"Loaded secrets from {filepath}")
        return secrets
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse secrets file: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading secrets file: {e}")
        return {}


def get_api_keys() -> Dict[str, Dict[str, Union[str, List[str]]]]:
    """
    Get API keys configuration from the UATP_API_KEYS environment variable.

    The environment variable should contain a valid JSON string.

    Returns:
        A dictionary of API keys and their configurations.

    Raises:
        SecretNotFoundError: If the environment variable is not set or empty.
        SecretValidationError: If the environment variable is not a valid JSON string
                               or the key structure is invalid.
    """
    api_keys_json = os.getenv(ENV_API_KEYS)
    if not api_keys_json:
        error_msg = f"{ENV_API_KEYS} environment variable not set. Please configure it in your .env file."
        logger.error(error_msg)
        raise SecretNotFoundError(error_msg)

    try:
        api_keys = json.loads(api_keys_json)
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse {ENV_API_KEYS}. Ensure it is a valid JSON string. Error: {e}"
        logger.error(error_msg)
        raise SecretValidationError(error_msg) from e

    # Validate the loaded API keys structure
    valid_keys = {}
    if isinstance(api_keys, dict):
        for key, config in api_keys.items():
            if isinstance(config, dict) and "roles" in config:
                if isinstance(config["roles"], list):
                    valid_keys[key] = config
                else:
                    logger.warning(
                        f"API key '{key}' has invalid 'roles' format (must be a list), skipping."
                    )
            else:
                logger.warning(
                    f"API key '{key}' has invalid configuration format (must be a dict with 'roles'), skipping."
                )

    if not valid_keys:
        error_msg = "No valid API keys found after validation. Check the structure in your .env file."
        logger.error(error_msg)
        raise SecretValidationError(error_msg)

    logger.info(
        f"Successfully loaded {len(valid_keys)} valid API key(s) from environment."
    )
    return valid_keys


def get_ed25519_private_key() -> str:
    """
    Get Ed25519 private key for capsule signing from the environment.

    Raises:
        SecretNotFoundError: If the key is not configured.

    Returns:
        str: Hex-encoded private key.
    """
    key = os.getenv(ENV_ED25519_PRIVATE_KEY)
    if key and len(key) >= 64:  # Ed25519 keys are 32 bytes (64 hex characters)
        logger.info("Successfully loaded Ed25519 private key from environment.")
        return key

    error_msg = f"{ENV_ED25519_PRIVATE_KEY} not configured or invalid. Set it in your .env file."
    logger.error(error_msg)
    raise SecretNotFoundError(error_msg)


def get_openai_api_key() -> str:
    """
    Get OpenAI API key from the environment.

    Raises:
        SecretNotFoundError: If the key is not configured.

    Returns:
        str: OpenAI API key.
    """
    key = os.getenv(ENV_OPENAI_API_KEY)
    if key and key.startswith("sk-") and len(key) > 20:
        logger.info("Successfully loaded OpenAI API key from environment.")
        return key

    error_msg = (
        f"{ENV_OPENAI_API_KEY} not configured or invalid. Set it in your .env file."
    )
    logger.error(error_msg)
    raise SecretNotFoundError(error_msg)


def generate_sample_secrets_file(filepath: Optional[Path] = None) -> Path:
    """
    Generate a sample secrets file template.

    Args:
        filepath: Optional custom path for the secrets file

    Returns:
        Path: The path to the generated file
    """
    if filepath is None:
        filepath = Path(os.path.expanduser("~/.uatp/secrets.template.json"))

    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    sample_secrets = {
        "api_keys": {
            "sample-key-1": {"name": "Development API Key", "roles": ["read", "write"]},
            "sample-key-2": {"name": "Read-only API Key", "roles": ["read"]},
        },
        "ed25519_private_key": "YOUR_PRIVATE_KEY_HERE",
        "openai_api_key": "sk-YOUR_OPENAI_API_KEY_HERE",
    }

    with open(filepath, "w") as f:
        json.dump(sample_secrets, f, indent=2)

    logger.info(f"Generated sample secrets file at {filepath}")
    return filepath
