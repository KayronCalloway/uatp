# Agent Receipt Demo Fixtures

Deterministic fixtures for `uatp verify-receipts`.

Files:

- `valid_bundle.json` — valid signed two-receipt bundle.
- `tampered_event_bundle.json` — event payload edited after signing.
- `tampered_parent_bundle.json` — second receipt signed with the wrong parent hash.
- `tampered_signature_bundle.json` — signature bytes edited after signing.
- `artifacts/` — valid content-addressed artifact root.
- `artifacts_tampered/` — same artifact path with modified bytes.

Run the single valid fixture:

```bash
uatp verify-receipts docs/examples/agent-receipts/valid_bundle.json \
  --artifact-root docs/examples/agent-receipts/artifacts \
  --strict \
  --no-color
```

Run the full pass/fail demo:

```bash
./.venv/bin/python scripts/demo/verify_agent_receipt_tamper_demo.py
```

A passing fixture result proves integrity/self-consistency. Add `--trusted-signer signer_id=public_key_hex` when the verifier must enforce signer identity. Current fixtures report `Trusted timestamp: missing`; do not treat them as trusted-time evidence.

See `docs/architecture/agent-receipt-verification.md` for the full tamper demo.
