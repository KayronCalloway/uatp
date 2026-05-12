"""Framework-neutral dataclasses for agent receipt events."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, ClassVar


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return {key: _serialize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


@dataclass(frozen=True)
class AgentIdentity:
    name: str
    version: str | None = None
    vendor: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: _serialize(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class ArtifactRef:
    digest: str
    path: str
    size: int
    media_type: str
    redaction: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {key: _serialize(value) for key, value in asdict(self).items()}


@dataclass(frozen=True)
class ReceiptContext:
    session_id: str
    adapter_name: str
    agent: AgentIdentity
    actor: str = "assistant"
    trust_level: str = "local"

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "adapter_name": self.adapter_name,
            "agent": self.agent.to_dict(),
            "actor": self.actor,
            "trust_level": self.trust_level,
        }


@dataclass(frozen=True)
class AgentReceiptEvent:
    event_type: ClassVar[str]

    event_id: str
    session_id: str
    adapter_name: str
    agent_name: str
    timestamp: datetime
    parent_event_hash: str | None
    actor: str
    payload: dict[str, Any]
    redaction_summary: dict[str, Any]
    trust_level: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "session_id": self.session_id,
            "adapter_name": self.adapter_name,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "parent_event_hash": self.parent_event_hash,
            "actor": self.actor,
            "payload": _serialize(self.payload),
            "redaction_summary": _serialize(self.redaction_summary),
            "trust_level": self.trust_level,
        }


@dataclass(frozen=True)
class SessionStarted(AgentReceiptEvent):
    event_type: ClassVar[str] = "session.started"


@dataclass(frozen=True)
class SessionEnded(AgentReceiptEvent):
    event_type: ClassVar[str] = "session.ended"


@dataclass(frozen=True)
class LLMCallStarted(AgentReceiptEvent):
    event_type: ClassVar[str] = "llm_call.started"


@dataclass(frozen=True)
class LLMCallCompleted(AgentReceiptEvent):
    event_type: ClassVar[str] = "llm_call.completed"


@dataclass(frozen=True)
class ToolCallStarted(AgentReceiptEvent):
    event_type: ClassVar[str] = "tool_call.started"


@dataclass(frozen=True)
class ToolCallCompleted(AgentReceiptEvent):
    event_type: ClassVar[str] = "tool_call.completed"


@dataclass(frozen=True)
class ActionTraceEvent(AgentReceiptEvent):
    event_type: ClassVar[str] = "action.trace"


@dataclass(frozen=True)
class DecisionPointEvent(AgentReceiptEvent):
    event_type: ClassVar[str] = "decision.point"


@dataclass(frozen=True)
class EnvironmentSnapshotEvent(AgentReceiptEvent):
    event_type: ClassVar[str] = "environment.snapshot"


@dataclass(frozen=True)
class MemoryWriteEvent(AgentReceiptEvent):
    event_type: ClassVar[str] = "memory.write"


@dataclass(frozen=True)
class SkillMutationEvent(AgentReceiptEvent):
    event_type: ClassVar[str] = "skill.mutation"


@dataclass(frozen=True)
class UserFeedbackEvent(AgentReceiptEvent):
    event_type: ClassVar[str] = "user.feedback"
