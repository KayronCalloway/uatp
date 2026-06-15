# UATP Trust Model

This document defines the current public trust boundary for UATP Core.

The short version: a valid receipt or capsule can prove that a specific key signed specific bytes, that the signed bytes still hash to the same value, and, when configured, that a trusted policy accepts the signer or timestamp evidence. It does not automatically prove legal admissibility, production readiness, trusted identity, trusted time, compensation, or regulatory compliance.

See [STATUS.md](STATUS.md) for component status and audit state.

---

## Current Guarantees

| Guarantee | Current status | Boundary |
|-----------|----------------|----------|
| Ed25519 signature verification | Shipped | Proves key possession for the signed preimage, not real-world identity by itself |
| Content / event hash verification | Shipped | Detects changes to signed payloads and receipt chains |
| Standalone legacy capsule verification | Shipped | Works for legacy capsule bundles; assurance depends on available signature/hash/timestamp evidence |
| Offline agent receipt bundle verification | Beta | Verifies signed receipt chains outside the agent runtime |
| Trusted signer policy | Shipped for receipt CLI | Only enforced when the verifier is given trusted signer bindings |
| RFC 3161 timestamp validation | Beta | Requires explicit TSA certificate/trust-anchor material; missing anchors do not create trusted-time proof |
| Transparency log | Planned | Not implemented |
| External security audit | Planned | Not completed |

---

## What a Valid Receipt Proves

A successful agent receipt verification can prove:

1. the receipt payload matches its recorded event hash;
2. the receipt signature verifies against the public key in the bundle;
3. the parent-hash chain is internally consistent;
4. referenced artifacts match expected digests when artifact checking is enabled;
5. capsule drafts and bundle metadata are internally consistent where the verifier checks them.

If `--trusted-signer signer_id=public_key_hex` is supplied, verification can also prove that the signer matched a verifier-provided trust policy.

If trusted timestamp verification is required and explicit TSA trust anchors are supplied, verification can also prove the timestamp token validated against that trust material.

---

## What a Valid Receipt Does Not Prove

A passing verification result does not automatically prove:

- that the signer is a specific person, company, device, or app;
- that the signer was authorized unless a trust policy was supplied and passed;
- that the event happened at a trusted time unless RFC 3161 validation passed against explicit trust anchors;
- that the event is legally admissible;
- that an insurance, regulator, or court will accept the record;
- that the system was unbiased or policy-compliant beyond what the signed payload and external review can establish;
- that attribution, licensing, or compensation has been solved.

The public core is a proof layer, not a legal or commercial conclusion engine.

---

## Trust Modes

### 1. Cryptographic self-consistency

Default receipt verification without a trust policy checks whether the bundle is internally valid.

This is useful for tamper detection and debugging, but the verifier is still trusting the bundle's embedded public key as evidence of only key possession.

### 2. Trusted signer policy

When a verifier supplies trusted signer bindings, verification checks that the receipt was signed by an accepted signer key.

Example:

```bash
uatp verify-receipts receipt_bundle.json \
  --trusted-signer uatp-mcp-gateway=<ed25519_public_key_hex> \
  --strict \
  --no-color
```

This is the minimum boundary for saying: “this known signer signed these bytes.”

### 3. Trusted timestamp policy

Trusted time requires explicit TSA certificate or trust-anchor material.

A bundle that reports `Trusted timestamp: missing` or has no verified TSA chain should not be described as trusted-time evidence.

---

## Legacy Capsules vs Agent Receipts

UATP currently has two relevant surfaces:

- **Legacy capsules:** broader UATP records, including schema 7.2-era bundles.
- **Agent receipt bundles:** verifier-first signed event chains for agent actions, tool calls, decisions, artifacts, corrections, and session traces.

The agent receipt path is the current public wedge because it can be exported and verified offline without trusting Hermes, SQLite, the MCP gateway, or the producing runtime.

---

## Key Management Boundary

UATP supports local signing paths where private keys stay on the user's machine. That is the preferred pattern for new integrations.

Some legacy/server paths still support server-side signing or attestation for compatibility and deployments that intentionally choose that boundary. Those records should not be described as user-sovereign signatures unless the signing key was actually controlled by the user.

Operational keys, API tokens, TLS certificates, and server attestation keys are separate from user signing keys.

---

## Threats UATP Helps With

| Threat | What UATP can help prove |
|--------|--------------------------|
| Payload tampering | Signed hash no longer matches |
| Chain tampering | Parent hash or chain tip no longer matches |
| Artifact tampering | Artifact digest check fails |
| Runtime trust gap | Receipt can be verified outside the runtime |
| Signer confusion | Trusted signer policy can reject unknown keys |
| Timestamp overclaim | Verifier can fail closed when trusted timestamp evidence is required but missing |

---

## Threats Outside the Current Public Core

| Threat | Boundary |
|--------|----------|
| Compromised signer key | Needs key rotation, revocation, and operational controls |
| False but signed event | A signature proves the signer committed to the payload; it does not prove the payload is true without external evidence |
| Biased model decision | Receipts can preserve evidence for audit; bias analysis is a separate review layer |
| Legal admissibility | Requires legal process, chain-of-custody controls, and jurisdiction-specific review |
| Insurance acceptance | Requires insurer workflows and review; UATP can supply evidence artifacts |
| Marketplace compensation | Future product/commercial layer, not a current public-core guarantee |

---

## Compliance Boundary

UATP can support compliance workflows by preserving signed, inspectable records. It is not itself a certification for GDPR, SOC 2, EU AI Act compliance, or evidentiary admissibility.

Those claims require deployment controls, organizational process, legal review, audits, and regulator- or customer-specific acceptance.

---

## Implementation Notes

Current shipped and planned pieces:

- [x] Local signing support in SDK paths
- [x] Standalone legacy capsule verification
- [x] Offline agent receipt bundle verification
- [x] Trusted signer policy support for `verify-receipts`
- [x] RFC 3161 token validation when explicit TSA trust anchors are supplied
- [ ] Transparency log
- [ ] External security audit
- [ ] Full key rotation / revocation workflow
- [ ] Production trust registry

Current assurance labels used by standalone capsule verification:

- `none`: signature verification failed
- `signature_only`: signature valid but content hash mismatch
- `signature_and_hash`: signature and content integrity verified; timestamp not cryptographically validated
- `full`: signature, hash, and RFC 3161 timestamp validated against explicit TSA trust anchors

---

## Bottom Line

Do not trust the agent runtime. Check the receipt somewhere else.

But do not overread the receipt either. UATP proves signed records and tamper evidence first. Trusted identity, trusted time, legal use, compliance, attribution, and compensation require additional layers on top of that proof.
