"""Generate non-mutating learning proposals from capsule correction chains."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from scripts.analysis.hermes_failure_taxonomy import (
    CorrectionChain,
    classify_failure_modes,
    evidence_id,
)

Proposal = dict[str, Any]


def generate_learning_proposals(chains: list[CorrectionChain]) -> list[Proposal]:
    by_mode: dict[str, list[CorrectionChain]] = defaultdict(list)
    for chain in chains:
        for mode in classify_failure_modes(chain):
            if mode != "unknown":
                by_mode[mode].append(chain)

    proposals: list[Proposal] = []

    action_chains = by_mode.get("explanation_instead_of_action", [])
    if len(action_chains) >= 3:
        proposals.append(
            {
                "type": "memory",
                "target": "user",
                "content": "Kay's short imperative corrections after long assistant answers usually refer to the immediately prior output; act on the correction and verify instead of asking what to fix.",
                "evidence": [evidence_id(chain) for chain in action_chains[:5]],
                "risk": "May over-act when multiple recent artifacts exist.",
                "safe_to_apply": False,
            }
        )

    local_chains = by_mode.get("local_file_blindness", [])
    if len(local_chains) >= 2:
        proposals.append(
            {
                "type": "skill_patch",
                "skill": "uatp-capsule-mining",
                "section": "Known Hermes failure modes",
                "patch_summary": "Add local visibility/tool-use miss rule for questions like 'can you see UATP?' and 'it's a file locally'.",
                "evidence": [evidence_id(chain) for chain in local_chains[:5]],
                "risk": "Should not trigger when the target project/file is genuinely unspecified.",
                "safe_to_apply": False,
            }
        )

    slop_chains = by_mode.get("over_formatting_ai_slop", [])
    if len(slop_chains) >= 3:
        proposals.append(
            {
                "type": "memory",
                "target": "user",
                "content": "Kay uses 'no ai slop' to mean concrete, understated, production-quality output without theatrical framing, placeholders, or filler.",
                "evidence": [evidence_id(chain) for chain in slop_chains[:5]],
                "risk": "May under-explain when Kay explicitly asks for detailed rationale.",
                "safe_to_apply": False,
            }
        )

    return proposals
