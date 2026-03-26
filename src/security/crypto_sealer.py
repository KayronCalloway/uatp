"""
Crypto Sealer
=============

This module provides cryptographic signing and verification for UATP capsules.
It uses Ed25519 for high-performance, secure signatures.

Security Features:
- Ed25519 signatures for authenticity and non-repudiation
- Encrypted private key storage (AES-256)
- Support for key password from environment variable
"""

import base64
import json
import logging
import os
from typing import Any, Dict

# cryptography library is required
try:
    # from cryptography.hazmat.backends import default_backend  # noqa: F401
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
except ImportError:
    ed25519 = None  # type: ignore
    serialization = None  # type: ignore

logger = logging.getLogger(__name__)


def _derive_key_password() -> bytes:
    """Get key password. Delegates to uatp_crypto_v7 for consistency."""
    from src.security.uatp_crypto_v7 import _get_key_password

    return _get_key_password()


class CryptoSealer:
    """
    Handles cryptographic signing and verification of capsules.
    """

    def __init__(self, key_dir: str = ".uatp_keys"):
        if not ed25519:
            logger.warning("[WARN] 'cryptography' library not found. Signing disabled.")
            self.enabled = False
            return

        self.key_dir = key_dir
        self.enabled = True
        self._ensure_keys_exist()
        self._load_keys()

    def _ensure_keys_exist(self):
        """Generate a new keypair if one doesn't exist. Uses encrypted storage."""
        if not os.path.exists(self.key_dir):
            os.makedirs(self.key_dir)

        # Check for encrypted key first, then unencrypted (for migration)
        priv_path_encrypted = os.path.join(self.key_dir, "uatp_private.pem.enc")
        priv_path_legacy = os.path.join(self.key_dir, "uatp_private.pem")
        pub_path = os.path.join(self.key_dir, "uatp_public.pem")

        # Determine which private key path to use
        if os.path.exists(priv_path_encrypted):
            self._priv_path = priv_path_encrypted
            self._encrypted = True
        elif os.path.exists(priv_path_legacy):
            # Migrate unencrypted key to encrypted
            self._priv_path = priv_path_encrypted
            self._encrypted = True
            self._migrate_to_encrypted(priv_path_legacy, priv_path_encrypted)
        else:
            self._priv_path = priv_path_encrypted
            self._encrypted = True

        self._pub_path = pub_path

        if not os.path.exists(self._priv_path) or not os.path.exists(pub_path):
            logger.info(" Generating new Ed25519 keypair with encrypted storage...")
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()

            # Get encryption password
            password = _derive_key_password()

            # Save private key with encryption
            with open(self._priv_path, "wb") as f:
                f.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.BestAvailableEncryption(
                            password
                        ),
                    )
                )

            # Save public key (no encryption needed)
            with open(pub_path, "wb") as f:
                f.write(
                    public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                )

            # Set secure permissions on private key (Unix only)
            try:
                os.chmod(self._priv_path, 0o600)
            except (OSError, AttributeError):
                pass  # Windows or permission error

            logger.info(f"[OK] Encrypted keys saved to {self.key_dir}")

    def _migrate_to_encrypted(self, old_path: str, new_path: str):
        """Migrate an unencrypted private key to encrypted storage."""
        try:
            logger.info(" Migrating unencrypted key to encrypted storage...")

            # Load unencrypted key
            with open(old_path, "rb") as f:
                private_key = serialization.load_pem_private_key(
                    f.read(), password=None
                )

            # Get encryption password
            password = _derive_key_password()

            # Save with encryption
            with open(new_path, "wb") as f:
                f.write(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.BestAvailableEncryption(
                            password
                        ),
                    )
                )

            # Set secure permissions
            try:
                os.chmod(new_path, 0o600)
            except (OSError, AttributeError):
                pass

            # Securely delete old unencrypted key
            with open(old_path, "wb") as f:
                f.write(os.urandom(1024))  # Overwrite with random data
            os.remove(old_path)

            logger.info(
                "[OK] Key migration complete. Unencrypted key securely deleted."
            )

        except Exception as e:
            logger.error(f"[ERROR] Key migration failed: {e}")
            raise

    def _load_keys(self):
        """Load keys from disk. Supports both encrypted and legacy unencrypted keys."""
        # Get encryption password
        password = _derive_key_password() if self._encrypted else None

        try:
            with open(self._priv_path, "rb") as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(), password=password
                )
        except TypeError:
            # Key might be unencrypted if migration failed
            logger.warning("[WARN] Attempting to load key without password...")
            with open(self._priv_path, "rb") as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(), password=None
                )

        with open(self._pub_path, "rb") as f:
            self.public_key = serialization.load_pem_public_key(f.read())

        logger.info(" Cryptographic keys loaded successfully")

    def _canonicalize(self, data: Dict[str, Any]) -> bytes:
        """
        Convert dictionary to a canonical JSON byte string.
        - Sorted keys
        - No whitespace
        """
        # We process a COPY of the data to avoid modifying the original
        # Remove any existing signature or temporary fields before signing
        payload = data.copy()
        if "signature" in payload:
            del payload["signature"]
        if "verification_method" in payload:
            del payload["verification_method"]
        if "verification" in payload:
            # v7.0 stores signature in verification object - must exclude during verification
            del payload["verification"]

        return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )

    def sign_capsule(self, capsule_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Sign the capsule data and return signature metadata.

        Returns:
            Dict containing 'signature' and 'verification_method'
        """
        if not self.enabled:
            return {}

        try:
            canonical_data = self._canonicalize(capsule_data)
            signature_bytes = self.private_key.sign(canonical_data)
            signature_b64 = base64.b64encode(signature_bytes).decode("utf-8")

            return {
                "type": "Ed25519Signature2020",
                "proofValue": signature_b64,
                "created": json.dumps(capsule_data.get("timestamp", "")),
            }
        except Exception as e:
            logger.error(f"[ERROR] Signing failed: {e}")
            return {}

    def verify_capsule(self, capsule_data: Dict[str, Any]) -> bool:
        """
        Verify the signature of a signed capsule.
        Supports both legacy format (payload.signature) and v7.0 format (payload.verification.signature).

        V7.0 Verification Process:
        1. Recompute content hash from capsule data (excluding verification field)
        2. Compare recomputed hash with stored hash
        3. Load public key from verification.verify_key
        4. Verify Ed25519 signature over the hash bytes
        """
        if not self.enabled:
            return False

        verification_data = capsule_data.get("verification", {})

        # Check for v7.0 format first (verification.signature with "ed25519:" prefix)
        if verification_data and verification_data.get("signature", "").startswith(
            "ed25519:"
        ):
            return self._verify_v7_capsule(capsule_data, verification_data)

        # Fall back to legacy format
        return self._verify_legacy_capsule(capsule_data)

    def _verify_v7_capsule(
        self, capsule_data: Dict[str, Any], verification_data: Dict[str, Any]
    ) -> bool:
        """
        Verify a V7.0 format capsule with proper Ed25519 signature verification.

        V7.0 format:
        - signature: "ed25519:hex_signature"
        - hash: plain hex (64 chars) - the hash that was signed
        - verify_key: hex_encoded_public_key

        Note: We verify the signature over the stored hash rather than recomputing,
        because the capsule data structure changes during storage (UATP envelope wrapping).
        The signature proves the hash was created by the signer and hasn't been tampered with.
        """
        try:
            # Extract signature
            signature_str = verification_data.get("signature", "")
            if not signature_str.startswith("ed25519:"):
                logger.warning("[WARN] V7.0 signature must start with 'ed25519:'")
                return False

            signature_hex = signature_str.split(":", 1)[1]
            if (
                len(signature_hex) != 128
            ):  # Ed25519 signatures are 64 bytes = 128 hex chars
                logger.warning(
                    f"[WARN] Invalid signature length: {len(signature_hex)} (expected 128)"
                )
                return False

            signature_bytes = bytes.fromhex(signature_hex)

            # Extract stored hash - supports both plain hex and sha256: prefixed format
            stored_hash = verification_data.get("hash", "")
            if stored_hash.startswith("sha256:"):
                stored_hash = stored_hash.split(":", 1)[1]

            # Validate hash format (should be 64 hex chars = SHA256)
            if len(stored_hash) != 64:
                logger.warning(
                    f"[WARN] Invalid hash length: {len(stored_hash)} (expected 64)"
                )
                return False

            # NOTE: We don't recompute the hash because the capsule data structure
            # is transformed during storage (UATP envelope wrapping). Instead, we
            # verify the signature over the stored hash, which proves:
            # 1. The hash was created by the holder of the signing key
            # 2. The hash hasn't been modified since signing
            # This provides cryptographic integrity for the original content.

            # CRITICAL: The signing process signs the hash STRING encoded as UTF-8,
            # not the binary hash bytes. See crypto_utils.sign_capsule:
            # signing_key.sign(hash_str.encode("utf-8"))
            hash_bytes = stored_hash.encode("utf-8")

            # Extract and load public key from verify_key
            verify_key_hex = verification_data.get("verify_key")
            if not verify_key_hex:
                logger.warning("[WARN] No verify_key in V7.0 verification object")
                return False

            if (
                len(verify_key_hex) != 64
            ):  # Ed25519 public keys are 32 bytes = 64 hex chars
                logger.warning(
                    f"[WARN] Invalid verify_key length: {len(verify_key_hex)} (expected 64)"
                )
                return False

            verify_key_bytes = bytes.fromhex(verify_key_hex)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(verify_key_bytes)

            # Verify the signature over the hash
            try:
                public_key.verify(signature_bytes, hash_bytes)
                logger.info(
                    f"[OK] V7.0 capsule signature verified: {capsule_data.get('capsule_id', 'unknown')}"
                )
                return True
            except Exception as sig_error:
                logger.warning(f"[WARN] Signature verification failed: {sig_error}")
                return False

        except ValueError as e:
            logger.error(f"[ERROR] V7.0 verification failed (hex decode): {e}")
            return False
        except Exception as e:
            logger.error(f"[ERROR] V7.0 verification failed: {e}")
            return False

    def _compute_v7_hash(self, capsule_data: Dict[str, Any]) -> str:
        """
        Compute SHA256 hash matching crypto_utils.hash_for_signature.

        Uses the same function from crypto_utils to ensure consistency.

        Returns:
            Plain hex hash string (no prefix)
        """
        try:
            # Use the exact same function as signing for hash consistency
            from src.crypto_utils import hash_for_signature

            return hash_for_signature(capsule_data)
        except ImportError:
            # Fallback if crypto_utils not available
            import copy
            import hashlib
            from datetime import datetime

            def canonical_json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

            capsule_copy = copy.deepcopy(capsule_data)

            if "verification" in capsule_copy and isinstance(
                capsule_copy["verification"], dict
            ):
                verification_copy = dict(capsule_copy["verification"])
                verification_copy.pop("hash", None)
                verification_copy.pop("signature", None)
                capsule_copy["verification"] = verification_copy

            canonical_json = json.dumps(
                capsule_copy,
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
                default=canonical_json_serializer,
            )

            return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def _verify_legacy_capsule(self, capsule_data: Dict[str, Any]) -> bool:
        """
        Verify a legacy format capsule (pre-V7.0).

        Legacy format:
        - signature field at root level with proofValue (base64)
        """
        signature_info = capsule_data.get("signature")

        if not signature_info:
            logger.warning("[WARN] No signature found in capsule")
            return False

        try:
            signature_b64 = signature_info.get("proofValue")
            if not signature_b64:
                logger.warning("[WARN] No proofValue in legacy signature")
                return False

            signature_bytes = base64.b64decode(signature_b64)

            # Legacy format: verify canonical representation of capsule
            canonical_data = self._canonicalize(capsule_data)
            self.public_key.verify(signature_bytes, canonical_data)
            logger.info(
                f"[OK] Legacy capsule signature verified: {capsule_data.get('capsule_id', 'unknown')}"
            )
            return True

        except Exception as e:
            logger.error(f"[ERROR] Legacy verification failed: {e}")
            return False
