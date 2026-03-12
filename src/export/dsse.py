"""
DSSE (Dead Simple Signing Envelope) - Sigstore-style envelope format.

DSSE provides a standardized way to package signed payloads:
- payload: Base64-encoded content
- payloadType: MIME type
- signatures: Array of keyid + sig pairs

This allows UATP capsules to be verified by any system that
understands DSSE, without requiring UATP-specific tooling.
"""

import base64
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.export.pae import pae_encode, sign_pae, verify_pae

# UATP-specific payload types
PAYLOAD_TYPE_CAPSULE = "application/vnd.uatp.capsule.v1+json"
PAYLOAD_TYPE_WORKFLOW = "application/vnd.uatp.workflow.v1+json"
PAYLOAD_TYPE_ATTESTATION = "application/vnd.uatp.attestation.v1+json"


@dataclass
class DSSESignature:
    """A single signature in a DSSE envelope."""

    keyid: str  # Key identifier (e.g., "ed25519-abc123")
    sig: str  # Base64-encoded signature

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DSSESignature":
        return cls(
            keyid=data["keyid"],
            sig=data["sig"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keyid": self.keyid,
            "sig": self.sig,
        }

    def signature_bytes(self) -> bytes:
        """Decode signature from base64."""
        return base64.b64decode(self.sig)


@dataclass
class DSSEEnvelope:
    """
    DSSE Envelope - standardized signed payload container.

    Structure:
    {
        "payload": "<Base64(content)>",
        "payloadType": "application/vnd.uatp.capsule.v1+json",
        "signatures": [
            {"keyid": "ed25519-<hash>", "sig": "<Base64(sig)>"}
        ]
    }
    """

    payload: str  # Base64-encoded payload
    payload_type: str  # MIME type
    signatures: List[DSSESignature] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        content: bytes,
        payload_type: str = PAYLOAD_TYPE_CAPSULE,
    ) -> "DSSEEnvelope":
        """
        Create an unsigned envelope from content.

        Args:
            content: Raw bytes to wrap
            payload_type: MIME type of content

        Returns:
            Unsigned DSSEEnvelope
        """
        return cls(
            payload=base64.b64encode(content).decode("ascii"),
            payload_type=payload_type,
        )

    @classmethod
    def from_json(cls, json_data: Any) -> "DSSEEnvelope":
        """
        Create from JSON dict or string.

        Args:
            json_data: Dict or JSON string

        Returns:
            DSSEEnvelope instance
        """
        if isinstance(json_data, str):
            json_data = json.loads(json_data)

        return cls(
            payload=json_data["payload"],
            payload_type=json_data["payloadType"],
            signatures=[
                DSSESignature.from_dict(s) for s in json_data.get("signatures", [])
            ],
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DSSEEnvelope":
        """Alias for from_json with dict input."""
        return cls.from_json(data)

    def payload_bytes(self) -> bytes:
        """Decode payload from base64."""
        return base64.b64decode(self.payload)

    def payload_json(self) -> Any:
        """Decode payload and parse as JSON."""
        return json.loads(self.payload_bytes())

    def pae_bytes(self) -> bytes:
        """Get PAE-encoded bytes for signing/verification."""
        return pae_encode(self.payload_type, self.payload_bytes())

    def sign(
        self,
        keyid: str,
        sign_func: Callable[[bytes], bytes],
    ) -> "DSSEEnvelope":
        """
        Add a signature to this envelope.

        Args:
            keyid: Key identifier
            sign_func: Function that signs bytes and returns signature bytes

        Returns:
            Self (for chaining)
        """
        # Sign the PAE-encoded data
        sig_bytes = sign_pae(self.payload_type, self.payload_bytes(), sign_func)
        sig_b64 = base64.b64encode(sig_bytes).decode("ascii")

        self.signatures.append(DSSESignature(keyid=keyid, sig=sig_b64))
        return self

    def verify(
        self,
        keyid: str,
        verify_func: Callable[[bytes, bytes], bool],
    ) -> bool:
        """
        Verify a specific signature.

        Args:
            keyid: Key identifier to verify
            verify_func: Function that verifies (message, signature) -> bool

        Returns:
            True if signature is valid
        """
        # Find signature with this keyid
        for sig in self.signatures:
            if sig.keyid == keyid:
                return verify_pae(
                    self.payload_type,
                    self.payload_bytes(),
                    sig.signature_bytes(),
                    verify_func,
                )
        return False

    def verify_any(
        self,
        verify_funcs: Dict[str, Callable[[bytes, bytes], bool]],
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify any signature with matching keyid.

        Args:
            verify_funcs: Dict of keyid -> verify function

        Returns:
            Tuple of (is_valid, keyid_that_verified)
        """
        for sig in self.signatures:
            if sig.keyid in verify_funcs:
                if self.verify(sig.keyid, verify_funcs[sig.keyid]):
                    return True, sig.keyid
        return False, None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "payload": self.payload,
            "payloadType": self.payload_type,
            "signatures": [s.to_dict() for s in self.signatures],
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @property
    def is_signed(self) -> bool:
        """Check if envelope has any signatures."""
        return len(self.signatures) > 0


def create_capsule_envelope(
    capsule_data: Dict[str, Any],
) -> DSSEEnvelope:
    """
    Create a DSSE envelope for a capsule.

    Args:
        capsule_data: Capsule as dictionary

    Returns:
        Unsigned DSSEEnvelope ready for signing
    """
    content = json.dumps(capsule_data, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return DSSEEnvelope.create(content, PAYLOAD_TYPE_CAPSULE)


def create_workflow_envelope(
    workflow_data: Dict[str, Any],
) -> DSSEEnvelope:
    """
    Create a DSSE envelope for a workflow attestation.

    Args:
        workflow_data: Workflow as dictionary

    Returns:
        Unsigned DSSEEnvelope ready for signing
    """
    content = json.dumps(workflow_data, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return DSSEEnvelope.create(content, PAYLOAD_TYPE_WORKFLOW)
