"""Deterministic tool-decision analysis for Hermes correction chains."""

from __future__ import annotations

from dataclasses import dataclass, field

from scripts.analysis.hermes_failure_taxonomy import CorrectionChain, evidence_id


@dataclass(frozen=True)
class ToolDecisionResult:
    labels: list[str] = field(default_factory=list)


def analyze_tool_decisions(chain: CorrectionChain) -> ToolDecisionResult:
    correction = (chain.correction or "").lower()
    prompt = (chain.prompt or "").lower()
    rejected = (chain.rejected_response or "").lower()
    labels: list[str] = []

    local_request = any(
        marker in correction
        for marker in ("can you see", "locally", "local", "file", "repo", "uatp")
    )
    no_tool_evidence = not any(
        marker in rejected
        for marker in (
            "checked",
            "read_file",
            "search_files",
            "terminal",
            "found",
            "ls",
            "stat",
        )
    )
    if local_request and no_tool_evidence:
        labels.extend(["should_have_used_file_tool", "should_have_used_terminal"])

    if "verify" in correction and any(
        marker in rejected
        for marker in ("should take effect", "takes effect", "should work")
    ):
        labels.append("should_have_verified_after_config_change")

    if "which machine" in rejected and any(
        marker in prompt for marker in ("port", "os", "time", "date", "running")
    ):
        labels.append("asked_when_obvious_default_existed")

    return ToolDecisionResult(labels=sorted(dict.fromkeys(labels)))


def summarize_tool_decisions(
    chains: list[CorrectionChain],
) -> dict[str, dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}
    lessons = {
        "should_have_used_file_tool": "When Kay asks whether Hermes can see a local project/file, check the filesystem immediately.",
        "should_have_used_terminal": "Use terminal for live local system state instead of answering abstractly.",
        "should_have_verified_after_config_change": "After config changes, verify with a command or status check before finalizing.",
        "asked_when_obvious_default_existed": "Use the obvious default local machine when Kay asks about system state unless scope truly changes the tool call.",
    }
    for chain in chains:
        for label in analyze_tool_decisions(chain).labels:
            bucket = summary.setdefault(
                label, {"count": 0, "evidence": [], "lesson": lessons[label]}
            )
            bucket["count"] += 1
            if len(bucket["evidence"]) < 5:
                bucket["evidence"].append(
                    {"id": evidence_id(chain), "correction": chain.correction[:160]}
                )
    return dict(sorted(summary.items(), key=lambda item: (-item[1]["count"], item[0])))
