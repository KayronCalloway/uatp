# UATP Dashboard Tab Testing Plan

**Created:** 2025-11-18
**Purpose:** Comprehensive testing checklist for all UATP dashboard tabs
**Status:** In Progress

## System Status

**Frontend:** http://localhost:3004
**Backend API:** http://localhost:8000
**Visualizer:** http://localhost:8501
**Unified Dashboard:** http://localhost:8502
**Governance Dashboard:** http://localhost:8503

---

## Testing Methodology

For each tab, we will verify:

1. **Page Load** - Tab renders without errors
2. **API Connectivity** - Backend endpoints return data
3. **Data Display** - Information displays correctly
4. **Interactive Features** - Buttons, filters, and actions work
5. **Error Handling** - Graceful handling of missing/bad data
6. **Console Errors** - No JavaScript errors in browser console
7. **Loading States** - Appropriate loading indicators
8. **Responsive Design** - Layout works on different screen sizes

---

## Phase 1: Core Dashboards

### 1. Dashboard (System Overview)
**Component:** `SystemOverviewDashboard`
**Priority:** HIGH

**Tests:**
- [ ] Page loads without errors
- [ ] System health metrics display correctly
- [ ] Total capsule count shows correct number
- [ ] Recent activity statistics load
- [ ] Capsule type breakdown chart renders
- [ ] Quick action buttons are functional
- [ ] Navigation to other sections works
- [ ] Real-time updates work (if applicable)

**API Endpoints:**
- `GET /health` - System health check
- `GET /capsules/stats` - Capsule statistics
- `GET /trust/metrics` - Trust score data

**Expected Issues:**
- Missing `/onboarding/api/health` endpoint (404 observed)
- Missing `/capsules/stats` endpoint (404 observed)

---

### 2. Capsules (Capsule Explorer)
**Component:** `CapsuleExplorer`
**Priority:** HIGH

**Tests:**
- [ ] Capsule list loads and displays
- [ ] Pagination controls work
- [ ] Filtering by type works
- [ ] Search functionality works
- [ ] Clicking capsule opens detail view
- [ ] Capsule detail shows all information
- [ ] Verification status displays correctly
- [ ] Content/payload renders properly
- [ ] Metadata displays in readable format
- [ ] Raw data toggle works (if available)

**API Endpoints:**
- `GET /capsules` - List capsules with pagination
- `GET /capsules/{id}` - Get specific capsule
- `GET /capsules/{id}/verify` - Verify capsule signature

**Expected Issues:**
- None identified yet (basic endpoints exist)

---

### 3. Trust (Trust Dashboard)
**Component:** `TrustDashboard`
**Priority:** HIGH

**Tests:**
- [ ] Trust metrics load
- [ ] Agent trust scores display
- [ ] Trust score visualization renders
- [ ] Historical trust data shows
- [ ] Trust threshold settings work
- [ ] Trust decay calculations display
- [ ] Agent reputation list populates

**API Endpoints:**
- `GET /trust/metrics` - Get trust scores
- `GET /trust/agents` - List agents with trust
- `GET /trust/history` - Historical trust data

**Expected Issues:**
- Unknown - need to verify endpoints exist

---

### 4. Analytics (Economic Dashboard)
**Component:** `EconomicDashboard`
**Priority:** MEDIUM

**Tests:**
- [ ] Economic attribution data loads
- [ ] Value flow visualization renders
- [ ] Payment distribution shows correctly
- [ ] Revenue metrics display
- [ ] Attribution breakdown by contributor
- [ ] Economic impact charts render
- [ ] Export functionality works (if available)

**API Endpoints:**
- `GET /economics/attribution` - Attribution data
- `GET /economics/payments` - Payment distribution
- `GET /economics/metrics` - Economic metrics

**Expected Issues:**
- Endpoints may not exist yet

---

## Phase 2: Visualization Tabs

### 5. Universe (Universe Visualization)
**Component:** `UniverseVisualization`
**Priority:** MEDIUM

**Tests:**
- [ ] Network graph renders
- [ ] Nodes represent capsules correctly
- [ ] Edges show relationships
- [ ] Zoom and pan controls work
- [ ] Node clicking shows details
- [ ] Legend explains visualization
- [ ] Filter by capsule type works
- [ ] Layout algorithm renders properly

**API Endpoints:**
- `GET /capsules/graph` - Graph data structure
- `GET /capsules/relationships` - Capsule relationships

**Expected Issues:**
- May need to implement graph endpoints

---

### 6. System (System Graph View)
**Component:** `SystemGraphView`
**Priority:** MEDIUM

**Tests:**
- [ ] System architecture diagram renders
- [ ] Component relationships display
- [ ] Service health indicators work
- [ ] Interactive node exploration
- [ ] Performance metrics overlay

**API Endpoints:**
- `GET /system/topology` - System architecture
- `GET /system/health` - Component health

**Expected Issues:**
- Endpoints likely not implemented

---

## Phase 3: Management Dashboards

### 7. Federation (Federation Dashboard)
**Component:** `FederationDashboard`
**Priority:** LOW

**Tests:**
- [ ] Federation members list loads
- [ ] Cross-organization sharing status
- [ ] Federation policies display
- [ ] Member trust scores show
- [ ] Inter-org capsule discovery works

**API Endpoints:**
- `GET /federation/members` - Federation members
- `GET /federation/shared` - Shared capsules
- `GET /federation/policies` - Federation policies

**Expected Issues:**
- Federation feature may not be implemented

---

### 8. Governance (Governance Dashboard)
**Component:** `GovernanceDashboard`
**Priority:** MEDIUM

**Tests:**
- [ ] Active proposals list loads
- [ ] Voting interface works
- [ ] Vote tallies display correctly
- [ ] Proposal creation form works
- [ ] Governance rules display
- [ ] Vote history shows

**API Endpoints:**
- `GET /governance/proposals` - Active proposals
- `POST /governance/vote` - Cast vote
- `GET /governance/history` - Vote history

**Expected Issues:**
- May redirect to Streamlit dashboard on port 8503

---

### 9. Organization (Organization Dashboard)
**Component:** `OrganizationDashboard`
**Priority:** MEDIUM

**Tests:**
- [ ] Organization settings load
- [ ] Team member list displays
- [ ] Usage statistics show
- [ ] Billing information displays (if applicable)
- [ ] API key management works
- [ ] Organization policies display

**API Endpoints:**
- `GET /organization/info` - Org information
- `GET /organization/members` - Team members
- `GET /organization/usage` - Usage stats

**Expected Issues:**
- Endpoints may not exist

---

## Phase 4: Advanced Features

### 10. Attribution (Advanced Attribution)
**Component:** `AdvancedAttribution`
**Priority:** HIGH

**Tests:**
- [ ] Attribution graph loads
- [ ] Source tracking displays
- [ ] Confidence scores show
- [ ] Gaming detection indicators work
- [ ] Semantic similarity visualization
- [ ] Attribution breakdown by source
- [ ] Historical attribution data

**API Endpoints:**
- `GET /attribution/track` - Attribution tracking
- `GET /attribution/sources` - Attribution sources
- `GET /attribution/gaming` - Gaming detection

**Expected Issues:**
- Complex feature - may have partial implementation

---

### 11. Rights Evolution (Rights & Evolution Dashboard)
**Component:** `RightsEvolutionDashboard`
**Priority:** MEDIUM

**Tests:**
- [ ] AI rights status displays
- [ ] Consent tracking shows
- [ ] Rights negotiation interface works
- [ ] Evolution timeline renders
- [ ] Self-advocacy logs display

**API Endpoints:**
- `GET /rights/status` - Rights status
- `GET /rights/consent` - Consent records
- `GET /rights/evolution` - Rights evolution history

**Expected Issues:**
- Advanced feature - likely partial implementation

---

### 12. Live Capture (Live Capture Dashboard)
**Component:** `LiveCaptureDashboard`
**Priority:** HIGH

**Tests:**
- [ ] Active conversations list loads
- [ ] Real-time conversation monitoring works
- [ ] Significance scoring displays
- [ ] Auto-encapsulation triggers correctly
- [ ] Manual capture controls work
- [ ] Conversation detail view works

**API Endpoints:**
- `GET /live/capture/conversations` - Active conversations
- `GET /live/capture/conversation/{id}` - Conversation status
- `POST /live/capture/message` - Capture message
- `GET /live/monitor/status` - Monitor status

**Expected Issues:**
- Endpoints exist but may need testing

---

### 13. Chain Sealing (Chain Sealing Dashboard)
**Component:** `ChainSealingDashboard`
**Priority:** MEDIUM

**Tests:**
- [ ] Chain sealing status displays
- [ ] Seal creation interface works
- [ ] Verification checks run correctly
- [ ] Chain integrity display works
- [ ] Merkle root visualization

**API Endpoints:**
- `GET /chain/seals` - Chain seals
- `POST /chain/seal` - Create seal
- `GET /chain/verify` - Verify chain

**Expected Issues:**
- Chain sealing implementation unclear

---

### 14. AKC (Autonomous Knowledge Collective)
**Component:** `AKCDashboard`
**Priority:** LOW

**Tests:**
- [ ] Knowledge graph loads
- [ ] Discovery mechanisms work
- [ ] Collective intelligence metrics
- [ ] Knowledge contributions display

**API Endpoints:**
- `GET /akc/knowledge` - Knowledge graph
- `GET /akc/discoveries` - Knowledge discoveries

**Expected Issues:**
- Advanced feature - likely not implemented

---

## Phase 5: Specialized Dashboards

### 15. Mirror Mode (Mirror Mode Dashboard)
**Component:** `MirrorModeDashboard`
**Priority:** MEDIUM

**Tests:**
- [ ] Mirror mode toggle works
- [ ] Test API interface displays
- [ ] Dry-run results show correctly
- [ ] No side effects occur in mirror mode
- [ ] Test history displays

**API Endpoints:**
- `GET /mirror/status` - Mirror mode status
- `POST /mirror/enable` - Enable mirror mode
- `POST /mirror/test` - Test API call

**Expected Issues:**
- Mirror mode implementation unclear

---

### 16. Reasoning (Reasoning Dashboard)
**Component:** `ReasoningDashboard`
**Priority:** HIGH

**Tests:**
- [ ] Reasoning traces load
- [ ] Step-by-step reasoning displays
- [ ] Confidence scores show
- [ ] Attribution sources link correctly
- [ ] Reasoning graph visualization
- [ ] Reasoning quality metrics

**API Endpoints:**
- `GET /reasoning/traces` - Reasoning traces
- `GET /reasoning/{id}` - Specific reasoning chain
- `GET /reasoning/analysis` - Reasoning analysis

**Expected Issues:**
- May need reasoning-specific endpoints

---

### 17. Platforms (Platform Dashboard)
**Component:** `PlatformDashboard`
**Priority:** MEDIUM

**Tests:**
- [ ] Connected platforms list loads
- [ ] Platform status indicators work
- [ ] API key configuration works
- [ ] Usage by platform displays
- [ ] Platform-specific metrics show

**API Endpoints:**
- `GET /platforms/list` - Connected platforms
- `GET /platforms/{id}/status` - Platform status
- `GET /platforms/usage` - Platform usage

**Expected Issues:**
- Missing `/onboarding/api/platforms` endpoint (404 observed)

---

## Phase 6: Operations Tabs

### 18. Payments (Payment Dashboard)
**Component:** `PaymentDashboard`
**Priority:** LOW

**Tests:**
- [ ] Payment history loads
- [ ] Transaction details display
- [ ] Payment methods configured
- [ ] Revenue distribution shows
- [ ] Payment status tracking

**API Endpoints:**
- `GET /payments/history` - Payment history
- `GET /payments/methods` - Payment methods
- `POST /payments/process` - Process payment

**Expected Issues:**
- Payment integration warnings observed (Stripe/PayPal not configured)

---

### 19. Compliance (Compliance Dashboard)
**Component:** `ComplianceDashboard`
**Priority:** LOW

**Tests:**
- [ ] Compliance status displays
- [ ] Regulatory framework checks
- [ ] Audit logs display
- [ ] Risk assessment shows
- [ ] Compliance reports generate

**API Endpoints:**
- `GET /compliance/status` - Compliance status
- `GET /compliance/audit-log` - Audit logs
- `GET /compliance/frameworks` - Regulatory frameworks

**Expected Issues:**
- Compliance features likely not implemented

---

## Phase 7: Diagnostics

### 20. Debug (Debug & Diagnostics)
**Component:** `DebugView` with sub-tabs:
- API Test
- Connection Test
- Hallucination Detection

**Priority:** HIGH

**Tests:**

**API Test Tab:**
- [ ] Endpoint testing interface works
- [ ] API response displays correctly
- [ ] Error messages show clearly
- [ ] Request/response logging works

**Connection Test Tab:**
- [ ] Database connection check works
- [ ] Service availability displays
- [ ] Latency measurements show
- [ ] Connection health indicators

**Hallucination Detection Tab:**
- [ ] Hallucination check interface works
- [ ] Detection results display
- [ ] Confidence scores show
- [ ] False positive tracking

**API Endpoints:**
- `GET /health` - Basic health check
- `GET /debug/connectivity` - Connection diagnostics
- `POST /debug/hallucination` - Hallucination detection

**Expected Issues:**
- Debug endpoints may need implementation

---

### 21. Settings
**Component:** `ComingSoonCard`
**Priority:** LOW

**Tests:**
- [ ] "Coming Soon" message displays
- [ ] No errors on navigation

**Expected Issues:**
- Not implemented - placeholder only

---

## Critical Issues Found

Based on initial diagnostics:

1. **Missing Endpoints (404s):**
   - `/onboarding/api/health`
   - `/onboarding/api/platforms`
   - `/onboarding/api/status/{user_id}`
   - `/capsules/stats`

2. **Payment Integration:**
   - Stripe API key not configured
   - PayPal credentials not configured
   - Payment routes will not work

3. **Authentication:**
   - JWT using default secret (insecure in production)
   - CSRF using generated key (needs fixed key in production)

---

## Testing Execution Plan

1. **Phase 1 (Day 1):** Test Core Dashboards - highest priority
2. **Phase 2 (Day 1):** Test Visualization Tabs
3. **Phase 3 (Day 2):** Test Management Dashboards
4. **Phase 4 (Day 2-3):** Test Advanced Features
5. **Phase 5 (Day 3):** Test Specialized Dashboards
6. **Phase 6 (Day 4):** Test Operations Tabs
7. **Phase 7 (Day 4):** Test Debug and create fix plan

---

## Success Criteria

A tab is considered "passing" if:
- No critical errors prevent functionality
- Core features work as expected
- API endpoints return valid data
- User can complete primary workflows
- Error messages are clear and helpful

A tab is considered "failing" if:
- Page doesn't load or shows critical errors
- API endpoints return 404/500 errors
- Core functionality is broken
- No data displays when it should

---

## Next Steps

1. Start testing Phase 1 tabs systematically
2. Document all issues found in detail
3. Create prioritized fix list
4. Implement fixes for critical issues
5. Retest after fixes
6. Update this document with results
