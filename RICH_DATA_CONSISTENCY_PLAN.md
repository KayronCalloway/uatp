# Rich Data Consistency Implementation Plan

**Date:** December 14, 2025
**Status:** In Progress
**Goal:** Ensure rich data format is consistent across SDK, Capture, and Frontend

---

## 🎯 Current State

### ✅ DONE: SDK (Python)
- Rich data models: `DataSource`, `RiskAssessment`, `Alternative`, `ReasoningStep`
- `certify_rich()` method
- `record_outcome()` method
- Working example creating rich capsules

### ⚠️  TODO: Live Capture Mechanisms
- Claude Code capture
- Antigravity/Gemini capture
- Need to output rich format matching SDK

### ⚠️  TODO: Frontend (React/TypeScript)
- TypeScript types for rich data
- UI components to display:
  - Data sources with provenance
  - Risk assessments
  - Alternatives evaluated
  - Plain language summaries
  - Outcomes

---

## 📋 Implementation Checklist

### Phase 1: TypeScript Types (Frontend)
- [ ] Add `DataSource` interface
- [ ] Add `RiskAssessment` interface
- [ ] Add `Alternative` interface
- [ ] Add `ReasoningStep` interface (enhanced)
- [ ] Add `Outcome` interface
- [ ] Add `PlainLanguageSummary` interface
- [ ] Update `AnyCapsule` to include rich fields

### Phase 2: Frontend UI Components
- [ ] `DataSourcesCard` - Show data provenance
- [ ] `RiskAssessmentCard` - Show risk analysis
- [ ] `AlternativesCard` - Show alternatives considered
- [ ] `PlainLanguageCard` - Show plain language summary
- [ ] `OutcomeCard` - Show actual outcomes
- [ ] Update `CapsuleDetail` to use new components

### Phase 3: Live Capture Updates
- [ ] Update `claude_code_capture.py` to generate rich format
- [ ] Update `antigravity_hook.py` to generate rich format
- [ ] Add helper functions for common data source types
- [ ] Add confidence calculation helpers

### Phase 4: Backend API Updates (if needed)
- [ ] Ensure API returns all rich fields
- [ ] Add `/capsules/{id}/outcome` endpoint
- [ ] Update schemas to match rich format

### Phase 5: Testing
- [ ] Test SDK → Backend → Frontend flow
- [ ] Test Capture → Backend → Frontend flow
- [ ] Verify all rich data displays correctly
- [ ] Test outcome recording end-to-end

---

## 🔧 Technical Details

### Rich Data Schema (JSON)

```json
{
  "capsule_id": "cap_abc123",
  "type": "reasoning_trace",
  "payload": {
    "task": "...",
    "decision": "...",

    "reasoning_chain": [
      {
        "step": 1,
        "action": "...",
        "confidence": 0.95,
        "reasoning": "...",
        "plain_language": "...",

        "data_sources": [
          {
            "source": "Experian Credit Bureau",
            "value": 720,
            "timestamp": "...",
            "api_endpoint": "...",
            "verification": {...}
          }
        ],

        "alternatives_evaluated": [
          {
            "option": "...",
            "score": 0.85,
            "why_not_chosen": "..."
          }
        ],

        "decision_criteria": [...],
        "confidence_basis": "..."
      }
    ],

    "risk_assessment": {
      "probability_correct": 0.87,
      "probability_wrong": 0.13,
      "expected_value": 280,
      "value_at_risk_95": 22500,
      "safeguards": [...],
      "failure_modes": [...]
    },

    "alternatives_considered": [...],

    "plain_language_summary": {
      "decision": "...",
      "why": "...",
      "key_factors": [...],
      "what_if_different": "...",
      "your_rights": "..."
    },

    "outcome": {
      "occurred": true,
      "result": "successful",
      "timestamp": "...",
      "ai_was_correct": true,
      "financial_impact": 2500,
      "customer_satisfaction": 4.5
    }
  }
}
```

---

## 🎨 Frontend Design Mockups

### Capsule Detail View (Enhanced)

```
┌─────────────────────────────────────────────────────┐
│ 🏛️ Capsule: cap_abc123                              │
│ Status: ✅ SEALED | Data Richness: Court-Admissible │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 📊 Decision Summary                                  │
│                                                       │
│ Task: Approve auto loan application                  │
│ Decision: Approved: $50,000 at 6.5% APR             │
│ Confidence: 87%                                       │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 🔍 Data Sources (3)                     [Expand ▼]  │
├─────────────────────────────────────────────────────┤
│ 1. Experian Credit Bureau                            │
│    Value: 720 (credit score)                         │
│    Verified: ✅ Cross-checked with TransUnion         │
│    API: https://api.experian.com/v3/...             │
│    Time: 2025-12-14 15:30:12                         │
│                                                       │
│ 2. Income Verification Service                       │
│    Value: $85,000/year                               │
│    Verified: ✅ With employer (TechCorp Inc)          │
│    ...                                                │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ ⚖️ Alternatives Considered (3)          [Expand ▼]  │
├─────────────────────────────────────────────────────┤
│ ✓ $50k @ 6.5% (Selected)               Score: 0.92  │
│ ✗ $40k @ 6.0%                           Score: 0.88  │
│   Why not: User requested $50k                       │
│ ✗ $50k @ 7.5%                           Score: 0.75  │
│   Why not: Rate too high for credit score           │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 📊 Risk Assessment                      [Expand ▼]  │
├─────────────────────────────────────────────────────┤
│ Probability Correct: 87%                             │
│ Expected Value: +$280                                 │
│ Value at Risk (95%): -$22,500                         │
│                                                       │
│ Safeguards (4):                                       │
│ ✅ Income verified with employer                      │
│ ✅ Vehicle title held as collateral                   │
│ ✅ Gap insurance required                             │
│ ✅ Monthly payment highly affordable (13% of income)  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 💬 Plain Language Summary               [Expand ▼]  │
├─────────────────────────────────────────────────────┤
│ ✨ For the user:                                     │
│                                                       │
│ "We approved your loan because you have excellent    │
│  credit (720), stable income, and manageable debts." │
│                                                       │
│ Key Factors:                                          │
│ • Credit score: 720/850 (excellent)                  │
│ • Income: $85k/year, verified                        │
│ • Debts: Only 28% of income (very good)              │
│                                                       │
│ Your Rights: You can request detailed explanation... │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 📈 Outcome (Recorded 30 days later)     [Expand ▼]  │
├─────────────────────────────────────────────────────┤
│ Status: ✅ Successful                                 │
│ AI was correct: ✅ Yes                                │
│ Financial impact: +$2,500 (interest earned)          │
│ Customer satisfaction: 4.5/5                          │
│ Notes: Loan fully paid on time                       │
└─────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

```
┌──────────────┐
│   SDK Call   │ → certify_rich(...)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Backend API │ → POST /capsules
└──────┬───────┘         (with rich payload)
       │
       ▼
┌──────────────┐
│  PostgreSQL  │ → Store rich capsule
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Frontend   │ → GET /capsules/{id}
└──────┬───────┘         Display rich data
       │
       ▼
   [User sees court-admissible evidence]
```

---

## 📝 Code Examples

### Frontend TypeScript Types

```typescript
// types/api.ts
export interface DataSource {
  source: string;
  value: any;
  timestamp?: string;
  api_endpoint?: string;
  api_version?: string;
  verification?: {
    cross_checked?: string[];
    values?: any[];
    consensus?: boolean;
  };
}

export interface RiskAssessment {
  probability_correct: number;
  probability_wrong: number;
  expected_value?: number;
  value_at_risk_95?: number;
  safeguards?: string[];
  failure_modes?: Array<{
    scenario: string;
    probability: number;
    mitigation: string;
  }>;
  historical_accuracy?: number;
}

export interface Alternative {
  option: string;
  score?: number;
  why_not_chosen: string;
  data?: Record<string, any>;
}

export interface EnhancedReasoningStep {
  step: number;
  action: string;
  confidence: number;
  reasoning?: string;
  plain_language?: string;
  data_sources?: DataSource[];
  alternatives_evaluated?: Alternative[];
  decision_criteria?: string[];
  confidence_basis?: string;
}

export interface PlainLanguageSummary {
  decision: string;
  why: string;
  key_factors: string[];
  what_if_different?: string;
  your_rights?: string;
}

export interface Outcome {
  occurred: boolean;
  result: 'successful' | 'failed' | 'partial' | 'pending';
  timestamp: string;
  ai_was_correct?: boolean;
  financial_impact?: number;
  customer_satisfaction?: number;
  notes?: string;
}

// Update AnyCapsule
export interface RichCapsule extends AnyCapsule {
  payload: {
    task: string;
    decision: string;
    reasoning_chain: EnhancedReasoningStep[];
    confidence: number;
    risk_assessment?: RiskAssessment;
    alternatives_considered?: Alternative[];
    plain_language_summary?: PlainLanguageSummary;
    outcome?: Outcome;
    metadata: Record<string, any>;
  };
}
```

### Frontend Component Example

```typescript
// components/capsules/RiskAssessmentCard.tsx
export function RiskAssessmentCard({
  riskAssessment
}: {
  riskAssessment: RiskAssessment
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Risk Assessment
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex justify-between">
            <span>Probability Correct:</span>
            <span className="font-semibold text-green-600">
              {(riskAssessment.probability_correct * 100).toFixed(1)}%
            </span>
          </div>

          {riskAssessment.expected_value && (
            <div className="flex justify-between">
              <span>Expected Value:</span>
              <span className="font-semibold">
                ${riskAssessment.expected_value.toLocaleString()}
              </span>
            </div>
          )}

          {riskAssessment.safeguards && (
            <div>
              <h4 className="font-semibold mb-2">Safeguards:</h4>
              <ul className="space-y-1">
                {riskAssessment.safeguards.map((safeguard, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <Shield className="w-4 h-4 text-green-600 mt-0.5" />
                    <span className="text-sm">{safeguard}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

---

## ⏱️ Timeline

**Week 1 (Current):**
- [x] SDK rich data implementation
- [ ] Frontend TypeScript types
- [ ] Basic frontend components

**Week 2:**
- [ ] Live capture updates
- [ ] Full frontend integration
- [ ] End-to-end testing

**Week 3:**
- [ ] Polish & documentation
- [ ] Deploy to production
- [ ] Customer demos

---

## 🎯 Success Criteria

✅ **SDK creates rich capsules** (Done)
⏳ **Capture creates rich capsules** (In Progress)
⏳ **Frontend displays all rich data** (In Progress)
⏳ **End-to-end test passes** (Pending)
⏳ **All data fields visible in UI** (Pending)

---

**Status:** Implementation starting now
**Next Step:** Update frontend TypeScript types
