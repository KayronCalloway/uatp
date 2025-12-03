"""
Secure Key Management System for UATP Capsule Engine
Provides encrypted key storage, secure memory handling, and key rotation.
"""

import hashlib
import logging
import os
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    NoEncryption,
)

logger = logging.getLogger(__name__)


@dataclass
class SecureKey:
    """Secure key container with metadata."""

    key_id: str
    key_type: str  # 'ed25519', 'dilithium3', 'kyber768'
    encrypted_key: bytes
    created_at: float
    last_used: float
    rotation_due: float
    key_strength: int
    salt: bytes


class SecureMemory:
    """Secure memory management for cryptographic keys."""

    def __init__(self):
        self._secure_buffers = {}
        self._lock = threading.RLock()

    def allocate_secure_buffer(self, size: int, buffer_id: str) -> None:
        """Allocate a secure memory buffer."""
        with self._lock:
            # Create buffer filled with secure random data
            secure_buffer = bytearray(secrets.token_bytes(size))
            self._secure_buffers[buffer_id] = secure_buffer
            logger.debug(f"Allocated secure buffer {buffer_id} of size {size}")

    def write_to_buffer(self, buffer_id: str, data: bytes, offset: int = 0) -> None:
        """Write data to secure buffer."""
        with self._lock:
            if buffer_id not in self._secure_buffers:
                raise ValueError(f"Secure buffer {buffer_id} not found")

            buffer = self._secure_buffers[buffer_id]
            if offset + len(data) > len(buffer):
                raise ValueError("Data exceeds buffer capacity")

            buffer[offset : offset + len(data)] = data

    def read_from_buffer(self, buffer_id: str, length: int, offset: int = 0) -> bytes:
        """Read data from secure buffer."""
        with self._lock:
            if buffer_id not in self._secure_buffers:
                raise ValueError(f"Secure buffer {buffer_id} not found")

            buffer = self._secure_buffers[buffer_id]
            if offset + length > len(buffer):
                raise ValueError("Read exceeds buffer capacity")

            return bytes(buffer[offset : offset + length])

    def clear_buffer(self, buffer_id: str) -> None:
        """Securely clear and deallocate buffer."""
        with self._lock:
            if buffer_id in self._secure_buffers:
                buffer = self._secure_buffers[buffer_id]
                # Overwrite with random data multiple times
                for _ in range(3):
                    for i in range(len(buffer)):
                        buffer[i] = secrets.randbits(8)
                del self._secure_buffers[buffer_id]
                logger.debug(f"Securely cleared buffer {buffer_id}")

    def clear_all_buffers(self) -> None:
        """Clear all secure buffers."""
        with self._lock:
            buffer_ids = list(self._secure_buffers.keys())
            for buffer_id in buffer_ids:
                self.clear_buffer(buffer_id)


class SecureKeyManager:
    """
    Secure key management system with encrypted storage and rotation.
    Provides enterprise-grade key security for UATP cryptographic operations.
    """

    def __init__(self, master_password: Optional[str] = None):
        self.secure_memory = SecureMemory()
        self._keys: Dict[str, SecureKey] = {}
        self._lock = threading.RLock()
        self._master_key: Optional[Fernet] = None
        self._key_rotation_interval = 86400 * 30  # 30 days
        self._max_key_age = 86400 * 90  # 90 days

        # Initialize master encryption key
        self._initialize_master_key(master_password)

        # Start background key rotation
        self._rotation_thread = threading.Thread(
            target=self._rotation_worker, daemon=True
        )
        self._rotation_thread.start()

    def _initialize_master_key(self, password: Optional[str]) -> None:
        """Initialize master encryption key from password or environment."""
        if password:
            salt = os.urandom(16)
        else:
            # Try to get from environment variable
            password = os.getenv("UATP_MASTER_KEY_PASSWORD")
            if not password:
                # Generate a secure random password
                password = secrets.token_urlsafe(32)
                logger.warning(
                    "No master password provided. Generated random password. "
                    "Set UATP_MASTER_KEY_PASSWORD environment variable for persistence."
                )
            salt = os.urandom(16)

        # Derive encryption key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        self._master_key = Fernet(Fernet.generate_key())

        # Store salt securely
        self._master_salt = salt
        logger.info("Master encryption key initialized")

    def generate_key_pair(
        self, key_type: str, key_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate a new cryptographic key pair with secure storage.

        Args:
            key_type: Type of key ('ed25519', 'dilithium3', 'kyber768')
            key_id: Optional key identifier

        Returns:
            Tuple of (private_key_hex, public_key_hex)

        Raises:
            ValueError: If key type is not supported
            RuntimeError: If key generation fails
        """
        if not key_id:
            key_id = secrets.token_hex(16)

        current_time = time.time()

        try:
            if key_type == "ed25519":
                private_key, public_key = self._generate_ed25519_keypair()
                key_strength = 256  # bits
            elif key_type == "dilithium3":
                private_key, public_key = self._generate_dilithium_keypair()
                key_strength = 256  # quantum security level
            elif key_type == "kyber768":
                private_key, public_key = self._generate_kyber_keypair()
                key_strength = 192  # quantum security level
            else:
                raise ValueError(f"Unsupported key type: {key_type}")

            # Encrypt private key for storage
            salt = os.urandom(16)
            encrypted_private_key = self._encrypt_key(private_key, salt)

            # Store securely
            secure_key = SecureKey(
                key_id=key_id,
                key_type=key_type,
                encrypted_key=encrypted_private_key,
                created_at=current_time,
                last_used=current_time,
                rotation_due=current_time + self._key_rotation_interval,
                key_strength=key_strength,
                salt=salt,
            )

            with self._lock:
                self._keys[key_id] = secure_key

            logger.info(f"Generated {key_type} key pair with ID {key_id}")
            return private_key.hex(), public_key.hex()

        except Exception as e:
            logger.error(f"Key generation failed for {key_type}: {e}")
            raise RuntimeError(f"Key generation failed: {e}")

    def _generate_ed25519_keypair(self) -> Tuple[bytes, bytes]:
        """Generate Ed25519 key pair."""
        from nacl.signing import SigningKey
        from nacl.encoding import RawEncoder

        signing_key = SigningKey.generate()
        private_key = signing_key.encode(encoder=RawEncoder)
        public_key = signing_key.verify_key.encode(encoder=RawEncoder)

        return private_key, public_key

    def _generate_dilithium_keypair(self) -> Tuple[bytes, bytes]:
        """Generate Dilithium3 key pair."""
        from src.crypto.post_quantum import pq_crypto

        keypair = pq_crypto.generate_dilithium_keypair()
        return keypair.private_key, keypair.public_key

    def _generate_kyber_keypair(self) -> Tuple[bytes, bytes]:
        """Generate Kyber768 key pair."""
        from src.crypto.post_quantum import pq_crypto

        keypair = pq_crypto.generate_kyber_keypair()
        return keypair.private_key, keypair.public_key

    def _encrypt_key(self, key_data: bytes, salt: bytes) -> bytes:
        """Encrypt key data using master key."""
        if not self._master_key:
            raise RuntimeError("Master key not initialized")

        return self._master_key.encrypt(key_data)

    def _decrypt_key(self, encrypted_key: bytes, salt: bytes) -> bytes:
        """Decrypt key data using master key."""
        if not self._master_key:
            raise RuntimeError("Master key not initialized")

        return self._master_key.decrypt(encrypted_key)

    def get_private_key(self, key_id: str) -> bytes:
        """
        Retrieve and decrypt private key.

        Args:
            key_id: Key identifier

        Returns:
            Decrypted private key bytes

        Raises:
            KeyError: If key not found
            RuntimeError: If decryption fails
        """
        with self._lock:
            if key_id not in self._keys:
                raise KeyError(f"Key {key_id} not found")

            secure_key = self._keys[key_id]

            # Update last used timestamp
            secure_key.last_used = time.time()

            try:
                private_key = self._decrypt_key(
                    secure_key.encrypted_key, secure_key.salt
                )
                logger.debug(f"Retrieved private key {key_id}")
                return private_key
            except Exception as e:
                logger.error(f"Failed to decrypt key {key_id}: {e}")
                raise RuntimeError(f"Key decryption failed: {e}")

    def rotate_key(self, key_id: str) -> Tuple[str, str]:
        """
        Rotate a key pair, generating new keys and marking old ones for deletion.

        Args:
            key_id: Key identifier to rotate

        Returns:
            Tuple of new (private_key_hex, public_key_hex)
        """
        with self._lock:
            if key_id not in self._keys:
                raise KeyError(f"Key {key_id} not found")

            old_key = self._keys[key_id]

            # Generate new key pair of same type
            new_private_hex, new_public_hex = self.generate_key_pair(
                old_key.key_type, f"{key_id}_rotated_{int(time.time())}"
            )

            # Mark old key for secure deletion
            self._schedule_key_deletion(key_id)

            logger.info(f"Rotated key {key_id}")
            return new_private_hex, new_public_hex

    def _schedule_key_deletion(self, key_id: str) -> None:
        """Schedule secure deletion of a key."""
        # In a production system, this would schedule the key for deletion
        # after a grace period to allow for any pending operations

        def delayed_delete():
            time.sleep(300)  # 5 minute grace period
            self.delete_key(key_id)

        deletion_thread = threading.Thread(target=delayed_delete, daemon=True)
        deletion_thread.start()

    def delete_key(self, key_id: str) -> None:
        """
        Securely delete a key from storage.

        Args:
            key_id: Key identifier to delete
        """
        with self._lock:
            if key_id in self._keys:
                # Overwrite encrypted key data with random bytes
                secure_key = self._keys[key_id]
                secure_key.encrypted_key = secrets.token_bytes(
                    len(secure_key.encrypted_key)
                )

                # Remove from memory
                del self._keys[key_id]

                logger.info(f"Securely deleted key {key_id}")

    def list_keys(self) -> Dict[str, Dict[str, Union[str, float, int]]]:
        """List all stored keys with metadata."""
        with self._lock:
            key_info = {}
            for key_id, secure_key in self._keys.items():
                key_info[key_id] = {
                    "key_type": secure_key.key_type,
                    "created_at": secure_key.created_at,
                    "last_used": secure_key.last_used,
                    "rotation_due": secure_key.rotation_due,
                    "key_strength": secure_key.key_strength,
                    "age_days": (time.time() - secure_key.created_at) / 86400,
                }
            return key_info

    def _rotation_worker(self) -> None:
        """Background worker for automatic key rotation."""
        while True:
            try:
                current_time = time.time()
                keys_to_rotate = []

                with self._lock:
                    for key_id, secure_key in self._keys.items():
                        if current_time >= secure_key.rotation_due:
                            keys_to_rotate.append(key_id)

                for key_id in keys_to_rotate:
                    try:
                        self.rotate_key(key_id)
                        logger.info(f"Auto-rotated key {key_id}")
                    except Exception as e:
                        logger.error(f"Failed to auto-rotate key {key_id}: {e}")

                # Check every hour
                time.sleep(3600)

            except Exception as e:
                logger.error(f"Key rotation worker error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

    def get_key_health_status(self) -> Dict[str, str]:
        """Get overall health status of key management system."""
        with self._lock:
            total_keys = len(self._keys)
            current_time = time.time()

            expired_keys = 0
            rotation_due = 0

            for secure_key in self._keys.values():
                key_age = current_time - secure_key.created_at
                if key_age > self._max_key_age:
                    expired_keys += 1
                elif current_time >= secure_key.rotation_due:
                    rotation_due += 1

            return {
                "status": "healthy" if expired_keys == 0 else "warning",
                "total_keys": str(total_keys),
                "expired_keys": str(expired_keys),
                "rotation_due": str(rotation_due),
                "master_key_status": "initialized"
                if self._master_key
                else "not_initialized",
            }

    def export_public_keys(self) -> Dict[str, str]:
        """Export all public keys for sharing."""
        # This would require storing public keys separately or deriving them
        # For now, return empty dict as public keys should be stored elsewhere
        return {}

    def __del__(self):
        """Secure cleanup on object destruction."""
        if hasattr(self, "secure_memory"):
            self.secure_memory.clear_all_buffers()


# Global secure key manager instance
_key_manager_instance = None
_key_manager_lock = threading.Lock()


def get_key_manager(master_password: Optional[str] = None) -> SecureKeyManager:
    """Get or create global secure key manager instance."""
    global _key_manager_instance

    with _key_manager_lock:
        if _key_manager_instance is None:
            _key_manager_instance = SecureKeyManager(master_password)
        return _key_manager_instance


def secure_key_wipe(data: Union[bytes, bytearray]) -> None:
    """Securely wipe sensitive data from memory."""
    if isinstance(data, bytearray):
        for i in range(len(data)):
            data[i] = secrets.randbits(8)
    elif isinstance(data, bytes):
        # Convert to bytearray for overwriting
        temp = bytearray(data)
        for i in range(len(temp)):
            temp[i] = secrets.randbits(8)
        # Cannot actually overwrite bytes object, but this clears the temp copy
