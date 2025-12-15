'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  Filter,
  Database,
  Eye,
  Calendar,
  User,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  SortAsc,
  SortDesc,
  X,
  Tag,
  Clock,
  ArrowLeft
} from 'lucide-react';
import { formatDate, truncateText, getCapsuleTypeColor } from '@/lib/utils';
import { ListCapsulesQuery, AnyCapsule } from '@/types/api';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { getMockCapsules, mockApiCall } from '@/lib/mock-data';
import { QualityBadgeInline } from '@/components/capsules/quality-badge';

interface CapsuleListProps {
  onCapsuleSelect?: (capsule: AnyCapsule) => void;
  onBack?: () => void;
}

export function CapsuleList({ onCapsuleSelect, onBack }: CapsuleListProps) {
  const { isDemoMode } = useDemoMode();
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [compress, setCompress] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  // Advanced filtering state
  const [filters, setFilters] = useState({
    type: '',
    agent: '',
    dateRange: '',
    tags: [] as string[],
    trustScore: '',
    sortBy: 'created_at',
    sortOrder: 'desc' as 'asc' | 'desc'
  });

  const queryParams: ListCapsulesQuery = {
    page: currentPage,
    per_page: pageSize,
    compress,
    demo_mode: false,  // Explicit: fetch live data only (exclude demo-* capsules)
  };

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['capsules', queryParams, isDemoMode],
    queryFn: async () => {
      if (isDemoMode) {
        console.log('Capsules: Using mock capsule data (demo mode)');
        return mockApiCall(getMockCapsules());
      }
      console.log('Capsules: Fetching real capsule data...');
      return api.getCapsules(queryParams);
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
    enabled: true, // Always enabled, but uses mock in demo mode
  });

  const capsules = data?.capsules || [];

  // Advanced filtering and sorting
  const filteredCapsules = useMemo(() => {
    const filtered = capsules.filter(capsule => {
      // Search term filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const matchesSearch =
          capsule.id?.toLowerCase().includes(searchLower) ||
          capsule.content?.toLowerCase().includes(searchLower) ||
          capsule.type?.toLowerCase().includes(searchLower) ||
          capsule.agent_id?.toLowerCase().includes(searchLower);
        if (!matchesSearch) return false;
      }

      // Type filter
      if (filters.type && capsule.type !== filters.type) return false;

      // Agent filter
      if (filters.agent && capsule.agent_id !== filters.agent) return false;

      // Date range filter
      if (filters.dateRange) {
        const now = new Date();
        const capsuleDate = new Date(capsule.created_at);
        const daysDiff = Math.floor((now.getTime() - capsuleDate.getTime()) / (1000 * 60 * 60 * 24));

        switch (filters.dateRange) {
          case 'today':
            if (daysDiff > 0) return false;
            break;
          case 'week':
            if (daysDiff > 7) return false;
            break;
          case 'month':
            if (daysDiff > 30) return false;
            break;
          case 'year':
            if (daysDiff > 365) return false;
            break;
        }
      }

      // Trust score filter
      if (filters.trustScore) {
        const trustScore = capsule.trust_score || 0;
        switch (filters.trustScore) {
          case 'high':
            if (trustScore < 0.8) return false;
            break;
          case 'medium':
            if (trustScore < 0.5 || trustScore >= 0.8) return false;
            break;
          case 'low':
            if (trustScore >= 0.5) return false;
            break;
        }
      }

      return true;
    });

    // Sorting
    const sortedFiltered = [...filtered].sort((a, b) => {
      let aVal, bVal;

      switch (filters.sortBy) {
        case 'created_at':
          aVal = new Date(a.created_at).getTime();
          bVal = new Date(b.created_at).getTime();
          break;
        case 'type':
          aVal = a.type || '';
          bVal = b.type || '';
          break;
        case 'agent_id':
          aVal = a.agent_id || '';
          bVal = b.agent_id || '';
          break;
        case 'trust_score':
          aVal = a.trust_score || 0;
          bVal = b.trust_score || 0;
          break;
        default:
          aVal = a.id || '';
          bVal = b.id || '';
      }

      if (filters.sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    return sortedFiltered;
  }, [capsules, searchTerm, filters]);

  // Get unique values for filter options
  const filterOptions = useMemo(() => {
    const types = [...new Set(capsules.map(c => c.type).filter(Boolean))];
    const agents = [...new Set(capsules.map(c => c.agent_id).filter(Boolean))];
    return { types, agents };
  }, [capsules]);

  const clearFilters = () => {
    setFilters({
      type: '',
      agent: '',
      dateRange: '',
      tags: [],
      trustScore: '',
      sortBy: 'created_at',
      sortOrder: 'desc'
    });
    setSearchTerm('');
  };

  const activeFiltersCount = Object.values(filters).filter(v =>
    Array.isArray(v) ? v.length > 0 : v !== '' && v !== 'created_at' && v !== 'desc'
  ).length + (searchTerm ? 1 : 0);

  // Legacy simple filter for backward compatibility
  const legacyFilteredCapsules = capsules.filter(capsule =>
    !searchTerm ||
    capsule.id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    capsule.content?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    capsule.type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    capsule.agent_id?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCapsuleClick = (capsule: AnyCapsule) => {
    if (onCapsuleSelect) {
      onCapsuleSelect(capsule);
    }
  };

  if (error) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="flex items-center justify-center text-red-600">
            <p>Error loading capsules: {error.message}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full space-y-4">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {onBack && (
                <Button variant="ghost" size="sm" onClick={onBack}>
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              )}
              <CardTitle className="flex items-center space-x-2">
                <Database className="h-5 w-5" />
                <span>Capsules</span>
              </CardTitle>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Search and Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-4">
            {/* Search and Filter Toggle */}
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search capsules..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center space-x-2"
                >
                  <Filter className="h-4 w-4" />
                  <span>Filters</span>
                  {activeFiltersCount > 0 && (
                    <Badge variant="secondary" className="ml-1">
                      {activeFiltersCount}
                    </Badge>
                  )}
                </Button>
                {activeFiltersCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearFilters}
                    className="text-red-600 hover:text-red-700"
                  >
                    <X className="h-4 w-4 mr-1" />
                    Clear
                  </Button>
                )}
              </div>
            </div>

            {/* Advanced Filters */}
            {showFilters && (
              <div className="border-t pt-4">
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                  {/* Type Filter */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Type</label>
                    <select
                      value={filters.type}
                      onChange={(e) => setFilters({...filters, type: e.target.value})}
                      className="w-full p-2 border rounded-md"
                    >
                      <option value="">All Types</option>
                      {filterOptions.types.map((type) => (
                        <option key={`type-${type}`} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>

                  {/* Agent Filter */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Agent</label>
                    <select
                      value={filters.agent}
                      onChange={(e) => setFilters({...filters, agent: e.target.value})}
                      className="w-full p-2 border rounded-md"
                    >
                      <option value="">All Agents</option>
                      {filterOptions.agents.map((agent) => (
                        <option key={`agent-${agent}`} value={agent}>{agent}</option>
                      ))}
                    </select>
                  </div>

                  {/* Date Range Filter */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Date Range</label>
                    <select
                      value={filters.dateRange}
                      onChange={(e) => setFilters({...filters, dateRange: e.target.value})}
                      className="w-full p-2 border rounded-md"
                    >
                      <option value="">All Time</option>
                      <option value="today">Today</option>
                      <option value="week">This Week</option>
                      <option value="month">This Month</option>
                      <option value="year">This Year</option>
                    </select>
                  </div>

                  {/* Trust Score Filter */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Trust Score</label>
                    <select
                      value={filters.trustScore}
                      onChange={(e) => setFilters({...filters, trustScore: e.target.value})}
                      className="w-full p-2 border rounded-md"
                    >
                      <option value="">All Scores</option>
                      <option value="high">High (0.8+)</option>
                      <option value="medium">Medium (0.5-0.8)</option>
                      <option value="low">Low (0.5-)</option>
                    </select>
                  </div>

                  {/* Sort Options */}
                  <div>
                    <label className="block text-sm font-medium mb-2">Sort By</label>
                    <div className="flex space-x-2">
                      <select
                        value={filters.sortBy}
                        onChange={(e) => setFilters({...filters, sortBy: e.target.value})}
                        className="flex-1 p-2 border rounded-md"
                      >
                        <option value="created_at">Date</option>
                        <option value="type">Type</option>
                        <option value="agent_id">Agent</option>
                        <option value="trust_score">Trust Score</option>
                      </select>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setFilters({...filters, sortOrder: filters.sortOrder === 'asc' ? 'desc' : 'asc'})}
                        className="px-2"
                      >
                        {filters.sortOrder === 'asc' ? <SortAsc className="h-4 w-4" /> : <SortDesc className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Filter Summary */}
                <div className="mt-4 pt-4 border-t">
                  <div className="flex flex-wrap gap-2 items-center">
                    <span className="text-sm text-gray-600">Active filters:</span>
                    {searchTerm && (
                      <Badge key="search-filter" variant="outline" className="flex items-center space-x-1">
                        <Search className="h-3 w-3" />
                        <span>Search: {searchTerm}</span>
                      </Badge>
                    )}
                    {filters.type && (
                      <Badge key="type-filter" variant="outline" className="flex items-center space-x-1">
                        <Tag className="h-3 w-3" />
                        <span>Type: {filters.type}</span>
                      </Badge>
                    )}
                    {filters.agent && (
                      <Badge key="agent-filter" variant="outline" className="flex items-center space-x-1">
                        <User className="h-3 w-3" />
                        <span>Agent: {filters.agent}</span>
                      </Badge>
                    )}
                    {filters.dateRange && (
                      <Badge key="date-filter" variant="outline" className="flex items-center space-x-1">
                        <Clock className="h-3 w-3" />
                        <span>Date: {filters.dateRange}</span>
                      </Badge>
                    )}
                    {filters.trustScore && (
                      <Badge key="trust-filter" variant="outline" className="flex items-center space-x-1">
                        <span>Trust: {filters.trustScore}</span>
                      </Badge>
                    )}
                    {activeFiltersCount === 0 && (
                      <span key="no-filters" className="text-sm text-gray-400">None</span>
                    )}
                  </div>
                  <div className="mt-2 text-sm text-gray-600">
                    Showing {filteredCapsules.length} of {capsules.length} capsules
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={pageSize}
                onChange={(e) => setPageSize(Number(e.target.value))}
                className="px-3 py-2 border rounded-md text-sm"
              >
                <option value={10}>10 per page</option>
                <option value={25}>25 per page</option>
                <option value={50}>50 per page</option>
              </select>
              <label className="flex items-center space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={compress}
                  onChange={(e) => setCompress(e.target.checked)}
                  className="rounded"
                />
                <span>Compress</span>
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Capsule List */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : filteredCapsules.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {searchTerm ? 'No capsules found matching your search.' : 'No capsules available.'}
            </div>
          ) : (
            <div className="divide-y">
              {filteredCapsules.map((capsule) => (
                <div
                  key={capsule.capsule_id || capsule.id || `capsule-${Math.random()}`}
                  className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => handleCapsuleClick(capsule)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getCapsuleTypeColor(capsule.capsule_type)}`}>
                          {capsule.capsule_type}
                        </span>
                        <QualityBadgeInline capsuleId={capsule.capsule_id} />
                        <span className="text-sm text-gray-500 font-mono">
                          {truncateText(capsule.capsule_id, 12)}
                        </span>
                      </div>

                      <h3 className="text-sm font-medium text-gray-900 mb-1">
                        {truncateText(capsule.capsule_type, 100)}
                      </h3>

                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <div className="flex items-center space-x-1">
                          <User className="h-3 w-3" />
                          <span>{truncateText(capsule.verification?.signer, 20)}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Calendar className="h-3 w-3" />
                          <span>{formatDate(capsule.timestamp)}</span>
                        </div>
                      </div>
                    </div>

                    <Button variant="ghost" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Showing {filteredCapsules.length} of {capsules.length} capsules
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm">
                Page {currentPage}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => prev + 1)}
                disabled={filteredCapsules.length < pageSize}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
