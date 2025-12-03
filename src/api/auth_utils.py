"""
Quart-compatible JWT Authentication Utilities
==============================================

Decorators and utilities for securing Quart API endpoints with JWT authentication.
"""

import functools
import logging
from typing import Optional, Callable, List

import jwt
from quart import request, jsonify

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Authentication failed"""

    pass


class AuthorizationError(Exception):
    """User not authorized for this resource"""

    pass


async def get_current_user() -> dict:
    """
    Extract and verify JWT token from request, return user info.

    Returns:
        dict: User information from JWT payload

    Raises:
        AuthenticationError: If token is missing or invalid
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise AuthenticationError("Missing Authorization header")

    if not auth_header.startswith("Bearer "):
        raise AuthenticationError("Invalid Authorization header format")

    token = auth_header.split(" ")[1]

    try:
        # Import JWT manager
        from ..auth.jwt_manager import JWTManager

        jwt_manager = JWTManager()

        # Verify token
        payload = jwt.decode(
            token, jwt_manager.secret_key, algorithms=[jwt_manager.algorithm]
        )

        # Check if token is revoked
        if payload.get("jti") in jwt_manager.revoked_tokens:
            raise AuthenticationError("Token has been revoked")

        return payload

    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require JWT authentication for Quart routes.

    Usage:
        @insurance_bp.route("/policies", methods=["GET"])
        @require_auth
        async def get_policies():
            user = await get_current_user()
            ...
    """

    @functools.wraps(f)
    async def decorated_function(*args, **kwargs):
        try:
            user = await get_current_user()
            # Add user to request context
            request.user = user
            return await f(*args, **kwargs)
        except AuthenticationError as e:
            logger.warning(f"Authentication failed: {e}")
            return jsonify({"error": str(e)}), 401
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return jsonify({"error": "Authentication failed"}), 401

    return decorated_function


def require_roles(allowed_roles: List[str]):
    """
    Decorator to require specific roles for access.

    Usage:
        @require_auth
        @require_roles(["admin", "insurance_reviewer"])
        async def approve_claim():
            ...
    """

    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        async def decorated_function(*args, **kwargs):
            try:
                user = await get_current_user()
                user_roles = user.get("scopes", [])

                if not any(role in user_roles for role in allowed_roles):
                    raise AuthorizationError(
                        f"User requires one of these roles: {', '.join(allowed_roles)}"
                    )

                return await f(*args, **kwargs)
            except AuthorizationError as e:
                logger.warning(f"Authorization failed: {e}")
                return jsonify({"error": str(e)}), 403
            except AuthenticationError as e:
                logger.warning(f"Authentication failed: {e}")
                return jsonify({"error": str(e)}), 401
            except Exception as e:
                logger.error(f"Authorization error: {e}")
                return jsonify({"error": "Authorization failed"}), 403

        return decorated_function

    return decorator


async def check_policy_ownership(policy_id: str, user_id: str) -> bool:
    """
    Check if user owns the policy or is an admin.

    Args:
        policy_id: Policy ID to check
        user_id: User ID from JWT token

    Returns:
        bool: True if user can access this policy
    """
    # In production, query database to check policy ownership
    # For now, we'll implement the check in the route handlers
    return True


async def check_claim_ownership(claim_id: str, user_id: str) -> bool:
    """
    Check if user owns the claim or is an admin.

    Args:
        claim_id: Claim ID to check
        user_id: User ID from JWT token

    Returns:
        bool: True if user can access this claim
    """
    # In production, query database to check claim ownership
    # For now, we'll implement the check in the route handlers
    return True
