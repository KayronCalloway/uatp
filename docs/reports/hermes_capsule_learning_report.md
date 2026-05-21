# Hermes Capsule Learning Report

## Summary Verdict

safe_to_promote_live: false
dry_run: true
Insufficient data for live behavior promotion.

## Data Inventory

Capsules total: 2242
Hermes capsules: 137
Hermes steps: 1169
Clean eval records: 8

## Signal Health

User signals: `{"acceptance": 41, "correction": 15, "neutral": 286, "refinement": 1}`
Meta contamination count: 0
Clean correction chains: 8
Minimum chains for behavior rules: 50
safe_for_behavior_rules: false

## Clean Correction Chains

Records: 8
Signals: `{"correction": 8}`
safe_to_finetune_raw: false

## Behavioral Failure Modes

### explanation_instead_of_action — 2 examples
Lesson: When Kay responds to analysis with an imperative fix request, act and verify instead of continuing to explain.
Evidence:
- caps_2026_04_08_032823_20260407:31-32-48-49: `fix that`
- caps_2026_04_27_190156_20260427:21-22-23-24: `ok fix it`

### context_drift — 1 examples
Lesson: Re-read the user's original request and pivot back to that context.
Evidence:
- caps_2026_04_08_032823_20260407:7-8-12-13: `i asked about uatp`

### over_formatting_ai_slop — 1 examples
Lesson: Strip theatrical framing and produce concrete, understated, production-quality output.
Evidence:
- caps_2026_04_10_044732_20260409:24-25-34-35: `no ai slop`

## Token Waste / Repetition

Long answer followed by short correction: 2
Estimated wasted tokens: 1000
Deflection phrases: `{"I can": 1}`
Evidence:
- caps_2026_04_27_190156_20260427:21-22-23-24: long_answer_short_correction
- caps_2026_05_06_170346_20260506:0-2-3-4: long_answer_short_correction

## Tool-Use Misses

### should_have_used_file_tool — 2 examples
Lesson: When Kay asks whether Hermes can see a local project/file, check the filesystem immediately.
- caps_2026_04_08_032823_20260407:7-8-12-13: `i asked about uatp`
- caps_2026_04_08_032823_20260407:12-13-15-16: `its a file locally`

### should_have_used_terminal — 2 examples
Lesson: Use terminal for live local system state instead of answering abstractly.
- caps_2026_04_08_032823_20260407:7-8-12-13: `i asked about uatp`
- caps_2026_04_08_032823_20260407:12-13-15-16: `its a file locally`

## Proposed Memory / Skill Diffs

No proposal met the evidence threshold. No memory or skill changes should be applied.

## Eval and Benchmark Results

Promotion gate: `{"baseline_pass_rate": 0.0, "beats_baseline": true, "safe_to_promote_live": false, "winner": "oracle_chosen", "winner_pass_rate": 1.0}`
Ranking:
- oracle_chosen: pass_rate=1.0 passed=8 failed=0
- concise_action_bias: pass_rate=1.0 passed=8 failed=0
- overexplainer_negative_control: pass_rate=0.75 passed=6 failed=2
- baseline_rejected: pass_rate=0.0 passed=0 failed=8

## Next Actions

- Do not promote live behavior until signal contamination is zero and clean correction-chain thresholds pass.
- Review proposed memory/skill diffs manually before applying any durable change.
- Keep raw fine-tuning disabled until a separate data-card gate exists.
