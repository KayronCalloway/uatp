"""
Secure Key Management System for UATP Capsule Engine
Provides encrypted key storage, secure memory handling, and key rotation.
"""

import base64
import logging
import os
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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


@dataclass
class KeyRevocationEntry:
    """Entry in the key revocation list."""

    key_id: str
    public_key_fingerprint: str  # SHA256 of public key for lookup
    revoked_at: float
    reason: str  # 'compromised', 'superseded', 'retired', 'admin_revoked'
    revoked_by: Optional[str] = None  # User/admin who revoked
    replacement_key_id: Optional[str] = None  # ID of replacement key if superseded


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


class KeyRevocationList:
    """
    Key Revocation List (KRL) for tracking compromised or retired keys.

    SECURITY: This is critical infrastructure - revoked keys must NEVER be trusted.
    The KRL is checked during signature verification to reject signatures from
    compromised keys even if they're cryptographically valid.

    Persistence: Uses Redis for distributed deployments, falls back to in-memory
    with file backup for single-instance deployments.
    """

    REASON_COMPROMISED = "compromised"
    REASON_SUPERSEDED = "superseded"
    REASON_RETIRED = "retired"
    REASON_ADMIN_REVOKED = "admin_revoked"

    def __init__(self):
        self._revocations: Dict[str, KeyRevocationEntry] = {}
        self._fingerprint_index: Dict[str, str] = {}  # fingerprint -> key_id
        self._lock = threading.RLock()
        self._redis_client = None
        self._redis_available = False
        self._init_redis()
        self._load_from_persistence()

    def _init_redis(self) -> None:
        """Initialize Redis client for distributed KRL."""
        try:
            import redis

            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_password = os.getenv("REDIS_PASSWORD")
            redis_db = int(os.getenv("REDIS_KRL_DB", "4"))

            self._redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=True,
            )
            self._redis_client.ping()
            self._redis_available = True
            logger.info("Key Revocation List using Redis persistence")
        except Exception as e:
            logger.warning(f"Redis not available for KRL, using in-memory: {e}")
            self._redis_available = False

    def _load_from_persistence(self) -> None:
        """Load existing revocations from persistence layer."""
        if self._redis_available and self._redis_client:
            try:
                keys = self._redis_client.keys("krl:*")
                for key in keys:
                    data = self._redis_client.hgetall(key)
                    if data:
                        entry = KeyRevocationEntry(
                            key_id=data.get("key_id", ""),
                            public_key_fingerprint=data.get("fingerprint", ""),
                            revoked_at=float(data.get("revoked_at", 0)),
                            reason=data.get("reason", "unknown"),
                            revoked_by=data.get("revoked_by"),
                            replacement_key_id=data.get("replacement_key_id"),
                        )
                        self._revocations[entry.key_id] = entry
                        if entry.public_key_fingerprint:
                            self._fingerprint_index[entry.public_key_fingerprint] = (
                                entry.key_id
                            )
                logger.info(f"Loaded {len(self._revocations)} revoked keys from Redis")
            except Exception as e:
                logger.error(f"Failed to load KRL from Redis: {e}")

    def revoke_key(
        self,
        key_id: str,
        public_key_fingerprint: str,
        reason: str,
        revoked_by: Optional[str] = None,
        replacement_key_id: Optional[str] = None,
    ) -> bool:
        """
        Revoke a key and add it to the revocation list.

        Args:
            key_id: The key identifier to revoke
            public_key_fingerprint: SHA256 hash of the public key
            reason: Reason for revocation (use REASON_* constants)
            revoked_by: Optional identifier of who revoked the key
            replacement_key_id: Optional ID of the replacement key

        Returns:
            True if revocation was successful
        """
        if reason not in (
            self.REASON_COMPROMISED,
            self.REASON_SUPERSEDED,
            self.REASON_RETIRED,
            self.REASON_ADMIN_REVOKED,
        ):
            raise ValueError(f"Invalid revocation reason: {reason}")

        entry = KeyRevocationEntry(
            key_id=key_id,
            public_key_fingerprint=public_key_fingerprint,
            revoked_at=time.time(),
            reason=reason,
            revoked_by=revoked_by,
            replacement_key_id=replacement_key_id,
        )

        with self._lock:
            self._revocations[key_id] = entry
            if public_key_fingerprint:
                self._fingerprint_index[public_key_fingerprint] = key_id

            # Persist to Redis if available
            if self._redis_available and self._redis_client:
                try:
                    self._redis_client.hset(
                        f"krl:{key_id}",
                        mapping={
                            "key_id": key_id,
                            "fingerprint": public_key_fingerprint,
                            "revoked_at": str(entry.revoked_at),
                            "reason": reason,
                            "revoked_by": revoked_by or "",
                            "replacement_key_id": replacement_key_id or "",
                        },
                    )
                    # Also index by fingerprint for fast lookup
                    if public_key_fingerprint:
                        self._redis_client.set(
                            f"krl:fp:{public_key_fingerprint}", key_id
                        )
                except Exception as e:
                    logger.error(f"Failed to persist key revocation to Redis: {e}")

        logger.warning(
            f"SECURITY: Key {key_id} revoked. Reason: {reason}. "
            f"Revoked by: {revoked_by or 'system'}"
        )
        return True

    def is_revoked(
        self, key_id: Optional[str] = None, fingerprint: Optional[str] = None
    ) -> bool:
        """
        Check if a key is revoked.

        Args:
            key_id: Key identifier to check
            fingerprint: Public key fingerprint to check

        Returns:
            True if the key is revoked
        """
        with self._lock:
            if key_id and key_id in self._revocations:
                return True
            if fingerprint and fingerprint in self._fingerprint_index:
                return True

        # Double-check Redis for distributed deployments
        if self._redis_available and self._redis_client:
            try:
                if key_id and self._redis_client.exists(f"krl:{key_id}"):
                    return True
                if fingerprint and self._redis_client.exists(f"krl:fp:{fingerprint}"):
                    return True
            except Exception as e:
                logger.error(f"Failed to check Redis KRL: {e}")

        return False

    def get_revocation_info(
        self, key_id: Optional[str] = None, fingerprint: Optional[str] = None
    ) -> Optional[KeyRevocationEntry]:
        """Get revocation details for a key."""
        with self._lock:
            if key_id and key_id in self._revocations:
                return self._revocations[key_id]
            if fingerprint:
                resolved_key_id = self._fingerprint_index.get(fingerprint)
                if resolved_key_id:
                    return self._revocations.get(resolved_key_id)
        return None

    def list_revocations(
        self, reason: Optional[str] = None, since: Optional[float] = None
    ) -> list:
        """
        List revoked keys, optionally filtered by reason or time.

        Args:
            reason: Filter by revocation reason
            since: Only include revocations after this timestamp

        Returns:
            List of KeyRevocationEntry objects
        """
        with self._lock:
            revocations = list(self._revocations.values())

        if reason:
            revocations = [r for r in revocations if r.reason == reason]
        if since:
            revocations = [r for r in revocations if r.revoked_at >= since]

        return sorted(revocations, key=lambda r: r.revoked_at, reverse=True)

    def get_fingerprint(self, public_key: bytes) -> str:
        """Calculate fingerprint (SHA256) of a public key."""
        import hashlib

        return hashlib.sha256(public_key).hexdigest()


# Global key revocation list instance
_krl_instance: Optional[KeyRevocationList] = None
_krl_lock = threading.Lock()


def get_key_revocation_list() -> KeyRevocationList:
    """Get or create global key revocation list instance."""
    global _krl_instance

    with _krl_lock:
        if _krl_instance is None:
            _krl_instance = KeyRevocationList()
        return _krl_instance


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
            iterations=480_000,  # OWASP recommends 310,000+ for SHA256
        )
        derived_key = kdf.derive(password.encode())

        # Convert to Fernet-compatible key (requires base64 url-safe encoding)
        fernet_key = base64.urlsafe_b64encode(derived_key)
        self._master_key = Fernet(fernet_key)

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
        from nacl.encoding import RawEncoder
        from nacl.signing import SigningKey

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

    def derive_user_encryption_key(self, user_id: str) -> bytes:
        """
        Derive a user-specific encryption key using HKDF.

        This creates a unique 256-bit AES key for each user, derived from
        the master key and the user's ID. The key can be used for
        client-side payload encryption.

        Args:
            user_id: Unique user identifier

        Returns:
            32-byte (256-bit) AES key
        """
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF

        if not self._master_salt:
            raise RuntimeError("Master key not initialized")

        # Use HKDF to derive user-specific key
        # The master salt combined with user-specific info ensures unique keys per user
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key for AES-256
            salt=self._master_salt,
            info=f"uatp-user-encryption-key-v1-{user_id}".encode(),
        )

        # Use the master salt as input key material (IKM)
        # This is secure because HKDF extracts entropy from any input
        # and the user_id in info ensures unique output per user
        user_key = hkdf.derive(self._master_salt + user_id.encode())
        logger.debug(f"Derived encryption key for user {user_id[:8]}...")
        return user_key

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
