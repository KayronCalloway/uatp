# Demo Mode Implementation Guide

## Overview

To prevent training/demo data from appearing in production, all mock data in frontend dashboards should be wrapped in demo mode conditionals.

**Demo Mode Status:**
- `NEXT_PUBLIC_DEMO_MODE=false` → Production (show only real API data)
- `NEXT_PUBLIC_DEMO_MODE=true` → Demo/Development (show mock data)

## Environment Configuration

### Files Created
- `frontend/.env.production` - Sets `NEXT_PUBLIC_DEMO_MODE=false`
- `frontend/.env.development` - Sets `NEXT_PUBLIC_DEMO_MODE=true`

### Setting Demo Mode

**For Production:**
```bash
cd frontend
# .env.production is used automatically for production builds
npm run build
npm start
```

**For Development/Demo:**
```bash
cd frontend
# .env.development is used automatically for dev mode
npm run dev
```

**Manual Override:**
```bash
# Temporarily enable demo mode in production
NEXT_PUBLIC_DEMO_MODE=true npm start

# Temporarily disable demo mode in development
NEXT_PUBLIC_DEMO_MODE=false npm run dev
```

## Implementation Pattern

### Step 1: Add Demo Mode Check

At the top of your dashboard component function, add:

```typescript
export function YourDashboard() {
  // Demo mode - mock data only shown when NEXT_PUBLIC_DEMO_MODE=true
  const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === 'true';

  // ... rest of component
}
```

### Step 2: Wrap Mock Data

#### For Simple Objects:

**Before:**
```typescript
const mockStats: Stats = {
  total_items: 100,
  active_items: 75,
  value: 12345.67
};
```

**After:**
```typescript
const mockStats: Stats = DEMO_MODE ? {
  total_items: 100,
  active_items: 75,
  value: 12345.67
} : {
  total_items: 0,
  active_items: 0,
  value: 0
};
```

#### For Arrays:

**Before:**
```typescript
const mockItems: Item[] = [
  { id: '1', name: 'Item 1', value: 100 },
  { id: '2', name: 'Item 2', value: 200 },
  // ... more items
];
```

**After:**
```typescript
const mockItems: Item[] = DEMO_MODE ? [
  { id: '1', name: 'Item 1', value: 100 },
  { id: '2', name: 'Item 2', value: 200 },
  // ... more items
] : [];
```

#### For Complex Nested Objects:

**Before:**
```typescript
const mockData = {
  stats: { total: 100, active: 75 },
  items: [
    { id: '1', name: 'Item 1' },
    { id: '2', name: 'Item 2' }
  ],
  config: { enabled: true, threshold: 0.75 }
};
```

**After:**
```typescript
const mockData = DEMO_MODE ? {
  stats: { total: 100, active: 75 },
  items: [
    { id: '1', name: 'Item 1' },
    { id: '2', name: 'Item 2' }
  ],
  config: { enabled: true, threshold: 0.75 }
} : {
  stats: { total: 0, active: 0 },
  items: [],
  config: { enabled: false, threshold: 0 }
};
```

### Step 3: Handle Display Logic

#### Empty State Messages:

```typescript
{mockItems.length === 0 && !DEMO_MODE && (
  <div className="text-center text-gray-500 py-8">
    <p>No data available yet.</p>
    <p className="text-sm">Start using the system to see data here.</p>
  </div>
)}

{mockItems.length === 0 && DEMO_MODE && (
  <div className="text-center text-gray-500 py-8">
    <p>Demo mode: No mock data loaded</p>
  </div>
)}
```

#### Demo Mode Banner (Optional):

```typescript
{DEMO_MODE && (
  <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
    <div className="flex">
      <div className="flex-shrink-0">
        <AlertCircle className="h-5 w-5 text-yellow-400" />
      </div>
      <div className="ml-3">
        <p className="text-sm text-yellow-700">
          <strong>Demo Mode Active:</strong> Showing mock data for demonstration purposes.
        </p>
      </div>
    </div>
  </div>
)}
```

## Dashboards Requiring Updates

Based on code analysis, these dashboards have mock data that needs wrapping:

### High Priority (Extensive Mock Data):
1. [OK] **compliance-dashboard.tsx** - Already cleared in previous cleanup
2. [OK] **payment-dashboard.tsx** - Already cleared in previous cleanup
3. ⏳ **platform-dashboard.tsx** - 19 mock references (platforms, API keys, usage)
4. ⏳ **akc-dashboard.tsx** - 13 mock references (sources, clusters, stats)
5. ⏳ **reasoning-dashboard.tsx** - 13 mock references (chains, steps, stats)
6. ⏳ **federation-dashboard.tsx** - 10 mock references (nodes, stats)
7. ⏳ **economic-dashboard.tsx** - 10 mock references (transactions, earnings)
8. ⏳ **mirror-mode-dashboard.tsx** - 9 mock references (configs, audits)

### Lower Priority (Minimal Mock Data):
9. ⏳ **organization-dashboard.tsx** - 1 reference but has full org mock data
10. ⏳ **trust-dashboard.tsx** - 1 reference, mostly uses real API

## Testing Checklist

After implementing demo mode for a dashboard:

- [ ] **Production Mode Test** (`DEMO_MODE=false`)
  - [ ] No mock data visible
  - [ ] Empty states display correctly
  - [ ] API data loads when available
  - [ ] No console errors

- [ ] **Demo Mode Test** (`DEMO_MODE=true`)
  - [ ] Mock data displays correctly
  - [ ] All stats/metrics show demo values
  - [ ] Charts/visualizations render
  - [ ] Demo banner appears (if implemented)

- [ ] **Toggle Test**
  - [ ] Can switch between modes without restart
  - [ ] State clears properly when switching
  - [ ] No stale data persists

## Complete Example

Here's a complete before/after example for reference:

### compliance-dashboard.tsx (Already Done)

**Before:**
```typescript
export function ComplianceDashboard() {
  const mockStats: ComplianceStats = {
    total_frameworks: 8,
    active_frameworks: 6,
    overall_compliance_score: 0.89,
    // ... more fields
  };

  const mockFrameworks: ComplianceFramework[] = [
    {
      id: 'gdpr-001',
      name: 'GDPR',
      // ... more fields
    },
    // ... more frameworks
  ];

  return (
    <div>
      {/* Display mock data */}
    </div>
  );
}
```

**After:**
```typescript
export function ComplianceDashboard() {
  const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === 'true';

  const mockStats: ComplianceStats = DEMO_MODE ? {
    total_frameworks: 8,
    active_frameworks: 6,
    overall_compliance_score: 0.89,
    // ... more fields
  } : {
    total_frameworks: 0,
    active_frameworks: 0,
    overall_compliance_score: 0,
    // ... zero values
  };

  const mockFrameworks: ComplianceFramework[] = DEMO_MODE ? [
    {
      id: 'gdpr-001',
      name: 'GDPR',
      // ... more fields
    },
    // ... more frameworks
  ] : [];

  return (
    <div>
      {DEMO_MODE && (
        <div className="bg-yellow-50 p-4 mb-4">
          Demo Mode: Showing sample data
        </div>
      )}

      {mockFrameworks.length === 0 && !DEMO_MODE && (
        <div className="text-center text-gray-500 py-8">
          No frameworks configured yet
        </div>
      )}

      {mockFrameworks.length > 0 && (
        <div>
          {/* Display frameworks */}
        </div>
      )}
    </div>
  );
}
```

## Next Steps

1. Review this guide
2. Start with platform-dashboard.tsx (highest mock count)
3. Follow the pattern for remaining dashboards
4. Test each dashboard in both modes
5. Document any edge cases or special handling needed

## Questions?

If you encounter mock data patterns not covered in this guide, document them here for future reference.
