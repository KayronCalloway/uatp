# PLATINUM FIX PLAN - Execution Roadmap

**Target**: Achieve 95+/100 (Platinum Standard)
**Current**: 82/100 (Gold Standard)
**Total Effort**: 126 hours across 20 fixes

---

## PHASE 1: BLOCKERS (P0) - 30 hours

### Fix 1: Missing `verify_capsule_signature` Function (4 hours)

**Problem**: Code calls non-existent function
**Files**:
- `src/insurance/risk_assessor.py:238`
- `src/insurance/claims_processor.py:551`

**Solution**:
```python
# Step 1: Update imports
from ..crypto_utils import verify_capsule

# Step 2: Replace verification logic
# OLD: if verify_capsule_signature(capsule):
# NEW: Proper verification with error handling

verification = capsule.get('verification', {})
public_key = verification.get('public_key')
signature = verification.get('signature')

if public_key and signature:
    is_valid, reason = verify_capsule(capsule, public_key, signature)
    if is_valid:
        valid_signatures += 1
```

**Files to modify**:
1. `src/insurance/risk_assessor.py` - Line 238
2. `src/insurance/claims_processor.py` - Line 551

---

### Fix 2: Missing `ClaimType.INCORRECT_OUTPUT` Enum (2 hours)

**Problem**: Tests and code reference non-existent enum value
**File**: `src/insurance/claims_processor.py:23-41`

**Solution**: Add missing enum value
```python
class ClaimType(str, Enum):
    AI_ERROR = "ai_error"
    AI_HARM = "ai_harm"
    DATA_BREACH = "data_breach"
    BIAS_DISCRIMINATION = "bias_discrimination"
    SYSTEM_FAILURE = "system_failure"
    INCORRECT_OUTPUT = "incorrect_output"  # ← ADD THIS
    OTHER = "other"
```

**Files to modify**:
1. `src/insurance/claims_processor.py` - Add enum value

---

### Fix 3: Fix Test Suite (8 hours)

**Problem**: 17 of 21 tests failing (81% failure rate)

**Sub-tasks**:

#### 3.1: Fix Attribute Name Mismatches (2 hours)
```python
# In tests/test_insurance_api.py:

# WRONG → CORRECT
assessment.overall_risk_level → assessment.risk_level
assessment.composite_score → assessment.overall_score
assessment.risk_factors → assessment.factors
assessment.insurability → (remove, doesn't exist)
```

**Lines to fix**: 178, 180, 195, 230, 494, 578, 593

#### 3.2: Fix Method Name Mismatches (1 hour)
```python
# WRONG → CORRECT
manager.check_claim_eligibility() → manager.check_policy_eligibility()
```

**Lines to fix**: 294, 308, 323

#### 3.3: Fix Constructor Arguments (2 hours)
```python
# Add policy_manager fixture
@pytest.fixture
def mock_policy_manager():
    return Mock(spec=PolicyManager)

# Update all ClaimsProcessor instantiations
processor = ClaimsProcessor(
    policy_manager=mock_policy_manager,  # ← ADD THIS
    database_manager=mock_db_manager
)
```

**Lines to fix**: 342, 362, 384, 406, 431, 456, 598

#### 3.4: Fix create_policy() Signature (1 hour)
```python
# Remove unexpected argument
policy = await manager.create_policy(
    holder=sample_policy_holder,
    terms=sample_policy_terms
    # payment_method_id="pm_test123"  ← REMOVE THIS
)
```

**Lines to fix**: 246-252

#### 3.5: Fix ClaimType References (1 hour)
```python
# Change all INCORRECT_OUTPUT to valid enum
claim_type=ClaimType.AI_ERROR  # or OTHER
```

**Lines to fix**: 349, 370, 391, 416, 438, 470, 520, 620

#### 3.6: Run and Verify Tests (1 hour)
```bash
python3 -m pytest tests/test_insurance_api.py -v
# Target: 21/21 passing (100%)
```

**Files to modify**:
1. `tests/test_insurance_api.py` - Multiple line fixes

---

### Fix 4: Add Authentication to All Endpoints (16 hours)

**Problem**: No authentication or authorization checks

**Sub-tasks**:

#### 4.1: Create Authentication Decorator (3 hours)
```python
# File: src/api/auth_decorators.py
from functools import wraps
from quart import request, jsonify, g
from src.auth.jwt_manager import verify_jwt_token

def require_auth(f):
    @wraps(f)
    async def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing authentication token"}), 401

        token = auth_header.split(' ')[1]
        try:
            payload = verify_jwt_token(token)
            g.current_user = payload
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 401

        return await f(*args, **kwargs)
    return decorated
```

#### 4.2: Create Authorization Helper (2 hours)
```python
# File: src/api/auth_decorators.py (continued)
def require_policy_access(f):
    @wraps(f)
    async def decorated(policy_id: str, *args, **kwargs):
        user = g.current_user
        policy = await policy_manager.get_policy(policy_id)

        if policy.holder.user_id != user['user_id'] and 'admin' not in user.get('roles', []):
            return jsonify({"error": "Unauthorized"}), 403

        return await f(policy_id, *args, **kwargs)
    return decorated
```

#### 4.3: Add Auth to All Endpoints (8 hours)
Apply decorators to 11 endpoints:
1. POST /risk-assessment
2. POST /policies
3. GET /policies/<id>
4. PUT /policies/<id>/activate
5. DELETE /policies/<id>
6. GET /policies
7. POST /claims
8. GET /claims/<id>
9. PUT /claims/<id>/approve
10. PUT /claims/<id>/deny
11. GET /claims

#### 4.4: Add Tests for Auth (3 hours)
Create `tests/test_insurance_auth.py`

**Files to create**:
1. `src/api/auth_decorators.py` - New file

**Files to modify**:
1. `src/api/insurance_routes.py` - Add decorators to all routes

---

## PHASE 2: SECURITY (P1) - 24 hours

### Fix 5: Add Input Validation (6 hours)

#### 5.1: Add Pydantic Validators (4 hours)

**File**: `src/api/insurance_routes.py:56-95`

```python
from pydantic import Field, field_validator
from decimal import Decimal

class PolicyCreationRequest(BaseModel):
    coverage_amount: int = Field(
        ...,
        gt=0,
        le=10_000_000,
        description="Coverage amount (max $10M)"
    )
    deductible: int = Field(
        default=1000,
        ge=0,
        le=100_000
    )
    term_months: int = Field(
        default=12,
        ge=1,
        le=60
    )
    decision_category: str = Field(...)

    @field_validator('coverage_amount')
    @classmethod
    def validate_coverage(cls, v):
        if v < 1000:
            raise ValueError("Minimum coverage is $1,000")
        if v % 1000 != 0:
            raise ValueError("Must be in $1,000 increments")
        return v

    @field_validator('deductible')
    @classmethod
    def validate_deductible(cls, v, info):
        coverage = info.data.get('coverage_amount', 0)
        if coverage > 0 and v > coverage * 0.1:
            raise ValueError("Deductible cannot exceed 10% of coverage")
        return v

class ClaimSubmissionRequest(BaseModel):
    policy_id: str = Field(..., min_length=1, max_length=100)
    claimed_amount: int = Field(..., gt=0, le=10_000_000)
    incident_description: str = Field(..., min_length=10, max_length=5000)
    capsule_chain: List[Dict] = Field(..., max_length=1000)

    @field_validator('capsule_chain')
    @classmethod
    def validate_chain(cls, v):
        if len(v) == 0:
            raise ValueError("Capsule chain cannot be empty")
        if len(v) > 1000:
            raise ValueError("Capsule chain too long (max 1000)")
        return v
```

#### 5.2: Add UUID Validation (1 hour)

```python
from uuid import UUID

def validate_uuid(value: str, field_name: str) -> str:
    try:
        UUID(value)
        return value
    except ValueError:
        raise ValueError(f"Invalid {field_name} format")

# Use in routes:
user_id = request.args.get("user_id")
if user_id:
    user_id = validate_uuid(user_id, "user_id")
```

#### 5.3: Add Tests (1 hour)

**Files to modify**:
1. `src/api/insurance_routes.py` - Update all request models

---

### Fix 6: Fix N+1 Queries (4 hours)

#### 6.1: Policy List Query (2 hours)

**File**: `src/insurance/policy_manager.py:690-764`

```python
from sqlalchemy.orm import selectinload

async def _query_policies(...) -> List[Policy]:
    query = select(DBPolicy).options(
        selectinload(DBPolicy.claims)  # Eager load related claims
    )

    # ... filters ...

    result = await session.execute(query)
    db_policies = result.unique().scalars().all()
```

#### 6.2: Claims List Query (2 hours)

**File**: `src/insurance/claims_processor.py:829-896`

```python
from sqlalchemy.orm import selectinload

async def _query_claims(...) -> List[Claim]:
    query = select(DBClaim).options(
        selectinload(DBClaim.policy),
        selectinload(DBClaim.event_logs)
    )

    # ... filters ...

    result = await session.execute(query)
    db_claims = result.unique().scalars().all()

    # No additional queries needed:
    for db_claim in db_claims:
        policy_number = db_claim.policy.policy_number  # Already loaded
```

**Files to modify**:
1. `src/insurance/policy_manager.py:690-764`
2. `src/insurance/claims_processor.py:829-896`

---

### Fix 7: Add Rate Limiting (6 hours)

#### 7.1: Install Rate Limiter (1 hour)

```bash
pip install quart-rate-limiter
```

#### 7.2: Configure Rate Limiter (2 hours)

**File**: `src/api/server.py`

```python
from quart_rate_limiter import RateLimiter, rate_limit

# Configure limits
app.config["RATELIMIT_STORAGE_URL"] = os.getenv("REDIS_URL", "memory://")
app.config["RATELIMIT_DEFAULT"] = "100 per minute"

limiter = RateLimiter(app)
```

#### 7.3: Apply to Endpoints (2 hours)

```python
# In insurance_routes.py:

@insurance_bp.route("/risk-assessment", methods=["POST"])
@rate_limit(10, timedelta(minutes=1))  # 10 assessments per minute
@require_auth
async def assess_risk():
    ...

@insurance_bp.route("/policies", methods=["POST"])
@rate_limit(5, timedelta(minutes=1))  # 5 policy creations per minute
@require_auth
async def create_policy():
    ...

@insurance_bp.route("/claims", methods=["POST"])
@rate_limit(10, timedelta(minutes=1))  # 10 claims per minute
@require_auth
async def submit_claim():
    ...
```

#### 7.4: Add Tests (1 hour)

**Files to modify**:
1. `src/api/server.py` - Configure rate limiter
2. `src/api/insurance_routes.py` - Add rate_limit decorators
3. `requirements.txt` - Add quart-rate-limiter

---

### Fix 8: Add Structured Logging (8 hours)

#### 8.1: Install and Configure structlog (2 hours)

```bash
pip install structlog
```

**File**: `src/config/logging_config.py`

```python
import structlog
import logging

def configure_structlog():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

#### 8.2: Replace print() Statements (3 hours)

Search and replace in:
- `src/insurance/policy_manager.py:761` - Replace print with logger.warning
- `src/insurance/claims_processor.py:893` - Replace print with logger.warning

```python
# OLD:
print(f"Warning: Failed to convert: {e}")

# NEW:
logger = structlog.get_logger()
logger.warning(
    "policy_conversion_failed",
    policy_id=db_policy.policy_number,
    error=str(e)
)
```

#### 8.3: Add Security Event Logging (2 hours)

```python
# In auth_decorators.py:
logger.info(
    "authentication_success",
    user_id=user['user_id'],
    endpoint=request.path
)

logger.warning(
    "authentication_failed",
    ip_address=request.remote_addr,
    endpoint=request.path
)

logger.critical(
    "unauthorized_access_attempt",
    user_id=user['user_id'],
    policy_id=policy_id,
    action="access_denied"
)
```

#### 8.4: Add Request ID Tracing (1 hour)

```python
# In server.py:
import uuid

@app.before_request
async def add_request_id():
    g.request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(request_id=g.request_id)

@app.after_request
async def add_request_id_header(response):
    response.headers['X-Request-ID'] = g.request_id
    return response
```

**Files to modify**:
1. `src/config/logging_config.py` - Configure structlog
2. `src/insurance/policy_manager.py` - Replace prints
3. `src/insurance/claims_processor.py` - Replace prints
4. `src/api/auth_decorators.py` - Add security logging
5. `src/api/server.py` - Add request ID
6. `requirements.txt` - Add structlog

---

## PHASE 3: PRODUCTION (P2) - 36 hours

### Fix 9: Add Prometheus Metrics (12 hours)

#### 9.1: Define Metrics (3 hours)

**File**: `src/observability/insurance_metrics.py` (new)

```python
from prometheus_client import Counter, Histogram, Gauge

# Risk assessment metrics
risk_assessments_total = Counter(
    'insurance_risk_assessments_total',
    'Total risk assessments performed',
    ['decision_category', 'risk_level']
)

risk_assessment_duration = Histogram(
    'insurance_risk_assessment_seconds',
    'Time to complete risk assessment',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

# Policy metrics
policies_created_total = Counter(
    'insurance_policies_created_total',
    'Total policies created',
    ['status']
)

policies_active = Gauge(
    'insurance_policies_active',
    'Number of active policies'
)

policy_premium_amount = Histogram(
    'insurance_policy_premium_usd',
    'Policy premium amounts',
    buckets=[50, 100, 200, 500, 1000, 2000]
)

# Claim metrics
claims_submitted_total = Counter(
    'insurance_claims_submitted_total',
    'Total claims submitted',
    ['claim_type']
)

claims_by_status = Gauge(
    'insurance_claims_by_status',
    'Claims grouped by status',
    ['status']
)

claim_approval_duration = Histogram(
    'insurance_claim_approval_seconds',
    'Time from submission to approval',
    buckets=[60, 300, 1800, 3600, 86400]  # 1min to 1day
)

claim_amount = Histogram(
    'insurance_claim_amount_usd',
    'Claim amounts',
    buckets=[100, 500, 1000, 5000, 10000, 50000]
)

# Database metrics
db_query_duration = Histogram(
    'insurance_db_query_seconds',
    'Database query duration',
    ['operation', 'table'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
)

# Error metrics
errors_total = Counter(
    'insurance_errors_total',
    'Total errors',
    ['error_type', 'operation']
)
```

#### 9.2: Instrument Risk Assessor (3 hours)

**File**: `src/insurance/risk_assessor.py`

```python
from src.observability.insurance_metrics import (
    risk_assessments_total,
    risk_assessment_duration
)

async def assess_capsule_chain(...):
    with risk_assessment_duration.time():
        # ... assessment logic ...

        risk_assessments_total.labels(
            decision_category=decision_category.value,
            risk_level=assessment.risk_level.value
        ).inc()

        return assessment
```

#### 9.3: Instrument Policy Manager (3 hours)

**File**: `src/insurance/policy_manager.py`

```python
from src.observability.insurance_metrics import (
    policies_created_total,
    policies_active,
    policy_premium_amount
)

async def create_policy(...):
    policy = Policy(...)

    policies_created_total.labels(
        status=policy.status.value
    ).inc()

    policy_premium_amount.observe(terms.premium_monthly)

    # Update active count
    active_count = await self._count_active_policies()
    policies_active.set(active_count)

    return policy
```

#### 9.4: Instrument Claims Processor (3 hours)

**File**: `src/insurance/claims_processor.py`

```python
from src.observability.insurance_metrics import (
    claims_submitted_total,
    claims_by_status,
    claim_amount
)

async def submit_claim(...):
    claim = Claim(...)

    claims_submitted_total.labels(
        claim_type=claim_type.value
    ).inc()

    claim_amount.observe(claimed_amount)

    # Update status counts
    await self._update_claim_metrics()

    return claim
```

**Files to create**:
1. `src/observability/insurance_metrics.py`

**Files to modify**:
1. `src/insurance/risk_assessor.py`
2. `src/insurance/policy_manager.py`
3. `src/insurance/claims_processor.py`
4. `requirements.txt` - Add prometheus_client

---

### Fix 10: Create Integration Tests (16 hours)

#### 10.1: Setup Test Database (3 hours)

**File**: `tests/integration/conftest.py` (new)

```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.core.database import DatabaseManager

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    # Use SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()

@pytest.fixture
async def db_session(test_db):
    async_session = sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()
```

#### 10.2: Test Risk Assessment Integration (3 hours)

**File**: `tests/integration/test_risk_assessment_integration.py` (new)

```python
import pytest
from src.insurance.risk_assessor import RiskAssessor

@pytest.mark.asyncio
async def test_complete_risk_assessment_workflow(db_session):
    assessor = RiskAssessor(database_manager=db_session)

    capsule_chain = [...]  # Real capsule data

    assessment = await assessor.assess_capsule_chain(
        capsule_chain=capsule_chain,
        decision_category=DecisionCategory.MEDICAL,
        requested_coverage=100000
    )

    assert assessment is not None
    assert assessment.risk_level in RiskLevel
    assert assessment.premium_estimate > 0
```

#### 10.3: Test Policy Lifecycle Integration (4 hours)

**File**: `tests/integration/test_policy_integration.py` (new)

```python
@pytest.mark.asyncio
async def test_complete_policy_lifecycle(db_session):
    manager = PolicyManager(database_manager=db_session)

    # Create policy
    policy = await manager.create_policy(...)
    assert policy.policy_id is not None

    # Activate policy
    activated = await manager.activate_policy(policy.policy_id)
    assert activated.status == PolicyStatus.ACTIVE

    # Fetch from DB
    fetched = await manager.get_policy(policy.policy_id)
    assert fetched.policy_id == policy.policy_id

    # List policies
    policies = await manager.list_policies()
    assert len(policies) > 0

    # Cancel policy
    cancelled = await manager.cancel_policy(policy.policy_id, "Test")
    assert cancelled.status == PolicyStatus.CANCELLED
```

#### 10.4: Test Claims Workflow Integration (3 hours)

**File**: `tests/integration/test_claims_integration.py` (new)

#### 10.5: Test API Endpoints Integration (3 hours)

**File**: `tests/integration/test_api_integration.py` (new)

**Files to create**:
1. `tests/integration/conftest.py`
2. `tests/integration/test_risk_assessment_integration.py`
3. `tests/integration/test_policy_integration.py`
4. `tests/integration/test_claims_integration.py`
5. `tests/integration/test_api_integration.py`

---

### Fix 11: Add Caching Layer (8 hours)

#### 11.1: Setup Redis Cache (2 hours)

**File**: `src/cache/redis_cache.py` (new)

```python
import redis.asyncio as redis
from typing import Optional, Any
import json
import os

class RedisCache:
    def __init__(self):
        self.redis = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            encoding="utf-8",
            decode_responses=True
        )

    async def get(self, key: str) -> Optional[Any]:
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: int = 300):
        await self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )

    async def delete(self, key: str):
        await self.redis.delete(key)
```

#### 11.2: Cache Risk Assessments (2 hours)

**File**: `src/insurance/risk_assessor.py`

```python
from src.cache.redis_cache import RedisCache
import hashlib

async def assess_capsule_chain(...):
    # Create cache key from capsule chain hash
    chain_hash = hashlib.sha256(
        json.dumps(capsule_chain).encode()
    ).hexdigest()
    cache_key = f"risk:assessment:{chain_hash}:{decision_category.value}"

    # Check cache
    cached = await self.cache.get(cache_key)
    if cached:
        return RiskAssessment(**cached)

    # Perform assessment
    assessment = ...

    # Cache result (5 min TTL)
    await self.cache.set(cache_key, assessment.__dict__, ttl=300)

    return assessment
```

#### 11.3: Cache Provider Scores (2 hours)

#### 11.4: Cache Policy Lookups (2 hours)

**Files to create**:
1. `src/cache/redis_cache.py`

**Files to modify**:
1. `src/insurance/risk_assessor.py`
2. `src/insurance/policy_manager.py`
3. `requirements.txt` - Add redis

---

## PHASE 4: OPTIMIZATION (P3) - 36 hours

### Fix 12-20: Additional Optimizations

(Detailed plans for remaining fixes...)

---

## EXECUTION CHECKLIST

### Pre-Execution
- [ ] Back up current codebase
- [ ] Create feature branch: `git checkout -b platinum-fixes`
- [ ] Verify test environment ready
- [ ] Review all file paths

### Execution Order
1. [ ] Phase 1: Fix Blockers (30h)
2. [ ] Run tests: Target 80%+ pass rate
3. [ ] Phase 2: Security (24h)
4. [ ] Security audit: No critical vulnerabilities
5. [ ] Phase 3: Production (36h)
6. [ ] Load test: 1000 RPS
7. [ ] Phase 4: Optimization (36h)
8. [ ] Final audit: Target 95+/100

### Post-Execution
- [ ] Run full test suite
- [ ] Run security scan
- [ ] Performance benchmark
- [ ] Documentation update
- [ ] Create PR with summary

---

## SUCCESS CRITERIA

**Phase 1 Complete**:
- [OK] All functions exist and work
- [OK] 21/21 tests passing (100%)
- [OK] All endpoints have authentication
- [OK] Can deploy to staging

**Phase 2 Complete**:
- [OK] All inputs validated
- [OK] Rate limiting on all endpoints
- [OK] No N+1 queries
- [OK] Structured logging everywhere
- [OK] Safe for beta users

**Phase 3 Complete**:
- [OK] Prometheus metrics on all operations
- [OK] Integration tests passing
- [OK] Redis caching working
- [OK] Production ready

**Platinum Standard Achieved**:
- [OK] Grade: 95+/100
- [OK] 100% test pass rate
- [OK] No security vulnerabilities
- [OK] <100ms response times
- [OK] Full observability

---

**Total Estimated Time**: 126 hours
**Phases**: 4 (Blockers → Security → Production → Optimization)
**Target Grade**: 95+/100 (Platinum)
