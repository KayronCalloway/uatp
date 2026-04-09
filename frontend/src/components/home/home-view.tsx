'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import {
  Database,
  Shield,
  Brain,
  Target,
  Zap,
  BarChart3,
} from 'lucide-react';

export function HomeView() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['capsule-stats'],
    queryFn: () => api.getCapsuleStats(false),
    staleTime: 1000 * 60 * 2,
  });

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.healthCheck(),
    staleTime: 1000 * 30,
  });

  const totalCapsules = stats?.total_capsules || 0;
  const isHealthy = health?.status === 'healthy';

  return (
    <div className="w-full space-y-8">
      {/* Hero Section */}
      <Card className="border-2 border-blue-600">
        <CardContent className="p-8">
          <div className="max-w-3xl">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              UATP Capsule Engine
            </h1>
            <p className="text-xl text-gray-600 mb-6">
              Signed reasoning traces for AI systems. Capture every interaction,
              detect implicit feedback, calibrate confidence, and generate training data.
            </p>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <div className="flex items-center space-x-2">
                <div className={`h-2 w-2 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span>System {isHealthy ? 'Online' : 'Offline'}</span>
              </div>
              <span>•</span>
              <span>{totalCapsules.toLocaleString()} Capsules</span>
              <span>•</span>
              <span>v1.1.0</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Pipeline */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Pipeline</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center space-x-3 mb-3">
                <div className="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Database className="h-5 w-5 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold">Capture</h3>
              </div>
              <p className="text-sm text-gray-600">
                Every AI interaction becomes a cryptographically signed capsule with
                full context, reasoning traces, and tool usage.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="flex items-center space-x-3 mb-3">
                <div className="h-10 w-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <Brain className="h-5 w-5 text-green-600" />
                </div>
                <h3 className="text-lg font-semibold">Detect</h3>
              </div>
              <p className="text-sm text-gray-600">
                Signal detection identifies corrections, acceptances, refinements,
                and abandonment from implicit user feedback.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="flex items-center space-x-3 mb-3">
                <div className="h-10 w-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Target className="h-5 w-5 text-purple-600" />
                </div>
                <h3 className="text-lg font-semibold">Calibrate</h3>
              </div>
              <p className="text-sm text-gray-600">
                Confidence scores are calibrated against actual outcomes using
                local models, reducing overconfidence bias.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="flex items-center space-x-3 mb-3">
                <div className="h-10 w-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <Zap className="h-5 w-5 text-orange-600" />
                </div>
                <h3 className="text-lg font-semibold">Train</h3>
              </div>
              <p className="text-sm text-gray-600">
                DPO pairs are generated from corrections and acceptances for
                fine-tuning models on real interaction data.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Quick Stats */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>System Overview</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-3xl font-bold text-blue-600 mb-1">
                  {totalCapsules.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">Total Capsules</div>
              </div>

              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-3xl font-bold text-green-600 mb-1">
                  {Object.keys(stats?.types || {}).length}
                </div>
                <div className="text-sm text-gray-600">Capsule Types</div>
              </div>

              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-3xl font-bold text-purple-600 mb-1">
                  {(stats as any)?.recent_activity?.last_24h || 0}
                </div>
                <div className="text-sm text-gray-600">Last 24 Hours</div>
              </div>

              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="text-3xl font-bold text-orange-600 mb-1">
                  <Shield className="h-8 w-8 mx-auto text-orange-600" />
                </div>
                <div className="text-sm text-gray-600">Ed25519 + ML-DSA-65</div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
