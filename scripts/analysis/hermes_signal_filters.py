"""Shared Hermes capsule signal filtering helpers."""

META_MARKERS = (
    "[CONTEXT COMPACTION",
    "[Your active task list was preserved",
    "[Note: model was just switched",
)


def is_hermes_meta_message(text: str) -> bool:
    """Return True for operational Hermes handoff text, not user feedback."""
    normalized = (text or "").strip()
    return any(marker.lower() in normalized.lower() for marker in META_MARKERS)
