"""Ed25519 signing helpers for framework-neutral agent receipts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from src.agent_receipts.chain import ChainVerificationReport, event_hash
from src.agent_receipts.events import AgentReceiptEvent
from src.agent_receipts.hashing import sha256_digest


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

    def sign_hash(self, receipt_hash: str) -> str:
        return self._signing_key.sign(receipt_hash.encode("utf-8")).signature.hex()

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


def _verify_signature(
    public_key_hex: str, signature_hex: str, receipt_hash: str
) -> None:
    verify_key = VerifyKey(bytes.fromhex(public_key_hex))
    verify_key.verify(receipt_hash.encode("utf-8"), bytes.fromhex(signature_hex))


def verify_signed_receipt(signed: SignedReceipt) -> SignatureVerificationReport:
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

    try:
        _verify_signature(signed.public_key, signed.signature, signed.event_hash)
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
) -> ChainVerificationReport:
    """Verify signatures and append-only parent-hash adjacency for signed receipts."""
    errors: list[str] = []
    event_hashes: list[str] = []

    for index, signed in enumerate(signed_receipts):
        signature_report = verify_signed_receipt(signed)
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
