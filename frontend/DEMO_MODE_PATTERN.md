# Demo Mode Integration Pattern

This document explains how to add demo mode support to any dashboard component in the UATP frontend.

## Overview

Demo mode allows users to toggle between real API data and mock presentation data via the toggle in the top-right header. All sidebar tabs should sync with this toggle automatically.

## Implementation Steps

### 1. Import Required Dependencies

```typescript
import { useDemoMode } from '@/contexts/demo-mode-context';
import { mockApiCall } from '@/lib/mock-data';
import { Play } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
```

### 2. Add Demo Mode Hook

At the beginning of your component:

```typescript
export function YourDashboard() {
  const { isDemoMode } = useDemoMode();
  // ... rest of your state
}
```

### 3. Create Mock Data Functions

Add mock data generators to `/frontend/src/lib/mock-data.ts`:

```typescript
export function getMockYourDashboardData() {
  return {
    // Your mock data structure matching the real API response
    items: [
      {
        id: 'demo-001',
        name: 'Demo Item',
        // ... more fields
      }
    ]
  };
}
```

### 4. Update Data Fetching Functions

Modify your fetch functions to check demo mode:

```typescript
const fetchData = async () => {
  try {
    if (isDemoMode) {
      // Use mock data
      const mockData = await mockApiCall(getMockYourDashboardData());
      setData(mockData);
      setError(null);
    } else {
      // Use real API
      const result = await api.getYourData();
      setData(result);
      setError(null);
    }
  } catch (err: any) {
    setError(err.message || 'Failed to fetch data');
  }
};
```

### 5. Add useEffect Dependency

Make sure to re-fetch when demo mode changes:

```typescript
useEffect(() => {
  fetchData();
  // ... optional polling
}, [isDemoMode]); // Important: Add isDemoMode as dependency
```

### 6. Add Visual Demo Indicator

Update your header/title section to show when demo mode is active:

```typescript
<div className="flex items-center space-x-2">
  <CardTitle>Your Dashboard</CardTitle>
  {isDemoMode && (
    <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-300">
      <Play className="h-3 w-3 mr-1" />
      Demo Data
    </Badge>
  )}
</div>
<p className="text-sm text-gray-600 mt-1">
  {isDemoMode
    ? 'Viewing simulated data for demonstration'
    : 'Real-time data from your UATP system'
  }
</p>
```

### 7. Handle Action Buttons in Demo Mode

For buttons that trigger API actions (create, update, delete), handle demo mode:

```typescript
const handleAction = async () => {
  try {
    if (isDemoMode) {
      // In demo mode, simulate the action
      setSuccess(true);
      // Maybe update local state optimistically
    } else {
      // Real API call
      await api.performAction(data);
      setSuccess(true);
    }
  } catch (err: any) {
    setError(err.message);
  }
};
```

## Example: Complete Implementation

See `/frontend/src/components/dashboard/live-capture-dashboard.tsx` for a complete working example.

## Testing Checklist

- [ ] Dashboard loads with demo data when demo mode is ON
- [ ] Dashboard loads with real data when demo mode is OFF
- [ ] Switching demo mode toggle updates the dashboard immediately
- [ ] Demo mode indicator badge appears when demo mode is ON
- [ ] Description text changes based on demo mode state
- [ ] Action buttons work appropriately in both modes
- [ ] No API errors when in demo mode
- [ ] Realistic simulated delays (200-800ms) for demo data

## Common Pitfalls

1. **Forgetting isDemoMode dependency**: Always add `isDemoMode` to useEffect dependencies
2. **Not handling actions**: Make sure buttons work in demo mode (don't just disable them)
3. **Missing visual indicator**: Users should always know when they're viewing demo data
4. **Unrealistic mock data**: Demo data should look real and professional
5. **Not simulating delays**: Use `mockApiCall()` wrapper for realistic loading states

## Dashboards to Update

Current status of demo mode integration across all dashboards:

- [x] Live Capture Dashboard
- [ ] Dashboard (main overview)
- [ ] Capsules Explorer
- [ ] Trust Dashboard
- [ ] Analytics Dashboard
- [ ] Universe Visualization
- [ ] Federation Dashboard
- [ ] Governance Dashboard
- [ ] Organization Dashboard
- [ ] Attribution Dashboard
- [ ] Rights Evolution Dashboard
- [ ] Chain Sealing Dashboard
- [ ] AKC Dashboard
- [ ] Mirror Mode Dashboard
- [ ] Payments Dashboard
- [ ] Compliance Dashboard
- [ ] Platforms Dashboard
- [ ] Reasoning Dashboard
- [ ] System Graph View
- [ ] Debug Tools

## Next Steps

1. Create mock data functions for each dashboard type
2. Apply this pattern to each dashboard systematically
3. Test demo mode switching across all tabs
4. Ensure consistent UX across all views
