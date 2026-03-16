'use client';

import React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Crown,
  Database,
  Eye,
  Activity,
  CheckCircle2
} from 'lucide-react';
import { useCreator } from '@/contexts/creator-context';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';

export function CreatorDashboard() {
  const { state } = useCreator();
  const { isDemoMode, toggleDemoMode } = useDemoMode();

  // Fetch real capsule stats
  const { data: statsData, isLoading } = useQuery({
    queryKey: ['capsule-stats'],
    queryFn: () => api.getCapsuleStats(false),
    refetchInterval: 60000,
    retry: 1,
    enabled: !isDemoMode // Only fetch when not in demo mode
  });

  // Fetch health check
  const { data: healthData } = useQuery({
    queryKey: ['health-check'],
    queryFn: api.healthCheck,
    refetchInterval: 30000,
    retry: 1,
    enabled: !isDemoMode
  });

  if (!state.isCreator) {
    return null;
  }

  const isBackendHealthy = healthData?.status === 'healthy';
  const totalCapsules = statsData?.total_capsules || 0;
  const uniqueAgents = statsData?.unique_agents || 0;

  return (
    <Card className="border-amber-200 bg-gradient-to-br from-amber-50 via-yellow-50 to-amber-50 mb-6">
      <div className="p-5">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 bg-gradient-to-br from-amber-500 to-yellow-600 rounded-lg flex items-center justify-center shadow-sm">
              <Crown className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-amber-900">
                Creator Mode
              </h3>
              <p className="text-xs text-amber-700">
                {state.creatorId} • Full system access
              </p>
            </div>
          </div>

          {/* Demo Mode Toggle */}
          <Button
            variant={isDemoMode ? "default" : "outline"}
            size="sm"
            onClick={toggleDemoMode}
            className={isDemoMode ? "bg-amber-600 hover:bg-amber-700 text-white" : "border-amber-300 text-amber-700 hover:bg-amber-100"}
          >
            <Eye className="h-3.5 w-3.5 mr-1.5" />
            {isDemoMode ? "Demo Mode" : "Live Mode"}
          </Button>
        </div>

        {/* System Status Grid */}
        <div className="grid grid-cols-3 gap-3">
          {/* Backend Status */}
          <div className="bg-white rounded-lg p-3 border border-amber-100">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-600">Backend</span>
              {isBackendHealthy ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
              ) : (
                <Activity className="h-3.5 w-3.5 text-gray-400" />
              )}
            </div>
            <div className="text-lg font-bold text-gray-900">
              {isLoading ? '...' : isBackendHealthy ? 'Online' : 'Offline'}
            </div>
            <div className="text-xs text-gray-500 mt-0.5">
              {healthData?.version || 'Checking...'}
            </div>
          </div>

          {/* Capsules Count */}
          <div className="bg-white rounded-lg p-3 border border-amber-100">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-600">Capsules</span>
              <Database className="h-3.5 w-3.5 text-blue-600" />
            </div>
            <div className="text-lg font-bold text-gray-900">
              {isDemoMode ? '1,247' : (isLoading ? '...' : totalCapsules.toLocaleString())}
            </div>
            <div className="text-xs text-gray-500 mt-0.5">
              {isDemoMode ? 'Demo data' : 'Real data'}
            </div>
          </div>

          {/* Agents Count */}
          <div className="bg-white rounded-lg p-3 border border-amber-100">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-600">Agents</span>
              <Activity className="h-3.5 w-3.5 text-purple-600" />
            </div>
            <div className="text-lg font-bold text-gray-900">
              {isDemoMode ? '23' : (isLoading ? '...' : uniqueAgents)}
            </div>
            <div className="text-xs text-gray-500 mt-0.5">
              Unique contributors
            </div>
          </div>
        </div>

        {/* Info Footer */}
        <div className="mt-3 pt-3 border-t border-amber-100">
          <div className="flex items-center justify-between text-xs">
            <div className="text-amber-700">
              {isDemoMode ? (
                <span>Viewing simulated UATP system data</span>
              ) : (
                <span>Connected to live backend at localhost:8000</span>
              )}
            </div>
            <Badge variant="outline" className="border-amber-300 text-amber-700 text-[10px] px-1.5 py-0.5">
              Development
            </Badge>
          </div>
        </div>
      </div>
    </Card>
  );
}
