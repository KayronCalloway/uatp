'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import {
  Search,
  Filter,
  X,
  ChevronDown,
  ChevronUp,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  GitBranch,
  Star,
  Zap,
  BookOpen,
  BarChart3,
  Target,
  Layers
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { CapsuleSearchParams, SearchPreset, AnyCapsule } from '@/types/api';

// Default search presets for common queries
const DEFAULT_PRESETS: SearchPreset[] = [
  {
    id: 'high-quality',
    name: 'High Quality',
    description: 'Grade A & B capsules',
    icon: 'star',
    params: { quality_grade: ['A', 'B'] as any },
    category: 'quality'
  },
  {
    id: 'verified-trusted',
    name: 'Court-Ready',
    description: 'Signed & RFC 3161 timestamped',
    icon: 'shield',
    params: { signature_valid: true, timestamp_trusted: true },
    category: 'verification'
  },
  {
    id: 'needs-review',
    name: 'Needs Review',
    description: 'Low quality or missing outcomes',
    icon: 'alert',
    params: { quality_grade: ['D', 'F'] as any, has_outcome: false },
    category: 'quality'
  },
  {
    id: 'recent-activity',
    name: 'Today',
    description: 'Capsules from today',
    icon: 'clock',
    params: { date_preset: 'today' },
    category: 'time'
  },
  {
    id: 'this-week',
    name: 'This Week',
    description: 'Last 7 days',
    icon: 'clock',
    params: { date_preset: 'week' },
    category: 'time'
  },
  {
    id: 'high-risk',
    name: 'High Risk',
    description: 'Probability correct < 60%',
    icon: 'alert-triangle',
    params: { probability_correct_max: 0.6 },
    category: 'risk'
  },
  {
    id: 'with-reasoning',
    name: 'With Reasoning',
    description: 'Has reasoning chain',
    icon: 'git-branch',
    params: { has_reasoning_chain: true },
    category: 'content'
  },
  {
    id: 'successful',
    name: 'Successful',
    description: 'Positive outcomes',
    icon: 'check',
    params: { outcome_status: 'success' },
    category: 'risk'
  }
];

interface CapsuleSearchProps {
  onSearch: (params: CapsuleSearchParams) => void;
  capsules?: AnyCapsule[];  // For computing facets
  initialParams?: CapsuleSearchParams;
  showPresets?: boolean;
  compact?: boolean;
}

// Helper to get icon component
const getPresetIcon = (iconName?: string) => {
  switch (iconName) {
    case 'star': return Star;
    case 'shield': return Shield;
    case 'alert': case 'alert-triangle': return AlertTriangle;
    case 'clock': return Clock;
    case 'check': return CheckCircle;
    case 'git-branch': return GitBranch;
    default: return Zap;
  }
};

// Quality grade colors
const gradeColors: Record<string, string> = {
  'A': 'bg-green-100 text-green-800 border-green-300',
  'B': 'bg-blue-100 text-blue-800 border-blue-300',
  'C': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'D': 'bg-orange-100 text-orange-800 border-orange-300',
  'F': 'bg-red-100 text-red-800 border-red-300',
};

export function CapsuleSearch({
  onSearch,
  capsules = [],
  initialParams = {},
  showPresets = true,
  compact = false
}: CapsuleSearchProps) {
  const [searchParams, setSearchParams] = useState<CapsuleSearchParams>(initialParams);
  const [query, setQuery] = useState(initialParams.query || '');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activePresets, setActivePresets] = useState<string[]>([]);

  // Compute facets from capsules for filter counts
  const facets = useMemo(() => {
    const types: Record<string, number> = {};
    const qualityGrades: Record<string, number> = {};
    const agents: Record<string, number> = {};
    const outcomes: Record<string, number> = {};

    let verifiedCount = 0;
    let trustedTimestampCount = 0;
    let withReasoningCount = 0;
    let withOutcomeCount = 0;

    capsules.forEach(capsule => {
      // Types
      const type = capsule.type || capsule.capsule_type || 'unknown';
      types[type] = (types[type] || 0) + 1;

      // Quality grades
      const quality = capsule.payload?.quality_assessment?.quality_grade;
      if (quality) {
        qualityGrades[quality] = (qualityGrades[quality] || 0) + 1;
      }

      // Agents
      const agent = capsule.verification?.signer || capsule.agent_id || 'unknown';
      agents[agent] = (agents[agent] || 0) + 1;

      // Outcomes
      const outcome = capsule.payload?.outcome?.result || 'untracked';
      outcomes[outcome] = (outcomes[outcome] || 0) + 1;

      // Verification
      if (capsule.verification?.signature) verifiedCount++;
      if (capsule.verification?.timestamp?.trusted) trustedTimestampCount++;

      // Content
      if (capsule.payload?.reasoning_chain?.length) withReasoningCount++;
      if (capsule.payload?.outcome) withOutcomeCount++;
    });

    return {
      types,
      qualityGrades,
      agents,
      outcomes,
      verifiedCount,
      trustedTimestampCount,
      withReasoningCount,
      withOutcomeCount,
      total: capsules.length
    };
  }, [capsules]);

  // Update search when params change
  useEffect(() => {
    const timer = setTimeout(() => {
      onSearch({ ...searchParams, query: query || undefined });
    }, 300); // Debounce
    return () => clearTimeout(timer);
  }, [searchParams, query, onSearch]);

  // Toggle a preset
  const togglePreset = useCallback((preset: SearchPreset) => {
    setActivePresets(prev => {
      const isActive = prev.includes(preset.id);
      if (isActive) {
        // Remove preset params
        const newParams = { ...searchParams };
        Object.keys(preset.params).forEach(key => {
          delete newParams[key as keyof CapsuleSearchParams];
        });
        setSearchParams(newParams);
        return prev.filter(id => id !== preset.id);
      } else {
        // Add preset params
        setSearchParams(prev => ({ ...prev, ...preset.params }));
        return [...prev, preset.id];
      }
    });
  }, [searchParams]);

  // Set a specific filter
  const setFilter = useCallback((key: keyof CapsuleSearchParams, value: any) => {
    if (value === undefined || value === '' || value === null) {
      setSearchParams(prev => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    } else {
      setSearchParams(prev => ({ ...prev, [key]: value }));
    }
  }, []);

  // Clear all filters
  const clearAll = useCallback(() => {
    setSearchParams({});
    setQuery('');
    setActivePresets([]);
  }, []);

  // Count active filters
  const activeFilterCount = useMemo(() => {
    return Object.keys(searchParams).filter(k =>
      k !== 'page' && k !== 'per_page' && k !== 'sort_by' && k !== 'sort_order'
    ).length + (query ? 1 : 0);
  }, [searchParams, query]);

  return (
    <Card className="w-full">
      <CardContent className={compact ? "p-3" : "p-4"}>
        {/* Main Search Bar */}
        <div className="flex flex-col gap-3">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search capsules... (try: quality:A risk:high)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-10 pr-4"
              />
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2"
            >
              <Filter className="h-4 w-4" />
              <span className="hidden sm:inline">Filters</span>
              {activeFilterCount > 0 && (
                <Badge variant="secondary" className="ml-1 h-5 w-5 p-0 justify-center">
                  {activeFilterCount}
                </Badge>
              )}
              {showAdvanced ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </Button>
            {activeFilterCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAll}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Quick Presets */}
          {showPresets && !compact && (
            <div className="flex flex-wrap gap-2">
              {DEFAULT_PRESETS.slice(0, 6).map(preset => {
                const Icon = getPresetIcon(preset.icon);
                const isActive = activePresets.includes(preset.id);
                return (
                  <Button
                    key={preset.id}
                    variant={isActive ? "default" : "outline"}
                    size="sm"
                    onClick={() => togglePreset(preset)}
                    className={`h-7 text-xs ${isActive ? '' : 'hover:bg-gray-100'}`}
                    title={preset.description}
                  >
                    <Icon className="h-3 w-3 mr-1" />
                    {preset.name}
                  </Button>
                );
              })}
            </div>
          )}

          {/* Active Filters Display */}
          {activeFilterCount > 0 && (
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-xs text-gray-500">Active:</span>
              {query && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <Search className="h-3 w-3" />
                  "{query}"
                  <button onClick={() => setQuery('')} className="ml-1 hover:text-red-500">
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {searchParams.quality_grade && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <Star className="h-3 w-3" />
                  Quality: {Array.isArray(searchParams.quality_grade)
                    ? searchParams.quality_grade.join(', ')
                    : searchParams.quality_grade}
                  <button onClick={() => setFilter('quality_grade', undefined)} className="ml-1 hover:text-red-500">
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {searchParams.signature_valid && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <Shield className="h-3 w-3" />
                  Verified
                  <button onClick={() => setFilter('signature_valid', undefined)} className="ml-1 hover:text-red-500">
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {searchParams.timestamp_trusted && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  RFC 3161
                  <button onClick={() => setFilter('timestamp_trusted', undefined)} className="ml-1 hover:text-red-500">
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {searchParams.date_preset && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {searchParams.date_preset}
                  <button onClick={() => setFilter('date_preset', undefined)} className="ml-1 hover:text-red-500">
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {searchParams.type && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <FileText className="h-3 w-3" />
                  {searchParams.type}
                  <button onClick={() => setFilter('type', undefined)} className="ml-1 hover:text-red-500">
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {searchParams.outcome_status && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <Target className="h-3 w-3" />
                  {searchParams.outcome_status}
                  <button onClick={() => setFilter('outcome_status', undefined)} className="ml-1 hover:text-red-500">
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
              {searchParams.has_reasoning_chain && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <GitBranch className="h-3 w-3" />
                  Has Reasoning
                  <button onClick={() => setFilter('has_reasoning_chain', undefined)} className="ml-1 hover:text-red-500">
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              )}
            </div>
          )}

          {/* Advanced Filter Panel */}
          {showAdvanced && (
            <div className="border-t pt-4 mt-2">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Quality Grade Filter */}
                <div>
                  <label className="block text-sm font-medium mb-2 flex items-center gap-1">
                    <Star className="h-4 w-4" />
                    Quality Grade
                  </label>
                  <div className="flex flex-wrap gap-1">
                    {['A', 'B', 'C', 'D', 'F'].map(grade => {
                      const count = facets.qualityGrades[grade] || 0;
                      const isSelected = Array.isArray(searchParams.quality_grade)
                        ? searchParams.quality_grade.includes(grade)
                        : searchParams.quality_grade === grade;
                      return (
                        <button
                          key={grade}
                          onClick={() => {
                            const current = Array.isArray(searchParams.quality_grade)
                              ? searchParams.quality_grade
                              : searchParams.quality_grade ? [searchParams.quality_grade] : [];
                            if (isSelected) {
                              const next = current.filter(g => g !== grade);
                              setFilter('quality_grade', next.length ? next : undefined);
                            } else {
                              setFilter('quality_grade', [...current, grade]);
                            }
                          }}
                          className={`px-2 py-1 text-xs rounded border ${
                            isSelected
                              ? gradeColors[grade]
                              : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
                          }`}
                        >
                          {grade} ({count})
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Verification Filters */}
                <div>
                  <label className="block text-sm font-medium mb-2 flex items-center gap-1">
                    <Shield className="h-4 w-4" />
                    Verification
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={searchParams.signature_valid || false}
                        onChange={(e) => setFilter('signature_valid', e.target.checked || undefined)}
                        className="rounded"
                      />
                      <span>Signed ({facets.verifiedCount})</span>
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={searchParams.timestamp_trusted || false}
                        onChange={(e) => setFilter('timestamp_trusted', e.target.checked || undefined)}
                        className="rounded"
                      />
                      <span>RFC 3161 Timestamp ({facets.trustedTimestampCount})</span>
                    </label>
                  </div>
                </div>

                {/* Date Range Filter */}
                <div>
                  <label className="block text-sm font-medium mb-2 flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    Time Period
                  </label>
                  <select
                    value={searchParams.date_preset || ''}
                    onChange={(e) => setFilter('date_preset', e.target.value || undefined)}
                    className="w-full p-2 border rounded-md text-sm"
                  >
                    <option value="">All Time</option>
                    <option value="today">Today</option>
                    <option value="week">This Week</option>
                    <option value="month">This Month</option>
                    <option value="quarter">This Quarter</option>
                    <option value="year">This Year</option>
                  </select>
                </div>

                {/* Type Filter */}
                <div>
                  <label className="block text-sm font-medium mb-2 flex items-center gap-1">
                    <Layers className="h-4 w-4" />
                    Capsule Type
                  </label>
                  <select
                    value={searchParams.type || ''}
                    onChange={(e) => setFilter('type', e.target.value || undefined)}
                    className="w-full p-2 border rounded-md text-sm"
                  >
                    <option value="">All Types</option>
                    {Object.entries(facets.types).map(([type, count]) => (
                      <option key={type} value={type}>
                        {type} ({count})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Content Filters */}
                <div>
                  <label className="block text-sm font-medium mb-2 flex items-center gap-1">
                    <BookOpen className="h-4 w-4" />
                    Content
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={searchParams.has_reasoning_chain || false}
                        onChange={(e) => setFilter('has_reasoning_chain', e.target.checked || undefined)}
                        className="rounded"
                      />
                      <span>Has Reasoning ({facets.withReasoningCount})</span>
                    </label>
                    <label className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={searchParams.has_outcome || false}
                        onChange={(e) => setFilter('has_outcome', e.target.checked || undefined)}
                        className="rounded"
                      />
                      <span>Has Outcome ({facets.withOutcomeCount})</span>
                    </label>
                  </div>
                </div>

                {/* Outcome Filter */}
                <div>
                  <label className="block text-sm font-medium mb-2 flex items-center gap-1">
                    <Target className="h-4 w-4" />
                    Outcome Status
                  </label>
                  <select
                    value={searchParams.outcome_status || ''}
                    onChange={(e) => setFilter('outcome_status', e.target.value || undefined)}
                    className="w-full p-2 border rounded-md text-sm"
                  >
                    <option value="">All</option>
                    {Object.entries(facets.outcomes).map(([status, count]) => (
                      <option key={status} value={status}>
                        {status} ({count})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Risk Filter */}
                <div>
                  <label className="block text-sm font-medium mb-2 flex items-center gap-1">
                    <AlertTriangle className="h-4 w-4" />
                    Risk Level
                  </label>
                  <select
                    value={searchParams.risk_level || ''}
                    onChange={(e) => setFilter('risk_level', e.target.value || undefined)}
                    className="w-full p-2 border rounded-md text-sm"
                  >
                    <option value="">All Levels</option>
                    <option value="low">Low Risk</option>
                    <option value="medium">Medium Risk</option>
                    <option value="high">High Risk</option>
                    <option value="critical">Critical Risk</option>
                  </select>
                </div>

                {/* Sort Options */}
                <div>
                  <label className="block text-sm font-medium mb-2 flex items-center gap-1">
                    <BarChart3 className="h-4 w-4" />
                    Sort By
                  </label>
                  <div className="flex gap-2">
                    <select
                      value={searchParams.sort_by || 'timestamp'}
                      onChange={(e) => setFilter('sort_by', e.target.value)}
                      className="flex-1 p-2 border rounded-md text-sm"
                    >
                      <option value="timestamp">Date</option>
                      <option value="quality_score">Quality</option>
                      <option value="risk_score">Risk</option>
                      <option value="type">Type</option>
                    </select>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setFilter('sort_order', searchParams.sort_order === 'asc' ? 'desc' : 'asc')}
                      className="px-2"
                    >
                      {searchParams.sort_order === 'asc' ? '↑' : '↓'}
                    </Button>
                  </div>
                </div>
              </div>

              {/* All Presets */}
              <div className="mt-4 pt-4 border-t">
                <label className="block text-sm font-medium mb-2">Quick Filters</label>
                <div className="flex flex-wrap gap-2">
                  {DEFAULT_PRESETS.map(preset => {
                    const Icon = getPresetIcon(preset.icon);
                    const isActive = activePresets.includes(preset.id);
                    return (
                      <Button
                        key={preset.id}
                        variant={isActive ? "default" : "outline"}
                        size="sm"
                        onClick={() => togglePreset(preset)}
                        className={`h-8 text-xs ${isActive ? '' : 'hover:bg-gray-100'}`}
                        title={preset.description}
                      >
                        <Icon className="h-3 w-3 mr-1" />
                        {preset.name}
                      </Button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default CapsuleSearch;
