# Agent Receipts Schema Map

Captured: 2026-05-08

Purpose: Phase 0.2 inventory of existing UATP 7.4 agent-execution schema support before adding the framework-neutral agent receipt layer.

## Executive Summary

The existing UATP repo already has first-class UATP 7.4 capsule types and SQLite tables for the core agent receipt concepts:

- `AGENT_SESSION`
- `TOOL_CALL`
- `ACTION_TRACE`
- `DECISION_POINT`
- `ENVIRONMENT_SNAPSHOT`

This confirms the earlier architectural judgment: the gap is not the top-level schema idea. The gap is event-native capture, adapter boundaries, deterministic receipt hashing, signing policy, artifact refs, chain verification, skill/memory provenance, and portable bundle verification.

Do not invent a Hermes-only schema. Build an agent-receipt event layer that maps into these existing types.

## Source Files Inspected

- `src/capsule_schema.py`
- SQLite dev DB: `./uatp_dev.db`

Important code locations:

- `src/capsule_schema.py:85-90` defines the UATP 7.4 capsule enum values.
- `src/capsule_schema.py:1212-1348` defines the UATP 7.4 payload models.
- `src/capsule_schema.py:1622-1656` defines the concrete UATP 7.4 capsule classes.
- `src/capsule_schema.py:1823-1828` registers the UATP 7.4 capsule models in the capsule model map.

## Existing Capsule Types

From `CapsuleType`:

```python
AGENT_SESSION = "agent_session"
TOOL_CALL = "tool_call"
ACTION_TRACE = "action_trace"
DECISION_POINT = "decision_point"
ENVIRONMENT_SNAPSHOT = "environment_snapshot"
```

Concrete capsule models exist:

```python
class AgentSessionCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.AGENT_SESSION] = CapsuleType.AGENT_SESSION
    agent_session: AgentSessionPayload

class ToolCallCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.TOOL_CALL] = CapsuleType.TOOL_CALL
    tool_call: ToolCallPayload

class ActionTraceCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.ACTION_TRACE] = CapsuleType.ACTION_TRACE
    action_trace: ActionTracePayload

class DecisionPointCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.DECISION_POINT] = CapsuleType.DECISION_POINT
    decision_point: DecisionPointPayload

class EnvironmentSnapshotCapsule(BaseCapsule):
    capsule_type: Literal[CapsuleType.ENVIRONMENT_SNAPSHOT] = CapsuleType.ENVIRONMENT_SNAPSHOT
    environment_snapshot: EnvironmentSnapshotPayload
```

## Existing Payload Coverage

### TOOL_CALL

Existing model: `ToolCallPayload`

Fields:

- `call_id`
- `session_id`
- `tool_name`
- `tool_category`
- `tool_inputs`
- `tool_outputs`
- `started_at`
- `completed_at`
- `duration_ms`
- `status`
- `error_message`
- `step_index`
- `parent_call_id`

Existing SQLite table: `tool_calls`

Additional persistence fields:

- `verification`
- `capsule_id`
- `created_at`

Coverage verdict: strong base for individual tool invocation receipts.

Gaps for gold-standard agent receipts:

- canonical `arguments_hash`
- redacted argument preview metadata
- canonical `result_hash`
- redacted/truncated result preview metadata
- `parent_event_hash`
- `receipt_event_hash`
- `policy_digest`
- `adapter_name`
- `agent_name`
- explicit degraded/trust status
- structured error type separate from redacted error message

### ACTION_TRACE

Existing model: `ActionTracePayload`

Fields:

- `action_id`
- `session_id`
- `tool_call_id`
- `action_type`
- `command`
- `exit_code`
- `stdout_hash`
- `stderr_hash`
- `url`
- `selector`
- `browser_action`
- `file_path`
- `file_operation`
- `bytes_affected`
- `executed_at`
- `duration_ms`

Existing SQLite table: `action_traces`

Additional persistence fields:

- `verification`
- `capsule_id`
- `created_at`

Coverage verdict: good base for terminal/browser/file side-effect evidence.

Gaps for gold-standard agent receipts:

- command hash separate from redacted command preview
- cwd
- stdout/stderr preview metadata
- before/after file content hashes
- file patch old/new string hashes
- browser screenshot/artifact refs
- MCP request/response hashes
- verification command classifier fields
- `parent_event_hash`
- `receipt_event_hash`
- `artifact_refs`
- explicit redaction summary

### DECISION_POINT

Existing model: `DecisionPointPayload`

Fields:

- `decision_id`
- `session_id`
- `step_index`
- `reasoning`
- `alternatives_considered`
- `selected_action`
- `confidence`
- `context_summary`
- `constraints_applied`
- `timestamp`

Existing SQLite table: `decision_points`

Additional persistence fields:

- `verification`
- `capsule_id`
- `created_at`

Coverage verdict: conceptually aligned, but needs safe handling before public use.

Gaps for gold-standard agent receipts:

- rename or policy-wrap `reasoning` as audit-safe decision summary by default
- optional encrypted/local-only raw reasoning ref
- evidence refs used by the decision
- policy digest
- raw reasoning capture policy flag
- `parent_event_hash`
- `receipt_event_hash`
- uncertainty/risk factors

Important: do not expose raw reasoning by default. The gold-standard path is audit-safe `DECISION_POINT` summaries with optional sensitive blob refs if explicitly enabled.

### ENVIRONMENT_SNAPSHOT

Existing model: `EnvironmentSnapshotPayload`

Fields:

- `snapshot_id`
- `session_id`
- `working_directory`
- `env_vars_hash`
- `git_branch`
- `git_commit_hash`
- `git_dirty`
- `open_files`
- `system_load`
- `memory_available_gb`
- `timestamp`

Existing SQLite table: `environment_snapshots`

Additional persistence fields:

- `verification`
- `capsule_id`
- `created_at`

Coverage verdict: useful base, but too machine-state-focused for agent reproducibility.

Gaps for gold-standard agent receipts:

- agent framework name/version
- adapter version
- model/provider
- active toolsets
- loaded skills with content hashes
- memory provider state hash where feasible
- MCP server names and config hashes with secrets excluded
- gateway/platform source
- terminal backend
- config digest with secret exclusion rules
- `parent_event_hash`
- `receipt_event_hash`

### AGENT_SESSION

Existing model: `AgentSessionPayload`

Fields:

- `session_id`
- `agent_type`
- `agent_version`
- `scheduler_type`
- `trigger_message`
- `trigger_source`
- `user_id_hash`
- `goals`
- `started_at`
- `completed_at`
- `status`
- `tool_call_count`
- `action_count`
- `decision_count`
- `total_duration_ms`
- `outcome_summary`
- `error_message`

Existing SQLite table: `agent_sessions`

Additional persistence fields:

- `verification`
- `capsule_id`
- `owner_id`
- `created_at`

Coverage verdict: good session envelope for aggregate receipt graphs.

Gaps for gold-standard agent receipts:

- `adapter_name`
- `agent_name`
- model/provider used during session
- receipt chain root hash
- receipt chain tip hash
- child receipt refs/counts by type
- exported bundle id
- signing status summary
- degraded receipt count
- artifact manifest summary
- policy digest
- environment snapshot refs

## Existing SQLite Table Coverage

SQLite dev DB already contains:

```text
agent_sessions
tool_calls
action_traces
decision_points
environment_snapshots
```

This matters because the near-term implementation can stay additive. The core platform can produce neutral receipt events, map them into existing capsule payloads, and persist the resulting capsules/tables without a large schema rewrite.

## Gold-Standard Extension Strategy

Recommended approach:

1. Do not mutate these payload models first.
2. Build `src/agent_receipts/events.py` as a framework-neutral receipt event layer.
3. Build deterministic hashing and chain verification outside the existing schema.
4. Map neutral events to existing UATP 7.4 capsule payloads.
5. Put receipt-chain metadata and artifact refs in additive metadata/verification fields first, if existing persistence supports it.
6. Only add schema fields after tests prove the exact recurring fields that need first-class status.

Reason: this avoids premature schema churn and keeps current Hermes capture tests stable.

## Required New Agent Receipt Concepts

These concepts are not sufficiently first-class today and should be implemented in the new receipt layer:

- `event_id`
- `event_type`
- `adapter_name`
- `agent_name`
- `parent_event_hash`
- `receipt_event_hash`
- `policy_digest`
- `redaction_summary`
- `trust_level`
- `artifact_refs`
- `signature_status`
- `degraded_reason`
- `receipt_bundle_id`
- `chain_root_hash`
- `chain_tip_hash`

## Risks to Avoid

- Do not turn `ToolCallPayload.tool_inputs` into raw unredacted argument dumps.
- Do not treat `stdout_hash` as useful without clearly defining whether it hashes raw, redacted, truncated, or normalized output.
- Do not treat unsigned/hash-only receipts as equivalent to signed receipts.
- Do not put raw reasoning in public capsules by default.
- Do not key skill provenance only by skill name; use exact content hashes.
- Do not couple the neutral event model to Hermes `state.db` rows.

## Phase 0.2 Conclusion

Existing UATP 7.4 schema is sufficient as the target capsule vocabulary. The implementation should proceed with a framework-neutral receipt event layer and additive mappers rather than a new Hermes-specific capsule family.
