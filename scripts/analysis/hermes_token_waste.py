"""Token waste and repetition heuristics for Hermes capsule chains."""

from __future__ import annotations

from dataclasses import dataclass, field

from scripts.analysis.hermes_failure_taxonomy import CorrectionChain

DEFLECTION_PHRASES = ("I would", "I can", "let me know if", "Here's a comprehensive")
SHIPPED_SLOP_PATTERNS = (
    "TODO:",
    "placeholder implementation",
    "stub response",
    "dummy data",
    "fake data",
    "mock response",
)


@dataclass(frozen=True)
class TokenWasteResult:
    flags: list[str] = field(default_factory=list)
    estimated_wasted_tokens: int = 0
    repeated_or_deflection_phrases: list[str] = field(default_factory=list)


def _mentions_removed_slop(text: str, pattern: str) -> bool:
    lower = text.lower()
    return pattern.lower() in lower and any(
        verb in lower
        for verb in ("removed", "delete", "deleted", "replaced", "cleaned")
    )


def analyze_token_waste(chain: CorrectionChain) -> TokenWasteResult:
    flags: list[str] = []
    phrases: list[str] = []
    rejected = chain.rejected_response or ""
    correction = chain.correction or ""
    chosen = (chain.chosen_response or "").lower()

    if len(rejected) > 1500 and len(correction) < 80:
        flags.append("long_answer_short_correction")

    for phrase in DEFLECTION_PHRASES:
        if phrase.lower() in rejected.lower():
            phrases.append(phrase)
    chosen_acted = any(
        verb in chosen
        for verb in ("fixed", "updated", "added", "removed", "verified", "ran")
    )
    if phrases and chosen_acted:
        flags.append("deflection_tokens")

    for pattern in SHIPPED_SLOP_PATTERNS:
        if pattern.lower() in rejected.lower() and not _mentions_removed_slop(
            rejected, pattern
        ):
            flags.append("shipped_slop_tokens")
            break

    wasted_chars = len(rejected) if flags else 0
    return TokenWasteResult(
        flags=sorted(dict.fromkeys(flags)),
        estimated_wasted_tokens=max(0, wasted_chars // 4),
        repeated_or_deflection_phrases=phrases,
    )


def summarize_token_waste(chains: list[CorrectionChain]) -> dict[str, object]:
    long_short = 0
    wasted = 0
    phrase_counts: dict[str, int] = {}
    evidence: list[dict[str, str]] = []
    for chain in chains:
        result = analyze_token_waste(chain)
        if "long_answer_short_correction" in result.flags:
            long_short += 1
        wasted += result.estimated_wasted_tokens
        for phrase in result.repeated_or_deflection_phrases:
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        if result.flags and len(evidence) < 5:
            from scripts.analysis.hermes_failure_taxonomy import evidence_id

            evidence.append(
                {"id": evidence_id(chain), "flags": ", ".join(result.flags)}
            )
    return {
        "long_answer_short_correction": long_short,
        "estimated_wasted_tokens": wasted,
        "phrases": dict(
            sorted(phrase_counts.items(), key=lambda item: (-item[1], item[0]))
        ),
        "evidence": evidence,
    }
