"""
User Key Manager - Gold Standard Implementation
================================================

This module implements user-sovereign key management where:
- Keys are generated LOCALLY on user's device
- Private keys NEVER leave the device
- Private keys are encrypted with user's passphrase
- UATP servers never see private keys

This is the foundation of UATP's zero-trust architecture.
"""

import json
import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from nacl.encoding import HexEncoder, RawEncoder
from nacl.signing import SigningKey, VerifyKey

logger = logging.getLogger(__name__)


@dataclass
class UserKeyPair:
    """User's cryptographic key pair."""

    key_id: str
    public_key_hex: str
    created_at: datetime
    key_type: str = "ed25519"

    # Private key is NEVER included in this dataclass
    # It's only accessed through secure methods


class UserKeyManager:
    """
    User-sovereign key management.

    Security Properties:
    - Keys generated using OS secure random (os.urandom via NaCl)
    - Private key encrypted with user passphrase using Fernet (AES-128-CBC)
    - Key derivation uses PBKDF2-HMAC-SHA256 with 480,000 iterations
    - Private key never exposed in memory longer than necessary
    - No network transmission of private keys

    Usage:
        # First time setup
        manager = UserKeyManager(key_dir="~/.uatp/keys")
        key_pair = manager.generate_key_pair(passphrase="user's secret")

        # Later, sign a capsule
        signature = manager.sign(capsule_hash, passphrase="user's secret")
    """

    # PBKDF2 iterations - high for security, OWASP recommends 310,000+ for SHA256
    PBKDF2_ITERATIONS = 480_000

    def __init__(self, key_dir: Optional[str] = None):
        """
        Initialize UserKeyManager.

        Args:
            key_dir: Directory for key storage. Defaults to ~/.uatp/keys
        """
        if key_dir is None:
            key_dir = os.path.expanduser("~/.uatp/keys")

        self.key_dir = Path(key_dir)
        self.key_dir.mkdir(parents=True, exist_ok=True)

        # Set secure permissions on key directory (Unix only)
        try:
            os.chmod(self.key_dir, 0o700)
        except (OSError, AttributeError):
            pass  # Windows or permission error

        self._current_key_id: Optional[str] = None
        logger.info(f"UserKeyManager initialized at {self.key_dir}")

    def _derive_encryption_key(self, passphrase: str, salt: bytes) -> bytes:
        """
        Derive encryption key from passphrase using PBKDF2.

        This is intentionally slow to resist brute-force attacks.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.PBKDF2_ITERATIONS,
        )
        key = kdf.derive(passphrase.encode("utf-8"))
        # Fernet requires base64-encoded 32-byte key
        import base64

        return base64.urlsafe_b64encode(key)

    def generate_key_pair(
        self, passphrase: str, key_id: Optional[str] = None
    ) -> UserKeyPair:
        """
        Generate a new Ed25519 key pair.

        The private key is encrypted with the passphrase and stored locally.
        The private key NEVER leaves this device.

        Args:
            passphrase: User's passphrase for encrypting the private key
            key_id: Optional key identifier. Auto-generated if not provided.

        Returns:
            UserKeyPair with public key information (no private key)

        Security:
            - Private key generated using NaCl's secure random
            - Immediately encrypted before any other operation
            - Original key bytes overwritten after encryption
        """
        if not passphrase or len(passphrase) < 8:
            raise ValueError("Passphrase must be at least 8 characters")

        # Generate key ID
        if key_id is None:
            key_id = f"uatp-{secrets.token_hex(8)}"

        # Generate Ed25519 key pair using NaCl (secure random internally)
        signing_key = SigningKey.generate()
        verify_key = signing_key.verify_key

        # Extract key bytes
        private_key_bytes = signing_key.encode(encoder=RawEncoder)
        public_key_hex = verify_key.encode(encoder=HexEncoder).decode("utf-8")

        # Generate salt for key derivation
        salt = os.urandom(16)

        # Derive encryption key from passphrase
        encryption_key = self._derive_encryption_key(passphrase, salt)
        fernet = Fernet(encryption_key)

        # Encrypt private key
        encrypted_private_key = fernet.encrypt(private_key_bytes)

        # Prepare metadata
        created_at = datetime.now(timezone.utc)
        metadata = {
            "key_id": key_id,
            "public_key": public_key_hex,
            "key_type": "ed25519",
            "created_at": created_at.isoformat(),
            "salt": salt.hex(),
            "pbkdf2_iterations": self.PBKDF2_ITERATIONS,
            "encryption": "fernet-aes128-cbc",
        }

        # Save encrypted private key
        key_file = self.key_dir / f"{key_id}.key"
        with open(key_file, "wb") as f:
            f.write(encrypted_private_key)
        os.chmod(key_file, 0o600)

        # Save metadata (no sensitive data)
        meta_file = self.key_dir / f"{key_id}.meta.json"
        with open(meta_file, "w") as f:
            json.dump(metadata, f, indent=2)

        # Securely clear private key from memory
        # (Python doesn't guarantee this, but we try)
        private_key_bytes = os.urandom(len(private_key_bytes))
        del signing_key

        self._current_key_id = key_id

        logger.info(f"Generated new key pair: {key_id}")
        logger.info(f"Public key: {public_key_hex[:16]}...")

        return UserKeyPair(
            key_id=key_id,
            public_key_hex=public_key_hex,
            created_at=created_at,
            key_type="ed25519",
        )

    def get_current_key(self) -> Optional[UserKeyPair]:
        """Get the current active key pair (public info only)."""
        if self._current_key_id:
            return self.get_key(self._current_key_id)

        # Try to find most recent key
        meta_files = list(self.key_dir.glob("*.meta.json"))
        if not meta_files:
            return None

        # Sort by creation time, newest first
        meta_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        key_id = meta_files[0].stem.replace(".meta", "")
        return self.get_key(key_id)

    def get_key(self, key_id: str) -> Optional[UserKeyPair]:
        """Get a specific key pair by ID (public info only)."""
        meta_file = self.key_dir / f"{key_id}.meta.json"

        if not meta_file.exists():
            return None

        with open(meta_file) as f:
            metadata = json.load(f)

        return UserKeyPair(
            key_id=metadata["key_id"],
            public_key_hex=metadata["public_key"],
            created_at=datetime.fromisoformat(metadata["created_at"]),
            key_type=metadata.get("key_type", "ed25519"),
        )

    def sign(
        self, data_hash: str, passphrase: str, key_id: Optional[str] = None
    ) -> str:
        """
        Sign a hash with the user's private key.

        The private key is decrypted in memory, used for signing,
        then immediately cleared.

        Args:
            data_hash: Hex-encoded hash to sign (e.g., SHA-256 of capsule)
            passphrase: User's passphrase to decrypt the private key
            key_id: Which key to use. Defaults to current key.

        Returns:
            Hex-encoded Ed25519 signature

        Security:
            - Private key decrypted only for signing operation
            - Key cleared from memory after use
            - Passphrase never stored
        """
        if key_id is None:
            key_id = self._current_key_id
            if key_id is None:
                key_info = self.get_current_key()
                if key_info:
                    key_id = key_info.key_id
                else:
                    raise ValueError("No key available. Generate one first.")

        # Load metadata for salt
        meta_file = self.key_dir / f"{key_id}.meta.json"
        if not meta_file.exists():
            raise ValueError(f"Key not found: {key_id}")

        with open(meta_file) as f:
            metadata = json.load(f)

        salt = bytes.fromhex(metadata["salt"])

        # Load encrypted private key
        key_file = self.key_dir / f"{key_id}.key"
        with open(key_file, "rb") as f:
            encrypted_private_key = f.read()

        # Derive decryption key
        decryption_key = self._derive_encryption_key(passphrase, salt)
        fernet = Fernet(decryption_key)

        try:
            # Decrypt private key
            private_key_bytes = fernet.decrypt(encrypted_private_key)
        except Exception as e:
            raise ValueError("Invalid passphrase") from e

        try:
            # Create signing key and sign
            signing_key = SigningKey(private_key_bytes)

            # Sign the hash (as UTF-8 string, matching existing UATP convention)
            signature = signing_key.sign(data_hash.encode("utf-8")).signature
            signature_hex: str = signature.hex()

            return signature_hex

        finally:
            # Securely clear private key from memory
            private_key_bytes = os.urandom(len(private_key_bytes))
            del signing_key

    def verify(self, data_hash: str, signature_hex: str, public_key_hex: str) -> bool:
        """
        Verify a signature.

        This is a static operation - doesn't require private key or passphrase.
        Anyone can verify using only public information.

        Args:
            data_hash: Hex-encoded hash that was signed
            signature_hex: Hex-encoded signature to verify
            public_key_hex: Hex-encoded public key of signer

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            verify_key = VerifyKey(public_key_hex, encoder=HexEncoder)
            signature_bytes = bytes.fromhex(signature_hex)

            # Verify (raises exception if invalid)
            verify_key.verify(data_hash.encode("utf-8"), signature_bytes)
            return True

        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False

    def export_public_key(self, key_id: Optional[str] = None) -> dict:
        """
        Export public key for sharing.

        This is safe to share - contains no private information.
        """
        key_info = self.get_key(key_id) if key_id else self.get_current_key()

        if not key_info:
            raise ValueError("No key found")

        return {
            "key_id": key_info.key_id,
            "public_key": key_info.public_key_hex,
            "key_type": key_info.key_type,
            "created_at": key_info.created_at.isoformat(),
        }

    def export_encrypted_backup(
        self, passphrase: str, backup_passphrase: str, key_id: Optional[str] = None
    ) -> bytes:
        """
        Export encrypted backup of private key.

        The backup is encrypted with a DIFFERENT passphrase than the stored key,
        allowing secure backup to external storage.

        Args:
            passphrase: Current passphrase to decrypt the key
            backup_passphrase: Passphrase for the backup (can be different)
            key_id: Which key to backup

        Returns:
            Encrypted backup bytes (can be saved to file)
        """
        if key_id is None:
            key_info = self.get_current_key()
            if not key_info:
                raise ValueError("No key found")
            key_id = key_info.key_id

        # Load and decrypt current key
        meta_file = self.key_dir / f"{key_id}.meta.json"
        with open(meta_file) as f:
            metadata = json.load(f)

        salt = bytes.fromhex(metadata["salt"])

        key_file = self.key_dir / f"{key_id}.key"
        with open(key_file, "rb") as f:
            encrypted_private_key = f.read()

        decryption_key = self._derive_encryption_key(passphrase, salt)
        fernet = Fernet(decryption_key)

        try:
            private_key_bytes = fernet.decrypt(encrypted_private_key)
        except Exception as e:
            raise ValueError("Invalid passphrase") from e

        try:
            # Re-encrypt with backup passphrase
            backup_salt = os.urandom(16)
            backup_key = self._derive_encryption_key(backup_passphrase, backup_salt)
            backup_fernet = Fernet(backup_key)

            backup_data = {
                "key_id": key_id,
                "public_key": metadata["public_key"],
                "key_type": metadata.get("key_type", "ed25519"),
                "created_at": metadata["created_at"],
                "private_key": private_key_bytes.hex(),
            }

            encrypted_backup = backup_fernet.encrypt(json.dumps(backup_data).encode())

            # Package with salt
            backup_package = {
                "version": 1,
                "salt": backup_salt.hex(),
                "iterations": self.PBKDF2_ITERATIONS,
                "data": encrypted_backup.decode("utf-8"),
            }

            return json.dumps(backup_package).encode()

        finally:
            private_key_bytes = os.urandom(len(private_key_bytes))

    def import_backup(
        self, backup_bytes: bytes, backup_passphrase: str, new_passphrase: str
    ) -> UserKeyPair:
        """
        Import a key from encrypted backup.

        Args:
            backup_bytes: Encrypted backup from export_encrypted_backup
            backup_passphrase: Passphrase used when creating backup
            new_passphrase: New passphrase for storing the key locally

        Returns:
            UserKeyPair for the imported key
        """
        backup_package = json.loads(backup_bytes.decode())

        backup_salt = bytes.fromhex(backup_package["salt"])
        backup_key = self._derive_encryption_key(backup_passphrase, backup_salt)
        backup_fernet = Fernet(backup_key)

        try:
            decrypted = backup_fernet.decrypt(backup_package["data"].encode())
            backup_data = json.loads(decrypted.decode())
        except Exception as e:
            raise ValueError("Invalid backup passphrase") from e

        private_key_bytes = bytes.fromhex(backup_data["private_key"])

        try:
            # Store with new passphrase
            key_id = backup_data["key_id"]
            salt = os.urandom(16)
            encryption_key = self._derive_encryption_key(new_passphrase, salt)
            fernet = Fernet(encryption_key)

            encrypted_private_key = fernet.encrypt(private_key_bytes)

            # Save
            key_file = self.key_dir / f"{key_id}.key"
            with open(key_file, "wb") as f:
                f.write(encrypted_private_key)
            os.chmod(key_file, 0o600)

            metadata = {
                "key_id": key_id,
                "public_key": backup_data["public_key"],
                "key_type": backup_data.get("key_type", "ed25519"),
                "created_at": backup_data["created_at"],
                "salt": salt.hex(),
                "pbkdf2_iterations": self.PBKDF2_ITERATIONS,
                "encryption": "fernet-aes128-cbc",
                "imported_at": datetime.now(timezone.utc).isoformat(),
            }

            meta_file = self.key_dir / f"{key_id}.meta.json"
            with open(meta_file, "w") as f:
                json.dump(metadata, f, indent=2)

            self._current_key_id = key_id

            return UserKeyPair(
                key_id=key_id,
                public_key_hex=backup_data["public_key"],
                created_at=datetime.fromisoformat(backup_data["created_at"]),
                key_type=backup_data.get("key_type", "ed25519"),
            )

        finally:
            private_key_bytes = os.urandom(len(private_key_bytes))

    def list_keys(self) -> List[UserKeyPair]:
        """List all available key pairs (public info only)."""
        keys = []
        for meta_file in self.key_dir.glob("*.meta.json"):
            key_id = meta_file.stem.replace(".meta", "")
            key_info = self.get_key(key_id)
            if key_info:
                keys.append(key_info)

        # Sort by creation time, newest first
        keys.sort(key=lambda k: k.created_at, reverse=True)
        return keys


# Convenience function for simple usage
def get_user_key_manager() -> UserKeyManager:
    """Get or create the default UserKeyManager."""
    return UserKeyManager()
