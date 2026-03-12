"""
UATP Bundle - Self-contained verification package.

A Bundle combines:
- DSSE envelope (signed payload)
- Verification material (public key, timestamp token)

This allows offline verification without needing access to UATP services.
"""

import base64
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from src.export.dsse import DSSEEnvelope, DSSESignature

BUNDLE_MEDIA_TYPE = "application/vnd.uatp.bundle.v1+json"


@dataclass
class TimestampEvidence:
    """RFC 3161 timestamp evidence."""

    rfc3161_token: Optional[str] = None  # Base64-encoded token
    authority: Optional[str] = None  # TSA URL
    timestamp: Optional[datetime] = None  # Parsed timestamp

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimestampEvidence":
        ts = None
        if data.get("timestamp"):
            ts = datetime.fromisoformat(data["timestamp"])
        return cls(
            rfc3161_token=data.get("rfc3161Token"),
            authority=data.get("authority"),
            timestamp=ts,
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.rfc3161_token:
            result["rfc3161Token"] = self.rfc3161_token
        if self.authority:
            result["authority"] = self.authority
        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()
        return result

    @property
    def has_token(self) -> bool:
        return self.rfc3161_token is not None


@dataclass
class VerificationMaterial:
    """
    Material needed to verify a bundle offline.

    Includes:
    - Public key(s) for signature verification
    - Timestamp evidence
    - Optional certificate chain
    """

    # Public key (Ed25519)
    public_key: Optional[str] = None  # Base64-encoded
    key_algorithm: str = "ed25519"

    # Post-quantum key (ML-DSA-65)
    pq_public_key: Optional[str] = None
    pq_algorithm: Optional[str] = None

    # Timestamp
    timestamp: Optional[TimestampEvidence] = None

    # Key ID used for signing
    key_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationMaterial":
        ts = None
        if data.get("timestamp"):
            ts = TimestampEvidence.from_dict(data["timestamp"])

        return cls(
            public_key=data.get("publicKey"),
            key_algorithm=data.get("keyAlgorithm", "ed25519"),
            pq_public_key=data.get("pqPublicKey"),
            pq_algorithm=data.get("pqAlgorithm"),
            timestamp=ts,
            key_id=data.get("keyId"),
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "keyAlgorithm": self.key_algorithm,
        }
        if self.public_key:
            result["publicKey"] = self.public_key
        if self.pq_public_key:
            result["pqPublicKey"] = self.pq_public_key
        if self.pq_algorithm:
            result["pqAlgorithm"] = self.pq_algorithm
        if self.timestamp:
            result["timestamp"] = self.timestamp.to_dict()
        if self.key_id:
            result["keyId"] = self.key_id
        return result

    def public_key_bytes(self) -> Optional[bytes]:
        """Decode public key from base64."""
        if self.public_key:
            return base64.b64decode(self.public_key)
        return None

    @property
    def is_hybrid(self) -> bool:
        """Check if bundle uses hybrid (classical + PQ) signatures."""
        return self.pq_public_key is not None


@dataclass
class VerificationResult:
    """Result of verifying a bundle."""

    is_valid: bool
    signature_valid: Optional[bool] = None
    timestamp_valid: Optional[bool] = None
    pq_signature_valid: Optional[bool] = None  # For hybrid
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "isValid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "verifiedAt": self.verified_at.isoformat(),
        }
        if self.signature_valid is not None:
            result["signatureValid"] = self.signature_valid
        if self.timestamp_valid is not None:
            result["timestampValid"] = self.timestamp_valid
        if self.pq_signature_valid is not None:
            result["pqSignatureValid"] = self.pq_signature_valid
        return result


@dataclass
class UATPBundle:
    """
    Self-contained verification bundle.

    Contains everything needed to verify a capsule offline:
    - DSSE envelope with signed payload
    - Verification material (keys, timestamps)

    Structure:
    {
        "mediaType": "application/vnd.uatp.bundle.v1+json",
        "dsse": { envelope },
        "verification": { material }
    }
    """

    media_type: str = BUNDLE_MEDIA_TYPE
    dsse: Optional[DSSEEnvelope] = None
    verification: Optional[VerificationMaterial] = None

    # Optional metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    capsule_id: Optional[str] = None

    @classmethod
    def create(
        cls,
        envelope: DSSEEnvelope,
        public_key: bytes,
        key_id: str,
        timestamp_token: Optional[str] = None,
        timestamp_authority: Optional[str] = None,
        pq_public_key: Optional[bytes] = None,
        pq_algorithm: Optional[str] = None,
    ) -> "UATPBundle":
        """
        Create a bundle from components.

        Args:
            envelope: Signed DSSE envelope
            public_key: Ed25519 public key bytes
            key_id: Key identifier
            timestamp_token: Base64 RFC 3161 token
            timestamp_authority: TSA URL
            pq_public_key: Post-quantum public key bytes (optional)
            pq_algorithm: Post-quantum algorithm name (optional)

        Returns:
            Complete UATPBundle
        """
        ts = None
        if timestamp_token:
            ts = TimestampEvidence(
                rfc3161_token=timestamp_token,
                authority=timestamp_authority,
            )

        verification = VerificationMaterial(
            public_key=base64.b64encode(public_key).decode("ascii"),
            key_id=key_id,
            timestamp=ts,
        )

        if pq_public_key:
            verification.pq_public_key = base64.b64encode(pq_public_key).decode("ascii")
            verification.pq_algorithm = pq_algorithm

        return cls(
            dsse=envelope,
            verification=verification,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UATPBundle":
        """Deserialize from dictionary."""
        dsse = None
        if data.get("dsse"):
            dsse = DSSEEnvelope.from_dict(data["dsse"])

        verification = None
        if data.get("verification"):
            verification = VerificationMaterial.from_dict(data["verification"])

        bundle = cls(
            media_type=data.get("mediaType", BUNDLE_MEDIA_TYPE),
            dsse=dsse,
            verification=verification,
            capsule_id=data.get("capsuleId"),
        )

        if data.get("createdAt"):
            bundle.created_at = datetime.fromisoformat(data["createdAt"])

        return bundle

    @classmethod
    def from_json(cls, json_str: str) -> "UATPBundle":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = {
            "mediaType": self.media_type,
            "createdAt": self.created_at.isoformat(),
        }

        if self.dsse:
            result["dsse"] = self.dsse.to_dict()
        if self.verification:
            result["verification"] = self.verification.to_dict()
        if self.capsule_id:
            result["capsuleId"] = self.capsule_id

        return result

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def verify(
        self,
        verify_func: Optional[Callable[[bytes, bytes], bool]] = None,
    ) -> VerificationResult:
        """
        Verify the bundle.

        Args:
            verify_func: Optional custom verification function.
                         If None, uses Ed25519 verification.

        Returns:
            VerificationResult with details
        """
        result = VerificationResult(is_valid=True)

        if not self.dsse:
            result.is_valid = False
            result.errors.append("Bundle has no DSSE envelope")
            return result

        if not self.dsse.is_signed:
            result.is_valid = False
            result.errors.append("DSSE envelope has no signatures")
            return result

        if not self.verification:
            result.is_valid = False
            result.errors.append("Bundle has no verification material")
            return result

        if not self.verification.public_key:
            result.is_valid = False
            result.errors.append("Verification material has no public key")
            return result

        # Verify signature
        try:
            if verify_func:
                sig_valid = self._verify_with_func(verify_func)
            else:
                sig_valid = self._verify_ed25519()

            result.signature_valid = sig_valid
            if not sig_valid:
                result.is_valid = False
                result.errors.append("Signature verification failed")
        except Exception as e:
            result.is_valid = False
            result.signature_valid = False
            result.errors.append(f"Signature verification error: {e}")

        # Check timestamp (if present)
        if self.verification.timestamp and self.verification.timestamp.has_token:
            result.warnings.append(
                "Timestamp token present but not verified (requires TSA)"
            )
            result.timestamp_valid = None  # Unknown without TSA

        return result

    def _verify_ed25519(self) -> bool:
        """Verify using Ed25519."""
        try:
            from nacl.exceptions import BadSignatureError
            from nacl.signing import VerifyKey
        except ImportError:
            raise ImportError("nacl library required for Ed25519 verification")

        pub_key_bytes = self.verification.public_key_bytes()
        verify_key = VerifyKey(pub_key_bytes)

        # Find signature with matching key_id
        key_id = self.verification.key_id
        for sig in self.dsse.signatures:
            if key_id and sig.keyid != key_id:
                continue

            # Verify PAE-encoded signature
            pae = self.dsse.pae_bytes()
            try:
                verify_key.verify(pae, sig.signature_bytes())
                return True
            except BadSignatureError:
                continue

        return False

    def _verify_with_func(self, verify_func: Callable[[bytes, bytes], bool]) -> bool:
        """Verify using custom function."""
        pae = self.dsse.pae_bytes()
        for sig in self.dsse.signatures:
            if verify_func(pae, sig.signature_bytes()):
                return True
        return False

    def get_payload(self) -> Optional[Dict[str, Any]]:
        """Extract and parse the payload from the DSSE envelope."""
        if self.dsse:
            return self.dsse.payload_json()
        return None

    @property
    def is_hybrid(self) -> bool:
        """Check if bundle uses hybrid (classical + PQ) signatures."""
        return self.verification is not None and self.verification.is_hybrid
