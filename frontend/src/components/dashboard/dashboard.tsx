'use client';

import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/contexts/auth-context';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { api } from '@/lib/api-client';
import {
  getMockHealthCheck,
  getMockCapsuleStats,
  getMockTrustMetricsData,
  mockApiCall
} from '@/lib/mock-data';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Database,
  Activity,
  Users,
  TrendingUp,
  Shield,
  Globe,
  Play
} from 'lucide-react';
import { ConnectionTest } from '@/components/debug/connection-test';

interface DashboardProps {
  onViewChange?: (view: string) => void;
}

export function Dashboard({ onViewChange }: DashboardProps) {
  const { isDemoMode } = useDemoMode();

  // Fetch dashboard data with demo mode support
  const { data: healthData, isLoading: healthLoading, error: healthError } = useQuery({
    queryKey: ['health', isDemoMode],
    queryFn: async () => {
      if (isDemoMode) {
        return mockApiCall(getMockHealthCheck());
      }
      return api.healthCheck();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: isDemoMode ? 0 : 3, // Don't retry in demo mode
    retryDelay: 1000,
  });

  const { data: statsData, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['capsule-stats', isDemoMode],
    queryFn: async () => {
      if (isDemoMode) {
        return mockApiCall(getMockCapsuleStats());
      }
      return api.getCapsuleStats(false);  // false = live data only (exclude demo capsules)
    },
    refetchInterval: 60000, // Refresh every minute
    retry: isDemoMode ? 0 : 3,
    retryDelay: 1000,
  });

  const { data: trustMetrics, isLoading: trustLoading, error: trustError } = useQuery({
    queryKey: ['trust-metrics', isDemoMode],
    queryFn: async () => {
      if (isDemoMode) {
        return mockApiCall(getMockTrustMetricsData());
      }
      return api.getTrustMetrics();
    },
    refetchInterval: 120000, // Refresh every 2 minutes
    retry: isDemoMode ? 0 : 3,
    retryDelay: 1000,
  });

  return (
    <div className="space-y-6">
      {/* Demo Mode Indicator */}
      {isDemoMode && (
        <Card className="bg-orange-50 border-orange-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Play className="h-5 w-5 text-orange-600" />
              <div>
                <h3 className="font-semibold text-orange-900">Demo Mode Active</h3>
                <p className="text-sm text-orange-700">
                  Viewing simulated UATP system data for demonstration purposes. Toggle off in the top-right to connect to real data.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Connection Test - Only show in real mode */}
      {!isDemoMode && (
        <div>
          <ConnectionTest />
        </div>
      )}

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* System Health */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Health</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {healthLoading ? '...' : healthError ? 'Error' : healthData?.status || 'Unknown'}
              </div>
              <p className="text-xs text-muted-foreground">
                {healthLoading ? 'Loading...' : healthError ? `Error: ${healthError.message}` : `Version ${healthData?.version || 'N/A'}`}
              </p>
            </CardContent>
          </Card>

          {/* Total Capsules */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Capsules</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statsLoading ? '...' : statsError ? 'Error' : statsData?.total_capsules?.toLocaleString() || '0'}
              </div>
              <p className="text-xs text-muted-foreground">
                {statsLoading ? 'Loading...' : statsError ? 'Failed to load' : `${Object.keys(statsData?.types || {}).length} types`}
              </p>
            </CardContent>
          </Card>

          {/* Unique Agents */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Unique Agents</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statsLoading ? '...' : statsData?.unique_agents?.toLocaleString() || '0'}
              </div>
              <p className="text-xs text-muted-foreground">
                Active contributors
              </p>
            </CardContent>
          </Card>

          {/* Trust Score - Only show in demo mode or with valid data */}
          {(isDemoMode || (trustMetrics && trustMetrics.length > 0)) && (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Trust Score</CardTitle>
                <Shield className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {trustLoading ? '...' :
                    isDemoMode ?
                      trustMetrics?.overall_score?.toFixed(1) || 'N/A' :
                      trustMetrics?.length ?
                        Math.round(trustMetrics.reduce((acc: any, m: any) => acc + m.trust_score, 0) / trustMetrics.length) :
                        'N/A'
                  }
                </div>
                <p className="text-xs text-muted-foreground">
                  {isDemoMode ? 'System trust level' : 'Average network trust'}
                </p>
              </CardContent>
            </Card>
          )}
        </div>

      {/* Main Dashboard Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Capsule Types */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Capsule Types Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <div className="flex items-center justify-center h-48">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <div className="space-y-4">
                {Object.entries(statsData?.types || {}).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-sm font-medium capitalize">{type}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{
                            width: `${((count as number) / (statsData?.total_capsules || 1)) * 100}%`
                          }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              className="w-full"
              variant="outline"
              onClick={() => onViewChange?.('capsules')}
            >
              <Database className="h-4 w-4 mr-2" />
              View Capsules
            </Button>
            <Button
              className="w-full"
              variant="outline"
              onClick={() => onViewChange?.('analytics')}
            >
              <TrendingUp className="h-4 w-4 mr-2" />
              Analytics
            </Button>
            <Button
              className="w-full"
              variant="outline"
              onClick={() => onViewChange?.('trust')}
            >
              <Shield className="h-4 w-4 mr-2" />
              Trust Dashboard
            </Button>
            <Button
              className="w-full"
              variant="outline"
              onClick={() => onViewChange?.('universe')}
            >
              <Globe className="h-4 w-4 mr-2" />
              Universe View
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
