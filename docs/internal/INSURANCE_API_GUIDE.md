# UATP Insurance API - Complete Guide

**AI Liability Insurance for the Future**

The UATP Insurance API provides comprehensive AI liability coverage through cryptographically-verified capsule chains. This enables AI assistants to operate with real-world permissions by making their decisions insurable.

---

##  Core Concept

**Problem:** AI assistants are sandboxed because their decisions aren't auditable or insurable.

**Solution:** UATP capsules create cryptographic audit trails that can be verified for insurance underwriting, allowing AI to gain real permissions for:
- Medical decisions
- Financial transactions
- Legal operations
- Autonomous vehicles
- Content moderation

**Revenue Model:** Insurance premiums based on risk assessment of capsule chains.

---

##  API Overview

**Base URL:** `https://api.uatp.app/api/v1/insurance`

**Authentication:** API key required for all endpoints

**Rate Limits:**
- Risk Assessment: 10 requests/minute
- Policy Operations: 30 requests/minute
- Claims Operations: 20 requests/minute

---

##  Risk Assessment

### POST `/risk-assessment`

Analyze a capsule chain to determine insurability and premium.

**Request:**
```json
{
  "capsule_chain": [
    {
      "capsule_id": "cap_abc123",
      "messages": [...],
      "provider": "anthropic",
      "timestamp": "2025-01-06T10:00:00Z",
      "signature": "..."
    }
  ],
  "decision_category": "medical",
  "requested_coverage": 100000,
  "user_id": "user_123"
}
```

**Decision Categories:**
- `medical` - Healthcare decisions (highest risk)
- `financial` - Financial transactions
- `legal` - Legal advice/operations
- `autonomous_vehicle` - Self-driving decisions
- `content_moderation` - Content filtering
- `customer_service` - Customer interactions
- `creative` - Creative work
- `information_retrieval` - Information lookup (lowest risk)

**Response:**
```json
{
  "assessment": {
    "risk_score": 0.23,
    "risk_level": "low",
    "confidence": 0.87,
    "premium_estimate": "$50.00/month",
    "coverage_recommended": "$100,000",
    "policy_term_months": 12
  },
  "factors": [
    {
      "name": "chain_integrity",
      "score": 0.05,
      "weight": 0.30,
      "description": "Cryptographic verification of capsule chain",
      "details": {
        "valid_signatures": 10,
        "signature_rate": 1.0,
        "valid_linkage": 9,
        "tampering_detected": false
      }
    },
    {
      "name": "reasoning_transparency",
      "score": 0.15,
      "weight": 0.20,
      "description": "Depth and quality of AI reasoning trails",
      "details": {
        "reasoning_rate": 0.9,
                "average_depth": 3.2,
        "evidence_citations": 8
      }
    }
  ],
  "conditions": [
    "All AI decisions must be captured in UATP capsules",
    "Capsule chain must be verifiable upon claim",
    "Human oversight required for high-stakes decisions"
  ],
  "exclusions": [
    "Intentional misuse or manipulation of AI systems",
    "Decisions made without proper capsule documentation"
  ]
}
```

**Risk Levels:**
- `very_low` (0.00-0.15) - Minimal risk, lowest premiums
- `low` (0.15-0.30) - Low risk, affordable premiums
- `medium` (0.30-0.50) - Moderate risk, standard premiums
- `high` (0.50-0.70) - High risk, elevated premiums
- `very_high` (0.70-0.85) - Very high risk, maximum premiums
- `uninsurable` (0.85-1.00) - Too risky to insure

**Risk Factors Analyzed:**

1. **Chain Integrity (30% weight)**
   - Cryptographic signature validation
   - Chain linkage verification
   - Tampering detection
   - Timestamp consistency

2. **Reasoning Transparency (20% weight)**
   - Presence of reasoning steps
   - Depth of explanation
   - Evidence citations
   - Intermediate conclusions

3. **Provider Reliability (15% weight)**
   - AI provider track record
   - Known issues or recalls
   - Model version maturity

4. **Decision Stakes (15% weight)**
   - Decision category impact
   - Coverage amount requested

5. **Audit Completeness (10% weight)**
   - Presence of required metadata
   - Timestamp completeness
   - User/provider information

6. **Historical Performance (10% weight)**
   - User's past verification rate
   - Previous claims history

---

##  Policy Management

### POST `/policies`

Create a new insurance policy.

**Request:**
```json
{
  "user_id": "user_123",
  "user_name": "Dr. Jane Smith",
  "user_email": "jane@example.com",
  "organization": "Health AI Clinic",
  "contact_phone": "+1-555-0100",

  "coverage_amount": 100000,
  "decision_category": "medical",
  "deductible": 1000,
  "term_months": 12,

  "payment_method_id": "pm_stripe_123",
  "auto_activate": true
}
```

**Response:**
```json
{
  "policy_id": "POL-A1B2C3D4E5F6",
  "status": "active",
  "holder": {
    "user_id": "user_123",
    "name": "Dr. Jane Smith",
    "email": "jane@example.com"
  },
  "terms": {
    "coverage_amount": 100000,
    "deductible": 1000,
    "premium_monthly": 50.00,
    "term_months": 12,
    "decision_category": "medical",
    "risk_level": "low"
  },
  "created_at": "2025-01-06T10:00:00Z"
}
```

### GET `/policies`

List user's policies.

**Query Parameters:**
- `user_id` - Filter by user (required)
- `status` - Filter by status (optional)
- `limit` - Maximum results (default: 100)

**Response:**
```json
{
  "policies": [
    {
      "policy_id": "POL-A1B2C3D4E5F6",
      "status": "active",
      "holder": {
        "user_id": "user_123",
        "name": "Dr. Jane Smith"
      },
      "coverage_amount": 100000,
      "premium_monthly": 50.00,
      "created_at": "2025-01-06T10:00:00Z",
      "expires_at": "2026-01-06T10:00:00Z",
      "claims_filed": 1,
      "total_paid_out": 5000
    }
  ],
  "count": 1
}
```

### GET `/policies/{policy_id}`

Get detailed policy information.

**Response:**
```json
{
  "policy_id": "POL-A1B2C3D4E5F6",
  "status": "active",
  "holder": {
    "user_id": "user_123",
    "name": "Dr. Jane Smith",
    "email": "jane@example.com",
    "organization": "Health AI Clinic"
  },
  "terms": {
    "coverage_amount": 100000,
    "deductible": 1000,
    "premium_monthly": 50.00,
    "term_months": 12,
    "decision_category": "medical",
    "risk_level": "low",
    "conditions": [...],
    "exclusions": [...],
    "max_claims_per_year": 3
  },
  "coverage_status": {
    "claims_filed": 1,
    "total_paid_out": 5000,
    "remaining_coverage": 95000
  },
  "dates": {
    "created_at": "2025-01-06T10:00:00Z",
    "activated_at": "2025-01-06T10:05:00Z",
    "expires_at": "2026-01-06T10:00:00Z",
    "next_payment_due": "2025-02-06T10:00:00Z"
  }
}
```

### PUT `/policies/{policy_id}/renew`

Renew an expiring policy.

**Request:**
```json
{
  "term_months": 12
}
```

**Response:**
```json
{
  "policy_id": "POL-A1B2C3D4E5F6",
  "status": "active",
  "expires_at": "2027-01-06T10:00:00Z",
  "message": "Policy renewed successfully"
}
```

### PUT `/policies/{policy_id}/cancel`

Cancel a policy.

**Request:**
```json
{
  "reason": "No longer needed",
  "refund_prorated": true
}
```

**Response:**
```json
{
  "policy_id": "POL-A1B2C3D4E5F6",
  "status": "cancelled",
  "cancelled_at": "2025-01-06T15:00:00Z",
  "cancellation_reason": "No longer needed",
  "message": "Policy cancelled successfully"
}
```

---

##  Claims Processing

### POST `/claims`

File a new insurance claim.

**Request:**
```json
{
  "policy_id": "POL-A1B2C3D4E5F6",
  "claim_type": "ai_error",
  "claimed_amount": 5000,

  "capsule_chain": [...],
  "incident_description": "AI recommended incorrect medication dosage",
  "incident_date": "2025-01-05T14:30:00Z",
  "harm_description": "Patient experienced adverse reaction",
  "financial_impact": 5000,
  "supporting_documents": ["doc_123.pdf", "lab_results.pdf"],
  "witness_statements": ["Attending physician statement"]
}
```

**Claim Types:**
- `ai_error` - AI made incorrect decision
- `ai_harm` - AI decision caused harm
- `data_breach` - Privacy violation
- `bias_discrimination` - Discriminatory outcome
- `system_failure` - Technical failure
- `other` - Other issues

**Response:**
```json
{
  "claim_id": "CLM-X1Y2Z3A4B5C6",
  "policy_id": "POL-A1B2C3D4E5F6",
  "status": "submitted",
  "claim_type": "ai_error",
  "claimed_amount": 5000,
  "submitted_at": "2025-01-06T10:00:00Z",
  "message": "Claim submitted successfully and under review"
}
```

**Claim Processing Workflow:**

1. **Submitted** - Initial submission
2. **Under Review** - Automated verification of capsule chain
3. **Investigating** - Manual investigation (if needed)
4. **Approved** - Claim approved, payout processed
5. **Paid** - Payout completed
6. **Denied** - Claim denied (can be appealed)

### GET `/claims`

List insurance claims.

**Query Parameters:**
- `policy_id` - Filter by policy (optional)
- `user_id` - Filter by user (optional)
- `status` - Filter by status (optional)
- `limit` - Maximum results (default: 100)

**Response:**
```json
{
  "claims": [
    {
      "claim_id": "CLM-X1Y2Z3A4B5C6",
      "policy_id": "POL-A1B2C3D4E5F6",
      "status": "paid",
      "claim_type": "ai_error",
      "claimed_amount": 5000,
      "approved_amount": 5000,
      "submitted_at": "2025-01-06T10:00:00Z",
      "resolved_at": "2025-01-08T16:00:00Z"
    }
  ],
  "count": 1
}
```

### GET `/claims/{claim_id}`

Get detailed claim information.

**Response:**
```json
{
  "claim_id": "CLM-X1Y2Z3A4B5C6",
  "policy_id": "POL-A1B2C3D4E5F6",
  "status": "paid",
  "claim_type": "ai_error",
  "claimed_amount": 5000,
  "approved_amount": 5000,
  "evidence": {
    "incident_description": "AI recommended incorrect medication dosage",
    "incident_date": "2025-01-05T14:30:00Z",
    "harm_description": "Patient experienced adverse reaction",
    "financial_impact": 5000,
    "chain_length": 10
  },
  "investigation": {
    "chain_verified": true,
    "fault_party": "ai",
    "recommended_payout": 5000,
    "findings": "Chain verification passed. Fault party: ai. Confidence: 0.85"
  },
  "dates": {
    "submitted_at": "2025-01-06T10:00:00Z",
    "reviewed_at": "2025-01-06T10:15:00Z",
    "resolved_at": "2025-01-08T16:00:00Z"
  },
  "payout_transaction_id": "txn_abc123def456",
  "notes": [
    {
      "timestamp": "2025-01-06T10:00:00Z",
      "author": "system",
      "note": "Claim submitted and awaiting review"
    },
    {
      "timestamp": "2025-01-08T16:00:00Z",
      "author": "system",
      "note": "Payout processed: $5,000. Transaction: txn_abc123def456"
    }
  ]
}
```

### PUT `/claims/{claim_id}/appeal`

Appeal a denied claim.

**Request:**
```json
{
  "appeal_reason": "Additional evidence provided showing AI was at fault",
  "additional_evidence": {
    "expert_opinion": "expert_analysis.pdf",
    "additional_capsules": [...]
  }
}
```

**Response:**
```json
{
  "claim_id": "CLM-X1Y2Z3A4B5C6",
  "status": "investigating",
  "message": "Appeal submitted successfully and under review"
}
```

---

##  Pricing

### Base Premium Rates

**Per $1,000 of coverage per month:**

| Risk Level | Rate |
|------------|------|
| Very Low | $0.50 |
| Low | $1.00 |
| Medium | $2.50 |
| High | $5.00 |
| Very High | $10.00 |

### Decision Category Multipliers

| Category | Multiplier |
|----------|------------|
| Medical | 3.0x |
| Autonomous Vehicle | 2.8x |
| Financial | 2.5x |
| Legal | 2.5x |
| Content Moderation | 1.5x |
| Customer Service | 1.2x |
| Creative | 1.0x |
| Information Retrieval | 1.0x |

### Example Calculations

**Medical AI ($100k coverage, Low risk):**
```
Base: ($100k / $1k) × $1.00 = $100/month
Medical multiplier: $100 × 3.0 = $300/month
```

**Customer Service AI ($50k coverage, Very Low risk):**
```
Base: ($50k / $1k) × $0.50 = $25/month
Customer service multiplier: $25 × 1.2 = $30/month
```

---

##  Authentication

All endpoints require API key authentication.

**Header:**
```
Authorization: Bearer YOUR_API_KEY
```

**Example:**
```bash
curl -X POST https://api.uatp.app/api/v1/insurance/risk-assessment \
  -H "Authorization: Bearer sk_prod_abc123def456" \
  -H "Content-Type: application/json" \
  -d '{"capsule_chain": [...], "decision_category": "medical"}'
```

---

##  Error Handling

**Standard Error Response:**
```json
{
  "error": "Policy not found",
  "code": "POLICY_NOT_FOUND",
  "details": {
    "policy_id": "POL-INVALID"
  }
}
```

**HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid/missing API key)
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

**Common Errors:**
- `INVALID_CAPSULE_CHAIN` - Capsule chain verification failed
- `POLICY_NOT_ELIGIBLE` - Policy cannot be used for claim
- `COVERAGE_EXHAUSTED` - Policy coverage limit reached
- `UNINSURABLE_RISK` - Risk score too high to insure

---

##  Webhooks (Coming Soon)

Subscribe to real-time events:

- `policy.created`
- `policy.activated`
- `policy.renewed`
- `policy.cancelled`
- `claim.submitted`
- `claim.approved`
- `claim.denied`
- `claim.paid`
- `payment.succeeded`
- `payment.failed`

---

##  Testing

**Test Environment:** `https://api-test.uatp.app/api/v1/insurance`

**Test API Key:** Contact support for test credentials

**Test Cards:**
- Success: `4242424242424242`
- Failure: `4000000000000002`

---

##  SDKs

**Python:**
```python
from uatp_insurance import InsuranceClient

client = InsuranceClient(api_key="sk_prod_abc123")

# Risk assessment
assessment = client.assess_risk(
    capsule_chain=capsules,
    decision_category="medical",
    requested_coverage=100000
)

# Create policy
policy = client.create_policy(
    user_id="user_123",
    coverage_amount=100000,
    decision_category="medical"
)

# File claim
claim = client.file_claim(
    policy_id=policy.id,
    capsule_chain=capsules,
    incident_description="..."
)
```

**JavaScript/TypeScript:**
```typescript
import { InsuranceClient } from '@uatp/insurance-sdk';

const client = new InsuranceClient({
  apiKey: 'sk_prod_abc123'
});

// Risk assessment
const assessment = await client.assessRisk({
  capsuleChain: capsules,
  decisionCategory: 'medical',
  requestedCoverage: 100000
});

// Create policy
const policy = await client.createPolicy({
  userId: 'user_123',
  coverageAmount: 100000,
  decisionCategory: 'medical'
});
```

---

## 🆘 Support

**Documentation:** https://docs.uatp.app/insurance

**Support Email:** insurance@uatp.app

**Status Page:** https://status.uatp.app

**Emergency Claims Line:** +1-555-UATP-911

---

**Last Updated:** 2025-01-06
**API Version:** 1.0.0
