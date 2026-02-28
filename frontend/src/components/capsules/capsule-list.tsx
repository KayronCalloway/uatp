'use client';

import { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Database,
  Eye,
  Calendar,
  User,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  ArrowLeft,
  Shield,
  Clock,
  AlertTriangle,
  Lock
} from 'lucide-react';
import { isEncrypted } from '@/lib/capsule-encryption';
import { formatDate, truncateText, getCapsuleTypeColor } from '@/lib/utils';
import { ListCapsulesQuery, AnyCapsule, CapsuleSearchParams } from '@/types/api';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { getMockCapsules, mockApiCall } from '@/lib/mock-data';
import { QualityBadgeInline } from '@/components/capsules/quality-badge';
import { CapsuleSearch } from '@/components/capsules/capsule-search';

interface CapsuleListProps {
  onCapsuleSelect?: (capsule: AnyCapsule) => void;
  onBack?: () => void;
}

export function CapsuleList({ onCapsuleSelect, onBack }: CapsuleListProps) {
  const { isDemoMode } = useDemoMode();
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [compress, setCompress] = useState(false);

  // Advanced search state using new comprehensive search params
  const [searchParams, setSearchParams] = useState<CapsuleSearchParams>({
    sort_by: 'timestamp',
    sort_order: 'desc'
  });

  // Handle search param changes from CapsuleSearch component
  const handleSearch = useCallback((params: CapsuleSearchParams) => {
    setSearchParams(params);
    setCurrentPage(1); // Reset to first page on search change
  }, []);

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

  // Comprehensive filtering using CapsuleSearchParams
  const filteredCapsules = useMemo(() => {
    let filtered = capsules.filter(capsule => {
      // Text search across multiple fields
      if (searchParams.query) {
        const q = searchParams.query.toLowerCase();
        const searchableText = [
          capsule.id,
          capsule.capsule_id,
          capsule.content,
          capsule.type,
          capsule.capsule_type,
          capsule.agent_id,
          capsule.verification?.signer,
          capsule.payload?.plain_language_summary?.decision,
          capsule.payload?.plain_language_summary?.why,
          JSON.stringify(capsule.payload?.reasoning_chain || [])
        ].filter(Boolean).join(' ').toLowerCase();

        if (!searchableText.includes(q)) return false;
      }

      // Type filter
      if (searchParams.type) {
        const capsuleType = capsule.type || capsule.capsule_type;
        if (capsuleType !== searchParams.type) return false;
      }

      // Agent filter
      if (searchParams.agent_id) {
        const agent = capsule.verification?.signer || capsule.agent_id;
        if (agent !== searchParams.agent_id) return false;
      }

      // Date preset filter
      if (searchParams.date_preset) {
        const now = new Date();
        const capsuleDate = new Date(capsule.timestamp || capsule.created_at);
        const daysDiff = Math.floor((now.getTime() - capsuleDate.getTime()) / (1000 * 60 * 60 * 24));

        switch (searchParams.date_preset) {
          case 'today':
            if (daysDiff > 0) return false;
            break;
          case 'week':
            if (daysDiff > 7) return false;
            break;
          case 'month':
            if (daysDiff > 30) return false;
            break;
          case 'quarter':
            if (daysDiff > 90) return false;
            break;
          case 'year':
            if (daysDiff > 365) return false;
            break;
        }
      }

      // Quality grade filter
      if (searchParams.quality_grade) {
        const grade = capsule.payload?.quality_assessment?.quality_grade;
        const grades = Array.isArray(searchParams.quality_grade)
          ? searchParams.quality_grade
          : [searchParams.quality_grade];
        if (!grade || !grades.includes(grade)) return false;
      }

      // Quality minimum score filter
      if (searchParams.quality_min !== undefined) {
        const score = capsule.payload?.quality_assessment?.overall_quality || 0;
        if (score < searchParams.quality_min) return false;
      }

      // Verification filters
      if (searchParams.signature_valid === true) {
        if (!capsule.verification?.signature) return false;
      }

      if (searchParams.timestamp_trusted === true) {
        if (!capsule.verification?.timestamp?.trusted) return false;
      }

      // Outcome status filter
      if (searchParams.outcome_status) {
        const outcome = capsule.payload?.outcome?.result || 'untracked';
        if (outcome !== searchParams.outcome_status) return false;
      }

      // Has outcome filter
      if (searchParams.has_outcome === true) {
        if (!capsule.payload?.outcome) return false;
      } else if (searchParams.has_outcome === false) {
        if (capsule.payload?.outcome) return false;
      }

      // Content filters
      if (searchParams.has_reasoning_chain === true) {
        if (!capsule.payload?.reasoning_chain?.length) return false;
      }

      if (searchParams.has_alternatives === true) {
        if (!capsule.payload?.alternatives_considered?.length) return false;
      }

      if (searchParams.has_plain_language === true) {
        if (!capsule.payload?.plain_language_summary) return false;
      }

      // Risk level filter
      if (searchParams.risk_level) {
        const riskAssessment = capsule.payload?.risk_assessment;
        if (!riskAssessment) return false;

        const probCorrect = riskAssessment.probability_correct || 0.5;
        switch (searchParams.risk_level) {
          case 'low':
            if (probCorrect < 0.8) return false;
            break;
          case 'medium':
            if (probCorrect < 0.6 || probCorrect >= 0.8) return false;
            break;
          case 'high':
            if (probCorrect < 0.4 || probCorrect >= 0.6) return false;
            break;
          case 'critical':
            if (probCorrect >= 0.4) return false;
            break;
        }
      }

      // Probability correct range filter
      if (searchParams.probability_correct_min !== undefined) {
        const prob = capsule.payload?.risk_assessment?.probability_correct || 0;
        if (prob < searchParams.probability_correct_min) return false;
      }
      if (searchParams.probability_correct_max !== undefined) {
        const prob = capsule.payload?.risk_assessment?.probability_correct || 1;
        if (prob > searchParams.probability_correct_max) return false;
      }

      // Lineage filters
      if (searchParams.has_parents === true) {
        if (!capsule.payload?.lineage?.parent_capsules?.length) return false;
      }

      if (searchParams.chain_id) {
        if (capsule.payload?.chain_context?.chain_id !== searchParams.chain_id) return false;
      }

      return true;
    });

    // Sorting
    const sortBy = searchParams.sort_by || 'timestamp';
    const sortOrder = searchParams.sort_order || 'desc';

    filtered.sort((a, b) => {
      let aVal: any, bVal: any;

      switch (sortBy) {
        case 'timestamp':
          aVal = new Date(a.timestamp || a.created_at).getTime();
          bVal = new Date(b.timestamp || b.created_at).getTime();
          break;
        case 'quality_score':
          aVal = a.payload?.quality_assessment?.overall_quality || 0;
          bVal = b.payload?.quality_assessment?.overall_quality || 0;
          break;
        case 'risk_score':
          aVal = a.payload?.risk_assessment?.probability_correct || 0.5;
          bVal = b.payload?.risk_assessment?.probability_correct || 0.5;
          break;
        case 'type':
          aVal = a.type || a.capsule_type || '';
          bVal = b.type || b.capsule_type || '';
          break;
        case 'agent_id':
          aVal = a.verification?.signer || a.agent_id || '';
          bVal = b.verification?.signer || b.agent_id || '';
          break;
        default:
          aVal = a.id || '';
          bVal = b.id || '';
      }

      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    return filtered;
  }, [capsules, searchParams]);

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

      {/* World-Class Search Component */}
      <CapsuleSearch
        onSearch={handleSearch}
        capsules={capsules}
        initialParams={searchParams}
        showPresets={true}
      />

      {/* Results Summary & Page Size */}
      <Card>
        <CardContent className="p-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="text-sm text-gray-600">
              Showing <strong>{filteredCapsules.length}</strong> of <strong>{capsules.length}</strong> capsules
              {filteredCapsules.length !== capsules.length && (
                <span className="text-blue-600 ml-1">(filtered)</span>
              )}
            </div>
            <div className="flex items-center gap-3">
              <select
                value={pageSize}
                onChange={(e) => setPageSize(Number(e.target.value))}
                className="px-2 py-1 border rounded text-sm"
              >
                <option value={10}>10 per page</option>
                <option value={25}>25 per page</option>
                <option value={50}>50 per page</option>
                <option value={100}>100 per page</option>
              </select>
              <label className="flex items-center gap-1 text-sm text-gray-500">
                <input
                  type="checkbox"
                  checked={compress}
                  onChange={(e) => setCompress(e.target.checked)}
                  className="rounded"
                />
                <span>Compact</span>
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
              {Object.keys(searchParams).length > 2 ? 'No capsules found matching your filters.' : 'No capsules available.'}
            </div>
          ) : (
            <div className="divide-y">
              {filteredCapsules.map((capsule) => {
                const hasSignature = !!capsule.verification?.signature;
                const hasTrustedTimestamp = capsule.verification?.timestamp?.trusted;
                const riskProb = capsule.payload?.risk_assessment?.probability_correct;
                const isHighRisk = riskProb !== undefined && riskProb < 0.6;
                const qualityGrade = capsule.payload?.quality_assessment?.quality_grade;
                const plainSummary = capsule.payload?.plain_language_summary?.decision;
                const capsuleIsEncrypted = isEncrypted(capsule);

                return (
                  <div
                    key={capsule.capsule_id || capsule.id || `capsule-${Math.random()}`}
                    className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => handleCapsuleClick(capsule)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        {/* Top row: Type, Quality, ID */}
                        <div className="flex items-center flex-wrap gap-2 mb-2">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getCapsuleTypeColor(capsule.capsule_type)}`}>
                            {capsule.capsule_type}
                          </span>
                          <QualityBadgeInline capsuleId={capsule.capsule_id} />

                          {/* Verification indicators */}
                          {hasSignature && (
                            <Badge variant="outline" className="h-5 text-xs flex items-center gap-1 bg-green-50 text-green-700 border-green-200">
                              <Shield className="h-3 w-3" />
                              Signed
                            </Badge>
                          )}
                          {hasTrustedTimestamp && (
                            <Badge variant="outline" className="h-5 text-xs flex items-center gap-1 bg-blue-50 text-blue-700 border-blue-200">
                              <Clock className="h-3 w-3" />
                              RFC 3161
                            </Badge>
                          )}
                          {isHighRisk && (
                            <Badge variant="outline" className="h-5 text-xs flex items-center gap-1 bg-orange-50 text-orange-700 border-orange-200">
                              <AlertTriangle className="h-3 w-3" />
                              {Math.round((riskProb || 0) * 100)}%
                            </Badge>
                          )}
                          {capsuleIsEncrypted && (
                            <Badge variant="outline" className="h-5 text-xs flex items-center gap-1 bg-purple-50 text-purple-700 border-purple-200">
                              <Lock className="h-3 w-3" />
                              E2E
                            </Badge>
                          )}

                          <span className="text-xs text-gray-400 font-mono ml-auto">
                            {truncateText(capsule.capsule_id, 12)}
                          </span>
                        </div>

                        {/* Main content - show plain language summary if available */}
                        {plainSummary ? (
                          <p className="text-sm text-gray-900 mb-2 line-clamp-2">
                            {truncateText(plainSummary, 150)}
                          </p>
                        ) : (
                          <p className="text-sm text-gray-600 mb-2 italic">
                            {capsule.capsule_type} capsule
                          </p>
                        )}

                        {/* Meta row */}
                        <div className="flex items-center flex-wrap gap-3 text-xs text-gray-500">
                          <div className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            <span>{truncateText(capsule.verification?.signer || 'unknown', 20)}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            <span>{formatDate(capsule.timestamp)}</span>
                          </div>
                          {capsule.payload?.outcome && (
                            <Badge
                              variant="outline"
                              className={`h-4 text-xs ${
                                capsule.payload.outcome.result === 'successful'
                                  ? 'bg-green-50 text-green-700'
                                  : capsule.payload.outcome.result === 'failed'
                                  ? 'bg-red-50 text-red-700'
                                  : 'bg-gray-50 text-gray-600'
                              }`}
                            >
                              {capsule.payload.outcome.result}
                            </Badge>
                          )}
                        </div>
                      </div>

                      <Button variant="ghost" size="sm" className="ml-2">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                );
              })}
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
