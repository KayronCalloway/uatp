'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api-client';
import { 
  Globe, 
  Zap, 
  Shield, 
  Users, 
  AlertTriangle,
  CheckCircle,
  Activity
} from 'lucide-react';

export function UniverseStatus() {
  const { data: healthData, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: api.healthCheck,
    refetchInterval: 10000,
  });

  const { data: universeData, isLoading: universeLoading } = useQuery({
    queryKey: ['universe-data'],
    queryFn: api.getUniverseVisualizationData,
    refetchInterval: 30000,
  });

  const { data: hallucinationStats } = useQuery({
    queryKey: ['hallucination-stats'],
    queryFn: api.getHallucinationStats,
    refetchInterval: 30000,
  });

  if (healthLoading || universeLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </CardContent>
      </Card>
    );
  }

  const isHealthy = healthData?.status === 'healthy';
  const totalNodes = universeData?.universe_stats?.total_capsules || 0;
  const activeAgents = universeData?.universe_stats?.active_agents || 0;
  const verificationRate = universeData?.universe_stats?.verification_rate || 0;
  const hallucinationRate = hallucinationStats?.detection_rate || 0;

  return (
    <div className="space-y-4">
      {/* System Health Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>Universe System Status</span>
            <Badge variant={isHealthy ? 'default' : 'destructive'}>
              {isHealthy ? 'Online' : 'Offline'}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-2">
              {isHealthy ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-red-600" />
              )}
              <span className="text-sm">API Server</span>
            </div>
            <div className="flex items-center space-x-2">
              <Shield className="h-4 w-4 text-blue-600" />
              <span className="text-sm">Security: Active</span>
            </div>
            <div className="flex items-center space-x-2">
              <Zap className="h-4 w-4 text-yellow-600" />
              <span className="text-sm">Performance: Optimized</span>
            </div>
            <div className="flex items-center space-x-2">
              <Globe className="h-4 w-4 text-green-600" />
              <span className="text-sm">Universe: Live</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Universe Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center space-x-2">
              <Globe className="h-4 w-4" />
              <span>Total Capsules</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{totalNodes}</div>
            <p className="text-xs text-gray-500">Active nodes in universe</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center space-x-2">
              <Users className="h-4 w-4" />
              <span>Active Agents</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{activeAgents}</div>
            <p className="text-xs text-gray-500">Contributing to universe</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center space-x-2">
              <CheckCircle className="h-4 w-4" />
              <span>Verification Rate</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">
              {(verificationRate * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-500">Capsules verified</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4" />
              <span>Hallucination Rate</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {(hallucinationRate * 100).toFixed(2)}%
            </div>
            <p className="text-xs text-gray-500">Content analyzed</p>
          </CardContent>
        </Card>
      </div>

      {/* Real-time Connection Status */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Backend Connection</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-red-500'} animate-pulse`}></div>
              <span className="text-sm">
                {isHealthy ? 'Connected to http://localhost:8000' : 'Disconnected'}
              </span>
            </div>
            <Badge variant="outline" className="text-xs">
              Live Data
            </Badge>
          </div>
          {healthData?.services && (
            <div className="mt-3 text-xs text-gray-600">
              <div className="grid grid-cols-2 gap-1">
                {Object.entries(healthData.services).map(([service, status]) => (
                  <div key={service} className="flex items-center space-x-1">
                    <span>{service}:</span>
                    <span className="text-green-600">{status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}