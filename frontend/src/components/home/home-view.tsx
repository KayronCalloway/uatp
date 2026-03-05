'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import {
  Database,
  Shield,
  CheckCircle,
  Clock,
  Package
} from 'lucide-react';

export function HomeView() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['capsule-stats'],
    queryFn: () => api.getCapsuleStats(false),  // false = live data only (exclude demo capsules)
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
              Universal Autonomous Transaction Protocol
            </h1>
            <p className="text-xl text-gray-600 mb-6">
              A cryptographically verified system for capturing, storing, and attributing
              autonomous agent transactions across the AI ecosystem.
            </p>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <div className="flex items-center space-x-2">
                <div className={`h-2 w-2 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span>System {isHealthy ? 'Online' : 'Offline'}</span>
              </div>
              <span>•</span>
              <span>{totalCapsules.toLocaleString()} Capsules</span>
              <span>•</span>
              <span>Version 7.4</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Core Principles */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Core Principles</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-3 mb-3">
                <div className="h-10 w-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Database className="h-5 w-5 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold">Capture</h3>
              </div>
              <p className="text-gray-600">
                Every autonomous transaction is captured as an immutable capsule,
                preserving the complete context and metadata.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-3 mb-3">
                <div className="h-10 w-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <Shield className="h-5 w-5 text-green-600" />
                </div>
                <h3 className="text-lg font-semibold">Verify</h3>
              </div>
              <p className="text-gray-600">
                Cryptographic signatures and hash verification ensure the integrity
                and authenticity of every transaction.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-3 mb-3">
                <div className="h-10 w-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="h-5 w-5 text-purple-600" />
                </div>
                <h3 className="text-lg font-semibold">Attribute</h3>
              </div>
              <p className="text-gray-600">
                Proper attribution tracks contributions across the AI value chain,
                enabling fair economic distribution.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* What is a Capsule */}
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">What is a Capsule?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-gray-700">
            A capsule is the fundamental unit of UATP. Each capsule contains:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2 flex items-center space-x-2">
                <Package className="h-4 w-4 text-blue-600" />
                <span>Transaction Data</span>
              </h4>
              <p className="text-sm text-gray-600">
                The complete payload including content, reasoning steps,
                or economic transactions between agents and humans.
              </p>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2 flex items-center space-x-2">
                <Shield className="h-4 w-4 text-green-600" />
                <span>Verification Proof</span>
              </h4>
              <p className="text-sm text-gray-600">
                Cryptographic hash and signature ensuring the capsule
                hasn't been tampered with since creation.
              </p>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2 flex items-center space-x-2">
                <Clock className="h-4 w-4 text-purple-600" />
                <span>Timestamp</span>
              </h4>
              <p className="text-sm text-gray-600">
                Precise creation time enabling temporal ordering
                and chronological analysis of transactions.
              </p>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2 flex items-center space-x-2">
                <Database className="h-4 w-4 text-orange-600" />
                <span>Metadata</span>
              </h4>
              <p className="text-sm text-gray-600">
                Rich context including agent identity, platform,
                environment, and attribution information.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <Card>
        <CardHeader>
          <CardTitle>System Overview</CardTitle>
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
                  {Object.keys(stats?.by_type || {}).length}
                </div>
                <div className="text-sm text-gray-600">Capsule Types</div>
              </div>

              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-3xl font-bold text-purple-600 mb-1">
                  {stats?.recent_activity?.last_24h || 0}
                </div>
                <div className="text-sm text-gray-600">Last 24 Hours</div>
              </div>

              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="text-3xl font-bold text-orange-600 mb-1">
                  100%
                </div>
                <div className="text-sm text-gray-600">Verified</div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Use Cases */}
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">Use Cases</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="font-semibold mb-1">AI-Human Collaboration</h4>
              <p className="text-sm text-gray-600">
                Capture and attribute work done collaboratively between humans and AI agents,
                enabling proper credit and economic distribution.
              </p>
            </div>

            <div className="border-l-4 border-green-500 pl-4">
              <h4 className="font-semibold mb-1">Reasoning Verification</h4>
              <p className="text-sm text-gray-600">
                Store complete reasoning traces with confidence scores, enabling audit
                and verification of AI decision-making processes.
              </p>
            </div>

            <div className="border-l-4 border-purple-500 pl-4">
              <h4 className="font-semibold mb-1">Economic Attribution</h4>
              <p className="text-sm text-gray-600">
                Track value creation across the AI supply chain, from data providers
                to model creators to end applications.
              </p>
            </div>

            <div className="border-l-4 border-orange-500 pl-4">
              <h4 className="font-semibold mb-1">Compliance & Audit</h4>
              <p className="text-sm text-gray-600">
                Maintain immutable records of autonomous transactions for regulatory
                compliance and security auditing.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
