#!/usr/bin/env python3
"""
Authentication API Endpoints
===========================

This module provides REST API endpoints for JWT authentication,
including login, registration, token refresh, and user management.
"""

import asyncio
import logging
import os
import sys
from typing import List

from quart import g, jsonify, request
from werkzeug.exceptions import BadRequest, Forbidden, Unauthorized

from src.utils.timezone_utils import utc_now

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from auth.jwt_auth import get_authenticator

from .custom_quart import CustomQuart

logger = logging.getLogger(__name__)

# Initialize Quart app
app = CustomQuart(__name__)

# Configure app
app.config.update(
    {"SECRET_KEY": os.getenv("SECRET_KEY", "dev-secret-key"), "TESTING": False}
)


# Request/Response schemas
class LoginRequest:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password


class RegisterRequest:
    def __init__(
        self, username: str, email: str, password: str, roles: List[str] = None
    ):
        self.username = username
        self.email = email
        self.password = password
        self.roles = roles or ["user"]


class TokenRefreshRequest:
    def __init__(self, refresh_token: str):
        self.refresh_token = refresh_token


# Authentication middleware
async def extract_token_from_request():
    """Extract JWT token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


async def get_current_user():
    """Get current authenticated user from token."""
    token = await extract_token_from_request()
    if not token:
        return None

    authenticator = get_authenticator()
    return authenticator.get_user_from_token(token)


def require_auth(required_roles: List[str] = None):
    """Decorator to require authentication for endpoints."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = await get_current_user()
            if not user:
                raise Unauthorized("Authentication required")

            if required_roles:
                authenticator = get_authenticator()
                if not authenticator.has_any_role(user, required_roles):
                    raise Forbidden("Insufficient permissions")

            g.current_user = user
            return await func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


# Authentication endpoints
@app.route("/auth/register", methods=["POST"])
async def register():
    """Register a new user."""
    try:
        data = await request.get_json()
        if not data:
            raise BadRequest("Request body required")

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        roles = data.get("roles", ["user"])

        if not all([username, email, password]):
            raise BadRequest("Username, email, and password are required")

        # Basic validation
        if len(password) < 6:
            raise BadRequest("Password must be at least 6 characters")

        if "@" not in email:
            raise BadRequest("Invalid email format")

        authenticator = get_authenticator()
        user = authenticator.create_user(username, email, password, roles)

        logger.info(f" User registered: {username}")

        return (
            jsonify(
                {
                    "message": "User registered successfully",
                    "user": {
                        "user_id": user.user_id,
                        "username": user.username,
                        "email": user.email,
                        "roles": user.roles,
                        "created_at": user.created_at.isoformat(),
                    },
                }
            ),
            201,
        )

    except ValueError as e:
        logger.warning(f"Registration failed: {e}")
        raise BadRequest(str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/auth/login", methods=["POST"])
async def login():
    """Authenticate user and return tokens."""
    try:
        data = await request.get_json()
        if not data:
            raise BadRequest("Request body required")

        username = data.get("username")
        password = data.get("password")

        if not all([username, password]):
            raise BadRequest("Username and password are required")

        authenticator = get_authenticator()
        user = authenticator.authenticate_user(username, password)

        if not user:
            logger.warning(f"Login failed for: {username}")
            raise Unauthorized("Invalid credentials")

        # Generate tokens
        access_token = authenticator.generate_access_token(user)
        refresh_token = authenticator.generate_refresh_token(user)

        logger.info(f" User logged in: {username}")

        return (
            jsonify(
                {
                    "message": "Login successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "user": {
                        "user_id": user.user_id,
                        "username": user.username,
                        "email": user.email,
                        "roles": user.roles,
                        "last_login": user.last_login.isoformat()
                        if user.last_login
                        else None,
                    },
                }
            ),
            200,
        )

    except Unauthorized:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/auth/refresh", methods=["POST"])
async def refresh_token():
    """Refresh access token using refresh token."""
    try:
        data = await request.get_json()
        if not data:
            raise BadRequest("Request body required")

        refresh_token = data.get("refresh_token")
        if not refresh_token:
            raise BadRequest("Refresh token required")

        authenticator = get_authenticator()
        new_access_token = authenticator.refresh_access_token(refresh_token)

        if not new_access_token:
            raise Unauthorized("Invalid or expired refresh token")

        logger.info(" Token refreshed")

        return (
            jsonify(
                {
                    "message": "Token refreshed successfully",
                    "access_token": new_access_token,
                    "token_type": "bearer",
                }
            ),
            200,
        )

    except Unauthorized:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/auth/logout", methods=["POST"])
@require_auth()
async def logout():
    """Logout user and revoke refresh token."""
    try:
        data = await request.get_json()
        refresh_token = data.get("refresh_token") if data else None

        if refresh_token:
            authenticator = get_authenticator()
            authenticator.revoke_refresh_token(refresh_token)

        logger.info(f" User logged out: {g.current_user.username}")

        return jsonify({"message": "Logout successful"}), 200

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/auth/me", methods=["GET"])
@require_auth()
async def get_current_user_info():
    """Get current user information."""
    try:
        user = g.current_user

        return (
            jsonify(
                {
                    "user": {
                        "user_id": user.user_id,
                        "username": user.username,
                        "email": user.email,
                        "roles": user.roles,
                        "created_at": user.created_at.isoformat(),
                        "last_login": user.last_login.isoformat()
                        if user.last_login
                        else None,
                        "is_active": user.is_active,
                    }
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Get user info error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/auth/users", methods=["GET"])
@require_auth(["admin"])
async def list_users():
    """List all users (admin only)."""
    try:
        authenticator = get_authenticator()
        users = authenticator.list_users()

        return jsonify({"users": users, "total": len(users)}), 200

    except Exception as e:
        logger.error(f"List users error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/auth/users/<username>/roles", methods=["POST"])
@require_auth(["admin"])
async def add_user_role(username: str):
    """Add role to user (admin only)."""
    try:
        data = await request.get_json()
        if not data:
            raise BadRequest("Request body required")

        role = data.get("role")
        if not role:
            raise BadRequest("Role required")

        authenticator = get_authenticator()
        success = authenticator.add_role(username, role)

        if not success:
            raise BadRequest("User not found")

        logger.info(f" Role '{role}' added to user: {username}")

        return jsonify({"message": f"Role '{role}' added to user '{username}'"}), 200

    except BadRequest:
        raise
    except Exception as e:
        logger.error(f"Add role error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/auth/users/<username>/roles", methods=["DELETE"])
@require_auth(["admin"])
async def remove_user_role(username: str):
    """Remove role from user (admin only)."""
    try:
        data = await request.get_json()
        if not data:
            raise BadRequest("Request body required")

        role = data.get("role")
        if not role:
            raise BadRequest("Role required")

        authenticator = get_authenticator()
        success = authenticator.remove_role(username, role)

        if not success:
            raise BadRequest("User not found")

        logger.info(f" Role '{role}' removed from user: {username}")

        return (
            jsonify({"message": f"Role '{role}' removed from user '{username}'"}),
            200,
        )

    except BadRequest:
        raise
    except Exception as e:
        logger.error(f"Remove role error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/auth/users/<username>/activate", methods=["POST"])
@require_auth(["admin"])
async def activate_user(username: str):
    """Activate user account (admin only)."""
    try:
        authenticator = get_authenticator()
        success = authenticator.activate_user(username)

        if not success:
            raise BadRequest("User not found")

        logger.info(f"[OK] User activated: {username}")

        return jsonify({"message": f"User '{username}' activated"}), 200

    except BadRequest:
        raise
    except Exception as e:
        logger.error(f"Activate user error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/auth/users/<username>/deactivate", methods=["POST"])
@require_auth(["admin"])
async def deactivate_user(username: str):
    """Deactivate user account (admin only)."""
    try:
        authenticator = get_authenticator()
        success = authenticator.deactivate_user(username)

        if not success:
            raise BadRequest("User not found")

        logger.info(f" User deactivated: {username}")

        return jsonify({"message": f"User '{username}' deactivated"}), 200

    except BadRequest:
        raise
    except Exception as e:
        logger.error(f"Deactivate user error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/auth/stats", methods=["GET"])
@require_auth(["admin"])
async def get_auth_stats():
    """Get authentication statistics (admin only)."""
    try:
        authenticator = get_authenticator()
        stats = authenticator.get_user_stats()

        return jsonify({"statistics": stats}), 200

    except Exception as e:
        logger.error(f"Get auth stats error: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Health check endpoint
@app.route("/auth/health", methods=["GET"])
async def health_check():
    """Authentication service health check."""
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "uatp-auth",
                "timestamp": utc_now().isoformat(),
            }
        ),
        200,
    )


# Error handlers
@app.errorhandler(BadRequest)
async def handle_bad_request(e):
    return jsonify({"error": str(e.description)}), 400


@app.errorhandler(Unauthorized)
async def handle_unauthorized(e):
    return jsonify({"error": str(e.description)}), 401


@app.errorhandler(Forbidden)
async def handle_forbidden(e):
    return jsonify({"error": str(e.description)}), 403


@app.errorhandler(404)
async def handle_not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
async def handle_internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


async def main():
    """Test the authentication API."""

    print(" Testing Authentication API")
    print("=" * 40)

    # Start the server in test mode
    logger.info(" Starting authentication API server...")

    # Create a test admin user
    authenticator = get_authenticator()
    try:
        admin_user = authenticator.create_user(
            "admin", "admin@uatp.com", "admin123", ["user", "admin"]
        )
        logger.info(f"[OK] Created admin user: {admin_user.username}")
    except ValueError:
        logger.info("Admin user already exists")

    # Run the server
    await app.run_task(host="0.0.0.0", port=5002, debug=True)


if __name__ == "__main__":
    asyncio.run(main())
