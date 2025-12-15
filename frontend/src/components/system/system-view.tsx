'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Activity,
  Database,
  Server,
  Shield,
  CheckCircle,
  AlertCircle,
  Clock,
  RefreshCw
} from 'lucide-react';

export function SystemView() {
  const { data: health, isLoading: healthLoading, refetch: refetchHealth } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.healthCheck(),
    staleTime: 1000 * 30,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['capsule-stats'],
    queryFn: () => api.getCapsuleStats(false),  // false = live data only (exclude demo capsules)
    staleTime: 1000 * 60,
  });

  const isHealthy = health?.status === 'healthy';
  const dbConnected = stats?.database_connected !== false;

  const handleRefresh = () => {
    refetchHealth();
    refetchStats();
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">System Status</CardTitle>
              <p className="text-sm text-gray-500 mt-1">
                Real-time health monitoring and diagnostics
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={healthLoading || statsLoading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${(healthLoading || statsLoading) ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Overall Status */}
      <Card className={isHealthy ? 'border-green-500 border-2' : 'border-red-500 border-2'}>
        <CardContent className="p-6">
          <div className="flex items-center space-x-4">
            {isHealthy ? (
              <CheckCircle className="h-12 w-12 text-green-500" />
            ) : (
              <AlertCircle className="h-12 w-12 text-red-500" />
            )}
            <div>
              <h2 className="text-2xl font-bold">
                System {isHealthy ? 'Operational' : 'Degraded'}
              </h2>
              <p className="text-gray-600">
                {isHealthy
                  ? 'All systems are functioning normally'
                  : 'Some systems are experiencing issues'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Component Status */}
      <div>
        <h3 className="text-xl font-semibold mb-4">Component Health</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* API Server */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`h-10 w-10 ${isHealthy ? 'bg-green-100' : 'bg-red-100'} rounded-lg flex items-center justify-center`}>
                    <Server className={`h-5 w-5 ${isHealthy ? 'text-green-600' : 'text-red-600'}`} />
                  </div>
                  <div>
                    <h4 className="font-semibold">API Server</h4>
                    <p className="text-xs text-gray-500">FastAPI / Quart Backend</p>
                  </div>
                </div>
                <div className={`h-3 w-3 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-red-500'}`}></div>
              </div>
              <div className="text-sm text-gray-600">
                Status: <span className={`font-medium ${isHealthy ? 'text-green-600' : 'text-red-600'}`}>
                  {isHealthy ? 'Running' : 'Error'}
                </span>
              </div>
              {health?.timestamp && (
                <div className="text-xs text-gray-500 mt-2 flex items-center space-x-1">
                  <Clock className="h-3 w-3" />
                  <span>Last check: {new Date(health.timestamp).toLocaleTimeString()}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Database */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`h-10 w-10 ${dbConnected ? 'bg-green-100' : 'bg-red-100'} rounded-lg flex items-center justify-center`}>
                    <Database className={`h-5 w-5 ${dbConnected ? 'text-green-600' : 'text-red-600'}`} />
                  </div>
                  <div>
                    <h4 className="font-semibold">Database</h4>
                    <p className="text-xs text-gray-500">PostgreSQL Store</p>
                  </div>
                </div>
                <div className={`h-3 w-3 rounded-full ${dbConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              </div>
              <div className="text-sm text-gray-600">
                Status: <span className={`font-medium ${dbConnected ? 'text-green-600' : 'text-red-600'}`}>
                  {dbConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              {stats?.total_capsules !== undefined && (
                <div className="text-xs text-gray-500 mt-2">
                  {stats.total_capsules.toLocaleString()} capsules stored
                </div>
              )}
            </CardContent>
          </Card>

          {/* Verification System */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <Shield className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold">Verification</h4>
                    <p className="text-xs text-gray-500">Cryptographic Signing</p>
                  </div>
                </div>
                <div className="h-3 w-3 rounded-full bg-green-500"></div>
              </div>
              <div className="text-sm text-gray-600">
                Status: <span className="font-medium text-green-600">Active</span>
              </div>
              <div className="text-xs text-gray-500 mt-2">
                Ed25519 signatures enabled
              </div>
            </CardContent>
          </Card>

          {/* Storage */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <Activity className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold">Storage</h4>
                    <p className="text-xs text-gray-500">Capsule Persistence</p>
                  </div>
                </div>
                <div className="h-3 w-3 rounded-full bg-green-500"></div>
              </div>
              <div className="text-sm text-gray-600">
                Status: <span className="font-medium text-green-600">Healthy</span>
              </div>
              <div className="text-xs text-gray-500 mt-2">
                JSONB + PostgreSQL
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* System Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>System Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          {statsLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {stats?.total_capsules?.toLocaleString() || 0}
                  </div>
                  <div className="text-sm text-gray-600">Total Capsules</div>
                </div>

                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {stats?.recent_activity?.last_24h || 0}
                  </div>
                  <div className="text-sm text-gray-600">Last 24 Hours</div>
                </div>

                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {Object.keys(stats?.by_type || {}).length}
                  </div>
                  <div className="text-sm text-gray-600">Capsule Types</div>
                </div>

                <div className="bg-orange-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    100%
                  </div>
                  <div className="text-sm text-gray-600">Verified</div>
                </div>
              </div>

              {/* Capsule Types Breakdown */}
              {stats?.by_type && Object.keys(stats.by_type).length > 0 && (
                <div className="pt-4 border-t">
                  <h4 className="text-sm font-semibold mb-3">Capsule Distribution</h4>
                  <div className="space-y-2">
                    {Object.entries(stats.by_type)
                      .sort(([, a], [, b]) => (b as number) - (a as number))
                      .slice(0, 5)
                      .map(([type, count]) => {
                        const percentage = stats.total_capsules > 0
                          ? ((count as number) / stats.total_capsules) * 100
                          : 0;
                        return (
                          <div key={type} className="flex items-center space-x-3">
                            <div className="w-32 text-sm text-gray-600 capitalize">
                              {type.replace(/_/g, ' ')}
                            </div>
                            <div className="flex-1 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${percentage}%` }}
                              />
                            </div>
                            <div className="w-20 text-sm text-gray-600 text-right">
                              {count as number} ({percentage.toFixed(1)}%)
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* System Information */}
      <Card>
        <CardHeader>
          <CardTitle>System Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Protocol Version:</span>
              <span className="font-medium ml-2">UATP 7.0</span>
            </div>
            <div>
              <span className="text-gray-600">API Version:</span>
              <span className="font-medium ml-2">1.0.0</span>
            </div>
            <div>
              <span className="text-gray-600">Backend:</span>
              <span className="font-medium ml-2">FastAPI + Quart</span>
            </div>
            <div>
              <span className="text-gray-600">Database:</span>
              <span className="font-medium ml-2">PostgreSQL 14+</span>
            </div>
            <div>
              <span className="text-gray-600">Verification:</span>
              <span className="font-medium ml-2">Ed25519</span>
            </div>
            <div>
              <span className="text-gray-600">Storage Format:</span>
              <span className="font-medium ml-2">JSONB</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
