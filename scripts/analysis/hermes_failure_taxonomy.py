"""Deterministic failure taxonomy for Hermes correction chains."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CorrectionChain:
    prompt: str
    rejected_response: str
    correction: str
    chosen_response: str
    model: str | None = None
    source_capsule_id: str | None = None
    step_indices: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_eval_record(cls, record: dict[str, Any]) -> CorrectionChain:
        return cls(
            prompt=str(record.get("prompt") or ""),
            rejected_response=str(record.get("rejected_response") or ""),
            correction=str(record.get("correction") or ""),
            chosen_response=str(record.get("chosen_response") or ""),
            model=str(record.get("model") or "") or None,
            source_capsule_id=str(record.get("source_capsule_id") or "") or None,
            step_indices=dict(record.get("step_indices") or {}),
        )


def evidence_id(chain: CorrectionChain) -> str:
    if not chain.source_capsule_id:
        return "unknown"
    indices = chain.step_indices or {}
    if {"prompt", "rejected_response", "correction", "chosen_response"}.issubset(
        indices
    ):
        return (
            f"{chain.source_capsule_id}:"
            f"{indices['prompt']}-{indices['rejected_response']}-"
            f"{indices['correction']}-{indices['chosen_response']}"
        )
    return chain.source_capsule_id


def _is_short_imperative(text: str) -> bool:
    lower = text.lower().strip()
    for prefix in ("ok ", "okay "):
        if lower.startswith(prefix):
            lower = lower[len(prefix) :].strip()
    starters = ("fix", "put", "add", "remove", "sync", "launch", "update", "change")
    return len(lower.split()) <= 10 and lower.startswith(starters)


def classify_failure_modes(chain: CorrectionChain) -> list[str]:
    """Classify what the correction implies the assistant got wrong."""
    correction = chain.correction.lower().strip()
    rejected = chain.rejected_response.lower()
    chosen = chain.chosen_response.lower()
    modes: list[str] = []

    if "i asked about" in correction or "asked about" in correction:
        modes.append("context_drift")

    local_markers = ("can you see", "locally", "local", "file", "repo", "uatp")
    if any(marker in correction for marker in local_markers) and not any(
        marker in rejected
        for marker in ("checked", "read", "found", "/", "terminal", "file")
    ):
        modes.append("local_file_blindness")
        modes.append("tool_omission")

    if "no ai slop" in correction or "slop" in correction:
        modes.append("over_formatting_ai_slop")

    rejected_is_long = len(chain.rejected_response) > 800
    deflects = any(
        phrase in rejected
        for phrase in ("i would", "i can", "let me know", "you can", "would approach")
    )
    chosen_acted = any(
        verb in chosen
        for verb in ("fixed", "updated", "added", "removed", "verified", "ran")
    )
    if _is_short_imperative(correction) and (
        rejected_is_long or deflects or chosen_acted
    ):
        modes.append("explanation_instead_of_action")

    if "verify" in correction and "should" in rejected:
        modes.append("unverified_claim")

    if "same" in correction or "again" in correction:
        modes.append("repeated_plan")

    if not modes:
        return ["unknown"]
    return sorted(dict.fromkeys(modes))


def summarize_failure_modes(chains: list[CorrectionChain]) -> dict[str, dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = {}
    for chain in chains:
        for mode in classify_failure_modes(chain):
            if mode == "unknown":
                continue
            bucket = summary.setdefault(
                mode, {"count": 0, "evidence": [], "lesson": lesson_for_mode(mode)}
            )
            bucket["count"] += 1
            if len(bucket["evidence"]) < 5:
                bucket["evidence"].append(
                    {"id": evidence_id(chain), "correction": chain.correction[:160]}
                )
    return dict(sorted(summary.items(), key=lambda item: (-item[1]["count"], item[0])))


def lesson_for_mode(mode: str) -> str:
    lessons = {
        "context_drift": "Re-read the user's original request and pivot back to that context.",
        "explanation_instead_of_action": "When Kay responds to analysis with an imperative fix request, act and verify instead of continuing to explain.",
        "tool_omission": "Use available tools when the missing fact is locally or externally checkable.",
        "local_file_blindness": "When Kay asks whether Hermes can see a local project/file, check the filesystem immediately.",
        "over_formatting_ai_slop": "Strip theatrical framing and produce concrete, understated, production-quality output.",
        "unverified_claim": "Verify configuration and system-state claims with tools before finalizing.",
        "repeated_plan": "Do not repeat a plan after a correction; move to the next concrete action.",
    }
    return lessons.get(mode, "Review the correction before promoting a rule.")
