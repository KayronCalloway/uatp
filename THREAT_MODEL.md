# UATP Threat Model

## Overview

This document describes the attack surface of UATP and how we mitigate threats. For a trust protocol, transparency about threats is itself a form of trust.

## Assets to Protect

| Asset | Criticality | Description |
|-------|-------------|-------------|
| User Private Keys | **Critical** | Ed25519 signing keys |
| Capsule Integrity | **Critical** | Proof that content hasn't been modified |
| Timestamp Accuracy | **High** | Proof of when capsules were created |
| User Privacy | **High** | Content of reasoning/decisions |
| System Availability | **Medium** | API uptime |

## Threat Actors

### 1. External Attackers
- **Goal**: Forge capsules, steal keys, compromise proofs
- **Capability**: Network access, known vulnerabilities

### 2. Malicious Insiders (UATP Operators)
- **Goal**: Forge user capsules, access private data
- **Capability**: Server access, database access
- **Mitigation**: Zero-trust architecture makes this impossible (see below)

### 3. Compromised Dependencies
- **Goal**: Supply chain attacks
- **Capability**: Malicious code in dependencies
- **Mitigation**: Pinned dependencies, security scanning

### 4. Nation-State Actors
- **Goal**: Mass surveillance, targeted compromise
- **Capability**: Extensive resources, zero-days
- **Mitigation**: Defense in depth, cryptographic minimalism

## Attack Vectors & Mitigations

### A. Key Compromise

| Attack | Impact | Mitigation | Status |
|--------|--------|------------|--------|
| Steal private key from server | Critical | **Keys never on server** - user-sovereign architecture | Mitigated |
| Steal private key from user device | Critical | Keys encrypted with PBKDF2 (480k iterations) + Fernet | Mitigated |
| Brute-force passphrase | Critical | High iteration count, minimum 8-char passphrase | Mitigated |
| Memory extraction | High | Keys cleared after use (best-effort in Python) | Partially mitigated |

### B. Capsule Forgery

| Attack | Impact | Mitigation | Status |
|--------|--------|------------|--------|
| UATP forges user signature | Critical | **Impossible** - UATP never has private keys | Mitigated |
| Attacker forges signature | Critical | Ed25519 cryptographic security | Mitigated |
| Modify capsule content | Critical | SHA-256 hash + signature verification | Mitigated |
| Replay old capsule | Medium | RFC 3161 timestamps from external TSA | Mitigated |

### C. Timestamp Manipulation

| Attack | Impact | Mitigation | Status |
|--------|--------|------------|--------|
| UATP backdates timestamp | High | **External TSA** (DigiCert) - UATP can't control | Mitigated |
| TSA compromise | High | Multiple TSA support planned | Planned |
| Network time attacks | Medium | TSA uses authenticated time sources | Mitigated |

### D. Data Exfiltration

| Attack | Impact | Mitigation | Status |
|--------|--------|------------|--------|
| UATP reads capsule content | High | Content stays local unless user publishes | Mitigated |
| Database breach | Medium | Only hashes stored on server | Mitigated |
| Network sniffing | Medium | TLS required for all connections | Mitigated |

### E. Denial of Service

| Attack | Impact | Mitigation | Status |
|--------|--------|------------|--------|
| API flooding | Medium | Rate limiting, caching | Implemented |
| Resource exhaustion | Medium | Request size limits | Implemented |
| TSA unavailability | Low | Graceful degradation, retry logic | Implemented |

### F. Supply Chain

| Attack | Impact | Mitigation | Status |
|--------|--------|------------|--------|
| Malicious dependency | High | Dependency pinning, Dependabot | Implemented |
| Compromised PyNaCl | Critical | Audited library, minimal dependencies | Accepted risk |
| CI/CD compromise | High | Branch protection, signed commits | Implemented |

## Trust Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                     USER DEVICE (Trusted)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Private Key │  │  Capsule    │  │  Signing    │          │
│  │  (encrypted)│  │  Content    │  │  Operation  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Only hash transmitted
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   UATP SERVER (Untrusted)                    │
│  ┌─────────────┐  ┌─────────────┐                           │
│  │   Hash      │  │  Timestamp  │                           │
│  │   Storage   │  │   Request   │                           │
│  └─────────────┘  └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Hash for timestamping
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  EXTERNAL TSA (Independent)                  │
│  ┌─────────────┐                                            │
│  │  RFC 3161   │  DigiCert / FreeTSA                        │
│  │  Timestamp  │  (Not controlled by UATP)                  │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

## What UATP Cannot Do

By design, UATP operators **cannot**:

1. ❌ Forge user signatures (no access to private keys)
2. ❌ Read capsule content (stays on user device)
3. ❌ Backdate timestamps (external TSA)
4. ❌ Modify existing capsules (hash verification)
5. ❌ Decrypt user keys (passphrase never transmitted)

## Residual Risks

| Risk | Likelihood | Impact | Acceptance |
|------|------------|--------|------------|
| Python memory not fully cleared | Medium | Medium | Accepted - language limitation |
| Single TSA dependency | Low | Medium | Planned multi-TSA |
| Cryptographic breakthrough | Very Low | Critical | Monitoring, PQ-ready |
| User loses passphrase | Medium | High | User responsibility |

## Security Assumptions

We assume:
1. User's device is not fully compromised
2. Ed25519 remains cryptographically secure
3. SHA-256 remains collision-resistant
4. External TSAs operate honestly
5. TLS provides transport security

## Incident Response

If a security incident occurs:
1. Affected users notified within 24 hours
2. Public disclosure within 72 hours
3. Post-mortem published
4. Mitigation deployed

## Contact

Security issues: Kayron@houseofcalloway.com

See [SECURITY.md](SECURITY.md) for responsible disclosure process.
