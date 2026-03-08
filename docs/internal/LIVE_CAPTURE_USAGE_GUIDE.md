# Live Rich Capture Integration - Usage Guide

## Overview

The live capture system now automatically generates **REAL rich metadata** from Claude Code conversations. Every conversation meeting significance criteria will be captured with:

- [OK] **Per-step confidence** calculated from message characteristics
- [OK] **Uncertainty sources** detected from language patterns
- [OK] **Real measurements** (token counts, response times, content metrics)
- [OK] **Alternatives considered** extracted from conversation content
- [OK] **Confidence methodology** explaining overall confidence calculation

## How It Works

### Automatic Capture Flow

```
Claude Code Session
    ↓
Conversation Messages
    ↓
RichCaptureEnhancer.analyze()
    ↓
Rich Metadata Generation
    ↓
PostgreSQL Storage
    ↓
Frontend Display
```

### What Gets Captured

For each message in your conversation, the system automatically:

1. **Calculates Confidence** (0.0-1.0)
   - Base: 0.85 for assistant, 0.70 for user
   - +0.05 for detailed responses (>1000 chars)
   - +0.08 for code examples
   - -0.10 for very short responses (<100 chars)
   - -0.05 for questions (indicating uncertainty)

2. **Detects Uncertainty Sources**
   - Language patterns: "might", "maybe", "possibly", "unclear"
   - Assumptions: "assume", "assuming", "probably"
   - Speculation: "could be", "may be", "seems like"
   - Clarifying questions from assistant

3. **Extracts Measurements**
   - `token_count`: Tokens in message
   - `content_length_chars`: Character count
   - `response_time_seconds`: Time since last message
   - `message_index`: Position in conversation

4. **Identifies Alternatives**
   - "instead of" / "rather than" patterns
   - "alternatively" / "could also" patterns
   - Multiple options presented ("option A", "option B")
   - Different implementation paths

## Usage

### No Code Changes Required

The integration is **automatic**. Just use Claude Code normally:

```bash
# Your conversations are automatically captured with rich metadata
# when they meet significance criteria
```

### Verifying Capture

After a significant Claude Code session:

1. **Check PostgreSQL**
   ```bash
   psql -d uatp_capsule_engine -c \
     "SELECT capsule_id, timestamp FROM capsules ORDER BY timestamp DESC LIMIT 5;"
   ```

2. **Check via API**
   ```bash
   # Get latest capsule
   curl http://localhost:8000/capsules?per_page=1 | jq '.capsules[0].capsule_id'

   # Get full details
   curl http://localhost:8000/capsules/caps_2025_12_05_xxxx | jq '.payload.reasoning_steps[0]'
   ```

3. **Check Frontend**
   - Navigate to: http://localhost:3000
   - Click **Capsules** → Browse → Select recent capsule
   - Look for:
     - Per-step confidence badges (green/blue/yellow/red)
     - Blue measurement boxes
     - Yellow uncertainty warning boxes
     - Purple alternatives boxes

## Expected Output

### Example Rich Step

```json
{
  "step_id": 1,
  "reasoning": "Analyzed user requirements for database performance...",
  "confidence": 0.92,
  "operation": "analysis",
  "confidence_basis": "measured characteristics",
  "measurements": {
    "token_count": 145,
    "content_length_chars": 687,
    "response_time_seconds": 2.3,
    "message_index": 3
  },
  "uncertainty_sources": null,
  "alternatives_considered": ["SQLAlchemy ORM", "asyncpg raw SQL"]
}
```

### Confidence Color Coding

-  **Green (0.9-1.0)**: High confidence - measured data, code provided
-  **Blue (0.75-0.89)**: Medium-high confidence - detailed analysis
-  **Yellow (0.6-0.74)**: Medium confidence - some uncertainty
-  **Red (0.0-0.59)**: Low confidence - speculative or unclear

## Real vs Demo Data

### How to Tell Them Apart

**Demo Capsules** (for testing):
- Capsule IDs like: `caps_2025_12_05_pg_rich_001`
- Created by manual scripts
- Perfect example data

**Real Capsules** (from live capture):
- Capsule IDs like: `caps_2025_12_05_143052_a3b4c5d6`
- Timestamp in ID matches conversation time
- Imperfect but REAL confidence/measurements

### What's Real in Live Capture

[OK] **Definitely Real**:
- Token counts (from API responses)
- Content lengths (measured)
- Response times (calculated)
- Message indices (counted)
- Uncertainty detection (pattern matching)
- Alternative detection (keyword analysis)

[WARN] **Estimated but Grounded**:
- Confidence scores (calculated from real characteristics)
- Confidence basis (derived from analysis)
- Operation types (inferred from content)

## Troubleshooting

### Capsule Not Appearing in Frontend

1. **Check database**: `psql -d uatp_capsule_engine -c "SELECT COUNT(*) FROM capsules;"`
2. **Verify API**: `curl http://localhost:8000/capsules`
3. **Check API logs**: Look for " Created RICH capsule" message
4. **Restart frontend**: `cd frontend && npm run dev`

### Missing Rich Metadata

If you see simple strings instead of rich objects:

1. **Check PostgreSQL**: Live capture requires PostgreSQL (not SQLite)
2. **Verify DATABASE_URL**: Should start with `postgresql://`
3. **Check dependencies**: `pip install asyncpg`
4. **Look for errors**: Check capture logs for database connection issues

### No Measurements Appearing

Common reasons:
- Short conversation (<3 messages) - limited timing data
- User messages - fewer measurements than assistant messages
- First message - no response_time_seconds available

This is normal. Not every step will have all measurement types.

## Integration Points

### Live Capture System

**File**: `/Users/kay/uatp-capsule-engine/src/live_capture/claude_code_capture.py`

The `ClaudeCodeCaptureSession` class automatically:
- Detects significant conversations
- Calls `RichCaptureEnhancer.create_capsule_from_session_with_rich_metadata()`
- Stores to PostgreSQL with all metadata

### Rich Metadata Analyzer

**File**: `/Users/kay/uatp-capsule-engine/src/live_capture/rich_capture_integration.py`

The `RichCaptureEnhancer` class provides:
- `calculate_message_confidence()` - Confidence from message characteristics
- `identify_uncertainty_sources()` - Pattern-based uncertainty detection
- `extract_measurements()` - Real metric extraction
- `detect_alternatives_considered()` - Alternative identification
- `create_rich_step_from_message()` - Complete rich step generation

### Frontend Display

**File**: `/Users/kay/uatp-capsule-engine/frontend/src/components/capsules/capsule-detail.tsx`

Already fully supports:
- Confidence badges with color coding
- Measurement displays
- Uncertainty warnings
- Alternative listings
- Confidence methodology explanations

## Testing the System

### Trigger a Capture

Have a substantive conversation with Claude Code:

```
User: "Analyze the performance of our database queries and suggest optimizations"
Assistant: [Detailed analysis with code examples, measurements, alternatives]
User: "Which approach would you recommend?"
Assistant: [Decision with reasoning and trade-offs]
```

This conversation should trigger capture because:
- Multiple turns (3+ messages)
- Technical content (code, analysis)
- Decision-making process
- Clear alternatives discussed

### Verify Rich Metadata

```bash
# 1. Find the capsule
psql -d uatp_capsule_engine -c \
  "SELECT capsule_id FROM capsules ORDER BY timestamp DESC LIMIT 1;"

# 2. Check the payload
psql -d uatp_capsule_engine -c \
  "SELECT payload->'reasoning_steps'->0 FROM capsules ORDER BY timestamp DESC LIMIT 1;" | jq '.'

# 3. Verify via API
CAPSULE_ID="[from step 1]"
curl "http://localhost:8000/capsules/$CAPSULE_ID" | jq '.payload.reasoning_steps[0]'
```

You should see:
- `confidence` field with value 0.0-1.0
- `measurements` object with token_count, content_length_chars
- `operation` field (analysis, decision, implementation, etc.)
- `alternatives_considered` array (if alternatives were mentioned)
- `uncertainty_sources` array (if uncertainty detected)

## Dependencies

### Required
- Python 3.11+
- PostgreSQL 12+
- asyncpg: `pip install asyncpg`

### Already Included
- `src.utils.rich_capsule_creator` - Rich step helpers
- `src.live_capture.rich_capture_integration` - Metadata analyzer

## What Changed

### Before
```python
# Simple string capture
reasoning_steps = [
    "User asked about database optimization",
    "I analyzed the query patterns",
    "I suggested using indexes"
]
```

### After
```python
# Rich object capture (automatic)
reasoning_steps = [
    RichReasoningStep(
        step=1,
        reasoning="User asked about database optimization",
        confidence=0.70,
        operation="query",
        measurements={"token_count": 12, "content_length_chars": 45}
    ),
    RichReasoningStep(
        step=2,
        reasoning="I analyzed the query patterns",
        confidence=0.88,
        operation="analysis",
        measurements={"token_count": 234, "response_time_seconds": 2.1},
        alternatives_considered=["Index optimization", "Query rewriting"]
    )
]
```

## Summary

 **You're all set!** The system is now capturing rich metadata automatically. Every significant Claude Code conversation will generate capsules with:

- Real confidence scores
- Detected uncertainty
- Measured metrics
- Identified alternatives

Just use Claude Code normally and check the frontend to see your rich reasoning traces!

## Questions?

If something doesn't work as expected:
1. Check PostgreSQL connection: `psql -d uatp_capsule_engine -c '\dt'`
2. Verify API is running: `curl http://localhost:8000/health`
3. Check capture logs for error messages
4. Ensure frontend can connect: http://localhost:3000

The system is designed to fail gracefully - if rich capture fails, it falls back to simple capture to ensure no data is lost.
