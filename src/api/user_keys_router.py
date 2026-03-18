"""
User Encryption Keys Router
============================

Provides endpoints for users to retrieve their encryption keys for client-side
payload encryption. This enables the privacy-first model where:
- Users encrypt payloads client-side before creating capsules
- Only the user who created a capsule can decrypt its contents
- Admins see metadata but not decrypted payloads

Security Model:
- Keys are derived from master key using HKDF
- Each user gets a unique key based on their user_id
- Keys are returned over HTTPS (TLS encrypted in transit)
- Frontend stores key in memory only (not localStorage)
"""

import base64
import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from ..auth.auth_middleware import get_current_user
from ..crypto.secure_key_manager import SecureKeyManager, get_key_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-keys", tags=["User Keys"])

# Global key manager instance
_key_manager: SecureKeyManager = None


def get_user_key_manager() -> SecureKeyManager:
    """Get or create the secure key manager singleton."""
    global _key_manager
    if _key_manager is None:
        _key_manager = get_key_manager()
    return _key_manager


@router.get("/my-encryption-key")
async def get_my_encryption_key(
    current_user: Dict = Depends(get_current_user),
):
    """
    Get the current user's encryption key for client-side payload encryption.

    Returns:
        - key: Base64-encoded AES-256 key
        - algorithm: Encryption algorithm to use (AES-256-GCM)
        - key_id: Key identifier for tracking

    Security:
        - Only returns the key for the authenticated user
        - Key is derived using HKDF from master key
        - Frontend should store key in memory only
    """
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    try:
        key_manager = get_user_key_manager()
        user_key = key_manager.derive_user_encryption_key(user_id)

        # Return key as Base64 for easy transport
        key_b64 = base64.b64encode(user_key).decode("utf-8")

        logger.info(f"Encryption key retrieved for user {user_id[:8]}...")

        return {
            "key": key_b64,
            "algorithm": "AES-256-GCM",
            "key_id": f"user_enc_{user_id[:8]}",
            "usage": {
                "encrypt": "Use for encrypting capsule payloads before POST /capsules",
                "decrypt": "Use for decrypting encrypted_payload from GET /capsules",
            },
        }

    except Exception as e:
        logger.error(f"Failed to get encryption key for user {user_id[:8]}...: {e}")
        raise HTTPException(status_code=500, detail="Failed to derive encryption key")


@router.get("/key-info")
async def get_key_info(
    current_user: Dict = Depends(get_current_user),
):
    """
    Get information about the user's encryption key without returning the key itself.

    Useful for checking if key rotation is needed or debugging encryption issues.
    """
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    return {
        "key_id": f"user_enc_{user_id[:8]}",
        "algorithm": "AES-256-GCM",
        "key_derivation": "HKDF-SHA256",
        "key_size_bits": 256,
        "iv_size_bits": 96,  # 12 bytes for GCM
        "tag_size_bits": 128,  # 16 bytes for GCM auth tag
    }
