'use client';

import { useQuery } from '@tanstack/react-query';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { api } from '@/lib/api-client';
import {
  getMockTrustMetricsData,
  getMockTrustPolicies,
  getMockRecentViolations,
  getMockQuarantinedAgents,
  mockApiCall
} from '@/lib/mock-data';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Shield,
  AlertTriangle,
  Users,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Clock,
  User,
  Eye,
  Lock,
  Activity,
  BarChart3,
  PieChart,
  Zap,
  Target,
  Gauge,
  Play,
  AlertCircle
} from 'lucide-react';
import { useState, useMemo } from 'react';
import { formatDate, truncateText } from '@/lib/utils';
import { logger } from '@/lib/logger';

export function TrustDashboard() {
  const { isDemoMode } = useDemoMode();

  const [activeTab, setActiveTab] = useState<'overview' | 'analytics' | 'violations' | 'agents'>('overview');
  const [timeRange, setTimeRange] = useState('24h');

  const { data: trustMetrics, isLoading: metricsLoading, refetch: refetchMetrics, error: metricsError } = useQuery({
    queryKey: ['trust-metrics', isDemoMode],
    queryFn: async () => {
      if (isDemoMode) {
        logger.debug('Trust: Using mock trust metrics (demo mode)');
        return mockApiCall(getMockTrustMetricsData());
      }
      try {
        logger.debug('Trust: Fetching trust metrics...');
        const result = await api.getTrustMetrics();
        logger.debug('Trust: Trust metrics response:', { result });
        return result;
      } catch (error) {
        logger.error('Trust: Trust metrics error:', { error });
        throw error;
      }
    },
    refetchInterval: isDemoMode ? false : 30000, // No refresh in demo mode
    retry: isDemoMode ? 0 : 3,
    retryDelay: 1000,
    enabled: isDemoMode, // Only fetch when in demo mode
  });

  const { data: trustPolicies, isLoading: policiesLoading, error: policiesError } = useQuery({
    queryKey: ['trust-policies', isDemoMode],
    queryFn: async () => {
      if (isDemoMode) {
        logger.debug('Trust: Using mock trust policies (demo mode)');
        return mockApiCall(getMockTrustPolicies());
      }
      try {
        logger.debug('Trust: Fetching trust policies...');
        const result = await api.getTrustPolicies();
        logger.debug('Trust: Trust policies response:', { result });
        return result;
      } catch (error) {
        logger.error('Trust: Trust policies error:', { error });
        throw error;
      }
    },
    refetchInterval: isDemoMode ? false : 120000, // No refresh in demo mode
    retry: isDemoMode ? 0 : 3,
    enabled: isDemoMode, // Only fetch when in demo mode
  });

  const { data: recentViolations, isLoading: violationsLoading, error: violationsError } = useQuery({
    queryKey: ['trust-violations', isDemoMode],
    queryFn: async () => {
      if (isDemoMode) {
        logger.debug('Trust: Using mock violations (demo mode)');
        return mockApiCall(getMockRecentViolations());
      }
      try {
        logger.debug('Trust: Fetching recent violations...');
        const result = await api.getRecentViolations();
        logger.debug('Trust: Recent violations response:', { result });
        return result;
      } catch (error) {
        logger.error('Trust: Recent violations error:', { error });
        throw error;
      }
    },
    refetchInterval: isDemoMode ? false : 60000, // No refresh in demo mode
    retry: isDemoMode ? 0 : 3,
    enabled: isDemoMode, // Only fetch when in demo mode
  });

  const { data: quarantinedAgents, isLoading: quarantineLoading, error: quarantineError } = useQuery({
    queryKey: ['quarantined-agents', isDemoMode],
    queryFn: async () => {
      if (isDemoMode) {
        logger.debug('Trust: Using mock quarantined agents (demo mode)');
        return mockApiCall(getMockQuarantinedAgents());
      }
      try {
        logger.debug('Trust: Fetching quarantined agents...');
        const result = await api.getQuarantinedAgents();
        logger.debug('Trust: Quarantined agents response:', { result });
        return result;
      } catch (error) {
        logger.error('Trust: Quarantined agents error:', { error });
        throw error;
      }
    },
    refetchInterval: isDemoMode ? false : 90000, // No refresh in demo mode
    retry: isDemoMode ? 0 : 3,
    enabled: isDemoMode, // Only fetch when in demo mode
  });

  // Real-time analytics calculations
  const analytics = useMemo(() => {
    if (!trustMetrics) return null;

    // Handle demo mode mock data structure
    if (isDemoMode && typeof trustMetrics === 'object' && 'overall_score' in trustMetrics) {
      return {
        trustDistribution: {},
        avgTrust: (trustMetrics.overall_score || 0) / 100, // Convert from 0-100 to 0-1
        trustTrend: 0.02, // Positive trend for demo
        totalAgents: 15, // From demo data
        activeAgents: 15
      };
    }

    // Handle the actual API response structure
    if (typeof trustMetrics === 'object' && 'trust_distribution' in trustMetrics) {
      const metrics = trustMetrics as any;
      return {
        trustDistribution: metrics.trust_distribution || {},
        avgTrust: metrics.average_trust || 0, // Use actual average, not hardcoded
        trustTrend: metrics.trust_trend || 0,
        totalAgents: metrics.total_agents || 0,
        activeAgents: metrics.total_agents || 0
      };
    }

    // Handle array structure (if it changes in future)
    if (Array.isArray(trustMetrics)) {
      const metricsArray = trustMetrics as any[];
      const now = new Date();
      const cutoff = new Date(now.getTime() - (timeRange === '24h' ? 24 * 60 * 60 * 1000 : 7 * 24 * 60 * 60 * 1000));

      // Filter metrics by time range
      const filteredMetrics = metricsArray.filter(metric =>
        new Date(metric.timestamp) >= cutoff
      );

      // Calculate trust score distribution
      const trustDistribution = {
        high: filteredMetrics.filter(m => m.trust_score >= 0.8).length,
        medium: filteredMetrics.filter(m => m.trust_score >= 0.5 && m.trust_score < 0.8).length,
        low: filteredMetrics.filter(m => m.trust_score < 0.5).length
      };

      // Calculate average trust over time
      const avgTrust = filteredMetrics.length > 0
        ? filteredMetrics.reduce((sum, m) => sum + m.trust_score, 0) / filteredMetrics.length
        : 0;

      // Calculate trust trend
      const recent = filteredMetrics.filter(m =>
        new Date(m.timestamp) >= new Date(now.getTime() - 60 * 60 * 1000)
      );
      const older = filteredMetrics.filter(m =>
        new Date(m.timestamp) < new Date(now.getTime() - 60 * 60 * 1000)
      );

      const recentAvg = recent.length > 0 ? recent.reduce((sum, m) => sum + m.trust_score, 0) / recent.length : 0;
      const olderAvg = older.length > 0 ? older.reduce((sum, m) => sum + m.trust_score, 0) / older.length : 0;
      const trustTrend = recentAvg - olderAvg;

      return {
        trustDistribution,
        avgTrust,
        trustTrend,
        totalAgents: filteredMetrics.length,
        activeAgents: filteredMetrics.filter(m =>
          new Date(m.timestamp) >= new Date(now.getTime() - 60 * 60 * 1000)
        ).length
      };
    }

    return null;
  }, [trustMetrics, timeRange, isDemoMode]);

  // Violation analytics
  const violationAnalytics = useMemo(() => {
    if (!recentViolations || !Array.isArray(recentViolations)) return null;

    const now = new Date();
    const cutoff = new Date(now.getTime() - (timeRange === '24h' ? 24 * 60 * 60 * 1000 : 7 * 24 * 60 * 60 * 1000));

    const filteredViolations = recentViolations.filter(violation =>
      new Date(violation.timestamp) >= cutoff
    );

    // Group violations by type
    const violationTypes = filteredViolations.reduce((acc, violation) => {
      acc[violation.type] = (acc[violation.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    // Calculate violation rate
    const violationRate = filteredViolations.length / (timeRange === '24h' ? 24 : 168); // per hour

    return {
      totalViolations: filteredViolations.length,
      violationTypes,
      violationRate,
      severityDistribution: {
        high: filteredViolations.filter(v => v.severity === 'high').length,
        medium: filteredViolations.filter(v => v.severity === 'medium').length,
        low: filteredViolations.filter(v => v.severity === 'low').length
      }
    };
  }, [recentViolations, timeRange]);

  const calculateAverageTrust = () => {
    if (!trustMetrics) return 0;

    // Handle demo mode mock data structure
    if (isDemoMode && typeof trustMetrics === 'object' && 'overall_score' in trustMetrics) {
      return Math.round((trustMetrics as any).overall_score || 0);
    }

    // Handle the actual API response structure
    if (typeof trustMetrics === 'object' && 'average_trust_score' in trustMetrics) {
      return Math.round((trustMetrics as any).average_trust_score || 0);
    }

    // Handle array structure (if it changes in future)
    if (Array.isArray(trustMetrics) && trustMetrics.length > 0) {
      const metricsArr = trustMetrics as any[];
      const total = metricsArr.reduce((sum, metric) => sum + metric.trust_score, 0);
      return Math.round((total / metricsArr.length) * 100); // Convert to 0-100 scale
    }

    return 0;
  };

  const getTrustScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getTrustScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    if (score >= 40) return 'bg-orange-100';
    return 'bg-red-100';
  };

  // Determine if we have trust metrics to display
  const displayTrustMetrics = trustMetrics && (
    (typeof trustMetrics === 'object' && Object.keys(trustMetrics).length > 0) ||
    (Array.isArray(trustMetrics) && trustMetrics.length > 0)
  );

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="h-6 w-6 text-green-600" />
              <div>
                <CardTitle>Trust Dashboard</CardTitle>
                <p className="text-sm text-gray-600 mt-1">
                  {isDemoMode
                    ? 'Viewing simulated trust metrics and agent monitoring for demonstration'
                    : 'Monitor trust scores and agent behavior across the system'
                  }
                </p>
              </div>
              {isDemoMode && (
                <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-300">
                  <Play className="h-3 w-3 mr-1" />
                  Demo Data
                </Badge>
              )}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchMetrics()}
              disabled={metricsLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${metricsLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Debug Error Display */}
      {(metricsError || policiesError || violationsError || quarantineError) && (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="text-red-800">Debug: API Errors</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              {metricsError && <div className="text-red-700">Trust Metrics: {metricsError.message}</div>}
              {policiesError && <div className="text-red-700">Trust Policies: {policiesError.message}</div>}
              {violationsError && <div className="text-red-700">Violations: {violationsError.message}</div>}
              {quarantineError && <div className="text-red-700">Quarantined Agents: {quarantineError.message}</div>}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Show notice when in live mode with no data */}
      {!isDemoMode && !displayTrustMetrics && !metricsLoading && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-900">Live Data Mode</h3>
                <p className="text-sm text-blue-700">
                  Trust metrics will appear here when the system has data. Toggle Demo Mode ON to see sample metrics.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Trust Metrics Overview - Only show in demo mode or with valid data */}
      {(isDemoMode || displayTrustMetrics) && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Average Trust Score</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${getTrustScoreColor(calculateAverageTrust())}`}>
                {metricsLoading ? '...' : calculateAverageTrust()}
              </div>
              <p className="text-xs text-muted-foreground">
                Network average
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metricsLoading ? '...' : (
                  (trustMetrics as any)?.total_agents !== undefined ? (trustMetrics as any).total_agents :
                  Array.isArray(trustMetrics) ? trustMetrics.length : 0
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Tracked agents
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Trust Violations</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {violationsLoading ? '...' : (
                  recentViolations?.count !== undefined ? recentViolations.count :
                  recentViolations?.violations?.length || 0
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Recent violations
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Quarantined</CardTitle>
              <Lock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {quarantineLoading ? '...' : (
                  quarantinedAgents?.count !== undefined ? quarantinedAgents.count :
                  quarantinedAgents?.agents?.length || 0
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Quarantined agents
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Trust Scores */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Trust Scores</CardTitle>
        </CardHeader>
        <CardContent>
          {metricsLoading ? (
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : !trustMetrics || !Array.isArray(trustMetrics) || trustMetrics.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="mb-2">No individual agent trust metrics available</div>
              <div className="text-sm">
                {(trustMetrics as any)?.system_health === 'healthy'
                  ? 'System is healthy with no agents being tracked yet'
                  : 'System status shows aggregated trust metrics only'}
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {trustMetrics.map((metric) => (
                <div
                  key={metric.agent_id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 rounded-full ${getTrustScoreBg(metric.trust_score)} flex items-center justify-center`}>
                      <span className={`text-sm font-bold ${getTrustScoreColor(metric.trust_score)}`}>
                        {metric.trust_score}
                      </span>
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <User className="h-4 w-4 text-gray-400" />
                        <span className="text-sm font-medium">
                          {truncateText(metric.agent_id, 30)}
                        </span>
                      </div>
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span>Reputation: {metric.reputation}</span>
                        <span>Violations: {metric.violations}</span>
                        <span>Updated: {formatDate(metric.last_updated)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${metric.trust_score >= 80 ? 'bg-green-600' :
                          metric.trust_score >= 60 ? 'bg-yellow-600' :
                          metric.trust_score >= 40 ? 'bg-orange-600' : 'bg-red-600'}`}
                        style={{ width: `${metric.trust_score}%` }}
                      />
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

      {/* Recent Violations - Only show in demo mode or with data */}
      {(isDemoMode || (recentViolations?.violations && Array.isArray(recentViolations.violations) && recentViolations.violations.length > 0)) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5" />
              <span>Recent Trust Violations</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {violationsLoading ? (
              <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : !recentViolations?.violations || !Array.isArray(recentViolations.violations) || recentViolations.violations.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No recent violations
              </div>
            ) : (
              <div className="space-y-3">
                {recentViolations.violations.map((violation: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-start space-x-3 p-3 bg-red-50 rounded-lg border border-red-200"
                  >
                    <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-sm font-medium text-red-900">
                          {violation.type || 'Trust Violation'}
                        </span>
                        <span className="text-xs text-red-600">
                          {violation.severity || 'Medium'}
                        </span>
                      </div>
                      <p className="text-sm text-red-800 mb-2">
                        {violation.description || 'Trust violation detected'}
                      </p>
                      <div className="flex items-center space-x-4 text-xs text-red-600">
                        <div className="flex items-center space-x-1">
                          <User className="h-3 w-3" />
                          <span>{truncateText(violation.agent_id, 20)}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Clock className="h-3 w-3" />
                          <span>{formatDate(violation.timestamp)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Quarantined Agents - Only show in demo mode or with data */}
      {(isDemoMode || quarantinedAgents?.quarantined_agents && Array.isArray(quarantinedAgents.quarantined_agents) && quarantinedAgents.quarantined_agents.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Lock className="h-5 w-5" />
              <span>Quarantined Agents</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {quarantinedAgents.quarantined_agents.map((agent: any, index: number) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-200"
                >
                  <div className="flex items-center space-x-3">
                    <Lock className="h-5 w-5 text-orange-600" />
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-orange-900">
                          {truncateText(agent.agent_id, 30)}
                        </span>
                      </div>
                      <div className="text-xs text-orange-600">
                        Quarantined: {formatDate(agent.quarantine_date)}
                      </div>
                    </div>
                  </div>
                  <div className="text-sm text-orange-800">
                    {agent.reason || 'Trust violation'}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
