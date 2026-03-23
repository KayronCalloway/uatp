# Security Policy

## Supported Versions

| Component | Version | Supported |
|-----------|---------|-----------|
| SDK (PyPI/npm) | 1.0.x | :white_check_mark: |
| Capsule Schema | 7.2 | :white_check_mark: |
| Capsule Schema | < 7.2 | :x: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **Kayron@houseofcalloway.com**

### What to Include

Please include the following information in your report:

- Type of vulnerability (e.g., cryptographic weakness, injection, authentication bypass)
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact assessment of the vulnerability

### Severity Levels

| Severity | Definition | Examples |
|----------|------------|----------|
| **Critical** | Remote code execution, key compromise, signature bypass | Private key extraction, forged signatures accepted |
| **High** | Authentication bypass, data exposure | JWT bypass, unauthorized capsule access |
| **Medium** | Limited security impact | Information disclosure, DoS vectors |
| **Low** | Minimal security impact | Minor information leaks, hardening issues |

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution Target**: Critical (7 days), High (14 days), Medium/Low (30 days)

### What to Expect

1. **Acknowledgment**: You'll receive confirmation that we've received your report
2. **Assessment**: We'll investigate and determine the severity
3. **Updates**: We'll keep you informed of our progress
4. **Resolution**: We'll notify you when the issue is fixed
5. **Credit**: With your permission, we'll acknowledge your contribution

## Security Architecture

UATP implements a zero-trust cryptographic architecture:

- **User-Sovereign Keys**: Private keys are generated and stored locally on user devices
- **Ed25519 Signatures**: FIPS 186-5 compliant digital signatures
- **RFC 3161 Timestamps**: External timestamping from trusted authorities (DigiCert)
- **PBKDF2-HMAC-SHA256**: 480,000 iterations for key derivation
- **No Server-Side Key Access**: UATP servers never see user private keys

For details, see [TRUST_MODEL.md](TRUST_MODEL.md).

## Security Best Practices for Users

1. **Protect Your Passphrase**: Use a strong, unique passphrase for your signing keys
2. **Secure Your Key Directory**: The `~/.uatp/keys` directory contains encrypted keys
3. **Backup Keys Securely**: Use `export_encrypted_backup()` for secure key backups
4. **Verify Signatures**: Always verify capsules using standalone verification

## Scope

This security policy applies to:

- The UATP Capsule Engine core (`src/`)
- The Python SDK (`sdk/python/`)
- Official documentation and examples

Third-party integrations and forks are outside our scope.
