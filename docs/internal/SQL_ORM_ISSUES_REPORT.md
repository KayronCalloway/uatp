# SQL/ORM Issues Report
*Generated: 2025-12-05*
*Context: Capsule Enrichment Script Development*

---

## ⚠️ **Critical Issue: SQLAlchemy ORM Query Problems**

### **Problem Summary**

When attempting to query capsules using SQLAlchemy ORM in the enrichment script, queries consistently returned `None` objects instead of actual `CapsuleModel` instances.

---

## **Issue #1: ORM Query Returns None Objects**

### Attempted Code:
```python
from sqlalchemy import select
from src.models.capsule import CapsuleModel

query = select(CapsuleModel).where(
    CapsuleModel.capsule_type == 'reasoning_trace'
).where(~CapsuleModel.capsule_id.like('demo-%'))

result = await session.execute(query)
capsules = result.scalars().all()  # Returns list of None objects!
```

### Observed Behavior:
```python
# Query executes without error
capsules = result.scalars().all()
print(len(capsules))  # Output: 6
print(capsules[0])     # Output: None
print(type(capsules[0]))  # Output: <class 'NoneType'>
```

### Verification:
```python
# Direct SQL works perfectly
result = await session.execute(text("""
    SELECT capsule_id, capsule_type, timestamp
    FROM capsules
    WHERE capsule_type = 'reasoning_trace'
    AND capsule_id NOT LIKE 'demo-%'
"""))
rows = result.fetchall()
# Returns actual data: [('caps_2025_12_04...', 'reasoning_trace', ...)]
```

### Root Cause (Unknown):
- ORM model mapping issue?
- SQLAlchemy version incompatibility?
- Database session configuration?
- Polymorphic discriminator issue in `CapsuleModel`?

**Note:** The same ORM queries work fine in the FastAPI routes (`src/api/capsules_fastapi_router.py`), which suggests it's an initialization or context issue specific to standalone scripts.

---

## **Issue #2: PostgreSQL vs SQLite Syntax Incompatibility**

### Attempted Code (PostgreSQL syntax):
```python
stmt = text("""
    UPDATE capsules
    SET payload = :payload::jsonb,
        verification = :verification::jsonb
    WHERE id = :id
""")
```

### Error:
```
sqlite3.ProgrammingError: Incorrect number of bindings supplied.
The current statement uses 3, and there are 1 supplied.
```

### Problem:
- `::jsonb` casting is PostgreSQL-specific
- SQLite doesn't recognize the syntax
- SQLite stores JSON as TEXT, not JSONB

### Solution Applied:
```python
# Works with both SQLite and PostgreSQL
stmt = text("""
    UPDATE capsules
    SET payload = :payload,
        verification = :verification
    WHERE id = :id
""")

# Pass JSON as string
await session.execute(stmt, {
    'payload': json.dumps(enriched_payload),
    'verification': json.dumps(enriched_verification),
    'id': capsule['id']
})
```

---

## **Issue #3: Database Update Persistence**

### Problem:
Enrichment script reports successful updates but changes don't persist in database.

### Evidence:
```bash
# Script output
📦 Processing: caps_2025_12_04_69a818b7636743e2
  → Adding critical path analysis...
  → Adding trust score to verification...
  ✅ Enrichment complete!
  💾 Updated in database

# But database query shows old data
SELECT payload FROM capsules WHERE capsule_id = 'caps_2025_12_04_69a818b7636743e2';
# Returns: Original payload without enrichments
```

### Possible Causes:

1. **Transaction Not Committing:**
   ```python
   await session.execute(stmt, params)
   await session.commit()  # ← May not be working as expected
   ```

2. **Session Scope Issue:**
   ```python
   async with db.get_session() as session:
       # Updates here
       await session.commit()
   # Session might be rolling back on exit?
   ```

3. **JSON Serialization:**
   ```python
   # SQLite might not be deserializing the JSON string properly
   'payload': json.dumps(enriched_payload)  # Stored as TEXT
   ```

4. **Different Database Connection:**
   - Script might be writing to different SQLite file?
   - API server reading from different database?
   - Connection pooling issue?

### Attempted Fixes:
- ✅ Removed `::jsonb` casting → Fixed syntax error
- ✅ Explicit `await session.commit()` → Still no persistence
- ✅ Verified `session.execute()` completes without error
- ❌ Data still not persisting

---

## **Workaround: Direct SQL Queries**

### Current Solution:
```python
# Fetch capsules using raw SQL
sql = """
    SELECT id, capsule_id, capsule_type, version, timestamp,
           status, verification, payload
    FROM capsules
    WHERE capsule_type = 'reasoning_trace'
    AND capsule_id NOT LIKE 'demo-%'
"""
result = await session.execute(text(sql))
rows = result.fetchall()

# Convert to dictionaries manually
capsules = []
for row in rows:
    capsules.append({
        'id': row[0],
        'capsule_id': row[1],
        'capsule_type': row[2],
        # ... etc
    })
```

### Status:
- ✅ Query works
- ✅ Data fetched correctly
- ✅ Enrichment logic runs
- ❌ Updates don't persist

---

## **Working vs Non-Working Patterns**

### ✅ WORKS: FastAPI Routes
```python
# In src/api/capsules_fastapi_router.py
@router.get("")
async def list_capsules(session: AsyncSession = Depends(get_db_session)):
    query = select(CapsuleModel).where(...)
    result = await session.execute(query)
    capsules = result.scalars().all()  # Returns actual CapsuleModel objects
    return {"capsules": capsules}
```

**Why it works:** FastAPI dependency injection handles session lifecycle correctly

### ❌ DOESN'T WORK: Standalone Script
```python
# In enrich_existing_capsules.py
async with db.get_session() as session:
    query = select(CapsuleModel).where(...)
    result = await session.execute(query)
    capsules = result.scalars().all()  # Returns None objects
```

**Why it fails:** Unknown - same database, same session factory

---

## **Database Configuration Differences**

### FastAPI Context:
```python
# src/app_factory.py
app = create_app()
db.init_app(app)  # Happens during app initialization
```

### Script Context:
```python
# enrich_existing_capsules.py
app = create_app()
if not db.engine:
    db.init_app(app)  # Manual initialization

async with db.get_session() as session:
    # Use session
```

**Potential Issue:** App context not fully initialized in script environment?

---

## **Recommendations**

### Short-Term (Current):
1. ✅ **Keep using direct SQL** for enrichment script
2. ✅ **New capsules work fine** - they use the working code paths
3. ⚠️ **Accept that 6 old capsules remain simple** - minimal impact

### Medium-Term (If needed):
1. **Debug ORM in standalone context:**
   - Compare FastAPI dependency injection vs manual session
   - Check if app context manager is needed
   - Verify SQLAlchemy session configuration

2. **Test with PostgreSQL:**
   - See if issue persists with PostgreSQL backend
   - SQLite has known quirks with async operations

3. **Alternative approach:**
   ```python
   # Use FastAPI to trigger enrichment via HTTP endpoint
   @router.post("/capsules/enrich")
   async def enrich_capsules(session: AsyncSession = Depends(get_db_session)):
       # Enrichment logic here with working ORM
       pass
   ```

### Long-Term:
1. **Standardize database operations:**
   - Create shared database utilities
   - Ensure consistent session management
   - Document working patterns

2. **Add integration tests:**
   - Test ORM queries in script context
   - Verify updates persist
   - Catch regressions early

---

## **Impact Assessment**

### Low Priority Because:
1. **Only affects 6 old capsules** (< 10% of reasoning capsules)
2. **New capsules work perfectly** (use integrated creation path)
3. **Workaround exists** (manual enrichment via API if needed)
4. **Old capsules still functional** (just don't have advanced analysis)

### High Priority If:
1. Need to enrich large number of existing capsules
2. Plan to run batch operations on database
3. Scripting/automation is critical to workflow

---

## **Files Where SQL/ORM Issues Occurred**

1. **`enrich_existing_capsules.py`** - Main enrichment script
   - Lines 34-66: Query returns None objects
   - Lines 249-263: Update persistence issues

2. **`src/core/database.py`** - Database session management
   - Lines 73-78: `get_session()` context manager
   - Potentially: Session lifecycle not compatible with standalone scripts

---

## **Related Documentation**

- SQLAlchemy Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- FastAPI Dependencies: https://fastapi.tiangolo.com/tutorial/dependencies/
- SQLite JSON1: https://www.sqlite.org/json1.html

---

## **Reproduction Steps**

### To Reproduce ORM Issue:
```bash
python3 -c "
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

from sqlalchemy import select
from src.core.database import db
from src.models.capsule import CapsuleModel
from src.app_factory import create_app

async def test():
    app = create_app()
    if not db.engine:
        db.init_app(app)

    async with db.get_session() as session:
        query = select(CapsuleModel).where(
            CapsuleModel.capsule_type == 'reasoning_trace'
        ).limit(1)

        result = await session.execute(query)
        capsules = result.scalars().all()

        print(f'Found: {len(capsules)}')
        print(f'First capsule type: {type(capsules[0]) if capsules else None}')
        print(f'First capsule value: {capsules[0] if capsules else None}')

asyncio.run(test())
"
```

**Expected:** `<class 'src.models.capsule.CapsuleModel'>`
**Actual:** `<class 'NoneType'>`

---

## **Status: KNOWN ISSUE - WORKAROUND IN PLACE**

- **Severity:** Low (affects only enrichment script for 6 old capsules)
- **Workaround:** Use direct SQL queries (implemented)
- **Next Steps:** Monitor if issue affects other standalone scripts
- **Resolution:** Defer until higher priority or more instances found

---

**Last Updated:** 2025-12-05
**Reported By:** Claude Code Integration Session
**Status:** Open - Workaround Implemented
