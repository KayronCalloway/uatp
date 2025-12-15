# API Architecture Documentation

## Overview

The UATP Capsule Engine uses a FastAPI-based REST API architecture with async PostgreSQL database access via SQLAlchemy ORM.

## Request Flow

```
Client Request
    ↓
run.py (Entry Point)
    ↓
Uvicorn ASGI Server
    ↓
src.main:app (ASGI Application)
    ↓
src.app_factory:create_app()
    ↓
FastAPI Application Instance
    ↓
Router: src/api/capsules_fastapi_router.py ✅ ACTIVE
    ↓
Database: PostgreSQL (async via SQLAlchemy)
```

## Critical Files

### Active Router (USE THIS)
- **File**: `/src/api/capsules_fastapi_router.py`
- **Framework**: FastAPI
- **Status**: ✅ **ACTIVE - This is the router being used**
- **Features**:
  - Demo mode filtering (`demo_mode=false` excludes 'demo-*' capsules)
  - Environment filtering (`include_test` parameter)
  - Pagination support
  - SQLAlchemy ORM queries
  - UATP 7.0 capsule format

### Deprecated Router (DO NOT EDIT)
- **File**: `/src/api/DEPRECATED_capsule_routes.py.old`
- **Framework**: Quart (Async Flask)
- **Status**: ⚠️ **DEPRECATED - Not used by application**
- **Note**: This file exists for reference but is NOT loaded by the application

## Application Entry Points

### run.py
Primary entry point for the API server.

```python
uvicorn.run(
    "src.main:app",  # Import string enables reload and workers
    host=host,
    port=port,
    reload=reload,
)
```

### src/main.py
ASGI application factory.

```python
from .app_factory import create_app

def create_asgi_app():
    """Create production-ready ASGI application"""
    app = create_app()
    return app

app = create_asgi_app()
```

### src/app_factory.py
Application configuration and router registration.

```python
from .api.capsules_fastapi_router import router as capsules_router

def create_app():
    app = FastAPI(title="UATP Capsule Engine API")
    app.include_router(capsules_router)
    return app
```

## Key API Endpoints

### GET /capsules
List capsules with filtering and pagination.

**Query Parameters**:
- `page` (int, default=1): Page number
- `per_page` (int, default=10, max=100): Items per page
- `type` (str, optional): Filter by capsule type
- `environment` (str, optional): Filter by environment (test|development|production)
- `include_test` (bool, default=false): Include test data
- `demo_mode` (bool, default=false): Include demo capsules

**Default Behavior**:
- Excludes capsules with IDs starting with 'demo-'
- Excludes test environment capsules
- Returns paginated results

**Example**:
```bash
# Get real capsules only (default)
curl "http://localhost:8000/capsules?demo_mode=false&per_page=10"

# Get all capsules including demos
curl "http://localhost:8000/capsules?demo_mode=true&per_page=10"
```

### GET /capsules/{capsule_id}
Get a specific capsule by ID.

### POST /capsules
Create a new capsule.

### GET /capsules/{capsule_id}/verify
Verify capsule cryptographic integrity.

### GET /capsules/stats
Get capsule statistics (counts by type, platform, recent activity).

## Database Layer

### Technology Stack
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy (async)
- **Driver**: asyncpg
- **Connection Pool**: Managed by SQLAlchemy async engine

### Capsule Model
Location: `src/models/capsule.py`

**Schema**:
- `id` (Primary Key)
- `capsule_id` (Unique, indexed)
- `capsule_type` (Indexed)
- `version`
- `timestamp` (Indexed)
- `status`
- `verification` (JSONB)
- `payload` (JSONB)

### Database Session Management
```python
async def get_db_session():
    """Dependency to get database session"""
    async with db.get_session() as session:
        yield session
```

## Filtering Implementation

### Demo Mode Filtering
Implemented at the database query level using SQLAlchemy:

```python
# Exclude demo capsules (default behavior)
if not demo_mode:
    query = query.where(~CapsuleModel.capsule_id.like('demo-%'))
```

This filtering is applied to:
1. Main list query
2. Count query (for pagination totals)

### Environment Filtering
Uses JSONB queries on PostgreSQL:

```python
# Exclude test environment by default
if not include_test:
    query = query.where(
        text("(payload::jsonb->'metadata'->>'environment' IS NULL OR "
             "payload::jsonb->'metadata'->>'environment' != 'test')")
    )
```

## Testing the API

### Direct SQL Testing
File: `test_sql_filtering.py`

Tests filtering at the raw SQL level to verify database queries work correctly.

### API Testing
```bash
# Test demo mode filtering
curl "http://localhost:8000/capsules?demo_mode=false&per_page=3"
curl "http://localhost:8000/capsules?demo_mode=true&per_page=3"

# Test environment filtering
curl "http://localhost:8000/capsules?environment=production&per_page=10"
curl "http://localhost:8000/capsules?include_test=true&per_page=10"
```

## Common Pitfalls

### ⚠️ Editing the Wrong Router
**Problem**: Multiple router implementations exist in the codebase (FastAPI and Quart versions).

**Solution**: Always edit `src/api/capsules_fastapi_router.py`. The Quart router (`DEPRECATED_capsule_routes.py.old`) is not loaded by the application.

**How to Verify**:
1. Check `src/app_factory.py` for which router is imported
2. Look for the file with clear "ACTIVE ROUTER" documentation header

### ⚠️ Cache Confusion
**Problem**: Response caching middleware might appear to interfere with requests.

**Reality**: The cache system only sets HTTP headers, it doesn't cache actual responses at the router level.

### ⚠️ Server Restarts
**Problem**: Changes not applying after code edits.

**Solution**:
1. Ensure you're editing the correct file (FastAPI router)
2. Restart the server: `kill $(cat api_server.pid) && python3 run.py &`
3. Check logs: `tail -f api_server.log`

## Architecture Decisions

### Why FastAPI over Quart?
- Better async performance
- Superior OpenAPI/Swagger documentation generation
- Stronger type validation via Pydantic
- More active community and ecosystem

### Why SQLAlchemy ORM vs Raw SQL?
- Type safety and IDE support
- Protection against SQL injection
- Easier database migration support
- Better testability with mocking

### Why Exclude Demo Capsules by Default?
- Production environments should show real data by default
- Prevents confusion between test/demo and production data
- Explicit opt-in (demo_mode=true) when demos are needed
- Follows principle of least surprise for end users

## Development Workflow

### Making Changes to the API

1. **Edit the correct router**: `src/api/capsules_fastapi_router.py`
2. **Test locally**:
   ```bash
   python3 run.py
   curl "http://localhost:8000/capsules?demo_mode=false"
   ```
3. **Verify filtering works**:
   ```bash
   # Should exclude demo-* capsules
   curl "http://localhost:8000/capsules?demo_mode=false" | jq '.capsules[].id'
   ```
4. **Check logs**: `tail -f api_server.log`

### Adding New Endpoints

1. Add route to `capsules_fastapi_router.py`
2. Use FastAPI dependencies for database session
3. Follow existing patterns for error handling
4. Update this documentation

## Monitoring and Debugging

### Server Status
```bash
# Check if server is running
cat api_server.pid
lsof -ti:8000

# View logs
tail -f api_server.log

# Test health
curl http://localhost:8000/health
```

### Database Queries
Enable SQL logging in `src/core/database.py`:
```python
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Enable SQL logging
)
```

### Request Tracing
Each request logs to `api_server.log` with:
- Timestamp
- Client IP
- HTTP method and path
- Response status code

## Version History

### Current: UATP 7.0
- All capsules use version 7.0 format
- Capsule types: economic_transaction, reasoning_trace, etc.
- Enhanced verification with cryptographic signatures
- JSONB payload structure for flexibility

## References

- FastAPI Documentation: https://fastapi.tiangolo.com/
- SQLAlchemy Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- UATP White Paper: `/UATP_White_Paper.docx`
- System Overview: `/SYSTEM_OVERVIEW.md`
