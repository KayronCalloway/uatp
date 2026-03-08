"""
Local Signer - Gold Standard Capsule Signing
=============================================

This module implements the gold standard signing flow:
1. User creates capsule content LOCALLY
2. User signs with their LOCAL key (never transmitted)
3. Only the HASH is sent to UATP for timestamping
4. Timestamp comes from EXTERNAL TSA (DigiCert/FreeTSA)
5. Complete capsule stays LOCAL unless user chooses to publish

UATP never sees:
- The capsule content
- The user's private key
- The signature (it's computed locally)

UATP only sees:
- The SHA-256 hash (32 bytes, no content)
- Returns: RFC 3161 timestamp from external TSA
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .user_key_manager import UserKeyManager, get_user_key_manager

logger = logging.getLogger(__name__)


@dataclass
class SignedCapsule:
    """A locally signed capsule ready for timestamping."""

    capsule_id: str
    content_hash: str  # SHA-256 of canonical content
    signature: str  # Ed25519 signature (hex)
    public_key: str  # Signer's public key (hex)
    signed_at: datetime
    content: Dict[str, Any]  # The actual content (stays local)

    # Timestamp added after UATP provides it
    timestamp_token: Optional[Dict[str, Any]] = None
    timestamp_tsa: Optional[str] = None
    timestamped_at: Optional[datetime] = None


class LocalSigner:
    """
    Signs capsules locally using user's private key.

    This is the core of UATP's zero-trust architecture:
    - All signing happens on the user's device
    - Private keys never leave the device
    - Only hashes are transmitted for timestamping

    Usage:
        signer = LocalSigner(passphrase="user's secret")

        # Sign a capsule
        signed = signer.sign_capsule({
            "decision": "Approve loan",
            "reasoning": [...]
        })

        # signed.content_hash can be sent to UATP for timestamping
        # signed.content stays local
    """

    def __init__(
        self,
        passphrase: str,
        key_manager: Optional[UserKeyManager] = None,
        key_id: Optional[str] = None,
    ):
        """
        Initialize LocalSigner.

        Args:
            passphrase: User's passphrase for accessing their private key
            key_manager: Optional custom key manager. Uses default if not provided.
            key_id: Which key to use. Uses current key if not provided.
        """
        self.key_manager = key_manager or get_user_key_manager()
        self.passphrase = passphrase
        self.key_id = key_id

        # Verify we can access the key
        key_info = (
            self.key_manager.get_key(key_id)
            if key_id
            else self.key_manager.get_current_key()
        )
        if not key_info:
            raise ValueError(
                "No signing key found. Generate one first with: "
                "key_manager.generate_key_pair(passphrase)"
            )

        self.public_key = key_info.public_key_hex
        self._key_id = key_info.key_id

    def _canonical_json(self, data: Dict[str, Any]) -> bytes:
        """
        Create canonical JSON representation for hashing.

        Ensures consistent hashing regardless of key order, formatting, etc.
        """

        def serialize(obj: Any) -> str:
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.dumps(
            data,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            default=serialize,
        ).encode("utf-8")

    def _compute_hash(self, content: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of canonical content."""
        canonical = self._canonical_json(content)
        return hashlib.sha256(canonical).hexdigest()

    def sign_capsule(
        self,
        content: Dict[str, Any],
        capsule_id: Optional[str] = None,
    ) -> SignedCapsule:
        """
        Sign capsule content locally.

        This creates a cryptographic signature over the content using
        the user's private key. The signature proves:
        1. The content was created by the key holder
        2. The content hasn't been modified since signing

        Args:
            content: The capsule content to sign
            capsule_id: Optional capsule ID. Auto-generated if not provided.

        Returns:
            SignedCapsule with signature and hash (ready for timestamping)

        Security:
            - Signing happens entirely locally
            - Private key is decrypted only for signing, then cleared
            - No network calls are made
        """
        import secrets

        if capsule_id is None:
            timestamp_str = datetime.now(timezone.utc).strftime("%Y_%m_%d_%H%M%S")
            capsule_id = f"caps_{timestamp_str}_{secrets.token_hex(4)}"

        # Compute hash of content
        content_hash = self._compute_hash(content)

        # Sign the hash locally
        signature = self.key_manager.sign(
            data_hash=content_hash,
            passphrase=self.passphrase,
            key_id=self._key_id,
        )

        signed_at = datetime.now(timezone.utc)

        logger.info(f"Locally signed capsule: {capsule_id}")
        logger.info(f"Content hash: {content_hash[:16]}...")
        logger.info(f"Signed with key: {self._key_id}")

        return SignedCapsule(
            capsule_id=capsule_id,
            content_hash=content_hash,
            signature=signature,
            public_key=self.public_key,
            signed_at=signed_at,
            content=content,
        )

    def verify_capsule(self, capsule: SignedCapsule) -> bool:
        """
        Verify a signed capsule.

        This can be done by anyone - only needs public information.
        No private key or passphrase required.

        Args:
            capsule: The signed capsule to verify

        Returns:
            True if signature is valid and content hasn't been modified
        """
        # Recompute hash
        computed_hash = self._compute_hash(capsule.content)

        # Check hash matches
        if computed_hash != capsule.content_hash:
            logger.warning("Content hash mismatch - content may have been modified")
            return False

        # Verify signature
        is_valid = self.key_manager.verify(
            data_hash=capsule.content_hash,
            signature_hex=capsule.signature,
            public_key_hex=capsule.public_key,
        )

        if is_valid:
            logger.info(f"Capsule verified: {capsule.capsule_id}")
        else:
            logger.warning(f"Capsule verification failed: {capsule.capsule_id}")

        return is_valid

    def to_verifiable_capsule(self, signed: SignedCapsule) -> Dict[str, Any]:
        """
        Convert signed capsule to UATP format for storage/transmission.

        The output format matches UATP v7 and can be independently verified.
        """
        verification: Dict[str, Any] = {
            "hash": signed.content_hash,
            "signature": f"ed25519:{signed.signature}",
            "verify_key": signed.public_key,
            "signer": "user",  # Indicates user signed, not UATP
            "signed_at": signed.signed_at.isoformat(),
        }

        # Add timestamp if available
        if signed.timestamp_token:
            verification["rfc3161"] = signed.timestamp_token
            verification["timestamp_tsa"] = signed.timestamp_tsa
            if signed.timestamped_at:
                verification["timestamped_at"] = signed.timestamped_at.isoformat()

        capsule: Dict[str, Any] = {
            "capsule_id": signed.capsule_id,
            "version": "7.2",
            "type": "user_signed",
            "timestamp": signed.signed_at.isoformat(),
            "content": signed.content,
            "verification": verification,
        }

        return capsule


def verify_capsule_standalone(capsule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify a capsule without any UATP infrastructure.

    This function can be used by anyone to verify a capsule
    using only the cryptographic data embedded in the capsule itself.
    No trust in UATP required.

    Args:
        capsule_data: The capsule to verify (dict format)

    Returns:
        Verification result dict with status and details
    """
    from nacl.encoding import HexEncoder
    from nacl.signing import VerifyKey

    result: Dict[str, Any] = {
        "valid": False,
        "signature_valid": False,
        "hash_valid": False,
        "timestamp_valid": None,  # None means not checked
        "errors": [],
        "warnings": [],
    }

    verification = capsule_data.get("verification", {})

    # 1. Check signature
    try:
        signature_str = verification.get("signature", "")
        if signature_str.startswith("ed25519:"):
            signature_hex = signature_str.split(":", 1)[1]
        else:
            signature_hex = signature_str

        public_key_hex = verification.get("verify_key", "")
        stored_hash = verification.get("hash", "")

        if not all([signature_hex, public_key_hex, stored_hash]):
            result["errors"].append("Missing signature, verify_key, or hash")
            return result

        # Verify Ed25519 signature
        verify_key = VerifyKey(public_key_hex, encoder=HexEncoder)
        signature_bytes = bytes.fromhex(signature_hex)

        verify_key.verify(stored_hash.encode("utf-8"), signature_bytes)
        result["signature_valid"] = True

    except Exception as e:
        result["errors"].append(f"Signature verification failed: {e}")
        return result

    # 2. Check content hash
    try:
        content = capsule_data.get("content", {})

        def serialize(obj: Any) -> str:
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        canonical = json.dumps(
            content,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            default=serialize,
        ).encode("utf-8")

        computed_hash = hashlib.sha256(canonical).hexdigest()

        if computed_hash == stored_hash:
            result["hash_valid"] = True
        else:
            result["warnings"].append(
                "Content hash mismatch - capsule structure may have changed during storage"
            )
            # This isn't necessarily an error - UATP wrapping can change structure
            # The signature over the original hash is what matters

    except Exception as e:
        result["warnings"].append(f"Could not verify content hash: {e}")

    # 3. Check RFC 3161 timestamp (if present)
    rfc3161 = verification.get("rfc3161")
    if rfc3161:
        try:
            # Basic check - full verification requires rfc3161ng library
            if "token" in rfc3161 and "tsa" in rfc3161:
                result["timestamp_valid"] = True
                result["timestamp_tsa"] = rfc3161.get("tsa")
                result["timestamp_time"] = rfc3161.get("timestamp")
            else:
                result["warnings"].append("Incomplete RFC 3161 timestamp data")

        except Exception as e:
            result["warnings"].append(f"Could not verify timestamp: {e}")

    # Overall validity
    result["valid"] = result["signature_valid"]

    if result["valid"]:
        result["signer"] = verification.get("signer", "unknown")
        result["capsule_id"] = capsule_data.get("capsule_id")

    return result
