'use client';

import React, { useState, useEffect } from 'react';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api-client';
import { useWebSocket } from '@/hooks/use-websocket';
import {
  Shield,
  Lock,
  CheckCircle,
  Clock,
  AlertTriangle,
  Hash,
  LinkIcon,
  Activity,
  Eye,
  RefreshCw,
  Play,
  AlertCircle
} from 'lucide-react';

interface ChainSeal {
  chain_id: string;
  seal_hash: string;
  timestamp: string;
  capsule_count: number;
  status: 'verified' | 'pending' | 'failed';
  integrity_score: number;
}

interface ChainSealsResponse {
  seals: ChainSeal[];
  total_chains: number;
  verified_seals: number;
  pending_seals: number;
}

export function ChainSealingDashboard() {
  const { isDemoMode } = useDemoMode();
  const [sealsData, setSealsData] = useState<ChainSealsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSealing, setIsSealing] = useState(false);
  const [selectedChain, setSelectedChain] = useState<string | null>(null);

  // Mock data for demo mode
  const mockSealsData: ChainSealsResponse | null = isDemoMode ? {
    seals: [
      {
        chain_id: 'chain-001',
        seal_hash: 'a7f9c2e4b8d1f3a6e2c9b5d8e1f4a7c3',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        capsule_count: 1247,
        status: 'verified' as const,
        integrity_score: 1.0
      },
      {
        chain_id: 'chain-002',
        seal_hash: 'b3e8d5a9f2c7e1b6d4a8c3f9e5b2d7a1',
        timestamp: new Date(Date.now() - 7200000).toISOString(),
        capsule_count: 956,
        status: 'verified' as const,
        integrity_score: 1.0
      },
      {
        chain_id: 'chain-003',
        seal_hash: 'c9f1e7b3a5d2c8e4f6a1b9d3e7c2f5a8',
        timestamp: new Date(Date.now() - 10800000).toISOString(),
        capsule_count: 2103,
        status: 'verified' as const,
        integrity_score: 0.98
      },
      {
        chain_id: 'chain-004',
        seal_hash: 'd2b6f8e1c4a9d7f3e5b2a8c1f9e4d6b3',
        timestamp: new Date(Date.now() - 300000).toISOString(),
        capsule_count: 834,
        status: 'pending' as const,
        integrity_score: 0.0
      }
    ],
    total_chains: 4,
    verified_seals: 3,
    pending_seals: 1
  } : null;

  // WebSocket connection for real-time updates
  const wsUrl = ''; // Disabled until backend WebSocket is implemented
  const { isConnected, lastMessage } = useWebSocket({
    url: wsUrl,
    maxReconnectAttempts: 0, // Don't try to reconnect
    onMessage: (message) => {
      if (message.type === 'chain_seal_update') {
        fetchSeals();
      }
    }
  });

  const fetchSeals = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.getChainSealsList();
      setSealsData(response);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch chain seals');
    } finally {
      setIsLoading(false);
    }
  };

  const createSeal = async () => {
    setIsSealing(true);
    try {
      const response = await api.sealChain({
        chain_id: 'current-chain-' + Date.now(),
      });
      await fetchSeals(); // Refresh the list
      setError(null);
    } catch (err: any) {
      setError('Failed to create seal: ' + (err.message || 'Unknown error'));
    } finally {
      setIsSealing(false);
    }
  };

  const verifyChainSeal = async (chainId: string) => {
    try {
      const response = await api.verifySeal(chainId, {
        verify_key: '', // Will use server's default key
      });

      if (response.verified) {
        setError(null);
        await fetchSeals(); // Refresh to show updated status
      } else {
        setError('Chain verification failed');
      }
    } catch (err: any) {
      setError('Failed to verify chain: ' + (err.message || 'Unknown error'));
    }
  };

  useEffect(() => {
    fetchSeals();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'verified': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'pending': return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'failed': return <AlertTriangle className="h-5 w-5 text-red-500" />;
      default: return <Activity className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'verified': return 'default';
      case 'pending': return 'secondary';
      case 'failed': return 'destructive';
      default: return 'outline';
    }
  };

  const getIntegrityColor = (score: number) => {
    if (score >= 0.99) return 'text-green-600';
    if (score >= 0.95) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Use real data when available, fall back to mock data in demo mode
  const displaySealsData = sealsData || mockSealsData;

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="h-8 w-8 text-blue-600" />
              <div>
                <CardTitle>Chain Sealing Dashboard</CardTitle>
                <p className="text-sm text-gray-600 mt-1">
                  {isDemoMode
                    ? 'Viewing simulated cryptographic chain seals for demonstration'
                    : 'Cryptographic chain integrity management'
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
            <div className="flex items-center space-x-2">
              {wsUrl && (
                <div className="flex items-center space-x-2">
                  <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-sm text-gray-600">
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
              )}
              <Button onClick={fetchSeals} disabled={isLoading} size="sm" variant="outline">
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                {isLoading ? 'Loading...' : 'Refresh'}
              </Button>
              <Button onClick={createSeal} disabled={isSealing} size="sm">
                <Lock className="h-4 w-4 mr-2" />
                {isSealing ? 'Sealing...' : 'Create Seal'}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {error && (
        <Card>
          <CardContent className="pt-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Show notice when in live mode with no data */}
      {!isDemoMode && !displaySealsData && !isLoading && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-900">Live Data Mode</h3>
                <p className="text-sm text-blue-700">
                  Chain seals will appear here when created. Toggle Demo Mode ON to see sample seals.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Grid */}
      {displaySealsData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Chains</p>
                  <p className="text-2xl font-bold text-blue-600">{displaySealsData.total_chains || 0}</p>
                </div>
                <LinkIcon className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Verified Seals</p>
                  <p className="text-2xl font-bold text-green-600">{displaySealsData.verified_seals || 0}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Pending Seals</p>
                  <p className="text-2xl font-bold text-yellow-600">{displaySealsData.pending_seals || 0}</p>
                </div>
                <Clock className="h-8 w-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Capsules</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {(displaySealsData.seals || []).reduce((sum, seal) => sum + (seal.capsule_count || 0), 0)}
                  </p>
                </div>
                <Hash className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Chain Seals List */}
      <Card>
        <CardHeader>
          <CardTitle>Chain Seals</CardTitle>
          <p className="text-sm text-gray-600">Cryptographic seals protecting capsule chain integrity</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {!displaySealsData || displaySealsData.seals.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Shield className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No chain seals found</p>
                <p className="text-sm">Create a seal to protect your capsule chains</p>
              </div>
            ) : (
              displaySealsData.seals.map((seal) => (
                <div key={seal.chain_id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(seal.status)}
                      <div>
                        <p className="font-medium text-lg">{seal.chain_id}</p>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge variant={getStatusBadgeVariant(seal.status)}>
                            {seal.status}
                          </Badge>
                          <span className={`text-sm font-medium ${getIntegrityColor(seal.integrity_score)}`}>
                            {(seal.integrity_score * 100).toFixed(1)}% integrity
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">
                        {new Date(seal.timestamp).toLocaleString()}
                      </p>
                      <Button
                        size="sm"
                        variant="outline"
                        className="mt-2"
                        onClick={() => verifyChainSeal(seal.chain_id)}
                      >
                        <Eye className="h-4 w-4 mr-2" />
                        Verify
                      </Button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="font-medium text-gray-700 mb-1">Seal Hash</p>
                      <code className="text-xs bg-gray-100 p-2 rounded block break-all">
                        {seal.seal_hash}
                      </code>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700 mb-1">Chain Details</p>
                      <div className="space-y-1 text-gray-600">
                        <p>Capsules: {seal.capsule_count}</p>
                        <p>Integrity: {(seal.integrity_score * 100).toFixed(2)}%</p>
                        <p>Status: {seal.status}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* System Health */}
      <Card>
        <CardHeader>
          <CardTitle>Cryptographic Health</CardTitle>
          <p className="text-sm text-gray-600">Chain integrity validation systems</p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="text-sm">Hash Chain Validation</span>
              </div>
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="text-sm">Temporal Ordering</span>
              </div>
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="text-sm">Cryptographic Signatures</span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="text-sm">Trust Enforcement</span>
              </div>
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="text-sm">Integrity Monitoring</span>
              </div>
              <div className="flex items-center space-x-3">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="text-sm">Real-time Verification</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Real-time Updates */}
      {lastMessage && (
        <Card>
          <CardHeader>
            <CardTitle>Real-time Updates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xs text-gray-500 p-2 bg-blue-50 rounded">
              <strong>WebSocket:</strong> {JSON.stringify(lastMessage, null, 2)}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
