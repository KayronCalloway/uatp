# Data Separation Report: Demo vs Live Capsules
*Generated: 2025-12-05*

## Executive Summary

**Issue:** Frontend shows 115 total capsules but lists only show 67 capsules.
**Root Cause:** Inconsistent demo filtering between stats and list endpoints.

---

## Current State

### Database Reality:
```
Total Capsules: 115
├─ Live Capsules (no demo- prefix): 67 capsules
└─ Demo Capsules (demo-* prefix):   48 capsules
```

### API Endpoint Behavior:

#### 1. `/capsules/stats` - Statistics Endpoint
**Location:** `src/api/capsules_fastapi_router.py` lines 50-116

**Behavior:** Returns ALL capsules (no filtering)
```python
# Get total count
total_result = await session.execute(select(func.count(CapsuleModel.id)))
total = total_result.scalar() or 0  # Returns 115
```

**Response:**
```json
{
  "total_capsules": 115,  ← Includes demos
  "by_type": {
    "reasoning_trace": 68,
    "economic_transaction": 32,
    "chat": 8,
    "conversation": 2,
    ...
  }
}
```

#### 2. `/capsules` - List Endpoint
**Location:** `src/api/capsules_fastapi_router.py` lines 119-240

**Parameters:**
- `demo_mode: bool = False` (default excludes demos)

**Filtering Logic (lines 152-154):**
```python
# Apply demo_mode filtering - exclude demo capsules unless demo_mode=True
if not demo_mode:
    query = query.where(~CapsuleModel.capsule_id.like('demo-%'))
```

**Behavior:**
- `demo_mode=false` (default) → Returns 67 capsules [OK]
- `demo_mode=true` → Returns 115 capsules (all)

**Current API Calls:**
```bash
# Default behavior
curl "http://localhost:8000/capsules"
→ Returns 67 capsules (excludes demo-*)

# Explicit exclusion
curl "http://localhost:8000/capsules?demo_mode=false"
→ Returns 67 capsules (excludes demo-*)

# Include demos
curl "http://localhost:8000/capsules?demo_mode=true"
→ Returns 115 capsules (includes demo-*)

# Stats endpoint (no filtering)
curl "http://localhost:8000/capsules/stats"
→ Returns total_capsules: 115
```

---

## Frontend Behavior

### What Shows 115:
All components using `api.getCapsuleStats()`:

1. **Dashboard** (`frontend/src/components/dashboard/dashboard.tsx`)
   - Line 126: Shows `statsData?.total_capsules` → **115**

2. **Mission Control** (`frontend/src/components/mission-control/mission-control.tsx`)
   - Line 105: `const totalCapsules = statsData?.total_capsules` → **115**

3. **System View** (`frontend/src/components/system/system-view.tsx`)
   - Line 143: `{stats.total_capsules.toLocaleString()} capsules stored` → **115**

4. **Capsule Overview** (`frontend/src/components/capsules/capsule-overview.tsx`)
   - Line 51: `const totalCapsules = stats?.total_capsules` → **115**

### What Shows 67:
Components using `api.getCapsules()`:

1. **Capsule List** (`frontend/src/components/capsules/capsule-list.tsx`)
   - Line 71: `api.getCapsules(queryParams)`
   - queryParams does NOT include `demo_mode` parameter
   - Result: Gets 67 capsules

2. **Universe Visualization** (`frontend/src/components/universe/universe-visualization.tsx`)
   - Line 60: `api.getCapsules({ per_page: 100 })`
   - No `demo_mode` parameter
   - Result: Gets 67 capsules (paginated)

---

## The Problem

### Inconsistency:
```
Stats Endpoint:     115 capsules (unfiltered)
                     ↓
Frontend Dashboard: "115 Total Capsules"
                     ↓
User clicks "View All Capsules"
                     ↓
List Endpoint:      67 capsules (filtered)
                     ↓
Frontend List:      Shows only 67 capsules

User sees: "Wait, where did 48 capsules go?!"
```

### Root Causes:

1. **Stats endpoint doesn't respect demo filtering**
   - Always returns ALL capsules
   - No `demo_mode` parameter available

2. **Frontend doesn't pass demo_mode consistently**
   - Has `useDemoMode()` context (line 39 of capsule-list.tsx)
   - But doesn't pass it to API calls

3. **Context mismatch**
   - `useDemoMode()` is for switching between real API and mock data
   - NOT for filtering demo capsules from real data
   - Two different concepts conflated

---

## Live Capsules Breakdown (67 Total)

### By Type:
```bash
curl "http://localhost:8000/capsules?demo_mode=false&per_page=100" | jq '.total'
→ 67
```

Estimated breakdown:
- `reasoning_trace`: ~33 live capsules
- `economic_transaction`: ~32 live capsules
- `chat`: ~2 live capsules

### Rich Metadata Analysis (Live Only):

Out of 67 live capsules, checking for advanced analysis fields:

**Reasoning Trace Capsules (33 total):**
```
Capsules with rich step objects:        1 capsule  (3%)
  - caps_2025_12_05_pg_rich_001

Capsules with step-level confidence:    1 capsule  (3%)
Capsules with critical_path_analysis:   0 capsules (0%)
Capsules with improvement_recommendations: 0 (0%)
Capsules with epistemic_uncertainty:    0 capsules (0%)
Capsules with aleatoric_uncertainty:    0 capsules (0%)
Capsules with trust_score:              0 capsules (0%)
```

**Simple format capsules:** 32 out of 33 (97%)
- Steps are plain strings: `["Step 1: ...", "Step 2: ..."]`
- No rich metadata

---

## Solutions

### Option 1: Make Stats Endpoint Respect Demo Mode  RECOMMENDED
Add `demo_mode` parameter to stats endpoint:

```python
@router.get("/stats")
async def get_capsule_stats(
    demo_mode: bool = Query(False, description="Include demo capsules"),
    session: AsyncSession = Depends(get_db_session)
):
    # Build query with demo filtering
    count_query = select(func.count(CapsuleModel.id))
    if not demo_mode:
        count_query = count_query.where(~CapsuleModel.capsule_id.like('demo-%'))

    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    # ... rest of stats logic with filtering
```

**Pros:**
- Consistent behavior across endpoints
- Frontend gets accurate counts
- Clear separation maintained

**Cons:**
- Breaking change for existing API consumers
- Need to update frontend calls

### Option 2: Frontend Passes Demo Mode Parameter
Update `capsule-list.tsx` to pass demo_mode:

```typescript
const queryParams: ListCapsulesQuery = {
  page: currentPage,
  per_page: pageSize,
  compress,
  demo_mode: false,  // ADD THIS - explicitly exclude demos
};
```

**Pros:**
- Minimal backend changes
- Makes frontend intent explicit

**Cons:**
- Doesn't fix stats inconsistency
- User still sees "115" in dashboard but "67" in list

### Option 3: Separate Demo/Live Completely  BEST LONG-TERM
Add separate endpoints:

```
GET /capsules/stats/live    → 67 capsules (excludes demo)
GET /capsules/stats/demo    → 48 capsules (only demo)
GET /capsules/stats/all     → 115 capsules (everything)

GET /capsules/live → default, excludes demo
GET /capsules/demo → only demo capsules
```

**Pros:**
- Crystal clear separation
- No ambiguity about what you're getting
- Easy to understand API

**Cons:**
- Most work
- Requires frontend updates

---

## Recommended Implementation

**Phase 1: Fix Stats Endpoint (Quick)**
```python
# src/api/capsules_fastapi_router.py

@router.get("/stats")
async def get_capsule_stats(
    demo_mode: bool = Query(False, description="Include demo capsules"),
    session: AsyncSession = Depends(get_db_session)
):
    # Add demo filtering to ALL count queries
    base_filter = ~CapsuleModel.capsule_id.like('demo-%') if not demo_mode else True

    # Apply to total count
    count_query = select(func.count(CapsuleModel.id)).where(base_filter)
    total = (await session.execute(count_query)).scalar() or 0

    # Apply to type breakdown
    type_query = select(
        CapsuleModel.capsule_type,
        func.count(CapsuleModel.id)
    ).where(base_filter).group_by(CapsuleModel.capsule_type)

    # ... etc
```

**Phase 2: Update Frontend (Consistency)**
```typescript
// frontend/src/components/capsules/capsule-list.tsx

const queryParams: ListCapsulesQuery = {
  page: currentPage,
  per_page: pageSize,
  compress,
  demo_mode: false,  // Explicit: we want live data only
};

// frontend/src/lib/api-client.ts
async getCapsuleStats(demoMode: boolean = false): Promise<CapsuleStatsResponse> {
  const response = await this.client.get('/capsules/stats', {
    params: { demo_mode: demoMode }
  });
  return response.data;
}

// Update all stats calls
const statsData = await api.getCapsuleStats(false); // Live only
```

---

## Verification Commands

After fixes, verify consistency:

```bash
# Should all show 67
curl -s "http://localhost:8000/capsules/stats?demo_mode=false" | jq '.total_capsules'
curl -s "http://localhost:8000/capsules?demo_mode=false&per_page=1" | jq '.total'

# Should all show 115 (or close with pagination)
curl -s "http://localhost:8000/capsules/stats?demo_mode=true" | jq '.total_capsules'
curl -s "http://localhost:8000/capsules?demo_mode=true&per_page=1" | jq '.total'
```

---

## Summary

**Current State:**
- [OK] Backend has demo filtering on list endpoint
- [ERROR] Backend stats endpoint ignores demo filtering
- [WARN] Frontend has demo context but doesn't use it correctly
- [ERROR] User sees 115 in dashboards, 67 in lists

**After Fix:**
- [OK] Stats endpoint respects demo_mode parameter
- [OK] Frontend explicitly passes demo_mode=false for live data
- [OK] Consistent counts: 67 live capsules everywhere
- [OK] Optional: demo_mode=true shows all 115

**Live Capsule Analysis:**
- 67 live capsules (confirmed)
- 33 reasoning_trace type
- Only 1 has rich metadata (partially)
- 0 have advanced analysis fields (critical_path, uncertainty, trust_score)
- **Ready for integration work to add missing analysis**
