'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDemoMode } from '@/contexts/demo-mode-context';
import { api } from '@/lib/api-client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Network,
  Server,
  Globe,
  Users,
  Activity,
  Plus,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
  Shield,
  Database,
  Play
} from 'lucide-react';

interface FederationNode {
  id: string;
  name: string;
  url: string;
  status: 'online' | 'offline' | 'syncing' | 'error';
  version: string;
  lastSeen: string;
  capsuleCount: number;
  agentCount: number;
  trustScore: number;
  syncProgress: number;
  region: string;
  latency: number;
}

interface FederationStats {
  totalNodes: number;
  onlineNodes: number;
  totalCapsules: number;
  totalAgents: number;
  averageLatency: number;
  syncStatus: 'healthy' | 'degraded' | 'critical';
}

export function FederationDashboard() {
  const { isDemoMode } = useDemoMode();

  const [selectedNode, setSelectedNode] = useState<FederationNode | null>(null);
  const [newNodeUrl, setNewNodeUrl] = useState('');
  const [showAddNode, setShowAddNode] = useState(false);

  // Mock data for federation nodes - only in demo mode
  const mockNodes: FederationNode[] = isDemoMode ? [
    {
      id: 'node-001',
      name: 'UATP North America',
      url: 'https://na.uatp.network',
      status: 'online',
      version: '7.4.0',
      lastSeen: new Date().toISOString(),
      capsuleCount: 15420,
      agentCount: 2156,
      trustScore: 0.94,
      syncProgress: 100,
      region: 'North America',
      latency: 45
    },
    {
      id: 'node-002',
      name: 'UATP Europe',
      url: 'https://eu.uatp.network',
      status: 'online',
      version: '7.4.0',
      lastSeen: new Date(Date.now() - 30000).toISOString(),
      capsuleCount: 12890,
      agentCount: 1876,
      trustScore: 0.91,
      syncProgress: 100,
      region: 'Europe',
      latency: 78
    },
    {
      id: 'node-003',
      name: 'UATP Asia Pacific',
      url: 'https://ap.uatp.network',
      status: 'syncing',
      version: '6.9.5',
      lastSeen: new Date(Date.now() - 120000).toISOString(),
      capsuleCount: 8945,
      agentCount: 1234,
      trustScore: 0.88,
      syncProgress: 67,
      region: 'Asia Pacific',
      latency: 156
    },
    {
      id: 'node-004',
      name: 'UATP Research Lab',
      url: 'https://lab.uatp.network',
      status: 'offline',
      version: '7.1.0-beta',
      lastSeen: new Date(Date.now() - 3600000).toISOString(),
      capsuleCount: 3421,
      agentCount: 567,
      trustScore: 0.97,
      syncProgress: 0,
      region: 'Research',
      latency: 0
    }
  ] : [];

  const stats: FederationStats = {
    totalNodes: mockNodes.length,
    onlineNodes: mockNodes.filter(n => n.status === 'online').length,
    totalCapsules: mockNodes.reduce((sum, node) => sum + node.capsuleCount, 0),
    totalAgents: mockNodes.reduce((sum, node) => sum + node.agentCount, 0),
    averageLatency: mockNodes.filter(n => n.latency > 0).reduce((sum, node) => sum + node.latency, 0) / mockNodes.filter(n => n.latency > 0).length,
    syncStatus: mockNodes.some(n => n.status === 'error') ? 'critical' :
                mockNodes.some(n => n.status === 'syncing') ? 'degraded' : 'healthy'
  };

  const getStatusIcon = (status: FederationNode['status']) => {
    switch (status) {
      case 'online': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'offline': return <AlertCircle className="h-4 w-4 text-red-600" />;
      case 'syncing': return <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'error': return <AlertCircle className="h-4 w-4 text-red-600" />;
      default: return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: FederationNode['status']) => {
    switch (status) {
      case 'online': return 'bg-green-100 text-green-800';
      case 'offline': return 'bg-red-100 text-red-800';
      case 'syncing': return 'bg-blue-100 text-blue-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getSyncStatusColor = (status: FederationStats['syncStatus']) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Demo Mode Indicator */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Network className="h-6 w-6 text-blue-600" />
              <div>
                <h2 className="text-2xl font-bold">Federation Dashboard</h2>
                <p className="text-sm text-gray-600 mt-1">
                  {isDemoMode
                    ? 'Viewing simulated federation network for demonstration'
                    : 'Multi-node network coordination and management'
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
          </div>
        </CardHeader>
      </Card>

      {/* Show notice when in live mode with no data */}
      {!isDemoMode && mockNodes.length === 0 && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-blue-600" />
              <div>
                <h3 className="font-semibold text-blue-900">Live Data Mode</h3>
                <p className="text-sm text-blue-700">
                  Federation nodes will appear here when connected. Toggle Demo Mode ON to see sample network.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Federation Overview - Only show if we have nodes */}
      {mockNodes.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center">
                <Network className="h-4 w-4 mr-2" />
                Federation Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold mb-1">{stats.onlineNodes}/{stats.totalNodes}</div>
              <p className="text-xs text-gray-500">Nodes Online</p>
              <div className={`text-sm font-medium ${getSyncStatusColor(stats.syncStatus)}`}>
                {stats.syncStatus.toUpperCase()}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center">
                <Database className="h-4 w-4 mr-2" />
                Global Capsules
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold mb-1">{stats.totalCapsules.toLocaleString()}</div>
              <p className="text-xs text-gray-500">Across all nodes</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center">
                <Users className="h-4 w-4 mr-2" />
                Global Agents
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold mb-1">{stats.totalAgents.toLocaleString()}</div>
              <p className="text-xs text-gray-500">Active participants</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center">
                <Activity className="h-4 w-4 mr-2" />
                Network Latency
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold mb-1">{Math.round(stats.averageLatency)}ms</div>
              <p className="text-xs text-gray-500">Average response time</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Node Management - Only show if we have nodes */}
      {mockNodes.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center">
                <Server className="h-5 w-5 mr-2" />
                Federation Nodes
              </CardTitle>
              <Button
                onClick={() => setShowAddNode(!showAddNode)}
                className="flex items-center"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Node
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {showAddNode && (
              <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Input
                    placeholder="Enter node URL (e.g., https://node.uatp.network)"
                    value={newNodeUrl}
                    onChange={(e) => setNewNodeUrl(e.target.value)}
                    className="flex-1"
                  />
                  <Button onClick={() => {
                    // TODO: Implement node addition via API
                    // api.addFederationNode({ url: newNodeUrl });
                    setNewNodeUrl('');
                    setShowAddNode(false);
                  }}>
                    Connect
                  </Button>
                  <Button variant="outline" onClick={() => setShowAddNode(false)}>
                    Cancel
                  </Button>
                </div>
              </div>
            )}

            <div className="space-y-3">
              {mockNodes.map((node) => (
                <div
                  key={node.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedNode?.id === node.id ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                  }`}
                  onClick={() => setSelectedNode(node)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(node.status)}
                      <div>
                        <h3 className="font-medium">{node.name}</h3>
                        <p className="text-sm text-gray-500">{node.url}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge className={getStatusColor(node.status)}>
                        {node.status}
                      </Badge>
                      <span className="text-sm text-gray-500">{node.region}</span>
                    </div>
                  </div>

                  {node.status === 'syncing' && (
                    <div className="mt-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>Sync Progress</span>
                        <span>{node.syncProgress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${node.syncProgress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  <div className="mt-3 grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Capsules:</span>
                      <div className="font-medium">{node.capsuleCount.toLocaleString()}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Agents:</span>
                      <div className="font-medium">{node.agentCount.toLocaleString()}</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Trust:</span>
                      <div className="font-medium">{(node.trustScore * 100).toFixed(1)}%</div>
                    </div>
                    <div>
                      <span className="text-gray-500">Latency:</span>
                      <div className="font-medium">{node.latency > 0 ? `${node.latency}ms` : 'N/A'}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Selected Node Details - Only show if node is selected */}
      {selectedNode && mockNodes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Globe className="h-5 w-5 mr-2" />
              Node Details: {selectedNode.name}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-3">Node Information</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">URL:</span>
                    <span>{selectedNode.url}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Version:</span>
                    <span>{selectedNode.version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Region:</span>
                    <span>{selectedNode.region}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Last Seen:</span>
                    <span>{new Date(selectedNode.lastSeen).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-3">Performance Metrics</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Capsules:</span>
                    <span>{selectedNode.capsuleCount.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Agents:</span>
                    <span>{selectedNode.agentCount.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Trust Score:</span>
                    <span className="flex items-center">
                      {(selectedNode.trustScore * 100).toFixed(1)}%
                      <Shield className="h-3 w-3 ml-1 text-green-600" />
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Latency:</span>
                    <span>{selectedNode.latency > 0 ? `${selectedNode.latency}ms` : 'Offline'}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">
                  Federation allows civilization-scale coordination across multiple UATP instances
                </span>
                <div className="flex space-x-2">
                  <Button variant="outline" size="sm">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Sync Now
                  </Button>
                  <Button variant="outline" size="sm">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    View Metrics
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
