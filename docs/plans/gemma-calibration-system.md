# Gemma Calibration System - Implementation Plan

## Problem Statement

We want Gemma to be self-aware of its own reliability. But:
- Model self-assessment is testimony, not proof
- Reflection outputs are `model_generated`, not `verified`
- The value is in **comparing** self-assessment to outcomes over time

## Core Principle

```
Model output ≠ evidence
Model self-assessment ≠ audit
The learning happens in the comparison, not the reflection
```

## What We Have

| Component | Status | Location |
|-----------|--------|----------|
| Gemma → UATP capture | ✓ Working | `src/integrations/ollama_capture.py` |
| Layered capsule format | ✓ Working | `src/core/provenance.py` |
| Ed25519 signing | ✓ Working | `src/security/uatp_crypto_v7.py` |
| `parent_capsule_id` linking | ✓ In DB | `src/models/capsule.py` |
| Outcome tracking fields | ✓ In DB | `outcome_status`, `outcome_metrics`, etc. |
| Contradiction engine | ✓ Working | `src/core/contradiction_engine.py` |

## What We Need to Build

### Phase 1: Epistemic Classification (Day 1)

**Goal:** Every claim explicitly states what kind of claim it is.

Add `EpistemicClass` enum to `src/core/provenance.py`:

```python
class EpistemicClass(str, Enum):
    """What kind of claim is this? Determines how it should be trusted."""

    # Model outputs - NEVER trust without verification
    MODEL_CLAIM = "model_claim"           # Any model assertion
    MODEL_SELF_ASSESSMENT = "model_self_assessment"  # Model evaluating itself

    # Verified by tooling/observation
    TOOL_OBSERVED = "tool_observed"       # We saw it happen (captured event)
    ARTIFACT_HASH = "artifact_hash"       # Verified from file/commit hash
    CRYPTO_SIGNED = "crypto_signed"       # Ed25519/RFC3161 verified

    # External verification
    HUMAN_VERIFIED = "human_verified"     # Human confirmed
    SYSTEM_VERIFIED = "system_verified"   # External system confirmed

    # Outcomes
    MEASURED_OUTCOME = "measured_outcome" # Actual result observed
    INFERRED_OUTCOME = "inferred_outcome" # Outcome inferred from signals
```

**Key insight:** `ProofLevel` tells you HOW something was verified. `EpistemicClass` tells you WHAT KIND of claim it is. Both are needed.

### Phase 2: Self-Assessment Capture (Day 1-2)

**Goal:** After each Gemma response, capture a structured self-assessment as a SEPARATE linked capsule.

#### 2.1 The Self-Assessment Prompt

```python
SELF_ASSESSMENT_PROMPT = """
Review your previous response and provide a structured self-assessment.

DO NOT defend your answer. BE HONEST about limitations.

Respond in this exact JSON format:
{
    "confidence_estimate": 0.0-1.0,
    "grounding_sources": ["list what you based this on"],
    "assumptions_made": ["list assumptions that might be wrong"],
    "uncertainty_areas": ["where you're least sure"],
    "potential_errors": ["what could be wrong"],
    "would_change_if": ["conditions that would change your answer"],
    "verification_needed": ["what should be checked"]
}
"""
```

#### 2.2 Self-Assessment Capsule Structure

```python
{
    "capsule_id": "caps_2026_04_03_123456_gemma4_self",
    "capsule_type": "model_self_assessment",
    "parent_capsule_id": "caps_2026_04_03_123456_gemma4",  # Links to original
    "payload": {
        "schema_version": "2.0_layered",
        "epistemic_class": "model_self_assessment",  # THE KEY FIELD
        "assessment": {
            "confidence_estimate": 0.75,
            "grounding_sources": [...],
            "assumptions_made": [...],
            "uncertainty_areas": [...],
            "potential_errors": [...],
            "verification_needed": [...]
        },
        "layers": {
            "events": [...],
            "evidence": [],  # Empty - this is model output
            "interpretation": {
                "summary": "Self-assessment of response",
                "status": "unverified"  # ALWAYS unverified
            },
            "judgment": {
                "gates_passed": [],
                "court_admissible": false,
                "blockers": ["Self-assessment cannot self-verify"]
            }
        },
        "trust_posture": {
            "provenance_integrity": "low",      # It's model output
            "artifact_verifiability": "low",    # Nothing to verify
            "semantic_alignment": "unknown",
            "decision_completeness": "unknown",
            "risk_calibration": "untested",     # That's what we're measuring
            "legal_reliance_readiness": "not_ready",
            "operational_utility": "medium"     # Useful as a hypothesis
        }
    }
}
```

### Phase 3: Outcome Recording (Day 2-3)

**Goal:** Record what actually happened so we can compare against self-assessment.

#### 3.1 Outcome Types

```python
class OutcomeType(str, Enum):
    # Direct outcomes
    WORKED = "worked"           # The suggestion/code worked
    FAILED = "failed"           # It didn't work
    PARTIALLY_WORKED = "partial" # Some parts worked

    # Indirect signals (inferred from user behavior)
    ACCEPTED = "accepted"       # User used the response
    REJECTED = "rejected"       # User ignored/contradicted
    REFINED = "refined"         # User asked for changes
    ABANDONED = "abandoned"     # User moved on entirely

    # Unknown
    UNKNOWN = "unknown"         # No signal either way
```

#### 3.2 Outcome Capsule Structure

```python
{
    "capsule_id": "caps_2026_04_03_234567_outcome",
    "capsule_type": "measured_outcome",
    "parent_capsule_id": "caps_2026_04_03_123456_gemma4",  # Links to original
    "payload": {
        "schema_version": "2.0_layered",
        "epistemic_class": "measured_outcome",  # OR "human_verified"
        "outcome": {
            "type": "worked",
            "confidence": 0.9,  # How sure we are about the outcome
            "evidence": "Tests passed, code deployed",
            "recorded_by": "human",  # or "system"
            "recorded_at": "2026-04-03T19:00:00Z"
        },
        "linked_capsules": {
            "original_response": "caps_2026_04_03_123456_gemma4",
            "self_assessment": "caps_2026_04_03_123456_gemma4_self"
        },
        "layers": {
            "evidence": [
                {
                    "claim": "Outcome was observed",
                    "verified": true,
                    "proof": "human_verified",
                    "verification_method": "manual_review"
                }
            ]
        }
    }
}
```

### Phase 4: Calibration Queries (Day 3-4)

**Goal:** Compare self-assessments to outcomes and measure calibration.

#### 4.1 Basic Calibration Query

```sql
-- Find capsules with self-assessments AND outcomes
SELECT
    original.capsule_id,
    json_extract(self_assess.payload, '$.assessment.confidence_estimate') as claimed_confidence,
    original.outcome_status,
    original.outcome_metrics
FROM capsules original
JOIN capsules self_assess
    ON self_assess.parent_capsule_id = original.capsule_id
    AND self_assess.capsule_type = 'model_self_assessment'
WHERE original.outcome_status IS NOT NULL
ORDER BY original.timestamp DESC;
```

#### 4.2 Calibration Metrics (calculated AFTER we have data)

```python
@dataclass
class CalibrationMetrics:
    """Calculated from historical comparison, not model output."""

    # Basic calibration
    total_predictions: int
    predictions_with_outcomes: int

    # Confidence calibration
    # "When the model said 80% confident, was it right 80% of the time?"
    confidence_buckets: Dict[str, float]  # {"0.8-0.9": 0.72, ...}
    overconfidence_score: float  # Positive = overconfident

    # Self-assessment accuracy
    # "Did the model correctly identify its uncertainty areas?"
    uncertainty_hit_rate: float  # Flagged uncertainties that were actual errors
    missed_error_rate: float     # Errors in areas model said were certain

    # Per-domain breakdown
    by_topic: Dict[str, "CalibrationMetrics"]
    by_question_type: Dict[str, "CalibrationMetrics"]
```

### Phase 5: Feedback Loop (Day 4-5)

**Goal:** Use calibration data to inform future responses.

#### 5.1 Calibration Context Injection

When Gemma responds, include relevant calibration history:

```python
def build_calibration_context(topic: str, model: str) -> str:
    """Build context about model's historical reliability on this topic."""

    metrics = get_calibration_metrics(model=model, topic=topic)

    if metrics.total_predictions < 10:
        return "Insufficient calibration data for this topic."

    return f"""
CALIBRATION CONTEXT (from {metrics.predictions_with_outcomes} verified outcomes):
- Your historical accuracy on "{topic}": {metrics.accuracy:.0%}
- Your confidence tends to be {metrics.overconfidence_score:+.0%} vs reality
- Common error patterns: {metrics.common_errors[:3]}
- Uncertainty areas you often miss: {metrics.missed_uncertainties[:3]}

Adjust your confidence accordingly.
"""
```

#### 5.2 NOT a feedback loop from self-assessment

The feedback comes from **measured outcomes**, not from the model's self-assessment. The self-assessment is just a hypothesis to be tested.

## File Changes

### New Files

| File | Purpose |
|------|---------|
| `src/core/epistemic.py` | `EpistemicClass` enum and helpers |
| `src/integrations/ollama_self_assessment.py` | Self-assessment prompt and capture |
| `src/integrations/outcome_recorder.py` | CLI/API for recording outcomes |
| `src/calibration/metrics.py` | Calibration calculation |
| `src/calibration/queries.py` | SQL queries for calibration data |

### Modified Files

| File | Changes |
|------|---------|
| `src/core/provenance.py` | Add `epistemic_class` to Claim, Event, Evidence |
| `src/integrations/ollama_capture.py` | Add self-assessment capture after response |
| `src/api/capsules/router_outcomes.py` | Add outcome recording endpoint |

## Implementation Order

```
Day 1:
├── Add EpistemicClass enum to provenance.py
├── Update Claim/Event/Evidence to include epistemic_class
└── Test with existing capsule creation

Day 2:
├── Create self-assessment prompt
├── Add self-assessment capture to ollama_capture.py
├── Create linked capsule with parent_capsule_id
└── Test: Gemma response → self-assessment capsule pair

Day 3:
├── Create outcome recording CLI
├── Add outcome recording API endpoint
├── Test: Record outcomes for existing capsules
└── Verify linking: original → self-assessment → outcome

Day 4:
├── Create calibration queries
├── Build CalibrationMetrics dataclass
├── Test with small dataset (manual outcomes)
└── Verify: metrics match manual calculation

Day 5:
├── Add calibration context injection
├── Test feedback loop with real interactions
├── Document the system
└── Create dashboard view (if time)
```

## Success Criteria

1. **Every capsule has `epistemic_class`** - no ambiguity about what kind of claim it is
2. **Self-assessments are linked** - can query original → self-assessment
3. **Outcomes are recorded** - can query original → outcome
4. **Calibration is measurable** - after N interactions, can calculate accuracy
5. **No false confidence** - system never claims verification it doesn't have

## What This Is NOT

- NOT a "self-auditing system" (model can't audit itself)
- NOT a confidence score generator (those are just more model claims)
- NOT a replacement for human review
- NOT magic - calibration requires data, data requires time

## What This IS

A system that:
1. Captures model claims explicitly labeled as claims
2. Captures model self-assessment explicitly labeled as unverified
3. Records actual outcomes as evidence
4. Compares claims to outcomes over time
5. Learns where the model is calibrated vs. miscalibrated

**The learning happens in the comparison, not the reflection.**
