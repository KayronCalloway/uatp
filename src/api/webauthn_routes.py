"""
WebAuthn/Passkeys API Routes for UATP Capsule Engine

Provides endpoints for passwordless authentication using:
- FIDO2/WebAuthn standard
- Platform authenticators (Touch ID, Face ID, Windows Hello)
- Cross-device passkey synchronization
"""

import logging
from datetime import datetime, timezone

from quart import Blueprint, jsonify, request

from src.auth.webauthn_handler import webauthn_handler
from src.api.dependencies import require_api_key

logger = logging.getLogger("uatp.api.webauthn")

webauthn_bp = Blueprint("webauthn", __name__)


@webauthn_bp.route("/register/begin", methods=["POST"])
@require_api_key(["write"])
async def begin_registration():
    """
    Begin passkey registration process.

    Request body:
    {
        "user_id": "unique_user_id",
        "user_name": "user@example.com",
        "user_display_name": "User Name"
    }

    Returns registration options for navigator.credentials.create()
    """
    data = await request.get_json()

    user_id = data.get("user_id")
    user_name = data.get("user_name")
    user_display_name = data.get("user_display_name", user_name)

    if not user_id or not user_name:
        return (
            jsonify({"success": False, "error": "user_id and user_name required"}),
            400,
        )

    try:
        options = webauthn_handler.generate_registration_options(
            user_id=user_id, user_name=user_name, user_display_name=user_display_name
        )

        logger.info(f"Registration initiated for user: {user_id}")

        return jsonify({"success": True, "options": options})

    except Exception as e:
        logger.error(f"Registration initiation failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@webauthn_bp.route("/register/complete", methods=["POST"])
@require_api_key(["write"])
async def complete_registration():
    """
    Complete passkey registration.

    Request body:
    {
        "credential": { ... },  // Response from navigator.credentials.create()
        "challenge": "base64_challenge"
    }

    Returns credential info on success.
    """
    data = await request.get_json()

    credential_response = data.get("credential")
    challenge = data.get("challenge")

    if not credential_response or not challenge:
        return (
            jsonify({"success": False, "error": "credential and challenge required"}),
            400,
        )

    try:
        credential = webauthn_handler.verify_registration(
            credential_response=credential_response, expected_challenge=challenge
        )

        logger.info(f"Registration completed for user: {credential.user_id}")

        return jsonify(
            {
                "success": True,
                "credential": {
                    "credential_id": credential.credential_id,
                    "user_id": credential.user_id,
                    "created_at": credential.created_at.isoformat(),
                    "transports": credential.transports,
                    "backup_eligible": credential.backup_eligible,
                },
            }
        )

    except ValueError as e:
        logger.warning(f"Registration verification failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Registration completion failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@webauthn_bp.route("/authenticate/begin", methods=["POST"])
async def begin_authentication():
    """
    Begin passkey authentication.

    Request body (optional):
    {
        "user_id": "unique_user_id"  // Optional for account-specific auth
    }

    Returns authentication options for navigator.credentials.get()
    """
    data = await request.get_json() or {}
    user_id = data.get("user_id")

    try:
        options = webauthn_handler.generate_authentication_options(user_id=user_id)

        logger.info(f"Authentication initiated for user: {user_id or 'any'}")

        return jsonify({"success": True, "options": options})

    except Exception as e:
        logger.error(f"Authentication initiation failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@webauthn_bp.route("/authenticate/complete", methods=["POST"])
async def complete_authentication():
    """
    Complete passkey authentication.

    Request body:
    {
        "credential": { ... },  // Response from navigator.credentials.get()
        "challenge": "base64_challenge"
    }

    Returns authentication result and user info.
    """
    data = await request.get_json()

    credential_response = data.get("credential")
    challenge = data.get("challenge")

    if not credential_response or not challenge:
        return (
            jsonify({"success": False, "error": "credential and challenge required"}),
            400,
        )

    try:
        credential = webauthn_handler.verify_authentication(
            credential_response=credential_response, expected_challenge=challenge
        )

        logger.info(f"Authentication successful for user: {credential.user_id}")

        # In production, create session token here
        session_token = f"session_{credential.user_id}_{datetime.now().timestamp()}"

        return jsonify(
            {
                "success": True,
                "user_id": credential.user_id,
                "session_token": session_token,
                "credential_id": credential.credential_id,
                "last_used": credential.last_used_at.isoformat(),
            }
        )

    except ValueError as e:
        logger.warning(f"Authentication verification failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 401
    except Exception as e:
        logger.error(f"Authentication completion failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@webauthn_bp.route("/credentials", methods=["GET"])
@require_api_key(["read"])
async def list_credentials():
    """
    List all passkeys for a user.

    Query params:
        user_id: User ID to list credentials for
    """
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"success": False, "error": "user_id required"}), 400

    try:
        credentials = webauthn_handler.list_user_credentials(user_id)

        return jsonify(
            {
                "success": True,
                "credentials": [
                    {
                        "credential_id": cred.credential_id,
                        "created_at": cred.created_at.isoformat(),
                        "last_used_at": cred.last_used_at.isoformat(),
                        "transports": cred.transports,
                        "backup_eligible": cred.backup_eligible,
                        "backup_state": cred.backup_state,
                        "device_name": cred.device_name,
                    }
                    for cred in credentials
                ],
            }
        )

    except Exception as e:
        logger.error(f"List credentials failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@webauthn_bp.route("/credentials/<credential_id>", methods=["DELETE"])
@require_api_key(["write"])
async def revoke_credential(credential_id: str):
    """
    Revoke a passkey.

    Removes the credential and prevents future authentication.
    """
    try:
        success = webauthn_handler.revoke_credential(credential_id)

        if not success:
            return jsonify({"success": False, "error": "Credential not found"}), 404

        logger.info(f"Credential revoked: {credential_id}")

        return jsonify({"success": True, "message": "Credential revoked"})

    except Exception as e:
        logger.error(f"Revoke credential failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@webauthn_bp.route("/health", methods=["GET"])
async def webauthn_health():
    """Health check for WebAuthn service."""
    return jsonify(
        {
            "status": "healthy",
            "service": "webauthn",
            "rp_id": webauthn_handler.rp_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
