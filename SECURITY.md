# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | Yes       |
| < 1.1   | No        |

## Reporting a Vulnerability

**Do not open public issues for security vulnerabilities.**

Email: **Kayron@houseofcalloway.com**

Include:
- Vulnerability type and affected files
- Step-by-step reproduction
- Proof-of-concept if possible
- Impact assessment

## Response Timeline

- **Initial response:** 48 hours
- **Status update:** 7 days
- **Resolution target:** Critical (7 days), High (14 days), Medium/Low (30 days)

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
