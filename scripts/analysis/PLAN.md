# UATP Capsule Intelligence — Implementation Plan

## Data Landscape
- 1789 capsules across 8 types
- 5604 reasoning steps (2887 user, 2705 assistant)
- Models: Claude (Opus/Sonnet via Claude Code + Hermes), Gemma4 (Ollama local)
- 90 capsules with >2 reasoning steps (usable conversation pairs)
- 101 capsules with feedback signals
- 1 capsule with full enrichment (hermes-capture)

## 1. Absence Detection (signal_detector.py)

Add a new signal type: `soft_rejection`. Fires when:
- User's message ignores the assistant's response entirely (no reference words)
- User immediately changes topic after a long assistant response
- User sends a new directive without acknowledging (no yes/thanks/ok/good)
- Short delay pattern: quick follow-up = didn't even read it

Implementation: compare current user message against previous assistant
response. If zero content overlap AND no acceptance phrases AND the
assistant response was substantial (>200 chars), flag as soft_rejection.

## 2. Cross-Model Comparison (scripts/analysis/cross_model_report.py)

Query capsules grouped by model. For each model compute:
- Correction rate (from signal detection)
- Acceptance rate
- Average confidence
- Average thinking-to-response ratio
- Token efficiency (output quality per token)
- Tool call patterns

Output: plain text report + JSON for programmatic use.

## 3. DPO Training Dataset (scripts/analysis/extract_dpo_pairs.py)

Extract preference pairs from capsules:
- CHOSEN: assistant response followed by user acceptance
- REJECTED: assistant response followed by user correction
- Include the thinking/reasoning as chain-of-thought
- Format: JSONL compatible with TRL/Axolotl DPO trainers

Each row: {prompt, chosen, rejected, chosen_thinking, rejected_thinking}

## 4. Tool Call Sequence Analysis (scripts/analysis/tool_patterns.py)

Extract tool call sequences from capsules with tool_call_graph.
Find common patterns (n-grams of tool sequences).
Identify which sequences lead to acceptances vs corrections.
Output: pattern report + recommended sequences.

## 5. Proxy Standalone Packaging (scripts/proxy/)

Make ollama_proxy.py runnable as a standalone package without
the full UATP codebase. Bundle minimal signing, minimal capsule
storage, zero heavy dependencies.
