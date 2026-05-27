"""Shared Hermes capsule signal filtering helpers."""

from __future__ import annotations

HERMES_META_MARKERS: tuple[tuple[str, str], ...] = (
    ("context_compaction", "[CONTEXT COMPACTION"),
    ("preserved_task_list", "[Your active task list was preserved"),
    ("model_switch", "[Note: model was just switched"),
    ("background_process_notification", "[IMPORTANT: Background process"),
    (
        "tool_iteration_limit",
        "You've reached the maximum number of tool-calling iterations allowed",
    ),
)

# Backwards-compatible alias for existing imports/references.
META_MARKERS = tuple(marker for _kind, marker in HERMES_META_MARKERS)


def classify_hermes_meta_message(text: str) -> str | None:
    """Return the operational Hermes meta-message kind, if text contains one."""
    normalized = (text or "").strip().lower()
    for kind, marker in HERMES_META_MARKERS:
        if marker.lower() in normalized:
            return kind
    return None


def is_hermes_meta_message(text: str) -> bool:
    """Return True for operational Hermes handoff text, not user feedback."""
    return classify_hermes_meta_message(text) is not None
