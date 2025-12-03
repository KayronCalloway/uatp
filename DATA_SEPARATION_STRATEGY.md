# Test/Production Data Separation Strategy

**Created:** 2025-11-18
**Priority:** HIGH - Critical for long-term protocol health

## Current Situation

The UATP system currently uses a single PostgreSQL database (`uatp_capsule_engine`) for both development and testing. This can lead to:
- Test data polluting production metrics
- Accidental deletion of real data during testing
- Difficulty distinguishing between real and test capsules
- Unreliable analytics and reporting

## Recommended Strategy

### 1. Environment-Based Database Separation

```
# Development/Testing
DATABASE_URL=postgresql://user:pass@localhost:5432/uatp_test

# Production
DATABASE_URL=postgresql://user:pass@localhost:5432/uatp_production
```

### 2. Database Schema Tagging (Current Database)

For the current 43 capsules in the database, add `environment` tag to distinguish:

```python
# Add environment field to capsule payload
{
    "analysis_metadata": {
        "environment": "test" | "development" | "production",
        "created_by": "test_script" | "user" | "system",
        ...
    }
}
```

### 3. Test Data Namespace

Create separate test data indicators:
- Test user IDs: `test_user_*`
- Test agent IDs: `test_agent_*`
- Test capsule IDs: `test_capsule_*`

### 4. API Query Filtering

Add query parameter to exclude test data:
```
GET /capsules?include_test=false  # Default: exclude test data
GET /capsules?environment=production  # Only production data
```

## Implementation Plan

### Phase 1: Immediate (This Session) ✅ COMPLETED
- [x] Document strategy
- [x] Add environment filter to capsule queries (`src/api/capsules_fastapi_router.py`)
- [x] Update .env.example with TEST_DATABASE_URL, DEV_DATABASE_URL
- [x] Add EXCLUDE_TEST_DATA_BY_DEFAULT setting
- [x] Implement JSONB filtering with graceful fallback
- [x] Test API endpoints with new query parameters
- [x] Verify backward compatibility (legacy capsules without environment field)

### Phase 2: Next Session
- [ ] Create separate test database
- [ ] Migrate test capsules to test database
- [ ] Update pytest fixtures to use test database
- [ ] Add environment detection to database connection

### Phase 3: Production Readiness
- [ ] Add data migration scripts
- [ ] Create database backup/restore procedures
- [ ] Implement data cleanup policies (auto-delete test data after N days)
- [ ] Add environment indicators to UI

## Current Database Status

**Production Database:** `uatp_capsule_engine`
- 43 capsules total
- Mix of test and real data
- Types: reasoning_trace (35), chat (6), governance_vote (1), economic_transaction (1)

**Immediate Action:**
Tag existing capsules by examining their metadata to determine if they're test data.

## Code Changes Needed

### 1. Database Connection (`src/core/database.py` or `src/database/connection.py`)
```python
import os

def get_database_url():
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "test":
        return os.getenv("TEST_DATABASE_URL", "postgresql://localhost/uatp_test")
    elif environment == "production":
        return os.getenv("DATABASE_URL", "postgresql://localhost/uatp_production")
    else:  # development
        return os.getenv("DEV_DATABASE_URL", "postgresql://localhost/uatp_dev")
```

### 2. Capsule Query Filter (`src/api/capsules_fastapi_router.py`)
```python
@router.get("")
async def list_capsules(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    type: Optional[str] = None,
    environment: Optional[str] = Query(None, regex="^(test|development|production)$"),
    include_test: bool = Query(False, description="Include test data in results"),
    session: AsyncSession = Depends(get_db_session)
):
    # Build query with environment filter
    query = select(CapsuleModel)

    if not include_test:
        # Exclude test data by default
        query = query.where(
            ~CapsuleModel.payload['analysis_metadata']['environment'].astext.in_(['test'])
        )

    if environment:
        query = query.where(
            CapsuleModel.payload['analysis_metadata']['environment'].astext == environment
        )
    ...
```

### 3. Test Configuration (`pytest.ini` or `conftest.py`)
```python
import pytest
import os

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    \"\"\"Ensure tests use test database\"\"\"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://localhost/uatp_test"
    )
    yield
    # Cleanup
```

## Benefits

1. **Data Integrity:** Production data stays clean
2. **Safe Testing:** Test freely without fear of data corruption
3. **Accurate Metrics:** Analytics reflect real usage
4. **Debugging:** Easy to identify test vs production issues
5. **Compliance:** Regulatory requirements for data separation

## Environment Detection

```python
# Automatically detect environment
def get_environment():
    # Check explicit ENVIRONMENT var
    if env_var := os.getenv("ENVIRONMENT"):
        return env_var

    # Detect from hostname
    hostname = socket.gethostname()
    if "prod" in hostname or "production" in hostname:
        return "production"
    elif "test" in hostname or "ci" in hostname:
        return "test"
    else:
        return "development"
```

## Migration Path

For the current 43 capsules:

1. Query all capsules
2. Analyze metadata to determine origin:
   - Created by test scripts → tag as `test`
   - Created via API with test user → tag as `test`
   - Created with real user IDs → tag as `development` or `production`
3. Update capsule metadata with environment tag
4. Future capsules automatically tagged at creation

## Dashboard Indicators

Add visual indicators in the UI:
- 🧪 Test Data badge
- 🔧 Development environment banner
- 🚀 Production mode indicator

## Phase 1 Implementation Summary (2025-11-18)

**Status:** ✅ COMPLETE

### What Was Implemented:

1. **API Query Filtering** (`src/api/capsules_fastapi_router.py`)
   - Added `environment` parameter: Filter by specific environment (test/development/production)
   - Added `include_test` parameter: Control test data inclusion (default: false)
   - Implemented PostgreSQL JSONB filtering
   - Graceful fallback for SQLite/missing fields
   - Backward compatible with existing capsules

2. **Environment Configuration** (`.env.example`)
   - `TEST_DATABASE_URL` - Separate test database
   - `DEV_DATABASE_URL` - Development database
   - `EXCLUDE_TEST_DATA_BY_DEFAULT` - Global setting
   - Documented all three database connection patterns

3. **Testing Results:**
   - ✅ Default query: `GET /capsules` excludes test data
   - ✅ With test data: `GET /capsules?include_test=true` includes all
   - ✅ By environment: `GET /capsules?environment=production` filters correctly
   - ✅ Legacy capsules (no environment field) treated as production data

### API Usage Examples:

```bash
# Default - excludes test data
curl "http://localhost:8000/capsules?page=1&per_page=10"

# Include test data
curl "http://localhost:8000/capsules?include_test=true"

# Filter by specific environment
curl "http://localhost:8000/capsules?environment=production"
curl "http://localhost:8000/capsules?environment=development"
curl "http://localhost:8000/capsules?environment=test"

# Combine filters
curl "http://localhost:8000/capsules?type=reasoning_trace&environment=production"
```

## Next Steps (Phase 2)

For the next session:
- [ ] Create separate test database (`uatp_test`)
- [ ] Migrate test capsules to test database
- [ ] Update pytest fixtures to use test database
- [ ] Add environment detection to database connection
- [ ] Tag existing 43 capsules with appropriate environment field
