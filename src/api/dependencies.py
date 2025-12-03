"""Dependency injection for API components."""

import functools
import logging
from typing import Any, List, Optional

from src.engine.capsule_engine import CapsuleEngine
from quart import current_app, g, jsonify, make_response, request

logger = logging.getLogger(__name__)


def get_engine() -> CapsuleEngine:
    """Get the CapsuleEngine instance for the current request."""
    if hasattr(current_app, "engine_override"):
        # For testing - use the overridden engine
        return current_app.engine_override

    if hasattr(current_app, "engine"):
        # For production - use the app's engine
        return current_app.engine

    raise RuntimeError("No engine configured")


def get_db():
    """Get the database session from the current app context."""
    # In testing mode, use the async session from the engine override
    if hasattr(current_app, "engine_override") and hasattr(
        current_app.engine_override, "db"
    ):
        return current_app.engine_override.db
    # Otherwise, use the sync session from the request context
    return g.get("db_session")


def _build_wrapper(func, required_permissions: Optional[List[str]]):
    """Inner helper to create the actual auth wrapper so that the result keeps the
    original function name (avoids endpoint collisions)."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return "", 200

        api_keys = current_app.config.get("API_KEYS", {})

        # If no keys are configured, bypass auth (useful for dev/tests).
        if not api_keys:
            return await func(*args, **kwargs)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            logger.warning("[Auth] API key missing from request header.")
            return jsonify({"error": "API key required"}), 401

        key_info = api_keys.get(api_key)
        if not key_info:
            logger.warning(f"[Auth] Invalid API key received: {api_key[:4]}...")
            return jsonify({"error": "Invalid API key"}), 401

        # Check permissions if required
        if required_permissions:
            permissions = key_info.get("permissions", [])
            if not set(required_permissions).issubset(set(permissions)):
                logger.warning(
                    f"[Auth] API key lacks required permissions: {required_permissions}"
                )
                return jsonify({"error": "Insufficient permissions"}), 403

        # Propagate agent_id for downstream use
        agent_id = key_info.get("agent_id")
        if not agent_id:
            logger.error(
                f"[Auth] Server config error: API key '{api_key[:4]}...' is missing an agent_id."
            )
            return (
                jsonify({"error": "API key is not configured with an agent_id"}),
                500,
            )

        g.api_key_info = key_info
        g.agent_id = agent_id

        return await func(*args, **kwargs)

    return wrapper


def require_api_key(arg: Optional[Any] = None):
    """Decorator to protect routes with API key authentication.

    Supports both usages:
    1. `@require_api_key` (no arguments) – all authenticated keys allowed.
    2. `@require_api_key(["read", "write"])` – restrict to given permissions.
    """

    # Case 1: used without parentheses – the first argument is the function itself.
    if callable(arg):
        return _build_wrapper(arg, required_permissions=None)

    # Case 2: used with a list/None – return a decorator waiting for the function.
    required_permissions: Optional[List[str]] = arg  # could be None or list

    def decorator(func):
        return _build_wrapper(func, required_permissions)

    return decorator


def cache_response_headers(ttl_seconds: int = 300):
    """Decorator to add cache headers to responses for ASGI caching middleware."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)

            # If it's already a Response object, modify headers
            if hasattr(response, "headers"):
                response.headers["Cache-Control"] = f"public, max-age={ttl_seconds}"
                return response

            # If it's data, create a Response and add headers
            response_obj = await make_response(response)
            response_obj.headers["Cache-Control"] = f"public, max-age={ttl_seconds}"
            return response_obj

        return wrapper

    return decorator
