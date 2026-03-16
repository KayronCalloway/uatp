"""
Cryptographic Key Rotation Manager
==================================

Provides secure key rotation for UATP cryptographic operations:
- Scheduled key replacement
- Key versioning and archival
- Re-signing capabilities
- Revocation support

Security Properties:
- Forward secrecy through rotation
- Key compromise recovery
- Audit trail of key changes
- Graceful transition periods
"""

import hashlib
import json
import logging
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class KeyStatus(Enum):
    """Status of a cryptographic key."""

    ACTIVE = "active"  # Currently in use for signing
    PENDING = "pending"  # Generated, waiting to become active
    ARCHIVED = "archived"  # No longer for signing, still valid for verification
    REVOKED = "revoked"  # Compromised, must not be trusted
    EXPIRED = "expired"  # Past validity period


class KeyType(Enum):
    """Type of cryptographic key."""

    ED25519 = "ed25519"
    ML_DSA_65 = "ml-dsa-65"
    HYBRID = "hybrid"


@dataclass
class KeyMetadata:
    """Metadata for a cryptographic key."""

    key_id: str
    key_type: KeyType
    version: int
    status: KeyStatus
    created_at: datetime
    activated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    public_key_hash: str = ""
    algorithm_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key_id": self.key_id,
            "key_type": self.key_type.value,
            "version": self.version,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "activated_at": self.activated_at.isoformat()
            if self.activated_at
            else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revocation_reason": self.revocation_reason,
            "public_key_hash": self.public_key_hash,
            "algorithm_params": self.algorithm_params,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyMetadata":
        """Create from dictionary."""
        return cls(
            key_id=data["key_id"],
            key_type=KeyType(data["key_type"]),
            version=data["version"],
            status=KeyStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            activated_at=datetime.fromisoformat(data["activated_at"])
            if data.get("activated_at")
            else None,
            expires_at=datetime.fromisoformat(data["expires_at"])
            if data.get("expires_at")
            else None,
            revoked_at=datetime.fromisoformat(data["revoked_at"])
            if data.get("revoked_at")
            else None,
            revocation_reason=data.get("revocation_reason"),
            public_key_hash=data.get("public_key_hash", ""),
            algorithm_params=data.get("algorithm_params", {}),
        )

    def is_valid_for_signing(self) -> bool:
        """Check if key can be used for signing."""
        if self.status != KeyStatus.ACTIVE:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def is_valid_for_verification(self) -> bool:
        """Check if key can be used for verification."""
        # Revoked keys should never be trusted
        if self.status == KeyStatus.REVOKED:
            return False
        # Active and archived keys can verify
        return self.status in (KeyStatus.ACTIVE, KeyStatus.ARCHIVED)


@dataclass
class RotationPolicy:
    """Policy for automatic key rotation."""

    rotation_interval_days: int = 90  # Rotate keys every 90 days
    overlap_period_days: int = 7  # Keep old key valid for 7 days after rotation
    max_archived_keys: int = 10  # Keep up to 10 old keys for verification
    auto_rotate: bool = True  # Enable automatic rotation
    notify_days_before: int = 14  # Notify 14 days before rotation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rotation_interval_days": self.rotation_interval_days,
            "overlap_period_days": self.overlap_period_days,
            "max_archived_keys": self.max_archived_keys,
            "auto_rotate": self.auto_rotate,
            "notify_days_before": self.notify_days_before,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RotationPolicy":
        return cls(**data)


class KeyRotationManager:
    """
    Manages cryptographic key lifecycle including rotation, archival, and revocation.

    Key Lifecycle:
    1. PENDING -> Generated but not yet active
    2. ACTIVE -> Currently used for signing and verification
    3. ARCHIVED -> No longer signs, but still verifies (grace period)
    4. EXPIRED -> Past validity, kept for audit
    5. REVOKED -> Compromised, do not trust

    Directory Structure:
    key_dir/
    ├── active/           # Current active keys
    ├── archived/         # Old keys for verification
    ├── revoked/          # Revoked keys (kept for audit)
    ├── pending/          # Keys waiting to become active
    └── metadata.json     # Key metadata and rotation state
    """

    def __init__(
        self,
        key_dir: str = ".uatp_keys",
        policy: Optional[RotationPolicy] = None,
        signer_id: str = "local_engine",
    ):
        """
        Initialize key rotation manager.

        Args:
            key_dir: Base directory for key storage
            policy: Rotation policy (uses defaults if None)
            signer_id: Identifier for the signing entity
        """
        self.key_dir = Path(key_dir)
        self.policy = policy or RotationPolicy()
        self.signer_id = signer_id

        # Ensure directory structure
        self._ensure_directories()

        # Load or initialize metadata
        self.metadata_file = self.key_dir / "rotation_metadata.json"
        self.keys: Dict[str, KeyMetadata] = {}
        self._load_metadata()

        logger.info(f"Key rotation manager initialized: {self.key_dir}")

    def _ensure_directories(self) -> None:
        """Create required directory structure."""
        for subdir in ["active", "archived", "revoked", "pending"]:
            (self.key_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _load_metadata(self) -> None:
        """Load key metadata from disk."""
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                data = json.load(f)
                self.keys = {
                    k: KeyMetadata.from_dict(v) for k, v in data.get("keys", {}).items()
                }
                if "policy" in data:
                    self.policy = RotationPolicy.from_dict(data["policy"])
        else:
            self.keys = {}

    def _save_metadata(self) -> None:
        """Save key metadata to disk."""
        data = {
            "keys": {k: v.to_dict() for k, v in self.keys.items()},
            "policy": self.policy.to_dict(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.metadata_file, "w") as f:
            json.dump(data, f, indent=2)

    def generate_key_id(self, key_type: KeyType) -> str:
        """Generate a unique key ID."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        random_suffix = os.urandom(4).hex()
        return f"{self.signer_id}_{key_type.value}_{timestamp}_{random_suffix}"

    def create_key(
        self,
        key_type: KeyType,
        activate_immediately: bool = False,
        validity_days: Optional[int] = None,
    ) -> KeyMetadata:
        """
        Create a new cryptographic key.

        Args:
            key_type: Type of key to create
            activate_immediately: If True, make key active immediately
            validity_days: Days until expiration (None = use policy default)

        Returns:
            KeyMetadata for the new key
        """
        key_id = self.generate_key_id(key_type)
        now = datetime.now(timezone.utc)

        # Calculate expiration
        if validity_days is None:
            validity_days = self.policy.rotation_interval_days
        expires_at = now + timedelta(days=validity_days)

        # Determine version (increment from highest existing)
        existing_versions = [
            k.version for k in self.keys.values() if k.key_type == key_type
        ]
        version = max(existing_versions, default=0) + 1

        # Create metadata
        metadata = KeyMetadata(
            key_id=key_id,
            key_type=key_type,
            version=version,
            status=KeyStatus.ACTIVE if activate_immediately else KeyStatus.PENDING,
            created_at=now,
            activated_at=now if activate_immediately else None,
            expires_at=expires_at,
        )

        # Generate actual keys based on type
        if key_type == KeyType.ED25519:
            public_key_hash = self._generate_ed25519_key(key_id, activate_immediately)
        elif key_type == KeyType.ML_DSA_65:
            public_key_hash = self._generate_ml_dsa_65_key(key_id, activate_immediately)
        elif key_type == KeyType.HYBRID:
            public_key_hash = self._generate_hybrid_keys(key_id, activate_immediately)
        else:
            raise ValueError(f"Unsupported key type: {key_type}")

        metadata.public_key_hash = public_key_hash

        # Store metadata
        self.keys[key_id] = metadata
        self._save_metadata()

        logger.info(f"Created key {key_id} (type={key_type.value}, version={version})")
        return metadata

    def _generate_ed25519_key(self, key_id: str, active: bool) -> str:
        """Generate Ed25519 keypair."""
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519

        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Determine storage directory
        subdir = "active" if active else "pending"
        key_path = self.key_dir / subdir / f"{key_id}_private.pem"
        pub_path = self.key_dir / subdir / f"{key_id}_public.pem"

        # Get password for encryption
        password = self._get_key_password()

        # Save private key (encrypted)
        with open(key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.BestAvailableEncryption(
                        password
                    ),
                )
            )
        os.chmod(key_path, 0o600)

        # Save public key
        with open(pub_path, "wb") as f:
            f.write(
                public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )

        # Return hash of public key for identification
        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return hashlib.sha256(pub_bytes).hexdigest()[:16]

    def _generate_ml_dsa_65_key(self, key_id: str, active: bool) -> str:
        """Generate ML-DSA-65 keypair."""
        try:
            import oqs
        except ImportError as e:
            raise RuntimeError("liboqs-python required for ML-DSA-65 keys") from e

        with oqs.Signature("ML-DSA-65") as sig:
            public_key = sig.generate_keypair()
            private_key = sig.export_secret_key()

        # Determine storage directory
        subdir = "active" if active else "pending"
        key_path = self.key_dir / subdir / f"{key_id}_private.bin"
        pub_path = self.key_dir / subdir / f"{key_id}_public.bin"

        # Encrypt and save private key
        encrypted = self._encrypt_key(private_key)
        with open(key_path, "wb") as f:
            f.write(encrypted)
        os.chmod(key_path, 0o600)

        # Save public key
        with open(pub_path, "wb") as f:
            f.write(public_key)

        return hashlib.sha256(public_key).hexdigest()[:16]

    def _generate_hybrid_keys(self, key_id: str, active: bool) -> str:
        """Generate both Ed25519 and ML-DSA-65 keys."""
        ed_hash = self._generate_ed25519_key(f"{key_id}_ed25519", active)
        pq_hash = self._generate_ml_dsa_65_key(f"{key_id}_ml_dsa_65", active)
        return f"{ed_hash}:{pq_hash}"

    def _get_key_password(self) -> bytes:
        """Get password for key encryption."""
        password = os.environ.get("UATP_KEY_PASSWORD")
        if password:
            return password.encode("utf-8")

        # Derive from machine-specific data (development only)
        factors = [
            os.environ.get("USER", ""),
            os.environ.get("HOME", ""),
            "uatp-key-rotation-v1",
        ]
        return hashlib.pbkdf2_hmac(
            "sha256",
            ":".join(factors).encode("utf-8"),
            b"key-rotation-salt",
            480_000,
        )

    def _encrypt_key(self, key_data: bytes) -> bytes:
        """Encrypt key data using AES-256-GCM."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        password = self._get_key_password()
        aes_key = hashlib.pbkdf2_hmac("sha256", password, b"rotation-aes-key", 480_000)
        nonce = os.urandom(12)
        aesgcm = AESGCM(aes_key)
        ciphertext: bytes = aesgcm.encrypt(nonce, key_data, None)
        return nonce + ciphertext

    def _decrypt_key(self, encrypted_data: bytes) -> bytes:
        """Decrypt key data."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        password = self._get_key_password()
        aes_key = hashlib.pbkdf2_hmac("sha256", password, b"rotation-aes-key", 480_000)
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        aesgcm = AESGCM(aes_key)
        plaintext: bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext

    def activate_key(self, key_id: str) -> bool:
        """
        Activate a pending key.

        Args:
            key_id: ID of key to activate

        Returns:
            True if activation successful
        """
        if key_id not in self.keys:
            logger.error(f"Key not found: {key_id}")
            return False

        metadata = self.keys[key_id]
        if metadata.status != KeyStatus.PENDING:
            logger.error(
                f"Key {key_id} is not pending (status={metadata.status.value})"
            )
            return False

        # Move key files from pending to active
        self._move_key_files(key_id, "pending", "active")

        # Update metadata
        metadata.status = KeyStatus.ACTIVE
        metadata.activated_at = datetime.now(timezone.utc)
        self._save_metadata()

        logger.info(f"Activated key: {key_id}")
        return True

    def archive_key(self, key_id: str) -> bool:
        """
        Archive an active key (no longer signs, still verifies).

        Args:
            key_id: ID of key to archive

        Returns:
            True if archival successful
        """
        if key_id not in self.keys:
            logger.error(f"Key not found: {key_id}")
            return False

        metadata = self.keys[key_id]
        if metadata.status != KeyStatus.ACTIVE:
            logger.error(f"Key {key_id} is not active")
            return False

        # Move key files
        self._move_key_files(key_id, "active", "archived")

        # Update metadata
        metadata.status = KeyStatus.ARCHIVED
        self._save_metadata()

        # Clean up old archived keys if needed
        self._cleanup_old_keys()

        logger.info(f"Archived key: {key_id}")
        return True

    def revoke_key(self, key_id: str, reason: str) -> bool:
        """
        Revoke a compromised key.

        Args:
            key_id: ID of key to revoke
            reason: Reason for revocation

        Returns:
            True if revocation successful
        """
        if key_id not in self.keys:
            logger.error(f"Key not found: {key_id}")
            return False

        metadata = self.keys[key_id]
        old_status = metadata.status

        # Determine source directory
        source_dir = {
            KeyStatus.ACTIVE: "active",
            KeyStatus.PENDING: "pending",
            KeyStatus.ARCHIVED: "archived",
        }.get(old_status)

        if source_dir:
            self._move_key_files(key_id, source_dir, "revoked")

        # Update metadata
        metadata.status = KeyStatus.REVOKED
        metadata.revoked_at = datetime.now(timezone.utc)
        metadata.revocation_reason = reason
        self._save_metadata()

        logger.warning(f"REVOKED key {key_id}: {reason}")
        return True

    def _move_key_files(self, key_id: str, from_dir: str, to_dir: str) -> None:
        """Move key files between directories."""
        from_path = self.key_dir / from_dir
        to_path = self.key_dir / to_dir

        for suffix in ["_private.pem", "_public.pem", "_private.bin", "_public.bin"]:
            src = from_path / f"{key_id}{suffix}"
            dst = to_path / f"{key_id}{suffix}"
            if src.exists():
                shutil.move(str(src), str(dst))

    def _cleanup_old_keys(self) -> None:
        """Remove old archived keys beyond retention limit."""
        archived_keys = [
            k for k in self.keys.values() if k.status == KeyStatus.ARCHIVED
        ]
        archived_keys.sort(key=lambda k: k.created_at, reverse=True)

        # Keep only max_archived_keys
        for old_key in archived_keys[self.policy.max_archived_keys :]:
            old_key.status = KeyStatus.EXPIRED
            logger.info(f"Expired old archived key: {old_key.key_id}")

        self._save_metadata()

    def rotate_keys(self, key_type: Optional[KeyType] = None) -> List[KeyMetadata]:
        """
        Perform key rotation.

        1. Creates new key(s)
        2. Activates new key(s)
        3. Archives old active key(s)

        Args:
            key_type: Specific key type to rotate (None = all types)

        Returns:
            List of newly created keys
        """
        types_to_rotate = [key_type] if key_type else list(KeyType)
        new_keys = []

        for kt in types_to_rotate:
            # Find current active key
            active_keys = [
                k
                for k in self.keys.values()
                if k.key_type == kt and k.status == KeyStatus.ACTIVE
            ]

            # Create new key
            new_key = self.create_key(kt, activate_immediately=True)
            new_keys.append(new_key)

            # Archive old active keys
            for old_key in active_keys:
                self.archive_key(old_key.key_id)

        logger.info(f"Rotated {len(new_keys)} key(s)")
        return new_keys

    def check_rotation_needed(self) -> List[KeyMetadata]:
        """
        Check if any keys need rotation.

        Returns:
            List of keys that need rotation
        """
        needs_rotation = []
        now = datetime.now(timezone.utc)
        rotation_threshold = timedelta(days=self.policy.rotation_interval_days)

        for key in self.keys.values():
            if key.status != KeyStatus.ACTIVE:
                continue

            # Check age
            if key.activated_at:
                age = now - key.activated_at
                if age >= rotation_threshold:
                    needs_rotation.append(key)
                    continue

            # Check expiration
            if key.expires_at and now >= key.expires_at - timedelta(
                days=self.policy.notify_days_before
            ):
                needs_rotation.append(key)

        return needs_rotation

    def get_active_key(self, key_type: KeyType) -> Optional[KeyMetadata]:
        """Get the current active key of specified type."""
        for key in self.keys.values():
            if key.key_type == key_type and key.status == KeyStatus.ACTIVE:
                return key
        return None

    def get_key_for_verification(self, key_id: str) -> Optional[KeyMetadata]:
        """Get a key for verification (must not be revoked)."""
        key = self.keys.get(key_id)
        if key and key.is_valid_for_verification():
            return key
        return None

    def list_keys(
        self,
        key_type: Optional[KeyType] = None,
        status: Optional[KeyStatus] = None,
    ) -> List[KeyMetadata]:
        """List keys with optional filtering."""
        keys = list(self.keys.values())

        if key_type:
            keys = [k for k in keys if k.key_type == key_type]
        if status:
            keys = [k for k in keys if k.status == status]

        return sorted(keys, key=lambda k: k.created_at, reverse=True)

    def get_rotation_status(self) -> Dict[str, Any]:
        """Get overall rotation status."""
        needs_rotation = self.check_rotation_needed()

        return {
            "total_keys": len(self.keys),
            "active_keys": len(
                [k for k in self.keys.values() if k.status == KeyStatus.ACTIVE]
            ),
            "archived_keys": len(
                [k for k in self.keys.values() if k.status == KeyStatus.ARCHIVED]
            ),
            "revoked_keys": len(
                [k for k in self.keys.values() if k.status == KeyStatus.REVOKED]
            ),
            "needs_rotation": [k.key_id for k in needs_rotation],
            "policy": self.policy.to_dict(),
        }


# Convenience functions
def rotate_all_keys(key_dir: str = ".uatp_keys") -> List[KeyMetadata]:
    """Rotate all cryptographic keys."""
    manager = KeyRotationManager(key_dir=key_dir)
    return manager.rotate_keys()


def check_key_health(key_dir: str = ".uatp_keys") -> Dict[str, Any]:
    """Check health of cryptographic keys."""
    manager = KeyRotationManager(key_dir=key_dir)
    return manager.get_rotation_status()
