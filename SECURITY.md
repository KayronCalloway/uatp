# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Source tree 1.1.x | Yes |
| GitHub release v1.1.0 | Yes |
| PyPI `uatp` 0.2.x / npm 1.0.x | Security fixes only until registry sync |
| < 0.2 | No |

## Reporting a Vulnerability

**Do not open public issues for security vulnerabilities.**

Email: **Kayron@houseofcalloway.com**

Include:
- Vulnerability type and affected files
- Step-by-step reproduction
- Proof-of-concept if possible
- Impact assessment

## Response Timeline

Expect an initial response within 48 hours and status updates within 7 days. Critical fixes are prioritized immediately; lower-severity issues are batched when safe.

## Security Architecture

- **User-sovereign keys:** Generated and stored locally. UATP servers never see private keys.
- **Ed25519 signatures:** FIPS 186-5 compliant
- **ML-DSA-65:** Post-quantum signing (FIPS 204), beta
- **RFC 3161 timestamps:** External timestamping from DigiCert TSA
- **PBKDF2-HMAC-SHA256:** 480,000 iterations for key derivation

See [TRUST_MODEL.md](TRUST_MODEL.md) for the full security model.

## Scope

This policy covers:
- UATP Capsule Engine core (`src/`)
- Python SDK (`sdk/python/`)
- Official documentation

Third-party integrations and forks are outside scope.
