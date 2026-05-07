from dataclasses import dataclass
from datetime import datetime
from typing import Any, List

from src.integrations.hermes import hermes_capture


@dataclass
class MockSignal:
    signal_type: str = "neutral"
    references_previous: bool = False
    sentiment_delta: float = 0.0
    matched_phrases: List[str] = None

    def __post_init__(self):
        if self.matched_phrases is None:
            self.matched_phrases = []


class MockDetector:
    def detect_signal(self, *_args, **_kwargs):
        return MockSignal()


@dataclass
class MockConversationMessage:
    role: str
    content: str
    timestamp: datetime
    message_id: str
    session_id: str
    token_count: int | None = None
    model_info: str | None = None
    signal_type: str = "neutral"
    references_previous: bool = False
    sentiment_delta: float = 0.0


@dataclass
class MockConversationSession:
    session_id: str
    user_id: str
    start_time: datetime
    platform: str
    end_time: datetime
    messages: List[Any]
    significance_score: float
    total_tokens: int
    topics: List[str]


def patch_capture_dependencies(monkeypatch):
    monkeypatch.setattr(
        hermes_capture,
        "_get_capture_classes",
        lambda: (MockConversationMessage, MockConversationSession),
    )
    monkeypatch.setattr(hermes_capture, "_get_signal_detector", lambda: MockDetector())


def test_assistant_thinking_is_preserved_for_enhancer(monkeypatch):
    patch_capture_dependencies(monkeypatch)

    conv = hermes_capture._convert_to_uatp_objects(
        "sess_1",
        {"started_at": 1, "model": "test-model"},
        [
            {"role": "user", "content": "do work", "timestamp": 2},
            {
                "role": "assistant",
                "content": "Visible answer.",
                "reasoning": "private reasoning trace",
                "timestamp": 3,
            },
        ],
    )

    assistant = conv.messages[1]
    assert assistant.content.startswith(
        "[THINKING]\nprivate reasoning trace\n[/THINKING]"
    )
    assert assistant.content.endswith("Visible answer.")
    assert assistant._hermes_thinking == "private reasoning trace"


def test_reasoning_only_assistant_turn_is_not_dropped(monkeypatch):
    patch_capture_dependencies(monkeypatch)

    conv = hermes_capture._convert_to_uatp_objects(
        "sess_2",
        {"started_at": 1, "model": "test-model"},
        [
            {"role": "user", "content": "inspect", "timestamp": 2},
            {
                "role": "assistant",
                "content": "",
                "reasoning": "deciding which tool to call",
                "timestamp": 3,
                "tool_calls": "[]",
            },
        ],
    )

    assert len(conv.messages) == 2
    assistant = conv.messages[1]
    assert assistant.content == "[THINKING]\ndeciding which tool to call\n[/THINKING]"
    assert assistant._hermes_thinking == "deciding which tool to call"
