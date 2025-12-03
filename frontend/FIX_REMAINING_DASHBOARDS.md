# Fix Remaining Dashboards - Demo Mode Integration

## ✅ Completed
1. Economic Dashboard - Fixed ✅
2. Federation Dashboard - Fixed ✅
3. Main Dashboard - Fixed ✅
4. Live Capture Dashboard - Fixed ✅

## 🔧 Pattern to Apply to Remaining Dashboards

For each dashboard that has hardcoded mock data:

### 1. Import Demo Mode Hook
```typescript
import { useDemoMode } from '@/contexts/demo-mode-context';
import { Play } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
```

### 2. Replace Static Env Check
```typescript
// OLD:
const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === 'true';
const mockData = DEMO_MODE ? [...] : [];

// NEW:
const { isDemoMode } = useDemoMode();
const mockData = isDemoMode ? [...] : [];
```

### 3. Add Demo Mode Indicator to Header
```typescript
<CardHeader>
  <div className="flex items-center space-x-3">
    <CardTitle>Dashboard Name</CardTitle>
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
</CardHeader>
```

### 4. Add "No Data" Message for Live Mode
```typescript
{!isDemoMode && !dataExists && (
  <Card className="bg-blue-50 border-blue-200">
    <CardContent className="pt-6">
      <div className="flex items-center space-x-2">
        <AlertCircle className="h-5 w-5 text-blue-600" />
        <div>
          <h3 className="font-semibold text-blue-900">Live Data Mode</h3>
          <p className="text-sm text-blue-700">
            Data will appear here when available. Toggle Demo Mode ON to see sample data.
          </p>
        </div>
      </div>
    </CardContent>
  </Card>
)}
```

### 5. Wrap All Data-Dependent Content
```typescript
{dataExists && (
  <div>
    {/* All content that uses mock data */}
  </div>
)}
```

## 📋 Dashboards Still Needing Fixes

### High Priority (User Reported Issues)
- [ ] Organization Dashboard (`organization-dashboard.tsx`)
- [ ] Attribution Dashboard (`advanced-attribution.tsx`)
- [ ] AKC Dashboard (`akc-dashboard.tsx`)
- [ ] Mirror Mode Dashboard (`mirror-mode-dashboard.tsx`)
- [ ] Platforms Dashboard (`platform-dashboard.tsx`)
- [ ] Reasoning Dashboard (`reasoning-dashboard.tsx`)

### Medium Priority
- [ ] Governance Dashboard (`governance-dashboard.tsx`)
- [ ] Rights Evolution Dashboard (`rights-evolution-dashboard.tsx`)
- [ ] Chain Sealing Dashboard (`chain-sealing-dashboard.tsx`)
- [ ] Trust Dashboard (`trust-dashboard.tsx`)
- [ ] Payments Dashboard (`payment-dashboard.tsx`)
- [ ] Compliance Dashboard (`compliance-dashboard.tsx`)

### To Check
- [ ] Capsules Explorer (`capsule-explorer.tsx`)
- [ ] Universe Visualization (check if has mock data)

## 🔍 Quick Audit Command

To find dashboards with hardcoded data:
```bash
cd frontend/src/components
grep -r "const mock" --include="*.tsx" | grep -v "node_modules"
grep -r "DEMO_MODE.*env" --include="*.tsx" | grep -v "node_modules"
```

## ⚡ Quick Fix Steps

For each dashboard:
1. Search for `DEMO_MODE = process.env`
2. Replace with `useDemoMode()` hook
3. Add demo mode badge to header
4. Add "no data" message for live mode
5. Wrap all data-dependent sections in conditionals
6. Test both demo ON and demo OFF modes

## 🎯 Expected Behavior

**Demo Mode ON**: Show all mock data with orange badge
**Demo Mode OFF**: Show ONLY real API data, or "no data" message if none exists

## Notes

- The main issue was that dashboards were checking a static environment variable instead of the runtime demo mode toggle
- All dashboards must respect the `isDemoMode` state from the context
- No hardcoded data should show when demo mode is OFF
