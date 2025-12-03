"""
Cache configuration and settings management for UATP Capsule Engine.

This module provides centralized configuration management for all caching-related
settings, including cache sizes, TTLs, and feature flags.
"""

import logging
import os

logger = logging.getLogger("uatp_api.cache")

# Default settings
DEFAULT_CACHE_SIZE = 1000
DEFAULT_CACHE_ENABLED = True
DEFAULT_CHAIN_TTL_SECONDS = 60
DEFAULT_VERIFICATION_TTL_SECONDS = 300
DEFAULT_STATS_TTL_SECONDS = 120
DEFAULT_FORKS_TTL_SECONDS = 300
DEFAULT_GENERAL_TTL_SECONDS = 60
DEFAULT_AI_CACHE_TTL_SECONDS = 900

# Load settings from environment variables
try:
    # Cache size and general settings
    CACHE_SIZE = int(os.getenv("UATP_CACHE_SIZE", DEFAULT_CACHE_SIZE))
    CACHE_ENABLED = os.getenv("UATP_CACHE_ENABLED", "true").lower() in (
        "true",
        "1",
        "t",
        "yes",
    )

    # TTL settings for different cache types
    CHAIN_TTL_SECONDS = int(
        os.getenv("UATP_CHAIN_CACHE_TTL", DEFAULT_CHAIN_TTL_SECONDS)
    )
    VERIFICATION_TTL_SECONDS = int(
        os.getenv("UATP_VERIFICATION_CACHE_TTL", DEFAULT_VERIFICATION_TTL_SECONDS)
    )
    STATS_TTL_SECONDS = int(
        os.getenv("UATP_STATS_CACHE_TTL", DEFAULT_STATS_TTL_SECONDS)
    )
    FORKS_TTL_SECONDS = int(
        os.getenv("UATP_FORKS_CACHE_TTL", DEFAULT_FORKS_TTL_SECONDS)
    )
    GENERAL_TTL_SECONDS = int(
        os.getenv("UATP_GENERAL_CACHE_TTL", DEFAULT_GENERAL_TTL_SECONDS)
    )
    AI_CACHE_TTL_SECONDS = int(
        os.getenv("UATP_AI_CACHE_TTL", DEFAULT_AI_CACHE_TTL_SECONDS)
    )

    logger.info(f"Cache settings loaded: size={CACHE_SIZE}, enabled={CACHE_ENABLED}")
    logger.debug(
        f"Cache TTL settings: chain={CHAIN_TTL_SECONDS}s, "
        f"verification={VERIFICATION_TTL_SECONDS}s, "
        f"stats={STATS_TTL_SECONDS}s, "
        f"forks={FORKS_TTL_SECONDS}s, "
        f"general={GENERAL_TTL_SECONDS}s, "
        f"ai={AI_CACHE_TTL_SECONDS}s"
    )

except (ValueError, TypeError) as e:
    logger.error(f"Error loading cache settings: {e}. Using defaults.")
    # Fallback to defaults
    CACHE_SIZE = DEFAULT_CACHE_SIZE
    CACHE_ENABLED = DEFAULT_CACHE_ENABLED
    CHAIN_TTL_SECONDS = DEFAULT_CHAIN_TTL_SECONDS
    VERIFICATION_TTL_SECONDS = DEFAULT_VERIFICATION_TTL_SECONDS
    STATS_TTL_SECONDS = DEFAULT_STATS_TTL_SECONDS
    FORKS_TTL_SECONDS = DEFAULT_FORKS_TTL_SECONDS
    GENERAL_TTL_SECONDS = DEFAULT_GENERAL_TTL_SECONDS
    AI_CACHE_TTL_SECONDS = DEFAULT_AI_CACHE_TTL_SECONDS


def get_ttl_for_endpoint(endpoint_type):
    """
    Get the appropriate TTL setting for a given endpoint type.

    Args:
        endpoint_type: String identifying the endpoint type
            ('chain', 'verification', 'stats', 'forks', or anything else)

    Returns:
        TTL in seconds for the given endpoint type
    """
    if not CACHE_ENABLED:
        return 0  # No caching if disabled

    ttl_map = {
        "chain": CHAIN_TTL_SECONDS,
        "verification": VERIFICATION_TTL_SECONDS,
        "stats": STATS_TTL_SECONDS,
        "forks": FORKS_TTL_SECONDS,
        "ai": AI_CACHE_TTL_SECONDS,
    }

    return ttl_map.get(endpoint_type, GENERAL_TTL_SECONDS)


def is_caching_enabled():
    """Check if caching is enabled globally."""
    return CACHE_ENABLED


def get_cache_size():
    """Get the configured cache size."""
    return CACHE_SIZE
