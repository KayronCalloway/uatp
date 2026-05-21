# Agent Receipt Verification

UATP agent receipt bundles are signed, append-only records of what an agent did: tool calls, action traces, artifacts, decisions, and verification summaries. They are designed to be checked outside the agent runtime.

The offline verifier does not trust Hermes, a database, or the running app. It loads a public receipt bundle, recomputes the receipt hashes, verifies Ed25519 signatures, checks parent-hash chain adjacency, and optionally verifies content-addressed artifact files.

## Command

```bash
uatp verify-receipts docs/examples/agent-receipts/valid_bundle.json \
  --artifact-root docs/examples/agent-receipts/artifacts \
  --strict \
  --no-color
```

Expected result:

```text
✓ Agent receipt verification PASSED

  Schema: agent_receipts.v1
  Receipts: 2
  Capsule drafts: 2
  Artifacts checked: 1
  Chain root: sha256:...
  Chain tip: sha256:...
```

For machine-readable output:

```bash
uatp verify-receipts docs/examples/agent-receipts/valid_bundle.json \
  --artifact-root docs/examples/agent-receipts/artifacts \
  --strict \
  --output json
```

## What the verifier checks

- Bundle schema version: `agent_receipts.v1`
- Signed receipt envelope shape
- Canonical event hash integrity
- Ed25519 signature validity
- Parent-hash chain adjacency
- Declared chain root/tip/count consistency
- Capsule draft list structure
- Nested artifact refs
- Artifact digest and size when `--artifact-root` is provided

## Tamper demo

These fixtures are intentionally small and deterministic so the failure modes are easy to inspect.

### 1. Valid bundle passes

```bash
uatp verify-receipts docs/examples/agent-receipts/valid_bundle.json \
  --artifact-root docs/examples/agent-receipts/artifacts \
  --strict \
  --no-color
```

Expected: PASS, exit code `0`.

### 2. Event payload tamper fails

```bash
uatp verify-receipts docs/examples/agent-receipts/tampered_event_bundle.json \
  --artifact-root docs/examples/agent-receipts/artifacts \
  --strict \
  --no-color
```

Expected: FAIL, exit code `1`, with:

```text
event_hash does not match signed event payload
```

Why: a signed event payload was edited after signing.

### 3. Parent hash tamper fails

```bash
uatp verify-receipts docs/examples/agent-receipts/tampered_parent_bundle.json \
  --artifact-root docs/examples/agent-receipts/artifacts \
  --strict \
  --no-color
```

Expected: FAIL, exit code `1`, with a `parent_event_hash` error.

Why: the second receipt was validly signed but linked to the wrong previous hash. This proves signature validity alone is not enough; the append-only chain must also verify.

### 4. Signature tamper fails

```bash
uatp verify-receipts docs/examples/agent-receipts/tampered_signature_bundle.json \
  --artifact-root docs/examples/agent-receipts/artifacts \
  --strict \
  --no-color
```

Expected: FAIL, exit code `1`, with:

```text
signature verification failed
```

Why: the receipt hash still matches the event, but the Ed25519 signature no longer verifies.

### 5. Artifact tamper fails

```bash
uatp verify-receipts docs/examples/agent-receipts/valid_bundle.json \
  --artifact-root docs/examples/agent-receipts/artifacts_tampered \
  --strict \
  --no-color
```

Expected: FAIL, exit code `1`, with:

```text
artifact verification failed
```

Why: the bundle points to a content-addressed artifact path, but the bytes under that path no longer match the recorded digest and size.

## Strict vs non-strict artifact checking

Strict mode fails if artifact refs are present but no artifact root is supplied:

```bash
uatp verify-receipts docs/examples/agent-receipts/valid_bundle.json --strict
```

Non-strict mode still verifies the signed receipt chain and reports artifact-root absence as a warning:

```bash
uatp verify-receipts docs/examples/agent-receipts/valid_bundle.json --no-color
```

Use strict mode in CI and demos where artifacts are available. Use non-strict mode when you only have a detached public receipt bundle.
