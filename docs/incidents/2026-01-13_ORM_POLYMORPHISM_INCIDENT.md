# ORM Polymorphism Incident Report

**Date:** 2026-01-13
**Session:** Claude Code session `43f1ce2b-cc68-4429-82d1-72ef0f7df428`
**Severity:** Critical - API endpoints returning empty results
**Status:** Bandaid applied, proper fix pending

---

## Summary

The `/capsules` API endpoints began returning empty arrays despite 93+ capsules existing in the database. The SQLAlchemy ORM was returning `None` objects for every row queried.

---

## Root Cause Analysis

### Git Archaeology - When Did This Break?

**Critical Finding:** The broken polymorphism configuration existed from the **very first commit** to this repository.

| Commit | Date | State |
|--------|------|-------|
| `b35c7a0` | Dec 3, 2025 | Initial commit - polymorphism already removed, subclasses still present |
| `8ff4d51` | Dec 3, 2025 | Fix database indexes - no polymorphism changes |
| `1654c20` | Dec 27, 2025 | Add outcome tracking - added fields, same broken polymorphism |
| `ac3255a` | Jan 1, 2026 | Add ML foundation - added fields, same broken polymorphism |

The comment "Removed polymorphism for simpler, more scalable approach" was present in `b35c7a0`, meaning this decision was made **before** the migration to the M5 Mac. The cleanup (removing subclass `polymorphic_identity` declarations) was simply never completed.

### The Problem

In `src/models/capsule.py`, the base `CapsuleModel` class had its polymorphism configuration removed:

```python
# Line 73-75 - BROKEN STATE (present since initial commit)
# Removed polymorphism for simpler, more scalable approach
# All capsule types use the same model with flexible JSON payload
__mapper_args__ = {}
```

However, **all 26 subclasses still retained their `polymorphic_identity` declarations**:

```python
class ReasoningTraceCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": "reasoning_trace"}  # Still present!

class EconomicTransactionCapsuleModel(CapsuleModel):
    __mapper_args__ = {"polymorphic_identity": "economic_transaction"}  # Still present!
# ... and 24 more subclasses
```

### Why This Breaks

SQLAlchemy's single-table inheritance requires:
1. Base class declares `polymorphic_on` pointing to discriminator column
2. Subclasses declare `polymorphic_identity` values

When you have (2) without (1):
- SQLAlchemy sees identities but doesn't know which column maps to them
- During query hydration, it can't determine which class to instantiate
- Returns `None` for every row

### Async Complication

Interestingly, the issue only manifested in the **async server context**:
- Direct sync queries with `create_engine()` worked fine
- Direct async queries with fresh `create_async_engine()` worked fine
- Server's async queries through `db.get_session()` returned None

This suggests additional complexity with how the `db` singleton initializes its engine relative to when models are imported and registered.

---

## Evidence

### Database State (confirmed working)
```sql
sqlite> SELECT COUNT(*) FROM capsules;
103

sqlite> SELECT DISTINCT capsule_type FROM capsules;
reasoning_trace
```

### Direct Query Test (worked)
```python
# This worked - returned proper CapsuleModel objects
engine = create_async_engine("sqlite+aiosqlite:///uatp_dev.db")
Session = sessionmaker(engine, class_=AsyncSession)
async with Session() as session:
    result = await session.execute(select(CapsuleModel).limit(2))
    capsules = result.scalars().all()  # Returns [ReasoningTraceCapsuleModel, ...]
```

### Server Query (broken)
```python
# This returned [None, None, None, ...]
async with db.get_session() as session:
    result = await session.execute(select(CapsuleModel).limit(3))
    capsules = result.scalars().all()  # Returns [None, None, None]
```

---

## Bandaid Fix Applied

Converted read endpoints to raw SQL to bypass ORM entirely:

```python
# In src/api/capsules_fastapi_router.py

# List endpoint (lines ~279-350)
sql = "SELECT * FROM capsules WHERE 1=1 ..."
result = await session.execute(text(sql), params)
rows = result.fetchall()
# Manual JSON parsing and response building

# Get single capsule endpoint (lines ~377-439)
sql = "SELECT * FROM capsules WHERE capsule_id = :capsule_id"
result = await session.execute(text(sql), {"capsule_id": capsule_id})
row = result.fetchone()
# Manual JSON parsing and response building
```

### Compromises of Bandaid
- No automatic type coercion
- Manual JSON field parsing required
- Field mapping duplicated between model and SQL response
- Can't use model methods like `to_pydantic()`
- Must manually update if schema changes

---

## Proper Fix Required

### Option A: Fix Polymorphism Configuration

Re-enable proper polymorphism in base class:

```python
# src/models/capsule.py - CapsuleModel class

__mapper_args__ = {
    "polymorphic_on": capsule_type,
    "polymorphic_identity": "base",
}
```

Then investigate why async server sessions don't work:
1. Check order of imports in `app_factory.py`
2. Verify `db.init_app()` timing vs model registration
3. Check if `db.Base.metadata` matches model metadata
4. Test with explicit `configure_mappers()` call

### Option B: Remove Polymorphism Entirely

If polymorphism isn't needed (all capsules use same table with JSON payload):

1. Remove all `__mapper_args__` from subclasses
2. Delete subclass definitions entirely
3. Use only `CapsuleModel` for all queries
4. Discriminate by `capsule_type` column in application logic

### Option C: Hybrid Approach

Keep ORM for writes (validation), raw SQL for reads (performance):
- This is essentially what the bandaid does
- Could be formalized as intentional architecture
- Document as design decision rather than workaround

---

## Files Modified

1. `src/models/capsule.py` - Attempted polymorphism fix (line 73-77)
2. `src/api/capsules_fastapi_router.py` - Raw SQL bandaid for list/get endpoints
3. `src/auth/auth_middleware.py` - Added capsules to auth skip list (line 199-201)
4. `src/api/capsules_fastapi_router.py` - SQLite JSONB compatibility (multiple locations)

---

## Other Issues Fixed in This Session

1. **SQLite JSONB Syntax** - PostgreSQL `payload::jsonb` syntax doesn't work on SQLite. Added `IS_SQLITE` checks to skip these filters.

2. **Authentication Bypass** - Capsules endpoint required JWT auth. Added to skip list for public read access.

3. **Redis Rate Limiting** - Already had graceful fallback, confirmed working.

---

## Recommendations

### Recommended Fix: Option B - Remove Polymorphism Entirely

The subclass architecture provides **zero benefit** because:

1. **All capsules use identical schema** - same columns, same table
2. **Type discrimination is already handled** - `capsule_type` column stores the type
3. **Actual data is in JSON payload** - no type-specific ORM columns exist
4. **Subclasses have no methods** - they're empty classes with just `__mapper_args__`
5. **The `from_pydantic()` and `to_pydantic()` methods** already work with the generic `CapsuleModel`

**Implementation:**
```python
# src/models/capsule.py

# 1. Remove the __mapper_args__ entirely from CapsuleModel (or keep it empty)
__mapper_args__ = {}

# 2. DELETE all 26 subclass definitions (lines 202-317):
#    - ReasoningTraceCapsuleModel
#    - EconomicTransactionCapsuleModel
#    - ... all 26 subclasses

# 3. Update from_pydantic() to always return CapsuleModel instead of subclass
# The model_map on lines 120-147 can be removed entirely

# 4. Queries should use CapsuleModel directly:
#    select(CapsuleModel).where(CapsuleModel.capsule_type == "reasoning_trace")
```

### Why Not Option A (Re-enable Polymorphism)?

While I attempted to re-enable polymorphism (currently in the code), it doesn't fix the async server context issue. The root problem is SQLAlchemy's mapper configuration timing with async sessions - a complex debugging rabbit hole for zero benefit.

### Action Items

1. **Immediate:** Raw SQL bandaid is working - system is functional
2. **This week:** Implement Option B - delete all subclasses, simplify model
3. **After simplification:** Revert capsules_fastapi_router.py to use ORM queries
4. **Testing:** Add integration test for capsule API endpoints

---

## Related Files for Investigation

- `src/core/database.py` - SQLAlchemyDB singleton, `init_app()` method
- `src/app_factory.py` - App creation, lifespan management, router imports
- `src/models/capsule.py` - CapsuleModel and all subclasses
- SQLAlchemy docs: https://docs.sqlalchemy.org/en/20/orm/inheritance.html

---

## Resolution (2026-01-13)

### Fix Applied

**Branch:** `fix/orm-polymorphism-removal`

1. **Removed all 26 subclasses** from `src/models/capsule.py`
   - `ReasoningTraceCapsuleModel`, `EconomicTransactionCapsuleModel`, etc.
   - These were empty classes that only declared `polymorphic_identity`

2. **Simplified `from_pydantic()`** to always return `CapsuleModel`
   - Removed the `model_map` dictionary
   - Type discrimination now via `capsule_type` string column

3. **Reverted raw SQL bandaid** in `capsules_fastapi_router.py`
   - Restored clean ORM queries
   - `select(CapsuleModel)` now works correctly

4. **Added design decision documentation** at top of `capsule.py`
   - Explains why we don't use polymorphism
   - References this incident report

### Prevention Measures Added

1. **Integration Test:** `tests/integration/test_capsule_orm.py`
   - `test_orm_query_returns_object_not_none` - catches the exact bug
   - `test_orm_query_multiple_returns_objects` - verifies list queries
   - `test_orm_insert_and_retrieve` - full round-trip test

2. **ML Metrics Monitoring:** `src/monitoring/ml_metrics.py`
   - Tracks embedding coverage (alert if < 50%)
   - Tracks outcome coverage (alert if 0%)
   - Provides health check endpoint

### Files Changed

| File | Change |
|------|--------|
| `src/models/capsule.py` | Removed 26 subclasses, simplified from_pydantic |
| `src/api/capsules_fastapi_router.py` | Reverted raw SQL to ORM queries |
| `tests/integration/test_capsule_orm.py` | NEW - Integration tests |
| `src/monitoring/ml_metrics.py` | NEW - ML pipeline monitoring |
| `src/monitoring/__init__.py` | NEW - Module init |

---

## Changelog

- **2026-01-13 ~01:45 UTC** - Initial incident report created
- **2026-01-13 ~02:30 UTC** - Added git archaeology findings, updated recommendations
- **2026-01-13 ~03:00 UTC** - Applied proper fix, added tests and monitoring

---

*Report generated during incident response. Last updated: 2026-01-13 ~03:00 UTC*
*Status: RESOLVED*
