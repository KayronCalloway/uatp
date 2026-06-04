"""Ed25519 signing helpers for framework-neutral agent receipts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from src.agent_receipts.chain import ChainVerificationReport, event_hash
from src.agent_receipts.events import AgentReceiptEvent
from src.agent_receipts.hashing import canonical_json_bytes, sha256_digest

SIGNATURE_PREIMAGE_DOMAIN = "UATP-AgentReceipt-v1"


def _is_all_zero_hex(value: str) -> bool:
    return bool(value) and all(char == "0" for char in value)


@dataclass(frozen=True)
class SignedReceipt:
    """JSON-compatible signed receipt envelope."""

    event: dict[str, Any]
    event_hash: str
    signature: str
    public_key: str
    signer_id: str
    signature_algorithm: str = "Ed25519"

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "event_hash": self.event_hash,
            "signature": self.signature,
            "public_key": self.public_key,
            "signer_id": self.signer_id,
            "signature_algorithm": self.signature_algorithm,
        }


@dataclass(frozen=True)
class ReceiptTrustPolicy:
    """Trust roots for offline receipt verification.

    A valid Ed25519 signature only proves possession of a private key. This
    policy binds signer identity to the raw public keys a verifier is willing
    to trust for that identity.
    """

    trusted_public_keys_by_signer: dict[str, frozenset[str]]

    @classmethod
    def from_signers(
        cls, signers: dict[str, str | Sequence[str]]
    ) -> ReceiptTrustPolicy:
        trusted: dict[str, frozenset[str]] = {}
        for signer_id, public_keys in signers.items():
            if isinstance(public_keys, str):
                key_set = frozenset([public_keys])
            else:
                key_set = frozenset(public_keys)
            trusted[signer_id] = key_set
        return cls(trusted_public_keys_by_signer=trusted)

    def validate(self, signed: SignedReceipt) -> tuple[str, ...]:
        trusted_keys = self.trusted_public_keys_by_signer.get(signed.signer_id)
        if trusted_keys is None:
            return (f"signer {signed.signer_id} is not trusted",)
        if signed.public_key not in trusted_keys:
            return (f"signer {signed.signer_id} public key is not trusted",)
        return ()


@dataclass(frozen=True)
class SignatureVerificationReport:
    valid: bool
    errors: tuple[str, ...]
    event_hash: str | None
    signer_id: str


class Ed25519ReceiptSigner:
    """Sign receipt event hashes with Ed25519."""

    def __init__(self, signing_key: SigningKey, *, signer_id: str) -> None:
        self._signing_key = signing_key
        self.signer_id = signer_id

    @classmethod
    def generate(cls, *, signer_id: str) -> Ed25519ReceiptSigner:
        return cls(SigningKey.generate(), signer_id=signer_id)

    @classmethod
    def from_hex(cls, signing_key_hex: str, *, signer_id: str) -> Ed25519ReceiptSigner:
        return cls(SigningKey(bytes.fromhex(signing_key_hex)), signer_id=signer_id)

    @property
    def public_key_hex(self) -> str:
        return bytes(self._signing_key.verify_key).hex()

    @property
    def signing_key_hex(self) -> str:
        return bytes(self._signing_key).hex()

    def signature_preimage(self, receipt_hash: str) -> bytes:
        return signature_preimage(
            event_hash=receipt_hash,
            public_key=self.public_key_hex,
            signer_id=self.signer_id,
        )

    def sign_hash(self, receipt_hash: str) -> str:
        return self._signing_key.sign(
            self.signature_preimage(receipt_hash)
        ).signature.hex()

    def sign_event(self, event: AgentReceiptEvent) -> SignedReceipt:
        serialized_event = event.to_dict()
        receipt_hash = event_hash(event)
        return SignedReceipt(
            event=serialized_event,
            event_hash=receipt_hash,
            signature=self.sign_hash(receipt_hash),
            public_key=self.public_key_hex,
            signer_id=self.signer_id,
        )


def signature_preimage(
    *,
    event_hash: str,
    public_key: str,
    signer_id: str,
    signature_algorithm: str = "Ed25519",
) -> bytes:
    """Return the domain-separated bytes covered by a receipt signature."""
    return canonical_json_bytes(
        {
            "domain": SIGNATURE_PREIMAGE_DOMAIN,
            "event_hash": event_hash,
            "public_key": public_key,
            "signature_algorithm": signature_algorithm,
            "signer_id": signer_id,
        }
    )


def verify_hash_signature(
    *,
    public_key: str,
    signature: str,
    digest: str,
    signer_id: str,
    signature_algorithm: str = "Ed25519",
) -> None:
    """Verify a signature over a domain-separated content hash."""
    if signature_algorithm != "Ed25519":
        raise ValueError(f"unsupported signature_algorithm: {signature_algorithm}")
    verify_key = VerifyKey(bytes.fromhex(public_key))
    verify_key.verify(
        signature_preimage(
            event_hash=digest,
            public_key=public_key,
            signer_id=signer_id,
            signature_algorithm=signature_algorithm,
        ),
        bytes.fromhex(signature),
    )


def _verify_signature(signed: SignedReceipt) -> None:
    verify_hash_signature(
        public_key=signed.public_key,
        signature=signed.signature,
        digest=signed.event_hash,
        signer_id=signed.signer_id,
        signature_algorithm=signed.signature_algorithm,
    )


def verify_signed_receipt(
    signed: SignedReceipt,
    *,
    trust_policy: ReceiptTrustPolicy | None = None,
) -> SignatureVerificationReport:
    """Verify a single signed receipt envelope."""
    errors: list[str] = []
    computed_hash = sha256_digest(signed.event)
    if computed_hash != signed.event_hash:
        errors.append("event_hash does not match signed event payload")
        return SignatureVerificationReport(
            valid=False,
            errors=tuple(errors),
            event_hash=None,
            signer_id=signed.signer_id,
        )

    if signed.signature_algorithm != "Ed25519":
        errors.append(f"unsupported signature_algorithm: {signed.signature_algorithm}")
        return SignatureVerificationReport(
            valid=False,
            errors=tuple(errors),
            event_hash=None,
            signer_id=signed.signer_id,
        )

    if _is_all_zero_hex(signed.signature):
        errors.append("placeholder signature is not valid evidence")
        return SignatureVerificationReport(
            valid=False,
            errors=tuple(errors),
            event_hash=None,
            signer_id=signed.signer_id,
        )

    if trust_policy is not None:
        errors.extend(trust_policy.validate(signed))
        if errors:
            return SignatureVerificationReport(
                valid=False,
                errors=tuple(errors),
                event_hash=None,
                signer_id=signed.signer_id,
            )

    try:
        _verify_signature(signed)
    except (BadSignatureError, ValueError) as exc:
        errors.append(f"signature verification failed: {exc}")

    valid = not errors
    return SignatureVerificationReport(
        valid=valid,
        errors=tuple(errors),
        event_hash=signed.event_hash if valid else None,
        signer_id=signed.signer_id,
    )


def sign_receipt_chain(
    events: Sequence[AgentReceiptEvent], signer: Ed25519ReceiptSigner
) -> list[SignedReceipt]:
    """Build parent-hash links for events and return signed receipt envelopes."""
    from src.agent_receipts.chain import build_receipt_chain

    return [signer.sign_event(event) for event in build_receipt_chain(events)]


def verify_signed_receipt_chain(
    signed_receipts: Sequence[SignedReceipt],
    *,
    trust_policy: ReceiptTrustPolicy | None = None,
) -> ChainVerificationReport:
    """Verify signatures and append-only parent-hash adjacency for signed receipts."""
    errors: list[str] = []
    event_hashes: list[str] = []

    for index, signed in enumerate(signed_receipts):
        signature_report = verify_signed_receipt(signed, trust_policy=trust_policy)
        if not signature_report.valid:
            errors.extend(
                f"event {index} ({signed.event.get('event_id')}): {error}"
                for error in signature_report.errors
            )
        event_hashes.append(sha256_digest(signed.event))

    for index, signed in enumerate(signed_receipts):
        event = signed.event
        expected_parent_hash = None if index == 0 else event_hashes[index - 1]
        if event.get("parent_event_hash") == expected_parent_hash:
            continue
        if index == 0:
            errors.append(
                f"event 0 ({event.get('event_id')}) parent_event_hash must be None for genesis event"
            )
        else:
            errors.append(
                f"event {index} ({event.get('event_id')}) parent_event_hash {event.get('parent_event_hash')} "
                f"does not match previous event hash {expected_parent_hash}"
            )

    valid = not errors
    return ChainVerificationReport(
        valid=valid,
        errors=tuple(errors),
        event_count=len(signed_receipts),
        chain_tip_hash=event_hashes[-1] if valid and event_hashes else None,
        chain_root_hash=event_hashes[0] if valid and event_hashes else None,
    )
