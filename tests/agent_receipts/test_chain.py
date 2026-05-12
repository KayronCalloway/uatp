from dataclasses import replace
from datetime import datetime, timezone

from src.agent_receipts.chain import (
    build_receipt_chain,
    event_hash,
    verify_receipt_chain,
)
from src.agent_receipts.events import (
    ActionTraceEvent,
    AgentReceiptEvent,
    SessionEnded,
    SessionStarted,
)
from src.agent_receipts.hashing import sha256_digest


def event_fields(
    event_id: str, payload: dict, parent_event_hash: str | None = "stale"
) -> dict:
    return {
        "event_id": event_id,
        "session_id": "sess_001",
        "adapter_name": "hermes",
        "agent_name": "Hermes Agent",
        "timestamp": datetime(2026, 5, 8, 21, 10, 0, tzinfo=timezone.utc),
        "parent_event_hash": parent_event_hash,
        "actor": "assistant",
        "payload": payload,
        "redaction_summary": {"secrets_removed": 0},
        "trust_level": "local",
    }


def sample_events() -> list[AgentReceiptEvent]:
    return [
        SessionStarted(**event_fields("evt_001", {"phase": "start"})),
        ActionTraceEvent(**event_fields("evt_002", {"action": "write_tests"})),
        SessionEnded(**event_fields("evt_003", {"phase": "end"})),
    ]


def test_event_hash_uses_canonical_event_dict_digest() -> None:
    event = SessionStarted(**event_fields("evt_001", {"phase": "start"}, None))

    assert event_hash(event) == sha256_digest(event.to_dict())


def test_build_empty_chain_returns_empty_list() -> None:
    assert build_receipt_chain([]) == []


def test_build_receipt_chain_sets_append_only_parent_hashes_without_mutating_inputs() -> (
    None
):
    original_events = sample_events()

    chained_events = build_receipt_chain(original_events)

    assert chained_events is not original_events
    assert [event.parent_event_hash for event in original_events] == [
        "stale",
        "stale",
        "stale",
    ]
    assert [event.parent_event_hash for event in chained_events] == [
        None,
        event_hash(chained_events[0]),
        event_hash(chained_events[1]),
    ]
    assert all(
        chained is not original
        for chained, original in zip(chained_events, original_events, strict=True)
    )


def test_verify_valid_chain_returns_structured_report_with_tip_and_root() -> None:
    chained_events = build_receipt_chain(sample_events())

    report = verify_receipt_chain(chained_events)

    assert report.valid is True
    assert report.errors == ()
    assert report.event_count == 3
    assert report.chain_root_hash == event_hash(chained_events[0])
    assert report.chain_tip_hash == event_hash(chained_events[-1])


def test_verify_empty_chain_reports_valid_empty_chain() -> None:
    report = verify_receipt_chain([])

    assert report.valid is True
    assert report.errors == ()
    assert report.event_count == 0
    assert report.chain_root_hash is None
    assert report.chain_tip_hash is None


def test_verify_detects_wrong_genesis_parent_hash() -> None:
    chained_events = build_receipt_chain(sample_events())
    broken = [
        replace(chained_events[0], parent_event_hash="sha256:not-genesis"),
        *chained_events[1:],
    ]

    report = verify_receipt_chain(broken)

    assert report.valid is False
    assert report.event_count == 3
    assert report.chain_tip_hash is None
    assert report.chain_root_hash is None
    assert report.errors == (
        "event 0 (evt_001) parent_event_hash must be None for genesis event",
        f"event 1 (evt_002) parent_event_hash {chained_events[1].parent_event_hash} does not match previous event hash {event_hash(broken[0])}",
    )


def test_verify_detects_wrong_parent_hash_with_clear_error() -> None:
    chained_events = build_receipt_chain(sample_events())
    broken = [
        chained_events[0],
        replace(chained_events[1], parent_event_hash="sha256:wrong"),
        chained_events[2],
    ]

    report = verify_receipt_chain(broken)

    assert report.valid is False
    assert report.errors == (
        f"event 1 (evt_002) parent_event_hash sha256:wrong does not match previous event hash {event_hash(broken[0])}",
        f"event 2 (evt_003) parent_event_hash {chained_events[2].parent_event_hash} does not match previous event hash {event_hash(broken[1])}",
    )


def test_verify_detects_reordered_events() -> None:
    chained_events = build_receipt_chain(sample_events())

    report = verify_receipt_chain(
        [chained_events[1], chained_events[0], chained_events[2]]
    )

    assert report.valid is False
    assert report.errors == (
        "event 0 (evt_002) parent_event_hash must be None for genesis event",
        f"event 1 (evt_001) parent_event_hash None does not match previous event hash {event_hash(chained_events[1])}",
        f"event 2 (evt_003) parent_event_hash {chained_events[2].parent_event_hash} does not match previous event hash {event_hash(chained_events[0])}",
    )


def test_verify_detects_missing_middle_event() -> None:
    chained_events = build_receipt_chain(sample_events())

    report = verify_receipt_chain([chained_events[0], chained_events[2]])

    assert report.valid is False
    assert report.event_count == 2
    assert report.chain_tip_hash is None
    assert report.chain_root_hash is None
    assert report.errors == (
        f"event 1 (evt_003) parent_event_hash {chained_events[2].parent_event_hash} does not match previous event hash {event_hash(chained_events[0])}",
    )


def test_verify_detects_tampered_middle_event_payload() -> None:
    chained_events = build_receipt_chain(sample_events())
    tampered_middle = replace(
        chained_events[1], payload={"action": "changed_after_chain_build"}
    )

    report = verify_receipt_chain(
        [chained_events[0], tampered_middle, chained_events[2]]
    )

    assert report.valid is False
    assert report.chain_tip_hash is None
    assert report.chain_root_hash is None
    assert report.errors == (
        f"event 2 (evt_003) parent_event_hash {chained_events[2].parent_event_hash} does not match previous event hash {event_hash(tampered_middle)}",
    )
