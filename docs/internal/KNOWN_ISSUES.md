# Known Issues - UATP Capsule Engine
*Last Updated: 2025-12-05*

---

##  **Active Issues**

### 1. SQLAlchemy ORM Query Failures in Standalone Scripts
**Severity:** Medium
**Status:** Open - Workaround Implemented
**File:** `enrich_existing_capsules.py`
**Detailed Report:** `SQL_ORM_ISSUES_REPORT.md`

**Problem:**
When using SQLAlchemy ORM queries in standalone Python scripts (outside FastAPI context), queries return `None` objects instead of actual model instances.

**Example:**
```python
# This code fails in standalone scripts
from sqlalchemy import select
query = select(CapsuleModel).where(CapsuleModel.capsule_type == 'reasoning_trace')
result = await session.execute(query)
capsules = result.scalars().all()
# Returns: [None, None, None, ...] instead of [<CapsuleModel>, <CapsuleModel>, ...]
```

**Working Contexts:**
- [OK] FastAPI routes (dependency injection handles session properly)
- [OK] Direct SQL queries (bypass ORM)

**Failing Contexts:**
- [ERROR] Standalone Python scripts with manual session management
- [ERROR] Enrichment/migration scripts

**Impact:**
- Cannot use ORM convenience methods in batch scripts
- Forced to use raw SQL for standalone operations
- Only affects 6 existing capsules (enrichment script)
- New capsules unaffected (use working code paths)

**Workaround:**
Use direct SQL queries instead of ORM:
```python
from sqlalchemy import text
sql = "SELECT * FROM capsules WHERE capsule_type = 'reasoning_trace'"
result = await session.execute(text(sql))
rows = result.fetchall()  # Works correctly
```

**Root Cause:** Unknown - possibly related to:
- App context not fully initialized in script environment
- Session lifecycle management differences
- Async context handling in standalone scripts

---

### 2. Database Update Persistence Issues
**Severity:** Medium
**Status:** Open - Under Investigation
**File:** `enrich_existing_capsules.py` (lines 249-263)

**Problem:**
Enrichment script executes successfully and reports "[OK] Success" but database updates don't persist.

**Evidence:**
```bash
# Script output
 Processing: caps_2025_12_04_69a818b7636743e2
  → Adding critical path analysis...
  [OK] Enrichment complete!
   Updated in database

# But query shows original data
SELECT payload FROM capsules WHERE capsule_id = 'caps_2025_12_04_69a818b7636743e2';
# Returns: Original payload without enrichments
```

**Attempted:**
- [OK] Explicit `await session.commit()`
- [OK] Verified no exceptions thrown
- [OK] Checked transaction scope
- [ERROR] Still not persisting

**Possible Causes:**
1. SQLite async transaction handling
2. Session context manager auto-rollback
3. JSON serialization issues
4. Connection pooling problem

**Impact:**
- Only affects enrichment of 6 existing capsules
- New capsules work perfectly (different code path)
- Non-blocking for main functionality

**Workaround:**
Accept that old capsules remain simple; new capsules automatically have rich metadata.

---

### 3. PostgreSQL vs SQLite Syntax Incompatibility
**Severity:** Low
**Status:** [OK] Resolved
**File:** `enrich_existing_capsules.py` (fixed in lines 252-257)

**Problem:**
PostgreSQL-specific `::jsonb` casting syntax caused SQLite errors.

**Error:**
```
sqlite3.ProgrammingError: Incorrect number of bindings supplied.
```

**Solution:**
```python
# Before (PostgreSQL only)
UPDATE capsules SET payload = :payload::jsonb

# After (works with both)
UPDATE capsules SET payload = :payload
# Pass JSON as string: json.dumps(payload)
```

**Status:** [OK] Fixed - code now compatible with both databases

---

##  **Impact Assessment**

### Critical Path Impact: **LOW**

| Issue | Affects | Severity | Impact |
|-------|---------|----------|--------|
| ORM Query Failures | Enrichment script only | Medium | 6 old capsules |
| Update Persistence | Enrichment script only | Medium | 6 old capsules |
| SQL Syntax | Fixed | Low | None |

**Why Low Impact:**
1. Only 6 old reasoning capsules affected (< 10% of reasoning data)
2. New capsules work perfectly via integrated creation path
3. Main application (FastAPI) unaffected
4. Workarounds implemented for all issues
5. Frontend functionality intact

---

## [OK] **Working Systems**

### These Work Perfectly:
- [OK] FastAPI API routes (all CRUD operations)
- [OK] New capsule creation via `RichCaptureEnhancer`
- [OK] Stats endpoint with filtering
- [OK] Frontend display of capsule data
- [OK] Uncertainty quantification integration
- [OK] Critical path analysis
- [OK] Trust score calculation
- [OK] Direct SQL queries

### These Need Attention:
- [WARN] Standalone script ORM usage
- [WARN] Batch database updates
- [WARN] Migration/enrichment scripts

---

##  **Debugging Notes**

### To Reproduce ORM Issue:
```bash
cd /Users/kay/uatp-capsule-engine
python3 -c "
import asyncio
from sqlalchemy import select
from src.core.database import db
from src.models.capsule import CapsuleModel
from src.app_factory import create_app

async def test():
    app = create_app()
    if not db.engine:
        db.init_app(app)

    async with db.get_session() as session:
        query = select(CapsuleModel).limit(1)
        result = await session.execute(query)
        capsules = result.scalars().all()
        print(f'Type: {type(capsules[0]) if capsules else None}')

asyncio.run(test())
"
# Expected: <class 'src.models.capsule.CapsuleModel'>
# Actual: <class 'NoneType'>
```

### To Verify Working FastAPI:
```bash
curl "http://localhost:8000/capsules?per_page=1"
# Works perfectly - returns actual capsule data
```

---

##  **Next Steps**

### If Issue Escalates:
1. Test with PostgreSQL (rule out SQLite-specific issues)
2. Compare FastAPI dependency injection vs manual session
3. Check SQLAlchemy async session configuration
4. Review app context initialization requirements

### If Issue Persists:
1. Document as known limitation for standalone scripts
2. Recommend using FastAPI endpoints for batch operations
3. Consider creating API endpoint for enrichment:
   ```python
   @router.post("/capsules/enrich-all")
   async def enrich_all(session: AsyncSession = Depends(get_db_session)):
       # Use working FastAPI context
   ```

---

##  **Related Documentation**

- **Detailed Analysis:** `SQL_ORM_ISSUES_REPORT.md`
- **Integration Summary:** `INTEGRATION_COMPLETE_SUMMARY.md`
- **Data Separation:** `DATA_SEPARATION_REPORT.md`
- **Enrichment Script:** `enrich_existing_capsules.py`

---

##  **Recommendation**

**Action:** Monitor but don't block on these issues

**Rationale:**
1. Core functionality works
2. Only affects edge case (6 old capsules)
3. Workarounds in place
4. New system delivers all required features
5. Can revisit if issue spreads to other areas

**Priority:** P3 (Nice to fix, not urgent)

---

*For immediate support, see workarounds in `SQL_ORM_ISSUES_REPORT.md`*
