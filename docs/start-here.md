# Start Here

Welcome to UATP. This page helps you find what you need based on who you are.

---

## I'm a Developer

**Goal:** Integrate UATP into my application

1. **[Quick Start](../README.md#quick-start)** - Get running in 5 minutes
2. **[SDK Documentation](../sdk/python/README.md)** - Python SDK reference
3. **[Examples](../examples/)** - Working code samples
4. **[API Documentation](api-documentation.md)** - REST API reference
5. **[Tests](../tests/)** - See how we test, write your own

**Key files:**
- `sdk/python/` - Install with `pip install -e .`
- `examples/` - Copy-paste starting points
- `src/api/` - Backend implementation

---

## I'm a Security Reviewer

**Goal:** Understand and verify UATP's security claims

1. **[Trust Model](../TRUST_MODEL.md)** - Zero-trust architecture explained
2. **[Threat Model](../THREAT_MODEL.md)** - Attack surface and mitigations
3. **[Security Policy](../SECURITY.md)** - Vulnerability reporting
4. **[Cryptographic Implementation](../src/crypto/)** - Ed25519, key management
5. **[Verification Tests](../tests/)** - Proof that claims hold

**Key files:**
- `src/crypto/user_key_manager.py` - Key generation and storage
- `src/crypto/local_signer.py` - Signing implementation
- `TRUST_MODEL.md` - What UATP can and cannot do

**The core claim to verify:**
```
User signs locally → Only hash sent to UATP → External TSA timestamps
```

---

## I'm Evaluating UATP for My Organization

**Goal:** Understand if UATP fits my needs

1. **[README](../README.md)** - What UATP does
2. **[Status](../STATUS.md)** - What's production-ready vs beta
3. **[Use Cases](../README.md#use-cases)** - Healthcare, Finance, Legal
4. **[Roadmap](../ROADMAP.md)** - Where we're headed
5. **[Architecture](architecture/)** - System design

**Questions you probably have:**

| Question | Answer |
|----------|--------|
| Is it production-ready? | Core signing: Yes. Dashboard: Beta. |
| Who controls the keys? | Users. Always. |
| Can you read my data? | No. Content stays local. |
| Is it audited? | Internal only. External audit planned. |
| What's the pricing? | Open beta: Free. See README. |

---

## I'm a Researcher

**Goal:** Understand the theory and vision

1. **[Trust Model](../TRUST_MODEL.md)** - Cryptographic architecture
2. **[Research Documents](research/)** - Whitepapers, system guides
3. **[Roadmap](../ROADMAP.md)** - Long-term vision
4. **[Concepts](concepts/)** - Core ideas explained

**The thesis:**
> AI decisions should be auditable with cryptographic proof. UATP makes AI reasoning court-admissible.

---

## I Want to Contribute

1. **[Contributing Guide](../CONTRIBUTING.md)** - How to help
2. **[Code of Conduct](../CODE_OF_CONDUCT.md)** - Community standards
3. **[Good First Issues](https://github.com/KayronCalloway/uatp/labels/good%20first%20issue)** - Where to start
4. **[Development Setup](operations/)** - Local environment

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | Project overview |
| [STATUS.md](../STATUS.md) | What's ready, what's not |
| [TRUST_MODEL.md](../TRUST_MODEL.md) | Security architecture |
| [THREAT_MODEL.md](../THREAT_MODEL.md) | Attack surface |
| [SECURITY.md](../SECURITY.md) | Vulnerability reporting |
| [CHANGELOG.md](../CHANGELOG.md) | Version history |
| [ROADMAP.md](../ROADMAP.md) | Future plans |

---

*Can't find what you need? [Open an issue](https://github.com/KayronCalloway/uatp/issues) or email Kayron@houseofcalloway.com*
