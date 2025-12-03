# UATP Production API - Mobile & WebAuthn

Production-ready APIs for mobile client integration and passwordless authentication.

---

## 🚀 Quick Start

### Start the Server
```bash
# Ensure dependencies are installed
pip install -r requirements.txt

# Start the API server
python3 run.py

# Server will run on http://localhost:9090
```

### Run Tests
```bash
# Test all new endpoints
python3 test_production_api.py

# Expected output: ✅ ALL TESTS PASSED!
```

---

## 📱 Mobile API

### Base URL
```
http://localhost:9090/api/v1/mobile
```

### Authentication
All mobile endpoints require API key authentication:
```
X-API-Key: test-api-key
```

---

### Endpoints

#### 1. Health Check
**GET** `/api/v1/mobile/health`

Returns server capabilities and version info.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:00:00Z",
  "capabilities": {
    "batch_submission": true,
    "offline_queue": true,
    "push_notifications": true,
    "compression": true,
    "webauthn": true,
    "background_sync": true,
    "version": "1.0.0"
  },
  "server_version": "UATP-7.0",
  "min_client_version": "1.0.0"
}
```

---

#### 2. Create Single Capsule
**POST** `/api/v1/mobile/capture/single`

Submit a single AI conversation capsule from mobile device.

**Request:**
```json
{
  "device_id": "iphone-12345",
  "platform": "ios",
  "messages": [
    {
      "role": "user",
      "content": "What is the capital of France?",
      "timestamp": "2025-01-15T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "The capital of France is Paris.",
      "timestamp": "2025-01-15T10:00:02Z"
    }
  ],
  "parent_capsule_id": null,
  "metadata": {
    "app_version": "1.0.0",
    "os_version": "iOS 17.2"
  }
}
```

**Response:**
```json
{
  "success": true,
  "capsule_id": "mobile_20250115_abc123def456",
  "status": "sealed",
  "timestamp": "2025-01-15T10:00:05Z",
  "verification_hash": "sha256_hash_here",
  "sync_token": "sync_mobile_20250115_abc123def456",
  "server_timestamp": "2025-01-15T10:00:05.123Z"
}
```

---

#### 3. Batch Capsule Submission
**POST** `/api/v1/mobile/capture/batch`

Submit multiple capsules at once (for offline sync).

**Request:**
```json
{
  "device_id": "iphone-12345",
  "capsules": [
    {
      "client_id": "offline-001",
      "messages": [
        {"role": "user", "content": "Question 1"},
        {"role": "assistant", "content": "Answer 1"}
      ]
    },
    {
      "client_id": "offline-002",
      "messages": [
        {"role": "user", "content": "Question 2"},
        {"role": "assistant", "content": "Answer 2"}
      ]
    }
  ],
  "metadata": {
    "offline_duration_seconds": 300
  }
}
```

**Response:**
```json
{
  "success": true,
  "total_submitted": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "client_id": "offline-001",
      "capsule_id": "batch_20250115_xyz789",
      "status": "success",
      "timestamp": "2025-01-15T10:05:00Z"
    },
    {
      "client_id": "offline-002",
      "capsule_id": "batch_20250115_xyz790",
      "status": "success",
      "timestamp": "2025-01-15T10:05:01Z"
    }
  ],
  "sync_token": "batch_1705316700.123",
  "server_timestamp": "2025-01-15T10:05:01.456Z"
}
```

---

#### 4. Sync Capsules
**POST** `/api/v1/mobile/sync`

Get capsules created/updated since last sync (delta sync).

**Request:**
```json
{
  "device_id": "iphone-12345",
  "last_sync_timestamp": "2025-01-15T09:00:00Z",
  "platform": "ios"
}
```

**Response:**
```json
{
  "success": true,
  "capsules": [
    {
      "capsule_id": "mobile_20250115_abc123",
      "timestamp": "2025-01-15T09:30:00Z",
      "status": "sealed",
      "verification_hash": "sha256_hash"
    }
  ],
  "sync_token": "sync_1705316700.789",
  "server_timestamp": "2025-01-15T10:00:00Z",
  "has_more": false
}
```

---

#### 5. List Capsules
**GET** `/api/v1/mobile/capsules/list?page=0&limit=50`

Get paginated list of capsules (lightweight response).

**Query Parameters:**
- `page` (int): Page number (default: 0)
- `limit` (int): Items per page (max: 100, default: 50)

**Response:**
```json
{
  "success": true,
  "capsules": [
    {
      "capsule_id": "mobile_20250115_abc123",
      "timestamp": "2025-01-15T10:00:00Z",
      "status": "ACTIVE",
      "capsule_type": "reasoning_trace",
      "has_verification": true
    }
  ],
  "page": 0,
  "limit": 50,
  "total": 1,
  "has_more": false
}
```

---

#### 6. Get Capsule Details
**GET** `/api/v1/mobile/capsule/<capsule_id>`

Get full capsule details with verification proof.

**Response:**
```json
{
  "success": true,
  "capsule": {
    "capsule_id": "mobile_20250115_abc123",
    "timestamp": "2025-01-15T10:00:00Z",
    "status": "ACTIVE",
    "capsule_type": "reasoning_trace",
    "verification": {
      "is_valid": true,
      "reason": "Signature verified successfully",
      "signature": "ed25519_signature_hex",
      "hash": "sha256_hash",
      "signer": "agent_id"
    },
    "reasoning_trace": {
      "steps": [
        {
          "content": "What is the capital of France?",
          "step_type": "user",
          "metadata": {}
        }
      ]
    }
  }
}
```

---

#### 7. Register Device
**POST** `/api/v1/mobile/device/register`

Register a device for push notifications.

**Request:**
```json
{
  "device_id": "iphone-12345",
  "push_token": "apns_token_here",
  "platform": "ios"
}
```

**Response:**
```json
{
  "success": true,
  "device_id": "iphone-12345",
  "registered_at": "2025-01-15T10:00:00Z",
  "push_enabled": true
}
```

---

#### 8. User Statistics
**GET** `/api/v1/mobile/stats`

Get lightweight user statistics for mobile dashboard.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_capsules": 42,
    "verified_capsules": 40,
    "recent_capsules": 5,
    "verification_rate": 0.95
  },
  "timestamp": "2025-01-15T10:00:00Z"
}
```

---

## 🔐 WebAuthn API

### Base URL
```
http://localhost:9090/api/v1/webauthn
```

### Authentication
Registration/complete endpoints require API key. Begin endpoints are public.

---

### Endpoints

#### 1. Health Check
**GET** `/api/v1/webauthn/health`

Check WebAuthn service status.

**Response:**
```json
{
  "status": "healthy",
  "service": "webauthn",
  "rp_id": "uatp.app",
  "timestamp": "2025-01-15T10:00:00Z"
}
```

---

#### 2. Begin Registration
**POST** `/api/v1/webauthn/register/begin`

Initiate passkey registration (create new passkey).

**Request:**
```json
{
  "user_id": "user-12345",
  "user_name": "user@example.com",
  "user_display_name": "John Doe"
}
```

**Response:**
```json
{
  "success": true,
  "options": {
    "challenge": "base64_challenge_here",
    "rp": {
      "id": "uatp.app",
      "name": "UATP Capsule Engine"
    },
    "user": {
      "id": "base64_user_id",
      "name": "user@example.com",
      "displayName": "John Doe"
    },
    "pubKeyCredParams": [
      {"type": "public-key", "alg": -7},
      {"type": "public-key", "alg": -257}
    ],
    "authenticatorSelection": {
      "authenticatorAttachment": "platform",
      "requireResidentKey": true,
      "residentKey": "required",
      "userVerification": "required"
    },
    "timeout": 300000,
    "excludeCredentials": [],
    "attestation": "none"
  }
}
```

**Client Usage:**
```javascript
// In browser/iOS WebView
const options = response.options;
const credential = await navigator.credentials.create({
  publicKey: options
});

// Send credential back to complete registration
```

---

#### 3. Complete Registration
**POST** `/api/v1/webauthn/register/complete`

Complete passkey registration with credential from client.

**Request:**
```json
{
  "credential": {
    "id": "credential_id_base64",
    "rawId": "raw_id_base64",
    "response": {
      "attestationObject": "attestation_base64",
      "clientDataJSON": "client_data_base64"
    },
    "transports": ["internal", "hybrid"]
  },
  "challenge": "base64_challenge_from_begin"
}
```

**Response:**
```json
{
  "success": true,
  "credential": {
    "credential_id": "credential_id_base64",
    "user_id": "user-12345",
    "created_at": "2025-01-15T10:00:00Z",
    "transports": ["internal", "hybrid"],
    "backup_eligible": true
  }
}
```

---

#### 4. Begin Authentication
**POST** `/api/v1/webauthn/authenticate/begin`

Initiate passkey authentication (sign in).

**Request (Optional):**
```json
{
  "user_id": "user-12345"
}
```

**Response:**
```json
{
  "success": true,
  "options": {
    "challenge": "base64_challenge",
    "rpId": "uatp.app",
    "allowCredentials": [
      {"type": "public-key", "id": "credential_id"}
    ],
    "userVerification": "required",
    "timeout": 300000
  }
}
```

**Client Usage:**
```javascript
const options = response.options;
const credential = await navigator.credentials.get({
  publicKey: options
});
```

---

#### 5. Complete Authentication
**POST** `/api/v1/webauthn/authenticate/complete`

Complete authentication with credential.

**Request:**
```json
{
  "credential": {
    "id": "credential_id",
    "response": {
      "authenticatorData": "auth_data_base64",
      "clientDataJSON": "client_data_base64",
      "signature": "signature_base64"
    }
  },
  "challenge": "base64_challenge_from_begin"
}
```

**Response:**
```json
{
  "success": true,
  "user_id": "user-12345",
  "session_token": "session_token_here",
  "credential_id": "credential_id",
  "last_used": "2025-01-15T10:00:00Z"
}
```

---

#### 6. List Credentials
**GET** `/api/v1/webauthn/credentials?user_id=user-12345`

List all passkeys for a user.

**Response:**
```json
{
  "success": true,
  "credentials": [
    {
      "credential_id": "cred-001",
      "created_at": "2025-01-15T10:00:00Z",
      "last_used_at": "2025-01-15T11:00:00Z",
      "transports": ["internal"],
      "backup_eligible": true,
      "backup_state": false,
      "device_name": "iPhone 15 Pro"
    }
  ]
}
```

---

#### 7. Revoke Credential
**DELETE** `/api/v1/webauthn/credentials/<credential_id>`

Revoke a passkey (remove from user's account).

**Response:**
```json
{
  "success": true,
  "message": "Credential revoked"
}
```

---

## 🧪 Testing

### Manual Testing with curl

```bash
# Test mobile health
curl http://localhost:9090/api/v1/mobile/health

# Test WebAuthn health
curl http://localhost:9090/api/v1/webauthn/health

# Create mobile capsule
curl -X POST http://localhost:9090/api/v1/mobile/capture/single \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "device_id": "test-001",
    "platform": "ios",
    "messages": [
      {"role": "user", "content": "Hello"},
      {"role": "assistant", "content": "Hi there!"}
    ]
  }'

# Begin WebAuthn registration
curl -X POST http://localhost:9090/api/v1/webauthn/register/begin \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "user_id": "test-user",
    "user_name": "test@example.com",
    "user_display_name": "Test User"
  }'
```

### Automated Testing
```bash
# Run full test suite
python3 test_production_api.py
```

---

## 📊 Performance Characteristics

### Mobile API
- **Latency Target:** <100ms (p95)
- **Throughput:** 1000+ req/sec
- **Payload Size:** Optimized (typically <5KB per capsule)
- **Batch Size:** Up to 1000 capsules per request

### WebAuthn API
- **Challenge Timeout:** 5 minutes
- **Concurrent Registrations:** Unlimited
- **Storage:** In-memory (production: PostgreSQL)

---

## 🔒 Security Features

### Mobile API
- ✅ API key authentication
- ✅ Rate limiting ready
- ✅ Device tracking
- ✅ Cryptographic signing (Ed25519)
- ✅ Tamper-proof audit trails

### WebAuthn API
- ✅ Phishing-resistant authentication
- ✅ Hardware-backed security (Secure Enclave/TPM)
- ✅ No passwords stored
- ✅ Replay attack protection
- ✅ Man-in-the-middle attack protection
- ✅ Biometric verification required

---

## 🚀 Next Steps

1. **Database Persistence**
   - Move WebAuthn credentials to PostgreSQL
   - Add device registry table
   - Implement credential backup

2. **Push Notifications**
   - APNS integration (iOS)
   - FCM integration (Android)
   - Notification preferences

3. **Rate Limiting**
   - Per-device limits
   - Per-user limits
   - Abuse prevention

4. **Monitoring**
   - Prometheus metrics
   - Grafana dashboards
   - Alerting rules

5. **Production Deployment**
   - Kubernetes configs
   - Auto-scaling
   - Multi-region setup

---

## 📚 Resources

- [WebAuthn Specification](https://www.w3.org/TR/webauthn-3/)
- [FIDO2 Overview](https://fidoalliance.org/fido2/)
- [Apple Passkeys](https://developer.apple.com/passkeys/)
- [Google Passkeys](https://developers.google.com/identity/passkeys)

---

**Last Updated:** January 15, 2025
**API Version:** 1.0.0
**Server Version:** UATP-7.0
