# Capsule Learning v2: Artifact + Verification Evidence Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Make Hermes/UATP capsules better agent-learning receipts by adding first-class artifact and verification evidence, then expose that evidence in the capsule learning report without mutating live behavior.

**Architecture:** Add an additive v2 evidence layer to the existing Hermes capture payload. Reuse existing redaction, command-artifact, file-artifact, and verification-classification helpers in `src.integrations.hermes.hermes_capture`; do not change the core capsule table schema or raw historical rows. Validate with focused tests first, then one dry-run report proving the new fields improve learning visibility.

**Tech Stack:** Python 3.12 via `./.venv/bin/python`, pytest, SQLite dev DB, Hermes capture plugin, UATP analysis scripts.

---

## Current Context

Inspected touchpoints:

- Hermes capture implementation source: `/Users/kay/.hermes/plugins/uatp-capture/hermes_capture.py`
- In-repo import path used by tests: `/Users/kay/uatp-capsule-engine/src/integrations/hermes/hermes_capture.py`
- Existing command/file artifact helpers:
  - `_extract_file_artifacts()` around plugin lines 298-372
  - `_extract_command_artifacts()` around plugin lines 375-421
  - `_summarize_command_verifications()` around plugin lines 424-445
  - `_classify_verification_command()` around plugin lines 236-295
- Existing agent receipt event layer already emits `ToolCallCompleted`, `ActionTraceEvent`, and `SessionEnded` with `outcome_summary` around plugin lines 900-1015.
- Existing Hermes conversation conversion and signal detection begins around plugin lines 1091-1160.
- Existing eval extraction: `scripts/analysis/build_learning_eval_set.py`
- Existing report: `scripts/analysis/hermes_capsule_learning_report.py`
- Existing failure taxonomy: `scripts/analysis/hermes_failure_taxonomy.py`
- Existing focused tests:
  - `tests/integration/test_hermes_command_artifacts.py`
  - `tests/unit/test_hermes_redaction.py`
  - `tests/analysis/test_hermes_capsule_learning_report.py`
  - `tests/analysis/test_capsule_learning_pipeline_contract.py`

Current issue:

- Capsules already contain transcript steps and some tool-call data, but the learning layer still mostly reasons from correction chains.
- The learner cannot reliably answer: what files changed, what verification ran after the final change, whether the task scope completed, or whether Kay’s standard was actually checked.
- Raw labels still include meta/system contamination, so the improvement must remain additive, read-only for historical analysis, and guarded by tests.

Non-goals for this slice:

- No DB migration.
- No live behavior mutation.
- No raw fine-tuning export.
- No broad visual screenshot storage yet.
- No Claude Code capture refactor yet.

---

## Additive Payload Contract

Add this top-level field to future Hermes capsules when tool invocations are available:

```json
"learning_receipt_v2": {
  "schema_version": "2026-06-04.artifact-verification.v1",
  "artifact_manifest": {
    "files": [],
    "commands": [],
    "tool_frequency": {},
    "tool_call_count": 0
  },
  "verification_evidence": {
    "verification_commands_total": 0,
    "verification_commands_passed": 0,
    "verification_commands_failed": 0,
    "verification_commands_by_type": {},
    "verification_commands_by_status": {},
    "ran_after_last_write": false,
    "last_write_index": null,
    "last_verification_index": null
  },
  "task_intent": {
    "quality_triggers": [],
    "action_directives": [],
    "project_markers": [],
    "requires_visual_qa": false,
    "requires_local_state": false
  },
  "learning_flags": {
    "acted_with_tools": false,
    "modified_artifacts": false,
    "verified_changes": false,
    "verification_after_change": false,
    "possible_explanation_bias": false
  }
}
```

Rules:

- Additive only. Existing fields stay unchanged.
- Store hashes/previews via existing redaction helpers; no raw secrets.
- Prefer relative/home-redacted paths in reports.
- Keep deterministic labels conservative.
- If tool data is missing, emit an empty v2 receipt rather than guessing.

---

## Task 1: Add tests for v2 receipt builder

**Objective:** Define the expected `learning_receipt_v2` shape before implementation.

**Files:**

- Create: `tests/integration/test_hermes_learning_receipt_v2.py`
- Modify later: `src/integrations/hermes/hermes_capture.py`

**Step 1: Create failing test for artifact and verification evidence**

Create `tests/integration/test_hermes_learning_receipt_v2.py`:

```python
from src.integrations.hermes import hermes_capture


def test_learning_receipt_v2_extracts_files_commands_and_verification_order():
    invocations = [
        {
            "tool": "write_file",
            "call_id": "call-write",
            "arguments": {"path": "src/example.py", "content": "print('ok')\n"},
            "result_preview": {"output": "wrote", "exit_code": 0},
            "timestamp": "2026-06-04T08:00:00+00:00",
        },
        {
            "tool": "terminal",
            "call_id": "call-test",
            "arguments": {"command": "./.venv/bin/python -m pytest tests/example -q"},
            "result_preview": {"output": "1 passed", "exit_code": 0},
            "timestamp": "2026-06-04T08:01:00+00:00",
        },
    ]
    messages = [
        {"role": "user", "content": "ok fix it to my standard"},
        {"role": "assistant", "content": "Changed src/example.py and ran tests."},
    ]

    receipt = hermes_capture._build_learning_receipt_v2(invocations, messages)

    assert receipt["schema_version"] == "2026-06-04.artifact-verification.v1"
    assert receipt["artifact_manifest"]["tool_call_count"] == 2
    assert receipt["artifact_manifest"]["files"][0]["operation"] == "write"
    assert receipt["artifact_manifest"]["commands"][0]["verification_type"] == "test"
    assert receipt["verification_evidence"]["verification_commands_total"] == 1
    assert receipt["verification_evidence"]["verification_commands_passed"] == 1
    assert receipt["verification_evidence"]["ran_after_last_write"] is True
    assert receipt["learning_flags"]["modified_artifacts"] is True
    assert receipt["learning_flags"]["verified_changes"] is True
    assert receipt["learning_flags"]["verification_after_change"] is True
    assert "standard" in receipt["task_intent"]["quality_triggers"]
```

**Step 2: Add failing test for no verification after last write**

Append:

```python

def test_learning_receipt_v2_detects_missing_post_change_verification():
    invocations = [
        {
            "tool": "terminal",
            "call_id": "call-test",
            "arguments": {"command": "pytest tests/example -q"},
            "result_preview": {"output": "1 passed", "exit_code": 0},
            "timestamp": "2026-06-04T08:00:00+00:00",
        },
        {
            "tool": "patch",
            "call_id": "call-patch",
            "arguments": {
                "path": "src/example.py",
                "old_string": "old",
                "new_string": "new",
            },
            "result_preview": {"output": "patched", "exit_code": 0},
            "timestamp": "2026-06-04T08:01:00+00:00",
        },
    ]

    receipt = hermes_capture._build_learning_receipt_v2(invocations, [])

    assert receipt["verification_evidence"]["verification_commands_total"] == 1
    assert receipt["verification_evidence"]["ran_after_last_write"] is False
    assert receipt["learning_flags"]["modified_artifacts"] is True
    assert receipt["learning_flags"]["verified_changes"] is True
    assert receipt["learning_flags"]["verification_after_change"] is False
```

**Step 3: Run the tests and verify failure**

Run:

```bash
cd /Users/kay/uatp-capsule-engine
./.venv/bin/python -m pytest tests/integration/test_hermes_learning_receipt_v2.py -q
```

Expected: FAIL because `_build_learning_receipt_v2` does not exist yet.

---

## Task 2: Implement `_build_learning_receipt_v2`

**Objective:** Build the additive receipt from existing tool invocation helpers and user messages.

**Files:**

- Modify: `src/integrations/hermes/hermes_capture.py`
- Test: `tests/integration/test_hermes_learning_receipt_v2.py`

**Step 1: Add constants near artifact helper constants**

Near `_ARTIFACT_PREVIEW_CHARS`, add:

```python
_LEARNING_RECEIPT_V2_SCHEMA = "2026-06-04.artifact-verification.v1"
_QUALITY_TRIGGER_TERMS = (
    "gold standard",
    "no ai slop",
    "no regression",
    "my standard",
    "standard",
)
_ACTION_DIRECTIVE_TERMS = (
    "fix",
    "apply",
    "continue",
    "do it",
    "commit",
    "push",
    "run",
    "test",
    "verify",
)
_PROJECT_MARKER_TERMS = ("uatp", "portfolio", "resume", "residuals", "hermes")
_VISUAL_TERMS = (
    "look at page",
    "screenshot",
    "visual",
    "higher",
    "lower",
    "left",
    "right",
    "border",
    "spacing",
    "from scratch",
)
_LOCAL_STATE_TERMS = ("local", "file", "repo", "can you see", "where is", "path")
```

**Step 2: Add helper for user text aggregation**

```python
def _user_text_from_messages(messages: List[Dict[str, Any]] | None) -> str:
    if not messages:
        return ""
    return "\n".join(
        str(message.get("content") or "")
        for message in messages
        if message.get("role") == "user"
    ).lower()
```

**Step 3: Add helper for deterministic term matching**

```python
def _matched_terms(text: str, terms: tuple[str, ...]) -> List[str]:
    return [term for term in terms if term in text]
```

**Step 4: Add helper for verification order**

```python
def _verification_order_summary(
    file_artifacts: List[Dict[str, Any]],
    command_artifacts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    write_indices = [
        artifact.get("call_id")
        for artifact in file_artifacts
        if artifact.get("operation") in {"write", "patch"}
    ]
    verification_call_ids = [
        command.get("call_id")
        for command in command_artifacts
        if command.get("is_verification") is True
    ]

    # Prefer invocation order when `step_index` exists; fall back to list order.
    last_write_pos = None
    last_verification_pos = None
    ordered_ids = []
    for artifact in file_artifacts:
        ordered_ids.append((artifact.get("call_id"), "file"))
    for command in command_artifacts:
        ordered_ids.append((command.get("call_id"), "command"))

    # The helper above cannot perfectly reconstruct mixed order after extraction,
    # so Task 2 Step 5 will compute exact order from raw invocations. This fallback
    # is intentionally conservative.
    if not write_indices:
        return {
            "ran_after_last_write": bool(verification_call_ids),
            "last_write_index": None,
            "last_verification_index": None,
        }
    return {
        "ran_after_last_write": False,
        "last_write_index": None,
        "last_verification_index": None,
    }
```

Do not stop here; this fallback is not enough for the tests. Implement exact ordering in the main builder from raw invocation indices.

**Step 5: Add `_build_learning_receipt_v2`**

```python
def _build_learning_receipt_v2(
    tool_invocations: List[Dict[str, Any]] | None,
    messages: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    invocations = tool_invocations or []
    file_artifacts = _extract_file_artifacts(invocations)
    command_artifacts = _extract_command_artifacts(invocations)
    verification_summary = _summarize_command_verifications(command_artifacts)

    last_write_index = None
    last_verification_index = None
    for index, invocation in enumerate(invocations):
        tool = invocation.get("tool")
        if tool in _FILE_WRITE_TOOLS | _FILE_PATCH_TOOLS:
            last_write_index = index
        if tool in _COMMAND_TOOLS:
            args = _parse_args(invocation.get("arguments")) or {}
            parsed_result = _parse_tool_result(invocation.get("result_preview"))
            command = args.get("command") or ""
            output = parsed_result.get("output") or parsed_result.get("stdout") or ""
            verification = _classify_verification_command(
                command,
                parsed_result.get("exit_code"),
                output if isinstance(output, str) else str(output),
            )
            if verification.get("is_verification") is True:
                last_verification_index = index

    ran_after_last_write = (
        last_verification_index is not None
        and (last_write_index is None or last_verification_index > last_write_index)
    )

    user_text = _user_text_from_messages(messages)
    task_intent = {
        "quality_triggers": _matched_terms(user_text, _QUALITY_TRIGGER_TERMS),
        "action_directives": _matched_terms(user_text, _ACTION_DIRECTIVE_TERMS),
        "project_markers": _matched_terms(user_text, _PROJECT_MARKER_TERMS),
        "requires_visual_qa": bool(_matched_terms(user_text, _VISUAL_TERMS)),
        "requires_local_state": bool(_matched_terms(user_text, _LOCAL_STATE_TERMS)),
    }

    modified_artifacts = any(
        artifact.get("operation") in {"write", "patch"} for artifact in file_artifacts
    )
    verified_changes = verification_summary["verification_commands_total"] > 0

    return {
        "schema_version": _LEARNING_RECEIPT_V2_SCHEMA,
        "artifact_manifest": {
            "files": file_artifacts,
            "commands": command_artifacts,
            "tool_frequency": dict(
                Counter(
                    invocation.get("tool")
                    for invocation in invocations
                    if invocation.get("tool")
                ).most_common()
            ),
            "tool_call_count": len(invocations),
        },
        "verification_evidence": {
            **verification_summary,
            "ran_after_last_write": ran_after_last_write,
            "last_write_index": last_write_index,
            "last_verification_index": last_verification_index,
        },
        "task_intent": task_intent,
        "learning_flags": {
            "acted_with_tools": bool(invocations),
            "modified_artifacts": modified_artifacts,
            "verified_changes": verified_changes,
            "verification_after_change": bool(modified_artifacts and ran_after_last_write),
            "possible_explanation_bias": bool(
                task_intent["action_directives"] and not invocations
            ),
        },
    }
```

**Step 6: Run focused test**

Run:

```bash
cd /Users/kay/uatp-capsule-engine
./.venv/bin/python -m pytest tests/integration/test_hermes_learning_receipt_v2.py -q
```

Expected: PASS.

---

## Task 3: Inject v2 receipt into future Hermes capsules

**Objective:** Add `learning_receipt_v2` to the capsule payload when the capture path has tool invocation data.

**Files:**

- Modify: `src/integrations/hermes/hermes_capture.py`
- Test: existing/new integration tests depending on available helper boundaries

**Step 1: Locate existing capsule payload enrichment path**

Use the existing tool-call injection/enrichment path. The plugin already has places where it builds or injects:

- `tool_call_graph`
- `economics`
- `artifacts`
- command/file artifacts

Search exact location before editing:

```bash
cd /Users/kay/uatp-capsule-engine
python - <<'PY'
from pathlib import Path
p = Path('src/integrations/hermes/hermes_capture.py')
for i, line in enumerate(p.read_text().splitlines(), 1):
    if 'tool_call_graph' in line or 'payload[' in line and 'artifacts' in line:
        print(i, line)
PY
```

**Step 2: Add receipt beside `tool_call_graph`**

Where `payload["tool_call_graph"]` is assigned, add:

```python
payload["learning_receipt_v2"] = _build_learning_receipt_v2(
    tool_graph_raw,
    session_data.get("messages") or [],
)
```

If that path does not have full `messages`, pass an empty list and add a follow-up task to thread messages into `session_data`. Do not fake task intent.

**Step 3: Add regression test for injection helper if one exists**

If there is an existing test for payload enrichment, extend it to assert:

```python
assert payload["learning_receipt_v2"]["schema_version"] == "2026-06-04.artifact-verification.v1"
assert "artifact_manifest" in payload["learning_receipt_v2"]
assert "verification_evidence" in payload["learning_receipt_v2"]
```

If no seam exists, do not overbuild a fake DB integration yet. Rely on Task 2 helper tests and Task 7 live dry-run capture verification.

**Step 4: Run focused tests**

Run:

```bash
cd /Users/kay/uatp-capsule-engine
./.venv/bin/python -m pytest tests/integration/test_hermes_learning_receipt_v2.py tests/integration/test_hermes_command_artifacts.py tests/unit/test_hermes_redaction.py -q
```

Expected: PASS.

---

## Task 4: Extend eval records with evidence when present

**Objective:** Preserve `learning_receipt_v2` evidence in clean eval records so behavior evaluation can use it.

**Files:**

- Modify: `scripts/analysis/build_learning_eval_set.py`
- Test: `tests/analysis/test_capsule_learning_pipeline_contract.py` or new `tests/analysis/test_build_learning_eval_set_receipt_v2.py`

**Step 1: Add failing test**

Create `tests/analysis/test_build_learning_eval_set_receipt_v2.py`:

```python
from scripts.analysis.build_learning_eval_set import extract_eval_records


def test_eval_record_includes_learning_receipt_v2_evidence():
    capsule = {
        "capsule_id": "caps_test",
        "capsule_type": "hermes-capture",
        "payload": {
            "model_used": "assistant:test",
            "learning_receipt_v2": {
                "schema_version": "2026-06-04.artifact-verification.v1",
                "verification_evidence": {"verification_commands_total": 1},
                "learning_flags": {"verification_after_change": True},
            },
            "reasoning_steps": [
                {"role": "user", "reasoning": "fix it"},
                {"role": "assistant", "reasoning": "I can explain."},
                {
                    "role": "user",
                    "reasoning": "ok fix it",
                    "measurements": {"signal_type": "correction"},
                },
                {"role": "assistant", "reasoning": "Fixed and tested."},
            ],
        },
    }

    records = extract_eval_records([capsule])

    assert len(records) == 1
    assert records[0]["evidence"]["learning_receipt_v2_schema"] == "2026-06-04.artifact-verification.v1"
    assert records[0]["evidence"]["verification_commands_total"] == 1
    assert records[0]["evidence"]["verification_after_change"] is True
```

**Step 2: Run and verify failure**

```bash
cd /Users/kay/uatp-capsule-engine
./.venv/bin/python -m pytest tests/analysis/test_build_learning_eval_set_receipt_v2.py -q
```

Expected: FAIL because evidence is not copied yet.

**Step 3: Modify `_build_record` in `scripts/analysis/build_learning_eval_set.py`**

Inside `_build_record`, before return:

```python
    receipt_v2 = payload.get("learning_receipt_v2") or {}
    verification_evidence = receipt_v2.get("verification_evidence") or {}
    learning_flags = receipt_v2.get("learning_flags") or {}
    evidence = {
        "text_field_priority": "reasoning,content",
        "signal_path": signal_path(correction_step),
    }
    if receipt_v2:
        evidence.update(
            {
                "learning_receipt_v2_schema": receipt_v2.get("schema_version"),
                "verification_commands_total": verification_evidence.get(
                    "verification_commands_total", 0
                ),
                "verification_after_change": learning_flags.get(
                    "verification_after_change", False
                ),
            }
        )
```

Then replace the existing literal `"evidence": {...}` with `"evidence": evidence`.

**Step 4: Run focused test**

```bash
cd /Users/kay/uatp-capsule-engine
./.venv/bin/python -m pytest tests/analysis/test_build_learning_eval_set_receipt_v2.py -q
```

Expected: PASS.

---

## Task 5: Add report section for receipt coverage and verification quality

**Objective:** Make the one-command learning report show whether capsule data quality improved.

**Files:**

- Modify: `scripts/analysis/hermes_capsule_learning_report.py`
- Test: `tests/analysis/test_hermes_capsule_learning_report.py`

**Step 1: Add summary helper**

In `hermes_capsule_learning_report.py`, add a helper near other report summarizers:

```python
def summarize_learning_receipt_v2(records: list[dict[str, Any]]) -> dict[str, Any]:
    with_receipt = 0
    with_verification = 0
    with_post_change_verification = 0
    for record in records:
        evidence = record.get("evidence") or {}
        if evidence.get("learning_receipt_v2_schema"):
            with_receipt += 1
        if int(evidence.get("verification_commands_total") or 0) > 0:
            with_verification += 1
        if evidence.get("verification_after_change") is True:
            with_post_change_verification += 1
    return {
        "records_total": len(records),
        "records_with_learning_receipt_v2": with_receipt,
        "records_with_verification": with_verification,
        "records_with_post_change_verification": with_post_change_verification,
    }
```

**Step 2: Include it in `build_report_payload`**

Add:

```python
"learning_receipt_v2": summarize_learning_receipt_v2(records),
```

near `token_waste`, `tool_misses`, and `proposals`.

**Step 3: Render it in Markdown**

In `render_markdown`, add a section after Data Inventory or Signal Health:

```python
receipt_v2 = payload.get("learning_receipt_v2", {})
lines.extend(
    [
        "",
        "## Learning Receipt v2 Coverage",
        "",
        f"records_total: {receipt_v2.get('records_total', 0)}",
        f"records_with_learning_receipt_v2: {receipt_v2.get('records_with_learning_receipt_v2', 0)}",
        f"records_with_verification: {receipt_v2.get('records_with_verification', 0)}",
        f"records_with_post_change_verification: {receipt_v2.get('records_with_post_change_verification', 0)}",
    ]
)
```

**Step 4: Add/adjust test**

In `tests/analysis/test_hermes_capsule_learning_report.py`, add a focused unit test for `summarize_learning_receipt_v2`.

Expected assertions:

```python
assert summary["records_total"] == 2
assert summary["records_with_learning_receipt_v2"] == 1
assert summary["records_with_verification"] == 1
assert summary["records_with_post_change_verification"] == 1
```

**Step 5: Run focused report tests**

```bash
cd /Users/kay/uatp-capsule-engine
./.venv/bin/python -m pytest tests/analysis/test_hermes_capsule_learning_report.py tests/analysis/test_build_learning_eval_set_receipt_v2.py -q
```

Expected: PASS.

---

## Task 6: Add safety tests for no secret/path leaks in receipt reports

**Objective:** Keep richer artifact evidence from leaking secrets or machine-specific paths into tracked reports.

**Files:**

- Modify or create: `tests/integration/test_hermes_learning_receipt_v2.py`
- Modify if needed: `src/integrations/hermes/hermes_capture.py`
- Existing redaction reference: `tests/unit/test_hermes_redaction.py`

**Step 1: Add test for secret redaction in command output**

```python

def test_learning_receipt_v2_redacts_command_output_secrets():
    invocations = [
        {
            "tool": "terminal",
            "call_id": "call-secret",
            "arguments": {"command": "printenv"},
            "result_preview": {"output": "OPENAI_API_KEY=sk-secret123456789", "exit_code": 0},
        }
    ]

    receipt = hermes_capture._build_learning_receipt_v2(invocations, [])
    preview = receipt["artifact_manifest"]["commands"][0]["stdout_preview"]

    assert "sk-secret123456789" not in preview
    assert "[REDACTED" in preview
```

**Step 2: Add report redaction check if report includes paths**

If Markdown rendering includes file paths from receipt v2, assert it passes `redact_report_text` or only uses existing redacted paths.

Do not expose `/Users/kay/...` in tracked generated reports unless explicitly intended as local-only untracked artifacts.

**Step 3: Run focused tests**

```bash
cd /Users/kay/uatp-capsule-engine
./.venv/bin/python -m pytest tests/integration/test_hermes_learning_receipt_v2.py tests/unit/test_hermes_redaction.py -q
```

Expected: PASS.

---

## Task 7: Generate dry-run report and prove improved visibility

**Objective:** Produce evidence that the new learning layer improves reports without promoting live behavior.

**Files:**

- Generated/local: `docs/reports/hermes_capsule_learning_report.md`
- No DB mutation.

**Step 1: Run focused tests**

```bash
cd /Users/kay/uatp-capsule-engine
./.venv/bin/python -m pytest \
  tests/integration/test_hermes_learning_receipt_v2.py \
  tests/integration/test_hermes_command_artifacts.py \
  tests/unit/test_hermes_redaction.py \
  tests/analysis/test_build_learning_eval_set_receipt_v2.py \
  tests/analysis/test_hermes_capsule_learning_report.py \
  -q
```

Expected: PASS.

**Step 2: Run full capsule learning report dry-run**

```bash
cd /Users/kay/uatp-capsule-engine
./.venv/bin/python scripts/analysis/hermes_capsule_learning_report.py --json --dry-run
```

Expected:

- `safe_to_promote_live: false`
- `learning_receipt_v2.records_total` present
- Existing clean eval record count unchanged unless current DB changed naturally
- No crash on capsules lacking receipt v2

**Step 3: Generate Markdown report**

```bash
cd /Users/kay/uatp-capsule-engine
./.venv/bin/python scripts/analysis/hermes_capsule_learning_report.py --output docs/reports/hermes_capsule_learning_report.md --dry-run
```

Expected:

- Markdown contains `## Learning Receipt v2 Coverage`
- No raw secrets
- No new public absolute local-path leak

**Step 4: Check report for local path leak**

```bash
cd /Users/kay/uatp-capsule-engine
if grep -n "/Users/kay" docs/reports/hermes_capsule_learning_report.md; then
  echo "LOCAL PATH LEAK"
  exit 1
fi
```

Expected: no output, exit 0.

---

## Task 8: Final no-regression gate

**Objective:** Verify this slice meets Kay’s standard before any commit/push.

**Files:** all changed files.

**Step 1: Run focused tests**

```bash
cd /Users/kay/uatp-capsule-engine
./.venv/bin/python -m pytest \
  tests/integration/test_hermes_learning_receipt_v2.py \
  tests/integration/test_hermes_command_artifacts.py \
  tests/unit/test_hermes_redaction.py \
  tests/analysis/test_build_learning_eval_set_receipt_v2.py \
  tests/analysis/test_hermes_capsule_learning_report.py \
  tests/analysis/test_capsule_learning_pipeline_contract.py \
  -q
```

Expected: PASS.

**Step 2: Run formatter/lint if configured**

Use the project’s existing commands if present. Start with:

```bash
cd /Users/kay/uatp-capsule-engine
./.venv/bin/python -m ruff check scripts/analysis tests/analysis tests/integration tests/unit src/integrations/hermes -q
```

Expected: PASS or only pre-existing unrelated failures. If ruff is unavailable, record that explicitly.

**Step 3: Run git diff check**

```bash
cd /Users/kay/uatp-capsule-engine
git diff --check
```

Expected: no whitespace errors.

**Step 4: Review changed files**

```bash
cd /Users/kay/uatp-capsule-engine
git diff -- src/integrations/hermes/hermes_capture.py scripts/analysis/build_learning_eval_set.py scripts/analysis/hermes_capsule_learning_report.py tests/integration/test_hermes_learning_receipt_v2.py tests/analysis/test_build_learning_eval_set_receipt_v2.py tests/analysis/test_hermes_capsule_learning_report.py
```

Review for:

- Additive v2 payload only
- No raw DB writes
- No live behavior promotion
- No broad unrelated refactors
- No secret/path leakage
- No fake outcome labels

**Step 5: Commit only after verification**

If Kay wants commit/push:

```bash
cd /Users/kay/uatp-capsule-engine
git status --short
git add src/integrations/hermes/hermes_capture.py \
  scripts/analysis/build_learning_eval_set.py \
  scripts/analysis/hermes_capsule_learning_report.py \
  tests/integration/test_hermes_learning_receipt_v2.py \
  tests/analysis/test_build_learning_eval_set_receipt_v2.py \
  tests/analysis/test_hermes_capsule_learning_report.py
git commit -m "feat: add Hermes learning receipt v2 evidence"
```

Do not include generated JSONL or DB backups.

---

## Risks and Guardrails

1. **Plugin/profile path mismatch**

Tests import `src.integrations.hermes.hermes_capture`, but the active plugin lives at `/Users/kay/.hermes/plugins/uatp-capture/hermes_capture.py`. Confirm whether these are synced before final implementation. If not, patch the in-repo source first and then intentionally sync to plugin path only after tests pass.

2. **Ordering bug**

Extracted file/command artifacts lose mixed invocation order. Compute `ran_after_last_write` from raw `tool_invocations`, not from extracted artifacts.

3. **False certainty**

Do not infer `task_completed` or `user_satisfied` in this slice. Those need explicit outcome labels or delayed correction links later.

4. **Privacy**

Do not store raw screenshots or raw command output in reports. Use redacted previews, hashes, and content-addressed refs.

5. **Historical backfill**

Do not rewrite historical capsules yet. First add capture for future capsules and reporting support for mixed old/new data.

---

## Follow-up Slices After This Plan

1. **Outcome Summary v2**

Add `outcome_summary_v2` with `task_completed`, `final_status`, `blocked_reason`, and `user_had_to_repeat_self` — but only where evidence supports it.

2. **Correction Target Classifier**

Add deterministic `correction_target` labels to eval records using `hermes_failure_taxonomy.py`, then expand taxonomy with visual/prose/regression/incomplete-scope labels.

3. **Visual QA Receipt**

For browser/frontend work, capture screenshot refs, viewport, URL/file, console errors, and visual-check status.

4. **Delayed Outcome Links**

Link later corrections to earlier capsules by artifact path/session lineage.

---

## Definition of Done

This slice is done when:

- New tests fail before implementation and pass after.
- Future Hermes capsules can include `learning_receipt_v2` without breaking old capsules.
- Eval records preserve receipt evidence when present.
- Learning report shows receipt coverage.
- Dry-run report remains safe_to_promote_live false.
- No DB mutation occurs during reporting.
- Redaction tests pass.
- Focused tests pass using `./.venv/bin/python`.
- Final response reports exact tests and files changed, with no “gold standard achieved” theater.
