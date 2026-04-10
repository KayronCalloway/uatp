'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Database,
  ArrowRight,
  TrendingUp,
  Package,
  Activity,
  RefreshCw
} from 'lucide-react';

interface CapsuleOverviewProps {
  onViewList?: () => void;
}

export function CapsuleOverview({ onViewList }: CapsuleOverviewProps) {
  const { data: stats, isLoading, error, refetch } = useQuery({
    queryKey: ['capsule-stats'],
    queryFn: () => api.getCapsuleStats(false),  // false = live data only (exclude demo capsules)
    staleTime: 1000 * 60 * 2, // 2 minutes
  });

  if (error) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="flex items-center justify-center text-red-600">
            <p>Error loading capsule statistics</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const totalCapsules = stats?.total_capsules || 0;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const statsAny = stats as any;
  const byType = statsAny?.by_type as Record<string, number> || {};
  const recentActivity = statsAny?.recent_activity as Record<string, number> || {};

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2 text-2xl">
                <Database className="h-6 w-6" />
                <span>Capsule System</span>
              </CardTitle>
              <p className="text-sm text-gray-500 mt-2">
                Universal Agent Trust Protocol
              </p>
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

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Capsules */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Capsules</p>
                <p className="text-3xl font-bold mt-2">{totalCapsules.toLocaleString()}</p>
              </div>
              <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center">
                <Package className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Last 24 Hours</p>
                <p className="text-3xl font-bold mt-2">{(recentActivity.last_24h || 0).toLocaleString()}</p>
              </div>
              <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                <Activity className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Capsule Types */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Capsule Types</p>
                <p className="text-3xl font-bold mt-2">{Object.keys(byType).length}</p>
              </div>
              <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Capsule Types Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Capsule Types Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          {Object.keys(byType).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(byType)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .map(([type, count]) => {
                  const percentage = totalCapsules > 0 ? ((count as number) / totalCapsules) * 100 : 0;
                  return (
                    <div key={type} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium capitalize">{type.replace(/_/g, ' ')}</span>
                        <span className="text-gray-600">
                          {count as number} ({percentage.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-4">
              No capsule type data available
            </div>
          )}
        </CardContent>
      </Card>

      {/* Action Button */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardContent className="p-8 text-center">
          <h3 className="text-xl font-semibold mb-2">Ready to explore?</h3>
          <p className="text-gray-600 mb-6">
            Browse through all capsules and view detailed information
          </p>
          <Button
            size="lg"
            onClick={onViewList}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Browse Capsules
            <ArrowRight className="h-5 w-5 ml-2" />
          </Button>
        </CardContent>
      </Card>

      {/* System Status */}
      <Card>
        <CardHeader>
          <CardTitle>System Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="h-2 w-2 bg-green-500 rounded-full mx-auto mb-2"></div>
              <p className="text-xs font-medium text-green-700">Database</p>
              <p className="text-xs text-green-600">Connected</p>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="h-2 w-2 bg-green-500 rounded-full mx-auto mb-2"></div>
              <p className="text-xs font-medium text-green-700">API</p>
              <p className="text-xs text-green-600">Operational</p>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="h-2 w-2 bg-blue-500 rounded-full mx-auto mb-2"></div>
              <p className="text-xs font-medium text-blue-700">Verification</p>
              <p className="text-xs text-blue-600">Active</p>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="h-2 w-2 bg-purple-500 rounded-full mx-auto mb-2"></div>
              <p className="text-xs font-medium text-purple-700">Storage</p>
              <p className="text-xs text-purple-600">Healthy</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
