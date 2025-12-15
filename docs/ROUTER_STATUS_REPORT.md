# Router Registration Status Report
## Generated: 2025-12-04

## Executive Summary

**Problem**: Many frontend tabs return 404 errors because their backend endpoints aren't registered in `app_factory.py`.

**Root Cause**: The application uses FastAPI, but 39 route files are written for Quart (incompatible framework). Only 8 FastAPI-compatible routers are currently available and registered.

**Current Status**:
- ✅ **7 Routers Registered** (working)
- ⚠️ **1 FastAPI Router Available** but not registered
- ❌ **39 Quart Blueprints** require conversion to FastAPI before registration

---

## Currently Registered Routers (Working ✅)

These routers are registered in `app_factory.py` and fully functional:

| Router | File | Status | Endpoints |
|--------|------|--------|-----------|
| auth | src/auth/auth_routes.py | ✅ Working | /auth/* |
| constellations | src/api/constellations_routes.py | ✅ Working | /constellations/* |
| capsules | src/api/capsules_fastapi_router.py | ✅ Working | /capsules, /capsules/{id}, /capsules/stats |
| live_capture | src/api/live_capture_fastapi_router.py | ✅ Working | /live_capture/* |
| trust | src/api/trust_fastapi_router.py | ✅ Working | /trust/metrics, /trust/* |
| onboarding | src/api/onboarding_fastapi_router.py | ✅ Working | /onboarding/* |
| insurance | src/insurance/api.py | ✅ Working | /insurance/* |

---

## FastAPI Routers Available But Not Registered

These routers are FastAPI-compatible and can be registered immediately:

| Router | File | Priority | Frontend Impact |
|--------|------|----------|----------------|
| enterprise | src/api/enterprise_api.py | **HIGH** | Enterprise features tab |

**Action Required**: Add `app.include_router(enterprise_router)` to `app_factory.py`

---

## Quart Blueprints (Require Conversion ⚠️)

These 39 files use Quart framework and CANNOT be registered without conversion to FastAPI:

### HIGH PRIORITY (Frontend Tabs Expect These)

| File | Expected Endpoint | Frontend Tab | Conversion Effort |
|------|-------------------|--------------|-------------------|
| governance_routes.py | /governance | Governance Dashboard | Medium (has mock data) |
| economics_routes.py | /economics | Economic Metrics | Medium (has mock data) |
| federation_routes.py | /federation | Federation Nodes | Medium (has mock data) |
| reasoning_api.py | /reasoning | Reasoning Analysis | High (complex logic) |
| mirror_mode_api.py | /mirror | Mirror Mode Audit | High (complex logic) |
| akc_routes.py | /akc | AKC Dashboard | Medium |
| platform_routes.py | /platform | Platform Integration | Medium |

### MEDIUM PRIORITY

| File | Expected Endpoint | Notes |
|------|-------------------|-------|
| ai_routes.py | /ai | AI integration features |
| auto_capture_routes.py | /auto_capture | Live capture automation |
| chain_routes.py | /chain | Capsule chain operations |
| organization_routes.py | /organization | Organization management |
| spatial_routes.py | /spatial | Spatial intelligence |
| monitoring_routes.py | /monitoring | System monitoring |
| mobile_routes.py | /mobile | Mobile API |
| user_routes.py | /user | User management |
| webauthn_routes.py | /webauthn | WebAuthn authentication |
| security_routes.py | /security | Security dashboard |
| cursor_routes.py | /cursor | Cursor AI integration |

### LOW PRIORITY (Utilities/Middleware)

These files provide support functionality but don't directly expose endpoints:

- agent_spending_middleware.py
- auth_api.py (duplicate of auth_routes?)
- auth_utils.py
- cache.py
- compliance_api.py
- custom_quart.py
- dependencies.py
- health_routes.py
- metrics.py
- monitoring_api.py
- openapi_spec.py
- payment_integration_api.py
- rate_limiting.py
- rights_evolution_advanced.py
- rights_evolution_api.py
- security_dashboard.py
- security_middleware.py
- structured_logging.py
- trust_routes.py (duplicate of trust_fastapi_router?)
- bonds_citizenship_api.py
- capsule_api.py (duplicate of capsules_fastapi_router?)
- live_capture_routes.py (duplicate of live_capture_fastapi_router?)

---

## Conversion Strategy

### Quick Win: Register Enterprise Router
**Effort**: 5 minutes
**Impact**: Eliminates 1 set of 404s immediately

```python
# In src/app_factory.py, add:
from .api.enterprise_api import router as enterprise_router
app.include_router(enterprise_router)
```

### Phase 1: Convert Critical 7 Routes (HIGH PRIORITY)
**Effort**: 2-3 hours per route
**Impact**: Eliminates most frontend 404s

Convert these Quart routes to FastAPI:
1. governance_routes.py → governance_fastapi_router.py
2. economics_routes.py → economics_fastapi_router.py
3. federation_routes.py → federation_fastapi_router.py
4. reasoning_api.py → reasoning_fastapi_router.py
5. mirror_mode_api.py → mirror_mode_fastapi_router.py
6. akc_routes.py → akc_fastapi_router.py
7. platform_routes.py → platform_fastapi_router.py

**Conversion Pattern**:
```python
# FROM (Quart):
from quart import Blueprint, jsonify
bp = Blueprint("governance", __name__)

@bp.route("/proposals", methods=["GET"])
async def get_proposals():
    return jsonify({"data": []})

# TO (FastAPI):
from fastapi import APIRouter
router = APIRouter(prefix="/governance", tags=["Governance"])

@router.get("/proposals")
async def get_proposals():
    return {"data": []}
```

### Phase 2: Convert Medium Priority Routes
**Effort**: 1-2 hours per route
**Impact**: Completes remaining frontend functionality

Convert the 12 medium-priority routes listed above.

### Phase 3: Clean Up Duplicates
**Effort**: 1 hour
**Impact**: Removes confusion, consolidates codebase

Identify and remove duplicate route files:
- Is `auth_api.py` the same as `auth_routes.py`?
- Is `capsule_api.py` the same as `capsules_fastapi_router.py`?
- Is `trust_routes.py` the same as `trust_fastapi_router.py`?

---

## Testing Plan

After each router is registered:

1. **Restart API server**:
   ```bash
   kill $(cat api_server.pid)
   python3 run.py &
   ```

2. **Test endpoint**:
   ```bash
   curl http://localhost:8000/{endpoint}
   ```

3. **Verify no 404**:
   - Should return JSON data (even if mock)
   - Should NOT return `{"detail":"Not Found"}`

4. **Test from frontend**:
   - Navigate to corresponding tab
   - Verify data loads
   - Check browser console for errors

---

## Recommended Immediate Actions

1. ✅ **Register enterprise_api** (5 minutes, immediate impact)
2. **Convert governance_routes.py** (first critical route with mock data already implemented)
3. **Convert economics_routes.py** (second critical route with mock data)
4. **Convert federation_routes.py** (third critical route with mock data)
5. Test all three endpoints and verify frontend tabs load

**Estimated Time for Steps 1-5**: 3-4 hours
**Impact**: Eliminates 404s on 4 major frontend tabs

---

## Architecture Notes

### Why Not Mix Quart and FastAPI?

**Cannot be done**: Quart uses async Flask patterns with Blueprints, FastAPI uses Starlette with APIRouters. They are fundamentally incompatible ASGI frameworks.

**Options**:
1. ✅ Convert Quart → FastAPI (recommended, maintains single framework)
2. ❌ Run separate Quart app (doubles infrastructure, confusing)
3. ❌ Proxy Quart through FastAPI (overly complex, performance overhead)

### FastAPI Conversion Benefits

- Better performance (Starlette is faster than Quart)
- Superior OpenAPI/Swagger documentation
- Stronger type validation with Pydantic
- More active community and ecosystem
- Consistent with current architecture

---

## Files Breakdown

**Total API Files**: 63
- **FastAPI-compatible**: 8 (13%)
  - Already registered: 7 ✅
  - Not registered: 1 (enterprise_api.py)
- **Quart-based**: 39 (62%)
  - High priority: 7
  - Medium priority: 12
  - Low priority/utilities: 20
- **Other** (utilities, tests): 16 (25%)

---

## Next Steps

1. Mark this task as complete
2. Register enterprise_api router
3. Start converting high-priority Quart routes
4. Test after each conversion
5. Update this document as progress is made

---

## References

- FastAPI Documentation: https://fastapi.tiangolo.com/
- Quart to FastAPI Migration Guide: https://fastapi.tiangolo.com/alternatives/#quart
- Current Router Registration: `src/app_factory.py:614-638`
- API Architecture Doc: `docs/API_ARCHITECTURE.md`
