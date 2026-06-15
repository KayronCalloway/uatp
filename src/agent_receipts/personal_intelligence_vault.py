"""Personal Intelligence Vault receipt helpers.

This module intentionally stays at the receipt layer. It does not implement an
Apple adapter or a marketplace. The point is narrower: model a local vault that
returns scoped references instead of raw memory, then build a signed,
offline-verifiable chain showing scoped memory access, policy, model action,
user correction, and the resulting memory write without exposing raw user
memory.
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
    RefusalEvent,
    SessionEnded,
    SessionStarted,
    UserFeedbackEvent,
)
from src.agent_receipts.hashing import sha256_digest

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
class LocalMemoryGrant:
    """Policy decision returned by the local vault."""

    granted: bool
    refs: list[ScopedMemoryRef]
    policy: PurposePolicy
    denial_reason: str | None = None

    def to_receipt_payload(self) -> dict[str, Any]:
        return {
            "granted": self.granted,
            "granted_refs": [ref.to_dict() for ref in self.refs],
            "policy": self.policy.to_dict(),
            "purpose": self.policy.purpose,
            "allowed_app": self.policy.allowed_app,
            "allowed_model": self.policy.allowed_model,
            "locality_requirement": self.policy.locality_requirement,
            "training_allowed": self.policy.training_allowed,
            "licensing_terms": self.policy.licensing_terms,
            "denial_reason": self.denial_reason,
        }


@dataclass(frozen=True)
class _VaultMemoryRecord:
    memory_id: str
    raw_memory: Any
    scope: tuple[str, ...]
    capsule_ref: str

    def scoped_ref(self, requested_scopes: set[str]) -> ScopedMemoryRef | None:
        granted_scope = sorted(set(self.scope) & requested_scopes)
        if not granted_scope:
            return None
        return ScopedMemoryRef(
            memory_id=self.memory_id,
            capsule_ref=self.capsule_ref,
            digest=sha256_digest(self.raw_memory),
            scope=granted_scope,
        )


class LocalPersonalMemoryVault:
    """In-memory vault that exposes scoped references, not raw memory.

    This is deliberately small and local. It is a standards slice for the receipt
    path, not a hosted product store.
    """

    def __init__(self) -> None:
        self._records: dict[str, _VaultMemoryRecord] = {}

    def put_memory(
        self,
        *,
        memory_id: str,
        raw_memory: Any,
        scope: Sequence[str],
        capsule_ref: str,
    ) -> ScopedMemoryRef:
        record = _VaultMemoryRecord(
            memory_id=memory_id,
            raw_memory=raw_memory,
            scope=tuple(scope),
            capsule_ref=capsule_ref,
        )
        self._records[memory_id] = record
        return ScopedMemoryRef(
            memory_id=memory_id,
            capsule_ref=capsule_ref,
            digest=sha256_digest(raw_memory),
            scope=list(scope),
        )

    def request_context(
        self,
        *,
        requested_scopes: Sequence[str],
        policy: PurposePolicy,
        app: str,
        model: str,
        locality: str = "local_only",
    ) -> LocalMemoryGrant:
        if app != policy.allowed_app:
            return LocalMemoryGrant(False, [], policy, "app_not_allowed")
        if model != policy.allowed_model:
            return LocalMemoryGrant(False, [], policy, "model_not_allowed")
        if policy.locality_requirement == "local_only" and locality != "local_only":
            return LocalMemoryGrant(False, [], policy, "locality_not_allowed")

        requested = set(requested_scopes)
        refs = [
            ref
            for record in self._records.values()
            if (ref := record.scoped_ref(requested)) is not None
        ]
        if not refs:
            return LocalMemoryGrant(False, [], policy, "scope_not_available")
        return LocalMemoryGrant(True, refs, policy)


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


def build_personal_memory_denial_receipt_events(
    *,
    session_id: str,
    adapter_name: str,
    agent_name: str,
    user_id_hash: str,
    request_id: str,
    requested_scopes: Sequence[str],
    policy: PurposePolicy,
    denial_reason: str,
    started_at: datetime,
    actor: str = "assistant",
    trust_level: str = "local",
) -> list[AgentReceiptEvent]:
    """Build a signed-receipt-ready chain for a denied context request."""
    _validate_sha256(user_id_hash, "user_id_hash")
    policy_dict = policy.to_dict()
    requested_scope_list = list(requested_scopes)

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
                "goals": ["request scoped personal memory under policy"],
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
                "alternatives_considered": ["answer without memory"],
                "constraints_applied": [
                    "return capsule references, not raw memory",
                    "deny context when purpose policy does not allow it",
                ],
                "confidence": 0.95,
                "context_summary": "Personal memory access must be denied when policy fails.",
                "requested_scopes": requested_scope_list,
                "policy": policy_dict,
            },
        )
    )
    refusal = RefusalEvent(
        **_event_fields(
            event_id=f"{request_id}:context_denied",
            session_id=session_id,
            adapter_name=adapter_name,
            agent_name=agent_name,
            timestamp=started_at + timedelta(seconds=2),
            actor="user",
            trust_level=trust_level,
            payload={
                "refusal_id": f"{request_id}:context_denied",
                "reason": denial_reason,
                "violations": [denial_reason],
                "request_id": request_id,
                "requested_scopes": requested_scope_list,
                "granted_refs": [],
                "policy": policy_dict,
                "purpose": policy.purpose,
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
            timestamp=started_at + timedelta(seconds=3),
            actor=actor,
            trust_level=trust_level,
            payload={
                "status": "refused",
                "tool_call_count": 0,
                "action_count": 0,
                "decision_count": 1,
                "outcome_summary": "Scoped personal memory request denied by purpose policy.",
            },
        )
    )
    return [start, context_request, refusal, end]


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
