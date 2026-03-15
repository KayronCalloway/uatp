# UATP Cryptographic Matrix

> This document maps which cryptographic algorithms are used where and why.

## Summary

| Purpose | Algorithm | Library | Strength |
|---------|-----------|---------|----------|
| **Signatures (primary)** | Ed25519 | PyNaCl / cryptography | 128-bit security |
| **Signatures (post-quantum)** | ML-DSA-65 | liboqs-python | NIST L3 |
| **Content Hashing** | SHA-256 | hashlib | 256-bit |
| **Key Encryption** | Fernet (AES-128-CBC + HMAC) | cryptography | 128-bit |
| **Key Derivation** | PBKDF2-HMAC-SHA256 | cryptography | 480,000 iterations |
| **Timestamps** | RFC 3161 | External TSA (DigiCert) | N/A |

---

## Module-by-Module Breakdown

### SDK (User-Sovereign Path)

**Location:** `sdk/python/uatp/crypto/`

| Module | Algorithm | Library | Notes |
|--------|-----------|---------|-------|
| `user_key_manager.py` | Ed25519 | PyNaCl (`nacl.signing`) | Key generation and signing |
| `user_key_manager.py` | Fernet | `cryptography.fernet` | Private key encryption |
| `user_key_manager.py` | PBKDF2-HMAC-SHA256 | `cryptography.hazmat.primitives.kdf.pbkdf2` | 480,000 iterations |
| `local_signer.py` | SHA-256 | `hashlib` | Content hashing |
| `local_signer.py` | Ed25519 verify | PyNaCl (`nacl.signing.VerifyKey`) | Signature verification |

**Security Properties:**
- Private keys never leave user's device
- Keys encrypted at rest with user passphrase
- 480,000 PBKDF2 iterations exceeds OWASP recommendation (310,000)

### Server Engine (Backend Path)

**Location:** `src/security/`, `src/crypto/`

| Module | Algorithm | Library | Notes |
|--------|-----------|---------|-------|
| `uatp_crypto_v7.py` | Ed25519 | `cryptography.hazmat.primitives.asymmetric.ed25519` | Classical signatures |
| `uatp_crypto_v7.py` | ML-DSA-65 | `oqs` (liboqs-python) | Post-quantum (optional) |
| `uatp_crypto_v7.py` | SHA-256 | `hashlib` | Content and Merkle hashing |
| `uatp_crypto_v7.py` | AES-256 | `cryptography.hazmat.primitives.ciphers` | Key storage |
| `secure_key_manager.py` | Fernet | `cryptography.fernet` | Session key encryption |
| `secure_key_manager.py` | PBKDF2HMAC | `cryptography.hazmat.primitives.kdf.pbkdf2` | Key derivation |
| `rfc3161_timestamps.py` | RFC 3161 | `httpx` (to external TSA) | DigiCert/FreeTSA |

**Security Properties:**
- Server can sign on behalf of user (legacy mode)
- Server-signed capsules marked with `"signer": "server"`
- Optional post-quantum hybrid signatures

### Authentication

**Location:** `src/auth/`

| Module | Algorithm | Notes |
|--------|-----------|-------|
| `security.py` | Argon2id | Password hashing (via `argon2-cffi`) |
| `jwt_manager.py` | HS256 | JWT signing |

---

## Two Crypto Implementations

UATP has two parallel signing implementations:

### 1. SDK Path (Recommended)
```
sdk/python/uatp/crypto/user_key_manager.py
      ↓
Uses: PyNaCl (libsodium bindings)
Ed25519 via: nacl.signing.SigningKey
```

### 2. Server Path (Legacy)
```
src/security/uatp_crypto_v7.py
      ↓
Uses: cryptography library (OpenSSL bindings)
Ed25519 via: cryptography.hazmat.primitives.asymmetric.ed25519
```

**Why two?**
- SDK: User-sovereign, zero-trust, PyNaCl for simplicity
- Server: Supports post-quantum (ML-DSA-65), richer features

**Compatibility:**
- Ed25519 signatures are interoperable (same curve, same output format)
- Verification works across both implementations
- Server can verify SDK-signed capsules and vice versa

---

## Algorithm Selection Rationale

### Ed25519
- FIPS 186-5 compliant
- 128-bit security level
- Small signatures (64 bytes)
- Fast signing and verification
- Deterministic (no random nonce needed)

### ML-DSA-65 (Post-Quantum)
- NIST FIPS 204 standard (formerly Dilithium3)
- Category 3 security (~128-bit classical equivalent)
- Larger signatures (~2.4 KB)
- Future-proofing against quantum computers

### SHA-256
- FIPS 180-4 compliant
- Collision-resistant
- Used for content hashing and Merkle trees

### Fernet (AES-128-CBC + HMAC-SHA256)
- Authenticated encryption
- Built into cryptography library
- Used for key-at-rest encryption

### PBKDF2
- NIST SP 800-132 compliant
- 480,000 iterations (exceeds OWASP guidance)
- Salt generated per-key using `secrets.token_bytes()`

---

## Dependencies

```toml
# Signatures
pynacl>=1.5.0        # Ed25519 (SDK path)
cryptography>=44.0.1 # Ed25519/AES (server path)

# Post-quantum (optional)
oqs                  # liboqs-python for ML-DSA-65

# Key derivation
argon2-cffi>=23.1.0  # Password hashing for auth
```

---

## Known Limitations

1. **No hardware key support**: Keys are software-only (no HSM/TPM integration shipped)
2. **RFC 3161 verification**: Timestamp presence checked, not cryptographically verified
3. **No key escrow**: User loses passphrase = key unrecoverable
4. **Library drift**: SDK uses PyNaCl, server uses cryptography (same algorithms, different bindings)

---

## Verification Assurance Levels

The `verify_capsule_standalone()` function returns an `assurance_level`:

| Level | What's Verified | Trust Implications |
|-------|-----------------|-------------------|
| `none` | Nothing | Verification failed |
| `signature_only` | Ed25519 signature valid | Content may have changed |
| `signature_and_hash` | Signature + content integrity | Strong (timestamp not verified) |
| `full` | All above + RFC 3161 timestamp | Strongest (time-bound proof) |

**Note:** `full` assurance requires the `rfc3161ng` library for TSA certificate chain validation.

---

*Last updated: 2026-03-14*
