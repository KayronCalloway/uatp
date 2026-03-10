'use client';

import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api-client';
import { useWebSocket } from '@/hooks/use-websocket';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useDemoMode } from '@/contexts/demo-mode-context';
import {
  getMockLiveCaptureStats,
  getMockLiveConversations,
  mockApiCall,
  LiveCaptureStats,
  LiveConversation,
  LiveCaptureConversationsResponse
} from '@/lib/mock-data';
import {
  Activity,
  MessageSquare,
  Play,
  Pause,
  Eye,
  AlertCircle,
  CheckCircle,
  Clock,
  Plus,
  Zap,
  RefreshCw
} from 'lucide-react';

export function LiveCaptureDashboard() {
  const { isDemoMode } = useDemoMode();
  const [stats, setStats] = useState<LiveCaptureStats | null>(null);
  const [conversations, setConversations] = useState<LiveConversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [monitoringActive, setMonitoringActive] = useState(false);
  const [createdCapsuleIds, setCreatedCapsuleIds] = useState<Set<string>>(new Set());

  const queryClient = useQueryClient();

  // WebSocket connection for real-time updates
  const wsUrl = ''; // Disabled until backend WebSocket is implemented
  const { isConnected, lastMessage } = useWebSocket({
    url: wsUrl,
    maxReconnectAttempts: 0, // Don't try to reconnect
    onMessage: (message) => {
      if (message.type === 'live_capture_update') {
        fetchStats();
        fetchConversations();
      }
    }
  });

  const fetchStats = async () => {
    try {
      if (isDemoMode) {
        const mockStats = await mockApiCall(getMockLiveCaptureStats());
        setStats(mockStats);
        setError(null);
      } else {
        const result = await api.getLiveCaptureStats();
        setStats(result);
        setError(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch live capture stats');
    }
  };

  const fetchConversations = async () => {
    try {
      if (isDemoMode) {
        const mockConversations = await mockApiCall(getMockLiveConversations());
        setConversations(mockConversations.conversations || []);
        setError(null);
      } else {
        const result = await api.getLiveCaptureConversations();
        setConversations(result.conversations || []);
        setError(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch conversations');
    }
  };

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await Promise.all([fetchStats(), fetchConversations()]);
    } finally {
      setIsLoading(false);
    }
  };

  const startMonitoring = async () => {
    try {
      if (isDemoMode) {
        // In demo mode, just toggle the state
        setMonitoringActive(true);
        setError(null);
      } else {
        await api.startLiveCaptureMonitor({
          sources: ['claude-code', 'cursor-ide', 'windsurf'],
          real_time: true
        });
        setMonitoringActive(true);
        setError(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to start monitoring');
    }
  };

  // Capsule creation mutation
  const createCapsuleMutation = useMutation({
    mutationFn: async (sessionId: string) => {
      return await api.createCapsuleFromConversation(sessionId);
    },
    onSuccess: (response, sessionId) => {
      // Add to created capsules set
      setCreatedCapsuleIds(prev => new Set(prev).add(sessionId));
      
      // Refresh capsules list
      queryClient.invalidateQueries({ queryKey: ['capsules'] });
      
      // Optionally refresh conversations
      fetchConversations();
    },
    onError: (error: any) => {
      setError(`Failed to create capsule: ${error.message}`);
    }
  });

  const handleCreateCapsule = (sessionId: string) => {
    createCapsuleMutation.mutate(sessionId);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'paused': return <Pause className="h-4 w-4 text-yellow-500" />;
      case 'completed': return <Clock className="h-4 w-4 text-gray-500" />;
      default: return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const getStatusBadgeVariant = (status: string): "default" | "secondary" | "destructive" | "outline" => {
    switch (status) {
      case 'active': return 'default';
      case 'paused': return 'secondary';
      case 'completed': return 'outline';
      default: return 'destructive';
    }
  };

  // Fetch data on mount and when demo mode changes
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [isDemoMode]); // Re-fetch when demo mode toggles

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Activity className="h-8 w-8 text-blue-600" />
              <div>
                <div className="flex items-center space-x-2">
                  <CardTitle>Live Capture Dashboard</CardTitle>
                  {isDemoMode && (
                    <Badge variant="secondary" className="bg-orange-100 text-orange-800 border-orange-300">
                      <Play className="h-3 w-3 mr-1" />
                      Demo Data
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {isDemoMode
                    ? 'Viewing simulated AI conversation data for demonstration'
                    : 'Real-time AI conversation monitoring'
                  }
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {!isDemoMode && wsUrl && (
                <div className="flex items-center space-x-2">
                  <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-sm text-gray-600">
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
              )}
              <Button onClick={fetchData} disabled={isLoading} size="sm">
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                {isLoading ? 'Refreshing...' : 'Refresh'}
              </Button>
              <Button
                onClick={startMonitoring}
                disabled={monitoringActive}
                size="sm"
                variant={monitoringActive ? "secondary" : "default"}
              >
                <Play className="h-4 w-4 mr-2" />
                {monitoringActive ? 'Monitoring Active' : 'Start Monitoring'}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {createCapsuleMutation.isSuccess && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            Capsule created successfully! ID: {createCapsuleMutation.data?.capsule_id}
          </AlertDescription>
        </Alert>
      )}

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Sessions</p>
                  <p className="text-2xl font-bold text-blue-600">{stats.active_sessions || 0}</p>
                </div>
                <MessageSquare className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Captured</p>
                  <p className="text-2xl font-bold text-green-600">{(stats.total_captured || 0).toLocaleString()}</p>
                </div>
                <Eye className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Capture Rate</p>
                  <p className="text-2xl font-bold text-purple-600">{(stats.capture_rate || 0).toFixed(1)}/min</p>
                </div>
                <Activity className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Status</p>
                  <p className="text-2xl font-bold text-emerald-600 capitalize">{stats.status || 'unknown'}</p>
                </div>
                {getStatusIcon(stats.status || 'unknown')}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Active Conversations */}
      <Card>
        <CardHeader>
          <CardTitle>Active Conversations</CardTitle>
          <p className="text-sm text-gray-600">Live AI interactions across different platforms</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {conversations.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No active conversations</p>
                <p className="text-sm">Start an AI interaction to see live captures here</p>
              </div>
            ) : (
              conversations.map((conv) => (
                <div key={conv.session_id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      {conv.should_create_capsule ? 
                        <CheckCircle className="h-4 w-4 text-green-500" /> : 
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                      }
                      <div>
                        <p className="font-medium">{conv.platform}</p>
                        <p className="text-sm text-gray-600">User: {conv.user_id}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-xs text-gray-500">Significance:</span>
                        <Badge variant={conv.significance_score >= 0.6 ? 'default' : 'secondary'}>
                          {conv.significance_score.toFixed(2)}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-500">
                        {conv.message_count} messages
                      </p>
                      {conv.should_create_capsule && (
                        <div className="mt-2">
                          <Badge variant="outline" className="text-green-600 border-green-600">
                            Auto-Capsule Eligible
                          </Badge>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex justify-between text-sm text-gray-500">
                    <span>Session: {conv.session_id.slice(0, 20)}...</span>
                    <span>Last activity: {new Date(conv.last_activity).toLocaleString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Source Integration Status */}
      {stats?.sources && (
        <Card>
          <CardHeader>
            <CardTitle>Integration Status</CardTitle>
            <p className="text-sm text-gray-600">AI platform capture hooks and their status</p>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(stats.sources).map(([source, info]) => (
                <div key={source} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium capitalize">{source.replace('-', ' ')}</h4>
                    <div className={`h-3 w-3 rounded-full ${info.active ? 'bg-green-500' : 'bg-gray-400'}`} />
                  </div>
                  <p className="text-sm text-gray-600">
                    {info.captures} captures
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {info.active ? 'Active' : 'Inactive'}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Real-time Activity Log */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <p className="text-sm text-gray-600">Latest captures and system events</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {lastMessage && (
              <div className="text-xs text-gray-500 p-2 bg-blue-50 rounded">
                <strong>WebSocket:</strong> {JSON.stringify(lastMessage, null, 2)}
              </div>
            )}
            {stats?.last_capture && (
              <div className="text-sm text-gray-600 p-2 border-l-4 border-blue-500 bg-gray-50">
                Last capture: {new Date(stats.last_capture).toLocaleString()}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}