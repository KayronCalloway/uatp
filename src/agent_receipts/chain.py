"""Append-only parent-hash receipt chain helpers."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

from src.agent_receipts.events import AgentReceiptEvent
from src.agent_receipts.hashing import sha256_digest


@dataclass(frozen=True)
class ChainVerificationReport:
    valid: bool
    errors: tuple[str, ...]
    event_count: int
    chain_tip_hash: str | None
    chain_root_hash: str | None = None


def event_hash(event: AgentReceiptEvent) -> str:
    """Return the canonical hash for an event's serialized representation."""
    return sha256_digest(event.to_dict())


def build_receipt_chain(events: Sequence[AgentReceiptEvent]) -> list[AgentReceiptEvent]:
    """Return new events linked by parent_event_hash in input order."""
    chained_events: list[AgentReceiptEvent] = []
    parent_hash: str | None = None

    for event in events:
        chained_event = replace(event, parent_event_hash=parent_hash)
        chained_events.append(chained_event)
        parent_hash = event_hash(chained_event)

    return chained_events


def verify_receipt_chain(
    events: Sequence[AgentReceiptEvent],
) -> ChainVerificationReport:
    """Verify local parent-hash adjacency for the supplied ordered event sequence.

    This does not prove completeness, signing, timestamp validity, or artifact
    integrity. Root/tip hashes are returned only when the supplied sequence is
    internally valid.
    """
    errors: list[str] = []
    event_hashes = [event_hash(event) for event in events]

    for index, event in enumerate(events):
        expected_parent_hash = None if index == 0 else event_hashes[index - 1]
        if event.parent_event_hash == expected_parent_hash:
            continue

        if index == 0:
            errors.append(
                f"event 0 ({event.event_id}) parent_event_hash must be None for genesis event"
            )
        else:
            errors.append(
                f"event {index} ({event.event_id}) parent_event_hash {event.parent_event_hash} "
                f"does not match previous event hash {expected_parent_hash}"
            )

    valid = not errors
    return ChainVerificationReport(
        valid=valid,
        errors=tuple(errors),
        event_count=len(events),
        chain_tip_hash=event_hashes[-1] if valid and event_hashes else None,
        chain_root_hash=event_hashes[0] if valid and event_hashes else None,
    )
