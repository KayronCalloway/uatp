# Demo Mode Implementation Status

## Summary
We've implemented foundational infrastructure for demo/live data separation in the UATP Capsule Engine. The database now contains both demo and real capsules, and filtering logic has been added at multiple layers.

## [OK] Completed Work

### 1. Database Population
- **5 demo capsules** successfully added to PostgreSQL database
  - `demo-attribution-001` (attribution type)
  - `demo-economic-001` (economic type)
  - `demo-reasoning-001` (reasoning type)
  - `demo-governance-001` (governance type)
  - `demo-conversation-001` (conversation type)
- **Total database**: 88 capsules (5 demo + 83 real)
- Demo capsules identified by `demo-` prefix in `capsule_id`

### 2. Engine Layer (Database Filtering)
**File**: `src/engine/capsule_engine.py`
**Lines**: 676-714

- Added `exclude_demo` parameter to `load_chain_async()` method
- Implemented SQL-level filtering:
  ```sql
  WHERE capsule_id NOT LIKE 'demo-%'
  ```
- Added debug logging to track filtering execution
- Filter applied at database query level for performance

### 3. API Layer (Query Parameters)
**File**: `src/api/schemas.py`

- Added `demo_mode: bool = False` field to `ListCapsulesQuery` schema
- Default is `False` (live mode - excludes demo capsules)

**File**: `src/api/capsule_routes.py`
**Lines**: 80-110

- Modified `list_capsules()` endpoint to pass `exclude_demo` parameter
- Logic: `exclude_demo=not query_args.demo_mode`
  - `demo_mode=false` → `exclude_demo=True` → filters out demo capsules
  - `demo_mode=true` → `exclude_demo=False` → shows all capsules
- Added debug logging to track parameter passing

### 4. Error Fixes
**File**: `src/integrations/anthropic_client.py`

- Fixed Anthropic SDK initialization error with graceful degradation
- Allows API to start even when Anthropic client fails to initialize

## [WARN] Current Issue

### Filtering Not Working as Expected
When testing with `demo_mode=false`, the API still returns demo capsules:
- **Expected**: 0 demo capsules, ~83 real capsules
- **Actual**: 5 demo capsules, 40 real capsules (45 total)

### Possible Causes

1. **Caching**: Python module caching may be serving old code
2. **SQLAlchemy Query Conversion**: The `db.fetch()` method converts asyncpg-style queries to SQLAlchemy format - the LIKE clause conversion might be failing
3. **Missing Logging Output**: Debug logs added aren't appearing, suggesting logging level configuration issues

##  Next Steps to Debug

### Option 1: Direct SQL Test
Test the SQL query directly at the database level to verify the WHERE clause works:
```python
# Test SQL filtering directly
query = """
SELECT capsule_id
FROM capsules
WHERE capsule_id NOT LIKE 'demo-%'
LIMIT 10
"""
```

### Option 2: Check SQLAlchemy Query Conversion
The `src/core/database.py` `fetch()` method converts queries. Need to log the actual SQL being executed to see if the LIKE clause is preserved.

###  Option 3: Simplify Filtering
Instead of SQL-level filtering, implement post-query Python filtering:
```python
if exclude_demo:
    capsules = [c for c in capsules if not c.capsule_id.startswith('demo-')]
```

### Option 4: Frontend Integration
Assuming backend filtering works, update frontend to:
1. Read `DemoModeContext` state
2. Include `demo_mode` query parameter in API calls
3. Files likely needing updates:
   - `frontend/src/lib/api-client.ts` or similar API client
   - Component making capsule list API calls

##  Implementation Notes

### Database Schema
- Capsules stored with `capsule_id` as primary key column
- Payload JSON stored separately (doesn't contain `capsule_id`)
- Demo identification is purely via ID prefix convention

### API Contract
```
GET /capsules?demo_mode=false&per_page=20
```
- `demo_mode=false` (default): Returns only real/live capsules
- `demo_mode=true`: Returns all capsules (demo + real)

### Frontend Component
The frontend already has `DemoModeContext` infrastructure:
- File: `frontend/src/contexts/demo-mode-context.tsx`
- This context should control the `demo_mode` API parameter

##  User's Goal

> "i want to run real data not demo. we have auto capture set up. yythere is a demo button that all the demo data can go but i want thw live one"

**Target Behavior**:
- Default view: Show only real auto-captured conversation data (83 capsules)
- Demo mode toggle: Show demo examples for testing/showcase (88 capsules)
- Clean separation at database level (not workarounds)
- Long-term sustainable architecture

##  Current Database State

```
PostgreSQL database: uatp_capsule_engine
Total: 88 capsules
Demo: 5 capsules (demo-* prefix)
Real: 83 capsules (auto-captured + manual)
```

##  To Complete Implementation

1. **Debug SQL filtering** - Verify WHERE clause is executed correctly
2. **Add logging configuration** - Make debug logs visible
3. **Test both modes end-to-end**:
   - Live mode: 0 demo capsules
   - Demo mode: 5 demo capsules
4. **Frontend integration** - Connect DemoModeContext to API calls
5. **Remove debug logging** - Clean up after confirmation works

##  Quick Test Commands

```bash
# Test live mode (should exclude demo)
curl "http://localhost:8000/capsules?demo_mode=false&per_page=100"

# Test demo mode (should include demo)
curl "http://localhost:8000/capsules?demo_mode=true&per_page=100"

# Check database directly
python3 check_capsule_storage.py
```

##  Modified Files

1. `src/engine/capsule_engine.py` - Added exclude_demo filtering
2. `src/api/schemas.py` - Added demo_mode parameter
3. `src/api/capsule_routes.py` - Pass filtering to engine
4. `src/integrations/anthropic_client.py` - Fixed initialization error
5. `add_demo_capsules_to_postgres.py` - Script to populate demo data

##  Success Criteria

- [ ] API with `demo_mode=false` returns 0 demo capsules
- [ ] API with `demo_mode=true` returns 5 demo capsules
- [ ] Frontend toggle controls which data is displayed
- [ ] Auto-capture continues populating real data
- [ ] No workarounds or temp fixes in production code
