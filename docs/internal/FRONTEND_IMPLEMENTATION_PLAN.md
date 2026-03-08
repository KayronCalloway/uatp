# Frontend Implementation Plan - First Principles

**Date**: 2025-12-05
**Philosophy**: Make intelligence visible, understandable, and actionable

---

## First Principles Analysis

### Core User Needs
1. **See** - Visualize what the system learned
2. **Understand** - Comprehend why it matters
3. **Act** - Use insights to make decisions
4. **Trust** - Verify the system is working correctly
5. **Improve** - Know what to do next

### Design Principles

**1. Progressive Disclosure**
- Show summary first, details on demand
- Simple view for everyone, advanced view for power users
- Don't overwhelm with data

**2. Visual > Textual**
- Patterns are easier to see than read
- Charts beat tables for trends
- Color conveys meaning faster than text

**3. Actionability**
- Every insight should suggest an action
- Make it easy to follow recommendations
- Close the feedback loop

**4. Real-Time Feedback**
- Immediate response to user actions
- Loading states for async operations
- Optimistic UI updates

**5. Context-Aware Display**
- Show relevant information for current task
- Hide irrelevant complexity
- Adapt to user's expertise level

---

## Architecture

### Component Hierarchy

```
src/
├── components/
│   ├── analytics/          # Reusable analytics components
│   │   ├── charts/         # Chart primitives
│   │   ├── metrics/        # Metric displays
│   │   └── visualizations/ # Complex visualizations
│   ├── capsules/           # Capsule-specific components
│   │   ├── quality/        # Quality assessment UI
│   │   ├── uncertainty/    # Uncertainty displays
│   │   └── recommendations/# Strategy recommendations
│   └── ui/                 # Base UI components (existing)
├── app/
│   └── analytics/          # Analytics pages
│       ├── overview/       # Dashboard home
│       ├── patterns/       # Pattern explorer
│       ├── calibration/    # Calibration dashboard
│       ├── quality/        # Quality trends
│       └── causal/         # Causal graph viewer
├── hooks/
│   ├── useOutcomes.ts      # Outcome data hooks
│   ├── usePatterns.ts      # Pattern data hooks
│   ├── useCalibration.ts   # Calibration data hooks
│   └── useAnalytics.ts     # General analytics hooks
└── lib/
    ├── analytics-api.ts    # Analytics API client
    └── chart-utils.ts      # Chart helpers
```

---

## Implementation Phases

### Phase 1: Foundation (6-8 hours)
**Goal**: Make Level 2 & 3 intelligence VISIBLE

**Components**:
1. Quality Badge & Details (2h)
2. Pattern Browser (3h)
3. Outcome Stats Dashboard (2h)
4. Shared Analytics Layout (1h)

**Output**: Users can SEE quality grades and discovered patterns

### Phase 2: Core Analytics (8-10 hours)
**Goal**: Enable EXPLORATION of learned insights

**Components**:
1. Calibration Dashboard (3h)
2. Uncertainty Components (2h)
3. Strategy Recommendations (2h)
4. Quality Trend Analyzer (3h)

**Output**: Users can EXPLORE calibration and strategies

### Phase 3: Advanced Intelligence (6-8 hours)
**Goal**: Enable INTERACTION with causal models

**Components**:
1. Causal Graph Viewer (4h)
2. Root Cause Analyzer (2h)
3. Intervention Simulator (2h)

**Output**: Users can QUERY causal relationships

### Phase 4: Integration & Polish (4-6 hours)
**Goal**: Seamless experience across all views

**Tasks**:
1. Cross-linking between views
2. Consistent styling and interactions
3. Performance optimization
4. Mobile responsiveness
5. Accessibility improvements

**Output**: Cohesive, polished analytics experience

---

## Component Specifications

### 1. Quality Badge (Priority: CRITICAL)

**Purpose**: Show quality grade at a glance

**Display**:
```
┌─────────┐
│    A    │  ← Letter grade (A-F)
│ Quality │  ← Label
└─────────┘
```

**Colors**:
- A: Green (#10b981)
- B: Blue (#3b82f6)
- C: Yellow (#f59e0b)
- D: Orange (#f97316)
- F: Red (#ef4444)

**Behavior**:
- Click to open Quality Details Modal
- Tooltip shows overall score (0.95)
- Pulse animation if grade is low (< C)

**Props**:
```typescript
interface QualityBadgeProps {
  capsuleId: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  onClick?: () => void;
}
```

### 2. Quality Details Modal (Priority: CRITICAL)

**Purpose**: Show detailed quality breakdown

**Sections**:
1. **Header**: Letter grade + overall score
2. **Radar Chart**: 6 dimensions visually
3. **Dimension Scores**: List with progress bars
4. **Issues**: Red warning list
5. **Suggestions**: Blue action list (prioritized)

**Dimensions** (with icons):
- Completeness ✓
- Coherence 🔗
- Evidence 📊
- Logic ⚖️
- Bias 👁️
- Clarity 💡

### 3. Pattern Browser (Priority: CRITICAL)

**Purpose**: Explore discovered reasoning patterns

**Layout**:
```
┌─────────────────────────────────────────────┐
│ Filters: [Type ▾] [Domain ▾] [Min Success ▾]│
├─────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────┐ │
│ │ Analysis → Measurement → Decision       │ │
│ │ Success: 85% | Uses: 12 | Domain: API  │ │
│ │ [View Examples]                         │ │
│ └─────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────┐ │
│ │ Investigation → Validation              │ │
│ │ Success: 92% | Uses: 8 | Domain: UI    │ │
│ │ [View Examples]                         │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

**Features**:
- Filter by pattern type (sequence, decision, failure)
- Filter by domain
- Sort by success rate
- Click to see example capsules
- Success rate bar chart
- Usage count badge

### 4. Calibration Dashboard (Priority: HIGH)

**Purpose**: Show confidence calibration quality

**Charts**:
1. **Reliability Diagram**: Scatter plot
   - X-axis: Predicted confidence
   - Y-axis: Actual success rate
   - Perfect calibration line (diagonal)
   - Points colored by domain

2. **Calibration Error Chart**: Bar chart
   - X-axis: Confidence buckets (0.1, 0.2, ..., 1.0)
   - Y-axis: Calibration error
   - Red bars for over-confident, green for under-confident

3. **ECE Trend**: Line chart over time
   - Show improvement trajectory
   - Target line at 0.1

4. **Domain Comparison**: Grouped bar chart
   - Compare calibration across domains

### 5. Uncertainty Display (Priority: HIGH)

**Purpose**: Show confidence intervals and risk

**In Capsule Detail** (enhance existing display):
```
Before:
Confidence: 0.85

After:
Confidence: 0.85 [0.78 - 0.92]  ← 95% CI
├─ Epistemic: 0.05 (reducible)
└─ Aleatoric: 0.02 (irreducible)
Risk: ⚠️ Medium
```

**Components**:
- Confidence interval error bars
- Uncertainty breakdown (pie chart or bars)
- Risk badge (Low/Medium/High with color)
- Worst/best case scenario display

### 6. Strategy Recommendations (Priority: MEDIUM)

**Purpose**: Suggest proven strategies

**Display Location**: Capsule detail page, below metadata

**Layout**:
```
┌─────────────────────────────────────────────┐
│ 💡 Recommended Strategies                   │
├─────────────────────────────────────────────┤
│ ✓ Analysis → Measurement → Decision        │
│   Success rate: 85% | Match: 92%           │
│   "Used successfully in 12 similar cases"  │
│   [View Examples] [Apply Strategy]         │
└─────────────────────────────────────────────┘
```

### 7. Causal Graph Viewer (Priority: MEDIUM)

**Purpose**: Visualize causal relationships

**Technology**: vis-network (already installed)

**Features**:
- Interactive DAG visualization
- Node types: action (square), condition (diamond), outcome (circle)
- Edge thickness = causal strength
- Click node to see details
- Highlight paths between nodes
- Pan, zoom, drag nodes

**Controls**:
- Select start/end nodes
- Show all paths between them
- Highlight root causes
- Highlight terminal effects

### 8. Outcome Stats Dashboard (Priority: MEDIUM)

**Purpose**: Aggregate outcome metrics

**Cards**:
1. **Total Outcomes**: Big number with trend
2. **Average Quality**: Gauge chart (0-1)
3. **By Validation Method**: Pie chart
4. **Recent Outcomes**: Timeline

---

## Data Flow

### API Integration Pattern

```typescript
// hooks/usePatterns.ts
export function usePatterns(filters?: PatternFilters) {
  return useQuery({
    queryKey: ['patterns', filters],
    queryFn: () => api.getPatterns(filters)
  });
}

// Component usage
function PatternBrowser() {
  const { data, isLoading } = usePatterns({
    pattern_type: 'sequence',
    min_success_rate: 0.7
  });

  if (isLoading) return <Spinner />;

  return <PatternList patterns={data.patterns} />;
}
```

### Type Definitions

```typescript
// types/analytics.ts
interface QualityAssessment {
  overall_quality: number;
  dimension_scores: Record<string, DimensionScore>;
  quality_grade: 'A' | 'B' | 'C' | 'D' | 'F';
  strengths: string[];
  weaknesses: string[];
  improvement_priority: [string, number][];
}

interface Pattern {
  pattern_id: string;
  pattern_name: string;
  pattern_type: 'sequence' | 'decision_tree' | 'failure_mode';
  success_rate: number;
  usage_count: number;
  applicable_domains: string[];
  example_capsule_ids: string[];
}

interface CalibrationData {
  domain: string;
  confidence_bucket: number;
  predicted_count: number;
  actual_success_count: number;
  calibration_error: number;
  success_rate: number;
}
```

---

## Visual Design System

### Color Palette (extends existing)

**Quality Grades**:
- A: `text-green-600 bg-green-50 border-green-200`
- B: `text-blue-600 bg-blue-50 border-blue-200`
- C: `text-yellow-600 bg-yellow-50 border-yellow-200`
- D: `text-orange-600 bg-orange-50 border-orange-200`
- F: `text-red-600 bg-red-50 border-red-200`

**Uncertainty**:
- Epistemic: `text-purple-600`
- Aleatoric: `text-teal-600`
- Risk Low: `text-green-600`
- Risk Medium: `text-yellow-600`
- Risk High: `text-red-600`

**Patterns**:
- Sequence: `text-blue-600`
- Decision: `text-indigo-600`
- Failure: `text-red-600`

### Typography

**Analytics Headers**: `text-2xl font-bold text-gray-900`
**Metric Labels**: `text-sm font-medium text-gray-500`
**Metric Values**: `text-3xl font-bold text-gray-900`
**Descriptions**: `text-sm text-gray-600`

### Spacing

- Section spacing: `space-y-6`
- Card padding: `p-6`
- Grid gaps: `gap-4`

---

## Implementation Order (Prioritized)

### Week 1: Foundation (Days 1-2, 6-8 hours)

**Day 1 Morning** (3 hours):
1. Quality Badge component
2. Quality Details Modal
3. API client methods for quality

**Day 1 Afternoon** (2 hours):
4. Integrate quality badge into capsule cards
5. Integrate quality modal into capsule detail

**Day 2** (3 hours):
6. Pattern Browser page
7. Pattern List component
8. Pattern filters
9. API integration

### Week 1: Core Analytics (Days 3-4, 8-10 hours)

**Day 3** (4 hours):
1. Calibration Dashboard page
2. Reliability Diagram chart
3. Calibration Error chart
4. API integration

**Day 4 Morning** (3 hours):
5. Uncertainty Display components
6. Integrate into capsule detail
7. Risk badges

**Day 4 Afternoon** (3 hours):
8. Strategy Recommendations component
9. Integrate into capsule detail
10. API integration

### Week 2: Advanced Features (Days 1-2, 6-8 hours)

**Day 1** (4 hours):
1. Causal Graph Viewer page
2. vis-network integration
3. Node/edge rendering
4. Basic interactivity

**Day 2** (4 hours):
5. Root Cause Analyzer
6. Path highlighting
7. Intervention simulator (basic)

### Week 2: Polish (Days 3-4, 4-6 hours)

**Day 3** (3 hours):
1. Cross-linking between analytics pages
2. Consistent styling
3. Loading states

**Day 4** (3 hours):
4. Performance optimization
5. Mobile responsiveness
6. Accessibility (ARIA labels, keyboard nav)

---

## Success Metrics

### Functional
- ✅ All backend intelligence visible in UI
- ✅ Quality grades shown on all capsules
- ✅ Patterns browsable and filterable
- ✅ Calibration data visualized
- ✅ Uncertainty displayed with intervals
- ✅ Causal graphs interactive

### Performance
- Page load < 1s
- Chart render < 500ms
- Smooth 60fps interactions

### Usability
- Quality grade understandable without docs
- Patterns discoverable within 30s
- Calibration meaningful to users
- Graphs navigable without training

---

## Technical Stack

**Already Have**:
- React 19.1.0 ✅
- Next.js 15.4.1 ✅
- TanStack Query 5.83.0 ✅
- Tailwind CSS ✅
- lucide-react (icons) ✅
- vis-network (graphs) ✅

**Need to Add**:
- Recharts (for analytics charts)
- OR use existing vis-network more extensively

**Decision**: Use **Recharts** for standard charts (line, bar, scatter) because:
- Declarative React components
- Responsive by default
- Good TypeScript support
- vis-network for graphs only

---

## File Structure

```
frontend/src/
├── app/
│   └── analytics/
│       ├── layout.tsx              # Shared analytics layout
│       ├── page.tsx                # Overview dashboard
│       ├── patterns/
│       │   └── page.tsx
│       ├── calibration/
│       │   └── page.tsx
│       ├── quality/
│       │   └── page.tsx
│       └── causal/
│           └── page.tsx
├── components/
│   ├── analytics/
│   │   ├── charts/
│   │   │   ├── reliability-diagram.tsx
│   │   │   ├── calibration-error-chart.tsx
│   │   │   ├── quality-radar.tsx
│   │   │   └── success-rate-bar.tsx
│   │   ├── pattern-card.tsx
│   │   ├── pattern-list.tsx
│   │   ├── pattern-filters.tsx
│   │   ├── causal-graph.tsx
│   │   └── metric-card.tsx
│   └── capsules/
│       ├── quality-badge.tsx
│       ├── quality-details-modal.tsx
│       ├── uncertainty-display.tsx
│       └── strategy-recommendations.tsx
├── hooks/
│   ├── usePatterns.ts
│   ├── useCalibration.ts
│   ├── useQuality.ts
│   └── useOutcomeStats.ts
├── lib/
│   └── analytics-api.ts
└── types/
    └── analytics.ts
```

---

## Next Steps

1. Install Recharts: `npm install recharts`
2. Create analytics API client
3. Build Quality Badge (highest priority)
4. Build Pattern Browser (high visibility)
5. Continue with prioritized list

---

*Created: 2025-12-05*
*Ready for systematic execution*
