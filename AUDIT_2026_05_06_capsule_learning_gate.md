# Capsule Learning Gate Audit — 2026-05-06

## Purpose

This manifest records the no-regression capsule-learning gate added for Hermes/UATP capsule data. The goal is to let Hermes learn from cleaned evidence without directly mutating live behavior, training on raw capsules, or trusting noisy self-reflection.

## Safety boundary

- safe_to_finetune_raw: false
- safe_to_promote_live: false
- safe_for_behavior_eval: true
- No schema migrations were added.
- No live Hermes behavior was changed.
- No model fine-tuning was run.
- No LLM-as-judge path was introduced.
- The only DB write in this workstream was the bounded historical Hermes rescore already backed up below.

## DB backup and bounded rescore

Backup created before applying historical rescore:

uatp_dev.db.backup.20260506_084405

Applied rescore command used before this public gate made dry-run the default:

```bash
PYTHONPATH=. .venv/bin/python scripts/analysis/rescore_hermes_capsules.py --apply
```

Applied rescore result:

- Updated 7 / 60 Hermes capsules
- requery -> neutral: 5
- correction -> neutral: 2
- neutral -> correction: 1

Final dry-run after DB write:

- Would update 0 / 60 capsules
- No signal transitions

## Added / changed analysis files

Added:

- scripts/analysis/capsule_learning_audit.py
- scripts/analysis/build_learning_eval_set.py
- scripts/analysis/run_capsule_behavior_eval.py
- scripts/analysis/generate_behavior_policy_candidates.py
- tests/analysis/test_rescore_hermes_capsules.py
- tests/analysis/test_build_learning_eval_set.py
- tests/analysis/test_run_capsule_behavior_eval.py
- tests/analysis/test_generate_behavior_policy_candidates.py
- tests/analysis/test_capsule_learning_pipeline_contract.py
- AUDIT_2026_05_06_capsule_learning_gate.md

Patched existing untracked script:

- scripts/analysis/rescore_hermes_capsules.py

Plan files created under docs/plans are intentionally gitignored.
Generated JSONL files under scripts/analysis are intentionally gitignored.

## Final audit snapshot

Final capsule audit after rescore:

- capsules_total: 1883
- hermes_capsules: 60
- hermes_steps_total: 637
- user_signal_counts: acceptance 21, correction 11, neutral 151, refinement 1
- meta_signal_counts: neutral 34
- approx_negative_chains: 11
- user_non_neutral_rate: 0.1793
- safe_to_finetune_raw: false
- safe_to_use_for_behavioral_rules: true

## Held-out eval set

Generated held-out eval JSONL:

scripts/analysis/hermes_learning_eval_set.jsonl

Ignored by git via scripts/analysis/*.jsonl.

Eval-set summary:

- records: 5
- capsule_type: hermes-capture only
- correction_signal: correction only
- no context compaction / task preservation / model-switch meta messages in required text fields
- safe_for_behavior_eval: true
- safe_to_finetune_raw: false

## Behavior eval runner

Deterministic runner:

scripts/analysis/run_capsule_behavior_eval.py

It checks candidate responses against held-out correction-chain records. It does not call an LLM and does not write to DB.

Oracle chosen-response smoke test:

- total: 5
- passed: 5
- failed: 0
- pass_rate: 1.0
- unknown_candidates: 0

## Policy candidate benchmark

Deterministic benchmark:

scripts/analysis/generate_behavior_policy_candidates.py

Variants:

- baseline_rejected
- oracle_chosen
- concise_action_bias
- overexplainer_negative_control

Final benchmark summary from /tmp/capsule_policy_benchmark.json:

1. oracle_chosen
   - passed: 5
   - failed: 0
   - pass_rate: 1.0

2. concise_action_bias
   - passed: 5
   - failed: 0
   - pass_rate: 1.0

3. overexplainer_negative_control
   - passed: 4
   - failed: 1
   - pass_rate: 0.8

4. baseline_rejected
   - passed: 0
   - failed: 5
   - pass_rate: 0.0

Promotion gate:

- winner: oracle_chosen
- baseline_pass_rate: 0.0
- winner_pass_rate: 1.0
- beats_baseline: true
- safe_to_promote_live: false

## Verification evidence

Final targeted verification passed:

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/analysis/test_generate_behavior_policy_candidates.py -q
# 6 passed

PYTHONPATH=. .venv/bin/python -m pytest tests/analysis/test_run_capsule_behavior_eval.py -q
# 8 passed

PYTHONPATH=. .venv/bin/python -m pytest tests/analysis/test_build_learning_eval_set.py -q
# 7 passed

PYTHONPATH=. .venv/bin/python -m pytest tests/analysis/test_rescore_hermes_capsules.py -q
# 5 passed

PYTHONPATH=. .venv/bin/python -m pytest tests/unit/test_signal_detector.py -q
# 46 passed

.venv/bin/python -m ruff check scripts/analysis/generate_behavior_policy_candidates.py tests/analysis/test_generate_behavior_policy_candidates.py scripts/analysis/run_capsule_behavior_eval.py tests/analysis/test_run_capsule_behavior_eval.py
# All checks passed

.venv/bin/python -m py_compile scripts/analysis/generate_behavior_policy_candidates.py scripts/analysis/run_capsule_behavior_eval.py scripts/analysis/build_learning_eval_set.py scripts/analysis/capsule_learning_audit.py scripts/analysis/rescore_hermes_capsules.py scripts/analysis/extract_dpo_pairs.py
# Passed

PYTHONPATH=. .venv/bin/python scripts/analysis/extract_dpo_pairs.py
# Correction chains: 723
# Labeled singles: 1287
# Total pairs: 2010
# Capsules used: 114
```

The stabilization slice also adds a synthetic pipeline contract test proving:

- meta/system messages are neutralized;
- short `ok fix it` after a long assistant response becomes correction;
- eval record evidence fields stay stable;
- baseline rejected candidate fails;
- oracle chosen candidate passes;
- policy benchmark beats baseline;
- no DB access is needed for the contract test.

## Rollback

To roll back only this gate work, remove the added analysis/test/manifest files listed above. To roll back the historical DB rescore, restore:

uatp_dev.db.backup.20260506_084405

## Remaining limits

- The held-out Hermes eval set is small: 5 records.
- It currently contains correction cases only, not enough requery/refinement coverage.
- Raw DPO/fine-tuning remains unsafe.
- Live Hermes behavior should not be changed until a human-readable policy patch is reviewed and this gate is kept passing.
