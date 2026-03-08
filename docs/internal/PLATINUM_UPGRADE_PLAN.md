# UATP Capsule Engine - Platinum Upgrade Action Plan

**Goal:** Achieve platinum-standard production readiness
**Timeline:** 3-4 weeks
**Current Grade:** A- (90/100) → Target: A+ (98/100)

---

##  Phase 1: Critical Blockers (Week 1)

### Priority 1.1: Fix Test Suite (Day 1)
**Status:** BLOCKING
**Owner:** Engineering
**Impact:** Cannot verify system correctness

**Actions:**
```bash
# 1. Fix dependency injection import error
# File: src/core/dependency_injection.py:396
# Current issue: ServiceScope.REQUEST reference fails

# 2. Run test suite
python3 -m pytest tests/ -v

# 3. Verify all tests pass
# Target: >50 tests passing
```

### Priority 1.2: Implement Database Persistence (Days 2-3)
**Status:** BLOCKING
**Owner:** Backend Engineering
**Impact:** Data loss risk, unusable for real customers

**Tasks:**

**A. Create Alembic Migrations**
```bash
# Create migrations for insurance tables
cd /Users/kay/uatp-capsule-engine

# Generate migration for policies table
alembic revision -m "create_insurance_policies_table"

# Generate migration for claims table
alembic revision -m "create_insurance_claims_table"

# Apply migrations
alembic upgrade head
```

**B. Implement PolicyManager Database Methods**
```python
# File: src/insurance/policy_manager.py

async def _store_policy(self, policy: Policy):
    """Store policy in PostgreSQL"""
    async with self.db.session() as session:
        policy_record = PolicyModel(
            policy_id=policy.policy_id,
            holder_user_id=policy.holder.user_id,
            holder_name=policy.holder.name,
            holder_email=policy.holder.email,
            # ... map all fields
        )
        session.add(policy_record)
        await session.commit()

async def _fetch_policy(self, policy_id: str) -> Policy:
    """Fetch policy from PostgreSQL"""
    async with self.db.session() as session:
        result = await session.execute(
            select(PolicyModel).where(PolicyModel.policy_id == policy_id)
        )
        policy_record = result.scalar_one_or_none()
        if not policy_record:
            raise NotFoundError(f"Policy {policy_id} not found")
        return self._map_to_policy(policy_record)
```

**C. Implement ClaimsProcessor Database Methods**
```python
# File: src/insurance/claims_processor.py

async def _store_claim(self, claim: Claim):
    """Store claim in PostgreSQL"""
    # Similar to policy storage

async def _fetch_claim(self, claim_id: str) -> Claim:
    """Fetch claim from PostgreSQL"""
    # Similar to policy fetch
```

**Acceptance Criteria:**
- [ ] All database TODO items completed
- [ ] Integration tests pass with real database
- [ ] Manual testing: create policy → retrieve policy → verify data

### Priority 1.3: Stripe Payment Integration (Days 4-5)
**Status:** BLOCKING
**Owner:** Backend Engineering
**Impact:** Cannot generate revenue

**Tasks:**

**A. Install Stripe SDK**
```bash
pip install stripe
echo "stripe>=8.0.0" >> requirements-production.txt
```

**B. Implement Payment Processing**
```python
# File: src/insurance/policy_manager.py

import stripe
import os

class PolicyManager:
    def __init__(self, ...):
        stripe.api_key = os.getenv("STRIPE_API_KEY")

    async def _process_payment(self, policy, amount, payment_method_id):
        """Process payment via Stripe"""
        try:
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency="usd",
                payment_method=payment_method_id,
                confirm=True,
                metadata={
                    "policy_id": policy.policy_id,
                    "user_id": policy.holder.user_id,
                    "type": "policy_payment"
                }
            )

            return {
                "success": True,
                "transaction_id": payment_intent.id,
                "amount": amount
            }

        except stripe.error.CardError as e:
            return {
                "success": False,
                "error": str(e.user_message)
            }
        except Exception as e:
            logger.error(f"Payment processing error: {e}")
            return {
                "success": False,
                "error": "Payment processing failed"
            }
```

**C. Set Up Stripe Webhooks**
```python
# File: src/api/billing_webhooks.py (NEW FILE)

from quart import Blueprint, request
import stripe

billing_webhooks_bp = Blueprint("billing_webhooks", __name__)

@billing_webhooks_bp.route("/stripe", methods=["POST"])
async def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = await request.get_data()
    sig_header = request.headers.get("Stripe-Signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return {"error": "Invalid payload"}, 400
    except stripe.error.SignatureVerificationError:
        return {"error": "Invalid signature"}, 400

    # Handle event types
    if event.type == "payment_intent.succeeded":
        await handle_payment_success(event.data.object)
    elif event.type == "payment_intent.payment_failed":
        await handle_payment_failure(event.data.object)

    return {"status": "success"}
```

**D. Add to server.py**
```python
from .billing_webhooks import billing_webhooks_bp
app.register_blueprint(billing_webhooks_bp, url_prefix="/webhooks/billing")
```

**Acceptance Criteria:**
- [ ] Stripe test mode working
- [ ] Payment success flow tested
- [ ] Payment failure flow tested
- [ ] Webhooks receiving events
- [ ] Refunds working

### Priority 1.4: Comprehensive Testing (Days 6-7)
**Status:** BLOCKING
**Owner:** QA + Engineering
**Impact:** Unknown bugs in production

**Tasks:**

**A. Create Insurance API Tests**
```python
# File: tests/test_insurance_api.py (NEW FILE)

import pytest
from src.insurance.risk_assessor import RiskAssessor, DecisionCategory

@pytest.mark.asyncio
async def test_risk_assessment_medical():
    """Test medical AI risk assessment"""
    assessor = RiskAssessor()

    capsule_chain = [
        {
            "capsule_id": "test_123",
            "messages": [{"role": "user", "content": "..."}],
            "provider": "anthropic",
            "timestamp": "2025-01-06T10:00:00Z",
            "signature": "valid_sig"
        }
    ]

    assessment = await assessor.assess_capsule_chain(
        capsule_chain=capsule_chain,
        decision_category=DecisionCategory.MEDICAL,
        requested_coverage=100000
    )

    assert assessment.risk_level in ["low", "medium", "high"]
    assert 0.0 <= assessment.overall_score <= 1.0
    assert assessment.premium_estimate.startswith("$")

@pytest.mark.asyncio
async def test_uninsurable_risk():
    """Test that high-risk cases are flagged as uninsurable"""
    assessor = RiskAssessor()

    # Create bad capsule chain (no signatures, tampering detected)
    bad_chain = [
        {
            "capsule_id": "bad_123",
            "tampered": True,
            "signature": None
        }
    ]

    assessment = await assessor.assess_capsule_chain(
        capsule_chain=bad_chain,
        decision_category=DecisionCategory.MEDICAL,
        requested_coverage=100000
    )

    assert assessment.risk_level == "uninsurable"

# Add 20+ more tests covering all scenarios
```

**B. Create Integration Tests**
```python
# File: tests/test_insurance_integration.py (NEW FILE)

@pytest.mark.asyncio
async def test_end_to_end_insurance_flow():
    """Complete flow: assessment → policy → claim → payout"""

    # 1. Risk assessment
    assessment = await risk_assessor.assess_capsule_chain(...)

    # 2. Create policy
    policy = await policy_manager.create_policy(...)
    assert policy.status == "active"

    # 3. File claim
    claim = await claims_processor.submit_claim(
        policy_id=policy.policy_id,
        ...
    )

    # 4. Verify claim processed
    await asyncio.sleep(1)  # Allow processing
    updated_claim = await claims_processor.get_claim(claim.claim_id)
    assert updated_claim.status in ["approved", "investigating"]
```

**C. Add Property-Based Tests**
```python
# File: tests/test_insurance_properties.py (NEW FILE)

from hypothesis import given, strategies as st

@given(
    coverage=st.integers(min_value=10000, max_value=10000000),
    risk_score=st.floats(min_value=0.0, max_value=1.0)
)
def test_premium_increases_with_coverage(coverage, risk_score):
    """Premium should increase monotonically with coverage"""
    premium1 = calculate_premium(coverage, risk_score)
    premium2 = calculate_premium(coverage * 2, risk_score)
    assert premium2 >= premium1

@given(
    coverage=st.integers(min_value=10000, max_value=1000000),
    risk_score=st.floats(min_value=0.0, max_value=0.85)
)
def test_premium_increases_with_risk(coverage, risk_score):
    """Premium should increase with risk score"""
    premium_low = calculate_premium(coverage, risk_score)
    premium_high = calculate_premium(coverage, min(risk_score + 0.1, 0.85))
    assert premium_high >= premium_low
```

**Target Coverage:**
- [ ] Unit tests: 80%+
- [ ] Integration tests: 60%+
- [ ] E2E tests: Critical paths
- [ ] All tests passing

---

##  Phase 2: Security & Performance (Week 2)

### Priority 2.1: Security Audit (Days 8-9)

**A. Run Security Scans**
```bash
# Install security tools
pip install bandit safety

# Run bandit (code security)
bandit -r src/ -f json -o security_report.json

# Run safety (dependency vulnerabilities)
safety check --json > dependencies_report.json

# Run OWASP dependency check
dependency-check --project uatp --scan . --format JSON
```

**B. Add Input Validation**
```python
# File: src/api/insurance_routes.py

from src.api.validation import validate_capsule_chain

@insurance_bp.route("/risk-assessment", methods=["POST"])
@limiter.limit("10 per minute")  # ← ADD RATE LIMITING
async def assess_risk():
    data = await request.get_json()
    req = RiskAssessmentRequest(**data)

    # Validate capsule chain length
    if len(req.capsule_chain) > 1000:  # ← ADD LIMIT
        return jsonify({"error": "Capsule chain too large (max: 1000)"}), 400

    # Validate coverage amount
    if req.requested_coverage > 10_000_000:  # ← ADD LIMIT
        return jsonify({"error": "Coverage amount too large (max: $10M)"}), 400

    # Continue processing...
```

**C. Add Security Headers**
```python
# File: src/api/security_middleware.py

@app.after_request
async def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

**Acceptance Criteria:**
- [ ] No critical vulnerabilities found
- [ ] No high-severity vulnerabilities
- [ ] All inputs validated
- [ ] Rate limiting on all endpoints
- [ ] Security headers added

### Priority 2.2: Performance Optimization (Days 10-11)

**A. Add Database Indexes**
```sql
-- File: alembic/versions/xxx_add_insurance_indexes.py

def upgrade():
    op.execute("""
        CREATE INDEX idx_policies_user_id ON insurance_policies(holder_user_id);
        CREATE INDEX idx_policies_status ON insurance_policies(status);
        CREATE INDEX idx_policies_expires_at ON insurance_policies(expires_at);

        CREATE INDEX idx_claims_policy_id ON insurance_claims(policy_id);
        CREATE INDEX idx_claims_user_id ON insurance_claims(claimant_user_id);
        CREATE INDEX idx_claims_status ON insurance_claims(status);
        CREATE INDEX idx_claims_submitted_at ON insurance_claims(submitted_at);
    """)
```

**B. Add Response Compression**
```python
# File: src/api/server.py

from quart_compress import Compress

def create_app(...):
    app = CustomQuart(__name__)

    # Add compression
    Compress(app)  # ← ADD THIS
    app.config["COMPRESS_ALGORITHM"] = "gzip"
    app.config["COMPRESS_LEVEL"] = 6
    app.config["COMPRESS_MIN_SIZE"] = 500
```

**C. Run Load Tests**
```python
# File: performance/locustfile.py

from locust import HttpUser, task, between

class UATPUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def risk_assessment(self):
        self.client.post("/api/v1/insurance/risk-assessment", json={
            "capsule_chain": [...],
            "decision_category": "medical",
            "requested_coverage": 100000
        }, headers={"Authorization": f"Bearer {API_KEY}"})

    @task(1)
    def list_policies(self):
        self.client.get("/api/v1/insurance/policies?user_id=test_user")
```

```bash
# Run load test
locust -f performance/locustfile.py --host=https://api-test.uatp.app --users 100 --spawn-rate 10
```

**Target Metrics:**
- [ ] 1000 RPS sustained
- [ ] P95 latency < 500ms
- [ ] P99 latency < 1000ms
- [ ] Error rate < 0.1%

**Acceptance Criteria:**
- [ ] Database indexes added
- [ ] Response compression enabled
- [ ] Load tests passing
- [ ] Performance metrics met

---

##  Phase 3: Observability (Days 12-14)

### Priority 3.1: Business Metrics

**Add Prometheus Metrics**
```python
# File: src/api/insurance_routes.py

from prometheus_client import Counter, Histogram, Gauge

# Define metrics
insurance_risk_assessments_total = Counter(
    'uatp_insurance_risk_assessments_total',
    'Total risk assessments performed',
    ['decision_category', 'risk_level']
)

insurance_policies_created_total = Counter(
    'uatp_insurance_policies_created_total',
    'Total insurance policies created',
    ['decision_category', 'risk_level']
)

insurance_claims_filed_total = Counter(
    'uatp_insurance_claims_filed_total',
    'Total insurance claims filed',
    ['claim_type', 'status']
)

insurance_premium_revenue = Gauge(
    'uatp_insurance_premium_revenue_total',
    'Total insurance premium revenue',
    ['currency']
)

# Instrument endpoints
@insurance_bp.route("/risk-assessment", methods=["POST"])
async def assess_risk():
    # ... existing code ...

    # Track metric
    insurance_risk_assessments_total.labels(
        decision_category=category.value,
        risk_level=assessment.risk_level.value
    ).inc()

    return jsonify(...)
```

### Priority 3.2: Error Tracking

**Set Up Sentry**
```python
# File: src/api/server.py

import sentry_sdk
from sentry_sdk.integrations.quart import QuartIntegration

def create_app(...):
    # Initialize Sentry
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[QuartIntegration()],
        traces_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "production")
    )
```

### Priority 3.3: Distributed Tracing

**Add OpenTelemetry**
```python
# File: src/insurance/risk_assessor.py

from opentelemetry import trace

tracer = trace.get_tracer(__name__)

class RiskAssessor:
    @tracer.start_as_current_span("assess_capsule_chain")
    async def assess_capsule_chain(self, ...):
        span = trace.get_current_span()
        span.set_attribute("capsule_chain_length", len(capsule_chain))
        span.set_attribute("decision_category", decision_category.value)

        # ... existing code ...

        span.set_attribute("risk_score", overall_score)
        span.set_attribute("risk_level", risk_level.value)
```

**Acceptance Criteria:**
- [ ] Business metrics tracked
- [ ] Sentry capturing errors
- [ ] Distributed tracing active
- [ ] Custom dashboards created

---

##  Phase 4: Deployment & CI/CD (Days 15-17)

### Priority 4.1: CI/CD Pipeline

**Create GitHub Actions Workflow**
```yaml
# File: .github/workflows/ci-cd.yml

name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: pytest tests/ --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Bandit
        run: bandit -r src/ -f json

      - name: Run Safety
        run: safety check

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -f Dockerfile.production -t uatp:${{ github.sha }} .

      - name: Push to registry
        run: |
          docker tag uatp:${{ github.sha }} registry.example.com/uatp:${{ github.sha }}
          docker push registry.example.com/uatp:${{ github.sha }}

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: |
          kubectl set image deployment/uatp-api \
            uatp-api=registry.example.com/uatp:${{ github.sha }} \
            -n uatp-staging

  deploy-production:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to production
        run: |
          kubectl set image deployment/uatp-api \
            uatp-api=registry.example.com/uatp:${{ github.sha }} \
            -n uatp-production
```

### Priority 4.2: Staging Environment

**Create Staging Configs**
```bash
# Copy production configs to staging
cp -r k8s/production k8s/staging

# Update namespace
sed -i 's/uatp-production/uatp-staging/g' k8s/staging/*.yaml

# Reduce resources for staging
# Edit k8s/staging/deployment.yaml:
# - replicas: 2 (instead of 3)
# - resources: 250m CPU, 256Mi RAM
```

**Acceptance Criteria:**
- [ ] CI/CD pipeline working
- [ ] Staging environment deployed
- [ ] Automated tests on PR
- [ ] Automated deployment on merge

---

##  Phase 5: Legal & Compliance (Ongoing)

### Priority 5.1: Insurance Regulatory

**Actions:**
1. Schedule consultation with insurance regulatory attorney
2. Research state-by-state insurance licensing requirements
3. Engage actuarial firm for risk model review
4. Apply for necessary licenses

**Timeline:** 3-6 months

### Priority 5.2: Privacy Compliance

**GDPR Compliance:**
- [ ] Add data export functionality
- [ ] Add data deletion (right to be forgotten)
- [ ] Create privacy policy
- [ ] Implement consent management

**HIPAA Compliance (for medical AI):**
- [ ] Complete HIPAA risk assessment
- [ ] Implement BAA (Business Associate Agreement)
- [ ] Add audit logging for PHI access
- [ ] Encrypt PHI at rest and in transit

---

##  Final Checklist

### Week 1 Deliverables
- [ ] Test suite fixed and passing (80%+ coverage)
- [ ] Database persistence implemented
- [ ] Stripe payment integration complete
- [ ] Comprehensive tests added

### Week 2 Deliverables
- [ ] Security audit passed
- [ ] Performance optimization complete
- [ ] Load tests passing (1000 RPS)
- [ ] All vulnerabilities fixed

### Week 3 Deliverables
- [ ] Business metrics tracked
- [ ] Error tracking (Sentry) active
- [ ] Distributed tracing working
- [ ] CI/CD pipeline deployed

### Week 4 Deliverables
- [ ] Staging environment live
- [ ] Production deployment tested
- [ ] Disaster recovery plan documented
- [ ] Legal consultation scheduled

---

##  Success Metrics

**Technical Excellence:**
- Test coverage: 80%+
- P95 latency: <500ms
- Error rate: <0.1%
- Uptime: 99.9%

**Business Readiness:**
- Payment processing: 100% functional
- Insurance policies: Can be created and managed
- Claims processing: Automated workflow working
- Revenue tracking: Real-time metrics

**Platinum Certification:**
- All critical blockers resolved
- All high-priority items complete
- Security audit passed
- Load tests passed
- Legal review in progress

---

**Plan Created:** 2025-01-06
**Target Completion:** 2025-02-03 (4 weeks)
**Owner:** UATP Engineering Team
