"""Personal Intelligence Vault receipt helpers.

This module intentionally stays at the receipt layer. It does not implement an
Apple adapter, a marketplace, or raw-memory storage. The point is narrower:
build a signed, offline-verifiable chain showing scoped memory access, policy,
model action, user correction, and the resulting memory write without exposing
raw user memory.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, ClassVar, Sequence

from src.agent_receipts.events import (
    AgentReceiptEvent,
    DecisionPointEvent,
    LLMCallCompleted,
    MemoryWriteEvent,
    SessionEnded,
    SessionStarted,
    UserFeedbackEvent,
)

SHA256_PATTERN = re.compile(r"^sha256:[a-f0-9]{64}$")


@dataclass(frozen=True)
class PurposePolicy:
    """Purpose-bound policy for scoped personal-memory use."""

    purpose: str
    allowed_app: str
    allowed_model: str
    locality_requirement: str
    training_allowed: bool
    retention_expires_at: datetime | None
    licensing_terms: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["retention_expires_at"] = (
            self.retention_expires_at.isoformat()
            if self.retention_expires_at is not None
            else None
        )
        return data


@dataclass(frozen=True)
class ScopedMemoryRef:
    """Reference to scoped memory; never carries raw memory content."""

    memory_id: str
    capsule_ref: str
    digest: str
    scope: list[str]

    def to_dict(self) -> dict[str, Any]:
        _validate_sha256(self.digest, "memory ref digest")
        return {
            "memory_id": self.memory_id,
            "capsule_ref": self.capsule_ref,
            "digest": self.digest,
            "scope": list(self.scope),
        }


@dataclass(frozen=True)
class ContextGrantEvent(AgentReceiptEvent):
    """Receipt event for a user/policy-scoped context grant."""

    event_type: ClassVar[str] = "consent"


def _validate_sha256(value: str, field_name: str) -> str:
    if not SHA256_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must use sha256:<64 lowercase hex> format")
    return value


def _event_fields(
    *,
    event_id: str,
    session_id: str,
    adapter_name: str,
    agent_name: str,
    timestamp: datetime,
    actor: str,
    payload: dict[str, Any],
    trust_level: str,
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "session_id": session_id,
        "adapter_name": adapter_name,
        "agent_name": agent_name,
        "timestamp": timestamp,
        "parent_event_hash": None,
        "actor": actor,
        "payload": payload,
        "redaction_summary": {"raw_memory_included": False, "secrets_removed": 0},
        "trust_level": trust_level,
    }


def build_personal_memory_receipt_events(
    *,
    session_id: str,
    adapter_name: str,
    agent_name: str,
    user_id_hash: str,
    request_id: str,
    granted_refs: Sequence[ScopedMemoryRef],
    policy: PurposePolicy,
    model_action_summary: str,
    correction: str,
    memory_write_id: str,
    memory_write_digest: str,
    started_at: datetime,
    actor: str = "assistant",
    trust_level: str = "local",
) -> list[AgentReceiptEvent]:
    """Build a minimal Personal Intelligence Vault receipt chain.

    The chain proves scoped memory was requested/granted under policy, used for a
    model action, corrected by the user, then written back by digest. It returns
    neutral receipt events only; signing and offline verification remain sink and
    verifier responsibilities.
    """
    _validate_sha256(user_id_hash, "user_id_hash")
    _validate_sha256(memory_write_digest, "memory_write_digest")
    scoped_refs = [ref.to_dict() for ref in granted_refs]
    policy_dict = policy.to_dict()

    start = SessionStarted(
        **_event_fields(
            event_id=f"{request_id}:session_started",
            session_id=session_id,
            adapter_name=adapter_name,
            agent_name=agent_name,
            timestamp=started_at,
            actor=actor,
            trust_level=trust_level,
            payload={
                "platform": "personal-intelligence-vault",
                "goals": ["use scoped personal memory without exposing raw memory"],
                "user_id_hash": user_id_hash,
            },
        )
    )
    context_request = DecisionPointEvent(
        **_event_fields(
            event_id=f"{request_id}:context_request",
            session_id=session_id,
            adapter_name=adapter_name,
            agent_name=agent_name,
            timestamp=started_at + timedelta(seconds=1),
            actor=actor,
            trust_level=trust_level,
            payload={
                "decision_id": request_id,
                "step_index": 1,
                "decision_summary": "Request scoped personal memory references for this user task.",
                "selected_action": "request_scoped_memory_context",
                "alternatives_considered": [
                    "answer without memory",
                    "request unrestricted raw memory",
                ],
                "constraints_applied": [
                    "return capsule references, not raw memory",
                    "enforce purpose policy before model use",
                ],
                "confidence": 0.95,
                "context_summary": "Personal memory is needed only as scoped references.",
                "policy": policy_dict,
            },
        )
    )
    context_grant = ContextGrantEvent(
        **_event_fields(
            event_id=f"{request_id}:context_grant",
            session_id=session_id,
            adapter_name=adapter_name,
            agent_name=agent_name,
            timestamp=started_at + timedelta(seconds=2),
            actor="user",
            trust_level=trust_level,
            payload={
                "request_id": request_id,
                "grantor": user_id_hash,
                "granted_to": agent_name,
                "consent_scope": sorted(
                    {scope for ref in scoped_refs for scope in ref["scope"]}
                ),
                "granted_refs": scoped_refs,
                "policy": policy_dict,
                "purpose": policy.purpose,
                "allowed_app": policy.allowed_app,
                "allowed_model": policy.allowed_model,
                "locality_requirement": policy.locality_requirement,
                "training_allowed": policy.training_allowed,
                "licensing_terms": policy.licensing_terms,
                "retention_expires_at": policy_dict["retention_expires_at"],
            },
        )
    )
    llm_completed = LLMCallCompleted(
        **_event_fields(
            event_id=f"{request_id}:llm_completed",
            session_id=session_id,
            adapter_name=adapter_name,
            agent_name=agent_name,
            timestamp=started_at + timedelta(seconds=3),
            actor=actor,
            trust_level=trust_level,
            payload={
                "request_id": request_id,
                "model": policy.allowed_model,
                "purpose": policy.purpose,
                "used_memory_refs": scoped_refs,
                "action_summary": model_action_summary,
                "training_allowed": policy.training_allowed,
            },
        )
    )
    feedback = UserFeedbackEvent(
        **_event_fields(
            event_id=f"{request_id}:user_feedback",
            session_id=session_id,
            adapter_name=adapter_name,
            agent_name=agent_name,
            timestamp=started_at + timedelta(seconds=4),
            actor="user",
            trust_level=trust_level,
            payload={
                "request_id": request_id,
                "feedback_type": "correction",
                "correction": correction,
                "license_status": policy.licensing_terms,
                "training_allowed": policy.training_allowed,
            },
        )
    )
    memory_write = MemoryWriteEvent(
        **_event_fields(
            event_id=f"{request_id}:memory_write",
            session_id=session_id,
            adapter_name=adapter_name,
            agent_name=agent_name,
            timestamp=started_at + timedelta(seconds=5),
            actor=actor,
            trust_level=trust_level,
            payload={
                "memory_write_id": memory_write_id,
                "source_feedback_event_id": feedback.event_id,
                "memory_write_digest": memory_write_digest,
                "purpose": policy.purpose,
                "policy": policy_dict,
                "training_allowed": policy.training_allowed,
                "licensing_terms": policy.licensing_terms,
            },
        )
    )
    end = SessionEnded(
        **_event_fields(
            event_id=f"{request_id}:session_ended",
            session_id=session_id,
            adapter_name=adapter_name,
            agent_name=agent_name,
            timestamp=started_at + timedelta(seconds=6),
            actor=actor,
            trust_level=trust_level,
            payload={
                "status": "completed",
                "tool_call_count": 0,
                "action_count": 1,
                "decision_count": 1,
                "outcome_summary": "Scoped personal memory used and corrected under signed policy receipts.",
            },
        )
    )
    return [
        start,
        context_request,
        context_grant,
        llm_completed,
        feedback,
        memory_write,
        end,
    ]
