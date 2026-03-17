# UATP TypeScript SDK

Cryptographic audit trails for AI decisions.

[![npm](https://img.shields.io/npm/v/uatp)](https://www.npmjs.com/package/uatp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
npm install uatp
```

## Quick Start

```typescript
import { UATP } from 'uatp';

const client = new UATP();

// Create and sign a capsule (keys generated locally, never transmitted)
const result = await client.certify({
  task: 'Loan decision',
  decision: 'Approved for $50,000 at 5.2% APR',
  reasoning: [
    { step: 1, thought: 'Credit score 720 (excellent)', confidence: 0.95 },
    { step: 2, thought: 'Debt-to-income 0.28 (acceptable)', confidence: 0.90 }
  ]
});

console.log(result.capsuleId);   // cap_xyz123...
console.log(result.signature);   // Ed25519 signature
console.log(result.publicKey);   // Your verification key
```

## Zero-Trust Architecture

Your private key **never leaves your device**:

```
┌─────────────────────────────┐
│  YOUR DEVICE                │
│  ✓ Private key (derived)    │
│  ✓ ALL signing happens here │
│  ✓ Ed25519 + PBKDF2 480K    │
└──────────────┬──────────────┘
               │ Only hash sent
               ▼
┌─────────────────────────────┐
│  UATP SERVER (optional)     │
│  - Timestamp service        │
│  - Capsule storage          │
└─────────────────────────────┘
```

## Usage Examples

### Basic Usage

```typescript
import { UATP } from 'uatp';

const client = new UATP();

const result = await client.certify({
  task: 'Product recommendation',
  decision: 'Recommended iPhone 15 Pro',
  reasoning: [
    { step: 1, thought: 'User prefers Apple ecosystem', confidence: 0.92 },
    { step: 2, thought: 'Budget matches Pro pricing', confidence: 0.88 }
  ]
});
```

### With Custom Passphrase (Production)

```typescript
const result = await client.certify({
  task: 'Medical diagnosis',
  decision: 'Recommend follow-up tests',
  reasoning: [
    { step: 1, thought: 'Symptoms consistent with condition X', confidence: 0.85 }
  ],
  passphrase: 'your-secure-passphrase',
  deviceBound: false
});
```

### Verify Locally (No Server Needed)

```typescript
const verification = client.verifyLocal(capsule);

if (verification.valid) {
  console.log('Capsule is authentic!');
} else {
  console.log('Verification failed:', verification.errors);
}
```

### Store on Server

```typescript
const result = await client.certify({
  task: 'Insurance claim',
  decision: 'Approved: $5,000',
  reasoning: [...],
  storeOnServer: true
});

console.log(result.proofUrl); // https://...
```

### Retrieve Proof

```typescript
const proof = await client.getProof('cap_abc123');
console.log(proof.payload.task);
console.log(proof.payload.decision);
```

## API Reference

### `new UATP(config?)`

Create a new UATP client.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiKey` | `string` | - | API key for authenticated requests |
| `baseUrl` | `string` | `http://localhost:8000` | UATP server URL |
| `timeout` | `number` | `30000` | Request timeout (ms) |

### `client.certify(options)`

Create a signed capsule.

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `task` | `string` | Yes | Description of the task |
| `decision` | `string` | Yes | The AI's decision |
| `reasoning` | `ReasoningStep[]` | Yes | Reasoning steps |
| `passphrase` | `string` | No | Key encryption passphrase |
| `deviceBound` | `boolean` | No | Derive passphrase from device (default: true) |
| `confidence` | `number` | No | Overall confidence (0-1) |
| `metadata` | `object` | No | Additional metadata |
| `requestTimestamp` | `boolean` | No | Get RFC 3161 timestamp (default: true) |
| `storeOnServer` | `boolean` | No | Store on UATP server (default: false) |

### `client.verifyLocal(capsule)`

Verify a capsule cryptographically without server.

### `client.getProof(capsuleId)`

Retrieve proof from server.

### `client.listCapsules(limit?)`

List capsules from server.

### `client.recordOutcome(capsuleId, outcome)`

Record actual outcome for a decision.

## Framework Integration

### React

```typescript
import { UATP } from 'uatp';
import { useState } from 'react';

function useUATP() {
  const [client] = useState(() => new UATP());

  const certify = async (task: string, decision: string, reasoning: any[]) => {
    return client.certify({ task, decision, reasoning });
  };

  return { certify };
}
```

### Next.js API Route

```typescript
// pages/api/certify.ts
import { UATP } from 'uatp';

const client = new UATP({ baseUrl: process.env.UATP_URL });

export default async function handler(req, res) {
  const result = await client.certify(req.body);
  res.json({ capsuleId: result.capsuleId });
}
```

### Lovable / AI App Builders

```typescript
// In your Lovable-generated app
import { UATP } from 'uatp';

const client = new UATP();

// Audit every AI decision
async function makeDecision(userQuery: string) {
  const aiResponse = await callYourAI(userQuery);

  // Create audit trail
  const proof = await client.certify({
    task: userQuery,
    decision: aiResponse.decision,
    reasoning: aiResponse.steps.map((s, i) => ({
      step: i + 1,
      thought: s.thought,
      confidence: s.confidence
    }))
  });

  return { ...aiResponse, proofId: proof.capsuleId };
}
```

## Security

- **Ed25519** signatures (128-bit security)
- **PBKDF2-HMAC-SHA256** key derivation (480,000 iterations)
- **SHA-256** content hashing
- Keys derived from passphrase, never stored in plaintext
- Optional **RFC 3161** timestamps from external authority

## License

MIT
