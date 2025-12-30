"""
UATP 7.0 Cryptographic Integration Module
==========================================

This module provides a unified cryptographic interface that outputs
signatures in the UATP 7.0 specification format.

Supported:
- Ed25519 signatures (classical)
- SHA256 content hashing
- Merkle root computation
- Post-quantum signatures (Dilithium3) - optional

Security Properties:
- Content integrity via SHA256
- Author authenticity via Ed25519
- Non-repudiation via signature binding
- Quantum resistance via Dilithium3 (when enabled)
- Encrypted private key storage (AES-256)
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Ed25519 (classical cryptography)
try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519

    ED25519_AVAILABLE = True
except ImportError:
    ED25519_AVAILABLE = False
    ed25519 = None
    serialization = None

# Dilithium3 (post-quantum cryptography)
try:
    import oqs  # liboqs-python

    PQ_AVAILABLE = True
except ImportError:
    PQ_AVAILABLE = False
    oqs = None

logger = logging.getLogger(__name__)


def _get_key_password() -> Optional[bytes]:
    """
    Get the key encryption password from environment.

    The password is read from UATP_KEY_PASSWORD environment variable.
    If not set, returns None.

    Returns:
        Password bytes or None
    """
    password = os.environ.get("UATP_KEY_PASSWORD")
    if password:
        return password.encode("utf-8")
    return None


def _derive_key_password() -> bytes:
    """
    Derive a secure password for key encryption.

    Uses UATP_KEY_PASSWORD if set, otherwise generates a machine-specific
    password based on a combination of factors for development use.

    Returns:
        Password bytes
    """
    env_password = _get_key_password()
    if env_password:
        return env_password

    # For development: derive from machine-specific data
    # WARNING: This is less secure than using UATP_KEY_PASSWORD
    factors = [
        os.environ.get("USER", ""),
        os.environ.get("HOME", ""),
        "uatp-capsule-engine-v7-key",  # Salt specific to v7
    ]
    combined = ":".join(factors).encode("utf-8")
    derived = hashlib.pbkdf2_hmac("sha256", combined, b"uatp-v7-salt", 100000)

    logger.warning(
        "⚠️ Using derived key password. Set UATP_KEY_PASSWORD for production."
    )
    return derived


class UATPCryptoV7:
    """
    Unified cryptographic module for UATP 7.0 capsules.

    This class handles all cryptographic operations and outputs
    signatures in the correct UATP 7.0 verification format.
    """

    def __init__(
        self,
        key_dir: str = ".uatp_keys",
        signer_id: Optional[str] = None,
        enable_pq: bool = False,
    ):
        """
        Initialize UATP v7 crypto module.

        Args:
            key_dir: Directory to store cryptographic keys
            signer_id: Identifier for the signing entity (agent/user)
            enable_pq: Enable post-quantum (Dilithium3) signatures
        """
        self.key_dir = Path(key_dir)
        self.signer_id = signer_id or "local_engine"
        self.enable_pq = enable_pq and PQ_AVAILABLE

        # Check Ed25519 availability
        if not ED25519_AVAILABLE:
            logger.error(
                "❌ cryptography library not installed. Ed25519 signing disabled."
            )
            logger.error("   Install: pip install cryptography")
            self.enabled = False
            return

        self.enabled = True

        # Ensure keys exist
        self._ensure_keys_exist()
        self._load_keys()

        if self.enable_pq:
            logger.info("🔐 Post-quantum signatures enabled (Dilithium3)")

        logger.info(f"🔐 UATP v7 Crypto initialized for signer: {self.signer_id}")

    def _ensure_keys_exist(self):
        """Generate Ed25519 and Dilithium3 keypairs if they don't exist. Uses encrypted storage."""
        if not self.key_dir.exists():
            self.key_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Created key directory: {self.key_dir}")

        # Ed25519 keys - check encrypted first, then legacy
        ed25519_priv_enc = self.key_dir / "ed25519_private.pem.enc"
        ed25519_priv_legacy = self.key_dir / "ed25519_private.pem"
        ed25519_pub = self.key_dir / "ed25519_public.pem"

        # Determine which private key path to use
        if ed25519_priv_enc.exists():
            self._ed25519_priv_path = ed25519_priv_enc
            self._ed25519_encrypted = True
        elif ed25519_priv_legacy.exists():
            # Migrate unencrypted key to encrypted
            self._ed25519_priv_path = ed25519_priv_enc
            self._ed25519_encrypted = True
            self._migrate_ed25519_to_encrypted(ed25519_priv_legacy, ed25519_priv_enc)
        else:
            self._ed25519_priv_path = ed25519_priv_enc
            self._ed25519_encrypted = True

        self._ed25519_pub_path = ed25519_pub

        if not self._ed25519_priv_path.exists() or not ed25519_pub.exists():
            logger.info("🔑 Generating Ed25519 keypair with encrypted storage...")
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()

            # Get encryption password
            password = _derive_key_password()

            # Save private key with encryption
            with open(self._ed25519_priv_path, "wb") as f:
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
            with open(ed25519_pub, "wb") as f:
                f.write(
                    public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    )
                )

            # Set secure permissions on private key
            try:
                os.chmod(self._ed25519_priv_path, 0o600)
            except (OSError, AttributeError):
                pass

            logger.info(f"✅ Ed25519 encrypted keys saved to {self.key_dir}")

        # Dilithium3 keys (post-quantum) - encrypted storage
        if self.enable_pq:
            dil_priv_enc = self.key_dir / "dilithium3_private.bin.enc"
            dil_priv_legacy = self.key_dir / "dilithium3_private.bin"
            dil_pub = self.key_dir / "dilithium3_public.bin"

            # Determine which private key path to use
            if dil_priv_enc.exists():
                self._dil_priv_path = dil_priv_enc
                self._dil_encrypted = True
            elif dil_priv_legacy.exists():
                self._dil_priv_path = dil_priv_enc
                self._dil_encrypted = True
                self._migrate_dilithium_to_encrypted(dil_priv_legacy, dil_priv_enc)
            else:
                self._dil_priv_path = dil_priv_enc
                self._dil_encrypted = True

            self._dil_pub_path = dil_pub

            if not self._dil_priv_path.exists() or not dil_pub.exists():
                logger.info(
                    "🔑 Generating Dilithium3 keypair with encrypted storage..."
                )
                with oqs.Signature("Dilithium3") as sig:
                    public_key = sig.generate_keypair()
                    private_key = sig.export_secret_key()

                    # Encrypt the Dilithium private key
                    encrypted_priv = self._encrypt_binary_key(private_key)
                    with open(self._dil_priv_path, "wb") as f:
                        f.write(encrypted_priv)

                    with open(dil_pub, "wb") as f:
                        f.write(public_key)

                    # Set secure permissions
                    try:
                        os.chmod(self._dil_priv_path, 0o600)
                    except (OSError, AttributeError):
                        pass

                logger.info(f"✅ Dilithium3 encrypted keys saved to {self.key_dir}")

    def _encrypt_binary_key(self, key_data: bytes) -> bytes:
        """Encrypt binary key data using AES-256-GCM."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        password = _derive_key_password()
        # Derive AES key from password
        aes_key = hashlib.pbkdf2_hmac("sha256", password, b"dilithium-aes-key", 100000)

        # Generate nonce and encrypt
        nonce = os.urandom(12)
        aesgcm = AESGCM(aes_key)
        ciphertext = aesgcm.encrypt(nonce, key_data, None)

        # Return nonce + ciphertext
        return nonce + ciphertext

    def _decrypt_binary_key(self, encrypted_data: bytes) -> bytes:
        """Decrypt binary key data using AES-256-GCM."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        password = _derive_key_password()
        # Derive AES key from password
        aes_key = hashlib.pbkdf2_hmac("sha256", password, b"dilithium-aes-key", 100000)

        # Extract nonce and ciphertext
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]

        # Decrypt
        aesgcm = AESGCM(aes_key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    def _migrate_ed25519_to_encrypted(self, old_path: Path, new_path: Path):
        """Migrate an unencrypted Ed25519 private key to encrypted storage."""
        try:
            logger.info("🔄 Migrating Ed25519 key to encrypted storage...")

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
                f.write(os.urandom(1024))
            old_path.unlink()

            logger.info("✅ Ed25519 key migration complete.")

        except Exception as e:
            logger.error(f"❌ Ed25519 key migration failed: {e}")
            raise

    def _migrate_dilithium_to_encrypted(self, old_path: Path, new_path: Path):
        """Migrate an unencrypted Dilithium private key to encrypted storage."""
        try:
            logger.info("🔄 Migrating Dilithium3 key to encrypted storage...")

            # Load unencrypted key
            with open(old_path, "rb") as f:
                private_key = f.read()

            # Encrypt and save
            encrypted_priv = self._encrypt_binary_key(private_key)
            with open(new_path, "wb") as f:
                f.write(encrypted_priv)

            # Set secure permissions
            try:
                os.chmod(new_path, 0o600)
            except (OSError, AttributeError):
                pass

            # Securely delete old unencrypted key
            with open(old_path, "wb") as f:
                f.write(os.urandom(len(private_key)))
            old_path.unlink()

            logger.info("✅ Dilithium3 key migration complete.")

        except Exception as e:
            logger.error(f"❌ Dilithium3 key migration failed: {e}")
            raise

    def _load_keys(self):
        """Load cryptographic keys from disk. Supports both encrypted and legacy keys."""
        # Load Ed25519 keys
        password = _derive_key_password() if self._ed25519_encrypted else None

        try:
            with open(self._ed25519_priv_path, "rb") as f:
                self.ed25519_private = serialization.load_pem_private_key(
                    f.read(), password=password
                )
        except TypeError:
            # Key might be unencrypted if migration failed
            logger.warning("⚠️ Attempting to load Ed25519 key without password...")
            with open(self._ed25519_priv_path, "rb") as f:
                self.ed25519_private = serialization.load_pem_private_key(
                    f.read(), password=None
                )

        with open(self._ed25519_pub_path, "rb") as f:
            self.ed25519_public = serialization.load_pem_public_key(f.read())

        logger.info("🔐 Ed25519 keys loaded successfully")

        # Load Dilithium3 keys (if enabled)
        if self.enable_pq:
            try:
                with open(self._dil_priv_path, "rb") as f:
                    encrypted_data = f.read()
                    if self._dil_encrypted:
                        self.dilithium3_private = self._decrypt_binary_key(
                            encrypted_data
                        )
                    else:
                        self.dilithium3_private = encrypted_data
            except Exception as e:
                logger.warning(f"⚠️ Dilithium3 private key load failed: {e}")
                # Try loading as unencrypted
                with open(self._dil_priv_path, "rb") as f:
                    self.dilithium3_private = f.read()

            with open(self._dil_pub_path, "rb") as f:
                self.dilithium3_public = f.read()

            logger.info("🔐 Dilithium3 keys loaded successfully")

    def _compute_content_hash(self, data: Dict[str, Any]) -> str:
        """
        Compute SHA256 hash of capsule content.

        Args:
            data: Capsule data dictionary

        Returns:
            Hash in format "sha256:hex_string"
        """
        # Create canonical representation
        # Exclude verification field itself to avoid circular dependency
        canonical_data = {k: v for k, v in data.items() if k != "verification"}
        canonical_json = json.dumps(
            canonical_data, sort_keys=True, separators=(",", ":")
        )

        # Compute SHA256
        hash_bytes = hashlib.sha256(canonical_json.encode("utf-8")).digest()
        hash_hex = hash_bytes.hex()

        return f"sha256:{hash_hex}"

    def _compute_merkle_root(self, data: Dict[str, Any]) -> str:
        """
        Compute Merkle root for the capsule.

        For single capsules, computes based on content hash.
        When the global chain manager is available, uses the chain's Merkle tree.

        Args:
            data: Capsule data dictionary

        Returns:
            Merkle root in format "sha256:hex_string"
        """
        try:
            # Try to use the chain Merkle manager for proper tree computation
            from src.security.merkle_tree import get_chain_merkle_manager

            manager = get_chain_merkle_manager()
            capsule_id = data.get("capsule_id")

            if capsule_id:
                # Add to chain and get updated root
                return manager.add_capsule(capsule_id, data)
            else:
                # Fallback for capsules without ID
                content_hash = self._compute_content_hash(data)
                return content_hash

        except ImportError:
            # Merkle tree module not available - use simple hash
            logger.debug("Merkle tree module not available, using content hash")
            content_hash = self._compute_content_hash(data)
            return content_hash
        except Exception as e:
            # Any other error - fallback to simple hash
            logger.warning(f"Merkle root computation failed: {e}, using content hash")
            content_hash = self._compute_content_hash(data)
            return content_hash

    def _sign_ed25519(self, data: Dict[str, Any]) -> str:
        """
        Create Ed25519 signature of the capsule.

        Args:
            data: Capsule data dictionary

        Returns:
            Signature in format "ed25519:hex_string"
        """
        # Sign the content hash string (not binary bytes) to match CryptoSealer/crypto_utils
        content_hash = self._compute_content_hash(data)
        # Extract plain hex string (remove 'sha256:' prefix if present)
        hash_hex = (
            content_hash.split(":", 1)[1] if ":" in content_hash else content_hash
        )
        hash_bytes = hash_hex.encode("utf-8")

        # Sign
        signature_bytes = self.ed25519_private.sign(hash_bytes)
        signature_hex = signature_bytes.hex()

        return f"ed25519:{signature_hex}"

    def _sign_dilithium3(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Create Dilithium3 (post-quantum) signature of the capsule.

        Args:
            data: Capsule data dictionary

        Returns:
            Signature in format "dilithium3:hex_string" or None if PQ disabled
        """
        if not self.enable_pq:
            return None

        # Sign the content hash string (not binary bytes) to match CryptoSealer/crypto_utils
        content_hash = self._compute_content_hash(data)
        # Extract plain hex string (remove 'sha256:' prefix)
        hash_hex = (
            content_hash.split(":", 1)[1] if ":" in content_hash else content_hash
        )
        hash_bytes = hash_hex.encode("utf-8")

        # Sign with Dilithium3
        with oqs.Signature("Dilithium3", secret_key=self.dilithium3_private) as sig:
            signature_bytes = sig.sign(hash_bytes)
            signature_hex = signature_bytes.hex()

        return f"dilithium3:{signature_hex}"

    def _verify_dilithium3(
        self, hash_bytes: bytes, pq_signature: str
    ) -> Tuple[bool, str]:
        """
        Verify a Dilithium3 (post-quantum) signature.

        Args:
            hash_bytes: The hash bytes that were signed
            pq_signature: Signature in format "dilithium3:hex_string"

        Returns:
            Tuple of (is_valid: bool, reason: str)
        """
        if not self.enable_pq or not PQ_AVAILABLE:
            return False, "Post-quantum crypto not available"

        try:
            # Parse signature format
            if not pq_signature.startswith("dilithium3:"):
                return (
                    False,
                    "Invalid PQ signature format (expected 'dilithium3:' prefix)",
                )

            signature_hex = pq_signature.split(":", 1)[1]

            # Validate signature length (Dilithium3 signatures are ~3293 bytes)
            # In hex that's ~6586 characters, but can vary slightly
            if len(signature_hex) < 5000 or len(signature_hex) > 8000:
                return (
                    False,
                    f"Invalid Dilithium3 signature length: {len(signature_hex)}",
                )

            signature_bytes = bytes.fromhex(signature_hex)

            # Verify using liboqs
            # Note: We need to use the stored public key for verification
            with oqs.Signature("Dilithium3") as sig:
                # Load our public key for verification
                is_valid = sig.verify(
                    hash_bytes, signature_bytes, self.dilithium3_public
                )

                if is_valid:
                    return True, "Dilithium3 signature valid"
                else:
                    return False, "Dilithium3 signature invalid"

        except ValueError as e:
            return False, f"Hex decode error: {e}"
        except Exception as e:
            logger.error(f"❌ Dilithium3 verification error: {e}", exc_info=True)
            return False, f"Verification error: {e}"

    def _get_public_key_hex(self) -> str:
        """
        Get Ed25519 public key in hex format.

        Returns:
            Public key as hex string
        """
        public_bytes = self.ed25519_public.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
        return public_bytes.hex()

    def sign_capsule(self, capsule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign a capsule and return UATP 7.0 verification object.

        This is the main entry point for signing capsules.

        Args:
            capsule_data: Complete capsule data (without verification field)

        Returns:
            UATP 7.0 verification object:
            {
                "signer": str,
                "verify_key": str (hex),
                "hash": "sha256:...",
                "signature": "ed25519:...",
                "pq_signature": "dilithium3:..." or None,
                "merkle_root": "sha256:..."
            }
        """
        if not self.enabled:
            logger.warning("⚠️ Crypto not enabled - returning placeholder verification")
            return self._create_placeholder_verification()

        try:
            # Compute all cryptographic components
            content_hash = self._compute_content_hash(capsule_data)
            ed25519_sig = self._sign_ed25519(capsule_data)
            merkle_root = self._compute_merkle_root(capsule_data)
            public_key_hex = self._get_public_key_hex()

            # Optional post-quantum signature
            pq_sig = self._sign_dilithium3(capsule_data) if self.enable_pq else None

            verification = {
                "signer": self.signer_id,
                "verify_key": public_key_hex,
                "hash": content_hash,
                "signature": ed25519_sig,
                "pq_signature": pq_sig,
                "merkle_root": merkle_root,
            }

            logger.debug(
                f"✅ Signed capsule {capsule_data.get('capsule_id', 'unknown')}"
            )
            return verification

        except Exception as e:
            logger.error(f"❌ Signing failed: {e}", exc_info=True)
            return self._create_placeholder_verification()

    def verify_capsule(
        self, capsule_data: Dict[str, Any], verification: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Verify a signed capsule.

        Args:
            capsule_data: Capsule data (without verification field)
            verification: UATP 7.0 verification object

        Returns:
            Tuple of (is_valid: bool, reason: str)
        """
        if not self.enabled:
            return False, "Crypto not enabled"

        try:
            # Verify content hash
            expected_hash = self._compute_content_hash(capsule_data)
            if verification.get("hash") != expected_hash:
                return (
                    False,
                    f"Hash mismatch: expected {expected_hash}, got {verification.get('hash')}",
                )

            # Verify Ed25519 signature
            signature_str = verification.get("signature", "")
            if not signature_str.startswith("ed25519:"):
                return False, "Invalid signature format"

            signature_hex = signature_str.split(":", 1)[1]
            signature_bytes = bytes.fromhex(signature_hex)

            # Get the hash bytes that were signed (UTF-8 encoded hex string, not raw bytes)
            hash_hex = (
                expected_hash.split(":", 1)[1]
                if ":" in expected_hash
                else expected_hash
            )
            hash_bytes = hash_hex.encode("utf-8")

            # Load public key from verification
            verify_key_hex = verification.get("verify_key")
            if not verify_key_hex:
                return False, "No verify_key in verification"

            verify_key_bytes = bytes.fromhex(verify_key_hex)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(verify_key_bytes)

            # Verify signature
            try:
                public_key.verify(signature_bytes, hash_bytes)
            except Exception as e:
                return False, f"Signature verification failed: {e}"

            # Verify PQ signature if present
            pq_signature = verification.get("pq_signature")
            if pq_signature and self.enable_pq:
                pq_valid, pq_reason = self._verify_dilithium3(hash_bytes, pq_signature)
                if not pq_valid:
                    return False, f"Post-quantum verification failed: {pq_reason}"
                logger.info("✅ Dilithium3 post-quantum signature verified")

            return True, "Signature valid"

        except Exception as e:
            logger.error(f"❌ Verification failed: {e}", exc_info=True)
            return False, f"Verification error: {e}"

    def _create_placeholder_verification(self) -> Dict[str, Any]:
        """
        Create a placeholder verification object (all zeros).
        Used when crypto is disabled or signing fails.
        """
        return {
            "signer": self.signer_id,
            "verify_key": None,
            "hash": None,
            "signature": "ed25519:" + "0" * 128,
            "pq_signature": None,
            "merkle_root": "sha256:" + "0" * 64,
        }


# Singleton instance for convenience
_default_crypto: Optional[UATPCryptoV7] = None


def get_default_crypto(enable_pq: bool = False) -> UATPCryptoV7:
    """
    Get or create the default UATP crypto instance.

    Args:
        enable_pq: Enable post-quantum signatures

    Returns:
        UATPCryptoV7 instance
    """
    global _default_crypto
    if _default_crypto is None:
        _default_crypto = UATPCryptoV7(enable_pq=enable_pq)
    return _default_crypto
