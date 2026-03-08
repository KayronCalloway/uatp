# UATP Trust Model

> This document defines what UATP can and cannot do, cryptographically enforced.

**Implementation Status:** Partial - see checklist at bottom for what's shipped vs. in progress.

## Core Principle

**UATP operates on a zero-knowledge, user-sovereign architecture.**

The system is designed so that even if UATP (the company/operator) wanted to act maliciously, the cryptography prevents it.

---

## Trust Guarantees

### What UATP CANNOT Do

| Action | Why It's Impossible |
|--------|---------------------|
| Forge a user's signature | User's private key never leaves their device |
| Backdate a capsule | Timestamps come from external TSA (DigiCert), not UATP |
| Read user's private capsules | Content stays local; only hash is transmitted for timestamping |
| Modify a sealed capsule | Any change invalidates the cryptographic signature |
| Deny a capsule existed | Timestamps are independently verifiable via TSA |
| Impersonate a user | Each user has unique key pair they control |

### What UATP CAN Do

| Action | Why It's Allowed |
|--------|------------------|
| Provide timestamp service | Relays hash to external TSA, returns signed timestamp |
| Host verification portal | Reads public data, performs signature verification |
| Operate marketplace | Handles commerce for capsules users choose to publish |
| Revoke API access | Can deny service, but cannot forge or tamper |
| Maintain protocol | Publishes updates, but changes are public and auditable |

---

## Cryptographic Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER'S DEVICE                                  │
│                                                                          │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │  Private Key     │    │  Capsule Content │    │  Local Storage   │   │
│  │  (NEVER LEAVES)  │    │  (NEVER LEAVES)  │    │  (Encrypted)     │   │
│  └────────┬─────────┘    └────────┬─────────┘    └──────────────────┘   │
│           │                       │                                      │
│           ▼                       ▼                                      │
│  ┌──────────────────────────────────────────┐                           │
│  │  LOCAL SIGNING                            │                           │
│  │  1. Hash capsule content (SHA-256)        │                           │
│  │  2. Sign hash with user's Ed25519 key     │                           │
│  │  3. Capsule now has user's signature      │                           │
│  └────────────────────┬─────────────────────┘                           │
│                       │                                                  │
│                       │ Only the HASH is sent                           │
│                       ▼                                                  │
└───────────────────────┼──────────────────────────────────────────────────┘
                        │
                        │  SHA-256 hash (32 bytes)
                        │  No content, no private key
                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                         UATP TIMESTAMP SERVICE                            │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  Receives: Hash only                                                 │ │
│  │  Cannot: See content, forge signature, backdate                      │ │
│  │  Does: Forward hash to external TSA                                  │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                    │                                      │
│                                    ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  EXTERNAL TSA (DigiCert/FreeTSA)                                     │ │
│  │  - Independent third party                                           │ │
│  │  - RFC 3161 compliant                                                │ │
│  │  - Signs timestamp with THEIR key (not UATP's)                       │ │
│  │  - Legally admissible                                                │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                    │                                      │
│                                    ▼                                      │
│  Returns: RFC 3161 timestamp token (signed by TSA, not UATP)             │
└───────────────────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                           USER'S DEVICE                                   │
│                                                                           │
│  Capsule now contains:                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │  • Content (local only)                                              │ │
│  │  • User's Ed25519 signature (proves authorship)                      │ │
│  │  • RFC 3161 timestamp (proves time, from external TSA)               │ │
│  │  • User's public key (for verification)                              │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  UATP has seen: Only the hash                                            │
│  UATP can prove: Nothing (they don't have the content or signature)      │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Verification (Anyone Can Do This)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        VERIFICATION PROCESS                              │
│                                                                          │
│  Given a capsule, ANYONE can verify without trusting UATP:               │
│                                                                          │
│  1. SIGNATURE CHECK                                                      │
│     ├─ Extract public key from capsule                                   │
│     ├─ Extract signature from capsule                                    │
│     ├─ Recompute hash of content                                         │
│     └─ Verify: Ed25519.verify(public_key, signature, hash)               │
│        Result: Proves content was signed by key holder                   │
│                                                                          │
│  2. TIMESTAMP CHECK                                                      │
│     ├─ Extract RFC 3161 token                                            │
│     ├─ Verify TSA signature (DigiCert's public key is public)            │
│     ├─ Check hash in token matches capsule hash                          │
│     └─ Result: Proves capsule existed at claimed time                    │
│                                                                          │
│  3. INTEGRITY CHECK                                                      │
│     ├─ Recompute hash of current content                                 │
│     ├─ Compare to signed hash                                            │
│     └─ Result: Proves content hasn't been modified                       │
│                                                                          │
│  UATP's role in verification: NONE                                       │
│  Verification is purely cryptographic, no trust required                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Key Management

### User Keys

| Property | Implementation |
|----------|----------------|
| Generation | On user's device, using OS secure random |
| Storage | Encrypted with user's passphrase, local only |
| Backup | User's responsibility (encrypted export available) |
| Recovery | From backup only; UATP cannot recover |
| Rotation | User-initiated; old capsules remain valid |

### UATP Keys (If Any)

UATP may have operational keys for:
- Signing software releases
- TLS certificates for services
- API authentication tokens

**These keys are NEVER used for user capsules.**

Any UATP signature is clearly labeled as "UATP Attestation" (e.g., "we received this hash at this time") and is separate from user signatures.

---

## Transparency Log

All UATP operations are logged to a public, append-only transparency log:

```
https://transparency.uatp.io/log

Entry format:
{
  "timestamp": "2026-03-08T12:00:00Z",
  "operation": "timestamp_request",
  "hash": "abc123...",  // The hash we received (not content)
  "tsa_response": "...", // What DigiCert returned
  "log_signature": "..." // Signed by UATP transparency key
}
```

Anyone can:
- Monitor the log for anomalies
- Verify log integrity (Merkle tree)
- Audit UATP's behavior

---

## Threat Model

### Threats We Protect Against

| Threat | Protection |
|--------|------------|
| UATP goes rogue | Can't forge (don't have keys), can't backdate (external TSA) |
| UATP gets hacked | Attacker can't forge user signatures (keys not on server) |
| UATP subpoenaed | Can only provide hashes, not content (content is local) |
| UATP shuts down | Capsules remain verifiable (self-contained proofs) |
| Man-in-the-middle | TLS + signature verification catches tampering |
| Replay attacks | Timestamps prevent replaying old signatures |

### Threats We Don't Protect Against

| Threat | Why | Mitigation |
|--------|-----|------------|
| User loses private key | User-sovereign = user-responsible | Backup guidance |
| User's device compromised | Keys on device | Security best practices |
| User shares private key | Social/operational issue | Education |
| TSA compromise | External dependency | Multiple TSA support |

---

## Compliance

This architecture supports:

| Requirement | How |
|-------------|-----|
| GDPR Right to Erasure | Content is local; user can delete |
| GDPR Data Minimization | UATP only sees hashes, not content |
| EU AI Act Transparency | Full audit trail of AI decisions |
| Court Admissibility | RFC 3161 timestamps, Ed25519 signatures (Daubert-compliant) |
| SOC 2 | Separation of concerns, audit logging |

---

## Summary

**The Gold Standard:**

1. **User-sovereign keys**: Generated and stored locally, never transmitted
2. **External timestamps**: DigiCert/FreeTSA, not UATP
3. **Hash-only transmission**: UATP never sees content
4. **Independent verification**: No trust in UATP required
5. **Transparency logging**: All UATP operations are public

**If the President calls:**

> "I cannot forge a capsule or backdate a timestamp. Users hold their own signing keys which never leave their devices. Timestamps come from DigiCert, not us. I can show you the code, the architecture, and the transparency logs. The math doesn't allow tampering."

---

## Implementation Checklist

- [x] Remove server-side signing keys from git
- [x] Implement `UserKeyManager` for local key generation (`src/crypto/user_key_manager.py`)
- [x] Implement `LocalSigner` for user-side signing (`src/crypto/local_signer.py`)
- [x] Implement hash-only timestamp flow
- [x] Document key backup/recovery process (in UserKeyManager)
- [x] Create standalone verification function
- [ ] Update SDK to use new local signing
- [ ] Create transparency log infrastructure
- [ ] Security audit of new architecture
- [ ] Update Claude Code capture to use local signing
