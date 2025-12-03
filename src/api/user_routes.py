"""
User Management API Routes
Handles user registration, authentication, and onboarding completion
"""

import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any

from quart import Blueprint, request, jsonify, g
from quart_cors import cors

# from quart_schema import validate_json  # Not needed for this module

from ..user_management.user_service import UserService
from ..core.database import db

logger = logging.getLogger(__name__)


def create_user_blueprint() -> Blueprint:
    """Create user management API blueprint"""

    bp = Blueprint("user_api", __name__, url_prefix="/api/user")
    cors(
        bp,
        allow_origin=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
        ],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-API-Key"],
        allow_credentials=True,
    )

    @bp.route("/register", methods=["POST", "OPTIONS"])
    async def register_user():
        """Register a new user account"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            data = await request.get_json()

            # Extract user data
            email = data.get("email")
            username = data.get("username")
            password = data.get("password")
            full_name = data.get("full_name", "")

            # Validate required fields
            if not all([email, username, password]):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Email, username, and password are required",
                        }
                    ),
                    400,
                )

            # Create user service
            async with db.session_factory() as db_session:
                user_service = UserService(db_session)

                # Register user
                result = await user_service.register_user(
                    email=email,
                    username=username,
                    password=password,
                    full_name=full_name,
                    attribution_enabled=data.get("attribution_enabled", True),
                    uba_participation=data.get("uba_participation", True),
                    data_sharing_consent=data.get("data_sharing_consent", False),
                    analytics_consent=data.get("analytics_consent", False),
                )

                if result["success"]:
                    # Set user as active by default for onboarding users
                    user = await user_service.get_user_profile(result["user_id"])
                    if user:
                        await user_service.update_user_profile(
                            result["user_id"], {"status": "active"}
                        )

                return jsonify(result)

        except Exception as e:
            logger.error(f"Failed to register user: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route("/login", methods=["POST", "OPTIONS"])
    async def login_user():
        """Login user and create session"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            data = await request.get_json()

            email = data.get("email")
            password = data.get("password")

            if not all([email, password]):
                return (
                    jsonify(
                        {"success": False, "error": "Email and password are required"}
                    ),
                    400,
                )

            # Get client info
            ip_address = request.headers.get("X-Real-IP", request.remote_addr)
            user_agent = request.headers.get("User-Agent", "Unknown")

            async with db.session_factory() as db_session:
                user_service = UserService(db_session)

                result = await user_service.login_user(
                    email=email,
                    password=password,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )

                return jsonify(result)

        except Exception as e:
            logger.error(f"Failed to login user: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route("/status/<user_id>", methods=["GET", "OPTIONS"])
    async def get_user_status(user_id: str):
        """Get user account status and onboarding completion"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            async with db.session_factory() as db_session:
                user_service = UserService(db_session)

                # Get user profile
                user = await user_service.get_user_profile(user_id)
                if not user:
                    return jsonify({"success": False, "error": "User not found"}), 404

                # Get onboarding status
                onboarding_status = await user_service.get_user_onboarding_status(
                    user_id
                )

                return jsonify(
                    {
                        "success": True,
                        "user": {
                            "id": str(user.id),
                            "username": user.username,
                            "email": user.email,
                            "status": user.status,
                            "verification_status": user.verification_status,
                            "has_completed_setup": user.status == "active"
                            and user.verification_status != "unverified",
                            "attribution_enabled": user.attribution_enabled,
                            "created_at": user.created_at.isoformat(),
                        },
                        "onboarding": onboarding_status
                        if onboarding_status.get("success")
                        else None,
                    }
                )

        except Exception as e:
            logger.error(f"Failed to get user status: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route("/complete-onboarding", methods=["POST", "OPTIONS"])
    async def complete_onboarding():
        """Mark user onboarding as complete and create persistent account"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            data = await request.get_json()

            # This can come from session or be passed explicitly
            user_id = data.get("user_id")
            if not user_id:
                return jsonify({"success": False, "error": "User ID is required"}), 400

            # User registration data if creating new account
            registration_data = data.get("registration_data", {})

            async with db.session_factory() as db_session:
                user_service = UserService(db_session)

                # Check if user exists
                existing_user = await user_service.get_user_profile(user_id)

                if not existing_user and registration_data:
                    # Create new user account
                    register_result = await user_service.register_user(
                        email=registration_data.get("email", f"{user_id}@uatp.local"),
                        username=registration_data.get("username", user_id),
                        password=registration_data.get(
                            "password", user_id
                        ),  # Temporary, should prompt for real password
                        full_name=registration_data.get("full_name", "UATP User"),
                        attribution_enabled=True,
                        uba_participation=True,
                    )

                    if not register_result["success"]:
                        return jsonify(register_result), 400

                    user_id = register_result["user_id"]

                # Update user to mark onboarding complete
                if existing_user or registration_data:
                    await user_service.update_user_profile(
                        user_id,
                        {
                            "status": "active",
                            "verification_status": "verified",  # Auto-verify for onboarding users
                        },
                    )

                return jsonify(
                    {
                        "success": True,
                        "user_id": user_id,
                        "message": "Onboarding completed successfully",
                    }
                )

        except Exception as e:
            logger.error(f"Failed to complete onboarding: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route("/creator-check", methods=["GET", "OPTIONS"])
    async def check_creator_status():
        """Check if current user is the system creator (Kay)"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            # Check various indicators for creator status
            is_creator = False
            creator_indicators = []

            # Check environment variables for creator indicators
            creator_names = ["kay", "kayvan", "creator"]
            system_user = os.getenv("USER", "").lower()
            home_dir = os.getenv("HOME", "").lower()

            if any(name in system_user for name in creator_names):
                is_creator = True
                creator_indicators.append("system_user_match")

            if any(name in home_dir for name in creator_names):
                is_creator = True
                creator_indicators.append("home_directory_match")

            # Check if running in development mode (another creator indicator)
            if os.getenv("FLASK_ENV") == "development" or os.getenv("DEBUG") == "true":
                creator_indicators.append("development_mode")

            # Check for presence of key development files
            dev_files = [".env", "requirements.txt", "src/onboarding"]
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

            if all(os.path.exists(os.path.join(project_root, f)) for f in dev_files):
                creator_indicators.append("development_environment")

            return jsonify(
                {
                    "success": True,
                    "is_creator": is_creator,
                    "indicators": creator_indicators,
                    "recommendation": "creator_dashboard"
                    if is_creator
                    else "standard_onboarding",
                }
            )

        except Exception as e:
            logger.error(f"Failed to check creator status: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route("/delete/<user_id>", methods=["DELETE", "OPTIONS"])
    async def delete_user(user_id: str):
        """Delete user account and all associated data (GDPR compliant)"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            data = await request.get_json() or {}
            reason = data.get("reason", "user_request")

            async with db.session_factory() as db_session:
                user_service = UserService(db_session)

                result = await user_service.delete_user_account(user_id, reason)

                if result["success"]:
                    return jsonify(result), 200
                else:
                    return (
                        jsonify(result),
                        404 if "not found" in result.get("error", "").lower() else 500,
                    )

        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @bp.route("/anonymize/<user_id>", methods=["POST", "OPTIONS"])
    async def anonymize_user(user_id: str):
        """Anonymize user account (alternative to deletion)"""
        if request.method == "OPTIONS":
            return "", 200

        try:
            data = await request.get_json() or {}
            reason = data.get("reason", "user_request")

            async with db.session_factory() as db_session:
                user_service = UserService(db_session)

                result = await user_service.anonymize_user_account(user_id, reason)

                if result["success"]:
                    return jsonify(result), 200
                else:
                    return (
                        jsonify(result),
                        404 if "not found" in result.get("error", "").lower() else 500,
                    )

        except Exception as e:
            logger.error(f"Failed to anonymize user: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    return bp
