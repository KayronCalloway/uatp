# Rich Capsule Capture Guide

## Overview

Your frontend is **fully ready** to display rich reasoning metadata. The capture system has been updated to support:

- ✅ Per-step confidence scores
- ✅ Uncertainty source tracking
- ✅ Measurement data
- ✅ Alternatives considered
- ✅ Step dependencies
- ✅ Confidence methodology

## What Was Fixed

### Problem
- Frontend expected rich metadata (confidence, measurements, uncertainty, etc.)
- Backend was capturing simple string steps instead of rich objects
- API uses **PostgreSQL** not SQLite for production data

### Solution
Created rich capture helper at `src/utils/rich_capsule_creator.py`:
- `RichReasoningStep` class with all metadata fields
- Helper functions for easy capsule creation
- Direct PostgreSQL import capability

## How to Create Rich Capsules

### Method 1: Using the Helper Class

```python
from src.utils.rich_capsule_creator import RichReasoningStep, create_rich_reasoning_capsule

# Create rich reasoning steps
steps = [
    RichReasoningStep(
        step=1,
        reasoning="Analyzed performance requirements",
        confidence=0.95,
        operation="analysis",
        confidence_basis="user requirements",
        measurements={"query_time_ms": 45, "throughput": 25000},
        alternatives_considered=["Option A", "Option B"]
    ),
    RichReasoningStep(
        step=2,
        reasoning="Evaluated trade-offs",
        confidence=0.87,
        operation="decision",
        uncertainty_sources=["Limited data", "External factors"],
        alternatives_considered=["Approach X", "Approach Y"],
        depends_on_steps=[1]
    )
]

# Create capsule
capsule = create_rich_reasoning_capsule(
    capsule_id="caps_2025_12_05_example",
    prompt="Your prompt here",
    reasoning_steps=steps,
    final_answer="Your conclusion",
    overall_confidence=0.92,
    confidence_methodology={
        "method": "weakest_critical_link",
        "critical_path_steps": [2],
        "explanation": "Confidence limited by step 2 uncertainty"
    }
)
```

### Method 2: Quick Import Script

Use the provided helper script:

```bash
./add_rich_capsule_to_postgres.sh
```

This creates a demo capsule with full metadata that you can view in the frontend.

## Frontend Display

Navigate to `http://localhost:3000`:
1. Click **Capsules** in sidebar
2. Find capsule `caps_2025_12_05_pg_rich_001`
3. Click to view details

You'll see:
- **Per-step confidence** with color coding (green/blue/yellow/red)
- **Measurements** in blue boxes with metrics
- **Uncertainty sources** in yellow warning boxes
- **Alternatives considered** in purple boxes
- **Confidence methodology** explaining how overall confidence was calculated

## Rich Metadata Fields

### Required
- `step_id`: Step number
- `reasoning`: The reasoning text
- `confidence`: Score from 0.0 to 1.0
- `operation`: Type (analysis, decision, measurement, etc.)

### Optional
- `confidence_basis`: How confidence was determined ("measured", "estimated", etc.)
- `measurements`: Dict of measured values
- `uncertainty_sources`: List of uncertainty factors
- `alternatives_considered`: List of options evaluated
- `depends_on_steps`: List of prerequisite step IDs
- `attribution_sources`: Who/what contributed

## Database Note

**Important**: The API uses **PostgreSQL** (`uatp_capsule_engine` database), not SQLite.

- SQLite file: `uatp_dev.db` (for local testing only)
- Production: PostgreSQL at `localhost:5432/uatp_capsule_engine`

Always add capsules to PostgreSQL for them to appear in the API/frontend.

## Files Created

1. `src/utils/rich_capsule_creator.py` - Rich capsule creation helpers
2. `create_rich_demo_capsules.py` - Demo capsule generator
3. `add_rich_capsule_to_postgres.sh` - Quick import script
4. `RICH_CAPTURE_GUIDE.md` - This guide

## Next Steps

To capture rich metadata in your live capture system:
1. Import `RichReasoningStep` in your capture code
2. Build steps with full metadata as you reason
3. Store to PostgreSQL (not SQLite)
4. Frontend will automatically display all the rich data

The frontend is ready - just feed it rich capsules!
