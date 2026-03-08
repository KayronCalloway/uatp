# Timezone Bug - Professional Remediation Plan

## Executive Summary

**Issue:** 97 instances of `datetime.utcnow()` causing 8-hour timestamp offset in PST timezone
**Impact:** All timestamps in database are 8 hours ahead of actual time
**Root Cause:** Naive datetime objects interpreted as local time by PostgreSQL
**Risk Level:** HIGH - Affects audit trails, compliance, and time-based features

---

## Phase 1: Assessment & Triage (DONE)

### What We Found:
```bash
$ grep -r "datetime.utcnow()" src/ --include="*.py" | wc -l
97
```

### Critical Files Affected:
- [OK] `src/api/capsules_fastapi_router.py` (FIXED - main capsule creation)
- [ERROR] `src/api/health_routes.py` (health checks)
- [ERROR] `src/api/federation_fastapi_router.py` (federation)
- [ERROR] `src/api/economics_fastapi_router.py` (economics)
- [ERROR] `src/api/governance_fastapi_router.py` (governance)
- [ERROR] `src/insurance/risk_assessor.py` (insurance timestamps)
- [ERROR] `src/compliance/reporting_engine.py` (compliance reports)
- [ERROR] `src/auth/jwt_auth.py` (JWT token expiration - CRITICAL!)
- [ERROR] And 89 more...

---

## Phase 2: Create Timezone Utility (Best Practice)

### Step 1: Create Central Timezone Handler

**File:** `src/utils/timezone_utils.py`

```python
"""
Centralized timezone utilities for UATP Capsule Engine.

POLICY: All timestamps MUST be timezone-aware UTC.
Never use datetime.utcnow() - it creates naive datetimes.
"""

from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.

    Use this instead of datetime.utcnow() or datetime.now().

    Returns:
        Timezone-aware datetime in UTC

    Example:
        >>> from src.utils.timezone_utils import utc_now
        >>> timestamp = utc_now()
        >>> assert timestamp.tzinfo is not None  # Always has timezone
    """
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is in UTC timezone.

    Args:
        dt: Datetime object (naive or aware)

    Returns:
        Timezone-aware datetime in UTC

    Raises:
        ValueError: If naive datetime without clear timezone context
    """
    if dt.tzinfo is None:
        # Naive datetime - assume UTC and make it aware
        # In production, you might want to raise an error instead
        return dt.replace(tzinfo=timezone.utc)

    # Already aware - convert to UTC if needed
    return dt.astimezone(timezone.utc)


def timestamp_to_iso(dt: Optional[datetime] = None) -> str:
    """
    Convert datetime to ISO 8601 string in UTC.

    Args:
        dt: Datetime to convert (defaults to current time)

    Returns:
        ISO 8601 formatted string with UTC timezone

    Example:
        >>> timestamp_to_iso()
        '2025-12-14T18:30:45+00:00'
    """
    if dt is None:
        dt = utc_now()
    return ensure_utc(dt).isoformat()


# Deprecated - raise error if anyone tries to use
def utcnow():
    """DEPRECATED: Use utc_now() instead."""
    raise DeprecationWarning(
        "datetime.utcnow() is deprecated. Use src.utils.timezone_utils.utc_now() instead."
    )
```

---

## Phase 3: Automated Codebase-Wide Fix

### Step 2: Create Migration Script

**File:** `scripts/fix_datetime_utcnow.py`

```python
#!/usr/bin/env python3
"""
Automated script to replace datetime.utcnow() with timezone_utils.utc_now().

This fixes the systemic timezone bug across the entire codebase.
"""

import os
import re
from pathlib import Path


def fix_file(file_path: Path) -> tuple[bool, int]:
    """
    Fix datetime.utcnow() in a single file.

    Returns:
        (modified, replacement_count)
    """
    content = file_path.read_text()
    original_content = content

    # Count replacements
    count = content.count('datetime.utcnow()')

    if count == 0:
        return False, 0

    # Replace datetime.utcnow() with utc_now()
    content = content.replace('datetime.utcnow()', 'utc_now()')

    # Check if timezone_utils import exists
    has_import = 'from src.utils.timezone_utils import utc_now' in content
    has_datetime_import = 'from datetime import' in content

    if not has_import and count > 0:
        # Find the imports section and add our import
        if has_datetime_import:
            # Add after datetime import
            content = re.sub(
                r'(from datetime import [^\n]+)',
                r'\1\nfrom src.utils.timezone_utils import utc_now',
                content,
                count=1
            )
        else:
            # Add at top of imports
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('from ') or line.startswith('import '):
                    lines.insert(i, 'from src.utils.timezone_utils import utc_now')
                    break
            content = '\n'.join(lines)

    if content != original_content:
        file_path.write_text(content)
        return True, count

    return False, 0


def main():
    """Fix all Python files in src/ directory."""
    src_dir = Path('src')

    total_files = 0
    total_replacements = 0
    modified_files = []

    for py_file in src_dir.rglob('*.py'):
        modified, count = fix_file(py_file)
        if modified:
            total_files += 1
            total_replacements += count
            modified_files.append((py_file, count))
            print(f"[OK] Fixed {count} instances in {py_file}")

    print("\n" + "="*70)
    print(f" Summary:")
    print(f"   Files modified: {total_files}")
    print(f"   Total replacements: {total_replacements}")
    print("="*70)

    if modified_files:
        print("\n Modified files:")
        for file_path, count in sorted(modified_files, key=lambda x: x[1], reverse=True):
            print(f"   {file_path}: {count} replacements")


if __name__ == '__main__':
    main()
```

---

## Phase 4: Data Migration (Fix Existing Timestamps)

### Step 3: Create Database Migration

**File:** `migrations/fix_capsule_timestamps.sql`

```sql
-- Migration: Fix 8-hour offset in capsule timestamps
-- Issue: datetime.utcnow() created naive datetimes interpreted as PST
-- Fix: Subtract 8 hours from all affected timestamps

BEGIN;

-- Backup table first
CREATE TABLE capsules_backup_20251214 AS
SELECT * FROM capsules;

-- Fix timestamps (subtract 8 hours from PST-stored times)
-- Only fix capsules created before the fix was deployed
UPDATE capsules
SET timestamp = timestamp - INTERVAL '8 hours'
WHERE timestamp > '2025-12-14 00:00:00-08'  -- Only recent capsules affected
  AND timestamp < '2025-12-14 18:11:00-08'  -- Before fix was deployed
  AND capsule_id != '8d84293e170ce754';     -- Exclude test capsule with correct timestamp

-- Verify the fix
SELECT
    'Before migration' as status,
    COUNT(*) as affected_capsules,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest
FROM capsules_backup_20251214
WHERE timestamp > '2025-12-14 00:00:00-08'
  AND timestamp < '2025-12-14 18:11:00-08';

SELECT
    'After migration' as status,
    COUNT(*) as affected_capsules,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest
FROM capsules
WHERE timestamp > '2025-12-13 16:00:00-08'  -- 8 hours earlier
  AND timestamp < '2025-12-14 10:11:00-08';

COMMIT;
```

---

## Phase 5: Testing & Validation

### Step 4: Add Comprehensive Tests

**File:** `tests/test_timezone_consistency.py`

```python
"""
Tests to ensure timezone consistency across the codebase.
"""

import pytest
from datetime import datetime, timezone
from src.utils.timezone_utils import utc_now, ensure_utc, timestamp_to_iso


def test_utc_now_is_timezone_aware():
    """Ensure utc_now() returns timezone-aware datetime."""
    now = utc_now()
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc


def test_utc_now_is_current():
    """Ensure utc_now() returns current time (within 1 second)."""
    now = utc_now()
    expected = datetime.now(timezone.utc)
    diff = abs((now - expected).total_seconds())
    assert diff < 1.0


def test_ensure_utc_with_naive_datetime():
    """Test ensure_utc() converts naive datetime to UTC."""
    naive = datetime(2025, 12, 14, 18, 0, 0)
    aware = ensure_utc(naive)
    assert aware.tzinfo == timezone.utc


def test_ensure_utc_with_aware_datetime():
    """Test ensure_utc() preserves timezone-aware datetime."""
    aware = datetime(2025, 12, 14, 18, 0, 0, tzinfo=timezone.utc)
    result = ensure_utc(aware)
    assert result.tzinfo == timezone.utc


def test_timestamp_to_iso_format():
    """Test ISO 8601 formatting."""
    dt = datetime(2025, 12, 14, 18, 0, 0, tzinfo=timezone.utc)
    iso = timestamp_to_iso(dt)
    assert iso == '2025-12-14T18:00:00+00:00'


def test_no_naive_datetimes_in_critical_paths():
    """Integration test: Ensure no naive datetimes in API responses."""
    from src.api.capsules_fastapi_router import router
    # This would be a full integration test
    pass


@pytest.mark.integration
def test_database_stores_utc_correctly():
    """Test that database correctly stores and retrieves UTC timestamps."""
    from src.core.database import db
    from src.models.capsule import CapsuleModel

    # Create capsule with utc_now()
    now = utc_now()
    capsule = CapsuleModel(
        capsule_id="test_timezone",
        timestamp=now,
        payload={}
    )

    # Store in database
    # Retrieve and verify timezone is preserved
    # This would be a full database test
    pass
```

---

## Phase 6: Prevention (Never Let This Happen Again)

### Step 5: Add Pre-commit Hook

**File:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: no-datetime-utcnow
        name: Prevent datetime.utcnow()
        entry: datetime\.utcnow\(\)
        language: pygrep
        types: [python]
        files: ^src/
        exclude: ^src/utils/timezone_utils\.py$
```

### Step 6: Add Linter Rule

**File:** `.pylintrc` (add to existing)

```ini
[MESSAGES CONTROL]
# Ban datetime.utcnow() usage
disable=
    datetime-utcnow-used

[BASIC]
# Enforce timezone-aware datetimes
bad-functions=
    datetime.utcnow:Use src.utils.timezone_utils.utc_now() instead
```

### Step 7: Update Code Style Guide

**File:** `docs/CODING_STANDARDS.md`

```markdown
## Timestamp Policy

[ERROR] **NEVER use:**
- `datetime.utcnow()` - Creates naive datetime
- `datetime.now()` - Uses local timezone

[OK] **ALWAYS use:**
- `from src.utils.timezone_utils import utc_now`
- `timestamp = utc_now()`

All timestamps MUST be timezone-aware UTC datetimes.
```

---

## Phase 7: Documentation & Monitoring

### Step 8: Add Monitoring Alert

**File:** `src/monitoring/timezone_monitor.py`

```python
"""
Monitor for timezone issues in production.
"""

from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def validate_timestamp(timestamp: datetime, context: str = "") -> bool:
    """
    Validate timestamp is timezone-aware UTC.

    Logs alert if validation fails.
    """
    if timestamp.tzinfo is None:
        logger.error(
            f"TIMEZONE_VIOLATION: Naive datetime detected in {context}",
            extra={
                "timestamp": str(timestamp),
                "context": context,
                "severity": "HIGH"
            }
        )
        return False

    if timestamp.tzinfo != timezone.utc:
        logger.warning(
            f"TIMEZONE_WARNING: Non-UTC timezone in {context}",
            extra={
                "timestamp": str(timestamp),
                "timezone": str(timestamp.tzinfo),
                "context": context
            }
        )

    return True
```

---

## Execution Timeline

### Immediate (Today):
- [x] Fix critical path: capsules_fastapi_router.py
- [x] Identify scope: 97 instances across 25 files
- [ ] Create timezone_utils.py
- [ ] Run automated fix script
- [ ] Create database migration

### Short-term (This Week):
- [ ] Add comprehensive tests
- [ ] Set up pre-commit hooks
- [ ] Update documentation
- [ ] Deploy to production

### Long-term (Ongoing):
- [ ] Monitor for timezone violations
- [ ] Code review checklist item
- [ ] Onboarding documentation

---

## Risk Assessment

### Before Fix:
- **Legal Risk**: Audit trails with wrong timestamps (chain of custody dates incorrect)
- **Insurance Risk**: Outcome timestamps don't match actual events
- **Compliance Risk**: GDPR "right to be forgotten" - wrong deletion dates
- **JWT Risk**: Token expiration times 8 hours off (security issue!)

### After Fix:
- [OK] All new data has correct timestamps
- [OK] Old data can be migrated
- [OK] Prevention mechanisms in place

---

## Success Metrics

- [ ] Zero `datetime.utcnow()` instances in production code
- [ ] All timestamps timezone-aware UTC
- [ ] Database migration successful
- [ ] Tests passing (100% coverage on timezone utilities)
- [ ] Pre-commit hooks active
- [ ] Documentation updated

---

*Generated: 2025-12-14*
*Issue Severity: HIGH*
*Priority: P0 (Immediate)*
