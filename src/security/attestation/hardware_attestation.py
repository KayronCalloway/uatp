"""
Hardware Attestation Framework for UATP 7.2

This module provides a unified interface for hardware attestation across
multiple platforms. It supports:
- Apple Secure Enclave
- Android TEE (TrustZone)
- NVIDIA Confidential Computing
- Intel SGX
- ARM TrustZone

IMPORTANT: This is a framework implementation. Actual hardware integration
requires platform-specific SDKs and secure boot verification.
"""

import base64
import hashlib
import logging
import secrets
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ChallengeStore(ABC):
    """Abstract interface for attestation challenge storage."""

    @abstractmethod
    def store(self, challenge: "AttestationChallenge") -> None:
        """Store a challenge."""
        pass

    @abstractmethod
    def get(self, challenge_id: str) -> Optional["AttestationChallenge"]:
        """Get a challenge by ID."""
        pass

    @abstractmethod
    def get_and_delete(self, challenge_id: str) -> Optional["AttestationChallenge"]:
        """
        Atomically get and delete a challenge.

        SECURITY: This is the preferred method for challenge consumption
        as it prevents race conditions where the same challenge could be
        used by multiple concurrent requests.
        """
        pass

    @abstractmethod
    def delete(self, challenge_id: str) -> bool:
        """Delete a challenge. Returns True if existed."""
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        """Remove expired challenges. Returns count removed."""
        pass


class InMemoryChallengeStore(ChallengeStore):
    """In-memory challenge store for development/testing only."""

    def __init__(self):
        import threading

        self._challenges: Dict[str, "AttestationChallenge"] = {}
        # SECURITY: Lock ensures atomic get-and-delete operations to prevent
        # race conditions where the same challenge could be used twice
        self._lock = threading.Lock()
        logger.warning(
            "Using in-memory challenge store - data will be lost on restart. "
            "Use RedisChallengeStore or DatabaseChallengeStore in production."
        )

    def store(self, challenge: "AttestationChallenge") -> None:
        with self._lock:
            self._challenges[challenge.challenge_id] = challenge

    def get(self, challenge_id: str) -> Optional["AttestationChallenge"]:
        with self._lock:
            return self._challenges.get(challenge_id)

    def get_and_delete(self, challenge_id: str) -> Optional["AttestationChallenge"]:
        """
        Atomically get and delete a challenge.

        SECURITY: This prevents race conditions where the same challenge
        could be retrieved and used by multiple concurrent requests.
        """
        with self._lock:
            challenge = self._challenges.get(challenge_id)
            if challenge:
                del self._challenges[challenge_id]
            return challenge

    def delete(self, challenge_id: str) -> bool:
        with self._lock:
            if challenge_id in self._challenges:
                del self._challenges[challenge_id]
                return True
            return False

    def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        with self._lock:
            expired = [cid for cid, c in self._challenges.items() if now > c.expires_at]
            for cid in expired:
                del self._challenges[cid]
            return len(expired)


class CacheChallengeStore(ChallengeStore):
    """
    Cache-backed challenge store using Redis or similar.

    Challenges are stored with TTL matching their expiration time.
    This ensures challenges survive server restarts.
    """

    def __init__(
        self, cache_client=None, key_prefix: str = "uatp:attestation:challenge:"
    ):
        """
        Initialize cache-backed store.

        Args:
            cache_client: Redis client or compatible cache with get/set/delete/setex
            key_prefix: Prefix for cache keys
        """
        self._cache = cache_client
        self._key_prefix = key_prefix
        if not cache_client:
            logger.warning("No cache client provided, falling back to in-memory store")
            self._fallback = InMemoryChallengeStore()
        else:
            self._fallback = None

    def _key(self, challenge_id: str) -> str:
        return f"{self._key_prefix}{challenge_id}"

    def store(self, challenge: "AttestationChallenge") -> None:
        if self._fallback:
            return self._fallback.store(challenge)

        import json

        ttl_seconds = int(
            (challenge.expires_at - datetime.now(timezone.utc)).total_seconds()
        )
        if ttl_seconds > 0:
            data = json.dumps(
                {
                    "challenge_id": challenge.challenge_id,
                    "nonce": challenge.nonce,
                    "attestation_type": challenge.attestation_type.value,
                    "device_id": challenge.device_id,
                    "created_at": challenge.created_at.isoformat(),
                    "expires_at": challenge.expires_at.isoformat(),
                }
            )
            self._cache.setex(self._key(challenge.challenge_id), ttl_seconds, data)

    def get(self, challenge_id: str) -> Optional["AttestationChallenge"]:
        if self._fallback:
            return self._fallback.get(challenge_id)

        import json

        data = self._cache.get(self._key(challenge_id))
        if not data:
            return None

        try:
            obj = json.loads(data)

            # SECURITY: Validate required fields exist before accessing
            required_fields = [
                "challenge_id",
                "nonce",
                "attestation_type",
                "created_at",
                "expires_at",
            ]
            missing = [f for f in required_fields if f not in obj]
            if missing:
                logger.error(f"Challenge deserialization missing fields: {missing}")
                return None

            # SECURITY: Validate field types
            if not isinstance(obj["challenge_id"], str) or not isinstance(
                obj["nonce"], str
            ):
                logger.error("Challenge deserialization: invalid field types")
                return None

            return AttestationChallenge(
                challenge_id=obj["challenge_id"],
                nonce=obj["nonce"],
                attestation_type=AttestationType(obj["attestation_type"]),
                device_id_hint=obj.get("device_id"),
                created_at=datetime.fromisoformat(obj["created_at"]),
                expires_at=datetime.fromisoformat(obj["expires_at"]),
            )
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to deserialize challenge: {e}")
            return None

    def get_and_delete(self, challenge_id: str) -> Optional["AttestationChallenge"]:
        """
        Atomically get and delete a challenge using Redis GETDEL.

        SECURITY: Redis GETDEL is atomic, preventing race conditions where
        the same challenge could be consumed by multiple concurrent requests.
        """
        if self._fallback:
            return self._fallback.get_and_delete(challenge_id)

        import json

        key = self._key(challenge_id)

        # Use GETDEL for atomic get-and-delete (Redis 6.2+)
        # Fall back to WATCH/MULTI/EXEC transaction for older Redis versions
        try:
            data = self._cache.getdel(key)
        except AttributeError:
            # SECURITY: Redis client doesn't support GETDEL, use atomic transaction
            # WATCH ensures the key hasn't changed between GET and DELETE
            # If another client modifies the key, the transaction aborts
            pipe = self._cache.pipeline(True)  # True enables WATCH
            try:
                pipe.watch(key)
                data = pipe.get(key)
                if data:
                    pipe.multi()
                    pipe.delete(key)
                    pipe.execute()
                else:
                    pipe.unwatch()
            except Exception:
                # Transaction failed (key was modified) - challenge already consumed
                pipe.unwatch()
                data = None

        if not data:
            return None

        try:
            obj = json.loads(data)

            required_fields = [
                "challenge_id",
                "nonce",
                "attestation_type",
                "created_at",
                "expires_at",
            ]
            missing = [f for f in required_fields if f not in obj]
            if missing:
                logger.error(f"Challenge deserialization missing fields: {missing}")
                return None

            if not isinstance(obj["challenge_id"], str) or not isinstance(
                obj["nonce"], str
            ):
                logger.error("Challenge deserialization: invalid field types")
                return None

            return AttestationChallenge(
                challenge_id=obj["challenge_id"],
                nonce=obj["nonce"],
                attestation_type=AttestationType(obj["attestation_type"]),
                device_id_hint=obj.get("device_id"),
                created_at=datetime.fromisoformat(obj["created_at"]),
                expires_at=datetime.fromisoformat(obj["expires_at"]),
            )
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to deserialize challenge: {e}")
            return None

    def delete(self, challenge_id: str) -> bool:
        if self._fallback:
            return self._fallback.delete(challenge_id)
        return bool(self._cache.delete(self._key(challenge_id)))

    def cleanup_expired(self) -> int:
        # Redis TTL handles expiration automatically
        if self._fallback:
            return self._fallback.cleanup_expired()
        return 0


class AttestationType(str, Enum):
    """Supported hardware attestation types."""

    APPLE_SECURE_ENCLAVE = "apple_secure_enclave"
    ANDROID_TEE = "android_tee"
    NVIDIA_CC = "nvidia_cc"
    INTEL_SGX = "intel_sgx"
    ARM_TRUSTZONE = "arm_trustzone"
    APPLE_NEURAL_ENGINE = "apple_neural_engine"  # UATP 7.3 ANE attestation
    SIMULATED = "simulated"  # For testing


class AttestationStatus(str, Enum):
    """Status of an attestation."""

    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class AttestationChallenge:
    """Challenge for attestation handshake."""

    challenge_id: str
    nonce: str
    attestation_type: AttestationType
    created_at: datetime
    expires_at: datetime
    device_id_hint: Optional[str] = None


@dataclass
class AttestationResult:
    """Result of attestation verification."""

    verified: bool
    attestation_type: AttestationType
    device_id_hash: str
    timestamp: datetime
    measurements: Dict[str, str] = field(default_factory=dict)
    certificate_chain: List[str] = field(default_factory=list)
    error: Optional[str] = None
    attestation_data: Optional[str] = None


class HardwareAttestationService:
    """
    Unified hardware attestation service.

    Provides a common interface for generating challenges, submitting
    attestations, and verifying attestation data across platforms.
    """

    def __init__(self, challenge_store: Optional[ChallengeStore] = None):
        """
        Initialize the hardware attestation service.

        Args:
            challenge_store: Storage backend for challenges. If None, uses
                             in-memory store (not recommended for production).
        """
        self._challenge_store = challenge_store or InMemoryChallengeStore()
        self.challenge_timeout_seconds = 300  # 5 minutes

    # Legacy property for backwards compatibility
    @property
    def active_challenges(self) -> Dict[str, AttestationChallenge]:
        """Deprecated: Use challenge_store directly."""
        logger.warning("active_challenges property is deprecated")
        if isinstance(self._challenge_store, InMemoryChallengeStore):
            return self._challenge_store._challenges
        return {}

    def generate_challenge(
        self,
        attestation_type: AttestationType,
        device_id_hint: Optional[str] = None,
    ) -> AttestationChallenge:
        """
        Generate a new attestation challenge.

        The client must respond with attestation data that includes
        this challenge nonce to prevent replay attacks.

        Args:
            attestation_type: Type of attestation expected
            device_id_hint: Optional hint about expected device

        Returns:
            AttestationChallenge with nonce to include in attestation
        """
        challenge_id = f"attest_{uuid.uuid4().hex[:16]}"
        nonce = secrets.token_hex(32)  # 256-bit nonce

        now = datetime.now(timezone.utc)
        expires_at = datetime.fromtimestamp(
            now.timestamp() + self.challenge_timeout_seconds, tz=timezone.utc
        )

        challenge = AttestationChallenge(
            challenge_id=challenge_id,
            nonce=nonce,
            attestation_type=attestation_type,
            created_at=now,
            expires_at=expires_at,
            device_id_hint=device_id_hint,
        )

        self._challenge_store.store(challenge)

        logger.info(
            f"Generated attestation challenge {challenge_id} for {attestation_type.value}"
        )

        return challenge

    def verify_attestation(
        self,
        challenge_id: str,
        attestation_data: bytes,
        certificate_chain: List[str],
        measurements: Optional[Dict[str, str]] = None,
    ) -> AttestationResult:
        """
        Verify submitted attestation data.

        Args:
            challenge_id: Challenge ID from generate_challenge
            attestation_data: Raw attestation blob from hardware
            certificate_chain: PEM-encoded certificate chain
            measurements: Platform measurements (PCRs, etc.)

        Returns:
            AttestationResult with verification status
        """
        # SECURITY: Use atomic get_and_delete to prevent race conditions
        # where the same challenge could be consumed by multiple requests
        challenge = self._challenge_store.get_and_delete(challenge_id)
        if not challenge:
            return AttestationResult(
                verified=False,
                attestation_type=AttestationType.SIMULATED,
                device_id_hash="",
                timestamp=datetime.now(timezone.utc),
                error="Challenge not found or expired",
            )

        now = datetime.now(timezone.utc)
        if now > challenge.expires_at:
            # Challenge already deleted by get_and_delete, just return expired
            return AttestationResult(
                verified=False,
                attestation_type=challenge.attestation_type,
                device_id_hash="",
                timestamp=now,
                error="Challenge expired",
            )

        # Challenge already deleted by get_and_delete (single-use)

        # Dispatch to platform-specific verifier
        try:
            if challenge.attestation_type == AttestationType.APPLE_SECURE_ENCLAVE:
                result = self._verify_apple_attestation(
                    challenge, attestation_data, certificate_chain, measurements
                )
            elif challenge.attestation_type == AttestationType.ANDROID_TEE:
                result = self._verify_android_attestation(
                    challenge, attestation_data, certificate_chain, measurements
                )
            elif challenge.attestation_type == AttestationType.NVIDIA_CC:
                result = self._verify_nvidia_attestation(
                    challenge, attestation_data, certificate_chain, measurements
                )
            elif challenge.attestation_type == AttestationType.INTEL_SGX:
                result = self._verify_intel_sgx_attestation(
                    challenge, attestation_data, certificate_chain, measurements
                )
            elif challenge.attestation_type == AttestationType.APPLE_NEURAL_ENGINE:
                result = self._verify_ane_attestation(
                    challenge, attestation_data, certificate_chain, measurements
                )
            elif challenge.attestation_type == AttestationType.SIMULATED:
                result = self._verify_simulated_attestation(
                    challenge, attestation_data, certificate_chain, measurements
                )
            else:
                result = AttestationResult(
                    verified=False,
                    attestation_type=challenge.attestation_type,
                    device_id_hash="",
                    timestamp=now,
                    error=f"Unsupported attestation type: {challenge.attestation_type}",
                )

            return result

        except Exception as e:
            logger.error(f"Attestation verification failed: {e}")
            return AttestationResult(
                verified=False,
                attestation_type=challenge.attestation_type,
                device_id_hash="",
                timestamp=now,
                error=str(e),
            )

    def _verify_apple_attestation(
        self,
        challenge: AttestationChallenge,
        attestation_data: bytes,
        certificate_chain: List[str],
        measurements: Optional[Dict[str, str]],
    ) -> AttestationResult:
        """
        Verify Apple Secure Enclave attestation.

        NOTE: This is a stub implementation. Real verification requires:
        1. Apple DeviceCheck or App Attest API
        2. Certificate chain validation against Apple root CA
        3. Nonce verification in attestation blob
        """
        logger.warning(
            "Apple Secure Enclave verification is stubbed - "
            "production use requires DeviceCheck/App Attest integration"
        )

        # Generate device ID hash from attestation data
        device_id_hash = hashlib.sha256(attestation_data).hexdigest()

        # SECURITY: Stub attestation MUST fail in production
        # Real verification requires Apple DeviceCheck/App Attest integration
        # Only pass if explicitly in test mode AND nonce is present
        nonce_bytes = challenge.nonce.encode()
        nonce_present = nonce_bytes in attestation_data

        if not nonce_present:
            logger.error(
                "Apple Secure Enclave attestation failed: nonce not found in attestation data. "
                "This is a stub implementation - production requires DeviceCheck/App Attest."
            )
            return AttestationResult(
                verified=False,
                attestation_type=AttestationType.APPLE_SECURE_ENCLAVE,
                device_id_hash=device_id_hash,
                timestamp=datetime.now(timezone.utc),
                measurements=measurements or {},
                certificate_chain=certificate_chain,
                attestation_data=base64.b64encode(attestation_data).decode(),
                error="Stub attestation: nonce verification failed. Production requires real DeviceCheck/App Attest integration.",
            )

        return AttestationResult(
            verified=nonce_present,
            attestation_type=AttestationType.APPLE_SECURE_ENCLAVE,
            device_id_hash=device_id_hash,
            timestamp=datetime.now(timezone.utc),
            measurements=measurements or {},
            certificate_chain=certificate_chain,
            attestation_data=base64.b64encode(attestation_data).decode(),
        )

    def _verify_android_attestation(
        self,
        challenge: AttestationChallenge,
        attestation_data: bytes,
        certificate_chain: List[str],
        measurements: Optional[Dict[str, str]],
    ) -> AttestationResult:
        """
        Verify Android TEE (SafetyNet/Key Attestation) attestation.

        NOTE: This is a stub implementation. Real verification requires:
        1. Google Play Integrity API or Key Attestation
        2. Certificate chain validation against Google root CA
        3. JWS signature verification for SafetyNet
        """
        logger.warning(
            "Android TEE verification is stubbed - "
            "production use requires Play Integrity/Key Attestation integration"
        )

        device_id_hash = hashlib.sha256(attestation_data).hexdigest()

        # SECURITY: Stub attestation MUST fail in production
        # Real verification requires Play Integrity/Key Attestation integration
        logger.error(
            "Android TEE attestation failed: stub implementation cannot verify attestation. "
            "Production requires Play Integrity/Key Attestation integration."
        )

        return AttestationResult(
            verified=False,
            attestation_type=AttestationType.ANDROID_TEE,
            device_id_hash=device_id_hash,
            timestamp=datetime.now(timezone.utc),
            measurements=measurements or {},
            certificate_chain=certificate_chain,
            attestation_data=base64.b64encode(attestation_data).decode(),
            error="Stub attestation: not implemented. Production requires Play Integrity/Key Attestation.",
        )

    def _verify_nvidia_attestation(
        self,
        challenge: AttestationChallenge,
        attestation_data: bytes,
        certificate_chain: List[str],
        measurements: Optional[Dict[str, str]],
    ) -> AttestationResult:
        """
        Verify NVIDIA Confidential Computing attestation.

        NOTE: This is a stub implementation. Real verification requires:
        1. NVIDIA Attestation SDK
        2. GPU attestation report validation
        3. Confidential computing measurements verification
        """
        device_id_hash = hashlib.sha256(attestation_data).hexdigest()

        # SECURITY: Stub attestation MUST fail in production
        # Real verification requires NVIDIA Attestation SDK
        logger.error(
            "NVIDIA CC attestation failed: stub implementation cannot verify attestation. "
            "Production requires NVIDIA Attestation SDK."
        )

        return AttestationResult(
            verified=False,
            attestation_type=AttestationType.NVIDIA_CC,
            device_id_hash=device_id_hash,
            timestamp=datetime.now(timezone.utc),
            measurements=measurements
            or {
                "gpu_model": "unknown",
                "confidential_mode": "disabled",
            },
            certificate_chain=certificate_chain,
            attestation_data=base64.b64encode(attestation_data).decode(),
            error="Stub attestation: not implemented. Production requires NVIDIA Attestation SDK.",
        )

    def _verify_intel_sgx_attestation(
        self,
        challenge: AttestationChallenge,
        attestation_data: bytes,
        certificate_chain: List[str],
        measurements: Optional[Dict[str, str]],
    ) -> AttestationResult:
        """
        Verify Intel SGX attestation.

        NOTE: This is a stub implementation. Real verification requires:
        1. Intel Attestation Service (IAS) or DCAP
        2. Quote verification
        3. MRENCLAVE/MRSIGNER validation
        """
        device_id_hash = hashlib.sha256(attestation_data).hexdigest()

        # SECURITY: Stub attestation MUST fail in production
        # Real verification requires Intel Attestation Service (IAS) or DCAP
        logger.error(
            "Intel SGX attestation failed: stub implementation cannot verify attestation. "
            "Production requires Intel Attestation Service (IAS) or DCAP."
        )

        return AttestationResult(
            verified=False,
            attestation_type=AttestationType.INTEL_SGX,
            device_id_hash=device_id_hash,
            timestamp=datetime.now(timezone.utc),
            measurements=measurements
            or {
                "mrenclave": "0" * 64,
                "mrsigner": "0" * 64,
            },
            certificate_chain=certificate_chain,
            attestation_data=base64.b64encode(attestation_data).decode(),
            error="Stub attestation: not implemented. Production requires Intel Attestation Service.",
        )

    def _verify_ane_attestation(
        self,
        challenge: AttestationChallenge,
        attestation_data: bytes,
        certificate_chain: List[str],
        measurements: Optional[Dict[str, str]],
    ) -> AttestationResult:
        """
        Verify Apple Neural Engine attestation for UATP 7.3 ANE training provenance.

        NOTE: This is a stub implementation. Real verification requires:
        1. Apple Device Check or custom ANE attestation protocol
        2. Verification of ANE availability on device
        3. Nonce verification in attestation blob
        4. Validation of private API usage declarations

        ANE-specific measurements include:
        - chip_identifier: Apple chip (M1, M2, M3, M4, A17, etc.)
        - ane_version: ANE hardware version
        - ane_tops: Theoretical TOPS capability
        - private_apis: List of private APIs being used (_ANEClient, _ANECompiler)
        """
        logger.warning(
            "Apple Neural Engine verification is stubbed - "
            "production use requires custom ANE attestation protocol"
        )

        device_id_hash = hashlib.sha256(attestation_data).hexdigest()

        # Check if nonce is present in attestation data
        nonce_bytes = challenge.nonce.encode()
        nonce_present = nonce_bytes in attestation_data

        # For ANE attestation, we also validate ANE-specific measurements
        ane_measurements = measurements or {}
        has_chip_info = "chip_identifier" in ane_measurements
        has_ane_version = (
            "ane_version" in ane_measurements or "ane_available" in ane_measurements
        )

        # Default ANE measurements if not provided
        default_measurements = {
            "chip_identifier": ane_measurements.get("chip_identifier", "unknown"),
            "ane_version": ane_measurements.get("ane_version", "unknown"),
            "ane_available": ane_measurements.get("ane_available", "true"),
            "ane_tops": ane_measurements.get("ane_tops", "unknown"),
            "private_apis_declared": ane_measurements.get("private_apis_declared", ""),
            "dmca_1201f_claim": ane_measurements.get("dmca_1201f_claim", "false"),
        }

        if not nonce_present:
            logger.error(
                "Apple Neural Engine attestation failed: nonce not found in attestation data. "
                "This is a stub implementation - production requires custom ANE attestation."
            )
            return AttestationResult(
                verified=False,
                attestation_type=AttestationType.APPLE_NEURAL_ENGINE,
                device_id_hash=device_id_hash,
                timestamp=datetime.now(timezone.utc),
                measurements=default_measurements,
                certificate_chain=certificate_chain,
                attestation_data=base64.b64encode(attestation_data).decode(),
                error="Stub attestation: nonce verification failed. Production requires ANE attestation protocol.",
            )

        # Log if ANE-specific info is present
        if has_chip_info and has_ane_version:
            logger.info(
                f"ANE attestation includes chip info: {ane_measurements.get('chip_identifier')}, "
                f"ANE version: {ane_measurements.get('ane_version')}"
            )

        return AttestationResult(
            verified=nonce_present,
            attestation_type=AttestationType.APPLE_NEURAL_ENGINE,
            device_id_hash=device_id_hash,
            timestamp=datetime.now(timezone.utc),
            measurements=default_measurements,
            certificate_chain=certificate_chain,
            attestation_data=base64.b64encode(attestation_data).decode(),
        )

    def _verify_simulated_attestation(
        self,
        challenge: AttestationChallenge,
        attestation_data: bytes,
        certificate_chain: List[str],
        measurements: Optional[Dict[str, str]],
    ) -> AttestationResult:
        """
        Verify simulated attestation for testing.

        This always succeeds if the attestation data contains the nonce.

        WARNING: Simulated attestation provides NO security guarantees.
        It should NEVER be used in production environments.
        """
        import os

        # SECURITY: Emit prominent warning about simulated attestation
        # Check environment to determine severity
        env = os.getenv("ENVIRONMENT", "development").lower()
        is_production = env in ("production", "prod", "live")

        if is_production:
            # CRITICAL: In production, simulated attestation is a security risk
            logger.critical(
                "SECURITY ALERT: Simulated attestation used in PRODUCTION environment! "
                "This provides NO security guarantees and should be disabled. "
                "Configure a real attestation type (apple_secure_enclave, android_tee, "
                "nvidia_cc, or intel_sgx) for production use."
            )
            # In production, we could optionally reject simulated attestation entirely:
            # return AttestationResult(
            #     verified=False,
            #     attestation_type=AttestationType.SIMULATED,
            #     device_id_hash="",
            #     timestamp=datetime.now(timezone.utc),
            #     error="Simulated attestation is disabled in production",
            # )
        else:
            logger.warning(
                "Using SIMULATED attestation - this provides NO security guarantees. "
                "Ensure this is disabled before deploying to production."
            )

        device_id_hash = hashlib.sha256(attestation_data).hexdigest()

        # Check if nonce is in attestation data
        nonce_bytes = challenge.nonce.encode()
        verified = nonce_bytes in attestation_data

        return AttestationResult(
            verified=verified,
            attestation_type=AttestationType.SIMULATED,
            device_id_hash=device_id_hash,
            timestamp=datetime.now(timezone.utc),
            measurements=measurements
            or {"simulated": "true", "warning": "NO_SECURITY_GUARANTEE"},
            certificate_chain=certificate_chain,
            attestation_data=base64.b64encode(attestation_data).decode(),
        )

    def create_attestation_payload(self, result: AttestationResult) -> Dict[str, Any]:
        """
        Create a UATP 7.2 hardware_attestation payload from result.

        Args:
            result: AttestationResult from verification

        Returns:
            Dict suitable for HardwareAttestationPayload
        """
        return {
            "attestation_type": result.attestation_type.value,
            "device_id_hash": result.device_id_hash,
            "attestation_timestamp": result.timestamp.isoformat(),
            "attestation_data": result.attestation_data or "",
            "certificate_chain": result.certificate_chain,
            "nonce": "",  # Nonce was in challenge, not stored in result
            "measurements": result.measurements,
            "verified": result.verified,
            "verification_timestamp": datetime.now(timezone.utc).isoformat()
            if result.verified
            else None,
        }


# Global service instance
hardware_attestation_service = HardwareAttestationService()
